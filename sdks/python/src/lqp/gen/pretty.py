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
        _t1679 = logic_pb2.Value(int32_value=v)
        return _t1679

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1680 = logic_pb2.Value(int_value=v)
        return _t1680

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1681 = logic_pb2.Value(float_value=v)
        return _t1681

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1682 = logic_pb2.Value(string_value=v)
        return _t1682

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1683 = logic_pb2.Value(boolean_value=v)
        return _t1683

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1684 = logic_pb2.Value(uint128_value=v)
        return _t1684

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1685 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1685,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1686 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1686,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1687 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1687,))
        _t1688 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1688,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1689 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1689,))
        _t1690 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1690,))
        if msg.new_line != "":
            _t1691 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1691,))
        _t1692 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1692,))
        _t1693 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1693,))
        _t1694 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1694,))
        if msg.comment != "":
            _t1695 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1695,))
        for missing_string in msg.missing_strings:
            _t1696 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1696,))
        _t1697 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1697,))
        _t1698 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1698,))
        _t1699 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1699,))
        if msg.partition_size_mb != 0:
            _t1700 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1700,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1701 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1701,))
        _t1702 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1702,))
        _t1703 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1703,))
        _t1704 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1704,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1705 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1705,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1706 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1706,))
        _t1707 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1707,))
        _t1708 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1708,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1709 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1709,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1710 = self._make_value_string(msg.compression)
            result.append(("compression", _t1710,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1711 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1711,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1712 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1712,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1713 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1713,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1714 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1714,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1715 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1715,))
        return sorted(result)

    def deconstruct_iceberg_catalog_config_scope_optional(self, msg: logic_pb2.IcebergCatalogConfig) -> str | None:
        assert msg.scope is not None
        if msg.scope != "":
            assert msg.scope is not None
            return msg.scope
        else:
            _t1716 = None
        return None

    def deconstruct_iceberg_data_to_snapshot_optional(self, msg: logic_pb2.IcebergData) -> str | None:
        assert msg.to_snapshot is not None
        if msg.to_snapshot != "":
            assert msg.to_snapshot is not None
            return msg.to_snapshot
        else:
            _t1717 = None
        return None

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1718 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1718,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1719 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1719,))
        if msg.compression != "":
            _t1720 = self._make_value_string(msg.compression)
            result.append(("compression", _t1720,))
        if len(result) == 0:
            return None
        else:
            _t1721 = None
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
            _t1722 = None
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
        flat779 = self._try_flat(msg, self.pretty_transaction)
        if flat779 is not None:
            assert flat779 is not None
            self.write(flat779)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1540 = _dollar_dollar.configure
            else:
                _t1540 = None
            if _dollar_dollar.HasField("sync"):
                _t1541 = _dollar_dollar.sync
            else:
                _t1541 = None
            fields770 = (_t1540, _t1541, _dollar_dollar.epochs,)
            assert fields770 is not None
            unwrapped_fields771 = fields770
            self.write("(transaction")
            self.indent_sexp()
            field772 = unwrapped_fields771[0]
            if field772 is not None:
                self.newline()
                assert field772 is not None
                opt_val773 = field772
                self.pretty_configure(opt_val773)
            field774 = unwrapped_fields771[1]
            if field774 is not None:
                self.newline()
                assert field774 is not None
                opt_val775 = field774
                self.pretty_sync(opt_val775)
            field776 = unwrapped_fields771[2]
            if not len(field776) == 0:
                self.newline()
                for i778, elem777 in enumerate(field776):
                    if (i778 > 0):
                        self.newline()
                    self.pretty_epoch(elem777)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat782 = self._try_flat(msg, self.pretty_configure)
        if flat782 is not None:
            assert flat782 is not None
            self.write(flat782)
            return None
        else:
            _dollar_dollar = msg
            _t1542 = self.deconstruct_configure(_dollar_dollar)
            fields780 = _t1542
            assert fields780 is not None
            unwrapped_fields781 = fields780
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields781)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat786 = self._try_flat(msg, self.pretty_config_dict)
        if flat786 is not None:
            assert flat786 is not None
            self.write(flat786)
            return None
        else:
            fields783 = msg
            self.write("{")
            self.indent()
            if not len(fields783) == 0:
                self.newline()
                for i785, elem784 in enumerate(fields783):
                    if (i785 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem784)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat791 = self._try_flat(msg, self.pretty_config_key_value)
        if flat791 is not None:
            assert flat791 is not None
            self.write(flat791)
            return None
        else:
            _dollar_dollar = msg
            fields787 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields787 is not None
            unwrapped_fields788 = fields787
            self.write(":")
            field789 = unwrapped_fields788[0]
            self.write(field789)
            self.write(" ")
            field790 = unwrapped_fields788[1]
            self.pretty_raw_value(field790)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat817 = self._try_flat(msg, self.pretty_raw_value)
        if flat817 is not None:
            assert flat817 is not None
            self.write(flat817)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1543 = _dollar_dollar.date_value
            else:
                _t1543 = None
            deconstruct_result815 = _t1543
            if deconstruct_result815 is not None:
                assert deconstruct_result815 is not None
                unwrapped816 = deconstruct_result815
                self.pretty_raw_date(unwrapped816)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1544 = _dollar_dollar.datetime_value
                else:
                    _t1544 = None
                deconstruct_result813 = _t1544
                if deconstruct_result813 is not None:
                    assert deconstruct_result813 is not None
                    unwrapped814 = deconstruct_result813
                    self.pretty_raw_datetime(unwrapped814)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1545 = _dollar_dollar.string_value
                    else:
                        _t1545 = None
                    deconstruct_result811 = _t1545
                    if deconstruct_result811 is not None:
                        assert deconstruct_result811 is not None
                        unwrapped812 = deconstruct_result811
                        self.write(self.format_string_value(unwrapped812))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1546 = _dollar_dollar.int32_value
                        else:
                            _t1546 = None
                        deconstruct_result809 = _t1546
                        if deconstruct_result809 is not None:
                            assert deconstruct_result809 is not None
                            unwrapped810 = deconstruct_result809
                            self.write((str(unwrapped810) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1547 = _dollar_dollar.int_value
                            else:
                                _t1547 = None
                            deconstruct_result807 = _t1547
                            if deconstruct_result807 is not None:
                                assert deconstruct_result807 is not None
                                unwrapped808 = deconstruct_result807
                                self.write(str(unwrapped808))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1548 = _dollar_dollar.float32_value
                                else:
                                    _t1548 = None
                                deconstruct_result805 = _t1548
                                if deconstruct_result805 is not None:
                                    assert deconstruct_result805 is not None
                                    unwrapped806 = deconstruct_result805
                                    self.write(self.format_float32_literal(unwrapped806))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1549 = _dollar_dollar.float_value
                                    else:
                                        _t1549 = None
                                    deconstruct_result803 = _t1549
                                    if deconstruct_result803 is not None:
                                        assert deconstruct_result803 is not None
                                        unwrapped804 = deconstruct_result803
                                        self.write(str(unwrapped804))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1550 = _dollar_dollar.uint32_value
                                        else:
                                            _t1550 = None
                                        deconstruct_result801 = _t1550
                                        if deconstruct_result801 is not None:
                                            assert deconstruct_result801 is not None
                                            unwrapped802 = deconstruct_result801
                                            self.write((str(unwrapped802) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1551 = _dollar_dollar.uint128_value
                                            else:
                                                _t1551 = None
                                            deconstruct_result799 = _t1551
                                            if deconstruct_result799 is not None:
                                                assert deconstruct_result799 is not None
                                                unwrapped800 = deconstruct_result799
                                                self.write(self.format_uint128(unwrapped800))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1552 = _dollar_dollar.int128_value
                                                else:
                                                    _t1552 = None
                                                deconstruct_result797 = _t1552
                                                if deconstruct_result797 is not None:
                                                    assert deconstruct_result797 is not None
                                                    unwrapped798 = deconstruct_result797
                                                    self.write(self.format_int128(unwrapped798))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1553 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1553 = None
                                                    deconstruct_result795 = _t1553
                                                    if deconstruct_result795 is not None:
                                                        assert deconstruct_result795 is not None
                                                        unwrapped796 = deconstruct_result795
                                                        self.write(self.format_decimal(unwrapped796))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1554 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1554 = None
                                                        deconstruct_result793 = _t1554
                                                        if deconstruct_result793 is not None:
                                                            assert deconstruct_result793 is not None
                                                            unwrapped794 = deconstruct_result793
                                                            self.pretty_boolean_value(unwrapped794)
                                                        else:
                                                            fields792 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat823 = self._try_flat(msg, self.pretty_raw_date)
        if flat823 is not None:
            assert flat823 is not None
            self.write(flat823)
            return None
        else:
            _dollar_dollar = msg
            fields818 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields818 is not None
            unwrapped_fields819 = fields818
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field820 = unwrapped_fields819[0]
            self.write(str(field820))
            self.newline()
            field821 = unwrapped_fields819[1]
            self.write(str(field821))
            self.newline()
            field822 = unwrapped_fields819[2]
            self.write(str(field822))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat834 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat834 is not None:
            assert flat834 is not None
            self.write(flat834)
            return None
        else:
            _dollar_dollar = msg
            fields824 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields824 is not None
            unwrapped_fields825 = fields824
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field826 = unwrapped_fields825[0]
            self.write(str(field826))
            self.newline()
            field827 = unwrapped_fields825[1]
            self.write(str(field827))
            self.newline()
            field828 = unwrapped_fields825[2]
            self.write(str(field828))
            self.newline()
            field829 = unwrapped_fields825[3]
            self.write(str(field829))
            self.newline()
            field830 = unwrapped_fields825[4]
            self.write(str(field830))
            self.newline()
            field831 = unwrapped_fields825[5]
            self.write(str(field831))
            field832 = unwrapped_fields825[6]
            if field832 is not None:
                self.newline()
                assert field832 is not None
                opt_val833 = field832
                self.write(str(opt_val833))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1555 = ()
        else:
            _t1555 = None
        deconstruct_result837 = _t1555
        if deconstruct_result837 is not None:
            assert deconstruct_result837 is not None
            unwrapped838 = deconstruct_result837
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1556 = ()
            else:
                _t1556 = None
            deconstruct_result835 = _t1556
            if deconstruct_result835 is not None:
                assert deconstruct_result835 is not None
                unwrapped836 = deconstruct_result835
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat843 = self._try_flat(msg, self.pretty_sync)
        if flat843 is not None:
            assert flat843 is not None
            self.write(flat843)
            return None
        else:
            _dollar_dollar = msg
            fields839 = _dollar_dollar.fragments
            assert fields839 is not None
            unwrapped_fields840 = fields839
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields840) == 0:
                self.newline()
                for i842, elem841 in enumerate(unwrapped_fields840):
                    if (i842 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem841)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat846 = self._try_flat(msg, self.pretty_fragment_id)
        if flat846 is not None:
            assert flat846 is not None
            self.write(flat846)
            return None
        else:
            _dollar_dollar = msg
            fields844 = self.fragment_id_to_string(_dollar_dollar)
            assert fields844 is not None
            unwrapped_fields845 = fields844
            self.write(":")
            self.write(unwrapped_fields845)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat853 = self._try_flat(msg, self.pretty_epoch)
        if flat853 is not None:
            assert flat853 is not None
            self.write(flat853)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1557 = _dollar_dollar.writes
            else:
                _t1557 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1558 = _dollar_dollar.reads
            else:
                _t1558 = None
            fields847 = (_t1557, _t1558,)
            assert fields847 is not None
            unwrapped_fields848 = fields847
            self.write("(epoch")
            self.indent_sexp()
            field849 = unwrapped_fields848[0]
            if field849 is not None:
                self.newline()
                assert field849 is not None
                opt_val850 = field849
                self.pretty_epoch_writes(opt_val850)
            field851 = unwrapped_fields848[1]
            if field851 is not None:
                self.newline()
                assert field851 is not None
                opt_val852 = field851
                self.pretty_epoch_reads(opt_val852)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat857 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat857 is not None:
            assert flat857 is not None
            self.write(flat857)
            return None
        else:
            fields854 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields854) == 0:
                self.newline()
                for i856, elem855 in enumerate(fields854):
                    if (i856 > 0):
                        self.newline()
                    self.pretty_write(elem855)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat866 = self._try_flat(msg, self.pretty_write)
        if flat866 is not None:
            assert flat866 is not None
            self.write(flat866)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1559 = _dollar_dollar.define
            else:
                _t1559 = None
            deconstruct_result864 = _t1559
            if deconstruct_result864 is not None:
                assert deconstruct_result864 is not None
                unwrapped865 = deconstruct_result864
                self.pretty_define(unwrapped865)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1560 = _dollar_dollar.undefine
                else:
                    _t1560 = None
                deconstruct_result862 = _t1560
                if deconstruct_result862 is not None:
                    assert deconstruct_result862 is not None
                    unwrapped863 = deconstruct_result862
                    self.pretty_undefine(unwrapped863)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1561 = _dollar_dollar.context
                    else:
                        _t1561 = None
                    deconstruct_result860 = _t1561
                    if deconstruct_result860 is not None:
                        assert deconstruct_result860 is not None
                        unwrapped861 = deconstruct_result860
                        self.pretty_context(unwrapped861)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1562 = _dollar_dollar.snapshot
                        else:
                            _t1562 = None
                        deconstruct_result858 = _t1562
                        if deconstruct_result858 is not None:
                            assert deconstruct_result858 is not None
                            unwrapped859 = deconstruct_result858
                            self.pretty_snapshot(unwrapped859)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat869 = self._try_flat(msg, self.pretty_define)
        if flat869 is not None:
            assert flat869 is not None
            self.write(flat869)
            return None
        else:
            _dollar_dollar = msg
            fields867 = _dollar_dollar.fragment
            assert fields867 is not None
            unwrapped_fields868 = fields867
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields868)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat876 = self._try_flat(msg, self.pretty_fragment)
        if flat876 is not None:
            assert flat876 is not None
            self.write(flat876)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields870 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields870 is not None
            unwrapped_fields871 = fields870
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field872 = unwrapped_fields871[0]
            self.pretty_new_fragment_id(field872)
            field873 = unwrapped_fields871[1]
            if not len(field873) == 0:
                self.newline()
                for i875, elem874 in enumerate(field873):
                    if (i875 > 0):
                        self.newline()
                    self.pretty_declaration(elem874)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat878 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat878 is not None:
            assert flat878 is not None
            self.write(flat878)
            return None
        else:
            fields877 = msg
            self.pretty_fragment_id(fields877)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat887 = self._try_flat(msg, self.pretty_declaration)
        if flat887 is not None:
            assert flat887 is not None
            self.write(flat887)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1563 = getattr(_dollar_dollar, 'def')
            else:
                _t1563 = None
            deconstruct_result885 = _t1563
            if deconstruct_result885 is not None:
                assert deconstruct_result885 is not None
                unwrapped886 = deconstruct_result885
                self.pretty_def(unwrapped886)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1564 = _dollar_dollar.algorithm
                else:
                    _t1564 = None
                deconstruct_result883 = _t1564
                if deconstruct_result883 is not None:
                    assert deconstruct_result883 is not None
                    unwrapped884 = deconstruct_result883
                    self.pretty_algorithm(unwrapped884)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1565 = _dollar_dollar.constraint
                    else:
                        _t1565 = None
                    deconstruct_result881 = _t1565
                    if deconstruct_result881 is not None:
                        assert deconstruct_result881 is not None
                        unwrapped882 = deconstruct_result881
                        self.pretty_constraint(unwrapped882)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1566 = _dollar_dollar.data
                        else:
                            _t1566 = None
                        deconstruct_result879 = _t1566
                        if deconstruct_result879 is not None:
                            assert deconstruct_result879 is not None
                            unwrapped880 = deconstruct_result879
                            self.pretty_data(unwrapped880)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat894 = self._try_flat(msg, self.pretty_def)
        if flat894 is not None:
            assert flat894 is not None
            self.write(flat894)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1567 = _dollar_dollar.attrs
            else:
                _t1567 = None
            fields888 = (_dollar_dollar.name, _dollar_dollar.body, _t1567,)
            assert fields888 is not None
            unwrapped_fields889 = fields888
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field890 = unwrapped_fields889[0]
            self.pretty_relation_id(field890)
            self.newline()
            field891 = unwrapped_fields889[1]
            self.pretty_abstraction(field891)
            field892 = unwrapped_fields889[2]
            if field892 is not None:
                self.newline()
                assert field892 is not None
                opt_val893 = field892
                self.pretty_attrs(opt_val893)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat899 = self._try_flat(msg, self.pretty_relation_id)
        if flat899 is not None:
            assert flat899 is not None
            self.write(flat899)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1569 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1568 = _t1569
            else:
                _t1568 = None
            deconstruct_result897 = _t1568
            if deconstruct_result897 is not None:
                assert deconstruct_result897 is not None
                unwrapped898 = deconstruct_result897
                self.write(":")
                self.write(unwrapped898)
            else:
                _dollar_dollar = msg
                _t1570 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result895 = _t1570
                if deconstruct_result895 is not None:
                    assert deconstruct_result895 is not None
                    unwrapped896 = deconstruct_result895
                    self.write(self.format_uint128(unwrapped896))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat904 = self._try_flat(msg, self.pretty_abstraction)
        if flat904 is not None:
            assert flat904 is not None
            self.write(flat904)
            return None
        else:
            _dollar_dollar = msg
            _t1571 = self.deconstruct_bindings(_dollar_dollar)
            fields900 = (_t1571, _dollar_dollar.value,)
            assert fields900 is not None
            unwrapped_fields901 = fields900
            self.write("(")
            self.indent()
            field902 = unwrapped_fields901[0]
            self.pretty_bindings(field902)
            self.newline()
            field903 = unwrapped_fields901[1]
            self.pretty_formula(field903)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat912 = self._try_flat(msg, self.pretty_bindings)
        if flat912 is not None:
            assert flat912 is not None
            self.write(flat912)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1572 = _dollar_dollar[1]
            else:
                _t1572 = None
            fields905 = (_dollar_dollar[0], _t1572,)
            assert fields905 is not None
            unwrapped_fields906 = fields905
            self.write("[")
            self.indent()
            field907 = unwrapped_fields906[0]
            for i909, elem908 in enumerate(field907):
                if (i909 > 0):
                    self.newline()
                self.pretty_binding(elem908)
            field910 = unwrapped_fields906[1]
            if field910 is not None:
                self.newline()
                assert field910 is not None
                opt_val911 = field910
                self.pretty_value_bindings(opt_val911)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat917 = self._try_flat(msg, self.pretty_binding)
        if flat917 is not None:
            assert flat917 is not None
            self.write(flat917)
            return None
        else:
            _dollar_dollar = msg
            fields913 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields913 is not None
            unwrapped_fields914 = fields913
            field915 = unwrapped_fields914[0]
            self.write(field915)
            self.write("::")
            field916 = unwrapped_fields914[1]
            self.pretty_type(field916)

    def pretty_type(self, msg: logic_pb2.Type):
        flat946 = self._try_flat(msg, self.pretty_type)
        if flat946 is not None:
            assert flat946 is not None
            self.write(flat946)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1573 = _dollar_dollar.unspecified_type
            else:
                _t1573 = None
            deconstruct_result944 = _t1573
            if deconstruct_result944 is not None:
                assert deconstruct_result944 is not None
                unwrapped945 = deconstruct_result944
                self.pretty_unspecified_type(unwrapped945)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1574 = _dollar_dollar.string_type
                else:
                    _t1574 = None
                deconstruct_result942 = _t1574
                if deconstruct_result942 is not None:
                    assert deconstruct_result942 is not None
                    unwrapped943 = deconstruct_result942
                    self.pretty_string_type(unwrapped943)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1575 = _dollar_dollar.int_type
                    else:
                        _t1575 = None
                    deconstruct_result940 = _t1575
                    if deconstruct_result940 is not None:
                        assert deconstruct_result940 is not None
                        unwrapped941 = deconstruct_result940
                        self.pretty_int_type(unwrapped941)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1576 = _dollar_dollar.float_type
                        else:
                            _t1576 = None
                        deconstruct_result938 = _t1576
                        if deconstruct_result938 is not None:
                            assert deconstruct_result938 is not None
                            unwrapped939 = deconstruct_result938
                            self.pretty_float_type(unwrapped939)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1577 = _dollar_dollar.uint128_type
                            else:
                                _t1577 = None
                            deconstruct_result936 = _t1577
                            if deconstruct_result936 is not None:
                                assert deconstruct_result936 is not None
                                unwrapped937 = deconstruct_result936
                                self.pretty_uint128_type(unwrapped937)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1578 = _dollar_dollar.int128_type
                                else:
                                    _t1578 = None
                                deconstruct_result934 = _t1578
                                if deconstruct_result934 is not None:
                                    assert deconstruct_result934 is not None
                                    unwrapped935 = deconstruct_result934
                                    self.pretty_int128_type(unwrapped935)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1579 = _dollar_dollar.date_type
                                    else:
                                        _t1579 = None
                                    deconstruct_result932 = _t1579
                                    if deconstruct_result932 is not None:
                                        assert deconstruct_result932 is not None
                                        unwrapped933 = deconstruct_result932
                                        self.pretty_date_type(unwrapped933)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1580 = _dollar_dollar.datetime_type
                                        else:
                                            _t1580 = None
                                        deconstruct_result930 = _t1580
                                        if deconstruct_result930 is not None:
                                            assert deconstruct_result930 is not None
                                            unwrapped931 = deconstruct_result930
                                            self.pretty_datetime_type(unwrapped931)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1581 = _dollar_dollar.missing_type
                                            else:
                                                _t1581 = None
                                            deconstruct_result928 = _t1581
                                            if deconstruct_result928 is not None:
                                                assert deconstruct_result928 is not None
                                                unwrapped929 = deconstruct_result928
                                                self.pretty_missing_type(unwrapped929)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1582 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1582 = None
                                                deconstruct_result926 = _t1582
                                                if deconstruct_result926 is not None:
                                                    assert deconstruct_result926 is not None
                                                    unwrapped927 = deconstruct_result926
                                                    self.pretty_decimal_type(unwrapped927)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1583 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1583 = None
                                                    deconstruct_result924 = _t1583
                                                    if deconstruct_result924 is not None:
                                                        assert deconstruct_result924 is not None
                                                        unwrapped925 = deconstruct_result924
                                                        self.pretty_boolean_type(unwrapped925)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1584 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1584 = None
                                                        deconstruct_result922 = _t1584
                                                        if deconstruct_result922 is not None:
                                                            assert deconstruct_result922 is not None
                                                            unwrapped923 = deconstruct_result922
                                                            self.pretty_int32_type(unwrapped923)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1585 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1585 = None
                                                            deconstruct_result920 = _t1585
                                                            if deconstruct_result920 is not None:
                                                                assert deconstruct_result920 is not None
                                                                unwrapped921 = deconstruct_result920
                                                                self.pretty_float32_type(unwrapped921)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1586 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1586 = None
                                                                deconstruct_result918 = _t1586
                                                                if deconstruct_result918 is not None:
                                                                    assert deconstruct_result918 is not None
                                                                    unwrapped919 = deconstruct_result918
                                                                    self.pretty_uint32_type(unwrapped919)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields947 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields948 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields949 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields950 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields951 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields952 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields953 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields954 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields955 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat960 = self._try_flat(msg, self.pretty_decimal_type)
        if flat960 is not None:
            assert flat960 is not None
            self.write(flat960)
            return None
        else:
            _dollar_dollar = msg
            fields956 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields956 is not None
            unwrapped_fields957 = fields956
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field958 = unwrapped_fields957[0]
            self.write(str(field958))
            self.newline()
            field959 = unwrapped_fields957[1]
            self.write(str(field959))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields961 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields962 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields963 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields964 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat968 = self._try_flat(msg, self.pretty_value_bindings)
        if flat968 is not None:
            assert flat968 is not None
            self.write(flat968)
            return None
        else:
            fields965 = msg
            self.write("|")
            if not len(fields965) == 0:
                self.write(" ")
                for i967, elem966 in enumerate(fields965):
                    if (i967 > 0):
                        self.newline()
                    self.pretty_binding(elem966)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat995 = self._try_flat(msg, self.pretty_formula)
        if flat995 is not None:
            assert flat995 is not None
            self.write(flat995)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1587 = _dollar_dollar.conjunction
            else:
                _t1587 = None
            deconstruct_result993 = _t1587
            if deconstruct_result993 is not None:
                assert deconstruct_result993 is not None
                unwrapped994 = deconstruct_result993
                self.pretty_true(unwrapped994)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1588 = _dollar_dollar.disjunction
                else:
                    _t1588 = None
                deconstruct_result991 = _t1588
                if deconstruct_result991 is not None:
                    assert deconstruct_result991 is not None
                    unwrapped992 = deconstruct_result991
                    self.pretty_false(unwrapped992)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1589 = _dollar_dollar.exists
                    else:
                        _t1589 = None
                    deconstruct_result989 = _t1589
                    if deconstruct_result989 is not None:
                        assert deconstruct_result989 is not None
                        unwrapped990 = deconstruct_result989
                        self.pretty_exists(unwrapped990)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1590 = _dollar_dollar.reduce
                        else:
                            _t1590 = None
                        deconstruct_result987 = _t1590
                        if deconstruct_result987 is not None:
                            assert deconstruct_result987 is not None
                            unwrapped988 = deconstruct_result987
                            self.pretty_reduce(unwrapped988)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1591 = _dollar_dollar.conjunction
                            else:
                                _t1591 = None
                            deconstruct_result985 = _t1591
                            if deconstruct_result985 is not None:
                                assert deconstruct_result985 is not None
                                unwrapped986 = deconstruct_result985
                                self.pretty_conjunction(unwrapped986)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1592 = _dollar_dollar.disjunction
                                else:
                                    _t1592 = None
                                deconstruct_result983 = _t1592
                                if deconstruct_result983 is not None:
                                    assert deconstruct_result983 is not None
                                    unwrapped984 = deconstruct_result983
                                    self.pretty_disjunction(unwrapped984)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1593 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1593 = None
                                    deconstruct_result981 = _t1593
                                    if deconstruct_result981 is not None:
                                        assert deconstruct_result981 is not None
                                        unwrapped982 = deconstruct_result981
                                        self.pretty_not(unwrapped982)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1594 = _dollar_dollar.ffi
                                        else:
                                            _t1594 = None
                                        deconstruct_result979 = _t1594
                                        if deconstruct_result979 is not None:
                                            assert deconstruct_result979 is not None
                                            unwrapped980 = deconstruct_result979
                                            self.pretty_ffi(unwrapped980)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1595 = _dollar_dollar.atom
                                            else:
                                                _t1595 = None
                                            deconstruct_result977 = _t1595
                                            if deconstruct_result977 is not None:
                                                assert deconstruct_result977 is not None
                                                unwrapped978 = deconstruct_result977
                                                self.pretty_atom(unwrapped978)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1596 = _dollar_dollar.pragma
                                                else:
                                                    _t1596 = None
                                                deconstruct_result975 = _t1596
                                                if deconstruct_result975 is not None:
                                                    assert deconstruct_result975 is not None
                                                    unwrapped976 = deconstruct_result975
                                                    self.pretty_pragma(unwrapped976)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1597 = _dollar_dollar.primitive
                                                    else:
                                                        _t1597 = None
                                                    deconstruct_result973 = _t1597
                                                    if deconstruct_result973 is not None:
                                                        assert deconstruct_result973 is not None
                                                        unwrapped974 = deconstruct_result973
                                                        self.pretty_primitive(unwrapped974)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1598 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1598 = None
                                                        deconstruct_result971 = _t1598
                                                        if deconstruct_result971 is not None:
                                                            assert deconstruct_result971 is not None
                                                            unwrapped972 = deconstruct_result971
                                                            self.pretty_rel_atom(unwrapped972)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1599 = _dollar_dollar.cast
                                                            else:
                                                                _t1599 = None
                                                            deconstruct_result969 = _t1599
                                                            if deconstruct_result969 is not None:
                                                                assert deconstruct_result969 is not None
                                                                unwrapped970 = deconstruct_result969
                                                                self.pretty_cast(unwrapped970)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields996 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields997 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat1002 = self._try_flat(msg, self.pretty_exists)
        if flat1002 is not None:
            assert flat1002 is not None
            self.write(flat1002)
            return None
        else:
            _dollar_dollar = msg
            _t1600 = self.deconstruct_bindings(_dollar_dollar.body)
            fields998 = (_t1600, _dollar_dollar.body.value,)
            assert fields998 is not None
            unwrapped_fields999 = fields998
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field1000 = unwrapped_fields999[0]
            self.pretty_bindings(field1000)
            self.newline()
            field1001 = unwrapped_fields999[1]
            self.pretty_formula(field1001)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat1008 = self._try_flat(msg, self.pretty_reduce)
        if flat1008 is not None:
            assert flat1008 is not None
            self.write(flat1008)
            return None
        else:
            _dollar_dollar = msg
            fields1003 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields1003 is not None
            unwrapped_fields1004 = fields1003
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field1005 = unwrapped_fields1004[0]
            self.pretty_abstraction(field1005)
            self.newline()
            field1006 = unwrapped_fields1004[1]
            self.pretty_abstraction(field1006)
            self.newline()
            field1007 = unwrapped_fields1004[2]
            self.pretty_terms(field1007)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat1012 = self._try_flat(msg, self.pretty_terms)
        if flat1012 is not None:
            assert flat1012 is not None
            self.write(flat1012)
            return None
        else:
            fields1009 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields1009) == 0:
                self.newline()
                for i1011, elem1010 in enumerate(fields1009):
                    if (i1011 > 0):
                        self.newline()
                    self.pretty_term(elem1010)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat1017 = self._try_flat(msg, self.pretty_term)
        if flat1017 is not None:
            assert flat1017 is not None
            self.write(flat1017)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1601 = _dollar_dollar.var
            else:
                _t1601 = None
            deconstruct_result1015 = _t1601
            if deconstruct_result1015 is not None:
                assert deconstruct_result1015 is not None
                unwrapped1016 = deconstruct_result1015
                self.pretty_var(unwrapped1016)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1602 = _dollar_dollar.constant
                else:
                    _t1602 = None
                deconstruct_result1013 = _t1602
                if deconstruct_result1013 is not None:
                    assert deconstruct_result1013 is not None
                    unwrapped1014 = deconstruct_result1013
                    self.pretty_value(unwrapped1014)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat1020 = self._try_flat(msg, self.pretty_var)
        if flat1020 is not None:
            assert flat1020 is not None
            self.write(flat1020)
            return None
        else:
            _dollar_dollar = msg
            fields1018 = _dollar_dollar.name
            assert fields1018 is not None
            unwrapped_fields1019 = fields1018
            self.write(unwrapped_fields1019)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1046 = self._try_flat(msg, self.pretty_value)
        if flat1046 is not None:
            assert flat1046 is not None
            self.write(flat1046)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1603 = _dollar_dollar.date_value
            else:
                _t1603 = None
            deconstruct_result1044 = _t1603
            if deconstruct_result1044 is not None:
                assert deconstruct_result1044 is not None
                unwrapped1045 = deconstruct_result1044
                self.pretty_date(unwrapped1045)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1604 = _dollar_dollar.datetime_value
                else:
                    _t1604 = None
                deconstruct_result1042 = _t1604
                if deconstruct_result1042 is not None:
                    assert deconstruct_result1042 is not None
                    unwrapped1043 = deconstruct_result1042
                    self.pretty_datetime(unwrapped1043)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1605 = _dollar_dollar.string_value
                    else:
                        _t1605 = None
                    deconstruct_result1040 = _t1605
                    if deconstruct_result1040 is not None:
                        assert deconstruct_result1040 is not None
                        unwrapped1041 = deconstruct_result1040
                        self.write(self.format_string_value(unwrapped1041))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1606 = _dollar_dollar.int32_value
                        else:
                            _t1606 = None
                        deconstruct_result1038 = _t1606
                        if deconstruct_result1038 is not None:
                            assert deconstruct_result1038 is not None
                            unwrapped1039 = deconstruct_result1038
                            self.write((str(unwrapped1039) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1607 = _dollar_dollar.int_value
                            else:
                                _t1607 = None
                            deconstruct_result1036 = _t1607
                            if deconstruct_result1036 is not None:
                                assert deconstruct_result1036 is not None
                                unwrapped1037 = deconstruct_result1036
                                self.write(str(unwrapped1037))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1608 = _dollar_dollar.float32_value
                                else:
                                    _t1608 = None
                                deconstruct_result1034 = _t1608
                                if deconstruct_result1034 is not None:
                                    assert deconstruct_result1034 is not None
                                    unwrapped1035 = deconstruct_result1034
                                    self.write(self.format_float32_literal(unwrapped1035))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1609 = _dollar_dollar.float_value
                                    else:
                                        _t1609 = None
                                    deconstruct_result1032 = _t1609
                                    if deconstruct_result1032 is not None:
                                        assert deconstruct_result1032 is not None
                                        unwrapped1033 = deconstruct_result1032
                                        self.write(str(unwrapped1033))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1610 = _dollar_dollar.uint32_value
                                        else:
                                            _t1610 = None
                                        deconstruct_result1030 = _t1610
                                        if deconstruct_result1030 is not None:
                                            assert deconstruct_result1030 is not None
                                            unwrapped1031 = deconstruct_result1030
                                            self.write((str(unwrapped1031) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1611 = _dollar_dollar.uint128_value
                                            else:
                                                _t1611 = None
                                            deconstruct_result1028 = _t1611
                                            if deconstruct_result1028 is not None:
                                                assert deconstruct_result1028 is not None
                                                unwrapped1029 = deconstruct_result1028
                                                self.write(self.format_uint128(unwrapped1029))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1612 = _dollar_dollar.int128_value
                                                else:
                                                    _t1612 = None
                                                deconstruct_result1026 = _t1612
                                                if deconstruct_result1026 is not None:
                                                    assert deconstruct_result1026 is not None
                                                    unwrapped1027 = deconstruct_result1026
                                                    self.write(self.format_int128(unwrapped1027))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1613 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1613 = None
                                                    deconstruct_result1024 = _t1613
                                                    if deconstruct_result1024 is not None:
                                                        assert deconstruct_result1024 is not None
                                                        unwrapped1025 = deconstruct_result1024
                                                        self.write(self.format_decimal(unwrapped1025))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1614 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1614 = None
                                                        deconstruct_result1022 = _t1614
                                                        if deconstruct_result1022 is not None:
                                                            assert deconstruct_result1022 is not None
                                                            unwrapped1023 = deconstruct_result1022
                                                            self.pretty_boolean_value(unwrapped1023)
                                                        else:
                                                            fields1021 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1052 = self._try_flat(msg, self.pretty_date)
        if flat1052 is not None:
            assert flat1052 is not None
            self.write(flat1052)
            return None
        else:
            _dollar_dollar = msg
            fields1047 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1047 is not None
            unwrapped_fields1048 = fields1047
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1049 = unwrapped_fields1048[0]
            self.write(str(field1049))
            self.newline()
            field1050 = unwrapped_fields1048[1]
            self.write(str(field1050))
            self.newline()
            field1051 = unwrapped_fields1048[2]
            self.write(str(field1051))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1063 = self._try_flat(msg, self.pretty_datetime)
        if flat1063 is not None:
            assert flat1063 is not None
            self.write(flat1063)
            return None
        else:
            _dollar_dollar = msg
            fields1053 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1053 is not None
            unwrapped_fields1054 = fields1053
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1055 = unwrapped_fields1054[0]
            self.write(str(field1055))
            self.newline()
            field1056 = unwrapped_fields1054[1]
            self.write(str(field1056))
            self.newline()
            field1057 = unwrapped_fields1054[2]
            self.write(str(field1057))
            self.newline()
            field1058 = unwrapped_fields1054[3]
            self.write(str(field1058))
            self.newline()
            field1059 = unwrapped_fields1054[4]
            self.write(str(field1059))
            self.newline()
            field1060 = unwrapped_fields1054[5]
            self.write(str(field1060))
            field1061 = unwrapped_fields1054[6]
            if field1061 is not None:
                self.newline()
                assert field1061 is not None
                opt_val1062 = field1061
                self.write(str(opt_val1062))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1068 = self._try_flat(msg, self.pretty_conjunction)
        if flat1068 is not None:
            assert flat1068 is not None
            self.write(flat1068)
            return None
        else:
            _dollar_dollar = msg
            fields1064 = _dollar_dollar.args
            assert fields1064 is not None
            unwrapped_fields1065 = fields1064
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1065) == 0:
                self.newline()
                for i1067, elem1066 in enumerate(unwrapped_fields1065):
                    if (i1067 > 0):
                        self.newline()
                    self.pretty_formula(elem1066)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1073 = self._try_flat(msg, self.pretty_disjunction)
        if flat1073 is not None:
            assert flat1073 is not None
            self.write(flat1073)
            return None
        else:
            _dollar_dollar = msg
            fields1069 = _dollar_dollar.args
            assert fields1069 is not None
            unwrapped_fields1070 = fields1069
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1070) == 0:
                self.newline()
                for i1072, elem1071 in enumerate(unwrapped_fields1070):
                    if (i1072 > 0):
                        self.newline()
                    self.pretty_formula(elem1071)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1076 = self._try_flat(msg, self.pretty_not)
        if flat1076 is not None:
            assert flat1076 is not None
            self.write(flat1076)
            return None
        else:
            _dollar_dollar = msg
            fields1074 = _dollar_dollar.arg
            assert fields1074 is not None
            unwrapped_fields1075 = fields1074
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1075)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1082 = self._try_flat(msg, self.pretty_ffi)
        if flat1082 is not None:
            assert flat1082 is not None
            self.write(flat1082)
            return None
        else:
            _dollar_dollar = msg
            fields1077 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1077 is not None
            unwrapped_fields1078 = fields1077
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1079 = unwrapped_fields1078[0]
            self.pretty_name(field1079)
            self.newline()
            field1080 = unwrapped_fields1078[1]
            self.pretty_ffi_args(field1080)
            self.newline()
            field1081 = unwrapped_fields1078[2]
            self.pretty_terms(field1081)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1084 = self._try_flat(msg, self.pretty_name)
        if flat1084 is not None:
            assert flat1084 is not None
            self.write(flat1084)
            return None
        else:
            fields1083 = msg
            self.write(":")
            self.write(fields1083)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1088 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1088 is not None:
            assert flat1088 is not None
            self.write(flat1088)
            return None
        else:
            fields1085 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1085) == 0:
                self.newline()
                for i1087, elem1086 in enumerate(fields1085):
                    if (i1087 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1086)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1095 = self._try_flat(msg, self.pretty_atom)
        if flat1095 is not None:
            assert flat1095 is not None
            self.write(flat1095)
            return None
        else:
            _dollar_dollar = msg
            fields1089 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1089 is not None
            unwrapped_fields1090 = fields1089
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1091 = unwrapped_fields1090[0]
            self.pretty_relation_id(field1091)
            field1092 = unwrapped_fields1090[1]
            if not len(field1092) == 0:
                self.newline()
                for i1094, elem1093 in enumerate(field1092):
                    if (i1094 > 0):
                        self.newline()
                    self.pretty_term(elem1093)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1102 = self._try_flat(msg, self.pretty_pragma)
        if flat1102 is not None:
            assert flat1102 is not None
            self.write(flat1102)
            return None
        else:
            _dollar_dollar = msg
            fields1096 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1096 is not None
            unwrapped_fields1097 = fields1096
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1098 = unwrapped_fields1097[0]
            self.pretty_name(field1098)
            field1099 = unwrapped_fields1097[1]
            if not len(field1099) == 0:
                self.newline()
                for i1101, elem1100 in enumerate(field1099):
                    if (i1101 > 0):
                        self.newline()
                    self.pretty_term(elem1100)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1118 = self._try_flat(msg, self.pretty_primitive)
        if flat1118 is not None:
            assert flat1118 is not None
            self.write(flat1118)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1615 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1615 = None
            guard_result1117 = _t1615
            if guard_result1117 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1616 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1616 = None
                guard_result1116 = _t1616
                if guard_result1116 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1617 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1617 = None
                    guard_result1115 = _t1617
                    if guard_result1115 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1618 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1618 = None
                        guard_result1114 = _t1618
                        if guard_result1114 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1619 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1619 = None
                            guard_result1113 = _t1619
                            if guard_result1113 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1620 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1620 = None
                                guard_result1112 = _t1620
                                if guard_result1112 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1621 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1621 = None
                                    guard_result1111 = _t1621
                                    if guard_result1111 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1622 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1622 = None
                                        guard_result1110 = _t1622
                                        if guard_result1110 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1623 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1623 = None
                                            guard_result1109 = _t1623
                                            if guard_result1109 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1103 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1103 is not None
                                                unwrapped_fields1104 = fields1103
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1105 = unwrapped_fields1104[0]
                                                self.pretty_name(field1105)
                                                field1106 = unwrapped_fields1104[1]
                                                if not len(field1106) == 0:
                                                    self.newline()
                                                    for i1108, elem1107 in enumerate(field1106):
                                                        if (i1108 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1107)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1123 = self._try_flat(msg, self.pretty_eq)
        if flat1123 is not None:
            assert flat1123 is not None
            self.write(flat1123)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1624 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1624 = None
            fields1119 = _t1624
            assert fields1119 is not None
            unwrapped_fields1120 = fields1119
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1121 = unwrapped_fields1120[0]
            self.pretty_term(field1121)
            self.newline()
            field1122 = unwrapped_fields1120[1]
            self.pretty_term(field1122)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1128 = self._try_flat(msg, self.pretty_lt)
        if flat1128 is not None:
            assert flat1128 is not None
            self.write(flat1128)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1625 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1625 = None
            fields1124 = _t1625
            assert fields1124 is not None
            unwrapped_fields1125 = fields1124
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1126 = unwrapped_fields1125[0]
            self.pretty_term(field1126)
            self.newline()
            field1127 = unwrapped_fields1125[1]
            self.pretty_term(field1127)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1133 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1133 is not None:
            assert flat1133 is not None
            self.write(flat1133)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1626 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1626 = None
            fields1129 = _t1626
            assert fields1129 is not None
            unwrapped_fields1130 = fields1129
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1131 = unwrapped_fields1130[0]
            self.pretty_term(field1131)
            self.newline()
            field1132 = unwrapped_fields1130[1]
            self.pretty_term(field1132)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1138 = self._try_flat(msg, self.pretty_gt)
        if flat1138 is not None:
            assert flat1138 is not None
            self.write(flat1138)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1627 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1627 = None
            fields1134 = _t1627
            assert fields1134 is not None
            unwrapped_fields1135 = fields1134
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1136 = unwrapped_fields1135[0]
            self.pretty_term(field1136)
            self.newline()
            field1137 = unwrapped_fields1135[1]
            self.pretty_term(field1137)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1143 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1143 is not None:
            assert flat1143 is not None
            self.write(flat1143)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1628 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1628 = None
            fields1139 = _t1628
            assert fields1139 is not None
            unwrapped_fields1140 = fields1139
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1141 = unwrapped_fields1140[0]
            self.pretty_term(field1141)
            self.newline()
            field1142 = unwrapped_fields1140[1]
            self.pretty_term(field1142)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1149 = self._try_flat(msg, self.pretty_add)
        if flat1149 is not None:
            assert flat1149 is not None
            self.write(flat1149)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1629 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1629 = None
            fields1144 = _t1629
            assert fields1144 is not None
            unwrapped_fields1145 = fields1144
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1146 = unwrapped_fields1145[0]
            self.pretty_term(field1146)
            self.newline()
            field1147 = unwrapped_fields1145[1]
            self.pretty_term(field1147)
            self.newline()
            field1148 = unwrapped_fields1145[2]
            self.pretty_term(field1148)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1155 = self._try_flat(msg, self.pretty_minus)
        if flat1155 is not None:
            assert flat1155 is not None
            self.write(flat1155)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1630 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1630 = None
            fields1150 = _t1630
            assert fields1150 is not None
            unwrapped_fields1151 = fields1150
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1152 = unwrapped_fields1151[0]
            self.pretty_term(field1152)
            self.newline()
            field1153 = unwrapped_fields1151[1]
            self.pretty_term(field1153)
            self.newline()
            field1154 = unwrapped_fields1151[2]
            self.pretty_term(field1154)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1161 = self._try_flat(msg, self.pretty_multiply)
        if flat1161 is not None:
            assert flat1161 is not None
            self.write(flat1161)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1631 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1631 = None
            fields1156 = _t1631
            assert fields1156 is not None
            unwrapped_fields1157 = fields1156
            self.write("(*")
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

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1167 = self._try_flat(msg, self.pretty_divide)
        if flat1167 is not None:
            assert flat1167 is not None
            self.write(flat1167)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1632 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1632 = None
            fields1162 = _t1632
            assert fields1162 is not None
            unwrapped_fields1163 = fields1162
            self.write("(/")
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

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1172 = self._try_flat(msg, self.pretty_rel_term)
        if flat1172 is not None:
            assert flat1172 is not None
            self.write(flat1172)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1633 = _dollar_dollar.specialized_value
            else:
                _t1633 = None
            deconstruct_result1170 = _t1633
            if deconstruct_result1170 is not None:
                assert deconstruct_result1170 is not None
                unwrapped1171 = deconstruct_result1170
                self.pretty_specialized_value(unwrapped1171)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1634 = _dollar_dollar.term
                else:
                    _t1634 = None
                deconstruct_result1168 = _t1634
                if deconstruct_result1168 is not None:
                    assert deconstruct_result1168 is not None
                    unwrapped1169 = deconstruct_result1168
                    self.pretty_term(unwrapped1169)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1174 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1174 is not None:
            assert flat1174 is not None
            self.write(flat1174)
            return None
        else:
            fields1173 = msg
            self.write("#")
            self.pretty_raw_value(fields1173)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1181 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1181 is not None:
            assert flat1181 is not None
            self.write(flat1181)
            return None
        else:
            _dollar_dollar = msg
            fields1175 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1175 is not None
            unwrapped_fields1176 = fields1175
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1177 = unwrapped_fields1176[0]
            self.pretty_name(field1177)
            field1178 = unwrapped_fields1176[1]
            if not len(field1178) == 0:
                self.newline()
                for i1180, elem1179 in enumerate(field1178):
                    if (i1180 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1179)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1186 = self._try_flat(msg, self.pretty_cast)
        if flat1186 is not None:
            assert flat1186 is not None
            self.write(flat1186)
            return None
        else:
            _dollar_dollar = msg
            fields1182 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1182 is not None
            unwrapped_fields1183 = fields1182
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1184 = unwrapped_fields1183[0]
            self.pretty_term(field1184)
            self.newline()
            field1185 = unwrapped_fields1183[1]
            self.pretty_term(field1185)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1190 = self._try_flat(msg, self.pretty_attrs)
        if flat1190 is not None:
            assert flat1190 is not None
            self.write(flat1190)
            return None
        else:
            fields1187 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1187) == 0:
                self.newline()
                for i1189, elem1188 in enumerate(fields1187):
                    if (i1189 > 0):
                        self.newline()
                    self.pretty_attribute(elem1188)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1197 = self._try_flat(msg, self.pretty_attribute)
        if flat1197 is not None:
            assert flat1197 is not None
            self.write(flat1197)
            return None
        else:
            _dollar_dollar = msg
            fields1191 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1191 is not None
            unwrapped_fields1192 = fields1191
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1193 = unwrapped_fields1192[0]
            self.pretty_name(field1193)
            field1194 = unwrapped_fields1192[1]
            if not len(field1194) == 0:
                self.newline()
                for i1196, elem1195 in enumerate(field1194):
                    if (i1196 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1195)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1204 = self._try_flat(msg, self.pretty_algorithm)
        if flat1204 is not None:
            assert flat1204 is not None
            self.write(flat1204)
            return None
        else:
            _dollar_dollar = msg
            fields1198 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            assert fields1198 is not None
            unwrapped_fields1199 = fields1198
            self.write("(algorithm")
            self.indent_sexp()
            field1200 = unwrapped_fields1199[0]
            if not len(field1200) == 0:
                self.newline()
                for i1202, elem1201 in enumerate(field1200):
                    if (i1202 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1201)
            self.newline()
            field1203 = unwrapped_fields1199[1]
            self.pretty_script(field1203)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1209 = self._try_flat(msg, self.pretty_script)
        if flat1209 is not None:
            assert flat1209 is not None
            self.write(flat1209)
            return None
        else:
            _dollar_dollar = msg
            fields1205 = _dollar_dollar.constructs
            assert fields1205 is not None
            unwrapped_fields1206 = fields1205
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1206) == 0:
                self.newline()
                for i1208, elem1207 in enumerate(unwrapped_fields1206):
                    if (i1208 > 0):
                        self.newline()
                    self.pretty_construct(elem1207)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1214 = self._try_flat(msg, self.pretty_construct)
        if flat1214 is not None:
            assert flat1214 is not None
            self.write(flat1214)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1635 = _dollar_dollar.loop
            else:
                _t1635 = None
            deconstruct_result1212 = _t1635
            if deconstruct_result1212 is not None:
                assert deconstruct_result1212 is not None
                unwrapped1213 = deconstruct_result1212
                self.pretty_loop(unwrapped1213)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1636 = _dollar_dollar.instruction
                else:
                    _t1636 = None
                deconstruct_result1210 = _t1636
                if deconstruct_result1210 is not None:
                    assert deconstruct_result1210 is not None
                    unwrapped1211 = deconstruct_result1210
                    self.pretty_instruction(unwrapped1211)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1219 = self._try_flat(msg, self.pretty_loop)
        if flat1219 is not None:
            assert flat1219 is not None
            self.write(flat1219)
            return None
        else:
            _dollar_dollar = msg
            fields1215 = (_dollar_dollar.init, _dollar_dollar.body,)
            assert fields1215 is not None
            unwrapped_fields1216 = fields1215
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1217 = unwrapped_fields1216[0]
            self.pretty_init(field1217)
            self.newline()
            field1218 = unwrapped_fields1216[1]
            self.pretty_script(field1218)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1223 = self._try_flat(msg, self.pretty_init)
        if flat1223 is not None:
            assert flat1223 is not None
            self.write(flat1223)
            return None
        else:
            fields1220 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1220) == 0:
                self.newline()
                for i1222, elem1221 in enumerate(fields1220):
                    if (i1222 > 0):
                        self.newline()
                    self.pretty_instruction(elem1221)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1234 = self._try_flat(msg, self.pretty_instruction)
        if flat1234 is not None:
            assert flat1234 is not None
            self.write(flat1234)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1637 = _dollar_dollar.assign
            else:
                _t1637 = None
            deconstruct_result1232 = _t1637
            if deconstruct_result1232 is not None:
                assert deconstruct_result1232 is not None
                unwrapped1233 = deconstruct_result1232
                self.pretty_assign(unwrapped1233)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1638 = _dollar_dollar.upsert
                else:
                    _t1638 = None
                deconstruct_result1230 = _t1638
                if deconstruct_result1230 is not None:
                    assert deconstruct_result1230 is not None
                    unwrapped1231 = deconstruct_result1230
                    self.pretty_upsert(unwrapped1231)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1639 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1639 = None
                    deconstruct_result1228 = _t1639
                    if deconstruct_result1228 is not None:
                        assert deconstruct_result1228 is not None
                        unwrapped1229 = deconstruct_result1228
                        self.pretty_break(unwrapped1229)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1640 = _dollar_dollar.monoid_def
                        else:
                            _t1640 = None
                        deconstruct_result1226 = _t1640
                        if deconstruct_result1226 is not None:
                            assert deconstruct_result1226 is not None
                            unwrapped1227 = deconstruct_result1226
                            self.pretty_monoid_def(unwrapped1227)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1641 = _dollar_dollar.monus_def
                            else:
                                _t1641 = None
                            deconstruct_result1224 = _t1641
                            if deconstruct_result1224 is not None:
                                assert deconstruct_result1224 is not None
                                unwrapped1225 = deconstruct_result1224
                                self.pretty_monus_def(unwrapped1225)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1241 = self._try_flat(msg, self.pretty_assign)
        if flat1241 is not None:
            assert flat1241 is not None
            self.write(flat1241)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1642 = _dollar_dollar.attrs
            else:
                _t1642 = None
            fields1235 = (_dollar_dollar.name, _dollar_dollar.body, _t1642,)
            assert fields1235 is not None
            unwrapped_fields1236 = fields1235
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1237 = unwrapped_fields1236[0]
            self.pretty_relation_id(field1237)
            self.newline()
            field1238 = unwrapped_fields1236[1]
            self.pretty_abstraction(field1238)
            field1239 = unwrapped_fields1236[2]
            if field1239 is not None:
                self.newline()
                assert field1239 is not None
                opt_val1240 = field1239
                self.pretty_attrs(opt_val1240)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1248 = self._try_flat(msg, self.pretty_upsert)
        if flat1248 is not None:
            assert flat1248 is not None
            self.write(flat1248)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1643 = _dollar_dollar.attrs
            else:
                _t1643 = None
            fields1242 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1643,)
            assert fields1242 is not None
            unwrapped_fields1243 = fields1242
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1244 = unwrapped_fields1243[0]
            self.pretty_relation_id(field1244)
            self.newline()
            field1245 = unwrapped_fields1243[1]
            self.pretty_abstraction_with_arity(field1245)
            field1246 = unwrapped_fields1243[2]
            if field1246 is not None:
                self.newline()
                assert field1246 is not None
                opt_val1247 = field1246
                self.pretty_attrs(opt_val1247)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1253 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1253 is not None:
            assert flat1253 is not None
            self.write(flat1253)
            return None
        else:
            _dollar_dollar = msg
            _t1644 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1249 = (_t1644, _dollar_dollar[0].value,)
            assert fields1249 is not None
            unwrapped_fields1250 = fields1249
            self.write("(")
            self.indent()
            field1251 = unwrapped_fields1250[0]
            self.pretty_bindings(field1251)
            self.newline()
            field1252 = unwrapped_fields1250[1]
            self.pretty_formula(field1252)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1260 = self._try_flat(msg, self.pretty_break)
        if flat1260 is not None:
            assert flat1260 is not None
            self.write(flat1260)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1645 = _dollar_dollar.attrs
            else:
                _t1645 = None
            fields1254 = (_dollar_dollar.name, _dollar_dollar.body, _t1645,)
            assert fields1254 is not None
            unwrapped_fields1255 = fields1254
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1256 = unwrapped_fields1255[0]
            self.pretty_relation_id(field1256)
            self.newline()
            field1257 = unwrapped_fields1255[1]
            self.pretty_abstraction(field1257)
            field1258 = unwrapped_fields1255[2]
            if field1258 is not None:
                self.newline()
                assert field1258 is not None
                opt_val1259 = field1258
                self.pretty_attrs(opt_val1259)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1268 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1268 is not None:
            assert flat1268 is not None
            self.write(flat1268)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1646 = _dollar_dollar.attrs
            else:
                _t1646 = None
            fields1261 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1646,)
            assert fields1261 is not None
            unwrapped_fields1262 = fields1261
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1263 = unwrapped_fields1262[0]
            self.pretty_monoid(field1263)
            self.newline()
            field1264 = unwrapped_fields1262[1]
            self.pretty_relation_id(field1264)
            self.newline()
            field1265 = unwrapped_fields1262[2]
            self.pretty_abstraction_with_arity(field1265)
            field1266 = unwrapped_fields1262[3]
            if field1266 is not None:
                self.newline()
                assert field1266 is not None
                opt_val1267 = field1266
                self.pretty_attrs(opt_val1267)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1277 = self._try_flat(msg, self.pretty_monoid)
        if flat1277 is not None:
            assert flat1277 is not None
            self.write(flat1277)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1647 = _dollar_dollar.or_monoid
            else:
                _t1647 = None
            deconstruct_result1275 = _t1647
            if deconstruct_result1275 is not None:
                assert deconstruct_result1275 is not None
                unwrapped1276 = deconstruct_result1275
                self.pretty_or_monoid(unwrapped1276)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1648 = _dollar_dollar.min_monoid
                else:
                    _t1648 = None
                deconstruct_result1273 = _t1648
                if deconstruct_result1273 is not None:
                    assert deconstruct_result1273 is not None
                    unwrapped1274 = deconstruct_result1273
                    self.pretty_min_monoid(unwrapped1274)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1649 = _dollar_dollar.max_monoid
                    else:
                        _t1649 = None
                    deconstruct_result1271 = _t1649
                    if deconstruct_result1271 is not None:
                        assert deconstruct_result1271 is not None
                        unwrapped1272 = deconstruct_result1271
                        self.pretty_max_monoid(unwrapped1272)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1650 = _dollar_dollar.sum_monoid
                        else:
                            _t1650 = None
                        deconstruct_result1269 = _t1650
                        if deconstruct_result1269 is not None:
                            assert deconstruct_result1269 is not None
                            unwrapped1270 = deconstruct_result1269
                            self.pretty_sum_monoid(unwrapped1270)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1278 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1281 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1281 is not None:
            assert flat1281 is not None
            self.write(flat1281)
            return None
        else:
            _dollar_dollar = msg
            fields1279 = _dollar_dollar.type
            assert fields1279 is not None
            unwrapped_fields1280 = fields1279
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1280)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1284 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1284 is not None:
            assert flat1284 is not None
            self.write(flat1284)
            return None
        else:
            _dollar_dollar = msg
            fields1282 = _dollar_dollar.type
            assert fields1282 is not None
            unwrapped_fields1283 = fields1282
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1283)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1287 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1287 is not None:
            assert flat1287 is not None
            self.write(flat1287)
            return None
        else:
            _dollar_dollar = msg
            fields1285 = _dollar_dollar.type
            assert fields1285 is not None
            unwrapped_fields1286 = fields1285
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1286)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1295 = self._try_flat(msg, self.pretty_monus_def)
        if flat1295 is not None:
            assert flat1295 is not None
            self.write(flat1295)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1651 = _dollar_dollar.attrs
            else:
                _t1651 = None
            fields1288 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1651,)
            assert fields1288 is not None
            unwrapped_fields1289 = fields1288
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1290 = unwrapped_fields1289[0]
            self.pretty_monoid(field1290)
            self.newline()
            field1291 = unwrapped_fields1289[1]
            self.pretty_relation_id(field1291)
            self.newline()
            field1292 = unwrapped_fields1289[2]
            self.pretty_abstraction_with_arity(field1292)
            field1293 = unwrapped_fields1289[3]
            if field1293 is not None:
                self.newline()
                assert field1293 is not None
                opt_val1294 = field1293
                self.pretty_attrs(opt_val1294)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1302 = self._try_flat(msg, self.pretty_constraint)
        if flat1302 is not None:
            assert flat1302 is not None
            self.write(flat1302)
            return None
        else:
            _dollar_dollar = msg
            fields1296 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1296 is not None
            unwrapped_fields1297 = fields1296
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1298 = unwrapped_fields1297[0]
            self.pretty_relation_id(field1298)
            self.newline()
            field1299 = unwrapped_fields1297[1]
            self.pretty_abstraction(field1299)
            self.newline()
            field1300 = unwrapped_fields1297[2]
            self.pretty_functional_dependency_keys(field1300)
            self.newline()
            field1301 = unwrapped_fields1297[3]
            self.pretty_functional_dependency_values(field1301)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1306 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1306 is not None:
            assert flat1306 is not None
            self.write(flat1306)
            return None
        else:
            fields1303 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1303) == 0:
                self.newline()
                for i1305, elem1304 in enumerate(fields1303):
                    if (i1305 > 0):
                        self.newline()
                    self.pretty_var(elem1304)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1310 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1310 is not None:
            assert flat1310 is not None
            self.write(flat1310)
            return None
        else:
            fields1307 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1307) == 0:
                self.newline()
                for i1309, elem1308 in enumerate(fields1307):
                    if (i1309 > 0):
                        self.newline()
                    self.pretty_var(elem1308)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1319 = self._try_flat(msg, self.pretty_data)
        if flat1319 is not None:
            assert flat1319 is not None
            self.write(flat1319)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1652 = _dollar_dollar.edb
            else:
                _t1652 = None
            deconstruct_result1317 = _t1652
            if deconstruct_result1317 is not None:
                assert deconstruct_result1317 is not None
                unwrapped1318 = deconstruct_result1317
                self.pretty_edb(unwrapped1318)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1653 = _dollar_dollar.betree_relation
                else:
                    _t1653 = None
                deconstruct_result1315 = _t1653
                if deconstruct_result1315 is not None:
                    assert deconstruct_result1315 is not None
                    unwrapped1316 = deconstruct_result1315
                    self.pretty_betree_relation(unwrapped1316)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1654 = _dollar_dollar.csv_data
                    else:
                        _t1654 = None
                    deconstruct_result1313 = _t1654
                    if deconstruct_result1313 is not None:
                        assert deconstruct_result1313 is not None
                        unwrapped1314 = deconstruct_result1313
                        self.pretty_csv_data(unwrapped1314)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1655 = _dollar_dollar.iceberg_data
                        else:
                            _t1655 = None
                        deconstruct_result1311 = _t1655
                        if deconstruct_result1311 is not None:
                            assert deconstruct_result1311 is not None
                            unwrapped1312 = deconstruct_result1311
                            self.pretty_iceberg_data(unwrapped1312)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1325 = self._try_flat(msg, self.pretty_edb)
        if flat1325 is not None:
            assert flat1325 is not None
            self.write(flat1325)
            return None
        else:
            _dollar_dollar = msg
            fields1320 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1320 is not None
            unwrapped_fields1321 = fields1320
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1322 = unwrapped_fields1321[0]
            self.pretty_relation_id(field1322)
            self.newline()
            field1323 = unwrapped_fields1321[1]
            self.pretty_edb_path(field1323)
            self.newline()
            field1324 = unwrapped_fields1321[2]
            self.pretty_edb_types(field1324)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1329 = self._try_flat(msg, self.pretty_edb_path)
        if flat1329 is not None:
            assert flat1329 is not None
            self.write(flat1329)
            return None
        else:
            fields1326 = msg
            self.write("[")
            self.indent()
            for i1328, elem1327 in enumerate(fields1326):
                if (i1328 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1327))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1333 = self._try_flat(msg, self.pretty_edb_types)
        if flat1333 is not None:
            assert flat1333 is not None
            self.write(flat1333)
            return None
        else:
            fields1330 = msg
            self.write("[")
            self.indent()
            for i1332, elem1331 in enumerate(fields1330):
                if (i1332 > 0):
                    self.newline()
                self.pretty_type(elem1331)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1338 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1338 is not None:
            assert flat1338 is not None
            self.write(flat1338)
            return None
        else:
            _dollar_dollar = msg
            fields1334 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1334 is not None
            unwrapped_fields1335 = fields1334
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1336 = unwrapped_fields1335[0]
            self.pretty_relation_id(field1336)
            self.newline()
            field1337 = unwrapped_fields1335[1]
            self.pretty_betree_info(field1337)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1344 = self._try_flat(msg, self.pretty_betree_info)
        if flat1344 is not None:
            assert flat1344 is not None
            self.write(flat1344)
            return None
        else:
            _dollar_dollar = msg
            _t1656 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1339 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1656,)
            assert fields1339 is not None
            unwrapped_fields1340 = fields1339
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1341 = unwrapped_fields1340[0]
            self.pretty_betree_info_key_types(field1341)
            self.newline()
            field1342 = unwrapped_fields1340[1]
            self.pretty_betree_info_value_types(field1342)
            self.newline()
            field1343 = unwrapped_fields1340[2]
            self.pretty_config_dict(field1343)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1348 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1348 is not None:
            assert flat1348 is not None
            self.write(flat1348)
            return None
        else:
            fields1345 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1345) == 0:
                self.newline()
                for i1347, elem1346 in enumerate(fields1345):
                    if (i1347 > 0):
                        self.newline()
                    self.pretty_type(elem1346)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1352 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1352 is not None:
            assert flat1352 is not None
            self.write(flat1352)
            return None
        else:
            fields1349 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1349) == 0:
                self.newline()
                for i1351, elem1350 in enumerate(fields1349):
                    if (i1351 > 0):
                        self.newline()
                    self.pretty_type(elem1350)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1359 = self._try_flat(msg, self.pretty_csv_data)
        if flat1359 is not None:
            assert flat1359 is not None
            self.write(flat1359)
            return None
        else:
            _dollar_dollar = msg
            fields1353 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1353 is not None
            unwrapped_fields1354 = fields1353
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1355 = unwrapped_fields1354[0]
            self.pretty_csvlocator(field1355)
            self.newline()
            field1356 = unwrapped_fields1354[1]
            self.pretty_csv_config(field1356)
            self.newline()
            field1357 = unwrapped_fields1354[2]
            self.pretty_gnf_columns(field1357)
            self.newline()
            field1358 = unwrapped_fields1354[3]
            self.pretty_csv_asof(field1358)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1366 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1366 is not None:
            assert flat1366 is not None
            self.write(flat1366)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1657 = _dollar_dollar.paths
            else:
                _t1657 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1658 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1658 = None
            fields1360 = (_t1657, _t1658,)
            assert fields1360 is not None
            unwrapped_fields1361 = fields1360
            self.write("(csv_locator")
            self.indent_sexp()
            field1362 = unwrapped_fields1361[0]
            if field1362 is not None:
                self.newline()
                assert field1362 is not None
                opt_val1363 = field1362
                self.pretty_csv_locator_paths(opt_val1363)
            field1364 = unwrapped_fields1361[1]
            if field1364 is not None:
                self.newline()
                assert field1364 is not None
                opt_val1365 = field1364
                self.pretty_csv_locator_inline_data(opt_val1365)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1370 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1370 is not None:
            assert flat1370 is not None
            self.write(flat1370)
            return None
        else:
            fields1367 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1367) == 0:
                self.newline()
                for i1369, elem1368 in enumerate(fields1367):
                    if (i1369 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1368))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1372 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1372 is not None:
            assert flat1372 is not None
            self.write(flat1372)
            return None
        else:
            fields1371 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1371))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1375 = self._try_flat(msg, self.pretty_csv_config)
        if flat1375 is not None:
            assert flat1375 is not None
            self.write(flat1375)
            return None
        else:
            _dollar_dollar = msg
            _t1659 = self.deconstruct_csv_config(_dollar_dollar)
            fields1373 = _t1659
            assert fields1373 is not None
            unwrapped_fields1374 = fields1373
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1374)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1379 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1379 is not None:
            assert flat1379 is not None
            self.write(flat1379)
            return None
        else:
            fields1376 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1376) == 0:
                self.newline()
                for i1378, elem1377 in enumerate(fields1376):
                    if (i1378 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1377)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1388 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1388 is not None:
            assert flat1388 is not None
            self.write(flat1388)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1660 = _dollar_dollar.target_id
            else:
                _t1660 = None
            fields1380 = (_dollar_dollar.column_path, _t1660, _dollar_dollar.types,)
            assert fields1380 is not None
            unwrapped_fields1381 = fields1380
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1382 = unwrapped_fields1381[0]
            self.pretty_gnf_column_path(field1382)
            field1383 = unwrapped_fields1381[1]
            if field1383 is not None:
                self.newline()
                assert field1383 is not None
                opt_val1384 = field1383
                self.pretty_relation_id(opt_val1384)
            self.newline()
            self.write("[")
            field1385 = unwrapped_fields1381[2]
            for i1387, elem1386 in enumerate(field1385):
                if (i1387 > 0):
                    self.newline()
                self.pretty_type(elem1386)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1395 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1395 is not None:
            assert flat1395 is not None
            self.write(flat1395)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1661 = _dollar_dollar[0]
            else:
                _t1661 = None
            deconstruct_result1393 = _t1661
            if deconstruct_result1393 is not None:
                assert deconstruct_result1393 is not None
                unwrapped1394 = deconstruct_result1393
                self.write(self.format_string_value(unwrapped1394))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1662 = _dollar_dollar
                else:
                    _t1662 = None
                deconstruct_result1389 = _t1662
                if deconstruct_result1389 is not None:
                    assert deconstruct_result1389 is not None
                    unwrapped1390 = deconstruct_result1389
                    self.write("[")
                    self.indent()
                    for i1392, elem1391 in enumerate(unwrapped1390):
                        if (i1392 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1391))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1397 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1397 is not None:
            assert flat1397 is not None
            self.write(flat1397)
            return None
        else:
            fields1396 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1396))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1405 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1405 is not None:
            assert flat1405 is not None
            self.write(flat1405)
            return None
        else:
            _dollar_dollar = msg
            _t1663 = self.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
            fields1398 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _t1663,)
            assert fields1398 is not None
            unwrapped_fields1399 = fields1398
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1400 = unwrapped_fields1399[0]
            self.pretty_iceberg_locator(field1400)
            self.newline()
            field1401 = unwrapped_fields1399[1]
            self.pretty_iceberg_catalog_config(field1401)
            self.newline()
            field1402 = unwrapped_fields1399[2]
            self.pretty_gnf_columns(field1402)
            field1403 = unwrapped_fields1399[3]
            if field1403 is not None:
                self.newline()
                assert field1403 is not None
                opt_val1404 = field1403
                self.pretty_iceberg_to_snapshot(opt_val1404)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1413 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1413 is not None:
            assert flat1413 is not None
            self.write(flat1413)
            return None
        else:
            _dollar_dollar = msg
            fields1406 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1406 is not None
            unwrapped_fields1407 = fields1406
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("table_name")
            self.newline()
            field1408 = unwrapped_fields1407[0]
            self.write(self.format_string_value(field1408))
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("namespace")
            field1409 = unwrapped_fields1407[1]
            if not len(field1409) == 0:
                self.newline()
                for i1411, elem1410 in enumerate(field1409):
                    if (i1411 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1410))
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("warehouse")
            self.newline()
            field1412 = unwrapped_fields1407[2]
            self.write(self.format_string_value(field1412))
            self.dedent()
            self.write(")")
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config(self, msg: logic_pb2.IcebergCatalogConfig):
        flat1425 = self._try_flat(msg, self.pretty_iceberg_catalog_config)
        if flat1425 is not None:
            assert flat1425 is not None
            self.write(flat1425)
            return None
        else:
            _dollar_dollar = msg
            _t1664 = self.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
            fields1414 = (_dollar_dollar.catalog_uri, _t1664, sorted(_dollar_dollar.properties.items()), sorted(_dollar_dollar.auth_properties.items()),)
            assert fields1414 is not None
            unwrapped_fields1415 = fields1414
            self.write("(iceberg_catalog_config")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("catalog_uri")
            self.newline()
            field1416 = unwrapped_fields1415[0]
            self.write(self.format_string_value(field1416))
            self.dedent()
            self.write(")")
            field1417 = unwrapped_fields1415[1]
            if field1417 is not None:
                self.newline()
                assert field1417 is not None
                opt_val1418 = field1417
                self.pretty_iceberg_catalog_config_scope(opt_val1418)
            self.newline()
            self.write("(")
            self.newline()
            self.write("properties")
            field1419 = unwrapped_fields1415[2]
            if not len(field1419) == 0:
                self.newline()
                for i1421, elem1420 in enumerate(field1419):
                    if (i1421 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1420)
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("auth_properties")
            field1422 = unwrapped_fields1415[3]
            if not len(field1422) == 0:
                self.newline()
                for i1424, elem1423 in enumerate(field1422):
                    if (i1424 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1423)
            self.dedent()
            self.write(")")
            self.dedent()
            self.write(")")

    def pretty_iceberg_catalog_config_scope(self, msg: str):
        flat1427 = self._try_flat(msg, self.pretty_iceberg_catalog_config_scope)
        if flat1427 is not None:
            assert flat1427 is not None
            self.write(flat1427)
            return None
        else:
            fields1426 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1426))
            self.dedent()
            self.write(")")

    def pretty_iceberg_property_entry(self, msg: tuple[str, str]):
        flat1432 = self._try_flat(msg, self.pretty_iceberg_property_entry)
        if flat1432 is not None:
            assert flat1432 is not None
            self.write(flat1432)
            return None
        else:
            _dollar_dollar = msg
            fields1428 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1428 is not None
            unwrapped_fields1429 = fields1428
            self.write("(prop")
            self.indent_sexp()
            self.newline()
            field1430 = unwrapped_fields1429[0]
            self.write(self.format_string_value(field1430))
            self.newline()
            field1431 = unwrapped_fields1429[1]
            self.write(self.format_string_value(field1431))
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1434 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1434 is not None:
            assert flat1434 is not None
            self.write(flat1434)
            return None
        else:
            fields1433 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1433))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1437 = self._try_flat(msg, self.pretty_undefine)
        if flat1437 is not None:
            assert flat1437 is not None
            self.write(flat1437)
            return None
        else:
            _dollar_dollar = msg
            fields1435 = _dollar_dollar.fragment_id
            assert fields1435 is not None
            unwrapped_fields1436 = fields1435
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1436)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1442 = self._try_flat(msg, self.pretty_context)
        if flat1442 is not None:
            assert flat1442 is not None
            self.write(flat1442)
            return None
        else:
            _dollar_dollar = msg
            fields1438 = _dollar_dollar.relations
            assert fields1438 is not None
            unwrapped_fields1439 = fields1438
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1439) == 0:
                self.newline()
                for i1441, elem1440 in enumerate(unwrapped_fields1439):
                    if (i1441 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1440)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1447 = self._try_flat(msg, self.pretty_snapshot)
        if flat1447 is not None:
            assert flat1447 is not None
            self.write(flat1447)
            return None
        else:
            _dollar_dollar = msg
            fields1443 = _dollar_dollar.mappings
            assert fields1443 is not None
            unwrapped_fields1444 = fields1443
            self.write("(snapshot")
            self.indent_sexp()
            if not len(unwrapped_fields1444) == 0:
                self.newline()
                for i1446, elem1445 in enumerate(unwrapped_fields1444):
                    if (i1446 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1445)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1452 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1452 is not None:
            assert flat1452 is not None
            self.write(flat1452)
            return None
        else:
            _dollar_dollar = msg
            fields1448 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1448 is not None
            unwrapped_fields1449 = fields1448
            field1450 = unwrapped_fields1449[0]
            self.pretty_edb_path(field1450)
            self.write(" ")
            field1451 = unwrapped_fields1449[1]
            self.pretty_relation_id(field1451)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1456 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1456 is not None:
            assert flat1456 is not None
            self.write(flat1456)
            return None
        else:
            fields1453 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1453) == 0:
                self.newline()
                for i1455, elem1454 in enumerate(fields1453):
                    if (i1455 > 0):
                        self.newline()
                    self.pretty_read(elem1454)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1467 = self._try_flat(msg, self.pretty_read)
        if flat1467 is not None:
            assert flat1467 is not None
            self.write(flat1467)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1665 = _dollar_dollar.demand
            else:
                _t1665 = None
            deconstruct_result1465 = _t1665
            if deconstruct_result1465 is not None:
                assert deconstruct_result1465 is not None
                unwrapped1466 = deconstruct_result1465
                self.pretty_demand(unwrapped1466)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1666 = _dollar_dollar.output
                else:
                    _t1666 = None
                deconstruct_result1463 = _t1666
                if deconstruct_result1463 is not None:
                    assert deconstruct_result1463 is not None
                    unwrapped1464 = deconstruct_result1463
                    self.pretty_output(unwrapped1464)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1667 = _dollar_dollar.what_if
                    else:
                        _t1667 = None
                    deconstruct_result1461 = _t1667
                    if deconstruct_result1461 is not None:
                        assert deconstruct_result1461 is not None
                        unwrapped1462 = deconstruct_result1461
                        self.pretty_what_if(unwrapped1462)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1668 = _dollar_dollar.abort
                        else:
                            _t1668 = None
                        deconstruct_result1459 = _t1668
                        if deconstruct_result1459 is not None:
                            assert deconstruct_result1459 is not None
                            unwrapped1460 = deconstruct_result1459
                            self.pretty_abort(unwrapped1460)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1669 = _dollar_dollar.export
                            else:
                                _t1669 = None
                            deconstruct_result1457 = _t1669
                            if deconstruct_result1457 is not None:
                                assert deconstruct_result1457 is not None
                                unwrapped1458 = deconstruct_result1457
                                self.pretty_export(unwrapped1458)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1470 = self._try_flat(msg, self.pretty_demand)
        if flat1470 is not None:
            assert flat1470 is not None
            self.write(flat1470)
            return None
        else:
            _dollar_dollar = msg
            fields1468 = _dollar_dollar.relation_id
            assert fields1468 is not None
            unwrapped_fields1469 = fields1468
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1469)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1475 = self._try_flat(msg, self.pretty_output)
        if flat1475 is not None:
            assert flat1475 is not None
            self.write(flat1475)
            return None
        else:
            _dollar_dollar = msg
            fields1471 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1471 is not None
            unwrapped_fields1472 = fields1471
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1473 = unwrapped_fields1472[0]
            self.pretty_name(field1473)
            self.newline()
            field1474 = unwrapped_fields1472[1]
            self.pretty_relation_id(field1474)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1480 = self._try_flat(msg, self.pretty_what_if)
        if flat1480 is not None:
            assert flat1480 is not None
            self.write(flat1480)
            return None
        else:
            _dollar_dollar = msg
            fields1476 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1476 is not None
            unwrapped_fields1477 = fields1476
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1478 = unwrapped_fields1477[0]
            self.pretty_name(field1478)
            self.newline()
            field1479 = unwrapped_fields1477[1]
            self.pretty_epoch(field1479)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1486 = self._try_flat(msg, self.pretty_abort)
        if flat1486 is not None:
            assert flat1486 is not None
            self.write(flat1486)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1670 = _dollar_dollar.name
            else:
                _t1670 = None
            fields1481 = (_t1670, _dollar_dollar.relation_id,)
            assert fields1481 is not None
            unwrapped_fields1482 = fields1481
            self.write("(abort")
            self.indent_sexp()
            field1483 = unwrapped_fields1482[0]
            if field1483 is not None:
                self.newline()
                assert field1483 is not None
                opt_val1484 = field1483
                self.pretty_name(opt_val1484)
            self.newline()
            field1485 = unwrapped_fields1482[1]
            self.pretty_relation_id(field1485)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1491 = self._try_flat(msg, self.pretty_export)
        if flat1491 is not None:
            assert flat1491 is not None
            self.write(flat1491)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1671 = _dollar_dollar.csv_config
            else:
                _t1671 = None
            deconstruct_result1489 = _t1671
            if deconstruct_result1489 is not None:
                assert deconstruct_result1489 is not None
                unwrapped1490 = deconstruct_result1489
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1490)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1672 = _dollar_dollar.iceberg_config
                else:
                    _t1672 = None
                deconstruct_result1487 = _t1672
                if deconstruct_result1487 is not None:
                    assert deconstruct_result1487 is not None
                    unwrapped1488 = deconstruct_result1487
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1488)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1502 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1502 is not None:
            assert flat1502 is not None
            self.write(flat1502)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1673 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1673 = None
            deconstruct_result1497 = _t1673
            if deconstruct_result1497 is not None:
                assert deconstruct_result1497 is not None
                unwrapped1498 = deconstruct_result1497
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1499 = unwrapped1498[0]
                self.pretty_export_csv_path(field1499)
                self.newline()
                field1500 = unwrapped1498[1]
                self.pretty_export_csv_source(field1500)
                self.newline()
                field1501 = unwrapped1498[2]
                self.pretty_csv_config(field1501)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1675 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1674 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1675,)
                else:
                    _t1674 = None
                deconstruct_result1492 = _t1674
                if deconstruct_result1492 is not None:
                    assert deconstruct_result1492 is not None
                    unwrapped1493 = deconstruct_result1492
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1494 = unwrapped1493[0]
                    self.pretty_export_csv_path(field1494)
                    self.newline()
                    field1495 = unwrapped1493[1]
                    self.pretty_export_csv_columns_list(field1495)
                    self.newline()
                    field1496 = unwrapped1493[2]
                    self.pretty_config_dict(field1496)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1504 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1504 is not None:
            assert flat1504 is not None
            self.write(flat1504)
            return None
        else:
            fields1503 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1503))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1511 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1511 is not None:
            assert flat1511 is not None
            self.write(flat1511)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1676 = _dollar_dollar.gnf_columns.columns
            else:
                _t1676 = None
            deconstruct_result1507 = _t1676
            if deconstruct_result1507 is not None:
                assert deconstruct_result1507 is not None
                unwrapped1508 = deconstruct_result1507
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1508) == 0:
                    self.newline()
                    for i1510, elem1509 in enumerate(unwrapped1508):
                        if (i1510 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1509)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1677 = _dollar_dollar.table_def
                else:
                    _t1677 = None
                deconstruct_result1505 = _t1677
                if deconstruct_result1505 is not None:
                    assert deconstruct_result1505 is not None
                    unwrapped1506 = deconstruct_result1505
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1506)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1516 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1516 is not None:
            assert flat1516 is not None
            self.write(flat1516)
            return None
        else:
            _dollar_dollar = msg
            fields1512 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1512 is not None
            unwrapped_fields1513 = fields1512
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1514 = unwrapped_fields1513[0]
            self.write(self.format_string_value(field1514))
            self.newline()
            field1515 = unwrapped_fields1513[1]
            self.pretty_relation_id(field1515)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1520 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1520 is not None:
            assert flat1520 is not None
            self.write(flat1520)
            return None
        else:
            fields1517 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1517) == 0:
                self.newline()
                for i1519, elem1518 in enumerate(fields1517):
                    if (i1519 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1518)
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
            _t1678 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1521 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.table_def, _dollar_dollar.columns, sorted(_dollar_dollar.table_properties.items()), _t1678,)
            assert fields1521 is not None
            unwrapped_fields1522 = fields1521
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            field1523 = unwrapped_fields1522[0]
            self.pretty_iceberg_locator(field1523)
            self.newline()
            field1524 = unwrapped_fields1522[1]
            self.pretty_iceberg_catalog_config(field1524)
            self.newline()
            self.write("(")
            self.newline()
            self.write("table_def")
            self.newline()
            field1525 = unwrapped_fields1522[2]
            self.pretty_relation_id(field1525)
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("columns")
            field1526 = unwrapped_fields1522[3]
            if not len(field1526) == 0:
                self.newline()
                for i1528, elem1527 in enumerate(field1526):
                    if (i1528 > 0):
                        self.newline()
                    self.pretty_export_iceberg_column(elem1527)
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("table_properties")
            field1529 = unwrapped_fields1522[4]
            if not len(field1529) == 0:
                self.newline()
                for i1531, elem1530 in enumerate(field1529):
                    if (i1531 > 0):
                        self.newline()
                    self.pretty_iceberg_property_entry(elem1530)
            self.dedent()
            self.write(")")
            field1532 = unwrapped_fields1522[5]
            if field1532 is not None:
                self.newline()
                assert field1532 is not None
                opt_val1533 = field1532
                self.pretty_config_dict(opt_val1533)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_column(self, msg: transactions_pb2.ExportIcebergColumn):
        flat1539 = self._try_flat(msg, self.pretty_export_iceberg_column)
        if flat1539 is not None:
            assert flat1539 is not None
            self.write(flat1539)
            return None
        else:
            _dollar_dollar = msg
            fields1535 = (_dollar_dollar.name, _dollar_dollar.nullable,)
            assert fields1535 is not None
            unwrapped_fields1536 = fields1535
            self.write("(iceberg_column")
            self.indent_sexp()
            self.newline()
            field1537 = unwrapped_fields1536[0]
            self.write(self.format_string_value(field1537))
            self.newline()
            field1538 = unwrapped_fields1536[1]
            self.pretty_boolean_value(field1538)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1723 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1723)
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
