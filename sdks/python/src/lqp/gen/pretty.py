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
        _t1768 = logic_pb2.Value(int32_value=v)
        return _t1768

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1769 = logic_pb2.Value(int_value=v)
        return _t1769

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1770 = logic_pb2.Value(float_value=v)
        return _t1770

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1771 = logic_pb2.Value(string_value=v)
        return _t1771

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1772 = logic_pb2.Value(boolean_value=v)
        return _t1772

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1773 = logic_pb2.Value(uint128_value=v)
        return _t1773

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1774 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1774,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1775 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1775,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1776 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1776,))
        _t1777 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1777,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1778 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1778,))
        _t1779 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1779,))
        if msg.new_line != "":
            _t1780 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1780,))
        _t1781 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1781,))
        _t1782 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1782,))
        _t1783 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1783,))
        if msg.comment != "":
            _t1784 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1784,))
        for missing_string in msg.missing_strings:
            _t1785 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1785,))
        _t1786 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1786,))
        _t1787 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1787,))
        _t1788 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1788,))
        if msg.partition_size_mb != 0:
            _t1789 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1789,))
        return sorted(result)

    def deconstruct_csv_storage_integration_optional(self, msg: logic_pb2.CSVConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        if not msg.HasField("storage_integration"):
            return None
        else:
            _t1790 = None
        assert msg.storage_integration is not None
        si = msg.storage_integration
        result = []
        if si.provider != "":
            _t1791 = self._make_value_string(si.provider)
            result.append(("provider", _t1791,))
        if si.azure_sas_token != "":
            _t1792 = self._make_value_string("***")
            result.append(("azure_sas_token", _t1792,))
        if si.s3_region != "":
            _t1793 = self._make_value_string(si.s3_region)
            result.append(("s3_region", _t1793,))
        if si.s3_access_key_id != "":
            _t1794 = self._make_value_string("***")
            result.append(("s3_access_key_id", _t1794,))
        if si.s3_secret_access_key != "":
            _t1795 = self._make_value_string("***")
            result.append(("s3_secret_access_key", _t1795,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1796 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1796,))
        _t1797 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1797,))
        _t1798 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1798,))
        _t1799 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1799,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1800 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1800,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1801 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1801,))
        _t1802 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1802,))
        _t1803 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1803,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1804 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1804,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1805 = self._make_value_string(msg.compression)
            result.append(("compression", _t1805,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1806 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1806,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1807 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1807,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1808 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1808,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1809 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1809,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1810 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1810,))
        return sorted(result)

    def mask_secret_value(self, pair: tuple[str, str]) -> str:
        return "***"

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1811 = None
        return None

    def deconstruct_iceberg_data_from_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.from_snapshot is not None
        if msg.from_snapshot != "":
            assert msg.from_snapshot is not None
            return msg.from_snapshot
        else:
            _t1812 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1813 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1814 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1814,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1815 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1815,))
        if msg.compression != "":
            _t1816 = self._make_value_string(msg.compression)
            result.append(("compression", _t1816,))
        if len(result) == 0:
            return None
        else:
            _t1817 = None
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
            _t1818 = None
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
        flat820 = self._try_flat(msg, self.pretty_transaction)
        if flat820 is not None:
            assert flat820 is not None
            self.write(flat820)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1622 = _dollar_dollar.configure
            else:
                _t1622 = None
            if _dollar_dollar.HasField("sync"):
                _t1623 = _dollar_dollar.sync
            else:
                _t1623 = None
            fields811 = (_t1622, _t1623, _dollar_dollar.epochs,)
            assert fields811 is not None
            unwrapped_fields812 = fields811
            self.write("(transaction")
            self.indent_sexp()
            field813 = unwrapped_fields812[0]
            if field813 is not None:
                self.newline()
                assert field813 is not None
                opt_val814 = field813
                self.pretty_configure(opt_val814)
            field815 = unwrapped_fields812[1]
            if field815 is not None:
                self.newline()
                assert field815 is not None
                opt_val816 = field815
                self.pretty_sync(opt_val816)
            field817 = unwrapped_fields812[2]
            if not len(field817) == 0:
                self.newline()
                for i819, elem818 in enumerate(field817):
                    if (i819 > 0):
                        self.newline()
                    self.pretty_epoch(elem818)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat823 = self._try_flat(msg, self.pretty_configure)
        if flat823 is not None:
            assert flat823 is not None
            self.write(flat823)
            return None
        else:
            _dollar_dollar = msg
            _t1624 = self.deconstruct_configure(_dollar_dollar)
            fields821 = _t1624
            assert fields821 is not None
            unwrapped_fields822 = fields821
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields822)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat827 = self._try_flat(msg, self.pretty_config_dict)
        if flat827 is not None:
            assert flat827 is not None
            self.write(flat827)
            return None
        else:
            fields824 = msg
            self.write("{")
            self.indent()
            if not len(fields824) == 0:
                self.newline()
                for i826, elem825 in enumerate(fields824):
                    if (i826 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem825)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat832 = self._try_flat(msg, self.pretty_config_key_value)
        if flat832 is not None:
            assert flat832 is not None
            self.write(flat832)
            return None
        else:
            _dollar_dollar = msg
            fields828 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields828 is not None
            unwrapped_fields829 = fields828
            self.write(":")
            field830 = unwrapped_fields829[0]
            self.write(field830)
            self.write(" ")
            field831 = unwrapped_fields829[1]
            self.pretty_raw_value(field831)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat858 = self._try_flat(msg, self.pretty_raw_value)
        if flat858 is not None:
            assert flat858 is not None
            self.write(flat858)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1625 = _dollar_dollar.date_value
            else:
                _t1625 = None
            deconstruct_result856 = _t1625
            if deconstruct_result856 is not None:
                assert deconstruct_result856 is not None
                unwrapped857 = deconstruct_result856
                self.pretty_raw_date(unwrapped857)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1626 = _dollar_dollar.datetime_value
                else:
                    _t1626 = None
                deconstruct_result854 = _t1626
                if deconstruct_result854 is not None:
                    assert deconstruct_result854 is not None
                    unwrapped855 = deconstruct_result854
                    self.pretty_raw_datetime(unwrapped855)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1627 = _dollar_dollar.string_value
                    else:
                        _t1627 = None
                    deconstruct_result852 = _t1627
                    if deconstruct_result852 is not None:
                        assert deconstruct_result852 is not None
                        unwrapped853 = deconstruct_result852
                        self.write(self.format_string_value(unwrapped853))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1628 = _dollar_dollar.int32_value
                        else:
                            _t1628 = None
                        deconstruct_result850 = _t1628
                        if deconstruct_result850 is not None:
                            assert deconstruct_result850 is not None
                            unwrapped851 = deconstruct_result850
                            self.write((str(unwrapped851) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1629 = _dollar_dollar.int_value
                            else:
                                _t1629 = None
                            deconstruct_result848 = _t1629
                            if deconstruct_result848 is not None:
                                assert deconstruct_result848 is not None
                                unwrapped849 = deconstruct_result848
                                self.write(str(unwrapped849))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1630 = _dollar_dollar.float32_value
                                else:
                                    _t1630 = None
                                deconstruct_result846 = _t1630
                                if deconstruct_result846 is not None:
                                    assert deconstruct_result846 is not None
                                    unwrapped847 = deconstruct_result846
                                    self.write(self.format_float32_literal(unwrapped847))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1631 = _dollar_dollar.float_value
                                    else:
                                        _t1631 = None
                                    deconstruct_result844 = _t1631
                                    if deconstruct_result844 is not None:
                                        assert deconstruct_result844 is not None
                                        unwrapped845 = deconstruct_result844
                                        self.write(str(unwrapped845))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1632 = _dollar_dollar.uint32_value
                                        else:
                                            _t1632 = None
                                        deconstruct_result842 = _t1632
                                        if deconstruct_result842 is not None:
                                            assert deconstruct_result842 is not None
                                            unwrapped843 = deconstruct_result842
                                            self.write((str(unwrapped843) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1633 = _dollar_dollar.uint128_value
                                            else:
                                                _t1633 = None
                                            deconstruct_result840 = _t1633
                                            if deconstruct_result840 is not None:
                                                assert deconstruct_result840 is not None
                                                unwrapped841 = deconstruct_result840
                                                self.write(self.format_uint128(unwrapped841))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1634 = _dollar_dollar.int128_value
                                                else:
                                                    _t1634 = None
                                                deconstruct_result838 = _t1634
                                                if deconstruct_result838 is not None:
                                                    assert deconstruct_result838 is not None
                                                    unwrapped839 = deconstruct_result838
                                                    self.write(self.format_int128(unwrapped839))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1635 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1635 = None
                                                    deconstruct_result836 = _t1635
                                                    if deconstruct_result836 is not None:
                                                        assert deconstruct_result836 is not None
                                                        unwrapped837 = deconstruct_result836
                                                        self.write(self.format_decimal(unwrapped837))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1636 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1636 = None
                                                        deconstruct_result834 = _t1636
                                                        if deconstruct_result834 is not None:
                                                            assert deconstruct_result834 is not None
                                                            unwrapped835 = deconstruct_result834
                                                            self.pretty_boolean_value(unwrapped835)
                                                        else:
                                                            fields833 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat864 = self._try_flat(msg, self.pretty_raw_date)
        if flat864 is not None:
            assert flat864 is not None
            self.write(flat864)
            return None
        else:
            _dollar_dollar = msg
            fields859 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields859 is not None
            unwrapped_fields860 = fields859
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field861 = unwrapped_fields860[0]
            self.write(str(field861))
            self.newline()
            field862 = unwrapped_fields860[1]
            self.write(str(field862))
            self.newline()
            field863 = unwrapped_fields860[2]
            self.write(str(field863))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat875 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat875 is not None:
            assert flat875 is not None
            self.write(flat875)
            return None
        else:
            _dollar_dollar = msg
            fields865 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields865 is not None
            unwrapped_fields866 = fields865
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field867 = unwrapped_fields866[0]
            self.write(str(field867))
            self.newline()
            field868 = unwrapped_fields866[1]
            self.write(str(field868))
            self.newline()
            field869 = unwrapped_fields866[2]
            self.write(str(field869))
            self.newline()
            field870 = unwrapped_fields866[3]
            self.write(str(field870))
            self.newline()
            field871 = unwrapped_fields866[4]
            self.write(str(field871))
            self.newline()
            field872 = unwrapped_fields866[5]
            self.write(str(field872))
            field873 = unwrapped_fields866[6]
            if field873 is not None:
                self.newline()
                assert field873 is not None
                opt_val874 = field873
                self.write(str(opt_val874))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1637 = ()
        else:
            _t1637 = None
        deconstruct_result878 = _t1637
        if deconstruct_result878 is not None:
            assert deconstruct_result878 is not None
            unwrapped879 = deconstruct_result878
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1638 = ()
            else:
                _t1638 = None
            deconstruct_result876 = _t1638
            if deconstruct_result876 is not None:
                assert deconstruct_result876 is not None
                unwrapped877 = deconstruct_result876
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat884 = self._try_flat(msg, self.pretty_sync)
        if flat884 is not None:
            assert flat884 is not None
            self.write(flat884)
            return None
        else:
            _dollar_dollar = msg
            fields880 = _dollar_dollar.fragments
            assert fields880 is not None
            unwrapped_fields881 = fields880
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields881) == 0:
                self.newline()
                for i883, elem882 in enumerate(unwrapped_fields881):
                    if (i883 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem882)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat887 = self._try_flat(msg, self.pretty_fragment_id)
        if flat887 is not None:
            assert flat887 is not None
            self.write(flat887)
            return None
        else:
            _dollar_dollar = msg
            fields885 = self.fragment_id_to_string(_dollar_dollar)
            assert fields885 is not None
            unwrapped_fields886 = fields885
            self.write(":")
            self.write(unwrapped_fields886)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat894 = self._try_flat(msg, self.pretty_epoch)
        if flat894 is not None:
            assert flat894 is not None
            self.write(flat894)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1639 = _dollar_dollar.writes
            else:
                _t1639 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1640 = _dollar_dollar.reads
            else:
                _t1640 = None
            fields888 = (_t1639, _t1640,)
            assert fields888 is not None
            unwrapped_fields889 = fields888
            self.write("(epoch")
            self.indent_sexp()
            field890 = unwrapped_fields889[0]
            if field890 is not None:
                self.newline()
                assert field890 is not None
                opt_val891 = field890
                self.pretty_epoch_writes(opt_val891)
            field892 = unwrapped_fields889[1]
            if field892 is not None:
                self.newline()
                assert field892 is not None
                opt_val893 = field892
                self.pretty_epoch_reads(opt_val893)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat898 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat898 is not None:
            assert flat898 is not None
            self.write(flat898)
            return None
        else:
            fields895 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields895) == 0:
                self.newline()
                for i897, elem896 in enumerate(fields895):
                    if (i897 > 0):
                        self.newline()
                    self.pretty_write(elem896)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat907 = self._try_flat(msg, self.pretty_write)
        if flat907 is not None:
            assert flat907 is not None
            self.write(flat907)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1641 = _dollar_dollar.define
            else:
                _t1641 = None
            deconstruct_result905 = _t1641
            if deconstruct_result905 is not None:
                assert deconstruct_result905 is not None
                unwrapped906 = deconstruct_result905
                self.pretty_define(unwrapped906)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1642 = _dollar_dollar.undefine
                else:
                    _t1642 = None
                deconstruct_result903 = _t1642
                if deconstruct_result903 is not None:
                    assert deconstruct_result903 is not None
                    unwrapped904 = deconstruct_result903
                    self.pretty_undefine(unwrapped904)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1643 = _dollar_dollar.context
                    else:
                        _t1643 = None
                    deconstruct_result901 = _t1643
                    if deconstruct_result901 is not None:
                        assert deconstruct_result901 is not None
                        unwrapped902 = deconstruct_result901
                        self.pretty_context(unwrapped902)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1644 = _dollar_dollar.snapshot
                        else:
                            _t1644 = None
                        deconstruct_result899 = _t1644
                        if deconstruct_result899 is not None:
                            assert deconstruct_result899 is not None
                            unwrapped900 = deconstruct_result899
                            self.pretty_snapshot(unwrapped900)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat910 = self._try_flat(msg, self.pretty_define)
        if flat910 is not None:
            assert flat910 is not None
            self.write(flat910)
            return None
        else:
            _dollar_dollar = msg
            fields908 = _dollar_dollar.fragment
            assert fields908 is not None
            unwrapped_fields909 = fields908
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields909)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat917 = self._try_flat(msg, self.pretty_fragment)
        if flat917 is not None:
            assert flat917 is not None
            self.write(flat917)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields911 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields911 is not None
            unwrapped_fields912 = fields911
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field913 = unwrapped_fields912[0]
            self.pretty_new_fragment_id(field913)
            field914 = unwrapped_fields912[1]
            if not len(field914) == 0:
                self.newline()
                for i916, elem915 in enumerate(field914):
                    if (i916 > 0):
                        self.newline()
                    self.pretty_declaration(elem915)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat919 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat919 is not None:
            assert flat919 is not None
            self.write(flat919)
            return None
        else:
            fields918 = msg
            self.pretty_fragment_id(fields918)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat928 = self._try_flat(msg, self.pretty_declaration)
        if flat928 is not None:
            assert flat928 is not None
            self.write(flat928)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1645 = getattr(_dollar_dollar, 'def')
            else:
                _t1645 = None
            deconstruct_result926 = _t1645
            if deconstruct_result926 is not None:
                assert deconstruct_result926 is not None
                unwrapped927 = deconstruct_result926
                self.pretty_def(unwrapped927)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1646 = _dollar_dollar.algorithm
                else:
                    _t1646 = None
                deconstruct_result924 = _t1646
                if deconstruct_result924 is not None:
                    assert deconstruct_result924 is not None
                    unwrapped925 = deconstruct_result924
                    self.pretty_algorithm(unwrapped925)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1647 = _dollar_dollar.constraint
                    else:
                        _t1647 = None
                    deconstruct_result922 = _t1647
                    if deconstruct_result922 is not None:
                        assert deconstruct_result922 is not None
                        unwrapped923 = deconstruct_result922
                        self.pretty_constraint(unwrapped923)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1648 = _dollar_dollar.data
                        else:
                            _t1648 = None
                        deconstruct_result920 = _t1648
                        if deconstruct_result920 is not None:
                            assert deconstruct_result920 is not None
                            unwrapped921 = deconstruct_result920
                            self.pretty_data(unwrapped921)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat935 = self._try_flat(msg, self.pretty_def)
        if flat935 is not None:
            assert flat935 is not None
            self.write(flat935)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1649 = _dollar_dollar.attrs
            else:
                _t1649 = None
            fields929 = (_dollar_dollar.name, _dollar_dollar.body, _t1649,)
            assert fields929 is not None
            unwrapped_fields930 = fields929
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field931 = unwrapped_fields930[0]
            self.pretty_relation_id(field931)
            self.newline()
            field932 = unwrapped_fields930[1]
            self.pretty_abstraction(field932)
            field933 = unwrapped_fields930[2]
            if field933 is not None:
                self.newline()
                assert field933 is not None
                opt_val934 = field933
                self.pretty_attrs(opt_val934)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat940 = self._try_flat(msg, self.pretty_relation_id)
        if flat940 is not None:
            assert flat940 is not None
            self.write(flat940)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1651 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1650 = _t1651
            else:
                _t1650 = None
            deconstruct_result938 = _t1650
            if deconstruct_result938 is not None:
                assert deconstruct_result938 is not None
                unwrapped939 = deconstruct_result938
                self.write(":")
                self.write(unwrapped939)
            else:
                _dollar_dollar = msg
                _t1652 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result936 = _t1652
                if deconstruct_result936 is not None:
                    assert deconstruct_result936 is not None
                    unwrapped937 = deconstruct_result936
                    self.write(self.format_uint128(unwrapped937))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat945 = self._try_flat(msg, self.pretty_abstraction)
        if flat945 is not None:
            assert flat945 is not None
            self.write(flat945)
            return None
        else:
            _dollar_dollar = msg
            _t1653 = self.deconstruct_bindings(_dollar_dollar)
            fields941 = (_t1653, _dollar_dollar.value,)
            assert fields941 is not None
            unwrapped_fields942 = fields941
            self.write("(")
            self.indent()
            field943 = unwrapped_fields942[0]
            self.pretty_bindings(field943)
            self.newline()
            field944 = unwrapped_fields942[1]
            self.pretty_formula(field944)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat953 = self._try_flat(msg, self.pretty_bindings)
        if flat953 is not None:
            assert flat953 is not None
            self.write(flat953)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1654 = _dollar_dollar[1]
            else:
                _t1654 = None
            fields946 = (_dollar_dollar[0], _t1654,)
            assert fields946 is not None
            unwrapped_fields947 = fields946
            self.write("[")
            self.indent()
            field948 = unwrapped_fields947[0]
            for i950, elem949 in enumerate(field948):
                if (i950 > 0):
                    self.newline()
                self.pretty_binding(elem949)
            field951 = unwrapped_fields947[1]
            if field951 is not None:
                self.newline()
                assert field951 is not None
                opt_val952 = field951
                self.pretty_value_bindings(opt_val952)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat958 = self._try_flat(msg, self.pretty_binding)
        if flat958 is not None:
            assert flat958 is not None
            self.write(flat958)
            return None
        else:
            _dollar_dollar = msg
            fields954 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields954 is not None
            unwrapped_fields955 = fields954
            field956 = unwrapped_fields955[0]
            self.write(field956)
            self.write("::")
            field957 = unwrapped_fields955[1]
            self.pretty_type(field957)

    def pretty_type(self, msg: logic_pb2.Type):
        flat987 = self._try_flat(msg, self.pretty_type)
        if flat987 is not None:
            assert flat987 is not None
            self.write(flat987)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1655 = _dollar_dollar.unspecified_type
            else:
                _t1655 = None
            deconstruct_result985 = _t1655
            if deconstruct_result985 is not None:
                assert deconstruct_result985 is not None
                unwrapped986 = deconstruct_result985
                self.pretty_unspecified_type(unwrapped986)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1656 = _dollar_dollar.string_type
                else:
                    _t1656 = None
                deconstruct_result983 = _t1656
                if deconstruct_result983 is not None:
                    assert deconstruct_result983 is not None
                    unwrapped984 = deconstruct_result983
                    self.pretty_string_type(unwrapped984)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1657 = _dollar_dollar.int_type
                    else:
                        _t1657 = None
                    deconstruct_result981 = _t1657
                    if deconstruct_result981 is not None:
                        assert deconstruct_result981 is not None
                        unwrapped982 = deconstruct_result981
                        self.pretty_int_type(unwrapped982)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1658 = _dollar_dollar.float_type
                        else:
                            _t1658 = None
                        deconstruct_result979 = _t1658
                        if deconstruct_result979 is not None:
                            assert deconstruct_result979 is not None
                            unwrapped980 = deconstruct_result979
                            self.pretty_float_type(unwrapped980)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1659 = _dollar_dollar.uint128_type
                            else:
                                _t1659 = None
                            deconstruct_result977 = _t1659
                            if deconstruct_result977 is not None:
                                assert deconstruct_result977 is not None
                                unwrapped978 = deconstruct_result977
                                self.pretty_uint128_type(unwrapped978)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1660 = _dollar_dollar.int128_type
                                else:
                                    _t1660 = None
                                deconstruct_result975 = _t1660
                                if deconstruct_result975 is not None:
                                    assert deconstruct_result975 is not None
                                    unwrapped976 = deconstruct_result975
                                    self.pretty_int128_type(unwrapped976)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1661 = _dollar_dollar.date_type
                                    else:
                                        _t1661 = None
                                    deconstruct_result973 = _t1661
                                    if deconstruct_result973 is not None:
                                        assert deconstruct_result973 is not None
                                        unwrapped974 = deconstruct_result973
                                        self.pretty_date_type(unwrapped974)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1662 = _dollar_dollar.datetime_type
                                        else:
                                            _t1662 = None
                                        deconstruct_result971 = _t1662
                                        if deconstruct_result971 is not None:
                                            assert deconstruct_result971 is not None
                                            unwrapped972 = deconstruct_result971
                                            self.pretty_datetime_type(unwrapped972)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1663 = _dollar_dollar.missing_type
                                            else:
                                                _t1663 = None
                                            deconstruct_result969 = _t1663
                                            if deconstruct_result969 is not None:
                                                assert deconstruct_result969 is not None
                                                unwrapped970 = deconstruct_result969
                                                self.pretty_missing_type(unwrapped970)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1664 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1664 = None
                                                deconstruct_result967 = _t1664
                                                if deconstruct_result967 is not None:
                                                    assert deconstruct_result967 is not None
                                                    unwrapped968 = deconstruct_result967
                                                    self.pretty_decimal_type(unwrapped968)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1665 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1665 = None
                                                    deconstruct_result965 = _t1665
                                                    if deconstruct_result965 is not None:
                                                        assert deconstruct_result965 is not None
                                                        unwrapped966 = deconstruct_result965
                                                        self.pretty_boolean_type(unwrapped966)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1666 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1666 = None
                                                        deconstruct_result963 = _t1666
                                                        if deconstruct_result963 is not None:
                                                            assert deconstruct_result963 is not None
                                                            unwrapped964 = deconstruct_result963
                                                            self.pretty_int32_type(unwrapped964)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1667 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1667 = None
                                                            deconstruct_result961 = _t1667
                                                            if deconstruct_result961 is not None:
                                                                assert deconstruct_result961 is not None
                                                                unwrapped962 = deconstruct_result961
                                                                self.pretty_float32_type(unwrapped962)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1668 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1668 = None
                                                                deconstruct_result959 = _t1668
                                                                if deconstruct_result959 is not None:
                                                                    assert deconstruct_result959 is not None
                                                                    unwrapped960 = deconstruct_result959
                                                                    self.pretty_uint32_type(unwrapped960)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields988 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields989 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields990 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields991 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields992 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields993 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields994 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields995 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields996 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat1001 = self._try_flat(msg, self.pretty_decimal_type)
        if flat1001 is not None:
            assert flat1001 is not None
            self.write(flat1001)
            return None
        else:
            _dollar_dollar = msg
            fields997 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields997 is not None
            unwrapped_fields998 = fields997
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field999 = unwrapped_fields998[0]
            self.write(str(field999))
            self.newline()
            field1000 = unwrapped_fields998[1]
            self.write(str(field1000))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields1002 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields1003 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields1004 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields1005 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat1009 = self._try_flat(msg, self.pretty_value_bindings)
        if flat1009 is not None:
            assert flat1009 is not None
            self.write(flat1009)
            return None
        else:
            fields1006 = msg
            self.write("|")
            if not len(fields1006) == 0:
                self.write(" ")
                for i1008, elem1007 in enumerate(fields1006):
                    if (i1008 > 0):
                        self.newline()
                    self.pretty_binding(elem1007)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1036 = self._try_flat(msg, self.pretty_formula)
        if flat1036 is not None:
            assert flat1036 is not None
            self.write(flat1036)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1669 = _dollar_dollar.conjunction
            else:
                _t1669 = None
            deconstruct_result1034 = _t1669
            if deconstruct_result1034 is not None:
                assert deconstruct_result1034 is not None
                unwrapped1035 = deconstruct_result1034
                self.pretty_true(unwrapped1035)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1670 = _dollar_dollar.disjunction
                else:
                    _t1670 = None
                deconstruct_result1032 = _t1670
                if deconstruct_result1032 is not None:
                    assert deconstruct_result1032 is not None
                    unwrapped1033 = deconstruct_result1032
                    self.pretty_false(unwrapped1033)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1671 = _dollar_dollar.exists
                    else:
                        _t1671 = None
                    deconstruct_result1030 = _t1671
                    if deconstruct_result1030 is not None:
                        assert deconstruct_result1030 is not None
                        unwrapped1031 = deconstruct_result1030
                        self.pretty_exists(unwrapped1031)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1672 = _dollar_dollar.reduce
                        else:
                            _t1672 = None
                        deconstruct_result1028 = _t1672
                        if deconstruct_result1028 is not None:
                            assert deconstruct_result1028 is not None
                            unwrapped1029 = deconstruct_result1028
                            self.pretty_reduce(unwrapped1029)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1673 = _dollar_dollar.conjunction
                            else:
                                _t1673 = None
                            deconstruct_result1026 = _t1673
                            if deconstruct_result1026 is not None:
                                assert deconstruct_result1026 is not None
                                unwrapped1027 = deconstruct_result1026
                                self.pretty_conjunction(unwrapped1027)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1674 = _dollar_dollar.disjunction
                                else:
                                    _t1674 = None
                                deconstruct_result1024 = _t1674
                                if deconstruct_result1024 is not None:
                                    assert deconstruct_result1024 is not None
                                    unwrapped1025 = deconstruct_result1024
                                    self.pretty_disjunction(unwrapped1025)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1675 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1675 = None
                                    deconstruct_result1022 = _t1675
                                    if deconstruct_result1022 is not None:
                                        assert deconstruct_result1022 is not None
                                        unwrapped1023 = deconstruct_result1022
                                        self.pretty_not(unwrapped1023)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1676 = _dollar_dollar.ffi
                                        else:
                                            _t1676 = None
                                        deconstruct_result1020 = _t1676
                                        if deconstruct_result1020 is not None:
                                            assert deconstruct_result1020 is not None
                                            unwrapped1021 = deconstruct_result1020
                                            self.pretty_ffi(unwrapped1021)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1677 = _dollar_dollar.atom
                                            else:
                                                _t1677 = None
                                            deconstruct_result1018 = _t1677
                                            if deconstruct_result1018 is not None:
                                                assert deconstruct_result1018 is not None
                                                unwrapped1019 = deconstruct_result1018
                                                self.pretty_atom(unwrapped1019)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1678 = _dollar_dollar.pragma
                                                else:
                                                    _t1678 = None
                                                deconstruct_result1016 = _t1678
                                                if deconstruct_result1016 is not None:
                                                    assert deconstruct_result1016 is not None
                                                    unwrapped1017 = deconstruct_result1016
                                                    self.pretty_pragma(unwrapped1017)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1679 = _dollar_dollar.primitive
                                                    else:
                                                        _t1679 = None
                                                    deconstruct_result1014 = _t1679
                                                    if deconstruct_result1014 is not None:
                                                        assert deconstruct_result1014 is not None
                                                        unwrapped1015 = deconstruct_result1014
                                                        self.pretty_primitive(unwrapped1015)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1680 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1680 = None
                                                        deconstruct_result1012 = _t1680
                                                        if deconstruct_result1012 is not None:
                                                            assert deconstruct_result1012 is not None
                                                            unwrapped1013 = deconstruct_result1012
                                                            self.pretty_rel_atom(unwrapped1013)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1681 = _dollar_dollar.cast
                                                            else:
                                                                _t1681 = None
                                                            deconstruct_result1010 = _t1681
                                                            if deconstruct_result1010 is not None:
                                                                assert deconstruct_result1010 is not None
                                                                unwrapped1011 = deconstruct_result1010
                                                                self.pretty_cast(unwrapped1011)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields1037 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1038 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1043 = self._try_flat(msg, self.pretty_exists)
        if flat1043 is not None:
            assert flat1043 is not None
            self.write(flat1043)
            return None
        else:
            _dollar_dollar = msg
            _t1682 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1039 = (_t1682, _dollar_dollar.body.value,)
            assert fields1039 is not None
            unwrapped_fields1040 = fields1039
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1041 = unwrapped_fields1040[0]
            self.pretty_bindings(field1041)
            self.newline()
            field1042 = unwrapped_fields1040[1]
            self.pretty_formula(field1042)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1049 = self._try_flat(msg, self.pretty_reduce)
        if flat1049 is not None:
            assert flat1049 is not None
            self.write(flat1049)
            return None
        else:
            _dollar_dollar = msg
            fields1044 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1044 is not None
            unwrapped_fields1045 = fields1044
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1046 = unwrapped_fields1045[0]
            self.pretty_abstraction(field1046)
            self.newline()
            field1047 = unwrapped_fields1045[1]
            self.pretty_abstraction(field1047)
            self.newline()
            field1048 = unwrapped_fields1045[2]
            self.pretty_terms(field1048)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1053 = self._try_flat(msg, self.pretty_terms)
        if flat1053 is not None:
            assert flat1053 is not None
            self.write(flat1053)
            return None
        else:
            fields1050 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1050) == 0:
                self.newline()
                for i1052, elem1051 in enumerate(fields1050):
                    if (i1052 > 0):
                        self.newline()
                    self.pretty_term(elem1051)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1058 = self._try_flat(msg, self.pretty_term)
        if flat1058 is not None:
            assert flat1058 is not None
            self.write(flat1058)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1683 = _dollar_dollar.var
            else:
                _t1683 = None
            deconstruct_result1056 = _t1683
            if deconstruct_result1056 is not None:
                assert deconstruct_result1056 is not None
                unwrapped1057 = deconstruct_result1056
                self.pretty_var(unwrapped1057)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1684 = _dollar_dollar.constant
                else:
                    _t1684 = None
                deconstruct_result1054 = _t1684
                if deconstruct_result1054 is not None:
                    assert deconstruct_result1054 is not None
                    unwrapped1055 = deconstruct_result1054
                    self.pretty_value(unwrapped1055)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1061 = self._try_flat(msg, self.pretty_var)
        if flat1061 is not None:
            assert flat1061 is not None
            self.write(flat1061)
            return None
        else:
            _dollar_dollar = msg
            fields1059 = _dollar_dollar.name
            assert fields1059 is not None
            unwrapped_fields1060 = fields1059
            self.write(unwrapped_fields1060)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1087 = self._try_flat(msg, self.pretty_value)
        if flat1087 is not None:
            assert flat1087 is not None
            self.write(flat1087)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1685 = _dollar_dollar.date_value
            else:
                _t1685 = None
            deconstruct_result1085 = _t1685
            if deconstruct_result1085 is not None:
                assert deconstruct_result1085 is not None
                unwrapped1086 = deconstruct_result1085
                self.pretty_date(unwrapped1086)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1686 = _dollar_dollar.datetime_value
                else:
                    _t1686 = None
                deconstruct_result1083 = _t1686
                if deconstruct_result1083 is not None:
                    assert deconstruct_result1083 is not None
                    unwrapped1084 = deconstruct_result1083
                    self.pretty_datetime(unwrapped1084)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1687 = _dollar_dollar.string_value
                    else:
                        _t1687 = None
                    deconstruct_result1081 = _t1687
                    if deconstruct_result1081 is not None:
                        assert deconstruct_result1081 is not None
                        unwrapped1082 = deconstruct_result1081
                        self.write(self.format_string_value(unwrapped1082))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1688 = _dollar_dollar.int32_value
                        else:
                            _t1688 = None
                        deconstruct_result1079 = _t1688
                        if deconstruct_result1079 is not None:
                            assert deconstruct_result1079 is not None
                            unwrapped1080 = deconstruct_result1079
                            self.write((str(unwrapped1080) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1689 = _dollar_dollar.int_value
                            else:
                                _t1689 = None
                            deconstruct_result1077 = _t1689
                            if deconstruct_result1077 is not None:
                                assert deconstruct_result1077 is not None
                                unwrapped1078 = deconstruct_result1077
                                self.write(str(unwrapped1078))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1690 = _dollar_dollar.float32_value
                                else:
                                    _t1690 = None
                                deconstruct_result1075 = _t1690
                                if deconstruct_result1075 is not None:
                                    assert deconstruct_result1075 is not None
                                    unwrapped1076 = deconstruct_result1075
                                    self.write(self.format_float32_literal(unwrapped1076))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1691 = _dollar_dollar.float_value
                                    else:
                                        _t1691 = None
                                    deconstruct_result1073 = _t1691
                                    if deconstruct_result1073 is not None:
                                        assert deconstruct_result1073 is not None
                                        unwrapped1074 = deconstruct_result1073
                                        self.write(str(unwrapped1074))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1692 = _dollar_dollar.uint32_value
                                        else:
                                            _t1692 = None
                                        deconstruct_result1071 = _t1692
                                        if deconstruct_result1071 is not None:
                                            assert deconstruct_result1071 is not None
                                            unwrapped1072 = deconstruct_result1071
                                            self.write((str(unwrapped1072) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1693 = _dollar_dollar.uint128_value
                                            else:
                                                _t1693 = None
                                            deconstruct_result1069 = _t1693
                                            if deconstruct_result1069 is not None:
                                                assert deconstruct_result1069 is not None
                                                unwrapped1070 = deconstruct_result1069
                                                self.write(self.format_uint128(unwrapped1070))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1694 = _dollar_dollar.int128_value
                                                else:
                                                    _t1694 = None
                                                deconstruct_result1067 = _t1694
                                                if deconstruct_result1067 is not None:
                                                    assert deconstruct_result1067 is not None
                                                    unwrapped1068 = deconstruct_result1067
                                                    self.write(self.format_int128(unwrapped1068))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1695 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1695 = None
                                                    deconstruct_result1065 = _t1695
                                                    if deconstruct_result1065 is not None:
                                                        assert deconstruct_result1065 is not None
                                                        unwrapped1066 = deconstruct_result1065
                                                        self.write(self.format_decimal(unwrapped1066))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1696 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1696 = None
                                                        deconstruct_result1063 = _t1696
                                                        if deconstruct_result1063 is not None:
                                                            assert deconstruct_result1063 is not None
                                                            unwrapped1064 = deconstruct_result1063
                                                            self.pretty_boolean_value(unwrapped1064)
                                                        else:
                                                            fields1062 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1093 = self._try_flat(msg, self.pretty_date)
        if flat1093 is not None:
            assert flat1093 is not None
            self.write(flat1093)
            return None
        else:
            _dollar_dollar = msg
            fields1088 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1088 is not None
            unwrapped_fields1089 = fields1088
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1090 = unwrapped_fields1089[0]
            self.write(str(field1090))
            self.newline()
            field1091 = unwrapped_fields1089[1]
            self.write(str(field1091))
            self.newline()
            field1092 = unwrapped_fields1089[2]
            self.write(str(field1092))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1104 = self._try_flat(msg, self.pretty_datetime)
        if flat1104 is not None:
            assert flat1104 is not None
            self.write(flat1104)
            return None
        else:
            _dollar_dollar = msg
            fields1094 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1094 is not None
            unwrapped_fields1095 = fields1094
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1096 = unwrapped_fields1095[0]
            self.write(str(field1096))
            self.newline()
            field1097 = unwrapped_fields1095[1]
            self.write(str(field1097))
            self.newline()
            field1098 = unwrapped_fields1095[2]
            self.write(str(field1098))
            self.newline()
            field1099 = unwrapped_fields1095[3]
            self.write(str(field1099))
            self.newline()
            field1100 = unwrapped_fields1095[4]
            self.write(str(field1100))
            self.newline()
            field1101 = unwrapped_fields1095[5]
            self.write(str(field1101))
            field1102 = unwrapped_fields1095[6]
            if field1102 is not None:
                self.newline()
                assert field1102 is not None
                opt_val1103 = field1102
                self.write(str(opt_val1103))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1109 = self._try_flat(msg, self.pretty_conjunction)
        if flat1109 is not None:
            assert flat1109 is not None
            self.write(flat1109)
            return None
        else:
            _dollar_dollar = msg
            fields1105 = _dollar_dollar.args
            assert fields1105 is not None
            unwrapped_fields1106 = fields1105
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1106) == 0:
                self.newline()
                for i1108, elem1107 in enumerate(unwrapped_fields1106):
                    if (i1108 > 0):
                        self.newline()
                    self.pretty_formula(elem1107)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1114 = self._try_flat(msg, self.pretty_disjunction)
        if flat1114 is not None:
            assert flat1114 is not None
            self.write(flat1114)
            return None
        else:
            _dollar_dollar = msg
            fields1110 = _dollar_dollar.args
            assert fields1110 is not None
            unwrapped_fields1111 = fields1110
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1111) == 0:
                self.newline()
                for i1113, elem1112 in enumerate(unwrapped_fields1111):
                    if (i1113 > 0):
                        self.newline()
                    self.pretty_formula(elem1112)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1117 = self._try_flat(msg, self.pretty_not)
        if flat1117 is not None:
            assert flat1117 is not None
            self.write(flat1117)
            return None
        else:
            _dollar_dollar = msg
            fields1115 = _dollar_dollar.arg
            assert fields1115 is not None
            unwrapped_fields1116 = fields1115
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1116)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1123 = self._try_flat(msg, self.pretty_ffi)
        if flat1123 is not None:
            assert flat1123 is not None
            self.write(flat1123)
            return None
        else:
            _dollar_dollar = msg
            fields1118 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1118 is not None
            unwrapped_fields1119 = fields1118
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1120 = unwrapped_fields1119[0]
            self.pretty_name(field1120)
            self.newline()
            field1121 = unwrapped_fields1119[1]
            self.pretty_ffi_args(field1121)
            self.newline()
            field1122 = unwrapped_fields1119[2]
            self.pretty_terms(field1122)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1125 = self._try_flat(msg, self.pretty_name)
        if flat1125 is not None:
            assert flat1125 is not None
            self.write(flat1125)
            return None
        else:
            fields1124 = msg
            self.write(":")
            self.write(fields1124)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1129 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1129 is not None:
            assert flat1129 is not None
            self.write(flat1129)
            return None
        else:
            fields1126 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1126) == 0:
                self.newline()
                for i1128, elem1127 in enumerate(fields1126):
                    if (i1128 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1127)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1136 = self._try_flat(msg, self.pretty_atom)
        if flat1136 is not None:
            assert flat1136 is not None
            self.write(flat1136)
            return None
        else:
            _dollar_dollar = msg
            fields1130 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1130 is not None
            unwrapped_fields1131 = fields1130
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1132 = unwrapped_fields1131[0]
            self.pretty_relation_id(field1132)
            field1133 = unwrapped_fields1131[1]
            if not len(field1133) == 0:
                self.newline()
                for i1135, elem1134 in enumerate(field1133):
                    if (i1135 > 0):
                        self.newline()
                    self.pretty_term(elem1134)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1143 = self._try_flat(msg, self.pretty_pragma)
        if flat1143 is not None:
            assert flat1143 is not None
            self.write(flat1143)
            return None
        else:
            _dollar_dollar = msg
            fields1137 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1137 is not None
            unwrapped_fields1138 = fields1137
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1139 = unwrapped_fields1138[0]
            self.pretty_name(field1139)
            field1140 = unwrapped_fields1138[1]
            if not len(field1140) == 0:
                self.newline()
                for i1142, elem1141 in enumerate(field1140):
                    if (i1142 > 0):
                        self.newline()
                    self.pretty_term(elem1141)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1159 = self._try_flat(msg, self.pretty_primitive)
        if flat1159 is not None:
            assert flat1159 is not None
            self.write(flat1159)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1697 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1697 = None
            guard_result1158 = _t1697
            if guard_result1158 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1698 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1698 = None
                guard_result1157 = _t1698
                if guard_result1157 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1699 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1699 = None
                    guard_result1156 = _t1699
                    if guard_result1156 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1700 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1700 = None
                        guard_result1155 = _t1700
                        if guard_result1155 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1701 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1701 = None
                            guard_result1154 = _t1701
                            if guard_result1154 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1702 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1702 = None
                                guard_result1153 = _t1702
                                if guard_result1153 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1703 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1703 = None
                                    guard_result1152 = _t1703
                                    if guard_result1152 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1704 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1704 = None
                                        guard_result1151 = _t1704
                                        if guard_result1151 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1705 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1705 = None
                                            guard_result1150 = _t1705
                                            if guard_result1150 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1144 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1144 is not None
                                                unwrapped_fields1145 = fields1144
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1146 = unwrapped_fields1145[0]
                                                self.pretty_name(field1146)
                                                field1147 = unwrapped_fields1145[1]
                                                if not len(field1147) == 0:
                                                    self.newline()
                                                    for i1149, elem1148 in enumerate(field1147):
                                                        if (i1149 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1148)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1164 = self._try_flat(msg, self.pretty_eq)
        if flat1164 is not None:
            assert flat1164 is not None
            self.write(flat1164)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1706 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1706 = None
            fields1160 = _t1706
            assert fields1160 is not None
            unwrapped_fields1161 = fields1160
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1162 = unwrapped_fields1161[0]
            self.pretty_term(field1162)
            self.newline()
            field1163 = unwrapped_fields1161[1]
            self.pretty_term(field1163)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1169 = self._try_flat(msg, self.pretty_lt)
        if flat1169 is not None:
            assert flat1169 is not None
            self.write(flat1169)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1707 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1707 = None
            fields1165 = _t1707
            assert fields1165 is not None
            unwrapped_fields1166 = fields1165
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1167 = unwrapped_fields1166[0]
            self.pretty_term(field1167)
            self.newline()
            field1168 = unwrapped_fields1166[1]
            self.pretty_term(field1168)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1174 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1174 is not None:
            assert flat1174 is not None
            self.write(flat1174)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1708 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1708 = None
            fields1170 = _t1708
            assert fields1170 is not None
            unwrapped_fields1171 = fields1170
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1172 = unwrapped_fields1171[0]
            self.pretty_term(field1172)
            self.newline()
            field1173 = unwrapped_fields1171[1]
            self.pretty_term(field1173)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1179 = self._try_flat(msg, self.pretty_gt)
        if flat1179 is not None:
            assert flat1179 is not None
            self.write(flat1179)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1709 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1709 = None
            fields1175 = _t1709
            assert fields1175 is not None
            unwrapped_fields1176 = fields1175
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1177 = unwrapped_fields1176[0]
            self.pretty_term(field1177)
            self.newline()
            field1178 = unwrapped_fields1176[1]
            self.pretty_term(field1178)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1184 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1184 is not None:
            assert flat1184 is not None
            self.write(flat1184)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1710 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1710 = None
            fields1180 = _t1710
            assert fields1180 is not None
            unwrapped_fields1181 = fields1180
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1182 = unwrapped_fields1181[0]
            self.pretty_term(field1182)
            self.newline()
            field1183 = unwrapped_fields1181[1]
            self.pretty_term(field1183)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1190 = self._try_flat(msg, self.pretty_add)
        if flat1190 is not None:
            assert flat1190 is not None
            self.write(flat1190)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1711 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1711 = None
            fields1185 = _t1711
            assert fields1185 is not None
            unwrapped_fields1186 = fields1185
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1187 = unwrapped_fields1186[0]
            self.pretty_term(field1187)
            self.newline()
            field1188 = unwrapped_fields1186[1]
            self.pretty_term(field1188)
            self.newline()
            field1189 = unwrapped_fields1186[2]
            self.pretty_term(field1189)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1196 = self._try_flat(msg, self.pretty_minus)
        if flat1196 is not None:
            assert flat1196 is not None
            self.write(flat1196)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1712 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1712 = None
            fields1191 = _t1712
            assert fields1191 is not None
            unwrapped_fields1192 = fields1191
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1193 = unwrapped_fields1192[0]
            self.pretty_term(field1193)
            self.newline()
            field1194 = unwrapped_fields1192[1]
            self.pretty_term(field1194)
            self.newline()
            field1195 = unwrapped_fields1192[2]
            self.pretty_term(field1195)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1202 = self._try_flat(msg, self.pretty_multiply)
        if flat1202 is not None:
            assert flat1202 is not None
            self.write(flat1202)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1713 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1713 = None
            fields1197 = _t1713
            assert fields1197 is not None
            unwrapped_fields1198 = fields1197
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1199 = unwrapped_fields1198[0]
            self.pretty_term(field1199)
            self.newline()
            field1200 = unwrapped_fields1198[1]
            self.pretty_term(field1200)
            self.newline()
            field1201 = unwrapped_fields1198[2]
            self.pretty_term(field1201)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1208 = self._try_flat(msg, self.pretty_divide)
        if flat1208 is not None:
            assert flat1208 is not None
            self.write(flat1208)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1714 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1714 = None
            fields1203 = _t1714
            assert fields1203 is not None
            unwrapped_fields1204 = fields1203
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1205 = unwrapped_fields1204[0]
            self.pretty_term(field1205)
            self.newline()
            field1206 = unwrapped_fields1204[1]
            self.pretty_term(field1206)
            self.newline()
            field1207 = unwrapped_fields1204[2]
            self.pretty_term(field1207)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1213 = self._try_flat(msg, self.pretty_rel_term)
        if flat1213 is not None:
            assert flat1213 is not None
            self.write(flat1213)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1715 = _dollar_dollar.specialized_value
            else:
                _t1715 = None
            deconstruct_result1211 = _t1715
            if deconstruct_result1211 is not None:
                assert deconstruct_result1211 is not None
                unwrapped1212 = deconstruct_result1211
                self.pretty_specialized_value(unwrapped1212)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1716 = _dollar_dollar.term
                else:
                    _t1716 = None
                deconstruct_result1209 = _t1716
                if deconstruct_result1209 is not None:
                    assert deconstruct_result1209 is not None
                    unwrapped1210 = deconstruct_result1209
                    self.pretty_term(unwrapped1210)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1215 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1215 is not None:
            assert flat1215 is not None
            self.write(flat1215)
            return None
        else:
            fields1214 = msg
            self.write("#")
            self.pretty_raw_value(fields1214)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1222 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1222 is not None:
            assert flat1222 is not None
            self.write(flat1222)
            return None
        else:
            _dollar_dollar = msg
            fields1216 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1216 is not None
            unwrapped_fields1217 = fields1216
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1218 = unwrapped_fields1217[0]
            self.pretty_name(field1218)
            field1219 = unwrapped_fields1217[1]
            if not len(field1219) == 0:
                self.newline()
                for i1221, elem1220 in enumerate(field1219):
                    if (i1221 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1220)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1227 = self._try_flat(msg, self.pretty_cast)
        if flat1227 is not None:
            assert flat1227 is not None
            self.write(flat1227)
            return None
        else:
            _dollar_dollar = msg
            fields1223 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1223 is not None
            unwrapped_fields1224 = fields1223
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1225 = unwrapped_fields1224[0]
            self.pretty_term(field1225)
            self.newline()
            field1226 = unwrapped_fields1224[1]
            self.pretty_term(field1226)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1231 = self._try_flat(msg, self.pretty_attrs)
        if flat1231 is not None:
            assert flat1231 is not None
            self.write(flat1231)
            return None
        else:
            fields1228 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1228) == 0:
                self.newline()
                for i1230, elem1229 in enumerate(fields1228):
                    if (i1230 > 0):
                        self.newline()
                    self.pretty_attribute(elem1229)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1238 = self._try_flat(msg, self.pretty_attribute)
        if flat1238 is not None:
            assert flat1238 is not None
            self.write(flat1238)
            return None
        else:
            _dollar_dollar = msg
            fields1232 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1232 is not None
            unwrapped_fields1233 = fields1232
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1234 = unwrapped_fields1233[0]
            self.pretty_name(field1234)
            field1235 = unwrapped_fields1233[1]
            if not len(field1235) == 0:
                self.newline()
                for i1237, elem1236 in enumerate(field1235):
                    if (i1237 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1236)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1247 = self._try_flat(msg, self.pretty_algorithm)
        if flat1247 is not None:
            assert flat1247 is not None
            self.write(flat1247)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1717 = _dollar_dollar.attrs
            else:
                _t1717 = None
            fields1239 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body, _t1717,)
            assert fields1239 is not None
            unwrapped_fields1240 = fields1239
            self.write("(algorithm")
            self.indent_sexp()
            field1241 = unwrapped_fields1240[0]
            if not len(field1241) == 0:
                self.newline()
                for i1243, elem1242 in enumerate(field1241):
                    if (i1243 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1242)
            self.newline()
            field1244 = unwrapped_fields1240[1]
            self.pretty_script(field1244)
            field1245 = unwrapped_fields1240[2]
            if field1245 is not None:
                self.newline()
                assert field1245 is not None
                opt_val1246 = field1245
                self.pretty_attrs(opt_val1246)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1252 = self._try_flat(msg, self.pretty_script)
        if flat1252 is not None:
            assert flat1252 is not None
            self.write(flat1252)
            return None
        else:
            _dollar_dollar = msg
            fields1248 = _dollar_dollar.constructs
            assert fields1248 is not None
            unwrapped_fields1249 = fields1248
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1249) == 0:
                self.newline()
                for i1251, elem1250 in enumerate(unwrapped_fields1249):
                    if (i1251 > 0):
                        self.newline()
                    self.pretty_construct(elem1250)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1257 = self._try_flat(msg, self.pretty_construct)
        if flat1257 is not None:
            assert flat1257 is not None
            self.write(flat1257)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1718 = _dollar_dollar.loop
            else:
                _t1718 = None
            deconstruct_result1255 = _t1718
            if deconstruct_result1255 is not None:
                assert deconstruct_result1255 is not None
                unwrapped1256 = deconstruct_result1255
                self.pretty_loop(unwrapped1256)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1719 = _dollar_dollar.instruction
                else:
                    _t1719 = None
                deconstruct_result1253 = _t1719
                if deconstruct_result1253 is not None:
                    assert deconstruct_result1253 is not None
                    unwrapped1254 = deconstruct_result1253
                    self.pretty_instruction(unwrapped1254)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1264 = self._try_flat(msg, self.pretty_loop)
        if flat1264 is not None:
            assert flat1264 is not None
            self.write(flat1264)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1720 = _dollar_dollar.attrs
            else:
                _t1720 = None
            fields1258 = (_dollar_dollar.init, _dollar_dollar.body, _t1720,)
            assert fields1258 is not None
            unwrapped_fields1259 = fields1258
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1260 = unwrapped_fields1259[0]
            self.pretty_init(field1260)
            self.newline()
            field1261 = unwrapped_fields1259[1]
            self.pretty_script(field1261)
            field1262 = unwrapped_fields1259[2]
            if field1262 is not None:
                self.newline()
                assert field1262 is not None
                opt_val1263 = field1262
                self.pretty_attrs(opt_val1263)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1268 = self._try_flat(msg, self.pretty_init)
        if flat1268 is not None:
            assert flat1268 is not None
            self.write(flat1268)
            return None
        else:
            fields1265 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1265) == 0:
                self.newline()
                for i1267, elem1266 in enumerate(fields1265):
                    if (i1267 > 0):
                        self.newline()
                    self.pretty_instruction(elem1266)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1279 = self._try_flat(msg, self.pretty_instruction)
        if flat1279 is not None:
            assert flat1279 is not None
            self.write(flat1279)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1721 = _dollar_dollar.assign
            else:
                _t1721 = None
            deconstruct_result1277 = _t1721
            if deconstruct_result1277 is not None:
                assert deconstruct_result1277 is not None
                unwrapped1278 = deconstruct_result1277
                self.pretty_assign(unwrapped1278)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1722 = _dollar_dollar.upsert
                else:
                    _t1722 = None
                deconstruct_result1275 = _t1722
                if deconstruct_result1275 is not None:
                    assert deconstruct_result1275 is not None
                    unwrapped1276 = deconstruct_result1275
                    self.pretty_upsert(unwrapped1276)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1723 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1723 = None
                    deconstruct_result1273 = _t1723
                    if deconstruct_result1273 is not None:
                        assert deconstruct_result1273 is not None
                        unwrapped1274 = deconstruct_result1273
                        self.pretty_break(unwrapped1274)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1724 = _dollar_dollar.monoid_def
                        else:
                            _t1724 = None
                        deconstruct_result1271 = _t1724
                        if deconstruct_result1271 is not None:
                            assert deconstruct_result1271 is not None
                            unwrapped1272 = deconstruct_result1271
                            self.pretty_monoid_def(unwrapped1272)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1725 = _dollar_dollar.monus_def
                            else:
                                _t1725 = None
                            deconstruct_result1269 = _t1725
                            if deconstruct_result1269 is not None:
                                assert deconstruct_result1269 is not None
                                unwrapped1270 = deconstruct_result1269
                                self.pretty_monus_def(unwrapped1270)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1286 = self._try_flat(msg, self.pretty_assign)
        if flat1286 is not None:
            assert flat1286 is not None
            self.write(flat1286)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1726 = _dollar_dollar.attrs
            else:
                _t1726 = None
            fields1280 = (_dollar_dollar.name, _dollar_dollar.body, _t1726,)
            assert fields1280 is not None
            unwrapped_fields1281 = fields1280
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1282 = unwrapped_fields1281[0]
            self.pretty_relation_id(field1282)
            self.newline()
            field1283 = unwrapped_fields1281[1]
            self.pretty_abstraction(field1283)
            field1284 = unwrapped_fields1281[2]
            if field1284 is not None:
                self.newline()
                assert field1284 is not None
                opt_val1285 = field1284
                self.pretty_attrs(opt_val1285)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1293 = self._try_flat(msg, self.pretty_upsert)
        if flat1293 is not None:
            assert flat1293 is not None
            self.write(flat1293)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1727 = _dollar_dollar.attrs
            else:
                _t1727 = None
            fields1287 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1727,)
            assert fields1287 is not None
            unwrapped_fields1288 = fields1287
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1289 = unwrapped_fields1288[0]
            self.pretty_relation_id(field1289)
            self.newline()
            field1290 = unwrapped_fields1288[1]
            self.pretty_abstraction_with_arity(field1290)
            field1291 = unwrapped_fields1288[2]
            if field1291 is not None:
                self.newline()
                assert field1291 is not None
                opt_val1292 = field1291
                self.pretty_attrs(opt_val1292)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1298 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1298 is not None:
            assert flat1298 is not None
            self.write(flat1298)
            return None
        else:
            _dollar_dollar = msg
            _t1728 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1294 = (_t1728, _dollar_dollar[0].value,)
            assert fields1294 is not None
            unwrapped_fields1295 = fields1294
            self.write("(")
            self.indent()
            field1296 = unwrapped_fields1295[0]
            self.pretty_bindings(field1296)
            self.newline()
            field1297 = unwrapped_fields1295[1]
            self.pretty_formula(field1297)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1305 = self._try_flat(msg, self.pretty_break)
        if flat1305 is not None:
            assert flat1305 is not None
            self.write(flat1305)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1729 = _dollar_dollar.attrs
            else:
                _t1729 = None
            fields1299 = (_dollar_dollar.name, _dollar_dollar.body, _t1729,)
            assert fields1299 is not None
            unwrapped_fields1300 = fields1299
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1301 = unwrapped_fields1300[0]
            self.pretty_relation_id(field1301)
            self.newline()
            field1302 = unwrapped_fields1300[1]
            self.pretty_abstraction(field1302)
            field1303 = unwrapped_fields1300[2]
            if field1303 is not None:
                self.newline()
                assert field1303 is not None
                opt_val1304 = field1303
                self.pretty_attrs(opt_val1304)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1313 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1313 is not None:
            assert flat1313 is not None
            self.write(flat1313)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1730 = _dollar_dollar.attrs
            else:
                _t1730 = None
            fields1306 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1730,)
            assert fields1306 is not None
            unwrapped_fields1307 = fields1306
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1308 = unwrapped_fields1307[0]
            self.pretty_monoid(field1308)
            self.newline()
            field1309 = unwrapped_fields1307[1]
            self.pretty_relation_id(field1309)
            self.newline()
            field1310 = unwrapped_fields1307[2]
            self.pretty_abstraction_with_arity(field1310)
            field1311 = unwrapped_fields1307[3]
            if field1311 is not None:
                self.newline()
                assert field1311 is not None
                opt_val1312 = field1311
                self.pretty_attrs(opt_val1312)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1322 = self._try_flat(msg, self.pretty_monoid)
        if flat1322 is not None:
            assert flat1322 is not None
            self.write(flat1322)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1731 = _dollar_dollar.or_monoid
            else:
                _t1731 = None
            deconstruct_result1320 = _t1731
            if deconstruct_result1320 is not None:
                assert deconstruct_result1320 is not None
                unwrapped1321 = deconstruct_result1320
                self.pretty_or_monoid(unwrapped1321)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1732 = _dollar_dollar.min_monoid
                else:
                    _t1732 = None
                deconstruct_result1318 = _t1732
                if deconstruct_result1318 is not None:
                    assert deconstruct_result1318 is not None
                    unwrapped1319 = deconstruct_result1318
                    self.pretty_min_monoid(unwrapped1319)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1733 = _dollar_dollar.max_monoid
                    else:
                        _t1733 = None
                    deconstruct_result1316 = _t1733
                    if deconstruct_result1316 is not None:
                        assert deconstruct_result1316 is not None
                        unwrapped1317 = deconstruct_result1316
                        self.pretty_max_monoid(unwrapped1317)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1734 = _dollar_dollar.sum_monoid
                        else:
                            _t1734 = None
                        deconstruct_result1314 = _t1734
                        if deconstruct_result1314 is not None:
                            assert deconstruct_result1314 is not None
                            unwrapped1315 = deconstruct_result1314
                            self.pretty_sum_monoid(unwrapped1315)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1323 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1326 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1326 is not None:
            assert flat1326 is not None
            self.write(flat1326)
            return None
        else:
            _dollar_dollar = msg
            fields1324 = _dollar_dollar.type
            assert fields1324 is not None
            unwrapped_fields1325 = fields1324
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1325)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1329 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1329 is not None:
            assert flat1329 is not None
            self.write(flat1329)
            return None
        else:
            _dollar_dollar = msg
            fields1327 = _dollar_dollar.type
            assert fields1327 is not None
            unwrapped_fields1328 = fields1327
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1328)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1332 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1332 is not None:
            assert flat1332 is not None
            self.write(flat1332)
            return None
        else:
            _dollar_dollar = msg
            fields1330 = _dollar_dollar.type
            assert fields1330 is not None
            unwrapped_fields1331 = fields1330
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1331)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1340 = self._try_flat(msg, self.pretty_monus_def)
        if flat1340 is not None:
            assert flat1340 is not None
            self.write(flat1340)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1735 = _dollar_dollar.attrs
            else:
                _t1735 = None
            fields1333 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1735,)
            assert fields1333 is not None
            unwrapped_fields1334 = fields1333
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1335 = unwrapped_fields1334[0]
            self.pretty_monoid(field1335)
            self.newline()
            field1336 = unwrapped_fields1334[1]
            self.pretty_relation_id(field1336)
            self.newline()
            field1337 = unwrapped_fields1334[2]
            self.pretty_abstraction_with_arity(field1337)
            field1338 = unwrapped_fields1334[3]
            if field1338 is not None:
                self.newline()
                assert field1338 is not None
                opt_val1339 = field1338
                self.pretty_attrs(opt_val1339)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1347 = self._try_flat(msg, self.pretty_constraint)
        if flat1347 is not None:
            assert flat1347 is not None
            self.write(flat1347)
            return None
        else:
            _dollar_dollar = msg
            fields1341 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1341 is not None
            unwrapped_fields1342 = fields1341
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1343 = unwrapped_fields1342[0]
            self.pretty_relation_id(field1343)
            self.newline()
            field1344 = unwrapped_fields1342[1]
            self.pretty_abstraction(field1344)
            self.newline()
            field1345 = unwrapped_fields1342[2]
            self.pretty_functional_dependency_keys(field1345)
            self.newline()
            field1346 = unwrapped_fields1342[3]
            self.pretty_functional_dependency_values(field1346)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1351 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1351 is not None:
            assert flat1351 is not None
            self.write(flat1351)
            return None
        else:
            fields1348 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1348) == 0:
                self.newline()
                for i1350, elem1349 in enumerate(fields1348):
                    if (i1350 > 0):
                        self.newline()
                    self.pretty_var(elem1349)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1355 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1355 is not None:
            assert flat1355 is not None
            self.write(flat1355)
            return None
        else:
            fields1352 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1352) == 0:
                self.newline()
                for i1354, elem1353 in enumerate(fields1352):
                    if (i1354 > 0):
                        self.newline()
                    self.pretty_var(elem1353)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1364 = self._try_flat(msg, self.pretty_data)
        if flat1364 is not None:
            assert flat1364 is not None
            self.write(flat1364)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1736 = _dollar_dollar.edb
            else:
                _t1736 = None
            deconstruct_result1362 = _t1736
            if deconstruct_result1362 is not None:
                assert deconstruct_result1362 is not None
                unwrapped1363 = deconstruct_result1362
                self.pretty_edb(unwrapped1363)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1737 = _dollar_dollar.betree_relation
                else:
                    _t1737 = None
                deconstruct_result1360 = _t1737
                if deconstruct_result1360 is not None:
                    assert deconstruct_result1360 is not None
                    unwrapped1361 = deconstruct_result1360
                    self.pretty_betree_relation(unwrapped1361)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1738 = _dollar_dollar.csv_data
                    else:
                        _t1738 = None
                    deconstruct_result1358 = _t1738
                    if deconstruct_result1358 is not None:
                        assert deconstruct_result1358 is not None
                        unwrapped1359 = deconstruct_result1358
                        self.pretty_csv_data(unwrapped1359)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1739 = _dollar_dollar.iceberg_data
                        else:
                            _t1739 = None
                        deconstruct_result1356 = _t1739
                        if deconstruct_result1356 is not None:
                            assert deconstruct_result1356 is not None
                            unwrapped1357 = deconstruct_result1356
                            self.pretty_iceberg_data(unwrapped1357)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1370 = self._try_flat(msg, self.pretty_edb)
        if flat1370 is not None:
            assert flat1370 is not None
            self.write(flat1370)
            return None
        else:
            _dollar_dollar = msg
            fields1365 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1365 is not None
            unwrapped_fields1366 = fields1365
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1367 = unwrapped_fields1366[0]
            self.pretty_relation_id(field1367)
            self.newline()
            field1368 = unwrapped_fields1366[1]
            self.pretty_edb_path(field1368)
            self.newline()
            field1369 = unwrapped_fields1366[2]
            self.pretty_edb_types(field1369)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1374 = self._try_flat(msg, self.pretty_edb_path)
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
                self.write(self.format_string_value(elem1372))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1378 = self._try_flat(msg, self.pretty_edb_types)
        if flat1378 is not None:
            assert flat1378 is not None
            self.write(flat1378)
            return None
        else:
            fields1375 = msg
            self.write("[")
            self.indent()
            for i1377, elem1376 in enumerate(fields1375):
                if (i1377 > 0):
                    self.newline()
                self.pretty_type(elem1376)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1383 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1383 is not None:
            assert flat1383 is not None
            self.write(flat1383)
            return None
        else:
            _dollar_dollar = msg
            fields1379 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1379 is not None
            unwrapped_fields1380 = fields1379
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1381 = unwrapped_fields1380[0]
            self.pretty_relation_id(field1381)
            self.newline()
            field1382 = unwrapped_fields1380[1]
            self.pretty_betree_info(field1382)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1389 = self._try_flat(msg, self.pretty_betree_info)
        if flat1389 is not None:
            assert flat1389 is not None
            self.write(flat1389)
            return None
        else:
            _dollar_dollar = msg
            _t1740 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1384 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1740,)
            assert fields1384 is not None
            unwrapped_fields1385 = fields1384
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1386 = unwrapped_fields1385[0]
            self.pretty_betree_info_key_types(field1386)
            self.newline()
            field1387 = unwrapped_fields1385[1]
            self.pretty_betree_info_value_types(field1387)
            self.newline()
            field1388 = unwrapped_fields1385[2]
            self.pretty_config_dict(field1388)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1393 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1393 is not None:
            assert flat1393 is not None
            self.write(flat1393)
            return None
        else:
            fields1390 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1390) == 0:
                self.newline()
                for i1392, elem1391 in enumerate(fields1390):
                    if (i1392 > 0):
                        self.newline()
                    self.pretty_type(elem1391)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1397 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1397 is not None:
            assert flat1397 is not None
            self.write(flat1397)
            return None
        else:
            fields1394 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1394) == 0:
                self.newline()
                for i1396, elem1395 in enumerate(fields1394):
                    if (i1396 > 0):
                        self.newline()
                    self.pretty_type(elem1395)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1404 = self._try_flat(msg, self.pretty_csv_data)
        if flat1404 is not None:
            assert flat1404 is not None
            self.write(flat1404)
            return None
        else:
            _dollar_dollar = msg
            fields1398 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1398 is not None
            unwrapped_fields1399 = fields1398
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1400 = unwrapped_fields1399[0]
            self.pretty_csvlocator(field1400)
            self.newline()
            field1401 = unwrapped_fields1399[1]
            self.pretty_csv_config(field1401)
            self.newline()
            field1402 = unwrapped_fields1399[2]
            self.pretty_gnf_columns(field1402)
            self.newline()
            field1403 = unwrapped_fields1399[3]
            self.pretty_csv_asof(field1403)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1411 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1411 is not None:
            assert flat1411 is not None
            self.write(flat1411)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1741 = _dollar_dollar.paths
            else:
                _t1741 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1742 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1742 = None
            fields1405 = (_t1741, _t1742,)
            assert fields1405 is not None
            unwrapped_fields1406 = fields1405
            self.write("(csv_locator")
            self.indent_sexp()
            field1407 = unwrapped_fields1406[0]
            if field1407 is not None:
                self.newline()
                assert field1407 is not None
                opt_val1408 = field1407
                self.pretty_csv_locator_paths(opt_val1408)
            field1409 = unwrapped_fields1406[1]
            if field1409 is not None:
                self.newline()
                assert field1409 is not None
                opt_val1410 = field1409
                self.pretty_csv_locator_inline_data(opt_val1410)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1415 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1415 is not None:
            assert flat1415 is not None
            self.write(flat1415)
            return None
        else:
            fields1412 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1412) == 0:
                self.newline()
                for i1414, elem1413 in enumerate(fields1412):
                    if (i1414 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1413))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1417 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1417 is not None:
            assert flat1417 is not None
            self.write(flat1417)
            return None
        else:
            fields1416 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1416))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1423 = self._try_flat(msg, self.pretty_csv_config)
        if flat1423 is not None:
            assert flat1423 is not None
            self.write(flat1423)
            return None
        else:
            _dollar_dollar = msg
            _t1743 = self.deconstruct_csv_config(_dollar_dollar)
            _t1744 = self.deconstruct_csv_storage_integration_optional(_dollar_dollar)
            fields1418 = (_t1743, _t1744,)
            assert fields1418 is not None
            unwrapped_fields1419 = fields1418
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            field1420 = unwrapped_fields1419[0]
            self.pretty_config_dict(field1420)
            field1421 = unwrapped_fields1419[1]
            if field1421 is not None:
                self.newline()
                assert field1421 is not None
                opt_val1422 = field1421
                self.pretty__storage_integration(opt_val1422)
            self.dedent()
            self.write(")")

    def pretty__storage_integration(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat1425 = self._try_flat(msg, self.pretty__storage_integration)
        if flat1425 is not None:
            assert flat1425 is not None
            self.write(flat1425)
            return None
        else:
            fields1424 = msg
            self.write("(storage_integration")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(fields1424)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1429 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1429 is not None:
            assert flat1429 is not None
            self.write(flat1429)
            return None
        else:
            fields1426 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1426) == 0:
                self.newline()
                for i1428, elem1427 in enumerate(fields1426):
                    if (i1428 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1427)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1438 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1438 is not None:
            assert flat1438 is not None
            self.write(flat1438)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1745 = _dollar_dollar.target_id
            else:
                _t1745 = None
            fields1430 = (_dollar_dollar.column_path, _t1745, _dollar_dollar.types,)
            assert fields1430 is not None
            unwrapped_fields1431 = fields1430
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1432 = unwrapped_fields1431[0]
            self.pretty_gnf_column_path(field1432)
            field1433 = unwrapped_fields1431[1]
            if field1433 is not None:
                self.newline()
                assert field1433 is not None
                opt_val1434 = field1433
                self.pretty_relation_id(opt_val1434)
            self.newline()
            self.write("[")
            field1435 = unwrapped_fields1431[2]
            for i1437, elem1436 in enumerate(field1435):
                if (i1437 > 0):
                    self.newline()
                self.pretty_type(elem1436)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1445 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1445 is not None:
            assert flat1445 is not None
            self.write(flat1445)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1746 = _dollar_dollar[0]
            else:
                _t1746 = None
            deconstruct_result1443 = _t1746
            if deconstruct_result1443 is not None:
                assert deconstruct_result1443 is not None
                unwrapped1444 = deconstruct_result1443
                self.write(self.format_string_value(unwrapped1444))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1747 = _dollar_dollar
                else:
                    _t1747 = None
                deconstruct_result1439 = _t1747
                if deconstruct_result1439 is not None:
                    assert deconstruct_result1439 is not None
                    unwrapped1440 = deconstruct_result1439
                    self.write("[")
                    self.indent()
                    for i1442, elem1441 in enumerate(unwrapped1440):
                        if (i1442 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1441))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1447 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1447 is not None:
            assert flat1447 is not None
            self.write(flat1447)
            return None
        else:
            fields1446 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1446))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1458 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1458 is not None:
            assert flat1458 is not None
            self.write(flat1458)
            return None
        else:
            _dollar_dollar = msg
            _t1748 = self.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
            _t1749 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1448 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1748, _t1749, _dollar_dollar.returns_delta,)
            assert fields1448 is not None
            unwrapped_fields1449 = fields1448
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1450 = unwrapped_fields1449[0]
            self.pretty_iceberg_locator(field1450)
            self.newline()
            field1451 = unwrapped_fields1449[1]
            self.pretty_iceberg_catalog_config(field1451)
            self.newline()
            field1452 = unwrapped_fields1449[2]
            self.pretty_gnf_columns(field1452)
            field1453 = unwrapped_fields1449[3]
            if field1453 is not None:
                self.newline()
                assert field1453 is not None
                opt_val1454 = field1453
                self.pretty_iceberg_from_snapshot(opt_val1454)
            field1455 = unwrapped_fields1449[4]
            if field1455 is not None:
                self.newline()
                assert field1455 is not None
                opt_val1456 = field1455
                self.pretty_iceberg_to_snapshot(opt_val1456)
            self.newline()
            field1457 = unwrapped_fields1449[5]
            self.pretty_boolean_value(field1457)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1464 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1464 is not None:
            assert flat1464 is not None
            self.write(flat1464)
            return None
        else:
            _dollar_dollar = msg
            fields1459 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1459 is not None
            unwrapped_fields1460 = fields1459
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            field1461 = unwrapped_fields1460[0]
            self.pretty_iceberg_locator_table_name(field1461)
            self.newline()
            field1462 = unwrapped_fields1460[1]
            self.pretty_iceberg_locator_namespace(field1462)
            self.newline()
            field1463 = unwrapped_fields1460[2]
            self.pretty_iceberg_locator_warehouse(field1463)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_table_name(self, msg: str):
        flat1466 = self._try_flat(msg, self.pretty_iceberg_locator_table_name)
        if flat1466 is not None:
            assert flat1466 is not None
            self.write(flat1466)
            return None
        else:
            fields1465 = msg
            self.write("(table_name")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1465))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_namespace(self, msg: Sequence[str]):
        flat1470 = self._try_flat(msg, self.pretty_iceberg_locator_namespace)
        if flat1470 is not None:
            assert flat1470 is not None
            self.write(flat1470)
            return None
        else:
            fields1467 = msg
            self.write("(namespace")
            self.indent_sexp()
            if not len(fields1467) == 0:
                self.newline()
                for i1469, elem1468 in enumerate(fields1467):
                    if (i1469 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1468))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_warehouse(self, msg: str):
        flat1472 = self._try_flat(msg, self.pretty_iceberg_locator_warehouse)
        if flat1472 is not None:
            assert flat1472 is not None
            self.write(flat1472)
            return None
        else:
            fields1471 = msg
            self.write("(warehouse")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1471))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1480 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1480 is not None:
            assert flat1480 is not None
            self.write(flat1480)
            return None
        else:
            _dollar_dollar = msg
            _t1750 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1473 = (_dollar_dollar.catalog_uri, _t1750, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1473 is not None
            unwrapped_fields1474 = fields1473
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            field1475 = unwrapped_fields1474[0]
            self.pretty_iceberg_catalog_uri(field1475)
            field1476 = unwrapped_fields1474[1]
            if field1476 is not None:
                self.newline()
                assert field1476 is not None
                opt_val1477 = field1476
                self.pretty_iceberg_catalog_config_scope(opt_val1477)
            self.newline()
            field1478 = unwrapped_fields1474[2]
            self.pretty_iceberg_properties(field1478)
            self.newline()
            field1479 = unwrapped_fields1474[3]
            self.pretty_iceberg_auth_properties(field1479)
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_uri(self, msg: str):
        flat1482 = self._try_flat(msg, self.pretty_iceberg_catalog_uri)
        if flat1482 is not None:
            assert flat1482 is not None
            self.write(flat1482)
            return None
        else:
            fields1481 = msg
            self.write("(catalog_uri")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1481))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1484 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1484 is not None:
            assert flat1484 is not None
            self.write(flat1484)
            return None
        else:
            fields1483 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1483))
            self.dedent()
            self.write(")")

    def pretty_iceberg_properties(self, msg: Sequence[tuple[str, str]]):
        flat1488 = self._try_flat(msg, self.pretty_iceberg_properties)
        if flat1488 is not None:
            assert flat1488 is not None
            self.write(flat1488)
            return None
        else:
            fields1485 = msg
            self.write("(properties")
            self.indent_sexp()
            if not len(fields1485) == 0:
                self.newline()
                for i1487, elem1486 in enumerate(fields1485):
                    if (i1487 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1486)
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1493 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1493 is not None:
            assert flat1493 is not None
            self.write(flat1493)
            return None
        else:
            _dollar_dollar = msg
            fields1489 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1489 is not None
            unwrapped_fields1490 = fields1489
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1491 = unwrapped_fields1490[0]
            self.write(self.format_string_value(field1491))
            self.newline()
            field1492 = unwrapped_fields1490[1]
            self.write(self.format_string_value(field1492))
            self.dedent()
            self.write(")")

    def pretty_iceberg_auth_properties(self, msg: Sequence[tuple[str, str]]):
        flat1497 = self._try_flat(msg, self.pretty_iceberg_auth_properties)
        if flat1497 is not None:
            assert flat1497 is not None
            self.write(flat1497)
            return None
        else:
            fields1494 = msg
            self.write("(auth_properties")
            self.indent_sexp()
            if not len(fields1494) == 0:
                self.newline()
                for i1496, elem1495 in enumerate(fields1494):
                    if (i1496 > 0):
                        self.newline()
                    self.pretty_iceberg_masked_property_entry(elem1495)
            self.dedent()
            self.write(")")

    def pretty_iceberg_masked_property_entry(self, msg: tuple[str, str]):
        flat1502 = self._try_flat(msg, self.pretty_iceberg_masked_property_entry)
        if flat1502 is not None:
            assert flat1502 is not None
            self.write(flat1502)
            return None
        else:
            _dollar_dollar = msg
            _t1751 = self.mask_secret_value(_dollar_dollar)
            fields1498 = (_dollar_dollar[0], _t1751,)
            assert fields1498 is not None
            unwrapped_fields1499 = fields1498
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1500 = unwrapped_fields1499[0]
            self.write(self.format_string_value(field1500))
            self.newline()
            field1501 = unwrapped_fields1499[1]
            self.write(self.format_string_value(field1501))
            self.dedent()
            self.write(")")

    def pretty_iceberg_from_snapshot(self, msg: str):
        flat1504 = self._try_flat(msg, self.pretty_iceberg_from_snapshot)
        if flat1504 is not None:
            assert flat1504 is not None
            self.write(flat1504)
            return None
        else:
            fields1503 = msg
            self.write("(from_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1503))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1506 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1506 is not None:
            assert flat1506 is not None
            self.write(flat1506)
            return None
        else:
            fields1505 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1505))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1509 = self._try_flat(msg, self.pretty_undefine)
        if flat1509 is not None:
            assert flat1509 is not None
            self.write(flat1509)
            return None
        else:
            _dollar_dollar = msg
            fields1507 = _dollar_dollar.fragment_id
            assert fields1507 is not None
            unwrapped_fields1508 = fields1507
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1508)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1514 = self._try_flat(msg, self.pretty_context)
        if flat1514 is not None:
            assert flat1514 is not None
            self.write(flat1514)
            return None
        else:
            _dollar_dollar = msg
            fields1510 = _dollar_dollar.relations
            assert fields1510 is not None
            unwrapped_fields1511 = fields1510
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1511) == 0:
                self.newline()
                for i1513, elem1512 in enumerate(unwrapped_fields1511):
                    if (i1513 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1512)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1521 = self._try_flat(msg, self.pretty_snapshot)
        if flat1521 is not None:
            assert flat1521 is not None
            self.write(flat1521)
            return None
        else:
            _dollar_dollar = msg
            fields1515 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
            assert fields1515 is not None
            unwrapped_fields1516 = fields1515
            self.write("(snapshot")
            self.indent_sexp()
            self.newline()
            field1517 = unwrapped_fields1516[0]
            self.pretty_edb_path(field1517)
            field1518 = unwrapped_fields1516[1]
            if not len(field1518) == 0:
                self.newline()
                for i1520, elem1519 in enumerate(field1518):
                    if (i1520 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1519)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1526 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1526 is not None:
            assert flat1526 is not None
            self.write(flat1526)
            return None
        else:
            _dollar_dollar = msg
            fields1522 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1522 is not None
            unwrapped_fields1523 = fields1522
            field1524 = unwrapped_fields1523[0]
            self.pretty_edb_path(field1524)
            self.write(" ")
            field1525 = unwrapped_fields1523[1]
            self.pretty_relation_id(field1525)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1530 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1530 is not None:
            assert flat1530 is not None
            self.write(flat1530)
            return None
        else:
            fields1527 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1527) == 0:
                self.newline()
                for i1529, elem1528 in enumerate(fields1527):
                    if (i1529 > 0):
                        self.newline()
                    self.pretty_read(elem1528)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1543 = self._try_flat(msg, self.pretty_read)
        if flat1543 is not None:
            assert flat1543 is not None
            self.write(flat1543)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1752 = _dollar_dollar.demand
            else:
                _t1752 = None
            deconstruct_result1541 = _t1752
            if deconstruct_result1541 is not None:
                assert deconstruct_result1541 is not None
                unwrapped1542 = deconstruct_result1541
                self.pretty_demand(unwrapped1542)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1753 = _dollar_dollar.output
                else:
                    _t1753 = None
                deconstruct_result1539 = _t1753
                if deconstruct_result1539 is not None:
                    assert deconstruct_result1539 is not None
                    unwrapped1540 = deconstruct_result1539
                    self.pretty_output(unwrapped1540)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1754 = _dollar_dollar.what_if
                    else:
                        _t1754 = None
                    deconstruct_result1537 = _t1754
                    if deconstruct_result1537 is not None:
                        assert deconstruct_result1537 is not None
                        unwrapped1538 = deconstruct_result1537
                        self.pretty_what_if(unwrapped1538)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1755 = _dollar_dollar.abort
                        else:
                            _t1755 = None
                        deconstruct_result1535 = _t1755
                        if deconstruct_result1535 is not None:
                            assert deconstruct_result1535 is not None
                            unwrapped1536 = deconstruct_result1535
                            self.pretty_abort(unwrapped1536)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1756 = _dollar_dollar.export
                            else:
                                _t1756 = None
                            deconstruct_result1533 = _t1756
                            if deconstruct_result1533 is not None:
                                assert deconstruct_result1533 is not None
                                unwrapped1534 = deconstruct_result1533
                                self.pretty_export(unwrapped1534)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("export_output"):
                                    _t1757 = _dollar_dollar.export_output
                                else:
                                    _t1757 = None
                                deconstruct_result1531 = _t1757
                                if deconstruct_result1531 is not None:
                                    assert deconstruct_result1531 is not None
                                    unwrapped1532 = deconstruct_result1531
                                    self.pretty_export_output(unwrapped1532)
                                else:
                                    raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1546 = self._try_flat(msg, self.pretty_demand)
        if flat1546 is not None:
            assert flat1546 is not None
            self.write(flat1546)
            return None
        else:
            _dollar_dollar = msg
            fields1544 = _dollar_dollar.relation_id
            assert fields1544 is not None
            unwrapped_fields1545 = fields1544
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1545)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1551 = self._try_flat(msg, self.pretty_output)
        if flat1551 is not None:
            assert flat1551 is not None
            self.write(flat1551)
            return None
        else:
            _dollar_dollar = msg
            fields1547 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1547 is not None
            unwrapped_fields1548 = fields1547
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1549 = unwrapped_fields1548[0]
            self.pretty_name(field1549)
            self.newline()
            field1550 = unwrapped_fields1548[1]
            self.pretty_relation_id(field1550)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1556 = self._try_flat(msg, self.pretty_what_if)
        if flat1556 is not None:
            assert flat1556 is not None
            self.write(flat1556)
            return None
        else:
            _dollar_dollar = msg
            fields1552 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1552 is not None
            unwrapped_fields1553 = fields1552
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1554 = unwrapped_fields1553[0]
            self.pretty_name(field1554)
            self.newline()
            field1555 = unwrapped_fields1553[1]
            self.pretty_epoch(field1555)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1562 = self._try_flat(msg, self.pretty_abort)
        if flat1562 is not None:
            assert flat1562 is not None
            self.write(flat1562)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1758 = _dollar_dollar.name
            else:
                _t1758 = None
            fields1557 = (_t1758, _dollar_dollar.relation_id,)
            assert fields1557 is not None
            unwrapped_fields1558 = fields1557
            self.write("(abort")
            self.indent_sexp()
            field1559 = unwrapped_fields1558[0]
            if field1559 is not None:
                self.newline()
                assert field1559 is not None
                opt_val1560 = field1559
                self.pretty_name(opt_val1560)
            self.newline()
            field1561 = unwrapped_fields1558[1]
            self.pretty_relation_id(field1561)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1567 = self._try_flat(msg, self.pretty_export)
        if flat1567 is not None:
            assert flat1567 is not None
            self.write(flat1567)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1759 = _dollar_dollar.csv_config
            else:
                _t1759 = None
            deconstruct_result1565 = _t1759
            if deconstruct_result1565 is not None:
                assert deconstruct_result1565 is not None
                unwrapped1566 = deconstruct_result1565
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1566)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1760 = _dollar_dollar.iceberg_config
                else:
                    _t1760 = None
                deconstruct_result1563 = _t1760
                if deconstruct_result1563 is not None:
                    assert deconstruct_result1563 is not None
                    unwrapped1564 = deconstruct_result1563
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1564)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1578 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1578 is not None:
            assert flat1578 is not None
            self.write(flat1578)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1761 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1761 = None
            deconstruct_result1573 = _t1761
            if deconstruct_result1573 is not None:
                assert deconstruct_result1573 is not None
                unwrapped1574 = deconstruct_result1573
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1575 = unwrapped1574[0]
                self.pretty_export_csv_path(field1575)
                self.newline()
                field1576 = unwrapped1574[1]
                self.pretty_export_csv_source(field1576)
                self.newline()
                field1577 = unwrapped1574[2]
                self.pretty_csv_config(field1577)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1763 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1762 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1763,)
                else:
                    _t1762 = None
                deconstruct_result1568 = _t1762
                if deconstruct_result1568 is not None:
                    assert deconstruct_result1568 is not None
                    unwrapped1569 = deconstruct_result1568
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1570 = unwrapped1569[0]
                    self.pretty_export_csv_path(field1570)
                    self.newline()
                    field1571 = unwrapped1569[1]
                    self.pretty_export_csv_columns_list(field1571)
                    self.newline()
                    field1572 = unwrapped1569[2]
                    self.pretty_config_dict(field1572)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1580 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1580 is not None:
            assert flat1580 is not None
            self.write(flat1580)
            return None
        else:
            fields1579 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1579))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1587 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1587 is not None:
            assert flat1587 is not None
            self.write(flat1587)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1764 = _dollar_dollar.gnf_columns.columns
            else:
                _t1764 = None
            deconstruct_result1583 = _t1764
            if deconstruct_result1583 is not None:
                assert deconstruct_result1583 is not None
                unwrapped1584 = deconstruct_result1583
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1584) == 0:
                    self.newline()
                    for i1586, elem1585 in enumerate(unwrapped1584):
                        if (i1586 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1585)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1765 = _dollar_dollar.table_def
                else:
                    _t1765 = None
                deconstruct_result1581 = _t1765
                if deconstruct_result1581 is not None:
                    assert deconstruct_result1581 is not None
                    unwrapped1582 = deconstruct_result1581
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1582)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1592 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1592 is not None:
            assert flat1592 is not None
            self.write(flat1592)
            return None
        else:
            _dollar_dollar = msg
            fields1588 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1588 is not None
            unwrapped_fields1589 = fields1588
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1590 = unwrapped_fields1589[0]
            self.write(self.format_string_value(field1590))
            self.newline()
            field1591 = unwrapped_fields1589[1]
            self.pretty_relation_id(field1591)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1596 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1596 is not None:
            assert flat1596 is not None
            self.write(flat1596)
            return None
        else:
            fields1593 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1593) == 0:
                self.newline()
                for i1595, elem1594 in enumerate(fields1593):
                    if (i1595 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1594)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1605 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1605 is not None:
            assert flat1605 is not None
            self.write(flat1605)
            return None
        else:
            _dollar_dollar = msg
            _t1766 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1597 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sorted(_dollar_dollar.table_properties.items()), _t1766,)
            assert fields1597 is not None
            unwrapped_fields1598 = fields1597
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1599 = unwrapped_fields1598[0]
            self.pretty_iceberg_locator(field1599)
            self.newline()
            field1600 = unwrapped_fields1598[1]
            self.pretty_iceberg_catalog_config(field1600)
            self.newline()
            field1601 = unwrapped_fields1598[2]
            self.pretty_export_iceberg_table_def(field1601)
            self.newline()
            field1602 = unwrapped_fields1598[3]
            self.pretty_iceberg_table_properties(field1602)
            field1603 = unwrapped_fields1598[4]
            if field1603 is not None:
                self.newline()
                assert field1603 is not None
                opt_val1604 = field1603
                self.pretty_config_dict(opt_val1604)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_table_def(self, msg: logic_pb2.RelationId):
        flat1607 = self._try_flat(msg, self.pretty_export_iceberg_table_def)
        if flat1607 is not None:
            assert flat1607 is not None
            self.write(flat1607)
            return None
        else:
            fields1606 = msg
            self.write("(table_def")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1606)
            self.dedent()
            self.write(")")

    def pretty_iceberg_table_properties(self, msg: Sequence[tuple[str, str]]):
        flat1611 = self._try_flat(msg, self.pretty_iceberg_table_properties)
        if flat1611 is not None:
            assert flat1611 is not None
            self.write(flat1611)
            return None
        else:
            fields1608 = msg
            self.write("(table_properties")
            self.indent_sexp()
            if not len(fields1608) == 0:
                self.newline()
                for i1610, elem1609 in enumerate(fields1608):
                    if (i1610 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1609)
            self.dedent()
            self.write(")")

    def pretty_export_output(self, msg: transactions_pb2.ExportOutput):
        flat1616 = self._try_flat(msg, self.pretty_export_output)
        if flat1616 is not None:
            assert flat1616 is not None
            self.write(flat1616)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv"):
                _t1767 = (_dollar_dollar.name, _dollar_dollar.csv,)
            else:
                _t1767 = None
            fields1612 = _t1767
            assert fields1612 is not None
            unwrapped_fields1613 = fields1612
            self.write("(export_output")
            self.indent_sexp()
            self.newline()
            field1614 = unwrapped_fields1613[0]
            self.pretty_name(field1614)
            self.newline()
            field1615 = unwrapped_fields1613[1]
            self.pretty_export_csv_output(field1615)
            self.dedent()
            self.write(")")

    def pretty_export_csv_output(self, msg: transactions_pb2.ExportCSVOutput):
        flat1621 = self._try_flat(msg, self.pretty_export_csv_output)
        if flat1621 is not None:
            assert flat1621 is not None
            self.write(flat1621)
            return None
        else:
            _dollar_dollar = msg
            fields1617 = (_dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            assert fields1617 is not None
            unwrapped_fields1618 = fields1617
            self.write("(csv")
            self.indent_sexp()
            self.newline()
            field1619 = unwrapped_fields1618[0]
            self.pretty_export_csv_source(field1619)
            self.newline()
            field1620 = unwrapped_fields1618[1]
            self.pretty_csv_config(field1620)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1819 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1819)
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
