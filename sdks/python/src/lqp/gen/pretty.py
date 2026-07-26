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

    def deconstruct_csv_data_columns_optional(self, msg: logic_pb2.CSVData) -> Sequence[logic_pb2.GNFColumn] | None:
        if msg.HasField("relations"):
            return None
        else:
            _t1854 = None
        return msg.columns

    def deconstruct_csv_data_relations_optional(self, msg: logic_pb2.CSVData) -> logic_pb2.TargetRelations | None:
        if msg.HasField("relations"):
            assert msg.relations is not None
            return msg.relations
        else:
            _t1855 = None
        return None

    def deconstruct_export_csv_output_location(self, msg: transactions_pb2.ExportCSVConfig) -> tuple[str, str]:
        return (msg.path, msg.transaction_output_name,)

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1856 = logic_pb2.Value(int32_value=v)
        return _t1856

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1857 = logic_pb2.Value(int_value=v)
        return _t1857

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1858 = logic_pb2.Value(float_value=v)
        return _t1858

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1859 = logic_pb2.Value(string_value=v)
        return _t1859

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1860 = logic_pb2.Value(boolean_value=v)
        return _t1860

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1861 = logic_pb2.Value(uint128_value=v)
        return _t1861

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1862 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1862,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1863 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1863,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1864 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1864,))
        _t1865 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1865,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1866 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1866,))
        _t1867 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1867,))
        if msg.new_line != "":
            _t1868 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1868,))
        _t1869 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1869,))
        _t1870 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1870,))
        _t1871 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1871,))
        if msg.comment != "":
            _t1872 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1872,))
        for missing_string in msg.missing_strings:
            _t1873 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1873,))
        _t1874 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1874,))
        _t1875 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1875,))
        _t1876 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1876,))
        if msg.partition_size_mb != 0:
            _t1877 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1877,))
        return sorted(result)

    def deconstruct_csv_storage_integration_optional(self, msg: logic_pb2.CSVConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        if not msg.HasField("storage_integration"):
            return None
        else:
            _t1878 = None
        assert msg.storage_integration is not None
        si = msg.storage_integration
        result = []
        if si.provider != "":
            _t1879 = self._make_value_string(si.provider)
            result.append(("provider", _t1879,))
        if si.azure_sas_token != "":
            _t1880 = self._make_value_string("***")
            result.append(("azure_sas_token", _t1880,))
        if si.s3_region != "":
            _t1881 = self._make_value_string(si.s3_region)
            result.append(("s3_region", _t1881,))
        if si.s3_access_key_id != "":
            _t1882 = self._make_value_string("***")
            result.append(("s3_access_key_id", _t1882,))
        if si.s3_secret_access_key != "":
            _t1883 = self._make_value_string("***")
            result.append(("s3_secret_access_key", _t1883,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1884 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1884,))
        _t1885 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1885,))
        _t1886 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1886,))
        _t1887 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1887,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1888 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1888,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1889 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1889,))
        _t1890 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1890,))
        _t1891 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1891,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1892 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1892,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1893 = self._make_value_string(msg.compression)
            result.append(("compression", _t1893,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1894 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1894,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1895 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1895,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1896 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1896,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1897 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1897,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1898 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1898,))
        return sorted(result)

    def mask_secret_value(self, pair: tuple[str, str]) -> str:
        return "***"

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1899 = None
        return None

    def deconstruct_iceberg_data_from_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.from_snapshot is not None
        if msg.from_snapshot != "":
            assert msg.from_snapshot is not None
            return msg.from_snapshot
        else:
            _t1900 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1901 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1902 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1902,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1903 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1903,))
        if msg.compression != "":
            _t1904 = self._make_value_string(msg.compression)
            result.append(("compression", _t1904,))
        if len(result) == 0:
            return None
        else:
            _t1905 = None
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
            _t1906 = None
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
        flat859 = self._try_flat(msg, self.pretty_transaction)
        if flat859 is not None:
            assert flat859 is not None
            self.write(flat859)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1700 = _dollar_dollar.configure
            else:
                _t1700 = None
            if _dollar_dollar.HasField("sync"):
                _t1701 = _dollar_dollar.sync
            else:
                _t1701 = None
            fields850 = (_t1700, _t1701, _dollar_dollar.epochs,)
            assert fields850 is not None
            unwrapped_fields851 = fields850
            self.write("(transaction")
            self.indent_sexp()
            field852 = unwrapped_fields851[0]
            if field852 is not None:
                self.newline()
                assert field852 is not None
                opt_val853 = field852
                self.pretty_configure(opt_val853)
            field854 = unwrapped_fields851[1]
            if field854 is not None:
                self.newline()
                assert field854 is not None
                opt_val855 = field854
                self.pretty_sync(opt_val855)
            field856 = unwrapped_fields851[2]
            if not len(field856) == 0:
                self.newline()
                for i858, elem857 in enumerate(field856):
                    if (i858 > 0):
                        self.newline()
                    self.pretty_epoch(elem857)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat862 = self._try_flat(msg, self.pretty_configure)
        if flat862 is not None:
            assert flat862 is not None
            self.write(flat862)
            return None
        else:
            _dollar_dollar = msg
            _t1702 = self.deconstruct_configure(_dollar_dollar)
            fields860 = _t1702
            assert fields860 is not None
            unwrapped_fields861 = fields860
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields861)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat866 = self._try_flat(msg, self.pretty_config_dict)
        if flat866 is not None:
            assert flat866 is not None
            self.write(flat866)
            return None
        else:
            fields863 = msg
            self.write("{")
            self.indent()
            if not len(fields863) == 0:
                self.newline()
                for i865, elem864 in enumerate(fields863):
                    if (i865 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem864)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat871 = self._try_flat(msg, self.pretty_config_key_value)
        if flat871 is not None:
            assert flat871 is not None
            self.write(flat871)
            return None
        else:
            _dollar_dollar = msg
            fields867 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields867 is not None
            unwrapped_fields868 = fields867
            self.write(":")
            field869 = unwrapped_fields868[0]
            self.write(field869)
            self.write(" ")
            field870 = unwrapped_fields868[1]
            self.pretty_raw_value(field870)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat897 = self._try_flat(msg, self.pretty_raw_value)
        if flat897 is not None:
            assert flat897 is not None
            self.write(flat897)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1703 = _dollar_dollar.date_value
            else:
                _t1703 = None
            deconstruct_result895 = _t1703
            if deconstruct_result895 is not None:
                assert deconstruct_result895 is not None
                unwrapped896 = deconstruct_result895
                self.pretty_raw_date(unwrapped896)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1704 = _dollar_dollar.datetime_value
                else:
                    _t1704 = None
                deconstruct_result893 = _t1704
                if deconstruct_result893 is not None:
                    assert deconstruct_result893 is not None
                    unwrapped894 = deconstruct_result893
                    self.pretty_raw_datetime(unwrapped894)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1705 = _dollar_dollar.string_value
                    else:
                        _t1705 = None
                    deconstruct_result891 = _t1705
                    if deconstruct_result891 is not None:
                        assert deconstruct_result891 is not None
                        unwrapped892 = deconstruct_result891
                        self.write(self.format_string_value(unwrapped892))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1706 = _dollar_dollar.int32_value
                        else:
                            _t1706 = None
                        deconstruct_result889 = _t1706
                        if deconstruct_result889 is not None:
                            assert deconstruct_result889 is not None
                            unwrapped890 = deconstruct_result889
                            self.write((str(unwrapped890) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1707 = _dollar_dollar.int_value
                            else:
                                _t1707 = None
                            deconstruct_result887 = _t1707
                            if deconstruct_result887 is not None:
                                assert deconstruct_result887 is not None
                                unwrapped888 = deconstruct_result887
                                self.write(str(unwrapped888))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1708 = _dollar_dollar.float32_value
                                else:
                                    _t1708 = None
                                deconstruct_result885 = _t1708
                                if deconstruct_result885 is not None:
                                    assert deconstruct_result885 is not None
                                    unwrapped886 = deconstruct_result885
                                    self.write(self.format_float32_literal(unwrapped886))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1709 = _dollar_dollar.float_value
                                    else:
                                        _t1709 = None
                                    deconstruct_result883 = _t1709
                                    if deconstruct_result883 is not None:
                                        assert deconstruct_result883 is not None
                                        unwrapped884 = deconstruct_result883
                                        self.write(str(unwrapped884))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1710 = _dollar_dollar.uint32_value
                                        else:
                                            _t1710 = None
                                        deconstruct_result881 = _t1710
                                        if deconstruct_result881 is not None:
                                            assert deconstruct_result881 is not None
                                            unwrapped882 = deconstruct_result881
                                            self.write((str(unwrapped882) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1711 = _dollar_dollar.uint128_value
                                            else:
                                                _t1711 = None
                                            deconstruct_result879 = _t1711
                                            if deconstruct_result879 is not None:
                                                assert deconstruct_result879 is not None
                                                unwrapped880 = deconstruct_result879
                                                self.write(self.format_uint128(unwrapped880))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1712 = _dollar_dollar.int128_value
                                                else:
                                                    _t1712 = None
                                                deconstruct_result877 = _t1712
                                                if deconstruct_result877 is not None:
                                                    assert deconstruct_result877 is not None
                                                    unwrapped878 = deconstruct_result877
                                                    self.write(self.format_int128(unwrapped878))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1713 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1713 = None
                                                    deconstruct_result875 = _t1713
                                                    if deconstruct_result875 is not None:
                                                        assert deconstruct_result875 is not None
                                                        unwrapped876 = deconstruct_result875
                                                        self.write(self.format_decimal(unwrapped876))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1714 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1714 = None
                                                        deconstruct_result873 = _t1714
                                                        if deconstruct_result873 is not None:
                                                            assert deconstruct_result873 is not None
                                                            unwrapped874 = deconstruct_result873
                                                            self.pretty_boolean_value(unwrapped874)
                                                        else:
                                                            fields872 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat903 = self._try_flat(msg, self.pretty_raw_date)
        if flat903 is not None:
            assert flat903 is not None
            self.write(flat903)
            return None
        else:
            _dollar_dollar = msg
            fields898 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields898 is not None
            unwrapped_fields899 = fields898
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field900 = unwrapped_fields899[0]
            self.write(str(field900))
            self.newline()
            field901 = unwrapped_fields899[1]
            self.write(str(field901))
            self.newline()
            field902 = unwrapped_fields899[2]
            self.write(str(field902))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat914 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat914 is not None:
            assert flat914 is not None
            self.write(flat914)
            return None
        else:
            _dollar_dollar = msg
            fields904 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields904 is not None
            unwrapped_fields905 = fields904
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field906 = unwrapped_fields905[0]
            self.write(str(field906))
            self.newline()
            field907 = unwrapped_fields905[1]
            self.write(str(field907))
            self.newline()
            field908 = unwrapped_fields905[2]
            self.write(str(field908))
            self.newline()
            field909 = unwrapped_fields905[3]
            self.write(str(field909))
            self.newline()
            field910 = unwrapped_fields905[4]
            self.write(str(field910))
            self.newline()
            field911 = unwrapped_fields905[5]
            self.write(str(field911))
            field912 = unwrapped_fields905[6]
            if field912 is not None:
                self.newline()
                assert field912 is not None
                opt_val913 = field912
                self.write(str(opt_val913))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1715 = ()
        else:
            _t1715 = None
        deconstruct_result917 = _t1715
        if deconstruct_result917 is not None:
            assert deconstruct_result917 is not None
            unwrapped918 = deconstruct_result917
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1716 = ()
            else:
                _t1716 = None
            deconstruct_result915 = _t1716
            if deconstruct_result915 is not None:
                assert deconstruct_result915 is not None
                unwrapped916 = deconstruct_result915
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat923 = self._try_flat(msg, self.pretty_sync)
        if flat923 is not None:
            assert flat923 is not None
            self.write(flat923)
            return None
        else:
            _dollar_dollar = msg
            fields919 = _dollar_dollar.fragments
            assert fields919 is not None
            unwrapped_fields920 = fields919
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields920) == 0:
                self.newline()
                for i922, elem921 in enumerate(unwrapped_fields920):
                    if (i922 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem921)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat926 = self._try_flat(msg, self.pretty_fragment_id)
        if flat926 is not None:
            assert flat926 is not None
            self.write(flat926)
            return None
        else:
            _dollar_dollar = msg
            fields924 = self.fragment_id_to_string(_dollar_dollar)
            assert fields924 is not None
            unwrapped_fields925 = fields924
            self.write(":")
            self.write(unwrapped_fields925)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat933 = self._try_flat(msg, self.pretty_epoch)
        if flat933 is not None:
            assert flat933 is not None
            self.write(flat933)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1717 = _dollar_dollar.writes
            else:
                _t1717 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1718 = _dollar_dollar.reads
            else:
                _t1718 = None
            fields927 = (_t1717, _t1718,)
            assert fields927 is not None
            unwrapped_fields928 = fields927
            self.write("(epoch")
            self.indent_sexp()
            field929 = unwrapped_fields928[0]
            if field929 is not None:
                self.newline()
                assert field929 is not None
                opt_val930 = field929
                self.pretty_epoch_writes(opt_val930)
            field931 = unwrapped_fields928[1]
            if field931 is not None:
                self.newline()
                assert field931 is not None
                opt_val932 = field931
                self.pretty_epoch_reads(opt_val932)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat937 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat937 is not None:
            assert flat937 is not None
            self.write(flat937)
            return None
        else:
            fields934 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields934) == 0:
                self.newline()
                for i936, elem935 in enumerate(fields934):
                    if (i936 > 0):
                        self.newline()
                    self.pretty_write(elem935)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat946 = self._try_flat(msg, self.pretty_write)
        if flat946 is not None:
            assert flat946 is not None
            self.write(flat946)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1719 = _dollar_dollar.define
            else:
                _t1719 = None
            deconstruct_result944 = _t1719
            if deconstruct_result944 is not None:
                assert deconstruct_result944 is not None
                unwrapped945 = deconstruct_result944
                self.pretty_define(unwrapped945)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1720 = _dollar_dollar.undefine
                else:
                    _t1720 = None
                deconstruct_result942 = _t1720
                if deconstruct_result942 is not None:
                    assert deconstruct_result942 is not None
                    unwrapped943 = deconstruct_result942
                    self.pretty_undefine(unwrapped943)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1721 = _dollar_dollar.context
                    else:
                        _t1721 = None
                    deconstruct_result940 = _t1721
                    if deconstruct_result940 is not None:
                        assert deconstruct_result940 is not None
                        unwrapped941 = deconstruct_result940
                        self.pretty_context(unwrapped941)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1722 = _dollar_dollar.snapshot
                        else:
                            _t1722 = None
                        deconstruct_result938 = _t1722
                        if deconstruct_result938 is not None:
                            assert deconstruct_result938 is not None
                            unwrapped939 = deconstruct_result938
                            self.pretty_snapshot(unwrapped939)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat949 = self._try_flat(msg, self.pretty_define)
        if flat949 is not None:
            assert flat949 is not None
            self.write(flat949)
            return None
        else:
            _dollar_dollar = msg
            fields947 = _dollar_dollar.fragment
            assert fields947 is not None
            unwrapped_fields948 = fields947
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields948)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat956 = self._try_flat(msg, self.pretty_fragment)
        if flat956 is not None:
            assert flat956 is not None
            self.write(flat956)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields950 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields950 is not None
            unwrapped_fields951 = fields950
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field952 = unwrapped_fields951[0]
            self.pretty_new_fragment_id(field952)
            field953 = unwrapped_fields951[1]
            if not len(field953) == 0:
                self.newline()
                for i955, elem954 in enumerate(field953):
                    if (i955 > 0):
                        self.newline()
                    self.pretty_declaration(elem954)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat958 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat958 is not None:
            assert flat958 is not None
            self.write(flat958)
            return None
        else:
            fields957 = msg
            self.pretty_fragment_id(fields957)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat967 = self._try_flat(msg, self.pretty_declaration)
        if flat967 is not None:
            assert flat967 is not None
            self.write(flat967)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1723 = getattr(_dollar_dollar, 'def')
            else:
                _t1723 = None
            deconstruct_result965 = _t1723
            if deconstruct_result965 is not None:
                assert deconstruct_result965 is not None
                unwrapped966 = deconstruct_result965
                self.pretty_def(unwrapped966)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1724 = _dollar_dollar.algorithm
                else:
                    _t1724 = None
                deconstruct_result963 = _t1724
                if deconstruct_result963 is not None:
                    assert deconstruct_result963 is not None
                    unwrapped964 = deconstruct_result963
                    self.pretty_algorithm(unwrapped964)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1725 = _dollar_dollar.constraint
                    else:
                        _t1725 = None
                    deconstruct_result961 = _t1725
                    if deconstruct_result961 is not None:
                        assert deconstruct_result961 is not None
                        unwrapped962 = deconstruct_result961
                        self.pretty_constraint(unwrapped962)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1726 = _dollar_dollar.data
                        else:
                            _t1726 = None
                        deconstruct_result959 = _t1726
                        if deconstruct_result959 is not None:
                            assert deconstruct_result959 is not None
                            unwrapped960 = deconstruct_result959
                            self.pretty_data(unwrapped960)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat974 = self._try_flat(msg, self.pretty_def)
        if flat974 is not None:
            assert flat974 is not None
            self.write(flat974)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1727 = _dollar_dollar.attrs
            else:
                _t1727 = None
            fields968 = (_dollar_dollar.name, _dollar_dollar.body, _t1727,)
            assert fields968 is not None
            unwrapped_fields969 = fields968
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field970 = unwrapped_fields969[0]
            self.pretty_relation_id(field970)
            self.newline()
            field971 = unwrapped_fields969[1]
            self.pretty_abstraction(field971)
            field972 = unwrapped_fields969[2]
            if field972 is not None:
                self.newline()
                assert field972 is not None
                opt_val973 = field972
                self.pretty_attrs(opt_val973)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat979 = self._try_flat(msg, self.pretty_relation_id)
        if flat979 is not None:
            assert flat979 is not None
            self.write(flat979)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1729 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1728 = _t1729
            else:
                _t1728 = None
            deconstruct_result977 = _t1728
            if deconstruct_result977 is not None:
                assert deconstruct_result977 is not None
                unwrapped978 = deconstruct_result977
                self.write(":")
                self.write(unwrapped978)
            else:
                _dollar_dollar = msg
                _t1730 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result975 = _t1730
                if deconstruct_result975 is not None:
                    assert deconstruct_result975 is not None
                    unwrapped976 = deconstruct_result975
                    self.write(self.format_uint128(unwrapped976))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat984 = self._try_flat(msg, self.pretty_abstraction)
        if flat984 is not None:
            assert flat984 is not None
            self.write(flat984)
            return None
        else:
            _dollar_dollar = msg
            _t1731 = self.deconstruct_bindings(_dollar_dollar)
            fields980 = (_t1731, _dollar_dollar.value,)
            assert fields980 is not None
            unwrapped_fields981 = fields980
            self.write("(")
            self.indent()
            field982 = unwrapped_fields981[0]
            self.pretty_bindings(field982)
            self.newline()
            field983 = unwrapped_fields981[1]
            self.pretty_formula(field983)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat992 = self._try_flat(msg, self.pretty_bindings)
        if flat992 is not None:
            assert flat992 is not None
            self.write(flat992)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1732 = _dollar_dollar[1]
            else:
                _t1732 = None
            fields985 = (_dollar_dollar[0], _t1732,)
            assert fields985 is not None
            unwrapped_fields986 = fields985
            self.write("[")
            self.indent()
            field987 = unwrapped_fields986[0]
            for i989, elem988 in enumerate(field987):
                if (i989 > 0):
                    self.newline()
                self.pretty_binding(elem988)
            field990 = unwrapped_fields986[1]
            if field990 is not None:
                self.newline()
                assert field990 is not None
                opt_val991 = field990
                self.pretty_value_bindings(opt_val991)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat997 = self._try_flat(msg, self.pretty_binding)
        if flat997 is not None:
            assert flat997 is not None
            self.write(flat997)
            return None
        else:
            _dollar_dollar = msg
            fields993 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields993 is not None
            unwrapped_fields994 = fields993
            field995 = unwrapped_fields994[0]
            self.write(field995)
            self.write("::")
            field996 = unwrapped_fields994[1]
            self.pretty_type(field996)

    def pretty_type(self, msg: logic_pb2.Type):
        flat1026 = self._try_flat(msg, self.pretty_type)
        if flat1026 is not None:
            assert flat1026 is not None
            self.write(flat1026)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1733 = _dollar_dollar.unspecified_type
            else:
                _t1733 = None
            deconstruct_result1024 = _t1733
            if deconstruct_result1024 is not None:
                assert deconstruct_result1024 is not None
                unwrapped1025 = deconstruct_result1024
                self.pretty_unspecified_type(unwrapped1025)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1734 = _dollar_dollar.string_type
                else:
                    _t1734 = None
                deconstruct_result1022 = _t1734
                if deconstruct_result1022 is not None:
                    assert deconstruct_result1022 is not None
                    unwrapped1023 = deconstruct_result1022
                    self.pretty_string_type(unwrapped1023)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1735 = _dollar_dollar.int_type
                    else:
                        _t1735 = None
                    deconstruct_result1020 = _t1735
                    if deconstruct_result1020 is not None:
                        assert deconstruct_result1020 is not None
                        unwrapped1021 = deconstruct_result1020
                        self.pretty_int_type(unwrapped1021)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1736 = _dollar_dollar.float_type
                        else:
                            _t1736 = None
                        deconstruct_result1018 = _t1736
                        if deconstruct_result1018 is not None:
                            assert deconstruct_result1018 is not None
                            unwrapped1019 = deconstruct_result1018
                            self.pretty_float_type(unwrapped1019)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1737 = _dollar_dollar.uint128_type
                            else:
                                _t1737 = None
                            deconstruct_result1016 = _t1737
                            if deconstruct_result1016 is not None:
                                assert deconstruct_result1016 is not None
                                unwrapped1017 = deconstruct_result1016
                                self.pretty_uint128_type(unwrapped1017)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1738 = _dollar_dollar.int128_type
                                else:
                                    _t1738 = None
                                deconstruct_result1014 = _t1738
                                if deconstruct_result1014 is not None:
                                    assert deconstruct_result1014 is not None
                                    unwrapped1015 = deconstruct_result1014
                                    self.pretty_int128_type(unwrapped1015)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1739 = _dollar_dollar.date_type
                                    else:
                                        _t1739 = None
                                    deconstruct_result1012 = _t1739
                                    if deconstruct_result1012 is not None:
                                        assert deconstruct_result1012 is not None
                                        unwrapped1013 = deconstruct_result1012
                                        self.pretty_date_type(unwrapped1013)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1740 = _dollar_dollar.datetime_type
                                        else:
                                            _t1740 = None
                                        deconstruct_result1010 = _t1740
                                        if deconstruct_result1010 is not None:
                                            assert deconstruct_result1010 is not None
                                            unwrapped1011 = deconstruct_result1010
                                            self.pretty_datetime_type(unwrapped1011)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1741 = _dollar_dollar.missing_type
                                            else:
                                                _t1741 = None
                                            deconstruct_result1008 = _t1741
                                            if deconstruct_result1008 is not None:
                                                assert deconstruct_result1008 is not None
                                                unwrapped1009 = deconstruct_result1008
                                                self.pretty_missing_type(unwrapped1009)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1742 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1742 = None
                                                deconstruct_result1006 = _t1742
                                                if deconstruct_result1006 is not None:
                                                    assert deconstruct_result1006 is not None
                                                    unwrapped1007 = deconstruct_result1006
                                                    self.pretty_decimal_type(unwrapped1007)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1743 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1743 = None
                                                    deconstruct_result1004 = _t1743
                                                    if deconstruct_result1004 is not None:
                                                        assert deconstruct_result1004 is not None
                                                        unwrapped1005 = deconstruct_result1004
                                                        self.pretty_boolean_type(unwrapped1005)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1744 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1744 = None
                                                        deconstruct_result1002 = _t1744
                                                        if deconstruct_result1002 is not None:
                                                            assert deconstruct_result1002 is not None
                                                            unwrapped1003 = deconstruct_result1002
                                                            self.pretty_int32_type(unwrapped1003)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1745 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1745 = None
                                                            deconstruct_result1000 = _t1745
                                                            if deconstruct_result1000 is not None:
                                                                assert deconstruct_result1000 is not None
                                                                unwrapped1001 = deconstruct_result1000
                                                                self.pretty_float32_type(unwrapped1001)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1746 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1746 = None
                                                                deconstruct_result998 = _t1746
                                                                if deconstruct_result998 is not None:
                                                                    assert deconstruct_result998 is not None
                                                                    unwrapped999 = deconstruct_result998
                                                                    self.pretty_uint32_type(unwrapped999)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields1027 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields1028 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields1029 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields1030 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields1031 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields1032 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields1033 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields1034 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields1035 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat1040 = self._try_flat(msg, self.pretty_decimal_type)
        if flat1040 is not None:
            assert flat1040 is not None
            self.write(flat1040)
            return None
        else:
            _dollar_dollar = msg
            fields1036 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields1036 is not None
            unwrapped_fields1037 = fields1036
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field1038 = unwrapped_fields1037[0]
            self.write(str(field1038))
            self.newline()
            field1039 = unwrapped_fields1037[1]
            self.write(str(field1039))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields1041 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields1042 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields1043 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields1044 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat1048 = self._try_flat(msg, self.pretty_value_bindings)
        if flat1048 is not None:
            assert flat1048 is not None
            self.write(flat1048)
            return None
        else:
            fields1045 = msg
            self.write("|")
            if not len(fields1045) == 0:
                self.write(" ")
                for i1047, elem1046 in enumerate(fields1045):
                    if (i1047 > 0):
                        self.newline()
                    self.pretty_binding(elem1046)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1075 = self._try_flat(msg, self.pretty_formula)
        if flat1075 is not None:
            assert flat1075 is not None
            self.write(flat1075)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1747 = _dollar_dollar.conjunction
            else:
                _t1747 = None
            deconstruct_result1073 = _t1747
            if deconstruct_result1073 is not None:
                assert deconstruct_result1073 is not None
                unwrapped1074 = deconstruct_result1073
                self.pretty_true(unwrapped1074)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1748 = _dollar_dollar.disjunction
                else:
                    _t1748 = None
                deconstruct_result1071 = _t1748
                if deconstruct_result1071 is not None:
                    assert deconstruct_result1071 is not None
                    unwrapped1072 = deconstruct_result1071
                    self.pretty_false(unwrapped1072)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1749 = _dollar_dollar.exists
                    else:
                        _t1749 = None
                    deconstruct_result1069 = _t1749
                    if deconstruct_result1069 is not None:
                        assert deconstruct_result1069 is not None
                        unwrapped1070 = deconstruct_result1069
                        self.pretty_exists(unwrapped1070)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1750 = _dollar_dollar.reduce
                        else:
                            _t1750 = None
                        deconstruct_result1067 = _t1750
                        if deconstruct_result1067 is not None:
                            assert deconstruct_result1067 is not None
                            unwrapped1068 = deconstruct_result1067
                            self.pretty_reduce(unwrapped1068)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1751 = _dollar_dollar.conjunction
                            else:
                                _t1751 = None
                            deconstruct_result1065 = _t1751
                            if deconstruct_result1065 is not None:
                                assert deconstruct_result1065 is not None
                                unwrapped1066 = deconstruct_result1065
                                self.pretty_conjunction(unwrapped1066)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1752 = _dollar_dollar.disjunction
                                else:
                                    _t1752 = None
                                deconstruct_result1063 = _t1752
                                if deconstruct_result1063 is not None:
                                    assert deconstruct_result1063 is not None
                                    unwrapped1064 = deconstruct_result1063
                                    self.pretty_disjunction(unwrapped1064)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1753 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1753 = None
                                    deconstruct_result1061 = _t1753
                                    if deconstruct_result1061 is not None:
                                        assert deconstruct_result1061 is not None
                                        unwrapped1062 = deconstruct_result1061
                                        self.pretty_not(unwrapped1062)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1754 = _dollar_dollar.ffi
                                        else:
                                            _t1754 = None
                                        deconstruct_result1059 = _t1754
                                        if deconstruct_result1059 is not None:
                                            assert deconstruct_result1059 is not None
                                            unwrapped1060 = deconstruct_result1059
                                            self.pretty_ffi(unwrapped1060)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1755 = _dollar_dollar.atom
                                            else:
                                                _t1755 = None
                                            deconstruct_result1057 = _t1755
                                            if deconstruct_result1057 is not None:
                                                assert deconstruct_result1057 is not None
                                                unwrapped1058 = deconstruct_result1057
                                                self.pretty_atom(unwrapped1058)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1756 = _dollar_dollar.pragma
                                                else:
                                                    _t1756 = None
                                                deconstruct_result1055 = _t1756
                                                if deconstruct_result1055 is not None:
                                                    assert deconstruct_result1055 is not None
                                                    unwrapped1056 = deconstruct_result1055
                                                    self.pretty_pragma(unwrapped1056)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1757 = _dollar_dollar.primitive
                                                    else:
                                                        _t1757 = None
                                                    deconstruct_result1053 = _t1757
                                                    if deconstruct_result1053 is not None:
                                                        assert deconstruct_result1053 is not None
                                                        unwrapped1054 = deconstruct_result1053
                                                        self.pretty_primitive(unwrapped1054)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1758 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1758 = None
                                                        deconstruct_result1051 = _t1758
                                                        if deconstruct_result1051 is not None:
                                                            assert deconstruct_result1051 is not None
                                                            unwrapped1052 = deconstruct_result1051
                                                            self.pretty_rel_atom(unwrapped1052)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1759 = _dollar_dollar.cast
                                                            else:
                                                                _t1759 = None
                                                            deconstruct_result1049 = _t1759
                                                            if deconstruct_result1049 is not None:
                                                                assert deconstruct_result1049 is not None
                                                                unwrapped1050 = deconstruct_result1049
                                                                self.pretty_cast(unwrapped1050)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields1076 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1077 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1082 = self._try_flat(msg, self.pretty_exists)
        if flat1082 is not None:
            assert flat1082 is not None
            self.write(flat1082)
            return None
        else:
            _dollar_dollar = msg
            _t1760 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1078 = (_t1760, _dollar_dollar.body.value,)
            assert fields1078 is not None
            unwrapped_fields1079 = fields1078
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1080 = unwrapped_fields1079[0]
            self.pretty_bindings(field1080)
            self.newline()
            field1081 = unwrapped_fields1079[1]
            self.pretty_formula(field1081)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1088 = self._try_flat(msg, self.pretty_reduce)
        if flat1088 is not None:
            assert flat1088 is not None
            self.write(flat1088)
            return None
        else:
            _dollar_dollar = msg
            fields1083 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1083 is not None
            unwrapped_fields1084 = fields1083
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1085 = unwrapped_fields1084[0]
            self.pretty_abstraction(field1085)
            self.newline()
            field1086 = unwrapped_fields1084[1]
            self.pretty_abstraction(field1086)
            self.newline()
            field1087 = unwrapped_fields1084[2]
            self.pretty_terms(field1087)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1092 = self._try_flat(msg, self.pretty_terms)
        if flat1092 is not None:
            assert flat1092 is not None
            self.write(flat1092)
            return None
        else:
            fields1089 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1089) == 0:
                self.newline()
                for i1091, elem1090 in enumerate(fields1089):
                    if (i1091 > 0):
                        self.newline()
                    self.pretty_term(elem1090)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1097 = self._try_flat(msg, self.pretty_term)
        if flat1097 is not None:
            assert flat1097 is not None
            self.write(flat1097)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1761 = _dollar_dollar.var
            else:
                _t1761 = None
            deconstruct_result1095 = _t1761
            if deconstruct_result1095 is not None:
                assert deconstruct_result1095 is not None
                unwrapped1096 = deconstruct_result1095
                self.pretty_var(unwrapped1096)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1762 = _dollar_dollar.constant
                else:
                    _t1762 = None
                deconstruct_result1093 = _t1762
                if deconstruct_result1093 is not None:
                    assert deconstruct_result1093 is not None
                    unwrapped1094 = deconstruct_result1093
                    self.pretty_value(unwrapped1094)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1100 = self._try_flat(msg, self.pretty_var)
        if flat1100 is not None:
            assert flat1100 is not None
            self.write(flat1100)
            return None
        else:
            _dollar_dollar = msg
            fields1098 = _dollar_dollar.name
            assert fields1098 is not None
            unwrapped_fields1099 = fields1098
            self.write(unwrapped_fields1099)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1126 = self._try_flat(msg, self.pretty_value)
        if flat1126 is not None:
            assert flat1126 is not None
            self.write(flat1126)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1763 = _dollar_dollar.date_value
            else:
                _t1763 = None
            deconstruct_result1124 = _t1763
            if deconstruct_result1124 is not None:
                assert deconstruct_result1124 is not None
                unwrapped1125 = deconstruct_result1124
                self.pretty_date(unwrapped1125)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1764 = _dollar_dollar.datetime_value
                else:
                    _t1764 = None
                deconstruct_result1122 = _t1764
                if deconstruct_result1122 is not None:
                    assert deconstruct_result1122 is not None
                    unwrapped1123 = deconstruct_result1122
                    self.pretty_datetime(unwrapped1123)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1765 = _dollar_dollar.string_value
                    else:
                        _t1765 = None
                    deconstruct_result1120 = _t1765
                    if deconstruct_result1120 is not None:
                        assert deconstruct_result1120 is not None
                        unwrapped1121 = deconstruct_result1120
                        self.write(self.format_string_value(unwrapped1121))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1766 = _dollar_dollar.int32_value
                        else:
                            _t1766 = None
                        deconstruct_result1118 = _t1766
                        if deconstruct_result1118 is not None:
                            assert deconstruct_result1118 is not None
                            unwrapped1119 = deconstruct_result1118
                            self.write((str(unwrapped1119) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1767 = _dollar_dollar.int_value
                            else:
                                _t1767 = None
                            deconstruct_result1116 = _t1767
                            if deconstruct_result1116 is not None:
                                assert deconstruct_result1116 is not None
                                unwrapped1117 = deconstruct_result1116
                                self.write(str(unwrapped1117))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1768 = _dollar_dollar.float32_value
                                else:
                                    _t1768 = None
                                deconstruct_result1114 = _t1768
                                if deconstruct_result1114 is not None:
                                    assert deconstruct_result1114 is not None
                                    unwrapped1115 = deconstruct_result1114
                                    self.write(self.format_float32_literal(unwrapped1115))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1769 = _dollar_dollar.float_value
                                    else:
                                        _t1769 = None
                                    deconstruct_result1112 = _t1769
                                    if deconstruct_result1112 is not None:
                                        assert deconstruct_result1112 is not None
                                        unwrapped1113 = deconstruct_result1112
                                        self.write(str(unwrapped1113))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1770 = _dollar_dollar.uint32_value
                                        else:
                                            _t1770 = None
                                        deconstruct_result1110 = _t1770
                                        if deconstruct_result1110 is not None:
                                            assert deconstruct_result1110 is not None
                                            unwrapped1111 = deconstruct_result1110
                                            self.write((str(unwrapped1111) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1771 = _dollar_dollar.uint128_value
                                            else:
                                                _t1771 = None
                                            deconstruct_result1108 = _t1771
                                            if deconstruct_result1108 is not None:
                                                assert deconstruct_result1108 is not None
                                                unwrapped1109 = deconstruct_result1108
                                                self.write(self.format_uint128(unwrapped1109))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1772 = _dollar_dollar.int128_value
                                                else:
                                                    _t1772 = None
                                                deconstruct_result1106 = _t1772
                                                if deconstruct_result1106 is not None:
                                                    assert deconstruct_result1106 is not None
                                                    unwrapped1107 = deconstruct_result1106
                                                    self.write(self.format_int128(unwrapped1107))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1773 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1773 = None
                                                    deconstruct_result1104 = _t1773
                                                    if deconstruct_result1104 is not None:
                                                        assert deconstruct_result1104 is not None
                                                        unwrapped1105 = deconstruct_result1104
                                                        self.write(self.format_decimal(unwrapped1105))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1774 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1774 = None
                                                        deconstruct_result1102 = _t1774
                                                        if deconstruct_result1102 is not None:
                                                            assert deconstruct_result1102 is not None
                                                            unwrapped1103 = deconstruct_result1102
                                                            self.pretty_boolean_value(unwrapped1103)
                                                        else:
                                                            fields1101 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1132 = self._try_flat(msg, self.pretty_date)
        if flat1132 is not None:
            assert flat1132 is not None
            self.write(flat1132)
            return None
        else:
            _dollar_dollar = msg
            fields1127 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1127 is not None
            unwrapped_fields1128 = fields1127
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1129 = unwrapped_fields1128[0]
            self.write(str(field1129))
            self.newline()
            field1130 = unwrapped_fields1128[1]
            self.write(str(field1130))
            self.newline()
            field1131 = unwrapped_fields1128[2]
            self.write(str(field1131))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1143 = self._try_flat(msg, self.pretty_datetime)
        if flat1143 is not None:
            assert flat1143 is not None
            self.write(flat1143)
            return None
        else:
            _dollar_dollar = msg
            fields1133 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1133 is not None
            unwrapped_fields1134 = fields1133
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1135 = unwrapped_fields1134[0]
            self.write(str(field1135))
            self.newline()
            field1136 = unwrapped_fields1134[1]
            self.write(str(field1136))
            self.newline()
            field1137 = unwrapped_fields1134[2]
            self.write(str(field1137))
            self.newline()
            field1138 = unwrapped_fields1134[3]
            self.write(str(field1138))
            self.newline()
            field1139 = unwrapped_fields1134[4]
            self.write(str(field1139))
            self.newline()
            field1140 = unwrapped_fields1134[5]
            self.write(str(field1140))
            field1141 = unwrapped_fields1134[6]
            if field1141 is not None:
                self.newline()
                assert field1141 is not None
                opt_val1142 = field1141
                self.write(str(opt_val1142))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1148 = self._try_flat(msg, self.pretty_conjunction)
        if flat1148 is not None:
            assert flat1148 is not None
            self.write(flat1148)
            return None
        else:
            _dollar_dollar = msg
            fields1144 = _dollar_dollar.args
            assert fields1144 is not None
            unwrapped_fields1145 = fields1144
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1145) == 0:
                self.newline()
                for i1147, elem1146 in enumerate(unwrapped_fields1145):
                    if (i1147 > 0):
                        self.newline()
                    self.pretty_formula(elem1146)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1153 = self._try_flat(msg, self.pretty_disjunction)
        if flat1153 is not None:
            assert flat1153 is not None
            self.write(flat1153)
            return None
        else:
            _dollar_dollar = msg
            fields1149 = _dollar_dollar.args
            assert fields1149 is not None
            unwrapped_fields1150 = fields1149
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1150) == 0:
                self.newline()
                for i1152, elem1151 in enumerate(unwrapped_fields1150):
                    if (i1152 > 0):
                        self.newline()
                    self.pretty_formula(elem1151)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1156 = self._try_flat(msg, self.pretty_not)
        if flat1156 is not None:
            assert flat1156 is not None
            self.write(flat1156)
            return None
        else:
            _dollar_dollar = msg
            fields1154 = _dollar_dollar.arg
            assert fields1154 is not None
            unwrapped_fields1155 = fields1154
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1155)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1162 = self._try_flat(msg, self.pretty_ffi)
        if flat1162 is not None:
            assert flat1162 is not None
            self.write(flat1162)
            return None
        else:
            _dollar_dollar = msg
            fields1157 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1157 is not None
            unwrapped_fields1158 = fields1157
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1159 = unwrapped_fields1158[0]
            self.pretty_name(field1159)
            self.newline()
            field1160 = unwrapped_fields1158[1]
            self.pretty_ffi_args(field1160)
            self.newline()
            field1161 = unwrapped_fields1158[2]
            self.pretty_terms(field1161)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1164 = self._try_flat(msg, self.pretty_name)
        if flat1164 is not None:
            assert flat1164 is not None
            self.write(flat1164)
            return None
        else:
            fields1163 = msg
            self.write(":")
            self.write(fields1163)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1168 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1168 is not None:
            assert flat1168 is not None
            self.write(flat1168)
            return None
        else:
            fields1165 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1165) == 0:
                self.newline()
                for i1167, elem1166 in enumerate(fields1165):
                    if (i1167 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1166)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1175 = self._try_flat(msg, self.pretty_atom)
        if flat1175 is not None:
            assert flat1175 is not None
            self.write(flat1175)
            return None
        else:
            _dollar_dollar = msg
            fields1169 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1169 is not None
            unwrapped_fields1170 = fields1169
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1171 = unwrapped_fields1170[0]
            self.pretty_relation_id(field1171)
            field1172 = unwrapped_fields1170[1]
            if not len(field1172) == 0:
                self.newline()
                for i1174, elem1173 in enumerate(field1172):
                    if (i1174 > 0):
                        self.newline()
                    self.pretty_term(elem1173)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1182 = self._try_flat(msg, self.pretty_pragma)
        if flat1182 is not None:
            assert flat1182 is not None
            self.write(flat1182)
            return None
        else:
            _dollar_dollar = msg
            fields1176 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1176 is not None
            unwrapped_fields1177 = fields1176
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1178 = unwrapped_fields1177[0]
            self.pretty_name(field1178)
            field1179 = unwrapped_fields1177[1]
            if not len(field1179) == 0:
                self.newline()
                for i1181, elem1180 in enumerate(field1179):
                    if (i1181 > 0):
                        self.newline()
                    self.pretty_term(elem1180)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1198 = self._try_flat(msg, self.pretty_primitive)
        if flat1198 is not None:
            assert flat1198 is not None
            self.write(flat1198)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1775 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1775 = None
            guard_result1197 = _t1775
            if guard_result1197 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1776 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1776 = None
                guard_result1196 = _t1776
                if guard_result1196 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1777 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1777 = None
                    guard_result1195 = _t1777
                    if guard_result1195 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1778 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1778 = None
                        guard_result1194 = _t1778
                        if guard_result1194 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1779 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1779 = None
                            guard_result1193 = _t1779
                            if guard_result1193 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1780 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1780 = None
                                guard_result1192 = _t1780
                                if guard_result1192 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1781 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1781 = None
                                    guard_result1191 = _t1781
                                    if guard_result1191 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1782 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1782 = None
                                        guard_result1190 = _t1782
                                        if guard_result1190 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1783 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1783 = None
                                            guard_result1189 = _t1783
                                            if guard_result1189 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1183 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1183 is not None
                                                unwrapped_fields1184 = fields1183
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1185 = unwrapped_fields1184[0]
                                                self.pretty_name(field1185)
                                                field1186 = unwrapped_fields1184[1]
                                                if not len(field1186) == 0:
                                                    self.newline()
                                                    for i1188, elem1187 in enumerate(field1186):
                                                        if (i1188 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1187)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1203 = self._try_flat(msg, self.pretty_eq)
        if flat1203 is not None:
            assert flat1203 is not None
            self.write(flat1203)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1784 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1784 = None
            fields1199 = _t1784
            assert fields1199 is not None
            unwrapped_fields1200 = fields1199
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1201 = unwrapped_fields1200[0]
            self.pretty_term(field1201)
            self.newline()
            field1202 = unwrapped_fields1200[1]
            self.pretty_term(field1202)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1208 = self._try_flat(msg, self.pretty_lt)
        if flat1208 is not None:
            assert flat1208 is not None
            self.write(flat1208)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1785 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1785 = None
            fields1204 = _t1785
            assert fields1204 is not None
            unwrapped_fields1205 = fields1204
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1206 = unwrapped_fields1205[0]
            self.pretty_term(field1206)
            self.newline()
            field1207 = unwrapped_fields1205[1]
            self.pretty_term(field1207)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1213 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1213 is not None:
            assert flat1213 is not None
            self.write(flat1213)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1786 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1786 = None
            fields1209 = _t1786
            assert fields1209 is not None
            unwrapped_fields1210 = fields1209
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1211 = unwrapped_fields1210[0]
            self.pretty_term(field1211)
            self.newline()
            field1212 = unwrapped_fields1210[1]
            self.pretty_term(field1212)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1218 = self._try_flat(msg, self.pretty_gt)
        if flat1218 is not None:
            assert flat1218 is not None
            self.write(flat1218)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1787 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1787 = None
            fields1214 = _t1787
            assert fields1214 is not None
            unwrapped_fields1215 = fields1214
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1216 = unwrapped_fields1215[0]
            self.pretty_term(field1216)
            self.newline()
            field1217 = unwrapped_fields1215[1]
            self.pretty_term(field1217)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1223 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1223 is not None:
            assert flat1223 is not None
            self.write(flat1223)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1788 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1788 = None
            fields1219 = _t1788
            assert fields1219 is not None
            unwrapped_fields1220 = fields1219
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1221 = unwrapped_fields1220[0]
            self.pretty_term(field1221)
            self.newline()
            field1222 = unwrapped_fields1220[1]
            self.pretty_term(field1222)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1229 = self._try_flat(msg, self.pretty_add)
        if flat1229 is not None:
            assert flat1229 is not None
            self.write(flat1229)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1789 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1789 = None
            fields1224 = _t1789
            assert fields1224 is not None
            unwrapped_fields1225 = fields1224
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1226 = unwrapped_fields1225[0]
            self.pretty_term(field1226)
            self.newline()
            field1227 = unwrapped_fields1225[1]
            self.pretty_term(field1227)
            self.newline()
            field1228 = unwrapped_fields1225[2]
            self.pretty_term(field1228)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1235 = self._try_flat(msg, self.pretty_minus)
        if flat1235 is not None:
            assert flat1235 is not None
            self.write(flat1235)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1790 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1790 = None
            fields1230 = _t1790
            assert fields1230 is not None
            unwrapped_fields1231 = fields1230
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1232 = unwrapped_fields1231[0]
            self.pretty_term(field1232)
            self.newline()
            field1233 = unwrapped_fields1231[1]
            self.pretty_term(field1233)
            self.newline()
            field1234 = unwrapped_fields1231[2]
            self.pretty_term(field1234)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1241 = self._try_flat(msg, self.pretty_multiply)
        if flat1241 is not None:
            assert flat1241 is not None
            self.write(flat1241)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1791 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1791 = None
            fields1236 = _t1791
            assert fields1236 is not None
            unwrapped_fields1237 = fields1236
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1238 = unwrapped_fields1237[0]
            self.pretty_term(field1238)
            self.newline()
            field1239 = unwrapped_fields1237[1]
            self.pretty_term(field1239)
            self.newline()
            field1240 = unwrapped_fields1237[2]
            self.pretty_term(field1240)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1247 = self._try_flat(msg, self.pretty_divide)
        if flat1247 is not None:
            assert flat1247 is not None
            self.write(flat1247)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1792 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1792 = None
            fields1242 = _t1792
            assert fields1242 is not None
            unwrapped_fields1243 = fields1242
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1244 = unwrapped_fields1243[0]
            self.pretty_term(field1244)
            self.newline()
            field1245 = unwrapped_fields1243[1]
            self.pretty_term(field1245)
            self.newline()
            field1246 = unwrapped_fields1243[2]
            self.pretty_term(field1246)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1252 = self._try_flat(msg, self.pretty_rel_term)
        if flat1252 is not None:
            assert flat1252 is not None
            self.write(flat1252)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1793 = _dollar_dollar.specialized_value
            else:
                _t1793 = None
            deconstruct_result1250 = _t1793
            if deconstruct_result1250 is not None:
                assert deconstruct_result1250 is not None
                unwrapped1251 = deconstruct_result1250
                self.pretty_specialized_value(unwrapped1251)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1794 = _dollar_dollar.term
                else:
                    _t1794 = None
                deconstruct_result1248 = _t1794
                if deconstruct_result1248 is not None:
                    assert deconstruct_result1248 is not None
                    unwrapped1249 = deconstruct_result1248
                    self.pretty_term(unwrapped1249)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1254 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1254 is not None:
            assert flat1254 is not None
            self.write(flat1254)
            return None
        else:
            fields1253 = msg
            self.write("#")
            self.pretty_raw_value(fields1253)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1261 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1261 is not None:
            assert flat1261 is not None
            self.write(flat1261)
            return None
        else:
            _dollar_dollar = msg
            fields1255 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1255 is not None
            unwrapped_fields1256 = fields1255
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1257 = unwrapped_fields1256[0]
            self.pretty_name(field1257)
            field1258 = unwrapped_fields1256[1]
            if not len(field1258) == 0:
                self.newline()
                for i1260, elem1259 in enumerate(field1258):
                    if (i1260 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1259)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1266 = self._try_flat(msg, self.pretty_cast)
        if flat1266 is not None:
            assert flat1266 is not None
            self.write(flat1266)
            return None
        else:
            _dollar_dollar = msg
            fields1262 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1262 is not None
            unwrapped_fields1263 = fields1262
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1264 = unwrapped_fields1263[0]
            self.pretty_term(field1264)
            self.newline()
            field1265 = unwrapped_fields1263[1]
            self.pretty_term(field1265)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1270 = self._try_flat(msg, self.pretty_attrs)
        if flat1270 is not None:
            assert flat1270 is not None
            self.write(flat1270)
            return None
        else:
            fields1267 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1267) == 0:
                self.newline()
                for i1269, elem1268 in enumerate(fields1267):
                    if (i1269 > 0):
                        self.newline()
                    self.pretty_attribute(elem1268)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1277 = self._try_flat(msg, self.pretty_attribute)
        if flat1277 is not None:
            assert flat1277 is not None
            self.write(flat1277)
            return None
        else:
            _dollar_dollar = msg
            fields1271 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1271 is not None
            unwrapped_fields1272 = fields1271
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1273 = unwrapped_fields1272[0]
            self.pretty_name(field1273)
            field1274 = unwrapped_fields1272[1]
            if not len(field1274) == 0:
                self.newline()
                for i1276, elem1275 in enumerate(field1274):
                    if (i1276 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1275)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1286 = self._try_flat(msg, self.pretty_algorithm)
        if flat1286 is not None:
            assert flat1286 is not None
            self.write(flat1286)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1795 = _dollar_dollar.attrs
            else:
                _t1795 = None
            fields1278 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body, _t1795,)
            assert fields1278 is not None
            unwrapped_fields1279 = fields1278
            self.write("(algorithm")
            self.indent_sexp()
            field1280 = unwrapped_fields1279[0]
            if not len(field1280) == 0:
                self.newline()
                for i1282, elem1281 in enumerate(field1280):
                    if (i1282 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1281)
            self.newline()
            field1283 = unwrapped_fields1279[1]
            self.pretty_script(field1283)
            field1284 = unwrapped_fields1279[2]
            if field1284 is not None:
                self.newline()
                assert field1284 is not None
                opt_val1285 = field1284
                self.pretty_attrs(opt_val1285)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1291 = self._try_flat(msg, self.pretty_script)
        if flat1291 is not None:
            assert flat1291 is not None
            self.write(flat1291)
            return None
        else:
            _dollar_dollar = msg
            fields1287 = _dollar_dollar.constructs
            assert fields1287 is not None
            unwrapped_fields1288 = fields1287
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1288) == 0:
                self.newline()
                for i1290, elem1289 in enumerate(unwrapped_fields1288):
                    if (i1290 > 0):
                        self.newline()
                    self.pretty_construct(elem1289)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1296 = self._try_flat(msg, self.pretty_construct)
        if flat1296 is not None:
            assert flat1296 is not None
            self.write(flat1296)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1796 = _dollar_dollar.loop
            else:
                _t1796 = None
            deconstruct_result1294 = _t1796
            if deconstruct_result1294 is not None:
                assert deconstruct_result1294 is not None
                unwrapped1295 = deconstruct_result1294
                self.pretty_loop(unwrapped1295)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1797 = _dollar_dollar.instruction
                else:
                    _t1797 = None
                deconstruct_result1292 = _t1797
                if deconstruct_result1292 is not None:
                    assert deconstruct_result1292 is not None
                    unwrapped1293 = deconstruct_result1292
                    self.pretty_instruction(unwrapped1293)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1303 = self._try_flat(msg, self.pretty_loop)
        if flat1303 is not None:
            assert flat1303 is not None
            self.write(flat1303)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1798 = _dollar_dollar.attrs
            else:
                _t1798 = None
            fields1297 = (_dollar_dollar.init, _dollar_dollar.body, _t1798,)
            assert fields1297 is not None
            unwrapped_fields1298 = fields1297
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1299 = unwrapped_fields1298[0]
            self.pretty_init(field1299)
            self.newline()
            field1300 = unwrapped_fields1298[1]
            self.pretty_script(field1300)
            field1301 = unwrapped_fields1298[2]
            if field1301 is not None:
                self.newline()
                assert field1301 is not None
                opt_val1302 = field1301
                self.pretty_attrs(opt_val1302)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1307 = self._try_flat(msg, self.pretty_init)
        if flat1307 is not None:
            assert flat1307 is not None
            self.write(flat1307)
            return None
        else:
            fields1304 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1304) == 0:
                self.newline()
                for i1306, elem1305 in enumerate(fields1304):
                    if (i1306 > 0):
                        self.newline()
                    self.pretty_instruction(elem1305)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1318 = self._try_flat(msg, self.pretty_instruction)
        if flat1318 is not None:
            assert flat1318 is not None
            self.write(flat1318)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1799 = _dollar_dollar.assign
            else:
                _t1799 = None
            deconstruct_result1316 = _t1799
            if deconstruct_result1316 is not None:
                assert deconstruct_result1316 is not None
                unwrapped1317 = deconstruct_result1316
                self.pretty_assign(unwrapped1317)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1800 = _dollar_dollar.upsert
                else:
                    _t1800 = None
                deconstruct_result1314 = _t1800
                if deconstruct_result1314 is not None:
                    assert deconstruct_result1314 is not None
                    unwrapped1315 = deconstruct_result1314
                    self.pretty_upsert(unwrapped1315)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1801 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1801 = None
                    deconstruct_result1312 = _t1801
                    if deconstruct_result1312 is not None:
                        assert deconstruct_result1312 is not None
                        unwrapped1313 = deconstruct_result1312
                        self.pretty_break(unwrapped1313)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1802 = _dollar_dollar.monoid_def
                        else:
                            _t1802 = None
                        deconstruct_result1310 = _t1802
                        if deconstruct_result1310 is not None:
                            assert deconstruct_result1310 is not None
                            unwrapped1311 = deconstruct_result1310
                            self.pretty_monoid_def(unwrapped1311)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1803 = _dollar_dollar.monus_def
                            else:
                                _t1803 = None
                            deconstruct_result1308 = _t1803
                            if deconstruct_result1308 is not None:
                                assert deconstruct_result1308 is not None
                                unwrapped1309 = deconstruct_result1308
                                self.pretty_monus_def(unwrapped1309)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1325 = self._try_flat(msg, self.pretty_assign)
        if flat1325 is not None:
            assert flat1325 is not None
            self.write(flat1325)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1804 = _dollar_dollar.attrs
            else:
                _t1804 = None
            fields1319 = (_dollar_dollar.name, _dollar_dollar.body, _t1804,)
            assert fields1319 is not None
            unwrapped_fields1320 = fields1319
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1321 = unwrapped_fields1320[0]
            self.pretty_relation_id(field1321)
            self.newline()
            field1322 = unwrapped_fields1320[1]
            self.pretty_abstraction(field1322)
            field1323 = unwrapped_fields1320[2]
            if field1323 is not None:
                self.newline()
                assert field1323 is not None
                opt_val1324 = field1323
                self.pretty_attrs(opt_val1324)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1332 = self._try_flat(msg, self.pretty_upsert)
        if flat1332 is not None:
            assert flat1332 is not None
            self.write(flat1332)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1805 = _dollar_dollar.attrs
            else:
                _t1805 = None
            fields1326 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1805,)
            assert fields1326 is not None
            unwrapped_fields1327 = fields1326
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1328 = unwrapped_fields1327[0]
            self.pretty_relation_id(field1328)
            self.newline()
            field1329 = unwrapped_fields1327[1]
            self.pretty_abstraction_with_arity(field1329)
            field1330 = unwrapped_fields1327[2]
            if field1330 is not None:
                self.newline()
                assert field1330 is not None
                opt_val1331 = field1330
                self.pretty_attrs(opt_val1331)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1337 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1337 is not None:
            assert flat1337 is not None
            self.write(flat1337)
            return None
        else:
            _dollar_dollar = msg
            _t1806 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1333 = (_t1806, _dollar_dollar[0].value,)
            assert fields1333 is not None
            unwrapped_fields1334 = fields1333
            self.write("(")
            self.indent()
            field1335 = unwrapped_fields1334[0]
            self.pretty_bindings(field1335)
            self.newline()
            field1336 = unwrapped_fields1334[1]
            self.pretty_formula(field1336)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1344 = self._try_flat(msg, self.pretty_break)
        if flat1344 is not None:
            assert flat1344 is not None
            self.write(flat1344)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1807 = _dollar_dollar.attrs
            else:
                _t1807 = None
            fields1338 = (_dollar_dollar.name, _dollar_dollar.body, _t1807,)
            assert fields1338 is not None
            unwrapped_fields1339 = fields1338
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1340 = unwrapped_fields1339[0]
            self.pretty_relation_id(field1340)
            self.newline()
            field1341 = unwrapped_fields1339[1]
            self.pretty_abstraction(field1341)
            field1342 = unwrapped_fields1339[2]
            if field1342 is not None:
                self.newline()
                assert field1342 is not None
                opt_val1343 = field1342
                self.pretty_attrs(opt_val1343)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1352 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1352 is not None:
            assert flat1352 is not None
            self.write(flat1352)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1808 = _dollar_dollar.attrs
            else:
                _t1808 = None
            fields1345 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1808,)
            assert fields1345 is not None
            unwrapped_fields1346 = fields1345
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1347 = unwrapped_fields1346[0]
            self.pretty_monoid(field1347)
            self.newline()
            field1348 = unwrapped_fields1346[1]
            self.pretty_relation_id(field1348)
            self.newline()
            field1349 = unwrapped_fields1346[2]
            self.pretty_abstraction_with_arity(field1349)
            field1350 = unwrapped_fields1346[3]
            if field1350 is not None:
                self.newline()
                assert field1350 is not None
                opt_val1351 = field1350
                self.pretty_attrs(opt_val1351)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1361 = self._try_flat(msg, self.pretty_monoid)
        if flat1361 is not None:
            assert flat1361 is not None
            self.write(flat1361)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1809 = _dollar_dollar.or_monoid
            else:
                _t1809 = None
            deconstruct_result1359 = _t1809
            if deconstruct_result1359 is not None:
                assert deconstruct_result1359 is not None
                unwrapped1360 = deconstruct_result1359
                self.pretty_or_monoid(unwrapped1360)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1810 = _dollar_dollar.min_monoid
                else:
                    _t1810 = None
                deconstruct_result1357 = _t1810
                if deconstruct_result1357 is not None:
                    assert deconstruct_result1357 is not None
                    unwrapped1358 = deconstruct_result1357
                    self.pretty_min_monoid(unwrapped1358)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1811 = _dollar_dollar.max_monoid
                    else:
                        _t1811 = None
                    deconstruct_result1355 = _t1811
                    if deconstruct_result1355 is not None:
                        assert deconstruct_result1355 is not None
                        unwrapped1356 = deconstruct_result1355
                        self.pretty_max_monoid(unwrapped1356)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1812 = _dollar_dollar.sum_monoid
                        else:
                            _t1812 = None
                        deconstruct_result1353 = _t1812
                        if deconstruct_result1353 is not None:
                            assert deconstruct_result1353 is not None
                            unwrapped1354 = deconstruct_result1353
                            self.pretty_sum_monoid(unwrapped1354)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1362 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1365 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1365 is not None:
            assert flat1365 is not None
            self.write(flat1365)
            return None
        else:
            _dollar_dollar = msg
            fields1363 = _dollar_dollar.type
            assert fields1363 is not None
            unwrapped_fields1364 = fields1363
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1364)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1368 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1368 is not None:
            assert flat1368 is not None
            self.write(flat1368)
            return None
        else:
            _dollar_dollar = msg
            fields1366 = _dollar_dollar.type
            assert fields1366 is not None
            unwrapped_fields1367 = fields1366
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1367)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1371 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1371 is not None:
            assert flat1371 is not None
            self.write(flat1371)
            return None
        else:
            _dollar_dollar = msg
            fields1369 = _dollar_dollar.type
            assert fields1369 is not None
            unwrapped_fields1370 = fields1369
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1370)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1379 = self._try_flat(msg, self.pretty_monus_def)
        if flat1379 is not None:
            assert flat1379 is not None
            self.write(flat1379)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1813 = _dollar_dollar.attrs
            else:
                _t1813 = None
            fields1372 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1813,)
            assert fields1372 is not None
            unwrapped_fields1373 = fields1372
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1374 = unwrapped_fields1373[0]
            self.pretty_monoid(field1374)
            self.newline()
            field1375 = unwrapped_fields1373[1]
            self.pretty_relation_id(field1375)
            self.newline()
            field1376 = unwrapped_fields1373[2]
            self.pretty_abstraction_with_arity(field1376)
            field1377 = unwrapped_fields1373[3]
            if field1377 is not None:
                self.newline()
                assert field1377 is not None
                opt_val1378 = field1377
                self.pretty_attrs(opt_val1378)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1386 = self._try_flat(msg, self.pretty_constraint)
        if flat1386 is not None:
            assert flat1386 is not None
            self.write(flat1386)
            return None
        else:
            _dollar_dollar = msg
            fields1380 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1380 is not None
            unwrapped_fields1381 = fields1380
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1382 = unwrapped_fields1381[0]
            self.pretty_relation_id(field1382)
            self.newline()
            field1383 = unwrapped_fields1381[1]
            self.pretty_abstraction(field1383)
            self.newline()
            field1384 = unwrapped_fields1381[2]
            self.pretty_functional_dependency_keys(field1384)
            self.newline()
            field1385 = unwrapped_fields1381[3]
            self.pretty_functional_dependency_values(field1385)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1390 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1390 is not None:
            assert flat1390 is not None
            self.write(flat1390)
            return None
        else:
            fields1387 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1387) == 0:
                self.newline()
                for i1389, elem1388 in enumerate(fields1387):
                    if (i1389 > 0):
                        self.newline()
                    self.pretty_var(elem1388)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1394 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1394 is not None:
            assert flat1394 is not None
            self.write(flat1394)
            return None
        else:
            fields1391 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1391) == 0:
                self.newline()
                for i1393, elem1392 in enumerate(fields1391):
                    if (i1393 > 0):
                        self.newline()
                    self.pretty_var(elem1392)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1403 = self._try_flat(msg, self.pretty_data)
        if flat1403 is not None:
            assert flat1403 is not None
            self.write(flat1403)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1814 = _dollar_dollar.edb
            else:
                _t1814 = None
            deconstruct_result1401 = _t1814
            if deconstruct_result1401 is not None:
                assert deconstruct_result1401 is not None
                unwrapped1402 = deconstruct_result1401
                self.pretty_edb(unwrapped1402)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1815 = _dollar_dollar.betree_relation
                else:
                    _t1815 = None
                deconstruct_result1399 = _t1815
                if deconstruct_result1399 is not None:
                    assert deconstruct_result1399 is not None
                    unwrapped1400 = deconstruct_result1399
                    self.pretty_betree_relation(unwrapped1400)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1816 = _dollar_dollar.csv_data
                    else:
                        _t1816 = None
                    deconstruct_result1397 = _t1816
                    if deconstruct_result1397 is not None:
                        assert deconstruct_result1397 is not None
                        unwrapped1398 = deconstruct_result1397
                        self.pretty_csv_data(unwrapped1398)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1817 = _dollar_dollar.iceberg_data
                        else:
                            _t1817 = None
                        deconstruct_result1395 = _t1817
                        if deconstruct_result1395 is not None:
                            assert deconstruct_result1395 is not None
                            unwrapped1396 = deconstruct_result1395
                            self.pretty_iceberg_data(unwrapped1396)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1409 = self._try_flat(msg, self.pretty_edb)
        if flat1409 is not None:
            assert flat1409 is not None
            self.write(flat1409)
            return None
        else:
            _dollar_dollar = msg
            fields1404 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1404 is not None
            unwrapped_fields1405 = fields1404
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1406 = unwrapped_fields1405[0]
            self.pretty_relation_id(field1406)
            self.newline()
            field1407 = unwrapped_fields1405[1]
            self.pretty_edb_path(field1407)
            self.newline()
            field1408 = unwrapped_fields1405[2]
            self.pretty_edb_types(field1408)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1413 = self._try_flat(msg, self.pretty_edb_path)
        if flat1413 is not None:
            assert flat1413 is not None
            self.write(flat1413)
            return None
        else:
            fields1410 = msg
            self.write("[")
            self.indent()
            for i1412, elem1411 in enumerate(fields1410):
                if (i1412 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1411))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1417 = self._try_flat(msg, self.pretty_edb_types)
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
                self.pretty_type(elem1415)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1422 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1422 is not None:
            assert flat1422 is not None
            self.write(flat1422)
            return None
        else:
            _dollar_dollar = msg
            fields1418 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1418 is not None
            unwrapped_fields1419 = fields1418
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1420 = unwrapped_fields1419[0]
            self.pretty_relation_id(field1420)
            self.newline()
            field1421 = unwrapped_fields1419[1]
            self.pretty_betree_info(field1421)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1428 = self._try_flat(msg, self.pretty_betree_info)
        if flat1428 is not None:
            assert flat1428 is not None
            self.write(flat1428)
            return None
        else:
            _dollar_dollar = msg
            _t1818 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1423 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1818,)
            assert fields1423 is not None
            unwrapped_fields1424 = fields1423
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1425 = unwrapped_fields1424[0]
            self.pretty_betree_info_key_types(field1425)
            self.newline()
            field1426 = unwrapped_fields1424[1]
            self.pretty_betree_info_value_types(field1426)
            self.newline()
            field1427 = unwrapped_fields1424[2]
            self.pretty_config_dict(field1427)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1432 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1432 is not None:
            assert flat1432 is not None
            self.write(flat1432)
            return None
        else:
            fields1429 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1429) == 0:
                self.newline()
                for i1431, elem1430 in enumerate(fields1429):
                    if (i1431 > 0):
                        self.newline()
                    self.pretty_type(elem1430)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1436 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1436 is not None:
            assert flat1436 is not None
            self.write(flat1436)
            return None
        else:
            fields1433 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1433) == 0:
                self.newline()
                for i1435, elem1434 in enumerate(fields1433):
                    if (i1435 > 0):
                        self.newline()
                    self.pretty_type(elem1434)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1446 = self._try_flat(msg, self.pretty_csv_data)
        if flat1446 is not None:
            assert flat1446 is not None
            self.write(flat1446)
            return None
        else:
            _dollar_dollar = msg
            _t1819 = self.deconstruct_csv_data_columns_optional(_dollar_dollar)
            _t1820 = self.deconstruct_csv_data_relations_optional(_dollar_dollar)
            fields1437 = (_dollar_dollar.locator, _dollar_dollar.config, _t1819, _t1820, _dollar_dollar.asof,)
            assert fields1437 is not None
            unwrapped_fields1438 = fields1437
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1439 = unwrapped_fields1438[0]
            self.pretty_csvlocator(field1439)
            self.newline()
            field1440 = unwrapped_fields1438[1]
            self.pretty_csv_config(field1440)
            field1441 = unwrapped_fields1438[2]
            if field1441 is not None:
                self.newline()
                assert field1441 is not None
                opt_val1442 = field1441
                self.pretty_gnf_columns(opt_val1442)
            field1443 = unwrapped_fields1438[3]
            if field1443 is not None:
                self.newline()
                assert field1443 is not None
                opt_val1444 = field1443
                self.pretty_target_relations(opt_val1444)
            self.newline()
            field1445 = unwrapped_fields1438[4]
            self.pretty_csv_asof(field1445)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1453 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1453 is not None:
            assert flat1453 is not None
            self.write(flat1453)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1821 = _dollar_dollar.paths
            else:
                _t1821 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1822 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1822 = None
            fields1447 = (_t1821, _t1822,)
            assert fields1447 is not None
            unwrapped_fields1448 = fields1447
            self.write("(csv_locator")
            self.indent_sexp()
            field1449 = unwrapped_fields1448[0]
            if field1449 is not None:
                self.newline()
                assert field1449 is not None
                opt_val1450 = field1449
                self.pretty_csv_locator_paths(opt_val1450)
            field1451 = unwrapped_fields1448[1]
            if field1451 is not None:
                self.newline()
                assert field1451 is not None
                opt_val1452 = field1451
                self.pretty_csv_locator_inline_data(opt_val1452)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1457 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1457 is not None:
            assert flat1457 is not None
            self.write(flat1457)
            return None
        else:
            fields1454 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1454) == 0:
                self.newline()
                for i1456, elem1455 in enumerate(fields1454):
                    if (i1456 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1455))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1459 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1459 is not None:
            assert flat1459 is not None
            self.write(flat1459)
            return None
        else:
            fields1458 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1458))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1465 = self._try_flat(msg, self.pretty_csv_config)
        if flat1465 is not None:
            assert flat1465 is not None
            self.write(flat1465)
            return None
        else:
            _dollar_dollar = msg
            _t1823 = self.deconstruct_csv_config(_dollar_dollar)
            _t1824 = self.deconstruct_csv_storage_integration_optional(_dollar_dollar)
            fields1460 = (_t1823, _t1824,)
            assert fields1460 is not None
            unwrapped_fields1461 = fields1460
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            field1462 = unwrapped_fields1461[0]
            self.pretty_config_dict(field1462)
            field1463 = unwrapped_fields1461[1]
            if field1463 is not None:
                self.newline()
                assert field1463 is not None
                opt_val1464 = field1463
                self.pretty__storage_integration(opt_val1464)
            self.dedent()
            self.write(")")

    def pretty__storage_integration(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat1467 = self._try_flat(msg, self.pretty__storage_integration)
        if flat1467 is not None:
            assert flat1467 is not None
            self.write(flat1467)
            return None
        else:
            fields1466 = msg
            self.write("(storage_integration")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(fields1466)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1471 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1471 is not None:
            assert flat1471 is not None
            self.write(flat1471)
            return None
        else:
            fields1468 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1468) == 0:
                self.newline()
                for i1470, elem1469 in enumerate(fields1468):
                    if (i1470 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1469)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1480 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1480 is not None:
            assert flat1480 is not None
            self.write(flat1480)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1825 = _dollar_dollar.target_id
            else:
                _t1825 = None
            fields1472 = (_dollar_dollar.column_path, _t1825, _dollar_dollar.types,)
            assert fields1472 is not None
            unwrapped_fields1473 = fields1472
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1474 = unwrapped_fields1473[0]
            self.pretty_gnf_column_path(field1474)
            field1475 = unwrapped_fields1473[1]
            if field1475 is not None:
                self.newline()
                assert field1475 is not None
                opt_val1476 = field1475
                self.pretty_relation_id(opt_val1476)
            self.newline()
            self.write("[")
            field1477 = unwrapped_fields1473[2]
            for i1479, elem1478 in enumerate(field1477):
                if (i1479 > 0):
                    self.newline()
                self.pretty_type(elem1478)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1487 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1487 is not None:
            assert flat1487 is not None
            self.write(flat1487)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1826 = _dollar_dollar[0]
            else:
                _t1826 = None
            deconstruct_result1485 = _t1826
            if deconstruct_result1485 is not None:
                assert deconstruct_result1485 is not None
                unwrapped1486 = deconstruct_result1485
                self.write(self.format_string_value(unwrapped1486))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1827 = _dollar_dollar
                else:
                    _t1827 = None
                deconstruct_result1481 = _t1827
                if deconstruct_result1481 is not None:
                    assert deconstruct_result1481 is not None
                    unwrapped1482 = deconstruct_result1481
                    self.write("[")
                    self.indent()
                    for i1484, elem1483 in enumerate(unwrapped1482):
                        if (i1484 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1483))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_target_relations(self, msg: logic_pb2.TargetRelations):
        flat1492 = self._try_flat(msg, self.pretty_target_relations)
        if flat1492 is not None:
            assert flat1492 is not None
            self.write(flat1492)
            return None
        else:
            _dollar_dollar = msg
            _t1828 = self.deconstruct_relation_keys(_dollar_dollar)
            fields1488 = (_t1828, _dollar_dollar,)
            assert fields1488 is not None
            unwrapped_fields1489 = fields1488
            self.write("(relations")
            self.indent_sexp()
            self.newline()
            field1490 = unwrapped_fields1489[0]
            self.pretty_relation_keys(field1490)
            self.newline()
            field1491 = unwrapped_fields1489[1]
            self.pretty_relation_body(field1491)
            self.dedent()
            self.write(")")

    def pretty_relation_keys(self, msg: tuple[Sequence[logic_pb2.NamedColumn], bool]):
        flat1499 = self._try_flat(msg, self.pretty_relation_keys)
        if flat1499 is not None:
            assert flat1499 is not None
            self.write(flat1499)
            return None
        else:
            _dollar_dollar = msg
            if not _dollar_dollar[1]:
                _t1829 = _dollar_dollar[0]
            else:
                _t1829 = None
            deconstruct_result1495 = _t1829
            if deconstruct_result1495 is not None:
                assert deconstruct_result1495 is not None
                unwrapped1496 = deconstruct_result1495
                self.write("(keys")
                self.indent_sexp()
                if not len(unwrapped1496) == 0:
                    self.newline()
                    for i1498, elem1497 in enumerate(unwrapped1496):
                        if (i1498 > 0):
                            self.newline()
                        self.pretty_named_column(elem1497)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar[1]:
                    _t1830 = ()
                else:
                    _t1830 = None
                deconstruct_result1493 = _t1830
                if deconstruct_result1493 is not None:
                    assert deconstruct_result1493 is not None
                    unwrapped1494 = deconstruct_result1493
                    self.write("(keys")
                    self.newline()
                    self.write("synthetic)")
                else:
                    raise ParseError("No matching rule for relation_keys")

    def pretty_named_column(self, msg: logic_pb2.NamedColumn):
        flat1504 = self._try_flat(msg, self.pretty_named_column)
        if flat1504 is not None:
            assert flat1504 is not None
            self.write(flat1504)
            return None
        else:
            _dollar_dollar = msg
            fields1500 = (_dollar_dollar.name, _dollar_dollar.type,)
            assert fields1500 is not None
            unwrapped_fields1501 = fields1500
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1502 = unwrapped_fields1501[0]
            self.write(self.format_string_value(field1502))
            self.newline()
            field1503 = unwrapped_fields1501[1]
            self.pretty_type(field1503)
            self.dedent()
            self.write(")")

    def pretty_relation_body(self, msg: logic_pb2.TargetRelations):
        flat1511 = self._try_flat(msg, self.pretty_relation_body)
        if flat1511 is not None:
            assert flat1511 is not None
            self.write(flat1511)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("plain"):
                _t1831 = _dollar_dollar.plain.targets
            else:
                _t1831 = None
            deconstruct_result1509 = _t1831
            if deconstruct_result1509 is not None:
                assert deconstruct_result1509 is not None
                unwrapped1510 = deconstruct_result1509
                self.pretty_non_cdc_relations(unwrapped1510)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("cdc"):
                    _t1832 = (_dollar_dollar.cdc.inserts, _dollar_dollar.cdc.deletes,)
                else:
                    _t1832 = None
                deconstruct_result1505 = _t1832
                if deconstruct_result1505 is not None:
                    assert deconstruct_result1505 is not None
                    unwrapped1506 = deconstruct_result1505
                    field1507 = unwrapped1506[0]
                    self.pretty_cdc_inserts(field1507)
                    self.write(" ")
                    field1508 = unwrapped1506[1]
                    self.pretty_cdc_deletes(field1508)
                else:
                    raise ParseError("No matching rule for relation_body")

    def pretty_non_cdc_relations(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1515 = self._try_flat(msg, self.pretty_non_cdc_relations)
        if flat1515 is not None:
            assert flat1515 is not None
            self.write(flat1515)
            return None
        else:
            fields1512 = msg
            for i1514, elem1513 in enumerate(fields1512):
                if (i1514 > 0):
                    self.newline()
                self.pretty_target_relation(elem1513)

    def pretty_target_relation(self, msg: logic_pb2.TargetRelation):
        flat1522 = self._try_flat(msg, self.pretty_target_relation)
        if flat1522 is not None:
            assert flat1522 is not None
            self.write(flat1522)
            return None
        else:
            _dollar_dollar = msg
            fields1516 = (_dollar_dollar.target_id, _dollar_dollar.values,)
            assert fields1516 is not None
            unwrapped_fields1517 = fields1516
            self.write("(relation")
            self.indent_sexp()
            self.newline()
            field1518 = unwrapped_fields1517[0]
            self.pretty_relation_id(field1518)
            field1519 = unwrapped_fields1517[1]
            if not len(field1519) == 0:
                self.newline()
                for i1521, elem1520 in enumerate(field1519):
                    if (i1521 > 0):
                        self.newline()
                    self.pretty_named_column(elem1520)
            self.dedent()
            self.write(")")

    def pretty_cdc_inserts(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1526 = self._try_flat(msg, self.pretty_cdc_inserts)
        if flat1526 is not None:
            assert flat1526 is not None
            self.write(flat1526)
            return None
        else:
            fields1523 = msg
            self.write("(inserts")
            self.indent_sexp()
            if not len(fields1523) == 0:
                self.newline()
                for i1525, elem1524 in enumerate(fields1523):
                    if (i1525 > 0):
                        self.newline()
                    self.pretty_target_relation(elem1524)
            self.dedent()
            self.write(")")

    def pretty_cdc_deletes(self, msg: Sequence[logic_pb2.TargetRelation]):
        flat1530 = self._try_flat(msg, self.pretty_cdc_deletes)
        if flat1530 is not None:
            assert flat1530 is not None
            self.write(flat1530)
            return None
        else:
            fields1527 = msg
            self.write("(deletes")
            self.indent_sexp()
            if not len(fields1527) == 0:
                self.newline()
                for i1529, elem1528 in enumerate(fields1527):
                    if (i1529 > 0):
                        self.newline()
                    self.pretty_target_relation(elem1528)
            self.dedent()
            self.write(")")

    def pretty_csv_asof(self, msg: str):
        flat1532 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1532 is not None:
            assert flat1532 is not None
            self.write(flat1532)
            return None
        else:
            fields1531 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1531))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1543 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1543 is not None:
            assert flat1543 is not None
            self.write(flat1543)
            return None
        else:
            _dollar_dollar = msg
            _t1833 = self.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
            _t1834 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1533 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1833, _t1834, _dollar_dollar.returns_delta,)
            assert fields1533 is not None
            unwrapped_fields1534 = fields1533
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1535 = unwrapped_fields1534[0]
            self.pretty_iceberg_locator(field1535)
            self.newline()
            field1536 = unwrapped_fields1534[1]
            self.pretty_iceberg_catalog_config(field1536)
            self.newline()
            field1537 = unwrapped_fields1534[2]
            self.pretty_gnf_columns(field1537)
            field1538 = unwrapped_fields1534[3]
            if field1538 is not None:
                self.newline()
                assert field1538 is not None
                opt_val1539 = field1538
                self.pretty_iceberg_from_snapshot(opt_val1539)
            field1540 = unwrapped_fields1534[4]
            if field1540 is not None:
                self.newline()
                assert field1540 is not None
                opt_val1541 = field1540
                self.pretty_iceberg_to_snapshot(opt_val1541)
            self.newline()
            field1542 = unwrapped_fields1534[5]
            self.pretty_boolean_value(field1542)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1549 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1549 is not None:
            assert flat1549 is not None
            self.write(flat1549)
            return None
        else:
            _dollar_dollar = msg
            fields1544 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1544 is not None
            unwrapped_fields1545 = fields1544
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            field1546 = unwrapped_fields1545[0]
            self.pretty_iceberg_locator_table_name(field1546)
            self.newline()
            field1547 = unwrapped_fields1545[1]
            self.pretty_iceberg_locator_namespace(field1547)
            self.newline()
            field1548 = unwrapped_fields1545[2]
            self.pretty_iceberg_locator_warehouse(field1548)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_table_name(self, msg: str):
        flat1551 = self._try_flat(msg, self.pretty_iceberg_locator_table_name)
        if flat1551 is not None:
            assert flat1551 is not None
            self.write(flat1551)
            return None
        else:
            fields1550 = msg
            self.write("(table_name")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1550))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_namespace(self, msg: Sequence[str]):
        flat1555 = self._try_flat(msg, self.pretty_iceberg_locator_namespace)
        if flat1555 is not None:
            assert flat1555 is not None
            self.write(flat1555)
            return None
        else:
            fields1552 = msg
            self.write("(namespace")
            self.indent_sexp()
            if not len(fields1552) == 0:
                self.newline()
                for i1554, elem1553 in enumerate(fields1552):
                    if (i1554 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1553))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_warehouse(self, msg: str):
        flat1557 = self._try_flat(msg, self.pretty_iceberg_locator_warehouse)
        if flat1557 is not None:
            assert flat1557 is not None
            self.write(flat1557)
            return None
        else:
            fields1556 = msg
            self.write("(warehouse")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1556))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1565 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1565 is not None:
            assert flat1565 is not None
            self.write(flat1565)
            return None
        else:
            _dollar_dollar = msg
            _t1835 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1558 = (_dollar_dollar.catalog_uri, _t1835, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1558 is not None
            unwrapped_fields1559 = fields1558
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            field1560 = unwrapped_fields1559[0]
            self.pretty_iceberg_catalog_uri(field1560)
            field1561 = unwrapped_fields1559[1]
            if field1561 is not None:
                self.newline()
                assert field1561 is not None
                opt_val1562 = field1561
                self.pretty_iceberg_catalog_config_scope(opt_val1562)
            self.newline()
            field1563 = unwrapped_fields1559[2]
            self.pretty_iceberg_properties(field1563)
            self.newline()
            field1564 = unwrapped_fields1559[3]
            self.pretty_iceberg_auth_properties(field1564)
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_uri(self, msg: str):
        flat1567 = self._try_flat(msg, self.pretty_iceberg_catalog_uri)
        if flat1567 is not None:
            assert flat1567 is not None
            self.write(flat1567)
            return None
        else:
            fields1566 = msg
            self.write("(catalog_uri")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1566))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1569 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1569 is not None:
            assert flat1569 is not None
            self.write(flat1569)
            return None
        else:
            fields1568 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1568))
            self.dedent()
            self.write(")")

    def pretty_iceberg_properties(self, msg: Sequence[tuple[str, str]]):
        flat1573 = self._try_flat(msg, self.pretty_iceberg_properties)
        if flat1573 is not None:
            assert flat1573 is not None
            self.write(flat1573)
            return None
        else:
            fields1570 = msg
            self.write("(properties")
            self.indent_sexp()
            if not len(fields1570) == 0:
                self.newline()
                for i1572, elem1571 in enumerate(fields1570):
                    if (i1572 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1571)
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1578 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1578 is not None:
            assert flat1578 is not None
            self.write(flat1578)
            return None
        else:
            _dollar_dollar = msg
            fields1574 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1574 is not None
            unwrapped_fields1575 = fields1574
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1576 = unwrapped_fields1575[0]
            self.write(self.format_string_value(field1576))
            self.newline()
            field1577 = unwrapped_fields1575[1]
            self.write(self.format_string_value(field1577))
            self.dedent()
            self.write(")")

    def pretty_iceberg_auth_properties(self, msg: Sequence[tuple[str, str]]):
        flat1582 = self._try_flat(msg, self.pretty_iceberg_auth_properties)
        if flat1582 is not None:
            assert flat1582 is not None
            self.write(flat1582)
            return None
        else:
            fields1579 = msg
            self.write("(auth_properties")
            self.indent_sexp()
            if not len(fields1579) == 0:
                self.newline()
                for i1581, elem1580 in enumerate(fields1579):
                    if (i1581 > 0):
                        self.newline()
                    self.pretty_iceberg_masked_property_entry(elem1580)
            self.dedent()
            self.write(")")

    def pretty_iceberg_masked_property_entry(self, msg: tuple[str, str]):
        flat1587 = self._try_flat(msg, self.pretty_iceberg_masked_property_entry)
        if flat1587 is not None:
            assert flat1587 is not None
            self.write(flat1587)
            return None
        else:
            _dollar_dollar = msg
            _t1836 = self.mask_secret_value(_dollar_dollar)
            fields1583 = (_dollar_dollar[0], _t1836,)
            assert fields1583 is not None
            unwrapped_fields1584 = fields1583
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1585 = unwrapped_fields1584[0]
            self.write(self.format_string_value(field1585))
            self.newline()
            field1586 = unwrapped_fields1584[1]
            self.write(self.format_string_value(field1586))
            self.dedent()
            self.write(")")

    def pretty_iceberg_from_snapshot(self, msg: str):
        flat1589 = self._try_flat(msg, self.pretty_iceberg_from_snapshot)
        if flat1589 is not None:
            assert flat1589 is not None
            self.write(flat1589)
            return None
        else:
            fields1588 = msg
            self.write("(from_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1588))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1591 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1591 is not None:
            assert flat1591 is not None
            self.write(flat1591)
            return None
        else:
            fields1590 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1590))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1594 = self._try_flat(msg, self.pretty_undefine)
        if flat1594 is not None:
            assert flat1594 is not None
            self.write(flat1594)
            return None
        else:
            _dollar_dollar = msg
            fields1592 = _dollar_dollar.fragment_id
            assert fields1592 is not None
            unwrapped_fields1593 = fields1592
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1593)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1599 = self._try_flat(msg, self.pretty_context)
        if flat1599 is not None:
            assert flat1599 is not None
            self.write(flat1599)
            return None
        else:
            _dollar_dollar = msg
            fields1595 = _dollar_dollar.relations
            assert fields1595 is not None
            unwrapped_fields1596 = fields1595
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1596) == 0:
                self.newline()
                for i1598, elem1597 in enumerate(unwrapped_fields1596):
                    if (i1598 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1597)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1606 = self._try_flat(msg, self.pretty_snapshot)
        if flat1606 is not None:
            assert flat1606 is not None
            self.write(flat1606)
            return None
        else:
            _dollar_dollar = msg
            fields1600 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
            assert fields1600 is not None
            unwrapped_fields1601 = fields1600
            self.write("(snapshot")
            self.indent_sexp()
            self.newline()
            field1602 = unwrapped_fields1601[0]
            self.pretty_edb_path(field1602)
            field1603 = unwrapped_fields1601[1]
            if not len(field1603) == 0:
                self.newline()
                for i1605, elem1604 in enumerate(field1603):
                    if (i1605 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1604)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1611 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1611 is not None:
            assert flat1611 is not None
            self.write(flat1611)
            return None
        else:
            _dollar_dollar = msg
            fields1607 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1607 is not None
            unwrapped_fields1608 = fields1607
            field1609 = unwrapped_fields1608[0]
            self.pretty_edb_path(field1609)
            self.write(" ")
            field1610 = unwrapped_fields1608[1]
            self.pretty_relation_id(field1610)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1615 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1615 is not None:
            assert flat1615 is not None
            self.write(flat1615)
            return None
        else:
            fields1612 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1612) == 0:
                self.newline()
                for i1614, elem1613 in enumerate(fields1612):
                    if (i1614 > 0):
                        self.newline()
                    self.pretty_read(elem1613)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1626 = self._try_flat(msg, self.pretty_read)
        if flat1626 is not None:
            assert flat1626 is not None
            self.write(flat1626)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1837 = _dollar_dollar.demand
            else:
                _t1837 = None
            deconstruct_result1624 = _t1837
            if deconstruct_result1624 is not None:
                assert deconstruct_result1624 is not None
                unwrapped1625 = deconstruct_result1624
                self.pretty_demand(unwrapped1625)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1838 = _dollar_dollar.output
                else:
                    _t1838 = None
                deconstruct_result1622 = _t1838
                if deconstruct_result1622 is not None:
                    assert deconstruct_result1622 is not None
                    unwrapped1623 = deconstruct_result1622
                    self.pretty_output(unwrapped1623)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1839 = _dollar_dollar.what_if
                    else:
                        _t1839 = None
                    deconstruct_result1620 = _t1839
                    if deconstruct_result1620 is not None:
                        assert deconstruct_result1620 is not None
                        unwrapped1621 = deconstruct_result1620
                        self.pretty_what_if(unwrapped1621)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1840 = _dollar_dollar.abort
                        else:
                            _t1840 = None
                        deconstruct_result1618 = _t1840
                        if deconstruct_result1618 is not None:
                            assert deconstruct_result1618 is not None
                            unwrapped1619 = deconstruct_result1618
                            self.pretty_abort(unwrapped1619)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1841 = _dollar_dollar.export
                            else:
                                _t1841 = None
                            deconstruct_result1616 = _t1841
                            if deconstruct_result1616 is not None:
                                assert deconstruct_result1616 is not None
                                unwrapped1617 = deconstruct_result1616
                                self.pretty_export(unwrapped1617)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1629 = self._try_flat(msg, self.pretty_demand)
        if flat1629 is not None:
            assert flat1629 is not None
            self.write(flat1629)
            return None
        else:
            _dollar_dollar = msg
            fields1627 = _dollar_dollar.relation_id
            assert fields1627 is not None
            unwrapped_fields1628 = fields1627
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1628)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1634 = self._try_flat(msg, self.pretty_output)
        if flat1634 is not None:
            assert flat1634 is not None
            self.write(flat1634)
            return None
        else:
            _dollar_dollar = msg
            fields1630 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1630 is not None
            unwrapped_fields1631 = fields1630
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1632 = unwrapped_fields1631[0]
            self.pretty_name(field1632)
            self.newline()
            field1633 = unwrapped_fields1631[1]
            self.pretty_relation_id(field1633)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1639 = self._try_flat(msg, self.pretty_what_if)
        if flat1639 is not None:
            assert flat1639 is not None
            self.write(flat1639)
            return None
        else:
            _dollar_dollar = msg
            fields1635 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1635 is not None
            unwrapped_fields1636 = fields1635
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1637 = unwrapped_fields1636[0]
            self.pretty_name(field1637)
            self.newline()
            field1638 = unwrapped_fields1636[1]
            self.pretty_epoch(field1638)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1645 = self._try_flat(msg, self.pretty_abort)
        if flat1645 is not None:
            assert flat1645 is not None
            self.write(flat1645)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1842 = _dollar_dollar.name
            else:
                _t1842 = None
            fields1640 = (_t1842, _dollar_dollar.relation_id,)
            assert fields1640 is not None
            unwrapped_fields1641 = fields1640
            self.write("(abort")
            self.indent_sexp()
            field1642 = unwrapped_fields1641[0]
            if field1642 is not None:
                self.newline()
                assert field1642 is not None
                opt_val1643 = field1642
                self.pretty_name(opt_val1643)
            self.newline()
            field1644 = unwrapped_fields1641[1]
            self.pretty_relation_id(field1644)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1650 = self._try_flat(msg, self.pretty_export)
        if flat1650 is not None:
            assert flat1650 is not None
            self.write(flat1650)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1843 = _dollar_dollar.csv_config
            else:
                _t1843 = None
            deconstruct_result1648 = _t1843
            if deconstruct_result1648 is not None:
                assert deconstruct_result1648 is not None
                unwrapped1649 = deconstruct_result1648
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1649)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1844 = _dollar_dollar.iceberg_config
                else:
                    _t1844 = None
                deconstruct_result1646 = _t1844
                if deconstruct_result1646 is not None:
                    assert deconstruct_result1646 is not None
                    unwrapped1647 = deconstruct_result1646
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1647)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1661 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1661 is not None:
            assert flat1661 is not None
            self.write(flat1661)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1846 = self.deconstruct_export_csv_output_location(_dollar_dollar)
                _t1845 = (_t1846, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1845 = None
            deconstruct_result1656 = _t1845
            if deconstruct_result1656 is not None:
                assert deconstruct_result1656 is not None
                unwrapped1657 = deconstruct_result1656
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1658 = unwrapped1657[0]
                self.pretty_export_csv_output_location(field1658)
                self.newline()
                field1659 = unwrapped1657[1]
                self.pretty_export_csv_source(field1659)
                self.newline()
                field1660 = unwrapped1657[2]
                self.pretty_csv_config(field1660)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1848 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1847 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1848,)
                else:
                    _t1847 = None
                deconstruct_result1651 = _t1847
                if deconstruct_result1651 is not None:
                    assert deconstruct_result1651 is not None
                    unwrapped1652 = deconstruct_result1651
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1653 = unwrapped1652[0]
                    self.pretty_export_csv_path(field1653)
                    self.newline()
                    field1654 = unwrapped1652[1]
                    self.pretty_export_csv_columns_list(field1654)
                    self.newline()
                    field1655 = unwrapped1652[2]
                    self.pretty_config_dict(field1655)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_output_location(self, msg: tuple[str, str]):
        flat1666 = self._try_flat(msg, self.pretty_export_csv_output_location)
        if flat1666 is not None:
            assert flat1666 is not None
            self.write(flat1666)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar[0] != "":
                _t1849 = _dollar_dollar[0]
            else:
                _t1849 = None
            deconstruct_result1664 = _t1849
            if deconstruct_result1664 is not None:
                assert deconstruct_result1664 is not None
                unwrapped1665 = deconstruct_result1664
                self.write("(path")
                self.indent_sexp()
                self.newline()
                self.write(self.format_string_value(unwrapped1665))
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar[1] != "":
                    _t1850 = _dollar_dollar[1]
                else:
                    _t1850 = None
                deconstruct_result1662 = _t1850
                if deconstruct_result1662 is not None:
                    assert deconstruct_result1662 is not None
                    unwrapped1663 = deconstruct_result1662
                    self.write("(transaction_output_name")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_name(unwrapped1663)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_output_location")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1673 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1673 is not None:
            assert flat1673 is not None
            self.write(flat1673)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1851 = _dollar_dollar.gnf_columns.columns
            else:
                _t1851 = None
            deconstruct_result1669 = _t1851
            if deconstruct_result1669 is not None:
                assert deconstruct_result1669 is not None
                unwrapped1670 = deconstruct_result1669
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1670) == 0:
                    self.newline()
                    for i1672, elem1671 in enumerate(unwrapped1670):
                        if (i1672 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1671)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1852 = _dollar_dollar.table_def
                else:
                    _t1852 = None
                deconstruct_result1667 = _t1852
                if deconstruct_result1667 is not None:
                    assert deconstruct_result1667 is not None
                    unwrapped1668 = deconstruct_result1667
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1668)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1678 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1678 is not None:
            assert flat1678 is not None
            self.write(flat1678)
            return None
        else:
            _dollar_dollar = msg
            fields1674 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1674 is not None
            unwrapped_fields1675 = fields1674
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1676 = unwrapped_fields1675[0]
            self.write(self.format_string_value(field1676))
            self.newline()
            field1677 = unwrapped_fields1675[1]
            self.pretty_relation_id(field1677)
            self.dedent()
            self.write(")")

    def pretty_export_csv_path(self, msg: str):
        flat1680 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1680 is not None:
            assert flat1680 is not None
            self.write(flat1680)
            return None
        else:
            fields1679 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1679))
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1684 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1684 is not None:
            assert flat1684 is not None
            self.write(flat1684)
            return None
        else:
            fields1681 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1681) == 0:
                self.newline()
                for i1683, elem1682 in enumerate(fields1681):
                    if (i1683 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1682)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1693 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1693 is not None:
            assert flat1693 is not None
            self.write(flat1693)
            return None
        else:
            _dollar_dollar = msg
            _t1853 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1685 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sorted(_dollar_dollar.table_properties.items()), _t1853,)
            assert fields1685 is not None
            unwrapped_fields1686 = fields1685
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1687 = unwrapped_fields1686[0]
            self.pretty_iceberg_locator(field1687)
            self.newline()
            field1688 = unwrapped_fields1686[1]
            self.pretty_iceberg_catalog_config(field1688)
            self.newline()
            field1689 = unwrapped_fields1686[2]
            self.pretty_export_iceberg_table_def(field1689)
            self.newline()
            field1690 = unwrapped_fields1686[3]
            self.pretty_iceberg_table_properties(field1690)
            field1691 = unwrapped_fields1686[4]
            if field1691 is not None:
                self.newline()
                assert field1691 is not None
                opt_val1692 = field1691
                self.pretty_config_dict(opt_val1692)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_table_def(self, msg: logic_pb2.RelationId):
        flat1695 = self._try_flat(msg, self.pretty_export_iceberg_table_def)
        if flat1695 is not None:
            assert flat1695 is not None
            self.write(flat1695)
            return None
        else:
            fields1694 = msg
            self.write("(table_def")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1694)
            self.dedent()
            self.write(")")

    def pretty_iceberg_table_properties(self, msg: Sequence[tuple[str, str]]):
        flat1699 = self._try_flat(msg, self.pretty_iceberg_table_properties)
        if flat1699 is not None:
            assert flat1699 is not None
            self.write(flat1699)
            return None
        else:
            fields1696 = msg
            self.write("(table_properties")
            self.indent_sexp()
            if not len(fields1696) == 0:
                self.newline()
                for i1698, elem1697 in enumerate(fields1696):
                    if (i1698 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1697)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1907 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1907)
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
