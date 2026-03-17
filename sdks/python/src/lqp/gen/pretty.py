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
        _t1553 = logic_pb2.Value(int32_value=v)
        return _t1553

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1554 = logic_pb2.Value(int_value=v)
        return _t1554

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1555 = logic_pb2.Value(float_value=v)
        return _t1555

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1556 = logic_pb2.Value(string_value=v)
        return _t1556

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1557 = logic_pb2.Value(boolean_value=v)
        return _t1557

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1558 = logic_pb2.Value(uint128_value=v)
        return _t1558

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1559 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1559,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1560 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1560,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1561 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1561,))
        _t1562 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1562,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1563 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1563,))
        _t1564 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1564,))
        if msg.new_line != "":
            _t1565 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1565,))
        _t1566 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1566,))
        _t1567 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1567,))
        _t1568 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1568,))
        if msg.comment != "":
            _t1569 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1569,))
        for missing_string in msg.missing_strings:
            _t1570 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1570,))
        _t1571 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1571,))
        _t1572 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1572,))
        _t1573 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1573,))
        if msg.partition_size_mb != 0:
            _t1574 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1574,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1575 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1575,))
        _t1576 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1576,))
        _t1577 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1577,))
        _t1578 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1578,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1579 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1579,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1580 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1580,))
        _t1581 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1581,))
        _t1582 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1582,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1583 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1583,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1584 = self._make_value_string(msg.compression)
            result.append(("compression", _t1584,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1585 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1585,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1586 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1586,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1587 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1587,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1588 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1588,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1589 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1589,))
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
            _t1590 = None
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
        flat719 = self._try_flat(msg, self.pretty_transaction)
        if flat719 is not None:
            assert flat719 is not None
            self.write(flat719)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1420 = _dollar_dollar.configure
            else:
                _t1420 = None
            if _dollar_dollar.HasField("sync"):
                _t1421 = _dollar_dollar.sync
            else:
                _t1421 = None
            fields710 = (_t1420, _t1421, _dollar_dollar.epochs,)
            assert fields710 is not None
            unwrapped_fields711 = fields710
            self.write("(transaction")
            self.indent_sexp()
            field712 = unwrapped_fields711[0]
            if field712 is not None:
                self.newline()
                assert field712 is not None
                opt_val713 = field712
                self.pretty_configure(opt_val713)
            field714 = unwrapped_fields711[1]
            if field714 is not None:
                self.newline()
                assert field714 is not None
                opt_val715 = field714
                self.pretty_sync(opt_val715)
            field716 = unwrapped_fields711[2]
            if not len(field716) == 0:
                self.newline()
                for i718, elem717 in enumerate(field716):
                    if (i718 > 0):
                        self.newline()
                    self.pretty_epoch(elem717)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat722 = self._try_flat(msg, self.pretty_configure)
        if flat722 is not None:
            assert flat722 is not None
            self.write(flat722)
            return None
        else:
            _dollar_dollar = msg
            _t1422 = self.deconstruct_configure(_dollar_dollar)
            fields720 = _t1422
            assert fields720 is not None
            unwrapped_fields721 = fields720
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields721)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat726 = self._try_flat(msg, self.pretty_config_dict)
        if flat726 is not None:
            assert flat726 is not None
            self.write(flat726)
            return None
        else:
            fields723 = msg
            self.write("{")
            self.indent()
            if not len(fields723) == 0:
                self.newline()
                for i725, elem724 in enumerate(fields723):
                    if (i725 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem724)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat731 = self._try_flat(msg, self.pretty_config_key_value)
        if flat731 is not None:
            assert flat731 is not None
            self.write(flat731)
            return None
        else:
            _dollar_dollar = msg
            fields727 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields727 is not None
            unwrapped_fields728 = fields727
            self.write(":")
            field729 = unwrapped_fields728[0]
            self.write(field729)
            self.write(" ")
            field730 = unwrapped_fields728[1]
            self.pretty_raw_value(field730)

    def pretty_raw_value(self, msg: logic_pb2.Value):
        flat757 = self._try_flat(msg, self.pretty_raw_value)
        if flat757 is not None:
            assert flat757 is not None
            self.write(flat757)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1423 = _dollar_dollar.date_value
            else:
                _t1423 = None
            deconstruct_result755 = _t1423
            if deconstruct_result755 is not None:
                assert deconstruct_result755 is not None
                unwrapped756 = deconstruct_result755
                self.pretty_raw_date(unwrapped756)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1424 = _dollar_dollar.datetime_value
                else:
                    _t1424 = None
                deconstruct_result753 = _t1424
                if deconstruct_result753 is not None:
                    assert deconstruct_result753 is not None
                    unwrapped754 = deconstruct_result753
                    self.pretty_raw_datetime(unwrapped754)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1425 = _dollar_dollar.string_value
                    else:
                        _t1425 = None
                    deconstruct_result751 = _t1425
                    if deconstruct_result751 is not None:
                        assert deconstruct_result751 is not None
                        unwrapped752 = deconstruct_result751
                        self.write(self.format_string_value(unwrapped752))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1426 = _dollar_dollar.int32_value
                        else:
                            _t1426 = None
                        deconstruct_result749 = _t1426
                        if deconstruct_result749 is not None:
                            assert deconstruct_result749 is not None
                            unwrapped750 = deconstruct_result749
                            self.write((str(unwrapped750) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1427 = _dollar_dollar.int_value
                            else:
                                _t1427 = None
                            deconstruct_result747 = _t1427
                            if deconstruct_result747 is not None:
                                assert deconstruct_result747 is not None
                                unwrapped748 = deconstruct_result747
                                self.write(str(unwrapped748))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1428 = _dollar_dollar.float32_value
                                else:
                                    _t1428 = None
                                deconstruct_result745 = _t1428
                                if deconstruct_result745 is not None:
                                    assert deconstruct_result745 is not None
                                    unwrapped746 = deconstruct_result745
                                    self.write(self.format_float32_literal(unwrapped746))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1429 = _dollar_dollar.float_value
                                    else:
                                        _t1429 = None
                                    deconstruct_result743 = _t1429
                                    if deconstruct_result743 is not None:
                                        assert deconstruct_result743 is not None
                                        unwrapped744 = deconstruct_result743
                                        self.write(str(unwrapped744))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1430 = _dollar_dollar.uint32_value
                                        else:
                                            _t1430 = None
                                        deconstruct_result741 = _t1430
                                        if deconstruct_result741 is not None:
                                            assert deconstruct_result741 is not None
                                            unwrapped742 = deconstruct_result741
                                            self.write((str(unwrapped742) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1431 = _dollar_dollar.uint128_value
                                            else:
                                                _t1431 = None
                                            deconstruct_result739 = _t1431
                                            if deconstruct_result739 is not None:
                                                assert deconstruct_result739 is not None
                                                unwrapped740 = deconstruct_result739
                                                self.write(self.format_uint128(unwrapped740))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1432 = _dollar_dollar.int128_value
                                                else:
                                                    _t1432 = None
                                                deconstruct_result737 = _t1432
                                                if deconstruct_result737 is not None:
                                                    assert deconstruct_result737 is not None
                                                    unwrapped738 = deconstruct_result737
                                                    self.write(self.format_int128(unwrapped738))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1433 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1433 = None
                                                    deconstruct_result735 = _t1433
                                                    if deconstruct_result735 is not None:
                                                        assert deconstruct_result735 is not None
                                                        unwrapped736 = deconstruct_result735
                                                        self.write(self.format_decimal(unwrapped736))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1434 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1434 = None
                                                        deconstruct_result733 = _t1434
                                                        if deconstruct_result733 is not None:
                                                            assert deconstruct_result733 is not None
                                                            unwrapped734 = deconstruct_result733
                                                            self.pretty_boolean_value(unwrapped734)
                                                        else:
                                                            fields732 = msg
                                                            self.write("missing")

    def pretty_raw_date(self, msg: logic_pb2.DateValue):
        flat763 = self._try_flat(msg, self.pretty_raw_date)
        if flat763 is not None:
            assert flat763 is not None
            self.write(flat763)
            return None
        else:
            _dollar_dollar = msg
            fields758 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields758 is not None
            unwrapped_fields759 = fields758
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field760 = unwrapped_fields759[0]
            self.write(str(field760))
            self.newline()
            field761 = unwrapped_fields759[1]
            self.write(str(field761))
            self.newline()
            field762 = unwrapped_fields759[2]
            self.write(str(field762))
            self.dedent()
            self.write(")")

    def pretty_raw_datetime(self, msg: logic_pb2.DateTimeValue):
        flat774 = self._try_flat(msg, self.pretty_raw_datetime)
        if flat774 is not None:
            assert flat774 is not None
            self.write(flat774)
            return None
        else:
            _dollar_dollar = msg
            fields764 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields764 is not None
            unwrapped_fields765 = fields764
            self.write("(datetime")
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
            self.newline()
            field769 = unwrapped_fields765[3]
            self.write(str(field769))
            self.newline()
            field770 = unwrapped_fields765[4]
            self.write(str(field770))
            self.newline()
            field771 = unwrapped_fields765[5]
            self.write(str(field771))
            field772 = unwrapped_fields765[6]
            if field772 is not None:
                self.newline()
                assert field772 is not None
                opt_val773 = field772
                self.write(str(opt_val773))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1435 = ()
        else:
            _t1435 = None
        deconstruct_result777 = _t1435
        if deconstruct_result777 is not None:
            assert deconstruct_result777 is not None
            unwrapped778 = deconstruct_result777
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1436 = ()
            else:
                _t1436 = None
            deconstruct_result775 = _t1436
            if deconstruct_result775 is not None:
                assert deconstruct_result775 is not None
                unwrapped776 = deconstruct_result775
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat783 = self._try_flat(msg, self.pretty_sync)
        if flat783 is not None:
            assert flat783 is not None
            self.write(flat783)
            return None
        else:
            _dollar_dollar = msg
            fields779 = _dollar_dollar.fragments
            assert fields779 is not None
            unwrapped_fields780 = fields779
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields780) == 0:
                self.newline()
                for i782, elem781 in enumerate(unwrapped_fields780):
                    if (i782 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem781)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat786 = self._try_flat(msg, self.pretty_fragment_id)
        if flat786 is not None:
            assert flat786 is not None
            self.write(flat786)
            return None
        else:
            _dollar_dollar = msg
            fields784 = self.fragment_id_to_string(_dollar_dollar)
            assert fields784 is not None
            unwrapped_fields785 = fields784
            self.write(":")
            self.write(unwrapped_fields785)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat793 = self._try_flat(msg, self.pretty_epoch)
        if flat793 is not None:
            assert flat793 is not None
            self.write(flat793)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1437 = _dollar_dollar.writes
            else:
                _t1437 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1438 = _dollar_dollar.reads
            else:
                _t1438 = None
            fields787 = (_t1437, _t1438,)
            assert fields787 is not None
            unwrapped_fields788 = fields787
            self.write("(epoch")
            self.indent_sexp()
            field789 = unwrapped_fields788[0]
            if field789 is not None:
                self.newline()
                assert field789 is not None
                opt_val790 = field789
                self.pretty_epoch_writes(opt_val790)
            field791 = unwrapped_fields788[1]
            if field791 is not None:
                self.newline()
                assert field791 is not None
                opt_val792 = field791
                self.pretty_epoch_reads(opt_val792)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat797 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat797 is not None:
            assert flat797 is not None
            self.write(flat797)
            return None
        else:
            fields794 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields794) == 0:
                self.newline()
                for i796, elem795 in enumerate(fields794):
                    if (i796 > 0):
                        self.newline()
                    self.pretty_write(elem795)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat806 = self._try_flat(msg, self.pretty_write)
        if flat806 is not None:
            assert flat806 is not None
            self.write(flat806)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1439 = _dollar_dollar.define
            else:
                _t1439 = None
            deconstruct_result804 = _t1439
            if deconstruct_result804 is not None:
                assert deconstruct_result804 is not None
                unwrapped805 = deconstruct_result804
                self.pretty_define(unwrapped805)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1440 = _dollar_dollar.undefine
                else:
                    _t1440 = None
                deconstruct_result802 = _t1440
                if deconstruct_result802 is not None:
                    assert deconstruct_result802 is not None
                    unwrapped803 = deconstruct_result802
                    self.pretty_undefine(unwrapped803)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1441 = _dollar_dollar.context
                    else:
                        _t1441 = None
                    deconstruct_result800 = _t1441
                    if deconstruct_result800 is not None:
                        assert deconstruct_result800 is not None
                        unwrapped801 = deconstruct_result800
                        self.pretty_context(unwrapped801)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1442 = _dollar_dollar.snapshot
                        else:
                            _t1442 = None
                        deconstruct_result798 = _t1442
                        if deconstruct_result798 is not None:
                            assert deconstruct_result798 is not None
                            unwrapped799 = deconstruct_result798
                            self.pretty_snapshot(unwrapped799)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat809 = self._try_flat(msg, self.pretty_define)
        if flat809 is not None:
            assert flat809 is not None
            self.write(flat809)
            return None
        else:
            _dollar_dollar = msg
            fields807 = _dollar_dollar.fragment
            assert fields807 is not None
            unwrapped_fields808 = fields807
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields808)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat816 = self._try_flat(msg, self.pretty_fragment)
        if flat816 is not None:
            assert flat816 is not None
            self.write(flat816)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields810 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields810 is not None
            unwrapped_fields811 = fields810
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field812 = unwrapped_fields811[0]
            self.pretty_new_fragment_id(field812)
            field813 = unwrapped_fields811[1]
            if not len(field813) == 0:
                self.newline()
                for i815, elem814 in enumerate(field813):
                    if (i815 > 0):
                        self.newline()
                    self.pretty_declaration(elem814)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat818 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat818 is not None:
            assert flat818 is not None
            self.write(flat818)
            return None
        else:
            fields817 = msg
            self.pretty_fragment_id(fields817)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat827 = self._try_flat(msg, self.pretty_declaration)
        if flat827 is not None:
            assert flat827 is not None
            self.write(flat827)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1443 = getattr(_dollar_dollar, 'def')
            else:
                _t1443 = None
            deconstruct_result825 = _t1443
            if deconstruct_result825 is not None:
                assert deconstruct_result825 is not None
                unwrapped826 = deconstruct_result825
                self.pretty_def(unwrapped826)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1444 = _dollar_dollar.algorithm
                else:
                    _t1444 = None
                deconstruct_result823 = _t1444
                if deconstruct_result823 is not None:
                    assert deconstruct_result823 is not None
                    unwrapped824 = deconstruct_result823
                    self.pretty_algorithm(unwrapped824)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1445 = _dollar_dollar.constraint
                    else:
                        _t1445 = None
                    deconstruct_result821 = _t1445
                    if deconstruct_result821 is not None:
                        assert deconstruct_result821 is not None
                        unwrapped822 = deconstruct_result821
                        self.pretty_constraint(unwrapped822)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1446 = _dollar_dollar.data
                        else:
                            _t1446 = None
                        deconstruct_result819 = _t1446
                        if deconstruct_result819 is not None:
                            assert deconstruct_result819 is not None
                            unwrapped820 = deconstruct_result819
                            self.pretty_data(unwrapped820)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat834 = self._try_flat(msg, self.pretty_def)
        if flat834 is not None:
            assert flat834 is not None
            self.write(flat834)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1447 = _dollar_dollar.attrs
            else:
                _t1447 = None
            fields828 = (_dollar_dollar.name, _dollar_dollar.body, _t1447,)
            assert fields828 is not None
            unwrapped_fields829 = fields828
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field830 = unwrapped_fields829[0]
            self.pretty_relation_id(field830)
            self.newline()
            field831 = unwrapped_fields829[1]
            self.pretty_abstraction(field831)
            field832 = unwrapped_fields829[2]
            if field832 is not None:
                self.newline()
                assert field832 is not None
                opt_val833 = field832
                self.pretty_attrs(opt_val833)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat839 = self._try_flat(msg, self.pretty_relation_id)
        if flat839 is not None:
            assert flat839 is not None
            self.write(flat839)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1449 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1448 = _t1449
            else:
                _t1448 = None
            deconstruct_result837 = _t1448
            if deconstruct_result837 is not None:
                assert deconstruct_result837 is not None
                unwrapped838 = deconstruct_result837
                self.write(":")
                self.write(unwrapped838)
            else:
                _dollar_dollar = msg
                _t1450 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result835 = _t1450
                if deconstruct_result835 is not None:
                    assert deconstruct_result835 is not None
                    unwrapped836 = deconstruct_result835
                    self.write(self.format_uint128(unwrapped836))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat844 = self._try_flat(msg, self.pretty_abstraction)
        if flat844 is not None:
            assert flat844 is not None
            self.write(flat844)
            return None
        else:
            _dollar_dollar = msg
            _t1451 = self.deconstruct_bindings(_dollar_dollar)
            fields840 = (_t1451, _dollar_dollar.value,)
            assert fields840 is not None
            unwrapped_fields841 = fields840
            self.write("(")
            self.indent()
            field842 = unwrapped_fields841[0]
            self.pretty_bindings(field842)
            self.newline()
            field843 = unwrapped_fields841[1]
            self.pretty_formula(field843)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat852 = self._try_flat(msg, self.pretty_bindings)
        if flat852 is not None:
            assert flat852 is not None
            self.write(flat852)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1452 = _dollar_dollar[1]
            else:
                _t1452 = None
            fields845 = (_dollar_dollar[0], _t1452,)
            assert fields845 is not None
            unwrapped_fields846 = fields845
            self.write("[")
            self.indent()
            field847 = unwrapped_fields846[0]
            for i849, elem848 in enumerate(field847):
                if (i849 > 0):
                    self.newline()
                self.pretty_binding(elem848)
            field850 = unwrapped_fields846[1]
            if field850 is not None:
                self.newline()
                assert field850 is not None
                opt_val851 = field850
                self.pretty_value_bindings(opt_val851)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat857 = self._try_flat(msg, self.pretty_binding)
        if flat857 is not None:
            assert flat857 is not None
            self.write(flat857)
            return None
        else:
            _dollar_dollar = msg
            fields853 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields853 is not None
            unwrapped_fields854 = fields853
            field855 = unwrapped_fields854[0]
            self.write(field855)
            self.write("::")
            field856 = unwrapped_fields854[1]
            self.pretty_type(field856)

    def pretty_type(self, msg: logic_pb2.Type):
        flat886 = self._try_flat(msg, self.pretty_type)
        if flat886 is not None:
            assert flat886 is not None
            self.write(flat886)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1453 = _dollar_dollar.unspecified_type
            else:
                _t1453 = None
            deconstruct_result884 = _t1453
            if deconstruct_result884 is not None:
                assert deconstruct_result884 is not None
                unwrapped885 = deconstruct_result884
                self.pretty_unspecified_type(unwrapped885)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1454 = _dollar_dollar.string_type
                else:
                    _t1454 = None
                deconstruct_result882 = _t1454
                if deconstruct_result882 is not None:
                    assert deconstruct_result882 is not None
                    unwrapped883 = deconstruct_result882
                    self.pretty_string_type(unwrapped883)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1455 = _dollar_dollar.int_type
                    else:
                        _t1455 = None
                    deconstruct_result880 = _t1455
                    if deconstruct_result880 is not None:
                        assert deconstruct_result880 is not None
                        unwrapped881 = deconstruct_result880
                        self.pretty_int_type(unwrapped881)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1456 = _dollar_dollar.float_type
                        else:
                            _t1456 = None
                        deconstruct_result878 = _t1456
                        if deconstruct_result878 is not None:
                            assert deconstruct_result878 is not None
                            unwrapped879 = deconstruct_result878
                            self.pretty_float_type(unwrapped879)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1457 = _dollar_dollar.uint128_type
                            else:
                                _t1457 = None
                            deconstruct_result876 = _t1457
                            if deconstruct_result876 is not None:
                                assert deconstruct_result876 is not None
                                unwrapped877 = deconstruct_result876
                                self.pretty_uint128_type(unwrapped877)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1458 = _dollar_dollar.int128_type
                                else:
                                    _t1458 = None
                                deconstruct_result874 = _t1458
                                if deconstruct_result874 is not None:
                                    assert deconstruct_result874 is not None
                                    unwrapped875 = deconstruct_result874
                                    self.pretty_int128_type(unwrapped875)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1459 = _dollar_dollar.date_type
                                    else:
                                        _t1459 = None
                                    deconstruct_result872 = _t1459
                                    if deconstruct_result872 is not None:
                                        assert deconstruct_result872 is not None
                                        unwrapped873 = deconstruct_result872
                                        self.pretty_date_type(unwrapped873)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1460 = _dollar_dollar.datetime_type
                                        else:
                                            _t1460 = None
                                        deconstruct_result870 = _t1460
                                        if deconstruct_result870 is not None:
                                            assert deconstruct_result870 is not None
                                            unwrapped871 = deconstruct_result870
                                            self.pretty_datetime_type(unwrapped871)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1461 = _dollar_dollar.missing_type
                                            else:
                                                _t1461 = None
                                            deconstruct_result868 = _t1461
                                            if deconstruct_result868 is not None:
                                                assert deconstruct_result868 is not None
                                                unwrapped869 = deconstruct_result868
                                                self.pretty_missing_type(unwrapped869)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1462 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1462 = None
                                                deconstruct_result866 = _t1462
                                                if deconstruct_result866 is not None:
                                                    assert deconstruct_result866 is not None
                                                    unwrapped867 = deconstruct_result866
                                                    self.pretty_decimal_type(unwrapped867)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1463 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1463 = None
                                                    deconstruct_result864 = _t1463
                                                    if deconstruct_result864 is not None:
                                                        assert deconstruct_result864 is not None
                                                        unwrapped865 = deconstruct_result864
                                                        self.pretty_boolean_type(unwrapped865)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1464 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1464 = None
                                                        deconstruct_result862 = _t1464
                                                        if deconstruct_result862 is not None:
                                                            assert deconstruct_result862 is not None
                                                            unwrapped863 = deconstruct_result862
                                                            self.pretty_int32_type(unwrapped863)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1465 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1465 = None
                                                            deconstruct_result860 = _t1465
                                                            if deconstruct_result860 is not None:
                                                                assert deconstruct_result860 is not None
                                                                unwrapped861 = deconstruct_result860
                                                                self.pretty_float32_type(unwrapped861)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1466 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1466 = None
                                                                deconstruct_result858 = _t1466
                                                                if deconstruct_result858 is not None:
                                                                    assert deconstruct_result858 is not None
                                                                    unwrapped859 = deconstruct_result858
                                                                    self.pretty_uint32_type(unwrapped859)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields887 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields888 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields889 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields890 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields891 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields892 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields893 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields894 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields895 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat900 = self._try_flat(msg, self.pretty_decimal_type)
        if flat900 is not None:
            assert flat900 is not None
            self.write(flat900)
            return None
        else:
            _dollar_dollar = msg
            fields896 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields896 is not None
            unwrapped_fields897 = fields896
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field898 = unwrapped_fields897[0]
            self.write(str(field898))
            self.newline()
            field899 = unwrapped_fields897[1]
            self.write(str(field899))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields901 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields902 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields903 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields904 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat908 = self._try_flat(msg, self.pretty_value_bindings)
        if flat908 is not None:
            assert flat908 is not None
            self.write(flat908)
            return None
        else:
            fields905 = msg
            self.write("|")
            if not len(fields905) == 0:
                self.write(" ")
                for i907, elem906 in enumerate(fields905):
                    if (i907 > 0):
                        self.newline()
                    self.pretty_binding(elem906)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat935 = self._try_flat(msg, self.pretty_formula)
        if flat935 is not None:
            assert flat935 is not None
            self.write(flat935)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1467 = _dollar_dollar.conjunction
            else:
                _t1467 = None
            deconstruct_result933 = _t1467
            if deconstruct_result933 is not None:
                assert deconstruct_result933 is not None
                unwrapped934 = deconstruct_result933
                self.pretty_true(unwrapped934)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1468 = _dollar_dollar.disjunction
                else:
                    _t1468 = None
                deconstruct_result931 = _t1468
                if deconstruct_result931 is not None:
                    assert deconstruct_result931 is not None
                    unwrapped932 = deconstruct_result931
                    self.pretty_false(unwrapped932)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1469 = _dollar_dollar.exists
                    else:
                        _t1469 = None
                    deconstruct_result929 = _t1469
                    if deconstruct_result929 is not None:
                        assert deconstruct_result929 is not None
                        unwrapped930 = deconstruct_result929
                        self.pretty_exists(unwrapped930)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1470 = _dollar_dollar.reduce
                        else:
                            _t1470 = None
                        deconstruct_result927 = _t1470
                        if deconstruct_result927 is not None:
                            assert deconstruct_result927 is not None
                            unwrapped928 = deconstruct_result927
                            self.pretty_reduce(unwrapped928)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1471 = _dollar_dollar.conjunction
                            else:
                                _t1471 = None
                            deconstruct_result925 = _t1471
                            if deconstruct_result925 is not None:
                                assert deconstruct_result925 is not None
                                unwrapped926 = deconstruct_result925
                                self.pretty_conjunction(unwrapped926)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1472 = _dollar_dollar.disjunction
                                else:
                                    _t1472 = None
                                deconstruct_result923 = _t1472
                                if deconstruct_result923 is not None:
                                    assert deconstruct_result923 is not None
                                    unwrapped924 = deconstruct_result923
                                    self.pretty_disjunction(unwrapped924)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1473 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1473 = None
                                    deconstruct_result921 = _t1473
                                    if deconstruct_result921 is not None:
                                        assert deconstruct_result921 is not None
                                        unwrapped922 = deconstruct_result921
                                        self.pretty_not(unwrapped922)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1474 = _dollar_dollar.ffi
                                        else:
                                            _t1474 = None
                                        deconstruct_result919 = _t1474
                                        if deconstruct_result919 is not None:
                                            assert deconstruct_result919 is not None
                                            unwrapped920 = deconstruct_result919
                                            self.pretty_ffi(unwrapped920)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1475 = _dollar_dollar.atom
                                            else:
                                                _t1475 = None
                                            deconstruct_result917 = _t1475
                                            if deconstruct_result917 is not None:
                                                assert deconstruct_result917 is not None
                                                unwrapped918 = deconstruct_result917
                                                self.pretty_atom(unwrapped918)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1476 = _dollar_dollar.pragma
                                                else:
                                                    _t1476 = None
                                                deconstruct_result915 = _t1476
                                                if deconstruct_result915 is not None:
                                                    assert deconstruct_result915 is not None
                                                    unwrapped916 = deconstruct_result915
                                                    self.pretty_pragma(unwrapped916)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1477 = _dollar_dollar.primitive
                                                    else:
                                                        _t1477 = None
                                                    deconstruct_result913 = _t1477
                                                    if deconstruct_result913 is not None:
                                                        assert deconstruct_result913 is not None
                                                        unwrapped914 = deconstruct_result913
                                                        self.pretty_primitive(unwrapped914)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1478 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1478 = None
                                                        deconstruct_result911 = _t1478
                                                        if deconstruct_result911 is not None:
                                                            assert deconstruct_result911 is not None
                                                            unwrapped912 = deconstruct_result911
                                                            self.pretty_rel_atom(unwrapped912)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1479 = _dollar_dollar.cast
                                                            else:
                                                                _t1479 = None
                                                            deconstruct_result909 = _t1479
                                                            if deconstruct_result909 is not None:
                                                                assert deconstruct_result909 is not None
                                                                unwrapped910 = deconstruct_result909
                                                                self.pretty_cast(unwrapped910)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields936 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields937 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat942 = self._try_flat(msg, self.pretty_exists)
        if flat942 is not None:
            assert flat942 is not None
            self.write(flat942)
            return None
        else:
            _dollar_dollar = msg
            _t1480 = self.deconstruct_bindings(_dollar_dollar.body)
            fields938 = (_t1480, _dollar_dollar.body.value,)
            assert fields938 is not None
            unwrapped_fields939 = fields938
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field940 = unwrapped_fields939[0]
            self.pretty_bindings(field940)
            self.newline()
            field941 = unwrapped_fields939[1]
            self.pretty_formula(field941)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat948 = self._try_flat(msg, self.pretty_reduce)
        if flat948 is not None:
            assert flat948 is not None
            self.write(flat948)
            return None
        else:
            _dollar_dollar = msg
            fields943 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields943 is not None
            unwrapped_fields944 = fields943
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field945 = unwrapped_fields944[0]
            self.pretty_abstraction(field945)
            self.newline()
            field946 = unwrapped_fields944[1]
            self.pretty_abstraction(field946)
            self.newline()
            field947 = unwrapped_fields944[2]
            self.pretty_terms(field947)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat952 = self._try_flat(msg, self.pretty_terms)
        if flat952 is not None:
            assert flat952 is not None
            self.write(flat952)
            return None
        else:
            fields949 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields949) == 0:
                self.newline()
                for i951, elem950 in enumerate(fields949):
                    if (i951 > 0):
                        self.newline()
                    self.pretty_term(elem950)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat957 = self._try_flat(msg, self.pretty_term)
        if flat957 is not None:
            assert flat957 is not None
            self.write(flat957)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1481 = _dollar_dollar.var
            else:
                _t1481 = None
            deconstruct_result955 = _t1481
            if deconstruct_result955 is not None:
                assert deconstruct_result955 is not None
                unwrapped956 = deconstruct_result955
                self.pretty_var(unwrapped956)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1482 = _dollar_dollar.constant
                else:
                    _t1482 = None
                deconstruct_result953 = _t1482
                if deconstruct_result953 is not None:
                    assert deconstruct_result953 is not None
                    unwrapped954 = deconstruct_result953
                    self.pretty_value(unwrapped954)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat960 = self._try_flat(msg, self.pretty_var)
        if flat960 is not None:
            assert flat960 is not None
            self.write(flat960)
            return None
        else:
            _dollar_dollar = msg
            fields958 = _dollar_dollar.name
            assert fields958 is not None
            unwrapped_fields959 = fields958
            self.write(unwrapped_fields959)

    def pretty_value(self, msg: logic_pb2.Value):
        flat986 = self._try_flat(msg, self.pretty_value)
        if flat986 is not None:
            assert flat986 is not None
            self.write(flat986)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1483 = _dollar_dollar.date_value
            else:
                _t1483 = None
            deconstruct_result984 = _t1483
            if deconstruct_result984 is not None:
                assert deconstruct_result984 is not None
                unwrapped985 = deconstruct_result984
                self.pretty_date(unwrapped985)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1484 = _dollar_dollar.datetime_value
                else:
                    _t1484 = None
                deconstruct_result982 = _t1484
                if deconstruct_result982 is not None:
                    assert deconstruct_result982 is not None
                    unwrapped983 = deconstruct_result982
                    self.pretty_datetime(unwrapped983)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1485 = _dollar_dollar.string_value
                    else:
                        _t1485 = None
                    deconstruct_result980 = _t1485
                    if deconstruct_result980 is not None:
                        assert deconstruct_result980 is not None
                        unwrapped981 = deconstruct_result980
                        self.write(self.format_string_value(unwrapped981))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int32_value"):
                            _t1486 = _dollar_dollar.int32_value
                        else:
                            _t1486 = None
                        deconstruct_result978 = _t1486
                        if deconstruct_result978 is not None:
                            assert deconstruct_result978 is not None
                            unwrapped979 = deconstruct_result978
                            self.write((str(unwrapped979) + 'i32'))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("int_value"):
                                _t1487 = _dollar_dollar.int_value
                            else:
                                _t1487 = None
                            deconstruct_result976 = _t1487
                            if deconstruct_result976 is not None:
                                assert deconstruct_result976 is not None
                                unwrapped977 = deconstruct_result976
                                self.write(str(unwrapped977))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("float32_value"):
                                    _t1488 = _dollar_dollar.float32_value
                                else:
                                    _t1488 = None
                                deconstruct_result974 = _t1488
                                if deconstruct_result974 is not None:
                                    assert deconstruct_result974 is not None
                                    unwrapped975 = deconstruct_result974
                                    self.write(self.format_float32_literal(unwrapped975))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("float_value"):
                                        _t1489 = _dollar_dollar.float_value
                                    else:
                                        _t1489 = None
                                    deconstruct_result972 = _t1489
                                    if deconstruct_result972 is not None:
                                        assert deconstruct_result972 is not None
                                        unwrapped973 = deconstruct_result972
                                        self.write(str(unwrapped973))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("uint32_value"):
                                            _t1490 = _dollar_dollar.uint32_value
                                        else:
                                            _t1490 = None
                                        deconstruct_result970 = _t1490
                                        if deconstruct_result970 is not None:
                                            assert deconstruct_result970 is not None
                                            unwrapped971 = deconstruct_result970
                                            self.write((str(unwrapped971) + 'u32'))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("uint128_value"):
                                                _t1491 = _dollar_dollar.uint128_value
                                            else:
                                                _t1491 = None
                                            deconstruct_result968 = _t1491
                                            if deconstruct_result968 is not None:
                                                assert deconstruct_result968 is not None
                                                unwrapped969 = deconstruct_result968
                                                self.write(self.format_uint128(unwrapped969))
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int128_value"):
                                                    _t1492 = _dollar_dollar.int128_value
                                                else:
                                                    _t1492 = None
                                                deconstruct_result966 = _t1492
                                                if deconstruct_result966 is not None:
                                                    assert deconstruct_result966 is not None
                                                    unwrapped967 = deconstruct_result966
                                                    self.write(self.format_int128(unwrapped967))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("decimal_value"):
                                                        _t1493 = _dollar_dollar.decimal_value
                                                    else:
                                                        _t1493 = None
                                                    deconstruct_result964 = _t1493
                                                    if deconstruct_result964 is not None:
                                                        assert deconstruct_result964 is not None
                                                        unwrapped965 = deconstruct_result964
                                                        self.write(self.format_decimal(unwrapped965))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("boolean_value"):
                                                            _t1494 = _dollar_dollar.boolean_value
                                                        else:
                                                            _t1494 = None
                                                        deconstruct_result962 = _t1494
                                                        if deconstruct_result962 is not None:
                                                            assert deconstruct_result962 is not None
                                                            unwrapped963 = deconstruct_result962
                                                            self.pretty_boolean_value(unwrapped963)
                                                        else:
                                                            fields961 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat992 = self._try_flat(msg, self.pretty_date)
        if flat992 is not None:
            assert flat992 is not None
            self.write(flat992)
            return None
        else:
            _dollar_dollar = msg
            fields987 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields987 is not None
            unwrapped_fields988 = fields987
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field989 = unwrapped_fields988[0]
            self.write(str(field989))
            self.newline()
            field990 = unwrapped_fields988[1]
            self.write(str(field990))
            self.newline()
            field991 = unwrapped_fields988[2]
            self.write(str(field991))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat1003 = self._try_flat(msg, self.pretty_datetime)
        if flat1003 is not None:
            assert flat1003 is not None
            self.write(flat1003)
            return None
        else:
            _dollar_dollar = msg
            fields993 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields993 is not None
            unwrapped_fields994 = fields993
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field995 = unwrapped_fields994[0]
            self.write(str(field995))
            self.newline()
            field996 = unwrapped_fields994[1]
            self.write(str(field996))
            self.newline()
            field997 = unwrapped_fields994[2]
            self.write(str(field997))
            self.newline()
            field998 = unwrapped_fields994[3]
            self.write(str(field998))
            self.newline()
            field999 = unwrapped_fields994[4]
            self.write(str(field999))
            self.newline()
            field1000 = unwrapped_fields994[5]
            self.write(str(field1000))
            field1001 = unwrapped_fields994[6]
            if field1001 is not None:
                self.newline()
                assert field1001 is not None
                opt_val1002 = field1001
                self.write(str(opt_val1002))
            self.dedent()
            self.write(")")

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat1008 = self._try_flat(msg, self.pretty_conjunction)
        if flat1008 is not None:
            assert flat1008 is not None
            self.write(flat1008)
            return None
        else:
            _dollar_dollar = msg
            fields1004 = _dollar_dollar.args
            assert fields1004 is not None
            unwrapped_fields1005 = fields1004
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields1005) == 0:
                self.newline()
                for i1007, elem1006 in enumerate(unwrapped_fields1005):
                    if (i1007 > 0):
                        self.newline()
                    self.pretty_formula(elem1006)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat1013 = self._try_flat(msg, self.pretty_disjunction)
        if flat1013 is not None:
            assert flat1013 is not None
            self.write(flat1013)
            return None
        else:
            _dollar_dollar = msg
            fields1009 = _dollar_dollar.args
            assert fields1009 is not None
            unwrapped_fields1010 = fields1009
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields1010) == 0:
                self.newline()
                for i1012, elem1011 in enumerate(unwrapped_fields1010):
                    if (i1012 > 0):
                        self.newline()
                    self.pretty_formula(elem1011)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat1016 = self._try_flat(msg, self.pretty_not)
        if flat1016 is not None:
            assert flat1016 is not None
            self.write(flat1016)
            return None
        else:
            _dollar_dollar = msg
            fields1014 = _dollar_dollar.arg
            assert fields1014 is not None
            unwrapped_fields1015 = fields1014
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields1015)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat1022 = self._try_flat(msg, self.pretty_ffi)
        if flat1022 is not None:
            assert flat1022 is not None
            self.write(flat1022)
            return None
        else:
            _dollar_dollar = msg
            fields1017 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields1017 is not None
            unwrapped_fields1018 = fields1017
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field1019 = unwrapped_fields1018[0]
            self.pretty_name(field1019)
            self.newline()
            field1020 = unwrapped_fields1018[1]
            self.pretty_ffi_args(field1020)
            self.newline()
            field1021 = unwrapped_fields1018[2]
            self.pretty_terms(field1021)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat1024 = self._try_flat(msg, self.pretty_name)
        if flat1024 is not None:
            assert flat1024 is not None
            self.write(flat1024)
            return None
        else:
            fields1023 = msg
            self.write(":")
            self.write(fields1023)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat1028 = self._try_flat(msg, self.pretty_ffi_args)
        if flat1028 is not None:
            assert flat1028 is not None
            self.write(flat1028)
            return None
        else:
            fields1025 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields1025) == 0:
                self.newline()
                for i1027, elem1026 in enumerate(fields1025):
                    if (i1027 > 0):
                        self.newline()
                    self.pretty_abstraction(elem1026)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat1035 = self._try_flat(msg, self.pretty_atom)
        if flat1035 is not None:
            assert flat1035 is not None
            self.write(flat1035)
            return None
        else:
            _dollar_dollar = msg
            fields1029 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1029 is not None
            unwrapped_fields1030 = fields1029
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field1031 = unwrapped_fields1030[0]
            self.pretty_relation_id(field1031)
            field1032 = unwrapped_fields1030[1]
            if not len(field1032) == 0:
                self.newline()
                for i1034, elem1033 in enumerate(field1032):
                    if (i1034 > 0):
                        self.newline()
                    self.pretty_term(elem1033)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat1042 = self._try_flat(msg, self.pretty_pragma)
        if flat1042 is not None:
            assert flat1042 is not None
            self.write(flat1042)
            return None
        else:
            _dollar_dollar = msg
            fields1036 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1036 is not None
            unwrapped_fields1037 = fields1036
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field1038 = unwrapped_fields1037[0]
            self.pretty_name(field1038)
            field1039 = unwrapped_fields1037[1]
            if not len(field1039) == 0:
                self.newline()
                for i1041, elem1040 in enumerate(field1039):
                    if (i1041 > 0):
                        self.newline()
                    self.pretty_term(elem1040)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat1058 = self._try_flat(msg, self.pretty_primitive)
        if flat1058 is not None:
            assert flat1058 is not None
            self.write(flat1058)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1495 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1495 = None
            guard_result1057 = _t1495
            if guard_result1057 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1496 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1496 = None
                guard_result1056 = _t1496
                if guard_result1056 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1497 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1497 = None
                    guard_result1055 = _t1497
                    if guard_result1055 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1498 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1498 = None
                        guard_result1054 = _t1498
                        if guard_result1054 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1499 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1499 = None
                            guard_result1053 = _t1499
                            if guard_result1053 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1500 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1500 = None
                                guard_result1052 = _t1500
                                if guard_result1052 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1501 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1501 = None
                                    guard_result1051 = _t1501
                                    if guard_result1051 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1502 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1502 = None
                                        guard_result1050 = _t1502
                                        if guard_result1050 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1503 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1503 = None
                                            guard_result1049 = _t1503
                                            if guard_result1049 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields1043 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields1043 is not None
                                                unwrapped_fields1044 = fields1043
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field1045 = unwrapped_fields1044[0]
                                                self.pretty_name(field1045)
                                                field1046 = unwrapped_fields1044[1]
                                                if not len(field1046) == 0:
                                                    self.newline()
                                                    for i1048, elem1047 in enumerate(field1046):
                                                        if (i1048 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem1047)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat1063 = self._try_flat(msg, self.pretty_eq)
        if flat1063 is not None:
            assert flat1063 is not None
            self.write(flat1063)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1504 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1504 = None
            fields1059 = _t1504
            assert fields1059 is not None
            unwrapped_fields1060 = fields1059
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field1061 = unwrapped_fields1060[0]
            self.pretty_term(field1061)
            self.newline()
            field1062 = unwrapped_fields1060[1]
            self.pretty_term(field1062)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat1068 = self._try_flat(msg, self.pretty_lt)
        if flat1068 is not None:
            assert flat1068 is not None
            self.write(flat1068)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1505 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1505 = None
            fields1064 = _t1505
            assert fields1064 is not None
            unwrapped_fields1065 = fields1064
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field1066 = unwrapped_fields1065[0]
            self.pretty_term(field1066)
            self.newline()
            field1067 = unwrapped_fields1065[1]
            self.pretty_term(field1067)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat1073 = self._try_flat(msg, self.pretty_lt_eq)
        if flat1073 is not None:
            assert flat1073 is not None
            self.write(flat1073)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1506 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1506 = None
            fields1069 = _t1506
            assert fields1069 is not None
            unwrapped_fields1070 = fields1069
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field1071 = unwrapped_fields1070[0]
            self.pretty_term(field1071)
            self.newline()
            field1072 = unwrapped_fields1070[1]
            self.pretty_term(field1072)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat1078 = self._try_flat(msg, self.pretty_gt)
        if flat1078 is not None:
            assert flat1078 is not None
            self.write(flat1078)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1507 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1507 = None
            fields1074 = _t1507
            assert fields1074 is not None
            unwrapped_fields1075 = fields1074
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field1076 = unwrapped_fields1075[0]
            self.pretty_term(field1076)
            self.newline()
            field1077 = unwrapped_fields1075[1]
            self.pretty_term(field1077)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1083 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1083 is not None:
            assert flat1083 is not None
            self.write(flat1083)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1508 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1508 = None
            fields1079 = _t1508
            assert fields1079 is not None
            unwrapped_fields1080 = fields1079
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field1081 = unwrapped_fields1080[0]
            self.pretty_term(field1081)
            self.newline()
            field1082 = unwrapped_fields1080[1]
            self.pretty_term(field1082)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1089 = self._try_flat(msg, self.pretty_add)
        if flat1089 is not None:
            assert flat1089 is not None
            self.write(flat1089)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1509 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1509 = None
            fields1084 = _t1509
            assert fields1084 is not None
            unwrapped_fields1085 = fields1084
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1086 = unwrapped_fields1085[0]
            self.pretty_term(field1086)
            self.newline()
            field1087 = unwrapped_fields1085[1]
            self.pretty_term(field1087)
            self.newline()
            field1088 = unwrapped_fields1085[2]
            self.pretty_term(field1088)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1095 = self._try_flat(msg, self.pretty_minus)
        if flat1095 is not None:
            assert flat1095 is not None
            self.write(flat1095)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1510 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1510 = None
            fields1090 = _t1510
            assert fields1090 is not None
            unwrapped_fields1091 = fields1090
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1092 = unwrapped_fields1091[0]
            self.pretty_term(field1092)
            self.newline()
            field1093 = unwrapped_fields1091[1]
            self.pretty_term(field1093)
            self.newline()
            field1094 = unwrapped_fields1091[2]
            self.pretty_term(field1094)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1101 = self._try_flat(msg, self.pretty_multiply)
        if flat1101 is not None:
            assert flat1101 is not None
            self.write(flat1101)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1511 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1511 = None
            fields1096 = _t1511
            assert fields1096 is not None
            unwrapped_fields1097 = fields1096
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1098 = unwrapped_fields1097[0]
            self.pretty_term(field1098)
            self.newline()
            field1099 = unwrapped_fields1097[1]
            self.pretty_term(field1099)
            self.newline()
            field1100 = unwrapped_fields1097[2]
            self.pretty_term(field1100)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1107 = self._try_flat(msg, self.pretty_divide)
        if flat1107 is not None:
            assert flat1107 is not None
            self.write(flat1107)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1512 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1512 = None
            fields1102 = _t1512
            assert fields1102 is not None
            unwrapped_fields1103 = fields1102
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1104 = unwrapped_fields1103[0]
            self.pretty_term(field1104)
            self.newline()
            field1105 = unwrapped_fields1103[1]
            self.pretty_term(field1105)
            self.newline()
            field1106 = unwrapped_fields1103[2]
            self.pretty_term(field1106)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1112 = self._try_flat(msg, self.pretty_rel_term)
        if flat1112 is not None:
            assert flat1112 is not None
            self.write(flat1112)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1513 = _dollar_dollar.specialized_value
            else:
                _t1513 = None
            deconstruct_result1110 = _t1513
            if deconstruct_result1110 is not None:
                assert deconstruct_result1110 is not None
                unwrapped1111 = deconstruct_result1110
                self.pretty_specialized_value(unwrapped1111)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1514 = _dollar_dollar.term
                else:
                    _t1514 = None
                deconstruct_result1108 = _t1514
                if deconstruct_result1108 is not None:
                    assert deconstruct_result1108 is not None
                    unwrapped1109 = deconstruct_result1108
                    self.pretty_term(unwrapped1109)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1114 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1114 is not None:
            assert flat1114 is not None
            self.write(flat1114)
            return None
        else:
            fields1113 = msg
            self.write("#")
            self.pretty_raw_value(fields1113)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1121 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1121 is not None:
            assert flat1121 is not None
            self.write(flat1121)
            return None
        else:
            _dollar_dollar = msg
            fields1115 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1115 is not None
            unwrapped_fields1116 = fields1115
            self.write("(relatom")
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

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1126 = self._try_flat(msg, self.pretty_cast)
        if flat1126 is not None:
            assert flat1126 is not None
            self.write(flat1126)
            return None
        else:
            _dollar_dollar = msg
            fields1122 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1122 is not None
            unwrapped_fields1123 = fields1122
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1124 = unwrapped_fields1123[0]
            self.pretty_term(field1124)
            self.newline()
            field1125 = unwrapped_fields1123[1]
            self.pretty_term(field1125)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1130 = self._try_flat(msg, self.pretty_attrs)
        if flat1130 is not None:
            assert flat1130 is not None
            self.write(flat1130)
            return None
        else:
            fields1127 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1127) == 0:
                self.newline()
                for i1129, elem1128 in enumerate(fields1127):
                    if (i1129 > 0):
                        self.newline()
                    self.pretty_attribute(elem1128)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1137 = self._try_flat(msg, self.pretty_attribute)
        if flat1137 is not None:
            assert flat1137 is not None
            self.write(flat1137)
            return None
        else:
            _dollar_dollar = msg
            fields1131 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1131 is not None
            unwrapped_fields1132 = fields1131
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1133 = unwrapped_fields1132[0]
            self.pretty_name(field1133)
            field1134 = unwrapped_fields1132[1]
            if not len(field1134) == 0:
                self.newline()
                for i1136, elem1135 in enumerate(field1134):
                    if (i1136 > 0):
                        self.newline()
                    self.pretty_raw_value(elem1135)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1144 = self._try_flat(msg, self.pretty_algorithm)
        if flat1144 is not None:
            assert flat1144 is not None
            self.write(flat1144)
            return None
        else:
            _dollar_dollar = msg
            fields1138 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            assert fields1138 is not None
            unwrapped_fields1139 = fields1138
            self.write("(algorithm")
            self.indent_sexp()
            field1140 = unwrapped_fields1139[0]
            if not len(field1140) == 0:
                self.newline()
                for i1142, elem1141 in enumerate(field1140):
                    if (i1142 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1141)
            self.newline()
            field1143 = unwrapped_fields1139[1]
            self.pretty_script(field1143)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1149 = self._try_flat(msg, self.pretty_script)
        if flat1149 is not None:
            assert flat1149 is not None
            self.write(flat1149)
            return None
        else:
            _dollar_dollar = msg
            fields1145 = _dollar_dollar.constructs
            assert fields1145 is not None
            unwrapped_fields1146 = fields1145
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1146) == 0:
                self.newline()
                for i1148, elem1147 in enumerate(unwrapped_fields1146):
                    if (i1148 > 0):
                        self.newline()
                    self.pretty_construct(elem1147)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1154 = self._try_flat(msg, self.pretty_construct)
        if flat1154 is not None:
            assert flat1154 is not None
            self.write(flat1154)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1515 = _dollar_dollar.loop
            else:
                _t1515 = None
            deconstruct_result1152 = _t1515
            if deconstruct_result1152 is not None:
                assert deconstruct_result1152 is not None
                unwrapped1153 = deconstruct_result1152
                self.pretty_loop(unwrapped1153)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1516 = _dollar_dollar.instruction
                else:
                    _t1516 = None
                deconstruct_result1150 = _t1516
                if deconstruct_result1150 is not None:
                    assert deconstruct_result1150 is not None
                    unwrapped1151 = deconstruct_result1150
                    self.pretty_instruction(unwrapped1151)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1159 = self._try_flat(msg, self.pretty_loop)
        if flat1159 is not None:
            assert flat1159 is not None
            self.write(flat1159)
            return None
        else:
            _dollar_dollar = msg
            fields1155 = (_dollar_dollar.init, _dollar_dollar.body,)
            assert fields1155 is not None
            unwrapped_fields1156 = fields1155
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1157 = unwrapped_fields1156[0]
            self.pretty_init(field1157)
            self.newline()
            field1158 = unwrapped_fields1156[1]
            self.pretty_script(field1158)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1163 = self._try_flat(msg, self.pretty_init)
        if flat1163 is not None:
            assert flat1163 is not None
            self.write(flat1163)
            return None
        else:
            fields1160 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1160) == 0:
                self.newline()
                for i1162, elem1161 in enumerate(fields1160):
                    if (i1162 > 0):
                        self.newline()
                    self.pretty_instruction(elem1161)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1174 = self._try_flat(msg, self.pretty_instruction)
        if flat1174 is not None:
            assert flat1174 is not None
            self.write(flat1174)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1517 = _dollar_dollar.assign
            else:
                _t1517 = None
            deconstruct_result1172 = _t1517
            if deconstruct_result1172 is not None:
                assert deconstruct_result1172 is not None
                unwrapped1173 = deconstruct_result1172
                self.pretty_assign(unwrapped1173)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1518 = _dollar_dollar.upsert
                else:
                    _t1518 = None
                deconstruct_result1170 = _t1518
                if deconstruct_result1170 is not None:
                    assert deconstruct_result1170 is not None
                    unwrapped1171 = deconstruct_result1170
                    self.pretty_upsert(unwrapped1171)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1519 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1519 = None
                    deconstruct_result1168 = _t1519
                    if deconstruct_result1168 is not None:
                        assert deconstruct_result1168 is not None
                        unwrapped1169 = deconstruct_result1168
                        self.pretty_break(unwrapped1169)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1520 = _dollar_dollar.monoid_def
                        else:
                            _t1520 = None
                        deconstruct_result1166 = _t1520
                        if deconstruct_result1166 is not None:
                            assert deconstruct_result1166 is not None
                            unwrapped1167 = deconstruct_result1166
                            self.pretty_monoid_def(unwrapped1167)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1521 = _dollar_dollar.monus_def
                            else:
                                _t1521 = None
                            deconstruct_result1164 = _t1521
                            if deconstruct_result1164 is not None:
                                assert deconstruct_result1164 is not None
                                unwrapped1165 = deconstruct_result1164
                                self.pretty_monus_def(unwrapped1165)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1181 = self._try_flat(msg, self.pretty_assign)
        if flat1181 is not None:
            assert flat1181 is not None
            self.write(flat1181)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1522 = _dollar_dollar.attrs
            else:
                _t1522 = None
            fields1175 = (_dollar_dollar.name, _dollar_dollar.body, _t1522,)
            assert fields1175 is not None
            unwrapped_fields1176 = fields1175
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1177 = unwrapped_fields1176[0]
            self.pretty_relation_id(field1177)
            self.newline()
            field1178 = unwrapped_fields1176[1]
            self.pretty_abstraction(field1178)
            field1179 = unwrapped_fields1176[2]
            if field1179 is not None:
                self.newline()
                assert field1179 is not None
                opt_val1180 = field1179
                self.pretty_attrs(opt_val1180)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1188 = self._try_flat(msg, self.pretty_upsert)
        if flat1188 is not None:
            assert flat1188 is not None
            self.write(flat1188)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1523 = _dollar_dollar.attrs
            else:
                _t1523 = None
            fields1182 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1523,)
            assert fields1182 is not None
            unwrapped_fields1183 = fields1182
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1184 = unwrapped_fields1183[0]
            self.pretty_relation_id(field1184)
            self.newline()
            field1185 = unwrapped_fields1183[1]
            self.pretty_abstraction_with_arity(field1185)
            field1186 = unwrapped_fields1183[2]
            if field1186 is not None:
                self.newline()
                assert field1186 is not None
                opt_val1187 = field1186
                self.pretty_attrs(opt_val1187)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1193 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1193 is not None:
            assert flat1193 is not None
            self.write(flat1193)
            return None
        else:
            _dollar_dollar = msg
            _t1524 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1189 = (_t1524, _dollar_dollar[0].value,)
            assert fields1189 is not None
            unwrapped_fields1190 = fields1189
            self.write("(")
            self.indent()
            field1191 = unwrapped_fields1190[0]
            self.pretty_bindings(field1191)
            self.newline()
            field1192 = unwrapped_fields1190[1]
            self.pretty_formula(field1192)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1200 = self._try_flat(msg, self.pretty_break)
        if flat1200 is not None:
            assert flat1200 is not None
            self.write(flat1200)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1525 = _dollar_dollar.attrs
            else:
                _t1525 = None
            fields1194 = (_dollar_dollar.name, _dollar_dollar.body, _t1525,)
            assert fields1194 is not None
            unwrapped_fields1195 = fields1194
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1196 = unwrapped_fields1195[0]
            self.pretty_relation_id(field1196)
            self.newline()
            field1197 = unwrapped_fields1195[1]
            self.pretty_abstraction(field1197)
            field1198 = unwrapped_fields1195[2]
            if field1198 is not None:
                self.newline()
                assert field1198 is not None
                opt_val1199 = field1198
                self.pretty_attrs(opt_val1199)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1208 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1208 is not None:
            assert flat1208 is not None
            self.write(flat1208)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1526 = _dollar_dollar.attrs
            else:
                _t1526 = None
            fields1201 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1526,)
            assert fields1201 is not None
            unwrapped_fields1202 = fields1201
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1203 = unwrapped_fields1202[0]
            self.pretty_monoid(field1203)
            self.newline()
            field1204 = unwrapped_fields1202[1]
            self.pretty_relation_id(field1204)
            self.newline()
            field1205 = unwrapped_fields1202[2]
            self.pretty_abstraction_with_arity(field1205)
            field1206 = unwrapped_fields1202[3]
            if field1206 is not None:
                self.newline()
                assert field1206 is not None
                opt_val1207 = field1206
                self.pretty_attrs(opt_val1207)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1217 = self._try_flat(msg, self.pretty_monoid)
        if flat1217 is not None:
            assert flat1217 is not None
            self.write(flat1217)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1527 = _dollar_dollar.or_monoid
            else:
                _t1527 = None
            deconstruct_result1215 = _t1527
            if deconstruct_result1215 is not None:
                assert deconstruct_result1215 is not None
                unwrapped1216 = deconstruct_result1215
                self.pretty_or_monoid(unwrapped1216)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1528 = _dollar_dollar.min_monoid
                else:
                    _t1528 = None
                deconstruct_result1213 = _t1528
                if deconstruct_result1213 is not None:
                    assert deconstruct_result1213 is not None
                    unwrapped1214 = deconstruct_result1213
                    self.pretty_min_monoid(unwrapped1214)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1529 = _dollar_dollar.max_monoid
                    else:
                        _t1529 = None
                    deconstruct_result1211 = _t1529
                    if deconstruct_result1211 is not None:
                        assert deconstruct_result1211 is not None
                        unwrapped1212 = deconstruct_result1211
                        self.pretty_max_monoid(unwrapped1212)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1530 = _dollar_dollar.sum_monoid
                        else:
                            _t1530 = None
                        deconstruct_result1209 = _t1530
                        if deconstruct_result1209 is not None:
                            assert deconstruct_result1209 is not None
                            unwrapped1210 = deconstruct_result1209
                            self.pretty_sum_monoid(unwrapped1210)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1218 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1221 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1221 is not None:
            assert flat1221 is not None
            self.write(flat1221)
            return None
        else:
            _dollar_dollar = msg
            fields1219 = _dollar_dollar.type
            assert fields1219 is not None
            unwrapped_fields1220 = fields1219
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1220)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1224 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1224 is not None:
            assert flat1224 is not None
            self.write(flat1224)
            return None
        else:
            _dollar_dollar = msg
            fields1222 = _dollar_dollar.type
            assert fields1222 is not None
            unwrapped_fields1223 = fields1222
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1223)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1227 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1227 is not None:
            assert flat1227 is not None
            self.write(flat1227)
            return None
        else:
            _dollar_dollar = msg
            fields1225 = _dollar_dollar.type
            assert fields1225 is not None
            unwrapped_fields1226 = fields1225
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1226)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1235 = self._try_flat(msg, self.pretty_monus_def)
        if flat1235 is not None:
            assert flat1235 is not None
            self.write(flat1235)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1531 = _dollar_dollar.attrs
            else:
                _t1531 = None
            fields1228 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1531,)
            assert fields1228 is not None
            unwrapped_fields1229 = fields1228
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1230 = unwrapped_fields1229[0]
            self.pretty_monoid(field1230)
            self.newline()
            field1231 = unwrapped_fields1229[1]
            self.pretty_relation_id(field1231)
            self.newline()
            field1232 = unwrapped_fields1229[2]
            self.pretty_abstraction_with_arity(field1232)
            field1233 = unwrapped_fields1229[3]
            if field1233 is not None:
                self.newline()
                assert field1233 is not None
                opt_val1234 = field1233
                self.pretty_attrs(opt_val1234)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1242 = self._try_flat(msg, self.pretty_constraint)
        if flat1242 is not None:
            assert flat1242 is not None
            self.write(flat1242)
            return None
        else:
            _dollar_dollar = msg
            fields1236 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1236 is not None
            unwrapped_fields1237 = fields1236
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1238 = unwrapped_fields1237[0]
            self.pretty_relation_id(field1238)
            self.newline()
            field1239 = unwrapped_fields1237[1]
            self.pretty_abstraction(field1239)
            self.newline()
            field1240 = unwrapped_fields1237[2]
            self.pretty_functional_dependency_keys(field1240)
            self.newline()
            field1241 = unwrapped_fields1237[3]
            self.pretty_functional_dependency_values(field1241)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1246 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1246 is not None:
            assert flat1246 is not None
            self.write(flat1246)
            return None
        else:
            fields1243 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1243) == 0:
                self.newline()
                for i1245, elem1244 in enumerate(fields1243):
                    if (i1245 > 0):
                        self.newline()
                    self.pretty_var(elem1244)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1250 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1250 is not None:
            assert flat1250 is not None
            self.write(flat1250)
            return None
        else:
            fields1247 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1247) == 0:
                self.newline()
                for i1249, elem1248 in enumerate(fields1247):
                    if (i1249 > 0):
                        self.newline()
                    self.pretty_var(elem1248)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1257 = self._try_flat(msg, self.pretty_data)
        if flat1257 is not None:
            assert flat1257 is not None
            self.write(flat1257)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1532 = _dollar_dollar.edb
            else:
                _t1532 = None
            deconstruct_result1255 = _t1532
            if deconstruct_result1255 is not None:
                assert deconstruct_result1255 is not None
                unwrapped1256 = deconstruct_result1255
                self.pretty_edb(unwrapped1256)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1533 = _dollar_dollar.betree_relation
                else:
                    _t1533 = None
                deconstruct_result1253 = _t1533
                if deconstruct_result1253 is not None:
                    assert deconstruct_result1253 is not None
                    unwrapped1254 = deconstruct_result1253
                    self.pretty_betree_relation(unwrapped1254)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1534 = _dollar_dollar.csv_data
                    else:
                        _t1534 = None
                    deconstruct_result1251 = _t1534
                    if deconstruct_result1251 is not None:
                        assert deconstruct_result1251 is not None
                        unwrapped1252 = deconstruct_result1251
                        self.pretty_csv_data(unwrapped1252)
                    else:
                        raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1263 = self._try_flat(msg, self.pretty_edb)
        if flat1263 is not None:
            assert flat1263 is not None
            self.write(flat1263)
            return None
        else:
            _dollar_dollar = msg
            fields1258 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1258 is not None
            unwrapped_fields1259 = fields1258
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1260 = unwrapped_fields1259[0]
            self.pretty_relation_id(field1260)
            self.newline()
            field1261 = unwrapped_fields1259[1]
            self.pretty_edb_path(field1261)
            self.newline()
            field1262 = unwrapped_fields1259[2]
            self.pretty_edb_types(field1262)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1267 = self._try_flat(msg, self.pretty_edb_path)
        if flat1267 is not None:
            assert flat1267 is not None
            self.write(flat1267)
            return None
        else:
            fields1264 = msg
            self.write("[")
            self.indent()
            for i1266, elem1265 in enumerate(fields1264):
                if (i1266 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1265))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1271 = self._try_flat(msg, self.pretty_edb_types)
        if flat1271 is not None:
            assert flat1271 is not None
            self.write(flat1271)
            return None
        else:
            fields1268 = msg
            self.write("[")
            self.indent()
            for i1270, elem1269 in enumerate(fields1268):
                if (i1270 > 0):
                    self.newline()
                self.pretty_type(elem1269)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1276 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1276 is not None:
            assert flat1276 is not None
            self.write(flat1276)
            return None
        else:
            _dollar_dollar = msg
            fields1272 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1272 is not None
            unwrapped_fields1273 = fields1272
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1274 = unwrapped_fields1273[0]
            self.pretty_relation_id(field1274)
            self.newline()
            field1275 = unwrapped_fields1273[1]
            self.pretty_betree_info(field1275)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1282 = self._try_flat(msg, self.pretty_betree_info)
        if flat1282 is not None:
            assert flat1282 is not None
            self.write(flat1282)
            return None
        else:
            _dollar_dollar = msg
            _t1535 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1277 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1535,)
            assert fields1277 is not None
            unwrapped_fields1278 = fields1277
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1279 = unwrapped_fields1278[0]
            self.pretty_betree_info_key_types(field1279)
            self.newline()
            field1280 = unwrapped_fields1278[1]
            self.pretty_betree_info_value_types(field1280)
            self.newline()
            field1281 = unwrapped_fields1278[2]
            self.pretty_config_dict(field1281)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1286 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1286 is not None:
            assert flat1286 is not None
            self.write(flat1286)
            return None
        else:
            fields1283 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1283) == 0:
                self.newline()
                for i1285, elem1284 in enumerate(fields1283):
                    if (i1285 > 0):
                        self.newline()
                    self.pretty_type(elem1284)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1290 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1290 is not None:
            assert flat1290 is not None
            self.write(flat1290)
            return None
        else:
            fields1287 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1287) == 0:
                self.newline()
                for i1289, elem1288 in enumerate(fields1287):
                    if (i1289 > 0):
                        self.newline()
                    self.pretty_type(elem1288)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1297 = self._try_flat(msg, self.pretty_csv_data)
        if flat1297 is not None:
            assert flat1297 is not None
            self.write(flat1297)
            return None
        else:
            _dollar_dollar = msg
            fields1291 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1291 is not None
            unwrapped_fields1292 = fields1291
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1293 = unwrapped_fields1292[0]
            self.pretty_csvlocator(field1293)
            self.newline()
            field1294 = unwrapped_fields1292[1]
            self.pretty_csv_config(field1294)
            self.newline()
            field1295 = unwrapped_fields1292[2]
            self.pretty_gnf_columns(field1295)
            self.newline()
            field1296 = unwrapped_fields1292[3]
            self.pretty_csv_asof(field1296)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1304 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1304 is not None:
            assert flat1304 is not None
            self.write(flat1304)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1536 = _dollar_dollar.paths
            else:
                _t1536 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1537 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1537 = None
            fields1298 = (_t1536, _t1537,)
            assert fields1298 is not None
            unwrapped_fields1299 = fields1298
            self.write("(csv_locator")
            self.indent_sexp()
            field1300 = unwrapped_fields1299[0]
            if field1300 is not None:
                self.newline()
                assert field1300 is not None
                opt_val1301 = field1300
                self.pretty_csv_locator_paths(opt_val1301)
            field1302 = unwrapped_fields1299[1]
            if field1302 is not None:
                self.newline()
                assert field1302 is not None
                opt_val1303 = field1302
                self.pretty_csv_locator_inline_data(opt_val1303)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1308 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1308 is not None:
            assert flat1308 is not None
            self.write(flat1308)
            return None
        else:
            fields1305 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1305) == 0:
                self.newline()
                for i1307, elem1306 in enumerate(fields1305):
                    if (i1307 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1306))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1310 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1310 is not None:
            assert flat1310 is not None
            self.write(flat1310)
            return None
        else:
            fields1309 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1309))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1313 = self._try_flat(msg, self.pretty_csv_config)
        if flat1313 is not None:
            assert flat1313 is not None
            self.write(flat1313)
            return None
        else:
            _dollar_dollar = msg
            _t1538 = self.deconstruct_csv_config(_dollar_dollar)
            fields1311 = _t1538
            assert fields1311 is not None
            unwrapped_fields1312 = fields1311
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1312)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1317 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1317 is not None:
            assert flat1317 is not None
            self.write(flat1317)
            return None
        else:
            fields1314 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1314) == 0:
                self.newline()
                for i1316, elem1315 in enumerate(fields1314):
                    if (i1316 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1315)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1326 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1326 is not None:
            assert flat1326 is not None
            self.write(flat1326)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1539 = _dollar_dollar.target_id
            else:
                _t1539 = None
            fields1318 = (_dollar_dollar.column_path, _t1539, _dollar_dollar.types,)
            assert fields1318 is not None
            unwrapped_fields1319 = fields1318
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1320 = unwrapped_fields1319[0]
            self.pretty_gnf_column_path(field1320)
            field1321 = unwrapped_fields1319[1]
            if field1321 is not None:
                self.newline()
                assert field1321 is not None
                opt_val1322 = field1321
                self.pretty_relation_id(opt_val1322)
            self.newline()
            self.write("[")
            field1323 = unwrapped_fields1319[2]
            for i1325, elem1324 in enumerate(field1323):
                if (i1325 > 0):
                    self.newline()
                self.pretty_type(elem1324)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1333 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1333 is not None:
            assert flat1333 is not None
            self.write(flat1333)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1540 = _dollar_dollar[0]
            else:
                _t1540 = None
            deconstruct_result1331 = _t1540
            if deconstruct_result1331 is not None:
                assert deconstruct_result1331 is not None
                unwrapped1332 = deconstruct_result1331
                self.write(self.format_string_value(unwrapped1332))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1541 = _dollar_dollar
                else:
                    _t1541 = None
                deconstruct_result1327 = _t1541
                if deconstruct_result1327 is not None:
                    assert deconstruct_result1327 is not None
                    unwrapped1328 = deconstruct_result1327
                    self.write("[")
                    self.indent()
                    for i1330, elem1329 in enumerate(unwrapped1328):
                        if (i1330 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1329))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1335 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1335 is not None:
            assert flat1335 is not None
            self.write(flat1335)
            return None
        else:
            fields1334 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1334))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1338 = self._try_flat(msg, self.pretty_undefine)
        if flat1338 is not None:
            assert flat1338 is not None
            self.write(flat1338)
            return None
        else:
            _dollar_dollar = msg
            fields1336 = _dollar_dollar.fragment_id
            assert fields1336 is not None
            unwrapped_fields1337 = fields1336
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1337)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1343 = self._try_flat(msg, self.pretty_context)
        if flat1343 is not None:
            assert flat1343 is not None
            self.write(flat1343)
            return None
        else:
            _dollar_dollar = msg
            fields1339 = _dollar_dollar.relations
            assert fields1339 is not None
            unwrapped_fields1340 = fields1339
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1340) == 0:
                self.newline()
                for i1342, elem1341 in enumerate(unwrapped_fields1340):
                    if (i1342 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1341)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1348 = self._try_flat(msg, self.pretty_snapshot)
        if flat1348 is not None:
            assert flat1348 is not None
            self.write(flat1348)
            return None
        else:
            _dollar_dollar = msg
            fields1344 = _dollar_dollar.mappings
            assert fields1344 is not None
            unwrapped_fields1345 = fields1344
            self.write("(snapshot")
            self.indent_sexp()
            if not len(unwrapped_fields1345) == 0:
                self.newline()
                for i1347, elem1346 in enumerate(unwrapped_fields1345):
                    if (i1347 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1346)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1353 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1353 is not None:
            assert flat1353 is not None
            self.write(flat1353)
            return None
        else:
            _dollar_dollar = msg
            fields1349 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1349 is not None
            unwrapped_fields1350 = fields1349
            field1351 = unwrapped_fields1350[0]
            self.pretty_edb_path(field1351)
            self.write(" ")
            field1352 = unwrapped_fields1350[1]
            self.pretty_relation_id(field1352)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1357 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1357 is not None:
            assert flat1357 is not None
            self.write(flat1357)
            return None
        else:
            fields1354 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1354) == 0:
                self.newline()
                for i1356, elem1355 in enumerate(fields1354):
                    if (i1356 > 0):
                        self.newline()
                    self.pretty_read(elem1355)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1368 = self._try_flat(msg, self.pretty_read)
        if flat1368 is not None:
            assert flat1368 is not None
            self.write(flat1368)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1542 = _dollar_dollar.demand
            else:
                _t1542 = None
            deconstruct_result1366 = _t1542
            if deconstruct_result1366 is not None:
                assert deconstruct_result1366 is not None
                unwrapped1367 = deconstruct_result1366
                self.pretty_demand(unwrapped1367)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1543 = _dollar_dollar.output
                else:
                    _t1543 = None
                deconstruct_result1364 = _t1543
                if deconstruct_result1364 is not None:
                    assert deconstruct_result1364 is not None
                    unwrapped1365 = deconstruct_result1364
                    self.pretty_output(unwrapped1365)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1544 = _dollar_dollar.what_if
                    else:
                        _t1544 = None
                    deconstruct_result1362 = _t1544
                    if deconstruct_result1362 is not None:
                        assert deconstruct_result1362 is not None
                        unwrapped1363 = deconstruct_result1362
                        self.pretty_what_if(unwrapped1363)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1545 = _dollar_dollar.abort
                        else:
                            _t1545 = None
                        deconstruct_result1360 = _t1545
                        if deconstruct_result1360 is not None:
                            assert deconstruct_result1360 is not None
                            unwrapped1361 = deconstruct_result1360
                            self.pretty_abort(unwrapped1361)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1546 = _dollar_dollar.export
                            else:
                                _t1546 = None
                            deconstruct_result1358 = _t1546
                            if deconstruct_result1358 is not None:
                                assert deconstruct_result1358 is not None
                                unwrapped1359 = deconstruct_result1358
                                self.pretty_export(unwrapped1359)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1371 = self._try_flat(msg, self.pretty_demand)
        if flat1371 is not None:
            assert flat1371 is not None
            self.write(flat1371)
            return None
        else:
            _dollar_dollar = msg
            fields1369 = _dollar_dollar.relation_id
            assert fields1369 is not None
            unwrapped_fields1370 = fields1369
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1370)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1376 = self._try_flat(msg, self.pretty_output)
        if flat1376 is not None:
            assert flat1376 is not None
            self.write(flat1376)
            return None
        else:
            _dollar_dollar = msg
            fields1372 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1372 is not None
            unwrapped_fields1373 = fields1372
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1374 = unwrapped_fields1373[0]
            self.pretty_name(field1374)
            self.newline()
            field1375 = unwrapped_fields1373[1]
            self.pretty_relation_id(field1375)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1381 = self._try_flat(msg, self.pretty_what_if)
        if flat1381 is not None:
            assert flat1381 is not None
            self.write(flat1381)
            return None
        else:
            _dollar_dollar = msg
            fields1377 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1377 is not None
            unwrapped_fields1378 = fields1377
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1379 = unwrapped_fields1378[0]
            self.pretty_name(field1379)
            self.newline()
            field1380 = unwrapped_fields1378[1]
            self.pretty_epoch(field1380)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1387 = self._try_flat(msg, self.pretty_abort)
        if flat1387 is not None:
            assert flat1387 is not None
            self.write(flat1387)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1547 = _dollar_dollar.name
            else:
                _t1547 = None
            fields1382 = (_t1547, _dollar_dollar.relation_id,)
            assert fields1382 is not None
            unwrapped_fields1383 = fields1382
            self.write("(abort")
            self.indent_sexp()
            field1384 = unwrapped_fields1383[0]
            if field1384 is not None:
                self.newline()
                assert field1384 is not None
                opt_val1385 = field1384
                self.pretty_name(opt_val1385)
            self.newline()
            field1386 = unwrapped_fields1383[1]
            self.pretty_relation_id(field1386)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1390 = self._try_flat(msg, self.pretty_export)
        if flat1390 is not None:
            assert flat1390 is not None
            self.write(flat1390)
            return None
        else:
            _dollar_dollar = msg
            fields1388 = _dollar_dollar.csv_config
            assert fields1388 is not None
            unwrapped_fields1389 = fields1388
            self.write("(export")
            self.indent_sexp()
            self.newline()
            self.pretty_export_csv_config(unwrapped_fields1389)
            self.dedent()
            self.write(")")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1401 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1401 is not None:
            assert flat1401 is not None
            self.write(flat1401)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1548 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1548 = None
            deconstruct_result1396 = _t1548
            if deconstruct_result1396 is not None:
                assert deconstruct_result1396 is not None
                unwrapped1397 = deconstruct_result1396
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1398 = unwrapped1397[0]
                self.pretty_export_csv_path(field1398)
                self.newline()
                field1399 = unwrapped1397[1]
                self.pretty_export_csv_source(field1399)
                self.newline()
                field1400 = unwrapped1397[2]
                self.pretty_csv_config(field1400)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1550 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1549 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1550,)
                else:
                    _t1549 = None
                deconstruct_result1391 = _t1549
                if deconstruct_result1391 is not None:
                    assert deconstruct_result1391 is not None
                    unwrapped1392 = deconstruct_result1391
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1393 = unwrapped1392[0]
                    self.pretty_export_csv_path(field1393)
                    self.newline()
                    field1394 = unwrapped1392[1]
                    self.pretty_export_csv_columns_list(field1394)
                    self.newline()
                    field1395 = unwrapped1392[2]
                    self.pretty_config_dict(field1395)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1403 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1403 is not None:
            assert flat1403 is not None
            self.write(flat1403)
            return None
        else:
            fields1402 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1402))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1410 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1410 is not None:
            assert flat1410 is not None
            self.write(flat1410)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1551 = _dollar_dollar.gnf_columns.columns
            else:
                _t1551 = None
            deconstruct_result1406 = _t1551
            if deconstruct_result1406 is not None:
                assert deconstruct_result1406 is not None
                unwrapped1407 = deconstruct_result1406
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1407) == 0:
                    self.newline()
                    for i1409, elem1408 in enumerate(unwrapped1407):
                        if (i1409 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1408)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1552 = _dollar_dollar.table_def
                else:
                    _t1552 = None
                deconstruct_result1404 = _t1552
                if deconstruct_result1404 is not None:
                    assert deconstruct_result1404 is not None
                    unwrapped1405 = deconstruct_result1404
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1405)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1415 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1415 is not None:
            assert flat1415 is not None
            self.write(flat1415)
            return None
        else:
            _dollar_dollar = msg
            fields1411 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1411 is not None
            unwrapped_fields1412 = fields1411
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1413 = unwrapped_fields1412[0]
            self.write(self.format_string_value(field1413))
            self.newline()
            field1414 = unwrapped_fields1412[1]
            self.pretty_relation_id(field1414)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1419 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1419 is not None:
            assert flat1419 is not None
            self.write(flat1419)
            return None
        else:
            fields1416 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1416) == 0:
                self.newline()
                for i1418, elem1417 in enumerate(fields1416):
                    if (i1418 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1417)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1591 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1591)
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
