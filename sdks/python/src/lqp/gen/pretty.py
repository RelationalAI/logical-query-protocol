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

<<<<<<< HEAD
    def deconstruct_export_csv_output_location(self, msg: transactions_pb2.ExportCSVConfig) -> tuple[str, str]:
        return (msg.path, msg.transaction_output_name,)

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1755 = logic_pb2.Value(int32_value=v)
        return _t1755

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1756 = logic_pb2.Value(int_value=v)
        return _t1756

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1757 = logic_pb2.Value(float_value=v)
        return _t1757

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1758 = logic_pb2.Value(string_value=v)
        return _t1758

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1759 = logic_pb2.Value(boolean_value=v)
        return _t1759

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1760 = logic_pb2.Value(uint128_value=v)
        return _t1760
=======
    def deconstruct_csv_data_columns_optional(self, msg: logic_pb2.CSVData) -> Sequence[logic_pb2.GNFColumn] | None:
        if msg.HasField("relations"):
            return None
        else:
            _t1832 = None
        return msg.columns

    def deconstruct_csv_data_relations_optional(self, msg: logic_pb2.CSVData) -> logic_pb2.TargetRelations | None:
        if msg.HasField("relations"):
            assert msg.relations is not None
            return msg.relations
        else:
            _t1833 = None
        return None

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1834 = logic_pb2.Value(int32_value=v)
        return _t1834

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1835 = logic_pb2.Value(int_value=v)
        return _t1835

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1836 = logic_pb2.Value(float_value=v)
        return _t1836

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1837 = logic_pb2.Value(string_value=v)
        return _t1837

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1838 = logic_pb2.Value(boolean_value=v)
        return _t1838

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1839 = logic_pb2.Value(uint128_value=v)
        return _t1839
>>>>>>> origin/main

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
<<<<<<< HEAD
            _t1761 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1761,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1762 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1762,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1763 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1763,))
        _t1764 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1764,))
=======
            _t1840 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1840,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1841 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1841,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1842 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1842,))
        _t1843 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1843,))
>>>>>>> origin/main
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
<<<<<<< HEAD
        _t1765 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1765,))
        _t1766 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1766,))
        if msg.new_line != "":
            _t1767 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1767,))
        _t1768 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1768,))
        _t1769 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1769,))
        _t1770 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1770,))
        if msg.comment != "":
            _t1771 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1771,))
        for missing_string in msg.missing_strings:
            _t1772 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1772,))
        _t1773 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1773,))
        _t1774 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1774,))
        _t1775 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1775,))
        if msg.partition_size_mb != 0:
            _t1776 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1776,))
=======
        _t1844 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1844,))
        _t1845 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1845,))
        if msg.new_line != "":
            _t1846 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1846,))
        _t1847 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1847,))
        _t1848 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1848,))
        _t1849 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1849,))
        if msg.comment != "":
            _t1850 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1850,))
        for missing_string in msg.missing_strings:
            _t1851 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1851,))
        _t1852 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1852,))
        _t1853 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1853,))
        _t1854 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1854,))
        if msg.partition_size_mb != 0:
            _t1855 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1855,))
>>>>>>> origin/main
        return sorted(result)

    def deconstruct_csv_storage_integration_optional(self, msg: logic_pb2.CSVConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        if not msg.HasField("storage_integration"):
            return None
        else:
<<<<<<< HEAD
            _t1777 = None
=======
            _t1856 = None
>>>>>>> origin/main
        assert msg.storage_integration is not None
        si = msg.storage_integration
        result = []
        if si.provider != "":
<<<<<<< HEAD
            _t1778 = self._make_value_string(si.provider)
            result.append(("provider", _t1778,))
        if si.azure_sas_token != "":
            _t1779 = self._make_value_string("***")
            result.append(("azure_sas_token", _t1779,))
        if si.s3_region != "":
            _t1780 = self._make_value_string(si.s3_region)
            result.append(("s3_region", _t1780,))
        if si.s3_access_key_id != "":
            _t1781 = self._make_value_string("***")
            result.append(("s3_access_key_id", _t1781,))
        if si.s3_secret_access_key != "":
            _t1782 = self._make_value_string("***")
            result.append(("s3_secret_access_key", _t1782,))
=======
            _t1857 = self._make_value_string(si.provider)
            result.append(("provider", _t1857,))
        if si.azure_sas_token != "":
            _t1858 = self._make_value_string("***")
            result.append(("azure_sas_token", _t1858,))
        if si.s3_region != "":
            _t1859 = self._make_value_string(si.s3_region)
            result.append(("s3_region", _t1859,))
        if si.s3_access_key_id != "":
            _t1860 = self._make_value_string("***")
            result.append(("s3_access_key_id", _t1860,))
        if si.s3_secret_access_key != "":
            _t1861 = self._make_value_string("***")
            result.append(("s3_secret_access_key", _t1861,))
>>>>>>> origin/main
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
<<<<<<< HEAD
        _t1783 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1783,))
        _t1784 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1784,))
        _t1785 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1785,))
        _t1786 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1786,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1787 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1787,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1788 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1788,))
        _t1789 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1789,))
        _t1790 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1790,))
=======
        _t1862 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1862,))
        _t1863 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1863,))
        _t1864 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1864,))
        _t1865 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1865,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1866 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1866,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1867 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1867,))
        _t1868 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1868,))
        _t1869 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1869,))
>>>>>>> origin/main
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
<<<<<<< HEAD
            _t1791 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1791,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1792 = self._make_value_string(msg.compression)
            result.append(("compression", _t1792,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1793 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1793,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1794 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1794,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1795 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1795,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1796 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1796,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1797 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1797,))
=======
            _t1870 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1870,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1871 = self._make_value_string(msg.compression)
            result.append(("compression", _t1871,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1872 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1872,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1873 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1873,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1874 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1874,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1875 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1875,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1876 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1876,))
>>>>>>> origin/main
        return sorted(result)

    def mask_secret_value(self, pair: tuple[str, str]) -> str:
        return "***"

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
<<<<<<< HEAD
            _t1798 = None
=======
            _t1877 = None
>>>>>>> origin/main
        return None

    def deconstruct_iceberg_data_from_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.from_snapshot is not None
        if msg.from_snapshot != "":
            assert msg.from_snapshot is not None
            return msg.from_snapshot
        else:
<<<<<<< HEAD
            _t1799 = None
=======
            _t1878 = None
>>>>>>> origin/main
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
<<<<<<< HEAD
            _t1800 = None
=======
            _t1879 = None
>>>>>>> origin/main
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
<<<<<<< HEAD
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
=======
            _t1880 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1880,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1881 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1881,))
        if msg.compression != "":
            _t1882 = self._make_value_string(msg.compression)
            result.append(("compression", _t1882,))
        if len(result) == 0:
            return None
        else:
            _t1883 = None
>>>>>>> origin/main
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
<<<<<<< HEAD
            _t1805 = None
=======
            _t1884 = None
>>>>>>> origin/main
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
<<<<<<< HEAD
        flat813 = self._try_flat(msg, self.pretty_transaction)
        if flat813 is not None:
            assert flat813 is not None
            self.write(flat813)
=======
        flat851 = self._try_flat(msg, self.pretty_transaction)
        if flat851 is not None:
            assert flat851 is not None
            self.write(flat851)
>>>>>>> origin/main
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
<<<<<<< HEAD
                _t1608 = _dollar_dollar.configure
            else:
                _t1608 = None
            if _dollar_dollar.HasField("sync"):
                _t1609 = _dollar_dollar.sync
            else:
                _t1609 = None
            fields804 = (_t1608, _t1609, _dollar_dollar.epochs,)
            assert fields804 is not None
            unwrapped_fields805 = fields804
            self.write("(transaction")
            self.indent_sexp()
            field806 = unwrapped_fields805[0]
            if field806 is not None:
                self.newline()
                assert field806 is not None
                opt_val807 = field806
                self.pretty_configure(opt_val807)
            field808 = unwrapped_fields805[1]
            if field808 is not None:
                self.newline()
                assert field808 is not None
                opt_val809 = field808
                self.pretty_sync(opt_val809)
            field810 = unwrapped_fields805[2]
            if not len(field810) == 0:
                self.newline()
                for i812, elem811 in enumerate(field810):
                    if (i812 > 0):
                        self.newline()
                    self.pretty_epoch(elem811)
=======
                _t1684 = _dollar_dollar.configure
            else:
                _t1684 = None
            if _dollar_dollar.HasField("sync"):
                _t1685 = _dollar_dollar.sync
            else:
                _t1685 = None
            fields842 = (_t1684, _t1685, _dollar_dollar.epochs,)
            assert fields842 is not None
            unwrapped_fields843 = fields842
            self.write("(transaction")
            self.indent_sexp()
            field844 = unwrapped_fields843[0]
            if field844 is not None:
                self.newline()
                assert field844 is not None
                opt_val845 = field844
                self.pretty_configure(opt_val845)
            field846 = unwrapped_fields843[1]
            if field846 is not None:
                self.newline()
                assert field846 is not None
                opt_val847 = field846
                self.pretty_sync(opt_val847)
            field848 = unwrapped_fields843[2]
            if not len(field848) == 0:
                self.newline()
                for i850, elem849 in enumerate(field848):
                    if (i850 > 0):
                        self.newline()
                    self.pretty_epoch(elem849)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
<<<<<<< HEAD
        flat816 = self._try_flat(msg, self.pretty_configure)
        if flat816 is not None:
            assert flat816 is not None
            self.write(flat816)
            return None
        else:
            _dollar_dollar = msg
            _t1610 = self.deconstruct_configure(_dollar_dollar)
            fields814 = _t1610
            assert fields814 is not None
            unwrapped_fields815 = fields814
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields815)
=======
        flat854 = self._try_flat(msg, self.pretty_configure)
        if flat854 is not None:
            assert flat854 is not None
            self.write(flat854)
            return None
        else:
            _dollar_dollar = msg
            _t1686 = self.deconstruct_configure(_dollar_dollar)
            fields852 = _t1686
            assert fields852 is not None
            unwrapped_fields853 = fields852
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields853)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
<<<<<<< HEAD
        flat820 = self._try_flat(msg, self.pretty_config_dict)
        if flat820 is not None:
            assert flat820 is not None
            self.write(flat820)
            return None
        else:
            fields817 = msg
            self.write("{")
            self.indent()
            if not len(fields817) == 0:
                self.newline()
                for i819, elem818 in enumerate(fields817):
                    if (i819 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem818)
=======
        flat858 = self._try_flat(msg, self.pretty_config_dict)
        if flat858 is not None:
            assert flat858 is not None
            self.write(flat858)
            return None
        else:
            fields855 = msg
            self.write("{")
            self.indent()
            if not len(fields855) == 0:
                self.newline()
                for i857, elem856 in enumerate(fields855):
                    if (i857 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem856)
>>>>>>> origin/main
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
<<<<<<< HEAD
        flat825 = self._try_flat(msg, self.pretty_config_key_value)
        if flat825 is not None:
            assert flat825 is not None
            self.write(flat825)
            return None
        else:
            _dollar_dollar = msg
            fields821 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields821 is not None
            unwrapped_fields822 = fields821
            self.write(":")
            field823 = unwrapped_fields822[0]
            self.write(field823)
            self.write(" ")
            field824 = unwrapped_fields822[1]
            self.pretty_raw_value(field824)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat851 = self._try_flat(msg, self.pretty_raw_value)
        if flat851 is not None:
            assert flat851 is not None
            self.write(flat851)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1611 = _dollar_dollar.date_value
            else:
                _t1611 = None
            deconstruct_result849 = _t1611
            if deconstruct_result849 is not None:
                assert deconstruct_result849 is not None
                unwrapped850 = deconstruct_result849
                self.pretty_raw_date(unwrapped850)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1612 = _dollar_dollar.datetime_value
                else:
                    _t1612 = None
                deconstruct_result847 = _t1612
                if deconstruct_result847 is not None:
                    assert deconstruct_result847 is not None
                    unwrapped848 = deconstruct_result847
                    self.pretty_raw_datetime(unwrapped848)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1613 = _dollar_dollar.string_value
                    else:
                        _t1613 = None
                    deconstruct_result845 = _t1613
                    if deconstruct_result845 is not None:
                        assert deconstruct_result845 is not None
                        unwrapped846 = deconstruct_result845
                        self.write(self.format_string_value(unwrapped846))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1614 = _dollar_dollar.int32_value
                        else:
                            _t1614 = None
                        deconstruct_result843 = _t1614
                        if deconstruct_result843 is not None:
                            assert deconstruct_result843 is not None
                            unwrapped844 = deconstruct_result843
                            self.write((str(unwrapped844) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1615 = _dollar_dollar.int_value
                            else:
                                _t1615 = None
                            deconstruct_result841 = _t1615
                            if deconstruct_result841 is not None:
                                assert deconstruct_result841 is not None
                                unwrapped842 = deconstruct_result841
                                self.write(str(unwrapped842))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1616 = _dollar_dollar.float32_value
                                else:
                                    _t1616 = None
                                deconstruct_result839 = _t1616
                                if deconstruct_result839 is not None:
                                    assert deconstruct_result839 is not None
                                    unwrapped840 = deconstruct_result839
                                    self.write(self.format_float32_literal(unwrapped840))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1617 = _dollar_dollar.float_value
                                    else:
                                        _t1617 = None
                                    deconstruct_result837 = _t1617
                                    if deconstruct_result837 is not None:
                                        assert deconstruct_result837 is not None
                                        unwrapped838 = deconstruct_result837
                                        self.write(str(unwrapped838))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1618 = _dollar_dollar.uint32_value
                                        else:
                                            _t1618 = None
                                        deconstruct_result835 = _t1618
                                        if deconstruct_result835 is not None:
                                            assert deconstruct_result835 is not None
                                            unwrapped836 = deconstruct_result835
                                            self.write((str(unwrapped836) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1619 = _dollar_dollar.uint128_value
                                            else:
                                                _t1619 = None
                                            deconstruct_result833 = _t1619
                                            if deconstruct_result833 is not None:
                                                assert deconstruct_result833 is not None
                                                unwrapped834 = deconstruct_result833
                                                self.write(self.format_uint128(unwrapped834))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1620 = _dollar_dollar.int128_value
                                                else:
                                                    _t1620 = None
                                                deconstruct_result831 = _t1620
                                                if deconstruct_result831 is not None:
                                                    assert deconstruct_result831 is not None
                                                    unwrapped832 = deconstruct_result831
                                                    self.write(self.format_int128(unwrapped832))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1621 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1621 = None
                                                    deconstruct_result829 = _t1621
                                                    if deconstruct_result829 is not None:
                                                        assert deconstruct_result829 is not None
                                                        unwrapped830 = deconstruct_result829
                                                        self.write(self.format_decimal(unwrapped830))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1622 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1622 = None
                                                        deconstruct_result827 = _t1622
                                                        if deconstruct_result827 is not None:
                                                            assert deconstruct_result827 is not None
                                                            unwrapped828 = deconstruct_result827
                                                            self.pretty_boolean_value(unwrapped828)
                                                        else:
                                                            fields826 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat857 = self._try_flat(msg, self.pretty_raw_date)
        if flat857 is not None:
            assert flat857 is not None
            self.write(flat857)
            return None
        else:
            _dollar_dollar = msg
            fields852 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields852 is not None
            unwrapped_fields853 = fields852
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field854 = unwrapped_fields853[0]
            self.write(str(field854))
            self.newline()
            field855 = unwrapped_fields853[1]
            self.write(str(field855))
            self.newline()
            field856 = unwrapped_fields853[2]
            self.write(str(field856))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat868 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat868 is not None:
            assert flat868 is not None
            self.write(flat868)
            return None
        else:
            _dollar_dollar = msg
            fields858 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields858 is not None
            unwrapped_fields859 = fields858
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field860 = unwrapped_fields859[0]
            self.write(str(field860))
            self.newline()
            field861 = unwrapped_fields859[1]
            self.write(str(field861))
            self.newline()
            field862 = unwrapped_fields859[2]
            self.write(str(field862))
            self.newline()
            field863 = unwrapped_fields859[3]
            self.write(str(field863))
            self.newline()
            field864 = unwrapped_fields859[4]
            self.write(str(field864))
            self.newline()
            field865 = unwrapped_fields859[5]
            self.write(str(field865))
            field866 = unwrapped_fields859[6]
            if field866 is not None:
                self.newline()
                assert field866 is not None
                opt_val867 = field866
                self.write(str(opt_val867))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1623 = ()
        else:
            _t1623 = None
        deconstruct_result871 = _t1623
        if deconstruct_result871 is not None:
            assert deconstruct_result871 is not None
            unwrapped872 = deconstruct_result871
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1624 = ()
            else:
                _t1624 = None
            deconstruct_result869 = _t1624
            if deconstruct_result869 is not None:
                assert deconstruct_result869 is not None
                unwrapped870 = deconstruct_result869
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat877 = self._try_flat(msg, self.pretty_sync)
        if flat877 is not None:
            assert flat877 is not None
            self.write(flat877)
            return None
        else:
            _dollar_dollar = msg
            fields873 = _dollar_dollar.fragments
            assert fields873 is not None
            unwrapped_fields874 = fields873
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields874) == 0:
                self.newline()
                for i876, elem875 in enumerate(unwrapped_fields874):
                    if (i876 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem875)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat880 = self._try_flat(msg, self.pretty_fragment_id)
        if flat880 is not None:
            assert flat880 is not None
            self.write(flat880)
            return None
        else:
            _dollar_dollar = msg
            fields878 = self.fragment_id_to_string(_dollar_dollar)
            assert fields878 is not None
            unwrapped_fields879 = fields878
            self.write(":")
            self.write(unwrapped_fields879)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat887 = self._try_flat(msg, self.pretty_epoch)
        if flat887 is not None:
            assert flat887 is not None
            self.write(flat887)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1625 = _dollar_dollar.writes
            else:
                _t1625 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1626 = _dollar_dollar.reads
            else:
                _t1626 = None
            fields881 = (_t1625, _t1626,)
            assert fields881 is not None
            unwrapped_fields882 = fields881
            self.write("(epoch")
            self.indent_sexp()
            field883 = unwrapped_fields882[0]
            if field883 is not None:
                self.newline()
                assert field883 is not None
                opt_val884 = field883
                self.pretty_epoch_writes(opt_val884)
            field885 = unwrapped_fields882[1]
            if field885 is not None:
                self.newline()
                assert field885 is not None
                opt_val886 = field885
                self.pretty_epoch_reads(opt_val886)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat891 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat891 is not None:
            assert flat891 is not None
            self.write(flat891)
            return None
        else:
            fields888 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields888) == 0:
                self.newline()
                for i890, elem889 in enumerate(fields888):
                    if (i890 > 0):
                        self.newline()
                    self.pretty_write(elem889)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat900 = self._try_flat(msg, self.pretty_write)
        if flat900 is not None:
            assert flat900 is not None
            self.write(flat900)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1627 = _dollar_dollar.define
            else:
                _t1627 = None
            deconstruct_result898 = _t1627
            if deconstruct_result898 is not None:
                assert deconstruct_result898 is not None
                unwrapped899 = deconstruct_result898
                self.pretty_define(unwrapped899)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1628 = _dollar_dollar.undefine
                else:
                    _t1628 = None
                deconstruct_result896 = _t1628
                if deconstruct_result896 is not None:
                    assert deconstruct_result896 is not None
                    unwrapped897 = deconstruct_result896
                    self.pretty_undefine(unwrapped897)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1629 = _dollar_dollar.context
                    else:
                        _t1629 = None
                    deconstruct_result894 = _t1629
                    if deconstruct_result894 is not None:
                        assert deconstruct_result894 is not None
                        unwrapped895 = deconstruct_result894
                        self.pretty_context(unwrapped895)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1630 = _dollar_dollar.snapshot
                        else:
                            _t1630 = None
                        deconstruct_result892 = _t1630
                        if deconstruct_result892 is not None:
                            assert deconstruct_result892 is not None
                            unwrapped893 = deconstruct_result892
                            self.pretty_snapshot(unwrapped893)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat903 = self._try_flat(msg, self.pretty_define)
        if flat903 is not None:
            assert flat903 is not None
            self.write(flat903)
            return None
        else:
            _dollar_dollar = msg
            fields901 = _dollar_dollar.fragment
            assert fields901 is not None
            unwrapped_fields902 = fields901
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields902)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat910 = self._try_flat(msg, self.pretty_fragment)
        if flat910 is not None:
            assert flat910 is not None
            self.write(flat910)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields904 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields904 is not None
            unwrapped_fields905 = fields904
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field906 = unwrapped_fields905[0]
            self.pretty_new_fragment_id(field906)
            field907 = unwrapped_fields905[1]
            if not len(field907) == 0:
                self.newline()
                for i909, elem908 in enumerate(field907):
                    if (i909 > 0):
                        self.newline()
                    self.pretty_declaration(elem908)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat912 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat912 is not None:
            assert flat912 is not None
            self.write(flat912)
            return None
        else:
            fields911 = msg
            self.pretty_fragment_id(fields911)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat921 = self._try_flat(msg, self.pretty_declaration)
        if flat921 is not None:
            assert flat921 is not None
            self.write(flat921)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1631 = getattr(_dollar_dollar, 'def')
            else:
                _t1631 = None
            deconstruct_result919 = _t1631
            if deconstruct_result919 is not None:
                assert deconstruct_result919 is not None
                unwrapped920 = deconstruct_result919
                self.pretty_def(unwrapped920)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1632 = _dollar_dollar.algorithm
                else:
                    _t1632 = None
                deconstruct_result917 = _t1632
                if deconstruct_result917 is not None:
                    assert deconstruct_result917 is not None
                    unwrapped918 = deconstruct_result917
                    self.pretty_algorithm(unwrapped918)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1633 = _dollar_dollar.constraint
                    else:
                        _t1633 = None
                    deconstruct_result915 = _t1633
                    if deconstruct_result915 is not None:
                        assert deconstruct_result915 is not None
                        unwrapped916 = deconstruct_result915
                        self.pretty_constraint(unwrapped916)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1634 = _dollar_dollar.data
                        else:
                            _t1634 = None
                        deconstruct_result913 = _t1634
                        if deconstruct_result913 is not None:
                            assert deconstruct_result913 is not None
                            unwrapped914 = deconstruct_result913
                            self.pretty_data(unwrapped914)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat928 = self._try_flat(msg, self.pretty_def)
        if flat928 is not None:
            assert flat928 is not None
            self.write(flat928)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1635 = _dollar_dollar.attrs
            else:
                _t1635 = None
            fields922 = (_dollar_dollar.name, _dollar_dollar.body, _t1635,)
            assert fields922 is not None
            unwrapped_fields923 = fields922
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field924 = unwrapped_fields923[0]
            self.pretty_relation_id(field924)
            self.newline()
            field925 = unwrapped_fields923[1]
            self.pretty_abstraction(field925)
            field926 = unwrapped_fields923[2]
            if field926 is not None:
                self.newline()
                assert field926 is not None
                opt_val927 = field926
                self.pretty_attrs(opt_val927)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat933 = self._try_flat(msg, self.pretty_relation_id)
        if flat933 is not None:
            assert flat933 is not None
            self.write(flat933)
=======
        flat863 = self._try_flat(msg, self.pretty_config_key_value)
        if flat863 is not None:
            assert flat863 is not None
            self.write(flat863)
            return None
        else:
            _dollar_dollar = msg
            fields859 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields859 is not None
            unwrapped_fields860 = fields859
            self.write(":")
            field861 = unwrapped_fields860[0]
            self.write(field861)
            self.write(" ")
            field862 = unwrapped_fields860[1]
            self.pretty_raw_value(field862)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat889 = self._try_flat(msg, self.pretty_raw_value)
        if flat889 is not None:
            assert flat889 is not None
            self.write(flat889)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1687 = _dollar_dollar.date_value
            else:
                _t1687 = None
            deconstruct_result887 = _t1687
            if deconstruct_result887 is not None:
                assert deconstruct_result887 is not None
                unwrapped888 = deconstruct_result887
                self.pretty_raw_date(unwrapped888)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1688 = _dollar_dollar.datetime_value
                else:
                    _t1688 = None
                deconstruct_result885 = _t1688
                if deconstruct_result885 is not None:
                    assert deconstruct_result885 is not None
                    unwrapped886 = deconstruct_result885
                    self.pretty_raw_datetime(unwrapped886)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1689 = _dollar_dollar.string_value
                    else:
                        _t1689 = None
                    deconstruct_result883 = _t1689
                    if deconstruct_result883 is not None:
                        assert deconstruct_result883 is not None
                        unwrapped884 = deconstruct_result883
                        self.write(self.format_string_value(unwrapped884))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1690 = _dollar_dollar.int32_value
                        else:
                            _t1690 = None
                        deconstruct_result881 = _t1690
                        if deconstruct_result881 is not None:
                            assert deconstruct_result881 is not None
                            unwrapped882 = deconstruct_result881
                            self.write((str(unwrapped882) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1691 = _dollar_dollar.int_value
                            else:
                                _t1691 = None
                            deconstruct_result879 = _t1691
                            if deconstruct_result879 is not None:
                                assert deconstruct_result879 is not None
                                unwrapped880 = deconstruct_result879
                                self.write(str(unwrapped880))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1692 = _dollar_dollar.float32_value
                                else:
                                    _t1692 = None
                                deconstruct_result877 = _t1692
                                if deconstruct_result877 is not None:
                                    assert deconstruct_result877 is not None
                                    unwrapped878 = deconstruct_result877
                                    self.write(self.format_float32_literal(unwrapped878))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1693 = _dollar_dollar.float_value
                                    else:
                                        _t1693 = None
                                    deconstruct_result875 = _t1693
                                    if deconstruct_result875 is not None:
                                        assert deconstruct_result875 is not None
                                        unwrapped876 = deconstruct_result875
                                        self.write(str(unwrapped876))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1694 = _dollar_dollar.uint32_value
                                        else:
                                            _t1694 = None
                                        deconstruct_result873 = _t1694
                                        if deconstruct_result873 is not None:
                                            assert deconstruct_result873 is not None
                                            unwrapped874 = deconstruct_result873
                                            self.write((str(unwrapped874) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1695 = _dollar_dollar.uint128_value
                                            else:
                                                _t1695 = None
                                            deconstruct_result871 = _t1695
                                            if deconstruct_result871 is not None:
                                                assert deconstruct_result871 is not None
                                                unwrapped872 = deconstruct_result871
                                                self.write(self.format_uint128(unwrapped872))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1696 = _dollar_dollar.int128_value
                                                else:
                                                    _t1696 = None
                                                deconstruct_result869 = _t1696
                                                if deconstruct_result869 is not None:
                                                    assert deconstruct_result869 is not None
                                                    unwrapped870 = deconstruct_result869
                                                    self.write(self.format_int128(unwrapped870))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1697 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1697 = None
                                                    deconstruct_result867 = _t1697
                                                    if deconstruct_result867 is not None:
                                                        assert deconstruct_result867 is not None
                                                        unwrapped868 = deconstruct_result867
                                                        self.write(self.format_decimal(unwrapped868))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1698 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1698 = None
                                                        deconstruct_result865 = _t1698
                                                        if deconstruct_result865 is not None:
                                                            assert deconstruct_result865 is not None
                                                            unwrapped866 = deconstruct_result865
                                                            self.pretty_boolean_value(unwrapped866)
                                                        else:
                                                            fields864 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat895 = self._try_flat(msg, self.pretty_raw_date)
        if flat895 is not None:
            assert flat895 is not None
            self.write(flat895)
            return None
        else:
            _dollar_dollar = msg
            fields890 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields890 is not None
            unwrapped_fields891 = fields890
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field892 = unwrapped_fields891[0]
            self.write(str(field892))
            self.newline()
            field893 = unwrapped_fields891[1]
            self.write(str(field893))
            self.newline()
            field894 = unwrapped_fields891[2]
            self.write(str(field894))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat906 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat906 is not None:
            assert flat906 is not None
            self.write(flat906)
            return None
        else:
            _dollar_dollar = msg
            fields896 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields896 is not None
            unwrapped_fields897 = fields896
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field898 = unwrapped_fields897[0]
            self.write(str(field898))
            self.newline()
            field899 = unwrapped_fields897[1]
            self.write(str(field899))
            self.newline()
            field900 = unwrapped_fields897[2]
            self.write(str(field900))
            self.newline()
            field901 = unwrapped_fields897[3]
            self.write(str(field901))
            self.newline()
            field902 = unwrapped_fields897[4]
            self.write(str(field902))
            self.newline()
            field903 = unwrapped_fields897[5]
            self.write(str(field903))
            field904 = unwrapped_fields897[6]
            if field904 is not None:
                self.newline()
                assert field904 is not None
                opt_val905 = field904
                self.write(str(opt_val905))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1699 = ()
        else:
            _t1699 = None
        deconstruct_result909 = _t1699
        if deconstruct_result909 is not None:
            assert deconstruct_result909 is not None
            unwrapped910 = deconstruct_result909
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1700 = ()
            else:
                _t1700 = None
            deconstruct_result907 = _t1700
            if deconstruct_result907 is not None:
                assert deconstruct_result907 is not None
                unwrapped908 = deconstruct_result907
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat915 = self._try_flat(msg, self.pretty_sync)
        if flat915 is not None:
            assert flat915 is not None
            self.write(flat915)
            return None
        else:
            _dollar_dollar = msg
            fields911 = _dollar_dollar.fragments
            assert fields911 is not None
            unwrapped_fields912 = fields911
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields912) == 0:
                self.newline()
                for i914, elem913 in enumerate(unwrapped_fields912):
                    if (i914 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem913)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat918 = self._try_flat(msg, self.pretty_fragment_id)
        if flat918 is not None:
            assert flat918 is not None
            self.write(flat918)
            return None
        else:
            _dollar_dollar = msg
            fields916 = self.fragment_id_to_string(_dollar_dollar)
            assert fields916 is not None
            unwrapped_fields917 = fields916
            self.write(":")
            self.write(unwrapped_fields917)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat925 = self._try_flat(msg, self.pretty_epoch)
        if flat925 is not None:
            assert flat925 is not None
            self.write(flat925)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1701 = _dollar_dollar.writes
            else:
                _t1701 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1702 = _dollar_dollar.reads
            else:
                _t1702 = None
            fields919 = (_t1701, _t1702,)
            assert fields919 is not None
            unwrapped_fields920 = fields919
            self.write("(epoch")
            self.indent_sexp()
            field921 = unwrapped_fields920[0]
            if field921 is not None:
                self.newline()
                assert field921 is not None
                opt_val922 = field921
                self.pretty_epoch_writes(opt_val922)
            field923 = unwrapped_fields920[1]
            if field923 is not None:
                self.newline()
                assert field923 is not None
                opt_val924 = field923
                self.pretty_epoch_reads(opt_val924)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat929 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat929 is not None:
            assert flat929 is not None
            self.write(flat929)
            return None
        else:
            fields926 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields926) == 0:
                self.newline()
                for i928, elem927 in enumerate(fields926):
                    if (i928 > 0):
                        self.newline()
                    self.pretty_write(elem927)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat938 = self._try_flat(msg, self.pretty_write)
        if flat938 is not None:
            assert flat938 is not None
            self.write(flat938)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1703 = _dollar_dollar.define
            else:
                _t1703 = None
            deconstruct_result936 = _t1703
            if deconstruct_result936 is not None:
                assert deconstruct_result936 is not None
                unwrapped937 = deconstruct_result936
                self.pretty_define(unwrapped937)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1704 = _dollar_dollar.undefine
                else:
                    _t1704 = None
                deconstruct_result934 = _t1704
                if deconstruct_result934 is not None:
                    assert deconstruct_result934 is not None
                    unwrapped935 = deconstruct_result934
                    self.pretty_undefine(unwrapped935)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1705 = _dollar_dollar.context
                    else:
                        _t1705 = None
                    deconstruct_result932 = _t1705
                    if deconstruct_result932 is not None:
                        assert deconstruct_result932 is not None
                        unwrapped933 = deconstruct_result932
                        self.pretty_context(unwrapped933)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1706 = _dollar_dollar.snapshot
                        else:
                            _t1706 = None
                        deconstruct_result930 = _t1706
                        if deconstruct_result930 is not None:
                            assert deconstruct_result930 is not None
                            unwrapped931 = deconstruct_result930
                            self.pretty_snapshot(unwrapped931)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat941 = self._try_flat(msg, self.pretty_define)
        if flat941 is not None:
            assert flat941 is not None
            self.write(flat941)
            return None
        else:
            _dollar_dollar = msg
            fields939 = _dollar_dollar.fragment
            assert fields939 is not None
            unwrapped_fields940 = fields939
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields940)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat948 = self._try_flat(msg, self.pretty_fragment)
        if flat948 is not None:
            assert flat948 is not None
            self.write(flat948)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields942 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields942 is not None
            unwrapped_fields943 = fields942
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field944 = unwrapped_fields943[0]
            self.pretty_new_fragment_id(field944)
            field945 = unwrapped_fields943[1]
            if not len(field945) == 0:
                self.newline()
                for i947, elem946 in enumerate(field945):
                    if (i947 > 0):
                        self.newline()
                    self.pretty_declaration(elem946)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat950 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat950 is not None:
            assert flat950 is not None
            self.write(flat950)
            return None
        else:
            fields949 = msg
            self.pretty_fragment_id(fields949)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat959 = self._try_flat(msg, self.pretty_declaration)
        if flat959 is not None:
            assert flat959 is not None
            self.write(flat959)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1707 = getattr(_dollar_dollar, 'def')
            else:
                _t1707 = None
            deconstruct_result957 = _t1707
            if deconstruct_result957 is not None:
                assert deconstruct_result957 is not None
                unwrapped958 = deconstruct_result957
                self.pretty_def(unwrapped958)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1708 = _dollar_dollar.algorithm
                else:
                    _t1708 = None
                deconstruct_result955 = _t1708
                if deconstruct_result955 is not None:
                    assert deconstruct_result955 is not None
                    unwrapped956 = deconstruct_result955
                    self.pretty_algorithm(unwrapped956)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1709 = _dollar_dollar.constraint
                    else:
                        _t1709 = None
                    deconstruct_result953 = _t1709
                    if deconstruct_result953 is not None:
                        assert deconstruct_result953 is not None
                        unwrapped954 = deconstruct_result953
                        self.pretty_constraint(unwrapped954)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1710 = _dollar_dollar.data
                        else:
                            _t1710 = None
                        deconstruct_result951 = _t1710
                        if deconstruct_result951 is not None:
                            assert deconstruct_result951 is not None
                            unwrapped952 = deconstruct_result951
                            self.pretty_data(unwrapped952)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat966 = self._try_flat(msg, self.pretty_def)
        if flat966 is not None:
            assert flat966 is not None
            self.write(flat966)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1711 = _dollar_dollar.attrs
            else:
                _t1711 = None
            fields960 = (_dollar_dollar.name, _dollar_dollar.body, _t1711,)
            assert fields960 is not None
            unwrapped_fields961 = fields960
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field962 = unwrapped_fields961[0]
            self.pretty_relation_id(field962)
            self.newline()
            field963 = unwrapped_fields961[1]
            self.pretty_abstraction(field963)
            field964 = unwrapped_fields961[2]
            if field964 is not None:
                self.newline()
                assert field964 is not None
                opt_val965 = field964
                self.pretty_attrs(opt_val965)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat971 = self._try_flat(msg, self.pretty_relation_id)
        if flat971 is not None:
            assert flat971 is not None
            self.write(flat971)
>>>>>>> origin/main
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
<<<<<<< HEAD
                _t1637 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1636 = _t1637
            else:
                _t1636 = None
            deconstruct_result931 = _t1636
            if deconstruct_result931 is not None:
                assert deconstruct_result931 is not None
                unwrapped932 = deconstruct_result931
                self.write(":")
                self.write(unwrapped932)
            else:
                _dollar_dollar = msg
                _t1638 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result929 = _t1638
                if deconstruct_result929 is not None:
                    assert deconstruct_result929 is not None
                    unwrapped930 = deconstruct_result929
                    self.write(self.format_uint128(unwrapped930))
=======
                _t1713 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1712 = _t1713
            else:
                _t1712 = None
            deconstruct_result969 = _t1712
            if deconstruct_result969 is not None:
                assert deconstruct_result969 is not None
                unwrapped970 = deconstruct_result969
                self.write(":")
                self.write(unwrapped970)
            else:
                _dollar_dollar = msg
                _t1714 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result967 = _t1714
                if deconstruct_result967 is not None:
                    assert deconstruct_result967 is not None
                    unwrapped968 = deconstruct_result967
                    self.write(self.format_uint128(unwrapped968))
>>>>>>> origin/main
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
<<<<<<< HEAD
        flat938 = self._try_flat(msg, self.pretty_abstraction)
        if flat938 is not None:
            assert flat938 is not None
            self.write(flat938)
            return None
        else:
            _dollar_dollar = msg
            _t1639 = self.deconstruct_bindings(_dollar_dollar)
            fields934 = (_t1639, _dollar_dollar.value,)
            assert fields934 is not None
            unwrapped_fields935 = fields934
            self.write("(")
            self.indent()
            field936 = unwrapped_fields935[0]
            self.pretty_bindings(field936)
            self.newline()
            field937 = unwrapped_fields935[1]
            self.pretty_formula(field937)
=======
        flat976 = self._try_flat(msg, self.pretty_abstraction)
        if flat976 is not None:
            assert flat976 is not None
            self.write(flat976)
            return None
        else:
            _dollar_dollar = msg
            _t1715 = self.deconstruct_bindings(_dollar_dollar)
            fields972 = (_t1715, _dollar_dollar.value,)
            assert fields972 is not None
            unwrapped_fields973 = fields972
            self.write("(")
            self.indent()
            field974 = unwrapped_fields973[0]
            self.pretty_bindings(field974)
            self.newline()
            field975 = unwrapped_fields973[1]
            self.pretty_formula(field975)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
<<<<<<< HEAD
        flat946 = self._try_flat(msg, self.pretty_bindings)
        if flat946 is not None:
            assert flat946 is not None
            self.write(flat946)
=======
        flat984 = self._try_flat(msg, self.pretty_bindings)
        if flat984 is not None:
            assert flat984 is not None
            self.write(flat984)
>>>>>>> origin/main
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
<<<<<<< HEAD
                _t1640 = _dollar_dollar[1]
            else:
                _t1640 = None
            fields939 = (_dollar_dollar[0], _t1640,)
            assert fields939 is not None
            unwrapped_fields940 = fields939
            self.write("[")
            self.indent()
            field941 = unwrapped_fields940[0]
            for i943, elem942 in enumerate(field941):
                if (i943 > 0):
                    self.newline()
                self.pretty_binding(elem942)
            field944 = unwrapped_fields940[1]
            if field944 is not None:
                self.newline()
                assert field944 is not None
                opt_val945 = field944
                self.pretty_value_bindings(opt_val945)
=======
                _t1716 = _dollar_dollar[1]
            else:
                _t1716 = None
            fields977 = (_dollar_dollar[0], _t1716,)
            assert fields977 is not None
            unwrapped_fields978 = fields977
            self.write("[")
            self.indent()
            field979 = unwrapped_fields978[0]
            for i981, elem980 in enumerate(field979):
                if (i981 > 0):
                    self.newline()
                self.pretty_binding(elem980)
            field982 = unwrapped_fields978[1]
            if field982 is not None:
                self.newline()
                assert field982 is not None
                opt_val983 = field982
                self.pretty_value_bindings(opt_val983)
>>>>>>> origin/main
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
<<<<<<< HEAD
        flat951 = self._try_flat(msg, self.pretty_binding)
        if flat951 is not None:
            assert flat951 is not None
            self.write(flat951)
            return None
        else:
            _dollar_dollar = msg
            fields947 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields947 is not None
            unwrapped_fields948 = fields947
            field949 = unwrapped_fields948[0]
            self.write(field949)
            self.write("::")
            field950 = unwrapped_fields948[1]
            self.pretty_type(field950)

    def pretty_type(self, msg: logic_pb2.Type):
        flat980 = self._try_flat(msg, self.pretty_type)
        if flat980 is not None:
            assert flat980 is not None
            self.write(flat980)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1641 = _dollar_dollar.unspecified_type
            else:
                _t1641 = None
            deconstruct_result978 = _t1641
            if deconstruct_result978 is not None:
                assert deconstruct_result978 is not None
                unwrapped979 = deconstruct_result978
                self.pretty_unspecified_type(unwrapped979)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1642 = _dollar_dollar.string_type
                else:
                    _t1642 = None
                deconstruct_result976 = _t1642
                if deconstruct_result976 is not None:
                    assert deconstruct_result976 is not None
                    unwrapped977 = deconstruct_result976
                    self.pretty_string_type(unwrapped977)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1643 = _dollar_dollar.int_type
                    else:
                        _t1643 = None
                    deconstruct_result974 = _t1643
                    if deconstruct_result974 is not None:
                        assert deconstruct_result974 is not None
                        unwrapped975 = deconstruct_result974
                        self.pretty_int_type(unwrapped975)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1644 = _dollar_dollar.float_type
                        else:
                            _t1644 = None
                        deconstruct_result972 = _t1644
                        if deconstruct_result972 is not None:
                            assert deconstruct_result972 is not None
                            unwrapped973 = deconstruct_result972
                            self.pretty_float_type(unwrapped973)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1645 = _dollar_dollar.uint128_type
                            else:
                                _t1645 = None
                            deconstruct_result970 = _t1645
                            if deconstruct_result970 is not None:
                                assert deconstruct_result970 is not None
                                unwrapped971 = deconstruct_result970
                                self.pretty_uint128_type(unwrapped971)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1646 = _dollar_dollar.int128_type
                                else:
                                    _t1646 = None
                                deconstruct_result968 = _t1646
                                if deconstruct_result968 is not None:
                                    assert deconstruct_result968 is not None
                                    unwrapped969 = deconstruct_result968
                                    self.pretty_int128_type(unwrapped969)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1647 = _dollar_dollar.date_type
                                    else:
                                        _t1647 = None
                                    deconstruct_result966 = _t1647
                                    if deconstruct_result966 is not None:
                                        assert deconstruct_result966 is not None
                                        unwrapped967 = deconstruct_result966
                                        self.pretty_date_type(unwrapped967)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1648 = _dollar_dollar.datetime_type
                                        else:
                                            _t1648 = None
                                        deconstruct_result964 = _t1648
                                        if deconstruct_result964 is not None:
                                            assert deconstruct_result964 is not None
                                            unwrapped965 = deconstruct_result964
                                            self.pretty_datetime_type(unwrapped965)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1649 = _dollar_dollar.missing_type
                                            else:
                                                _t1649 = None
                                            deconstruct_result962 = _t1649
                                            if deconstruct_result962 is not None:
                                                assert deconstruct_result962 is not None
                                                unwrapped963 = deconstruct_result962
                                                self.pretty_missing_type(unwrapped963)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1650 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1650 = None
                                                deconstruct_result960 = _t1650
                                                if deconstruct_result960 is not None:
                                                    assert deconstruct_result960 is not None
                                                    unwrapped961 = deconstruct_result960
                                                    self.pretty_decimal_type(unwrapped961)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1651 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1651 = None
                                                    deconstruct_result958 = _t1651
                                                    if deconstruct_result958 is not None:
                                                        assert deconstruct_result958 is not None
                                                        unwrapped959 = deconstruct_result958
                                                        self.pretty_boolean_type(unwrapped959)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1652 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1652 = None
                                                        deconstruct_result956 = _t1652
                                                        if deconstruct_result956 is not None:
                                                            assert deconstruct_result956 is not None
                                                            unwrapped957 = deconstruct_result956
                                                            self.pretty_int32_type(unwrapped957)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1653 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1653 = None
                                                            deconstruct_result954 = _t1653
                                                            if deconstruct_result954 is not None:
                                                                assert deconstruct_result954 is not None
                                                                unwrapped955 = deconstruct_result954
                                                                self.pretty_float32_type(unwrapped955)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1654 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1654 = None
                                                                deconstruct_result952 = _t1654
                                                                if deconstruct_result952 is not None:
                                                                    assert deconstruct_result952 is not None
                                                                    unwrapped953 = deconstruct_result952
                                                                    self.pretty_uint32_type(unwrapped953)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields981 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields982 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields983 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields984 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields985 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields986 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields987 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields988 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields989 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat994 = self._try_flat(msg, self.pretty_decimal_type)
        if flat994 is not None:
            assert flat994 is not None
            self.write(flat994)
            return None
        else:
            _dollar_dollar = msg
            fields990 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields990 is not None
            unwrapped_fields991 = fields990
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field992 = unwrapped_fields991[0]
            self.write(str(field992))
            self.newline()
            field993 = unwrapped_fields991[1]
            self.write(str(field993))
=======
        flat989 = self._try_flat(msg, self.pretty_binding)
        if flat989 is not None:
            assert flat989 is not None
            self.write(flat989)
            return None
        else:
            _dollar_dollar = msg
            fields985 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields985 is not None
            unwrapped_fields986 = fields985
            field987 = unwrapped_fields986[0]
            self.write(field987)
            self.write("::")
            field988 = unwrapped_fields986[1]
            self.pretty_type(field988)

    def pretty_type(self, msg: logic_pb2.Type):
        flat1018 = self._try_flat(msg, self.pretty_type)
        if flat1018 is not None:
            assert flat1018 is not None
            self.write(flat1018)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1717 = _dollar_dollar.unspecified_type
            else:
                _t1717 = None
            deconstruct_result1016 = _t1717
            if deconstruct_result1016 is not None:
                assert deconstruct_result1016 is not None
                unwrapped1017 = deconstruct_result1016
                self.pretty_unspecified_type(unwrapped1017)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1718 = _dollar_dollar.string_type
                else:
                    _t1718 = None
                deconstruct_result1014 = _t1718
                if deconstruct_result1014 is not None:
                    assert deconstruct_result1014 is not None
                    unwrapped1015 = deconstruct_result1014
                    self.pretty_string_type(unwrapped1015)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1719 = _dollar_dollar.int_type
                    else:
                        _t1719 = None
                    deconstruct_result1012 = _t1719
                    if deconstruct_result1012 is not None:
                        assert deconstruct_result1012 is not None
                        unwrapped1013 = deconstruct_result1012
                        self.pretty_int_type(unwrapped1013)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1720 = _dollar_dollar.float_type
                        else:
                            _t1720 = None
                        deconstruct_result1010 = _t1720
                        if deconstruct_result1010 is not None:
                            assert deconstruct_result1010 is not None
                            unwrapped1011 = deconstruct_result1010
                            self.pretty_float_type(unwrapped1011)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1721 = _dollar_dollar.uint128_type
                            else:
                                _t1721 = None
                            deconstruct_result1008 = _t1721
                            if deconstruct_result1008 is not None:
                                assert deconstruct_result1008 is not None
                                unwrapped1009 = deconstruct_result1008
                                self.pretty_uint128_type(unwrapped1009)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1722 = _dollar_dollar.int128_type
                                else:
                                    _t1722 = None
                                deconstruct_result1006 = _t1722
                                if deconstruct_result1006 is not None:
                                    assert deconstruct_result1006 is not None
                                    unwrapped1007 = deconstruct_result1006
                                    self.pretty_int128_type(unwrapped1007)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1723 = _dollar_dollar.date_type
                                    else:
                                        _t1723 = None
                                    deconstruct_result1004 = _t1723
                                    if deconstruct_result1004 is not None:
                                        assert deconstruct_result1004 is not None
                                        unwrapped1005 = deconstruct_result1004
                                        self.pretty_date_type(unwrapped1005)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1724 = _dollar_dollar.datetime_type
                                        else:
                                            _t1724 = None
                                        deconstruct_result1002 = _t1724
                                        if deconstruct_result1002 is not None:
                                            assert deconstruct_result1002 is not None
                                            unwrapped1003 = deconstruct_result1002
                                            self.pretty_datetime_type(unwrapped1003)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1725 = _dollar_dollar.missing_type
                                            else:
                                                _t1725 = None
                                            deconstruct_result1000 = _t1725
                                            if deconstruct_result1000 is not None:
                                                assert deconstruct_result1000 is not None
                                                unwrapped1001 = deconstruct_result1000
                                                self.pretty_missing_type(unwrapped1001)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1726 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1726 = None
                                                deconstruct_result998 = _t1726
                                                if deconstruct_result998 is not None:
                                                    assert deconstruct_result998 is not None
                                                    unwrapped999 = deconstruct_result998
                                                    self.pretty_decimal_type(unwrapped999)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1727 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1727 = None
                                                    deconstruct_result996 = _t1727
                                                    if deconstruct_result996 is not None:
                                                        assert deconstruct_result996 is not None
                                                        unwrapped997 = deconstruct_result996
                                                        self.pretty_boolean_type(unwrapped997)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1728 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1728 = None
                                                        deconstruct_result994 = _t1728
                                                        if deconstruct_result994 is not None:
                                                            assert deconstruct_result994 is not None
                                                            unwrapped995 = deconstruct_result994
                                                            self.pretty_int32_type(unwrapped995)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1729 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1729 = None
                                                            deconstruct_result992 = _t1729
                                                            if deconstruct_result992 is not None:
                                                                assert deconstruct_result992 is not None
                                                                unwrapped993 = deconstruct_result992
                                                                self.pretty_float32_type(unwrapped993)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1730 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1730 = None
                                                                deconstruct_result990 = _t1730
                                                                if deconstruct_result990 is not None:
                                                                    assert deconstruct_result990 is not None
                                                                    unwrapped991 = deconstruct_result990
                                                                    self.pretty_uint32_type(unwrapped991)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields1019 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields1020 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields1021 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields1022 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields1023 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields1024 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields1025 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields1026 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields1027 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat1032 = self._try_flat(msg, self.pretty_decimal_type)
        if flat1032 is not None:
            assert flat1032 is not None
            self.write(flat1032)
            return None
        else:
            _dollar_dollar = msg
            fields1028 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields1028 is not None
            unwrapped_fields1029 = fields1028
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field1030 = unwrapped_fields1029[0]
            self.write(str(field1030))
            self.newline()
            field1031 = unwrapped_fields1029[1]
            self.write(str(field1031))
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
<<<<<<< HEAD
        fields995 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields996 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields997 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields998 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat1002 = self._try_flat(msg, self.pretty_value_bindings)
        if flat1002 is not None:
            assert flat1002 is not None
            self.write(flat1002)
            return None
        else:
            fields999 = msg
            self.write("|")
            if not len(fields999) == 0:
                self.write(" ")
                for i1001, elem1000 in enumerate(fields999):
                    if (i1001 > 0):
                        self.newline()
                    self.pretty_binding(elem1000)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1029 = self._try_flat(msg, self.pretty_formula)
        if flat1029 is not None:
            assert flat1029 is not None
            self.write(flat1029)
=======
        fields1033 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields1034 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields1035 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields1036 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat1040 = self._try_flat(msg, self.pretty_value_bindings)
        if flat1040 is not None:
            assert flat1040 is not None
            self.write(flat1040)
            return None
        else:
            fields1037 = msg
            self.write("|")
            if not len(fields1037) == 0:
                self.write(" ")
                for i1039, elem1038 in enumerate(fields1037):
                    if (i1039 > 0):
                        self.newline()
                    self.pretty_binding(elem1038)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1067 = self._try_flat(msg, self.pretty_formula)
        if flat1067 is not None:
            assert flat1067 is not None
            self.write(flat1067)
>>>>>>> origin/main
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
<<<<<<< HEAD
                _t1655 = _dollar_dollar.conjunction
            else:
                _t1655 = None
            deconstruct_result1027 = _t1655
            if deconstruct_result1027 is not None:
                assert deconstruct_result1027 is not None
                unwrapped1028 = deconstruct_result1027
                self.pretty_true(unwrapped1028)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1656 = _dollar_dollar.disjunction
                else:
                    _t1656 = None
                deconstruct_result1025 = _t1656
                if deconstruct_result1025 is not None:
                    assert deconstruct_result1025 is not None
                    unwrapped1026 = deconstruct_result1025
                    self.pretty_false(unwrapped1026)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1657 = _dollar_dollar.exists
                    else:
                        _t1657 = None
                    deconstruct_result1023 = _t1657
                    if deconstruct_result1023 is not None:
                        assert deconstruct_result1023 is not None
                        unwrapped1024 = deconstruct_result1023
                        self.pretty_exists(unwrapped1024)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1658 = _dollar_dollar.reduce
                        else:
                            _t1658 = None
                        deconstruct_result1021 = _t1658
                        if deconstruct_result1021 is not None:
                            assert deconstruct_result1021 is not None
                            unwrapped1022 = deconstruct_result1021
                            self.pretty_reduce(unwrapped1022)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1659 = _dollar_dollar.conjunction
                            else:
                                _t1659 = None
                            deconstruct_result1019 = _t1659
                            if deconstruct_result1019 is not None:
                                assert deconstruct_result1019 is not None
                                unwrapped1020 = deconstruct_result1019
                                self.pretty_conjunction(unwrapped1020)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1660 = _dollar_dollar.disjunction
                                else:
                                    _t1660 = None
                                deconstruct_result1017 = _t1660
                                if deconstruct_result1017 is not None:
                                    assert deconstruct_result1017 is not None
                                    unwrapped1018 = deconstruct_result1017
                                    self.pretty_disjunction(unwrapped1018)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1661 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1661 = None
                                    deconstruct_result1015 = _t1661
                                    if deconstruct_result1015 is not None:
                                        assert deconstruct_result1015 is not None
                                        unwrapped1016 = deconstruct_result1015
                                        self.pretty_not(unwrapped1016)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1662 = _dollar_dollar.ffi
                                        else:
                                            _t1662 = None
                                        deconstruct_result1013 = _t1662
                                        if deconstruct_result1013 is not None:
                                            assert deconstruct_result1013 is not None
                                            unwrapped1014 = deconstruct_result1013
                                            self.pretty_ffi(unwrapped1014)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1663 = _dollar_dollar.atom
                                            else:
                                                _t1663 = None
                                            deconstruct_result1011 = _t1663
                                            if deconstruct_result1011 is not None:
                                                assert deconstruct_result1011 is not None
                                                unwrapped1012 = deconstruct_result1011
                                                self.pretty_atom(unwrapped1012)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1664 = _dollar_dollar.pragma
                                                else:
                                                    _t1664 = None
                                                deconstruct_result1009 = _t1664
                                                if deconstruct_result1009 is not None:
                                                    assert deconstruct_result1009 is not None
                                                    unwrapped1010 = deconstruct_result1009
                                                    self.pretty_pragma(unwrapped1010)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1665 = _dollar_dollar.primitive
                                                    else:
                                                        _t1665 = None
                                                    deconstruct_result1007 = _t1665
                                                    if deconstruct_result1007 is not None:
                                                        assert deconstruct_result1007 is not None
                                                        unwrapped1008 = deconstruct_result1007
                                                        self.pretty_primitive(unwrapped1008)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1666 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1666 = None
                                                        deconstruct_result1005 = _t1666
                                                        if deconstruct_result1005 is not None:
                                                            assert deconstruct_result1005 is not None
                                                            unwrapped1006 = deconstruct_result1005
                                                            self.pretty_rel_atom(unwrapped1006)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1667 = _dollar_dollar.cast
                                                            else:
                                                                _t1667 = None
                                                            deconstruct_result1003 = _t1667
                                                            if deconstruct_result1003 is not None:
                                                                assert deconstruct_result1003 is not None
                                                                unwrapped1004 = deconstruct_result1003
                                                                self.pretty_cast(unwrapped1004)
=======
                _t1731 = _dollar_dollar.conjunction
            else:
                _t1731 = None
            deconstruct_result1065 = _t1731
            if deconstruct_result1065 is not None:
                assert deconstruct_result1065 is not None
                unwrapped1066 = deconstruct_result1065
                self.pretty_true(unwrapped1066)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1732 = _dollar_dollar.disjunction
                else:
                    _t1732 = None
                deconstruct_result1063 = _t1732
                if deconstruct_result1063 is not None:
                    assert deconstruct_result1063 is not None
                    unwrapped1064 = deconstruct_result1063
                    self.pretty_false(unwrapped1064)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1733 = _dollar_dollar.exists
                    else:
                        _t1733 = None
                    deconstruct_result1061 = _t1733
                    if deconstruct_result1061 is not None:
                        assert deconstruct_result1061 is not None
                        unwrapped1062 = deconstruct_result1061
                        self.pretty_exists(unwrapped1062)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1734 = _dollar_dollar.reduce
                        else:
                            _t1734 = None
                        deconstruct_result1059 = _t1734
                        if deconstruct_result1059 is not None:
                            assert deconstruct_result1059 is not None
                            unwrapped1060 = deconstruct_result1059
                            self.pretty_reduce(unwrapped1060)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1735 = _dollar_dollar.conjunction
                            else:
                                _t1735 = None
                            deconstruct_result1057 = _t1735
                            if deconstruct_result1057 is not None:
                                assert deconstruct_result1057 is not None
                                unwrapped1058 = deconstruct_result1057
                                self.pretty_conjunction(unwrapped1058)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1736 = _dollar_dollar.disjunction
                                else:
                                    _t1736 = None
                                deconstruct_result1055 = _t1736
                                if deconstruct_result1055 is not None:
                                    assert deconstruct_result1055 is not None
                                    unwrapped1056 = deconstruct_result1055
                                    self.pretty_disjunction(unwrapped1056)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1737 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1737 = None
                                    deconstruct_result1053 = _t1737
                                    if deconstruct_result1053 is not None:
                                        assert deconstruct_result1053 is not None
                                        unwrapped1054 = deconstruct_result1053
                                        self.pretty_not(unwrapped1054)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1738 = _dollar_dollar.ffi
                                        else:
                                            _t1738 = None
                                        deconstruct_result1051 = _t1738
                                        if deconstruct_result1051 is not None:
                                            assert deconstruct_result1051 is not None
                                            unwrapped1052 = deconstruct_result1051
                                            self.pretty_ffi(unwrapped1052)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1739 = _dollar_dollar.atom
                                            else:
                                                _t1739 = None
                                            deconstruct_result1049 = _t1739
                                            if deconstruct_result1049 is not None:
                                                assert deconstruct_result1049 is not None
                                                unwrapped1050 = deconstruct_result1049
                                                self.pretty_atom(unwrapped1050)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1740 = _dollar_dollar.pragma
                                                else:
                                                    _t1740 = None
                                                deconstruct_result1047 = _t1740
                                                if deconstruct_result1047 is not None:
                                                    assert deconstruct_result1047 is not None
                                                    unwrapped1048 = deconstruct_result1047
                                                    self.pretty_pragma(unwrapped1048)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1741 = _dollar_dollar.primitive
                                                    else:
                                                        _t1741 = None
                                                    deconstruct_result1045 = _t1741
                                                    if deconstruct_result1045 is not None:
                                                        assert deconstruct_result1045 is not None
                                                        unwrapped1046 = deconstruct_result1045
                                                        self.pretty_primitive(unwrapped1046)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1742 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1742 = None
                                                        deconstruct_result1043 = _t1742
                                                        if deconstruct_result1043 is not None:
                                                            assert deconstruct_result1043 is not None
                                                            unwrapped1044 = deconstruct_result1043
                                                            self.pretty_rel_atom(unwrapped1044)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1743 = _dollar_dollar.cast
                                                            else:
                                                                _t1743 = None
                                                            deconstruct_result1041 = _t1743
                                                            if deconstruct_result1041 is not None:
                                                                assert deconstruct_result1041 is not None
                                                                unwrapped1042 = deconstruct_result1041
                                                                self.pretty_cast(unwrapped1042)
>>>>>>> origin/main
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
<<<<<<< HEAD
        fields1030 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1031 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1036 = self._try_flat(msg, self.pretty_exists)
        if flat1036 is not None:
            assert flat1036 is not None
            self.write(flat1036)
            return None
        else:
            _dollar_dollar = msg
            _t1668 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1032 = (_t1668, _dollar_dollar.body.value,)
            assert fields1032 is not None
            unwrapped_fields1033 = fields1032
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1034 = unwrapped_fields1033[0]
            self.pretty_bindings(field1034)
            self.newline()
            field1035 = unwrapped_fields1033[1]
            self.pretty_formula(field1035)
=======
        fields1068 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1069 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1074 = self._try_flat(msg, self.pretty_exists)
        if flat1074 is not None:
            assert flat1074 is not None
            self.write(flat1074)
            return None
        else:
            _dollar_dollar = msg
            _t1744 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1070 = (_t1744, _dollar_dollar.body.value,)
            assert fields1070 is not None
            unwrapped_fields1071 = fields1070
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1072 = unwrapped_fields1071[0]
            self.pretty_bindings(field1072)
            self.newline()
            field1073 = unwrapped_fields1071[1]
            self.pretty_formula(field1073)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
<<<<<<< HEAD
        flat1042 = self._try_flat(msg, self.pretty_reduce)
        if flat1042 is not None:
            assert flat1042 is not None
            self.write(flat1042)
            return None
        else:
            _dollar_dollar = msg
            fields1037 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1037 is not None
            unwrapped_fields1038 = fields1037
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1039 = unwrapped_fields1038[0]
            self.pretty_abstraction(field1039)
            self.newline()
            field1040 = unwrapped_fields1038[1]
            self.pretty_abstraction(field1040)
            self.newline()
            field1041 = unwrapped_fields1038[2]
            self.pretty_terms(field1041)
=======
        flat1080 = self._try_flat(msg, self.pretty_reduce)
        if flat1080 is not None:
            assert flat1080 is not None
            self.write(flat1080)
            return None
        else:
            _dollar_dollar = msg
            fields1075 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1075 is not None
            unwrapped_fields1076 = fields1075
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1077 = unwrapped_fields1076[0]
            self.pretty_abstraction(field1077)
            self.newline()
            field1078 = unwrapped_fields1076[1]
            self.pretty_abstraction(field1078)
            self.newline()
            field1079 = unwrapped_fields1076[2]
            self.pretty_terms(field1079)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
<<<<<<< HEAD
        flat1046 = self._try_flat(msg, self.pretty_terms)
        if flat1046 is not None:
            assert flat1046 is not None
            self.write(flat1046)
=======
        flat1084 = self._try_flat(msg, self.pretty_terms)
        if flat1084 is not None:
            assert flat1084 is not None
            self.write(flat1084)
            return None
        else:
            fields1081 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1081) == 0:
                self.newline()
                for i1083, elem1082 in enumerate(fields1081):
                    if (i1083 > 0):
                        self.newline()
                    self.pretty_term(elem1082)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1089 = self._try_flat(msg, self.pretty_term)
        if flat1089 is not None:
            assert flat1089 is not None
            self.write(flat1089)
>>>>>>> origin/main
            return None
        else:
            fields1043 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1043) == 0:
                self.newline()
                for i1045, elem1044 in enumerate(fields1043):
                    if (i1045 > 0):
                        self.newline()
                    self.pretty_term(elem1044)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1051 = self._try_flat(msg, self.pretty_term)
        if flat1051 is not None:
            assert flat1051 is not None
            self.write(flat1051)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
<<<<<<< HEAD
                _t1669 = _dollar_dollar.var
            else:
                _t1669 = None
            deconstruct_result1049 = _t1669
            if deconstruct_result1049 is not None:
                assert deconstruct_result1049 is not None
                unwrapped1050 = deconstruct_result1049
                self.pretty_var(unwrapped1050)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1670 = _dollar_dollar.constant
                else:
                    _t1670 = None
                deconstruct_result1047 = _t1670
                if deconstruct_result1047 is not None:
                    assert deconstruct_result1047 is not None
                    unwrapped1048 = deconstruct_result1047
                    self.pretty_value(unwrapped1048)
=======
                _t1745 = _dollar_dollar.var
            else:
                _t1745 = None
            deconstruct_result1087 = _t1745
            if deconstruct_result1087 is not None:
                assert deconstruct_result1087 is not None
                unwrapped1088 = deconstruct_result1087
                self.pretty_var(unwrapped1088)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1746 = _dollar_dollar.constant
                else:
                    _t1746 = None
                deconstruct_result1085 = _t1746
                if deconstruct_result1085 is not None:
                    assert deconstruct_result1085 is not None
                    unwrapped1086 = deconstruct_result1085
                    self.pretty_value(unwrapped1086)
>>>>>>> origin/main
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
<<<<<<< HEAD
        flat1054 = self._try_flat(msg, self.pretty_var)
        if flat1054 is not None:
            assert flat1054 is not None
            self.write(flat1054)
            return None
        else:
            _dollar_dollar = msg
            fields1052 = _dollar_dollar.name
            assert fields1052 is not None
            unwrapped_fields1053 = fields1052
            self.write(unwrapped_fields1053)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1080 = self._try_flat(msg, self.pretty_value)
        if flat1080 is not None:
            assert flat1080 is not None
            self.write(flat1080)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1671 = _dollar_dollar.date_value
            else:
                _t1671 = None
            deconstruct_result1078 = _t1671
            if deconstruct_result1078 is not None:
                assert deconstruct_result1078 is not None
                unwrapped1079 = deconstruct_result1078
                self.pretty_date(unwrapped1079)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1672 = _dollar_dollar.datetime_value
                else:
                    _t1672 = None
                deconstruct_result1076 = _t1672
                if deconstruct_result1076 is not None:
                    assert deconstruct_result1076 is not None
                    unwrapped1077 = deconstruct_result1076
                    self.pretty_datetime(unwrapped1077)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1673 = _dollar_dollar.string_value
                    else:
                        _t1673 = None
                    deconstruct_result1074 = _t1673
                    if deconstruct_result1074 is not None:
                        assert deconstruct_result1074 is not None
                        unwrapped1075 = deconstruct_result1074
                        self.write(self.format_string_value(unwrapped1075))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1674 = _dollar_dollar.int32_value
                        else:
                            _t1674 = None
                        deconstruct_result1072 = _t1674
                        if deconstruct_result1072 is not None:
                            assert deconstruct_result1072 is not None
                            unwrapped1073 = deconstruct_result1072
                            self.write((str(unwrapped1073) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1675 = _dollar_dollar.int_value
                            else:
                                _t1675 = None
                            deconstruct_result1070 = _t1675
                            if deconstruct_result1070 is not None:
                                assert deconstruct_result1070 is not None
                                unwrapped1071 = deconstruct_result1070
                                self.write(str(unwrapped1071))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1676 = _dollar_dollar.float32_value
                                else:
                                    _t1676 = None
                                deconstruct_result1068 = _t1676
                                if deconstruct_result1068 is not None:
                                    assert deconstruct_result1068 is not None
                                    unwrapped1069 = deconstruct_result1068
                                    self.write(self.format_float32_literal(unwrapped1069))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1677 = _dollar_dollar.float_value
                                    else:
                                        _t1677 = None
                                    deconstruct_result1066 = _t1677
                                    if deconstruct_result1066 is not None:
                                        assert deconstruct_result1066 is not None
                                        unwrapped1067 = deconstruct_result1066
                                        self.write(str(unwrapped1067))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1678 = _dollar_dollar.uint32_value
                                        else:
                                            _t1678 = None
                                        deconstruct_result1064 = _t1678
                                        if deconstruct_result1064 is not None:
                                            assert deconstruct_result1064 is not None
                                            unwrapped1065 = deconstruct_result1064
                                            self.write((str(unwrapped1065) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1679 = _dollar_dollar.uint128_value
                                            else:
                                                _t1679 = None
                                            deconstruct_result1062 = _t1679
                                            if deconstruct_result1062 is not None:
                                                assert deconstruct_result1062 is not None
                                                unwrapped1063 = deconstruct_result1062
                                                self.write(self.format_uint128(unwrapped1063))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1680 = _dollar_dollar.int128_value
                                                else:
                                                    _t1680 = None
                                                deconstruct_result1060 = _t1680
                                                if deconstruct_result1060 is not None:
                                                    assert deconstruct_result1060 is not None
                                                    unwrapped1061 = deconstruct_result1060
                                                    self.write(self.format_int128(unwrapped1061))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1681 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1681 = None
                                                    deconstruct_result1058 = _t1681
                                                    if deconstruct_result1058 is not None:
                                                        assert deconstruct_result1058 is not None
                                                        unwrapped1059 = deconstruct_result1058
                                                        self.write(self.format_decimal(unwrapped1059))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1682 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1682 = None
                                                        deconstruct_result1056 = _t1682
                                                        if deconstruct_result1056 is not None:
                                                            assert deconstruct_result1056 is not None
                                                            unwrapped1057 = deconstruct_result1056
                                                            self.pretty_boolean_value(unwrapped1057)
                                                        else:
                                                            fields1055 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1086 = self._try_flat(msg, self.pretty_date)
        if flat1086 is not None:
            assert flat1086 is not None
            self.write(flat1086)
            return None
        else:
            _dollar_dollar = msg
            fields1081 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1081 is not None
            unwrapped_fields1082 = fields1081
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1083 = unwrapped_fields1082[0]
            self.write(str(field1083))
            self.newline()
            field1084 = unwrapped_fields1082[1]
            self.write(str(field1084))
            self.newline()
            field1085 = unwrapped_fields1082[2]
            self.write(str(field1085))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1097 = self._try_flat(msg, self.pretty_datetime)
        if flat1097 is not None:
            assert flat1097 is not None
            self.write(flat1097)
            return None
        else:
            _dollar_dollar = msg
            fields1087 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1087 is not None
            unwrapped_fields1088 = fields1087
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1089 = unwrapped_fields1088[0]
            self.write(str(field1089))
            self.newline()
            field1090 = unwrapped_fields1088[1]
            self.write(str(field1090))
            self.newline()
            field1091 = unwrapped_fields1088[2]
            self.write(str(field1091))
            self.newline()
            field1092 = unwrapped_fields1088[3]
            self.write(str(field1092))
            self.newline()
            field1093 = unwrapped_fields1088[4]
            self.write(str(field1093))
            self.newline()
            field1094 = unwrapped_fields1088[5]
            self.write(str(field1094))
            field1095 = unwrapped_fields1088[6]
            if field1095 is not None:
                self.newline()
                assert field1095 is not None
                opt_val1096 = field1095
                self.write(str(opt_val1096))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1102 = self._try_flat(msg, self.pretty_conjunction)
        if flat1102 is not None:
            assert flat1102 is not None
            self.write(flat1102)
            return None
        else:
            _dollar_dollar = msg
            fields1098 = _dollar_dollar.args
            assert fields1098 is not None
            unwrapped_fields1099 = fields1098
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1099) == 0:
                self.newline()
                for i1101, elem1100 in enumerate(unwrapped_fields1099):
                    if (i1101 > 0):
                        self.newline()
                    self.pretty_formula(elem1100)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1107 = self._try_flat(msg, self.pretty_disjunction)
        if flat1107 is not None:
            assert flat1107 is not None
            self.write(flat1107)
            return None
        else:
            _dollar_dollar = msg
            fields1103 = _dollar_dollar.args
            assert fields1103 is not None
            unwrapped_fields1104 = fields1103
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1104) == 0:
                self.newline()
                for i1106, elem1105 in enumerate(unwrapped_fields1104):
                    if (i1106 > 0):
                        self.newline()
                    self.pretty_formula(elem1105)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1110 = self._try_flat(msg, self.pretty_not)
        if flat1110 is not None:
            assert flat1110 is not None
            self.write(flat1110)
            return None
        else:
            _dollar_dollar = msg
            fields1108 = _dollar_dollar.arg
            assert fields1108 is not None
            unwrapped_fields1109 = fields1108
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1109)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1116 = self._try_flat(msg, self.pretty_ffi)
        if flat1116 is not None:
            assert flat1116 is not None
            self.write(flat1116)
            return None
        else:
            _dollar_dollar = msg
            fields1111 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1111 is not None
            unwrapped_fields1112 = fields1111
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1113 = unwrapped_fields1112[0]
            self.pretty_name(field1113)
            self.newline()
            field1114 = unwrapped_fields1112[1]
            self.pretty_ffi_args(field1114)
            self.newline()
            field1115 = unwrapped_fields1112[2]
            self.pretty_terms(field1115)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1118 = self._try_flat(msg, self.pretty_name)
        if flat1118 is not None:
            assert flat1118 is not None
            self.write(flat1118)
            return None
        else:
            fields1117 = msg
            self.write(":")
            self.write(fields1117)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1122 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1122 is not None:
            assert flat1122 is not None
            self.write(flat1122)
            return None
        else:
            fields1119 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1119) == 0:
                self.newline()
                for i1121, elem1120 in enumerate(fields1119):
                    if (i1121 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1120)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1129 = self._try_flat(msg, self.pretty_atom)
        if flat1129 is not None:
            assert flat1129 is not None
            self.write(flat1129)
            return None
        else:
            _dollar_dollar = msg
            fields1123 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1123 is not None
            unwrapped_fields1124 = fields1123
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1125 = unwrapped_fields1124[0]
            self.pretty_relation_id(field1125)
            field1126 = unwrapped_fields1124[1]
            if not len(field1126) == 0:
                self.newline()
                for i1128, elem1127 in enumerate(field1126):
                    if (i1128 > 0):
                        self.newline()
                    self.pretty_term(elem1127)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1136 = self._try_flat(msg, self.pretty_pragma)
        if flat1136 is not None:
            assert flat1136 is not None
            self.write(flat1136)
            return None
        else:
            _dollar_dollar = msg
            fields1130 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1130 is not None
            unwrapped_fields1131 = fields1130
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1132 = unwrapped_fields1131[0]
            self.pretty_name(field1132)
            field1133 = unwrapped_fields1131[1]
            if not len(field1133) == 0:
                self.newline()
                for i1135, elem1134 in enumerate(field1133):
                    if (i1135 > 0):
                        self.newline()
                    self.pretty_term(elem1134)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1152 = self._try_flat(msg, self.pretty_primitive)
        if flat1152 is not None:
            assert flat1152 is not None
            self.write(flat1152)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1683 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1683 = None
            guard_result1151 = _t1683
            if guard_result1151 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1684 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1684 = None
                guard_result1150 = _t1684
                if guard_result1150 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1685 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1685 = None
                    guard_result1149 = _t1685
                    if guard_result1149 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1686 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1686 = None
                        guard_result1148 = _t1686
                        if guard_result1148 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1687 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1687 = None
                            guard_result1147 = _t1687
                            if guard_result1147 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1688 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1688 = None
                                guard_result1146 = _t1688
                                if guard_result1146 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1689 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1689 = None
                                    guard_result1145 = _t1689
                                    if guard_result1145 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1690 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1690 = None
                                        guard_result1144 = _t1690
                                        if guard_result1144 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1691 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1691 = None
                                            guard_result1143 = _t1691
                                            if guard_result1143 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1137 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1137 is not None
                                                unwrapped_fields1138 = fields1137
                                                self.write("(primitive")
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
                                                        self.pretty_rel_term(elem1141)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1157 = self._try_flat(msg, self.pretty_eq)
        if flat1157 is not None:
            assert flat1157 is not None
            self.write(flat1157)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1692 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1692 = None
            fields1153 = _t1692
            assert fields1153 is not None
            unwrapped_fields1154 = fields1153
            self.write("(=")
=======
        flat1092 = self._try_flat(msg, self.pretty_var)
        if flat1092 is not None:
            assert flat1092 is not None
            self.write(flat1092)
            return None
        else:
            _dollar_dollar = msg
            fields1090 = _dollar_dollar.name
            assert fields1090 is not None
            unwrapped_fields1091 = fields1090
            self.write(unwrapped_fields1091)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1118 = self._try_flat(msg, self.pretty_value)
        if flat1118 is not None:
            assert flat1118 is not None
            self.write(flat1118)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1747 = _dollar_dollar.date_value
            else:
                _t1747 = None
            deconstruct_result1116 = _t1747
            if deconstruct_result1116 is not None:
                assert deconstruct_result1116 is not None
                unwrapped1117 = deconstruct_result1116
                self.pretty_date(unwrapped1117)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1748 = _dollar_dollar.datetime_value
                else:
                    _t1748 = None
                deconstruct_result1114 = _t1748
                if deconstruct_result1114 is not None:
                    assert deconstruct_result1114 is not None
                    unwrapped1115 = deconstruct_result1114
                    self.pretty_datetime(unwrapped1115)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1749 = _dollar_dollar.string_value
                    else:
                        _t1749 = None
                    deconstruct_result1112 = _t1749
                    if deconstruct_result1112 is not None:
                        assert deconstruct_result1112 is not None
                        unwrapped1113 = deconstruct_result1112
                        self.write(self.format_string_value(unwrapped1113))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1750 = _dollar_dollar.int32_value
                        else:
                            _t1750 = None
                        deconstruct_result1110 = _t1750
                        if deconstruct_result1110 is not None:
                            assert deconstruct_result1110 is not None
                            unwrapped1111 = deconstruct_result1110
                            self.write((str(unwrapped1111) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1751 = _dollar_dollar.int_value
                            else:
                                _t1751 = None
                            deconstruct_result1108 = _t1751
                            if deconstruct_result1108 is not None:
                                assert deconstruct_result1108 is not None
                                unwrapped1109 = deconstruct_result1108
                                self.write(str(unwrapped1109))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1752 = _dollar_dollar.float32_value
                                else:
                                    _t1752 = None
                                deconstruct_result1106 = _t1752
                                if deconstruct_result1106 is not None:
                                    assert deconstruct_result1106 is not None
                                    unwrapped1107 = deconstruct_result1106
                                    self.write(self.format_float32_literal(unwrapped1107))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1753 = _dollar_dollar.float_value
                                    else:
                                        _t1753 = None
                                    deconstruct_result1104 = _t1753
                                    if deconstruct_result1104 is not None:
                                        assert deconstruct_result1104 is not None
                                        unwrapped1105 = deconstruct_result1104
                                        self.write(str(unwrapped1105))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1754 = _dollar_dollar.uint32_value
                                        else:
                                            _t1754 = None
                                        deconstruct_result1102 = _t1754
                                        if deconstruct_result1102 is not None:
                                            assert deconstruct_result1102 is not None
                                            unwrapped1103 = deconstruct_result1102
                                            self.write((str(unwrapped1103) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1755 = _dollar_dollar.uint128_value
                                            else:
                                                _t1755 = None
                                            deconstruct_result1100 = _t1755
                                            if deconstruct_result1100 is not None:
                                                assert deconstruct_result1100 is not None
                                                unwrapped1101 = deconstruct_result1100
                                                self.write(self.format_uint128(unwrapped1101))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1756 = _dollar_dollar.int128_value
                                                else:
                                                    _t1756 = None
                                                deconstruct_result1098 = _t1756
                                                if deconstruct_result1098 is not None:
                                                    assert deconstruct_result1098 is not None
                                                    unwrapped1099 = deconstruct_result1098
                                                    self.write(self.format_int128(unwrapped1099))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1757 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1757 = None
                                                    deconstruct_result1096 = _t1757
                                                    if deconstruct_result1096 is not None:
                                                        assert deconstruct_result1096 is not None
                                                        unwrapped1097 = deconstruct_result1096
                                                        self.write(self.format_decimal(unwrapped1097))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1758 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1758 = None
                                                        deconstruct_result1094 = _t1758
                                                        if deconstruct_result1094 is not None:
                                                            assert deconstruct_result1094 is not None
                                                            unwrapped1095 = deconstruct_result1094
                                                            self.pretty_boolean_value(unwrapped1095)
                                                        else:
                                                            fields1093 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1124 = self._try_flat(msg, self.pretty_date)
        if flat1124 is not None:
            assert flat1124 is not None
            self.write(flat1124)
            return None
        else:
            _dollar_dollar = msg
            fields1119 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1119 is not None
            unwrapped_fields1120 = fields1119
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1121 = unwrapped_fields1120[0]
            self.write(str(field1121))
            self.newline()
            field1122 = unwrapped_fields1120[1]
            self.write(str(field1122))
            self.newline()
            field1123 = unwrapped_fields1120[2]
            self.write(str(field1123))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1135 = self._try_flat(msg, self.pretty_datetime)
        if flat1135 is not None:
            assert flat1135 is not None
            self.write(flat1135)
            return None
        else:
            _dollar_dollar = msg
            fields1125 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1125 is not None
            unwrapped_fields1126 = fields1125
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1127 = unwrapped_fields1126[0]
            self.write(str(field1127))
            self.newline()
            field1128 = unwrapped_fields1126[1]
            self.write(str(field1128))
            self.newline()
            field1129 = unwrapped_fields1126[2]
            self.write(str(field1129))
            self.newline()
            field1130 = unwrapped_fields1126[3]
            self.write(str(field1130))
            self.newline()
            field1131 = unwrapped_fields1126[4]
            self.write(str(field1131))
            self.newline()
            field1132 = unwrapped_fields1126[5]
            self.write(str(field1132))
            field1133 = unwrapped_fields1126[6]
            if field1133 is not None:
                self.newline()
                assert field1133 is not None
                opt_val1134 = field1133
                self.write(str(opt_val1134))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1140 = self._try_flat(msg, self.pretty_conjunction)
        if flat1140 is not None:
            assert flat1140 is not None
            self.write(flat1140)
            return None
        else:
            _dollar_dollar = msg
            fields1136 = _dollar_dollar.args
            assert fields1136 is not None
            unwrapped_fields1137 = fields1136
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1137) == 0:
                self.newline()
                for i1139, elem1138 in enumerate(unwrapped_fields1137):
                    if (i1139 > 0):
                        self.newline()
                    self.pretty_formula(elem1138)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1145 = self._try_flat(msg, self.pretty_disjunction)
        if flat1145 is not None:
            assert flat1145 is not None
            self.write(flat1145)
            return None
        else:
            _dollar_dollar = msg
            fields1141 = _dollar_dollar.args
            assert fields1141 is not None
            unwrapped_fields1142 = fields1141
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1142) == 0:
                self.newline()
                for i1144, elem1143 in enumerate(unwrapped_fields1142):
                    if (i1144 > 0):
                        self.newline()
                    self.pretty_formula(elem1143)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1148 = self._try_flat(msg, self.pretty_not)
        if flat1148 is not None:
            assert flat1148 is not None
            self.write(flat1148)
            return None
        else:
            _dollar_dollar = msg
            fields1146 = _dollar_dollar.arg
            assert fields1146 is not None
            unwrapped_fields1147 = fields1146
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1147)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1154 = self._try_flat(msg, self.pretty_ffi)
        if flat1154 is not None:
            assert flat1154 is not None
            self.write(flat1154)
            return None
        else:
            _dollar_dollar = msg
            fields1149 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1149 is not None
            unwrapped_fields1150 = fields1149
            self.write("(ffi")
>>>>>>> origin/main
            self.indent_sexp()
            self.newline()
            field1151 = unwrapped_fields1150[0]
            self.pretty_name(field1151)
            self.newline()
            field1152 = unwrapped_fields1150[1]
            self.pretty_ffi_args(field1152)
            self.newline()
            field1153 = unwrapped_fields1150[2]
            self.pretty_terms(field1153)
            self.dedent()
            self.write(")")

<<<<<<< HEAD
    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1162 = self._try_flat(msg, self.pretty_lt)
        if flat1162 is not None:
            assert flat1162 is not None
            self.write(flat1162)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1693 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1693 = None
            fields1158 = _t1693
            assert fields1158 is not None
            unwrapped_fields1159 = fields1158
            self.write("(<")
=======
    def pretty_name(self, msg: str):
        flat1156 = self._try_flat(msg, self.pretty_name)
        if flat1156 is not None:
            assert flat1156 is not None
            self.write(flat1156)
            return None
        else:
            fields1155 = msg
            self.write(":")
            self.write(fields1155)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1160 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1160 is not None:
            assert flat1160 is not None
            self.write(flat1160)
            return None
        else:
            fields1157 = msg
            self.write("(args")
>>>>>>> origin/main
            self.indent_sexp()
            if not len(fields1157) == 0:
                self.newline()
                for i1159, elem1158 in enumerate(fields1157):
                    if (i1159 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1158)
            self.dedent()
            self.write(")")

<<<<<<< HEAD
    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1167 = self._try_flat(msg, self.pretty_lt_eq)
=======
    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1167 = self._try_flat(msg, self.pretty_atom)
>>>>>>> origin/main
        if flat1167 is not None:
            assert flat1167 is not None
            self.write(flat1167)
            return None
        else:
            _dollar_dollar = msg
<<<<<<< HEAD
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1694 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1694 = None
            fields1163 = _t1694
            assert fields1163 is not None
            unwrapped_fields1164 = fields1163
            self.write("(<=")
=======
            fields1161 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1161 is not None
            unwrapped_fields1162 = fields1161
            self.write("(atom")
>>>>>>> origin/main
            self.indent_sexp()
            self.newline()
            field1163 = unwrapped_fields1162[0]
            self.pretty_relation_id(field1163)
            field1164 = unwrapped_fields1162[1]
            if not len(field1164) == 0:
                self.newline()
                for i1166, elem1165 in enumerate(field1164):
                    if (i1166 > 0):
                        self.newline()
                    self.pretty_term(elem1165)
            self.dedent()
            self.write(")")

<<<<<<< HEAD
    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1172 = self._try_flat(msg, self.pretty_gt)
        if flat1172 is not None:
            assert flat1172 is not None
            self.write(flat1172)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1695 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1695 = None
            fields1168 = _t1695
            assert fields1168 is not None
            unwrapped_fields1169 = fields1168
            self.write("(>")
=======
    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1174 = self._try_flat(msg, self.pretty_pragma)
        if flat1174 is not None:
            assert flat1174 is not None
            self.write(flat1174)
            return None
        else:
            _dollar_dollar = msg
            fields1168 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1168 is not None
            unwrapped_fields1169 = fields1168
            self.write("(pragma")
>>>>>>> origin/main
            self.indent_sexp()
            self.newline()
            field1170 = unwrapped_fields1169[0]
            self.pretty_name(field1170)
            field1171 = unwrapped_fields1169[1]
            if not len(field1171) == 0:
                self.newline()
                for i1173, elem1172 in enumerate(field1171):
                    if (i1173 > 0):
                        self.newline()
                    self.pretty_term(elem1172)
            self.dedent()
            self.write(")")

<<<<<<< HEAD
    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1177 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1177 is not None:
            assert flat1177 is not None
            self.write(flat1177)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1696 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1696 = None
            fields1173 = _t1696
            assert fields1173 is not None
            unwrapped_fields1174 = fields1173
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1175 = unwrapped_fields1174[0]
            self.pretty_term(field1175)
            self.newline()
            field1176 = unwrapped_fields1174[1]
            self.pretty_term(field1176)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1183 = self._try_flat(msg, self.pretty_add)
        if flat1183 is not None:
            assert flat1183 is not None
            self.write(flat1183)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1697 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1697 = None
            fields1178 = _t1697
            assert fields1178 is not None
            unwrapped_fields1179 = fields1178
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1180 = unwrapped_fields1179[0]
            self.pretty_term(field1180)
            self.newline()
            field1181 = unwrapped_fields1179[1]
            self.pretty_term(field1181)
            self.newline()
            field1182 = unwrapped_fields1179[2]
            self.pretty_term(field1182)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1189 = self._try_flat(msg, self.pretty_minus)
        if flat1189 is not None:
            assert flat1189 is not None
            self.write(flat1189)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1698 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1698 = None
            fields1184 = _t1698
            assert fields1184 is not None
            unwrapped_fields1185 = fields1184
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1186 = unwrapped_fields1185[0]
            self.pretty_term(field1186)
            self.newline()
            field1187 = unwrapped_fields1185[1]
            self.pretty_term(field1187)
            self.newline()
            field1188 = unwrapped_fields1185[2]
            self.pretty_term(field1188)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1195 = self._try_flat(msg, self.pretty_multiply)
        if flat1195 is not None:
            assert flat1195 is not None
            self.write(flat1195)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1699 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1699 = None
            fields1190 = _t1699
            assert fields1190 is not None
            unwrapped_fields1191 = fields1190
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1192 = unwrapped_fields1191[0]
            self.pretty_term(field1192)
            self.newline()
            field1193 = unwrapped_fields1191[1]
            self.pretty_term(field1193)
            self.newline()
            field1194 = unwrapped_fields1191[2]
            self.pretty_term(field1194)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1201 = self._try_flat(msg, self.pretty_divide)
        if flat1201 is not None:
            assert flat1201 is not None
            self.write(flat1201)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1700 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1700 = None
            fields1196 = _t1700
            assert fields1196 is not None
            unwrapped_fields1197 = fields1196
            self.write("(/")
=======
    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1190 = self._try_flat(msg, self.pretty_primitive)
        if flat1190 is not None:
            assert flat1190 is not None
            self.write(flat1190)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1759 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1759 = None
            guard_result1189 = _t1759
            if guard_result1189 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1760 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1760 = None
                guard_result1188 = _t1760
                if guard_result1188 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1761 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1761 = None
                    guard_result1187 = _t1761
                    if guard_result1187 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1762 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1762 = None
                        guard_result1186 = _t1762
                        if guard_result1186 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1763 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1763 = None
                            guard_result1185 = _t1763
                            if guard_result1185 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1764 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1764 = None
                                guard_result1184 = _t1764
                                if guard_result1184 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1765 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1765 = None
                                    guard_result1183 = _t1765
                                    if guard_result1183 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1766 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1766 = None
                                        guard_result1182 = _t1766
                                        if guard_result1182 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1767 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1767 = None
                                            guard_result1181 = _t1767
                                            if guard_result1181 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1175 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1175 is not None
                                                unwrapped_fields1176 = fields1175
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1177 = unwrapped_fields1176[0]
                                                self.pretty_name(field1177)
                                                field1178 = unwrapped_fields1176[1]
                                                if not len(field1178) == 0:
                                                    self.newline()
                                                    for i1180, elem1179 in enumerate(field1178):
                                                        if (i1180 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1179)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1195 = self._try_flat(msg, self.pretty_eq)
        if flat1195 is not None:
            assert flat1195 is not None
            self.write(flat1195)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1768 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1768 = None
            fields1191 = _t1768
            assert fields1191 is not None
            unwrapped_fields1192 = fields1191
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1193 = unwrapped_fields1192[0]
            self.pretty_term(field1193)
            self.newline()
            field1194 = unwrapped_fields1192[1]
            self.pretty_term(field1194)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1200 = self._try_flat(msg, self.pretty_lt)
        if flat1200 is not None:
            assert flat1200 is not None
            self.write(flat1200)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1769 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1769 = None
            fields1196 = _t1769
            assert fields1196 is not None
            unwrapped_fields1197 = fields1196
            self.write("(<")
>>>>>>> origin/main
            self.indent_sexp()
            self.newline()
            field1198 = unwrapped_fields1197[0]
            self.pretty_term(field1198)
            self.newline()
            field1199 = unwrapped_fields1197[1]
            self.pretty_term(field1199)
<<<<<<< HEAD
            self.newline()
            field1200 = unwrapped_fields1197[2]
            self.pretty_term(field1200)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1206 = self._try_flat(msg, self.pretty_rel_term)
        if flat1206 is not None:
            assert flat1206 is not None
            self.write(flat1206)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1701 = _dollar_dollar.specialized_value
            else:
                _t1701 = None
            deconstruct_result1204 = _t1701
            if deconstruct_result1204 is not None:
                assert deconstruct_result1204 is not None
                unwrapped1205 = deconstruct_result1204
                self.pretty_specialized_value(unwrapped1205)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1702 = _dollar_dollar.term
                else:
                    _t1702 = None
                deconstruct_result1202 = _t1702
                if deconstruct_result1202 is not None:
                    assert deconstruct_result1202 is not None
                    unwrapped1203 = deconstruct_result1202
                    self.pretty_term(unwrapped1203)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1208 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1208 is not None:
            assert flat1208 is not None
            self.write(flat1208)
            return None
        else:
            fields1207 = msg
            self.write("#")
            self.pretty_raw_value(fields1207)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1215 = self._try_flat(msg, self.pretty_rel_atom)
=======
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1205 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1205 is not None:
            assert flat1205 is not None
            self.write(flat1205)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1770 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1770 = None
            fields1201 = _t1770
            assert fields1201 is not None
            unwrapped_fields1202 = fields1201
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1203 = unwrapped_fields1202[0]
            self.pretty_term(field1203)
            self.newline()
            field1204 = unwrapped_fields1202[1]
            self.pretty_term(field1204)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1210 = self._try_flat(msg, self.pretty_gt)
        if flat1210 is not None:
            assert flat1210 is not None
            self.write(flat1210)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1771 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1771 = None
            fields1206 = _t1771
            assert fields1206 is not None
            unwrapped_fields1207 = fields1206
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1208 = unwrapped_fields1207[0]
            self.pretty_term(field1208)
            self.newline()
            field1209 = unwrapped_fields1207[1]
            self.pretty_term(field1209)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1215 = self._try_flat(msg, self.pretty_gt_eq)
>>>>>>> origin/main
        if flat1215 is not None:
            assert flat1215 is not None
            self.write(flat1215)
            return None
        else:
            _dollar_dollar = msg
<<<<<<< HEAD
            fields1209 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1209 is not None
            unwrapped_fields1210 = fields1209
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1211 = unwrapped_fields1210[0]
            self.pretty_name(field1211)
            field1212 = unwrapped_fields1210[1]
            if not len(field1212) == 0:
                self.newline()
                for i1214, elem1213 in enumerate(field1212):
                    if (i1214 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1213)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1220 = self._try_flat(msg, self.pretty_cast)
        if flat1220 is not None:
            assert flat1220 is not None
            self.write(flat1220)
            return None
        else:
            _dollar_dollar = msg
            fields1216 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1216 is not None
            unwrapped_fields1217 = fields1216
            self.write("(cast")
=======
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1772 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1772 = None
            fields1211 = _t1772
            assert fields1211 is not None
            unwrapped_fields1212 = fields1211
            self.write("(>=")
>>>>>>> origin/main
            self.indent_sexp()
            self.newline()
            field1218 = unwrapped_fields1217[0]
            self.pretty_term(field1218)
            self.newline()
            field1219 = unwrapped_fields1217[1]
            self.pretty_term(field1219)
            self.dedent()
            self.write(")")

<<<<<<< HEAD
    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1224 = self._try_flat(msg, self.pretty_attrs)
        if flat1224 is not None:
            assert flat1224 is not None
            self.write(flat1224)
            return None
        else:
            fields1221 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1221) == 0:
                self.newline()
                for i1223, elem1222 in enumerate(fields1221):
                    if (i1223 > 0):
                        self.newline()
                    self.pretty_attribute(elem1222)
=======
    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1221 = self._try_flat(msg, self.pretty_add)
        if flat1221 is not None:
            assert flat1221 is not None
            self.write(flat1221)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1773 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1773 = None
            fields1216 = _t1773
            assert fields1216 is not None
            unwrapped_fields1217 = fields1216
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1218 = unwrapped_fields1217[0]
            self.pretty_term(field1218)
            self.newline()
            field1219 = unwrapped_fields1217[1]
            self.pretty_term(field1219)
            self.newline()
            field1220 = unwrapped_fields1217[2]
            self.pretty_term(field1220)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1227 = self._try_flat(msg, self.pretty_minus)
        if flat1227 is not None:
            assert flat1227 is not None
            self.write(flat1227)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1774 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1774 = None
            fields1222 = _t1774
            assert fields1222 is not None
            unwrapped_fields1223 = fields1222
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1224 = unwrapped_fields1223[0]
            self.pretty_term(field1224)
            self.newline()
            field1225 = unwrapped_fields1223[1]
            self.pretty_term(field1225)
            self.newline()
            field1226 = unwrapped_fields1223[2]
            self.pretty_term(field1226)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1233 = self._try_flat(msg, self.pretty_multiply)
        if flat1233 is not None:
            assert flat1233 is not None
            self.write(flat1233)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1775 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1775 = None
            fields1228 = _t1775
            assert fields1228 is not None
            unwrapped_fields1229 = fields1228
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1230 = unwrapped_fields1229[0]
            self.pretty_term(field1230)
            self.newline()
            field1231 = unwrapped_fields1229[1]
            self.pretty_term(field1231)
            self.newline()
            field1232 = unwrapped_fields1229[2]
            self.pretty_term(field1232)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1239 = self._try_flat(msg, self.pretty_divide)
        if flat1239 is not None:
            assert flat1239 is not None
            self.write(flat1239)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1776 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1776 = None
            fields1234 = _t1776
            assert fields1234 is not None
            unwrapped_fields1235 = fields1234
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1236 = unwrapped_fields1235[0]
            self.pretty_term(field1236)
            self.newline()
            field1237 = unwrapped_fields1235[1]
            self.pretty_term(field1237)
            self.newline()
            field1238 = unwrapped_fields1235[2]
            self.pretty_term(field1238)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1244 = self._try_flat(msg, self.pretty_rel_term)
        if flat1244 is not None:
            assert flat1244 is not None
            self.write(flat1244)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1777 = _dollar_dollar.specialized_value
            else:
                _t1777 = None
            deconstruct_result1242 = _t1777
            if deconstruct_result1242 is not None:
                assert deconstruct_result1242 is not None
                unwrapped1243 = deconstruct_result1242
                self.pretty_specialized_value(unwrapped1243)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1778 = _dollar_dollar.term
                else:
                    _t1778 = None
                deconstruct_result1240 = _t1778
                if deconstruct_result1240 is not None:
                    assert deconstruct_result1240 is not None
                    unwrapped1241 = deconstruct_result1240
                    self.pretty_term(unwrapped1241)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1246 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1246 is not None:
            assert flat1246 is not None
            self.write(flat1246)
            return None
        else:
            fields1245 = msg
            self.write("#")
            self.pretty_raw_value(fields1245)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1253 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1253 is not None:
            assert flat1253 is not None
            self.write(flat1253)
            return None
        else:
            _dollar_dollar = msg
            fields1247 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1247 is not None
            unwrapped_fields1248 = fields1247
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1249 = unwrapped_fields1248[0]
            self.pretty_name(field1249)
            field1250 = unwrapped_fields1248[1]
            if not len(field1250) == 0:
                self.newline()
                for i1252, elem1251 in enumerate(field1250):
                    if (i1252 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1251)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1258 = self._try_flat(msg, self.pretty_cast)
        if flat1258 is not None:
            assert flat1258 is not None
            self.write(flat1258)
            return None
        else:
            _dollar_dollar = msg
            fields1254 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1254 is not None
            unwrapped_fields1255 = fields1254
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1256 = unwrapped_fields1255[0]
            self.pretty_term(field1256)
            self.newline()
            field1257 = unwrapped_fields1255[1]
            self.pretty_term(field1257)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1262 = self._try_flat(msg, self.pretty_attrs)
        if flat1262 is not None:
            assert flat1262 is not None
            self.write(flat1262)
            return None
        else:
            fields1259 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1259) == 0:
                self.newline()
                for i1261, elem1260 in enumerate(fields1259):
                    if (i1261 > 0):
                        self.newline()
                    self.pretty_attribute(elem1260)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
<<<<<<< HEAD
        flat1231 = self._try_flat(msg, self.pretty_attribute)
        if flat1231 is not None:
            assert flat1231 is not None
            self.write(flat1231)
            return None
        else:
            _dollar_dollar = msg
            fields1225 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1225 is not None
            unwrapped_fields1226 = fields1225
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1227 = unwrapped_fields1226[0]
            self.pretty_name(field1227)
            field1228 = unwrapped_fields1226[1]
            if not len(field1228) == 0:
                self.newline()
                for i1230, elem1229 in enumerate(field1228):
                    if (i1230 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1229)
=======
        flat1269 = self._try_flat(msg, self.pretty_attribute)
        if flat1269 is not None:
            assert flat1269 is not None
            self.write(flat1269)
            return None
        else:
            _dollar_dollar = msg
            fields1263 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1263 is not None
            unwrapped_fields1264 = fields1263
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1265 = unwrapped_fields1264[0]
            self.pretty_name(field1265)
            field1266 = unwrapped_fields1264[1]
            if not len(field1266) == 0:
                self.newline()
                for i1268, elem1267 in enumerate(field1266):
                    if (i1268 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1267)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
<<<<<<< HEAD
        flat1240 = self._try_flat(msg, self.pretty_algorithm)
        if flat1240 is not None:
            assert flat1240 is not None
            self.write(flat1240)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1703 = _dollar_dollar.attrs
            else:
                _t1703 = None
            fields1232 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body, _t1703,)
            assert fields1232 is not None
            unwrapped_fields1233 = fields1232
            self.write("(algorithm")
            self.indent_sexp()
            field1234 = unwrapped_fields1233[0]
            if not len(field1234) == 0:
                self.newline()
                for i1236, elem1235 in enumerate(field1234):
                    if (i1236 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1235)
            self.newline()
            field1237 = unwrapped_fields1233[1]
            self.pretty_script(field1237)
            field1238 = unwrapped_fields1233[2]
            if field1238 is not None:
                self.newline()
                assert field1238 is not None
                opt_val1239 = field1238
                self.pretty_attrs(opt_val1239)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1245 = self._try_flat(msg, self.pretty_script)
        if flat1245 is not None:
            assert flat1245 is not None
            self.write(flat1245)
            return None
        else:
            _dollar_dollar = msg
            fields1241 = _dollar_dollar.constructs
            assert fields1241 is not None
            unwrapped_fields1242 = fields1241
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1242) == 0:
                self.newline()
                for i1244, elem1243 in enumerate(unwrapped_fields1242):
                    if (i1244 > 0):
                        self.newline()
                    self.pretty_construct(elem1243)
=======
        flat1278 = self._try_flat(msg, self.pretty_algorithm)
        if flat1278 is not None:
            assert flat1278 is not None
            self.write(flat1278)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1779 = _dollar_dollar.attrs
            else:
                _t1779 = None
            fields1270 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body, _t1779,)
            assert fields1270 is not None
            unwrapped_fields1271 = fields1270
            self.write("(algorithm")
            self.indent_sexp()
            field1272 = unwrapped_fields1271[0]
            if not len(field1272) == 0:
                self.newline()
                for i1274, elem1273 in enumerate(field1272):
                    if (i1274 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1273)
            self.newline()
            field1275 = unwrapped_fields1271[1]
            self.pretty_script(field1275)
            field1276 = unwrapped_fields1271[2]
            if field1276 is not None:
                self.newline()
                assert field1276 is not None
                opt_val1277 = field1276
                self.pretty_attrs(opt_val1277)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1283 = self._try_flat(msg, self.pretty_script)
        if flat1283 is not None:
            assert flat1283 is not None
            self.write(flat1283)
            return None
        else:
            _dollar_dollar = msg
            fields1279 = _dollar_dollar.constructs
            assert fields1279 is not None
            unwrapped_fields1280 = fields1279
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1280) == 0:
                self.newline()
                for i1282, elem1281 in enumerate(unwrapped_fields1280):
                    if (i1282 > 0):
                        self.newline()
                    self.pretty_construct(elem1281)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
<<<<<<< HEAD
        flat1250 = self._try_flat(msg, self.pretty_construct)
        if flat1250 is not None:
            assert flat1250 is not None
            self.write(flat1250)
=======
        flat1288 = self._try_flat(msg, self.pretty_construct)
        if flat1288 is not None:
            assert flat1288 is not None
            self.write(flat1288)
>>>>>>> origin/main
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
<<<<<<< HEAD
                _t1704 = _dollar_dollar.loop
            else:
                _t1704 = None
            deconstruct_result1248 = _t1704
            if deconstruct_result1248 is not None:
                assert deconstruct_result1248 is not None
                unwrapped1249 = deconstruct_result1248
                self.pretty_loop(unwrapped1249)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1705 = _dollar_dollar.instruction
                else:
                    _t1705 = None
                deconstruct_result1246 = _t1705
                if deconstruct_result1246 is not None:
                    assert deconstruct_result1246 is not None
                    unwrapped1247 = deconstruct_result1246
                    self.pretty_instruction(unwrapped1247)
=======
                _t1780 = _dollar_dollar.loop
            else:
                _t1780 = None
            deconstruct_result1286 = _t1780
            if deconstruct_result1286 is not None:
                assert deconstruct_result1286 is not None
                unwrapped1287 = deconstruct_result1286
                self.pretty_loop(unwrapped1287)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1781 = _dollar_dollar.instruction
                else:
                    _t1781 = None
                deconstruct_result1284 = _t1781
                if deconstruct_result1284 is not None:
                    assert deconstruct_result1284 is not None
                    unwrapped1285 = deconstruct_result1284
                    self.pretty_instruction(unwrapped1285)
>>>>>>> origin/main
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
<<<<<<< HEAD
        flat1257 = self._try_flat(msg, self.pretty_loop)
        if flat1257 is not None:
            assert flat1257 is not None
            self.write(flat1257)
=======
        flat1295 = self._try_flat(msg, self.pretty_loop)
        if flat1295 is not None:
            assert flat1295 is not None
            self.write(flat1295)
>>>>>>> origin/main
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
<<<<<<< HEAD
                _t1706 = _dollar_dollar.attrs
            else:
                _t1706 = None
            fields1251 = (_dollar_dollar.init, _dollar_dollar.body, _t1706,)
            assert fields1251 is not None
            unwrapped_fields1252 = fields1251
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1253 = unwrapped_fields1252[0]
            self.pretty_init(field1253)
            self.newline()
            field1254 = unwrapped_fields1252[1]
            self.pretty_script(field1254)
            field1255 = unwrapped_fields1252[2]
            if field1255 is not None:
                self.newline()
                assert field1255 is not None
                opt_val1256 = field1255
                self.pretty_attrs(opt_val1256)
=======
                _t1782 = _dollar_dollar.attrs
            else:
                _t1782 = None
            fields1289 = (_dollar_dollar.init, _dollar_dollar.body, _t1782,)
            assert fields1289 is not None
            unwrapped_fields1290 = fields1289
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1291 = unwrapped_fields1290[0]
            self.pretty_init(field1291)
            self.newline()
            field1292 = unwrapped_fields1290[1]
            self.pretty_script(field1292)
            field1293 = unwrapped_fields1290[2]
            if field1293 is not None:
                self.newline()
                assert field1293 is not None
                opt_val1294 = field1293
                self.pretty_attrs(opt_val1294)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
<<<<<<< HEAD
        flat1261 = self._try_flat(msg, self.pretty_init)
        if flat1261 is not None:
            assert flat1261 is not None
            self.write(flat1261)
            return None
        else:
            fields1258 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1258) == 0:
                self.newline()
                for i1260, elem1259 in enumerate(fields1258):
                    if (i1260 > 0):
                        self.newline()
                    self.pretty_instruction(elem1259)
=======
        flat1299 = self._try_flat(msg, self.pretty_init)
        if flat1299 is not None:
            assert flat1299 is not None
            self.write(flat1299)
            return None
        else:
            fields1296 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1296) == 0:
                self.newline()
                for i1298, elem1297 in enumerate(fields1296):
                    if (i1298 > 0):
                        self.newline()
                    self.pretty_instruction(elem1297)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
<<<<<<< HEAD
        flat1272 = self._try_flat(msg, self.pretty_instruction)
        if flat1272 is not None:
            assert flat1272 is not None
            self.write(flat1272)
=======
        flat1310 = self._try_flat(msg, self.pretty_instruction)
        if flat1310 is not None:
            assert flat1310 is not None
            self.write(flat1310)
>>>>>>> origin/main
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
<<<<<<< HEAD
                _t1707 = _dollar_dollar.assign
            else:
                _t1707 = None
            deconstruct_result1270 = _t1707
            if deconstruct_result1270 is not None:
                assert deconstruct_result1270 is not None
                unwrapped1271 = deconstruct_result1270
                self.pretty_assign(unwrapped1271)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1708 = _dollar_dollar.upsert
                else:
                    _t1708 = None
                deconstruct_result1268 = _t1708
                if deconstruct_result1268 is not None:
                    assert deconstruct_result1268 is not None
                    unwrapped1269 = deconstruct_result1268
                    self.pretty_upsert(unwrapped1269)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1709 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1709 = None
                    deconstruct_result1266 = _t1709
                    if deconstruct_result1266 is not None:
                        assert deconstruct_result1266 is not None
                        unwrapped1267 = deconstruct_result1266
                        self.pretty_break(unwrapped1267)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1710 = _dollar_dollar.monoid_def
                        else:
                            _t1710 = None
                        deconstruct_result1264 = _t1710
                        if deconstruct_result1264 is not None:
                            assert deconstruct_result1264 is not None
                            unwrapped1265 = deconstruct_result1264
                            self.pretty_monoid_def(unwrapped1265)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1711 = _dollar_dollar.monus_def
                            else:
                                _t1711 = None
                            deconstruct_result1262 = _t1711
                            if deconstruct_result1262 is not None:
                                assert deconstruct_result1262 is not None
                                unwrapped1263 = deconstruct_result1262
                                self.pretty_monus_def(unwrapped1263)
=======
                _t1783 = _dollar_dollar.assign
            else:
                _t1783 = None
            deconstruct_result1308 = _t1783
            if deconstruct_result1308 is not None:
                assert deconstruct_result1308 is not None
                unwrapped1309 = deconstruct_result1308
                self.pretty_assign(unwrapped1309)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1784 = _dollar_dollar.upsert
                else:
                    _t1784 = None
                deconstruct_result1306 = _t1784
                if deconstruct_result1306 is not None:
                    assert deconstruct_result1306 is not None
                    unwrapped1307 = deconstruct_result1306
                    self.pretty_upsert(unwrapped1307)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1785 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1785 = None
                    deconstruct_result1304 = _t1785
                    if deconstruct_result1304 is not None:
                        assert deconstruct_result1304 is not None
                        unwrapped1305 = deconstruct_result1304
                        self.pretty_break(unwrapped1305)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1786 = _dollar_dollar.monoid_def
                        else:
                            _t1786 = None
                        deconstruct_result1302 = _t1786
                        if deconstruct_result1302 is not None:
                            assert deconstruct_result1302 is not None
                            unwrapped1303 = deconstruct_result1302
                            self.pretty_monoid_def(unwrapped1303)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1787 = _dollar_dollar.monus_def
                            else:
                                _t1787 = None
                            deconstruct_result1300 = _t1787
                            if deconstruct_result1300 is not None:
                                assert deconstruct_result1300 is not None
                                unwrapped1301 = deconstruct_result1300
                                self.pretty_monus_def(unwrapped1301)
>>>>>>> origin/main
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
<<<<<<< HEAD
        flat1279 = self._try_flat(msg, self.pretty_assign)
        if flat1279 is not None:
            assert flat1279 is not None
            self.write(flat1279)
=======
        flat1317 = self._try_flat(msg, self.pretty_assign)
        if flat1317 is not None:
            assert flat1317 is not None
            self.write(flat1317)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1788 = _dollar_dollar.attrs
            else:
                _t1788 = None
            fields1311 = (_dollar_dollar.name, _dollar_dollar.body, _t1788,)
            assert fields1311 is not None
            unwrapped_fields1312 = fields1311
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1313 = unwrapped_fields1312[0]
            self.pretty_relation_id(field1313)
            self.newline()
            field1314 = unwrapped_fields1312[1]
            self.pretty_abstraction(field1314)
            field1315 = unwrapped_fields1312[2]
            if field1315 is not None:
                self.newline()
                assert field1315 is not None
                opt_val1316 = field1315
                self.pretty_attrs(opt_val1316)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1324 = self._try_flat(msg, self.pretty_upsert)
        if flat1324 is not None:
            assert flat1324 is not None
            self.write(flat1324)
>>>>>>> origin/main
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
<<<<<<< HEAD
                _t1712 = _dollar_dollar.attrs
            else:
                _t1712 = None
            fields1273 = (_dollar_dollar.name, _dollar_dollar.body, _t1712,)
            assert fields1273 is not None
            unwrapped_fields1274 = fields1273
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1275 = unwrapped_fields1274[0]
            self.pretty_relation_id(field1275)
            self.newline()
            field1276 = unwrapped_fields1274[1]
            self.pretty_abstraction(field1276)
            field1277 = unwrapped_fields1274[2]
            if field1277 is not None:
                self.newline()
                assert field1277 is not None
                opt_val1278 = field1277
                self.pretty_attrs(opt_val1278)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1286 = self._try_flat(msg, self.pretty_upsert)
        if flat1286 is not None:
            assert flat1286 is not None
            self.write(flat1286)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1713 = _dollar_dollar.attrs
            else:
                _t1713 = None
            fields1280 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1713,)
            assert fields1280 is not None
            unwrapped_fields1281 = fields1280
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1282 = unwrapped_fields1281[0]
            self.pretty_relation_id(field1282)
            self.newline()
            field1283 = unwrapped_fields1281[1]
            self.pretty_abstraction_with_arity(field1283)
            field1284 = unwrapped_fields1281[2]
            if field1284 is not None:
                self.newline()
                assert field1284 is not None
                opt_val1285 = field1284
                self.pretty_attrs(opt_val1285)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1291 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1291 is not None:
            assert flat1291 is not None
            self.write(flat1291)
            return None
        else:
            _dollar_dollar = msg
            _t1714 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1287 = (_t1714, _dollar_dollar[0].value,)
            assert fields1287 is not None
            unwrapped_fields1288 = fields1287
            self.write("(")
            self.indent()
            field1289 = unwrapped_fields1288[0]
            self.pretty_bindings(field1289)
            self.newline()
            field1290 = unwrapped_fields1288[1]
            self.pretty_formula(field1290)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1298 = self._try_flat(msg, self.pretty_break)
        if flat1298 is not None:
            assert flat1298 is not None
            self.write(flat1298)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1715 = _dollar_dollar.attrs
            else:
                _t1715 = None
            fields1292 = (_dollar_dollar.name, _dollar_dollar.body, _t1715,)
            assert fields1292 is not None
            unwrapped_fields1293 = fields1292
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1294 = unwrapped_fields1293[0]
            self.pretty_relation_id(field1294)
            self.newline()
            field1295 = unwrapped_fields1293[1]
            self.pretty_abstraction(field1295)
            field1296 = unwrapped_fields1293[2]
            if field1296 is not None:
                self.newline()
                assert field1296 is not None
                opt_val1297 = field1296
                self.pretty_attrs(opt_val1297)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1306 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1306 is not None:
            assert flat1306 is not None
            self.write(flat1306)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1716 = _dollar_dollar.attrs
            else:
                _t1716 = None
            fields1299 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1716,)
            assert fields1299 is not None
            unwrapped_fields1300 = fields1299
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1301 = unwrapped_fields1300[0]
            self.pretty_monoid(field1301)
            self.newline()
            field1302 = unwrapped_fields1300[1]
            self.pretty_relation_id(field1302)
            self.newline()
            field1303 = unwrapped_fields1300[2]
            self.pretty_abstraction_with_arity(field1303)
            field1304 = unwrapped_fields1300[3]
            if field1304 is not None:
                self.newline()
                assert field1304 is not None
                opt_val1305 = field1304
                self.pretty_attrs(opt_val1305)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1315 = self._try_flat(msg, self.pretty_monoid)
        if flat1315 is not None:
            assert flat1315 is not None
            self.write(flat1315)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1717 = _dollar_dollar.or_monoid
            else:
                _t1717 = None
            deconstruct_result1313 = _t1717
            if deconstruct_result1313 is not None:
                assert deconstruct_result1313 is not None
                unwrapped1314 = deconstruct_result1313
                self.pretty_or_monoid(unwrapped1314)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1718 = _dollar_dollar.min_monoid
                else:
                    _t1718 = None
                deconstruct_result1311 = _t1718
                if deconstruct_result1311 is not None:
                    assert deconstruct_result1311 is not None
                    unwrapped1312 = deconstruct_result1311
                    self.pretty_min_monoid(unwrapped1312)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1719 = _dollar_dollar.max_monoid
                    else:
                        _t1719 = None
                    deconstruct_result1309 = _t1719
                    if deconstruct_result1309 is not None:
                        assert deconstruct_result1309 is not None
                        unwrapped1310 = deconstruct_result1309
                        self.pretty_max_monoid(unwrapped1310)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1720 = _dollar_dollar.sum_monoid
                        else:
                            _t1720 = None
                        deconstruct_result1307 = _t1720
                        if deconstruct_result1307 is not None:
                            assert deconstruct_result1307 is not None
                            unwrapped1308 = deconstruct_result1307
                            self.pretty_sum_monoid(unwrapped1308)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1316 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1319 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1319 is not None:
            assert flat1319 is not None
            self.write(flat1319)
            return None
        else:
            _dollar_dollar = msg
            fields1317 = _dollar_dollar.type
            assert fields1317 is not None
            unwrapped_fields1318 = fields1317
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1318)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1322 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1322 is not None:
            assert flat1322 is not None
            self.write(flat1322)
            return None
        else:
            _dollar_dollar = msg
            fields1320 = _dollar_dollar.type
            assert fields1320 is not None
            unwrapped_fields1321 = fields1320
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1321)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1325 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1325 is not None:
            assert flat1325 is not None
            self.write(flat1325)
            return None
        else:
            _dollar_dollar = msg
            fields1323 = _dollar_dollar.type
            assert fields1323 is not None
            unwrapped_fields1324 = fields1323
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1324)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1333 = self._try_flat(msg, self.pretty_monus_def)
        if flat1333 is not None:
            assert flat1333 is not None
            self.write(flat1333)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1721 = _dollar_dollar.attrs
            else:
                _t1721 = None
            fields1326 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1721,)
            assert fields1326 is not None
            unwrapped_fields1327 = fields1326
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1328 = unwrapped_fields1327[0]
            self.pretty_monoid(field1328)
            self.newline()
            field1329 = unwrapped_fields1327[1]
            self.pretty_relation_id(field1329)
            self.newline()
            field1330 = unwrapped_fields1327[2]
            self.pretty_abstraction_with_arity(field1330)
            field1331 = unwrapped_fields1327[3]
            if field1331 is not None:
                self.newline()
                assert field1331 is not None
                opt_val1332 = field1331
                self.pretty_attrs(opt_val1332)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1340 = self._try_flat(msg, self.pretty_constraint)
        if flat1340 is not None:
            assert flat1340 is not None
            self.write(flat1340)
            return None
        else:
            _dollar_dollar = msg
            fields1334 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1334 is not None
            unwrapped_fields1335 = fields1334
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1336 = unwrapped_fields1335[0]
            self.pretty_relation_id(field1336)
            self.newline()
            field1337 = unwrapped_fields1335[1]
            self.pretty_abstraction(field1337)
            self.newline()
            field1338 = unwrapped_fields1335[2]
            self.pretty_functional_dependency_keys(field1338)
            self.newline()
            field1339 = unwrapped_fields1335[3]
            self.pretty_functional_dependency_values(field1339)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1344 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1344 is not None:
            assert flat1344 is not None
            self.write(flat1344)
            return None
        else:
            fields1341 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1341) == 0:
                self.newline()
                for i1343, elem1342 in enumerate(fields1341):
                    if (i1343 > 0):
                        self.newline()
                    self.pretty_var(elem1342)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1348 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1348 is not None:
            assert flat1348 is not None
            self.write(flat1348)
            return None
        else:
            fields1345 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1345) == 0:
                self.newline()
                for i1347, elem1346 in enumerate(fields1345):
                    if (i1347 > 0):
                        self.newline()
                    self.pretty_var(elem1346)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1357 = self._try_flat(msg, self.pretty_data)
        if flat1357 is not None:
            assert flat1357 is not None
            self.write(flat1357)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1722 = _dollar_dollar.edb
            else:
                _t1722 = None
            deconstruct_result1355 = _t1722
            if deconstruct_result1355 is not None:
                assert deconstruct_result1355 is not None
                unwrapped1356 = deconstruct_result1355
                self.pretty_edb(unwrapped1356)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1723 = _dollar_dollar.betree_relation
                else:
                    _t1723 = None
                deconstruct_result1353 = _t1723
                if deconstruct_result1353 is not None:
                    assert deconstruct_result1353 is not None
                    unwrapped1354 = deconstruct_result1353
                    self.pretty_betree_relation(unwrapped1354)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1724 = _dollar_dollar.csv_data
                    else:
                        _t1724 = None
                    deconstruct_result1351 = _t1724
                    if deconstruct_result1351 is not None:
                        assert deconstruct_result1351 is not None
                        unwrapped1352 = deconstruct_result1351
                        self.pretty_csv_data(unwrapped1352)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1725 = _dollar_dollar.iceberg_data
                        else:
                            _t1725 = None
                        deconstruct_result1349 = _t1725
                        if deconstruct_result1349 is not None:
                            assert deconstruct_result1349 is not None
                            unwrapped1350 = deconstruct_result1349
                            self.pretty_iceberg_data(unwrapped1350)
=======
                _t1789 = _dollar_dollar.attrs
            else:
                _t1789 = None
            fields1318 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1789,)
            assert fields1318 is not None
            unwrapped_fields1319 = fields1318
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1320 = unwrapped_fields1319[0]
            self.pretty_relation_id(field1320)
            self.newline()
            field1321 = unwrapped_fields1319[1]
            self.pretty_abstraction_with_arity(field1321)
            field1322 = unwrapped_fields1319[2]
            if field1322 is not None:
                self.newline()
                assert field1322 is not None
                opt_val1323 = field1322
                self.pretty_attrs(opt_val1323)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1329 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1329 is not None:
            assert flat1329 is not None
            self.write(flat1329)
            return None
        else:
            _dollar_dollar = msg
            _t1790 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1325 = (_t1790, _dollar_dollar[0].value,)
            assert fields1325 is not None
            unwrapped_fields1326 = fields1325
            self.write("(")
            self.indent()
            field1327 = unwrapped_fields1326[0]
            self.pretty_bindings(field1327)
            self.newline()
            field1328 = unwrapped_fields1326[1]
            self.pretty_formula(field1328)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1336 = self._try_flat(msg, self.pretty_break)
        if flat1336 is not None:
            assert flat1336 is not None
            self.write(flat1336)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1791 = _dollar_dollar.attrs
            else:
                _t1791 = None
            fields1330 = (_dollar_dollar.name, _dollar_dollar.body, _t1791,)
            assert fields1330 is not None
            unwrapped_fields1331 = fields1330
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1332 = unwrapped_fields1331[0]
            self.pretty_relation_id(field1332)
            self.newline()
            field1333 = unwrapped_fields1331[1]
            self.pretty_abstraction(field1333)
            field1334 = unwrapped_fields1331[2]
            if field1334 is not None:
                self.newline()
                assert field1334 is not None
                opt_val1335 = field1334
                self.pretty_attrs(opt_val1335)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1344 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1344 is not None:
            assert flat1344 is not None
            self.write(flat1344)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1792 = _dollar_dollar.attrs
            else:
                _t1792 = None
            fields1337 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1792,)
            assert fields1337 is not None
            unwrapped_fields1338 = fields1337
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1339 = unwrapped_fields1338[0]
            self.pretty_monoid(field1339)
            self.newline()
            field1340 = unwrapped_fields1338[1]
            self.pretty_relation_id(field1340)
            self.newline()
            field1341 = unwrapped_fields1338[2]
            self.pretty_abstraction_with_arity(field1341)
            field1342 = unwrapped_fields1338[3]
            if field1342 is not None:
                self.newline()
                assert field1342 is not None
                opt_val1343 = field1342
                self.pretty_attrs(opt_val1343)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1353 = self._try_flat(msg, self.pretty_monoid)
        if flat1353 is not None:
            assert flat1353 is not None
            self.write(flat1353)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1793 = _dollar_dollar.or_monoid
            else:
                _t1793 = None
            deconstruct_result1351 = _t1793
            if deconstruct_result1351 is not None:
                assert deconstruct_result1351 is not None
                unwrapped1352 = deconstruct_result1351
                self.pretty_or_monoid(unwrapped1352)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1794 = _dollar_dollar.min_monoid
                else:
                    _t1794 = None
                deconstruct_result1349 = _t1794
                if deconstruct_result1349 is not None:
                    assert deconstruct_result1349 is not None
                    unwrapped1350 = deconstruct_result1349
                    self.pretty_min_monoid(unwrapped1350)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1795 = _dollar_dollar.max_monoid
                    else:
                        _t1795 = None
                    deconstruct_result1347 = _t1795
                    if deconstruct_result1347 is not None:
                        assert deconstruct_result1347 is not None
                        unwrapped1348 = deconstruct_result1347
                        self.pretty_max_monoid(unwrapped1348)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1796 = _dollar_dollar.sum_monoid
                        else:
                            _t1796 = None
                        deconstruct_result1345 = _t1796
                        if deconstruct_result1345 is not None:
                            assert deconstruct_result1345 is not None
                            unwrapped1346 = deconstruct_result1345
                            self.pretty_sum_monoid(unwrapped1346)
>>>>>>> origin/main
                        else:
                            raise ParseError("No matching rule for monoid")

<<<<<<< HEAD
    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1363 = self._try_flat(msg, self.pretty_edb)
        if flat1363 is not None:
            assert flat1363 is not None
            self.write(flat1363)
            return None
        else:
            _dollar_dollar = msg
            fields1358 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1358 is not None
            unwrapped_fields1359 = fields1358
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1360 = unwrapped_fields1359[0]
            self.pretty_relation_id(field1360)
            self.newline()
            field1361 = unwrapped_fields1359[1]
            self.pretty_edb_path(field1361)
            self.newline()
            field1362 = unwrapped_fields1359[2]
            self.pretty_edb_types(field1362)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1367 = self._try_flat(msg, self.pretty_edb_path)
        if flat1367 is not None:
            assert flat1367 is not None
            self.write(flat1367)
            return None
        else:
            fields1364 = msg
            self.write("[")
            self.indent()
            for i1366, elem1365 in enumerate(fields1364):
                if (i1366 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1365))
=======
    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1354 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1357 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1357 is not None:
            assert flat1357 is not None
            self.write(flat1357)
            return None
        else:
            _dollar_dollar = msg
            fields1355 = _dollar_dollar.type
            assert fields1355 is not None
            unwrapped_fields1356 = fields1355
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1356)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1360 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1360 is not None:
            assert flat1360 is not None
            self.write(flat1360)
            return None
        else:
            _dollar_dollar = msg
            fields1358 = _dollar_dollar.type
            assert fields1358 is not None
            unwrapped_fields1359 = fields1358
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1359)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

<<<<<<< HEAD
    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1371 = self._try_flat(msg, self.pretty_edb_types)
=======
    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1363 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1363 is not None:
            assert flat1363 is not None
            self.write(flat1363)
            return None
        else:
            _dollar_dollar = msg
            fields1361 = _dollar_dollar.type
            assert fields1361 is not None
            unwrapped_fields1362 = fields1361
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1362)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1371 = self._try_flat(msg, self.pretty_monus_def)
>>>>>>> origin/main
        if flat1371 is not None:
            assert flat1371 is not None
            self.write(flat1371)
            return None
        else:
            fields1368 = msg
            self.write("[")
            self.indent()
            for i1370, elem1369 in enumerate(fields1368):
                if (i1370 > 0):
                    self.newline()
                self.pretty_type(elem1369)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1376 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1376 is not None:
            assert flat1376 is not None
            self.write(flat1376)
            return None
        else:
            _dollar_dollar = msg
<<<<<<< HEAD
            fields1372 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1372 is not None
            unwrapped_fields1373 = fields1372
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1374 = unwrapped_fields1373[0]
            self.pretty_relation_id(field1374)
            self.newline()
            field1375 = unwrapped_fields1373[1]
            self.pretty_betree_info(field1375)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1382 = self._try_flat(msg, self.pretty_betree_info)
        if flat1382 is not None:
            assert flat1382 is not None
            self.write(flat1382)
            return None
        else:
            _dollar_dollar = msg
            _t1726 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1377 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1726,)
            assert fields1377 is not None
            unwrapped_fields1378 = fields1377
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1379 = unwrapped_fields1378[0]
            self.pretty_betree_info_key_types(field1379)
            self.newline()
            field1380 = unwrapped_fields1378[1]
            self.pretty_betree_info_value_types(field1380)
            self.newline()
            field1381 = unwrapped_fields1378[2]
            self.pretty_config_dict(field1381)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1386 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1386 is not None:
            assert flat1386 is not None
            self.write(flat1386)
            return None
        else:
            fields1383 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1383) == 0:
                self.newline()
                for i1385, elem1384 in enumerate(fields1383):
                    if (i1385 > 0):
                        self.newline()
                    self.pretty_type(elem1384)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1390 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1390 is not None:
            assert flat1390 is not None
            self.write(flat1390)
            return None
        else:
            fields1387 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1387) == 0:
                self.newline()
                for i1389, elem1388 in enumerate(fields1387):
                    if (i1389 > 0):
                        self.newline()
                    self.pretty_type(elem1388)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1397 = self._try_flat(msg, self.pretty_csv_data)
        if flat1397 is not None:
            assert flat1397 is not None
            self.write(flat1397)
            return None
        else:
            _dollar_dollar = msg
            fields1391 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1391 is not None
            unwrapped_fields1392 = fields1391
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1393 = unwrapped_fields1392[0]
            self.pretty_csvlocator(field1393)
            self.newline()
            field1394 = unwrapped_fields1392[1]
            self.pretty_csv_config(field1394)
            self.newline()
            field1395 = unwrapped_fields1392[2]
            self.pretty_gnf_columns(field1395)
            self.newline()
            field1396 = unwrapped_fields1392[3]
            self.pretty_csv_asof(field1396)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1404 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1404 is not None:
            assert flat1404 is not None
            self.write(flat1404)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1727 = _dollar_dollar.paths
            else:
                _t1727 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1728 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1728 = None
            fields1398 = (_t1727, _t1728,)
            assert fields1398 is not None
            unwrapped_fields1399 = fields1398
            self.write("(csv_locator")
            self.indent_sexp()
            field1400 = unwrapped_fields1399[0]
            if field1400 is not None:
                self.newline()
                assert field1400 is not None
                opt_val1401 = field1400
                self.pretty_csv_locator_paths(opt_val1401)
            field1402 = unwrapped_fields1399[1]
            if field1402 is not None:
                self.newline()
                assert field1402 is not None
                opt_val1403 = field1402
                self.pretty_csv_locator_inline_data(opt_val1403)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1408 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1408 is not None:
            assert flat1408 is not None
            self.write(flat1408)
            return None
        else:
            fields1405 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1405) == 0:
                self.newline()
                for i1407, elem1406 in enumerate(fields1405):
                    if (i1407 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1406))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1410 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1410 is not None:
            assert flat1410 is not None
            self.write(flat1410)
            return None
        else:
            fields1409 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1409))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1416 = self._try_flat(msg, self.pretty_csv_config)
        if flat1416 is not None:
            assert flat1416 is not None
            self.write(flat1416)
            return None
        else:
            _dollar_dollar = msg
            _t1729 = self.deconstruct_csv_config(_dollar_dollar)
            _t1730 = self.deconstruct_csv_storage_integration_optional(_dollar_dollar)
            fields1411 = (_t1729, _t1730,)
            assert fields1411 is not None
            unwrapped_fields1412 = fields1411
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            field1413 = unwrapped_fields1412[0]
            self.pretty_config_dict(field1413)
            field1414 = unwrapped_fields1412[1]
            if field1414 is not None:
                self.newline()
                assert field1414 is not None
                opt_val1415 = field1414
                self.pretty__storage_integration(opt_val1415)
            self.dedent()
            self.write(")")

    def pretty__storage_integration(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat1418 = self._try_flat(msg, self.pretty__storage_integration)
        if flat1418 is not None:
            assert flat1418 is not None
            self.write(flat1418)
            return None
        else:
            fields1417 = msg
            self.write("(storage_integration")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(fields1417)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1422 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1422 is not None:
            assert flat1422 is not None
            self.write(flat1422)
            return None
        else:
            fields1419 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1419) == 0:
                self.newline()
                for i1421, elem1420 in enumerate(fields1419):
                    if (i1421 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1420)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1431 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1431 is not None:
            assert flat1431 is not None
            self.write(flat1431)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1731 = _dollar_dollar.target_id
            else:
                _t1731 = None
            fields1423 = (_dollar_dollar.column_path, _t1731, _dollar_dollar.types,)
            assert fields1423 is not None
            unwrapped_fields1424 = fields1423
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1425 = unwrapped_fields1424[0]
            self.pretty_gnf_column_path(field1425)
            field1426 = unwrapped_fields1424[1]
            if field1426 is not None:
                self.newline()
                assert field1426 is not None
                opt_val1427 = field1426
                self.pretty_relation_id(opt_val1427)
            self.newline()
            self.write("[")
            field1428 = unwrapped_fields1424[2]
            for i1430, elem1429 in enumerate(field1428):
                if (i1430 > 0):
                    self.newline()
                self.pretty_type(elem1429)
=======
            if not len(_dollar_dollar.attrs) == 0:
                _t1797 = _dollar_dollar.attrs
            else:
                _t1797 = None
            fields1364 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1797,)
            assert fields1364 is not None
            unwrapped_fields1365 = fields1364
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1366 = unwrapped_fields1365[0]
            self.pretty_monoid(field1366)
            self.newline()
            field1367 = unwrapped_fields1365[1]
            self.pretty_relation_id(field1367)
            self.newline()
            field1368 = unwrapped_fields1365[2]
            self.pretty_abstraction_with_arity(field1368)
            field1369 = unwrapped_fields1365[3]
            if field1369 is not None:
                self.newline()
                assert field1369 is not None
                opt_val1370 = field1369
                self.pretty_attrs(opt_val1370)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1378 = self._try_flat(msg, self.pretty_constraint)
        if flat1378 is not None:
            assert flat1378 is not None
            self.write(flat1378)
            return None
        else:
            _dollar_dollar = msg
            fields1372 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1372 is not None
            unwrapped_fields1373 = fields1372
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1374 = unwrapped_fields1373[0]
            self.pretty_relation_id(field1374)
            self.newline()
            field1375 = unwrapped_fields1373[1]
            self.pretty_abstraction(field1375)
            self.newline()
            field1376 = unwrapped_fields1373[2]
            self.pretty_functional_dependency_keys(field1376)
            self.newline()
            field1377 = unwrapped_fields1373[3]
            self.pretty_functional_dependency_values(field1377)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1382 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1382 is not None:
            assert flat1382 is not None
            self.write(flat1382)
            return None
        else:
            fields1379 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1379) == 0:
                self.newline()
                for i1381, elem1380 in enumerate(fields1379):
                    if (i1381 > 0):
                        self.newline()
                    self.pretty_var(elem1380)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1386 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1386 is not None:
            assert flat1386 is not None
            self.write(flat1386)
            return None
        else:
            fields1383 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1383) == 0:
                self.newline()
                for i1385, elem1384 in enumerate(fields1383):
                    if (i1385 > 0):
                        self.newline()
                    self.pretty_var(elem1384)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1395 = self._try_flat(msg, self.pretty_data)
        if flat1395 is not None:
            assert flat1395 is not None
            self.write(flat1395)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1798 = _dollar_dollar.edb
            else:
                _t1798 = None
            deconstruct_result1393 = _t1798
            if deconstruct_result1393 is not None:
                assert deconstruct_result1393 is not None
                unwrapped1394 = deconstruct_result1393
                self.pretty_edb(unwrapped1394)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1799 = _dollar_dollar.betree_relation
                else:
                    _t1799 = None
                deconstruct_result1391 = _t1799
                if deconstruct_result1391 is not None:
                    assert deconstruct_result1391 is not None
                    unwrapped1392 = deconstruct_result1391
                    self.pretty_betree_relation(unwrapped1392)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1800 = _dollar_dollar.csv_data
                    else:
                        _t1800 = None
                    deconstruct_result1389 = _t1800
                    if deconstruct_result1389 is not None:
                        assert deconstruct_result1389 is not None
                        unwrapped1390 = deconstruct_result1389
                        self.pretty_csv_data(unwrapped1390)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1801 = _dollar_dollar.iceberg_data
                        else:
                            _t1801 = None
                        deconstruct_result1387 = _t1801
                        if deconstruct_result1387 is not None:
                            assert deconstruct_result1387 is not None
                            unwrapped1388 = deconstruct_result1387
                            self.pretty_iceberg_data(unwrapped1388)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1401 = self._try_flat(msg, self.pretty_edb)
        if flat1401 is not None:
            assert flat1401 is not None
            self.write(flat1401)
            return None
        else:
            _dollar_dollar = msg
            fields1396 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1396 is not None
            unwrapped_fields1397 = fields1396
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1398 = unwrapped_fields1397[0]
            self.pretty_relation_id(field1398)
            self.newline()
            field1399 = unwrapped_fields1397[1]
            self.pretty_edb_path(field1399)
            self.newline()
            field1400 = unwrapped_fields1397[2]
            self.pretty_edb_types(field1400)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1405 = self._try_flat(msg, self.pretty_edb_path)
        if flat1405 is not None:
            assert flat1405 is not None
            self.write(flat1405)
            return None
        else:
            fields1402 = msg
            self.write("[")
            self.indent()
            for i1404, elem1403 in enumerate(fields1402):
                if (i1404 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1403))
            self.dedent()
>>>>>>> origin/main
            self.write("]")

<<<<<<< HEAD
    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1438 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1438 is not None:
            assert flat1438 is not None
            self.write(flat1438)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1732 = _dollar_dollar[0]
            else:
                _t1732 = None
            deconstruct_result1436 = _t1732
            if deconstruct_result1436 is not None:
                assert deconstruct_result1436 is not None
                unwrapped1437 = deconstruct_result1436
                self.write(self.format_string_value(unwrapped1437))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1733 = _dollar_dollar
                else:
                    _t1733 = None
                deconstruct_result1432 = _t1733
                if deconstruct_result1432 is not None:
                    assert deconstruct_result1432 is not None
                    unwrapped1433 = deconstruct_result1432
                    self.write("[")
                    self.indent()
                    for i1435, elem1434 in enumerate(unwrapped1433):
                        if (i1435 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1434))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1440 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1440 is not None:
            assert flat1440 is not None
            self.write(flat1440)
            return None
        else:
            fields1439 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1439))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1451 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1451 is not None:
            assert flat1451 is not None
            self.write(flat1451)
            return None
        else:
            _dollar_dollar = msg
            _t1734 = self.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
            _t1735 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1441 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1734, _t1735, _dollar_dollar.returns_delta,)
            assert fields1441 is not None
            unwrapped_fields1442 = fields1441
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1443 = unwrapped_fields1442[0]
            self.pretty_iceberg_locator(field1443)
            self.newline()
            field1444 = unwrapped_fields1442[1]
            self.pretty_iceberg_catalog_config(field1444)
            self.newline()
            field1445 = unwrapped_fields1442[2]
            self.pretty_gnf_columns(field1445)
            field1446 = unwrapped_fields1442[3]
            if field1446 is not None:
                self.newline()
                assert field1446 is not None
                opt_val1447 = field1446
                self.pretty_iceberg_from_snapshot(opt_val1447)
            field1448 = unwrapped_fields1442[4]
            if field1448 is not None:
                self.newline()
                assert field1448 is not None
                opt_val1449 = field1448
                self.pretty_iceberg_to_snapshot(opt_val1449)
            self.newline()
            field1450 = unwrapped_fields1442[5]
            self.pretty_boolean_value(field1450)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1457 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1457 is not None:
            assert flat1457 is not None
            self.write(flat1457)
            return None
        else:
            _dollar_dollar = msg
            fields1452 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1452 is not None
            unwrapped_fields1453 = fields1452
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            field1454 = unwrapped_fields1453[0]
            self.pretty_iceberg_locator_table_name(field1454)
            self.newline()
            field1455 = unwrapped_fields1453[1]
            self.pretty_iceberg_locator_namespace(field1455)
            self.newline()
            field1456 = unwrapped_fields1453[2]
            self.pretty_iceberg_locator_warehouse(field1456)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_table_name(self, msg: str):
        flat1459 = self._try_flat(msg, self.pretty_iceberg_locator_table_name)
        if flat1459 is not None:
            assert flat1459 is not None
            self.write(flat1459)
            return None
        else:
            fields1458 = msg
            self.write("(table_name")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1458))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_namespace(self, msg: Sequence[str]):
        flat1463 = self._try_flat(msg, self.pretty_iceberg_locator_namespace)
        if flat1463 is not None:
            assert flat1463 is not None
            self.write(flat1463)
            return None
        else:
            fields1460 = msg
            self.write("(namespace")
            self.indent_sexp()
            if not len(fields1460) == 0:
                self.newline()
                for i1462, elem1461 in enumerate(fields1460):
                    if (i1462 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1461))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_warehouse(self, msg: str):
        flat1465 = self._try_flat(msg, self.pretty_iceberg_locator_warehouse)
        if flat1465 is not None:
            assert flat1465 is not None
            self.write(flat1465)
            return None
        else:
            fields1464 = msg
            self.write("(warehouse")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1464))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1473 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1473 is not None:
            assert flat1473 is not None
            self.write(flat1473)
            return None
        else:
            _dollar_dollar = msg
            _t1736 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1466 = (_dollar_dollar.catalog_uri, _t1736, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1466 is not None
            unwrapped_fields1467 = fields1466
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            field1468 = unwrapped_fields1467[0]
            self.pretty_iceberg_catalog_uri(field1468)
            field1469 = unwrapped_fields1467[1]
            if field1469 is not None:
                self.newline()
                assert field1469 is not None
                opt_val1470 = field1469
                self.pretty_iceberg_catalog_config_scope(opt_val1470)
            self.newline()
            field1471 = unwrapped_fields1467[2]
            self.pretty_iceberg_properties(field1471)
            self.newline()
            field1472 = unwrapped_fields1467[3]
            self.pretty_iceberg_auth_properties(field1472)
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_uri(self, msg: str):
        flat1475 = self._try_flat(msg, self.pretty_iceberg_catalog_uri)
        if flat1475 is not None:
            assert flat1475 is not None
            self.write(flat1475)
            return None
        else:
            fields1474 = msg
            self.write("(catalog_uri")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1474))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1477 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1477 is not None:
            assert flat1477 is not None
            self.write(flat1477)
            return None
        else:
            fields1476 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1476))
            self.dedent()
            self.write(")")

    def pretty_iceberg_properties(self, msg: Sequence[tuple[str, str]]):
        flat1481 = self._try_flat(msg, self.pretty_iceberg_properties)
        if flat1481 is not None:
            assert flat1481 is not None
            self.write(flat1481)
            return None
        else:
            fields1478 = msg
            self.write("(properties")
            self.indent_sexp()
            if not len(fields1478) == 0:
                self.newline()
                for i1480, elem1479 in enumerate(fields1478):
                    if (i1480 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1479)
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1486 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1486 is not None:
            assert flat1486 is not None
            self.write(flat1486)
            return None
        else:
            _dollar_dollar = msg
            fields1482 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1482 is not None
            unwrapped_fields1483 = fields1482
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1484 = unwrapped_fields1483[0]
            self.write(self.format_string_value(field1484))
            self.newline()
            field1485 = unwrapped_fields1483[1]
            self.write(self.format_string_value(field1485))
            self.dedent()
            self.write(")")

    def pretty_iceberg_auth_properties(self, msg: Sequence[tuple[str, str]]):
        flat1490 = self._try_flat(msg, self.pretty_iceberg_auth_properties)
        if flat1490 is not None:
            assert flat1490 is not None
            self.write(flat1490)
            return None
        else:
            fields1487 = msg
            self.write("(auth_properties")
            self.indent_sexp()
            if not len(fields1487) == 0:
                self.newline()
                for i1489, elem1488 in enumerate(fields1487):
                    if (i1489 > 0):
                        self.newline()
                    self.pretty_iceberg_masked_property_entry(elem1488)
            self.dedent()
            self.write(")")

    def pretty_iceberg_masked_property_entry(self, msg: tuple[str, str]):
        flat1495 = self._try_flat(msg, self.pretty_iceberg_masked_property_entry)
        if flat1495 is not None:
            assert flat1495 is not None
            self.write(flat1495)
            return None
        else:
            _dollar_dollar = msg
            _t1737 = self.mask_secret_value(_dollar_dollar)
            fields1491 = (_dollar_dollar[0], _t1737,)
            assert fields1491 is not None
            unwrapped_fields1492 = fields1491
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1493 = unwrapped_fields1492[0]
            self.write(self.format_string_value(field1493))
            self.newline()
            field1494 = unwrapped_fields1492[1]
            self.write(self.format_string_value(field1494))
            self.dedent()
            self.write(")")

    def pretty_iceberg_from_snapshot(self, msg: str):
        flat1497 = self._try_flat(msg, self.pretty_iceberg_from_snapshot)
        if flat1497 is not None:
            assert flat1497 is not None
            self.write(flat1497)
            return None
        else:
            fields1496 = msg
            self.write("(from_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1496))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1499 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1499 is not None:
            assert flat1499 is not None
            self.write(flat1499)
            return None
        else:
            fields1498 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1498))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1502 = self._try_flat(msg, self.pretty_undefine)
        if flat1502 is not None:
            assert flat1502 is not None
            self.write(flat1502)
            return None
        else:
            _dollar_dollar = msg
            fields1500 = _dollar_dollar.fragment_id
            assert fields1500 is not None
            unwrapped_fields1501 = fields1500
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1501)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1507 = self._try_flat(msg, self.pretty_context)
        if flat1507 is not None:
            assert flat1507 is not None
            self.write(flat1507)
            return None
        else:
            _dollar_dollar = msg
            fields1503 = _dollar_dollar.relations
            assert fields1503 is not None
            unwrapped_fields1504 = fields1503
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1504) == 0:
                self.newline()
                for i1506, elem1505 in enumerate(unwrapped_fields1504):
                    if (i1506 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1505)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1514 = self._try_flat(msg, self.pretty_snapshot)
        if flat1514 is not None:
            assert flat1514 is not None
            self.write(flat1514)
            return None
        else:
            _dollar_dollar = msg
            fields1508 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
            assert fields1508 is not None
            unwrapped_fields1509 = fields1508
            self.write("(snapshot")
            self.indent_sexp()
            self.newline()
            field1510 = unwrapped_fields1509[0]
            self.pretty_edb_path(field1510)
            field1511 = unwrapped_fields1509[1]
            if not len(field1511) == 0:
                self.newline()
                for i1513, elem1512 in enumerate(field1511):
                    if (i1513 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1512)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1519 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1519 is not None:
            assert flat1519 is not None
            self.write(flat1519)
            return None
        else:
            _dollar_dollar = msg
            fields1515 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1515 is not None
            unwrapped_fields1516 = fields1515
            field1517 = unwrapped_fields1516[0]
            self.pretty_edb_path(field1517)
            self.write(" ")
            field1518 = unwrapped_fields1516[1]
            self.pretty_relation_id(field1518)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1523 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1523 is not None:
            assert flat1523 is not None
            self.write(flat1523)
            return None
        else:
            fields1520 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1520) == 0:
                self.newline()
                for i1522, elem1521 in enumerate(fields1520):
                    if (i1522 > 0):
                        self.newline()
                    self.pretty_read(elem1521)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1534 = self._try_flat(msg, self.pretty_read)
        if flat1534 is not None:
            assert flat1534 is not None
            self.write(flat1534)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1738 = _dollar_dollar.demand
            else:
                _t1738 = None
            deconstruct_result1532 = _t1738
            if deconstruct_result1532 is not None:
                assert deconstruct_result1532 is not None
                unwrapped1533 = deconstruct_result1532
                self.pretty_demand(unwrapped1533)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1739 = _dollar_dollar.output
                else:
                    _t1739 = None
                deconstruct_result1530 = _t1739
                if deconstruct_result1530 is not None:
                    assert deconstruct_result1530 is not None
                    unwrapped1531 = deconstruct_result1530
                    self.pretty_output(unwrapped1531)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1740 = _dollar_dollar.what_if
                    else:
                        _t1740 = None
                    deconstruct_result1528 = _t1740
                    if deconstruct_result1528 is not None:
                        assert deconstruct_result1528 is not None
                        unwrapped1529 = deconstruct_result1528
                        self.pretty_what_if(unwrapped1529)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1741 = _dollar_dollar.abort
                        else:
                            _t1741 = None
                        deconstruct_result1526 = _t1741
                        if deconstruct_result1526 is not None:
                            assert deconstruct_result1526 is not None
                            unwrapped1527 = deconstruct_result1526
                            self.pretty_abort(unwrapped1527)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1742 = _dollar_dollar.export
                            else:
                                _t1742 = None
                            deconstruct_result1524 = _t1742
                            if deconstruct_result1524 is not None:
                                assert deconstruct_result1524 is not None
                                unwrapped1525 = deconstruct_result1524
                                self.pretty_export(unwrapped1525)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1537 = self._try_flat(msg, self.pretty_demand)
        if flat1537 is not None:
            assert flat1537 is not None
            self.write(flat1537)
            return None
        else:
            _dollar_dollar = msg
            fields1535 = _dollar_dollar.relation_id
            assert fields1535 is not None
            unwrapped_fields1536 = fields1535
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1536)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1542 = self._try_flat(msg, self.pretty_output)
        if flat1542 is not None:
            assert flat1542 is not None
            self.write(flat1542)
            return None
        else:
            _dollar_dollar = msg
            fields1538 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1538 is not None
            unwrapped_fields1539 = fields1538
            self.write("(output")
=======
    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1409 = self._try_flat(msg, self.pretty_edb_types)
        if flat1409 is not None:
            assert flat1409 is not None
            self.write(flat1409)
            return None
        else:
            fields1406 = msg
            self.write("[")
            self.indent()
            for i1408, elem1407 in enumerate(fields1406):
                if (i1408 > 0):
                    self.newline()
                self.pretty_type(elem1407)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1414 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1414 is not None:
            assert flat1414 is not None
            self.write(flat1414)
            return None
        else:
            _dollar_dollar = msg
            fields1410 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1410 is not None
            unwrapped_fields1411 = fields1410
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1412 = unwrapped_fields1411[0]
            self.pretty_relation_id(field1412)
            self.newline()
            field1413 = unwrapped_fields1411[1]
            self.pretty_betree_info(field1413)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1420 = self._try_flat(msg, self.pretty_betree_info)
        if flat1420 is not None:
            assert flat1420 is not None
            self.write(flat1420)
            return None
        else:
            _dollar_dollar = msg
            _t1802 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1415 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1802,)
            assert fields1415 is not None
            unwrapped_fields1416 = fields1415
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1417 = unwrapped_fields1416[0]
            self.pretty_betree_info_key_types(field1417)
            self.newline()
            field1418 = unwrapped_fields1416[1]
            self.pretty_betree_info_value_types(field1418)
            self.newline()
            field1419 = unwrapped_fields1416[2]
            self.pretty_config_dict(field1419)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1424 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1424 is not None:
            assert flat1424 is not None
            self.write(flat1424)
            return None
        else:
            fields1421 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1421) == 0:
                self.newline()
                for i1423, elem1422 in enumerate(fields1421):
                    if (i1423 > 0):
                        self.newline()
                    self.pretty_type(elem1422)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1428 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1428 is not None:
            assert flat1428 is not None
            self.write(flat1428)
            return None
        else:
            fields1425 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1425) == 0:
                self.newline()
                for i1427, elem1426 in enumerate(fields1425):
                    if (i1427 > 0):
                        self.newline()
                    self.pretty_type(elem1426)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1438 = self._try_flat(msg, self.pretty_csv_data)
        if flat1438 is not None:
            assert flat1438 is not None
            self.write(flat1438)
            return None
        else:
            _dollar_dollar = msg
            _t1803 = self.deconstruct_csv_data_columns_optional(_dollar_dollar)
            _t1804 = self.deconstruct_csv_data_relations_optional(_dollar_dollar)
            fields1429 = (_dollar_dollar.locator, _dollar_dollar.config, _t1803, _t1804, _dollar_dollar.asof,)
            assert fields1429 is not None
            unwrapped_fields1430 = fields1429
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1431 = unwrapped_fields1430[0]
            self.pretty_csvlocator(field1431)
            self.newline()
            field1432 = unwrapped_fields1430[1]
            self.pretty_csv_config(field1432)
            field1433 = unwrapped_fields1430[2]
            if field1433 is not None:
                self.newline()
                assert field1433 is not None
                opt_val1434 = field1433
                self.pretty_gnf_columns(opt_val1434)
            field1435 = unwrapped_fields1430[3]
            if field1435 is not None:
                self.newline()
                assert field1435 is not None
                opt_val1436 = field1435
                self.pretty_target_relations(opt_val1436)
            self.newline()
            field1437 = unwrapped_fields1430[4]
            self.pretty_csv_asof(field1437)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1445 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1445 is not None:
            assert flat1445 is not None
            self.write(flat1445)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1805 = _dollar_dollar.paths
            else:
                _t1805 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1806 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1806 = None
            fields1439 = (_t1805, _t1806,)
            assert fields1439 is not None
            unwrapped_fields1440 = fields1439
            self.write("(csv_locator")
            self.indent_sexp()
            field1441 = unwrapped_fields1440[0]
            if field1441 is not None:
                self.newline()
                assert field1441 is not None
                opt_val1442 = field1441
                self.pretty_csv_locator_paths(opt_val1442)
            field1443 = unwrapped_fields1440[1]
            if field1443 is not None:
                self.newline()
                assert field1443 is not None
                opt_val1444 = field1443
                self.pretty_csv_locator_inline_data(opt_val1444)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1449 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1449 is not None:
            assert flat1449 is not None
            self.write(flat1449)
            return None
        else:
            fields1446 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1446) == 0:
                self.newline()
                for i1448, elem1447 in enumerate(fields1446):
                    if (i1448 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1447))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1451 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1451 is not None:
            assert flat1451 is not None
            self.write(flat1451)
            return None
        else:
            fields1450 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1450))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1457 = self._try_flat(msg, self.pretty_csv_config)
        if flat1457 is not None:
            assert flat1457 is not None
            self.write(flat1457)
            return None
        else:
            _dollar_dollar = msg
            _t1807 = self.deconstruct_csv_config(_dollar_dollar)
            _t1808 = self.deconstruct_csv_storage_integration_optional(_dollar_dollar)
            fields1452 = (_t1807, _t1808,)
            assert fields1452 is not None
            unwrapped_fields1453 = fields1452
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            field1454 = unwrapped_fields1453[0]
            self.pretty_config_dict(field1454)
            field1455 = unwrapped_fields1453[1]
            if field1455 is not None:
                self.newline()
                assert field1455 is not None
                opt_val1456 = field1455
                self.pretty__storage_integration(opt_val1456)
            self.dedent()
            self.write(")")

    def pretty__storage_integration(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat1459 = self._try_flat(msg, self.pretty__storage_integration)
        if flat1459 is not None:
            assert flat1459 is not None
            self.write(flat1459)
            return None
        else:
            fields1458 = msg
            self.write("(storage_integration")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(fields1458)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1463 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1463 is not None:
            assert flat1463 is not None
            self.write(flat1463)
            return None
        else:
            fields1460 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1460) == 0:
                self.newline()
                for i1462, elem1461 in enumerate(fields1460):
                    if (i1462 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1461)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1472 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1472 is not None:
            assert flat1472 is not None
            self.write(flat1472)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1809 = _dollar_dollar.target_id
            else:
                _t1809 = None
            fields1464 = (_dollar_dollar.column_path, _t1809, _dollar_dollar.types,)
            assert fields1464 is not None
            unwrapped_fields1465 = fields1464
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1466 = unwrapped_fields1465[0]
            self.pretty_gnf_column_path(field1466)
            field1467 = unwrapped_fields1465[1]
            if field1467 is not None:
                self.newline()
                assert field1467 is not None
                opt_val1468 = field1467
                self.pretty_relation_id(opt_val1468)
            self.newline()
            self.write("[")
            field1469 = unwrapped_fields1465[2]
            for i1471, elem1470 in enumerate(field1469):
                if (i1471 > 0):
                    self.newline()
                self.pretty_type(elem1470)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1479 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1479 is not None:
            assert flat1479 is not None
            self.write(flat1479)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1810 = _dollar_dollar[0]
            else:
                _t1810 = None
            deconstruct_result1477 = _t1810
            if deconstruct_result1477 is not None:
                assert deconstruct_result1477 is not None
                unwrapped1478 = deconstruct_result1477
                self.write(self.format_string_value(unwrapped1478))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1811 = _dollar_dollar
                else:
                    _t1811 = None
                deconstruct_result1473 = _t1811
                if deconstruct_result1473 is not None:
                    assert deconstruct_result1473 is not None
                    unwrapped1474 = deconstruct_result1473
                    self.write("[")
                    self.indent()
                    for i1476, elem1475 in enumerate(unwrapped1474):
                        if (i1476 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1475))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_target_relations(self, msg: logic_pb2.TargetRelations):
        flat1484 = self._try_flat(msg, self.pretty_target_relations)
        if flat1484 is not None:
            assert flat1484 is not None
            self.write(flat1484)
            return None
        else:
            _dollar_dollar = msg
            fields1480 = (_dollar_dollar.keys, _dollar_dollar,)
            assert fields1480 is not None
            unwrapped_fields1481 = fields1480
            self.write("(relations")
            self.indent_sexp()
            self.newline()
            field1482 = unwrapped_fields1481[0]
            self.pretty_relation_keys(field1482)
            self.newline()
            field1483 = unwrapped_fields1481[1]
            self.pretty_relation_body(field1483)
            self.dedent()
            self.write(")")

    def pretty_relation_keys(self, msg: Sequence[logic_pb2.NamedColumn]):
        flat1488 = self._try_flat(msg, self.pretty_relation_keys)
        if flat1488 is not None:
            assert flat1488 is not None
            self.write(flat1488)
            return None
        else:
            fields1485 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1485) == 0:
                self.newline()
                for i1487, elem1486 in enumerate(fields1485):
                    if (i1487 > 0):
                        self.newline()
                    self.pretty_named_column(elem1486)
            self.dedent()
            self.write(")")

    def pretty_named_column(self, msg: logic_pb2.NamedColumn):
        flat1493 = self._try_flat(msg, self.pretty_named_column)
        if flat1493 is not None:
            assert flat1493 is not None
            self.write(flat1493)
            return None
        else:
            _dollar_dollar = msg
            fields1489 = (_dollar_dollar.name, _dollar_dollar.type,)
            assert fields1489 is not None
            unwrapped_fields1490 = fields1489
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1491 = unwrapped_fields1490[0]
            self.write(self.format_string_value(field1491))
            self.newline()
            field1492 = unwrapped_fields1490[1]
            self.pretty_type(field1492)
            self.dedent()
            self.write(")")

    def pretty_relation_body(self, msg: logic_pb2.TargetRelations):
        flat1500 = self._try_flat(msg, self.pretty_relation_body)
        if flat1500 is not None:
            assert flat1500 is not None
            self.write(flat1500)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("plain"):
                _t1812 = _dollar_dollar.plain.targets
            else:
                _t1812 = None
            deconstruct_result1498 = _t1812
            if deconstruct_result1498 is not None:
                assert deconstruct_result1498 is not None
                unwrapped1499 = deconstruct_result1498
                self.pretty_non_cdc_relations(unwrapped1499)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("cdc"):
                    _t1813 = (_dollar_dollar.cdc.inserts, _dollar_dollar.cdc.deletes,)
                else:
                    _t1813 = None
                deconstruct_result1494 = _t1813
                if deconstruct_result1494 is not None:
                    assert deconstruct_result1494 is not None
                    unwrapped1495 = deconstruct_result1494
                    field1496 = unwrapped1495[0]
                    self.pretty_cdc_inserts(field1496)
                    self.write(" ")
                    field1497 = unwrapped1495[1]
                    self.pretty_cdc_deletes(field1497)
                else:
                    raise ParseError("No matching rule for relation_body")

    def pretty_non_cdc_relations(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1504 = self._try_flat(msg, self.pretty_non_cdc_relations)
        if flat1504 is not None:
            assert flat1504 is not None
            self.write(flat1504)
            return None
        else:
            fields1501 = msg
            for i1503, elem1502 in enumerate(fields1501):
                if (i1503 > 0):
                    self.newline()
                self.pretty_target_relation(elem1502)

    def pretty_target_relation(self, msg: logic_pb2.TargetRelation):
        flat1511 = self._try_flat(msg, self.pretty_target_relation)
        if flat1511 is not None:
            assert flat1511 is not None
            self.write(flat1511)
            return None
        else:
            _dollar_dollar = msg
            fields1505 = (_dollar_dollar.target_id, _dollar_dollar.values,)
            assert fields1505 is not None
            unwrapped_fields1506 = fields1505
            self.write("(relation")
            self.indent_sexp()
            self.newline()
            field1507 = unwrapped_fields1506[0]
            self.pretty_relation_id(field1507)
            field1508 = unwrapped_fields1506[1]
            if not len(field1508) == 0:
                self.newline()
                for i1510, elem1509 in enumerate(field1508):
                    if (i1510 > 0):
                        self.newline()
                    self.pretty_named_column(elem1509)
            self.dedent()
            self.write(")")

    def pretty_cdc_inserts(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1515 = self._try_flat(msg, self.pretty_cdc_inserts)
        if flat1515 is not None:
            assert flat1515 is not None
            self.write(flat1515)
            return None
        else:
            fields1512 = msg
            self.write("(inserts")
            self.indent_sexp()
            if not len(fields1512) == 0:
                self.newline()
                for i1514, elem1513 in enumerate(fields1512):
                    if (i1514 > 0):
                        self.newline()
                    self.pretty_target_relation(elem1513)
            self.dedent()
            self.write(")")

    def pretty_cdc_deletes(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1519 = self._try_flat(msg, self.pretty_cdc_deletes)
        if flat1519 is not None:
            assert flat1519 is not None
            self.write(flat1519)
            return None
        else:
            fields1516 = msg
            self.write("(deletes")
            self.indent_sexp()
            if not len(fields1516) == 0:
                self.newline()
                for i1518, elem1517 in enumerate(fields1516):
                    if (i1518 > 0):
                        self.newline()
                    self.pretty_target_relation(elem1517)
            self.dedent()
            self.write(")")

    def pretty_csv_asof(self, msg: str):
        flat1521 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1521 is not None:
            assert flat1521 is not None
            self.write(flat1521)
            return None
        else:
            fields1520 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1520))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1532 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1532 is not None:
            assert flat1532 is not None
            self.write(flat1532)
            return None
        else:
            _dollar_dollar = msg
            _t1814 = self.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
            _t1815 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1522 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1814, _t1815, _dollar_dollar.returns_delta,)
            assert fields1522 is not None
            unwrapped_fields1523 = fields1522
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1524 = unwrapped_fields1523[0]
            self.pretty_iceberg_locator(field1524)
            self.newline()
            field1525 = unwrapped_fields1523[1]
            self.pretty_iceberg_catalog_config(field1525)
            self.newline()
            field1526 = unwrapped_fields1523[2]
            self.pretty_gnf_columns(field1526)
            field1527 = unwrapped_fields1523[3]
            if field1527 is not None:
                self.newline()
                assert field1527 is not None
                opt_val1528 = field1527
                self.pretty_iceberg_from_snapshot(opt_val1528)
            field1529 = unwrapped_fields1523[4]
            if field1529 is not None:
                self.newline()
                assert field1529 is not None
                opt_val1530 = field1529
                self.pretty_iceberg_to_snapshot(opt_val1530)
            self.newline()
            field1531 = unwrapped_fields1523[5]
            self.pretty_boolean_value(field1531)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1538 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1538 is not None:
            assert flat1538 is not None
            self.write(flat1538)
            return None
        else:
            _dollar_dollar = msg
            fields1533 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1533 is not None
            unwrapped_fields1534 = fields1533
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            field1535 = unwrapped_fields1534[0]
            self.pretty_iceberg_locator_table_name(field1535)
            self.newline()
            field1536 = unwrapped_fields1534[1]
            self.pretty_iceberg_locator_namespace(field1536)
            self.newline()
            field1537 = unwrapped_fields1534[2]
            self.pretty_iceberg_locator_warehouse(field1537)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_table_name(self, msg: str):
        flat1540 = self._try_flat(msg, self.pretty_iceberg_locator_table_name)
        if flat1540 is not None:
            assert flat1540 is not None
            self.write(flat1540)
            return None
        else:
            fields1539 = msg
            self.write("(table_name")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1539))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_namespace(self, msg: Sequence[str]):
        flat1544 = self._try_flat(msg, self.pretty_iceberg_locator_namespace)
        if flat1544 is not None:
            assert flat1544 is not None
            self.write(flat1544)
            return None
        else:
            fields1541 = msg
            self.write("(namespace")
            self.indent_sexp()
            if not len(fields1541) == 0:
                self.newline()
                for i1543, elem1542 in enumerate(fields1541):
                    if (i1543 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1542))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_warehouse(self, msg: str):
        flat1546 = self._try_flat(msg, self.pretty_iceberg_locator_warehouse)
        if flat1546 is not None:
            assert flat1546 is not None
            self.write(flat1546)
            return None
        else:
            fields1545 = msg
            self.write("(warehouse")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1545))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1554 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1554 is not None:
            assert flat1554 is not None
            self.write(flat1554)
            return None
        else:
            _dollar_dollar = msg
            _t1816 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1547 = (_dollar_dollar.catalog_uri, _t1816, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1547 is not None
            unwrapped_fields1548 = fields1547
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            field1549 = unwrapped_fields1548[0]
            self.pretty_iceberg_catalog_uri(field1549)
            field1550 = unwrapped_fields1548[1]
            if field1550 is not None:
                self.newline()
                assert field1550 is not None
                opt_val1551 = field1550
                self.pretty_iceberg_catalog_config_scope(opt_val1551)
            self.newline()
            field1552 = unwrapped_fields1548[2]
            self.pretty_iceberg_properties(field1552)
            self.newline()
            field1553 = unwrapped_fields1548[3]
            self.pretty_iceberg_auth_properties(field1553)
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_uri(self, msg: str):
        flat1556 = self._try_flat(msg, self.pretty_iceberg_catalog_uri)
        if flat1556 is not None:
            assert flat1556 is not None
            self.write(flat1556)
            return None
        else:
            fields1555 = msg
            self.write("(catalog_uri")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1555))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1558 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1558 is not None:
            assert flat1558 is not None
            self.write(flat1558)
            return None
        else:
            fields1557 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1557))
            self.dedent()
            self.write(")")

    def pretty_iceberg_properties(self, msg: Sequence[tuple[str, str]]):
        flat1562 = self._try_flat(msg, self.pretty_iceberg_properties)
        if flat1562 is not None:
            assert flat1562 is not None
            self.write(flat1562)
            return None
        else:
            fields1559 = msg
            self.write("(properties")
            self.indent_sexp()
            if not len(fields1559) == 0:
                self.newline()
                for i1561, elem1560 in enumerate(fields1559):
                    if (i1561 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1560)
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1567 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1567 is not None:
            assert flat1567 is not None
            self.write(flat1567)
            return None
        else:
            _dollar_dollar = msg
            fields1563 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1563 is not None
            unwrapped_fields1564 = fields1563
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1565 = unwrapped_fields1564[0]
            self.write(self.format_string_value(field1565))
            self.newline()
            field1566 = unwrapped_fields1564[1]
            self.write(self.format_string_value(field1566))
            self.dedent()
            self.write(")")

    def pretty_iceberg_auth_properties(self, msg: Sequence[tuple[str, str]]):
        flat1571 = self._try_flat(msg, self.pretty_iceberg_auth_properties)
        if flat1571 is not None:
            assert flat1571 is not None
            self.write(flat1571)
            return None
        else:
            fields1568 = msg
            self.write("(auth_properties")
            self.indent_sexp()
            if not len(fields1568) == 0:
                self.newline()
                for i1570, elem1569 in enumerate(fields1568):
                    if (i1570 > 0):
                        self.newline()
                    self.pretty_iceberg_masked_property_entry(elem1569)
            self.dedent()
            self.write(")")

    def pretty_iceberg_masked_property_entry(self, msg: tuple[str, str]):
        flat1576 = self._try_flat(msg, self.pretty_iceberg_masked_property_entry)
        if flat1576 is not None:
            assert flat1576 is not None
            self.write(flat1576)
            return None
        else:
            _dollar_dollar = msg
            _t1817 = self.mask_secret_value(_dollar_dollar)
            fields1572 = (_dollar_dollar[0], _t1817,)
            assert fields1572 is not None
            unwrapped_fields1573 = fields1572
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1574 = unwrapped_fields1573[0]
            self.write(self.format_string_value(field1574))
            self.newline()
            field1575 = unwrapped_fields1573[1]
            self.write(self.format_string_value(field1575))
            self.dedent()
            self.write(")")

    def pretty_iceberg_from_snapshot(self, msg: str):
        flat1578 = self._try_flat(msg, self.pretty_iceberg_from_snapshot)
        if flat1578 is not None:
            assert flat1578 is not None
            self.write(flat1578)
            return None
        else:
            fields1577 = msg
            self.write("(from_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1577))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1580 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1580 is not None:
            assert flat1580 is not None
            self.write(flat1580)
            return None
        else:
            fields1579 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1579))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1583 = self._try_flat(msg, self.pretty_undefine)
        if flat1583 is not None:
            assert flat1583 is not None
            self.write(flat1583)
            return None
        else:
            _dollar_dollar = msg
            fields1581 = _dollar_dollar.fragment_id
            assert fields1581 is not None
            unwrapped_fields1582 = fields1581
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1582)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1588 = self._try_flat(msg, self.pretty_context)
        if flat1588 is not None:
            assert flat1588 is not None
            self.write(flat1588)
            return None
        else:
            _dollar_dollar = msg
            fields1584 = _dollar_dollar.relations
            assert fields1584 is not None
            unwrapped_fields1585 = fields1584
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1585) == 0:
                self.newline()
                for i1587, elem1586 in enumerate(unwrapped_fields1585):
                    if (i1587 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1586)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1595 = self._try_flat(msg, self.pretty_snapshot)
        if flat1595 is not None:
            assert flat1595 is not None
            self.write(flat1595)
            return None
        else:
            _dollar_dollar = msg
            fields1589 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
            assert fields1589 is not None
            unwrapped_fields1590 = fields1589
            self.write("(snapshot")
            self.indent_sexp()
            self.newline()
            field1591 = unwrapped_fields1590[0]
            self.pretty_edb_path(field1591)
            field1592 = unwrapped_fields1590[1]
            if not len(field1592) == 0:
                self.newline()
                for i1594, elem1593 in enumerate(field1592):
                    if (i1594 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1593)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1600 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1600 is not None:
            assert flat1600 is not None
            self.write(flat1600)
            return None
        else:
            _dollar_dollar = msg
            fields1596 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1596 is not None
            unwrapped_fields1597 = fields1596
            field1598 = unwrapped_fields1597[0]
            self.pretty_edb_path(field1598)
            self.write(" ")
            field1599 = unwrapped_fields1597[1]
            self.pretty_relation_id(field1599)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1604 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1604 is not None:
            assert flat1604 is not None
            self.write(flat1604)
            return None
        else:
            fields1601 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1601) == 0:
                self.newline()
                for i1603, elem1602 in enumerate(fields1601):
                    if (i1603 > 0):
                        self.newline()
                    self.pretty_read(elem1602)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1615 = self._try_flat(msg, self.pretty_read)
        if flat1615 is not None:
            assert flat1615 is not None
            self.write(flat1615)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1818 = _dollar_dollar.demand
            else:
                _t1818 = None
            deconstruct_result1613 = _t1818
            if deconstruct_result1613 is not None:
                assert deconstruct_result1613 is not None
                unwrapped1614 = deconstruct_result1613
                self.pretty_demand(unwrapped1614)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1819 = _dollar_dollar.output
                else:
                    _t1819 = None
                deconstruct_result1611 = _t1819
                if deconstruct_result1611 is not None:
                    assert deconstruct_result1611 is not None
                    unwrapped1612 = deconstruct_result1611
                    self.pretty_output(unwrapped1612)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1820 = _dollar_dollar.what_if
                    else:
                        _t1820 = None
                    deconstruct_result1609 = _t1820
                    if deconstruct_result1609 is not None:
                        assert deconstruct_result1609 is not None
                        unwrapped1610 = deconstruct_result1609
                        self.pretty_what_if(unwrapped1610)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1821 = _dollar_dollar.abort
                        else:
                            _t1821 = None
                        deconstruct_result1607 = _t1821
                        if deconstruct_result1607 is not None:
                            assert deconstruct_result1607 is not None
                            unwrapped1608 = deconstruct_result1607
                            self.pretty_abort(unwrapped1608)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1822 = _dollar_dollar.export
                            else:
                                _t1822 = None
                            deconstruct_result1605 = _t1822
                            if deconstruct_result1605 is not None:
                                assert deconstruct_result1605 is not None
                                unwrapped1606 = deconstruct_result1605
                                self.pretty_export(unwrapped1606)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1618 = self._try_flat(msg, self.pretty_demand)
        if flat1618 is not None:
            assert flat1618 is not None
            self.write(flat1618)
            return None
        else:
            _dollar_dollar = msg
            fields1616 = _dollar_dollar.relation_id
            assert fields1616 is not None
            unwrapped_fields1617 = fields1616
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1617)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1623 = self._try_flat(msg, self.pretty_output)
        if flat1623 is not None:
            assert flat1623 is not None
            self.write(flat1623)
            return None
        else:
            _dollar_dollar = msg
            fields1619 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1619 is not None
            unwrapped_fields1620 = fields1619
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1621 = unwrapped_fields1620[0]
            self.pretty_name(field1621)
            self.newline()
            field1622 = unwrapped_fields1620[1]
            self.pretty_relation_id(field1622)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1628 = self._try_flat(msg, self.pretty_what_if)
        if flat1628 is not None:
            assert flat1628 is not None
            self.write(flat1628)
            return None
        else:
            _dollar_dollar = msg
            fields1624 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1624 is not None
            unwrapped_fields1625 = fields1624
            self.write("(what_if")
>>>>>>> origin/main
            self.indent_sexp()
            self.newline()
            field1626 = unwrapped_fields1625[0]
            self.pretty_name(field1626)
            self.newline()
<<<<<<< HEAD
            field1541 = unwrapped_fields1539[1]
            self.pretty_relation_id(field1541)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1547 = self._try_flat(msg, self.pretty_what_if)
        if flat1547 is not None:
            assert flat1547 is not None
            self.write(flat1547)
            return None
        else:
            _dollar_dollar = msg
            fields1543 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1543 is not None
            unwrapped_fields1544 = fields1543
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1545 = unwrapped_fields1544[0]
            self.pretty_name(field1545)
            self.newline()
            field1546 = unwrapped_fields1544[1]
            self.pretty_epoch(field1546)
=======
            field1627 = unwrapped_fields1625[1]
            self.pretty_epoch(field1627)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
<<<<<<< HEAD
        flat1553 = self._try_flat(msg, self.pretty_abort)
        if flat1553 is not None:
            assert flat1553 is not None
            self.write(flat1553)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1743 = _dollar_dollar.name
            else:
                _t1743 = None
            fields1548 = (_t1743, _dollar_dollar.relation_id,)
            assert fields1548 is not None
            unwrapped_fields1549 = fields1548
            self.write("(abort")
            self.indent_sexp()
            field1550 = unwrapped_fields1549[0]
            if field1550 is not None:
                self.newline()
                assert field1550 is not None
                opt_val1551 = field1550
                self.pretty_name(opt_val1551)
            self.newline()
            field1552 = unwrapped_fields1549[1]
            self.pretty_relation_id(field1552)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1558 = self._try_flat(msg, self.pretty_export)
        if flat1558 is not None:
            assert flat1558 is not None
            self.write(flat1558)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1744 = _dollar_dollar.csv_config
            else:
                _t1744 = None
            deconstruct_result1556 = _t1744
            if deconstruct_result1556 is not None:
                assert deconstruct_result1556 is not None
                unwrapped1557 = deconstruct_result1556
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1557)
=======
        flat1634 = self._try_flat(msg, self.pretty_abort)
        if flat1634 is not None:
            assert flat1634 is not None
            self.write(flat1634)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1823 = _dollar_dollar.name
            else:
                _t1823 = None
            fields1629 = (_t1823, _dollar_dollar.relation_id,)
            assert fields1629 is not None
            unwrapped_fields1630 = fields1629
            self.write("(abort")
            self.indent_sexp()
            field1631 = unwrapped_fields1630[0]
            if field1631 is not None:
                self.newline()
                assert field1631 is not None
                opt_val1632 = field1631
                self.pretty_name(opt_val1632)
            self.newline()
            field1633 = unwrapped_fields1630[1]
            self.pretty_relation_id(field1633)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1639 = self._try_flat(msg, self.pretty_export)
        if flat1639 is not None:
            assert flat1639 is not None
            self.write(flat1639)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1824 = _dollar_dollar.csv_config
            else:
                _t1824 = None
            deconstruct_result1637 = _t1824
            if deconstruct_result1637 is not None:
                assert deconstruct_result1637 is not None
                unwrapped1638 = deconstruct_result1637
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1638)
>>>>>>> origin/main
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
<<<<<<< HEAD
                    _t1745 = _dollar_dollar.iceberg_config
                else:
                    _t1745 = None
                deconstruct_result1554 = _t1745
                if deconstruct_result1554 is not None:
                    assert deconstruct_result1554 is not None
                    unwrapped1555 = deconstruct_result1554
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1555)
=======
                    _t1825 = _dollar_dollar.iceberg_config
                else:
                    _t1825 = None
                deconstruct_result1635 = _t1825
                if deconstruct_result1635 is not None:
                    assert deconstruct_result1635 is not None
                    unwrapped1636 = deconstruct_result1635
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1636)
>>>>>>> origin/main
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
<<<<<<< HEAD
        flat1569 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1569 is not None:
            assert flat1569 is not None
            self.write(flat1569)
=======
        flat1650 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1650 is not None:
            assert flat1650 is not None
            self.write(flat1650)
>>>>>>> origin/main
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
<<<<<<< HEAD
                _t1747 = self.deconstruct_export_csv_output_location(_dollar_dollar)
                _t1746 = (_t1747, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1746 = None
            deconstruct_result1564 = _t1746
            if deconstruct_result1564 is not None:
                assert deconstruct_result1564 is not None
                unwrapped1565 = deconstruct_result1564
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1566 = unwrapped1565[0]
                self.pretty_export_csv_output_location(field1566)
                self.newline()
                field1567 = unwrapped1565[1]
                self.pretty_export_csv_source(field1567)
                self.newline()
                field1568 = unwrapped1565[2]
                self.pretty_csv_config(field1568)
=======
                _t1826 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1826 = None
            deconstruct_result1645 = _t1826
            if deconstruct_result1645 is not None:
                assert deconstruct_result1645 is not None
                unwrapped1646 = deconstruct_result1645
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1647 = unwrapped1646[0]
                self.pretty_export_csv_path(field1647)
                self.newline()
                field1648 = unwrapped1646[1]
                self.pretty_export_csv_source(field1648)
                self.newline()
                field1649 = unwrapped1646[2]
                self.pretty_csv_config(field1649)
>>>>>>> origin/main
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
<<<<<<< HEAD
                    _t1749 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1748 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1749,)
                else:
                    _t1748 = None
                deconstruct_result1559 = _t1748
                if deconstruct_result1559 is not None:
                    assert deconstruct_result1559 is not None
                    unwrapped1560 = deconstruct_result1559
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1561 = unwrapped1560[0]
                    self.pretty_export_csv_path(field1561)
                    self.newline()
                    field1562 = unwrapped1560[1]
                    self.pretty_export_csv_columns_list(field1562)
                    self.newline()
                    field1563 = unwrapped1560[2]
                    self.pretty_config_dict(field1563)
=======
                    _t1828 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1827 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1828,)
                else:
                    _t1827 = None
                deconstruct_result1640 = _t1827
                if deconstruct_result1640 is not None:
                    assert deconstruct_result1640 is not None
                    unwrapped1641 = deconstruct_result1640
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1642 = unwrapped1641[0]
                    self.pretty_export_csv_path(field1642)
                    self.newline()
                    field1643 = unwrapped1641[1]
                    self.pretty_export_csv_columns_list(field1643)
                    self.newline()
                    field1644 = unwrapped1641[2]
                    self.pretty_config_dict(field1644)
>>>>>>> origin/main
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

<<<<<<< HEAD
    def pretty_export_csv_output_location(self, msg: tuple[str, str]):
        flat1574 = self._try_flat(msg, self.pretty_export_csv_output_location)
        if flat1574 is not None:
            assert flat1574 is not None
            self.write(flat1574)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar[0] != "":
                _t1750 = _dollar_dollar[0]
            else:
                _t1750 = None
            deconstruct_result1572 = _t1750
            if deconstruct_result1572 is not None:
                assert deconstruct_result1572 is not None
                unwrapped1573 = deconstruct_result1572
                self.write("(path")
                self.indent_sexp()
                self.newline()
                self.write(self.format_string_value(unwrapped1573))
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar[1] != "":
                    _t1751 = _dollar_dollar[1]
                else:
                    _t1751 = None
                deconstruct_result1570 = _t1751
                if deconstruct_result1570 is not None:
                    assert deconstruct_result1570 is not None
                    unwrapped1571 = deconstruct_result1570
                    self.write("(transaction_output_name")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_name(unwrapped1571)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_output_location")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1581 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1581 is not None:
            assert flat1581 is not None
            self.write(flat1581)
=======
    def pretty_export_csv_path(self, msg: str):
        flat1652 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1652 is not None:
            assert flat1652 is not None
            self.write(flat1652)
            return None
        else:
            fields1651 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1651))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1659 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1659 is not None:
            assert flat1659 is not None
            self.write(flat1659)
>>>>>>> origin/main
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
<<<<<<< HEAD
                _t1752 = _dollar_dollar.gnf_columns.columns
            else:
                _t1752 = None
            deconstruct_result1577 = _t1752
            if deconstruct_result1577 is not None:
                assert deconstruct_result1577 is not None
                unwrapped1578 = deconstruct_result1577
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1578) == 0:
                    self.newline()
                    for i1580, elem1579 in enumerate(unwrapped1578):
                        if (i1580 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1579)
=======
                _t1829 = _dollar_dollar.gnf_columns.columns
            else:
                _t1829 = None
            deconstruct_result1655 = _t1829
            if deconstruct_result1655 is not None:
                assert deconstruct_result1655 is not None
                unwrapped1656 = deconstruct_result1655
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1656) == 0:
                    self.newline()
                    for i1658, elem1657 in enumerate(unwrapped1656):
                        if (i1658 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1657)
>>>>>>> origin/main
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
<<<<<<< HEAD
                    _t1753 = _dollar_dollar.table_def
                else:
                    _t1753 = None
                deconstruct_result1575 = _t1753
                if deconstruct_result1575 is not None:
                    assert deconstruct_result1575 is not None
                    unwrapped1576 = deconstruct_result1575
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1576)
=======
                    _t1830 = _dollar_dollar.table_def
                else:
                    _t1830 = None
                deconstruct_result1653 = _t1830
                if deconstruct_result1653 is not None:
                    assert deconstruct_result1653 is not None
                    unwrapped1654 = deconstruct_result1653
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1654)
>>>>>>> origin/main
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
<<<<<<< HEAD
        flat1586 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1586 is not None:
            assert flat1586 is not None
            self.write(flat1586)
            return None
        else:
            _dollar_dollar = msg
            fields1582 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1582 is not None
            unwrapped_fields1583 = fields1582
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1584 = unwrapped_fields1583[0]
            self.write(self.format_string_value(field1584))
            self.newline()
            field1585 = unwrapped_fields1583[1]
            self.pretty_relation_id(field1585)
            self.dedent()
            self.write(")")

    def pretty_export_csv_path(self, msg: str):
        flat1588 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1588 is not None:
            assert flat1588 is not None
            self.write(flat1588)
            return None
        else:
            fields1587 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1587))
=======
        flat1664 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1664 is not None:
            assert flat1664 is not None
            self.write(flat1664)
            return None
        else:
            _dollar_dollar = msg
            fields1660 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1660 is not None
            unwrapped_fields1661 = fields1660
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1662 = unwrapped_fields1661[0]
            self.write(self.format_string_value(field1662))
            self.newline()
            field1663 = unwrapped_fields1661[1]
            self.pretty_relation_id(field1663)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
<<<<<<< HEAD
        flat1592 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1592 is not None:
            assert flat1592 is not None
            self.write(flat1592)
            return None
        else:
            fields1589 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1589) == 0:
                self.newline()
                for i1591, elem1590 in enumerate(fields1589):
                    if (i1591 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1590)
=======
        flat1668 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1668 is not None:
            assert flat1668 is not None
            self.write(flat1668)
            return None
        else:
            fields1665 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1665) == 0:
                self.newline()
                for i1667, elem1666 in enumerate(fields1665):
                    if (i1667 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1666)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
<<<<<<< HEAD
        flat1601 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1601 is not None:
            assert flat1601 is not None
            self.write(flat1601)
            return None
        else:
            _dollar_dollar = msg
            _t1754 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1593 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sorted(_dollar_dollar.table_properties.items()), _t1754,)
            assert fields1593 is not None
            unwrapped_fields1594 = fields1593
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1595 = unwrapped_fields1594[0]
            self.pretty_iceberg_locator(field1595)
            self.newline()
            field1596 = unwrapped_fields1594[1]
            self.pretty_iceberg_catalog_config(field1596)
            self.newline()
            field1597 = unwrapped_fields1594[2]
            self.pretty_export_iceberg_table_def(field1597)
            self.newline()
            field1598 = unwrapped_fields1594[3]
            self.pretty_iceberg_table_properties(field1598)
            field1599 = unwrapped_fields1594[4]
            if field1599 is not None:
                self.newline()
                assert field1599 is not None
                opt_val1600 = field1599
                self.pretty_config_dict(opt_val1600)
=======
        flat1677 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1677 is not None:
            assert flat1677 is not None
            self.write(flat1677)
            return None
        else:
            _dollar_dollar = msg
            _t1831 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1669 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sorted(_dollar_dollar.table_properties.items()), _t1831,)
            assert fields1669 is not None
            unwrapped_fields1670 = fields1669
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1671 = unwrapped_fields1670[0]
            self.pretty_iceberg_locator(field1671)
            self.newline()
            field1672 = unwrapped_fields1670[1]
            self.pretty_iceberg_catalog_config(field1672)
            self.newline()
            field1673 = unwrapped_fields1670[2]
            self.pretty_export_iceberg_table_def(field1673)
            self.newline()
            field1674 = unwrapped_fields1670[3]
            self.pretty_iceberg_table_properties(field1674)
            field1675 = unwrapped_fields1670[4]
            if field1675 is not None:
                self.newline()
                assert field1675 is not None
                opt_val1676 = field1675
                self.pretty_config_dict(opt_val1676)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_table_def(self, msg: logic_pb2.RelationId):
<<<<<<< HEAD
        flat1603 = self._try_flat(msg, self.pretty_export_iceberg_table_def)
        if flat1603 is not None:
            assert flat1603 is not None
            self.write(flat1603)
            return None
        else:
            fields1602 = msg
            self.write("(table_def")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1602)
=======
        flat1679 = self._try_flat(msg, self.pretty_export_iceberg_table_def)
        if flat1679 is not None:
            assert flat1679 is not None
            self.write(flat1679)
            return None
        else:
            fields1678 = msg
            self.write("(table_def")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1678)
>>>>>>> origin/main
            self.dedent()
            self.write(")")

    def pretty_iceberg_table_properties(self, msg: Sequence[tuple[str, str]]):
<<<<<<< HEAD
        flat1607 = self._try_flat(msg, self.pretty_iceberg_table_properties)
        if flat1607 is not None:
            assert flat1607 is not None
            self.write(flat1607)
            return None
        else:
            fields1604 = msg
            self.write("(table_properties")
            self.indent_sexp()
            if not len(fields1604) == 0:
                self.newline()
                for i1606, elem1605 in enumerate(fields1604):
                    if (i1606 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1605)
=======
        flat1683 = self._try_flat(msg, self.pretty_iceberg_table_properties)
        if flat1683 is not None:
            assert flat1683 is not None
            self.write(flat1683)
            return None
        else:
            fields1680 = msg
            self.write("(table_properties")
            self.indent_sexp()
            if not len(fields1680) == 0:
                self.newline()
                for i1682, elem1681 in enumerate(fields1680):
                    if (i1682 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1681)
>>>>>>> origin/main
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
<<<<<<< HEAD
            _t1806 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1806)
=======
            _t1885 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1885)
>>>>>>> origin/main
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

    def pretty_cdc_targets(self, msg: logic_pb2.CDCTargets):
        self.write("(cdc_targets")
        self.indent_sexp()
        self.newline()
        self.write(":inserts (")
        for _idx, _elem in enumerate(msg.inserts):
            if (_idx > 0):
                self.write(" ")
            self.pprint_dispatch(_elem)
        self.write(")")
        self.newline()
        self.write(":deletes (")
        for _idx, _elem in enumerate(msg.deletes):
            if (_idx > 0):
                self.write(" ")
            self.pprint_dispatch(_elem)
        self.write("))")
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

    def pretty_plain_targets(self, msg: logic_pb2.PlainTargets):
        self.write("(plain_targets")
        self.indent_sexp()
        self.newline()
        self.write(":targets (")
        for _idx, _elem in enumerate(msg.targets):
            if (_idx > 0):
                self.write(" ")
            self.pprint_dispatch(_elem)
        self.write("))")
        self.dedent()

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
        elif isinstance(msg, logic_pb2.TargetRelations):
            self.pretty_target_relations(msg)
        elif isinstance(msg, logic_pb2.NamedColumn):
            self.pretty_named_column(msg)
        elif isinstance(msg, logic_pb2.TargetRelation):
            self.pretty_target_relation(msg)
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
        elif isinstance(msg, logic_pb2.CDCTargets):
            self.pretty_cdc_targets(msg)
        elif isinstance(msg, logic_pb2.DecimalValue):
            self.pretty_decimal_value(msg)
        elif isinstance(msg, logic_pb2.FunctionalDependency):
            self.pretty_functional_dependency(msg)
        elif isinstance(msg, logic_pb2.Int128Value):
            self.pretty_int128_value(msg)
        elif isinstance(msg, logic_pb2.MissingValue):
            self.pretty_missing_value(msg)
        elif isinstance(msg, logic_pb2.PlainTargets):
            self.pretty_plain_targets(msg)
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
