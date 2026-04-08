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
        _t1741 = logic_pb2.Value(int32_value=v)
        return _t1741

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1742 = logic_pb2.Value(int_value=v)
        return _t1742

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1743 = logic_pb2.Value(float_value=v)
        return _t1743

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1744 = logic_pb2.Value(string_value=v)
        return _t1744

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1745 = logic_pb2.Value(boolean_value=v)
        return _t1745

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1746 = logic_pb2.Value(uint128_value=v)
        return _t1746

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1747 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1747,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1748 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1748,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1749 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1749,))
        _t1750 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1750,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1751 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1751,))
        _t1752 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1752,))
        if msg.new_line != "":
            _t1753 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1753,))
        _t1754 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1754,))
        _t1755 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1755,))
        _t1756 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1756,))
        if msg.comment != "":
            _t1757 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1757,))
        for missing_string in msg.missing_strings:
            _t1758 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1758,))
        _t1759 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1759,))
        _t1760 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1760,))
        _t1761 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1761,))
        if msg.partition_size_mb != 0:
            _t1762 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1762,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1763 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1763,))
        _t1764 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1764,))
        _t1765 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1765,))
        _t1766 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1766,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1767 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1767,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1768 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1768,))
        _t1769 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1769,))
        _t1770 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1770,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1771 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1771,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1772 = self._make_value_string(msg.compression)
            result.append(("compression", _t1772,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1773 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1773,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1774 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1774,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1775 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1775,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1776 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1776,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1777 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1777,))
        return sorted(result)

    def mask_secret_value(self, pair: tuple[str, str]) -> str:
        return "***"

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1778 = None
        return None

    def deconstruct_iceberg_data_from_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.from_snapshot is not None
        if msg.from_snapshot != "":
            assert msg.from_snapshot is not None
            return msg.from_snapshot
        else:
            _t1779 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1780 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1781 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1781,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1782 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1782,))
        if msg.compression != "":
            _t1783 = self._make_value_string(msg.compression)
            result.append(("compression", _t1783,))
        if len(result) == 0:
            return None
        else:
            _t1784 = None
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
            _t1785 = None
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
        flat809 = self._try_flat(msg, self.pretty_transaction)
        if flat809 is not None:
            assert flat809 is not None
            self.write(flat809)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1600 = _dollar_dollar.configure
            else:
                _t1600 = None
            if _dollar_dollar.HasField("sync"):
                _t1601 = _dollar_dollar.sync
            else:
                _t1601 = None
            fields800 = (_t1600, _t1601, _dollar_dollar.epochs,)
            assert fields800 is not None
            unwrapped_fields801 = fields800
            self.write("(transaction")
            self.indent_sexp()
            field802 = unwrapped_fields801[0]
            if field802 is not None:
                self.newline()
                assert field802 is not None
                opt_val803 = field802
                self.pretty_configure(opt_val803)
            field804 = unwrapped_fields801[1]
            if field804 is not None:
                self.newline()
                assert field804 is not None
                opt_val805 = field804
                self.pretty_sync(opt_val805)
            field806 = unwrapped_fields801[2]
            if not len(field806) == 0:
                self.newline()
                for i808, elem807 in enumerate(field806):
                    if (i808 > 0):
                        self.newline()
                    self.pretty_epoch(elem807)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat812 = self._try_flat(msg, self.pretty_configure)
        if flat812 is not None:
            assert flat812 is not None
            self.write(flat812)
            return None
        else:
            _dollar_dollar = msg
            _t1602 = self.deconstruct_configure(_dollar_dollar)
            fields810 = _t1602
            assert fields810 is not None
            unwrapped_fields811 = fields810
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields811)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat816 = self._try_flat(msg, self.pretty_config_dict)
        if flat816 is not None:
            assert flat816 is not None
            self.write(flat816)
            return None
        else:
            fields813 = msg
            self.write("{")
            self.indent()
            if not len(fields813) == 0:
                self.newline()
                for i815, elem814 in enumerate(fields813):
                    if (i815 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem814)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat821 = self._try_flat(msg, self.pretty_config_key_value)
        if flat821 is not None:
            assert flat821 is not None
            self.write(flat821)
            return None
        else:
            _dollar_dollar = msg
            fields817 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields817 is not None
            unwrapped_fields818 = fields817
            self.write(":")
            field819 = unwrapped_fields818[0]
            self.write(field819)
            self.write(" ")
            field820 = unwrapped_fields818[1]
            self.pretty_raw_value(field820)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat847 = self._try_flat(msg, self.pretty_raw_value)
        if flat847 is not None:
            assert flat847 is not None
            self.write(flat847)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1603 = _dollar_dollar.date_value
            else:
                _t1603 = None
            deconstruct_result845 = _t1603
            if deconstruct_result845 is not None:
                assert deconstruct_result845 is not None
                unwrapped846 = deconstruct_result845
                self.pretty_raw_date(unwrapped846)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1604 = _dollar_dollar.datetime_value
                else:
                    _t1604 = None
                deconstruct_result843 = _t1604
                if deconstruct_result843 is not None:
                    assert deconstruct_result843 is not None
                    unwrapped844 = deconstruct_result843
                    self.pretty_raw_datetime(unwrapped844)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1605 = _dollar_dollar.string_value
                    else:
                        _t1605 = None
                    deconstruct_result841 = _t1605
                    if deconstruct_result841 is not None:
                        assert deconstruct_result841 is not None
                        unwrapped842 = deconstruct_result841
                        self.write(self.format_string_value(unwrapped842))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1606 = _dollar_dollar.int32_value
                        else:
                            _t1606 = None
                        deconstruct_result839 = _t1606
                        if deconstruct_result839 is not None:
                            assert deconstruct_result839 is not None
                            unwrapped840 = deconstruct_result839
                            self.write((str(unwrapped840) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1607 = _dollar_dollar.int_value
                            else:
                                _t1607 = None
                            deconstruct_result837 = _t1607
                            if deconstruct_result837 is not None:
                                assert deconstruct_result837 is not None
                                unwrapped838 = deconstruct_result837
                                self.write(str(unwrapped838))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1608 = _dollar_dollar.float32_value
                                else:
                                    _t1608 = None
                                deconstruct_result835 = _t1608
                                if deconstruct_result835 is not None:
                                    assert deconstruct_result835 is not None
                                    unwrapped836 = deconstruct_result835
                                    self.write(self.format_float32_literal(unwrapped836))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1609 = _dollar_dollar.float_value
                                    else:
                                        _t1609 = None
                                    deconstruct_result833 = _t1609
                                    if deconstruct_result833 is not None:
                                        assert deconstruct_result833 is not None
                                        unwrapped834 = deconstruct_result833
                                        self.write(str(unwrapped834))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1610 = _dollar_dollar.uint32_value
                                        else:
                                            _t1610 = None
                                        deconstruct_result831 = _t1610
                                        if deconstruct_result831 is not None:
                                            assert deconstruct_result831 is not None
                                            unwrapped832 = deconstruct_result831
                                            self.write((str(unwrapped832) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1611 = _dollar_dollar.uint128_value
                                            else:
                                                _t1611 = None
                                            deconstruct_result829 = _t1611
                                            if deconstruct_result829 is not None:
                                                assert deconstruct_result829 is not None
                                                unwrapped830 = deconstruct_result829
                                                self.write(self.format_uint128(unwrapped830))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1612 = _dollar_dollar.int128_value
                                                else:
                                                    _t1612 = None
                                                deconstruct_result827 = _t1612
                                                if deconstruct_result827 is not None:
                                                    assert deconstruct_result827 is not None
                                                    unwrapped828 = deconstruct_result827
                                                    self.write(self.format_int128(unwrapped828))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1613 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1613 = None
                                                    deconstruct_result825 = _t1613
                                                    if deconstruct_result825 is not None:
                                                        assert deconstruct_result825 is not None
                                                        unwrapped826 = deconstruct_result825
                                                        self.write(self.format_decimal(unwrapped826))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1614 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1614 = None
                                                        deconstruct_result823 = _t1614
                                                        if deconstruct_result823 is not None:
                                                            assert deconstruct_result823 is not None
                                                            unwrapped824 = deconstruct_result823
                                                            self.pretty_boolean_value(unwrapped824)
                                                        else:
                                                            fields822 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat853 = self._try_flat(msg, self.pretty_raw_date)
        if flat853 is not None:
            assert flat853 is not None
            self.write(flat853)
            return None
        else:
            _dollar_dollar = msg
            fields848 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields848 is not None
            unwrapped_fields849 = fields848
            self.write("(date")
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
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat864 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat864 is not None:
            assert flat864 is not None
            self.write(flat864)
            return None
        else:
            _dollar_dollar = msg
            fields854 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields854 is not None
            unwrapped_fields855 = fields854
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field856 = unwrapped_fields855[0]
            self.write(str(field856))
            self.newline()
            field857 = unwrapped_fields855[1]
            self.write(str(field857))
            self.newline()
            field858 = unwrapped_fields855[2]
            self.write(str(field858))
            self.newline()
            field859 = unwrapped_fields855[3]
            self.write(str(field859))
            self.newline()
            field860 = unwrapped_fields855[4]
            self.write(str(field860))
            self.newline()
            field861 = unwrapped_fields855[5]
            self.write(str(field861))
            field862 = unwrapped_fields855[6]
            if field862 is not None:
                self.newline()
                assert field862 is not None
                opt_val863 = field862
                self.write(str(opt_val863))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1615 = ()
        else:
            _t1615 = None
        deconstruct_result867 = _t1615
        if deconstruct_result867 is not None:
            assert deconstruct_result867 is not None
            unwrapped868 = deconstruct_result867
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1616 = ()
            else:
                _t1616 = None
            deconstruct_result865 = _t1616
            if deconstruct_result865 is not None:
                assert deconstruct_result865 is not None
                unwrapped866 = deconstruct_result865
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat873 = self._try_flat(msg, self.pretty_sync)
        if flat873 is not None:
            assert flat873 is not None
            self.write(flat873)
            return None
        else:
            _dollar_dollar = msg
            fields869 = _dollar_dollar.fragments
            assert fields869 is not None
            unwrapped_fields870 = fields869
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields870) == 0:
                self.newline()
                for i872, elem871 in enumerate(unwrapped_fields870):
                    if (i872 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem871)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat876 = self._try_flat(msg, self.pretty_fragment_id)
        if flat876 is not None:
            assert flat876 is not None
            self.write(flat876)
            return None
        else:
            _dollar_dollar = msg
            fields874 = self.fragment_id_to_string(_dollar_dollar)
            assert fields874 is not None
            unwrapped_fields875 = fields874
            self.write(":")
            self.write(unwrapped_fields875)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat883 = self._try_flat(msg, self.pretty_epoch)
        if flat883 is not None:
            assert flat883 is not None
            self.write(flat883)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1617 = _dollar_dollar.writes
            else:
                _t1617 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1618 = _dollar_dollar.reads
            else:
                _t1618 = None
            fields877 = (_t1617, _t1618,)
            assert fields877 is not None
            unwrapped_fields878 = fields877
            self.write("(epoch")
            self.indent_sexp()
            field879 = unwrapped_fields878[0]
            if field879 is not None:
                self.newline()
                assert field879 is not None
                opt_val880 = field879
                self.pretty_epoch_writes(opt_val880)
            field881 = unwrapped_fields878[1]
            if field881 is not None:
                self.newline()
                assert field881 is not None
                opt_val882 = field881
                self.pretty_epoch_reads(opt_val882)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat887 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat887 is not None:
            assert flat887 is not None
            self.write(flat887)
            return None
        else:
            fields884 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields884) == 0:
                self.newline()
                for i886, elem885 in enumerate(fields884):
                    if (i886 > 0):
                        self.newline()
                    self.pretty_write(elem885)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat896 = self._try_flat(msg, self.pretty_write)
        if flat896 is not None:
            assert flat896 is not None
            self.write(flat896)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1619 = _dollar_dollar.define
            else:
                _t1619 = None
            deconstruct_result894 = _t1619
            if deconstruct_result894 is not None:
                assert deconstruct_result894 is not None
                unwrapped895 = deconstruct_result894
                self.pretty_define(unwrapped895)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1620 = _dollar_dollar.undefine
                else:
                    _t1620 = None
                deconstruct_result892 = _t1620
                if deconstruct_result892 is not None:
                    assert deconstruct_result892 is not None
                    unwrapped893 = deconstruct_result892
                    self.pretty_undefine(unwrapped893)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1621 = _dollar_dollar.context
                    else:
                        _t1621 = None
                    deconstruct_result890 = _t1621
                    if deconstruct_result890 is not None:
                        assert deconstruct_result890 is not None
                        unwrapped891 = deconstruct_result890
                        self.pretty_context(unwrapped891)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1622 = _dollar_dollar.snapshot
                        else:
                            _t1622 = None
                        deconstruct_result888 = _t1622
                        if deconstruct_result888 is not None:
                            assert deconstruct_result888 is not None
                            unwrapped889 = deconstruct_result888
                            self.pretty_snapshot(unwrapped889)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat899 = self._try_flat(msg, self.pretty_define)
        if flat899 is not None:
            assert flat899 is not None
            self.write(flat899)
            return None
        else:
            _dollar_dollar = msg
            fields897 = _dollar_dollar.fragment
            assert fields897 is not None
            unwrapped_fields898 = fields897
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields898)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat906 = self._try_flat(msg, self.pretty_fragment)
        if flat906 is not None:
            assert flat906 is not None
            self.write(flat906)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields900 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields900 is not None
            unwrapped_fields901 = fields900
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field902 = unwrapped_fields901[0]
            self.pretty_new_fragment_id(field902)
            field903 = unwrapped_fields901[1]
            if not len(field903) == 0:
                self.newline()
                for i905, elem904 in enumerate(field903):
                    if (i905 > 0):
                        self.newline()
                    self.pretty_declaration(elem904)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat908 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat908 is not None:
            assert flat908 is not None
            self.write(flat908)
            return None
        else:
            fields907 = msg
            self.pretty_fragment_id(fields907)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat917 = self._try_flat(msg, self.pretty_declaration)
        if flat917 is not None:
            assert flat917 is not None
            self.write(flat917)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1623 = getattr(_dollar_dollar, 'def')
            else:
                _t1623 = None
            deconstruct_result915 = _t1623
            if deconstruct_result915 is not None:
                assert deconstruct_result915 is not None
                unwrapped916 = deconstruct_result915
                self.pretty_def(unwrapped916)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1624 = _dollar_dollar.algorithm
                else:
                    _t1624 = None
                deconstruct_result913 = _t1624
                if deconstruct_result913 is not None:
                    assert deconstruct_result913 is not None
                    unwrapped914 = deconstruct_result913
                    self.pretty_algorithm(unwrapped914)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1625 = _dollar_dollar.constraint
                    else:
                        _t1625 = None
                    deconstruct_result911 = _t1625
                    if deconstruct_result911 is not None:
                        assert deconstruct_result911 is not None
                        unwrapped912 = deconstruct_result911
                        self.pretty_constraint(unwrapped912)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1626 = _dollar_dollar.data
                        else:
                            _t1626 = None
                        deconstruct_result909 = _t1626
                        if deconstruct_result909 is not None:
                            assert deconstruct_result909 is not None
                            unwrapped910 = deconstruct_result909
                            self.pretty_data(unwrapped910)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat924 = self._try_flat(msg, self.pretty_def)
        if flat924 is not None:
            assert flat924 is not None
            self.write(flat924)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1627 = _dollar_dollar.attrs
            else:
                _t1627 = None
            fields918 = (_dollar_dollar.name, _dollar_dollar.body, _t1627,)
            assert fields918 is not None
            unwrapped_fields919 = fields918
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field920 = unwrapped_fields919[0]
            self.pretty_relation_id(field920)
            self.newline()
            field921 = unwrapped_fields919[1]
            self.pretty_abstraction(field921)
            field922 = unwrapped_fields919[2]
            if field922 is not None:
                self.newline()
                assert field922 is not None
                opt_val923 = field922
                self.pretty_attrs(opt_val923)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat929 = self._try_flat(msg, self.pretty_relation_id)
        if flat929 is not None:
            assert flat929 is not None
            self.write(flat929)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1629 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1628 = _t1629
            else:
                _t1628 = None
            deconstruct_result927 = _t1628
            if deconstruct_result927 is not None:
                assert deconstruct_result927 is not None
                unwrapped928 = deconstruct_result927
                self.write(":")
                self.write(unwrapped928)
            else:
                _dollar_dollar = msg
                _t1630 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result925 = _t1630
                if deconstruct_result925 is not None:
                    assert deconstruct_result925 is not None
                    unwrapped926 = deconstruct_result925
                    self.write(self.format_uint128(unwrapped926))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat934 = self._try_flat(msg, self.pretty_abstraction)
        if flat934 is not None:
            assert flat934 is not None
            self.write(flat934)
            return None
        else:
            _dollar_dollar = msg
            _t1631 = self.deconstruct_bindings(_dollar_dollar)
            fields930 = (_t1631, _dollar_dollar.value,)
            assert fields930 is not None
            unwrapped_fields931 = fields930
            self.write("(")
            self.indent()
            field932 = unwrapped_fields931[0]
            self.pretty_bindings(field932)
            self.newline()
            field933 = unwrapped_fields931[1]
            self.pretty_formula(field933)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat942 = self._try_flat(msg, self.pretty_bindings)
        if flat942 is not None:
            assert flat942 is not None
            self.write(flat942)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1632 = _dollar_dollar[1]
            else:
                _t1632 = None
            fields935 = (_dollar_dollar[0], _t1632,)
            assert fields935 is not None
            unwrapped_fields936 = fields935
            self.write("[")
            self.indent()
            field937 = unwrapped_fields936[0]
            for i939, elem938 in enumerate(field937):
                if (i939 > 0):
                    self.newline()
                self.pretty_binding(elem938)
            field940 = unwrapped_fields936[1]
            if field940 is not None:
                self.newline()
                assert field940 is not None
                opt_val941 = field940
                self.pretty_value_bindings(opt_val941)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat947 = self._try_flat(msg, self.pretty_binding)
        if flat947 is not None:
            assert flat947 is not None
            self.write(flat947)
            return None
        else:
            _dollar_dollar = msg
            fields943 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields943 is not None
            unwrapped_fields944 = fields943
            field945 = unwrapped_fields944[0]
            self.write(field945)
            self.write("::")
            field946 = unwrapped_fields944[1]
            self.pretty_type(field946)

    def pretty_type(self, msg: logic_pb2.Type):
        flat976 = self._try_flat(msg, self.pretty_type)
        if flat976 is not None:
            assert flat976 is not None
            self.write(flat976)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1633 = _dollar_dollar.unspecified_type
            else:
                _t1633 = None
            deconstruct_result974 = _t1633
            if deconstruct_result974 is not None:
                assert deconstruct_result974 is not None
                unwrapped975 = deconstruct_result974
                self.pretty_unspecified_type(unwrapped975)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1634 = _dollar_dollar.string_type
                else:
                    _t1634 = None
                deconstruct_result972 = _t1634
                if deconstruct_result972 is not None:
                    assert deconstruct_result972 is not None
                    unwrapped973 = deconstruct_result972
                    self.pretty_string_type(unwrapped973)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1635 = _dollar_dollar.int_type
                    else:
                        _t1635 = None
                    deconstruct_result970 = _t1635
                    if deconstruct_result970 is not None:
                        assert deconstruct_result970 is not None
                        unwrapped971 = deconstruct_result970
                        self.pretty_int_type(unwrapped971)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1636 = _dollar_dollar.float_type
                        else:
                            _t1636 = None
                        deconstruct_result968 = _t1636
                        if deconstruct_result968 is not None:
                            assert deconstruct_result968 is not None
                            unwrapped969 = deconstruct_result968
                            self.pretty_float_type(unwrapped969)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1637 = _dollar_dollar.uint128_type
                            else:
                                _t1637 = None
                            deconstruct_result966 = _t1637
                            if deconstruct_result966 is not None:
                                assert deconstruct_result966 is not None
                                unwrapped967 = deconstruct_result966
                                self.pretty_uint128_type(unwrapped967)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1638 = _dollar_dollar.int128_type
                                else:
                                    _t1638 = None
                                deconstruct_result964 = _t1638
                                if deconstruct_result964 is not None:
                                    assert deconstruct_result964 is not None
                                    unwrapped965 = deconstruct_result964
                                    self.pretty_int128_type(unwrapped965)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1639 = _dollar_dollar.date_type
                                    else:
                                        _t1639 = None
                                    deconstruct_result962 = _t1639
                                    if deconstruct_result962 is not None:
                                        assert deconstruct_result962 is not None
                                        unwrapped963 = deconstruct_result962
                                        self.pretty_date_type(unwrapped963)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1640 = _dollar_dollar.datetime_type
                                        else:
                                            _t1640 = None
                                        deconstruct_result960 = _t1640
                                        if deconstruct_result960 is not None:
                                            assert deconstruct_result960 is not None
                                            unwrapped961 = deconstruct_result960
                                            self.pretty_datetime_type(unwrapped961)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1641 = _dollar_dollar.missing_type
                                            else:
                                                _t1641 = None
                                            deconstruct_result958 = _t1641
                                            if deconstruct_result958 is not None:
                                                assert deconstruct_result958 is not None
                                                unwrapped959 = deconstruct_result958
                                                self.pretty_missing_type(unwrapped959)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1642 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1642 = None
                                                deconstruct_result956 = _t1642
                                                if deconstruct_result956 is not None:
                                                    assert deconstruct_result956 is not None
                                                    unwrapped957 = deconstruct_result956
                                                    self.pretty_decimal_type(unwrapped957)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1643 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1643 = None
                                                    deconstruct_result954 = _t1643
                                                    if deconstruct_result954 is not None:
                                                        assert deconstruct_result954 is not None
                                                        unwrapped955 = deconstruct_result954
                                                        self.pretty_boolean_type(unwrapped955)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1644 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1644 = None
                                                        deconstruct_result952 = _t1644
                                                        if deconstruct_result952 is not None:
                                                            assert deconstruct_result952 is not None
                                                            unwrapped953 = deconstruct_result952
                                                            self.pretty_int32_type(unwrapped953)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1645 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1645 = None
                                                            deconstruct_result950 = _t1645
                                                            if deconstruct_result950 is not None:
                                                                assert deconstruct_result950 is not None
                                                                unwrapped951 = deconstruct_result950
                                                                self.pretty_float32_type(unwrapped951)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1646 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1646 = None
                                                                deconstruct_result948 = _t1646
                                                                if deconstruct_result948 is not None:
                                                                    assert deconstruct_result948 is not None
                                                                    unwrapped949 = deconstruct_result948
                                                                    self.pretty_uint32_type(unwrapped949)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields977 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields978 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields979 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields980 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields981 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields982 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields983 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields984 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields985 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat990 = self._try_flat(msg, self.pretty_decimal_type)
        if flat990 is not None:
            assert flat990 is not None
            self.write(flat990)
            return None
        else:
            _dollar_dollar = msg
            fields986 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields986 is not None
            unwrapped_fields987 = fields986
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field988 = unwrapped_fields987[0]
            self.write(str(field988))
            self.newline()
            field989 = unwrapped_fields987[1]
            self.write(str(field989))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields991 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields992 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields993 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields994 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat998 = self._try_flat(msg, self.pretty_value_bindings)
        if flat998 is not None:
            assert flat998 is not None
            self.write(flat998)
            return None
        else:
            fields995 = msg
            self.write("|")
            if not len(fields995) == 0:
                self.write(" ")
                for i997, elem996 in enumerate(fields995):
                    if (i997 > 0):
                        self.newline()
                    self.pretty_binding(elem996)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1025 = self._try_flat(msg, self.pretty_formula)
        if flat1025 is not None:
            assert flat1025 is not None
            self.write(flat1025)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1647 = _dollar_dollar.conjunction
            else:
                _t1647 = None
            deconstruct_result1023 = _t1647
            if deconstruct_result1023 is not None:
                assert deconstruct_result1023 is not None
                unwrapped1024 = deconstruct_result1023
                self.pretty_true(unwrapped1024)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1648 = _dollar_dollar.disjunction
                else:
                    _t1648 = None
                deconstruct_result1021 = _t1648
                if deconstruct_result1021 is not None:
                    assert deconstruct_result1021 is not None
                    unwrapped1022 = deconstruct_result1021
                    self.pretty_false(unwrapped1022)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1649 = _dollar_dollar.exists
                    else:
                        _t1649 = None
                    deconstruct_result1019 = _t1649
                    if deconstruct_result1019 is not None:
                        assert deconstruct_result1019 is not None
                        unwrapped1020 = deconstruct_result1019
                        self.pretty_exists(unwrapped1020)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1650 = _dollar_dollar.reduce
                        else:
                            _t1650 = None
                        deconstruct_result1017 = _t1650
                        if deconstruct_result1017 is not None:
                            assert deconstruct_result1017 is not None
                            unwrapped1018 = deconstruct_result1017
                            self.pretty_reduce(unwrapped1018)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1651 = _dollar_dollar.conjunction
                            else:
                                _t1651 = None
                            deconstruct_result1015 = _t1651
                            if deconstruct_result1015 is not None:
                                assert deconstruct_result1015 is not None
                                unwrapped1016 = deconstruct_result1015
                                self.pretty_conjunction(unwrapped1016)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1652 = _dollar_dollar.disjunction
                                else:
                                    _t1652 = None
                                deconstruct_result1013 = _t1652
                                if deconstruct_result1013 is not None:
                                    assert deconstruct_result1013 is not None
                                    unwrapped1014 = deconstruct_result1013
                                    self.pretty_disjunction(unwrapped1014)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1653 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1653 = None
                                    deconstruct_result1011 = _t1653
                                    if deconstruct_result1011 is not None:
                                        assert deconstruct_result1011 is not None
                                        unwrapped1012 = deconstruct_result1011
                                        self.pretty_not(unwrapped1012)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1654 = _dollar_dollar.ffi
                                        else:
                                            _t1654 = None
                                        deconstruct_result1009 = _t1654
                                        if deconstruct_result1009 is not None:
                                            assert deconstruct_result1009 is not None
                                            unwrapped1010 = deconstruct_result1009
                                            self.pretty_ffi(unwrapped1010)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1655 = _dollar_dollar.atom
                                            else:
                                                _t1655 = None
                                            deconstruct_result1007 = _t1655
                                            if deconstruct_result1007 is not None:
                                                assert deconstruct_result1007 is not None
                                                unwrapped1008 = deconstruct_result1007
                                                self.pretty_atom(unwrapped1008)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1656 = _dollar_dollar.pragma
                                                else:
                                                    _t1656 = None
                                                deconstruct_result1005 = _t1656
                                                if deconstruct_result1005 is not None:
                                                    assert deconstruct_result1005 is not None
                                                    unwrapped1006 = deconstruct_result1005
                                                    self.pretty_pragma(unwrapped1006)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1657 = _dollar_dollar.primitive
                                                    else:
                                                        _t1657 = None
                                                    deconstruct_result1003 = _t1657
                                                    if deconstruct_result1003 is not None:
                                                        assert deconstruct_result1003 is not None
                                                        unwrapped1004 = deconstruct_result1003
                                                        self.pretty_primitive(unwrapped1004)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1658 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1658 = None
                                                        deconstruct_result1001 = _t1658
                                                        if deconstruct_result1001 is not None:
                                                            assert deconstruct_result1001 is not None
                                                            unwrapped1002 = deconstruct_result1001
                                                            self.pretty_rel_atom(unwrapped1002)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1659 = _dollar_dollar.cast
                                                            else:
                                                                _t1659 = None
                                                            deconstruct_result999 = _t1659
                                                            if deconstruct_result999 is not None:
                                                                assert deconstruct_result999 is not None
                                                                unwrapped1000 = deconstruct_result999
                                                                self.pretty_cast(unwrapped1000)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields1026 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1027 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1032 = self._try_flat(msg, self.pretty_exists)
        if flat1032 is not None:
            assert flat1032 is not None
            self.write(flat1032)
            return None
        else:
            _dollar_dollar = msg
            _t1660 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1028 = (_t1660, _dollar_dollar.body.value,)
            assert fields1028 is not None
            unwrapped_fields1029 = fields1028
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1030 = unwrapped_fields1029[0]
            self.pretty_bindings(field1030)
            self.newline()
            field1031 = unwrapped_fields1029[1]
            self.pretty_formula(field1031)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1038 = self._try_flat(msg, self.pretty_reduce)
        if flat1038 is not None:
            assert flat1038 is not None
            self.write(flat1038)
            return None
        else:
            _dollar_dollar = msg
            fields1033 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1033 is not None
            unwrapped_fields1034 = fields1033
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1035 = unwrapped_fields1034[0]
            self.pretty_abstraction(field1035)
            self.newline()
            field1036 = unwrapped_fields1034[1]
            self.pretty_abstraction(field1036)
            self.newline()
            field1037 = unwrapped_fields1034[2]
            self.pretty_terms(field1037)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1042 = self._try_flat(msg, self.pretty_terms)
        if flat1042 is not None:
            assert flat1042 is not None
            self.write(flat1042)
            return None
        else:
            fields1039 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1039) == 0:
                self.newline()
                for i1041, elem1040 in enumerate(fields1039):
                    if (i1041 > 0):
                        self.newline()
                    self.pretty_term(elem1040)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1047 = self._try_flat(msg, self.pretty_term)
        if flat1047 is not None:
            assert flat1047 is not None
            self.write(flat1047)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1661 = _dollar_dollar.var
            else:
                _t1661 = None
            deconstruct_result1045 = _t1661
            if deconstruct_result1045 is not None:
                assert deconstruct_result1045 is not None
                unwrapped1046 = deconstruct_result1045
                self.pretty_var(unwrapped1046)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1662 = _dollar_dollar.constant
                else:
                    _t1662 = None
                deconstruct_result1043 = _t1662
                if deconstruct_result1043 is not None:
                    assert deconstruct_result1043 is not None
                    unwrapped1044 = deconstruct_result1043
                    self.pretty_value(unwrapped1044)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1050 = self._try_flat(msg, self.pretty_var)
        if flat1050 is not None:
            assert flat1050 is not None
            self.write(flat1050)
            return None
        else:
            _dollar_dollar = msg
            fields1048 = _dollar_dollar.name
            assert fields1048 is not None
            unwrapped_fields1049 = fields1048
            self.write(unwrapped_fields1049)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1076 = self._try_flat(msg, self.pretty_value)
        if flat1076 is not None:
            assert flat1076 is not None
            self.write(flat1076)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1663 = _dollar_dollar.date_value
            else:
                _t1663 = None
            deconstruct_result1074 = _t1663
            if deconstruct_result1074 is not None:
                assert deconstruct_result1074 is not None
                unwrapped1075 = deconstruct_result1074
                self.pretty_date(unwrapped1075)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1664 = _dollar_dollar.datetime_value
                else:
                    _t1664 = None
                deconstruct_result1072 = _t1664
                if deconstruct_result1072 is not None:
                    assert deconstruct_result1072 is not None
                    unwrapped1073 = deconstruct_result1072
                    self.pretty_datetime(unwrapped1073)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1665 = _dollar_dollar.string_value
                    else:
                        _t1665 = None
                    deconstruct_result1070 = _t1665
                    if deconstruct_result1070 is not None:
                        assert deconstruct_result1070 is not None
                        unwrapped1071 = deconstruct_result1070
                        self.write(self.format_string_value(unwrapped1071))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1666 = _dollar_dollar.int32_value
                        else:
                            _t1666 = None
                        deconstruct_result1068 = _t1666
                        if deconstruct_result1068 is not None:
                            assert deconstruct_result1068 is not None
                            unwrapped1069 = deconstruct_result1068
                            self.write((str(unwrapped1069) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1667 = _dollar_dollar.int_value
                            else:
                                _t1667 = None
                            deconstruct_result1066 = _t1667
                            if deconstruct_result1066 is not None:
                                assert deconstruct_result1066 is not None
                                unwrapped1067 = deconstruct_result1066
                                self.write(str(unwrapped1067))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1668 = _dollar_dollar.float32_value
                                else:
                                    _t1668 = None
                                deconstruct_result1064 = _t1668
                                if deconstruct_result1064 is not None:
                                    assert deconstruct_result1064 is not None
                                    unwrapped1065 = deconstruct_result1064
                                    self.write(self.format_float32_literal(unwrapped1065))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1669 = _dollar_dollar.float_value
                                    else:
                                        _t1669 = None
                                    deconstruct_result1062 = _t1669
                                    if deconstruct_result1062 is not None:
                                        assert deconstruct_result1062 is not None
                                        unwrapped1063 = deconstruct_result1062
                                        self.write(str(unwrapped1063))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1670 = _dollar_dollar.uint32_value
                                        else:
                                            _t1670 = None
                                        deconstruct_result1060 = _t1670
                                        if deconstruct_result1060 is not None:
                                            assert deconstruct_result1060 is not None
                                            unwrapped1061 = deconstruct_result1060
                                            self.write((str(unwrapped1061) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1671 = _dollar_dollar.uint128_value
                                            else:
                                                _t1671 = None
                                            deconstruct_result1058 = _t1671
                                            if deconstruct_result1058 is not None:
                                                assert deconstruct_result1058 is not None
                                                unwrapped1059 = deconstruct_result1058
                                                self.write(self.format_uint128(unwrapped1059))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1672 = _dollar_dollar.int128_value
                                                else:
                                                    _t1672 = None
                                                deconstruct_result1056 = _t1672
                                                if deconstruct_result1056 is not None:
                                                    assert deconstruct_result1056 is not None
                                                    unwrapped1057 = deconstruct_result1056
                                                    self.write(self.format_int128(unwrapped1057))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1673 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1673 = None
                                                    deconstruct_result1054 = _t1673
                                                    if deconstruct_result1054 is not None:
                                                        assert deconstruct_result1054 is not None
                                                        unwrapped1055 = deconstruct_result1054
                                                        self.write(self.format_decimal(unwrapped1055))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1674 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1674 = None
                                                        deconstruct_result1052 = _t1674
                                                        if deconstruct_result1052 is not None:
                                                            assert deconstruct_result1052 is not None
                                                            unwrapped1053 = deconstruct_result1052
                                                            self.pretty_boolean_value(unwrapped1053)
                                                        else:
                                                            fields1051 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1082 = self._try_flat(msg, self.pretty_date)
        if flat1082 is not None:
            assert flat1082 is not None
            self.write(flat1082)
            return None
        else:
            _dollar_dollar = msg
            fields1077 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1077 is not None
            unwrapped_fields1078 = fields1077
            self.write("(date")
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
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1093 = self._try_flat(msg, self.pretty_datetime)
        if flat1093 is not None:
            assert flat1093 is not None
            self.write(flat1093)
            return None
        else:
            _dollar_dollar = msg
            fields1083 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1083 is not None
            unwrapped_fields1084 = fields1083
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1085 = unwrapped_fields1084[0]
            self.write(str(field1085))
            self.newline()
            field1086 = unwrapped_fields1084[1]
            self.write(str(field1086))
            self.newline()
            field1087 = unwrapped_fields1084[2]
            self.write(str(field1087))
            self.newline()
            field1088 = unwrapped_fields1084[3]
            self.write(str(field1088))
            self.newline()
            field1089 = unwrapped_fields1084[4]
            self.write(str(field1089))
            self.newline()
            field1090 = unwrapped_fields1084[5]
            self.write(str(field1090))
            field1091 = unwrapped_fields1084[6]
            if field1091 is not None:
                self.newline()
                assert field1091 is not None
                opt_val1092 = field1091
                self.write(str(opt_val1092))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1098 = self._try_flat(msg, self.pretty_conjunction)
        if flat1098 is not None:
            assert flat1098 is not None
            self.write(flat1098)
            return None
        else:
            _dollar_dollar = msg
            fields1094 = _dollar_dollar.args
            assert fields1094 is not None
            unwrapped_fields1095 = fields1094
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1095) == 0:
                self.newline()
                for i1097, elem1096 in enumerate(unwrapped_fields1095):
                    if (i1097 > 0):
                        self.newline()
                    self.pretty_formula(elem1096)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1103 = self._try_flat(msg, self.pretty_disjunction)
        if flat1103 is not None:
            assert flat1103 is not None
            self.write(flat1103)
            return None
        else:
            _dollar_dollar = msg
            fields1099 = _dollar_dollar.args
            assert fields1099 is not None
            unwrapped_fields1100 = fields1099
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1100) == 0:
                self.newline()
                for i1102, elem1101 in enumerate(unwrapped_fields1100):
                    if (i1102 > 0):
                        self.newline()
                    self.pretty_formula(elem1101)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1106 = self._try_flat(msg, self.pretty_not)
        if flat1106 is not None:
            assert flat1106 is not None
            self.write(flat1106)
            return None
        else:
            _dollar_dollar = msg
            fields1104 = _dollar_dollar.arg
            assert fields1104 is not None
            unwrapped_fields1105 = fields1104
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1105)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1112 = self._try_flat(msg, self.pretty_ffi)
        if flat1112 is not None:
            assert flat1112 is not None
            self.write(flat1112)
            return None
        else:
            _dollar_dollar = msg
            fields1107 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1107 is not None
            unwrapped_fields1108 = fields1107
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1109 = unwrapped_fields1108[0]
            self.pretty_name(field1109)
            self.newline()
            field1110 = unwrapped_fields1108[1]
            self.pretty_ffi_args(field1110)
            self.newline()
            field1111 = unwrapped_fields1108[2]
            self.pretty_terms(field1111)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1114 = self._try_flat(msg, self.pretty_name)
        if flat1114 is not None:
            assert flat1114 is not None
            self.write(flat1114)
            return None
        else:
            fields1113 = msg
            self.write(":")
            self.write(fields1113)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1118 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1118 is not None:
            assert flat1118 is not None
            self.write(flat1118)
            return None
        else:
            fields1115 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1115) == 0:
                self.newline()
                for i1117, elem1116 in enumerate(fields1115):
                    if (i1117 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1116)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1125 = self._try_flat(msg, self.pretty_atom)
        if flat1125 is not None:
            assert flat1125 is not None
            self.write(flat1125)
            return None
        else:
            _dollar_dollar = msg
            fields1119 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1119 is not None
            unwrapped_fields1120 = fields1119
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1121 = unwrapped_fields1120[0]
            self.pretty_relation_id(field1121)
            field1122 = unwrapped_fields1120[1]
            if not len(field1122) == 0:
                self.newline()
                for i1124, elem1123 in enumerate(field1122):
                    if (i1124 > 0):
                        self.newline()
                    self.pretty_term(elem1123)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1132 = self._try_flat(msg, self.pretty_pragma)
        if flat1132 is not None:
            assert flat1132 is not None
            self.write(flat1132)
            return None
        else:
            _dollar_dollar = msg
            fields1126 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1126 is not None
            unwrapped_fields1127 = fields1126
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1128 = unwrapped_fields1127[0]
            self.pretty_name(field1128)
            field1129 = unwrapped_fields1127[1]
            if not len(field1129) == 0:
                self.newline()
                for i1131, elem1130 in enumerate(field1129):
                    if (i1131 > 0):
                        self.newline()
                    self.pretty_term(elem1130)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1148 = self._try_flat(msg, self.pretty_primitive)
        if flat1148 is not None:
            assert flat1148 is not None
            self.write(flat1148)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1675 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1675 = None
            guard_result1147 = _t1675
            if guard_result1147 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1676 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1676 = None
                guard_result1146 = _t1676
                if guard_result1146 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1677 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1677 = None
                    guard_result1145 = _t1677
                    if guard_result1145 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1678 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1678 = None
                        guard_result1144 = _t1678
                        if guard_result1144 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1679 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1679 = None
                            guard_result1143 = _t1679
                            if guard_result1143 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1680 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1680 = None
                                guard_result1142 = _t1680
                                if guard_result1142 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1681 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1681 = None
                                    guard_result1141 = _t1681
                                    if guard_result1141 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1682 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1682 = None
                                        guard_result1140 = _t1682
                                        if guard_result1140 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1683 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1683 = None
                                            guard_result1139 = _t1683
                                            if guard_result1139 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1133 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1133 is not None
                                                unwrapped_fields1134 = fields1133
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1135 = unwrapped_fields1134[0]
                                                self.pretty_name(field1135)
                                                field1136 = unwrapped_fields1134[1]
                                                if not len(field1136) == 0:
                                                    self.newline()
                                                    for i1138, elem1137 in enumerate(field1136):
                                                        if (i1138 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1137)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1153 = self._try_flat(msg, self.pretty_eq)
        if flat1153 is not None:
            assert flat1153 is not None
            self.write(flat1153)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1684 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1684 = None
            fields1149 = _t1684
            assert fields1149 is not None
            unwrapped_fields1150 = fields1149
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1151 = unwrapped_fields1150[0]
            self.pretty_term(field1151)
            self.newline()
            field1152 = unwrapped_fields1150[1]
            self.pretty_term(field1152)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1158 = self._try_flat(msg, self.pretty_lt)
        if flat1158 is not None:
            assert flat1158 is not None
            self.write(flat1158)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1685 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1685 = None
            fields1154 = _t1685
            assert fields1154 is not None
            unwrapped_fields1155 = fields1154
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1156 = unwrapped_fields1155[0]
            self.pretty_term(field1156)
            self.newline()
            field1157 = unwrapped_fields1155[1]
            self.pretty_term(field1157)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1163 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1163 is not None:
            assert flat1163 is not None
            self.write(flat1163)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1686 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1686 = None
            fields1159 = _t1686
            assert fields1159 is not None
            unwrapped_fields1160 = fields1159
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1161 = unwrapped_fields1160[0]
            self.pretty_term(field1161)
            self.newline()
            field1162 = unwrapped_fields1160[1]
            self.pretty_term(field1162)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1168 = self._try_flat(msg, self.pretty_gt)
        if flat1168 is not None:
            assert flat1168 is not None
            self.write(flat1168)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1687 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1687 = None
            fields1164 = _t1687
            assert fields1164 is not None
            unwrapped_fields1165 = fields1164
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1166 = unwrapped_fields1165[0]
            self.pretty_term(field1166)
            self.newline()
            field1167 = unwrapped_fields1165[1]
            self.pretty_term(field1167)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1173 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1173 is not None:
            assert flat1173 is not None
            self.write(flat1173)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1688 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1688 = None
            fields1169 = _t1688
            assert fields1169 is not None
            unwrapped_fields1170 = fields1169
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1171 = unwrapped_fields1170[0]
            self.pretty_term(field1171)
            self.newline()
            field1172 = unwrapped_fields1170[1]
            self.pretty_term(field1172)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1179 = self._try_flat(msg, self.pretty_add)
        if flat1179 is not None:
            assert flat1179 is not None
            self.write(flat1179)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1689 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1689 = None
            fields1174 = _t1689
            assert fields1174 is not None
            unwrapped_fields1175 = fields1174
            self.write("(+")
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

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1185 = self._try_flat(msg, self.pretty_minus)
        if flat1185 is not None:
            assert flat1185 is not None
            self.write(flat1185)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1690 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1690 = None
            fields1180 = _t1690
            assert fields1180 is not None
            unwrapped_fields1181 = fields1180
            self.write("(-")
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

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1191 = self._try_flat(msg, self.pretty_multiply)
        if flat1191 is not None:
            assert flat1191 is not None
            self.write(flat1191)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1691 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1691 = None
            fields1186 = _t1691
            assert fields1186 is not None
            unwrapped_fields1187 = fields1186
            self.write("(*")
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

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1197 = self._try_flat(msg, self.pretty_divide)
        if flat1197 is not None:
            assert flat1197 is not None
            self.write(flat1197)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1692 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1692 = None
            fields1192 = _t1692
            assert fields1192 is not None
            unwrapped_fields1193 = fields1192
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1194 = unwrapped_fields1193[0]
            self.pretty_term(field1194)
            self.newline()
            field1195 = unwrapped_fields1193[1]
            self.pretty_term(field1195)
            self.newline()
            field1196 = unwrapped_fields1193[2]
            self.pretty_term(field1196)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1202 = self._try_flat(msg, self.pretty_rel_term)
        if flat1202 is not None:
            assert flat1202 is not None
            self.write(flat1202)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1693 = _dollar_dollar.specialized_value
            else:
                _t1693 = None
            deconstruct_result1200 = _t1693
            if deconstruct_result1200 is not None:
                assert deconstruct_result1200 is not None
                unwrapped1201 = deconstruct_result1200
                self.pretty_specialized_value(unwrapped1201)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1694 = _dollar_dollar.term
                else:
                    _t1694 = None
                deconstruct_result1198 = _t1694
                if deconstruct_result1198 is not None:
                    assert deconstruct_result1198 is not None
                    unwrapped1199 = deconstruct_result1198
                    self.pretty_term(unwrapped1199)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1204 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1204 is not None:
            assert flat1204 is not None
            self.write(flat1204)
            return None
        else:
            fields1203 = msg
            self.write("#")
            self.pretty_raw_value(fields1203)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1211 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1211 is not None:
            assert flat1211 is not None
            self.write(flat1211)
            return None
        else:
            _dollar_dollar = msg
            fields1205 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1205 is not None
            unwrapped_fields1206 = fields1205
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1207 = unwrapped_fields1206[0]
            self.pretty_name(field1207)
            field1208 = unwrapped_fields1206[1]
            if not len(field1208) == 0:
                self.newline()
                for i1210, elem1209 in enumerate(field1208):
                    if (i1210 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1209)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1216 = self._try_flat(msg, self.pretty_cast)
        if flat1216 is not None:
            assert flat1216 is not None
            self.write(flat1216)
            return None
        else:
            _dollar_dollar = msg
            fields1212 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1212 is not None
            unwrapped_fields1213 = fields1212
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1214 = unwrapped_fields1213[0]
            self.pretty_term(field1214)
            self.newline()
            field1215 = unwrapped_fields1213[1]
            self.pretty_term(field1215)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1220 = self._try_flat(msg, self.pretty_attrs)
        if flat1220 is not None:
            assert flat1220 is not None
            self.write(flat1220)
            return None
        else:
            fields1217 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1217) == 0:
                self.newline()
                for i1219, elem1218 in enumerate(fields1217):
                    if (i1219 > 0):
                        self.newline()
                    self.pretty_attribute(elem1218)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1227 = self._try_flat(msg, self.pretty_attribute)
        if flat1227 is not None:
            assert flat1227 is not None
            self.write(flat1227)
            return None
        else:
            _dollar_dollar = msg
            fields1221 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1221 is not None
            unwrapped_fields1222 = fields1221
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1223 = unwrapped_fields1222[0]
            self.pretty_name(field1223)
            field1224 = unwrapped_fields1222[1]
            if not len(field1224) == 0:
                self.newline()
                for i1226, elem1225 in enumerate(field1224):
                    if (i1226 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1225)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1234 = self._try_flat(msg, self.pretty_algorithm)
        if flat1234 is not None:
            assert flat1234 is not None
            self.write(flat1234)
            return None
        else:
            _dollar_dollar = msg
            fields1228 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            assert fields1228 is not None
            unwrapped_fields1229 = fields1228
            self.write("(algorithm")
            self.indent_sexp()
            field1230 = unwrapped_fields1229[0]
            if not len(field1230) == 0:
                self.newline()
                for i1232, elem1231 in enumerate(field1230):
                    if (i1232 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1231)
            self.newline()
            field1233 = unwrapped_fields1229[1]
            self.pretty_script(field1233)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1239 = self._try_flat(msg, self.pretty_script)
        if flat1239 is not None:
            assert flat1239 is not None
            self.write(flat1239)
            return None
        else:
            _dollar_dollar = msg
            fields1235 = _dollar_dollar.constructs
            assert fields1235 is not None
            unwrapped_fields1236 = fields1235
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1236) == 0:
                self.newline()
                for i1238, elem1237 in enumerate(unwrapped_fields1236):
                    if (i1238 > 0):
                        self.newline()
                    self.pretty_construct(elem1237)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1244 = self._try_flat(msg, self.pretty_construct)
        if flat1244 is not None:
            assert flat1244 is not None
            self.write(flat1244)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1695 = _dollar_dollar.loop
            else:
                _t1695 = None
            deconstruct_result1242 = _t1695
            if deconstruct_result1242 is not None:
                assert deconstruct_result1242 is not None
                unwrapped1243 = deconstruct_result1242
                self.pretty_loop(unwrapped1243)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1696 = _dollar_dollar.instruction
                else:
                    _t1696 = None
                deconstruct_result1240 = _t1696
                if deconstruct_result1240 is not None:
                    assert deconstruct_result1240 is not None
                    unwrapped1241 = deconstruct_result1240
                    self.pretty_instruction(unwrapped1241)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1249 = self._try_flat(msg, self.pretty_loop)
        if flat1249 is not None:
            assert flat1249 is not None
            self.write(flat1249)
            return None
        else:
            _dollar_dollar = msg
            fields1245 = (_dollar_dollar.init, _dollar_dollar.body,)
            assert fields1245 is not None
            unwrapped_fields1246 = fields1245
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1247 = unwrapped_fields1246[0]
            self.pretty_init(field1247)
            self.newline()
            field1248 = unwrapped_fields1246[1]
            self.pretty_script(field1248)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1253 = self._try_flat(msg, self.pretty_init)
        if flat1253 is not None:
            assert flat1253 is not None
            self.write(flat1253)
            return None
        else:
            fields1250 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1250) == 0:
                self.newline()
                for i1252, elem1251 in enumerate(fields1250):
                    if (i1252 > 0):
                        self.newline()
                    self.pretty_instruction(elem1251)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1264 = self._try_flat(msg, self.pretty_instruction)
        if flat1264 is not None:
            assert flat1264 is not None
            self.write(flat1264)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1697 = _dollar_dollar.assign
            else:
                _t1697 = None
            deconstruct_result1262 = _t1697
            if deconstruct_result1262 is not None:
                assert deconstruct_result1262 is not None
                unwrapped1263 = deconstruct_result1262
                self.pretty_assign(unwrapped1263)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1698 = _dollar_dollar.upsert
                else:
                    _t1698 = None
                deconstruct_result1260 = _t1698
                if deconstruct_result1260 is not None:
                    assert deconstruct_result1260 is not None
                    unwrapped1261 = deconstruct_result1260
                    self.pretty_upsert(unwrapped1261)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1699 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1699 = None
                    deconstruct_result1258 = _t1699
                    if deconstruct_result1258 is not None:
                        assert deconstruct_result1258 is not None
                        unwrapped1259 = deconstruct_result1258
                        self.pretty_break(unwrapped1259)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1700 = _dollar_dollar.monoid_def
                        else:
                            _t1700 = None
                        deconstruct_result1256 = _t1700
                        if deconstruct_result1256 is not None:
                            assert deconstruct_result1256 is not None
                            unwrapped1257 = deconstruct_result1256
                            self.pretty_monoid_def(unwrapped1257)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1701 = _dollar_dollar.monus_def
                            else:
                                _t1701 = None
                            deconstruct_result1254 = _t1701
                            if deconstruct_result1254 is not None:
                                assert deconstruct_result1254 is not None
                                unwrapped1255 = deconstruct_result1254
                                self.pretty_monus_def(unwrapped1255)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1271 = self._try_flat(msg, self.pretty_assign)
        if flat1271 is not None:
            assert flat1271 is not None
            self.write(flat1271)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1702 = _dollar_dollar.attrs
            else:
                _t1702 = None
            fields1265 = (_dollar_dollar.name, _dollar_dollar.body, _t1702,)
            assert fields1265 is not None
            unwrapped_fields1266 = fields1265
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1267 = unwrapped_fields1266[0]
            self.pretty_relation_id(field1267)
            self.newline()
            field1268 = unwrapped_fields1266[1]
            self.pretty_abstraction(field1268)
            field1269 = unwrapped_fields1266[2]
            if field1269 is not None:
                self.newline()
                assert field1269 is not None
                opt_val1270 = field1269
                self.pretty_attrs(opt_val1270)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1278 = self._try_flat(msg, self.pretty_upsert)
        if flat1278 is not None:
            assert flat1278 is not None
            self.write(flat1278)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1703 = _dollar_dollar.attrs
            else:
                _t1703 = None
            fields1272 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1703,)
            assert fields1272 is not None
            unwrapped_fields1273 = fields1272
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1274 = unwrapped_fields1273[0]
            self.pretty_relation_id(field1274)
            self.newline()
            field1275 = unwrapped_fields1273[1]
            self.pretty_abstraction_with_arity(field1275)
            field1276 = unwrapped_fields1273[2]
            if field1276 is not None:
                self.newline()
                assert field1276 is not None
                opt_val1277 = field1276
                self.pretty_attrs(opt_val1277)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1283 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1283 is not None:
            assert flat1283 is not None
            self.write(flat1283)
            return None
        else:
            _dollar_dollar = msg
            _t1704 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1279 = (_t1704, _dollar_dollar[0].value,)
            assert fields1279 is not None
            unwrapped_fields1280 = fields1279
            self.write("(")
            self.indent()
            field1281 = unwrapped_fields1280[0]
            self.pretty_bindings(field1281)
            self.newline()
            field1282 = unwrapped_fields1280[1]
            self.pretty_formula(field1282)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1290 = self._try_flat(msg, self.pretty_break)
        if flat1290 is not None:
            assert flat1290 is not None
            self.write(flat1290)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1705 = _dollar_dollar.attrs
            else:
                _t1705 = None
            fields1284 = (_dollar_dollar.name, _dollar_dollar.body, _t1705,)
            assert fields1284 is not None
            unwrapped_fields1285 = fields1284
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1286 = unwrapped_fields1285[0]
            self.pretty_relation_id(field1286)
            self.newline()
            field1287 = unwrapped_fields1285[1]
            self.pretty_abstraction(field1287)
            field1288 = unwrapped_fields1285[2]
            if field1288 is not None:
                self.newline()
                assert field1288 is not None
                opt_val1289 = field1288
                self.pretty_attrs(opt_val1289)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1298 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1298 is not None:
            assert flat1298 is not None
            self.write(flat1298)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1706 = _dollar_dollar.attrs
            else:
                _t1706 = None
            fields1291 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1706,)
            assert fields1291 is not None
            unwrapped_fields1292 = fields1291
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1293 = unwrapped_fields1292[0]
            self.pretty_monoid(field1293)
            self.newline()
            field1294 = unwrapped_fields1292[1]
            self.pretty_relation_id(field1294)
            self.newline()
            field1295 = unwrapped_fields1292[2]
            self.pretty_abstraction_with_arity(field1295)
            field1296 = unwrapped_fields1292[3]
            if field1296 is not None:
                self.newline()
                assert field1296 is not None
                opt_val1297 = field1296
                self.pretty_attrs(opt_val1297)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1307 = self._try_flat(msg, self.pretty_monoid)
        if flat1307 is not None:
            assert flat1307 is not None
            self.write(flat1307)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1707 = _dollar_dollar.or_monoid
            else:
                _t1707 = None
            deconstruct_result1305 = _t1707
            if deconstruct_result1305 is not None:
                assert deconstruct_result1305 is not None
                unwrapped1306 = deconstruct_result1305
                self.pretty_or_monoid(unwrapped1306)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1708 = _dollar_dollar.min_monoid
                else:
                    _t1708 = None
                deconstruct_result1303 = _t1708
                if deconstruct_result1303 is not None:
                    assert deconstruct_result1303 is not None
                    unwrapped1304 = deconstruct_result1303
                    self.pretty_min_monoid(unwrapped1304)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1709 = _dollar_dollar.max_monoid
                    else:
                        _t1709 = None
                    deconstruct_result1301 = _t1709
                    if deconstruct_result1301 is not None:
                        assert deconstruct_result1301 is not None
                        unwrapped1302 = deconstruct_result1301
                        self.pretty_max_monoid(unwrapped1302)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1710 = _dollar_dollar.sum_monoid
                        else:
                            _t1710 = None
                        deconstruct_result1299 = _t1710
                        if deconstruct_result1299 is not None:
                            assert deconstruct_result1299 is not None
                            unwrapped1300 = deconstruct_result1299
                            self.pretty_sum_monoid(unwrapped1300)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1308 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1311 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1311 is not None:
            assert flat1311 is not None
            self.write(flat1311)
            return None
        else:
            _dollar_dollar = msg
            fields1309 = _dollar_dollar.type
            assert fields1309 is not None
            unwrapped_fields1310 = fields1309
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1310)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1314 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1314 is not None:
            assert flat1314 is not None
            self.write(flat1314)
            return None
        else:
            _dollar_dollar = msg
            fields1312 = _dollar_dollar.type
            assert fields1312 is not None
            unwrapped_fields1313 = fields1312
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1313)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1317 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1317 is not None:
            assert flat1317 is not None
            self.write(flat1317)
            return None
        else:
            _dollar_dollar = msg
            fields1315 = _dollar_dollar.type
            assert fields1315 is not None
            unwrapped_fields1316 = fields1315
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1316)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1325 = self._try_flat(msg, self.pretty_monus_def)
        if flat1325 is not None:
            assert flat1325 is not None
            self.write(flat1325)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1711 = _dollar_dollar.attrs
            else:
                _t1711 = None
            fields1318 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1711,)
            assert fields1318 is not None
            unwrapped_fields1319 = fields1318
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1320 = unwrapped_fields1319[0]
            self.pretty_monoid(field1320)
            self.newline()
            field1321 = unwrapped_fields1319[1]
            self.pretty_relation_id(field1321)
            self.newline()
            field1322 = unwrapped_fields1319[2]
            self.pretty_abstraction_with_arity(field1322)
            field1323 = unwrapped_fields1319[3]
            if field1323 is not None:
                self.newline()
                assert field1323 is not None
                opt_val1324 = field1323
                self.pretty_attrs(opt_val1324)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1332 = self._try_flat(msg, self.pretty_constraint)
        if flat1332 is not None:
            assert flat1332 is not None
            self.write(flat1332)
            return None
        else:
            _dollar_dollar = msg
            fields1326 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1326 is not None
            unwrapped_fields1327 = fields1326
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1328 = unwrapped_fields1327[0]
            self.pretty_relation_id(field1328)
            self.newline()
            field1329 = unwrapped_fields1327[1]
            self.pretty_abstraction(field1329)
            self.newline()
            field1330 = unwrapped_fields1327[2]
            self.pretty_functional_dependency_keys(field1330)
            self.newline()
            field1331 = unwrapped_fields1327[3]
            self.pretty_functional_dependency_values(field1331)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1336 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1336 is not None:
            assert flat1336 is not None
            self.write(flat1336)
            return None
        else:
            fields1333 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1333) == 0:
                self.newline()
                for i1335, elem1334 in enumerate(fields1333):
                    if (i1335 > 0):
                        self.newline()
                    self.pretty_var(elem1334)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1340 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1340 is not None:
            assert flat1340 is not None
            self.write(flat1340)
            return None
        else:
            fields1337 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1337) == 0:
                self.newline()
                for i1339, elem1338 in enumerate(fields1337):
                    if (i1339 > 0):
                        self.newline()
                    self.pretty_var(elem1338)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1349 = self._try_flat(msg, self.pretty_data)
        if flat1349 is not None:
            assert flat1349 is not None
            self.write(flat1349)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1712 = _dollar_dollar.edb
            else:
                _t1712 = None
            deconstruct_result1347 = _t1712
            if deconstruct_result1347 is not None:
                assert deconstruct_result1347 is not None
                unwrapped1348 = deconstruct_result1347
                self.pretty_edb(unwrapped1348)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1713 = _dollar_dollar.betree_relation
                else:
                    _t1713 = None
                deconstruct_result1345 = _t1713
                if deconstruct_result1345 is not None:
                    assert deconstruct_result1345 is not None
                    unwrapped1346 = deconstruct_result1345
                    self.pretty_betree_relation(unwrapped1346)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1714 = _dollar_dollar.csv_data
                    else:
                        _t1714 = None
                    deconstruct_result1343 = _t1714
                    if deconstruct_result1343 is not None:
                        assert deconstruct_result1343 is not None
                        unwrapped1344 = deconstruct_result1343
                        self.pretty_csv_data(unwrapped1344)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1715 = _dollar_dollar.iceberg_data
                        else:
                            _t1715 = None
                        deconstruct_result1341 = _t1715
                        if deconstruct_result1341 is not None:
                            assert deconstruct_result1341 is not None
                            unwrapped1342 = deconstruct_result1341
                            self.pretty_iceberg_data(unwrapped1342)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1355 = self._try_flat(msg, self.pretty_edb)
        if flat1355 is not None:
            assert flat1355 is not None
            self.write(flat1355)
            return None
        else:
            _dollar_dollar = msg
            fields1350 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1350 is not None
            unwrapped_fields1351 = fields1350
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1352 = unwrapped_fields1351[0]
            self.pretty_relation_id(field1352)
            self.newline()
            field1353 = unwrapped_fields1351[1]
            self.pretty_edb_path(field1353)
            self.newline()
            field1354 = unwrapped_fields1351[2]
            self.pretty_edb_types(field1354)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1359 = self._try_flat(msg, self.pretty_edb_path)
        if flat1359 is not None:
            assert flat1359 is not None
            self.write(flat1359)
            return None
        else:
            fields1356 = msg
            self.write("[")
            self.indent()
            for i1358, elem1357 in enumerate(fields1356):
                if (i1358 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1357))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1363 = self._try_flat(msg, self.pretty_edb_types)
        if flat1363 is not None:
            assert flat1363 is not None
            self.write(flat1363)
            return None
        else:
            fields1360 = msg
            self.write("[")
            self.indent()
            for i1362, elem1361 in enumerate(fields1360):
                if (i1362 > 0):
                    self.newline()
                self.pretty_type(elem1361)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1368 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1368 is not None:
            assert flat1368 is not None
            self.write(flat1368)
            return None
        else:
            _dollar_dollar = msg
            fields1364 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1364 is not None
            unwrapped_fields1365 = fields1364
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1366 = unwrapped_fields1365[0]
            self.pretty_relation_id(field1366)
            self.newline()
            field1367 = unwrapped_fields1365[1]
            self.pretty_betree_info(field1367)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1374 = self._try_flat(msg, self.pretty_betree_info)
        if flat1374 is not None:
            assert flat1374 is not None
            self.write(flat1374)
            return None
        else:
            _dollar_dollar = msg
            _t1716 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1369 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1716,)
            assert fields1369 is not None
            unwrapped_fields1370 = fields1369
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1371 = unwrapped_fields1370[0]
            self.pretty_betree_info_key_types(field1371)
            self.newline()
            field1372 = unwrapped_fields1370[1]
            self.pretty_betree_info_value_types(field1372)
            self.newline()
            field1373 = unwrapped_fields1370[2]
            self.pretty_config_dict(field1373)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1378 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1378 is not None:
            assert flat1378 is not None
            self.write(flat1378)
            return None
        else:
            fields1375 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1375) == 0:
                self.newline()
                for i1377, elem1376 in enumerate(fields1375):
                    if (i1377 > 0):
                        self.newline()
                    self.pretty_type(elem1376)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1382 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1382 is not None:
            assert flat1382 is not None
            self.write(flat1382)
            return None
        else:
            fields1379 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1379) == 0:
                self.newline()
                for i1381, elem1380 in enumerate(fields1379):
                    if (i1381 > 0):
                        self.newline()
                    self.pretty_type(elem1380)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1389 = self._try_flat(msg, self.pretty_csv_data)
        if flat1389 is not None:
            assert flat1389 is not None
            self.write(flat1389)
            return None
        else:
            _dollar_dollar = msg
            fields1383 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1383 is not None
            unwrapped_fields1384 = fields1383
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1385 = unwrapped_fields1384[0]
            self.pretty_csvlocator(field1385)
            self.newline()
            field1386 = unwrapped_fields1384[1]
            self.pretty_csv_config(field1386)
            self.newline()
            field1387 = unwrapped_fields1384[2]
            self.pretty_gnf_columns(field1387)
            self.newline()
            field1388 = unwrapped_fields1384[3]
            self.pretty_csv_asof(field1388)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1396 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1396 is not None:
            assert flat1396 is not None
            self.write(flat1396)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1717 = _dollar_dollar.paths
            else:
                _t1717 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1718 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1718 = None
            fields1390 = (_t1717, _t1718,)
            assert fields1390 is not None
            unwrapped_fields1391 = fields1390
            self.write("(csv_locator")
            self.indent_sexp()
            field1392 = unwrapped_fields1391[0]
            if field1392 is not None:
                self.newline()
                assert field1392 is not None
                opt_val1393 = field1392
                self.pretty_csv_locator_paths(opt_val1393)
            field1394 = unwrapped_fields1391[1]
            if field1394 is not None:
                self.newline()
                assert field1394 is not None
                opt_val1395 = field1394
                self.pretty_csv_locator_inline_data(opt_val1395)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1400 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1400 is not None:
            assert flat1400 is not None
            self.write(flat1400)
            return None
        else:
            fields1397 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1397) == 0:
                self.newline()
                for i1399, elem1398 in enumerate(fields1397):
                    if (i1399 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1398))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1402 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1402 is not None:
            assert flat1402 is not None
            self.write(flat1402)
            return None
        else:
            fields1401 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1401))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1405 = self._try_flat(msg, self.pretty_csv_config)
        if flat1405 is not None:
            assert flat1405 is not None
            self.write(flat1405)
            return None
        else:
            _dollar_dollar = msg
            _t1719 = self.deconstruct_csv_config(_dollar_dollar)
            fields1403 = _t1719
            assert fields1403 is not None
            unwrapped_fields1404 = fields1403
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1404)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1409 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1409 is not None:
            assert flat1409 is not None
            self.write(flat1409)
            return None
        else:
            fields1406 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1406) == 0:
                self.newline()
                for i1408, elem1407 in enumerate(fields1406):
                    if (i1408 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1407)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1418 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1418 is not None:
            assert flat1418 is not None
            self.write(flat1418)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1720 = _dollar_dollar.target_id
            else:
                _t1720 = None
            fields1410 = (_dollar_dollar.column_path, _t1720, _dollar_dollar.types,)
            assert fields1410 is not None
            unwrapped_fields1411 = fields1410
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1412 = unwrapped_fields1411[0]
            self.pretty_gnf_column_path(field1412)
            field1413 = unwrapped_fields1411[1]
            if field1413 is not None:
                self.newline()
                assert field1413 is not None
                opt_val1414 = field1413
                self.pretty_relation_id(opt_val1414)
            self.newline()
            self.write("[")
            field1415 = unwrapped_fields1411[2]
            for i1417, elem1416 in enumerate(field1415):
                if (i1417 > 0):
                    self.newline()
                self.pretty_type(elem1416)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1425 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1425 is not None:
            assert flat1425 is not None
            self.write(flat1425)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1721 = _dollar_dollar[0]
            else:
                _t1721 = None
            deconstruct_result1423 = _t1721
            if deconstruct_result1423 is not None:
                assert deconstruct_result1423 is not None
                unwrapped1424 = deconstruct_result1423
                self.write(self.format_string_value(unwrapped1424))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1722 = _dollar_dollar
                else:
                    _t1722 = None
                deconstruct_result1419 = _t1722
                if deconstruct_result1419 is not None:
                    assert deconstruct_result1419 is not None
                    unwrapped1420 = deconstruct_result1419
                    self.write("[")
                    self.indent()
                    for i1422, elem1421 in enumerate(unwrapped1420):
                        if (i1422 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1421))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1427 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1427 is not None:
            assert flat1427 is not None
            self.write(flat1427)
            return None
        else:
            fields1426 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1426))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1438 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1438 is not None:
            assert flat1438 is not None
            self.write(flat1438)
            return None
        else:
            _dollar_dollar = msg
            _t1723 = self.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
            _t1724 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1428 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1723, _t1724, _dollar_dollar.returns_delta,)
            assert fields1428 is not None
            unwrapped_fields1429 = fields1428
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1430 = unwrapped_fields1429[0]
            self.pretty_iceberg_locator(field1430)
            self.newline()
            field1431 = unwrapped_fields1429[1]
            self.pretty_iceberg_catalog_config(field1431)
            self.newline()
            field1432 = unwrapped_fields1429[2]
            self.pretty_gnf_columns(field1432)
            field1433 = unwrapped_fields1429[3]
            if field1433 is not None:
                self.newline()
                assert field1433 is not None
                opt_val1434 = field1433
                self.pretty_iceberg_from_snapshot(opt_val1434)
            field1435 = unwrapped_fields1429[4]
            if field1435 is not None:
                self.newline()
                assert field1435 is not None
                opt_val1436 = field1435
                self.pretty_iceberg_to_snapshot(opt_val1436)
            self.newline()
            field1437 = unwrapped_fields1429[5]
            self.pretty_boolean_value(field1437)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1444 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1444 is not None:
            assert flat1444 is not None
            self.write(flat1444)
            return None
        else:
            _dollar_dollar = msg
            fields1439 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1439 is not None
            unwrapped_fields1440 = fields1439
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            field1441 = unwrapped_fields1440[0]
            self.pretty_iceberg_locator_table_name(field1441)
            self.newline()
            field1442 = unwrapped_fields1440[1]
            self.pretty_iceberg_locator_namespace(field1442)
            self.newline()
            field1443 = unwrapped_fields1440[2]
            self.pretty_iceberg_locator_warehouse(field1443)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_table_name(self, msg: str):
        flat1446 = self._try_flat(msg, self.pretty_iceberg_locator_table_name)
        if flat1446 is not None:
            assert flat1446 is not None
            self.write(flat1446)
            return None
        else:
            fields1445 = msg
            self.write("(table_name")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1445))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_namespace(self, msg: Sequence[str]):
        flat1450 = self._try_flat(msg, self.pretty_iceberg_locator_namespace)
        if flat1450 is not None:
            assert flat1450 is not None
            self.write(flat1450)
            return None
        else:
            fields1447 = msg
            self.write("(namespace")
            self.indent_sexp()
            if not len(fields1447) == 0:
                self.newline()
                for i1449, elem1448 in enumerate(fields1447):
                    if (i1449 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1448))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_warehouse(self, msg: str):
        flat1452 = self._try_flat(msg, self.pretty_iceberg_locator_warehouse)
        if flat1452 is not None:
            assert flat1452 is not None
            self.write(flat1452)
            return None
        else:
            fields1451 = msg
            self.write("(warehouse")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1451))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1460 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1460 is not None:
            assert flat1460 is not None
            self.write(flat1460)
            return None
        else:
            _dollar_dollar = msg
            _t1725 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1453 = (_dollar_dollar.catalog_uri, _t1725, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1453 is not None
            unwrapped_fields1454 = fields1453
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            field1455 = unwrapped_fields1454[0]
            self.pretty_iceberg_catalog_uri(field1455)
            field1456 = unwrapped_fields1454[1]
            if field1456 is not None:
                self.newline()
                assert field1456 is not None
                opt_val1457 = field1456
                self.pretty_iceberg_catalog_config_scope(opt_val1457)
            self.newline()
            field1458 = unwrapped_fields1454[2]
            self.pretty_iceberg_properties(field1458)
            self.newline()
            field1459 = unwrapped_fields1454[3]
            self.pretty_iceberg_auth_properties(field1459)
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_uri(self, msg: str):
        flat1462 = self._try_flat(msg, self.pretty_iceberg_catalog_uri)
        if flat1462 is not None:
            assert flat1462 is not None
            self.write(flat1462)
            return None
        else:
            fields1461 = msg
            self.write("(catalog_uri")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1461))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1464 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1464 is not None:
            assert flat1464 is not None
            self.write(flat1464)
            return None
        else:
            fields1463 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1463))
            self.dedent()
            self.write(")")

    def pretty_iceberg_properties(self, msg: Sequence[tuple[str, str]]):
        flat1468 = self._try_flat(msg, self.pretty_iceberg_properties)
        if flat1468 is not None:
            assert flat1468 is not None
            self.write(flat1468)
            return None
        else:
            fields1465 = msg
            self.write("(properties")
            self.indent_sexp()
            if not len(fields1465) == 0:
                self.newline()
                for i1467, elem1466 in enumerate(fields1465):
                    if (i1467 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1466)
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1473 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1473 is not None:
            assert flat1473 is not None
            self.write(flat1473)
            return None
        else:
            _dollar_dollar = msg
            fields1469 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1469 is not None
            unwrapped_fields1470 = fields1469
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1471 = unwrapped_fields1470[0]
            self.write(self.format_string_value(field1471))
            self.newline()
            field1472 = unwrapped_fields1470[1]
            self.write(self.format_string_value(field1472))
            self.dedent()
            self.write(")")

    def pretty_iceberg_auth_properties(self, msg: Sequence[tuple[str, str]]):
        flat1477 = self._try_flat(msg, self.pretty_iceberg_auth_properties)
        if flat1477 is not None:
            assert flat1477 is not None
            self.write(flat1477)
            return None
        else:
            fields1474 = msg
            self.write("(auth_properties")
            self.indent_sexp()
            if not len(fields1474) == 0:
                self.newline()
                for i1476, elem1475 in enumerate(fields1474):
                    if (i1476 > 0):
                        self.newline()
                    self.pretty_iceberg_masked_property_entry(elem1475)
            self.dedent()
            self.write(")")

    def pretty_iceberg_masked_property_entry(self, msg: tuple[str, str]):
        flat1482 = self._try_flat(msg, self.pretty_iceberg_masked_property_entry)
        if flat1482 is not None:
            assert flat1482 is not None
            self.write(flat1482)
            return None
        else:
            _dollar_dollar = msg
            _t1726 = self.mask_secret_value(_dollar_dollar)
            fields1478 = (_dollar_dollar[0], _t1726,)
            assert fields1478 is not None
            unwrapped_fields1479 = fields1478
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1480 = unwrapped_fields1479[0]
            self.write(self.format_string_value(field1480))
            self.newline()
            field1481 = unwrapped_fields1479[1]
            self.write(self.format_string_value(field1481))
            self.dedent()
            self.write(")")

    def pretty_iceberg_from_snapshot(self, msg: str):
        flat1484 = self._try_flat(msg, self.pretty_iceberg_from_snapshot)
        if flat1484 is not None:
            assert flat1484 is not None
            self.write(flat1484)
            return None
        else:
            fields1483 = msg
            self.write("(from_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1483))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1486 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1486 is not None:
            assert flat1486 is not None
            self.write(flat1486)
            return None
        else:
            fields1485 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1485))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1489 = self._try_flat(msg, self.pretty_undefine)
        if flat1489 is not None:
            assert flat1489 is not None
            self.write(flat1489)
            return None
        else:
            _dollar_dollar = msg
            fields1487 = _dollar_dollar.fragment_id
            assert fields1487 is not None
            unwrapped_fields1488 = fields1487
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1488)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1494 = self._try_flat(msg, self.pretty_context)
        if flat1494 is not None:
            assert flat1494 is not None
            self.write(flat1494)
            return None
        else:
            _dollar_dollar = msg
            fields1490 = _dollar_dollar.relations
            assert fields1490 is not None
            unwrapped_fields1491 = fields1490
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1491) == 0:
                self.newline()
                for i1493, elem1492 in enumerate(unwrapped_fields1491):
                    if (i1493 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1492)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1501 = self._try_flat(msg, self.pretty_snapshot)
        if flat1501 is not None:
            assert flat1501 is not None
            self.write(flat1501)
            return None
        else:
            _dollar_dollar = msg
            fields1495 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
            assert fields1495 is not None
            unwrapped_fields1496 = fields1495
            self.write("(snapshot")
            self.indent_sexp()
            self.newline()
            field1497 = unwrapped_fields1496[0]
            self.pretty_edb_path(field1497)
            field1498 = unwrapped_fields1496[1]
            if not len(field1498) == 0:
                self.newline()
                for i1500, elem1499 in enumerate(field1498):
                    if (i1500 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1499)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1506 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1506 is not None:
            assert flat1506 is not None
            self.write(flat1506)
            return None
        else:
            _dollar_dollar = msg
            fields1502 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1502 is not None
            unwrapped_fields1503 = fields1502
            field1504 = unwrapped_fields1503[0]
            self.pretty_edb_path(field1504)
            self.write(" ")
            field1505 = unwrapped_fields1503[1]
            self.pretty_relation_id(field1505)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1510 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1510 is not None:
            assert flat1510 is not None
            self.write(flat1510)
            return None
        else:
            fields1507 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1507) == 0:
                self.newline()
                for i1509, elem1508 in enumerate(fields1507):
                    if (i1509 > 0):
                        self.newline()
                    self.pretty_read(elem1508)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1521 = self._try_flat(msg, self.pretty_read)
        if flat1521 is not None:
            assert flat1521 is not None
            self.write(flat1521)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1727 = _dollar_dollar.demand
            else:
                _t1727 = None
            deconstruct_result1519 = _t1727
            if deconstruct_result1519 is not None:
                assert deconstruct_result1519 is not None
                unwrapped1520 = deconstruct_result1519
                self.pretty_demand(unwrapped1520)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1728 = _dollar_dollar.output
                else:
                    _t1728 = None
                deconstruct_result1517 = _t1728
                if deconstruct_result1517 is not None:
                    assert deconstruct_result1517 is not None
                    unwrapped1518 = deconstruct_result1517
                    self.pretty_output(unwrapped1518)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1729 = _dollar_dollar.what_if
                    else:
                        _t1729 = None
                    deconstruct_result1515 = _t1729
                    if deconstruct_result1515 is not None:
                        assert deconstruct_result1515 is not None
                        unwrapped1516 = deconstruct_result1515
                        self.pretty_what_if(unwrapped1516)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1730 = _dollar_dollar.abort
                        else:
                            _t1730 = None
                        deconstruct_result1513 = _t1730
                        if deconstruct_result1513 is not None:
                            assert deconstruct_result1513 is not None
                            unwrapped1514 = deconstruct_result1513
                            self.pretty_abort(unwrapped1514)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1731 = _dollar_dollar.export
                            else:
                                _t1731 = None
                            deconstruct_result1511 = _t1731
                            if deconstruct_result1511 is not None:
                                assert deconstruct_result1511 is not None
                                unwrapped1512 = deconstruct_result1511
                                self.pretty_export(unwrapped1512)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1524 = self._try_flat(msg, self.pretty_demand)
        if flat1524 is not None:
            assert flat1524 is not None
            self.write(flat1524)
            return None
        else:
            _dollar_dollar = msg
            fields1522 = _dollar_dollar.relation_id
            assert fields1522 is not None
            unwrapped_fields1523 = fields1522
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1523)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1529 = self._try_flat(msg, self.pretty_output)
        if flat1529 is not None:
            assert flat1529 is not None
            self.write(flat1529)
            return None
        else:
            _dollar_dollar = msg
            fields1525 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1525 is not None
            unwrapped_fields1526 = fields1525
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1527 = unwrapped_fields1526[0]
            self.pretty_name(field1527)
            self.newline()
            field1528 = unwrapped_fields1526[1]
            self.pretty_relation_id(field1528)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1534 = self._try_flat(msg, self.pretty_what_if)
        if flat1534 is not None:
            assert flat1534 is not None
            self.write(flat1534)
            return None
        else:
            _dollar_dollar = msg
            fields1530 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1530 is not None
            unwrapped_fields1531 = fields1530
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1532 = unwrapped_fields1531[0]
            self.pretty_name(field1532)
            self.newline()
            field1533 = unwrapped_fields1531[1]
            self.pretty_epoch(field1533)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1540 = self._try_flat(msg, self.pretty_abort)
        if flat1540 is not None:
            assert flat1540 is not None
            self.write(flat1540)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1732 = _dollar_dollar.name
            else:
                _t1732 = None
            fields1535 = (_t1732, _dollar_dollar.relation_id,)
            assert fields1535 is not None
            unwrapped_fields1536 = fields1535
            self.write("(abort")
            self.indent_sexp()
            field1537 = unwrapped_fields1536[0]
            if field1537 is not None:
                self.newline()
                assert field1537 is not None
                opt_val1538 = field1537
                self.pretty_name(opt_val1538)
            self.newline()
            field1539 = unwrapped_fields1536[1]
            self.pretty_relation_id(field1539)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1545 = self._try_flat(msg, self.pretty_export)
        if flat1545 is not None:
            assert flat1545 is not None
            self.write(flat1545)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1733 = _dollar_dollar.csv_config
            else:
                _t1733 = None
            deconstruct_result1543 = _t1733
            if deconstruct_result1543 is not None:
                assert deconstruct_result1543 is not None
                unwrapped1544 = deconstruct_result1543
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1544)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1734 = _dollar_dollar.iceberg_config
                else:
                    _t1734 = None
                deconstruct_result1541 = _t1734
                if deconstruct_result1541 is not None:
                    assert deconstruct_result1541 is not None
                    unwrapped1542 = deconstruct_result1541
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1542)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1556 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1556 is not None:
            assert flat1556 is not None
            self.write(flat1556)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1735 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1735 = None
            deconstruct_result1551 = _t1735
            if deconstruct_result1551 is not None:
                assert deconstruct_result1551 is not None
                unwrapped1552 = deconstruct_result1551
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1553 = unwrapped1552[0]
                self.pretty_export_csv_path(field1553)
                self.newline()
                field1554 = unwrapped1552[1]
                self.pretty_export_csv_source(field1554)
                self.newline()
                field1555 = unwrapped1552[2]
                self.pretty_csv_config(field1555)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1737 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1736 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1737,)
                else:
                    _t1736 = None
                deconstruct_result1546 = _t1736
                if deconstruct_result1546 is not None:
                    assert deconstruct_result1546 is not None
                    unwrapped1547 = deconstruct_result1546
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1548 = unwrapped1547[0]
                    self.pretty_export_csv_path(field1548)
                    self.newline()
                    field1549 = unwrapped1547[1]
                    self.pretty_export_csv_columns_list(field1549)
                    self.newline()
                    field1550 = unwrapped1547[2]
                    self.pretty_config_dict(field1550)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1558 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1558 is not None:
            assert flat1558 is not None
            self.write(flat1558)
            return None
        else:
            fields1557 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1557))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1565 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1565 is not None:
            assert flat1565 is not None
            self.write(flat1565)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1738 = _dollar_dollar.gnf_columns.columns
            else:
                _t1738 = None
            deconstruct_result1561 = _t1738
            if deconstruct_result1561 is not None:
                assert deconstruct_result1561 is not None
                unwrapped1562 = deconstruct_result1561
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1562) == 0:
                    self.newline()
                    for i1564, elem1563 in enumerate(unwrapped1562):
                        if (i1564 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1563)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1739 = _dollar_dollar.table_def
                else:
                    _t1739 = None
                deconstruct_result1559 = _t1739
                if deconstruct_result1559 is not None:
                    assert deconstruct_result1559 is not None
                    unwrapped1560 = deconstruct_result1559
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1560)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1570 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1570 is not None:
            assert flat1570 is not None
            self.write(flat1570)
            return None
        else:
            _dollar_dollar = msg
            fields1566 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1566 is not None
            unwrapped_fields1567 = fields1566
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1568 = unwrapped_fields1567[0]
            self.write(self.format_string_value(field1568))
            self.newline()
            field1569 = unwrapped_fields1567[1]
            self.pretty_relation_id(field1569)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1574 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1574 is not None:
            assert flat1574 is not None
            self.write(flat1574)
            return None
        else:
            fields1571 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1571) == 0:
                self.newline()
                for i1573, elem1572 in enumerate(fields1571):
                    if (i1573 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1572)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1584 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1584 is not None:
            assert flat1584 is not None
            self.write(flat1584)
            return None
        else:
            _dollar_dollar = msg
            _t1740 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1575 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, _dollar_dollar.columns, sorted(_dollar_dollar.table_properties.items()), _t1740,)
            assert fields1575 is not None
            unwrapped_fields1576 = fields1575
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1577 = unwrapped_fields1576[0]
            self.pretty_iceberg_locator(field1577)
            self.newline()
            field1578 = unwrapped_fields1576[1]
            self.pretty_iceberg_catalog_config(field1578)
            self.newline()
            field1579 = unwrapped_fields1576[2]
            self.pretty_export_iceberg_table_def(field1579)
            self.newline()
            field1580 = unwrapped_fields1576[3]
            self.pretty_export_iceberg_columns(field1580)
            self.newline()
            field1581 = unwrapped_fields1576[4]
            self.pretty_iceberg_table_properties(field1581)
            field1582 = unwrapped_fields1576[5]
            if field1582 is not None:
                self.newline()
                assert field1582 is not None
                opt_val1583 = field1582
                self.pretty_config_dict(opt_val1583)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_table_def(self, msg: logic_pb2.RelationId):
        flat1586 = self._try_flat(msg, self.pretty_export_iceberg_table_def)
        if flat1586 is not None:
            assert flat1586 is not None
            self.write(flat1586)
            return None
        else:
            fields1585 = msg
            self.write("(table_def")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1585)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_columns(self, msg: Sequence[transactions_pb2.ExportColumn]):
        flat1590 = self._try_flat(msg, self.pretty_export_iceberg_columns)
        if flat1590 is not None:
            assert flat1590 is not None
            self.write(flat1590)
            return None
        else:
            fields1587 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1587) == 0:
                self.newline()
                for i1589, elem1588 in enumerate(fields1587):
                    if (i1589 > 0):
                        self.newline()
                    self.pretty_export_iceberg_column(elem1588)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_column(self, msg: transactions_pb2.ExportColumn):
        flat1595 = self._try_flat(msg, self.pretty_export_iceberg_column)
        if flat1595 is not None:
            assert flat1595 is not None
            self.write(flat1595)
            return None
        else:
            _dollar_dollar = msg
            fields1591 = (_dollar_dollar.name, _dollar_dollar.nullable,)
            assert fields1591 is not None
            unwrapped_fields1592 = fields1591
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1593 = unwrapped_fields1592[0]
            self.write(self.format_string_value(field1593))
            self.newline()
            field1594 = unwrapped_fields1592[1]
            self.pretty_boolean_value(field1594)
            self.dedent()
            self.write(")")

    def pretty_iceberg_table_properties(self, msg: Sequence[tuple[str, str]]):
        flat1599 = self._try_flat(msg, self.pretty_iceberg_table_properties)
        if flat1599 is not None:
            assert flat1599 is not None
            self.write(flat1599)
            return None
        else:
            fields1596 = msg
            self.write("(table_properties")
            self.indent_sexp()
            if not len(fields1596) == 0:
                self.newline()
                for i1598, elem1597 in enumerate(fields1596):
                    if (i1598 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1597)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1786 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1786)
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
        elif isinstance(msg, transactions_pb2.ExportColumn):
            self.pretty_export_iceberg_column(msg)
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
