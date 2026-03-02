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

    def __init__(self, io: Optional[IO[str]] = None, max_width: int = 92, print_symbolic_relation_ids: bool = True):
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

    def relation_id_to_string(self, msg: logic_pb2.RelationId) -> str | None:
        """Convert RelationId to string representation using debug info."""
        if not self.print_symbolic_relation_ids:
            return None
        return self._debug_info.get((msg.id_low, msg.id_high), None)

    def relation_id_to_uint128(self, msg: logic_pb2.RelationId) -> logic_pb2.UInt128Value:
        """Convert RelationId to UInt128Value representation."""
        return logic_pb2.UInt128Value(low=msg.id_low, high=msg.id_high)

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
        _t1423 = logic_pb2.Value(int_value=int(v))
        return _t1423

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1424 = logic_pb2.Value(int_value=v)
        return _t1424

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1425 = logic_pb2.Value(float_value=v)
        return _t1425

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1426 = logic_pb2.Value(string_value=v)
        return _t1426

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1427 = logic_pb2.Value(boolean_value=v)
        return _t1427

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1428 = logic_pb2.Value(uint128_value=v)
        return _t1428

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1429 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1429,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1430 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1430,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1431 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1431,))
        _t1432 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1432,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1433 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1433,))
        _t1434 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1434,))
        if msg.new_line != "":
            _t1435 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1435,))
        _t1436 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1436,))
        _t1437 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1437,))
        _t1438 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1438,))
        if msg.comment != "":
            _t1439 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1439,))
        for missing_string in msg.missing_strings:
            _t1440 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1440,))
        _t1441 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1441,))
        _t1442 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1442,))
        _t1443 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1443,))
        if msg.partition_size_mb != 0:
            _t1444 = self._make_value_int64(msg.partition_size_mb)
            result.append(("csv_partition_size_mb", _t1444,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1445 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1445,))
        _t1446 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1446,))
        _t1447 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1447,))
        _t1448 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1448,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1449 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1449,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1450 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1450,))
        _t1451 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1451,))
        _t1452 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1452,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1453 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1453,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1454 = self._make_value_string(msg.compression)
            result.append(("compression", _t1454,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1455 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1455,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1456 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1456,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1457 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1457,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1458 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1458,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1459 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1459,))
        return sorted(result)

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> str:
        name = self.relation_id_to_string(msg)
        assert name is not None
        return name

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name is None:
            return self.relation_id_to_uint128(msg)
        else:
            _t1460 = None
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
        flat663 = self._try_flat(msg, self.pretty_transaction)
        if flat663 is not None:
            assert flat663 is not None
            self.write(flat663)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("configure"):
                _t1308 = _dollar_dollar.configure
            else:
                _t1308 = None
            if _dollar_dollar.HasField("sync"):
                _t1309 = _dollar_dollar.sync
            else:
                _t1309 = None
            fields654 = (_t1308, _t1309, _dollar_dollar.epochs,)
            assert fields654 is not None
            unwrapped_fields655 = fields654
            self.write("(transaction")
            self.indent_sexp()
            field656 = unwrapped_fields655[0]
            if field656 is not None:
                self.newline()
                assert field656 is not None
                opt_val657 = field656
                self.pretty_configure(opt_val657)
            field658 = unwrapped_fields655[1]
            if field658 is not None:
                self.newline()
                assert field658 is not None
                opt_val659 = field658
                self.pretty_sync(opt_val659)
            field660 = unwrapped_fields655[2]
            if not len(field660) == 0:
                self.newline()
                for i662, elem661 in enumerate(field660):
                    if (i662 > 0):
                        self.newline()
                    self.pretty_epoch(elem661)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat666 = self._try_flat(msg, self.pretty_configure)
        if flat666 is not None:
            assert flat666 is not None
            self.write(flat666)
            return None
        else:
            _dollar_dollar = msg
            _t1310 = self.deconstruct_configure(_dollar_dollar)
            fields664 = _t1310
            assert fields664 is not None
            unwrapped_fields665 = fields664
            self.write("(configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields665)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat670 = self._try_flat(msg, self.pretty_config_dict)
        if flat670 is not None:
            assert flat670 is not None
            self.write(flat670)
            return None
        else:
            fields667 = msg
            self.write("{")
            self.indent()
            if not len(fields667) == 0:
                self.newline()
                for i669, elem668 in enumerate(fields667):
                    if (i669 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem668)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat675 = self._try_flat(msg, self.pretty_config_key_value)
        if flat675 is not None:
            assert flat675 is not None
            self.write(flat675)
            return None
        else:
            _dollar_dollar = msg
            fields671 = (_dollar_dollar[0], _dollar_dollar[1],)
            assert fields671 is not None
            unwrapped_fields672 = fields671
            self.write(":")
            field673 = unwrapped_fields672[0]
            self.write(field673)
            self.write(" ")
            field674 = unwrapped_fields672[1]
            self.pretty_value(field674)

    def pretty_value(self, msg: logic_pb2.Value):
        flat695 = self._try_flat(msg, self.pretty_value)
        if flat695 is not None:
            assert flat695 is not None
            self.write(flat695)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("date_value"):
                _t1311 = _dollar_dollar.date_value
            else:
                _t1311 = None
            deconstruct_result693 = _t1311
            if deconstruct_result693 is not None:
                assert deconstruct_result693 is not None
                unwrapped694 = deconstruct_result693
                self.pretty_date(unwrapped694)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("datetime_value"):
                    _t1312 = _dollar_dollar.datetime_value
                else:
                    _t1312 = None
                deconstruct_result691 = _t1312
                if deconstruct_result691 is not None:
                    assert deconstruct_result691 is not None
                    unwrapped692 = deconstruct_result691
                    self.pretty_datetime(unwrapped692)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("string_value"):
                        _t1313 = _dollar_dollar.string_value
                    else:
                        _t1313 = None
                    deconstruct_result689 = _t1313
                    if deconstruct_result689 is not None:
                        assert deconstruct_result689 is not None
                        unwrapped690 = deconstruct_result689
                        self.write(self.format_string_value(unwrapped690))
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("int_value"):
                            _t1314 = _dollar_dollar.int_value
                        else:
                            _t1314 = None
                        deconstruct_result687 = _t1314
                        if deconstruct_result687 is not None:
                            assert deconstruct_result687 is not None
                            unwrapped688 = deconstruct_result687
                            self.write(str(unwrapped688))
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("float_value"):
                                _t1315 = _dollar_dollar.float_value
                            else:
                                _t1315 = None
                            deconstruct_result685 = _t1315
                            if deconstruct_result685 is not None:
                                assert deconstruct_result685 is not None
                                unwrapped686 = deconstruct_result685
                                self.write(str(unwrapped686))
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("uint128_value"):
                                    _t1316 = _dollar_dollar.uint128_value
                                else:
                                    _t1316 = None
                                deconstruct_result683 = _t1316
                                if deconstruct_result683 is not None:
                                    assert deconstruct_result683 is not None
                                    unwrapped684 = deconstruct_result683
                                    self.write(self.format_uint128(unwrapped684))
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("int128_value"):
                                        _t1317 = _dollar_dollar.int128_value
                                    else:
                                        _t1317 = None
                                    deconstruct_result681 = _t1317
                                    if deconstruct_result681 is not None:
                                        assert deconstruct_result681 is not None
                                        unwrapped682 = deconstruct_result681
                                        self.write(self.format_int128(unwrapped682))
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("decimal_value"):
                                            _t1318 = _dollar_dollar.decimal_value
                                        else:
                                            _t1318 = None
                                        deconstruct_result679 = _t1318
                                        if deconstruct_result679 is not None:
                                            assert deconstruct_result679 is not None
                                            unwrapped680 = deconstruct_result679
                                            self.write(self.format_decimal(unwrapped680))
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("boolean_value"):
                                                _t1319 = _dollar_dollar.boolean_value
                                            else:
                                                _t1319 = None
                                            deconstruct_result677 = _t1319
                                            if deconstruct_result677 is not None:
                                                assert deconstruct_result677 is not None
                                                unwrapped678 = deconstruct_result677
                                                self.pretty_boolean_value(unwrapped678)
                                            else:
                                                fields676 = msg
                                                self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat701 = self._try_flat(msg, self.pretty_date)
        if flat701 is not None:
            assert flat701 is not None
            self.write(flat701)
            return None
        else:
            _dollar_dollar = msg
            fields696 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            assert fields696 is not None
            unwrapped_fields697 = fields696
            self.write("(date")
            self.indent_sexp()
            self.newline()
            field698 = unwrapped_fields697[0]
            self.write(str(field698))
            self.newline()
            field699 = unwrapped_fields697[1]
            self.write(str(field699))
            self.newline()
            field700 = unwrapped_fields697[2]
            self.write(str(field700))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat712 = self._try_flat(msg, self.pretty_datetime)
        if flat712 is not None:
            assert flat712 is not None
            self.write(flat712)
            return None
        else:
            _dollar_dollar = msg
            fields702 = (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            assert fields702 is not None
            unwrapped_fields703 = fields702
            self.write("(datetime")
            self.indent_sexp()
            self.newline()
            field704 = unwrapped_fields703[0]
            self.write(str(field704))
            self.newline()
            field705 = unwrapped_fields703[1]
            self.write(str(field705))
            self.newline()
            field706 = unwrapped_fields703[2]
            self.write(str(field706))
            self.newline()
            field707 = unwrapped_fields703[3]
            self.write(str(field707))
            self.newline()
            field708 = unwrapped_fields703[4]
            self.write(str(field708))
            self.newline()
            field709 = unwrapped_fields703[5]
            self.write(str(field709))
            field710 = unwrapped_fields703[6]
            if field710 is not None:
                self.newline()
                assert field710 is not None
                opt_val711 = field710
                self.write(str(opt_val711))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        _dollar_dollar = msg
        if _dollar_dollar:
            _t1320 = ()
        else:
            _t1320 = None
        deconstruct_result715 = _t1320
        if deconstruct_result715 is not None:
            assert deconstruct_result715 is not None
            unwrapped716 = deconstruct_result715
            self.write("true")
        else:
            _dollar_dollar = msg
            if not _dollar_dollar:
                _t1321 = ()
            else:
                _t1321 = None
            deconstruct_result713 = _t1321
            if deconstruct_result713 is not None:
                assert deconstruct_result713 is not None
                unwrapped714 = deconstruct_result713
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat721 = self._try_flat(msg, self.pretty_sync)
        if flat721 is not None:
            assert flat721 is not None
            self.write(flat721)
            return None
        else:
            _dollar_dollar = msg
            fields717 = _dollar_dollar.fragments
            assert fields717 is not None
            unwrapped_fields718 = fields717
            self.write("(sync")
            self.indent_sexp()
            if not len(unwrapped_fields718) == 0:
                self.newline()
                for i720, elem719 in enumerate(unwrapped_fields718):
                    if (i720 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem719)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat724 = self._try_flat(msg, self.pretty_fragment_id)
        if flat724 is not None:
            assert flat724 is not None
            self.write(flat724)
            return None
        else:
            _dollar_dollar = msg
            fields722 = self.fragment_id_to_string(_dollar_dollar)
            assert fields722 is not None
            unwrapped_fields723 = fields722
            self.write(":")
            self.write(unwrapped_fields723)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat731 = self._try_flat(msg, self.pretty_epoch)
        if flat731 is not None:
            assert flat731 is not None
            self.write(flat731)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.writes) == 0:
                _t1322 = _dollar_dollar.writes
            else:
                _t1322 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1323 = _dollar_dollar.reads
            else:
                _t1323 = None
            fields725 = (_t1322, _t1323,)
            assert fields725 is not None
            unwrapped_fields726 = fields725
            self.write("(epoch")
            self.indent_sexp()
            field727 = unwrapped_fields726[0]
            if field727 is not None:
                self.newline()
                assert field727 is not None
                opt_val728 = field727
                self.pretty_epoch_writes(opt_val728)
            field729 = unwrapped_fields726[1]
            if field729 is not None:
                self.newline()
                assert field729 is not None
                opt_val730 = field729
                self.pretty_epoch_reads(opt_val730)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat735 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat735 is not None:
            assert flat735 is not None
            self.write(flat735)
            return None
        else:
            fields732 = msg
            self.write("(writes")
            self.indent_sexp()
            if not len(fields732) == 0:
                self.newline()
                for i734, elem733 in enumerate(fields732):
                    if (i734 > 0):
                        self.newline()
                    self.pretty_write(elem733)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat744 = self._try_flat(msg, self.pretty_write)
        if flat744 is not None:
            assert flat744 is not None
            self.write(flat744)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("define"):
                _t1324 = _dollar_dollar.define
            else:
                _t1324 = None
            deconstruct_result742 = _t1324
            if deconstruct_result742 is not None:
                assert deconstruct_result742 is not None
                unwrapped743 = deconstruct_result742
                self.pretty_define(unwrapped743)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("undefine"):
                    _t1325 = _dollar_dollar.undefine
                else:
                    _t1325 = None
                deconstruct_result740 = _t1325
                if deconstruct_result740 is not None:
                    assert deconstruct_result740 is not None
                    unwrapped741 = deconstruct_result740
                    self.pretty_undefine(unwrapped741)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("context"):
                        _t1326 = _dollar_dollar.context
                    else:
                        _t1326 = None
                    deconstruct_result738 = _t1326
                    if deconstruct_result738 is not None:
                        assert deconstruct_result738 is not None
                        unwrapped739 = deconstruct_result738
                        self.pretty_context(unwrapped739)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("snapshot"):
                            _t1327 = _dollar_dollar.snapshot
                        else:
                            _t1327 = None
                        deconstruct_result736 = _t1327
                        if deconstruct_result736 is not None:
                            assert deconstruct_result736 is not None
                            unwrapped737 = deconstruct_result736
                            self.pretty_snapshot(unwrapped737)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat747 = self._try_flat(msg, self.pretty_define)
        if flat747 is not None:
            assert flat747 is not None
            self.write(flat747)
            return None
        else:
            _dollar_dollar = msg
            fields745 = _dollar_dollar.fragment
            assert fields745 is not None
            unwrapped_fields746 = fields745
            self.write("(define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields746)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat754 = self._try_flat(msg, self.pretty_fragment)
        if flat754 is not None:
            assert flat754 is not None
            self.write(flat754)
            return None
        else:
            _dollar_dollar = msg
            self.start_pretty_fragment(_dollar_dollar)
            fields748 = (_dollar_dollar.id, _dollar_dollar.declarations,)
            assert fields748 is not None
            unwrapped_fields749 = fields748
            self.write("(fragment")
            self.indent_sexp()
            self.newline()
            field750 = unwrapped_fields749[0]
            self.pretty_new_fragment_id(field750)
            field751 = unwrapped_fields749[1]
            if not len(field751) == 0:
                self.newline()
                for i753, elem752 in enumerate(field751):
                    if (i753 > 0):
                        self.newline()
                    self.pretty_declaration(elem752)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat756 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat756 is not None:
            assert flat756 is not None
            self.write(flat756)
            return None
        else:
            fields755 = msg
            self.pretty_fragment_id(fields755)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat765 = self._try_flat(msg, self.pretty_declaration)
        if flat765 is not None:
            assert flat765 is not None
            self.write(flat765)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("def"):
                _t1328 = getattr(_dollar_dollar, 'def')
            else:
                _t1328 = None
            deconstruct_result763 = _t1328
            if deconstruct_result763 is not None:
                assert deconstruct_result763 is not None
                unwrapped764 = deconstruct_result763
                self.pretty_def(unwrapped764)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("algorithm"):
                    _t1329 = _dollar_dollar.algorithm
                else:
                    _t1329 = None
                deconstruct_result761 = _t1329
                if deconstruct_result761 is not None:
                    assert deconstruct_result761 is not None
                    unwrapped762 = deconstruct_result761
                    self.pretty_algorithm(unwrapped762)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("constraint"):
                        _t1330 = _dollar_dollar.constraint
                    else:
                        _t1330 = None
                    deconstruct_result759 = _t1330
                    if deconstruct_result759 is not None:
                        assert deconstruct_result759 is not None
                        unwrapped760 = deconstruct_result759
                        self.pretty_constraint(unwrapped760)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("data"):
                            _t1331 = _dollar_dollar.data
                        else:
                            _t1331 = None
                        deconstruct_result757 = _t1331
                        if deconstruct_result757 is not None:
                            assert deconstruct_result757 is not None
                            unwrapped758 = deconstruct_result757
                            self.pretty_data(unwrapped758)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat772 = self._try_flat(msg, self.pretty_def)
        if flat772 is not None:
            assert flat772 is not None
            self.write(flat772)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1332 = _dollar_dollar.attrs
            else:
                _t1332 = None
            fields766 = (_dollar_dollar.name, _dollar_dollar.body, _t1332,)
            assert fields766 is not None
            unwrapped_fields767 = fields766
            self.write("(def")
            self.indent_sexp()
            self.newline()
            field768 = unwrapped_fields767[0]
            self.pretty_relation_id(field768)
            self.newline()
            field769 = unwrapped_fields767[1]
            self.pretty_abstraction(field769)
            field770 = unwrapped_fields767[2]
            if field770 is not None:
                self.newline()
                assert field770 is not None
                opt_val771 = field770
                self.pretty_attrs(opt_val771)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat777 = self._try_flat(msg, self.pretty_relation_id)
        if flat777 is not None:
            assert flat777 is not None
            self.write(flat777)
            return None
        else:
            _dollar_dollar = msg
            if self.relation_id_to_string(_dollar_dollar) is not None:
                _t1334 = self.deconstruct_relation_id_string(_dollar_dollar)
                _t1333 = _t1334
            else:
                _t1333 = None
            deconstruct_result775 = _t1333
            if deconstruct_result775 is not None:
                assert deconstruct_result775 is not None
                unwrapped776 = deconstruct_result775
                self.write(":")
                self.write(unwrapped776)
            else:
                _dollar_dollar = msg
                _t1335 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                deconstruct_result773 = _t1335
                if deconstruct_result773 is not None:
                    assert deconstruct_result773 is not None
                    unwrapped774 = deconstruct_result773
                    self.write(self.format_uint128(unwrapped774))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat782 = self._try_flat(msg, self.pretty_abstraction)
        if flat782 is not None:
            assert flat782 is not None
            self.write(flat782)
            return None
        else:
            _dollar_dollar = msg
            _t1336 = self.deconstruct_bindings(_dollar_dollar)
            fields778 = (_t1336, _dollar_dollar.value,)
            assert fields778 is not None
            unwrapped_fields779 = fields778
            self.write("(")
            self.indent()
            field780 = unwrapped_fields779[0]
            self.pretty_bindings(field780)
            self.newline()
            field781 = unwrapped_fields779[1]
            self.pretty_formula(field781)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat790 = self._try_flat(msg, self.pretty_bindings)
        if flat790 is not None:
            assert flat790 is not None
            self.write(flat790)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar[1]) == 0:
                _t1337 = _dollar_dollar[1]
            else:
                _t1337 = None
            fields783 = (_dollar_dollar[0], _t1337,)
            assert fields783 is not None
            unwrapped_fields784 = fields783
            self.write("[")
            self.indent()
            field785 = unwrapped_fields784[0]
            for i787, elem786 in enumerate(field785):
                if (i787 > 0):
                    self.newline()
                self.pretty_binding(elem786)
            field788 = unwrapped_fields784[1]
            if field788 is not None:
                self.newline()
                assert field788 is not None
                opt_val789 = field788
                self.pretty_value_bindings(opt_val789)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat795 = self._try_flat(msg, self.pretty_binding)
        if flat795 is not None:
            assert flat795 is not None
            self.write(flat795)
            return None
        else:
            _dollar_dollar = msg
            fields791 = (_dollar_dollar.var.name, _dollar_dollar.type,)
            assert fields791 is not None
            unwrapped_fields792 = fields791
            field793 = unwrapped_fields792[0]
            self.write(field793)
            self.write("::")
            field794 = unwrapped_fields792[1]
            self.pretty_type(field794)

    def pretty_type(self, msg: logic_pb2.Type):
        flat818 = self._try_flat(msg, self.pretty_type)
        if flat818 is not None:
            assert flat818 is not None
            self.write(flat818)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("unspecified_type"):
                _t1338 = _dollar_dollar.unspecified_type
            else:
                _t1338 = None
            deconstruct_result816 = _t1338
            if deconstruct_result816 is not None:
                assert deconstruct_result816 is not None
                unwrapped817 = deconstruct_result816
                self.pretty_unspecified_type(unwrapped817)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("string_type"):
                    _t1339 = _dollar_dollar.string_type
                else:
                    _t1339 = None
                deconstruct_result814 = _t1339
                if deconstruct_result814 is not None:
                    assert deconstruct_result814 is not None
                    unwrapped815 = deconstruct_result814
                    self.pretty_string_type(unwrapped815)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("int_type"):
                        _t1340 = _dollar_dollar.int_type
                    else:
                        _t1340 = None
                    deconstruct_result812 = _t1340
                    if deconstruct_result812 is not None:
                        assert deconstruct_result812 is not None
                        unwrapped813 = deconstruct_result812
                        self.pretty_int_type(unwrapped813)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("float_type"):
                            _t1341 = _dollar_dollar.float_type
                        else:
                            _t1341 = None
                        deconstruct_result810 = _t1341
                        if deconstruct_result810 is not None:
                            assert deconstruct_result810 is not None
                            unwrapped811 = deconstruct_result810
                            self.pretty_float_type(unwrapped811)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1342 = _dollar_dollar.uint128_type
                            else:
                                _t1342 = None
                            deconstruct_result808 = _t1342
                            if deconstruct_result808 is not None:
                                assert deconstruct_result808 is not None
                                unwrapped809 = deconstruct_result808
                                self.pretty_uint128_type(unwrapped809)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1343 = _dollar_dollar.int128_type
                                else:
                                    _t1343 = None
                                deconstruct_result806 = _t1343
                                if deconstruct_result806 is not None:
                                    assert deconstruct_result806 is not None
                                    unwrapped807 = deconstruct_result806
                                    self.pretty_int128_type(unwrapped807)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1344 = _dollar_dollar.date_type
                                    else:
                                        _t1344 = None
                                    deconstruct_result804 = _t1344
                                    if deconstruct_result804 is not None:
                                        assert deconstruct_result804 is not None
                                        unwrapped805 = deconstruct_result804
                                        self.pretty_date_type(unwrapped805)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1345 = _dollar_dollar.datetime_type
                                        else:
                                            _t1345 = None
                                        deconstruct_result802 = _t1345
                                        if deconstruct_result802 is not None:
                                            assert deconstruct_result802 is not None
                                            unwrapped803 = deconstruct_result802
                                            self.pretty_datetime_type(unwrapped803)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1346 = _dollar_dollar.missing_type
                                            else:
                                                _t1346 = None
                                            deconstruct_result800 = _t1346
                                            if deconstruct_result800 is not None:
                                                assert deconstruct_result800 is not None
                                                unwrapped801 = deconstruct_result800
                                                self.pretty_missing_type(unwrapped801)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1347 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1347 = None
                                                deconstruct_result798 = _t1347
                                                if deconstruct_result798 is not None:
                                                    assert deconstruct_result798 is not None
                                                    unwrapped799 = deconstruct_result798
                                                    self.pretty_decimal_type(unwrapped799)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1348 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1348 = None
                                                    deconstruct_result796 = _t1348
                                                    if deconstruct_result796 is not None:
                                                        assert deconstruct_result796 is not None
                                                        unwrapped797 = deconstruct_result796
                                                        self.pretty_boolean_type(unwrapped797)
                                                    else:
                                                        raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields819 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields820 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields821 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields822 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields823 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields824 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields825 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields826 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields827 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat832 = self._try_flat(msg, self.pretty_decimal_type)
        if flat832 is not None:
            assert flat832 is not None
            self.write(flat832)
            return None
        else:
            _dollar_dollar = msg
            fields828 = (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            assert fields828 is not None
            unwrapped_fields829 = fields828
            self.write("(DECIMAL")
            self.indent_sexp()
            self.newline()
            field830 = unwrapped_fields829[0]
            self.write(str(field830))
            self.newline()
            field831 = unwrapped_fields829[1]
            self.write(str(field831))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields833 = msg
        self.write("BOOLEAN")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat837 = self._try_flat(msg, self.pretty_value_bindings)
        if flat837 is not None:
            assert flat837 is not None
            self.write(flat837)
            return None
        else:
            fields834 = msg
            self.write("|")
            if not len(fields834) == 0:
                self.write(" ")
                for i836, elem835 in enumerate(fields834):
                    if (i836 > 0):
                        self.newline()
                    self.pretty_binding(elem835)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat864 = self._try_flat(msg, self.pretty_formula)
        if flat864 is not None:
            assert flat864 is not None
            self.write(flat864)
            return None
        else:
            _dollar_dollar = msg
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1349 = _dollar_dollar.conjunction
            else:
                _t1349 = None
            deconstruct_result862 = _t1349
            if deconstruct_result862 is not None:
                assert deconstruct_result862 is not None
                unwrapped863 = deconstruct_result862
                self.pretty_true(unwrapped863)
            else:
                _dollar_dollar = msg
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1350 = _dollar_dollar.disjunction
                else:
                    _t1350 = None
                deconstruct_result860 = _t1350
                if deconstruct_result860 is not None:
                    assert deconstruct_result860 is not None
                    unwrapped861 = deconstruct_result860
                    self.pretty_false(unwrapped861)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("exists"):
                        _t1351 = _dollar_dollar.exists
                    else:
                        _t1351 = None
                    deconstruct_result858 = _t1351
                    if deconstruct_result858 is not None:
                        assert deconstruct_result858 is not None
                        unwrapped859 = deconstruct_result858
                        self.pretty_exists(unwrapped859)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("reduce"):
                            _t1352 = _dollar_dollar.reduce
                        else:
                            _t1352 = None
                        deconstruct_result856 = _t1352
                        if deconstruct_result856 is not None:
                            assert deconstruct_result856 is not None
                            unwrapped857 = deconstruct_result856
                            self.pretty_reduce(unwrapped857)
                        else:
                            _dollar_dollar = msg
                            if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                _t1353 = _dollar_dollar.conjunction
                            else:
                                _t1353 = None
                            deconstruct_result854 = _t1353
                            if deconstruct_result854 is not None:
                                assert deconstruct_result854 is not None
                                unwrapped855 = deconstruct_result854
                                self.pretty_conjunction(unwrapped855)
                            else:
                                _dollar_dollar = msg
                                if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                    _t1354 = _dollar_dollar.disjunction
                                else:
                                    _t1354 = None
                                deconstruct_result852 = _t1354
                                if deconstruct_result852 is not None:
                                    assert deconstruct_result852 is not None
                                    unwrapped853 = deconstruct_result852
                                    self.pretty_disjunction(unwrapped853)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.HasField("not"):
                                        _t1355 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1355 = None
                                    deconstruct_result850 = _t1355
                                    if deconstruct_result850 is not None:
                                        assert deconstruct_result850 is not None
                                        unwrapped851 = deconstruct_result850
                                        self.pretty_not(unwrapped851)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1356 = _dollar_dollar.ffi
                                        else:
                                            _t1356 = None
                                        deconstruct_result848 = _t1356
                                        if deconstruct_result848 is not None:
                                            assert deconstruct_result848 is not None
                                            unwrapped849 = deconstruct_result848
                                            self.pretty_ffi(unwrapped849)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.HasField("atom"):
                                                _t1357 = _dollar_dollar.atom
                                            else:
                                                _t1357 = None
                                            deconstruct_result846 = _t1357
                                            if deconstruct_result846 is not None:
                                                assert deconstruct_result846 is not None
                                                unwrapped847 = deconstruct_result846
                                                self.pretty_atom(unwrapped847)
                                            else:
                                                _dollar_dollar = msg
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1358 = _dollar_dollar.pragma
                                                else:
                                                    _t1358 = None
                                                deconstruct_result844 = _t1358
                                                if deconstruct_result844 is not None:
                                                    assert deconstruct_result844 is not None
                                                    unwrapped845 = deconstruct_result844
                                                    self.pretty_pragma(unwrapped845)
                                                else:
                                                    _dollar_dollar = msg
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1359 = _dollar_dollar.primitive
                                                    else:
                                                        _t1359 = None
                                                    deconstruct_result842 = _t1359
                                                    if deconstruct_result842 is not None:
                                                        assert deconstruct_result842 is not None
                                                        unwrapped843 = deconstruct_result842
                                                        self.pretty_primitive(unwrapped843)
                                                    else:
                                                        _dollar_dollar = msg
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1360 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1360 = None
                                                        deconstruct_result840 = _t1360
                                                        if deconstruct_result840 is not None:
                                                            assert deconstruct_result840 is not None
                                                            unwrapped841 = deconstruct_result840
                                                            self.pretty_rel_atom(unwrapped841)
                                                        else:
                                                            _dollar_dollar = msg
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1361 = _dollar_dollar.cast
                                                            else:
                                                                _t1361 = None
                                                            deconstruct_result838 = _t1361
                                                            if deconstruct_result838 is not None:
                                                                assert deconstruct_result838 is not None
                                                                unwrapped839 = deconstruct_result838
                                                                self.pretty_cast(unwrapped839)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields865 = msg
        self.write("(true)")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields866 = msg
        self.write("(false)")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat871 = self._try_flat(msg, self.pretty_exists)
        if flat871 is not None:
            assert flat871 is not None
            self.write(flat871)
            return None
        else:
            _dollar_dollar = msg
            _t1362 = self.deconstruct_bindings(_dollar_dollar.body)
            fields867 = (_t1362, _dollar_dollar.body.value,)
            assert fields867 is not None
            unwrapped_fields868 = fields867
            self.write("(exists")
            self.indent_sexp()
            self.newline()
            field869 = unwrapped_fields868[0]
            self.pretty_bindings(field869)
            self.newline()
            field870 = unwrapped_fields868[1]
            self.pretty_formula(field870)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat877 = self._try_flat(msg, self.pretty_reduce)
        if flat877 is not None:
            assert flat877 is not None
            self.write(flat877)
            return None
        else:
            _dollar_dollar = msg
            fields872 = (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            assert fields872 is not None
            unwrapped_fields873 = fields872
            self.write("(reduce")
            self.indent_sexp()
            self.newline()
            field874 = unwrapped_fields873[0]
            self.pretty_abstraction(field874)
            self.newline()
            field875 = unwrapped_fields873[1]
            self.pretty_abstraction(field875)
            self.newline()
            field876 = unwrapped_fields873[2]
            self.pretty_terms(field876)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat881 = self._try_flat(msg, self.pretty_terms)
        if flat881 is not None:
            assert flat881 is not None
            self.write(flat881)
            return None
        else:
            fields878 = msg
            self.write("(terms")
            self.indent_sexp()
            if not len(fields878) == 0:
                self.newline()
                for i880, elem879 in enumerate(fields878):
                    if (i880 > 0):
                        self.newline()
                    self.pretty_term(elem879)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat886 = self._try_flat(msg, self.pretty_term)
        if flat886 is not None:
            assert flat886 is not None
            self.write(flat886)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("var"):
                _t1363 = _dollar_dollar.var
            else:
                _t1363 = None
            deconstruct_result884 = _t1363
            if deconstruct_result884 is not None:
                assert deconstruct_result884 is not None
                unwrapped885 = deconstruct_result884
                self.pretty_var(unwrapped885)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("constant"):
                    _t1364 = _dollar_dollar.constant
                else:
                    _t1364 = None
                deconstruct_result882 = _t1364
                if deconstruct_result882 is not None:
                    assert deconstruct_result882 is not None
                    unwrapped883 = deconstruct_result882
                    self.pretty_constant(unwrapped883)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat889 = self._try_flat(msg, self.pretty_var)
        if flat889 is not None:
            assert flat889 is not None
            self.write(flat889)
            return None
        else:
            _dollar_dollar = msg
            fields887 = _dollar_dollar.name
            assert fields887 is not None
            unwrapped_fields888 = fields887
            self.write(unwrapped_fields888)

    def pretty_constant(self, msg: logic_pb2.Value):
        flat891 = self._try_flat(msg, self.pretty_constant)
        if flat891 is not None:
            assert flat891 is not None
            self.write(flat891)
            return None
        else:
            fields890 = msg
            self.pretty_value(fields890)

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat896 = self._try_flat(msg, self.pretty_conjunction)
        if flat896 is not None:
            assert flat896 is not None
            self.write(flat896)
            return None
        else:
            _dollar_dollar = msg
            fields892 = _dollar_dollar.args
            assert fields892 is not None
            unwrapped_fields893 = fields892
            self.write("(and")
            self.indent_sexp()
            if not len(unwrapped_fields893) == 0:
                self.newline()
                for i895, elem894 in enumerate(unwrapped_fields893):
                    if (i895 > 0):
                        self.newline()
                    self.pretty_formula(elem894)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat901 = self._try_flat(msg, self.pretty_disjunction)
        if flat901 is not None:
            assert flat901 is not None
            self.write(flat901)
            return None
        else:
            _dollar_dollar = msg
            fields897 = _dollar_dollar.args
            assert fields897 is not None
            unwrapped_fields898 = fields897
            self.write("(or")
            self.indent_sexp()
            if not len(unwrapped_fields898) == 0:
                self.newline()
                for i900, elem899 in enumerate(unwrapped_fields898):
                    if (i900 > 0):
                        self.newline()
                    self.pretty_formula(elem899)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat904 = self._try_flat(msg, self.pretty_not)
        if flat904 is not None:
            assert flat904 is not None
            self.write(flat904)
            return None
        else:
            _dollar_dollar = msg
            fields902 = _dollar_dollar.arg
            assert fields902 is not None
            unwrapped_fields903 = fields902
            self.write("(not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields903)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat910 = self._try_flat(msg, self.pretty_ffi)
        if flat910 is not None:
            assert flat910 is not None
            self.write(flat910)
            return None
        else:
            _dollar_dollar = msg
            fields905 = (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            assert fields905 is not None
            unwrapped_fields906 = fields905
            self.write("(ffi")
            self.indent_sexp()
            self.newline()
            field907 = unwrapped_fields906[0]
            self.pretty_name(field907)
            self.newline()
            field908 = unwrapped_fields906[1]
            self.pretty_ffi_args(field908)
            self.newline()
            field909 = unwrapped_fields906[2]
            self.pretty_terms(field909)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat912 = self._try_flat(msg, self.pretty_name)
        if flat912 is not None:
            assert flat912 is not None
            self.write(flat912)
            return None
        else:
            fields911 = msg
            self.write(":")
            self.write(fields911)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat916 = self._try_flat(msg, self.pretty_ffi_args)
        if flat916 is not None:
            assert flat916 is not None
            self.write(flat916)
            return None
        else:
            fields913 = msg
            self.write("(args")
            self.indent_sexp()
            if not len(fields913) == 0:
                self.newline()
                for i915, elem914 in enumerate(fields913):
                    if (i915 > 0):
                        self.newline()
                    self.pretty_abstraction(elem914)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat923 = self._try_flat(msg, self.pretty_atom)
        if flat923 is not None:
            assert flat923 is not None
            self.write(flat923)
            return None
        else:
            _dollar_dollar = msg
            fields917 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields917 is not None
            unwrapped_fields918 = fields917
            self.write("(atom")
            self.indent_sexp()
            self.newline()
            field919 = unwrapped_fields918[0]
            self.pretty_relation_id(field919)
            field920 = unwrapped_fields918[1]
            if not len(field920) == 0:
                self.newline()
                for i922, elem921 in enumerate(field920):
                    if (i922 > 0):
                        self.newline()
                    self.pretty_term(elem921)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat930 = self._try_flat(msg, self.pretty_pragma)
        if flat930 is not None:
            assert flat930 is not None
            self.write(flat930)
            return None
        else:
            _dollar_dollar = msg
            fields924 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields924 is not None
            unwrapped_fields925 = fields924
            self.write("(pragma")
            self.indent_sexp()
            self.newline()
            field926 = unwrapped_fields925[0]
            self.pretty_name(field926)
            field927 = unwrapped_fields925[1]
            if not len(field927) == 0:
                self.newline()
                for i929, elem928 in enumerate(field927):
                    if (i929 > 0):
                        self.newline()
                    self.pretty_term(elem928)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat946 = self._try_flat(msg, self.pretty_primitive)
        if flat946 is not None:
            assert flat946 is not None
            self.write(flat946)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1365 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1365 = None
            guard_result945 = _t1365
            if guard_result945 is not None:
                self.pretty_eq(msg)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1366 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1366 = None
                guard_result944 = _t1366
                if guard_result944 is not None:
                    self.pretty_lt(msg)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1367 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1367 = None
                    guard_result943 = _t1367
                    if guard_result943 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1368 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1368 = None
                        guard_result942 = _t1368
                        if guard_result942 is not None:
                            self.pretty_gt(msg)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1369 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1369 = None
                            guard_result941 = _t1369
                            if guard_result941 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                _dollar_dollar = msg
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1370 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1370 = None
                                guard_result940 = _t1370
                                if guard_result940 is not None:
                                    self.pretty_add(msg)
                                else:
                                    _dollar_dollar = msg
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1371 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1371 = None
                                    guard_result939 = _t1371
                                    if guard_result939 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        _dollar_dollar = msg
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1372 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1372 = None
                                        guard_result938 = _t1372
                                        if guard_result938 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            _dollar_dollar = msg
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1373 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1373 = None
                                            guard_result937 = _t1373
                                            if guard_result937 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                _dollar_dollar = msg
                                                fields931 = (_dollar_dollar.name, _dollar_dollar.terms,)
                                                assert fields931 is not None
                                                unwrapped_fields932 = fields931
                                                self.write("(primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field933 = unwrapped_fields932[0]
                                                self.pretty_name(field933)
                                                field934 = unwrapped_fields932[1]
                                                if not len(field934) == 0:
                                                    self.newline()
                                                    for i936, elem935 in enumerate(field934):
                                                        if (i936 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem935)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat951 = self._try_flat(msg, self.pretty_eq)
        if flat951 is not None:
            assert flat951 is not None
            self.write(flat951)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1374 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1374 = None
            fields947 = _t1374
            assert fields947 is not None
            unwrapped_fields948 = fields947
            self.write("(=")
            self.indent_sexp()
            self.newline()
            field949 = unwrapped_fields948[0]
            self.pretty_term(field949)
            self.newline()
            field950 = unwrapped_fields948[1]
            self.pretty_term(field950)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat956 = self._try_flat(msg, self.pretty_lt)
        if flat956 is not None:
            assert flat956 is not None
            self.write(flat956)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1375 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1375 = None
            fields952 = _t1375
            assert fields952 is not None
            unwrapped_fields953 = fields952
            self.write("(<")
            self.indent_sexp()
            self.newline()
            field954 = unwrapped_fields953[0]
            self.pretty_term(field954)
            self.newline()
            field955 = unwrapped_fields953[1]
            self.pretty_term(field955)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat961 = self._try_flat(msg, self.pretty_lt_eq)
        if flat961 is not None:
            assert flat961 is not None
            self.write(flat961)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1376 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1376 = None
            fields957 = _t1376
            assert fields957 is not None
            unwrapped_fields958 = fields957
            self.write("(<=")
            self.indent_sexp()
            self.newline()
            field959 = unwrapped_fields958[0]
            self.pretty_term(field959)
            self.newline()
            field960 = unwrapped_fields958[1]
            self.pretty_term(field960)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat966 = self._try_flat(msg, self.pretty_gt)
        if flat966 is not None:
            assert flat966 is not None
            self.write(flat966)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1377 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1377 = None
            fields962 = _t1377
            assert fields962 is not None
            unwrapped_fields963 = fields962
            self.write("(>")
            self.indent_sexp()
            self.newline()
            field964 = unwrapped_fields963[0]
            self.pretty_term(field964)
            self.newline()
            field965 = unwrapped_fields963[1]
            self.pretty_term(field965)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat971 = self._try_flat(msg, self.pretty_gt_eq)
        if flat971 is not None:
            assert flat971 is not None
            self.write(flat971)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1378 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1378 = None
            fields967 = _t1378
            assert fields967 is not None
            unwrapped_fields968 = fields967
            self.write("(>=")
            self.indent_sexp()
            self.newline()
            field969 = unwrapped_fields968[0]
            self.pretty_term(field969)
            self.newline()
            field970 = unwrapped_fields968[1]
            self.pretty_term(field970)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat977 = self._try_flat(msg, self.pretty_add)
        if flat977 is not None:
            assert flat977 is not None
            self.write(flat977)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1379 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1379 = None
            fields972 = _t1379
            assert fields972 is not None
            unwrapped_fields973 = fields972
            self.write("(+")
            self.indent_sexp()
            self.newline()
            field974 = unwrapped_fields973[0]
            self.pretty_term(field974)
            self.newline()
            field975 = unwrapped_fields973[1]
            self.pretty_term(field975)
            self.newline()
            field976 = unwrapped_fields973[2]
            self.pretty_term(field976)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat983 = self._try_flat(msg, self.pretty_minus)
        if flat983 is not None:
            assert flat983 is not None
            self.write(flat983)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1380 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1380 = None
            fields978 = _t1380
            assert fields978 is not None
            unwrapped_fields979 = fields978
            self.write("(-")
            self.indent_sexp()
            self.newline()
            field980 = unwrapped_fields979[0]
            self.pretty_term(field980)
            self.newline()
            field981 = unwrapped_fields979[1]
            self.pretty_term(field981)
            self.newline()
            field982 = unwrapped_fields979[2]
            self.pretty_term(field982)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat989 = self._try_flat(msg, self.pretty_multiply)
        if flat989 is not None:
            assert flat989 is not None
            self.write(flat989)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1381 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1381 = None
            fields984 = _t1381
            assert fields984 is not None
            unwrapped_fields985 = fields984
            self.write("(*")
            self.indent_sexp()
            self.newline()
            field986 = unwrapped_fields985[0]
            self.pretty_term(field986)
            self.newline()
            field987 = unwrapped_fields985[1]
            self.pretty_term(field987)
            self.newline()
            field988 = unwrapped_fields985[2]
            self.pretty_term(field988)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat995 = self._try_flat(msg, self.pretty_divide)
        if flat995 is not None:
            assert flat995 is not None
            self.write(flat995)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1382 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1382 = None
            fields990 = _t1382
            assert fields990 is not None
            unwrapped_fields991 = fields990
            self.write("(/")
            self.indent_sexp()
            self.newline()
            field992 = unwrapped_fields991[0]
            self.pretty_term(field992)
            self.newline()
            field993 = unwrapped_fields991[1]
            self.pretty_term(field993)
            self.newline()
            field994 = unwrapped_fields991[2]
            self.pretty_term(field994)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat1000 = self._try_flat(msg, self.pretty_rel_term)
        if flat1000 is not None:
            assert flat1000 is not None
            self.write(flat1000)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("specialized_value"):
                _t1383 = _dollar_dollar.specialized_value
            else:
                _t1383 = None
            deconstruct_result998 = _t1383
            if deconstruct_result998 is not None:
                assert deconstruct_result998 is not None
                unwrapped999 = deconstruct_result998
                self.pretty_specialized_value(unwrapped999)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("term"):
                    _t1384 = _dollar_dollar.term
                else:
                    _t1384 = None
                deconstruct_result996 = _t1384
                if deconstruct_result996 is not None:
                    assert deconstruct_result996 is not None
                    unwrapped997 = deconstruct_result996
                    self.pretty_term(unwrapped997)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat1002 = self._try_flat(msg, self.pretty_specialized_value)
        if flat1002 is not None:
            assert flat1002 is not None
            self.write(flat1002)
            return None
        else:
            fields1001 = msg
            self.write("#")
            self.pretty_value(fields1001)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat1009 = self._try_flat(msg, self.pretty_rel_atom)
        if flat1009 is not None:
            assert flat1009 is not None
            self.write(flat1009)
            return None
        else:
            _dollar_dollar = msg
            fields1003 = (_dollar_dollar.name, _dollar_dollar.terms,)
            assert fields1003 is not None
            unwrapped_fields1004 = fields1003
            self.write("(relatom")
            self.indent_sexp()
            self.newline()
            field1005 = unwrapped_fields1004[0]
            self.pretty_name(field1005)
            field1006 = unwrapped_fields1004[1]
            if not len(field1006) == 0:
                self.newline()
                for i1008, elem1007 in enumerate(field1006):
                    if (i1008 > 0):
                        self.newline()
                    self.pretty_rel_term(elem1007)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1014 = self._try_flat(msg, self.pretty_cast)
        if flat1014 is not None:
            assert flat1014 is not None
            self.write(flat1014)
            return None
        else:
            _dollar_dollar = msg
            fields1010 = (_dollar_dollar.input, _dollar_dollar.result,)
            assert fields1010 is not None
            unwrapped_fields1011 = fields1010
            self.write("(cast")
            self.indent_sexp()
            self.newline()
            field1012 = unwrapped_fields1011[0]
            self.pretty_term(field1012)
            self.newline()
            field1013 = unwrapped_fields1011[1]
            self.pretty_term(field1013)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1018 = self._try_flat(msg, self.pretty_attrs)
        if flat1018 is not None:
            assert flat1018 is not None
            self.write(flat1018)
            return None
        else:
            fields1015 = msg
            self.write("(attrs")
            self.indent_sexp()
            if not len(fields1015) == 0:
                self.newline()
                for i1017, elem1016 in enumerate(fields1015):
                    if (i1017 > 0):
                        self.newline()
                    self.pretty_attribute(elem1016)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1025 = self._try_flat(msg, self.pretty_attribute)
        if flat1025 is not None:
            assert flat1025 is not None
            self.write(flat1025)
            return None
        else:
            _dollar_dollar = msg
            fields1019 = (_dollar_dollar.name, _dollar_dollar.args,)
            assert fields1019 is not None
            unwrapped_fields1020 = fields1019
            self.write("(attribute")
            self.indent_sexp()
            self.newline()
            field1021 = unwrapped_fields1020[0]
            self.pretty_name(field1021)
            field1022 = unwrapped_fields1020[1]
            if not len(field1022) == 0:
                self.newline()
                for i1024, elem1023 in enumerate(field1022):
                    if (i1024 > 0):
                        self.newline()
                    self.pretty_value(elem1023)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1032 = self._try_flat(msg, self.pretty_algorithm)
        if flat1032 is not None:
            assert flat1032 is not None
            self.write(flat1032)
            return None
        else:
            _dollar_dollar = msg
            fields1026 = (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            assert fields1026 is not None
            unwrapped_fields1027 = fields1026
            self.write("(algorithm")
            self.indent_sexp()
            field1028 = unwrapped_fields1027[0]
            if not len(field1028) == 0:
                self.newline()
                for i1030, elem1029 in enumerate(field1028):
                    if (i1030 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1029)
            self.newline()
            field1031 = unwrapped_fields1027[1]
            self.pretty_script(field1031)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1037 = self._try_flat(msg, self.pretty_script)
        if flat1037 is not None:
            assert flat1037 is not None
            self.write(flat1037)
            return None
        else:
            _dollar_dollar = msg
            fields1033 = _dollar_dollar.constructs
            assert fields1033 is not None
            unwrapped_fields1034 = fields1033
            self.write("(script")
            self.indent_sexp()
            if not len(unwrapped_fields1034) == 0:
                self.newline()
                for i1036, elem1035 in enumerate(unwrapped_fields1034):
                    if (i1036 > 0):
                        self.newline()
                    self.pretty_construct(elem1035)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1042 = self._try_flat(msg, self.pretty_construct)
        if flat1042 is not None:
            assert flat1042 is not None
            self.write(flat1042)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("loop"):
                _t1385 = _dollar_dollar.loop
            else:
                _t1385 = None
            deconstruct_result1040 = _t1385
            if deconstruct_result1040 is not None:
                assert deconstruct_result1040 is not None
                unwrapped1041 = deconstruct_result1040
                self.pretty_loop(unwrapped1041)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("instruction"):
                    _t1386 = _dollar_dollar.instruction
                else:
                    _t1386 = None
                deconstruct_result1038 = _t1386
                if deconstruct_result1038 is not None:
                    assert deconstruct_result1038 is not None
                    unwrapped1039 = deconstruct_result1038
                    self.pretty_instruction(unwrapped1039)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1047 = self._try_flat(msg, self.pretty_loop)
        if flat1047 is not None:
            assert flat1047 is not None
            self.write(flat1047)
            return None
        else:
            _dollar_dollar = msg
            fields1043 = (_dollar_dollar.init, _dollar_dollar.body,)
            assert fields1043 is not None
            unwrapped_fields1044 = fields1043
            self.write("(loop")
            self.indent_sexp()
            self.newline()
            field1045 = unwrapped_fields1044[0]
            self.pretty_init(field1045)
            self.newline()
            field1046 = unwrapped_fields1044[1]
            self.pretty_script(field1046)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1051 = self._try_flat(msg, self.pretty_init)
        if flat1051 is not None:
            assert flat1051 is not None
            self.write(flat1051)
            return None
        else:
            fields1048 = msg
            self.write("(init")
            self.indent_sexp()
            if not len(fields1048) == 0:
                self.newline()
                for i1050, elem1049 in enumerate(fields1048):
                    if (i1050 > 0):
                        self.newline()
                    self.pretty_instruction(elem1049)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1062 = self._try_flat(msg, self.pretty_instruction)
        if flat1062 is not None:
            assert flat1062 is not None
            self.write(flat1062)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("assign"):
                _t1387 = _dollar_dollar.assign
            else:
                _t1387 = None
            deconstruct_result1060 = _t1387
            if deconstruct_result1060 is not None:
                assert deconstruct_result1060 is not None
                unwrapped1061 = deconstruct_result1060
                self.pretty_assign(unwrapped1061)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("upsert"):
                    _t1388 = _dollar_dollar.upsert
                else:
                    _t1388 = None
                deconstruct_result1058 = _t1388
                if deconstruct_result1058 is not None:
                    assert deconstruct_result1058 is not None
                    unwrapped1059 = deconstruct_result1058
                    self.pretty_upsert(unwrapped1059)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("break"):
                        _t1389 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1389 = None
                    deconstruct_result1056 = _t1389
                    if deconstruct_result1056 is not None:
                        assert deconstruct_result1056 is not None
                        unwrapped1057 = deconstruct_result1056
                        self.pretty_break(unwrapped1057)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1390 = _dollar_dollar.monoid_def
                        else:
                            _t1390 = None
                        deconstruct_result1054 = _t1390
                        if deconstruct_result1054 is not None:
                            assert deconstruct_result1054 is not None
                            unwrapped1055 = deconstruct_result1054
                            self.pretty_monoid_def(unwrapped1055)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("monus_def"):
                                _t1391 = _dollar_dollar.monus_def
                            else:
                                _t1391 = None
                            deconstruct_result1052 = _t1391
                            if deconstruct_result1052 is not None:
                                assert deconstruct_result1052 is not None
                                unwrapped1053 = deconstruct_result1052
                                self.pretty_monus_def(unwrapped1053)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1069 = self._try_flat(msg, self.pretty_assign)
        if flat1069 is not None:
            assert flat1069 is not None
            self.write(flat1069)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1392 = _dollar_dollar.attrs
            else:
                _t1392 = None
            fields1063 = (_dollar_dollar.name, _dollar_dollar.body, _t1392,)
            assert fields1063 is not None
            unwrapped_fields1064 = fields1063
            self.write("(assign")
            self.indent_sexp()
            self.newline()
            field1065 = unwrapped_fields1064[0]
            self.pretty_relation_id(field1065)
            self.newline()
            field1066 = unwrapped_fields1064[1]
            self.pretty_abstraction(field1066)
            field1067 = unwrapped_fields1064[2]
            if field1067 is not None:
                self.newline()
                assert field1067 is not None
                opt_val1068 = field1067
                self.pretty_attrs(opt_val1068)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1076 = self._try_flat(msg, self.pretty_upsert)
        if flat1076 is not None:
            assert flat1076 is not None
            self.write(flat1076)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1393 = _dollar_dollar.attrs
            else:
                _t1393 = None
            fields1070 = (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1393,)
            assert fields1070 is not None
            unwrapped_fields1071 = fields1070
            self.write("(upsert")
            self.indent_sexp()
            self.newline()
            field1072 = unwrapped_fields1071[0]
            self.pretty_relation_id(field1072)
            self.newline()
            field1073 = unwrapped_fields1071[1]
            self.pretty_abstraction_with_arity(field1073)
            field1074 = unwrapped_fields1071[2]
            if field1074 is not None:
                self.newline()
                assert field1074 is not None
                opt_val1075 = field1074
                self.pretty_attrs(opt_val1075)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1081 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1081 is not None:
            assert flat1081 is not None
            self.write(flat1081)
            return None
        else:
            _dollar_dollar = msg
            _t1394 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            fields1077 = (_t1394, _dollar_dollar[0].value,)
            assert fields1077 is not None
            unwrapped_fields1078 = fields1077
            self.write("(")
            self.indent()
            field1079 = unwrapped_fields1078[0]
            self.pretty_bindings(field1079)
            self.newline()
            field1080 = unwrapped_fields1078[1]
            self.pretty_formula(field1080)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1088 = self._try_flat(msg, self.pretty_break)
        if flat1088 is not None:
            assert flat1088 is not None
            self.write(flat1088)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1395 = _dollar_dollar.attrs
            else:
                _t1395 = None
            fields1082 = (_dollar_dollar.name, _dollar_dollar.body, _t1395,)
            assert fields1082 is not None
            unwrapped_fields1083 = fields1082
            self.write("(break")
            self.indent_sexp()
            self.newline()
            field1084 = unwrapped_fields1083[0]
            self.pretty_relation_id(field1084)
            self.newline()
            field1085 = unwrapped_fields1083[1]
            self.pretty_abstraction(field1085)
            field1086 = unwrapped_fields1083[2]
            if field1086 is not None:
                self.newline()
                assert field1086 is not None
                opt_val1087 = field1086
                self.pretty_attrs(opt_val1087)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1096 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1096 is not None:
            assert flat1096 is not None
            self.write(flat1096)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1396 = _dollar_dollar.attrs
            else:
                _t1396 = None
            fields1089 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1396,)
            assert fields1089 is not None
            unwrapped_fields1090 = fields1089
            self.write("(monoid")
            self.indent_sexp()
            self.newline()
            field1091 = unwrapped_fields1090[0]
            self.pretty_monoid(field1091)
            self.newline()
            field1092 = unwrapped_fields1090[1]
            self.pretty_relation_id(field1092)
            self.newline()
            field1093 = unwrapped_fields1090[2]
            self.pretty_abstraction_with_arity(field1093)
            field1094 = unwrapped_fields1090[3]
            if field1094 is not None:
                self.newline()
                assert field1094 is not None
                opt_val1095 = field1094
                self.pretty_attrs(opt_val1095)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1105 = self._try_flat(msg, self.pretty_monoid)
        if flat1105 is not None:
            assert flat1105 is not None
            self.write(flat1105)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("or_monoid"):
                _t1397 = _dollar_dollar.or_monoid
            else:
                _t1397 = None
            deconstruct_result1103 = _t1397
            if deconstruct_result1103 is not None:
                assert deconstruct_result1103 is not None
                unwrapped1104 = deconstruct_result1103
                self.pretty_or_monoid(unwrapped1104)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("min_monoid"):
                    _t1398 = _dollar_dollar.min_monoid
                else:
                    _t1398 = None
                deconstruct_result1101 = _t1398
                if deconstruct_result1101 is not None:
                    assert deconstruct_result1101 is not None
                    unwrapped1102 = deconstruct_result1101
                    self.pretty_min_monoid(unwrapped1102)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1399 = _dollar_dollar.max_monoid
                    else:
                        _t1399 = None
                    deconstruct_result1099 = _t1399
                    if deconstruct_result1099 is not None:
                        assert deconstruct_result1099 is not None
                        unwrapped1100 = deconstruct_result1099
                        self.pretty_max_monoid(unwrapped1100)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1400 = _dollar_dollar.sum_monoid
                        else:
                            _t1400 = None
                        deconstruct_result1097 = _t1400
                        if deconstruct_result1097 is not None:
                            assert deconstruct_result1097 is not None
                            unwrapped1098 = deconstruct_result1097
                            self.pretty_sum_monoid(unwrapped1098)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1106 = msg
        self.write("(or)")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1109 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1109 is not None:
            assert flat1109 is not None
            self.write(flat1109)
            return None
        else:
            _dollar_dollar = msg
            fields1107 = _dollar_dollar.type
            assert fields1107 is not None
            unwrapped_fields1108 = fields1107
            self.write("(min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1108)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1112 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1112 is not None:
            assert flat1112 is not None
            self.write(flat1112)
            return None
        else:
            _dollar_dollar = msg
            fields1110 = _dollar_dollar.type
            assert fields1110 is not None
            unwrapped_fields1111 = fields1110
            self.write("(max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1111)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1115 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1115 is not None:
            assert flat1115 is not None
            self.write(flat1115)
            return None
        else:
            _dollar_dollar = msg
            fields1113 = _dollar_dollar.type
            assert fields1113 is not None
            unwrapped_fields1114 = fields1113
            self.write("(sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1114)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1123 = self._try_flat(msg, self.pretty_monus_def)
        if flat1123 is not None:
            assert flat1123 is not None
            self.write(flat1123)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.attrs) == 0:
                _t1401 = _dollar_dollar.attrs
            else:
                _t1401 = None
            fields1116 = (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1401,)
            assert fields1116 is not None
            unwrapped_fields1117 = fields1116
            self.write("(monus")
            self.indent_sexp()
            self.newline()
            field1118 = unwrapped_fields1117[0]
            self.pretty_monoid(field1118)
            self.newline()
            field1119 = unwrapped_fields1117[1]
            self.pretty_relation_id(field1119)
            self.newline()
            field1120 = unwrapped_fields1117[2]
            self.pretty_abstraction_with_arity(field1120)
            field1121 = unwrapped_fields1117[3]
            if field1121 is not None:
                self.newline()
                assert field1121 is not None
                opt_val1122 = field1121
                self.pretty_attrs(opt_val1122)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1130 = self._try_flat(msg, self.pretty_constraint)
        if flat1130 is not None:
            assert flat1130 is not None
            self.write(flat1130)
            return None
        else:
            _dollar_dollar = msg
            fields1124 = (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            assert fields1124 is not None
            unwrapped_fields1125 = fields1124
            self.write("(functional_dependency")
            self.indent_sexp()
            self.newline()
            field1126 = unwrapped_fields1125[0]
            self.pretty_relation_id(field1126)
            self.newline()
            field1127 = unwrapped_fields1125[1]
            self.pretty_abstraction(field1127)
            self.newline()
            field1128 = unwrapped_fields1125[2]
            self.pretty_functional_dependency_keys(field1128)
            self.newline()
            field1129 = unwrapped_fields1125[3]
            self.pretty_functional_dependency_values(field1129)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1134 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1134 is not None:
            assert flat1134 is not None
            self.write(flat1134)
            return None
        else:
            fields1131 = msg
            self.write("(keys")
            self.indent_sexp()
            if not len(fields1131) == 0:
                self.newline()
                for i1133, elem1132 in enumerate(fields1131):
                    if (i1133 > 0):
                        self.newline()
                    self.pretty_var(elem1132)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1138 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1138 is not None:
            assert flat1138 is not None
            self.write(flat1138)
            return None
        else:
            fields1135 = msg
            self.write("(values")
            self.indent_sexp()
            if not len(fields1135) == 0:
                self.newline()
                for i1137, elem1136 in enumerate(fields1135):
                    if (i1137 > 0):
                        self.newline()
                    self.pretty_var(elem1136)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1145 = self._try_flat(msg, self.pretty_data)
        if flat1145 is not None:
            assert flat1145 is not None
            self.write(flat1145)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("edb"):
                _t1402 = _dollar_dollar.edb
            else:
                _t1402 = None
            deconstruct_result1143 = _t1402
            if deconstruct_result1143 is not None:
                assert deconstruct_result1143 is not None
                unwrapped1144 = deconstruct_result1143
                self.pretty_edb(unwrapped1144)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("betree_relation"):
                    _t1403 = _dollar_dollar.betree_relation
                else:
                    _t1403 = None
                deconstruct_result1141 = _t1403
                if deconstruct_result1141 is not None:
                    assert deconstruct_result1141 is not None
                    unwrapped1142 = deconstruct_result1141
                    self.pretty_betree_relation(unwrapped1142)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("csv_data"):
                        _t1404 = _dollar_dollar.csv_data
                    else:
                        _t1404 = None
                    deconstruct_result1139 = _t1404
                    if deconstruct_result1139 is not None:
                        assert deconstruct_result1139 is not None
                        unwrapped1140 = deconstruct_result1139
                        self.pretty_csv_data(unwrapped1140)
                    else:
                        raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1151 = self._try_flat(msg, self.pretty_edb)
        if flat1151 is not None:
            assert flat1151 is not None
            self.write(flat1151)
            return None
        else:
            _dollar_dollar = msg
            fields1146 = (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            assert fields1146 is not None
            unwrapped_fields1147 = fields1146
            self.write("(edb")
            self.indent_sexp()
            self.newline()
            field1148 = unwrapped_fields1147[0]
            self.pretty_relation_id(field1148)
            self.newline()
            field1149 = unwrapped_fields1147[1]
            self.pretty_edb_path(field1149)
            self.newline()
            field1150 = unwrapped_fields1147[2]
            self.pretty_edb_types(field1150)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1155 = self._try_flat(msg, self.pretty_edb_path)
        if flat1155 is not None:
            assert flat1155 is not None
            self.write(flat1155)
            return None
        else:
            fields1152 = msg
            self.write("[")
            self.indent()
            for i1154, elem1153 in enumerate(fields1152):
                if (i1154 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1153))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1159 = self._try_flat(msg, self.pretty_edb_types)
        if flat1159 is not None:
            assert flat1159 is not None
            self.write(flat1159)
            return None
        else:
            fields1156 = msg
            self.write("[")
            self.indent()
            for i1158, elem1157 in enumerate(fields1156):
                if (i1158 > 0):
                    self.newline()
                self.pretty_type(elem1157)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1164 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1164 is not None:
            assert flat1164 is not None
            self.write(flat1164)
            return None
        else:
            _dollar_dollar = msg
            fields1160 = (_dollar_dollar.name, _dollar_dollar.relation_info,)
            assert fields1160 is not None
            unwrapped_fields1161 = fields1160
            self.write("(betree_relation")
            self.indent_sexp()
            self.newline()
            field1162 = unwrapped_fields1161[0]
            self.pretty_relation_id(field1162)
            self.newline()
            field1163 = unwrapped_fields1161[1]
            self.pretty_betree_info(field1163)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1170 = self._try_flat(msg, self.pretty_betree_info)
        if flat1170 is not None:
            assert flat1170 is not None
            self.write(flat1170)
            return None
        else:
            _dollar_dollar = msg
            _t1405 = self.deconstruct_betree_info_config(_dollar_dollar)
            fields1165 = (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1405,)
            assert fields1165 is not None
            unwrapped_fields1166 = fields1165
            self.write("(betree_info")
            self.indent_sexp()
            self.newline()
            field1167 = unwrapped_fields1166[0]
            self.pretty_betree_info_key_types(field1167)
            self.newline()
            field1168 = unwrapped_fields1166[1]
            self.pretty_betree_info_value_types(field1168)
            self.newline()
            field1169 = unwrapped_fields1166[2]
            self.pretty_config_dict(field1169)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1174 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1174 is not None:
            assert flat1174 is not None
            self.write(flat1174)
            return None
        else:
            fields1171 = msg
            self.write("(key_types")
            self.indent_sexp()
            if not len(fields1171) == 0:
                self.newline()
                for i1173, elem1172 in enumerate(fields1171):
                    if (i1173 > 0):
                        self.newline()
                    self.pretty_type(elem1172)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1178 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1178 is not None:
            assert flat1178 is not None
            self.write(flat1178)
            return None
        else:
            fields1175 = msg
            self.write("(value_types")
            self.indent_sexp()
            if not len(fields1175) == 0:
                self.newline()
                for i1177, elem1176 in enumerate(fields1175):
                    if (i1177 > 0):
                        self.newline()
                    self.pretty_type(elem1176)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1185 = self._try_flat(msg, self.pretty_csv_data)
        if flat1185 is not None:
            assert flat1185 is not None
            self.write(flat1185)
            return None
        else:
            _dollar_dollar = msg
            fields1179 = (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            assert fields1179 is not None
            unwrapped_fields1180 = fields1179
            self.write("(csv_data")
            self.indent_sexp()
            self.newline()
            field1181 = unwrapped_fields1180[0]
            self.pretty_csvlocator(field1181)
            self.newline()
            field1182 = unwrapped_fields1180[1]
            self.pretty_csv_config(field1182)
            self.newline()
            field1183 = unwrapped_fields1180[2]
            self.pretty_gnf_columns(field1183)
            self.newline()
            field1184 = unwrapped_fields1180[3]
            self.pretty_csv_asof(field1184)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1192 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1192 is not None:
            assert flat1192 is not None
            self.write(flat1192)
            return None
        else:
            _dollar_dollar = msg
            if not len(_dollar_dollar.paths) == 0:
                _t1406 = _dollar_dollar.paths
            else:
                _t1406 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1407 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1407 = None
            fields1186 = (_t1406, _t1407,)
            assert fields1186 is not None
            unwrapped_fields1187 = fields1186
            self.write("(csv_locator")
            self.indent_sexp()
            field1188 = unwrapped_fields1187[0]
            if field1188 is not None:
                self.newline()
                assert field1188 is not None
                opt_val1189 = field1188
                self.pretty_csv_locator_paths(opt_val1189)
            field1190 = unwrapped_fields1187[1]
            if field1190 is not None:
                self.newline()
                assert field1190 is not None
                opt_val1191 = field1190
                self.pretty_csv_locator_inline_data(opt_val1191)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1196 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1196 is not None:
            assert flat1196 is not None
            self.write(flat1196)
            return None
        else:
            fields1193 = msg
            self.write("(paths")
            self.indent_sexp()
            if not len(fields1193) == 0:
                self.newline()
                for i1195, elem1194 in enumerate(fields1193):
                    if (i1195 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1194))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1198 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1198 is not None:
            assert flat1198 is not None
            self.write(flat1198)
            return None
        else:
            fields1197 = msg
            self.write("(inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1197))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1201 = self._try_flat(msg, self.pretty_csv_config)
        if flat1201 is not None:
            assert flat1201 is not None
            self.write(flat1201)
            return None
        else:
            _dollar_dollar = msg
            _t1408 = self.deconstruct_csv_config(_dollar_dollar)
            fields1199 = _t1408
            assert fields1199 is not None
            unwrapped_fields1200 = fields1199
            self.write("(csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1200)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1205 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1205 is not None:
            assert flat1205 is not None
            self.write(flat1205)
            return None
        else:
            fields1202 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1202) == 0:
                self.newline()
                for i1204, elem1203 in enumerate(fields1202):
                    if (i1204 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1203)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1214 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1214 is not None:
            assert flat1214 is not None
            self.write(flat1214)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("target_id"):
                _t1409 = _dollar_dollar.target_id
            else:
                _t1409 = None
            fields1206 = (_dollar_dollar.column_path, _t1409, _dollar_dollar.types,)
            assert fields1206 is not None
            unwrapped_fields1207 = fields1206
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1208 = unwrapped_fields1207[0]
            self.pretty_gnf_column_path(field1208)
            field1209 = unwrapped_fields1207[1]
            if field1209 is not None:
                self.newline()
                assert field1209 is not None
                opt_val1210 = field1209
                self.pretty_relation_id(opt_val1210)
            self.newline()
            self.write("[")
            field1211 = unwrapped_fields1207[2]
            for i1213, elem1212 in enumerate(field1211):
                if (i1213 > 0):
                    self.newline()
                self.pretty_type(elem1212)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1221 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1221 is not None:
            assert flat1221 is not None
            self.write(flat1221)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar) == 1:
                _t1410 = _dollar_dollar[0]
            else:
                _t1410 = None
            deconstruct_result1219 = _t1410
            if deconstruct_result1219 is not None:
                assert deconstruct_result1219 is not None
                unwrapped1220 = deconstruct_result1219
                self.write(self.format_string_value(unwrapped1220))
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar) != 1:
                    _t1411 = _dollar_dollar
                else:
                    _t1411 = None
                deconstruct_result1215 = _t1411
                if deconstruct_result1215 is not None:
                    assert deconstruct_result1215 is not None
                    unwrapped1216 = deconstruct_result1215
                    self.write("[")
                    self.indent()
                    for i1218, elem1217 in enumerate(unwrapped1216):
                        if (i1218 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1217))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1223 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1223 is not None:
            assert flat1223 is not None
            self.write(flat1223)
            return None
        else:
            fields1222 = msg
            self.write("(asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1222))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1226 = self._try_flat(msg, self.pretty_undefine)
        if flat1226 is not None:
            assert flat1226 is not None
            self.write(flat1226)
            return None
        else:
            _dollar_dollar = msg
            fields1224 = _dollar_dollar.fragment_id
            assert fields1224 is not None
            unwrapped_fields1225 = fields1224
            self.write("(undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1225)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1231 = self._try_flat(msg, self.pretty_context)
        if flat1231 is not None:
            assert flat1231 is not None
            self.write(flat1231)
            return None
        else:
            _dollar_dollar = msg
            fields1227 = _dollar_dollar.relations
            assert fields1227 is not None
            unwrapped_fields1228 = fields1227
            self.write("(context")
            self.indent_sexp()
            if not len(unwrapped_fields1228) == 0:
                self.newline()
                for i1230, elem1229 in enumerate(unwrapped_fields1228):
                    if (i1230 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1229)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1236 = self._try_flat(msg, self.pretty_snapshot)
        if flat1236 is not None:
            assert flat1236 is not None
            self.write(flat1236)
            return None
        else:
            _dollar_dollar = msg
            fields1232 = _dollar_dollar.mappings
            assert fields1232 is not None
            unwrapped_fields1233 = fields1232
            self.write("(snapshot")
            self.indent_sexp()
            if not len(unwrapped_fields1233) == 0:
                self.newline()
                for i1235, elem1234 in enumerate(unwrapped_fields1233):
                    if (i1235 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1234)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1241 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1241 is not None:
            assert flat1241 is not None
            self.write(flat1241)
            return None
        else:
            _dollar_dollar = msg
            fields1237 = (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            assert fields1237 is not None
            unwrapped_fields1238 = fields1237
            field1239 = unwrapped_fields1238[0]
            self.pretty_edb_path(field1239)
            self.write(" ")
            field1240 = unwrapped_fields1238[1]
            self.pretty_relation_id(field1240)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1245 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1245 is not None:
            assert flat1245 is not None
            self.write(flat1245)
            return None
        else:
            fields1242 = msg
            self.write("(reads")
            self.indent_sexp()
            if not len(fields1242) == 0:
                self.newline()
                for i1244, elem1243 in enumerate(fields1242):
                    if (i1244 > 0):
                        self.newline()
                    self.pretty_read(elem1243)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1256 = self._try_flat(msg, self.pretty_read)
        if flat1256 is not None:
            assert flat1256 is not None
            self.write(flat1256)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("demand"):
                _t1412 = _dollar_dollar.demand
            else:
                _t1412 = None
            deconstruct_result1254 = _t1412
            if deconstruct_result1254 is not None:
                assert deconstruct_result1254 is not None
                unwrapped1255 = deconstruct_result1254
                self.pretty_demand(unwrapped1255)
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("output"):
                    _t1413 = _dollar_dollar.output
                else:
                    _t1413 = None
                deconstruct_result1252 = _t1413
                if deconstruct_result1252 is not None:
                    assert deconstruct_result1252 is not None
                    unwrapped1253 = deconstruct_result1252
                    self.pretty_output(unwrapped1253)
                else:
                    _dollar_dollar = msg
                    if _dollar_dollar.HasField("what_if"):
                        _t1414 = _dollar_dollar.what_if
                    else:
                        _t1414 = None
                    deconstruct_result1250 = _t1414
                    if deconstruct_result1250 is not None:
                        assert deconstruct_result1250 is not None
                        unwrapped1251 = deconstruct_result1250
                        self.pretty_what_if(unwrapped1251)
                    else:
                        _dollar_dollar = msg
                        if _dollar_dollar.HasField("abort"):
                            _t1415 = _dollar_dollar.abort
                        else:
                            _t1415 = None
                        deconstruct_result1248 = _t1415
                        if deconstruct_result1248 is not None:
                            assert deconstruct_result1248 is not None
                            unwrapped1249 = deconstruct_result1248
                            self.pretty_abort(unwrapped1249)
                        else:
                            _dollar_dollar = msg
                            if _dollar_dollar.HasField("export"):
                                _t1416 = _dollar_dollar.export
                            else:
                                _t1416 = None
                            deconstruct_result1246 = _t1416
                            if deconstruct_result1246 is not None:
                                assert deconstruct_result1246 is not None
                                unwrapped1247 = deconstruct_result1246
                                self.pretty_export(unwrapped1247)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1259 = self._try_flat(msg, self.pretty_demand)
        if flat1259 is not None:
            assert flat1259 is not None
            self.write(flat1259)
            return None
        else:
            _dollar_dollar = msg
            fields1257 = _dollar_dollar.relation_id
            assert fields1257 is not None
            unwrapped_fields1258 = fields1257
            self.write("(demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1258)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1264 = self._try_flat(msg, self.pretty_output)
        if flat1264 is not None:
            assert flat1264 is not None
            self.write(flat1264)
            return None
        else:
            _dollar_dollar = msg
            fields1260 = (_dollar_dollar.name, _dollar_dollar.relation_id,)
            assert fields1260 is not None
            unwrapped_fields1261 = fields1260
            self.write("(output")
            self.indent_sexp()
            self.newline()
            field1262 = unwrapped_fields1261[0]
            self.pretty_name(field1262)
            self.newline()
            field1263 = unwrapped_fields1261[1]
            self.pretty_relation_id(field1263)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1269 = self._try_flat(msg, self.pretty_what_if)
        if flat1269 is not None:
            assert flat1269 is not None
            self.write(flat1269)
            return None
        else:
            _dollar_dollar = msg
            fields1265 = (_dollar_dollar.branch, _dollar_dollar.epoch,)
            assert fields1265 is not None
            unwrapped_fields1266 = fields1265
            self.write("(what_if")
            self.indent_sexp()
            self.newline()
            field1267 = unwrapped_fields1266[0]
            self.pretty_name(field1267)
            self.newline()
            field1268 = unwrapped_fields1266[1]
            self.pretty_epoch(field1268)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1275 = self._try_flat(msg, self.pretty_abort)
        if flat1275 is not None:
            assert flat1275 is not None
            self.write(flat1275)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.name != "abort":
                _t1417 = _dollar_dollar.name
            else:
                _t1417 = None
            fields1270 = (_t1417, _dollar_dollar.relation_id,)
            assert fields1270 is not None
            unwrapped_fields1271 = fields1270
            self.write("(abort")
            self.indent_sexp()
            field1272 = unwrapped_fields1271[0]
            if field1272 is not None:
                self.newline()
                assert field1272 is not None
                opt_val1273 = field1272
                self.pretty_name(opt_val1273)
            self.newline()
            field1274 = unwrapped_fields1271[1]
            self.pretty_relation_id(field1274)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1278 = self._try_flat(msg, self.pretty_export)
        if flat1278 is not None:
            assert flat1278 is not None
            self.write(flat1278)
            return None
        else:
            _dollar_dollar = msg
            fields1276 = _dollar_dollar.csv_config
            assert fields1276 is not None
            unwrapped_fields1277 = fields1276
            self.write("(export")
            self.indent_sexp()
            self.newline()
            self.pretty_export_csv_config(unwrapped_fields1277)
            self.dedent()
            self.write(")")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1289 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1289 is not None:
            assert flat1289 is not None
            self.write(flat1289)
            return None
        else:
            _dollar_dollar = msg
            if len(_dollar_dollar.data_columns) == 0:
                _t1418 = (_dollar_dollar.path, _dollar_dollar.csv_source, _dollar_dollar.csv_config,)
            else:
                _t1418 = None
            deconstruct_result1284 = _t1418
            if deconstruct_result1284 is not None:
                assert deconstruct_result1284 is not None
                unwrapped1285 = deconstruct_result1284
                self.write("(export_csv_config_v2")
                self.indent_sexp()
                self.newline()
                field1286 = unwrapped1285[0]
                self.pretty_export_csv_path(field1286)
                self.newline()
                field1287 = unwrapped1285[1]
                self.pretty_export_csv_source(field1287)
                self.newline()
                field1288 = unwrapped1285[2]
                self.pretty_csv_config(field1288)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if len(_dollar_dollar.data_columns) != 0:
                    _t1420 = self.deconstruct_export_csv_config(_dollar_dollar)
                    _t1419 = (_dollar_dollar.path, _dollar_dollar.data_columns, _t1420,)
                else:
                    _t1419 = None
                deconstruct_result1279 = _t1419
                if deconstruct_result1279 is not None:
                    assert deconstruct_result1279 is not None
                    unwrapped1280 = deconstruct_result1279
                    self.write("(export_csv_config")
                    self.indent_sexp()
                    self.newline()
                    field1281 = unwrapped1280[0]
                    self.pretty_export_csv_path(field1281)
                    self.newline()
                    field1282 = unwrapped1280[1]
                    self.pretty_export_csv_columns_list(field1282)
                    self.newline()
                    field1283 = unwrapped1280[2]
                    self.pretty_config_dict(field1283)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_config")

    def pretty_export_csv_path(self, msg: str):
        flat1291 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1291 is not None:
            assert flat1291 is not None
            self.write(flat1291)
            return None
        else:
            fields1290 = msg
            self.write("(path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1290))
            self.dedent()
            self.write(")")

    def pretty_export_csv_source(self, msg: transactions_pb2.ExportCSVSource):
        flat1298 = self._try_flat(msg, self.pretty_export_csv_source)
        if flat1298 is not None:
            assert flat1298 is not None
            self.write(flat1298)
            return None
        else:
            _dollar_dollar = msg
            if _dollar_dollar.HasField("gnf_columns"):
                _t1421 = _dollar_dollar.gnf_columns.columns
            else:
                _t1421 = None
            deconstruct_result1294 = _t1421
            if deconstruct_result1294 is not None:
                assert deconstruct_result1294 is not None
                unwrapped1295 = deconstruct_result1294
                self.write("(gnf_columns")
                self.indent_sexp()
                if not len(unwrapped1295) == 0:
                    self.newline()
                    for i1297, elem1296 in enumerate(unwrapped1295):
                        if (i1297 > 0):
                            self.newline()
                        self.pretty_export_csv_column(elem1296)
                self.dedent()
                self.write(")")
            else:
                _dollar_dollar = msg
                if _dollar_dollar.HasField("table_def"):
                    _t1422 = _dollar_dollar.table_def
                else:
                    _t1422 = None
                deconstruct_result1292 = _t1422
                if deconstruct_result1292 is not None:
                    assert deconstruct_result1292 is not None
                    unwrapped1293 = deconstruct_result1292
                    self.write("(table_def")
                    self.indent_sexp()
                    self.newline()
                    self.pretty_relation_id(unwrapped1293)
                    self.dedent()
                    self.write(")")
                else:
                    raise ParseError("No matching rule for export_csv_source")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1303 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1303 is not None:
            assert flat1303 is not None
            self.write(flat1303)
            return None
        else:
            _dollar_dollar = msg
            fields1299 = (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            assert fields1299 is not None
            unwrapped_fields1300 = fields1299
            self.write("(column")
            self.indent_sexp()
            self.newline()
            field1301 = unwrapped_fields1300[0]
            self.write(self.format_string_value(field1301))
            self.newline()
            field1302 = unwrapped_fields1300[1]
            self.pretty_relation_id(field1302)
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns_list(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1307 = self._try_flat(msg, self.pretty_export_csv_columns_list)
        if flat1307 is not None:
            assert flat1307 is not None
            self.write(flat1307)
            return None
        else:
            fields1304 = msg
            self.write("(columns")
            self.indent_sexp()
            if not len(fields1304) == 0:
                self.newline()
                for i1306, elem1305 in enumerate(fields1304):
                    if (i1306 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1305)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1461 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1461)
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

def pretty(msg: Any, io: Optional[IO[str]] = None, max_width: int = 92) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io, max_width=max_width)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()


def pretty_debug(msg: Any, io: Optional[IO[str]] = None, max_width: int = 92) -> str:
    """Pretty print a protobuf message with raw relation IDs and debug info appended as comments."""
    printer = PrettyPrinter(io, max_width=max_width, print_symbolic_relation_ids=False)
    printer.pretty_transaction(msg)
    printer.newline()
    printer.write_debug_info()
    return printer.get_output()
