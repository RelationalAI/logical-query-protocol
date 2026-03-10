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
        _t1459 = logic_pb2.Value(int32_value=v)
        return _t1459

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1460 = logic_pb2.Value(int_value=v)
        return _t1460

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1461 = logic_pb2.Value(float_value=v)
        return _t1461

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1462 = logic_pb2.Value(string_value=v)
        return _t1462

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1463 = logic_pb2.Value(boolean_value=v)
        return _t1463

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1464 = logic_pb2.Value(uint128_value=v)
        return _t1464

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1465 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1465,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1466 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1466,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1467 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1467,))
        _t1468 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1468,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1469 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1469,))
        _t1470 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1470,))
        if msg.new_line != "":
            _t1471 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1471,))
        _t1472 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1472,))
        _t1473 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1473,))
        _t1474 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1474,))
        if msg.comment != "":
            _t1475 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1475,))
        for missing_string in msg.missing_strings:
            _t1476 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1476,))
        _t1477 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1477,))
        _t1478 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1478,))
        _t1479 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1479,))
        if msg.partition_size_mb != 0:
            _t1480 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1480,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1481 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1481,))
        _t1482 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1482,))
        _t1483 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1483,))
        _t1484 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1484,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1485 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1485,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1486 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1486,))
        _t1487 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1487,))
        _t1488 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1488,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1489 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1489,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1490 = self._make_value_string(msg.compression)
            result.append(("compression", _t1490,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1491 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1491,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1492 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1492,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1493 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1493,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1494 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1494,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1495 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1495,))
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
            _t1496 = None
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
        flat678 = self._try_flat(msg, self.pretty_transaction)
        if flat678 is not None:
            assert flat678 is not None
            self.write(flat678)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1338 = _dollar_dollar.configure
            else:
                _t1338 = None
            if _dollar_dollar.HasField("sync"):
                _t1339 = _dollar_dollar.sync
            else:
                _t1339 = None
            fields669 = (_t1338, _t1339, _dollar_dollar.epochs,)
            assert fields669 is not None
            unwrapped_fields670 = fields669
            self.write("(transaction")
            self.indent_sexp()
            field671 = unwrapped_fields670[0]
            if field671 is not None:
                self.newline()
                assert field671 is not None
                opt_val672 = field671
                self.pretty_configure(opt_val672)
            field673 = unwrapped_fields670[1]
            if field673 is not None:
                self.newline()
                assert field673 is not None
                opt_val674 = field673
                self.pretty_sync(opt_val674)
            field675 = unwrapped_fields670[2]
            if not len(field675) == 0:
                self.newline()
                for i677, elem676 in enumerate(field675):
                    if (i677 > 0):
                        self.newline()
                    self.pretty_epoch(elem676)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat681 = self._try_flat(msg, self.pretty_configure)
        if flat681 is not None:
            assert flat681 is not None
            self.write(flat681)
            return None
        else:
            _dollar_dollar = msg
            _t1340 = self.deconstruct_configure(_dollar_dollar)
            fields679 = _t1340
            assert fields679 is not None
            unwrapped_fields680 = fields679
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields680)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat685 = self._try_flat(msg, self.pretty_config_dict)
        if flat685 is not None:
            assert flat685 is not None
            self.write(flat685)
            return None
        else:
            fields682 = msg
            self.write("{")
            self.indent()
            if not len(fields682) == 0:
                self.newline()
                for i684, elem683 in enumerate(fields682):
                    if (i684 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem683)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat690 = self._try_flat(msg, self.pretty_config_key_value)
        if flat690 is not None:
            assert flat690 is not None
            self.write(flat690)
            return None
        else:
            _dollar_dollar = msg
            fields686 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields686 is not None
            unwrapped_fields687 = fields686
            self.write(":")
            field688 = unwrapped_fields687[0]
            self.write(field688)
            self.write(" ")
            field689 = unwrapped_fields687[1]
            self.pretty_value(field689)

    def pretty_value(self, msg: logic_pb2.Value):
        flat716 = self._try_flat(msg, self.pretty_value)
        if flat716 is not None:
            assert flat716 is not None
            self.write(flat716)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1341 = _dollar_dollar.date_value
            else:
                _t1341 = None
            deconstruct_result714 = _t1341
            if deconstruct_result714 is not None:
                assert deconstruct_result714 is not None
                unwrapped715 = deconstruct_result714
                self.pretty_date(unwrapped715)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1342 = _dollar_dollar.datetime_value
                else:
                    _t1342 = None
                deconstruct_result712 = _t1342
                if deconstruct_result712 is not None:
                    assert deconstruct_result712 is not None
                    unwrapped713 = deconstruct_result712
                    self.pretty_datetime(unwrapped713)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1343 = _dollar_dollar.string_value
                    else:
                        _t1343 = None
                    deconstruct_result710 = _t1343
                    if deconstruct_result710 is not None:
                        assert deconstruct_result710 is not None
                        unwrapped711 = deconstruct_result710
                        self.write(self.format_string_value(unwrapped711))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int_value"):
                            _t1344 = _dollar_dollar.int_value
                        else:
                            _t1344 = None
                        deconstruct_result708 = _t1344
                        if deconstruct_result708 is not None:
                            assert deconstruct_result708 is not None
                            unwrapped709 = deconstruct_result708
                            self.write(str(unwrapped709))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("float_value"):
                                _t1345 = _dollar_dollar.float_value
                            else:
                                _t1345 = None
                            deconstruct_result706 = _t1345
                            if deconstruct_result706 is not None:
                                assert deconstruct_result706 is not None
                                unwrapped707 = deconstruct_result706
                                self.write(str(unwrapped707))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("uint128_value"):
                                    _t1346 = _dollar_dollar.uint128_value
                                else:
                                    _t1346 = None
                                deconstruct_result704 = _t1346
                                if deconstruct_result704 is not None:
                                    assert deconstruct_result704 is not None
                                    unwrapped705 = deconstruct_result704
                                    self.write(self.format_uint128(unwrapped705))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("int128_value"):
                                        _t1347 = _dollar_dollar.int128_value
                                    else:
                                        _t1347 = None
                                    deconstruct_result702 = _t1347
                                    if deconstruct_result702 is not None:
                                        assert deconstruct_result702 is not None
                                        unwrapped703 = deconstruct_result702
                                        self.write(self.format_int128(unwrapped703))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("decimal_value"):
                                            _t1348 = _dollar_dollar.decimal_value
                                        else:
                                            _t1348 = None
                                        deconstruct_result700 = _t1348
                                        if deconstruct_result700 is not None:
                                            assert deconstruct_result700 is not None
                                            unwrapped701 = deconstruct_result700
                                            self.write(self.format_decimal(unwrapped701))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("boolean_value"):
                                                _t1349 = _dollar_dollar.boolean_value
                                            else:
                                                _t1349 = None
                                            deconstruct_result698 = _t1349
                                            if deconstruct_result698 is not None:
                                                assert deconstruct_result698 is not None
                                                unwrapped699 = deconstruct_result698
                                                self.pretty_boolean_value(unwrapped699)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int32_value"):
                                                    _t1350 = _dollar_dollar.int32_value
                                                else:
                                                    _t1350 = None
                                                deconstruct_result696 = _t1350
                                                if deconstruct_result696 is not None:
                                                    assert deconstruct_result696 is not None
                                                    unwrapped697 = deconstruct_result696
                                                    self.write((str(unwrapped697) + 'i32'))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("float32_value"):
                                                        _t1351 = _dollar_dollar.float32_value
                                                    else:
                                                        _t1351 = None
                                                    deconstruct_result694 = _t1351
                                                    if deconstruct_result694 is not None:
                                                        assert deconstruct_result694 is not None
                                                        unwrapped695 = deconstruct_result694
                                                        self.write((self.format_float32_value(unwrapped695) + 'f32'))
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("uint32_value"):
                                                            _t1352 = _dollar_dollar.uint32_value
                                                        else:
                                                            _t1352 = None
                                                        deconstruct_result692 = _t1352
                                                        if deconstruct_result692 is not None:
                                                            assert deconstruct_result692 is not None
                                                            unwrapped693 = deconstruct_result692
                                                            self.write((str(unwrapped693) + 'u32'))
                                                        else:
                                                            fields691 = msg
                                                            self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat722 = self._try_flat(msg, self.pretty_date)
        if flat722 is not None:
            assert flat722 is not None
            self.write(flat722)
            return None
        else:
            _dollar_dollar = msg
            fields717 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields717 is not None
            unwrapped_fields718 = fields717
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field719 = unwrapped_fields718[0]
            self.write(str(field719))
            self.newline()
            field720 = unwrapped_fields718[1]
            self.write(str(field720))
            self.newline()
            field721 = unwrapped_fields718[2]
            self.write(str(field721))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat733 = self._try_flat(msg, self.pretty_datetime)
        if flat733 is not None:
            assert flat733 is not None
            self.write(flat733)
            return None
        else:
            _dollar_dollar = msg
            fields723 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields723 is not None
            unwrapped_fields724 = fields723
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field725 = unwrapped_fields724[0]
            self.write(str(field725))
            self.newline()
            field726 = unwrapped_fields724[1]
            self.write(str(field726))
            self.newline()
            field727 = unwrapped_fields724[2]
            self.write(str(field727))
            self.newline()
            field728 = unwrapped_fields724[3]
            self.write(str(field728))
            self.newline()
            field729 = unwrapped_fields724[4]
            self.write(str(field729))
            self.newline()
            field730 = unwrapped_fields724[5]
            self.write(str(field730))
            field731 = unwrapped_fields724[6]
            if field731 is not None:
                self.newline()
                assert field731 is not None
                opt_val732 = field731
                self.write(str(opt_val732))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1353 = ()
        else:
            _t1353 = None
        deconstruct_result736 = _t1353
        if deconstruct_result736 is not None:
            assert deconstruct_result736 is not None
            unwrapped737 = deconstruct_result736
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1354 = ()
            else:
                _t1354 = None
            deconstruct_result734 = _t1354
            if deconstruct_result734 is not None:
                assert deconstruct_result734 is not None
                unwrapped735 = deconstruct_result734
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat742 = self._try_flat(msg, self.pretty_sync)
        if flat742 is not None:
            assert flat742 is not None
            self.write(flat742)
            return None
        else:
            _dollar_dollar = msg
            fields738 = _dollar_dollar.fragments
            assert fields738 is not None
            unwrapped_fields739 = fields738
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields739) == 0:
                self.newline()
                for i741, elem740 in enumerate(unwrapped_fields739):
                    if (i741 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem740)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat745 = self._try_flat(msg, self.pretty_fragment_id)
        if flat745 is not None:
            assert flat745 is not None
            self.write(flat745)
            return None
        else:
            _dollar_dollar = msg
            fields743 = self.fragment_id_to_string(_dollar_dollar)
            assert fields743 is not None
            unwrapped_fields744 = fields743
            self.write(":")
            self.write(unwrapped_fields744)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat752 = self._try_flat(msg, self.pretty_epoch)
        if flat752 is not None:
            assert flat752 is not None
            self.write(flat752)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1355 = _dollar_dollar.writes
            else:
                _t1355 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1356 = _dollar_dollar.reads
            else:
                _t1356 = None
            fields746 = (_t1355, _t1356,)
            assert fields746 is not None
            unwrapped_fields747 = fields746
            self.write("(epoch")
            self.indent_sexp()
            field748 = unwrapped_fields747[0]
            if field748 is not None:
                self.newline()
                assert field748 is not None
                opt_val749 = field748
                self.pretty_epoch_writes(opt_val749)
            field750 = unwrapped_fields747[1]
            if field750 is not None:
                self.newline()
                assert field750 is not None
                opt_val751 = field750
                self.pretty_epoch_reads(opt_val751)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat756 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat756 is not None:
            assert flat756 is not None
            self.write(flat756)
            return None
        else:
            fields753 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields753) == 0:
                self.newline()
                for i755, elem754 in enumerate(fields753):
                    if (i755 > 0):
                        self.newline()
                    self.pretty_write(elem754)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat765 = self._try_flat(msg, self.pretty_write)
        if flat765 is not None:
            assert flat765 is not None
            self.write(flat765)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1357 = _dollar_dollar.define
            else:
                _t1357 = None
            deconstruct_result763 = _t1357
            if deconstruct_result763 is not None:
                assert deconstruct_result763 is not None
                unwrapped764 = deconstruct_result763
                self.pretty_define(unwrapped764)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1358 = _dollar_dollar.undefine
                else:
                    _t1358 = None
                deconstruct_result761 = _t1358
                if deconstruct_result761 is not None:
                    assert deconstruct_result761 is not None
                    unwrapped762 = deconstruct_result761
                    self.pretty_undefine(unwrapped762)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1359 = _dollar_dollar.context
                    else:
                        _t1359 = None
                    deconstruct_result759 = _t1359
                    if deconstruct_result759 is not None:
                        assert deconstruct_result759 is not None
                        unwrapped760 = deconstruct_result759
                        self.pretty_context(unwrapped760)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1360 = _dollar_dollar.snapshot
                        else:
                            _t1360 = None
                        deconstruct_result757 = _t1360
                        if deconstruct_result757 is not None:
                            assert deconstruct_result757 is not None
                            unwrapped758 = deconstruct_result757
                            self.pretty_snapshot(unwrapped758)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat768 = self._try_flat(msg, self.pretty_define)
        if flat768 is not None:
            assert flat768 is not None
            self.write(flat768)
            return None
        else:
            _dollar_dollar = msg
            fields766 = _dollar_dollar.fragment
            assert fields766 is not None
            unwrapped_fields767 = fields766
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields767)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat775 = self._try_flat(msg, self.pretty_fragment)
        if flat775 is not None:
            assert flat775 is not None
            self.write(flat775)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields769 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields769 is not None
            unwrapped_fields770 = fields769
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field771 = unwrapped_fields770[0]
            self.pretty_new_fragment_id(field771)
            field772 = unwrapped_fields770[1]
            if not len(field772) == 0:
                self.newline()
                for i774, elem773 in enumerate(field772):
                    if (i774 > 0):
                        self.newline()
                    self.pretty_declaration(elem773)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat777 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat777 is not None:
            assert flat777 is not None
            self.write(flat777)
            return None
        else:
            fields776 = msg
            self.pretty_fragment_id(fields776)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat786 = self._try_flat(msg, self.pretty_declaration)
        if flat786 is not None:
            assert flat786 is not None
            self.write(flat786)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1361 = getattr(_dollar_dollar, 'def')
            else:
                _t1361 = None
            deconstruct_result784 = _t1361
            if deconstruct_result784 is not None:
                assert deconstruct_result784 is not None
                unwrapped785 = deconstruct_result784
                self.pretty_def(unwrapped785)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1362 = _dollar_dollar.algorithm
                else:
                    _t1362 = None
                deconstruct_result782 = _t1362
                if deconstruct_result782 is not None:
                    assert deconstruct_result782 is not None
                    unwrapped783 = deconstruct_result782
                    self.pretty_algorithm(unwrapped783)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1363 = _dollar_dollar.constraint
                    else:
                        _t1363 = None
                    deconstruct_result780 = _t1363
                    if deconstruct_result780 is not None:
                        assert deconstruct_result780 is not None
                        unwrapped781 = deconstruct_result780
                        self.pretty_constraint(unwrapped781)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1364 = _dollar_dollar.data
                        else:
                            _t1364 = None
                        deconstruct_result778 = _t1364
                        if deconstruct_result778 is not None:
                            assert deconstruct_result778 is not None
                            unwrapped779 = deconstruct_result778
                            self.pretty_data(unwrapped779)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat793 = self._try_flat(msg, self.pretty_def)
        if flat793 is not None:
            assert flat793 is not None
            self.write(flat793)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1365 = _dollar_dollar.attrs
            else:
                _t1365 = None
            fields787 = (_dollar_dollar.name, _dollar_dollar.body, _t1365,)
            assert fields787 is not None
            unwrapped_fields788 = fields787
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field789 = unwrapped_fields788[0]
            self.pretty_relation_id(field789)
            self.newline()
            field790 = unwrapped_fields788[1]
            self.pretty_abstraction(field790)
            field791 = unwrapped_fields788[2]
            if field791 is not None:
                self.newline()
                assert field791 is not None
                opt_val792 = field791
                self.pretty_attrs(opt_val792)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat798 = self._try_flat(msg, self.pretty_relation_id)
        if flat798 is not None:
            assert flat798 is not None
            self.write(flat798)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1367 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1366 = _t1367
            else:
                _t1366 = None
            deconstruct_result796 = _t1366
            if deconstruct_result796 is not None:
                assert deconstruct_result796 is not None
                unwrapped797 = deconstruct_result796
                self.write(":")
                self.write(unwrapped797)
            else:
                _dollar_dollar = msg
                _t1368 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result794 = _t1368
                if deconstruct_result794 is not None:
                    assert deconstruct_result794 is not None
                    unwrapped795 = deconstruct_result794
                    self.write(self.format_uint128(unwrapped795))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat803 = self._try_flat(msg, self.pretty_abstraction)
        if flat803 is not None:
            assert flat803 is not None
            self.write(flat803)
            return None
        else:
            _dollar_dollar = msg
            _t1369 = self.deconstruct_bindings(_dollar_dollar)
            fields799 = (_t1369, _dollar_dollar.value,)
            assert fields799 is not None
            unwrapped_fields800 = fields799
            self.write("(")
            self.indent()
            field801 = unwrapped_fields800[0]
            self.pretty_bindings(field801)
            self.newline()
            field802 = unwrapped_fields800[1]
            self.pretty_formula(field802)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat811 = self._try_flat(msg, self.pretty_bindings)
        if flat811 is not None:
            assert flat811 is not None
            self.write(flat811)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1370 = _dollar_dollar[1]
            else:
                _t1370 = None
            fields804 = (_dollar_dollar[0], _t1370,)
            assert fields804 is not None
            unwrapped_fields805 = fields804
            self.write("[")
            self.indent()
            field806 = unwrapped_fields805[0]
            for i808, elem807 in enumerate(field806):
                if (i808 > 0):
                    self.newline()
                self.pretty_binding(elem807)
            field809 = unwrapped_fields805[1]
            if field809 is not None:
                self.newline()
                assert field809 is not None
                opt_val810 = field809
                self.pretty_value_bindings(opt_val810)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat816 = self._try_flat(msg, self.pretty_binding)
        if flat816 is not None:
            assert flat816 is not None
            self.write(flat816)
            return None
        else:
            _dollar_dollar = msg
            fields812 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields812 is not None
            unwrapped_fields813 = fields812
            field814 = unwrapped_fields813[0]
            self.write(field814)
            self.write("::")
            field815 = unwrapped_fields813[1]
            self.pretty_type(field815)

    def pretty_type(self, msg: logic_pb2.Type):
        flat845 = self._try_flat(msg, self.pretty_type)
        if flat845 is not None:
            assert flat845 is not None
            self.write(flat845)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1371 = _dollar_dollar.unspecified_type
            else:
                _t1371 = None
            deconstruct_result843 = _t1371
            if deconstruct_result843 is not None:
                assert deconstruct_result843 is not None
                unwrapped844 = deconstruct_result843
                self.pretty_unspecified_type(unwrapped844)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1372 = _dollar_dollar.string_type
                else:
                    _t1372 = None
                deconstruct_result841 = _t1372
                if deconstruct_result841 is not None:
                    assert deconstruct_result841 is not None
                    unwrapped842 = deconstruct_result841
                    self.pretty_string_type(unwrapped842)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1373 = _dollar_dollar.int_type
                    else:
                        _t1373 = None
                    deconstruct_result839 = _t1373
                    if deconstruct_result839 is not None:
                        assert deconstruct_result839 is not None
                        unwrapped840 = deconstruct_result839
                        self.pretty_int_type(unwrapped840)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1374 = _dollar_dollar.float_type
                        else:
                            _t1374 = None
                        deconstruct_result837 = _t1374
                        if deconstruct_result837 is not None:
                            assert deconstruct_result837 is not None
                            unwrapped838 = deconstruct_result837
                            self.pretty_float_type(unwrapped838)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1375 = _dollar_dollar.uint128_type
                            else:
                                _t1375 = None
                            deconstruct_result835 = _t1375
                            if deconstruct_result835 is not None:
                                assert deconstruct_result835 is not None
                                unwrapped836 = deconstruct_result835
                                self.pretty_uint128_type(unwrapped836)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1376 = _dollar_dollar.int128_type
                                else:
                                    _t1376 = None
                                deconstruct_result833 = _t1376
                                if deconstruct_result833 is not None:
                                    assert deconstruct_result833 is not None
                                    unwrapped834 = deconstruct_result833
                                    self.pretty_int128_type(unwrapped834)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1377 = _dollar_dollar.date_type
                                    else:
                                        _t1377 = None
                                    deconstruct_result831 = _t1377
                                    if deconstruct_result831 is not None:
                                        assert deconstruct_result831 is not None
                                        unwrapped832 = deconstruct_result831
                                        self.pretty_date_type(unwrapped832)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1378 = _dollar_dollar.datetime_type
                                        else:
                                            _t1378 = None
                                        deconstruct_result829 = _t1378
                                        if deconstruct_result829 is not None:
                                            assert deconstruct_result829 is not None
                                            unwrapped830 = deconstruct_result829
                                            self.pretty_datetime_type(unwrapped830)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1379 = _dollar_dollar.missing_type
                                            else:
                                                _t1379 = None
                                            deconstruct_result827 = _t1379
                                            if deconstruct_result827 is not None:
                                                assert deconstruct_result827 is not None
                                                unwrapped828 = deconstruct_result827
                                                self.pretty_missing_type(unwrapped828)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1380 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1380 = None
                                                deconstruct_result825 = _t1380
                                                if deconstruct_result825 is not None:
                                                    assert deconstruct_result825 is not None
                                                    unwrapped826 = deconstruct_result825
                                                    self.pretty_decimal_type(unwrapped826)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1381 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1381 = None
                                                    deconstruct_result823 = _t1381
                                                    if deconstruct_result823 is not None:
                                                        assert deconstruct_result823 is not None
                                                        unwrapped824 = deconstruct_result823
                                                        self.pretty_boolean_type(unwrapped824)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1382 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1382 = None
                                                        deconstruct_result821 = _t1382
                                                        if deconstruct_result821 is not None:
                                                            assert deconstruct_result821 is not None
                                                            unwrapped822 = deconstruct_result821
                                                            self.pretty_int32_type(unwrapped822)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1383 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1383 = None
                                                            deconstruct_result819 = _t1383
                                                            if deconstruct_result819 is not None:
                                                                assert deconstruct_result819 is not None
                                                                unwrapped820 = deconstruct_result819
                                                                self.pretty_float32_type(unwrapped820)
                                                            else:
                                                                _dollar_dollar = msg
                                                                if _dollar_dollar.HasField("uint32_type"):
                                                                    _t1384 = _dollar_dollar.uint32_type
                                                                else:
                                                                    _t1384 = None
                                                                deconstruct_result817 = _t1384
                                                                if deconstruct_result817 is not None:
                                                                    assert deconstruct_result817 is not None
                                                                    unwrapped818 = deconstruct_result817
                                                                    self.pretty_uint32_type(unwrapped818)
                                                                else:
                                                                    raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields846 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields847 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields848 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields849 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields850 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields851 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields852 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields853 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields854 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat859 = self._try_flat(msg, self.pretty_decimal_type)
        if flat859 is not None:
            assert flat859 is not None
            self.write(flat859)
            return None
        else:
            _dollar_dollar = msg
            fields855 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields855 is not None
            unwrapped_fields856 = fields855
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field857 = unwrapped_fields856[0]
            self.write(str(field857))
            self.newline()
            field858 = unwrapped_fields856[1]
            self.write(str(field858))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields860 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields861 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields862 = msg
        self.write("FLOAT32")

    def pretty_uint32_type(self, msg: logic_pb2.UInt32Type):
        fields863 = msg
        self.write("UINT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat867 = self._try_flat(msg, self.pretty_value_bindings)
        if flat867 is not None:
            assert flat867 is not None
            self.write(flat867)
            return None
        else:
            fields864 = msg
            self.write("|")
            if not len(fields864) == 0:
                self.write(" ")
                for i866, elem865 in enumerate(fields864):
                    if (i866 > 0):
                        self.newline()
                    self.pretty_binding(elem865)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat894 = self._try_flat(msg, self.pretty_formula)
        if flat894 is not None:
            assert flat894 is not None
            self.write(flat894)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1385 = _dollar_dollar.conjunction
            else:
                _t1385 = None
            deconstruct_result892 = _t1385
            if deconstruct_result892 is not None:
                assert deconstruct_result892 is not None
                unwrapped893 = deconstruct_result892
                self.pretty_true(unwrapped893)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1386 = _dollar_dollar.disjunction
                else:
                    _t1386 = None
                deconstruct_result890 = _t1386
                if deconstruct_result890 is not None:
                    assert deconstruct_result890 is not None
                    unwrapped891 = deconstruct_result890
                    self.pretty_false(unwrapped891)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1387 = _dollar_dollar.exists
                    else:
                        _t1387 = None
                    deconstruct_result888 = _t1387
                    if deconstruct_result888 is not None:
                        assert deconstruct_result888 is not None
                        unwrapped889 = deconstruct_result888
                        self.pretty_exists(unwrapped889)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1388 = _dollar_dollar.reduce
                        else:
                            _t1388 = None
                        deconstruct_result886 = _t1388
                        if deconstruct_result886 is not None:
                            assert deconstruct_result886 is not None
                            unwrapped887 = deconstruct_result886
                            self.pretty_reduce(unwrapped887)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1389 = _dollar_dollar.conjunction
                            else:
                                _t1389 = None
                            deconstruct_result884 = _t1389
                            if deconstruct_result884 is not None:
                                assert deconstruct_result884 is not None
                                unwrapped885 = deconstruct_result884
                                self.pretty_conjunction(unwrapped885)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1390 = _dollar_dollar.disjunction
                                else:
                                    _t1390 = None
                                deconstruct_result882 = _t1390
                                if deconstruct_result882 is not None:
                                    assert deconstruct_result882 is not None
                                    unwrapped883 = deconstruct_result882
                                    self.pretty_disjunction(unwrapped883)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1391 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1391 = None
                                    deconstruct_result880 = _t1391
                                    if deconstruct_result880 is not None:
                                        assert deconstruct_result880 is not None
                                        unwrapped881 = deconstruct_result880
                                        self.pretty_not(unwrapped881)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1392 = _dollar_dollar.ffi
                                        else:
                                            _t1392 = None
                                        deconstruct_result878 = _t1392
                                        if deconstruct_result878 is not None:
                                            assert deconstruct_result878 is not None
                                            unwrapped879 = deconstruct_result878
                                            self.pretty_ffi(unwrapped879)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1393 = _dollar_dollar.atom
                                            else:
                                                _t1393 = None
                                            deconstruct_result876 = _t1393
                                            if deconstruct_result876 is not None:
                                                assert deconstruct_result876 is not None
                                                unwrapped877 = deconstruct_result876
                                                self.pretty_atom(unwrapped877)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1394 = _dollar_dollar.pragma
                                                else:
                                                    _t1394 = None
                                                deconstruct_result874 = _t1394
                                                if deconstruct_result874 is not None:
                                                    assert deconstruct_result874 is not None
                                                    unwrapped875 = deconstruct_result874
                                                    self.pretty_pragma(unwrapped875)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1395 = _dollar_dollar.primitive
                                                    else:
                                                        _t1395 = None
                                                    deconstruct_result872 = _t1395
                                                    if deconstruct_result872 is not None:
                                                        assert deconstruct_result872 is not None
                                                        unwrapped873 = deconstruct_result872
                                                        self.pretty_primitive(unwrapped873)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1396 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1396 = None
                                                        deconstruct_result870 = _t1396
                                                        if deconstruct_result870 is not None:
                                                            assert deconstruct_result870 is not None
                                                            unwrapped871 = deconstruct_result870
                                                            self.pretty_rel_atom(unwrapped871)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1397 = _dollar_dollar.cast
                                                            else:
                                                                _t1397 = None
                                                            deconstruct_result868 = _t1397
                                                            if deconstruct_result868 is not None:
                                                                assert deconstruct_result868 is not None
                                                                unwrapped869 = deconstruct_result868
                                                                self.pretty_cast(unwrapped869)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields895 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields896 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat901 = self._try_flat(msg, self.pretty_exists)
        if flat901 is not None:
            assert flat901 is not None
            self.write(flat901)
            return None
        else:
            _dollar_dollar = msg
            _t1398 = self.deconstruct_bindings(_dollar_dollar.body)
            fields897 = (_t1398, _dollar_dollar.body.value,)
            assert fields897 is not None
            unwrapped_fields898 = fields897
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field899 = unwrapped_fields898[0]
            self.pretty_bindings(field899)
            self.newline()
            field900 = unwrapped_fields898[1]
            self.pretty_formula(field900)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat907 = self._try_flat(msg, self.pretty_reduce)
        if flat907 is not None:
            assert flat907 is not None
            self.write(flat907)
            return None
        else:
            _dollar_dollar = msg
            fields902 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields902 is not None
            unwrapped_fields903 = fields902
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field904 = unwrapped_fields903[0]
            self.pretty_abstraction(field904)
            self.newline()
            field905 = unwrapped_fields903[1]
            self.pretty_abstraction(field905)
            self.newline()
            field906 = unwrapped_fields903[2]
            self.pretty_terms(field906)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat911 = self._try_flat(msg, self.pretty_terms)
        if flat911 is not None:
            assert flat911 is not None
            self.write(flat911)
            return None
        else:
            fields908 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields908) == 0:
                self.newline()
                for i910, elem909 in enumerate(fields908):
                    if (i910 > 0):
                        self.newline()
                    self.pretty_term(elem909)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat916 = self._try_flat(msg, self.pretty_term)
        if flat916 is not None:
            assert flat916 is not None
            self.write(flat916)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1399 = _dollar_dollar.var
            else:
                _t1399 = None
            deconstruct_result914 = _t1399
            if deconstruct_result914 is not None:
                assert deconstruct_result914 is not None
                unwrapped915 = deconstruct_result914
                self.pretty_var(unwrapped915)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1400 = _dollar_dollar.constant
                else:
                    _t1400 = None
                deconstruct_result912 = _t1400
                if deconstruct_result912 is not None:
                    assert deconstruct_result912 is not None
                    unwrapped913 = deconstruct_result912
                    self.pretty_constant(unwrapped913)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat919 = self._try_flat(msg, self.pretty_var)
        if flat919 is not None:
            assert flat919 is not None
            self.write(flat919)
            return None
        else:
            _dollar_dollar = msg
            fields917 = _dollar_dollar.name
            assert fields917 is not None
            unwrapped_fields918 = fields917
            self.write(unwrapped_fields918)

    def pretty_constant(self, msg: logic_pb2.Value):
        flat921 = self._try_flat(msg, self.pretty_constant)
        if flat921 is not None:
            assert flat921 is not None
            self.write(flat921)
            return None
        else:
            fields920 = msg
            self.pretty_value(fields920)

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat926 = self._try_flat(msg, self.pretty_conjunction)
        if flat926 is not None:
            assert flat926 is not None
            self.write(flat926)
            return None
        else:
            _dollar_dollar = msg
            fields922 = _dollar_dollar.args
            assert fields922 is not None
            unwrapped_fields923 = fields922
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields923) == 0:
                self.newline()
                for i925, elem924 in enumerate(unwrapped_fields923):
                    if (i925 > 0):
                        self.newline()
                    self.pretty_formula(elem924)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat931 = self._try_flat(msg, self.pretty_disjunction)
        if flat931 is not None:
            assert flat931 is not None
            self.write(flat931)
            return None
        else:
            _dollar_dollar = msg
            fields927 = _dollar_dollar.args
            assert fields927 is not None
            unwrapped_fields928 = fields927
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields928) == 0:
                self.newline()
                for i930, elem929 in enumerate(unwrapped_fields928):
                    if (i930 > 0):
                        self.newline()
                    self.pretty_formula(elem929)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat934 = self._try_flat(msg, self.pretty_not)
        if flat934 is not None:
            assert flat934 is not None
            self.write(flat934)
            return None
        else:
            _dollar_dollar = msg
            fields932 = _dollar_dollar.arg
            assert fields932 is not None
            unwrapped_fields933 = fields932
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields933)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat940 = self._try_flat(msg, self.pretty_ffi)
        if flat940 is not None:
            assert flat940 is not None
            self.write(flat940)
            return None
        else:
            _dollar_dollar = msg
            fields935 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields935 is not None
            unwrapped_fields936 = fields935
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field937 = unwrapped_fields936[0]
            self.pretty_name(field937)
            self.newline()
            field938 = unwrapped_fields936[1]
            self.pretty_ffi_args(field938)
            self.newline()
            field939 = unwrapped_fields936[2]
            self.pretty_terms(field939)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat942 = self._try_flat(msg, self.pretty_name)
        if flat942 is not None:
            assert flat942 is not None
            self.write(flat942)
            return None
        else:
            fields941 = msg
            self.write(":")
            self.write(fields941)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat946 = self._try_flat(msg, self.pretty_ffi_args)
        if flat946 is not None:
            assert flat946 is not None
            self.write(flat946)
            return None
        else:
            fields943 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields943) == 0:
                self.newline()
                for i945, elem944 in enumerate(fields943):
                    if (i945 > 0):
                        self.newline()
                    self.pretty_abstraction(elem944)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat953 = self._try_flat(msg, self.pretty_atom)
        if flat953 is not None:
            assert flat953 is not None
            self.write(flat953)
            return None
        else:
            _dollar_dollar = msg
            fields947 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields947 is not None
            unwrapped_fields948 = fields947
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field949 = unwrapped_fields948[0]
            self.pretty_relation_id(field949)
            field950 = unwrapped_fields948[1]
            if not len(field950) == 0:
                self.newline()
                for i952, elem951 in enumerate(field950):
                    if (i952 > 0):
                        self.newline()
                    self.pretty_term(elem951)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat960 = self._try_flat(msg, self.pretty_pragma)
        if flat960 is not None:
            assert flat960 is not None
            self.write(flat960)
            return None
        else:
            _dollar_dollar = msg
            fields954 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields954 is not None
            unwrapped_fields955 = fields954
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field956 = unwrapped_fields955[0]
            self.pretty_name(field956)
            field957 = unwrapped_fields955[1]
            if not len(field957) == 0:
                self.newline()
                for i959, elem958 in enumerate(field957):
                    if (i959 > 0):
                        self.newline()
                    self.pretty_term(elem958)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat976 = self._try_flat(msg, self.pretty_primitive)
        if flat976 is not None:
            assert flat976 is not None
            self.write(flat976)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1401 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1401 = None
            guard_result975 = _t1401
            if guard_result975 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1402 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1402 = None
                guard_result974 = _t1402
                if guard_result974 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1403 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1403 = None
                    guard_result973 = _t1403
                    if guard_result973 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1404 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1404 = None
                        guard_result972 = _t1404
                        if guard_result972 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1405 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1405 = None
                            guard_result971 = _t1405
                            if guard_result971 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1406 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1406 = None
                                guard_result970 = _t1406
                                if guard_result970 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1407 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1407 = None
                                    guard_result969 = _t1407
                                    if guard_result969 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1408 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1408 = None
                                        guard_result968 = _t1408
                                        if guard_result968 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1409 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1409 = None
                                            guard_result967 = _t1409
                                            if guard_result967 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields961 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields961 is not None
                                                unwrapped_fields962 = fields961
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field963 = unwrapped_fields962[0]
                                                self.pretty_name(field963)
                                                field964 = unwrapped_fields962[1]
                                                if not len(field964) == 0:
                                                    self.newline()
                                                    for i966, elem965 in enumerate(field964):
                                                        if (i966 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem965)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat981 = self._try_flat(msg, self.pretty_eq)
        if flat981 is not None:
            assert flat981 is not None
            self.write(flat981)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1410 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1410 = None
            fields977 = _t1410
            assert fields977 is not None
            unwrapped_fields978 = fields977
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field979 = unwrapped_fields978[0]
            self.pretty_term(field979)
            self.newline()
            field980 = unwrapped_fields978[1]
            self.pretty_term(field980)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat986 = self._try_flat(msg, self.pretty_lt)
        if flat986 is not None:
            assert flat986 is not None
            self.write(flat986)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1411 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1411 = None
            fields982 = _t1411
            assert fields982 is not None
            unwrapped_fields983 = fields982
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field984 = unwrapped_fields983[0]
            self.pretty_term(field984)
            self.newline()
            field985 = unwrapped_fields983[1]
            self.pretty_term(field985)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat991 = self._try_flat(msg, self.pretty_lt_eq)
        if flat991 is not None:
            assert flat991 is not None
            self.write(flat991)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1412 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1412 = None
            fields987 = _t1412
            assert fields987 is not None
            unwrapped_fields988 = fields987
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field989 = unwrapped_fields988[0]
            self.pretty_term(field989)
            self.newline()
            field990 = unwrapped_fields988[1]
            self.pretty_term(field990)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat996 = self._try_flat(msg, self.pretty_gt)
        if flat996 is not None:
            assert flat996 is not None
            self.write(flat996)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1413 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1413 = None
            fields992 = _t1413
            assert fields992 is not None
            unwrapped_fields993 = fields992
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field994 = unwrapped_fields993[0]
            self.pretty_term(field994)
            self.newline()
            field995 = unwrapped_fields993[1]
            self.pretty_term(field995)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat1001 = self._try_flat(msg, self.pretty_gt_eq)
        if flat1001 is not None:
            assert flat1001 is not None
            self.write(flat1001)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1414 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1414 = None
            fields997 = _t1414
            assert fields997 is not None
            unwrapped_fields998 = fields997
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field999 = unwrapped_fields998[0]
            self.pretty_term(field999)
            self.newline()
            field1000 = unwrapped_fields998[1]
            self.pretty_term(field1000)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat1007 = self._try_flat(msg, self.pretty_add)
        if flat1007 is not None:
            assert flat1007 is not None
            self.write(flat1007)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1415 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1415 = None
            fields1002 = _t1415
            assert fields1002 is not None
            unwrapped_fields1003 = fields1002
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field1004 = unwrapped_fields1003[0]
            self.pretty_term(field1004)
            self.newline()
            field1005 = unwrapped_fields1003[1]
            self.pretty_term(field1005)
            self.newline()
            field1006 = unwrapped_fields1003[2]
            self.pretty_term(field1006)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1013 = self._try_flat(msg, self.pretty_minus)
        if flat1013 is not None:
            assert flat1013 is not None
            self.write(flat1013)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1416 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1416 = None
            fields1008 = _t1416
            assert fields1008 is not None
            unwrapped_fields1009 = fields1008
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1010 = unwrapped_fields1009[0]
            self.pretty_term(field1010)
            self.newline()
            field1011 = unwrapped_fields1009[1]
            self.pretty_term(field1011)
            self.newline()
            field1012 = unwrapped_fields1009[2]
            self.pretty_term(field1012)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1019 = self._try_flat(msg, self.pretty_multiply)
        if flat1019 is not None:
            assert flat1019 is not None
            self.write(flat1019)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1417 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1417 = None
            fields1014 = _t1417
            assert fields1014 is not None
            unwrapped_fields1015 = fields1014
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1016 = unwrapped_fields1015[0]
            self.pretty_term(field1016)
            self.newline()
            field1017 = unwrapped_fields1015[1]
            self.pretty_term(field1017)
            self.newline()
            field1018 = unwrapped_fields1015[2]
            self.pretty_term(field1018)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1025 = self._try_flat(msg, self.pretty_divide)
        if flat1025 is not None:
            assert flat1025 is not None
            self.write(flat1025)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1418 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1418 = None
            fields1020 = _t1418
            assert fields1020 is not None
            unwrapped_fields1021 = fields1020
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1022 = unwrapped_fields1021[0]
            self.pretty_term(field1022)
            self.newline()
            field1023 = unwrapped_fields1021[1]
            self.pretty_term(field1023)
            self.newline()
            field1024 = unwrapped_fields1021[2]
            self.pretty_term(field1024)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1030 = self._try_flat(msg, self.pretty_rel_term)
        if flat1030 is not None:
            assert flat1030 is not None
            self.write(flat1030)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1419 = _dollar_dollar.specialized_value
            else:
                _t1419 = None
            deconstruct_result1028 = _t1419
            if deconstruct_result1028 is not None:
                assert deconstruct_result1028 is not None
                unwrapped1029 = deconstruct_result1028
                self.pretty_specialized_value(unwrapped1029)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1420 = _dollar_dollar.term
                else:
                    _t1420 = None
                deconstruct_result1026 = _t1420
                if deconstruct_result1026 is not None:
                    assert deconstruct_result1026 is not None
                    unwrapped1027 = deconstruct_result1026
                    self.pretty_term(unwrapped1027)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1032 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1032 is not None:
            assert flat1032 is not None
            self.write(flat1032)
            return None
        else:
            fields1031 = msg
            self.write("#")
            self.pretty_value(fields1031)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1039 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1039 is not None:
            assert flat1039 is not None
            self.write(flat1039)
            return None
        else:
            _dollar_dollar = msg
            fields1033 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1033 is not None
            unwrapped_fields1034 = fields1033
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1035 = unwrapped_fields1034[0]
            self.pretty_name(field1035)
            field1036 = unwrapped_fields1034[1]
            if not len(field1036) == 0:
                self.newline()
                for i1038, elem1037 in enumerate(field1036):
                    if (i1038 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1037)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1044 = self._try_flat(msg, self.pretty_cast)
        if flat1044 is not None:
            assert flat1044 is not None
            self.write(flat1044)
            return None
        else:
            _dollar_dollar = msg
            fields1040 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1040 is not None
            unwrapped_fields1041 = fields1040
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1042 = unwrapped_fields1041[0]
            self.pretty_term(field1042)
            self.newline()
            field1043 = unwrapped_fields1041[1]
            self.pretty_term(field1043)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1048 = self._try_flat(msg, self.pretty_attrs)
        if flat1048 is not None:
            assert flat1048 is not None
            self.write(flat1048)
            return None
        else:
            fields1045 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1045) == 0:
                self.newline()
                for i1047, elem1046 in enumerate(fields1045):
                    if (i1047 > 0):
                        self.newline()
                    self.pretty_attribute(elem1046)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1055 = self._try_flat(msg, self.pretty_attribute)
        if flat1055 is not None:
            assert flat1055 is not None
            self.write(flat1055)
            return None
        else:
            _dollar_dollar = msg
            fields1049 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1049 is not None
            unwrapped_fields1050 = fields1049
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1051 = unwrapped_fields1050[0]
            self.pretty_name(field1051)
            field1052 = unwrapped_fields1050[1]
            if not len(field1052) == 0:
                self.newline()
                for i1054, elem1053 in enumerate(field1052):
                    if (i1054 > 0):
                        self.newline()
                    self.pretty_value(elem1053)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1062 = self._try_flat(msg, self.pretty_algorithm)
        if flat1062 is not None:
            assert flat1062 is not None
            self.write(flat1062)
            return None
        else:
            _dollar_dollar = msg
            fields1056 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            assert fields1056 is not None
            unwrapped_fields1057 = fields1056
            self.write("(algorithm")
            self.indent_sexp()
            field1058 = unwrapped_fields1057[0]
            if not len(field1058) == 0:
                self.newline()
                for i1060, elem1059 in enumerate(field1058):
                    if (i1060 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1059)
            self.newline()
            field1061 = unwrapped_fields1057[1]
            self.pretty_script(field1061)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1067 = self._try_flat(msg, self.pretty_script)
        if flat1067 is not None:
            assert flat1067 is not None
            self.write(flat1067)
            return None
        else:
            _dollar_dollar = msg
            fields1063 = _dollar_dollar.constructs
            assert fields1063 is not None
            unwrapped_fields1064 = fields1063
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1064) == 0:
                self.newline()
                for i1066, elem1065 in enumerate(unwrapped_fields1064):
                    if (i1066 > 0):
                        self.newline()
                    self.pretty_construct(elem1065)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1072 = self._try_flat(msg, self.pretty_construct)
        if flat1072 is not None:
            assert flat1072 is not None
            self.write(flat1072)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1421 = _dollar_dollar.loop
            else:
                _t1421 = None
            deconstruct_result1070 = _t1421
            if deconstruct_result1070 is not None:
                assert deconstruct_result1070 is not None
                unwrapped1071 = deconstruct_result1070
                self.pretty_loop(unwrapped1071)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1422 = _dollar_dollar.instruction
                else:
                    _t1422 = None
                deconstruct_result1068 = _t1422
                if deconstruct_result1068 is not None:
                    assert deconstruct_result1068 is not None
                    unwrapped1069 = deconstruct_result1068
                    self.pretty_instruction(unwrapped1069)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1077 = self._try_flat(msg, self.pretty_loop)
        if flat1077 is not None:
            assert flat1077 is not None
            self.write(flat1077)
            return None
        else:
            _dollar_dollar = msg
            fields1073 = (_dollar_dollar.init, _dollar_dollar.body,)
            assert fields1073 is not None
            unwrapped_fields1074 = fields1073
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1075 = unwrapped_fields1074[0]
            self.pretty_init(field1075)
            self.newline()
            field1076 = unwrapped_fields1074[1]
            self.pretty_script(field1076)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1081 = self._try_flat(msg, self.pretty_init)
        if flat1081 is not None:
            assert flat1081 is not None
            self.write(flat1081)
            return None
        else:
            fields1078 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1078) == 0:
                self.newline()
                for i1080, elem1079 in enumerate(fields1078):
                    if (i1080 > 0):
                        self.newline()
                    self.pretty_instruction(elem1079)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1092 = self._try_flat(msg, self.pretty_instruction)
        if flat1092 is not None:
            assert flat1092 is not None
            self.write(flat1092)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1423 = _dollar_dollar.assign
            else:
                _t1423 = None
            deconstruct_result1090 = _t1423
            if deconstruct_result1090 is not None:
                assert deconstruct_result1090 is not None
                unwrapped1091 = deconstruct_result1090
                self.pretty_assign(unwrapped1091)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1424 = _dollar_dollar.upsert
                else:
                    _t1424 = None
                deconstruct_result1088 = _t1424
                if deconstruct_result1088 is not None:
                    assert deconstruct_result1088 is not None
                    unwrapped1089 = deconstruct_result1088
                    self.pretty_upsert(unwrapped1089)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1425 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1425 = None
                    deconstruct_result1086 = _t1425
                    if deconstruct_result1086 is not None:
                        assert deconstruct_result1086 is not None
                        unwrapped1087 = deconstruct_result1086
                        self.pretty_break(unwrapped1087)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1426 = _dollar_dollar.monoid_def
                        else:
                            _t1426 = None
                        deconstruct_result1084 = _t1426
                        if deconstruct_result1084 is not None:
                            assert deconstruct_result1084 is not None
                            unwrapped1085 = deconstruct_result1084
                            self.pretty_monoid_def(unwrapped1085)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1427 = _dollar_dollar.monus_def
                            else:
                                _t1427 = None
                            deconstruct_result1082 = _t1427
                            if deconstruct_result1082 is not None:
                                assert deconstruct_result1082 is not None
                                unwrapped1083 = deconstruct_result1082
                                self.pretty_monus_def(unwrapped1083)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1099 = self._try_flat(msg, self.pretty_assign)
        if flat1099 is not None:
            assert flat1099 is not None
            self.write(flat1099)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1428 = _dollar_dollar.attrs
            else:
                _t1428 = None
            fields1093 = (_dollar_dollar.name, _dollar_dollar.body, _t1428,)
            assert fields1093 is not None
            unwrapped_fields1094 = fields1093
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1095 = unwrapped_fields1094[0]
            self.pretty_relation_id(field1095)
            self.newline()
            field1096 = unwrapped_fields1094[1]
            self.pretty_abstraction(field1096)
            field1097 = unwrapped_fields1094[2]
            if field1097 is not None:
                self.newline()
                assert field1097 is not None
                opt_val1098 = field1097
                self.pretty_attrs(opt_val1098)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1106 = self._try_flat(msg, self.pretty_upsert)
        if flat1106 is not None:
            assert flat1106 is not None
            self.write(flat1106)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1429 = _dollar_dollar.attrs
            else:
                _t1429 = None
            fields1100 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1429,)
            assert fields1100 is not None
            unwrapped_fields1101 = fields1100
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1102 = unwrapped_fields1101[0]
            self.pretty_relation_id(field1102)
            self.newline()
            field1103 = unwrapped_fields1101[1]
            self.pretty_abstraction_with_arity(field1103)
            field1104 = unwrapped_fields1101[2]
            if field1104 is not None:
                self.newline()
                assert field1104 is not None
                opt_val1105 = field1104
                self.pretty_attrs(opt_val1105)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1111 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1111 is not None:
            assert flat1111 is not None
            self.write(flat1111)
            return None
        else:
            _dollar_dollar = msg
            _t1430 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1107 = (_t1430, _dollar_dollar[0].value,)
            assert fields1107 is not None
            unwrapped_fields1108 = fields1107
            self.write("(")
            self.indent()
            field1109 = unwrapped_fields1108[0]
            self.pretty_bindings(field1109)
            self.newline()
            field1110 = unwrapped_fields1108[1]
            self.pretty_formula(field1110)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1118 = self._try_flat(msg, self.pretty_break)
        if flat1118 is not None:
            assert flat1118 is not None
            self.write(flat1118)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1431 = _dollar_dollar.attrs
            else:
                _t1431 = None
            fields1112 = (_dollar_dollar.name, _dollar_dollar.body, _t1431,)
            assert fields1112 is not None
            unwrapped_fields1113 = fields1112
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1114 = unwrapped_fields1113[0]
            self.pretty_relation_id(field1114)
            self.newline()
            field1115 = unwrapped_fields1113[1]
            self.pretty_abstraction(field1115)
            field1116 = unwrapped_fields1113[2]
            if field1116 is not None:
                self.newline()
                assert field1116 is not None
                opt_val1117 = field1116
                self.pretty_attrs(opt_val1117)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1126 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1126 is not None:
            assert flat1126 is not None
            self.write(flat1126)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1432 = _dollar_dollar.attrs
            else:
                _t1432 = None
            fields1119 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1432,)
            assert fields1119 is not None
            unwrapped_fields1120 = fields1119
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1121 = unwrapped_fields1120[0]
            self.pretty_monoid(field1121)
            self.newline()
            field1122 = unwrapped_fields1120[1]
            self.pretty_relation_id(field1122)
            self.newline()
            field1123 = unwrapped_fields1120[2]
            self.pretty_abstraction_with_arity(field1123)
            field1124 = unwrapped_fields1120[3]
            if field1124 is not None:
                self.newline()
                assert field1124 is not None
                opt_val1125 = field1124
                self.pretty_attrs(opt_val1125)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1135 = self._try_flat(msg, self.pretty_monoid)
        if flat1135 is not None:
            assert flat1135 is not None
            self.write(flat1135)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1433 = _dollar_dollar.or_monoid
            else:
                _t1433 = None
            deconstruct_result1133 = _t1433
            if deconstruct_result1133 is not None:
                assert deconstruct_result1133 is not None
                unwrapped1134 = deconstruct_result1133
                self.pretty_or_monoid(unwrapped1134)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1434 = _dollar_dollar.min_monoid
                else:
                    _t1434 = None
                deconstruct_result1131 = _t1434
                if deconstruct_result1131 is not None:
                    assert deconstruct_result1131 is not None
                    unwrapped1132 = deconstruct_result1131
                    self.pretty_min_monoid(unwrapped1132)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1435 = _dollar_dollar.max_monoid
                    else:
                        _t1435 = None
                    deconstruct_result1129 = _t1435
                    if deconstruct_result1129 is not None:
                        assert deconstruct_result1129 is not None
                        unwrapped1130 = deconstruct_result1129
                        self.pretty_max_monoid(unwrapped1130)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1436 = _dollar_dollar.sum_monoid
                        else:
                            _t1436 = None
                        deconstruct_result1127 = _t1436
                        if deconstruct_result1127 is not None:
                            assert deconstruct_result1127 is not None
                            unwrapped1128 = deconstruct_result1127
                            self.pretty_sum_monoid(unwrapped1128)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1136 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1139 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1139 is not None:
            assert flat1139 is not None
            self.write(flat1139)
            return None
        else:
            _dollar_dollar = msg
            fields1137 = _dollar_dollar.type
            assert fields1137 is not None
            unwrapped_fields1138 = fields1137
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1138)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1142 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1142 is not None:
            assert flat1142 is not None
            self.write(flat1142)
            return None
        else:
            _dollar_dollar = msg
            fields1140 = _dollar_dollar.type
            assert fields1140 is not None
            unwrapped_fields1141 = fields1140
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1141)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1145 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1145 is not None:
            assert flat1145 is not None
            self.write(flat1145)
            return None
        else:
            _dollar_dollar = msg
            fields1143 = _dollar_dollar.type
            assert fields1143 is not None
            unwrapped_fields1144 = fields1143
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1144)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1153 = self._try_flat(msg, self.pretty_monus_def)
        if flat1153 is not None:
            assert flat1153 is not None
            self.write(flat1153)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1437 = _dollar_dollar.attrs
            else:
                _t1437 = None
            fields1146 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1437,)
            assert fields1146 is not None
            unwrapped_fields1147 = fields1146
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1148 = unwrapped_fields1147[0]
            self.pretty_monoid(field1148)
            self.newline()
            field1149 = unwrapped_fields1147[1]
            self.pretty_relation_id(field1149)
            self.newline()
            field1150 = unwrapped_fields1147[2]
            self.pretty_abstraction_with_arity(field1150)
            field1151 = unwrapped_fields1147[3]
            if field1151 is not None:
                self.newline()
                assert field1151 is not None
                opt_val1152 = field1151
                self.pretty_attrs(opt_val1152)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1160 = self._try_flat(msg, self.pretty_constraint)
        if flat1160 is not None:
            assert flat1160 is not None
            self.write(flat1160)
            return None
        else:
            _dollar_dollar = msg
            fields1154 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1154 is not None
            unwrapped_fields1155 = fields1154
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1156 = unwrapped_fields1155[0]
            self.pretty_relation_id(field1156)
            self.newline()
            field1157 = unwrapped_fields1155[1]
            self.pretty_abstraction(field1157)
            self.newline()
            field1158 = unwrapped_fields1155[2]
            self.pretty_functional_dependency_keys(field1158)
            self.newline()
            field1159 = unwrapped_fields1155[3]
            self.pretty_functional_dependency_values(field1159)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1164 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1164 is not None:
            assert flat1164 is not None
            self.write(flat1164)
            return None
        else:
            fields1161 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1161) == 0:
                self.newline()
                for i1163, elem1162 in enumerate(fields1161):
                    if (i1163 > 0):
                        self.newline()
                    self.pretty_var(elem1162)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1168 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1168 is not None:
            assert flat1168 is not None
            self.write(flat1168)
            return None
        else:
            fields1165 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1165) == 0:
                self.newline()
                for i1167, elem1166 in enumerate(fields1165):
                    if (i1167 > 0):
                        self.newline()
                    self.pretty_var(elem1166)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1175 = self._try_flat(msg, self.pretty_data)
        if flat1175 is not None:
            assert flat1175 is not None
            self.write(flat1175)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1438 = _dollar_dollar.edb
            else:
                _t1438 = None
            deconstruct_result1173 = _t1438
            if deconstruct_result1173 is not None:
                assert deconstruct_result1173 is not None
                unwrapped1174 = deconstruct_result1173
                self.pretty_edb(unwrapped1174)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1439 = _dollar_dollar.betree_relation
                else:
                    _t1439 = None
                deconstruct_result1171 = _t1439
                if deconstruct_result1171 is not None:
                    assert deconstruct_result1171 is not None
                    unwrapped1172 = deconstruct_result1171
                    self.pretty_betree_relation(unwrapped1172)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1440 = _dollar_dollar.csv_data
                    else:
                        _t1440 = None
                    deconstruct_result1169 = _t1440
                    if deconstruct_result1169 is not None:
                        assert deconstruct_result1169 is not None
                        unwrapped1170 = deconstruct_result1169
                        self.pretty_csv_data(unwrapped1170)
                    else:
                        raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1181 = self._try_flat(msg, self.pretty_edb)
        if flat1181 is not None:
            assert flat1181 is not None
            self.write(flat1181)
            return None
        else:
            _dollar_dollar = msg
            fields1176 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1176 is not None
            unwrapped_fields1177 = fields1176
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1178 = unwrapped_fields1177[0]
            self.pretty_relation_id(field1178)
            self.newline()
            field1179 = unwrapped_fields1177[1]
            self.pretty_edb_path(field1179)
            self.newline()
            field1180 = unwrapped_fields1177[2]
            self.pretty_edb_types(field1180)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1185 = self._try_flat(msg, self.pretty_edb_path)
        if flat1185 is not None:
            assert flat1185 is not None
            self.write(flat1185)
            return None
        else:
            fields1182 = msg
            self.write("[")
            self.indent()
            for i1184, elem1183 in enumerate(fields1182):
                if (i1184 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1183))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1189 = self._try_flat(msg, self.pretty_edb_types)
        if flat1189 is not None:
            assert flat1189 is not None
            self.write(flat1189)
            return None
        else:
            fields1186 = msg
            self.write("[")
            self.indent()
            for i1188, elem1187 in enumerate(fields1186):
                if (i1188 > 0):
                    self.newline()
                self.pretty_type(elem1187)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1194 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1194 is not None:
            assert flat1194 is not None
            self.write(flat1194)
            return None
        else:
            _dollar_dollar = msg
            fields1190 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1190 is not None
            unwrapped_fields1191 = fields1190
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1192 = unwrapped_fields1191[0]
            self.pretty_relation_id(field1192)
            self.newline()
            field1193 = unwrapped_fields1191[1]
            self.pretty_betree_info(field1193)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1200 = self._try_flat(msg, self.pretty_betree_info)
        if flat1200 is not None:
            assert flat1200 is not None
            self.write(flat1200)
            return None
        else:
            _dollar_dollar = msg
            _t1441 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1195 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1441,)
            assert fields1195 is not None
            unwrapped_fields1196 = fields1195
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1197 = unwrapped_fields1196[0]
            self.pretty_betree_info_key_types(field1197)
            self.newline()
            field1198 = unwrapped_fields1196[1]
            self.pretty_betree_info_value_types(field1198)
            self.newline()
            field1199 = unwrapped_fields1196[2]
            self.pretty_config_dict(field1199)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1204 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1204 is not None:
            assert flat1204 is not None
            self.write(flat1204)
            return None
        else:
            fields1201 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1201) == 0:
                self.newline()
                for i1203, elem1202 in enumerate(fields1201):
                    if (i1203 > 0):
                        self.newline()
                    self.pretty_type(elem1202)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1208 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1208 is not None:
            assert flat1208 is not None
            self.write(flat1208)
            return None
        else:
            fields1205 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1205) == 0:
                self.newline()
                for i1207, elem1206 in enumerate(fields1205):
                    if (i1207 > 0):
                        self.newline()
                    self.pretty_type(elem1206)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1215 = self._try_flat(msg, self.pretty_csv_data)
        if flat1215 is not None:
            assert flat1215 is not None
            self.write(flat1215)
            return None
        else:
            _dollar_dollar = msg
            fields1209 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1209 is not None
            unwrapped_fields1210 = fields1209
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1211 = unwrapped_fields1210[0]
            self.pretty_csvlocator(field1211)
            self.newline()
            field1212 = unwrapped_fields1210[1]
            self.pretty_csv_config(field1212)
            self.newline()
            field1213 = unwrapped_fields1210[2]
            self.pretty_gnf_columns(field1213)
            self.newline()
            field1214 = unwrapped_fields1210[3]
            self.pretty_csv_asof(field1214)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1222 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1222 is not None:
            assert flat1222 is not None
            self.write(flat1222)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1442 = _dollar_dollar.paths
            else:
                _t1442 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1443 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1443 = None
            fields1216 = (_t1442, _t1443,)
            assert fields1216 is not None
            unwrapped_fields1217 = fields1216
            self.write("(csv_locator")
            self.indent_sexp()
            field1218 = unwrapped_fields1217[0]
            if field1218 is not None:
                self.newline()
                assert field1218 is not None
                opt_val1219 = field1218
                self.pretty_csv_locator_paths(opt_val1219)
            field1220 = unwrapped_fields1217[1]
            if field1220 is not None:
                self.newline()
                assert field1220 is not None
                opt_val1221 = field1220
                self.pretty_csv_locator_inline_data(opt_val1221)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1226 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1226 is not None:
            assert flat1226 is not None
            self.write(flat1226)
            return None
        else:
            fields1223 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1223) == 0:
                self.newline()
                for i1225, elem1224 in enumerate(fields1223):
                    if (i1225 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1224))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1228 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1228 is not None:
            assert flat1228 is not None
            self.write(flat1228)
            return None
        else:
            fields1227 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1227))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1231 = self._try_flat(msg, self.pretty_csv_config)
        if flat1231 is not None:
            assert flat1231 is not None
            self.write(flat1231)
            return None
        else:
            _dollar_dollar = msg
            _t1444 = self.deconstruct_csv_config(_dollar_dollar)
            fields1229 = _t1444
            assert fields1229 is not None
            unwrapped_fields1230 = fields1229
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1230)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1235 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1235 is not None:
            assert flat1235 is not None
            self.write(flat1235)
            return None
        else:
            fields1232 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1232) == 0:
                self.newline()
                for i1234, elem1233 in enumerate(fields1232):
                    if (i1234 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1233)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1244 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1244 is not None:
            assert flat1244 is not None
            self.write(flat1244)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1445 = _dollar_dollar.target_id
            else:
                _t1445 = None
            fields1236 = (_dollar_dollar.column_path, _t1445, _dollar_dollar.types,)
            assert fields1236 is not None
            unwrapped_fields1237 = fields1236
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1238 = unwrapped_fields1237[0]
            self.pretty_gnf_column_path(field1238)
            field1239 = unwrapped_fields1237[1]
            if field1239 is not None:
                self.newline()
                assert field1239 is not None
                opt_val1240 = field1239
                self.pretty_relation_id(opt_val1240)
            self.newline()
            self.write("[")
            field1241 = unwrapped_fields1237[2]
            for i1243, elem1242 in enumerate(field1241):
                if (i1243 > 0):
                    self.newline()
                self.pretty_type(elem1242)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1251 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1251 is not None:
            assert flat1251 is not None
            self.write(flat1251)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1446 = _dollar_dollar[0]
            else:
                _t1446 = None
            deconstruct_result1249 = _t1446
            if deconstruct_result1249 is not None:
                assert deconstruct_result1249 is not None
                unwrapped1250 = deconstruct_result1249
                self.write(self.format_string_value(unwrapped1250))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1447 = _dollar_dollar
                else:
                    _t1447 = None
                deconstruct_result1245 = _t1447
                if deconstruct_result1245 is not None:
                    assert deconstruct_result1245 is not None
                    unwrapped1246 = deconstruct_result1245
                    self.write("[")
                    self.indent()
                    for i1248, elem1247 in enumerate(unwrapped1246):
                        if (i1248 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1247))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1253 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1253 is not None:
            assert flat1253 is not None
            self.write(flat1253)
            return None
        else:
            fields1252 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1252))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1256 = self._try_flat(msg, self.pretty_undefine)
        if flat1256 is not None:
            assert flat1256 is not None
            self.write(flat1256)
            return None
        else:
            _dollar_dollar = msg
            fields1254 = _dollar_dollar.fragment_id
            assert fields1254 is not None
            unwrapped_fields1255 = fields1254
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1255)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1261 = self._try_flat(msg, self.pretty_context)
        if flat1261 is not None:
            assert flat1261 is not None
            self.write(flat1261)
            return None
        else:
            _dollar_dollar = msg
            fields1257 = _dollar_dollar.relations
            assert fields1257 is not None
            unwrapped_fields1258 = fields1257
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1258) == 0:
                self.newline()
                for i1260, elem1259 in enumerate(unwrapped_fields1258):
                    if (i1260 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1259)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1266 = self._try_flat(msg, self.pretty_snapshot)
        if flat1266 is not None:
            assert flat1266 is not None
            self.write(flat1266)
            return None
        else:
            _dollar_dollar = msg
            fields1262 = _dollar_dollar.mappings
            assert fields1262 is not None
            unwrapped_fields1263 = fields1262
            self.write("(snapshot")
            self.indent_sexp()
            if not len(unwrapped_fields1263) == 0:
                self.newline()
                for i1265, elem1264 in enumerate(unwrapped_fields1263):
                    if (i1265 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1264)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1271 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1271 is not None:
            assert flat1271 is not None
            self.write(flat1271)
            return None
        else:
            _dollar_dollar = msg
            fields1267 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1267 is not None
            unwrapped_fields1268 = fields1267
            field1269 = unwrapped_fields1268[0]
            self.pretty_edb_path(field1269)
            self.write(" ")
            field1270 = unwrapped_fields1268[1]
            self.pretty_relation_id(field1270)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1275 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1275 is not None:
            assert flat1275 is not None
            self.write(flat1275)
            return None
        else:
            fields1272 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1272) == 0:
                self.newline()
                for i1274, elem1273 in enumerate(fields1272):
                    if (i1274 > 0):
                        self.newline()
                    self.pretty_read(elem1273)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1286 = self._try_flat(msg, self.pretty_read)
        if flat1286 is not None:
            assert flat1286 is not None
            self.write(flat1286)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1448 = _dollar_dollar.demand
            else:
                _t1448 = None
            deconstruct_result1284 = _t1448
            if deconstruct_result1284 is not None:
                assert deconstruct_result1284 is not None
                unwrapped1285 = deconstruct_result1284
                self.pretty_demand(unwrapped1285)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1449 = _dollar_dollar.output
                else:
                    _t1449 = None
                deconstruct_result1282 = _t1449
                if deconstruct_result1282 is not None:
                    assert deconstruct_result1282 is not None
                    unwrapped1283 = deconstruct_result1282
                    self.pretty_output(unwrapped1283)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1450 = _dollar_dollar.what_if
                    else:
                        _t1450 = None
                    deconstruct_result1280 = _t1450
                    if deconstruct_result1280 is not None:
                        assert deconstruct_result1280 is not None
                        unwrapped1281 = deconstruct_result1280
                        self.pretty_what_if(unwrapped1281)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1451 = _dollar_dollar.abort
                        else:
                            _t1451 = None
                        deconstruct_result1278 = _t1451
                        if deconstruct_result1278 is not None:
                            assert deconstruct_result1278 is not None
                            unwrapped1279 = deconstruct_result1278
                            self.pretty_abort(unwrapped1279)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1452 = _dollar_dollar.export
                            else:
                                _t1452 = None
                            deconstruct_result1276 = _t1452
                            if deconstruct_result1276 is not None:
                                assert deconstruct_result1276 is not None
                                unwrapped1277 = deconstruct_result1276
                                self.pretty_export(unwrapped1277)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1289 = self._try_flat(msg, self.pretty_demand)
        if flat1289 is not None:
            assert flat1289 is not None
            self.write(flat1289)
            return None
        else:
            _dollar_dollar = msg
            fields1287 = _dollar_dollar.relation_id
            assert fields1287 is not None
            unwrapped_fields1288 = fields1287
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1288)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1294 = self._try_flat(msg, self.pretty_output)
        if flat1294 is not None:
            assert flat1294 is not None
            self.write(flat1294)
            return None
        else:
            _dollar_dollar = msg
            fields1290 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1290 is not None
            unwrapped_fields1291 = fields1290
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1292 = unwrapped_fields1291[0]
            self.pretty_name(field1292)
            self.newline()
            field1293 = unwrapped_fields1291[1]
            self.pretty_relation_id(field1293)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1299 = self._try_flat(msg, self.pretty_what_if)
        if flat1299 is not None:
            assert flat1299 is not None
            self.write(flat1299)
            return None
        else:
            _dollar_dollar = msg
            fields1295 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1295 is not None
            unwrapped_fields1296 = fields1295
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1297 = unwrapped_fields1296[0]
            self.pretty_name(field1297)
            self.newline()
            field1298 = unwrapped_fields1296[1]
            self.pretty_epoch(field1298)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1305 = self._try_flat(msg, self.pretty_abort)
        if flat1305 is not None:
            assert flat1305 is not None
            self.write(flat1305)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1453 = _dollar_dollar.name
            else:
                _t1453 = None
            fields1300 = (_t1453, _dollar_dollar.relation_id,)
            assert fields1300 is not None
            unwrapped_fields1301 = fields1300
            self.write("(abort")
            self.indent_sexp()
            field1302 = unwrapped_fields1301[0]
            if field1302 is not None:
                self.newline()
                assert field1302 is not None
                opt_val1303 = field1302
                self.pretty_name(opt_val1303)
            self.newline()
            field1304 = unwrapped_fields1301[1]
            self.pretty_relation_id(field1304)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1308 = self._try_flat(msg, self.pretty_export)
        if flat1308 is not None:
            assert flat1308 is not None
            self.write(flat1308)
            return None
        else:
            _dollar_dollar = msg
            fields1306 = _dollar_dollar.csv_config
            assert fields1306 is not None
            unwrapped_fields1307 = fields1306
            self.write("(export")
            self.indent_sexp()
            self.newline()
            self.pretty_export_csv_config(unwrapped_fields1307)
            self.dedent()
            self.write(")")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1319 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1319 is not None:
            assert flat1319 is not None
            self.write(flat1319)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1454 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1454 = None
            deconstruct_result1314 = _t1454
            if deconstruct_result1314 is not None:
                assert deconstruct_result1314 is not None
                unwrapped1315 = deconstruct_result1314
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1316 = unwrapped1315[0]
                self.pretty_export_csv_path(field1316)
                self.newline()
                field1317 = unwrapped1315[1]
                self.pretty_export_csv_source(field1317)
                self.newline()
                field1318 = unwrapped1315[2]
                self.pretty_csv_config(field1318)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1456 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1455 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1456,)
                else:
                    _t1455 = None
                deconstruct_result1309 = _t1455
                if deconstruct_result1309 is not None:
                    assert deconstruct_result1309 is not None
                    unwrapped1310 = deconstruct_result1309
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1311 = unwrapped1310[0]
                    self.pretty_export_csv_path(field1311)
                    self.newline()
                    field1312 = unwrapped1310[1]
                    self.pretty_export_csv_columns_list(field1312)
                    self.newline()
                    field1313 = unwrapped1310[2]
                    self.pretty_config_dict(field1313)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1321 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1321 is not None:
            assert flat1321 is not None
            self.write(flat1321)
            return None
        else:
            fields1320 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1320))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1328 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1328 is not None:
            assert flat1328 is not None
            self.write(flat1328)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1457 = _dollar_dollar.gnf_columns.columns
            else:
                _t1457 = None
            deconstruct_result1324 = _t1457
            if deconstruct_result1324 is not None:
                assert deconstruct_result1324 is not None
                unwrapped1325 = deconstruct_result1324
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1325) == 0:
                    self.newline()
                    for i1327, elem1326 in enumerate(unwrapped1325):
                        if (i1327 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1326)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1458 = _dollar_dollar.table_def
                else:
                    _t1458 = None
                deconstruct_result1322 = _t1458
                if deconstruct_result1322 is not None:
                    assert deconstruct_result1322 is not None
                    unwrapped1323 = deconstruct_result1322
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1323)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1333 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1333 is not None:
            assert flat1333 is not None
            self.write(flat1333)
            return None
        else:
            _dollar_dollar = msg
            fields1329 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1329 is not None
            unwrapped_fields1330 = fields1329
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1331 = unwrapped_fields1330[0]
            self.write(self.format_string_value(field1331))
            self.newline()
            field1332 = unwrapped_fields1330[1]
            self.pretty_relation_id(field1332)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1337 = self._try_flat(msg, self.pretty_export_csv_columns_list)
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
                    self.pretty_export_csv_column(elem1335)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1497 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1497)
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
