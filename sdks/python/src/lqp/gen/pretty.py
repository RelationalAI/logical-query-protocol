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
        _t1689 = logic_pb2.Value(int32_value=v)
        return _t1689

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1690 = logic_pb2.Value(int_value=v)
        return _t1690

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1691 = logic_pb2.Value(float_value=v)
        return _t1691

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1692 = logic_pb2.Value(string_value=v)
        return _t1692

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1693 = logic_pb2.Value(boolean_value=v)
        return _t1693

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1694 = logic_pb2.Value(uint128_value=v)
        return _t1694

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1695 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1695,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1696 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1696,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1697 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1697,))
        _t1698 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1698,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1699 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1699,))
        _t1700 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1700,))
        if msg.new_line != "":
            _t1701 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1701,))
        _t1702 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1702,))
        _t1703 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1703,))
        _t1704 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1704,))
        if msg.comment != "":
            _t1705 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1705,))
        for missing_string in msg.missing_strings:
            _t1706 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1706,))
        _t1707 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1707,))
        _t1708 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1708,))
        _t1709 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1709,))
        if msg.partition_size_mb != 0:
            _t1710 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1710,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1711 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1711,))
        _t1712 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1712,))
        _t1713 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1713,))
        _t1714 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1714,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1715 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1715,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1716 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1716,))
        _t1717 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1717,))
        _t1718 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1718,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1719 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1719,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1720 = self._make_value_string(msg.compression)
            result.append(("compression", _t1720,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1721 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1721,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1722 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1722,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1723 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1723,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1724 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1724,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1725 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1725,))
        return sorted(result)

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1726 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1727 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1728 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1728,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1729 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1729,))
        if msg.compression != "":
            _t1730 = self._make_value_string(msg.compression)
            result.append(("compression", _t1730,))
        if len(result) == 0:
            return None
        else:
            _t1731 = None
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
            _t1732 = None
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
        flat784 = self._try_flat(msg, self.pretty_transaction)
        if flat784 is not None:
            assert flat784 is not None
            self.write(flat784)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1550 = _dollar_dollar.configure
            else:
                _t1550 = None
            if _dollar_dollar.HasField("sync"):
                _t1551 = _dollar_dollar.sync
            else:
                _t1551 = None
            fields775 = (_t1550, _t1551, _dollar_dollar.epochs,)
            assert fields775 is not None
            unwrapped_fields776 = fields775
            self.write("(transaction")
            self.indent_sexp()
            field777 = unwrapped_fields776[0]
            if field777 is not None:
                self.newline()
                assert field777 is not None
                opt_val778 = field777
                self.pretty_configure(opt_val778)
            field779 = unwrapped_fields776[1]
            if field779 is not None:
                self.newline()
                assert field779 is not None
                opt_val780 = field779
                self.pretty_sync(opt_val780)
            field781 = unwrapped_fields776[2]
            if not len(field781) == 0:
                self.newline()
                for i783, elem782 in enumerate(field781):
                    if (i783 > 0):
                        self.newline()
                    self.pretty_epoch(elem782)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat787 = self._try_flat(msg, self.pretty_configure)
        if flat787 is not None:
            assert flat787 is not None
            self.write(flat787)
            return None
        else:
            _dollar_dollar = msg
            _t1552 = self.deconstruct_configure(_dollar_dollar)
            fields785 = _t1552
            assert fields785 is not None
            unwrapped_fields786 = fields785
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields786)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat791 = self._try_flat(msg, self.pretty_config_dict)
        if flat791 is not None:
            assert flat791 is not None
            self.write(flat791)
            return None
        else:
            fields788 = msg
            self.write("{")
            self.indent()
            if not len(fields788) == 0:
                self.newline()
                for i790, elem789 in enumerate(fields788):
                    if (i790 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem789)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat796 = self._try_flat(msg, self.pretty_config_key_value)
        if flat796 is not None:
            assert flat796 is not None
            self.write(flat796)
            return None
        else:
            _dollar_dollar = msg
            fields792 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields792 is not None
            unwrapped_fields793 = fields792
            self.write(":")
            field794 = unwrapped_fields793[0]
            self.write(field794)
            self.write(" ")
            field795 = unwrapped_fields793[1]
            self.pretty_raw_value(field795)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat822 = self._try_flat(msg, self.pretty_raw_value)
        if flat822 is not None:
            assert flat822 is not None
            self.write(flat822)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1553 = _dollar_dollar.date_value
            else:
                _t1553 = None
            deconstruct_result820 = _t1553
            if deconstruct_result820 is not None:
                assert deconstruct_result820 is not None
                unwrapped821 = deconstruct_result820
                self.pretty_raw_date(unwrapped821)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1554 = _dollar_dollar.datetime_value
                else:
                    _t1554 = None
                deconstruct_result818 = _t1554
                if deconstruct_result818 is not None:
                    assert deconstruct_result818 is not None
                    unwrapped819 = deconstruct_result818
                    self.pretty_raw_datetime(unwrapped819)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1555 = _dollar_dollar.string_value
                    else:
                        _t1555 = None
                    deconstruct_result816 = _t1555
                    if deconstruct_result816 is not None:
                        assert deconstruct_result816 is not None
                        unwrapped817 = deconstruct_result816
                        self.write(self.format_string_value(unwrapped817))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1556 = _dollar_dollar.int32_value
                        else:
                            _t1556 = None
                        deconstruct_result814 = _t1556
                        if deconstruct_result814 is not None:
                            assert deconstruct_result814 is not None
                            unwrapped815 = deconstruct_result814
                            self.write((str(unwrapped815) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1557 = _dollar_dollar.int_value
                            else:
                                _t1557 = None
                            deconstruct_result812 = _t1557
                            if deconstruct_result812 is not None:
                                assert deconstruct_result812 is not None
                                unwrapped813 = deconstruct_result812
                                self.write(str(unwrapped813))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1558 = _dollar_dollar.float32_value
                                else:
                                    _t1558 = None
                                deconstruct_result810 = _t1558
                                if deconstruct_result810 is not None:
                                    assert deconstruct_result810 is not None
                                    unwrapped811 = deconstruct_result810
                                    self.write(self.format_float32_literal(unwrapped811))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1559 = _dollar_dollar.float_value
                                    else:
                                        _t1559 = None
                                    deconstruct_result808 = _t1559
                                    if deconstruct_result808 is not None:
                                        assert deconstruct_result808 is not None
                                        unwrapped809 = deconstruct_result808
                                        self.write(str(unwrapped809))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1560 = _dollar_dollar.uint32_value
                                        else:
                                            _t1560 = None
                                        deconstruct_result806 = _t1560
                                        if deconstruct_result806 is not None:
                                            assert deconstruct_result806 is not None
                                            unwrapped807 = deconstruct_result806
                                            self.write((str(unwrapped807) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1561 = _dollar_dollar.uint128_value
                                            else:
                                                _t1561 = None
                                            deconstruct_result804 = _t1561
                                            if deconstruct_result804 is not None:
                                                assert deconstruct_result804 is not None
                                                unwrapped805 = deconstruct_result804
                                                self.write(self.format_uint128(unwrapped805))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1562 = _dollar_dollar.int128_value
                                                else:
                                                    _t1562 = None
                                                deconstruct_result802 = _t1562
                                                if deconstruct_result802 is not None:
                                                    assert deconstruct_result802 is not None
                                                    unwrapped803 = deconstruct_result802
                                                    self.write(self.format_int128(unwrapped803))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1563 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1563 = None
                                                    deconstruct_result800 = _t1563
                                                    if deconstruct_result800 is not None:
                                                        assert deconstruct_result800 is not None
                                                        unwrapped801 = deconstruct_result800
                                                        self.write(self.format_decimal(unwrapped801))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1564 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1564 = None
                                                        deconstruct_result798 = _t1564
                                                        if deconstruct_result798 is not None:
                                                            assert deconstruct_result798 is not None
                                                            unwrapped799 = deconstruct_result798
                                                            self.pretty_boolean_value(unwrapped799)
                                                        else:
                                                            fields797 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat828 = self._try_flat(msg, self.pretty_raw_date)
        if flat828 is not None:
            assert flat828 is not None
            self.write(flat828)
            return None
        else:
            _dollar_dollar = msg
            fields823 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields823 is not None
            unwrapped_fields824 = fields823
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field825 = unwrapped_fields824[0]
            self.write(str(field825))
            self.newline()
            field826 = unwrapped_fields824[1]
            self.write(str(field826))
            self.newline()
            field827 = unwrapped_fields824[2]
            self.write(str(field827))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat839 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat839 is not None:
            assert flat839 is not None
            self.write(flat839)
            return None
        else:
            _dollar_dollar = msg
            fields829 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields829 is not None
            unwrapped_fields830 = fields829
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field831 = unwrapped_fields830[0]
            self.write(str(field831))
            self.newline()
            field832 = unwrapped_fields830[1]
            self.write(str(field832))
            self.newline()
            field833 = unwrapped_fields830[2]
            self.write(str(field833))
            self.newline()
            field834 = unwrapped_fields830[3]
            self.write(str(field834))
            self.newline()
            field835 = unwrapped_fields830[4]
            self.write(str(field835))
            self.newline()
            field836 = unwrapped_fields830[5]
            self.write(str(field836))
            field837 = unwrapped_fields830[6]
            if field837 is not None:
                self.newline()
                assert field837 is not None
                opt_val838 = field837
                self.write(str(opt_val838))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1565 = ()
        else:
            _t1565 = None
        deconstruct_result842 = _t1565
        if deconstruct_result842 is not None:
            assert deconstruct_result842 is not None
            unwrapped843 = deconstruct_result842
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1566 = ()
            else:
                _t1566 = None
            deconstruct_result840 = _t1566
            if deconstruct_result840 is not None:
                assert deconstruct_result840 is not None
                unwrapped841 = deconstruct_result840
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat848 = self._try_flat(msg, self.pretty_sync)
        if flat848 is not None:
            assert flat848 is not None
            self.write(flat848)
            return None
        else:
            _dollar_dollar = msg
            fields844 = _dollar_dollar.fragments
            assert fields844 is not None
            unwrapped_fields845 = fields844
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields845) == 0:
                self.newline()
                for i847, elem846 in enumerate(unwrapped_fields845):
                    if (i847 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem846)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat851 = self._try_flat(msg, self.pretty_fragment_id)
        if flat851 is not None:
            assert flat851 is not None
            self.write(flat851)
            return None
        else:
            _dollar_dollar = msg
            fields849 = self.fragment_id_to_string(_dollar_dollar)
            assert fields849 is not None
            unwrapped_fields850 = fields849
            self.write(":")
            self.write(unwrapped_fields850)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat858 = self._try_flat(msg, self.pretty_epoch)
        if flat858 is not None:
            assert flat858 is not None
            self.write(flat858)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1567 = _dollar_dollar.writes
            else:
                _t1567 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1568 = _dollar_dollar.reads
            else:
                _t1568 = None
            fields852 = (_t1567, _t1568,)
            assert fields852 is not None
            unwrapped_fields853 = fields852
            self.write("(epoch")
            self.indent_sexp()
            field854 = unwrapped_fields853[0]
            if field854 is not None:
                self.newline()
                assert field854 is not None
                opt_val855 = field854
                self.pretty_epoch_writes(opt_val855)
            field856 = unwrapped_fields853[1]
            if field856 is not None:
                self.newline()
                assert field856 is not None
                opt_val857 = field856
                self.pretty_epoch_reads(opt_val857)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat862 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat862 is not None:
            assert flat862 is not None
            self.write(flat862)
            return None
        else:
            fields859 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields859) == 0:
                self.newline()
                for i861, elem860 in enumerate(fields859):
                    if (i861 > 0):
                        self.newline()
                    self.pretty_write(elem860)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat871 = self._try_flat(msg, self.pretty_write)
        if flat871 is not None:
            assert flat871 is not None
            self.write(flat871)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1569 = _dollar_dollar.define
            else:
                _t1569 = None
            deconstruct_result869 = _t1569
            if deconstruct_result869 is not None:
                assert deconstruct_result869 is not None
                unwrapped870 = deconstruct_result869
                self.pretty_define(unwrapped870)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1570 = _dollar_dollar.undefine
                else:
                    _t1570 = None
                deconstruct_result867 = _t1570
                if deconstruct_result867 is not None:
                    assert deconstruct_result867 is not None
                    unwrapped868 = deconstruct_result867
                    self.pretty_undefine(unwrapped868)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1571 = _dollar_dollar.context
                    else:
                        _t1571 = None
                    deconstruct_result865 = _t1571
                    if deconstruct_result865 is not None:
                        assert deconstruct_result865 is not None
                        unwrapped866 = deconstruct_result865
                        self.pretty_context(unwrapped866)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1572 = _dollar_dollar.snapshot
                        else:
                            _t1572 = None
                        deconstruct_result863 = _t1572
                        if deconstruct_result863 is not None:
                            assert deconstruct_result863 is not None
                            unwrapped864 = deconstruct_result863
                            self.pretty_snapshot(unwrapped864)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat874 = self._try_flat(msg, self.pretty_define)
        if flat874 is not None:
            assert flat874 is not None
            self.write(flat874)
            return None
        else:
            _dollar_dollar = msg
            fields872 = _dollar_dollar.fragment
            assert fields872 is not None
            unwrapped_fields873 = fields872
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields873)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat881 = self._try_flat(msg, self.pretty_fragment)
        if flat881 is not None:
            assert flat881 is not None
            self.write(flat881)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields875 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields875 is not None
            unwrapped_fields876 = fields875
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field877 = unwrapped_fields876[0]
            self.pretty_new_fragment_id(field877)
            field878 = unwrapped_fields876[1]
            if not len(field878) == 0:
                self.newline()
                for i880, elem879 in enumerate(field878):
                    if (i880 > 0):
                        self.newline()
                    self.pretty_declaration(elem879)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat883 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat883 is not None:
            assert flat883 is not None
            self.write(flat883)
            return None
        else:
            fields882 = msg
            self.pretty_fragment_id(fields882)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat892 = self._try_flat(msg, self.pretty_declaration)
        if flat892 is not None:
            assert flat892 is not None
            self.write(flat892)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1573 = getattr(_dollar_dollar, 'def')
            else:
                _t1573 = None
            deconstruct_result890 = _t1573
            if deconstruct_result890 is not None:
                assert deconstruct_result890 is not None
                unwrapped891 = deconstruct_result890
                self.pretty_def(unwrapped891)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1574 = _dollar_dollar.algorithm
                else:
                    _t1574 = None
                deconstruct_result888 = _t1574
                if deconstruct_result888 is not None:
                    assert deconstruct_result888 is not None
                    unwrapped889 = deconstruct_result888
                    self.pretty_algorithm(unwrapped889)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1575 = _dollar_dollar.constraint
                    else:
                        _t1575 = None
                    deconstruct_result886 = _t1575
                    if deconstruct_result886 is not None:
                        assert deconstruct_result886 is not None
                        unwrapped887 = deconstruct_result886
                        self.pretty_constraint(unwrapped887)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1576 = _dollar_dollar.data
                        else:
                            _t1576 = None
                        deconstruct_result884 = _t1576
                        if deconstruct_result884 is not None:
                            assert deconstruct_result884 is not None
                            unwrapped885 = deconstruct_result884
                            self.pretty_data(unwrapped885)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat899 = self._try_flat(msg, self.pretty_def)
        if flat899 is not None:
            assert flat899 is not None
            self.write(flat899)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1577 = _dollar_dollar.attrs
            else:
                _t1577 = None
            fields893 = (_dollar_dollar.name, _dollar_dollar.body, _t1577,)
            assert fields893 is not None
            unwrapped_fields894 = fields893
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field895 = unwrapped_fields894[0]
            self.pretty_relation_id(field895)
            self.newline()
            field896 = unwrapped_fields894[1]
            self.pretty_abstraction(field896)
            field897 = unwrapped_fields894[2]
            if field897 is not None:
                self.newline()
                assert field897 is not None
                opt_val898 = field897
                self.pretty_attrs(opt_val898)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat904 = self._try_flat(msg, self.pretty_relation_id)
        if flat904 is not None:
            assert flat904 is not None
            self.write(flat904)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1579 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1578 = _t1579
            else:
                _t1578 = None
            deconstruct_result902 = _t1578
            if deconstruct_result902 is not None:
                assert deconstruct_result902 is not None
                unwrapped903 = deconstruct_result902
                self.write(":")
                self.write(unwrapped903)
            else:
                _dollar_dollar = msg
                _t1580 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result900 = _t1580
                if deconstruct_result900 is not None:
                    assert deconstruct_result900 is not None
                    unwrapped901 = deconstruct_result900
                    self.write(self.format_uint128(unwrapped901))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat909 = self._try_flat(msg, self.pretty_abstraction)
        if flat909 is not None:
            assert flat909 is not None
            self.write(flat909)
            return None
        else:
            _dollar_dollar = msg
            _t1581 = self.deconstruct_bindings(_dollar_dollar)
            fields905 = (_t1581, _dollar_dollar.value,)
            assert fields905 is not None
            unwrapped_fields906 = fields905
            self.write("(")
            self.indent()
            field907 = unwrapped_fields906[0]
            self.pretty_bindings(field907)
            self.newline()
            field908 = unwrapped_fields906[1]
            self.pretty_formula(field908)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat917 = self._try_flat(msg, self.pretty_bindings)
        if flat917 is not None:
            assert flat917 is not None
            self.write(flat917)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1582 = _dollar_dollar[1]
            else:
                _t1582 = None
            fields910 = (_dollar_dollar[0], _t1582,)
            assert fields910 is not None
            unwrapped_fields911 = fields910
            self.write("[")
            self.indent()
            field912 = unwrapped_fields911[0]
            for i914, elem913 in enumerate(field912):
                if (i914 > 0):
                    self.newline()
                self.pretty_binding(elem913)
            field915 = unwrapped_fields911[1]
            if field915 is not None:
                self.newline()
                assert field915 is not None
                opt_val916 = field915
                self.pretty_value_bindings(opt_val916)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat922 = self._try_flat(msg, self.pretty_binding)
        if flat922 is not None:
            assert flat922 is not None
            self.write(flat922)
            return None
        else:
            _dollar_dollar = msg
            fields918 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields918 is not None
            unwrapped_fields919 = fields918
            field920 = unwrapped_fields919[0]
            self.write(field920)
            self.write("::")
            field921 = unwrapped_fields919[1]
            self.pretty_type(field921)

    def pretty_type(self, msg: logic_pb2.Type):
        flat951 = self._try_flat(msg, self.pretty_type)
        if flat951 is not None:
            assert flat951 is not None
            self.write(flat951)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1583 = _dollar_dollar.unspecified_type
            else:
                _t1583 = None
            deconstruct_result949 = _t1583
            if deconstruct_result949 is not None:
                assert deconstruct_result949 is not None
                unwrapped950 = deconstruct_result949
                self.pretty_unspecified_type(unwrapped950)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1584 = _dollar_dollar.string_type
                else:
                    _t1584 = None
                deconstruct_result947 = _t1584
                if deconstruct_result947 is not None:
                    assert deconstruct_result947 is not None
                    unwrapped948 = deconstruct_result947
                    self.pretty_string_type(unwrapped948)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1585 = _dollar_dollar.int_type
                    else:
                        _t1585 = None
                    deconstruct_result945 = _t1585
                    if deconstruct_result945 is not None:
                        assert deconstruct_result945 is not None
                        unwrapped946 = deconstruct_result945
                        self.pretty_int_type(unwrapped946)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1586 = _dollar_dollar.float_type
                        else:
                            _t1586 = None
                        deconstruct_result943 = _t1586
                        if deconstruct_result943 is not None:
                            assert deconstruct_result943 is not None
                            unwrapped944 = deconstruct_result943
                            self.pretty_float_type(unwrapped944)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1587 = _dollar_dollar.uint128_type
                            else:
                                _t1587 = None
                            deconstruct_result941 = _t1587
                            if deconstruct_result941 is not None:
                                assert deconstruct_result941 is not None
                                unwrapped942 = deconstruct_result941
                                self.pretty_uint128_type(unwrapped942)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1588 = _dollar_dollar.int128_type
                                else:
                                    _t1588 = None
                                deconstruct_result939 = _t1588
                                if deconstruct_result939 is not None:
                                    assert deconstruct_result939 is not None
                                    unwrapped940 = deconstruct_result939
                                    self.pretty_int128_type(unwrapped940)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1589 = _dollar_dollar.date_type
                                    else:
                                        _t1589 = None
                                    deconstruct_result937 = _t1589
                                    if deconstruct_result937 is not None:
                                        assert deconstruct_result937 is not None
                                        unwrapped938 = deconstruct_result937
                                        self.pretty_date_type(unwrapped938)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1590 = _dollar_dollar.datetime_type
                                        else:
                                            _t1590 = None
                                        deconstruct_result935 = _t1590
                                        if deconstruct_result935 is not None:
                                            assert deconstruct_result935 is not None
                                            unwrapped936 = deconstruct_result935
                                            self.pretty_datetime_type(unwrapped936)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1591 = _dollar_dollar.missing_type
                                            else:
                                                _t1591 = None
                                            deconstruct_result933 = _t1591
                                            if deconstruct_result933 is not None:
                                                assert deconstruct_result933 is not None
                                                unwrapped934 = deconstruct_result933
                                                self.pretty_missing_type(unwrapped934)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1592 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1592 = None
                                                deconstruct_result931 = _t1592
                                                if deconstruct_result931 is not None:
                                                    assert deconstruct_result931 is not None
                                                    unwrapped932 = deconstruct_result931
                                                    self.pretty_decimal_type(unwrapped932)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1593 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1593 = None
                                                    deconstruct_result929 = _t1593
                                                    if deconstruct_result929 is not None:
                                                        assert deconstruct_result929 is not None
                                                        unwrapped930 = deconstruct_result929
                                                        self.pretty_boolean_type(unwrapped930)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1594 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1594 = None
                                                        deconstruct_result927 = _t1594
                                                        if deconstruct_result927 is not None:
                                                            assert deconstruct_result927 is not None
                                                            unwrapped928 = deconstruct_result927
                                                            self.pretty_int32_type(unwrapped928)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1595 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1595 = None
                                                            deconstruct_result925 = _t1595
                                                            if deconstruct_result925 is not None:
                                                                assert deconstruct_result925 is not None
                                                                unwrapped926 = deconstruct_result925
                                                                self.pretty_float32_type(unwrapped926)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1596 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1596 = None
                                                                deconstruct_result923 = _t1596
                                                                if deconstruct_result923 is not None:
                                                                    assert deconstruct_result923 is not None
                                                                    unwrapped924 = deconstruct_result923
                                                                    self.pretty_uint32_type(unwrapped924)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields952 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields953 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields954 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields955 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields956 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields957 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields958 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields959 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields960 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat965 = self._try_flat(msg, self.pretty_decimal_type)
        if flat965 is not None:
            assert flat965 is not None
            self.write(flat965)
            return None
        else:
            _dollar_dollar = msg
            fields961 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields961 is not None
            unwrapped_fields962 = fields961
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field963 = unwrapped_fields962[0]
            self.write(str(field963))
            self.newline()
            field964 = unwrapped_fields962[1]
            self.write(str(field964))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields966 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields967 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields968 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields969 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat973 = self._try_flat(msg, self.pretty_value_bindings)
        if flat973 is not None:
            assert flat973 is not None
            self.write(flat973)
            return None
        else:
            fields970 = msg
            self.write("|")
            if not len(fields970) == 0:
                self.write(" ")
                for i972, elem971 in enumerate(fields970):
                    if (i972 > 0):
                        self.newline()
                    self.pretty_binding(elem971)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat1000 = self._try_flat(msg, self.pretty_formula)
        if flat1000 is not None:
            assert flat1000 is not None
            self.write(flat1000)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1597 = _dollar_dollar.conjunction
            else:
                _t1597 = None
            deconstruct_result998 = _t1597
            if deconstruct_result998 is not None:
                assert deconstruct_result998 is not None
                unwrapped999 = deconstruct_result998
                self.pretty_true(unwrapped999)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1598 = _dollar_dollar.disjunction
                else:
                    _t1598 = None
                deconstruct_result996 = _t1598
                if deconstruct_result996 is not None:
                    assert deconstruct_result996 is not None
                    unwrapped997 = deconstruct_result996
                    self.pretty_false(unwrapped997)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1599 = _dollar_dollar.exists
                    else:
                        _t1599 = None
                    deconstruct_result994 = _t1599
                    if deconstruct_result994 is not None:
                        assert deconstruct_result994 is not None
                        unwrapped995 = deconstruct_result994
                        self.pretty_exists(unwrapped995)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1600 = _dollar_dollar.reduce
                        else:
                            _t1600 = None
                        deconstruct_result992 = _t1600
                        if deconstruct_result992 is not None:
                            assert deconstruct_result992 is not None
                            unwrapped993 = deconstruct_result992
                            self.pretty_reduce(unwrapped993)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1601 = _dollar_dollar.conjunction
                            else:
                                _t1601 = None
                            deconstruct_result990 = _t1601
                            if deconstruct_result990 is not None:
                                assert deconstruct_result990 is not None
                                unwrapped991 = deconstruct_result990
                                self.pretty_conjunction(unwrapped991)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1602 = _dollar_dollar.disjunction
                                else:
                                    _t1602 = None
                                deconstruct_result988 = _t1602
                                if deconstruct_result988 is not None:
                                    assert deconstruct_result988 is not None
                                    unwrapped989 = deconstruct_result988
                                    self.pretty_disjunction(unwrapped989)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1603 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1603 = None
                                    deconstruct_result986 = _t1603
                                    if deconstruct_result986 is not None:
                                        assert deconstruct_result986 is not None
                                        unwrapped987 = deconstruct_result986
                                        self.pretty_not(unwrapped987)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1604 = _dollar_dollar.ffi
                                        else:
                                            _t1604 = None
                                        deconstruct_result984 = _t1604
                                        if deconstruct_result984 is not None:
                                            assert deconstruct_result984 is not None
                                            unwrapped985 = deconstruct_result984
                                            self.pretty_ffi(unwrapped985)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1605 = _dollar_dollar.atom
                                            else:
                                                _t1605 = None
                                            deconstruct_result982 = _t1605
                                            if deconstruct_result982 is not None:
                                                assert deconstruct_result982 is not None
                                                unwrapped983 = deconstruct_result982
                                                self.pretty_atom(unwrapped983)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1606 = _dollar_dollar.pragma
                                                else:
                                                    _t1606 = None
                                                deconstruct_result980 = _t1606
                                                if deconstruct_result980 is not None:
                                                    assert deconstruct_result980 is not None
                                                    unwrapped981 = deconstruct_result980
                                                    self.pretty_pragma(unwrapped981)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1607 = _dollar_dollar.primitive
                                                    else:
                                                        _t1607 = None
                                                    deconstruct_result978 = _t1607
                                                    if deconstruct_result978 is not None:
                                                        assert deconstruct_result978 is not None
                                                        unwrapped979 = deconstruct_result978
                                                        self.pretty_primitive(unwrapped979)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1608 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1608 = None
                                                        deconstruct_result976 = _t1608
                                                        if deconstruct_result976 is not None:
                                                            assert deconstruct_result976 is not None
                                                            unwrapped977 = deconstruct_result976
                                                            self.pretty_rel_atom(unwrapped977)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1609 = _dollar_dollar.cast
                                                            else:
                                                                _t1609 = None
                                                            deconstruct_result974 = _t1609
                                                            if deconstruct_result974 is not None:
                                                                assert deconstruct_result974 is not None
                                                                unwrapped975 = deconstruct_result974
                                                                self.pretty_cast(unwrapped975)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields1001 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields1002 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1007 = self._try_flat(msg, self.pretty_exists)
        if flat1007 is not None:
            assert flat1007 is not None
            self.write(flat1007)
            return None
        else:
            _dollar_dollar = msg
            _t1610 = self.deconstruct_bindings(_dollar_dollar.body)
            fields1003 = (_t1610, _dollar_dollar.body.value,)
            assert fields1003 is not None
            unwrapped_fields1004 = fields1003
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1005 = unwrapped_fields1004[0]
            self.pretty_bindings(field1005)
            self.newline()
            field1006 = unwrapped_fields1004[1]
            self.pretty_formula(field1006)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1013 = self._try_flat(msg, self.pretty_reduce)
        if flat1013 is not None:
            assert flat1013 is not None
            self.write(flat1013)
            return None
        else:
            _dollar_dollar = msg
            fields1008 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1008 is not None
            unwrapped_fields1009 = fields1008
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1010 = unwrapped_fields1009[0]
            self.pretty_abstraction(field1010)
            self.newline()
            field1011 = unwrapped_fields1009[1]
            self.pretty_abstraction(field1011)
            self.newline()
            field1012 = unwrapped_fields1009[2]
            self.pretty_terms(field1012)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1017 = self._try_flat(msg, self.pretty_terms)
        if flat1017 is not None:
            assert flat1017 is not None
            self.write(flat1017)
            return None
        else:
            fields1014 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1014) == 0:
                self.newline()
                for i1016, elem1015 in enumerate(fields1014):
                    if (i1016 > 0):
                        self.newline()
                    self.pretty_term(elem1015)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1022 = self._try_flat(msg, self.pretty_term)
        if flat1022 is not None:
            assert flat1022 is not None
            self.write(flat1022)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1611 = _dollar_dollar.var
            else:
                _t1611 = None
            deconstruct_result1020 = _t1611
            if deconstruct_result1020 is not None:
                assert deconstruct_result1020 is not None
                unwrapped1021 = deconstruct_result1020
                self.pretty_var(unwrapped1021)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1612 = _dollar_dollar.constant
                else:
                    _t1612 = None
                deconstruct_result1018 = _t1612
                if deconstruct_result1018 is not None:
                    assert deconstruct_result1018 is not None
                    unwrapped1019 = deconstruct_result1018
                    self.pretty_value(unwrapped1019)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1025 = self._try_flat(msg, self.pretty_var)
        if flat1025 is not None:
            assert flat1025 is not None
            self.write(flat1025)
            return None
        else:
            _dollar_dollar = msg
            fields1023 = _dollar_dollar.name
            assert fields1023 is not None
            unwrapped_fields1024 = fields1023
            self.write(unwrapped_fields1024)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1051 = self._try_flat(msg, self.pretty_value)
        if flat1051 is not None:
            assert flat1051 is not None
            self.write(flat1051)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1613 = _dollar_dollar.date_value
            else:
                _t1613 = None
            deconstruct_result1049 = _t1613
            if deconstruct_result1049 is not None:
                assert deconstruct_result1049 is not None
                unwrapped1050 = deconstruct_result1049
                self.pretty_date(unwrapped1050)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1614 = _dollar_dollar.datetime_value
                else:
                    _t1614 = None
                deconstruct_result1047 = _t1614
                if deconstruct_result1047 is not None:
                    assert deconstruct_result1047 is not None
                    unwrapped1048 = deconstruct_result1047
                    self.pretty_datetime(unwrapped1048)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1615 = _dollar_dollar.string_value
                    else:
                        _t1615 = None
                    deconstruct_result1045 = _t1615
                    if deconstruct_result1045 is not None:
                        assert deconstruct_result1045 is not None
                        unwrapped1046 = deconstruct_result1045
                        self.write(self.format_string_value(unwrapped1046))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1616 = _dollar_dollar.int32_value
                        else:
                            _t1616 = None
                        deconstruct_result1043 = _t1616
                        if deconstruct_result1043 is not None:
                            assert deconstruct_result1043 is not None
                            unwrapped1044 = deconstruct_result1043
                            self.write((str(unwrapped1044) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1617 = _dollar_dollar.int_value
                            else:
                                _t1617 = None
                            deconstruct_result1041 = _t1617
                            if deconstruct_result1041 is not None:
                                assert deconstruct_result1041 is not None
                                unwrapped1042 = deconstruct_result1041
                                self.write(str(unwrapped1042))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1618 = _dollar_dollar.float32_value
                                else:
                                    _t1618 = None
                                deconstruct_result1039 = _t1618
                                if deconstruct_result1039 is not None:
                                    assert deconstruct_result1039 is not None
                                    unwrapped1040 = deconstruct_result1039
                                    self.write(self.format_float32_literal(unwrapped1040))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1619 = _dollar_dollar.float_value
                                    else:
                                        _t1619 = None
                                    deconstruct_result1037 = _t1619
                                    if deconstruct_result1037 is not None:
                                        assert deconstruct_result1037 is not None
                                        unwrapped1038 = deconstruct_result1037
                                        self.write(str(unwrapped1038))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1620 = _dollar_dollar.uint32_value
                                        else:
                                            _t1620 = None
                                        deconstruct_result1035 = _t1620
                                        if deconstruct_result1035 is not None:
                                            assert deconstruct_result1035 is not None
                                            unwrapped1036 = deconstruct_result1035
                                            self.write((str(unwrapped1036) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1621 = _dollar_dollar.uint128_value
                                            else:
                                                _t1621 = None
                                            deconstruct_result1033 = _t1621
                                            if deconstruct_result1033 is not None:
                                                assert deconstruct_result1033 is not None
                                                unwrapped1034 = deconstruct_result1033
                                                self.write(self.format_uint128(unwrapped1034))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1622 = _dollar_dollar.int128_value
                                                else:
                                                    _t1622 = None
                                                deconstruct_result1031 = _t1622
                                                if deconstruct_result1031 is not None:
                                                    assert deconstruct_result1031 is not None
                                                    unwrapped1032 = deconstruct_result1031
                                                    self.write(self.format_int128(unwrapped1032))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1623 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1623 = None
                                                    deconstruct_result1029 = _t1623
                                                    if deconstruct_result1029 is not None:
                                                        assert deconstruct_result1029 is not None
                                                        unwrapped1030 = deconstruct_result1029
                                                        self.write(self.format_decimal(unwrapped1030))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1624 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1624 = None
                                                        deconstruct_result1027 = _t1624
                                                        if deconstruct_result1027 is not None:
                                                            assert deconstruct_result1027 is not None
                                                            unwrapped1028 = deconstruct_result1027
                                                            self.pretty_boolean_value(unwrapped1028)
                                                        else:
                                                            fields1026 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1057 = self._try_flat(msg, self.pretty_date)
        if flat1057 is not None:
            assert flat1057 is not None
            self.write(flat1057)
            return None
        else:
            _dollar_dollar = msg
            fields1052 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1052 is not None
            unwrapped_fields1053 = fields1052
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1054 = unwrapped_fields1053[0]
            self.write(str(field1054))
            self.newline()
            field1055 = unwrapped_fields1053[1]
            self.write(str(field1055))
            self.newline()
            field1056 = unwrapped_fields1053[2]
            self.write(str(field1056))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1068 = self._try_flat(msg, self.pretty_datetime)
        if flat1068 is not None:
            assert flat1068 is not None
            self.write(flat1068)
            return None
        else:
            _dollar_dollar = msg
            fields1058 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1058 is not None
            unwrapped_fields1059 = fields1058
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1060 = unwrapped_fields1059[0]
            self.write(str(field1060))
            self.newline()
            field1061 = unwrapped_fields1059[1]
            self.write(str(field1061))
            self.newline()
            field1062 = unwrapped_fields1059[2]
            self.write(str(field1062))
            self.newline()
            field1063 = unwrapped_fields1059[3]
            self.write(str(field1063))
            self.newline()
            field1064 = unwrapped_fields1059[4]
            self.write(str(field1064))
            self.newline()
            field1065 = unwrapped_fields1059[5]
            self.write(str(field1065))
            field1066 = unwrapped_fields1059[6]
            if field1066 is not None:
                self.newline()
                assert field1066 is not None
                opt_val1067 = field1066
                self.write(str(opt_val1067))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1073 = self._try_flat(msg, self.pretty_conjunction)
        if flat1073 is not None:
            assert flat1073 is not None
            self.write(flat1073)
            return None
        else:
            _dollar_dollar = msg
            fields1069 = _dollar_dollar.args
            assert fields1069 is not None
            unwrapped_fields1070 = fields1069
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1070) == 0:
                self.newline()
                for i1072, elem1071 in enumerate(unwrapped_fields1070):
                    if (i1072 > 0):
                        self.newline()
                    self.pretty_formula(elem1071)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1078 = self._try_flat(msg, self.pretty_disjunction)
        if flat1078 is not None:
            assert flat1078 is not None
            self.write(flat1078)
            return None
        else:
            _dollar_dollar = msg
            fields1074 = _dollar_dollar.args
            assert fields1074 is not None
            unwrapped_fields1075 = fields1074
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1075) == 0:
                self.newline()
                for i1077, elem1076 in enumerate(unwrapped_fields1075):
                    if (i1077 > 0):
                        self.newline()
                    self.pretty_formula(elem1076)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1081 = self._try_flat(msg, self.pretty_not)
        if flat1081 is not None:
            assert flat1081 is not None
            self.write(flat1081)
            return None
        else:
            _dollar_dollar = msg
            fields1079 = _dollar_dollar.arg
            assert fields1079 is not None
            unwrapped_fields1080 = fields1079
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1080)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1087 = self._try_flat(msg, self.pretty_ffi)
        if flat1087 is not None:
            assert flat1087 is not None
            self.write(flat1087)
            return None
        else:
            _dollar_dollar = msg
            fields1082 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1082 is not None
            unwrapped_fields1083 = fields1082
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1084 = unwrapped_fields1083[0]
            self.pretty_name(field1084)
            self.newline()
            field1085 = unwrapped_fields1083[1]
            self.pretty_ffi_args(field1085)
            self.newline()
            field1086 = unwrapped_fields1083[2]
            self.pretty_terms(field1086)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1089 = self._try_flat(msg, self.pretty_name)
        if flat1089 is not None:
            assert flat1089 is not None
            self.write(flat1089)
            return None
        else:
            fields1088 = msg
            self.write(":")
            self.write(fields1088)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1093 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1093 is not None:
            assert flat1093 is not None
            self.write(flat1093)
            return None
        else:
            fields1090 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1090) == 0:
                self.newline()
                for i1092, elem1091 in enumerate(fields1090):
                    if (i1092 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1091)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1100 = self._try_flat(msg, self.pretty_atom)
        if flat1100 is not None:
            assert flat1100 is not None
            self.write(flat1100)
            return None
        else:
            _dollar_dollar = msg
            fields1094 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1094 is not None
            unwrapped_fields1095 = fields1094
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1096 = unwrapped_fields1095[0]
            self.pretty_relation_id(field1096)
            field1097 = unwrapped_fields1095[1]
            if not len(field1097) == 0:
                self.newline()
                for i1099, elem1098 in enumerate(field1097):
                    if (i1099 > 0):
                        self.newline()
                    self.pretty_term(elem1098)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1107 = self._try_flat(msg, self.pretty_pragma)
        if flat1107 is not None:
            assert flat1107 is not None
            self.write(flat1107)
            return None
        else:
            _dollar_dollar = msg
            fields1101 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1101 is not None
            unwrapped_fields1102 = fields1101
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1103 = unwrapped_fields1102[0]
            self.pretty_name(field1103)
            field1104 = unwrapped_fields1102[1]
            if not len(field1104) == 0:
                self.newline()
                for i1106, elem1105 in enumerate(field1104):
                    if (i1106 > 0):
                        self.newline()
                    self.pretty_term(elem1105)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1123 = self._try_flat(msg, self.pretty_primitive)
        if flat1123 is not None:
            assert flat1123 is not None
            self.write(flat1123)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1625 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1625 = None
            guard_result1122 = _t1625
            if guard_result1122 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1626 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1626 = None
                guard_result1121 = _t1626
                if guard_result1121 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1627 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1627 = None
                    guard_result1120 = _t1627
                    if guard_result1120 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1628 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1628 = None
                        guard_result1119 = _t1628
                        if guard_result1119 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1629 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1629 = None
                            guard_result1118 = _t1629
                            if guard_result1118 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1630 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1630 = None
                                guard_result1117 = _t1630
                                if guard_result1117 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1631 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1631 = None
                                    guard_result1116 = _t1631
                                    if guard_result1116 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1632 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1632 = None
                                        guard_result1115 = _t1632
                                        if guard_result1115 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1633 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1633 = None
                                            guard_result1114 = _t1633
                                            if guard_result1114 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1108 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1108 is not None
                                                unwrapped_fields1109 = fields1108
                                                self.write("(primitive")
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
                                                        self.pretty_rel_term(elem1112)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1128 = self._try_flat(msg, self.pretty_eq)
        if flat1128 is not None:
            assert flat1128 is not None
            self.write(flat1128)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1634 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1634 = None
            fields1124 = _t1634
            assert fields1124 is not None
            unwrapped_fields1125 = fields1124
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1126 = unwrapped_fields1125[0]
            self.pretty_term(field1126)
            self.newline()
            field1127 = unwrapped_fields1125[1]
            self.pretty_term(field1127)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1133 = self._try_flat(msg, self.pretty_lt)
        if flat1133 is not None:
            assert flat1133 is not None
            self.write(flat1133)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1635 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1635 = None
            fields1129 = _t1635
            assert fields1129 is not None
            unwrapped_fields1130 = fields1129
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1131 = unwrapped_fields1130[0]
            self.pretty_term(field1131)
            self.newline()
            field1132 = unwrapped_fields1130[1]
            self.pretty_term(field1132)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1138 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1138 is not None:
            assert flat1138 is not None
            self.write(flat1138)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1636 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1636 = None
            fields1134 = _t1636
            assert fields1134 is not None
            unwrapped_fields1135 = fields1134
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1136 = unwrapped_fields1135[0]
            self.pretty_term(field1136)
            self.newline()
            field1137 = unwrapped_fields1135[1]
            self.pretty_term(field1137)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1143 = self._try_flat(msg, self.pretty_gt)
        if flat1143 is not None:
            assert flat1143 is not None
            self.write(flat1143)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1637 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1637 = None
            fields1139 = _t1637
            assert fields1139 is not None
            unwrapped_fields1140 = fields1139
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1141 = unwrapped_fields1140[0]
            self.pretty_term(field1141)
            self.newline()
            field1142 = unwrapped_fields1140[1]
            self.pretty_term(field1142)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1148 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1148 is not None:
            assert flat1148 is not None
            self.write(flat1148)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1638 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1638 = None
            fields1144 = _t1638
            assert fields1144 is not None
            unwrapped_fields1145 = fields1144
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1146 = unwrapped_fields1145[0]
            self.pretty_term(field1146)
            self.newline()
            field1147 = unwrapped_fields1145[1]
            self.pretty_term(field1147)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1154 = self._try_flat(msg, self.pretty_add)
        if flat1154 is not None:
            assert flat1154 is not None
            self.write(flat1154)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1639 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1639 = None
            fields1149 = _t1639
            assert fields1149 is not None
            unwrapped_fields1150 = fields1149
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1151 = unwrapped_fields1150[0]
            self.pretty_term(field1151)
            self.newline()
            field1152 = unwrapped_fields1150[1]
            self.pretty_term(field1152)
            self.newline()
            field1153 = unwrapped_fields1150[2]
            self.pretty_term(field1153)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1160 = self._try_flat(msg, self.pretty_minus)
        if flat1160 is not None:
            assert flat1160 is not None
            self.write(flat1160)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1640 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1640 = None
            fields1155 = _t1640
            assert fields1155 is not None
            unwrapped_fields1156 = fields1155
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1157 = unwrapped_fields1156[0]
            self.pretty_term(field1157)
            self.newline()
            field1158 = unwrapped_fields1156[1]
            self.pretty_term(field1158)
            self.newline()
            field1159 = unwrapped_fields1156[2]
            self.pretty_term(field1159)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1166 = self._try_flat(msg, self.pretty_multiply)
        if flat1166 is not None:
            assert flat1166 is not None
            self.write(flat1166)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1641 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1641 = None
            fields1161 = _t1641
            assert fields1161 is not None
            unwrapped_fields1162 = fields1161
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1163 = unwrapped_fields1162[0]
            self.pretty_term(field1163)
            self.newline()
            field1164 = unwrapped_fields1162[1]
            self.pretty_term(field1164)
            self.newline()
            field1165 = unwrapped_fields1162[2]
            self.pretty_term(field1165)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1172 = self._try_flat(msg, self.pretty_divide)
        if flat1172 is not None:
            assert flat1172 is not None
            self.write(flat1172)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1642 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1642 = None
            fields1167 = _t1642
            assert fields1167 is not None
            unwrapped_fields1168 = fields1167
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1169 = unwrapped_fields1168[0]
            self.pretty_term(field1169)
            self.newline()
            field1170 = unwrapped_fields1168[1]
            self.pretty_term(field1170)
            self.newline()
            field1171 = unwrapped_fields1168[2]
            self.pretty_term(field1171)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1177 = self._try_flat(msg, self.pretty_rel_term)
        if flat1177 is not None:
            assert flat1177 is not None
            self.write(flat1177)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1643 = _dollar_dollar.specialized_value
            else:
                _t1643 = None
            deconstruct_result1175 = _t1643
            if deconstruct_result1175 is not None:
                assert deconstruct_result1175 is not None
                unwrapped1176 = deconstruct_result1175
                self.pretty_specialized_value(unwrapped1176)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1644 = _dollar_dollar.term
                else:
                    _t1644 = None
                deconstruct_result1173 = _t1644
                if deconstruct_result1173 is not None:
                    assert deconstruct_result1173 is not None
                    unwrapped1174 = deconstruct_result1173
                    self.pretty_term(unwrapped1174)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1179 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1179 is not None:
            assert flat1179 is not None
            self.write(flat1179)
            return None
        else:
            fields1178 = msg
            self.write("#")
            self.pretty_raw_value(fields1178)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1186 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1186 is not None:
            assert flat1186 is not None
            self.write(flat1186)
            return None
        else:
            _dollar_dollar = msg
            fields1180 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1180 is not None
            unwrapped_fields1181 = fields1180
            self.write("(relatom")
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

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1191 = self._try_flat(msg, self.pretty_cast)
        if flat1191 is not None:
            assert flat1191 is not None
            self.write(flat1191)
            return None
        else:
            _dollar_dollar = msg
            fields1187 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1187 is not None
            unwrapped_fields1188 = fields1187
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1189 = unwrapped_fields1188[0]
            self.pretty_term(field1189)
            self.newline()
            field1190 = unwrapped_fields1188[1]
            self.pretty_term(field1190)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1195 = self._try_flat(msg, self.pretty_attrs)
        if flat1195 is not None:
            assert flat1195 is not None
            self.write(flat1195)
            return None
        else:
            fields1192 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1192) == 0:
                self.newline()
                for i1194, elem1193 in enumerate(fields1192):
                    if (i1194 > 0):
                        self.newline()
                    self.pretty_attribute(elem1193)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1202 = self._try_flat(msg, self.pretty_attribute)
        if flat1202 is not None:
            assert flat1202 is not None
            self.write(flat1202)
            return None
        else:
            _dollar_dollar = msg
            fields1196 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1196 is not None
            unwrapped_fields1197 = fields1196
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1198 = unwrapped_fields1197[0]
            self.pretty_name(field1198)
            field1199 = unwrapped_fields1197[1]
            if not len(field1199) == 0:
                self.newline()
                for i1201, elem1200 in enumerate(field1199):
                    if (i1201 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1200)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1209 = self._try_flat(msg, self.pretty_algorithm)
        if flat1209 is not None:
            assert flat1209 is not None
            self.write(flat1209)
            return None
        else:
            _dollar_dollar = msg
            fields1203 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            assert fields1203 is not None
            unwrapped_fields1204 = fields1203
            self.write("(algorithm")
            self.indent_sexp()
            field1205 = unwrapped_fields1204[0]
            if not len(field1205) == 0:
                self.newline()
                for i1207, elem1206 in enumerate(field1205):
                    if (i1207 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1206)
            self.newline()
            field1208 = unwrapped_fields1204[1]
            self.pretty_script(field1208)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1214 = self._try_flat(msg, self.pretty_script)
        if flat1214 is not None:
            assert flat1214 is not None
            self.write(flat1214)
            return None
        else:
            _dollar_dollar = msg
            fields1210 = _dollar_dollar.constructs
            assert fields1210 is not None
            unwrapped_fields1211 = fields1210
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1211) == 0:
                self.newline()
                for i1213, elem1212 in enumerate(unwrapped_fields1211):
                    if (i1213 > 0):
                        self.newline()
                    self.pretty_construct(elem1212)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1219 = self._try_flat(msg, self.pretty_construct)
        if flat1219 is not None:
            assert flat1219 is not None
            self.write(flat1219)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1645 = _dollar_dollar.loop
            else:
                _t1645 = None
            deconstruct_result1217 = _t1645
            if deconstruct_result1217 is not None:
                assert deconstruct_result1217 is not None
                unwrapped1218 = deconstruct_result1217
                self.pretty_loop(unwrapped1218)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1646 = _dollar_dollar.instruction
                else:
                    _t1646 = None
                deconstruct_result1215 = _t1646
                if deconstruct_result1215 is not None:
                    assert deconstruct_result1215 is not None
                    unwrapped1216 = deconstruct_result1215
                    self.pretty_instruction(unwrapped1216)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1224 = self._try_flat(msg, self.pretty_loop)
        if flat1224 is not None:
            assert flat1224 is not None
            self.write(flat1224)
            return None
        else:
            _dollar_dollar = msg
            fields1220 = (_dollar_dollar.init, _dollar_dollar.body,)
            assert fields1220 is not None
            unwrapped_fields1221 = fields1220
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1222 = unwrapped_fields1221[0]
            self.pretty_init(field1222)
            self.newline()
            field1223 = unwrapped_fields1221[1]
            self.pretty_script(field1223)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1228 = self._try_flat(msg, self.pretty_init)
        if flat1228 is not None:
            assert flat1228 is not None
            self.write(flat1228)
            return None
        else:
            fields1225 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1225) == 0:
                self.newline()
                for i1227, elem1226 in enumerate(fields1225):
                    if (i1227 > 0):
                        self.newline()
                    self.pretty_instruction(elem1226)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1239 = self._try_flat(msg, self.pretty_instruction)
        if flat1239 is not None:
            assert flat1239 is not None
            self.write(flat1239)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1647 = _dollar_dollar.assign
            else:
                _t1647 = None
            deconstruct_result1237 = _t1647
            if deconstruct_result1237 is not None:
                assert deconstruct_result1237 is not None
                unwrapped1238 = deconstruct_result1237
                self.pretty_assign(unwrapped1238)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1648 = _dollar_dollar.upsert
                else:
                    _t1648 = None
                deconstruct_result1235 = _t1648
                if deconstruct_result1235 is not None:
                    assert deconstruct_result1235 is not None
                    unwrapped1236 = deconstruct_result1235
                    self.pretty_upsert(unwrapped1236)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1649 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1649 = None
                    deconstruct_result1233 = _t1649
                    if deconstruct_result1233 is not None:
                        assert deconstruct_result1233 is not None
                        unwrapped1234 = deconstruct_result1233
                        self.pretty_break(unwrapped1234)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1650 = _dollar_dollar.monoid_def
                        else:
                            _t1650 = None
                        deconstruct_result1231 = _t1650
                        if deconstruct_result1231 is not None:
                            assert deconstruct_result1231 is not None
                            unwrapped1232 = deconstruct_result1231
                            self.pretty_monoid_def(unwrapped1232)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1651 = _dollar_dollar.monus_def
                            else:
                                _t1651 = None
                            deconstruct_result1229 = _t1651
                            if deconstruct_result1229 is not None:
                                assert deconstruct_result1229 is not None
                                unwrapped1230 = deconstruct_result1229
                                self.pretty_monus_def(unwrapped1230)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1246 = self._try_flat(msg, self.pretty_assign)
        if flat1246 is not None:
            assert flat1246 is not None
            self.write(flat1246)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1652 = _dollar_dollar.attrs
            else:
                _t1652 = None
            fields1240 = (_dollar_dollar.name, _dollar_dollar.body, _t1652,)
            assert fields1240 is not None
            unwrapped_fields1241 = fields1240
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1242 = unwrapped_fields1241[0]
            self.pretty_relation_id(field1242)
            self.newline()
            field1243 = unwrapped_fields1241[1]
            self.pretty_abstraction(field1243)
            field1244 = unwrapped_fields1241[2]
            if field1244 is not None:
                self.newline()
                assert field1244 is not None
                opt_val1245 = field1244
                self.pretty_attrs(opt_val1245)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1253 = self._try_flat(msg, self.pretty_upsert)
        if flat1253 is not None:
            assert flat1253 is not None
            self.write(flat1253)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1653 = _dollar_dollar.attrs
            else:
                _t1653 = None
            fields1247 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1653,)
            assert fields1247 is not None
            unwrapped_fields1248 = fields1247
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1249 = unwrapped_fields1248[0]
            self.pretty_relation_id(field1249)
            self.newline()
            field1250 = unwrapped_fields1248[1]
            self.pretty_abstraction_with_arity(field1250)
            field1251 = unwrapped_fields1248[2]
            if field1251 is not None:
                self.newline()
                assert field1251 is not None
                opt_val1252 = field1251
                self.pretty_attrs(opt_val1252)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1258 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1258 is not None:
            assert flat1258 is not None
            self.write(flat1258)
            return None
        else:
            _dollar_dollar = msg
            _t1654 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1254 = (_t1654, _dollar_dollar[0].value,)
            assert fields1254 is not None
            unwrapped_fields1255 = fields1254
            self.write("(")
            self.indent()
            field1256 = unwrapped_fields1255[0]
            self.pretty_bindings(field1256)
            self.newline()
            field1257 = unwrapped_fields1255[1]
            self.pretty_formula(field1257)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1265 = self._try_flat(msg, self.pretty_break)
        if flat1265 is not None:
            assert flat1265 is not None
            self.write(flat1265)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1655 = _dollar_dollar.attrs
            else:
                _t1655 = None
            fields1259 = (_dollar_dollar.name, _dollar_dollar.body, _t1655,)
            assert fields1259 is not None
            unwrapped_fields1260 = fields1259
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1261 = unwrapped_fields1260[0]
            self.pretty_relation_id(field1261)
            self.newline()
            field1262 = unwrapped_fields1260[1]
            self.pretty_abstraction(field1262)
            field1263 = unwrapped_fields1260[2]
            if field1263 is not None:
                self.newline()
                assert field1263 is not None
                opt_val1264 = field1263
                self.pretty_attrs(opt_val1264)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1273 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1273 is not None:
            assert flat1273 is not None
            self.write(flat1273)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1656 = _dollar_dollar.attrs
            else:
                _t1656 = None
            fields1266 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1656,)
            assert fields1266 is not None
            unwrapped_fields1267 = fields1266
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1268 = unwrapped_fields1267[0]
            self.pretty_monoid(field1268)
            self.newline()
            field1269 = unwrapped_fields1267[1]
            self.pretty_relation_id(field1269)
            self.newline()
            field1270 = unwrapped_fields1267[2]
            self.pretty_abstraction_with_arity(field1270)
            field1271 = unwrapped_fields1267[3]
            if field1271 is not None:
                self.newline()
                assert field1271 is not None
                opt_val1272 = field1271
                self.pretty_attrs(opt_val1272)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1282 = self._try_flat(msg, self.pretty_monoid)
        if flat1282 is not None:
            assert flat1282 is not None
            self.write(flat1282)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1657 = _dollar_dollar.or_monoid
            else:
                _t1657 = None
            deconstruct_result1280 = _t1657
            if deconstruct_result1280 is not None:
                assert deconstruct_result1280 is not None
                unwrapped1281 = deconstruct_result1280
                self.pretty_or_monoid(unwrapped1281)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1658 = _dollar_dollar.min_monoid
                else:
                    _t1658 = None
                deconstruct_result1278 = _t1658
                if deconstruct_result1278 is not None:
                    assert deconstruct_result1278 is not None
                    unwrapped1279 = deconstruct_result1278
                    self.pretty_min_monoid(unwrapped1279)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1659 = _dollar_dollar.max_monoid
                    else:
                        _t1659 = None
                    deconstruct_result1276 = _t1659
                    if deconstruct_result1276 is not None:
                        assert deconstruct_result1276 is not None
                        unwrapped1277 = deconstruct_result1276
                        self.pretty_max_monoid(unwrapped1277)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1660 = _dollar_dollar.sum_monoid
                        else:
                            _t1660 = None
                        deconstruct_result1274 = _t1660
                        if deconstruct_result1274 is not None:
                            assert deconstruct_result1274 is not None
                            unwrapped1275 = deconstruct_result1274
                            self.pretty_sum_monoid(unwrapped1275)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1283 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1286 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1286 is not None:
            assert flat1286 is not None
            self.write(flat1286)
            return None
        else:
            _dollar_dollar = msg
            fields1284 = _dollar_dollar.type
            assert fields1284 is not None
            unwrapped_fields1285 = fields1284
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1285)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1289 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1289 is not None:
            assert flat1289 is not None
            self.write(flat1289)
            return None
        else:
            _dollar_dollar = msg
            fields1287 = _dollar_dollar.type
            assert fields1287 is not None
            unwrapped_fields1288 = fields1287
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1288)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1292 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1292 is not None:
            assert flat1292 is not None
            self.write(flat1292)
            return None
        else:
            _dollar_dollar = msg
            fields1290 = _dollar_dollar.type
            assert fields1290 is not None
            unwrapped_fields1291 = fields1290
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1291)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1300 = self._try_flat(msg, self.pretty_monus_def)
        if flat1300 is not None:
            assert flat1300 is not None
            self.write(flat1300)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1661 = _dollar_dollar.attrs
            else:
                _t1661 = None
            fields1293 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1661,)
            assert fields1293 is not None
            unwrapped_fields1294 = fields1293
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1295 = unwrapped_fields1294[0]
            self.pretty_monoid(field1295)
            self.newline()
            field1296 = unwrapped_fields1294[1]
            self.pretty_relation_id(field1296)
            self.newline()
            field1297 = unwrapped_fields1294[2]
            self.pretty_abstraction_with_arity(field1297)
            field1298 = unwrapped_fields1294[3]
            if field1298 is not None:
                self.newline()
                assert field1298 is not None
                opt_val1299 = field1298
                self.pretty_attrs(opt_val1299)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1307 = self._try_flat(msg, self.pretty_constraint)
        if flat1307 is not None:
            assert flat1307 is not None
            self.write(flat1307)
            return None
        else:
            _dollar_dollar = msg
            fields1301 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1301 is not None
            unwrapped_fields1302 = fields1301
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1303 = unwrapped_fields1302[0]
            self.pretty_relation_id(field1303)
            self.newline()
            field1304 = unwrapped_fields1302[1]
            self.pretty_abstraction(field1304)
            self.newline()
            field1305 = unwrapped_fields1302[2]
            self.pretty_functional_dependency_keys(field1305)
            self.newline()
            field1306 = unwrapped_fields1302[3]
            self.pretty_functional_dependency_values(field1306)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1311 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1311 is not None:
            assert flat1311 is not None
            self.write(flat1311)
            return None
        else:
            fields1308 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1308) == 0:
                self.newline()
                for i1310, elem1309 in enumerate(fields1308):
                    if (i1310 > 0):
                        self.newline()
                    self.pretty_var(elem1309)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1315 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1315 is not None:
            assert flat1315 is not None
            self.write(flat1315)
            return None
        else:
            fields1312 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1312) == 0:
                self.newline()
                for i1314, elem1313 in enumerate(fields1312):
                    if (i1314 > 0):
                        self.newline()
                    self.pretty_var(elem1313)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1324 = self._try_flat(msg, self.pretty_data)
        if flat1324 is not None:
            assert flat1324 is not None
            self.write(flat1324)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1662 = _dollar_dollar.edb
            else:
                _t1662 = None
            deconstruct_result1322 = _t1662
            if deconstruct_result1322 is not None:
                assert deconstruct_result1322 is not None
                unwrapped1323 = deconstruct_result1322
                self.pretty_edb(unwrapped1323)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1663 = _dollar_dollar.betree_relation
                else:
                    _t1663 = None
                deconstruct_result1320 = _t1663
                if deconstruct_result1320 is not None:
                    assert deconstruct_result1320 is not None
                    unwrapped1321 = deconstruct_result1320
                    self.pretty_betree_relation(unwrapped1321)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1664 = _dollar_dollar.csv_data
                    else:
                        _t1664 = None
                    deconstruct_result1318 = _t1664
                    if deconstruct_result1318 is not None:
                        assert deconstruct_result1318 is not None
                        unwrapped1319 = deconstruct_result1318
                        self.pretty_csv_data(unwrapped1319)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1665 = _dollar_dollar.iceberg_data
                        else:
                            _t1665 = None
                        deconstruct_result1316 = _t1665
                        if deconstruct_result1316 is not None:
                            assert deconstruct_result1316 is not None
                            unwrapped1317 = deconstruct_result1316
                            self.pretty_iceberg_data(unwrapped1317)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1330 = self._try_flat(msg, self.pretty_edb)
        if flat1330 is not None:
            assert flat1330 is not None
            self.write(flat1330)
            return None
        else:
            _dollar_dollar = msg
            fields1325 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1325 is not None
            unwrapped_fields1326 = fields1325
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1327 = unwrapped_fields1326[0]
            self.pretty_relation_id(field1327)
            self.newline()
            field1328 = unwrapped_fields1326[1]
            self.pretty_edb_path(field1328)
            self.newline()
            field1329 = unwrapped_fields1326[2]
            self.pretty_edb_types(field1329)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1334 = self._try_flat(msg, self.pretty_edb_path)
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
                self.write(self.format_string_value(elem1332))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1338 = self._try_flat(msg, self.pretty_edb_types)
        if flat1338 is not None:
            assert flat1338 is not None
            self.write(flat1338)
            return None
        else:
            fields1335 = msg
            self.write("[")
            self.indent()
            for i1337, elem1336 in enumerate(fields1335):
                if (i1337 > 0):
                    self.newline()
                self.pretty_type(elem1336)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1343 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1343 is not None:
            assert flat1343 is not None
            self.write(flat1343)
            return None
        else:
            _dollar_dollar = msg
            fields1339 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1339 is not None
            unwrapped_fields1340 = fields1339
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1341 = unwrapped_fields1340[0]
            self.pretty_relation_id(field1341)
            self.newline()
            field1342 = unwrapped_fields1340[1]
            self.pretty_betree_info(field1342)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1349 = self._try_flat(msg, self.pretty_betree_info)
        if flat1349 is not None:
            assert flat1349 is not None
            self.write(flat1349)
            return None
        else:
            _dollar_dollar = msg
            _t1666 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1344 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1666,)
            assert fields1344 is not None
            unwrapped_fields1345 = fields1344
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1346 = unwrapped_fields1345[0]
            self.pretty_betree_info_key_types(field1346)
            self.newline()
            field1347 = unwrapped_fields1345[1]
            self.pretty_betree_info_value_types(field1347)
            self.newline()
            field1348 = unwrapped_fields1345[2]
            self.pretty_config_dict(field1348)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1353 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1353 is not None:
            assert flat1353 is not None
            self.write(flat1353)
            return None
        else:
            fields1350 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1350) == 0:
                self.newline()
                for i1352, elem1351 in enumerate(fields1350):
                    if (i1352 > 0):
                        self.newline()
                    self.pretty_type(elem1351)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1357 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1357 is not None:
            assert flat1357 is not None
            self.write(flat1357)
            return None
        else:
            fields1354 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1354) == 0:
                self.newline()
                for i1356, elem1355 in enumerate(fields1354):
                    if (i1356 > 0):
                        self.newline()
                    self.pretty_type(elem1355)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1364 = self._try_flat(msg, self.pretty_csv_data)
        if flat1364 is not None:
            assert flat1364 is not None
            self.write(flat1364)
            return None
        else:
            _dollar_dollar = msg
            fields1358 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1358 is not None
            unwrapped_fields1359 = fields1358
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1360 = unwrapped_fields1359[0]
            self.pretty_csvlocator(field1360)
            self.newline()
            field1361 = unwrapped_fields1359[1]
            self.pretty_csv_config(field1361)
            self.newline()
            field1362 = unwrapped_fields1359[2]
            self.pretty_gnf_columns(field1362)
            self.newline()
            field1363 = unwrapped_fields1359[3]
            self.pretty_csv_asof(field1363)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1371 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1371 is not None:
            assert flat1371 is not None
            self.write(flat1371)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1667 = _dollar_dollar.paths
            else:
                _t1667 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1668 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1668 = None
            fields1365 = (_t1667, _t1668,)
            assert fields1365 is not None
            unwrapped_fields1366 = fields1365
            self.write("(csv_locator")
            self.indent_sexp()
            field1367 = unwrapped_fields1366[0]
            if field1367 is not None:
                self.newline()
                assert field1367 is not None
                opt_val1368 = field1367
                self.pretty_csv_locator_paths(opt_val1368)
            field1369 = unwrapped_fields1366[1]
            if field1369 is not None:
                self.newline()
                assert field1369 is not None
                opt_val1370 = field1369
                self.pretty_csv_locator_inline_data(opt_val1370)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1375 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1375 is not None:
            assert flat1375 is not None
            self.write(flat1375)
            return None
        else:
            fields1372 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1372) == 0:
                self.newline()
                for i1374, elem1373 in enumerate(fields1372):
                    if (i1374 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1373))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1377 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1377 is not None:
            assert flat1377 is not None
            self.write(flat1377)
            return None
        else:
            fields1376 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1376))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1380 = self._try_flat(msg, self.pretty_csv_config)
        if flat1380 is not None:
            assert flat1380 is not None
            self.write(flat1380)
            return None
        else:
            _dollar_dollar = msg
            _t1669 = self.deconstruct_csv_config(_dollar_dollar)
            fields1378 = _t1669
            assert fields1378 is not None
            unwrapped_fields1379 = fields1378
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1379)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1384 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1384 is not None:
            assert flat1384 is not None
            self.write(flat1384)
            return None
        else:
            fields1381 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1381) == 0:
                self.newline()
                for i1383, elem1382 in enumerate(fields1381):
                    if (i1383 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1382)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1393 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1393 is not None:
            assert flat1393 is not None
            self.write(flat1393)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1670 = _dollar_dollar.target_id
            else:
                _t1670 = None
            fields1385 = (_dollar_dollar.column_path, _t1670, _dollar_dollar.types,)
            assert fields1385 is not None
            unwrapped_fields1386 = fields1385
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1387 = unwrapped_fields1386[0]
            self.pretty_gnf_column_path(field1387)
            field1388 = unwrapped_fields1386[1]
            if field1388 is not None:
                self.newline()
                assert field1388 is not None
                opt_val1389 = field1388
                self.pretty_relation_id(opt_val1389)
            self.newline()
            self.write("[")
            field1390 = unwrapped_fields1386[2]
            for i1392, elem1391 in enumerate(field1390):
                if (i1392 > 0):
                    self.newline()
                self.pretty_type(elem1391)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1400 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1400 is not None:
            assert flat1400 is not None
            self.write(flat1400)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1671 = _dollar_dollar[0]
            else:
                _t1671 = None
            deconstruct_result1398 = _t1671
            if deconstruct_result1398 is not None:
                assert deconstruct_result1398 is not None
                unwrapped1399 = deconstruct_result1398
                self.write(self.format_string_value(unwrapped1399))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1672 = _dollar_dollar
                else:
                    _t1672 = None
                deconstruct_result1394 = _t1672
                if deconstruct_result1394 is not None:
                    assert deconstruct_result1394 is not None
                    unwrapped1395 = deconstruct_result1394
                    self.write("[")
                    self.indent()
                    for i1397, elem1396 in enumerate(unwrapped1395):
                        if (i1397 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1396))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1402 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1402 is not None:
            assert flat1402 is not None
            self.write(flat1402)
            return None
        else:
            fields1401 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1401))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1410 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1410 is not None:
            assert flat1410 is not None
            self.write(flat1410)
            return None
        else:
            _dollar_dollar = msg
            _t1673 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1403 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1673,)
            assert fields1403 is not None
            unwrapped_fields1404 = fields1403
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1405 = unwrapped_fields1404[0]
            self.pretty_iceberg_locator(field1405)
            self.newline()
            field1406 = unwrapped_fields1404[1]
            self.pretty_iceberg_catalog_config(field1406)
            self.newline()
            field1407 = unwrapped_fields1404[2]
            self.pretty_gnf_columns(field1407)
            field1408 = unwrapped_fields1404[3]
            if field1408 is not None:
                self.newline()
                assert field1408 is not None
                opt_val1409 = field1408
                self.pretty_iceberg_to_snapshot(opt_val1409)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1418 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1418 is not None:
            assert flat1418 is not None
            self.write(flat1418)
            return None
        else:
            _dollar_dollar = msg
            fields1411 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1411 is not None
            unwrapped_fields1412 = fields1411
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("table_name")
            self.newline()
            field1413 = unwrapped_fields1412[0]
            self.write(self.format_string_value(field1413))
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("namespace")
            field1414 = unwrapped_fields1412[1]
            if not len(field1414) == 0:
                self.newline()
                for i1416, elem1415 in enumerate(field1414):
                    if (i1416 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1415))
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("warehouse")
            self.newline()
            field1417 = unwrapped_fields1412[2]
            self.write(self.format_string_value(field1417))
            self.dedent()
            self.write(")")
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1430 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1430 is not None:
            assert flat1430 is not None
            self.write(flat1430)
            return None
        else:
            _dollar_dollar = msg
            _t1674 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1419 = (_dollar_dollar.catalog_uri, _t1674, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1419 is not None
            unwrapped_fields1420 = fields1419
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("catalog_uri")
            self.newline()
            field1421 = unwrapped_fields1420[0]
            self.write(self.format_string_value(field1421))
            self.dedent()
            self.write(")")
            field1422 = unwrapped_fields1420[1]
            if field1422 is not None:
                self.newline()
                assert field1422 is not None
                opt_val1423 = field1422
                self.pretty_iceberg_catalog_config_scope(opt_val1423)
            self.newline()
            self.write("(")
            self.newline()
            self.write("properties")
            field1424 = unwrapped_fields1420[2]
            if not len(field1424) == 0:
                self.newline()
                for i1426, elem1425 in enumerate(field1424):
                    if (i1426 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1425)
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("auth_properties")
            field1427 = unwrapped_fields1420[3]
            if not len(field1427) == 0:
                self.newline()
                for i1429, elem1428 in enumerate(field1427):
                    if (i1429 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1428)
            self.dedent()
            self.write(")")
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1432 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1432 is not None:
            assert flat1432 is not None
            self.write(flat1432)
            return None
        else:
            fields1431 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1431))
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1437 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1437 is not None:
            assert flat1437 is not None
            self.write(flat1437)
            return None
        else:
            _dollar_dollar = msg
            fields1433 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1433 is not None
            unwrapped_fields1434 = fields1433
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1435 = unwrapped_fields1434[0]
            self.write(self.format_string_value(field1435))
            self.newline()
            field1436 = unwrapped_fields1434[1]
            self.write(self.format_string_value(field1436))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1439 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1439 is not None:
            assert flat1439 is not None
            self.write(flat1439)
            return None
        else:
            fields1438 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1438))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1442 = self._try_flat(msg, self.pretty_undefine)
        if flat1442 is not None:
            assert flat1442 is not None
            self.write(flat1442)
            return None
        else:
            _dollar_dollar = msg
            fields1440 = _dollar_dollar.fragment_id
            assert fields1440 is not None
            unwrapped_fields1441 = fields1440
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1441)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1447 = self._try_flat(msg, self.pretty_context)
        if flat1447 is not None:
            assert flat1447 is not None
            self.write(flat1447)
            return None
        else:
            _dollar_dollar = msg
            fields1443 = _dollar_dollar.relations
            assert fields1443 is not None
            unwrapped_fields1444 = fields1443
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1444) == 0:
                self.newline()
                for i1446, elem1445 in enumerate(unwrapped_fields1444):
                    if (i1446 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1445)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1452 = self._try_flat(msg, self.pretty_snapshot)
        if flat1452 is not None:
            assert flat1452 is not None
            self.write(flat1452)
            return None
        else:
            _dollar_dollar = msg
            fields1448 = _dollar_dollar.mappings
            assert fields1448 is not None
            unwrapped_fields1449 = fields1448
            self.write("(snapshot")
            self.indent_sexp()
            if not len(unwrapped_fields1449) == 0:
                self.newline()
                for i1451, elem1450 in enumerate(unwrapped_fields1449):
                    if (i1451 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1450)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1457 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1457 is not None:
            assert flat1457 is not None
            self.write(flat1457)
            return None
        else:
            _dollar_dollar = msg
            fields1453 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1453 is not None
            unwrapped_fields1454 = fields1453
            field1455 = unwrapped_fields1454[0]
            self.pretty_edb_path(field1455)
            self.write(" ")
            field1456 = unwrapped_fields1454[1]
            self.pretty_relation_id(field1456)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1461 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1461 is not None:
            assert flat1461 is not None
            self.write(flat1461)
            return None
        else:
            fields1458 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1458) == 0:
                self.newline()
                for i1460, elem1459 in enumerate(fields1458):
                    if (i1460 > 0):
                        self.newline()
                    self.pretty_read(elem1459)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1472 = self._try_flat(msg, self.pretty_read)
        if flat1472 is not None:
            assert flat1472 is not None
            self.write(flat1472)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1675 = _dollar_dollar.demand
            else:
                _t1675 = None
            deconstruct_result1470 = _t1675
            if deconstruct_result1470 is not None:
                assert deconstruct_result1470 is not None
                unwrapped1471 = deconstruct_result1470
                self.pretty_demand(unwrapped1471)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1676 = _dollar_dollar.output
                else:
                    _t1676 = None
                deconstruct_result1468 = _t1676
                if deconstruct_result1468 is not None:
                    assert deconstruct_result1468 is not None
                    unwrapped1469 = deconstruct_result1468
                    self.pretty_output(unwrapped1469)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1677 = _dollar_dollar.what_if
                    else:
                        _t1677 = None
                    deconstruct_result1466 = _t1677
                    if deconstruct_result1466 is not None:
                        assert deconstruct_result1466 is not None
                        unwrapped1467 = deconstruct_result1466
                        self.pretty_what_if(unwrapped1467)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1678 = _dollar_dollar.abort
                        else:
                            _t1678 = None
                        deconstruct_result1464 = _t1678
                        if deconstruct_result1464 is not None:
                            assert deconstruct_result1464 is not None
                            unwrapped1465 = deconstruct_result1464
                            self.pretty_abort(unwrapped1465)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1679 = _dollar_dollar.export
                            else:
                                _t1679 = None
                            deconstruct_result1462 = _t1679
                            if deconstruct_result1462 is not None:
                                assert deconstruct_result1462 is not None
                                unwrapped1463 = deconstruct_result1462
                                self.pretty_export(unwrapped1463)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1475 = self._try_flat(msg, self.pretty_demand)
        if flat1475 is not None:
            assert flat1475 is not None
            self.write(flat1475)
            return None
        else:
            _dollar_dollar = msg
            fields1473 = _dollar_dollar.relation_id
            assert fields1473 is not None
            unwrapped_fields1474 = fields1473
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1474)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1480 = self._try_flat(msg, self.pretty_output)
        if flat1480 is not None:
            assert flat1480 is not None
            self.write(flat1480)
            return None
        else:
            _dollar_dollar = msg
            fields1476 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1476 is not None
            unwrapped_fields1477 = fields1476
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1478 = unwrapped_fields1477[0]
            self.pretty_name(field1478)
            self.newline()
            field1479 = unwrapped_fields1477[1]
            self.pretty_relation_id(field1479)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1485 = self._try_flat(msg, self.pretty_what_if)
        if flat1485 is not None:
            assert flat1485 is not None
            self.write(flat1485)
            return None
        else:
            _dollar_dollar = msg
            fields1481 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1481 is not None
            unwrapped_fields1482 = fields1481
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1483 = unwrapped_fields1482[0]
            self.pretty_name(field1483)
            self.newline()
            field1484 = unwrapped_fields1482[1]
            self.pretty_epoch(field1484)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1491 = self._try_flat(msg, self.pretty_abort)
        if flat1491 is not None:
            assert flat1491 is not None
            self.write(flat1491)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1680 = _dollar_dollar.name
            else:
                _t1680 = None
            fields1486 = (_t1680, _dollar_dollar.relation_id,)
            assert fields1486 is not None
            unwrapped_fields1487 = fields1486
            self.write("(abort")
            self.indent_sexp()
            field1488 = unwrapped_fields1487[0]
            if field1488 is not None:
                self.newline()
                assert field1488 is not None
                opt_val1489 = field1488
                self.pretty_name(opt_val1489)
            self.newline()
            field1490 = unwrapped_fields1487[1]
            self.pretty_relation_id(field1490)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1496 = self._try_flat(msg, self.pretty_export)
        if flat1496 is not None:
            assert flat1496 is not None
            self.write(flat1496)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1681 = _dollar_dollar.csv_config
            else:
                _t1681 = None
            deconstruct_result1494 = _t1681
            if deconstruct_result1494 is not None:
                assert deconstruct_result1494 is not None
                unwrapped1495 = deconstruct_result1494
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1495)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1682 = _dollar_dollar.iceberg_config
                else:
                    _t1682 = None
                deconstruct_result1492 = _t1682
                if deconstruct_result1492 is not None:
                    assert deconstruct_result1492 is not None
                    unwrapped1493 = deconstruct_result1492
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1493)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1507 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1507 is not None:
            assert flat1507 is not None
            self.write(flat1507)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1683 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1683 = None
            deconstruct_result1502 = _t1683
            if deconstruct_result1502 is not None:
                assert deconstruct_result1502 is not None
                unwrapped1503 = deconstruct_result1502
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1504 = unwrapped1503[0]
                self.pretty_export_csv_path(field1504)
                self.newline()
                field1505 = unwrapped1503[1]
                self.pretty_export_csv_source(field1505)
                self.newline()
                field1506 = unwrapped1503[2]
                self.pretty_csv_config(field1506)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1685 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1684 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1685,)
                else:
                    _t1684 = None
                deconstruct_result1497 = _t1684
                if deconstruct_result1497 is not None:
                    assert deconstruct_result1497 is not None
                    unwrapped1498 = deconstruct_result1497
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1499 = unwrapped1498[0]
                    self.pretty_export_csv_path(field1499)
                    self.newline()
                    field1500 = unwrapped1498[1]
                    self.pretty_export_csv_columns_list(field1500)
                    self.newline()
                    field1501 = unwrapped1498[2]
                    self.pretty_config_dict(field1501)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1509 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1509 is not None:
            assert flat1509 is not None
            self.write(flat1509)
            return None
        else:
            fields1508 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1508))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1516 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1516 is not None:
            assert flat1516 is not None
            self.write(flat1516)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1686 = _dollar_dollar.gnf_columns.columns
            else:
                _t1686 = None
            deconstruct_result1512 = _t1686
            if deconstruct_result1512 is not None:
                assert deconstruct_result1512 is not None
                unwrapped1513 = deconstruct_result1512
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1513) == 0:
                    self.newline()
                    for i1515, elem1514 in enumerate(unwrapped1513):
                        if (i1515 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1514)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1687 = _dollar_dollar.table_def
                else:
                    _t1687 = None
                deconstruct_result1510 = _t1687
                if deconstruct_result1510 is not None:
                    assert deconstruct_result1510 is not None
                    unwrapped1511 = deconstruct_result1510
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1511)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1521 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1521 is not None:
            assert flat1521 is not None
            self.write(flat1521)
            return None
        else:
            _dollar_dollar = msg
            fields1517 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1517 is not None
            unwrapped_fields1518 = fields1517
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1519 = unwrapped_fields1518[0]
            self.write(self.format_string_value(field1519))
            self.newline()
            field1520 = unwrapped_fields1518[1]
            self.pretty_relation_id(field1520)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1525 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1525 is not None:
            assert flat1525 is not None
            self.write(flat1525)
            return None
        else:
            fields1522 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1522) == 0:
                self.newline()
                for i1524, elem1523 in enumerate(fields1522):
                    if (i1524 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1523)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1536 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1536 is not None:
            assert flat1536 is not None
            self.write(flat1536)
            return None
        else:
            _dollar_dollar = msg
            _t1688 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1526 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, sorted(_dollar_dollar.table_properties.items()), _t1688,)
            assert fields1526 is not None
            unwrapped_fields1527 = fields1526
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1528 = unwrapped_fields1527[0]
            self.pretty_iceberg_locator(field1528)
            self.newline()
            field1529 = unwrapped_fields1527[1]
            self.pretty_iceberg_catalog_config(field1529)
            self.newline()
            field1530 = unwrapped_fields1527[2]
            self.pretty_export_iceberg_columns(field1530)
            self.newline()
            self.write("(")
            self.newline()
            self.write("table_properties")
            field1531 = unwrapped_fields1527[3]
            if not len(field1531) == 0:
                self.newline()
                for i1533, elem1532 in enumerate(field1531):
                    if (i1533 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1532)
            self.dedent()
            self.write(")")
            field1534 = unwrapped_fields1527[4]
            if field1534 is not None:
                self.newline()
                assert field1534 is not None
                opt_val1535 = field1534
                self.pretty_config_dict(opt_val1535)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_columns(self, msg: transactions_pb2.ExportIcebergColumns):
        flat1543 = self._try_flat(msg, self.pretty_export_iceberg_columns)
        if flat1543 is not None:
            assert flat1543 is not None
            self.write(flat1543)
            return None
        else:
            _dollar_dollar = msg
            fields1537 = (_dollar_dollar.source_table_def, _dollar_dollar.target_columns,)
            assert fields1537 is not None
            unwrapped_fields1538 = fields1537
            self.write("(columns")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("source_table_def")
            self.newline()
            field1539 = unwrapped_fields1538[0]
            self.pretty_relation_id(field1539)
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("target_columns")
            field1540 = unwrapped_fields1538[1]
            if not len(field1540) == 0:
                self.newline()
                for i1542, elem1541 in enumerate(field1540):
                    if (i1542 > 0):
                        self.newline()
                    self.pretty_export_iceberg_column(elem1541)
            self.dedent()
            self.write(")")
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_column(self, msg: transactions_pb2.ExportIcebergColumn):
        flat1549 = self._try_flat(msg, self.pretty_export_iceberg_column)
        if flat1549 is not None:
            assert flat1549 is not None
            self.write(flat1549)
            return None
        else:
            _dollar_dollar = msg
            fields1544 = (_dollar_dollar.name, _dollar_dollar.type, _dollar_dollar.nullable,)
            assert fields1544 is not None
            unwrapped_fields1545 = fields1544
            self.write("(iceberg_column")
            self.indent_sexp()
            self.newline()
            field1546 = unwrapped_fields1545[0]
            self.write(self.format_string_value(field1546))
            self.newline()
            field1547 = unwrapped_fields1545[1]
            self.pretty_type(field1547)
            self.newline()
            field1548 = unwrapped_fields1545[2]
            self.pretty_boolean_value(field1548)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1733 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1733)
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
