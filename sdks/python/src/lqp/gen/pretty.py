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
        _t1759 = logic_pb2.Value(int32_value=v)
        return _t1759

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1760 = logic_pb2.Value(int_value=v)
        return _t1760

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1761 = logic_pb2.Value(float_value=v)
        return _t1761

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1762 = logic_pb2.Value(string_value=v)
        return _t1762

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1763 = logic_pb2.Value(boolean_value=v)
        return _t1763

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1764 = logic_pb2.Value(uint128_value=v)
        return _t1764

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1765 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1765,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1766 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1766,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1767 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1767,))
        _t1768 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1768,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1769 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1769,))
        _t1770 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1770,))
        if msg.new_line != "":
            _t1771 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1771,))
        _t1772 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1772,))
        _t1773 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1773,))
        _t1774 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1774,))
        if msg.comment != "":
            _t1775 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1775,))
        for missing_string in msg.missing_strings:
            _t1776 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1776,))
        _t1777 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1777,))
        _t1778 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1778,))
        _t1779 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1779,))
        if msg.partition_size_mb != 0:
            _t1780 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1780,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1781 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1781,))
        _t1782 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1782,))
        _t1783 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1783,))
        _t1784 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1784,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1785 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1785,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1786 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1786,))
        _t1787 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1787,))
        _t1788 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1788,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1789 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1789,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1790 = self._make_value_string(msg.compression)
            result.append(("compression", _t1790,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1791 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1791,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1792 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1792,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1793 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1793,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1794 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1794,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1795 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1795,))
        return sorted(result)

    def mask_secret_value(self, pair: tuple[str, str]) -> str:
        return "***"

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1796 = None
        return None

    def deconstruct_iceberg_data_from_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.from_snapshot is not None
        if msg.from_snapshot != "":
            assert msg.from_snapshot is not None
            return msg.from_snapshot
        else:
            _t1797 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1798 = None
        return None

    def deconstruct_csv_data_columns_optional(self, msg: logic_pb2.CSVData) -> Sequence[logic_pb2.GNFColumn] | None:
        if not msg.HasField("target"):
            return msg.columns
        else:
            _t1799 = None
        return None

    def deconstruct_csv_data_target_optional(self, msg: logic_pb2.CSVData) -> logic_pb2.CSVTarget | None:
        if msg.HasField("target"):
            assert msg.target is not None
            return msg.target
        else:
            _t1800 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1801 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1801,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1802 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1802,))
        if msg.compression != "":
            _t1803 = self._make_value_string(msg.compression)
            result.append(("compression", _t1803,))
        if len(result) == 0:
            return None
        else:
            _t1804 = None
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
            _t1805 = None
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
        flat816 = self._try_flat(msg, self.pretty_transaction)
        if flat816 is not None:
            assert flat816 is not None
            self.write(flat816)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1614 = _dollar_dollar.configure
            else:
                _t1614 = None
            if _dollar_dollar.HasField("sync"):
                _t1615 = _dollar_dollar.sync
            else:
                _t1615 = None
            fields807 = (_t1614, _t1615, _dollar_dollar.epochs,)
            assert fields807 is not None
            unwrapped_fields808 = fields807
            self.write("(transaction")
            self.indent_sexp()
            field809 = unwrapped_fields808[0]
            if field809 is not None:
                self.newline()
                assert field809 is not None
                opt_val810 = field809
                self.pretty_configure(opt_val810)
            field811 = unwrapped_fields808[1]
            if field811 is not None:
                self.newline()
                assert field811 is not None
                opt_val812 = field811
                self.pretty_sync(opt_val812)
            field813 = unwrapped_fields808[2]
            if not len(field813) == 0:
                self.newline()
                for i815, elem814 in enumerate(field813):
                    if (i815 > 0):
                        self.newline()
                    self.pretty_epoch(elem814)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat819 = self._try_flat(msg, self.pretty_configure)
        if flat819 is not None:
            assert flat819 is not None
            self.write(flat819)
            return None
        else:
            _dollar_dollar = msg
            _t1616 = self.deconstruct_configure(_dollar_dollar)
            fields817 = _t1616
            assert fields817 is not None
            unwrapped_fields818 = fields817
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields818)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat823 = self._try_flat(msg, self.pretty_config_dict)
        if flat823 is not None:
            assert flat823 is not None
            self.write(flat823)
            return None
        else:
            fields820 = msg
            self.write("{")
            self.indent()
            if not len(fields820) == 0:
                self.newline()
                for i822, elem821 in enumerate(fields820):
                    if (i822 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem821)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat828 = self._try_flat(msg, self.pretty_config_key_value)
        if flat828 is not None:
            assert flat828 is not None
            self.write(flat828)
            return None
        else:
            _dollar_dollar = msg
            fields824 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields824 is not None
            unwrapped_fields825 = fields824
            self.write(":")
            field826 = unwrapped_fields825[0]
            self.write(field826)
            self.write(" ")
            field827 = unwrapped_fields825[1]
            self.pretty_raw_value(field827)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat854 = self._try_flat(msg, self.pretty_raw_value)
        if flat854 is not None:
            assert flat854 is not None
            self.write(flat854)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1617 = _dollar_dollar.date_value
            else:
                _t1617 = None
            deconstruct_result852 = _t1617
            if deconstruct_result852 is not None:
                assert deconstruct_result852 is not None
                unwrapped853 = deconstruct_result852
                self.pretty_raw_date(unwrapped853)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1618 = _dollar_dollar.datetime_value
                else:
                    _t1618 = None
                deconstruct_result850 = _t1618
                if deconstruct_result850 is not None:
                    assert deconstruct_result850 is not None
                    unwrapped851 = deconstruct_result850
                    self.pretty_raw_datetime(unwrapped851)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1619 = _dollar_dollar.string_value
                    else:
                        _t1619 = None
                    deconstruct_result848 = _t1619
                    if deconstruct_result848 is not None:
                        assert deconstruct_result848 is not None
                        unwrapped849 = deconstruct_result848
                        self.write(self.format_string_value(unwrapped849))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1620 = _dollar_dollar.int32_value
                        else:
                            _t1620 = None
                        deconstruct_result846 = _t1620
                        if deconstruct_result846 is not None:
                            assert deconstruct_result846 is not None
                            unwrapped847 = deconstruct_result846
                            self.write((str(unwrapped847) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1621 = _dollar_dollar.int_value
                            else:
                                _t1621 = None
                            deconstruct_result844 = _t1621
                            if deconstruct_result844 is not None:
                                assert deconstruct_result844 is not None
                                unwrapped845 = deconstruct_result844
                                self.write(str(unwrapped845))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1622 = _dollar_dollar.float32_value
                                else:
                                    _t1622 = None
                                deconstruct_result842 = _t1622
                                if deconstruct_result842 is not None:
                                    assert deconstruct_result842 is not None
                                    unwrapped843 = deconstruct_result842
                                    self.write(self.format_float32_literal(unwrapped843))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1623 = _dollar_dollar.float_value
                                    else:
                                        _t1623 = None
                                    deconstruct_result840 = _t1623
                                    if deconstruct_result840 is not None:
                                        assert deconstruct_result840 is not None
                                        unwrapped841 = deconstruct_result840
                                        self.write(str(unwrapped841))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1624 = _dollar_dollar.uint32_value
                                        else:
                                            _t1624 = None
                                        deconstruct_result838 = _t1624
                                        if deconstruct_result838 is not None:
                                            assert deconstruct_result838 is not None
                                            unwrapped839 = deconstruct_result838
                                            self.write((str(unwrapped839) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1625 = _dollar_dollar.uint128_value
                                            else:
                                                _t1625 = None
                                            deconstruct_result836 = _t1625
                                            if deconstruct_result836 is not None:
                                                assert deconstruct_result836 is not None
                                                unwrapped837 = deconstruct_result836
                                                self.write(self.format_uint128(unwrapped837))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1626 = _dollar_dollar.int128_value
                                                else:
                                                    _t1626 = None
                                                deconstruct_result834 = _t1626
                                                if deconstruct_result834 is not None:
                                                    assert deconstruct_result834 is not None
                                                    unwrapped835 = deconstruct_result834
                                                    self.write(self.format_int128(unwrapped835))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1627 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1627 = None
                                                    deconstruct_result832 = _t1627
                                                    if deconstruct_result832 is not None:
                                                        assert deconstruct_result832 is not None
                                                        unwrapped833 = deconstruct_result832
                                                        self.write(self.format_decimal(unwrapped833))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1628 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1628 = None
                                                        deconstruct_result830 = _t1628
                                                        if deconstruct_result830 is not None:
                                                            assert deconstruct_result830 is not None
                                                            unwrapped831 = deconstruct_result830
                                                            self.pretty_boolean_value(unwrapped831)
                                                        else:
                                                            fields829 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat860 = self._try_flat(msg, self.pretty_raw_date)
        if flat860 is not None:
            assert flat860 is not None
            self.write(flat860)
            return None
        else:
            _dollar_dollar = msg
            fields855 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields855 is not None
            unwrapped_fields856 = fields855
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field857 = unwrapped_fields856[0]
            self.write(str(field857))
            self.newline()
            field858 = unwrapped_fields856[1]
            self.write(str(field858))
            self.newline()
            field859 = unwrapped_fields856[2]
            self.write(str(field859))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat871 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat871 is not None:
            assert flat871 is not None
            self.write(flat871)
            return None
        else:
            _dollar_dollar = msg
            fields861 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields861 is not None
            unwrapped_fields862 = fields861
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field863 = unwrapped_fields862[0]
            self.write(str(field863))
            self.newline()
            field864 = unwrapped_fields862[1]
            self.write(str(field864))
            self.newline()
            field865 = unwrapped_fields862[2]
            self.write(str(field865))
            self.newline()
            field866 = unwrapped_fields862[3]
            self.write(str(field866))
            self.newline()
            field867 = unwrapped_fields862[4]
            self.write(str(field867))
            self.newline()
            field868 = unwrapped_fields862[5]
            self.write(str(field868))
            field869 = unwrapped_fields862[6]
            if field869 is not None:
                self.newline()
                assert field869 is not None
                opt_val870 = field869
                self.write(str(opt_val870))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1629 = ()
        else:
            _t1629 = None
        deconstruct_result874 = _t1629
        if deconstruct_result874 is not None:
            assert deconstruct_result874 is not None
            unwrapped875 = deconstruct_result874
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1630 = ()
            else:
                _t1630 = None
            deconstruct_result872 = _t1630
            if deconstruct_result872 is not None:
                assert deconstruct_result872 is not None
                unwrapped873 = deconstruct_result872
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat880 = self._try_flat(msg, self.pretty_sync)
        if flat880 is not None:
            assert flat880 is not None
            self.write(flat880)
            return None
        else:
            _dollar_dollar = msg
            fields876 = _dollar_dollar.fragments
            assert fields876 is not None
            unwrapped_fields877 = fields876
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields877) == 0:
                self.newline()
                for i879, elem878 in enumerate(unwrapped_fields877):
                    if (i879 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem878)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat883 = self._try_flat(msg, self.pretty_fragment_id)
        if flat883 is not None:
            assert flat883 is not None
            self.write(flat883)
            return None
        else:
            _dollar_dollar = msg
            fields881 = self.fragment_id_to_string(_dollar_dollar)
            assert fields881 is not None
            unwrapped_fields882 = fields881
            self.write(":")
            self.write(unwrapped_fields882)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat890 = self._try_flat(msg, self.pretty_epoch)
        if flat890 is not None:
            assert flat890 is not None
            self.write(flat890)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1631 = _dollar_dollar.writes
            else:
                _t1631 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1632 = _dollar_dollar.reads
            else:
                _t1632 = None
            fields884 = (_t1631, _t1632,)
            assert fields884 is not None
            unwrapped_fields885 = fields884
            self.write("(epoch")
            self.indent_sexp()
            field886 = unwrapped_fields885[0]
            if field886 is not None:
                self.newline()
                assert field886 is not None
                opt_val887 = field886
                self.pretty_epoch_writes(opt_val887)
            field888 = unwrapped_fields885[1]
            if field888 is not None:
                self.newline()
                assert field888 is not None
                opt_val889 = field888
                self.pretty_epoch_reads(opt_val889)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat894 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat894 is not None:
            assert flat894 is not None
            self.write(flat894)
            return None
        else:
            fields891 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields891) == 0:
                self.newline()
                for i893, elem892 in enumerate(fields891):
                    if (i893 > 0):
                        self.newline()
                    self.pretty_write(elem892)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat903 = self._try_flat(msg, self.pretty_write)
        if flat903 is not None:
            assert flat903 is not None
            self.write(flat903)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1633 = _dollar_dollar.define
            else:
                _t1633 = None
            deconstruct_result901 = _t1633
            if deconstruct_result901 is not None:
                assert deconstruct_result901 is not None
                unwrapped902 = deconstruct_result901
                self.pretty_define(unwrapped902)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1634 = _dollar_dollar.undefine
                else:
                    _t1634 = None
                deconstruct_result899 = _t1634
                if deconstruct_result899 is not None:
                    assert deconstruct_result899 is not None
                    unwrapped900 = deconstruct_result899
                    self.pretty_undefine(unwrapped900)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1635 = _dollar_dollar.context
                    else:
                        _t1635 = None
                    deconstruct_result897 = _t1635
                    if deconstruct_result897 is not None:
                        assert deconstruct_result897 is not None
                        unwrapped898 = deconstruct_result897
                        self.pretty_context(unwrapped898)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1636 = _dollar_dollar.snapshot
                        else:
                            _t1636 = None
                        deconstruct_result895 = _t1636
                        if deconstruct_result895 is not None:
                            assert deconstruct_result895 is not None
                            unwrapped896 = deconstruct_result895
                            self.pretty_snapshot(unwrapped896)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat906 = self._try_flat(msg, self.pretty_define)
        if flat906 is not None:
            assert flat906 is not None
            self.write(flat906)
            return None
        else:
            _dollar_dollar = msg
            fields904 = _dollar_dollar.fragment
            assert fields904 is not None
            unwrapped_fields905 = fields904
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields905)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat913 = self._try_flat(msg, self.pretty_fragment)
        if flat913 is not None:
            assert flat913 is not None
            self.write(flat913)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields907 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields907 is not None
            unwrapped_fields908 = fields907
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field909 = unwrapped_fields908[0]
            self.pretty_new_fragment_id(field909)
            field910 = unwrapped_fields908[1]
            if not len(field910) == 0:
                self.newline()
                for i912, elem911 in enumerate(field910):
                    if (i912 > 0):
                        self.newline()
                    self.pretty_declaration(elem911)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat915 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat915 is not None:
            assert flat915 is not None
            self.write(flat915)
            return None
        else:
            fields914 = msg
            self.pretty_fragment_id(fields914)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat924 = self._try_flat(msg, self.pretty_declaration)
        if flat924 is not None:
            assert flat924 is not None
            self.write(flat924)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1637 = getattr(_dollar_dollar, 'def')
            else:
                _t1637 = None
            deconstruct_result922 = _t1637
            if deconstruct_result922 is not None:
                assert deconstruct_result922 is not None
                unwrapped923 = deconstruct_result922
                self.pretty_def(unwrapped923)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1638 = _dollar_dollar.algorithm
                else:
                    _t1638 = None
                deconstruct_result920 = _t1638
                if deconstruct_result920 is not None:
                    assert deconstruct_result920 is not None
                    unwrapped921 = deconstruct_result920
                    self.pretty_algorithm(unwrapped921)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1639 = _dollar_dollar.constraint
                    else:
                        _t1639 = None
                    deconstruct_result918 = _t1639
                    if deconstruct_result918 is not None:
                        assert deconstruct_result918 is not None
                        unwrapped919 = deconstruct_result918
                        self.pretty_constraint(unwrapped919)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1640 = _dollar_dollar.data
                        else:
                            _t1640 = None
                        deconstruct_result916 = _t1640
                        if deconstruct_result916 is not None:
                            assert deconstruct_result916 is not None
                            unwrapped917 = deconstruct_result916
                            self.pretty_data(unwrapped917)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat931 = self._try_flat(msg, self.pretty_def)
        if flat931 is not None:
            assert flat931 is not None
            self.write(flat931)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1641 = _dollar_dollar.attrs
            else:
                _t1641 = None
            fields925 = (_dollar_dollar.name, _dollar_dollar.body, _t1641,)
            assert fields925 is not None
            unwrapped_fields926 = fields925
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field927 = unwrapped_fields926[0]
            self.pretty_relation_id(field927)
            self.newline()
            field928 = unwrapped_fields926[1]
            self.pretty_abstraction(field928)
            field929 = unwrapped_fields926[2]
            if field929 is not None:
                self.newline()
                assert field929 is not None
                opt_val930 = field929
                self.pretty_attrs(opt_val930)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat936 = self._try_flat(msg, self.pretty_relation_id)
        if flat936 is not None:
            assert flat936 is not None
            self.write(flat936)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1643 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1642 = _t1643
            else:
                _t1642 = None
            deconstruct_result934 = _t1642
            if deconstruct_result934 is not None:
                assert deconstruct_result934 is not None
                unwrapped935 = deconstruct_result934
                self.write(":")
                self.write(unwrapped935)
            else:
                _dollar_dollar = msg
                _t1644 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result932 = _t1644
                if deconstruct_result932 is not None:
                    assert deconstruct_result932 is not None
                    unwrapped933 = deconstruct_result932
                    self.write(self.format_uint128(unwrapped933))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat941 = self._try_flat(msg, self.pretty_abstraction)
        if flat941 is not None:
            assert flat941 is not None
            self.write(flat941)
            return None
        else:
            _dollar_dollar = msg
            _t1645 = self.deconstruct_bindings(_dollar_dollar)
            fields937 = (_t1645, _dollar_dollar.value,)
            assert fields937 is not None
            unwrapped_fields938 = fields937
            self.write("(")
            self.indent()
            field939 = unwrapped_fields938[0]
            self.pretty_bindings(field939)
            self.newline()
            field940 = unwrapped_fields938[1]
            self.pretty_formula(field940)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat949 = self._try_flat(msg, self.pretty_bindings)
        if flat949 is not None:
            assert flat949 is not None
            self.write(flat949)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1646 = _dollar_dollar[1]
            else:
                _t1646 = None
            fields942 = (_dollar_dollar[0], _t1646,)
            assert fields942 is not None
            unwrapped_fields943 = fields942
            self.write("[")
            self.indent()
            field944 = unwrapped_fields943[0]
            for i946, elem945 in enumerate(field944):
                if (i946 > 0):
                    self.newline()
                self.pretty_binding(elem945)
            field947 = unwrapped_fields943[1]
            if field947 is not None:
                self.newline()
                assert field947 is not None
                opt_val948 = field947
                self.pretty_value_bindings(opt_val948)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat954 = self._try_flat(msg, self.pretty_binding)
        if flat954 is not None:
            assert flat954 is not None
            self.write(flat954)
            return None
        else:
            _dollar_dollar = msg
            fields950 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields950 is not None
            unwrapped_fields951 = fields950
            field952 = unwrapped_fields951[0]
            self.write(field952)
            self.write("::")
            field953 = unwrapped_fields951[1]
            self.pretty_type(field953)

    def pretty_type(self, msg: logic_pb2.Type):
        flat983 = self._try_flat(msg, self.pretty_type)
        if flat983 is not None:
            assert flat983 is not None
            self.write(flat983)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1647 = _dollar_dollar.unspecified_type
            else:
                _t1647 = None
            deconstruct_result981 = _t1647
            if deconstruct_result981 is not None:
                assert deconstruct_result981 is not None
                unwrapped982 = deconstruct_result981
                self.pretty_unspecified_type(unwrapped982)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1648 = _dollar_dollar.string_type
                else:
                    _t1648 = None
                deconstruct_result979 = _t1648
                if deconstruct_result979 is not None:
                    assert deconstruct_result979 is not None
                    unwrapped980 = deconstruct_result979
                    self.pretty_string_type(unwrapped980)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1649 = _dollar_dollar.int_type
                    else:
                        _t1649 = None
                    deconstruct_result977 = _t1649
                    if deconstruct_result977 is not None:
                        assert deconstruct_result977 is not None
                        unwrapped978 = deconstruct_result977
                        self.pretty_int_type(unwrapped978)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1650 = _dollar_dollar.float_type
                        else:
                            _t1650 = None
                        deconstruct_result975 = _t1650
                        if deconstruct_result975 is not None:
                            assert deconstruct_result975 is not None
                            unwrapped976 = deconstruct_result975
                            self.pretty_float_type(unwrapped976)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1651 = _dollar_dollar.uint128_type
                            else:
                                _t1651 = None
                            deconstruct_result973 = _t1651
                            if deconstruct_result973 is not None:
                                assert deconstruct_result973 is not None
                                unwrapped974 = deconstruct_result973
                                self.pretty_uint128_type(unwrapped974)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1652 = _dollar_dollar.int128_type
                                else:
                                    _t1652 = None
                                deconstruct_result971 = _t1652
                                if deconstruct_result971 is not None:
                                    assert deconstruct_result971 is not None
                                    unwrapped972 = deconstruct_result971
                                    self.pretty_int128_type(unwrapped972)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1653 = _dollar_dollar.date_type
                                    else:
                                        _t1653 = None
                                    deconstruct_result969 = _t1653
                                    if deconstruct_result969 is not None:
                                        assert deconstruct_result969 is not None
                                        unwrapped970 = deconstruct_result969
                                        self.pretty_date_type(unwrapped970)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1654 = _dollar_dollar.datetime_type
                                        else:
                                            _t1654 = None
                                        deconstruct_result967 = _t1654
                                        if deconstruct_result967 is not None:
                                            assert deconstruct_result967 is not None
                                            unwrapped968 = deconstruct_result967
                                            self.pretty_datetime_type(unwrapped968)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1655 = _dollar_dollar.missing_type
                                            else:
                                                _t1655 = None
                                            deconstruct_result965 = _t1655
                                            if deconstruct_result965 is not None:
                                                assert deconstruct_result965 is not None
                                                unwrapped966 = deconstruct_result965
                                                self.pretty_missing_type(unwrapped966)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1656 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1656 = None
                                                deconstruct_result963 = _t1656
                                                if deconstruct_result963 is not None:
                                                    assert deconstruct_result963 is not None
                                                    unwrapped964 = deconstruct_result963
                                                    self.pretty_decimal_type(unwrapped964)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1657 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1657 = None
                                                    deconstruct_result961 = _t1657
                                                    if deconstruct_result961 is not None:
                                                        assert deconstruct_result961 is not None
                                                        unwrapped962 = deconstruct_result961
                                                        self.pretty_boolean_type(unwrapped962)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1658 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1658 = None
                                                        deconstruct_result959 = _t1658
                                                        if deconstruct_result959 is not None:
                                                            assert deconstruct_result959 is not None
                                                            unwrapped960 = deconstruct_result959
                                                            self.pretty_int32_type(unwrapped960)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1659 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1659 = None
                                                            deconstruct_result957 = _t1659
                                                            if deconstruct_result957 is not None:
                                                                assert deconstruct_result957 is not None
                                                                unwrapped958 = deconstruct_result957
                                                                self.pretty_float32_type(unwrapped958)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1660 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1660 = None
                                                                deconstruct_result955 = _t1660
                                                                if deconstruct_result955 is not None:
                                                                    assert deconstruct_result955 is not None
                                                                    unwrapped956 = deconstruct_result955
                                                                    self.pretty_uint32_type(unwrapped956)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields984 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields985 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields986 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields987 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields988 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields989 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields990 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields991 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields992 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat997 = self._try_flat(msg, self.pretty_decimal_type)
        if flat997 is not None:
            assert flat997 is not None
            self.write(flat997)
            return None
        else:
            _dollar_dollar = msg
            fields993 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields993 is not None
            unwrapped_fields994 = fields993
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field995 = unwrapped_fields994[0]
            self.write(str(field995))
            self.newline()
            field996 = unwrapped_fields994[1]
            self.write(str(field996))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields998 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields999 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields1000 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields1001 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat1005 = self._try_flat(msg, self.pretty_value_bindings)
        if flat1005 is not None:
            assert flat1005 is not None
            self.write(flat1005)
            return None
        else:
            fields1002 = msg
            self.write("|")
            if not len(fields1002) == 0:
                self.write(" ")
                for i1004, elem1003 in enumerate(fields1002):
                    if (i1004 > 0):
                        self.newline()
                    self.pretty_binding(elem1003)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1032 = self._try_flat(msg, self.pretty_formula)
        if flat1032 is not None:
            assert flat1032 is not None
            self.write(flat1032)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1661 = _dollar_dollar.conjunction
            else:
                _t1661 = None
            deconstruct_result1030 = _t1661
            if deconstruct_result1030 is not None:
                assert deconstruct_result1030 is not None
                unwrapped1031 = deconstruct_result1030
                self.pretty_true(unwrapped1031)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1662 = _dollar_dollar.disjunction
                else:
                    _t1662 = None
                deconstruct_result1028 = _t1662
                if deconstruct_result1028 is not None:
                    assert deconstruct_result1028 is not None
                    unwrapped1029 = deconstruct_result1028
                    self.pretty_false(unwrapped1029)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1663 = _dollar_dollar.exists
                    else:
                        _t1663 = None
                    deconstruct_result1026 = _t1663
                    if deconstruct_result1026 is not None:
                        assert deconstruct_result1026 is not None
                        unwrapped1027 = deconstruct_result1026
                        self.pretty_exists(unwrapped1027)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1664 = _dollar_dollar.reduce
                        else:
                            _t1664 = None
                        deconstruct_result1024 = _t1664
                        if deconstruct_result1024 is not None:
                            assert deconstruct_result1024 is not None
                            unwrapped1025 = deconstruct_result1024
                            self.pretty_reduce(unwrapped1025)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1665 = _dollar_dollar.conjunction
                            else:
                                _t1665 = None
                            deconstruct_result1022 = _t1665
                            if deconstruct_result1022 is not None:
                                assert deconstruct_result1022 is not None
                                unwrapped1023 = deconstruct_result1022
                                self.pretty_conjunction(unwrapped1023)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1666 = _dollar_dollar.disjunction
                                else:
                                    _t1666 = None
                                deconstruct_result1020 = _t1666
                                if deconstruct_result1020 is not None:
                                    assert deconstruct_result1020 is not None
                                    unwrapped1021 = deconstruct_result1020
                                    self.pretty_disjunction(unwrapped1021)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1667 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1667 = None
                                    deconstruct_result1018 = _t1667
                                    if deconstruct_result1018 is not None:
                                        assert deconstruct_result1018 is not None
                                        unwrapped1019 = deconstruct_result1018
                                        self.pretty_not(unwrapped1019)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1668 = _dollar_dollar.ffi
                                        else:
                                            _t1668 = None
                                        deconstruct_result1016 = _t1668
                                        if deconstruct_result1016 is not None:
                                            assert deconstruct_result1016 is not None
                                            unwrapped1017 = deconstruct_result1016
                                            self.pretty_ffi(unwrapped1017)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1669 = _dollar_dollar.atom
                                            else:
                                                _t1669 = None
                                            deconstruct_result1014 = _t1669
                                            if deconstruct_result1014 is not None:
                                                assert deconstruct_result1014 is not None
                                                unwrapped1015 = deconstruct_result1014
                                                self.pretty_atom(unwrapped1015)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1670 = _dollar_dollar.pragma
                                                else:
                                                    _t1670 = None
                                                deconstruct_result1012 = _t1670
                                                if deconstruct_result1012 is not None:
                                                    assert deconstruct_result1012 is not None
                                                    unwrapped1013 = deconstruct_result1012
                                                    self.pretty_pragma(unwrapped1013)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1671 = _dollar_dollar.primitive
                                                    else:
                                                        _t1671 = None
                                                    deconstruct_result1010 = _t1671
                                                    if deconstruct_result1010 is not None:
                                                        assert deconstruct_result1010 is not None
                                                        unwrapped1011 = deconstruct_result1010
                                                        self.pretty_primitive(unwrapped1011)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1672 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1672 = None
                                                        deconstruct_result1008 = _t1672
                                                        if deconstruct_result1008 is not None:
                                                            assert deconstruct_result1008 is not None
                                                            unwrapped1009 = deconstruct_result1008
                                                            self.pretty_rel_atom(unwrapped1009)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1673 = _dollar_dollar.cast
                                                            else:
                                                                _t1673 = None
                                                            deconstruct_result1006 = _t1673
                                                            if deconstruct_result1006 is not None:
                                                                assert deconstruct_result1006 is not None
                                                                unwrapped1007 = deconstruct_result1006
                                                                self.pretty_cast(unwrapped1007)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields1033 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1034 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1039 = self._try_flat(msg, self.pretty_exists)
        if flat1039 is not None:
            assert flat1039 is not None
            self.write(flat1039)
            return None
        else:
            _dollar_dollar = msg
            _t1674 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1035 = (_t1674, _dollar_dollar.body.value,)
            assert fields1035 is not None
            unwrapped_fields1036 = fields1035
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1037 = unwrapped_fields1036[0]
            self.pretty_bindings(field1037)
            self.newline()
            field1038 = unwrapped_fields1036[1]
            self.pretty_formula(field1038)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1045 = self._try_flat(msg, self.pretty_reduce)
        if flat1045 is not None:
            assert flat1045 is not None
            self.write(flat1045)
            return None
        else:
            _dollar_dollar = msg
            fields1040 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1040 is not None
            unwrapped_fields1041 = fields1040
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1042 = unwrapped_fields1041[0]
            self.pretty_abstraction(field1042)
            self.newline()
            field1043 = unwrapped_fields1041[1]
            self.pretty_abstraction(field1043)
            self.newline()
            field1044 = unwrapped_fields1041[2]
            self.pretty_terms(field1044)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1049 = self._try_flat(msg, self.pretty_terms)
        if flat1049 is not None:
            assert flat1049 is not None
            self.write(flat1049)
            return None
        else:
            fields1046 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1046) == 0:
                self.newline()
                for i1048, elem1047 in enumerate(fields1046):
                    if (i1048 > 0):
                        self.newline()
                    self.pretty_term(elem1047)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1054 = self._try_flat(msg, self.pretty_term)
        if flat1054 is not None:
            assert flat1054 is not None
            self.write(flat1054)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1675 = _dollar_dollar.var
            else:
                _t1675 = None
            deconstruct_result1052 = _t1675
            if deconstruct_result1052 is not None:
                assert deconstruct_result1052 is not None
                unwrapped1053 = deconstruct_result1052
                self.pretty_var(unwrapped1053)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1676 = _dollar_dollar.constant
                else:
                    _t1676 = None
                deconstruct_result1050 = _t1676
                if deconstruct_result1050 is not None:
                    assert deconstruct_result1050 is not None
                    unwrapped1051 = deconstruct_result1050
                    self.pretty_value(unwrapped1051)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1057 = self._try_flat(msg, self.pretty_var)
        if flat1057 is not None:
            assert flat1057 is not None
            self.write(flat1057)
            return None
        else:
            _dollar_dollar = msg
            fields1055 = _dollar_dollar.name
            assert fields1055 is not None
            unwrapped_fields1056 = fields1055
            self.write(unwrapped_fields1056)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1083 = self._try_flat(msg, self.pretty_value)
        if flat1083 is not None:
            assert flat1083 is not None
            self.write(flat1083)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1677 = _dollar_dollar.date_value
            else:
                _t1677 = None
            deconstruct_result1081 = _t1677
            if deconstruct_result1081 is not None:
                assert deconstruct_result1081 is not None
                unwrapped1082 = deconstruct_result1081
                self.pretty_date(unwrapped1082)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1678 = _dollar_dollar.datetime_value
                else:
                    _t1678 = None
                deconstruct_result1079 = _t1678
                if deconstruct_result1079 is not None:
                    assert deconstruct_result1079 is not None
                    unwrapped1080 = deconstruct_result1079
                    self.pretty_datetime(unwrapped1080)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1679 = _dollar_dollar.string_value
                    else:
                        _t1679 = None
                    deconstruct_result1077 = _t1679
                    if deconstruct_result1077 is not None:
                        assert deconstruct_result1077 is not None
                        unwrapped1078 = deconstruct_result1077
                        self.write(self.format_string_value(unwrapped1078))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1680 = _dollar_dollar.int32_value
                        else:
                            _t1680 = None
                        deconstruct_result1075 = _t1680
                        if deconstruct_result1075 is not None:
                            assert deconstruct_result1075 is not None
                            unwrapped1076 = deconstruct_result1075
                            self.write((str(unwrapped1076) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1681 = _dollar_dollar.int_value
                            else:
                                _t1681 = None
                            deconstruct_result1073 = _t1681
                            if deconstruct_result1073 is not None:
                                assert deconstruct_result1073 is not None
                                unwrapped1074 = deconstruct_result1073
                                self.write(str(unwrapped1074))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1682 = _dollar_dollar.float32_value
                                else:
                                    _t1682 = None
                                deconstruct_result1071 = _t1682
                                if deconstruct_result1071 is not None:
                                    assert deconstruct_result1071 is not None
                                    unwrapped1072 = deconstruct_result1071
                                    self.write(self.format_float32_literal(unwrapped1072))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1683 = _dollar_dollar.float_value
                                    else:
                                        _t1683 = None
                                    deconstruct_result1069 = _t1683
                                    if deconstruct_result1069 is not None:
                                        assert deconstruct_result1069 is not None
                                        unwrapped1070 = deconstruct_result1069
                                        self.write(str(unwrapped1070))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1684 = _dollar_dollar.uint32_value
                                        else:
                                            _t1684 = None
                                        deconstruct_result1067 = _t1684
                                        if deconstruct_result1067 is not None:
                                            assert deconstruct_result1067 is not None
                                            unwrapped1068 = deconstruct_result1067
                                            self.write((str(unwrapped1068) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1685 = _dollar_dollar.uint128_value
                                            else:
                                                _t1685 = None
                                            deconstruct_result1065 = _t1685
                                            if deconstruct_result1065 is not None:
                                                assert deconstruct_result1065 is not None
                                                unwrapped1066 = deconstruct_result1065
                                                self.write(self.format_uint128(unwrapped1066))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1686 = _dollar_dollar.int128_value
                                                else:
                                                    _t1686 = None
                                                deconstruct_result1063 = _t1686
                                                if deconstruct_result1063 is not None:
                                                    assert deconstruct_result1063 is not None
                                                    unwrapped1064 = deconstruct_result1063
                                                    self.write(self.format_int128(unwrapped1064))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1687 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1687 = None
                                                    deconstruct_result1061 = _t1687
                                                    if deconstruct_result1061 is not None:
                                                        assert deconstruct_result1061 is not None
                                                        unwrapped1062 = deconstruct_result1061
                                                        self.write(self.format_decimal(unwrapped1062))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1688 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1688 = None
                                                        deconstruct_result1059 = _t1688
                                                        if deconstruct_result1059 is not None:
                                                            assert deconstruct_result1059 is not None
                                                            unwrapped1060 = deconstruct_result1059
                                                            self.pretty_boolean_value(unwrapped1060)
                                                        else:
                                                            fields1058 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1089 = self._try_flat(msg, self.pretty_date)
        if flat1089 is not None:
            assert flat1089 is not None
            self.write(flat1089)
            return None
        else:
            _dollar_dollar = msg
            fields1084 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1084 is not None
            unwrapped_fields1085 = fields1084
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1086 = unwrapped_fields1085[0]
            self.write(str(field1086))
            self.newline()
            field1087 = unwrapped_fields1085[1]
            self.write(str(field1087))
            self.newline()
            field1088 = unwrapped_fields1085[2]
            self.write(str(field1088))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1100 = self._try_flat(msg, self.pretty_datetime)
        if flat1100 is not None:
            assert flat1100 is not None
            self.write(flat1100)
            return None
        else:
            _dollar_dollar = msg
            fields1090 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1090 is not None
            unwrapped_fields1091 = fields1090
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1092 = unwrapped_fields1091[0]
            self.write(str(field1092))
            self.newline()
            field1093 = unwrapped_fields1091[1]
            self.write(str(field1093))
            self.newline()
            field1094 = unwrapped_fields1091[2]
            self.write(str(field1094))
            self.newline()
            field1095 = unwrapped_fields1091[3]
            self.write(str(field1095))
            self.newline()
            field1096 = unwrapped_fields1091[4]
            self.write(str(field1096))
            self.newline()
            field1097 = unwrapped_fields1091[5]
            self.write(str(field1097))
            field1098 = unwrapped_fields1091[6]
            if field1098 is not None:
                self.newline()
                assert field1098 is not None
                opt_val1099 = field1098
                self.write(str(opt_val1099))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1105 = self._try_flat(msg, self.pretty_conjunction)
        if flat1105 is not None:
            assert flat1105 is not None
            self.write(flat1105)
            return None
        else:
            _dollar_dollar = msg
            fields1101 = _dollar_dollar.args
            assert fields1101 is not None
            unwrapped_fields1102 = fields1101
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1102) == 0:
                self.newline()
                for i1104, elem1103 in enumerate(unwrapped_fields1102):
                    if (i1104 > 0):
                        self.newline()
                    self.pretty_formula(elem1103)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1110 = self._try_flat(msg, self.pretty_disjunction)
        if flat1110 is not None:
            assert flat1110 is not None
            self.write(flat1110)
            return None
        else:
            _dollar_dollar = msg
            fields1106 = _dollar_dollar.args
            assert fields1106 is not None
            unwrapped_fields1107 = fields1106
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1107) == 0:
                self.newline()
                for i1109, elem1108 in enumerate(unwrapped_fields1107):
                    if (i1109 > 0):
                        self.newline()
                    self.pretty_formula(elem1108)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1113 = self._try_flat(msg, self.pretty_not)
        if flat1113 is not None:
            assert flat1113 is not None
            self.write(flat1113)
            return None
        else:
            _dollar_dollar = msg
            fields1111 = _dollar_dollar.arg
            assert fields1111 is not None
            unwrapped_fields1112 = fields1111
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1112)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1119 = self._try_flat(msg, self.pretty_ffi)
        if flat1119 is not None:
            assert flat1119 is not None
            self.write(flat1119)
            return None
        else:
            _dollar_dollar = msg
            fields1114 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1114 is not None
            unwrapped_fields1115 = fields1114
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1116 = unwrapped_fields1115[0]
            self.pretty_name(field1116)
            self.newline()
            field1117 = unwrapped_fields1115[1]
            self.pretty_ffi_args(field1117)
            self.newline()
            field1118 = unwrapped_fields1115[2]
            self.pretty_terms(field1118)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1121 = self._try_flat(msg, self.pretty_name)
        if flat1121 is not None:
            assert flat1121 is not None
            self.write(flat1121)
            return None
        else:
            fields1120 = msg
            self.write(":")
            self.write(fields1120)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1125 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1125 is not None:
            assert flat1125 is not None
            self.write(flat1125)
            return None
        else:
            fields1122 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1122) == 0:
                self.newline()
                for i1124, elem1123 in enumerate(fields1122):
                    if (i1124 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1123)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1132 = self._try_flat(msg, self.pretty_atom)
        if flat1132 is not None:
            assert flat1132 is not None
            self.write(flat1132)
            return None
        else:
            _dollar_dollar = msg
            fields1126 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1126 is not None
            unwrapped_fields1127 = fields1126
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1128 = unwrapped_fields1127[0]
            self.pretty_relation_id(field1128)
            field1129 = unwrapped_fields1127[1]
            if not len(field1129) == 0:
                self.newline()
                for i1131, elem1130 in enumerate(field1129):
                    if (i1131 > 0):
                        self.newline()
                    self.pretty_term(elem1130)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1139 = self._try_flat(msg, self.pretty_pragma)
        if flat1139 is not None:
            assert flat1139 is not None
            self.write(flat1139)
            return None
        else:
            _dollar_dollar = msg
            fields1133 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1133 is not None
            unwrapped_fields1134 = fields1133
            self.write("(pragma")
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
                    self.pretty_term(elem1137)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1155 = self._try_flat(msg, self.pretty_primitive)
        if flat1155 is not None:
            assert flat1155 is not None
            self.write(flat1155)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1689 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1689 = None
            guard_result1154 = _t1689
            if guard_result1154 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1690 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1690 = None
                guard_result1153 = _t1690
                if guard_result1153 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1691 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1691 = None
                    guard_result1152 = _t1691
                    if guard_result1152 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1692 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1692 = None
                        guard_result1151 = _t1692
                        if guard_result1151 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1693 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1693 = None
                            guard_result1150 = _t1693
                            if guard_result1150 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1694 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1694 = None
                                guard_result1149 = _t1694
                                if guard_result1149 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1695 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1695 = None
                                    guard_result1148 = _t1695
                                    if guard_result1148 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1696 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1696 = None
                                        guard_result1147 = _t1696
                                        if guard_result1147 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1697 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1697 = None
                                            guard_result1146 = _t1697
                                            if guard_result1146 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1140 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1140 is not None
                                                unwrapped_fields1141 = fields1140
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1142 = unwrapped_fields1141[0]
                                                self.pretty_name(field1142)
                                                field1143 = unwrapped_fields1141[1]
                                                if not len(field1143) == 0:
                                                    self.newline()
                                                    for i1145, elem1144 in enumerate(field1143):
                                                        if (i1145 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1144)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1160 = self._try_flat(msg, self.pretty_eq)
        if flat1160 is not None:
            assert flat1160 is not None
            self.write(flat1160)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1698 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1698 = None
            fields1156 = _t1698
            assert fields1156 is not None
            unwrapped_fields1157 = fields1156
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1158 = unwrapped_fields1157[0]
            self.pretty_term(field1158)
            self.newline()
            field1159 = unwrapped_fields1157[1]
            self.pretty_term(field1159)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1165 = self._try_flat(msg, self.pretty_lt)
        if flat1165 is not None:
            assert flat1165 is not None
            self.write(flat1165)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1699 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1699 = None
            fields1161 = _t1699
            assert fields1161 is not None
            unwrapped_fields1162 = fields1161
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1163 = unwrapped_fields1162[0]
            self.pretty_term(field1163)
            self.newline()
            field1164 = unwrapped_fields1162[1]
            self.pretty_term(field1164)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1170 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1170 is not None:
            assert flat1170 is not None
            self.write(flat1170)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1700 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1700 = None
            fields1166 = _t1700
            assert fields1166 is not None
            unwrapped_fields1167 = fields1166
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1168 = unwrapped_fields1167[0]
            self.pretty_term(field1168)
            self.newline()
            field1169 = unwrapped_fields1167[1]
            self.pretty_term(field1169)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1175 = self._try_flat(msg, self.pretty_gt)
        if flat1175 is not None:
            assert flat1175 is not None
            self.write(flat1175)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1701 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1701 = None
            fields1171 = _t1701
            assert fields1171 is not None
            unwrapped_fields1172 = fields1171
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1173 = unwrapped_fields1172[0]
            self.pretty_term(field1173)
            self.newline()
            field1174 = unwrapped_fields1172[1]
            self.pretty_term(field1174)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1180 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1180 is not None:
            assert flat1180 is not None
            self.write(flat1180)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1702 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1702 = None
            fields1176 = _t1702
            assert fields1176 is not None
            unwrapped_fields1177 = fields1176
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1178 = unwrapped_fields1177[0]
            self.pretty_term(field1178)
            self.newline()
            field1179 = unwrapped_fields1177[1]
            self.pretty_term(field1179)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1186 = self._try_flat(msg, self.pretty_add)
        if flat1186 is not None:
            assert flat1186 is not None
            self.write(flat1186)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1703 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1703 = None
            fields1181 = _t1703
            assert fields1181 is not None
            unwrapped_fields1182 = fields1181
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1183 = unwrapped_fields1182[0]
            self.pretty_term(field1183)
            self.newline()
            field1184 = unwrapped_fields1182[1]
            self.pretty_term(field1184)
            self.newline()
            field1185 = unwrapped_fields1182[2]
            self.pretty_term(field1185)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1192 = self._try_flat(msg, self.pretty_minus)
        if flat1192 is not None:
            assert flat1192 is not None
            self.write(flat1192)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1704 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1704 = None
            fields1187 = _t1704
            assert fields1187 is not None
            unwrapped_fields1188 = fields1187
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1189 = unwrapped_fields1188[0]
            self.pretty_term(field1189)
            self.newline()
            field1190 = unwrapped_fields1188[1]
            self.pretty_term(field1190)
            self.newline()
            field1191 = unwrapped_fields1188[2]
            self.pretty_term(field1191)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1198 = self._try_flat(msg, self.pretty_multiply)
        if flat1198 is not None:
            assert flat1198 is not None
            self.write(flat1198)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1705 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1705 = None
            fields1193 = _t1705
            assert fields1193 is not None
            unwrapped_fields1194 = fields1193
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1195 = unwrapped_fields1194[0]
            self.pretty_term(field1195)
            self.newline()
            field1196 = unwrapped_fields1194[1]
            self.pretty_term(field1196)
            self.newline()
            field1197 = unwrapped_fields1194[2]
            self.pretty_term(field1197)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1204 = self._try_flat(msg, self.pretty_divide)
        if flat1204 is not None:
            assert flat1204 is not None
            self.write(flat1204)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1706 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1706 = None
            fields1199 = _t1706
            assert fields1199 is not None
            unwrapped_fields1200 = fields1199
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1201 = unwrapped_fields1200[0]
            self.pretty_term(field1201)
            self.newline()
            field1202 = unwrapped_fields1200[1]
            self.pretty_term(field1202)
            self.newline()
            field1203 = unwrapped_fields1200[2]
            self.pretty_term(field1203)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1209 = self._try_flat(msg, self.pretty_rel_term)
        if flat1209 is not None:
            assert flat1209 is not None
            self.write(flat1209)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1707 = _dollar_dollar.specialized_value
            else:
                _t1707 = None
            deconstruct_result1207 = _t1707
            if deconstruct_result1207 is not None:
                assert deconstruct_result1207 is not None
                unwrapped1208 = deconstruct_result1207
                self.pretty_specialized_value(unwrapped1208)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1708 = _dollar_dollar.term
                else:
                    _t1708 = None
                deconstruct_result1205 = _t1708
                if deconstruct_result1205 is not None:
                    assert deconstruct_result1205 is not None
                    unwrapped1206 = deconstruct_result1205
                    self.pretty_term(unwrapped1206)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1211 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1211 is not None:
            assert flat1211 is not None
            self.write(flat1211)
            return None
        else:
            fields1210 = msg
            self.write("#")
            self.pretty_raw_value(fields1210)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1218 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1218 is not None:
            assert flat1218 is not None
            self.write(flat1218)
            return None
        else:
            _dollar_dollar = msg
            fields1212 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1212 is not None
            unwrapped_fields1213 = fields1212
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1214 = unwrapped_fields1213[0]
            self.pretty_name(field1214)
            field1215 = unwrapped_fields1213[1]
            if not len(field1215) == 0:
                self.newline()
                for i1217, elem1216 in enumerate(field1215):
                    if (i1217 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1216)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1223 = self._try_flat(msg, self.pretty_cast)
        if flat1223 is not None:
            assert flat1223 is not None
            self.write(flat1223)
            return None
        else:
            _dollar_dollar = msg
            fields1219 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1219 is not None
            unwrapped_fields1220 = fields1219
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1221 = unwrapped_fields1220[0]
            self.pretty_term(field1221)
            self.newline()
            field1222 = unwrapped_fields1220[1]
            self.pretty_term(field1222)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1227 = self._try_flat(msg, self.pretty_attrs)
        if flat1227 is not None:
            assert flat1227 is not None
            self.write(flat1227)
            return None
        else:
            fields1224 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1224) == 0:
                self.newline()
                for i1226, elem1225 in enumerate(fields1224):
                    if (i1226 > 0):
                        self.newline()
                    self.pretty_attribute(elem1225)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1234 = self._try_flat(msg, self.pretty_attribute)
        if flat1234 is not None:
            assert flat1234 is not None
            self.write(flat1234)
            return None
        else:
            _dollar_dollar = msg
            fields1228 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1228 is not None
            unwrapped_fields1229 = fields1228
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1230 = unwrapped_fields1229[0]
            self.pretty_name(field1230)
            field1231 = unwrapped_fields1229[1]
            if not len(field1231) == 0:
                self.newline()
                for i1233, elem1232 in enumerate(field1231):
                    if (i1233 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1232)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1243 = self._try_flat(msg, self.pretty_algorithm)
        if flat1243 is not None:
            assert flat1243 is not None
            self.write(flat1243)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1709 = _dollar_dollar.attrs
            else:
                _t1709 = None
            fields1235 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body, _t1709,)
            assert fields1235 is not None
            unwrapped_fields1236 = fields1235
            self.write("(algorithm")
            self.indent_sexp()
            field1237 = unwrapped_fields1236[0]
            if not len(field1237) == 0:
                self.newline()
                for i1239, elem1238 in enumerate(field1237):
                    if (i1239 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1238)
            self.newline()
            field1240 = unwrapped_fields1236[1]
            self.pretty_script(field1240)
            field1241 = unwrapped_fields1236[2]
            if field1241 is not None:
                self.newline()
                assert field1241 is not None
                opt_val1242 = field1241
                self.pretty_attrs(opt_val1242)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1248 = self._try_flat(msg, self.pretty_script)
        if flat1248 is not None:
            assert flat1248 is not None
            self.write(flat1248)
            return None
        else:
            _dollar_dollar = msg
            fields1244 = _dollar_dollar.constructs
            assert fields1244 is not None
            unwrapped_fields1245 = fields1244
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1245) == 0:
                self.newline()
                for i1247, elem1246 in enumerate(unwrapped_fields1245):
                    if (i1247 > 0):
                        self.newline()
                    self.pretty_construct(elem1246)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1253 = self._try_flat(msg, self.pretty_construct)
        if flat1253 is not None:
            assert flat1253 is not None
            self.write(flat1253)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1710 = _dollar_dollar.loop
            else:
                _t1710 = None
            deconstruct_result1251 = _t1710
            if deconstruct_result1251 is not None:
                assert deconstruct_result1251 is not None
                unwrapped1252 = deconstruct_result1251
                self.pretty_loop(unwrapped1252)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1711 = _dollar_dollar.instruction
                else:
                    _t1711 = None
                deconstruct_result1249 = _t1711
                if deconstruct_result1249 is not None:
                    assert deconstruct_result1249 is not None
                    unwrapped1250 = deconstruct_result1249
                    self.pretty_instruction(unwrapped1250)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1260 = self._try_flat(msg, self.pretty_loop)
        if flat1260 is not None:
            assert flat1260 is not None
            self.write(flat1260)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1712 = _dollar_dollar.attrs
            else:
                _t1712 = None
            fields1254 = (_dollar_dollar.init, _dollar_dollar.body, _t1712,)
            assert fields1254 is not None
            unwrapped_fields1255 = fields1254
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1256 = unwrapped_fields1255[0]
            self.pretty_init(field1256)
            self.newline()
            field1257 = unwrapped_fields1255[1]
            self.pretty_script(field1257)
            field1258 = unwrapped_fields1255[2]
            if field1258 is not None:
                self.newline()
                assert field1258 is not None
                opt_val1259 = field1258
                self.pretty_attrs(opt_val1259)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1264 = self._try_flat(msg, self.pretty_init)
        if flat1264 is not None:
            assert flat1264 is not None
            self.write(flat1264)
            return None
        else:
            fields1261 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1261) == 0:
                self.newline()
                for i1263, elem1262 in enumerate(fields1261):
                    if (i1263 > 0):
                        self.newline()
                    self.pretty_instruction(elem1262)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1275 = self._try_flat(msg, self.pretty_instruction)
        if flat1275 is not None:
            assert flat1275 is not None
            self.write(flat1275)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1713 = _dollar_dollar.assign
            else:
                _t1713 = None
            deconstruct_result1273 = _t1713
            if deconstruct_result1273 is not None:
                assert deconstruct_result1273 is not None
                unwrapped1274 = deconstruct_result1273
                self.pretty_assign(unwrapped1274)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1714 = _dollar_dollar.upsert
                else:
                    _t1714 = None
                deconstruct_result1271 = _t1714
                if deconstruct_result1271 is not None:
                    assert deconstruct_result1271 is not None
                    unwrapped1272 = deconstruct_result1271
                    self.pretty_upsert(unwrapped1272)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1715 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1715 = None
                    deconstruct_result1269 = _t1715
                    if deconstruct_result1269 is not None:
                        assert deconstruct_result1269 is not None
                        unwrapped1270 = deconstruct_result1269
                        self.pretty_break(unwrapped1270)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1716 = _dollar_dollar.monoid_def
                        else:
                            _t1716 = None
                        deconstruct_result1267 = _t1716
                        if deconstruct_result1267 is not None:
                            assert deconstruct_result1267 is not None
                            unwrapped1268 = deconstruct_result1267
                            self.pretty_monoid_def(unwrapped1268)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1717 = _dollar_dollar.monus_def
                            else:
                                _t1717 = None
                            deconstruct_result1265 = _t1717
                            if deconstruct_result1265 is not None:
                                assert deconstruct_result1265 is not None
                                unwrapped1266 = deconstruct_result1265
                                self.pretty_monus_def(unwrapped1266)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1282 = self._try_flat(msg, self.pretty_assign)
        if flat1282 is not None:
            assert flat1282 is not None
            self.write(flat1282)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1718 = _dollar_dollar.attrs
            else:
                _t1718 = None
            fields1276 = (_dollar_dollar.name, _dollar_dollar.body, _t1718,)
            assert fields1276 is not None
            unwrapped_fields1277 = fields1276
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1278 = unwrapped_fields1277[0]
            self.pretty_relation_id(field1278)
            self.newline()
            field1279 = unwrapped_fields1277[1]
            self.pretty_abstraction(field1279)
            field1280 = unwrapped_fields1277[2]
            if field1280 is not None:
                self.newline()
                assert field1280 is not None
                opt_val1281 = field1280
                self.pretty_attrs(opt_val1281)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1289 = self._try_flat(msg, self.pretty_upsert)
        if flat1289 is not None:
            assert flat1289 is not None
            self.write(flat1289)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1719 = _dollar_dollar.attrs
            else:
                _t1719 = None
            fields1283 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1719,)
            assert fields1283 is not None
            unwrapped_fields1284 = fields1283
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1285 = unwrapped_fields1284[0]
            self.pretty_relation_id(field1285)
            self.newline()
            field1286 = unwrapped_fields1284[1]
            self.pretty_abstraction_with_arity(field1286)
            field1287 = unwrapped_fields1284[2]
            if field1287 is not None:
                self.newline()
                assert field1287 is not None
                opt_val1288 = field1287
                self.pretty_attrs(opt_val1288)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1294 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1294 is not None:
            assert flat1294 is not None
            self.write(flat1294)
            return None
        else:
            _dollar_dollar = msg
            _t1720 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1290 = (_t1720, _dollar_dollar[0].value,)
            assert fields1290 is not None
            unwrapped_fields1291 = fields1290
            self.write("(")
            self.indent()
            field1292 = unwrapped_fields1291[0]
            self.pretty_bindings(field1292)
            self.newline()
            field1293 = unwrapped_fields1291[1]
            self.pretty_formula(field1293)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1301 = self._try_flat(msg, self.pretty_break)
        if flat1301 is not None:
            assert flat1301 is not None
            self.write(flat1301)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1721 = _dollar_dollar.attrs
            else:
                _t1721 = None
            fields1295 = (_dollar_dollar.name, _dollar_dollar.body, _t1721,)
            assert fields1295 is not None
            unwrapped_fields1296 = fields1295
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1297 = unwrapped_fields1296[0]
            self.pretty_relation_id(field1297)
            self.newline()
            field1298 = unwrapped_fields1296[1]
            self.pretty_abstraction(field1298)
            field1299 = unwrapped_fields1296[2]
            if field1299 is not None:
                self.newline()
                assert field1299 is not None
                opt_val1300 = field1299
                self.pretty_attrs(opt_val1300)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1309 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1309 is not None:
            assert flat1309 is not None
            self.write(flat1309)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1722 = _dollar_dollar.attrs
            else:
                _t1722 = None
            fields1302 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1722,)
            assert fields1302 is not None
            unwrapped_fields1303 = fields1302
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1304 = unwrapped_fields1303[0]
            self.pretty_monoid(field1304)
            self.newline()
            field1305 = unwrapped_fields1303[1]
            self.pretty_relation_id(field1305)
            self.newline()
            field1306 = unwrapped_fields1303[2]
            self.pretty_abstraction_with_arity(field1306)
            field1307 = unwrapped_fields1303[3]
            if field1307 is not None:
                self.newline()
                assert field1307 is not None
                opt_val1308 = field1307
                self.pretty_attrs(opt_val1308)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1318 = self._try_flat(msg, self.pretty_monoid)
        if flat1318 is not None:
            assert flat1318 is not None
            self.write(flat1318)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1723 = _dollar_dollar.or_monoid
            else:
                _t1723 = None
            deconstruct_result1316 = _t1723
            if deconstruct_result1316 is not None:
                assert deconstruct_result1316 is not None
                unwrapped1317 = deconstruct_result1316
                self.pretty_or_monoid(unwrapped1317)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1724 = _dollar_dollar.min_monoid
                else:
                    _t1724 = None
                deconstruct_result1314 = _t1724
                if deconstruct_result1314 is not None:
                    assert deconstruct_result1314 is not None
                    unwrapped1315 = deconstruct_result1314
                    self.pretty_min_monoid(unwrapped1315)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1725 = _dollar_dollar.max_monoid
                    else:
                        _t1725 = None
                    deconstruct_result1312 = _t1725
                    if deconstruct_result1312 is not None:
                        assert deconstruct_result1312 is not None
                        unwrapped1313 = deconstruct_result1312
                        self.pretty_max_monoid(unwrapped1313)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1726 = _dollar_dollar.sum_monoid
                        else:
                            _t1726 = None
                        deconstruct_result1310 = _t1726
                        if deconstruct_result1310 is not None:
                            assert deconstruct_result1310 is not None
                            unwrapped1311 = deconstruct_result1310
                            self.pretty_sum_monoid(unwrapped1311)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1319 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1322 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1322 is not None:
            assert flat1322 is not None
            self.write(flat1322)
            return None
        else:
            _dollar_dollar = msg
            fields1320 = _dollar_dollar.type
            assert fields1320 is not None
            unwrapped_fields1321 = fields1320
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1321)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1325 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1325 is not None:
            assert flat1325 is not None
            self.write(flat1325)
            return None
        else:
            _dollar_dollar = msg
            fields1323 = _dollar_dollar.type
            assert fields1323 is not None
            unwrapped_fields1324 = fields1323
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1324)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1328 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1328 is not None:
            assert flat1328 is not None
            self.write(flat1328)
            return None
        else:
            _dollar_dollar = msg
            fields1326 = _dollar_dollar.type
            assert fields1326 is not None
            unwrapped_fields1327 = fields1326
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1327)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1336 = self._try_flat(msg, self.pretty_monus_def)
        if flat1336 is not None:
            assert flat1336 is not None
            self.write(flat1336)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1727 = _dollar_dollar.attrs
            else:
                _t1727 = None
            fields1329 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1727,)
            assert fields1329 is not None
            unwrapped_fields1330 = fields1329
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1331 = unwrapped_fields1330[0]
            self.pretty_monoid(field1331)
            self.newline()
            field1332 = unwrapped_fields1330[1]
            self.pretty_relation_id(field1332)
            self.newline()
            field1333 = unwrapped_fields1330[2]
            self.pretty_abstraction_with_arity(field1333)
            field1334 = unwrapped_fields1330[3]
            if field1334 is not None:
                self.newline()
                assert field1334 is not None
                opt_val1335 = field1334
                self.pretty_attrs(opt_val1335)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1343 = self._try_flat(msg, self.pretty_constraint)
        if flat1343 is not None:
            assert flat1343 is not None
            self.write(flat1343)
            return None
        else:
            _dollar_dollar = msg
            fields1337 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1337 is not None
            unwrapped_fields1338 = fields1337
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1339 = unwrapped_fields1338[0]
            self.pretty_relation_id(field1339)
            self.newline()
            field1340 = unwrapped_fields1338[1]
            self.pretty_abstraction(field1340)
            self.newline()
            field1341 = unwrapped_fields1338[2]
            self.pretty_functional_dependency_keys(field1341)
            self.newline()
            field1342 = unwrapped_fields1338[3]
            self.pretty_functional_dependency_values(field1342)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1347 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1347 is not None:
            assert flat1347 is not None
            self.write(flat1347)
            return None
        else:
            fields1344 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1344) == 0:
                self.newline()
                for i1346, elem1345 in enumerate(fields1344):
                    if (i1346 > 0):
                        self.newline()
                    self.pretty_var(elem1345)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1351 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1351 is not None:
            assert flat1351 is not None
            self.write(flat1351)
            return None
        else:
            fields1348 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1348) == 0:
                self.newline()
                for i1350, elem1349 in enumerate(fields1348):
                    if (i1350 > 0):
                        self.newline()
                    self.pretty_var(elem1349)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1360 = self._try_flat(msg, self.pretty_data)
        if flat1360 is not None:
            assert flat1360 is not None
            self.write(flat1360)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1728 = _dollar_dollar.edb
            else:
                _t1728 = None
            deconstruct_result1358 = _t1728
            if deconstruct_result1358 is not None:
                assert deconstruct_result1358 is not None
                unwrapped1359 = deconstruct_result1358
                self.pretty_edb(unwrapped1359)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1729 = _dollar_dollar.betree_relation
                else:
                    _t1729 = None
                deconstruct_result1356 = _t1729
                if deconstruct_result1356 is not None:
                    assert deconstruct_result1356 is not None
                    unwrapped1357 = deconstruct_result1356
                    self.pretty_betree_relation(unwrapped1357)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1730 = _dollar_dollar.csv_data
                    else:
                        _t1730 = None
                    deconstruct_result1354 = _t1730
                    if deconstruct_result1354 is not None:
                        assert deconstruct_result1354 is not None
                        unwrapped1355 = deconstruct_result1354
                        self.pretty_csv_data(unwrapped1355)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1731 = _dollar_dollar.iceberg_data
                        else:
                            _t1731 = None
                        deconstruct_result1352 = _t1731
                        if deconstruct_result1352 is not None:
                            assert deconstruct_result1352 is not None
                            unwrapped1353 = deconstruct_result1352
                            self.pretty_iceberg_data(unwrapped1353)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1366 = self._try_flat(msg, self.pretty_edb)
        if flat1366 is not None:
            assert flat1366 is not None
            self.write(flat1366)
            return None
        else:
            _dollar_dollar = msg
            fields1361 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1361 is not None
            unwrapped_fields1362 = fields1361
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1363 = unwrapped_fields1362[0]
            self.pretty_relation_id(field1363)
            self.newline()
            field1364 = unwrapped_fields1362[1]
            self.pretty_edb_path(field1364)
            self.newline()
            field1365 = unwrapped_fields1362[2]
            self.pretty_edb_types(field1365)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1370 = self._try_flat(msg, self.pretty_edb_path)
        if flat1370 is not None:
            assert flat1370 is not None
            self.write(flat1370)
            return None
        else:
            fields1367 = msg
            self.write("[")
            self.indent()
            for i1369, elem1368 in enumerate(fields1367):
                if (i1369 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1368))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1374 = self._try_flat(msg, self.pretty_edb_types)
        if flat1374 is not None:
            assert flat1374 is not None
            self.write(flat1374)
            return None
        else:
            fields1371 = msg
            self.write("[")
            self.indent()
            for i1373, elem1372 in enumerate(fields1371):
                if (i1373 > 0):
                    self.newline()
                self.pretty_type(elem1372)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1379 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1379 is not None:
            assert flat1379 is not None
            self.write(flat1379)
            return None
        else:
            _dollar_dollar = msg
            fields1375 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1375 is not None
            unwrapped_fields1376 = fields1375
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1377 = unwrapped_fields1376[0]
            self.pretty_relation_id(field1377)
            self.newline()
            field1378 = unwrapped_fields1376[1]
            self.pretty_betree_info(field1378)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1385 = self._try_flat(msg, self.pretty_betree_info)
        if flat1385 is not None:
            assert flat1385 is not None
            self.write(flat1385)
            return None
        else:
            _dollar_dollar = msg
            _t1732 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1380 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1732,)
            assert fields1380 is not None
            unwrapped_fields1381 = fields1380
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1382 = unwrapped_fields1381[0]
            self.pretty_betree_info_key_types(field1382)
            self.newline()
            field1383 = unwrapped_fields1381[1]
            self.pretty_betree_info_value_types(field1383)
            self.newline()
            field1384 = unwrapped_fields1381[2]
            self.pretty_config_dict(field1384)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1389 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1389 is not None:
            assert flat1389 is not None
            self.write(flat1389)
            return None
        else:
            fields1386 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1386) == 0:
                self.newline()
                for i1388, elem1387 in enumerate(fields1386):
                    if (i1388 > 0):
                        self.newline()
                    self.pretty_type(elem1387)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1393 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1393 is not None:
            assert flat1393 is not None
            self.write(flat1393)
            return None
        else:
            fields1390 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1390) == 0:
                self.newline()
                for i1392, elem1391 in enumerate(fields1390):
                    if (i1392 > 0):
                        self.newline()
                    self.pretty_type(elem1391)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1403 = self._try_flat(msg, self.pretty_csv_data)
        if flat1403 is not None:
            assert flat1403 is not None
            self.write(flat1403)
            return None
        else:
            _dollar_dollar = msg
            _t1733 = self.deconstruct_csv_data_columns_optional(_dollar_dollar)
            _t1734 = self.deconstruct_csv_data_target_optional(_dollar_dollar)
            fields1394 = (_dollar_dollar.locator, _dollar_dollar.config, _t1733, _t1734, _dollar_dollar.asof,)
            assert fields1394 is not None
            unwrapped_fields1395 = fields1394
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1396 = unwrapped_fields1395[0]
            self.pretty_csvlocator(field1396)
            self.newline()
            field1397 = unwrapped_fields1395[1]
            self.pretty_csv_config(field1397)
            field1398 = unwrapped_fields1395[2]
            if field1398 is not None:
                self.newline()
                assert field1398 is not None
                opt_val1399 = field1398
                self.pretty_gnf_columns(opt_val1399)
            field1400 = unwrapped_fields1395[3]
            if field1400 is not None:
                self.newline()
                assert field1400 is not None
                opt_val1401 = field1400
                self.pretty_csv_table(opt_val1401)
            self.newline()
            field1402 = unwrapped_fields1395[4]
            self.pretty_csv_asof(field1402)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1410 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1410 is not None:
            assert flat1410 is not None
            self.write(flat1410)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1735 = _dollar_dollar.paths
            else:
                _t1735 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1736 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1736 = None
            fields1404 = (_t1735, _t1736,)
            assert fields1404 is not None
            unwrapped_fields1405 = fields1404
            self.write("(csv_locator")
            self.indent_sexp()
            field1406 = unwrapped_fields1405[0]
            if field1406 is not None:
                self.newline()
                assert field1406 is not None
                opt_val1407 = field1406
                self.pretty_csv_locator_paths(opt_val1407)
            field1408 = unwrapped_fields1405[1]
            if field1408 is not None:
                self.newline()
                assert field1408 is not None
                opt_val1409 = field1408
                self.pretty_csv_locator_inline_data(opt_val1409)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1414 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1414 is not None:
            assert flat1414 is not None
            self.write(flat1414)
            return None
        else:
            fields1411 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1411) == 0:
                self.newline()
                for i1413, elem1412 in enumerate(fields1411):
                    if (i1413 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1412))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1416 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1416 is not None:
            assert flat1416 is not None
            self.write(flat1416)
            return None
        else:
            fields1415 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1415))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1419 = self._try_flat(msg, self.pretty_csv_config)
        if flat1419 is not None:
            assert flat1419 is not None
            self.write(flat1419)
            return None
        else:
            _dollar_dollar = msg
            _t1737 = self.deconstruct_csv_config(_dollar_dollar)
            fields1417 = _t1737
            assert fields1417 is not None
            unwrapped_fields1418 = fields1417
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1418)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1423 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1423 is not None:
            assert flat1423 is not None
            self.write(flat1423)
            return None
        else:
            fields1420 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1420) == 0:
                self.newline()
                for i1422, elem1421 in enumerate(fields1420):
                    if (i1422 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1421)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1432 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1432 is not None:
            assert flat1432 is not None
            self.write(flat1432)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1738 = _dollar_dollar.target_id
            else:
                _t1738 = None
            fields1424 = (_dollar_dollar.column_path, _t1738, _dollar_dollar.types,)
            assert fields1424 is not None
            unwrapped_fields1425 = fields1424
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1426 = unwrapped_fields1425[0]
            self.pretty_gnf_column_path(field1426)
            field1427 = unwrapped_fields1425[1]
            if field1427 is not None:
                self.newline()
                assert field1427 is not None
                opt_val1428 = field1427
                self.pretty_relation_id(opt_val1428)
            self.newline()
            self.write("[")
            field1429 = unwrapped_fields1425[2]
            for i1431, elem1430 in enumerate(field1429):
                if (i1431 > 0):
                    self.newline()
                self.pretty_type(elem1430)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1439 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1439 is not None:
            assert flat1439 is not None
            self.write(flat1439)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1739 = _dollar_dollar[0]
            else:
                _t1739 = None
            deconstruct_result1437 = _t1739
            if deconstruct_result1437 is not None:
                assert deconstruct_result1437 is not None
                unwrapped1438 = deconstruct_result1437
                self.write(self.format_string_value(unwrapped1438))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1740 = _dollar_dollar
                else:
                    _t1740 = None
                deconstruct_result1433 = _t1740
                if deconstruct_result1433 is not None:
                    assert deconstruct_result1433 is not None
                    unwrapped1434 = deconstruct_result1433
                    self.write("[")
                    self.indent()
                    for i1436, elem1435 in enumerate(unwrapped1434):
                        if (i1436 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1435))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_table(self, msg: logic_pb2.CSVTarget):
        flat1449 = self._try_flat(msg, self.pretty_csv_table)
        if flat1449 is not None:
            assert flat1449 is not None
            self.write(flat1449)
            return None
        else:
            _dollar_dollar = msg
            fields1440 = (_dollar_dollar.target_id, _dollar_dollar.column_names, _dollar_dollar.types,)
            assert fields1440 is not None
            unwrapped_fields1441 = fields1440
            self.write("(table")
            self.indent_sexp()
            self.newline()
            field1442 = unwrapped_fields1441[0]
            self.pretty_relation_id(field1442)
            self.newline()
            self.write("[")
            field1443 = unwrapped_fields1441[1]
            for i1445, elem1444 in enumerate(field1443):
                if (i1445 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1444))
            self.write("]")
            self.newline()
            self.write("[")
            field1446 = unwrapped_fields1441[2]
            for i1448, elem1447 in enumerate(field1446):
                if (i1448 > 0):
                    self.newline()
                self.pretty_type(elem1447)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_csv_asof(self, msg: str):
        flat1451 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1451 is not None:
            assert flat1451 is not None
            self.write(flat1451)
            return None
        else:
            fields1450 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1450))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1462 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1462 is not None:
            assert flat1462 is not None
            self.write(flat1462)
            return None
        else:
            _dollar_dollar = msg
            _t1741 = self.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
            _t1742 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1452 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1741, _t1742, _dollar_dollar.returns_delta,)
            assert fields1452 is not None
            unwrapped_fields1453 = fields1452
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1454 = unwrapped_fields1453[0]
            self.pretty_iceberg_locator(field1454)
            self.newline()
            field1455 = unwrapped_fields1453[1]
            self.pretty_iceberg_catalog_config(field1455)
            self.newline()
            field1456 = unwrapped_fields1453[2]
            self.pretty_gnf_columns(field1456)
            field1457 = unwrapped_fields1453[3]
            if field1457 is not None:
                self.newline()
                assert field1457 is not None
                opt_val1458 = field1457
                self.pretty_iceberg_from_snapshot(opt_val1458)
            field1459 = unwrapped_fields1453[4]
            if field1459 is not None:
                self.newline()
                assert field1459 is not None
                opt_val1460 = field1459
                self.pretty_iceberg_to_snapshot(opt_val1460)
            self.newline()
            field1461 = unwrapped_fields1453[5]
            self.pretty_boolean_value(field1461)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1468 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1468 is not None:
            assert flat1468 is not None
            self.write(flat1468)
            return None
        else:
            _dollar_dollar = msg
            fields1463 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1463 is not None
            unwrapped_fields1464 = fields1463
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            field1465 = unwrapped_fields1464[0]
            self.pretty_iceberg_locator_table_name(field1465)
            self.newline()
            field1466 = unwrapped_fields1464[1]
            self.pretty_iceberg_locator_namespace(field1466)
            self.newline()
            field1467 = unwrapped_fields1464[2]
            self.pretty_iceberg_locator_warehouse(field1467)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_table_name(self, msg: str):
        flat1470 = self._try_flat(msg, self.pretty_iceberg_locator_table_name)
        if flat1470 is not None:
            assert flat1470 is not None
            self.write(flat1470)
            return None
        else:
            fields1469 = msg
            self.write("(table_name")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1469))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_namespace(self, msg: Sequence[str]):
        flat1474 = self._try_flat(msg, self.pretty_iceberg_locator_namespace)
        if flat1474 is not None:
            assert flat1474 is not None
            self.write(flat1474)
            return None
        else:
            fields1471 = msg
            self.write("(namespace")
            self.indent_sexp()
            if not len(fields1471) == 0:
                self.newline()
                for i1473, elem1472 in enumerate(fields1471):
                    if (i1473 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1472))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_warehouse(self, msg: str):
        flat1476 = self._try_flat(msg, self.pretty_iceberg_locator_warehouse)
        if flat1476 is not None:
            assert flat1476 is not None
            self.write(flat1476)
            return None
        else:
            fields1475 = msg
            self.write("(warehouse")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1475))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1484 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1484 is not None:
            assert flat1484 is not None
            self.write(flat1484)
            return None
        else:
            _dollar_dollar = msg
            _t1743 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1477 = (_dollar_dollar.catalog_uri, _t1743, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1477 is not None
            unwrapped_fields1478 = fields1477
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            field1479 = unwrapped_fields1478[0]
            self.pretty_iceberg_catalog_uri(field1479)
            field1480 = unwrapped_fields1478[1]
            if field1480 is not None:
                self.newline()
                assert field1480 is not None
                opt_val1481 = field1480
                self.pretty_iceberg_catalog_config_scope(opt_val1481)
            self.newline()
            field1482 = unwrapped_fields1478[2]
            self.pretty_iceberg_properties(field1482)
            self.newline()
            field1483 = unwrapped_fields1478[3]
            self.pretty_iceberg_auth_properties(field1483)
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_uri(self, msg: str):
        flat1486 = self._try_flat(msg, self.pretty_iceberg_catalog_uri)
        if flat1486 is not None:
            assert flat1486 is not None
            self.write(flat1486)
            return None
        else:
            fields1485 = msg
            self.write("(catalog_uri")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1485))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1488 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1488 is not None:
            assert flat1488 is not None
            self.write(flat1488)
            return None
        else:
            fields1487 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1487))
            self.dedent()
            self.write(")")

    def pretty_iceberg_properties(self, msg: Sequence[tuple[str, str]]):
        flat1492 = self._try_flat(msg, self.pretty_iceberg_properties)
        if flat1492 is not None:
            assert flat1492 is not None
            self.write(flat1492)
            return None
        else:
            fields1489 = msg
            self.write("(properties")
            self.indent_sexp()
            if not len(fields1489) == 0:
                self.newline()
                for i1491, elem1490 in enumerate(fields1489):
                    if (i1491 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1490)
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1497 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1497 is not None:
            assert flat1497 is not None
            self.write(flat1497)
            return None
        else:
            _dollar_dollar = msg
            fields1493 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1493 is not None
            unwrapped_fields1494 = fields1493
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1495 = unwrapped_fields1494[0]
            self.write(self.format_string_value(field1495))
            self.newline()
            field1496 = unwrapped_fields1494[1]
            self.write(self.format_string_value(field1496))
            self.dedent()
            self.write(")")

    def pretty_iceberg_auth_properties(self, msg: Sequence[tuple[str, str]]):
        flat1501 = self._try_flat(msg, self.pretty_iceberg_auth_properties)
        if flat1501 is not None:
            assert flat1501 is not None
            self.write(flat1501)
            return None
        else:
            fields1498 = msg
            self.write("(auth_properties")
            self.indent_sexp()
            if not len(fields1498) == 0:
                self.newline()
                for i1500, elem1499 in enumerate(fields1498):
                    if (i1500 > 0):
                        self.newline()
                    self.pretty_iceberg_masked_property_entry(elem1499)
            self.dedent()
            self.write(")")

    def pretty_iceberg_masked_property_entry(self, msg: tuple[str, str]):
        flat1506 = self._try_flat(msg, self.pretty_iceberg_masked_property_entry)
        if flat1506 is not None:
            assert flat1506 is not None
            self.write(flat1506)
            return None
        else:
            _dollar_dollar = msg
            _t1744 = self.mask_secret_value(_dollar_dollar)
            fields1502 = (_dollar_dollar[0], _t1744,)
            assert fields1502 is not None
            unwrapped_fields1503 = fields1502
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1504 = unwrapped_fields1503[0]
            self.write(self.format_string_value(field1504))
            self.newline()
            field1505 = unwrapped_fields1503[1]
            self.write(self.format_string_value(field1505))
            self.dedent()
            self.write(")")

    def pretty_iceberg_from_snapshot(self, msg: str):
        flat1508 = self._try_flat(msg, self.pretty_iceberg_from_snapshot)
        if flat1508 is not None:
            assert flat1508 is not None
            self.write(flat1508)
            return None
        else:
            fields1507 = msg
            self.write("(from_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1507))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1510 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1510 is not None:
            assert flat1510 is not None
            self.write(flat1510)
            return None
        else:
            fields1509 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1509))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1513 = self._try_flat(msg, self.pretty_undefine)
        if flat1513 is not None:
            assert flat1513 is not None
            self.write(flat1513)
            return None
        else:
            _dollar_dollar = msg
            fields1511 = _dollar_dollar.fragment_id
            assert fields1511 is not None
            unwrapped_fields1512 = fields1511
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1512)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1518 = self._try_flat(msg, self.pretty_context)
        if flat1518 is not None:
            assert flat1518 is not None
            self.write(flat1518)
            return None
        else:
            _dollar_dollar = msg
            fields1514 = _dollar_dollar.relations
            assert fields1514 is not None
            unwrapped_fields1515 = fields1514
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1515) == 0:
                self.newline()
                for i1517, elem1516 in enumerate(unwrapped_fields1515):
                    if (i1517 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1516)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1525 = self._try_flat(msg, self.pretty_snapshot)
        if flat1525 is not None:
            assert flat1525 is not None
            self.write(flat1525)
            return None
        else:
            _dollar_dollar = msg
            fields1519 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
            assert fields1519 is not None
            unwrapped_fields1520 = fields1519
            self.write("(snapshot")
            self.indent_sexp()
            self.newline()
            field1521 = unwrapped_fields1520[0]
            self.pretty_edb_path(field1521)
            field1522 = unwrapped_fields1520[1]
            if not len(field1522) == 0:
                self.newline()
                for i1524, elem1523 in enumerate(field1522):
                    if (i1524 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1523)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1530 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1530 is not None:
            assert flat1530 is not None
            self.write(flat1530)
            return None
        else:
            _dollar_dollar = msg
            fields1526 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1526 is not None
            unwrapped_fields1527 = fields1526
            field1528 = unwrapped_fields1527[0]
            self.pretty_edb_path(field1528)
            self.write(" ")
            field1529 = unwrapped_fields1527[1]
            self.pretty_relation_id(field1529)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1534 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1534 is not None:
            assert flat1534 is not None
            self.write(flat1534)
            return None
        else:
            fields1531 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1531) == 0:
                self.newline()
                for i1533, elem1532 in enumerate(fields1531):
                    if (i1533 > 0):
                        self.newline()
                    self.pretty_read(elem1532)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1545 = self._try_flat(msg, self.pretty_read)
        if flat1545 is not None:
            assert flat1545 is not None
            self.write(flat1545)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1745 = _dollar_dollar.demand
            else:
                _t1745 = None
            deconstruct_result1543 = _t1745
            if deconstruct_result1543 is not None:
                assert deconstruct_result1543 is not None
                unwrapped1544 = deconstruct_result1543
                self.pretty_demand(unwrapped1544)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1746 = _dollar_dollar.output
                else:
                    _t1746 = None
                deconstruct_result1541 = _t1746
                if deconstruct_result1541 is not None:
                    assert deconstruct_result1541 is not None
                    unwrapped1542 = deconstruct_result1541
                    self.pretty_output(unwrapped1542)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1747 = _dollar_dollar.what_if
                    else:
                        _t1747 = None
                    deconstruct_result1539 = _t1747
                    if deconstruct_result1539 is not None:
                        assert deconstruct_result1539 is not None
                        unwrapped1540 = deconstruct_result1539
                        self.pretty_what_if(unwrapped1540)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1748 = _dollar_dollar.abort
                        else:
                            _t1748 = None
                        deconstruct_result1537 = _t1748
                        if deconstruct_result1537 is not None:
                            assert deconstruct_result1537 is not None
                            unwrapped1538 = deconstruct_result1537
                            self.pretty_abort(unwrapped1538)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1749 = _dollar_dollar.export
                            else:
                                _t1749 = None
                            deconstruct_result1535 = _t1749
                            if deconstruct_result1535 is not None:
                                assert deconstruct_result1535 is not None
                                unwrapped1536 = deconstruct_result1535
                                self.pretty_export(unwrapped1536)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1548 = self._try_flat(msg, self.pretty_demand)
        if flat1548 is not None:
            assert flat1548 is not None
            self.write(flat1548)
            return None
        else:
            _dollar_dollar = msg
            fields1546 = _dollar_dollar.relation_id
            assert fields1546 is not None
            unwrapped_fields1547 = fields1546
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1547)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1553 = self._try_flat(msg, self.pretty_output)
        if flat1553 is not None:
            assert flat1553 is not None
            self.write(flat1553)
            return None
        else:
            _dollar_dollar = msg
            fields1549 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1549 is not None
            unwrapped_fields1550 = fields1549
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1551 = unwrapped_fields1550[0]
            self.pretty_name(field1551)
            self.newline()
            field1552 = unwrapped_fields1550[1]
            self.pretty_relation_id(field1552)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1558 = self._try_flat(msg, self.pretty_what_if)
        if flat1558 is not None:
            assert flat1558 is not None
            self.write(flat1558)
            return None
        else:
            _dollar_dollar = msg
            fields1554 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1554 is not None
            unwrapped_fields1555 = fields1554
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1556 = unwrapped_fields1555[0]
            self.pretty_name(field1556)
            self.newline()
            field1557 = unwrapped_fields1555[1]
            self.pretty_epoch(field1557)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1564 = self._try_flat(msg, self.pretty_abort)
        if flat1564 is not None:
            assert flat1564 is not None
            self.write(flat1564)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1750 = _dollar_dollar.name
            else:
                _t1750 = None
            fields1559 = (_t1750, _dollar_dollar.relation_id,)
            assert fields1559 is not None
            unwrapped_fields1560 = fields1559
            self.write("(abort")
            self.indent_sexp()
            field1561 = unwrapped_fields1560[0]
            if field1561 is not None:
                self.newline()
                assert field1561 is not None
                opt_val1562 = field1561
                self.pretty_name(opt_val1562)
            self.newline()
            field1563 = unwrapped_fields1560[1]
            self.pretty_relation_id(field1563)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1569 = self._try_flat(msg, self.pretty_export)
        if flat1569 is not None:
            assert flat1569 is not None
            self.write(flat1569)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1751 = _dollar_dollar.csv_config
            else:
                _t1751 = None
            deconstruct_result1567 = _t1751
            if deconstruct_result1567 is not None:
                assert deconstruct_result1567 is not None
                unwrapped1568 = deconstruct_result1567
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1568)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1752 = _dollar_dollar.iceberg_config
                else:
                    _t1752 = None
                deconstruct_result1565 = _t1752
                if deconstruct_result1565 is not None:
                    assert deconstruct_result1565 is not None
                    unwrapped1566 = deconstruct_result1565
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1566)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1580 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1580 is not None:
            assert flat1580 is not None
            self.write(flat1580)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1753 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1753 = None
            deconstruct_result1575 = _t1753
            if deconstruct_result1575 is not None:
                assert deconstruct_result1575 is not None
                unwrapped1576 = deconstruct_result1575
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1577 = unwrapped1576[0]
                self.pretty_export_csv_path(field1577)
                self.newline()
                field1578 = unwrapped1576[1]
                self.pretty_export_csv_source(field1578)
                self.newline()
                field1579 = unwrapped1576[2]
                self.pretty_csv_config(field1579)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1755 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1754 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1755,)
                else:
                    _t1754 = None
                deconstruct_result1570 = _t1754
                if deconstruct_result1570 is not None:
                    assert deconstruct_result1570 is not None
                    unwrapped1571 = deconstruct_result1570
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1572 = unwrapped1571[0]
                    self.pretty_export_csv_path(field1572)
                    self.newline()
                    field1573 = unwrapped1571[1]
                    self.pretty_export_csv_columns_list(field1573)
                    self.newline()
                    field1574 = unwrapped1571[2]
                    self.pretty_config_dict(field1574)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1582 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1582 is not None:
            assert flat1582 is not None
            self.write(flat1582)
            return None
        else:
            fields1581 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1581))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1589 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1589 is not None:
            assert flat1589 is not None
            self.write(flat1589)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1756 = _dollar_dollar.gnf_columns.columns
            else:
                _t1756 = None
            deconstruct_result1585 = _t1756
            if deconstruct_result1585 is not None:
                assert deconstruct_result1585 is not None
                unwrapped1586 = deconstruct_result1585
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1586) == 0:
                    self.newline()
                    for i1588, elem1587 in enumerate(unwrapped1586):
                        if (i1588 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1587)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1757 = _dollar_dollar.table_def
                else:
                    _t1757 = None
                deconstruct_result1583 = _t1757
                if deconstruct_result1583 is not None:
                    assert deconstruct_result1583 is not None
                    unwrapped1584 = deconstruct_result1583
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1584)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1594 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1594 is not None:
            assert flat1594 is not None
            self.write(flat1594)
            return None
        else:
            _dollar_dollar = msg
            fields1590 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1590 is not None
            unwrapped_fields1591 = fields1590
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1592 = unwrapped_fields1591[0]
            self.write(self.format_string_value(field1592))
            self.newline()
            field1593 = unwrapped_fields1591[1]
            self.pretty_relation_id(field1593)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1598 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1598 is not None:
            assert flat1598 is not None
            self.write(flat1598)
            return None
        else:
            fields1595 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1595) == 0:
                self.newline()
                for i1597, elem1596 in enumerate(fields1595):
                    if (i1597 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1596)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1607 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1607 is not None:
            assert flat1607 is not None
            self.write(flat1607)
            return None
        else:
            _dollar_dollar = msg
            _t1758 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1599 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sorted(_dollar_dollar.table_properties.items()), _t1758,)
            assert fields1599 is not None
            unwrapped_fields1600 = fields1599
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1601 = unwrapped_fields1600[0]
            self.pretty_iceberg_locator(field1601)
            self.newline()
            field1602 = unwrapped_fields1600[1]
            self.pretty_iceberg_catalog_config(field1602)
            self.newline()
            field1603 = unwrapped_fields1600[2]
            self.pretty_export_iceberg_table_def(field1603)
            self.newline()
            field1604 = unwrapped_fields1600[3]
            self.pretty_iceberg_table_properties(field1604)
            field1605 = unwrapped_fields1600[4]
            if field1605 is not None:
                self.newline()
                assert field1605 is not None
                opt_val1606 = field1605
                self.pretty_config_dict(opt_val1606)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_table_def(self, msg: logic_pb2.RelationId):
        flat1609 = self._try_flat(msg, self.pretty_export_iceberg_table_def)
        if flat1609 is not None:
            assert flat1609 is not None
            self.write(flat1609)
            return None
        else:
            fields1608 = msg
            self.write("(table_def")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1608)
            self.dedent()
            self.write(")")

    def pretty_iceberg_table_properties(self, msg: Sequence[tuple[str, str]]):
        flat1613 = self._try_flat(msg, self.pretty_iceberg_table_properties)
        if flat1613 is not None:
            assert flat1613 is not None
            self.write(flat1613)
            return None
        else:
            fields1610 = msg
            self.write("(table_properties")
            self.indent_sexp()
            if not len(fields1610) == 0:
                self.newline()
                for i1612, elem1611 in enumerate(fields1610):
                    if (i1612 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1611)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1806 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1806)
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
        elif isinstance(msg, logic_pb2.CSVTarget):
            self.pretty_csv_table(msg)
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
