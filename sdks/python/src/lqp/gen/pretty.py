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
    from typing import Any, IO, Never
else:
    from typing import Any, IO, NoReturn as Never

from lqp.proto.v1 import logic_pb2, fragments_pb2, transactions_pb2


class ParseError(Exception):
    pass


class PrettyPrinter:
    """Pretty printer for protobuf messages."""

    def __init__(self, io: IO[str] | None = None, max_width: int = 92, print_symbolic_relation_ids: bool = True):
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

    def _try_flat(self, msg: Any, pretty_fn: Any) -> str | None:
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

    @staticmethod
    def format_float32_value(v: float) -> str:
        """Format a float32 value at 32-bit precision (without suffix)."""
        import struct
        # Round-trip through float32 to get the exact 32-bit value,
        # then format with enough precision to distinguish it.
        f32 = struct.unpack('f', struct.pack('f', v))[0]
        # Use repr-style formatting: shortest string that round-trips
        s = f"{f32:.8g}"
        # Ensure it looks like a float (has a decimal point)
        if '.' not in s and 'e' not in s and 'inf' not in s and 'nan' not in s:
            s += '.0'
        return s

    @staticmethod
    def format_float32_literal(v: float) -> str:
        """Format a float32 value as an LQP literal with the f32 suffix."""
        import math
        if math.isinf(v):
            return 'inf32'
        if math.isnan(v):
            return 'nan32'
        return PrettyPrinter.format_float32_value(v) + 'f32'

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
        _t1731 = logic_pb2.Value(int32_value=v)
        return _t1731

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1732 = logic_pb2.Value(int_value=v)
        return _t1732

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1733 = logic_pb2.Value(float_value=v)
        return _t1733

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1734 = logic_pb2.Value(string_value=v)
        return _t1734

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1735 = logic_pb2.Value(boolean_value=v)
        return _t1735

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1736 = logic_pb2.Value(uint128_value=v)
        return _t1736

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1737 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1737,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1738 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1738,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1739 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1739,))
        _t1740 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1740,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1741 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1741,))
        _t1742 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1742,))
        if msg.new_line != "":
            _t1743 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1743,))
        _t1744 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1744,))
        _t1745 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1745,))
        _t1746 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1746,))
        if msg.comment != "":
            _t1747 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1747,))
        for missing_string in msg.missing_strings:
            _t1748 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1748,))
        _t1749 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1749,))
        _t1750 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1750,))
        _t1751 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1751,))
        if msg.partition_size_mb != 0:
            _t1752 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1752,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1753 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1753,))
        _t1754 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1754,))
        _t1755 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1755,))
        _t1756 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1756,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1757 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1757,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1758 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1758,))
        _t1759 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1759,))
        _t1760 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1760,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1761 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1761,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1762 = self._make_value_string(msg.compression)
            result.append(("compression", _t1762,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1763 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1763,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1764 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1764,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1765 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1765,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1766 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1766,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1767 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1767,))
        return sorted(result)

    def mask_secret_value(self, pair: tuple[str, str]) -> str:
        return "***"

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1768 = None
        return None

    def deconstruct_iceberg_data_from_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.from_snapshot is not None
        if msg.from_snapshot != "":
            assert msg.from_snapshot is not None
            return msg.from_snapshot
        else:
            _t1769 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1770 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1771 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1771,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1772 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1772,))
        if msg.compression != "":
            _t1773 = self._make_value_string(msg.compression)
            result.append(("compression", _t1773,))
        if len(result) == 0:
            return None
        else:
            _t1774 = None
        return sorted(result)

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> str:
        name = self.relation_id_to_string(msg)
        assert name is not None
        return name

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> logic_pb2.UInt128Value | None:
        name = self.relation_id_to_string(msg)
        if name is None:
            return self.relation_id_to_uint128(msg)
        else:
            _t1775 = None
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
        flat803 = self._try_flat(msg, self.pretty_transaction)
        if flat803 is not None:
            assert flat803 is not None
            self.write(flat803)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1588 = _dollar_dollar.configure
            else:
                _t1588 = None
            if _dollar_dollar.HasField("sync"):
                _t1589 = _dollar_dollar.sync
            else:
                _t1589 = None
            fields794 = (_t1588, _t1589, _dollar_dollar.epochs,)
            assert fields794 is not None
            unwrapped_fields795 = fields794
            self.write("(transaction")
            self.indent_sexp()
            field796 = unwrapped_fields795[0]
            if field796 is not None:
                self.newline()
                assert field796 is not None
                opt_val797 = field796
                self.pretty_configure(opt_val797)
            field798 = unwrapped_fields795[1]
            if field798 is not None:
                self.newline()
                assert field798 is not None
                opt_val799 = field798
                self.pretty_sync(opt_val799)
            field800 = unwrapped_fields795[2]
            if not len(field800) == 0:
                self.newline()
                for i802, elem801 in enumerate(field800):
                    if (i802 > 0):
                        self.newline()
                    self.pretty_epoch(elem801)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat806 = self._try_flat(msg, self.pretty_configure)
        if flat806 is not None:
            assert flat806 is not None
            self.write(flat806)
            return None
        else:
            _dollar_dollar = msg
            _t1590 = self.deconstruct_configure(_dollar_dollar)
            fields804 = _t1590
            assert fields804 is not None
            unwrapped_fields805 = fields804
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields805)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat810 = self._try_flat(msg, self.pretty_config_dict)
        if flat810 is not None:
            assert flat810 is not None
            self.write(flat810)
            return None
        else:
            fields807 = msg
            self.write("{")
            self.indent()
            if not len(fields807) == 0:
                self.newline()
                for i809, elem808 in enumerate(fields807):
                    if (i809 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem808)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat815 = self._try_flat(msg, self.pretty_config_key_value)
        if flat815 is not None:
            assert flat815 is not None
            self.write(flat815)
            return None
        else:
            _dollar_dollar = msg
            fields811 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields811 is not None
            unwrapped_fields812 = fields811
            self.write(":")
            field813 = unwrapped_fields812[0]
            self.write(field813)
            self.write(" ")
            field814 = unwrapped_fields812[1]
            self.pretty_raw_value(field814)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat841 = self._try_flat(msg, self.pretty_raw_value)
        if flat841 is not None:
            assert flat841 is not None
            self.write(flat841)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1591 = _dollar_dollar.date_value
            else:
                _t1591 = None
            deconstruct_result839 = _t1591
            if deconstruct_result839 is not None:
                assert deconstruct_result839 is not None
                unwrapped840 = deconstruct_result839
                self.pretty_raw_date(unwrapped840)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1592 = _dollar_dollar.datetime_value
                else:
                    _t1592 = None
                deconstruct_result837 = _t1592
                if deconstruct_result837 is not None:
                    assert deconstruct_result837 is not None
                    unwrapped838 = deconstruct_result837
                    self.pretty_raw_datetime(unwrapped838)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1593 = _dollar_dollar.string_value
                    else:
                        _t1593 = None
                    deconstruct_result835 = _t1593
                    if deconstruct_result835 is not None:
                        assert deconstruct_result835 is not None
                        unwrapped836 = deconstruct_result835
                        self.write(self.format_string_value(unwrapped836))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1594 = _dollar_dollar.int32_value
                        else:
                            _t1594 = None
                        deconstruct_result833 = _t1594
                        if deconstruct_result833 is not None:
                            assert deconstruct_result833 is not None
                            unwrapped834 = deconstruct_result833
                            self.write((str(unwrapped834) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1595 = _dollar_dollar.int_value
                            else:
                                _t1595 = None
                            deconstruct_result831 = _t1595
                            if deconstruct_result831 is not None:
                                assert deconstruct_result831 is not None
                                unwrapped832 = deconstruct_result831
                                self.write(str(unwrapped832))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1596 = _dollar_dollar.float32_value
                                else:
                                    _t1596 = None
                                deconstruct_result829 = _t1596
                                if deconstruct_result829 is not None:
                                    assert deconstruct_result829 is not None
                                    unwrapped830 = deconstruct_result829
                                    self.write(self.format_float32_literal(unwrapped830))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1597 = _dollar_dollar.float_value
                                    else:
                                        _t1597 = None
                                    deconstruct_result827 = _t1597
                                    if deconstruct_result827 is not None:
                                        assert deconstruct_result827 is not None
                                        unwrapped828 = deconstruct_result827
                                        self.write(str(unwrapped828))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1598 = _dollar_dollar.uint32_value
                                        else:
                                            _t1598 = None
                                        deconstruct_result825 = _t1598
                                        if deconstruct_result825 is not None:
                                            assert deconstruct_result825 is not None
                                            unwrapped826 = deconstruct_result825
                                            self.write((str(unwrapped826) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1599 = _dollar_dollar.uint128_value
                                            else:
                                                _t1599 = None
                                            deconstruct_result823 = _t1599
                                            if deconstruct_result823 is not None:
                                                assert deconstruct_result823 is not None
                                                unwrapped824 = deconstruct_result823
                                                self.write(self.format_uint128(unwrapped824))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1600 = _dollar_dollar.int128_value
                                                else:
                                                    _t1600 = None
                                                deconstruct_result821 = _t1600
                                                if deconstruct_result821 is not None:
                                                    assert deconstruct_result821 is not None
                                                    unwrapped822 = deconstruct_result821
                                                    self.write(self.format_int128(unwrapped822))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1601 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1601 = None
                                                    deconstruct_result819 = _t1601
                                                    if deconstruct_result819 is not None:
                                                        assert deconstruct_result819 is not None
                                                        unwrapped820 = deconstruct_result819
                                                        self.write(self.format_decimal(unwrapped820))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1602 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1602 = None
                                                        deconstruct_result817 = _t1602
                                                        if deconstruct_result817 is not None:
                                                            assert deconstruct_result817 is not None
                                                            unwrapped818 = deconstruct_result817
                                                            self.pretty_boolean_value(unwrapped818)
                                                        else:
                                                            fields816 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat847 = self._try_flat(msg, self.pretty_raw_date)
        if flat847 is not None:
            assert flat847 is not None
            self.write(flat847)
            return None
        else:
            _dollar_dollar = msg
            fields842 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields842 is not None
            unwrapped_fields843 = fields842
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field844 = unwrapped_fields843[0]
            self.write(str(field844))
            self.newline()
            field845 = unwrapped_fields843[1]
            self.write(str(field845))
            self.newline()
            field846 = unwrapped_fields843[2]
            self.write(str(field846))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat858 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat858 is not None:
            assert flat858 is not None
            self.write(flat858)
            return None
        else:
            _dollar_dollar = msg
            fields848 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields848 is not None
            unwrapped_fields849 = fields848
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field850 = unwrapped_fields849[0]
            self.write(str(field850))
            self.newline()
            field851 = unwrapped_fields849[1]
            self.write(str(field851))
            self.newline()
            field852 = unwrapped_fields849[2]
            self.write(str(field852))
            self.newline()
            field853 = unwrapped_fields849[3]
            self.write(str(field853))
            self.newline()
            field854 = unwrapped_fields849[4]
            self.write(str(field854))
            self.newline()
            field855 = unwrapped_fields849[5]
            self.write(str(field855))
            field856 = unwrapped_fields849[6]
            if field856 is not None:
                self.newline()
                assert field856 is not None
                opt_val857 = field856
                self.write(str(opt_val857))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1603 = ()
        else:
            _t1603 = None
        deconstruct_result861 = _t1603
        if deconstruct_result861 is not None:
            assert deconstruct_result861 is not None
            unwrapped862 = deconstruct_result861
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1604 = ()
            else:
                _t1604 = None
            deconstruct_result859 = _t1604
            if deconstruct_result859 is not None:
                assert deconstruct_result859 is not None
                unwrapped860 = deconstruct_result859
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat867 = self._try_flat(msg, self.pretty_sync)
        if flat867 is not None:
            assert flat867 is not None
            self.write(flat867)
            return None
        else:
            _dollar_dollar = msg
            fields863 = _dollar_dollar.fragments
            assert fields863 is not None
            unwrapped_fields864 = fields863
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields864) == 0:
                self.newline()
                for i866, elem865 in enumerate(unwrapped_fields864):
                    if (i866 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem865)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat870 = self._try_flat(msg, self.pretty_fragment_id)
        if flat870 is not None:
            assert flat870 is not None
            self.write(flat870)
            return None
        else:
            _dollar_dollar = msg
            fields868 = self.fragment_id_to_string(_dollar_dollar)
            assert fields868 is not None
            unwrapped_fields869 = fields868
            self.write(":")
            self.write(unwrapped_fields869)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat877 = self._try_flat(msg, self.pretty_epoch)
        if flat877 is not None:
            assert flat877 is not None
            self.write(flat877)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1605 = _dollar_dollar.writes
            else:
                _t1605 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1606 = _dollar_dollar.reads
            else:
                _t1606 = None
            fields871 = (_t1605, _t1606,)
            assert fields871 is not None
            unwrapped_fields872 = fields871
            self.write("(epoch")
            self.indent_sexp()
            field873 = unwrapped_fields872[0]
            if field873 is not None:
                self.newline()
                assert field873 is not None
                opt_val874 = field873
                self.pretty_epoch_writes(opt_val874)
            field875 = unwrapped_fields872[1]
            if field875 is not None:
                self.newline()
                assert field875 is not None
                opt_val876 = field875
                self.pretty_epoch_reads(opt_val876)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat881 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat881 is not None:
            assert flat881 is not None
            self.write(flat881)
            return None
        else:
            fields878 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields878) == 0:
                self.newline()
                for i880, elem879 in enumerate(fields878):
                    if (i880 > 0):
                        self.newline()
                    self.pretty_write(elem879)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat890 = self._try_flat(msg, self.pretty_write)
        if flat890 is not None:
            assert flat890 is not None
            self.write(flat890)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1607 = _dollar_dollar.define
            else:
                _t1607 = None
            deconstruct_result888 = _t1607
            if deconstruct_result888 is not None:
                assert deconstruct_result888 is not None
                unwrapped889 = deconstruct_result888
                self.pretty_define(unwrapped889)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1608 = _dollar_dollar.undefine
                else:
                    _t1608 = None
                deconstruct_result886 = _t1608
                if deconstruct_result886 is not None:
                    assert deconstruct_result886 is not None
                    unwrapped887 = deconstruct_result886
                    self.pretty_undefine(unwrapped887)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1609 = _dollar_dollar.context
                    else:
                        _t1609 = None
                    deconstruct_result884 = _t1609
                    if deconstruct_result884 is not None:
                        assert deconstruct_result884 is not None
                        unwrapped885 = deconstruct_result884
                        self.pretty_context(unwrapped885)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1610 = _dollar_dollar.snapshot
                        else:
                            _t1610 = None
                        deconstruct_result882 = _t1610
                        if deconstruct_result882 is not None:
                            assert deconstruct_result882 is not None
                            unwrapped883 = deconstruct_result882
                            self.pretty_snapshot(unwrapped883)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat893 = self._try_flat(msg, self.pretty_define)
        if flat893 is not None:
            assert flat893 is not None
            self.write(flat893)
            return None
        else:
            _dollar_dollar = msg
            fields891 = _dollar_dollar.fragment
            assert fields891 is not None
            unwrapped_fields892 = fields891
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields892)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat900 = self._try_flat(msg, self.pretty_fragment)
        if flat900 is not None:
            assert flat900 is not None
            self.write(flat900)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields894 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields894 is not None
            unwrapped_fields895 = fields894
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field896 = unwrapped_fields895[0]
            self.pretty_new_fragment_id(field896)
            field897 = unwrapped_fields895[1]
            if not len(field897) == 0:
                self.newline()
                for i899, elem898 in enumerate(field897):
                    if (i899 > 0):
                        self.newline()
                    self.pretty_declaration(elem898)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat902 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat902 is not None:
            assert flat902 is not None
            self.write(flat902)
            return None
        else:
            fields901 = msg
            self.pretty_fragment_id(fields901)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat911 = self._try_flat(msg, self.pretty_declaration)
        if flat911 is not None:
            assert flat911 is not None
            self.write(flat911)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1611 = getattr(_dollar_dollar, 'def')
            else:
                _t1611 = None
            deconstruct_result909 = _t1611
            if deconstruct_result909 is not None:
                assert deconstruct_result909 is not None
                unwrapped910 = deconstruct_result909
                self.pretty_def(unwrapped910)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1612 = _dollar_dollar.algorithm
                else:
                    _t1612 = None
                deconstruct_result907 = _t1612
                if deconstruct_result907 is not None:
                    assert deconstruct_result907 is not None
                    unwrapped908 = deconstruct_result907
                    self.pretty_algorithm(unwrapped908)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1613 = _dollar_dollar.constraint
                    else:
                        _t1613 = None
                    deconstruct_result905 = _t1613
                    if deconstruct_result905 is not None:
                        assert deconstruct_result905 is not None
                        unwrapped906 = deconstruct_result905
                        self.pretty_constraint(unwrapped906)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1614 = _dollar_dollar.data
                        else:
                            _t1614 = None
                        deconstruct_result903 = _t1614
                        if deconstruct_result903 is not None:
                            assert deconstruct_result903 is not None
                            unwrapped904 = deconstruct_result903
                            self.pretty_data(unwrapped904)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat918 = self._try_flat(msg, self.pretty_def)
        if flat918 is not None:
            assert flat918 is not None
            self.write(flat918)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1615 = _dollar_dollar.attrs
            else:
                _t1615 = None
            fields912 = (_dollar_dollar.name, _dollar_dollar.body, _t1615,)
            assert fields912 is not None
            unwrapped_fields913 = fields912
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field914 = unwrapped_fields913[0]
            self.pretty_relation_id(field914)
            self.newline()
            field915 = unwrapped_fields913[1]
            self.pretty_abstraction(field915)
            field916 = unwrapped_fields913[2]
            if field916 is not None:
                self.newline()
                assert field916 is not None
                opt_val917 = field916
                self.pretty_attrs(opt_val917)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat923 = self._try_flat(msg, self.pretty_relation_id)
        if flat923 is not None:
            assert flat923 is not None
            self.write(flat923)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1617 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1616 = _t1617
            else:
                _t1616 = None
            deconstruct_result921 = _t1616
            if deconstruct_result921 is not None:
                assert deconstruct_result921 is not None
                unwrapped922 = deconstruct_result921
                self.write(":")
                self.write(unwrapped922)
            else:
                _dollar_dollar = msg
                _t1618 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result919 = _t1618
                if deconstruct_result919 is not None:
                    assert deconstruct_result919 is not None
                    unwrapped920 = deconstruct_result919
                    self.write(self.format_uint128(unwrapped920))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat928 = self._try_flat(msg, self.pretty_abstraction)
        if flat928 is not None:
            assert flat928 is not None
            self.write(flat928)
            return None
        else:
            _dollar_dollar = msg
            _t1619 = self.deconstruct_bindings(_dollar_dollar)
            fields924 = (_t1619, _dollar_dollar.value,)
            assert fields924 is not None
            unwrapped_fields925 = fields924
            self.write("(")
            self.indent()
            field926 = unwrapped_fields925[0]
            self.pretty_bindings(field926)
            self.newline()
            field927 = unwrapped_fields925[1]
            self.pretty_formula(field927)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat936 = self._try_flat(msg, self.pretty_bindings)
        if flat936 is not None:
            assert flat936 is not None
            self.write(flat936)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1620 = _dollar_dollar[1]
            else:
                _t1620 = None
            fields929 = (_dollar_dollar[0], _t1620,)
            assert fields929 is not None
            unwrapped_fields930 = fields929
            self.write("[")
            self.indent()
            field931 = unwrapped_fields930[0]
            for i933, elem932 in enumerate(field931):
                if (i933 > 0):
                    self.newline()
                self.pretty_binding(elem932)
            field934 = unwrapped_fields930[1]
            if field934 is not None:
                self.newline()
                assert field934 is not None
                opt_val935 = field934
                self.pretty_value_bindings(opt_val935)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat941 = self._try_flat(msg, self.pretty_binding)
        if flat941 is not None:
            assert flat941 is not None
            self.write(flat941)
            return None
        else:
            _dollar_dollar = msg
            fields937 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields937 is not None
            unwrapped_fields938 = fields937
            field939 = unwrapped_fields938[0]
            self.write(field939)
            self.write("::")
            field940 = unwrapped_fields938[1]
            self.pretty_type(field940)

    def pretty_type(self, msg: logic_pb2.Type):
        flat970 = self._try_flat(msg, self.pretty_type)
        if flat970 is not None:
            assert flat970 is not None
            self.write(flat970)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1621 = _dollar_dollar.unspecified_type
            else:
                _t1621 = None
            deconstruct_result968 = _t1621
            if deconstruct_result968 is not None:
                assert deconstruct_result968 is not None
                unwrapped969 = deconstruct_result968
                self.pretty_unspecified_type(unwrapped969)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1622 = _dollar_dollar.string_type
                else:
                    _t1622 = None
                deconstruct_result966 = _t1622
                if deconstruct_result966 is not None:
                    assert deconstruct_result966 is not None
                    unwrapped967 = deconstruct_result966
                    self.pretty_string_type(unwrapped967)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1623 = _dollar_dollar.int_type
                    else:
                        _t1623 = None
                    deconstruct_result964 = _t1623
                    if deconstruct_result964 is not None:
                        assert deconstruct_result964 is not None
                        unwrapped965 = deconstruct_result964
                        self.pretty_int_type(unwrapped965)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1624 = _dollar_dollar.float_type
                        else:
                            _t1624 = None
                        deconstruct_result962 = _t1624
                        if deconstruct_result962 is not None:
                            assert deconstruct_result962 is not None
                            unwrapped963 = deconstruct_result962
                            self.pretty_float_type(unwrapped963)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1625 = _dollar_dollar.uint128_type
                            else:
                                _t1625 = None
                            deconstruct_result960 = _t1625
                            if deconstruct_result960 is not None:
                                assert deconstruct_result960 is not None
                                unwrapped961 = deconstruct_result960
                                self.pretty_uint128_type(unwrapped961)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1626 = _dollar_dollar.int128_type
                                else:
                                    _t1626 = None
                                deconstruct_result958 = _t1626
                                if deconstruct_result958 is not None:
                                    assert deconstruct_result958 is not None
                                    unwrapped959 = deconstruct_result958
                                    self.pretty_int128_type(unwrapped959)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1627 = _dollar_dollar.date_type
                                    else:
                                        _t1627 = None
                                    deconstruct_result956 = _t1627
                                    if deconstruct_result956 is not None:
                                        assert deconstruct_result956 is not None
                                        unwrapped957 = deconstruct_result956
                                        self.pretty_date_type(unwrapped957)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1628 = _dollar_dollar.datetime_type
                                        else:
                                            _t1628 = None
                                        deconstruct_result954 = _t1628
                                        if deconstruct_result954 is not None:
                                            assert deconstruct_result954 is not None
                                            unwrapped955 = deconstruct_result954
                                            self.pretty_datetime_type(unwrapped955)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1629 = _dollar_dollar.missing_type
                                            else:
                                                _t1629 = None
                                            deconstruct_result952 = _t1629
                                            if deconstruct_result952 is not None:
                                                assert deconstruct_result952 is not None
                                                unwrapped953 = deconstruct_result952
                                                self.pretty_missing_type(unwrapped953)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1630 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1630 = None
                                                deconstruct_result950 = _t1630
                                                if deconstruct_result950 is not None:
                                                    assert deconstruct_result950 is not None
                                                    unwrapped951 = deconstruct_result950
                                                    self.pretty_decimal_type(unwrapped951)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1631 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1631 = None
                                                    deconstruct_result948 = _t1631
                                                    if deconstruct_result948 is not None:
                                                        assert deconstruct_result948 is not None
                                                        unwrapped949 = deconstruct_result948
                                                        self.pretty_boolean_type(unwrapped949)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1632 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1632 = None
                                                        deconstruct_result946 = _t1632
                                                        if deconstruct_result946 is not None:
                                                            assert deconstruct_result946 is not None
                                                            unwrapped947 = deconstruct_result946
                                                            self.pretty_int32_type(unwrapped947)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1633 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1633 = None
                                                            deconstruct_result944 = _t1633
                                                            if deconstruct_result944 is not None:
                                                                assert deconstruct_result944 is not None
                                                                unwrapped945 = deconstruct_result944
                                                                self.pretty_float32_type(unwrapped945)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1634 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1634 = None
                                                                deconstruct_result942 = _t1634
                                                                if deconstruct_result942 is not None:
                                                                    assert deconstruct_result942 is not None
                                                                    unwrapped943 = deconstruct_result942
                                                                    self.pretty_uint32_type(unwrapped943)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields971 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields972 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields973 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields974 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields975 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields976 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields977 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields978 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields979 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat984 = self._try_flat(msg, self.pretty_decimal_type)
        if flat984 is not None:
            assert flat984 is not None
            self.write(flat984)
            return None
        else:
            _dollar_dollar = msg
            fields980 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields980 is not None
            unwrapped_fields981 = fields980
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field982 = unwrapped_fields981[0]
            self.write(str(field982))
            self.newline()
            field983 = unwrapped_fields981[1]
            self.write(str(field983))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields985 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields986 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields987 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields988 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat992 = self._try_flat(msg, self.pretty_value_bindings)
        if flat992 is not None:
            assert flat992 is not None
            self.write(flat992)
            return None
        else:
            fields989 = msg
            self.write("|")
            if not len(fields989) == 0:
                self.write(" ")
                for i991, elem990 in enumerate(fields989):
                    if (i991 > 0):
                        self.newline()
                    self.pretty_binding(elem990)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1019 = self._try_flat(msg, self.pretty_formula)
        if flat1019 is not None:
            assert flat1019 is not None
            self.write(flat1019)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1635 = _dollar_dollar.conjunction
            else:
                _t1635 = None
            deconstruct_result1017 = _t1635
            if deconstruct_result1017 is not None:
                assert deconstruct_result1017 is not None
                unwrapped1018 = deconstruct_result1017
                self.pretty_true(unwrapped1018)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1636 = _dollar_dollar.disjunction
                else:
                    _t1636 = None
                deconstruct_result1015 = _t1636
                if deconstruct_result1015 is not None:
                    assert deconstruct_result1015 is not None
                    unwrapped1016 = deconstruct_result1015
                    self.pretty_false(unwrapped1016)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1637 = _dollar_dollar.exists
                    else:
                        _t1637 = None
                    deconstruct_result1013 = _t1637
                    if deconstruct_result1013 is not None:
                        assert deconstruct_result1013 is not None
                        unwrapped1014 = deconstruct_result1013
                        self.pretty_exists(unwrapped1014)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1638 = _dollar_dollar.reduce
                        else:
                            _t1638 = None
                        deconstruct_result1011 = _t1638
                        if deconstruct_result1011 is not None:
                            assert deconstruct_result1011 is not None
                            unwrapped1012 = deconstruct_result1011
                            self.pretty_reduce(unwrapped1012)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1639 = _dollar_dollar.conjunction
                            else:
                                _t1639 = None
                            deconstruct_result1009 = _t1639
                            if deconstruct_result1009 is not None:
                                assert deconstruct_result1009 is not None
                                unwrapped1010 = deconstruct_result1009
                                self.pretty_conjunction(unwrapped1010)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1640 = _dollar_dollar.disjunction
                                else:
                                    _t1640 = None
                                deconstruct_result1007 = _t1640
                                if deconstruct_result1007 is not None:
                                    assert deconstruct_result1007 is not None
                                    unwrapped1008 = deconstruct_result1007
                                    self.pretty_disjunction(unwrapped1008)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1641 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1641 = None
                                    deconstruct_result1005 = _t1641
                                    if deconstruct_result1005 is not None:
                                        assert deconstruct_result1005 is not None
                                        unwrapped1006 = deconstruct_result1005
                                        self.pretty_not(unwrapped1006)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1642 = _dollar_dollar.ffi
                                        else:
                                            _t1642 = None
                                        deconstruct_result1003 = _t1642
                                        if deconstruct_result1003 is not None:
                                            assert deconstruct_result1003 is not None
                                            unwrapped1004 = deconstruct_result1003
                                            self.pretty_ffi(unwrapped1004)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1643 = _dollar_dollar.atom
                                            else:
                                                _t1643 = None
                                            deconstruct_result1001 = _t1643
                                            if deconstruct_result1001 is not None:
                                                assert deconstruct_result1001 is not None
                                                unwrapped1002 = deconstruct_result1001
                                                self.pretty_atom(unwrapped1002)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1644 = _dollar_dollar.pragma
                                                else:
                                                    _t1644 = None
                                                deconstruct_result999 = _t1644
                                                if deconstruct_result999 is not None:
                                                    assert deconstruct_result999 is not None
                                                    unwrapped1000 = deconstruct_result999
                                                    self.pretty_pragma(unwrapped1000)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1645 = _dollar_dollar.primitive
                                                    else:
                                                        _t1645 = None
                                                    deconstruct_result997 = _t1645
                                                    if deconstruct_result997 is not None:
                                                        assert deconstruct_result997 is not None
                                                        unwrapped998 = deconstruct_result997
                                                        self.pretty_primitive(unwrapped998)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1646 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1646 = None
                                                        deconstruct_result995 = _t1646
                                                        if deconstruct_result995 is not None:
                                                            assert deconstruct_result995 is not None
                                                            unwrapped996 = deconstruct_result995
                                                            self.pretty_rel_atom(unwrapped996)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1647 = _dollar_dollar.cast
                                                            else:
                                                                _t1647 = None
                                                            deconstruct_result993 = _t1647
                                                            if deconstruct_result993 is not None:
                                                                assert deconstruct_result993 is not None
                                                                unwrapped994 = deconstruct_result993
                                                                self.pretty_cast(unwrapped994)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields1020 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1021 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1026 = self._try_flat(msg, self.pretty_exists)
        if flat1026 is not None:
            assert flat1026 is not None
            self.write(flat1026)
            return None
        else:
            _dollar_dollar = msg
            _t1648 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1022 = (_t1648, _dollar_dollar.body.value,)
            assert fields1022 is not None
            unwrapped_fields1023 = fields1022
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1024 = unwrapped_fields1023[0]
            self.pretty_bindings(field1024)
            self.newline()
            field1025 = unwrapped_fields1023[1]
            self.pretty_formula(field1025)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1032 = self._try_flat(msg, self.pretty_reduce)
        if flat1032 is not None:
            assert flat1032 is not None
            self.write(flat1032)
            return None
        else:
            _dollar_dollar = msg
            fields1027 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1027 is not None
            unwrapped_fields1028 = fields1027
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1029 = unwrapped_fields1028[0]
            self.pretty_abstraction(field1029)
            self.newline()
            field1030 = unwrapped_fields1028[1]
            self.pretty_abstraction(field1030)
            self.newline()
            field1031 = unwrapped_fields1028[2]
            self.pretty_terms(field1031)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1036 = self._try_flat(msg, self.pretty_terms)
        if flat1036 is not None:
            assert flat1036 is not None
            self.write(flat1036)
            return None
        else:
            fields1033 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1033) == 0:
                self.newline()
                for i1035, elem1034 in enumerate(fields1033):
                    if (i1035 > 0):
                        self.newline()
                    self.pretty_term(elem1034)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1041 = self._try_flat(msg, self.pretty_term)
        if flat1041 is not None:
            assert flat1041 is not None
            self.write(flat1041)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1649 = _dollar_dollar.var
            else:
                _t1649 = None
            deconstruct_result1039 = _t1649
            if deconstruct_result1039 is not None:
                assert deconstruct_result1039 is not None
                unwrapped1040 = deconstruct_result1039
                self.pretty_var(unwrapped1040)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1650 = _dollar_dollar.constant
                else:
                    _t1650 = None
                deconstruct_result1037 = _t1650
                if deconstruct_result1037 is not None:
                    assert deconstruct_result1037 is not None
                    unwrapped1038 = deconstruct_result1037
                    self.pretty_value(unwrapped1038)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1044 = self._try_flat(msg, self.pretty_var)
        if flat1044 is not None:
            assert flat1044 is not None
            self.write(flat1044)
            return None
        else:
            _dollar_dollar = msg
            fields1042 = _dollar_dollar.name
            assert fields1042 is not None
            unwrapped_fields1043 = fields1042
            self.write(unwrapped_fields1043)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1070 = self._try_flat(msg, self.pretty_value)
        if flat1070 is not None:
            assert flat1070 is not None
            self.write(flat1070)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1651 = _dollar_dollar.date_value
            else:
                _t1651 = None
            deconstruct_result1068 = _t1651
            if deconstruct_result1068 is not None:
                assert deconstruct_result1068 is not None
                unwrapped1069 = deconstruct_result1068
                self.pretty_date(unwrapped1069)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1652 = _dollar_dollar.datetime_value
                else:
                    _t1652 = None
                deconstruct_result1066 = _t1652
                if deconstruct_result1066 is not None:
                    assert deconstruct_result1066 is not None
                    unwrapped1067 = deconstruct_result1066
                    self.pretty_datetime(unwrapped1067)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1653 = _dollar_dollar.string_value
                    else:
                        _t1653 = None
                    deconstruct_result1064 = _t1653
                    if deconstruct_result1064 is not None:
                        assert deconstruct_result1064 is not None
                        unwrapped1065 = deconstruct_result1064
                        self.write(self.format_string_value(unwrapped1065))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1654 = _dollar_dollar.int32_value
                        else:
                            _t1654 = None
                        deconstruct_result1062 = _t1654
                        if deconstruct_result1062 is not None:
                            assert deconstruct_result1062 is not None
                            unwrapped1063 = deconstruct_result1062
                            self.write((str(unwrapped1063) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1655 = _dollar_dollar.int_value
                            else:
                                _t1655 = None
                            deconstruct_result1060 = _t1655
                            if deconstruct_result1060 is not None:
                                assert deconstruct_result1060 is not None
                                unwrapped1061 = deconstruct_result1060
                                self.write(str(unwrapped1061))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1656 = _dollar_dollar.float32_value
                                else:
                                    _t1656 = None
                                deconstruct_result1058 = _t1656
                                if deconstruct_result1058 is not None:
                                    assert deconstruct_result1058 is not None
                                    unwrapped1059 = deconstruct_result1058
                                    self.write(self.format_float32_literal(unwrapped1059))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1657 = _dollar_dollar.float_value
                                    else:
                                        _t1657 = None
                                    deconstruct_result1056 = _t1657
                                    if deconstruct_result1056 is not None:
                                        assert deconstruct_result1056 is not None
                                        unwrapped1057 = deconstruct_result1056
                                        self.write(str(unwrapped1057))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1658 = _dollar_dollar.uint32_value
                                        else:
                                            _t1658 = None
                                        deconstruct_result1054 = _t1658
                                        if deconstruct_result1054 is not None:
                                            assert deconstruct_result1054 is not None
                                            unwrapped1055 = deconstruct_result1054
                                            self.write((str(unwrapped1055) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1659 = _dollar_dollar.uint128_value
                                            else:
                                                _t1659 = None
                                            deconstruct_result1052 = _t1659
                                            if deconstruct_result1052 is not None:
                                                assert deconstruct_result1052 is not None
                                                unwrapped1053 = deconstruct_result1052
                                                self.write(self.format_uint128(unwrapped1053))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1660 = _dollar_dollar.int128_value
                                                else:
                                                    _t1660 = None
                                                deconstruct_result1050 = _t1660
                                                if deconstruct_result1050 is not None:
                                                    assert deconstruct_result1050 is not None
                                                    unwrapped1051 = deconstruct_result1050
                                                    self.write(self.format_int128(unwrapped1051))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1661 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1661 = None
                                                    deconstruct_result1048 = _t1661
                                                    if deconstruct_result1048 is not None:
                                                        assert deconstruct_result1048 is not None
                                                        unwrapped1049 = deconstruct_result1048
                                                        self.write(self.format_decimal(unwrapped1049))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1662 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1662 = None
                                                        deconstruct_result1046 = _t1662
                                                        if deconstruct_result1046 is not None:
                                                            assert deconstruct_result1046 is not None
                                                            unwrapped1047 = deconstruct_result1046
                                                            self.pretty_boolean_value(unwrapped1047)
                                                        else:
                                                            fields1045 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1076 = self._try_flat(msg, self.pretty_date)
        if flat1076 is not None:
            assert flat1076 is not None
            self.write(flat1076)
            return None
        else:
            _dollar_dollar = msg
            fields1071 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1071 is not None
            unwrapped_fields1072 = fields1071
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1073 = unwrapped_fields1072[0]
            self.write(str(field1073))
            self.newline()
            field1074 = unwrapped_fields1072[1]
            self.write(str(field1074))
            self.newline()
            field1075 = unwrapped_fields1072[2]
            self.write(str(field1075))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1087 = self._try_flat(msg, self.pretty_datetime)
        if flat1087 is not None:
            assert flat1087 is not None
            self.write(flat1087)
            return None
        else:
            _dollar_dollar = msg
            fields1077 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1077 is not None
            unwrapped_fields1078 = fields1077
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1079 = unwrapped_fields1078[0]
            self.write(str(field1079))
            self.newline()
            field1080 = unwrapped_fields1078[1]
            self.write(str(field1080))
            self.newline()
            field1081 = unwrapped_fields1078[2]
            self.write(str(field1081))
            self.newline()
            field1082 = unwrapped_fields1078[3]
            self.write(str(field1082))
            self.newline()
            field1083 = unwrapped_fields1078[4]
            self.write(str(field1083))
            self.newline()
            field1084 = unwrapped_fields1078[5]
            self.write(str(field1084))
            field1085 = unwrapped_fields1078[6]
            if field1085 is not None:
                self.newline()
                assert field1085 is not None
                opt_val1086 = field1085
                self.write(str(opt_val1086))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1092 = self._try_flat(msg, self.pretty_conjunction)
        if flat1092 is not None:
            assert flat1092 is not None
            self.write(flat1092)
            return None
        else:
            _dollar_dollar = msg
            fields1088 = _dollar_dollar.args
            assert fields1088 is not None
            unwrapped_fields1089 = fields1088
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1089) == 0:
                self.newline()
                for i1091, elem1090 in enumerate(unwrapped_fields1089):
                    if (i1091 > 0):
                        self.newline()
                    self.pretty_formula(elem1090)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1097 = self._try_flat(msg, self.pretty_disjunction)
        if flat1097 is not None:
            assert flat1097 is not None
            self.write(flat1097)
            return None
        else:
            _dollar_dollar = msg
            fields1093 = _dollar_dollar.args
            assert fields1093 is not None
            unwrapped_fields1094 = fields1093
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1094) == 0:
                self.newline()
                for i1096, elem1095 in enumerate(unwrapped_fields1094):
                    if (i1096 > 0):
                        self.newline()
                    self.pretty_formula(elem1095)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1100 = self._try_flat(msg, self.pretty_not)
        if flat1100 is not None:
            assert flat1100 is not None
            self.write(flat1100)
            return None
        else:
            _dollar_dollar = msg
            fields1098 = _dollar_dollar.arg
            assert fields1098 is not None
            unwrapped_fields1099 = fields1098
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1099)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1106 = self._try_flat(msg, self.pretty_ffi)
        if flat1106 is not None:
            assert flat1106 is not None
            self.write(flat1106)
            return None
        else:
            _dollar_dollar = msg
            fields1101 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1101 is not None
            unwrapped_fields1102 = fields1101
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1103 = unwrapped_fields1102[0]
            self.pretty_name(field1103)
            self.newline()
            field1104 = unwrapped_fields1102[1]
            self.pretty_ffi_args(field1104)
            self.newline()
            field1105 = unwrapped_fields1102[2]
            self.pretty_terms(field1105)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1108 = self._try_flat(msg, self.pretty_name)
        if flat1108 is not None:
            assert flat1108 is not None
            self.write(flat1108)
            return None
        else:
            fields1107 = msg
            self.write(":")
            self.write(fields1107)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1112 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1112 is not None:
            assert flat1112 is not None
            self.write(flat1112)
            return None
        else:
            fields1109 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1109) == 0:
                self.newline()
                for i1111, elem1110 in enumerate(fields1109):
                    if (i1111 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1110)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1119 = self._try_flat(msg, self.pretty_atom)
        if flat1119 is not None:
            assert flat1119 is not None
            self.write(flat1119)
            return None
        else:
            _dollar_dollar = msg
            fields1113 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1113 is not None
            unwrapped_fields1114 = fields1113
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1115 = unwrapped_fields1114[0]
            self.pretty_relation_id(field1115)
            field1116 = unwrapped_fields1114[1]
            if not len(field1116) == 0:
                self.newline()
                for i1118, elem1117 in enumerate(field1116):
                    if (i1118 > 0):
                        self.newline()
                    self.pretty_term(elem1117)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1126 = self._try_flat(msg, self.pretty_pragma)
        if flat1126 is not None:
            assert flat1126 is not None
            self.write(flat1126)
            return None
        else:
            _dollar_dollar = msg
            fields1120 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1120 is not None
            unwrapped_fields1121 = fields1120
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1122 = unwrapped_fields1121[0]
            self.pretty_name(field1122)
            field1123 = unwrapped_fields1121[1]
            if not len(field1123) == 0:
                self.newline()
                for i1125, elem1124 in enumerate(field1123):
                    if (i1125 > 0):
                        self.newline()
                    self.pretty_term(elem1124)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1142 = self._try_flat(msg, self.pretty_primitive)
        if flat1142 is not None:
            assert flat1142 is not None
            self.write(flat1142)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1663 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1663 = None
            guard_result1141 = _t1663
            if guard_result1141 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1664 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1664 = None
                guard_result1140 = _t1664
                if guard_result1140 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1665 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1665 = None
                    guard_result1139 = _t1665
                    if guard_result1139 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1666 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1666 = None
                        guard_result1138 = _t1666
                        if guard_result1138 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1667 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1667 = None
                            guard_result1137 = _t1667
                            if guard_result1137 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1668 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1668 = None
                                guard_result1136 = _t1668
                                if guard_result1136 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1669 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1669 = None
                                    guard_result1135 = _t1669
                                    if guard_result1135 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1670 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1670 = None
                                        guard_result1134 = _t1670
                                        if guard_result1134 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1671 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1671 = None
                                            guard_result1133 = _t1671
                                            if guard_result1133 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1127 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1127 is not None
                                                unwrapped_fields1128 = fields1127
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1129 = unwrapped_fields1128[0]
                                                self.pretty_name(field1129)
                                                field1130 = unwrapped_fields1128[1]
                                                if not len(field1130) == 0:
                                                    self.newline()
                                                    for i1132, elem1131 in enumerate(field1130):
                                                        if (i1132 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1131)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1147 = self._try_flat(msg, self.pretty_eq)
        if flat1147 is not None:
            assert flat1147 is not None
            self.write(flat1147)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1672 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1672 = None
            fields1143 = _t1672
            assert fields1143 is not None
            unwrapped_fields1144 = fields1143
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1145 = unwrapped_fields1144[0]
            self.pretty_term(field1145)
            self.newline()
            field1146 = unwrapped_fields1144[1]
            self.pretty_term(field1146)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1152 = self._try_flat(msg, self.pretty_lt)
        if flat1152 is not None:
            assert flat1152 is not None
            self.write(flat1152)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1673 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1673 = None
            fields1148 = _t1673
            assert fields1148 is not None
            unwrapped_fields1149 = fields1148
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1150 = unwrapped_fields1149[0]
            self.pretty_term(field1150)
            self.newline()
            field1151 = unwrapped_fields1149[1]
            self.pretty_term(field1151)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1157 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1157 is not None:
            assert flat1157 is not None
            self.write(flat1157)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1674 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1674 = None
            fields1153 = _t1674
            assert fields1153 is not None
            unwrapped_fields1154 = fields1153
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1155 = unwrapped_fields1154[0]
            self.pretty_term(field1155)
            self.newline()
            field1156 = unwrapped_fields1154[1]
            self.pretty_term(field1156)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1162 = self._try_flat(msg, self.pretty_gt)
        if flat1162 is not None:
            assert flat1162 is not None
            self.write(flat1162)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1675 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1675 = None
            fields1158 = _t1675
            assert fields1158 is not None
            unwrapped_fields1159 = fields1158
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1160 = unwrapped_fields1159[0]
            self.pretty_term(field1160)
            self.newline()
            field1161 = unwrapped_fields1159[1]
            self.pretty_term(field1161)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1167 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1167 is not None:
            assert flat1167 is not None
            self.write(flat1167)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1676 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1676 = None
            fields1163 = _t1676
            assert fields1163 is not None
            unwrapped_fields1164 = fields1163
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1165 = unwrapped_fields1164[0]
            self.pretty_term(field1165)
            self.newline()
            field1166 = unwrapped_fields1164[1]
            self.pretty_term(field1166)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1173 = self._try_flat(msg, self.pretty_add)
        if flat1173 is not None:
            assert flat1173 is not None
            self.write(flat1173)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1677 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1677 = None
            fields1168 = _t1677
            assert fields1168 is not None
            unwrapped_fields1169 = fields1168
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1170 = unwrapped_fields1169[0]
            self.pretty_term(field1170)
            self.newline()
            field1171 = unwrapped_fields1169[1]
            self.pretty_term(field1171)
            self.newline()
            field1172 = unwrapped_fields1169[2]
            self.pretty_term(field1172)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1179 = self._try_flat(msg, self.pretty_minus)
        if flat1179 is not None:
            assert flat1179 is not None
            self.write(flat1179)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1678 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1678 = None
            fields1174 = _t1678
            assert fields1174 is not None
            unwrapped_fields1175 = fields1174
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1176 = unwrapped_fields1175[0]
            self.pretty_term(field1176)
            self.newline()
            field1177 = unwrapped_fields1175[1]
            self.pretty_term(field1177)
            self.newline()
            field1178 = unwrapped_fields1175[2]
            self.pretty_term(field1178)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1185 = self._try_flat(msg, self.pretty_multiply)
        if flat1185 is not None:
            assert flat1185 is not None
            self.write(flat1185)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1679 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1679 = None
            fields1180 = _t1679
            assert fields1180 is not None
            unwrapped_fields1181 = fields1180
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1182 = unwrapped_fields1181[0]
            self.pretty_term(field1182)
            self.newline()
            field1183 = unwrapped_fields1181[1]
            self.pretty_term(field1183)
            self.newline()
            field1184 = unwrapped_fields1181[2]
            self.pretty_term(field1184)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1191 = self._try_flat(msg, self.pretty_divide)
        if flat1191 is not None:
            assert flat1191 is not None
            self.write(flat1191)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1680 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1680 = None
            fields1186 = _t1680
            assert fields1186 is not None
            unwrapped_fields1187 = fields1186
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1188 = unwrapped_fields1187[0]
            self.pretty_term(field1188)
            self.newline()
            field1189 = unwrapped_fields1187[1]
            self.pretty_term(field1189)
            self.newline()
            field1190 = unwrapped_fields1187[2]
            self.pretty_term(field1190)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1196 = self._try_flat(msg, self.pretty_rel_term)
        if flat1196 is not None:
            assert flat1196 is not None
            self.write(flat1196)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1681 = _dollar_dollar.specialized_value
            else:
                _t1681 = None
            deconstruct_result1194 = _t1681
            if deconstruct_result1194 is not None:
                assert deconstruct_result1194 is not None
                unwrapped1195 = deconstruct_result1194
                self.pretty_specialized_value(unwrapped1195)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1682 = _dollar_dollar.term
                else:
                    _t1682 = None
                deconstruct_result1192 = _t1682
                if deconstruct_result1192 is not None:
                    assert deconstruct_result1192 is not None
                    unwrapped1193 = deconstruct_result1192
                    self.pretty_term(unwrapped1193)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1198 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1198 is not None:
            assert flat1198 is not None
            self.write(flat1198)
            return None
        else:
            fields1197 = msg
            self.write("#")
            self.pretty_raw_value(fields1197)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1205 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1205 is not None:
            assert flat1205 is not None
            self.write(flat1205)
            return None
        else:
            _dollar_dollar = msg
            fields1199 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1199 is not None
            unwrapped_fields1200 = fields1199
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1201 = unwrapped_fields1200[0]
            self.pretty_name(field1201)
            field1202 = unwrapped_fields1200[1]
            if not len(field1202) == 0:
                self.newline()
                for i1204, elem1203 in enumerate(field1202):
                    if (i1204 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1203)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1210 = self._try_flat(msg, self.pretty_cast)
        if flat1210 is not None:
            assert flat1210 is not None
            self.write(flat1210)
            return None
        else:
            _dollar_dollar = msg
            fields1206 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1206 is not None
            unwrapped_fields1207 = fields1206
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1208 = unwrapped_fields1207[0]
            self.pretty_term(field1208)
            self.newline()
            field1209 = unwrapped_fields1207[1]
            self.pretty_term(field1209)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1214 = self._try_flat(msg, self.pretty_attrs)
        if flat1214 is not None:
            assert flat1214 is not None
            self.write(flat1214)
            return None
        else:
            fields1211 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1211) == 0:
                self.newline()
                for i1213, elem1212 in enumerate(fields1211):
                    if (i1213 > 0):
                        self.newline()
                    self.pretty_attribute(elem1212)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1221 = self._try_flat(msg, self.pretty_attribute)
        if flat1221 is not None:
            assert flat1221 is not None
            self.write(flat1221)
            return None
        else:
            _dollar_dollar = msg
            fields1215 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1215 is not None
            unwrapped_fields1216 = fields1215
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1217 = unwrapped_fields1216[0]
            self.pretty_name(field1217)
            field1218 = unwrapped_fields1216[1]
            if not len(field1218) == 0:
                self.newline()
                for i1220, elem1219 in enumerate(field1218):
                    if (i1220 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1219)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1230 = self._try_flat(msg, self.pretty_algorithm)
        if flat1230 is not None:
            assert flat1230 is not None
            self.write(flat1230)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1683 = _dollar_dollar.attrs
            else:
                _t1683 = None
            fields1222 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body, _t1683,)
            assert fields1222 is not None
            unwrapped_fields1223 = fields1222
            self.write("(algorithm")
            self.indent_sexp()
            field1224 = unwrapped_fields1223[0]
            if not len(field1224) == 0:
                self.newline()
                for i1226, elem1225 in enumerate(field1224):
                    if (i1226 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1225)
            self.newline()
            field1227 = unwrapped_fields1223[1]
            self.pretty_script(field1227)
            field1228 = unwrapped_fields1223[2]
            if field1228 is not None:
                self.newline()
                assert field1228 is not None
                opt_val1229 = field1228
                self.pretty_attrs(opt_val1229)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1235 = self._try_flat(msg, self.pretty_script)
        if flat1235 is not None:
            assert flat1235 is not None
            self.write(flat1235)
            return None
        else:
            _dollar_dollar = msg
            fields1231 = _dollar_dollar.constructs
            assert fields1231 is not None
            unwrapped_fields1232 = fields1231
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1232) == 0:
                self.newline()
                for i1234, elem1233 in enumerate(unwrapped_fields1232):
                    if (i1234 > 0):
                        self.newline()
                    self.pretty_construct(elem1233)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1240 = self._try_flat(msg, self.pretty_construct)
        if flat1240 is not None:
            assert flat1240 is not None
            self.write(flat1240)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1684 = _dollar_dollar.loop
            else:
                _t1684 = None
            deconstruct_result1238 = _t1684
            if deconstruct_result1238 is not None:
                assert deconstruct_result1238 is not None
                unwrapped1239 = deconstruct_result1238
                self.pretty_loop(unwrapped1239)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1685 = _dollar_dollar.instruction
                else:
                    _t1685 = None
                deconstruct_result1236 = _t1685
                if deconstruct_result1236 is not None:
                    assert deconstruct_result1236 is not None
                    unwrapped1237 = deconstruct_result1236
                    self.pretty_instruction(unwrapped1237)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1247 = self._try_flat(msg, self.pretty_loop)
        if flat1247 is not None:
            assert flat1247 is not None
            self.write(flat1247)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1686 = _dollar_dollar.attrs
            else:
                _t1686 = None
            fields1241 = (_dollar_dollar.init, _dollar_dollar.body, _t1686,)
            assert fields1241 is not None
            unwrapped_fields1242 = fields1241
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1243 = unwrapped_fields1242[0]
            self.pretty_init(field1243)
            self.newline()
            field1244 = unwrapped_fields1242[1]
            self.pretty_script(field1244)
            field1245 = unwrapped_fields1242[2]
            if field1245 is not None:
                self.newline()
                assert field1245 is not None
                opt_val1246 = field1245
                self.pretty_attrs(opt_val1246)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1251 = self._try_flat(msg, self.pretty_init)
        if flat1251 is not None:
            assert flat1251 is not None
            self.write(flat1251)
            return None
        else:
            fields1248 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1248) == 0:
                self.newline()
                for i1250, elem1249 in enumerate(fields1248):
                    if (i1250 > 0):
                        self.newline()
                    self.pretty_instruction(elem1249)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1262 = self._try_flat(msg, self.pretty_instruction)
        if flat1262 is not None:
            assert flat1262 is not None
            self.write(flat1262)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1687 = _dollar_dollar.assign
            else:
                _t1687 = None
            deconstruct_result1260 = _t1687
            if deconstruct_result1260 is not None:
                assert deconstruct_result1260 is not None
                unwrapped1261 = deconstruct_result1260
                self.pretty_assign(unwrapped1261)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1688 = _dollar_dollar.upsert
                else:
                    _t1688 = None
                deconstruct_result1258 = _t1688
                if deconstruct_result1258 is not None:
                    assert deconstruct_result1258 is not None
                    unwrapped1259 = deconstruct_result1258
                    self.pretty_upsert(unwrapped1259)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1689 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1689 = None
                    deconstruct_result1256 = _t1689
                    if deconstruct_result1256 is not None:
                        assert deconstruct_result1256 is not None
                        unwrapped1257 = deconstruct_result1256
                        self.pretty_break(unwrapped1257)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1690 = _dollar_dollar.monoid_def
                        else:
                            _t1690 = None
                        deconstruct_result1254 = _t1690
                        if deconstruct_result1254 is not None:
                            assert deconstruct_result1254 is not None
                            unwrapped1255 = deconstruct_result1254
                            self.pretty_monoid_def(unwrapped1255)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1691 = _dollar_dollar.monus_def
                            else:
                                _t1691 = None
                            deconstruct_result1252 = _t1691
                            if deconstruct_result1252 is not None:
                                assert deconstruct_result1252 is not None
                                unwrapped1253 = deconstruct_result1252
                                self.pretty_monus_def(unwrapped1253)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1269 = self._try_flat(msg, self.pretty_assign)
        if flat1269 is not None:
            assert flat1269 is not None
            self.write(flat1269)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1692 = _dollar_dollar.attrs
            else:
                _t1692 = None
            fields1263 = (_dollar_dollar.name, _dollar_dollar.body, _t1692,)
            assert fields1263 is not None
            unwrapped_fields1264 = fields1263
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1265 = unwrapped_fields1264[0]
            self.pretty_relation_id(field1265)
            self.newline()
            field1266 = unwrapped_fields1264[1]
            self.pretty_abstraction(field1266)
            field1267 = unwrapped_fields1264[2]
            if field1267 is not None:
                self.newline()
                assert field1267 is not None
                opt_val1268 = field1267
                self.pretty_attrs(opt_val1268)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1276 = self._try_flat(msg, self.pretty_upsert)
        if flat1276 is not None:
            assert flat1276 is not None
            self.write(flat1276)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1693 = _dollar_dollar.attrs
            else:
                _t1693 = None
            fields1270 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1693,)
            assert fields1270 is not None
            unwrapped_fields1271 = fields1270
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1272 = unwrapped_fields1271[0]
            self.pretty_relation_id(field1272)
            self.newline()
            field1273 = unwrapped_fields1271[1]
            self.pretty_abstraction_with_arity(field1273)
            field1274 = unwrapped_fields1271[2]
            if field1274 is not None:
                self.newline()
                assert field1274 is not None
                opt_val1275 = field1274
                self.pretty_attrs(opt_val1275)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1281 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1281 is not None:
            assert flat1281 is not None
            self.write(flat1281)
            return None
        else:
            _dollar_dollar = msg
            _t1694 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1277 = (_t1694, _dollar_dollar[0].value,)
            assert fields1277 is not None
            unwrapped_fields1278 = fields1277
            self.write("(")
            self.indent()
            field1279 = unwrapped_fields1278[0]
            self.pretty_bindings(field1279)
            self.newline()
            field1280 = unwrapped_fields1278[1]
            self.pretty_formula(field1280)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1288 = self._try_flat(msg, self.pretty_break)
        if flat1288 is not None:
            assert flat1288 is not None
            self.write(flat1288)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1695 = _dollar_dollar.attrs
            else:
                _t1695 = None
            fields1282 = (_dollar_dollar.name, _dollar_dollar.body, _t1695,)
            assert fields1282 is not None
            unwrapped_fields1283 = fields1282
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1284 = unwrapped_fields1283[0]
            self.pretty_relation_id(field1284)
            self.newline()
            field1285 = unwrapped_fields1283[1]
            self.pretty_abstraction(field1285)
            field1286 = unwrapped_fields1283[2]
            if field1286 is not None:
                self.newline()
                assert field1286 is not None
                opt_val1287 = field1286
                self.pretty_attrs(opt_val1287)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1296 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1296 is not None:
            assert flat1296 is not None
            self.write(flat1296)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1696 = _dollar_dollar.attrs
            else:
                _t1696 = None
            fields1289 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1696,)
            assert fields1289 is not None
            unwrapped_fields1290 = fields1289
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1291 = unwrapped_fields1290[0]
            self.pretty_monoid(field1291)
            self.newline()
            field1292 = unwrapped_fields1290[1]
            self.pretty_relation_id(field1292)
            self.newline()
            field1293 = unwrapped_fields1290[2]
            self.pretty_abstraction_with_arity(field1293)
            field1294 = unwrapped_fields1290[3]
            if field1294 is not None:
                self.newline()
                assert field1294 is not None
                opt_val1295 = field1294
                self.pretty_attrs(opt_val1295)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1305 = self._try_flat(msg, self.pretty_monoid)
        if flat1305 is not None:
            assert flat1305 is not None
            self.write(flat1305)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1697 = _dollar_dollar.or_monoid
            else:
                _t1697 = None
            deconstruct_result1303 = _t1697
            if deconstruct_result1303 is not None:
                assert deconstruct_result1303 is not None
                unwrapped1304 = deconstruct_result1303
                self.pretty_or_monoid(unwrapped1304)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1698 = _dollar_dollar.min_monoid
                else:
                    _t1698 = None
                deconstruct_result1301 = _t1698
                if deconstruct_result1301 is not None:
                    assert deconstruct_result1301 is not None
                    unwrapped1302 = deconstruct_result1301
                    self.pretty_min_monoid(unwrapped1302)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1699 = _dollar_dollar.max_monoid
                    else:
                        _t1699 = None
                    deconstruct_result1299 = _t1699
                    if deconstruct_result1299 is not None:
                        assert deconstruct_result1299 is not None
                        unwrapped1300 = deconstruct_result1299
                        self.pretty_max_monoid(unwrapped1300)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1700 = _dollar_dollar.sum_monoid
                        else:
                            _t1700 = None
                        deconstruct_result1297 = _t1700
                        if deconstruct_result1297 is not None:
                            assert deconstruct_result1297 is not None
                            unwrapped1298 = deconstruct_result1297
                            self.pretty_sum_monoid(unwrapped1298)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1306 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1309 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1309 is not None:
            assert flat1309 is not None
            self.write(flat1309)
            return None
        else:
            _dollar_dollar = msg
            fields1307 = _dollar_dollar.type
            assert fields1307 is not None
            unwrapped_fields1308 = fields1307
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1308)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1312 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1312 is not None:
            assert flat1312 is not None
            self.write(flat1312)
            return None
        else:
            _dollar_dollar = msg
            fields1310 = _dollar_dollar.type
            assert fields1310 is not None
            unwrapped_fields1311 = fields1310
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1311)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1315 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1315 is not None:
            assert flat1315 is not None
            self.write(flat1315)
            return None
        else:
            _dollar_dollar = msg
            fields1313 = _dollar_dollar.type
            assert fields1313 is not None
            unwrapped_fields1314 = fields1313
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1314)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1323 = self._try_flat(msg, self.pretty_monus_def)
        if flat1323 is not None:
            assert flat1323 is not None
            self.write(flat1323)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1701 = _dollar_dollar.attrs
            else:
                _t1701 = None
            fields1316 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1701,)
            assert fields1316 is not None
            unwrapped_fields1317 = fields1316
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1318 = unwrapped_fields1317[0]
            self.pretty_monoid(field1318)
            self.newline()
            field1319 = unwrapped_fields1317[1]
            self.pretty_relation_id(field1319)
            self.newline()
            field1320 = unwrapped_fields1317[2]
            self.pretty_abstraction_with_arity(field1320)
            field1321 = unwrapped_fields1317[3]
            if field1321 is not None:
                self.newline()
                assert field1321 is not None
                opt_val1322 = field1321
                self.pretty_attrs(opt_val1322)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1330 = self._try_flat(msg, self.pretty_constraint)
        if flat1330 is not None:
            assert flat1330 is not None
            self.write(flat1330)
            return None
        else:
            _dollar_dollar = msg
            fields1324 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1324 is not None
            unwrapped_fields1325 = fields1324
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1326 = unwrapped_fields1325[0]
            self.pretty_relation_id(field1326)
            self.newline()
            field1327 = unwrapped_fields1325[1]
            self.pretty_abstraction(field1327)
            self.newline()
            field1328 = unwrapped_fields1325[2]
            self.pretty_functional_dependency_keys(field1328)
            self.newline()
            field1329 = unwrapped_fields1325[3]
            self.pretty_functional_dependency_values(field1329)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1334 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1334 is not None:
            assert flat1334 is not None
            self.write(flat1334)
            return None
        else:
            fields1331 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1331) == 0:
                self.newline()
                for i1333, elem1332 in enumerate(fields1331):
                    if (i1333 > 0):
                        self.newline()
                    self.pretty_var(elem1332)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1338 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1338 is not None:
            assert flat1338 is not None
            self.write(flat1338)
            return None
        else:
            fields1335 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1335) == 0:
                self.newline()
                for i1337, elem1336 in enumerate(fields1335):
                    if (i1337 > 0):
                        self.newline()
                    self.pretty_var(elem1336)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1347 = self._try_flat(msg, self.pretty_data)
        if flat1347 is not None:
            assert flat1347 is not None
            self.write(flat1347)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1702 = _dollar_dollar.edb
            else:
                _t1702 = None
            deconstruct_result1345 = _t1702
            if deconstruct_result1345 is not None:
                assert deconstruct_result1345 is not None
                unwrapped1346 = deconstruct_result1345
                self.pretty_edb(unwrapped1346)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1703 = _dollar_dollar.betree_relation
                else:
                    _t1703 = None
                deconstruct_result1343 = _t1703
                if deconstruct_result1343 is not None:
                    assert deconstruct_result1343 is not None
                    unwrapped1344 = deconstruct_result1343
                    self.pretty_betree_relation(unwrapped1344)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1704 = _dollar_dollar.csv_data
                    else:
                        _t1704 = None
                    deconstruct_result1341 = _t1704
                    if deconstruct_result1341 is not None:
                        assert deconstruct_result1341 is not None
                        unwrapped1342 = deconstruct_result1341
                        self.pretty_csv_data(unwrapped1342)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1705 = _dollar_dollar.iceberg_data
                        else:
                            _t1705 = None
                        deconstruct_result1339 = _t1705
                        if deconstruct_result1339 is not None:
                            assert deconstruct_result1339 is not None
                            unwrapped1340 = deconstruct_result1339
                            self.pretty_iceberg_data(unwrapped1340)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1353 = self._try_flat(msg, self.pretty_edb)
        if flat1353 is not None:
            assert flat1353 is not None
            self.write(flat1353)
            return None
        else:
            _dollar_dollar = msg
            fields1348 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1348 is not None
            unwrapped_fields1349 = fields1348
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1350 = unwrapped_fields1349[0]
            self.pretty_relation_id(field1350)
            self.newline()
            field1351 = unwrapped_fields1349[1]
            self.pretty_edb_path(field1351)
            self.newline()
            field1352 = unwrapped_fields1349[2]
            self.pretty_edb_types(field1352)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1357 = self._try_flat(msg, self.pretty_edb_path)
        if flat1357 is not None:
            assert flat1357 is not None
            self.write(flat1357)
            return None
        else:
            fields1354 = msg
            self.write("[")
            self.indent()
            for i1356, elem1355 in enumerate(fields1354):
                if (i1356 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1355))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1361 = self._try_flat(msg, self.pretty_edb_types)
        if flat1361 is not None:
            assert flat1361 is not None
            self.write(flat1361)
            return None
        else:
            fields1358 = msg
            self.write("[")
            self.indent()
            for i1360, elem1359 in enumerate(fields1358):
                if (i1360 > 0):
                    self.newline()
                self.pretty_type(elem1359)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1366 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1366 is not None:
            assert flat1366 is not None
            self.write(flat1366)
            return None
        else:
            _dollar_dollar = msg
            fields1362 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1362 is not None
            unwrapped_fields1363 = fields1362
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1364 = unwrapped_fields1363[0]
            self.pretty_relation_id(field1364)
            self.newline()
            field1365 = unwrapped_fields1363[1]
            self.pretty_betree_info(field1365)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1372 = self._try_flat(msg, self.pretty_betree_info)
        if flat1372 is not None:
            assert flat1372 is not None
            self.write(flat1372)
            return None
        else:
            _dollar_dollar = msg
            _t1706 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1367 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1706,)
            assert fields1367 is not None
            unwrapped_fields1368 = fields1367
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1369 = unwrapped_fields1368[0]
            self.pretty_betree_info_key_types(field1369)
            self.newline()
            field1370 = unwrapped_fields1368[1]
            self.pretty_betree_info_value_types(field1370)
            self.newline()
            field1371 = unwrapped_fields1368[2]
            self.pretty_config_dict(field1371)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1376 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1376 is not None:
            assert flat1376 is not None
            self.write(flat1376)
            return None
        else:
            fields1373 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1373) == 0:
                self.newline()
                for i1375, elem1374 in enumerate(fields1373):
                    if (i1375 > 0):
                        self.newline()
                    self.pretty_type(elem1374)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1380 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1380 is not None:
            assert flat1380 is not None
            self.write(flat1380)
            return None
        else:
            fields1377 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1377) == 0:
                self.newline()
                for i1379, elem1378 in enumerate(fields1377):
                    if (i1379 > 0):
                        self.newline()
                    self.pretty_type(elem1378)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1387 = self._try_flat(msg, self.pretty_csv_data)
        if flat1387 is not None:
            assert flat1387 is not None
            self.write(flat1387)
            return None
        else:
            _dollar_dollar = msg
            fields1381 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1381 is not None
            unwrapped_fields1382 = fields1381
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1383 = unwrapped_fields1382[0]
            self.pretty_csvlocator(field1383)
            self.newline()
            field1384 = unwrapped_fields1382[1]
            self.pretty_csv_config(field1384)
            self.newline()
            field1385 = unwrapped_fields1382[2]
            self.pretty_gnf_columns(field1385)
            self.newline()
            field1386 = unwrapped_fields1382[3]
            self.pretty_csv_asof(field1386)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1394 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1394 is not None:
            assert flat1394 is not None
            self.write(flat1394)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1707 = _dollar_dollar.paths
            else:
                _t1707 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1708 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1708 = None
            fields1388 = (_t1707, _t1708,)
            assert fields1388 is not None
            unwrapped_fields1389 = fields1388
            self.write("(csv_locator")
            self.indent_sexp()
            field1390 = unwrapped_fields1389[0]
            if field1390 is not None:
                self.newline()
                assert field1390 is not None
                opt_val1391 = field1390
                self.pretty_csv_locator_paths(opt_val1391)
            field1392 = unwrapped_fields1389[1]
            if field1392 is not None:
                self.newline()
                assert field1392 is not None
                opt_val1393 = field1392
                self.pretty_csv_locator_inline_data(opt_val1393)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1398 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1398 is not None:
            assert flat1398 is not None
            self.write(flat1398)
            return None
        else:
            fields1395 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1395) == 0:
                self.newline()
                for i1397, elem1396 in enumerate(fields1395):
                    if (i1397 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1396))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1400 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1400 is not None:
            assert flat1400 is not None
            self.write(flat1400)
            return None
        else:
            fields1399 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1399))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1403 = self._try_flat(msg, self.pretty_csv_config)
        if flat1403 is not None:
            assert flat1403 is not None
            self.write(flat1403)
            return None
        else:
            _dollar_dollar = msg
            _t1709 = self.deconstruct_csv_config(_dollar_dollar)
            fields1401 = _t1709
            assert fields1401 is not None
            unwrapped_fields1402 = fields1401
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1402)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1407 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1407 is not None:
            assert flat1407 is not None
            self.write(flat1407)
            return None
        else:
            fields1404 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1404) == 0:
                self.newline()
                for i1406, elem1405 in enumerate(fields1404):
                    if (i1406 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1405)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1416 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1416 is not None:
            assert flat1416 is not None
            self.write(flat1416)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1710 = _dollar_dollar.target_id
            else:
                _t1710 = None
            fields1408 = (_dollar_dollar.column_path, _t1710, _dollar_dollar.types,)
            assert fields1408 is not None
            unwrapped_fields1409 = fields1408
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1410 = unwrapped_fields1409[0]
            self.pretty_gnf_column_path(field1410)
            field1411 = unwrapped_fields1409[1]
            if field1411 is not None:
                self.newline()
                assert field1411 is not None
                opt_val1412 = field1411
                self.pretty_relation_id(opt_val1412)
            self.newline()
            self.write("[")
            field1413 = unwrapped_fields1409[2]
            for i1415, elem1414 in enumerate(field1413):
                if (i1415 > 0):
                    self.newline()
                self.pretty_type(elem1414)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1423 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1423 is not None:
            assert flat1423 is not None
            self.write(flat1423)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1711 = _dollar_dollar[0]
            else:
                _t1711 = None
            deconstruct_result1421 = _t1711
            if deconstruct_result1421 is not None:
                assert deconstruct_result1421 is not None
                unwrapped1422 = deconstruct_result1421
                self.write(self.format_string_value(unwrapped1422))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1712 = _dollar_dollar
                else:
                    _t1712 = None
                deconstruct_result1417 = _t1712
                if deconstruct_result1417 is not None:
                    assert deconstruct_result1417 is not None
                    unwrapped1418 = deconstruct_result1417
                    self.write("[")
                    self.indent()
                    for i1420, elem1419 in enumerate(unwrapped1418):
                        if (i1420 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1419))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1425 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1425 is not None:
            assert flat1425 is not None
            self.write(flat1425)
            return None
        else:
            fields1424 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1424))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1436 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1436 is not None:
            assert flat1436 is not None
            self.write(flat1436)
            return None
        else:
            _dollar_dollar = msg
            _t1713 = self.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
            _t1714 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1426 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1713, _t1714, _dollar_dollar.returns_delta,)
            assert fields1426 is not None
            unwrapped_fields1427 = fields1426
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1428 = unwrapped_fields1427[0]
            self.pretty_iceberg_locator(field1428)
            self.newline()
            field1429 = unwrapped_fields1427[1]
            self.pretty_iceberg_catalog_config(field1429)
            self.newline()
            field1430 = unwrapped_fields1427[2]
            self.pretty_gnf_columns(field1430)
            field1431 = unwrapped_fields1427[3]
            if field1431 is not None:
                self.newline()
                assert field1431 is not None
                opt_val1432 = field1431
                self.pretty_iceberg_from_snapshot(opt_val1432)
            field1433 = unwrapped_fields1427[4]
            if field1433 is not None:
                self.newline()
                assert field1433 is not None
                opt_val1434 = field1433
                self.pretty_iceberg_to_snapshot(opt_val1434)
            self.newline()
            field1435 = unwrapped_fields1427[5]
            self.pretty_boolean_value(field1435)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1442 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1442 is not None:
            assert flat1442 is not None
            self.write(flat1442)
            return None
        else:
            _dollar_dollar = msg
            fields1437 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1437 is not None
            unwrapped_fields1438 = fields1437
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            field1439 = unwrapped_fields1438[0]
            self.pretty_iceberg_locator_table_name(field1439)
            self.newline()
            field1440 = unwrapped_fields1438[1]
            self.pretty_iceberg_locator_namespace(field1440)
            self.newline()
            field1441 = unwrapped_fields1438[2]
            self.pretty_iceberg_locator_warehouse(field1441)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_table_name(self, msg: str):
        flat1444 = self._try_flat(msg, self.pretty_iceberg_locator_table_name)
        if flat1444 is not None:
            assert flat1444 is not None
            self.write(flat1444)
            return None
        else:
            fields1443 = msg
            self.write("(table_name")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1443))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_namespace(self, msg: Sequence[str]):
        flat1448 = self._try_flat(msg, self.pretty_iceberg_locator_namespace)
        if flat1448 is not None:
            assert flat1448 is not None
            self.write(flat1448)
            return None
        else:
            fields1445 = msg
            self.write("(namespace")
            self.indent_sexp()
            if not len(fields1445) == 0:
                self.newline()
                for i1447, elem1446 in enumerate(fields1445):
                    if (i1447 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1446))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_warehouse(self, msg: str):
        flat1450 = self._try_flat(msg, self.pretty_iceberg_locator_warehouse)
        if flat1450 is not None:
            assert flat1450 is not None
            self.write(flat1450)
            return None
        else:
            fields1449 = msg
            self.write("(warehouse")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1449))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1458 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1458 is not None:
            assert flat1458 is not None
            self.write(flat1458)
            return None
        else:
            _dollar_dollar = msg
            _t1715 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1451 = (_dollar_dollar.catalog_uri, _t1715, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1451 is not None
            unwrapped_fields1452 = fields1451
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            field1453 = unwrapped_fields1452[0]
            self.pretty_iceberg_catalog_uri(field1453)
            field1454 = unwrapped_fields1452[1]
            if field1454 is not None:
                self.newline()
                assert field1454 is not None
                opt_val1455 = field1454
                self.pretty_iceberg_catalog_config_scope(opt_val1455)
            self.newline()
            field1456 = unwrapped_fields1452[2]
            self.pretty_iceberg_properties(field1456)
            self.newline()
            field1457 = unwrapped_fields1452[3]
            self.pretty_iceberg_auth_properties(field1457)
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_uri(self, msg: str):
        flat1460 = self._try_flat(msg, self.pretty_iceberg_catalog_uri)
        if flat1460 is not None:
            assert flat1460 is not None
            self.write(flat1460)
            return None
        else:
            fields1459 = msg
            self.write("(catalog_uri")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1459))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1462 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1462 is not None:
            assert flat1462 is not None
            self.write(flat1462)
            return None
        else:
            fields1461 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1461))
            self.dedent()
            self.write(")")

    def pretty_iceberg_properties(self, msg: Sequence[tuple[str, str]]):
        flat1466 = self._try_flat(msg, self.pretty_iceberg_properties)
        if flat1466 is not None:
            assert flat1466 is not None
            self.write(flat1466)
            return None
        else:
            fields1463 = msg
            self.write("(properties")
            self.indent_sexp()
            if not len(fields1463) == 0:
                self.newline()
                for i1465, elem1464 in enumerate(fields1463):
                    if (i1465 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1464)
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1471 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1471 is not None:
            assert flat1471 is not None
            self.write(flat1471)
            return None
        else:
            _dollar_dollar = msg
            fields1467 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1467 is not None
            unwrapped_fields1468 = fields1467
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1469 = unwrapped_fields1468[0]
            self.write(self.format_string_value(field1469))
            self.newline()
            field1470 = unwrapped_fields1468[1]
            self.write(self.format_string_value(field1470))
            self.dedent()
            self.write(")")

    def pretty_iceberg_auth_properties(self, msg: Sequence[tuple[str, str]]):
        flat1475 = self._try_flat(msg, self.pretty_iceberg_auth_properties)
        if flat1475 is not None:
            assert flat1475 is not None
            self.write(flat1475)
            return None
        else:
            fields1472 = msg
            self.write("(auth_properties")
            self.indent_sexp()
            if not len(fields1472) == 0:
                self.newline()
                for i1474, elem1473 in enumerate(fields1472):
                    if (i1474 > 0):
                        self.newline()
                    self.pretty_iceberg_masked_property_entry(elem1473)
            self.dedent()
            self.write(")")

    def pretty_iceberg_masked_property_entry(self, msg: tuple[str, str]):
        flat1480 = self._try_flat(msg, self.pretty_iceberg_masked_property_entry)
        if flat1480 is not None:
            assert flat1480 is not None
            self.write(flat1480)
            return None
        else:
            _dollar_dollar = msg
            _t1716 = self.mask_secret_value(_dollar_dollar)
            fields1476 = (_dollar_dollar[0], _t1716,)
            assert fields1476 is not None
            unwrapped_fields1477 = fields1476
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1478 = unwrapped_fields1477[0]
            self.write(self.format_string_value(field1478))
            self.newline()
            field1479 = unwrapped_fields1477[1]
            self.write(self.format_string_value(field1479))
            self.dedent()
            self.write(")")

    def pretty_iceberg_from_snapshot(self, msg: str):
        flat1482 = self._try_flat(msg, self.pretty_iceberg_from_snapshot)
        if flat1482 is not None:
            assert flat1482 is not None
            self.write(flat1482)
            return None
        else:
            fields1481 = msg
            self.write("(from_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1481))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1484 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1484 is not None:
            assert flat1484 is not None
            self.write(flat1484)
            return None
        else:
            fields1483 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1483))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1487 = self._try_flat(msg, self.pretty_undefine)
        if flat1487 is not None:
            assert flat1487 is not None
            self.write(flat1487)
            return None
        else:
            _dollar_dollar = msg
            fields1485 = _dollar_dollar.fragment_id
            assert fields1485 is not None
            unwrapped_fields1486 = fields1485
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1486)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1492 = self._try_flat(msg, self.pretty_context)
        if flat1492 is not None:
            assert flat1492 is not None
            self.write(flat1492)
            return None
        else:
            _dollar_dollar = msg
            fields1488 = _dollar_dollar.relations
            assert fields1488 is not None
            unwrapped_fields1489 = fields1488
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1489) == 0:
                self.newline()
                for i1491, elem1490 in enumerate(unwrapped_fields1489):
                    if (i1491 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1490)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1499 = self._try_flat(msg, self.pretty_snapshot)
        if flat1499 is not None:
            assert flat1499 is not None
            self.write(flat1499)
            return None
        else:
            _dollar_dollar = msg
            fields1493 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
            assert fields1493 is not None
            unwrapped_fields1494 = fields1493
            self.write("(snapshot")
            self.indent_sexp()
            self.newline()
            field1495 = unwrapped_fields1494[0]
            self.pretty_edb_path(field1495)
            field1496 = unwrapped_fields1494[1]
            if not len(field1496) == 0:
                self.newline()
                for i1498, elem1497 in enumerate(field1496):
                    if (i1498 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1497)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1504 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1504 is not None:
            assert flat1504 is not None
            self.write(flat1504)
            return None
        else:
            _dollar_dollar = msg
            fields1500 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1500 is not None
            unwrapped_fields1501 = fields1500
            field1502 = unwrapped_fields1501[0]
            self.pretty_edb_path(field1502)
            self.write(" ")
            field1503 = unwrapped_fields1501[1]
            self.pretty_relation_id(field1503)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1508 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1508 is not None:
            assert flat1508 is not None
            self.write(flat1508)
            return None
        else:
            fields1505 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1505) == 0:
                self.newline()
                for i1507, elem1506 in enumerate(fields1505):
                    if (i1507 > 0):
                        self.newline()
                    self.pretty_read(elem1506)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1519 = self._try_flat(msg, self.pretty_read)
        if flat1519 is not None:
            assert flat1519 is not None
            self.write(flat1519)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1717 = _dollar_dollar.demand
            else:
                _t1717 = None
            deconstruct_result1517 = _t1717
            if deconstruct_result1517 is not None:
                assert deconstruct_result1517 is not None
                unwrapped1518 = deconstruct_result1517
                self.pretty_demand(unwrapped1518)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1718 = _dollar_dollar.output
                else:
                    _t1718 = None
                deconstruct_result1515 = _t1718
                if deconstruct_result1515 is not None:
                    assert deconstruct_result1515 is not None
                    unwrapped1516 = deconstruct_result1515
                    self.pretty_output(unwrapped1516)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1719 = _dollar_dollar.what_if
                    else:
                        _t1719 = None
                    deconstruct_result1513 = _t1719
                    if deconstruct_result1513 is not None:
                        assert deconstruct_result1513 is not None
                        unwrapped1514 = deconstruct_result1513
                        self.pretty_what_if(unwrapped1514)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1720 = _dollar_dollar.abort
                        else:
                            _t1720 = None
                        deconstruct_result1511 = _t1720
                        if deconstruct_result1511 is not None:
                            assert deconstruct_result1511 is not None
                            unwrapped1512 = deconstruct_result1511
                            self.pretty_abort(unwrapped1512)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1721 = _dollar_dollar.export
                            else:
                                _t1721 = None
                            deconstruct_result1509 = _t1721
                            if deconstruct_result1509 is not None:
                                assert deconstruct_result1509 is not None
                                unwrapped1510 = deconstruct_result1509
                                self.pretty_export(unwrapped1510)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1522 = self._try_flat(msg, self.pretty_demand)
        if flat1522 is not None:
            assert flat1522 is not None
            self.write(flat1522)
            return None
        else:
            _dollar_dollar = msg
            fields1520 = _dollar_dollar.relation_id
            assert fields1520 is not None
            unwrapped_fields1521 = fields1520
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1521)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1527 = self._try_flat(msg, self.pretty_output)
        if flat1527 is not None:
            assert flat1527 is not None
            self.write(flat1527)
            return None
        else:
            _dollar_dollar = msg
            fields1523 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1523 is not None
            unwrapped_fields1524 = fields1523
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1525 = unwrapped_fields1524[0]
            self.pretty_name(field1525)
            self.newline()
            field1526 = unwrapped_fields1524[1]
            self.pretty_relation_id(field1526)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1532 = self._try_flat(msg, self.pretty_what_if)
        if flat1532 is not None:
            assert flat1532 is not None
            self.write(flat1532)
            return None
        else:
            _dollar_dollar = msg
            fields1528 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1528 is not None
            unwrapped_fields1529 = fields1528
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1530 = unwrapped_fields1529[0]
            self.pretty_name(field1530)
            self.newline()
            field1531 = unwrapped_fields1529[1]
            self.pretty_epoch(field1531)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1538 = self._try_flat(msg, self.pretty_abort)
        if flat1538 is not None:
            assert flat1538 is not None
            self.write(flat1538)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1722 = _dollar_dollar.name
            else:
                _t1722 = None
            fields1533 = (_t1722, _dollar_dollar.relation_id,)
            assert fields1533 is not None
            unwrapped_fields1534 = fields1533
            self.write("(abort")
            self.indent_sexp()
            field1535 = unwrapped_fields1534[0]
            if field1535 is not None:
                self.newline()
                assert field1535 is not None
                opt_val1536 = field1535
                self.pretty_name(opt_val1536)
            self.newline()
            field1537 = unwrapped_fields1534[1]
            self.pretty_relation_id(field1537)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1543 = self._try_flat(msg, self.pretty_export)
        if flat1543 is not None:
            assert flat1543 is not None
            self.write(flat1543)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1723 = _dollar_dollar.csv_config
            else:
                _t1723 = None
            deconstruct_result1541 = _t1723
            if deconstruct_result1541 is not None:
                assert deconstruct_result1541 is not None
                unwrapped1542 = deconstruct_result1541
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1542)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1724 = _dollar_dollar.iceberg_config
                else:
                    _t1724 = None
                deconstruct_result1539 = _t1724
                if deconstruct_result1539 is not None:
                    assert deconstruct_result1539 is not None
                    unwrapped1540 = deconstruct_result1539
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1540)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1554 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1554 is not None:
            assert flat1554 is not None
            self.write(flat1554)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1725 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1725 = None
            deconstruct_result1549 = _t1725
            if deconstruct_result1549 is not None:
                assert deconstruct_result1549 is not None
                unwrapped1550 = deconstruct_result1549
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1551 = unwrapped1550[0]
                self.pretty_export_csv_path(field1551)
                self.newline()
                field1552 = unwrapped1550[1]
                self.pretty_export_csv_source(field1552)
                self.newline()
                field1553 = unwrapped1550[2]
                self.pretty_csv_config(field1553)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1727 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1726 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1727,)
                else:
                    _t1726 = None
                deconstruct_result1544 = _t1726
                if deconstruct_result1544 is not None:
                    assert deconstruct_result1544 is not None
                    unwrapped1545 = deconstruct_result1544
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1546 = unwrapped1545[0]
                    self.pretty_export_csv_path(field1546)
                    self.newline()
                    field1547 = unwrapped1545[1]
                    self.pretty_export_csv_columns_list(field1547)
                    self.newline()
                    field1548 = unwrapped1545[2]
                    self.pretty_config_dict(field1548)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1556 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1556 is not None:
            assert flat1556 is not None
            self.write(flat1556)
            return None
        else:
            fields1555 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1555))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1563 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1563 is not None:
            assert flat1563 is not None
            self.write(flat1563)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1728 = _dollar_dollar.gnf_columns.columns
            else:
                _t1728 = None
            deconstruct_result1559 = _t1728
            if deconstruct_result1559 is not None:
                assert deconstruct_result1559 is not None
                unwrapped1560 = deconstruct_result1559
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1560) == 0:
                    self.newline()
                    for i1562, elem1561 in enumerate(unwrapped1560):
                        if (i1562 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1561)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1729 = _dollar_dollar.table_def
                else:
                    _t1729 = None
                deconstruct_result1557 = _t1729
                if deconstruct_result1557 is not None:
                    assert deconstruct_result1557 is not None
                    unwrapped1558 = deconstruct_result1557
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1558)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1568 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1568 is not None:
            assert flat1568 is not None
            self.write(flat1568)
            return None
        else:
            _dollar_dollar = msg
            fields1564 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1564 is not None
            unwrapped_fields1565 = fields1564
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1566 = unwrapped_fields1565[0]
            self.write(self.format_string_value(field1566))
            self.newline()
            field1567 = unwrapped_fields1565[1]
            self.pretty_relation_id(field1567)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1572 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1572 is not None:
            assert flat1572 is not None
            self.write(flat1572)
            return None
        else:
            fields1569 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1569) == 0:
                self.newline()
                for i1571, elem1570 in enumerate(fields1569):
                    if (i1571 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1570)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1581 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1581 is not None:
            assert flat1581 is not None
            self.write(flat1581)
            return None
        else:
            _dollar_dollar = msg
            _t1730 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1573 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sorted(_dollar_dollar.table_properties.items()), _t1730,)
            assert fields1573 is not None
            unwrapped_fields1574 = fields1573
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1575 = unwrapped_fields1574[0]
            self.pretty_iceberg_locator(field1575)
            self.newline()
            field1576 = unwrapped_fields1574[1]
            self.pretty_iceberg_catalog_config(field1576)
            self.newline()
            field1577 = unwrapped_fields1574[2]
            self.pretty_export_iceberg_table_def(field1577)
            self.newline()
            field1578 = unwrapped_fields1574[3]
            self.pretty_iceberg_table_properties(field1578)
            field1579 = unwrapped_fields1574[4]
            if field1579 is not None:
                self.newline()
                assert field1579 is not None
                opt_val1580 = field1579
                self.pretty_config_dict(opt_val1580)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_table_def(self, msg: logic_pb2.RelationId):
        flat1583 = self._try_flat(msg, self.pretty_export_iceberg_table_def)
        if flat1583 is not None:
            assert flat1583 is not None
            self.write(flat1583)
            return None
        else:
            fields1582 = msg
            self.write("(table_def")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1582)
            self.dedent()
            self.write(")")

    def pretty_iceberg_table_properties(self, msg: Sequence[tuple[str, str]]):
        flat1587 = self._try_flat(msg, self.pretty_iceberg_table_properties)
        if flat1587 is not None:
            assert flat1587 is not None
            self.write(flat1587)
            return None
        else:
            fields1584 = msg
            self.write("(table_properties")
            self.indent_sexp()
            if not len(fields1584) == 0:
                self.newline()
                for i1586, elem1585 in enumerate(fields1584):
                    if (i1586 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1585)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1776 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1776)
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
        self.write(":keys (")
        for _idx, _elem in enumerate(msg.keys):
            if (_idx > 0):
                self.write(" ")
            self.pprint_dispatch(_elem)
        self.write(")")
        self.newline()
        self.write(":values (")
        for _idx, _elem in enumerate(msg.values):
            if (_idx > 0):
                self.write(" ")
            self.pprint_dispatch(_elem)
        self.write("))")
        self.dedent()

    def pretty_int128_value(self, msg: logic_pb2.Int128Value):
        self.write(self.format_int128(msg))

    def pretty_missing_value(self, msg: logic_pb2.MissingValue):
        self.write("missing")

    def pretty_u_int128_value(self, msg: logic_pb2.UInt128Value):
        self.write(self.format_uint128(msg))

    def pretty_export_csv_columns(self, msg: transactions_pb2.ExportCSVColumns):
        self.write("(export_csv_columns")
        self.indent_sexp()
        self.newline()
        self.write(":columns (")
        for _idx, _elem in enumerate(msg.columns):
            if (_idx > 0):
                self.write(" ")
            self.pprint_dispatch(_elem)
        self.write("))")
        self.dedent()

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
            self.pretty_raw_date(msg)
        elif isinstance(msg, logic_pb2.DateTimeValue):
            self.pretty_raw_datetime(msg)
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
        elif isinstance(msg, logic_pb2.Int32Type):
            self.pretty_int32_type(msg)
        elif isinstance(msg, logic_pb2.Float32Type):
            self.pretty_float32_type(msg)
        elif isinstance(msg, logic_pb2.UInt32Type):
            self.pretty_uint32_type(msg)
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
        elif isinstance(msg, logic_pb2.EDB):
            self.pretty_edb(msg)
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
        elif isinstance(msg, logic_pb2.GNFColumn):
            self.pretty_gnf_column(msg)
        elif isinstance(msg, logic_pb2.IcebergData):
            self.pretty_iceberg_data(msg)
        elif isinstance(msg, logic_pb2.IcebergLocator):
            self.pretty_iceberg_locator(msg)
        elif isinstance(msg, logic_pb2.IcebergCatalogConfig):
            self.pretty_iceberg_catalog_config(msg)
        elif isinstance(msg, transactions_pb2.Undefine):
            self.pretty_undefine(msg)
        elif isinstance(msg, transactions_pb2.Context):
            self.pretty_context(msg)
        elif isinstance(msg, transactions_pb2.Snapshot):
            self.pretty_snapshot(msg)
        elif isinstance(msg, transactions_pb2.SnapshotMapping):
            self.pretty_snapshot_mapping(msg)
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
        elif isinstance(msg, transactions_pb2.ExportCSVSource):
            self.pretty_export_csv_source(msg)
        elif isinstance(msg, transactions_pb2.ExportCSVColumn):
            self.pretty_export_csv_column(msg)
        elif isinstance(msg, transactions_pb2.ExportIcebergConfig):
            self.pretty_export_iceberg_config(msg)
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
        elif isinstance(msg, transactions_pb2.ExportCSVColumns):
            self.pretty_export_csv_columns(msg)
        elif isinstance(msg, transactions_pb2.IVMConfig):
            self.pretty_ivm_config(msg)
        # enum: int
        elif isinstance(msg, int):
            self.pretty_maintenance_level(msg)
        else:
            raise ParseError(f"no pretty printer for {type(msg)}")

def pretty(msg: Any, io: IO[str] | None = None, max_width: int = 92) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io, max_width=max_width)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()


def pretty_debug(msg: Any, io: IO[str] | None = None, max_width: int = 92) -> str:
    """Pretty print a protobuf message with raw relation IDs and debug info appended as comments."""
    printer = PrettyPrinter(io, max_width=max_width, print_symbolic_relation_ids=False)
    printer.pretty_transaction(msg)
    printer.newline()
    printer.write_debug_info()
    return printer.get_output()
