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
        _t1742 = logic_pb2.Value(int32_value=v)
        return _t1742

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1743 = logic_pb2.Value(int_value=v)
        return _t1743

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1744 = logic_pb2.Value(float_value=v)
        return _t1744

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1745 = logic_pb2.Value(string_value=v)
        return _t1745

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1746 = logic_pb2.Value(boolean_value=v)
        return _t1746

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1747 = logic_pb2.Value(uint128_value=v)
        return _t1747

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1748 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1748,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1749 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1749,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1750 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1750,))
        _t1751 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1751,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1752 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1752,))
        _t1753 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1753,))
        if msg.new_line != "":
            _t1754 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1754,))
        _t1755 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1755,))
        _t1756 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1756,))
        _t1757 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1757,))
        if msg.comment != "":
            _t1758 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1758,))
        for missing_string in msg.missing_strings:
            _t1759 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1759,))
        _t1760 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1760,))
        _t1761 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1761,))
        _t1762 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1762,))
        if msg.partition_size_mb != 0:
            _t1763 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1763,))
        return sorted(result)

    def deconstruct_csv_storage_integration_optional(self, msg: logic_pb2.CSVConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        if not msg.HasField("storage_integration"):
            return None
        else:
            _t1764 = None
        assert msg.storage_integration is not None
        si = msg.storage_integration
        result = []
        if si.provider != "":
            _t1765 = self._make_value_string(si.provider)
            result.append(("provider", _t1765,))
        if si.azure_sas_token != "":
            _t1766 = self._make_value_string("***")
            result.append(("azure_sas_token", _t1766,))
        if si.s3_region != "":
            _t1767 = self._make_value_string(si.s3_region)
            result.append(("s3_region", _t1767,))
        if si.s3_access_key_id != "":
            _t1768 = self._make_value_string("***")
            result.append(("s3_access_key_id", _t1768,))
        if si.s3_secret_access_key != "":
            _t1769 = self._make_value_string("***")
            result.append(("s3_secret_access_key", _t1769,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1770 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1770,))
        _t1771 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1771,))
        _t1772 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1772,))
        _t1773 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1773,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1774 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1774,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1775 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1775,))
        _t1776 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1776,))
        _t1777 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1777,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1778 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1778,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1779 = self._make_value_string(msg.compression)
            result.append(("compression", _t1779,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1780 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1780,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1781 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1781,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1782 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1782,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1783 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1783,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1784 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1784,))
        return sorted(result)

    def mask_secret_value(self, pair: tuple[str, str]) -> str:
        return "***"

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1785 = None
        return None

    def deconstruct_iceberg_data_from_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.from_snapshot is not None
        if msg.from_snapshot != "":
            assert msg.from_snapshot is not None
            return msg.from_snapshot
        else:
            _t1786 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1787 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1788 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1788,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1789 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1789,))
        if msg.compression != "":
            _t1790 = self._make_value_string(msg.compression)
            result.append(("compression", _t1790,))
        if len(result) == 0:
            return None
        else:
            _t1791 = None
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
            _t1792 = None
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
        flat808 = self._try_flat(msg, self.pretty_transaction)
        if flat808 is not None:
            assert flat808 is not None
            self.write(flat808)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1598 = _dollar_dollar.configure
            else:
                _t1598 = None
            if _dollar_dollar.HasField("sync"):
                _t1599 = _dollar_dollar.sync
            else:
                _t1599 = None
            fields799 = (_t1598, _t1599, _dollar_dollar.epochs,)
            assert fields799 is not None
            unwrapped_fields800 = fields799
            self.write("(transaction")
            self.indent_sexp()
            field801 = unwrapped_fields800[0]
            if field801 is not None:
                self.newline()
                assert field801 is not None
                opt_val802 = field801
                self.pretty_configure(opt_val802)
            field803 = unwrapped_fields800[1]
            if field803 is not None:
                self.newline()
                assert field803 is not None
                opt_val804 = field803
                self.pretty_sync(opt_val804)
            field805 = unwrapped_fields800[2]
            if not len(field805) == 0:
                self.newline()
                for i807, elem806 in enumerate(field805):
                    if (i807 > 0):
                        self.newline()
                    self.pretty_epoch(elem806)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat811 = self._try_flat(msg, self.pretty_configure)
        if flat811 is not None:
            assert flat811 is not None
            self.write(flat811)
            return None
        else:
            _dollar_dollar = msg
            _t1600 = self.deconstruct_configure(_dollar_dollar)
            fields809 = _t1600
            assert fields809 is not None
            unwrapped_fields810 = fields809
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields810)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat815 = self._try_flat(msg, self.pretty_config_dict)
        if flat815 is not None:
            assert flat815 is not None
            self.write(flat815)
            return None
        else:
            fields812 = msg
            self.write("{")
            self.indent()
            if not len(fields812) == 0:
                self.newline()
                for i814, elem813 in enumerate(fields812):
                    if (i814 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem813)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat820 = self._try_flat(msg, self.pretty_config_key_value)
        if flat820 is not None:
            assert flat820 is not None
            self.write(flat820)
            return None
        else:
            _dollar_dollar = msg
            fields816 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields816 is not None
            unwrapped_fields817 = fields816
            self.write(":")
            field818 = unwrapped_fields817[0]
            self.write(field818)
            self.write(" ")
            field819 = unwrapped_fields817[1]
            self.pretty_raw_value(field819)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat846 = self._try_flat(msg, self.pretty_raw_value)
        if flat846 is not None:
            assert flat846 is not None
            self.write(flat846)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1601 = _dollar_dollar.date_value
            else:
                _t1601 = None
            deconstruct_result844 = _t1601
            if deconstruct_result844 is not None:
                assert deconstruct_result844 is not None
                unwrapped845 = deconstruct_result844
                self.pretty_raw_date(unwrapped845)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1602 = _dollar_dollar.datetime_value
                else:
                    _t1602 = None
                deconstruct_result842 = _t1602
                if deconstruct_result842 is not None:
                    assert deconstruct_result842 is not None
                    unwrapped843 = deconstruct_result842
                    self.pretty_raw_datetime(unwrapped843)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1603 = _dollar_dollar.string_value
                    else:
                        _t1603 = None
                    deconstruct_result840 = _t1603
                    if deconstruct_result840 is not None:
                        assert deconstruct_result840 is not None
                        unwrapped841 = deconstruct_result840
                        self.write(self.format_string_value(unwrapped841))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1604 = _dollar_dollar.int32_value
                        else:
                            _t1604 = None
                        deconstruct_result838 = _t1604
                        if deconstruct_result838 is not None:
                            assert deconstruct_result838 is not None
                            unwrapped839 = deconstruct_result838
                            self.write((str(unwrapped839) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1605 = _dollar_dollar.int_value
                            else:
                                _t1605 = None
                            deconstruct_result836 = _t1605
                            if deconstruct_result836 is not None:
                                assert deconstruct_result836 is not None
                                unwrapped837 = deconstruct_result836
                                self.write(str(unwrapped837))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1606 = _dollar_dollar.float32_value
                                else:
                                    _t1606 = None
                                deconstruct_result834 = _t1606
                                if deconstruct_result834 is not None:
                                    assert deconstruct_result834 is not None
                                    unwrapped835 = deconstruct_result834
                                    self.write(self.format_float32_literal(unwrapped835))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1607 = _dollar_dollar.float_value
                                    else:
                                        _t1607 = None
                                    deconstruct_result832 = _t1607
                                    if deconstruct_result832 is not None:
                                        assert deconstruct_result832 is not None
                                        unwrapped833 = deconstruct_result832
                                        self.write(str(unwrapped833))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1608 = _dollar_dollar.uint32_value
                                        else:
                                            _t1608 = None
                                        deconstruct_result830 = _t1608
                                        if deconstruct_result830 is not None:
                                            assert deconstruct_result830 is not None
                                            unwrapped831 = deconstruct_result830
                                            self.write((str(unwrapped831) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1609 = _dollar_dollar.uint128_value
                                            else:
                                                _t1609 = None
                                            deconstruct_result828 = _t1609
                                            if deconstruct_result828 is not None:
                                                assert deconstruct_result828 is not None
                                                unwrapped829 = deconstruct_result828
                                                self.write(self.format_uint128(unwrapped829))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1610 = _dollar_dollar.int128_value
                                                else:
                                                    _t1610 = None
                                                deconstruct_result826 = _t1610
                                                if deconstruct_result826 is not None:
                                                    assert deconstruct_result826 is not None
                                                    unwrapped827 = deconstruct_result826
                                                    self.write(self.format_int128(unwrapped827))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1611 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1611 = None
                                                    deconstruct_result824 = _t1611
                                                    if deconstruct_result824 is not None:
                                                        assert deconstruct_result824 is not None
                                                        unwrapped825 = deconstruct_result824
                                                        self.write(self.format_decimal(unwrapped825))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1612 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1612 = None
                                                        deconstruct_result822 = _t1612
                                                        if deconstruct_result822 is not None:
                                                            assert deconstruct_result822 is not None
                                                            unwrapped823 = deconstruct_result822
                                                            self.pretty_boolean_value(unwrapped823)
                                                        else:
                                                            fields821 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat852 = self._try_flat(msg, self.pretty_raw_date)
        if flat852 is not None:
            assert flat852 is not None
            self.write(flat852)
            return None
        else:
            _dollar_dollar = msg
            fields847 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields847 is not None
            unwrapped_fields848 = fields847
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field849 = unwrapped_fields848[0]
            self.write(str(field849))
            self.newline()
            field850 = unwrapped_fields848[1]
            self.write(str(field850))
            self.newline()
            field851 = unwrapped_fields848[2]
            self.write(str(field851))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat863 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat863 is not None:
            assert flat863 is not None
            self.write(flat863)
            return None
        else:
            _dollar_dollar = msg
            fields853 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields853 is not None
            unwrapped_fields854 = fields853
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field855 = unwrapped_fields854[0]
            self.write(str(field855))
            self.newline()
            field856 = unwrapped_fields854[1]
            self.write(str(field856))
            self.newline()
            field857 = unwrapped_fields854[2]
            self.write(str(field857))
            self.newline()
            field858 = unwrapped_fields854[3]
            self.write(str(field858))
            self.newline()
            field859 = unwrapped_fields854[4]
            self.write(str(field859))
            self.newline()
            field860 = unwrapped_fields854[5]
            self.write(str(field860))
            field861 = unwrapped_fields854[6]
            if field861 is not None:
                self.newline()
                assert field861 is not None
                opt_val862 = field861
                self.write(str(opt_val862))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1613 = ()
        else:
            _t1613 = None
        deconstruct_result866 = _t1613
        if deconstruct_result866 is not None:
            assert deconstruct_result866 is not None
            unwrapped867 = deconstruct_result866
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1614 = ()
            else:
                _t1614 = None
            deconstruct_result864 = _t1614
            if deconstruct_result864 is not None:
                assert deconstruct_result864 is not None
                unwrapped865 = deconstruct_result864
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat872 = self._try_flat(msg, self.pretty_sync)
        if flat872 is not None:
            assert flat872 is not None
            self.write(flat872)
            return None
        else:
            _dollar_dollar = msg
            fields868 = _dollar_dollar.fragments
            assert fields868 is not None
            unwrapped_fields869 = fields868
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields869) == 0:
                self.newline()
                for i871, elem870 in enumerate(unwrapped_fields869):
                    if (i871 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem870)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat875 = self._try_flat(msg, self.pretty_fragment_id)
        if flat875 is not None:
            assert flat875 is not None
            self.write(flat875)
            return None
        else:
            _dollar_dollar = msg
            fields873 = self.fragment_id_to_string(_dollar_dollar)
            assert fields873 is not None
            unwrapped_fields874 = fields873
            self.write(":")
            self.write(unwrapped_fields874)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat882 = self._try_flat(msg, self.pretty_epoch)
        if flat882 is not None:
            assert flat882 is not None
            self.write(flat882)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1615 = _dollar_dollar.writes
            else:
                _t1615 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1616 = _dollar_dollar.reads
            else:
                _t1616 = None
            fields876 = (_t1615, _t1616,)
            assert fields876 is not None
            unwrapped_fields877 = fields876
            self.write("(epoch")
            self.indent_sexp()
            field878 = unwrapped_fields877[0]
            if field878 is not None:
                self.newline()
                assert field878 is not None
                opt_val879 = field878
                self.pretty_epoch_writes(opt_val879)
            field880 = unwrapped_fields877[1]
            if field880 is not None:
                self.newline()
                assert field880 is not None
                opt_val881 = field880
                self.pretty_epoch_reads(opt_val881)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat886 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat886 is not None:
            assert flat886 is not None
            self.write(flat886)
            return None
        else:
            fields883 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields883) == 0:
                self.newline()
                for i885, elem884 in enumerate(fields883):
                    if (i885 > 0):
                        self.newline()
                    self.pretty_write(elem884)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat895 = self._try_flat(msg, self.pretty_write)
        if flat895 is not None:
            assert flat895 is not None
            self.write(flat895)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1617 = _dollar_dollar.define
            else:
                _t1617 = None
            deconstruct_result893 = _t1617
            if deconstruct_result893 is not None:
                assert deconstruct_result893 is not None
                unwrapped894 = deconstruct_result893
                self.pretty_define(unwrapped894)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1618 = _dollar_dollar.undefine
                else:
                    _t1618 = None
                deconstruct_result891 = _t1618
                if deconstruct_result891 is not None:
                    assert deconstruct_result891 is not None
                    unwrapped892 = deconstruct_result891
                    self.pretty_undefine(unwrapped892)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1619 = _dollar_dollar.context
                    else:
                        _t1619 = None
                    deconstruct_result889 = _t1619
                    if deconstruct_result889 is not None:
                        assert deconstruct_result889 is not None
                        unwrapped890 = deconstruct_result889
                        self.pretty_context(unwrapped890)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1620 = _dollar_dollar.snapshot
                        else:
                            _t1620 = None
                        deconstruct_result887 = _t1620
                        if deconstruct_result887 is not None:
                            assert deconstruct_result887 is not None
                            unwrapped888 = deconstruct_result887
                            self.pretty_snapshot(unwrapped888)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat898 = self._try_flat(msg, self.pretty_define)
        if flat898 is not None:
            assert flat898 is not None
            self.write(flat898)
            return None
        else:
            _dollar_dollar = msg
            fields896 = _dollar_dollar.fragment
            assert fields896 is not None
            unwrapped_fields897 = fields896
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields897)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat905 = self._try_flat(msg, self.pretty_fragment)
        if flat905 is not None:
            assert flat905 is not None
            self.write(flat905)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields899 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields899 is not None
            unwrapped_fields900 = fields899
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field901 = unwrapped_fields900[0]
            self.pretty_new_fragment_id(field901)
            field902 = unwrapped_fields900[1]
            if not len(field902) == 0:
                self.newline()
                for i904, elem903 in enumerate(field902):
                    if (i904 > 0):
                        self.newline()
                    self.pretty_declaration(elem903)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat907 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat907 is not None:
            assert flat907 is not None
            self.write(flat907)
            return None
        else:
            fields906 = msg
            self.pretty_fragment_id(fields906)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat916 = self._try_flat(msg, self.pretty_declaration)
        if flat916 is not None:
            assert flat916 is not None
            self.write(flat916)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1621 = getattr(_dollar_dollar, 'def')
            else:
                _t1621 = None
            deconstruct_result914 = _t1621
            if deconstruct_result914 is not None:
                assert deconstruct_result914 is not None
                unwrapped915 = deconstruct_result914
                self.pretty_def(unwrapped915)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1622 = _dollar_dollar.algorithm
                else:
                    _t1622 = None
                deconstruct_result912 = _t1622
                if deconstruct_result912 is not None:
                    assert deconstruct_result912 is not None
                    unwrapped913 = deconstruct_result912
                    self.pretty_algorithm(unwrapped913)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1623 = _dollar_dollar.constraint
                    else:
                        _t1623 = None
                    deconstruct_result910 = _t1623
                    if deconstruct_result910 is not None:
                        assert deconstruct_result910 is not None
                        unwrapped911 = deconstruct_result910
                        self.pretty_constraint(unwrapped911)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1624 = _dollar_dollar.data
                        else:
                            _t1624 = None
                        deconstruct_result908 = _t1624
                        if deconstruct_result908 is not None:
                            assert deconstruct_result908 is not None
                            unwrapped909 = deconstruct_result908
                            self.pretty_data(unwrapped909)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat923 = self._try_flat(msg, self.pretty_def)
        if flat923 is not None:
            assert flat923 is not None
            self.write(flat923)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1625 = _dollar_dollar.attrs
            else:
                _t1625 = None
            fields917 = (_dollar_dollar.name, _dollar_dollar.body, _t1625,)
            assert fields917 is not None
            unwrapped_fields918 = fields917
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field919 = unwrapped_fields918[0]
            self.pretty_relation_id(field919)
            self.newline()
            field920 = unwrapped_fields918[1]
            self.pretty_abstraction(field920)
            field921 = unwrapped_fields918[2]
            if field921 is not None:
                self.newline()
                assert field921 is not None
                opt_val922 = field921
                self.pretty_attrs(opt_val922)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat928 = self._try_flat(msg, self.pretty_relation_id)
        if flat928 is not None:
            assert flat928 is not None
            self.write(flat928)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1627 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1626 = _t1627
            else:
                _t1626 = None
            deconstruct_result926 = _t1626
            if deconstruct_result926 is not None:
                assert deconstruct_result926 is not None
                unwrapped927 = deconstruct_result926
                self.write(":")
                self.write(unwrapped927)
            else:
                _dollar_dollar = msg
                _t1628 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result924 = _t1628
                if deconstruct_result924 is not None:
                    assert deconstruct_result924 is not None
                    unwrapped925 = deconstruct_result924
                    self.write(self.format_uint128(unwrapped925))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat933 = self._try_flat(msg, self.pretty_abstraction)
        if flat933 is not None:
            assert flat933 is not None
            self.write(flat933)
            return None
        else:
            _dollar_dollar = msg
            _t1629 = self.deconstruct_bindings(_dollar_dollar)
            fields929 = (_t1629, _dollar_dollar.value,)
            assert fields929 is not None
            unwrapped_fields930 = fields929
            self.write("(")
            self.indent()
            field931 = unwrapped_fields930[0]
            self.pretty_bindings(field931)
            self.newline()
            field932 = unwrapped_fields930[1]
            self.pretty_formula(field932)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat941 = self._try_flat(msg, self.pretty_bindings)
        if flat941 is not None:
            assert flat941 is not None
            self.write(flat941)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1630 = _dollar_dollar[1]
            else:
                _t1630 = None
            fields934 = (_dollar_dollar[0], _t1630,)
            assert fields934 is not None
            unwrapped_fields935 = fields934
            self.write("[")
            self.indent()
            field936 = unwrapped_fields935[0]
            for i938, elem937 in enumerate(field936):
                if (i938 > 0):
                    self.newline()
                self.pretty_binding(elem937)
            field939 = unwrapped_fields935[1]
            if field939 is not None:
                self.newline()
                assert field939 is not None
                opt_val940 = field939
                self.pretty_value_bindings(opt_val940)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat946 = self._try_flat(msg, self.pretty_binding)
        if flat946 is not None:
            assert flat946 is not None
            self.write(flat946)
            return None
        else:
            _dollar_dollar = msg
            fields942 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields942 is not None
            unwrapped_fields943 = fields942
            field944 = unwrapped_fields943[0]
            self.write(field944)
            self.write("::")
            field945 = unwrapped_fields943[1]
            self.pretty_type(field945)

    def pretty_type(self, msg: logic_pb2.Type):
        flat975 = self._try_flat(msg, self.pretty_type)
        if flat975 is not None:
            assert flat975 is not None
            self.write(flat975)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1631 = _dollar_dollar.unspecified_type
            else:
                _t1631 = None
            deconstruct_result973 = _t1631
            if deconstruct_result973 is not None:
                assert deconstruct_result973 is not None
                unwrapped974 = deconstruct_result973
                self.pretty_unspecified_type(unwrapped974)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1632 = _dollar_dollar.string_type
                else:
                    _t1632 = None
                deconstruct_result971 = _t1632
                if deconstruct_result971 is not None:
                    assert deconstruct_result971 is not None
                    unwrapped972 = deconstruct_result971
                    self.pretty_string_type(unwrapped972)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1633 = _dollar_dollar.int_type
                    else:
                        _t1633 = None
                    deconstruct_result969 = _t1633
                    if deconstruct_result969 is not None:
                        assert deconstruct_result969 is not None
                        unwrapped970 = deconstruct_result969
                        self.pretty_int_type(unwrapped970)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1634 = _dollar_dollar.float_type
                        else:
                            _t1634 = None
                        deconstruct_result967 = _t1634
                        if deconstruct_result967 is not None:
                            assert deconstruct_result967 is not None
                            unwrapped968 = deconstruct_result967
                            self.pretty_float_type(unwrapped968)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1635 = _dollar_dollar.uint128_type
                            else:
                                _t1635 = None
                            deconstruct_result965 = _t1635
                            if deconstruct_result965 is not None:
                                assert deconstruct_result965 is not None
                                unwrapped966 = deconstruct_result965
                                self.pretty_uint128_type(unwrapped966)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1636 = _dollar_dollar.int128_type
                                else:
                                    _t1636 = None
                                deconstruct_result963 = _t1636
                                if deconstruct_result963 is not None:
                                    assert deconstruct_result963 is not None
                                    unwrapped964 = deconstruct_result963
                                    self.pretty_int128_type(unwrapped964)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1637 = _dollar_dollar.date_type
                                    else:
                                        _t1637 = None
                                    deconstruct_result961 = _t1637
                                    if deconstruct_result961 is not None:
                                        assert deconstruct_result961 is not None
                                        unwrapped962 = deconstruct_result961
                                        self.pretty_date_type(unwrapped962)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1638 = _dollar_dollar.datetime_type
                                        else:
                                            _t1638 = None
                                        deconstruct_result959 = _t1638
                                        if deconstruct_result959 is not None:
                                            assert deconstruct_result959 is not None
                                            unwrapped960 = deconstruct_result959
                                            self.pretty_datetime_type(unwrapped960)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1639 = _dollar_dollar.missing_type
                                            else:
                                                _t1639 = None
                                            deconstruct_result957 = _t1639
                                            if deconstruct_result957 is not None:
                                                assert deconstruct_result957 is not None
                                                unwrapped958 = deconstruct_result957
                                                self.pretty_missing_type(unwrapped958)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1640 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1640 = None
                                                deconstruct_result955 = _t1640
                                                if deconstruct_result955 is not None:
                                                    assert deconstruct_result955 is not None
                                                    unwrapped956 = deconstruct_result955
                                                    self.pretty_decimal_type(unwrapped956)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1641 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1641 = None
                                                    deconstruct_result953 = _t1641
                                                    if deconstruct_result953 is not None:
                                                        assert deconstruct_result953 is not None
                                                        unwrapped954 = deconstruct_result953
                                                        self.pretty_boolean_type(unwrapped954)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1642 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1642 = None
                                                        deconstruct_result951 = _t1642
                                                        if deconstruct_result951 is not None:
                                                            assert deconstruct_result951 is not None
                                                            unwrapped952 = deconstruct_result951
                                                            self.pretty_int32_type(unwrapped952)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1643 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1643 = None
                                                            deconstruct_result949 = _t1643
                                                            if deconstruct_result949 is not None:
                                                                assert deconstruct_result949 is not None
                                                                unwrapped950 = deconstruct_result949
                                                                self.pretty_float32_type(unwrapped950)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1644 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1644 = None
                                                                deconstruct_result947 = _t1644
                                                                if deconstruct_result947 is not None:
                                                                    assert deconstruct_result947 is not None
                                                                    unwrapped948 = deconstruct_result947
                                                                    self.pretty_uint32_type(unwrapped948)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields976 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields977 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields978 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields979 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields980 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields981 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields982 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields983 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields984 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat989 = self._try_flat(msg, self.pretty_decimal_type)
        if flat989 is not None:
            assert flat989 is not None
            self.write(flat989)
            return None
        else:
            _dollar_dollar = msg
            fields985 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields985 is not None
            unwrapped_fields986 = fields985
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field987 = unwrapped_fields986[0]
            self.write(str(field987))
            self.newline()
            field988 = unwrapped_fields986[1]
            self.write(str(field988))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields990 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields991 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields992 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields993 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat997 = self._try_flat(msg, self.pretty_value_bindings)
        if flat997 is not None:
            assert flat997 is not None
            self.write(flat997)
            return None
        else:
            fields994 = msg
            self.write("|")
            if not len(fields994) == 0:
                self.write(" ")
                for i996, elem995 in enumerate(fields994):
                    if (i996 > 0):
                        self.newline()
                    self.pretty_binding(elem995)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1024 = self._try_flat(msg, self.pretty_formula)
        if flat1024 is not None:
            assert flat1024 is not None
            self.write(flat1024)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1645 = _dollar_dollar.conjunction
            else:
                _t1645 = None
            deconstruct_result1022 = _t1645
            if deconstruct_result1022 is not None:
                assert deconstruct_result1022 is not None
                unwrapped1023 = deconstruct_result1022
                self.pretty_true(unwrapped1023)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1646 = _dollar_dollar.disjunction
                else:
                    _t1646 = None
                deconstruct_result1020 = _t1646
                if deconstruct_result1020 is not None:
                    assert deconstruct_result1020 is not None
                    unwrapped1021 = deconstruct_result1020
                    self.pretty_false(unwrapped1021)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1647 = _dollar_dollar.exists
                    else:
                        _t1647 = None
                    deconstruct_result1018 = _t1647
                    if deconstruct_result1018 is not None:
                        assert deconstruct_result1018 is not None
                        unwrapped1019 = deconstruct_result1018
                        self.pretty_exists(unwrapped1019)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1648 = _dollar_dollar.reduce
                        else:
                            _t1648 = None
                        deconstruct_result1016 = _t1648
                        if deconstruct_result1016 is not None:
                            assert deconstruct_result1016 is not None
                            unwrapped1017 = deconstruct_result1016
                            self.pretty_reduce(unwrapped1017)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1649 = _dollar_dollar.conjunction
                            else:
                                _t1649 = None
                            deconstruct_result1014 = _t1649
                            if deconstruct_result1014 is not None:
                                assert deconstruct_result1014 is not None
                                unwrapped1015 = deconstruct_result1014
                                self.pretty_conjunction(unwrapped1015)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1650 = _dollar_dollar.disjunction
                                else:
                                    _t1650 = None
                                deconstruct_result1012 = _t1650
                                if deconstruct_result1012 is not None:
                                    assert deconstruct_result1012 is not None
                                    unwrapped1013 = deconstruct_result1012
                                    self.pretty_disjunction(unwrapped1013)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1651 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1651 = None
                                    deconstruct_result1010 = _t1651
                                    if deconstruct_result1010 is not None:
                                        assert deconstruct_result1010 is not None
                                        unwrapped1011 = deconstruct_result1010
                                        self.pretty_not(unwrapped1011)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1652 = _dollar_dollar.ffi
                                        else:
                                            _t1652 = None
                                        deconstruct_result1008 = _t1652
                                        if deconstruct_result1008 is not None:
                                            assert deconstruct_result1008 is not None
                                            unwrapped1009 = deconstruct_result1008
                                            self.pretty_ffi(unwrapped1009)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1653 = _dollar_dollar.atom
                                            else:
                                                _t1653 = None
                                            deconstruct_result1006 = _t1653
                                            if deconstruct_result1006 is not None:
                                                assert deconstruct_result1006 is not None
                                                unwrapped1007 = deconstruct_result1006
                                                self.pretty_atom(unwrapped1007)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1654 = _dollar_dollar.pragma
                                                else:
                                                    _t1654 = None
                                                deconstruct_result1004 = _t1654
                                                if deconstruct_result1004 is not None:
                                                    assert deconstruct_result1004 is not None
                                                    unwrapped1005 = deconstruct_result1004
                                                    self.pretty_pragma(unwrapped1005)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1655 = _dollar_dollar.primitive
                                                    else:
                                                        _t1655 = None
                                                    deconstruct_result1002 = _t1655
                                                    if deconstruct_result1002 is not None:
                                                        assert deconstruct_result1002 is not None
                                                        unwrapped1003 = deconstruct_result1002
                                                        self.pretty_primitive(unwrapped1003)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1656 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1656 = None
                                                        deconstruct_result1000 = _t1656
                                                        if deconstruct_result1000 is not None:
                                                            assert deconstruct_result1000 is not None
                                                            unwrapped1001 = deconstruct_result1000
                                                            self.pretty_rel_atom(unwrapped1001)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1657 = _dollar_dollar.cast
                                                            else:
                                                                _t1657 = None
                                                            deconstruct_result998 = _t1657
                                                            if deconstruct_result998 is not None:
                                                                assert deconstruct_result998 is not None
                                                                unwrapped999 = deconstruct_result998
                                                                self.pretty_cast(unwrapped999)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields1025 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1026 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1031 = self._try_flat(msg, self.pretty_exists)
        if flat1031 is not None:
            assert flat1031 is not None
            self.write(flat1031)
            return None
        else:
            _dollar_dollar = msg
            _t1658 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1027 = (_t1658, _dollar_dollar.body.value,)
            assert fields1027 is not None
            unwrapped_fields1028 = fields1027
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1029 = unwrapped_fields1028[0]
            self.pretty_bindings(field1029)
            self.newline()
            field1030 = unwrapped_fields1028[1]
            self.pretty_formula(field1030)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1037 = self._try_flat(msg, self.pretty_reduce)
        if flat1037 is not None:
            assert flat1037 is not None
            self.write(flat1037)
            return None
        else:
            _dollar_dollar = msg
            fields1032 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1032 is not None
            unwrapped_fields1033 = fields1032
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1034 = unwrapped_fields1033[0]
            self.pretty_abstraction(field1034)
            self.newline()
            field1035 = unwrapped_fields1033[1]
            self.pretty_abstraction(field1035)
            self.newline()
            field1036 = unwrapped_fields1033[2]
            self.pretty_terms(field1036)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1041 = self._try_flat(msg, self.pretty_terms)
        if flat1041 is not None:
            assert flat1041 is not None
            self.write(flat1041)
            return None
        else:
            fields1038 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1038) == 0:
                self.newline()
                for i1040, elem1039 in enumerate(fields1038):
                    if (i1040 > 0):
                        self.newline()
                    self.pretty_term(elem1039)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1046 = self._try_flat(msg, self.pretty_term)
        if flat1046 is not None:
            assert flat1046 is not None
            self.write(flat1046)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1659 = _dollar_dollar.var
            else:
                _t1659 = None
            deconstruct_result1044 = _t1659
            if deconstruct_result1044 is not None:
                assert deconstruct_result1044 is not None
                unwrapped1045 = deconstruct_result1044
                self.pretty_var(unwrapped1045)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1660 = _dollar_dollar.constant
                else:
                    _t1660 = None
                deconstruct_result1042 = _t1660
                if deconstruct_result1042 is not None:
                    assert deconstruct_result1042 is not None
                    unwrapped1043 = deconstruct_result1042
                    self.pretty_value(unwrapped1043)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1049 = self._try_flat(msg, self.pretty_var)
        if flat1049 is not None:
            assert flat1049 is not None
            self.write(flat1049)
            return None
        else:
            _dollar_dollar = msg
            fields1047 = _dollar_dollar.name
            assert fields1047 is not None
            unwrapped_fields1048 = fields1047
            self.write(unwrapped_fields1048)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1075 = self._try_flat(msg, self.pretty_value)
        if flat1075 is not None:
            assert flat1075 is not None
            self.write(flat1075)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1661 = _dollar_dollar.date_value
            else:
                _t1661 = None
            deconstruct_result1073 = _t1661
            if deconstruct_result1073 is not None:
                assert deconstruct_result1073 is not None
                unwrapped1074 = deconstruct_result1073
                self.pretty_date(unwrapped1074)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1662 = _dollar_dollar.datetime_value
                else:
                    _t1662 = None
                deconstruct_result1071 = _t1662
                if deconstruct_result1071 is not None:
                    assert deconstruct_result1071 is not None
                    unwrapped1072 = deconstruct_result1071
                    self.pretty_datetime(unwrapped1072)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1663 = _dollar_dollar.string_value
                    else:
                        _t1663 = None
                    deconstruct_result1069 = _t1663
                    if deconstruct_result1069 is not None:
                        assert deconstruct_result1069 is not None
                        unwrapped1070 = deconstruct_result1069
                        self.write(self.format_string_value(unwrapped1070))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1664 = _dollar_dollar.int32_value
                        else:
                            _t1664 = None
                        deconstruct_result1067 = _t1664
                        if deconstruct_result1067 is not None:
                            assert deconstruct_result1067 is not None
                            unwrapped1068 = deconstruct_result1067
                            self.write((str(unwrapped1068) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1665 = _dollar_dollar.int_value
                            else:
                                _t1665 = None
                            deconstruct_result1065 = _t1665
                            if deconstruct_result1065 is not None:
                                assert deconstruct_result1065 is not None
                                unwrapped1066 = deconstruct_result1065
                                self.write(str(unwrapped1066))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1666 = _dollar_dollar.float32_value
                                else:
                                    _t1666 = None
                                deconstruct_result1063 = _t1666
                                if deconstruct_result1063 is not None:
                                    assert deconstruct_result1063 is not None
                                    unwrapped1064 = deconstruct_result1063
                                    self.write(self.format_float32_literal(unwrapped1064))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1667 = _dollar_dollar.float_value
                                    else:
                                        _t1667 = None
                                    deconstruct_result1061 = _t1667
                                    if deconstruct_result1061 is not None:
                                        assert deconstruct_result1061 is not None
                                        unwrapped1062 = deconstruct_result1061
                                        self.write(str(unwrapped1062))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1668 = _dollar_dollar.uint32_value
                                        else:
                                            _t1668 = None
                                        deconstruct_result1059 = _t1668
                                        if deconstruct_result1059 is not None:
                                            assert deconstruct_result1059 is not None
                                            unwrapped1060 = deconstruct_result1059
                                            self.write((str(unwrapped1060) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1669 = _dollar_dollar.uint128_value
                                            else:
                                                _t1669 = None
                                            deconstruct_result1057 = _t1669
                                            if deconstruct_result1057 is not None:
                                                assert deconstruct_result1057 is not None
                                                unwrapped1058 = deconstruct_result1057
                                                self.write(self.format_uint128(unwrapped1058))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1670 = _dollar_dollar.int128_value
                                                else:
                                                    _t1670 = None
                                                deconstruct_result1055 = _t1670
                                                if deconstruct_result1055 is not None:
                                                    assert deconstruct_result1055 is not None
                                                    unwrapped1056 = deconstruct_result1055
                                                    self.write(self.format_int128(unwrapped1056))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1671 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1671 = None
                                                    deconstruct_result1053 = _t1671
                                                    if deconstruct_result1053 is not None:
                                                        assert deconstruct_result1053 is not None
                                                        unwrapped1054 = deconstruct_result1053
                                                        self.write(self.format_decimal(unwrapped1054))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1672 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1672 = None
                                                        deconstruct_result1051 = _t1672
                                                        if deconstruct_result1051 is not None:
                                                            assert deconstruct_result1051 is not None
                                                            unwrapped1052 = deconstruct_result1051
                                                            self.pretty_boolean_value(unwrapped1052)
                                                        else:
                                                            fields1050 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1081 = self._try_flat(msg, self.pretty_date)
        if flat1081 is not None:
            assert flat1081 is not None
            self.write(flat1081)
            return None
        else:
            _dollar_dollar = msg
            fields1076 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1076 is not None
            unwrapped_fields1077 = fields1076
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1078 = unwrapped_fields1077[0]
            self.write(str(field1078))
            self.newline()
            field1079 = unwrapped_fields1077[1]
            self.write(str(field1079))
            self.newline()
            field1080 = unwrapped_fields1077[2]
            self.write(str(field1080))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1092 = self._try_flat(msg, self.pretty_datetime)
        if flat1092 is not None:
            assert flat1092 is not None
            self.write(flat1092)
            return None
        else:
            _dollar_dollar = msg
            fields1082 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1082 is not None
            unwrapped_fields1083 = fields1082
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1084 = unwrapped_fields1083[0]
            self.write(str(field1084))
            self.newline()
            field1085 = unwrapped_fields1083[1]
            self.write(str(field1085))
            self.newline()
            field1086 = unwrapped_fields1083[2]
            self.write(str(field1086))
            self.newline()
            field1087 = unwrapped_fields1083[3]
            self.write(str(field1087))
            self.newline()
            field1088 = unwrapped_fields1083[4]
            self.write(str(field1088))
            self.newline()
            field1089 = unwrapped_fields1083[5]
            self.write(str(field1089))
            field1090 = unwrapped_fields1083[6]
            if field1090 is not None:
                self.newline()
                assert field1090 is not None
                opt_val1091 = field1090
                self.write(str(opt_val1091))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1097 = self._try_flat(msg, self.pretty_conjunction)
        if flat1097 is not None:
            assert flat1097 is not None
            self.write(flat1097)
            return None
        else:
            _dollar_dollar = msg
            fields1093 = _dollar_dollar.args
            assert fields1093 is not None
            unwrapped_fields1094 = fields1093
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1094) == 0:
                self.newline()
                for i1096, elem1095 in enumerate(unwrapped_fields1094):
                    if (i1096 > 0):
                        self.newline()
                    self.pretty_formula(elem1095)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1102 = self._try_flat(msg, self.pretty_disjunction)
        if flat1102 is not None:
            assert flat1102 is not None
            self.write(flat1102)
            return None
        else:
            _dollar_dollar = msg
            fields1098 = _dollar_dollar.args
            assert fields1098 is not None
            unwrapped_fields1099 = fields1098
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1099) == 0:
                self.newline()
                for i1101, elem1100 in enumerate(unwrapped_fields1099):
                    if (i1101 > 0):
                        self.newline()
                    self.pretty_formula(elem1100)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1105 = self._try_flat(msg, self.pretty_not)
        if flat1105 is not None:
            assert flat1105 is not None
            self.write(flat1105)
            return None
        else:
            _dollar_dollar = msg
            fields1103 = _dollar_dollar.arg
            assert fields1103 is not None
            unwrapped_fields1104 = fields1103
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1104)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1111 = self._try_flat(msg, self.pretty_ffi)
        if flat1111 is not None:
            assert flat1111 is not None
            self.write(flat1111)
            return None
        else:
            _dollar_dollar = msg
            fields1106 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1106 is not None
            unwrapped_fields1107 = fields1106
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1108 = unwrapped_fields1107[0]
            self.pretty_name(field1108)
            self.newline()
            field1109 = unwrapped_fields1107[1]
            self.pretty_ffi_args(field1109)
            self.newline()
            field1110 = unwrapped_fields1107[2]
            self.pretty_terms(field1110)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1113 = self._try_flat(msg, self.pretty_name)
        if flat1113 is not None:
            assert flat1113 is not None
            self.write(flat1113)
            return None
        else:
            fields1112 = msg
            self.write(":")
            self.write(fields1112)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1117 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1117 is not None:
            assert flat1117 is not None
            self.write(flat1117)
            return None
        else:
            fields1114 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1114) == 0:
                self.newline()
                for i1116, elem1115 in enumerate(fields1114):
                    if (i1116 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1115)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1124 = self._try_flat(msg, self.pretty_atom)
        if flat1124 is not None:
            assert flat1124 is not None
            self.write(flat1124)
            return None
        else:
            _dollar_dollar = msg
            fields1118 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1118 is not None
            unwrapped_fields1119 = fields1118
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1120 = unwrapped_fields1119[0]
            self.pretty_relation_id(field1120)
            field1121 = unwrapped_fields1119[1]
            if not len(field1121) == 0:
                self.newline()
                for i1123, elem1122 in enumerate(field1121):
                    if (i1123 > 0):
                        self.newline()
                    self.pretty_term(elem1122)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1131 = self._try_flat(msg, self.pretty_pragma)
        if flat1131 is not None:
            assert flat1131 is not None
            self.write(flat1131)
            return None
        else:
            _dollar_dollar = msg
            fields1125 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1125 is not None
            unwrapped_fields1126 = fields1125
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1127 = unwrapped_fields1126[0]
            self.pretty_name(field1127)
            field1128 = unwrapped_fields1126[1]
            if not len(field1128) == 0:
                self.newline()
                for i1130, elem1129 in enumerate(field1128):
                    if (i1130 > 0):
                        self.newline()
                    self.pretty_term(elem1129)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1147 = self._try_flat(msg, self.pretty_primitive)
        if flat1147 is not None:
            assert flat1147 is not None
            self.write(flat1147)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1673 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1673 = None
            guard_result1146 = _t1673
            if guard_result1146 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1674 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1674 = None
                guard_result1145 = _t1674
                if guard_result1145 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1675 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1675 = None
                    guard_result1144 = _t1675
                    if guard_result1144 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1676 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1676 = None
                        guard_result1143 = _t1676
                        if guard_result1143 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1677 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1677 = None
                            guard_result1142 = _t1677
                            if guard_result1142 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1678 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1678 = None
                                guard_result1141 = _t1678
                                if guard_result1141 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1679 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1679 = None
                                    guard_result1140 = _t1679
                                    if guard_result1140 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1680 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1680 = None
                                        guard_result1139 = _t1680
                                        if guard_result1139 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1681 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1681 = None
                                            guard_result1138 = _t1681
                                            if guard_result1138 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1132 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1132 is not None
                                                unwrapped_fields1133 = fields1132
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1134 = unwrapped_fields1133[0]
                                                self.pretty_name(field1134)
                                                field1135 = unwrapped_fields1133[1]
                                                if not len(field1135) == 0:
                                                    self.newline()
                                                    for i1137, elem1136 in enumerate(field1135):
                                                        if (i1137 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1136)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1152 = self._try_flat(msg, self.pretty_eq)
        if flat1152 is not None:
            assert flat1152 is not None
            self.write(flat1152)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1682 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1682 = None
            fields1148 = _t1682
            assert fields1148 is not None
            unwrapped_fields1149 = fields1148
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1150 = unwrapped_fields1149[0]
            self.pretty_term(field1150)
            self.newline()
            field1151 = unwrapped_fields1149[1]
            self.pretty_term(field1151)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1157 = self._try_flat(msg, self.pretty_lt)
        if flat1157 is not None:
            assert flat1157 is not None
            self.write(flat1157)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1683 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1683 = None
            fields1153 = _t1683
            assert fields1153 is not None
            unwrapped_fields1154 = fields1153
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1155 = unwrapped_fields1154[0]
            self.pretty_term(field1155)
            self.newline()
            field1156 = unwrapped_fields1154[1]
            self.pretty_term(field1156)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1162 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1162 is not None:
            assert flat1162 is not None
            self.write(flat1162)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1684 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1684 = None
            fields1158 = _t1684
            assert fields1158 is not None
            unwrapped_fields1159 = fields1158
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1160 = unwrapped_fields1159[0]
            self.pretty_term(field1160)
            self.newline()
            field1161 = unwrapped_fields1159[1]
            self.pretty_term(field1161)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1167 = self._try_flat(msg, self.pretty_gt)
        if flat1167 is not None:
            assert flat1167 is not None
            self.write(flat1167)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1685 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1685 = None
            fields1163 = _t1685
            assert fields1163 is not None
            unwrapped_fields1164 = fields1163
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1165 = unwrapped_fields1164[0]
            self.pretty_term(field1165)
            self.newline()
            field1166 = unwrapped_fields1164[1]
            self.pretty_term(field1166)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1172 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1172 is not None:
            assert flat1172 is not None
            self.write(flat1172)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1686 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1686 = None
            fields1168 = _t1686
            assert fields1168 is not None
            unwrapped_fields1169 = fields1168
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1170 = unwrapped_fields1169[0]
            self.pretty_term(field1170)
            self.newline()
            field1171 = unwrapped_fields1169[1]
            self.pretty_term(field1171)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1178 = self._try_flat(msg, self.pretty_add)
        if flat1178 is not None:
            assert flat1178 is not None
            self.write(flat1178)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1687 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1687 = None
            fields1173 = _t1687
            assert fields1173 is not None
            unwrapped_fields1174 = fields1173
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1175 = unwrapped_fields1174[0]
            self.pretty_term(field1175)
            self.newline()
            field1176 = unwrapped_fields1174[1]
            self.pretty_term(field1176)
            self.newline()
            field1177 = unwrapped_fields1174[2]
            self.pretty_term(field1177)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1184 = self._try_flat(msg, self.pretty_minus)
        if flat1184 is not None:
            assert flat1184 is not None
            self.write(flat1184)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1688 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1688 = None
            fields1179 = _t1688
            assert fields1179 is not None
            unwrapped_fields1180 = fields1179
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1181 = unwrapped_fields1180[0]
            self.pretty_term(field1181)
            self.newline()
            field1182 = unwrapped_fields1180[1]
            self.pretty_term(field1182)
            self.newline()
            field1183 = unwrapped_fields1180[2]
            self.pretty_term(field1183)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1190 = self._try_flat(msg, self.pretty_multiply)
        if flat1190 is not None:
            assert flat1190 is not None
            self.write(flat1190)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1689 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1689 = None
            fields1185 = _t1689
            assert fields1185 is not None
            unwrapped_fields1186 = fields1185
            self.write("(*")
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

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1196 = self._try_flat(msg, self.pretty_divide)
        if flat1196 is not None:
            assert flat1196 is not None
            self.write(flat1196)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1690 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1690 = None
            fields1191 = _t1690
            assert fields1191 is not None
            unwrapped_fields1192 = fields1191
            self.write("(/")
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

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1201 = self._try_flat(msg, self.pretty_rel_term)
        if flat1201 is not None:
            assert flat1201 is not None
            self.write(flat1201)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1691 = _dollar_dollar.specialized_value
            else:
                _t1691 = None
            deconstruct_result1199 = _t1691
            if deconstruct_result1199 is not None:
                assert deconstruct_result1199 is not None
                unwrapped1200 = deconstruct_result1199
                self.pretty_specialized_value(unwrapped1200)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1692 = _dollar_dollar.term
                else:
                    _t1692 = None
                deconstruct_result1197 = _t1692
                if deconstruct_result1197 is not None:
                    assert deconstruct_result1197 is not None
                    unwrapped1198 = deconstruct_result1197
                    self.pretty_term(unwrapped1198)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1203 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1203 is not None:
            assert flat1203 is not None
            self.write(flat1203)
            return None
        else:
            fields1202 = msg
            self.write("#")
            self.pretty_raw_value(fields1202)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1210 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1210 is not None:
            assert flat1210 is not None
            self.write(flat1210)
            return None
        else:
            _dollar_dollar = msg
            fields1204 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1204 is not None
            unwrapped_fields1205 = fields1204
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1206 = unwrapped_fields1205[0]
            self.pretty_name(field1206)
            field1207 = unwrapped_fields1205[1]
            if not len(field1207) == 0:
                self.newline()
                for i1209, elem1208 in enumerate(field1207):
                    if (i1209 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1208)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1215 = self._try_flat(msg, self.pretty_cast)
        if flat1215 is not None:
            assert flat1215 is not None
            self.write(flat1215)
            return None
        else:
            _dollar_dollar = msg
            fields1211 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1211 is not None
            unwrapped_fields1212 = fields1211
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1213 = unwrapped_fields1212[0]
            self.pretty_term(field1213)
            self.newline()
            field1214 = unwrapped_fields1212[1]
            self.pretty_term(field1214)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1219 = self._try_flat(msg, self.pretty_attrs)
        if flat1219 is not None:
            assert flat1219 is not None
            self.write(flat1219)
            return None
        else:
            fields1216 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1216) == 0:
                self.newline()
                for i1218, elem1217 in enumerate(fields1216):
                    if (i1218 > 0):
                        self.newline()
                    self.pretty_attribute(elem1217)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1226 = self._try_flat(msg, self.pretty_attribute)
        if flat1226 is not None:
            assert flat1226 is not None
            self.write(flat1226)
            return None
        else:
            _dollar_dollar = msg
            fields1220 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1220 is not None
            unwrapped_fields1221 = fields1220
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1222 = unwrapped_fields1221[0]
            self.pretty_name(field1222)
            field1223 = unwrapped_fields1221[1]
            if not len(field1223) == 0:
                self.newline()
                for i1225, elem1224 in enumerate(field1223):
                    if (i1225 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1224)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1235 = self._try_flat(msg, self.pretty_algorithm)
        if flat1235 is not None:
            assert flat1235 is not None
            self.write(flat1235)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1693 = _dollar_dollar.attrs
            else:
                _t1693 = None
            fields1227 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body, _t1693,)
            assert fields1227 is not None
            unwrapped_fields1228 = fields1227
            self.write("(algorithm")
            self.indent_sexp()
            field1229 = unwrapped_fields1228[0]
            if not len(field1229) == 0:
                self.newline()
                for i1231, elem1230 in enumerate(field1229):
                    if (i1231 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1230)
            self.newline()
            field1232 = unwrapped_fields1228[1]
            self.pretty_script(field1232)
            field1233 = unwrapped_fields1228[2]
            if field1233 is not None:
                self.newline()
                assert field1233 is not None
                opt_val1234 = field1233
                self.pretty_attrs(opt_val1234)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1240 = self._try_flat(msg, self.pretty_script)
        if flat1240 is not None:
            assert flat1240 is not None
            self.write(flat1240)
            return None
        else:
            _dollar_dollar = msg
            fields1236 = _dollar_dollar.constructs
            assert fields1236 is not None
            unwrapped_fields1237 = fields1236
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1237) == 0:
                self.newline()
                for i1239, elem1238 in enumerate(unwrapped_fields1237):
                    if (i1239 > 0):
                        self.newline()
                    self.pretty_construct(elem1238)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1245 = self._try_flat(msg, self.pretty_construct)
        if flat1245 is not None:
            assert flat1245 is not None
            self.write(flat1245)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1694 = _dollar_dollar.loop
            else:
                _t1694 = None
            deconstruct_result1243 = _t1694
            if deconstruct_result1243 is not None:
                assert deconstruct_result1243 is not None
                unwrapped1244 = deconstruct_result1243
                self.pretty_loop(unwrapped1244)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1695 = _dollar_dollar.instruction
                else:
                    _t1695 = None
                deconstruct_result1241 = _t1695
                if deconstruct_result1241 is not None:
                    assert deconstruct_result1241 is not None
                    unwrapped1242 = deconstruct_result1241
                    self.pretty_instruction(unwrapped1242)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1252 = self._try_flat(msg, self.pretty_loop)
        if flat1252 is not None:
            assert flat1252 is not None
            self.write(flat1252)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1696 = _dollar_dollar.attrs
            else:
                _t1696 = None
            fields1246 = (_dollar_dollar.init, _dollar_dollar.body, _t1696,)
            assert fields1246 is not None
            unwrapped_fields1247 = fields1246
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1248 = unwrapped_fields1247[0]
            self.pretty_init(field1248)
            self.newline()
            field1249 = unwrapped_fields1247[1]
            self.pretty_script(field1249)
            field1250 = unwrapped_fields1247[2]
            if field1250 is not None:
                self.newline()
                assert field1250 is not None
                opt_val1251 = field1250
                self.pretty_attrs(opt_val1251)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1256 = self._try_flat(msg, self.pretty_init)
        if flat1256 is not None:
            assert flat1256 is not None
            self.write(flat1256)
            return None
        else:
            fields1253 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1253) == 0:
                self.newline()
                for i1255, elem1254 in enumerate(fields1253):
                    if (i1255 > 0):
                        self.newline()
                    self.pretty_instruction(elem1254)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1267 = self._try_flat(msg, self.pretty_instruction)
        if flat1267 is not None:
            assert flat1267 is not None
            self.write(flat1267)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1697 = _dollar_dollar.assign
            else:
                _t1697 = None
            deconstruct_result1265 = _t1697
            if deconstruct_result1265 is not None:
                assert deconstruct_result1265 is not None
                unwrapped1266 = deconstruct_result1265
                self.pretty_assign(unwrapped1266)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1698 = _dollar_dollar.upsert
                else:
                    _t1698 = None
                deconstruct_result1263 = _t1698
                if deconstruct_result1263 is not None:
                    assert deconstruct_result1263 is not None
                    unwrapped1264 = deconstruct_result1263
                    self.pretty_upsert(unwrapped1264)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1699 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1699 = None
                    deconstruct_result1261 = _t1699
                    if deconstruct_result1261 is not None:
                        assert deconstruct_result1261 is not None
                        unwrapped1262 = deconstruct_result1261
                        self.pretty_break(unwrapped1262)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1700 = _dollar_dollar.monoid_def
                        else:
                            _t1700 = None
                        deconstruct_result1259 = _t1700
                        if deconstruct_result1259 is not None:
                            assert deconstruct_result1259 is not None
                            unwrapped1260 = deconstruct_result1259
                            self.pretty_monoid_def(unwrapped1260)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1701 = _dollar_dollar.monus_def
                            else:
                                _t1701 = None
                            deconstruct_result1257 = _t1701
                            if deconstruct_result1257 is not None:
                                assert deconstruct_result1257 is not None
                                unwrapped1258 = deconstruct_result1257
                                self.pretty_monus_def(unwrapped1258)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1274 = self._try_flat(msg, self.pretty_assign)
        if flat1274 is not None:
            assert flat1274 is not None
            self.write(flat1274)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1702 = _dollar_dollar.attrs
            else:
                _t1702 = None
            fields1268 = (_dollar_dollar.name, _dollar_dollar.body, _t1702,)
            assert fields1268 is not None
            unwrapped_fields1269 = fields1268
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1270 = unwrapped_fields1269[0]
            self.pretty_relation_id(field1270)
            self.newline()
            field1271 = unwrapped_fields1269[1]
            self.pretty_abstraction(field1271)
            field1272 = unwrapped_fields1269[2]
            if field1272 is not None:
                self.newline()
                assert field1272 is not None
                opt_val1273 = field1272
                self.pretty_attrs(opt_val1273)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1281 = self._try_flat(msg, self.pretty_upsert)
        if flat1281 is not None:
            assert flat1281 is not None
            self.write(flat1281)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1703 = _dollar_dollar.attrs
            else:
                _t1703 = None
            fields1275 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1703,)
            assert fields1275 is not None
            unwrapped_fields1276 = fields1275
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1277 = unwrapped_fields1276[0]
            self.pretty_relation_id(field1277)
            self.newline()
            field1278 = unwrapped_fields1276[1]
            self.pretty_abstraction_with_arity(field1278)
            field1279 = unwrapped_fields1276[2]
            if field1279 is not None:
                self.newline()
                assert field1279 is not None
                opt_val1280 = field1279
                self.pretty_attrs(opt_val1280)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1286 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1286 is not None:
            assert flat1286 is not None
            self.write(flat1286)
            return None
        else:
            _dollar_dollar = msg
            _t1704 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1282 = (_t1704, _dollar_dollar[0].value,)
            assert fields1282 is not None
            unwrapped_fields1283 = fields1282
            self.write("(")
            self.indent()
            field1284 = unwrapped_fields1283[0]
            self.pretty_bindings(field1284)
            self.newline()
            field1285 = unwrapped_fields1283[1]
            self.pretty_formula(field1285)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1293 = self._try_flat(msg, self.pretty_break)
        if flat1293 is not None:
            assert flat1293 is not None
            self.write(flat1293)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1705 = _dollar_dollar.attrs
            else:
                _t1705 = None
            fields1287 = (_dollar_dollar.name, _dollar_dollar.body, _t1705,)
            assert fields1287 is not None
            unwrapped_fields1288 = fields1287
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1289 = unwrapped_fields1288[0]
            self.pretty_relation_id(field1289)
            self.newline()
            field1290 = unwrapped_fields1288[1]
            self.pretty_abstraction(field1290)
            field1291 = unwrapped_fields1288[2]
            if field1291 is not None:
                self.newline()
                assert field1291 is not None
                opt_val1292 = field1291
                self.pretty_attrs(opt_val1292)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1301 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1301 is not None:
            assert flat1301 is not None
            self.write(flat1301)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1706 = _dollar_dollar.attrs
            else:
                _t1706 = None
            fields1294 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1706,)
            assert fields1294 is not None
            unwrapped_fields1295 = fields1294
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1296 = unwrapped_fields1295[0]
            self.pretty_monoid(field1296)
            self.newline()
            field1297 = unwrapped_fields1295[1]
            self.pretty_relation_id(field1297)
            self.newline()
            field1298 = unwrapped_fields1295[2]
            self.pretty_abstraction_with_arity(field1298)
            field1299 = unwrapped_fields1295[3]
            if field1299 is not None:
                self.newline()
                assert field1299 is not None
                opt_val1300 = field1299
                self.pretty_attrs(opt_val1300)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1310 = self._try_flat(msg, self.pretty_monoid)
        if flat1310 is not None:
            assert flat1310 is not None
            self.write(flat1310)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1707 = _dollar_dollar.or_monoid
            else:
                _t1707 = None
            deconstruct_result1308 = _t1707
            if deconstruct_result1308 is not None:
                assert deconstruct_result1308 is not None
                unwrapped1309 = deconstruct_result1308
                self.pretty_or_monoid(unwrapped1309)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1708 = _dollar_dollar.min_monoid
                else:
                    _t1708 = None
                deconstruct_result1306 = _t1708
                if deconstruct_result1306 is not None:
                    assert deconstruct_result1306 is not None
                    unwrapped1307 = deconstruct_result1306
                    self.pretty_min_monoid(unwrapped1307)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1709 = _dollar_dollar.max_monoid
                    else:
                        _t1709 = None
                    deconstruct_result1304 = _t1709
                    if deconstruct_result1304 is not None:
                        assert deconstruct_result1304 is not None
                        unwrapped1305 = deconstruct_result1304
                        self.pretty_max_monoid(unwrapped1305)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1710 = _dollar_dollar.sum_monoid
                        else:
                            _t1710 = None
                        deconstruct_result1302 = _t1710
                        if deconstruct_result1302 is not None:
                            assert deconstruct_result1302 is not None
                            unwrapped1303 = deconstruct_result1302
                            self.pretty_sum_monoid(unwrapped1303)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1311 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1314 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1314 is not None:
            assert flat1314 is not None
            self.write(flat1314)
            return None
        else:
            _dollar_dollar = msg
            fields1312 = _dollar_dollar.type
            assert fields1312 is not None
            unwrapped_fields1313 = fields1312
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1313)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1317 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1317 is not None:
            assert flat1317 is not None
            self.write(flat1317)
            return None
        else:
            _dollar_dollar = msg
            fields1315 = _dollar_dollar.type
            assert fields1315 is not None
            unwrapped_fields1316 = fields1315
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1316)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1320 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1320 is not None:
            assert flat1320 is not None
            self.write(flat1320)
            return None
        else:
            _dollar_dollar = msg
            fields1318 = _dollar_dollar.type
            assert fields1318 is not None
            unwrapped_fields1319 = fields1318
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1319)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1328 = self._try_flat(msg, self.pretty_monus_def)
        if flat1328 is not None:
            assert flat1328 is not None
            self.write(flat1328)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1711 = _dollar_dollar.attrs
            else:
                _t1711 = None
            fields1321 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1711,)
            assert fields1321 is not None
            unwrapped_fields1322 = fields1321
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1323 = unwrapped_fields1322[0]
            self.pretty_monoid(field1323)
            self.newline()
            field1324 = unwrapped_fields1322[1]
            self.pretty_relation_id(field1324)
            self.newline()
            field1325 = unwrapped_fields1322[2]
            self.pretty_abstraction_with_arity(field1325)
            field1326 = unwrapped_fields1322[3]
            if field1326 is not None:
                self.newline()
                assert field1326 is not None
                opt_val1327 = field1326
                self.pretty_attrs(opt_val1327)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1335 = self._try_flat(msg, self.pretty_constraint)
        if flat1335 is not None:
            assert flat1335 is not None
            self.write(flat1335)
            return None
        else:
            _dollar_dollar = msg
            fields1329 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1329 is not None
            unwrapped_fields1330 = fields1329
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1331 = unwrapped_fields1330[0]
            self.pretty_relation_id(field1331)
            self.newline()
            field1332 = unwrapped_fields1330[1]
            self.pretty_abstraction(field1332)
            self.newline()
            field1333 = unwrapped_fields1330[2]
            self.pretty_functional_dependency_keys(field1333)
            self.newline()
            field1334 = unwrapped_fields1330[3]
            self.pretty_functional_dependency_values(field1334)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1339 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1339 is not None:
            assert flat1339 is not None
            self.write(flat1339)
            return None
        else:
            fields1336 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1336) == 0:
                self.newline()
                for i1338, elem1337 in enumerate(fields1336):
                    if (i1338 > 0):
                        self.newline()
                    self.pretty_var(elem1337)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1343 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1343 is not None:
            assert flat1343 is not None
            self.write(flat1343)
            return None
        else:
            fields1340 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1340) == 0:
                self.newline()
                for i1342, elem1341 in enumerate(fields1340):
                    if (i1342 > 0):
                        self.newline()
                    self.pretty_var(elem1341)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1352 = self._try_flat(msg, self.pretty_data)
        if flat1352 is not None:
            assert flat1352 is not None
            self.write(flat1352)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1712 = _dollar_dollar.edb
            else:
                _t1712 = None
            deconstruct_result1350 = _t1712
            if deconstruct_result1350 is not None:
                assert deconstruct_result1350 is not None
                unwrapped1351 = deconstruct_result1350
                self.pretty_edb(unwrapped1351)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1713 = _dollar_dollar.betree_relation
                else:
                    _t1713 = None
                deconstruct_result1348 = _t1713
                if deconstruct_result1348 is not None:
                    assert deconstruct_result1348 is not None
                    unwrapped1349 = deconstruct_result1348
                    self.pretty_betree_relation(unwrapped1349)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1714 = _dollar_dollar.csv_data
                    else:
                        _t1714 = None
                    deconstruct_result1346 = _t1714
                    if deconstruct_result1346 is not None:
                        assert deconstruct_result1346 is not None
                        unwrapped1347 = deconstruct_result1346
                        self.pretty_csv_data(unwrapped1347)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1715 = _dollar_dollar.iceberg_data
                        else:
                            _t1715 = None
                        deconstruct_result1344 = _t1715
                        if deconstruct_result1344 is not None:
                            assert deconstruct_result1344 is not None
                            unwrapped1345 = deconstruct_result1344
                            self.pretty_iceberg_data(unwrapped1345)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1358 = self._try_flat(msg, self.pretty_edb)
        if flat1358 is not None:
            assert flat1358 is not None
            self.write(flat1358)
            return None
        else:
            _dollar_dollar = msg
            fields1353 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1353 is not None
            unwrapped_fields1354 = fields1353
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1355 = unwrapped_fields1354[0]
            self.pretty_relation_id(field1355)
            self.newline()
            field1356 = unwrapped_fields1354[1]
            self.pretty_edb_path(field1356)
            self.newline()
            field1357 = unwrapped_fields1354[2]
            self.pretty_edb_types(field1357)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1362 = self._try_flat(msg, self.pretty_edb_path)
        if flat1362 is not None:
            assert flat1362 is not None
            self.write(flat1362)
            return None
        else:
            fields1359 = msg
            self.write("[")
            self.indent()
            for i1361, elem1360 in enumerate(fields1359):
                if (i1361 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1360))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1366 = self._try_flat(msg, self.pretty_edb_types)
        if flat1366 is not None:
            assert flat1366 is not None
            self.write(flat1366)
            return None
        else:
            fields1363 = msg
            self.write("[")
            self.indent()
            for i1365, elem1364 in enumerate(fields1363):
                if (i1365 > 0):
                    self.newline()
                self.pretty_type(elem1364)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1371 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1371 is not None:
            assert flat1371 is not None
            self.write(flat1371)
            return None
        else:
            _dollar_dollar = msg
            fields1367 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1367 is not None
            unwrapped_fields1368 = fields1367
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1369 = unwrapped_fields1368[0]
            self.pretty_relation_id(field1369)
            self.newline()
            field1370 = unwrapped_fields1368[1]
            self.pretty_betree_info(field1370)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1377 = self._try_flat(msg, self.pretty_betree_info)
        if flat1377 is not None:
            assert flat1377 is not None
            self.write(flat1377)
            return None
        else:
            _dollar_dollar = msg
            _t1716 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1372 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1716,)
            assert fields1372 is not None
            unwrapped_fields1373 = fields1372
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1374 = unwrapped_fields1373[0]
            self.pretty_betree_info_key_types(field1374)
            self.newline()
            field1375 = unwrapped_fields1373[1]
            self.pretty_betree_info_value_types(field1375)
            self.newline()
            field1376 = unwrapped_fields1373[2]
            self.pretty_config_dict(field1376)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1381 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1381 is not None:
            assert flat1381 is not None
            self.write(flat1381)
            return None
        else:
            fields1378 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1378) == 0:
                self.newline()
                for i1380, elem1379 in enumerate(fields1378):
                    if (i1380 > 0):
                        self.newline()
                    self.pretty_type(elem1379)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1385 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1385 is not None:
            assert flat1385 is not None
            self.write(flat1385)
            return None
        else:
            fields1382 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1382) == 0:
                self.newline()
                for i1384, elem1383 in enumerate(fields1382):
                    if (i1384 > 0):
                        self.newline()
                    self.pretty_type(elem1383)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1392 = self._try_flat(msg, self.pretty_csv_data)
        if flat1392 is not None:
            assert flat1392 is not None
            self.write(flat1392)
            return None
        else:
            _dollar_dollar = msg
            fields1386 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1386 is not None
            unwrapped_fields1387 = fields1386
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1388 = unwrapped_fields1387[0]
            self.pretty_csvlocator(field1388)
            self.newline()
            field1389 = unwrapped_fields1387[1]
            self.pretty_csv_config(field1389)
            self.newline()
            field1390 = unwrapped_fields1387[2]
            self.pretty_gnf_columns(field1390)
            self.newline()
            field1391 = unwrapped_fields1387[3]
            self.pretty_csv_asof(field1391)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1399 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1399 is not None:
            assert flat1399 is not None
            self.write(flat1399)
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
            fields1393 = (_t1717, _t1718,)
            assert fields1393 is not None
            unwrapped_fields1394 = fields1393
            self.write("(csv_locator")
            self.indent_sexp()
            field1395 = unwrapped_fields1394[0]
            if field1395 is not None:
                self.newline()
                assert field1395 is not None
                opt_val1396 = field1395
                self.pretty_csv_locator_paths(opt_val1396)
            field1397 = unwrapped_fields1394[1]
            if field1397 is not None:
                self.newline()
                assert field1397 is not None
                opt_val1398 = field1397
                self.pretty_csv_locator_inline_data(opt_val1398)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1403 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1403 is not None:
            assert flat1403 is not None
            self.write(flat1403)
            return None
        else:
            fields1400 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1400) == 0:
                self.newline()
                for i1402, elem1401 in enumerate(fields1400):
                    if (i1402 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1401))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1405 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1405 is not None:
            assert flat1405 is not None
            self.write(flat1405)
            return None
        else:
            fields1404 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1404))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1411 = self._try_flat(msg, self.pretty_csv_config)
        if flat1411 is not None:
            assert flat1411 is not None
            self.write(flat1411)
            return None
        else:
            _dollar_dollar = msg
            _t1719 = self.deconstruct_csv_config(_dollar_dollar)
            _t1720 = self.deconstruct_csv_storage_integration_optional(_dollar_dollar)
            fields1406 = (_t1719, _t1720,)
            assert fields1406 is not None
            unwrapped_fields1407 = fields1406
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            field1408 = unwrapped_fields1407[0]
            self.pretty_config_dict(field1408)
            field1409 = unwrapped_fields1407[1]
            if field1409 is not None:
                self.newline()
                assert field1409 is not None
                opt_val1410 = field1409
                self.pretty_csv_storage_integration(opt_val1410)
            self.dedent()
            self.write(")")

    def pretty_csv_storage_integration(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat1413 = self._try_flat(msg, self.pretty_csv_storage_integration)
        if flat1413 is not None:
            assert flat1413 is not None
            self.write(flat1413)
            return None
        else:
            fields1412 = msg
            self.write("(storage_integration")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(fields1412)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1417 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1417 is not None:
            assert flat1417 is not None
            self.write(flat1417)
            return None
        else:
            fields1414 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1414) == 0:
                self.newline()
                for i1416, elem1415 in enumerate(fields1414):
                    if (i1416 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1415)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1426 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1426 is not None:
            assert flat1426 is not None
            self.write(flat1426)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1721 = _dollar_dollar.target_id
            else:
                _t1721 = None
            fields1418 = (_dollar_dollar.column_path, _t1721, _dollar_dollar.types,)
            assert fields1418 is not None
            unwrapped_fields1419 = fields1418
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1420 = unwrapped_fields1419[0]
            self.pretty_gnf_column_path(field1420)
            field1421 = unwrapped_fields1419[1]
            if field1421 is not None:
                self.newline()
                assert field1421 is not None
                opt_val1422 = field1421
                self.pretty_relation_id(opt_val1422)
            self.newline()
            self.write("[")
            field1423 = unwrapped_fields1419[2]
            for i1425, elem1424 in enumerate(field1423):
                if (i1425 > 0):
                    self.newline()
                self.pretty_type(elem1424)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1433 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1433 is not None:
            assert flat1433 is not None
            self.write(flat1433)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1722 = _dollar_dollar[0]
            else:
                _t1722 = None
            deconstruct_result1431 = _t1722
            if deconstruct_result1431 is not None:
                assert deconstruct_result1431 is not None
                unwrapped1432 = deconstruct_result1431
                self.write(self.format_string_value(unwrapped1432))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1723 = _dollar_dollar
                else:
                    _t1723 = None
                deconstruct_result1427 = _t1723
                if deconstruct_result1427 is not None:
                    assert deconstruct_result1427 is not None
                    unwrapped1428 = deconstruct_result1427
                    self.write("[")
                    self.indent()
                    for i1430, elem1429 in enumerate(unwrapped1428):
                        if (i1430 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1429))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1435 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1435 is not None:
            assert flat1435 is not None
            self.write(flat1435)
            return None
        else:
            fields1434 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1434))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1446 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1446 is not None:
            assert flat1446 is not None
            self.write(flat1446)
            return None
        else:
            _dollar_dollar = msg
            _t1724 = self.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
            _t1725 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1436 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1724, _t1725, _dollar_dollar.returns_delta,)
            assert fields1436 is not None
            unwrapped_fields1437 = fields1436
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1438 = unwrapped_fields1437[0]
            self.pretty_iceberg_locator(field1438)
            self.newline()
            field1439 = unwrapped_fields1437[1]
            self.pretty_iceberg_catalog_config(field1439)
            self.newline()
            field1440 = unwrapped_fields1437[2]
            self.pretty_gnf_columns(field1440)
            field1441 = unwrapped_fields1437[3]
            if field1441 is not None:
                self.newline()
                assert field1441 is not None
                opt_val1442 = field1441
                self.pretty_iceberg_from_snapshot(opt_val1442)
            field1443 = unwrapped_fields1437[4]
            if field1443 is not None:
                self.newline()
                assert field1443 is not None
                opt_val1444 = field1443
                self.pretty_iceberg_to_snapshot(opt_val1444)
            self.newline()
            field1445 = unwrapped_fields1437[5]
            self.pretty_boolean_value(field1445)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1452 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1452 is not None:
            assert flat1452 is not None
            self.write(flat1452)
            return None
        else:
            _dollar_dollar = msg
            fields1447 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1447 is not None
            unwrapped_fields1448 = fields1447
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            field1449 = unwrapped_fields1448[0]
            self.pretty_iceberg_locator_table_name(field1449)
            self.newline()
            field1450 = unwrapped_fields1448[1]
            self.pretty_iceberg_locator_namespace(field1450)
            self.newline()
            field1451 = unwrapped_fields1448[2]
            self.pretty_iceberg_locator_warehouse(field1451)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_table_name(self, msg: str):
        flat1454 = self._try_flat(msg, self.pretty_iceberg_locator_table_name)
        if flat1454 is not None:
            assert flat1454 is not None
            self.write(flat1454)
            return None
        else:
            fields1453 = msg
            self.write("(table_name")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1453))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_namespace(self, msg: Sequence[str]):
        flat1458 = self._try_flat(msg, self.pretty_iceberg_locator_namespace)
        if flat1458 is not None:
            assert flat1458 is not None
            self.write(flat1458)
            return None
        else:
            fields1455 = msg
            self.write("(namespace")
            self.indent_sexp()
            if not len(fields1455) == 0:
                self.newline()
                for i1457, elem1456 in enumerate(fields1455):
                    if (i1457 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1456))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_warehouse(self, msg: str):
        flat1460 = self._try_flat(msg, self.pretty_iceberg_locator_warehouse)
        if flat1460 is not None:
            assert flat1460 is not None
            self.write(flat1460)
            return None
        else:
            fields1459 = msg
            self.write("(warehouse")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1459))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1468 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1468 is not None:
            assert flat1468 is not None
            self.write(flat1468)
            return None
        else:
            _dollar_dollar = msg
            _t1726 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1461 = (_dollar_dollar.catalog_uri, _t1726, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1461 is not None
            unwrapped_fields1462 = fields1461
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            field1463 = unwrapped_fields1462[0]
            self.pretty_iceberg_catalog_uri(field1463)
            field1464 = unwrapped_fields1462[1]
            if field1464 is not None:
                self.newline()
                assert field1464 is not None
                opt_val1465 = field1464
                self.pretty_iceberg_catalog_config_scope(opt_val1465)
            self.newline()
            field1466 = unwrapped_fields1462[2]
            self.pretty_iceberg_properties(field1466)
            self.newline()
            field1467 = unwrapped_fields1462[3]
            self.pretty_iceberg_auth_properties(field1467)
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_uri(self, msg: str):
        flat1470 = self._try_flat(msg, self.pretty_iceberg_catalog_uri)
        if flat1470 is not None:
            assert flat1470 is not None
            self.write(flat1470)
            return None
        else:
            fields1469 = msg
            self.write("(catalog_uri")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1469))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1472 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1472 is not None:
            assert flat1472 is not None
            self.write(flat1472)
            return None
        else:
            fields1471 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1471))
            self.dedent()
            self.write(")")

    def pretty_iceberg_properties(self, msg: Sequence[tuple[str, str]]):
        flat1476 = self._try_flat(msg, self.pretty_iceberg_properties)
        if flat1476 is not None:
            assert flat1476 is not None
            self.write(flat1476)
            return None
        else:
            fields1473 = msg
            self.write("(properties")
            self.indent_sexp()
            if not len(fields1473) == 0:
                self.newline()
                for i1475, elem1474 in enumerate(fields1473):
                    if (i1475 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1474)
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1481 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1481 is not None:
            assert flat1481 is not None
            self.write(flat1481)
            return None
        else:
            _dollar_dollar = msg
            fields1477 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1477 is not None
            unwrapped_fields1478 = fields1477
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1479 = unwrapped_fields1478[0]
            self.write(self.format_string_value(field1479))
            self.newline()
            field1480 = unwrapped_fields1478[1]
            self.write(self.format_string_value(field1480))
            self.dedent()
            self.write(")")

    def pretty_iceberg_auth_properties(self, msg: Sequence[tuple[str, str]]):
        flat1485 = self._try_flat(msg, self.pretty_iceberg_auth_properties)
        if flat1485 is not None:
            assert flat1485 is not None
            self.write(flat1485)
            return None
        else:
            fields1482 = msg
            self.write("(auth_properties")
            self.indent_sexp()
            if not len(fields1482) == 0:
                self.newline()
                for i1484, elem1483 in enumerate(fields1482):
                    if (i1484 > 0):
                        self.newline()
                    self.pretty_iceberg_masked_property_entry(elem1483)
            self.dedent()
            self.write(")")

    def pretty_iceberg_masked_property_entry(self, msg: tuple[str, str]):
        flat1490 = self._try_flat(msg, self.pretty_iceberg_masked_property_entry)
        if flat1490 is not None:
            assert flat1490 is not None
            self.write(flat1490)
            return None
        else:
            _dollar_dollar = msg
            _t1727 = self.mask_secret_value(_dollar_dollar)
            fields1486 = (_dollar_dollar[0], _t1727,)
            assert fields1486 is not None
            unwrapped_fields1487 = fields1486
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1488 = unwrapped_fields1487[0]
            self.write(self.format_string_value(field1488))
            self.newline()
            field1489 = unwrapped_fields1487[1]
            self.write(self.format_string_value(field1489))
            self.dedent()
            self.write(")")

    def pretty_iceberg_from_snapshot(self, msg: str):
        flat1492 = self._try_flat(msg, self.pretty_iceberg_from_snapshot)
        if flat1492 is not None:
            assert flat1492 is not None
            self.write(flat1492)
            return None
        else:
            fields1491 = msg
            self.write("(from_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1491))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1494 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1494 is not None:
            assert flat1494 is not None
            self.write(flat1494)
            return None
        else:
            fields1493 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1493))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1497 = self._try_flat(msg, self.pretty_undefine)
        if flat1497 is not None:
            assert flat1497 is not None
            self.write(flat1497)
            return None
        else:
            _dollar_dollar = msg
            fields1495 = _dollar_dollar.fragment_id
            assert fields1495 is not None
            unwrapped_fields1496 = fields1495
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1496)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1502 = self._try_flat(msg, self.pretty_context)
        if flat1502 is not None:
            assert flat1502 is not None
            self.write(flat1502)
            return None
        else:
            _dollar_dollar = msg
            fields1498 = _dollar_dollar.relations
            assert fields1498 is not None
            unwrapped_fields1499 = fields1498
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1499) == 0:
                self.newline()
                for i1501, elem1500 in enumerate(unwrapped_fields1499):
                    if (i1501 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1500)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1509 = self._try_flat(msg, self.pretty_snapshot)
        if flat1509 is not None:
            assert flat1509 is not None
            self.write(flat1509)
            return None
        else:
            _dollar_dollar = msg
            fields1503 = (_dollar_dollar.prefix, _dollar_dollar.mappings,)
            assert fields1503 is not None
            unwrapped_fields1504 = fields1503
            self.write("(snapshot")
            self.indent_sexp()
            self.newline()
            field1505 = unwrapped_fields1504[0]
            self.pretty_edb_path(field1505)
            field1506 = unwrapped_fields1504[1]
            if not len(field1506) == 0:
                self.newline()
                for i1508, elem1507 in enumerate(field1506):
                    if (i1508 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1507)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1514 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1514 is not None:
            assert flat1514 is not None
            self.write(flat1514)
            return None
        else:
            _dollar_dollar = msg
            fields1510 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1510 is not None
            unwrapped_fields1511 = fields1510
            field1512 = unwrapped_fields1511[0]
            self.pretty_edb_path(field1512)
            self.write(" ")
            field1513 = unwrapped_fields1511[1]
            self.pretty_relation_id(field1513)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1518 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1518 is not None:
            assert flat1518 is not None
            self.write(flat1518)
            return None
        else:
            fields1515 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1515) == 0:
                self.newline()
                for i1517, elem1516 in enumerate(fields1515):
                    if (i1517 > 0):
                        self.newline()
                    self.pretty_read(elem1516)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1529 = self._try_flat(msg, self.pretty_read)
        if flat1529 is not None:
            assert flat1529 is not None
            self.write(flat1529)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1728 = _dollar_dollar.demand
            else:
                _t1728 = None
            deconstruct_result1527 = _t1728
            if deconstruct_result1527 is not None:
                assert deconstruct_result1527 is not None
                unwrapped1528 = deconstruct_result1527
                self.pretty_demand(unwrapped1528)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1729 = _dollar_dollar.output
                else:
                    _t1729 = None
                deconstruct_result1525 = _t1729
                if deconstruct_result1525 is not None:
                    assert deconstruct_result1525 is not None
                    unwrapped1526 = deconstruct_result1525
                    self.pretty_output(unwrapped1526)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1730 = _dollar_dollar.what_if
                    else:
                        _t1730 = None
                    deconstruct_result1523 = _t1730
                    if deconstruct_result1523 is not None:
                        assert deconstruct_result1523 is not None
                        unwrapped1524 = deconstruct_result1523
                        self.pretty_what_if(unwrapped1524)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1731 = _dollar_dollar.abort
                        else:
                            _t1731 = None
                        deconstruct_result1521 = _t1731
                        if deconstruct_result1521 is not None:
                            assert deconstruct_result1521 is not None
                            unwrapped1522 = deconstruct_result1521
                            self.pretty_abort(unwrapped1522)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1732 = _dollar_dollar.export
                            else:
                                _t1732 = None
                            deconstruct_result1519 = _t1732
                            if deconstruct_result1519 is not None:
                                assert deconstruct_result1519 is not None
                                unwrapped1520 = deconstruct_result1519
                                self.pretty_export(unwrapped1520)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1532 = self._try_flat(msg, self.pretty_demand)
        if flat1532 is not None:
            assert flat1532 is not None
            self.write(flat1532)
            return None
        else:
            _dollar_dollar = msg
            fields1530 = _dollar_dollar.relation_id
            assert fields1530 is not None
            unwrapped_fields1531 = fields1530
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1531)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1537 = self._try_flat(msg, self.pretty_output)
        if flat1537 is not None:
            assert flat1537 is not None
            self.write(flat1537)
            return None
        else:
            _dollar_dollar = msg
            fields1533 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1533 is not None
            unwrapped_fields1534 = fields1533
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1535 = unwrapped_fields1534[0]
            self.pretty_name(field1535)
            self.newline()
            field1536 = unwrapped_fields1534[1]
            self.pretty_relation_id(field1536)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1542 = self._try_flat(msg, self.pretty_what_if)
        if flat1542 is not None:
            assert flat1542 is not None
            self.write(flat1542)
            return None
        else:
            _dollar_dollar = msg
            fields1538 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1538 is not None
            unwrapped_fields1539 = fields1538
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1540 = unwrapped_fields1539[0]
            self.pretty_name(field1540)
            self.newline()
            field1541 = unwrapped_fields1539[1]
            self.pretty_epoch(field1541)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1548 = self._try_flat(msg, self.pretty_abort)
        if flat1548 is not None:
            assert flat1548 is not None
            self.write(flat1548)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1733 = _dollar_dollar.name
            else:
                _t1733 = None
            fields1543 = (_t1733, _dollar_dollar.relation_id,)
            assert fields1543 is not None
            unwrapped_fields1544 = fields1543
            self.write("(abort")
            self.indent_sexp()
            field1545 = unwrapped_fields1544[0]
            if field1545 is not None:
                self.newline()
                assert field1545 is not None
                opt_val1546 = field1545
                self.pretty_name(opt_val1546)
            self.newline()
            field1547 = unwrapped_fields1544[1]
            self.pretty_relation_id(field1547)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1553 = self._try_flat(msg, self.pretty_export)
        if flat1553 is not None:
            assert flat1553 is not None
            self.write(flat1553)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1734 = _dollar_dollar.csv_config
            else:
                _t1734 = None
            deconstruct_result1551 = _t1734
            if deconstruct_result1551 is not None:
                assert deconstruct_result1551 is not None
                unwrapped1552 = deconstruct_result1551
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1552)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1735 = _dollar_dollar.iceberg_config
                else:
                    _t1735 = None
                deconstruct_result1549 = _t1735
                if deconstruct_result1549 is not None:
                    assert deconstruct_result1549 is not None
                    unwrapped1550 = deconstruct_result1549
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1550)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1564 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1564 is not None:
            assert flat1564 is not None
            self.write(flat1564)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1736 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1736 = None
            deconstruct_result1559 = _t1736
            if deconstruct_result1559 is not None:
                assert deconstruct_result1559 is not None
                unwrapped1560 = deconstruct_result1559
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1561 = unwrapped1560[0]
                self.pretty_export_csv_path(field1561)
                self.newline()
                field1562 = unwrapped1560[1]
                self.pretty_export_csv_source(field1562)
                self.newline()
                field1563 = unwrapped1560[2]
                self.pretty_csv_config(field1563)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1738 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1737 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1738,)
                else:
                    _t1737 = None
                deconstruct_result1554 = _t1737
                if deconstruct_result1554 is not None:
                    assert deconstruct_result1554 is not None
                    unwrapped1555 = deconstruct_result1554
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1556 = unwrapped1555[0]
                    self.pretty_export_csv_path(field1556)
                    self.newline()
                    field1557 = unwrapped1555[1]
                    self.pretty_export_csv_columns_list(field1557)
                    self.newline()
                    field1558 = unwrapped1555[2]
                    self.pretty_config_dict(field1558)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1566 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1566 is not None:
            assert flat1566 is not None
            self.write(flat1566)
            return None
        else:
            fields1565 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1565))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1573 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1573 is not None:
            assert flat1573 is not None
            self.write(flat1573)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1739 = _dollar_dollar.gnf_columns.columns
            else:
                _t1739 = None
            deconstruct_result1569 = _t1739
            if deconstruct_result1569 is not None:
                assert deconstruct_result1569 is not None
                unwrapped1570 = deconstruct_result1569
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1570) == 0:
                    self.newline()
                    for i1572, elem1571 in enumerate(unwrapped1570):
                        if (i1572 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1571)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1740 = _dollar_dollar.table_def
                else:
                    _t1740 = None
                deconstruct_result1567 = _t1740
                if deconstruct_result1567 is not None:
                    assert deconstruct_result1567 is not None
                    unwrapped1568 = deconstruct_result1567
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1568)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1578 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1578 is not None:
            assert flat1578 is not None
            self.write(flat1578)
            return None
        else:
            _dollar_dollar = msg
            fields1574 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1574 is not None
            unwrapped_fields1575 = fields1574
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1576 = unwrapped_fields1575[0]
            self.write(self.format_string_value(field1576))
            self.newline()
            field1577 = unwrapped_fields1575[1]
            self.pretty_relation_id(field1577)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1582 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1582 is not None:
            assert flat1582 is not None
            self.write(flat1582)
            return None
        else:
            fields1579 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1579) == 0:
                self.newline()
                for i1581, elem1580 in enumerate(fields1579):
                    if (i1581 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1580)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1591 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1591 is not None:
            assert flat1591 is not None
            self.write(flat1591)
            return None
        else:
            _dollar_dollar = msg
            _t1741 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1583 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, sorted(_dollar_dollar.table_properties.items()), _t1741,)
            assert fields1583 is not None
            unwrapped_fields1584 = fields1583
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1585 = unwrapped_fields1584[0]
            self.pretty_iceberg_locator(field1585)
            self.newline()
            field1586 = unwrapped_fields1584[1]
            self.pretty_iceberg_catalog_config(field1586)
            self.newline()
            field1587 = unwrapped_fields1584[2]
            self.pretty_export_iceberg_table_def(field1587)
            self.newline()
            field1588 = unwrapped_fields1584[3]
            self.pretty_iceberg_table_properties(field1588)
            field1589 = unwrapped_fields1584[4]
            if field1589 is not None:
                self.newline()
                assert field1589 is not None
                opt_val1590 = field1589
                self.pretty_config_dict(opt_val1590)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_table_def(self, msg: logic_pb2.RelationId):
        flat1593 = self._try_flat(msg, self.pretty_export_iceberg_table_def)
        if flat1593 is not None:
            assert flat1593 is not None
            self.write(flat1593)
            return None
        else:
            fields1592 = msg
            self.write("(table_def")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(fields1592)
            self.dedent()
            self.write(")")

    def pretty_iceberg_table_properties(self, msg: Sequence[tuple[str, str]]):
        flat1597 = self._try_flat(msg, self.pretty_iceberg_table_properties)
        if flat1597 is not None:
            assert flat1597 is not None
            self.write(flat1597)
            return None
        else:
            fields1594 = msg
            self.write("(table_properties")
            self.indent_sexp()
            if not len(fields1594) == 0:
                self.newline()
                for i1596, elem1595 in enumerate(fields1594):
                    if (i1596 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1595)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1793 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1793)
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

    def pretty_csv_storage_integration(self, msg: logic_pb2.CSVStorageIntegration):
        self.write("(csv_storage_integration")
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
        elif isinstance(msg, fragments_pb2.DebugInfo):
            self.pretty_debug_info(msg)
        elif isinstance(msg, logic_pb2.BeTreeConfig):
            self.pretty_be_tree_config(msg)
        elif isinstance(msg, logic_pb2.BeTreeLocator):
            self.pretty_be_tree_locator(msg)
        elif isinstance(msg, logic_pb2.CSVStorageIntegration):
            self.pretty_csv_storage_integration(msg)
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
