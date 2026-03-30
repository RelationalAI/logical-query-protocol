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
        _t1701 = logic_pb2.Value(int32_value=v)
        return _t1701

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1702 = logic_pb2.Value(int_value=v)
        return _t1702

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1703 = logic_pb2.Value(float_value=v)
        return _t1703

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1704 = logic_pb2.Value(string_value=v)
        return _t1704

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1705 = logic_pb2.Value(boolean_value=v)
        return _t1705

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1706 = logic_pb2.Value(uint128_value=v)
        return _t1706

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1707 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1707,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1708 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1708,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1709 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1709,))
        _t1710 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1710,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1711 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1711,))
        _t1712 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1712,))
        if msg.new_line != "":
            _t1713 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1713,))
        _t1714 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1714,))
        _t1715 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1715,))
        _t1716 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1716,))
        if msg.comment != "":
            _t1717 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1717,))
        for missing_string in msg.missing_strings:
            _t1718 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1718,))
        _t1719 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1719,))
        _t1720 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1720,))
        _t1721 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1721,))
        if msg.partition_size_mb != 0:
            _t1722 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1722,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1723 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1723,))
        _t1724 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1724,))
        _t1725 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1725,))
        _t1726 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1726,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1727 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1727,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1728 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1728,))
        _t1729 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1729,))
        _t1730 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1730,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1731 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1731,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1732 = self._make_value_string(msg.compression)
            result.append(("compression", _t1732,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1733 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1733,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1734 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1734,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1735 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1735,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1736 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1736,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1737 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1737,))
        return sorted(result)

    def mask_secret_value(self, pair: tuple[str, str]) -> str:
        return "***"

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1738 = None
        return None

    def deconstruct_iceberg_locator_from_snapshot_optional(self, msg: logic_pb2.IcebergLocator) -> str | None:
        assert msg.from_snapshot is not None
        if msg.from_snapshot != "":
            assert msg.from_snapshot is not None
            return msg.from_snapshot
        else:
            _t1739 = None
        return None

    def deconstruct_iceberg_locator_to_snapshot_optional(self, msg: logic_pb2.IcebergLocator) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1740 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1741 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1741,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1742 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1742,))
        if msg.compression != "":
            _t1743 = self._make_value_string(msg.compression)
            result.append(("compression", _t1743,))
        if len(result) == 0:
            return None
        else:
            _t1744 = None
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
            _t1745 = None
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
        flat789 = self._try_flat(msg, self.pretty_transaction)
        if flat789 is not None:
            assert flat789 is not None
            self.write(flat789)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1560 = _dollar_dollar.configure
            else:
                _t1560 = None
            if _dollar_dollar.HasField("sync"):
                _t1561 = _dollar_dollar.sync
            else:
                _t1561 = None
            fields780 = (_t1560, _t1561, _dollar_dollar.epochs,)
            assert fields780 is not None
            unwrapped_fields781 = fields780
            self.write("(transaction")
            self.indent_sexp()
            field782 = unwrapped_fields781[0]
            if field782 is not None:
                self.newline()
                assert field782 is not None
                opt_val783 = field782
                self.pretty_configure(opt_val783)
            field784 = unwrapped_fields781[1]
            if field784 is not None:
                self.newline()
                assert field784 is not None
                opt_val785 = field784
                self.pretty_sync(opt_val785)
            field786 = unwrapped_fields781[2]
            if not len(field786) == 0:
                self.newline()
                for i788, elem787 in enumerate(field786):
                    if (i788 > 0):
                        self.newline()
                    self.pretty_epoch(elem787)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat792 = self._try_flat(msg, self.pretty_configure)
        if flat792 is not None:
            assert flat792 is not None
            self.write(flat792)
            return None
        else:
            _dollar_dollar = msg
            _t1562 = self.deconstruct_configure(_dollar_dollar)
            fields790 = _t1562
            assert fields790 is not None
            unwrapped_fields791 = fields790
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields791)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat796 = self._try_flat(msg, self.pretty_config_dict)
        if flat796 is not None:
            assert flat796 is not None
            self.write(flat796)
            return None
        else:
            fields793 = msg
            self.write("{")
            self.indent()
            if not len(fields793) == 0:
                self.newline()
                for i795, elem794 in enumerate(fields793):
                    if (i795 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem794)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat801 = self._try_flat(msg, self.pretty_config_key_value)
        if flat801 is not None:
            assert flat801 is not None
            self.write(flat801)
            return None
        else:
            _dollar_dollar = msg
            fields797 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields797 is not None
            unwrapped_fields798 = fields797
            self.write(":")
            field799 = unwrapped_fields798[0]
            self.write(field799)
            self.write(" ")
            field800 = unwrapped_fields798[1]
            self.pretty_raw_value(field800)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat827 = self._try_flat(msg, self.pretty_raw_value)
        if flat827 is not None:
            assert flat827 is not None
            self.write(flat827)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1563 = _dollar_dollar.date_value
            else:
                _t1563 = None
            deconstruct_result825 = _t1563
            if deconstruct_result825 is not None:
                assert deconstruct_result825 is not None
                unwrapped826 = deconstruct_result825
                self.pretty_raw_date(unwrapped826)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1564 = _dollar_dollar.datetime_value
                else:
                    _t1564 = None
                deconstruct_result823 = _t1564
                if deconstruct_result823 is not None:
                    assert deconstruct_result823 is not None
                    unwrapped824 = deconstruct_result823
                    self.pretty_raw_datetime(unwrapped824)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1565 = _dollar_dollar.string_value
                    else:
                        _t1565 = None
                    deconstruct_result821 = _t1565
                    if deconstruct_result821 is not None:
                        assert deconstruct_result821 is not None
                        unwrapped822 = deconstruct_result821
                        self.write(self.format_string_value(unwrapped822))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1566 = _dollar_dollar.int32_value
                        else:
                            _t1566 = None
                        deconstruct_result819 = _t1566
                        if deconstruct_result819 is not None:
                            assert deconstruct_result819 is not None
                            unwrapped820 = deconstruct_result819
                            self.write((str(unwrapped820) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1567 = _dollar_dollar.int_value
                            else:
                                _t1567 = None
                            deconstruct_result817 = _t1567
                            if deconstruct_result817 is not None:
                                assert deconstruct_result817 is not None
                                unwrapped818 = deconstruct_result817
                                self.write(str(unwrapped818))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1568 = _dollar_dollar.float32_value
                                else:
                                    _t1568 = None
                                deconstruct_result815 = _t1568
                                if deconstruct_result815 is not None:
                                    assert deconstruct_result815 is not None
                                    unwrapped816 = deconstruct_result815
                                    self.write(self.format_float32_literal(unwrapped816))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1569 = _dollar_dollar.float_value
                                    else:
                                        _t1569 = None
                                    deconstruct_result813 = _t1569
                                    if deconstruct_result813 is not None:
                                        assert deconstruct_result813 is not None
                                        unwrapped814 = deconstruct_result813
                                        self.write(str(unwrapped814))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1570 = _dollar_dollar.uint32_value
                                        else:
                                            _t1570 = None
                                        deconstruct_result811 = _t1570
                                        if deconstruct_result811 is not None:
                                            assert deconstruct_result811 is not None
                                            unwrapped812 = deconstruct_result811
                                            self.write((str(unwrapped812) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1571 = _dollar_dollar.uint128_value
                                            else:
                                                _t1571 = None
                                            deconstruct_result809 = _t1571
                                            if deconstruct_result809 is not None:
                                                assert deconstruct_result809 is not None
                                                unwrapped810 = deconstruct_result809
                                                self.write(self.format_uint128(unwrapped810))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1572 = _dollar_dollar.int128_value
                                                else:
                                                    _t1572 = None
                                                deconstruct_result807 = _t1572
                                                if deconstruct_result807 is not None:
                                                    assert deconstruct_result807 is not None
                                                    unwrapped808 = deconstruct_result807
                                                    self.write(self.format_int128(unwrapped808))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1573 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1573 = None
                                                    deconstruct_result805 = _t1573
                                                    if deconstruct_result805 is not None:
                                                        assert deconstruct_result805 is not None
                                                        unwrapped806 = deconstruct_result805
                                                        self.write(self.format_decimal(unwrapped806))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1574 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1574 = None
                                                        deconstruct_result803 = _t1574
                                                        if deconstruct_result803 is not None:
                                                            assert deconstruct_result803 is not None
                                                            unwrapped804 = deconstruct_result803
                                                            self.pretty_boolean_value(unwrapped804)
                                                        else:
                                                            fields802 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat833 = self._try_flat(msg, self.pretty_raw_date)
        if flat833 is not None:
            assert flat833 is not None
            self.write(flat833)
            return None
        else:
            _dollar_dollar = msg
            fields828 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields828 is not None
            unwrapped_fields829 = fields828
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field830 = unwrapped_fields829[0]
            self.write(str(field830))
            self.newline()
            field831 = unwrapped_fields829[1]
            self.write(str(field831))
            self.newline()
            field832 = unwrapped_fields829[2]
            self.write(str(field832))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat844 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat844 is not None:
            assert flat844 is not None
            self.write(flat844)
            return None
        else:
            _dollar_dollar = msg
            fields834 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields834 is not None
            unwrapped_fields835 = fields834
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field836 = unwrapped_fields835[0]
            self.write(str(field836))
            self.newline()
            field837 = unwrapped_fields835[1]
            self.write(str(field837))
            self.newline()
            field838 = unwrapped_fields835[2]
            self.write(str(field838))
            self.newline()
            field839 = unwrapped_fields835[3]
            self.write(str(field839))
            self.newline()
            field840 = unwrapped_fields835[4]
            self.write(str(field840))
            self.newline()
            field841 = unwrapped_fields835[5]
            self.write(str(field841))
            field842 = unwrapped_fields835[6]
            if field842 is not None:
                self.newline()
                assert field842 is not None
                opt_val843 = field842
                self.write(str(opt_val843))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1575 = ()
        else:
            _t1575 = None
        deconstruct_result847 = _t1575
        if deconstruct_result847 is not None:
            assert deconstruct_result847 is not None
            unwrapped848 = deconstruct_result847
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1576 = ()
            else:
                _t1576 = None
            deconstruct_result845 = _t1576
            if deconstruct_result845 is not None:
                assert deconstruct_result845 is not None
                unwrapped846 = deconstruct_result845
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat853 = self._try_flat(msg, self.pretty_sync)
        if flat853 is not None:
            assert flat853 is not None
            self.write(flat853)
            return None
        else:
            _dollar_dollar = msg
            fields849 = _dollar_dollar.fragments
            assert fields849 is not None
            unwrapped_fields850 = fields849
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields850) == 0:
                self.newline()
                for i852, elem851 in enumerate(unwrapped_fields850):
                    if (i852 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem851)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat856 = self._try_flat(msg, self.pretty_fragment_id)
        if flat856 is not None:
            assert flat856 is not None
            self.write(flat856)
            return None
        else:
            _dollar_dollar = msg
            fields854 = self.fragment_id_to_string(_dollar_dollar)
            assert fields854 is not None
            unwrapped_fields855 = fields854
            self.write(":")
            self.write(unwrapped_fields855)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat863 = self._try_flat(msg, self.pretty_epoch)
        if flat863 is not None:
            assert flat863 is not None
            self.write(flat863)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1577 = _dollar_dollar.writes
            else:
                _t1577 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1578 = _dollar_dollar.reads
            else:
                _t1578 = None
            fields857 = (_t1577, _t1578,)
            assert fields857 is not None
            unwrapped_fields858 = fields857
            self.write("(epoch")
            self.indent_sexp()
            field859 = unwrapped_fields858[0]
            if field859 is not None:
                self.newline()
                assert field859 is not None
                opt_val860 = field859
                self.pretty_epoch_writes(opt_val860)
            field861 = unwrapped_fields858[1]
            if field861 is not None:
                self.newline()
                assert field861 is not None
                opt_val862 = field861
                self.pretty_epoch_reads(opt_val862)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat867 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat867 is not None:
            assert flat867 is not None
            self.write(flat867)
            return None
        else:
            fields864 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields864) == 0:
                self.newline()
                for i866, elem865 in enumerate(fields864):
                    if (i866 > 0):
                        self.newline()
                    self.pretty_write(elem865)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat876 = self._try_flat(msg, self.pretty_write)
        if flat876 is not None:
            assert flat876 is not None
            self.write(flat876)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1579 = _dollar_dollar.define
            else:
                _t1579 = None
            deconstruct_result874 = _t1579
            if deconstruct_result874 is not None:
                assert deconstruct_result874 is not None
                unwrapped875 = deconstruct_result874
                self.pretty_define(unwrapped875)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1580 = _dollar_dollar.undefine
                else:
                    _t1580 = None
                deconstruct_result872 = _t1580
                if deconstruct_result872 is not None:
                    assert deconstruct_result872 is not None
                    unwrapped873 = deconstruct_result872
                    self.pretty_undefine(unwrapped873)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1581 = _dollar_dollar.context
                    else:
                        _t1581 = None
                    deconstruct_result870 = _t1581
                    if deconstruct_result870 is not None:
                        assert deconstruct_result870 is not None
                        unwrapped871 = deconstruct_result870
                        self.pretty_context(unwrapped871)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1582 = _dollar_dollar.snapshot
                        else:
                            _t1582 = None
                        deconstruct_result868 = _t1582
                        if deconstruct_result868 is not None:
                            assert deconstruct_result868 is not None
                            unwrapped869 = deconstruct_result868
                            self.pretty_snapshot(unwrapped869)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat879 = self._try_flat(msg, self.pretty_define)
        if flat879 is not None:
            assert flat879 is not None
            self.write(flat879)
            return None
        else:
            _dollar_dollar = msg
            fields877 = _dollar_dollar.fragment
            assert fields877 is not None
            unwrapped_fields878 = fields877
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields878)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat886 = self._try_flat(msg, self.pretty_fragment)
        if flat886 is not None:
            assert flat886 is not None
            self.write(flat886)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields880 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields880 is not None
            unwrapped_fields881 = fields880
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field882 = unwrapped_fields881[0]
            self.pretty_new_fragment_id(field882)
            field883 = unwrapped_fields881[1]
            if not len(field883) == 0:
                self.newline()
                for i885, elem884 in enumerate(field883):
                    if (i885 > 0):
                        self.newline()
                    self.pretty_declaration(elem884)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat888 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat888 is not None:
            assert flat888 is not None
            self.write(flat888)
            return None
        else:
            fields887 = msg
            self.pretty_fragment_id(fields887)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat897 = self._try_flat(msg, self.pretty_declaration)
        if flat897 is not None:
            assert flat897 is not None
            self.write(flat897)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1583 = getattr(_dollar_dollar, 'def')
            else:
                _t1583 = None
            deconstruct_result895 = _t1583
            if deconstruct_result895 is not None:
                assert deconstruct_result895 is not None
                unwrapped896 = deconstruct_result895
                self.pretty_def(unwrapped896)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1584 = _dollar_dollar.algorithm
                else:
                    _t1584 = None
                deconstruct_result893 = _t1584
                if deconstruct_result893 is not None:
                    assert deconstruct_result893 is not None
                    unwrapped894 = deconstruct_result893
                    self.pretty_algorithm(unwrapped894)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1585 = _dollar_dollar.constraint
                    else:
                        _t1585 = None
                    deconstruct_result891 = _t1585
                    if deconstruct_result891 is not None:
                        assert deconstruct_result891 is not None
                        unwrapped892 = deconstruct_result891
                        self.pretty_constraint(unwrapped892)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1586 = _dollar_dollar.data
                        else:
                            _t1586 = None
                        deconstruct_result889 = _t1586
                        if deconstruct_result889 is not None:
                            assert deconstruct_result889 is not None
                            unwrapped890 = deconstruct_result889
                            self.pretty_data(unwrapped890)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat904 = self._try_flat(msg, self.pretty_def)
        if flat904 is not None:
            assert flat904 is not None
            self.write(flat904)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1587 = _dollar_dollar.attrs
            else:
                _t1587 = None
            fields898 = (_dollar_dollar.name, _dollar_dollar.body, _t1587,)
            assert fields898 is not None
            unwrapped_fields899 = fields898
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field900 = unwrapped_fields899[0]
            self.pretty_relation_id(field900)
            self.newline()
            field901 = unwrapped_fields899[1]
            self.pretty_abstraction(field901)
            field902 = unwrapped_fields899[2]
            if field902 is not None:
                self.newline()
                assert field902 is not None
                opt_val903 = field902
                self.pretty_attrs(opt_val903)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat909 = self._try_flat(msg, self.pretty_relation_id)
        if flat909 is not None:
            assert flat909 is not None
            self.write(flat909)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1589 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1588 = _t1589
            else:
                _t1588 = None
            deconstruct_result907 = _t1588
            if deconstruct_result907 is not None:
                assert deconstruct_result907 is not None
                unwrapped908 = deconstruct_result907
                self.write(":")
                self.write(unwrapped908)
            else:
                _dollar_dollar = msg
                _t1590 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result905 = _t1590
                if deconstruct_result905 is not None:
                    assert deconstruct_result905 is not None
                    unwrapped906 = deconstruct_result905
                    self.write(self.format_uint128(unwrapped906))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat914 = self._try_flat(msg, self.pretty_abstraction)
        if flat914 is not None:
            assert flat914 is not None
            self.write(flat914)
            return None
        else:
            _dollar_dollar = msg
            _t1591 = self.deconstruct_bindings(_dollar_dollar)
            fields910 = (_t1591, _dollar_dollar.value,)
            assert fields910 is not None
            unwrapped_fields911 = fields910
            self.write("(")
            self.indent()
            field912 = unwrapped_fields911[0]
            self.pretty_bindings(field912)
            self.newline()
            field913 = unwrapped_fields911[1]
            self.pretty_formula(field913)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat922 = self._try_flat(msg, self.pretty_bindings)
        if flat922 is not None:
            assert flat922 is not None
            self.write(flat922)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1592 = _dollar_dollar[1]
            else:
                _t1592 = None
            fields915 = (_dollar_dollar[0], _t1592,)
            assert fields915 is not None
            unwrapped_fields916 = fields915
            self.write("[")
            self.indent()
            field917 = unwrapped_fields916[0]
            for i919, elem918 in enumerate(field917):
                if (i919 > 0):
                    self.newline()
                self.pretty_binding(elem918)
            field920 = unwrapped_fields916[1]
            if field920 is not None:
                self.newline()
                assert field920 is not None
                opt_val921 = field920
                self.pretty_value_bindings(opt_val921)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat927 = self._try_flat(msg, self.pretty_binding)
        if flat927 is not None:
            assert flat927 is not None
            self.write(flat927)
            return None
        else:
            _dollar_dollar = msg
            fields923 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields923 is not None
            unwrapped_fields924 = fields923
            field925 = unwrapped_fields924[0]
            self.write(field925)
            self.write("::")
            field926 = unwrapped_fields924[1]
            self.pretty_type(field926)

    def pretty_type(self, msg: logic_pb2.Type):
        flat956 = self._try_flat(msg, self.pretty_type)
        if flat956 is not None:
            assert flat956 is not None
            self.write(flat956)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1593 = _dollar_dollar.unspecified_type
            else:
                _t1593 = None
            deconstruct_result954 = _t1593
            if deconstruct_result954 is not None:
                assert deconstruct_result954 is not None
                unwrapped955 = deconstruct_result954
                self.pretty_unspecified_type(unwrapped955)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1594 = _dollar_dollar.string_type
                else:
                    _t1594 = None
                deconstruct_result952 = _t1594
                if deconstruct_result952 is not None:
                    assert deconstruct_result952 is not None
                    unwrapped953 = deconstruct_result952
                    self.pretty_string_type(unwrapped953)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1595 = _dollar_dollar.int_type
                    else:
                        _t1595 = None
                    deconstruct_result950 = _t1595
                    if deconstruct_result950 is not None:
                        assert deconstruct_result950 is not None
                        unwrapped951 = deconstruct_result950
                        self.pretty_int_type(unwrapped951)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1596 = _dollar_dollar.float_type
                        else:
                            _t1596 = None
                        deconstruct_result948 = _t1596
                        if deconstruct_result948 is not None:
                            assert deconstruct_result948 is not None
                            unwrapped949 = deconstruct_result948
                            self.pretty_float_type(unwrapped949)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1597 = _dollar_dollar.uint128_type
                            else:
                                _t1597 = None
                            deconstruct_result946 = _t1597
                            if deconstruct_result946 is not None:
                                assert deconstruct_result946 is not None
                                unwrapped947 = deconstruct_result946
                                self.pretty_uint128_type(unwrapped947)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1598 = _dollar_dollar.int128_type
                                else:
                                    _t1598 = None
                                deconstruct_result944 = _t1598
                                if deconstruct_result944 is not None:
                                    assert deconstruct_result944 is not None
                                    unwrapped945 = deconstruct_result944
                                    self.pretty_int128_type(unwrapped945)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1599 = _dollar_dollar.date_type
                                    else:
                                        _t1599 = None
                                    deconstruct_result942 = _t1599
                                    if deconstruct_result942 is not None:
                                        assert deconstruct_result942 is not None
                                        unwrapped943 = deconstruct_result942
                                        self.pretty_date_type(unwrapped943)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1600 = _dollar_dollar.datetime_type
                                        else:
                                            _t1600 = None
                                        deconstruct_result940 = _t1600
                                        if deconstruct_result940 is not None:
                                            assert deconstruct_result940 is not None
                                            unwrapped941 = deconstruct_result940
                                            self.pretty_datetime_type(unwrapped941)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1601 = _dollar_dollar.missing_type
                                            else:
                                                _t1601 = None
                                            deconstruct_result938 = _t1601
                                            if deconstruct_result938 is not None:
                                                assert deconstruct_result938 is not None
                                                unwrapped939 = deconstruct_result938
                                                self.pretty_missing_type(unwrapped939)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1602 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1602 = None
                                                deconstruct_result936 = _t1602
                                                if deconstruct_result936 is not None:
                                                    assert deconstruct_result936 is not None
                                                    unwrapped937 = deconstruct_result936
                                                    self.pretty_decimal_type(unwrapped937)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1603 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1603 = None
                                                    deconstruct_result934 = _t1603
                                                    if deconstruct_result934 is not None:
                                                        assert deconstruct_result934 is not None
                                                        unwrapped935 = deconstruct_result934
                                                        self.pretty_boolean_type(unwrapped935)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1604 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1604 = None
                                                        deconstruct_result932 = _t1604
                                                        if deconstruct_result932 is not None:
                                                            assert deconstruct_result932 is not None
                                                            unwrapped933 = deconstruct_result932
                                                            self.pretty_int32_type(unwrapped933)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1605 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1605 = None
                                                            deconstruct_result930 = _t1605
                                                            if deconstruct_result930 is not None:
                                                                assert deconstruct_result930 is not None
                                                                unwrapped931 = deconstruct_result930
                                                                self.pretty_float32_type(unwrapped931)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1606 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1606 = None
                                                                deconstruct_result928 = _t1606
                                                                if deconstruct_result928 is not None:
                                                                    assert deconstruct_result928 is not None
                                                                    unwrapped929 = deconstruct_result928
                                                                    self.pretty_uint32_type(unwrapped929)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields957 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields958 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields959 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields960 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields961 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields962 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields963 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields964 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields965 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat970 = self._try_flat(msg, self.pretty_decimal_type)
        if flat970 is not None:
            assert flat970 is not None
            self.write(flat970)
            return None
        else:
            _dollar_dollar = msg
            fields966 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields966 is not None
            unwrapped_fields967 = fields966
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field968 = unwrapped_fields967[0]
            self.write(str(field968))
            self.newline()
            field969 = unwrapped_fields967[1]
            self.write(str(field969))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields971 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields972 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields973 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields974 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat978 = self._try_flat(msg, self.pretty_value_bindings)
        if flat978 is not None:
            assert flat978 is not None
            self.write(flat978)
            return None
        else:
            fields975 = msg
            self.write("|")
            if not len(fields975) == 0:
                self.write(" ")
                for i977, elem976 in enumerate(fields975):
                    if (i977 > 0):
                        self.newline()
                    self.pretty_binding(elem976)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1005 = self._try_flat(msg, self.pretty_formula)
        if flat1005 is not None:
            assert flat1005 is not None
            self.write(flat1005)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1607 = _dollar_dollar.conjunction
            else:
                _t1607 = None
            deconstruct_result1003 = _t1607
            if deconstruct_result1003 is not None:
                assert deconstruct_result1003 is not None
                unwrapped1004 = deconstruct_result1003
                self.pretty_true(unwrapped1004)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1608 = _dollar_dollar.disjunction
                else:
                    _t1608 = None
                deconstruct_result1001 = _t1608
                if deconstruct_result1001 is not None:
                    assert deconstruct_result1001 is not None
                    unwrapped1002 = deconstruct_result1001
                    self.pretty_false(unwrapped1002)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1609 = _dollar_dollar.exists
                    else:
                        _t1609 = None
                    deconstruct_result999 = _t1609
                    if deconstruct_result999 is not None:
                        assert deconstruct_result999 is not None
                        unwrapped1000 = deconstruct_result999
                        self.pretty_exists(unwrapped1000)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1610 = _dollar_dollar.reduce
                        else:
                            _t1610 = None
                        deconstruct_result997 = _t1610
                        if deconstruct_result997 is not None:
                            assert deconstruct_result997 is not None
                            unwrapped998 = deconstruct_result997
                            self.pretty_reduce(unwrapped998)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1611 = _dollar_dollar.conjunction
                            else:
                                _t1611 = None
                            deconstruct_result995 = _t1611
                            if deconstruct_result995 is not None:
                                assert deconstruct_result995 is not None
                                unwrapped996 = deconstruct_result995
                                self.pretty_conjunction(unwrapped996)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1612 = _dollar_dollar.disjunction
                                else:
                                    _t1612 = None
                                deconstruct_result993 = _t1612
                                if deconstruct_result993 is not None:
                                    assert deconstruct_result993 is not None
                                    unwrapped994 = deconstruct_result993
                                    self.pretty_disjunction(unwrapped994)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1613 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1613 = None
                                    deconstruct_result991 = _t1613
                                    if deconstruct_result991 is not None:
                                        assert deconstruct_result991 is not None
                                        unwrapped992 = deconstruct_result991
                                        self.pretty_not(unwrapped992)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1614 = _dollar_dollar.ffi
                                        else:
                                            _t1614 = None
                                        deconstruct_result989 = _t1614
                                        if deconstruct_result989 is not None:
                                            assert deconstruct_result989 is not None
                                            unwrapped990 = deconstruct_result989
                                            self.pretty_ffi(unwrapped990)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1615 = _dollar_dollar.atom
                                            else:
                                                _t1615 = None
                                            deconstruct_result987 = _t1615
                                            if deconstruct_result987 is not None:
                                                assert deconstruct_result987 is not None
                                                unwrapped988 = deconstruct_result987
                                                self.pretty_atom(unwrapped988)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1616 = _dollar_dollar.pragma
                                                else:
                                                    _t1616 = None
                                                deconstruct_result985 = _t1616
                                                if deconstruct_result985 is not None:
                                                    assert deconstruct_result985 is not None
                                                    unwrapped986 = deconstruct_result985
                                                    self.pretty_pragma(unwrapped986)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1617 = _dollar_dollar.primitive
                                                    else:
                                                        _t1617 = None
                                                    deconstruct_result983 = _t1617
                                                    if deconstruct_result983 is not None:
                                                        assert deconstruct_result983 is not None
                                                        unwrapped984 = deconstruct_result983
                                                        self.pretty_primitive(unwrapped984)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1618 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1618 = None
                                                        deconstruct_result981 = _t1618
                                                        if deconstruct_result981 is not None:
                                                            assert deconstruct_result981 is not None
                                                            unwrapped982 = deconstruct_result981
                                                            self.pretty_rel_atom(unwrapped982)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1619 = _dollar_dollar.cast
                                                            else:
                                                                _t1619 = None
                                                            deconstruct_result979 = _t1619
                                                            if deconstruct_result979 is not None:
                                                                assert deconstruct_result979 is not None
                                                                unwrapped980 = deconstruct_result979
                                                                self.pretty_cast(unwrapped980)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields1006 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1007 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1012 = self._try_flat(msg, self.pretty_exists)
        if flat1012 is not None:
            assert flat1012 is not None
            self.write(flat1012)
            return None
        else:
            _dollar_dollar = msg
            _t1620 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1008 = (_t1620, _dollar_dollar.body.value,)
            assert fields1008 is not None
            unwrapped_fields1009 = fields1008
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1010 = unwrapped_fields1009[0]
            self.pretty_bindings(field1010)
            self.newline()
            field1011 = unwrapped_fields1009[1]
            self.pretty_formula(field1011)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1018 = self._try_flat(msg, self.pretty_reduce)
        if flat1018 is not None:
            assert flat1018 is not None
            self.write(flat1018)
            return None
        else:
            _dollar_dollar = msg
            fields1013 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1013 is not None
            unwrapped_fields1014 = fields1013
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1015 = unwrapped_fields1014[0]
            self.pretty_abstraction(field1015)
            self.newline()
            field1016 = unwrapped_fields1014[1]
            self.pretty_abstraction(field1016)
            self.newline()
            field1017 = unwrapped_fields1014[2]
            self.pretty_terms(field1017)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1022 = self._try_flat(msg, self.pretty_terms)
        if flat1022 is not None:
            assert flat1022 is not None
            self.write(flat1022)
            return None
        else:
            fields1019 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1019) == 0:
                self.newline()
                for i1021, elem1020 in enumerate(fields1019):
                    if (i1021 > 0):
                        self.newline()
                    self.pretty_term(elem1020)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1027 = self._try_flat(msg, self.pretty_term)
        if flat1027 is not None:
            assert flat1027 is not None
            self.write(flat1027)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1621 = _dollar_dollar.var
            else:
                _t1621 = None
            deconstruct_result1025 = _t1621
            if deconstruct_result1025 is not None:
                assert deconstruct_result1025 is not None
                unwrapped1026 = deconstruct_result1025
                self.pretty_var(unwrapped1026)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1622 = _dollar_dollar.constant
                else:
                    _t1622 = None
                deconstruct_result1023 = _t1622
                if deconstruct_result1023 is not None:
                    assert deconstruct_result1023 is not None
                    unwrapped1024 = deconstruct_result1023
                    self.pretty_value(unwrapped1024)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1030 = self._try_flat(msg, self.pretty_var)
        if flat1030 is not None:
            assert flat1030 is not None
            self.write(flat1030)
            return None
        else:
            _dollar_dollar = msg
            fields1028 = _dollar_dollar.name
            assert fields1028 is not None
            unwrapped_fields1029 = fields1028
            self.write(unwrapped_fields1029)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1056 = self._try_flat(msg, self.pretty_value)
        if flat1056 is not None:
            assert flat1056 is not None
            self.write(flat1056)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1623 = _dollar_dollar.date_value
            else:
                _t1623 = None
            deconstruct_result1054 = _t1623
            if deconstruct_result1054 is not None:
                assert deconstruct_result1054 is not None
                unwrapped1055 = deconstruct_result1054
                self.pretty_date(unwrapped1055)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1624 = _dollar_dollar.datetime_value
                else:
                    _t1624 = None
                deconstruct_result1052 = _t1624
                if deconstruct_result1052 is not None:
                    assert deconstruct_result1052 is not None
                    unwrapped1053 = deconstruct_result1052
                    self.pretty_datetime(unwrapped1053)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1625 = _dollar_dollar.string_value
                    else:
                        _t1625 = None
                    deconstruct_result1050 = _t1625
                    if deconstruct_result1050 is not None:
                        assert deconstruct_result1050 is not None
                        unwrapped1051 = deconstruct_result1050
                        self.write(self.format_string_value(unwrapped1051))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1626 = _dollar_dollar.int32_value
                        else:
                            _t1626 = None
                        deconstruct_result1048 = _t1626
                        if deconstruct_result1048 is not None:
                            assert deconstruct_result1048 is not None
                            unwrapped1049 = deconstruct_result1048
                            self.write((str(unwrapped1049) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1627 = _dollar_dollar.int_value
                            else:
                                _t1627 = None
                            deconstruct_result1046 = _t1627
                            if deconstruct_result1046 is not None:
                                assert deconstruct_result1046 is not None
                                unwrapped1047 = deconstruct_result1046
                                self.write(str(unwrapped1047))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1628 = _dollar_dollar.float32_value
                                else:
                                    _t1628 = None
                                deconstruct_result1044 = _t1628
                                if deconstruct_result1044 is not None:
                                    assert deconstruct_result1044 is not None
                                    unwrapped1045 = deconstruct_result1044
                                    self.write(self.format_float32_literal(unwrapped1045))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1629 = _dollar_dollar.float_value
                                    else:
                                        _t1629 = None
                                    deconstruct_result1042 = _t1629
                                    if deconstruct_result1042 is not None:
                                        assert deconstruct_result1042 is not None
                                        unwrapped1043 = deconstruct_result1042
                                        self.write(str(unwrapped1043))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1630 = _dollar_dollar.uint32_value
                                        else:
                                            _t1630 = None
                                        deconstruct_result1040 = _t1630
                                        if deconstruct_result1040 is not None:
                                            assert deconstruct_result1040 is not None
                                            unwrapped1041 = deconstruct_result1040
                                            self.write((str(unwrapped1041) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1631 = _dollar_dollar.uint128_value
                                            else:
                                                _t1631 = None
                                            deconstruct_result1038 = _t1631
                                            if deconstruct_result1038 is not None:
                                                assert deconstruct_result1038 is not None
                                                unwrapped1039 = deconstruct_result1038
                                                self.write(self.format_uint128(unwrapped1039))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1632 = _dollar_dollar.int128_value
                                                else:
                                                    _t1632 = None
                                                deconstruct_result1036 = _t1632
                                                if deconstruct_result1036 is not None:
                                                    assert deconstruct_result1036 is not None
                                                    unwrapped1037 = deconstruct_result1036
                                                    self.write(self.format_int128(unwrapped1037))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1633 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1633 = None
                                                    deconstruct_result1034 = _t1633
                                                    if deconstruct_result1034 is not None:
                                                        assert deconstruct_result1034 is not None
                                                        unwrapped1035 = deconstruct_result1034
                                                        self.write(self.format_decimal(unwrapped1035))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1634 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1634 = None
                                                        deconstruct_result1032 = _t1634
                                                        if deconstruct_result1032 is not None:
                                                            assert deconstruct_result1032 is not None
                                                            unwrapped1033 = deconstruct_result1032
                                                            self.pretty_boolean_value(unwrapped1033)
                                                        else:
                                                            fields1031 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1062 = self._try_flat(msg, self.pretty_date)
        if flat1062 is not None:
            assert flat1062 is not None
            self.write(flat1062)
            return None
        else:
            _dollar_dollar = msg
            fields1057 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1057 is not None
            unwrapped_fields1058 = fields1057
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1059 = unwrapped_fields1058[0]
            self.write(str(field1059))
            self.newline()
            field1060 = unwrapped_fields1058[1]
            self.write(str(field1060))
            self.newline()
            field1061 = unwrapped_fields1058[2]
            self.write(str(field1061))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1073 = self._try_flat(msg, self.pretty_datetime)
        if flat1073 is not None:
            assert flat1073 is not None
            self.write(flat1073)
            return None
        else:
            _dollar_dollar = msg
            fields1063 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1063 is not None
            unwrapped_fields1064 = fields1063
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1065 = unwrapped_fields1064[0]
            self.write(str(field1065))
            self.newline()
            field1066 = unwrapped_fields1064[1]
            self.write(str(field1066))
            self.newline()
            field1067 = unwrapped_fields1064[2]
            self.write(str(field1067))
            self.newline()
            field1068 = unwrapped_fields1064[3]
            self.write(str(field1068))
            self.newline()
            field1069 = unwrapped_fields1064[4]
            self.write(str(field1069))
            self.newline()
            field1070 = unwrapped_fields1064[5]
            self.write(str(field1070))
            field1071 = unwrapped_fields1064[6]
            if field1071 is not None:
                self.newline()
                assert field1071 is not None
                opt_val1072 = field1071
                self.write(str(opt_val1072))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1078 = self._try_flat(msg, self.pretty_conjunction)
        if flat1078 is not None:
            assert flat1078 is not None
            self.write(flat1078)
            return None
        else:
            _dollar_dollar = msg
            fields1074 = _dollar_dollar.args
            assert fields1074 is not None
            unwrapped_fields1075 = fields1074
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1075) == 0:
                self.newline()
                for i1077, elem1076 in enumerate(unwrapped_fields1075):
                    if (i1077 > 0):
                        self.newline()
                    self.pretty_formula(elem1076)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1083 = self._try_flat(msg, self.pretty_disjunction)
        if flat1083 is not None:
            assert flat1083 is not None
            self.write(flat1083)
            return None
        else:
            _dollar_dollar = msg
            fields1079 = _dollar_dollar.args
            assert fields1079 is not None
            unwrapped_fields1080 = fields1079
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1080) == 0:
                self.newline()
                for i1082, elem1081 in enumerate(unwrapped_fields1080):
                    if (i1082 > 0):
                        self.newline()
                    self.pretty_formula(elem1081)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1086 = self._try_flat(msg, self.pretty_not)
        if flat1086 is not None:
            assert flat1086 is not None
            self.write(flat1086)
            return None
        else:
            _dollar_dollar = msg
            fields1084 = _dollar_dollar.arg
            assert fields1084 is not None
            unwrapped_fields1085 = fields1084
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1085)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1092 = self._try_flat(msg, self.pretty_ffi)
        if flat1092 is not None:
            assert flat1092 is not None
            self.write(flat1092)
            return None
        else:
            _dollar_dollar = msg
            fields1087 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1087 is not None
            unwrapped_fields1088 = fields1087
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1089 = unwrapped_fields1088[0]
            self.pretty_name(field1089)
            self.newline()
            field1090 = unwrapped_fields1088[1]
            self.pretty_ffi_args(field1090)
            self.newline()
            field1091 = unwrapped_fields1088[2]
            self.pretty_terms(field1091)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1094 = self._try_flat(msg, self.pretty_name)
        if flat1094 is not None:
            assert flat1094 is not None
            self.write(flat1094)
            return None
        else:
            fields1093 = msg
            self.write(":")
            self.write(fields1093)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1098 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1098 is not None:
            assert flat1098 is not None
            self.write(flat1098)
            return None
        else:
            fields1095 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1095) == 0:
                self.newline()
                for i1097, elem1096 in enumerate(fields1095):
                    if (i1097 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1096)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1105 = self._try_flat(msg, self.pretty_atom)
        if flat1105 is not None:
            assert flat1105 is not None
            self.write(flat1105)
            return None
        else:
            _dollar_dollar = msg
            fields1099 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1099 is not None
            unwrapped_fields1100 = fields1099
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1101 = unwrapped_fields1100[0]
            self.pretty_relation_id(field1101)
            field1102 = unwrapped_fields1100[1]
            if not len(field1102) == 0:
                self.newline()
                for i1104, elem1103 in enumerate(field1102):
                    if (i1104 > 0):
                        self.newline()
                    self.pretty_term(elem1103)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1112 = self._try_flat(msg, self.pretty_pragma)
        if flat1112 is not None:
            assert flat1112 is not None
            self.write(flat1112)
            return None
        else:
            _dollar_dollar = msg
            fields1106 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1106 is not None
            unwrapped_fields1107 = fields1106
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1108 = unwrapped_fields1107[0]
            self.pretty_name(field1108)
            field1109 = unwrapped_fields1107[1]
            if not len(field1109) == 0:
                self.newline()
                for i1111, elem1110 in enumerate(field1109):
                    if (i1111 > 0):
                        self.newline()
                    self.pretty_term(elem1110)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1128 = self._try_flat(msg, self.pretty_primitive)
        if flat1128 is not None:
            assert flat1128 is not None
            self.write(flat1128)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1635 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1635 = None
            guard_result1127 = _t1635
            if guard_result1127 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1636 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1636 = None
                guard_result1126 = _t1636
                if guard_result1126 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1637 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1637 = None
                    guard_result1125 = _t1637
                    if guard_result1125 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1638 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1638 = None
                        guard_result1124 = _t1638
                        if guard_result1124 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1639 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1639 = None
                            guard_result1123 = _t1639
                            if guard_result1123 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1640 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1640 = None
                                guard_result1122 = _t1640
                                if guard_result1122 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1641 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1641 = None
                                    guard_result1121 = _t1641
                                    if guard_result1121 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1642 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1642 = None
                                        guard_result1120 = _t1642
                                        if guard_result1120 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1643 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1643 = None
                                            guard_result1119 = _t1643
                                            if guard_result1119 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1113 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1113 is not None
                                                unwrapped_fields1114 = fields1113
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1115 = unwrapped_fields1114[0]
                                                self.pretty_name(field1115)
                                                field1116 = unwrapped_fields1114[1]
                                                if not len(field1116) == 0:
                                                    self.newline()
                                                    for i1118, elem1117 in enumerate(field1116):
                                                        if (i1118 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1117)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1133 = self._try_flat(msg, self.pretty_eq)
        if flat1133 is not None:
            assert flat1133 is not None
            self.write(flat1133)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1644 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1644 = None
            fields1129 = _t1644
            assert fields1129 is not None
            unwrapped_fields1130 = fields1129
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1131 = unwrapped_fields1130[0]
            self.pretty_term(field1131)
            self.newline()
            field1132 = unwrapped_fields1130[1]
            self.pretty_term(field1132)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1138 = self._try_flat(msg, self.pretty_lt)
        if flat1138 is not None:
            assert flat1138 is not None
            self.write(flat1138)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1645 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1645 = None
            fields1134 = _t1645
            assert fields1134 is not None
            unwrapped_fields1135 = fields1134
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1136 = unwrapped_fields1135[0]
            self.pretty_term(field1136)
            self.newline()
            field1137 = unwrapped_fields1135[1]
            self.pretty_term(field1137)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1143 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1143 is not None:
            assert flat1143 is not None
            self.write(flat1143)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1646 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1646 = None
            fields1139 = _t1646
            assert fields1139 is not None
            unwrapped_fields1140 = fields1139
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1141 = unwrapped_fields1140[0]
            self.pretty_term(field1141)
            self.newline()
            field1142 = unwrapped_fields1140[1]
            self.pretty_term(field1142)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1148 = self._try_flat(msg, self.pretty_gt)
        if flat1148 is not None:
            assert flat1148 is not None
            self.write(flat1148)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1647 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1647 = None
            fields1144 = _t1647
            assert fields1144 is not None
            unwrapped_fields1145 = fields1144
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1146 = unwrapped_fields1145[0]
            self.pretty_term(field1146)
            self.newline()
            field1147 = unwrapped_fields1145[1]
            self.pretty_term(field1147)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1153 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1153 is not None:
            assert flat1153 is not None
            self.write(flat1153)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1648 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1648 = None
            fields1149 = _t1648
            assert fields1149 is not None
            unwrapped_fields1150 = fields1149
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1151 = unwrapped_fields1150[0]
            self.pretty_term(field1151)
            self.newline()
            field1152 = unwrapped_fields1150[1]
            self.pretty_term(field1152)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1159 = self._try_flat(msg, self.pretty_add)
        if flat1159 is not None:
            assert flat1159 is not None
            self.write(flat1159)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1649 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1649 = None
            fields1154 = _t1649
            assert fields1154 is not None
            unwrapped_fields1155 = fields1154
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1156 = unwrapped_fields1155[0]
            self.pretty_term(field1156)
            self.newline()
            field1157 = unwrapped_fields1155[1]
            self.pretty_term(field1157)
            self.newline()
            field1158 = unwrapped_fields1155[2]
            self.pretty_term(field1158)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1165 = self._try_flat(msg, self.pretty_minus)
        if flat1165 is not None:
            assert flat1165 is not None
            self.write(flat1165)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1650 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1650 = None
            fields1160 = _t1650
            assert fields1160 is not None
            unwrapped_fields1161 = fields1160
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1162 = unwrapped_fields1161[0]
            self.pretty_term(field1162)
            self.newline()
            field1163 = unwrapped_fields1161[1]
            self.pretty_term(field1163)
            self.newline()
            field1164 = unwrapped_fields1161[2]
            self.pretty_term(field1164)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1171 = self._try_flat(msg, self.pretty_multiply)
        if flat1171 is not None:
            assert flat1171 is not None
            self.write(flat1171)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1651 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1651 = None
            fields1166 = _t1651
            assert fields1166 is not None
            unwrapped_fields1167 = fields1166
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1168 = unwrapped_fields1167[0]
            self.pretty_term(field1168)
            self.newline()
            field1169 = unwrapped_fields1167[1]
            self.pretty_term(field1169)
            self.newline()
            field1170 = unwrapped_fields1167[2]
            self.pretty_term(field1170)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1177 = self._try_flat(msg, self.pretty_divide)
        if flat1177 is not None:
            assert flat1177 is not None
            self.write(flat1177)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1652 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1652 = None
            fields1172 = _t1652
            assert fields1172 is not None
            unwrapped_fields1173 = fields1172
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1174 = unwrapped_fields1173[0]
            self.pretty_term(field1174)
            self.newline()
            field1175 = unwrapped_fields1173[1]
            self.pretty_term(field1175)
            self.newline()
            field1176 = unwrapped_fields1173[2]
            self.pretty_term(field1176)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1182 = self._try_flat(msg, self.pretty_rel_term)
        if flat1182 is not None:
            assert flat1182 is not None
            self.write(flat1182)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1653 = _dollar_dollar.specialized_value
            else:
                _t1653 = None
            deconstruct_result1180 = _t1653
            if deconstruct_result1180 is not None:
                assert deconstruct_result1180 is not None
                unwrapped1181 = deconstruct_result1180
                self.pretty_specialized_value(unwrapped1181)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1654 = _dollar_dollar.term
                else:
                    _t1654 = None
                deconstruct_result1178 = _t1654
                if deconstruct_result1178 is not None:
                    assert deconstruct_result1178 is not None
                    unwrapped1179 = deconstruct_result1178
                    self.pretty_term(unwrapped1179)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1184 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1184 is not None:
            assert flat1184 is not None
            self.write(flat1184)
            return None
        else:
            fields1183 = msg
            self.write("#")
            self.pretty_raw_value(fields1183)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1191 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1191 is not None:
            assert flat1191 is not None
            self.write(flat1191)
            return None
        else:
            _dollar_dollar = msg
            fields1185 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1185 is not None
            unwrapped_fields1186 = fields1185
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1187 = unwrapped_fields1186[0]
            self.pretty_name(field1187)
            field1188 = unwrapped_fields1186[1]
            if not len(field1188) == 0:
                self.newline()
                for i1190, elem1189 in enumerate(field1188):
                    if (i1190 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1189)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1196 = self._try_flat(msg, self.pretty_cast)
        if flat1196 is not None:
            assert flat1196 is not None
            self.write(flat1196)
            return None
        else:
            _dollar_dollar = msg
            fields1192 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1192 is not None
            unwrapped_fields1193 = fields1192
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1194 = unwrapped_fields1193[0]
            self.pretty_term(field1194)
            self.newline()
            field1195 = unwrapped_fields1193[1]
            self.pretty_term(field1195)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1200 = self._try_flat(msg, self.pretty_attrs)
        if flat1200 is not None:
            assert flat1200 is not None
            self.write(flat1200)
            return None
        else:
            fields1197 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1197) == 0:
                self.newline()
                for i1199, elem1198 in enumerate(fields1197):
                    if (i1199 > 0):
                        self.newline()
                    self.pretty_attribute(elem1198)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1207 = self._try_flat(msg, self.pretty_attribute)
        if flat1207 is not None:
            assert flat1207 is not None
            self.write(flat1207)
            return None
        else:
            _dollar_dollar = msg
            fields1201 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1201 is not None
            unwrapped_fields1202 = fields1201
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1203 = unwrapped_fields1202[0]
            self.pretty_name(field1203)
            field1204 = unwrapped_fields1202[1]
            if not len(field1204) == 0:
                self.newline()
                for i1206, elem1205 in enumerate(field1204):
                    if (i1206 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1205)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1214 = self._try_flat(msg, self.pretty_algorithm)
        if flat1214 is not None:
            assert flat1214 is not None
            self.write(flat1214)
            return None
        else:
            _dollar_dollar = msg
            fields1208 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            assert fields1208 is not None
            unwrapped_fields1209 = fields1208
            self.write("(algorithm")
            self.indent_sexp()
            field1210 = unwrapped_fields1209[0]
            if not len(field1210) == 0:
                self.newline()
                for i1212, elem1211 in enumerate(field1210):
                    if (i1212 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1211)
            self.newline()
            field1213 = unwrapped_fields1209[1]
            self.pretty_script(field1213)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1219 = self._try_flat(msg, self.pretty_script)
        if flat1219 is not None:
            assert flat1219 is not None
            self.write(flat1219)
            return None
        else:
            _dollar_dollar = msg
            fields1215 = _dollar_dollar.constructs
            assert fields1215 is not None
            unwrapped_fields1216 = fields1215
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1216) == 0:
                self.newline()
                for i1218, elem1217 in enumerate(unwrapped_fields1216):
                    if (i1218 > 0):
                        self.newline()
                    self.pretty_construct(elem1217)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1224 = self._try_flat(msg, self.pretty_construct)
        if flat1224 is not None:
            assert flat1224 is not None
            self.write(flat1224)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1655 = _dollar_dollar.loop
            else:
                _t1655 = None
            deconstruct_result1222 = _t1655
            if deconstruct_result1222 is not None:
                assert deconstruct_result1222 is not None
                unwrapped1223 = deconstruct_result1222
                self.pretty_loop(unwrapped1223)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1656 = _dollar_dollar.instruction
                else:
                    _t1656 = None
                deconstruct_result1220 = _t1656
                if deconstruct_result1220 is not None:
                    assert deconstruct_result1220 is not None
                    unwrapped1221 = deconstruct_result1220
                    self.pretty_instruction(unwrapped1221)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1229 = self._try_flat(msg, self.pretty_loop)
        if flat1229 is not None:
            assert flat1229 is not None
            self.write(flat1229)
            return None
        else:
            _dollar_dollar = msg
            fields1225 = (_dollar_dollar.init, _dollar_dollar.body,)
            assert fields1225 is not None
            unwrapped_fields1226 = fields1225
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1227 = unwrapped_fields1226[0]
            self.pretty_init(field1227)
            self.newline()
            field1228 = unwrapped_fields1226[1]
            self.pretty_script(field1228)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1233 = self._try_flat(msg, self.pretty_init)
        if flat1233 is not None:
            assert flat1233 is not None
            self.write(flat1233)
            return None
        else:
            fields1230 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1230) == 0:
                self.newline()
                for i1232, elem1231 in enumerate(fields1230):
                    if (i1232 > 0):
                        self.newline()
                    self.pretty_instruction(elem1231)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1244 = self._try_flat(msg, self.pretty_instruction)
        if flat1244 is not None:
            assert flat1244 is not None
            self.write(flat1244)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1657 = _dollar_dollar.assign
            else:
                _t1657 = None
            deconstruct_result1242 = _t1657
            if deconstruct_result1242 is not None:
                assert deconstruct_result1242 is not None
                unwrapped1243 = deconstruct_result1242
                self.pretty_assign(unwrapped1243)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1658 = _dollar_dollar.upsert
                else:
                    _t1658 = None
                deconstruct_result1240 = _t1658
                if deconstruct_result1240 is not None:
                    assert deconstruct_result1240 is not None
                    unwrapped1241 = deconstruct_result1240
                    self.pretty_upsert(unwrapped1241)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1659 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1659 = None
                    deconstruct_result1238 = _t1659
                    if deconstruct_result1238 is not None:
                        assert deconstruct_result1238 is not None
                        unwrapped1239 = deconstruct_result1238
                        self.pretty_break(unwrapped1239)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1660 = _dollar_dollar.monoid_def
                        else:
                            _t1660 = None
                        deconstruct_result1236 = _t1660
                        if deconstruct_result1236 is not None:
                            assert deconstruct_result1236 is not None
                            unwrapped1237 = deconstruct_result1236
                            self.pretty_monoid_def(unwrapped1237)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1661 = _dollar_dollar.monus_def
                            else:
                                _t1661 = None
                            deconstruct_result1234 = _t1661
                            if deconstruct_result1234 is not None:
                                assert deconstruct_result1234 is not None
                                unwrapped1235 = deconstruct_result1234
                                self.pretty_monus_def(unwrapped1235)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1251 = self._try_flat(msg, self.pretty_assign)
        if flat1251 is not None:
            assert flat1251 is not None
            self.write(flat1251)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1662 = _dollar_dollar.attrs
            else:
                _t1662 = None
            fields1245 = (_dollar_dollar.name, _dollar_dollar.body, _t1662,)
            assert fields1245 is not None
            unwrapped_fields1246 = fields1245
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1247 = unwrapped_fields1246[0]
            self.pretty_relation_id(field1247)
            self.newline()
            field1248 = unwrapped_fields1246[1]
            self.pretty_abstraction(field1248)
            field1249 = unwrapped_fields1246[2]
            if field1249 is not None:
                self.newline()
                assert field1249 is not None
                opt_val1250 = field1249
                self.pretty_attrs(opt_val1250)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1258 = self._try_flat(msg, self.pretty_upsert)
        if flat1258 is not None:
            assert flat1258 is not None
            self.write(flat1258)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1663 = _dollar_dollar.attrs
            else:
                _t1663 = None
            fields1252 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1663,)
            assert fields1252 is not None
            unwrapped_fields1253 = fields1252
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1254 = unwrapped_fields1253[0]
            self.pretty_relation_id(field1254)
            self.newline()
            field1255 = unwrapped_fields1253[1]
            self.pretty_abstraction_with_arity(field1255)
            field1256 = unwrapped_fields1253[2]
            if field1256 is not None:
                self.newline()
                assert field1256 is not None
                opt_val1257 = field1256
                self.pretty_attrs(opt_val1257)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1263 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1263 is not None:
            assert flat1263 is not None
            self.write(flat1263)
            return None
        else:
            _dollar_dollar = msg
            _t1664 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1259 = (_t1664, _dollar_dollar[0].value,)
            assert fields1259 is not None
            unwrapped_fields1260 = fields1259
            self.write("(")
            self.indent()
            field1261 = unwrapped_fields1260[0]
            self.pretty_bindings(field1261)
            self.newline()
            field1262 = unwrapped_fields1260[1]
            self.pretty_formula(field1262)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1270 = self._try_flat(msg, self.pretty_break)
        if flat1270 is not None:
            assert flat1270 is not None
            self.write(flat1270)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1665 = _dollar_dollar.attrs
            else:
                _t1665 = None
            fields1264 = (_dollar_dollar.name, _dollar_dollar.body, _t1665,)
            assert fields1264 is not None
            unwrapped_fields1265 = fields1264
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1266 = unwrapped_fields1265[0]
            self.pretty_relation_id(field1266)
            self.newline()
            field1267 = unwrapped_fields1265[1]
            self.pretty_abstraction(field1267)
            field1268 = unwrapped_fields1265[2]
            if field1268 is not None:
                self.newline()
                assert field1268 is not None
                opt_val1269 = field1268
                self.pretty_attrs(opt_val1269)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1278 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1278 is not None:
            assert flat1278 is not None
            self.write(flat1278)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1666 = _dollar_dollar.attrs
            else:
                _t1666 = None
            fields1271 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1666,)
            assert fields1271 is not None
            unwrapped_fields1272 = fields1271
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1273 = unwrapped_fields1272[0]
            self.pretty_monoid(field1273)
            self.newline()
            field1274 = unwrapped_fields1272[1]
            self.pretty_relation_id(field1274)
            self.newline()
            field1275 = unwrapped_fields1272[2]
            self.pretty_abstraction_with_arity(field1275)
            field1276 = unwrapped_fields1272[3]
            if field1276 is not None:
                self.newline()
                assert field1276 is not None
                opt_val1277 = field1276
                self.pretty_attrs(opt_val1277)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1287 = self._try_flat(msg, self.pretty_monoid)
        if flat1287 is not None:
            assert flat1287 is not None
            self.write(flat1287)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1667 = _dollar_dollar.or_monoid
            else:
                _t1667 = None
            deconstruct_result1285 = _t1667
            if deconstruct_result1285 is not None:
                assert deconstruct_result1285 is not None
                unwrapped1286 = deconstruct_result1285
                self.pretty_or_monoid(unwrapped1286)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1668 = _dollar_dollar.min_monoid
                else:
                    _t1668 = None
                deconstruct_result1283 = _t1668
                if deconstruct_result1283 is not None:
                    assert deconstruct_result1283 is not None
                    unwrapped1284 = deconstruct_result1283
                    self.pretty_min_monoid(unwrapped1284)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1669 = _dollar_dollar.max_monoid
                    else:
                        _t1669 = None
                    deconstruct_result1281 = _t1669
                    if deconstruct_result1281 is not None:
                        assert deconstruct_result1281 is not None
                        unwrapped1282 = deconstruct_result1281
                        self.pretty_max_monoid(unwrapped1282)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1670 = _dollar_dollar.sum_monoid
                        else:
                            _t1670 = None
                        deconstruct_result1279 = _t1670
                        if deconstruct_result1279 is not None:
                            assert deconstruct_result1279 is not None
                            unwrapped1280 = deconstruct_result1279
                            self.pretty_sum_monoid(unwrapped1280)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1288 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1291 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1291 is not None:
            assert flat1291 is not None
            self.write(flat1291)
            return None
        else:
            _dollar_dollar = msg
            fields1289 = _dollar_dollar.type
            assert fields1289 is not None
            unwrapped_fields1290 = fields1289
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1290)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1294 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1294 is not None:
            assert flat1294 is not None
            self.write(flat1294)
            return None
        else:
            _dollar_dollar = msg
            fields1292 = _dollar_dollar.type
            assert fields1292 is not None
            unwrapped_fields1293 = fields1292
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1293)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1297 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1297 is not None:
            assert flat1297 is not None
            self.write(flat1297)
            return None
        else:
            _dollar_dollar = msg
            fields1295 = _dollar_dollar.type
            assert fields1295 is not None
            unwrapped_fields1296 = fields1295
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1296)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1305 = self._try_flat(msg, self.pretty_monus_def)
        if flat1305 is not None:
            assert flat1305 is not None
            self.write(flat1305)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1671 = _dollar_dollar.attrs
            else:
                _t1671 = None
            fields1298 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1671,)
            assert fields1298 is not None
            unwrapped_fields1299 = fields1298
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1300 = unwrapped_fields1299[0]
            self.pretty_monoid(field1300)
            self.newline()
            field1301 = unwrapped_fields1299[1]
            self.pretty_relation_id(field1301)
            self.newline()
            field1302 = unwrapped_fields1299[2]
            self.pretty_abstraction_with_arity(field1302)
            field1303 = unwrapped_fields1299[3]
            if field1303 is not None:
                self.newline()
                assert field1303 is not None
                opt_val1304 = field1303
                self.pretty_attrs(opt_val1304)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1312 = self._try_flat(msg, self.pretty_constraint)
        if flat1312 is not None:
            assert flat1312 is not None
            self.write(flat1312)
            return None
        else:
            _dollar_dollar = msg
            fields1306 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1306 is not None
            unwrapped_fields1307 = fields1306
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1308 = unwrapped_fields1307[0]
            self.pretty_relation_id(field1308)
            self.newline()
            field1309 = unwrapped_fields1307[1]
            self.pretty_abstraction(field1309)
            self.newline()
            field1310 = unwrapped_fields1307[2]
            self.pretty_functional_dependency_keys(field1310)
            self.newline()
            field1311 = unwrapped_fields1307[3]
            self.pretty_functional_dependency_values(field1311)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1316 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1316 is not None:
            assert flat1316 is not None
            self.write(flat1316)
            return None
        else:
            fields1313 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1313) == 0:
                self.newline()
                for i1315, elem1314 in enumerate(fields1313):
                    if (i1315 > 0):
                        self.newline()
                    self.pretty_var(elem1314)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1320 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1320 is not None:
            assert flat1320 is not None
            self.write(flat1320)
            return None
        else:
            fields1317 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1317) == 0:
                self.newline()
                for i1319, elem1318 in enumerate(fields1317):
                    if (i1319 > 0):
                        self.newline()
                    self.pretty_var(elem1318)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1329 = self._try_flat(msg, self.pretty_data)
        if flat1329 is not None:
            assert flat1329 is not None
            self.write(flat1329)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1672 = _dollar_dollar.edb
            else:
                _t1672 = None
            deconstruct_result1327 = _t1672
            if deconstruct_result1327 is not None:
                assert deconstruct_result1327 is not None
                unwrapped1328 = deconstruct_result1327
                self.pretty_edb(unwrapped1328)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1673 = _dollar_dollar.betree_relation
                else:
                    _t1673 = None
                deconstruct_result1325 = _t1673
                if deconstruct_result1325 is not None:
                    assert deconstruct_result1325 is not None
                    unwrapped1326 = deconstruct_result1325
                    self.pretty_betree_relation(unwrapped1326)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1674 = _dollar_dollar.csv_data
                    else:
                        _t1674 = None
                    deconstruct_result1323 = _t1674
                    if deconstruct_result1323 is not None:
                        assert deconstruct_result1323 is not None
                        unwrapped1324 = deconstruct_result1323
                        self.pretty_csv_data(unwrapped1324)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1675 = _dollar_dollar.iceberg_data
                        else:
                            _t1675 = None
                        deconstruct_result1321 = _t1675
                        if deconstruct_result1321 is not None:
                            assert deconstruct_result1321 is not None
                            unwrapped1322 = deconstruct_result1321
                            self.pretty_iceberg_data(unwrapped1322)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1335 = self._try_flat(msg, self.pretty_edb)
        if flat1335 is not None:
            assert flat1335 is not None
            self.write(flat1335)
            return None
        else:
            _dollar_dollar = msg
            fields1330 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1330 is not None
            unwrapped_fields1331 = fields1330
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1332 = unwrapped_fields1331[0]
            self.pretty_relation_id(field1332)
            self.newline()
            field1333 = unwrapped_fields1331[1]
            self.pretty_edb_path(field1333)
            self.newline()
            field1334 = unwrapped_fields1331[2]
            self.pretty_edb_types(field1334)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1339 = self._try_flat(msg, self.pretty_edb_path)
        if flat1339 is not None:
            assert flat1339 is not None
            self.write(flat1339)
            return None
        else:
            fields1336 = msg
            self.write("[")
            self.indent()
            for i1338, elem1337 in enumerate(fields1336):
                if (i1338 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1337))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1343 = self._try_flat(msg, self.pretty_edb_types)
        if flat1343 is not None:
            assert flat1343 is not None
            self.write(flat1343)
            return None
        else:
            fields1340 = msg
            self.write("[")
            self.indent()
            for i1342, elem1341 in enumerate(fields1340):
                if (i1342 > 0):
                    self.newline()
                self.pretty_type(elem1341)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1348 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1348 is not None:
            assert flat1348 is not None
            self.write(flat1348)
            return None
        else:
            _dollar_dollar = msg
            fields1344 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1344 is not None
            unwrapped_fields1345 = fields1344
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1346 = unwrapped_fields1345[0]
            self.pretty_relation_id(field1346)
            self.newline()
            field1347 = unwrapped_fields1345[1]
            self.pretty_betree_info(field1347)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1354 = self._try_flat(msg, self.pretty_betree_info)
        if flat1354 is not None:
            assert flat1354 is not None
            self.write(flat1354)
            return None
        else:
            _dollar_dollar = msg
            _t1676 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1349 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1676,)
            assert fields1349 is not None
            unwrapped_fields1350 = fields1349
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1351 = unwrapped_fields1350[0]
            self.pretty_betree_info_key_types(field1351)
            self.newline()
            field1352 = unwrapped_fields1350[1]
            self.pretty_betree_info_value_types(field1352)
            self.newline()
            field1353 = unwrapped_fields1350[2]
            self.pretty_config_dict(field1353)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1358 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1358 is not None:
            assert flat1358 is not None
            self.write(flat1358)
            return None
        else:
            fields1355 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1355) == 0:
                self.newline()
                for i1357, elem1356 in enumerate(fields1355):
                    if (i1357 > 0):
                        self.newline()
                    self.pretty_type(elem1356)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1362 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1362 is not None:
            assert flat1362 is not None
            self.write(flat1362)
            return None
        else:
            fields1359 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1359) == 0:
                self.newline()
                for i1361, elem1360 in enumerate(fields1359):
                    if (i1361 > 0):
                        self.newline()
                    self.pretty_type(elem1360)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1369 = self._try_flat(msg, self.pretty_csv_data)
        if flat1369 is not None:
            assert flat1369 is not None
            self.write(flat1369)
            return None
        else:
            _dollar_dollar = msg
            fields1363 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1363 is not None
            unwrapped_fields1364 = fields1363
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1365 = unwrapped_fields1364[0]
            self.pretty_csvlocator(field1365)
            self.newline()
            field1366 = unwrapped_fields1364[1]
            self.pretty_csv_config(field1366)
            self.newline()
            field1367 = unwrapped_fields1364[2]
            self.pretty_gnf_columns(field1367)
            self.newline()
            field1368 = unwrapped_fields1364[3]
            self.pretty_csv_asof(field1368)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1376 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1376 is not None:
            assert flat1376 is not None
            self.write(flat1376)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1677 = _dollar_dollar.paths
            else:
                _t1677 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1678 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1678 = None
            fields1370 = (_t1677, _t1678,)
            assert fields1370 is not None
            unwrapped_fields1371 = fields1370
            self.write("(csv_locator")
            self.indent_sexp()
            field1372 = unwrapped_fields1371[0]
            if field1372 is not None:
                self.newline()
                assert field1372 is not None
                opt_val1373 = field1372
                self.pretty_csv_locator_paths(opt_val1373)
            field1374 = unwrapped_fields1371[1]
            if field1374 is not None:
                self.newline()
                assert field1374 is not None
                opt_val1375 = field1374
                self.pretty_csv_locator_inline_data(opt_val1375)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1380 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1380 is not None:
            assert flat1380 is not None
            self.write(flat1380)
            return None
        else:
            fields1377 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1377) == 0:
                self.newline()
                for i1379, elem1378 in enumerate(fields1377):
                    if (i1379 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1378))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1382 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1382 is not None:
            assert flat1382 is not None
            self.write(flat1382)
            return None
        else:
            fields1381 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1381))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1385 = self._try_flat(msg, self.pretty_csv_config)
        if flat1385 is not None:
            assert flat1385 is not None
            self.write(flat1385)
            return None
        else:
            _dollar_dollar = msg
            _t1679 = self.deconstruct_csv_config(_dollar_dollar)
            fields1383 = _t1679
            assert fields1383 is not None
            unwrapped_fields1384 = fields1383
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1384)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1389 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1389 is not None:
            assert flat1389 is not None
            self.write(flat1389)
            return None
        else:
            fields1386 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1386) == 0:
                self.newline()
                for i1388, elem1387 in enumerate(fields1386):
                    if (i1388 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1387)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1398 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1398 is not None:
            assert flat1398 is not None
            self.write(flat1398)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1680 = _dollar_dollar.target_id
            else:
                _t1680 = None
            fields1390 = (_dollar_dollar.column_path, _t1680, _dollar_dollar.types,)
            assert fields1390 is not None
            unwrapped_fields1391 = fields1390
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1392 = unwrapped_fields1391[0]
            self.pretty_gnf_column_path(field1392)
            field1393 = unwrapped_fields1391[1]
            if field1393 is not None:
                self.newline()
                assert field1393 is not None
                opt_val1394 = field1393
                self.pretty_relation_id(opt_val1394)
            self.newline()
            self.write("[")
            field1395 = unwrapped_fields1391[2]
            for i1397, elem1396 in enumerate(field1395):
                if (i1397 > 0):
                    self.newline()
                self.pretty_type(elem1396)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1405 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1405 is not None:
            assert flat1405 is not None
            self.write(flat1405)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1681 = _dollar_dollar[0]
            else:
                _t1681 = None
            deconstruct_result1403 = _t1681
            if deconstruct_result1403 is not None:
                assert deconstruct_result1403 is not None
                unwrapped1404 = deconstruct_result1403
                self.write(self.format_string_value(unwrapped1404))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1682 = _dollar_dollar
                else:
                    _t1682 = None
                deconstruct_result1399 = _t1682
                if deconstruct_result1399 is not None:
                    assert deconstruct_result1399 is not None
                    unwrapped1400 = deconstruct_result1399
                    self.write("[")
                    self.indent()
                    for i1402, elem1401 in enumerate(unwrapped1400):
                        if (i1402 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1401))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1407 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1407 is not None:
            assert flat1407 is not None
            self.write(flat1407)
            return None
        else:
            fields1406 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1406))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1414 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1414 is not None:
            assert flat1414 is not None
            self.write(flat1414)
            return None
        else:
            _dollar_dollar = msg
            fields1408 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.returns_delta,)
            assert fields1408 is not None
            unwrapped_fields1409 = fields1408
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1410 = unwrapped_fields1409[0]
            self.pretty_iceberg_locator(field1410)
            self.newline()
            field1411 = unwrapped_fields1409[1]
            self.pretty_iceberg_catalog_config(field1411)
            self.newline()
            field1412 = unwrapped_fields1409[2]
            self.pretty_gnf_columns(field1412)
            self.newline()
            field1413 = unwrapped_fields1409[3]
            self.pretty_boolean_value(field1413)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1426 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1426 is not None:
            assert flat1426 is not None
            self.write(flat1426)
            return None
        else:
            _dollar_dollar = msg
            _t1683 = self.deconstruct_iceberg_locator_from_snapshot_optional(_dollar_dollar)
            _t1684 = self.deconstruct_iceberg_locator_to_snapshot_optional(_dollar_dollar)
            fields1415 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse, _t1683, _t1684,)
            assert fields1415 is not None
            unwrapped_fields1416 = fields1415
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("table_name")
            self.newline()
            field1417 = unwrapped_fields1416[0]
            self.write(self.format_string_value(field1417))
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("namespace")
            field1418 = unwrapped_fields1416[1]
            if not len(field1418) == 0:
                self.newline()
                for i1420, elem1419 in enumerate(field1418):
                    if (i1420 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1419))
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("warehouse")
            self.newline()
            field1421 = unwrapped_fields1416[2]
            self.write(self.format_string_value(field1421))
            self.dedent()
            self.write(")")
            field1422 = unwrapped_fields1416[3]
            if field1422 is not None:
                self.newline()
                assert field1422 is not None
                opt_val1423 = field1422
                self.pretty_iceberg_from_snapshot(opt_val1423)
            field1424 = unwrapped_fields1416[4]
            if field1424 is not None:
                self.newline()
                assert field1424 is not None
                opt_val1425 = field1424
                self.pretty_iceberg_to_snapshot(opt_val1425)
            self.dedent()
            self.write(")")

    def pretty_iceberg_from_snapshot(self, msg: str):
        flat1428 = self._try_flat(msg, self.pretty_iceberg_from_snapshot)
        if flat1428 is not None:
            assert flat1428 is not None
            self.write(flat1428)
            return None
        else:
            fields1427 = msg
            self.write("(from_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1427))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1430 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1430 is not None:
            assert flat1430 is not None
            self.write(flat1430)
            return None
        else:
            fields1429 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1429))
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1442 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1442 is not None:
            assert flat1442 is not None
            self.write(flat1442)
            return None
        else:
            _dollar_dollar = msg
            _t1685 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1431 = (_dollar_dollar.catalog_uri, _t1685, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1431 is not None
            unwrapped_fields1432 = fields1431
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("catalog_uri")
            self.newline()
            field1433 = unwrapped_fields1432[0]
            self.write(self.format_string_value(field1433))
            self.dedent()
            self.write(")")
            field1434 = unwrapped_fields1432[1]
            if field1434 is not None:
                self.newline()
                assert field1434 is not None
                opt_val1435 = field1434
                self.pretty_iceberg_catalog_config_scope(opt_val1435)
            self.newline()
            self.write("(")
            self.newline()
            self.write("properties")
            field1436 = unwrapped_fields1432[2]
            if not len(field1436) == 0:
                self.newline()
                for i1438, elem1437 in enumerate(field1436):
                    if (i1438 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1437)
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("auth_properties")
            field1439 = unwrapped_fields1432[3]
            if not len(field1439) == 0:
                self.newline()
                for i1441, elem1440 in enumerate(field1439):
                    if (i1441 > 0):
                        self.newline()
                    self.pretty_iceberg_masked_property_entry(elem1440)
            self.dedent()
            self.write(")")
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1444 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1444 is not None:
            assert flat1444 is not None
            self.write(flat1444)
            return None
        else:
            fields1443 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1443))
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1449 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1449 is not None:
            assert flat1449 is not None
            self.write(flat1449)
            return None
        else:
            _dollar_dollar = msg
            fields1445 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1445 is not None
            unwrapped_fields1446 = fields1445
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1447 = unwrapped_fields1446[0]
            self.write(self.format_string_value(field1447))
            self.newline()
            field1448 = unwrapped_fields1446[1]
            self.write(self.format_string_value(field1448))
            self.dedent()
            self.write(")")

    def pretty_iceberg_masked_property_entry(self, msg: tuple[str, str]):
        flat1454 = self._try_flat(msg, self.pretty_iceberg_masked_property_entry)
        if flat1454 is not None:
            assert flat1454 is not None
            self.write(flat1454)
            return None
        else:
            _dollar_dollar = msg
            _t1686 = self.mask_secret_value(_dollar_dollar)
            fields1450 = (_dollar_dollar[0], _t1686,)
            assert fields1450 is not None
            unwrapped_fields1451 = fields1450
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1452 = unwrapped_fields1451[0]
            self.write(self.format_string_value(field1452))
            self.newline()
            field1453 = unwrapped_fields1451[1]
            self.write(self.format_string_value(field1453))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1457 = self._try_flat(msg, self.pretty_undefine)
        if flat1457 is not None:
            assert flat1457 is not None
            self.write(flat1457)
            return None
        else:
            _dollar_dollar = msg
            fields1455 = _dollar_dollar.fragment_id
            assert fields1455 is not None
            unwrapped_fields1456 = fields1455
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1456)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1462 = self._try_flat(msg, self.pretty_context)
        if flat1462 is not None:
            assert flat1462 is not None
            self.write(flat1462)
            return None
        else:
            _dollar_dollar = msg
            fields1458 = _dollar_dollar.relations
            assert fields1458 is not None
            unwrapped_fields1459 = fields1458
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1459) == 0:
                self.newline()
                for i1461, elem1460 in enumerate(unwrapped_fields1459):
                    if (i1461 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1460)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1467 = self._try_flat(msg, self.pretty_snapshot)
        if flat1467 is not None:
            assert flat1467 is not None
            self.write(flat1467)
            return None
        else:
            _dollar_dollar = msg
            fields1463 = _dollar_dollar.mappings
            assert fields1463 is not None
            unwrapped_fields1464 = fields1463
            self.write("(snapshot")
            self.indent_sexp()
            if not len(unwrapped_fields1464) == 0:
                self.newline()
                for i1466, elem1465 in enumerate(unwrapped_fields1464):
                    if (i1466 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1465)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1472 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1472 is not None:
            assert flat1472 is not None
            self.write(flat1472)
            return None
        else:
            _dollar_dollar = msg
            fields1468 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1468 is not None
            unwrapped_fields1469 = fields1468
            field1470 = unwrapped_fields1469[0]
            self.pretty_edb_path(field1470)
            self.write(" ")
            field1471 = unwrapped_fields1469[1]
            self.pretty_relation_id(field1471)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1476 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1476 is not None:
            assert flat1476 is not None
            self.write(flat1476)
            return None
        else:
            fields1473 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1473) == 0:
                self.newline()
                for i1475, elem1474 in enumerate(fields1473):
                    if (i1475 > 0):
                        self.newline()
                    self.pretty_read(elem1474)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1487 = self._try_flat(msg, self.pretty_read)
        if flat1487 is not None:
            assert flat1487 is not None
            self.write(flat1487)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1687 = _dollar_dollar.demand
            else:
                _t1687 = None
            deconstruct_result1485 = _t1687
            if deconstruct_result1485 is not None:
                assert deconstruct_result1485 is not None
                unwrapped1486 = deconstruct_result1485
                self.pretty_demand(unwrapped1486)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1688 = _dollar_dollar.output
                else:
                    _t1688 = None
                deconstruct_result1483 = _t1688
                if deconstruct_result1483 is not None:
                    assert deconstruct_result1483 is not None
                    unwrapped1484 = deconstruct_result1483
                    self.pretty_output(unwrapped1484)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1689 = _dollar_dollar.what_if
                    else:
                        _t1689 = None
                    deconstruct_result1481 = _t1689
                    if deconstruct_result1481 is not None:
                        assert deconstruct_result1481 is not None
                        unwrapped1482 = deconstruct_result1481
                        self.pretty_what_if(unwrapped1482)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1690 = _dollar_dollar.abort
                        else:
                            _t1690 = None
                        deconstruct_result1479 = _t1690
                        if deconstruct_result1479 is not None:
                            assert deconstruct_result1479 is not None
                            unwrapped1480 = deconstruct_result1479
                            self.pretty_abort(unwrapped1480)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1691 = _dollar_dollar.export
                            else:
                                _t1691 = None
                            deconstruct_result1477 = _t1691
                            if deconstruct_result1477 is not None:
                                assert deconstruct_result1477 is not None
                                unwrapped1478 = deconstruct_result1477
                                self.pretty_export(unwrapped1478)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1490 = self._try_flat(msg, self.pretty_demand)
        if flat1490 is not None:
            assert flat1490 is not None
            self.write(flat1490)
            return None
        else:
            _dollar_dollar = msg
            fields1488 = _dollar_dollar.relation_id
            assert fields1488 is not None
            unwrapped_fields1489 = fields1488
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1489)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1495 = self._try_flat(msg, self.pretty_output)
        if flat1495 is not None:
            assert flat1495 is not None
            self.write(flat1495)
            return None
        else:
            _dollar_dollar = msg
            fields1491 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1491 is not None
            unwrapped_fields1492 = fields1491
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1493 = unwrapped_fields1492[0]
            self.pretty_name(field1493)
            self.newline()
            field1494 = unwrapped_fields1492[1]
            self.pretty_relation_id(field1494)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1500 = self._try_flat(msg, self.pretty_what_if)
        if flat1500 is not None:
            assert flat1500 is not None
            self.write(flat1500)
            return None
        else:
            _dollar_dollar = msg
            fields1496 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1496 is not None
            unwrapped_fields1497 = fields1496
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1498 = unwrapped_fields1497[0]
            self.pretty_name(field1498)
            self.newline()
            field1499 = unwrapped_fields1497[1]
            self.pretty_epoch(field1499)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1506 = self._try_flat(msg, self.pretty_abort)
        if flat1506 is not None:
            assert flat1506 is not None
            self.write(flat1506)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1692 = _dollar_dollar.name
            else:
                _t1692 = None
            fields1501 = (_t1692, _dollar_dollar.relation_id,)
            assert fields1501 is not None
            unwrapped_fields1502 = fields1501
            self.write("(abort")
            self.indent_sexp()
            field1503 = unwrapped_fields1502[0]
            if field1503 is not None:
                self.newline()
                assert field1503 is not None
                opt_val1504 = field1503
                self.pretty_name(opt_val1504)
            self.newline()
            field1505 = unwrapped_fields1502[1]
            self.pretty_relation_id(field1505)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1511 = self._try_flat(msg, self.pretty_export)
        if flat1511 is not None:
            assert flat1511 is not None
            self.write(flat1511)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1693 = _dollar_dollar.csv_config
            else:
                _t1693 = None
            deconstruct_result1509 = _t1693
            if deconstruct_result1509 is not None:
                assert deconstruct_result1509 is not None
                unwrapped1510 = deconstruct_result1509
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1510)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1694 = _dollar_dollar.iceberg_config
                else:
                    _t1694 = None
                deconstruct_result1507 = _t1694
                if deconstruct_result1507 is not None:
                    assert deconstruct_result1507 is not None
                    unwrapped1508 = deconstruct_result1507
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1508)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1522 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1522 is not None:
            assert flat1522 is not None
            self.write(flat1522)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1695 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1695 = None
            deconstruct_result1517 = _t1695
            if deconstruct_result1517 is not None:
                assert deconstruct_result1517 is not None
                unwrapped1518 = deconstruct_result1517
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1519 = unwrapped1518[0]
                self.pretty_export_csv_path(field1519)
                self.newline()
                field1520 = unwrapped1518[1]
                self.pretty_export_csv_source(field1520)
                self.newline()
                field1521 = unwrapped1518[2]
                self.pretty_csv_config(field1521)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1697 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1696 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1697,)
                else:
                    _t1696 = None
                deconstruct_result1512 = _t1696
                if deconstruct_result1512 is not None:
                    assert deconstruct_result1512 is not None
                    unwrapped1513 = deconstruct_result1512
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1514 = unwrapped1513[0]
                    self.pretty_export_csv_path(field1514)
                    self.newline()
                    field1515 = unwrapped1513[1]
                    self.pretty_export_csv_columns_list(field1515)
                    self.newline()
                    field1516 = unwrapped1513[2]
                    self.pretty_config_dict(field1516)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1524 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1524 is not None:
            assert flat1524 is not None
            self.write(flat1524)
            return None
        else:
            fields1523 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1523))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1531 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1531 is not None:
            assert flat1531 is not None
            self.write(flat1531)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1698 = _dollar_dollar.gnf_columns.columns
            else:
                _t1698 = None
            deconstruct_result1527 = _t1698
            if deconstruct_result1527 is not None:
                assert deconstruct_result1527 is not None
                unwrapped1528 = deconstruct_result1527
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1528) == 0:
                    self.newline()
                    for i1530, elem1529 in enumerate(unwrapped1528):
                        if (i1530 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1529)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1699 = _dollar_dollar.table_def
                else:
                    _t1699 = None
                deconstruct_result1525 = _t1699
                if deconstruct_result1525 is not None:
                    assert deconstruct_result1525 is not None
                    unwrapped1526 = deconstruct_result1525
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1526)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1536 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1536 is not None:
            assert flat1536 is not None
            self.write(flat1536)
            return None
        else:
            _dollar_dollar = msg
            fields1532 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1532 is not None
            unwrapped_fields1533 = fields1532
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1534 = unwrapped_fields1533[0]
            self.write(self.format_string_value(field1534))
            self.newline()
            field1535 = unwrapped_fields1533[1]
            self.pretty_relation_id(field1535)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1540 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1540 is not None:
            assert flat1540 is not None
            self.write(flat1540)
            return None
        else:
            fields1537 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1537) == 0:
                self.newline()
                for i1539, elem1538 in enumerate(fields1537):
                    if (i1539 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1538)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1554 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1554 is not None:
            assert flat1554 is not None
            self.write(flat1554)
            return None
        else:
            _dollar_dollar = msg
            _t1700 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1541 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, _dollar_dollar.columns, sorted(_dollar_dollar.table_properties.items()), _t1700,)
            assert fields1541 is not None
            unwrapped_fields1542 = fields1541
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1543 = unwrapped_fields1542[0]
            self.pretty_iceberg_locator(field1543)
            self.newline()
            field1544 = unwrapped_fields1542[1]
            self.pretty_iceberg_catalog_config(field1544)
            self.newline()
            self.write("(")
            self.newline()
            self.write("table_def")
            self.newline()
            field1545 = unwrapped_fields1542[2]
            self.pretty_relation_id(field1545)
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("columns")
            field1546 = unwrapped_fields1542[3]
            if not len(field1546) == 0:
                self.newline()
                for i1548, elem1547 in enumerate(field1546):
                    if (i1548 > 0):
                        self.newline()
                    self.pretty_export_gnf_column(elem1547)
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("table_properties")
            field1549 = unwrapped_fields1542[4]
            if not len(field1549) == 0:
                self.newline()
                for i1551, elem1550 in enumerate(field1549):
                    if (i1551 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1550)
            self.dedent()
            self.write(")")
            field1552 = unwrapped_fields1542[5]
            if field1552 is not None:
                self.newline()
                assert field1552 is not None
                opt_val1553 = field1552
                self.pretty_config_dict(opt_val1553)
            self.dedent()
            self.write(")")

    def pretty_export_gnf_column(self, msg: transactions_pb2.ExportGNFColumn):
        flat1559 = self._try_flat(msg, self.pretty_export_gnf_column)
        if flat1559 is not None:
            assert flat1559 is not None
            self.write(flat1559)
            return None
        else:
            _dollar_dollar = msg
            fields1555 = (_dollar_dollar.name, _dollar_dollar.nullable,)
            assert fields1555 is not None
            unwrapped_fields1556 = fields1555
            self.write("(gnf_column")
            self.indent_sexp()
            self.newline()
            field1557 = unwrapped_fields1556[0]
            self.write(self.format_string_value(field1557))
            self.newline()
            field1558 = unwrapped_fields1556[1]
            self.pretty_boolean_value(field1558)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1746 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1746)
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
        elif isinstance(msg, transactions_pb2.ExportGNFColumn):
            self.pretty_export_gnf_column(msg)
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
