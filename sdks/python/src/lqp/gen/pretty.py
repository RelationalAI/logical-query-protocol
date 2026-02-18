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
    from typing import Any, IO, Never, Optional
else:
    from typing import Any, IO, NoReturn as Never, Optional

from lqp.proto.v1 import logic_pb2, fragments_pb2, transactions_pb2


class ParseError(Exception):
    pass


class PrettyPrinter:
    """Pretty printer for protobuf messages."""

    def __init__(self, io: Optional[IO[str]] = None, max_width: int = 92):
        self.io = io if io is not None else StringIO()
        self.indent_stack: list[int] = [0]
        self.column = 0
        self.at_line_start = True
        self.separator = '\n'
        self.max_width = max_width
        self._computing: set[int] = set()
        self._memo: dict[int, str] = {}
        self._memo_refs: list[Any] = []
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

    def _try_flat(self, msg: Any, pretty_fn: Any) -> Optional[str]:
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

    def relation_id_to_string(self, msg: logic_pb2.RelationId) -> str:
        """Convert RelationId to string representation using debug info."""
        return self._debug_info.get((msg.id_low, msg.id_high), "")

    def relation_id_to_int(self, msg: logic_pb2.RelationId) -> Optional[int]:
        """Convert RelationId to int if it fits in signed 64-bit range."""
        value = (msg.id_high << 64) | msg.id_low
        if value <= 0x7FFFFFFFFFFFFFFF:
            return value
        return None

    def relation_id_to_uint128(self, msg: logic_pb2.RelationId) -> logic_pb2.UInt128Value:
        """Convert RelationId to UInt128Value representation."""
        return logic_pb2.UInt128Value(low=msg.id_low, high=msg.id_high)

    def format_string_value(self, s: str) -> str:
        """Format a string value with double quotes for LQP output."""
        escaped = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return '"' + escaped + '"'

    # --- Helper functions ---

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1387 = logic_pb2.Value(int_value=int(v))
        return _t1387

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1388 = logic_pb2.Value(int_value=v)
        return _t1388

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1389 = logic_pb2.Value(float_value=v)
        return _t1389

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1390 = logic_pb2.Value(string_value=v)
        return _t1390

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1391 = logic_pb2.Value(boolean_value=v)
        return _t1391

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1392 = logic_pb2.Value(uint128_value=v)
        return _t1392

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1393 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1393,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1394 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1394,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1395 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1395,))
        _t1396 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1396,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1397 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1397,))
        _t1398 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1398,))
        if msg.new_line != "":
            _t1399 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1399,))
        _t1400 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1400,))
        _t1401 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1401,))
        _t1402 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1402,))
        if msg.comment != "":
            _t1403 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1403,))
        for missing_string in msg.missing_strings:
            _t1404 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1404,))
        _t1405 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1405,))
        _t1406 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1406,))
        _t1407 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1407,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1408 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1408,))
        _t1409 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1409,))
        _t1410 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1410,))
        _t1411 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1411,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1412 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1412,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1413 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1413,))
        _t1414 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1414,))
        _t1415 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1415,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1416 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1416,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1417 = self._make_value_string(msg.compression)
            result.append(("compression", _t1417,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1418 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1418,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1419 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1419,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1420 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1420,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1421 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1421,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1422 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1422,))
        return sorted(result)

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> Optional[str]:
        name = self.relation_id_to_string(msg)
        if name != "":
            return name
        return None

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name == "":
            return self.relation_id_to_uint128(msg)
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
        flat9 = self._try_flat(msg, self.pretty_transaction)
        if flat9 is not None:
            assert flat9 is not None
            self.write(flat9)
            return None
        else:
            def _t607(_dollar_dollar):
                if _dollar_dollar.HasField("configure"):
                    _t608 = _dollar_dollar.configure
                else:
                    _t608 = None
                if _dollar_dollar.HasField("sync"):
                    _t609 = _dollar_dollar.sync
                else:
                    _t609 = None
                return (_t608, _t609, _dollar_dollar.epochs,)
            _t610 = _t607(msg)
            fields0 = _t610
            assert fields0 is not None
            unwrapped_fields1 = fields0
            self.write("(")
            self.write("transaction")
            self.indent_sexp()
            field2 = unwrapped_fields1[0]
            if field2 is not None:
                self.newline()
                assert field2 is not None
                opt_val3 = field2
                _t612 = self.pretty_configure(opt_val3)
                _t611 = _t612
            else:
                _t611 = None
            field4 = unwrapped_fields1[1]
            if field4 is not None:
                self.newline()
                assert field4 is not None
                opt_val5 = field4
                _t614 = self.pretty_sync(opt_val5)
                _t613 = _t614
            else:
                _t613 = None
            field6 = unwrapped_fields1[2]
            if not len(field6) == 0:
                self.newline()
                for i8, elem7 in enumerate(field6):
                    if (i8 > 0):
                        self.newline()
                    _t615 = self.pretty_epoch(elem7)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat12 = self._try_flat(msg, self.pretty_configure)
        if flat12 is not None:
            assert flat12 is not None
            self.write(flat12)
            return None
        else:
            def _t616(_dollar_dollar):
                _t617 = self.deconstruct_configure(_dollar_dollar)
                return _t617
            _t618 = _t616(msg)
            fields10 = _t618
            assert fields10 is not None
            unwrapped_fields11 = fields10
            self.write("(")
            self.write("configure")
            self.indent_sexp()
            self.newline()
            _t619 = self.pretty_config_dict(unwrapped_fields11)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat17 = self._try_flat(msg, self.pretty_config_dict)
        if flat17 is not None:
            assert flat17 is not None
            self.write(flat17)
            return None
        else:
            def _t620(_dollar_dollar):
                return _dollar_dollar
            _t621 = _t620(msg)
            fields13 = _t621
            assert fields13 is not None
            unwrapped_fields14 = fields13
            self.write("{")
            self.indent()
            if not len(unwrapped_fields14) == 0:
                self.newline()
                for i16, elem15 in enumerate(unwrapped_fields14):
                    if (i16 > 0):
                        self.newline()
                    _t622 = self.pretty_config_key_value(elem15)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat22 = self._try_flat(msg, self.pretty_config_key_value)
        if flat22 is not None:
            assert flat22 is not None
            self.write(flat22)
            return None
        else:
            def _t624(_dollar_dollar):
                return (_dollar_dollar[0], _dollar_dollar[1],)
            _t625 = _t624(msg)
            fields18 = _t625
            assert fields18 is not None
            unwrapped_fields19 = fields18
            self.write(":")
            field20 = unwrapped_fields19[0]
            self.write(field20)
            self.write(" ")
            field21 = unwrapped_fields19[1]
            _t626 = self.pretty_value(field21)
            _t623 = _t626

    def pretty_value(self, msg: logic_pb2.Value):
        flat34 = self._try_flat(msg, self.pretty_value)
        if flat34 is not None:
            assert flat34 is not None
            self.write(flat34)
            return None
        else:
            def _t628(_dollar_dollar):
                if _dollar_dollar.HasField("date_value"):
                    _t629 = _dollar_dollar.date_value
                else:
                    _t629 = None
                return _t629
            _t630 = _t628(msg)
            deconstruct_result33 = _t630
            if deconstruct_result33 is not None:
                _t632 = self.pretty_date(deconstruct_result33)
                _t631 = _t632
            else:
                def _t633(_dollar_dollar):
                    if _dollar_dollar.HasField("datetime_value"):
                        _t634 = _dollar_dollar.datetime_value
                    else:
                        _t634 = None
                    return _t634
                _t635 = _t633(msg)
                deconstruct_result32 = _t635
                if deconstruct_result32 is not None:
                    _t637 = self.pretty_datetime(deconstruct_result32)
                    _t636 = _t637
                else:
                    def _t638(_dollar_dollar):
                        if _dollar_dollar.HasField("string_value"):
                            _t639 = _dollar_dollar.string_value
                        else:
                            _t639 = None
                        return _t639
                    _t640 = _t638(msg)
                    deconstruct_result31 = _t640
                    if deconstruct_result31 is not None:
                        self.write(self.format_string_value(deconstruct_result31))
                        _t641 = None
                    else:
                        def _t642(_dollar_dollar):
                            if _dollar_dollar.HasField("int_value"):
                                _t643 = _dollar_dollar.int_value
                            else:
                                _t643 = None
                            return _t643
                        _t644 = _t642(msg)
                        deconstruct_result30 = _t644
                        if deconstruct_result30 is not None:
                            self.write(str(deconstruct_result30))
                            _t645 = None
                        else:
                            def _t646(_dollar_dollar):
                                if _dollar_dollar.HasField("float_value"):
                                    _t647 = _dollar_dollar.float_value
                                else:
                                    _t647 = None
                                return _t647
                            _t648 = _t646(msg)
                            deconstruct_result29 = _t648
                            if deconstruct_result29 is not None:
                                self.write(str(deconstruct_result29))
                                _t649 = None
                            else:
                                def _t650(_dollar_dollar):
                                    if _dollar_dollar.HasField("uint128_value"):
                                        _t651 = _dollar_dollar.uint128_value
                                    else:
                                        _t651 = None
                                    return _t651
                                _t652 = _t650(msg)
                                deconstruct_result28 = _t652
                                if deconstruct_result28 is not None:
                                    self.write(self.format_uint128(deconstruct_result28))
                                    _t653 = None
                                else:
                                    def _t654(_dollar_dollar):
                                        if _dollar_dollar.HasField("int128_value"):
                                            _t655 = _dollar_dollar.int128_value
                                        else:
                                            _t655 = None
                                        return _t655
                                    _t656 = _t654(msg)
                                    deconstruct_result27 = _t656
                                    if deconstruct_result27 is not None:
                                        self.write(self.format_int128(deconstruct_result27))
                                        _t657 = None
                                    else:
                                        def _t658(_dollar_dollar):
                                            if _dollar_dollar.HasField("decimal_value"):
                                                _t659 = _dollar_dollar.decimal_value
                                            else:
                                                _t659 = None
                                            return _t659
                                        _t660 = _t658(msg)
                                        deconstruct_result26 = _t660
                                        if deconstruct_result26 is not None:
                                            self.write(self.format_decimal(deconstruct_result26))
                                            _t661 = None
                                        else:
                                            def _t662(_dollar_dollar):
                                                if _dollar_dollar.HasField("boolean_value"):
                                                    _t663 = _dollar_dollar.boolean_value
                                                else:
                                                    _t663 = None
                                                return _t663
                                            _t664 = _t662(msg)
                                            deconstruct_result25 = _t664
                                            if deconstruct_result25 is not None:
                                                _t666 = self.pretty_boolean_value(deconstruct_result25)
                                                _t665 = _t666
                                            else:
                                                def _t667(_dollar_dollar):
                                                    return _dollar_dollar
                                                _t668 = _t667(msg)
                                                fields23 = _t668
                                                assert fields23 is not None
                                                unwrapped_fields24 = fields23
                                                self.write("missing")
                                                _t665 = None
                                            _t661 = _t665
                                        _t657 = _t661
                                    _t653 = _t657
                                _t649 = _t653
                            _t645 = _t649
                        _t641 = _t645
                    _t636 = _t641
                _t631 = _t636
            _t627 = _t631

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat40 = self._try_flat(msg, self.pretty_date)
        if flat40 is not None:
            assert flat40 is not None
            self.write(flat40)
            return None
        else:
            def _t669(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            _t670 = _t669(msg)
            fields35 = _t670
            assert fields35 is not None
            unwrapped_fields36 = fields35
            self.write("(")
            self.write("date")
            self.indent_sexp()
            self.newline()
            field37 = unwrapped_fields36[0]
            self.write(str(field37))
            self.newline()
            field38 = unwrapped_fields36[1]
            self.write(str(field38))
            self.newline()
            field39 = unwrapped_fields36[2]
            self.write(str(field39))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat51 = self._try_flat(msg, self.pretty_datetime)
        if flat51 is not None:
            assert flat51 is not None
            self.write(flat51)
            return None
        else:
            def _t671(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            _t672 = _t671(msg)
            fields41 = _t672
            assert fields41 is not None
            unwrapped_fields42 = fields41
            self.write("(")
            self.write("datetime")
            self.indent_sexp()
            self.newline()
            field43 = unwrapped_fields42[0]
            self.write(str(field43))
            self.newline()
            field44 = unwrapped_fields42[1]
            self.write(str(field44))
            self.newline()
            field45 = unwrapped_fields42[2]
            self.write(str(field45))
            self.newline()
            field46 = unwrapped_fields42[3]
            self.write(str(field46))
            self.newline()
            field47 = unwrapped_fields42[4]
            self.write(str(field47))
            self.newline()
            field48 = unwrapped_fields42[5]
            self.write(str(field48))
            field49 = unwrapped_fields42[6]
            if field49 is not None:
                self.newline()
                assert field49 is not None
                opt_val50 = field49
                self.write(str(opt_val50))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        flat54 = self._try_flat(msg, self.pretty_boolean_value)
        if flat54 is not None:
            assert flat54 is not None
            self.write(flat54)
            return None
        else:
            def _t673(_dollar_dollar):
                if _dollar_dollar:
                    _t674 = ()
                else:
                    _t674 = None
                return _t674
            _t675 = _t673(msg)
            deconstruct_result53 = _t675
            if deconstruct_result53 is not None:
                self.write("true")
            else:
                def _t676(_dollar_dollar):
                    if not _dollar_dollar:
                        _t677 = ()
                    else:
                        _t677 = None
                    return _t677
                _t678 = _t676(msg)
                deconstruct_result52 = _t678
                if deconstruct_result52 is not None:
                    self.write("false")
                else:
                    raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat59 = self._try_flat(msg, self.pretty_sync)
        if flat59 is not None:
            assert flat59 is not None
            self.write(flat59)
            return None
        else:
            def _t679(_dollar_dollar):
                return _dollar_dollar.fragments
            _t680 = _t679(msg)
            fields55 = _t680
            assert fields55 is not None
            unwrapped_fields56 = fields55
            self.write("(")
            self.write("sync")
            self.indent_sexp()
            if not len(unwrapped_fields56) == 0:
                self.newline()
                for i58, elem57 in enumerate(unwrapped_fields56):
                    if (i58 > 0):
                        self.newline()
                    _t681 = self.pretty_fragment_id(elem57)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat62 = self._try_flat(msg, self.pretty_fragment_id)
        if flat62 is not None:
            assert flat62 is not None
            self.write(flat62)
            return None
        else:
            def _t682(_dollar_dollar):
                return self.fragment_id_to_string(_dollar_dollar)
            _t683 = _t682(msg)
            fields60 = _t683
            assert fields60 is not None
            unwrapped_fields61 = fields60
            self.write(":")
            self.write(unwrapped_fields61)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat69 = self._try_flat(msg, self.pretty_epoch)
        if flat69 is not None:
            assert flat69 is not None
            self.write(flat69)
            return None
        else:
            def _t684(_dollar_dollar):
                if not len(_dollar_dollar.writes) == 0:
                    _t685 = _dollar_dollar.writes
                else:
                    _t685 = None
                if not len(_dollar_dollar.reads) == 0:
                    _t686 = _dollar_dollar.reads
                else:
                    _t686 = None
                return (_t685, _t686,)
            _t687 = _t684(msg)
            fields63 = _t687
            assert fields63 is not None
            unwrapped_fields64 = fields63
            self.write("(")
            self.write("epoch")
            self.indent_sexp()
            field65 = unwrapped_fields64[0]
            if field65 is not None:
                self.newline()
                assert field65 is not None
                opt_val66 = field65
                _t689 = self.pretty_epoch_writes(opt_val66)
                _t688 = _t689
            else:
                _t688 = None
            field67 = unwrapped_fields64[1]
            if field67 is not None:
                self.newline()
                assert field67 is not None
                opt_val68 = field67
                _t691 = self.pretty_epoch_reads(opt_val68)
                _t690 = _t691
            else:
                _t690 = None
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat74 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat74 is not None:
            assert flat74 is not None
            self.write(flat74)
            return None
        else:
            def _t692(_dollar_dollar):
                return _dollar_dollar
            _t693 = _t692(msg)
            fields70 = _t693
            assert fields70 is not None
            unwrapped_fields71 = fields70
            self.write("(")
            self.write("writes")
            self.indent_sexp()
            if not len(unwrapped_fields71) == 0:
                self.newline()
                for i73, elem72 in enumerate(unwrapped_fields71):
                    if (i73 > 0):
                        self.newline()
                    _t694 = self.pretty_write(elem72)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat78 = self._try_flat(msg, self.pretty_write)
        if flat78 is not None:
            assert flat78 is not None
            self.write(flat78)
            return None
        else:
            def _t696(_dollar_dollar):
                if _dollar_dollar.HasField("define"):
                    _t697 = _dollar_dollar.define
                else:
                    _t697 = None
                return _t697
            _t698 = _t696(msg)
            deconstruct_result77 = _t698
            if deconstruct_result77 is not None:
                _t700 = self.pretty_define(deconstruct_result77)
                _t699 = _t700
            else:
                def _t701(_dollar_dollar):
                    if _dollar_dollar.HasField("undefine"):
                        _t702 = _dollar_dollar.undefine
                    else:
                        _t702 = None
                    return _t702
                _t703 = _t701(msg)
                deconstruct_result76 = _t703
                if deconstruct_result76 is not None:
                    _t705 = self.pretty_undefine(deconstruct_result76)
                    _t704 = _t705
                else:
                    def _t706(_dollar_dollar):
                        if _dollar_dollar.HasField("context"):
                            _t707 = _dollar_dollar.context
                        else:
                            _t707 = None
                        return _t707
                    _t708 = _t706(msg)
                    deconstruct_result75 = _t708
                    if deconstruct_result75 is not None:
                        _t710 = self.pretty_context(deconstruct_result75)
                        _t709 = _t710
                    else:
                        raise ParseError("No matching rule for write")
                    _t704 = _t709
                _t699 = _t704
            _t695 = _t699

    def pretty_define(self, msg: transactions_pb2.Define):
        flat81 = self._try_flat(msg, self.pretty_define)
        if flat81 is not None:
            assert flat81 is not None
            self.write(flat81)
            return None
        else:
            def _t711(_dollar_dollar):
                return _dollar_dollar.fragment
            _t712 = _t711(msg)
            fields79 = _t712
            assert fields79 is not None
            unwrapped_fields80 = fields79
            self.write("(")
            self.write("define")
            self.indent_sexp()
            self.newline()
            _t713 = self.pretty_fragment(unwrapped_fields80)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat88 = self._try_flat(msg, self.pretty_fragment)
        if flat88 is not None:
            assert flat88 is not None
            self.write(flat88)
            return None
        else:
            def _t714(_dollar_dollar):
                self.start_pretty_fragment(_dollar_dollar)
                return (_dollar_dollar.id, _dollar_dollar.declarations,)
            _t715 = _t714(msg)
            fields82 = _t715
            assert fields82 is not None
            unwrapped_fields83 = fields82
            self.write("(")
            self.write("fragment")
            self.indent_sexp()
            self.newline()
            field84 = unwrapped_fields83[0]
            _t716 = self.pretty_new_fragment_id(field84)
            field85 = unwrapped_fields83[1]
            if not len(field85) == 0:
                self.newline()
                for i87, elem86 in enumerate(field85):
                    if (i87 > 0):
                        self.newline()
                    _t717 = self.pretty_declaration(elem86)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat91 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat91 is not None:
            assert flat91 is not None
            self.write(flat91)
            return None
        else:
            def _t719(_dollar_dollar):
                return _dollar_dollar
            _t720 = _t719(msg)
            fields89 = _t720
            assert fields89 is not None
            unwrapped_fields90 = fields89
            _t721 = self.pretty_fragment_id(unwrapped_fields90)
            _t718 = _t721

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat96 = self._try_flat(msg, self.pretty_declaration)
        if flat96 is not None:
            assert flat96 is not None
            self.write(flat96)
            return None
        else:
            def _t723(_dollar_dollar):
                if _dollar_dollar.HasField("def"):
                    _t724 = getattr(_dollar_dollar, 'def')
                else:
                    _t724 = None
                return _t724
            _t725 = _t723(msg)
            deconstruct_result95 = _t725
            if deconstruct_result95 is not None:
                _t727 = self.pretty_def(deconstruct_result95)
                _t726 = _t727
            else:
                def _t728(_dollar_dollar):
                    if _dollar_dollar.HasField("algorithm"):
                        _t729 = _dollar_dollar.algorithm
                    else:
                        _t729 = None
                    return _t729
                _t730 = _t728(msg)
                deconstruct_result94 = _t730
                if deconstruct_result94 is not None:
                    _t732 = self.pretty_algorithm(deconstruct_result94)
                    _t731 = _t732
                else:
                    def _t733(_dollar_dollar):
                        if _dollar_dollar.HasField("constraint"):
                            _t734 = _dollar_dollar.constraint
                        else:
                            _t734 = None
                        return _t734
                    _t735 = _t733(msg)
                    deconstruct_result93 = _t735
                    if deconstruct_result93 is not None:
                        _t737 = self.pretty_constraint(deconstruct_result93)
                        _t736 = _t737
                    else:
                        def _t738(_dollar_dollar):
                            if _dollar_dollar.HasField("data"):
                                _t739 = _dollar_dollar.data
                            else:
                                _t739 = None
                            return _t739
                        _t740 = _t738(msg)
                        deconstruct_result92 = _t740
                        if deconstruct_result92 is not None:
                            _t742 = self.pretty_data(deconstruct_result92)
                            _t741 = _t742
                        else:
                            raise ParseError("No matching rule for declaration")
                        _t736 = _t741
                    _t731 = _t736
                _t726 = _t731
            _t722 = _t726

    def pretty_def(self, msg: logic_pb2.Def):
        flat103 = self._try_flat(msg, self.pretty_def)
        if flat103 is not None:
            assert flat103 is not None
            self.write(flat103)
            return None
        else:
            def _t743(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t744 = _dollar_dollar.attrs
                else:
                    _t744 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t744,)
            _t745 = _t743(msg)
            fields97 = _t745
            assert fields97 is not None
            unwrapped_fields98 = fields97
            self.write("(")
            self.write("def")
            self.indent_sexp()
            self.newline()
            field99 = unwrapped_fields98[0]
            _t746 = self.pretty_relation_id(field99)
            self.newline()
            field100 = unwrapped_fields98[1]
            _t747 = self.pretty_abstraction(field100)
            field101 = unwrapped_fields98[2]
            if field101 is not None:
                self.newline()
                assert field101 is not None
                opt_val102 = field101
                _t749 = self.pretty_attrs(opt_val102)
                _t748 = _t749
            else:
                _t748 = None
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat106 = self._try_flat(msg, self.pretty_relation_id)
        if flat106 is not None:
            assert flat106 is not None
            self.write(flat106)
            return None
        else:
            def _t750(_dollar_dollar):
                _t751 = self.deconstruct_relation_id_string(_dollar_dollar)
                return _t751
            _t752 = _t750(msg)
            deconstruct_result105 = _t752
            if deconstruct_result105 is not None:
                self.write(":")
                self.write(deconstruct_result105)
            else:
                def _t753(_dollar_dollar):
                    _t754 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                    return _t754
                _t755 = _t753(msg)
                deconstruct_result104 = _t755
                if deconstruct_result104 is not None:
                    self.write(self.format_uint128(deconstruct_result104))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat111 = self._try_flat(msg, self.pretty_abstraction)
        if flat111 is not None:
            assert flat111 is not None
            self.write(flat111)
            return None
        else:
            def _t756(_dollar_dollar):
                _t757 = self.deconstruct_bindings(_dollar_dollar)
                return (_t757, _dollar_dollar.value,)
            _t758 = _t756(msg)
            fields107 = _t758
            assert fields107 is not None
            unwrapped_fields108 = fields107
            self.write("(")
            self.indent()
            field109 = unwrapped_fields108[0]
            _t759 = self.pretty_bindings(field109)
            self.newline()
            field110 = unwrapped_fields108[1]
            _t760 = self.pretty_formula(field110)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat119 = self._try_flat(msg, self.pretty_bindings)
        if flat119 is not None:
            assert flat119 is not None
            self.write(flat119)
            return None
        else:
            def _t761(_dollar_dollar):
                if not len(_dollar_dollar[1]) == 0:
                    _t762 = _dollar_dollar[1]
                else:
                    _t762 = None
                return (_dollar_dollar[0], _t762,)
            _t763 = _t761(msg)
            fields112 = _t763
            assert fields112 is not None
            unwrapped_fields113 = fields112
            self.write("[")
            self.indent()
            field114 = unwrapped_fields113[0]
            for i116, elem115 in enumerate(field114):
                if (i116 > 0):
                    self.newline()
                _t764 = self.pretty_binding(elem115)
            field117 = unwrapped_fields113[1]
            if field117 is not None:
                self.newline()
                assert field117 is not None
                opt_val118 = field117
                _t766 = self.pretty_value_bindings(opt_val118)
                _t765 = _t766
            else:
                _t765 = None
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat124 = self._try_flat(msg, self.pretty_binding)
        if flat124 is not None:
            assert flat124 is not None
            self.write(flat124)
            return None
        else:
            def _t768(_dollar_dollar):
                return (_dollar_dollar.var.name, _dollar_dollar.type,)
            _t769 = _t768(msg)
            fields120 = _t769
            assert fields120 is not None
            unwrapped_fields121 = fields120
            field122 = unwrapped_fields121[0]
            self.write(field122)
            self.write("::")
            field123 = unwrapped_fields121[1]
            _t770 = self.pretty_type(field123)
            _t767 = _t770

    def pretty_type(self, msg: logic_pb2.Type):
        flat136 = self._try_flat(msg, self.pretty_type)
        if flat136 is not None:
            assert flat136 is not None
            self.write(flat136)
            return None
        else:
            def _t772(_dollar_dollar):
                if _dollar_dollar.HasField("unspecified_type"):
                    _t773 = _dollar_dollar.unspecified_type
                else:
                    _t773 = None
                return _t773
            _t774 = _t772(msg)
            deconstruct_result135 = _t774
            if deconstruct_result135 is not None:
                _t776 = self.pretty_unspecified_type(deconstruct_result135)
                _t775 = _t776
            else:
                def _t777(_dollar_dollar):
                    if _dollar_dollar.HasField("string_type"):
                        _t778 = _dollar_dollar.string_type
                    else:
                        _t778 = None
                    return _t778
                _t779 = _t777(msg)
                deconstruct_result134 = _t779
                if deconstruct_result134 is not None:
                    _t781 = self.pretty_string_type(deconstruct_result134)
                    _t780 = _t781
                else:
                    def _t782(_dollar_dollar):
                        if _dollar_dollar.HasField("int_type"):
                            _t783 = _dollar_dollar.int_type
                        else:
                            _t783 = None
                        return _t783
                    _t784 = _t782(msg)
                    deconstruct_result133 = _t784
                    if deconstruct_result133 is not None:
                        _t786 = self.pretty_int_type(deconstruct_result133)
                        _t785 = _t786
                    else:
                        def _t787(_dollar_dollar):
                            if _dollar_dollar.HasField("float_type"):
                                _t788 = _dollar_dollar.float_type
                            else:
                                _t788 = None
                            return _t788
                        _t789 = _t787(msg)
                        deconstruct_result132 = _t789
                        if deconstruct_result132 is not None:
                            _t791 = self.pretty_float_type(deconstruct_result132)
                            _t790 = _t791
                        else:
                            def _t792(_dollar_dollar):
                                if _dollar_dollar.HasField("uint128_type"):
                                    _t793 = _dollar_dollar.uint128_type
                                else:
                                    _t793 = None
                                return _t793
                            _t794 = _t792(msg)
                            deconstruct_result131 = _t794
                            if deconstruct_result131 is not None:
                                _t796 = self.pretty_uint128_type(deconstruct_result131)
                                _t795 = _t796
                            else:
                                def _t797(_dollar_dollar):
                                    if _dollar_dollar.HasField("int128_type"):
                                        _t798 = _dollar_dollar.int128_type
                                    else:
                                        _t798 = None
                                    return _t798
                                _t799 = _t797(msg)
                                deconstruct_result130 = _t799
                                if deconstruct_result130 is not None:
                                    _t801 = self.pretty_int128_type(deconstruct_result130)
                                    _t800 = _t801
                                else:
                                    def _t802(_dollar_dollar):
                                        if _dollar_dollar.HasField("date_type"):
                                            _t803 = _dollar_dollar.date_type
                                        else:
                                            _t803 = None
                                        return _t803
                                    _t804 = _t802(msg)
                                    deconstruct_result129 = _t804
                                    if deconstruct_result129 is not None:
                                        _t806 = self.pretty_date_type(deconstruct_result129)
                                        _t805 = _t806
                                    else:
                                        def _t807(_dollar_dollar):
                                            if _dollar_dollar.HasField("datetime_type"):
                                                _t808 = _dollar_dollar.datetime_type
                                            else:
                                                _t808 = None
                                            return _t808
                                        _t809 = _t807(msg)
                                        deconstruct_result128 = _t809
                                        if deconstruct_result128 is not None:
                                            _t811 = self.pretty_datetime_type(deconstruct_result128)
                                            _t810 = _t811
                                        else:
                                            def _t812(_dollar_dollar):
                                                if _dollar_dollar.HasField("missing_type"):
                                                    _t813 = _dollar_dollar.missing_type
                                                else:
                                                    _t813 = None
                                                return _t813
                                            _t814 = _t812(msg)
                                            deconstruct_result127 = _t814
                                            if deconstruct_result127 is not None:
                                                _t816 = self.pretty_missing_type(deconstruct_result127)
                                                _t815 = _t816
                                            else:
                                                def _t817(_dollar_dollar):
                                                    if _dollar_dollar.HasField("decimal_type"):
                                                        _t818 = _dollar_dollar.decimal_type
                                                    else:
                                                        _t818 = None
                                                    return _t818
                                                _t819 = _t817(msg)
                                                deconstruct_result126 = _t819
                                                if deconstruct_result126 is not None:
                                                    _t821 = self.pretty_decimal_type(deconstruct_result126)
                                                    _t820 = _t821
                                                else:
                                                    def _t822(_dollar_dollar):
                                                        if _dollar_dollar.HasField("boolean_type"):
                                                            _t823 = _dollar_dollar.boolean_type
                                                        else:
                                                            _t823 = None
                                                        return _t823
                                                    _t824 = _t822(msg)
                                                    deconstruct_result125 = _t824
                                                    if deconstruct_result125 is not None:
                                                        _t826 = self.pretty_boolean_type(deconstruct_result125)
                                                        _t825 = _t826
                                                    else:
                                                        raise ParseError("No matching rule for type")
                                                    _t820 = _t825
                                                _t815 = _t820
                                            _t810 = _t815
                                        _t805 = _t810
                                    _t800 = _t805
                                _t795 = _t800
                            _t790 = _t795
                        _t785 = _t790
                    _t780 = _t785
                _t775 = _t780
            _t771 = _t775

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        flat139 = self._try_flat(msg, self.pretty_unspecified_type)
        if flat139 is not None:
            assert flat139 is not None
            self.write(flat139)
            return None
        else:
            def _t827(_dollar_dollar):
                return _dollar_dollar
            _t828 = _t827(msg)
            fields137 = _t828
            assert fields137 is not None
            unwrapped_fields138 = fields137
            self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        flat142 = self._try_flat(msg, self.pretty_string_type)
        if flat142 is not None:
            assert flat142 is not None
            self.write(flat142)
            return None
        else:
            def _t829(_dollar_dollar):
                return _dollar_dollar
            _t830 = _t829(msg)
            fields140 = _t830
            assert fields140 is not None
            unwrapped_fields141 = fields140
            self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        flat145 = self._try_flat(msg, self.pretty_int_type)
        if flat145 is not None:
            assert flat145 is not None
            self.write(flat145)
            return None
        else:
            def _t831(_dollar_dollar):
                return _dollar_dollar
            _t832 = _t831(msg)
            fields143 = _t832
            assert fields143 is not None
            unwrapped_fields144 = fields143
            self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        flat148 = self._try_flat(msg, self.pretty_float_type)
        if flat148 is not None:
            assert flat148 is not None
            self.write(flat148)
            return None
        else:
            def _t833(_dollar_dollar):
                return _dollar_dollar
            _t834 = _t833(msg)
            fields146 = _t834
            assert fields146 is not None
            unwrapped_fields147 = fields146
            self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        flat151 = self._try_flat(msg, self.pretty_uint128_type)
        if flat151 is not None:
            assert flat151 is not None
            self.write(flat151)
            return None
        else:
            def _t835(_dollar_dollar):
                return _dollar_dollar
            _t836 = _t835(msg)
            fields149 = _t836
            assert fields149 is not None
            unwrapped_fields150 = fields149
            self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        flat154 = self._try_flat(msg, self.pretty_int128_type)
        if flat154 is not None:
            assert flat154 is not None
            self.write(flat154)
            return None
        else:
            def _t837(_dollar_dollar):
                return _dollar_dollar
            _t838 = _t837(msg)
            fields152 = _t838
            assert fields152 is not None
            unwrapped_fields153 = fields152
            self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        flat157 = self._try_flat(msg, self.pretty_date_type)
        if flat157 is not None:
            assert flat157 is not None
            self.write(flat157)
            return None
        else:
            def _t839(_dollar_dollar):
                return _dollar_dollar
            _t840 = _t839(msg)
            fields155 = _t840
            assert fields155 is not None
            unwrapped_fields156 = fields155
            self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        flat160 = self._try_flat(msg, self.pretty_datetime_type)
        if flat160 is not None:
            assert flat160 is not None
            self.write(flat160)
            return None
        else:
            def _t841(_dollar_dollar):
                return _dollar_dollar
            _t842 = _t841(msg)
            fields158 = _t842
            assert fields158 is not None
            unwrapped_fields159 = fields158
            self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        flat163 = self._try_flat(msg, self.pretty_missing_type)
        if flat163 is not None:
            assert flat163 is not None
            self.write(flat163)
            return None
        else:
            def _t843(_dollar_dollar):
                return _dollar_dollar
            _t844 = _t843(msg)
            fields161 = _t844
            assert fields161 is not None
            unwrapped_fields162 = fields161
            self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat168 = self._try_flat(msg, self.pretty_decimal_type)
        if flat168 is not None:
            assert flat168 is not None
            self.write(flat168)
            return None
        else:
            def _t845(_dollar_dollar):
                return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            _t846 = _t845(msg)
            fields164 = _t846
            assert fields164 is not None
            unwrapped_fields165 = fields164
            self.write("(")
            self.write("DECIMAL")
            self.indent_sexp()
            self.newline()
            field166 = unwrapped_fields165[0]
            self.write(str(field166))
            self.newline()
            field167 = unwrapped_fields165[1]
            self.write(str(field167))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        flat171 = self._try_flat(msg, self.pretty_boolean_type)
        if flat171 is not None:
            assert flat171 is not None
            self.write(flat171)
            return None
        else:
            def _t847(_dollar_dollar):
                return _dollar_dollar
            _t848 = _t847(msg)
            fields169 = _t848
            assert fields169 is not None
            unwrapped_fields170 = fields169
            self.write("BOOLEAN")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat176 = self._try_flat(msg, self.pretty_value_bindings)
        if flat176 is not None:
            assert flat176 is not None
            self.write(flat176)
            return None
        else:
            def _t849(_dollar_dollar):
                return _dollar_dollar
            _t850 = _t849(msg)
            fields172 = _t850
            assert fields172 is not None
            unwrapped_fields173 = fields172
            self.write("|")
            if not len(unwrapped_fields173) == 0:
                self.write(" ")
                for i175, elem174 in enumerate(unwrapped_fields173):
                    if (i175 > 0):
                        self.newline()
                    _t851 = self.pretty_binding(elem174)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat190 = self._try_flat(msg, self.pretty_formula)
        if flat190 is not None:
            assert flat190 is not None
            self.write(flat190)
            return None
        else:
            def _t853(_dollar_dollar):
                if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                    _t854 = _dollar_dollar.conjunction
                else:
                    _t854 = None
                return _t854
            _t855 = _t853(msg)
            deconstruct_result189 = _t855
            if deconstruct_result189 is not None:
                _t857 = self.pretty_true(deconstruct_result189)
                _t856 = _t857
            else:
                def _t858(_dollar_dollar):
                    if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                        _t859 = _dollar_dollar.disjunction
                    else:
                        _t859 = None
                    return _t859
                _t860 = _t858(msg)
                deconstruct_result188 = _t860
                if deconstruct_result188 is not None:
                    _t862 = self.pretty_false(deconstruct_result188)
                    _t861 = _t862
                else:
                    def _t863(_dollar_dollar):
                        if _dollar_dollar.HasField("exists"):
                            _t864 = _dollar_dollar.exists
                        else:
                            _t864 = None
                        return _t864
                    _t865 = _t863(msg)
                    deconstruct_result187 = _t865
                    if deconstruct_result187 is not None:
                        _t867 = self.pretty_exists(deconstruct_result187)
                        _t866 = _t867
                    else:
                        def _t868(_dollar_dollar):
                            if _dollar_dollar.HasField("reduce"):
                                _t869 = _dollar_dollar.reduce
                            else:
                                _t869 = None
                            return _t869
                        _t870 = _t868(msg)
                        deconstruct_result186 = _t870
                        if deconstruct_result186 is not None:
                            _t872 = self.pretty_reduce(deconstruct_result186)
                            _t871 = _t872
                        else:
                            def _t873(_dollar_dollar):
                                if _dollar_dollar.HasField("conjunction"):
                                    _t874 = _dollar_dollar.conjunction
                                else:
                                    _t874 = None
                                return _t874
                            _t875 = _t873(msg)
                            deconstruct_result185 = _t875
                            if deconstruct_result185 is not None:
                                _t877 = self.pretty_conjunction(deconstruct_result185)
                                _t876 = _t877
                            else:
                                def _t878(_dollar_dollar):
                                    if _dollar_dollar.HasField("disjunction"):
                                        _t879 = _dollar_dollar.disjunction
                                    else:
                                        _t879 = None
                                    return _t879
                                _t880 = _t878(msg)
                                deconstruct_result184 = _t880
                                if deconstruct_result184 is not None:
                                    _t882 = self.pretty_disjunction(deconstruct_result184)
                                    _t881 = _t882
                                else:
                                    def _t883(_dollar_dollar):
                                        if _dollar_dollar.HasField("not"):
                                            _t884 = getattr(_dollar_dollar, 'not')
                                        else:
                                            _t884 = None
                                        return _t884
                                    _t885 = _t883(msg)
                                    deconstruct_result183 = _t885
                                    if deconstruct_result183 is not None:
                                        _t887 = self.pretty_not(deconstruct_result183)
                                        _t886 = _t887
                                    else:
                                        def _t888(_dollar_dollar):
                                            if _dollar_dollar.HasField("ffi"):
                                                _t889 = _dollar_dollar.ffi
                                            else:
                                                _t889 = None
                                            return _t889
                                        _t890 = _t888(msg)
                                        deconstruct_result182 = _t890
                                        if deconstruct_result182 is not None:
                                            _t892 = self.pretty_ffi(deconstruct_result182)
                                            _t891 = _t892
                                        else:
                                            def _t893(_dollar_dollar):
                                                if _dollar_dollar.HasField("atom"):
                                                    _t894 = _dollar_dollar.atom
                                                else:
                                                    _t894 = None
                                                return _t894
                                            _t895 = _t893(msg)
                                            deconstruct_result181 = _t895
                                            if deconstruct_result181 is not None:
                                                _t897 = self.pretty_atom(deconstruct_result181)
                                                _t896 = _t897
                                            else:
                                                def _t898(_dollar_dollar):
                                                    if _dollar_dollar.HasField("pragma"):
                                                        _t899 = _dollar_dollar.pragma
                                                    else:
                                                        _t899 = None
                                                    return _t899
                                                _t900 = _t898(msg)
                                                deconstruct_result180 = _t900
                                                if deconstruct_result180 is not None:
                                                    _t902 = self.pretty_pragma(deconstruct_result180)
                                                    _t901 = _t902
                                                else:
                                                    def _t903(_dollar_dollar):
                                                        if _dollar_dollar.HasField("primitive"):
                                                            _t904 = _dollar_dollar.primitive
                                                        else:
                                                            _t904 = None
                                                        return _t904
                                                    _t905 = _t903(msg)
                                                    deconstruct_result179 = _t905
                                                    if deconstruct_result179 is not None:
                                                        _t907 = self.pretty_primitive(deconstruct_result179)
                                                        _t906 = _t907
                                                    else:
                                                        def _t908(_dollar_dollar):
                                                            if _dollar_dollar.HasField("rel_atom"):
                                                                _t909 = _dollar_dollar.rel_atom
                                                            else:
                                                                _t909 = None
                                                            return _t909
                                                        _t910 = _t908(msg)
                                                        deconstruct_result178 = _t910
                                                        if deconstruct_result178 is not None:
                                                            _t912 = self.pretty_rel_atom(deconstruct_result178)
                                                            _t911 = _t912
                                                        else:
                                                            def _t913(_dollar_dollar):
                                                                if _dollar_dollar.HasField("cast"):
                                                                    _t914 = _dollar_dollar.cast
                                                                else:
                                                                    _t914 = None
                                                                return _t914
                                                            _t915 = _t913(msg)
                                                            deconstruct_result177 = _t915
                                                            if deconstruct_result177 is not None:
                                                                _t917 = self.pretty_cast(deconstruct_result177)
                                                                _t916 = _t917
                                                            else:
                                                                raise ParseError("No matching rule for formula")
                                                            _t911 = _t916
                                                        _t906 = _t911
                                                    _t901 = _t906
                                                _t896 = _t901
                                            _t891 = _t896
                                        _t886 = _t891
                                    _t881 = _t886
                                _t876 = _t881
                            _t871 = _t876
                        _t866 = _t871
                    _t861 = _t866
                _t856 = _t861
            _t852 = _t856

    def pretty_true(self, msg: logic_pb2.Conjunction):
        flat193 = self._try_flat(msg, self.pretty_true)
        if flat193 is not None:
            assert flat193 is not None
            self.write(flat193)
            return None
        else:
            def _t918(_dollar_dollar):
                return _dollar_dollar
            _t919 = _t918(msg)
            fields191 = _t919
            assert fields191 is not None
            unwrapped_fields192 = fields191
            self.write("(")
            self.write("true")
            self.write(")")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        flat196 = self._try_flat(msg, self.pretty_false)
        if flat196 is not None:
            assert flat196 is not None
            self.write(flat196)
            return None
        else:
            def _t920(_dollar_dollar):
                return _dollar_dollar
            _t921 = _t920(msg)
            fields194 = _t921
            assert fields194 is not None
            unwrapped_fields195 = fields194
            self.write("(")
            self.write("false")
            self.write(")")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat201 = self._try_flat(msg, self.pretty_exists)
        if flat201 is not None:
            assert flat201 is not None
            self.write(flat201)
            return None
        else:
            def _t922(_dollar_dollar):
                _t923 = self.deconstruct_bindings(_dollar_dollar.body)
                return (_t923, _dollar_dollar.body.value,)
            _t924 = _t922(msg)
            fields197 = _t924
            assert fields197 is not None
            unwrapped_fields198 = fields197
            self.write("(")
            self.write("exists")
            self.indent_sexp()
            self.newline()
            field199 = unwrapped_fields198[0]
            _t925 = self.pretty_bindings(field199)
            self.newline()
            field200 = unwrapped_fields198[1]
            _t926 = self.pretty_formula(field200)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat207 = self._try_flat(msg, self.pretty_reduce)
        if flat207 is not None:
            assert flat207 is not None
            self.write(flat207)
            return None
        else:
            def _t927(_dollar_dollar):
                return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            _t928 = _t927(msg)
            fields202 = _t928
            assert fields202 is not None
            unwrapped_fields203 = fields202
            self.write("(")
            self.write("reduce")
            self.indent_sexp()
            self.newline()
            field204 = unwrapped_fields203[0]
            _t929 = self.pretty_abstraction(field204)
            self.newline()
            field205 = unwrapped_fields203[1]
            _t930 = self.pretty_abstraction(field205)
            self.newline()
            field206 = unwrapped_fields203[2]
            _t931 = self.pretty_terms(field206)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat212 = self._try_flat(msg, self.pretty_terms)
        if flat212 is not None:
            assert flat212 is not None
            self.write(flat212)
            return None
        else:
            def _t932(_dollar_dollar):
                return _dollar_dollar
            _t933 = _t932(msg)
            fields208 = _t933
            assert fields208 is not None
            unwrapped_fields209 = fields208
            self.write("(")
            self.write("terms")
            self.indent_sexp()
            if not len(unwrapped_fields209) == 0:
                self.newline()
                for i211, elem210 in enumerate(unwrapped_fields209):
                    if (i211 > 0):
                        self.newline()
                    _t934 = self.pretty_term(elem210)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat215 = self._try_flat(msg, self.pretty_term)
        if flat215 is not None:
            assert flat215 is not None
            self.write(flat215)
            return None
        else:
            def _t936(_dollar_dollar):
                if _dollar_dollar.HasField("var"):
                    _t937 = _dollar_dollar.var
                else:
                    _t937 = None
                return _t937
            _t938 = _t936(msg)
            deconstruct_result214 = _t938
            if deconstruct_result214 is not None:
                _t940 = self.pretty_var(deconstruct_result214)
                _t939 = _t940
            else:
                def _t941(_dollar_dollar):
                    if _dollar_dollar.HasField("constant"):
                        _t942 = _dollar_dollar.constant
                    else:
                        _t942 = None
                    return _t942
                _t943 = _t941(msg)
                deconstruct_result213 = _t943
                if deconstruct_result213 is not None:
                    _t945 = self.pretty_constant(deconstruct_result213)
                    _t944 = _t945
                else:
                    raise ParseError("No matching rule for term")
                _t939 = _t944
            _t935 = _t939

    def pretty_var(self, msg: logic_pb2.Var):
        flat218 = self._try_flat(msg, self.pretty_var)
        if flat218 is not None:
            assert flat218 is not None
            self.write(flat218)
            return None
        else:
            def _t946(_dollar_dollar):
                return _dollar_dollar.name
            _t947 = _t946(msg)
            fields216 = _t947
            assert fields216 is not None
            unwrapped_fields217 = fields216
            self.write(unwrapped_fields217)

    def pretty_constant(self, msg: logic_pb2.Value):
        flat221 = self._try_flat(msg, self.pretty_constant)
        if flat221 is not None:
            assert flat221 is not None
            self.write(flat221)
            return None
        else:
            def _t949(_dollar_dollar):
                return _dollar_dollar
            _t950 = _t949(msg)
            fields219 = _t950
            assert fields219 is not None
            unwrapped_fields220 = fields219
            _t951 = self.pretty_value(unwrapped_fields220)
            _t948 = _t951

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat226 = self._try_flat(msg, self.pretty_conjunction)
        if flat226 is not None:
            assert flat226 is not None
            self.write(flat226)
            return None
        else:
            def _t952(_dollar_dollar):
                return _dollar_dollar.args
            _t953 = _t952(msg)
            fields222 = _t953
            assert fields222 is not None
            unwrapped_fields223 = fields222
            self.write("(")
            self.write("and")
            self.indent_sexp()
            if not len(unwrapped_fields223) == 0:
                self.newline()
                for i225, elem224 in enumerate(unwrapped_fields223):
                    if (i225 > 0):
                        self.newline()
                    _t954 = self.pretty_formula(elem224)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat231 = self._try_flat(msg, self.pretty_disjunction)
        if flat231 is not None:
            assert flat231 is not None
            self.write(flat231)
            return None
        else:
            def _t955(_dollar_dollar):
                return _dollar_dollar.args
            _t956 = _t955(msg)
            fields227 = _t956
            assert fields227 is not None
            unwrapped_fields228 = fields227
            self.write("(")
            self.write("or")
            self.indent_sexp()
            if not len(unwrapped_fields228) == 0:
                self.newline()
                for i230, elem229 in enumerate(unwrapped_fields228):
                    if (i230 > 0):
                        self.newline()
                    _t957 = self.pretty_formula(elem229)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat234 = self._try_flat(msg, self.pretty_not)
        if flat234 is not None:
            assert flat234 is not None
            self.write(flat234)
            return None
        else:
            def _t958(_dollar_dollar):
                return _dollar_dollar.arg
            _t959 = _t958(msg)
            fields232 = _t959
            assert fields232 is not None
            unwrapped_fields233 = fields232
            self.write("(")
            self.write("not")
            self.indent_sexp()
            self.newline()
            _t960 = self.pretty_formula(unwrapped_fields233)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat240 = self._try_flat(msg, self.pretty_ffi)
        if flat240 is not None:
            assert flat240 is not None
            self.write(flat240)
            return None
        else:
            def _t961(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            _t962 = _t961(msg)
            fields235 = _t962
            assert fields235 is not None
            unwrapped_fields236 = fields235
            self.write("(")
            self.write("ffi")
            self.indent_sexp()
            self.newline()
            field237 = unwrapped_fields236[0]
            _t963 = self.pretty_name(field237)
            self.newline()
            field238 = unwrapped_fields236[1]
            _t964 = self.pretty_ffi_args(field238)
            self.newline()
            field239 = unwrapped_fields236[2]
            _t965 = self.pretty_terms(field239)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat243 = self._try_flat(msg, self.pretty_name)
        if flat243 is not None:
            assert flat243 is not None
            self.write(flat243)
            return None
        else:
            def _t966(_dollar_dollar):
                return _dollar_dollar
            _t967 = _t966(msg)
            fields241 = _t967
            assert fields241 is not None
            unwrapped_fields242 = fields241
            self.write(":")
            self.write(unwrapped_fields242)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat248 = self._try_flat(msg, self.pretty_ffi_args)
        if flat248 is not None:
            assert flat248 is not None
            self.write(flat248)
            return None
        else:
            def _t968(_dollar_dollar):
                return _dollar_dollar
            _t969 = _t968(msg)
            fields244 = _t969
            assert fields244 is not None
            unwrapped_fields245 = fields244
            self.write("(")
            self.write("args")
            self.indent_sexp()
            if not len(unwrapped_fields245) == 0:
                self.newline()
                for i247, elem246 in enumerate(unwrapped_fields245):
                    if (i247 > 0):
                        self.newline()
                    _t970 = self.pretty_abstraction(elem246)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat255 = self._try_flat(msg, self.pretty_atom)
        if flat255 is not None:
            assert flat255 is not None
            self.write(flat255)
            return None
        else:
            def _t971(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t972 = _t971(msg)
            fields249 = _t972
            assert fields249 is not None
            unwrapped_fields250 = fields249
            self.write("(")
            self.write("atom")
            self.indent_sexp()
            self.newline()
            field251 = unwrapped_fields250[0]
            _t973 = self.pretty_relation_id(field251)
            field252 = unwrapped_fields250[1]
            if not len(field252) == 0:
                self.newline()
                for i254, elem253 in enumerate(field252):
                    if (i254 > 0):
                        self.newline()
                    _t974 = self.pretty_term(elem253)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat262 = self._try_flat(msg, self.pretty_pragma)
        if flat262 is not None:
            assert flat262 is not None
            self.write(flat262)
            return None
        else:
            def _t975(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t976 = _t975(msg)
            fields256 = _t976
            assert fields256 is not None
            unwrapped_fields257 = fields256
            self.write("(")
            self.write("pragma")
            self.indent_sexp()
            self.newline()
            field258 = unwrapped_fields257[0]
            _t977 = self.pretty_name(field258)
            field259 = unwrapped_fields257[1]
            if not len(field259) == 0:
                self.newline()
                for i261, elem260 in enumerate(field259):
                    if (i261 > 0):
                        self.newline()
                    _t978 = self.pretty_term(elem260)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat278 = self._try_flat(msg, self.pretty_primitive)
        if flat278 is not None:
            assert flat278 is not None
            self.write(flat278)
            return None
        else:
            def _t980(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t981 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t981 = None
                return _t981
            _t982 = _t980(msg)
            guard_result277 = _t982
            if guard_result277 is not None:
                _t984 = self.pretty_eq(msg)
                _t983 = _t984
            else:
                def _t985(_dollar_dollar):
                    if _dollar_dollar.name == "rel_primitive_lt_monotype":
                        _t986 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t986 = None
                    return _t986
                _t987 = _t985(msg)
                guard_result276 = _t987
                if guard_result276 is not None:
                    _t989 = self.pretty_lt(msg)
                    _t988 = _t989
                else:
                    def _t990(_dollar_dollar):
                        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                            _t991 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t991 = None
                        return _t991
                    _t992 = _t990(msg)
                    guard_result275 = _t992
                    if guard_result275 is not None:
                        _t994 = self.pretty_lt_eq(msg)
                        _t993 = _t994
                    else:
                        def _t995(_dollar_dollar):
                            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                                _t996 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t996 = None
                            return _t996
                        _t997 = _t995(msg)
                        guard_result274 = _t997
                        if guard_result274 is not None:
                            _t999 = self.pretty_gt(msg)
                            _t998 = _t999
                        else:
                            def _t1000(_dollar_dollar):
                                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                    _t1001 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                                else:
                                    _t1001 = None
                                return _t1001
                            _t1002 = _t1000(msg)
                            guard_result273 = _t1002
                            if guard_result273 is not None:
                                _t1004 = self.pretty_gt_eq(msg)
                                _t1003 = _t1004
                            else:
                                def _t1005(_dollar_dollar):
                                    if _dollar_dollar.name == "rel_primitive_add_monotype":
                                        _t1006 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1006 = None
                                    return _t1006
                                _t1007 = _t1005(msg)
                                guard_result272 = _t1007
                                if guard_result272 is not None:
                                    _t1009 = self.pretty_add(msg)
                                    _t1008 = _t1009
                                else:
                                    def _t1010(_dollar_dollar):
                                        if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                            _t1011 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1011 = None
                                        return _t1011
                                    _t1012 = _t1010(msg)
                                    guard_result271 = _t1012
                                    if guard_result271 is not None:
                                        _t1014 = self.pretty_minus(msg)
                                        _t1013 = _t1014
                                    else:
                                        def _t1015(_dollar_dollar):
                                            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                                _t1016 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1016 = None
                                            return _t1016
                                        _t1017 = _t1015(msg)
                                        guard_result270 = _t1017
                                        if guard_result270 is not None:
                                            _t1019 = self.pretty_multiply(msg)
                                            _t1018 = _t1019
                                        else:
                                            def _t1020(_dollar_dollar):
                                                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                    _t1021 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                                else:
                                                    _t1021 = None
                                                return _t1021
                                            _t1022 = _t1020(msg)
                                            guard_result269 = _t1022
                                            if guard_result269 is not None:
                                                _t1024 = self.pretty_divide(msg)
                                                _t1023 = _t1024
                                            else:
                                                def _t1025(_dollar_dollar):
                                                    return (_dollar_dollar.name, _dollar_dollar.terms,)
                                                _t1026 = _t1025(msg)
                                                fields263 = _t1026
                                                assert fields263 is not None
                                                unwrapped_fields264 = fields263
                                                self.write("(")
                                                self.write("primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field265 = unwrapped_fields264[0]
                                                _t1027 = self.pretty_name(field265)
                                                field266 = unwrapped_fields264[1]
                                                if not len(field266) == 0:
                                                    self.newline()
                                                    for i268, elem267 in enumerate(field266):
                                                        if (i268 > 0):
                                                            self.newline()
                                                        _t1028 = self.pretty_rel_term(elem267)
                                                self.dedent()
                                                self.write(")")
                                                _t1023 = None
                                            _t1018 = _t1023
                                        _t1013 = _t1018
                                    _t1008 = _t1013
                                _t1003 = _t1008
                            _t998 = _t1003
                        _t993 = _t998
                    _t988 = _t993
                _t983 = _t988
            _t979 = _t983

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat283 = self._try_flat(msg, self.pretty_eq)
        if flat283 is not None:
            assert flat283 is not None
            self.write(flat283)
            return None
        else:
            def _t1029(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1030 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1030 = None
                return _t1030
            _t1031 = _t1029(msg)
            fields279 = _t1031
            assert fields279 is not None
            unwrapped_fields280 = fields279
            self.write("(")
            self.write("=")
            self.indent_sexp()
            self.newline()
            field281 = unwrapped_fields280[0]
            _t1032 = self.pretty_term(field281)
            self.newline()
            field282 = unwrapped_fields280[1]
            _t1033 = self.pretty_term(field282)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat288 = self._try_flat(msg, self.pretty_lt)
        if flat288 is not None:
            assert flat288 is not None
            self.write(flat288)
            return None
        else:
            def _t1034(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1035 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1035 = None
                return _t1035
            _t1036 = _t1034(msg)
            fields284 = _t1036
            assert fields284 is not None
            unwrapped_fields285 = fields284
            self.write("(")
            self.write("<")
            self.indent_sexp()
            self.newline()
            field286 = unwrapped_fields285[0]
            _t1037 = self.pretty_term(field286)
            self.newline()
            field287 = unwrapped_fields285[1]
            _t1038 = self.pretty_term(field287)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat293 = self._try_flat(msg, self.pretty_lt_eq)
        if flat293 is not None:
            assert flat293 is not None
            self.write(flat293)
            return None
        else:
            def _t1039(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                    _t1040 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1040 = None
                return _t1040
            _t1041 = _t1039(msg)
            fields289 = _t1041
            assert fields289 is not None
            unwrapped_fields290 = fields289
            self.write("(")
            self.write("<=")
            self.indent_sexp()
            self.newline()
            field291 = unwrapped_fields290[0]
            _t1042 = self.pretty_term(field291)
            self.newline()
            field292 = unwrapped_fields290[1]
            _t1043 = self.pretty_term(field292)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat298 = self._try_flat(msg, self.pretty_gt)
        if flat298 is not None:
            assert flat298 is not None
            self.write(flat298)
            return None
        else:
            def _t1044(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_monotype":
                    _t1045 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1045 = None
                return _t1045
            _t1046 = _t1044(msg)
            fields294 = _t1046
            assert fields294 is not None
            unwrapped_fields295 = fields294
            self.write("(")
            self.write(">")
            self.indent_sexp()
            self.newline()
            field296 = unwrapped_fields295[0]
            _t1047 = self.pretty_term(field296)
            self.newline()
            field297 = unwrapped_fields295[1]
            _t1048 = self.pretty_term(field297)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat303 = self._try_flat(msg, self.pretty_gt_eq)
        if flat303 is not None:
            assert flat303 is not None
            self.write(flat303)
            return None
        else:
            def _t1049(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                    _t1050 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1050 = None
                return _t1050
            _t1051 = _t1049(msg)
            fields299 = _t1051
            assert fields299 is not None
            unwrapped_fields300 = fields299
            self.write("(")
            self.write(">=")
            self.indent_sexp()
            self.newline()
            field301 = unwrapped_fields300[0]
            _t1052 = self.pretty_term(field301)
            self.newline()
            field302 = unwrapped_fields300[1]
            _t1053 = self.pretty_term(field302)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat309 = self._try_flat(msg, self.pretty_add)
        if flat309 is not None:
            assert flat309 is not None
            self.write(flat309)
            return None
        else:
            def _t1054(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_add_monotype":
                    _t1055 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1055 = None
                return _t1055
            _t1056 = _t1054(msg)
            fields304 = _t1056
            assert fields304 is not None
            unwrapped_fields305 = fields304
            self.write("(")
            self.write("+")
            self.indent_sexp()
            self.newline()
            field306 = unwrapped_fields305[0]
            _t1057 = self.pretty_term(field306)
            self.newline()
            field307 = unwrapped_fields305[1]
            _t1058 = self.pretty_term(field307)
            self.newline()
            field308 = unwrapped_fields305[2]
            _t1059 = self.pretty_term(field308)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat315 = self._try_flat(msg, self.pretty_minus)
        if flat315 is not None:
            assert flat315 is not None
            self.write(flat315)
            return None
        else:
            def _t1060(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                    _t1061 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1061 = None
                return _t1061
            _t1062 = _t1060(msg)
            fields310 = _t1062
            assert fields310 is not None
            unwrapped_fields311 = fields310
            self.write("(")
            self.write("-")
            self.indent_sexp()
            self.newline()
            field312 = unwrapped_fields311[0]
            _t1063 = self.pretty_term(field312)
            self.newline()
            field313 = unwrapped_fields311[1]
            _t1064 = self.pretty_term(field313)
            self.newline()
            field314 = unwrapped_fields311[2]
            _t1065 = self.pretty_term(field314)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat321 = self._try_flat(msg, self.pretty_multiply)
        if flat321 is not None:
            assert flat321 is not None
            self.write(flat321)
            return None
        else:
            def _t1066(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                    _t1067 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1067 = None
                return _t1067
            _t1068 = _t1066(msg)
            fields316 = _t1068
            assert fields316 is not None
            unwrapped_fields317 = fields316
            self.write("(")
            self.write("*")
            self.indent_sexp()
            self.newline()
            field318 = unwrapped_fields317[0]
            _t1069 = self.pretty_term(field318)
            self.newline()
            field319 = unwrapped_fields317[1]
            _t1070 = self.pretty_term(field319)
            self.newline()
            field320 = unwrapped_fields317[2]
            _t1071 = self.pretty_term(field320)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat327 = self._try_flat(msg, self.pretty_divide)
        if flat327 is not None:
            assert flat327 is not None
            self.write(flat327)
            return None
        else:
            def _t1072(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                    _t1073 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1073 = None
                return _t1073
            _t1074 = _t1072(msg)
            fields322 = _t1074
            assert fields322 is not None
            unwrapped_fields323 = fields322
            self.write("(")
            self.write("/")
            self.indent_sexp()
            self.newline()
            field324 = unwrapped_fields323[0]
            _t1075 = self.pretty_term(field324)
            self.newline()
            field325 = unwrapped_fields323[1]
            _t1076 = self.pretty_term(field325)
            self.newline()
            field326 = unwrapped_fields323[2]
            _t1077 = self.pretty_term(field326)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat330 = self._try_flat(msg, self.pretty_rel_term)
        if flat330 is not None:
            assert flat330 is not None
            self.write(flat330)
            return None
        else:
            def _t1079(_dollar_dollar):
                if _dollar_dollar.HasField("specialized_value"):
                    _t1080 = _dollar_dollar.specialized_value
                else:
                    _t1080 = None
                return _t1080
            _t1081 = _t1079(msg)
            deconstruct_result329 = _t1081
            if deconstruct_result329 is not None:
                _t1083 = self.pretty_specialized_value(deconstruct_result329)
                _t1082 = _t1083
            else:
                def _t1084(_dollar_dollar):
                    if _dollar_dollar.HasField("term"):
                        _t1085 = _dollar_dollar.term
                    else:
                        _t1085 = None
                    return _t1085
                _t1086 = _t1084(msg)
                deconstruct_result328 = _t1086
                if deconstruct_result328 is not None:
                    _t1088 = self.pretty_term(deconstruct_result328)
                    _t1087 = _t1088
                else:
                    raise ParseError("No matching rule for rel_term")
                _t1082 = _t1087
            _t1078 = _t1082

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat333 = self._try_flat(msg, self.pretty_specialized_value)
        if flat333 is not None:
            assert flat333 is not None
            self.write(flat333)
            return None
        else:
            def _t1090(_dollar_dollar):
                return _dollar_dollar
            _t1091 = _t1090(msg)
            fields331 = _t1091
            assert fields331 is not None
            unwrapped_fields332 = fields331
            self.write("#")
            _t1092 = self.pretty_value(unwrapped_fields332)
            _t1089 = _t1092

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat340 = self._try_flat(msg, self.pretty_rel_atom)
        if flat340 is not None:
            assert flat340 is not None
            self.write(flat340)
            return None
        else:
            def _t1093(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1094 = _t1093(msg)
            fields334 = _t1094
            assert fields334 is not None
            unwrapped_fields335 = fields334
            self.write("(")
            self.write("relatom")
            self.indent_sexp()
            self.newline()
            field336 = unwrapped_fields335[0]
            _t1095 = self.pretty_name(field336)
            field337 = unwrapped_fields335[1]
            if not len(field337) == 0:
                self.newline()
                for i339, elem338 in enumerate(field337):
                    if (i339 > 0):
                        self.newline()
                    _t1096 = self.pretty_rel_term(elem338)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat345 = self._try_flat(msg, self.pretty_cast)
        if flat345 is not None:
            assert flat345 is not None
            self.write(flat345)
            return None
        else:
            def _t1097(_dollar_dollar):
                return (_dollar_dollar.input, _dollar_dollar.result,)
            _t1098 = _t1097(msg)
            fields341 = _t1098
            assert fields341 is not None
            unwrapped_fields342 = fields341
            self.write("(")
            self.write("cast")
            self.indent_sexp()
            self.newline()
            field343 = unwrapped_fields342[0]
            _t1099 = self.pretty_term(field343)
            self.newline()
            field344 = unwrapped_fields342[1]
            _t1100 = self.pretty_term(field344)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat350 = self._try_flat(msg, self.pretty_attrs)
        if flat350 is not None:
            assert flat350 is not None
            self.write(flat350)
            return None
        else:
            def _t1101(_dollar_dollar):
                return _dollar_dollar
            _t1102 = _t1101(msg)
            fields346 = _t1102
            assert fields346 is not None
            unwrapped_fields347 = fields346
            self.write("(")
            self.write("attrs")
            self.indent_sexp()
            if not len(unwrapped_fields347) == 0:
                self.newline()
                for i349, elem348 in enumerate(unwrapped_fields347):
                    if (i349 > 0):
                        self.newline()
                    _t1103 = self.pretty_attribute(elem348)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat357 = self._try_flat(msg, self.pretty_attribute)
        if flat357 is not None:
            assert flat357 is not None
            self.write(flat357)
            return None
        else:
            def _t1104(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args,)
            _t1105 = _t1104(msg)
            fields351 = _t1105
            assert fields351 is not None
            unwrapped_fields352 = fields351
            self.write("(")
            self.write("attribute")
            self.indent_sexp()
            self.newline()
            field353 = unwrapped_fields352[0]
            _t1106 = self.pretty_name(field353)
            field354 = unwrapped_fields352[1]
            if not len(field354) == 0:
                self.newline()
                for i356, elem355 in enumerate(field354):
                    if (i356 > 0):
                        self.newline()
                    _t1107 = self.pretty_value(elem355)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat364 = self._try_flat(msg, self.pretty_algorithm)
        if flat364 is not None:
            assert flat364 is not None
            self.write(flat364)
            return None
        else:
            def _t1108(_dollar_dollar):
                return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            _t1109 = _t1108(msg)
            fields358 = _t1109
            assert fields358 is not None
            unwrapped_fields359 = fields358
            self.write("(")
            self.write("algorithm")
            self.indent_sexp()
            field360 = unwrapped_fields359[0]
            if not len(field360) == 0:
                self.newline()
                for i362, elem361 in enumerate(field360):
                    if (i362 > 0):
                        self.newline()
                    _t1110 = self.pretty_relation_id(elem361)
            self.newline()
            field363 = unwrapped_fields359[1]
            _t1111 = self.pretty_script(field363)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat369 = self._try_flat(msg, self.pretty_script)
        if flat369 is not None:
            assert flat369 is not None
            self.write(flat369)
            return None
        else:
            def _t1112(_dollar_dollar):
                return _dollar_dollar.constructs
            _t1113 = _t1112(msg)
            fields365 = _t1113
            assert fields365 is not None
            unwrapped_fields366 = fields365
            self.write("(")
            self.write("script")
            self.indent_sexp()
            if not len(unwrapped_fields366) == 0:
                self.newline()
                for i368, elem367 in enumerate(unwrapped_fields366):
                    if (i368 > 0):
                        self.newline()
                    _t1114 = self.pretty_construct(elem367)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat372 = self._try_flat(msg, self.pretty_construct)
        if flat372 is not None:
            assert flat372 is not None
            self.write(flat372)
            return None
        else:
            def _t1116(_dollar_dollar):
                if _dollar_dollar.HasField("loop"):
                    _t1117 = _dollar_dollar.loop
                else:
                    _t1117 = None
                return _t1117
            _t1118 = _t1116(msg)
            deconstruct_result371 = _t1118
            if deconstruct_result371 is not None:
                _t1120 = self.pretty_loop(deconstruct_result371)
                _t1119 = _t1120
            else:
                def _t1121(_dollar_dollar):
                    if _dollar_dollar.HasField("instruction"):
                        _t1122 = _dollar_dollar.instruction
                    else:
                        _t1122 = None
                    return _t1122
                _t1123 = _t1121(msg)
                deconstruct_result370 = _t1123
                if deconstruct_result370 is not None:
                    _t1125 = self.pretty_instruction(deconstruct_result370)
                    _t1124 = _t1125
                else:
                    raise ParseError("No matching rule for construct")
                _t1119 = _t1124
            _t1115 = _t1119

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat377 = self._try_flat(msg, self.pretty_loop)
        if flat377 is not None:
            assert flat377 is not None
            self.write(flat377)
            return None
        else:
            def _t1126(_dollar_dollar):
                return (_dollar_dollar.init, _dollar_dollar.body,)
            _t1127 = _t1126(msg)
            fields373 = _t1127
            assert fields373 is not None
            unwrapped_fields374 = fields373
            self.write("(")
            self.write("loop")
            self.indent_sexp()
            self.newline()
            field375 = unwrapped_fields374[0]
            _t1128 = self.pretty_init(field375)
            self.newline()
            field376 = unwrapped_fields374[1]
            _t1129 = self.pretty_script(field376)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat382 = self._try_flat(msg, self.pretty_init)
        if flat382 is not None:
            assert flat382 is not None
            self.write(flat382)
            return None
        else:
            def _t1130(_dollar_dollar):
                return _dollar_dollar
            _t1131 = _t1130(msg)
            fields378 = _t1131
            assert fields378 is not None
            unwrapped_fields379 = fields378
            self.write("(")
            self.write("init")
            self.indent_sexp()
            if not len(unwrapped_fields379) == 0:
                self.newline()
                for i381, elem380 in enumerate(unwrapped_fields379):
                    if (i381 > 0):
                        self.newline()
                    _t1132 = self.pretty_instruction(elem380)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat388 = self._try_flat(msg, self.pretty_instruction)
        if flat388 is not None:
            assert flat388 is not None
            self.write(flat388)
            return None
        else:
            def _t1134(_dollar_dollar):
                if _dollar_dollar.HasField("assign"):
                    _t1135 = _dollar_dollar.assign
                else:
                    _t1135 = None
                return _t1135
            _t1136 = _t1134(msg)
            deconstruct_result387 = _t1136
            if deconstruct_result387 is not None:
                _t1138 = self.pretty_assign(deconstruct_result387)
                _t1137 = _t1138
            else:
                def _t1139(_dollar_dollar):
                    if _dollar_dollar.HasField("upsert"):
                        _t1140 = _dollar_dollar.upsert
                    else:
                        _t1140 = None
                    return _t1140
                _t1141 = _t1139(msg)
                deconstruct_result386 = _t1141
                if deconstruct_result386 is not None:
                    _t1143 = self.pretty_upsert(deconstruct_result386)
                    _t1142 = _t1143
                else:
                    def _t1144(_dollar_dollar):
                        if _dollar_dollar.HasField("break"):
                            _t1145 = getattr(_dollar_dollar, 'break')
                        else:
                            _t1145 = None
                        return _t1145
                    _t1146 = _t1144(msg)
                    deconstruct_result385 = _t1146
                    if deconstruct_result385 is not None:
                        _t1148 = self.pretty_break(deconstruct_result385)
                        _t1147 = _t1148
                    else:
                        def _t1149(_dollar_dollar):
                            if _dollar_dollar.HasField("monoid_def"):
                                _t1150 = _dollar_dollar.monoid_def
                            else:
                                _t1150 = None
                            return _t1150
                        _t1151 = _t1149(msg)
                        deconstruct_result384 = _t1151
                        if deconstruct_result384 is not None:
                            _t1153 = self.pretty_monoid_def(deconstruct_result384)
                            _t1152 = _t1153
                        else:
                            def _t1154(_dollar_dollar):
                                if _dollar_dollar.HasField("monus_def"):
                                    _t1155 = _dollar_dollar.monus_def
                                else:
                                    _t1155 = None
                                return _t1155
                            _t1156 = _t1154(msg)
                            deconstruct_result383 = _t1156
                            if deconstruct_result383 is not None:
                                _t1158 = self.pretty_monus_def(deconstruct_result383)
                                _t1157 = _t1158
                            else:
                                raise ParseError("No matching rule for instruction")
                            _t1152 = _t1157
                        _t1147 = _t1152
                    _t1142 = _t1147
                _t1137 = _t1142
            _t1133 = _t1137

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat395 = self._try_flat(msg, self.pretty_assign)
        if flat395 is not None:
            assert flat395 is not None
            self.write(flat395)
            return None
        else:
            def _t1159(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1160 = _dollar_dollar.attrs
                else:
                    _t1160 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1160,)
            _t1161 = _t1159(msg)
            fields389 = _t1161
            assert fields389 is not None
            unwrapped_fields390 = fields389
            self.write("(")
            self.write("assign")
            self.indent_sexp()
            self.newline()
            field391 = unwrapped_fields390[0]
            _t1162 = self.pretty_relation_id(field391)
            self.newline()
            field392 = unwrapped_fields390[1]
            _t1163 = self.pretty_abstraction(field392)
            field393 = unwrapped_fields390[2]
            if field393 is not None:
                self.newline()
                assert field393 is not None
                opt_val394 = field393
                _t1165 = self.pretty_attrs(opt_val394)
                _t1164 = _t1165
            else:
                _t1164 = None
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat402 = self._try_flat(msg, self.pretty_upsert)
        if flat402 is not None:
            assert flat402 is not None
            self.write(flat402)
            return None
        else:
            def _t1166(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1167 = _dollar_dollar.attrs
                else:
                    _t1167 = None
                return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1167,)
            _t1168 = _t1166(msg)
            fields396 = _t1168
            assert fields396 is not None
            unwrapped_fields397 = fields396
            self.write("(")
            self.write("upsert")
            self.indent_sexp()
            self.newline()
            field398 = unwrapped_fields397[0]
            _t1169 = self.pretty_relation_id(field398)
            self.newline()
            field399 = unwrapped_fields397[1]
            _t1170 = self.pretty_abstraction_with_arity(field399)
            field400 = unwrapped_fields397[2]
            if field400 is not None:
                self.newline()
                assert field400 is not None
                opt_val401 = field400
                _t1172 = self.pretty_attrs(opt_val401)
                _t1171 = _t1172
            else:
                _t1171 = None
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat407 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat407 is not None:
            assert flat407 is not None
            self.write(flat407)
            return None
        else:
            def _t1173(_dollar_dollar):
                _t1174 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
                return (_t1174, _dollar_dollar[0].value,)
            _t1175 = _t1173(msg)
            fields403 = _t1175
            assert fields403 is not None
            unwrapped_fields404 = fields403
            self.write("(")
            self.indent()
            field405 = unwrapped_fields404[0]
            _t1176 = self.pretty_bindings(field405)
            self.newline()
            field406 = unwrapped_fields404[1]
            _t1177 = self.pretty_formula(field406)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat414 = self._try_flat(msg, self.pretty_break)
        if flat414 is not None:
            assert flat414 is not None
            self.write(flat414)
            return None
        else:
            def _t1178(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1179 = _dollar_dollar.attrs
                else:
                    _t1179 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1179,)
            _t1180 = _t1178(msg)
            fields408 = _t1180
            assert fields408 is not None
            unwrapped_fields409 = fields408
            self.write("(")
            self.write("break")
            self.indent_sexp()
            self.newline()
            field410 = unwrapped_fields409[0]
            _t1181 = self.pretty_relation_id(field410)
            self.newline()
            field411 = unwrapped_fields409[1]
            _t1182 = self.pretty_abstraction(field411)
            field412 = unwrapped_fields409[2]
            if field412 is not None:
                self.newline()
                assert field412 is not None
                opt_val413 = field412
                _t1184 = self.pretty_attrs(opt_val413)
                _t1183 = _t1184
            else:
                _t1183 = None
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat422 = self._try_flat(msg, self.pretty_monoid_def)
        if flat422 is not None:
            assert flat422 is not None
            self.write(flat422)
            return None
        else:
            def _t1185(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1186 = _dollar_dollar.attrs
                else:
                    _t1186 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1186,)
            _t1187 = _t1185(msg)
            fields415 = _t1187
            assert fields415 is not None
            unwrapped_fields416 = fields415
            self.write("(")
            self.write("monoid")
            self.indent_sexp()
            self.newline()
            field417 = unwrapped_fields416[0]
            _t1188 = self.pretty_monoid(field417)
            self.newline()
            field418 = unwrapped_fields416[1]
            _t1189 = self.pretty_relation_id(field418)
            self.newline()
            field419 = unwrapped_fields416[2]
            _t1190 = self.pretty_abstraction_with_arity(field419)
            field420 = unwrapped_fields416[3]
            if field420 is not None:
                self.newline()
                assert field420 is not None
                opt_val421 = field420
                _t1192 = self.pretty_attrs(opt_val421)
                _t1191 = _t1192
            else:
                _t1191 = None
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat427 = self._try_flat(msg, self.pretty_monoid)
        if flat427 is not None:
            assert flat427 is not None
            self.write(flat427)
            return None
        else:
            def _t1194(_dollar_dollar):
                if _dollar_dollar.HasField("or_monoid"):
                    _t1195 = _dollar_dollar.or_monoid
                else:
                    _t1195 = None
                return _t1195
            _t1196 = _t1194(msg)
            deconstruct_result426 = _t1196
            if deconstruct_result426 is not None:
                _t1198 = self.pretty_or_monoid(deconstruct_result426)
                _t1197 = _t1198
            else:
                def _t1199(_dollar_dollar):
                    if _dollar_dollar.HasField("min_monoid"):
                        _t1200 = _dollar_dollar.min_monoid
                    else:
                        _t1200 = None
                    return _t1200
                _t1201 = _t1199(msg)
                deconstruct_result425 = _t1201
                if deconstruct_result425 is not None:
                    _t1203 = self.pretty_min_monoid(deconstruct_result425)
                    _t1202 = _t1203
                else:
                    def _t1204(_dollar_dollar):
                        if _dollar_dollar.HasField("max_monoid"):
                            _t1205 = _dollar_dollar.max_monoid
                        else:
                            _t1205 = None
                        return _t1205
                    _t1206 = _t1204(msg)
                    deconstruct_result424 = _t1206
                    if deconstruct_result424 is not None:
                        _t1208 = self.pretty_max_monoid(deconstruct_result424)
                        _t1207 = _t1208
                    else:
                        def _t1209(_dollar_dollar):
                            if _dollar_dollar.HasField("sum_monoid"):
                                _t1210 = _dollar_dollar.sum_monoid
                            else:
                                _t1210 = None
                            return _t1210
                        _t1211 = _t1209(msg)
                        deconstruct_result423 = _t1211
                        if deconstruct_result423 is not None:
                            _t1213 = self.pretty_sum_monoid(deconstruct_result423)
                            _t1212 = _t1213
                        else:
                            raise ParseError("No matching rule for monoid")
                        _t1207 = _t1212
                    _t1202 = _t1207
                _t1197 = _t1202
            _t1193 = _t1197

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        flat430 = self._try_flat(msg, self.pretty_or_monoid)
        if flat430 is not None:
            assert flat430 is not None
            self.write(flat430)
            return None
        else:
            def _t1214(_dollar_dollar):
                return _dollar_dollar
            _t1215 = _t1214(msg)
            fields428 = _t1215
            assert fields428 is not None
            unwrapped_fields429 = fields428
            self.write("(")
            self.write("or")
            self.write(")")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat433 = self._try_flat(msg, self.pretty_min_monoid)
        if flat433 is not None:
            assert flat433 is not None
            self.write(flat433)
            return None
        else:
            def _t1216(_dollar_dollar):
                return _dollar_dollar.type
            _t1217 = _t1216(msg)
            fields431 = _t1217
            assert fields431 is not None
            unwrapped_fields432 = fields431
            self.write("(")
            self.write("min")
            self.indent_sexp()
            self.newline()
            _t1218 = self.pretty_type(unwrapped_fields432)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat436 = self._try_flat(msg, self.pretty_max_monoid)
        if flat436 is not None:
            assert flat436 is not None
            self.write(flat436)
            return None
        else:
            def _t1219(_dollar_dollar):
                return _dollar_dollar.type
            _t1220 = _t1219(msg)
            fields434 = _t1220
            assert fields434 is not None
            unwrapped_fields435 = fields434
            self.write("(")
            self.write("max")
            self.indent_sexp()
            self.newline()
            _t1221 = self.pretty_type(unwrapped_fields435)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat439 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat439 is not None:
            assert flat439 is not None
            self.write(flat439)
            return None
        else:
            def _t1222(_dollar_dollar):
                return _dollar_dollar.type
            _t1223 = _t1222(msg)
            fields437 = _t1223
            assert fields437 is not None
            unwrapped_fields438 = fields437
            self.write("(")
            self.write("sum")
            self.indent_sexp()
            self.newline()
            _t1224 = self.pretty_type(unwrapped_fields438)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat447 = self._try_flat(msg, self.pretty_monus_def)
        if flat447 is not None:
            assert flat447 is not None
            self.write(flat447)
            return None
        else:
            def _t1225(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1226 = _dollar_dollar.attrs
                else:
                    _t1226 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1226,)
            _t1227 = _t1225(msg)
            fields440 = _t1227
            assert fields440 is not None
            unwrapped_fields441 = fields440
            self.write("(")
            self.write("monus")
            self.indent_sexp()
            self.newline()
            field442 = unwrapped_fields441[0]
            _t1228 = self.pretty_monoid(field442)
            self.newline()
            field443 = unwrapped_fields441[1]
            _t1229 = self.pretty_relation_id(field443)
            self.newline()
            field444 = unwrapped_fields441[2]
            _t1230 = self.pretty_abstraction_with_arity(field444)
            field445 = unwrapped_fields441[3]
            if field445 is not None:
                self.newline()
                assert field445 is not None
                opt_val446 = field445
                _t1232 = self.pretty_attrs(opt_val446)
                _t1231 = _t1232
            else:
                _t1231 = None
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat454 = self._try_flat(msg, self.pretty_constraint)
        if flat454 is not None:
            assert flat454 is not None
            self.write(flat454)
            return None
        else:
            def _t1233(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            _t1234 = _t1233(msg)
            fields448 = _t1234
            assert fields448 is not None
            unwrapped_fields449 = fields448
            self.write("(")
            self.write("functional_dependency")
            self.indent_sexp()
            self.newline()
            field450 = unwrapped_fields449[0]
            _t1235 = self.pretty_relation_id(field450)
            self.newline()
            field451 = unwrapped_fields449[1]
            _t1236 = self.pretty_abstraction(field451)
            self.newline()
            field452 = unwrapped_fields449[2]
            _t1237 = self.pretty_functional_dependency_keys(field452)
            self.newline()
            field453 = unwrapped_fields449[3]
            _t1238 = self.pretty_functional_dependency_values(field453)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat459 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat459 is not None:
            assert flat459 is not None
            self.write(flat459)
            return None
        else:
            def _t1239(_dollar_dollar):
                return _dollar_dollar
            _t1240 = _t1239(msg)
            fields455 = _t1240
            assert fields455 is not None
            unwrapped_fields456 = fields455
            self.write("(")
            self.write("keys")
            self.indent_sexp()
            if not len(unwrapped_fields456) == 0:
                self.newline()
                for i458, elem457 in enumerate(unwrapped_fields456):
                    if (i458 > 0):
                        self.newline()
                    _t1241 = self.pretty_var(elem457)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat464 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat464 is not None:
            assert flat464 is not None
            self.write(flat464)
            return None
        else:
            def _t1242(_dollar_dollar):
                return _dollar_dollar
            _t1243 = _t1242(msg)
            fields460 = _t1243
            assert fields460 is not None
            unwrapped_fields461 = fields460
            self.write("(")
            self.write("values")
            self.indent_sexp()
            if not len(unwrapped_fields461) == 0:
                self.newline()
                for i463, elem462 in enumerate(unwrapped_fields461):
                    if (i463 > 0):
                        self.newline()
                    _t1244 = self.pretty_var(elem462)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat468 = self._try_flat(msg, self.pretty_data)
        if flat468 is not None:
            assert flat468 is not None
            self.write(flat468)
            return None
        else:
            def _t1246(_dollar_dollar):
                if _dollar_dollar.HasField("rel_edb"):
                    _t1247 = _dollar_dollar.rel_edb
                else:
                    _t1247 = None
                return _t1247
            _t1248 = _t1246(msg)
            deconstruct_result467 = _t1248
            if deconstruct_result467 is not None:
                _t1250 = self.pretty_rel_edb(deconstruct_result467)
                _t1249 = _t1250
            else:
                def _t1251(_dollar_dollar):
                    if _dollar_dollar.HasField("betree_relation"):
                        _t1252 = _dollar_dollar.betree_relation
                    else:
                        _t1252 = None
                    return _t1252
                _t1253 = _t1251(msg)
                deconstruct_result466 = _t1253
                if deconstruct_result466 is not None:
                    _t1255 = self.pretty_betree_relation(deconstruct_result466)
                    _t1254 = _t1255
                else:
                    def _t1256(_dollar_dollar):
                        if _dollar_dollar.HasField("csv_data"):
                            _t1257 = _dollar_dollar.csv_data
                        else:
                            _t1257 = None
                        return _t1257
                    _t1258 = _t1256(msg)
                    deconstruct_result465 = _t1258
                    if deconstruct_result465 is not None:
                        _t1260 = self.pretty_csv_data(deconstruct_result465)
                        _t1259 = _t1260
                    else:
                        raise ParseError("No matching rule for data")
                    _t1254 = _t1259
                _t1249 = _t1254
            _t1245 = _t1249

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB):
        flat474 = self._try_flat(msg, self.pretty_rel_edb)
        if flat474 is not None:
            assert flat474 is not None
            self.write(flat474)
            return None
        else:
            def _t1261(_dollar_dollar):
                return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            _t1262 = _t1261(msg)
            fields469 = _t1262
            assert fields469 is not None
            unwrapped_fields470 = fields469
            self.write("(")
            self.write("rel_edb")
            self.indent_sexp()
            self.newline()
            field471 = unwrapped_fields470[0]
            _t1263 = self.pretty_relation_id(field471)
            self.newline()
            field472 = unwrapped_fields470[1]
            _t1264 = self.pretty_rel_edb_path(field472)
            self.newline()
            field473 = unwrapped_fields470[2]
            _t1265 = self.pretty_rel_edb_types(field473)
            self.dedent()
            self.write(")")

    def pretty_rel_edb_path(self, msg: Sequence[str]):
        flat479 = self._try_flat(msg, self.pretty_rel_edb_path)
        if flat479 is not None:
            assert flat479 is not None
            self.write(flat479)
            return None
        else:
            def _t1266(_dollar_dollar):
                return _dollar_dollar
            _t1267 = _t1266(msg)
            fields475 = _t1267
            assert fields475 is not None
            unwrapped_fields476 = fields475
            self.write("[")
            self.indent()
            for i478, elem477 in enumerate(unwrapped_fields476):
                if (i478 > 0):
                    self.newline()
                self.write(self.format_string_value(elem477))
            self.dedent()
            self.write("]")

    def pretty_rel_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat484 = self._try_flat(msg, self.pretty_rel_edb_types)
        if flat484 is not None:
            assert flat484 is not None
            self.write(flat484)
            return None
        else:
            def _t1268(_dollar_dollar):
                return _dollar_dollar
            _t1269 = _t1268(msg)
            fields480 = _t1269
            assert fields480 is not None
            unwrapped_fields481 = fields480
            self.write("[")
            self.indent()
            for i483, elem482 in enumerate(unwrapped_fields481):
                if (i483 > 0):
                    self.newline()
                _t1270 = self.pretty_type(elem482)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat489 = self._try_flat(msg, self.pretty_betree_relation)
        if flat489 is not None:
            assert flat489 is not None
            self.write(flat489)
            return None
        else:
            def _t1271(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_info,)
            _t1272 = _t1271(msg)
            fields485 = _t1272
            assert fields485 is not None
            unwrapped_fields486 = fields485
            self.write("(")
            self.write("betree_relation")
            self.indent_sexp()
            self.newline()
            field487 = unwrapped_fields486[0]
            _t1273 = self.pretty_relation_id(field487)
            self.newline()
            field488 = unwrapped_fields486[1]
            _t1274 = self.pretty_betree_info(field488)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat495 = self._try_flat(msg, self.pretty_betree_info)
        if flat495 is not None:
            assert flat495 is not None
            self.write(flat495)
            return None
        else:
            def _t1275(_dollar_dollar):
                _t1276 = self.deconstruct_betree_info_config(_dollar_dollar)
                return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1276,)
            _t1277 = _t1275(msg)
            fields490 = _t1277
            assert fields490 is not None
            unwrapped_fields491 = fields490
            self.write("(")
            self.write("betree_info")
            self.indent_sexp()
            self.newline()
            field492 = unwrapped_fields491[0]
            _t1278 = self.pretty_betree_info_key_types(field492)
            self.newline()
            field493 = unwrapped_fields491[1]
            _t1279 = self.pretty_betree_info_value_types(field493)
            self.newline()
            field494 = unwrapped_fields491[2]
            _t1280 = self.pretty_config_dict(field494)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat500 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat500 is not None:
            assert flat500 is not None
            self.write(flat500)
            return None
        else:
            def _t1281(_dollar_dollar):
                return _dollar_dollar
            _t1282 = _t1281(msg)
            fields496 = _t1282
            assert fields496 is not None
            unwrapped_fields497 = fields496
            self.write("(")
            self.write("key_types")
            self.indent_sexp()
            if not len(unwrapped_fields497) == 0:
                self.newline()
                for i499, elem498 in enumerate(unwrapped_fields497):
                    if (i499 > 0):
                        self.newline()
                    _t1283 = self.pretty_type(elem498)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat505 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat505 is not None:
            assert flat505 is not None
            self.write(flat505)
            return None
        else:
            def _t1284(_dollar_dollar):
                return _dollar_dollar
            _t1285 = _t1284(msg)
            fields501 = _t1285
            assert fields501 is not None
            unwrapped_fields502 = fields501
            self.write("(")
            self.write("value_types")
            self.indent_sexp()
            if not len(unwrapped_fields502) == 0:
                self.newline()
                for i504, elem503 in enumerate(unwrapped_fields502):
                    if (i504 > 0):
                        self.newline()
                    _t1286 = self.pretty_type(elem503)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat512 = self._try_flat(msg, self.pretty_csv_data)
        if flat512 is not None:
            assert flat512 is not None
            self.write(flat512)
            return None
        else:
            def _t1287(_dollar_dollar):
                return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            _t1288 = _t1287(msg)
            fields506 = _t1288
            assert fields506 is not None
            unwrapped_fields507 = fields506
            self.write("(")
            self.write("csv_data")
            self.indent_sexp()
            self.newline()
            field508 = unwrapped_fields507[0]
            _t1289 = self.pretty_csvlocator(field508)
            self.newline()
            field509 = unwrapped_fields507[1]
            _t1290 = self.pretty_csv_config(field509)
            self.newline()
            field510 = unwrapped_fields507[2]
            _t1291 = self.pretty_csv_columns(field510)
            self.newline()
            field511 = unwrapped_fields507[3]
            _t1292 = self.pretty_csv_asof(field511)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat519 = self._try_flat(msg, self.pretty_csvlocator)
        if flat519 is not None:
            assert flat519 is not None
            self.write(flat519)
            return None
        else:
            def _t1293(_dollar_dollar):
                if not len(_dollar_dollar.paths) == 0:
                    _t1294 = _dollar_dollar.paths
                else:
                    _t1294 = None
                if _dollar_dollar.inline_data.decode('utf-8') != "":
                    _t1295 = _dollar_dollar.inline_data.decode('utf-8')
                else:
                    _t1295 = None
                return (_t1294, _t1295,)
            _t1296 = _t1293(msg)
            fields513 = _t1296
            assert fields513 is not None
            unwrapped_fields514 = fields513
            self.write("(")
            self.write("csv_locator")
            self.indent_sexp()
            field515 = unwrapped_fields514[0]
            if field515 is not None:
                self.newline()
                assert field515 is not None
                opt_val516 = field515
                _t1298 = self.pretty_csv_locator_paths(opt_val516)
                _t1297 = _t1298
            else:
                _t1297 = None
            field517 = unwrapped_fields514[1]
            if field517 is not None:
                self.newline()
                assert field517 is not None
                opt_val518 = field517
                _t1300 = self.pretty_csv_locator_inline_data(opt_val518)
                _t1299 = _t1300
            else:
                _t1299 = None
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat524 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat524 is not None:
            assert flat524 is not None
            self.write(flat524)
            return None
        else:
            def _t1301(_dollar_dollar):
                return _dollar_dollar
            _t1302 = _t1301(msg)
            fields520 = _t1302
            assert fields520 is not None
            unwrapped_fields521 = fields520
            self.write("(")
            self.write("paths")
            self.indent_sexp()
            if not len(unwrapped_fields521) == 0:
                self.newline()
                for i523, elem522 in enumerate(unwrapped_fields521):
                    if (i523 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem522))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat527 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat527 is not None:
            assert flat527 is not None
            self.write(flat527)
            return None
        else:
            def _t1303(_dollar_dollar):
                return _dollar_dollar
            _t1304 = _t1303(msg)
            fields525 = _t1304
            assert fields525 is not None
            unwrapped_fields526 = fields525
            self.write("(")
            self.write("inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(unwrapped_fields526))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat530 = self._try_flat(msg, self.pretty_csv_config)
        if flat530 is not None:
            assert flat530 is not None
            self.write(flat530)
            return None
        else:
            def _t1305(_dollar_dollar):
                _t1306 = self.deconstruct_csv_config(_dollar_dollar)
                return _t1306
            _t1307 = _t1305(msg)
            fields528 = _t1307
            assert fields528 is not None
            unwrapped_fields529 = fields528
            self.write("(")
            self.write("csv_config")
            self.indent_sexp()
            self.newline()
            _t1308 = self.pretty_config_dict(unwrapped_fields529)
            self.dedent()
            self.write(")")

    def pretty_csv_columns(self, msg: Sequence[logic_pb2.CSVColumn]):
        flat535 = self._try_flat(msg, self.pretty_csv_columns)
        if flat535 is not None:
            assert flat535 is not None
            self.write(flat535)
            return None
        else:
            def _t1309(_dollar_dollar):
                return _dollar_dollar
            _t1310 = _t1309(msg)
            fields531 = _t1310
            assert fields531 is not None
            unwrapped_fields532 = fields531
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(unwrapped_fields532) == 0:
                self.newline()
                for i534, elem533 in enumerate(unwrapped_fields532):
                    if (i534 > 0):
                        self.newline()
                    _t1311 = self.pretty_csv_column(elem533)
            self.dedent()
            self.write(")")

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn):
        flat543 = self._try_flat(msg, self.pretty_csv_column)
        if flat543 is not None:
            assert flat543 is not None
            self.write(flat543)
            return None
        else:
            def _t1312(_dollar_dollar):
                return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
            _t1313 = _t1312(msg)
            fields536 = _t1313
            assert fields536 is not None
            unwrapped_fields537 = fields536
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field538 = unwrapped_fields537[0]
            self.write(self.format_string_value(field538))
            self.newline()
            field539 = unwrapped_fields537[1]
            _t1314 = self.pretty_relation_id(field539)
            self.newline()
            self.write("[")
            field540 = unwrapped_fields537[2]
            for i542, elem541 in enumerate(field540):
                if (i542 > 0):
                    self.newline()
                _t1315 = self.pretty_type(elem541)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_csv_asof(self, msg: str):
        flat546 = self._try_flat(msg, self.pretty_csv_asof)
        if flat546 is not None:
            assert flat546 is not None
            self.write(flat546)
            return None
        else:
            def _t1316(_dollar_dollar):
                return _dollar_dollar
            _t1317 = _t1316(msg)
            fields544 = _t1317
            assert fields544 is not None
            unwrapped_fields545 = fields544
            self.write("(")
            self.write("asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(unwrapped_fields545))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat549 = self._try_flat(msg, self.pretty_undefine)
        if flat549 is not None:
            assert flat549 is not None
            self.write(flat549)
            return None
        else:
            def _t1318(_dollar_dollar):
                return _dollar_dollar.fragment_id
            _t1319 = _t1318(msg)
            fields547 = _t1319
            assert fields547 is not None
            unwrapped_fields548 = fields547
            self.write("(")
            self.write("undefine")
            self.indent_sexp()
            self.newline()
            _t1320 = self.pretty_fragment_id(unwrapped_fields548)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat554 = self._try_flat(msg, self.pretty_context)
        if flat554 is not None:
            assert flat554 is not None
            self.write(flat554)
            return None
        else:
            def _t1321(_dollar_dollar):
                return _dollar_dollar.relations
            _t1322 = _t1321(msg)
            fields550 = _t1322
            assert fields550 is not None
            unwrapped_fields551 = fields550
            self.write("(")
            self.write("context")
            self.indent_sexp()
            if not len(unwrapped_fields551) == 0:
                self.newline()
                for i553, elem552 in enumerate(unwrapped_fields551):
                    if (i553 > 0):
                        self.newline()
                    _t1323 = self.pretty_relation_id(elem552)
            self.dedent()
            self.write(")")

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat559 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat559 is not None:
            assert flat559 is not None
            self.write(flat559)
            return None
        else:
            def _t1324(_dollar_dollar):
                return _dollar_dollar
            _t1325 = _t1324(msg)
            fields555 = _t1325
            assert fields555 is not None
            unwrapped_fields556 = fields555
            self.write("(")
            self.write("reads")
            self.indent_sexp()
            if not len(unwrapped_fields556) == 0:
                self.newline()
                for i558, elem557 in enumerate(unwrapped_fields556):
                    if (i558 > 0):
                        self.newline()
                    _t1326 = self.pretty_read(elem557)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat565 = self._try_flat(msg, self.pretty_read)
        if flat565 is not None:
            assert flat565 is not None
            self.write(flat565)
            return None
        else:
            def _t1328(_dollar_dollar):
                if _dollar_dollar.HasField("demand"):
                    _t1329 = _dollar_dollar.demand
                else:
                    _t1329 = None
                return _t1329
            _t1330 = _t1328(msg)
            deconstruct_result564 = _t1330
            if deconstruct_result564 is not None:
                _t1332 = self.pretty_demand(deconstruct_result564)
                _t1331 = _t1332
            else:
                def _t1333(_dollar_dollar):
                    if _dollar_dollar.HasField("output"):
                        _t1334 = _dollar_dollar.output
                    else:
                        _t1334 = None
                    return _t1334
                _t1335 = _t1333(msg)
                deconstruct_result563 = _t1335
                if deconstruct_result563 is not None:
                    _t1337 = self.pretty_output(deconstruct_result563)
                    _t1336 = _t1337
                else:
                    def _t1338(_dollar_dollar):
                        if _dollar_dollar.HasField("what_if"):
                            _t1339 = _dollar_dollar.what_if
                        else:
                            _t1339 = None
                        return _t1339
                    _t1340 = _t1338(msg)
                    deconstruct_result562 = _t1340
                    if deconstruct_result562 is not None:
                        _t1342 = self.pretty_what_if(deconstruct_result562)
                        _t1341 = _t1342
                    else:
                        def _t1343(_dollar_dollar):
                            if _dollar_dollar.HasField("abort"):
                                _t1344 = _dollar_dollar.abort
                            else:
                                _t1344 = None
                            return _t1344
                        _t1345 = _t1343(msg)
                        deconstruct_result561 = _t1345
                        if deconstruct_result561 is not None:
                            _t1347 = self.pretty_abort(deconstruct_result561)
                            _t1346 = _t1347
                        else:
                            def _t1348(_dollar_dollar):
                                if _dollar_dollar.HasField("export"):
                                    _t1349 = _dollar_dollar.export
                                else:
                                    _t1349 = None
                                return _t1349
                            _t1350 = _t1348(msg)
                            deconstruct_result560 = _t1350
                            if deconstruct_result560 is not None:
                                _t1352 = self.pretty_export(deconstruct_result560)
                                _t1351 = _t1352
                            else:
                                raise ParseError("No matching rule for read")
                            _t1346 = _t1351
                        _t1341 = _t1346
                    _t1336 = _t1341
                _t1331 = _t1336
            _t1327 = _t1331

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat568 = self._try_flat(msg, self.pretty_demand)
        if flat568 is not None:
            assert flat568 is not None
            self.write(flat568)
            return None
        else:
            def _t1353(_dollar_dollar):
                return _dollar_dollar.relation_id
            _t1354 = _t1353(msg)
            fields566 = _t1354
            assert fields566 is not None
            unwrapped_fields567 = fields566
            self.write("(")
            self.write("demand")
            self.indent_sexp()
            self.newline()
            _t1355 = self.pretty_relation_id(unwrapped_fields567)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat573 = self._try_flat(msg, self.pretty_output)
        if flat573 is not None:
            assert flat573 is not None
            self.write(flat573)
            return None
        else:
            def _t1356(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_id,)
            _t1357 = _t1356(msg)
            fields569 = _t1357
            assert fields569 is not None
            unwrapped_fields570 = fields569
            self.write("(")
            self.write("output")
            self.indent_sexp()
            self.newline()
            field571 = unwrapped_fields570[0]
            _t1358 = self.pretty_name(field571)
            self.newline()
            field572 = unwrapped_fields570[1]
            _t1359 = self.pretty_relation_id(field572)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat578 = self._try_flat(msg, self.pretty_what_if)
        if flat578 is not None:
            assert flat578 is not None
            self.write(flat578)
            return None
        else:
            def _t1360(_dollar_dollar):
                return (_dollar_dollar.branch, _dollar_dollar.epoch,)
            _t1361 = _t1360(msg)
            fields574 = _t1361
            assert fields574 is not None
            unwrapped_fields575 = fields574
            self.write("(")
            self.write("what_if")
            self.indent_sexp()
            self.newline()
            field576 = unwrapped_fields575[0]
            _t1362 = self.pretty_name(field576)
            self.newline()
            field577 = unwrapped_fields575[1]
            _t1363 = self.pretty_epoch(field577)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat584 = self._try_flat(msg, self.pretty_abort)
        if flat584 is not None:
            assert flat584 is not None
            self.write(flat584)
            return None
        else:
            def _t1364(_dollar_dollar):
                if _dollar_dollar.name != "abort":
                    _t1365 = _dollar_dollar.name
                else:
                    _t1365 = None
                return (_t1365, _dollar_dollar.relation_id,)
            _t1366 = _t1364(msg)
            fields579 = _t1366
            assert fields579 is not None
            unwrapped_fields580 = fields579
            self.write("(")
            self.write("abort")
            self.indent_sexp()
            field581 = unwrapped_fields580[0]
            if field581 is not None:
                self.newline()
                assert field581 is not None
                opt_val582 = field581
                _t1368 = self.pretty_name(opt_val582)
                _t1367 = _t1368
            else:
                _t1367 = None
            self.newline()
            field583 = unwrapped_fields580[1]
            _t1369 = self.pretty_relation_id(field583)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat587 = self._try_flat(msg, self.pretty_export)
        if flat587 is not None:
            assert flat587 is not None
            self.write(flat587)
            return None
        else:
            def _t1370(_dollar_dollar):
                return _dollar_dollar.csv_config
            _t1371 = _t1370(msg)
            fields585 = _t1371
            assert fields585 is not None
            unwrapped_fields586 = fields585
            self.write("(")
            self.write("export")
            self.indent_sexp()
            self.newline()
            _t1372 = self.pretty_export_csv_config(unwrapped_fields586)
            self.dedent()
            self.write(")")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat593 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat593 is not None:
            assert flat593 is not None
            self.write(flat593)
            return None
        else:
            def _t1373(_dollar_dollar):
                _t1374 = self.deconstruct_export_csv_config(_dollar_dollar)
                return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1374,)
            _t1375 = _t1373(msg)
            fields588 = _t1375
            assert fields588 is not None
            unwrapped_fields589 = fields588
            self.write("(")
            self.write("export_csv_config")
            self.indent_sexp()
            self.newline()
            field590 = unwrapped_fields589[0]
            _t1376 = self.pretty_export_csv_path(field590)
            self.newline()
            field591 = unwrapped_fields589[1]
            _t1377 = self.pretty_export_csv_columns(field591)
            self.newline()
            field592 = unwrapped_fields589[2]
            _t1378 = self.pretty_config_dict(field592)
            self.dedent()
            self.write(")")

    def pretty_export_csv_path(self, msg: str):
        flat596 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat596 is not None:
            assert flat596 is not None
            self.write(flat596)
            return None
        else:
            def _t1379(_dollar_dollar):
                return _dollar_dollar
            _t1380 = _t1379(msg)
            fields594 = _t1380
            assert fields594 is not None
            unwrapped_fields595 = fields594
            self.write("(")
            self.write("path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(unwrapped_fields595))
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat601 = self._try_flat(msg, self.pretty_export_csv_columns)
        if flat601 is not None:
            assert flat601 is not None
            self.write(flat601)
            return None
        else:
            def _t1381(_dollar_dollar):
                return _dollar_dollar
            _t1382 = _t1381(msg)
            fields597 = _t1382
            assert fields597 is not None
            unwrapped_fields598 = fields597
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(unwrapped_fields598) == 0:
                self.newline()
                for i600, elem599 in enumerate(unwrapped_fields598):
                    if (i600 > 0):
                        self.newline()
                    _t1383 = self.pretty_export_csv_column(elem599)
            self.dedent()
            self.write(")")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat606 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat606 is not None:
            assert flat606 is not None
            self.write(flat606)
            return None
        else:
            def _t1384(_dollar_dollar):
                return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            _t1385 = _t1384(msg)
            fields602 = _t1385
            assert fields602 is not None
            unwrapped_fields603 = fields602
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field604 = unwrapped_fields603[0]
            self.write(self.format_string_value(field604))
            self.newline()
            field605 = unwrapped_fields603[1]
            _t1386 = self.pretty_relation_id(field605)
            self.dedent()
            self.write(")")


def pretty(msg: Any, io: Optional[IO[str]] = None, max_width: int = 92) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io, max_width=max_width)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()
