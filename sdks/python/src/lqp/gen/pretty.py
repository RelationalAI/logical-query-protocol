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

    def deconstruct_relation_keys(self, msg: logic_pb2.TargetRelations) -> tuple[Sequence[logic_pb2.NamedColumn], bool]:
        return (msg.keys, msg.synthetic_key,)

    def deconstruct_load_errors_optional(self, msg: logic_pb2.TargetRelations) -> logic_pb2.RelationId | None:
        if msg.HasField("load_errors"):
            assert msg.load_errors is not None
            return msg.load_errors
        else:
            _t1863 = None
        return None

    def deconstruct_csv_data_columns_optional(self, msg: logic_pb2.CSVData) -> Sequence[logic_pb2.GNFColumn] | None:
        if msg.HasField("relations"):
            return None
        else:
            _t1864 = None
        return msg.columns

    def deconstruct_csv_data_relations_optional(self, msg: logic_pb2.CSVData) -> logic_pb2.TargetRelations | None:
        if msg.HasField("relations"):
            assert msg.relations is not None
            return msg.relations
        else:
            _t1865 = None
        return None

    def deconstruct_export_csv_output_location(self, msg: transactions_pb2.ExportCSVConfig) -> tuple[str, str]:
        return (msg.path, msg.transaction_output_name,)

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1866 = logic_pb2.Value(int32_value=v)
        return _t1866

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1867 = logic_pb2.Value(int_value=v)
        return _t1867

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1868 = logic_pb2.Value(float_value=v)
        return _t1868

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1869 = logic_pb2.Value(string_value=v)
        return _t1869

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1870 = logic_pb2.Value(boolean_value=v)
        return _t1870

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1871 = logic_pb2.Value(uint128_value=v)
        return _t1871

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1872 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1872,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1873 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1873,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1874 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1874,))
        _t1875 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1875,))
        for pair in sorted(msg.configuration_values.items()):
            result.append(pair)
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1876 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1876,))
        _t1877 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1877,))
        if msg.new_line != "":
            _t1878 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1878,))
        _t1879 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1879,))
        _t1880 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1880,))
        _t1881 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1881,))
        if msg.comment != "":
            _t1882 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1882,))
        for missing_string in msg.missing_strings:
            _t1883 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1883,))
        _t1884 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1884,))
        _t1885 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1885,))
        _t1886 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1886,))
        if msg.partition_size_mb != 0:
            _t1887 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1887,))
        return sorted(result)

    def deconstruct_csv_storage_integration_optional(self, msg: logic_pb2.CSVConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        if not msg.HasField("storage_integration"):
            return None
        else:
            _t1888 = None
        assert msg.storage_integration is not None
        si = msg.storage_integration
        result = []
        if si.provider != "":
            _t1889 = self._make_value_string(si.provider)
            result.append(("provider", _t1889,))
        if si.azure_sas_token != "":
            _t1890 = self._make_value_string("***")
            result.append(("azure_sas_token", _t1890,))
        if si.s3_region != "":
            _t1891 = self._make_value_string(si.s3_region)
            result.append(("s3_region", _t1891,))
        if si.s3_access_key_id != "":
            _t1892 = self._make_value_string("***")
            result.append(("s3_access_key_id", _t1892,))
        if si.s3_secret_access_key != "":
            _t1893 = self._make_value_string("***")
            result.append(("s3_secret_access_key", _t1893,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1894 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1894,))
        _t1895 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1895,))
        _t1896 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1896,))
        _t1897 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1897,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1898 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1898,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1899 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1899,))
        _t1900 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1900,))
        _t1901 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1901,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1902 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1902,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1903 = self._make_value_string(msg.compression)
            result.append(("compression", _t1903,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1904 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1904,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1905 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1905,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1906 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1906,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1907 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1907,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1908 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1908,))
        return sorted(result)

    def mask_secret_value(self, pair: tuple[str, str]) -> str:
        return "***"

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1909 = None
        return None

    def deconstruct_iceberg_data_from_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.from_snapshot is not None
        if msg.from_snapshot != "":
            assert msg.from_snapshot is not None
            return msg.from_snapshot
        else:
            _t1910 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1911 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1912 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1912,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1913 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1913,))
        if msg.compression != "":
            _t1914 = self._make_value_string(msg.compression)
            result.append(("compression", _t1914,))
        if len(result) == 0:
            return None
        else:
            _t1915 = None
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
            _t1916 = None
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
        flat863 = self._try_flat(msg, self.pretty_transaction)
        if flat863 is not None:
            assert flat863 is not None
            self.write(flat863)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1708 = _dollar_dollar.configure
            else:
                _t1708 = None
            if _dollar_dollar.HasField("sync"):
                _t1709 = _dollar_dollar.sync
            else:
                _t1709 = None
            fields854 = (_t1708, _t1709, _dollar_dollar.epochs,)
            assert fields854 is not None
            unwrapped_fields855 = fields854
            self.write("(transaction")
            self.indent_sexp()
            field856 = unwrapped_fields855[0]
            if field856 is not None:
                self.newline()
                assert field856 is not None
                opt_val857 = field856
                self.pretty_configure(opt_val857)
            field858 = unwrapped_fields855[1]
            if field858 is not None:
                self.newline()
                assert field858 is not None
                opt_val859 = field858
                self.pretty_sync(opt_val859)
            field860 = unwrapped_fields855[2]
            if not len(field860) == 0:
                self.newline()
                for i862, elem861 in enumerate(field860):
                    if (i862 > 0):
                        self.newline()
                    self.pretty_epoch(elem861)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat866 = self._try_flat(msg, self.pretty_configure)
        if flat866 is not None:
            assert flat866 is not None
            self.write(flat866)
            return None
        else:
            _dollar_dollar = msg
            _t1710 = self.deconstruct_configure(_dollar_dollar)
            fields864 = _t1710
            assert fields864 is not None
            unwrapped_fields865 = fields864
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields865)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat870 = self._try_flat(msg, self.pretty_config_dict)
        if flat870 is not None:
            assert flat870 is not None
            self.write(flat870)
            return None
        else:
            fields867 = msg
            self.write("{")
            self.indent()
            if not len(fields867) == 0:
                self.newline()
                for i869, elem868 in enumerate(fields867):
                    if (i869 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem868)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat875 = self._try_flat(msg, self.pretty_config_key_value)
        if flat875 is not None:
            assert flat875 is not None
            self.write(flat875)
            return None
        else:
            _dollar_dollar = msg
            fields871 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields871 is not None
            unwrapped_fields872 = fields871
            self.write(":")
            field873 = unwrapped_fields872[0]
            self.write(field873)
            self.write(" ")
            field874 = unwrapped_fields872[1]
            self.pretty_raw_value(field874)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat901 = self._try_flat(msg, self.pretty_raw_value)
        if flat901 is not None:
            assert flat901 is not None
            self.write(flat901)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1711 = _dollar_dollar.date_value
            else:
                _t1711 = None
            deconstruct_result899 = _t1711
            if deconstruct_result899 is not None:
                assert deconstruct_result899 is not None
                unwrapped900 = deconstruct_result899
                self.pretty_raw_date(unwrapped900)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1712 = _dollar_dollar.datetime_value
                else:
                    _t1712 = None
                deconstruct_result897 = _t1712
                if deconstruct_result897 is not None:
                    assert deconstruct_result897 is not None
                    unwrapped898 = deconstruct_result897
                    self.pretty_raw_datetime(unwrapped898)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1713 = _dollar_dollar.string_value
                    else:
                        _t1713 = None
                    deconstruct_result895 = _t1713
                    if deconstruct_result895 is not None:
                        assert deconstruct_result895 is not None
                        unwrapped896 = deconstruct_result895
                        self.write(self.format_string_value(unwrapped896))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1714 = _dollar_dollar.int32_value
                        else:
                            _t1714 = None
                        deconstruct_result893 = _t1714
                        if deconstruct_result893 is not None:
                            assert deconstruct_result893 is not None
                            unwrapped894 = deconstruct_result893
                            self.write((str(unwrapped894) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1715 = _dollar_dollar.int_value
                            else:
                                _t1715 = None
                            deconstruct_result891 = _t1715
                            if deconstruct_result891 is not None:
                                assert deconstruct_result891 is not None
                                unwrapped892 = deconstruct_result891
                                self.write(str(unwrapped892))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1716 = _dollar_dollar.float32_value
                                else:
                                    _t1716 = None
                                deconstruct_result889 = _t1716
                                if deconstruct_result889 is not None:
                                    assert deconstruct_result889 is not None
                                    unwrapped890 = deconstruct_result889
                                    self.write(self.format_float32_literal(unwrapped890))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1717 = _dollar_dollar.float_value
                                    else:
                                        _t1717 = None
                                    deconstruct_result887 = _t1717
                                    if deconstruct_result887 is not None:
                                        assert deconstruct_result887 is not None
                                        unwrapped888 = deconstruct_result887
                                        self.write(str(unwrapped888))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1718 = _dollar_dollar.uint32_value
                                        else:
                                            _t1718 = None
                                        deconstruct_result885 = _t1718
                                        if deconstruct_result885 is not None:
                                            assert deconstruct_result885 is not None
                                            unwrapped886 = deconstruct_result885
                                            self.write((str(unwrapped886) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1719 = _dollar_dollar.uint128_value
                                            else:
                                                _t1719 = None
                                            deconstruct_result883 = _t1719
                                            if deconstruct_result883 is not None:
                                                assert deconstruct_result883 is not None
                                                unwrapped884 = deconstruct_result883
                                                self.write(self.format_uint128(unwrapped884))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1720 = _dollar_dollar.int128_value
                                                else:
                                                    _t1720 = None
                                                deconstruct_result881 = _t1720
                                                if deconstruct_result881 is not None:
                                                    assert deconstruct_result881 is not None
                                                    unwrapped882 = deconstruct_result881
                                                    self.write(self.format_int128(unwrapped882))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1721 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1721 = None
                                                    deconstruct_result879 = _t1721
                                                    if deconstruct_result879 is not None:
                                                        assert deconstruct_result879 is not None
                                                        unwrapped880 = deconstruct_result879
                                                        self.write(self.format_decimal(unwrapped880))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1722 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1722 = None
                                                        deconstruct_result877 = _t1722
                                                        if deconstruct_result877 is not None:
                                                            assert deconstruct_result877 is not None
                                                            unwrapped878 = deconstruct_result877
                                                            self.pretty_boolean_value(unwrapped878)
                                                        else:
                                                            fields876 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat907 = self._try_flat(msg, self.pretty_raw_date)
        if flat907 is not None:
            assert flat907 is not None
            self.write(flat907)
            return None
        else:
            _dollar_dollar = msg
            fields902 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields902 is not None
            unwrapped_fields903 = fields902
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field904 = unwrapped_fields903[0]
            self.write(str(field904))
            self.newline()
            field905 = unwrapped_fields903[1]
            self.write(str(field905))
            self.newline()
            field906 = unwrapped_fields903[2]
            self.write(str(field906))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat918 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat918 is not None:
            assert flat918 is not None
            self.write(flat918)
            return None
        else:
            _dollar_dollar = msg
            fields908 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields908 is not None
            unwrapped_fields909 = fields908
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field910 = unwrapped_fields909[0]
            self.write(str(field910))
            self.newline()
            field911 = unwrapped_fields909[1]
            self.write(str(field911))
            self.newline()
            field912 = unwrapped_fields909[2]
            self.write(str(field912))
            self.newline()
            field913 = unwrapped_fields909[3]
            self.write(str(field913))
            self.newline()
            field914 = unwrapped_fields909[4]
            self.write(str(field914))
            self.newline()
            field915 = unwrapped_fields909[5]
            self.write(str(field915))
            field916 = unwrapped_fields909[6]
            if field916 is not None:
                self.newline()
                assert field916 is not None
                opt_val917 = field916
                self.write(str(opt_val917))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1723 = ()
        else:
            _t1723 = None
        deconstruct_result921 = _t1723
        if deconstruct_result921 is not None:
            assert deconstruct_result921 is not None
            unwrapped922 = deconstruct_result921
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1724 = ()
            else:
                _t1724 = None
            deconstruct_result919 = _t1724
            if deconstruct_result919 is not None:
                assert deconstruct_result919 is not None
                unwrapped920 = deconstruct_result919
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat927 = self._try_flat(msg, self.pretty_sync)
        if flat927 is not None:
            assert flat927 is not None
            self.write(flat927)
            return None
        else:
            _dollar_dollar = msg
            fields923 = _dollar_dollar.fragments
            assert fields923 is not None
            unwrapped_fields924 = fields923
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields924) == 0:
                self.newline()
                for i926, elem925 in enumerate(unwrapped_fields924):
                    if (i926 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem925)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat930 = self._try_flat(msg, self.pretty_fragment_id)
        if flat930 is not None:
            assert flat930 is not None
            self.write(flat930)
            return None
        else:
            _dollar_dollar = msg
            fields928 = self.fragment_id_to_string(_dollar_dollar)
            assert fields928 is not None
            unwrapped_fields929 = fields928
            self.write(":")
            self.write(unwrapped_fields929)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat937 = self._try_flat(msg, self.pretty_epoch)
        if flat937 is not None:
            assert flat937 is not None
            self.write(flat937)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1725 = _dollar_dollar.writes
            else:
                _t1725 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1726 = _dollar_dollar.reads
            else:
                _t1726 = None
            fields931 = (_t1725, _t1726,)
            assert fields931 is not None
            unwrapped_fields932 = fields931
            self.write("(epoch")
            self.indent_sexp()
            field933 = unwrapped_fields932[0]
            if field933 is not None:
                self.newline()
                assert field933 is not None
                opt_val934 = field933
                self.pretty_epoch_writes(opt_val934)
            field935 = unwrapped_fields932[1]
            if field935 is not None:
                self.newline()
                assert field935 is not None
                opt_val936 = field935
                self.pretty_epoch_reads(opt_val936)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat941 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat941 is not None:
            assert flat941 is not None
            self.write(flat941)
            return None
        else:
            fields938 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields938) == 0:
                self.newline()
                for i940, elem939 in enumerate(fields938):
                    if (i940 > 0):
                        self.newline()
                    self.pretty_write(elem939)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat950 = self._try_flat(msg, self.pretty_write)
        if flat950 is not None:
            assert flat950 is not None
            self.write(flat950)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1727 = _dollar_dollar.define
            else:
                _t1727 = None
            deconstruct_result948 = _t1727
            if deconstruct_result948 is not None:
                assert deconstruct_result948 is not None
                unwrapped949 = deconstruct_result948
                self.pretty_define(unwrapped949)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1728 = _dollar_dollar.undefine
                else:
                    _t1728 = None
                deconstruct_result946 = _t1728
                if deconstruct_result946 is not None:
                    assert deconstruct_result946 is not None
                    unwrapped947 = deconstruct_result946
                    self.pretty_undefine(unwrapped947)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1729 = _dollar_dollar.context
                    else:
                        _t1729 = None
                    deconstruct_result944 = _t1729
                    if deconstruct_result944 is not None:
                        assert deconstruct_result944 is not None
                        unwrapped945 = deconstruct_result944
                        self.pretty_context(unwrapped945)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1730 = _dollar_dollar.snapshot
                        else:
                            _t1730 = None
                        deconstruct_result942 = _t1730
                        if deconstruct_result942 is not None:
                            assert deconstruct_result942 is not None
                            unwrapped943 = deconstruct_result942
                            self.pretty_snapshot(unwrapped943)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat953 = self._try_flat(msg, self.pretty_define)
        if flat953 is not None:
            assert flat953 is not None
            self.write(flat953)
            return None
        else:
            _dollar_dollar = msg
            fields951 = _dollar_dollar.fragment
            assert fields951 is not None
            unwrapped_fields952 = fields951
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields952)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat960 = self._try_flat(msg, self.pretty_fragment)
        if flat960 is not None:
            assert flat960 is not None
            self.write(flat960)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields954 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields954 is not None
            unwrapped_fields955 = fields954
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field956 = unwrapped_fields955[0]
            self.pretty_new_fragment_id(field956)
            field957 = unwrapped_fields955[1]
            if not len(field957) == 0:
                self.newline()
                for i959, elem958 in enumerate(field957):
                    if (i959 > 0):
                        self.newline()
                    self.pretty_declaration(elem958)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat962 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat962 is not None:
            assert flat962 is not None
            self.write(flat962)
            return None
        else:
            fields961 = msg
            self.pretty_fragment_id(fields961)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat971 = self._try_flat(msg, self.pretty_declaration)
        if flat971 is not None:
            assert flat971 is not None
            self.write(flat971)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1731 = getattr(_dollar_dollar, 'def')
            else:
                _t1731 = None
            deconstruct_result969 = _t1731
            if deconstruct_result969 is not None:
                assert deconstruct_result969 is not None
                unwrapped970 = deconstruct_result969
                self.pretty_def(unwrapped970)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1732 = _dollar_dollar.algorithm
                else:
                    _t1732 = None
                deconstruct_result967 = _t1732
                if deconstruct_result967 is not None:
                    assert deconstruct_result967 is not None
                    unwrapped968 = deconstruct_result967
                    self.pretty_algorithm(unwrapped968)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1733 = _dollar_dollar.constraint
                    else:
                        _t1733 = None
                    deconstruct_result965 = _t1733
                    if deconstruct_result965 is not None:
                        assert deconstruct_result965 is not None
                        unwrapped966 = deconstruct_result965
                        self.pretty_constraint(unwrapped966)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1734 = _dollar_dollar.data
                        else:
                            _t1734 = None
                        deconstruct_result963 = _t1734
                        if deconstruct_result963 is not None:
                            assert deconstruct_result963 is not None
                            unwrapped964 = deconstruct_result963
                            self.pretty_data(unwrapped964)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat978 = self._try_flat(msg, self.pretty_def)
        if flat978 is not None:
            assert flat978 is not None
            self.write(flat978)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1735 = _dollar_dollar.attrs
            else:
                _t1735 = None
            fields972 = (_dollar_dollar.name, _dollar_dollar.body, _t1735,)
            assert fields972 is not None
            unwrapped_fields973 = fields972
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field974 = unwrapped_fields973[0]
            self.pretty_relation_id(field974)
            self.newline()
            field975 = unwrapped_fields973[1]
            self.pretty_abstraction(field975)
            field976 = unwrapped_fields973[2]
            if field976 is not None:
                self.newline()
                assert field976 is not None
                opt_val977 = field976
                self.pretty_attrs(opt_val977)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat983 = self._try_flat(msg, self.pretty_relation_id)
        if flat983 is not None:
            assert flat983 is not None
            self.write(flat983)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1737 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1736 = _t1737
            else:
                _t1736 = None
            deconstruct_result981 = _t1736
            if deconstruct_result981 is not None:
                assert deconstruct_result981 is not None
                unwrapped982 = deconstruct_result981
                self.write(":")
                self.write(unwrapped982)
            else:
                _dollar_dollar = msg
                _t1738 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result979 = _t1738
                if deconstruct_result979 is not None:
                    assert deconstruct_result979 is not None
                    unwrapped980 = deconstruct_result979
                    self.write(self.format_uint128(unwrapped980))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat988 = self._try_flat(msg, self.pretty_abstraction)
        if flat988 is not None:
            assert flat988 is not None
            self.write(flat988)
            return None
        else:
            _dollar_dollar = msg
            _t1739 = self.deconstruct_bindings(_dollar_dollar)
            fields984 = (_t1739, _dollar_dollar.value,)
            assert fields984 is not None
            unwrapped_fields985 = fields984
            self.write("(")
            self.indent()
            field986 = unwrapped_fields985[0]
            self.pretty_bindings(field986)
            self.newline()
            field987 = unwrapped_fields985[1]
            self.pretty_formula(field987)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat996 = self._try_flat(msg, self.pretty_bindings)
        if flat996 is not None:
            assert flat996 is not None
            self.write(flat996)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1740 = _dollar_dollar[1]
            else:
                _t1740 = None
            fields989 = (_dollar_dollar[0], _t1740,)
            assert fields989 is not None
            unwrapped_fields990 = fields989
            self.write("[")
            self.indent()
            field991 = unwrapped_fields990[0]
            for i993, elem992 in enumerate(field991):
                if (i993 > 0):
                    self.newline()
                self.pretty_binding(elem992)
            field994 = unwrapped_fields990[1]
            if field994 is not None:
                self.newline()
                assert field994 is not None
                opt_val995 = field994
                self.pretty_value_bindings(opt_val995)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat1001 = self._try_flat(msg, self.pretty_binding)
        if flat1001 is not None:
            assert flat1001 is not None
            self.write(flat1001)
            return None
        else:
            _dollar_dollar = msg
            fields997 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields997 is not None
            unwrapped_fields998 = fields997
            field999 = unwrapped_fields998[0]
            self.write(field999)
            self.write("::")
            field1000 = unwrapped_fields998[1]
            self.pretty_type(field1000)

    def pretty_type(self, msg: logic_pb2.Type):
        flat1030 = self._try_flat(msg, self.pretty_type)
        if flat1030 is not None:
            assert flat1030 is not None
            self.write(flat1030)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1741 = _dollar_dollar.unspecified_type
            else:
                _t1741 = None
            deconstruct_result1028 = _t1741
            if deconstruct_result1028 is not None:
                assert deconstruct_result1028 is not None
                unwrapped1029 = deconstruct_result1028
                self.pretty_unspecified_type(unwrapped1029)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1742 = _dollar_dollar.string_type
                else:
                    _t1742 = None
                deconstruct_result1026 = _t1742
                if deconstruct_result1026 is not None:
                    assert deconstruct_result1026 is not None
                    unwrapped1027 = deconstruct_result1026
                    self.pretty_string_type(unwrapped1027)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1743 = _dollar_dollar.int_type
                    else:
                        _t1743 = None
                    deconstruct_result1024 = _t1743
                    if deconstruct_result1024 is not None:
                        assert deconstruct_result1024 is not None
                        unwrapped1025 = deconstruct_result1024
                        self.pretty_int_type(unwrapped1025)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1744 = _dollar_dollar.float_type
                        else:
                            _t1744 = None
                        deconstruct_result1022 = _t1744
                        if deconstruct_result1022 is not None:
                            assert deconstruct_result1022 is not None
                            unwrapped1023 = deconstruct_result1022
                            self.pretty_float_type(unwrapped1023)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1745 = _dollar_dollar.uint128_type
                            else:
                                _t1745 = None
                            deconstruct_result1020 = _t1745
                            if deconstruct_result1020 is not None:
                                assert deconstruct_result1020 is not None
                                unwrapped1021 = deconstruct_result1020
                                self.pretty_uint128_type(unwrapped1021)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1746 = _dollar_dollar.int128_type
                                else:
                                    _t1746 = None
                                deconstruct_result1018 = _t1746
                                if deconstruct_result1018 is not None:
                                    assert deconstruct_result1018 is not None
                                    unwrapped1019 = deconstruct_result1018
                                    self.pretty_int128_type(unwrapped1019)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1747 = _dollar_dollar.date_type
                                    else:
                                        _t1747 = None
                                    deconstruct_result1016 = _t1747
                                    if deconstruct_result1016 is not None:
                                        assert deconstruct_result1016 is not None
                                        unwrapped1017 = deconstruct_result1016
                                        self.pretty_date_type(unwrapped1017)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1748 = _dollar_dollar.datetime_type
                                        else:
                                            _t1748 = None
                                        deconstruct_result1014 = _t1748
                                        if deconstruct_result1014 is not None:
                                            assert deconstruct_result1014 is not None
                                            unwrapped1015 = deconstruct_result1014
                                            self.pretty_datetime_type(unwrapped1015)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1749 = _dollar_dollar.missing_type
                                            else:
                                                _t1749 = None
                                            deconstruct_result1012 = _t1749
                                            if deconstruct_result1012 is not None:
                                                assert deconstruct_result1012 is not None
                                                unwrapped1013 = deconstruct_result1012
                                                self.pretty_missing_type(unwrapped1013)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1750 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1750 = None
                                                deconstruct_result1010 = _t1750
                                                if deconstruct_result1010 is not None:
                                                    assert deconstruct_result1010 is not None
                                                    unwrapped1011 = deconstruct_result1010
                                                    self.pretty_decimal_type(unwrapped1011)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1751 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1751 = None
                                                    deconstruct_result1008 = _t1751
                                                    if deconstruct_result1008 is not None:
                                                        assert deconstruct_result1008 is not None
                                                        unwrapped1009 = deconstruct_result1008
                                                        self.pretty_boolean_type(unwrapped1009)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1752 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1752 = None
                                                        deconstruct_result1006 = _t1752
                                                        if deconstruct_result1006 is not None:
                                                            assert deconstruct_result1006 is not None
                                                            unwrapped1007 = deconstruct_result1006
                                                            self.pretty_int32_type(unwrapped1007)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1753 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1753 = None
                                                            deconstruct_result1004 = _t1753
                                                            if deconstruct_result1004 is not None:
                                                                assert deconstruct_result1004 is not None
                                                                unwrapped1005 = deconstruct_result1004
                                                                self.pretty_float32_type(unwrapped1005)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1754 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1754 = None
                                                                deconstruct_result1002 = _t1754
                                                                if deconstruct_result1002 is not None:
                                                                    assert deconstruct_result1002 is not None
                                                                    unwrapped1003 = deconstruct_result1002
                                                                    self.pretty_uint32_type(unwrapped1003)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields1031 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields1032 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields1033 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields1034 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields1035 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields1036 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields1037 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields1038 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields1039 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat1044 = self._try_flat(msg, self.pretty_decimal_type)
        if flat1044 is not None:
            assert flat1044 is not None
            self.write(flat1044)
            return None
        else:
            _dollar_dollar = msg
            fields1040 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields1040 is not None
            unwrapped_fields1041 = fields1040
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field1042 = unwrapped_fields1041[0]
            self.write(str(field1042))
            self.newline()
            field1043 = unwrapped_fields1041[1]
            self.write(str(field1043))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields1045 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields1046 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields1047 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields1048 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat1052 = self._try_flat(msg, self.pretty_value_bindings)
        if flat1052 is not None:
            assert flat1052 is not None
            self.write(flat1052)
            return None
        else:
            fields1049 = msg
            self.write("|")
            if not len(fields1049) == 0:
                self.write(" ")
                for i1051, elem1050 in enumerate(fields1049):
                    if (i1051 > 0):
                        self.newline()
                    self.pretty_binding(elem1050)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1079 = self._try_flat(msg, self.pretty_formula)
        if flat1079 is not None:
            assert flat1079 is not None
            self.write(flat1079)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1755 = _dollar_dollar.conjunction
            else:
                _t1755 = None
            deconstruct_result1077 = _t1755
            if deconstruct_result1077 is not None:
                assert deconstruct_result1077 is not None
                unwrapped1078 = deconstruct_result1077
                self.pretty_true(unwrapped1078)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1756 = _dollar_dollar.disjunction
                else:
                    _t1756 = None
                deconstruct_result1075 = _t1756
                if deconstruct_result1075 is not None:
                    assert deconstruct_result1075 is not None
                    unwrapped1076 = deconstruct_result1075
                    self.pretty_false(unwrapped1076)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1757 = _dollar_dollar.exists
                    else:
                        _t1757 = None
                    deconstruct_result1073 = _t1757
                    if deconstruct_result1073 is not None:
                        assert deconstruct_result1073 is not None
                        unwrapped1074 = deconstruct_result1073
                        self.pretty_exists(unwrapped1074)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1758 = _dollar_dollar.reduce
                        else:
                            _t1758 = None
                        deconstruct_result1071 = _t1758
                        if deconstruct_result1071 is not None:
                            assert deconstruct_result1071 is not None
                            unwrapped1072 = deconstruct_result1071
                            self.pretty_reduce(unwrapped1072)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1759 = _dollar_dollar.conjunction
                            else:
                                _t1759 = None
                            deconstruct_result1069 = _t1759
                            if deconstruct_result1069 is not None:
                                assert deconstruct_result1069 is not None
                                unwrapped1070 = deconstruct_result1069
                                self.pretty_conjunction(unwrapped1070)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1760 = _dollar_dollar.disjunction
                                else:
                                    _t1760 = None
                                deconstruct_result1067 = _t1760
                                if deconstruct_result1067 is not None:
                                    assert deconstruct_result1067 is not None
                                    unwrapped1068 = deconstruct_result1067
                                    self.pretty_disjunction(unwrapped1068)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1761 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1761 = None
                                    deconstruct_result1065 = _t1761
                                    if deconstruct_result1065 is not None:
                                        assert deconstruct_result1065 is not None
                                        unwrapped1066 = deconstruct_result1065
                                        self.pretty_not(unwrapped1066)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1762 = _dollar_dollar.ffi
                                        else:
                                            _t1762 = None
                                        deconstruct_result1063 = _t1762
                                        if deconstruct_result1063 is not None:
                                            assert deconstruct_result1063 is not None
                                            unwrapped1064 = deconstruct_result1063
                                            self.pretty_ffi(unwrapped1064)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1763 = _dollar_dollar.atom
                                            else:
                                                _t1763 = None
                                            deconstruct_result1061 = _t1763
                                            if deconstruct_result1061 is not None:
                                                assert deconstruct_result1061 is not None
                                                unwrapped1062 = deconstruct_result1061
                                                self.pretty_atom(unwrapped1062)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1764 = _dollar_dollar.pragma
                                                else:
                                                    _t1764 = None
                                                deconstruct_result1059 = _t1764
                                                if deconstruct_result1059 is not None:
                                                    assert deconstruct_result1059 is not None
                                                    unwrapped1060 = deconstruct_result1059
                                                    self.pretty_pragma(unwrapped1060)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1765 = _dollar_dollar.primitive
                                                    else:
                                                        _t1765 = None
                                                    deconstruct_result1057 = _t1765
                                                    if deconstruct_result1057 is not None:
                                                        assert deconstruct_result1057 is not None
                                                        unwrapped1058 = deconstruct_result1057
                                                        self.pretty_primitive(unwrapped1058)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1766 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1766 = None
                                                        deconstruct_result1055 = _t1766
                                                        if deconstruct_result1055 is not None:
                                                            assert deconstruct_result1055 is not None
                                                            unwrapped1056 = deconstruct_result1055
                                                            self.pretty_rel_atom(unwrapped1056)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1767 = _dollar_dollar.cast
                                                            else:
                                                                _t1767 = None
                                                            deconstruct_result1053 = _t1767
                                                            if deconstruct_result1053 is not None:
                                                                assert deconstruct_result1053 is not None
                                                                unwrapped1054 = deconstruct_result1053
                                                                self.pretty_cast(unwrapped1054)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields1080 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1081 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1086 = self._try_flat(msg, self.pretty_exists)
        if flat1086 is not None:
            assert flat1086 is not None
            self.write(flat1086)
            return None
        else:
            _dollar_dollar = msg
            _t1768 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1082 = (_t1768, _dollar_dollar.body.value,)
            assert fields1082 is not None
            unwrapped_fields1083 = fields1082
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1084 = unwrapped_fields1083[0]
            self.pretty_bindings(field1084)
            self.newline()
            field1085 = unwrapped_fields1083[1]
            self.pretty_formula(field1085)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1092 = self._try_flat(msg, self.pretty_reduce)
        if flat1092 is not None:
            assert flat1092 is not None
            self.write(flat1092)
            return None
        else:
            _dollar_dollar = msg
            fields1087 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1087 is not None
            unwrapped_fields1088 = fields1087
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1089 = unwrapped_fields1088[0]
            self.pretty_abstraction(field1089)
            self.newline()
            field1090 = unwrapped_fields1088[1]
            self.pretty_abstraction(field1090)
            self.newline()
            field1091 = unwrapped_fields1088[2]
            self.pretty_terms(field1091)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1096 = self._try_flat(msg, self.pretty_terms)
        if flat1096 is not None:
            assert flat1096 is not None
            self.write(flat1096)
            return None
        else:
            fields1093 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1093) == 0:
                self.newline()
                for i1095, elem1094 in enumerate(fields1093):
                    if (i1095 > 0):
                        self.newline()
                    self.pretty_term(elem1094)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1101 = self._try_flat(msg, self.pretty_term)
        if flat1101 is not None:
            assert flat1101 is not None
            self.write(flat1101)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1769 = _dollar_dollar.var
            else:
                _t1769 = None
            deconstruct_result1099 = _t1769
            if deconstruct_result1099 is not None:
                assert deconstruct_result1099 is not None
                unwrapped1100 = deconstruct_result1099
                self.pretty_var(unwrapped1100)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1770 = _dollar_dollar.constant
                else:
                    _t1770 = None
                deconstruct_result1097 = _t1770
                if deconstruct_result1097 is not None:
                    assert deconstruct_result1097 is not None
                    unwrapped1098 = deconstruct_result1097
                    self.pretty_value(unwrapped1098)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1104 = self._try_flat(msg, self.pretty_var)
        if flat1104 is not None:
            assert flat1104 is not None
            self.write(flat1104)
            return None
        else:
            _dollar_dollar = msg
            fields1102 = _dollar_dollar.name
            assert fields1102 is not None
            unwrapped_fields1103 = fields1102
            self.write(unwrapped_fields1103)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1130 = self._try_flat(msg, self.pretty_value)
        if flat1130 is not None:
            assert flat1130 is not None
            self.write(flat1130)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1771 = _dollar_dollar.date_value
            else:
                _t1771 = None
            deconstruct_result1128 = _t1771
            if deconstruct_result1128 is not None:
                assert deconstruct_result1128 is not None
                unwrapped1129 = deconstruct_result1128
                self.pretty_date(unwrapped1129)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1772 = _dollar_dollar.datetime_value
                else:
                    _t1772 = None
                deconstruct_result1126 = _t1772
                if deconstruct_result1126 is not None:
                    assert deconstruct_result1126 is not None
                    unwrapped1127 = deconstruct_result1126
                    self.pretty_datetime(unwrapped1127)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1773 = _dollar_dollar.string_value
                    else:
                        _t1773 = None
                    deconstruct_result1124 = _t1773
                    if deconstruct_result1124 is not None:
                        assert deconstruct_result1124 is not None
                        unwrapped1125 = deconstruct_result1124
                        self.write(self.format_string_value(unwrapped1125))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1774 = _dollar_dollar.int32_value
                        else:
                            _t1774 = None
                        deconstruct_result1122 = _t1774
                        if deconstruct_result1122 is not None:
                            assert deconstruct_result1122 is not None
                            unwrapped1123 = deconstruct_result1122
                            self.write((str(unwrapped1123) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1775 = _dollar_dollar.int_value
                            else:
                                _t1775 = None
                            deconstruct_result1120 = _t1775
                            if deconstruct_result1120 is not None:
                                assert deconstruct_result1120 is not None
                                unwrapped1121 = deconstruct_result1120
                                self.write(str(unwrapped1121))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1776 = _dollar_dollar.float32_value
                                else:
                                    _t1776 = None
                                deconstruct_result1118 = _t1776
                                if deconstruct_result1118 is not None:
                                    assert deconstruct_result1118 is not None
                                    unwrapped1119 = deconstruct_result1118
                                    self.write(self.format_float32_literal(unwrapped1119))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1777 = _dollar_dollar.float_value
                                    else:
                                        _t1777 = None
                                    deconstruct_result1116 = _t1777
                                    if deconstruct_result1116 is not None:
                                        assert deconstruct_result1116 is not None
                                        unwrapped1117 = deconstruct_result1116
                                        self.write(str(unwrapped1117))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1778 = _dollar_dollar.uint32_value
                                        else:
                                            _t1778 = None
                                        deconstruct_result1114 = _t1778
                                        if deconstruct_result1114 is not None:
                                            assert deconstruct_result1114 is not None
                                            unwrapped1115 = deconstruct_result1114
                                            self.write((str(unwrapped1115) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1779 = _dollar_dollar.uint128_value
                                            else:
                                                _t1779 = None
                                            deconstruct_result1112 = _t1779
                                            if deconstruct_result1112 is not None:
                                                assert deconstruct_result1112 is not None
                                                unwrapped1113 = deconstruct_result1112
                                                self.write(self.format_uint128(unwrapped1113))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1780 = _dollar_dollar.int128_value
                                                else:
                                                    _t1780 = None
                                                deconstruct_result1110 = _t1780
                                                if deconstruct_result1110 is not None:
                                                    assert deconstruct_result1110 is not None
                                                    unwrapped1111 = deconstruct_result1110
                                                    self.write(self.format_int128(unwrapped1111))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1781 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1781 = None
                                                    deconstruct_result1108 = _t1781
                                                    if deconstruct_result1108 is not None:
                                                        assert deconstruct_result1108 is not None
                                                        unwrapped1109 = deconstruct_result1108
                                                        self.write(self.format_decimal(unwrapped1109))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1782 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1782 = None
                                                        deconstruct_result1106 = _t1782
                                                        if deconstruct_result1106 is not None:
                                                            assert deconstruct_result1106 is not None
                                                            unwrapped1107 = deconstruct_result1106
                                                            self.pretty_boolean_value(unwrapped1107)
                                                        else:
                                                            fields1105 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1136 = self._try_flat(msg, self.pretty_date)
        if flat1136 is not None:
            assert flat1136 is not None
            self.write(flat1136)
            return None
        else:
            _dollar_dollar = msg
            fields1131 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1131 is not None
            unwrapped_fields1132 = fields1131
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1133 = unwrapped_fields1132[0]
            self.write(str(field1133))
            self.newline()
            field1134 = unwrapped_fields1132[1]
            self.write(str(field1134))
            self.newline()
            field1135 = unwrapped_fields1132[2]
            self.write(str(field1135))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1147 = self._try_flat(msg, self.pretty_datetime)
        if flat1147 is not None:
            assert flat1147 is not None
            self.write(flat1147)
            return None
        else:
            _dollar_dollar = msg
            fields1137 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1137 is not None
            unwrapped_fields1138 = fields1137
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1139 = unwrapped_fields1138[0]
            self.write(str(field1139))
            self.newline()
            field1140 = unwrapped_fields1138[1]
            self.write(str(field1140))
            self.newline()
            field1141 = unwrapped_fields1138[2]
            self.write(str(field1141))
            self.newline()
            field1142 = unwrapped_fields1138[3]
            self.write(str(field1142))
            self.newline()
            field1143 = unwrapped_fields1138[4]
            self.write(str(field1143))
            self.newline()
            field1144 = unwrapped_fields1138[5]
            self.write(str(field1144))
            field1145 = unwrapped_fields1138[6]
            if field1145 is not None:
                self.newline()
                assert field1145 is not None
                opt_val1146 = field1145
                self.write(str(opt_val1146))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1152 = self._try_flat(msg, self.pretty_conjunction)
        if flat1152 is not None:
            assert flat1152 is not None
            self.write(flat1152)
            return None
        else:
            _dollar_dollar = msg
            fields1148 = _dollar_dollar.args
            assert fields1148 is not None
            unwrapped_fields1149 = fields1148
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1149) == 0:
                self.newline()
                for i1151, elem1150 in enumerate(unwrapped_fields1149):
                    if (i1151 > 0):
                        self.newline()
                    self.pretty_formula(elem1150)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1157 = self._try_flat(msg, self.pretty_disjunction)
        if flat1157 is not None:
            assert flat1157 is not None
            self.write(flat1157)
            return None
        else:
            _dollar_dollar = msg
            fields1153 = _dollar_dollar.args
            assert fields1153 is not None
            unwrapped_fields1154 = fields1153
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1154) == 0:
                self.newline()
                for i1156, elem1155 in enumerate(unwrapped_fields1154):
                    if (i1156 > 0):
                        self.newline()
                    self.pretty_formula(elem1155)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1160 = self._try_flat(msg, self.pretty_not)
        if flat1160 is not None:
            assert flat1160 is not None
            self.write(flat1160)
            return None
        else:
            _dollar_dollar = msg
            fields1158 = _dollar_dollar.arg
            assert fields1158 is not None
            unwrapped_fields1159 = fields1158
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1159)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1166 = self._try_flat(msg, self.pretty_ffi)
        if flat1166 is not None:
            assert flat1166 is not None
            self.write(flat1166)
            return None
        else:
            _dollar_dollar = msg
            fields1161 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1161 is not None
            unwrapped_fields1162 = fields1161
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1163 = unwrapped_fields1162[0]
            self.pretty_name(field1163)
            self.newline()
            field1164 = unwrapped_fields1162[1]
            self.pretty_ffi_args(field1164)
            self.newline()
            field1165 = unwrapped_fields1162[2]
            self.pretty_terms(field1165)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1168 = self._try_flat(msg, self.pretty_name)
        if flat1168 is not None:
            assert flat1168 is not None
            self.write(flat1168)
            return None
        else:
            fields1167 = msg
            self.write(":")
            self.write(fields1167)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1172 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1172 is not None:
            assert flat1172 is not None
            self.write(flat1172)
            return None
        else:
            fields1169 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1169) == 0:
                self.newline()
                for i1171, elem1170 in enumerate(fields1169):
                    if (i1171 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1170)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1179 = self._try_flat(msg, self.pretty_atom)
        if flat1179 is not None:
            assert flat1179 is not None
            self.write(flat1179)
            return None
        else:
            _dollar_dollar = msg
            fields1173 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1173 is not None
            unwrapped_fields1174 = fields1173
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1175 = unwrapped_fields1174[0]
            self.pretty_relation_id(field1175)
            field1176 = unwrapped_fields1174[1]
            if not len(field1176) == 0:
                self.newline()
                for i1178, elem1177 in enumerate(field1176):
                    if (i1178 > 0):
                        self.newline()
                    self.pretty_term(elem1177)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1186 = self._try_flat(msg, self.pretty_pragma)
        if flat1186 is not None:
            assert flat1186 is not None
            self.write(flat1186)
            return None
        else:
            _dollar_dollar = msg
            fields1180 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1180 is not None
            unwrapped_fields1181 = fields1180
            self.write("(pragma")
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
                    self.pretty_term(elem1184)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1202 = self._try_flat(msg, self.pretty_primitive)
        if flat1202 is not None:
            assert flat1202 is not None
            self.write(flat1202)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1783 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1783 = None
            guard_result1201 = _t1783
            if guard_result1201 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1784 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1784 = None
                guard_result1200 = _t1784
                if guard_result1200 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1785 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1785 = None
                    guard_result1199 = _t1785
                    if guard_result1199 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1786 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1786 = None
                        guard_result1198 = _t1786
                        if guard_result1198 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1787 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1787 = None
                            guard_result1197 = _t1787
                            if guard_result1197 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1788 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1788 = None
                                guard_result1196 = _t1788
                                if guard_result1196 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1789 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1789 = None
                                    guard_result1195 = _t1789
                                    if guard_result1195 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1790 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1790 = None
                                        guard_result1194 = _t1790
                                        if guard_result1194 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1791 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1791 = None
                                            guard_result1193 = _t1791
                                            if guard_result1193 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1187 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1187 is not None
                                                unwrapped_fields1188 = fields1187
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1189 = unwrapped_fields1188[0]
                                                self.pretty_name(field1189)
                                                field1190 = unwrapped_fields1188[1]
                                                if not len(field1190) == 0:
                                                    self.newline()
                                                    for i1192, elem1191 in enumerate(field1190):
                                                        if (i1192 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1191)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1207 = self._try_flat(msg, self.pretty_eq)
        if flat1207 is not None:
            assert flat1207 is not None
            self.write(flat1207)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1792 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1792 = None
            fields1203 = _t1792
            assert fields1203 is not None
            unwrapped_fields1204 = fields1203
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1205 = unwrapped_fields1204[0]
            self.pretty_term(field1205)
            self.newline()
            field1206 = unwrapped_fields1204[1]
            self.pretty_term(field1206)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1212 = self._try_flat(msg, self.pretty_lt)
        if flat1212 is not None:
            assert flat1212 is not None
            self.write(flat1212)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1793 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1793 = None
            fields1208 = _t1793
            assert fields1208 is not None
            unwrapped_fields1209 = fields1208
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1210 = unwrapped_fields1209[0]
            self.pretty_term(field1210)
            self.newline()
            field1211 = unwrapped_fields1209[1]
            self.pretty_term(field1211)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1217 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1217 is not None:
            assert flat1217 is not None
            self.write(flat1217)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1794 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1794 = None
            fields1213 = _t1794
            assert fields1213 is not None
            unwrapped_fields1214 = fields1213
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1215 = unwrapped_fields1214[0]
            self.pretty_term(field1215)
            self.newline()
            field1216 = unwrapped_fields1214[1]
            self.pretty_term(field1216)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1222 = self._try_flat(msg, self.pretty_gt)
        if flat1222 is not None:
            assert flat1222 is not None
            self.write(flat1222)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1795 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1795 = None
            fields1218 = _t1795
            assert fields1218 is not None
            unwrapped_fields1219 = fields1218
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1220 = unwrapped_fields1219[0]
            self.pretty_term(field1220)
            self.newline()
            field1221 = unwrapped_fields1219[1]
            self.pretty_term(field1221)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1227 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1227 is not None:
            assert flat1227 is not None
            self.write(flat1227)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1796 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1796 = None
            fields1223 = _t1796
            assert fields1223 is not None
            unwrapped_fields1224 = fields1223
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1225 = unwrapped_fields1224[0]
            self.pretty_term(field1225)
            self.newline()
            field1226 = unwrapped_fields1224[1]
            self.pretty_term(field1226)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1233 = self._try_flat(msg, self.pretty_add)
        if flat1233 is not None:
            assert flat1233 is not None
            self.write(flat1233)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1797 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1797 = None
            fields1228 = _t1797
            assert fields1228 is not None
            unwrapped_fields1229 = fields1228
            self.write("(+")
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

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1239 = self._try_flat(msg, self.pretty_minus)
        if flat1239 is not None:
            assert flat1239 is not None
            self.write(flat1239)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1798 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1798 = None
            fields1234 = _t1798
            assert fields1234 is not None
            unwrapped_fields1235 = fields1234
            self.write("(-")
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

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1245 = self._try_flat(msg, self.pretty_multiply)
        if flat1245 is not None:
            assert flat1245 is not None
            self.write(flat1245)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1799 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1799 = None
            fields1240 = _t1799
            assert fields1240 is not None
            unwrapped_fields1241 = fields1240
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1242 = unwrapped_fields1241[0]
            self.pretty_term(field1242)
            self.newline()
            field1243 = unwrapped_fields1241[1]
            self.pretty_term(field1243)
            self.newline()
            field1244 = unwrapped_fields1241[2]
            self.pretty_term(field1244)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1251 = self._try_flat(msg, self.pretty_divide)
        if flat1251 is not None:
            assert flat1251 is not None
            self.write(flat1251)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1800 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1800 = None
            fields1246 = _t1800
            assert fields1246 is not None
            unwrapped_fields1247 = fields1246
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1248 = unwrapped_fields1247[0]
            self.pretty_term(field1248)
            self.newline()
            field1249 = unwrapped_fields1247[1]
            self.pretty_term(field1249)
            self.newline()
            field1250 = unwrapped_fields1247[2]
            self.pretty_term(field1250)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1256 = self._try_flat(msg, self.pretty_rel_term)
        if flat1256 is not None:
            assert flat1256 is not None
            self.write(flat1256)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1801 = _dollar_dollar.specialized_value
            else:
                _t1801 = None
            deconstruct_result1254 = _t1801
            if deconstruct_result1254 is not None:
                assert deconstruct_result1254 is not None
                unwrapped1255 = deconstruct_result1254
                self.pretty_specialized_value(unwrapped1255)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1802 = _dollar_dollar.term
                else:
                    _t1802 = None
                deconstruct_result1252 = _t1802
                if deconstruct_result1252 is not None:
                    assert deconstruct_result1252 is not None
                    unwrapped1253 = deconstruct_result1252
                    self.pretty_term(unwrapped1253)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1258 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1258 is not None:
            assert flat1258 is not None
            self.write(flat1258)
            return None
        else:
            fields1257 = msg
            self.write("#")
            self.pretty_raw_value(fields1257)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1265 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1265 is not None:
            assert flat1265 is not None
            self.write(flat1265)
            return None
        else:
            _dollar_dollar = msg
            fields1259 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1259 is not None
            unwrapped_fields1260 = fields1259
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1261 = unwrapped_fields1260[0]
            self.pretty_name(field1261)
            field1262 = unwrapped_fields1260[1]
            if not len(field1262) == 0:
                self.newline()
                for i1264, elem1263 in enumerate(field1262):
                    if (i1264 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1263)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1270 = self._try_flat(msg, self.pretty_cast)
        if flat1270 is not None:
            assert flat1270 is not None
            self.write(flat1270)
            return None
        else:
            _dollar_dollar = msg
            fields1266 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1266 is not None
            unwrapped_fields1267 = fields1266
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1268 = unwrapped_fields1267[0]
            self.pretty_term(field1268)
            self.newline()
            field1269 = unwrapped_fields1267[1]
            self.pretty_term(field1269)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1274 = self._try_flat(msg, self.pretty_attrs)
        if flat1274 is not None:
            assert flat1274 is not None
            self.write(flat1274)
            return None
        else:
            fields1271 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1271) == 0:
                self.newline()
                for i1273, elem1272 in enumerate(fields1271):
                    if (i1273 > 0):
                        self.newline()
                    self.pretty_attribute(elem1272)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1281 = self._try_flat(msg, self.pretty_attribute)
        if flat1281 is not None:
            assert flat1281 is not None
            self.write(flat1281)
            return None
        else:
            _dollar_dollar = msg
            fields1275 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1275 is not None
            unwrapped_fields1276 = fields1275
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1277 = unwrapped_fields1276[0]
            self.pretty_name(field1277)
            field1278 = unwrapped_fields1276[1]
            if not len(field1278) == 0:
                self.newline()
                for i1280, elem1279 in enumerate(field1278):
                    if (i1280 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1279)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1290 = self._try_flat(msg, self.pretty_algorithm)
        if flat1290 is not None:
            assert flat1290 is not None
            self.write(flat1290)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1803 = _dollar_dollar.attrs
            else:
                _t1803 = None
            fields1282 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body, _t1803,)
            assert fields1282 is not None
            unwrapped_fields1283 = fields1282
            self.write("(algorithm")
            self.indent_sexp()
            field1284 = unwrapped_fields1283[0]
            if not len(field1284) == 0:
                self.newline()
                for i1286, elem1285 in enumerate(field1284):
                    if (i1286 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1285)
            self.newline()
            field1287 = unwrapped_fields1283[1]
            self.pretty_script(field1287)
            field1288 = unwrapped_fields1283[2]
            if field1288 is not None:
                self.newline()
                assert field1288 is not None
                opt_val1289 = field1288
                self.pretty_attrs(opt_val1289)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1295 = self._try_flat(msg, self.pretty_script)
        if flat1295 is not None:
            assert flat1295 is not None
            self.write(flat1295)
            return None
        else:
            _dollar_dollar = msg
            fields1291 = _dollar_dollar.constructs
            assert fields1291 is not None
            unwrapped_fields1292 = fields1291
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1292) == 0:
                self.newline()
                for i1294, elem1293 in enumerate(unwrapped_fields1292):
                    if (i1294 > 0):
                        self.newline()
                    self.pretty_construct(elem1293)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1300 = self._try_flat(msg, self.pretty_construct)
        if flat1300 is not None:
            assert flat1300 is not None
            self.write(flat1300)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1804 = _dollar_dollar.loop
            else:
                _t1804 = None
            deconstruct_result1298 = _t1804
            if deconstruct_result1298 is not None:
                assert deconstruct_result1298 is not None
                unwrapped1299 = deconstruct_result1298
                self.pretty_loop(unwrapped1299)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1805 = _dollar_dollar.instruction
                else:
                    _t1805 = None
                deconstruct_result1296 = _t1805
                if deconstruct_result1296 is not None:
                    assert deconstruct_result1296 is not None
                    unwrapped1297 = deconstruct_result1296
                    self.pretty_instruction(unwrapped1297)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1307 = self._try_flat(msg, self.pretty_loop)
        if flat1307 is not None:
            assert flat1307 is not None
            self.write(flat1307)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1806 = _dollar_dollar.attrs
            else:
                _t1806 = None
            fields1301 = (_dollar_dollar.init, _dollar_dollar.body, _t1806,)
            assert fields1301 is not None
            unwrapped_fields1302 = fields1301
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1303 = unwrapped_fields1302[0]
            self.pretty_init(field1303)
            self.newline()
            field1304 = unwrapped_fields1302[1]
            self.pretty_script(field1304)
            field1305 = unwrapped_fields1302[2]
            if field1305 is not None:
                self.newline()
                assert field1305 is not None
                opt_val1306 = field1305
                self.pretty_attrs(opt_val1306)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1311 = self._try_flat(msg, self.pretty_init)
        if flat1311 is not None:
            assert flat1311 is not None
            self.write(flat1311)
            return None
        else:
            fields1308 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1308) == 0:
                self.newline()
                for i1310, elem1309 in enumerate(fields1308):
                    if (i1310 > 0):
                        self.newline()
                    self.pretty_instruction(elem1309)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1322 = self._try_flat(msg, self.pretty_instruction)
        if flat1322 is not None:
            assert flat1322 is not None
            self.write(flat1322)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1807 = _dollar_dollar.assign
            else:
                _t1807 = None
            deconstruct_result1320 = _t1807
            if deconstruct_result1320 is not None:
                assert deconstruct_result1320 is not None
                unwrapped1321 = deconstruct_result1320
                self.pretty_assign(unwrapped1321)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1808 = _dollar_dollar.upsert
                else:
                    _t1808 = None
                deconstruct_result1318 = _t1808
                if deconstruct_result1318 is not None:
                    assert deconstruct_result1318 is not None
                    unwrapped1319 = deconstruct_result1318
                    self.pretty_upsert(unwrapped1319)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1809 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1809 = None
                    deconstruct_result1316 = _t1809
                    if deconstruct_result1316 is not None:
                        assert deconstruct_result1316 is not None
                        unwrapped1317 = deconstruct_result1316
                        self.pretty_break(unwrapped1317)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1810 = _dollar_dollar.monoid_def
                        else:
                            _t1810 = None
                        deconstruct_result1314 = _t1810
                        if deconstruct_result1314 is not None:
                            assert deconstruct_result1314 is not None
                            unwrapped1315 = deconstruct_result1314
                            self.pretty_monoid_def(unwrapped1315)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1811 = _dollar_dollar.monus_def
                            else:
                                _t1811 = None
                            deconstruct_result1312 = _t1811
                            if deconstruct_result1312 is not None:
                                assert deconstruct_result1312 is not None
                                unwrapped1313 = deconstruct_result1312
                                self.pretty_monus_def(unwrapped1313)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1329 = self._try_flat(msg, self.pretty_assign)
        if flat1329 is not None:
            assert flat1329 is not None
            self.write(flat1329)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1812 = _dollar_dollar.attrs
            else:
                _t1812 = None
            fields1323 = (_dollar_dollar.name, _dollar_dollar.body, _t1812,)
            assert fields1323 is not None
            unwrapped_fields1324 = fields1323
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1325 = unwrapped_fields1324[0]
            self.pretty_relation_id(field1325)
            self.newline()
            field1326 = unwrapped_fields1324[1]
            self.pretty_abstraction(field1326)
            field1327 = unwrapped_fields1324[2]
            if field1327 is not None:
                self.newline()
                assert field1327 is not None
                opt_val1328 = field1327
                self.pretty_attrs(opt_val1328)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1336 = self._try_flat(msg, self.pretty_upsert)
        if flat1336 is not None:
            assert flat1336 is not None
            self.write(flat1336)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1813 = _dollar_dollar.attrs
            else:
                _t1813 = None
            fields1330 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1813,)
            assert fields1330 is not None
            unwrapped_fields1331 = fields1330
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1332 = unwrapped_fields1331[0]
            self.pretty_relation_id(field1332)
            self.newline()
            field1333 = unwrapped_fields1331[1]
            self.pretty_abstraction_with_arity(field1333)
            field1334 = unwrapped_fields1331[2]
            if field1334 is not None:
                self.newline()
                assert field1334 is not None
                opt_val1335 = field1334
                self.pretty_attrs(opt_val1335)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1341 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1341 is not None:
            assert flat1341 is not None
            self.write(flat1341)
            return None
        else:
            _dollar_dollar = msg
            _t1814 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1337 = (_t1814, _dollar_dollar[0].value,)
            assert fields1337 is not None
            unwrapped_fields1338 = fields1337
            self.write("(")
            self.indent()
            field1339 = unwrapped_fields1338[0]
            self.pretty_bindings(field1339)
            self.newline()
            field1340 = unwrapped_fields1338[1]
            self.pretty_formula(field1340)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1348 = self._try_flat(msg, self.pretty_break)
        if flat1348 is not None:
            assert flat1348 is not None
            self.write(flat1348)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1815 = _dollar_dollar.attrs
            else:
                _t1815 = None
            fields1342 = (_dollar_dollar.name, _dollar_dollar.body, _t1815,)
            assert fields1342 is not None
            unwrapped_fields1343 = fields1342
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1344 = unwrapped_fields1343[0]
            self.pretty_relation_id(field1344)
            self.newline()
            field1345 = unwrapped_fields1343[1]
            self.pretty_abstraction(field1345)
            field1346 = unwrapped_fields1343[2]
            if field1346 is not None:
                self.newline()
                assert field1346 is not None
                opt_val1347 = field1346
                self.pretty_attrs(opt_val1347)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1356 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1356 is not None:
            assert flat1356 is not None
            self.write(flat1356)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1816 = _dollar_dollar.attrs
            else:
                _t1816 = None
            fields1349 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1816,)
            assert fields1349 is not None
            unwrapped_fields1350 = fields1349
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1351 = unwrapped_fields1350[0]
            self.pretty_monoid(field1351)
            self.newline()
            field1352 = unwrapped_fields1350[1]
            self.pretty_relation_id(field1352)
            self.newline()
            field1353 = unwrapped_fields1350[2]
            self.pretty_abstraction_with_arity(field1353)
            field1354 = unwrapped_fields1350[3]
            if field1354 is not None:
                self.newline()
                assert field1354 is not None
                opt_val1355 = field1354
                self.pretty_attrs(opt_val1355)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1365 = self._try_flat(msg, self.pretty_monoid)
        if flat1365 is not None:
            assert flat1365 is not None
            self.write(flat1365)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1817 = _dollar_dollar.or_monoid
            else:
                _t1817 = None
            deconstruct_result1363 = _t1817
            if deconstruct_result1363 is not None:
                assert deconstruct_result1363 is not None
                unwrapped1364 = deconstruct_result1363
                self.pretty_or_monoid(unwrapped1364)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1818 = _dollar_dollar.min_monoid
                else:
                    _t1818 = None
                deconstruct_result1361 = _t1818
                if deconstruct_result1361 is not None:
                    assert deconstruct_result1361 is not None
                    unwrapped1362 = deconstruct_result1361
                    self.pretty_min_monoid(unwrapped1362)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1819 = _dollar_dollar.max_monoid
                    else:
                        _t1819 = None
                    deconstruct_result1359 = _t1819
                    if deconstruct_result1359 is not None:
                        assert deconstruct_result1359 is not None
                        unwrapped1360 = deconstruct_result1359
                        self.pretty_max_monoid(unwrapped1360)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1820 = _dollar_dollar.sum_monoid
                        else:
                            _t1820 = None
                        deconstruct_result1357 = _t1820
                        if deconstruct_result1357 is not None:
                            assert deconstruct_result1357 is not None
                            unwrapped1358 = deconstruct_result1357
                            self.pretty_sum_monoid(unwrapped1358)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1366 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1369 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1369 is not None:
            assert flat1369 is not None
            self.write(flat1369)
            return None
        else:
            _dollar_dollar = msg
            fields1367 = _dollar_dollar.type
            assert fields1367 is not None
            unwrapped_fields1368 = fields1367
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1368)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1372 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1372 is not None:
            assert flat1372 is not None
            self.write(flat1372)
            return None
        else:
            _dollar_dollar = msg
            fields1370 = _dollar_dollar.type
            assert fields1370 is not None
            unwrapped_fields1371 = fields1370
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1371)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1375 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1375 is not None:
            assert flat1375 is not None
            self.write(flat1375)
            return None
        else:
            _dollar_dollar = msg
            fields1373 = _dollar_dollar.type
            assert fields1373 is not None
            unwrapped_fields1374 = fields1373
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1374)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1383 = self._try_flat(msg, self.pretty_monus_def)
        if flat1383 is not None:
            assert flat1383 is not None
            self.write(flat1383)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1821 = _dollar_dollar.attrs
            else:
                _t1821 = None
            fields1376 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1821,)
            assert fields1376 is not None
            unwrapped_fields1377 = fields1376
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1378 = unwrapped_fields1377[0]
            self.pretty_monoid(field1378)
            self.newline()
            field1379 = unwrapped_fields1377[1]
            self.pretty_relation_id(field1379)
            self.newline()
            field1380 = unwrapped_fields1377[2]
            self.pretty_abstraction_with_arity(field1380)
            field1381 = unwrapped_fields1377[3]
            if field1381 is not None:
                self.newline()
                assert field1381 is not None
                opt_val1382 = field1381
                self.pretty_attrs(opt_val1382)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1390 = self._try_flat(msg, self.pretty_constraint)
        if flat1390 is not None:
            assert flat1390 is not None
            self.write(flat1390)
            return None
        else:
            _dollar_dollar = msg
            fields1384 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1384 is not None
            unwrapped_fields1385 = fields1384
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1386 = unwrapped_fields1385[0]
            self.pretty_relation_id(field1386)
            self.newline()
            field1387 = unwrapped_fields1385[1]
            self.pretty_abstraction(field1387)
            self.newline()
            field1388 = unwrapped_fields1385[2]
            self.pretty_functional_dependency_keys(field1388)
            self.newline()
            field1389 = unwrapped_fields1385[3]
            self.pretty_functional_dependency_values(field1389)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1394 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1394 is not None:
            assert flat1394 is not None
            self.write(flat1394)
            return None
        else:
            fields1391 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1391) == 0:
                self.newline()
                for i1393, elem1392 in enumerate(fields1391):
                    if (i1393 > 0):
                        self.newline()
                    self.pretty_var(elem1392)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1398 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1398 is not None:
            assert flat1398 is not None
            self.write(flat1398)
            return None
        else:
            fields1395 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1395) == 0:
                self.newline()
                for i1397, elem1396 in enumerate(fields1395):
                    if (i1397 > 0):
                        self.newline()
                    self.pretty_var(elem1396)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1407 = self._try_flat(msg, self.pretty_data)
        if flat1407 is not None:
            assert flat1407 is not None
            self.write(flat1407)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1822 = _dollar_dollar.edb
            else:
                _t1822 = None
            deconstruct_result1405 = _t1822
            if deconstruct_result1405 is not None:
                assert deconstruct_result1405 is not None
                unwrapped1406 = deconstruct_result1405
                self.pretty_edb(unwrapped1406)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1823 = _dollar_dollar.betree_relation
                else:
                    _t1823 = None
                deconstruct_result1403 = _t1823
                if deconstruct_result1403 is not None:
                    assert deconstruct_result1403 is not None
                    unwrapped1404 = deconstruct_result1403
                    self.pretty_betree_relation(unwrapped1404)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1824 = _dollar_dollar.csv_data
                    else:
                        _t1824 = None
                    deconstruct_result1401 = _t1824
                    if deconstruct_result1401 is not None:
                        assert deconstruct_result1401 is not None
                        unwrapped1402 = deconstruct_result1401
                        self.pretty_csv_data(unwrapped1402)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1825 = _dollar_dollar.iceberg_data
                        else:
                            _t1825 = None
                        deconstruct_result1399 = _t1825
                        if deconstruct_result1399 is not None:
                            assert deconstruct_result1399 is not None
                            unwrapped1400 = deconstruct_result1399
                            self.pretty_iceberg_data(unwrapped1400)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1413 = self._try_flat(msg, self.pretty_edb)
        if flat1413 is not None:
            assert flat1413 is not None
            self.write(flat1413)
            return None
        else:
            _dollar_dollar = msg
            fields1408 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1408 is not None
            unwrapped_fields1409 = fields1408
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1410 = unwrapped_fields1409[0]
            self.pretty_relation_id(field1410)
            self.newline()
            field1411 = unwrapped_fields1409[1]
            self.pretty_edb_path(field1411)
            self.newline()
            field1412 = unwrapped_fields1409[2]
            self.pretty_edb_types(field1412)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1417 = self._try_flat(msg, self.pretty_edb_path)
        if flat1417 is not None:
            assert flat1417 is not None
            self.write(flat1417)
            return None
        else:
            fields1414 = msg
            self.write("[")
            self.indent()
            for i1416, elem1415 in enumerate(fields1414):
                if (i1416 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1415))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1421 = self._try_flat(msg, self.pretty_edb_types)
        if flat1421 is not None:
            assert flat1421 is not None
            self.write(flat1421)
            return None
        else:
            fields1418 = msg
            self.write("[")
            self.indent()
            for i1420, elem1419 in enumerate(fields1418):
                if (i1420 > 0):
                    self.newline()
                self.pretty_type(elem1419)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1426 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1426 is not None:
            assert flat1426 is not None
            self.write(flat1426)
            return None
        else:
            _dollar_dollar = msg
            fields1422 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1422 is not None
            unwrapped_fields1423 = fields1422
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1424 = unwrapped_fields1423[0]
            self.pretty_relation_id(field1424)
            self.newline()
            field1425 = unwrapped_fields1423[1]
            self.pretty_betree_info(field1425)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1432 = self._try_flat(msg, self.pretty_betree_info)
        if flat1432 is not None:
            assert flat1432 is not None
            self.write(flat1432)
            return None
        else:
            _dollar_dollar = msg
            _t1826 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1427 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1826,)
            assert fields1427 is not None
            unwrapped_fields1428 = fields1427
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1429 = unwrapped_fields1428[0]
            self.pretty_betree_info_key_types(field1429)
            self.newline()
            field1430 = unwrapped_fields1428[1]
            self.pretty_betree_info_value_types(field1430)
            self.newline()
            field1431 = unwrapped_fields1428[2]
            self.pretty_config_dict(field1431)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1436 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1436 is not None:
            assert flat1436 is not None
            self.write(flat1436)
            return None
        else:
            fields1433 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1433) == 0:
                self.newline()
                for i1435, elem1434 in enumerate(fields1433):
                    if (i1435 > 0):
                        self.newline()
                    self.pretty_type(elem1434)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1440 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1440 is not None:
            assert flat1440 is not None
            self.write(flat1440)
            return None
        else:
            fields1437 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1437) == 0:
                self.newline()
                for i1439, elem1438 in enumerate(fields1437):
                    if (i1439 > 0):
                        self.newline()
                    self.pretty_type(elem1438)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1450 = self._try_flat(msg, self.pretty_csv_data)
        if flat1450 is not None:
            assert flat1450 is not None
            self.write(flat1450)
            return None
        else:
            _dollar_dollar = msg
            _t1827 = self.deconstruct_csv_data_columns_optional(_dollar_dollar)
            _t1828 = self.deconstruct_csv_data_relations_optional(_dollar_dollar)
            fields1441 = (_dollar_dollar.locator, _dollar_dollar.config, _t1827, _t1828, _dollar_dollar.asof,)
            assert fields1441 is not None
            unwrapped_fields1442 = fields1441
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1443 = unwrapped_fields1442[0]
            self.pretty_csvlocator(field1443)
            self.newline()
            field1444 = unwrapped_fields1442[1]
            self.pretty_csv_config(field1444)
            field1445 = unwrapped_fields1442[2]
            if field1445 is not None:
                self.newline()
                assert field1445 is not None
                opt_val1446 = field1445
                self.pretty_gnf_columns(opt_val1446)
            field1447 = unwrapped_fields1442[3]
            if field1447 is not None:
                self.newline()
                assert field1447 is not None
                opt_val1448 = field1447
                self.pretty_target_relations(opt_val1448)
            self.newline()
            field1449 = unwrapped_fields1442[4]
            self.pretty_csv_asof(field1449)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1457 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1457 is not None:
            assert flat1457 is not None
            self.write(flat1457)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1829 = _dollar_dollar.paths
            else:
                _t1829 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1830 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1830 = None
            fields1451 = (_t1829, _t1830,)
            assert fields1451 is not None
            unwrapped_fields1452 = fields1451
            self.write("(csv_locator")
            self.indent_sexp()
            field1453 = unwrapped_fields1452[0]
            if field1453 is not None:
                self.newline()
                assert field1453 is not None
                opt_val1454 = field1453
                self.pretty_csv_locator_paths(opt_val1454)
            field1455 = unwrapped_fields1452[1]
            if field1455 is not None:
                self.newline()
                assert field1455 is not None
                opt_val1456 = field1455
                self.pretty_csv_locator_inline_data(opt_val1456)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1461 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1461 is not None:
            assert flat1461 is not None
            self.write(flat1461)
            return None
        else:
            fields1458 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1458) == 0:
                self.newline()
                for i1460, elem1459 in enumerate(fields1458):
                    if (i1460 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1459))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1463 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1463 is not None:
            assert flat1463 is not None
            self.write(flat1463)
            return None
        else:
            fields1462 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1462))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1469 = self._try_flat(msg, self.pretty_csv_config)
        if flat1469 is not None:
            assert flat1469 is not None
            self.write(flat1469)
            return None
        else:
            _dollar_dollar = msg
            _t1831 = self.deconstruct_csv_config(_dollar_dollar)
            _t1832 = self.deconstruct_csv_storage_integration_optional(_dollar_dollar)
            fields1464 = (_t1831, _t1832,)
            assert fields1464 is not None
            unwrapped_fields1465 = fields1464
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            field1466 = unwrapped_fields1465[0]
            self.pretty_config_dict(field1466)
            field1467 = unwrapped_fields1465[1]
            if field1467 is not None:
                self.newline()
                assert field1467 is not None
                opt_val1468 = field1467
                self.pretty__storage_integration(opt_val1468)
            self.dedent()
            self.write(")")

    def pretty__storage_integration(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat1471 = self._try_flat(msg, self.pretty__storage_integration)
        if flat1471 is not None:
            assert flat1471 is not None
            self.write(flat1471)
            return None
        else:
            fields1470 = msg
            self.write("(storage_integration")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(fields1470)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1475 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1475 is not None:
            assert flat1475 is not None
            self.write(flat1475)
            return None
        else:
            fields1472 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1472) == 0:
                self.newline()
                for i1474, elem1473 in enumerate(fields1472):
                    if (i1474 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1473)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1484 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1484 is not None:
            assert flat1484 is not None
            self.write(flat1484)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1833 = _dollar_dollar.target_id
            else:
                _t1833 = None
            fields1476 = (_dollar_dollar.column_path, _t1833, _dollar_dollar.types,)
            assert fields1476 is not None
            unwrapped_fields1477 = fields1476
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1478 = unwrapped_fields1477[0]
            self.pretty_gnf_column_path(field1478)
            field1479 = unwrapped_fields1477[1]
            if field1479 is not None:
                self.newline()
                assert field1479 is not None
                opt_val1480 = field1479
                self.pretty_relation_id(opt_val1480)
            self.newline()
            self.write("[")
            field1481 = unwrapped_fields1477[2]
            for i1483, elem1482 in enumerate(field1481):
                if (i1483 > 0):
                    self.newline()
                self.pretty_type(elem1482)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1491 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1491 is not None:
            assert flat1491 is not None
            self.write(flat1491)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1834 = _dollar_dollar[0]
            else:
                _t1834 = None
            deconstruct_result1489 = _t1834
            if deconstruct_result1489 is not None:
                assert deconstruct_result1489 is not None
                unwrapped1490 = deconstruct_result1489
                self.write(self.format_string_value(unwrapped1490))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1835 = _dollar_dollar
                else:
                    _t1835 = None
                deconstruct_result1485 = _t1835
                if deconstruct_result1485 is not None:
                    assert deconstruct_result1485 is not None
                    unwrapped1486 = deconstruct_result1485
                    self.write("[")
                    self.indent()
                    for i1488, elem1487 in enumerate(unwrapped1486):
                        if (i1488 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1487))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_target_relations(self, msg: logic_pb2.TargetRelations):
        flat1498 = self._try_flat(msg, self.pretty_target_relations)
        if flat1498 is not None:
            assert flat1498 is not None
            self.write(flat1498)
            return None
        else:
            _dollar_dollar = msg
            _t1836 = self.deconstruct_relation_keys(_dollar_dollar)
            _t1837 = self.deconstruct_load_errors_optional(_dollar_dollar)
            fields1492 = (_t1836, _dollar_dollar, _t1837,)
            assert fields1492 is not None
            unwrapped_fields1493 = fields1492
            self.write("(relations")
            self.indent_sexp()
            self.newline()
            field1494 = unwrapped_fields1493[0]
            self.pretty_relation_keys(field1494)
            self.newline()
            field1495 = unwrapped_fields1493[1]
            self.pretty_relation_body(field1495)
            field1496 = unwrapped_fields1493[2]
            if field1496 is not None:
                self.newline()
                assert field1496 is not None
                opt_val1497 = field1496
                self.pretty_load_errors(opt_val1497)
            self.dedent()
            self.write(")")

    def pretty_relation_keys(self, msg: tuple[Sequence[logic_pb2.NamedColumn], bool]):
        flat1505 = self._try_flat(msg, self.pretty_relation_keys)
        if flat1505 is not None:
            assert flat1505 is not None
            self.write(flat1505)
            return None
        else:
            _dollar_dollar = msg
            if not _dollar_dollar[1]:
                _t1838 = _dollar_dollar[0]
            else:
                _t1838 = None
            deconstruct_result1501 = _t1838
            if deconstruct_result1501 is not None:
                assert deconstruct_result1501 is not None
                unwrapped1502 = deconstruct_result1501
                self.write("(keys")
                self.indent_sexp()
                if not len(unwrapped1502) == 0:
                    self.newline()
                    for i1504, elem1503 in enumerate(unwrapped1502):
                        if (i1504 > 0):
                            self.newline()
                        self.pretty_named_column(elem1503)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar[1]:
                    _t1839 = ()
                else:
                    _t1839 = None
                deconstruct_result1499 = _t1839
                if deconstruct_result1499 is not None:
                    assert deconstruct_result1499 is not None
                    unwrapped1500 = deconstruct_result1499
                    self.write("(keys")
                    self.newline()
                    self.write("synthetic)")
                else:
                    raise ParseError("No matching rule for relation_keys")

    def pretty_named_column(self, msg: logic_pb2.NamedColumn):
        flat1510 = self._try_flat(msg, self.pretty_named_column)
        if flat1510 is not None:
            assert flat1510 is not None
            self.write(flat1510)
            return None
        else:
            _dollar_dollar = msg
            fields1506 = (_dollar_dollar.name, _dollar_dollar.type,)
            assert fields1506 is not None
            unwrapped_fields1507 = fields1506
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1508 = unwrapped_fields1507[0]
            self.write(self.format_string_value(field1508))
            self.newline()
            field1509 = unwrapped_fields1507[1]
            self.pretty_type(field1509)
            self.dedent()
            self.write(")")

    def pretty_relation_body(self, msg: logic_pb2.TargetRelations):
        flat1517 = self._try_flat(msg, self.pretty_relation_body)
        if flat1517 is not None:
            assert flat1517 is not None
            self.write(flat1517)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("plain"):
                _t1840 = _dollar_dollar.plain.targets
            else:
                _t1840 = None
            deconstruct_result1515 = _t1840
            if deconstruct_result1515 is not None:
                assert deconstruct_result1515 is not None
                unwrapped1516 = deconstruct_result1515
                self.pretty_non_cdc_relations(unwrapped1516)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("cdc"):
                    _t1841 = (_dollar_dollar.cdc.inserts, _dollar_dollar.cdc.deletes,)
                else:
                    _t1841 = None
                deconstruct_result1511 = _t1841
                if deconstruct_result1511 is not None:
                    assert deconstruct_result1511 is not None
                    unwrapped1512 = deconstruct_result1511
                    field1513 = unwrapped1512[0]
                    self.pretty_cdc_inserts(field1513)
                    self.write(" ")
                    field1514 = unwrapped1512[1]
                    self.pretty_cdc_deletes(field1514)
                else:
                    raise ParseError("No matching rule for relation_body")

    def pretty_non_cdc_relations(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1521 = self._try_flat(msg, self.pretty_non_cdc_relations)
        if flat1521 is not None:
            assert flat1521 is not None
            self.write(flat1521)
            return None
        else:
            fields1518 = msg
            for i1520, elem1519 in enumerate(fields1518):
                if (i1520 > 0):
                    self.newline()
                self.pretty_target_relation(elem1519)

    def pretty_target_relation(self, msg: logic_pb2.TargetRelation):
        flat1528 = self._try_flat(msg, self.pretty_target_relation)
        if flat1528 is not None:
            assert flat1528 is not None
            self.write(flat1528)
            return None
        else:
            _dollar_dollar = msg
            fields1522 = (_dollar_dollar.target_id, _dollar_dollar.values,)
            assert fields1522 is not None
            unwrapped_fields1523 = fields1522
            self.write("(relation")
            self.indent_sexp()
            self.newline()
            field1524 = unwrapped_fields1523[0]
            self.pretty_relation_id(field1524)
            field1525 = unwrapped_fields1523[1]
            if not len(field1525) == 0:
                self.newline()
                for i1527, elem1526 in enumerate(field1525):
                    if (i1527 > 0):
                        self.newline()
                    self.pretty_named_column(elem1526)
            self.dedent()
            self.write(")")

    def pretty_cdc_inserts(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1532 = self._try_flat(msg, self.pretty_cdc_inserts)
        if flat1532 is not None:
            assert flat1532 is not None
            self.write(flat1532)
            return None
        else:
            fields1529 = msg
            self.write("(inserts")
            self.indent_sexp()
            if not len(fields1529) == 0:
                self.newline()
                for i1531, elem1530 in enumerate(fields1529):
                    if (i1531 > 0):
                        self.newline()
                    self.pretty_target_relation(elem1530)
            self.dedent()
            self.write(")")

    def pretty_cdc_deletes(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1536 = self._try_flat(msg, self.pretty_cdc_deletes)
        if flat1536 is not None:
            assert flat1536 is not None
            self.write(flat1536)
            return None
        else:
            fields1533 = msg
            self.write("(deletes")
            self.indent_sexp()
            if not len(fields1533) == 0:
                self.newline()
                for i1535, elem1534 in enumerate(fields1533):
                    if (i1535 > 0):
                        self.newline()
                    self.pretty_target_relation(elem1534)
            self.dedent()
            self.write(")")

    def pretty_load_errors(self, msg: logic_pb2.RelationId):
        flat1538 = self._try_flat(msg, self.pretty_load_errors)
        if flat1538 is not None:
            assert flat1538 is not None
            self.write(flat1538)
            return None
        else:
            fields1537 = msg
            self.write("(load_errors")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1537)
            self.dedent()
            self.write(")")

    def pretty_csv_asof(self, msg: str):
        flat1540 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1540 is not None:
            assert flat1540 is not None
            self.write(flat1540)
            return None
        else:
            fields1539 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1539))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1551 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1551 is not None:
            assert flat1551 is not None
            self.write(flat1551)
            return None
        else:
            _dollar_dollar = msg
            _t1842 = self.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
            _t1843 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1541 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1842, _t1843, _dollar_dollar.returns_delta,)
            assert fields1541 is not None
            unwrapped_fields1542 = fields1541
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1543 = unwrapped_fields1542[0]
            self.pretty_iceberg_locator(field1543)
            self.newline()
            field1544 = unwrapped_fields1542[1]
            self.pretty_iceberg_catalog_config(field1544)
            self.newline()
            field1545 = unwrapped_fields1542[2]
            self.pretty_gnf_columns(field1545)
            field1546 = unwrapped_fields1542[3]
            if field1546 is not None:
                self.newline()
                assert field1546 is not None
                opt_val1547 = field1546
                self.pretty_iceberg_from_snapshot(opt_val1547)
            field1548 = unwrapped_fields1542[4]
            if field1548 is not None:
                self.newline()
                assert field1548 is not None
                opt_val1549 = field1548
                self.pretty_iceberg_to_snapshot(opt_val1549)
            self.newline()
            field1550 = unwrapped_fields1542[5]
            self.pretty_boolean_value(field1550)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1557 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1557 is not None:
            assert flat1557 is not None
            self.write(flat1557)
            return None
        else:
            _dollar_dollar = msg
            fields1552 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1552 is not None
            unwrapped_fields1553 = fields1552
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            field1554 = unwrapped_fields1553[0]
            self.pretty_iceberg_locator_table_name(field1554)
            self.newline()
            field1555 = unwrapped_fields1553[1]
            self.pretty_iceberg_locator_namespace(field1555)
            self.newline()
            field1556 = unwrapped_fields1553[2]
            self.pretty_iceberg_locator_warehouse(field1556)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_table_name(self, msg: str):
        flat1559 = self._try_flat(msg, self.pretty_iceberg_locator_table_name)
        if flat1559 is not None:
            assert flat1559 is not None
            self.write(flat1559)
            return None
        else:
            fields1558 = msg
            self.write("(table_name")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1558))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_namespace(self, msg: Sequence[str]):
        flat1563 = self._try_flat(msg, self.pretty_iceberg_locator_namespace)
        if flat1563 is not None:
            assert flat1563 is not None
            self.write(flat1563)
            return None
        else:
            fields1560 = msg
            self.write("(namespace")
            self.indent_sexp()
            if not len(fields1560) == 0:
                self.newline()
                for i1562, elem1561 in enumerate(fields1560):
                    if (i1562 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1561))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_warehouse(self, msg: str):
        flat1565 = self._try_flat(msg, self.pretty_iceberg_locator_warehouse)
        if flat1565 is not None:
            assert flat1565 is not None
            self.write(flat1565)
            return None
        else:
            fields1564 = msg
            self.write("(warehouse")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1564))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1573 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1573 is not None:
            assert flat1573 is not None
            self.write(flat1573)
            return None
        else:
            _dollar_dollar = msg
            _t1844 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1566 = (_dollar_dollar.catalog_uri, _t1844, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1566 is not None
            unwrapped_fields1567 = fields1566
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            field1568 = unwrapped_fields1567[0]
            self.pretty_iceberg_catalog_uri(field1568)
            field1569 = unwrapped_fields1567[1]
            if field1569 is not None:
                self.newline()
                assert field1569 is not None
                opt_val1570 = field1569
                self.pretty_iceberg_catalog_config_scope(opt_val1570)
            self.newline()
            field1571 = unwrapped_fields1567[2]
            self.pretty_iceberg_properties(field1571)
            self.newline()
            field1572 = unwrapped_fields1567[3]
            self.pretty_iceberg_auth_properties(field1572)
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_uri(self, msg: str):
        flat1575 = self._try_flat(msg, self.pretty_iceberg_catalog_uri)
        if flat1575 is not None:
            assert flat1575 is not None
            self.write(flat1575)
            return None
        else:
            fields1574 = msg
            self.write("(catalog_uri")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1574))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1577 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1577 is not None:
            assert flat1577 is not None
            self.write(flat1577)
            return None
        else:
            fields1576 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1576))
            self.dedent()
            self.write(")")

    def pretty_iceberg_properties(self, msg: Sequence[tuple[str, str]]):
        flat1581 = self._try_flat(msg, self.pretty_iceberg_properties)
        if flat1581 is not None:
            assert flat1581 is not None
            self.write(flat1581)
            return None
        else:
            fields1578 = msg
            self.write("(properties")
            self.indent_sexp()
            if not len(fields1578) == 0:
                self.newline()
                for i1580, elem1579 in enumerate(fields1578):
                    if (i1580 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1579)
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1586 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1586 is not None:
            assert flat1586 is not None
            self.write(flat1586)
            return None
        else:
            _dollar_dollar = msg
            fields1582 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1582 is not None
            unwrapped_fields1583 = fields1582
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1584 = unwrapped_fields1583[0]
            self.write(self.format_string_value(field1584))
            self.newline()
            field1585 = unwrapped_fields1583[1]
            self.write(self.format_string_value(field1585))
            self.dedent()
            self.write(")")

    def pretty_iceberg_auth_properties(self, msg: Sequence[tuple[str, str]]):
        flat1590 = self._try_flat(msg, self.pretty_iceberg_auth_properties)
        if flat1590 is not None:
            assert flat1590 is not None
            self.write(flat1590)
            return None
        else:
            fields1587 = msg
            self.write("(auth_properties")
            self.indent_sexp()
            if not len(fields1587) == 0:
                self.newline()
                for i1589, elem1588 in enumerate(fields1587):
                    if (i1589 > 0):
                        self.newline()
                    self.pretty_iceberg_masked_property_entry(elem1588)
            self.dedent()
            self.write(")")

    def pretty_iceberg_masked_property_entry(self, msg: tuple[str, str]):
        flat1595 = self._try_flat(msg, self.pretty_iceberg_masked_property_entry)
        if flat1595 is not None:
            assert flat1595 is not None
            self.write(flat1595)
            return None
        else:
            _dollar_dollar = msg
            _t1845 = self.mask_secret_value(_dollar_dollar)
            fields1591 = (_dollar_dollar[0], _t1845,)
            assert fields1591 is not None
            unwrapped_fields1592 = fields1591
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1593 = unwrapped_fields1592[0]
            self.write(self.format_string_value(field1593))
            self.newline()
            field1594 = unwrapped_fields1592[1]
            self.write(self.format_string_value(field1594))
            self.dedent()
            self.write(")")

    def pretty_iceberg_from_snapshot(self, msg: str):
        flat1597 = self._try_flat(msg, self.pretty_iceberg_from_snapshot)
        if flat1597 is not None:
            assert flat1597 is not None
            self.write(flat1597)
            return None
        else:
            fields1596 = msg
            self.write("(from_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1596))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1599 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1599 is not None:
            assert flat1599 is not None
            self.write(flat1599)
            return None
        else:
            fields1598 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1598))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1602 = self._try_flat(msg, self.pretty_undefine)
        if flat1602 is not None:
            assert flat1602 is not None
            self.write(flat1602)
            return None
        else:
            _dollar_dollar = msg
            fields1600 = _dollar_dollar.fragment_id
            assert fields1600 is not None
            unwrapped_fields1601 = fields1600
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1601)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1607 = self._try_flat(msg, self.pretty_context)
        if flat1607 is not None:
            assert flat1607 is not None
            self.write(flat1607)
            return None
        else:
            _dollar_dollar = msg
            fields1603 = _dollar_dollar.relations
            assert fields1603 is not None
            unwrapped_fields1604 = fields1603
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1604) == 0:
                self.newline()
                for i1606, elem1605 in enumerate(unwrapped_fields1604):
                    if (i1606 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1605)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1614 = self._try_flat(msg, self.pretty_snapshot)
        if flat1614 is not None:
            assert flat1614 is not None
            self.write(flat1614)
            return None
        else:
            _dollar_dollar = msg
            fields1608 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
            assert fields1608 is not None
            unwrapped_fields1609 = fields1608
            self.write("(snapshot")
            self.indent_sexp()
            self.newline()
            field1610 = unwrapped_fields1609[0]
            self.pretty_edb_path(field1610)
            field1611 = unwrapped_fields1609[1]
            if not len(field1611) == 0:
                self.newline()
                for i1613, elem1612 in enumerate(field1611):
                    if (i1613 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1612)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1619 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1619 is not None:
            assert flat1619 is not None
            self.write(flat1619)
            return None
        else:
            _dollar_dollar = msg
            fields1615 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1615 is not None
            unwrapped_fields1616 = fields1615
            field1617 = unwrapped_fields1616[0]
            self.pretty_edb_path(field1617)
            self.write(" ")
            field1618 = unwrapped_fields1616[1]
            self.pretty_relation_id(field1618)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1623 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1623 is not None:
            assert flat1623 is not None
            self.write(flat1623)
            return None
        else:
            fields1620 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1620) == 0:
                self.newline()
                for i1622, elem1621 in enumerate(fields1620):
                    if (i1622 > 0):
                        self.newline()
                    self.pretty_read(elem1621)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1634 = self._try_flat(msg, self.pretty_read)
        if flat1634 is not None:
            assert flat1634 is not None
            self.write(flat1634)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1846 = _dollar_dollar.demand
            else:
                _t1846 = None
            deconstruct_result1632 = _t1846
            if deconstruct_result1632 is not None:
                assert deconstruct_result1632 is not None
                unwrapped1633 = deconstruct_result1632
                self.pretty_demand(unwrapped1633)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1847 = _dollar_dollar.output
                else:
                    _t1847 = None
                deconstruct_result1630 = _t1847
                if deconstruct_result1630 is not None:
                    assert deconstruct_result1630 is not None
                    unwrapped1631 = deconstruct_result1630
                    self.pretty_output(unwrapped1631)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1848 = _dollar_dollar.what_if
                    else:
                        _t1848 = None
                    deconstruct_result1628 = _t1848
                    if deconstruct_result1628 is not None:
                        assert deconstruct_result1628 is not None
                        unwrapped1629 = deconstruct_result1628
                        self.pretty_what_if(unwrapped1629)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1849 = _dollar_dollar.abort
                        else:
                            _t1849 = None
                        deconstruct_result1626 = _t1849
                        if deconstruct_result1626 is not None:
                            assert deconstruct_result1626 is not None
                            unwrapped1627 = deconstruct_result1626
                            self.pretty_abort(unwrapped1627)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1850 = _dollar_dollar.export
                            else:
                                _t1850 = None
                            deconstruct_result1624 = _t1850
                            if deconstruct_result1624 is not None:
                                assert deconstruct_result1624 is not None
                                unwrapped1625 = deconstruct_result1624
                                self.pretty_export(unwrapped1625)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1637 = self._try_flat(msg, self.pretty_demand)
        if flat1637 is not None:
            assert flat1637 is not None
            self.write(flat1637)
            return None
        else:
            _dollar_dollar = msg
            fields1635 = _dollar_dollar.relation_id
            assert fields1635 is not None
            unwrapped_fields1636 = fields1635
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1636)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1642 = self._try_flat(msg, self.pretty_output)
        if flat1642 is not None:
            assert flat1642 is not None
            self.write(flat1642)
            return None
        else:
            _dollar_dollar = msg
            fields1638 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1638 is not None
            unwrapped_fields1639 = fields1638
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1640 = unwrapped_fields1639[0]
            self.pretty_name(field1640)
            self.newline()
            field1641 = unwrapped_fields1639[1]
            self.pretty_relation_id(field1641)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1647 = self._try_flat(msg, self.pretty_what_if)
        if flat1647 is not None:
            assert flat1647 is not None
            self.write(flat1647)
            return None
        else:
            _dollar_dollar = msg
            fields1643 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1643 is not None
            unwrapped_fields1644 = fields1643
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1645 = unwrapped_fields1644[0]
            self.pretty_name(field1645)
            self.newline()
            field1646 = unwrapped_fields1644[1]
            self.pretty_epoch(field1646)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1653 = self._try_flat(msg, self.pretty_abort)
        if flat1653 is not None:
            assert flat1653 is not None
            self.write(flat1653)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1851 = _dollar_dollar.name
            else:
                _t1851 = None
            fields1648 = (_t1851, _dollar_dollar.relation_id,)
            assert fields1648 is not None
            unwrapped_fields1649 = fields1648
            self.write("(abort")
            self.indent_sexp()
            field1650 = unwrapped_fields1649[0]
            if field1650 is not None:
                self.newline()
                assert field1650 is not None
                opt_val1651 = field1650
                self.pretty_name(opt_val1651)
            self.newline()
            field1652 = unwrapped_fields1649[1]
            self.pretty_relation_id(field1652)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1658 = self._try_flat(msg, self.pretty_export)
        if flat1658 is not None:
            assert flat1658 is not None
            self.write(flat1658)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1852 = _dollar_dollar.csv_config
            else:
                _t1852 = None
            deconstruct_result1656 = _t1852
            if deconstruct_result1656 is not None:
                assert deconstruct_result1656 is not None
                unwrapped1657 = deconstruct_result1656
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1657)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1853 = _dollar_dollar.iceberg_config
                else:
                    _t1853 = None
                deconstruct_result1654 = _t1853
                if deconstruct_result1654 is not None:
                    assert deconstruct_result1654 is not None
                    unwrapped1655 = deconstruct_result1654
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1655)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1669 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1669 is not None:
            assert flat1669 is not None
            self.write(flat1669)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1855 = self.deconstruct_export_csv_output_location(_dollar_dollar)
                _t1854 = (_t1855, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1854 = None
            deconstruct_result1664 = _t1854
            if deconstruct_result1664 is not None:
                assert deconstruct_result1664 is not None
                unwrapped1665 = deconstruct_result1664
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1666 = unwrapped1665[0]
                self.pretty_export_csv_output_location(field1666)
                self.newline()
                field1667 = unwrapped1665[1]
                self.pretty_export_csv_source(field1667)
                self.newline()
                field1668 = unwrapped1665[2]
                self.pretty_csv_config(field1668)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1857 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1856 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1857,)
                else:
                    _t1856 = None
                deconstruct_result1659 = _t1856
                if deconstruct_result1659 is not None:
                    assert deconstruct_result1659 is not None
                    unwrapped1660 = deconstruct_result1659
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1661 = unwrapped1660[0]
                    self.pretty_export_csv_path(field1661)
                    self.newline()
                    field1662 = unwrapped1660[1]
                    self.pretty_export_csv_columns_list(field1662)
                    self.newline()
                    field1663 = unwrapped1660[2]
                    self.pretty_config_dict(field1663)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_output_location(self, msg: tuple[str, str]):
        flat1674 = self._try_flat(msg, self.pretty_export_csv_output_location)
        if flat1674 is not None:
            assert flat1674 is not None
            self.write(flat1674)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar[0] != "":
                _t1858 = _dollar_dollar[0]
            else:
                _t1858 = None
            deconstruct_result1672 = _t1858
            if deconstruct_result1672 is not None:
                assert deconstruct_result1672 is not None
                unwrapped1673 = deconstruct_result1672
                self.write("(path")
                self.indent_sexp()
                self.newline()
                self.write(self.format_string_value(unwrapped1673))
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar[1] != "":
                    _t1859 = _dollar_dollar[1]
                else:
                    _t1859 = None
                deconstruct_result1670 = _t1859
                if deconstruct_result1670 is not None:
                    assert deconstruct_result1670 is not None
                    unwrapped1671 = deconstruct_result1670
                    self.write("(transaction_output_name")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_name(unwrapped1671)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_output_location")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1681 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1681 is not None:
            assert flat1681 is not None
            self.write(flat1681)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1860 = _dollar_dollar.gnf_columns.columns
            else:
                _t1860 = None
            deconstruct_result1677 = _t1860
            if deconstruct_result1677 is not None:
                assert deconstruct_result1677 is not None
                unwrapped1678 = deconstruct_result1677
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1678) == 0:
                    self.newline()
                    for i1680, elem1679 in enumerate(unwrapped1678):
                        if (i1680 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1679)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1861 = _dollar_dollar.table_def
                else:
                    _t1861 = None
                deconstruct_result1675 = _t1861
                if deconstruct_result1675 is not None:
                    assert deconstruct_result1675 is not None
                    unwrapped1676 = deconstruct_result1675
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1676)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1686 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1686 is not None:
            assert flat1686 is not None
            self.write(flat1686)
            return None
        else:
            _dollar_dollar = msg
            fields1682 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1682 is not None
            unwrapped_fields1683 = fields1682
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1684 = unwrapped_fields1683[0]
            self.write(self.format_string_value(field1684))
            self.newline()
            field1685 = unwrapped_fields1683[1]
            self.pretty_relation_id(field1685)
            self.dedent()
            self.write(")")

    def pretty_export_csv_path(self, msg: str):
        flat1688 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1688 is not None:
            assert flat1688 is not None
            self.write(flat1688)
            return None
        else:
            fields1687 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1687))
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1692 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1692 is not None:
            assert flat1692 is not None
            self.write(flat1692)
            return None
        else:
            fields1689 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1689) == 0:
                self.newline()
                for i1691, elem1690 in enumerate(fields1689):
                    if (i1691 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1690)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1701 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1701 is not None:
            assert flat1701 is not None
            self.write(flat1701)
            return None
        else:
            _dollar_dollar = msg
            _t1862 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1693 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sorted(_dollar_dollar.table_properties.items()), _t1862,)
            assert fields1693 is not None
            unwrapped_fields1694 = fields1693
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1695 = unwrapped_fields1694[0]
            self.pretty_iceberg_locator(field1695)
            self.newline()
            field1696 = unwrapped_fields1694[1]
            self.pretty_iceberg_catalog_config(field1696)
            self.newline()
            field1697 = unwrapped_fields1694[2]
            self.pretty_export_iceberg_table_def(field1697)
            self.newline()
            field1698 = unwrapped_fields1694[3]
            self.pretty_iceberg_table_properties(field1698)
            field1699 = unwrapped_fields1694[4]
            if field1699 is not None:
                self.newline()
                assert field1699 is not None
                opt_val1700 = field1699
                self.pretty_config_dict(opt_val1700)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_table_def(self, msg: logic_pb2.RelationId):
        flat1703 = self._try_flat(msg, self.pretty_export_iceberg_table_def)
        if flat1703 is not None:
            assert flat1703 is not None
            self.write(flat1703)
            return None
        else:
            fields1702 = msg
            self.write("(table_def")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1702)
            self.dedent()
            self.write(")")

    def pretty_iceberg_table_properties(self, msg: Sequence[tuple[str, str]]):
        flat1707 = self._try_flat(msg, self.pretty_iceberg_table_properties)
        if flat1707 is not None:
            assert flat1707 is not None
            self.write(flat1707)
            return None
        else:
            fields1704 = msg
            self.write("(table_properties")
            self.indent_sexp()
            if not len(fields1704) == 0:
                self.newline()
                for i1706, elem1705 in enumerate(fields1704):
                    if (i1706 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1705)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1917 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1917)
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
