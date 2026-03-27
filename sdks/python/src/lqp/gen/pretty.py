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
        _t1705 = logic_pb2.Value(int32_value=v)
        return _t1705

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1706 = logic_pb2.Value(int_value=v)
        return _t1706

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1707 = logic_pb2.Value(float_value=v)
        return _t1707

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1708 = logic_pb2.Value(string_value=v)
        return _t1708

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1709 = logic_pb2.Value(boolean_value=v)
        return _t1709

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1710 = logic_pb2.Value(uint128_value=v)
        return _t1710

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1711 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1711,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1712 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1712,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1713 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1713,))
        _t1714 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1714,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1715 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1715,))
        _t1716 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1716,))
        if msg.new_line != "":
            _t1717 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1717,))
        _t1718 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1718,))
        _t1719 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1719,))
        _t1720 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1720,))
        if msg.comment != "":
            _t1721 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1721,))
        for missing_string in msg.missing_strings:
            _t1722 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1722,))
        _t1723 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1723,))
        _t1724 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1724,))
        _t1725 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1725,))
        if msg.partition_size_mb != 0:
            _t1726 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1726,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1727 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1727,))
        _t1728 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1728,))
        _t1729 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1729,))
        _t1730 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1730,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1731 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1731,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1732 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1732,))
        _t1733 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1733,))
        _t1734 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1734,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1735 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1735,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1736 = self._make_value_string(msg.compression)
            result.append(("compression", _t1736,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1737 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1737,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1738 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1738,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1739 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1739,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1740 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1740,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1741 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1741,))
        return sorted(result)

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1742 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1743 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1744 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1744,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1745 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1745,))
        if msg.compression != "":
            _t1746 = self._make_value_string(msg.compression)
            result.append(("compression", _t1746,))
        if len(result) == 0:
            return None
        else:
            _t1747 = None
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
            _t1748 = None
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
        flat791 = self._try_flat(msg, self.pretty_transaction)
        if flat791 is not None:
            assert flat791 is not None
            self.write(flat791)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1564 = _dollar_dollar.configure
            else:
                _t1564 = None
            if _dollar_dollar.HasField("sync"):
                _t1565 = _dollar_dollar.sync
            else:
                _t1565 = None
            fields782 = (_t1564, _t1565, _dollar_dollar.epochs,)
            assert fields782 is not None
            unwrapped_fields783 = fields782
            self.write("(transaction")
            self.indent_sexp()
            field784 = unwrapped_fields783[0]
            if field784 is not None:
                self.newline()
                assert field784 is not None
                opt_val785 = field784
                self.pretty_configure(opt_val785)
            field786 = unwrapped_fields783[1]
            if field786 is not None:
                self.newline()
                assert field786 is not None
                opt_val787 = field786
                self.pretty_sync(opt_val787)
            field788 = unwrapped_fields783[2]
            if not len(field788) == 0:
                self.newline()
                for i790, elem789 in enumerate(field788):
                    if (i790 > 0):
                        self.newline()
                    self.pretty_epoch(elem789)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat794 = self._try_flat(msg, self.pretty_configure)
        if flat794 is not None:
            assert flat794 is not None
            self.write(flat794)
            return None
        else:
            _dollar_dollar = msg
            _t1566 = self.deconstruct_configure(_dollar_dollar)
            fields792 = _t1566
            assert fields792 is not None
            unwrapped_fields793 = fields792
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields793)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat798 = self._try_flat(msg, self.pretty_config_dict)
        if flat798 is not None:
            assert flat798 is not None
            self.write(flat798)
            return None
        else:
            fields795 = msg
            self.write("{")
            self.indent()
            if not len(fields795) == 0:
                self.newline()
                for i797, elem796 in enumerate(fields795):
                    if (i797 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem796)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat803 = self._try_flat(msg, self.pretty_config_key_value)
        if flat803 is not None:
            assert flat803 is not None
            self.write(flat803)
            return None
        else:
            _dollar_dollar = msg
            fields799 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields799 is not None
            unwrapped_fields800 = fields799
            self.write(":")
            field801 = unwrapped_fields800[0]
            self.write(field801)
            self.write(" ")
            field802 = unwrapped_fields800[1]
            self.pretty_raw_value(field802)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat829 = self._try_flat(msg, self.pretty_raw_value)
        if flat829 is not None:
            assert flat829 is not None
            self.write(flat829)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1567 = _dollar_dollar.date_value
            else:
                _t1567 = None
            deconstruct_result827 = _t1567
            if deconstruct_result827 is not None:
                assert deconstruct_result827 is not None
                unwrapped828 = deconstruct_result827
                self.pretty_raw_date(unwrapped828)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1568 = _dollar_dollar.datetime_value
                else:
                    _t1568 = None
                deconstruct_result825 = _t1568
                if deconstruct_result825 is not None:
                    assert deconstruct_result825 is not None
                    unwrapped826 = deconstruct_result825
                    self.pretty_raw_datetime(unwrapped826)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1569 = _dollar_dollar.string_value
                    else:
                        _t1569 = None
                    deconstruct_result823 = _t1569
                    if deconstruct_result823 is not None:
                        assert deconstruct_result823 is not None
                        unwrapped824 = deconstruct_result823
                        self.write(self.format_string_value(unwrapped824))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1570 = _dollar_dollar.int32_value
                        else:
                            _t1570 = None
                        deconstruct_result821 = _t1570
                        if deconstruct_result821 is not None:
                            assert deconstruct_result821 is not None
                            unwrapped822 = deconstruct_result821
                            self.write((str(unwrapped822) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1571 = _dollar_dollar.int_value
                            else:
                                _t1571 = None
                            deconstruct_result819 = _t1571
                            if deconstruct_result819 is not None:
                                assert deconstruct_result819 is not None
                                unwrapped820 = deconstruct_result819
                                self.write(str(unwrapped820))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1572 = _dollar_dollar.float32_value
                                else:
                                    _t1572 = None
                                deconstruct_result817 = _t1572
                                if deconstruct_result817 is not None:
                                    assert deconstruct_result817 is not None
                                    unwrapped818 = deconstruct_result817
                                    self.write(self.format_float32_literal(unwrapped818))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1573 = _dollar_dollar.float_value
                                    else:
                                        _t1573 = None
                                    deconstruct_result815 = _t1573
                                    if deconstruct_result815 is not None:
                                        assert deconstruct_result815 is not None
                                        unwrapped816 = deconstruct_result815
                                        self.write(str(unwrapped816))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1574 = _dollar_dollar.uint32_value
                                        else:
                                            _t1574 = None
                                        deconstruct_result813 = _t1574
                                        if deconstruct_result813 is not None:
                                            assert deconstruct_result813 is not None
                                            unwrapped814 = deconstruct_result813
                                            self.write((str(unwrapped814) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1575 = _dollar_dollar.uint128_value
                                            else:
                                                _t1575 = None
                                            deconstruct_result811 = _t1575
                                            if deconstruct_result811 is not None:
                                                assert deconstruct_result811 is not None
                                                unwrapped812 = deconstruct_result811
                                                self.write(self.format_uint128(unwrapped812))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1576 = _dollar_dollar.int128_value
                                                else:
                                                    _t1576 = None
                                                deconstruct_result809 = _t1576
                                                if deconstruct_result809 is not None:
                                                    assert deconstruct_result809 is not None
                                                    unwrapped810 = deconstruct_result809
                                                    self.write(self.format_int128(unwrapped810))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1577 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1577 = None
                                                    deconstruct_result807 = _t1577
                                                    if deconstruct_result807 is not None:
                                                        assert deconstruct_result807 is not None
                                                        unwrapped808 = deconstruct_result807
                                                        self.write(self.format_decimal(unwrapped808))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1578 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1578 = None
                                                        deconstruct_result805 = _t1578
                                                        if deconstruct_result805 is not None:
                                                            assert deconstruct_result805 is not None
                                                            unwrapped806 = deconstruct_result805
                                                            self.pretty_boolean_value(unwrapped806)
                                                        else:
                                                            fields804 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat835 = self._try_flat(msg, self.pretty_raw_date)
        if flat835 is not None:
            assert flat835 is not None
            self.write(flat835)
            return None
        else:
            _dollar_dollar = msg
            fields830 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields830 is not None
            unwrapped_fields831 = fields830
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field832 = unwrapped_fields831[0]
            self.write(str(field832))
            self.newline()
            field833 = unwrapped_fields831[1]
            self.write(str(field833))
            self.newline()
            field834 = unwrapped_fields831[2]
            self.write(str(field834))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat846 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat846 is not None:
            assert flat846 is not None
            self.write(flat846)
            return None
        else:
            _dollar_dollar = msg
            fields836 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields836 is not None
            unwrapped_fields837 = fields836
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field838 = unwrapped_fields837[0]
            self.write(str(field838))
            self.newline()
            field839 = unwrapped_fields837[1]
            self.write(str(field839))
            self.newline()
            field840 = unwrapped_fields837[2]
            self.write(str(field840))
            self.newline()
            field841 = unwrapped_fields837[3]
            self.write(str(field841))
            self.newline()
            field842 = unwrapped_fields837[4]
            self.write(str(field842))
            self.newline()
            field843 = unwrapped_fields837[5]
            self.write(str(field843))
            field844 = unwrapped_fields837[6]
            if field844 is not None:
                self.newline()
                assert field844 is not None
                opt_val845 = field844
                self.write(str(opt_val845))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1579 = ()
        else:
            _t1579 = None
        deconstruct_result849 = _t1579
        if deconstruct_result849 is not None:
            assert deconstruct_result849 is not None
            unwrapped850 = deconstruct_result849
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1580 = ()
            else:
                _t1580 = None
            deconstruct_result847 = _t1580
            if deconstruct_result847 is not None:
                assert deconstruct_result847 is not None
                unwrapped848 = deconstruct_result847
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat855 = self._try_flat(msg, self.pretty_sync)
        if flat855 is not None:
            assert flat855 is not None
            self.write(flat855)
            return None
        else:
            _dollar_dollar = msg
            fields851 = _dollar_dollar.fragments
            assert fields851 is not None
            unwrapped_fields852 = fields851
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields852) == 0:
                self.newline()
                for i854, elem853 in enumerate(unwrapped_fields852):
                    if (i854 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem853)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat858 = self._try_flat(msg, self.pretty_fragment_id)
        if flat858 is not None:
            assert flat858 is not None
            self.write(flat858)
            return None
        else:
            _dollar_dollar = msg
            fields856 = self.fragment_id_to_string(_dollar_dollar)
            assert fields856 is not None
            unwrapped_fields857 = fields856
            self.write(":")
            self.write(unwrapped_fields857)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat865 = self._try_flat(msg, self.pretty_epoch)
        if flat865 is not None:
            assert flat865 is not None
            self.write(flat865)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1581 = _dollar_dollar.writes
            else:
                _t1581 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1582 = _dollar_dollar.reads
            else:
                _t1582 = None
            fields859 = (_t1581, _t1582,)
            assert fields859 is not None
            unwrapped_fields860 = fields859
            self.write("(epoch")
            self.indent_sexp()
            field861 = unwrapped_fields860[0]
            if field861 is not None:
                self.newline()
                assert field861 is not None
                opt_val862 = field861
                self.pretty_epoch_writes(opt_val862)
            field863 = unwrapped_fields860[1]
            if field863 is not None:
                self.newline()
                assert field863 is not None
                opt_val864 = field863
                self.pretty_epoch_reads(opt_val864)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat869 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat869 is not None:
            assert flat869 is not None
            self.write(flat869)
            return None
        else:
            fields866 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields866) == 0:
                self.newline()
                for i868, elem867 in enumerate(fields866):
                    if (i868 > 0):
                        self.newline()
                    self.pretty_write(elem867)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat878 = self._try_flat(msg, self.pretty_write)
        if flat878 is not None:
            assert flat878 is not None
            self.write(flat878)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1583 = _dollar_dollar.define
            else:
                _t1583 = None
            deconstruct_result876 = _t1583
            if deconstruct_result876 is not None:
                assert deconstruct_result876 is not None
                unwrapped877 = deconstruct_result876
                self.pretty_define(unwrapped877)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1584 = _dollar_dollar.undefine
                else:
                    _t1584 = None
                deconstruct_result874 = _t1584
                if deconstruct_result874 is not None:
                    assert deconstruct_result874 is not None
                    unwrapped875 = deconstruct_result874
                    self.pretty_undefine(unwrapped875)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1585 = _dollar_dollar.context
                    else:
                        _t1585 = None
                    deconstruct_result872 = _t1585
                    if deconstruct_result872 is not None:
                        assert deconstruct_result872 is not None
                        unwrapped873 = deconstruct_result872
                        self.pretty_context(unwrapped873)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1586 = _dollar_dollar.snapshot
                        else:
                            _t1586 = None
                        deconstruct_result870 = _t1586
                        if deconstruct_result870 is not None:
                            assert deconstruct_result870 is not None
                            unwrapped871 = deconstruct_result870
                            self.pretty_snapshot(unwrapped871)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat881 = self._try_flat(msg, self.pretty_define)
        if flat881 is not None:
            assert flat881 is not None
            self.write(flat881)
            return None
        else:
            _dollar_dollar = msg
            fields879 = _dollar_dollar.fragment
            assert fields879 is not None
            unwrapped_fields880 = fields879
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields880)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat888 = self._try_flat(msg, self.pretty_fragment)
        if flat888 is not None:
            assert flat888 is not None
            self.write(flat888)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields882 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields882 is not None
            unwrapped_fields883 = fields882
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field884 = unwrapped_fields883[0]
            self.pretty_new_fragment_id(field884)
            field885 = unwrapped_fields883[1]
            if not len(field885) == 0:
                self.newline()
                for i887, elem886 in enumerate(field885):
                    if (i887 > 0):
                        self.newline()
                    self.pretty_declaration(elem886)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat890 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat890 is not None:
            assert flat890 is not None
            self.write(flat890)
            return None
        else:
            fields889 = msg
            self.pretty_fragment_id(fields889)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat899 = self._try_flat(msg, self.pretty_declaration)
        if flat899 is not None:
            assert flat899 is not None
            self.write(flat899)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1587 = getattr(_dollar_dollar, 'def')
            else:
                _t1587 = None
            deconstruct_result897 = _t1587
            if deconstruct_result897 is not None:
                assert deconstruct_result897 is not None
                unwrapped898 = deconstruct_result897
                self.pretty_def(unwrapped898)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1588 = _dollar_dollar.algorithm
                else:
                    _t1588 = None
                deconstruct_result895 = _t1588
                if deconstruct_result895 is not None:
                    assert deconstruct_result895 is not None
                    unwrapped896 = deconstruct_result895
                    self.pretty_algorithm(unwrapped896)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1589 = _dollar_dollar.constraint
                    else:
                        _t1589 = None
                    deconstruct_result893 = _t1589
                    if deconstruct_result893 is not None:
                        assert deconstruct_result893 is not None
                        unwrapped894 = deconstruct_result893
                        self.pretty_constraint(unwrapped894)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1590 = _dollar_dollar.data
                        else:
                            _t1590 = None
                        deconstruct_result891 = _t1590
                        if deconstruct_result891 is not None:
                            assert deconstruct_result891 is not None
                            unwrapped892 = deconstruct_result891
                            self.pretty_data(unwrapped892)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat906 = self._try_flat(msg, self.pretty_def)
        if flat906 is not None:
            assert flat906 is not None
            self.write(flat906)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1591 = _dollar_dollar.attrs
            else:
                _t1591 = None
            fields900 = (_dollar_dollar.name, _dollar_dollar.body, _t1591,)
            assert fields900 is not None
            unwrapped_fields901 = fields900
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field902 = unwrapped_fields901[0]
            self.pretty_relation_id(field902)
            self.newline()
            field903 = unwrapped_fields901[1]
            self.pretty_abstraction(field903)
            field904 = unwrapped_fields901[2]
            if field904 is not None:
                self.newline()
                assert field904 is not None
                opt_val905 = field904
                self.pretty_attrs(opt_val905)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat911 = self._try_flat(msg, self.pretty_relation_id)
        if flat911 is not None:
            assert flat911 is not None
            self.write(flat911)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1593 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1592 = _t1593
            else:
                _t1592 = None
            deconstruct_result909 = _t1592
            if deconstruct_result909 is not None:
                assert deconstruct_result909 is not None
                unwrapped910 = deconstruct_result909
                self.write(":")
                self.write(unwrapped910)
            else:
                _dollar_dollar = msg
                _t1594 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result907 = _t1594
                if deconstruct_result907 is not None:
                    assert deconstruct_result907 is not None
                    unwrapped908 = deconstruct_result907
                    self.write(self.format_uint128(unwrapped908))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat916 = self._try_flat(msg, self.pretty_abstraction)
        if flat916 is not None:
            assert flat916 is not None
            self.write(flat916)
            return None
        else:
            _dollar_dollar = msg
            _t1595 = self.deconstruct_bindings(_dollar_dollar)
            fields912 = (_t1595, _dollar_dollar.value,)
            assert fields912 is not None
            unwrapped_fields913 = fields912
            self.write("(")
            self.indent()
            field914 = unwrapped_fields913[0]
            self.pretty_bindings(field914)
            self.newline()
            field915 = unwrapped_fields913[1]
            self.pretty_formula(field915)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat924 = self._try_flat(msg, self.pretty_bindings)
        if flat924 is not None:
            assert flat924 is not None
            self.write(flat924)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1596 = _dollar_dollar[1]
            else:
                _t1596 = None
            fields917 = (_dollar_dollar[0], _t1596,)
            assert fields917 is not None
            unwrapped_fields918 = fields917
            self.write("[")
            self.indent()
            field919 = unwrapped_fields918[0]
            for i921, elem920 in enumerate(field919):
                if (i921 > 0):
                    self.newline()
                self.pretty_binding(elem920)
            field922 = unwrapped_fields918[1]
            if field922 is not None:
                self.newline()
                assert field922 is not None
                opt_val923 = field922
                self.pretty_value_bindings(opt_val923)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat929 = self._try_flat(msg, self.pretty_binding)
        if flat929 is not None:
            assert flat929 is not None
            self.write(flat929)
            return None
        else:
            _dollar_dollar = msg
            fields925 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields925 is not None
            unwrapped_fields926 = fields925
            field927 = unwrapped_fields926[0]
            self.write(field927)
            self.write("::")
            field928 = unwrapped_fields926[1]
            self.pretty_type(field928)

    def pretty_type(self, msg: logic_pb2.Type):
        flat958 = self._try_flat(msg, self.pretty_type)
        if flat958 is not None:
            assert flat958 is not None
            self.write(flat958)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1597 = _dollar_dollar.unspecified_type
            else:
                _t1597 = None
            deconstruct_result956 = _t1597
            if deconstruct_result956 is not None:
                assert deconstruct_result956 is not None
                unwrapped957 = deconstruct_result956
                self.pretty_unspecified_type(unwrapped957)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1598 = _dollar_dollar.string_type
                else:
                    _t1598 = None
                deconstruct_result954 = _t1598
                if deconstruct_result954 is not None:
                    assert deconstruct_result954 is not None
                    unwrapped955 = deconstruct_result954
                    self.pretty_string_type(unwrapped955)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1599 = _dollar_dollar.int_type
                    else:
                        _t1599 = None
                    deconstruct_result952 = _t1599
                    if deconstruct_result952 is not None:
                        assert deconstruct_result952 is not None
                        unwrapped953 = deconstruct_result952
                        self.pretty_int_type(unwrapped953)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1600 = _dollar_dollar.float_type
                        else:
                            _t1600 = None
                        deconstruct_result950 = _t1600
                        if deconstruct_result950 is not None:
                            assert deconstruct_result950 is not None
                            unwrapped951 = deconstruct_result950
                            self.pretty_float_type(unwrapped951)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1601 = _dollar_dollar.uint128_type
                            else:
                                _t1601 = None
                            deconstruct_result948 = _t1601
                            if deconstruct_result948 is not None:
                                assert deconstruct_result948 is not None
                                unwrapped949 = deconstruct_result948
                                self.pretty_uint128_type(unwrapped949)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1602 = _dollar_dollar.int128_type
                                else:
                                    _t1602 = None
                                deconstruct_result946 = _t1602
                                if deconstruct_result946 is not None:
                                    assert deconstruct_result946 is not None
                                    unwrapped947 = deconstruct_result946
                                    self.pretty_int128_type(unwrapped947)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1603 = _dollar_dollar.date_type
                                    else:
                                        _t1603 = None
                                    deconstruct_result944 = _t1603
                                    if deconstruct_result944 is not None:
                                        assert deconstruct_result944 is not None
                                        unwrapped945 = deconstruct_result944
                                        self.pretty_date_type(unwrapped945)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1604 = _dollar_dollar.datetime_type
                                        else:
                                            _t1604 = None
                                        deconstruct_result942 = _t1604
                                        if deconstruct_result942 is not None:
                                            assert deconstruct_result942 is not None
                                            unwrapped943 = deconstruct_result942
                                            self.pretty_datetime_type(unwrapped943)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1605 = _dollar_dollar.missing_type
                                            else:
                                                _t1605 = None
                                            deconstruct_result940 = _t1605
                                            if deconstruct_result940 is not None:
                                                assert deconstruct_result940 is not None
                                                unwrapped941 = deconstruct_result940
                                                self.pretty_missing_type(unwrapped941)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1606 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1606 = None
                                                deconstruct_result938 = _t1606
                                                if deconstruct_result938 is not None:
                                                    assert deconstruct_result938 is not None
                                                    unwrapped939 = deconstruct_result938
                                                    self.pretty_decimal_type(unwrapped939)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1607 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1607 = None
                                                    deconstruct_result936 = _t1607
                                                    if deconstruct_result936 is not None:
                                                        assert deconstruct_result936 is not None
                                                        unwrapped937 = deconstruct_result936
                                                        self.pretty_boolean_type(unwrapped937)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1608 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1608 = None
                                                        deconstruct_result934 = _t1608
                                                        if deconstruct_result934 is not None:
                                                            assert deconstruct_result934 is not None
                                                            unwrapped935 = deconstruct_result934
                                                            self.pretty_int32_type(unwrapped935)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1609 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1609 = None
                                                            deconstruct_result932 = _t1609
                                                            if deconstruct_result932 is not None:
                                                                assert deconstruct_result932 is not None
                                                                unwrapped933 = deconstruct_result932
                                                                self.pretty_float32_type(unwrapped933)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1610 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1610 = None
                                                                deconstruct_result930 = _t1610
                                                                if deconstruct_result930 is not None:
                                                                    assert deconstruct_result930 is not None
                                                                    unwrapped931 = deconstruct_result930
                                                                    self.pretty_uint32_type(unwrapped931)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields959 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields960 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields961 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields962 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields963 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields964 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields965 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields966 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields967 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat972 = self._try_flat(msg, self.pretty_decimal_type)
        if flat972 is not None:
            assert flat972 is not None
            self.write(flat972)
            return None
        else:
            _dollar_dollar = msg
            fields968 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields968 is not None
            unwrapped_fields969 = fields968
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field970 = unwrapped_fields969[0]
            self.write(str(field970))
            self.newline()
            field971 = unwrapped_fields969[1]
            self.write(str(field971))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields973 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields974 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields975 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields976 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat980 = self._try_flat(msg, self.pretty_value_bindings)
        if flat980 is not None:
            assert flat980 is not None
            self.write(flat980)
            return None
        else:
            fields977 = msg
            self.write("|")
            if not len(fields977) == 0:
                self.write(" ")
                for i979, elem978 in enumerate(fields977):
                    if (i979 > 0):
                        self.newline()
                    self.pretty_binding(elem978)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1007 = self._try_flat(msg, self.pretty_formula)
        if flat1007 is not None:
            assert flat1007 is not None
            self.write(flat1007)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1611 = _dollar_dollar.conjunction
            else:
                _t1611 = None
            deconstruct_result1005 = _t1611
            if deconstruct_result1005 is not None:
                assert deconstruct_result1005 is not None
                unwrapped1006 = deconstruct_result1005
                self.pretty_true(unwrapped1006)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1612 = _dollar_dollar.disjunction
                else:
                    _t1612 = None
                deconstruct_result1003 = _t1612
                if deconstruct_result1003 is not None:
                    assert deconstruct_result1003 is not None
                    unwrapped1004 = deconstruct_result1003
                    self.pretty_false(unwrapped1004)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1613 = _dollar_dollar.exists
                    else:
                        _t1613 = None
                    deconstruct_result1001 = _t1613
                    if deconstruct_result1001 is not None:
                        assert deconstruct_result1001 is not None
                        unwrapped1002 = deconstruct_result1001
                        self.pretty_exists(unwrapped1002)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1614 = _dollar_dollar.reduce
                        else:
                            _t1614 = None
                        deconstruct_result999 = _t1614
                        if deconstruct_result999 is not None:
                            assert deconstruct_result999 is not None
                            unwrapped1000 = deconstruct_result999
                            self.pretty_reduce(unwrapped1000)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1615 = _dollar_dollar.conjunction
                            else:
                                _t1615 = None
                            deconstruct_result997 = _t1615
                            if deconstruct_result997 is not None:
                                assert deconstruct_result997 is not None
                                unwrapped998 = deconstruct_result997
                                self.pretty_conjunction(unwrapped998)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1616 = _dollar_dollar.disjunction
                                else:
                                    _t1616 = None
                                deconstruct_result995 = _t1616
                                if deconstruct_result995 is not None:
                                    assert deconstruct_result995 is not None
                                    unwrapped996 = deconstruct_result995
                                    self.pretty_disjunction(unwrapped996)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1617 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1617 = None
                                    deconstruct_result993 = _t1617
                                    if deconstruct_result993 is not None:
                                        assert deconstruct_result993 is not None
                                        unwrapped994 = deconstruct_result993
                                        self.pretty_not(unwrapped994)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1618 = _dollar_dollar.ffi
                                        else:
                                            _t1618 = None
                                        deconstruct_result991 = _t1618
                                        if deconstruct_result991 is not None:
                                            assert deconstruct_result991 is not None
                                            unwrapped992 = deconstruct_result991
                                            self.pretty_ffi(unwrapped992)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1619 = _dollar_dollar.atom
                                            else:
                                                _t1619 = None
                                            deconstruct_result989 = _t1619
                                            if deconstruct_result989 is not None:
                                                assert deconstruct_result989 is not None
                                                unwrapped990 = deconstruct_result989
                                                self.pretty_atom(unwrapped990)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1620 = _dollar_dollar.pragma
                                                else:
                                                    _t1620 = None
                                                deconstruct_result987 = _t1620
                                                if deconstruct_result987 is not None:
                                                    assert deconstruct_result987 is not None
                                                    unwrapped988 = deconstruct_result987
                                                    self.pretty_pragma(unwrapped988)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1621 = _dollar_dollar.primitive
                                                    else:
                                                        _t1621 = None
                                                    deconstruct_result985 = _t1621
                                                    if deconstruct_result985 is not None:
                                                        assert deconstruct_result985 is not None
                                                        unwrapped986 = deconstruct_result985
                                                        self.pretty_primitive(unwrapped986)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1622 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1622 = None
                                                        deconstruct_result983 = _t1622
                                                        if deconstruct_result983 is not None:
                                                            assert deconstruct_result983 is not None
                                                            unwrapped984 = deconstruct_result983
                                                            self.pretty_rel_atom(unwrapped984)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1623 = _dollar_dollar.cast
                                                            else:
                                                                _t1623 = None
                                                            deconstruct_result981 = _t1623
                                                            if deconstruct_result981 is not None:
                                                                assert deconstruct_result981 is not None
                                                                unwrapped982 = deconstruct_result981
                                                                self.pretty_cast(unwrapped982)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields1008 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1009 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1014 = self._try_flat(msg, self.pretty_exists)
        if flat1014 is not None:
            assert flat1014 is not None
            self.write(flat1014)
            return None
        else:
            _dollar_dollar = msg
            _t1624 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1010 = (_t1624, _dollar_dollar.body.value,)
            assert fields1010 is not None
            unwrapped_fields1011 = fields1010
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1012 = unwrapped_fields1011[0]
            self.pretty_bindings(field1012)
            self.newline()
            field1013 = unwrapped_fields1011[1]
            self.pretty_formula(field1013)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1020 = self._try_flat(msg, self.pretty_reduce)
        if flat1020 is not None:
            assert flat1020 is not None
            self.write(flat1020)
            return None
        else:
            _dollar_dollar = msg
            fields1015 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1015 is not None
            unwrapped_fields1016 = fields1015
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1017 = unwrapped_fields1016[0]
            self.pretty_abstraction(field1017)
            self.newline()
            field1018 = unwrapped_fields1016[1]
            self.pretty_abstraction(field1018)
            self.newline()
            field1019 = unwrapped_fields1016[2]
            self.pretty_terms(field1019)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1024 = self._try_flat(msg, self.pretty_terms)
        if flat1024 is not None:
            assert flat1024 is not None
            self.write(flat1024)
            return None
        else:
            fields1021 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1021) == 0:
                self.newline()
                for i1023, elem1022 in enumerate(fields1021):
                    if (i1023 > 0):
                        self.newline()
                    self.pretty_term(elem1022)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1029 = self._try_flat(msg, self.pretty_term)
        if flat1029 is not None:
            assert flat1029 is not None
            self.write(flat1029)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1625 = _dollar_dollar.var
            else:
                _t1625 = None
            deconstruct_result1027 = _t1625
            if deconstruct_result1027 is not None:
                assert deconstruct_result1027 is not None
                unwrapped1028 = deconstruct_result1027
                self.pretty_var(unwrapped1028)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1626 = _dollar_dollar.constant
                else:
                    _t1626 = None
                deconstruct_result1025 = _t1626
                if deconstruct_result1025 is not None:
                    assert deconstruct_result1025 is not None
                    unwrapped1026 = deconstruct_result1025
                    self.pretty_value(unwrapped1026)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1032 = self._try_flat(msg, self.pretty_var)
        if flat1032 is not None:
            assert flat1032 is not None
            self.write(flat1032)
            return None
        else:
            _dollar_dollar = msg
            fields1030 = _dollar_dollar.name
            assert fields1030 is not None
            unwrapped_fields1031 = fields1030
            self.write(unwrapped_fields1031)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1058 = self._try_flat(msg, self.pretty_value)
        if flat1058 is not None:
            assert flat1058 is not None
            self.write(flat1058)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1627 = _dollar_dollar.date_value
            else:
                _t1627 = None
            deconstruct_result1056 = _t1627
            if deconstruct_result1056 is not None:
                assert deconstruct_result1056 is not None
                unwrapped1057 = deconstruct_result1056
                self.pretty_date(unwrapped1057)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1628 = _dollar_dollar.datetime_value
                else:
                    _t1628 = None
                deconstruct_result1054 = _t1628
                if deconstruct_result1054 is not None:
                    assert deconstruct_result1054 is not None
                    unwrapped1055 = deconstruct_result1054
                    self.pretty_datetime(unwrapped1055)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1629 = _dollar_dollar.string_value
                    else:
                        _t1629 = None
                    deconstruct_result1052 = _t1629
                    if deconstruct_result1052 is not None:
                        assert deconstruct_result1052 is not None
                        unwrapped1053 = deconstruct_result1052
                        self.write(self.format_string_value(unwrapped1053))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1630 = _dollar_dollar.int32_value
                        else:
                            _t1630 = None
                        deconstruct_result1050 = _t1630
                        if deconstruct_result1050 is not None:
                            assert deconstruct_result1050 is not None
                            unwrapped1051 = deconstruct_result1050
                            self.write((str(unwrapped1051) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1631 = _dollar_dollar.int_value
                            else:
                                _t1631 = None
                            deconstruct_result1048 = _t1631
                            if deconstruct_result1048 is not None:
                                assert deconstruct_result1048 is not None
                                unwrapped1049 = deconstruct_result1048
                                self.write(str(unwrapped1049))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1632 = _dollar_dollar.float32_value
                                else:
                                    _t1632 = None
                                deconstruct_result1046 = _t1632
                                if deconstruct_result1046 is not None:
                                    assert deconstruct_result1046 is not None
                                    unwrapped1047 = deconstruct_result1046
                                    self.write(self.format_float32_literal(unwrapped1047))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1633 = _dollar_dollar.float_value
                                    else:
                                        _t1633 = None
                                    deconstruct_result1044 = _t1633
                                    if deconstruct_result1044 is not None:
                                        assert deconstruct_result1044 is not None
                                        unwrapped1045 = deconstruct_result1044
                                        self.write(str(unwrapped1045))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1634 = _dollar_dollar.uint32_value
                                        else:
                                            _t1634 = None
                                        deconstruct_result1042 = _t1634
                                        if deconstruct_result1042 is not None:
                                            assert deconstruct_result1042 is not None
                                            unwrapped1043 = deconstruct_result1042
                                            self.write((str(unwrapped1043) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1635 = _dollar_dollar.uint128_value
                                            else:
                                                _t1635 = None
                                            deconstruct_result1040 = _t1635
                                            if deconstruct_result1040 is not None:
                                                assert deconstruct_result1040 is not None
                                                unwrapped1041 = deconstruct_result1040
                                                self.write(self.format_uint128(unwrapped1041))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1636 = _dollar_dollar.int128_value
                                                else:
                                                    _t1636 = None
                                                deconstruct_result1038 = _t1636
                                                if deconstruct_result1038 is not None:
                                                    assert deconstruct_result1038 is not None
                                                    unwrapped1039 = deconstruct_result1038
                                                    self.write(self.format_int128(unwrapped1039))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1637 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1637 = None
                                                    deconstruct_result1036 = _t1637
                                                    if deconstruct_result1036 is not None:
                                                        assert deconstruct_result1036 is not None
                                                        unwrapped1037 = deconstruct_result1036
                                                        self.write(self.format_decimal(unwrapped1037))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1638 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1638 = None
                                                        deconstruct_result1034 = _t1638
                                                        if deconstruct_result1034 is not None:
                                                            assert deconstruct_result1034 is not None
                                                            unwrapped1035 = deconstruct_result1034
                                                            self.pretty_boolean_value(unwrapped1035)
                                                        else:
                                                            fields1033 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1064 = self._try_flat(msg, self.pretty_date)
        if flat1064 is not None:
            assert flat1064 is not None
            self.write(flat1064)
            return None
        else:
            _dollar_dollar = msg
            fields1059 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1059 is not None
            unwrapped_fields1060 = fields1059
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1061 = unwrapped_fields1060[0]
            self.write(str(field1061))
            self.newline()
            field1062 = unwrapped_fields1060[1]
            self.write(str(field1062))
            self.newline()
            field1063 = unwrapped_fields1060[2]
            self.write(str(field1063))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1075 = self._try_flat(msg, self.pretty_datetime)
        if flat1075 is not None:
            assert flat1075 is not None
            self.write(flat1075)
            return None
        else:
            _dollar_dollar = msg
            fields1065 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1065 is not None
            unwrapped_fields1066 = fields1065
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1067 = unwrapped_fields1066[0]
            self.write(str(field1067))
            self.newline()
            field1068 = unwrapped_fields1066[1]
            self.write(str(field1068))
            self.newline()
            field1069 = unwrapped_fields1066[2]
            self.write(str(field1069))
            self.newline()
            field1070 = unwrapped_fields1066[3]
            self.write(str(field1070))
            self.newline()
            field1071 = unwrapped_fields1066[4]
            self.write(str(field1071))
            self.newline()
            field1072 = unwrapped_fields1066[5]
            self.write(str(field1072))
            field1073 = unwrapped_fields1066[6]
            if field1073 is not None:
                self.newline()
                assert field1073 is not None
                opt_val1074 = field1073
                self.write(str(opt_val1074))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1080 = self._try_flat(msg, self.pretty_conjunction)
        if flat1080 is not None:
            assert flat1080 is not None
            self.write(flat1080)
            return None
        else:
            _dollar_dollar = msg
            fields1076 = _dollar_dollar.args
            assert fields1076 is not None
            unwrapped_fields1077 = fields1076
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1077) == 0:
                self.newline()
                for i1079, elem1078 in enumerate(unwrapped_fields1077):
                    if (i1079 > 0):
                        self.newline()
                    self.pretty_formula(elem1078)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1085 = self._try_flat(msg, self.pretty_disjunction)
        if flat1085 is not None:
            assert flat1085 is not None
            self.write(flat1085)
            return None
        else:
            _dollar_dollar = msg
            fields1081 = _dollar_dollar.args
            assert fields1081 is not None
            unwrapped_fields1082 = fields1081
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1082) == 0:
                self.newline()
                for i1084, elem1083 in enumerate(unwrapped_fields1082):
                    if (i1084 > 0):
                        self.newline()
                    self.pretty_formula(elem1083)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1088 = self._try_flat(msg, self.pretty_not)
        if flat1088 is not None:
            assert flat1088 is not None
            self.write(flat1088)
            return None
        else:
            _dollar_dollar = msg
            fields1086 = _dollar_dollar.arg
            assert fields1086 is not None
            unwrapped_fields1087 = fields1086
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1087)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1094 = self._try_flat(msg, self.pretty_ffi)
        if flat1094 is not None:
            assert flat1094 is not None
            self.write(flat1094)
            return None
        else:
            _dollar_dollar = msg
            fields1089 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1089 is not None
            unwrapped_fields1090 = fields1089
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1091 = unwrapped_fields1090[0]
            self.pretty_name(field1091)
            self.newline()
            field1092 = unwrapped_fields1090[1]
            self.pretty_ffi_args(field1092)
            self.newline()
            field1093 = unwrapped_fields1090[2]
            self.pretty_terms(field1093)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1096 = self._try_flat(msg, self.pretty_name)
        if flat1096 is not None:
            assert flat1096 is not None
            self.write(flat1096)
            return None
        else:
            fields1095 = msg
            self.write(":")
            self.write(fields1095)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1100 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1100 is not None:
            assert flat1100 is not None
            self.write(flat1100)
            return None
        else:
            fields1097 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1097) == 0:
                self.newline()
                for i1099, elem1098 in enumerate(fields1097):
                    if (i1099 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1098)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1107 = self._try_flat(msg, self.pretty_atom)
        if flat1107 is not None:
            assert flat1107 is not None
            self.write(flat1107)
            return None
        else:
            _dollar_dollar = msg
            fields1101 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1101 is not None
            unwrapped_fields1102 = fields1101
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1103 = unwrapped_fields1102[0]
            self.pretty_relation_id(field1103)
            field1104 = unwrapped_fields1102[1]
            if not len(field1104) == 0:
                self.newline()
                for i1106, elem1105 in enumerate(field1104):
                    if (i1106 > 0):
                        self.newline()
                    self.pretty_term(elem1105)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1114 = self._try_flat(msg, self.pretty_pragma)
        if flat1114 is not None:
            assert flat1114 is not None
            self.write(flat1114)
            return None
        else:
            _dollar_dollar = msg
            fields1108 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1108 is not None
            unwrapped_fields1109 = fields1108
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1110 = unwrapped_fields1109[0]
            self.pretty_name(field1110)
            field1111 = unwrapped_fields1109[1]
            if not len(field1111) == 0:
                self.newline()
                for i1113, elem1112 in enumerate(field1111):
                    if (i1113 > 0):
                        self.newline()
                    self.pretty_term(elem1112)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1130 = self._try_flat(msg, self.pretty_primitive)
        if flat1130 is not None:
            assert flat1130 is not None
            self.write(flat1130)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1639 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1639 = None
            guard_result1129 = _t1639
            if guard_result1129 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1640 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1640 = None
                guard_result1128 = _t1640
                if guard_result1128 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1641 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1641 = None
                    guard_result1127 = _t1641
                    if guard_result1127 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1642 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1642 = None
                        guard_result1126 = _t1642
                        if guard_result1126 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1643 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1643 = None
                            guard_result1125 = _t1643
                            if guard_result1125 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1644 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1644 = None
                                guard_result1124 = _t1644
                                if guard_result1124 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1645 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1645 = None
                                    guard_result1123 = _t1645
                                    if guard_result1123 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1646 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1646 = None
                                        guard_result1122 = _t1646
                                        if guard_result1122 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1647 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1647 = None
                                            guard_result1121 = _t1647
                                            if guard_result1121 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1115 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1115 is not None
                                                unwrapped_fields1116 = fields1115
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1117 = unwrapped_fields1116[0]
                                                self.pretty_name(field1117)
                                                field1118 = unwrapped_fields1116[1]
                                                if not len(field1118) == 0:
                                                    self.newline()
                                                    for i1120, elem1119 in enumerate(field1118):
                                                        if (i1120 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1119)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1135 = self._try_flat(msg, self.pretty_eq)
        if flat1135 is not None:
            assert flat1135 is not None
            self.write(flat1135)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1648 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1648 = None
            fields1131 = _t1648
            assert fields1131 is not None
            unwrapped_fields1132 = fields1131
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1133 = unwrapped_fields1132[0]
            self.pretty_term(field1133)
            self.newline()
            field1134 = unwrapped_fields1132[1]
            self.pretty_term(field1134)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1140 = self._try_flat(msg, self.pretty_lt)
        if flat1140 is not None:
            assert flat1140 is not None
            self.write(flat1140)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1649 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1649 = None
            fields1136 = _t1649
            assert fields1136 is not None
            unwrapped_fields1137 = fields1136
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1138 = unwrapped_fields1137[0]
            self.pretty_term(field1138)
            self.newline()
            field1139 = unwrapped_fields1137[1]
            self.pretty_term(field1139)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1145 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1145 is not None:
            assert flat1145 is not None
            self.write(flat1145)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1650 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1650 = None
            fields1141 = _t1650
            assert fields1141 is not None
            unwrapped_fields1142 = fields1141
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1143 = unwrapped_fields1142[0]
            self.pretty_term(field1143)
            self.newline()
            field1144 = unwrapped_fields1142[1]
            self.pretty_term(field1144)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1150 = self._try_flat(msg, self.pretty_gt)
        if flat1150 is not None:
            assert flat1150 is not None
            self.write(flat1150)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1651 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1651 = None
            fields1146 = _t1651
            assert fields1146 is not None
            unwrapped_fields1147 = fields1146
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1148 = unwrapped_fields1147[0]
            self.pretty_term(field1148)
            self.newline()
            field1149 = unwrapped_fields1147[1]
            self.pretty_term(field1149)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1155 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1155 is not None:
            assert flat1155 is not None
            self.write(flat1155)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1652 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1652 = None
            fields1151 = _t1652
            assert fields1151 is not None
            unwrapped_fields1152 = fields1151
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1153 = unwrapped_fields1152[0]
            self.pretty_term(field1153)
            self.newline()
            field1154 = unwrapped_fields1152[1]
            self.pretty_term(field1154)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1161 = self._try_flat(msg, self.pretty_add)
        if flat1161 is not None:
            assert flat1161 is not None
            self.write(flat1161)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1653 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1653 = None
            fields1156 = _t1653
            assert fields1156 is not None
            unwrapped_fields1157 = fields1156
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1158 = unwrapped_fields1157[0]
            self.pretty_term(field1158)
            self.newline()
            field1159 = unwrapped_fields1157[1]
            self.pretty_term(field1159)
            self.newline()
            field1160 = unwrapped_fields1157[2]
            self.pretty_term(field1160)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1167 = self._try_flat(msg, self.pretty_minus)
        if flat1167 is not None:
            assert flat1167 is not None
            self.write(flat1167)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1654 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1654 = None
            fields1162 = _t1654
            assert fields1162 is not None
            unwrapped_fields1163 = fields1162
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1164 = unwrapped_fields1163[0]
            self.pretty_term(field1164)
            self.newline()
            field1165 = unwrapped_fields1163[1]
            self.pretty_term(field1165)
            self.newline()
            field1166 = unwrapped_fields1163[2]
            self.pretty_term(field1166)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1173 = self._try_flat(msg, self.pretty_multiply)
        if flat1173 is not None:
            assert flat1173 is not None
            self.write(flat1173)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1655 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1655 = None
            fields1168 = _t1655
            assert fields1168 is not None
            unwrapped_fields1169 = fields1168
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1170 = unwrapped_fields1169[0]
            self.pretty_term(field1170)
            self.newline()
            field1171 = unwrapped_fields1169[1]
            self.pretty_term(field1171)
            self.newline()
            field1172 = unwrapped_fields1169[2]
            self.pretty_term(field1172)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1179 = self._try_flat(msg, self.pretty_divide)
        if flat1179 is not None:
            assert flat1179 is not None
            self.write(flat1179)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1656 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1656 = None
            fields1174 = _t1656
            assert fields1174 is not None
            unwrapped_fields1175 = fields1174
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1176 = unwrapped_fields1175[0]
            self.pretty_term(field1176)
            self.newline()
            field1177 = unwrapped_fields1175[1]
            self.pretty_term(field1177)
            self.newline()
            field1178 = unwrapped_fields1175[2]
            self.pretty_term(field1178)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1184 = self._try_flat(msg, self.pretty_rel_term)
        if flat1184 is not None:
            assert flat1184 is not None
            self.write(flat1184)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1657 = _dollar_dollar.specialized_value
            else:
                _t1657 = None
            deconstruct_result1182 = _t1657
            if deconstruct_result1182 is not None:
                assert deconstruct_result1182 is not None
                unwrapped1183 = deconstruct_result1182
                self.pretty_specialized_value(unwrapped1183)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1658 = _dollar_dollar.term
                else:
                    _t1658 = None
                deconstruct_result1180 = _t1658
                if deconstruct_result1180 is not None:
                    assert deconstruct_result1180 is not None
                    unwrapped1181 = deconstruct_result1180
                    self.pretty_term(unwrapped1181)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1186 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1186 is not None:
            assert flat1186 is not None
            self.write(flat1186)
            return None
        else:
            fields1185 = msg
            self.write("#")
            self.pretty_raw_value(fields1185)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1193 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1193 is not None:
            assert flat1193 is not None
            self.write(flat1193)
            return None
        else:
            _dollar_dollar = msg
            fields1187 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1187 is not None
            unwrapped_fields1188 = fields1187
            self.write("(relatom")
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

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1198 = self._try_flat(msg, self.pretty_cast)
        if flat1198 is not None:
            assert flat1198 is not None
            self.write(flat1198)
            return None
        else:
            _dollar_dollar = msg
            fields1194 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1194 is not None
            unwrapped_fields1195 = fields1194
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1196 = unwrapped_fields1195[0]
            self.pretty_term(field1196)
            self.newline()
            field1197 = unwrapped_fields1195[1]
            self.pretty_term(field1197)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1202 = self._try_flat(msg, self.pretty_attrs)
        if flat1202 is not None:
            assert flat1202 is not None
            self.write(flat1202)
            return None
        else:
            fields1199 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1199) == 0:
                self.newline()
                for i1201, elem1200 in enumerate(fields1199):
                    if (i1201 > 0):
                        self.newline()
                    self.pretty_attribute(elem1200)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1209 = self._try_flat(msg, self.pretty_attribute)
        if flat1209 is not None:
            assert flat1209 is not None
            self.write(flat1209)
            return None
        else:
            _dollar_dollar = msg
            fields1203 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1203 is not None
            unwrapped_fields1204 = fields1203
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1205 = unwrapped_fields1204[0]
            self.pretty_name(field1205)
            field1206 = unwrapped_fields1204[1]
            if not len(field1206) == 0:
                self.newline()
                for i1208, elem1207 in enumerate(field1206):
                    if (i1208 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1207)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1216 = self._try_flat(msg, self.pretty_algorithm)
        if flat1216 is not None:
            assert flat1216 is not None
            self.write(flat1216)
            return None
        else:
            _dollar_dollar = msg
            fields1210 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            assert fields1210 is not None
            unwrapped_fields1211 = fields1210
            self.write("(algorithm")
            self.indent_sexp()
            field1212 = unwrapped_fields1211[0]
            if not len(field1212) == 0:
                self.newline()
                for i1214, elem1213 in enumerate(field1212):
                    if (i1214 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1213)
            self.newline()
            field1215 = unwrapped_fields1211[1]
            self.pretty_script(field1215)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1221 = self._try_flat(msg, self.pretty_script)
        if flat1221 is not None:
            assert flat1221 is not None
            self.write(flat1221)
            return None
        else:
            _dollar_dollar = msg
            fields1217 = _dollar_dollar.constructs
            assert fields1217 is not None
            unwrapped_fields1218 = fields1217
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1218) == 0:
                self.newline()
                for i1220, elem1219 in enumerate(unwrapped_fields1218):
                    if (i1220 > 0):
                        self.newline()
                    self.pretty_construct(elem1219)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1226 = self._try_flat(msg, self.pretty_construct)
        if flat1226 is not None:
            assert flat1226 is not None
            self.write(flat1226)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1659 = _dollar_dollar.loop
            else:
                _t1659 = None
            deconstruct_result1224 = _t1659
            if deconstruct_result1224 is not None:
                assert deconstruct_result1224 is not None
                unwrapped1225 = deconstruct_result1224
                self.pretty_loop(unwrapped1225)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1660 = _dollar_dollar.instruction
                else:
                    _t1660 = None
                deconstruct_result1222 = _t1660
                if deconstruct_result1222 is not None:
                    assert deconstruct_result1222 is not None
                    unwrapped1223 = deconstruct_result1222
                    self.pretty_instruction(unwrapped1223)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1231 = self._try_flat(msg, self.pretty_loop)
        if flat1231 is not None:
            assert flat1231 is not None
            self.write(flat1231)
            return None
        else:
            _dollar_dollar = msg
            fields1227 = (_dollar_dollar.init, _dollar_dollar.body,)
            assert fields1227 is not None
            unwrapped_fields1228 = fields1227
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1229 = unwrapped_fields1228[0]
            self.pretty_init(field1229)
            self.newline()
            field1230 = unwrapped_fields1228[1]
            self.pretty_script(field1230)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1235 = self._try_flat(msg, self.pretty_init)
        if flat1235 is not None:
            assert flat1235 is not None
            self.write(flat1235)
            return None
        else:
            fields1232 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1232) == 0:
                self.newline()
                for i1234, elem1233 in enumerate(fields1232):
                    if (i1234 > 0):
                        self.newline()
                    self.pretty_instruction(elem1233)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1246 = self._try_flat(msg, self.pretty_instruction)
        if flat1246 is not None:
            assert flat1246 is not None
            self.write(flat1246)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1661 = _dollar_dollar.assign
            else:
                _t1661 = None
            deconstruct_result1244 = _t1661
            if deconstruct_result1244 is not None:
                assert deconstruct_result1244 is not None
                unwrapped1245 = deconstruct_result1244
                self.pretty_assign(unwrapped1245)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1662 = _dollar_dollar.upsert
                else:
                    _t1662 = None
                deconstruct_result1242 = _t1662
                if deconstruct_result1242 is not None:
                    assert deconstruct_result1242 is not None
                    unwrapped1243 = deconstruct_result1242
                    self.pretty_upsert(unwrapped1243)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1663 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1663 = None
                    deconstruct_result1240 = _t1663
                    if deconstruct_result1240 is not None:
                        assert deconstruct_result1240 is not None
                        unwrapped1241 = deconstruct_result1240
                        self.pretty_break(unwrapped1241)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1664 = _dollar_dollar.monoid_def
                        else:
                            _t1664 = None
                        deconstruct_result1238 = _t1664
                        if deconstruct_result1238 is not None:
                            assert deconstruct_result1238 is not None
                            unwrapped1239 = deconstruct_result1238
                            self.pretty_monoid_def(unwrapped1239)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1665 = _dollar_dollar.monus_def
                            else:
                                _t1665 = None
                            deconstruct_result1236 = _t1665
                            if deconstruct_result1236 is not None:
                                assert deconstruct_result1236 is not None
                                unwrapped1237 = deconstruct_result1236
                                self.pretty_monus_def(unwrapped1237)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1253 = self._try_flat(msg, self.pretty_assign)
        if flat1253 is not None:
            assert flat1253 is not None
            self.write(flat1253)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1666 = _dollar_dollar.attrs
            else:
                _t1666 = None
            fields1247 = (_dollar_dollar.name, _dollar_dollar.body, _t1666,)
            assert fields1247 is not None
            unwrapped_fields1248 = fields1247
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1249 = unwrapped_fields1248[0]
            self.pretty_relation_id(field1249)
            self.newline()
            field1250 = unwrapped_fields1248[1]
            self.pretty_abstraction(field1250)
            field1251 = unwrapped_fields1248[2]
            if field1251 is not None:
                self.newline()
                assert field1251 is not None
                opt_val1252 = field1251
                self.pretty_attrs(opt_val1252)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1260 = self._try_flat(msg, self.pretty_upsert)
        if flat1260 is not None:
            assert flat1260 is not None
            self.write(flat1260)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1667 = _dollar_dollar.attrs
            else:
                _t1667 = None
            fields1254 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1667,)
            assert fields1254 is not None
            unwrapped_fields1255 = fields1254
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1256 = unwrapped_fields1255[0]
            self.pretty_relation_id(field1256)
            self.newline()
            field1257 = unwrapped_fields1255[1]
            self.pretty_abstraction_with_arity(field1257)
            field1258 = unwrapped_fields1255[2]
            if field1258 is not None:
                self.newline()
                assert field1258 is not None
                opt_val1259 = field1258
                self.pretty_attrs(opt_val1259)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1265 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1265 is not None:
            assert flat1265 is not None
            self.write(flat1265)
            return None
        else:
            _dollar_dollar = msg
            _t1668 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1261 = (_t1668, _dollar_dollar[0].value,)
            assert fields1261 is not None
            unwrapped_fields1262 = fields1261
            self.write("(")
            self.indent()
            field1263 = unwrapped_fields1262[0]
            self.pretty_bindings(field1263)
            self.newline()
            field1264 = unwrapped_fields1262[1]
            self.pretty_formula(field1264)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1272 = self._try_flat(msg, self.pretty_break)
        if flat1272 is not None:
            assert flat1272 is not None
            self.write(flat1272)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1669 = _dollar_dollar.attrs
            else:
                _t1669 = None
            fields1266 = (_dollar_dollar.name, _dollar_dollar.body, _t1669,)
            assert fields1266 is not None
            unwrapped_fields1267 = fields1266
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1268 = unwrapped_fields1267[0]
            self.pretty_relation_id(field1268)
            self.newline()
            field1269 = unwrapped_fields1267[1]
            self.pretty_abstraction(field1269)
            field1270 = unwrapped_fields1267[2]
            if field1270 is not None:
                self.newline()
                assert field1270 is not None
                opt_val1271 = field1270
                self.pretty_attrs(opt_val1271)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1280 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1280 is not None:
            assert flat1280 is not None
            self.write(flat1280)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1670 = _dollar_dollar.attrs
            else:
                _t1670 = None
            fields1273 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1670,)
            assert fields1273 is not None
            unwrapped_fields1274 = fields1273
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1275 = unwrapped_fields1274[0]
            self.pretty_monoid(field1275)
            self.newline()
            field1276 = unwrapped_fields1274[1]
            self.pretty_relation_id(field1276)
            self.newline()
            field1277 = unwrapped_fields1274[2]
            self.pretty_abstraction_with_arity(field1277)
            field1278 = unwrapped_fields1274[3]
            if field1278 is not None:
                self.newline()
                assert field1278 is not None
                opt_val1279 = field1278
                self.pretty_attrs(opt_val1279)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1289 = self._try_flat(msg, self.pretty_monoid)
        if flat1289 is not None:
            assert flat1289 is not None
            self.write(flat1289)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1671 = _dollar_dollar.or_monoid
            else:
                _t1671 = None
            deconstruct_result1287 = _t1671
            if deconstruct_result1287 is not None:
                assert deconstruct_result1287 is not None
                unwrapped1288 = deconstruct_result1287
                self.pretty_or_monoid(unwrapped1288)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1672 = _dollar_dollar.min_monoid
                else:
                    _t1672 = None
                deconstruct_result1285 = _t1672
                if deconstruct_result1285 is not None:
                    assert deconstruct_result1285 is not None
                    unwrapped1286 = deconstruct_result1285
                    self.pretty_min_monoid(unwrapped1286)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1673 = _dollar_dollar.max_monoid
                    else:
                        _t1673 = None
                    deconstruct_result1283 = _t1673
                    if deconstruct_result1283 is not None:
                        assert deconstruct_result1283 is not None
                        unwrapped1284 = deconstruct_result1283
                        self.pretty_max_monoid(unwrapped1284)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1674 = _dollar_dollar.sum_monoid
                        else:
                            _t1674 = None
                        deconstruct_result1281 = _t1674
                        if deconstruct_result1281 is not None:
                            assert deconstruct_result1281 is not None
                            unwrapped1282 = deconstruct_result1281
                            self.pretty_sum_monoid(unwrapped1282)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1290 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1293 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1293 is not None:
            assert flat1293 is not None
            self.write(flat1293)
            return None
        else:
            _dollar_dollar = msg
            fields1291 = _dollar_dollar.type
            assert fields1291 is not None
            unwrapped_fields1292 = fields1291
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1292)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1296 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1296 is not None:
            assert flat1296 is not None
            self.write(flat1296)
            return None
        else:
            _dollar_dollar = msg
            fields1294 = _dollar_dollar.type
            assert fields1294 is not None
            unwrapped_fields1295 = fields1294
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1295)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1299 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1299 is not None:
            assert flat1299 is not None
            self.write(flat1299)
            return None
        else:
            _dollar_dollar = msg
            fields1297 = _dollar_dollar.type
            assert fields1297 is not None
            unwrapped_fields1298 = fields1297
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1298)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1307 = self._try_flat(msg, self.pretty_monus_def)
        if flat1307 is not None:
            assert flat1307 is not None
            self.write(flat1307)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1675 = _dollar_dollar.attrs
            else:
                _t1675 = None
            fields1300 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1675,)
            assert fields1300 is not None
            unwrapped_fields1301 = fields1300
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1302 = unwrapped_fields1301[0]
            self.pretty_monoid(field1302)
            self.newline()
            field1303 = unwrapped_fields1301[1]
            self.pretty_relation_id(field1303)
            self.newline()
            field1304 = unwrapped_fields1301[2]
            self.pretty_abstraction_with_arity(field1304)
            field1305 = unwrapped_fields1301[3]
            if field1305 is not None:
                self.newline()
                assert field1305 is not None
                opt_val1306 = field1305
                self.pretty_attrs(opt_val1306)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1314 = self._try_flat(msg, self.pretty_constraint)
        if flat1314 is not None:
            assert flat1314 is not None
            self.write(flat1314)
            return None
        else:
            _dollar_dollar = msg
            fields1308 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1308 is not None
            unwrapped_fields1309 = fields1308
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1310 = unwrapped_fields1309[0]
            self.pretty_relation_id(field1310)
            self.newline()
            field1311 = unwrapped_fields1309[1]
            self.pretty_abstraction(field1311)
            self.newline()
            field1312 = unwrapped_fields1309[2]
            self.pretty_functional_dependency_keys(field1312)
            self.newline()
            field1313 = unwrapped_fields1309[3]
            self.pretty_functional_dependency_values(field1313)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1318 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1318 is not None:
            assert flat1318 is not None
            self.write(flat1318)
            return None
        else:
            fields1315 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1315) == 0:
                self.newline()
                for i1317, elem1316 in enumerate(fields1315):
                    if (i1317 > 0):
                        self.newline()
                    self.pretty_var(elem1316)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1322 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1322 is not None:
            assert flat1322 is not None
            self.write(flat1322)
            return None
        else:
            fields1319 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1319) == 0:
                self.newline()
                for i1321, elem1320 in enumerate(fields1319):
                    if (i1321 > 0):
                        self.newline()
                    self.pretty_var(elem1320)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1331 = self._try_flat(msg, self.pretty_data)
        if flat1331 is not None:
            assert flat1331 is not None
            self.write(flat1331)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1676 = _dollar_dollar.edb
            else:
                _t1676 = None
            deconstruct_result1329 = _t1676
            if deconstruct_result1329 is not None:
                assert deconstruct_result1329 is not None
                unwrapped1330 = deconstruct_result1329
                self.pretty_edb(unwrapped1330)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1677 = _dollar_dollar.betree_relation
                else:
                    _t1677 = None
                deconstruct_result1327 = _t1677
                if deconstruct_result1327 is not None:
                    assert deconstruct_result1327 is not None
                    unwrapped1328 = deconstruct_result1327
                    self.pretty_betree_relation(unwrapped1328)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1678 = _dollar_dollar.csv_data
                    else:
                        _t1678 = None
                    deconstruct_result1325 = _t1678
                    if deconstruct_result1325 is not None:
                        assert deconstruct_result1325 is not None
                        unwrapped1326 = deconstruct_result1325
                        self.pretty_csv_data(unwrapped1326)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1679 = _dollar_dollar.iceberg_data
                        else:
                            _t1679 = None
                        deconstruct_result1323 = _t1679
                        if deconstruct_result1323 is not None:
                            assert deconstruct_result1323 is not None
                            unwrapped1324 = deconstruct_result1323
                            self.pretty_iceberg_data(unwrapped1324)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1337 = self._try_flat(msg, self.pretty_edb)
        if flat1337 is not None:
            assert flat1337 is not None
            self.write(flat1337)
            return None
        else:
            _dollar_dollar = msg
            fields1332 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1332 is not None
            unwrapped_fields1333 = fields1332
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1334 = unwrapped_fields1333[0]
            self.pretty_relation_id(field1334)
            self.newline()
            field1335 = unwrapped_fields1333[1]
            self.pretty_edb_path(field1335)
            self.newline()
            field1336 = unwrapped_fields1333[2]
            self.pretty_edb_types(field1336)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1341 = self._try_flat(msg, self.pretty_edb_path)
        if flat1341 is not None:
            assert flat1341 is not None
            self.write(flat1341)
            return None
        else:
            fields1338 = msg
            self.write("[")
            self.indent()
            for i1340, elem1339 in enumerate(fields1338):
                if (i1340 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1339))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1345 = self._try_flat(msg, self.pretty_edb_types)
        if flat1345 is not None:
            assert flat1345 is not None
            self.write(flat1345)
            return None
        else:
            fields1342 = msg
            self.write("[")
            self.indent()
            for i1344, elem1343 in enumerate(fields1342):
                if (i1344 > 0):
                    self.newline()
                self.pretty_type(elem1343)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1350 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1350 is not None:
            assert flat1350 is not None
            self.write(flat1350)
            return None
        else:
            _dollar_dollar = msg
            fields1346 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1346 is not None
            unwrapped_fields1347 = fields1346
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1348 = unwrapped_fields1347[0]
            self.pretty_relation_id(field1348)
            self.newline()
            field1349 = unwrapped_fields1347[1]
            self.pretty_betree_info(field1349)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1356 = self._try_flat(msg, self.pretty_betree_info)
        if flat1356 is not None:
            assert flat1356 is not None
            self.write(flat1356)
            return None
        else:
            _dollar_dollar = msg
            _t1680 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1351 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1680,)
            assert fields1351 is not None
            unwrapped_fields1352 = fields1351
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1353 = unwrapped_fields1352[0]
            self.pretty_betree_info_key_types(field1353)
            self.newline()
            field1354 = unwrapped_fields1352[1]
            self.pretty_betree_info_value_types(field1354)
            self.newline()
            field1355 = unwrapped_fields1352[2]
            self.pretty_config_dict(field1355)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1360 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1360 is not None:
            assert flat1360 is not None
            self.write(flat1360)
            return None
        else:
            fields1357 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1357) == 0:
                self.newline()
                for i1359, elem1358 in enumerate(fields1357):
                    if (i1359 > 0):
                        self.newline()
                    self.pretty_type(elem1358)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1364 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1364 is not None:
            assert flat1364 is not None
            self.write(flat1364)
            return None
        else:
            fields1361 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1361) == 0:
                self.newline()
                for i1363, elem1362 in enumerate(fields1361):
                    if (i1363 > 0):
                        self.newline()
                    self.pretty_type(elem1362)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1371 = self._try_flat(msg, self.pretty_csv_data)
        if flat1371 is not None:
            assert flat1371 is not None
            self.write(flat1371)
            return None
        else:
            _dollar_dollar = msg
            fields1365 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1365 is not None
            unwrapped_fields1366 = fields1365
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1367 = unwrapped_fields1366[0]
            self.pretty_csvlocator(field1367)
            self.newline()
            field1368 = unwrapped_fields1366[1]
            self.pretty_csv_config(field1368)
            self.newline()
            field1369 = unwrapped_fields1366[2]
            self.pretty_gnf_columns(field1369)
            self.newline()
            field1370 = unwrapped_fields1366[3]
            self.pretty_csv_asof(field1370)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1378 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1378 is not None:
            assert flat1378 is not None
            self.write(flat1378)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1681 = _dollar_dollar.paths
            else:
                _t1681 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1682 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1682 = None
            fields1372 = (_t1681, _t1682,)
            assert fields1372 is not None
            unwrapped_fields1373 = fields1372
            self.write("(csv_locator")
            self.indent_sexp()
            field1374 = unwrapped_fields1373[0]
            if field1374 is not None:
                self.newline()
                assert field1374 is not None
                opt_val1375 = field1374
                self.pretty_csv_locator_paths(opt_val1375)
            field1376 = unwrapped_fields1373[1]
            if field1376 is not None:
                self.newline()
                assert field1376 is not None
                opt_val1377 = field1376
                self.pretty_csv_locator_inline_data(opt_val1377)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1382 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1382 is not None:
            assert flat1382 is not None
            self.write(flat1382)
            return None
        else:
            fields1379 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1379) == 0:
                self.newline()
                for i1381, elem1380 in enumerate(fields1379):
                    if (i1381 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1380))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1384 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1384 is not None:
            assert flat1384 is not None
            self.write(flat1384)
            return None
        else:
            fields1383 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1383))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1387 = self._try_flat(msg, self.pretty_csv_config)
        if flat1387 is not None:
            assert flat1387 is not None
            self.write(flat1387)
            return None
        else:
            _dollar_dollar = msg
            _t1683 = self.deconstruct_csv_config(_dollar_dollar)
            fields1385 = _t1683
            assert fields1385 is not None
            unwrapped_fields1386 = fields1385
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1386)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1391 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1391 is not None:
            assert flat1391 is not None
            self.write(flat1391)
            return None
        else:
            fields1388 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1388) == 0:
                self.newline()
                for i1390, elem1389 in enumerate(fields1388):
                    if (i1390 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1389)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1400 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1400 is not None:
            assert flat1400 is not None
            self.write(flat1400)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1684 = _dollar_dollar.target_id
            else:
                _t1684 = None
            fields1392 = (_dollar_dollar.column_path, _t1684, _dollar_dollar.types,)
            assert fields1392 is not None
            unwrapped_fields1393 = fields1392
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1394 = unwrapped_fields1393[0]
            self.pretty_gnf_column_path(field1394)
            field1395 = unwrapped_fields1393[1]
            if field1395 is not None:
                self.newline()
                assert field1395 is not None
                opt_val1396 = field1395
                self.pretty_relation_id(opt_val1396)
            self.newline()
            self.write("[")
            field1397 = unwrapped_fields1393[2]
            for i1399, elem1398 in enumerate(field1397):
                if (i1399 > 0):
                    self.newline()
                self.pretty_type(elem1398)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1407 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1407 is not None:
            assert flat1407 is not None
            self.write(flat1407)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1685 = _dollar_dollar[0]
            else:
                _t1685 = None
            deconstruct_result1405 = _t1685
            if deconstruct_result1405 is not None:
                assert deconstruct_result1405 is not None
                unwrapped1406 = deconstruct_result1405
                self.write(self.format_string_value(unwrapped1406))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1686 = _dollar_dollar
                else:
                    _t1686 = None
                deconstruct_result1401 = _t1686
                if deconstruct_result1401 is not None:
                    assert deconstruct_result1401 is not None
                    unwrapped1402 = deconstruct_result1401
                    self.write("[")
                    self.indent()
                    for i1404, elem1403 in enumerate(unwrapped1402):
                        if (i1404 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1403))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1409 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1409 is not None:
            assert flat1409 is not None
            self.write(flat1409)
            return None
        else:
            fields1408 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1408))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1417 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1417 is not None:
            assert flat1417 is not None
            self.write(flat1417)
            return None
        else:
            _dollar_dollar = msg
            _t1687 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1410 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1687,)
            assert fields1410 is not None
            unwrapped_fields1411 = fields1410
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1412 = unwrapped_fields1411[0]
            self.pretty_iceberg_locator(field1412)
            self.newline()
            field1413 = unwrapped_fields1411[1]
            self.pretty_iceberg_catalog_config(field1413)
            self.newline()
            field1414 = unwrapped_fields1411[2]
            self.pretty_gnf_columns(field1414)
            field1415 = unwrapped_fields1411[3]
            if field1415 is not None:
                self.newline()
                assert field1415 is not None
                opt_val1416 = field1415
                self.pretty_iceberg_to_snapshot(opt_val1416)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1425 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1425 is not None:
            assert flat1425 is not None
            self.write(flat1425)
            return None
        else:
            _dollar_dollar = msg
            fields1418 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1418 is not None
            unwrapped_fields1419 = fields1418
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("table_name")
            self.newline()
            field1420 = unwrapped_fields1419[0]
            self.write(self.format_string_value(field1420))
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("namespace")
            field1421 = unwrapped_fields1419[1]
            if not len(field1421) == 0:
                self.newline()
                for i1423, elem1422 in enumerate(field1421):
                    if (i1423 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1422))
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("warehouse")
            self.newline()
            field1424 = unwrapped_fields1419[2]
            self.write(self.format_string_value(field1424))
            self.dedent()
            self.write(")")
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1437 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1437 is not None:
            assert flat1437 is not None
            self.write(flat1437)
            return None
        else:
            _dollar_dollar = msg
            _t1688 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1426 = (_dollar_dollar.catalog_uri, _t1688, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1426 is not None
            unwrapped_fields1427 = fields1426
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("catalog_uri")
            self.newline()
            field1428 = unwrapped_fields1427[0]
            self.write(self.format_string_value(field1428))
            self.dedent()
            self.write(")")
            field1429 = unwrapped_fields1427[1]
            if field1429 is not None:
                self.newline()
                assert field1429 is not None
                opt_val1430 = field1429
                self.pretty_iceberg_catalog_config_scope(opt_val1430)
            self.newline()
            self.write("(")
            self.newline()
            self.write("properties")
            field1431 = unwrapped_fields1427[2]
            if not len(field1431) == 0:
                self.newline()
                for i1433, elem1432 in enumerate(field1431):
                    if (i1433 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1432)
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("auth_properties")
            field1434 = unwrapped_fields1427[3]
            if not len(field1434) == 0:
                self.newline()
                for i1436, elem1435 in enumerate(field1434):
                    if (i1436 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1435)
            self.dedent()
            self.write(")")
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1439 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1439 is not None:
            assert flat1439 is not None
            self.write(flat1439)
            return None
        else:
            fields1438 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1438))
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1444 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1444 is not None:
            assert flat1444 is not None
            self.write(flat1444)
            return None
        else:
            _dollar_dollar = msg
            fields1440 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1440 is not None
            unwrapped_fields1441 = fields1440
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1442 = unwrapped_fields1441[0]
            self.write(self.format_string_value(field1442))
            self.newline()
            field1443 = unwrapped_fields1441[1]
            self.write(self.format_string_value(field1443))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1446 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1446 is not None:
            assert flat1446 is not None
            self.write(flat1446)
            return None
        else:
            fields1445 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1445))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1449 = self._try_flat(msg, self.pretty_undefine)
        if flat1449 is not None:
            assert flat1449 is not None
            self.write(flat1449)
            return None
        else:
            _dollar_dollar = msg
            fields1447 = _dollar_dollar.fragment_id
            assert fields1447 is not None
            unwrapped_fields1448 = fields1447
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1448)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1454 = self._try_flat(msg, self.pretty_context)
        if flat1454 is not None:
            assert flat1454 is not None
            self.write(flat1454)
            return None
        else:
            _dollar_dollar = msg
            fields1450 = _dollar_dollar.relations
            assert fields1450 is not None
            unwrapped_fields1451 = fields1450
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1451) == 0:
                self.newline()
                for i1453, elem1452 in enumerate(unwrapped_fields1451):
                    if (i1453 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1452)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1459 = self._try_flat(msg, self.pretty_snapshot)
        if flat1459 is not None:
            assert flat1459 is not None
            self.write(flat1459)
            return None
        else:
            _dollar_dollar = msg
            fields1455 = _dollar_dollar.mappings
            assert fields1455 is not None
            unwrapped_fields1456 = fields1455
            self.write("(snapshot")
            self.indent_sexp()
            if not len(unwrapped_fields1456) == 0:
                self.newline()
                for i1458, elem1457 in enumerate(unwrapped_fields1456):
                    if (i1458 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1457)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1464 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1464 is not None:
            assert flat1464 is not None
            self.write(flat1464)
            return None
        else:
            _dollar_dollar = msg
            fields1460 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1460 is not None
            unwrapped_fields1461 = fields1460
            field1462 = unwrapped_fields1461[0]
            self.pretty_edb_path(field1462)
            self.write(" ")
            field1463 = unwrapped_fields1461[1]
            self.pretty_relation_id(field1463)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1468 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1468 is not None:
            assert flat1468 is not None
            self.write(flat1468)
            return None
        else:
            fields1465 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1465) == 0:
                self.newline()
                for i1467, elem1466 in enumerate(fields1465):
                    if (i1467 > 0):
                        self.newline()
                    self.pretty_read(elem1466)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1479 = self._try_flat(msg, self.pretty_read)
        if flat1479 is not None:
            assert flat1479 is not None
            self.write(flat1479)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1689 = _dollar_dollar.demand
            else:
                _t1689 = None
            deconstruct_result1477 = _t1689
            if deconstruct_result1477 is not None:
                assert deconstruct_result1477 is not None
                unwrapped1478 = deconstruct_result1477
                self.pretty_demand(unwrapped1478)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1690 = _dollar_dollar.output
                else:
                    _t1690 = None
                deconstruct_result1475 = _t1690
                if deconstruct_result1475 is not None:
                    assert deconstruct_result1475 is not None
                    unwrapped1476 = deconstruct_result1475
                    self.pretty_output(unwrapped1476)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1691 = _dollar_dollar.what_if
                    else:
                        _t1691 = None
                    deconstruct_result1473 = _t1691
                    if deconstruct_result1473 is not None:
                        assert deconstruct_result1473 is not None
                        unwrapped1474 = deconstruct_result1473
                        self.pretty_what_if(unwrapped1474)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1692 = _dollar_dollar.abort
                        else:
                            _t1692 = None
                        deconstruct_result1471 = _t1692
                        if deconstruct_result1471 is not None:
                            assert deconstruct_result1471 is not None
                            unwrapped1472 = deconstruct_result1471
                            self.pretty_abort(unwrapped1472)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1693 = _dollar_dollar.export
                            else:
                                _t1693 = None
                            deconstruct_result1469 = _t1693
                            if deconstruct_result1469 is not None:
                                assert deconstruct_result1469 is not None
                                unwrapped1470 = deconstruct_result1469
                                self.pretty_export(unwrapped1470)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1482 = self._try_flat(msg, self.pretty_demand)
        if flat1482 is not None:
            assert flat1482 is not None
            self.write(flat1482)
            return None
        else:
            _dollar_dollar = msg
            fields1480 = _dollar_dollar.relation_id
            assert fields1480 is not None
            unwrapped_fields1481 = fields1480
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1481)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1487 = self._try_flat(msg, self.pretty_output)
        if flat1487 is not None:
            assert flat1487 is not None
            self.write(flat1487)
            return None
        else:
            _dollar_dollar = msg
            fields1483 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1483 is not None
            unwrapped_fields1484 = fields1483
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1485 = unwrapped_fields1484[0]
            self.pretty_name(field1485)
            self.newline()
            field1486 = unwrapped_fields1484[1]
            self.pretty_relation_id(field1486)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1492 = self._try_flat(msg, self.pretty_what_if)
        if flat1492 is not None:
            assert flat1492 is not None
            self.write(flat1492)
            return None
        else:
            _dollar_dollar = msg
            fields1488 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1488 is not None
            unwrapped_fields1489 = fields1488
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1490 = unwrapped_fields1489[0]
            self.pretty_name(field1490)
            self.newline()
            field1491 = unwrapped_fields1489[1]
            self.pretty_epoch(field1491)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1498 = self._try_flat(msg, self.pretty_abort)
        if flat1498 is not None:
            assert flat1498 is not None
            self.write(flat1498)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1694 = _dollar_dollar.name
            else:
                _t1694 = None
            fields1493 = (_t1694, _dollar_dollar.relation_id,)
            assert fields1493 is not None
            unwrapped_fields1494 = fields1493
            self.write("(abort")
            self.indent_sexp()
            field1495 = unwrapped_fields1494[0]
            if field1495 is not None:
                self.newline()
                assert field1495 is not None
                opt_val1496 = field1495
                self.pretty_name(opt_val1496)
            self.newline()
            field1497 = unwrapped_fields1494[1]
            self.pretty_relation_id(field1497)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1503 = self._try_flat(msg, self.pretty_export)
        if flat1503 is not None:
            assert flat1503 is not None
            self.write(flat1503)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1695 = _dollar_dollar.csv_config
            else:
                _t1695 = None
            deconstruct_result1501 = _t1695
            if deconstruct_result1501 is not None:
                assert deconstruct_result1501 is not None
                unwrapped1502 = deconstruct_result1501
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1502)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1696 = _dollar_dollar.iceberg_config
                else:
                    _t1696 = None
                deconstruct_result1499 = _t1696
                if deconstruct_result1499 is not None:
                    assert deconstruct_result1499 is not None
                    unwrapped1500 = deconstruct_result1499
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1500)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1514 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1514 is not None:
            assert flat1514 is not None
            self.write(flat1514)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1697 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1697 = None
            deconstruct_result1509 = _t1697
            if deconstruct_result1509 is not None:
                assert deconstruct_result1509 is not None
                unwrapped1510 = deconstruct_result1509
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1511 = unwrapped1510[0]
                self.pretty_export_csv_path(field1511)
                self.newline()
                field1512 = unwrapped1510[1]
                self.pretty_export_csv_source(field1512)
                self.newline()
                field1513 = unwrapped1510[2]
                self.pretty_csv_config(field1513)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1699 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1698 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1699,)
                else:
                    _t1698 = None
                deconstruct_result1504 = _t1698
                if deconstruct_result1504 is not None:
                    assert deconstruct_result1504 is not None
                    unwrapped1505 = deconstruct_result1504
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1506 = unwrapped1505[0]
                    self.pretty_export_csv_path(field1506)
                    self.newline()
                    field1507 = unwrapped1505[1]
                    self.pretty_export_csv_columns_list(field1507)
                    self.newline()
                    field1508 = unwrapped1505[2]
                    self.pretty_config_dict(field1508)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1516 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1516 is not None:
            assert flat1516 is not None
            self.write(flat1516)
            return None
        else:
            fields1515 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1515))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1523 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1523 is not None:
            assert flat1523 is not None
            self.write(flat1523)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1700 = _dollar_dollar.gnf_columns.columns
            else:
                _t1700 = None
            deconstruct_result1519 = _t1700
            if deconstruct_result1519 is not None:
                assert deconstruct_result1519 is not None
                unwrapped1520 = deconstruct_result1519
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1520) == 0:
                    self.newline()
                    for i1522, elem1521 in enumerate(unwrapped1520):
                        if (i1522 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1521)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1701 = _dollar_dollar.table_def
                else:
                    _t1701 = None
                deconstruct_result1517 = _t1701
                if deconstruct_result1517 is not None:
                    assert deconstruct_result1517 is not None
                    unwrapped1518 = deconstruct_result1517
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1518)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1528 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1528 is not None:
            assert flat1528 is not None
            self.write(flat1528)
            return None
        else:
            _dollar_dollar = msg
            fields1524 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1524 is not None
            unwrapped_fields1525 = fields1524
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1526 = unwrapped_fields1525[0]
            self.write(self.format_string_value(field1526))
            self.newline()
            field1527 = unwrapped_fields1525[1]
            self.pretty_relation_id(field1527)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1532 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1532 is not None:
            assert flat1532 is not None
            self.write(flat1532)
            return None
        else:
            fields1529 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1529) == 0:
                self.newline()
                for i1531, elem1530 in enumerate(fields1529):
                    if (i1531 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1530)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1543 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1543 is not None:
            assert flat1543 is not None
            self.write(flat1543)
            return None
        else:
            _dollar_dollar = msg
            _t1702 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1533 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, sorted(_dollar_dollar.table_properties.items()), _t1702,)
            assert fields1533 is not None
            unwrapped_fields1534 = fields1533
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1535 = unwrapped_fields1534[0]
            self.pretty_iceberg_locator(field1535)
            self.newline()
            field1536 = unwrapped_fields1534[1]
            self.pretty_iceberg_catalog_config(field1536)
            self.newline()
            field1537 = unwrapped_fields1534[2]
            self.pretty_export_iceberg_columns(field1537)
            self.newline()
            self.write("(")
            self.newline()
            self.write("table_properties")
            field1538 = unwrapped_fields1534[3]
            if not len(field1538) == 0:
                self.newline()
                for i1540, elem1539 in enumerate(field1538):
                    if (i1540 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1539)
            self.dedent()
            self.write(")")
            field1541 = unwrapped_fields1534[4]
            if field1541 is not None:
                self.newline()
                assert field1541 is not None
                opt_val1542 = field1541
                self.pretty_config_dict(opt_val1542)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_columns(self, msg: transactions_pb2.ExportIcebergColumns):
        flat1550 = self._try_flat(msg, self.pretty_export_iceberg_columns)
        if flat1550 is not None:
            assert flat1550 is not None
            self.write(flat1550)
            return None
        else:
            _dollar_dollar = msg
            fields1544 = (_dollar_dollar, _dollar_dollar.target_columns,)
            assert fields1544 is not None
            unwrapped_fields1545 = fields1544
            self.write("(columns")
            self.indent_sexp()
            self.newline()
            field1546 = unwrapped_fields1545[0]
            self.pretty_export_iceberg_column_source(field1546)
            self.newline()
            self.write("(")
            self.newline()
            self.write("target_columns")
            field1547 = unwrapped_fields1545[1]
            if not len(field1547) == 0:
                self.newline()
                for i1549, elem1548 in enumerate(field1547):
                    if (i1549 > 0):
                        self.newline()
                    self.pretty_export_iceberg_column(elem1548)
            self.dedent()
            self.write(")")
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_column_source(self, msg: transactions_pb2.ExportIcebergColumns):
        flat1557 = self._try_flat(msg, self.pretty_export_iceberg_column_source)
        if flat1557 is not None:
            assert flat1557 is not None
            self.write(flat1557)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("source_gnf_defs"):
                _t1703 = _dollar_dollar.source_gnf_defs.defs
            else:
                _t1703 = None
            deconstruct_result1553 = _t1703
            if deconstruct_result1553 is not None:
                assert deconstruct_result1553 is not None
                unwrapped1554 = deconstruct_result1553
                self.write("(source_gnf_defs")
                self.indent_sexp()
                if not len(unwrapped1554) == 0:
                    self.newline()
                    for i1556, elem1555 in enumerate(unwrapped1554):
                        if (i1556 > 0):
                            self.newline()
                        self.pretty_relation_id(elem1555)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("source_table_def"):
                    _t1704 = _dollar_dollar.source_table_def
                else:
                    _t1704 = None
                deconstruct_result1551 = _t1704
                if deconstruct_result1551 is not None:
                    assert deconstruct_result1551 is not None
                    unwrapped1552 = deconstruct_result1551
                    self.write("(source_table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1552)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_iceberg_column_source")

    def pretty_export_iceberg_column(self, msg: transactions_pb2.ExportIcebergColumn):
        flat1563 = self._try_flat(msg, self.pretty_export_iceberg_column)
        if flat1563 is not None:
            assert flat1563 is not None
            self.write(flat1563)
            return None
        else:
            _dollar_dollar = msg
            fields1558 = (_dollar_dollar.name, _dollar_dollar.type, _dollar_dollar.nullable,)
            assert fields1558 is not None
            unwrapped_fields1559 = fields1558
            self.write("(iceberg_column")
            self.indent_sexp()
            self.newline()
            field1560 = unwrapped_fields1559[0]
            self.write(self.format_string_value(field1560))
            self.newline()
            field1561 = unwrapped_fields1559[1]
            self.pretty_type(field1561)
            self.newline()
            field1562 = unwrapped_fields1559[2]
            self.pretty_boolean_value(field1562)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1749 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1749)
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

    def pretty_export_iceberg_gnf_defs(self, msg: transactions_pb2.ExportIcebergGnfDefs):
        self.write("(export_iceberg_gnf_defs")
        self.indent_sexp()
        self.newline()
        self.write(":defs (")
        for _idx, _elem in enumerate(msg.defs):
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
        elif isinstance(msg, transactions_pb2.ExportIcebergColumns):
            self.pretty_export_iceberg_columns(msg)
        elif isinstance(msg, transactions_pb2.ExportIcebergColumn):
            self.pretty_export_iceberg_column(msg)
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
        elif isinstance(msg, transactions_pb2.ExportIcebergGnfDefs):
            self.pretty_export_iceberg_gnf_defs(msg)
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
