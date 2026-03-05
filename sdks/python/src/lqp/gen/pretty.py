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
        _t1447 = logic_pb2.Value(int_value=int(v))
        return _t1447

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1448 = logic_pb2.Value(int_value=v)
        return _t1448

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1449 = logic_pb2.Value(float_value=v)
        return _t1449

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1450 = logic_pb2.Value(string_value=v)
        return _t1450

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1451 = logic_pb2.Value(boolean_value=v)
        return _t1451

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1452 = logic_pb2.Value(uint128_value=v)
        return _t1452

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1453 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1453,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1454 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1454,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1455 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1455,))
        _t1456 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1456,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1457 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1457,))
        _t1458 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1458,))
        if msg.new_line != "":
            _t1459 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1459,))
        _t1460 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1460,))
        _t1461 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1461,))
        _t1462 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1462,))
        if msg.comment != "":
            _t1463 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1463,))
        for missing_string in msg.missing_strings:
            _t1464 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1464,))
        _t1465 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1465,))
        _t1466 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1466,))
        _t1467 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1467,))
        if msg.partition_size_mb != 0:
            _t1468 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1468,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1469 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1469,))
        _t1470 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1470,))
        _t1471 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1471,))
        _t1472 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1472,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1473 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1473,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1474 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1474,))
        _t1475 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1475,))
        _t1476 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1476,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1477 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1477,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1478 = self._make_value_string(msg.compression)
            result.append(("compression", _t1478,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1479 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1479,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1480 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1480,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1481 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1481,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1482 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1482,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1483 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1483,))
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
            _t1484 = None
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
        flat673 = self._try_flat(msg, self.pretty_transaction)
        if flat673 is not None:
            assert flat673 is not None
            self.write(flat673)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1328 = _dollar_dollar.configure
            else:
                _t1328 = None
            if _dollar_dollar.HasField("sync"):
                _t1329 = _dollar_dollar.sync
            else:
                _t1329 = None
            fields664 = (_t1328, _t1329, _dollar_dollar.epochs,)
            assert fields664 is not None
            unwrapped_fields665 = fields664
            self.write("(transaction")
            self.indent_sexp()
            field666 = unwrapped_fields665[0]
            if field666 is not None:
                self.newline()
                assert field666 is not None
                opt_val667 = field666
                self.pretty_configure(opt_val667)
            field668 = unwrapped_fields665[1]
            if field668 is not None:
                self.newline()
                assert field668 is not None
                opt_val669 = field668
                self.pretty_sync(opt_val669)
            field670 = unwrapped_fields665[2]
            if not len(field670) == 0:
                self.newline()
                for i672, elem671 in enumerate(field670):
                    if (i672 > 0):
                        self.newline()
                    self.pretty_epoch(elem671)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat676 = self._try_flat(msg, self.pretty_configure)
        if flat676 is not None:
            assert flat676 is not None
            self.write(flat676)
            return None
        else:
            _dollar_dollar = msg
            _t1330 = self.deconstruct_configure(_dollar_dollar)
            fields674 = _t1330
            assert fields674 is not None
            unwrapped_fields675 = fields674
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields675)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat680 = self._try_flat(msg, self.pretty_config_dict)
        if flat680 is not None:
            assert flat680 is not None
            self.write(flat680)
            return None
        else:
            fields677 = msg
            self.write("{")
            self.indent()
            if not len(fields677) == 0:
                self.newline()
                for i679, elem678 in enumerate(fields677):
                    if (i679 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem678)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat685 = self._try_flat(msg, self.pretty_config_key_value)
        if flat685 is not None:
            assert flat685 is not None
            self.write(flat685)
            return None
        else:
            _dollar_dollar = msg
            fields681 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields681 is not None
            unwrapped_fields682 = fields681
            self.write(":")
            field683 = unwrapped_fields682[0]
            self.write(field683)
            self.write(" ")
            field684 = unwrapped_fields682[1]
            self.pretty_value(field684)

    def pretty_value(self, msg: logic_pb2.Value):
        flat709 = self._try_flat(msg, self.pretty_value)
        if flat709 is not None:
            assert flat709 is not None
            self.write(flat709)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1331 = _dollar_dollar.date_value
            else:
                _t1331 = None
            deconstruct_result707 = _t1331
            if deconstruct_result707 is not None:
                assert deconstruct_result707 is not None
                unwrapped708 = deconstruct_result707
                self.pretty_date(unwrapped708)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1332 = _dollar_dollar.datetime_value
                else:
                    _t1332 = None
                deconstruct_result705 = _t1332
                if deconstruct_result705 is not None:
                    assert deconstruct_result705 is not None
                    unwrapped706 = deconstruct_result705
                    self.pretty_datetime(unwrapped706)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1333 = _dollar_dollar.string_value
                    else:
                        _t1333 = None
                    deconstruct_result703 = _t1333
                    if deconstruct_result703 is not None:
                        assert deconstruct_result703 is not None
                        unwrapped704 = deconstruct_result703
                        self.write(self.format_string_value(unwrapped704))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int_value"):
                            _t1334 = _dollar_dollar.int_value
                        else:
                            _t1334 = None
                        deconstruct_result701 = _t1334
                        if deconstruct_result701 is not None:
                            assert deconstruct_result701 is not None
                            unwrapped702 = deconstruct_result701
                            self.write(str(unwrapped702))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("float_value"):
                                _t1335 = _dollar_dollar.float_value
                            else:
                                _t1335 = None
                            deconstruct_result699 = _t1335
                            if deconstruct_result699 is not None:
                                assert deconstruct_result699 is not None
                                unwrapped700 = deconstruct_result699
                                self.write(str(unwrapped700))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("uint128_value"):
                                    _t1336 = _dollar_dollar.uint128_value
                                else:
                                    _t1336 = None
                                deconstruct_result697 = _t1336
                                if deconstruct_result697 is not None:
                                    assert deconstruct_result697 is not None
                                    unwrapped698 = deconstruct_result697
                                    self.write(self.format_uint128(unwrapped698))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("int128_value"):
                                        _t1337 = _dollar_dollar.int128_value
                                    else:
                                        _t1337 = None
                                    deconstruct_result695 = _t1337
                                    if deconstruct_result695 is not None:
                                        assert deconstruct_result695 is not None
                                        unwrapped696 = deconstruct_result695
                                        self.write(self.format_int128(unwrapped696))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("decimal_value"):
                                            _t1338 = _dollar_dollar.decimal_value
                                        else:
                                            _t1338 = None
                                        deconstruct_result693 = _t1338
                                        if deconstruct_result693 is not None:
                                            assert deconstruct_result693 is not None
                                            unwrapped694 = deconstruct_result693
                                            self.write(self.format_decimal(unwrapped694))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("boolean_value"):
                                                _t1339 = _dollar_dollar.boolean_value
                                            else:
                                                _t1339 = None
                                            deconstruct_result691 = _t1339
                                            if deconstruct_result691 is not None:
                                                assert deconstruct_result691 is not None
                                                unwrapped692 = deconstruct_result691
                                                self.pretty_boolean_value(unwrapped692)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("int32_value"):
                                                    _t1340 = _dollar_dollar.int32_value
                                                else:
                                                    _t1340 = None
                                                deconstruct_result689 = _t1340
                                                if deconstruct_result689 is not None:
                                                    assert deconstruct_result689 is not None
                                                    unwrapped690 = deconstruct_result689
                                                    self.write((str(unwrapped690) + 'i32'))
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("float32_value"):
                                                        _t1341 = _dollar_dollar.float32_value
                                                    else:
                                                        _t1341 = None
                                                    deconstruct_result687 = _t1341
                                                    if deconstruct_result687 is not None:
                                                        assert deconstruct_result687 is not None
                                                        unwrapped688 = deconstruct_result687
                                                        self.write((self.format_float32_value(unwrapped688) + 'f32'))
                                                    else:
                                                        fields686 = msg
                                                        self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat715 = self._try_flat(msg, self.pretty_date)
        if flat715 is not None:
            assert flat715 is not None
            self.write(flat715)
            return None
        else:
            _dollar_dollar = msg
            fields710 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields710 is not None
            unwrapped_fields711 = fields710
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field712 = unwrapped_fields711[0]
            self.write(str(field712))
            self.newline()
            field713 = unwrapped_fields711[1]
            self.write(str(field713))
            self.newline()
            field714 = unwrapped_fields711[2]
            self.write(str(field714))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat726 = self._try_flat(msg, self.pretty_datetime)
        if flat726 is not None:
            assert flat726 is not None
            self.write(flat726)
            return None
        else:
            _dollar_dollar = msg
            fields716 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields716 is not None
            unwrapped_fields717 = fields716
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field718 = unwrapped_fields717[0]
            self.write(str(field718))
            self.newline()
            field719 = unwrapped_fields717[1]
            self.write(str(field719))
            self.newline()
            field720 = unwrapped_fields717[2]
            self.write(str(field720))
            self.newline()
            field721 = unwrapped_fields717[3]
            self.write(str(field721))
            self.newline()
            field722 = unwrapped_fields717[4]
            self.write(str(field722))
            self.newline()
            field723 = unwrapped_fields717[5]
            self.write(str(field723))
            field724 = unwrapped_fields717[6]
            if field724 is not None:
                self.newline()
                assert field724 is not None
                opt_val725 = field724
                self.write(str(opt_val725))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1342 = ()
        else:
            _t1342 = None
        deconstruct_result729 = _t1342
        if deconstruct_result729 is not None:
            assert deconstruct_result729 is not None
            unwrapped730 = deconstruct_result729
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1343 = ()
            else:
                _t1343 = None
            deconstruct_result727 = _t1343
            if deconstruct_result727 is not None:
                assert deconstruct_result727 is not None
                unwrapped728 = deconstruct_result727
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat735 = self._try_flat(msg, self.pretty_sync)
        if flat735 is not None:
            assert flat735 is not None
            self.write(flat735)
            return None
        else:
            _dollar_dollar = msg
            fields731 = _dollar_dollar.fragments
            assert fields731 is not None
            unwrapped_fields732 = fields731
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields732) == 0:
                self.newline()
                for i734, elem733 in enumerate(unwrapped_fields732):
                    if (i734 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem733)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat738 = self._try_flat(msg, self.pretty_fragment_id)
        if flat738 is not None:
            assert flat738 is not None
            self.write(flat738)
            return None
        else:
            _dollar_dollar = msg
            fields736 = self.fragment_id_to_string(_dollar_dollar)
            assert fields736 is not None
            unwrapped_fields737 = fields736
            self.write(":")
            self.write(unwrapped_fields737)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat745 = self._try_flat(msg, self.pretty_epoch)
        if flat745 is not None:
            assert flat745 is not None
            self.write(flat745)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1344 = _dollar_dollar.writes
            else:
                _t1344 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1345 = _dollar_dollar.reads
            else:
                _t1345 = None
            fields739 = (_t1344, _t1345,)
            assert fields739 is not None
            unwrapped_fields740 = fields739
            self.write("(epoch")
            self.indent_sexp()
            field741 = unwrapped_fields740[0]
            if field741 is not None:
                self.newline()
                assert field741 is not None
                opt_val742 = field741
                self.pretty_epoch_writes(opt_val742)
            field743 = unwrapped_fields740[1]
            if field743 is not None:
                self.newline()
                assert field743 is not None
                opt_val744 = field743
                self.pretty_epoch_reads(opt_val744)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat749 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat749 is not None:
            assert flat749 is not None
            self.write(flat749)
            return None
        else:
            fields746 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields746) == 0:
                self.newline()
                for i748, elem747 in enumerate(fields746):
                    if (i748 > 0):
                        self.newline()
                    self.pretty_write(elem747)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat758 = self._try_flat(msg, self.pretty_write)
        if flat758 is not None:
            assert flat758 is not None
            self.write(flat758)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1346 = _dollar_dollar.define
            else:
                _t1346 = None
            deconstruct_result756 = _t1346
            if deconstruct_result756 is not None:
                assert deconstruct_result756 is not None
                unwrapped757 = deconstruct_result756
                self.pretty_define(unwrapped757)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1347 = _dollar_dollar.undefine
                else:
                    _t1347 = None
                deconstruct_result754 = _t1347
                if deconstruct_result754 is not None:
                    assert deconstruct_result754 is not None
                    unwrapped755 = deconstruct_result754
                    self.pretty_undefine(unwrapped755)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1348 = _dollar_dollar.context
                    else:
                        _t1348 = None
                    deconstruct_result752 = _t1348
                    if deconstruct_result752 is not None:
                        assert deconstruct_result752 is not None
                        unwrapped753 = deconstruct_result752
                        self.pretty_context(unwrapped753)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1349 = _dollar_dollar.snapshot
                        else:
                            _t1349 = None
                        deconstruct_result750 = _t1349
                        if deconstruct_result750 is not None:
                            assert deconstruct_result750 is not None
                            unwrapped751 = deconstruct_result750
                            self.pretty_snapshot(unwrapped751)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat761 = self._try_flat(msg, self.pretty_define)
        if flat761 is not None:
            assert flat761 is not None
            self.write(flat761)
            return None
        else:
            _dollar_dollar = msg
            fields759 = _dollar_dollar.fragment
            assert fields759 is not None
            unwrapped_fields760 = fields759
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields760)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat768 = self._try_flat(msg, self.pretty_fragment)
        if flat768 is not None:
            assert flat768 is not None
            self.write(flat768)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields762 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields762 is not None
            unwrapped_fields763 = fields762
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field764 = unwrapped_fields763[0]
            self.pretty_new_fragment_id(field764)
            field765 = unwrapped_fields763[1]
            if not len(field765) == 0:
                self.newline()
                for i767, elem766 in enumerate(field765):
                    if (i767 > 0):
                        self.newline()
                    self.pretty_declaration(elem766)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat770 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat770 is not None:
            assert flat770 is not None
            self.write(flat770)
            return None
        else:
            fields769 = msg
            self.pretty_fragment_id(fields769)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat779 = self._try_flat(msg, self.pretty_declaration)
        if flat779 is not None:
            assert flat779 is not None
            self.write(flat779)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1350 = getattr(_dollar_dollar, 'def')
            else:
                _t1350 = None
            deconstruct_result777 = _t1350
            if deconstruct_result777 is not None:
                assert deconstruct_result777 is not None
                unwrapped778 = deconstruct_result777
                self.pretty_def(unwrapped778)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1351 = _dollar_dollar.algorithm
                else:
                    _t1351 = None
                deconstruct_result775 = _t1351
                if deconstruct_result775 is not None:
                    assert deconstruct_result775 is not None
                    unwrapped776 = deconstruct_result775
                    self.pretty_algorithm(unwrapped776)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1352 = _dollar_dollar.constraint
                    else:
                        _t1352 = None
                    deconstruct_result773 = _t1352
                    if deconstruct_result773 is not None:
                        assert deconstruct_result773 is not None
                        unwrapped774 = deconstruct_result773
                        self.pretty_constraint(unwrapped774)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1353 = _dollar_dollar.data
                        else:
                            _t1353 = None
                        deconstruct_result771 = _t1353
                        if deconstruct_result771 is not None:
                            assert deconstruct_result771 is not None
                            unwrapped772 = deconstruct_result771
                            self.pretty_data(unwrapped772)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat786 = self._try_flat(msg, self.pretty_def)
        if flat786 is not None:
            assert flat786 is not None
            self.write(flat786)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1354 = _dollar_dollar.attrs
            else:
                _t1354 = None
            fields780 = (_dollar_dollar.name, _dollar_dollar.body, _t1354,)
            assert fields780 is not None
            unwrapped_fields781 = fields780
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field782 = unwrapped_fields781[0]
            self.pretty_relation_id(field782)
            self.newline()
            field783 = unwrapped_fields781[1]
            self.pretty_abstraction(field783)
            field784 = unwrapped_fields781[2]
            if field784 is not None:
                self.newline()
                assert field784 is not None
                opt_val785 = field784
                self.pretty_attrs(opt_val785)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat791 = self._try_flat(msg, self.pretty_relation_id)
        if flat791 is not None:
            assert flat791 is not None
            self.write(flat791)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1356 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1355 = _t1356
            else:
                _t1355 = None
            deconstruct_result789 = _t1355
            if deconstruct_result789 is not None:
                assert deconstruct_result789 is not None
                unwrapped790 = deconstruct_result789
                self.write(":")
                self.write(unwrapped790)
            else:
                _dollar_dollar = msg
                _t1357 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result787 = _t1357
                if deconstruct_result787 is not None:
                    assert deconstruct_result787 is not None
                    unwrapped788 = deconstruct_result787
                    self.write(self.format_uint128(unwrapped788))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat796 = self._try_flat(msg, self.pretty_abstraction)
        if flat796 is not None:
            assert flat796 is not None
            self.write(flat796)
            return None
        else:
            _dollar_dollar = msg
            _t1358 = self.deconstruct_bindings(_dollar_dollar)
            fields792 = (_t1358, _dollar_dollar.value,)
            assert fields792 is not None
            unwrapped_fields793 = fields792
            self.write("(")
            self.indent()
            field794 = unwrapped_fields793[0]
            self.pretty_bindings(field794)
            self.newline()
            field795 = unwrapped_fields793[1]
            self.pretty_formula(field795)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat804 = self._try_flat(msg, self.pretty_bindings)
        if flat804 is not None:
            assert flat804 is not None
            self.write(flat804)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1359 = _dollar_dollar[1]
            else:
                _t1359 = None
            fields797 = (_dollar_dollar[0], _t1359,)
            assert fields797 is not None
            unwrapped_fields798 = fields797
            self.write("[")
            self.indent()
            field799 = unwrapped_fields798[0]
            for i801, elem800 in enumerate(field799):
                if (i801 > 0):
                    self.newline()
                self.pretty_binding(elem800)
            field802 = unwrapped_fields798[1]
            if field802 is not None:
                self.newline()
                assert field802 is not None
                opt_val803 = field802
                self.pretty_value_bindings(opt_val803)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat809 = self._try_flat(msg, self.pretty_binding)
        if flat809 is not None:
            assert flat809 is not None
            self.write(flat809)
            return None
        else:
            _dollar_dollar = msg
            fields805 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields805 is not None
            unwrapped_fields806 = fields805
            field807 = unwrapped_fields806[0]
            self.write(field807)
            self.write("::")
            field808 = unwrapped_fields806[1]
            self.pretty_type(field808)

    def pretty_type(self, msg: logic_pb2.Type):
        flat836 = self._try_flat(msg, self.pretty_type)
        if flat836 is not None:
            assert flat836 is not None
            self.write(flat836)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1360 = _dollar_dollar.unspecified_type
            else:
                _t1360 = None
            deconstruct_result834 = _t1360
            if deconstruct_result834 is not None:
                assert deconstruct_result834 is not None
                unwrapped835 = deconstruct_result834
                self.pretty_unspecified_type(unwrapped835)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1361 = _dollar_dollar.string_type
                else:
                    _t1361 = None
                deconstruct_result832 = _t1361
                if deconstruct_result832 is not None:
                    assert deconstruct_result832 is not None
                    unwrapped833 = deconstruct_result832
                    self.pretty_string_type(unwrapped833)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1362 = _dollar_dollar.int_type
                    else:
                        _t1362 = None
                    deconstruct_result830 = _t1362
                    if deconstruct_result830 is not None:
                        assert deconstruct_result830 is not None
                        unwrapped831 = deconstruct_result830
                        self.pretty_int_type(unwrapped831)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1363 = _dollar_dollar.float_type
                        else:
                            _t1363 = None
                        deconstruct_result828 = _t1363
                        if deconstruct_result828 is not None:
                            assert deconstruct_result828 is not None
                            unwrapped829 = deconstruct_result828
                            self.pretty_float_type(unwrapped829)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1364 = _dollar_dollar.uint128_type
                            else:
                                _t1364 = None
                            deconstruct_result826 = _t1364
                            if deconstruct_result826 is not None:
                                assert deconstruct_result826 is not None
                                unwrapped827 = deconstruct_result826
                                self.pretty_uint128_type(unwrapped827)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1365 = _dollar_dollar.int128_type
                                else:
                                    _t1365 = None
                                deconstruct_result824 = _t1365
                                if deconstruct_result824 is not None:
                                    assert deconstruct_result824 is not None
                                    unwrapped825 = deconstruct_result824
                                    self.pretty_int128_type(unwrapped825)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1366 = _dollar_dollar.date_type
                                    else:
                                        _t1366 = None
                                    deconstruct_result822 = _t1366
                                    if deconstruct_result822 is not None:
                                        assert deconstruct_result822 is not None
                                        unwrapped823 = deconstruct_result822
                                        self.pretty_date_type(unwrapped823)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1367 = _dollar_dollar.datetime_type
                                        else:
                                            _t1367 = None
                                        deconstruct_result820 = _t1367
                                        if deconstruct_result820 is not None:
                                            assert deconstruct_result820 is not None
                                            unwrapped821 = deconstruct_result820
                                            self.pretty_datetime_type(unwrapped821)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1368 = _dollar_dollar.missing_type
                                            else:
                                                _t1368 = None
                                            deconstruct_result818 = _t1368
                                            if deconstruct_result818 is not None:
                                                assert deconstruct_result818 is not None
                                                unwrapped819 = deconstruct_result818
                                                self.pretty_missing_type(unwrapped819)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1369 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1369 = None
                                                deconstruct_result816 = _t1369
                                                if deconstruct_result816 is not None:
                                                    assert deconstruct_result816 is not None
                                                    unwrapped817 = deconstruct_result816
                                                    self.pretty_decimal_type(unwrapped817)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1370 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1370 = None
                                                    deconstruct_result814 = _t1370
                                                    if deconstruct_result814 is not None:
                                                        assert deconstruct_result814 is not None
                                                        unwrapped815 = deconstruct_result814
                                                        self.pretty_boolean_type(unwrapped815)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("int32_type"):
                                                            _t1371 = _dollar_dollar.int32_type
                                                        else:
                                                            _t1371 = None
                                                        deconstruct_result812 = _t1371
                                                        if deconstruct_result812 is not None:
                                                            assert deconstruct_result812 is not None
                                                            unwrapped813 = deconstruct_result812
                                                            self.pretty_int32_type(unwrapped813)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("float32_type"):
                                                                _t1372 = _dollar_dollar.float32_type
                                                            else:
                                                                _t1372 = None
                                                            deconstruct_result810 = _t1372
                                                            if deconstruct_result810 is not None:
                                                                assert deconstruct_result810 is not None
                                                                unwrapped811 = deconstruct_result810
                                                                self.pretty_float32_type(unwrapped811)
                                                            else:
                                                                raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields837 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields838 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields839 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields840 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields841 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields842 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields843 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields844 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields845 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat850 = self._try_flat(msg, self.pretty_decimal_type)
        if flat850 is not None:
            assert flat850 is not None
            self.write(flat850)
            return None
        else:
            _dollar_dollar = msg
            fields846 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields846 is not None
            unwrapped_fields847 = fields846
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field848 = unwrapped_fields847[0]
            self.write(str(field848))
            self.newline()
            field849 = unwrapped_fields847[1]
            self.write(str(field849))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields851 = msg
        self.write("BOOLEAN")

    def pretty_int32_type(self, msg: logic_pb2.Int32Type):
        fields852 = msg
        self.write("INT32")

    def pretty_float32_type(self, msg: logic_pb2.Float32Type):
        fields853 = msg
        self.write("FLOAT32")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat857 = self._try_flat(msg, self.pretty_value_bindings)
        if flat857 is not None:
            assert flat857 is not None
            self.write(flat857)
            return None
        else:
            fields854 = msg
            self.write("|")
            if not len(fields854) == 0:
                self.write(" ")
                for i856, elem855 in enumerate(fields854):
                    if (i856 > 0):
                        self.newline()
                    self.pretty_binding(elem855)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat884 = self._try_flat(msg, self.pretty_formula)
        if flat884 is not None:
            assert flat884 is not None
            self.write(flat884)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1373 = _dollar_dollar.conjunction
            else:
                _t1373 = None
            deconstruct_result882 = _t1373
            if deconstruct_result882 is not None:
                assert deconstruct_result882 is not None
                unwrapped883 = deconstruct_result882
                self.pretty_true(unwrapped883)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1374 = _dollar_dollar.disjunction
                else:
                    _t1374 = None
                deconstruct_result880 = _t1374
                if deconstruct_result880 is not None:
                    assert deconstruct_result880 is not None
                    unwrapped881 = deconstruct_result880
                    self.pretty_false(unwrapped881)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1375 = _dollar_dollar.exists
                    else:
                        _t1375 = None
                    deconstruct_result878 = _t1375
                    if deconstruct_result878 is not None:
                        assert deconstruct_result878 is not None
                        unwrapped879 = deconstruct_result878
                        self.pretty_exists(unwrapped879)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1376 = _dollar_dollar.reduce
                        else:
                            _t1376 = None
                        deconstruct_result876 = _t1376
                        if deconstruct_result876 is not None:
                            assert deconstruct_result876 is not None
                            unwrapped877 = deconstruct_result876
                            self.pretty_reduce(unwrapped877)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1377 = _dollar_dollar.conjunction
                            else:
                                _t1377 = None
                            deconstruct_result874 = _t1377
                            if deconstruct_result874 is not None:
                                assert deconstruct_result874 is not None
                                unwrapped875 = deconstruct_result874
                                self.pretty_conjunction(unwrapped875)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1378 = _dollar_dollar.disjunction
                                else:
                                    _t1378 = None
                                deconstruct_result872 = _t1378
                                if deconstruct_result872 is not None:
                                    assert deconstruct_result872 is not None
                                    unwrapped873 = deconstruct_result872
                                    self.pretty_disjunction(unwrapped873)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1379 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1379 = None
                                    deconstruct_result870 = _t1379
                                    if deconstruct_result870 is not None:
                                        assert deconstruct_result870 is not None
                                        unwrapped871 = deconstruct_result870
                                        self.pretty_not(unwrapped871)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1380 = _dollar_dollar.ffi
                                        else:
                                            _t1380 = None
                                        deconstruct_result868 = _t1380
                                        if deconstruct_result868 is not None:
                                            assert deconstruct_result868 is not None
                                            unwrapped869 = deconstruct_result868
                                            self.pretty_ffi(unwrapped869)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1381 = _dollar_dollar.atom
                                            else:
                                                _t1381 = None
                                            deconstruct_result866 = _t1381
                                            if deconstruct_result866 is not None:
                                                assert deconstruct_result866 is not None
                                                unwrapped867 = deconstruct_result866
                                                self.pretty_atom(unwrapped867)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1382 = _dollar_dollar.pragma
                                                else:
                                                    _t1382 = None
                                                deconstruct_result864 = _t1382
                                                if deconstruct_result864 is not None:
                                                    assert deconstruct_result864 is not None
                                                    unwrapped865 = deconstruct_result864
                                                    self.pretty_pragma(unwrapped865)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1383 = _dollar_dollar.primitive
                                                    else:
                                                        _t1383 = None
                                                    deconstruct_result862 = _t1383
                                                    if deconstruct_result862 is not None:
                                                        assert deconstruct_result862 is not None
                                                        unwrapped863 = deconstruct_result862
                                                        self.pretty_primitive(unwrapped863)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1384 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1384 = None
                                                        deconstruct_result860 = _t1384
                                                        if deconstruct_result860 is not None:
                                                            assert deconstruct_result860 is not None
                                                            unwrapped861 = deconstruct_result860
                                                            self.pretty_rel_atom(unwrapped861)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1385 = _dollar_dollar.cast
                                                            else:
                                                                _t1385 = None
                                                            deconstruct_result858 = _t1385
                                                            if deconstruct_result858 is not None:
                                                                assert deconstruct_result858 is not None
                                                                unwrapped859 = deconstruct_result858
                                                                self.pretty_cast(unwrapped859)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields885 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields886 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat891 = self._try_flat(msg, self.pretty_exists)
        if flat891 is not None:
            assert flat891 is not None
            self.write(flat891)
            return None
        else:
            _dollar_dollar = msg
            _t1386 = self.deconstruct_bindings(_dollar_dollar.body)
            fields887 = (_t1386, _dollar_dollar.body.value,)
            assert fields887 is not None
            unwrapped_fields888 = fields887
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field889 = unwrapped_fields888[0]
            self.pretty_bindings(field889)
            self.newline()
            field890 = unwrapped_fields888[1]
            self.pretty_formula(field890)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat897 = self._try_flat(msg, self.pretty_reduce)
        if flat897 is not None:
            assert flat897 is not None
            self.write(flat897)
            return None
        else:
            _dollar_dollar = msg
            fields892 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields892 is not None
            unwrapped_fields893 = fields892
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field894 = unwrapped_fields893[0]
            self.pretty_abstraction(field894)
            self.newline()
            field895 = unwrapped_fields893[1]
            self.pretty_abstraction(field895)
            self.newline()
            field896 = unwrapped_fields893[2]
            self.pretty_terms(field896)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat901 = self._try_flat(msg, self.pretty_terms)
        if flat901 is not None:
            assert flat901 is not None
            self.write(flat901)
            return None
        else:
            fields898 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields898) == 0:
                self.newline()
                for i900, elem899 in enumerate(fields898):
                    if (i900 > 0):
                        self.newline()
                    self.pretty_term(elem899)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat906 = self._try_flat(msg, self.pretty_term)
        if flat906 is not None:
            assert flat906 is not None
            self.write(flat906)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1387 = _dollar_dollar.var
            else:
                _t1387 = None
            deconstruct_result904 = _t1387
            if deconstruct_result904 is not None:
                assert deconstruct_result904 is not None
                unwrapped905 = deconstruct_result904
                self.pretty_var(unwrapped905)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1388 = _dollar_dollar.constant
                else:
                    _t1388 = None
                deconstruct_result902 = _t1388
                if deconstruct_result902 is not None:
                    assert deconstruct_result902 is not None
                    unwrapped903 = deconstruct_result902
                    self.pretty_constant(unwrapped903)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat909 = self._try_flat(msg, self.pretty_var)
        if flat909 is not None:
            assert flat909 is not None
            self.write(flat909)
            return None
        else:
            _dollar_dollar = msg
            fields907 = _dollar_dollar.name
            assert fields907 is not None
            unwrapped_fields908 = fields907
            self.write(unwrapped_fields908)

    def pretty_constant(self, msg: logic_pb2.Value):
        flat911 = self._try_flat(msg, self.pretty_constant)
        if flat911 is not None:
            assert flat911 is not None
            self.write(flat911)
            return None
        else:
            fields910 = msg
            self.pretty_value(fields910)

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat916 = self._try_flat(msg, self.pretty_conjunction)
        if flat916 is not None:
            assert flat916 is not None
            self.write(flat916)
            return None
        else:
            _dollar_dollar = msg
            fields912 = _dollar_dollar.args
            assert fields912 is not None
            unwrapped_fields913 = fields912
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields913) == 0:
                self.newline()
                for i915, elem914 in enumerate(unwrapped_fields913):
                    if (i915 > 0):
                        self.newline()
                    self.pretty_formula(elem914)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat921 = self._try_flat(msg, self.pretty_disjunction)
        if flat921 is not None:
            assert flat921 is not None
            self.write(flat921)
            return None
        else:
            _dollar_dollar = msg
            fields917 = _dollar_dollar.args
            assert fields917 is not None
            unwrapped_fields918 = fields917
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields918) == 0:
                self.newline()
                for i920, elem919 in enumerate(unwrapped_fields918):
                    if (i920 > 0):
                        self.newline()
                    self.pretty_formula(elem919)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat924 = self._try_flat(msg, self.pretty_not)
        if flat924 is not None:
            assert flat924 is not None
            self.write(flat924)
            return None
        else:
            _dollar_dollar = msg
            fields922 = _dollar_dollar.arg
            assert fields922 is not None
            unwrapped_fields923 = fields922
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields923)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat930 = self._try_flat(msg, self.pretty_ffi)
        if flat930 is not None:
            assert flat930 is not None
            self.write(flat930)
            return None
        else:
            _dollar_dollar = msg
            fields925 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields925 is not None
            unwrapped_fields926 = fields925
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field927 = unwrapped_fields926[0]
            self.pretty_name(field927)
            self.newline()
            field928 = unwrapped_fields926[1]
            self.pretty_ffi_args(field928)
            self.newline()
            field929 = unwrapped_fields926[2]
            self.pretty_terms(field929)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat932 = self._try_flat(msg, self.pretty_name)
        if flat932 is not None:
            assert flat932 is not None
            self.write(flat932)
            return None
        else:
            fields931 = msg
            self.write(":")
            self.write(fields931)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat936 = self._try_flat(msg, self.pretty_ffi_args)
        if flat936 is not None:
            assert flat936 is not None
            self.write(flat936)
            return None
        else:
            fields933 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields933) == 0:
                self.newline()
                for i935, elem934 in enumerate(fields933):
                    if (i935 > 0):
                        self.newline()
                    self.pretty_abstraction(elem934)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat943 = self._try_flat(msg, self.pretty_atom)
        if flat943 is not None:
            assert flat943 is not None
            self.write(flat943)
            return None
        else:
            _dollar_dollar = msg
            fields937 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields937 is not None
            unwrapped_fields938 = fields937
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field939 = unwrapped_fields938[0]
            self.pretty_relation_id(field939)
            field940 = unwrapped_fields938[1]
            if not len(field940) == 0:
                self.newline()
                for i942, elem941 in enumerate(field940):
                    if (i942 > 0):
                        self.newline()
                    self.pretty_term(elem941)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat950 = self._try_flat(msg, self.pretty_pragma)
        if flat950 is not None:
            assert flat950 is not None
            self.write(flat950)
            return None
        else:
            _dollar_dollar = msg
            fields944 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields944 is not None
            unwrapped_fields945 = fields944
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field946 = unwrapped_fields945[0]
            self.pretty_name(field946)
            field947 = unwrapped_fields945[1]
            if not len(field947) == 0:
                self.newline()
                for i949, elem948 in enumerate(field947):
                    if (i949 > 0):
                        self.newline()
                    self.pretty_term(elem948)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat966 = self._try_flat(msg, self.pretty_primitive)
        if flat966 is not None:
            assert flat966 is not None
            self.write(flat966)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1389 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1389 = None
            guard_result965 = _t1389
            if guard_result965 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1390 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1390 = None
                guard_result964 = _t1390
                if guard_result964 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1391 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1391 = None
                    guard_result963 = _t1391
                    if guard_result963 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1392 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1392 = None
                        guard_result962 = _t1392
                        if guard_result962 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1393 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1393 = None
                            guard_result961 = _t1393
                            if guard_result961 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1394 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1394 = None
                                guard_result960 = _t1394
                                if guard_result960 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1395 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1395 = None
                                    guard_result959 = _t1395
                                    if guard_result959 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1396 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1396 = None
                                        guard_result958 = _t1396
                                        if guard_result958 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1397 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1397 = None
                                            guard_result957 = _t1397
                                            if guard_result957 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields951 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields951 is not None
                                                unwrapped_fields952 = fields951
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field953 = unwrapped_fields952[0]
                                                self.pretty_name(field953)
                                                field954 = unwrapped_fields952[1]
                                                if not len(field954) == 0:
                                                    self.newline()
                                                    for i956, elem955 in enumerate(field954):
                                                        if (i956 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem955)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat971 = self._try_flat(msg, self.pretty_eq)
        if flat971 is not None:
            assert flat971 is not None
            self.write(flat971)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1398 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1398 = None
            fields967 = _t1398
            assert fields967 is not None
            unwrapped_fields968 = fields967
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field969 = unwrapped_fields968[0]
            self.pretty_term(field969)
            self.newline()
            field970 = unwrapped_fields968[1]
            self.pretty_term(field970)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat976 = self._try_flat(msg, self.pretty_lt)
        if flat976 is not None:
            assert flat976 is not None
            self.write(flat976)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1399 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1399 = None
            fields972 = _t1399
            assert fields972 is not None
            unwrapped_fields973 = fields972
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field974 = unwrapped_fields973[0]
            self.pretty_term(field974)
            self.newline()
            field975 = unwrapped_fields973[1]
            self.pretty_term(field975)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat981 = self._try_flat(msg, self.pretty_lt_eq)
        if flat981 is not None:
            assert flat981 is not None
            self.write(flat981)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1400 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1400 = None
            fields977 = _t1400
            assert fields977 is not None
            unwrapped_fields978 = fields977
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field979 = unwrapped_fields978[0]
            self.pretty_term(field979)
            self.newline()
            field980 = unwrapped_fields978[1]
            self.pretty_term(field980)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat986 = self._try_flat(msg, self.pretty_gt)
        if flat986 is not None:
            assert flat986 is not None
            self.write(flat986)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1401 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1401 = None
            fields982 = _t1401
            assert fields982 is not None
            unwrapped_fields983 = fields982
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field984 = unwrapped_fields983[0]
            self.pretty_term(field984)
            self.newline()
            field985 = unwrapped_fields983[1]
            self.pretty_term(field985)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat991 = self._try_flat(msg, self.pretty_gt_eq)
        if flat991 is not None:
            assert flat991 is not None
            self.write(flat991)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1402 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1402 = None
            fields987 = _t1402
            assert fields987 is not None
            unwrapped_fields988 = fields987
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field989 = unwrapped_fields988[0]
            self.pretty_term(field989)
            self.newline()
            field990 = unwrapped_fields988[1]
            self.pretty_term(field990)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat997 = self._try_flat(msg, self.pretty_add)
        if flat997 is not None:
            assert flat997 is not None
            self.write(flat997)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1403 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1403 = None
            fields992 = _t1403
            assert fields992 is not None
            unwrapped_fields993 = fields992
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field994 = unwrapped_fields993[0]
            self.pretty_term(field994)
            self.newline()
            field995 = unwrapped_fields993[1]
            self.pretty_term(field995)
            self.newline()
            field996 = unwrapped_fields993[2]
            self.pretty_term(field996)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat1003 = self._try_flat(msg, self.pretty_minus)
        if flat1003 is not None:
            assert flat1003 is not None
            self.write(flat1003)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1404 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1404 = None
            fields998 = _t1404
            assert fields998 is not None
            unwrapped_fields999 = fields998
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field1000 = unwrapped_fields999[0]
            self.pretty_term(field1000)
            self.newline()
            field1001 = unwrapped_fields999[1]
            self.pretty_term(field1001)
            self.newline()
            field1002 = unwrapped_fields999[2]
            self.pretty_term(field1002)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat1009 = self._try_flat(msg, self.pretty_multiply)
        if flat1009 is not None:
            assert flat1009 is not None
            self.write(flat1009)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1405 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1405 = None
            fields1004 = _t1405
            assert fields1004 is not None
            unwrapped_fields1005 = fields1004
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field1006 = unwrapped_fields1005[0]
            self.pretty_term(field1006)
            self.newline()
            field1007 = unwrapped_fields1005[1]
            self.pretty_term(field1007)
            self.newline()
            field1008 = unwrapped_fields1005[2]
            self.pretty_term(field1008)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat1015 = self._try_flat(msg, self.pretty_divide)
        if flat1015 is not None:
            assert flat1015 is not None
            self.write(flat1015)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1406 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1406 = None
            fields1010 = _t1406
            assert fields1010 is not None
            unwrapped_fields1011 = fields1010
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field1012 = unwrapped_fields1011[0]
            self.pretty_term(field1012)
            self.newline()
            field1013 = unwrapped_fields1011[1]
            self.pretty_term(field1013)
            self.newline()
            field1014 = unwrapped_fields1011[2]
            self.pretty_term(field1014)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1020 = self._try_flat(msg, self.pretty_rel_term)
        if flat1020 is not None:
            assert flat1020 is not None
            self.write(flat1020)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1407 = _dollar_dollar.specialized_value
            else:
                _t1407 = None
            deconstruct_result1018 = _t1407
            if deconstruct_result1018 is not None:
                assert deconstruct_result1018 is not None
                unwrapped1019 = deconstruct_result1018
                self.pretty_specialized_value(unwrapped1019)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1408 = _dollar_dollar.term
                else:
                    _t1408 = None
                deconstruct_result1016 = _t1408
                if deconstruct_result1016 is not None:
                    assert deconstruct_result1016 is not None
                    unwrapped1017 = deconstruct_result1016
                    self.pretty_term(unwrapped1017)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1022 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1022 is not None:
            assert flat1022 is not None
            self.write(flat1022)
            return None
        else:
            fields1021 = msg
            self.write("#")
            self.pretty_value(fields1021)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1029 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1029 is not None:
            assert flat1029 is not None
            self.write(flat1029)
            return None
        else:
            _dollar_dollar = msg
            fields1023 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1023 is not None
            unwrapped_fields1024 = fields1023
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1025 = unwrapped_fields1024[0]
            self.pretty_name(field1025)
            field1026 = unwrapped_fields1024[1]
            if not len(field1026) == 0:
                self.newline()
                for i1028, elem1027 in enumerate(field1026):
                    if (i1028 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1027)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1034 = self._try_flat(msg, self.pretty_cast)
        if flat1034 is not None:
            assert flat1034 is not None
            self.write(flat1034)
            return None
        else:
            _dollar_dollar = msg
            fields1030 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1030 is not None
            unwrapped_fields1031 = fields1030
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1032 = unwrapped_fields1031[0]
            self.pretty_term(field1032)
            self.newline()
            field1033 = unwrapped_fields1031[1]
            self.pretty_term(field1033)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1038 = self._try_flat(msg, self.pretty_attrs)
        if flat1038 is not None:
            assert flat1038 is not None
            self.write(flat1038)
            return None
        else:
            fields1035 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1035) == 0:
                self.newline()
                for i1037, elem1036 in enumerate(fields1035):
                    if (i1037 > 0):
                        self.newline()
                    self.pretty_attribute(elem1036)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1045 = self._try_flat(msg, self.pretty_attribute)
        if flat1045 is not None:
            assert flat1045 is not None
            self.write(flat1045)
            return None
        else:
            _dollar_dollar = msg
            fields1039 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1039 is not None
            unwrapped_fields1040 = fields1039
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1041 = unwrapped_fields1040[0]
            self.pretty_name(field1041)
            field1042 = unwrapped_fields1040[1]
            if not len(field1042) == 0:
                self.newline()
                for i1044, elem1043 in enumerate(field1042):
                    if (i1044 > 0):
                        self.newline()
                    self.pretty_value(elem1043)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1052 = self._try_flat(msg, self.pretty_algorithm)
        if flat1052 is not None:
            assert flat1052 is not None
            self.write(flat1052)
            return None
        else:
            _dollar_dollar = msg
            fields1046 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            assert fields1046 is not None
            unwrapped_fields1047 = fields1046
            self.write("(algorithm")
            self.indent_sexp()
            field1048 = unwrapped_fields1047[0]
            if not len(field1048) == 0:
                self.newline()
                for i1050, elem1049 in enumerate(field1048):
                    if (i1050 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1049)
            self.newline()
            field1051 = unwrapped_fields1047[1]
            self.pretty_script(field1051)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1057 = self._try_flat(msg, self.pretty_script)
        if flat1057 is not None:
            assert flat1057 is not None
            self.write(flat1057)
            return None
        else:
            _dollar_dollar = msg
            fields1053 = _dollar_dollar.constructs
            assert fields1053 is not None
            unwrapped_fields1054 = fields1053
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1054) == 0:
                self.newline()
                for i1056, elem1055 in enumerate(unwrapped_fields1054):
                    if (i1056 > 0):
                        self.newline()
                    self.pretty_construct(elem1055)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1062 = self._try_flat(msg, self.pretty_construct)
        if flat1062 is not None:
            assert flat1062 is not None
            self.write(flat1062)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1409 = _dollar_dollar.loop
            else:
                _t1409 = None
            deconstruct_result1060 = _t1409
            if deconstruct_result1060 is not None:
                assert deconstruct_result1060 is not None
                unwrapped1061 = deconstruct_result1060
                self.pretty_loop(unwrapped1061)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1410 = _dollar_dollar.instruction
                else:
                    _t1410 = None
                deconstruct_result1058 = _t1410
                if deconstruct_result1058 is not None:
                    assert deconstruct_result1058 is not None
                    unwrapped1059 = deconstruct_result1058
                    self.pretty_instruction(unwrapped1059)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1067 = self._try_flat(msg, self.pretty_loop)
        if flat1067 is not None:
            assert flat1067 is not None
            self.write(flat1067)
            return None
        else:
            _dollar_dollar = msg
            fields1063 = (_dollar_dollar.init, _dollar_dollar.body,)
            assert fields1063 is not None
            unwrapped_fields1064 = fields1063
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1065 = unwrapped_fields1064[0]
            self.pretty_init(field1065)
            self.newline()
            field1066 = unwrapped_fields1064[1]
            self.pretty_script(field1066)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1071 = self._try_flat(msg, self.pretty_init)
        if flat1071 is not None:
            assert flat1071 is not None
            self.write(flat1071)
            return None
        else:
            fields1068 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1068) == 0:
                self.newline()
                for i1070, elem1069 in enumerate(fields1068):
                    if (i1070 > 0):
                        self.newline()
                    self.pretty_instruction(elem1069)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1082 = self._try_flat(msg, self.pretty_instruction)
        if flat1082 is not None:
            assert flat1082 is not None
            self.write(flat1082)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1411 = _dollar_dollar.assign
            else:
                _t1411 = None
            deconstruct_result1080 = _t1411
            if deconstruct_result1080 is not None:
                assert deconstruct_result1080 is not None
                unwrapped1081 = deconstruct_result1080
                self.pretty_assign(unwrapped1081)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1412 = _dollar_dollar.upsert
                else:
                    _t1412 = None
                deconstruct_result1078 = _t1412
                if deconstruct_result1078 is not None:
                    assert deconstruct_result1078 is not None
                    unwrapped1079 = deconstruct_result1078
                    self.pretty_upsert(unwrapped1079)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1413 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1413 = None
                    deconstruct_result1076 = _t1413
                    if deconstruct_result1076 is not None:
                        assert deconstruct_result1076 is not None
                        unwrapped1077 = deconstruct_result1076
                        self.pretty_break(unwrapped1077)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1414 = _dollar_dollar.monoid_def
                        else:
                            _t1414 = None
                        deconstruct_result1074 = _t1414
                        if deconstruct_result1074 is not None:
                            assert deconstruct_result1074 is not None
                            unwrapped1075 = deconstruct_result1074
                            self.pretty_monoid_def(unwrapped1075)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1415 = _dollar_dollar.monus_def
                            else:
                                _t1415 = None
                            deconstruct_result1072 = _t1415
                            if deconstruct_result1072 is not None:
                                assert deconstruct_result1072 is not None
                                unwrapped1073 = deconstruct_result1072
                                self.pretty_monus_def(unwrapped1073)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1089 = self._try_flat(msg, self.pretty_assign)
        if flat1089 is not None:
            assert flat1089 is not None
            self.write(flat1089)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1416 = _dollar_dollar.attrs
            else:
                _t1416 = None
            fields1083 = (_dollar_dollar.name, _dollar_dollar.body, _t1416,)
            assert fields1083 is not None
            unwrapped_fields1084 = fields1083
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1085 = unwrapped_fields1084[0]
            self.pretty_relation_id(field1085)
            self.newline()
            field1086 = unwrapped_fields1084[1]
            self.pretty_abstraction(field1086)
            field1087 = unwrapped_fields1084[2]
            if field1087 is not None:
                self.newline()
                assert field1087 is not None
                opt_val1088 = field1087
                self.pretty_attrs(opt_val1088)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1096 = self._try_flat(msg, self.pretty_upsert)
        if flat1096 is not None:
            assert flat1096 is not None
            self.write(flat1096)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1417 = _dollar_dollar.attrs
            else:
                _t1417 = None
            fields1090 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1417,)
            assert fields1090 is not None
            unwrapped_fields1091 = fields1090
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1092 = unwrapped_fields1091[0]
            self.pretty_relation_id(field1092)
            self.newline()
            field1093 = unwrapped_fields1091[1]
            self.pretty_abstraction_with_arity(field1093)
            field1094 = unwrapped_fields1091[2]
            if field1094 is not None:
                self.newline()
                assert field1094 is not None
                opt_val1095 = field1094
                self.pretty_attrs(opt_val1095)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1101 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1101 is not None:
            assert flat1101 is not None
            self.write(flat1101)
            return None
        else:
            _dollar_dollar = msg
            _t1418 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1097 = (_t1418, _dollar_dollar[0].value,)
            assert fields1097 is not None
            unwrapped_fields1098 = fields1097
            self.write("(")
            self.indent()
            field1099 = unwrapped_fields1098[0]
            self.pretty_bindings(field1099)
            self.newline()
            field1100 = unwrapped_fields1098[1]
            self.pretty_formula(field1100)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1108 = self._try_flat(msg, self.pretty_break)
        if flat1108 is not None:
            assert flat1108 is not None
            self.write(flat1108)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1419 = _dollar_dollar.attrs
            else:
                _t1419 = None
            fields1102 = (_dollar_dollar.name, _dollar_dollar.body, _t1419,)
            assert fields1102 is not None
            unwrapped_fields1103 = fields1102
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1104 = unwrapped_fields1103[0]
            self.pretty_relation_id(field1104)
            self.newline()
            field1105 = unwrapped_fields1103[1]
            self.pretty_abstraction(field1105)
            field1106 = unwrapped_fields1103[2]
            if field1106 is not None:
                self.newline()
                assert field1106 is not None
                opt_val1107 = field1106
                self.pretty_attrs(opt_val1107)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1116 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1116 is not None:
            assert flat1116 is not None
            self.write(flat1116)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1420 = _dollar_dollar.attrs
            else:
                _t1420 = None
            fields1109 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1420,)
            assert fields1109 is not None
            unwrapped_fields1110 = fields1109
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1111 = unwrapped_fields1110[0]
            self.pretty_monoid(field1111)
            self.newline()
            field1112 = unwrapped_fields1110[1]
            self.pretty_relation_id(field1112)
            self.newline()
            field1113 = unwrapped_fields1110[2]
            self.pretty_abstraction_with_arity(field1113)
            field1114 = unwrapped_fields1110[3]
            if field1114 is not None:
                self.newline()
                assert field1114 is not None
                opt_val1115 = field1114
                self.pretty_attrs(opt_val1115)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1125 = self._try_flat(msg, self.pretty_monoid)
        if flat1125 is not None:
            assert flat1125 is not None
            self.write(flat1125)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1421 = _dollar_dollar.or_monoid
            else:
                _t1421 = None
            deconstruct_result1123 = _t1421
            if deconstruct_result1123 is not None:
                assert deconstruct_result1123 is not None
                unwrapped1124 = deconstruct_result1123
                self.pretty_or_monoid(unwrapped1124)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1422 = _dollar_dollar.min_monoid
                else:
                    _t1422 = None
                deconstruct_result1121 = _t1422
                if deconstruct_result1121 is not None:
                    assert deconstruct_result1121 is not None
                    unwrapped1122 = deconstruct_result1121
                    self.pretty_min_monoid(unwrapped1122)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1423 = _dollar_dollar.max_monoid
                    else:
                        _t1423 = None
                    deconstruct_result1119 = _t1423
                    if deconstruct_result1119 is not None:
                        assert deconstruct_result1119 is not None
                        unwrapped1120 = deconstruct_result1119
                        self.pretty_max_monoid(unwrapped1120)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1424 = _dollar_dollar.sum_monoid
                        else:
                            _t1424 = None
                        deconstruct_result1117 = _t1424
                        if deconstruct_result1117 is not None:
                            assert deconstruct_result1117 is not None
                            unwrapped1118 = deconstruct_result1117
                            self.pretty_sum_monoid(unwrapped1118)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1126 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1129 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1129 is not None:
            assert flat1129 is not None
            self.write(flat1129)
            return None
        else:
            _dollar_dollar = msg
            fields1127 = _dollar_dollar.type
            assert fields1127 is not None
            unwrapped_fields1128 = fields1127
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1128)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1132 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1132 is not None:
            assert flat1132 is not None
            self.write(flat1132)
            return None
        else:
            _dollar_dollar = msg
            fields1130 = _dollar_dollar.type
            assert fields1130 is not None
            unwrapped_fields1131 = fields1130
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1131)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1135 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1135 is not None:
            assert flat1135 is not None
            self.write(flat1135)
            return None
        else:
            _dollar_dollar = msg
            fields1133 = _dollar_dollar.type
            assert fields1133 is not None
            unwrapped_fields1134 = fields1133
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1134)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1143 = self._try_flat(msg, self.pretty_monus_def)
        if flat1143 is not None:
            assert flat1143 is not None
            self.write(flat1143)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1425 = _dollar_dollar.attrs
            else:
                _t1425 = None
            fields1136 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1425,)
            assert fields1136 is not None
            unwrapped_fields1137 = fields1136
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1138 = unwrapped_fields1137[0]
            self.pretty_monoid(field1138)
            self.newline()
            field1139 = unwrapped_fields1137[1]
            self.pretty_relation_id(field1139)
            self.newline()
            field1140 = unwrapped_fields1137[2]
            self.pretty_abstraction_with_arity(field1140)
            field1141 = unwrapped_fields1137[3]
            if field1141 is not None:
                self.newline()
                assert field1141 is not None
                opt_val1142 = field1141
                self.pretty_attrs(opt_val1142)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1150 = self._try_flat(msg, self.pretty_constraint)
        if flat1150 is not None:
            assert flat1150 is not None
            self.write(flat1150)
            return None
        else:
            _dollar_dollar = msg
            fields1144 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1144 is not None
            unwrapped_fields1145 = fields1144
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1146 = unwrapped_fields1145[0]
            self.pretty_relation_id(field1146)
            self.newline()
            field1147 = unwrapped_fields1145[1]
            self.pretty_abstraction(field1147)
            self.newline()
            field1148 = unwrapped_fields1145[2]
            self.pretty_functional_dependency_keys(field1148)
            self.newline()
            field1149 = unwrapped_fields1145[3]
            self.pretty_functional_dependency_values(field1149)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1154 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1154 is not None:
            assert flat1154 is not None
            self.write(flat1154)
            return None
        else:
            fields1151 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1151) == 0:
                self.newline()
                for i1153, elem1152 in enumerate(fields1151):
                    if (i1153 > 0):
                        self.newline()
                    self.pretty_var(elem1152)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1158 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1158 is not None:
            assert flat1158 is not None
            self.write(flat1158)
            return None
        else:
            fields1155 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1155) == 0:
                self.newline()
                for i1157, elem1156 in enumerate(fields1155):
                    if (i1157 > 0):
                        self.newline()
                    self.pretty_var(elem1156)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1165 = self._try_flat(msg, self.pretty_data)
        if flat1165 is not None:
            assert flat1165 is not None
            self.write(flat1165)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1426 = _dollar_dollar.edb
            else:
                _t1426 = None
            deconstruct_result1163 = _t1426
            if deconstruct_result1163 is not None:
                assert deconstruct_result1163 is not None
                unwrapped1164 = deconstruct_result1163
                self.pretty_edb(unwrapped1164)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1427 = _dollar_dollar.betree_relation
                else:
                    _t1427 = None
                deconstruct_result1161 = _t1427
                if deconstruct_result1161 is not None:
                    assert deconstruct_result1161 is not None
                    unwrapped1162 = deconstruct_result1161
                    self.pretty_betree_relation(unwrapped1162)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1428 = _dollar_dollar.csv_data
                    else:
                        _t1428 = None
                    deconstruct_result1159 = _t1428
                    if deconstruct_result1159 is not None:
                        assert deconstruct_result1159 is not None
                        unwrapped1160 = deconstruct_result1159
                        self.pretty_csv_data(unwrapped1160)
                    else:
                        raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1171 = self._try_flat(msg, self.pretty_edb)
        if flat1171 is not None:
            assert flat1171 is not None
            self.write(flat1171)
            return None
        else:
            _dollar_dollar = msg
            fields1166 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1166 is not None
            unwrapped_fields1167 = fields1166
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1168 = unwrapped_fields1167[0]
            self.pretty_relation_id(field1168)
            self.newline()
            field1169 = unwrapped_fields1167[1]
            self.pretty_edb_path(field1169)
            self.newline()
            field1170 = unwrapped_fields1167[2]
            self.pretty_edb_types(field1170)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1175 = self._try_flat(msg, self.pretty_edb_path)
        if flat1175 is not None:
            assert flat1175 is not None
            self.write(flat1175)
            return None
        else:
            fields1172 = msg
            self.write("[")
            self.indent()
            for i1174, elem1173 in enumerate(fields1172):
                if (i1174 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1173))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1179 = self._try_flat(msg, self.pretty_edb_types)
        if flat1179 is not None:
            assert flat1179 is not None
            self.write(flat1179)
            return None
        else:
            fields1176 = msg
            self.write("[")
            self.indent()
            for i1178, elem1177 in enumerate(fields1176):
                if (i1178 > 0):
                    self.newline()
                self.pretty_type(elem1177)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1184 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1184 is not None:
            assert flat1184 is not None
            self.write(flat1184)
            return None
        else:
            _dollar_dollar = msg
            fields1180 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1180 is not None
            unwrapped_fields1181 = fields1180
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1182 = unwrapped_fields1181[0]
            self.pretty_relation_id(field1182)
            self.newline()
            field1183 = unwrapped_fields1181[1]
            self.pretty_betree_info(field1183)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1190 = self._try_flat(msg, self.pretty_betree_info)
        if flat1190 is not None:
            assert flat1190 is not None
            self.write(flat1190)
            return None
        else:
            _dollar_dollar = msg
            _t1429 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1185 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1429,)
            assert fields1185 is not None
            unwrapped_fields1186 = fields1185
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1187 = unwrapped_fields1186[0]
            self.pretty_betree_info_key_types(field1187)
            self.newline()
            field1188 = unwrapped_fields1186[1]
            self.pretty_betree_info_value_types(field1188)
            self.newline()
            field1189 = unwrapped_fields1186[2]
            self.pretty_config_dict(field1189)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1194 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1194 is not None:
            assert flat1194 is not None
            self.write(flat1194)
            return None
        else:
            fields1191 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1191) == 0:
                self.newline()
                for i1193, elem1192 in enumerate(fields1191):
                    if (i1193 > 0):
                        self.newline()
                    self.pretty_type(elem1192)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1198 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1198 is not None:
            assert flat1198 is not None
            self.write(flat1198)
            return None
        else:
            fields1195 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1195) == 0:
                self.newline()
                for i1197, elem1196 in enumerate(fields1195):
                    if (i1197 > 0):
                        self.newline()
                    self.pretty_type(elem1196)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1205 = self._try_flat(msg, self.pretty_csv_data)
        if flat1205 is not None:
            assert flat1205 is not None
            self.write(flat1205)
            return None
        else:
            _dollar_dollar = msg
            fields1199 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1199 is not None
            unwrapped_fields1200 = fields1199
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1201 = unwrapped_fields1200[0]
            self.pretty_csvlocator(field1201)
            self.newline()
            field1202 = unwrapped_fields1200[1]
            self.pretty_csv_config(field1202)
            self.newline()
            field1203 = unwrapped_fields1200[2]
            self.pretty_gnf_columns(field1203)
            self.newline()
            field1204 = unwrapped_fields1200[3]
            self.pretty_csv_asof(field1204)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1212 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1212 is not None:
            assert flat1212 is not None
            self.write(flat1212)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1430 = _dollar_dollar.paths
            else:
                _t1430 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1431 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1431 = None
            fields1206 = (_t1430, _t1431,)
            assert fields1206 is not None
            unwrapped_fields1207 = fields1206
            self.write("(csv_locator")
            self.indent_sexp()
            field1208 = unwrapped_fields1207[0]
            if field1208 is not None:
                self.newline()
                assert field1208 is not None
                opt_val1209 = field1208
                self.pretty_csv_locator_paths(opt_val1209)
            field1210 = unwrapped_fields1207[1]
            if field1210 is not None:
                self.newline()
                assert field1210 is not None
                opt_val1211 = field1210
                self.pretty_csv_locator_inline_data(opt_val1211)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1216 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1216 is not None:
            assert flat1216 is not None
            self.write(flat1216)
            return None
        else:
            fields1213 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1213) == 0:
                self.newline()
                for i1215, elem1214 in enumerate(fields1213):
                    if (i1215 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1214))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1218 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1218 is not None:
            assert flat1218 is not None
            self.write(flat1218)
            return None
        else:
            fields1217 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1217))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1221 = self._try_flat(msg, self.pretty_csv_config)
        if flat1221 is not None:
            assert flat1221 is not None
            self.write(flat1221)
            return None
        else:
            _dollar_dollar = msg
            _t1432 = self.deconstruct_csv_config(_dollar_dollar)
            fields1219 = _t1432
            assert fields1219 is not None
            unwrapped_fields1220 = fields1219
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1220)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1225 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1225 is not None:
            assert flat1225 is not None
            self.write(flat1225)
            return None
        else:
            fields1222 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1222) == 0:
                self.newline()
                for i1224, elem1223 in enumerate(fields1222):
                    if (i1224 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1223)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1234 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1234 is not None:
            assert flat1234 is not None
            self.write(flat1234)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1433 = _dollar_dollar.target_id
            else:
                _t1433 = None
            fields1226 = (_dollar_dollar.column_path, _t1433, _dollar_dollar.types,)
            assert fields1226 is not None
            unwrapped_fields1227 = fields1226
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1228 = unwrapped_fields1227[0]
            self.pretty_gnf_column_path(field1228)
            field1229 = unwrapped_fields1227[1]
            if field1229 is not None:
                self.newline()
                assert field1229 is not None
                opt_val1230 = field1229
                self.pretty_relation_id(opt_val1230)
            self.newline()
            self.write("[")
            field1231 = unwrapped_fields1227[2]
            for i1233, elem1232 in enumerate(field1231):
                if (i1233 > 0):
                    self.newline()
                self.pretty_type(elem1232)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1241 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1241 is not None:
            assert flat1241 is not None
            self.write(flat1241)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1434 = _dollar_dollar[0]
            else:
                _t1434 = None
            deconstruct_result1239 = _t1434
            if deconstruct_result1239 is not None:
                assert deconstruct_result1239 is not None
                unwrapped1240 = deconstruct_result1239
                self.write(self.format_string_value(unwrapped1240))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1435 = _dollar_dollar
                else:
                    _t1435 = None
                deconstruct_result1235 = _t1435
                if deconstruct_result1235 is not None:
                    assert deconstruct_result1235 is not None
                    unwrapped1236 = deconstruct_result1235
                    self.write("[")
                    self.indent()
                    for i1238, elem1237 in enumerate(unwrapped1236):
                        if (i1238 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1237))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1243 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1243 is not None:
            assert flat1243 is not None
            self.write(flat1243)
            return None
        else:
            fields1242 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1242))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1246 = self._try_flat(msg, self.pretty_undefine)
        if flat1246 is not None:
            assert flat1246 is not None
            self.write(flat1246)
            return None
        else:
            _dollar_dollar = msg
            fields1244 = _dollar_dollar.fragment_id
            assert fields1244 is not None
            unwrapped_fields1245 = fields1244
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1245)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1251 = self._try_flat(msg, self.pretty_context)
        if flat1251 is not None:
            assert flat1251 is not None
            self.write(flat1251)
            return None
        else:
            _dollar_dollar = msg
            fields1247 = _dollar_dollar.relations
            assert fields1247 is not None
            unwrapped_fields1248 = fields1247
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1248) == 0:
                self.newline()
                for i1250, elem1249 in enumerate(unwrapped_fields1248):
                    if (i1250 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1249)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1256 = self._try_flat(msg, self.pretty_snapshot)
        if flat1256 is not None:
            assert flat1256 is not None
            self.write(flat1256)
            return None
        else:
            _dollar_dollar = msg
            fields1252 = _dollar_dollar.mappings
            assert fields1252 is not None
            unwrapped_fields1253 = fields1252
            self.write("(snapshot")
            self.indent_sexp()
            if not len(unwrapped_fields1253) == 0:
                self.newline()
                for i1255, elem1254 in enumerate(unwrapped_fields1253):
                    if (i1255 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1254)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1261 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1261 is not None:
            assert flat1261 is not None
            self.write(flat1261)
            return None
        else:
            _dollar_dollar = msg
            fields1257 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1257 is not None
            unwrapped_fields1258 = fields1257
            field1259 = unwrapped_fields1258[0]
            self.pretty_edb_path(field1259)
            self.write(" ")
            field1260 = unwrapped_fields1258[1]
            self.pretty_relation_id(field1260)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1265 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1265 is not None:
            assert flat1265 is not None
            self.write(flat1265)
            return None
        else:
            fields1262 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1262) == 0:
                self.newline()
                for i1264, elem1263 in enumerate(fields1262):
                    if (i1264 > 0):
                        self.newline()
                    self.pretty_read(elem1263)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1276 = self._try_flat(msg, self.pretty_read)
        if flat1276 is not None:
            assert flat1276 is not None
            self.write(flat1276)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1436 = _dollar_dollar.demand
            else:
                _t1436 = None
            deconstruct_result1274 = _t1436
            if deconstruct_result1274 is not None:
                assert deconstruct_result1274 is not None
                unwrapped1275 = deconstruct_result1274
                self.pretty_demand(unwrapped1275)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1437 = _dollar_dollar.output
                else:
                    _t1437 = None
                deconstruct_result1272 = _t1437
                if deconstruct_result1272 is not None:
                    assert deconstruct_result1272 is not None
                    unwrapped1273 = deconstruct_result1272
                    self.pretty_output(unwrapped1273)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1438 = _dollar_dollar.what_if
                    else:
                        _t1438 = None
                    deconstruct_result1270 = _t1438
                    if deconstruct_result1270 is not None:
                        assert deconstruct_result1270 is not None
                        unwrapped1271 = deconstruct_result1270
                        self.pretty_what_if(unwrapped1271)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1439 = _dollar_dollar.abort
                        else:
                            _t1439 = None
                        deconstruct_result1268 = _t1439
                        if deconstruct_result1268 is not None:
                            assert deconstruct_result1268 is not None
                            unwrapped1269 = deconstruct_result1268
                            self.pretty_abort(unwrapped1269)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1440 = _dollar_dollar.export
                            else:
                                _t1440 = None
                            deconstruct_result1266 = _t1440
                            if deconstruct_result1266 is not None:
                                assert deconstruct_result1266 is not None
                                unwrapped1267 = deconstruct_result1266
                                self.pretty_export(unwrapped1267)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1279 = self._try_flat(msg, self.pretty_demand)
        if flat1279 is not None:
            assert flat1279 is not None
            self.write(flat1279)
            return None
        else:
            _dollar_dollar = msg
            fields1277 = _dollar_dollar.relation_id
            assert fields1277 is not None
            unwrapped_fields1278 = fields1277
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1278)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1284 = self._try_flat(msg, self.pretty_output)
        if flat1284 is not None:
            assert flat1284 is not None
            self.write(flat1284)
            return None
        else:
            _dollar_dollar = msg
            fields1280 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1280 is not None
            unwrapped_fields1281 = fields1280
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1282 = unwrapped_fields1281[0]
            self.pretty_name(field1282)
            self.newline()
            field1283 = unwrapped_fields1281[1]
            self.pretty_relation_id(field1283)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1289 = self._try_flat(msg, self.pretty_what_if)
        if flat1289 is not None:
            assert flat1289 is not None
            self.write(flat1289)
            return None
        else:
            _dollar_dollar = msg
            fields1285 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1285 is not None
            unwrapped_fields1286 = fields1285
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1287 = unwrapped_fields1286[0]
            self.pretty_name(field1287)
            self.newline()
            field1288 = unwrapped_fields1286[1]
            self.pretty_epoch(field1288)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1295 = self._try_flat(msg, self.pretty_abort)
        if flat1295 is not None:
            assert flat1295 is not None
            self.write(flat1295)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1441 = _dollar_dollar.name
            else:
                _t1441 = None
            fields1290 = (_t1441, _dollar_dollar.relation_id,)
            assert fields1290 is not None
            unwrapped_fields1291 = fields1290
            self.write("(abort")
            self.indent_sexp()
            field1292 = unwrapped_fields1291[0]
            if field1292 is not None:
                self.newline()
                assert field1292 is not None
                opt_val1293 = field1292
                self.pretty_name(opt_val1293)
            self.newline()
            field1294 = unwrapped_fields1291[1]
            self.pretty_relation_id(field1294)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1298 = self._try_flat(msg, self.pretty_export)
        if flat1298 is not None:
            assert flat1298 is not None
            self.write(flat1298)
            return None
        else:
            _dollar_dollar = msg
            fields1296 = _dollar_dollar.csv_config
            assert fields1296 is not None
            unwrapped_fields1297 = fields1296
            self.write("(export")
            self.indent_sexp()
            self.newline()
            self.pretty_export_csv_config(unwrapped_fields1297)
            self.dedent()
            self.write(")")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1309 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1309 is not None:
            assert flat1309 is not None
            self.write(flat1309)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1442 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1442 = None
            deconstruct_result1304 = _t1442
            if deconstruct_result1304 is not None:
                assert deconstruct_result1304 is not None
                unwrapped1305 = deconstruct_result1304
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1306 = unwrapped1305[0]
                self.pretty_export_csv_path(field1306)
                self.newline()
                field1307 = unwrapped1305[1]
                self.pretty_export_csv_source(field1307)
                self.newline()
                field1308 = unwrapped1305[2]
                self.pretty_csv_config(field1308)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1444 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1443 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1444,)
                else:
                    _t1443 = None
                deconstruct_result1299 = _t1443
                if deconstruct_result1299 is not None:
                    assert deconstruct_result1299 is not None
                    unwrapped1300 = deconstruct_result1299
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1301 = unwrapped1300[0]
                    self.pretty_export_csv_path(field1301)
                    self.newline()
                    field1302 = unwrapped1300[1]
                    self.pretty_export_csv_columns_list(field1302)
                    self.newline()
                    field1303 = unwrapped1300[2]
                    self.pretty_config_dict(field1303)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1311 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1311 is not None:
            assert flat1311 is not None
            self.write(flat1311)
            return None
        else:
            fields1310 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1310))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1318 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1318 is not None:
            assert flat1318 is not None
            self.write(flat1318)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1445 = _dollar_dollar.gnf_columns.columns
            else:
                _t1445 = None
            deconstruct_result1314 = _t1445
            if deconstruct_result1314 is not None:
                assert deconstruct_result1314 is not None
                unwrapped1315 = deconstruct_result1314
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1315) == 0:
                    self.newline()
                    for i1317, elem1316 in enumerate(unwrapped1315):
                        if (i1317 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1316)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1446 = _dollar_dollar.table_def
                else:
                    _t1446 = None
                deconstruct_result1312 = _t1446
                if deconstruct_result1312 is not None:
                    assert deconstruct_result1312 is not None
                    unwrapped1313 = deconstruct_result1312
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1313)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1323 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1323 is not None:
            assert flat1323 is not None
            self.write(flat1323)
            return None
        else:
            _dollar_dollar = msg
            fields1319 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1319 is not None
            unwrapped_fields1320 = fields1319
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1321 = unwrapped_fields1320[0]
            self.write(self.format_string_value(field1321))
            self.newline()
            field1322 = unwrapped_fields1320[1]
            self.pretty_relation_id(field1322)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1327 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1327 is not None:
            assert flat1327 is not None
            self.write(flat1327)
            return None
        else:
            fields1324 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1324) == 0:
                self.newline()
                for i1326, elem1325 in enumerate(fields1324):
                    if (i1326 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1325)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1485 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1485)
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
