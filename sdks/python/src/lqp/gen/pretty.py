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
        """Format a float32 value at 32-bit precision."""
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
        _t1557 = logic_pb2.Value(int32_value=v)
        return _t1557

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1558 = logic_pb2.Value(int_value=v)
        return _t1558

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1559 = logic_pb2.Value(float_value=v)
        return _t1559

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1560 = logic_pb2.Value(string_value=v)
        return _t1560

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1561 = logic_pb2.Value(boolean_value=v)
        return _t1561

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1562 = logic_pb2.Value(uint128_value=v)
        return _t1562

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1563 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1563,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1564 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1564,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1565 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1565,))
        _t1566 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1566,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1567 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1567,))
        _t1568 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1568,))
        if msg.new_line != "":
            _t1569 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1569,))
        _t1570 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1570,))
        _t1571 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1571,))
        _t1572 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1572,))
        if msg.comment != "":
            _t1573 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1573,))
        for missing_string in msg.missing_strings:
            _t1574 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1574,))
        _t1575 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1575,))
        _t1576 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1576,))
        _t1577 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1577,))
        if msg.partition_size_mb != 0:
            _t1578 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1578,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1579 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1579,))
        _t1580 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1580,))
        _t1581 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1581,))
        _t1582 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1582,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1583 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1583,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1584 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1584,))
        _t1585 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1585,))
        _t1586 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1586,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1587 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1587,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1588 = self._make_value_string(msg.compression)
            result.append(("compression", _t1588,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1589 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1589,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1590 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1590,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1591 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1591,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1592 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1592,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1593 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1593,))
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
            _t1594 = None
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
        flat725 = self._try_flat(msg, self.pretty_transaction)
        if flat725 is not None:
            assert flat725 is not None
            self.write(flat725)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1432 = _dollar_dollar.configure
            else:
                _t1432 = None
            if _dollar_dollar.HasField("sync"):
                _t1433 = _dollar_dollar.sync
            else:
                _t1433 = None
            fields716 = (_t1432, _t1433, _dollar_dollar.epochs,)
            assert fields716 is not None
            unwrapped_fields717 = fields716
            self.write("(transaction")
            self.indent_sexp()
            field718 = unwrapped_fields717[0]
            if field718 is not None:
                self.newline()
                assert field718 is not None
                opt_val719 = field718
                self.pretty_configure(opt_val719)
            field720 = unwrapped_fields717[1]
            if field720 is not None:
                self.newline()
                assert field720 is not None
                opt_val721 = field720
                self.pretty_sync(opt_val721)
            field722 = unwrapped_fields717[2]
            if not len(field722) == 0:
                self.newline()
                for i724, elem723 in enumerate(field722):
                    if (i724 > 0):
                        self.newline()
                    self.pretty_epoch(elem723)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat728 = self._try_flat(msg, self.pretty_configure)
        if flat728 is not None:
            assert flat728 is not None
            self.write(flat728)
            return None
        else:
            _dollar_dollar = msg
            _t1434 = self.deconstruct_configure(_dollar_dollar)
            fields726 = _t1434
            assert fields726 is not None
            unwrapped_fields727 = fields726
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields727)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat732 = self._try_flat(msg, self.pretty_config_dict)
        if flat732 is not None:
            assert flat732 is not None
            self.write(flat732)
            return None
        else:
            fields729 = msg
            self.write("{")
            self.indent()
            if not len(fields729) == 0:
                self.newline()
                for i731, elem730 in enumerate(fields729):
                    if (i731 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem730)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat737 = self._try_flat(msg, self.pretty_config_key_value)
        if flat737 is not None:
            assert flat737 is not None
            self.write(flat737)
            return None
        else:
            _dollar_dollar = msg
            fields733 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields733 is not None
            unwrapped_fields734 = fields733
            self.write(":")
            field735 = unwrapped_fields734[0]
            self.write(field735)
            self.write(" ")
            field736 = unwrapped_fields734[1]
            self.pretty_value(field736)

    def pretty_value(self, msg: logic_pb2.Value):
        flat763 = self._try_flat(msg, self.pretty_value)
        if flat763 is not None:
            assert flat763 is not None
            self.write(flat763)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1435 = _dollar_dollar.date_value
            else:
                _t1435 = None
            deconstruct_result761 = _t1435
            if deconstruct_result761 is not None:
                assert deconstruct_result761 is not None
                unwrapped762 = deconstruct_result761
                self.pretty_date(unwrapped762)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1436 = _dollar_dollar.datetime_value
                else:
                    _t1436 = None
                deconstruct_result759 = _t1436
                if deconstruct_result759 is not None:
                    assert deconstruct_result759 is not None
                    unwrapped760 = deconstruct_result759
                    self.pretty_datetime(unwrapped760)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1437 = _dollar_dollar.string_value
                    else:
                        _t1437 = None
                    deconstruct_result757 = _t1437
                    if deconstruct_result757 is not None:
                        assert deconstruct_result757 is not None
                        unwrapped758 = deconstruct_result757
                        self.write(self.format_string_value(unwrapped758))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int_value"):
                            _t1438 = _dollar_dollar.int_value
                        else:
                            _t1438 = None
                        deconstruct_result755 = _t1438
                        if deconstruct_result755 is not None:
                            assert deconstruct_result755 is not None
                            unwrapped756 = deconstruct_result755
                            self.write(str(unwrapped756))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("float_value"):
                                _t1439 = _dollar_dollar.float_value
                            else:
                                _t1439 = None
                            deconstruct_result753 = _t1439
                            if deconstruct_result753 is not None:
                                assert deconstruct_result753 is not None
                                unwrapped754 = deconstruct_result753
                                self.write(str(unwrapped754))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("uint128_value"):
                                    _t1440 = _dollar_dollar.uint128_value
                                else:
                                    _t1440 = None
                                deconstruct_result751 = _t1440
                                if deconstruct_result751 is not None:
                                    assert deconstruct_result751 is not None
                                    unwrapped752 = deconstruct_result751
                                    self.write(self.format_uint128(unwrapped752))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("int128_value"):
                                        _t1441 = _dollar_dollar.int128_value
                                    else:
                                        _t1441 = None
                                    deconstruct_result749 = _t1441
                                    if deconstruct_result749 is not None:
                                        assert deconstruct_result749 is not None
                                        unwrapped750 = deconstruct_result749
                                        self.write(self.format_int128(unwrapped750))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("decimal_value"):
                                            _t1442 = _dollar_dollar.decimal_value
                                        else:
                                            _t1442 = None
                                        deconstruct_result747 = _t1442
                                        if deconstruct_result747 is not None:
                                            assert deconstruct_result747 is not None
                                            unwrapped748 = deconstruct_result747
                                            self.write(self.format_decimal(unwrapped748))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("boolean_value"):
                                                _t1443 = _dollar_dollar.boolean_value
                                            else:
                                                _t1443 = None
                                            deconstruct_result745 = _t1443
                                            if deconstruct_result745 is not None:
                                                assert deconstruct_result745 is not None
                                                unwrapped746 = deconstruct_result745
                                                self.pretty_boolean_value(unwrapped746)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int32_value"):
                                                    _t1444 = _dollar_dollar.int32_value
                                                else:
                                                    _t1444 = None
                                                deconstruct_result743 = _t1444
                                                if deconstruct_result743 is not None:
                                                    assert deconstruct_result743 is not None
                                                    unwrapped744 = deconstruct_result743
                                                    self.write((str(unwrapped744) + 'i32'))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("float32_value"):
                                                        _t1445 = _dollar_dollar.float32_value
                                                    else:
                                                        _t1445 = None
                                                    deconstruct_result741 = _t1445
                                                    if deconstruct_result741 is not None:
                                                        assert deconstruct_result741 is not None
                                                        unwrapped742 = deconstruct_result741
                                                        self.write((self.format_float32_value(unwrapped742) + 'f32'))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("uint32_value"):
                                                            _t1446 = _dollar_dollar.uint32_value
                                                        else:
                                                            _t1446 = None
                                                        deconstruct_result739 = _t1446
                                                        if deconstruct_result739 is not None:
                                                            assert deconstruct_result739 is not None
                                                            unwrapped740 = deconstruct_result739
                                                            self.write((str(unwrapped740) + 'u32'))
                                                        else:
                                                            fields738 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat769 = self._try_flat(msg, self.pretty_date)
        if flat769 is not None:
            assert flat769 is not None
            self.write(flat769)
            return None
        else:
            _dollar_dollar = msg
            fields764 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields764 is not None
            unwrapped_fields765 = fields764
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field766 = unwrapped_fields765[0]
            self.write(str(field766))
            self.newline()
            field767 = unwrapped_fields765[1]
            self.write(str(field767))
            self.newline()
            field768 = unwrapped_fields765[2]
            self.write(str(field768))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat780 = self._try_flat(msg, self.pretty_datetime)
        if flat780 is not None:
            assert flat780 is not None
            self.write(flat780)
            return None
        else:
            _dollar_dollar = msg
            fields770 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields770 is not None
            unwrapped_fields771 = fields770
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field772 = unwrapped_fields771[0]
            self.write(str(field772))
            self.newline()
            field773 = unwrapped_fields771[1]
            self.write(str(field773))
            self.newline()
            field774 = unwrapped_fields771[2]
            self.write(str(field774))
            self.newline()
            field775 = unwrapped_fields771[3]
            self.write(str(field775))
            self.newline()
            field776 = unwrapped_fields771[4]
            self.write(str(field776))
            self.newline()
            field777 = unwrapped_fields771[5]
            self.write(str(field777))
            field778 = unwrapped_fields771[6]
            if field778 is not None:
                self.newline()
                assert field778 is not None
                opt_val779 = field778
                self.write(str(opt_val779))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1447 = ()
        else:
            _t1447 = None
        deconstruct_result783 = _t1447
        if deconstruct_result783 is not None:
            assert deconstruct_result783 is not None
            unwrapped784 = deconstruct_result783
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1448 = ()
            else:
                _t1448 = None
            deconstruct_result781 = _t1448
            if deconstruct_result781 is not None:
                assert deconstruct_result781 is not None
                unwrapped782 = deconstruct_result781
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat789 = self._try_flat(msg, self.pretty_sync)
        if flat789 is not None:
            assert flat789 is not None
            self.write(flat789)
            return None
        else:
            _dollar_dollar = msg
            fields785 = _dollar_dollar.fragments
            assert fields785 is not None
            unwrapped_fields786 = fields785
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields786) == 0:
                self.newline()
                for i788, elem787 in enumerate(unwrapped_fields786):
                    if (i788 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem787)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat792 = self._try_flat(msg, self.pretty_fragment_id)
        if flat792 is not None:
            assert flat792 is not None
            self.write(flat792)
            return None
        else:
            _dollar_dollar = msg
            fields790 = self.fragment_id_to_string(_dollar_dollar)
            assert fields790 is not None
            unwrapped_fields791 = fields790
            self.write(":")
            self.write(unwrapped_fields791)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat799 = self._try_flat(msg, self.pretty_epoch)
        if flat799 is not None:
            assert flat799 is not None
            self.write(flat799)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1449 = _dollar_dollar.writes
            else:
                _t1449 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1450 = _dollar_dollar.reads
            else:
                _t1450 = None
            fields793 = (_t1449, _t1450,)
            assert fields793 is not None
            unwrapped_fields794 = fields793
            self.write("(epoch")
            self.indent_sexp()
            field795 = unwrapped_fields794[0]
            if field795 is not None:
                self.newline()
                assert field795 is not None
                opt_val796 = field795
                self.pretty_epoch_writes(opt_val796)
            field797 = unwrapped_fields794[1]
            if field797 is not None:
                self.newline()
                assert field797 is not None
                opt_val798 = field797
                self.pretty_epoch_reads(opt_val798)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat803 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat803 is not None:
            assert flat803 is not None
            self.write(flat803)
            return None
        else:
            fields800 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields800) == 0:
                self.newline()
                for i802, elem801 in enumerate(fields800):
                    if (i802 > 0):
                        self.newline()
                    self.pretty_write(elem801)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat812 = self._try_flat(msg, self.pretty_write)
        if flat812 is not None:
            assert flat812 is not None
            self.write(flat812)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1451 = _dollar_dollar.define
            else:
                _t1451 = None
            deconstruct_result810 = _t1451
            if deconstruct_result810 is not None:
                assert deconstruct_result810 is not None
                unwrapped811 = deconstruct_result810
                self.pretty_define(unwrapped811)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1452 = _dollar_dollar.undefine
                else:
                    _t1452 = None
                deconstruct_result808 = _t1452
                if deconstruct_result808 is not None:
                    assert deconstruct_result808 is not None
                    unwrapped809 = deconstruct_result808
                    self.pretty_undefine(unwrapped809)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1453 = _dollar_dollar.context
                    else:
                        _t1453 = None
                    deconstruct_result806 = _t1453
                    if deconstruct_result806 is not None:
                        assert deconstruct_result806 is not None
                        unwrapped807 = deconstruct_result806
                        self.pretty_context(unwrapped807)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1454 = _dollar_dollar.snapshot
                        else:
                            _t1454 = None
                        deconstruct_result804 = _t1454
                        if deconstruct_result804 is not None:
                            assert deconstruct_result804 is not None
                            unwrapped805 = deconstruct_result804
                            self.pretty_snapshot(unwrapped805)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat815 = self._try_flat(msg, self.pretty_define)
        if flat815 is not None:
            assert flat815 is not None
            self.write(flat815)
            return None
        else:
            _dollar_dollar = msg
            fields813 = _dollar_dollar.fragment
            assert fields813 is not None
            unwrapped_fields814 = fields813
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields814)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat822 = self._try_flat(msg, self.pretty_fragment)
        if flat822 is not None:
            assert flat822 is not None
            self.write(flat822)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields816 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields816 is not None
            unwrapped_fields817 = fields816
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field818 = unwrapped_fields817[0]
            self.pretty_new_fragment_id(field818)
            field819 = unwrapped_fields817[1]
            if not len(field819) == 0:
                self.newline()
                for i821, elem820 in enumerate(field819):
                    if (i821 > 0):
                        self.newline()
                    self.pretty_declaration(elem820)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat824 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat824 is not None:
            assert flat824 is not None
            self.write(flat824)
            return None
        else:
            fields823 = msg
            self.pretty_fragment_id(fields823)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat833 = self._try_flat(msg, self.pretty_declaration)
        if flat833 is not None:
            assert flat833 is not None
            self.write(flat833)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1455 = getattr(_dollar_dollar, 'def')
            else:
                _t1455 = None
            deconstruct_result831 = _t1455
            if deconstruct_result831 is not None:
                assert deconstruct_result831 is not None
                unwrapped832 = deconstruct_result831
                self.pretty_def(unwrapped832)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1456 = _dollar_dollar.algorithm
                else:
                    _t1456 = None
                deconstruct_result829 = _t1456
                if deconstruct_result829 is not None:
                    assert deconstruct_result829 is not None
                    unwrapped830 = deconstruct_result829
                    self.pretty_algorithm(unwrapped830)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1457 = _dollar_dollar.constraint
                    else:
                        _t1457 = None
                    deconstruct_result827 = _t1457
                    if deconstruct_result827 is not None:
                        assert deconstruct_result827 is not None
                        unwrapped828 = deconstruct_result827
                        self.pretty_constraint(unwrapped828)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1458 = _dollar_dollar.data
                        else:
                            _t1458 = None
                        deconstruct_result825 = _t1458
                        if deconstruct_result825 is not None:
                            assert deconstruct_result825 is not None
                            unwrapped826 = deconstruct_result825
                            self.pretty_data(unwrapped826)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat840 = self._try_flat(msg, self.pretty_def)
        if flat840 is not None:
            assert flat840 is not None
            self.write(flat840)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1459 = _dollar_dollar.attrs
            else:
                _t1459 = None
            fields834 = (_dollar_dollar.name, _dollar_dollar.body, _t1459,)
            assert fields834 is not None
            unwrapped_fields835 = fields834
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field836 = unwrapped_fields835[0]
            self.pretty_relation_id(field836)
            self.newline()
            field837 = unwrapped_fields835[1]
            self.pretty_abstraction(field837)
            field838 = unwrapped_fields835[2]
            if field838 is not None:
                self.newline()
                assert field838 is not None
                opt_val839 = field838
                self.pretty_attrs(opt_val839)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat845 = self._try_flat(msg, self.pretty_relation_id)
        if flat845 is not None:
            assert flat845 is not None
            self.write(flat845)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1461 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1460 = _t1461
            else:
                _t1460 = None
            deconstruct_result843 = _t1460
            if deconstruct_result843 is not None:
                assert deconstruct_result843 is not None
                unwrapped844 = deconstruct_result843
                self.write(":")
                self.write(unwrapped844)
            else:
                _dollar_dollar = msg
                _t1462 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result841 = _t1462
                if deconstruct_result841 is not None:
                    assert deconstruct_result841 is not None
                    unwrapped842 = deconstruct_result841
                    self.write(self.format_uint128(unwrapped842))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat850 = self._try_flat(msg, self.pretty_abstraction)
        if flat850 is not None:
            assert flat850 is not None
            self.write(flat850)
            return None
        else:
            _dollar_dollar = msg
            _t1463 = self.deconstruct_bindings(_dollar_dollar)
            fields846 = (_t1463, _dollar_dollar.value,)
            assert fields846 is not None
            unwrapped_fields847 = fields846
            self.write("(")
            self.indent()
            field848 = unwrapped_fields847[0]
            self.pretty_bindings(field848)
            self.newline()
            field849 = unwrapped_fields847[1]
            self.pretty_formula(field849)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat858 = self._try_flat(msg, self.pretty_bindings)
        if flat858 is not None:
            assert flat858 is not None
            self.write(flat858)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1464 = _dollar_dollar[1]
            else:
                _t1464 = None
            fields851 = (_dollar_dollar[0], _t1464,)
            assert fields851 is not None
            unwrapped_fields852 = fields851
            self.write("[")
            self.indent()
            field853 = unwrapped_fields852[0]
            for i855, elem854 in enumerate(field853):
                if (i855 > 0):
                    self.newline()
                self.pretty_binding(elem854)
            field856 = unwrapped_fields852[1]
            if field856 is not None:
                self.newline()
                assert field856 is not None
                opt_val857 = field856
                self.pretty_value_bindings(opt_val857)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat863 = self._try_flat(msg, self.pretty_binding)
        if flat863 is not None:
            assert flat863 is not None
            self.write(flat863)
            return None
        else:
            _dollar_dollar = msg
            fields859 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields859 is not None
            unwrapped_fields860 = fields859
            field861 = unwrapped_fields860[0]
            self.write(field861)
            self.write("::")
            field862 = unwrapped_fields860[1]
            self.pretty_type(field862)

    def pretty_type(self, msg: logic_pb2.Type):
        flat892 = self._try_flat(msg, self.pretty_type)
        if flat892 is not None:
            assert flat892 is not None
            self.write(flat892)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1465 = _dollar_dollar.unspecified_type
            else:
                _t1465 = None
            deconstruct_result890 = _t1465
            if deconstruct_result890 is not None:
                assert deconstruct_result890 is not None
                unwrapped891 = deconstruct_result890
                self.pretty_unspecified_type(unwrapped891)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1466 = _dollar_dollar.string_type
                else:
                    _t1466 = None
                deconstruct_result888 = _t1466
                if deconstruct_result888 is not None:
                    assert deconstruct_result888 is not None
                    unwrapped889 = deconstruct_result888
                    self.pretty_string_type(unwrapped889)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1467 = _dollar_dollar.int_type
                    else:
                        _t1467 = None
                    deconstruct_result886 = _t1467
                    if deconstruct_result886 is not None:
                        assert deconstruct_result886 is not None
                        unwrapped887 = deconstruct_result886
                        self.pretty_int_type(unwrapped887)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1468 = _dollar_dollar.float_type
                        else:
                            _t1468 = None
                        deconstruct_result884 = _t1468
                        if deconstruct_result884 is not None:
                            assert deconstruct_result884 is not None
                            unwrapped885 = deconstruct_result884
                            self.pretty_float_type(unwrapped885)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1469 = _dollar_dollar.uint128_type
                            else:
                                _t1469 = None
                            deconstruct_result882 = _t1469
                            if deconstruct_result882 is not None:
                                assert deconstruct_result882 is not None
                                unwrapped883 = deconstruct_result882
                                self.pretty_uint128_type(unwrapped883)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1470 = _dollar_dollar.int128_type
                                else:
                                    _t1470 = None
                                deconstruct_result880 = _t1470
                                if deconstruct_result880 is not None:
                                    assert deconstruct_result880 is not None
                                    unwrapped881 = deconstruct_result880
                                    self.pretty_int128_type(unwrapped881)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1471 = _dollar_dollar.date_type
                                    else:
                                        _t1471 = None
                                    deconstruct_result878 = _t1471
                                    if deconstruct_result878 is not None:
                                        assert deconstruct_result878 is not None
                                        unwrapped879 = deconstruct_result878
                                        self.pretty_date_type(unwrapped879)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1472 = _dollar_dollar.datetime_type
                                        else:
                                            _t1472 = None
                                        deconstruct_result876 = _t1472
                                        if deconstruct_result876 is not None:
                                            assert deconstruct_result876 is not None
                                            unwrapped877 = deconstruct_result876
                                            self.pretty_datetime_type(unwrapped877)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1473 = _dollar_dollar.missing_type
                                            else:
                                                _t1473 = None
                                            deconstruct_result874 = _t1473
                                            if deconstruct_result874 is not None:
                                                assert deconstruct_result874 is not None
                                                unwrapped875 = deconstruct_result874
                                                self.pretty_missing_type(unwrapped875)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1474 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1474 = None
                                                deconstruct_result872 = _t1474
                                                if deconstruct_result872 is not None:
                                                    assert deconstruct_result872 is not None
                                                    unwrapped873 = deconstruct_result872
                                                    self.pretty_decimal_type(unwrapped873)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1475 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1475 = None
                                                    deconstruct_result870 = _t1475
                                                    if deconstruct_result870 is not None:
                                                        assert deconstruct_result870 is not None
                                                        unwrapped871 = deconstruct_result870
                                                        self.pretty_boolean_type(unwrapped871)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1476 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1476 = None
                                                        deconstruct_result868 = _t1476
                                                        if deconstruct_result868 is not None:
                                                            assert deconstruct_result868 is not None
                                                            unwrapped869 = deconstruct_result868
                                                            self.pretty_int32_type(unwrapped869)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1477 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1477 = None
                                                            deconstruct_result866 = _t1477
                                                            if deconstruct_result866 is not None:
                                                                assert deconstruct_result866 is not None
                                                                unwrapped867 = deconstruct_result866
                                                                self.pretty_float32_type(unwrapped867)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1478 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1478 = None
                                                                deconstruct_result864 = _t1478
                                                                if deconstruct_result864 is not None:
                                                                    assert deconstruct_result864 is not None
                                                                    unwrapped865 = deconstruct_result864
                                                                    self.pretty_uint32_type(unwrapped865)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields893 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields894 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields895 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields896 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields897 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields898 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields899 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields900 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields901 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat906 = self._try_flat(msg, self.pretty_decimal_type)
        if flat906 is not None:
            assert flat906 is not None
            self.write(flat906)
            return None
        else:
            _dollar_dollar = msg
            fields902 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields902 is not None
            unwrapped_fields903 = fields902
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field904 = unwrapped_fields903[0]
            self.write(str(field904))
            self.newline()
            field905 = unwrapped_fields903[1]
            self.write(str(field905))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields907 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields908 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields909 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields910 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat914 = self._try_flat(msg, self.pretty_value_bindings)
        if flat914 is not None:
            assert flat914 is not None
            self.write(flat914)
            return None
        else:
            fields911 = msg
            self.write("|")
            if not len(fields911) == 0:
                self.write(" ")
                for i913, elem912 in enumerate(fields911):
                    if (i913 > 0):
                        self.newline()
                    self.pretty_binding(elem912)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat941 = self._try_flat(msg, self.pretty_formula)
        if flat941 is not None:
            assert flat941 is not None
            self.write(flat941)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1479 = _dollar_dollar.conjunction
            else:
                _t1479 = None
            deconstruct_result939 = _t1479
            if deconstruct_result939 is not None:
                assert deconstruct_result939 is not None
                unwrapped940 = deconstruct_result939
                self.pretty_true(unwrapped940)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1480 = _dollar_dollar.disjunction
                else:
                    _t1480 = None
                deconstruct_result937 = _t1480
                if deconstruct_result937 is not None:
                    assert deconstruct_result937 is not None
                    unwrapped938 = deconstruct_result937
                    self.pretty_false(unwrapped938)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1481 = _dollar_dollar.exists
                    else:
                        _t1481 = None
                    deconstruct_result935 = _t1481
                    if deconstruct_result935 is not None:
                        assert deconstruct_result935 is not None
                        unwrapped936 = deconstruct_result935
                        self.pretty_exists(unwrapped936)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1482 = _dollar_dollar.reduce
                        else:
                            _t1482 = None
                        deconstruct_result933 = _t1482
                        if deconstruct_result933 is not None:
                            assert deconstruct_result933 is not None
                            unwrapped934 = deconstruct_result933
                            self.pretty_reduce(unwrapped934)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1483 = _dollar_dollar.conjunction
                            else:
                                _t1483 = None
                            deconstruct_result931 = _t1483
                            if deconstruct_result931 is not None:
                                assert deconstruct_result931 is not None
                                unwrapped932 = deconstruct_result931
                                self.pretty_conjunction(unwrapped932)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1484 = _dollar_dollar.disjunction
                                else:
                                    _t1484 = None
                                deconstruct_result929 = _t1484
                                if deconstruct_result929 is not None:
                                    assert deconstruct_result929 is not None
                                    unwrapped930 = deconstruct_result929
                                    self.pretty_disjunction(unwrapped930)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1485 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1485 = None
                                    deconstruct_result927 = _t1485
                                    if deconstruct_result927 is not None:
                                        assert deconstruct_result927 is not None
                                        unwrapped928 = deconstruct_result927
                                        self.pretty_not(unwrapped928)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1486 = _dollar_dollar.ffi
                                        else:
                                            _t1486 = None
                                        deconstruct_result925 = _t1486
                                        if deconstruct_result925 is not None:
                                            assert deconstruct_result925 is not None
                                            unwrapped926 = deconstruct_result925
                                            self.pretty_ffi(unwrapped926)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1487 = _dollar_dollar.atom
                                            else:
                                                _t1487 = None
                                            deconstruct_result923 = _t1487
                                            if deconstruct_result923 is not None:
                                                assert deconstruct_result923 is not None
                                                unwrapped924 = deconstruct_result923
                                                self.pretty_atom(unwrapped924)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1488 = _dollar_dollar.pragma
                                                else:
                                                    _t1488 = None
                                                deconstruct_result921 = _t1488
                                                if deconstruct_result921 is not None:
                                                    assert deconstruct_result921 is not None
                                                    unwrapped922 = deconstruct_result921
                                                    self.pretty_pragma(unwrapped922)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1489 = _dollar_dollar.primitive
                                                    else:
                                                        _t1489 = None
                                                    deconstruct_result919 = _t1489
                                                    if deconstruct_result919 is not None:
                                                        assert deconstruct_result919 is not None
                                                        unwrapped920 = deconstruct_result919
                                                        self.pretty_primitive(unwrapped920)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1490 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1490 = None
                                                        deconstruct_result917 = _t1490
                                                        if deconstruct_result917 is not None:
                                                            assert deconstruct_result917 is not None
                                                            unwrapped918 = deconstruct_result917
                                                            self.pretty_rel_atom(unwrapped918)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1491 = _dollar_dollar.cast
                                                            else:
                                                                _t1491 = None
                                                            deconstruct_result915 = _t1491
                                                            if deconstruct_result915 is not None:
                                                                assert deconstruct_result915 is not None
                                                                unwrapped916 = deconstruct_result915
                                                                self.pretty_cast(unwrapped916)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields942 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields943 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat948 = self._try_flat(msg, self.pretty_exists)
        if flat948 is not None:
            assert flat948 is not None
            self.write(flat948)
            return None
        else:
            _dollar_dollar = msg
            _t1492 = self.deconstruct_bindings(_dollar_dollar.body)
            fields944 = (_t1492, _dollar_dollar.body.value,)
            assert fields944 is not None
            unwrapped_fields945 = fields944
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field946 = unwrapped_fields945[0]
            self.pretty_bindings(field946)
            self.newline()
            field947 = unwrapped_fields945[1]
            self.pretty_formula(field947)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat954 = self._try_flat(msg, self.pretty_reduce)
        if flat954 is not None:
            assert flat954 is not None
            self.write(flat954)
            return None
        else:
            _dollar_dollar = msg
            fields949 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields949 is not None
            unwrapped_fields950 = fields949
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field951 = unwrapped_fields950[0]
            self.pretty_abstraction(field951)
            self.newline()
            field952 = unwrapped_fields950[1]
            self.pretty_abstraction(field952)
            self.newline()
            field953 = unwrapped_fields950[2]
            self.pretty_terms(field953)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat958 = self._try_flat(msg, self.pretty_terms)
        if flat958 is not None:
            assert flat958 is not None
            self.write(flat958)
            return None
        else:
            fields955 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields955) == 0:
                self.newline()
                for i957, elem956 in enumerate(fields955):
                    if (i957 > 0):
                        self.newline()
                    self.pretty_term(elem956)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat963 = self._try_flat(msg, self.pretty_term)
        if flat963 is not None:
            assert flat963 is not None
            self.write(flat963)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1493 = _dollar_dollar.var
            else:
                _t1493 = None
            deconstruct_result961 = _t1493
            if deconstruct_result961 is not None:
                assert deconstruct_result961 is not None
                unwrapped962 = deconstruct_result961
                self.pretty_var(unwrapped962)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1494 = _dollar_dollar.constant
                else:
                    _t1494 = None
                deconstruct_result959 = _t1494
                if deconstruct_result959 is not None:
                    assert deconstruct_result959 is not None
                    unwrapped960 = deconstruct_result959
                    self.pretty_constant(unwrapped960)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat966 = self._try_flat(msg, self.pretty_var)
        if flat966 is not None:
            assert flat966 is not None
            self.write(flat966)
            return None
        else:
            _dollar_dollar = msg
            fields964 = _dollar_dollar.name
            assert fields964 is not None
            unwrapped_fields965 = fields964
            self.write(unwrapped_fields965)

    def pretty_constant(self, msg: logic_pb2.Value):
        flat968 = self._try_flat(msg, self.pretty_constant)
        if flat968 is not None:
            assert flat968 is not None
            self.write(flat968)
            return None
        else:
            fields967 = msg
            self.pretty_value(fields967)

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat973 = self._try_flat(msg, self.pretty_conjunction)
        if flat973 is not None:
            assert flat973 is not None
            self.write(flat973)
            return None
        else:
            _dollar_dollar = msg
            fields969 = _dollar_dollar.args
            assert fields969 is not None
            unwrapped_fields970 = fields969
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields970) == 0:
                self.newline()
                for i972, elem971 in enumerate(unwrapped_fields970):
                    if (i972 > 0):
                        self.newline()
                    self.pretty_formula(elem971)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat978 = self._try_flat(msg, self.pretty_disjunction)
        if flat978 is not None:
            assert flat978 is not None
            self.write(flat978)
            return None
        else:
            _dollar_dollar = msg
            fields974 = _dollar_dollar.args
            assert fields974 is not None
            unwrapped_fields975 = fields974
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields975) == 0:
                self.newline()
                for i977, elem976 in enumerate(unwrapped_fields975):
                    if (i977 > 0):
                        self.newline()
                    self.pretty_formula(elem976)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat981 = self._try_flat(msg, self.pretty_not)
        if flat981 is not None:
            assert flat981 is not None
            self.write(flat981)
            return None
        else:
            _dollar_dollar = msg
            fields979 = _dollar_dollar.arg
            assert fields979 is not None
            unwrapped_fields980 = fields979
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields980)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat987 = self._try_flat(msg, self.pretty_ffi)
        if flat987 is not None:
            assert flat987 is not None
            self.write(flat987)
            return None
        else:
            _dollar_dollar = msg
            fields982 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields982 is not None
            unwrapped_fields983 = fields982
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field984 = unwrapped_fields983[0]
            self.pretty_name(field984)
            self.newline()
            field985 = unwrapped_fields983[1]
            self.pretty_ffi_args(field985)
            self.newline()
            field986 = unwrapped_fields983[2]
            self.pretty_terms(field986)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat989 = self._try_flat(msg, self.pretty_name)
        if flat989 is not None:
            assert flat989 is not None
            self.write(flat989)
            return None
        else:
            fields988 = msg
            self.write(":")
            self.write(fields988)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat993 = self._try_flat(msg, self.pretty_ffi_args)
        if flat993 is not None:
            assert flat993 is not None
            self.write(flat993)
            return None
        else:
            fields990 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields990) == 0:
                self.newline()
                for i992, elem991 in enumerate(fields990):
                    if (i992 > 0):
                        self.newline()
                    self.pretty_abstraction(elem991)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1000 = self._try_flat(msg, self.pretty_atom)
        if flat1000 is not None:
            assert flat1000 is not None
            self.write(flat1000)
            return None
        else:
            _dollar_dollar = msg
            fields994 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields994 is not None
            unwrapped_fields995 = fields994
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field996 = unwrapped_fields995[0]
            self.pretty_relation_id(field996)
            field997 = unwrapped_fields995[1]
            if not len(field997) == 0:
                self.newline()
                for i999, elem998 in enumerate(field997):
                    if (i999 > 0):
                        self.newline()
                    self.pretty_term(elem998)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1007 = self._try_flat(msg, self.pretty_pragma)
        if flat1007 is not None:
            assert flat1007 is not None
            self.write(flat1007)
            return None
        else:
            _dollar_dollar = msg
            fields1001 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1001 is not None
            unwrapped_fields1002 = fields1001
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1003 = unwrapped_fields1002[0]
            self.pretty_name(field1003)
            field1004 = unwrapped_fields1002[1]
            if not len(field1004) == 0:
                self.newline()
                for i1006, elem1005 in enumerate(field1004):
                    if (i1006 > 0):
                        self.newline()
                    self.pretty_term(elem1005)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1023 = self._try_flat(msg, self.pretty_primitive)
        if flat1023 is not None:
            assert flat1023 is not None
            self.write(flat1023)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1495 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1495 = None
            guard_result1022 = _t1495
            if guard_result1022 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1496 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1496 = None
                guard_result1021 = _t1496
                if guard_result1021 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1497 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1497 = None
                    guard_result1020 = _t1497
                    if guard_result1020 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1498 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1498 = None
                        guard_result1019 = _t1498
                        if guard_result1019 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1499 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1499 = None
                            guard_result1018 = _t1499
                            if guard_result1018 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1500 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1500 = None
                                guard_result1017 = _t1500
                                if guard_result1017 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1501 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1501 = None
                                    guard_result1016 = _t1501
                                    if guard_result1016 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1502 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1502 = None
                                        guard_result1015 = _t1502
                                        if guard_result1015 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1503 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1503 = None
                                            guard_result1014 = _t1503
                                            if guard_result1014 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1008 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1008 is not None
                                                unwrapped_fields1009 = fields1008
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1010 = unwrapped_fields1009[0]
                                                self.pretty_name(field1010)
                                                field1011 = unwrapped_fields1009[1]
                                                if not len(field1011) == 0:
                                                    self.newline()
                                                    for i1013, elem1012 in enumerate(field1011):
                                                        if (i1013 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1012)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1028 = self._try_flat(msg, self.pretty_eq)
        if flat1028 is not None:
            assert flat1028 is not None
            self.write(flat1028)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1504 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1504 = None
            fields1024 = _t1504
            assert fields1024 is not None
            unwrapped_fields1025 = fields1024
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1026 = unwrapped_fields1025[0]
            self.pretty_term(field1026)
            self.newline()
            field1027 = unwrapped_fields1025[1]
            self.pretty_term(field1027)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1033 = self._try_flat(msg, self.pretty_lt)
        if flat1033 is not None:
            assert flat1033 is not None
            self.write(flat1033)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1505 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1505 = None
            fields1029 = _t1505
            assert fields1029 is not None
            unwrapped_fields1030 = fields1029
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1031 = unwrapped_fields1030[0]
            self.pretty_term(field1031)
            self.newline()
            field1032 = unwrapped_fields1030[1]
            self.pretty_term(field1032)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1038 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1038 is not None:
            assert flat1038 is not None
            self.write(flat1038)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1506 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1506 = None
            fields1034 = _t1506
            assert fields1034 is not None
            unwrapped_fields1035 = fields1034
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1036 = unwrapped_fields1035[0]
            self.pretty_term(field1036)
            self.newline()
            field1037 = unwrapped_fields1035[1]
            self.pretty_term(field1037)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1043 = self._try_flat(msg, self.pretty_gt)
        if flat1043 is not None:
            assert flat1043 is not None
            self.write(flat1043)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1507 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1507 = None
            fields1039 = _t1507
            assert fields1039 is not None
            unwrapped_fields1040 = fields1039
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1041 = unwrapped_fields1040[0]
            self.pretty_term(field1041)
            self.newline()
            field1042 = unwrapped_fields1040[1]
            self.pretty_term(field1042)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1048 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1048 is not None:
            assert flat1048 is not None
            self.write(flat1048)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1508 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1508 = None
            fields1044 = _t1508
            assert fields1044 is not None
            unwrapped_fields1045 = fields1044
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1046 = unwrapped_fields1045[0]
            self.pretty_term(field1046)
            self.newline()
            field1047 = unwrapped_fields1045[1]
            self.pretty_term(field1047)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1054 = self._try_flat(msg, self.pretty_add)
        if flat1054 is not None:
            assert flat1054 is not None
            self.write(flat1054)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1509 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1509 = None
            fields1049 = _t1509
            assert fields1049 is not None
            unwrapped_fields1050 = fields1049
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1051 = unwrapped_fields1050[0]
            self.pretty_term(field1051)
            self.newline()
            field1052 = unwrapped_fields1050[1]
            self.pretty_term(field1052)
            self.newline()
            field1053 = unwrapped_fields1050[2]
            self.pretty_term(field1053)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1060 = self._try_flat(msg, self.pretty_minus)
        if flat1060 is not None:
            assert flat1060 is not None
            self.write(flat1060)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1510 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1510 = None
            fields1055 = _t1510
            assert fields1055 is not None
            unwrapped_fields1056 = fields1055
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1057 = unwrapped_fields1056[0]
            self.pretty_term(field1057)
            self.newline()
            field1058 = unwrapped_fields1056[1]
            self.pretty_term(field1058)
            self.newline()
            field1059 = unwrapped_fields1056[2]
            self.pretty_term(field1059)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1066 = self._try_flat(msg, self.pretty_multiply)
        if flat1066 is not None:
            assert flat1066 is not None
            self.write(flat1066)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1511 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1511 = None
            fields1061 = _t1511
            assert fields1061 is not None
            unwrapped_fields1062 = fields1061
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1063 = unwrapped_fields1062[0]
            self.pretty_term(field1063)
            self.newline()
            field1064 = unwrapped_fields1062[1]
            self.pretty_term(field1064)
            self.newline()
            field1065 = unwrapped_fields1062[2]
            self.pretty_term(field1065)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1072 = self._try_flat(msg, self.pretty_divide)
        if flat1072 is not None:
            assert flat1072 is not None
            self.write(flat1072)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1512 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1512 = None
            fields1067 = _t1512
            assert fields1067 is not None
            unwrapped_fields1068 = fields1067
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1069 = unwrapped_fields1068[0]
            self.pretty_term(field1069)
            self.newline()
            field1070 = unwrapped_fields1068[1]
            self.pretty_term(field1070)
            self.newline()
            field1071 = unwrapped_fields1068[2]
            self.pretty_term(field1071)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1077 = self._try_flat(msg, self.pretty_rel_term)
        if flat1077 is not None:
            assert flat1077 is not None
            self.write(flat1077)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1513 = _dollar_dollar.specialized_value
            else:
                _t1513 = None
            deconstruct_result1075 = _t1513
            if deconstruct_result1075 is not None:
                assert deconstruct_result1075 is not None
                unwrapped1076 = deconstruct_result1075
                self.pretty_specialized_value(unwrapped1076)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1514 = _dollar_dollar.term
                else:
                    _t1514 = None
                deconstruct_result1073 = _t1514
                if deconstruct_result1073 is not None:
                    assert deconstruct_result1073 is not None
                    unwrapped1074 = deconstruct_result1073
                    self.pretty_term(unwrapped1074)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1079 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1079 is not None:
            assert flat1079 is not None
            self.write(flat1079)
            return None
        else:
            fields1078 = msg
            self.write("#")
            self.pretty_value(fields1078)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1086 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1086 is not None:
            assert flat1086 is not None
            self.write(flat1086)
            return None
        else:
            _dollar_dollar = msg
            fields1080 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1080 is not None
            unwrapped_fields1081 = fields1080
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1082 = unwrapped_fields1081[0]
            self.pretty_name(field1082)
            field1083 = unwrapped_fields1081[1]
            if not len(field1083) == 0:
                self.newline()
                for i1085, elem1084 in enumerate(field1083):
                    if (i1085 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1084)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1091 = self._try_flat(msg, self.pretty_cast)
        if flat1091 is not None:
            assert flat1091 is not None
            self.write(flat1091)
            return None
        else:
            _dollar_dollar = msg
            fields1087 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1087 is not None
            unwrapped_fields1088 = fields1087
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1089 = unwrapped_fields1088[0]
            self.pretty_term(field1089)
            self.newline()
            field1090 = unwrapped_fields1088[1]
            self.pretty_term(field1090)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1095 = self._try_flat(msg, self.pretty_attrs)
        if flat1095 is not None:
            assert flat1095 is not None
            self.write(flat1095)
            return None
        else:
            fields1092 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1092) == 0:
                self.newline()
                for i1094, elem1093 in enumerate(fields1092):
                    if (i1094 > 0):
                        self.newline()
                    self.pretty_attribute(elem1093)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1102 = self._try_flat(msg, self.pretty_attribute)
        if flat1102 is not None:
            assert flat1102 is not None
            self.write(flat1102)
            return None
        else:
            _dollar_dollar = msg
            fields1096 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1096 is not None
            unwrapped_fields1097 = fields1096
            self.write("(attribute")
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
                    self.pretty_value(elem1100)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1109 = self._try_flat(msg, self.pretty_algorithm)
        if flat1109 is not None:
            assert flat1109 is not None
            self.write(flat1109)
            return None
        else:
            _dollar_dollar = msg
            fields1103 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            assert fields1103 is not None
            unwrapped_fields1104 = fields1103
            self.write("(algorithm")
            self.indent_sexp()
            field1105 = unwrapped_fields1104[0]
            if not len(field1105) == 0:
                self.newline()
                for i1107, elem1106 in enumerate(field1105):
                    if (i1107 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1106)
            self.newline()
            field1108 = unwrapped_fields1104[1]
            self.pretty_script(field1108)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1114 = self._try_flat(msg, self.pretty_script)
        if flat1114 is not None:
            assert flat1114 is not None
            self.write(flat1114)
            return None
        else:
            _dollar_dollar = msg
            fields1110 = _dollar_dollar.constructs
            assert fields1110 is not None
            unwrapped_fields1111 = fields1110
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1111) == 0:
                self.newline()
                for i1113, elem1112 in enumerate(unwrapped_fields1111):
                    if (i1113 > 0):
                        self.newline()
                    self.pretty_construct(elem1112)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1119 = self._try_flat(msg, self.pretty_construct)
        if flat1119 is not None:
            assert flat1119 is not None
            self.write(flat1119)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1515 = _dollar_dollar.loop
            else:
                _t1515 = None
            deconstruct_result1117 = _t1515
            if deconstruct_result1117 is not None:
                assert deconstruct_result1117 is not None
                unwrapped1118 = deconstruct_result1117
                self.pretty_loop(unwrapped1118)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1516 = _dollar_dollar.instruction
                else:
                    _t1516 = None
                deconstruct_result1115 = _t1516
                if deconstruct_result1115 is not None:
                    assert deconstruct_result1115 is not None
                    unwrapped1116 = deconstruct_result1115
                    self.pretty_instruction(unwrapped1116)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1124 = self._try_flat(msg, self.pretty_loop)
        if flat1124 is not None:
            assert flat1124 is not None
            self.write(flat1124)
            return None
        else:
            _dollar_dollar = msg
            fields1120 = (_dollar_dollar.init, _dollar_dollar.body,)
            assert fields1120 is not None
            unwrapped_fields1121 = fields1120
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1122 = unwrapped_fields1121[0]
            self.pretty_init(field1122)
            self.newline()
            field1123 = unwrapped_fields1121[1]
            self.pretty_script(field1123)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1128 = self._try_flat(msg, self.pretty_init)
        if flat1128 is not None:
            assert flat1128 is not None
            self.write(flat1128)
            return None
        else:
            fields1125 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1125) == 0:
                self.newline()
                for i1127, elem1126 in enumerate(fields1125):
                    if (i1127 > 0):
                        self.newline()
                    self.pretty_instruction(elem1126)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1139 = self._try_flat(msg, self.pretty_instruction)
        if flat1139 is not None:
            assert flat1139 is not None
            self.write(flat1139)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1517 = _dollar_dollar.assign
            else:
                _t1517 = None
            deconstruct_result1137 = _t1517
            if deconstruct_result1137 is not None:
                assert deconstruct_result1137 is not None
                unwrapped1138 = deconstruct_result1137
                self.pretty_assign(unwrapped1138)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1518 = _dollar_dollar.upsert
                else:
                    _t1518 = None
                deconstruct_result1135 = _t1518
                if deconstruct_result1135 is not None:
                    assert deconstruct_result1135 is not None
                    unwrapped1136 = deconstruct_result1135
                    self.pretty_upsert(unwrapped1136)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1519 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1519 = None
                    deconstruct_result1133 = _t1519
                    if deconstruct_result1133 is not None:
                        assert deconstruct_result1133 is not None
                        unwrapped1134 = deconstruct_result1133
                        self.pretty_break(unwrapped1134)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1520 = _dollar_dollar.monoid_def
                        else:
                            _t1520 = None
                        deconstruct_result1131 = _t1520
                        if deconstruct_result1131 is not None:
                            assert deconstruct_result1131 is not None
                            unwrapped1132 = deconstruct_result1131
                            self.pretty_monoid_def(unwrapped1132)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1521 = _dollar_dollar.monus_def
                            else:
                                _t1521 = None
                            deconstruct_result1129 = _t1521
                            if deconstruct_result1129 is not None:
                                assert deconstruct_result1129 is not None
                                unwrapped1130 = deconstruct_result1129
                                self.pretty_monus_def(unwrapped1130)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1146 = self._try_flat(msg, self.pretty_assign)
        if flat1146 is not None:
            assert flat1146 is not None
            self.write(flat1146)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1522 = _dollar_dollar.attrs
            else:
                _t1522 = None
            fields1140 = (_dollar_dollar.name, _dollar_dollar.body, _t1522,)
            assert fields1140 is not None
            unwrapped_fields1141 = fields1140
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1142 = unwrapped_fields1141[0]
            self.pretty_relation_id(field1142)
            self.newline()
            field1143 = unwrapped_fields1141[1]
            self.pretty_abstraction(field1143)
            field1144 = unwrapped_fields1141[2]
            if field1144 is not None:
                self.newline()
                assert field1144 is not None
                opt_val1145 = field1144
                self.pretty_attrs(opt_val1145)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1153 = self._try_flat(msg, self.pretty_upsert)
        if flat1153 is not None:
            assert flat1153 is not None
            self.write(flat1153)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1523 = _dollar_dollar.attrs
            else:
                _t1523 = None
            fields1147 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1523,)
            assert fields1147 is not None
            unwrapped_fields1148 = fields1147
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1149 = unwrapped_fields1148[0]
            self.pretty_relation_id(field1149)
            self.newline()
            field1150 = unwrapped_fields1148[1]
            self.pretty_abstraction_with_arity(field1150)
            field1151 = unwrapped_fields1148[2]
            if field1151 is not None:
                self.newline()
                assert field1151 is not None
                opt_val1152 = field1151
                self.pretty_attrs(opt_val1152)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1158 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1158 is not None:
            assert flat1158 is not None
            self.write(flat1158)
            return None
        else:
            _dollar_dollar = msg
            _t1524 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1154 = (_t1524, _dollar_dollar[0].value,)
            assert fields1154 is not None
            unwrapped_fields1155 = fields1154
            self.write("(")
            self.indent()
            field1156 = unwrapped_fields1155[0]
            self.pretty_bindings(field1156)
            self.newline()
            field1157 = unwrapped_fields1155[1]
            self.pretty_formula(field1157)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1165 = self._try_flat(msg, self.pretty_break)
        if flat1165 is not None:
            assert flat1165 is not None
            self.write(flat1165)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1525 = _dollar_dollar.attrs
            else:
                _t1525 = None
            fields1159 = (_dollar_dollar.name, _dollar_dollar.body, _t1525,)
            assert fields1159 is not None
            unwrapped_fields1160 = fields1159
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1161 = unwrapped_fields1160[0]
            self.pretty_relation_id(field1161)
            self.newline()
            field1162 = unwrapped_fields1160[1]
            self.pretty_abstraction(field1162)
            field1163 = unwrapped_fields1160[2]
            if field1163 is not None:
                self.newline()
                assert field1163 is not None
                opt_val1164 = field1163
                self.pretty_attrs(opt_val1164)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1173 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1173 is not None:
            assert flat1173 is not None
            self.write(flat1173)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1526 = _dollar_dollar.attrs
            else:
                _t1526 = None
            fields1166 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1526,)
            assert fields1166 is not None
            unwrapped_fields1167 = fields1166
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1168 = unwrapped_fields1167[0]
            self.pretty_monoid(field1168)
            self.newline()
            field1169 = unwrapped_fields1167[1]
            self.pretty_relation_id(field1169)
            self.newline()
            field1170 = unwrapped_fields1167[2]
            self.pretty_abstraction_with_arity(field1170)
            field1171 = unwrapped_fields1167[3]
            if field1171 is not None:
                self.newline()
                assert field1171 is not None
                opt_val1172 = field1171
                self.pretty_attrs(opt_val1172)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1182 = self._try_flat(msg, self.pretty_monoid)
        if flat1182 is not None:
            assert flat1182 is not None
            self.write(flat1182)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1527 = _dollar_dollar.or_monoid
            else:
                _t1527 = None
            deconstruct_result1180 = _t1527
            if deconstruct_result1180 is not None:
                assert deconstruct_result1180 is not None
                unwrapped1181 = deconstruct_result1180
                self.pretty_or_monoid(unwrapped1181)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1528 = _dollar_dollar.min_monoid
                else:
                    _t1528 = None
                deconstruct_result1178 = _t1528
                if deconstruct_result1178 is not None:
                    assert deconstruct_result1178 is not None
                    unwrapped1179 = deconstruct_result1178
                    self.pretty_min_monoid(unwrapped1179)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1529 = _dollar_dollar.max_monoid
                    else:
                        _t1529 = None
                    deconstruct_result1176 = _t1529
                    if deconstruct_result1176 is not None:
                        assert deconstruct_result1176 is not None
                        unwrapped1177 = deconstruct_result1176
                        self.pretty_max_monoid(unwrapped1177)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1530 = _dollar_dollar.sum_monoid
                        else:
                            _t1530 = None
                        deconstruct_result1174 = _t1530
                        if deconstruct_result1174 is not None:
                            assert deconstruct_result1174 is not None
                            unwrapped1175 = deconstruct_result1174
                            self.pretty_sum_monoid(unwrapped1175)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1183 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1186 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1186 is not None:
            assert flat1186 is not None
            self.write(flat1186)
            return None
        else:
            _dollar_dollar = msg
            fields1184 = _dollar_dollar.type
            assert fields1184 is not None
            unwrapped_fields1185 = fields1184
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1185)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1189 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1189 is not None:
            assert flat1189 is not None
            self.write(flat1189)
            return None
        else:
            _dollar_dollar = msg
            fields1187 = _dollar_dollar.type
            assert fields1187 is not None
            unwrapped_fields1188 = fields1187
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1188)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1192 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1192 is not None:
            assert flat1192 is not None
            self.write(flat1192)
            return None
        else:
            _dollar_dollar = msg
            fields1190 = _dollar_dollar.type
            assert fields1190 is not None
            unwrapped_fields1191 = fields1190
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1191)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1200 = self._try_flat(msg, self.pretty_monus_def)
        if flat1200 is not None:
            assert flat1200 is not None
            self.write(flat1200)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1531 = _dollar_dollar.attrs
            else:
                _t1531 = None
            fields1193 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1531,)
            assert fields1193 is not None
            unwrapped_fields1194 = fields1193
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1195 = unwrapped_fields1194[0]
            self.pretty_monoid(field1195)
            self.newline()
            field1196 = unwrapped_fields1194[1]
            self.pretty_relation_id(field1196)
            self.newline()
            field1197 = unwrapped_fields1194[2]
            self.pretty_abstraction_with_arity(field1197)
            field1198 = unwrapped_fields1194[3]
            if field1198 is not None:
                self.newline()
                assert field1198 is not None
                opt_val1199 = field1198
                self.pretty_attrs(opt_val1199)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1207 = self._try_flat(msg, self.pretty_constraint)
        if flat1207 is not None:
            assert flat1207 is not None
            self.write(flat1207)
            return None
        else:
            _dollar_dollar = msg
            fields1201 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1201 is not None
            unwrapped_fields1202 = fields1201
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1203 = unwrapped_fields1202[0]
            self.pretty_relation_id(field1203)
            self.newline()
            field1204 = unwrapped_fields1202[1]
            self.pretty_abstraction(field1204)
            self.newline()
            field1205 = unwrapped_fields1202[2]
            self.pretty_functional_dependency_keys(field1205)
            self.newline()
            field1206 = unwrapped_fields1202[3]
            self.pretty_functional_dependency_values(field1206)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1211 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1211 is not None:
            assert flat1211 is not None
            self.write(flat1211)
            return None
        else:
            fields1208 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1208) == 0:
                self.newline()
                for i1210, elem1209 in enumerate(fields1208):
                    if (i1210 > 0):
                        self.newline()
                    self.pretty_var(elem1209)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1215 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1215 is not None:
            assert flat1215 is not None
            self.write(flat1215)
            return None
        else:
            fields1212 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1212) == 0:
                self.newline()
                for i1214, elem1213 in enumerate(fields1212):
                    if (i1214 > 0):
                        self.newline()
                    self.pretty_var(elem1213)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1224 = self._try_flat(msg, self.pretty_data)
        if flat1224 is not None:
            assert flat1224 is not None
            self.write(flat1224)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1532 = _dollar_dollar.edb
            else:
                _t1532 = None
            deconstruct_result1222 = _t1532
            if deconstruct_result1222 is not None:
                assert deconstruct_result1222 is not None
                unwrapped1223 = deconstruct_result1222
                self.pretty_edb(unwrapped1223)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1533 = _dollar_dollar.betree_relation
                else:
                    _t1533 = None
                deconstruct_result1220 = _t1533
                if deconstruct_result1220 is not None:
                    assert deconstruct_result1220 is not None
                    unwrapped1221 = deconstruct_result1220
                    self.pretty_betree_relation(unwrapped1221)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1534 = _dollar_dollar.csv_data
                    else:
                        _t1534 = None
                    deconstruct_result1218 = _t1534
                    if deconstruct_result1218 is not None:
                        assert deconstruct_result1218 is not None
                        unwrapped1219 = deconstruct_result1218
                        self.pretty_csv_data(unwrapped1219)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("iceberg_data"):
                            _t1535 = _dollar_dollar.iceberg_data
                        else:
                            _t1535 = None
                        deconstruct_result1216 = _t1535
                        if deconstruct_result1216 is not None:
                            assert deconstruct_result1216 is not None
                            unwrapped1217 = deconstruct_result1216
                            self.pretty_iceberg_data(unwrapped1217)
                        else:
                            raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1230 = self._try_flat(msg, self.pretty_edb)
        if flat1230 is not None:
            assert flat1230 is not None
            self.write(flat1230)
            return None
        else:
            _dollar_dollar = msg
            fields1225 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1225 is not None
            unwrapped_fields1226 = fields1225
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1227 = unwrapped_fields1226[0]
            self.pretty_relation_id(field1227)
            self.newline()
            field1228 = unwrapped_fields1226[1]
            self.pretty_edb_path(field1228)
            self.newline()
            field1229 = unwrapped_fields1226[2]
            self.pretty_edb_types(field1229)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1234 = self._try_flat(msg, self.pretty_edb_path)
        if flat1234 is not None:
            assert flat1234 is not None
            self.write(flat1234)
            return None
        else:
            fields1231 = msg
            self.write("[")
            self.indent()
            for i1233, elem1232 in enumerate(fields1231):
                if (i1233 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1232))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1238 = self._try_flat(msg, self.pretty_edb_types)
        if flat1238 is not None:
            assert flat1238 is not None
            self.write(flat1238)
            return None
        else:
            fields1235 = msg
            self.write("[")
            self.indent()
            for i1237, elem1236 in enumerate(fields1235):
                if (i1237 > 0):
                    self.newline()
                self.pretty_type(elem1236)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1243 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1243 is not None:
            assert flat1243 is not None
            self.write(flat1243)
            return None
        else:
            _dollar_dollar = msg
            fields1239 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1239 is not None
            unwrapped_fields1240 = fields1239
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1241 = unwrapped_fields1240[0]
            self.pretty_relation_id(field1241)
            self.newline()
            field1242 = unwrapped_fields1240[1]
            self.pretty_betree_info(field1242)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1249 = self._try_flat(msg, self.pretty_betree_info)
        if flat1249 is not None:
            assert flat1249 is not None
            self.write(flat1249)
            return None
        else:
            _dollar_dollar = msg
            _t1536 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1244 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1536,)
            assert fields1244 is not None
            unwrapped_fields1245 = fields1244
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1246 = unwrapped_fields1245[0]
            self.pretty_betree_info_key_types(field1246)
            self.newline()
            field1247 = unwrapped_fields1245[1]
            self.pretty_betree_info_value_types(field1247)
            self.newline()
            field1248 = unwrapped_fields1245[2]
            self.pretty_config_dict(field1248)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1253 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1253 is not None:
            assert flat1253 is not None
            self.write(flat1253)
            return None
        else:
            fields1250 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1250) == 0:
                self.newline()
                for i1252, elem1251 in enumerate(fields1250):
                    if (i1252 > 0):
                        self.newline()
                    self.pretty_type(elem1251)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1257 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1257 is not None:
            assert flat1257 is not None
            self.write(flat1257)
            return None
        else:
            fields1254 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1254) == 0:
                self.newline()
                for i1256, elem1255 in enumerate(fields1254):
                    if (i1256 > 0):
                        self.newline()
                    self.pretty_type(elem1255)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1264 = self._try_flat(msg, self.pretty_csv_data)
        if flat1264 is not None:
            assert flat1264 is not None
            self.write(flat1264)
            return None
        else:
            _dollar_dollar = msg
            fields1258 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1258 is not None
            unwrapped_fields1259 = fields1258
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1260 = unwrapped_fields1259[0]
            self.pretty_csvlocator(field1260)
            self.newline()
            field1261 = unwrapped_fields1259[1]
            self.pretty_csv_config(field1261)
            self.newline()
            field1262 = unwrapped_fields1259[2]
            self.pretty_gnf_columns(field1262)
            self.newline()
            field1263 = unwrapped_fields1259[3]
            self.pretty_csv_asof(field1263)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1271 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1271 is not None:
            assert flat1271 is not None
            self.write(flat1271)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1537 = _dollar_dollar.paths
            else:
                _t1537 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1538 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1538 = None
            fields1265 = (_t1537, _t1538,)
            assert fields1265 is not None
            unwrapped_fields1266 = fields1265
            self.write("(csv_locator")
            self.indent_sexp()
            field1267 = unwrapped_fields1266[0]
            if field1267 is not None:
                self.newline()
                assert field1267 is not None
                opt_val1268 = field1267
                self.pretty_csv_locator_paths(opt_val1268)
            field1269 = unwrapped_fields1266[1]
            if field1269 is not None:
                self.newline()
                assert field1269 is not None
                opt_val1270 = field1269
                self.pretty_csv_locator_inline_data(opt_val1270)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1275 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1275 is not None:
            assert flat1275 is not None
            self.write(flat1275)
            return None
        else:
            fields1272 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1272) == 0:
                self.newline()
                for i1274, elem1273 in enumerate(fields1272):
                    if (i1274 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1273))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1277 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1277 is not None:
            assert flat1277 is not None
            self.write(flat1277)
            return None
        else:
            fields1276 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1276))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1280 = self._try_flat(msg, self.pretty_csv_config)
        if flat1280 is not None:
            assert flat1280 is not None
            self.write(flat1280)
            return None
        else:
            _dollar_dollar = msg
            _t1539 = self.deconstruct_csv_config(_dollar_dollar)
            fields1278 = _t1539
            assert fields1278 is not None
            unwrapped_fields1279 = fields1278
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1279)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1284 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1284 is not None:
            assert flat1284 is not None
            self.write(flat1284)
            return None
        else:
            fields1281 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1281) == 0:
                self.newline()
                for i1283, elem1282 in enumerate(fields1281):
                    if (i1283 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1282)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1293 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1293 is not None:
            assert flat1293 is not None
            self.write(flat1293)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1540 = _dollar_dollar.target_id
            else:
                _t1540 = None
            fields1285 = (_dollar_dollar.column_path, _t1540, _dollar_dollar.types,)
            assert fields1285 is not None
            unwrapped_fields1286 = fields1285
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1287 = unwrapped_fields1286[0]
            self.pretty_gnf_column_path(field1287)
            field1288 = unwrapped_fields1286[1]
            if field1288 is not None:
                self.newline()
                assert field1288 is not None
                opt_val1289 = field1288
                self.pretty_relation_id(opt_val1289)
            self.newline()
            self.write("[")
            field1290 = unwrapped_fields1286[2]
            for i1292, elem1291 in enumerate(field1290):
                if (i1292 > 0):
                    self.newline()
                self.pretty_type(elem1291)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1300 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1300 is not None:
            assert flat1300 is not None
            self.write(flat1300)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1541 = _dollar_dollar[0]
            else:
                _t1541 = None
            deconstruct_result1298 = _t1541
            if deconstruct_result1298 is not None:
                assert deconstruct_result1298 is not None
                unwrapped1299 = deconstruct_result1298
                self.write(self.format_string_value(unwrapped1299))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1542 = _dollar_dollar
                else:
                    _t1542 = None
                deconstruct_result1294 = _t1542
                if deconstruct_result1294 is not None:
                    assert deconstruct_result1294 is not None
                    unwrapped1295 = deconstruct_result1294
                    self.write("[")
                    self.indent()
                    for i1297, elem1296 in enumerate(unwrapped1295):
                        if (i1297 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1296))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1302 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1302 is not None:
            assert flat1302 is not None
            self.write(flat1302)
            return None
        else:
            fields1301 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1301))
            self.dedent()
            self.write(")")

    def pretty_iceberg_data(self, msg: logic_pb2.IcebergData):
        flat1310 = self._try_flat(msg, self.pretty_iceberg_data)
        if flat1310 is not None:
            assert flat1310 is not None
            self.write(flat1310)
            return None
        else:
            _dollar_dollar = msg
            fields1303 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.to_snapshot,)
            assert fields1303 is not None
            unwrapped_fields1304 = fields1303
            self.write("(iceberg_data")
            self.indent_sexp()
            self.newline()
            field1305 = unwrapped_fields1304[0]
            self.pretty_iceberg_locator(field1305)
            self.newline()
            field1306 = unwrapped_fields1304[1]
            self.pretty_iceberg_config(field1306)
            self.newline()
            field1307 = unwrapped_fields1304[2]
            self.pretty_gnf_columns(field1307)
            field1308 = unwrapped_fields1304[3]
            if field1308 is not None:
                self.newline()
                assert field1308 is not None
                opt_val1309 = field1308
                self.pretty_iceberg_to_snapshot(opt_val1309)
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator(self, msg: logic_pb2.IcebergLocator):
        flat1316 = self._try_flat(msg, self.pretty_iceberg_locator)
        if flat1316 is not None:
            assert flat1316 is not None
            self.write(flat1316)
            return None
        else:
            _dollar_dollar = msg
            fields1311 = (_dollar_dollar.table_name, _dollar_dollar.namespace, _dollar_dollar.warehouse,)
            assert fields1311 is not None
            unwrapped_fields1312 = fields1311
            self.write("(iceberg_locator")
            self.indent_sexp()
            self.newline()
            field1313 = unwrapped_fields1312[0]
            self.write(self.format_string_value(field1313))
            self.newline()
            field1314 = unwrapped_fields1312[1]
            self.pretty_iceberg_locator_namespace(field1314)
            self.newline()
            field1315 = unwrapped_fields1312[2]
            self.write(self.format_string_value(field1315))
            self.dedent()
            self.write(")")

    def pretty_iceberg_locator_namespace(self, msg: Sequence[str]):
        flat1320 = self._try_flat(msg, self.pretty_iceberg_locator_namespace)
        if flat1320 is not None:
            assert flat1320 is not None
            self.write(flat1320)
            return None
        else:
            fields1317 = msg
            self.write("(namespace")
            self.indent_sexp()
            if not len(fields1317) == 0:
                self.newline()
                for i1319, elem1318 in enumerate(fields1317):
                    if (i1319 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1318))
            self.dedent()
            self.write(")")

    def pretty_iceberg_config(self, msg: logic_pb2.IcebergConfig):
        flat1330 = self._try_flat(msg, self.pretty_iceberg_config)
        if flat1330 is not None:
            assert flat1330 is not None
            self.write(flat1330)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.scope != "":
                _t1543 = _dollar_dollar.scope
            else:
                _t1543 = None
            if not len(sorted(_dollar_dollar.properties.items())) == 0:
                _t1544 = sorted(_dollar_dollar.properties.items())
            else:
                _t1544 = None
            if not len(sorted(_dollar_dollar.credentials.items())) == 0:
                _t1545 = sorted(_dollar_dollar.credentials.items())
            else:
                _t1545 = None
            fields1321 = (_dollar_dollar.catalog_uri, _t1543, _t1544, _t1545,)
            assert fields1321 is not None
            unwrapped_fields1322 = fields1321
            self.write("(iceberg_config")
            self.indent_sexp()
            self.newline()
            field1323 = unwrapped_fields1322[0]
            self.write(self.format_string_value(field1323))
            field1324 = unwrapped_fields1322[1]
            if field1324 is not None:
                self.newline()
                assert field1324 is not None
                opt_val1325 = field1324
                self.pretty_iceberg_config_scope(opt_val1325)
            field1326 = unwrapped_fields1322[2]
            if field1326 is not None:
                self.newline()
                assert field1326 is not None
                opt_val1327 = field1326
                self.pretty_iceberg_config_properties(opt_val1327)
            field1328 = unwrapped_fields1322[3]
            if field1328 is not None:
                self.newline()
                assert field1328 is not None
                opt_val1329 = field1328
                self.pretty_iceberg_config_credentials(opt_val1329)
            self.dedent()
            self.write(")")

    def pretty_iceberg_config_scope(self, msg: str):
        flat1332 = self._try_flat(msg, self.pretty_iceberg_config_scope)
        if flat1332 is not None:
            assert flat1332 is not None
            self.write(flat1332)
            return None
        else:
            fields1331 = msg
            self.write("(scope")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1331))
            self.dedent()
            self.write(")")

    def pretty_iceberg_config_properties(self, msg: Sequence[tuple[str, str]]):
        flat1336 = self._try_flat(msg, self.pretty_iceberg_config_properties)
        if flat1336 is not None:
            assert flat1336 is not None
            self.write(flat1336)
            return None
        else:
            fields1333 = msg
            self.write("(properties")
            self.indent_sexp()
            if not len(fields1333) == 0:
                self.newline()
                for i1335, elem1334 in enumerate(fields1333):
                    if (i1335 > 0):
                        self.newline()
                    self.pretty_iceberg_kv_pair(elem1334)
            self.dedent()
            self.write(")")

    def pretty_iceberg_kv_pair(self, msg: tuple[str, str]):
        flat1341 = self._try_flat(msg, self.pretty_iceberg_kv_pair)
        if flat1341 is not None:
            assert flat1341 is not None
            self.write(flat1341)
            return None
        else:
            _dollar_dollar = msg
            fields1337 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields1337 is not None
            unwrapped_fields1338 = fields1337
            self.write("(")
            self.indent()
            field1339 = unwrapped_fields1338[0]
            self.write(self.format_string_value(field1339))
            self.newline()
            field1340 = unwrapped_fields1338[1]
            self.write(self.format_string_value(field1340))
            self.dedent()
            self.write(")")

    def pretty_iceberg_config_credentials(self, msg: Sequence[tuple[str, str]]):
        flat1345 = self._try_flat(msg, self.pretty_iceberg_config_credentials)
        if flat1345 is not None:
            assert flat1345 is not None
            self.write(flat1345)
            return None
        else:
            fields1342 = msg
            self.write("(credentials")
            self.indent_sexp()
            if not len(fields1342) == 0:
                self.newline()
                for i1344, elem1343 in enumerate(fields1342):
                    if (i1344 > 0):
                        self.newline()
                    self.pretty_iceberg_kv_pair(elem1343)
            self.dedent()
            self.write(")")

    def pretty_iceberg_to_snapshot(self, msg: str):
        flat1347 = self._try_flat(msg, self.pretty_iceberg_to_snapshot)
        if flat1347 is not None:
            assert flat1347 is not None
            self.write(flat1347)
            return None
        else:
            fields1346 = msg
            self.write("(to_snapshot")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1346))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1350 = self._try_flat(msg, self.pretty_undefine)
        if flat1350 is not None:
            assert flat1350 is not None
            self.write(flat1350)
            return None
        else:
            _dollar_dollar = msg
            fields1348 = _dollar_dollar.fragment_id
            assert fields1348 is not None
            unwrapped_fields1349 = fields1348
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1349)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1355 = self._try_flat(msg, self.pretty_context)
        if flat1355 is not None:
            assert flat1355 is not None
            self.write(flat1355)
            return None
        else:
            _dollar_dollar = msg
            fields1351 = _dollar_dollar.relations
            assert fields1351 is not None
            unwrapped_fields1352 = fields1351
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1352) == 0:
                self.newline()
                for i1354, elem1353 in enumerate(unwrapped_fields1352):
                    if (i1354 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1353)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1360 = self._try_flat(msg, self.pretty_snapshot)
        if flat1360 is not None:
            assert flat1360 is not None
            self.write(flat1360)
            return None
        else:
            _dollar_dollar = msg
            fields1356 = _dollar_dollar.mappings
            assert fields1356 is not None
            unwrapped_fields1357 = fields1356
            self.write("(snapshot")
            self.indent_sexp()
            if not len(unwrapped_fields1357) == 0:
                self.newline()
                for i1359, elem1358 in enumerate(unwrapped_fields1357):
                    if (i1359 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1358)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1365 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1365 is not None:
            assert flat1365 is not None
            self.write(flat1365)
            return None
        else:
            _dollar_dollar = msg
            fields1361 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1361 is not None
            unwrapped_fields1362 = fields1361
            field1363 = unwrapped_fields1362[0]
            self.pretty_edb_path(field1363)
            self.write(" ")
            field1364 = unwrapped_fields1362[1]
            self.pretty_relation_id(field1364)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1369 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1369 is not None:
            assert flat1369 is not None
            self.write(flat1369)
            return None
        else:
            fields1366 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1366) == 0:
                self.newline()
                for i1368, elem1367 in enumerate(fields1366):
                    if (i1368 > 0):
                        self.newline()
                    self.pretty_read(elem1367)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1380 = self._try_flat(msg, self.pretty_read)
        if flat1380 is not None:
            assert flat1380 is not None
            self.write(flat1380)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1546 = _dollar_dollar.demand
            else:
                _t1546 = None
            deconstruct_result1378 = _t1546
            if deconstruct_result1378 is not None:
                assert deconstruct_result1378 is not None
                unwrapped1379 = deconstruct_result1378
                self.pretty_demand(unwrapped1379)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1547 = _dollar_dollar.output
                else:
                    _t1547 = None
                deconstruct_result1376 = _t1547
                if deconstruct_result1376 is not None:
                    assert deconstruct_result1376 is not None
                    unwrapped1377 = deconstruct_result1376
                    self.pretty_output(unwrapped1377)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1548 = _dollar_dollar.what_if
                    else:
                        _t1548 = None
                    deconstruct_result1374 = _t1548
                    if deconstruct_result1374 is not None:
                        assert deconstruct_result1374 is not None
                        unwrapped1375 = deconstruct_result1374
                        self.pretty_what_if(unwrapped1375)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1549 = _dollar_dollar.abort
                        else:
                            _t1549 = None
                        deconstruct_result1372 = _t1549
                        if deconstruct_result1372 is not None:
                            assert deconstruct_result1372 is not None
                            unwrapped1373 = deconstruct_result1372
                            self.pretty_abort(unwrapped1373)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1550 = _dollar_dollar.export
                            else:
                                _t1550 = None
                            deconstruct_result1370 = _t1550
                            if deconstruct_result1370 is not None:
                                assert deconstruct_result1370 is not None
                                unwrapped1371 = deconstruct_result1370
                                self.pretty_export(unwrapped1371)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1383 = self._try_flat(msg, self.pretty_demand)
        if flat1383 is not None:
            assert flat1383 is not None
            self.write(flat1383)
            return None
        else:
            _dollar_dollar = msg
            fields1381 = _dollar_dollar.relation_id
            assert fields1381 is not None
            unwrapped_fields1382 = fields1381
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1382)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1388 = self._try_flat(msg, self.pretty_output)
        if flat1388 is not None:
            assert flat1388 is not None
            self.write(flat1388)
            return None
        else:
            _dollar_dollar = msg
            fields1384 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1384 is not None
            unwrapped_fields1385 = fields1384
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1386 = unwrapped_fields1385[0]
            self.pretty_name(field1386)
            self.newline()
            field1387 = unwrapped_fields1385[1]
            self.pretty_relation_id(field1387)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1393 = self._try_flat(msg, self.pretty_what_if)
        if flat1393 is not None:
            assert flat1393 is not None
            self.write(flat1393)
            return None
        else:
            _dollar_dollar = msg
            fields1389 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1389 is not None
            unwrapped_fields1390 = fields1389
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1391 = unwrapped_fields1390[0]
            self.pretty_name(field1391)
            self.newline()
            field1392 = unwrapped_fields1390[1]
            self.pretty_epoch(field1392)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1399 = self._try_flat(msg, self.pretty_abort)
        if flat1399 is not None:
            assert flat1399 is not None
            self.write(flat1399)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1551 = _dollar_dollar.name
            else:
                _t1551 = None
            fields1394 = (_t1551, _dollar_dollar.relation_id,)
            assert fields1394 is not None
            unwrapped_fields1395 = fields1394
            self.write("(abort")
            self.indent_sexp()
            field1396 = unwrapped_fields1395[0]
            if field1396 is not None:
                self.newline()
                assert field1396 is not None
                opt_val1397 = field1396
                self.pretty_name(opt_val1397)
            self.newline()
            field1398 = unwrapped_fields1395[1]
            self.pretty_relation_id(field1398)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1402 = self._try_flat(msg, self.pretty_export)
        if flat1402 is not None:
            assert flat1402 is not None
            self.write(flat1402)
            return None
        else:
            _dollar_dollar = msg
            fields1400 = _dollar_dollar.csv_config
            assert fields1400 is not None
            unwrapped_fields1401 = fields1400
            self.write("(export")
            self.indent_sexp()
            self.newline()
            self.pretty_export_csv_config(unwrapped_fields1401)
            self.dedent()
            self.write(")")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1413 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1413 is not None:
            assert flat1413 is not None
            self.write(flat1413)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1552 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1552 = None
            deconstruct_result1408 = _t1552
            if deconstruct_result1408 is not None:
                assert deconstruct_result1408 is not None
                unwrapped1409 = deconstruct_result1408
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1410 = unwrapped1409[0]
                self.pretty_export_csv_path(field1410)
                self.newline()
                field1411 = unwrapped1409[1]
                self.pretty_export_csv_source(field1411)
                self.newline()
                field1412 = unwrapped1409[2]
                self.pretty_csv_config(field1412)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1554 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1553 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1554,)
                else:
                    _t1553 = None
                deconstruct_result1403 = _t1553
                if deconstruct_result1403 is not None:
                    assert deconstruct_result1403 is not None
                    unwrapped1404 = deconstruct_result1403
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1405 = unwrapped1404[0]
                    self.pretty_export_csv_path(field1405)
                    self.newline()
                    field1406 = unwrapped1404[1]
                    self.pretty_export_csv_columns_list(field1406)
                    self.newline()
                    field1407 = unwrapped1404[2]
                    self.pretty_config_dict(field1407)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1415 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1415 is not None:
            assert flat1415 is not None
            self.write(flat1415)
            return None
        else:
            fields1414 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1414))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1422 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1422 is not None:
            assert flat1422 is not None
            self.write(flat1422)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1555 = _dollar_dollar.gnf_columns.columns
            else:
                _t1555 = None
            deconstruct_result1418 = _t1555
            if deconstruct_result1418 is not None:
                assert deconstruct_result1418 is not None
                unwrapped1419 = deconstruct_result1418
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1419) == 0:
                    self.newline()
                    for i1421, elem1420 in enumerate(unwrapped1419):
                        if (i1421 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1420)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1556 = _dollar_dollar.table_def
                else:
                    _t1556 = None
                deconstruct_result1416 = _t1556
                if deconstruct_result1416 is not None:
                    assert deconstruct_result1416 is not None
                    unwrapped1417 = deconstruct_result1416
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1417)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1427 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1427 is not None:
            assert flat1427 is not None
            self.write(flat1427)
            return None
        else:
            _dollar_dollar = msg
            fields1423 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1423 is not None
            unwrapped_fields1424 = fields1423
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1425 = unwrapped_fields1424[0]
            self.write(self.format_string_value(field1425))
            self.newline()
            field1426 = unwrapped_fields1424[1]
            self.pretty_relation_id(field1426)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1431 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1431 is not None:
            assert flat1431 is not None
            self.write(flat1431)
            return None
        else:
            fields1428 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1428) == 0:
                self.newline()
                for i1430, elem1429 in enumerate(fields1428):
                    if (i1430 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1429)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1595 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1595)
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
            self.pretty_date(msg)
        elif isinstance(msg, logic_pb2.DateTimeValue):
            self.pretty_datetime(msg)
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
