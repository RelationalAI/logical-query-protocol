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
        _t1764 = logic_pb2.Value(int32_value=v)
        return _t1764

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1765 = logic_pb2.Value(int_value=v)
        return _t1765

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1766 = logic_pb2.Value(float_value=v)
        return _t1766

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1767 = logic_pb2.Value(string_value=v)
        return _t1767

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1768 = logic_pb2.Value(boolean_value=v)
        return _t1768

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1769 = logic_pb2.Value(uint128_value=v)
        return _t1769

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1770 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1770,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1771 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1771,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1772 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1772,))
        _t1773 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1773,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1774 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1774,))
        _t1775 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1775,))
        if msg.new_line != "":
            _t1776 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1776,))
        _t1777 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1777,))
        _t1778 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1778,))
        _t1779 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1779,))
        if msg.comment != "":
            _t1780 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1780,))
        for missing_string in msg.missing_strings:
            _t1781 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1781,))
        _t1782 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1782,))
        _t1783 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1783,))
        _t1784 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1784,))
        if msg.partition_size_mb != 0:
            _t1785 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1785,))
        return sorted(result)

    def deconstruct_csv_storage_integration_optional(self, msg: logic_pb2.CSVConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        if not msg.HasField("storage_integration"):
            return None
        else:
            _t1786 = None
        assert msg.storage_integration is not None
        si = msg.storage_integration
        result = []
        if si.provider != "":
            _t1787 = self._make_value_string(si.provider)
            result.append(("provider", _t1787,))
        if si.azure_sas_token != "":
            _t1788 = self._make_value_string("***")
            result.append(("azure_sas_token", _t1788,))
        if si.s3_region != "":
            _t1789 = self._make_value_string(si.s3_region)
            result.append(("s3_region", _t1789,))
        if si.s3_access_key_id != "":
            _t1790 = self._make_value_string("***")
            result.append(("s3_access_key_id", _t1790,))
        if si.s3_secret_access_key != "":
            _t1791 = self._make_value_string("***")
            result.append(("s3_secret_access_key", _t1791,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1792 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1792,))
        _t1793 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1793,))
        _t1794 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1794,))
        _t1795 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1795,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1796 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1796,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1797 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1797,))
        _t1798 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1798,))
        _t1799 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1799,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1800 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1800,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1801 = self._make_value_string(msg.compression)
            result.append(("compression", _t1801,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1802 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1802,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1803 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1803,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1804 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1804,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1805 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1805,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1806 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1806,))
        return sorted(result)

    def mask_secret_value(self, pair: tuple[str, str]) -> str:
        return "***"

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1807 = None
        return None

    def deconstruct_iceberg_data_from_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.from_snapshot is not None
        if msg.from_snapshot != "":
            assert msg.from_snapshot is not None
            return msg.from_snapshot
        else:
            _t1808 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1809 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1810 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1810,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1811 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1811,))
        if msg.compression != "":
            _t1812 = self._make_value_string(msg.compression)
            result.append(("compression", _t1812,))
        if len(result) == 0:
            return None
        else:
            _t1813 = None
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
            _t1814 = None
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
        flat818 = self._try_flat(msg, self.pretty_transaction)
        if flat818 is not None:
            assert flat818 is not None
            self.write(flat818)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1618 = _dollar_dollar.configure
            else:
                _t1618 = None
            if _dollar_dollar.HasField("sync"):
                _t1619 = _dollar_dollar.sync
            else:
                _t1619 = None
            fields809 = (_t1618, _t1619, _dollar_dollar.epochs,)
            assert fields809 is not None
            unwrapped_fields810 = fields809
            self.write("(transaction")
            self.indent_sexp()
            field811 = unwrapped_fields810[0]
            if field811 is not None:
                self.newline()
                assert field811 is not None
                opt_val812 = field811
                self.pretty_configure(opt_val812)
            field813 = unwrapped_fields810[1]
            if field813 is not None:
                self.newline()
                assert field813 is not None
                opt_val814 = field813
                self.pretty_sync(opt_val814)
            field815 = unwrapped_fields810[2]
            if not len(field815) == 0:
                self.newline()
                for i817, elem816 in enumerate(field815):
                    if (i817 > 0):
                        self.newline()
                    self.pretty_epoch(elem816)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat821 = self._try_flat(msg, self.pretty_configure)
        if flat821 is not None:
            assert flat821 is not None
            self.write(flat821)
            return None
        else:
            _dollar_dollar = msg
            _t1620 = self.deconstruct_configure(_dollar_dollar)
            fields819 = _t1620
            assert fields819 is not None
            unwrapped_fields820 = fields819
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields820)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat825 = self._try_flat(msg, self.pretty_config_dict)
        if flat825 is not None:
            assert flat825 is not None
            self.write(flat825)
            return None
        else:
            fields822 = msg
            self.write("{")
            self.indent()
            if not len(fields822) == 0:
                self.newline()
                for i824, elem823 in enumerate(fields822):
                    if (i824 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem823)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat830 = self._try_flat(msg, self.pretty_config_key_value)
        if flat830 is not None:
            assert flat830 is not None
            self.write(flat830)
            return None
        else:
            _dollar_dollar = msg
            fields826 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields826 is not None
            unwrapped_fields827 = fields826
            self.write(":")
            field828 = unwrapped_fields827[0]
            self.write(field828)
            self.write(" ")
            field829 = unwrapped_fields827[1]
            self.pretty_raw_value(field829)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat856 = self._try_flat(msg, self.pretty_raw_value)
        if flat856 is not None:
            assert flat856 is not None
            self.write(flat856)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1621 = _dollar_dollar.date_value
            else:
                _t1621 = None
            deconstruct_result854 = _t1621
            if deconstruct_result854 is not None:
                assert deconstruct_result854 is not None
                unwrapped855 = deconstruct_result854
                self.pretty_raw_date(unwrapped855)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1622 = _dollar_dollar.datetime_value
                else:
                    _t1622 = None
                deconstruct_result852 = _t1622
                if deconstruct_result852 is not None:
                    assert deconstruct_result852 is not None
                    unwrapped853 = deconstruct_result852
                    self.pretty_raw_datetime(unwrapped853)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1623 = _dollar_dollar.string_value
                    else:
                        _t1623 = None
                    deconstruct_result850 = _t1623
                    if deconstruct_result850 is not None:
                        assert deconstruct_result850 is not None
                        unwrapped851 = deconstruct_result850
                        self.write(self.format_string_value(unwrapped851))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1624 = _dollar_dollar.int32_value
                        else:
                            _t1624 = None
                        deconstruct_result848 = _t1624
                        if deconstruct_result848 is not None:
                            assert deconstruct_result848 is not None
                            unwrapped849 = deconstruct_result848
                            self.write((str(unwrapped849) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1625 = _dollar_dollar.int_value
                            else:
                                _t1625 = None
                            deconstruct_result846 = _t1625
                            if deconstruct_result846 is not None:
                                assert deconstruct_result846 is not None
                                unwrapped847 = deconstruct_result846
                                self.write(str(unwrapped847))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1626 = _dollar_dollar.float32_value
                                else:
                                    _t1626 = None
                                deconstruct_result844 = _t1626
                                if deconstruct_result844 is not None:
                                    assert deconstruct_result844 is not None
                                    unwrapped845 = deconstruct_result844
                                    self.write(self.format_float32_literal(unwrapped845))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1627 = _dollar_dollar.float_value
                                    else:
                                        _t1627 = None
                                    deconstruct_result842 = _t1627
                                    if deconstruct_result842 is not None:
                                        assert deconstruct_result842 is not None
                                        unwrapped843 = deconstruct_result842
                                        self.write(str(unwrapped843))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1628 = _dollar_dollar.uint32_value
                                        else:
                                            _t1628 = None
                                        deconstruct_result840 = _t1628
                                        if deconstruct_result840 is not None:
                                            assert deconstruct_result840 is not None
                                            unwrapped841 = deconstruct_result840
                                            self.write((str(unwrapped841) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1629 = _dollar_dollar.uint128_value
                                            else:
                                                _t1629 = None
                                            deconstruct_result838 = _t1629
                                            if deconstruct_result838 is not None:
                                                assert deconstruct_result838 is not None
                                                unwrapped839 = deconstruct_result838
                                                self.write(self.format_uint128(unwrapped839))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1630 = _dollar_dollar.int128_value
                                                else:
                                                    _t1630 = None
                                                deconstruct_result836 = _t1630
                                                if deconstruct_result836 is not None:
                                                    assert deconstruct_result836 is not None
                                                    unwrapped837 = deconstruct_result836
                                                    self.write(self.format_int128(unwrapped837))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1631 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1631 = None
                                                    deconstruct_result834 = _t1631
                                                    if deconstruct_result834 is not None:
                                                        assert deconstruct_result834 is not None
                                                        unwrapped835 = deconstruct_result834
                                                        self.write(self.format_decimal(unwrapped835))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1632 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1632 = None
                                                        deconstruct_result832 = _t1632
                                                        if deconstruct_result832 is not None:
                                                            assert deconstruct_result832 is not None
                                                            unwrapped833 = deconstruct_result832
                                                            self.pretty_boolean_value(unwrapped833)
                                                        else:
                                                            fields831 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat862 = self._try_flat(msg, self.pretty_raw_date)
        if flat862 is not None:
            assert flat862 is not None
            self.write(flat862)
            return None
        else:
            _dollar_dollar = msg
            fields857 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields857 is not None
            unwrapped_fields858 = fields857
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field859 = unwrapped_fields858[0]
            self.write(str(field859))
            self.newline()
            field860 = unwrapped_fields858[1]
            self.write(str(field860))
            self.newline()
            field861 = unwrapped_fields858[2]
            self.write(str(field861))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat873 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat873 is not None:
            assert flat873 is not None
            self.write(flat873)
            return None
        else:
            _dollar_dollar = msg
            fields863 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields863 is not None
            unwrapped_fields864 = fields863
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field865 = unwrapped_fields864[0]
            self.write(str(field865))
            self.newline()
            field866 = unwrapped_fields864[1]
            self.write(str(field866))
            self.newline()
            field867 = unwrapped_fields864[2]
            self.write(str(field867))
            self.newline()
            field868 = unwrapped_fields864[3]
            self.write(str(field868))
            self.newline()
            field869 = unwrapped_fields864[4]
            self.write(str(field869))
            self.newline()
            field870 = unwrapped_fields864[5]
            self.write(str(field870))
            field871 = unwrapped_fields864[6]
            if field871 is not None:
                self.newline()
                assert field871 is not None
                opt_val872 = field871
                self.write(str(opt_val872))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1633 = ()
        else:
            _t1633 = None
        deconstruct_result876 = _t1633
        if deconstruct_result876 is not None:
            assert deconstruct_result876 is not None
            unwrapped877 = deconstruct_result876
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1634 = ()
            else:
                _t1634 = None
            deconstruct_result874 = _t1634
            if deconstruct_result874 is not None:
                assert deconstruct_result874 is not None
                unwrapped875 = deconstruct_result874
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat882 = self._try_flat(msg, self.pretty_sync)
        if flat882 is not None:
            assert flat882 is not None
            self.write(flat882)
            return None
        else:
            _dollar_dollar = msg
            fields878 = _dollar_dollar.fragments
            assert fields878 is not None
            unwrapped_fields879 = fields878
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields879) == 0:
                self.newline()
                for i881, elem880 in enumerate(unwrapped_fields879):
                    if (i881 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem880)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat885 = self._try_flat(msg, self.pretty_fragment_id)
        if flat885 is not None:
            assert flat885 is not None
            self.write(flat885)
            return None
        else:
            _dollar_dollar = msg
            fields883 = self.fragment_id_to_string(_dollar_dollar)
            assert fields883 is not None
            unwrapped_fields884 = fields883
            self.write(":")
            self.write(unwrapped_fields884)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat892 = self._try_flat(msg, self.pretty_epoch)
        if flat892 is not None:
            assert flat892 is not None
            self.write(flat892)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1635 = _dollar_dollar.writes
            else:
                _t1635 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1636 = _dollar_dollar.reads
            else:
                _t1636 = None
            fields886 = (_t1635, _t1636,)
            assert fields886 is not None
            unwrapped_fields887 = fields886
            self.write("(epoch")
            self.indent_sexp()
            field888 = unwrapped_fields887[0]
            if field888 is not None:
                self.newline()
                assert field888 is not None
                opt_val889 = field888
                self.pretty_epoch_writes(opt_val889)
            field890 = unwrapped_fields887[1]
            if field890 is not None:
                self.newline()
                assert field890 is not None
                opt_val891 = field890
                self.pretty_epoch_reads(opt_val891)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat896 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat896 is not None:
            assert flat896 is not None
            self.write(flat896)
            return None
        else:
            fields893 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields893) == 0:
                self.newline()
                for i895, elem894 in enumerate(fields893):
                    if (i895 > 0):
                        self.newline()
                    self.pretty_write(elem894)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat905 = self._try_flat(msg, self.pretty_write)
        if flat905 is not None:
            assert flat905 is not None
            self.write(flat905)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1637 = _dollar_dollar.define
            else:
                _t1637 = None
            deconstruct_result903 = _t1637
            if deconstruct_result903 is not None:
                assert deconstruct_result903 is not None
                unwrapped904 = deconstruct_result903
                self.pretty_define(unwrapped904)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1638 = _dollar_dollar.undefine
                else:
                    _t1638 = None
                deconstruct_result901 = _t1638
                if deconstruct_result901 is not None:
                    assert deconstruct_result901 is not None
                    unwrapped902 = deconstruct_result901
                    self.pretty_undefine(unwrapped902)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1639 = _dollar_dollar.context
                    else:
                        _t1639 = None
                    deconstruct_result899 = _t1639
                    if deconstruct_result899 is not None:
                        assert deconstruct_result899 is not None
                        unwrapped900 = deconstruct_result899
                        self.pretty_context(unwrapped900)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1640 = _dollar_dollar.snapshot
                        else:
                            _t1640 = None
                        deconstruct_result897 = _t1640
                        if deconstruct_result897 is not None:
                            assert deconstruct_result897 is not None
                            unwrapped898 = deconstruct_result897
                            self.pretty_snapshot(unwrapped898)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat908 = self._try_flat(msg, self.pretty_define)
        if flat908 is not None:
            assert flat908 is not None
            self.write(flat908)
            return None
        else:
            _dollar_dollar = msg
            fields906 = _dollar_dollar.fragment
            assert fields906 is not None
            unwrapped_fields907 = fields906
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields907)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat915 = self._try_flat(msg, self.pretty_fragment)
        if flat915 is not None:
            assert flat915 is not None
            self.write(flat915)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields909 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields909 is not None
            unwrapped_fields910 = fields909
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field911 = unwrapped_fields910[0]
            self.pretty_new_fragment_id(field911)
            field912 = unwrapped_fields910[1]
            if not len(field912) == 0:
                self.newline()
                for i914, elem913 in enumerate(field912):
                    if (i914 > 0):
                        self.newline()
                    self.pretty_declaration(elem913)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat917 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat917 is not None:
            assert flat917 is not None
            self.write(flat917)
            return None
        else:
            fields916 = msg
            self.pretty_fragment_id(fields916)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat926 = self._try_flat(msg, self.pretty_declaration)
        if flat926 is not None:
            assert flat926 is not None
            self.write(flat926)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1641 = getattr(_dollar_dollar, 'def')
            else:
                _t1641 = None
            deconstruct_result924 = _t1641
            if deconstruct_result924 is not None:
                assert deconstruct_result924 is not None
                unwrapped925 = deconstruct_result924
                self.pretty_def(unwrapped925)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1642 = _dollar_dollar.algorithm
                else:
                    _t1642 = None
                deconstruct_result922 = _t1642
                if deconstruct_result922 is not None:
                    assert deconstruct_result922 is not None
                    unwrapped923 = deconstruct_result922
                    self.pretty_algorithm(unwrapped923)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1643 = _dollar_dollar.constraint
                    else:
                        _t1643 = None
                    deconstruct_result920 = _t1643
                    if deconstruct_result920 is not None:
                        assert deconstruct_result920 is not None
                        unwrapped921 = deconstruct_result920
                        self.pretty_constraint(unwrapped921)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1644 = _dollar_dollar.data
                        else:
                            _t1644 = None
                        deconstruct_result918 = _t1644
                        if deconstruct_result918 is not None:
                            assert deconstruct_result918 is not None
                            unwrapped919 = deconstruct_result918
                            self.pretty_data(unwrapped919)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat933 = self._try_flat(msg, self.pretty_def)
        if flat933 is not None:
            assert flat933 is not None
            self.write(flat933)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1645 = _dollar_dollar.attrs
            else:
                _t1645 = None
            fields927 = (_dollar_dollar.name, _dollar_dollar.body, _t1645,)
            assert fields927 is not None
            unwrapped_fields928 = fields927
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field929 = unwrapped_fields928[0]
            self.pretty_relation_id(field929)
            self.newline()
            field930 = unwrapped_fields928[1]
            self.pretty_abstraction(field930)
            field931 = unwrapped_fields928[2]
            if field931 is not None:
                self.newline()
                assert field931 is not None
                opt_val932 = field931
                self.pretty_attrs(opt_val932)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat938 = self._try_flat(msg, self.pretty_relation_id)
        if flat938 is not None:
            assert flat938 is not None
            self.write(flat938)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1647 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1646 = _t1647
            else:
                _t1646 = None
            deconstruct_result936 = _t1646
            if deconstruct_result936 is not None:
                assert deconstruct_result936 is not None
                unwrapped937 = deconstruct_result936
                self.write(":")
                self.write(unwrapped937)
            else:
                _dollar_dollar = msg
                _t1648 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result934 = _t1648
                if deconstruct_result934 is not None:
                    assert deconstruct_result934 is not None
                    unwrapped935 = deconstruct_result934
                    self.write(self.format_uint128(unwrapped935))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat943 = self._try_flat(msg, self.pretty_abstraction)
        if flat943 is not None:
            assert flat943 is not None
            self.write(flat943)
            return None
        else:
            _dollar_dollar = msg
            _t1649 = self.deconstruct_bindings(_dollar_dollar)
            fields939 = (_t1649, _dollar_dollar.value,)
            assert fields939 is not None
            unwrapped_fields940 = fields939
            self.write("(")
            self.indent()
            field941 = unwrapped_fields940[0]
            self.pretty_bindings(field941)
            self.newline()
            field942 = unwrapped_fields940[1]
            self.pretty_formula(field942)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat951 = self._try_flat(msg, self.pretty_bindings)
        if flat951 is not None:
            assert flat951 is not None
            self.write(flat951)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1650 = _dollar_dollar[1]
            else:
                _t1650 = None
            fields944 = (_dollar_dollar[0], _t1650,)
            assert fields944 is not None
            unwrapped_fields945 = fields944
            self.write("[")
            self.indent()
            field946 = unwrapped_fields945[0]
            for i948, elem947 in enumerate(field946):
                if (i948 > 0):
                    self.newline()
                self.pretty_binding(elem947)
            field949 = unwrapped_fields945[1]
            if field949 is not None:
                self.newline()
                assert field949 is not None
                opt_val950 = field949
                self.pretty_value_bindings(opt_val950)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat956 = self._try_flat(msg, self.pretty_binding)
        if flat956 is not None:
            assert flat956 is not None
            self.write(flat956)
            return None
        else:
            _dollar_dollar = msg
            fields952 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields952 is not None
            unwrapped_fields953 = fields952
            field954 = unwrapped_fields953[0]
            self.write(field954)
            self.write("::")
            field955 = unwrapped_fields953[1]
            self.pretty_type(field955)

    def pretty_type(self, msg: logic_pb2.Type):
        flat985 = self._try_flat(msg, self.pretty_type)
        if flat985 is not None:
            assert flat985 is not None
            self.write(flat985)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1651 = _dollar_dollar.unspecified_type
            else:
                _t1651 = None
            deconstruct_result983 = _t1651
            if deconstruct_result983 is not None:
                assert deconstruct_result983 is not None
                unwrapped984 = deconstruct_result983
                self.pretty_unspecified_type(unwrapped984)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1652 = _dollar_dollar.string_type
                else:
                    _t1652 = None
                deconstruct_result981 = _t1652
                if deconstruct_result981 is not None:
                    assert deconstruct_result981 is not None
                    unwrapped982 = deconstruct_result981
                    self.pretty_string_type(unwrapped982)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1653 = _dollar_dollar.int_type
                    else:
                        _t1653 = None
                    deconstruct_result979 = _t1653
                    if deconstruct_result979 is not None:
                        assert deconstruct_result979 is not None
                        unwrapped980 = deconstruct_result979
                        self.pretty_int_type(unwrapped980)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1654 = _dollar_dollar.float_type
                        else:
                            _t1654 = None
                        deconstruct_result977 = _t1654
                        if deconstruct_result977 is not None:
                            assert deconstruct_result977 is not None
                            unwrapped978 = deconstruct_result977
                            self.pretty_float_type(unwrapped978)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1655 = _dollar_dollar.uint128_type
                            else:
                                _t1655 = None
                            deconstruct_result975 = _t1655
                            if deconstruct_result975 is not None:
                                assert deconstruct_result975 is not None
                                unwrapped976 = deconstruct_result975
                                self.pretty_uint128_type(unwrapped976)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1656 = _dollar_dollar.int128_type
                                else:
                                    _t1656 = None
                                deconstruct_result973 = _t1656
                                if deconstruct_result973 is not None:
                                    assert deconstruct_result973 is not None
                                    unwrapped974 = deconstruct_result973
                                    self.pretty_int128_type(unwrapped974)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1657 = _dollar_dollar.date_type
                                    else:
                                        _t1657 = None
                                    deconstruct_result971 = _t1657
                                    if deconstruct_result971 is not None:
                                        assert deconstruct_result971 is not None
                                        unwrapped972 = deconstruct_result971
                                        self.pretty_date_type(unwrapped972)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1658 = _dollar_dollar.datetime_type
                                        else:
                                            _t1658 = None
                                        deconstruct_result969 = _t1658
                                        if deconstruct_result969 is not None:
                                            assert deconstruct_result969 is not None
                                            unwrapped970 = deconstruct_result969
                                            self.pretty_datetime_type(unwrapped970)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1659 = _dollar_dollar.missing_type
                                            else:
                                                _t1659 = None
                                            deconstruct_result967 = _t1659
                                            if deconstruct_result967 is not None:
                                                assert deconstruct_result967 is not None
                                                unwrapped968 = deconstruct_result967
                                                self.pretty_missing_type(unwrapped968)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1660 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1660 = None
                                                deconstruct_result965 = _t1660
                                                if deconstruct_result965 is not None:
                                                    assert deconstruct_result965 is not None
                                                    unwrapped966 = deconstruct_result965
                                                    self.pretty_decimal_type(unwrapped966)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1661 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1661 = None
                                                    deconstruct_result963 = _t1661
                                                    if deconstruct_result963 is not None:
                                                        assert deconstruct_result963 is not None
                                                        unwrapped964 = deconstruct_result963
                                                        self.pretty_boolean_type(unwrapped964)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1662 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1662 = None
                                                        deconstruct_result961 = _t1662
                                                        if deconstruct_result961 is not None:
                                                            assert deconstruct_result961 is not None
                                                            unwrapped962 = deconstruct_result961
                                                            self.pretty_int32_type(unwrapped962)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1663 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1663 = None
                                                            deconstruct_result959 = _t1663
                                                            if deconstruct_result959 is not None:
                                                                assert deconstruct_result959 is not None
                                                                unwrapped960 = deconstruct_result959
                                                                self.pretty_float32_type(unwrapped960)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1664 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1664 = None
                                                                deconstruct_result957 = _t1664
                                                                if deconstruct_result957 is not None:
                                                                    assert deconstruct_result957 is not None
                                                                    unwrapped958 = deconstruct_result957
                                                                    self.pretty_uint32_type(unwrapped958)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields986 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields987 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields988 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields989 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields990 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields991 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields992 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields993 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields994 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat999 = self._try_flat(msg, self.pretty_decimal_type)
        if flat999 is not None:
            assert flat999 is not None
            self.write(flat999)
            return None
        else:
            _dollar_dollar = msg
            fields995 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields995 is not None
            unwrapped_fields996 = fields995
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field997 = unwrapped_fields996[0]
            self.write(str(field997))
            self.newline()
            field998 = unwrapped_fields996[1]
            self.write(str(field998))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields1000 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields1001 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields1002 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields1003 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat1007 = self._try_flat(msg, self.pretty_value_bindings)
        if flat1007 is not None:
            assert flat1007 is not None
            self.write(flat1007)
            return None
        else:
            fields1004 = msg
            self.write("|")
            if not len(fields1004) == 0:
                self.write(" ")
                for i1006, elem1005 in enumerate(fields1004):
                    if (i1006 > 0):
                        self.newline()
                    self.pretty_binding(elem1005)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1034 = self._try_flat(msg, self.pretty_formula)
        if flat1034 is not None:
            assert flat1034 is not None
            self.write(flat1034)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1665 = _dollar_dollar.conjunction
            else:
                _t1665 = None
            deconstruct_result1032 = _t1665
            if deconstruct_result1032 is not None:
                assert deconstruct_result1032 is not None
                unwrapped1033 = deconstruct_result1032
                self.pretty_true(unwrapped1033)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1666 = _dollar_dollar.disjunction
                else:
                    _t1666 = None
                deconstruct_result1030 = _t1666
                if deconstruct_result1030 is not None:
                    assert deconstruct_result1030 is not None
                    unwrapped1031 = deconstruct_result1030
                    self.pretty_false(unwrapped1031)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1667 = _dollar_dollar.exists
                    else:
                        _t1667 = None
                    deconstruct_result1028 = _t1667
                    if deconstruct_result1028 is not None:
                        assert deconstruct_result1028 is not None
                        unwrapped1029 = deconstruct_result1028
                        self.pretty_exists(unwrapped1029)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1668 = _dollar_dollar.reduce
                        else:
                            _t1668 = None
                        deconstruct_result1026 = _t1668
                        if deconstruct_result1026 is not None:
                            assert deconstruct_result1026 is not None
                            unwrapped1027 = deconstruct_result1026
                            self.pretty_reduce(unwrapped1027)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1669 = _dollar_dollar.conjunction
                            else:
                                _t1669 = None
                            deconstruct_result1024 = _t1669
                            if deconstruct_result1024 is not None:
                                assert deconstruct_result1024 is not None
                                unwrapped1025 = deconstruct_result1024
                                self.pretty_conjunction(unwrapped1025)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1670 = _dollar_dollar.disjunction
                                else:
                                    _t1670 = None
                                deconstruct_result1022 = _t1670
                                if deconstruct_result1022 is not None:
                                    assert deconstruct_result1022 is not None
                                    unwrapped1023 = deconstruct_result1022
                                    self.pretty_disjunction(unwrapped1023)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1671 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1671 = None
                                    deconstruct_result1020 = _t1671
                                    if deconstruct_result1020 is not None:
                                        assert deconstruct_result1020 is not None
                                        unwrapped1021 = deconstruct_result1020
                                        self.pretty_not(unwrapped1021)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1672 = _dollar_dollar.ffi
                                        else:
                                            _t1672 = None
                                        deconstruct_result1018 = _t1672
                                        if deconstruct_result1018 is not None:
                                            assert deconstruct_result1018 is not None
                                            unwrapped1019 = deconstruct_result1018
                                            self.pretty_ffi(unwrapped1019)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1673 = _dollar_dollar.atom
                                            else:
                                                _t1673 = None
                                            deconstruct_result1016 = _t1673
                                            if deconstruct_result1016 is not None:
                                                assert deconstruct_result1016 is not None
                                                unwrapped1017 = deconstruct_result1016
                                                self.pretty_atom(unwrapped1017)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1674 = _dollar_dollar.pragma
                                                else:
                                                    _t1674 = None
                                                deconstruct_result1014 = _t1674
                                                if deconstruct_result1014 is not None:
                                                    assert deconstruct_result1014 is not None
                                                    unwrapped1015 = deconstruct_result1014
                                                    self.pretty_pragma(unwrapped1015)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1675 = _dollar_dollar.primitive
                                                    else:
                                                        _t1675 = None
                                                    deconstruct_result1012 = _t1675
                                                    if deconstruct_result1012 is not None:
                                                        assert deconstruct_result1012 is not None
                                                        unwrapped1013 = deconstruct_result1012
                                                        self.pretty_primitive(unwrapped1013)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1676 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1676 = None
                                                        deconstruct_result1010 = _t1676
                                                        if deconstruct_result1010 is not None:
                                                            assert deconstruct_result1010 is not None
                                                            unwrapped1011 = deconstruct_result1010
                                                            self.pretty_rel_atom(unwrapped1011)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1677 = _dollar_dollar.cast
                                                            else:
                                                                _t1677 = None
                                                            deconstruct_result1008 = _t1677
                                                            if deconstruct_result1008 is not None:
                                                                assert deconstruct_result1008 is not None
                                                                unwrapped1009 = deconstruct_result1008
                                                                self.pretty_cast(unwrapped1009)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields1035 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1036 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1041 = self._try_flat(msg, self.pretty_exists)
        if flat1041 is not None:
            assert flat1041 is not None
            self.write(flat1041)
            return None
        else:
            _dollar_dollar = msg
            _t1678 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1037 = (_t1678, _dollar_dollar.body.value,)
            assert fields1037 is not None
            unwrapped_fields1038 = fields1037
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1039 = unwrapped_fields1038[0]
            self.pretty_bindings(field1039)
            self.newline()
            field1040 = unwrapped_fields1038[1]
            self.pretty_formula(field1040)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1047 = self._try_flat(msg, self.pretty_reduce)
        if flat1047 is not None:
            assert flat1047 is not None
            self.write(flat1047)
            return None
        else:
            _dollar_dollar = msg
            fields1042 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1042 is not None
            unwrapped_fields1043 = fields1042
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1044 = unwrapped_fields1043[0]
            self.pretty_abstraction(field1044)
            self.newline()
            field1045 = unwrapped_fields1043[1]
            self.pretty_abstraction(field1045)
            self.newline()
            field1046 = unwrapped_fields1043[2]
            self.pretty_terms(field1046)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1051 = self._try_flat(msg, self.pretty_terms)
        if flat1051 is not None:
            assert flat1051 is not None
            self.write(flat1051)
            return None
        else:
            fields1048 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1048) == 0:
                self.newline()
                for i1050, elem1049 in enumerate(fields1048):
                    if (i1050 > 0):
                        self.newline()
                    self.pretty_term(elem1049)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1056 = self._try_flat(msg, self.pretty_term)
        if flat1056 is not None:
            assert flat1056 is not None
            self.write(flat1056)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1679 = _dollar_dollar.var
            else:
                _t1679 = None
            deconstruct_result1054 = _t1679
            if deconstruct_result1054 is not None:
                assert deconstruct_result1054 is not None
                unwrapped1055 = deconstruct_result1054
                self.pretty_var(unwrapped1055)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1680 = _dollar_dollar.constant
                else:
                    _t1680 = None
                deconstruct_result1052 = _t1680
                if deconstruct_result1052 is not None:
                    assert deconstruct_result1052 is not None
                    unwrapped1053 = deconstruct_result1052
                    self.pretty_value(unwrapped1053)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1059 = self._try_flat(msg, self.pretty_var)
        if flat1059 is not None:
            assert flat1059 is not None
            self.write(flat1059)
            return None
        else:
            _dollar_dollar = msg
            fields1057 = _dollar_dollar.name
            assert fields1057 is not None
            unwrapped_fields1058 = fields1057
            self.write(unwrapped_fields1058)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1085 = self._try_flat(msg, self.pretty_value)
        if flat1085 is not None:
            assert flat1085 is not None
            self.write(flat1085)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1681 = _dollar_dollar.date_value
            else:
                _t1681 = None
            deconstruct_result1083 = _t1681
            if deconstruct_result1083 is not None:
                assert deconstruct_result1083 is not None
                unwrapped1084 = deconstruct_result1083
                self.pretty_date(unwrapped1084)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1682 = _dollar_dollar.datetime_value
                else:
                    _t1682 = None
                deconstruct_result1081 = _t1682
                if deconstruct_result1081 is not None:
                    assert deconstruct_result1081 is not None
                    unwrapped1082 = deconstruct_result1081
                    self.pretty_datetime(unwrapped1082)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1683 = _dollar_dollar.string_value
                    else:
                        _t1683 = None
                    deconstruct_result1079 = _t1683
                    if deconstruct_result1079 is not None:
                        assert deconstruct_result1079 is not None
                        unwrapped1080 = deconstruct_result1079
                        self.write(self.format_string_value(unwrapped1080))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1684 = _dollar_dollar.int32_value
                        else:
                            _t1684 = None
                        deconstruct_result1077 = _t1684
                        if deconstruct_result1077 is not None:
                            assert deconstruct_result1077 is not None
                            unwrapped1078 = deconstruct_result1077
                            self.write((str(unwrapped1078) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1685 = _dollar_dollar.int_value
                            else:
                                _t1685 = None
                            deconstruct_result1075 = _t1685
                            if deconstruct_result1075 is not None:
                                assert deconstruct_result1075 is not None
                                unwrapped1076 = deconstruct_result1075
                                self.write(str(unwrapped1076))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1686 = _dollar_dollar.float32_value
                                else:
                                    _t1686 = None
                                deconstruct_result1073 = _t1686
                                if deconstruct_result1073 is not None:
                                    assert deconstruct_result1073 is not None
                                    unwrapped1074 = deconstruct_result1073
                                    self.write(self.format_float32_literal(unwrapped1074))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1687 = _dollar_dollar.float_value
                                    else:
                                        _t1687 = None
                                    deconstruct_result1071 = _t1687
                                    if deconstruct_result1071 is not None:
                                        assert deconstruct_result1071 is not None
                                        unwrapped1072 = deconstruct_result1071
                                        self.write(str(unwrapped1072))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1688 = _dollar_dollar.uint32_value
                                        else:
                                            _t1688 = None
                                        deconstruct_result1069 = _t1688
                                        if deconstruct_result1069 is not None:
                                            assert deconstruct_result1069 is not None
                                            unwrapped1070 = deconstruct_result1069
                                            self.write((str(unwrapped1070) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1689 = _dollar_dollar.uint128_value
                                            else:
                                                _t1689 = None
                                            deconstruct_result1067 = _t1689
                                            if deconstruct_result1067 is not None:
                                                assert deconstruct_result1067 is not None
                                                unwrapped1068 = deconstruct_result1067
                                                self.write(self.format_uint128(unwrapped1068))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1690 = _dollar_dollar.int128_value
                                                else:
                                                    _t1690 = None
                                                deconstruct_result1065 = _t1690
                                                if deconstruct_result1065 is not None:
                                                    assert deconstruct_result1065 is not None
                                                    unwrapped1066 = deconstruct_result1065
                                                    self.write(self.format_int128(unwrapped1066))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1691 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1691 = None
                                                    deconstruct_result1063 = _t1691
                                                    if deconstruct_result1063 is not None:
                                                        assert deconstruct_result1063 is not None
                                                        unwrapped1064 = deconstruct_result1063
                                                        self.write(self.format_decimal(unwrapped1064))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1692 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1692 = None
                                                        deconstruct_result1061 = _t1692
                                                        if deconstruct_result1061 is not None:
                                                            assert deconstruct_result1061 is not None
                                                            unwrapped1062 = deconstruct_result1061
                                                            self.pretty_boolean_value(unwrapped1062)
                                                        else:
                                                            fields1060 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1091 = self._try_flat(msg, self.pretty_date)
        if flat1091 is not None:
            assert flat1091 is not None
            self.write(flat1091)
            return None
        else:
            _dollar_dollar = msg
            fields1086 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1086 is not None
            unwrapped_fields1087 = fields1086
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1088 = unwrapped_fields1087[0]
            self.write(str(field1088))
            self.newline()
            field1089 = unwrapped_fields1087[1]
            self.write(str(field1089))
            self.newline()
            field1090 = unwrapped_fields1087[2]
            self.write(str(field1090))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1102 = self._try_flat(msg, self.pretty_datetime)
        if flat1102 is not None:
            assert flat1102 is not None
            self.write(flat1102)
            return None
        else:
            _dollar_dollar = msg
            fields1092 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1092 is not None
            unwrapped_fields1093 = fields1092
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1094 = unwrapped_fields1093[0]
            self.write(str(field1094))
            self.newline()
            field1095 = unwrapped_fields1093[1]
            self.write(str(field1095))
            self.newline()
            field1096 = unwrapped_fields1093[2]
            self.write(str(field1096))
            self.newline()
            field1097 = unwrapped_fields1093[3]
            self.write(str(field1097))
            self.newline()
            field1098 = unwrapped_fields1093[4]
            self.write(str(field1098))
            self.newline()
            field1099 = unwrapped_fields1093[5]
            self.write(str(field1099))
            field1100 = unwrapped_fields1093[6]
            if field1100 is not None:
                self.newline()
                assert field1100 is not None
                opt_val1101 = field1100
                self.write(str(opt_val1101))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1107 = self._try_flat(msg, self.pretty_conjunction)
        if flat1107 is not None:
            assert flat1107 is not None
            self.write(flat1107)
            return None
        else:
            _dollar_dollar = msg
            fields1103 = _dollar_dollar.args
            assert fields1103 is not None
            unwrapped_fields1104 = fields1103
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1104) == 0:
                self.newline()
                for i1106, elem1105 in enumerate(unwrapped_fields1104):
                    if (i1106 > 0):
                        self.newline()
                    self.pretty_formula(elem1105)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1112 = self._try_flat(msg, self.pretty_disjunction)
        if flat1112 is not None:
            assert flat1112 is not None
            self.write(flat1112)
            return None
        else:
            _dollar_dollar = msg
            fields1108 = _dollar_dollar.args
            assert fields1108 is not None
            unwrapped_fields1109 = fields1108
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1109) == 0:
                self.newline()
                for i1111, elem1110 in enumerate(unwrapped_fields1109):
                    if (i1111 > 0):
                        self.newline()
                    self.pretty_formula(elem1110)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1115 = self._try_flat(msg, self.pretty_not)
        if flat1115 is not None:
            assert flat1115 is not None
            self.write(flat1115)
            return None
        else:
            _dollar_dollar = msg
            fields1113 = _dollar_dollar.arg
            assert fields1113 is not None
            unwrapped_fields1114 = fields1113
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1114)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1121 = self._try_flat(msg, self.pretty_ffi)
        if flat1121 is not None:
            assert flat1121 is not None
            self.write(flat1121)
            return None
        else:
            _dollar_dollar = msg
            fields1116 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1116 is not None
            unwrapped_fields1117 = fields1116
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1118 = unwrapped_fields1117[0]
            self.pretty_name(field1118)
            self.newline()
            field1119 = unwrapped_fields1117[1]
            self.pretty_ffi_args(field1119)
            self.newline()
            field1120 = unwrapped_fields1117[2]
            self.pretty_terms(field1120)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1123 = self._try_flat(msg, self.pretty_name)
        if flat1123 is not None:
            assert flat1123 is not None
            self.write(flat1123)
            return None
        else:
            fields1122 = msg
            self.write(":")
            self.write(fields1122)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1127 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1127 is not None:
            assert flat1127 is not None
            self.write(flat1127)
            return None
        else:
            fields1124 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1124) == 0:
                self.newline()
                for i1126, elem1125 in enumerate(fields1124):
                    if (i1126 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1125)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1134 = self._try_flat(msg, self.pretty_atom)
        if flat1134 is not None:
            assert flat1134 is not None
            self.write(flat1134)
            return None
        else:
            _dollar_dollar = msg
            fields1128 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1128 is not None
            unwrapped_fields1129 = fields1128
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1130 = unwrapped_fields1129[0]
            self.pretty_relation_id(field1130)
            field1131 = unwrapped_fields1129[1]
            if not len(field1131) == 0:
                self.newline()
                for i1133, elem1132 in enumerate(field1131):
                    if (i1133 > 0):
                        self.newline()
                    self.pretty_term(elem1132)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1141 = self._try_flat(msg, self.pretty_pragma)
        if flat1141 is not None:
            assert flat1141 is not None
            self.write(flat1141)
            return None
        else:
            _dollar_dollar = msg
            fields1135 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1135 is not None
            unwrapped_fields1136 = fields1135
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1137 = unwrapped_fields1136[0]
            self.pretty_name(field1137)
            field1138 = unwrapped_fields1136[1]
            if not len(field1138) == 0:
                self.newline()
                for i1140, elem1139 in enumerate(field1138):
                    if (i1140 > 0):
                        self.newline()
                    self.pretty_term(elem1139)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1157 = self._try_flat(msg, self.pretty_primitive)
        if flat1157 is not None:
            assert flat1157 is not None
            self.write(flat1157)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1693 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1693 = None
            guard_result1156 = _t1693
            if guard_result1156 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1694 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1694 = None
                guard_result1155 = _t1694
                if guard_result1155 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1695 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1695 = None
                    guard_result1154 = _t1695
                    if guard_result1154 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1696 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1696 = None
                        guard_result1153 = _t1696
                        if guard_result1153 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1697 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1697 = None
                            guard_result1152 = _t1697
                            if guard_result1152 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1698 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1698 = None
                                guard_result1151 = _t1698
                                if guard_result1151 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1699 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1699 = None
                                    guard_result1150 = _t1699
                                    if guard_result1150 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1700 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1700 = None
                                        guard_result1149 = _t1700
                                        if guard_result1149 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1701 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1701 = None
                                            guard_result1148 = _t1701
                                            if guard_result1148 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1142 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1142 is not None
                                                unwrapped_fields1143 = fields1142
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1144 = unwrapped_fields1143[0]
                                                self.pretty_name(field1144)
                                                field1145 = unwrapped_fields1143[1]
                                                if not len(field1145) == 0:
                                                    self.newline()
                                                    for i1147, elem1146 in enumerate(field1145):
                                                        if (i1147 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1146)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1162 = self._try_flat(msg, self.pretty_eq)
        if flat1162 is not None:
            assert flat1162 is not None
            self.write(flat1162)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1702 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1702 = None
            fields1158 = _t1702
            assert fields1158 is not None
            unwrapped_fields1159 = fields1158
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1160 = unwrapped_fields1159[0]
            self.pretty_term(field1160)
            self.newline()
            field1161 = unwrapped_fields1159[1]
            self.pretty_term(field1161)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1167 = self._try_flat(msg, self.pretty_lt)
        if flat1167 is not None:
            assert flat1167 is not None
            self.write(flat1167)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1703 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1703 = None
            fields1163 = _t1703
            assert fields1163 is not None
            unwrapped_fields1164 = fields1163
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1165 = unwrapped_fields1164[0]
            self.pretty_term(field1165)
            self.newline()
            field1166 = unwrapped_fields1164[1]
            self.pretty_term(field1166)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1172 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1172 is not None:
            assert flat1172 is not None
            self.write(flat1172)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1704 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1704 = None
            fields1168 = _t1704
            assert fields1168 is not None
            unwrapped_fields1169 = fields1168
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1170 = unwrapped_fields1169[0]
            self.pretty_term(field1170)
            self.newline()
            field1171 = unwrapped_fields1169[1]
            self.pretty_term(field1171)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1177 = self._try_flat(msg, self.pretty_gt)
        if flat1177 is not None:
            assert flat1177 is not None
            self.write(flat1177)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1705 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1705 = None
            fields1173 = _t1705
            assert fields1173 is not None
            unwrapped_fields1174 = fields1173
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1175 = unwrapped_fields1174[0]
            self.pretty_term(field1175)
            self.newline()
            field1176 = unwrapped_fields1174[1]
            self.pretty_term(field1176)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1182 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1182 is not None:
            assert flat1182 is not None
            self.write(flat1182)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1706 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1706 = None
            fields1178 = _t1706
            assert fields1178 is not None
            unwrapped_fields1179 = fields1178
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1180 = unwrapped_fields1179[0]
            self.pretty_term(field1180)
            self.newline()
            field1181 = unwrapped_fields1179[1]
            self.pretty_term(field1181)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1188 = self._try_flat(msg, self.pretty_add)
        if flat1188 is not None:
            assert flat1188 is not None
            self.write(flat1188)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1707 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1707 = None
            fields1183 = _t1707
            assert fields1183 is not None
            unwrapped_fields1184 = fields1183
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1185 = unwrapped_fields1184[0]
            self.pretty_term(field1185)
            self.newline()
            field1186 = unwrapped_fields1184[1]
            self.pretty_term(field1186)
            self.newline()
            field1187 = unwrapped_fields1184[2]
            self.pretty_term(field1187)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1194 = self._try_flat(msg, self.pretty_minus)
        if flat1194 is not None:
            assert flat1194 is not None
            self.write(flat1194)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1708 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1708 = None
            fields1189 = _t1708
            assert fields1189 is not None
            unwrapped_fields1190 = fields1189
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1191 = unwrapped_fields1190[0]
            self.pretty_term(field1191)
            self.newline()
            field1192 = unwrapped_fields1190[1]
            self.pretty_term(field1192)
            self.newline()
            field1193 = unwrapped_fields1190[2]
            self.pretty_term(field1193)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1200 = self._try_flat(msg, self.pretty_multiply)
        if flat1200 is not None:
            assert flat1200 is not None
            self.write(flat1200)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1709 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1709 = None
            fields1195 = _t1709
            assert fields1195 is not None
            unwrapped_fields1196 = fields1195
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1197 = unwrapped_fields1196[0]
            self.pretty_term(field1197)
            self.newline()
            field1198 = unwrapped_fields1196[1]
            self.pretty_term(field1198)
            self.newline()
            field1199 = unwrapped_fields1196[2]
            self.pretty_term(field1199)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1206 = self._try_flat(msg, self.pretty_divide)
        if flat1206 is not None:
            assert flat1206 is not None
            self.write(flat1206)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1710 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1710 = None
            fields1201 = _t1710
            assert fields1201 is not None
            unwrapped_fields1202 = fields1201
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1203 = unwrapped_fields1202[0]
            self.pretty_term(field1203)
            self.newline()
            field1204 = unwrapped_fields1202[1]
            self.pretty_term(field1204)
            self.newline()
            field1205 = unwrapped_fields1202[2]
            self.pretty_term(field1205)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1211 = self._try_flat(msg, self.pretty_rel_term)
        if flat1211 is not None:
            assert flat1211 is not None
            self.write(flat1211)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1711 = _dollar_dollar.specialized_value
            else:
                _t1711 = None
            deconstruct_result1209 = _t1711
            if deconstruct_result1209 is not None:
                assert deconstruct_result1209 is not None
                unwrapped1210 = deconstruct_result1209
                self.pretty_specialized_value(unwrapped1210)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1712 = _dollar_dollar.term
                else:
                    _t1712 = None
                deconstruct_result1207 = _t1712
                if deconstruct_result1207 is not None:
                    assert deconstruct_result1207 is not None
                    unwrapped1208 = deconstruct_result1207
                    self.pretty_term(unwrapped1208)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1213 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1213 is not None:
            assert flat1213 is not None
            self.write(flat1213)
            return None
        else:
            fields1212 = msg
            self.write("#")
            self.pretty_raw_value(fields1212)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1220 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1220 is not None:
            assert flat1220 is not None
            self.write(flat1220)
            return None
        else:
            _dollar_dollar = msg
            fields1214 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1214 is not None
            unwrapped_fields1215 = fields1214
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1216 = unwrapped_fields1215[0]
            self.pretty_name(field1216)
            field1217 = unwrapped_fields1215[1]
            if not len(field1217) == 0:
                self.newline()
                for i1219, elem1218 in enumerate(field1217):
                    if (i1219 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1218)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1225 = self._try_flat(msg, self.pretty_cast)
        if flat1225 is not None:
            assert flat1225 is not None
            self.write(flat1225)
            return None
        else:
            _dollar_dollar = msg
            fields1221 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1221 is not None
            unwrapped_fields1222 = fields1221
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1223 = unwrapped_fields1222[0]
            self.pretty_term(field1223)
            self.newline()
            field1224 = unwrapped_fields1222[1]
            self.pretty_term(field1224)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1229 = self._try_flat(msg, self.pretty_attrs)
        if flat1229 is not None:
            assert flat1229 is not None
            self.write(flat1229)
            return None
        else:
            fields1226 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1226) == 0:
                self.newline()
                for i1228, elem1227 in enumerate(fields1226):
                    if (i1228 > 0):
                        self.newline()
                    self.pretty_attribute(elem1227)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1236 = self._try_flat(msg, self.pretty_attribute)
        if flat1236 is not None:
            assert flat1236 is not None
            self.write(flat1236)
            return None
        else:
            _dollar_dollar = msg
            fields1230 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1230 is not None
            unwrapped_fields1231 = fields1230
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1232 = unwrapped_fields1231[0]
            self.pretty_name(field1232)
            field1233 = unwrapped_fields1231[1]
            if not len(field1233) == 0:
                self.newline()
                for i1235, elem1234 in enumerate(field1233):
                    if (i1235 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1234)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1245 = self._try_flat(msg, self.pretty_algorithm)
        if flat1245 is not None:
            assert flat1245 is not None
            self.write(flat1245)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1713 = _dollar_dollar.attrs
            else:
                _t1713 = None
            fields1237 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body, _t1713,)
            assert fields1237 is not None
            unwrapped_fields1238 = fields1237
            self.write("(algorithm")
            self.indent_sexp()
            field1239 = unwrapped_fields1238[0]
            if not len(field1239) == 0:
                self.newline()
                for i1241, elem1240 in enumerate(field1239):
                    if (i1241 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1240)
            self.newline()
            field1242 = unwrapped_fields1238[1]
            self.pretty_script(field1242)
            field1243 = unwrapped_fields1238[2]
            if field1243 is not None:
                self.newline()
                assert field1243 is not None
                opt_val1244 = field1243
                self.pretty_attrs(opt_val1244)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1250 = self._try_flat(msg, self.pretty_script)
        if flat1250 is not None:
            assert flat1250 is not None
            self.write(flat1250)
            return None
        else:
            _dollar_dollar = msg
            fields1246 = _dollar_dollar.constructs
            assert fields1246 is not None
            unwrapped_fields1247 = fields1246
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1247) == 0:
                self.newline()
                for i1249, elem1248 in enumerate(unwrapped_fields1247):
                    if (i1249 > 0):
                        self.newline()
                    self.pretty_construct(elem1248)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1255 = self._try_flat(msg, self.pretty_construct)
        if flat1255 is not None:
            assert flat1255 is not None
            self.write(flat1255)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1714 = _dollar_dollar.loop
            else:
                _t1714 = None
            deconstruct_result1253 = _t1714
            if deconstruct_result1253 is not None:
                assert deconstruct_result1253 is not None
                unwrapped1254 = deconstruct_result1253
                self.pretty_loop(unwrapped1254)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1715 = _dollar_dollar.instruction
                else:
                    _t1715 = None
                deconstruct_result1251 = _t1715
                if deconstruct_result1251 is not None:
                    assert deconstruct_result1251 is not None
                    unwrapped1252 = deconstruct_result1251
                    self.pretty_instruction(unwrapped1252)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1262 = self._try_flat(msg, self.pretty_loop)
        if flat1262 is not None:
            assert flat1262 is not None
            self.write(flat1262)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1716 = _dollar_dollar.attrs
            else:
                _t1716 = None
            fields1256 = (_dollar_dollar.init, _dollar_dollar.body, _t1716,)
            assert fields1256 is not None
            unwrapped_fields1257 = fields1256
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1258 = unwrapped_fields1257[0]
            self.pretty_init(field1258)
            self.newline()
            field1259 = unwrapped_fields1257[1]
            self.pretty_script(field1259)
            field1260 = unwrapped_fields1257[2]
            if field1260 is not None:
                self.newline()
                assert field1260 is not None
                opt_val1261 = field1260
                self.pretty_attrs(opt_val1261)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1266 = self._try_flat(msg, self.pretty_init)
        if flat1266 is not None:
            assert flat1266 is not None
            self.write(flat1266)
            return None
        else:
            fields1263 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1263) == 0:
                self.newline()
                for i1265, elem1264 in enumerate(fields1263):
                    if (i1265 > 0):
                        self.newline()
                    self.pretty_instruction(elem1264)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1277 = self._try_flat(msg, self.pretty_instruction)
        if flat1277 is not None:
            assert flat1277 is not None
            self.write(flat1277)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1717 = _dollar_dollar.assign
            else:
                _t1717 = None
            deconstruct_result1275 = _t1717
            if deconstruct_result1275 is not None:
                assert deconstruct_result1275 is not None
                unwrapped1276 = deconstruct_result1275
                self.pretty_assign(unwrapped1276)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1718 = _dollar_dollar.upsert
                else:
                    _t1718 = None
                deconstruct_result1273 = _t1718
                if deconstruct_result1273 is not None:
                    assert deconstruct_result1273 is not None
                    unwrapped1274 = deconstruct_result1273
                    self.pretty_upsert(unwrapped1274)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1719 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1719 = None
                    deconstruct_result1271 = _t1719
                    if deconstruct_result1271 is not None:
                        assert deconstruct_result1271 is not None
                        unwrapped1272 = deconstruct_result1271
                        self.pretty_break(unwrapped1272)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1720 = _dollar_dollar.monoid_def
                        else:
                            _t1720 = None
                        deconstruct_result1269 = _t1720
                        if deconstruct_result1269 is not None:
                            assert deconstruct_result1269 is not None
                            unwrapped1270 = deconstruct_result1269
                            self.pretty_monoid_def(unwrapped1270)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1721 = _dollar_dollar.monus_def
                            else:
                                _t1721 = None
                            deconstruct_result1267 = _t1721
                            if deconstruct_result1267 is not None:
                                assert deconstruct_result1267 is not None
                                unwrapped1268 = deconstruct_result1267
                                self.pretty_monus_def(unwrapped1268)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1284 = self._try_flat(msg, self.pretty_assign)
        if flat1284 is not None:
            assert flat1284 is not None
            self.write(flat1284)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1722 = _dollar_dollar.attrs
            else:
                _t1722 = None
            fields1278 = (_dollar_dollar.name, _dollar_dollar.body, _t1722,)
            assert fields1278 is not None
            unwrapped_fields1279 = fields1278
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1280 = unwrapped_fields1279[0]
            self.pretty_relation_id(field1280)
            self.newline()
            field1281 = unwrapped_fields1279[1]
            self.pretty_abstraction(field1281)
            field1282 = unwrapped_fields1279[2]
            if field1282 is not None:
                self.newline()
                assert field1282 is not None
                opt_val1283 = field1282
                self.pretty_attrs(opt_val1283)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1291 = self._try_flat(msg, self.pretty_upsert)
        if flat1291 is not None:
            assert flat1291 is not None
            self.write(flat1291)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1723 = _dollar_dollar.attrs
            else:
                _t1723 = None
            fields1285 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1723,)
            assert fields1285 is not None
            unwrapped_fields1286 = fields1285
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1287 = unwrapped_fields1286[0]
            self.pretty_relation_id(field1287)
            self.newline()
            field1288 = unwrapped_fields1286[1]
            self.pretty_abstraction_with_arity(field1288)
            field1289 = unwrapped_fields1286[2]
            if field1289 is not None:
                self.newline()
                assert field1289 is not None
                opt_val1290 = field1289
                self.pretty_attrs(opt_val1290)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1296 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1296 is not None:
            assert flat1296 is not None
            self.write(flat1296)
            return None
        else:
            _dollar_dollar = msg
            _t1724 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1292 = (_t1724, _dollar_dollar[0].value,)
            assert fields1292 is not None
            unwrapped_fields1293 = fields1292
            self.write("(")
            self.indent()
            field1294 = unwrapped_fields1293[0]
            self.pretty_bindings(field1294)
            self.newline()
            field1295 = unwrapped_fields1293[1]
            self.pretty_formula(field1295)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1303 = self._try_flat(msg, self.pretty_break)
        if flat1303 is not None:
            assert flat1303 is not None
            self.write(flat1303)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1725 = _dollar_dollar.attrs
            else:
                _t1725 = None
            fields1297 = (_dollar_dollar.name, _dollar_dollar.body, _t1725,)
            assert fields1297 is not None
            unwrapped_fields1298 = fields1297
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1299 = unwrapped_fields1298[0]
            self.pretty_relation_id(field1299)
            self.newline()
            field1300 = unwrapped_fields1298[1]
            self.pretty_abstraction(field1300)
            field1301 = unwrapped_fields1298[2]
            if field1301 is not None:
                self.newline()
                assert field1301 is not None
                opt_val1302 = field1301
                self.pretty_attrs(opt_val1302)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1311 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1311 is not None:
            assert flat1311 is not None
            self.write(flat1311)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1726 = _dollar_dollar.attrs
            else:
                _t1726 = None
            fields1304 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1726,)
            assert fields1304 is not None
            unwrapped_fields1305 = fields1304
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1306 = unwrapped_fields1305[0]
            self.pretty_monoid(field1306)
            self.newline()
            field1307 = unwrapped_fields1305[1]
            self.pretty_relation_id(field1307)
            self.newline()
            field1308 = unwrapped_fields1305[2]
            self.pretty_abstraction_with_arity(field1308)
            field1309 = unwrapped_fields1305[3]
            if field1309 is not None:
                self.newline()
                assert field1309 is not None
                opt_val1310 = field1309
                self.pretty_attrs(opt_val1310)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1320 = self._try_flat(msg, self.pretty_monoid)
        if flat1320 is not None:
            assert flat1320 is not None
            self.write(flat1320)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1727 = _dollar_dollar.or_monoid
            else:
                _t1727 = None
            deconstruct_result1318 = _t1727
            if deconstruct_result1318 is not None:
                assert deconstruct_result1318 is not None
                unwrapped1319 = deconstruct_result1318
                self.pretty_or_monoid(unwrapped1319)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1728 = _dollar_dollar.min_monoid
                else:
                    _t1728 = None
                deconstruct_result1316 = _t1728
                if deconstruct_result1316 is not None:
                    assert deconstruct_result1316 is not None
                    unwrapped1317 = deconstruct_result1316
                    self.pretty_min_monoid(unwrapped1317)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1729 = _dollar_dollar.max_monoid
                    else:
                        _t1729 = None
                    deconstruct_result1314 = _t1729
                    if deconstruct_result1314 is not None:
                        assert deconstruct_result1314 is not None
                        unwrapped1315 = deconstruct_result1314
                        self.pretty_max_monoid(unwrapped1315)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1730 = _dollar_dollar.sum_monoid
                        else:
                            _t1730 = None
                        deconstruct_result1312 = _t1730
                        if deconstruct_result1312 is not None:
                            assert deconstruct_result1312 is not None
                            unwrapped1313 = deconstruct_result1312
                            self.pretty_sum_monoid(unwrapped1313)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1321 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1324 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1324 is not None:
            assert flat1324 is not None
            self.write(flat1324)
            return None
        else:
            _dollar_dollar = msg
            fields1322 = _dollar_dollar.type
            assert fields1322 is not None
            unwrapped_fields1323 = fields1322
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1323)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1327 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1327 is not None:
            assert flat1327 is not None
            self.write(flat1327)
            return None
        else:
            _dollar_dollar = msg
            fields1325 = _dollar_dollar.type
            assert fields1325 is not None
            unwrapped_fields1326 = fields1325
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1326)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1330 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1330 is not None:
            assert flat1330 is not None
            self.write(flat1330)
            return None
        else:
            _dollar_dollar = msg
            fields1328 = _dollar_dollar.type
            assert fields1328 is not None
            unwrapped_fields1329 = fields1328
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1329)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1338 = self._try_flat(msg, self.pretty_monus_def)
        if flat1338 is not None:
            assert flat1338 is not None
            self.write(flat1338)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1731 = _dollar_dollar.attrs
            else:
                _t1731 = None
            fields1331 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1731,)
            assert fields1331 is not None
            unwrapped_fields1332 = fields1331
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1333 = unwrapped_fields1332[0]
            self.pretty_monoid(field1333)
            self.newline()
            field1334 = unwrapped_fields1332[1]
            self.pretty_relation_id(field1334)
            self.newline()
            field1335 = unwrapped_fields1332[2]
            self.pretty_abstraction_with_arity(field1335)
            field1336 = unwrapped_fields1332[3]
            if field1336 is not None:
                self.newline()
                assert field1336 is not None
                opt_val1337 = field1336
                self.pretty_attrs(opt_val1337)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1345 = self._try_flat(msg, self.pretty_constraint)
        if flat1345 is not None:
            assert flat1345 is not None
            self.write(flat1345)
            return None
        else:
            _dollar_dollar = msg
            fields1339 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1339 is not None
            unwrapped_fields1340 = fields1339
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1341 = unwrapped_fields1340[0]
            self.pretty_relation_id(field1341)
            self.newline()
            field1342 = unwrapped_fields1340[1]
            self.pretty_abstraction(field1342)
            self.newline()
            field1343 = unwrapped_fields1340[2]
            self.pretty_functional_dependency_keys(field1343)
            self.newline()
            field1344 = unwrapped_fields1340[3]
            self.pretty_functional_dependency_values(field1344)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1349 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1349 is not None:
            assert flat1349 is not None
            self.write(flat1349)
            return None
        else:
            fields1346 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1346) == 0:
                self.newline()
                for i1348, elem1347 in enumerate(fields1346):
                    if (i1348 > 0):
                        self.newline()
                    self.pretty_var(elem1347)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1353 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1353 is not None:
            assert flat1353 is not None
            self.write(flat1353)
            return None
        else:
            fields1350 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1350) == 0:
                self.newline()
                for i1352, elem1351 in enumerate(fields1350):
                    if (i1352 > 0):
                        self.newline()
                    self.pretty_var(elem1351)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1362 = self._try_flat(msg, self.pretty_data)
        if flat1362 is not None:
            assert flat1362 is not None
            self.write(flat1362)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1732 = _dollar_dollar.edb
            else:
                _t1732 = None
            deconstruct_result1360 = _t1732
            if deconstruct_result1360 is not None:
                assert deconstruct_result1360 is not None
                unwrapped1361 = deconstruct_result1360
                self.pretty_edb(unwrapped1361)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1733 = _dollar_dollar.betree_relation
                else:
                    _t1733 = None
                deconstruct_result1358 = _t1733
                if deconstruct_result1358 is not None:
                    assert deconstruct_result1358 is not None
                    unwrapped1359 = deconstruct_result1358
                    self.pretty_betree_relation(unwrapped1359)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1734 = _dollar_dollar.csv_data
                    else:
                        _t1734 = None
                    deconstruct_result1356 = _t1734
                    if deconstruct_result1356 is not None:
                        assert deconstruct_result1356 is not None
                        unwrapped1357 = deconstruct_result1356
                        self.pretty_csv_data(unwrapped1357)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1735 = _dollar_dollar.iceberg_data
                        else:
                            _t1735 = None
                        deconstruct_result1354 = _t1735
                        if deconstruct_result1354 is not None:
                            assert deconstruct_result1354 is not None
                            unwrapped1355 = deconstruct_result1354
                            self.pretty_iceberg_data(unwrapped1355)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1368 = self._try_flat(msg, self.pretty_edb)
        if flat1368 is not None:
            assert flat1368 is not None
            self.write(flat1368)
            return None
        else:
            _dollar_dollar = msg
            fields1363 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1363 is not None
            unwrapped_fields1364 = fields1363
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1365 = unwrapped_fields1364[0]
            self.pretty_relation_id(field1365)
            self.newline()
            field1366 = unwrapped_fields1364[1]
            self.pretty_edb_path(field1366)
            self.newline()
            field1367 = unwrapped_fields1364[2]
            self.pretty_edb_types(field1367)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1372 = self._try_flat(msg, self.pretty_edb_path)
        if flat1372 is not None:
            assert flat1372 is not None
            self.write(flat1372)
            return None
        else:
            fields1369 = msg
            self.write("[")
            self.indent()
            for i1371, elem1370 in enumerate(fields1369):
                if (i1371 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1370))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1376 = self._try_flat(msg, self.pretty_edb_types)
        if flat1376 is not None:
            assert flat1376 is not None
            self.write(flat1376)
            return None
        else:
            fields1373 = msg
            self.write("[")
            self.indent()
            for i1375, elem1374 in enumerate(fields1373):
                if (i1375 > 0):
                    self.newline()
                self.pretty_type(elem1374)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1381 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1381 is not None:
            assert flat1381 is not None
            self.write(flat1381)
            return None
        else:
            _dollar_dollar = msg
            fields1377 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1377 is not None
            unwrapped_fields1378 = fields1377
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1379 = unwrapped_fields1378[0]
            self.pretty_relation_id(field1379)
            self.newline()
            field1380 = unwrapped_fields1378[1]
            self.pretty_betree_info(field1380)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1387 = self._try_flat(msg, self.pretty_betree_info)
        if flat1387 is not None:
            assert flat1387 is not None
            self.write(flat1387)
            return None
        else:
            _dollar_dollar = msg
            _t1736 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1382 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1736,)
            assert fields1382 is not None
            unwrapped_fields1383 = fields1382
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1384 = unwrapped_fields1383[0]
            self.pretty_betree_info_key_types(field1384)
            self.newline()
            field1385 = unwrapped_fields1383[1]
            self.pretty_betree_info_value_types(field1385)
            self.newline()
            field1386 = unwrapped_fields1383[2]
            self.pretty_config_dict(field1386)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1391 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1391 is not None:
            assert flat1391 is not None
            self.write(flat1391)
            return None
        else:
            fields1388 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1388) == 0:
                self.newline()
                for i1390, elem1389 in enumerate(fields1388):
                    if (i1390 > 0):
                        self.newline()
                    self.pretty_type(elem1389)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1395 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1395 is not None:
            assert flat1395 is not None
            self.write(flat1395)
            return None
        else:
            fields1392 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1392) == 0:
                self.newline()
                for i1394, elem1393 in enumerate(fields1392):
                    if (i1394 > 0):
                        self.newline()
                    self.pretty_type(elem1393)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1402 = self._try_flat(msg, self.pretty_csv_data)
        if flat1402 is not None:
            assert flat1402 is not None
            self.write(flat1402)
            return None
        else:
            _dollar_dollar = msg
            fields1396 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1396 is not None
            unwrapped_fields1397 = fields1396
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1398 = unwrapped_fields1397[0]
            self.pretty_csvlocator(field1398)
            self.newline()
            field1399 = unwrapped_fields1397[1]
            self.pretty_csv_config(field1399)
            self.newline()
            field1400 = unwrapped_fields1397[2]
            self.pretty_gnf_columns(field1400)
            self.newline()
            field1401 = unwrapped_fields1397[3]
            self.pretty_csv_asof(field1401)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1409 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1409 is not None:
            assert flat1409 is not None
            self.write(flat1409)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1737 = _dollar_dollar.paths
            else:
                _t1737 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1738 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1738 = None
            fields1403 = (_t1737, _t1738,)
            assert fields1403 is not None
            unwrapped_fields1404 = fields1403
            self.write("(csv_locator")
            self.indent_sexp()
            field1405 = unwrapped_fields1404[0]
            if field1405 is not None:
                self.newline()
                assert field1405 is not None
                opt_val1406 = field1405
                self.pretty_csv_locator_paths(opt_val1406)
            field1407 = unwrapped_fields1404[1]
            if field1407 is not None:
                self.newline()
                assert field1407 is not None
                opt_val1408 = field1407
                self.pretty_csv_locator_inline_data(opt_val1408)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1413 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1413 is not None:
            assert flat1413 is not None
            self.write(flat1413)
            return None
        else:
            fields1410 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1410) == 0:
                self.newline()
                for i1412, elem1411 in enumerate(fields1410):
                    if (i1412 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1411))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1415 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1415 is not None:
            assert flat1415 is not None
            self.write(flat1415)
            return None
        else:
            fields1414 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1414))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1421 = self._try_flat(msg, self.pretty_csv_config)
        if flat1421 is not None:
            assert flat1421 is not None
            self.write(flat1421)
            return None
        else:
            _dollar_dollar = msg
            _t1739 = self.deconstruct_csv_config(_dollar_dollar)
            _t1740 = self.deconstruct_csv_storage_integration_optional(_dollar_dollar)
            fields1416 = (_t1739, _t1740,)
            assert fields1416 is not None
            unwrapped_fields1417 = fields1416
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            field1418 = unwrapped_fields1417[0]
            self.pretty_config_dict(field1418)
            field1419 = unwrapped_fields1417[1]
            if field1419 is not None:
                self.newline()
                assert field1419 is not None
                opt_val1420 = field1419
                self.pretty__storage_integration(opt_val1420)
            self.dedent()
            self.write(")")

    def pretty__storage_integration(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat1423 = self._try_flat(msg, self.pretty__storage_integration)
        if flat1423 is not None:
            assert flat1423 is not None
            self.write(flat1423)
            return None
        else:
            fields1422 = msg
            self.write("(storage_integration")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(fields1422)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1427 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1427 is not None:
            assert flat1427 is not None
            self.write(flat1427)
            return None
        else:
            fields1424 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1424) == 0:
                self.newline()
                for i1426, elem1425 in enumerate(fields1424):
                    if (i1426 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1425)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1436 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1436 is not None:
            assert flat1436 is not None
            self.write(flat1436)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1741 = _dollar_dollar.target_id
            else:
                _t1741 = None
            fields1428 = (_dollar_dollar.column_path, _t1741, _dollar_dollar.types,)
            assert fields1428 is not None
            unwrapped_fields1429 = fields1428
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1430 = unwrapped_fields1429[0]
            self.pretty_gnf_column_path(field1430)
            field1431 = unwrapped_fields1429[1]
            if field1431 is not None:
                self.newline()
                assert field1431 is not None
                opt_val1432 = field1431
                self.pretty_relation_id(opt_val1432)
            self.newline()
            self.write("[")
            field1433 = unwrapped_fields1429[2]
            for i1435, elem1434 in enumerate(field1433):
                if (i1435 > 0):
                    self.newline()
                self.pretty_type(elem1434)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1443 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1443 is not None:
            assert flat1443 is not None
            self.write(flat1443)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1742 = _dollar_dollar[0]
            else:
                _t1742 = None
            deconstruct_result1441 = _t1742
            if deconstruct_result1441 is not None:
                assert deconstruct_result1441 is not None
                unwrapped1442 = deconstruct_result1441
                self.write(self.format_string_value(unwrapped1442))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1743 = _dollar_dollar
                else:
                    _t1743 = None
                deconstruct_result1437 = _t1743
                if deconstruct_result1437 is not None:
                    assert deconstruct_result1437 is not None
                    unwrapped1438 = deconstruct_result1437
                    self.write("[")
                    self.indent()
                    for i1440, elem1439 in enumerate(unwrapped1438):
                        if (i1440 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1439))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1445 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1445 is not None:
            assert flat1445 is not None
            self.write(flat1445)
            return None
        else:
            fields1444 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1444))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1456 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1456 is not None:
            assert flat1456 is not None
            self.write(flat1456)
            return None
        else:
            _dollar_dollar = msg
            _t1744 = self.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
            _t1745 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1446 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1744, _t1745, _dollar_dollar.returns_delta,)
            assert fields1446 is not None
            unwrapped_fields1447 = fields1446
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1448 = unwrapped_fields1447[0]
            self.pretty_iceberg_locator(field1448)
            self.newline()
            field1449 = unwrapped_fields1447[1]
            self.pretty_iceberg_catalog_config(field1449)
            self.newline()
            field1450 = unwrapped_fields1447[2]
            self.pretty_gnf_columns(field1450)
            field1451 = unwrapped_fields1447[3]
            if field1451 is not None:
                self.newline()
                assert field1451 is not None
                opt_val1452 = field1451
                self.pretty_iceberg_from_snapshot(opt_val1452)
            field1453 = unwrapped_fields1447[4]
            if field1453 is not None:
                self.newline()
                assert field1453 is not None
                opt_val1454 = field1453
                self.pretty_iceberg_to_snapshot(opt_val1454)
            self.newline()
            field1455 = unwrapped_fields1447[5]
            self.pretty_boolean_value(field1455)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1462 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1462 is not None:
            assert flat1462 is not None
            self.write(flat1462)
            return None
        else:
            _dollar_dollar = msg
            fields1457 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1457 is not None
            unwrapped_fields1458 = fields1457
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            field1459 = unwrapped_fields1458[0]
            self.pretty_iceberg_locator_table_name(field1459)
            self.newline()
            field1460 = unwrapped_fields1458[1]
            self.pretty_iceberg_locator_namespace(field1460)
            self.newline()
            field1461 = unwrapped_fields1458[2]
            self.pretty_iceberg_locator_warehouse(field1461)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_table_name(self, msg: str):
        flat1464 = self._try_flat(msg, self.pretty_iceberg_locator_table_name)
        if flat1464 is not None:
            assert flat1464 is not None
            self.write(flat1464)
            return None
        else:
            fields1463 = msg
            self.write("(table_name")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1463))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_namespace(self, msg: Sequence[str]):
        flat1468 = self._try_flat(msg, self.pretty_iceberg_locator_namespace)
        if flat1468 is not None:
            assert flat1468 is not None
            self.write(flat1468)
            return None
        else:
            fields1465 = msg
            self.write("(namespace")
            self.indent_sexp()
            if not len(fields1465) == 0:
                self.newline()
                for i1467, elem1466 in enumerate(fields1465):
                    if (i1467 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1466))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_warehouse(self, msg: str):
        flat1470 = self._try_flat(msg, self.pretty_iceberg_locator_warehouse)
        if flat1470 is not None:
            assert flat1470 is not None
            self.write(flat1470)
            return None
        else:
            fields1469 = msg
            self.write("(warehouse")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1469))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1478 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1478 is not None:
            assert flat1478 is not None
            self.write(flat1478)
            return None
        else:
            _dollar_dollar = msg
            _t1746 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1471 = (_dollar_dollar.catalog_uri, _t1746, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1471 is not None
            unwrapped_fields1472 = fields1471
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            field1473 = unwrapped_fields1472[0]
            self.pretty_iceberg_catalog_uri(field1473)
            field1474 = unwrapped_fields1472[1]
            if field1474 is not None:
                self.newline()
                assert field1474 is not None
                opt_val1475 = field1474
                self.pretty_iceberg_catalog_config_scope(opt_val1475)
            self.newline()
            field1476 = unwrapped_fields1472[2]
            self.pretty_iceberg_properties(field1476)
            self.newline()
            field1477 = unwrapped_fields1472[3]
            self.pretty_iceberg_auth_properties(field1477)
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_uri(self, msg: str):
        flat1480 = self._try_flat(msg, self.pretty_iceberg_catalog_uri)
        if flat1480 is not None:
            assert flat1480 is not None
            self.write(flat1480)
            return None
        else:
            fields1479 = msg
            self.write("(catalog_uri")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1479))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1482 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1482 is not None:
            assert flat1482 is not None
            self.write(flat1482)
            return None
        else:
            fields1481 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1481))
            self.dedent()
            self.write(")")

    def pretty_iceberg_properties(self, msg: Sequence[tuple[str, str]]):
        flat1486 = self._try_flat(msg, self.pretty_iceberg_properties)
        if flat1486 is not None:
            assert flat1486 is not None
            self.write(flat1486)
            return None
        else:
            fields1483 = msg
            self.write("(properties")
            self.indent_sexp()
            if not len(fields1483) == 0:
                self.newline()
                for i1485, elem1484 in enumerate(fields1483):
                    if (i1485 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1484)
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1491 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1491 is not None:
            assert flat1491 is not None
            self.write(flat1491)
            return None
        else:
            _dollar_dollar = msg
            fields1487 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1487 is not None
            unwrapped_fields1488 = fields1487
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1489 = unwrapped_fields1488[0]
            self.write(self.format_string_value(field1489))
            self.newline()
            field1490 = unwrapped_fields1488[1]
            self.write(self.format_string_value(field1490))
            self.dedent()
            self.write(")")

    def pretty_iceberg_auth_properties(self, msg: Sequence[tuple[str, str]]):
        flat1495 = self._try_flat(msg, self.pretty_iceberg_auth_properties)
        if flat1495 is not None:
            assert flat1495 is not None
            self.write(flat1495)
            return None
        else:
            fields1492 = msg
            self.write("(auth_properties")
            self.indent_sexp()
            if not len(fields1492) == 0:
                self.newline()
                for i1494, elem1493 in enumerate(fields1492):
                    if (i1494 > 0):
                        self.newline()
                    self.pretty_iceberg_masked_property_entry(elem1493)
            self.dedent()
            self.write(")")

    def pretty_iceberg_masked_property_entry(self, msg: tuple[str, str]):
        flat1500 = self._try_flat(msg, self.pretty_iceberg_masked_property_entry)
        if flat1500 is not None:
            assert flat1500 is not None
            self.write(flat1500)
            return None
        else:
            _dollar_dollar = msg
            _t1747 = self.mask_secret_value(_dollar_dollar)
            fields1496 = (_dollar_dollar[0], _t1747,)
            assert fields1496 is not None
            unwrapped_fields1497 = fields1496
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1498 = unwrapped_fields1497[0]
            self.write(self.format_string_value(field1498))
            self.newline()
            field1499 = unwrapped_fields1497[1]
            self.write(self.format_string_value(field1499))
            self.dedent()
            self.write(")")

    def pretty_iceberg_from_snapshot(self, msg: str):
        flat1502 = self._try_flat(msg, self.pretty_iceberg_from_snapshot)
        if flat1502 is not None:
            assert flat1502 is not None
            self.write(flat1502)
            return None
        else:
            fields1501 = msg
            self.write("(from_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1501))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1504 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1504 is not None:
            assert flat1504 is not None
            self.write(flat1504)
            return None
        else:
            fields1503 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1503))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1507 = self._try_flat(msg, self.pretty_undefine)
        if flat1507 is not None:
            assert flat1507 is not None
            self.write(flat1507)
            return None
        else:
            _dollar_dollar = msg
            fields1505 = _dollar_dollar.fragment_id
            assert fields1505 is not None
            unwrapped_fields1506 = fields1505
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1506)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1512 = self._try_flat(msg, self.pretty_context)
        if flat1512 is not None:
            assert flat1512 is not None
            self.write(flat1512)
            return None
        else:
            _dollar_dollar = msg
            fields1508 = _dollar_dollar.relations
            assert fields1508 is not None
            unwrapped_fields1509 = fields1508
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1509) == 0:
                self.newline()
                for i1511, elem1510 in enumerate(unwrapped_fields1509):
                    if (i1511 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1510)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1519 = self._try_flat(msg, self.pretty_snapshot)
        if flat1519 is not None:
            assert flat1519 is not None
            self.write(flat1519)
            return None
        else:
            _dollar_dollar = msg
            fields1513 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
            assert fields1513 is not None
            unwrapped_fields1514 = fields1513
            self.write("(snapshot")
            self.indent_sexp()
            self.newline()
            field1515 = unwrapped_fields1514[0]
            self.pretty_edb_path(field1515)
            field1516 = unwrapped_fields1514[1]
            if not len(field1516) == 0:
                self.newline()
                for i1518, elem1517 in enumerate(field1516):
                    if (i1518 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1517)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1524 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1524 is not None:
            assert flat1524 is not None
            self.write(flat1524)
            return None
        else:
            _dollar_dollar = msg
            fields1520 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1520 is not None
            unwrapped_fields1521 = fields1520
            field1522 = unwrapped_fields1521[0]
            self.pretty_edb_path(field1522)
            self.write(" ")
            field1523 = unwrapped_fields1521[1]
            self.pretty_relation_id(field1523)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1528 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1528 is not None:
            assert flat1528 is not None
            self.write(flat1528)
            return None
        else:
            fields1525 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1525) == 0:
                self.newline()
                for i1527, elem1526 in enumerate(fields1525):
                    if (i1527 > 0):
                        self.newline()
                    self.pretty_read(elem1526)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1541 = self._try_flat(msg, self.pretty_read)
        if flat1541 is not None:
            assert flat1541 is not None
            self.write(flat1541)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1748 = _dollar_dollar.demand
            else:
                _t1748 = None
            deconstruct_result1539 = _t1748
            if deconstruct_result1539 is not None:
                assert deconstruct_result1539 is not None
                unwrapped1540 = deconstruct_result1539
                self.pretty_demand(unwrapped1540)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1749 = _dollar_dollar.output
                else:
                    _t1749 = None
                deconstruct_result1537 = _t1749
                if deconstruct_result1537 is not None:
                    assert deconstruct_result1537 is not None
                    unwrapped1538 = deconstruct_result1537
                    self.pretty_output(unwrapped1538)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1750 = _dollar_dollar.what_if
                    else:
                        _t1750 = None
                    deconstruct_result1535 = _t1750
                    if deconstruct_result1535 is not None:
                        assert deconstruct_result1535 is not None
                        unwrapped1536 = deconstruct_result1535
                        self.pretty_what_if(unwrapped1536)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1751 = _dollar_dollar.abort
                        else:
                            _t1751 = None
                        deconstruct_result1533 = _t1751
                        if deconstruct_result1533 is not None:
                            assert deconstruct_result1533 is not None
                            unwrapped1534 = deconstruct_result1533
                            self.pretty_abort(unwrapped1534)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1752 = _dollar_dollar.export
                            else:
                                _t1752 = None
                            deconstruct_result1531 = _t1752
                            if deconstruct_result1531 is not None:
                                assert deconstruct_result1531 is not None
                                unwrapped1532 = deconstruct_result1531
                                self.pretty_export(unwrapped1532)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("export_output"):
                                    _t1753 = _dollar_dollar.export_output
                                else:
                                    _t1753 = None
                                deconstruct_result1529 = _t1753
                                if deconstruct_result1529 is not None:
                                    assert deconstruct_result1529 is not None
                                    unwrapped1530 = deconstruct_result1529
                                    self.pretty_export_output(unwrapped1530)
                                else:
                                    raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1544 = self._try_flat(msg, self.pretty_demand)
        if flat1544 is not None:
            assert flat1544 is not None
            self.write(flat1544)
            return None
        else:
            _dollar_dollar = msg
            fields1542 = _dollar_dollar.relation_id
            assert fields1542 is not None
            unwrapped_fields1543 = fields1542
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1543)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1549 = self._try_flat(msg, self.pretty_output)
        if flat1549 is not None:
            assert flat1549 is not None
            self.write(flat1549)
            return None
        else:
            _dollar_dollar = msg
            fields1545 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1545 is not None
            unwrapped_fields1546 = fields1545
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1547 = unwrapped_fields1546[0]
            self.pretty_name(field1547)
            self.newline()
            field1548 = unwrapped_fields1546[1]
            self.pretty_relation_id(field1548)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1554 = self._try_flat(msg, self.pretty_what_if)
        if flat1554 is not None:
            assert flat1554 is not None
            self.write(flat1554)
            return None
        else:
            _dollar_dollar = msg
            fields1550 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1550 is not None
            unwrapped_fields1551 = fields1550
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1552 = unwrapped_fields1551[0]
            self.pretty_name(field1552)
            self.newline()
            field1553 = unwrapped_fields1551[1]
            self.pretty_epoch(field1553)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1560 = self._try_flat(msg, self.pretty_abort)
        if flat1560 is not None:
            assert flat1560 is not None
            self.write(flat1560)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1754 = _dollar_dollar.name
            else:
                _t1754 = None
            fields1555 = (_t1754, _dollar_dollar.relation_id,)
            assert fields1555 is not None
            unwrapped_fields1556 = fields1555
            self.write("(abort")
            self.indent_sexp()
            field1557 = unwrapped_fields1556[0]
            if field1557 is not None:
                self.newline()
                assert field1557 is not None
                opt_val1558 = field1557
                self.pretty_name(opt_val1558)
            self.newline()
            field1559 = unwrapped_fields1556[1]
            self.pretty_relation_id(field1559)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1565 = self._try_flat(msg, self.pretty_export)
        if flat1565 is not None:
            assert flat1565 is not None
            self.write(flat1565)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1755 = _dollar_dollar.csv_config
            else:
                _t1755 = None
            deconstruct_result1563 = _t1755
            if deconstruct_result1563 is not None:
                assert deconstruct_result1563 is not None
                unwrapped1564 = deconstruct_result1563
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1564)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1756 = _dollar_dollar.iceberg_config
                else:
                    _t1756 = None
                deconstruct_result1561 = _t1756
                if deconstruct_result1561 is not None:
                    assert deconstruct_result1561 is not None
                    unwrapped1562 = deconstruct_result1561
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1562)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1576 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1576 is not None:
            assert flat1576 is not None
            self.write(flat1576)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1757 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1757 = None
            deconstruct_result1571 = _t1757
            if deconstruct_result1571 is not None:
                assert deconstruct_result1571 is not None
                unwrapped1572 = deconstruct_result1571
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1573 = unwrapped1572[0]
                self.pretty_export_csv_path(field1573)
                self.newline()
                field1574 = unwrapped1572[1]
                self.pretty_export_csv_source(field1574)
                self.newline()
                field1575 = unwrapped1572[2]
                self.pretty_csv_config(field1575)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1759 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1758 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1759,)
                else:
                    _t1758 = None
                deconstruct_result1566 = _t1758
                if deconstruct_result1566 is not None:
                    assert deconstruct_result1566 is not None
                    unwrapped1567 = deconstruct_result1566
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1568 = unwrapped1567[0]
                    self.pretty_export_csv_path(field1568)
                    self.newline()
                    field1569 = unwrapped1567[1]
                    self.pretty_export_csv_columns_list(field1569)
                    self.newline()
                    field1570 = unwrapped1567[2]
                    self.pretty_config_dict(field1570)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1578 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1578 is not None:
            assert flat1578 is not None
            self.write(flat1578)
            return None
        else:
            fields1577 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1577))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1585 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1585 is not None:
            assert flat1585 is not None
            self.write(flat1585)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1760 = _dollar_dollar.gnf_columns.columns
            else:
                _t1760 = None
            deconstruct_result1581 = _t1760
            if deconstruct_result1581 is not None:
                assert deconstruct_result1581 is not None
                unwrapped1582 = deconstruct_result1581
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1582) == 0:
                    self.newline()
                    for i1584, elem1583 in enumerate(unwrapped1582):
                        if (i1584 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1583)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1761 = _dollar_dollar.table_def
                else:
                    _t1761 = None
                deconstruct_result1579 = _t1761
                if deconstruct_result1579 is not None:
                    assert deconstruct_result1579 is not None
                    unwrapped1580 = deconstruct_result1579
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1580)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1590 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1590 is not None:
            assert flat1590 is not None
            self.write(flat1590)
            return None
        else:
            _dollar_dollar = msg
            fields1586 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1586 is not None
            unwrapped_fields1587 = fields1586
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1588 = unwrapped_fields1587[0]
            self.write(self.format_string_value(field1588))
            self.newline()
            field1589 = unwrapped_fields1587[1]
            self.pretty_relation_id(field1589)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1594 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1594 is not None:
            assert flat1594 is not None
            self.write(flat1594)
            return None
        else:
            fields1591 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1591) == 0:
                self.newline()
                for i1593, elem1592 in enumerate(fields1591):
                    if (i1593 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1592)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1603 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1603 is not None:
            assert flat1603 is not None
            self.write(flat1603)
            return None
        else:
            _dollar_dollar = msg
            _t1762 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1595 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sorted(_dollar_dollar.table_properties.items()), _t1762,)
            assert fields1595 is not None
            unwrapped_fields1596 = fields1595
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1597 = unwrapped_fields1596[0]
            self.pretty_iceberg_locator(field1597)
            self.newline()
            field1598 = unwrapped_fields1596[1]
            self.pretty_iceberg_catalog_config(field1598)
            self.newline()
            field1599 = unwrapped_fields1596[2]
            self.pretty_export_iceberg_table_def(field1599)
            self.newline()
            field1600 = unwrapped_fields1596[3]
            self.pretty_iceberg_table_properties(field1600)
            field1601 = unwrapped_fields1596[4]
            if field1601 is not None:
                self.newline()
                assert field1601 is not None
                opt_val1602 = field1601
                self.pretty_config_dict(opt_val1602)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_table_def(self, msg: logic_pb2.RelationId):
        flat1605 = self._try_flat(msg, self.pretty_export_iceberg_table_def)
        if flat1605 is not None:
            assert flat1605 is not None
            self.write(flat1605)
            return None
        else:
            fields1604 = msg
            self.write("(table_def")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1604)
            self.dedent()
            self.write(")")

    def pretty_iceberg_table_properties(self, msg: Sequence[tuple[str, str]]):
        flat1609 = self._try_flat(msg, self.pretty_iceberg_table_properties)
        if flat1609 is not None:
            assert flat1609 is not None
            self.write(flat1609)
            return None
        else:
            fields1606 = msg
            self.write("(table_properties")
            self.indent_sexp()
            if not len(fields1606) == 0:
                self.newline()
                for i1608, elem1607 in enumerate(fields1606):
                    if (i1608 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1607)
            self.dedent()
            self.write(")")

    def pretty_export_output(self, msg: transactions_pb2.ExportOutput):
        flat1612 = self._try_flat(msg, self.pretty_export_output)
        if flat1612 is not None:
            assert flat1612 is not None
            self.write(flat1612)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv"):
                _t1763 = _dollar_dollar.csv
            else:
                _t1763 = None
            fields1610 = _t1763
            assert fields1610 is not None
            unwrapped_fields1611 = fields1610
            self.write("(output_export")
            self.indent_sexp()
            self.newline()
            self.pretty_export_csv_output(unwrapped_fields1611)
            self.dedent()
            self.write(")")

    def pretty_export_csv_output(self, msg: transactions_pb2.ExportCSVOutput):
        flat1617 = self._try_flat(msg, self.pretty_export_csv_output)
        if flat1617 is not None:
            assert flat1617 is not None
            self.write(flat1617)
            return None
        else:
            _dollar_dollar = msg
            fields1613 = (_dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            assert fields1613 is not None
            unwrapped_fields1614 = fields1613
            self.write("(csv")
            self.indent_sexp()
            self.newline()
            field1615 = unwrapped_fields1614[0]
            self.pretty_export_csv_source(field1615)
            self.newline()
            field1616 = unwrapped_fields1614[1]
            self.pretty_csv_config(field1616)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1815 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1815)
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

    def pretty_storage_integration(self, msg: logic_pb2.StorageIntegration):
        self.write("(storage_integration")
        self.indent_sexp()
        self.newline()
        self.write(":provider ")
        self.write(self.format_string_value(msg.provider))
        self.newline()
        self.write(":azure_sas_token ")
        self.write(self.format_string_value(msg.azure_sas_token))
        self.newline()
        self.write(":s3_region ")
        self.write(self.format_string_value(msg.s3_region))
        self.newline()
        self.write(":s3_access_key_id ")
        self.write(self.format_string_value(msg.s3_access_key_id))
        self.newline()
        self.write(":s3_secret_access_key ")
        self.write(self.format_string_value(msg.s3_secret_access_key))
        self.write(")")
        self.dedent()

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
        elif isinstance(msg, transactions_pb2.ExportOutput):
            self.pretty_export_output(msg)
        elif isinstance(msg, transactions_pb2.ExportCSVOutput):
            self.pretty_export_csv_output(msg)
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
        elif isinstance(msg, logic_pb2.StorageIntegration):
            self.pretty_storage_integration(msg)
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
