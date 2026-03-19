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
        _t1597 = logic_pb2.Value(int32_value=v)
        return _t1597

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1598 = logic_pb2.Value(int_value=v)
        return _t1598

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1599 = logic_pb2.Value(float_value=v)
        return _t1599

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1600 = logic_pb2.Value(string_value=v)
        return _t1600

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1601 = logic_pb2.Value(boolean_value=v)
        return _t1601

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1602 = logic_pb2.Value(uint128_value=v)
        return _t1602

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1603 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1603,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1604 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1604,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1605 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1605,))
        _t1606 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1606,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1607 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1607,))
        _t1608 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1608,))
        if msg.new_line != "":
            _t1609 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1609,))
        _t1610 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1610,))
        _t1611 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1611,))
        _t1612 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1612,))
        if msg.comment != "":
            _t1613 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1613,))
        for missing_string in msg.missing_strings:
            _t1614 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1614,))
        _t1615 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1615,))
        _t1616 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1616,))
        _t1617 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1617,))
        if msg.partition_size_mb != 0:
            _t1618 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1618,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1619 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1619,))
        _t1620 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1620,))
        _t1621 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1621,))
        _t1622 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1622,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1623 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1623,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1624 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1624,))
        _t1625 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1625,))
        _t1626 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1626,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1627 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1627,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1628 = self._make_value_string(msg.compression)
            result.append(("compression", _t1628,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1629 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1629,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1630 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1630,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1631 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1631,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1632 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1632,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1633 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1633,))
        return sorted(result)

    def deconstruct_export_iceberg_config_optional(self, msg: transactions_pb2.ExportIcebergConfig) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.prefix is not None
        if msg.prefix != "":
            assert msg.prefix is not None
            _t1634 = self._make_value_string(msg.prefix)
            result.append(("prefix", _t1634,))
        assert msg.target_file_size_bytes is not None
        if msg.target_file_size_bytes != 0:
            assert msg.target_file_size_bytes is not None
            _t1635 = self._make_value_int64(msg.target_file_size_bytes)
            result.append(("target_file_size_bytes", _t1635,))
        if msg.compression != "":
            _t1636 = self._make_value_string(msg.compression)
            result.append(("compression", _t1636,))
        if len(result) == 0:
            return None
        else:
            _t1637 = None
        return sorted(result)

    def deconstruct_iceberg_catalog_properties_optional(self, msg: transactions_pb2.IcebergCatalogProperties) -> Sequence[tuple[str, logic_pb2.Value]] | None:
        result = []
        assert msg.token is not None
        if msg.token != "":
            assert msg.token is not None
            _t1638 = self._make_value_string(msg.token)
            result.append(("token", _t1638,))
        assert msg.credential is not None
        if msg.credential != "":
            assert msg.credential is not None
            _t1639 = self._make_value_string(msg.credential)
            result.append(("credential", _t1639,))
        if len(result) == 0:
            return None
        else:
            _t1640 = None
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
            _t1641 = None
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
        flat739 = self._try_flat(msg, self.pretty_transaction)
        if flat739 is not None:
            assert flat739 is not None
            self.write(flat739)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1460 = _dollar_dollar.configure
            else:
                _t1460 = None
            if _dollar_dollar.HasField("sync"):
                _t1461 = _dollar_dollar.sync
            else:
                _t1461 = None
            fields730 = (_t1460, _t1461, _dollar_dollar.epochs,)
            assert fields730 is not None
            unwrapped_fields731 = fields730
            self.write("(transaction")
            self.indent_sexp()
            field732 = unwrapped_fields731[0]
            if field732 is not None:
                self.newline()
                assert field732 is not None
                opt_val733 = field732
                self.pretty_configure(opt_val733)
            field734 = unwrapped_fields731[1]
            if field734 is not None:
                self.newline()
                assert field734 is not None
                opt_val735 = field734
                self.pretty_sync(opt_val735)
            field736 = unwrapped_fields731[2]
            if not len(field736) == 0:
                self.newline()
                for i738, elem737 in enumerate(field736):
                    if (i738 > 0):
                        self.newline()
                    self.pretty_epoch(elem737)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat742 = self._try_flat(msg, self.pretty_configure)
        if flat742 is not None:
            assert flat742 is not None
            self.write(flat742)
            return None
        else:
            _dollar_dollar = msg
            _t1462 = self.deconstruct_configure(_dollar_dollar)
            fields740 = _t1462
            assert fields740 is not None
            unwrapped_fields741 = fields740
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields741)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat746 = self._try_flat(msg, self.pretty_config_dict)
        if flat746 is not None:
            assert flat746 is not None
            self.write(flat746)
            return None
        else:
            fields743 = msg
            self.write("{")
            self.indent()
            if not len(fields743) == 0:
                self.newline()
                for i745, elem744 in enumerate(fields743):
                    if (i745 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem744)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat751 = self._try_flat(msg, self.pretty_config_key_value)
        if flat751 is not None:
            assert flat751 is not None
            self.write(flat751)
            return None
        else:
            _dollar_dollar = msg
            fields747 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields747 is not None
            unwrapped_fields748 = fields747
            self.write(":")
            field749 = unwrapped_fields748[0]
            self.write(field749)
            self.write(" ")
            field750 = unwrapped_fields748[1]
            self.pretty_raw_value(field750)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat777 = self._try_flat(msg, self.pretty_raw_value)
        if flat777 is not None:
            assert flat777 is not None
            self.write(flat777)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1463 = _dollar_dollar.date_value
            else:
                _t1463 = None
            deconstruct_result775 = _t1463
            if deconstruct_result775 is not None:
                assert deconstruct_result775 is not None
                unwrapped776 = deconstruct_result775
                self.pretty_raw_date(unwrapped776)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1464 = _dollar_dollar.datetime_value
                else:
                    _t1464 = None
                deconstruct_result773 = _t1464
                if deconstruct_result773 is not None:
                    assert deconstruct_result773 is not None
                    unwrapped774 = deconstruct_result773
                    self.pretty_raw_datetime(unwrapped774)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1465 = _dollar_dollar.string_value
                    else:
                        _t1465 = None
                    deconstruct_result771 = _t1465
                    if deconstruct_result771 is not None:
                        assert deconstruct_result771 is not None
                        unwrapped772 = deconstruct_result771
                        self.write(self.format_string_value(unwrapped772))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1466 = _dollar_dollar.int32_value
                        else:
                            _t1466 = None
                        deconstruct_result769 = _t1466
                        if deconstruct_result769 is not None:
                            assert deconstruct_result769 is not None
                            unwrapped770 = deconstruct_result769
                            self.write((str(unwrapped770) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1467 = _dollar_dollar.int_value
                            else:
                                _t1467 = None
                            deconstruct_result767 = _t1467
                            if deconstruct_result767 is not None:
                                assert deconstruct_result767 is not None
                                unwrapped768 = deconstruct_result767
                                self.write(str(unwrapped768))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1468 = _dollar_dollar.float32_value
                                else:
                                    _t1468 = None
                                deconstruct_result765 = _t1468
                                if deconstruct_result765 is not None:
                                    assert deconstruct_result765 is not None
                                    unwrapped766 = deconstruct_result765
                                    self.write(self.format_float32_literal(unwrapped766))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1469 = _dollar_dollar.float_value
                                    else:
                                        _t1469 = None
                                    deconstruct_result763 = _t1469
                                    if deconstruct_result763 is not None:
                                        assert deconstruct_result763 is not None
                                        unwrapped764 = deconstruct_result763
                                        self.write(str(unwrapped764))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1470 = _dollar_dollar.uint32_value
                                        else:
                                            _t1470 = None
                                        deconstruct_result761 = _t1470
                                        if deconstruct_result761 is not None:
                                            assert deconstruct_result761 is not None
                                            unwrapped762 = deconstruct_result761
                                            self.write((str(unwrapped762) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1471 = _dollar_dollar.uint128_value
                                            else:
                                                _t1471 = None
                                            deconstruct_result759 = _t1471
                                            if deconstruct_result759 is not None:
                                                assert deconstruct_result759 is not None
                                                unwrapped760 = deconstruct_result759
                                                self.write(self.format_uint128(unwrapped760))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1472 = _dollar_dollar.int128_value
                                                else:
                                                    _t1472 = None
                                                deconstruct_result757 = _t1472
                                                if deconstruct_result757 is not None:
                                                    assert deconstruct_result757 is not None
                                                    unwrapped758 = deconstruct_result757
                                                    self.write(self.format_int128(unwrapped758))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1473 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1473 = None
                                                    deconstruct_result755 = _t1473
                                                    if deconstruct_result755 is not None:
                                                        assert deconstruct_result755 is not None
                                                        unwrapped756 = deconstruct_result755
                                                        self.write(self.format_decimal(unwrapped756))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1474 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1474 = None
                                                        deconstruct_result753 = _t1474
                                                        if deconstruct_result753 is not None:
                                                            assert deconstruct_result753 is not None
                                                            unwrapped754 = deconstruct_result753
                                                            self.pretty_boolean_value(unwrapped754)
                                                        else:
                                                            fields752 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat783 = self._try_flat(msg, self.pretty_raw_date)
        if flat783 is not None:
            assert flat783 is not None
            self.write(flat783)
            return None
        else:
            _dollar_dollar = msg
            fields778 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields778 is not None
            unwrapped_fields779 = fields778
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field780 = unwrapped_fields779[0]
            self.write(str(field780))
            self.newline()
            field781 = unwrapped_fields779[1]
            self.write(str(field781))
            self.newline()
            field782 = unwrapped_fields779[2]
            self.write(str(field782))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat794 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat794 is not None:
            assert flat794 is not None
            self.write(flat794)
            return None
        else:
            _dollar_dollar = msg
            fields784 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields784 is not None
            unwrapped_fields785 = fields784
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field786 = unwrapped_fields785[0]
            self.write(str(field786))
            self.newline()
            field787 = unwrapped_fields785[1]
            self.write(str(field787))
            self.newline()
            field788 = unwrapped_fields785[2]
            self.write(str(field788))
            self.newline()
            field789 = unwrapped_fields785[3]
            self.write(str(field789))
            self.newline()
            field790 = unwrapped_fields785[4]
            self.write(str(field790))
            self.newline()
            field791 = unwrapped_fields785[5]
            self.write(str(field791))
            field792 = unwrapped_fields785[6]
            if field792 is not None:
                self.newline()
                assert field792 is not None
                opt_val793 = field792
                self.write(str(opt_val793))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1475 = ()
        else:
            _t1475 = None
        deconstruct_result797 = _t1475
        if deconstruct_result797 is not None:
            assert deconstruct_result797 is not None
            unwrapped798 = deconstruct_result797
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1476 = ()
            else:
                _t1476 = None
            deconstruct_result795 = _t1476
            if deconstruct_result795 is not None:
                assert deconstruct_result795 is not None
                unwrapped796 = deconstruct_result795
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat803 = self._try_flat(msg, self.pretty_sync)
        if flat803 is not None:
            assert flat803 is not None
            self.write(flat803)
            return None
        else:
            _dollar_dollar = msg
            fields799 = _dollar_dollar.fragments
            assert fields799 is not None
            unwrapped_fields800 = fields799
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields800) == 0:
                self.newline()
                for i802, elem801 in enumerate(unwrapped_fields800):
                    if (i802 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem801)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat806 = self._try_flat(msg, self.pretty_fragment_id)
        if flat806 is not None:
            assert flat806 is not None
            self.write(flat806)
            return None
        else:
            _dollar_dollar = msg
            fields804 = self.fragment_id_to_string(_dollar_dollar)
            assert fields804 is not None
            unwrapped_fields805 = fields804
            self.write(":")
            self.write(unwrapped_fields805)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat813 = self._try_flat(msg, self.pretty_epoch)
        if flat813 is not None:
            assert flat813 is not None
            self.write(flat813)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1477 = _dollar_dollar.writes
            else:
                _t1477 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1478 = _dollar_dollar.reads
            else:
                _t1478 = None
            fields807 = (_t1477, _t1478,)
            assert fields807 is not None
            unwrapped_fields808 = fields807
            self.write("(epoch")
            self.indent_sexp()
            field809 = unwrapped_fields808[0]
            if field809 is not None:
                self.newline()
                assert field809 is not None
                opt_val810 = field809
                self.pretty_epoch_writes(opt_val810)
            field811 = unwrapped_fields808[1]
            if field811 is not None:
                self.newline()
                assert field811 is not None
                opt_val812 = field811
                self.pretty_epoch_reads(opt_val812)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat817 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat817 is not None:
            assert flat817 is not None
            self.write(flat817)
            return None
        else:
            fields814 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields814) == 0:
                self.newline()
                for i816, elem815 in enumerate(fields814):
                    if (i816 > 0):
                        self.newline()
                    self.pretty_write(elem815)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat826 = self._try_flat(msg, self.pretty_write)
        if flat826 is not None:
            assert flat826 is not None
            self.write(flat826)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1479 = _dollar_dollar.define
            else:
                _t1479 = None
            deconstruct_result824 = _t1479
            if deconstruct_result824 is not None:
                assert deconstruct_result824 is not None
                unwrapped825 = deconstruct_result824
                self.pretty_define(unwrapped825)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1480 = _dollar_dollar.undefine
                else:
                    _t1480 = None
                deconstruct_result822 = _t1480
                if deconstruct_result822 is not None:
                    assert deconstruct_result822 is not None
                    unwrapped823 = deconstruct_result822
                    self.pretty_undefine(unwrapped823)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1481 = _dollar_dollar.context
                    else:
                        _t1481 = None
                    deconstruct_result820 = _t1481
                    if deconstruct_result820 is not None:
                        assert deconstruct_result820 is not None
                        unwrapped821 = deconstruct_result820
                        self.pretty_context(unwrapped821)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1482 = _dollar_dollar.snapshot
                        else:
                            _t1482 = None
                        deconstruct_result818 = _t1482
                        if deconstruct_result818 is not None:
                            assert deconstruct_result818 is not None
                            unwrapped819 = deconstruct_result818
                            self.pretty_snapshot(unwrapped819)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat829 = self._try_flat(msg, self.pretty_define)
        if flat829 is not None:
            assert flat829 is not None
            self.write(flat829)
            return None
        else:
            _dollar_dollar = msg
            fields827 = _dollar_dollar.fragment
            assert fields827 is not None
            unwrapped_fields828 = fields827
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields828)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat836 = self._try_flat(msg, self.pretty_fragment)
        if flat836 is not None:
            assert flat836 is not None
            self.write(flat836)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields830 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields830 is not None
            unwrapped_fields831 = fields830
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field832 = unwrapped_fields831[0]
            self.pretty_new_fragment_id(field832)
            field833 = unwrapped_fields831[1]
            if not len(field833) == 0:
                self.newline()
                for i835, elem834 in enumerate(field833):
                    if (i835 > 0):
                        self.newline()
                    self.pretty_declaration(elem834)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat838 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat838 is not None:
            assert flat838 is not None
            self.write(flat838)
            return None
        else:
            fields837 = msg
            self.pretty_fragment_id(fields837)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat847 = self._try_flat(msg, self.pretty_declaration)
        if flat847 is not None:
            assert flat847 is not None
            self.write(flat847)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1483 = getattr(_dollar_dollar, 'def')
            else:
                _t1483 = None
            deconstruct_result845 = _t1483
            if deconstruct_result845 is not None:
                assert deconstruct_result845 is not None
                unwrapped846 = deconstruct_result845
                self.pretty_def(unwrapped846)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1484 = _dollar_dollar.algorithm
                else:
                    _t1484 = None
                deconstruct_result843 = _t1484
                if deconstruct_result843 is not None:
                    assert deconstruct_result843 is not None
                    unwrapped844 = deconstruct_result843
                    self.pretty_algorithm(unwrapped844)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1485 = _dollar_dollar.constraint
                    else:
                        _t1485 = None
                    deconstruct_result841 = _t1485
                    if deconstruct_result841 is not None:
                        assert deconstruct_result841 is not None
                        unwrapped842 = deconstruct_result841
                        self.pretty_constraint(unwrapped842)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1486 = _dollar_dollar.data
                        else:
                            _t1486 = None
                        deconstruct_result839 = _t1486
                        if deconstruct_result839 is not None:
                            assert deconstruct_result839 is not None
                            unwrapped840 = deconstruct_result839
                            self.pretty_data(unwrapped840)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat854 = self._try_flat(msg, self.pretty_def)
        if flat854 is not None:
            assert flat854 is not None
            self.write(flat854)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1487 = _dollar_dollar.attrs
            else:
                _t1487 = None
            fields848 = (_dollar_dollar.name, _dollar_dollar.body, _t1487,)
            assert fields848 is not None
            unwrapped_fields849 = fields848
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field850 = unwrapped_fields849[0]
            self.pretty_relation_id(field850)
            self.newline()
            field851 = unwrapped_fields849[1]
            self.pretty_abstraction(field851)
            field852 = unwrapped_fields849[2]
            if field852 is not None:
                self.newline()
                assert field852 is not None
                opt_val853 = field852
                self.pretty_attrs(opt_val853)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat859 = self._try_flat(msg, self.pretty_relation_id)
        if flat859 is not None:
            assert flat859 is not None
            self.write(flat859)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1489 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1488 = _t1489
            else:
                _t1488 = None
            deconstruct_result857 = _t1488
            if deconstruct_result857 is not None:
                assert deconstruct_result857 is not None
                unwrapped858 = deconstruct_result857
                self.write(":")
                self.write(unwrapped858)
            else:
                _dollar_dollar = msg
                _t1490 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result855 = _t1490
                if deconstruct_result855 is not None:
                    assert deconstruct_result855 is not None
                    unwrapped856 = deconstruct_result855
                    self.write(self.format_uint128(unwrapped856))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat864 = self._try_flat(msg, self.pretty_abstraction)
        if flat864 is not None:
            assert flat864 is not None
            self.write(flat864)
            return None
        else:
            _dollar_dollar = msg
            _t1491 = self.deconstruct_bindings(_dollar_dollar)
            fields860 = (_t1491, _dollar_dollar.value,)
            assert fields860 is not None
            unwrapped_fields861 = fields860
            self.write("(")
            self.indent()
            field862 = unwrapped_fields861[0]
            self.pretty_bindings(field862)
            self.newline()
            field863 = unwrapped_fields861[1]
            self.pretty_formula(field863)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat872 = self._try_flat(msg, self.pretty_bindings)
        if flat872 is not None:
            assert flat872 is not None
            self.write(flat872)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1492 = _dollar_dollar[1]
            else:
                _t1492 = None
            fields865 = (_dollar_dollar[0], _t1492,)
            assert fields865 is not None
            unwrapped_fields866 = fields865
            self.write("[")
            self.indent()
            field867 = unwrapped_fields866[0]
            for i869, elem868 in enumerate(field867):
                if (i869 > 0):
                    self.newline()
                self.pretty_binding(elem868)
            field870 = unwrapped_fields866[1]
            if field870 is not None:
                self.newline()
                assert field870 is not None
                opt_val871 = field870
                self.pretty_value_bindings(opt_val871)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat877 = self._try_flat(msg, self.pretty_binding)
        if flat877 is not None:
            assert flat877 is not None
            self.write(flat877)
            return None
        else:
            _dollar_dollar = msg
            fields873 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields873 is not None
            unwrapped_fields874 = fields873
            field875 = unwrapped_fields874[0]
            self.write(field875)
            self.write("::")
            field876 = unwrapped_fields874[1]
            self.pretty_type(field876)

    def pretty_type(self, msg: logic_pb2.Type):
        flat906 = self._try_flat(msg, self.pretty_type)
        if flat906 is not None:
            assert flat906 is not None
            self.write(flat906)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1493 = _dollar_dollar.unspecified_type
            else:
                _t1493 = None
            deconstruct_result904 = _t1493
            if deconstruct_result904 is not None:
                assert deconstruct_result904 is not None
                unwrapped905 = deconstruct_result904
                self.pretty_unspecified_type(unwrapped905)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1494 = _dollar_dollar.string_type
                else:
                    _t1494 = None
                deconstruct_result902 = _t1494
                if deconstruct_result902 is not None:
                    assert deconstruct_result902 is not None
                    unwrapped903 = deconstruct_result902
                    self.pretty_string_type(unwrapped903)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1495 = _dollar_dollar.int_type
                    else:
                        _t1495 = None
                    deconstruct_result900 = _t1495
                    if deconstruct_result900 is not None:
                        assert deconstruct_result900 is not None
                        unwrapped901 = deconstruct_result900
                        self.pretty_int_type(unwrapped901)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1496 = _dollar_dollar.float_type
                        else:
                            _t1496 = None
                        deconstruct_result898 = _t1496
                        if deconstruct_result898 is not None:
                            assert deconstruct_result898 is not None
                            unwrapped899 = deconstruct_result898
                            self.pretty_float_type(unwrapped899)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1497 = _dollar_dollar.uint128_type
                            else:
                                _t1497 = None
                            deconstruct_result896 = _t1497
                            if deconstruct_result896 is not None:
                                assert deconstruct_result896 is not None
                                unwrapped897 = deconstruct_result896
                                self.pretty_uint128_type(unwrapped897)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1498 = _dollar_dollar.int128_type
                                else:
                                    _t1498 = None
                                deconstruct_result894 = _t1498
                                if deconstruct_result894 is not None:
                                    assert deconstruct_result894 is not None
                                    unwrapped895 = deconstruct_result894
                                    self.pretty_int128_type(unwrapped895)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1499 = _dollar_dollar.date_type
                                    else:
                                        _t1499 = None
                                    deconstruct_result892 = _t1499
                                    if deconstruct_result892 is not None:
                                        assert deconstruct_result892 is not None
                                        unwrapped893 = deconstruct_result892
                                        self.pretty_date_type(unwrapped893)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1500 = _dollar_dollar.datetime_type
                                        else:
                                            _t1500 = None
                                        deconstruct_result890 = _t1500
                                        if deconstruct_result890 is not None:
                                            assert deconstruct_result890 is not None
                                            unwrapped891 = deconstruct_result890
                                            self.pretty_datetime_type(unwrapped891)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1501 = _dollar_dollar.missing_type
                                            else:
                                                _t1501 = None
                                            deconstruct_result888 = _t1501
                                            if deconstruct_result888 is not None:
                                                assert deconstruct_result888 is not None
                                                unwrapped889 = deconstruct_result888
                                                self.pretty_missing_type(unwrapped889)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1502 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1502 = None
                                                deconstruct_result886 = _t1502
                                                if deconstruct_result886 is not None:
                                                    assert deconstruct_result886 is not None
                                                    unwrapped887 = deconstruct_result886
                                                    self.pretty_decimal_type(unwrapped887)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1503 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1503 = None
                                                    deconstruct_result884 = _t1503
                                                    if deconstruct_result884 is not None:
                                                        assert deconstruct_result884 is not None
                                                        unwrapped885 = deconstruct_result884
                                                        self.pretty_boolean_type(unwrapped885)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1504 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1504 = None
                                                        deconstruct_result882 = _t1504
                                                        if deconstruct_result882 is not None:
                                                            assert deconstruct_result882 is not None
                                                            unwrapped883 = deconstruct_result882
                                                            self.pretty_int32_type(unwrapped883)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1505 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1505 = None
                                                            deconstruct_result880 = _t1505
                                                            if deconstruct_result880 is not None:
                                                                assert deconstruct_result880 is not None
                                                                unwrapped881 = deconstruct_result880
                                                                self.pretty_float32_type(unwrapped881)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1506 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1506 = None
                                                                deconstruct_result878 = _t1506
                                                                if deconstruct_result878 is not None:
                                                                    assert deconstruct_result878 is not None
                                                                    unwrapped879 = deconstruct_result878
                                                                    self.pretty_uint32_type(unwrapped879)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields907 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields908 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields909 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields910 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields911 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields912 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields913 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields914 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields915 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat920 = self._try_flat(msg, self.pretty_decimal_type)
        if flat920 is not None:
            assert flat920 is not None
            self.write(flat920)
            return None
        else:
            _dollar_dollar = msg
            fields916 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields916 is not None
            unwrapped_fields917 = fields916
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field918 = unwrapped_fields917[0]
            self.write(str(field918))
            self.newline()
            field919 = unwrapped_fields917[1]
            self.write(str(field919))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields921 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields922 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields923 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields924 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat928 = self._try_flat(msg, self.pretty_value_bindings)
        if flat928 is not None:
            assert flat928 is not None
            self.write(flat928)
            return None
        else:
            fields925 = msg
            self.write("|")
            if not len(fields925) == 0:
                self.write(" ")
                for i927, elem926 in enumerate(fields925):
                    if (i927 > 0):
                        self.newline()
                    self.pretty_binding(elem926)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat955 = self._try_flat(msg, self.pretty_formula)
        if flat955 is not None:
            assert flat955 is not None
            self.write(flat955)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1507 = _dollar_dollar.conjunction
            else:
                _t1507 = None
            deconstruct_result953 = _t1507
            if deconstruct_result953 is not None:
                assert deconstruct_result953 is not None
                unwrapped954 = deconstruct_result953
                self.pretty_true(unwrapped954)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1508 = _dollar_dollar.disjunction
                else:
                    _t1508 = None
                deconstruct_result951 = _t1508
                if deconstruct_result951 is not None:
                    assert deconstruct_result951 is not None
                    unwrapped952 = deconstruct_result951
                    self.pretty_false(unwrapped952)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1509 = _dollar_dollar.exists
                    else:
                        _t1509 = None
                    deconstruct_result949 = _t1509
                    if deconstruct_result949 is not None:
                        assert deconstruct_result949 is not None
                        unwrapped950 = deconstruct_result949
                        self.pretty_exists(unwrapped950)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1510 = _dollar_dollar.reduce
                        else:
                            _t1510 = None
                        deconstruct_result947 = _t1510
                        if deconstruct_result947 is not None:
                            assert deconstruct_result947 is not None
                            unwrapped948 = deconstruct_result947
                            self.pretty_reduce(unwrapped948)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1511 = _dollar_dollar.conjunction
                            else:
                                _t1511 = None
                            deconstruct_result945 = _t1511
                            if deconstruct_result945 is not None:
                                assert deconstruct_result945 is not None
                                unwrapped946 = deconstruct_result945
                                self.pretty_conjunction(unwrapped946)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1512 = _dollar_dollar.disjunction
                                else:
                                    _t1512 = None
                                deconstruct_result943 = _t1512
                                if deconstruct_result943 is not None:
                                    assert deconstruct_result943 is not None
                                    unwrapped944 = deconstruct_result943
                                    self.pretty_disjunction(unwrapped944)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1513 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1513 = None
                                    deconstruct_result941 = _t1513
                                    if deconstruct_result941 is not None:
                                        assert deconstruct_result941 is not None
                                        unwrapped942 = deconstruct_result941
                                        self.pretty_not(unwrapped942)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1514 = _dollar_dollar.ffi
                                        else:
                                            _t1514 = None
                                        deconstruct_result939 = _t1514
                                        if deconstruct_result939 is not None:
                                            assert deconstruct_result939 is not None
                                            unwrapped940 = deconstruct_result939
                                            self.pretty_ffi(unwrapped940)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1515 = _dollar_dollar.atom
                                            else:
                                                _t1515 = None
                                            deconstruct_result937 = _t1515
                                            if deconstruct_result937 is not None:
                                                assert deconstruct_result937 is not None
                                                unwrapped938 = deconstruct_result937
                                                self.pretty_atom(unwrapped938)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1516 = _dollar_dollar.pragma
                                                else:
                                                    _t1516 = None
                                                deconstruct_result935 = _t1516
                                                if deconstruct_result935 is not None:
                                                    assert deconstruct_result935 is not None
                                                    unwrapped936 = deconstruct_result935
                                                    self.pretty_pragma(unwrapped936)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1517 = _dollar_dollar.primitive
                                                    else:
                                                        _t1517 = None
                                                    deconstruct_result933 = _t1517
                                                    if deconstruct_result933 is not None:
                                                        assert deconstruct_result933 is not None
                                                        unwrapped934 = deconstruct_result933
                                                        self.pretty_primitive(unwrapped934)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1518 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1518 = None
                                                        deconstruct_result931 = _t1518
                                                        if deconstruct_result931 is not None:
                                                            assert deconstruct_result931 is not None
                                                            unwrapped932 = deconstruct_result931
                                                            self.pretty_rel_atom(unwrapped932)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1519 = _dollar_dollar.cast
                                                            else:
                                                                _t1519 = None
                                                            deconstruct_result929 = _t1519
                                                            if deconstruct_result929 is not None:
                                                                assert deconstruct_result929 is not None
                                                                unwrapped930 = deconstruct_result929
                                                                self.pretty_cast(unwrapped930)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields956 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields957 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat962 = self._try_flat(msg, self.pretty_exists)
        if flat962 is not None:
            assert flat962 is not None
            self.write(flat962)
            return None
        else:
            _dollar_dollar = msg
            _t1520 = self.deconstruct_bindings(_dollar_dollar.body)
            fields958 = (_t1520, _dollar_dollar.body.value,)
            assert fields958 is not None
            unwrapped_fields959 = fields958
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field960 = unwrapped_fields959[0]
            self.pretty_bindings(field960)
            self.newline()
            field961 = unwrapped_fields959[1]
            self.pretty_formula(field961)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat968 = self._try_flat(msg, self.pretty_reduce)
        if flat968 is not None:
            assert flat968 is not None
            self.write(flat968)
            return None
        else:
            _dollar_dollar = msg
            fields963 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields963 is not None
            unwrapped_fields964 = fields963
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field965 = unwrapped_fields964[0]
            self.pretty_abstraction(field965)
            self.newline()
            field966 = unwrapped_fields964[1]
            self.pretty_abstraction(field966)
            self.newline()
            field967 = unwrapped_fields964[2]
            self.pretty_terms(field967)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat972 = self._try_flat(msg, self.pretty_terms)
        if flat972 is not None:
            assert flat972 is not None
            self.write(flat972)
            return None
        else:
            fields969 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields969) == 0:
                self.newline()
                for i971, elem970 in enumerate(fields969):
                    if (i971 > 0):
                        self.newline()
                    self.pretty_term(elem970)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat977 = self._try_flat(msg, self.pretty_term)
        if flat977 is not None:
            assert flat977 is not None
            self.write(flat977)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1521 = _dollar_dollar.var
            else:
                _t1521 = None
            deconstruct_result975 = _t1521
            if deconstruct_result975 is not None:
                assert deconstruct_result975 is not None
                unwrapped976 = deconstruct_result975
                self.pretty_var(unwrapped976)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1522 = _dollar_dollar.constant
                else:
                    _t1522 = None
                deconstruct_result973 = _t1522
                if deconstruct_result973 is not None:
                    assert deconstruct_result973 is not None
                    unwrapped974 = deconstruct_result973
                    self.pretty_value(unwrapped974)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat980 = self._try_flat(msg, self.pretty_var)
        if flat980 is not None:
            assert flat980 is not None
            self.write(flat980)
            return None
        else:
            _dollar_dollar = msg
            fields978 = _dollar_dollar.name
            assert fields978 is not None
            unwrapped_fields979 = fields978
            self.write(unwrapped_fields979)

    def pretty_value(self, msg: logic_pb2.Value):
        flat1006 = self._try_flat(msg, self.pretty_value)
        if flat1006 is not None:
            assert flat1006 is not None
            self.write(flat1006)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1523 = _dollar_dollar.date_value
            else:
                _t1523 = None
            deconstruct_result1004 = _t1523
            if deconstruct_result1004 is not None:
                assert deconstruct_result1004 is not None
                unwrapped1005 = deconstruct_result1004
                self.pretty_date(unwrapped1005)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1524 = _dollar_dollar.datetime_value
                else:
                    _t1524 = None
                deconstruct_result1002 = _t1524
                if deconstruct_result1002 is not None:
                    assert deconstruct_result1002 is not None
                    unwrapped1003 = deconstruct_result1002
                    self.pretty_datetime(unwrapped1003)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1525 = _dollar_dollar.string_value
                    else:
                        _t1525 = None
                    deconstruct_result1000 = _t1525
                    if deconstruct_result1000 is not None:
                        assert deconstruct_result1000 is not None
                        unwrapped1001 = deconstruct_result1000
                        self.write(self.format_string_value(unwrapped1001))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1526 = _dollar_dollar.int32_value
                        else:
                            _t1526 = None
                        deconstruct_result998 = _t1526
                        if deconstruct_result998 is not None:
                            assert deconstruct_result998 is not None
                            unwrapped999 = deconstruct_result998
                            self.write((str(unwrapped999) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1527 = _dollar_dollar.int_value
                            else:
                                _t1527 = None
                            deconstruct_result996 = _t1527
                            if deconstruct_result996 is not None:
                                assert deconstruct_result996 is not None
                                unwrapped997 = deconstruct_result996
                                self.write(str(unwrapped997))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1528 = _dollar_dollar.float32_value
                                else:
                                    _t1528 = None
                                deconstruct_result994 = _t1528
                                if deconstruct_result994 is not None:
                                    assert deconstruct_result994 is not None
                                    unwrapped995 = deconstruct_result994
                                    self.write(self.format_float32_literal(unwrapped995))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1529 = _dollar_dollar.float_value
                                    else:
                                        _t1529 = None
                                    deconstruct_result992 = _t1529
                                    if deconstruct_result992 is not None:
                                        assert deconstruct_result992 is not None
                                        unwrapped993 = deconstruct_result992
                                        self.write(str(unwrapped993))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1530 = _dollar_dollar.uint32_value
                                        else:
                                            _t1530 = None
                                        deconstruct_result990 = _t1530
                                        if deconstruct_result990 is not None:
                                            assert deconstruct_result990 is not None
                                            unwrapped991 = deconstruct_result990
                                            self.write((str(unwrapped991) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1531 = _dollar_dollar.uint128_value
                                            else:
                                                _t1531 = None
                                            deconstruct_result988 = _t1531
                                            if deconstruct_result988 is not None:
                                                assert deconstruct_result988 is not None
                                                unwrapped989 = deconstruct_result988
                                                self.write(self.format_uint128(unwrapped989))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1532 = _dollar_dollar.int128_value
                                                else:
                                                    _t1532 = None
                                                deconstruct_result986 = _t1532
                                                if deconstruct_result986 is not None:
                                                    assert deconstruct_result986 is not None
                                                    unwrapped987 = deconstruct_result986
                                                    self.write(self.format_int128(unwrapped987))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1533 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1533 = None
                                                    deconstruct_result984 = _t1533
                                                    if deconstruct_result984 is not None:
                                                        assert deconstruct_result984 is not None
                                                        unwrapped985 = deconstruct_result984
                                                        self.write(self.format_decimal(unwrapped985))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1534 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1534 = None
                                                        deconstruct_result982 = _t1534
                                                        if deconstruct_result982 is not None:
                                                            assert deconstruct_result982 is not None
                                                            unwrapped983 = deconstruct_result982
                                                            self.pretty_boolean_value(unwrapped983)
                                                        else:
                                                            fields981 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat1012 = self._try_flat(msg, self.pretty_date)
        if flat1012 is not None:
            assert flat1012 is not None
            self.write(flat1012)
            return None
        else:
            _dollar_dollar = msg
            fields1007 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields1007 is not None
            unwrapped_fields1008 = fields1007
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field1009 = unwrapped_fields1008[0]
            self.write(str(field1009))
            self.newline()
            field1010 = unwrapped_fields1008[1]
            self.write(str(field1010))
            self.newline()
            field1011 = unwrapped_fields1008[2]
            self.write(str(field1011))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1023 = self._try_flat(msg, self.pretty_datetime)
        if flat1023 is not None:
            assert flat1023 is not None
            self.write(flat1023)
            return None
        else:
            _dollar_dollar = msg
            fields1013 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields1013 is not None
            unwrapped_fields1014 = fields1013
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field1015 = unwrapped_fields1014[0]
            self.write(str(field1015))
            self.newline()
            field1016 = unwrapped_fields1014[1]
            self.write(str(field1016))
            self.newline()
            field1017 = unwrapped_fields1014[2]
            self.write(str(field1017))
            self.newline()
            field1018 = unwrapped_fields1014[3]
            self.write(str(field1018))
            self.newline()
            field1019 = unwrapped_fields1014[4]
            self.write(str(field1019))
            self.newline()
            field1020 = unwrapped_fields1014[5]
            self.write(str(field1020))
            field1021 = unwrapped_fields1014[6]
            if field1021 is not None:
                self.newline()
                assert field1021 is not None
                opt_val1022 = field1021
                self.write(str(opt_val1022))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1028 = self._try_flat(msg, self.pretty_conjunction)
        if flat1028 is not None:
            assert flat1028 is not None
            self.write(flat1028)
            return None
        else:
            _dollar_dollar = msg
            fields1024 = _dollar_dollar.args
            assert fields1024 is not None
            unwrapped_fields1025 = fields1024
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1025) == 0:
                self.newline()
                for i1027, elem1026 in enumerate(unwrapped_fields1025):
                    if (i1027 > 0):
                        self.newline()
                    self.pretty_formula(elem1026)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1033 = self._try_flat(msg, self.pretty_disjunction)
        if flat1033 is not None:
            assert flat1033 is not None
            self.write(flat1033)
            return None
        else:
            _dollar_dollar = msg
            fields1029 = _dollar_dollar.args
            assert fields1029 is not None
            unwrapped_fields1030 = fields1029
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1030) == 0:
                self.newline()
                for i1032, elem1031 in enumerate(unwrapped_fields1030):
                    if (i1032 > 0):
                        self.newline()
                    self.pretty_formula(elem1031)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1036 = self._try_flat(msg, self.pretty_not)
        if flat1036 is not None:
            assert flat1036 is not None
            self.write(flat1036)
            return None
        else:
            _dollar_dollar = msg
            fields1034 = _dollar_dollar.arg
            assert fields1034 is not None
            unwrapped_fields1035 = fields1034
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1035)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1042 = self._try_flat(msg, self.pretty_ffi)
        if flat1042 is not None:
            assert flat1042 is not None
            self.write(flat1042)
            return None
        else:
            _dollar_dollar = msg
            fields1037 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1037 is not None
            unwrapped_fields1038 = fields1037
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1039 = unwrapped_fields1038[0]
            self.pretty_name(field1039)
            self.newline()
            field1040 = unwrapped_fields1038[1]
            self.pretty_ffi_args(field1040)
            self.newline()
            field1041 = unwrapped_fields1038[2]
            self.pretty_terms(field1041)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1044 = self._try_flat(msg, self.pretty_name)
        if flat1044 is not None:
            assert flat1044 is not None
            self.write(flat1044)
            return None
        else:
            fields1043 = msg
            self.write(":")
            self.write(fields1043)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1048 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1048 is not None:
            assert flat1048 is not None
            self.write(flat1048)
            return None
        else:
            fields1045 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1045) == 0:
                self.newline()
                for i1047, elem1046 in enumerate(fields1045):
                    if (i1047 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1046)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1055 = self._try_flat(msg, self.pretty_atom)
        if flat1055 is not None:
            assert flat1055 is not None
            self.write(flat1055)
            return None
        else:
            _dollar_dollar = msg
            fields1049 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1049 is not None
            unwrapped_fields1050 = fields1049
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1051 = unwrapped_fields1050[0]
            self.pretty_relation_id(field1051)
            field1052 = unwrapped_fields1050[1]
            if not len(field1052) == 0:
                self.newline()
                for i1054, elem1053 in enumerate(field1052):
                    if (i1054 > 0):
                        self.newline()
                    self.pretty_term(elem1053)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1062 = self._try_flat(msg, self.pretty_pragma)
        if flat1062 is not None:
            assert flat1062 is not None
            self.write(flat1062)
            return None
        else:
            _dollar_dollar = msg
            fields1056 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1056 is not None
            unwrapped_fields1057 = fields1056
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1058 = unwrapped_fields1057[0]
            self.pretty_name(field1058)
            field1059 = unwrapped_fields1057[1]
            if not len(field1059) == 0:
                self.newline()
                for i1061, elem1060 in enumerate(field1059):
                    if (i1061 > 0):
                        self.newline()
                    self.pretty_term(elem1060)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1078 = self._try_flat(msg, self.pretty_primitive)
        if flat1078 is not None:
            assert flat1078 is not None
            self.write(flat1078)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1535 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1535 = None
            guard_result1077 = _t1535
            if guard_result1077 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1536 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1536 = None
                guard_result1076 = _t1536
                if guard_result1076 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1537 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1537 = None
                    guard_result1075 = _t1537
                    if guard_result1075 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1538 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1538 = None
                        guard_result1074 = _t1538
                        if guard_result1074 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1539 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1539 = None
                            guard_result1073 = _t1539
                            if guard_result1073 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1540 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1540 = None
                                guard_result1072 = _t1540
                                if guard_result1072 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1541 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1541 = None
                                    guard_result1071 = _t1541
                                    if guard_result1071 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1542 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1542 = None
                                        guard_result1070 = _t1542
                                        if guard_result1070 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1543 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1543 = None
                                            guard_result1069 = _t1543
                                            if guard_result1069 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1063 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1063 is not None
                                                unwrapped_fields1064 = fields1063
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1065 = unwrapped_fields1064[0]
                                                self.pretty_name(field1065)
                                                field1066 = unwrapped_fields1064[1]
                                                if not len(field1066) == 0:
                                                    self.newline()
                                                    for i1068, elem1067 in enumerate(field1066):
                                                        if (i1068 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1067)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1083 = self._try_flat(msg, self.pretty_eq)
        if flat1083 is not None:
            assert flat1083 is not None
            self.write(flat1083)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1544 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1544 = None
            fields1079 = _t1544
            assert fields1079 is not None
            unwrapped_fields1080 = fields1079
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1081 = unwrapped_fields1080[0]
            self.pretty_term(field1081)
            self.newline()
            field1082 = unwrapped_fields1080[1]
            self.pretty_term(field1082)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1088 = self._try_flat(msg, self.pretty_lt)
        if flat1088 is not None:
            assert flat1088 is not None
            self.write(flat1088)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1545 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1545 = None
            fields1084 = _t1545
            assert fields1084 is not None
            unwrapped_fields1085 = fields1084
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1086 = unwrapped_fields1085[0]
            self.pretty_term(field1086)
            self.newline()
            field1087 = unwrapped_fields1085[1]
            self.pretty_term(field1087)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1093 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1093 is not None:
            assert flat1093 is not None
            self.write(flat1093)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1546 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1546 = None
            fields1089 = _t1546
            assert fields1089 is not None
            unwrapped_fields1090 = fields1089
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1091 = unwrapped_fields1090[0]
            self.pretty_term(field1091)
            self.newline()
            field1092 = unwrapped_fields1090[1]
            self.pretty_term(field1092)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1098 = self._try_flat(msg, self.pretty_gt)
        if flat1098 is not None:
            assert flat1098 is not None
            self.write(flat1098)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1547 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1547 = None
            fields1094 = _t1547
            assert fields1094 is not None
            unwrapped_fields1095 = fields1094
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1096 = unwrapped_fields1095[0]
            self.pretty_term(field1096)
            self.newline()
            field1097 = unwrapped_fields1095[1]
            self.pretty_term(field1097)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1103 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1103 is not None:
            assert flat1103 is not None
            self.write(flat1103)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1548 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1548 = None
            fields1099 = _t1548
            assert fields1099 is not None
            unwrapped_fields1100 = fields1099
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1101 = unwrapped_fields1100[0]
            self.pretty_term(field1101)
            self.newline()
            field1102 = unwrapped_fields1100[1]
            self.pretty_term(field1102)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1109 = self._try_flat(msg, self.pretty_add)
        if flat1109 is not None:
            assert flat1109 is not None
            self.write(flat1109)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1549 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1549 = None
            fields1104 = _t1549
            assert fields1104 is not None
            unwrapped_fields1105 = fields1104
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1106 = unwrapped_fields1105[0]
            self.pretty_term(field1106)
            self.newline()
            field1107 = unwrapped_fields1105[1]
            self.pretty_term(field1107)
            self.newline()
            field1108 = unwrapped_fields1105[2]
            self.pretty_term(field1108)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1115 = self._try_flat(msg, self.pretty_minus)
        if flat1115 is not None:
            assert flat1115 is not None
            self.write(flat1115)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1550 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1550 = None
            fields1110 = _t1550
            assert fields1110 is not None
            unwrapped_fields1111 = fields1110
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1112 = unwrapped_fields1111[0]
            self.pretty_term(field1112)
            self.newline()
            field1113 = unwrapped_fields1111[1]
            self.pretty_term(field1113)
            self.newline()
            field1114 = unwrapped_fields1111[2]
            self.pretty_term(field1114)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1121 = self._try_flat(msg, self.pretty_multiply)
        if flat1121 is not None:
            assert flat1121 is not None
            self.write(flat1121)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1551 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1551 = None
            fields1116 = _t1551
            assert fields1116 is not None
            unwrapped_fields1117 = fields1116
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1118 = unwrapped_fields1117[0]
            self.pretty_term(field1118)
            self.newline()
            field1119 = unwrapped_fields1117[1]
            self.pretty_term(field1119)
            self.newline()
            field1120 = unwrapped_fields1117[2]
            self.pretty_term(field1120)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1127 = self._try_flat(msg, self.pretty_divide)
        if flat1127 is not None:
            assert flat1127 is not None
            self.write(flat1127)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1552 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1552 = None
            fields1122 = _t1552
            assert fields1122 is not None
            unwrapped_fields1123 = fields1122
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1124 = unwrapped_fields1123[0]
            self.pretty_term(field1124)
            self.newline()
            field1125 = unwrapped_fields1123[1]
            self.pretty_term(field1125)
            self.newline()
            field1126 = unwrapped_fields1123[2]
            self.pretty_term(field1126)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1132 = self._try_flat(msg, self.pretty_rel_term)
        if flat1132 is not None:
            assert flat1132 is not None
            self.write(flat1132)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1553 = _dollar_dollar.specialized_value
            else:
                _t1553 = None
            deconstruct_result1130 = _t1553
            if deconstruct_result1130 is not None:
                assert deconstruct_result1130 is not None
                unwrapped1131 = deconstruct_result1130
                self.pretty_specialized_value(unwrapped1131)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1554 = _dollar_dollar.term
                else:
                    _t1554 = None
                deconstruct_result1128 = _t1554
                if deconstruct_result1128 is not None:
                    assert deconstruct_result1128 is not None
                    unwrapped1129 = deconstruct_result1128
                    self.pretty_term(unwrapped1129)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1134 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1134 is not None:
            assert flat1134 is not None
            self.write(flat1134)
            return None
        else:
            fields1133 = msg
            self.write("#")
            self.pretty_raw_value(fields1133)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1141 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1141 is not None:
            assert flat1141 is not None
            self.write(flat1141)
            return None
        else:
            _dollar_dollar = msg
            fields1135 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1135 is not None
            unwrapped_fields1136 = fields1135
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1137 = unwrapped_fields1136[0]
            self.pretty_name(field1137)
            field1138 = unwrapped_fields1136[1]
            if not len(field1138) == 0:
                self.newline()
                for i1140, elem1139 in enumerate(field1138):
                    if (i1140 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1139)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1146 = self._try_flat(msg, self.pretty_cast)
        if flat1146 is not None:
            assert flat1146 is not None
            self.write(flat1146)
            return None
        else:
            _dollar_dollar = msg
            fields1142 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1142 is not None
            unwrapped_fields1143 = fields1142
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1144 = unwrapped_fields1143[0]
            self.pretty_term(field1144)
            self.newline()
            field1145 = unwrapped_fields1143[1]
            self.pretty_term(field1145)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1150 = self._try_flat(msg, self.pretty_attrs)
        if flat1150 is not None:
            assert flat1150 is not None
            self.write(flat1150)
            return None
        else:
            fields1147 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1147) == 0:
                self.newline()
                for i1149, elem1148 in enumerate(fields1147):
                    if (i1149 > 0):
                        self.newline()
                    self.pretty_attribute(elem1148)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1157 = self._try_flat(msg, self.pretty_attribute)
        if flat1157 is not None:
            assert flat1157 is not None
            self.write(flat1157)
            return None
        else:
            _dollar_dollar = msg
            fields1151 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1151 is not None
            unwrapped_fields1152 = fields1151
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1153 = unwrapped_fields1152[0]
            self.pretty_name(field1153)
            field1154 = unwrapped_fields1152[1]
            if not len(field1154) == 0:
                self.newline()
                for i1156, elem1155 in enumerate(field1154):
                    if (i1156 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1155)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1164 = self._try_flat(msg, self.pretty_algorithm)
        if flat1164 is not None:
            assert flat1164 is not None
            self.write(flat1164)
            return None
        else:
            _dollar_dollar = msg
            fields1158 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            assert fields1158 is not None
            unwrapped_fields1159 = fields1158
            self.write("(algorithm")
            self.indent_sexp()
            field1160 = unwrapped_fields1159[0]
            if not len(field1160) == 0:
                self.newline()
                for i1162, elem1161 in enumerate(field1160):
                    if (i1162 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1161)
            self.newline()
            field1163 = unwrapped_fields1159[1]
            self.pretty_script(field1163)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1169 = self._try_flat(msg, self.pretty_script)
        if flat1169 is not None:
            assert flat1169 is not None
            self.write(flat1169)
            return None
        else:
            _dollar_dollar = msg
            fields1165 = _dollar_dollar.constructs
            assert fields1165 is not None
            unwrapped_fields1166 = fields1165
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1166) == 0:
                self.newline()
                for i1168, elem1167 in enumerate(unwrapped_fields1166):
                    if (i1168 > 0):
                        self.newline()
                    self.pretty_construct(elem1167)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1174 = self._try_flat(msg, self.pretty_construct)
        if flat1174 is not None:
            assert flat1174 is not None
            self.write(flat1174)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1555 = _dollar_dollar.loop
            else:
                _t1555 = None
            deconstruct_result1172 = _t1555
            if deconstruct_result1172 is not None:
                assert deconstruct_result1172 is not None
                unwrapped1173 = deconstruct_result1172
                self.pretty_loop(unwrapped1173)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1556 = _dollar_dollar.instruction
                else:
                    _t1556 = None
                deconstruct_result1170 = _t1556
                if deconstruct_result1170 is not None:
                    assert deconstruct_result1170 is not None
                    unwrapped1171 = deconstruct_result1170
                    self.pretty_instruction(unwrapped1171)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1179 = self._try_flat(msg, self.pretty_loop)
        if flat1179 is not None:
            assert flat1179 is not None
            self.write(flat1179)
            return None
        else:
            _dollar_dollar = msg
            fields1175 = (_dollar_dollar.init, _dollar_dollar.body,)
            assert fields1175 is not None
            unwrapped_fields1176 = fields1175
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1177 = unwrapped_fields1176[0]
            self.pretty_init(field1177)
            self.newline()
            field1178 = unwrapped_fields1176[1]
            self.pretty_script(field1178)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1183 = self._try_flat(msg, self.pretty_init)
        if flat1183 is not None:
            assert flat1183 is not None
            self.write(flat1183)
            return None
        else:
            fields1180 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1180) == 0:
                self.newline()
                for i1182, elem1181 in enumerate(fields1180):
                    if (i1182 > 0):
                        self.newline()
                    self.pretty_instruction(elem1181)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1194 = self._try_flat(msg, self.pretty_instruction)
        if flat1194 is not None:
            assert flat1194 is not None
            self.write(flat1194)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1557 = _dollar_dollar.assign
            else:
                _t1557 = None
            deconstruct_result1192 = _t1557
            if deconstruct_result1192 is not None:
                assert deconstruct_result1192 is not None
                unwrapped1193 = deconstruct_result1192
                self.pretty_assign(unwrapped1193)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1558 = _dollar_dollar.upsert
                else:
                    _t1558 = None
                deconstruct_result1190 = _t1558
                if deconstruct_result1190 is not None:
                    assert deconstruct_result1190 is not None
                    unwrapped1191 = deconstruct_result1190
                    self.pretty_upsert(unwrapped1191)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1559 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1559 = None
                    deconstruct_result1188 = _t1559
                    if deconstruct_result1188 is not None:
                        assert deconstruct_result1188 is not None
                        unwrapped1189 = deconstruct_result1188
                        self.pretty_break(unwrapped1189)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1560 = _dollar_dollar.monoid_def
                        else:
                            _t1560 = None
                        deconstruct_result1186 = _t1560
                        if deconstruct_result1186 is not None:
                            assert deconstruct_result1186 is not None
                            unwrapped1187 = deconstruct_result1186
                            self.pretty_monoid_def(unwrapped1187)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1561 = _dollar_dollar.monus_def
                            else:
                                _t1561 = None
                            deconstruct_result1184 = _t1561
                            if deconstruct_result1184 is not None:
                                assert deconstruct_result1184 is not None
                                unwrapped1185 = deconstruct_result1184
                                self.pretty_monus_def(unwrapped1185)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1201 = self._try_flat(msg, self.pretty_assign)
        if flat1201 is not None:
            assert flat1201 is not None
            self.write(flat1201)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1562 = _dollar_dollar.attrs
            else:
                _t1562 = None
            fields1195 = (_dollar_dollar.name, _dollar_dollar.body, _t1562,)
            assert fields1195 is not None
            unwrapped_fields1196 = fields1195
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1197 = unwrapped_fields1196[0]
            self.pretty_relation_id(field1197)
            self.newline()
            field1198 = unwrapped_fields1196[1]
            self.pretty_abstraction(field1198)
            field1199 = unwrapped_fields1196[2]
            if field1199 is not None:
                self.newline()
                assert field1199 is not None
                opt_val1200 = field1199
                self.pretty_attrs(opt_val1200)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1208 = self._try_flat(msg, self.pretty_upsert)
        if flat1208 is not None:
            assert flat1208 is not None
            self.write(flat1208)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1563 = _dollar_dollar.attrs
            else:
                _t1563 = None
            fields1202 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1563,)
            assert fields1202 is not None
            unwrapped_fields1203 = fields1202
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1204 = unwrapped_fields1203[0]
            self.pretty_relation_id(field1204)
            self.newline()
            field1205 = unwrapped_fields1203[1]
            self.pretty_abstraction_with_arity(field1205)
            field1206 = unwrapped_fields1203[2]
            if field1206 is not None:
                self.newline()
                assert field1206 is not None
                opt_val1207 = field1206
                self.pretty_attrs(opt_val1207)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1213 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1213 is not None:
            assert flat1213 is not None
            self.write(flat1213)
            return None
        else:
            _dollar_dollar = msg
            _t1564 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1209 = (_t1564, _dollar_dollar[0].value,)
            assert fields1209 is not None
            unwrapped_fields1210 = fields1209
            self.write("(")
            self.indent()
            field1211 = unwrapped_fields1210[0]
            self.pretty_bindings(field1211)
            self.newline()
            field1212 = unwrapped_fields1210[1]
            self.pretty_formula(field1212)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1220 = self._try_flat(msg, self.pretty_break)
        if flat1220 is not None:
            assert flat1220 is not None
            self.write(flat1220)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1565 = _dollar_dollar.attrs
            else:
                _t1565 = None
            fields1214 = (_dollar_dollar.name, _dollar_dollar.body, _t1565,)
            assert fields1214 is not None
            unwrapped_fields1215 = fields1214
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1216 = unwrapped_fields1215[0]
            self.pretty_relation_id(field1216)
            self.newline()
            field1217 = unwrapped_fields1215[1]
            self.pretty_abstraction(field1217)
            field1218 = unwrapped_fields1215[2]
            if field1218 is not None:
                self.newline()
                assert field1218 is not None
                opt_val1219 = field1218
                self.pretty_attrs(opt_val1219)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1228 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1228 is not None:
            assert flat1228 is not None
            self.write(flat1228)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1566 = _dollar_dollar.attrs
            else:
                _t1566 = None
            fields1221 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1566,)
            assert fields1221 is not None
            unwrapped_fields1222 = fields1221
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1223 = unwrapped_fields1222[0]
            self.pretty_monoid(field1223)
            self.newline()
            field1224 = unwrapped_fields1222[1]
            self.pretty_relation_id(field1224)
            self.newline()
            field1225 = unwrapped_fields1222[2]
            self.pretty_abstraction_with_arity(field1225)
            field1226 = unwrapped_fields1222[3]
            if field1226 is not None:
                self.newline()
                assert field1226 is not None
                opt_val1227 = field1226
                self.pretty_attrs(opt_val1227)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1237 = self._try_flat(msg, self.pretty_monoid)
        if flat1237 is not None:
            assert flat1237 is not None
            self.write(flat1237)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1567 = _dollar_dollar.or_monoid
            else:
                _t1567 = None
            deconstruct_result1235 = _t1567
            if deconstruct_result1235 is not None:
                assert deconstruct_result1235 is not None
                unwrapped1236 = deconstruct_result1235
                self.pretty_or_monoid(unwrapped1236)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1568 = _dollar_dollar.min_monoid
                else:
                    _t1568 = None
                deconstruct_result1233 = _t1568
                if deconstruct_result1233 is not None:
                    assert deconstruct_result1233 is not None
                    unwrapped1234 = deconstruct_result1233
                    self.pretty_min_monoid(unwrapped1234)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1569 = _dollar_dollar.max_monoid
                    else:
                        _t1569 = None
                    deconstruct_result1231 = _t1569
                    if deconstruct_result1231 is not None:
                        assert deconstruct_result1231 is not None
                        unwrapped1232 = deconstruct_result1231
                        self.pretty_max_monoid(unwrapped1232)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1570 = _dollar_dollar.sum_monoid
                        else:
                            _t1570 = None
                        deconstruct_result1229 = _t1570
                        if deconstruct_result1229 is not None:
                            assert deconstruct_result1229 is not None
                            unwrapped1230 = deconstruct_result1229
                            self.pretty_sum_monoid(unwrapped1230)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1238 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1241 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1241 is not None:
            assert flat1241 is not None
            self.write(flat1241)
            return None
        else:
            _dollar_dollar = msg
            fields1239 = _dollar_dollar.type
            assert fields1239 is not None
            unwrapped_fields1240 = fields1239
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1240)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1244 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1244 is not None:
            assert flat1244 is not None
            self.write(flat1244)
            return None
        else:
            _dollar_dollar = msg
            fields1242 = _dollar_dollar.type
            assert fields1242 is not None
            unwrapped_fields1243 = fields1242
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1243)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1247 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1247 is not None:
            assert flat1247 is not None
            self.write(flat1247)
            return None
        else:
            _dollar_dollar = msg
            fields1245 = _dollar_dollar.type
            assert fields1245 is not None
            unwrapped_fields1246 = fields1245
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1246)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1255 = self._try_flat(msg, self.pretty_monus_def)
        if flat1255 is not None:
            assert flat1255 is not None
            self.write(flat1255)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1571 = _dollar_dollar.attrs
            else:
                _t1571 = None
            fields1248 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1571,)
            assert fields1248 is not None
            unwrapped_fields1249 = fields1248
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1250 = unwrapped_fields1249[0]
            self.pretty_monoid(field1250)
            self.newline()
            field1251 = unwrapped_fields1249[1]
            self.pretty_relation_id(field1251)
            self.newline()
            field1252 = unwrapped_fields1249[2]
            self.pretty_abstraction_with_arity(field1252)
            field1253 = unwrapped_fields1249[3]
            if field1253 is not None:
                self.newline()
                assert field1253 is not None
                opt_val1254 = field1253
                self.pretty_attrs(opt_val1254)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1262 = self._try_flat(msg, self.pretty_constraint)
        if flat1262 is not None:
            assert flat1262 is not None
            self.write(flat1262)
            return None
        else:
            _dollar_dollar = msg
            fields1256 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1256 is not None
            unwrapped_fields1257 = fields1256
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1258 = unwrapped_fields1257[0]
            self.pretty_relation_id(field1258)
            self.newline()
            field1259 = unwrapped_fields1257[1]
            self.pretty_abstraction(field1259)
            self.newline()
            field1260 = unwrapped_fields1257[2]
            self.pretty_functional_dependency_keys(field1260)
            self.newline()
            field1261 = unwrapped_fields1257[3]
            self.pretty_functional_dependency_values(field1261)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1266 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1266 is not None:
            assert flat1266 is not None
            self.write(flat1266)
            return None
        else:
            fields1263 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1263) == 0:
                self.newline()
                for i1265, elem1264 in enumerate(fields1263):
                    if (i1265 > 0):
                        self.newline()
                    self.pretty_var(elem1264)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1270 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1270 is not None:
            assert flat1270 is not None
            self.write(flat1270)
            return None
        else:
            fields1267 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1267) == 0:
                self.newline()
                for i1269, elem1268 in enumerate(fields1267):
                    if (i1269 > 0):
                        self.newline()
                    self.pretty_var(elem1268)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1277 = self._try_flat(msg, self.pretty_data)
        if flat1277 is not None:
            assert flat1277 is not None
            self.write(flat1277)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1572 = _dollar_dollar.edb
            else:
                _t1572 = None
            deconstruct_result1275 = _t1572
            if deconstruct_result1275 is not None:
                assert deconstruct_result1275 is not None
                unwrapped1276 = deconstruct_result1275
                self.pretty_edb(unwrapped1276)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1573 = _dollar_dollar.betree_relation
                else:
                    _t1573 = None
                deconstruct_result1273 = _t1573
                if deconstruct_result1273 is not None:
                    assert deconstruct_result1273 is not None
                    unwrapped1274 = deconstruct_result1273
                    self.pretty_betree_relation(unwrapped1274)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1574 = _dollar_dollar.csv_data
                    else:
                        _t1574 = None
                    deconstruct_result1271 = _t1574
                    if deconstruct_result1271 is not None:
                        assert deconstruct_result1271 is not None
                        unwrapped1272 = deconstruct_result1271
                        self.pretty_csv_data(unwrapped1272)
                    else:
                        raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1283 = self._try_flat(msg, self.pretty_edb)
        if flat1283 is not None:
            assert flat1283 is not None
            self.write(flat1283)
            return None
        else:
            _dollar_dollar = msg
            fields1278 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1278 is not None
            unwrapped_fields1279 = fields1278
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1280 = unwrapped_fields1279[0]
            self.pretty_relation_id(field1280)
            self.newline()
            field1281 = unwrapped_fields1279[1]
            self.pretty_edb_path(field1281)
            self.newline()
            field1282 = unwrapped_fields1279[2]
            self.pretty_edb_types(field1282)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1287 = self._try_flat(msg, self.pretty_edb_path)
        if flat1287 is not None:
            assert flat1287 is not None
            self.write(flat1287)
            return None
        else:
            fields1284 = msg
            self.write("[")
            self.indent()
            for i1286, elem1285 in enumerate(fields1284):
                if (i1286 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1285))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1291 = self._try_flat(msg, self.pretty_edb_types)
        if flat1291 is not None:
            assert flat1291 is not None
            self.write(flat1291)
            return None
        else:
            fields1288 = msg
            self.write("[")
            self.indent()
            for i1290, elem1289 in enumerate(fields1288):
                if (i1290 > 0):
                    self.newline()
                self.pretty_type(elem1289)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1296 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1296 is not None:
            assert flat1296 is not None
            self.write(flat1296)
            return None
        else:
            _dollar_dollar = msg
            fields1292 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1292 is not None
            unwrapped_fields1293 = fields1292
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1294 = unwrapped_fields1293[0]
            self.pretty_relation_id(field1294)
            self.newline()
            field1295 = unwrapped_fields1293[1]
            self.pretty_betree_info(field1295)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1302 = self._try_flat(msg, self.pretty_betree_info)
        if flat1302 is not None:
            assert flat1302 is not None
            self.write(flat1302)
            return None
        else:
            _dollar_dollar = msg
            _t1575 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1297 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1575,)
            assert fields1297 is not None
            unwrapped_fields1298 = fields1297
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1299 = unwrapped_fields1298[0]
            self.pretty_betree_info_key_types(field1299)
            self.newline()
            field1300 = unwrapped_fields1298[1]
            self.pretty_betree_info_value_types(field1300)
            self.newline()
            field1301 = unwrapped_fields1298[2]
            self.pretty_config_dict(field1301)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1306 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1306 is not None:
            assert flat1306 is not None
            self.write(flat1306)
            return None
        else:
            fields1303 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1303) == 0:
                self.newline()
                for i1305, elem1304 in enumerate(fields1303):
                    if (i1305 > 0):
                        self.newline()
                    self.pretty_type(elem1304)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1310 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1310 is not None:
            assert flat1310 is not None
            self.write(flat1310)
            return None
        else:
            fields1307 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1307) == 0:
                self.newline()
                for i1309, elem1308 in enumerate(fields1307):
                    if (i1309 > 0):
                        self.newline()
                    self.pretty_type(elem1308)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1317 = self._try_flat(msg, self.pretty_csv_data)
        if flat1317 is not None:
            assert flat1317 is not None
            self.write(flat1317)
            return None
        else:
            _dollar_dollar = msg
            fields1311 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1311 is not None
            unwrapped_fields1312 = fields1311
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1313 = unwrapped_fields1312[0]
            self.pretty_csvlocator(field1313)
            self.newline()
            field1314 = unwrapped_fields1312[1]
            self.pretty_csv_config(field1314)
            self.newline()
            field1315 = unwrapped_fields1312[2]
            self.pretty_gnf_columns(field1315)
            self.newline()
            field1316 = unwrapped_fields1312[3]
            self.pretty_csv_asof(field1316)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1324 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1324 is not None:
            assert flat1324 is not None
            self.write(flat1324)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1576 = _dollar_dollar.paths
            else:
                _t1576 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1577 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1577 = None
            fields1318 = (_t1576, _t1577,)
            assert fields1318 is not None
            unwrapped_fields1319 = fields1318
            self.write("(csv_locator")
            self.indent_sexp()
            field1320 = unwrapped_fields1319[0]
            if field1320 is not None:
                self.newline()
                assert field1320 is not None
                opt_val1321 = field1320
                self.pretty_csv_locator_paths(opt_val1321)
            field1322 = unwrapped_fields1319[1]
            if field1322 is not None:
                self.newline()
                assert field1322 is not None
                opt_val1323 = field1322
                self.pretty_csv_locator_inline_data(opt_val1323)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1328 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1328 is not None:
            assert flat1328 is not None
            self.write(flat1328)
            return None
        else:
            fields1325 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1325) == 0:
                self.newline()
                for i1327, elem1326 in enumerate(fields1325):
                    if (i1327 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1326))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1330 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1330 is not None:
            assert flat1330 is not None
            self.write(flat1330)
            return None
        else:
            fields1329 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1329))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1333 = self._try_flat(msg, self.pretty_csv_config)
        if flat1333 is not None:
            assert flat1333 is not None
            self.write(flat1333)
            return None
        else:
            _dollar_dollar = msg
            _t1578 = self.deconstruct_csv_config(_dollar_dollar)
            fields1331 = _t1578
            assert fields1331 is not None
            unwrapped_fields1332 = fields1331
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1332)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1337 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1337 is not None:
            assert flat1337 is not None
            self.write(flat1337)
            return None
        else:
            fields1334 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1334) == 0:
                self.newline()
                for i1336, elem1335 in enumerate(fields1334):
                    if (i1336 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1335)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1346 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1346 is not None:
            assert flat1346 is not None
            self.write(flat1346)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1579 = _dollar_dollar.target_id
            else:
                _t1579 = None
            fields1338 = (_dollar_dollar.column_path, _t1579, _dollar_dollar.types,)
            assert fields1338 is not None
            unwrapped_fields1339 = fields1338
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1340 = unwrapped_fields1339[0]
            self.pretty_gnf_column_path(field1340)
            field1341 = unwrapped_fields1339[1]
            if field1341 is not None:
                self.newline()
                assert field1341 is not None
                opt_val1342 = field1341
                self.pretty_relation_id(opt_val1342)
            self.newline()
            self.write("[")
            field1343 = unwrapped_fields1339[2]
            for i1345, elem1344 in enumerate(field1343):
                if (i1345 > 0):
                    self.newline()
                self.pretty_type(elem1344)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1353 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1353 is not None:
            assert flat1353 is not None
            self.write(flat1353)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1580 = _dollar_dollar[0]
            else:
                _t1580 = None
            deconstruct_result1351 = _t1580
            if deconstruct_result1351 is not None:
                assert deconstruct_result1351 is not None
                unwrapped1352 = deconstruct_result1351
                self.write(self.format_string_value(unwrapped1352))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1581 = _dollar_dollar
                else:
                    _t1581 = None
                deconstruct_result1347 = _t1581
                if deconstruct_result1347 is not None:
                    assert deconstruct_result1347 is not None
                    unwrapped1348 = deconstruct_result1347
                    self.write("[")
                    self.indent()
                    for i1350, elem1349 in enumerate(unwrapped1348):
                        if (i1350 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1349))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1355 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1355 is not None:
            assert flat1355 is not None
            self.write(flat1355)
            return None
        else:
            fields1354 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1354))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1358 = self._try_flat(msg, self.pretty_undefine)
        if flat1358 is not None:
            assert flat1358 is not None
            self.write(flat1358)
            return None
        else:
            _dollar_dollar = msg
            fields1356 = _dollar_dollar.fragment_id
            assert fields1356 is not None
            unwrapped_fields1357 = fields1356
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1357)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1363 = self._try_flat(msg, self.pretty_context)
        if flat1363 is not None:
            assert flat1363 is not None
            self.write(flat1363)
            return None
        else:
            _dollar_dollar = msg
            fields1359 = _dollar_dollar.relations
            assert fields1359 is not None
            unwrapped_fields1360 = fields1359
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1360) == 0:
                self.newline()
                for i1362, elem1361 in enumerate(unwrapped_fields1360):
                    if (i1362 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1361)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1368 = self._try_flat(msg, self.pretty_snapshot)
        if flat1368 is not None:
            assert flat1368 is not None
            self.write(flat1368)
            return None
        else:
            _dollar_dollar = msg
            fields1364 = _dollar_dollar.mappings
            assert fields1364 is not None
            unwrapped_fields1365 = fields1364
            self.write("(snapshot")
            self.indent_sexp()
            if not len(unwrapped_fields1365) == 0:
                self.newline()
                for i1367, elem1366 in enumerate(unwrapped_fields1365):
                    if (i1367 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1366)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1373 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1373 is not None:
            assert flat1373 is not None
            self.write(flat1373)
            return None
        else:
            _dollar_dollar = msg
            fields1369 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1369 is not None
            unwrapped_fields1370 = fields1369
            field1371 = unwrapped_fields1370[0]
            self.pretty_edb_path(field1371)
            self.write(" ")
            field1372 = unwrapped_fields1370[1]
            self.pretty_relation_id(field1372)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1377 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1377 is not None:
            assert flat1377 is not None
            self.write(flat1377)
            return None
        else:
            fields1374 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1374) == 0:
                self.newline()
                for i1376, elem1375 in enumerate(fields1374):
                    if (i1376 > 0):
                        self.newline()
                    self.pretty_read(elem1375)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1388 = self._try_flat(msg, self.pretty_read)
        if flat1388 is not None:
            assert flat1388 is not None
            self.write(flat1388)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1582 = _dollar_dollar.demand
            else:
                _t1582 = None
            deconstruct_result1386 = _t1582
            if deconstruct_result1386 is not None:
                assert deconstruct_result1386 is not None
                unwrapped1387 = deconstruct_result1386
                self.pretty_demand(unwrapped1387)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1583 = _dollar_dollar.output
                else:
                    _t1583 = None
                deconstruct_result1384 = _t1583
                if deconstruct_result1384 is not None:
                    assert deconstruct_result1384 is not None
                    unwrapped1385 = deconstruct_result1384
                    self.pretty_output(unwrapped1385)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1584 = _dollar_dollar.what_if
                    else:
                        _t1584 = None
                    deconstruct_result1382 = _t1584
                    if deconstruct_result1382 is not None:
                        assert deconstruct_result1382 is not None
                        unwrapped1383 = deconstruct_result1382
                        self.pretty_what_if(unwrapped1383)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1585 = _dollar_dollar.abort
                        else:
                            _t1585 = None
                        deconstruct_result1380 = _t1585
                        if deconstruct_result1380 is not None:
                            assert deconstruct_result1380 is not None
                            unwrapped1381 = deconstruct_result1380
                            self.pretty_abort(unwrapped1381)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1586 = _dollar_dollar.export
                            else:
                                _t1586 = None
                            deconstruct_result1378 = _t1586
                            if deconstruct_result1378 is not None:
                                assert deconstruct_result1378 is not None
                                unwrapped1379 = deconstruct_result1378
                                self.pretty_export(unwrapped1379)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1391 = self._try_flat(msg, self.pretty_demand)
        if flat1391 is not None:
            assert flat1391 is not None
            self.write(flat1391)
            return None
        else:
            _dollar_dollar = msg
            fields1389 = _dollar_dollar.relation_id
            assert fields1389 is not None
            unwrapped_fields1390 = fields1389
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1390)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1396 = self._try_flat(msg, self.pretty_output)
        if flat1396 is not None:
            assert flat1396 is not None
            self.write(flat1396)
            return None
        else:
            _dollar_dollar = msg
            fields1392 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1392 is not None
            unwrapped_fields1393 = fields1392
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1394 = unwrapped_fields1393[0]
            self.pretty_name(field1394)
            self.newline()
            field1395 = unwrapped_fields1393[1]
            self.pretty_relation_id(field1395)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1401 = self._try_flat(msg, self.pretty_what_if)
        if flat1401 is not None:
            assert flat1401 is not None
            self.write(flat1401)
            return None
        else:
            _dollar_dollar = msg
            fields1397 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1397 is not None
            unwrapped_fields1398 = fields1397
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1399 = unwrapped_fields1398[0]
            self.pretty_name(field1399)
            self.newline()
            field1400 = unwrapped_fields1398[1]
            self.pretty_epoch(field1400)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1407 = self._try_flat(msg, self.pretty_abort)
        if flat1407 is not None:
            assert flat1407 is not None
            self.write(flat1407)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1587 = _dollar_dollar.name
            else:
                _t1587 = None
            fields1402 = (_t1587, _dollar_dollar.relation_id,)
            assert fields1402 is not None
            unwrapped_fields1403 = fields1402
            self.write("(abort")
            self.indent_sexp()
            field1404 = unwrapped_fields1403[0]
            if field1404 is not None:
                self.newline()
                assert field1404 is not None
                opt_val1405 = field1404
                self.pretty_name(opt_val1405)
            self.newline()
            field1406 = unwrapped_fields1403[1]
            self.pretty_relation_id(field1406)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1412 = self._try_flat(msg, self.pretty_export)
        if flat1412 is not None:
            assert flat1412 is not None
            self.write(flat1412)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("csv_config"):
                _t1588 = _dollar_dollar.csv_config
            else:
                _t1588 = None
            deconstruct_result1410 = _t1588
            if deconstruct_result1410 is not None:
                assert deconstruct_result1410 is not None
                unwrapped1411 = deconstruct_result1410
                self.write("(export")
                self.indent_sexp()
                self.newline()
                self.pretty_export_csv_config(unwrapped1411)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("iceberg_config"):
                    _t1589 = _dollar_dollar.iceberg_config
                else:
                    _t1589 = None
                deconstruct_result1408 = _t1589
                if deconstruct_result1408 is not None:
                    assert deconstruct_result1408 is not None
                    unwrapped1409 = deconstruct_result1408
                    self.write("(export_iceberg")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_export_iceberg_config(unwrapped1409)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1423 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1423 is not None:
            assert flat1423 is not None
            self.write(flat1423)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1590 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1590 = None
            deconstruct_result1418 = _t1590
            if deconstruct_result1418 is not None:
                assert deconstruct_result1418 is not None
                unwrapped1419 = deconstruct_result1418
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1420 = unwrapped1419[0]
                self.pretty_export_csv_path(field1420)
                self.newline()
                field1421 = unwrapped1419[1]
                self.pretty_export_csv_source(field1421)
                self.newline()
                field1422 = unwrapped1419[2]
                self.pretty_csv_config(field1422)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1592 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1591 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1592,)
                else:
                    _t1591 = None
                deconstruct_result1413 = _t1591
                if deconstruct_result1413 is not None:
                    assert deconstruct_result1413 is not None
                    unwrapped1414 = deconstruct_result1413
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1415 = unwrapped1414[0]
                    self.pretty_export_csv_path(field1415)
                    self.newline()
                    field1416 = unwrapped1414[1]
                    self.pretty_export_csv_columns_list(field1416)
                    self.newline()
                    field1417 = unwrapped1414[2]
                    self.pretty_config_dict(field1417)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1425 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1425 is not None:
            assert flat1425 is not None
            self.write(flat1425)
            return None
        else:
            fields1424 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1424))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1432 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1432 is not None:
            assert flat1432 is not None
            self.write(flat1432)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1593 = _dollar_dollar.gnf_columns.columns
            else:
                _t1593 = None
            deconstruct_result1428 = _t1593
            if deconstruct_result1428 is not None:
                assert deconstruct_result1428 is not None
                unwrapped1429 = deconstruct_result1428
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1429) == 0:
                    self.newline()
                    for i1431, elem1430 in enumerate(unwrapped1429):
                        if (i1431 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1430)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1594 = _dollar_dollar.table_def
                else:
                    _t1594 = None
                deconstruct_result1426 = _t1594
                if deconstruct_result1426 is not None:
                    assert deconstruct_result1426 is not None
                    unwrapped1427 = deconstruct_result1426
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1427)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1437 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1437 is not None:
            assert flat1437 is not None
            self.write(flat1437)
            return None
        else:
            _dollar_dollar = msg
            fields1433 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1433 is not None
            unwrapped_fields1434 = fields1433
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1435 = unwrapped_fields1434[0]
            self.write(self.format_string_value(field1435))
            self.newline()
            field1436 = unwrapped_fields1434[1]
            self.pretty_relation_id(field1436)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1441 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1441 is not None:
            assert flat1441 is not None
            self.write(flat1441)
            return None
        else:
            fields1438 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1438) == 0:
                self.newline()
                for i1440, elem1439 in enumerate(fields1438):
                    if (i1440 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1439)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_config(self, msg: transactions_pb2.ExportIcebergConfig):
        flat1453 = self._try_flat(msg, self.pretty_export_iceberg_config)
        if flat1453 is not None:
            assert flat1453 is not None
            self.write(flat1453)
            return None
        else:
            _dollar_dollar = msg
            _t1595 = self.deconstruct_export_iceberg_config_optional(_dollar_dollar)
            fields1442 = (_dollar_dollar.catalog_uri, _dollar_dollar.namespace, _dollar_dollar.table_name, _dollar_dollar.catalog_properties, _dollar_dollar.schema, _t1595,)
            assert fields1442 is not None
            unwrapped_fields1443 = fields1442
            self.write("(export_iceberg_config")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("catalog_uri")
            self.newline()
            field1444 = unwrapped_fields1443[0]
            self.write(self.format_string_value(field1444))
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("namespace")
            field1445 = unwrapped_fields1443[1]
            if not len(field1445) == 0:
                self.newline()
                for i1447, elem1446 in enumerate(field1445):
                    if (i1447 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1446))
            self.dedent()
            self.write(")")
            self.newline()
            self.write("(")
            self.newline()
            self.write("table_name")
            self.newline()
            field1448 = unwrapped_fields1443[2]
            self.write(self.format_string_value(field1448))
            self.dedent()
            self.write(")")
            self.newline()
            field1449 = unwrapped_fields1443[3]
            self.pretty_export_iceberg_catalog_properties(field1449)
            self.newline()
            self.write("(")
            self.newline()
            self.write("schema")
            self.newline()
            field1450 = unwrapped_fields1443[4]
            self.write(self.format_string_value(field1450))
            self.dedent()
            self.write(")")
            field1451 = unwrapped_fields1443[5]
            if field1451 is not None:
                self.newline()
                assert field1451 is not None
                opt_val1452 = field1451
                self.pretty_config_dict(opt_val1452)
            self.dedent()
            self.write(")")

    def pretty_export_iceberg_catalog_properties(self, msg: transactions_pb2.IcebergCatalogProperties):
        flat1459 = self._try_flat(msg, self.pretty_export_iceberg_catalog_properties)
        if flat1459 is not None:
            assert flat1459 is not None
            self.write(flat1459)
            return None
        else:
            _dollar_dollar = msg
            _t1596 = self.deconstruct_iceberg_catalog_properties_optional(_dollar_dollar)
            fields1454 = (_dollar_dollar.warehouse, _t1596,)
            assert fields1454 is not None
            unwrapped_fields1455 = fields1454
            self.write("(catalog_properties")
            self.indent_sexp()
            self.newline()
            self.write("(")
            self.newline()
            self.write("warehouse")
            self.newline()
            field1456 = unwrapped_fields1455[0]
            self.write(self.format_string_value(field1456))
            self.dedent()
            self.write(")")
            field1457 = unwrapped_fields1455[1]
            if field1457 is not None:
                self.newline()
                assert field1457 is not None
                opt_val1458 = field1457
                self.pretty_config_dict(opt_val1458)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1642 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1642)
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
        elif isinstance(msg, transactions_pb2.IcebergCatalogProperties):
            self.pretty_export_iceberg_catalog_properties(msg)
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
