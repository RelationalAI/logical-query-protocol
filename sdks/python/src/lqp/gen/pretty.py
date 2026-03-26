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
        _t1673 = logic_pb2.Value(int32_value=v)
        return _t1673

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1674 = logic_pb2.Value(int_value=v)
        return _t1674

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1675 = logic_pb2.Value(float_value=v)
        return _t1675

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1676 = logic_pb2.Value(string_value=v)
        return _t1676

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1677 = logic_pb2.Value(boolean_value=v)
        return _t1677

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1678 = logic_pb2.Value(uint128_value=v)
        return _t1678

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1679 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1679,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1680 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1680,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1681 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1681,))
        _t1682 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1682,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1683 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1683,))
        _t1684 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1684,))
        if msg.new_line != "":
            _t1685 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1685,))
        _t1686 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1686,))
        _t1687 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1687,))
        _t1688 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1688,))
        if msg.comment != "":
            _t1689 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1689,))
        for missing_string in msg.missing_strings:
            _t1690 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1690,))
        _t1691 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1691,))
        _t1692 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1692,))
        _t1693 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1693,))
        if msg.partition_size_mb != 0:
            _t1694 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1694,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1695 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1695,))
        _t1696 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1696,))
        _t1697 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1697,))
        _t1698 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1698,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1699 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1699,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1700 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1700,))
        _t1701 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1701,))
        _t1702 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1702,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1703 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1703,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1704 = self._make_value_string(msg.compression)
            result.append(("compression", _t1704,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1705 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1705,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1706 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1706,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1707 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1707,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1708 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1708,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1709 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1709,))
        return sorted(result)

    def deconstruct_iceberg_config_scope_optional(self, msg: logic_pb2.IcebergConfig) -> str | None:
        if msg.HasField("scope"):
            assert msg.scope is not None
            return msg.scope
        else:
            _t1710 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        if msg.HasField("to_snapshot"):
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1711 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1712 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1712,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1713 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1713,))
        if msg.compression != "":
            _t1714 = self._make_value_string(msg.compression)
            result.append(("compression", _t1714,))
        if len(result) == 0:
            return None
        else:
            _t1715 = None
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
            _t1716 = None
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
        flat776 = self._try_flat(msg, self.pretty_transaction)
        if flat776 is not None:
            assert flat776 is not None
            self.write(flat776)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1534 = _dollar_dollar.configure
            else:
                _t1534 = None
            if _dollar_dollar.HasField("sync"):
                _t1535 = _dollar_dollar.sync
            else:
                _t1535 = None
            fields767 = (_t1534, _t1535, _dollar_dollar.epochs,)
            assert fields767 is not None
            unwrapped_fields768 = fields767
            self.write("(transaction")
            self.indent_sexp()
            field769 = unwrapped_fields768[0]
            if field769 is not None:
                self.newline()
                assert field769 is not None
                opt_val770 = field769
                self.pretty_configure(opt_val770)
            field771 = unwrapped_fields768[1]
            if field771 is not None:
                self.newline()
                assert field771 is not None
                opt_val772 = field771
                self.pretty_sync(opt_val772)
            field773 = unwrapped_fields768[2]
            if not len(field773) == 0:
                self.newline()
                for i775, elem774 in enumerate(field773):
                    if (i775 > 0):
                        self.newline()
                    self.pretty_epoch(elem774)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat779 = self._try_flat(msg, self.pretty_configure)
        if flat779 is not None:
            assert flat779 is not None
            self.write(flat779)
            return None
        else:
            _dollar_dollar = msg
            _t1536 = self.deconstruct_configure(_dollar_dollar)
            fields777 = _t1536
            assert fields777 is not None
            unwrapped_fields778 = fields777
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields778)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat783 = self._try_flat(msg, self.pretty_config_dict)
        if flat783 is not None:
            assert flat783 is not None
            self.write(flat783)
            return None
        else:
            fields780 = msg
            self.write("{")
            self.indent()
            if not len(fields780) == 0:
                self.newline()
                for i782, elem781 in enumerate(fields780):
                    if (i782 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem781)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat788 = self._try_flat(msg, self.pretty_config_key_value)
        if flat788 is not None:
            assert flat788 is not None
            self.write(flat788)
            return None
        else:
            _dollar_dollar = msg
            fields784 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields784 is not None
            unwrapped_fields785 = fields784
            self.write(":")
            field786 = unwrapped_fields785[0]
            self.write(field786)
            self.write(" ")
            field787 = unwrapped_fields785[1]
            self.pretty_raw_value(field787)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat814 = self._try_flat(msg, self.pretty_raw_value)
        if flat814 is not None:
            assert flat814 is not None
            self.write(flat814)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1537 = _dollar_dollar.date_value
            else:
                _t1537 = None
            deconstruct_result812 = _t1537
            if deconstruct_result812 is not None:
                assert deconstruct_result812 is not None
                unwrapped813 = deconstruct_result812
                self.pretty_raw_date(unwrapped813)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1538 = _dollar_dollar.datetime_value
                else:
                    _t1538 = None
                deconstruct_result810 = _t1538
                if deconstruct_result810 is not None:
                    assert deconstruct_result810 is not None
                    unwrapped811 = deconstruct_result810
                    self.pretty_raw_datetime(unwrapped811)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1539 = _dollar_dollar.string_value
                    else:
                        _t1539 = None
                    deconstruct_result808 = _t1539
                    if deconstruct_result808 is not None:
                        assert deconstruct_result808 is not None
                        unwrapped809 = deconstruct_result808
                        self.write(self.format_string_value(unwrapped809))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1540 = _dollar_dollar.int32_value
                        else:
                            _t1540 = None
                        deconstruct_result806 = _t1540
                        if deconstruct_result806 is not None:
                            assert deconstruct_result806 is not None
                            unwrapped807 = deconstruct_result806
                            self.write((str(unwrapped807) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1541 = _dollar_dollar.int_value
                            else:
                                _t1541 = None
                            deconstruct_result804 = _t1541
                            if deconstruct_result804 is not None:
                                assert deconstruct_result804 is not None
                                unwrapped805 = deconstruct_result804
                                self.write(str(unwrapped805))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1542 = _dollar_dollar.float32_value
                                else:
                                    _t1542 = None
                                deconstruct_result802 = _t1542
                                if deconstruct_result802 is not None:
                                    assert deconstruct_result802 is not None
                                    unwrapped803 = deconstruct_result802
                                    self.write(self.format_float32_literal(unwrapped803))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1543 = _dollar_dollar.float_value
                                    else:
                                        _t1543 = None
                                    deconstruct_result800 = _t1543
                                    if deconstruct_result800 is not None:
                                        assert deconstruct_result800 is not None
                                        unwrapped801 = deconstruct_result800
                                        self.write(str(unwrapped801))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1544 = _dollar_dollar.uint32_value
                                        else:
                                            _t1544 = None
                                        deconstruct_result798 = _t1544
                                        if deconstruct_result798 is not None:
                                            assert deconstruct_result798 is not None
                                            unwrapped799 = deconstruct_result798
                                            self.write((str(unwrapped799) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1545 = _dollar_dollar.uint128_value
                                            else:
                                                _t1545 = None
                                            deconstruct_result796 = _t1545
                                            if deconstruct_result796 is not None:
                                                assert deconstruct_result796 is not None
                                                unwrapped797 = deconstruct_result796
                                                self.write(self.format_uint128(unwrapped797))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1546 = _dollar_dollar.int128_value
                                                else:
                                                    _t1546 = None
                                                deconstruct_result794 = _t1546
                                                if deconstruct_result794 is not None:
                                                    assert deconstruct_result794 is not None
                                                    unwrapped795 = deconstruct_result794
                                                    self.write(self.format_int128(unwrapped795))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1547 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1547 = None
                                                    deconstruct_result792 = _t1547
                                                    if deconstruct_result792 is not None:
                                                        assert deconstruct_result792 is not None
                                                        unwrapped793 = deconstruct_result792
                                                        self.write(self.format_decimal(unwrapped793))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1548 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1548 = None
                                                        deconstruct_result790 = _t1548
                                                        if deconstruct_result790 is not None:
                                                            assert deconstruct_result790 is not None
                                                            unwrapped791 = deconstruct_result790
                                                            self.pretty_boolean_value(unwrapped791)
                                                        else:
                                                            fields789 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat820 = self._try_flat(msg, self.pretty_raw_date)
        if flat820 is not None:
            assert flat820 is not None
            self.write(flat820)
            return None
        else:
            _dollar_dollar = msg
            fields815 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields815 is not None
            unwrapped_fields816 = fields815
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field817 = unwrapped_fields816[0]
            self.write(str(field817))
            self.newline()
            field818 = unwrapped_fields816[1]
            self.write(str(field818))
            self.newline()
            field819 = unwrapped_fields816[2]
            self.write(str(field819))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat831 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat831 is not None:
            assert flat831 is not None
            self.write(flat831)
            return None
        else:
            _dollar_dollar = msg
            fields821 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields821 is not None
            unwrapped_fields822 = fields821
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field823 = unwrapped_fields822[0]
            self.write(str(field823))
            self.newline()
            field824 = unwrapped_fields822[1]
            self.write(str(field824))
            self.newline()
            field825 = unwrapped_fields822[2]
            self.write(str(field825))
            self.newline()
            field826 = unwrapped_fields822[3]
            self.write(str(field826))
            self.newline()
            field827 = unwrapped_fields822[4]
            self.write(str(field827))
            self.newline()
            field828 = unwrapped_fields822[5]
            self.write(str(field828))
            field829 = unwrapped_fields822[6]
            if field829 is not None:
                self.newline()
                assert field829 is not None
                opt_val830 = field829
                self.write(str(opt_val830))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1549 = ()
        else:
            _t1549 = None
        deconstruct_result834 = _t1549
        if deconstruct_result834 is not None:
            assert deconstruct_result834 is not None
            unwrapped835 = deconstruct_result834
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1550 = ()
            else:
                _t1550 = None
            deconstruct_result832 = _t1550
            if deconstruct_result832 is not None:
                assert deconstruct_result832 is not None
                unwrapped833 = deconstruct_result832
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat840 = self._try_flat(msg, self.pretty_sync)
        if flat840 is not None:
            assert flat840 is not None
            self.write(flat840)
            return None
        else:
            _dollar_dollar = msg
            fields836 = _dollar_dollar.fragments
            assert fields836 is not None
            unwrapped_fields837 = fields836
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields837) == 0:
                self.newline()
                for i839, elem838 in enumerate(unwrapped_fields837):
                    if (i839 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem838)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat843 = self._try_flat(msg, self.pretty_fragment_id)
        if flat843 is not None:
            assert flat843 is not None
            self.write(flat843)
            return None
        else:
            _dollar_dollar = msg
            fields841 = self.fragment_id_to_string(_dollar_dollar)
            assert fields841 is not None
            unwrapped_fields842 = fields841
            self.write(":")
            self.write(unwrapped_fields842)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat850 = self._try_flat(msg, self.pretty_epoch)
        if flat850 is not None:
            assert flat850 is not None
            self.write(flat850)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1551 = _dollar_dollar.writes
            else:
                _t1551 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1552 = _dollar_dollar.reads
            else:
                _t1552 = None
            fields844 = (_t1551, _t1552,)
            assert fields844 is not None
            unwrapped_fields845 = fields844
            self.write("(epoch")
            self.indent_sexp()
            field846 = unwrapped_fields845[0]
            if field846 is not None:
                self.newline()
                assert field846 is not None
                opt_val847 = field846
                self.pretty_epoch_writes(opt_val847)
            field848 = unwrapped_fields845[1]
            if field848 is not None:
                self.newline()
                assert field848 is not None
                opt_val849 = field848
                self.pretty_epoch_reads(opt_val849)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat854 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat854 is not None:
            assert flat854 is not None
            self.write(flat854)
            return None
        else:
            fields851 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields851) == 0:
                self.newline()
                for i853, elem852 in enumerate(fields851):
                    if (i853 > 0):
                        self.newline()
                    self.pretty_write(elem852)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat863 = self._try_flat(msg, self.pretty_write)
        if flat863 is not None:
            assert flat863 is not None
            self.write(flat863)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1553 = _dollar_dollar.define
            else:
                _t1553 = None
            deconstruct_result861 = _t1553
            if deconstruct_result861 is not None:
                assert deconstruct_result861 is not None
                unwrapped862 = deconstruct_result861
                self.pretty_define(unwrapped862)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1554 = _dollar_dollar.undefine
                else:
                    _t1554 = None
                deconstruct_result859 = _t1554
                if deconstruct_result859 is not None:
                    assert deconstruct_result859 is not None
                    unwrapped860 = deconstruct_result859
                    self.pretty_undefine(unwrapped860)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1555 = _dollar_dollar.context
                    else:
                        _t1555 = None
                    deconstruct_result857 = _t1555
                    if deconstruct_result857 is not None:
                        assert deconstruct_result857 is not None
                        unwrapped858 = deconstruct_result857
                        self.pretty_context(unwrapped858)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1556 = _dollar_dollar.snapshot
                        else:
                            _t1556 = None
                        deconstruct_result855 = _t1556
                        if deconstruct_result855 is not None:
                            assert deconstruct_result855 is not None
                            unwrapped856 = deconstruct_result855
                            self.pretty_snapshot(unwrapped856)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat866 = self._try_flat(msg, self.pretty_define)
        if flat866 is not None:
            assert flat866 is not None
            self.write(flat866)
            return None
        else:
            _dollar_dollar = msg
            fields864 = _dollar_dollar.fragment
            assert fields864 is not None
            unwrapped_fields865 = fields864
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields865)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat873 = self._try_flat(msg, self.pretty_fragment)
        if flat873 is not None:
            assert flat873 is not None
            self.write(flat873)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields867 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields867 is not None
            unwrapped_fields868 = fields867
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field869 = unwrapped_fields868[0]
            self.pretty_new_fragment_id(field869)
            field870 = unwrapped_fields868[1]
            if not len(field870) == 0:
                self.newline()
                for i872, elem871 in enumerate(field870):
                    if (i872 > 0):
                        self.newline()
                    self.pretty_declaration(elem871)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat875 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat875 is not None:
            assert flat875 is not None
            self.write(flat875)
            return None
        else:
            fields874 = msg
            self.pretty_fragment_id(fields874)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat884 = self._try_flat(msg, self.pretty_declaration)
        if flat884 is not None:
            assert flat884 is not None
            self.write(flat884)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1557 = getattr(_dollar_dollar, 'def')
            else:
                _t1557 = None
            deconstruct_result882 = _t1557
            if deconstruct_result882 is not None:
                assert deconstruct_result882 is not None
                unwrapped883 = deconstruct_result882
                self.pretty_def(unwrapped883)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1558 = _dollar_dollar.algorithm
                else:
                    _t1558 = None
                deconstruct_result880 = _t1558
                if deconstruct_result880 is not None:
                    assert deconstruct_result880 is not None
                    unwrapped881 = deconstruct_result880
                    self.pretty_algorithm(unwrapped881)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1559 = _dollar_dollar.constraint
                    else:
                        _t1559 = None
                    deconstruct_result878 = _t1559
                    if deconstruct_result878 is not None:
                        assert deconstruct_result878 is not None
                        unwrapped879 = deconstruct_result878
                        self.pretty_constraint(unwrapped879)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1560 = _dollar_dollar.data
                        else:
                            _t1560 = None
                        deconstruct_result876 = _t1560
                        if deconstruct_result876 is not None:
                            assert deconstruct_result876 is not None
                            unwrapped877 = deconstruct_result876
                            self.pretty_data(unwrapped877)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat891 = self._try_flat(msg, self.pretty_def)
        if flat891 is not None:
            assert flat891 is not None
            self.write(flat891)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1561 = _dollar_dollar.attrs
            else:
                _t1561 = None
            fields885 = (_dollar_dollar.name, _dollar_dollar.body, _t1561,)
            assert fields885 is not None
            unwrapped_fields886 = fields885
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field887 = unwrapped_fields886[0]
            self.pretty_relation_id(field887)
            self.newline()
            field888 = unwrapped_fields886[1]
            self.pretty_abstraction(field888)
            field889 = unwrapped_fields886[2]
            if field889 is not None:
                self.newline()
                assert field889 is not None
                opt_val890 = field889
                self.pretty_attrs(opt_val890)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat896 = self._try_flat(msg, self.pretty_relation_id)
        if flat896 is not None:
            assert flat896 is not None
            self.write(flat896)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1563 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1562 = _t1563
            else:
                _t1562 = None
            deconstruct_result894 = _t1562
            if deconstruct_result894 is not None:
                assert deconstruct_result894 is not None
                unwrapped895 = deconstruct_result894
                self.write(":")
                self.write(unwrapped895)
            else:
                _dollar_dollar = msg
                _t1564 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result892 = _t1564
                if deconstruct_result892 is not None:
                    assert deconstruct_result892 is not None
                    unwrapped893 = deconstruct_result892
                    self.write(self.format_uint128(unwrapped893))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat901 = self._try_flat(msg, self.pretty_abstraction)
        if flat901 is not None:
            assert flat901 is not None
            self.write(flat901)
            return None
        else:
            _dollar_dollar = msg
            _t1565 = self.deconstruct_bindings(_dollar_dollar)
            fields897 = (_t1565, _dollar_dollar.value,)
            assert fields897 is not None
            unwrapped_fields898 = fields897
            self.write("(")
            self.indent()
            field899 = unwrapped_fields898[0]
            self.pretty_bindings(field899)
            self.newline()
            field900 = unwrapped_fields898[1]
            self.pretty_formula(field900)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat909 = self._try_flat(msg, self.pretty_bindings)
        if flat909 is not None:
            assert flat909 is not None
            self.write(flat909)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1566 = _dollar_dollar[1]
            else:
                _t1566 = None
            fields902 = (_dollar_dollar[0], _t1566,)
            assert fields902 is not None
            unwrapped_fields903 = fields902
            self.write("[")
            self.indent()
            field904 = unwrapped_fields903[0]
            for i906, elem905 in enumerate(field904):
                if (i906 > 0):
                    self.newline()
                self.pretty_binding(elem905)
            field907 = unwrapped_fields903[1]
            if field907 is not None:
                self.newline()
                assert field907 is not None
                opt_val908 = field907
                self.pretty_value_bindings(opt_val908)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat914 = self._try_flat(msg, self.pretty_binding)
        if flat914 is not None:
            assert flat914 is not None
            self.write(flat914)
            return None
        else:
            _dollar_dollar = msg
            fields910 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields910 is not None
            unwrapped_fields911 = fields910
            field912 = unwrapped_fields911[0]
            self.write(field912)
            self.write("::")
            field913 = unwrapped_fields911[1]
            self.pretty_type(field913)

    def pretty_type(self, msg: logic_pb2.Type):
        flat943 = self._try_flat(msg, self.pretty_type)
        if flat943 is not None:
            assert flat943 is not None
            self.write(flat943)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1567 = _dollar_dollar.unspecified_type
            else:
                _t1567 = None
            deconstruct_result941 = _t1567
            if deconstruct_result941 is not None:
                assert deconstruct_result941 is not None
                unwrapped942 = deconstruct_result941
                self.pretty_unspecified_type(unwrapped942)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1568 = _dollar_dollar.string_type
                else:
                    _t1568 = None
                deconstruct_result939 = _t1568
                if deconstruct_result939 is not None:
                    assert deconstruct_result939 is not None
                    unwrapped940 = deconstruct_result939
                    self.pretty_string_type(unwrapped940)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1569 = _dollar_dollar.int_type
                    else:
                        _t1569 = None
                    deconstruct_result937 = _t1569
                    if deconstruct_result937 is not None:
                        assert deconstruct_result937 is not None
                        unwrapped938 = deconstruct_result937
                        self.pretty_int_type(unwrapped938)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1570 = _dollar_dollar.float_type
                        else:
                            _t1570 = None
                        deconstruct_result935 = _t1570
                        if deconstruct_result935 is not None:
                            assert deconstruct_result935 is not None
                            unwrapped936 = deconstruct_result935
                            self.pretty_float_type(unwrapped936)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1571 = _dollar_dollar.uint128_type
                            else:
                                _t1571 = None
                            deconstruct_result933 = _t1571
                            if deconstruct_result933 is not None:
                                assert deconstruct_result933 is not None
                                unwrapped934 = deconstruct_result933
                                self.pretty_uint128_type(unwrapped934)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1572 = _dollar_dollar.int128_type
                                else:
                                    _t1572 = None
                                deconstruct_result931 = _t1572
                                if deconstruct_result931 is not None:
                                    assert deconstruct_result931 is not None
                                    unwrapped932 = deconstruct_result931
                                    self.pretty_int128_type(unwrapped932)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1573 = _dollar_dollar.date_type
                                    else:
                                        _t1573 = None
                                    deconstruct_result929 = _t1573
                                    if deconstruct_result929 is not None:
                                        assert deconstruct_result929 is not None
                                        unwrapped930 = deconstruct_result929
                                        self.pretty_date_type(unwrapped930)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1574 = _dollar_dollar.datetime_type
                                        else:
                                            _t1574 = None
                                        deconstruct_result927 = _t1574
                                        if deconstruct_result927 is not None:
                                            assert deconstruct_result927 is not None
                                            unwrapped928 = deconstruct_result927
                                            self.pretty_datetime_type(unwrapped928)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1575 = _dollar_dollar.missing_type
                                            else:
                                                _t1575 = None
                                            deconstruct_result925 = _t1575
                                            if deconstruct_result925 is not None:
                                                assert deconstruct_result925 is not None
                                                unwrapped926 = deconstruct_result925
                                                self.pretty_missing_type(unwrapped926)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1576 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1576 = None
                                                deconstruct_result923 = _t1576
                                                if deconstruct_result923 is not None:
                                                    assert deconstruct_result923 is not None
                                                    unwrapped924 = deconstruct_result923
                                                    self.pretty_decimal_type(unwrapped924)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1577 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1577 = None
                                                    deconstruct_result921 = _t1577
                                                    if deconstruct_result921 is not None:
                                                        assert deconstruct_result921 is not None
                                                        unwrapped922 = deconstruct_result921
                                                        self.pretty_boolean_type(unwrapped922)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1578 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1578 = None
                                                        deconstruct_result919 = _t1578
                                                        if deconstruct_result919 is not None:
                                                            assert deconstruct_result919 is not None
                                                            unwrapped920 = deconstruct_result919
                                                            self.pretty_int32_type(unwrapped920)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1579 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1579 = None
                                                            deconstruct_result917 = _t1579
                                                            if deconstruct_result917 is not None:
                                                                assert deconstruct_result917 is not None
                                                                unwrapped918 = deconstruct_result917
                                                                self.pretty_float32_type(unwrapped918)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1580 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1580 = None
                                                                deconstruct_result915 = _t1580
                                                                if deconstruct_result915 is not None:
                                                                    assert deconstruct_result915 is not None
                                                                    unwrapped916 = deconstruct_result915
                                                                    self.pretty_uint32_type(unwrapped916)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields944 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields945 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields946 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields947 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields948 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields949 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields950 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields951 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields952 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat957 = self._try_flat(msg, self.pretty_decimal_type)
        if flat957 is not None:
            assert flat957 is not None
            self.write(flat957)
            return None
        else:
            _dollar_dollar = msg
            fields953 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields953 is not None
            unwrapped_fields954 = fields953
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field955 = unwrapped_fields954[0]
            self.write(str(field955))
            self.newline()
            field956 = unwrapped_fields954[1]
            self.write(str(field956))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields958 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields959 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields960 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields961 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat965 = self._try_flat(msg, self.pretty_value_bindings)
        if flat965 is not None:
            assert flat965 is not None
            self.write(flat965)
            return None
        else:
            fields962 = msg
            self.write("|")
            if not len(fields962) == 0:
                self.write(" ")
                for i964, elem963 in enumerate(fields962):
                    if (i964 > 0):
                        self.newline()
                    self.pretty_binding(elem963)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat992 = self._try_flat(msg, self.pretty_formula)
        if flat992 is not None:
            assert flat992 is not None
            self.write(flat992)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1581 = _dollar_dollar.conjunction
            else:
                _t1581 = None
            deconstruct_result990 = _t1581
            if deconstruct_result990 is not None:
                assert deconstruct_result990 is not None
                unwrapped991 = deconstruct_result990
                self.pretty_true(unwrapped991)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1582 = _dollar_dollar.disjunction
                else:
                    _t1582 = None
                deconstruct_result988 = _t1582
                if deconstruct_result988 is not None:
                    assert deconstruct_result988 is not None
                    unwrapped989 = deconstruct_result988
                    self.pretty_false(unwrapped989)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1583 = _dollar_dollar.exists
                    else:
                        _t1583 = None
                    deconstruct_result986 = _t1583
                    if deconstruct_result986 is not None:
                        assert deconstruct_result986 is not None
                        unwrapped987 = deconstruct_result986
                        self.pretty_exists(unwrapped987)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1584 = _dollar_dollar.reduce
                        else:
                            _t1584 = None
                        deconstruct_result984 = _t1584
                        if deconstruct_result984 is not None:
                            assert deconstruct_result984 is not None
                            unwrapped985 = deconstruct_result984
                            self.pretty_reduce(unwrapped985)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1585 = _dollar_dollar.conjunction
                            else:
                                _t1585 = None
                            deconstruct_result982 = _t1585
                            if deconstruct_result982 is not None:
                                assert deconstruct_result982 is not None
                                unwrapped983 = deconstruct_result982
                                self.pretty_conjunction(unwrapped983)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1586 = _dollar_dollar.disjunction
                                else:
                                    _t1586 = None
                                deconstruct_result980 = _t1586
                                if deconstruct_result980 is not None:
                                    assert deconstruct_result980 is not None
                                    unwrapped981 = deconstruct_result980
                                    self.pretty_disjunction(unwrapped981)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1587 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1587 = None
                                    deconstruct_result978 = _t1587
                                    if deconstruct_result978 is not None:
                                        assert deconstruct_result978 is not None
                                        unwrapped979 = deconstruct_result978
                                        self.pretty_not(unwrapped979)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1588 = _dollar_dollar.ffi
                                        else:
                                            _t1588 = None
                                        deconstruct_result976 = _t1588
                                        if deconstruct_result976 is not None:
                                            assert deconstruct_result976 is not None
                                            unwrapped977 = deconstruct_result976
                                            self.pretty_ffi(unwrapped977)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1589 = _dollar_dollar.atom
                                            else:
                                                _t1589 = None
                                            deconstruct_result974 = _t1589
                                            if deconstruct_result974 is not None:
                                                assert deconstruct_result974 is not None
                                                unwrapped975 = deconstruct_result974
                                                self.pretty_atom(unwrapped975)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1590 = _dollar_dollar.pragma
                                                else:
                                                    _t1590 = None
                                                deconstruct_result972 = _t1590
                                                if deconstruct_result972 is not None:
                                                    assert deconstruct_result972 is not None
                                                    unwrapped973 = deconstruct_result972
                                                    self.pretty_pragma(unwrapped973)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1591 = _dollar_dollar.primitive
                                                    else:
                                                        _t1591 = None
                                                    deconstruct_result970 = _t1591
                                                    if deconstruct_result970 is not None:
                                                        assert deconstruct_result970 is not None
                                                        unwrapped971 = deconstruct_result970
                                                        self.pretty_primitive(unwrapped971)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1592 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1592 = None
                                                        deconstruct_result968 = _t1592
                                                        if deconstruct_result968 is not None:
                                                            assert deconstruct_result968 is not None
                                                            unwrapped969 = deconstruct_result968
                                                            self.pretty_rel_atom(unwrapped969)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1593 = _dollar_dollar.cast
                                                            else:
                                                                _t1593 = None
                                                            deconstruct_result966 = _t1593
                                                            if deconstruct_result966 is not None:
                                                                assert deconstruct_result966 is not None
                                                                unwrapped967 = deconstruct_result966
                                                                self.pretty_cast(unwrapped967)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields993 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields994 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat999 = self._try_flat(msg, self.pretty_exists)
        if flat999 is not None:
            assert flat999 is not None
            self.write(flat999)
            return None
        else:
            _dollar_dollar = msg
            _t1594 = self.deconstruct_bindings(_dollar_dollar.body)
            fields995 = (_t1594, _dollar_dollar.body.value,)
            assert fields995 is not None
            unwrapped_fields996 = fields995
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field997 = unwrapped_fields996[0]
            self.pretty_bindings(field997)
            self.newline()
            field998 = unwrapped_fields996[1]
            self.pretty_formula(field998)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1005 = self._try_flat(msg, self.pretty_reduce)
        if flat1005 is not None:
            assert flat1005 is not None
            self.write(flat1005)
            return None
        else:
            _dollar_dollar = msg
            fields1000 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1000 is not None
            unwrapped_fields1001 = fields1000
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1002 = unwrapped_fields1001[0]
            self.pretty_abstraction(field1002)
            self.newline()
            field1003 = unwrapped_fields1001[1]
            self.pretty_abstraction(field1003)
            self.newline()
            field1004 = unwrapped_fields1001[2]
            self.pretty_terms(field1004)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1009 = self._try_flat(msg, self.pretty_terms)
        if flat1009 is not None:
            assert flat1009 is not None
            self.write(flat1009)
            return None
        else:
            fields1006 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1006) == 0:
                self.newline()
                for i1008, elem1007 in enumerate(fields1006):
                    if (i1008 > 0):
                        self.newline()
                    self.pretty_term(elem1007)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1014 = self._try_flat(msg, self.pretty_term)
        if flat1014 is not None:
            assert flat1014 is not None
            self.write(flat1014)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1595 = _dollar_dollar.var
            else:
                _t1595 = None
            deconstruct_result1012 = _t1595
            if deconstruct_result1012 is not None:
                assert deconstruct_result1012 is not None
                unwrapped1013 = deconstruct_result1012
                self.pretty_var(unwrapped1013)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1596 = _dollar_dollar.constant
                else:
                    _t1596 = None
                deconstruct_result1010 = _t1596
                if deconstruct_result1010 is not None:
                    assert deconstruct_result1010 is not None
                    unwrapped1011 = deconstruct_result1010
                    self.pretty_value(unwrapped1011)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1017 = self._try_flat(msg, self.pretty_var)
        if flat1017 is not None:
            assert flat1017 is not None
            self.write(flat1017)
            return None
        else:
            _dollar_dollar = msg
            fields1015 = _dollar_dollar.name
            assert fields1015 is not None
            unwrapped_fields1016 = fields1015
            self.write(unwrapped_fields1016)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1043 = self._try_flat(msg, self.pretty_value)
        if flat1043 is not None:
            assert flat1043 is not None
            self.write(flat1043)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1597 = _dollar_dollar.date_value
            else:
                _t1597 = None
            deconstruct_result1041 = _t1597
            if deconstruct_result1041 is not None:
                assert deconstruct_result1041 is not None
                unwrapped1042 = deconstruct_result1041
                self.pretty_date(unwrapped1042)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1598 = _dollar_dollar.datetime_value
                else:
                    _t1598 = None
                deconstruct_result1039 = _t1598
                if deconstruct_result1039 is not None:
                    assert deconstruct_result1039 is not None
                    unwrapped1040 = deconstruct_result1039
                    self.pretty_datetime(unwrapped1040)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1599 = _dollar_dollar.string_value
                    else:
                        _t1599 = None
                    deconstruct_result1037 = _t1599
                    if deconstruct_result1037 is not None:
                        assert deconstruct_result1037 is not None
                        unwrapped1038 = deconstruct_result1037
                        self.write(self.format_string_value(unwrapped1038))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1600 = _dollar_dollar.int32_value
                        else:
                            _t1600 = None
                        deconstruct_result1035 = _t1600
                        if deconstruct_result1035 is not None:
                            assert deconstruct_result1035 is not None
                            unwrapped1036 = deconstruct_result1035
                            self.write((str(unwrapped1036) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1601 = _dollar_dollar.int_value
                            else:
                                _t1601 = None
                            deconstruct_result1033 = _t1601
                            if deconstruct_result1033 is not None:
                                assert deconstruct_result1033 is not None
                                unwrapped1034 = deconstruct_result1033
                                self.write(str(unwrapped1034))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1602 = _dollar_dollar.float32_value
                                else:
                                    _t1602 = None
                                deconstruct_result1031 = _t1602
                                if deconstruct_result1031 is not None:
                                    assert deconstruct_result1031 is not None
                                    unwrapped1032 = deconstruct_result1031
                                    self.write(self.format_float32_literal(unwrapped1032))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1603 = _dollar_dollar.float_value
                                    else:
                                        _t1603 = None
                                    deconstruct_result1029 = _t1603
                                    if deconstruct_result1029 is not None:
                                        assert deconstruct_result1029 is not None
                                        unwrapped1030 = deconstruct_result1029
                                        self.write(str(unwrapped1030))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1604 = _dollar_dollar.uint32_value
                                        else:
                                            _t1604 = None
                                        deconstruct_result1027 = _t1604
                                        if deconstruct_result1027 is not None:
                                            assert deconstruct_result1027 is not None
                                            unwrapped1028 = deconstruct_result1027
                                            self.write((str(unwrapped1028) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1605 = _dollar_dollar.uint128_value
                                            else:
                                                _t1605 = None
                                            deconstruct_result1025 = _t1605
                                            if deconstruct_result1025 is not None:
                                                assert deconstruct_result1025 is not None
                                                unwrapped1026 = deconstruct_result1025
                                                self.write(self.format_uint128(unwrapped1026))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1606 = _dollar_dollar.int128_value
                                                else:
                                                    _t1606 = None
                                                deconstruct_result1023 = _t1606
                                                if deconstruct_result1023 is not None:
                                                    assert deconstruct_result1023 is not None
                                                    unwrapped1024 = deconstruct_result1023
                                                    self.write(self.format_int128(unwrapped1024))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1607 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1607 = None
                                                    deconstruct_result1021 = _t1607
                                                    if deconstruct_result1021 is not None:
                                                        assert deconstruct_result1021 is not None
                                                        unwrapped1022 = deconstruct_result1021
                                                        self.write(self.format_decimal(unwrapped1022))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1608 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1608 = None
                                                        deconstruct_result1019 = _t1608
                                                        if deconstruct_result1019 is not None:
                                                            assert deconstruct_result1019 is not None
                                                            unwrapped1020 = deconstruct_result1019
                                                            self.pretty_boolean_value(unwrapped1020)
                                                        else:
                                                            fields1018 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1049 = self._try_flat(msg, self.pretty_date)
        if flat1049 is not None:
            assert flat1049 is not None
            self.write(flat1049)
            return None
        else:
            _dollar_dollar = msg
            fields1044 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1044 is not None
            unwrapped_fields1045 = fields1044
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1046 = unwrapped_fields1045[0]
            self.write(str(field1046))
            self.newline()
            field1047 = unwrapped_fields1045[1]
            self.write(str(field1047))
            self.newline()
            field1048 = unwrapped_fields1045[2]
            self.write(str(field1048))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1060 = self._try_flat(msg, self.pretty_datetime)
        if flat1060 is not None:
            assert flat1060 is not None
            self.write(flat1060)
            return None
        else:
            _dollar_dollar = msg
            fields1050 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1050 is not None
            unwrapped_fields1051 = fields1050
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1052 = unwrapped_fields1051[0]
            self.write(str(field1052))
            self.newline()
            field1053 = unwrapped_fields1051[1]
            self.write(str(field1053))
            self.newline()
            field1054 = unwrapped_fields1051[2]
            self.write(str(field1054))
            self.newline()
            field1055 = unwrapped_fields1051[3]
            self.write(str(field1055))
            self.newline()
            field1056 = unwrapped_fields1051[4]
            self.write(str(field1056))
            self.newline()
            field1057 = unwrapped_fields1051[5]
            self.write(str(field1057))
            field1058 = unwrapped_fields1051[6]
            if field1058 is not None:
                self.newline()
                assert field1058 is not None
                opt_val1059 = field1058
                self.write(str(opt_val1059))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1065 = self._try_flat(msg, self.pretty_conjunction)
        if flat1065 is not None:
            assert flat1065 is not None
            self.write(flat1065)
            return None
        else:
            _dollar_dollar = msg
            fields1061 = _dollar_dollar.args
            assert fields1061 is not None
            unwrapped_fields1062 = fields1061
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1062) == 0:
                self.newline()
                for i1064, elem1063 in enumerate(unwrapped_fields1062):
                    if (i1064 > 0):
                        self.newline()
                    self.pretty_formula(elem1063)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1070 = self._try_flat(msg, self.pretty_disjunction)
        if flat1070 is not None:
            assert flat1070 is not None
            self.write(flat1070)
            return None
        else:
            _dollar_dollar = msg
            fields1066 = _dollar_dollar.args
            assert fields1066 is not None
            unwrapped_fields1067 = fields1066
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1067) == 0:
                self.newline()
                for i1069, elem1068 in enumerate(unwrapped_fields1067):
                    if (i1069 > 0):
                        self.newline()
                    self.pretty_formula(elem1068)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1073 = self._try_flat(msg, self.pretty_not)
        if flat1073 is not None:
            assert flat1073 is not None
            self.write(flat1073)
            return None
        else:
            _dollar_dollar = msg
            fields1071 = _dollar_dollar.arg
            assert fields1071 is not None
            unwrapped_fields1072 = fields1071
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1072)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1079 = self._try_flat(msg, self.pretty_ffi)
        if flat1079 is not None:
            assert flat1079 is not None
            self.write(flat1079)
            return None
        else:
            _dollar_dollar = msg
            fields1074 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1074 is not None
            unwrapped_fields1075 = fields1074
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1076 = unwrapped_fields1075[0]
            self.pretty_name(field1076)
            self.newline()
            field1077 = unwrapped_fields1075[1]
            self.pretty_ffi_args(field1077)
            self.newline()
            field1078 = unwrapped_fields1075[2]
            self.pretty_terms(field1078)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1081 = self._try_flat(msg, self.pretty_name)
        if flat1081 is not None:
            assert flat1081 is not None
            self.write(flat1081)
            return None
        else:
            fields1080 = msg
            self.write(":")
            self.write(fields1080)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1085 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1085 is not None:
            assert flat1085 is not None
            self.write(flat1085)
            return None
        else:
            fields1082 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1082) == 0:
                self.newline()
                for i1084, elem1083 in enumerate(fields1082):
                    if (i1084 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1083)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1092 = self._try_flat(msg, self.pretty_atom)
        if flat1092 is not None:
            assert flat1092 is not None
            self.write(flat1092)
            return None
        else:
            _dollar_dollar = msg
            fields1086 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1086 is not None
            unwrapped_fields1087 = fields1086
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1088 = unwrapped_fields1087[0]
            self.pretty_relation_id(field1088)
            field1089 = unwrapped_fields1087[1]
            if not len(field1089) == 0:
                self.newline()
                for i1091, elem1090 in enumerate(field1089):
                    if (i1091 > 0):
                        self.newline()
                    self.pretty_term(elem1090)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1099 = self._try_flat(msg, self.pretty_pragma)
        if flat1099 is not None:
            assert flat1099 is not None
            self.write(flat1099)
            return None
        else:
            _dollar_dollar = msg
            fields1093 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1093 is not None
            unwrapped_fields1094 = fields1093
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1095 = unwrapped_fields1094[0]
            self.pretty_name(field1095)
            field1096 = unwrapped_fields1094[1]
            if not len(field1096) == 0:
                self.newline()
                for i1098, elem1097 in enumerate(field1096):
                    if (i1098 > 0):
                        self.newline()
                    self.pretty_term(elem1097)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1115 = self._try_flat(msg, self.pretty_primitive)
        if flat1115 is not None:
            assert flat1115 is not None
            self.write(flat1115)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1609 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1609 = None
            guard_result1114 = _t1609
            if guard_result1114 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1610 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1610 = None
                guard_result1113 = _t1610
                if guard_result1113 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1611 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1611 = None
                    guard_result1112 = _t1611
                    if guard_result1112 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1612 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1612 = None
                        guard_result1111 = _t1612
                        if guard_result1111 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1613 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1613 = None
                            guard_result1110 = _t1613
                            if guard_result1110 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1614 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1614 = None
                                guard_result1109 = _t1614
                                if guard_result1109 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1615 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1615 = None
                                    guard_result1108 = _t1615
                                    if guard_result1108 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1616 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1616 = None
                                        guard_result1107 = _t1616
                                        if guard_result1107 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1617 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1617 = None
                                            guard_result1106 = _t1617
                                            if guard_result1106 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1100 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1100 is not None
                                                unwrapped_fields1101 = fields1100
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1102 = unwrapped_fields1101[0]
                                                self.pretty_name(field1102)
                                                field1103 = unwrapped_fields1101[1]
                                                if not len(field1103) == 0:
                                                    self.newline()
                                                    for i1105, elem1104 in enumerate(field1103):
                                                        if (i1105 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1104)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1120 = self._try_flat(msg, self.pretty_eq)
        if flat1120 is not None:
            assert flat1120 is not None
            self.write(flat1120)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1618 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1618 = None
            fields1116 = _t1618
            assert fields1116 is not None
            unwrapped_fields1117 = fields1116
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1118 = unwrapped_fields1117[0]
            self.pretty_term(field1118)
            self.newline()
            field1119 = unwrapped_fields1117[1]
            self.pretty_term(field1119)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1125 = self._try_flat(msg, self.pretty_lt)
        if flat1125 is not None:
            assert flat1125 is not None
            self.write(flat1125)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1619 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1619 = None
            fields1121 = _t1619
            assert fields1121 is not None
            unwrapped_fields1122 = fields1121
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1123 = unwrapped_fields1122[0]
            self.pretty_term(field1123)
            self.newline()
            field1124 = unwrapped_fields1122[1]
            self.pretty_term(field1124)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1130 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1130 is not None:
            assert flat1130 is not None
            self.write(flat1130)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1620 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1620 = None
            fields1126 = _t1620
            assert fields1126 is not None
            unwrapped_fields1127 = fields1126
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1128 = unwrapped_fields1127[0]
            self.pretty_term(field1128)
            self.newline()
            field1129 = unwrapped_fields1127[1]
            self.pretty_term(field1129)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1135 = self._try_flat(msg, self.pretty_gt)
        if flat1135 is not None:
            assert flat1135 is not None
            self.write(flat1135)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1621 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1621 = None
            fields1131 = _t1621
            assert fields1131 is not None
            unwrapped_fields1132 = fields1131
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1133 = unwrapped_fields1132[0]
            self.pretty_term(field1133)
            self.newline()
            field1134 = unwrapped_fields1132[1]
            self.pretty_term(field1134)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1140 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1140 is not None:
            assert flat1140 is not None
            self.write(flat1140)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1622 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1622 = None
            fields1136 = _t1622
            assert fields1136 is not None
            unwrapped_fields1137 = fields1136
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1138 = unwrapped_fields1137[0]
            self.pretty_term(field1138)
            self.newline()
            field1139 = unwrapped_fields1137[1]
            self.pretty_term(field1139)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1146 = self._try_flat(msg, self.pretty_add)
        if flat1146 is not None:
            assert flat1146 is not None
            self.write(flat1146)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1623 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1623 = None
            fields1141 = _t1623
            assert fields1141 is not None
            unwrapped_fields1142 = fields1141
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1143 = unwrapped_fields1142[0]
            self.pretty_term(field1143)
            self.newline()
            field1144 = unwrapped_fields1142[1]
            self.pretty_term(field1144)
            self.newline()
            field1145 = unwrapped_fields1142[2]
            self.pretty_term(field1145)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1152 = self._try_flat(msg, self.pretty_minus)
        if flat1152 is not None:
            assert flat1152 is not None
            self.write(flat1152)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1624 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1624 = None
            fields1147 = _t1624
            assert fields1147 is not None
            unwrapped_fields1148 = fields1147
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1149 = unwrapped_fields1148[0]
            self.pretty_term(field1149)
            self.newline()
            field1150 = unwrapped_fields1148[1]
            self.pretty_term(field1150)
            self.newline()
            field1151 = unwrapped_fields1148[2]
            self.pretty_term(field1151)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1158 = self._try_flat(msg, self.pretty_multiply)
        if flat1158 is not None:
            assert flat1158 is not None
            self.write(flat1158)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1625 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1625 = None
            fields1153 = _t1625
            assert fields1153 is not None
            unwrapped_fields1154 = fields1153
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1155 = unwrapped_fields1154[0]
            self.pretty_term(field1155)
            self.newline()
            field1156 = unwrapped_fields1154[1]
            self.pretty_term(field1156)
            self.newline()
            field1157 = unwrapped_fields1154[2]
            self.pretty_term(field1157)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1164 = self._try_flat(msg, self.pretty_divide)
        if flat1164 is not None:
            assert flat1164 is not None
            self.write(flat1164)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1626 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1626 = None
            fields1159 = _t1626
            assert fields1159 is not None
            unwrapped_fields1160 = fields1159
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1161 = unwrapped_fields1160[0]
            self.pretty_term(field1161)
            self.newline()
            field1162 = unwrapped_fields1160[1]
            self.pretty_term(field1162)
            self.newline()
            field1163 = unwrapped_fields1160[2]
            self.pretty_term(field1163)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1169 = self._try_flat(msg, self.pretty_rel_term)
        if flat1169 is not None:
            assert flat1169 is not None
            self.write(flat1169)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1627 = _dollar_dollar.specialized_value
            else:
                _t1627 = None
            deconstruct_result1167 = _t1627
            if deconstruct_result1167 is not None:
                assert deconstruct_result1167 is not None
                unwrapped1168 = deconstruct_result1167
                self.pretty_specialized_value(unwrapped1168)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1628 = _dollar_dollar.term
                else:
                    _t1628 = None
                deconstruct_result1165 = _t1628
                if deconstruct_result1165 is not None:
                    assert deconstruct_result1165 is not None
                    unwrapped1166 = deconstruct_result1165
                    self.pretty_term(unwrapped1166)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1171 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1171 is not None:
            assert flat1171 is not None
            self.write(flat1171)
            return None
        else:
            fields1170 = msg
            self.write("#")
            self.pretty_raw_value(fields1170)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1178 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1178 is not None:
            assert flat1178 is not None
            self.write(flat1178)
            return None
        else:
            _dollar_dollar = msg
            fields1172 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1172 is not None
            unwrapped_fields1173 = fields1172
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1174 = unwrapped_fields1173[0]
            self.pretty_name(field1174)
            field1175 = unwrapped_fields1173[1]
            if not len(field1175) == 0:
                self.newline()
                for i1177, elem1176 in enumerate(field1175):
                    if (i1177 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1176)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1183 = self._try_flat(msg, self.pretty_cast)
        if flat1183 is not None:
            assert flat1183 is not None
            self.write(flat1183)
            return None
        else:
            _dollar_dollar = msg
            fields1179 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1179 is not None
            unwrapped_fields1180 = fields1179
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1181 = unwrapped_fields1180[0]
            self.pretty_term(field1181)
            self.newline()
            field1182 = unwrapped_fields1180[1]
            self.pretty_term(field1182)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1187 = self._try_flat(msg, self.pretty_attrs)
        if flat1187 is not None:
            assert flat1187 is not None
            self.write(flat1187)
            return None
        else:
            fields1184 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1184) == 0:
                self.newline()
                for i1186, elem1185 in enumerate(fields1184):
                    if (i1186 > 0):
                        self.newline()
                    self.pretty_attribute(elem1185)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1194 = self._try_flat(msg, self.pretty_attribute)
        if flat1194 is not None:
            assert flat1194 is not None
            self.write(flat1194)
            return None
        else:
            _dollar_dollar = msg
            fields1188 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1188 is not None
            unwrapped_fields1189 = fields1188
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1190 = unwrapped_fields1189[0]
            self.pretty_name(field1190)
            field1191 = unwrapped_fields1189[1]
            if not len(field1191) == 0:
                self.newline()
                for i1193, elem1192 in enumerate(field1191):
                    if (i1193 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1192)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1201 = self._try_flat(msg, self.pretty_algorithm)
        if flat1201 is not None:
            assert flat1201 is not None
            self.write(flat1201)
            return None
        else:
            _dollar_dollar = msg
            fields1195 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            assert fields1195 is not None
            unwrapped_fields1196 = fields1195
            self.write("(algorithm")
            self.indent_sexp()
            field1197 = unwrapped_fields1196[0]
            if not len(field1197) == 0:
                self.newline()
                for i1199, elem1198 in enumerate(field1197):
                    if (i1199 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1198)
            self.newline()
            field1200 = unwrapped_fields1196[1]
            self.pretty_script(field1200)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1206 = self._try_flat(msg, self.pretty_script)
        if flat1206 is not None:
            assert flat1206 is not None
            self.write(flat1206)
            return None
        else:
            _dollar_dollar = msg
            fields1202 = _dollar_dollar.constructs
            assert fields1202 is not None
            unwrapped_fields1203 = fields1202
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1203) == 0:
                self.newline()
                for i1205, elem1204 in enumerate(unwrapped_fields1203):
                    if (i1205 > 0):
                        self.newline()
                    self.pretty_construct(elem1204)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1211 = self._try_flat(msg, self.pretty_construct)
        if flat1211 is not None:
            assert flat1211 is not None
            self.write(flat1211)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1629 = _dollar_dollar.loop
            else:
                _t1629 = None
            deconstruct_result1209 = _t1629
            if deconstruct_result1209 is not None:
                assert deconstruct_result1209 is not None
                unwrapped1210 = deconstruct_result1209
                self.pretty_loop(unwrapped1210)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1630 = _dollar_dollar.instruction
                else:
                    _t1630 = None
                deconstruct_result1207 = _t1630
                if deconstruct_result1207 is not None:
                    assert deconstruct_result1207 is not None
                    unwrapped1208 = deconstruct_result1207
                    self.pretty_instruction(unwrapped1208)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1216 = self._try_flat(msg, self.pretty_loop)
        if flat1216 is not None:
            assert flat1216 is not None
            self.write(flat1216)
            return None
        else:
            _dollar_dollar = msg
            fields1212 = (_dollar_dollar.init, _dollar_dollar.body,)
            assert fields1212 is not None
            unwrapped_fields1213 = fields1212
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1214 = unwrapped_fields1213[0]
            self.pretty_init(field1214)
            self.newline()
            field1215 = unwrapped_fields1213[1]
            self.pretty_script(field1215)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1220 = self._try_flat(msg, self.pretty_init)
        if flat1220 is not None:
            assert flat1220 is not None
            self.write(flat1220)
            return None
        else:
            fields1217 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1217) == 0:
                self.newline()
                for i1219, elem1218 in enumerate(fields1217):
                    if (i1219 > 0):
                        self.newline()
                    self.pretty_instruction(elem1218)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1231 = self._try_flat(msg, self.pretty_instruction)
        if flat1231 is not None:
            assert flat1231 is not None
            self.write(flat1231)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1631 = _dollar_dollar.assign
            else:
                _t1631 = None
            deconstruct_result1229 = _t1631
            if deconstruct_result1229 is not None:
                assert deconstruct_result1229 is not None
                unwrapped1230 = deconstruct_result1229
                self.pretty_assign(unwrapped1230)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1632 = _dollar_dollar.upsert
                else:
                    _t1632 = None
                deconstruct_result1227 = _t1632
                if deconstruct_result1227 is not None:
                    assert deconstruct_result1227 is not None
                    unwrapped1228 = deconstruct_result1227
                    self.pretty_upsert(unwrapped1228)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1633 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1633 = None
                    deconstruct_result1225 = _t1633
                    if deconstruct_result1225 is not None:
                        assert deconstruct_result1225 is not None
                        unwrapped1226 = deconstruct_result1225
                        self.pretty_break(unwrapped1226)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1634 = _dollar_dollar.monoid_def
                        else:
                            _t1634 = None
                        deconstruct_result1223 = _t1634
                        if deconstruct_result1223 is not None:
                            assert deconstruct_result1223 is not None
                            unwrapped1224 = deconstruct_result1223
                            self.pretty_monoid_def(unwrapped1224)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1635 = _dollar_dollar.monus_def
                            else:
                                _t1635 = None
                            deconstruct_result1221 = _t1635
                            if deconstruct_result1221 is not None:
                                assert deconstruct_result1221 is not None
                                unwrapped1222 = deconstruct_result1221
                                self.pretty_monus_def(unwrapped1222)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1238 = self._try_flat(msg, self.pretty_assign)
        if flat1238 is not None:
            assert flat1238 is not None
            self.write(flat1238)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1636 = _dollar_dollar.attrs
            else:
                _t1636 = None
            fields1232 = (_dollar_dollar.name, _dollar_dollar.body, _t1636,)
            assert fields1232 is not None
            unwrapped_fields1233 = fields1232
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1234 = unwrapped_fields1233[0]
            self.pretty_relation_id(field1234)
            self.newline()
            field1235 = unwrapped_fields1233[1]
            self.pretty_abstraction(field1235)
            field1236 = unwrapped_fields1233[2]
            if field1236 is not None:
                self.newline()
                assert field1236 is not None
                opt_val1237 = field1236
                self.pretty_attrs(opt_val1237)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1245 = self._try_flat(msg, self.pretty_upsert)
        if flat1245 is not None:
            assert flat1245 is not None
            self.write(flat1245)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1637 = _dollar_dollar.attrs
            else:
                _t1637 = None
            fields1239 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1637,)
            assert fields1239 is not None
            unwrapped_fields1240 = fields1239
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1241 = unwrapped_fields1240[0]
            self.pretty_relation_id(field1241)
            self.newline()
            field1242 = unwrapped_fields1240[1]
            self.pretty_abstraction_with_arity(field1242)
            field1243 = unwrapped_fields1240[2]
            if field1243 is not None:
                self.newline()
                assert field1243 is not None
                opt_val1244 = field1243
                self.pretty_attrs(opt_val1244)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1250 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1250 is not None:
            assert flat1250 is not None
            self.write(flat1250)
            return None
        else:
            _dollar_dollar = msg
            _t1638 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1246 = (_t1638, _dollar_dollar[0].value,)
            assert fields1246 is not None
            unwrapped_fields1247 = fields1246
            self.write("(")
            self.indent()
            field1248 = unwrapped_fields1247[0]
            self.pretty_bindings(field1248)
            self.newline()
            field1249 = unwrapped_fields1247[1]
            self.pretty_formula(field1249)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1257 = self._try_flat(msg, self.pretty_break)
        if flat1257 is not None:
            assert flat1257 is not None
            self.write(flat1257)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1639 = _dollar_dollar.attrs
            else:
                _t1639 = None
            fields1251 = (_dollar_dollar.name, _dollar_dollar.body, _t1639,)
            assert fields1251 is not None
            unwrapped_fields1252 = fields1251
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1253 = unwrapped_fields1252[0]
            self.pretty_relation_id(field1253)
            self.newline()
            field1254 = unwrapped_fields1252[1]
            self.pretty_abstraction(field1254)
            field1255 = unwrapped_fields1252[2]
            if field1255 is not None:
                self.newline()
                assert field1255 is not None
                opt_val1256 = field1255
                self.pretty_attrs(opt_val1256)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1265 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1265 is not None:
            assert flat1265 is not None
            self.write(flat1265)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1640 = _dollar_dollar.attrs
            else:
                _t1640 = None
            fields1258 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1640,)
            assert fields1258 is not None
            unwrapped_fields1259 = fields1258
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1260 = unwrapped_fields1259[0]
            self.pretty_monoid(field1260)
            self.newline()
            field1261 = unwrapped_fields1259[1]
            self.pretty_relation_id(field1261)
            self.newline()
            field1262 = unwrapped_fields1259[2]
            self.pretty_abstraction_with_arity(field1262)
            field1263 = unwrapped_fields1259[3]
            if field1263 is not None:
                self.newline()
                assert field1263 is not None
                opt_val1264 = field1263
                self.pretty_attrs(opt_val1264)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1274 = self._try_flat(msg, self.pretty_monoid)
        if flat1274 is not None:
            assert flat1274 is not None
            self.write(flat1274)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1641 = _dollar_dollar.or_monoid
            else:
                _t1641 = None
            deconstruct_result1272 = _t1641
            if deconstruct_result1272 is not None:
                assert deconstruct_result1272 is not None
                unwrapped1273 = deconstruct_result1272
                self.pretty_or_monoid(unwrapped1273)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1642 = _dollar_dollar.min_monoid
                else:
                    _t1642 = None
                deconstruct_result1270 = _t1642
                if deconstruct_result1270 is not None:
                    assert deconstruct_result1270 is not None
                    unwrapped1271 = deconstruct_result1270
                    self.pretty_min_monoid(unwrapped1271)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1643 = _dollar_dollar.max_monoid
                    else:
                        _t1643 = None
                    deconstruct_result1268 = _t1643
                    if deconstruct_result1268 is not None:
                        assert deconstruct_result1268 is not None
                        unwrapped1269 = deconstruct_result1268
                        self.pretty_max_monoid(unwrapped1269)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1644 = _dollar_dollar.sum_monoid
                        else:
                            _t1644 = None
                        deconstruct_result1266 = _t1644
                        if deconstruct_result1266 is not None:
                            assert deconstruct_result1266 is not None
                            unwrapped1267 = deconstruct_result1266
                            self.pretty_sum_monoid(unwrapped1267)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1275 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1278 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1278 is not None:
            assert flat1278 is not None
            self.write(flat1278)
            return None
        else:
            _dollar_dollar = msg
            fields1276 = _dollar_dollar.type
            assert fields1276 is not None
            unwrapped_fields1277 = fields1276
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1277)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1281 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1281 is not None:
            assert flat1281 is not None
            self.write(flat1281)
            return None
        else:
            _dollar_dollar = msg
            fields1279 = _dollar_dollar.type
            assert fields1279 is not None
            unwrapped_fields1280 = fields1279
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1280)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1284 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1284 is not None:
            assert flat1284 is not None
            self.write(flat1284)
            return None
        else:
            _dollar_dollar = msg
            fields1282 = _dollar_dollar.type
            assert fields1282 is not None
            unwrapped_fields1283 = fields1282
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1283)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1292 = self._try_flat(msg, self.pretty_monus_def)
        if flat1292 is not None:
            assert flat1292 is not None
            self.write(flat1292)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1645 = _dollar_dollar.attrs
            else:
                _t1645 = None
            fields1285 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1645,)
            assert fields1285 is not None
            unwrapped_fields1286 = fields1285
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1287 = unwrapped_fields1286[0]
            self.pretty_monoid(field1287)
            self.newline()
            field1288 = unwrapped_fields1286[1]
            self.pretty_relation_id(field1288)
            self.newline()
            field1289 = unwrapped_fields1286[2]
            self.pretty_abstraction_with_arity(field1289)
            field1290 = unwrapped_fields1286[3]
            if field1290 is not None:
                self.newline()
                assert field1290 is not None
                opt_val1291 = field1290
                self.pretty_attrs(opt_val1291)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1299 = self._try_flat(msg, self.pretty_constraint)
        if flat1299 is not None:
            assert flat1299 is not None
            self.write(flat1299)
            return None
        else:
            _dollar_dollar = msg
            fields1293 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1293 is not None
            unwrapped_fields1294 = fields1293
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1295 = unwrapped_fields1294[0]
            self.pretty_relation_id(field1295)
            self.newline()
            field1296 = unwrapped_fields1294[1]
            self.pretty_abstraction(field1296)
            self.newline()
            field1297 = unwrapped_fields1294[2]
            self.pretty_functional_dependency_keys(field1297)
            self.newline()
            field1298 = unwrapped_fields1294[3]
            self.pretty_functional_dependency_values(field1298)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1303 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1303 is not None:
            assert flat1303 is not None
            self.write(flat1303)
            return None
        else:
            fields1300 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1300) == 0:
                self.newline()
                for i1302, elem1301 in enumerate(fields1300):
                    if (i1302 > 0):
                        self.newline()
                    self.pretty_var(elem1301)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1307 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1307 is not None:
            assert flat1307 is not None
            self.write(flat1307)
            return None
        else:
            fields1304 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1304) == 0:
                self.newline()
                for i1306, elem1305 in enumerate(fields1304):
                    if (i1306 > 0):
                        self.newline()
                    self.pretty_var(elem1305)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1316 = self._try_flat(msg, self.pretty_data)
        if flat1316 is not None:
            assert flat1316 is not None
            self.write(flat1316)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1646 = _dollar_dollar.edb
            else:
                _t1646 = None
            deconstruct_result1314 = _t1646
            if deconstruct_result1314 is not None:
                assert deconstruct_result1314 is not None
                unwrapped1315 = deconstruct_result1314
                self.pretty_edb(unwrapped1315)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1647 = _dollar_dollar.betree_relation
                else:
                    _t1647 = None
                deconstruct_result1312 = _t1647
                if deconstruct_result1312 is not None:
                    assert deconstruct_result1312 is not None
                    unwrapped1313 = deconstruct_result1312
                    self.pretty_betree_relation(unwrapped1313)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1648 = _dollar_dollar.csv_data
                    else:
                        _t1648 = None
                    deconstruct_result1310 = _t1648
                    if deconstruct_result1310 is not None:
                        assert deconstruct_result1310 is not None
                        unwrapped1311 = deconstruct_result1310
                        self.pretty_csv_data(unwrapped1311)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1649 = _dollar_dollar.iceberg_data
                        else:
                            _t1649 = None
                        deconstruct_result1308 = _t1649
                        if deconstruct_result1308 is not None:
                            assert deconstruct_result1308 is not None
                            unwrapped1309 = deconstruct_result1308
                            self.pretty_iceberg_data(unwrapped1309)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1322 = self._try_flat(msg, self.pretty_edb)
        if flat1322 is not None:
            assert flat1322 is not None
            self.write(flat1322)
            return None
        else:
            _dollar_dollar = msg
            fields1317 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1317 is not None
            unwrapped_fields1318 = fields1317
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1319 = unwrapped_fields1318[0]
            self.pretty_relation_id(field1319)
            self.newline()
            field1320 = unwrapped_fields1318[1]
            self.pretty_edb_path(field1320)
            self.newline()
            field1321 = unwrapped_fields1318[2]
            self.pretty_edb_types(field1321)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1326 = self._try_flat(msg, self.pretty_edb_path)
        if flat1326 is not None:
            assert flat1326 is not None
            self.write(flat1326)
            return None
        else:
            fields1323 = msg
            self.write("[")
            self.indent()
            for i1325, elem1324 in enumerate(fields1323):
                if (i1325 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1324))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1330 = self._try_flat(msg, self.pretty_edb_types)
        if flat1330 is not None:
            assert flat1330 is not None
            self.write(flat1330)
            return None
        else:
            fields1327 = msg
            self.write("[")
            self.indent()
            for i1329, elem1328 in enumerate(fields1327):
                if (i1329 > 0):
                    self.newline()
                self.pretty_type(elem1328)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1335 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1335 is not None:
            assert flat1335 is not None
            self.write(flat1335)
            return None
        else:
            _dollar_dollar = msg
            fields1331 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1331 is not None
            unwrapped_fields1332 = fields1331
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1333 = unwrapped_fields1332[0]
            self.pretty_relation_id(field1333)
            self.newline()
            field1334 = unwrapped_fields1332[1]
            self.pretty_betree_info(field1334)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1341 = self._try_flat(msg, self.pretty_betree_info)
        if flat1341 is not None:
            assert flat1341 is not None
            self.write(flat1341)
            return None
        else:
            _dollar_dollar = msg
            _t1650 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1336 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1650,)
            assert fields1336 is not None
            unwrapped_fields1337 = fields1336
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1338 = unwrapped_fields1337[0]
            self.pretty_betree_info_key_types(field1338)
            self.newline()
            field1339 = unwrapped_fields1337[1]
            self.pretty_betree_info_value_types(field1339)
            self.newline()
            field1340 = unwrapped_fields1337[2]
            self.pretty_config_dict(field1340)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1345 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1345 is not None:
            assert flat1345 is not None
            self.write(flat1345)
            return None
        else:
            fields1342 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1342) == 0:
                self.newline()
                for i1344, elem1343 in enumerate(fields1342):
                    if (i1344 > 0):
                        self.newline()
                    self.pretty_type(elem1343)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1349 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1349 is not None:
            assert flat1349 is not None
            self.write(flat1349)
            return None
        else:
            fields1346 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1346) == 0:
                self.newline()
                for i1348, elem1347 in enumerate(fields1346):
                    if (i1348 > 0):
                        self.newline()
                    self.pretty_type(elem1347)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1356 = self._try_flat(msg, self.pretty_csv_data)
        if flat1356 is not None:
            assert flat1356 is not None
            self.write(flat1356)
            return None
        else:
            _dollar_dollar = msg
            fields1350 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1350 is not None
            unwrapped_fields1351 = fields1350
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1352 = unwrapped_fields1351[0]
            self.pretty_csvlocator(field1352)
            self.newline()
            field1353 = unwrapped_fields1351[1]
            self.pretty_csv_config(field1353)
            self.newline()
            field1354 = unwrapped_fields1351[2]
            self.pretty_gnf_columns(field1354)
            self.newline()
            field1355 = unwrapped_fields1351[3]
            self.pretty_csv_asof(field1355)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1363 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1363 is not None:
            assert flat1363 is not None
            self.write(flat1363)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1651 = _dollar_dollar.paths
            else:
                _t1651 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1652 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1652 = None
            fields1357 = (_t1651, _t1652,)
            assert fields1357 is not None
            unwrapped_fields1358 = fields1357
            self.write("(csv_locator")
            self.indent_sexp()
            field1359 = unwrapped_fields1358[0]
            if field1359 is not None:
                self.newline()
                assert field1359 is not None
                opt_val1360 = field1359
                self.pretty_csv_locator_paths(opt_val1360)
            field1361 = unwrapped_fields1358[1]
            if field1361 is not None:
                self.newline()
                assert field1361 is not None
                opt_val1362 = field1361
                self.pretty_csv_locator_inline_data(opt_val1362)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1367 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1367 is not None:
            assert flat1367 is not None
            self.write(flat1367)
            return None
        else:
            fields1364 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1364) == 0:
                self.newline()
                for i1366, elem1365 in enumerate(fields1364):
                    if (i1366 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1365))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1369 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1369 is not None:
            assert flat1369 is not None
            self.write(flat1369)
            return None
        else:
            fields1368 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1368))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1372 = self._try_flat(msg, self.pretty_csv_config)
        if flat1372 is not None:
            assert flat1372 is not None
            self.write(flat1372)
            return None
        else:
            _dollar_dollar = msg
            _t1653 = self.deconstruct_csv_config(_dollar_dollar)
            fields1370 = _t1653
            assert fields1370 is not None
            unwrapped_fields1371 = fields1370
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1371)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1376 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1376 is not None:
            assert flat1376 is not None
            self.write(flat1376)
            return None
        else:
            fields1373 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1373) == 0:
                self.newline()
                for i1375, elem1374 in enumerate(fields1373):
                    if (i1375 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1374)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1385 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1385 is not None:
            assert flat1385 is not None
            self.write(flat1385)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1654 = _dollar_dollar.target_id
            else:
                _t1654 = None
            fields1377 = (_dollar_dollar.column_path, _t1654, _dollar_dollar.types,)
            assert fields1377 is not None
            unwrapped_fields1378 = fields1377
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1379 = unwrapped_fields1378[0]
            self.pretty_gnf_column_path(field1379)
            field1380 = unwrapped_fields1378[1]
            if field1380 is not None:
                self.newline()
                assert field1380 is not None
                opt_val1381 = field1380
                self.pretty_relation_id(opt_val1381)
            self.newline()
            self.write("[")
            field1382 = unwrapped_fields1378[2]
            for i1384, elem1383 in enumerate(field1382):
                if (i1384 > 0):
                    self.newline()
                self.pretty_type(elem1383)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1392 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1392 is not None:
            assert flat1392 is not None
            self.write(flat1392)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1655 = _dollar_dollar[0]
            else:
                _t1655 = None
            deconstruct_result1390 = _t1655
            if deconstruct_result1390 is not None:
                assert deconstruct_result1390 is not None
                unwrapped1391 = deconstruct_result1390
                self.write(self.format_string_value(unwrapped1391))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1656 = _dollar_dollar
                else:
                    _t1656 = None
                deconstruct_result1386 = _t1656
                if deconstruct_result1386 is not None:
                    assert deconstruct_result1386 is not None
                    unwrapped1387 = deconstruct_result1386
                    self.write("[")
                    self.indent()
                    for i1389, elem1388 in enumerate(unwrapped1387):
                        if (i1389 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1388))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1394 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1394 is not None:
            assert flat1394 is not None
            self.write(flat1394)
            return None
        else:
            fields1393 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1393))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1402 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1402 is not None:
            assert flat1402 is not None
            self.write(flat1402)
            return None
        else:
            _dollar_dollar = msg
            _t1657 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1395 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1657,)
            assert fields1395 is not None
            unwrapped_fields1396 = fields1395
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1397 = unwrapped_fields1396[0]
            self.pretty_iceberg_locator(field1397)
            self.newline()
            field1398 = unwrapped_fields1396[1]
            self.pretty_iceberg_config(field1398)
            self.newline()
            field1399 = unwrapped_fields1396[2]
            self.pretty_gnf_columns(field1399)
            field1400 = unwrapped_fields1396[3]
            if field1400 is not None:
                self.newline()
                assert field1400 is not None
                opt_val1401 = field1400
                self.pretty_iceberg_to_snapshot(opt_val1401)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1410 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1410 is not None:
            assert flat1410 is not None
            self.write(flat1410)
            return None
        else:
            _dollar_dollar = msg
            fields1403 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1403 is not None
            unwrapped_fields1404 = fields1403
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("table_name")
            self.newline()
            field1405 = unwrapped_fields1404[0]
            self.write(self.format_string_value(field1405))
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("namespace")
            field1406 = unwrapped_fields1404[1]
            if not len(field1406) == 0:
                self.newline()
                for i1408, elem1407 in enumerate(field1406):
                    if (i1408 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1407))
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("warehouse")
            self.newline()
            field1409 = unwrapped_fields1404[2]
            self.write(self.format_string_value(field1409))
            self.dedent()
            self.write(")")
            self.dedent()
            self.write(")")

    def pretty_iceberg_config(self, msg: logic_pb2.IcebergConfig):
        flat1422 = self._try_flat(msg, self.pretty_iceberg_config)
        if flat1422 is not None:
            assert flat1422 is not None
            self.write(flat1422)
            return None
        else:
            _dollar_dollar = msg
            _t1658 = self.deconstruct_iceberg_config_scope_optional(_dollar_dollar)
            fields1411 = (_dollar_dollar.catalog_uri, _t1658, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1411 is not None
            unwrapped_fields1412 = fields1411
            self.write("(iceberg_config")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("catalog_uri")
            self.newline()
            field1413 = unwrapped_fields1412[0]
            self.write(self.format_string_value(field1413))
            self.dedent()
            self.write(")")
            field1414 = unwrapped_fields1412[1]
            if field1414 is not None:
                self.newline()
                assert field1414 is not None
                opt_val1415 = field1414
                self.pretty_iceberg_config_scope(opt_val1415)
            self.newline()
            self.write("(")
            self.newline()
            self.write("properties")
            field1416 = unwrapped_fields1412[2]
            if not len(field1416) == 0:
                self.newline()
                for i1418, elem1417 in enumerate(field1416):
                    if (i1418 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1417)
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("auth_properties")
            field1419 = unwrapped_fields1412[3]
            if not len(field1419) == 0:
                self.newline()
                for i1421, elem1420 in enumerate(field1419):
                    if (i1421 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1420)
            self.dedent()
            self.write(")")
            self.dedent()
            self.write(")")

    def pretty_iceberg_config_scope(self, msg: str):
        flat1424 = self._try_flat(msg, self.pretty_iceberg_config_scope)
        if flat1424 is not None:
            assert flat1424 is not None
            self.write(flat1424)
            return None
        else:
            fields1423 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1423))
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1429 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1429 is not None:
            assert flat1429 is not None
            self.write(flat1429)
            return None
        else:
            _dollar_dollar = msg
            fields1425 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1425 is not None
            unwrapped_fields1426 = fields1425
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1427 = unwrapped_fields1426[0]
            self.write(self.format_string_value(field1427))
            self.newline()
            field1428 = unwrapped_fields1426[1]
            self.write(self.format_string_value(field1428))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1431 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1431 is not None:
            assert flat1431 is not None
            self.write(flat1431)
            return None
        else:
            fields1430 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1430))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1434 = self._try_flat(msg, self.pretty_undefine)
        if flat1434 is not None:
            assert flat1434 is not None
            self.write(flat1434)
            return None
        else:
            _dollar_dollar = msg
            fields1432 = _dollar_dollar.fragment_id
            assert fields1432 is not None
            unwrapped_fields1433 = fields1432
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1433)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1439 = self._try_flat(msg, self.pretty_context)
        if flat1439 is not None:
            assert flat1439 is not None
            self.write(flat1439)
            return None
        else:
            _dollar_dollar = msg
            fields1435 = _dollar_dollar.relations
            assert fields1435 is not None
            unwrapped_fields1436 = fields1435
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1436) == 0:
                self.newline()
                for i1438, elem1437 in enumerate(unwrapped_fields1436):
                    if (i1438 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1437)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1444 = self._try_flat(msg, self.pretty_snapshot)
        if flat1444 is not None:
            assert flat1444 is not None
            self.write(flat1444)
            return None
        else:
            _dollar_dollar = msg
            fields1440 = _dollar_dollar.mappings
            assert fields1440 is not None
            unwrapped_fields1441 = fields1440
            self.write("(snapshot")
            self.indent_sexp()
            if not len(unwrapped_fields1441) == 0:
                self.newline()
                for i1443, elem1442 in enumerate(unwrapped_fields1441):
                    if (i1443 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1442)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1449 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1449 is not None:
            assert flat1449 is not None
            self.write(flat1449)
            return None
        else:
            _dollar_dollar = msg
            fields1445 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1445 is not None
            unwrapped_fields1446 = fields1445
            field1447 = unwrapped_fields1446[0]
            self.pretty_edb_path(field1447)
            self.write(" ")
            field1448 = unwrapped_fields1446[1]
            self.pretty_relation_id(field1448)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1453 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1453 is not None:
            assert flat1453 is not None
            self.write(flat1453)
            return None
        else:
            fields1450 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1450) == 0:
                self.newline()
                for i1452, elem1451 in enumerate(fields1450):
                    if (i1452 > 0):
                        self.newline()
                    self.pretty_read(elem1451)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1464 = self._try_flat(msg, self.pretty_read)
        if flat1464 is not None:
            assert flat1464 is not None
            self.write(flat1464)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1659 = _dollar_dollar.demand
            else:
                _t1659 = None
            deconstruct_result1462 = _t1659
            if deconstruct_result1462 is not None:
                assert deconstruct_result1462 is not None
                unwrapped1463 = deconstruct_result1462
                self.pretty_demand(unwrapped1463)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1660 = _dollar_dollar.output
                else:
                    _t1660 = None
                deconstruct_result1460 = _t1660
                if deconstruct_result1460 is not None:
                    assert deconstruct_result1460 is not None
                    unwrapped1461 = deconstruct_result1460
                    self.pretty_output(unwrapped1461)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1661 = _dollar_dollar.what_if
                    else:
                        _t1661 = None
                    deconstruct_result1458 = _t1661
                    if deconstruct_result1458 is not None:
                        assert deconstruct_result1458 is not None
                        unwrapped1459 = deconstruct_result1458
                        self.pretty_what_if(unwrapped1459)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1662 = _dollar_dollar.abort
                        else:
                            _t1662 = None
                        deconstruct_result1456 = _t1662
                        if deconstruct_result1456 is not None:
                            assert deconstruct_result1456 is not None
                            unwrapped1457 = deconstruct_result1456
                            self.pretty_abort(unwrapped1457)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1663 = _dollar_dollar.export
                            else:
                                _t1663 = None
                            deconstruct_result1454 = _t1663
                            if deconstruct_result1454 is not None:
                                assert deconstruct_result1454 is not None
                                unwrapped1455 = deconstruct_result1454
                                self.pretty_export(unwrapped1455)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1467 = self._try_flat(msg, self.pretty_demand)
        if flat1467 is not None:
            assert flat1467 is not None
            self.write(flat1467)
            return None
        else:
            _dollar_dollar = msg
            fields1465 = _dollar_dollar.relation_id
            assert fields1465 is not None
            unwrapped_fields1466 = fields1465
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1466)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1472 = self._try_flat(msg, self.pretty_output)
        if flat1472 is not None:
            assert flat1472 is not None
            self.write(flat1472)
            return None
        else:
            _dollar_dollar = msg
            fields1468 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1468 is not None
            unwrapped_fields1469 = fields1468
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1470 = unwrapped_fields1469[0]
            self.pretty_name(field1470)
            self.newline()
            field1471 = unwrapped_fields1469[1]
            self.pretty_relation_id(field1471)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1477 = self._try_flat(msg, self.pretty_what_if)
        if flat1477 is not None:
            assert flat1477 is not None
            self.write(flat1477)
            return None
        else:
            _dollar_dollar = msg
            fields1473 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1473 is not None
            unwrapped_fields1474 = fields1473
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1475 = unwrapped_fields1474[0]
            self.pretty_name(field1475)
            self.newline()
            field1476 = unwrapped_fields1474[1]
            self.pretty_epoch(field1476)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1483 = self._try_flat(msg, self.pretty_abort)
        if flat1483 is not None:
            assert flat1483 is not None
            self.write(flat1483)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1664 = _dollar_dollar.name
            else:
                _t1664 = None
            fields1478 = (_t1664, _dollar_dollar.relation_id,)
            assert fields1478 is not None
            unwrapped_fields1479 = fields1478
            self.write("(abort")
            self.indent_sexp()
            field1480 = unwrapped_fields1479[0]
            if field1480 is not None:
                self.newline()
                assert field1480 is not None
                opt_val1481 = field1480
                self.pretty_name(opt_val1481)
            self.newline()
            field1482 = unwrapped_fields1479[1]
            self.pretty_relation_id(field1482)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1488 = self._try_flat(msg, self.pretty_export)
        if flat1488 is not None:
            assert flat1488 is not None
            self.write(flat1488)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1665 = _dollar_dollar.csv_config
            else:
                _t1665 = None
            deconstruct_result1486 = _t1665
            if deconstruct_result1486 is not None:
                assert deconstruct_result1486 is not None
                unwrapped1487 = deconstruct_result1486
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1487)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1666 = _dollar_dollar.iceberg_config
                else:
                    _t1666 = None
                deconstruct_result1484 = _t1666
                if deconstruct_result1484 is not None:
                    assert deconstruct_result1484 is not None
                    unwrapped1485 = deconstruct_result1484
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1485)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1499 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1499 is not None:
            assert flat1499 is not None
            self.write(flat1499)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1667 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1667 = None
            deconstruct_result1494 = _t1667
            if deconstruct_result1494 is not None:
                assert deconstruct_result1494 is not None
                unwrapped1495 = deconstruct_result1494
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1496 = unwrapped1495[0]
                self.pretty_export_csv_path(field1496)
                self.newline()
                field1497 = unwrapped1495[1]
                self.pretty_export_csv_source(field1497)
                self.newline()
                field1498 = unwrapped1495[2]
                self.pretty_csv_config(field1498)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1669 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1668 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1669,)
                else:
                    _t1668 = None
                deconstruct_result1489 = _t1668
                if deconstruct_result1489 is not None:
                    assert deconstruct_result1489 is not None
                    unwrapped1490 = deconstruct_result1489
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1491 = unwrapped1490[0]
                    self.pretty_export_csv_path(field1491)
                    self.newline()
                    field1492 = unwrapped1490[1]
                    self.pretty_export_csv_columns_list(field1492)
                    self.newline()
                    field1493 = unwrapped1490[2]
                    self.pretty_config_dict(field1493)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1501 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1501 is not None:
            assert flat1501 is not None
            self.write(flat1501)
            return None
        else:
            fields1500 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1500))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1508 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1508 is not None:
            assert flat1508 is not None
            self.write(flat1508)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1670 = _dollar_dollar.gnf_columns.columns
            else:
                _t1670 = None
            deconstruct_result1504 = _t1670
            if deconstruct_result1504 is not None:
                assert deconstruct_result1504 is not None
                unwrapped1505 = deconstruct_result1504
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1505) == 0:
                    self.newline()
                    for i1507, elem1506 in enumerate(unwrapped1505):
                        if (i1507 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1506)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1671 = _dollar_dollar.table_def
                else:
                    _t1671 = None
                deconstruct_result1502 = _t1671
                if deconstruct_result1502 is not None:
                    assert deconstruct_result1502 is not None
                    unwrapped1503 = deconstruct_result1502
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1503)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1513 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1513 is not None:
            assert flat1513 is not None
            self.write(flat1513)
            return None
        else:
            _dollar_dollar = msg
            fields1509 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1509 is not None
            unwrapped_fields1510 = fields1509
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1511 = unwrapped_fields1510[0]
            self.write(self.format_string_value(field1511))
            self.newline()
            field1512 = unwrapped_fields1510[1]
            self.pretty_relation_id(field1512)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1517 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1517 is not None:
            assert flat1517 is not None
            self.write(flat1517)
            return None
        else:
            fields1514 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1514) == 0:
                self.newline()
                for i1516, elem1515 in enumerate(fields1514):
                    if (i1516 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1515)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1527 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1527 is not None:
            assert flat1527 is not None
            self.write(flat1527)
            return None
        else:
            _dollar_dollar = msg
            _t1672 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1518 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1672,)
            assert fields1518 is not None
            unwrapped_fields1519 = fields1518
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1520 = unwrapped_fields1519[0]
            self.pretty_iceberg_locator(field1520)
            self.newline()
            field1521 = unwrapped_fields1519[1]
            self.pretty_iceberg_config(field1521)
            self.newline()
            self.write("(")
            self.newline()
            self.write("columns")
            field1522 = unwrapped_fields1519[2]
            if not len(field1522) == 0:
                self.newline()
                for i1524, elem1523 in enumerate(field1522):
                    if (i1524 > 0):
                        self.newline()
                    self.pretty_iceberg_export_column(elem1523)
            self.dedent()
            self.write(")")
            field1525 = unwrapped_fields1519[3]
            if field1525 is not None:
                self.newline()
                assert field1525 is not None
                opt_val1526 = field1525
                self.pretty_config_dict(opt_val1526)
            self.dedent()
            self.write(")")

    def pretty_iceberg_export_column(self, msg: transactions_pb2.IcebergExportColumn):
        flat1533 = self._try_flat(msg, self.pretty_iceberg_export_column)
        if flat1533 is not None:
            assert flat1533 is not None
            self.write(flat1533)
            return None
        else:
            _dollar_dollar = msg
            fields1528 = (_dollar_dollar.name, _dollar_dollar.type, _dollar_dollar.nullable,)
            assert fields1528 is not None
            unwrapped_fields1529 = fields1528
            self.write("(iceberg_column")
            self.indent_sexp()
            self.newline()
            field1530 = unwrapped_fields1529[0]
            self.write(self.format_string_value(field1530))
            self.newline()
            field1531 = unwrapped_fields1529[1]
            self.pretty_type(field1531)
            self.newline()
            field1532 = unwrapped_fields1529[2]
            self.pretty_boolean_value(field1532)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1717 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1717)
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
        elif isinstance(msg, logic_pb2.IcebergConfig):
            self.pretty_iceberg_config(msg)
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
        elif isinstance(msg, transactions_pb2.IcebergExportColumn):
            self.pretty_iceberg_export_column(msg)
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
