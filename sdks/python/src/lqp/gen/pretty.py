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
        _t1681 = logic_pb2.Value(int32_value=v)
        return _t1681

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1682 = logic_pb2.Value(int_value=v)
        return _t1682

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1683 = logic_pb2.Value(float_value=v)
        return _t1683

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1684 = logic_pb2.Value(string_value=v)
        return _t1684

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1685 = logic_pb2.Value(boolean_value=v)
        return _t1685

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1686 = logic_pb2.Value(uint128_value=v)
        return _t1686

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1687 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1687,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1688 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1688,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1689 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1689,))
        _t1690 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1690,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1691 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1691,))
        _t1692 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1692,))
        if msg.new_line != "":
            _t1693 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1693,))
        _t1694 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1694,))
        _t1695 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1695,))
        _t1696 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1696,))
        if msg.comment != "":
            _t1697 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1697,))
        for missing_string in msg.missing_strings:
            _t1698 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1698,))
        _t1699 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1699,))
        _t1700 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1700,))
        _t1701 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1701,))
        if msg.partition_size_mb != 0:
            _t1702 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1702,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1703 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1703,))
        _t1704 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1704,))
        _t1705 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1705,))
        _t1706 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1706,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1707 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1707,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1708 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1708,))
        _t1709 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1709,))
        _t1710 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1710,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1711 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1711,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1712 = self._make_value_string(msg.compression)
            result.append(("compression", _t1712,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1713 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1713,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1714 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1714,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1715 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1715,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1716 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1716,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1717 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1717,))
        return sorted(result)

    def deconstruct_iceberg_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1718 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1719 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1720 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1720,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1721 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1721,))
        if msg.compression != "":
            _t1722 = self._make_value_string(msg.compression)
            result.append(("compression", _t1722,))
        if len(result) == 0:
            return None
        else:
            _t1723 = None
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
            _t1724 = None
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
        flat780 = self._try_flat(msg, self.pretty_transaction)
        if flat780 is not None:
            assert flat780 is not None
            self.write(flat780)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1542 = _dollar_dollar.configure
            else:
                _t1542 = None
            if _dollar_dollar.HasField("sync"):
                _t1543 = _dollar_dollar.sync
            else:
                _t1543 = None
            fields771 = (_t1542, _t1543, _dollar_dollar.epochs,)
            assert fields771 is not None
            unwrapped_fields772 = fields771
            self.write("(transaction")
            self.indent_sexp()
            field773 = unwrapped_fields772[0]
            if field773 is not None:
                self.newline()
                assert field773 is not None
                opt_val774 = field773
                self.pretty_configure(opt_val774)
            field775 = unwrapped_fields772[1]
            if field775 is not None:
                self.newline()
                assert field775 is not None
                opt_val776 = field775
                self.pretty_sync(opt_val776)
            field777 = unwrapped_fields772[2]
            if not len(field777) == 0:
                self.newline()
                for i779, elem778 in enumerate(field777):
                    if (i779 > 0):
                        self.newline()
                    self.pretty_epoch(elem778)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat783 = self._try_flat(msg, self.pretty_configure)
        if flat783 is not None:
            assert flat783 is not None
            self.write(flat783)
            return None
        else:
            _dollar_dollar = msg
            _t1544 = self.deconstruct_configure(_dollar_dollar)
            fields781 = _t1544
            assert fields781 is not None
            unwrapped_fields782 = fields781
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields782)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat787 = self._try_flat(msg, self.pretty_config_dict)
        if flat787 is not None:
            assert flat787 is not None
            self.write(flat787)
            return None
        else:
            fields784 = msg
            self.write("{")
            self.indent()
            if not len(fields784) == 0:
                self.newline()
                for i786, elem785 in enumerate(fields784):
                    if (i786 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem785)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat792 = self._try_flat(msg, self.pretty_config_key_value)
        if flat792 is not None:
            assert flat792 is not None
            self.write(flat792)
            return None
        else:
            _dollar_dollar = msg
            fields788 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields788 is not None
            unwrapped_fields789 = fields788
            self.write(":")
            field790 = unwrapped_fields789[0]
            self.write(field790)
            self.write(" ")
            field791 = unwrapped_fields789[1]
            self.pretty_raw_value(field791)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat818 = self._try_flat(msg, self.pretty_raw_value)
        if flat818 is not None:
            assert flat818 is not None
            self.write(flat818)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1545 = _dollar_dollar.date_value
            else:
                _t1545 = None
            deconstruct_result816 = _t1545
            if deconstruct_result816 is not None:
                assert deconstruct_result816 is not None
                unwrapped817 = deconstruct_result816
                self.pretty_raw_date(unwrapped817)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1546 = _dollar_dollar.datetime_value
                else:
                    _t1546 = None
                deconstruct_result814 = _t1546
                if deconstruct_result814 is not None:
                    assert deconstruct_result814 is not None
                    unwrapped815 = deconstruct_result814
                    self.pretty_raw_datetime(unwrapped815)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1547 = _dollar_dollar.string_value
                    else:
                        _t1547 = None
                    deconstruct_result812 = _t1547
                    if deconstruct_result812 is not None:
                        assert deconstruct_result812 is not None
                        unwrapped813 = deconstruct_result812
                        self.write(self.format_string_value(unwrapped813))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1548 = _dollar_dollar.int32_value
                        else:
                            _t1548 = None
                        deconstruct_result810 = _t1548
                        if deconstruct_result810 is not None:
                            assert deconstruct_result810 is not None
                            unwrapped811 = deconstruct_result810
                            self.write((str(unwrapped811) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1549 = _dollar_dollar.int_value
                            else:
                                _t1549 = None
                            deconstruct_result808 = _t1549
                            if deconstruct_result808 is not None:
                                assert deconstruct_result808 is not None
                                unwrapped809 = deconstruct_result808
                                self.write(str(unwrapped809))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1550 = _dollar_dollar.float32_value
                                else:
                                    _t1550 = None
                                deconstruct_result806 = _t1550
                                if deconstruct_result806 is not None:
                                    assert deconstruct_result806 is not None
                                    unwrapped807 = deconstruct_result806
                                    self.write(self.format_float32_literal(unwrapped807))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1551 = _dollar_dollar.float_value
                                    else:
                                        _t1551 = None
                                    deconstruct_result804 = _t1551
                                    if deconstruct_result804 is not None:
                                        assert deconstruct_result804 is not None
                                        unwrapped805 = deconstruct_result804
                                        self.write(str(unwrapped805))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1552 = _dollar_dollar.uint32_value
                                        else:
                                            _t1552 = None
                                        deconstruct_result802 = _t1552
                                        if deconstruct_result802 is not None:
                                            assert deconstruct_result802 is not None
                                            unwrapped803 = deconstruct_result802
                                            self.write((str(unwrapped803) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1553 = _dollar_dollar.uint128_value
                                            else:
                                                _t1553 = None
                                            deconstruct_result800 = _t1553
                                            if deconstruct_result800 is not None:
                                                assert deconstruct_result800 is not None
                                                unwrapped801 = deconstruct_result800
                                                self.write(self.format_uint128(unwrapped801))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1554 = _dollar_dollar.int128_value
                                                else:
                                                    _t1554 = None
                                                deconstruct_result798 = _t1554
                                                if deconstruct_result798 is not None:
                                                    assert deconstruct_result798 is not None
                                                    unwrapped799 = deconstruct_result798
                                                    self.write(self.format_int128(unwrapped799))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1555 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1555 = None
                                                    deconstruct_result796 = _t1555
                                                    if deconstruct_result796 is not None:
                                                        assert deconstruct_result796 is not None
                                                        unwrapped797 = deconstruct_result796
                                                        self.write(self.format_decimal(unwrapped797))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1556 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1556 = None
                                                        deconstruct_result794 = _t1556
                                                        if deconstruct_result794 is not None:
                                                            assert deconstruct_result794 is not None
                                                            unwrapped795 = deconstruct_result794
                                                            self.pretty_boolean_value(unwrapped795)
                                                        else:
                                                            fields793 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat824 = self._try_flat(msg, self.pretty_raw_date)
        if flat824 is not None:
            assert flat824 is not None
            self.write(flat824)
            return None
        else:
            _dollar_dollar = msg
            fields819 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields819 is not None
            unwrapped_fields820 = fields819
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field821 = unwrapped_fields820[0]
            self.write(str(field821))
            self.newline()
            field822 = unwrapped_fields820[1]
            self.write(str(field822))
            self.newline()
            field823 = unwrapped_fields820[2]
            self.write(str(field823))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat835 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat835 is not None:
            assert flat835 is not None
            self.write(flat835)
            return None
        else:
            _dollar_dollar = msg
            fields825 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields825 is not None
            unwrapped_fields826 = fields825
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field827 = unwrapped_fields826[0]
            self.write(str(field827))
            self.newline()
            field828 = unwrapped_fields826[1]
            self.write(str(field828))
            self.newline()
            field829 = unwrapped_fields826[2]
            self.write(str(field829))
            self.newline()
            field830 = unwrapped_fields826[3]
            self.write(str(field830))
            self.newline()
            field831 = unwrapped_fields826[4]
            self.write(str(field831))
            self.newline()
            field832 = unwrapped_fields826[5]
            self.write(str(field832))
            field833 = unwrapped_fields826[6]
            if field833 is not None:
                self.newline()
                assert field833 is not None
                opt_val834 = field833
                self.write(str(opt_val834))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1557 = ()
        else:
            _t1557 = None
        deconstruct_result838 = _t1557
        if deconstruct_result838 is not None:
            assert deconstruct_result838 is not None
            unwrapped839 = deconstruct_result838
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1558 = ()
            else:
                _t1558 = None
            deconstruct_result836 = _t1558
            if deconstruct_result836 is not None:
                assert deconstruct_result836 is not None
                unwrapped837 = deconstruct_result836
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat844 = self._try_flat(msg, self.pretty_sync)
        if flat844 is not None:
            assert flat844 is not None
            self.write(flat844)
            return None
        else:
            _dollar_dollar = msg
            fields840 = _dollar_dollar.fragments
            assert fields840 is not None
            unwrapped_fields841 = fields840
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields841) == 0:
                self.newline()
                for i843, elem842 in enumerate(unwrapped_fields841):
                    if (i843 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem842)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat847 = self._try_flat(msg, self.pretty_fragment_id)
        if flat847 is not None:
            assert flat847 is not None
            self.write(flat847)
            return None
        else:
            _dollar_dollar = msg
            fields845 = self.fragment_id_to_string(_dollar_dollar)
            assert fields845 is not None
            unwrapped_fields846 = fields845
            self.write(":")
            self.write(unwrapped_fields846)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat854 = self._try_flat(msg, self.pretty_epoch)
        if flat854 is not None:
            assert flat854 is not None
            self.write(flat854)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1559 = _dollar_dollar.writes
            else:
                _t1559 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1560 = _dollar_dollar.reads
            else:
                _t1560 = None
            fields848 = (_t1559, _t1560,)
            assert fields848 is not None
            unwrapped_fields849 = fields848
            self.write("(epoch")
            self.indent_sexp()
            field850 = unwrapped_fields849[0]
            if field850 is not None:
                self.newline()
                assert field850 is not None
                opt_val851 = field850
                self.pretty_epoch_writes(opt_val851)
            field852 = unwrapped_fields849[1]
            if field852 is not None:
                self.newline()
                assert field852 is not None
                opt_val853 = field852
                self.pretty_epoch_reads(opt_val853)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat858 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat858 is not None:
            assert flat858 is not None
            self.write(flat858)
            return None
        else:
            fields855 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields855) == 0:
                self.newline()
                for i857, elem856 in enumerate(fields855):
                    if (i857 > 0):
                        self.newline()
                    self.pretty_write(elem856)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat867 = self._try_flat(msg, self.pretty_write)
        if flat867 is not None:
            assert flat867 is not None
            self.write(flat867)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1561 = _dollar_dollar.define
            else:
                _t1561 = None
            deconstruct_result865 = _t1561
            if deconstruct_result865 is not None:
                assert deconstruct_result865 is not None
                unwrapped866 = deconstruct_result865
                self.pretty_define(unwrapped866)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1562 = _dollar_dollar.undefine
                else:
                    _t1562 = None
                deconstruct_result863 = _t1562
                if deconstruct_result863 is not None:
                    assert deconstruct_result863 is not None
                    unwrapped864 = deconstruct_result863
                    self.pretty_undefine(unwrapped864)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1563 = _dollar_dollar.context
                    else:
                        _t1563 = None
                    deconstruct_result861 = _t1563
                    if deconstruct_result861 is not None:
                        assert deconstruct_result861 is not None
                        unwrapped862 = deconstruct_result861
                        self.pretty_context(unwrapped862)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1564 = _dollar_dollar.snapshot
                        else:
                            _t1564 = None
                        deconstruct_result859 = _t1564
                        if deconstruct_result859 is not None:
                            assert deconstruct_result859 is not None
                            unwrapped860 = deconstruct_result859
                            self.pretty_snapshot(unwrapped860)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat870 = self._try_flat(msg, self.pretty_define)
        if flat870 is not None:
            assert flat870 is not None
            self.write(flat870)
            return None
        else:
            _dollar_dollar = msg
            fields868 = _dollar_dollar.fragment
            assert fields868 is not None
            unwrapped_fields869 = fields868
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields869)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat877 = self._try_flat(msg, self.pretty_fragment)
        if flat877 is not None:
            assert flat877 is not None
            self.write(flat877)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields871 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields871 is not None
            unwrapped_fields872 = fields871
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field873 = unwrapped_fields872[0]
            self.pretty_new_fragment_id(field873)
            field874 = unwrapped_fields872[1]
            if not len(field874) == 0:
                self.newline()
                for i876, elem875 in enumerate(field874):
                    if (i876 > 0):
                        self.newline()
                    self.pretty_declaration(elem875)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat879 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat879 is not None:
            assert flat879 is not None
            self.write(flat879)
            return None
        else:
            fields878 = msg
            self.pretty_fragment_id(fields878)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat888 = self._try_flat(msg, self.pretty_declaration)
        if flat888 is not None:
            assert flat888 is not None
            self.write(flat888)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1565 = getattr(_dollar_dollar, 'def')
            else:
                _t1565 = None
            deconstruct_result886 = _t1565
            if deconstruct_result886 is not None:
                assert deconstruct_result886 is not None
                unwrapped887 = deconstruct_result886
                self.pretty_def(unwrapped887)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1566 = _dollar_dollar.algorithm
                else:
                    _t1566 = None
                deconstruct_result884 = _t1566
                if deconstruct_result884 is not None:
                    assert deconstruct_result884 is not None
                    unwrapped885 = deconstruct_result884
                    self.pretty_algorithm(unwrapped885)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1567 = _dollar_dollar.constraint
                    else:
                        _t1567 = None
                    deconstruct_result882 = _t1567
                    if deconstruct_result882 is not None:
                        assert deconstruct_result882 is not None
                        unwrapped883 = deconstruct_result882
                        self.pretty_constraint(unwrapped883)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1568 = _dollar_dollar.data
                        else:
                            _t1568 = None
                        deconstruct_result880 = _t1568
                        if deconstruct_result880 is not None:
                            assert deconstruct_result880 is not None
                            unwrapped881 = deconstruct_result880
                            self.pretty_data(unwrapped881)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat895 = self._try_flat(msg, self.pretty_def)
        if flat895 is not None:
            assert flat895 is not None
            self.write(flat895)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1569 = _dollar_dollar.attrs
            else:
                _t1569 = None
            fields889 = (_dollar_dollar.name, _dollar_dollar.body, _t1569,)
            assert fields889 is not None
            unwrapped_fields890 = fields889
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field891 = unwrapped_fields890[0]
            self.pretty_relation_id(field891)
            self.newline()
            field892 = unwrapped_fields890[1]
            self.pretty_abstraction(field892)
            field893 = unwrapped_fields890[2]
            if field893 is not None:
                self.newline()
                assert field893 is not None
                opt_val894 = field893
                self.pretty_attrs(opt_val894)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat900 = self._try_flat(msg, self.pretty_relation_id)
        if flat900 is not None:
            assert flat900 is not None
            self.write(flat900)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1571 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1570 = _t1571
            else:
                _t1570 = None
            deconstruct_result898 = _t1570
            if deconstruct_result898 is not None:
                assert deconstruct_result898 is not None
                unwrapped899 = deconstruct_result898
                self.write(":")
                self.write(unwrapped899)
            else:
                _dollar_dollar = msg
                _t1572 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result896 = _t1572
                if deconstruct_result896 is not None:
                    assert deconstruct_result896 is not None
                    unwrapped897 = deconstruct_result896
                    self.write(self.format_uint128(unwrapped897))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat905 = self._try_flat(msg, self.pretty_abstraction)
        if flat905 is not None:
            assert flat905 is not None
            self.write(flat905)
            return None
        else:
            _dollar_dollar = msg
            _t1573 = self.deconstruct_bindings(_dollar_dollar)
            fields901 = (_t1573, _dollar_dollar.value,)
            assert fields901 is not None
            unwrapped_fields902 = fields901
            self.write("(")
            self.indent()
            field903 = unwrapped_fields902[0]
            self.pretty_bindings(field903)
            self.newline()
            field904 = unwrapped_fields902[1]
            self.pretty_formula(field904)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat913 = self._try_flat(msg, self.pretty_bindings)
        if flat913 is not None:
            assert flat913 is not None
            self.write(flat913)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1574 = _dollar_dollar[1]
            else:
                _t1574 = None
            fields906 = (_dollar_dollar[0], _t1574,)
            assert fields906 is not None
            unwrapped_fields907 = fields906
            self.write("[")
            self.indent()
            field908 = unwrapped_fields907[0]
            for i910, elem909 in enumerate(field908):
                if (i910 > 0):
                    self.newline()
                self.pretty_binding(elem909)
            field911 = unwrapped_fields907[1]
            if field911 is not None:
                self.newline()
                assert field911 is not None
                opt_val912 = field911
                self.pretty_value_bindings(opt_val912)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat918 = self._try_flat(msg, self.pretty_binding)
        if flat918 is not None:
            assert flat918 is not None
            self.write(flat918)
            return None
        else:
            _dollar_dollar = msg
            fields914 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields914 is not None
            unwrapped_fields915 = fields914
            field916 = unwrapped_fields915[0]
            self.write(field916)
            self.write("::")
            field917 = unwrapped_fields915[1]
            self.pretty_type(field917)

    def pretty_type(self, msg: logic_pb2.Type):
        flat947 = self._try_flat(msg, self.pretty_type)
        if flat947 is not None:
            assert flat947 is not None
            self.write(flat947)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1575 = _dollar_dollar.unspecified_type
            else:
                _t1575 = None
            deconstruct_result945 = _t1575
            if deconstruct_result945 is not None:
                assert deconstruct_result945 is not None
                unwrapped946 = deconstruct_result945
                self.pretty_unspecified_type(unwrapped946)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1576 = _dollar_dollar.string_type
                else:
                    _t1576 = None
                deconstruct_result943 = _t1576
                if deconstruct_result943 is not None:
                    assert deconstruct_result943 is not None
                    unwrapped944 = deconstruct_result943
                    self.pretty_string_type(unwrapped944)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1577 = _dollar_dollar.int_type
                    else:
                        _t1577 = None
                    deconstruct_result941 = _t1577
                    if deconstruct_result941 is not None:
                        assert deconstruct_result941 is not None
                        unwrapped942 = deconstruct_result941
                        self.pretty_int_type(unwrapped942)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1578 = _dollar_dollar.float_type
                        else:
                            _t1578 = None
                        deconstruct_result939 = _t1578
                        if deconstruct_result939 is not None:
                            assert deconstruct_result939 is not None
                            unwrapped940 = deconstruct_result939
                            self.pretty_float_type(unwrapped940)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1579 = _dollar_dollar.uint128_type
                            else:
                                _t1579 = None
                            deconstruct_result937 = _t1579
                            if deconstruct_result937 is not None:
                                assert deconstruct_result937 is not None
                                unwrapped938 = deconstruct_result937
                                self.pretty_uint128_type(unwrapped938)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1580 = _dollar_dollar.int128_type
                                else:
                                    _t1580 = None
                                deconstruct_result935 = _t1580
                                if deconstruct_result935 is not None:
                                    assert deconstruct_result935 is not None
                                    unwrapped936 = deconstruct_result935
                                    self.pretty_int128_type(unwrapped936)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1581 = _dollar_dollar.date_type
                                    else:
                                        _t1581 = None
                                    deconstruct_result933 = _t1581
                                    if deconstruct_result933 is not None:
                                        assert deconstruct_result933 is not None
                                        unwrapped934 = deconstruct_result933
                                        self.pretty_date_type(unwrapped934)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1582 = _dollar_dollar.datetime_type
                                        else:
                                            _t1582 = None
                                        deconstruct_result931 = _t1582
                                        if deconstruct_result931 is not None:
                                            assert deconstruct_result931 is not None
                                            unwrapped932 = deconstruct_result931
                                            self.pretty_datetime_type(unwrapped932)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1583 = _dollar_dollar.missing_type
                                            else:
                                                _t1583 = None
                                            deconstruct_result929 = _t1583
                                            if deconstruct_result929 is not None:
                                                assert deconstruct_result929 is not None
                                                unwrapped930 = deconstruct_result929
                                                self.pretty_missing_type(unwrapped930)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1584 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1584 = None
                                                deconstruct_result927 = _t1584
                                                if deconstruct_result927 is not None:
                                                    assert deconstruct_result927 is not None
                                                    unwrapped928 = deconstruct_result927
                                                    self.pretty_decimal_type(unwrapped928)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1585 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1585 = None
                                                    deconstruct_result925 = _t1585
                                                    if deconstruct_result925 is not None:
                                                        assert deconstruct_result925 is not None
                                                        unwrapped926 = deconstruct_result925
                                                        self.pretty_boolean_type(unwrapped926)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1586 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1586 = None
                                                        deconstruct_result923 = _t1586
                                                        if deconstruct_result923 is not None:
                                                            assert deconstruct_result923 is not None
                                                            unwrapped924 = deconstruct_result923
                                                            self.pretty_int32_type(unwrapped924)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1587 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1587 = None
                                                            deconstruct_result921 = _t1587
                                                            if deconstruct_result921 is not None:
                                                                assert deconstruct_result921 is not None
                                                                unwrapped922 = deconstruct_result921
                                                                self.pretty_float32_type(unwrapped922)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1588 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1588 = None
                                                                deconstruct_result919 = _t1588
                                                                if deconstruct_result919 is not None:
                                                                    assert deconstruct_result919 is not None
                                                                    unwrapped920 = deconstruct_result919
                                                                    self.pretty_uint32_type(unwrapped920)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields948 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields949 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields950 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields951 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields952 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields953 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields954 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields955 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields956 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat961 = self._try_flat(msg, self.pretty_decimal_type)
        if flat961 is not None:
            assert flat961 is not None
            self.write(flat961)
            return None
        else:
            _dollar_dollar = msg
            fields957 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields957 is not None
            unwrapped_fields958 = fields957
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field959 = unwrapped_fields958[0]
            self.write(str(field959))
            self.newline()
            field960 = unwrapped_fields958[1]
            self.write(str(field960))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields962 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields963 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields964 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields965 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat969 = self._try_flat(msg, self.pretty_value_bindings)
        if flat969 is not None:
            assert flat969 is not None
            self.write(flat969)
            return None
        else:
            fields966 = msg
            self.write("|")
            if not len(fields966) == 0:
                self.write(" ")
                for i968, elem967 in enumerate(fields966):
                    if (i968 > 0):
                        self.newline()
                    self.pretty_binding(elem967)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat996 = self._try_flat(msg, self.pretty_formula)
        if flat996 is not None:
            assert flat996 is not None
            self.write(flat996)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1589 = _dollar_dollar.conjunction
            else:
                _t1589 = None
            deconstruct_result994 = _t1589
            if deconstruct_result994 is not None:
                assert deconstruct_result994 is not None
                unwrapped995 = deconstruct_result994
                self.pretty_true(unwrapped995)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1590 = _dollar_dollar.disjunction
                else:
                    _t1590 = None
                deconstruct_result992 = _t1590
                if deconstruct_result992 is not None:
                    assert deconstruct_result992 is not None
                    unwrapped993 = deconstruct_result992
                    self.pretty_false(unwrapped993)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1591 = _dollar_dollar.exists
                    else:
                        _t1591 = None
                    deconstruct_result990 = _t1591
                    if deconstruct_result990 is not None:
                        assert deconstruct_result990 is not None
                        unwrapped991 = deconstruct_result990
                        self.pretty_exists(unwrapped991)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1592 = _dollar_dollar.reduce
                        else:
                            _t1592 = None
                        deconstruct_result988 = _t1592
                        if deconstruct_result988 is not None:
                            assert deconstruct_result988 is not None
                            unwrapped989 = deconstruct_result988
                            self.pretty_reduce(unwrapped989)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1593 = _dollar_dollar.conjunction
                            else:
                                _t1593 = None
                            deconstruct_result986 = _t1593
                            if deconstruct_result986 is not None:
                                assert deconstruct_result986 is not None
                                unwrapped987 = deconstruct_result986
                                self.pretty_conjunction(unwrapped987)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1594 = _dollar_dollar.disjunction
                                else:
                                    _t1594 = None
                                deconstruct_result984 = _t1594
                                if deconstruct_result984 is not None:
                                    assert deconstruct_result984 is not None
                                    unwrapped985 = deconstruct_result984
                                    self.pretty_disjunction(unwrapped985)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1595 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1595 = None
                                    deconstruct_result982 = _t1595
                                    if deconstruct_result982 is not None:
                                        assert deconstruct_result982 is not None
                                        unwrapped983 = deconstruct_result982
                                        self.pretty_not(unwrapped983)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1596 = _dollar_dollar.ffi
                                        else:
                                            _t1596 = None
                                        deconstruct_result980 = _t1596
                                        if deconstruct_result980 is not None:
                                            assert deconstruct_result980 is not None
                                            unwrapped981 = deconstruct_result980
                                            self.pretty_ffi(unwrapped981)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1597 = _dollar_dollar.atom
                                            else:
                                                _t1597 = None
                                            deconstruct_result978 = _t1597
                                            if deconstruct_result978 is not None:
                                                assert deconstruct_result978 is not None
                                                unwrapped979 = deconstruct_result978
                                                self.pretty_atom(unwrapped979)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1598 = _dollar_dollar.pragma
                                                else:
                                                    _t1598 = None
                                                deconstruct_result976 = _t1598
                                                if deconstruct_result976 is not None:
                                                    assert deconstruct_result976 is not None
                                                    unwrapped977 = deconstruct_result976
                                                    self.pretty_pragma(unwrapped977)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1599 = _dollar_dollar.primitive
                                                    else:
                                                        _t1599 = None
                                                    deconstruct_result974 = _t1599
                                                    if deconstruct_result974 is not None:
                                                        assert deconstruct_result974 is not None
                                                        unwrapped975 = deconstruct_result974
                                                        self.pretty_primitive(unwrapped975)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1600 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1600 = None
                                                        deconstruct_result972 = _t1600
                                                        if deconstruct_result972 is not None:
                                                            assert deconstruct_result972 is not None
                                                            unwrapped973 = deconstruct_result972
                                                            self.pretty_rel_atom(unwrapped973)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1601 = _dollar_dollar.cast
                                                            else:
                                                                _t1601 = None
                                                            deconstruct_result970 = _t1601
                                                            if deconstruct_result970 is not None:
                                                                assert deconstruct_result970 is not None
                                                                unwrapped971 = deconstruct_result970
                                                                self.pretty_cast(unwrapped971)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields997 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields998 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1003 = self._try_flat(msg, self.pretty_exists)
        if flat1003 is not None:
            assert flat1003 is not None
            self.write(flat1003)
            return None
        else:
            _dollar_dollar = msg
            _t1602 = self.deconstruct_bindings(_dollar_dollar.body)
            fields999 = (_t1602, _dollar_dollar.body.value,)
            assert fields999 is not None
            unwrapped_fields1000 = fields999
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1001 = unwrapped_fields1000[0]
            self.pretty_bindings(field1001)
            self.newline()
            field1002 = unwrapped_fields1000[1]
            self.pretty_formula(field1002)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1009 = self._try_flat(msg, self.pretty_reduce)
        if flat1009 is not None:
            assert flat1009 is not None
            self.write(flat1009)
            return None
        else:
            _dollar_dollar = msg
            fields1004 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1004 is not None
            unwrapped_fields1005 = fields1004
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1006 = unwrapped_fields1005[0]
            self.pretty_abstraction(field1006)
            self.newline()
            field1007 = unwrapped_fields1005[1]
            self.pretty_abstraction(field1007)
            self.newline()
            field1008 = unwrapped_fields1005[2]
            self.pretty_terms(field1008)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1013 = self._try_flat(msg, self.pretty_terms)
        if flat1013 is not None:
            assert flat1013 is not None
            self.write(flat1013)
            return None
        else:
            fields1010 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1010) == 0:
                self.newline()
                for i1012, elem1011 in enumerate(fields1010):
                    if (i1012 > 0):
                        self.newline()
                    self.pretty_term(elem1011)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1018 = self._try_flat(msg, self.pretty_term)
        if flat1018 is not None:
            assert flat1018 is not None
            self.write(flat1018)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1603 = _dollar_dollar.var
            else:
                _t1603 = None
            deconstruct_result1016 = _t1603
            if deconstruct_result1016 is not None:
                assert deconstruct_result1016 is not None
                unwrapped1017 = deconstruct_result1016
                self.pretty_var(unwrapped1017)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1604 = _dollar_dollar.constant
                else:
                    _t1604 = None
                deconstruct_result1014 = _t1604
                if deconstruct_result1014 is not None:
                    assert deconstruct_result1014 is not None
                    unwrapped1015 = deconstruct_result1014
                    self.pretty_value(unwrapped1015)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1021 = self._try_flat(msg, self.pretty_var)
        if flat1021 is not None:
            assert flat1021 is not None
            self.write(flat1021)
            return None
        else:
            _dollar_dollar = msg
            fields1019 = _dollar_dollar.name
            assert fields1019 is not None
            unwrapped_fields1020 = fields1019
            self.write(unwrapped_fields1020)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1047 = self._try_flat(msg, self.pretty_value)
        if flat1047 is not None:
            assert flat1047 is not None
            self.write(flat1047)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1605 = _dollar_dollar.date_value
            else:
                _t1605 = None
            deconstruct_result1045 = _t1605
            if deconstruct_result1045 is not None:
                assert deconstruct_result1045 is not None
                unwrapped1046 = deconstruct_result1045
                self.pretty_date(unwrapped1046)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1606 = _dollar_dollar.datetime_value
                else:
                    _t1606 = None
                deconstruct_result1043 = _t1606
                if deconstruct_result1043 is not None:
                    assert deconstruct_result1043 is not None
                    unwrapped1044 = deconstruct_result1043
                    self.pretty_datetime(unwrapped1044)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1607 = _dollar_dollar.string_value
                    else:
                        _t1607 = None
                    deconstruct_result1041 = _t1607
                    if deconstruct_result1041 is not None:
                        assert deconstruct_result1041 is not None
                        unwrapped1042 = deconstruct_result1041
                        self.write(self.format_string_value(unwrapped1042))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1608 = _dollar_dollar.int32_value
                        else:
                            _t1608 = None
                        deconstruct_result1039 = _t1608
                        if deconstruct_result1039 is not None:
                            assert deconstruct_result1039 is not None
                            unwrapped1040 = deconstruct_result1039
                            self.write((str(unwrapped1040) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1609 = _dollar_dollar.int_value
                            else:
                                _t1609 = None
                            deconstruct_result1037 = _t1609
                            if deconstruct_result1037 is not None:
                                assert deconstruct_result1037 is not None
                                unwrapped1038 = deconstruct_result1037
                                self.write(str(unwrapped1038))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1610 = _dollar_dollar.float32_value
                                else:
                                    _t1610 = None
                                deconstruct_result1035 = _t1610
                                if deconstruct_result1035 is not None:
                                    assert deconstruct_result1035 is not None
                                    unwrapped1036 = deconstruct_result1035
                                    self.write(self.format_float32_literal(unwrapped1036))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1611 = _dollar_dollar.float_value
                                    else:
                                        _t1611 = None
                                    deconstruct_result1033 = _t1611
                                    if deconstruct_result1033 is not None:
                                        assert deconstruct_result1033 is not None
                                        unwrapped1034 = deconstruct_result1033
                                        self.write(str(unwrapped1034))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1612 = _dollar_dollar.uint32_value
                                        else:
                                            _t1612 = None
                                        deconstruct_result1031 = _t1612
                                        if deconstruct_result1031 is not None:
                                            assert deconstruct_result1031 is not None
                                            unwrapped1032 = deconstruct_result1031
                                            self.write((str(unwrapped1032) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1613 = _dollar_dollar.uint128_value
                                            else:
                                                _t1613 = None
                                            deconstruct_result1029 = _t1613
                                            if deconstruct_result1029 is not None:
                                                assert deconstruct_result1029 is not None
                                                unwrapped1030 = deconstruct_result1029
                                                self.write(self.format_uint128(unwrapped1030))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1614 = _dollar_dollar.int128_value
                                                else:
                                                    _t1614 = None
                                                deconstruct_result1027 = _t1614
                                                if deconstruct_result1027 is not None:
                                                    assert deconstruct_result1027 is not None
                                                    unwrapped1028 = deconstruct_result1027
                                                    self.write(self.format_int128(unwrapped1028))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1615 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1615 = None
                                                    deconstruct_result1025 = _t1615
                                                    if deconstruct_result1025 is not None:
                                                        assert deconstruct_result1025 is not None
                                                        unwrapped1026 = deconstruct_result1025
                                                        self.write(self.format_decimal(unwrapped1026))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1616 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1616 = None
                                                        deconstruct_result1023 = _t1616
                                                        if deconstruct_result1023 is not None:
                                                            assert deconstruct_result1023 is not None
                                                            unwrapped1024 = deconstruct_result1023
                                                            self.pretty_boolean_value(unwrapped1024)
                                                        else:
                                                            fields1022 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1053 = self._try_flat(msg, self.pretty_date)
        if flat1053 is not None:
            assert flat1053 is not None
            self.write(flat1053)
            return None
        else:
            _dollar_dollar = msg
            fields1048 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1048 is not None
            unwrapped_fields1049 = fields1048
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1050 = unwrapped_fields1049[0]
            self.write(str(field1050))
            self.newline()
            field1051 = unwrapped_fields1049[1]
            self.write(str(field1051))
            self.newline()
            field1052 = unwrapped_fields1049[2]
            self.write(str(field1052))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1064 = self._try_flat(msg, self.pretty_datetime)
        if flat1064 is not None:
            assert flat1064 is not None
            self.write(flat1064)
            return None
        else:
            _dollar_dollar = msg
            fields1054 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1054 is not None
            unwrapped_fields1055 = fields1054
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1056 = unwrapped_fields1055[0]
            self.write(str(field1056))
            self.newline()
            field1057 = unwrapped_fields1055[1]
            self.write(str(field1057))
            self.newline()
            field1058 = unwrapped_fields1055[2]
            self.write(str(field1058))
            self.newline()
            field1059 = unwrapped_fields1055[3]
            self.write(str(field1059))
            self.newline()
            field1060 = unwrapped_fields1055[4]
            self.write(str(field1060))
            self.newline()
            field1061 = unwrapped_fields1055[5]
            self.write(str(field1061))
            field1062 = unwrapped_fields1055[6]
            if field1062 is not None:
                self.newline()
                assert field1062 is not None
                opt_val1063 = field1062
                self.write(str(opt_val1063))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1069 = self._try_flat(msg, self.pretty_conjunction)
        if flat1069 is not None:
            assert flat1069 is not None
            self.write(flat1069)
            return None
        else:
            _dollar_dollar = msg
            fields1065 = _dollar_dollar.args
            assert fields1065 is not None
            unwrapped_fields1066 = fields1065
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1066) == 0:
                self.newline()
                for i1068, elem1067 in enumerate(unwrapped_fields1066):
                    if (i1068 > 0):
                        self.newline()
                    self.pretty_formula(elem1067)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1074 = self._try_flat(msg, self.pretty_disjunction)
        if flat1074 is not None:
            assert flat1074 is not None
            self.write(flat1074)
            return None
        else:
            _dollar_dollar = msg
            fields1070 = _dollar_dollar.args
            assert fields1070 is not None
            unwrapped_fields1071 = fields1070
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1071) == 0:
                self.newline()
                for i1073, elem1072 in enumerate(unwrapped_fields1071):
                    if (i1073 > 0):
                        self.newline()
                    self.pretty_formula(elem1072)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1077 = self._try_flat(msg, self.pretty_not)
        if flat1077 is not None:
            assert flat1077 is not None
            self.write(flat1077)
            return None
        else:
            _dollar_dollar = msg
            fields1075 = _dollar_dollar.arg
            assert fields1075 is not None
            unwrapped_fields1076 = fields1075
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1076)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1083 = self._try_flat(msg, self.pretty_ffi)
        if flat1083 is not None:
            assert flat1083 is not None
            self.write(flat1083)
            return None
        else:
            _dollar_dollar = msg
            fields1078 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1078 is not None
            unwrapped_fields1079 = fields1078
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1080 = unwrapped_fields1079[0]
            self.pretty_name(field1080)
            self.newline()
            field1081 = unwrapped_fields1079[1]
            self.pretty_ffi_args(field1081)
            self.newline()
            field1082 = unwrapped_fields1079[2]
            self.pretty_terms(field1082)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1085 = self._try_flat(msg, self.pretty_name)
        if flat1085 is not None:
            assert flat1085 is not None
            self.write(flat1085)
            return None
        else:
            fields1084 = msg
            self.write(":")
            self.write(fields1084)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1089 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1089 is not None:
            assert flat1089 is not None
            self.write(flat1089)
            return None
        else:
            fields1086 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1086) == 0:
                self.newline()
                for i1088, elem1087 in enumerate(fields1086):
                    if (i1088 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1087)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1096 = self._try_flat(msg, self.pretty_atom)
        if flat1096 is not None:
            assert flat1096 is not None
            self.write(flat1096)
            return None
        else:
            _dollar_dollar = msg
            fields1090 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1090 is not None
            unwrapped_fields1091 = fields1090
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1092 = unwrapped_fields1091[0]
            self.pretty_relation_id(field1092)
            field1093 = unwrapped_fields1091[1]
            if not len(field1093) == 0:
                self.newline()
                for i1095, elem1094 in enumerate(field1093):
                    if (i1095 > 0):
                        self.newline()
                    self.pretty_term(elem1094)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1103 = self._try_flat(msg, self.pretty_pragma)
        if flat1103 is not None:
            assert flat1103 is not None
            self.write(flat1103)
            return None
        else:
            _dollar_dollar = msg
            fields1097 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1097 is not None
            unwrapped_fields1098 = fields1097
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1099 = unwrapped_fields1098[0]
            self.pretty_name(field1099)
            field1100 = unwrapped_fields1098[1]
            if not len(field1100) == 0:
                self.newline()
                for i1102, elem1101 in enumerate(field1100):
                    if (i1102 > 0):
                        self.newline()
                    self.pretty_term(elem1101)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1119 = self._try_flat(msg, self.pretty_primitive)
        if flat1119 is not None:
            assert flat1119 is not None
            self.write(flat1119)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1617 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1617 = None
            guard_result1118 = _t1617
            if guard_result1118 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1618 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1618 = None
                guard_result1117 = _t1618
                if guard_result1117 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1619 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1619 = None
                    guard_result1116 = _t1619
                    if guard_result1116 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1620 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1620 = None
                        guard_result1115 = _t1620
                        if guard_result1115 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1621 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1621 = None
                            guard_result1114 = _t1621
                            if guard_result1114 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1622 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1622 = None
                                guard_result1113 = _t1622
                                if guard_result1113 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1623 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1623 = None
                                    guard_result1112 = _t1623
                                    if guard_result1112 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1624 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1624 = None
                                        guard_result1111 = _t1624
                                        if guard_result1111 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1625 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1625 = None
                                            guard_result1110 = _t1625
                                            if guard_result1110 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1104 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1104 is not None
                                                unwrapped_fields1105 = fields1104
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1106 = unwrapped_fields1105[0]
                                                self.pretty_name(field1106)
                                                field1107 = unwrapped_fields1105[1]
                                                if not len(field1107) == 0:
                                                    self.newline()
                                                    for i1109, elem1108 in enumerate(field1107):
                                                        if (i1109 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1108)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1124 = self._try_flat(msg, self.pretty_eq)
        if flat1124 is not None:
            assert flat1124 is not None
            self.write(flat1124)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1626 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1626 = None
            fields1120 = _t1626
            assert fields1120 is not None
            unwrapped_fields1121 = fields1120
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1122 = unwrapped_fields1121[0]
            self.pretty_term(field1122)
            self.newline()
            field1123 = unwrapped_fields1121[1]
            self.pretty_term(field1123)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1129 = self._try_flat(msg, self.pretty_lt)
        if flat1129 is not None:
            assert flat1129 is not None
            self.write(flat1129)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1627 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1627 = None
            fields1125 = _t1627
            assert fields1125 is not None
            unwrapped_fields1126 = fields1125
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1127 = unwrapped_fields1126[0]
            self.pretty_term(field1127)
            self.newline()
            field1128 = unwrapped_fields1126[1]
            self.pretty_term(field1128)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1134 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1134 is not None:
            assert flat1134 is not None
            self.write(flat1134)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1628 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1628 = None
            fields1130 = _t1628
            assert fields1130 is not None
            unwrapped_fields1131 = fields1130
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1132 = unwrapped_fields1131[0]
            self.pretty_term(field1132)
            self.newline()
            field1133 = unwrapped_fields1131[1]
            self.pretty_term(field1133)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1139 = self._try_flat(msg, self.pretty_gt)
        if flat1139 is not None:
            assert flat1139 is not None
            self.write(flat1139)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1629 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1629 = None
            fields1135 = _t1629
            assert fields1135 is not None
            unwrapped_fields1136 = fields1135
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1137 = unwrapped_fields1136[0]
            self.pretty_term(field1137)
            self.newline()
            field1138 = unwrapped_fields1136[1]
            self.pretty_term(field1138)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1144 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1144 is not None:
            assert flat1144 is not None
            self.write(flat1144)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1630 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1630 = None
            fields1140 = _t1630
            assert fields1140 is not None
            unwrapped_fields1141 = fields1140
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1142 = unwrapped_fields1141[0]
            self.pretty_term(field1142)
            self.newline()
            field1143 = unwrapped_fields1141[1]
            self.pretty_term(field1143)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1150 = self._try_flat(msg, self.pretty_add)
        if flat1150 is not None:
            assert flat1150 is not None
            self.write(flat1150)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1631 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1631 = None
            fields1145 = _t1631
            assert fields1145 is not None
            unwrapped_fields1146 = fields1145
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1147 = unwrapped_fields1146[0]
            self.pretty_term(field1147)
            self.newline()
            field1148 = unwrapped_fields1146[1]
            self.pretty_term(field1148)
            self.newline()
            field1149 = unwrapped_fields1146[2]
            self.pretty_term(field1149)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1156 = self._try_flat(msg, self.pretty_minus)
        if flat1156 is not None:
            assert flat1156 is not None
            self.write(flat1156)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1632 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1632 = None
            fields1151 = _t1632
            assert fields1151 is not None
            unwrapped_fields1152 = fields1151
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1153 = unwrapped_fields1152[0]
            self.pretty_term(field1153)
            self.newline()
            field1154 = unwrapped_fields1152[1]
            self.pretty_term(field1154)
            self.newline()
            field1155 = unwrapped_fields1152[2]
            self.pretty_term(field1155)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1162 = self._try_flat(msg, self.pretty_multiply)
        if flat1162 is not None:
            assert flat1162 is not None
            self.write(flat1162)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1633 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1633 = None
            fields1157 = _t1633
            assert fields1157 is not None
            unwrapped_fields1158 = fields1157
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1159 = unwrapped_fields1158[0]
            self.pretty_term(field1159)
            self.newline()
            field1160 = unwrapped_fields1158[1]
            self.pretty_term(field1160)
            self.newline()
            field1161 = unwrapped_fields1158[2]
            self.pretty_term(field1161)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1168 = self._try_flat(msg, self.pretty_divide)
        if flat1168 is not None:
            assert flat1168 is not None
            self.write(flat1168)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1634 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1634 = None
            fields1163 = _t1634
            assert fields1163 is not None
            unwrapped_fields1164 = fields1163
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1165 = unwrapped_fields1164[0]
            self.pretty_term(field1165)
            self.newline()
            field1166 = unwrapped_fields1164[1]
            self.pretty_term(field1166)
            self.newline()
            field1167 = unwrapped_fields1164[2]
            self.pretty_term(field1167)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1173 = self._try_flat(msg, self.pretty_rel_term)
        if flat1173 is not None:
            assert flat1173 is not None
            self.write(flat1173)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1635 = _dollar_dollar.specialized_value
            else:
                _t1635 = None
            deconstruct_result1171 = _t1635
            if deconstruct_result1171 is not None:
                assert deconstruct_result1171 is not None
                unwrapped1172 = deconstruct_result1171
                self.pretty_specialized_value(unwrapped1172)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1636 = _dollar_dollar.term
                else:
                    _t1636 = None
                deconstruct_result1169 = _t1636
                if deconstruct_result1169 is not None:
                    assert deconstruct_result1169 is not None
                    unwrapped1170 = deconstruct_result1169
                    self.pretty_term(unwrapped1170)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1175 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1175 is not None:
            assert flat1175 is not None
            self.write(flat1175)
            return None
        else:
            fields1174 = msg
            self.write("#")
            self.pretty_raw_value(fields1174)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1182 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1182 is not None:
            assert flat1182 is not None
            self.write(flat1182)
            return None
        else:
            _dollar_dollar = msg
            fields1176 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1176 is not None
            unwrapped_fields1177 = fields1176
            self.write("(relatom")
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
                    self.pretty_rel_term(elem1180)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1187 = self._try_flat(msg, self.pretty_cast)
        if flat1187 is not None:
            assert flat1187 is not None
            self.write(flat1187)
            return None
        else:
            _dollar_dollar = msg
            fields1183 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1183 is not None
            unwrapped_fields1184 = fields1183
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1185 = unwrapped_fields1184[0]
            self.pretty_term(field1185)
            self.newline()
            field1186 = unwrapped_fields1184[1]
            self.pretty_term(field1186)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1191 = self._try_flat(msg, self.pretty_attrs)
        if flat1191 is not None:
            assert flat1191 is not None
            self.write(flat1191)
            return None
        else:
            fields1188 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1188) == 0:
                self.newline()
                for i1190, elem1189 in enumerate(fields1188):
                    if (i1190 > 0):
                        self.newline()
                    self.pretty_attribute(elem1189)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1198 = self._try_flat(msg, self.pretty_attribute)
        if flat1198 is not None:
            assert flat1198 is not None
            self.write(flat1198)
            return None
        else:
            _dollar_dollar = msg
            fields1192 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1192 is not None
            unwrapped_fields1193 = fields1192
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1194 = unwrapped_fields1193[0]
            self.pretty_name(field1194)
            field1195 = unwrapped_fields1193[1]
            if not len(field1195) == 0:
                self.newline()
                for i1197, elem1196 in enumerate(field1195):
                    if (i1197 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1196)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1205 = self._try_flat(msg, self.pretty_algorithm)
        if flat1205 is not None:
            assert flat1205 is not None
            self.write(flat1205)
            return None
        else:
            _dollar_dollar = msg
            fields1199 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            assert fields1199 is not None
            unwrapped_fields1200 = fields1199
            self.write("(algorithm")
            self.indent_sexp()
            field1201 = unwrapped_fields1200[0]
            if not len(field1201) == 0:
                self.newline()
                for i1203, elem1202 in enumerate(field1201):
                    if (i1203 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1202)
            self.newline()
            field1204 = unwrapped_fields1200[1]
            self.pretty_script(field1204)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1210 = self._try_flat(msg, self.pretty_script)
        if flat1210 is not None:
            assert flat1210 is not None
            self.write(flat1210)
            return None
        else:
            _dollar_dollar = msg
            fields1206 = _dollar_dollar.constructs
            assert fields1206 is not None
            unwrapped_fields1207 = fields1206
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1207) == 0:
                self.newline()
                for i1209, elem1208 in enumerate(unwrapped_fields1207):
                    if (i1209 > 0):
                        self.newline()
                    self.pretty_construct(elem1208)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1215 = self._try_flat(msg, self.pretty_construct)
        if flat1215 is not None:
            assert flat1215 is not None
            self.write(flat1215)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1637 = _dollar_dollar.loop
            else:
                _t1637 = None
            deconstruct_result1213 = _t1637
            if deconstruct_result1213 is not None:
                assert deconstruct_result1213 is not None
                unwrapped1214 = deconstruct_result1213
                self.pretty_loop(unwrapped1214)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1638 = _dollar_dollar.instruction
                else:
                    _t1638 = None
                deconstruct_result1211 = _t1638
                if deconstruct_result1211 is not None:
                    assert deconstruct_result1211 is not None
                    unwrapped1212 = deconstruct_result1211
                    self.pretty_instruction(unwrapped1212)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1220 = self._try_flat(msg, self.pretty_loop)
        if flat1220 is not None:
            assert flat1220 is not None
            self.write(flat1220)
            return None
        else:
            _dollar_dollar = msg
            fields1216 = (_dollar_dollar.init, _dollar_dollar.body,)
            assert fields1216 is not None
            unwrapped_fields1217 = fields1216
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1218 = unwrapped_fields1217[0]
            self.pretty_init(field1218)
            self.newline()
            field1219 = unwrapped_fields1217[1]
            self.pretty_script(field1219)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1224 = self._try_flat(msg, self.pretty_init)
        if flat1224 is not None:
            assert flat1224 is not None
            self.write(flat1224)
            return None
        else:
            fields1221 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1221) == 0:
                self.newline()
                for i1223, elem1222 in enumerate(fields1221):
                    if (i1223 > 0):
                        self.newline()
                    self.pretty_instruction(elem1222)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1235 = self._try_flat(msg, self.pretty_instruction)
        if flat1235 is not None:
            assert flat1235 is not None
            self.write(flat1235)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1639 = _dollar_dollar.assign
            else:
                _t1639 = None
            deconstruct_result1233 = _t1639
            if deconstruct_result1233 is not None:
                assert deconstruct_result1233 is not None
                unwrapped1234 = deconstruct_result1233
                self.pretty_assign(unwrapped1234)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1640 = _dollar_dollar.upsert
                else:
                    _t1640 = None
                deconstruct_result1231 = _t1640
                if deconstruct_result1231 is not None:
                    assert deconstruct_result1231 is not None
                    unwrapped1232 = deconstruct_result1231
                    self.pretty_upsert(unwrapped1232)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1641 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1641 = None
                    deconstruct_result1229 = _t1641
                    if deconstruct_result1229 is not None:
                        assert deconstruct_result1229 is not None
                        unwrapped1230 = deconstruct_result1229
                        self.pretty_break(unwrapped1230)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1642 = _dollar_dollar.monoid_def
                        else:
                            _t1642 = None
                        deconstruct_result1227 = _t1642
                        if deconstruct_result1227 is not None:
                            assert deconstruct_result1227 is not None
                            unwrapped1228 = deconstruct_result1227
                            self.pretty_monoid_def(unwrapped1228)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1643 = _dollar_dollar.monus_def
                            else:
                                _t1643 = None
                            deconstruct_result1225 = _t1643
                            if deconstruct_result1225 is not None:
                                assert deconstruct_result1225 is not None
                                unwrapped1226 = deconstruct_result1225
                                self.pretty_monus_def(unwrapped1226)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1242 = self._try_flat(msg, self.pretty_assign)
        if flat1242 is not None:
            assert flat1242 is not None
            self.write(flat1242)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1644 = _dollar_dollar.attrs
            else:
                _t1644 = None
            fields1236 = (_dollar_dollar.name, _dollar_dollar.body, _t1644,)
            assert fields1236 is not None
            unwrapped_fields1237 = fields1236
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1238 = unwrapped_fields1237[0]
            self.pretty_relation_id(field1238)
            self.newline()
            field1239 = unwrapped_fields1237[1]
            self.pretty_abstraction(field1239)
            field1240 = unwrapped_fields1237[2]
            if field1240 is not None:
                self.newline()
                assert field1240 is not None
                opt_val1241 = field1240
                self.pretty_attrs(opt_val1241)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1249 = self._try_flat(msg, self.pretty_upsert)
        if flat1249 is not None:
            assert flat1249 is not None
            self.write(flat1249)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1645 = _dollar_dollar.attrs
            else:
                _t1645 = None
            fields1243 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1645,)
            assert fields1243 is not None
            unwrapped_fields1244 = fields1243
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1245 = unwrapped_fields1244[0]
            self.pretty_relation_id(field1245)
            self.newline()
            field1246 = unwrapped_fields1244[1]
            self.pretty_abstraction_with_arity(field1246)
            field1247 = unwrapped_fields1244[2]
            if field1247 is not None:
                self.newline()
                assert field1247 is not None
                opt_val1248 = field1247
                self.pretty_attrs(opt_val1248)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1254 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1254 is not None:
            assert flat1254 is not None
            self.write(flat1254)
            return None
        else:
            _dollar_dollar = msg
            _t1646 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1250 = (_t1646, _dollar_dollar[0].value,)
            assert fields1250 is not None
            unwrapped_fields1251 = fields1250
            self.write("(")
            self.indent()
            field1252 = unwrapped_fields1251[0]
            self.pretty_bindings(field1252)
            self.newline()
            field1253 = unwrapped_fields1251[1]
            self.pretty_formula(field1253)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1261 = self._try_flat(msg, self.pretty_break)
        if flat1261 is not None:
            assert flat1261 is not None
            self.write(flat1261)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1647 = _dollar_dollar.attrs
            else:
                _t1647 = None
            fields1255 = (_dollar_dollar.name, _dollar_dollar.body, _t1647,)
            assert fields1255 is not None
            unwrapped_fields1256 = fields1255
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1257 = unwrapped_fields1256[0]
            self.pretty_relation_id(field1257)
            self.newline()
            field1258 = unwrapped_fields1256[1]
            self.pretty_abstraction(field1258)
            field1259 = unwrapped_fields1256[2]
            if field1259 is not None:
                self.newline()
                assert field1259 is not None
                opt_val1260 = field1259
                self.pretty_attrs(opt_val1260)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1269 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1269 is not None:
            assert flat1269 is not None
            self.write(flat1269)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1648 = _dollar_dollar.attrs
            else:
                _t1648 = None
            fields1262 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1648,)
            assert fields1262 is not None
            unwrapped_fields1263 = fields1262
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1264 = unwrapped_fields1263[0]
            self.pretty_monoid(field1264)
            self.newline()
            field1265 = unwrapped_fields1263[1]
            self.pretty_relation_id(field1265)
            self.newline()
            field1266 = unwrapped_fields1263[2]
            self.pretty_abstraction_with_arity(field1266)
            field1267 = unwrapped_fields1263[3]
            if field1267 is not None:
                self.newline()
                assert field1267 is not None
                opt_val1268 = field1267
                self.pretty_attrs(opt_val1268)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1278 = self._try_flat(msg, self.pretty_monoid)
        if flat1278 is not None:
            assert flat1278 is not None
            self.write(flat1278)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1649 = _dollar_dollar.or_monoid
            else:
                _t1649 = None
            deconstruct_result1276 = _t1649
            if deconstruct_result1276 is not None:
                assert deconstruct_result1276 is not None
                unwrapped1277 = deconstruct_result1276
                self.pretty_or_monoid(unwrapped1277)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1650 = _dollar_dollar.min_monoid
                else:
                    _t1650 = None
                deconstruct_result1274 = _t1650
                if deconstruct_result1274 is not None:
                    assert deconstruct_result1274 is not None
                    unwrapped1275 = deconstruct_result1274
                    self.pretty_min_monoid(unwrapped1275)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1651 = _dollar_dollar.max_monoid
                    else:
                        _t1651 = None
                    deconstruct_result1272 = _t1651
                    if deconstruct_result1272 is not None:
                        assert deconstruct_result1272 is not None
                        unwrapped1273 = deconstruct_result1272
                        self.pretty_max_monoid(unwrapped1273)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1652 = _dollar_dollar.sum_monoid
                        else:
                            _t1652 = None
                        deconstruct_result1270 = _t1652
                        if deconstruct_result1270 is not None:
                            assert deconstruct_result1270 is not None
                            unwrapped1271 = deconstruct_result1270
                            self.pretty_sum_monoid(unwrapped1271)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1279 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1282 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1282 is not None:
            assert flat1282 is not None
            self.write(flat1282)
            return None
        else:
            _dollar_dollar = msg
            fields1280 = _dollar_dollar.type
            assert fields1280 is not None
            unwrapped_fields1281 = fields1280
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1281)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1285 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1285 is not None:
            assert flat1285 is not None
            self.write(flat1285)
            return None
        else:
            _dollar_dollar = msg
            fields1283 = _dollar_dollar.type
            assert fields1283 is not None
            unwrapped_fields1284 = fields1283
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1284)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1288 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1288 is not None:
            assert flat1288 is not None
            self.write(flat1288)
            return None
        else:
            _dollar_dollar = msg
            fields1286 = _dollar_dollar.type
            assert fields1286 is not None
            unwrapped_fields1287 = fields1286
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1287)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1296 = self._try_flat(msg, self.pretty_monus_def)
        if flat1296 is not None:
            assert flat1296 is not None
            self.write(flat1296)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1653 = _dollar_dollar.attrs
            else:
                _t1653 = None
            fields1289 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1653,)
            assert fields1289 is not None
            unwrapped_fields1290 = fields1289
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1291 = unwrapped_fields1290[0]
            self.pretty_monoid(field1291)
            self.newline()
            field1292 = unwrapped_fields1290[1]
            self.pretty_relation_id(field1292)
            self.newline()
            field1293 = unwrapped_fields1290[2]
            self.pretty_abstraction_with_arity(field1293)
            field1294 = unwrapped_fields1290[3]
            if field1294 is not None:
                self.newline()
                assert field1294 is not None
                opt_val1295 = field1294
                self.pretty_attrs(opt_val1295)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1303 = self._try_flat(msg, self.pretty_constraint)
        if flat1303 is not None:
            assert flat1303 is not None
            self.write(flat1303)
            return None
        else:
            _dollar_dollar = msg
            fields1297 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1297 is not None
            unwrapped_fields1298 = fields1297
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1299 = unwrapped_fields1298[0]
            self.pretty_relation_id(field1299)
            self.newline()
            field1300 = unwrapped_fields1298[1]
            self.pretty_abstraction(field1300)
            self.newline()
            field1301 = unwrapped_fields1298[2]
            self.pretty_functional_dependency_keys(field1301)
            self.newline()
            field1302 = unwrapped_fields1298[3]
            self.pretty_functional_dependency_values(field1302)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1307 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1307 is not None:
            assert flat1307 is not None
            self.write(flat1307)
            return None
        else:
            fields1304 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1304) == 0:
                self.newline()
                for i1306, elem1305 in enumerate(fields1304):
                    if (i1306 > 0):
                        self.newline()
                    self.pretty_var(elem1305)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1311 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1311 is not None:
            assert flat1311 is not None
            self.write(flat1311)
            return None
        else:
            fields1308 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1308) == 0:
                self.newline()
                for i1310, elem1309 in enumerate(fields1308):
                    if (i1310 > 0):
                        self.newline()
                    self.pretty_var(elem1309)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1320 = self._try_flat(msg, self.pretty_data)
        if flat1320 is not None:
            assert flat1320 is not None
            self.write(flat1320)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1654 = _dollar_dollar.edb
            else:
                _t1654 = None
            deconstruct_result1318 = _t1654
            if deconstruct_result1318 is not None:
                assert deconstruct_result1318 is not None
                unwrapped1319 = deconstruct_result1318
                self.pretty_edb(unwrapped1319)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1655 = _dollar_dollar.betree_relation
                else:
                    _t1655 = None
                deconstruct_result1316 = _t1655
                if deconstruct_result1316 is not None:
                    assert deconstruct_result1316 is not None
                    unwrapped1317 = deconstruct_result1316
                    self.pretty_betree_relation(unwrapped1317)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1656 = _dollar_dollar.csv_data
                    else:
                        _t1656 = None
                    deconstruct_result1314 = _t1656
                    if deconstruct_result1314 is not None:
                        assert deconstruct_result1314 is not None
                        unwrapped1315 = deconstruct_result1314
                        self.pretty_csv_data(unwrapped1315)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1657 = _dollar_dollar.iceberg_data
                        else:
                            _t1657 = None
                        deconstruct_result1312 = _t1657
                        if deconstruct_result1312 is not None:
                            assert deconstruct_result1312 is not None
                            unwrapped1313 = deconstruct_result1312
                            self.pretty_iceberg_data(unwrapped1313)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1326 = self._try_flat(msg, self.pretty_edb)
        if flat1326 is not None:
            assert flat1326 is not None
            self.write(flat1326)
            return None
        else:
            _dollar_dollar = msg
            fields1321 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1321 is not None
            unwrapped_fields1322 = fields1321
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1323 = unwrapped_fields1322[0]
            self.pretty_relation_id(field1323)
            self.newline()
            field1324 = unwrapped_fields1322[1]
            self.pretty_edb_path(field1324)
            self.newline()
            field1325 = unwrapped_fields1322[2]
            self.pretty_edb_types(field1325)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1330 = self._try_flat(msg, self.pretty_edb_path)
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
                self.write(self.format_string_value(elem1328))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1334 = self._try_flat(msg, self.pretty_edb_types)
        if flat1334 is not None:
            assert flat1334 is not None
            self.write(flat1334)
            return None
        else:
            fields1331 = msg
            self.write("[")
            self.indent()
            for i1333, elem1332 in enumerate(fields1331):
                if (i1333 > 0):
                    self.newline()
                self.pretty_type(elem1332)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1339 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1339 is not None:
            assert flat1339 is not None
            self.write(flat1339)
            return None
        else:
            _dollar_dollar = msg
            fields1335 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1335 is not None
            unwrapped_fields1336 = fields1335
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1337 = unwrapped_fields1336[0]
            self.pretty_relation_id(field1337)
            self.newline()
            field1338 = unwrapped_fields1336[1]
            self.pretty_betree_info(field1338)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1345 = self._try_flat(msg, self.pretty_betree_info)
        if flat1345 is not None:
            assert flat1345 is not None
            self.write(flat1345)
            return None
        else:
            _dollar_dollar = msg
            _t1658 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1340 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1658,)
            assert fields1340 is not None
            unwrapped_fields1341 = fields1340
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1342 = unwrapped_fields1341[0]
            self.pretty_betree_info_key_types(field1342)
            self.newline()
            field1343 = unwrapped_fields1341[1]
            self.pretty_betree_info_value_types(field1343)
            self.newline()
            field1344 = unwrapped_fields1341[2]
            self.pretty_config_dict(field1344)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1349 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1349 is not None:
            assert flat1349 is not None
            self.write(flat1349)
            return None
        else:
            fields1346 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1346) == 0:
                self.newline()
                for i1348, elem1347 in enumerate(fields1346):
                    if (i1348 > 0):
                        self.newline()
                    self.pretty_type(elem1347)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1353 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1353 is not None:
            assert flat1353 is not None
            self.write(flat1353)
            return None
        else:
            fields1350 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1350) == 0:
                self.newline()
                for i1352, elem1351 in enumerate(fields1350):
                    if (i1352 > 0):
                        self.newline()
                    self.pretty_type(elem1351)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1360 = self._try_flat(msg, self.pretty_csv_data)
        if flat1360 is not None:
            assert flat1360 is not None
            self.write(flat1360)
            return None
        else:
            _dollar_dollar = msg
            fields1354 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1354 is not None
            unwrapped_fields1355 = fields1354
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1356 = unwrapped_fields1355[0]
            self.pretty_csvlocator(field1356)
            self.newline()
            field1357 = unwrapped_fields1355[1]
            self.pretty_csv_config(field1357)
            self.newline()
            field1358 = unwrapped_fields1355[2]
            self.pretty_gnf_columns(field1358)
            self.newline()
            field1359 = unwrapped_fields1355[3]
            self.pretty_csv_asof(field1359)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1367 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1367 is not None:
            assert flat1367 is not None
            self.write(flat1367)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1659 = _dollar_dollar.paths
            else:
                _t1659 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1660 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1660 = None
            fields1361 = (_t1659, _t1660,)
            assert fields1361 is not None
            unwrapped_fields1362 = fields1361
            self.write("(csv_locator")
            self.indent_sexp()
            field1363 = unwrapped_fields1362[0]
            if field1363 is not None:
                self.newline()
                assert field1363 is not None
                opt_val1364 = field1363
                self.pretty_csv_locator_paths(opt_val1364)
            field1365 = unwrapped_fields1362[1]
            if field1365 is not None:
                self.newline()
                assert field1365 is not None
                opt_val1366 = field1365
                self.pretty_csv_locator_inline_data(opt_val1366)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1371 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1371 is not None:
            assert flat1371 is not None
            self.write(flat1371)
            return None
        else:
            fields1368 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1368) == 0:
                self.newline()
                for i1370, elem1369 in enumerate(fields1368):
                    if (i1370 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1369))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1373 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1373 is not None:
            assert flat1373 is not None
            self.write(flat1373)
            return None
        else:
            fields1372 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1372))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1376 = self._try_flat(msg, self.pretty_csv_config)
        if flat1376 is not None:
            assert flat1376 is not None
            self.write(flat1376)
            return None
        else:
            _dollar_dollar = msg
            _t1661 = self.deconstruct_csv_config(_dollar_dollar)
            fields1374 = _t1661
            assert fields1374 is not None
            unwrapped_fields1375 = fields1374
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1375)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1380 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1380 is not None:
            assert flat1380 is not None
            self.write(flat1380)
            return None
        else:
            fields1377 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1377) == 0:
                self.newline()
                for i1379, elem1378 in enumerate(fields1377):
                    if (i1379 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1378)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1389 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1389 is not None:
            assert flat1389 is not None
            self.write(flat1389)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1662 = _dollar_dollar.target_id
            else:
                _t1662 = None
            fields1381 = (_dollar_dollar.column_path, _t1662, _dollar_dollar.types,)
            assert fields1381 is not None
            unwrapped_fields1382 = fields1381
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1383 = unwrapped_fields1382[0]
            self.pretty_gnf_column_path(field1383)
            field1384 = unwrapped_fields1382[1]
            if field1384 is not None:
                self.newline()
                assert field1384 is not None
                opt_val1385 = field1384
                self.pretty_relation_id(opt_val1385)
            self.newline()
            self.write("[")
            field1386 = unwrapped_fields1382[2]
            for i1388, elem1387 in enumerate(field1386):
                if (i1388 > 0):
                    self.newline()
                self.pretty_type(elem1387)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1396 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1396 is not None:
            assert flat1396 is not None
            self.write(flat1396)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1663 = _dollar_dollar[0]
            else:
                _t1663 = None
            deconstruct_result1394 = _t1663
            if deconstruct_result1394 is not None:
                assert deconstruct_result1394 is not None
                unwrapped1395 = deconstruct_result1394
                self.write(self.format_string_value(unwrapped1395))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1664 = _dollar_dollar
                else:
                    _t1664 = None
                deconstruct_result1390 = _t1664
                if deconstruct_result1390 is not None:
                    assert deconstruct_result1390 is not None
                    unwrapped1391 = deconstruct_result1390
                    self.write("[")
                    self.indent()
                    for i1393, elem1392 in enumerate(unwrapped1391):
                        if (i1393 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1392))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1398 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1398 is not None:
            assert flat1398 is not None
            self.write(flat1398)
            return None
        else:
            fields1397 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1397))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1406 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1406 is not None:
            assert flat1406 is not None
            self.write(flat1406)
            return None
        else:
            _dollar_dollar = msg
            _t1665 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1399 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1665,)
            assert fields1399 is not None
            unwrapped_fields1400 = fields1399
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1401 = unwrapped_fields1400[0]
            self.pretty_iceberg_locator(field1401)
            self.newline()
            field1402 = unwrapped_fields1400[1]
            self.pretty_iceberg_config(field1402)
            self.newline()
            field1403 = unwrapped_fields1400[2]
            self.pretty_gnf_columns(field1403)
            field1404 = unwrapped_fields1400[3]
            if field1404 is not None:
                self.newline()
                assert field1404 is not None
                opt_val1405 = field1404
                self.pretty_iceberg_to_snapshot(opt_val1405)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1414 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1414 is not None:
            assert flat1414 is not None
            self.write(flat1414)
            return None
        else:
            _dollar_dollar = msg
            fields1407 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1407 is not None
            unwrapped_fields1408 = fields1407
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("table_name")
            self.newline()
            field1409 = unwrapped_fields1408[0]
            self.write(self.format_string_value(field1409))
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("namespace")
            field1410 = unwrapped_fields1408[1]
            if not len(field1410) == 0:
                self.newline()
                for i1412, elem1411 in enumerate(field1410):
                    if (i1412 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1411))
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("warehouse")
            self.newline()
            field1413 = unwrapped_fields1408[2]
            self.write(self.format_string_value(field1413))
            self.dedent()
            self.write(")")
            self.dedent()
            self.write(")")

    def pretty_iceberg_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1426 = self._try_flat(msg, self.pretty_iceberg_config)
        if flat1426 is not None:
            assert flat1426 is not None
            self.write(flat1426)
            return None
        else:
            _dollar_dollar = msg
            _t1666 = self.deconstruct_iceberg_config_scope_optional(_dollar_dollar)
            fields1415 = (_dollar_dollar.catalog_uri, _t1666, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1415 is not None
            unwrapped_fields1416 = fields1415
            self.write("(iceberg_config")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("catalog_uri")
            self.newline()
            field1417 = unwrapped_fields1416[0]
            self.write(self.format_string_value(field1417))
            self.dedent()
            self.write(")")
            field1418 = unwrapped_fields1416[1]
            if field1418 is not None:
                self.newline()
                assert field1418 is not None
                opt_val1419 = field1418
                self.pretty_iceberg_config_scope(opt_val1419)
            self.newline()
            self.write("(")
            self.newline()
            self.write("properties")
            field1420 = unwrapped_fields1416[2]
            if not len(field1420) == 0:
                self.newline()
                for i1422, elem1421 in enumerate(field1420):
                    if (i1422 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1421)
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("auth_properties")
            field1423 = unwrapped_fields1416[3]
            if not len(field1423) == 0:
                self.newline()
                for i1425, elem1424 in enumerate(field1423):
                    if (i1425 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1424)
            self.dedent()
            self.write(")")
            self.dedent()
            self.write(")")

    def pretty_iceberg_config_scope(self, msg: str):
        flat1428 = self._try_flat(msg, self.pretty_iceberg_config_scope)
        if flat1428 is not None:
            assert flat1428 is not None
            self.write(flat1428)
            return None
        else:
            fields1427 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1427))
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1433 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1433 is not None:
            assert flat1433 is not None
            self.write(flat1433)
            return None
        else:
            _dollar_dollar = msg
            fields1429 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1429 is not None
            unwrapped_fields1430 = fields1429
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1431 = unwrapped_fields1430[0]
            self.write(self.format_string_value(field1431))
            self.newline()
            field1432 = unwrapped_fields1430[1]
            self.write(self.format_string_value(field1432))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1435 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1435 is not None:
            assert flat1435 is not None
            self.write(flat1435)
            return None
        else:
            fields1434 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1434))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1438 = self._try_flat(msg, self.pretty_undefine)
        if flat1438 is not None:
            assert flat1438 is not None
            self.write(flat1438)
            return None
        else:
            _dollar_dollar = msg
            fields1436 = _dollar_dollar.fragment_id
            assert fields1436 is not None
            unwrapped_fields1437 = fields1436
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1437)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1443 = self._try_flat(msg, self.pretty_context)
        if flat1443 is not None:
            assert flat1443 is not None
            self.write(flat1443)
            return None
        else:
            _dollar_dollar = msg
            fields1439 = _dollar_dollar.relations
            assert fields1439 is not None
            unwrapped_fields1440 = fields1439
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1440) == 0:
                self.newline()
                for i1442, elem1441 in enumerate(unwrapped_fields1440):
                    if (i1442 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1441)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1448 = self._try_flat(msg, self.pretty_snapshot)
        if flat1448 is not None:
            assert flat1448 is not None
            self.write(flat1448)
            return None
        else:
            _dollar_dollar = msg
            fields1444 = _dollar_dollar.mappings
            assert fields1444 is not None
            unwrapped_fields1445 = fields1444
            self.write("(snapshot")
            self.indent_sexp()
            if not len(unwrapped_fields1445) == 0:
                self.newline()
                for i1447, elem1446 in enumerate(unwrapped_fields1445):
                    if (i1447 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1446)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1453 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1453 is not None:
            assert flat1453 is not None
            self.write(flat1453)
            return None
        else:
            _dollar_dollar = msg
            fields1449 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1449 is not None
            unwrapped_fields1450 = fields1449
            field1451 = unwrapped_fields1450[0]
            self.pretty_edb_path(field1451)
            self.write(" ")
            field1452 = unwrapped_fields1450[1]
            self.pretty_relation_id(field1452)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1457 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1457 is not None:
            assert flat1457 is not None
            self.write(flat1457)
            return None
        else:
            fields1454 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1454) == 0:
                self.newline()
                for i1456, elem1455 in enumerate(fields1454):
                    if (i1456 > 0):
                        self.newline()
                    self.pretty_read(elem1455)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1468 = self._try_flat(msg, self.pretty_read)
        if flat1468 is not None:
            assert flat1468 is not None
            self.write(flat1468)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1667 = _dollar_dollar.demand
            else:
                _t1667 = None
            deconstruct_result1466 = _t1667
            if deconstruct_result1466 is not None:
                assert deconstruct_result1466 is not None
                unwrapped1467 = deconstruct_result1466
                self.pretty_demand(unwrapped1467)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1668 = _dollar_dollar.output
                else:
                    _t1668 = None
                deconstruct_result1464 = _t1668
                if deconstruct_result1464 is not None:
                    assert deconstruct_result1464 is not None
                    unwrapped1465 = deconstruct_result1464
                    self.pretty_output(unwrapped1465)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1669 = _dollar_dollar.what_if
                    else:
                        _t1669 = None
                    deconstruct_result1462 = _t1669
                    if deconstruct_result1462 is not None:
                        assert deconstruct_result1462 is not None
                        unwrapped1463 = deconstruct_result1462
                        self.pretty_what_if(unwrapped1463)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1670 = _dollar_dollar.abort
                        else:
                            _t1670 = None
                        deconstruct_result1460 = _t1670
                        if deconstruct_result1460 is not None:
                            assert deconstruct_result1460 is not None
                            unwrapped1461 = deconstruct_result1460
                            self.pretty_abort(unwrapped1461)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1671 = _dollar_dollar.export
                            else:
                                _t1671 = None
                            deconstruct_result1458 = _t1671
                            if deconstruct_result1458 is not None:
                                assert deconstruct_result1458 is not None
                                unwrapped1459 = deconstruct_result1458
                                self.pretty_export(unwrapped1459)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1471 = self._try_flat(msg, self.pretty_demand)
        if flat1471 is not None:
            assert flat1471 is not None
            self.write(flat1471)
            return None
        else:
            _dollar_dollar = msg
            fields1469 = _dollar_dollar.relation_id
            assert fields1469 is not None
            unwrapped_fields1470 = fields1469
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1470)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1476 = self._try_flat(msg, self.pretty_output)
        if flat1476 is not None:
            assert flat1476 is not None
            self.write(flat1476)
            return None
        else:
            _dollar_dollar = msg
            fields1472 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1472 is not None
            unwrapped_fields1473 = fields1472
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1474 = unwrapped_fields1473[0]
            self.pretty_name(field1474)
            self.newline()
            field1475 = unwrapped_fields1473[1]
            self.pretty_relation_id(field1475)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1481 = self._try_flat(msg, self.pretty_what_if)
        if flat1481 is not None:
            assert flat1481 is not None
            self.write(flat1481)
            return None
        else:
            _dollar_dollar = msg
            fields1477 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1477 is not None
            unwrapped_fields1478 = fields1477
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1479 = unwrapped_fields1478[0]
            self.pretty_name(field1479)
            self.newline()
            field1480 = unwrapped_fields1478[1]
            self.pretty_epoch(field1480)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1487 = self._try_flat(msg, self.pretty_abort)
        if flat1487 is not None:
            assert flat1487 is not None
            self.write(flat1487)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1672 = _dollar_dollar.name
            else:
                _t1672 = None
            fields1482 = (_t1672, _dollar_dollar.relation_id,)
            assert fields1482 is not None
            unwrapped_fields1483 = fields1482
            self.write("(abort")
            self.indent_sexp()
            field1484 = unwrapped_fields1483[0]
            if field1484 is not None:
                self.newline()
                assert field1484 is not None
                opt_val1485 = field1484
                self.pretty_name(opt_val1485)
            self.newline()
            field1486 = unwrapped_fields1483[1]
            self.pretty_relation_id(field1486)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1492 = self._try_flat(msg, self.pretty_export)
        if flat1492 is not None:
            assert flat1492 is not None
            self.write(flat1492)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1673 = _dollar_dollar.csv_config
            else:
                _t1673 = None
            deconstruct_result1490 = _t1673
            if deconstruct_result1490 is not None:
                assert deconstruct_result1490 is not None
                unwrapped1491 = deconstruct_result1490
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1491)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1674 = _dollar_dollar.iceberg_config
                else:
                    _t1674 = None
                deconstruct_result1488 = _t1674
                if deconstruct_result1488 is not None:
                    assert deconstruct_result1488 is not None
                    unwrapped1489 = deconstruct_result1488
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1489)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1503 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1503 is not None:
            assert flat1503 is not None
            self.write(flat1503)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1675 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1675 = None
            deconstruct_result1498 = _t1675
            if deconstruct_result1498 is not None:
                assert deconstruct_result1498 is not None
                unwrapped1499 = deconstruct_result1498
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1500 = unwrapped1499[0]
                self.pretty_export_csv_path(field1500)
                self.newline()
                field1501 = unwrapped1499[1]
                self.pretty_export_csv_source(field1501)
                self.newline()
                field1502 = unwrapped1499[2]
                self.pretty_csv_config(field1502)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1677 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1676 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1677,)
                else:
                    _t1676 = None
                deconstruct_result1493 = _t1676
                if deconstruct_result1493 is not None:
                    assert deconstruct_result1493 is not None
                    unwrapped1494 = deconstruct_result1493
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1495 = unwrapped1494[0]
                    self.pretty_export_csv_path(field1495)
                    self.newline()
                    field1496 = unwrapped1494[1]
                    self.pretty_export_csv_columns_list(field1496)
                    self.newline()
                    field1497 = unwrapped1494[2]
                    self.pretty_config_dict(field1497)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1505 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1505 is not None:
            assert flat1505 is not None
            self.write(flat1505)
            return None
        else:
            fields1504 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1504))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1512 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1512 is not None:
            assert flat1512 is not None
            self.write(flat1512)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1678 = _dollar_dollar.gnf_columns.columns
            else:
                _t1678 = None
            deconstruct_result1508 = _t1678
            if deconstruct_result1508 is not None:
                assert deconstruct_result1508 is not None
                unwrapped1509 = deconstruct_result1508
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1509) == 0:
                    self.newline()
                    for i1511, elem1510 in enumerate(unwrapped1509):
                        if (i1511 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1510)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1679 = _dollar_dollar.table_def
                else:
                    _t1679 = None
                deconstruct_result1506 = _t1679
                if deconstruct_result1506 is not None:
                    assert deconstruct_result1506 is not None
                    unwrapped1507 = deconstruct_result1506
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1507)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1517 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1517 is not None:
            assert flat1517 is not None
            self.write(flat1517)
            return None
        else:
            _dollar_dollar = msg
            fields1513 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1513 is not None
            unwrapped_fields1514 = fields1513
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1515 = unwrapped_fields1514[0]
            self.write(self.format_string_value(field1515))
            self.newline()
            field1516 = unwrapped_fields1514[1]
            self.pretty_relation_id(field1516)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1521 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1521 is not None:
            assert flat1521 is not None
            self.write(flat1521)
            return None
        else:
            fields1518 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1518) == 0:
                self.newline()
                for i1520, elem1519 in enumerate(fields1518):
                    if (i1520 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1519)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1534 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1534 is not None:
            assert flat1534 is not None
            self.write(flat1534)
            return None
        else:
            _dollar_dollar = msg
            _t1680 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1522 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, sorted(_dollar_dollar.create_table_properties.items()), _t1680,)
            assert fields1522 is not None
            unwrapped_fields1523 = fields1522
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1524 = unwrapped_fields1523[0]
            self.pretty_iceberg_locator(field1524)
            self.newline()
            field1525 = unwrapped_fields1523[1]
            self.pretty_iceberg_config(field1525)
            self.newline()
            self.write("(")
            self.newline()
            self.write("columns")
            field1526 = unwrapped_fields1523[2]
            if not len(field1526) == 0:
                self.newline()
                for i1528, elem1527 in enumerate(field1526):
                    if (i1528 > 0):
                        self.newline()
                    self.pretty_iceberg_export_column(elem1527)
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("create_table_properties")
            field1529 = unwrapped_fields1523[3]
            if not len(field1529) == 0:
                self.newline()
                for i1531, elem1530 in enumerate(field1529):
                    if (i1531 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1530)
            self.dedent()
            self.write(")")
            field1532 = unwrapped_fields1523[4]
            if field1532 is not None:
                self.newline()
                assert field1532 is not None
                opt_val1533 = field1532
                self.pretty_config_dict(opt_val1533)
            self.dedent()
            self.write(")")

    def pretty_iceberg_export_column(self, msg: transactions_pb2.ExportIcebergColumn):
        flat1541 = self._try_flat(msg, self.pretty_iceberg_export_column)
        if flat1541 is not None:
            assert flat1541 is not None
            self.write(flat1541)
            return None
        else:
            _dollar_dollar = msg
            fields1535 = (_dollar_dollar.name, _dollar_dollar.column_data, _dollar_dollar.type, _dollar_dollar.nullable,)
            assert fields1535 is not None
            unwrapped_fields1536 = fields1535
            self.write("(iceberg_column")
            self.indent_sexp()
            self.newline()
            field1537 = unwrapped_fields1536[0]
            self.write(self.format_string_value(field1537))
            self.newline()
            field1538 = unwrapped_fields1536[1]
            self.pretty_relation_id(field1538)
            self.newline()
            field1539 = unwrapped_fields1536[2]
            self.pretty_type(field1539)
            self.newline()
            field1540 = unwrapped_fields1536[3]
            self.pretty_boolean_value(field1540)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1725 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1725)
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
        elif isinstance(msg, transactions_pb2.ExportIcebergColumn):
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
