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
            _t1874 = None
        return None

    def deconstruct_csv_data_columns_optional(self, msg: logic_pb2.CSVData) -> Sequence[logic_pb2.GNFColumn] | None:
        if msg.HasField("relations"):
            return None
        else:
            _t1875 = None
        return msg.columns

    def deconstruct_csv_data_relations_optional(self, msg: logic_pb2.CSVData) -> logic_pb2.TargetRelations | None:
        if msg.HasField("relations"):
            assert msg.relations is not None
            return msg.relations
        else:
            _t1876 = None
        return None

    def deconstruct_export_csv_output_location(self, msg: transactions_pb2.ExportCSVConfig) -> tuple[str, str]:
        return (msg.path, msg.transaction_output_name,)

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1877 = logic_pb2.Value(int32_value=v)
        return _t1877

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1878 = logic_pb2.Value(int_value=v)
        return _t1878

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1879 = logic_pb2.Value(float_value=v)
        return _t1879

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1880 = logic_pb2.Value(string_value=v)
        return _t1880

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1881 = logic_pb2.Value(boolean_value=v)
        return _t1881

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1882 = logic_pb2.Value(uint128_value=v)
        return _t1882

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1883 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1883,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1884 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1884,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1885 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1885,))
        _t1886 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1886,))
        for pair in sorted(msg.configuration_values.items()):
            result.append(pair)
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1887 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1887,))
        _t1888 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1888,))
        if msg.new_line != "":
            _t1889 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1889,))
        _t1890 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1890,))
        _t1891 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1891,))
        _t1892 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1892,))
        if msg.comment != "":
            _t1893 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1893,))
        for missing_string in msg.missing_strings:
            _t1894 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1894,))
        _t1895 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1895,))
        _t1896 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1896,))
        _t1897 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1897,))
        if msg.partition_size_mb != 0:
            _t1898 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1898,))
        return sorted(result)

    def deconstruct_csv_storage_integration_optional(self, msg: logic_pb2.CSVConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        if not msg.HasField("storage_integration"):
            return None
        else:
            _t1899 = None
        assert msg.storage_integration is not None
        si = msg.storage_integration
        result = []
        if si.provider != "":
            _t1900 = self._make_value_string(si.provider)
            result.append(("provider", _t1900,))
        if si.azure_sas_token != "":
            _t1901 = self._make_value_string("***")
            result.append(("azure_sas_token", _t1901,))
        if si.s3_region != "":
            _t1902 = self._make_value_string(si.s3_region)
            result.append(("s3_region", _t1902,))
        if si.s3_access_key_id != "":
            _t1903 = self._make_value_string("***")
            result.append(("s3_access_key_id", _t1903,))
        if si.s3_secret_access_key != "":
            _t1904 = self._make_value_string("***")
            result.append(("s3_secret_access_key", _t1904,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1905 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1905,))
        _t1906 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1906,))
        _t1907 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1907,))
        _t1908 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1908,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1909 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1909,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1910 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1910,))
        _t1911 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1911,))
        _t1912 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1912,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1913 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1913,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1914 = self._make_value_string(msg.compression)
            result.append(("compression", _t1914,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1915 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1915,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1916 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1916,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1917 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1917,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1918 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1918,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1919 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1919,))
        return sorted(result)

    def mask_secret_value(self, pair: tuple[str, str]) -> str:
        return "***"

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1920 = None
        return None

    def deconstruct_iceberg_data_from_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.from_snapshot is not None
        if msg.from_snapshot != "":
            assert msg.from_snapshot is not None
            return msg.from_snapshot
        else:
            _t1921 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1922 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1923 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1923,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1924 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1924,))
        if msg.compression != "":
            _t1925 = self._make_value_string(msg.compression)
            result.append(("compression", _t1925,))
        if len(result) == 0:
            return None
        else:
            _t1926 = None
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
            _t1927 = None
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
        flat868 = self._try_flat(msg, self.pretty_transaction)
        if flat868 is not None:
            assert flat868 is not None
            self.write(flat868)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1718 = _dollar_dollar.configure
            else:
                _t1718 = None
            if _dollar_dollar.HasField("sync"):
                _t1719 = _dollar_dollar.sync
            else:
                _t1719 = None
            fields859 = (_t1718, _t1719, _dollar_dollar.epochs,)
            assert fields859 is not None
            unwrapped_fields860 = fields859
            self.write("(transaction")
            self.indent_sexp()
            field861 = unwrapped_fields860[0]
            if field861 is not None:
                self.newline()
                assert field861 is not None
                opt_val862 = field861
                self.pretty_configure(opt_val862)
            field863 = unwrapped_fields860[1]
            if field863 is not None:
                self.newline()
                assert field863 is not None
                opt_val864 = field863
                self.pretty_sync(opt_val864)
            field865 = unwrapped_fields860[2]
            if not len(field865) == 0:
                self.newline()
                for i867, elem866 in enumerate(field865):
                    if (i867 > 0):
                        self.newline()
                    self.pretty_epoch(elem866)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat871 = self._try_flat(msg, self.pretty_configure)
        if flat871 is not None:
            assert flat871 is not None
            self.write(flat871)
            return None
        else:
            _dollar_dollar = msg
            _t1720 = self.deconstruct_configure(_dollar_dollar)
            fields869 = _t1720
            assert fields869 is not None
            unwrapped_fields870 = fields869
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields870)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat875 = self._try_flat(msg, self.pretty_config_dict)
        if flat875 is not None:
            assert flat875 is not None
            self.write(flat875)
            return None
        else:
            fields872 = msg
            self.write("{")
            self.indent()
            if not len(fields872) == 0:
                self.newline()
                for i874, elem873 in enumerate(fields872):
                    if (i874 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem873)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat880 = self._try_flat(msg, self.pretty_config_key_value)
        if flat880 is not None:
            assert flat880 is not None
            self.write(flat880)
            return None
        else:
            _dollar_dollar = msg
            fields876 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields876 is not None
            unwrapped_fields877 = fields876
            self.write(":")
            field878 = unwrapped_fields877[0]
            self.write(field878)
            self.write(" ")
            field879 = unwrapped_fields877[1]
            self.pretty_raw_value(field879)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat906 = self._try_flat(msg, self.pretty_raw_value)
        if flat906 is not None:
            assert flat906 is not None
            self.write(flat906)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1721 = _dollar_dollar.date_value
            else:
                _t1721 = None
            deconstruct_result904 = _t1721
            if deconstruct_result904 is not None:
                assert deconstruct_result904 is not None
                unwrapped905 = deconstruct_result904
                self.pretty_raw_date(unwrapped905)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1722 = _dollar_dollar.datetime_value
                else:
                    _t1722 = None
                deconstruct_result902 = _t1722
                if deconstruct_result902 is not None:
                    assert deconstruct_result902 is not None
                    unwrapped903 = deconstruct_result902
                    self.pretty_raw_datetime(unwrapped903)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1723 = _dollar_dollar.string_value
                    else:
                        _t1723 = None
                    deconstruct_result900 = _t1723
                    if deconstruct_result900 is not None:
                        assert deconstruct_result900 is not None
                        unwrapped901 = deconstruct_result900
                        self.write(self.format_string_value(unwrapped901))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1724 = _dollar_dollar.int32_value
                        else:
                            _t1724 = None
                        deconstruct_result898 = _t1724
                        if deconstruct_result898 is not None:
                            assert deconstruct_result898 is not None
                            unwrapped899 = deconstruct_result898
                            self.write((str(unwrapped899) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1725 = _dollar_dollar.int_value
                            else:
                                _t1725 = None
                            deconstruct_result896 = _t1725
                            if deconstruct_result896 is not None:
                                assert deconstruct_result896 is not None
                                unwrapped897 = deconstruct_result896
                                self.write(str(unwrapped897))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1726 = _dollar_dollar.float32_value
                                else:
                                    _t1726 = None
                                deconstruct_result894 = _t1726
                                if deconstruct_result894 is not None:
                                    assert deconstruct_result894 is not None
                                    unwrapped895 = deconstruct_result894
                                    self.write(self.format_float32_literal(unwrapped895))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1727 = _dollar_dollar.float_value
                                    else:
                                        _t1727 = None
                                    deconstruct_result892 = _t1727
                                    if deconstruct_result892 is not None:
                                        assert deconstruct_result892 is not None
                                        unwrapped893 = deconstruct_result892
                                        self.write(str(unwrapped893))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1728 = _dollar_dollar.uint32_value
                                        else:
                                            _t1728 = None
                                        deconstruct_result890 = _t1728
                                        if deconstruct_result890 is not None:
                                            assert deconstruct_result890 is not None
                                            unwrapped891 = deconstruct_result890
                                            self.write((str(unwrapped891) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1729 = _dollar_dollar.uint128_value
                                            else:
                                                _t1729 = None
                                            deconstruct_result888 = _t1729
                                            if deconstruct_result888 is not None:
                                                assert deconstruct_result888 is not None
                                                unwrapped889 = deconstruct_result888
                                                self.write(self.format_uint128(unwrapped889))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1730 = _dollar_dollar.int128_value
                                                else:
                                                    _t1730 = None
                                                deconstruct_result886 = _t1730
                                                if deconstruct_result886 is not None:
                                                    assert deconstruct_result886 is not None
                                                    unwrapped887 = deconstruct_result886
                                                    self.write(self.format_int128(unwrapped887))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1731 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1731 = None
                                                    deconstruct_result884 = _t1731
                                                    if deconstruct_result884 is not None:
                                                        assert deconstruct_result884 is not None
                                                        unwrapped885 = deconstruct_result884
                                                        self.write(self.format_decimal(unwrapped885))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1732 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1732 = None
                                                        deconstruct_result882 = _t1732
                                                        if deconstruct_result882 is not None:
                                                            assert deconstruct_result882 is not None
                                                            unwrapped883 = deconstruct_result882
                                                            self.pretty_boolean_value(unwrapped883)
                                                        else:
                                                            fields881 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat912 = self._try_flat(msg, self.pretty_raw_date)
        if flat912 is not None:
            assert flat912 is not None
            self.write(flat912)
            return None
        else:
            _dollar_dollar = msg
            fields907 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields907 is not None
            unwrapped_fields908 = fields907
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field909 = unwrapped_fields908[0]
            self.write(str(field909))
            self.newline()
            field910 = unwrapped_fields908[1]
            self.write(str(field910))
            self.newline()
            field911 = unwrapped_fields908[2]
            self.write(str(field911))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat923 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat923 is not None:
            assert flat923 is not None
            self.write(flat923)
            return None
        else:
            _dollar_dollar = msg
            fields913 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields913 is not None
            unwrapped_fields914 = fields913
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field915 = unwrapped_fields914[0]
            self.write(str(field915))
            self.newline()
            field916 = unwrapped_fields914[1]
            self.write(str(field916))
            self.newline()
            field917 = unwrapped_fields914[2]
            self.write(str(field917))
            self.newline()
            field918 = unwrapped_fields914[3]
            self.write(str(field918))
            self.newline()
            field919 = unwrapped_fields914[4]
            self.write(str(field919))
            self.newline()
            field920 = unwrapped_fields914[5]
            self.write(str(field920))
            field921 = unwrapped_fields914[6]
            if field921 is not None:
                self.newline()
                assert field921 is not None
                opt_val922 = field921
                self.write(str(opt_val922))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1733 = ()
        else:
            _t1733 = None
        deconstruct_result926 = _t1733
        if deconstruct_result926 is not None:
            assert deconstruct_result926 is not None
            unwrapped927 = deconstruct_result926
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1734 = ()
            else:
                _t1734 = None
            deconstruct_result924 = _t1734
            if deconstruct_result924 is not None:
                assert deconstruct_result924 is not None
                unwrapped925 = deconstruct_result924
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat932 = self._try_flat(msg, self.pretty_sync)
        if flat932 is not None:
            assert flat932 is not None
            self.write(flat932)
            return None
        else:
            _dollar_dollar = msg
            fields928 = _dollar_dollar.fragments
            assert fields928 is not None
            unwrapped_fields929 = fields928
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields929) == 0:
                self.newline()
                for i931, elem930 in enumerate(unwrapped_fields929):
                    if (i931 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem930)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat935 = self._try_flat(msg, self.pretty_fragment_id)
        if flat935 is not None:
            assert flat935 is not None
            self.write(flat935)
            return None
        else:
            _dollar_dollar = msg
            fields933 = self.fragment_id_to_string(_dollar_dollar)
            assert fields933 is not None
            unwrapped_fields934 = fields933
            self.write(":")
            self.write(unwrapped_fields934)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat942 = self._try_flat(msg, self.pretty_epoch)
        if flat942 is not None:
            assert flat942 is not None
            self.write(flat942)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1735 = _dollar_dollar.writes
            else:
                _t1735 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1736 = _dollar_dollar.reads
            else:
                _t1736 = None
            fields936 = (_t1735, _t1736,)
            assert fields936 is not None
            unwrapped_fields937 = fields936
            self.write("(epoch")
            self.indent_sexp()
            field938 = unwrapped_fields937[0]
            if field938 is not None:
                self.newline()
                assert field938 is not None
                opt_val939 = field938
                self.pretty_epoch_writes(opt_val939)
            field940 = unwrapped_fields937[1]
            if field940 is not None:
                self.newline()
                assert field940 is not None
                opt_val941 = field940
                self.pretty_epoch_reads(opt_val941)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat946 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat946 is not None:
            assert flat946 is not None
            self.write(flat946)
            return None
        else:
            fields943 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields943) == 0:
                self.newline()
                for i945, elem944 in enumerate(fields943):
                    if (i945 > 0):
                        self.newline()
                    self.pretty_write(elem944)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat955 = self._try_flat(msg, self.pretty_write)
        if flat955 is not None:
            assert flat955 is not None
            self.write(flat955)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1737 = _dollar_dollar.define
            else:
                _t1737 = None
            deconstruct_result953 = _t1737
            if deconstruct_result953 is not None:
                assert deconstruct_result953 is not None
                unwrapped954 = deconstruct_result953
                self.pretty_define(unwrapped954)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1738 = _dollar_dollar.undefine
                else:
                    _t1738 = None
                deconstruct_result951 = _t1738
                if deconstruct_result951 is not None:
                    assert deconstruct_result951 is not None
                    unwrapped952 = deconstruct_result951
                    self.pretty_undefine(unwrapped952)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1739 = _dollar_dollar.context
                    else:
                        _t1739 = None
                    deconstruct_result949 = _t1739
                    if deconstruct_result949 is not None:
                        assert deconstruct_result949 is not None
                        unwrapped950 = deconstruct_result949
                        self.pretty_context(unwrapped950)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1740 = _dollar_dollar.snapshot
                        else:
                            _t1740 = None
                        deconstruct_result947 = _t1740
                        if deconstruct_result947 is not None:
                            assert deconstruct_result947 is not None
                            unwrapped948 = deconstruct_result947
                            self.pretty_snapshot(unwrapped948)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat958 = self._try_flat(msg, self.pretty_define)
        if flat958 is not None:
            assert flat958 is not None
            self.write(flat958)
            return None
        else:
            _dollar_dollar = msg
            fields956 = _dollar_dollar.fragment
            assert fields956 is not None
            unwrapped_fields957 = fields956
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields957)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat965 = self._try_flat(msg, self.pretty_fragment)
        if flat965 is not None:
            assert flat965 is not None
            self.write(flat965)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields959 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields959 is not None
            unwrapped_fields960 = fields959
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field961 = unwrapped_fields960[0]
            self.pretty_new_fragment_id(field961)
            field962 = unwrapped_fields960[1]
            if not len(field962) == 0:
                self.newline()
                for i964, elem963 in enumerate(field962):
                    if (i964 > 0):
                        self.newline()
                    self.pretty_declaration(elem963)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat967 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat967 is not None:
            assert flat967 is not None
            self.write(flat967)
            return None
        else:
            fields966 = msg
            self.pretty_fragment_id(fields966)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat976 = self._try_flat(msg, self.pretty_declaration)
        if flat976 is not None:
            assert flat976 is not None
            self.write(flat976)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1741 = getattr(_dollar_dollar, 'def')
            else:
                _t1741 = None
            deconstruct_result974 = _t1741
            if deconstruct_result974 is not None:
                assert deconstruct_result974 is not None
                unwrapped975 = deconstruct_result974
                self.pretty_def(unwrapped975)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1742 = _dollar_dollar.algorithm
                else:
                    _t1742 = None
                deconstruct_result972 = _t1742
                if deconstruct_result972 is not None:
                    assert deconstruct_result972 is not None
                    unwrapped973 = deconstruct_result972
                    self.pretty_algorithm(unwrapped973)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1743 = _dollar_dollar.constraint
                    else:
                        _t1743 = None
                    deconstruct_result970 = _t1743
                    if deconstruct_result970 is not None:
                        assert deconstruct_result970 is not None
                        unwrapped971 = deconstruct_result970
                        self.pretty_constraint(unwrapped971)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1744 = _dollar_dollar.data
                        else:
                            _t1744 = None
                        deconstruct_result968 = _t1744
                        if deconstruct_result968 is not None:
                            assert deconstruct_result968 is not None
                            unwrapped969 = deconstruct_result968
                            self.pretty_data(unwrapped969)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat983 = self._try_flat(msg, self.pretty_def)
        if flat983 is not None:
            assert flat983 is not None
            self.write(flat983)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1745 = _dollar_dollar.attrs
            else:
                _t1745 = None
            fields977 = (_dollar_dollar.name, _dollar_dollar.body, _t1745,)
            assert fields977 is not None
            unwrapped_fields978 = fields977
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field979 = unwrapped_fields978[0]
            self.pretty_relation_id(field979)
            self.newline()
            field980 = unwrapped_fields978[1]
            self.pretty_abstraction(field980)
            field981 = unwrapped_fields978[2]
            if field981 is not None:
                self.newline()
                assert field981 is not None
                opt_val982 = field981
                self.pretty_attrs(opt_val982)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat988 = self._try_flat(msg, self.pretty_relation_id)
        if flat988 is not None:
            assert flat988 is not None
            self.write(flat988)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1747 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1746 = _t1747
            else:
                _t1746 = None
            deconstruct_result986 = _t1746
            if deconstruct_result986 is not None:
                assert deconstruct_result986 is not None
                unwrapped987 = deconstruct_result986
                self.write(":")
                self.write(unwrapped987)
            else:
                _dollar_dollar = msg
                _t1748 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result984 = _t1748
                if deconstruct_result984 is not None:
                    assert deconstruct_result984 is not None
                    unwrapped985 = deconstruct_result984
                    self.write(self.format_uint128(unwrapped985))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat993 = self._try_flat(msg, self.pretty_abstraction)
        if flat993 is not None:
            assert flat993 is not None
            self.write(flat993)
            return None
        else:
            _dollar_dollar = msg
            _t1749 = self.deconstruct_bindings(_dollar_dollar)
            fields989 = (_t1749, _dollar_dollar.value,)
            assert fields989 is not None
            unwrapped_fields990 = fields989
            self.write("(")
            self.indent()
            field991 = unwrapped_fields990[0]
            self.pretty_bindings(field991)
            self.newline()
            field992 = unwrapped_fields990[1]
            self.pretty_formula(field992)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat1001 = self._try_flat(msg, self.pretty_bindings)
        if flat1001 is not None:
            assert flat1001 is not None
            self.write(flat1001)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1750 = _dollar_dollar[1]
            else:
                _t1750 = None
            fields994 = (_dollar_dollar[0], _t1750,)
            assert fields994 is not None
            unwrapped_fields995 = fields994
            self.write("[")
            self.indent()
            field996 = unwrapped_fields995[0]
            for i998, elem997 in enumerate(field996):
                if (i998 > 0):
                    self.newline()
                self.pretty_binding(elem997)
            field999 = unwrapped_fields995[1]
            if field999 is not None:
                self.newline()
                assert field999 is not None
                opt_val1000 = field999
                self.pretty_value_bindings(opt_val1000)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat1006 = self._try_flat(msg, self.pretty_binding)
        if flat1006 is not None:
            assert flat1006 is not None
            self.write(flat1006)
            return None
        else:
            _dollar_dollar = msg
            fields1002 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields1002 is not None
            unwrapped_fields1003 = fields1002
            field1004 = unwrapped_fields1003[0]
            self.write(field1004)
            self.write("::")
            field1005 = unwrapped_fields1003[1]
            self.pretty_type(field1005)

    def pretty_type(self, msg: logic_pb2.Type):
        flat1037 = self._try_flat(msg, self.pretty_type)
        if flat1037 is not None:
            assert flat1037 is not None
            self.write(flat1037)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1751 = _dollar_dollar.unspecified_type
            else:
                _t1751 = None
            deconstruct_result1035 = _t1751
            if deconstruct_result1035 is not None:
                assert deconstruct_result1035 is not None
                unwrapped1036 = deconstruct_result1035
                self.pretty_unspecified_type(unwrapped1036)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1752 = _dollar_dollar.string_type
                else:
                    _t1752 = None
                deconstruct_result1033 = _t1752
                if deconstruct_result1033 is not None:
                    assert deconstruct_result1033 is not None
                    unwrapped1034 = deconstruct_result1033
                    self.pretty_string_type(unwrapped1034)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1753 = _dollar_dollar.int_type
                    else:
                        _t1753 = None
                    deconstruct_result1031 = _t1753
                    if deconstruct_result1031 is not None:
                        assert deconstruct_result1031 is not None
                        unwrapped1032 = deconstruct_result1031
                        self.pretty_int_type(unwrapped1032)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1754 = _dollar_dollar.float_type
                        else:
                            _t1754 = None
                        deconstruct_result1029 = _t1754
                        if deconstruct_result1029 is not None:
                            assert deconstruct_result1029 is not None
                            unwrapped1030 = deconstruct_result1029
                            self.pretty_float_type(unwrapped1030)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1755 = _dollar_dollar.uint128_type
                            else:
                                _t1755 = None
                            deconstruct_result1027 = _t1755
                            if deconstruct_result1027 is not None:
                                assert deconstruct_result1027 is not None
                                unwrapped1028 = deconstruct_result1027
                                self.pretty_uint128_type(unwrapped1028)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1756 = _dollar_dollar.int128_type
                                else:
                                    _t1756 = None
                                deconstruct_result1025 = _t1756
                                if deconstruct_result1025 is not None:
                                    assert deconstruct_result1025 is not None
                                    unwrapped1026 = deconstruct_result1025
                                    self.pretty_int128_type(unwrapped1026)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1757 = _dollar_dollar.date_type
                                    else:
                                        _t1757 = None
                                    deconstruct_result1023 = _t1757
                                    if deconstruct_result1023 is not None:
                                        assert deconstruct_result1023 is not None
                                        unwrapped1024 = deconstruct_result1023
                                        self.pretty_date_type(unwrapped1024)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1758 = _dollar_dollar.datetime_type
                                        else:
                                            _t1758 = None
                                        deconstruct_result1021 = _t1758
                                        if deconstruct_result1021 is not None:
                                            assert deconstruct_result1021 is not None
                                            unwrapped1022 = deconstruct_result1021
                                            self.pretty_datetime_type(unwrapped1022)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1759 = _dollar_dollar.missing_type
                                            else:
                                                _t1759 = None
                                            deconstruct_result1019 = _t1759
                                            if deconstruct_result1019 is not None:
                                                assert deconstruct_result1019 is not None
                                                unwrapped1020 = deconstruct_result1019
                                                self.pretty_missing_type(unwrapped1020)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1760 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1760 = None
                                                deconstruct_result1017 = _t1760
                                                if deconstruct_result1017 is not None:
                                                    assert deconstruct_result1017 is not None
                                                    unwrapped1018 = deconstruct_result1017
                                                    self.pretty_decimal_type(unwrapped1018)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1761 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1761 = None
                                                    deconstruct_result1015 = _t1761
                                                    if deconstruct_result1015 is not None:
                                                        assert deconstruct_result1015 is not None
                                                        unwrapped1016 = deconstruct_result1015
                                                        self.pretty_boolean_type(unwrapped1016)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1762 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1762 = None
                                                        deconstruct_result1013 = _t1762
                                                        if deconstruct_result1013 is not None:
                                                            assert deconstruct_result1013 is not None
                                                            unwrapped1014 = deconstruct_result1013
                                                            self.pretty_int32_type(unwrapped1014)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1763 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1763 = None
                                                            deconstruct_result1011 = _t1763
                                                            if deconstruct_result1011 is not None:
                                                                assert deconstruct_result1011 is not None
                                                                unwrapped1012 = deconstruct_result1011
                                                                self.pretty_float32_type(unwrapped1012)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1764 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1764 = None
                                                                deconstruct_result1009 = _t1764
                                                                if deconstruct_result1009 is not None:
                                                                    assert deconstruct_result1009 is not None
                                                                    unwrapped1010 = deconstruct_result1009
                                                                    self.pretty_uint32_type(unwrapped1010)
                                                                else:
                                                                    _dollar_dollar = msg
                                                                    if _dollar_dollar.HasField("fixed_type"):
                                                                        _t1765 = _dollar_dollar.fixed_type
                                                                    else:
                                                                        _t1765 = None
                                                                    deconstruct_result1007 = _t1765
                                                                    if deconstruct_result1007 is not None:
                                                                        assert deconstruct_result1007 is not None
                                                                        unwrapped1008 = deconstruct_result1007
                                                                        self.pretty_fixed_type(unwrapped1008)
                                                                    else:
                                                                        raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields1038 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields1039 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields1040 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields1041 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields1042 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields1043 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields1044 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields1045 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields1046 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat1051 = self._try_flat(msg, self.pretty_decimal_type)
        if flat1051 is not None:
            assert flat1051 is not None
            self.write(flat1051)
            return None
        else:
            _dollar_dollar = msg
            fields1047 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields1047 is not None
            unwrapped_fields1048 = fields1047
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field1049 = unwrapped_fields1048[0]
            self.write(str(field1049))
            self.newline()
            field1050 = unwrapped_fields1048[1]
            self.write(str(field1050))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields1052 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields1053 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields1054 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields1055 = msg
        self.write("UINT32")

    def pretty_fixed_type(self, msg: logic_pb2.FixedType):
        flat1058 = self._try_flat(msg, self.pretty_fixed_type)
        if flat1058 is not None:
            assert flat1058 is not None
            self.write(flat1058)
            return None
        else:
            _dollar_dollar = msg
            fields1056 = int(_dollar_dollar.length)
            assert fields1056 is not None
            unwrapped_fields1057 = fields1056
            self.write("(FIXED")
            self.indent_sexp()
            self.newline()
            self.write(str(unwrapped_fields1057))
            self.dedent()
            self.write(")")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat1062 = self._try_flat(msg, self.pretty_value_bindings)
        if flat1062 is not None:
            assert flat1062 is not None
            self.write(flat1062)
            return None
        else:
            fields1059 = msg
            self.write("|")
            if not len(fields1059) == 0:
                self.write(" ")
                for i1061, elem1060 in enumerate(fields1059):
                    if (i1061 > 0):
                        self.newline()
                    self.pretty_binding(elem1060)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1089 = self._try_flat(msg, self.pretty_formula)
        if flat1089 is not None:
            assert flat1089 is not None
            self.write(flat1089)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1766 = _dollar_dollar.conjunction
            else:
                _t1766 = None
            deconstruct_result1087 = _t1766
            if deconstruct_result1087 is not None:
                assert deconstruct_result1087 is not None
                unwrapped1088 = deconstruct_result1087
                self.pretty_true(unwrapped1088)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1767 = _dollar_dollar.disjunction
                else:
                    _t1767 = None
                deconstruct_result1085 = _t1767
                if deconstruct_result1085 is not None:
                    assert deconstruct_result1085 is not None
                    unwrapped1086 = deconstruct_result1085
                    self.pretty_false(unwrapped1086)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1768 = _dollar_dollar.exists
                    else:
                        _t1768 = None
                    deconstruct_result1083 = _t1768
                    if deconstruct_result1083 is not None:
                        assert deconstruct_result1083 is not None
                        unwrapped1084 = deconstruct_result1083
                        self.pretty_exists(unwrapped1084)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1769 = _dollar_dollar.reduce
                        else:
                            _t1769 = None
                        deconstruct_result1081 = _t1769
                        if deconstruct_result1081 is not None:
                            assert deconstruct_result1081 is not None
                            unwrapped1082 = deconstruct_result1081
                            self.pretty_reduce(unwrapped1082)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1770 = _dollar_dollar.conjunction
                            else:
                                _t1770 = None
                            deconstruct_result1079 = _t1770
                            if deconstruct_result1079 is not None:
                                assert deconstruct_result1079 is not None
                                unwrapped1080 = deconstruct_result1079
                                self.pretty_conjunction(unwrapped1080)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1771 = _dollar_dollar.disjunction
                                else:
                                    _t1771 = None
                                deconstruct_result1077 = _t1771
                                if deconstruct_result1077 is not None:
                                    assert deconstruct_result1077 is not None
                                    unwrapped1078 = deconstruct_result1077
                                    self.pretty_disjunction(unwrapped1078)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1772 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1772 = None
                                    deconstruct_result1075 = _t1772
                                    if deconstruct_result1075 is not None:
                                        assert deconstruct_result1075 is not None
                                        unwrapped1076 = deconstruct_result1075
                                        self.pretty_not(unwrapped1076)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1773 = _dollar_dollar.ffi
                                        else:
                                            _t1773 = None
                                        deconstruct_result1073 = _t1773
                                        if deconstruct_result1073 is not None:
                                            assert deconstruct_result1073 is not None
                                            unwrapped1074 = deconstruct_result1073
                                            self.pretty_ffi(unwrapped1074)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1774 = _dollar_dollar.atom
                                            else:
                                                _t1774 = None
                                            deconstruct_result1071 = _t1774
                                            if deconstruct_result1071 is not None:
                                                assert deconstruct_result1071 is not None
                                                unwrapped1072 = deconstruct_result1071
                                                self.pretty_atom(unwrapped1072)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1775 = _dollar_dollar.pragma
                                                else:
                                                    _t1775 = None
                                                deconstruct_result1069 = _t1775
                                                if deconstruct_result1069 is not None:
                                                    assert deconstruct_result1069 is not None
                                                    unwrapped1070 = deconstruct_result1069
                                                    self.pretty_pragma(unwrapped1070)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1776 = _dollar_dollar.primitive
                                                    else:
                                                        _t1776 = None
                                                    deconstruct_result1067 = _t1776
                                                    if deconstruct_result1067 is not None:
                                                        assert deconstruct_result1067 is not None
                                                        unwrapped1068 = deconstruct_result1067
                                                        self.pretty_primitive(unwrapped1068)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1777 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1777 = None
                                                        deconstruct_result1065 = _t1777
                                                        if deconstruct_result1065 is not None:
                                                            assert deconstruct_result1065 is not None
                                                            unwrapped1066 = deconstruct_result1065
                                                            self.pretty_rel_atom(unwrapped1066)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1778 = _dollar_dollar.cast
                                                            else:
                                                                _t1778 = None
                                                            deconstruct_result1063 = _t1778
                                                            if deconstruct_result1063 is not None:
                                                                assert deconstruct_result1063 is not None
                                                                unwrapped1064 = deconstruct_result1063
                                                                self.pretty_cast(unwrapped1064)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields1090 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1091 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1096 = self._try_flat(msg, self.pretty_exists)
        if flat1096 is not None:
            assert flat1096 is not None
            self.write(flat1096)
            return None
        else:
            _dollar_dollar = msg
            _t1779 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1092 = (_t1779, _dollar_dollar.body.value,)
            assert fields1092 is not None
            unwrapped_fields1093 = fields1092
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1094 = unwrapped_fields1093[0]
            self.pretty_bindings(field1094)
            self.newline()
            field1095 = unwrapped_fields1093[1]
            self.pretty_formula(field1095)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1102 = self._try_flat(msg, self.pretty_reduce)
        if flat1102 is not None:
            assert flat1102 is not None
            self.write(flat1102)
            return None
        else:
            _dollar_dollar = msg
            fields1097 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1097 is not None
            unwrapped_fields1098 = fields1097
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1099 = unwrapped_fields1098[0]
            self.pretty_abstraction(field1099)
            self.newline()
            field1100 = unwrapped_fields1098[1]
            self.pretty_abstraction(field1100)
            self.newline()
            field1101 = unwrapped_fields1098[2]
            self.pretty_terms(field1101)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1106 = self._try_flat(msg, self.pretty_terms)
        if flat1106 is not None:
            assert flat1106 is not None
            self.write(flat1106)
            return None
        else:
            fields1103 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1103) == 0:
                self.newline()
                for i1105, elem1104 in enumerate(fields1103):
                    if (i1105 > 0):
                        self.newline()
                    self.pretty_term(elem1104)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1111 = self._try_flat(msg, self.pretty_term)
        if flat1111 is not None:
            assert flat1111 is not None
            self.write(flat1111)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1780 = _dollar_dollar.var
            else:
                _t1780 = None
            deconstruct_result1109 = _t1780
            if deconstruct_result1109 is not None:
                assert deconstruct_result1109 is not None
                unwrapped1110 = deconstruct_result1109
                self.pretty_var(unwrapped1110)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1781 = _dollar_dollar.constant
                else:
                    _t1781 = None
                deconstruct_result1107 = _t1781
                if deconstruct_result1107 is not None:
                    assert deconstruct_result1107 is not None
                    unwrapped1108 = deconstruct_result1107
                    self.pretty_value(unwrapped1108)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1114 = self._try_flat(msg, self.pretty_var)
        if flat1114 is not None:
            assert flat1114 is not None
            self.write(flat1114)
            return None
        else:
            _dollar_dollar = msg
            fields1112 = _dollar_dollar.name
            assert fields1112 is not None
            unwrapped_fields1113 = fields1112
            self.write(unwrapped_fields1113)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1140 = self._try_flat(msg, self.pretty_value)
        if flat1140 is not None:
            assert flat1140 is not None
            self.write(flat1140)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1782 = _dollar_dollar.date_value
            else:
                _t1782 = None
            deconstruct_result1138 = _t1782
            if deconstruct_result1138 is not None:
                assert deconstruct_result1138 is not None
                unwrapped1139 = deconstruct_result1138
                self.pretty_date(unwrapped1139)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1783 = _dollar_dollar.datetime_value
                else:
                    _t1783 = None
                deconstruct_result1136 = _t1783
                if deconstruct_result1136 is not None:
                    assert deconstruct_result1136 is not None
                    unwrapped1137 = deconstruct_result1136
                    self.pretty_datetime(unwrapped1137)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1784 = _dollar_dollar.string_value
                    else:
                        _t1784 = None
                    deconstruct_result1134 = _t1784
                    if deconstruct_result1134 is not None:
                        assert deconstruct_result1134 is not None
                        unwrapped1135 = deconstruct_result1134
                        self.write(self.format_string_value(unwrapped1135))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1785 = _dollar_dollar.int32_value
                        else:
                            _t1785 = None
                        deconstruct_result1132 = _t1785
                        if deconstruct_result1132 is not None:
                            assert deconstruct_result1132 is not None
                            unwrapped1133 = deconstruct_result1132
                            self.write((str(unwrapped1133) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1786 = _dollar_dollar.int_value
                            else:
                                _t1786 = None
                            deconstruct_result1130 = _t1786
                            if deconstruct_result1130 is not None:
                                assert deconstruct_result1130 is not None
                                unwrapped1131 = deconstruct_result1130
                                self.write(str(unwrapped1131))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1787 = _dollar_dollar.float32_value
                                else:
                                    _t1787 = None
                                deconstruct_result1128 = _t1787
                                if deconstruct_result1128 is not None:
                                    assert deconstruct_result1128 is not None
                                    unwrapped1129 = deconstruct_result1128
                                    self.write(self.format_float32_literal(unwrapped1129))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1788 = _dollar_dollar.float_value
                                    else:
                                        _t1788 = None
                                    deconstruct_result1126 = _t1788
                                    if deconstruct_result1126 is not None:
                                        assert deconstruct_result1126 is not None
                                        unwrapped1127 = deconstruct_result1126
                                        self.write(str(unwrapped1127))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1789 = _dollar_dollar.uint32_value
                                        else:
                                            _t1789 = None
                                        deconstruct_result1124 = _t1789
                                        if deconstruct_result1124 is not None:
                                            assert deconstruct_result1124 is not None
                                            unwrapped1125 = deconstruct_result1124
                                            self.write((str(unwrapped1125) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1790 = _dollar_dollar.uint128_value
                                            else:
                                                _t1790 = None
                                            deconstruct_result1122 = _t1790
                                            if deconstruct_result1122 is not None:
                                                assert deconstruct_result1122 is not None
                                                unwrapped1123 = deconstruct_result1122
                                                self.write(self.format_uint128(unwrapped1123))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1791 = _dollar_dollar.int128_value
                                                else:
                                                    _t1791 = None
                                                deconstruct_result1120 = _t1791
                                                if deconstruct_result1120 is not None:
                                                    assert deconstruct_result1120 is not None
                                                    unwrapped1121 = deconstruct_result1120
                                                    self.write(self.format_int128(unwrapped1121))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1792 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1792 = None
                                                    deconstruct_result1118 = _t1792
                                                    if deconstruct_result1118 is not None:
                                                        assert deconstruct_result1118 is not None
                                                        unwrapped1119 = deconstruct_result1118
                                                        self.write(self.format_decimal(unwrapped1119))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1793 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1793 = None
                                                        deconstruct_result1116 = _t1793
                                                        if deconstruct_result1116 is not None:
                                                            assert deconstruct_result1116 is not None
                                                            unwrapped1117 = deconstruct_result1116
                                                            self.pretty_boolean_value(unwrapped1117)
                                                        else:
                                                            fields1115 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1146 = self._try_flat(msg, self.pretty_date)
        if flat1146 is not None:
            assert flat1146 is not None
            self.write(flat1146)
            return None
        else:
            _dollar_dollar = msg
            fields1141 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1141 is not None
            unwrapped_fields1142 = fields1141
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1143 = unwrapped_fields1142[0]
            self.write(str(field1143))
            self.newline()
            field1144 = unwrapped_fields1142[1]
            self.write(str(field1144))
            self.newline()
            field1145 = unwrapped_fields1142[2]
            self.write(str(field1145))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1157 = self._try_flat(msg, self.pretty_datetime)
        if flat1157 is not None:
            assert flat1157 is not None
            self.write(flat1157)
            return None
        else:
            _dollar_dollar = msg
            fields1147 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1147 is not None
            unwrapped_fields1148 = fields1147
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1149 = unwrapped_fields1148[0]
            self.write(str(field1149))
            self.newline()
            field1150 = unwrapped_fields1148[1]
            self.write(str(field1150))
            self.newline()
            field1151 = unwrapped_fields1148[2]
            self.write(str(field1151))
            self.newline()
            field1152 = unwrapped_fields1148[3]
            self.write(str(field1152))
            self.newline()
            field1153 = unwrapped_fields1148[4]
            self.write(str(field1153))
            self.newline()
            field1154 = unwrapped_fields1148[5]
            self.write(str(field1154))
            field1155 = unwrapped_fields1148[6]
            if field1155 is not None:
                self.newline()
                assert field1155 is not None
                opt_val1156 = field1155
                self.write(str(opt_val1156))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1162 = self._try_flat(msg, self.pretty_conjunction)
        if flat1162 is not None:
            assert flat1162 is not None
            self.write(flat1162)
            return None
        else:
            _dollar_dollar = msg
            fields1158 = _dollar_dollar.args
            assert fields1158 is not None
            unwrapped_fields1159 = fields1158
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1159) == 0:
                self.newline()
                for i1161, elem1160 in enumerate(unwrapped_fields1159):
                    if (i1161 > 0):
                        self.newline()
                    self.pretty_formula(elem1160)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1167 = self._try_flat(msg, self.pretty_disjunction)
        if flat1167 is not None:
            assert flat1167 is not None
            self.write(flat1167)
            return None
        else:
            _dollar_dollar = msg
            fields1163 = _dollar_dollar.args
            assert fields1163 is not None
            unwrapped_fields1164 = fields1163
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1164) == 0:
                self.newline()
                for i1166, elem1165 in enumerate(unwrapped_fields1164):
                    if (i1166 > 0):
                        self.newline()
                    self.pretty_formula(elem1165)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1170 = self._try_flat(msg, self.pretty_not)
        if flat1170 is not None:
            assert flat1170 is not None
            self.write(flat1170)
            return None
        else:
            _dollar_dollar = msg
            fields1168 = _dollar_dollar.arg
            assert fields1168 is not None
            unwrapped_fields1169 = fields1168
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1169)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1176 = self._try_flat(msg, self.pretty_ffi)
        if flat1176 is not None:
            assert flat1176 is not None
            self.write(flat1176)
            return None
        else:
            _dollar_dollar = msg
            fields1171 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1171 is not None
            unwrapped_fields1172 = fields1171
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1173 = unwrapped_fields1172[0]
            self.pretty_name(field1173)
            self.newline()
            field1174 = unwrapped_fields1172[1]
            self.pretty_ffi_args(field1174)
            self.newline()
            field1175 = unwrapped_fields1172[2]
            self.pretty_terms(field1175)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1178 = self._try_flat(msg, self.pretty_name)
        if flat1178 is not None:
            assert flat1178 is not None
            self.write(flat1178)
            return None
        else:
            fields1177 = msg
            self.write(":")
            self.write(fields1177)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1182 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1182 is not None:
            assert flat1182 is not None
            self.write(flat1182)
            return None
        else:
            fields1179 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1179) == 0:
                self.newline()
                for i1181, elem1180 in enumerate(fields1179):
                    if (i1181 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1180)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1189 = self._try_flat(msg, self.pretty_atom)
        if flat1189 is not None:
            assert flat1189 is not None
            self.write(flat1189)
            return None
        else:
            _dollar_dollar = msg
            fields1183 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1183 is not None
            unwrapped_fields1184 = fields1183
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1185 = unwrapped_fields1184[0]
            self.pretty_relation_id(field1185)
            field1186 = unwrapped_fields1184[1]
            if not len(field1186) == 0:
                self.newline()
                for i1188, elem1187 in enumerate(field1186):
                    if (i1188 > 0):
                        self.newline()
                    self.pretty_term(elem1187)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1196 = self._try_flat(msg, self.pretty_pragma)
        if flat1196 is not None:
            assert flat1196 is not None
            self.write(flat1196)
            return None
        else:
            _dollar_dollar = msg
            fields1190 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1190 is not None
            unwrapped_fields1191 = fields1190
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1192 = unwrapped_fields1191[0]
            self.pretty_name(field1192)
            field1193 = unwrapped_fields1191[1]
            if not len(field1193) == 0:
                self.newline()
                for i1195, elem1194 in enumerate(field1193):
                    if (i1195 > 0):
                        self.newline()
                    self.pretty_term(elem1194)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1212 = self._try_flat(msg, self.pretty_primitive)
        if flat1212 is not None:
            assert flat1212 is not None
            self.write(flat1212)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1794 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1794 = None
            guard_result1211 = _t1794
            if guard_result1211 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1795 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1795 = None
                guard_result1210 = _t1795
                if guard_result1210 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1796 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1796 = None
                    guard_result1209 = _t1796
                    if guard_result1209 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1797 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1797 = None
                        guard_result1208 = _t1797
                        if guard_result1208 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1798 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1798 = None
                            guard_result1207 = _t1798
                            if guard_result1207 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1799 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1799 = None
                                guard_result1206 = _t1799
                                if guard_result1206 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1800 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1800 = None
                                    guard_result1205 = _t1800
                                    if guard_result1205 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1801 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1801 = None
                                        guard_result1204 = _t1801
                                        if guard_result1204 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1802 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1802 = None
                                            guard_result1203 = _t1802
                                            if guard_result1203 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1197 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1197 is not None
                                                unwrapped_fields1198 = fields1197
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1199 = unwrapped_fields1198[0]
                                                self.pretty_name(field1199)
                                                field1200 = unwrapped_fields1198[1]
                                                if not len(field1200) == 0:
                                                    self.newline()
                                                    for i1202, elem1201 in enumerate(field1200):
                                                        if (i1202 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1201)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1217 = self._try_flat(msg, self.pretty_eq)
        if flat1217 is not None:
            assert flat1217 is not None
            self.write(flat1217)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1803 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1803 = None
            fields1213 = _t1803
            assert fields1213 is not None
            unwrapped_fields1214 = fields1213
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1215 = unwrapped_fields1214[0]
            self.pretty_term(field1215)
            self.newline()
            field1216 = unwrapped_fields1214[1]
            self.pretty_term(field1216)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1222 = self._try_flat(msg, self.pretty_lt)
        if flat1222 is not None:
            assert flat1222 is not None
            self.write(flat1222)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1804 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1804 = None
            fields1218 = _t1804
            assert fields1218 is not None
            unwrapped_fields1219 = fields1218
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1220 = unwrapped_fields1219[0]
            self.pretty_term(field1220)
            self.newline()
            field1221 = unwrapped_fields1219[1]
            self.pretty_term(field1221)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1227 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1227 is not None:
            assert flat1227 is not None
            self.write(flat1227)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1805 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1805 = None
            fields1223 = _t1805
            assert fields1223 is not None
            unwrapped_fields1224 = fields1223
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1225 = unwrapped_fields1224[0]
            self.pretty_term(field1225)
            self.newline()
            field1226 = unwrapped_fields1224[1]
            self.pretty_term(field1226)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1232 = self._try_flat(msg, self.pretty_gt)
        if flat1232 is not None:
            assert flat1232 is not None
            self.write(flat1232)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1806 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1806 = None
            fields1228 = _t1806
            assert fields1228 is not None
            unwrapped_fields1229 = fields1228
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1230 = unwrapped_fields1229[0]
            self.pretty_term(field1230)
            self.newline()
            field1231 = unwrapped_fields1229[1]
            self.pretty_term(field1231)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1237 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1237 is not None:
            assert flat1237 is not None
            self.write(flat1237)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1807 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1807 = None
            fields1233 = _t1807
            assert fields1233 is not None
            unwrapped_fields1234 = fields1233
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1235 = unwrapped_fields1234[0]
            self.pretty_term(field1235)
            self.newline()
            field1236 = unwrapped_fields1234[1]
            self.pretty_term(field1236)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1243 = self._try_flat(msg, self.pretty_add)
        if flat1243 is not None:
            assert flat1243 is not None
            self.write(flat1243)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1808 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1808 = None
            fields1238 = _t1808
            assert fields1238 is not None
            unwrapped_fields1239 = fields1238
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1240 = unwrapped_fields1239[0]
            self.pretty_term(field1240)
            self.newline()
            field1241 = unwrapped_fields1239[1]
            self.pretty_term(field1241)
            self.newline()
            field1242 = unwrapped_fields1239[2]
            self.pretty_term(field1242)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1249 = self._try_flat(msg, self.pretty_minus)
        if flat1249 is not None:
            assert flat1249 is not None
            self.write(flat1249)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1809 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1809 = None
            fields1244 = _t1809
            assert fields1244 is not None
            unwrapped_fields1245 = fields1244
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1246 = unwrapped_fields1245[0]
            self.pretty_term(field1246)
            self.newline()
            field1247 = unwrapped_fields1245[1]
            self.pretty_term(field1247)
            self.newline()
            field1248 = unwrapped_fields1245[2]
            self.pretty_term(field1248)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1255 = self._try_flat(msg, self.pretty_multiply)
        if flat1255 is not None:
            assert flat1255 is not None
            self.write(flat1255)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1810 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1810 = None
            fields1250 = _t1810
            assert fields1250 is not None
            unwrapped_fields1251 = fields1250
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1252 = unwrapped_fields1251[0]
            self.pretty_term(field1252)
            self.newline()
            field1253 = unwrapped_fields1251[1]
            self.pretty_term(field1253)
            self.newline()
            field1254 = unwrapped_fields1251[2]
            self.pretty_term(field1254)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1261 = self._try_flat(msg, self.pretty_divide)
        if flat1261 is not None:
            assert flat1261 is not None
            self.write(flat1261)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1811 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1811 = None
            fields1256 = _t1811
            assert fields1256 is not None
            unwrapped_fields1257 = fields1256
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1258 = unwrapped_fields1257[0]
            self.pretty_term(field1258)
            self.newline()
            field1259 = unwrapped_fields1257[1]
            self.pretty_term(field1259)
            self.newline()
            field1260 = unwrapped_fields1257[2]
            self.pretty_term(field1260)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1266 = self._try_flat(msg, self.pretty_rel_term)
        if flat1266 is not None:
            assert flat1266 is not None
            self.write(flat1266)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1812 = _dollar_dollar.specialized_value
            else:
                _t1812 = None
            deconstruct_result1264 = _t1812
            if deconstruct_result1264 is not None:
                assert deconstruct_result1264 is not None
                unwrapped1265 = deconstruct_result1264
                self.pretty_specialized_value(unwrapped1265)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1813 = _dollar_dollar.term
                else:
                    _t1813 = None
                deconstruct_result1262 = _t1813
                if deconstruct_result1262 is not None:
                    assert deconstruct_result1262 is not None
                    unwrapped1263 = deconstruct_result1262
                    self.pretty_term(unwrapped1263)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1268 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1268 is not None:
            assert flat1268 is not None
            self.write(flat1268)
            return None
        else:
            fields1267 = msg
            self.write("#")
            self.pretty_raw_value(fields1267)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1275 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1275 is not None:
            assert flat1275 is not None
            self.write(flat1275)
            return None
        else:
            _dollar_dollar = msg
            fields1269 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1269 is not None
            unwrapped_fields1270 = fields1269
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1271 = unwrapped_fields1270[0]
            self.pretty_name(field1271)
            field1272 = unwrapped_fields1270[1]
            if not len(field1272) == 0:
                self.newline()
                for i1274, elem1273 in enumerate(field1272):
                    if (i1274 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1273)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1280 = self._try_flat(msg, self.pretty_cast)
        if flat1280 is not None:
            assert flat1280 is not None
            self.write(flat1280)
            return None
        else:
            _dollar_dollar = msg
            fields1276 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1276 is not None
            unwrapped_fields1277 = fields1276
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1278 = unwrapped_fields1277[0]
            self.pretty_term(field1278)
            self.newline()
            field1279 = unwrapped_fields1277[1]
            self.pretty_term(field1279)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1284 = self._try_flat(msg, self.pretty_attrs)
        if flat1284 is not None:
            assert flat1284 is not None
            self.write(flat1284)
            return None
        else:
            fields1281 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1281) == 0:
                self.newline()
                for i1283, elem1282 in enumerate(fields1281):
                    if (i1283 > 0):
                        self.newline()
                    self.pretty_attribute(elem1282)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1291 = self._try_flat(msg, self.pretty_attribute)
        if flat1291 is not None:
            assert flat1291 is not None
            self.write(flat1291)
            return None
        else:
            _dollar_dollar = msg
            fields1285 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1285 is not None
            unwrapped_fields1286 = fields1285
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1287 = unwrapped_fields1286[0]
            self.pretty_name(field1287)
            field1288 = unwrapped_fields1286[1]
            if not len(field1288) == 0:
                self.newline()
                for i1290, elem1289 in enumerate(field1288):
                    if (i1290 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1289)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1300 = self._try_flat(msg, self.pretty_algorithm)
        if flat1300 is not None:
            assert flat1300 is not None
            self.write(flat1300)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1814 = _dollar_dollar.attrs
            else:
                _t1814 = None
            fields1292 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body, _t1814,)
            assert fields1292 is not None
            unwrapped_fields1293 = fields1292
            self.write("(algorithm")
            self.indent_sexp()
            field1294 = unwrapped_fields1293[0]
            if not len(field1294) == 0:
                self.newline()
                for i1296, elem1295 in enumerate(field1294):
                    if (i1296 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1295)
            self.newline()
            field1297 = unwrapped_fields1293[1]
            self.pretty_script(field1297)
            field1298 = unwrapped_fields1293[2]
            if field1298 is not None:
                self.newline()
                assert field1298 is not None
                opt_val1299 = field1298
                self.pretty_attrs(opt_val1299)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1305 = self._try_flat(msg, self.pretty_script)
        if flat1305 is not None:
            assert flat1305 is not None
            self.write(flat1305)
            return None
        else:
            _dollar_dollar = msg
            fields1301 = _dollar_dollar.constructs
            assert fields1301 is not None
            unwrapped_fields1302 = fields1301
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1302) == 0:
                self.newline()
                for i1304, elem1303 in enumerate(unwrapped_fields1302):
                    if (i1304 > 0):
                        self.newline()
                    self.pretty_construct(elem1303)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1310 = self._try_flat(msg, self.pretty_construct)
        if flat1310 is not None:
            assert flat1310 is not None
            self.write(flat1310)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1815 = _dollar_dollar.loop
            else:
                _t1815 = None
            deconstruct_result1308 = _t1815
            if deconstruct_result1308 is not None:
                assert deconstruct_result1308 is not None
                unwrapped1309 = deconstruct_result1308
                self.pretty_loop(unwrapped1309)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1816 = _dollar_dollar.instruction
                else:
                    _t1816 = None
                deconstruct_result1306 = _t1816
                if deconstruct_result1306 is not None:
                    assert deconstruct_result1306 is not None
                    unwrapped1307 = deconstruct_result1306
                    self.pretty_instruction(unwrapped1307)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1317 = self._try_flat(msg, self.pretty_loop)
        if flat1317 is not None:
            assert flat1317 is not None
            self.write(flat1317)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1817 = _dollar_dollar.attrs
            else:
                _t1817 = None
            fields1311 = (_dollar_dollar.init, _dollar_dollar.body, _t1817,)
            assert fields1311 is not None
            unwrapped_fields1312 = fields1311
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1313 = unwrapped_fields1312[0]
            self.pretty_init(field1313)
            self.newline()
            field1314 = unwrapped_fields1312[1]
            self.pretty_script(field1314)
            field1315 = unwrapped_fields1312[2]
            if field1315 is not None:
                self.newline()
                assert field1315 is not None
                opt_val1316 = field1315
                self.pretty_attrs(opt_val1316)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1321 = self._try_flat(msg, self.pretty_init)
        if flat1321 is not None:
            assert flat1321 is not None
            self.write(flat1321)
            return None
        else:
            fields1318 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1318) == 0:
                self.newline()
                for i1320, elem1319 in enumerate(fields1318):
                    if (i1320 > 0):
                        self.newline()
                    self.pretty_instruction(elem1319)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1332 = self._try_flat(msg, self.pretty_instruction)
        if flat1332 is not None:
            assert flat1332 is not None
            self.write(flat1332)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1818 = _dollar_dollar.assign
            else:
                _t1818 = None
            deconstruct_result1330 = _t1818
            if deconstruct_result1330 is not None:
                assert deconstruct_result1330 is not None
                unwrapped1331 = deconstruct_result1330
                self.pretty_assign(unwrapped1331)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1819 = _dollar_dollar.upsert
                else:
                    _t1819 = None
                deconstruct_result1328 = _t1819
                if deconstruct_result1328 is not None:
                    assert deconstruct_result1328 is not None
                    unwrapped1329 = deconstruct_result1328
                    self.pretty_upsert(unwrapped1329)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1820 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1820 = None
                    deconstruct_result1326 = _t1820
                    if deconstruct_result1326 is not None:
                        assert deconstruct_result1326 is not None
                        unwrapped1327 = deconstruct_result1326
                        self.pretty_break(unwrapped1327)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1821 = _dollar_dollar.monoid_def
                        else:
                            _t1821 = None
                        deconstruct_result1324 = _t1821
                        if deconstruct_result1324 is not None:
                            assert deconstruct_result1324 is not None
                            unwrapped1325 = deconstruct_result1324
                            self.pretty_monoid_def(unwrapped1325)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1822 = _dollar_dollar.monus_def
                            else:
                                _t1822 = None
                            deconstruct_result1322 = _t1822
                            if deconstruct_result1322 is not None:
                                assert deconstruct_result1322 is not None
                                unwrapped1323 = deconstruct_result1322
                                self.pretty_monus_def(unwrapped1323)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1339 = self._try_flat(msg, self.pretty_assign)
        if flat1339 is not None:
            assert flat1339 is not None
            self.write(flat1339)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1823 = _dollar_dollar.attrs
            else:
                _t1823 = None
            fields1333 = (_dollar_dollar.name, _dollar_dollar.body, _t1823,)
            assert fields1333 is not None
            unwrapped_fields1334 = fields1333
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1335 = unwrapped_fields1334[0]
            self.pretty_relation_id(field1335)
            self.newline()
            field1336 = unwrapped_fields1334[1]
            self.pretty_abstraction(field1336)
            field1337 = unwrapped_fields1334[2]
            if field1337 is not None:
                self.newline()
                assert field1337 is not None
                opt_val1338 = field1337
                self.pretty_attrs(opt_val1338)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1346 = self._try_flat(msg, self.pretty_upsert)
        if flat1346 is not None:
            assert flat1346 is not None
            self.write(flat1346)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1824 = _dollar_dollar.attrs
            else:
                _t1824 = None
            fields1340 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1824,)
            assert fields1340 is not None
            unwrapped_fields1341 = fields1340
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1342 = unwrapped_fields1341[0]
            self.pretty_relation_id(field1342)
            self.newline()
            field1343 = unwrapped_fields1341[1]
            self.pretty_abstraction_with_arity(field1343)
            field1344 = unwrapped_fields1341[2]
            if field1344 is not None:
                self.newline()
                assert field1344 is not None
                opt_val1345 = field1344
                self.pretty_attrs(opt_val1345)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1351 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1351 is not None:
            assert flat1351 is not None
            self.write(flat1351)
            return None
        else:
            _dollar_dollar = msg
            _t1825 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1347 = (_t1825, _dollar_dollar[0].value,)
            assert fields1347 is not None
            unwrapped_fields1348 = fields1347
            self.write("(")
            self.indent()
            field1349 = unwrapped_fields1348[0]
            self.pretty_bindings(field1349)
            self.newline()
            field1350 = unwrapped_fields1348[1]
            self.pretty_formula(field1350)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1358 = self._try_flat(msg, self.pretty_break)
        if flat1358 is not None:
            assert flat1358 is not None
            self.write(flat1358)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1826 = _dollar_dollar.attrs
            else:
                _t1826 = None
            fields1352 = (_dollar_dollar.name, _dollar_dollar.body, _t1826,)
            assert fields1352 is not None
            unwrapped_fields1353 = fields1352
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1354 = unwrapped_fields1353[0]
            self.pretty_relation_id(field1354)
            self.newline()
            field1355 = unwrapped_fields1353[1]
            self.pretty_abstraction(field1355)
            field1356 = unwrapped_fields1353[2]
            if field1356 is not None:
                self.newline()
                assert field1356 is not None
                opt_val1357 = field1356
                self.pretty_attrs(opt_val1357)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1366 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1366 is not None:
            assert flat1366 is not None
            self.write(flat1366)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1827 = _dollar_dollar.attrs
            else:
                _t1827 = None
            fields1359 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1827,)
            assert fields1359 is not None
            unwrapped_fields1360 = fields1359
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1361 = unwrapped_fields1360[0]
            self.pretty_monoid(field1361)
            self.newline()
            field1362 = unwrapped_fields1360[1]
            self.pretty_relation_id(field1362)
            self.newline()
            field1363 = unwrapped_fields1360[2]
            self.pretty_abstraction_with_arity(field1363)
            field1364 = unwrapped_fields1360[3]
            if field1364 is not None:
                self.newline()
                assert field1364 is not None
                opt_val1365 = field1364
                self.pretty_attrs(opt_val1365)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1375 = self._try_flat(msg, self.pretty_monoid)
        if flat1375 is not None:
            assert flat1375 is not None
            self.write(flat1375)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1828 = _dollar_dollar.or_monoid
            else:
                _t1828 = None
            deconstruct_result1373 = _t1828
            if deconstruct_result1373 is not None:
                assert deconstruct_result1373 is not None
                unwrapped1374 = deconstruct_result1373
                self.pretty_or_monoid(unwrapped1374)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1829 = _dollar_dollar.min_monoid
                else:
                    _t1829 = None
                deconstruct_result1371 = _t1829
                if deconstruct_result1371 is not None:
                    assert deconstruct_result1371 is not None
                    unwrapped1372 = deconstruct_result1371
                    self.pretty_min_monoid(unwrapped1372)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1830 = _dollar_dollar.max_monoid
                    else:
                        _t1830 = None
                    deconstruct_result1369 = _t1830
                    if deconstruct_result1369 is not None:
                        assert deconstruct_result1369 is not None
                        unwrapped1370 = deconstruct_result1369
                        self.pretty_max_monoid(unwrapped1370)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1831 = _dollar_dollar.sum_monoid
                        else:
                            _t1831 = None
                        deconstruct_result1367 = _t1831
                        if deconstruct_result1367 is not None:
                            assert deconstruct_result1367 is not None
                            unwrapped1368 = deconstruct_result1367
                            self.pretty_sum_monoid(unwrapped1368)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1376 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1379 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1379 is not None:
            assert flat1379 is not None
            self.write(flat1379)
            return None
        else:
            _dollar_dollar = msg
            fields1377 = _dollar_dollar.type
            assert fields1377 is not None
            unwrapped_fields1378 = fields1377
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1378)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1382 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1382 is not None:
            assert flat1382 is not None
            self.write(flat1382)
            return None
        else:
            _dollar_dollar = msg
            fields1380 = _dollar_dollar.type
            assert fields1380 is not None
            unwrapped_fields1381 = fields1380
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1381)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1385 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1385 is not None:
            assert flat1385 is not None
            self.write(flat1385)
            return None
        else:
            _dollar_dollar = msg
            fields1383 = _dollar_dollar.type
            assert fields1383 is not None
            unwrapped_fields1384 = fields1383
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1384)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1393 = self._try_flat(msg, self.pretty_monus_def)
        if flat1393 is not None:
            assert flat1393 is not None
            self.write(flat1393)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1832 = _dollar_dollar.attrs
            else:
                _t1832 = None
            fields1386 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1832,)
            assert fields1386 is not None
            unwrapped_fields1387 = fields1386
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1388 = unwrapped_fields1387[0]
            self.pretty_monoid(field1388)
            self.newline()
            field1389 = unwrapped_fields1387[1]
            self.pretty_relation_id(field1389)
            self.newline()
            field1390 = unwrapped_fields1387[2]
            self.pretty_abstraction_with_arity(field1390)
            field1391 = unwrapped_fields1387[3]
            if field1391 is not None:
                self.newline()
                assert field1391 is not None
                opt_val1392 = field1391
                self.pretty_attrs(opt_val1392)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1400 = self._try_flat(msg, self.pretty_constraint)
        if flat1400 is not None:
            assert flat1400 is not None
            self.write(flat1400)
            return None
        else:
            _dollar_dollar = msg
            fields1394 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1394 is not None
            unwrapped_fields1395 = fields1394
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1396 = unwrapped_fields1395[0]
            self.pretty_relation_id(field1396)
            self.newline()
            field1397 = unwrapped_fields1395[1]
            self.pretty_abstraction(field1397)
            self.newline()
            field1398 = unwrapped_fields1395[2]
            self.pretty_functional_dependency_keys(field1398)
            self.newline()
            field1399 = unwrapped_fields1395[3]
            self.pretty_functional_dependency_values(field1399)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1404 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1404 is not None:
            assert flat1404 is not None
            self.write(flat1404)
            return None
        else:
            fields1401 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1401) == 0:
                self.newline()
                for i1403, elem1402 in enumerate(fields1401):
                    if (i1403 > 0):
                        self.newline()
                    self.pretty_var(elem1402)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1408 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1408 is not None:
            assert flat1408 is not None
            self.write(flat1408)
            return None
        else:
            fields1405 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1405) == 0:
                self.newline()
                for i1407, elem1406 in enumerate(fields1405):
                    if (i1407 > 0):
                        self.newline()
                    self.pretty_var(elem1406)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1417 = self._try_flat(msg, self.pretty_data)
        if flat1417 is not None:
            assert flat1417 is not None
            self.write(flat1417)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1833 = _dollar_dollar.edb
            else:
                _t1833 = None
            deconstruct_result1415 = _t1833
            if deconstruct_result1415 is not None:
                assert deconstruct_result1415 is not None
                unwrapped1416 = deconstruct_result1415
                self.pretty_edb(unwrapped1416)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1834 = _dollar_dollar.betree_relation
                else:
                    _t1834 = None
                deconstruct_result1413 = _t1834
                if deconstruct_result1413 is not None:
                    assert deconstruct_result1413 is not None
                    unwrapped1414 = deconstruct_result1413
                    self.pretty_betree_relation(unwrapped1414)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1835 = _dollar_dollar.csv_data
                    else:
                        _t1835 = None
                    deconstruct_result1411 = _t1835
                    if deconstruct_result1411 is not None:
                        assert deconstruct_result1411 is not None
                        unwrapped1412 = deconstruct_result1411
                        self.pretty_csv_data(unwrapped1412)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1836 = _dollar_dollar.iceberg_data
                        else:
                            _t1836 = None
                        deconstruct_result1409 = _t1836
                        if deconstruct_result1409 is not None:
                            assert deconstruct_result1409 is not None
                            unwrapped1410 = deconstruct_result1409
                            self.pretty_iceberg_data(unwrapped1410)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1423 = self._try_flat(msg, self.pretty_edb)
        if flat1423 is not None:
            assert flat1423 is not None
            self.write(flat1423)
            return None
        else:
            _dollar_dollar = msg
            fields1418 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1418 is not None
            unwrapped_fields1419 = fields1418
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1420 = unwrapped_fields1419[0]
            self.pretty_relation_id(field1420)
            self.newline()
            field1421 = unwrapped_fields1419[1]
            self.pretty_edb_path(field1421)
            self.newline()
            field1422 = unwrapped_fields1419[2]
            self.pretty_edb_types(field1422)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1427 = self._try_flat(msg, self.pretty_edb_path)
        if flat1427 is not None:
            assert flat1427 is not None
            self.write(flat1427)
            return None
        else:
            fields1424 = msg
            self.write("[")
            self.indent()
            for i1426, elem1425 in enumerate(fields1424):
                if (i1426 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1425))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1431 = self._try_flat(msg, self.pretty_edb_types)
        if flat1431 is not None:
            assert flat1431 is not None
            self.write(flat1431)
            return None
        else:
            fields1428 = msg
            self.write("[")
            self.indent()
            for i1430, elem1429 in enumerate(fields1428):
                if (i1430 > 0):
                    self.newline()
                self.pretty_type(elem1429)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1436 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1436 is not None:
            assert flat1436 is not None
            self.write(flat1436)
            return None
        else:
            _dollar_dollar = msg
            fields1432 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1432 is not None
            unwrapped_fields1433 = fields1432
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1434 = unwrapped_fields1433[0]
            self.pretty_relation_id(field1434)
            self.newline()
            field1435 = unwrapped_fields1433[1]
            self.pretty_betree_info(field1435)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1442 = self._try_flat(msg, self.pretty_betree_info)
        if flat1442 is not None:
            assert flat1442 is not None
            self.write(flat1442)
            return None
        else:
            _dollar_dollar = msg
            _t1837 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1437 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1837,)
            assert fields1437 is not None
            unwrapped_fields1438 = fields1437
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1439 = unwrapped_fields1438[0]
            self.pretty_betree_info_key_types(field1439)
            self.newline()
            field1440 = unwrapped_fields1438[1]
            self.pretty_betree_info_value_types(field1440)
            self.newline()
            field1441 = unwrapped_fields1438[2]
            self.pretty_config_dict(field1441)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1446 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1446 is not None:
            assert flat1446 is not None
            self.write(flat1446)
            return None
        else:
            fields1443 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1443) == 0:
                self.newline()
                for i1445, elem1444 in enumerate(fields1443):
                    if (i1445 > 0):
                        self.newline()
                    self.pretty_type(elem1444)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1450 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1450 is not None:
            assert flat1450 is not None
            self.write(flat1450)
            return None
        else:
            fields1447 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1447) == 0:
                self.newline()
                for i1449, elem1448 in enumerate(fields1447):
                    if (i1449 > 0):
                        self.newline()
                    self.pretty_type(elem1448)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1460 = self._try_flat(msg, self.pretty_csv_data)
        if flat1460 is not None:
            assert flat1460 is not None
            self.write(flat1460)
            return None
        else:
            _dollar_dollar = msg
            _t1838 = self.deconstruct_csv_data_columns_optional(_dollar_dollar)
            _t1839 = self.deconstruct_csv_data_relations_optional(_dollar_dollar)
            fields1451 = (_dollar_dollar.locator, _dollar_dollar.config, _t1838, _t1839, _dollar_dollar.asof,)
            assert fields1451 is not None
            unwrapped_fields1452 = fields1451
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1453 = unwrapped_fields1452[0]
            self.pretty_csvlocator(field1453)
            self.newline()
            field1454 = unwrapped_fields1452[1]
            self.pretty_csv_config(field1454)
            field1455 = unwrapped_fields1452[2]
            if field1455 is not None:
                self.newline()
                assert field1455 is not None
                opt_val1456 = field1455
                self.pretty_gnf_columns(opt_val1456)
            field1457 = unwrapped_fields1452[3]
            if field1457 is not None:
                self.newline()
                assert field1457 is not None
                opt_val1458 = field1457
                self.pretty_target_relations(opt_val1458)
            self.newline()
            field1459 = unwrapped_fields1452[4]
            self.pretty_csv_asof(field1459)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1467 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1467 is not None:
            assert flat1467 is not None
            self.write(flat1467)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1840 = _dollar_dollar.paths
            else:
                _t1840 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1841 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1841 = None
            fields1461 = (_t1840, _t1841,)
            assert fields1461 is not None
            unwrapped_fields1462 = fields1461
            self.write("(csv_locator")
            self.indent_sexp()
            field1463 = unwrapped_fields1462[0]
            if field1463 is not None:
                self.newline()
                assert field1463 is not None
                opt_val1464 = field1463
                self.pretty_csv_locator_paths(opt_val1464)
            field1465 = unwrapped_fields1462[1]
            if field1465 is not None:
                self.newline()
                assert field1465 is not None
                opt_val1466 = field1465
                self.pretty_csv_locator_inline_data(opt_val1466)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1471 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1471 is not None:
            assert flat1471 is not None
            self.write(flat1471)
            return None
        else:
            fields1468 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1468) == 0:
                self.newline()
                for i1470, elem1469 in enumerate(fields1468):
                    if (i1470 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1469))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1473 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1473 is not None:
            assert flat1473 is not None
            self.write(flat1473)
            return None
        else:
            fields1472 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1472))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1479 = self._try_flat(msg, self.pretty_csv_config)
        if flat1479 is not None:
            assert flat1479 is not None
            self.write(flat1479)
            return None
        else:
            _dollar_dollar = msg
            _t1842 = self.deconstruct_csv_config(_dollar_dollar)
            _t1843 = self.deconstruct_csv_storage_integration_optional(_dollar_dollar)
            fields1474 = (_t1842, _t1843,)
            assert fields1474 is not None
            unwrapped_fields1475 = fields1474
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            field1476 = unwrapped_fields1475[0]
            self.pretty_config_dict(field1476)
            field1477 = unwrapped_fields1475[1]
            if field1477 is not None:
                self.newline()
                assert field1477 is not None
                opt_val1478 = field1477
                self.pretty__storage_integration(opt_val1478)
            self.dedent()
            self.write(")")

    def pretty__storage_integration(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat1481 = self._try_flat(msg, self.pretty__storage_integration)
        if flat1481 is not None:
            assert flat1481 is not None
            self.write(flat1481)
            return None
        else:
            fields1480 = msg
            self.write("(storage_integration")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(fields1480)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1485 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1485 is not None:
            assert flat1485 is not None
            self.write(flat1485)
            return None
        else:
            fields1482 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1482) == 0:
                self.newline()
                for i1484, elem1483 in enumerate(fields1482):
                    if (i1484 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1483)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1494 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1494 is not None:
            assert flat1494 is not None
            self.write(flat1494)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1844 = _dollar_dollar.target_id
            else:
                _t1844 = None
            fields1486 = (_dollar_dollar.column_path, _t1844, _dollar_dollar.types,)
            assert fields1486 is not None
            unwrapped_fields1487 = fields1486
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1488 = unwrapped_fields1487[0]
            self.pretty_gnf_column_path(field1488)
            field1489 = unwrapped_fields1487[1]
            if field1489 is not None:
                self.newline()
                assert field1489 is not None
                opt_val1490 = field1489
                self.pretty_relation_id(opt_val1490)
            self.newline()
            self.write("[")
            field1491 = unwrapped_fields1487[2]
            for i1493, elem1492 in enumerate(field1491):
                if (i1493 > 0):
                    self.newline()
                self.pretty_type(elem1492)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1501 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1501 is not None:
            assert flat1501 is not None
            self.write(flat1501)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1845 = _dollar_dollar[0]
            else:
                _t1845 = None
            deconstruct_result1499 = _t1845
            if deconstruct_result1499 is not None:
                assert deconstruct_result1499 is not None
                unwrapped1500 = deconstruct_result1499
                self.write(self.format_string_value(unwrapped1500))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1846 = _dollar_dollar
                else:
                    _t1846 = None
                deconstruct_result1495 = _t1846
                if deconstruct_result1495 is not None:
                    assert deconstruct_result1495 is not None
                    unwrapped1496 = deconstruct_result1495
                    self.write("[")
                    self.indent()
                    for i1498, elem1497 in enumerate(unwrapped1496):
                        if (i1498 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1497))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_target_relations(self, msg: logic_pb2.TargetRelations):
        flat1508 = self._try_flat(msg, self.pretty_target_relations)
        if flat1508 is not None:
            assert flat1508 is not None
            self.write(flat1508)
            return None
        else:
            _dollar_dollar = msg
            _t1847 = self.deconstruct_relation_keys(_dollar_dollar)
            _t1848 = self.deconstruct_load_errors_optional(_dollar_dollar)
            fields1502 = (_t1847, _dollar_dollar, _t1848,)
            assert fields1502 is not None
            unwrapped_fields1503 = fields1502
            self.write("(relations")
            self.indent_sexp()
            self.newline()
            field1504 = unwrapped_fields1503[0]
            self.pretty_relation_keys(field1504)
            self.newline()
            field1505 = unwrapped_fields1503[1]
            self.pretty_relation_body(field1505)
            field1506 = unwrapped_fields1503[2]
            if field1506 is not None:
                self.newline()
                assert field1506 is not None
                opt_val1507 = field1506
                self.pretty_load_errors(opt_val1507)
            self.dedent()
            self.write(")")

    def pretty_relation_keys(self, msg: tuple[Sequence[logic_pb2.NamedColumn], bool]):
        flat1515 = self._try_flat(msg, self.pretty_relation_keys)
        if flat1515 is not None:
            assert flat1515 is not None
            self.write(flat1515)
            return None
        else:
            _dollar_dollar = msg
            if not _dollar_dollar[1]:
                _t1849 = _dollar_dollar[0]
            else:
                _t1849 = None
            deconstruct_result1511 = _t1849
            if deconstruct_result1511 is not None:
                assert deconstruct_result1511 is not None
                unwrapped1512 = deconstruct_result1511
                self.write("(keys")
                self.indent_sexp()
                if not len(unwrapped1512) == 0:
                    self.newline()
                    for i1514, elem1513 in enumerate(unwrapped1512):
                        if (i1514 > 0):
                            self.newline()
                        self.pretty_named_column(elem1513)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar[1]:
                    _t1850 = ()
                else:
                    _t1850 = None
                deconstruct_result1509 = _t1850
                if deconstruct_result1509 is not None:
                    assert deconstruct_result1509 is not None
                    unwrapped1510 = deconstruct_result1509
                    self.write("(keys")
                    self.newline()
                    self.write("synthetic)")
                else:
                    raise ParseError("No matching rule for relation_keys")

    def pretty_named_column(self, msg: logic_pb2.NamedColumn):
        flat1520 = self._try_flat(msg, self.pretty_named_column)
        if flat1520 is not None:
            assert flat1520 is not None
            self.write(flat1520)
            return None
        else:
            _dollar_dollar = msg
            fields1516 = (_dollar_dollar.name, _dollar_dollar.type,)
            assert fields1516 is not None
            unwrapped_fields1517 = fields1516
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1518 = unwrapped_fields1517[0]
            self.write(self.format_string_value(field1518))
            self.newline()
            field1519 = unwrapped_fields1517[1]
            self.pretty_type(field1519)
            self.dedent()
            self.write(")")

    def pretty_relation_body(self, msg: logic_pb2.TargetRelations):
        flat1527 = self._try_flat(msg, self.pretty_relation_body)
        if flat1527 is not None:
            assert flat1527 is not None
            self.write(flat1527)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("plain"):
                _t1851 = _dollar_dollar.plain.targets
            else:
                _t1851 = None
            deconstruct_result1525 = _t1851
            if deconstruct_result1525 is not None:
                assert deconstruct_result1525 is not None
                unwrapped1526 = deconstruct_result1525
                self.pretty_non_cdc_relations(unwrapped1526)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("cdc"):
                    _t1852 = (_dollar_dollar.cdc.inserts, _dollar_dollar.cdc.deletes,)
                else:
                    _t1852 = None
                deconstruct_result1521 = _t1852
                if deconstruct_result1521 is not None:
                    assert deconstruct_result1521 is not None
                    unwrapped1522 = deconstruct_result1521
                    field1523 = unwrapped1522[0]
                    self.pretty_cdc_inserts(field1523)
                    self.write(" ")
                    field1524 = unwrapped1522[1]
                    self.pretty_cdc_deletes(field1524)
                else:
                    raise ParseError("No matching rule for relation_body")

    def pretty_non_cdc_relations(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1531 = self._try_flat(msg, self.pretty_non_cdc_relations)
        if flat1531 is not None:
            assert flat1531 is not None
            self.write(flat1531)
            return None
        else:
            fields1528 = msg
            for i1530, elem1529 in enumerate(fields1528):
                if (i1530 > 0):
                    self.newline()
                self.pretty_target_relation(elem1529)

    def pretty_target_relation(self, msg: logic_pb2.TargetRelation):
        flat1538 = self._try_flat(msg, self.pretty_target_relation)
        if flat1538 is not None:
            assert flat1538 is not None
            self.write(flat1538)
            return None
        else:
            _dollar_dollar = msg
            fields1532 = (_dollar_dollar.target_id, _dollar_dollar.values,)
            assert fields1532 is not None
            unwrapped_fields1533 = fields1532
            self.write("(relation")
            self.indent_sexp()
            self.newline()
            field1534 = unwrapped_fields1533[0]
            self.pretty_relation_id(field1534)
            field1535 = unwrapped_fields1533[1]
            if not len(field1535) == 0:
                self.newline()
                for i1537, elem1536 in enumerate(field1535):
                    if (i1537 > 0):
                        self.newline()
                    self.pretty_named_column(elem1536)
            self.dedent()
            self.write(")")

    def pretty_cdc_inserts(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1542 = self._try_flat(msg, self.pretty_cdc_inserts)
        if flat1542 is not None:
            assert flat1542 is not None
            self.write(flat1542)
            return None
        else:
            fields1539 = msg
            self.write("(inserts")
            self.indent_sexp()
            if not len(fields1539) == 0:
                self.newline()
                for i1541, elem1540 in enumerate(fields1539):
                    if (i1541 > 0):
                        self.newline()
                    self.pretty_target_relation(elem1540)
            self.dedent()
            self.write(")")

    def pretty_cdc_deletes(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1546 = self._try_flat(msg, self.pretty_cdc_deletes)
        if flat1546 is not None:
            assert flat1546 is not None
            self.write(flat1546)
            return None
        else:
            fields1543 = msg
            self.write("(deletes")
            self.indent_sexp()
            if not len(fields1543) == 0:
                self.newline()
                for i1545, elem1544 in enumerate(fields1543):
                    if (i1545 > 0):
                        self.newline()
                    self.pretty_target_relation(elem1544)
            self.dedent()
            self.write(")")

    def pretty_load_errors(self, msg: logic_pb2.RelationId):
        flat1548 = self._try_flat(msg, self.pretty_load_errors)
        if flat1548 is not None:
            assert flat1548 is not None
            self.write(flat1548)
            return None
        else:
            fields1547 = msg
            self.write("(load_errors")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1547)
            self.dedent()
            self.write(")")

    def pretty_csv_asof(self, msg: str):
        flat1550 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1550 is not None:
            assert flat1550 is not None
            self.write(flat1550)
            return None
        else:
            fields1549 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1549))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1561 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1561 is not None:
            assert flat1561 is not None
            self.write(flat1561)
            return None
        else:
            _dollar_dollar = msg
            _t1853 = self.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
            _t1854 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1551 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1853, _t1854, _dollar_dollar.returns_delta,)
            assert fields1551 is not None
            unwrapped_fields1552 = fields1551
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1553 = unwrapped_fields1552[0]
            self.pretty_iceberg_locator(field1553)
            self.newline()
            field1554 = unwrapped_fields1552[1]
            self.pretty_iceberg_catalog_config(field1554)
            self.newline()
            field1555 = unwrapped_fields1552[2]
            self.pretty_gnf_columns(field1555)
            field1556 = unwrapped_fields1552[3]
            if field1556 is not None:
                self.newline()
                assert field1556 is not None
                opt_val1557 = field1556
                self.pretty_iceberg_from_snapshot(opt_val1557)
            field1558 = unwrapped_fields1552[4]
            if field1558 is not None:
                self.newline()
                assert field1558 is not None
                opt_val1559 = field1558
                self.pretty_iceberg_to_snapshot(opt_val1559)
            self.newline()
            field1560 = unwrapped_fields1552[5]
            self.pretty_boolean_value(field1560)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1567 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1567 is not None:
            assert flat1567 is not None
            self.write(flat1567)
            return None
        else:
            _dollar_dollar = msg
            fields1562 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1562 is not None
            unwrapped_fields1563 = fields1562
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            field1564 = unwrapped_fields1563[0]
            self.pretty_iceberg_locator_table_name(field1564)
            self.newline()
            field1565 = unwrapped_fields1563[1]
            self.pretty_iceberg_locator_namespace(field1565)
            self.newline()
            field1566 = unwrapped_fields1563[2]
            self.pretty_iceberg_locator_warehouse(field1566)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_table_name(self, msg: str):
        flat1569 = self._try_flat(msg, self.pretty_iceberg_locator_table_name)
        if flat1569 is not None:
            assert flat1569 is not None
            self.write(flat1569)
            return None
        else:
            fields1568 = msg
            self.write("(table_name")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1568))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_namespace(self, msg: Sequence[str]):
        flat1573 = self._try_flat(msg, self.pretty_iceberg_locator_namespace)
        if flat1573 is not None:
            assert flat1573 is not None
            self.write(flat1573)
            return None
        else:
            fields1570 = msg
            self.write("(namespace")
            self.indent_sexp()
            if not len(fields1570) == 0:
                self.newline()
                for i1572, elem1571 in enumerate(fields1570):
                    if (i1572 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1571))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_warehouse(self, msg: str):
        flat1575 = self._try_flat(msg, self.pretty_iceberg_locator_warehouse)
        if flat1575 is not None:
            assert flat1575 is not None
            self.write(flat1575)
            return None
        else:
            fields1574 = msg
            self.write("(warehouse")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1574))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1583 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1583 is not None:
            assert flat1583 is not None
            self.write(flat1583)
            return None
        else:
            _dollar_dollar = msg
            _t1855 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1576 = (_dollar_dollar.catalog_uri, _t1855, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1576 is not None
            unwrapped_fields1577 = fields1576
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            field1578 = unwrapped_fields1577[0]
            self.pretty_iceberg_catalog_uri(field1578)
            field1579 = unwrapped_fields1577[1]
            if field1579 is not None:
                self.newline()
                assert field1579 is not None
                opt_val1580 = field1579
                self.pretty_iceberg_catalog_config_scope(opt_val1580)
            self.newline()
            field1581 = unwrapped_fields1577[2]
            self.pretty_iceberg_properties(field1581)
            self.newline()
            field1582 = unwrapped_fields1577[3]
            self.pretty_iceberg_auth_properties(field1582)
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_uri(self, msg: str):
        flat1585 = self._try_flat(msg, self.pretty_iceberg_catalog_uri)
        if flat1585 is not None:
            assert flat1585 is not None
            self.write(flat1585)
            return None
        else:
            fields1584 = msg
            self.write("(catalog_uri")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1584))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1587 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1587 is not None:
            assert flat1587 is not None
            self.write(flat1587)
            return None
        else:
            fields1586 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1586))
            self.dedent()
            self.write(")")

    def pretty_iceberg_properties(self, msg: Sequence[tuple[str, str]]):
        flat1591 = self._try_flat(msg, self.pretty_iceberg_properties)
        if flat1591 is not None:
            assert flat1591 is not None
            self.write(flat1591)
            return None
        else:
            fields1588 = msg
            self.write("(properties")
            self.indent_sexp()
            if not len(fields1588) == 0:
                self.newline()
                for i1590, elem1589 in enumerate(fields1588):
                    if (i1590 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1589)
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1596 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1596 is not None:
            assert flat1596 is not None
            self.write(flat1596)
            return None
        else:
            _dollar_dollar = msg
            fields1592 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1592 is not None
            unwrapped_fields1593 = fields1592
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1594 = unwrapped_fields1593[0]
            self.write(self.format_string_value(field1594))
            self.newline()
            field1595 = unwrapped_fields1593[1]
            self.write(self.format_string_value(field1595))
            self.dedent()
            self.write(")")

    def pretty_iceberg_auth_properties(self, msg: Sequence[tuple[str, str]]):
        flat1600 = self._try_flat(msg, self.pretty_iceberg_auth_properties)
        if flat1600 is not None:
            assert flat1600 is not None
            self.write(flat1600)
            return None
        else:
            fields1597 = msg
            self.write("(auth_properties")
            self.indent_sexp()
            if not len(fields1597) == 0:
                self.newline()
                for i1599, elem1598 in enumerate(fields1597):
                    if (i1599 > 0):
                        self.newline()
                    self.pretty_iceberg_masked_property_entry(elem1598)
            self.dedent()
            self.write(")")

    def pretty_iceberg_masked_property_entry(self, msg: tuple[str, str]):
        flat1605 = self._try_flat(msg, self.pretty_iceberg_masked_property_entry)
        if flat1605 is not None:
            assert flat1605 is not None
            self.write(flat1605)
            return None
        else:
            _dollar_dollar = msg
            _t1856 = self.mask_secret_value(_dollar_dollar)
            fields1601 = (_dollar_dollar[0], _t1856,)
            assert fields1601 is not None
            unwrapped_fields1602 = fields1601
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1603 = unwrapped_fields1602[0]
            self.write(self.format_string_value(field1603))
            self.newline()
            field1604 = unwrapped_fields1602[1]
            self.write(self.format_string_value(field1604))
            self.dedent()
            self.write(")")

    def pretty_iceberg_from_snapshot(self, msg: str):
        flat1607 = self._try_flat(msg, self.pretty_iceberg_from_snapshot)
        if flat1607 is not None:
            assert flat1607 is not None
            self.write(flat1607)
            return None
        else:
            fields1606 = msg
            self.write("(from_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1606))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1609 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1609 is not None:
            assert flat1609 is not None
            self.write(flat1609)
            return None
        else:
            fields1608 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1608))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1612 = self._try_flat(msg, self.pretty_undefine)
        if flat1612 is not None:
            assert flat1612 is not None
            self.write(flat1612)
            return None
        else:
            _dollar_dollar = msg
            fields1610 = _dollar_dollar.fragment_id
            assert fields1610 is not None
            unwrapped_fields1611 = fields1610
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1611)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1617 = self._try_flat(msg, self.pretty_context)
        if flat1617 is not None:
            assert flat1617 is not None
            self.write(flat1617)
            return None
        else:
            _dollar_dollar = msg
            fields1613 = _dollar_dollar.relations
            assert fields1613 is not None
            unwrapped_fields1614 = fields1613
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1614) == 0:
                self.newline()
                for i1616, elem1615 in enumerate(unwrapped_fields1614):
                    if (i1616 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1615)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1624 = self._try_flat(msg, self.pretty_snapshot)
        if flat1624 is not None:
            assert flat1624 is not None
            self.write(flat1624)
            return None
        else:
            _dollar_dollar = msg
            fields1618 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
            assert fields1618 is not None
            unwrapped_fields1619 = fields1618
            self.write("(snapshot")
            self.indent_sexp()
            self.newline()
            field1620 = unwrapped_fields1619[0]
            self.pretty_edb_path(field1620)
            field1621 = unwrapped_fields1619[1]
            if not len(field1621) == 0:
                self.newline()
                for i1623, elem1622 in enumerate(field1621):
                    if (i1623 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1622)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1629 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1629 is not None:
            assert flat1629 is not None
            self.write(flat1629)
            return None
        else:
            _dollar_dollar = msg
            fields1625 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1625 is not None
            unwrapped_fields1626 = fields1625
            field1627 = unwrapped_fields1626[0]
            self.pretty_edb_path(field1627)
            self.write(" ")
            field1628 = unwrapped_fields1626[1]
            self.pretty_relation_id(field1628)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1633 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1633 is not None:
            assert flat1633 is not None
            self.write(flat1633)
            return None
        else:
            fields1630 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1630) == 0:
                self.newline()
                for i1632, elem1631 in enumerate(fields1630):
                    if (i1632 > 0):
                        self.newline()
                    self.pretty_read(elem1631)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1644 = self._try_flat(msg, self.pretty_read)
        if flat1644 is not None:
            assert flat1644 is not None
            self.write(flat1644)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1857 = _dollar_dollar.demand
            else:
                _t1857 = None
            deconstruct_result1642 = _t1857
            if deconstruct_result1642 is not None:
                assert deconstruct_result1642 is not None
                unwrapped1643 = deconstruct_result1642
                self.pretty_demand(unwrapped1643)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1858 = _dollar_dollar.output
                else:
                    _t1858 = None
                deconstruct_result1640 = _t1858
                if deconstruct_result1640 is not None:
                    assert deconstruct_result1640 is not None
                    unwrapped1641 = deconstruct_result1640
                    self.pretty_output(unwrapped1641)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1859 = _dollar_dollar.what_if
                    else:
                        _t1859 = None
                    deconstruct_result1638 = _t1859
                    if deconstruct_result1638 is not None:
                        assert deconstruct_result1638 is not None
                        unwrapped1639 = deconstruct_result1638
                        self.pretty_what_if(unwrapped1639)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1860 = _dollar_dollar.abort
                        else:
                            _t1860 = None
                        deconstruct_result1636 = _t1860
                        if deconstruct_result1636 is not None:
                            assert deconstruct_result1636 is not None
                            unwrapped1637 = deconstruct_result1636
                            self.pretty_abort(unwrapped1637)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1861 = _dollar_dollar.export
                            else:
                                _t1861 = None
                            deconstruct_result1634 = _t1861
                            if deconstruct_result1634 is not None:
                                assert deconstruct_result1634 is not None
                                unwrapped1635 = deconstruct_result1634
                                self.pretty_export(unwrapped1635)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1647 = self._try_flat(msg, self.pretty_demand)
        if flat1647 is not None:
            assert flat1647 is not None
            self.write(flat1647)
            return None
        else:
            _dollar_dollar = msg
            fields1645 = _dollar_dollar.relation_id
            assert fields1645 is not None
            unwrapped_fields1646 = fields1645
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1646)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1652 = self._try_flat(msg, self.pretty_output)
        if flat1652 is not None:
            assert flat1652 is not None
            self.write(flat1652)
            return None
        else:
            _dollar_dollar = msg
            fields1648 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1648 is not None
            unwrapped_fields1649 = fields1648
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1650 = unwrapped_fields1649[0]
            self.pretty_name(field1650)
            self.newline()
            field1651 = unwrapped_fields1649[1]
            self.pretty_relation_id(field1651)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1657 = self._try_flat(msg, self.pretty_what_if)
        if flat1657 is not None:
            assert flat1657 is not None
            self.write(flat1657)
            return None
        else:
            _dollar_dollar = msg
            fields1653 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1653 is not None
            unwrapped_fields1654 = fields1653
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1655 = unwrapped_fields1654[0]
            self.pretty_name(field1655)
            self.newline()
            field1656 = unwrapped_fields1654[1]
            self.pretty_epoch(field1656)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1663 = self._try_flat(msg, self.pretty_abort)
        if flat1663 is not None:
            assert flat1663 is not None
            self.write(flat1663)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1862 = _dollar_dollar.name
            else:
                _t1862 = None
            fields1658 = (_t1862, _dollar_dollar.relation_id,)
            assert fields1658 is not None
            unwrapped_fields1659 = fields1658
            self.write("(abort")
            self.indent_sexp()
            field1660 = unwrapped_fields1659[0]
            if field1660 is not None:
                self.newline()
                assert field1660 is not None
                opt_val1661 = field1660
                self.pretty_name(opt_val1661)
            self.newline()
            field1662 = unwrapped_fields1659[1]
            self.pretty_relation_id(field1662)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1668 = self._try_flat(msg, self.pretty_export)
        if flat1668 is not None:
            assert flat1668 is not None
            self.write(flat1668)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1863 = _dollar_dollar.csv_config
            else:
                _t1863 = None
            deconstruct_result1666 = _t1863
            if deconstruct_result1666 is not None:
                assert deconstruct_result1666 is not None
                unwrapped1667 = deconstruct_result1666
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1667)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1864 = _dollar_dollar.iceberg_config
                else:
                    _t1864 = None
                deconstruct_result1664 = _t1864
                if deconstruct_result1664 is not None:
                    assert deconstruct_result1664 is not None
                    unwrapped1665 = deconstruct_result1664
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1665)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1679 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1679 is not None:
            assert flat1679 is not None
            self.write(flat1679)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1866 = self.deconstruct_export_csv_output_location(_dollar_dollar)
                _t1865 = (_t1866, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1865 = None
            deconstruct_result1674 = _t1865
            if deconstruct_result1674 is not None:
                assert deconstruct_result1674 is not None
                unwrapped1675 = deconstruct_result1674
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1676 = unwrapped1675[0]
                self.pretty_export_csv_output_location(field1676)
                self.newline()
                field1677 = unwrapped1675[1]
                self.pretty_export_csv_source(field1677)
                self.newline()
                field1678 = unwrapped1675[2]
                self.pretty_csv_config(field1678)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1868 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1867 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1868,)
                else:
                    _t1867 = None
                deconstruct_result1669 = _t1867
                if deconstruct_result1669 is not None:
                    assert deconstruct_result1669 is not None
                    unwrapped1670 = deconstruct_result1669
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1671 = unwrapped1670[0]
                    self.pretty_export_csv_path(field1671)
                    self.newline()
                    field1672 = unwrapped1670[1]
                    self.pretty_export_csv_columns_list(field1672)
                    self.newline()
                    field1673 = unwrapped1670[2]
                    self.pretty_config_dict(field1673)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_output_location(self, msg: tuple[str, str]):
        flat1684 = self._try_flat(msg, self.pretty_export_csv_output_location)
        if flat1684 is not None:
            assert flat1684 is not None
            self.write(flat1684)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar[0] != "":
                _t1869 = _dollar_dollar[0]
            else:
                _t1869 = None
            deconstruct_result1682 = _t1869
            if deconstruct_result1682 is not None:
                assert deconstruct_result1682 is not None
                unwrapped1683 = deconstruct_result1682
                self.write("(path")
                self.indent_sexp()
                self.newline()
                self.write(self.format_string_value(unwrapped1683))
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar[1] != "":
                    _t1870 = _dollar_dollar[1]
                else:
                    _t1870 = None
                deconstruct_result1680 = _t1870
                if deconstruct_result1680 is not None:
                    assert deconstruct_result1680 is not None
                    unwrapped1681 = deconstruct_result1680
                    self.write("(transaction_output_name")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_name(unwrapped1681)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_output_location")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1691 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1691 is not None:
            assert flat1691 is not None
            self.write(flat1691)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1871 = _dollar_dollar.gnf_columns.columns
            else:
                _t1871 = None
            deconstruct_result1687 = _t1871
            if deconstruct_result1687 is not None:
                assert deconstruct_result1687 is not None
                unwrapped1688 = deconstruct_result1687
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1688) == 0:
                    self.newline()
                    for i1690, elem1689 in enumerate(unwrapped1688):
                        if (i1690 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1689)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1872 = _dollar_dollar.table_def
                else:
                    _t1872 = None
                deconstruct_result1685 = _t1872
                if deconstruct_result1685 is not None:
                    assert deconstruct_result1685 is not None
                    unwrapped1686 = deconstruct_result1685
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1686)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1696 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1696 is not None:
            assert flat1696 is not None
            self.write(flat1696)
            return None
        else:
            _dollar_dollar = msg
            fields1692 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1692 is not None
            unwrapped_fields1693 = fields1692
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1694 = unwrapped_fields1693[0]
            self.write(self.format_string_value(field1694))
            self.newline()
            field1695 = unwrapped_fields1693[1]
            self.pretty_relation_id(field1695)
            self.dedent()
            self.write(")")

    def pretty_export_csv_path(self, msg: str):
        flat1698 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1698 is not None:
            assert flat1698 is not None
            self.write(flat1698)
            return None
        else:
            fields1697 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1697))
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1702 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1702 is not None:
            assert flat1702 is not None
            self.write(flat1702)
            return None
        else:
            fields1699 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1699) == 0:
                self.newline()
                for i1701, elem1700 in enumerate(fields1699):
                    if (i1701 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1700)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1711 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1711 is not None:
            assert flat1711 is not None
            self.write(flat1711)
            return None
        else:
            _dollar_dollar = msg
            _t1873 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1703 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sorted(_dollar_dollar.table_properties.items()), _t1873,)
            assert fields1703 is not None
            unwrapped_fields1704 = fields1703
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1705 = unwrapped_fields1704[0]
            self.pretty_iceberg_locator(field1705)
            self.newline()
            field1706 = unwrapped_fields1704[1]
            self.pretty_iceberg_catalog_config(field1706)
            self.newline()
            field1707 = unwrapped_fields1704[2]
            self.pretty_export_iceberg_table_def(field1707)
            self.newline()
            field1708 = unwrapped_fields1704[3]
            self.pretty_iceberg_table_properties(field1708)
            field1709 = unwrapped_fields1704[4]
            if field1709 is not None:
                self.newline()
                assert field1709 is not None
                opt_val1710 = field1709
                self.pretty_config_dict(opt_val1710)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_table_def(self, msg: logic_pb2.RelationId):
        flat1713 = self._try_flat(msg, self.pretty_export_iceberg_table_def)
        if flat1713 is not None:
            assert flat1713 is not None
            self.write(flat1713)
            return None
        else:
            fields1712 = msg
            self.write("(table_def")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1712)
            self.dedent()
            self.write(")")

    def pretty_iceberg_table_properties(self, msg: Sequence[tuple[str, str]]):
        flat1717 = self._try_flat(msg, self.pretty_iceberg_table_properties)
        if flat1717 is not None:
            assert flat1717 is not None
            self.write(flat1717)
            return None
        else:
            fields1714 = msg
            self.write("(table_properties")
            self.indent_sexp()
            if not len(fields1714) == 0:
                self.newline()
                for i1716, elem1715 in enumerate(fields1714):
                    if (i1716 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1715)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1928 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1928)
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
        elif isinstance(msg, logic_pb2.FixedType):
            self.pretty_fixed_type(msg)
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
