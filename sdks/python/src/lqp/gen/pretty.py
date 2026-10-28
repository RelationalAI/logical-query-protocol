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
            _t1882 = None
        return None

    def deconstruct_csv_data_columns_optional(self, msg: logic_pb2.CSVData) -> Sequence[logic_pb2.GNFColumn] | None:
        if msg.HasField("relations"):
            return None
        else:
            _t1883 = None
        return msg.columns

    def deconstruct_csv_data_relations_optional(self, msg: logic_pb2.CSVData) -> logic_pb2.TargetRelations | None:
        if msg.HasField("relations"):
            assert msg.relations is not None
            return msg.relations
        else:
            _t1884 = None
        return None

    def deconstruct_export_csv_output_location(self, msg: transactions_pb2.ExportCSVConfig) -> tuple[str, str]:
        return (msg.path, msg.transaction_output_name,)

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1885 = logic_pb2.Value(int32_value=v)
        return _t1885

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1886 = logic_pb2.Value(int_value=v)
        return _t1886

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1887 = logic_pb2.Value(float_value=v)
        return _t1887

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1888 = logic_pb2.Value(string_value=v)
        return _t1888

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1889 = logic_pb2.Value(boolean_value=v)
        return _t1889

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1890 = logic_pb2.Value(uint128_value=v)
        return _t1890

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1891 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1891,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1892 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1892,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1893 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1893,))
        _t1894 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1894,))
        for pair in sorted(msg.configuration_values.items()):
            result.append(pair)
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1895 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1895,))
        _t1896 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1896,))
        if msg.new_line != "":
            _t1897 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1897,))
        _t1898 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1898,))
        _t1899 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1899,))
        _t1900 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1900,))
        if msg.comment != "":
            _t1901 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1901,))
        for missing_string in msg.missing_strings:
            _t1902 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1902,))
        _t1903 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1903,))
        _t1904 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1904,))
        _t1905 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1905,))
        if msg.partition_size_mb != 0:
            _t1906 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1906,))
        return sorted(result)

    def deconstruct_csv_storage_integration_optional(self, msg: logic_pb2.CSVConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        if not msg.HasField("storage_integration"):
            return None
        else:
            _t1907 = None
        assert msg.storage_integration is not None
        si = msg.storage_integration
        result = []
        if si.provider != "":
            _t1908 = self._make_value_string(si.provider)
            result.append(("provider", _t1908,))
        if si.azure_sas_token != "":
            _t1909 = self._make_value_string("***")
            result.append(("azure_sas_token", _t1909,))
        if si.s3_region != "":
            _t1910 = self._make_value_string(si.s3_region)
            result.append(("s3_region", _t1910,))
        if si.s3_access_key_id != "":
            _t1911 = self._make_value_string("***")
            result.append(("s3_access_key_id", _t1911,))
        if si.s3_secret_access_key != "":
            _t1912 = self._make_value_string("***")
            result.append(("s3_secret_access_key", _t1912,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1913 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1913,))
        _t1914 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1914,))
        _t1915 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1915,))
        _t1916 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1916,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1917 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1917,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1918 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1918,))
        _t1919 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1919,))
        _t1920 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1920,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1921 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1921,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1922 = self._make_value_string(msg.compression)
            result.append(("compression", _t1922,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1923 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1923,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1924 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1924,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1925 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1925,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1926 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1926,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1927 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1927,))
        return sorted(result)

    def mask_secret_value(self, pair: tuple[str, str]) -> str:
        return "***"

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1928 = None
        return None

    def deconstruct_iceberg_data_columns_optional(self, msg: logic_pb2.IcebergData) -> Sequence[logic_pb2.GNFColumn] | None:
        if msg.HasField("relations"):
            return None
        else:
            _t1929 = None
        return msg.columns

    def deconstruct_iceberg_data_relations_optional(self, msg: logic_pb2.IcebergData) -> logic_pb2.TargetRelations | None:
        if msg.HasField("relations"):
            assert msg.relations is not None
            return msg.relations
        else:
            _t1930 = None
        return None

    def deconstruct_iceberg_data_from_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.from_snapshot is not None
        if msg.from_snapshot != "":
            assert msg.from_snapshot is not None
            return msg.from_snapshot
        else:
            _t1931 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1932 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1933 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1933,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1934 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1934,))
        if msg.compression != "":
            _t1935 = self._make_value_string(msg.compression)
            result.append(("compression", _t1935,))
        if len(result) == 0:
            return None
        else:
            _t1936 = None
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
            _t1937 = None
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
        flat871 = self._try_flat(msg, self.pretty_transaction)
        if flat871 is not None:
            assert flat871 is not None
            self.write(flat871)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1724 = _dollar_dollar.configure
            else:
                _t1724 = None
            if _dollar_dollar.HasField("sync"):
                _t1725 = _dollar_dollar.sync
            else:
                _t1725 = None
            fields862 = (_t1724, _t1725, _dollar_dollar.epochs,)
            assert fields862 is not None
            unwrapped_fields863 = fields862
            self.write("(transaction")
            self.indent_sexp()
            field864 = unwrapped_fields863[0]
            if field864 is not None:
                self.newline()
                assert field864 is not None
                opt_val865 = field864
                self.pretty_configure(opt_val865)
            field866 = unwrapped_fields863[1]
            if field866 is not None:
                self.newline()
                assert field866 is not None
                opt_val867 = field866
                self.pretty_sync(opt_val867)
            field868 = unwrapped_fields863[2]
            if not len(field868) == 0:
                self.newline()
                for i870, elem869 in enumerate(field868):
                    if (i870 > 0):
                        self.newline()
                    self.pretty_epoch(elem869)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat874 = self._try_flat(msg, self.pretty_configure)
        if flat874 is not None:
            assert flat874 is not None
            self.write(flat874)
            return None
        else:
            _dollar_dollar = msg
            _t1726 = self.deconstruct_configure(_dollar_dollar)
            fields872 = _t1726
            assert fields872 is not None
            unwrapped_fields873 = fields872
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields873)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat878 = self._try_flat(msg, self.pretty_config_dict)
        if flat878 is not None:
            assert flat878 is not None
            self.write(flat878)
            return None
        else:
            fields875 = msg
            self.write("{")
            self.indent()
            if not len(fields875) == 0:
                self.newline()
                for i877, elem876 in enumerate(fields875):
                    if (i877 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem876)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat883 = self._try_flat(msg, self.pretty_config_key_value)
        if flat883 is not None:
            assert flat883 is not None
            self.write(flat883)
            return None
        else:
            _dollar_dollar = msg
            fields879 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields879 is not None
            unwrapped_fields880 = fields879
            self.write(":")
            field881 = unwrapped_fields880[0]
            self.write(field881)
            self.write(" ")
            field882 = unwrapped_fields880[1]
            self.pretty_raw_value(field882)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat909 = self._try_flat(msg, self.pretty_raw_value)
        if flat909 is not None:
            assert flat909 is not None
            self.write(flat909)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1727 = _dollar_dollar.date_value
            else:
                _t1727 = None
            deconstruct_result907 = _t1727
            if deconstruct_result907 is not None:
                assert deconstruct_result907 is not None
                unwrapped908 = deconstruct_result907
                self.pretty_raw_date(unwrapped908)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1728 = _dollar_dollar.datetime_value
                else:
                    _t1728 = None
                deconstruct_result905 = _t1728
                if deconstruct_result905 is not None:
                    assert deconstruct_result905 is not None
                    unwrapped906 = deconstruct_result905
                    self.pretty_raw_datetime(unwrapped906)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1729 = _dollar_dollar.string_value
                    else:
                        _t1729 = None
                    deconstruct_result903 = _t1729
                    if deconstruct_result903 is not None:
                        assert deconstruct_result903 is not None
                        unwrapped904 = deconstruct_result903
                        self.write(self.format_string_value(unwrapped904))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1730 = _dollar_dollar.int32_value
                        else:
                            _t1730 = None
                        deconstruct_result901 = _t1730
                        if deconstruct_result901 is not None:
                            assert deconstruct_result901 is not None
                            unwrapped902 = deconstruct_result901
                            self.write((str(unwrapped902) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1731 = _dollar_dollar.int_value
                            else:
                                _t1731 = None
                            deconstruct_result899 = _t1731
                            if deconstruct_result899 is not None:
                                assert deconstruct_result899 is not None
                                unwrapped900 = deconstruct_result899
                                self.write(str(unwrapped900))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1732 = _dollar_dollar.float32_value
                                else:
                                    _t1732 = None
                                deconstruct_result897 = _t1732
                                if deconstruct_result897 is not None:
                                    assert deconstruct_result897 is not None
                                    unwrapped898 = deconstruct_result897
                                    self.write(self.format_float32_literal(unwrapped898))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1733 = _dollar_dollar.float_value
                                    else:
                                        _t1733 = None
                                    deconstruct_result895 = _t1733
                                    if deconstruct_result895 is not None:
                                        assert deconstruct_result895 is not None
                                        unwrapped896 = deconstruct_result895
                                        self.write(str(unwrapped896))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1734 = _dollar_dollar.uint32_value
                                        else:
                                            _t1734 = None
                                        deconstruct_result893 = _t1734
                                        if deconstruct_result893 is not None:
                                            assert deconstruct_result893 is not None
                                            unwrapped894 = deconstruct_result893
                                            self.write((str(unwrapped894) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1735 = _dollar_dollar.uint128_value
                                            else:
                                                _t1735 = None
                                            deconstruct_result891 = _t1735
                                            if deconstruct_result891 is not None:
                                                assert deconstruct_result891 is not None
                                                unwrapped892 = deconstruct_result891
                                                self.write(self.format_uint128(unwrapped892))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1736 = _dollar_dollar.int128_value
                                                else:
                                                    _t1736 = None
                                                deconstruct_result889 = _t1736
                                                if deconstruct_result889 is not None:
                                                    assert deconstruct_result889 is not None
                                                    unwrapped890 = deconstruct_result889
                                                    self.write(self.format_int128(unwrapped890))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1737 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1737 = None
                                                    deconstruct_result887 = _t1737
                                                    if deconstruct_result887 is not None:
                                                        assert deconstruct_result887 is not None
                                                        unwrapped888 = deconstruct_result887
                                                        self.write(self.format_decimal(unwrapped888))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1738 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1738 = None
                                                        deconstruct_result885 = _t1738
                                                        if deconstruct_result885 is not None:
                                                            assert deconstruct_result885 is not None
                                                            unwrapped886 = deconstruct_result885
                                                            self.pretty_boolean_value(unwrapped886)
                                                        else:
                                                            fields884 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat915 = self._try_flat(msg, self.pretty_raw_date)
        if flat915 is not None:
            assert flat915 is not None
            self.write(flat915)
            return None
        else:
            _dollar_dollar = msg
            fields910 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields910 is not None
            unwrapped_fields911 = fields910
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field912 = unwrapped_fields911[0]
            self.write(str(field912))
            self.newline()
            field913 = unwrapped_fields911[1]
            self.write(str(field913))
            self.newline()
            field914 = unwrapped_fields911[2]
            self.write(str(field914))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat926 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat926 is not None:
            assert flat926 is not None
            self.write(flat926)
            return None
        else:
            _dollar_dollar = msg
            fields916 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields916 is not None
            unwrapped_fields917 = fields916
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field918 = unwrapped_fields917[0]
            self.write(str(field918))
            self.newline()
            field919 = unwrapped_fields917[1]
            self.write(str(field919))
            self.newline()
            field920 = unwrapped_fields917[2]
            self.write(str(field920))
            self.newline()
            field921 = unwrapped_fields917[3]
            self.write(str(field921))
            self.newline()
            field922 = unwrapped_fields917[4]
            self.write(str(field922))
            self.newline()
            field923 = unwrapped_fields917[5]
            self.write(str(field923))
            field924 = unwrapped_fields917[6]
            if field924 is not None:
                self.newline()
                assert field924 is not None
                opt_val925 = field924
                self.write(str(opt_val925))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1739 = ()
        else:
            _t1739 = None
        deconstruct_result929 = _t1739
        if deconstruct_result929 is not None:
            assert deconstruct_result929 is not None
            unwrapped930 = deconstruct_result929
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1740 = ()
            else:
                _t1740 = None
            deconstruct_result927 = _t1740
            if deconstruct_result927 is not None:
                assert deconstruct_result927 is not None
                unwrapped928 = deconstruct_result927
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat935 = self._try_flat(msg, self.pretty_sync)
        if flat935 is not None:
            assert flat935 is not None
            self.write(flat935)
            return None
        else:
            _dollar_dollar = msg
            fields931 = _dollar_dollar.fragments
            assert fields931 is not None
            unwrapped_fields932 = fields931
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields932) == 0:
                self.newline()
                for i934, elem933 in enumerate(unwrapped_fields932):
                    if (i934 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem933)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat938 = self._try_flat(msg, self.pretty_fragment_id)
        if flat938 is not None:
            assert flat938 is not None
            self.write(flat938)
            return None
        else:
            _dollar_dollar = msg
            fields936 = self.fragment_id_to_string(_dollar_dollar)
            assert fields936 is not None
            unwrapped_fields937 = fields936
            self.write(":")
            self.write(unwrapped_fields937)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat945 = self._try_flat(msg, self.pretty_epoch)
        if flat945 is not None:
            assert flat945 is not None
            self.write(flat945)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1741 = _dollar_dollar.writes
            else:
                _t1741 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1742 = _dollar_dollar.reads
            else:
                _t1742 = None
            fields939 = (_t1741, _t1742,)
            assert fields939 is not None
            unwrapped_fields940 = fields939
            self.write("(epoch")
            self.indent_sexp()
            field941 = unwrapped_fields940[0]
            if field941 is not None:
                self.newline()
                assert field941 is not None
                opt_val942 = field941
                self.pretty_epoch_writes(opt_val942)
            field943 = unwrapped_fields940[1]
            if field943 is not None:
                self.newline()
                assert field943 is not None
                opt_val944 = field943
                self.pretty_epoch_reads(opt_val944)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat949 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat949 is not None:
            assert flat949 is not None
            self.write(flat949)
            return None
        else:
            fields946 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields946) == 0:
                self.newline()
                for i948, elem947 in enumerate(fields946):
                    if (i948 > 0):
                        self.newline()
                    self.pretty_write(elem947)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat958 = self._try_flat(msg, self.pretty_write)
        if flat958 is not None:
            assert flat958 is not None
            self.write(flat958)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1743 = _dollar_dollar.define
            else:
                _t1743 = None
            deconstruct_result956 = _t1743
            if deconstruct_result956 is not None:
                assert deconstruct_result956 is not None
                unwrapped957 = deconstruct_result956
                self.pretty_define(unwrapped957)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1744 = _dollar_dollar.undefine
                else:
                    _t1744 = None
                deconstruct_result954 = _t1744
                if deconstruct_result954 is not None:
                    assert deconstruct_result954 is not None
                    unwrapped955 = deconstruct_result954
                    self.pretty_undefine(unwrapped955)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1745 = _dollar_dollar.context
                    else:
                        _t1745 = None
                    deconstruct_result952 = _t1745
                    if deconstruct_result952 is not None:
                        assert deconstruct_result952 is not None
                        unwrapped953 = deconstruct_result952
                        self.pretty_context(unwrapped953)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1746 = _dollar_dollar.snapshot
                        else:
                            _t1746 = None
                        deconstruct_result950 = _t1746
                        if deconstruct_result950 is not None:
                            assert deconstruct_result950 is not None
                            unwrapped951 = deconstruct_result950
                            self.pretty_snapshot(unwrapped951)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat961 = self._try_flat(msg, self.pretty_define)
        if flat961 is not None:
            assert flat961 is not None
            self.write(flat961)
            return None
        else:
            _dollar_dollar = msg
            fields959 = _dollar_dollar.fragment
            assert fields959 is not None
            unwrapped_fields960 = fields959
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields960)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat968 = self._try_flat(msg, self.pretty_fragment)
        if flat968 is not None:
            assert flat968 is not None
            self.write(flat968)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields962 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields962 is not None
            unwrapped_fields963 = fields962
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field964 = unwrapped_fields963[0]
            self.pretty_new_fragment_id(field964)
            field965 = unwrapped_fields963[1]
            if not len(field965) == 0:
                self.newline()
                for i967, elem966 in enumerate(field965):
                    if (i967 > 0):
                        self.newline()
                    self.pretty_declaration(elem966)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat970 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat970 is not None:
            assert flat970 is not None
            self.write(flat970)
            return None
        else:
            fields969 = msg
            self.pretty_fragment_id(fields969)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat979 = self._try_flat(msg, self.pretty_declaration)
        if flat979 is not None:
            assert flat979 is not None
            self.write(flat979)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1747 = getattr(_dollar_dollar, 'def')
            else:
                _t1747 = None
            deconstruct_result977 = _t1747
            if deconstruct_result977 is not None:
                assert deconstruct_result977 is not None
                unwrapped978 = deconstruct_result977
                self.pretty_def(unwrapped978)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1748 = _dollar_dollar.algorithm
                else:
                    _t1748 = None
                deconstruct_result975 = _t1748
                if deconstruct_result975 is not None:
                    assert deconstruct_result975 is not None
                    unwrapped976 = deconstruct_result975
                    self.pretty_algorithm(unwrapped976)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1749 = _dollar_dollar.constraint
                    else:
                        _t1749 = None
                    deconstruct_result973 = _t1749
                    if deconstruct_result973 is not None:
                        assert deconstruct_result973 is not None
                        unwrapped974 = deconstruct_result973
                        self.pretty_constraint(unwrapped974)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1750 = _dollar_dollar.data
                        else:
                            _t1750 = None
                        deconstruct_result971 = _t1750
                        if deconstruct_result971 is not None:
                            assert deconstruct_result971 is not None
                            unwrapped972 = deconstruct_result971
                            self.pretty_data(unwrapped972)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat986 = self._try_flat(msg, self.pretty_def)
        if flat986 is not None:
            assert flat986 is not None
            self.write(flat986)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1751 = _dollar_dollar.attrs
            else:
                _t1751 = None
            fields980 = (_dollar_dollar.name, _dollar_dollar.body, _t1751,)
            assert fields980 is not None
            unwrapped_fields981 = fields980
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field982 = unwrapped_fields981[0]
            self.pretty_relation_id(field982)
            self.newline()
            field983 = unwrapped_fields981[1]
            self.pretty_abstraction(field983)
            field984 = unwrapped_fields981[2]
            if field984 is not None:
                self.newline()
                assert field984 is not None
                opt_val985 = field984
                self.pretty_attrs(opt_val985)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat991 = self._try_flat(msg, self.pretty_relation_id)
        if flat991 is not None:
            assert flat991 is not None
            self.write(flat991)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1753 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1752 = _t1753
            else:
                _t1752 = None
            deconstruct_result989 = _t1752
            if deconstruct_result989 is not None:
                assert deconstruct_result989 is not None
                unwrapped990 = deconstruct_result989
                self.write(":")
                self.write(unwrapped990)
            else:
                _dollar_dollar = msg
                _t1754 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result987 = _t1754
                if deconstruct_result987 is not None:
                    assert deconstruct_result987 is not None
                    unwrapped988 = deconstruct_result987
                    self.write(self.format_uint128(unwrapped988))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat996 = self._try_flat(msg, self.pretty_abstraction)
        if flat996 is not None:
            assert flat996 is not None
            self.write(flat996)
            return None
        else:
            _dollar_dollar = msg
            _t1755 = self.deconstruct_bindings(_dollar_dollar)
            fields992 = (_t1755, _dollar_dollar.value,)
            assert fields992 is not None
            unwrapped_fields993 = fields992
            self.write("(")
            self.indent()
            field994 = unwrapped_fields993[0]
            self.pretty_bindings(field994)
            self.newline()
            field995 = unwrapped_fields993[1]
            self.pretty_formula(field995)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat1004 = self._try_flat(msg, self.pretty_bindings)
        if flat1004 is not None:
            assert flat1004 is not None
            self.write(flat1004)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1756 = _dollar_dollar[1]
            else:
                _t1756 = None
            fields997 = (_dollar_dollar[0], _t1756,)
            assert fields997 is not None
            unwrapped_fields998 = fields997
            self.write("[")
            self.indent()
            field999 = unwrapped_fields998[0]
            for i1001, elem1000 in enumerate(field999):
                if (i1001 > 0):
                    self.newline()
                self.pretty_binding(elem1000)
            field1002 = unwrapped_fields998[1]
            if field1002 is not None:
                self.newline()
                assert field1002 is not None
                opt_val1003 = field1002
                self.pretty_value_bindings(opt_val1003)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat1009 = self._try_flat(msg, self.pretty_binding)
        if flat1009 is not None:
            assert flat1009 is not None
            self.write(flat1009)
            return None
        else:
            _dollar_dollar = msg
            fields1005 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields1005 is not None
            unwrapped_fields1006 = fields1005
            field1007 = unwrapped_fields1006[0]
            self.write(field1007)
            self.write("::")
            field1008 = unwrapped_fields1006[1]
            self.pretty_type(field1008)

    def pretty_type(self, msg: logic_pb2.Type):
        flat1040 = self._try_flat(msg, self.pretty_type)
        if flat1040 is not None:
            assert flat1040 is not None
            self.write(flat1040)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1757 = _dollar_dollar.unspecified_type
            else:
                _t1757 = None
            deconstruct_result1038 = _t1757
            if deconstruct_result1038 is not None:
                assert deconstruct_result1038 is not None
                unwrapped1039 = deconstruct_result1038
                self.pretty_unspecified_type(unwrapped1039)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1758 = _dollar_dollar.string_type
                else:
                    _t1758 = None
                deconstruct_result1036 = _t1758
                if deconstruct_result1036 is not None:
                    assert deconstruct_result1036 is not None
                    unwrapped1037 = deconstruct_result1036
                    self.pretty_string_type(unwrapped1037)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1759 = _dollar_dollar.int_type
                    else:
                        _t1759 = None
                    deconstruct_result1034 = _t1759
                    if deconstruct_result1034 is not None:
                        assert deconstruct_result1034 is not None
                        unwrapped1035 = deconstruct_result1034
                        self.pretty_int_type(unwrapped1035)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1760 = _dollar_dollar.float_type
                        else:
                            _t1760 = None
                        deconstruct_result1032 = _t1760
                        if deconstruct_result1032 is not None:
                            assert deconstruct_result1032 is not None
                            unwrapped1033 = deconstruct_result1032
                            self.pretty_float_type(unwrapped1033)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1761 = _dollar_dollar.uint128_type
                            else:
                                _t1761 = None
                            deconstruct_result1030 = _t1761
                            if deconstruct_result1030 is not None:
                                assert deconstruct_result1030 is not None
                                unwrapped1031 = deconstruct_result1030
                                self.pretty_uint128_type(unwrapped1031)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1762 = _dollar_dollar.int128_type
                                else:
                                    _t1762 = None
                                deconstruct_result1028 = _t1762
                                if deconstruct_result1028 is not None:
                                    assert deconstruct_result1028 is not None
                                    unwrapped1029 = deconstruct_result1028
                                    self.pretty_int128_type(unwrapped1029)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1763 = _dollar_dollar.date_type
                                    else:
                                        _t1763 = None
                                    deconstruct_result1026 = _t1763
                                    if deconstruct_result1026 is not None:
                                        assert deconstruct_result1026 is not None
                                        unwrapped1027 = deconstruct_result1026
                                        self.pretty_date_type(unwrapped1027)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1764 = _dollar_dollar.datetime_type
                                        else:
                                            _t1764 = None
                                        deconstruct_result1024 = _t1764
                                        if deconstruct_result1024 is not None:
                                            assert deconstruct_result1024 is not None
                                            unwrapped1025 = deconstruct_result1024
                                            self.pretty_datetime_type(unwrapped1025)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1765 = _dollar_dollar.missing_type
                                            else:
                                                _t1765 = None
                                            deconstruct_result1022 = _t1765
                                            if deconstruct_result1022 is not None:
                                                assert deconstruct_result1022 is not None
                                                unwrapped1023 = deconstruct_result1022
                                                self.pretty_missing_type(unwrapped1023)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1766 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1766 = None
                                                deconstruct_result1020 = _t1766
                                                if deconstruct_result1020 is not None:
                                                    assert deconstruct_result1020 is not None
                                                    unwrapped1021 = deconstruct_result1020
                                                    self.pretty_decimal_type(unwrapped1021)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1767 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1767 = None
                                                    deconstruct_result1018 = _t1767
                                                    if deconstruct_result1018 is not None:
                                                        assert deconstruct_result1018 is not None
                                                        unwrapped1019 = deconstruct_result1018
                                                        self.pretty_boolean_type(unwrapped1019)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1768 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1768 = None
                                                        deconstruct_result1016 = _t1768
                                                        if deconstruct_result1016 is not None:
                                                            assert deconstruct_result1016 is not None
                                                            unwrapped1017 = deconstruct_result1016
                                                            self.pretty_int32_type(unwrapped1017)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1769 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1769 = None
                                                            deconstruct_result1014 = _t1769
                                                            if deconstruct_result1014 is not None:
                                                                assert deconstruct_result1014 is not None
                                                                unwrapped1015 = deconstruct_result1014
                                                                self.pretty_float32_type(unwrapped1015)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1770 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1770 = None
                                                                deconstruct_result1012 = _t1770
                                                                if deconstruct_result1012 is not None:
                                                                    assert deconstruct_result1012 is not None
                                                                    unwrapped1013 = deconstruct_result1012
                                                                    self.pretty_uint32_type(unwrapped1013)
                                                                else:
                                                                    _dollar_dollar = msg
                                                                    if _dollar_dollar.HasField("fixed_type"):
                                                                        _t1771 = _dollar_dollar.fixed_type
                                                                    else:
                                                                        _t1771 = None
                                                                    deconstruct_result1010 = _t1771
                                                                    if deconstruct_result1010 is not None:
                                                                        assert deconstruct_result1010 is not None
                                                                        unwrapped1011 = deconstruct_result1010
                                                                        self.pretty_fixed_type(unwrapped1011)
                                                                    else:
                                                                        raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields1041 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields1042 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields1043 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields1044 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields1045 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields1046 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields1047 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields1048 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields1049 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat1054 = self._try_flat(msg, self.pretty_decimal_type)
        if flat1054 is not None:
            assert flat1054 is not None
            self.write(flat1054)
            return None
        else:
            _dollar_dollar = msg
            fields1050 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields1050 is not None
            unwrapped_fields1051 = fields1050
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field1052 = unwrapped_fields1051[0]
            self.write(str(field1052))
            self.newline()
            field1053 = unwrapped_fields1051[1]
            self.write(str(field1053))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields1055 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields1056 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields1057 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields1058 = msg
        self.write("UINT32")

    def pretty_fixed_type(self, msg: logic_pb2.FixedType):
        flat1061 = self._try_flat(msg, self.pretty_fixed_type)
        if flat1061 is not None:
            assert flat1061 is not None
            self.write(flat1061)
            return None
        else:
            _dollar_dollar = msg
            fields1059 = int(_dollar_dollar.length)
            assert fields1059 is not None
            unwrapped_fields1060 = fields1059
            self.write("(FIXED")
            self.indent_sexp()
            self.newline()
            self.write(str(unwrapped_fields1060))
            self.dedent()
            self.write(")")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat1065 = self._try_flat(msg, self.pretty_value_bindings)
        if flat1065 is not None:
            assert flat1065 is not None
            self.write(flat1065)
            return None
        else:
            fields1062 = msg
            self.write("|")
            if not len(fields1062) == 0:
                self.write(" ")
                for i1064, elem1063 in enumerate(fields1062):
                    if (i1064 > 0):
                        self.newline()
                    self.pretty_binding(elem1063)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1092 = self._try_flat(msg, self.pretty_formula)
        if flat1092 is not None:
            assert flat1092 is not None
            self.write(flat1092)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1772 = _dollar_dollar.conjunction
            else:
                _t1772 = None
            deconstruct_result1090 = _t1772
            if deconstruct_result1090 is not None:
                assert deconstruct_result1090 is not None
                unwrapped1091 = deconstruct_result1090
                self.pretty_true(unwrapped1091)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1773 = _dollar_dollar.disjunction
                else:
                    _t1773 = None
                deconstruct_result1088 = _t1773
                if deconstruct_result1088 is not None:
                    assert deconstruct_result1088 is not None
                    unwrapped1089 = deconstruct_result1088
                    self.pretty_false(unwrapped1089)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1774 = _dollar_dollar.exists
                    else:
                        _t1774 = None
                    deconstruct_result1086 = _t1774
                    if deconstruct_result1086 is not None:
                        assert deconstruct_result1086 is not None
                        unwrapped1087 = deconstruct_result1086
                        self.pretty_exists(unwrapped1087)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1775 = _dollar_dollar.reduce
                        else:
                            _t1775 = None
                        deconstruct_result1084 = _t1775
                        if deconstruct_result1084 is not None:
                            assert deconstruct_result1084 is not None
                            unwrapped1085 = deconstruct_result1084
                            self.pretty_reduce(unwrapped1085)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1776 = _dollar_dollar.conjunction
                            else:
                                _t1776 = None
                            deconstruct_result1082 = _t1776
                            if deconstruct_result1082 is not None:
                                assert deconstruct_result1082 is not None
                                unwrapped1083 = deconstruct_result1082
                                self.pretty_conjunction(unwrapped1083)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1777 = _dollar_dollar.disjunction
                                else:
                                    _t1777 = None
                                deconstruct_result1080 = _t1777
                                if deconstruct_result1080 is not None:
                                    assert deconstruct_result1080 is not None
                                    unwrapped1081 = deconstruct_result1080
                                    self.pretty_disjunction(unwrapped1081)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1778 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1778 = None
                                    deconstruct_result1078 = _t1778
                                    if deconstruct_result1078 is not None:
                                        assert deconstruct_result1078 is not None
                                        unwrapped1079 = deconstruct_result1078
                                        self.pretty_not(unwrapped1079)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1779 = _dollar_dollar.ffi
                                        else:
                                            _t1779 = None
                                        deconstruct_result1076 = _t1779
                                        if deconstruct_result1076 is not None:
                                            assert deconstruct_result1076 is not None
                                            unwrapped1077 = deconstruct_result1076
                                            self.pretty_ffi(unwrapped1077)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1780 = _dollar_dollar.atom
                                            else:
                                                _t1780 = None
                                            deconstruct_result1074 = _t1780
                                            if deconstruct_result1074 is not None:
                                                assert deconstruct_result1074 is not None
                                                unwrapped1075 = deconstruct_result1074
                                                self.pretty_atom(unwrapped1075)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1781 = _dollar_dollar.pragma
                                                else:
                                                    _t1781 = None
                                                deconstruct_result1072 = _t1781
                                                if deconstruct_result1072 is not None:
                                                    assert deconstruct_result1072 is not None
                                                    unwrapped1073 = deconstruct_result1072
                                                    self.pretty_pragma(unwrapped1073)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1782 = _dollar_dollar.primitive
                                                    else:
                                                        _t1782 = None
                                                    deconstruct_result1070 = _t1782
                                                    if deconstruct_result1070 is not None:
                                                        assert deconstruct_result1070 is not None
                                                        unwrapped1071 = deconstruct_result1070
                                                        self.pretty_primitive(unwrapped1071)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1783 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1783 = None
                                                        deconstruct_result1068 = _t1783
                                                        if deconstruct_result1068 is not None:
                                                            assert deconstruct_result1068 is not None
                                                            unwrapped1069 = deconstruct_result1068
                                                            self.pretty_rel_atom(unwrapped1069)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1784 = _dollar_dollar.cast
                                                            else:
                                                                _t1784 = None
                                                            deconstruct_result1066 = _t1784
                                                            if deconstruct_result1066 is not None:
                                                                assert deconstruct_result1066 is not None
                                                                unwrapped1067 = deconstruct_result1066
                                                                self.pretty_cast(unwrapped1067)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields1093 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1094 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1099 = self._try_flat(msg, self.pretty_exists)
        if flat1099 is not None:
            assert flat1099 is not None
            self.write(flat1099)
            return None
        else:
            _dollar_dollar = msg
            _t1785 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1095 = (_t1785, _dollar_dollar.body.value,)
            assert fields1095 is not None
            unwrapped_fields1096 = fields1095
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1097 = unwrapped_fields1096[0]
            self.pretty_bindings(field1097)
            self.newline()
            field1098 = unwrapped_fields1096[1]
            self.pretty_formula(field1098)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1105 = self._try_flat(msg, self.pretty_reduce)
        if flat1105 is not None:
            assert flat1105 is not None
            self.write(flat1105)
            return None
        else:
            _dollar_dollar = msg
            fields1100 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1100 is not None
            unwrapped_fields1101 = fields1100
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1102 = unwrapped_fields1101[0]
            self.pretty_abstraction(field1102)
            self.newline()
            field1103 = unwrapped_fields1101[1]
            self.pretty_abstraction(field1103)
            self.newline()
            field1104 = unwrapped_fields1101[2]
            self.pretty_terms(field1104)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1109 = self._try_flat(msg, self.pretty_terms)
        if flat1109 is not None:
            assert flat1109 is not None
            self.write(flat1109)
            return None
        else:
            fields1106 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1106) == 0:
                self.newline()
                for i1108, elem1107 in enumerate(fields1106):
                    if (i1108 > 0):
                        self.newline()
                    self.pretty_term(elem1107)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1114 = self._try_flat(msg, self.pretty_term)
        if flat1114 is not None:
            assert flat1114 is not None
            self.write(flat1114)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1786 = _dollar_dollar.var
            else:
                _t1786 = None
            deconstruct_result1112 = _t1786
            if deconstruct_result1112 is not None:
                assert deconstruct_result1112 is not None
                unwrapped1113 = deconstruct_result1112
                self.pretty_var(unwrapped1113)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1787 = _dollar_dollar.constant
                else:
                    _t1787 = None
                deconstruct_result1110 = _t1787
                if deconstruct_result1110 is not None:
                    assert deconstruct_result1110 is not None
                    unwrapped1111 = deconstruct_result1110
                    self.pretty_value(unwrapped1111)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1117 = self._try_flat(msg, self.pretty_var)
        if flat1117 is not None:
            assert flat1117 is not None
            self.write(flat1117)
            return None
        else:
            _dollar_dollar = msg
            fields1115 = _dollar_dollar.name
            assert fields1115 is not None
            unwrapped_fields1116 = fields1115
            self.write(unwrapped_fields1116)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1143 = self._try_flat(msg, self.pretty_value)
        if flat1143 is not None:
            assert flat1143 is not None
            self.write(flat1143)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1788 = _dollar_dollar.date_value
            else:
                _t1788 = None
            deconstruct_result1141 = _t1788
            if deconstruct_result1141 is not None:
                assert deconstruct_result1141 is not None
                unwrapped1142 = deconstruct_result1141
                self.pretty_date(unwrapped1142)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1789 = _dollar_dollar.datetime_value
                else:
                    _t1789 = None
                deconstruct_result1139 = _t1789
                if deconstruct_result1139 is not None:
                    assert deconstruct_result1139 is not None
                    unwrapped1140 = deconstruct_result1139
                    self.pretty_datetime(unwrapped1140)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1790 = _dollar_dollar.string_value
                    else:
                        _t1790 = None
                    deconstruct_result1137 = _t1790
                    if deconstruct_result1137 is not None:
                        assert deconstruct_result1137 is not None
                        unwrapped1138 = deconstruct_result1137
                        self.write(self.format_string_value(unwrapped1138))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1791 = _dollar_dollar.int32_value
                        else:
                            _t1791 = None
                        deconstruct_result1135 = _t1791
                        if deconstruct_result1135 is not None:
                            assert deconstruct_result1135 is not None
                            unwrapped1136 = deconstruct_result1135
                            self.write((str(unwrapped1136) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1792 = _dollar_dollar.int_value
                            else:
                                _t1792 = None
                            deconstruct_result1133 = _t1792
                            if deconstruct_result1133 is not None:
                                assert deconstruct_result1133 is not None
                                unwrapped1134 = deconstruct_result1133
                                self.write(str(unwrapped1134))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1793 = _dollar_dollar.float32_value
                                else:
                                    _t1793 = None
                                deconstruct_result1131 = _t1793
                                if deconstruct_result1131 is not None:
                                    assert deconstruct_result1131 is not None
                                    unwrapped1132 = deconstruct_result1131
                                    self.write(self.format_float32_literal(unwrapped1132))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1794 = _dollar_dollar.float_value
                                    else:
                                        _t1794 = None
                                    deconstruct_result1129 = _t1794
                                    if deconstruct_result1129 is not None:
                                        assert deconstruct_result1129 is not None
                                        unwrapped1130 = deconstruct_result1129
                                        self.write(str(unwrapped1130))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1795 = _dollar_dollar.uint32_value
                                        else:
                                            _t1795 = None
                                        deconstruct_result1127 = _t1795
                                        if deconstruct_result1127 is not None:
                                            assert deconstruct_result1127 is not None
                                            unwrapped1128 = deconstruct_result1127
                                            self.write((str(unwrapped1128) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1796 = _dollar_dollar.uint128_value
                                            else:
                                                _t1796 = None
                                            deconstruct_result1125 = _t1796
                                            if deconstruct_result1125 is not None:
                                                assert deconstruct_result1125 is not None
                                                unwrapped1126 = deconstruct_result1125
                                                self.write(self.format_uint128(unwrapped1126))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1797 = _dollar_dollar.int128_value
                                                else:
                                                    _t1797 = None
                                                deconstruct_result1123 = _t1797
                                                if deconstruct_result1123 is not None:
                                                    assert deconstruct_result1123 is not None
                                                    unwrapped1124 = deconstruct_result1123
                                                    self.write(self.format_int128(unwrapped1124))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1798 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1798 = None
                                                    deconstruct_result1121 = _t1798
                                                    if deconstruct_result1121 is not None:
                                                        assert deconstruct_result1121 is not None
                                                        unwrapped1122 = deconstruct_result1121
                                                        self.write(self.format_decimal(unwrapped1122))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1799 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1799 = None
                                                        deconstruct_result1119 = _t1799
                                                        if deconstruct_result1119 is not None:
                                                            assert deconstruct_result1119 is not None
                                                            unwrapped1120 = deconstruct_result1119
                                                            self.pretty_boolean_value(unwrapped1120)
                                                        else:
                                                            fields1118 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1149 = self._try_flat(msg, self.pretty_date)
        if flat1149 is not None:
            assert flat1149 is not None
            self.write(flat1149)
            return None
        else:
            _dollar_dollar = msg
            fields1144 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1144 is not None
            unwrapped_fields1145 = fields1144
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1146 = unwrapped_fields1145[0]
            self.write(str(field1146))
            self.newline()
            field1147 = unwrapped_fields1145[1]
            self.write(str(field1147))
            self.newline()
            field1148 = unwrapped_fields1145[2]
            self.write(str(field1148))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1160 = self._try_flat(msg, self.pretty_datetime)
        if flat1160 is not None:
            assert flat1160 is not None
            self.write(flat1160)
            return None
        else:
            _dollar_dollar = msg
            fields1150 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1150 is not None
            unwrapped_fields1151 = fields1150
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1152 = unwrapped_fields1151[0]
            self.write(str(field1152))
            self.newline()
            field1153 = unwrapped_fields1151[1]
            self.write(str(field1153))
            self.newline()
            field1154 = unwrapped_fields1151[2]
            self.write(str(field1154))
            self.newline()
            field1155 = unwrapped_fields1151[3]
            self.write(str(field1155))
            self.newline()
            field1156 = unwrapped_fields1151[4]
            self.write(str(field1156))
            self.newline()
            field1157 = unwrapped_fields1151[5]
            self.write(str(field1157))
            field1158 = unwrapped_fields1151[6]
            if field1158 is not None:
                self.newline()
                assert field1158 is not None
                opt_val1159 = field1158
                self.write(str(opt_val1159))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1165 = self._try_flat(msg, self.pretty_conjunction)
        if flat1165 is not None:
            assert flat1165 is not None
            self.write(flat1165)
            return None
        else:
            _dollar_dollar = msg
            fields1161 = _dollar_dollar.args
            assert fields1161 is not None
            unwrapped_fields1162 = fields1161
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1162) == 0:
                self.newline()
                for i1164, elem1163 in enumerate(unwrapped_fields1162):
                    if (i1164 > 0):
                        self.newline()
                    self.pretty_formula(elem1163)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1170 = self._try_flat(msg, self.pretty_disjunction)
        if flat1170 is not None:
            assert flat1170 is not None
            self.write(flat1170)
            return None
        else:
            _dollar_dollar = msg
            fields1166 = _dollar_dollar.args
            assert fields1166 is not None
            unwrapped_fields1167 = fields1166
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1167) == 0:
                self.newline()
                for i1169, elem1168 in enumerate(unwrapped_fields1167):
                    if (i1169 > 0):
                        self.newline()
                    self.pretty_formula(elem1168)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1173 = self._try_flat(msg, self.pretty_not)
        if flat1173 is not None:
            assert flat1173 is not None
            self.write(flat1173)
            return None
        else:
            _dollar_dollar = msg
            fields1171 = _dollar_dollar.arg
            assert fields1171 is not None
            unwrapped_fields1172 = fields1171
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1172)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1179 = self._try_flat(msg, self.pretty_ffi)
        if flat1179 is not None:
            assert flat1179 is not None
            self.write(flat1179)
            return None
        else:
            _dollar_dollar = msg
            fields1174 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1174 is not None
            unwrapped_fields1175 = fields1174
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1176 = unwrapped_fields1175[0]
            self.pretty_name(field1176)
            self.newline()
            field1177 = unwrapped_fields1175[1]
            self.pretty_ffi_args(field1177)
            self.newline()
            field1178 = unwrapped_fields1175[2]
            self.pretty_terms(field1178)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1181 = self._try_flat(msg, self.pretty_name)
        if flat1181 is not None:
            assert flat1181 is not None
            self.write(flat1181)
            return None
        else:
            fields1180 = msg
            self.write(":")
            self.write(fields1180)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1185 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1185 is not None:
            assert flat1185 is not None
            self.write(flat1185)
            return None
        else:
            fields1182 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1182) == 0:
                self.newline()
                for i1184, elem1183 in enumerate(fields1182):
                    if (i1184 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1183)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1192 = self._try_flat(msg, self.pretty_atom)
        if flat1192 is not None:
            assert flat1192 is not None
            self.write(flat1192)
            return None
        else:
            _dollar_dollar = msg
            fields1186 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1186 is not None
            unwrapped_fields1187 = fields1186
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1188 = unwrapped_fields1187[0]
            self.pretty_relation_id(field1188)
            field1189 = unwrapped_fields1187[1]
            if not len(field1189) == 0:
                self.newline()
                for i1191, elem1190 in enumerate(field1189):
                    if (i1191 > 0):
                        self.newline()
                    self.pretty_term(elem1190)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1199 = self._try_flat(msg, self.pretty_pragma)
        if flat1199 is not None:
            assert flat1199 is not None
            self.write(flat1199)
            return None
        else:
            _dollar_dollar = msg
            fields1193 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1193 is not None
            unwrapped_fields1194 = fields1193
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1195 = unwrapped_fields1194[0]
            self.pretty_name(field1195)
            field1196 = unwrapped_fields1194[1]
            if not len(field1196) == 0:
                self.newline()
                for i1198, elem1197 in enumerate(field1196):
                    if (i1198 > 0):
                        self.newline()
                    self.pretty_term(elem1197)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1215 = self._try_flat(msg, self.pretty_primitive)
        if flat1215 is not None:
            assert flat1215 is not None
            self.write(flat1215)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1800 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1800 = None
            guard_result1214 = _t1800
            if guard_result1214 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1801 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1801 = None
                guard_result1213 = _t1801
                if guard_result1213 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1802 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1802 = None
                    guard_result1212 = _t1802
                    if guard_result1212 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1803 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1803 = None
                        guard_result1211 = _t1803
                        if guard_result1211 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1804 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1804 = None
                            guard_result1210 = _t1804
                            if guard_result1210 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1805 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1805 = None
                                guard_result1209 = _t1805
                                if guard_result1209 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1806 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1806 = None
                                    guard_result1208 = _t1806
                                    if guard_result1208 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1807 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1807 = None
                                        guard_result1207 = _t1807
                                        if guard_result1207 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1808 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1808 = None
                                            guard_result1206 = _t1808
                                            if guard_result1206 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1200 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1200 is not None
                                                unwrapped_fields1201 = fields1200
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1202 = unwrapped_fields1201[0]
                                                self.pretty_name(field1202)
                                                field1203 = unwrapped_fields1201[1]
                                                if not len(field1203) == 0:
                                                    self.newline()
                                                    for i1205, elem1204 in enumerate(field1203):
                                                        if (i1205 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1204)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1220 = self._try_flat(msg, self.pretty_eq)
        if flat1220 is not None:
            assert flat1220 is not None
            self.write(flat1220)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1809 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1809 = None
            fields1216 = _t1809
            assert fields1216 is not None
            unwrapped_fields1217 = fields1216
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1218 = unwrapped_fields1217[0]
            self.pretty_term(field1218)
            self.newline()
            field1219 = unwrapped_fields1217[1]
            self.pretty_term(field1219)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1225 = self._try_flat(msg, self.pretty_lt)
        if flat1225 is not None:
            assert flat1225 is not None
            self.write(flat1225)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1810 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1810 = None
            fields1221 = _t1810
            assert fields1221 is not None
            unwrapped_fields1222 = fields1221
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1223 = unwrapped_fields1222[0]
            self.pretty_term(field1223)
            self.newline()
            field1224 = unwrapped_fields1222[1]
            self.pretty_term(field1224)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1230 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1230 is not None:
            assert flat1230 is not None
            self.write(flat1230)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1811 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1811 = None
            fields1226 = _t1811
            assert fields1226 is not None
            unwrapped_fields1227 = fields1226
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1228 = unwrapped_fields1227[0]
            self.pretty_term(field1228)
            self.newline()
            field1229 = unwrapped_fields1227[1]
            self.pretty_term(field1229)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1235 = self._try_flat(msg, self.pretty_gt)
        if flat1235 is not None:
            assert flat1235 is not None
            self.write(flat1235)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1812 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1812 = None
            fields1231 = _t1812
            assert fields1231 is not None
            unwrapped_fields1232 = fields1231
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1233 = unwrapped_fields1232[0]
            self.pretty_term(field1233)
            self.newline()
            field1234 = unwrapped_fields1232[1]
            self.pretty_term(field1234)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1240 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1240 is not None:
            assert flat1240 is not None
            self.write(flat1240)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1813 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1813 = None
            fields1236 = _t1813
            assert fields1236 is not None
            unwrapped_fields1237 = fields1236
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1238 = unwrapped_fields1237[0]
            self.pretty_term(field1238)
            self.newline()
            field1239 = unwrapped_fields1237[1]
            self.pretty_term(field1239)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1246 = self._try_flat(msg, self.pretty_add)
        if flat1246 is not None:
            assert flat1246 is not None
            self.write(flat1246)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1814 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1814 = None
            fields1241 = _t1814
            assert fields1241 is not None
            unwrapped_fields1242 = fields1241
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1243 = unwrapped_fields1242[0]
            self.pretty_term(field1243)
            self.newline()
            field1244 = unwrapped_fields1242[1]
            self.pretty_term(field1244)
            self.newline()
            field1245 = unwrapped_fields1242[2]
            self.pretty_term(field1245)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1252 = self._try_flat(msg, self.pretty_minus)
        if flat1252 is not None:
            assert flat1252 is not None
            self.write(flat1252)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1815 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1815 = None
            fields1247 = _t1815
            assert fields1247 is not None
            unwrapped_fields1248 = fields1247
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1249 = unwrapped_fields1248[0]
            self.pretty_term(field1249)
            self.newline()
            field1250 = unwrapped_fields1248[1]
            self.pretty_term(field1250)
            self.newline()
            field1251 = unwrapped_fields1248[2]
            self.pretty_term(field1251)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1258 = self._try_flat(msg, self.pretty_multiply)
        if flat1258 is not None:
            assert flat1258 is not None
            self.write(flat1258)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1816 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1816 = None
            fields1253 = _t1816
            assert fields1253 is not None
            unwrapped_fields1254 = fields1253
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1255 = unwrapped_fields1254[0]
            self.pretty_term(field1255)
            self.newline()
            field1256 = unwrapped_fields1254[1]
            self.pretty_term(field1256)
            self.newline()
            field1257 = unwrapped_fields1254[2]
            self.pretty_term(field1257)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1264 = self._try_flat(msg, self.pretty_divide)
        if flat1264 is not None:
            assert flat1264 is not None
            self.write(flat1264)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1817 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1817 = None
            fields1259 = _t1817
            assert fields1259 is not None
            unwrapped_fields1260 = fields1259
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1261 = unwrapped_fields1260[0]
            self.pretty_term(field1261)
            self.newline()
            field1262 = unwrapped_fields1260[1]
            self.pretty_term(field1262)
            self.newline()
            field1263 = unwrapped_fields1260[2]
            self.pretty_term(field1263)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1269 = self._try_flat(msg, self.pretty_rel_term)
        if flat1269 is not None:
            assert flat1269 is not None
            self.write(flat1269)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1818 = _dollar_dollar.specialized_value
            else:
                _t1818 = None
            deconstruct_result1267 = _t1818
            if deconstruct_result1267 is not None:
                assert deconstruct_result1267 is not None
                unwrapped1268 = deconstruct_result1267
                self.pretty_specialized_value(unwrapped1268)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1819 = _dollar_dollar.term
                else:
                    _t1819 = None
                deconstruct_result1265 = _t1819
                if deconstruct_result1265 is not None:
                    assert deconstruct_result1265 is not None
                    unwrapped1266 = deconstruct_result1265
                    self.pretty_term(unwrapped1266)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1271 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1271 is not None:
            assert flat1271 is not None
            self.write(flat1271)
            return None
        else:
            fields1270 = msg
            self.write("#")
            self.pretty_raw_value(fields1270)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1278 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1278 is not None:
            assert flat1278 is not None
            self.write(flat1278)
            return None
        else:
            _dollar_dollar = msg
            fields1272 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1272 is not None
            unwrapped_fields1273 = fields1272
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1274 = unwrapped_fields1273[0]
            self.pretty_name(field1274)
            field1275 = unwrapped_fields1273[1]
            if not len(field1275) == 0:
                self.newline()
                for i1277, elem1276 in enumerate(field1275):
                    if (i1277 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1276)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1283 = self._try_flat(msg, self.pretty_cast)
        if flat1283 is not None:
            assert flat1283 is not None
            self.write(flat1283)
            return None
        else:
            _dollar_dollar = msg
            fields1279 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1279 is not None
            unwrapped_fields1280 = fields1279
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1281 = unwrapped_fields1280[0]
            self.pretty_term(field1281)
            self.newline()
            field1282 = unwrapped_fields1280[1]
            self.pretty_term(field1282)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1287 = self._try_flat(msg, self.pretty_attrs)
        if flat1287 is not None:
            assert flat1287 is not None
            self.write(flat1287)
            return None
        else:
            fields1284 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1284) == 0:
                self.newline()
                for i1286, elem1285 in enumerate(fields1284):
                    if (i1286 > 0):
                        self.newline()
                    self.pretty_attribute(elem1285)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1294 = self._try_flat(msg, self.pretty_attribute)
        if flat1294 is not None:
            assert flat1294 is not None
            self.write(flat1294)
            return None
        else:
            _dollar_dollar = msg
            fields1288 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1288 is not None
            unwrapped_fields1289 = fields1288
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1290 = unwrapped_fields1289[0]
            self.pretty_name(field1290)
            field1291 = unwrapped_fields1289[1]
            if not len(field1291) == 0:
                self.newline()
                for i1293, elem1292 in enumerate(field1291):
                    if (i1293 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1292)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1303 = self._try_flat(msg, self.pretty_algorithm)
        if flat1303 is not None:
            assert flat1303 is not None
            self.write(flat1303)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1820 = _dollar_dollar.attrs
            else:
                _t1820 = None
            fields1295 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body, _t1820,)
            assert fields1295 is not None
            unwrapped_fields1296 = fields1295
            self.write("(algorithm")
            self.indent_sexp()
            field1297 = unwrapped_fields1296[0]
            if not len(field1297) == 0:
                self.newline()
                for i1299, elem1298 in enumerate(field1297):
                    if (i1299 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1298)
            self.newline()
            field1300 = unwrapped_fields1296[1]
            self.pretty_script(field1300)
            field1301 = unwrapped_fields1296[2]
            if field1301 is not None:
                self.newline()
                assert field1301 is not None
                opt_val1302 = field1301
                self.pretty_attrs(opt_val1302)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1308 = self._try_flat(msg, self.pretty_script)
        if flat1308 is not None:
            assert flat1308 is not None
            self.write(flat1308)
            return None
        else:
            _dollar_dollar = msg
            fields1304 = _dollar_dollar.constructs
            assert fields1304 is not None
            unwrapped_fields1305 = fields1304
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1305) == 0:
                self.newline()
                for i1307, elem1306 in enumerate(unwrapped_fields1305):
                    if (i1307 > 0):
                        self.newline()
                    self.pretty_construct(elem1306)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1313 = self._try_flat(msg, self.pretty_construct)
        if flat1313 is not None:
            assert flat1313 is not None
            self.write(flat1313)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1821 = _dollar_dollar.loop
            else:
                _t1821 = None
            deconstruct_result1311 = _t1821
            if deconstruct_result1311 is not None:
                assert deconstruct_result1311 is not None
                unwrapped1312 = deconstruct_result1311
                self.pretty_loop(unwrapped1312)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1822 = _dollar_dollar.instruction
                else:
                    _t1822 = None
                deconstruct_result1309 = _t1822
                if deconstruct_result1309 is not None:
                    assert deconstruct_result1309 is not None
                    unwrapped1310 = deconstruct_result1309
                    self.pretty_instruction(unwrapped1310)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1320 = self._try_flat(msg, self.pretty_loop)
        if flat1320 is not None:
            assert flat1320 is not None
            self.write(flat1320)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1823 = _dollar_dollar.attrs
            else:
                _t1823 = None
            fields1314 = (_dollar_dollar.init, _dollar_dollar.body, _t1823,)
            assert fields1314 is not None
            unwrapped_fields1315 = fields1314
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1316 = unwrapped_fields1315[0]
            self.pretty_init(field1316)
            self.newline()
            field1317 = unwrapped_fields1315[1]
            self.pretty_script(field1317)
            field1318 = unwrapped_fields1315[2]
            if field1318 is not None:
                self.newline()
                assert field1318 is not None
                opt_val1319 = field1318
                self.pretty_attrs(opt_val1319)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1324 = self._try_flat(msg, self.pretty_init)
        if flat1324 is not None:
            assert flat1324 is not None
            self.write(flat1324)
            return None
        else:
            fields1321 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1321) == 0:
                self.newline()
                for i1323, elem1322 in enumerate(fields1321):
                    if (i1323 > 0):
                        self.newline()
                    self.pretty_instruction(elem1322)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1335 = self._try_flat(msg, self.pretty_instruction)
        if flat1335 is not None:
            assert flat1335 is not None
            self.write(flat1335)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1824 = _dollar_dollar.assign
            else:
                _t1824 = None
            deconstruct_result1333 = _t1824
            if deconstruct_result1333 is not None:
                assert deconstruct_result1333 is not None
                unwrapped1334 = deconstruct_result1333
                self.pretty_assign(unwrapped1334)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1825 = _dollar_dollar.upsert
                else:
                    _t1825 = None
                deconstruct_result1331 = _t1825
                if deconstruct_result1331 is not None:
                    assert deconstruct_result1331 is not None
                    unwrapped1332 = deconstruct_result1331
                    self.pretty_upsert(unwrapped1332)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1826 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1826 = None
                    deconstruct_result1329 = _t1826
                    if deconstruct_result1329 is not None:
                        assert deconstruct_result1329 is not None
                        unwrapped1330 = deconstruct_result1329
                        self.pretty_break(unwrapped1330)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1827 = _dollar_dollar.monoid_def
                        else:
                            _t1827 = None
                        deconstruct_result1327 = _t1827
                        if deconstruct_result1327 is not None:
                            assert deconstruct_result1327 is not None
                            unwrapped1328 = deconstruct_result1327
                            self.pretty_monoid_def(unwrapped1328)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1828 = _dollar_dollar.monus_def
                            else:
                                _t1828 = None
                            deconstruct_result1325 = _t1828
                            if deconstruct_result1325 is not None:
                                assert deconstruct_result1325 is not None
                                unwrapped1326 = deconstruct_result1325
                                self.pretty_monus_def(unwrapped1326)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1342 = self._try_flat(msg, self.pretty_assign)
        if flat1342 is not None:
            assert flat1342 is not None
            self.write(flat1342)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1829 = _dollar_dollar.attrs
            else:
                _t1829 = None
            fields1336 = (_dollar_dollar.name, _dollar_dollar.body, _t1829,)
            assert fields1336 is not None
            unwrapped_fields1337 = fields1336
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1338 = unwrapped_fields1337[0]
            self.pretty_relation_id(field1338)
            self.newline()
            field1339 = unwrapped_fields1337[1]
            self.pretty_abstraction(field1339)
            field1340 = unwrapped_fields1337[2]
            if field1340 is not None:
                self.newline()
                assert field1340 is not None
                opt_val1341 = field1340
                self.pretty_attrs(opt_val1341)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1349 = self._try_flat(msg, self.pretty_upsert)
        if flat1349 is not None:
            assert flat1349 is not None
            self.write(flat1349)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1830 = _dollar_dollar.attrs
            else:
                _t1830 = None
            fields1343 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1830,)
            assert fields1343 is not None
            unwrapped_fields1344 = fields1343
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1345 = unwrapped_fields1344[0]
            self.pretty_relation_id(field1345)
            self.newline()
            field1346 = unwrapped_fields1344[1]
            self.pretty_abstraction_with_arity(field1346)
            field1347 = unwrapped_fields1344[2]
            if field1347 is not None:
                self.newline()
                assert field1347 is not None
                opt_val1348 = field1347
                self.pretty_attrs(opt_val1348)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1354 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1354 is not None:
            assert flat1354 is not None
            self.write(flat1354)
            return None
        else:
            _dollar_dollar = msg
            _t1831 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1350 = (_t1831, _dollar_dollar[0].value,)
            assert fields1350 is not None
            unwrapped_fields1351 = fields1350
            self.write("(")
            self.indent()
            field1352 = unwrapped_fields1351[0]
            self.pretty_bindings(field1352)
            self.newline()
            field1353 = unwrapped_fields1351[1]
            self.pretty_formula(field1353)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1361 = self._try_flat(msg, self.pretty_break)
        if flat1361 is not None:
            assert flat1361 is not None
            self.write(flat1361)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1832 = _dollar_dollar.attrs
            else:
                _t1832 = None
            fields1355 = (_dollar_dollar.name, _dollar_dollar.body, _t1832,)
            assert fields1355 is not None
            unwrapped_fields1356 = fields1355
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1357 = unwrapped_fields1356[0]
            self.pretty_relation_id(field1357)
            self.newline()
            field1358 = unwrapped_fields1356[1]
            self.pretty_abstraction(field1358)
            field1359 = unwrapped_fields1356[2]
            if field1359 is not None:
                self.newline()
                assert field1359 is not None
                opt_val1360 = field1359
                self.pretty_attrs(opt_val1360)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1369 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1369 is not None:
            assert flat1369 is not None
            self.write(flat1369)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1833 = _dollar_dollar.attrs
            else:
                _t1833 = None
            fields1362 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1833,)
            assert fields1362 is not None
            unwrapped_fields1363 = fields1362
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1364 = unwrapped_fields1363[0]
            self.pretty_monoid(field1364)
            self.newline()
            field1365 = unwrapped_fields1363[1]
            self.pretty_relation_id(field1365)
            self.newline()
            field1366 = unwrapped_fields1363[2]
            self.pretty_abstraction_with_arity(field1366)
            field1367 = unwrapped_fields1363[3]
            if field1367 is not None:
                self.newline()
                assert field1367 is not None
                opt_val1368 = field1367
                self.pretty_attrs(opt_val1368)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1378 = self._try_flat(msg, self.pretty_monoid)
        if flat1378 is not None:
            assert flat1378 is not None
            self.write(flat1378)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1834 = _dollar_dollar.or_monoid
            else:
                _t1834 = None
            deconstruct_result1376 = _t1834
            if deconstruct_result1376 is not None:
                assert deconstruct_result1376 is not None
                unwrapped1377 = deconstruct_result1376
                self.pretty_or_monoid(unwrapped1377)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1835 = _dollar_dollar.min_monoid
                else:
                    _t1835 = None
                deconstruct_result1374 = _t1835
                if deconstruct_result1374 is not None:
                    assert deconstruct_result1374 is not None
                    unwrapped1375 = deconstruct_result1374
                    self.pretty_min_monoid(unwrapped1375)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1836 = _dollar_dollar.max_monoid
                    else:
                        _t1836 = None
                    deconstruct_result1372 = _t1836
                    if deconstruct_result1372 is not None:
                        assert deconstruct_result1372 is not None
                        unwrapped1373 = deconstruct_result1372
                        self.pretty_max_monoid(unwrapped1373)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1837 = _dollar_dollar.sum_monoid
                        else:
                            _t1837 = None
                        deconstruct_result1370 = _t1837
                        if deconstruct_result1370 is not None:
                            assert deconstruct_result1370 is not None
                            unwrapped1371 = deconstruct_result1370
                            self.pretty_sum_monoid(unwrapped1371)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1379 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1382 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1382 is not None:
            assert flat1382 is not None
            self.write(flat1382)
            return None
        else:
            _dollar_dollar = msg
            fields1380 = _dollar_dollar.type
            assert fields1380 is not None
            unwrapped_fields1381 = fields1380
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1381)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1385 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1385 is not None:
            assert flat1385 is not None
            self.write(flat1385)
            return None
        else:
            _dollar_dollar = msg
            fields1383 = _dollar_dollar.type
            assert fields1383 is not None
            unwrapped_fields1384 = fields1383
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1384)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1388 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1388 is not None:
            assert flat1388 is not None
            self.write(flat1388)
            return None
        else:
            _dollar_dollar = msg
            fields1386 = _dollar_dollar.type
            assert fields1386 is not None
            unwrapped_fields1387 = fields1386
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1387)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1396 = self._try_flat(msg, self.pretty_monus_def)
        if flat1396 is not None:
            assert flat1396 is not None
            self.write(flat1396)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1838 = _dollar_dollar.attrs
            else:
                _t1838 = None
            fields1389 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1838,)
            assert fields1389 is not None
            unwrapped_fields1390 = fields1389
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1391 = unwrapped_fields1390[0]
            self.pretty_monoid(field1391)
            self.newline()
            field1392 = unwrapped_fields1390[1]
            self.pretty_relation_id(field1392)
            self.newline()
            field1393 = unwrapped_fields1390[2]
            self.pretty_abstraction_with_arity(field1393)
            field1394 = unwrapped_fields1390[3]
            if field1394 is not None:
                self.newline()
                assert field1394 is not None
                opt_val1395 = field1394
                self.pretty_attrs(opt_val1395)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1403 = self._try_flat(msg, self.pretty_constraint)
        if flat1403 is not None:
            assert flat1403 is not None
            self.write(flat1403)
            return None
        else:
            _dollar_dollar = msg
            fields1397 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1397 is not None
            unwrapped_fields1398 = fields1397
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1399 = unwrapped_fields1398[0]
            self.pretty_relation_id(field1399)
            self.newline()
            field1400 = unwrapped_fields1398[1]
            self.pretty_abstraction(field1400)
            self.newline()
            field1401 = unwrapped_fields1398[2]
            self.pretty_functional_dependency_keys(field1401)
            self.newline()
            field1402 = unwrapped_fields1398[3]
            self.pretty_functional_dependency_values(field1402)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1407 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1407 is not None:
            assert flat1407 is not None
            self.write(flat1407)
            return None
        else:
            fields1404 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1404) == 0:
                self.newline()
                for i1406, elem1405 in enumerate(fields1404):
                    if (i1406 > 0):
                        self.newline()
                    self.pretty_var(elem1405)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1411 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1411 is not None:
            assert flat1411 is not None
            self.write(flat1411)
            return None
        else:
            fields1408 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1408) == 0:
                self.newline()
                for i1410, elem1409 in enumerate(fields1408):
                    if (i1410 > 0):
                        self.newline()
                    self.pretty_var(elem1409)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1420 = self._try_flat(msg, self.pretty_data)
        if flat1420 is not None:
            assert flat1420 is not None
            self.write(flat1420)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1839 = _dollar_dollar.edb
            else:
                _t1839 = None
            deconstruct_result1418 = _t1839
            if deconstruct_result1418 is not None:
                assert deconstruct_result1418 is not None
                unwrapped1419 = deconstruct_result1418
                self.pretty_edb(unwrapped1419)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1840 = _dollar_dollar.betree_relation
                else:
                    _t1840 = None
                deconstruct_result1416 = _t1840
                if deconstruct_result1416 is not None:
                    assert deconstruct_result1416 is not None
                    unwrapped1417 = deconstruct_result1416
                    self.pretty_betree_relation(unwrapped1417)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1841 = _dollar_dollar.csv_data
                    else:
                        _t1841 = None
                    deconstruct_result1414 = _t1841
                    if deconstruct_result1414 is not None:
                        assert deconstruct_result1414 is not None
                        unwrapped1415 = deconstruct_result1414
                        self.pretty_csv_data(unwrapped1415)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1842 = _dollar_dollar.iceberg_data
                        else:
                            _t1842 = None
                        deconstruct_result1412 = _t1842
                        if deconstruct_result1412 is not None:
                            assert deconstruct_result1412 is not None
                            unwrapped1413 = deconstruct_result1412
                            self.pretty_iceberg_data(unwrapped1413)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1426 = self._try_flat(msg, self.pretty_edb)
        if flat1426 is not None:
            assert flat1426 is not None
            self.write(flat1426)
            return None
        else:
            _dollar_dollar = msg
            fields1421 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1421 is not None
            unwrapped_fields1422 = fields1421
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1423 = unwrapped_fields1422[0]
            self.pretty_relation_id(field1423)
            self.newline()
            field1424 = unwrapped_fields1422[1]
            self.pretty_edb_path(field1424)
            self.newline()
            field1425 = unwrapped_fields1422[2]
            self.pretty_edb_types(field1425)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1430 = self._try_flat(msg, self.pretty_edb_path)
        if flat1430 is not None:
            assert flat1430 is not None
            self.write(flat1430)
            return None
        else:
            fields1427 = msg
            self.write("[")
            self.indent()
            for i1429, elem1428 in enumerate(fields1427):
                if (i1429 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1428))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1434 = self._try_flat(msg, self.pretty_edb_types)
        if flat1434 is not None:
            assert flat1434 is not None
            self.write(flat1434)
            return None
        else:
            fields1431 = msg
            self.write("[")
            self.indent()
            for i1433, elem1432 in enumerate(fields1431):
                if (i1433 > 0):
                    self.newline()
                self.pretty_type(elem1432)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1439 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1439 is not None:
            assert flat1439 is not None
            self.write(flat1439)
            return None
        else:
            _dollar_dollar = msg
            fields1435 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1435 is not None
            unwrapped_fields1436 = fields1435
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1437 = unwrapped_fields1436[0]
            self.pretty_relation_id(field1437)
            self.newline()
            field1438 = unwrapped_fields1436[1]
            self.pretty_betree_info(field1438)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1445 = self._try_flat(msg, self.pretty_betree_info)
        if flat1445 is not None:
            assert flat1445 is not None
            self.write(flat1445)
            return None
        else:
            _dollar_dollar = msg
            _t1843 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1440 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1843,)
            assert fields1440 is not None
            unwrapped_fields1441 = fields1440
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1442 = unwrapped_fields1441[0]
            self.pretty_betree_info_key_types(field1442)
            self.newline()
            field1443 = unwrapped_fields1441[1]
            self.pretty_betree_info_value_types(field1443)
            self.newline()
            field1444 = unwrapped_fields1441[2]
            self.pretty_config_dict(field1444)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1449 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1449 is not None:
            assert flat1449 is not None
            self.write(flat1449)
            return None
        else:
            fields1446 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1446) == 0:
                self.newline()
                for i1448, elem1447 in enumerate(fields1446):
                    if (i1448 > 0):
                        self.newline()
                    self.pretty_type(elem1447)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1453 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1453 is not None:
            assert flat1453 is not None
            self.write(flat1453)
            return None
        else:
            fields1450 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1450) == 0:
                self.newline()
                for i1452, elem1451 in enumerate(fields1450):
                    if (i1452 > 0):
                        self.newline()
                    self.pretty_type(elem1451)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1463 = self._try_flat(msg, self.pretty_csv_data)
        if flat1463 is not None:
            assert flat1463 is not None
            self.write(flat1463)
            return None
        else:
            _dollar_dollar = msg
            _t1844 = self.deconstruct_csv_data_columns_optional(_dollar_dollar)
            _t1845 = self.deconstruct_csv_data_relations_optional(_dollar_dollar)
            fields1454 = (_dollar_dollar.locator, _dollar_dollar.config, _t1844, _t1845, _dollar_dollar.asof,)
            assert fields1454 is not None
            unwrapped_fields1455 = fields1454
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1456 = unwrapped_fields1455[0]
            self.pretty_csvlocator(field1456)
            self.newline()
            field1457 = unwrapped_fields1455[1]
            self.pretty_csv_config(field1457)
            field1458 = unwrapped_fields1455[2]
            if field1458 is not None:
                self.newline()
                assert field1458 is not None
                opt_val1459 = field1458
                self.pretty_gnf_columns(opt_val1459)
            field1460 = unwrapped_fields1455[3]
            if field1460 is not None:
                self.newline()
                assert field1460 is not None
                opt_val1461 = field1460
                self.pretty_target_relations(opt_val1461)
            self.newline()
            field1462 = unwrapped_fields1455[4]
            self.pretty_csv_asof(field1462)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1470 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1470 is not None:
            assert flat1470 is not None
            self.write(flat1470)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1846 = _dollar_dollar.paths
            else:
                _t1846 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1847 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1847 = None
            fields1464 = (_t1846, _t1847,)
            assert fields1464 is not None
            unwrapped_fields1465 = fields1464
            self.write("(csv_locator")
            self.indent_sexp()
            field1466 = unwrapped_fields1465[0]
            if field1466 is not None:
                self.newline()
                assert field1466 is not None
                opt_val1467 = field1466
                self.pretty_csv_locator_paths(opt_val1467)
            field1468 = unwrapped_fields1465[1]
            if field1468 is not None:
                self.newline()
                assert field1468 is not None
                opt_val1469 = field1468
                self.pretty_csv_locator_inline_data(opt_val1469)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1474 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1474 is not None:
            assert flat1474 is not None
            self.write(flat1474)
            return None
        else:
            fields1471 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1471) == 0:
                self.newline()
                for i1473, elem1472 in enumerate(fields1471):
                    if (i1473 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1472))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1476 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1476 is not None:
            assert flat1476 is not None
            self.write(flat1476)
            return None
        else:
            fields1475 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1475))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1482 = self._try_flat(msg, self.pretty_csv_config)
        if flat1482 is not None:
            assert flat1482 is not None
            self.write(flat1482)
            return None
        else:
            _dollar_dollar = msg
            _t1848 = self.deconstruct_csv_config(_dollar_dollar)
            _t1849 = self.deconstruct_csv_storage_integration_optional(_dollar_dollar)
            fields1477 = (_t1848, _t1849,)
            assert fields1477 is not None
            unwrapped_fields1478 = fields1477
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            field1479 = unwrapped_fields1478[0]
            self.pretty_config_dict(field1479)
            field1480 = unwrapped_fields1478[1]
            if field1480 is not None:
                self.newline()
                assert field1480 is not None
                opt_val1481 = field1480
                self.pretty__storage_integration(opt_val1481)
            self.dedent()
            self.write(")")

    def pretty__storage_integration(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat1484 = self._try_flat(msg, self.pretty__storage_integration)
        if flat1484 is not None:
            assert flat1484 is not None
            self.write(flat1484)
            return None
        else:
            fields1483 = msg
            self.write("(storage_integration")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(fields1483)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1488 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1488 is not None:
            assert flat1488 is not None
            self.write(flat1488)
            return None
        else:
            fields1485 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1485) == 0:
                self.newline()
                for i1487, elem1486 in enumerate(fields1485):
                    if (i1487 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1486)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1497 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1497 is not None:
            assert flat1497 is not None
            self.write(flat1497)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1850 = _dollar_dollar.target_id
            else:
                _t1850 = None
            fields1489 = (_dollar_dollar.column_path, _t1850, _dollar_dollar.types,)
            assert fields1489 is not None
            unwrapped_fields1490 = fields1489
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1491 = unwrapped_fields1490[0]
            self.pretty_gnf_column_path(field1491)
            field1492 = unwrapped_fields1490[1]
            if field1492 is not None:
                self.newline()
                assert field1492 is not None
                opt_val1493 = field1492
                self.pretty_relation_id(opt_val1493)
            self.newline()
            self.write("[")
            field1494 = unwrapped_fields1490[2]
            for i1496, elem1495 in enumerate(field1494):
                if (i1496 > 0):
                    self.newline()
                self.pretty_type(elem1495)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1504 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1504 is not None:
            assert flat1504 is not None
            self.write(flat1504)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1851 = _dollar_dollar[0]
            else:
                _t1851 = None
            deconstruct_result1502 = _t1851
            if deconstruct_result1502 is not None:
                assert deconstruct_result1502 is not None
                unwrapped1503 = deconstruct_result1502
                self.write(self.format_string_value(unwrapped1503))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1852 = _dollar_dollar
                else:
                    _t1852 = None
                deconstruct_result1498 = _t1852
                if deconstruct_result1498 is not None:
                    assert deconstruct_result1498 is not None
                    unwrapped1499 = deconstruct_result1498
                    self.write("[")
                    self.indent()
                    for i1501, elem1500 in enumerate(unwrapped1499):
                        if (i1501 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1500))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_target_relations(self, msg: logic_pb2.TargetRelations):
        flat1511 = self._try_flat(msg, self.pretty_target_relations)
        if flat1511 is not None:
            assert flat1511 is not None
            self.write(flat1511)
            return None
        else:
            _dollar_dollar = msg
            _t1853 = self.deconstruct_relation_keys(_dollar_dollar)
            _t1854 = self.deconstruct_load_errors_optional(_dollar_dollar)
            fields1505 = (_t1853, _dollar_dollar, _t1854,)
            assert fields1505 is not None
            unwrapped_fields1506 = fields1505
            self.write("(relations")
            self.indent_sexp()
            self.newline()
            field1507 = unwrapped_fields1506[0]
            self.pretty_relation_keys(field1507)
            self.newline()
            field1508 = unwrapped_fields1506[1]
            self.pretty_relation_body(field1508)
            field1509 = unwrapped_fields1506[2]
            if field1509 is not None:
                self.newline()
                assert field1509 is not None
                opt_val1510 = field1509
                self.pretty_load_errors(opt_val1510)
            self.dedent()
            self.write(")")

    def pretty_relation_keys(self, msg: tuple[Sequence[logic_pb2.NamedColumn], bool]):
        flat1518 = self._try_flat(msg, self.pretty_relation_keys)
        if flat1518 is not None:
            assert flat1518 is not None
            self.write(flat1518)
            return None
        else:
            _dollar_dollar = msg
            if not _dollar_dollar[1]:
                _t1855 = _dollar_dollar[0]
            else:
                _t1855 = None
            deconstruct_result1514 = _t1855
            if deconstruct_result1514 is not None:
                assert deconstruct_result1514 is not None
                unwrapped1515 = deconstruct_result1514
                self.write("(keys")
                self.indent_sexp()
                if not len(unwrapped1515) == 0:
                    self.newline()
                    for i1517, elem1516 in enumerate(unwrapped1515):
                        if (i1517 > 0):
                            self.newline()
                        self.pretty_named_column(elem1516)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar[1]:
                    _t1856 = ()
                else:
                    _t1856 = None
                deconstruct_result1512 = _t1856
                if deconstruct_result1512 is not None:
                    assert deconstruct_result1512 is not None
                    unwrapped1513 = deconstruct_result1512
                    self.write("(keys")
                    self.newline()
                    self.write("synthetic)")
                else:
                    raise ParseError("No matching rule for relation_keys")

    def pretty_named_column(self, msg: logic_pb2.NamedColumn):
        flat1523 = self._try_flat(msg, self.pretty_named_column)
        if flat1523 is not None:
            assert flat1523 is not None
            self.write(flat1523)
            return None
        else:
            _dollar_dollar = msg
            fields1519 = (_dollar_dollar.name, _dollar_dollar.type,)
            assert fields1519 is not None
            unwrapped_fields1520 = fields1519
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1521 = unwrapped_fields1520[0]
            self.write(self.format_string_value(field1521))
            self.newline()
            field1522 = unwrapped_fields1520[1]
            self.pretty_type(field1522)
            self.dedent()
            self.write(")")

    def pretty_relation_body(self, msg: logic_pb2.TargetRelations):
        flat1530 = self._try_flat(msg, self.pretty_relation_body)
        if flat1530 is not None:
            assert flat1530 is not None
            self.write(flat1530)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("plain"):
                _t1857 = _dollar_dollar.plain.targets
            else:
                _t1857 = None
            deconstruct_result1528 = _t1857
            if deconstruct_result1528 is not None:
                assert deconstruct_result1528 is not None
                unwrapped1529 = deconstruct_result1528
                self.pretty_non_cdc_relations(unwrapped1529)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("cdc"):
                    _t1858 = (_dollar_dollar.cdc.inserts, _dollar_dollar.cdc.deletes,)
                else:
                    _t1858 = None
                deconstruct_result1524 = _t1858
                if deconstruct_result1524 is not None:
                    assert deconstruct_result1524 is not None
                    unwrapped1525 = deconstruct_result1524
                    field1526 = unwrapped1525[0]
                    self.pretty_cdc_inserts(field1526)
                    self.write(" ")
                    field1527 = unwrapped1525[1]
                    self.pretty_cdc_deletes(field1527)
                else:
                    raise ParseError("No matching rule for relation_body")

    def pretty_non_cdc_relations(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1534 = self._try_flat(msg, self.pretty_non_cdc_relations)
        if flat1534 is not None:
            assert flat1534 is not None
            self.write(flat1534)
            return None
        else:
            fields1531 = msg
            for i1533, elem1532 in enumerate(fields1531):
                if (i1533 > 0):
                    self.newline()
                self.pretty_target_relation(elem1532)

    def pretty_target_relation(self, msg: logic_pb2.TargetRelation):
        flat1541 = self._try_flat(msg, self.pretty_target_relation)
        if flat1541 is not None:
            assert flat1541 is not None
            self.write(flat1541)
            return None
        else:
            _dollar_dollar = msg
            fields1535 = (_dollar_dollar.target_id, _dollar_dollar.values,)
            assert fields1535 is not None
            unwrapped_fields1536 = fields1535
            self.write("(relation")
            self.indent_sexp()
            self.newline()
            field1537 = unwrapped_fields1536[0]
            self.pretty_relation_id(field1537)
            field1538 = unwrapped_fields1536[1]
            if not len(field1538) == 0:
                self.newline()
                for i1540, elem1539 in enumerate(field1538):
                    if (i1540 > 0):
                        self.newline()
                    self.pretty_named_column(elem1539)
            self.dedent()
            self.write(")")

    def pretty_cdc_inserts(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1545 = self._try_flat(msg, self.pretty_cdc_inserts)
        if flat1545 is not None:
            assert flat1545 is not None
            self.write(flat1545)
            return None
        else:
            fields1542 = msg
            self.write("(inserts")
            self.indent_sexp()
            if not len(fields1542) == 0:
                self.newline()
                for i1544, elem1543 in enumerate(fields1542):
                    if (i1544 > 0):
                        self.newline()
                    self.pretty_target_relation(elem1543)
            self.dedent()
            self.write(")")

    def pretty_cdc_deletes(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1549 = self._try_flat(msg, self.pretty_cdc_deletes)
        if flat1549 is not None:
            assert flat1549 is not None
            self.write(flat1549)
            return None
        else:
            fields1546 = msg
            self.write("(deletes")
            self.indent_sexp()
            if not len(fields1546) == 0:
                self.newline()
                for i1548, elem1547 in enumerate(fields1546):
                    if (i1548 > 0):
                        self.newline()
                    self.pretty_target_relation(elem1547)
            self.dedent()
            self.write(")")

    def pretty_load_errors(self, msg: logic_pb2.RelationId):
        flat1551 = self._try_flat(msg, self.pretty_load_errors)
        if flat1551 is not None:
            assert flat1551 is not None
            self.write(flat1551)
            return None
        else:
            fields1550 = msg
            self.write("(load_errors")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1550)
            self.dedent()
            self.write(")")

    def pretty_csv_asof(self, msg: str):
        flat1553 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1553 is not None:
            assert flat1553 is not None
            self.write(flat1553)
            return None
        else:
            fields1552 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1552))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1567 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1567 is not None:
            assert flat1567 is not None
            self.write(flat1567)
            return None
        else:
            _dollar_dollar = msg
            _t1859 = self.deconstruct_iceberg_data_columns_optional(_dollar_dollar)
            _t1860 = self.deconstruct_iceberg_data_relations_optional(_dollar_dollar)
            _t1861 = self.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
            _t1862 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1554 = (_dollar_dollar.locator, _dollar_dollar.config, _t1859, _t1860, _t1861, _t1862, _dollar_dollar.returns_delta,)
            assert fields1554 is not None
            unwrapped_fields1555 = fields1554
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1556 = unwrapped_fields1555[0]
            self.pretty_iceberg_locator(field1556)
            self.newline()
            field1557 = unwrapped_fields1555[1]
            self.pretty_iceberg_catalog_config(field1557)
            field1558 = unwrapped_fields1555[2]
            if field1558 is not None:
                self.newline()
                assert field1558 is not None
                opt_val1559 = field1558
                self.pretty_gnf_columns(opt_val1559)
            field1560 = unwrapped_fields1555[3]
            if field1560 is not None:
                self.newline()
                assert field1560 is not None
                opt_val1561 = field1560
                self.pretty_target_relations(opt_val1561)
            field1562 = unwrapped_fields1555[4]
            if field1562 is not None:
                self.newline()
                assert field1562 is not None
                opt_val1563 = field1562
                self.pretty_iceberg_from_snapshot(opt_val1563)
            field1564 = unwrapped_fields1555[5]
            if field1564 is not None:
                self.newline()
                assert field1564 is not None
                opt_val1565 = field1564
                self.pretty_iceberg_to_snapshot(opt_val1565)
            self.newline()
            field1566 = unwrapped_fields1555[6]
            self.pretty_boolean_value(field1566)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1573 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1573 is not None:
            assert flat1573 is not None
            self.write(flat1573)
            return None
        else:
            _dollar_dollar = msg
            fields1568 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1568 is not None
            unwrapped_fields1569 = fields1568
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            field1570 = unwrapped_fields1569[0]
            self.pretty_iceberg_locator_table_name(field1570)
            self.newline()
            field1571 = unwrapped_fields1569[1]
            self.pretty_iceberg_locator_namespace(field1571)
            self.newline()
            field1572 = unwrapped_fields1569[2]
            self.pretty_iceberg_locator_warehouse(field1572)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_table_name(self, msg: str):
        flat1575 = self._try_flat(msg, self.pretty_iceberg_locator_table_name)
        if flat1575 is not None:
            assert flat1575 is not None
            self.write(flat1575)
            return None
        else:
            fields1574 = msg
            self.write("(table_name")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1574))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_namespace(self, msg: Sequence[str]):
        flat1579 = self._try_flat(msg, self.pretty_iceberg_locator_namespace)
        if flat1579 is not None:
            assert flat1579 is not None
            self.write(flat1579)
            return None
        else:
            fields1576 = msg
            self.write("(namespace")
            self.indent_sexp()
            if not len(fields1576) == 0:
                self.newline()
                for i1578, elem1577 in enumerate(fields1576):
                    if (i1578 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1577))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_warehouse(self, msg: str):
        flat1581 = self._try_flat(msg, self.pretty_iceberg_locator_warehouse)
        if flat1581 is not None:
            assert flat1581 is not None
            self.write(flat1581)
            return None
        else:
            fields1580 = msg
            self.write("(warehouse")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1580))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1589 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1589 is not None:
            assert flat1589 is not None
            self.write(flat1589)
            return None
        else:
            _dollar_dollar = msg
            _t1863 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1582 = (_dollar_dollar.catalog_uri, _t1863, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1582 is not None
            unwrapped_fields1583 = fields1582
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            field1584 = unwrapped_fields1583[0]
            self.pretty_iceberg_catalog_uri(field1584)
            field1585 = unwrapped_fields1583[1]
            if field1585 is not None:
                self.newline()
                assert field1585 is not None
                opt_val1586 = field1585
                self.pretty_iceberg_catalog_config_scope(opt_val1586)
            self.newline()
            field1587 = unwrapped_fields1583[2]
            self.pretty_iceberg_properties(field1587)
            self.newline()
            field1588 = unwrapped_fields1583[3]
            self.pretty_iceberg_auth_properties(field1588)
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_uri(self, msg: str):
        flat1591 = self._try_flat(msg, self.pretty_iceberg_catalog_uri)
        if flat1591 is not None:
            assert flat1591 is not None
            self.write(flat1591)
            return None
        else:
            fields1590 = msg
            self.write("(catalog_uri")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1590))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1593 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1593 is not None:
            assert flat1593 is not None
            self.write(flat1593)
            return None
        else:
            fields1592 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1592))
            self.dedent()
            self.write(")")

    def pretty_iceberg_properties(self, msg: Sequence[tuple[str, str]]):
        flat1597 = self._try_flat(msg, self.pretty_iceberg_properties)
        if flat1597 is not None:
            assert flat1597 is not None
            self.write(flat1597)
            return None
        else:
            fields1594 = msg
            self.write("(properties")
            self.indent_sexp()
            if not len(fields1594) == 0:
                self.newline()
                for i1596, elem1595 in enumerate(fields1594):
                    if (i1596 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1595)
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1602 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1602 is not None:
            assert flat1602 is not None
            self.write(flat1602)
            return None
        else:
            _dollar_dollar = msg
            fields1598 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1598 is not None
            unwrapped_fields1599 = fields1598
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1600 = unwrapped_fields1599[0]
            self.write(self.format_string_value(field1600))
            self.newline()
            field1601 = unwrapped_fields1599[1]
            self.write(self.format_string_value(field1601))
            self.dedent()
            self.write(")")

    def pretty_iceberg_auth_properties(self, msg: Sequence[tuple[str, str]]):
        flat1606 = self._try_flat(msg, self.pretty_iceberg_auth_properties)
        if flat1606 is not None:
            assert flat1606 is not None
            self.write(flat1606)
            return None
        else:
            fields1603 = msg
            self.write("(auth_properties")
            self.indent_sexp()
            if not len(fields1603) == 0:
                self.newline()
                for i1605, elem1604 in enumerate(fields1603):
                    if (i1605 > 0):
                        self.newline()
                    self.pretty_iceberg_masked_property_entry(elem1604)
            self.dedent()
            self.write(")")

    def pretty_iceberg_masked_property_entry(self, msg: tuple[str, str]):
        flat1611 = self._try_flat(msg, self.pretty_iceberg_masked_property_entry)
        if flat1611 is not None:
            assert flat1611 is not None
            self.write(flat1611)
            return None
        else:
            _dollar_dollar = msg
            _t1864 = self.mask_secret_value(_dollar_dollar)
            fields1607 = (_dollar_dollar[0], _t1864,)
            assert fields1607 is not None
            unwrapped_fields1608 = fields1607
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1609 = unwrapped_fields1608[0]
            self.write(self.format_string_value(field1609))
            self.newline()
            field1610 = unwrapped_fields1608[1]
            self.write(self.format_string_value(field1610))
            self.dedent()
            self.write(")")

    def pretty_iceberg_from_snapshot(self, msg: str):
        flat1613 = self._try_flat(msg, self.pretty_iceberg_from_snapshot)
        if flat1613 is not None:
            assert flat1613 is not None
            self.write(flat1613)
            return None
        else:
            fields1612 = msg
            self.write("(from_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1612))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1615 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1615 is not None:
            assert flat1615 is not None
            self.write(flat1615)
            return None
        else:
            fields1614 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1614))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1618 = self._try_flat(msg, self.pretty_undefine)
        if flat1618 is not None:
            assert flat1618 is not None
            self.write(flat1618)
            return None
        else:
            _dollar_dollar = msg
            fields1616 = _dollar_dollar.fragment_id
            assert fields1616 is not None
            unwrapped_fields1617 = fields1616
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1617)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1623 = self._try_flat(msg, self.pretty_context)
        if flat1623 is not None:
            assert flat1623 is not None
            self.write(flat1623)
            return None
        else:
            _dollar_dollar = msg
            fields1619 = _dollar_dollar.relations
            assert fields1619 is not None
            unwrapped_fields1620 = fields1619
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1620) == 0:
                self.newline()
                for i1622, elem1621 in enumerate(unwrapped_fields1620):
                    if (i1622 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1621)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1630 = self._try_flat(msg, self.pretty_snapshot)
        if flat1630 is not None:
            assert flat1630 is not None
            self.write(flat1630)
            return None
        else:
            _dollar_dollar = msg
            fields1624 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
            assert fields1624 is not None
            unwrapped_fields1625 = fields1624
            self.write("(snapshot")
            self.indent_sexp()
            self.newline()
            field1626 = unwrapped_fields1625[0]
            self.pretty_edb_path(field1626)
            field1627 = unwrapped_fields1625[1]
            if not len(field1627) == 0:
                self.newline()
                for i1629, elem1628 in enumerate(field1627):
                    if (i1629 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1628)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1635 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1635 is not None:
            assert flat1635 is not None
            self.write(flat1635)
            return None
        else:
            _dollar_dollar = msg
            fields1631 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1631 is not None
            unwrapped_fields1632 = fields1631
            field1633 = unwrapped_fields1632[0]
            self.pretty_edb_path(field1633)
            self.write(" ")
            field1634 = unwrapped_fields1632[1]
            self.pretty_relation_id(field1634)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1639 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1639 is not None:
            assert flat1639 is not None
            self.write(flat1639)
            return None
        else:
            fields1636 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1636) == 0:
                self.newline()
                for i1638, elem1637 in enumerate(fields1636):
                    if (i1638 > 0):
                        self.newline()
                    self.pretty_read(elem1637)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1650 = self._try_flat(msg, self.pretty_read)
        if flat1650 is not None:
            assert flat1650 is not None
            self.write(flat1650)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1865 = _dollar_dollar.demand
            else:
                _t1865 = None
            deconstruct_result1648 = _t1865
            if deconstruct_result1648 is not None:
                assert deconstruct_result1648 is not None
                unwrapped1649 = deconstruct_result1648
                self.pretty_demand(unwrapped1649)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1866 = _dollar_dollar.output
                else:
                    _t1866 = None
                deconstruct_result1646 = _t1866
                if deconstruct_result1646 is not None:
                    assert deconstruct_result1646 is not None
                    unwrapped1647 = deconstruct_result1646
                    self.pretty_output(unwrapped1647)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1867 = _dollar_dollar.what_if
                    else:
                        _t1867 = None
                    deconstruct_result1644 = _t1867
                    if deconstruct_result1644 is not None:
                        assert deconstruct_result1644 is not None
                        unwrapped1645 = deconstruct_result1644
                        self.pretty_what_if(unwrapped1645)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1868 = _dollar_dollar.abort
                        else:
                            _t1868 = None
                        deconstruct_result1642 = _t1868
                        if deconstruct_result1642 is not None:
                            assert deconstruct_result1642 is not None
                            unwrapped1643 = deconstruct_result1642
                            self.pretty_abort(unwrapped1643)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1869 = _dollar_dollar.export
                            else:
                                _t1869 = None
                            deconstruct_result1640 = _t1869
                            if deconstruct_result1640 is not None:
                                assert deconstruct_result1640 is not None
                                unwrapped1641 = deconstruct_result1640
                                self.pretty_export(unwrapped1641)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1653 = self._try_flat(msg, self.pretty_demand)
        if flat1653 is not None:
            assert flat1653 is not None
            self.write(flat1653)
            return None
        else:
            _dollar_dollar = msg
            fields1651 = _dollar_dollar.relation_id
            assert fields1651 is not None
            unwrapped_fields1652 = fields1651
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1652)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1658 = self._try_flat(msg, self.pretty_output)
        if flat1658 is not None:
            assert flat1658 is not None
            self.write(flat1658)
            return None
        else:
            _dollar_dollar = msg
            fields1654 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1654 is not None
            unwrapped_fields1655 = fields1654
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1656 = unwrapped_fields1655[0]
            self.pretty_name(field1656)
            self.newline()
            field1657 = unwrapped_fields1655[1]
            self.pretty_relation_id(field1657)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1663 = self._try_flat(msg, self.pretty_what_if)
        if flat1663 is not None:
            assert flat1663 is not None
            self.write(flat1663)
            return None
        else:
            _dollar_dollar = msg
            fields1659 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1659 is not None
            unwrapped_fields1660 = fields1659
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1661 = unwrapped_fields1660[0]
            self.pretty_name(field1661)
            self.newline()
            field1662 = unwrapped_fields1660[1]
            self.pretty_epoch(field1662)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1669 = self._try_flat(msg, self.pretty_abort)
        if flat1669 is not None:
            assert flat1669 is not None
            self.write(flat1669)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1870 = _dollar_dollar.name
            else:
                _t1870 = None
            fields1664 = (_t1870, _dollar_dollar.relation_id,)
            assert fields1664 is not None
            unwrapped_fields1665 = fields1664
            self.write("(abort")
            self.indent_sexp()
            field1666 = unwrapped_fields1665[0]
            if field1666 is not None:
                self.newline()
                assert field1666 is not None
                opt_val1667 = field1666
                self.pretty_name(opt_val1667)
            self.newline()
            field1668 = unwrapped_fields1665[1]
            self.pretty_relation_id(field1668)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1674 = self._try_flat(msg, self.pretty_export)
        if flat1674 is not None:
            assert flat1674 is not None
            self.write(flat1674)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1871 = _dollar_dollar.csv_config
            else:
                _t1871 = None
            deconstruct_result1672 = _t1871
            if deconstruct_result1672 is not None:
                assert deconstruct_result1672 is not None
                unwrapped1673 = deconstruct_result1672
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1673)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1872 = _dollar_dollar.iceberg_config
                else:
                    _t1872 = None
                deconstruct_result1670 = _t1872
                if deconstruct_result1670 is not None:
                    assert deconstruct_result1670 is not None
                    unwrapped1671 = deconstruct_result1670
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1671)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1685 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1685 is not None:
            assert flat1685 is not None
            self.write(flat1685)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1874 = self.deconstruct_export_csv_output_location(_dollar_dollar)
                _t1873 = (_t1874, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1873 = None
            deconstruct_result1680 = _t1873
            if deconstruct_result1680 is not None:
                assert deconstruct_result1680 is not None
                unwrapped1681 = deconstruct_result1680
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1682 = unwrapped1681[0]
                self.pretty_export_csv_output_location(field1682)
                self.newline()
                field1683 = unwrapped1681[1]
                self.pretty_export_csv_source(field1683)
                self.newline()
                field1684 = unwrapped1681[2]
                self.pretty_csv_config(field1684)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1876 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1875 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1876,)
                else:
                    _t1875 = None
                deconstruct_result1675 = _t1875
                if deconstruct_result1675 is not None:
                    assert deconstruct_result1675 is not None
                    unwrapped1676 = deconstruct_result1675
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1677 = unwrapped1676[0]
                    self.pretty_export_csv_path(field1677)
                    self.newline()
                    field1678 = unwrapped1676[1]
                    self.pretty_export_csv_columns_list(field1678)
                    self.newline()
                    field1679 = unwrapped1676[2]
                    self.pretty_config_dict(field1679)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_output_location(self, msg: tuple[str, str]):
        flat1690 = self._try_flat(msg, self.pretty_export_csv_output_location)
        if flat1690 is not None:
            assert flat1690 is not None
            self.write(flat1690)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar[0] != "":
                _t1877 = _dollar_dollar[0]
            else:
                _t1877 = None
            deconstruct_result1688 = _t1877
            if deconstruct_result1688 is not None:
                assert deconstruct_result1688 is not None
                unwrapped1689 = deconstruct_result1688
                self.write("(path")
                self.indent_sexp()
                self.newline()
                self.write(self.format_string_value(unwrapped1689))
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar[1] != "":
                    _t1878 = _dollar_dollar[1]
                else:
                    _t1878 = None
                deconstruct_result1686 = _t1878
                if deconstruct_result1686 is not None:
                    assert deconstruct_result1686 is not None
                    unwrapped1687 = deconstruct_result1686
                    self.write("(transaction_output_name")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_name(unwrapped1687)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_output_location")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1697 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1697 is not None:
            assert flat1697 is not None
            self.write(flat1697)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1879 = _dollar_dollar.gnf_columns.columns
            else:
                _t1879 = None
            deconstruct_result1693 = _t1879
            if deconstruct_result1693 is not None:
                assert deconstruct_result1693 is not None
                unwrapped1694 = deconstruct_result1693
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1694) == 0:
                    self.newline()
                    for i1696, elem1695 in enumerate(unwrapped1694):
                        if (i1696 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1695)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1880 = _dollar_dollar.table_def
                else:
                    _t1880 = None
                deconstruct_result1691 = _t1880
                if deconstruct_result1691 is not None:
                    assert deconstruct_result1691 is not None
                    unwrapped1692 = deconstruct_result1691
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1692)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1702 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1702 is not None:
            assert flat1702 is not None
            self.write(flat1702)
            return None
        else:
            _dollar_dollar = msg
            fields1698 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1698 is not None
            unwrapped_fields1699 = fields1698
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1700 = unwrapped_fields1699[0]
            self.write(self.format_string_value(field1700))
            self.newline()
            field1701 = unwrapped_fields1699[1]
            self.pretty_relation_id(field1701)
            self.dedent()
            self.write(")")

    def pretty_export_csv_path(self, msg: str):
        flat1704 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1704 is not None:
            assert flat1704 is not None
            self.write(flat1704)
            return None
        else:
            fields1703 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1703))
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1708 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1708 is not None:
            assert flat1708 is not None
            self.write(flat1708)
            return None
        else:
            fields1705 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1705) == 0:
                self.newline()
                for i1707, elem1706 in enumerate(fields1705):
                    if (i1707 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1706)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1717 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1717 is not None:
            assert flat1717 is not None
            self.write(flat1717)
            return None
        else:
            _dollar_dollar = msg
            _t1881 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1709 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sorted(_dollar_dollar.table_properties.items()), _t1881,)
            assert fields1709 is not None
            unwrapped_fields1710 = fields1709
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1711 = unwrapped_fields1710[0]
            self.pretty_iceberg_locator(field1711)
            self.newline()
            field1712 = unwrapped_fields1710[1]
            self.pretty_iceberg_catalog_config(field1712)
            self.newline()
            field1713 = unwrapped_fields1710[2]
            self.pretty_export_iceberg_table_def(field1713)
            self.newline()
            field1714 = unwrapped_fields1710[3]
            self.pretty_iceberg_table_properties(field1714)
            field1715 = unwrapped_fields1710[4]
            if field1715 is not None:
                self.newline()
                assert field1715 is not None
                opt_val1716 = field1715
                self.pretty_config_dict(opt_val1716)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_table_def(self, msg: logic_pb2.RelationId):
        flat1719 = self._try_flat(msg, self.pretty_export_iceberg_table_def)
        if flat1719 is not None:
            assert flat1719 is not None
            self.write(flat1719)
            return None
        else:
            fields1718 = msg
            self.write("(table_def")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1718)
            self.dedent()
            self.write(")")

    def pretty_iceberg_table_properties(self, msg: Sequence[tuple[str, str]]):
        flat1723 = self._try_flat(msg, self.pretty_iceberg_table_properties)
        if flat1723 is not None:
            assert flat1723 is not None
            self.write(flat1723)
            return None
        else:
            fields1720 = msg
            self.write("(table_properties")
            self.indent_sexp()
            if not len(fields1720) == 0:
                self.newline()
                for i1722, elem1721 in enumerate(fields1720):
                    if (i1722 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1721)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1938 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1938)
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
