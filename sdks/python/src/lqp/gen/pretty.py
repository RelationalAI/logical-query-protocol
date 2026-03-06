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
        _t1536 = logic_pb2.Value(int32_value=v)
        return _t1536

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1537 = logic_pb2.Value(int_value=v)
        return _t1537

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1538 = logic_pb2.Value(float_value=v)
        return _t1538

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1539 = logic_pb2.Value(string_value=v)
        return _t1539

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1540 = logic_pb2.Value(boolean_value=v)
        return _t1540

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1541 = logic_pb2.Value(uint128_value=v)
        return _t1541

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1542 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1542,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1543 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1543,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1544 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1544,))
        _t1545 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1545,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1546 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1546,))
        _t1547 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1547,))
        if msg.new_line != "":
            _t1548 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1548,))
        _t1549 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1549,))
        _t1550 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1550,))
        _t1551 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1551,))
        if msg.comment != "":
            _t1552 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1552,))
        for missing_string in msg.missing_strings:
            _t1553 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1553,))
        _t1554 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1554,))
        _t1555 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1555,))
        _t1556 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1556,))
        if msg.partition_size_mb != 0:
            _t1557 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1557,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1558 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1558,))
        _t1559 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1559,))
        _t1560 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1560,))
        _t1561 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1561,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1562 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1562,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1563 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1563,))
        _t1564 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1564,))
        _t1565 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1565,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1566 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1566,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1567 = self._make_value_string(msg.compression)
            result.append(("compression", _t1567,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1568 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1568,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1569 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1569,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1570 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1570,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1571 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1571,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1572 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1572,))
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
            _t1573 = None
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
        flat712 = self._try_flat(msg, self.pretty_transaction)
        if flat712 is not None:
            assert flat712 is not None
            self.write(flat712)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1406 = _dollar_dollar.configure
            else:
                _t1406 = None
            if _dollar_dollar.HasField("sync"):
                _t1407 = _dollar_dollar.sync
            else:
                _t1407 = None
            fields703 = (_t1406, _t1407, _dollar_dollar.epochs,)
            assert fields703 is not None
            unwrapped_fields704 = fields703
            self.write("(transaction")
            self.indent_sexp()
            field705 = unwrapped_fields704[0]
            if field705 is not None:
                self.newline()
                assert field705 is not None
                opt_val706 = field705
                self.pretty_configure(opt_val706)
            field707 = unwrapped_fields704[1]
            if field707 is not None:
                self.newline()
                assert field707 is not None
                opt_val708 = field707
                self.pretty_sync(opt_val708)
            field709 = unwrapped_fields704[2]
            if not len(field709) == 0:
                self.newline()
                for i711, elem710 in enumerate(field709):
                    if (i711 > 0):
                        self.newline()
                    self.pretty_epoch(elem710)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat715 = self._try_flat(msg, self.pretty_configure)
        if flat715 is not None:
            assert flat715 is not None
            self.write(flat715)
            return None
        else:
            _dollar_dollar = msg
            _t1408 = self.deconstruct_configure(_dollar_dollar)
            fields713 = _t1408
            assert fields713 is not None
            unwrapped_fields714 = fields713
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields714)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat719 = self._try_flat(msg, self.pretty_config_dict)
        if flat719 is not None:
            assert flat719 is not None
            self.write(flat719)
            return None
        else:
            fields716 = msg
            self.write("{")
            self.indent()
            if not len(fields716) == 0:
                self.newline()
                for i718, elem717 in enumerate(fields716):
                    if (i718 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem717)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat724 = self._try_flat(msg, self.pretty_config_key_value)
        if flat724 is not None:
            assert flat724 is not None
            self.write(flat724)
            return None
        else:
            _dollar_dollar = msg
            fields720 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields720 is not None
            unwrapped_fields721 = fields720
            self.write(":")
            field722 = unwrapped_fields721[0]
            self.write(field722)
            self.write(" ")
            field723 = unwrapped_fields721[1]
            self.pretty_raw_value(field723)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat748 = self._try_flat(msg, self.pretty_raw_value)
        if flat748 is not None:
            assert flat748 is not None
            self.write(flat748)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1409 = _dollar_dollar.date_value
            else:
                _t1409 = None
            deconstruct_result746 = _t1409
            if deconstruct_result746 is not None:
                assert deconstruct_result746 is not None
                unwrapped747 = deconstruct_result746
                self.pretty_raw_date(unwrapped747)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1410 = _dollar_dollar.datetime_value
                else:
                    _t1410 = None
                deconstruct_result744 = _t1410
                if deconstruct_result744 is not None:
                    assert deconstruct_result744 is not None
                    unwrapped745 = deconstruct_result744
                    self.pretty_raw_datetime(unwrapped745)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1411 = _dollar_dollar.string_value
                    else:
                        _t1411 = None
                    deconstruct_result742 = _t1411
                    if deconstruct_result742 is not None:
                        assert deconstruct_result742 is not None
                        unwrapped743 = deconstruct_result742
                        self.write(self.format_string_value(unwrapped743))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1412 = _dollar_dollar.int32_value
                        else:
                            _t1412 = None
                        deconstruct_result740 = _t1412
                        if deconstruct_result740 is not None:
                            assert deconstruct_result740 is not None
                            unwrapped741 = deconstruct_result740
                            self.write((str(unwrapped741) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1413 = _dollar_dollar.int_value
                            else:
                                _t1413 = None
                            deconstruct_result738 = _t1413
                            if deconstruct_result738 is not None:
                                assert deconstruct_result738 is not None
                                unwrapped739 = deconstruct_result738
                                self.write(str(unwrapped739))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1414 = _dollar_dollar.float32_value
                                else:
                                    _t1414 = None
                                deconstruct_result736 = _t1414
                                if deconstruct_result736 is not None:
                                    assert deconstruct_result736 is not None
                                    unwrapped737 = deconstruct_result736
                                    self.write((self.format_float32_value(unwrapped737) + 'f32'))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1415 = _dollar_dollar.float_value
                                    else:
                                        _t1415 = None
                                    deconstruct_result734 = _t1415
                                    if deconstruct_result734 is not None:
                                        assert deconstruct_result734 is not None
                                        unwrapped735 = deconstruct_result734
                                        self.write(str(unwrapped735))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint128_value"):
                                            _t1416 = _dollar_dollar.uint128_value
                                        else:
                                            _t1416 = None
                                        deconstruct_result732 = _t1416
                                        if deconstruct_result732 is not None:
                                            assert deconstruct_result732 is not None
                                            unwrapped733 = deconstruct_result732
                                            self.write(self.format_uint128(unwrapped733))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("int128_value"):
                                                _t1417 = _dollar_dollar.int128_value
                                            else:
                                                _t1417 = None
                                            deconstruct_result730 = _t1417
                                            if deconstruct_result730 is not None:
                                                assert deconstruct_result730 is not None
                                                unwrapped731 = deconstruct_result730
                                                self.write(self.format_int128(unwrapped731))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_value"):
                                                    _t1418 = _dollar_dollar.decimal_value
                                                else:
                                                    _t1418 = None
                                                deconstruct_result728 = _t1418
                                                if deconstruct_result728 is not None:
                                                    assert deconstruct_result728 is not None
                                                    unwrapped729 = deconstruct_result728
                                                    self.write(self.format_decimal(unwrapped729))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_value"):
                                                        _t1419 = _dollar_dollar.boolean_value
                                                    else:
                                                        _t1419 = None
                                                    deconstruct_result726 = _t1419
                                                    if deconstruct_result726 is not None:
                                                        assert deconstruct_result726 is not None
                                                        unwrapped727 = deconstruct_result726
                                                        self.pretty_boolean_value(unwrapped727)
                                                    else:
                                                        fields725 = msg
                                                        self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat754 = self._try_flat(msg, self.pretty_raw_date)
        if flat754 is not None:
            assert flat754 is not None
            self.write(flat754)
            return None
        else:
            _dollar_dollar = msg
            fields749 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields749 is not None
            unwrapped_fields750 = fields749
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field751 = unwrapped_fields750[0]
            self.write(str(field751))
            self.newline()
            field752 = unwrapped_fields750[1]
            self.write(str(field752))
            self.newline()
            field753 = unwrapped_fields750[2]
            self.write(str(field753))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat765 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat765 is not None:
            assert flat765 is not None
            self.write(flat765)
            return None
        else:
            _dollar_dollar = msg
            fields755 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields755 is not None
            unwrapped_fields756 = fields755
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field757 = unwrapped_fields756[0]
            self.write(str(field757))
            self.newline()
            field758 = unwrapped_fields756[1]
            self.write(str(field758))
            self.newline()
            field759 = unwrapped_fields756[2]
            self.write(str(field759))
            self.newline()
            field760 = unwrapped_fields756[3]
            self.write(str(field760))
            self.newline()
            field761 = unwrapped_fields756[4]
            self.write(str(field761))
            self.newline()
            field762 = unwrapped_fields756[5]
            self.write(str(field762))
            field763 = unwrapped_fields756[6]
            if field763 is not None:
                self.newline()
                assert field763 is not None
                opt_val764 = field763
                self.write(str(opt_val764))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1420 = ()
        else:
            _t1420 = None
        deconstruct_result768 = _t1420
        if deconstruct_result768 is not None:
            assert deconstruct_result768 is not None
            unwrapped769 = deconstruct_result768
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1421 = ()
            else:
                _t1421 = None
            deconstruct_result766 = _t1421
            if deconstruct_result766 is not None:
                assert deconstruct_result766 is not None
                unwrapped767 = deconstruct_result766
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat774 = self._try_flat(msg, self.pretty_sync)
        if flat774 is not None:
            assert flat774 is not None
            self.write(flat774)
            return None
        else:
            _dollar_dollar = msg
            fields770 = _dollar_dollar.fragments
            assert fields770 is not None
            unwrapped_fields771 = fields770
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields771) == 0:
                self.newline()
                for i773, elem772 in enumerate(unwrapped_fields771):
                    if (i773 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem772)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat777 = self._try_flat(msg, self.pretty_fragment_id)
        if flat777 is not None:
            assert flat777 is not None
            self.write(flat777)
            return None
        else:
            _dollar_dollar = msg
            fields775 = self.fragment_id_to_string(_dollar_dollar)
            assert fields775 is not None
            unwrapped_fields776 = fields775
            self.write(":")
            self.write(unwrapped_fields776)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat784 = self._try_flat(msg, self.pretty_epoch)
        if flat784 is not None:
            assert flat784 is not None
            self.write(flat784)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1422 = _dollar_dollar.writes
            else:
                _t1422 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1423 = _dollar_dollar.reads
            else:
                _t1423 = None
            fields778 = (_t1422, _t1423,)
            assert fields778 is not None
            unwrapped_fields779 = fields778
            self.write("(epoch")
            self.indent_sexp()
            field780 = unwrapped_fields779[0]
            if field780 is not None:
                self.newline()
                assert field780 is not None
                opt_val781 = field780
                self.pretty_epoch_writes(opt_val781)
            field782 = unwrapped_fields779[1]
            if field782 is not None:
                self.newline()
                assert field782 is not None
                opt_val783 = field782
                self.pretty_epoch_reads(opt_val783)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat788 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat788 is not None:
            assert flat788 is not None
            self.write(flat788)
            return None
        else:
            fields785 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields785) == 0:
                self.newline()
                for i787, elem786 in enumerate(fields785):
                    if (i787 > 0):
                        self.newline()
                    self.pretty_write(elem786)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat797 = self._try_flat(msg, self.pretty_write)
        if flat797 is not None:
            assert flat797 is not None
            self.write(flat797)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1424 = _dollar_dollar.define
            else:
                _t1424 = None
            deconstruct_result795 = _t1424
            if deconstruct_result795 is not None:
                assert deconstruct_result795 is not None
                unwrapped796 = deconstruct_result795
                self.pretty_define(unwrapped796)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1425 = _dollar_dollar.undefine
                else:
                    _t1425 = None
                deconstruct_result793 = _t1425
                if deconstruct_result793 is not None:
                    assert deconstruct_result793 is not None
                    unwrapped794 = deconstruct_result793
                    self.pretty_undefine(unwrapped794)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1426 = _dollar_dollar.context
                    else:
                        _t1426 = None
                    deconstruct_result791 = _t1426
                    if deconstruct_result791 is not None:
                        assert deconstruct_result791 is not None
                        unwrapped792 = deconstruct_result791
                        self.pretty_context(unwrapped792)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1427 = _dollar_dollar.snapshot
                        else:
                            _t1427 = None
                        deconstruct_result789 = _t1427
                        if deconstruct_result789 is not None:
                            assert deconstruct_result789 is not None
                            unwrapped790 = deconstruct_result789
                            self.pretty_snapshot(unwrapped790)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat800 = self._try_flat(msg, self.pretty_define)
        if flat800 is not None:
            assert flat800 is not None
            self.write(flat800)
            return None
        else:
            _dollar_dollar = msg
            fields798 = _dollar_dollar.fragment
            assert fields798 is not None
            unwrapped_fields799 = fields798
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields799)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat807 = self._try_flat(msg, self.pretty_fragment)
        if flat807 is not None:
            assert flat807 is not None
            self.write(flat807)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields801 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields801 is not None
            unwrapped_fields802 = fields801
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field803 = unwrapped_fields802[0]
            self.pretty_new_fragment_id(field803)
            field804 = unwrapped_fields802[1]
            if not len(field804) == 0:
                self.newline()
                for i806, elem805 in enumerate(field804):
                    if (i806 > 0):
                        self.newline()
                    self.pretty_declaration(elem805)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat809 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat809 is not None:
            assert flat809 is not None
            self.write(flat809)
            return None
        else:
            fields808 = msg
            self.pretty_fragment_id(fields808)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat818 = self._try_flat(msg, self.pretty_declaration)
        if flat818 is not None:
            assert flat818 is not None
            self.write(flat818)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1428 = getattr(_dollar_dollar, 'def')
            else:
                _t1428 = None
            deconstruct_result816 = _t1428
            if deconstruct_result816 is not None:
                assert deconstruct_result816 is not None
                unwrapped817 = deconstruct_result816
                self.pretty_def(unwrapped817)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1429 = _dollar_dollar.algorithm
                else:
                    _t1429 = None
                deconstruct_result814 = _t1429
                if deconstruct_result814 is not None:
                    assert deconstruct_result814 is not None
                    unwrapped815 = deconstruct_result814
                    self.pretty_algorithm(unwrapped815)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1430 = _dollar_dollar.constraint
                    else:
                        _t1430 = None
                    deconstruct_result812 = _t1430
                    if deconstruct_result812 is not None:
                        assert deconstruct_result812 is not None
                        unwrapped813 = deconstruct_result812
                        self.pretty_constraint(unwrapped813)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1431 = _dollar_dollar.data
                        else:
                            _t1431 = None
                        deconstruct_result810 = _t1431
                        if deconstruct_result810 is not None:
                            assert deconstruct_result810 is not None
                            unwrapped811 = deconstruct_result810
                            self.pretty_data(unwrapped811)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat825 = self._try_flat(msg, self.pretty_def)
        if flat825 is not None:
            assert flat825 is not None
            self.write(flat825)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1432 = _dollar_dollar.attrs
            else:
                _t1432 = None
            fields819 = (_dollar_dollar.name, _dollar_dollar.body, _t1432,)
            assert fields819 is not None
            unwrapped_fields820 = fields819
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field821 = unwrapped_fields820[0]
            self.pretty_relation_id(field821)
            self.newline()
            field822 = unwrapped_fields820[1]
            self.pretty_abstraction(field822)
            field823 = unwrapped_fields820[2]
            if field823 is not None:
                self.newline()
                assert field823 is not None
                opt_val824 = field823
                self.pretty_attrs(opt_val824)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat830 = self._try_flat(msg, self.pretty_relation_id)
        if flat830 is not None:
            assert flat830 is not None
            self.write(flat830)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1434 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1433 = _t1434
            else:
                _t1433 = None
            deconstruct_result828 = _t1433
            if deconstruct_result828 is not None:
                assert deconstruct_result828 is not None
                unwrapped829 = deconstruct_result828
                self.write(":")
                self.write(unwrapped829)
            else:
                _dollar_dollar = msg
                _t1435 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result826 = _t1435
                if deconstruct_result826 is not None:
                    assert deconstruct_result826 is not None
                    unwrapped827 = deconstruct_result826
                    self.write(self.format_uint128(unwrapped827))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat835 = self._try_flat(msg, self.pretty_abstraction)
        if flat835 is not None:
            assert flat835 is not None
            self.write(flat835)
            return None
        else:
            _dollar_dollar = msg
            _t1436 = self.deconstruct_bindings(_dollar_dollar)
            fields831 = (_t1436, _dollar_dollar.value,)
            assert fields831 is not None
            unwrapped_fields832 = fields831
            self.write("(")
            self.indent()
            field833 = unwrapped_fields832[0]
            self.pretty_bindings(field833)
            self.newline()
            field834 = unwrapped_fields832[1]
            self.pretty_formula(field834)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat843 = self._try_flat(msg, self.pretty_bindings)
        if flat843 is not None:
            assert flat843 is not None
            self.write(flat843)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1437 = _dollar_dollar[1]
            else:
                _t1437 = None
            fields836 = (_dollar_dollar[0], _t1437,)
            assert fields836 is not None
            unwrapped_fields837 = fields836
            self.write("[")
            self.indent()
            field838 = unwrapped_fields837[0]
            for i840, elem839 in enumerate(field838):
                if (i840 > 0):
                    self.newline()
                self.pretty_binding(elem839)
            field841 = unwrapped_fields837[1]
            if field841 is not None:
                self.newline()
                assert field841 is not None
                opt_val842 = field841
                self.pretty_value_bindings(opt_val842)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat848 = self._try_flat(msg, self.pretty_binding)
        if flat848 is not None:
            assert flat848 is not None
            self.write(flat848)
            return None
        else:
            _dollar_dollar = msg
            fields844 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields844 is not None
            unwrapped_fields845 = fields844
            field846 = unwrapped_fields845[0]
            self.write(field846)
            self.write("::")
            field847 = unwrapped_fields845[1]
            self.pretty_type(field847)

    def pretty_type(self, msg: logic_pb2.Type):
        flat875 = self._try_flat(msg, self.pretty_type)
        if flat875 is not None:
            assert flat875 is not None
            self.write(flat875)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1438 = _dollar_dollar.unspecified_type
            else:
                _t1438 = None
            deconstruct_result873 = _t1438
            if deconstruct_result873 is not None:
                assert deconstruct_result873 is not None
                unwrapped874 = deconstruct_result873
                self.pretty_unspecified_type(unwrapped874)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1439 = _dollar_dollar.string_type
                else:
                    _t1439 = None
                deconstruct_result871 = _t1439
                if deconstruct_result871 is not None:
                    assert deconstruct_result871 is not None
                    unwrapped872 = deconstruct_result871
                    self.pretty_string_type(unwrapped872)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1440 = _dollar_dollar.int_type
                    else:
                        _t1440 = None
                    deconstruct_result869 = _t1440
                    if deconstruct_result869 is not None:
                        assert deconstruct_result869 is not None
                        unwrapped870 = deconstruct_result869
                        self.pretty_int_type(unwrapped870)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1441 = _dollar_dollar.float_type
                        else:
                            _t1441 = None
                        deconstruct_result867 = _t1441
                        if deconstruct_result867 is not None:
                            assert deconstruct_result867 is not None
                            unwrapped868 = deconstruct_result867
                            self.pretty_float_type(unwrapped868)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1442 = _dollar_dollar.uint128_type
                            else:
                                _t1442 = None
                            deconstruct_result865 = _t1442
                            if deconstruct_result865 is not None:
                                assert deconstruct_result865 is not None
                                unwrapped866 = deconstruct_result865
                                self.pretty_uint128_type(unwrapped866)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1443 = _dollar_dollar.int128_type
                                else:
                                    _t1443 = None
                                deconstruct_result863 = _t1443
                                if deconstruct_result863 is not None:
                                    assert deconstruct_result863 is not None
                                    unwrapped864 = deconstruct_result863
                                    self.pretty_int128_type(unwrapped864)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1444 = _dollar_dollar.date_type
                                    else:
                                        _t1444 = None
                                    deconstruct_result861 = _t1444
                                    if deconstruct_result861 is not None:
                                        assert deconstruct_result861 is not None
                                        unwrapped862 = deconstruct_result861
                                        self.pretty_date_type(unwrapped862)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1445 = _dollar_dollar.datetime_type
                                        else:
                                            _t1445 = None
                                        deconstruct_result859 = _t1445
                                        if deconstruct_result859 is not None:
                                            assert deconstruct_result859 is not None
                                            unwrapped860 = deconstruct_result859
                                            self.pretty_datetime_type(unwrapped860)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1446 = _dollar_dollar.missing_type
                                            else:
                                                _t1446 = None
                                            deconstruct_result857 = _t1446
                                            if deconstruct_result857 is not None:
                                                assert deconstruct_result857 is not None
                                                unwrapped858 = deconstruct_result857
                                                self.pretty_missing_type(unwrapped858)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1447 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1447 = None
                                                deconstruct_result855 = _t1447
                                                if deconstruct_result855 is not None:
                                                    assert deconstruct_result855 is not None
                                                    unwrapped856 = deconstruct_result855
                                                    self.pretty_decimal_type(unwrapped856)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1448 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1448 = None
                                                    deconstruct_result853 = _t1448
                                                    if deconstruct_result853 is not None:
                                                        assert deconstruct_result853 is not None
                                                        unwrapped854 = deconstruct_result853
                                                        self.pretty_boolean_type(unwrapped854)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1449 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1449 = None
                                                        deconstruct_result851 = _t1449
                                                        if deconstruct_result851 is not None:
                                                            assert deconstruct_result851 is not None
                                                            unwrapped852 = deconstruct_result851
                                                            self.pretty_int32_type(unwrapped852)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1450 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1450 = None
                                                            deconstruct_result849 = _t1450
                                                            if deconstruct_result849 is not None:
                                                                assert deconstruct_result849 is not None
                                                                unwrapped850 = deconstruct_result849
                                                                self.pretty_float32_type(unwrapped850)
                                                            else:
                                                                raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields876 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields877 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields878 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields879 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields880 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields881 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields882 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields883 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields884 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat889 = self._try_flat(msg, self.pretty_decimal_type)
        if flat889 is not None:
            assert flat889 is not None
            self.write(flat889)
            return None
        else:
            _dollar_dollar = msg
            fields885 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields885 is not None
            unwrapped_fields886 = fields885
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field887 = unwrapped_fields886[0]
            self.write(str(field887))
            self.newline()
            field888 = unwrapped_fields886[1]
            self.write(str(field888))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields890 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields891 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields892 = msg
        self.write("FLOAT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat896 = self._try_flat(msg, self.pretty_value_bindings)
        if flat896 is not None:
            assert flat896 is not None
            self.write(flat896)
            return None
        else:
            fields893 = msg
            self.write("|")
            if not len(fields893) == 0:
                self.write(" ")
                for i895, elem894 in enumerate(fields893):
                    if (i895 > 0):
                        self.newline()
                    self.pretty_binding(elem894)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat923 = self._try_flat(msg, self.pretty_formula)
        if flat923 is not None:
            assert flat923 is not None
            self.write(flat923)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1451 = _dollar_dollar.conjunction
            else:
                _t1451 = None
            deconstruct_result921 = _t1451
            if deconstruct_result921 is not None:
                assert deconstruct_result921 is not None
                unwrapped922 = deconstruct_result921
                self.pretty_true(unwrapped922)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1452 = _dollar_dollar.disjunction
                else:
                    _t1452 = None
                deconstruct_result919 = _t1452
                if deconstruct_result919 is not None:
                    assert deconstruct_result919 is not None
                    unwrapped920 = deconstruct_result919
                    self.pretty_false(unwrapped920)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1453 = _dollar_dollar.exists
                    else:
                        _t1453 = None
                    deconstruct_result917 = _t1453
                    if deconstruct_result917 is not None:
                        assert deconstruct_result917 is not None
                        unwrapped918 = deconstruct_result917
                        self.pretty_exists(unwrapped918)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1454 = _dollar_dollar.reduce
                        else:
                            _t1454 = None
                        deconstruct_result915 = _t1454
                        if deconstruct_result915 is not None:
                            assert deconstruct_result915 is not None
                            unwrapped916 = deconstruct_result915
                            self.pretty_reduce(unwrapped916)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1455 = _dollar_dollar.conjunction
                            else:
                                _t1455 = None
                            deconstruct_result913 = _t1455
                            if deconstruct_result913 is not None:
                                assert deconstruct_result913 is not None
                                unwrapped914 = deconstruct_result913
                                self.pretty_conjunction(unwrapped914)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1456 = _dollar_dollar.disjunction
                                else:
                                    _t1456 = None
                                deconstruct_result911 = _t1456
                                if deconstruct_result911 is not None:
                                    assert deconstruct_result911 is not None
                                    unwrapped912 = deconstruct_result911
                                    self.pretty_disjunction(unwrapped912)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1457 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1457 = None
                                    deconstruct_result909 = _t1457
                                    if deconstruct_result909 is not None:
                                        assert deconstruct_result909 is not None
                                        unwrapped910 = deconstruct_result909
                                        self.pretty_not(unwrapped910)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1458 = _dollar_dollar.ffi
                                        else:
                                            _t1458 = None
                                        deconstruct_result907 = _t1458
                                        if deconstruct_result907 is not None:
                                            assert deconstruct_result907 is not None
                                            unwrapped908 = deconstruct_result907
                                            self.pretty_ffi(unwrapped908)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1459 = _dollar_dollar.atom
                                            else:
                                                _t1459 = None
                                            deconstruct_result905 = _t1459
                                            if deconstruct_result905 is not None:
                                                assert deconstruct_result905 is not None
                                                unwrapped906 = deconstruct_result905
                                                self.pretty_atom(unwrapped906)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1460 = _dollar_dollar.pragma
                                                else:
                                                    _t1460 = None
                                                deconstruct_result903 = _t1460
                                                if deconstruct_result903 is not None:
                                                    assert deconstruct_result903 is not None
                                                    unwrapped904 = deconstruct_result903
                                                    self.pretty_pragma(unwrapped904)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1461 = _dollar_dollar.primitive
                                                    else:
                                                        _t1461 = None
                                                    deconstruct_result901 = _t1461
                                                    if deconstruct_result901 is not None:
                                                        assert deconstruct_result901 is not None
                                                        unwrapped902 = deconstruct_result901
                                                        self.pretty_primitive(unwrapped902)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1462 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1462 = None
                                                        deconstruct_result899 = _t1462
                                                        if deconstruct_result899 is not None:
                                                            assert deconstruct_result899 is not None
                                                            unwrapped900 = deconstruct_result899
                                                            self.pretty_rel_atom(unwrapped900)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1463 = _dollar_dollar.cast
                                                            else:
                                                                _t1463 = None
                                                            deconstruct_result897 = _t1463
                                                            if deconstruct_result897 is not None:
                                                                assert deconstruct_result897 is not None
                                                                unwrapped898 = deconstruct_result897
                                                                self.pretty_cast(unwrapped898)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields924 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields925 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat930 = self._try_flat(msg, self.pretty_exists)
        if flat930 is not None:
            assert flat930 is not None
            self.write(flat930)
            return None
        else:
            _dollar_dollar = msg
            _t1464 = self.deconstruct_bindings(_dollar_dollar.body)
            fields926 = (_t1464, _dollar_dollar.body.value,)
            assert fields926 is not None
            unwrapped_fields927 = fields926
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field928 = unwrapped_fields927[0]
            self.pretty_bindings(field928)
            self.newline()
            field929 = unwrapped_fields927[1]
            self.pretty_formula(field929)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat936 = self._try_flat(msg, self.pretty_reduce)
        if flat936 is not None:
            assert flat936 is not None
            self.write(flat936)
            return None
        else:
            _dollar_dollar = msg
            fields931 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields931 is not None
            unwrapped_fields932 = fields931
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field933 = unwrapped_fields932[0]
            self.pretty_abstraction(field933)
            self.newline()
            field934 = unwrapped_fields932[1]
            self.pretty_abstraction(field934)
            self.newline()
            field935 = unwrapped_fields932[2]
            self.pretty_terms(field935)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat940 = self._try_flat(msg, self.pretty_terms)
        if flat940 is not None:
            assert flat940 is not None
            self.write(flat940)
            return None
        else:
            fields937 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields937) == 0:
                self.newline()
                for i939, elem938 in enumerate(fields937):
                    if (i939 > 0):
                        self.newline()
                    self.pretty_term(elem938)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat945 = self._try_flat(msg, self.pretty_term)
        if flat945 is not None:
            assert flat945 is not None
            self.write(flat945)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1465 = _dollar_dollar.var
            else:
                _t1465 = None
            deconstruct_result943 = _t1465
            if deconstruct_result943 is not None:
                assert deconstruct_result943 is not None
                unwrapped944 = deconstruct_result943
                self.pretty_var(unwrapped944)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1466 = _dollar_dollar.constant
                else:
                    _t1466 = None
                deconstruct_result941 = _t1466
                if deconstruct_result941 is not None:
                    assert deconstruct_result941 is not None
                    unwrapped942 = deconstruct_result941
                    self.pretty_value(unwrapped942)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat948 = self._try_flat(msg, self.pretty_var)
        if flat948 is not None:
            assert flat948 is not None
            self.write(flat948)
            return None
        else:
            _dollar_dollar = msg
            fields946 = _dollar_dollar.name
            assert fields946 is not None
            unwrapped_fields947 = fields946
            self.write(unwrapped_fields947)

    def pretty_value(self, msg: logic_pb2.Value):
        flat972 = self._try_flat(msg, self.pretty_value)
        if flat972 is not None:
            assert flat972 is not None
            self.write(flat972)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1467 = _dollar_dollar.date_value
            else:
                _t1467 = None
            deconstruct_result970 = _t1467
            if deconstruct_result970 is not None:
                assert deconstruct_result970 is not None
                unwrapped971 = deconstruct_result970
                self.pretty_date(unwrapped971)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1468 = _dollar_dollar.datetime_value
                else:
                    _t1468 = None
                deconstruct_result968 = _t1468
                if deconstruct_result968 is not None:
                    assert deconstruct_result968 is not None
                    unwrapped969 = deconstruct_result968
                    self.pretty_datetime(unwrapped969)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1469 = _dollar_dollar.string_value
                    else:
                        _t1469 = None
                    deconstruct_result966 = _t1469
                    if deconstruct_result966 is not None:
                        assert deconstruct_result966 is not None
                        unwrapped967 = deconstruct_result966
                        self.write(self.format_string_value(unwrapped967))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1470 = _dollar_dollar.int32_value
                        else:
                            _t1470 = None
                        deconstruct_result964 = _t1470
                        if deconstruct_result964 is not None:
                            assert deconstruct_result964 is not None
                            unwrapped965 = deconstruct_result964
                            self.write((str(unwrapped965) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1471 = _dollar_dollar.int_value
                            else:
                                _t1471 = None
                            deconstruct_result962 = _t1471
                            if deconstruct_result962 is not None:
                                assert deconstruct_result962 is not None
                                unwrapped963 = deconstruct_result962
                                self.write(str(unwrapped963))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1472 = _dollar_dollar.float32_value
                                else:
                                    _t1472 = None
                                deconstruct_result960 = _t1472
                                if deconstruct_result960 is not None:
                                    assert deconstruct_result960 is not None
                                    unwrapped961 = deconstruct_result960
                                    self.write((self.format_float32_value(unwrapped961) + 'f32'))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1473 = _dollar_dollar.float_value
                                    else:
                                        _t1473 = None
                                    deconstruct_result958 = _t1473
                                    if deconstruct_result958 is not None:
                                        assert deconstruct_result958 is not None
                                        unwrapped959 = deconstruct_result958
                                        self.write(str(unwrapped959))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint128_value"):
                                            _t1474 = _dollar_dollar.uint128_value
                                        else:
                                            _t1474 = None
                                        deconstruct_result956 = _t1474
                                        if deconstruct_result956 is not None:
                                            assert deconstruct_result956 is not None
                                            unwrapped957 = deconstruct_result956
                                            self.write(self.format_uint128(unwrapped957))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("int128_value"):
                                                _t1475 = _dollar_dollar.int128_value
                                            else:
                                                _t1475 = None
                                            deconstruct_result954 = _t1475
                                            if deconstruct_result954 is not None:
                                                assert deconstruct_result954 is not None
                                                unwrapped955 = deconstruct_result954
                                                self.write(self.format_int128(unwrapped955))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_value"):
                                                    _t1476 = _dollar_dollar.decimal_value
                                                else:
                                                    _t1476 = None
                                                deconstruct_result952 = _t1476
                                                if deconstruct_result952 is not None:
                                                    assert deconstruct_result952 is not None
                                                    unwrapped953 = deconstruct_result952
                                                    self.write(self.format_decimal(unwrapped953))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_value"):
                                                        _t1477 = _dollar_dollar.boolean_value
                                                    else:
                                                        _t1477 = None
                                                    deconstruct_result950 = _t1477
                                                    if deconstruct_result950 is not None:
                                                        assert deconstruct_result950 is not None
                                                        unwrapped951 = deconstruct_result950
                                                        self.pretty_boolean_value(unwrapped951)
                                                    else:
                                                        fields949 = msg
                                                        self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat978 = self._try_flat(msg, self.pretty_date)
        if flat978 is not None:
            assert flat978 is not None
            self.write(flat978)
            return None
        else:
            _dollar_dollar = msg
            fields973 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields973 is not None
            unwrapped_fields974 = fields973
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field975 = unwrapped_fields974[0]
            self.write(str(field975))
            self.newline()
            field976 = unwrapped_fields974[1]
            self.write(str(field976))
            self.newline()
            field977 = unwrapped_fields974[2]
            self.write(str(field977))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat989 = self._try_flat(msg, self.pretty_datetime)
        if flat989 is not None:
            assert flat989 is not None
            self.write(flat989)
            return None
        else:
            _dollar_dollar = msg
            fields979 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields979 is not None
            unwrapped_fields980 = fields979
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field981 = unwrapped_fields980[0]
            self.write(str(field981))
            self.newline()
            field982 = unwrapped_fields980[1]
            self.write(str(field982))
            self.newline()
            field983 = unwrapped_fields980[2]
            self.write(str(field983))
            self.newline()
            field984 = unwrapped_fields980[3]
            self.write(str(field984))
            self.newline()
            field985 = unwrapped_fields980[4]
            self.write(str(field985))
            self.newline()
            field986 = unwrapped_fields980[5]
            self.write(str(field986))
            field987 = unwrapped_fields980[6]
            if field987 is not None:
                self.newline()
                assert field987 is not None
                opt_val988 = field987
                self.write(str(opt_val988))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat994 = self._try_flat(msg, self.pretty_conjunction)
        if flat994 is not None:
            assert flat994 is not None
            self.write(flat994)
            return None
        else:
            _dollar_dollar = msg
            fields990 = _dollar_dollar.args
            assert fields990 is not None
            unwrapped_fields991 = fields990
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields991) == 0:
                self.newline()
                for i993, elem992 in enumerate(unwrapped_fields991):
                    if (i993 > 0):
                        self.newline()
                    self.pretty_formula(elem992)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat999 = self._try_flat(msg, self.pretty_disjunction)
        if flat999 is not None:
            assert flat999 is not None
            self.write(flat999)
            return None
        else:
            _dollar_dollar = msg
            fields995 = _dollar_dollar.args
            assert fields995 is not None
            unwrapped_fields996 = fields995
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields996) == 0:
                self.newline()
                for i998, elem997 in enumerate(unwrapped_fields996):
                    if (i998 > 0):
                        self.newline()
                    self.pretty_formula(elem997)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1002 = self._try_flat(msg, self.pretty_not)
        if flat1002 is not None:
            assert flat1002 is not None
            self.write(flat1002)
            return None
        else:
            _dollar_dollar = msg
            fields1000 = _dollar_dollar.arg
            assert fields1000 is not None
            unwrapped_fields1001 = fields1000
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1001)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1008 = self._try_flat(msg, self.pretty_ffi)
        if flat1008 is not None:
            assert flat1008 is not None
            self.write(flat1008)
            return None
        else:
            _dollar_dollar = msg
            fields1003 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1003 is not None
            unwrapped_fields1004 = fields1003
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1005 = unwrapped_fields1004[0]
            self.pretty_name(field1005)
            self.newline()
            field1006 = unwrapped_fields1004[1]
            self.pretty_ffi_args(field1006)
            self.newline()
            field1007 = unwrapped_fields1004[2]
            self.pretty_terms(field1007)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1010 = self._try_flat(msg, self.pretty_name)
        if flat1010 is not None:
            assert flat1010 is not None
            self.write(flat1010)
            return None
        else:
            fields1009 = msg
            self.write(":")
            self.write(fields1009)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1014 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1014 is not None:
            assert flat1014 is not None
            self.write(flat1014)
            return None
        else:
            fields1011 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1011) == 0:
                self.newline()
                for i1013, elem1012 in enumerate(fields1011):
                    if (i1013 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1012)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1021 = self._try_flat(msg, self.pretty_atom)
        if flat1021 is not None:
            assert flat1021 is not None
            self.write(flat1021)
            return None
        else:
            _dollar_dollar = msg
            fields1015 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1015 is not None
            unwrapped_fields1016 = fields1015
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1017 = unwrapped_fields1016[0]
            self.pretty_relation_id(field1017)
            field1018 = unwrapped_fields1016[1]
            if not len(field1018) == 0:
                self.newline()
                for i1020, elem1019 in enumerate(field1018):
                    if (i1020 > 0):
                        self.newline()
                    self.pretty_term(elem1019)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1028 = self._try_flat(msg, self.pretty_pragma)
        if flat1028 is not None:
            assert flat1028 is not None
            self.write(flat1028)
            return None
        else:
            _dollar_dollar = msg
            fields1022 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1022 is not None
            unwrapped_fields1023 = fields1022
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1024 = unwrapped_fields1023[0]
            self.pretty_name(field1024)
            field1025 = unwrapped_fields1023[1]
            if not len(field1025) == 0:
                self.newline()
                for i1027, elem1026 in enumerate(field1025):
                    if (i1027 > 0):
                        self.newline()
                    self.pretty_term(elem1026)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1044 = self._try_flat(msg, self.pretty_primitive)
        if flat1044 is not None:
            assert flat1044 is not None
            self.write(flat1044)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1478 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1478 = None
            guard_result1043 = _t1478
            if guard_result1043 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1479 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1479 = None
                guard_result1042 = _t1479
                if guard_result1042 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1480 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1480 = None
                    guard_result1041 = _t1480
                    if guard_result1041 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1481 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1481 = None
                        guard_result1040 = _t1481
                        if guard_result1040 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1482 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1482 = None
                            guard_result1039 = _t1482
                            if guard_result1039 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1483 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1483 = None
                                guard_result1038 = _t1483
                                if guard_result1038 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1484 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1484 = None
                                    guard_result1037 = _t1484
                                    if guard_result1037 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1485 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1485 = None
                                        guard_result1036 = _t1485
                                        if guard_result1036 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1486 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1486 = None
                                            guard_result1035 = _t1486
                                            if guard_result1035 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1029 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1029 is not None
                                                unwrapped_fields1030 = fields1029
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1031 = unwrapped_fields1030[0]
                                                self.pretty_name(field1031)
                                                field1032 = unwrapped_fields1030[1]
                                                if not len(field1032) == 0:
                                                    self.newline()
                                                    for i1034, elem1033 in enumerate(field1032):
                                                        if (i1034 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1033)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1049 = self._try_flat(msg, self.pretty_eq)
        if flat1049 is not None:
            assert flat1049 is not None
            self.write(flat1049)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1487 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1487 = None
            fields1045 = _t1487
            assert fields1045 is not None
            unwrapped_fields1046 = fields1045
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1047 = unwrapped_fields1046[0]
            self.pretty_term(field1047)
            self.newline()
            field1048 = unwrapped_fields1046[1]
            self.pretty_term(field1048)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1054 = self._try_flat(msg, self.pretty_lt)
        if flat1054 is not None:
            assert flat1054 is not None
            self.write(flat1054)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1488 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1488 = None
            fields1050 = _t1488
            assert fields1050 is not None
            unwrapped_fields1051 = fields1050
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1052 = unwrapped_fields1051[0]
            self.pretty_term(field1052)
            self.newline()
            field1053 = unwrapped_fields1051[1]
            self.pretty_term(field1053)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1059 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1059 is not None:
            assert flat1059 is not None
            self.write(flat1059)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1489 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1489 = None
            fields1055 = _t1489
            assert fields1055 is not None
            unwrapped_fields1056 = fields1055
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1057 = unwrapped_fields1056[0]
            self.pretty_term(field1057)
            self.newline()
            field1058 = unwrapped_fields1056[1]
            self.pretty_term(field1058)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1064 = self._try_flat(msg, self.pretty_gt)
        if flat1064 is not None:
            assert flat1064 is not None
            self.write(flat1064)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1490 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1490 = None
            fields1060 = _t1490
            assert fields1060 is not None
            unwrapped_fields1061 = fields1060
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1062 = unwrapped_fields1061[0]
            self.pretty_term(field1062)
            self.newline()
            field1063 = unwrapped_fields1061[1]
            self.pretty_term(field1063)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1069 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1069 is not None:
            assert flat1069 is not None
            self.write(flat1069)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1491 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1491 = None
            fields1065 = _t1491
            assert fields1065 is not None
            unwrapped_fields1066 = fields1065
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1067 = unwrapped_fields1066[0]
            self.pretty_term(field1067)
            self.newline()
            field1068 = unwrapped_fields1066[1]
            self.pretty_term(field1068)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1075 = self._try_flat(msg, self.pretty_add)
        if flat1075 is not None:
            assert flat1075 is not None
            self.write(flat1075)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1492 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1492 = None
            fields1070 = _t1492
            assert fields1070 is not None
            unwrapped_fields1071 = fields1070
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1072 = unwrapped_fields1071[0]
            self.pretty_term(field1072)
            self.newline()
            field1073 = unwrapped_fields1071[1]
            self.pretty_term(field1073)
            self.newline()
            field1074 = unwrapped_fields1071[2]
            self.pretty_term(field1074)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1081 = self._try_flat(msg, self.pretty_minus)
        if flat1081 is not None:
            assert flat1081 is not None
            self.write(flat1081)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1493 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1493 = None
            fields1076 = _t1493
            assert fields1076 is not None
            unwrapped_fields1077 = fields1076
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1078 = unwrapped_fields1077[0]
            self.pretty_term(field1078)
            self.newline()
            field1079 = unwrapped_fields1077[1]
            self.pretty_term(field1079)
            self.newline()
            field1080 = unwrapped_fields1077[2]
            self.pretty_term(field1080)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1087 = self._try_flat(msg, self.pretty_multiply)
        if flat1087 is not None:
            assert flat1087 is not None
            self.write(flat1087)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1494 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1494 = None
            fields1082 = _t1494
            assert fields1082 is not None
            unwrapped_fields1083 = fields1082
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1084 = unwrapped_fields1083[0]
            self.pretty_term(field1084)
            self.newline()
            field1085 = unwrapped_fields1083[1]
            self.pretty_term(field1085)
            self.newline()
            field1086 = unwrapped_fields1083[2]
            self.pretty_term(field1086)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1093 = self._try_flat(msg, self.pretty_divide)
        if flat1093 is not None:
            assert flat1093 is not None
            self.write(flat1093)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1495 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1495 = None
            fields1088 = _t1495
            assert fields1088 is not None
            unwrapped_fields1089 = fields1088
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1090 = unwrapped_fields1089[0]
            self.pretty_term(field1090)
            self.newline()
            field1091 = unwrapped_fields1089[1]
            self.pretty_term(field1091)
            self.newline()
            field1092 = unwrapped_fields1089[2]
            self.pretty_term(field1092)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1098 = self._try_flat(msg, self.pretty_rel_term)
        if flat1098 is not None:
            assert flat1098 is not None
            self.write(flat1098)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1496 = _dollar_dollar.specialized_value
            else:
                _t1496 = None
            deconstruct_result1096 = _t1496
            if deconstruct_result1096 is not None:
                assert deconstruct_result1096 is not None
                unwrapped1097 = deconstruct_result1096
                self.pretty_specialized_value(unwrapped1097)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1497 = _dollar_dollar.term
                else:
                    _t1497 = None
                deconstruct_result1094 = _t1497
                if deconstruct_result1094 is not None:
                    assert deconstruct_result1094 is not None
                    unwrapped1095 = deconstruct_result1094
                    self.pretty_term(unwrapped1095)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1100 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1100 is not None:
            assert flat1100 is not None
            self.write(flat1100)
            return None
        else:
            fields1099 = msg
            self.write("#")
            self.pretty_raw_value(fields1099)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1107 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1107 is not None:
            assert flat1107 is not None
            self.write(flat1107)
            return None
        else:
            _dollar_dollar = msg
            fields1101 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1101 is not None
            unwrapped_fields1102 = fields1101
            self.write("(relatom")
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
                    self.pretty_rel_term(elem1105)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1112 = self._try_flat(msg, self.pretty_cast)
        if flat1112 is not None:
            assert flat1112 is not None
            self.write(flat1112)
            return None
        else:
            _dollar_dollar = msg
            fields1108 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1108 is not None
            unwrapped_fields1109 = fields1108
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1110 = unwrapped_fields1109[0]
            self.pretty_term(field1110)
            self.newline()
            field1111 = unwrapped_fields1109[1]
            self.pretty_term(field1111)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1116 = self._try_flat(msg, self.pretty_attrs)
        if flat1116 is not None:
            assert flat1116 is not None
            self.write(flat1116)
            return None
        else:
            fields1113 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1113) == 0:
                self.newline()
                for i1115, elem1114 in enumerate(fields1113):
                    if (i1115 > 0):
                        self.newline()
                    self.pretty_attribute(elem1114)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1123 = self._try_flat(msg, self.pretty_attribute)
        if flat1123 is not None:
            assert flat1123 is not None
            self.write(flat1123)
            return None
        else:
            _dollar_dollar = msg
            fields1117 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1117 is not None
            unwrapped_fields1118 = fields1117
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1119 = unwrapped_fields1118[0]
            self.pretty_name(field1119)
            field1120 = unwrapped_fields1118[1]
            if not len(field1120) == 0:
                self.newline()
                for i1122, elem1121 in enumerate(field1120):
                    if (i1122 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1121)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1130 = self._try_flat(msg, self.pretty_algorithm)
        if flat1130 is not None:
            assert flat1130 is not None
            self.write(flat1130)
            return None
        else:
            _dollar_dollar = msg
            fields1124 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            assert fields1124 is not None
            unwrapped_fields1125 = fields1124
            self.write("(algorithm")
            self.indent_sexp()
            field1126 = unwrapped_fields1125[0]
            if not len(field1126) == 0:
                self.newline()
                for i1128, elem1127 in enumerate(field1126):
                    if (i1128 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1127)
            self.newline()
            field1129 = unwrapped_fields1125[1]
            self.pretty_script(field1129)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1135 = self._try_flat(msg, self.pretty_script)
        if flat1135 is not None:
            assert flat1135 is not None
            self.write(flat1135)
            return None
        else:
            _dollar_dollar = msg
            fields1131 = _dollar_dollar.constructs
            assert fields1131 is not None
            unwrapped_fields1132 = fields1131
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1132) == 0:
                self.newline()
                for i1134, elem1133 in enumerate(unwrapped_fields1132):
                    if (i1134 > 0):
                        self.newline()
                    self.pretty_construct(elem1133)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1140 = self._try_flat(msg, self.pretty_construct)
        if flat1140 is not None:
            assert flat1140 is not None
            self.write(flat1140)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1498 = _dollar_dollar.loop
            else:
                _t1498 = None
            deconstruct_result1138 = _t1498
            if deconstruct_result1138 is not None:
                assert deconstruct_result1138 is not None
                unwrapped1139 = deconstruct_result1138
                self.pretty_loop(unwrapped1139)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1499 = _dollar_dollar.instruction
                else:
                    _t1499 = None
                deconstruct_result1136 = _t1499
                if deconstruct_result1136 is not None:
                    assert deconstruct_result1136 is not None
                    unwrapped1137 = deconstruct_result1136
                    self.pretty_instruction(unwrapped1137)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1145 = self._try_flat(msg, self.pretty_loop)
        if flat1145 is not None:
            assert flat1145 is not None
            self.write(flat1145)
            return None
        else:
            _dollar_dollar = msg
            fields1141 = (_dollar_dollar.init, _dollar_dollar.body,)
            assert fields1141 is not None
            unwrapped_fields1142 = fields1141
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1143 = unwrapped_fields1142[0]
            self.pretty_init(field1143)
            self.newline()
            field1144 = unwrapped_fields1142[1]
            self.pretty_script(field1144)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1149 = self._try_flat(msg, self.pretty_init)
        if flat1149 is not None:
            assert flat1149 is not None
            self.write(flat1149)
            return None
        else:
            fields1146 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1146) == 0:
                self.newline()
                for i1148, elem1147 in enumerate(fields1146):
                    if (i1148 > 0):
                        self.newline()
                    self.pretty_instruction(elem1147)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1160 = self._try_flat(msg, self.pretty_instruction)
        if flat1160 is not None:
            assert flat1160 is not None
            self.write(flat1160)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1500 = _dollar_dollar.assign
            else:
                _t1500 = None
            deconstruct_result1158 = _t1500
            if deconstruct_result1158 is not None:
                assert deconstruct_result1158 is not None
                unwrapped1159 = deconstruct_result1158
                self.pretty_assign(unwrapped1159)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1501 = _dollar_dollar.upsert
                else:
                    _t1501 = None
                deconstruct_result1156 = _t1501
                if deconstruct_result1156 is not None:
                    assert deconstruct_result1156 is not None
                    unwrapped1157 = deconstruct_result1156
                    self.pretty_upsert(unwrapped1157)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1502 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1502 = None
                    deconstruct_result1154 = _t1502
                    if deconstruct_result1154 is not None:
                        assert deconstruct_result1154 is not None
                        unwrapped1155 = deconstruct_result1154
                        self.pretty_break(unwrapped1155)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1503 = _dollar_dollar.monoid_def
                        else:
                            _t1503 = None
                        deconstruct_result1152 = _t1503
                        if deconstruct_result1152 is not None:
                            assert deconstruct_result1152 is not None
                            unwrapped1153 = deconstruct_result1152
                            self.pretty_monoid_def(unwrapped1153)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1504 = _dollar_dollar.monus_def
                            else:
                                _t1504 = None
                            deconstruct_result1150 = _t1504
                            if deconstruct_result1150 is not None:
                                assert deconstruct_result1150 is not None
                                unwrapped1151 = deconstruct_result1150
                                self.pretty_monus_def(unwrapped1151)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1167 = self._try_flat(msg, self.pretty_assign)
        if flat1167 is not None:
            assert flat1167 is not None
            self.write(flat1167)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1505 = _dollar_dollar.attrs
            else:
                _t1505 = None
            fields1161 = (_dollar_dollar.name, _dollar_dollar.body, _t1505,)
            assert fields1161 is not None
            unwrapped_fields1162 = fields1161
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1163 = unwrapped_fields1162[0]
            self.pretty_relation_id(field1163)
            self.newline()
            field1164 = unwrapped_fields1162[1]
            self.pretty_abstraction(field1164)
            field1165 = unwrapped_fields1162[2]
            if field1165 is not None:
                self.newline()
                assert field1165 is not None
                opt_val1166 = field1165
                self.pretty_attrs(opt_val1166)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1174 = self._try_flat(msg, self.pretty_upsert)
        if flat1174 is not None:
            assert flat1174 is not None
            self.write(flat1174)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1506 = _dollar_dollar.attrs
            else:
                _t1506 = None
            fields1168 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1506,)
            assert fields1168 is not None
            unwrapped_fields1169 = fields1168
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1170 = unwrapped_fields1169[0]
            self.pretty_relation_id(field1170)
            self.newline()
            field1171 = unwrapped_fields1169[1]
            self.pretty_abstraction_with_arity(field1171)
            field1172 = unwrapped_fields1169[2]
            if field1172 is not None:
                self.newline()
                assert field1172 is not None
                opt_val1173 = field1172
                self.pretty_attrs(opt_val1173)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1179 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1179 is not None:
            assert flat1179 is not None
            self.write(flat1179)
            return None
        else:
            _dollar_dollar = msg
            _t1507 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1175 = (_t1507, _dollar_dollar[0].value,)
            assert fields1175 is not None
            unwrapped_fields1176 = fields1175
            self.write("(")
            self.indent()
            field1177 = unwrapped_fields1176[0]
            self.pretty_bindings(field1177)
            self.newline()
            field1178 = unwrapped_fields1176[1]
            self.pretty_formula(field1178)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1186 = self._try_flat(msg, self.pretty_break)
        if flat1186 is not None:
            assert flat1186 is not None
            self.write(flat1186)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1508 = _dollar_dollar.attrs
            else:
                _t1508 = None
            fields1180 = (_dollar_dollar.name, _dollar_dollar.body, _t1508,)
            assert fields1180 is not None
            unwrapped_fields1181 = fields1180
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1182 = unwrapped_fields1181[0]
            self.pretty_relation_id(field1182)
            self.newline()
            field1183 = unwrapped_fields1181[1]
            self.pretty_abstraction(field1183)
            field1184 = unwrapped_fields1181[2]
            if field1184 is not None:
                self.newline()
                assert field1184 is not None
                opt_val1185 = field1184
                self.pretty_attrs(opt_val1185)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1194 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1194 is not None:
            assert flat1194 is not None
            self.write(flat1194)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1509 = _dollar_dollar.attrs
            else:
                _t1509 = None
            fields1187 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1509,)
            assert fields1187 is not None
            unwrapped_fields1188 = fields1187
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1189 = unwrapped_fields1188[0]
            self.pretty_monoid(field1189)
            self.newline()
            field1190 = unwrapped_fields1188[1]
            self.pretty_relation_id(field1190)
            self.newline()
            field1191 = unwrapped_fields1188[2]
            self.pretty_abstraction_with_arity(field1191)
            field1192 = unwrapped_fields1188[3]
            if field1192 is not None:
                self.newline()
                assert field1192 is not None
                opt_val1193 = field1192
                self.pretty_attrs(opt_val1193)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1203 = self._try_flat(msg, self.pretty_monoid)
        if flat1203 is not None:
            assert flat1203 is not None
            self.write(flat1203)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1510 = _dollar_dollar.or_monoid
            else:
                _t1510 = None
            deconstruct_result1201 = _t1510
            if deconstruct_result1201 is not None:
                assert deconstruct_result1201 is not None
                unwrapped1202 = deconstruct_result1201
                self.pretty_or_monoid(unwrapped1202)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1511 = _dollar_dollar.min_monoid
                else:
                    _t1511 = None
                deconstruct_result1199 = _t1511
                if deconstruct_result1199 is not None:
                    assert deconstruct_result1199 is not None
                    unwrapped1200 = deconstruct_result1199
                    self.pretty_min_monoid(unwrapped1200)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1512 = _dollar_dollar.max_monoid
                    else:
                        _t1512 = None
                    deconstruct_result1197 = _t1512
                    if deconstruct_result1197 is not None:
                        assert deconstruct_result1197 is not None
                        unwrapped1198 = deconstruct_result1197
                        self.pretty_max_monoid(unwrapped1198)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1513 = _dollar_dollar.sum_monoid
                        else:
                            _t1513 = None
                        deconstruct_result1195 = _t1513
                        if deconstruct_result1195 is not None:
                            assert deconstruct_result1195 is not None
                            unwrapped1196 = deconstruct_result1195
                            self.pretty_sum_monoid(unwrapped1196)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1204 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1207 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1207 is not None:
            assert flat1207 is not None
            self.write(flat1207)
            return None
        else:
            _dollar_dollar = msg
            fields1205 = _dollar_dollar.type
            assert fields1205 is not None
            unwrapped_fields1206 = fields1205
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1206)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1210 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1210 is not None:
            assert flat1210 is not None
            self.write(flat1210)
            return None
        else:
            _dollar_dollar = msg
            fields1208 = _dollar_dollar.type
            assert fields1208 is not None
            unwrapped_fields1209 = fields1208
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1209)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1213 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1213 is not None:
            assert flat1213 is not None
            self.write(flat1213)
            return None
        else:
            _dollar_dollar = msg
            fields1211 = _dollar_dollar.type
            assert fields1211 is not None
            unwrapped_fields1212 = fields1211
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1212)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1221 = self._try_flat(msg, self.pretty_monus_def)
        if flat1221 is not None:
            assert flat1221 is not None
            self.write(flat1221)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1514 = _dollar_dollar.attrs
            else:
                _t1514 = None
            fields1214 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1514,)
            assert fields1214 is not None
            unwrapped_fields1215 = fields1214
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1216 = unwrapped_fields1215[0]
            self.pretty_monoid(field1216)
            self.newline()
            field1217 = unwrapped_fields1215[1]
            self.pretty_relation_id(field1217)
            self.newline()
            field1218 = unwrapped_fields1215[2]
            self.pretty_abstraction_with_arity(field1218)
            field1219 = unwrapped_fields1215[3]
            if field1219 is not None:
                self.newline()
                assert field1219 is not None
                opt_val1220 = field1219
                self.pretty_attrs(opt_val1220)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1228 = self._try_flat(msg, self.pretty_constraint)
        if flat1228 is not None:
            assert flat1228 is not None
            self.write(flat1228)
            return None
        else:
            _dollar_dollar = msg
            fields1222 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1222 is not None
            unwrapped_fields1223 = fields1222
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1224 = unwrapped_fields1223[0]
            self.pretty_relation_id(field1224)
            self.newline()
            field1225 = unwrapped_fields1223[1]
            self.pretty_abstraction(field1225)
            self.newline()
            field1226 = unwrapped_fields1223[2]
            self.pretty_functional_dependency_keys(field1226)
            self.newline()
            field1227 = unwrapped_fields1223[3]
            self.pretty_functional_dependency_values(field1227)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1232 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1232 is not None:
            assert flat1232 is not None
            self.write(flat1232)
            return None
        else:
            fields1229 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1229) == 0:
                self.newline()
                for i1231, elem1230 in enumerate(fields1229):
                    if (i1231 > 0):
                        self.newline()
                    self.pretty_var(elem1230)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1236 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1236 is not None:
            assert flat1236 is not None
            self.write(flat1236)
            return None
        else:
            fields1233 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1233) == 0:
                self.newline()
                for i1235, elem1234 in enumerate(fields1233):
                    if (i1235 > 0):
                        self.newline()
                    self.pretty_var(elem1234)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1243 = self._try_flat(msg, self.pretty_data)
        if flat1243 is not None:
            assert flat1243 is not None
            self.write(flat1243)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1515 = _dollar_dollar.edb
            else:
                _t1515 = None
            deconstruct_result1241 = _t1515
            if deconstruct_result1241 is not None:
                assert deconstruct_result1241 is not None
                unwrapped1242 = deconstruct_result1241
                self.pretty_edb(unwrapped1242)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1516 = _dollar_dollar.betree_relation
                else:
                    _t1516 = None
                deconstruct_result1239 = _t1516
                if deconstruct_result1239 is not None:
                    assert deconstruct_result1239 is not None
                    unwrapped1240 = deconstruct_result1239
                    self.pretty_betree_relation(unwrapped1240)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1517 = _dollar_dollar.csv_data
                    else:
                        _t1517 = None
                    deconstruct_result1237 = _t1517
                    if deconstruct_result1237 is not None:
                        assert deconstruct_result1237 is not None
                        unwrapped1238 = deconstruct_result1237
                        self.pretty_csv_data(unwrapped1238)
                    else:
                        raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1249 = self._try_flat(msg, self.pretty_edb)
        if flat1249 is not None:
            assert flat1249 is not None
            self.write(flat1249)
            return None
        else:
            _dollar_dollar = msg
            fields1244 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1244 is not None
            unwrapped_fields1245 = fields1244
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1246 = unwrapped_fields1245[0]
            self.pretty_relation_id(field1246)
            self.newline()
            field1247 = unwrapped_fields1245[1]
            self.pretty_edb_path(field1247)
            self.newline()
            field1248 = unwrapped_fields1245[2]
            self.pretty_edb_types(field1248)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1253 = self._try_flat(msg, self.pretty_edb_path)
        if flat1253 is not None:
            assert flat1253 is not None
            self.write(flat1253)
            return None
        else:
            fields1250 = msg
            self.write("[")
            self.indent()
            for i1252, elem1251 in enumerate(fields1250):
                if (i1252 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1251))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1257 = self._try_flat(msg, self.pretty_edb_types)
        if flat1257 is not None:
            assert flat1257 is not None
            self.write(flat1257)
            return None
        else:
            fields1254 = msg
            self.write("[")
            self.indent()
            for i1256, elem1255 in enumerate(fields1254):
                if (i1256 > 0):
                    self.newline()
                self.pretty_type(elem1255)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1262 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1262 is not None:
            assert flat1262 is not None
            self.write(flat1262)
            return None
        else:
            _dollar_dollar = msg
            fields1258 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1258 is not None
            unwrapped_fields1259 = fields1258
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1260 = unwrapped_fields1259[0]
            self.pretty_relation_id(field1260)
            self.newline()
            field1261 = unwrapped_fields1259[1]
            self.pretty_betree_info(field1261)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1268 = self._try_flat(msg, self.pretty_betree_info)
        if flat1268 is not None:
            assert flat1268 is not None
            self.write(flat1268)
            return None
        else:
            _dollar_dollar = msg
            _t1518 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1263 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1518,)
            assert fields1263 is not None
            unwrapped_fields1264 = fields1263
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1265 = unwrapped_fields1264[0]
            self.pretty_betree_info_key_types(field1265)
            self.newline()
            field1266 = unwrapped_fields1264[1]
            self.pretty_betree_info_value_types(field1266)
            self.newline()
            field1267 = unwrapped_fields1264[2]
            self.pretty_config_dict(field1267)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1272 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1272 is not None:
            assert flat1272 is not None
            self.write(flat1272)
            return None
        else:
            fields1269 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1269) == 0:
                self.newline()
                for i1271, elem1270 in enumerate(fields1269):
                    if (i1271 > 0):
                        self.newline()
                    self.pretty_type(elem1270)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1276 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1276 is not None:
            assert flat1276 is not None
            self.write(flat1276)
            return None
        else:
            fields1273 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1273) == 0:
                self.newline()
                for i1275, elem1274 in enumerate(fields1273):
                    if (i1275 > 0):
                        self.newline()
                    self.pretty_type(elem1274)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1283 = self._try_flat(msg, self.pretty_csv_data)
        if flat1283 is not None:
            assert flat1283 is not None
            self.write(flat1283)
            return None
        else:
            _dollar_dollar = msg
            fields1277 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1277 is not None
            unwrapped_fields1278 = fields1277
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1279 = unwrapped_fields1278[0]
            self.pretty_csvlocator(field1279)
            self.newline()
            field1280 = unwrapped_fields1278[1]
            self.pretty_csv_config(field1280)
            self.newline()
            field1281 = unwrapped_fields1278[2]
            self.pretty_gnf_columns(field1281)
            self.newline()
            field1282 = unwrapped_fields1278[3]
            self.pretty_csv_asof(field1282)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1290 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1290 is not None:
            assert flat1290 is not None
            self.write(flat1290)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1519 = _dollar_dollar.paths
            else:
                _t1519 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1520 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1520 = None
            fields1284 = (_t1519, _t1520,)
            assert fields1284 is not None
            unwrapped_fields1285 = fields1284
            self.write("(csv_locator")
            self.indent_sexp()
            field1286 = unwrapped_fields1285[0]
            if field1286 is not None:
                self.newline()
                assert field1286 is not None
                opt_val1287 = field1286
                self.pretty_csv_locator_paths(opt_val1287)
            field1288 = unwrapped_fields1285[1]
            if field1288 is not None:
                self.newline()
                assert field1288 is not None
                opt_val1289 = field1288
                self.pretty_csv_locator_inline_data(opt_val1289)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1294 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1294 is not None:
            assert flat1294 is not None
            self.write(flat1294)
            return None
        else:
            fields1291 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1291) == 0:
                self.newline()
                for i1293, elem1292 in enumerate(fields1291):
                    if (i1293 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1292))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1296 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1296 is not None:
            assert flat1296 is not None
            self.write(flat1296)
            return None
        else:
            fields1295 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1295))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1299 = self._try_flat(msg, self.pretty_csv_config)
        if flat1299 is not None:
            assert flat1299 is not None
            self.write(flat1299)
            return None
        else:
            _dollar_dollar = msg
            _t1521 = self.deconstruct_csv_config(_dollar_dollar)
            fields1297 = _t1521
            assert fields1297 is not None
            unwrapped_fields1298 = fields1297
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1298)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1303 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1303 is not None:
            assert flat1303 is not None
            self.write(flat1303)
            return None
        else:
            fields1300 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1300) == 0:
                self.newline()
                for i1302, elem1301 in enumerate(fields1300):
                    if (i1302 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1301)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1312 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1312 is not None:
            assert flat1312 is not None
            self.write(flat1312)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1522 = _dollar_dollar.target_id
            else:
                _t1522 = None
            fields1304 = (_dollar_dollar.column_path, _t1522, _dollar_dollar.types,)
            assert fields1304 is not None
            unwrapped_fields1305 = fields1304
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1306 = unwrapped_fields1305[0]
            self.pretty_gnf_column_path(field1306)
            field1307 = unwrapped_fields1305[1]
            if field1307 is not None:
                self.newline()
                assert field1307 is not None
                opt_val1308 = field1307
                self.pretty_relation_id(opt_val1308)
            self.newline()
            self.write("[")
            field1309 = unwrapped_fields1305[2]
            for i1311, elem1310 in enumerate(field1309):
                if (i1311 > 0):
                    self.newline()
                self.pretty_type(elem1310)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1319 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1319 is not None:
            assert flat1319 is not None
            self.write(flat1319)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1523 = _dollar_dollar[0]
            else:
                _t1523 = None
            deconstruct_result1317 = _t1523
            if deconstruct_result1317 is not None:
                assert deconstruct_result1317 is not None
                unwrapped1318 = deconstruct_result1317
                self.write(self.format_string_value(unwrapped1318))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1524 = _dollar_dollar
                else:
                    _t1524 = None
                deconstruct_result1313 = _t1524
                if deconstruct_result1313 is not None:
                    assert deconstruct_result1313 is not None
                    unwrapped1314 = deconstruct_result1313
                    self.write("[")
                    self.indent()
                    for i1316, elem1315 in enumerate(unwrapped1314):
                        if (i1316 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1315))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1321 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1321 is not None:
            assert flat1321 is not None
            self.write(flat1321)
            return None
        else:
            fields1320 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1320))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1324 = self._try_flat(msg, self.pretty_undefine)
        if flat1324 is not None:
            assert flat1324 is not None
            self.write(flat1324)
            return None
        else:
            _dollar_dollar = msg
            fields1322 = _dollar_dollar.fragment_id
            assert fields1322 is not None
            unwrapped_fields1323 = fields1322
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1323)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1329 = self._try_flat(msg, self.pretty_context)
        if flat1329 is not None:
            assert flat1329 is not None
            self.write(flat1329)
            return None
        else:
            _dollar_dollar = msg
            fields1325 = _dollar_dollar.relations
            assert fields1325 is not None
            unwrapped_fields1326 = fields1325
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1326) == 0:
                self.newline()
                for i1328, elem1327 in enumerate(unwrapped_fields1326):
                    if (i1328 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1327)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1334 = self._try_flat(msg, self.pretty_snapshot)
        if flat1334 is not None:
            assert flat1334 is not None
            self.write(flat1334)
            return None
        else:
            _dollar_dollar = msg
            fields1330 = _dollar_dollar.mappings
            assert fields1330 is not None
            unwrapped_fields1331 = fields1330
            self.write("(snapshot")
            self.indent_sexp()
            if not len(unwrapped_fields1331) == 0:
                self.newline()
                for i1333, elem1332 in enumerate(unwrapped_fields1331):
                    if (i1333 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1332)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1339 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1339 is not None:
            assert flat1339 is not None
            self.write(flat1339)
            return None
        else:
            _dollar_dollar = msg
            fields1335 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1335 is not None
            unwrapped_fields1336 = fields1335
            field1337 = unwrapped_fields1336[0]
            self.pretty_edb_path(field1337)
            self.write(" ")
            field1338 = unwrapped_fields1336[1]
            self.pretty_relation_id(field1338)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1343 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1343 is not None:
            assert flat1343 is not None
            self.write(flat1343)
            return None
        else:
            fields1340 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1340) == 0:
                self.newline()
                for i1342, elem1341 in enumerate(fields1340):
                    if (i1342 > 0):
                        self.newline()
                    self.pretty_read(elem1341)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1354 = self._try_flat(msg, self.pretty_read)
        if flat1354 is not None:
            assert flat1354 is not None
            self.write(flat1354)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1525 = _dollar_dollar.demand
            else:
                _t1525 = None
            deconstruct_result1352 = _t1525
            if deconstruct_result1352 is not None:
                assert deconstruct_result1352 is not None
                unwrapped1353 = deconstruct_result1352
                self.pretty_demand(unwrapped1353)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1526 = _dollar_dollar.output
                else:
                    _t1526 = None
                deconstruct_result1350 = _t1526
                if deconstruct_result1350 is not None:
                    assert deconstruct_result1350 is not None
                    unwrapped1351 = deconstruct_result1350
                    self.pretty_output(unwrapped1351)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1527 = _dollar_dollar.what_if
                    else:
                        _t1527 = None
                    deconstruct_result1348 = _t1527
                    if deconstruct_result1348 is not None:
                        assert deconstruct_result1348 is not None
                        unwrapped1349 = deconstruct_result1348
                        self.pretty_what_if(unwrapped1349)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1528 = _dollar_dollar.abort
                        else:
                            _t1528 = None
                        deconstruct_result1346 = _t1528
                        if deconstruct_result1346 is not None:
                            assert deconstruct_result1346 is not None
                            unwrapped1347 = deconstruct_result1346
                            self.pretty_abort(unwrapped1347)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1529 = _dollar_dollar.export
                            else:
                                _t1529 = None
                            deconstruct_result1344 = _t1529
                            if deconstruct_result1344 is not None:
                                assert deconstruct_result1344 is not None
                                unwrapped1345 = deconstruct_result1344
                                self.pretty_export(unwrapped1345)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1357 = self._try_flat(msg, self.pretty_demand)
        if flat1357 is not None:
            assert flat1357 is not None
            self.write(flat1357)
            return None
        else:
            _dollar_dollar = msg
            fields1355 = _dollar_dollar.relation_id
            assert fields1355 is not None
            unwrapped_fields1356 = fields1355
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1356)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1362 = self._try_flat(msg, self.pretty_output)
        if flat1362 is not None:
            assert flat1362 is not None
            self.write(flat1362)
            return None
        else:
            _dollar_dollar = msg
            fields1358 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1358 is not None
            unwrapped_fields1359 = fields1358
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1360 = unwrapped_fields1359[0]
            self.pretty_name(field1360)
            self.newline()
            field1361 = unwrapped_fields1359[1]
            self.pretty_relation_id(field1361)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1367 = self._try_flat(msg, self.pretty_what_if)
        if flat1367 is not None:
            assert flat1367 is not None
            self.write(flat1367)
            return None
        else:
            _dollar_dollar = msg
            fields1363 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1363 is not None
            unwrapped_fields1364 = fields1363
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1365 = unwrapped_fields1364[0]
            self.pretty_name(field1365)
            self.newline()
            field1366 = unwrapped_fields1364[1]
            self.pretty_epoch(field1366)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1373 = self._try_flat(msg, self.pretty_abort)
        if flat1373 is not None:
            assert flat1373 is not None
            self.write(flat1373)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1530 = _dollar_dollar.name
            else:
                _t1530 = None
            fields1368 = (_t1530, _dollar_dollar.relation_id,)
            assert fields1368 is not None
            unwrapped_fields1369 = fields1368
            self.write("(abort")
            self.indent_sexp()
            field1370 = unwrapped_fields1369[0]
            if field1370 is not None:
                self.newline()
                assert field1370 is not None
                opt_val1371 = field1370
                self.pretty_name(opt_val1371)
            self.newline()
            field1372 = unwrapped_fields1369[1]
            self.pretty_relation_id(field1372)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1376 = self._try_flat(msg, self.pretty_export)
        if flat1376 is not None:
            assert flat1376 is not None
            self.write(flat1376)
            return None
        else:
            _dollar_dollar = msg
            fields1374 = _dollar_dollar.csv_config
            assert fields1374 is not None
            unwrapped_fields1375 = fields1374
            self.write("(export")
            self.indent_sexp()
            self.newline()
            self.pretty_export_csv_config(unwrapped_fields1375)
            self.dedent()
            self.write(")")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1387 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1387 is not None:
            assert flat1387 is not None
            self.write(flat1387)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1531 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1531 = None
            deconstruct_result1382 = _t1531
            if deconstruct_result1382 is not None:
                assert deconstruct_result1382 is not None
                unwrapped1383 = deconstruct_result1382
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1384 = unwrapped1383[0]
                self.pretty_export_csv_path(field1384)
                self.newline()
                field1385 = unwrapped1383[1]
                self.pretty_export_csv_source(field1385)
                self.newline()
                field1386 = unwrapped1383[2]
                self.pretty_csv_config(field1386)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1533 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1532 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1533,)
                else:
                    _t1532 = None
                deconstruct_result1377 = _t1532
                if deconstruct_result1377 is not None:
                    assert deconstruct_result1377 is not None
                    unwrapped1378 = deconstruct_result1377
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1379 = unwrapped1378[0]
                    self.pretty_export_csv_path(field1379)
                    self.newline()
                    field1380 = unwrapped1378[1]
                    self.pretty_export_csv_columns_list(field1380)
                    self.newline()
                    field1381 = unwrapped1378[2]
                    self.pretty_config_dict(field1381)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1389 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1389 is not None:
            assert flat1389 is not None
            self.write(flat1389)
            return None
        else:
            fields1388 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1388))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1396 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1396 is not None:
            assert flat1396 is not None
            self.write(flat1396)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1534 = _dollar_dollar.gnf_columns.columns
            else:
                _t1534 = None
            deconstruct_result1392 = _t1534
            if deconstruct_result1392 is not None:
                assert deconstruct_result1392 is not None
                unwrapped1393 = deconstruct_result1392
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1393) == 0:
                    self.newline()
                    for i1395, elem1394 in enumerate(unwrapped1393):
                        if (i1395 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1394)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1535 = _dollar_dollar.table_def
                else:
                    _t1535 = None
                deconstruct_result1390 = _t1535
                if deconstruct_result1390 is not None:
                    assert deconstruct_result1390 is not None
                    unwrapped1391 = deconstruct_result1390
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1391)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1401 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1401 is not None:
            assert flat1401 is not None
            self.write(flat1401)
            return None
        else:
            _dollar_dollar = msg
            fields1397 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1397 is not None
            unwrapped_fields1398 = fields1397
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1399 = unwrapped_fields1398[0]
            self.write(self.format_string_value(field1399))
            self.newline()
            field1400 = unwrapped_fields1398[1]
            self.pretty_relation_id(field1400)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1405 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1405 is not None:
            assert flat1405 is not None
            self.write(flat1405)
            return None
        else:
            fields1402 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1402) == 0:
                self.newline()
                for i1404, elem1403 in enumerate(fields1402):
                    if (i1404 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1403)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1574 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1574)
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
