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

    def deconstruct_csv_data_columns_optional(self, msg: logic_pb2.CSVData) -> Sequence[logic_pb2.GNFColumn] | None:
        if msg.HasField("relations"):
            return None
        else:
            _t1845 = None
        return msg.columns

    def deconstruct_csv_data_relations_optional(self, msg: logic_pb2.CSVData) -> logic_pb2.TargetRelations | None:
        if msg.HasField("relations"):
            assert msg.relations is not None
            return msg.relations
        else:
            _t1846 = None
        return None

    def deconstruct_export_csv_output_location(self, msg: transactions_pb2.ExportCSVConfig) -> tuple[str, str]:
        return (msg.path, msg.transaction_output_name,)

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1847 = logic_pb2.Value(int32_value=v)
        return _t1847

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1848 = logic_pb2.Value(int_value=v)
        return _t1848

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1849 = logic_pb2.Value(float_value=v)
        return _t1849

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1850 = logic_pb2.Value(string_value=v)
        return _t1850

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1851 = logic_pb2.Value(boolean_value=v)
        return _t1851

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1852 = logic_pb2.Value(uint128_value=v)
        return _t1852

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1853 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1853,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1854 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1854,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1855 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1855,))
        _t1856 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1856,))
        for pair in sorted(msg.configuration_values.items()):
            result.append(pair)
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1857 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1857,))
        _t1858 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1858,))
        if msg.new_line != "":
            _t1859 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1859,))
        _t1860 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1860,))
        _t1861 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1861,))
        _t1862 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1862,))
        if msg.comment != "":
            _t1863 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1863,))
        for missing_string in msg.missing_strings:
            _t1864 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1864,))
        _t1865 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1865,))
        _t1866 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1866,))
        _t1867 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1867,))
        if msg.partition_size_mb != 0:
            _t1868 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1868,))
        return sorted(result)

    def deconstruct_csv_storage_integration_optional(self, msg: logic_pb2.CSVConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        if not msg.HasField("storage_integration"):
            return None
        else:
            _t1869 = None
        assert msg.storage_integration is not None
        si = msg.storage_integration
        result = []
        if si.provider != "":
            _t1870 = self._make_value_string(si.provider)
            result.append(("provider", _t1870,))
        if si.azure_sas_token != "":
            _t1871 = self._make_value_string("***")
            result.append(("azure_sas_token", _t1871,))
        if si.s3_region != "":
            _t1872 = self._make_value_string(si.s3_region)
            result.append(("s3_region", _t1872,))
        if si.s3_access_key_id != "":
            _t1873 = self._make_value_string("***")
            result.append(("s3_access_key_id", _t1873,))
        if si.s3_secret_access_key != "":
            _t1874 = self._make_value_string("***")
            result.append(("s3_secret_access_key", _t1874,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1875 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1875,))
        _t1876 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1876,))
        _t1877 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1877,))
        _t1878 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1878,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1879 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1879,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1880 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1880,))
        _t1881 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1881,))
        _t1882 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1882,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1883 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1883,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1884 = self._make_value_string(msg.compression)
            result.append(("compression", _t1884,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1885 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1885,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1886 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1886,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1887 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1887,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1888 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1888,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1889 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1889,))
        return sorted(result)

    def mask_secret_value(self, pair: tuple[str, str]) -> str:
        return "***"

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1890 = None
        return None

    def deconstruct_iceberg_data_from_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.from_snapshot is not None
        if msg.from_snapshot != "":
            assert msg.from_snapshot is not None
            return msg.from_snapshot
        else:
            _t1891 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1892 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1893 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1893,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1894 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1894,))
        if msg.compression != "":
            _t1895 = self._make_value_string(msg.compression)
            result.append(("compression", _t1895,))
        if len(result) == 0:
            return None
        else:
            _t1896 = None
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
            _t1897 = None
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
        flat856 = self._try_flat(msg, self.pretty_transaction)
        if flat856 is not None:
            assert flat856 is not None
            self.write(flat856)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1694 = _dollar_dollar.configure
            else:
                _t1694 = None
            if _dollar_dollar.HasField("sync"):
                _t1695 = _dollar_dollar.sync
            else:
                _t1695 = None
            fields847 = (_t1694, _t1695, _dollar_dollar.epochs,)
            assert fields847 is not None
            unwrapped_fields848 = fields847
            self.write("(transaction")
            self.indent_sexp()
            field849 = unwrapped_fields848[0]
            if field849 is not None:
                self.newline()
                assert field849 is not None
                opt_val850 = field849
                self.pretty_configure(opt_val850)
            field851 = unwrapped_fields848[1]
            if field851 is not None:
                self.newline()
                assert field851 is not None
                opt_val852 = field851
                self.pretty_sync(opt_val852)
            field853 = unwrapped_fields848[2]
            if not len(field853) == 0:
                self.newline()
                for i855, elem854 in enumerate(field853):
                    if (i855 > 0):
                        self.newline()
                    self.pretty_epoch(elem854)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat859 = self._try_flat(msg, self.pretty_configure)
        if flat859 is not None:
            assert flat859 is not None
            self.write(flat859)
            return None
        else:
            _dollar_dollar = msg
            _t1696 = self.deconstruct_configure(_dollar_dollar)
            fields857 = _t1696
            assert fields857 is not None
            unwrapped_fields858 = fields857
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields858)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat863 = self._try_flat(msg, self.pretty_config_dict)
        if flat863 is not None:
            assert flat863 is not None
            self.write(flat863)
            return None
        else:
            fields860 = msg
            self.write("{")
            self.indent()
            if not len(fields860) == 0:
                self.newline()
                for i862, elem861 in enumerate(fields860):
                    if (i862 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem861)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat868 = self._try_flat(msg, self.pretty_config_key_value)
        if flat868 is not None:
            assert flat868 is not None
            self.write(flat868)
            return None
        else:
            _dollar_dollar = msg
            fields864 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields864 is not None
            unwrapped_fields865 = fields864
            self.write(":")
            field866 = unwrapped_fields865[0]
            self.write(field866)
            self.write(" ")
            field867 = unwrapped_fields865[1]
            self.pretty_raw_value(field867)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat894 = self._try_flat(msg, self.pretty_raw_value)
        if flat894 is not None:
            assert flat894 is not None
            self.write(flat894)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1697 = _dollar_dollar.date_value
            else:
                _t1697 = None
            deconstruct_result892 = _t1697
            if deconstruct_result892 is not None:
                assert deconstruct_result892 is not None
                unwrapped893 = deconstruct_result892
                self.pretty_raw_date(unwrapped893)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1698 = _dollar_dollar.datetime_value
                else:
                    _t1698 = None
                deconstruct_result890 = _t1698
                if deconstruct_result890 is not None:
                    assert deconstruct_result890 is not None
                    unwrapped891 = deconstruct_result890
                    self.pretty_raw_datetime(unwrapped891)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1699 = _dollar_dollar.string_value
                    else:
                        _t1699 = None
                    deconstruct_result888 = _t1699
                    if deconstruct_result888 is not None:
                        assert deconstruct_result888 is not None
                        unwrapped889 = deconstruct_result888
                        self.write(self.format_string_value(unwrapped889))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1700 = _dollar_dollar.int32_value
                        else:
                            _t1700 = None
                        deconstruct_result886 = _t1700
                        if deconstruct_result886 is not None:
                            assert deconstruct_result886 is not None
                            unwrapped887 = deconstruct_result886
                            self.write((str(unwrapped887) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1701 = _dollar_dollar.int_value
                            else:
                                _t1701 = None
                            deconstruct_result884 = _t1701
                            if deconstruct_result884 is not None:
                                assert deconstruct_result884 is not None
                                unwrapped885 = deconstruct_result884
                                self.write(str(unwrapped885))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1702 = _dollar_dollar.float32_value
                                else:
                                    _t1702 = None
                                deconstruct_result882 = _t1702
                                if deconstruct_result882 is not None:
                                    assert deconstruct_result882 is not None
                                    unwrapped883 = deconstruct_result882
                                    self.write(self.format_float32_literal(unwrapped883))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1703 = _dollar_dollar.float_value
                                    else:
                                        _t1703 = None
                                    deconstruct_result880 = _t1703
                                    if deconstruct_result880 is not None:
                                        assert deconstruct_result880 is not None
                                        unwrapped881 = deconstruct_result880
                                        self.write(str(unwrapped881))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1704 = _dollar_dollar.uint32_value
                                        else:
                                            _t1704 = None
                                        deconstruct_result878 = _t1704
                                        if deconstruct_result878 is not None:
                                            assert deconstruct_result878 is not None
                                            unwrapped879 = deconstruct_result878
                                            self.write((str(unwrapped879) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1705 = _dollar_dollar.uint128_value
                                            else:
                                                _t1705 = None
                                            deconstruct_result876 = _t1705
                                            if deconstruct_result876 is not None:
                                                assert deconstruct_result876 is not None
                                                unwrapped877 = deconstruct_result876
                                                self.write(self.format_uint128(unwrapped877))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1706 = _dollar_dollar.int128_value
                                                else:
                                                    _t1706 = None
                                                deconstruct_result874 = _t1706
                                                if deconstruct_result874 is not None:
                                                    assert deconstruct_result874 is not None
                                                    unwrapped875 = deconstruct_result874
                                                    self.write(self.format_int128(unwrapped875))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1707 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1707 = None
                                                    deconstruct_result872 = _t1707
                                                    if deconstruct_result872 is not None:
                                                        assert deconstruct_result872 is not None
                                                        unwrapped873 = deconstruct_result872
                                                        self.write(self.format_decimal(unwrapped873))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1708 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1708 = None
                                                        deconstruct_result870 = _t1708
                                                        if deconstruct_result870 is not None:
                                                            assert deconstruct_result870 is not None
                                                            unwrapped871 = deconstruct_result870
                                                            self.pretty_boolean_value(unwrapped871)
                                                        else:
                                                            fields869 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat900 = self._try_flat(msg, self.pretty_raw_date)
        if flat900 is not None:
            assert flat900 is not None
            self.write(flat900)
            return None
        else:
            _dollar_dollar = msg
            fields895 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields895 is not None
            unwrapped_fields896 = fields895
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field897 = unwrapped_fields896[0]
            self.write(str(field897))
            self.newline()
            field898 = unwrapped_fields896[1]
            self.write(str(field898))
            self.newline()
            field899 = unwrapped_fields896[2]
            self.write(str(field899))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat911 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat911 is not None:
            assert flat911 is not None
            self.write(flat911)
            return None
        else:
            _dollar_dollar = msg
            fields901 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields901 is not None
            unwrapped_fields902 = fields901
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field903 = unwrapped_fields902[0]
            self.write(str(field903))
            self.newline()
            field904 = unwrapped_fields902[1]
            self.write(str(field904))
            self.newline()
            field905 = unwrapped_fields902[2]
            self.write(str(field905))
            self.newline()
            field906 = unwrapped_fields902[3]
            self.write(str(field906))
            self.newline()
            field907 = unwrapped_fields902[4]
            self.write(str(field907))
            self.newline()
            field908 = unwrapped_fields902[5]
            self.write(str(field908))
            field909 = unwrapped_fields902[6]
            if field909 is not None:
                self.newline()
                assert field909 is not None
                opt_val910 = field909
                self.write(str(opt_val910))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1709 = ()
        else:
            _t1709 = None
        deconstruct_result914 = _t1709
        if deconstruct_result914 is not None:
            assert deconstruct_result914 is not None
            unwrapped915 = deconstruct_result914
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1710 = ()
            else:
                _t1710 = None
            deconstruct_result912 = _t1710
            if deconstruct_result912 is not None:
                assert deconstruct_result912 is not None
                unwrapped913 = deconstruct_result912
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat920 = self._try_flat(msg, self.pretty_sync)
        if flat920 is not None:
            assert flat920 is not None
            self.write(flat920)
            return None
        else:
            _dollar_dollar = msg
            fields916 = _dollar_dollar.fragments
            assert fields916 is not None
            unwrapped_fields917 = fields916
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields917) == 0:
                self.newline()
                for i919, elem918 in enumerate(unwrapped_fields917):
                    if (i919 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem918)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat923 = self._try_flat(msg, self.pretty_fragment_id)
        if flat923 is not None:
            assert flat923 is not None
            self.write(flat923)
            return None
        else:
            _dollar_dollar = msg
            fields921 = self.fragment_id_to_string(_dollar_dollar)
            assert fields921 is not None
            unwrapped_fields922 = fields921
            self.write(":")
            self.write(unwrapped_fields922)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat930 = self._try_flat(msg, self.pretty_epoch)
        if flat930 is not None:
            assert flat930 is not None
            self.write(flat930)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1711 = _dollar_dollar.writes
            else:
                _t1711 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1712 = _dollar_dollar.reads
            else:
                _t1712 = None
            fields924 = (_t1711, _t1712,)
            assert fields924 is not None
            unwrapped_fields925 = fields924
            self.write("(epoch")
            self.indent_sexp()
            field926 = unwrapped_fields925[0]
            if field926 is not None:
                self.newline()
                assert field926 is not None
                opt_val927 = field926
                self.pretty_epoch_writes(opt_val927)
            field928 = unwrapped_fields925[1]
            if field928 is not None:
                self.newline()
                assert field928 is not None
                opt_val929 = field928
                self.pretty_epoch_reads(opt_val929)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat934 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat934 is not None:
            assert flat934 is not None
            self.write(flat934)
            return None
        else:
            fields931 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields931) == 0:
                self.newline()
                for i933, elem932 in enumerate(fields931):
                    if (i933 > 0):
                        self.newline()
                    self.pretty_write(elem932)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat943 = self._try_flat(msg, self.pretty_write)
        if flat943 is not None:
            assert flat943 is not None
            self.write(flat943)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1713 = _dollar_dollar.define
            else:
                _t1713 = None
            deconstruct_result941 = _t1713
            if deconstruct_result941 is not None:
                assert deconstruct_result941 is not None
                unwrapped942 = deconstruct_result941
                self.pretty_define(unwrapped942)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1714 = _dollar_dollar.undefine
                else:
                    _t1714 = None
                deconstruct_result939 = _t1714
                if deconstruct_result939 is not None:
                    assert deconstruct_result939 is not None
                    unwrapped940 = deconstruct_result939
                    self.pretty_undefine(unwrapped940)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1715 = _dollar_dollar.context
                    else:
                        _t1715 = None
                    deconstruct_result937 = _t1715
                    if deconstruct_result937 is not None:
                        assert deconstruct_result937 is not None
                        unwrapped938 = deconstruct_result937
                        self.pretty_context(unwrapped938)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1716 = _dollar_dollar.snapshot
                        else:
                            _t1716 = None
                        deconstruct_result935 = _t1716
                        if deconstruct_result935 is not None:
                            assert deconstruct_result935 is not None
                            unwrapped936 = deconstruct_result935
                            self.pretty_snapshot(unwrapped936)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat946 = self._try_flat(msg, self.pretty_define)
        if flat946 is not None:
            assert flat946 is not None
            self.write(flat946)
            return None
        else:
            _dollar_dollar = msg
            fields944 = _dollar_dollar.fragment
            assert fields944 is not None
            unwrapped_fields945 = fields944
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields945)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat953 = self._try_flat(msg, self.pretty_fragment)
        if flat953 is not None:
            assert flat953 is not None
            self.write(flat953)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields947 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields947 is not None
            unwrapped_fields948 = fields947
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field949 = unwrapped_fields948[0]
            self.pretty_new_fragment_id(field949)
            field950 = unwrapped_fields948[1]
            if not len(field950) == 0:
                self.newline()
                for i952, elem951 in enumerate(field950):
                    if (i952 > 0):
                        self.newline()
                    self.pretty_declaration(elem951)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat955 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat955 is not None:
            assert flat955 is not None
            self.write(flat955)
            return None
        else:
            fields954 = msg
            self.pretty_fragment_id(fields954)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat964 = self._try_flat(msg, self.pretty_declaration)
        if flat964 is not None:
            assert flat964 is not None
            self.write(flat964)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1717 = getattr(_dollar_dollar, 'def')
            else:
                _t1717 = None
            deconstruct_result962 = _t1717
            if deconstruct_result962 is not None:
                assert deconstruct_result962 is not None
                unwrapped963 = deconstruct_result962
                self.pretty_def(unwrapped963)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1718 = _dollar_dollar.algorithm
                else:
                    _t1718 = None
                deconstruct_result960 = _t1718
                if deconstruct_result960 is not None:
                    assert deconstruct_result960 is not None
                    unwrapped961 = deconstruct_result960
                    self.pretty_algorithm(unwrapped961)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1719 = _dollar_dollar.constraint
                    else:
                        _t1719 = None
                    deconstruct_result958 = _t1719
                    if deconstruct_result958 is not None:
                        assert deconstruct_result958 is not None
                        unwrapped959 = deconstruct_result958
                        self.pretty_constraint(unwrapped959)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1720 = _dollar_dollar.data
                        else:
                            _t1720 = None
                        deconstruct_result956 = _t1720
                        if deconstruct_result956 is not None:
                            assert deconstruct_result956 is not None
                            unwrapped957 = deconstruct_result956
                            self.pretty_data(unwrapped957)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat971 = self._try_flat(msg, self.pretty_def)
        if flat971 is not None:
            assert flat971 is not None
            self.write(flat971)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1721 = _dollar_dollar.attrs
            else:
                _t1721 = None
            fields965 = (_dollar_dollar.name, _dollar_dollar.body, _t1721,)
            assert fields965 is not None
            unwrapped_fields966 = fields965
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field967 = unwrapped_fields966[0]
            self.pretty_relation_id(field967)
            self.newline()
            field968 = unwrapped_fields966[1]
            self.pretty_abstraction(field968)
            field969 = unwrapped_fields966[2]
            if field969 is not None:
                self.newline()
                assert field969 is not None
                opt_val970 = field969
                self.pretty_attrs(opt_val970)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat976 = self._try_flat(msg, self.pretty_relation_id)
        if flat976 is not None:
            assert flat976 is not None
            self.write(flat976)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1723 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1722 = _t1723
            else:
                _t1722 = None
            deconstruct_result974 = _t1722
            if deconstruct_result974 is not None:
                assert deconstruct_result974 is not None
                unwrapped975 = deconstruct_result974
                self.write(":")
                self.write(unwrapped975)
            else:
                _dollar_dollar = msg
                _t1724 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result972 = _t1724
                if deconstruct_result972 is not None:
                    assert deconstruct_result972 is not None
                    unwrapped973 = deconstruct_result972
                    self.write(self.format_uint128(unwrapped973))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat981 = self._try_flat(msg, self.pretty_abstraction)
        if flat981 is not None:
            assert flat981 is not None
            self.write(flat981)
            return None
        else:
            _dollar_dollar = msg
            _t1725 = self.deconstruct_bindings(_dollar_dollar)
            fields977 = (_t1725, _dollar_dollar.value,)
            assert fields977 is not None
            unwrapped_fields978 = fields977
            self.write("(")
            self.indent()
            field979 = unwrapped_fields978[0]
            self.pretty_bindings(field979)
            self.newline()
            field980 = unwrapped_fields978[1]
            self.pretty_formula(field980)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat989 = self._try_flat(msg, self.pretty_bindings)
        if flat989 is not None:
            assert flat989 is not None
            self.write(flat989)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1726 = _dollar_dollar[1]
            else:
                _t1726 = None
            fields982 = (_dollar_dollar[0], _t1726,)
            assert fields982 is not None
            unwrapped_fields983 = fields982
            self.write("[")
            self.indent()
            field984 = unwrapped_fields983[0]
            for i986, elem985 in enumerate(field984):
                if (i986 > 0):
                    self.newline()
                self.pretty_binding(elem985)
            field987 = unwrapped_fields983[1]
            if field987 is not None:
                self.newline()
                assert field987 is not None
                opt_val988 = field987
                self.pretty_value_bindings(opt_val988)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat994 = self._try_flat(msg, self.pretty_binding)
        if flat994 is not None:
            assert flat994 is not None
            self.write(flat994)
            return None
        else:
            _dollar_dollar = msg
            fields990 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields990 is not None
            unwrapped_fields991 = fields990
            field992 = unwrapped_fields991[0]
            self.write(field992)
            self.write("::")
            field993 = unwrapped_fields991[1]
            self.pretty_type(field993)

    def pretty_type(self, msg: logic_pb2.Type):
        flat1023 = self._try_flat(msg, self.pretty_type)
        if flat1023 is not None:
            assert flat1023 is not None
            self.write(flat1023)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1727 = _dollar_dollar.unspecified_type
            else:
                _t1727 = None
            deconstruct_result1021 = _t1727
            if deconstruct_result1021 is not None:
                assert deconstruct_result1021 is not None
                unwrapped1022 = deconstruct_result1021
                self.pretty_unspecified_type(unwrapped1022)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1728 = _dollar_dollar.string_type
                else:
                    _t1728 = None
                deconstruct_result1019 = _t1728
                if deconstruct_result1019 is not None:
                    assert deconstruct_result1019 is not None
                    unwrapped1020 = deconstruct_result1019
                    self.pretty_string_type(unwrapped1020)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1729 = _dollar_dollar.int_type
                    else:
                        _t1729 = None
                    deconstruct_result1017 = _t1729
                    if deconstruct_result1017 is not None:
                        assert deconstruct_result1017 is not None
                        unwrapped1018 = deconstruct_result1017
                        self.pretty_int_type(unwrapped1018)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1730 = _dollar_dollar.float_type
                        else:
                            _t1730 = None
                        deconstruct_result1015 = _t1730
                        if deconstruct_result1015 is not None:
                            assert deconstruct_result1015 is not None
                            unwrapped1016 = deconstruct_result1015
                            self.pretty_float_type(unwrapped1016)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1731 = _dollar_dollar.uint128_type
                            else:
                                _t1731 = None
                            deconstruct_result1013 = _t1731
                            if deconstruct_result1013 is not None:
                                assert deconstruct_result1013 is not None
                                unwrapped1014 = deconstruct_result1013
                                self.pretty_uint128_type(unwrapped1014)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1732 = _dollar_dollar.int128_type
                                else:
                                    _t1732 = None
                                deconstruct_result1011 = _t1732
                                if deconstruct_result1011 is not None:
                                    assert deconstruct_result1011 is not None
                                    unwrapped1012 = deconstruct_result1011
                                    self.pretty_int128_type(unwrapped1012)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1733 = _dollar_dollar.date_type
                                    else:
                                        _t1733 = None
                                    deconstruct_result1009 = _t1733
                                    if deconstruct_result1009 is not None:
                                        assert deconstruct_result1009 is not None
                                        unwrapped1010 = deconstruct_result1009
                                        self.pretty_date_type(unwrapped1010)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1734 = _dollar_dollar.datetime_type
                                        else:
                                            _t1734 = None
                                        deconstruct_result1007 = _t1734
                                        if deconstruct_result1007 is not None:
                                            assert deconstruct_result1007 is not None
                                            unwrapped1008 = deconstruct_result1007
                                            self.pretty_datetime_type(unwrapped1008)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1735 = _dollar_dollar.missing_type
                                            else:
                                                _t1735 = None
                                            deconstruct_result1005 = _t1735
                                            if deconstruct_result1005 is not None:
                                                assert deconstruct_result1005 is not None
                                                unwrapped1006 = deconstruct_result1005
                                                self.pretty_missing_type(unwrapped1006)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1736 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1736 = None
                                                deconstruct_result1003 = _t1736
                                                if deconstruct_result1003 is not None:
                                                    assert deconstruct_result1003 is not None
                                                    unwrapped1004 = deconstruct_result1003
                                                    self.pretty_decimal_type(unwrapped1004)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1737 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1737 = None
                                                    deconstruct_result1001 = _t1737
                                                    if deconstruct_result1001 is not None:
                                                        assert deconstruct_result1001 is not None
                                                        unwrapped1002 = deconstruct_result1001
                                                        self.pretty_boolean_type(unwrapped1002)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1738 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1738 = None
                                                        deconstruct_result999 = _t1738
                                                        if deconstruct_result999 is not None:
                                                            assert deconstruct_result999 is not None
                                                            unwrapped1000 = deconstruct_result999
                                                            self.pretty_int32_type(unwrapped1000)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1739 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1739 = None
                                                            deconstruct_result997 = _t1739
                                                            if deconstruct_result997 is not None:
                                                                assert deconstruct_result997 is not None
                                                                unwrapped998 = deconstruct_result997
                                                                self.pretty_float32_type(unwrapped998)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1740 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1740 = None
                                                                deconstruct_result995 = _t1740
                                                                if deconstruct_result995 is not None:
                                                                    assert deconstruct_result995 is not None
                                                                    unwrapped996 = deconstruct_result995
                                                                    self.pretty_uint32_type(unwrapped996)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields1024 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields1025 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields1026 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields1027 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields1028 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields1029 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields1030 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields1031 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields1032 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat1037 = self._try_flat(msg, self.pretty_decimal_type)
        if flat1037 is not None:
            assert flat1037 is not None
            self.write(flat1037)
            return None
        else:
            _dollar_dollar = msg
            fields1033 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields1033 is not None
            unwrapped_fields1034 = fields1033
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field1035 = unwrapped_fields1034[0]
            self.write(str(field1035))
            self.newline()
            field1036 = unwrapped_fields1034[1]
            self.write(str(field1036))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields1038 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields1039 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields1040 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields1041 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat1045 = self._try_flat(msg, self.pretty_value_bindings)
        if flat1045 is not None:
            assert flat1045 is not None
            self.write(flat1045)
            return None
        else:
            fields1042 = msg
            self.write("|")
            if not len(fields1042) == 0:
                self.write(" ")
                for i1044, elem1043 in enumerate(fields1042):
                    if (i1044 > 0):
                        self.newline()
                    self.pretty_binding(elem1043)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1072 = self._try_flat(msg, self.pretty_formula)
        if flat1072 is not None:
            assert flat1072 is not None
            self.write(flat1072)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1741 = _dollar_dollar.conjunction
            else:
                _t1741 = None
            deconstruct_result1070 = _t1741
            if deconstruct_result1070 is not None:
                assert deconstruct_result1070 is not None
                unwrapped1071 = deconstruct_result1070
                self.pretty_true(unwrapped1071)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1742 = _dollar_dollar.disjunction
                else:
                    _t1742 = None
                deconstruct_result1068 = _t1742
                if deconstruct_result1068 is not None:
                    assert deconstruct_result1068 is not None
                    unwrapped1069 = deconstruct_result1068
                    self.pretty_false(unwrapped1069)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1743 = _dollar_dollar.exists
                    else:
                        _t1743 = None
                    deconstruct_result1066 = _t1743
                    if deconstruct_result1066 is not None:
                        assert deconstruct_result1066 is not None
                        unwrapped1067 = deconstruct_result1066
                        self.pretty_exists(unwrapped1067)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1744 = _dollar_dollar.reduce
                        else:
                            _t1744 = None
                        deconstruct_result1064 = _t1744
                        if deconstruct_result1064 is not None:
                            assert deconstruct_result1064 is not None
                            unwrapped1065 = deconstruct_result1064
                            self.pretty_reduce(unwrapped1065)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1745 = _dollar_dollar.conjunction
                            else:
                                _t1745 = None
                            deconstruct_result1062 = _t1745
                            if deconstruct_result1062 is not None:
                                assert deconstruct_result1062 is not None
                                unwrapped1063 = deconstruct_result1062
                                self.pretty_conjunction(unwrapped1063)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1746 = _dollar_dollar.disjunction
                                else:
                                    _t1746 = None
                                deconstruct_result1060 = _t1746
                                if deconstruct_result1060 is not None:
                                    assert deconstruct_result1060 is not None
                                    unwrapped1061 = deconstruct_result1060
                                    self.pretty_disjunction(unwrapped1061)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1747 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1747 = None
                                    deconstruct_result1058 = _t1747
                                    if deconstruct_result1058 is not None:
                                        assert deconstruct_result1058 is not None
                                        unwrapped1059 = deconstruct_result1058
                                        self.pretty_not(unwrapped1059)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1748 = _dollar_dollar.ffi
                                        else:
                                            _t1748 = None
                                        deconstruct_result1056 = _t1748
                                        if deconstruct_result1056 is not None:
                                            assert deconstruct_result1056 is not None
                                            unwrapped1057 = deconstruct_result1056
                                            self.pretty_ffi(unwrapped1057)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1749 = _dollar_dollar.atom
                                            else:
                                                _t1749 = None
                                            deconstruct_result1054 = _t1749
                                            if deconstruct_result1054 is not None:
                                                assert deconstruct_result1054 is not None
                                                unwrapped1055 = deconstruct_result1054
                                                self.pretty_atom(unwrapped1055)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1750 = _dollar_dollar.pragma
                                                else:
                                                    _t1750 = None
                                                deconstruct_result1052 = _t1750
                                                if deconstruct_result1052 is not None:
                                                    assert deconstruct_result1052 is not None
                                                    unwrapped1053 = deconstruct_result1052
                                                    self.pretty_pragma(unwrapped1053)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1751 = _dollar_dollar.primitive
                                                    else:
                                                        _t1751 = None
                                                    deconstruct_result1050 = _t1751
                                                    if deconstruct_result1050 is not None:
                                                        assert deconstruct_result1050 is not None
                                                        unwrapped1051 = deconstruct_result1050
                                                        self.pretty_primitive(unwrapped1051)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1752 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1752 = None
                                                        deconstruct_result1048 = _t1752
                                                        if deconstruct_result1048 is not None:
                                                            assert deconstruct_result1048 is not None
                                                            unwrapped1049 = deconstruct_result1048
                                                            self.pretty_rel_atom(unwrapped1049)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1753 = _dollar_dollar.cast
                                                            else:
                                                                _t1753 = None
                                                            deconstruct_result1046 = _t1753
                                                            if deconstruct_result1046 is not None:
                                                                assert deconstruct_result1046 is not None
                                                                unwrapped1047 = deconstruct_result1046
                                                                self.pretty_cast(unwrapped1047)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields1073 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1074 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1079 = self._try_flat(msg, self.pretty_exists)
        if flat1079 is not None:
            assert flat1079 is not None
            self.write(flat1079)
            return None
        else:
            _dollar_dollar = msg
            _t1754 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1075 = (_t1754, _dollar_dollar.body.value,)
            assert fields1075 is not None
            unwrapped_fields1076 = fields1075
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1077 = unwrapped_fields1076[0]
            self.pretty_bindings(field1077)
            self.newline()
            field1078 = unwrapped_fields1076[1]
            self.pretty_formula(field1078)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1085 = self._try_flat(msg, self.pretty_reduce)
        if flat1085 is not None:
            assert flat1085 is not None
            self.write(flat1085)
            return None
        else:
            _dollar_dollar = msg
            fields1080 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1080 is not None
            unwrapped_fields1081 = fields1080
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1082 = unwrapped_fields1081[0]
            self.pretty_abstraction(field1082)
            self.newline()
            field1083 = unwrapped_fields1081[1]
            self.pretty_abstraction(field1083)
            self.newline()
            field1084 = unwrapped_fields1081[2]
            self.pretty_terms(field1084)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1089 = self._try_flat(msg, self.pretty_terms)
        if flat1089 is not None:
            assert flat1089 is not None
            self.write(flat1089)
            return None
        else:
            fields1086 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1086) == 0:
                self.newline()
                for i1088, elem1087 in enumerate(fields1086):
                    if (i1088 > 0):
                        self.newline()
                    self.pretty_term(elem1087)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1094 = self._try_flat(msg, self.pretty_term)
        if flat1094 is not None:
            assert flat1094 is not None
            self.write(flat1094)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1755 = _dollar_dollar.var
            else:
                _t1755 = None
            deconstruct_result1092 = _t1755
            if deconstruct_result1092 is not None:
                assert deconstruct_result1092 is not None
                unwrapped1093 = deconstruct_result1092
                self.pretty_var(unwrapped1093)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1756 = _dollar_dollar.constant
                else:
                    _t1756 = None
                deconstruct_result1090 = _t1756
                if deconstruct_result1090 is not None:
                    assert deconstruct_result1090 is not None
                    unwrapped1091 = deconstruct_result1090
                    self.pretty_value(unwrapped1091)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1097 = self._try_flat(msg, self.pretty_var)
        if flat1097 is not None:
            assert flat1097 is not None
            self.write(flat1097)
            return None
        else:
            _dollar_dollar = msg
            fields1095 = _dollar_dollar.name
            assert fields1095 is not None
            unwrapped_fields1096 = fields1095
            self.write(unwrapped_fields1096)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1123 = self._try_flat(msg, self.pretty_value)
        if flat1123 is not None:
            assert flat1123 is not None
            self.write(flat1123)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1757 = _dollar_dollar.date_value
            else:
                _t1757 = None
            deconstruct_result1121 = _t1757
            if deconstruct_result1121 is not None:
                assert deconstruct_result1121 is not None
                unwrapped1122 = deconstruct_result1121
                self.pretty_date(unwrapped1122)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1758 = _dollar_dollar.datetime_value
                else:
                    _t1758 = None
                deconstruct_result1119 = _t1758
                if deconstruct_result1119 is not None:
                    assert deconstruct_result1119 is not None
                    unwrapped1120 = deconstruct_result1119
                    self.pretty_datetime(unwrapped1120)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1759 = _dollar_dollar.string_value
                    else:
                        _t1759 = None
                    deconstruct_result1117 = _t1759
                    if deconstruct_result1117 is not None:
                        assert deconstruct_result1117 is not None
                        unwrapped1118 = deconstruct_result1117
                        self.write(self.format_string_value(unwrapped1118))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1760 = _dollar_dollar.int32_value
                        else:
                            _t1760 = None
                        deconstruct_result1115 = _t1760
                        if deconstruct_result1115 is not None:
                            assert deconstruct_result1115 is not None
                            unwrapped1116 = deconstruct_result1115
                            self.write((str(unwrapped1116) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1761 = _dollar_dollar.int_value
                            else:
                                _t1761 = None
                            deconstruct_result1113 = _t1761
                            if deconstruct_result1113 is not None:
                                assert deconstruct_result1113 is not None
                                unwrapped1114 = deconstruct_result1113
                                self.write(str(unwrapped1114))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1762 = _dollar_dollar.float32_value
                                else:
                                    _t1762 = None
                                deconstruct_result1111 = _t1762
                                if deconstruct_result1111 is not None:
                                    assert deconstruct_result1111 is not None
                                    unwrapped1112 = deconstruct_result1111
                                    self.write(self.format_float32_literal(unwrapped1112))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1763 = _dollar_dollar.float_value
                                    else:
                                        _t1763 = None
                                    deconstruct_result1109 = _t1763
                                    if deconstruct_result1109 is not None:
                                        assert deconstruct_result1109 is not None
                                        unwrapped1110 = deconstruct_result1109
                                        self.write(str(unwrapped1110))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1764 = _dollar_dollar.uint32_value
                                        else:
                                            _t1764 = None
                                        deconstruct_result1107 = _t1764
                                        if deconstruct_result1107 is not None:
                                            assert deconstruct_result1107 is not None
                                            unwrapped1108 = deconstruct_result1107
                                            self.write((str(unwrapped1108) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1765 = _dollar_dollar.uint128_value
                                            else:
                                                _t1765 = None
                                            deconstruct_result1105 = _t1765
                                            if deconstruct_result1105 is not None:
                                                assert deconstruct_result1105 is not None
                                                unwrapped1106 = deconstruct_result1105
                                                self.write(self.format_uint128(unwrapped1106))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1766 = _dollar_dollar.int128_value
                                                else:
                                                    _t1766 = None
                                                deconstruct_result1103 = _t1766
                                                if deconstruct_result1103 is not None:
                                                    assert deconstruct_result1103 is not None
                                                    unwrapped1104 = deconstruct_result1103
                                                    self.write(self.format_int128(unwrapped1104))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1767 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1767 = None
                                                    deconstruct_result1101 = _t1767
                                                    if deconstruct_result1101 is not None:
                                                        assert deconstruct_result1101 is not None
                                                        unwrapped1102 = deconstruct_result1101
                                                        self.write(self.format_decimal(unwrapped1102))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1768 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1768 = None
                                                        deconstruct_result1099 = _t1768
                                                        if deconstruct_result1099 is not None:
                                                            assert deconstruct_result1099 is not None
                                                            unwrapped1100 = deconstruct_result1099
                                                            self.pretty_boolean_value(unwrapped1100)
                                                        else:
                                                            fields1098 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1129 = self._try_flat(msg, self.pretty_date)
        if flat1129 is not None:
            assert flat1129 is not None
            self.write(flat1129)
            return None
        else:
            _dollar_dollar = msg
            fields1124 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1124 is not None
            unwrapped_fields1125 = fields1124
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1126 = unwrapped_fields1125[0]
            self.write(str(field1126))
            self.newline()
            field1127 = unwrapped_fields1125[1]
            self.write(str(field1127))
            self.newline()
            field1128 = unwrapped_fields1125[2]
            self.write(str(field1128))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1140 = self._try_flat(msg, self.pretty_datetime)
        if flat1140 is not None:
            assert flat1140 is not None
            self.write(flat1140)
            return None
        else:
            _dollar_dollar = msg
            fields1130 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1130 is not None
            unwrapped_fields1131 = fields1130
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1132 = unwrapped_fields1131[0]
            self.write(str(field1132))
            self.newline()
            field1133 = unwrapped_fields1131[1]
            self.write(str(field1133))
            self.newline()
            field1134 = unwrapped_fields1131[2]
            self.write(str(field1134))
            self.newline()
            field1135 = unwrapped_fields1131[3]
            self.write(str(field1135))
            self.newline()
            field1136 = unwrapped_fields1131[4]
            self.write(str(field1136))
            self.newline()
            field1137 = unwrapped_fields1131[5]
            self.write(str(field1137))
            field1138 = unwrapped_fields1131[6]
            if field1138 is not None:
                self.newline()
                assert field1138 is not None
                opt_val1139 = field1138
                self.write(str(opt_val1139))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1145 = self._try_flat(msg, self.pretty_conjunction)
        if flat1145 is not None:
            assert flat1145 is not None
            self.write(flat1145)
            return None
        else:
            _dollar_dollar = msg
            fields1141 = _dollar_dollar.args
            assert fields1141 is not None
            unwrapped_fields1142 = fields1141
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1142) == 0:
                self.newline()
                for i1144, elem1143 in enumerate(unwrapped_fields1142):
                    if (i1144 > 0):
                        self.newline()
                    self.pretty_formula(elem1143)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1150 = self._try_flat(msg, self.pretty_disjunction)
        if flat1150 is not None:
            assert flat1150 is not None
            self.write(flat1150)
            return None
        else:
            _dollar_dollar = msg
            fields1146 = _dollar_dollar.args
            assert fields1146 is not None
            unwrapped_fields1147 = fields1146
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1147) == 0:
                self.newline()
                for i1149, elem1148 in enumerate(unwrapped_fields1147):
                    if (i1149 > 0):
                        self.newline()
                    self.pretty_formula(elem1148)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1153 = self._try_flat(msg, self.pretty_not)
        if flat1153 is not None:
            assert flat1153 is not None
            self.write(flat1153)
            return None
        else:
            _dollar_dollar = msg
            fields1151 = _dollar_dollar.arg
            assert fields1151 is not None
            unwrapped_fields1152 = fields1151
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1152)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1159 = self._try_flat(msg, self.pretty_ffi)
        if flat1159 is not None:
            assert flat1159 is not None
            self.write(flat1159)
            return None
        else:
            _dollar_dollar = msg
            fields1154 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1154 is not None
            unwrapped_fields1155 = fields1154
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1156 = unwrapped_fields1155[0]
            self.pretty_name(field1156)
            self.newline()
            field1157 = unwrapped_fields1155[1]
            self.pretty_ffi_args(field1157)
            self.newline()
            field1158 = unwrapped_fields1155[2]
            self.pretty_terms(field1158)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1161 = self._try_flat(msg, self.pretty_name)
        if flat1161 is not None:
            assert flat1161 is not None
            self.write(flat1161)
            return None
        else:
            fields1160 = msg
            self.write(":")
            self.write(fields1160)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1165 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1165 is not None:
            assert flat1165 is not None
            self.write(flat1165)
            return None
        else:
            fields1162 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1162) == 0:
                self.newline()
                for i1164, elem1163 in enumerate(fields1162):
                    if (i1164 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1163)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1172 = self._try_flat(msg, self.pretty_atom)
        if flat1172 is not None:
            assert flat1172 is not None
            self.write(flat1172)
            return None
        else:
            _dollar_dollar = msg
            fields1166 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1166 is not None
            unwrapped_fields1167 = fields1166
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1168 = unwrapped_fields1167[0]
            self.pretty_relation_id(field1168)
            field1169 = unwrapped_fields1167[1]
            if not len(field1169) == 0:
                self.newline()
                for i1171, elem1170 in enumerate(field1169):
                    if (i1171 > 0):
                        self.newline()
                    self.pretty_term(elem1170)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1179 = self._try_flat(msg, self.pretty_pragma)
        if flat1179 is not None:
            assert flat1179 is not None
            self.write(flat1179)
            return None
        else:
            _dollar_dollar = msg
            fields1173 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1173 is not None
            unwrapped_fields1174 = fields1173
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1175 = unwrapped_fields1174[0]
            self.pretty_name(field1175)
            field1176 = unwrapped_fields1174[1]
            if not len(field1176) == 0:
                self.newline()
                for i1178, elem1177 in enumerate(field1176):
                    if (i1178 > 0):
                        self.newline()
                    self.pretty_term(elem1177)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1195 = self._try_flat(msg, self.pretty_primitive)
        if flat1195 is not None:
            assert flat1195 is not None
            self.write(flat1195)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1769 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1769 = None
            guard_result1194 = _t1769
            if guard_result1194 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1770 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1770 = None
                guard_result1193 = _t1770
                if guard_result1193 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1771 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1771 = None
                    guard_result1192 = _t1771
                    if guard_result1192 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1772 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1772 = None
                        guard_result1191 = _t1772
                        if guard_result1191 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1773 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1773 = None
                            guard_result1190 = _t1773
                            if guard_result1190 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1774 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1774 = None
                                guard_result1189 = _t1774
                                if guard_result1189 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1775 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1775 = None
                                    guard_result1188 = _t1775
                                    if guard_result1188 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1776 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1776 = None
                                        guard_result1187 = _t1776
                                        if guard_result1187 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1777 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1777 = None
                                            guard_result1186 = _t1777
                                            if guard_result1186 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1180 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1180 is not None
                                                unwrapped_fields1181 = fields1180
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1182 = unwrapped_fields1181[0]
                                                self.pretty_name(field1182)
                                                field1183 = unwrapped_fields1181[1]
                                                if not len(field1183) == 0:
                                                    self.newline()
                                                    for i1185, elem1184 in enumerate(field1183):
                                                        if (i1185 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1184)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1200 = self._try_flat(msg, self.pretty_eq)
        if flat1200 is not None:
            assert flat1200 is not None
            self.write(flat1200)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1778 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1778 = None
            fields1196 = _t1778
            assert fields1196 is not None
            unwrapped_fields1197 = fields1196
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1198 = unwrapped_fields1197[0]
            self.pretty_term(field1198)
            self.newline()
            field1199 = unwrapped_fields1197[1]
            self.pretty_term(field1199)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1205 = self._try_flat(msg, self.pretty_lt)
        if flat1205 is not None:
            assert flat1205 is not None
            self.write(flat1205)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1779 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1779 = None
            fields1201 = _t1779
            assert fields1201 is not None
            unwrapped_fields1202 = fields1201
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1203 = unwrapped_fields1202[0]
            self.pretty_term(field1203)
            self.newline()
            field1204 = unwrapped_fields1202[1]
            self.pretty_term(field1204)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1210 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1210 is not None:
            assert flat1210 is not None
            self.write(flat1210)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1780 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1780 = None
            fields1206 = _t1780
            assert fields1206 is not None
            unwrapped_fields1207 = fields1206
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1208 = unwrapped_fields1207[0]
            self.pretty_term(field1208)
            self.newline()
            field1209 = unwrapped_fields1207[1]
            self.pretty_term(field1209)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1215 = self._try_flat(msg, self.pretty_gt)
        if flat1215 is not None:
            assert flat1215 is not None
            self.write(flat1215)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1781 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1781 = None
            fields1211 = _t1781
            assert fields1211 is not None
            unwrapped_fields1212 = fields1211
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1213 = unwrapped_fields1212[0]
            self.pretty_term(field1213)
            self.newline()
            field1214 = unwrapped_fields1212[1]
            self.pretty_term(field1214)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1220 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1220 is not None:
            assert flat1220 is not None
            self.write(flat1220)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1782 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1782 = None
            fields1216 = _t1782
            assert fields1216 is not None
            unwrapped_fields1217 = fields1216
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1218 = unwrapped_fields1217[0]
            self.pretty_term(field1218)
            self.newline()
            field1219 = unwrapped_fields1217[1]
            self.pretty_term(field1219)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1226 = self._try_flat(msg, self.pretty_add)
        if flat1226 is not None:
            assert flat1226 is not None
            self.write(flat1226)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1783 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1783 = None
            fields1221 = _t1783
            assert fields1221 is not None
            unwrapped_fields1222 = fields1221
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1223 = unwrapped_fields1222[0]
            self.pretty_term(field1223)
            self.newline()
            field1224 = unwrapped_fields1222[1]
            self.pretty_term(field1224)
            self.newline()
            field1225 = unwrapped_fields1222[2]
            self.pretty_term(field1225)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1232 = self._try_flat(msg, self.pretty_minus)
        if flat1232 is not None:
            assert flat1232 is not None
            self.write(flat1232)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1784 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1784 = None
            fields1227 = _t1784
            assert fields1227 is not None
            unwrapped_fields1228 = fields1227
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1229 = unwrapped_fields1228[0]
            self.pretty_term(field1229)
            self.newline()
            field1230 = unwrapped_fields1228[1]
            self.pretty_term(field1230)
            self.newline()
            field1231 = unwrapped_fields1228[2]
            self.pretty_term(field1231)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1238 = self._try_flat(msg, self.pretty_multiply)
        if flat1238 is not None:
            assert flat1238 is not None
            self.write(flat1238)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1785 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1785 = None
            fields1233 = _t1785
            assert fields1233 is not None
            unwrapped_fields1234 = fields1233
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1235 = unwrapped_fields1234[0]
            self.pretty_term(field1235)
            self.newline()
            field1236 = unwrapped_fields1234[1]
            self.pretty_term(field1236)
            self.newline()
            field1237 = unwrapped_fields1234[2]
            self.pretty_term(field1237)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1244 = self._try_flat(msg, self.pretty_divide)
        if flat1244 is not None:
            assert flat1244 is not None
            self.write(flat1244)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1786 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1786 = None
            fields1239 = _t1786
            assert fields1239 is not None
            unwrapped_fields1240 = fields1239
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1241 = unwrapped_fields1240[0]
            self.pretty_term(field1241)
            self.newline()
            field1242 = unwrapped_fields1240[1]
            self.pretty_term(field1242)
            self.newline()
            field1243 = unwrapped_fields1240[2]
            self.pretty_term(field1243)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1249 = self._try_flat(msg, self.pretty_rel_term)
        if flat1249 is not None:
            assert flat1249 is not None
            self.write(flat1249)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1787 = _dollar_dollar.specialized_value
            else:
                _t1787 = None
            deconstruct_result1247 = _t1787
            if deconstruct_result1247 is not None:
                assert deconstruct_result1247 is not None
                unwrapped1248 = deconstruct_result1247
                self.pretty_specialized_value(unwrapped1248)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1788 = _dollar_dollar.term
                else:
                    _t1788 = None
                deconstruct_result1245 = _t1788
                if deconstruct_result1245 is not None:
                    assert deconstruct_result1245 is not None
                    unwrapped1246 = deconstruct_result1245
                    self.pretty_term(unwrapped1246)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1251 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1251 is not None:
            assert flat1251 is not None
            self.write(flat1251)
            return None
        else:
            fields1250 = msg
            self.write("#")
            self.pretty_raw_value(fields1250)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1258 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1258 is not None:
            assert flat1258 is not None
            self.write(flat1258)
            return None
        else:
            _dollar_dollar = msg
            fields1252 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1252 is not None
            unwrapped_fields1253 = fields1252
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1254 = unwrapped_fields1253[0]
            self.pretty_name(field1254)
            field1255 = unwrapped_fields1253[1]
            if not len(field1255) == 0:
                self.newline()
                for i1257, elem1256 in enumerate(field1255):
                    if (i1257 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1256)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1263 = self._try_flat(msg, self.pretty_cast)
        if flat1263 is not None:
            assert flat1263 is not None
            self.write(flat1263)
            return None
        else:
            _dollar_dollar = msg
            fields1259 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1259 is not None
            unwrapped_fields1260 = fields1259
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1261 = unwrapped_fields1260[0]
            self.pretty_term(field1261)
            self.newline()
            field1262 = unwrapped_fields1260[1]
            self.pretty_term(field1262)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1267 = self._try_flat(msg, self.pretty_attrs)
        if flat1267 is not None:
            assert flat1267 is not None
            self.write(flat1267)
            return None
        else:
            fields1264 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1264) == 0:
                self.newline()
                for i1266, elem1265 in enumerate(fields1264):
                    if (i1266 > 0):
                        self.newline()
                    self.pretty_attribute(elem1265)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1274 = self._try_flat(msg, self.pretty_attribute)
        if flat1274 is not None:
            assert flat1274 is not None
            self.write(flat1274)
            return None
        else:
            _dollar_dollar = msg
            fields1268 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1268 is not None
            unwrapped_fields1269 = fields1268
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1270 = unwrapped_fields1269[0]
            self.pretty_name(field1270)
            field1271 = unwrapped_fields1269[1]
            if not len(field1271) == 0:
                self.newline()
                for i1273, elem1272 in enumerate(field1271):
                    if (i1273 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1272)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1283 = self._try_flat(msg, self.pretty_algorithm)
        if flat1283 is not None:
            assert flat1283 is not None
            self.write(flat1283)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1789 = _dollar_dollar.attrs
            else:
                _t1789 = None
            fields1275 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body, _t1789,)
            assert fields1275 is not None
            unwrapped_fields1276 = fields1275
            self.write("(algorithm")
            self.indent_sexp()
            field1277 = unwrapped_fields1276[0]
            if not len(field1277) == 0:
                self.newline()
                for i1279, elem1278 in enumerate(field1277):
                    if (i1279 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1278)
            self.newline()
            field1280 = unwrapped_fields1276[1]
            self.pretty_script(field1280)
            field1281 = unwrapped_fields1276[2]
            if field1281 is not None:
                self.newline()
                assert field1281 is not None
                opt_val1282 = field1281
                self.pretty_attrs(opt_val1282)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1288 = self._try_flat(msg, self.pretty_script)
        if flat1288 is not None:
            assert flat1288 is not None
            self.write(flat1288)
            return None
        else:
            _dollar_dollar = msg
            fields1284 = _dollar_dollar.constructs
            assert fields1284 is not None
            unwrapped_fields1285 = fields1284
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1285) == 0:
                self.newline()
                for i1287, elem1286 in enumerate(unwrapped_fields1285):
                    if (i1287 > 0):
                        self.newline()
                    self.pretty_construct(elem1286)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1293 = self._try_flat(msg, self.pretty_construct)
        if flat1293 is not None:
            assert flat1293 is not None
            self.write(flat1293)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1790 = _dollar_dollar.loop
            else:
                _t1790 = None
            deconstruct_result1291 = _t1790
            if deconstruct_result1291 is not None:
                assert deconstruct_result1291 is not None
                unwrapped1292 = deconstruct_result1291
                self.pretty_loop(unwrapped1292)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1791 = _dollar_dollar.instruction
                else:
                    _t1791 = None
                deconstruct_result1289 = _t1791
                if deconstruct_result1289 is not None:
                    assert deconstruct_result1289 is not None
                    unwrapped1290 = deconstruct_result1289
                    self.pretty_instruction(unwrapped1290)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1300 = self._try_flat(msg, self.pretty_loop)
        if flat1300 is not None:
            assert flat1300 is not None
            self.write(flat1300)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1792 = _dollar_dollar.attrs
            else:
                _t1792 = None
            fields1294 = (_dollar_dollar.init, _dollar_dollar.body, _t1792,)
            assert fields1294 is not None
            unwrapped_fields1295 = fields1294
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1296 = unwrapped_fields1295[0]
            self.pretty_init(field1296)
            self.newline()
            field1297 = unwrapped_fields1295[1]
            self.pretty_script(field1297)
            field1298 = unwrapped_fields1295[2]
            if field1298 is not None:
                self.newline()
                assert field1298 is not None
                opt_val1299 = field1298
                self.pretty_attrs(opt_val1299)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1304 = self._try_flat(msg, self.pretty_init)
        if flat1304 is not None:
            assert flat1304 is not None
            self.write(flat1304)
            return None
        else:
            fields1301 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1301) == 0:
                self.newline()
                for i1303, elem1302 in enumerate(fields1301):
                    if (i1303 > 0):
                        self.newline()
                    self.pretty_instruction(elem1302)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1315 = self._try_flat(msg, self.pretty_instruction)
        if flat1315 is not None:
            assert flat1315 is not None
            self.write(flat1315)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1793 = _dollar_dollar.assign
            else:
                _t1793 = None
            deconstruct_result1313 = _t1793
            if deconstruct_result1313 is not None:
                assert deconstruct_result1313 is not None
                unwrapped1314 = deconstruct_result1313
                self.pretty_assign(unwrapped1314)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1794 = _dollar_dollar.upsert
                else:
                    _t1794 = None
                deconstruct_result1311 = _t1794
                if deconstruct_result1311 is not None:
                    assert deconstruct_result1311 is not None
                    unwrapped1312 = deconstruct_result1311
                    self.pretty_upsert(unwrapped1312)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1795 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1795 = None
                    deconstruct_result1309 = _t1795
                    if deconstruct_result1309 is not None:
                        assert deconstruct_result1309 is not None
                        unwrapped1310 = deconstruct_result1309
                        self.pretty_break(unwrapped1310)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1796 = _dollar_dollar.monoid_def
                        else:
                            _t1796 = None
                        deconstruct_result1307 = _t1796
                        if deconstruct_result1307 is not None:
                            assert deconstruct_result1307 is not None
                            unwrapped1308 = deconstruct_result1307
                            self.pretty_monoid_def(unwrapped1308)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1797 = _dollar_dollar.monus_def
                            else:
                                _t1797 = None
                            deconstruct_result1305 = _t1797
                            if deconstruct_result1305 is not None:
                                assert deconstruct_result1305 is not None
                                unwrapped1306 = deconstruct_result1305
                                self.pretty_monus_def(unwrapped1306)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1322 = self._try_flat(msg, self.pretty_assign)
        if flat1322 is not None:
            assert flat1322 is not None
            self.write(flat1322)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1798 = _dollar_dollar.attrs
            else:
                _t1798 = None
            fields1316 = (_dollar_dollar.name, _dollar_dollar.body, _t1798,)
            assert fields1316 is not None
            unwrapped_fields1317 = fields1316
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1318 = unwrapped_fields1317[0]
            self.pretty_relation_id(field1318)
            self.newline()
            field1319 = unwrapped_fields1317[1]
            self.pretty_abstraction(field1319)
            field1320 = unwrapped_fields1317[2]
            if field1320 is not None:
                self.newline()
                assert field1320 is not None
                opt_val1321 = field1320
                self.pretty_attrs(opt_val1321)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1329 = self._try_flat(msg, self.pretty_upsert)
        if flat1329 is not None:
            assert flat1329 is not None
            self.write(flat1329)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1799 = _dollar_dollar.attrs
            else:
                _t1799 = None
            fields1323 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1799,)
            assert fields1323 is not None
            unwrapped_fields1324 = fields1323
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1325 = unwrapped_fields1324[0]
            self.pretty_relation_id(field1325)
            self.newline()
            field1326 = unwrapped_fields1324[1]
            self.pretty_abstraction_with_arity(field1326)
            field1327 = unwrapped_fields1324[2]
            if field1327 is not None:
                self.newline()
                assert field1327 is not None
                opt_val1328 = field1327
                self.pretty_attrs(opt_val1328)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1334 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1334 is not None:
            assert flat1334 is not None
            self.write(flat1334)
            return None
        else:
            _dollar_dollar = msg
            _t1800 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1330 = (_t1800, _dollar_dollar[0].value,)
            assert fields1330 is not None
            unwrapped_fields1331 = fields1330
            self.write("(")
            self.indent()
            field1332 = unwrapped_fields1331[0]
            self.pretty_bindings(field1332)
            self.newline()
            field1333 = unwrapped_fields1331[1]
            self.pretty_formula(field1333)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1341 = self._try_flat(msg, self.pretty_break)
        if flat1341 is not None:
            assert flat1341 is not None
            self.write(flat1341)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1801 = _dollar_dollar.attrs
            else:
                _t1801 = None
            fields1335 = (_dollar_dollar.name, _dollar_dollar.body, _t1801,)
            assert fields1335 is not None
            unwrapped_fields1336 = fields1335
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1337 = unwrapped_fields1336[0]
            self.pretty_relation_id(field1337)
            self.newline()
            field1338 = unwrapped_fields1336[1]
            self.pretty_abstraction(field1338)
            field1339 = unwrapped_fields1336[2]
            if field1339 is not None:
                self.newline()
                assert field1339 is not None
                opt_val1340 = field1339
                self.pretty_attrs(opt_val1340)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1349 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1349 is not None:
            assert flat1349 is not None
            self.write(flat1349)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1802 = _dollar_dollar.attrs
            else:
                _t1802 = None
            fields1342 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1802,)
            assert fields1342 is not None
            unwrapped_fields1343 = fields1342
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1344 = unwrapped_fields1343[0]
            self.pretty_monoid(field1344)
            self.newline()
            field1345 = unwrapped_fields1343[1]
            self.pretty_relation_id(field1345)
            self.newline()
            field1346 = unwrapped_fields1343[2]
            self.pretty_abstraction_with_arity(field1346)
            field1347 = unwrapped_fields1343[3]
            if field1347 is not None:
                self.newline()
                assert field1347 is not None
                opt_val1348 = field1347
                self.pretty_attrs(opt_val1348)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1358 = self._try_flat(msg, self.pretty_monoid)
        if flat1358 is not None:
            assert flat1358 is not None
            self.write(flat1358)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1803 = _dollar_dollar.or_monoid
            else:
                _t1803 = None
            deconstruct_result1356 = _t1803
            if deconstruct_result1356 is not None:
                assert deconstruct_result1356 is not None
                unwrapped1357 = deconstruct_result1356
                self.pretty_or_monoid(unwrapped1357)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1804 = _dollar_dollar.min_monoid
                else:
                    _t1804 = None
                deconstruct_result1354 = _t1804
                if deconstruct_result1354 is not None:
                    assert deconstruct_result1354 is not None
                    unwrapped1355 = deconstruct_result1354
                    self.pretty_min_monoid(unwrapped1355)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1805 = _dollar_dollar.max_monoid
                    else:
                        _t1805 = None
                    deconstruct_result1352 = _t1805
                    if deconstruct_result1352 is not None:
                        assert deconstruct_result1352 is not None
                        unwrapped1353 = deconstruct_result1352
                        self.pretty_max_monoid(unwrapped1353)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1806 = _dollar_dollar.sum_monoid
                        else:
                            _t1806 = None
                        deconstruct_result1350 = _t1806
                        if deconstruct_result1350 is not None:
                            assert deconstruct_result1350 is not None
                            unwrapped1351 = deconstruct_result1350
                            self.pretty_sum_monoid(unwrapped1351)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1359 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1362 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1362 is not None:
            assert flat1362 is not None
            self.write(flat1362)
            return None
        else:
            _dollar_dollar = msg
            fields1360 = _dollar_dollar.type
            assert fields1360 is not None
            unwrapped_fields1361 = fields1360
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1361)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1365 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1365 is not None:
            assert flat1365 is not None
            self.write(flat1365)
            return None
        else:
            _dollar_dollar = msg
            fields1363 = _dollar_dollar.type
            assert fields1363 is not None
            unwrapped_fields1364 = fields1363
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1364)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1368 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1368 is not None:
            assert flat1368 is not None
            self.write(flat1368)
            return None
        else:
            _dollar_dollar = msg
            fields1366 = _dollar_dollar.type
            assert fields1366 is not None
            unwrapped_fields1367 = fields1366
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1367)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1376 = self._try_flat(msg, self.pretty_monus_def)
        if flat1376 is not None:
            assert flat1376 is not None
            self.write(flat1376)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1807 = _dollar_dollar.attrs
            else:
                _t1807 = None
            fields1369 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1807,)
            assert fields1369 is not None
            unwrapped_fields1370 = fields1369
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1371 = unwrapped_fields1370[0]
            self.pretty_monoid(field1371)
            self.newline()
            field1372 = unwrapped_fields1370[1]
            self.pretty_relation_id(field1372)
            self.newline()
            field1373 = unwrapped_fields1370[2]
            self.pretty_abstraction_with_arity(field1373)
            field1374 = unwrapped_fields1370[3]
            if field1374 is not None:
                self.newline()
                assert field1374 is not None
                opt_val1375 = field1374
                self.pretty_attrs(opt_val1375)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1383 = self._try_flat(msg, self.pretty_constraint)
        if flat1383 is not None:
            assert flat1383 is not None
            self.write(flat1383)
            return None
        else:
            _dollar_dollar = msg
            fields1377 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1377 is not None
            unwrapped_fields1378 = fields1377
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1379 = unwrapped_fields1378[0]
            self.pretty_relation_id(field1379)
            self.newline()
            field1380 = unwrapped_fields1378[1]
            self.pretty_abstraction(field1380)
            self.newline()
            field1381 = unwrapped_fields1378[2]
            self.pretty_functional_dependency_keys(field1381)
            self.newline()
            field1382 = unwrapped_fields1378[3]
            self.pretty_functional_dependency_values(field1382)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1387 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1387 is not None:
            assert flat1387 is not None
            self.write(flat1387)
            return None
        else:
            fields1384 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1384) == 0:
                self.newline()
                for i1386, elem1385 in enumerate(fields1384):
                    if (i1386 > 0):
                        self.newline()
                    self.pretty_var(elem1385)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1391 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1391 is not None:
            assert flat1391 is not None
            self.write(flat1391)
            return None
        else:
            fields1388 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1388) == 0:
                self.newline()
                for i1390, elem1389 in enumerate(fields1388):
                    if (i1390 > 0):
                        self.newline()
                    self.pretty_var(elem1389)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1400 = self._try_flat(msg, self.pretty_data)
        if flat1400 is not None:
            assert flat1400 is not None
            self.write(flat1400)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1808 = _dollar_dollar.edb
            else:
                _t1808 = None
            deconstruct_result1398 = _t1808
            if deconstruct_result1398 is not None:
                assert deconstruct_result1398 is not None
                unwrapped1399 = deconstruct_result1398
                self.pretty_edb(unwrapped1399)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1809 = _dollar_dollar.betree_relation
                else:
                    _t1809 = None
                deconstruct_result1396 = _t1809
                if deconstruct_result1396 is not None:
                    assert deconstruct_result1396 is not None
                    unwrapped1397 = deconstruct_result1396
                    self.pretty_betree_relation(unwrapped1397)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1810 = _dollar_dollar.csv_data
                    else:
                        _t1810 = None
                    deconstruct_result1394 = _t1810
                    if deconstruct_result1394 is not None:
                        assert deconstruct_result1394 is not None
                        unwrapped1395 = deconstruct_result1394
                        self.pretty_csv_data(unwrapped1395)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1811 = _dollar_dollar.iceberg_data
                        else:
                            _t1811 = None
                        deconstruct_result1392 = _t1811
                        if deconstruct_result1392 is not None:
                            assert deconstruct_result1392 is not None
                            unwrapped1393 = deconstruct_result1392
                            self.pretty_iceberg_data(unwrapped1393)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1406 = self._try_flat(msg, self.pretty_edb)
        if flat1406 is not None:
            assert flat1406 is not None
            self.write(flat1406)
            return None
        else:
            _dollar_dollar = msg
            fields1401 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1401 is not None
            unwrapped_fields1402 = fields1401
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1403 = unwrapped_fields1402[0]
            self.pretty_relation_id(field1403)
            self.newline()
            field1404 = unwrapped_fields1402[1]
            self.pretty_edb_path(field1404)
            self.newline()
            field1405 = unwrapped_fields1402[2]
            self.pretty_edb_types(field1405)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1410 = self._try_flat(msg, self.pretty_edb_path)
        if flat1410 is not None:
            assert flat1410 is not None
            self.write(flat1410)
            return None
        else:
            fields1407 = msg
            self.write("[")
            self.indent()
            for i1409, elem1408 in enumerate(fields1407):
                if (i1409 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1408))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1414 = self._try_flat(msg, self.pretty_edb_types)
        if flat1414 is not None:
            assert flat1414 is not None
            self.write(flat1414)
            return None
        else:
            fields1411 = msg
            self.write("[")
            self.indent()
            for i1413, elem1412 in enumerate(fields1411):
                if (i1413 > 0):
                    self.newline()
                self.pretty_type(elem1412)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1419 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1419 is not None:
            assert flat1419 is not None
            self.write(flat1419)
            return None
        else:
            _dollar_dollar = msg
            fields1415 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1415 is not None
            unwrapped_fields1416 = fields1415
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1417 = unwrapped_fields1416[0]
            self.pretty_relation_id(field1417)
            self.newline()
            field1418 = unwrapped_fields1416[1]
            self.pretty_betree_info(field1418)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1425 = self._try_flat(msg, self.pretty_betree_info)
        if flat1425 is not None:
            assert flat1425 is not None
            self.write(flat1425)
            return None
        else:
            _dollar_dollar = msg
            _t1812 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1420 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1812,)
            assert fields1420 is not None
            unwrapped_fields1421 = fields1420
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1422 = unwrapped_fields1421[0]
            self.pretty_betree_info_key_types(field1422)
            self.newline()
            field1423 = unwrapped_fields1421[1]
            self.pretty_betree_info_value_types(field1423)
            self.newline()
            field1424 = unwrapped_fields1421[2]
            self.pretty_config_dict(field1424)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1429 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1429 is not None:
            assert flat1429 is not None
            self.write(flat1429)
            return None
        else:
            fields1426 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1426) == 0:
                self.newline()
                for i1428, elem1427 in enumerate(fields1426):
                    if (i1428 > 0):
                        self.newline()
                    self.pretty_type(elem1427)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1433 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1433 is not None:
            assert flat1433 is not None
            self.write(flat1433)
            return None
        else:
            fields1430 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1430) == 0:
                self.newline()
                for i1432, elem1431 in enumerate(fields1430):
                    if (i1432 > 0):
                        self.newline()
                    self.pretty_type(elem1431)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1443 = self._try_flat(msg, self.pretty_csv_data)
        if flat1443 is not None:
            assert flat1443 is not None
            self.write(flat1443)
            return None
        else:
            _dollar_dollar = msg
            _t1813 = self.deconstruct_csv_data_columns_optional(_dollar_dollar)
            _t1814 = self.deconstruct_csv_data_relations_optional(_dollar_dollar)
            fields1434 = (_dollar_dollar.locator, _dollar_dollar.config, _t1813, _t1814, _dollar_dollar.asof,)
            assert fields1434 is not None
            unwrapped_fields1435 = fields1434
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1436 = unwrapped_fields1435[0]
            self.pretty_csvlocator(field1436)
            self.newline()
            field1437 = unwrapped_fields1435[1]
            self.pretty_csv_config(field1437)
            field1438 = unwrapped_fields1435[2]
            if field1438 is not None:
                self.newline()
                assert field1438 is not None
                opt_val1439 = field1438
                self.pretty_gnf_columns(opt_val1439)
            field1440 = unwrapped_fields1435[3]
            if field1440 is not None:
                self.newline()
                assert field1440 is not None
                opt_val1441 = field1440
                self.pretty_target_relations(opt_val1441)
            self.newline()
            field1442 = unwrapped_fields1435[4]
            self.pretty_csv_asof(field1442)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1450 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1450 is not None:
            assert flat1450 is not None
            self.write(flat1450)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1815 = _dollar_dollar.paths
            else:
                _t1815 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1816 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1816 = None
            fields1444 = (_t1815, _t1816,)
            assert fields1444 is not None
            unwrapped_fields1445 = fields1444
            self.write("(csv_locator")
            self.indent_sexp()
            field1446 = unwrapped_fields1445[0]
            if field1446 is not None:
                self.newline()
                assert field1446 is not None
                opt_val1447 = field1446
                self.pretty_csv_locator_paths(opt_val1447)
            field1448 = unwrapped_fields1445[1]
            if field1448 is not None:
                self.newline()
                assert field1448 is not None
                opt_val1449 = field1448
                self.pretty_csv_locator_inline_data(opt_val1449)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1454 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1454 is not None:
            assert flat1454 is not None
            self.write(flat1454)
            return None
        else:
            fields1451 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1451) == 0:
                self.newline()
                for i1453, elem1452 in enumerate(fields1451):
                    if (i1453 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1452))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1456 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1456 is not None:
            assert flat1456 is not None
            self.write(flat1456)
            return None
        else:
            fields1455 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1455))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1462 = self._try_flat(msg, self.pretty_csv_config)
        if flat1462 is not None:
            assert flat1462 is not None
            self.write(flat1462)
            return None
        else:
            _dollar_dollar = msg
            _t1817 = self.deconstruct_csv_config(_dollar_dollar)
            _t1818 = self.deconstruct_csv_storage_integration_optional(_dollar_dollar)
            fields1457 = (_t1817, _t1818,)
            assert fields1457 is not None
            unwrapped_fields1458 = fields1457
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            field1459 = unwrapped_fields1458[0]
            self.pretty_config_dict(field1459)
            field1460 = unwrapped_fields1458[1]
            if field1460 is not None:
                self.newline()
                assert field1460 is not None
                opt_val1461 = field1460
                self.pretty__storage_integration(opt_val1461)
            self.dedent()
            self.write(")")

    def pretty__storage_integration(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat1464 = self._try_flat(msg, self.pretty__storage_integration)
        if flat1464 is not None:
            assert flat1464 is not None
            self.write(flat1464)
            return None
        else:
            fields1463 = msg
            self.write("(storage_integration")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(fields1463)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1468 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1468 is not None:
            assert flat1468 is not None
            self.write(flat1468)
            return None
        else:
            fields1465 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1465) == 0:
                self.newline()
                for i1467, elem1466 in enumerate(fields1465):
                    if (i1467 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1466)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1477 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1477 is not None:
            assert flat1477 is not None
            self.write(flat1477)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1819 = _dollar_dollar.target_id
            else:
                _t1819 = None
            fields1469 = (_dollar_dollar.column_path, _t1819, _dollar_dollar.types,)
            assert fields1469 is not None
            unwrapped_fields1470 = fields1469
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1471 = unwrapped_fields1470[0]
            self.pretty_gnf_column_path(field1471)
            field1472 = unwrapped_fields1470[1]
            if field1472 is not None:
                self.newline()
                assert field1472 is not None
                opt_val1473 = field1472
                self.pretty_relation_id(opt_val1473)
            self.newline()
            self.write("[")
            field1474 = unwrapped_fields1470[2]
            for i1476, elem1475 in enumerate(field1474):
                if (i1476 > 0):
                    self.newline()
                self.pretty_type(elem1475)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1484 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1484 is not None:
            assert flat1484 is not None
            self.write(flat1484)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1820 = _dollar_dollar[0]
            else:
                _t1820 = None
            deconstruct_result1482 = _t1820
            if deconstruct_result1482 is not None:
                assert deconstruct_result1482 is not None
                unwrapped1483 = deconstruct_result1482
                self.write(self.format_string_value(unwrapped1483))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1821 = _dollar_dollar
                else:
                    _t1821 = None
                deconstruct_result1478 = _t1821
                if deconstruct_result1478 is not None:
                    assert deconstruct_result1478 is not None
                    unwrapped1479 = deconstruct_result1478
                    self.write("[")
                    self.indent()
                    for i1481, elem1480 in enumerate(unwrapped1479):
                        if (i1481 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1480))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_target_relations(self, msg: logic_pb2.TargetRelations):
        flat1489 = self._try_flat(msg, self.pretty_target_relations)
        if flat1489 is not None:
            assert flat1489 is not None
            self.write(flat1489)
            return None
        else:
            _dollar_dollar = msg
            fields1485 = (_dollar_dollar.keys, _dollar_dollar,)
            assert fields1485 is not None
            unwrapped_fields1486 = fields1485
            self.write("(relations")
            self.indent_sexp()
            self.newline()
            field1487 = unwrapped_fields1486[0]
            self.pretty_relation_keys(field1487)
            self.newline()
            field1488 = unwrapped_fields1486[1]
            self.pretty_relation_body(field1488)
            self.dedent()
            self.write(")")

    def pretty_relation_keys(self, msg: Sequence[logic_pb2.NamedColumn]):
        flat1493 = self._try_flat(msg, self.pretty_relation_keys)
        if flat1493 is not None:
            assert flat1493 is not None
            self.write(flat1493)
            return None
        else:
            fields1490 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1490) == 0:
                self.newline()
                for i1492, elem1491 in enumerate(fields1490):
                    if (i1492 > 0):
                        self.newline()
                    self.pretty_named_column(elem1491)
            self.dedent()
            self.write(")")

    def pretty_named_column(self, msg: logic_pb2.NamedColumn):
        flat1498 = self._try_flat(msg, self.pretty_named_column)
        if flat1498 is not None:
            assert flat1498 is not None
            self.write(flat1498)
            return None
        else:
            _dollar_dollar = msg
            fields1494 = (_dollar_dollar.name, _dollar_dollar.type,)
            assert fields1494 is not None
            unwrapped_fields1495 = fields1494
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1496 = unwrapped_fields1495[0]
            self.write(self.format_string_value(field1496))
            self.newline()
            field1497 = unwrapped_fields1495[1]
            self.pretty_type(field1497)
            self.dedent()
            self.write(")")

    def pretty_relation_body(self, msg: logic_pb2.TargetRelations):
        flat1505 = self._try_flat(msg, self.pretty_relation_body)
        if flat1505 is not None:
            assert flat1505 is not None
            self.write(flat1505)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("plain"):
                _t1822 = _dollar_dollar.plain.targets
            else:
                _t1822 = None
            deconstruct_result1503 = _t1822
            if deconstruct_result1503 is not None:
                assert deconstruct_result1503 is not None
                unwrapped1504 = deconstruct_result1503
                self.pretty_non_cdc_relations(unwrapped1504)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("cdc"):
                    _t1823 = (_dollar_dollar.cdc.inserts, _dollar_dollar.cdc.deletes,)
                else:
                    _t1823 = None
                deconstruct_result1499 = _t1823
                if deconstruct_result1499 is not None:
                    assert deconstruct_result1499 is not None
                    unwrapped1500 = deconstruct_result1499
                    field1501 = unwrapped1500[0]
                    self.pretty_cdc_inserts(field1501)
                    self.write(" ")
                    field1502 = unwrapped1500[1]
                    self.pretty_cdc_deletes(field1502)
                else:
                    raise ParseError("No matching rule for relation_body")

    def pretty_non_cdc_relations(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1509 = self._try_flat(msg, self.pretty_non_cdc_relations)
        if flat1509 is not None:
            assert flat1509 is not None
            self.write(flat1509)
            return None
        else:
            fields1506 = msg
            for i1508, elem1507 in enumerate(fields1506):
                if (i1508 > 0):
                    self.newline()
                self.pretty_target_relation(elem1507)

    def pretty_target_relation(self, msg: logic_pb2.TargetRelation):
        flat1516 = self._try_flat(msg, self.pretty_target_relation)
        if flat1516 is not None:
            assert flat1516 is not None
            self.write(flat1516)
            return None
        else:
            _dollar_dollar = msg
            fields1510 = (_dollar_dollar.target_id, _dollar_dollar.values,)
            assert fields1510 is not None
            unwrapped_fields1511 = fields1510
            self.write("(relation")
            self.indent_sexp()
            self.newline()
            field1512 = unwrapped_fields1511[0]
            self.pretty_relation_id(field1512)
            field1513 = unwrapped_fields1511[1]
            if not len(field1513) == 0:
                self.newline()
                for i1515, elem1514 in enumerate(field1513):
                    if (i1515 > 0):
                        self.newline()
                    self.pretty_named_column(elem1514)
            self.dedent()
            self.write(")")

    def pretty_cdc_inserts(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1520 = self._try_flat(msg, self.pretty_cdc_inserts)
        if flat1520 is not None:
            assert flat1520 is not None
            self.write(flat1520)
            return None
        else:
            fields1517 = msg
            self.write("(inserts")
            self.indent_sexp()
            if not len(fields1517) == 0:
                self.newline()
                for i1519, elem1518 in enumerate(fields1517):
                    if (i1519 > 0):
                        self.newline()
                    self.pretty_target_relation(elem1518)
            self.dedent()
            self.write(")")

    def pretty_cdc_deletes(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1524 = self._try_flat(msg, self.pretty_cdc_deletes)
        if flat1524 is not None:
            assert flat1524 is not None
            self.write(flat1524)
            return None
        else:
            fields1521 = msg
            self.write("(deletes")
            self.indent_sexp()
            if not len(fields1521) == 0:
                self.newline()
                for i1523, elem1522 in enumerate(fields1521):
                    if (i1523 > 0):
                        self.newline()
                    self.pretty_target_relation(elem1522)
            self.dedent()
            self.write(")")

    def pretty_csv_asof(self, msg: str):
        flat1526 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1526 is not None:
            assert flat1526 is not None
            self.write(flat1526)
            return None
        else:
            fields1525 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1525))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1537 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1537 is not None:
            assert flat1537 is not None
            self.write(flat1537)
            return None
        else:
            _dollar_dollar = msg
            _t1824 = self.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
            _t1825 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1527 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1824, _t1825, _dollar_dollar.returns_delta,)
            assert fields1527 is not None
            unwrapped_fields1528 = fields1527
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1529 = unwrapped_fields1528[0]
            self.pretty_iceberg_locator(field1529)
            self.newline()
            field1530 = unwrapped_fields1528[1]
            self.pretty_iceberg_catalog_config(field1530)
            self.newline()
            field1531 = unwrapped_fields1528[2]
            self.pretty_gnf_columns(field1531)
            field1532 = unwrapped_fields1528[3]
            if field1532 is not None:
                self.newline()
                assert field1532 is not None
                opt_val1533 = field1532
                self.pretty_iceberg_from_snapshot(opt_val1533)
            field1534 = unwrapped_fields1528[4]
            if field1534 is not None:
                self.newline()
                assert field1534 is not None
                opt_val1535 = field1534
                self.pretty_iceberg_to_snapshot(opt_val1535)
            self.newline()
            field1536 = unwrapped_fields1528[5]
            self.pretty_boolean_value(field1536)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1543 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1543 is not None:
            assert flat1543 is not None
            self.write(flat1543)
            return None
        else:
            _dollar_dollar = msg
            fields1538 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1538 is not None
            unwrapped_fields1539 = fields1538
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            field1540 = unwrapped_fields1539[0]
            self.pretty_iceberg_locator_table_name(field1540)
            self.newline()
            field1541 = unwrapped_fields1539[1]
            self.pretty_iceberg_locator_namespace(field1541)
            self.newline()
            field1542 = unwrapped_fields1539[2]
            self.pretty_iceberg_locator_warehouse(field1542)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_table_name(self, msg: str):
        flat1545 = self._try_flat(msg, self.pretty_iceberg_locator_table_name)
        if flat1545 is not None:
            assert flat1545 is not None
            self.write(flat1545)
            return None
        else:
            fields1544 = msg
            self.write("(table_name")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1544))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_namespace(self, msg: Sequence[str]):
        flat1549 = self._try_flat(msg, self.pretty_iceberg_locator_namespace)
        if flat1549 is not None:
            assert flat1549 is not None
            self.write(flat1549)
            return None
        else:
            fields1546 = msg
            self.write("(namespace")
            self.indent_sexp()
            if not len(fields1546) == 0:
                self.newline()
                for i1548, elem1547 in enumerate(fields1546):
                    if (i1548 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1547))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_warehouse(self, msg: str):
        flat1551 = self._try_flat(msg, self.pretty_iceberg_locator_warehouse)
        if flat1551 is not None:
            assert flat1551 is not None
            self.write(flat1551)
            return None
        else:
            fields1550 = msg
            self.write("(warehouse")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1550))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1559 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1559 is not None:
            assert flat1559 is not None
            self.write(flat1559)
            return None
        else:
            _dollar_dollar = msg
            _t1826 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1552 = (_dollar_dollar.catalog_uri, _t1826, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1552 is not None
            unwrapped_fields1553 = fields1552
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            field1554 = unwrapped_fields1553[0]
            self.pretty_iceberg_catalog_uri(field1554)
            field1555 = unwrapped_fields1553[1]
            if field1555 is not None:
                self.newline()
                assert field1555 is not None
                opt_val1556 = field1555
                self.pretty_iceberg_catalog_config_scope(opt_val1556)
            self.newline()
            field1557 = unwrapped_fields1553[2]
            self.pretty_iceberg_properties(field1557)
            self.newline()
            field1558 = unwrapped_fields1553[3]
            self.pretty_iceberg_auth_properties(field1558)
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_uri(self, msg: str):
        flat1561 = self._try_flat(msg, self.pretty_iceberg_catalog_uri)
        if flat1561 is not None:
            assert flat1561 is not None
            self.write(flat1561)
            return None
        else:
            fields1560 = msg
            self.write("(catalog_uri")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1560))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1563 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1563 is not None:
            assert flat1563 is not None
            self.write(flat1563)
            return None
        else:
            fields1562 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1562))
            self.dedent()
            self.write(")")

    def pretty_iceberg_properties(self, msg: Sequence[tuple[str, str]]):
        flat1567 = self._try_flat(msg, self.pretty_iceberg_properties)
        if flat1567 is not None:
            assert flat1567 is not None
            self.write(flat1567)
            return None
        else:
            fields1564 = msg
            self.write("(properties")
            self.indent_sexp()
            if not len(fields1564) == 0:
                self.newline()
                for i1566, elem1565 in enumerate(fields1564):
                    if (i1566 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1565)
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1572 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1572 is not None:
            assert flat1572 is not None
            self.write(flat1572)
            return None
        else:
            _dollar_dollar = msg
            fields1568 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1568 is not None
            unwrapped_fields1569 = fields1568
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1570 = unwrapped_fields1569[0]
            self.write(self.format_string_value(field1570))
            self.newline()
            field1571 = unwrapped_fields1569[1]
            self.write(self.format_string_value(field1571))
            self.dedent()
            self.write(")")

    def pretty_iceberg_auth_properties(self, msg: Sequence[tuple[str, str]]):
        flat1576 = self._try_flat(msg, self.pretty_iceberg_auth_properties)
        if flat1576 is not None:
            assert flat1576 is not None
            self.write(flat1576)
            return None
        else:
            fields1573 = msg
            self.write("(auth_properties")
            self.indent_sexp()
            if not len(fields1573) == 0:
                self.newline()
                for i1575, elem1574 in enumerate(fields1573):
                    if (i1575 > 0):
                        self.newline()
                    self.pretty_iceberg_masked_property_entry(elem1574)
            self.dedent()
            self.write(")")

    def pretty_iceberg_masked_property_entry(self, msg: tuple[str, str]):
        flat1581 = self._try_flat(msg, self.pretty_iceberg_masked_property_entry)
        if flat1581 is not None:
            assert flat1581 is not None
            self.write(flat1581)
            return None
        else:
            _dollar_dollar = msg
            _t1827 = self.mask_secret_value(_dollar_dollar)
            fields1577 = (_dollar_dollar[0], _t1827,)
            assert fields1577 is not None
            unwrapped_fields1578 = fields1577
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1579 = unwrapped_fields1578[0]
            self.write(self.format_string_value(field1579))
            self.newline()
            field1580 = unwrapped_fields1578[1]
            self.write(self.format_string_value(field1580))
            self.dedent()
            self.write(")")

    def pretty_iceberg_from_snapshot(self, msg: str):
        flat1583 = self._try_flat(msg, self.pretty_iceberg_from_snapshot)
        if flat1583 is not None:
            assert flat1583 is not None
            self.write(flat1583)
            return None
        else:
            fields1582 = msg
            self.write("(from_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1582))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1585 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1585 is not None:
            assert flat1585 is not None
            self.write(flat1585)
            return None
        else:
            fields1584 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1584))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1588 = self._try_flat(msg, self.pretty_undefine)
        if flat1588 is not None:
            assert flat1588 is not None
            self.write(flat1588)
            return None
        else:
            _dollar_dollar = msg
            fields1586 = _dollar_dollar.fragment_id
            assert fields1586 is not None
            unwrapped_fields1587 = fields1586
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1587)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1593 = self._try_flat(msg, self.pretty_context)
        if flat1593 is not None:
            assert flat1593 is not None
            self.write(flat1593)
            return None
        else:
            _dollar_dollar = msg
            fields1589 = _dollar_dollar.relations
            assert fields1589 is not None
            unwrapped_fields1590 = fields1589
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1590) == 0:
                self.newline()
                for i1592, elem1591 in enumerate(unwrapped_fields1590):
                    if (i1592 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1591)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1600 = self._try_flat(msg, self.pretty_snapshot)
        if flat1600 is not None:
            assert flat1600 is not None
            self.write(flat1600)
            return None
        else:
            _dollar_dollar = msg
            fields1594 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
            assert fields1594 is not None
            unwrapped_fields1595 = fields1594
            self.write("(snapshot")
            self.indent_sexp()
            self.newline()
            field1596 = unwrapped_fields1595[0]
            self.pretty_edb_path(field1596)
            field1597 = unwrapped_fields1595[1]
            if not len(field1597) == 0:
                self.newline()
                for i1599, elem1598 in enumerate(field1597):
                    if (i1599 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1598)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1605 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1605 is not None:
            assert flat1605 is not None
            self.write(flat1605)
            return None
        else:
            _dollar_dollar = msg
            fields1601 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1601 is not None
            unwrapped_fields1602 = fields1601
            field1603 = unwrapped_fields1602[0]
            self.pretty_edb_path(field1603)
            self.write(" ")
            field1604 = unwrapped_fields1602[1]
            self.pretty_relation_id(field1604)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1609 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1609 is not None:
            assert flat1609 is not None
            self.write(flat1609)
            return None
        else:
            fields1606 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1606) == 0:
                self.newline()
                for i1608, elem1607 in enumerate(fields1606):
                    if (i1608 > 0):
                        self.newline()
                    self.pretty_read(elem1607)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1620 = self._try_flat(msg, self.pretty_read)
        if flat1620 is not None:
            assert flat1620 is not None
            self.write(flat1620)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1828 = _dollar_dollar.demand
            else:
                _t1828 = None
            deconstruct_result1618 = _t1828
            if deconstruct_result1618 is not None:
                assert deconstruct_result1618 is not None
                unwrapped1619 = deconstruct_result1618
                self.pretty_demand(unwrapped1619)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1829 = _dollar_dollar.output
                else:
                    _t1829 = None
                deconstruct_result1616 = _t1829
                if deconstruct_result1616 is not None:
                    assert deconstruct_result1616 is not None
                    unwrapped1617 = deconstruct_result1616
                    self.pretty_output(unwrapped1617)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1830 = _dollar_dollar.what_if
                    else:
                        _t1830 = None
                    deconstruct_result1614 = _t1830
                    if deconstruct_result1614 is not None:
                        assert deconstruct_result1614 is not None
                        unwrapped1615 = deconstruct_result1614
                        self.pretty_what_if(unwrapped1615)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1831 = _dollar_dollar.abort
                        else:
                            _t1831 = None
                        deconstruct_result1612 = _t1831
                        if deconstruct_result1612 is not None:
                            assert deconstruct_result1612 is not None
                            unwrapped1613 = deconstruct_result1612
                            self.pretty_abort(unwrapped1613)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1832 = _dollar_dollar.export
                            else:
                                _t1832 = None
                            deconstruct_result1610 = _t1832
                            if deconstruct_result1610 is not None:
                                assert deconstruct_result1610 is not None
                                unwrapped1611 = deconstruct_result1610
                                self.pretty_export(unwrapped1611)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1623 = self._try_flat(msg, self.pretty_demand)
        if flat1623 is not None:
            assert flat1623 is not None
            self.write(flat1623)
            return None
        else:
            _dollar_dollar = msg
            fields1621 = _dollar_dollar.relation_id
            assert fields1621 is not None
            unwrapped_fields1622 = fields1621
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1622)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1628 = self._try_flat(msg, self.pretty_output)
        if flat1628 is not None:
            assert flat1628 is not None
            self.write(flat1628)
            return None
        else:
            _dollar_dollar = msg
            fields1624 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1624 is not None
            unwrapped_fields1625 = fields1624
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1626 = unwrapped_fields1625[0]
            self.pretty_name(field1626)
            self.newline()
            field1627 = unwrapped_fields1625[1]
            self.pretty_relation_id(field1627)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1633 = self._try_flat(msg, self.pretty_what_if)
        if flat1633 is not None:
            assert flat1633 is not None
            self.write(flat1633)
            return None
        else:
            _dollar_dollar = msg
            fields1629 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1629 is not None
            unwrapped_fields1630 = fields1629
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1631 = unwrapped_fields1630[0]
            self.pretty_name(field1631)
            self.newline()
            field1632 = unwrapped_fields1630[1]
            self.pretty_epoch(field1632)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1639 = self._try_flat(msg, self.pretty_abort)
        if flat1639 is not None:
            assert flat1639 is not None
            self.write(flat1639)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1833 = _dollar_dollar.name
            else:
                _t1833 = None
            fields1634 = (_t1833, _dollar_dollar.relation_id,)
            assert fields1634 is not None
            unwrapped_fields1635 = fields1634
            self.write("(abort")
            self.indent_sexp()
            field1636 = unwrapped_fields1635[0]
            if field1636 is not None:
                self.newline()
                assert field1636 is not None
                opt_val1637 = field1636
                self.pretty_name(opt_val1637)
            self.newline()
            field1638 = unwrapped_fields1635[1]
            self.pretty_relation_id(field1638)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1644 = self._try_flat(msg, self.pretty_export)
        if flat1644 is not None:
            assert flat1644 is not None
            self.write(flat1644)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1834 = _dollar_dollar.csv_config
            else:
                _t1834 = None
            deconstruct_result1642 = _t1834
            if deconstruct_result1642 is not None:
                assert deconstruct_result1642 is not None
                unwrapped1643 = deconstruct_result1642
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1643)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1835 = _dollar_dollar.iceberg_config
                else:
                    _t1835 = None
                deconstruct_result1640 = _t1835
                if deconstruct_result1640 is not None:
                    assert deconstruct_result1640 is not None
                    unwrapped1641 = deconstruct_result1640
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1641)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1655 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1655 is not None:
            assert flat1655 is not None
            self.write(flat1655)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1837 = self.deconstruct_export_csv_output_location(_dollar_dollar)
                _t1836 = (_t1837, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1836 = None
            deconstruct_result1650 = _t1836
            if deconstruct_result1650 is not None:
                assert deconstruct_result1650 is not None
                unwrapped1651 = deconstruct_result1650
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1652 = unwrapped1651[0]
                self.pretty_export_csv_output_location(field1652)
                self.newline()
                field1653 = unwrapped1651[1]
                self.pretty_export_csv_source(field1653)
                self.newline()
                field1654 = unwrapped1651[2]
                self.pretty_csv_config(field1654)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1839 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1838 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1839,)
                else:
                    _t1838 = None
                deconstruct_result1645 = _t1838
                if deconstruct_result1645 is not None:
                    assert deconstruct_result1645 is not None
                    unwrapped1646 = deconstruct_result1645
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1647 = unwrapped1646[0]
                    self.pretty_export_csv_path(field1647)
                    self.newline()
                    field1648 = unwrapped1646[1]
                    self.pretty_export_csv_columns_list(field1648)
                    self.newline()
                    field1649 = unwrapped1646[2]
                    self.pretty_config_dict(field1649)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_output_location(self, msg: tuple[str, str]):
        flat1660 = self._try_flat(msg, self.pretty_export_csv_output_location)
        if flat1660 is not None:
            assert flat1660 is not None
            self.write(flat1660)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar[0] != "":
                _t1840 = _dollar_dollar[0]
            else:
                _t1840 = None
            deconstruct_result1658 = _t1840
            if deconstruct_result1658 is not None:
                assert deconstruct_result1658 is not None
                unwrapped1659 = deconstruct_result1658
                self.write("(path")
                self.indent_sexp()
                self.newline()
                self.write(self.format_string_value(unwrapped1659))
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar[1] != "":
                    _t1841 = _dollar_dollar[1]
                else:
                    _t1841 = None
                deconstruct_result1656 = _t1841
                if deconstruct_result1656 is not None:
                    assert deconstruct_result1656 is not None
                    unwrapped1657 = deconstruct_result1656
                    self.write("(transaction_output_name")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_name(unwrapped1657)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_output_location")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1667 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1667 is not None:
            assert flat1667 is not None
            self.write(flat1667)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1842 = _dollar_dollar.gnf_columns.columns
            else:
                _t1842 = None
            deconstruct_result1663 = _t1842
            if deconstruct_result1663 is not None:
                assert deconstruct_result1663 is not None
                unwrapped1664 = deconstruct_result1663
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1664) == 0:
                    self.newline()
                    for i1666, elem1665 in enumerate(unwrapped1664):
                        if (i1666 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1665)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1843 = _dollar_dollar.table_def
                else:
                    _t1843 = None
                deconstruct_result1661 = _t1843
                if deconstruct_result1661 is not None:
                    assert deconstruct_result1661 is not None
                    unwrapped1662 = deconstruct_result1661
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1662)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1672 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1672 is not None:
            assert flat1672 is not None
            self.write(flat1672)
            return None
        else:
            _dollar_dollar = msg
            fields1668 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1668 is not None
            unwrapped_fields1669 = fields1668
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1670 = unwrapped_fields1669[0]
            self.write(self.format_string_value(field1670))
            self.newline()
            field1671 = unwrapped_fields1669[1]
            self.pretty_relation_id(field1671)
            self.dedent()
            self.write(")")

    def pretty_export_csv_path(self, msg: str):
        flat1674 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1674 is not None:
            assert flat1674 is not None
            self.write(flat1674)
            return None
        else:
            fields1673 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1673))
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1678 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1678 is not None:
            assert flat1678 is not None
            self.write(flat1678)
            return None
        else:
            fields1675 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1675) == 0:
                self.newline()
                for i1677, elem1676 in enumerate(fields1675):
                    if (i1677 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1676)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1687 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1687 is not None:
            assert flat1687 is not None
            self.write(flat1687)
            return None
        else:
            _dollar_dollar = msg
            _t1844 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1679 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sorted(_dollar_dollar.table_properties.items()), _t1844,)
            assert fields1679 is not None
            unwrapped_fields1680 = fields1679
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1681 = unwrapped_fields1680[0]
            self.pretty_iceberg_locator(field1681)
            self.newline()
            field1682 = unwrapped_fields1680[1]
            self.pretty_iceberg_catalog_config(field1682)
            self.newline()
            field1683 = unwrapped_fields1680[2]
            self.pretty_export_iceberg_table_def(field1683)
            self.newline()
            field1684 = unwrapped_fields1680[3]
            self.pretty_iceberg_table_properties(field1684)
            field1685 = unwrapped_fields1680[4]
            if field1685 is not None:
                self.newline()
                assert field1685 is not None
                opt_val1686 = field1685
                self.pretty_config_dict(opt_val1686)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_table_def(self, msg: logic_pb2.RelationId):
        flat1689 = self._try_flat(msg, self.pretty_export_iceberg_table_def)
        if flat1689 is not None:
            assert flat1689 is not None
            self.write(flat1689)
            return None
        else:
            fields1688 = msg
            self.write("(table_def")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1688)
            self.dedent()
            self.write(")")

    def pretty_iceberg_table_properties(self, msg: Sequence[tuple[str, str]]):
        flat1693 = self._try_flat(msg, self.pretty_iceberg_table_properties)
        if flat1693 is not None:
            assert flat1693 is not None
            self.write(flat1693)
            return None
        else:
            fields1690 = msg
            self.write("(table_properties")
            self.indent_sexp()
            if not len(fields1690) == 0:
                self.newline()
                for i1692, elem1691 in enumerate(fields1690):
                    if (i1692 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1691)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1898 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1898)
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
