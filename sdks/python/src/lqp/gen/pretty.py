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
        _t1677 = logic_pb2.Value(int_value=int(v))
        return _t1677

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1678 = logic_pb2.Value(int_value=v)
        return _t1678

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1679 = logic_pb2.Value(float_value=v)
        return _t1679

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1680 = logic_pb2.Value(string_value=v)
        return _t1680

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1681 = logic_pb2.Value(boolean_value=v)
        return _t1681

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1682 = logic_pb2.Value(uint128_value=v)
        return _t1682

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1683 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1683,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1684 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1684,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1685 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1685,))
        _t1686 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1686,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1687 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1687,))
        _t1688 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1688,))
        if msg.new_line != "":
            _t1689 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1689,))
        _t1690 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1690,))
        _t1691 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1691,))
        _t1692 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1692,))
        if msg.comment != "":
            _t1693 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1693,))
        for missing_string in msg.missing_strings:
            _t1694 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1694,))
        _t1695 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1695,))
        _t1696 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1696,))
        _t1697 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1697,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1698 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1698,))
        _t1699 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1699,))
        _t1700 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1700,))
        _t1701 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1701,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1702 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1702,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1703 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1703,))
        _t1704 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1704,))
        _t1705 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1705,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1706 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1706,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1707 = self._make_value_string(msg.compression)
            result.append(("compression", _t1707,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1708 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1708,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1709 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1709,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1710 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1710,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1711 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1711,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1712 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1712,))
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
            _t1713 = None
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
        flat646 = self._try_flat(msg, self.pretty_transaction)
        if flat646 is not None:
            assert flat646 is not None
            self.write(flat646)
            return None
        else:
            def _t1274(_dollar_dollar):
                if _dollar_dollar.HasField("configure"):
                    _t1275 = _dollar_dollar.configure
                else:
                    _t1275 = None
                if _dollar_dollar.HasField("sync"):
                    _t1276 = _dollar_dollar.sync
                else:
                    _t1276 = None
                return (_t1275, _t1276, _dollar_dollar.epochs,)
            _t1277 = _t1274(msg)
            fields637 = _t1277
            assert fields637 is not None
            unwrapped_fields638 = fields637
            self.write("(")
            self.write("transaction")
            self.indent_sexp()
            field639 = unwrapped_fields638[0]
            if field639 is not None:
                self.newline()
                assert field639 is not None
                opt_val640 = field639
                self.pretty_configure(opt_val640)
            field641 = unwrapped_fields638[1]
            if field641 is not None:
                self.newline()
                assert field641 is not None
                opt_val642 = field641
                self.pretty_sync(opt_val642)
            field643 = unwrapped_fields638[2]
            if not len(field643) == 0:
                self.newline()
                for i645, elem644 in enumerate(field643):
                    if (i645 > 0):
                        self.newline()
                    self.pretty_epoch(elem644)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat649 = self._try_flat(msg, self.pretty_configure)
        if flat649 is not None:
            assert flat649 is not None
            self.write(flat649)
            return None
        else:
            def _t1278(_dollar_dollar):
                _t1279 = self.deconstruct_configure(_dollar_dollar)
                return _t1279
            _t1280 = _t1278(msg)
            fields647 = _t1280
            assert fields647 is not None
            unwrapped_fields648 = fields647
            self.write("(")
            self.write("configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields648)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat653 = self._try_flat(msg, self.pretty_config_dict)
        if flat653 is not None:
            assert flat653 is not None
            self.write(flat653)
            return None
        else:
            fields650 = msg
            self.write("{")
            self.indent()
            if not len(fields650) == 0:
                self.newline()
                for i652, elem651 in enumerate(fields650):
                    if (i652 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem651)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat658 = self._try_flat(msg, self.pretty_config_key_value)
        if flat658 is not None:
            assert flat658 is not None
            self.write(flat658)
            return None
        else:
            def _t1281(_dollar_dollar):
                return (_dollar_dollar[0], _dollar_dollar[1],)
            _t1282 = _t1281(msg)
            fields654 = _t1282
            assert fields654 is not None
            unwrapped_fields655 = fields654
            self.write(":")
            field656 = unwrapped_fields655[0]
            self.write(field656)
            self.write(" ")
            field657 = unwrapped_fields655[1]
            self.pretty_value(field657)

    def pretty_value(self, msg: logic_pb2.Value):
        flat678 = self._try_flat(msg, self.pretty_value)
        if flat678 is not None:
            assert flat678 is not None
            self.write(flat678)
            return None
        else:
            def _t1283(_dollar_dollar):
                if _dollar_dollar.HasField("date_value"):
                    _t1284 = _dollar_dollar.date_value
                else:
                    _t1284 = None
                return _t1284
            _t1285 = _t1283(msg)
            deconstruct_result676 = _t1285
            if deconstruct_result676 is not None:
                assert deconstruct_result676 is not None
                unwrapped677 = deconstruct_result676
                self.pretty_date(unwrapped677)
            else:
                def _t1286(_dollar_dollar):
                    if _dollar_dollar.HasField("datetime_value"):
                        _t1287 = _dollar_dollar.datetime_value
                    else:
                        _t1287 = None
                    return _t1287
                _t1288 = _t1286(msg)
                deconstruct_result674 = _t1288
                if deconstruct_result674 is not None:
                    assert deconstruct_result674 is not None
                    unwrapped675 = deconstruct_result674
                    self.pretty_datetime(unwrapped675)
                else:
                    def _t1289(_dollar_dollar):
                        if _dollar_dollar.HasField("string_value"):
                            _t1290 = _dollar_dollar.string_value
                        else:
                            _t1290 = None
                        return _t1290
                    _t1291 = _t1289(msg)
                    deconstruct_result672 = _t1291
                    if deconstruct_result672 is not None:
                        assert deconstruct_result672 is not None
                        unwrapped673 = deconstruct_result672
                        self.write(self.format_string_value(unwrapped673))
                    else:
                        def _t1292(_dollar_dollar):
                            if _dollar_dollar.HasField("int_value"):
                                _t1293 = _dollar_dollar.int_value
                            else:
                                _t1293 = None
                            return _t1293
                        _t1294 = _t1292(msg)
                        deconstruct_result670 = _t1294
                        if deconstruct_result670 is not None:
                            assert deconstruct_result670 is not None
                            unwrapped671 = deconstruct_result670
                            self.write(str(unwrapped671))
                        else:
                            def _t1295(_dollar_dollar):
                                if _dollar_dollar.HasField("float_value"):
                                    _t1296 = _dollar_dollar.float_value
                                else:
                                    _t1296 = None
                                return _t1296
                            _t1297 = _t1295(msg)
                            deconstruct_result668 = _t1297
                            if deconstruct_result668 is not None:
                                assert deconstruct_result668 is not None
                                unwrapped669 = deconstruct_result668
                                self.write(str(unwrapped669))
                            else:
                                def _t1298(_dollar_dollar):
                                    if _dollar_dollar.HasField("uint128_value"):
                                        _t1299 = _dollar_dollar.uint128_value
                                    else:
                                        _t1299 = None
                                    return _t1299
                                _t1300 = _t1298(msg)
                                deconstruct_result666 = _t1300
                                if deconstruct_result666 is not None:
                                    assert deconstruct_result666 is not None
                                    unwrapped667 = deconstruct_result666
                                    self.write(self.format_uint128(unwrapped667))
                                else:
                                    def _t1301(_dollar_dollar):
                                        if _dollar_dollar.HasField("int128_value"):
                                            _t1302 = _dollar_dollar.int128_value
                                        else:
                                            _t1302 = None
                                        return _t1302
                                    _t1303 = _t1301(msg)
                                    deconstruct_result664 = _t1303
                                    if deconstruct_result664 is not None:
                                        assert deconstruct_result664 is not None
                                        unwrapped665 = deconstruct_result664
                                        self.write(self.format_int128(unwrapped665))
                                    else:
                                        def _t1304(_dollar_dollar):
                                            if _dollar_dollar.HasField("decimal_value"):
                                                _t1305 = _dollar_dollar.decimal_value
                                            else:
                                                _t1305 = None
                                            return _t1305
                                        _t1306 = _t1304(msg)
                                        deconstruct_result662 = _t1306
                                        if deconstruct_result662 is not None:
                                            assert deconstruct_result662 is not None
                                            unwrapped663 = deconstruct_result662
                                            self.write(self.format_decimal(unwrapped663))
                                        else:
                                            def _t1307(_dollar_dollar):
                                                if _dollar_dollar.HasField("boolean_value"):
                                                    _t1308 = _dollar_dollar.boolean_value
                                                else:
                                                    _t1308 = None
                                                return _t1308
                                            _t1309 = _t1307(msg)
                                            deconstruct_result660 = _t1309
                                            if deconstruct_result660 is not None:
                                                assert deconstruct_result660 is not None
                                                unwrapped661 = deconstruct_result660
                                                self.pretty_boolean_value(unwrapped661)
                                            else:
                                                fields659 = msg
                                                self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat684 = self._try_flat(msg, self.pretty_date)
        if flat684 is not None:
            assert flat684 is not None
            self.write(flat684)
            return None
        else:
            def _t1310(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            _t1311 = _t1310(msg)
            fields679 = _t1311
            assert fields679 is not None
            unwrapped_fields680 = fields679
            self.write("(")
            self.write("date")
            self.indent_sexp()
            self.newline()
            field681 = unwrapped_fields680[0]
            self.write(str(field681))
            self.newline()
            field682 = unwrapped_fields680[1]
            self.write(str(field682))
            self.newline()
            field683 = unwrapped_fields680[2]
            self.write(str(field683))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat695 = self._try_flat(msg, self.pretty_datetime)
        if flat695 is not None:
            assert flat695 is not None
            self.write(flat695)
            return None
        else:
            def _t1312(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            _t1313 = _t1312(msg)
            fields685 = _t1313
            assert fields685 is not None
            unwrapped_fields686 = fields685
            self.write("(")
            self.write("datetime")
            self.indent_sexp()
            self.newline()
            field687 = unwrapped_fields686[0]
            self.write(str(field687))
            self.newline()
            field688 = unwrapped_fields686[1]
            self.write(str(field688))
            self.newline()
            field689 = unwrapped_fields686[2]
            self.write(str(field689))
            self.newline()
            field690 = unwrapped_fields686[3]
            self.write(str(field690))
            self.newline()
            field691 = unwrapped_fields686[4]
            self.write(str(field691))
            self.newline()
            field692 = unwrapped_fields686[5]
            self.write(str(field692))
            field693 = unwrapped_fields686[6]
            if field693 is not None:
                self.newline()
                assert field693 is not None
                opt_val694 = field693
                self.write(str(opt_val694))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        def _t1314(_dollar_dollar):
            if _dollar_dollar:
                _t1315 = ()
            else:
                _t1315 = None
            return _t1315
        _t1316 = _t1314(msg)
        deconstruct_result698 = _t1316
        if deconstruct_result698 is not None:
            assert deconstruct_result698 is not None
            unwrapped699 = deconstruct_result698
            self.write("true")
        else:
            def _t1317(_dollar_dollar):
                if not _dollar_dollar:
                    _t1318 = ()
                else:
                    _t1318 = None
                return _t1318
            _t1319 = _t1317(msg)
            deconstruct_result696 = _t1319
            if deconstruct_result696 is not None:
                assert deconstruct_result696 is not None
                unwrapped697 = deconstruct_result696
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat704 = self._try_flat(msg, self.pretty_sync)
        if flat704 is not None:
            assert flat704 is not None
            self.write(flat704)
            return None
        else:
            def _t1320(_dollar_dollar):
                return _dollar_dollar.fragments
            _t1321 = _t1320(msg)
            fields700 = _t1321
            assert fields700 is not None
            unwrapped_fields701 = fields700
            self.write("(")
            self.write("sync")
            self.indent_sexp()
            if not len(unwrapped_fields701) == 0:
                self.newline()
                for i703, elem702 in enumerate(unwrapped_fields701):
                    if (i703 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem702)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat707 = self._try_flat(msg, self.pretty_fragment_id)
        if flat707 is not None:
            assert flat707 is not None
            self.write(flat707)
            return None
        else:
            def _t1322(_dollar_dollar):
                return self.fragment_id_to_string(_dollar_dollar)
            _t1323 = _t1322(msg)
            fields705 = _t1323
            assert fields705 is not None
            unwrapped_fields706 = fields705
            self.write(":")
            self.write(unwrapped_fields706)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat714 = self._try_flat(msg, self.pretty_epoch)
        if flat714 is not None:
            assert flat714 is not None
            self.write(flat714)
            return None
        else:
            def _t1324(_dollar_dollar):
                if not len(_dollar_dollar.writes) == 0:
                    _t1325 = _dollar_dollar.writes
                else:
                    _t1325 = None
                if not len(_dollar_dollar.reads) == 0:
                    _t1326 = _dollar_dollar.reads
                else:
                    _t1326 = None
                return (_t1325, _t1326,)
            _t1327 = _t1324(msg)
            fields708 = _t1327
            assert fields708 is not None
            unwrapped_fields709 = fields708
            self.write("(")
            self.write("epoch")
            self.indent_sexp()
            field710 = unwrapped_fields709[0]
            if field710 is not None:
                self.newline()
                assert field710 is not None
                opt_val711 = field710
                self.pretty_epoch_writes(opt_val711)
            field712 = unwrapped_fields709[1]
            if field712 is not None:
                self.newline()
                assert field712 is not None
                opt_val713 = field712
                self.pretty_epoch_reads(opt_val713)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat718 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat718 is not None:
            assert flat718 is not None
            self.write(flat718)
            return None
        else:
            fields715 = msg
            self.write("(")
            self.write("writes")
            self.indent_sexp()
            if not len(fields715) == 0:
                self.newline()
                for i717, elem716 in enumerate(fields715):
                    if (i717 > 0):
                        self.newline()
                    self.pretty_write(elem716)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat727 = self._try_flat(msg, self.pretty_write)
        if flat727 is not None:
            assert flat727 is not None
            self.write(flat727)
            return None
        else:
            def _t1328(_dollar_dollar):
                if _dollar_dollar.HasField("define"):
                    _t1329 = _dollar_dollar.define
                else:
                    _t1329 = None
                return _t1329
            _t1330 = _t1328(msg)
            deconstruct_result725 = _t1330
            if deconstruct_result725 is not None:
                assert deconstruct_result725 is not None
                unwrapped726 = deconstruct_result725
                self.pretty_define(unwrapped726)
            else:
                def _t1331(_dollar_dollar):
                    if _dollar_dollar.HasField("undefine"):
                        _t1332 = _dollar_dollar.undefine
                    else:
                        _t1332 = None
                    return _t1332
                _t1333 = _t1331(msg)
                deconstruct_result723 = _t1333
                if deconstruct_result723 is not None:
                    assert deconstruct_result723 is not None
                    unwrapped724 = deconstruct_result723
                    self.pretty_undefine(unwrapped724)
                else:
                    def _t1334(_dollar_dollar):
                        if _dollar_dollar.HasField("context"):
                            _t1335 = _dollar_dollar.context
                        else:
                            _t1335 = None
                        return _t1335
                    _t1336 = _t1334(msg)
                    deconstruct_result721 = _t1336
                    if deconstruct_result721 is not None:
                        assert deconstruct_result721 is not None
                        unwrapped722 = deconstruct_result721
                        self.pretty_context(unwrapped722)
                    else:
                        def _t1337(_dollar_dollar):
                            if _dollar_dollar.HasField("snapshot"):
                                _t1338 = _dollar_dollar.snapshot
                            else:
                                _t1338 = None
                            return _t1338
                        _t1339 = _t1337(msg)
                        deconstruct_result719 = _t1339
                        if deconstruct_result719 is not None:
                            assert deconstruct_result719 is not None
                            unwrapped720 = deconstruct_result719
                            self.pretty_snapshot(unwrapped720)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat730 = self._try_flat(msg, self.pretty_define)
        if flat730 is not None:
            assert flat730 is not None
            self.write(flat730)
            return None
        else:
            def _t1340(_dollar_dollar):
                return _dollar_dollar.fragment
            _t1341 = _t1340(msg)
            fields728 = _t1341
            assert fields728 is not None
            unwrapped_fields729 = fields728
            self.write("(")
            self.write("define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields729)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat737 = self._try_flat(msg, self.pretty_fragment)
        if flat737 is not None:
            assert flat737 is not None
            self.write(flat737)
            return None
        else:
            def _t1342(_dollar_dollar):
                self.start_pretty_fragment(_dollar_dollar)
                return (_dollar_dollar.id, _dollar_dollar.declarations,)
            _t1343 = _t1342(msg)
            fields731 = _t1343
            assert fields731 is not None
            unwrapped_fields732 = fields731
            self.write("(")
            self.write("fragment")
            self.indent_sexp()
            self.newline()
            field733 = unwrapped_fields732[0]
            self.pretty_new_fragment_id(field733)
            field734 = unwrapped_fields732[1]
            if not len(field734) == 0:
                self.newline()
                for i736, elem735 in enumerate(field734):
                    if (i736 > 0):
                        self.newline()
                    self.pretty_declaration(elem735)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat739 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat739 is not None:
            assert flat739 is not None
            self.write(flat739)
            return None
        else:
            fields738 = msg
            self.pretty_fragment_id(fields738)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat748 = self._try_flat(msg, self.pretty_declaration)
        if flat748 is not None:
            assert flat748 is not None
            self.write(flat748)
            return None
        else:
            def _t1344(_dollar_dollar):
                if _dollar_dollar.HasField("def"):
                    _t1345 = getattr(_dollar_dollar, 'def')
                else:
                    _t1345 = None
                return _t1345
            _t1346 = _t1344(msg)
            deconstruct_result746 = _t1346
            if deconstruct_result746 is not None:
                assert deconstruct_result746 is not None
                unwrapped747 = deconstruct_result746
                self.pretty_def(unwrapped747)
            else:
                def _t1347(_dollar_dollar):
                    if _dollar_dollar.HasField("algorithm"):
                        _t1348 = _dollar_dollar.algorithm
                    else:
                        _t1348 = None
                    return _t1348
                _t1349 = _t1347(msg)
                deconstruct_result744 = _t1349
                if deconstruct_result744 is not None:
                    assert deconstruct_result744 is not None
                    unwrapped745 = deconstruct_result744
                    self.pretty_algorithm(unwrapped745)
                else:
                    def _t1350(_dollar_dollar):
                        if _dollar_dollar.HasField("constraint"):
                            _t1351 = _dollar_dollar.constraint
                        else:
                            _t1351 = None
                        return _t1351
                    _t1352 = _t1350(msg)
                    deconstruct_result742 = _t1352
                    if deconstruct_result742 is not None:
                        assert deconstruct_result742 is not None
                        unwrapped743 = deconstruct_result742
                        self.pretty_constraint(unwrapped743)
                    else:
                        def _t1353(_dollar_dollar):
                            if _dollar_dollar.HasField("data"):
                                _t1354 = _dollar_dollar.data
                            else:
                                _t1354 = None
                            return _t1354
                        _t1355 = _t1353(msg)
                        deconstruct_result740 = _t1355
                        if deconstruct_result740 is not None:
                            assert deconstruct_result740 is not None
                            unwrapped741 = deconstruct_result740
                            self.pretty_data(unwrapped741)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat755 = self._try_flat(msg, self.pretty_def)
        if flat755 is not None:
            assert flat755 is not None
            self.write(flat755)
            return None
        else:
            def _t1356(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1357 = _dollar_dollar.attrs
                else:
                    _t1357 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1357,)
            _t1358 = _t1356(msg)
            fields749 = _t1358
            assert fields749 is not None
            unwrapped_fields750 = fields749
            self.write("(")
            self.write("def")
            self.indent_sexp()
            self.newline()
            field751 = unwrapped_fields750[0]
            self.pretty_relation_id(field751)
            self.newline()
            field752 = unwrapped_fields750[1]
            self.pretty_abstraction(field752)
            field753 = unwrapped_fields750[2]
            if field753 is not None:
                self.newline()
                assert field753 is not None
                opt_val754 = field753
                self.pretty_attrs(opt_val754)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat760 = self._try_flat(msg, self.pretty_relation_id)
        if flat760 is not None:
            assert flat760 is not None
            self.write(flat760)
            return None
        else:
            def _t1359(_dollar_dollar):
                if self.relation_id_to_string(_dollar_dollar) is not None:
                    _t1361 = self.deconstruct_relation_id_string(_dollar_dollar)
                    _t1360 = _t1361
                else:
                    _t1360 = None
                return _t1360
            _t1362 = _t1359(msg)
            deconstruct_result758 = _t1362
            if deconstruct_result758 is not None:
                assert deconstruct_result758 is not None
                unwrapped759 = deconstruct_result758
                self.write(":")
                self.write(unwrapped759)
            else:
                def _t1363(_dollar_dollar):
                    _t1364 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                    return _t1364
                _t1365 = _t1363(msg)
                deconstruct_result756 = _t1365
                if deconstruct_result756 is not None:
                    assert deconstruct_result756 is not None
                    unwrapped757 = deconstruct_result756
                    self.write(self.format_uint128(unwrapped757))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat765 = self._try_flat(msg, self.pretty_abstraction)
        if flat765 is not None:
            assert flat765 is not None
            self.write(flat765)
            return None
        else:
            def _t1366(_dollar_dollar):
                _t1367 = self.deconstruct_bindings(_dollar_dollar)
                return (_t1367, _dollar_dollar.value,)
            _t1368 = _t1366(msg)
            fields761 = _t1368
            assert fields761 is not None
            unwrapped_fields762 = fields761
            self.write("(")
            self.indent()
            field763 = unwrapped_fields762[0]
            self.pretty_bindings(field763)
            self.newline()
            field764 = unwrapped_fields762[1]
            self.pretty_formula(field764)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat773 = self._try_flat(msg, self.pretty_bindings)
        if flat773 is not None:
            assert flat773 is not None
            self.write(flat773)
            return None
        else:
            def _t1369(_dollar_dollar):
                if not len(_dollar_dollar[1]) == 0:
                    _t1370 = _dollar_dollar[1]
                else:
                    _t1370 = None
                return (_dollar_dollar[0], _t1370,)
            _t1371 = _t1369(msg)
            fields766 = _t1371
            assert fields766 is not None
            unwrapped_fields767 = fields766
            self.write("[")
            self.indent()
            field768 = unwrapped_fields767[0]
            for i770, elem769 in enumerate(field768):
                if (i770 > 0):
                    self.newline()
                self.pretty_binding(elem769)
            field771 = unwrapped_fields767[1]
            if field771 is not None:
                self.newline()
                assert field771 is not None
                opt_val772 = field771
                self.pretty_value_bindings(opt_val772)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat778 = self._try_flat(msg, self.pretty_binding)
        if flat778 is not None:
            assert flat778 is not None
            self.write(flat778)
            return None
        else:
            def _t1372(_dollar_dollar):
                return (_dollar_dollar.var.name, _dollar_dollar.type,)
            _t1373 = _t1372(msg)
            fields774 = _t1373
            assert fields774 is not None
            unwrapped_fields775 = fields774
            field776 = unwrapped_fields775[0]
            self.write(field776)
            self.write("::")
            field777 = unwrapped_fields775[1]
            self.pretty_type(field777)

    def pretty_type(self, msg: logic_pb2.Type):
        flat801 = self._try_flat(msg, self.pretty_type)
        if flat801 is not None:
            assert flat801 is not None
            self.write(flat801)
            return None
        else:
            def _t1374(_dollar_dollar):
                if _dollar_dollar.HasField("unspecified_type"):
                    _t1375 = _dollar_dollar.unspecified_type
                else:
                    _t1375 = None
                return _t1375
            _t1376 = _t1374(msg)
            deconstruct_result799 = _t1376
            if deconstruct_result799 is not None:
                assert deconstruct_result799 is not None
                unwrapped800 = deconstruct_result799
                self.pretty_unspecified_type(unwrapped800)
            else:
                def _t1377(_dollar_dollar):
                    if _dollar_dollar.HasField("string_type"):
                        _t1378 = _dollar_dollar.string_type
                    else:
                        _t1378 = None
                    return _t1378
                _t1379 = _t1377(msg)
                deconstruct_result797 = _t1379
                if deconstruct_result797 is not None:
                    assert deconstruct_result797 is not None
                    unwrapped798 = deconstruct_result797
                    self.pretty_string_type(unwrapped798)
                else:
                    def _t1380(_dollar_dollar):
                        if _dollar_dollar.HasField("int_type"):
                            _t1381 = _dollar_dollar.int_type
                        else:
                            _t1381 = None
                        return _t1381
                    _t1382 = _t1380(msg)
                    deconstruct_result795 = _t1382
                    if deconstruct_result795 is not None:
                        assert deconstruct_result795 is not None
                        unwrapped796 = deconstruct_result795
                        self.pretty_int_type(unwrapped796)
                    else:
                        def _t1383(_dollar_dollar):
                            if _dollar_dollar.HasField("float_type"):
                                _t1384 = _dollar_dollar.float_type
                            else:
                                _t1384 = None
                            return _t1384
                        _t1385 = _t1383(msg)
                        deconstruct_result793 = _t1385
                        if deconstruct_result793 is not None:
                            assert deconstruct_result793 is not None
                            unwrapped794 = deconstruct_result793
                            self.pretty_float_type(unwrapped794)
                        else:
                            def _t1386(_dollar_dollar):
                                if _dollar_dollar.HasField("uint128_type"):
                                    _t1387 = _dollar_dollar.uint128_type
                                else:
                                    _t1387 = None
                                return _t1387
                            _t1388 = _t1386(msg)
                            deconstruct_result791 = _t1388
                            if deconstruct_result791 is not None:
                                assert deconstruct_result791 is not None
                                unwrapped792 = deconstruct_result791
                                self.pretty_uint128_type(unwrapped792)
                            else:
                                def _t1389(_dollar_dollar):
                                    if _dollar_dollar.HasField("int128_type"):
                                        _t1390 = _dollar_dollar.int128_type
                                    else:
                                        _t1390 = None
                                    return _t1390
                                _t1391 = _t1389(msg)
                                deconstruct_result789 = _t1391
                                if deconstruct_result789 is not None:
                                    assert deconstruct_result789 is not None
                                    unwrapped790 = deconstruct_result789
                                    self.pretty_int128_type(unwrapped790)
                                else:
                                    def _t1392(_dollar_dollar):
                                        if _dollar_dollar.HasField("date_type"):
                                            _t1393 = _dollar_dollar.date_type
                                        else:
                                            _t1393 = None
                                        return _t1393
                                    _t1394 = _t1392(msg)
                                    deconstruct_result787 = _t1394
                                    if deconstruct_result787 is not None:
                                        assert deconstruct_result787 is not None
                                        unwrapped788 = deconstruct_result787
                                        self.pretty_date_type(unwrapped788)
                                    else:
                                        def _t1395(_dollar_dollar):
                                            if _dollar_dollar.HasField("datetime_type"):
                                                _t1396 = _dollar_dollar.datetime_type
                                            else:
                                                _t1396 = None
                                            return _t1396
                                        _t1397 = _t1395(msg)
                                        deconstruct_result785 = _t1397
                                        if deconstruct_result785 is not None:
                                            assert deconstruct_result785 is not None
                                            unwrapped786 = deconstruct_result785
                                            self.pretty_datetime_type(unwrapped786)
                                        else:
                                            def _t1398(_dollar_dollar):
                                                if _dollar_dollar.HasField("missing_type"):
                                                    _t1399 = _dollar_dollar.missing_type
                                                else:
                                                    _t1399 = None
                                                return _t1399
                                            _t1400 = _t1398(msg)
                                            deconstruct_result783 = _t1400
                                            if deconstruct_result783 is not None:
                                                assert deconstruct_result783 is not None
                                                unwrapped784 = deconstruct_result783
                                                self.pretty_missing_type(unwrapped784)
                                            else:
                                                def _t1401(_dollar_dollar):
                                                    if _dollar_dollar.HasField("decimal_type"):
                                                        _t1402 = _dollar_dollar.decimal_type
                                                    else:
                                                        _t1402 = None
                                                    return _t1402
                                                _t1403 = _t1401(msg)
                                                deconstruct_result781 = _t1403
                                                if deconstruct_result781 is not None:
                                                    assert deconstruct_result781 is not None
                                                    unwrapped782 = deconstruct_result781
                                                    self.pretty_decimal_type(unwrapped782)
                                                else:
                                                    def _t1404(_dollar_dollar):
                                                        if _dollar_dollar.HasField("boolean_type"):
                                                            _t1405 = _dollar_dollar.boolean_type
                                                        else:
                                                            _t1405 = None
                                                        return _t1405
                                                    _t1406 = _t1404(msg)
                                                    deconstruct_result779 = _t1406
                                                    if deconstruct_result779 is not None:
                                                        assert deconstruct_result779 is not None
                                                        unwrapped780 = deconstruct_result779
                                                        self.pretty_boolean_type(unwrapped780)
                                                    else:
                                                        raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields802 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields803 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields804 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields805 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields806 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields807 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields808 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields809 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields810 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat815 = self._try_flat(msg, self.pretty_decimal_type)
        if flat815 is not None:
            assert flat815 is not None
            self.write(flat815)
            return None
        else:
            def _t1407(_dollar_dollar):
                return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            _t1408 = _t1407(msg)
            fields811 = _t1408
            assert fields811 is not None
            unwrapped_fields812 = fields811
            self.write("(")
            self.write("DECIMAL")
            self.indent_sexp()
            self.newline()
            field813 = unwrapped_fields812[0]
            self.write(str(field813))
            self.newline()
            field814 = unwrapped_fields812[1]
            self.write(str(field814))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields816 = msg
        self.write("BOOLEAN")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat820 = self._try_flat(msg, self.pretty_value_bindings)
        if flat820 is not None:
            assert flat820 is not None
            self.write(flat820)
            return None
        else:
            fields817 = msg
            self.write("|")
            if not len(fields817) == 0:
                self.write(" ")
                for i819, elem818 in enumerate(fields817):
                    if (i819 > 0):
                        self.newline()
                    self.pretty_binding(elem818)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat847 = self._try_flat(msg, self.pretty_formula)
        if flat847 is not None:
            assert flat847 is not None
            self.write(flat847)
            return None
        else:
            def _t1409(_dollar_dollar):
                if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                    _t1410 = _dollar_dollar.conjunction
                else:
                    _t1410 = None
                return _t1410
            _t1411 = _t1409(msg)
            deconstruct_result845 = _t1411
            if deconstruct_result845 is not None:
                assert deconstruct_result845 is not None
                unwrapped846 = deconstruct_result845
                self.pretty_true(unwrapped846)
            else:
                def _t1412(_dollar_dollar):
                    if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                        _t1413 = _dollar_dollar.disjunction
                    else:
                        _t1413 = None
                    return _t1413
                _t1414 = _t1412(msg)
                deconstruct_result843 = _t1414
                if deconstruct_result843 is not None:
                    assert deconstruct_result843 is not None
                    unwrapped844 = deconstruct_result843
                    self.pretty_false(unwrapped844)
                else:
                    def _t1415(_dollar_dollar):
                        if _dollar_dollar.HasField("exists"):
                            _t1416 = _dollar_dollar.exists
                        else:
                            _t1416 = None
                        return _t1416
                    _t1417 = _t1415(msg)
                    deconstruct_result841 = _t1417
                    if deconstruct_result841 is not None:
                        assert deconstruct_result841 is not None
                        unwrapped842 = deconstruct_result841
                        self.pretty_exists(unwrapped842)
                    else:
                        def _t1418(_dollar_dollar):
                            if _dollar_dollar.HasField("reduce"):
                                _t1419 = _dollar_dollar.reduce
                            else:
                                _t1419 = None
                            return _t1419
                        _t1420 = _t1418(msg)
                        deconstruct_result839 = _t1420
                        if deconstruct_result839 is not None:
                            assert deconstruct_result839 is not None
                            unwrapped840 = deconstruct_result839
                            self.pretty_reduce(unwrapped840)
                        else:
                            def _t1421(_dollar_dollar):
                                if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                    _t1422 = _dollar_dollar.conjunction
                                else:
                                    _t1422 = None
                                return _t1422
                            _t1423 = _t1421(msg)
                            deconstruct_result837 = _t1423
                            if deconstruct_result837 is not None:
                                assert deconstruct_result837 is not None
                                unwrapped838 = deconstruct_result837
                                self.pretty_conjunction(unwrapped838)
                            else:
                                def _t1424(_dollar_dollar):
                                    if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                        _t1425 = _dollar_dollar.disjunction
                                    else:
                                        _t1425 = None
                                    return _t1425
                                _t1426 = _t1424(msg)
                                deconstruct_result835 = _t1426
                                if deconstruct_result835 is not None:
                                    assert deconstruct_result835 is not None
                                    unwrapped836 = deconstruct_result835
                                    self.pretty_disjunction(unwrapped836)
                                else:
                                    def _t1427(_dollar_dollar):
                                        if _dollar_dollar.HasField("not"):
                                            _t1428 = getattr(_dollar_dollar, 'not')
                                        else:
                                            _t1428 = None
                                        return _t1428
                                    _t1429 = _t1427(msg)
                                    deconstruct_result833 = _t1429
                                    if deconstruct_result833 is not None:
                                        assert deconstruct_result833 is not None
                                        unwrapped834 = deconstruct_result833
                                        self.pretty_not(unwrapped834)
                                    else:
                                        def _t1430(_dollar_dollar):
                                            if _dollar_dollar.HasField("ffi"):
                                                _t1431 = _dollar_dollar.ffi
                                            else:
                                                _t1431 = None
                                            return _t1431
                                        _t1432 = _t1430(msg)
                                        deconstruct_result831 = _t1432
                                        if deconstruct_result831 is not None:
                                            assert deconstruct_result831 is not None
                                            unwrapped832 = deconstruct_result831
                                            self.pretty_ffi(unwrapped832)
                                        else:
                                            def _t1433(_dollar_dollar):
                                                if _dollar_dollar.HasField("atom"):
                                                    _t1434 = _dollar_dollar.atom
                                                else:
                                                    _t1434 = None
                                                return _t1434
                                            _t1435 = _t1433(msg)
                                            deconstruct_result829 = _t1435
                                            if deconstruct_result829 is not None:
                                                assert deconstruct_result829 is not None
                                                unwrapped830 = deconstruct_result829
                                                self.pretty_atom(unwrapped830)
                                            else:
                                                def _t1436(_dollar_dollar):
                                                    if _dollar_dollar.HasField("pragma"):
                                                        _t1437 = _dollar_dollar.pragma
                                                    else:
                                                        _t1437 = None
                                                    return _t1437
                                                _t1438 = _t1436(msg)
                                                deconstruct_result827 = _t1438
                                                if deconstruct_result827 is not None:
                                                    assert deconstruct_result827 is not None
                                                    unwrapped828 = deconstruct_result827
                                                    self.pretty_pragma(unwrapped828)
                                                else:
                                                    def _t1439(_dollar_dollar):
                                                        if _dollar_dollar.HasField("primitive"):
                                                            _t1440 = _dollar_dollar.primitive
                                                        else:
                                                            _t1440 = None
                                                        return _t1440
                                                    _t1441 = _t1439(msg)
                                                    deconstruct_result825 = _t1441
                                                    if deconstruct_result825 is not None:
                                                        assert deconstruct_result825 is not None
                                                        unwrapped826 = deconstruct_result825
                                                        self.pretty_primitive(unwrapped826)
                                                    else:
                                                        def _t1442(_dollar_dollar):
                                                            if _dollar_dollar.HasField("rel_atom"):
                                                                _t1443 = _dollar_dollar.rel_atom
                                                            else:
                                                                _t1443 = None
                                                            return _t1443
                                                        _t1444 = _t1442(msg)
                                                        deconstruct_result823 = _t1444
                                                        if deconstruct_result823 is not None:
                                                            assert deconstruct_result823 is not None
                                                            unwrapped824 = deconstruct_result823
                                                            self.pretty_rel_atom(unwrapped824)
                                                        else:
                                                            def _t1445(_dollar_dollar):
                                                                if _dollar_dollar.HasField("cast"):
                                                                    _t1446 = _dollar_dollar.cast
                                                                else:
                                                                    _t1446 = None
                                                                return _t1446
                                                            _t1447 = _t1445(msg)
                                                            deconstruct_result821 = _t1447
                                                            if deconstruct_result821 is not None:
                                                                assert deconstruct_result821 is not None
                                                                unwrapped822 = deconstruct_result821
                                                                self.pretty_cast(unwrapped822)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields848 = msg
        self.write("(")
        self.write("true")
        self.write(")")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields849 = msg
        self.write("(")
        self.write("false")
        self.write(")")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat854 = self._try_flat(msg, self.pretty_exists)
        if flat854 is not None:
            assert flat854 is not None
            self.write(flat854)
            return None
        else:
            def _t1448(_dollar_dollar):
                _t1449 = self.deconstruct_bindings(_dollar_dollar.body)
                return (_t1449, _dollar_dollar.body.value,)
            _t1450 = _t1448(msg)
            fields850 = _t1450
            assert fields850 is not None
            unwrapped_fields851 = fields850
            self.write("(")
            self.write("exists")
            self.indent_sexp()
            self.newline()
            field852 = unwrapped_fields851[0]
            self.pretty_bindings(field852)
            self.newline()
            field853 = unwrapped_fields851[1]
            self.pretty_formula(field853)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat860 = self._try_flat(msg, self.pretty_reduce)
        if flat860 is not None:
            assert flat860 is not None
            self.write(flat860)
            return None
        else:
            def _t1451(_dollar_dollar):
                return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            _t1452 = _t1451(msg)
            fields855 = _t1452
            assert fields855 is not None
            unwrapped_fields856 = fields855
            self.write("(")
            self.write("reduce")
            self.indent_sexp()
            self.newline()
            field857 = unwrapped_fields856[0]
            self.pretty_abstraction(field857)
            self.newline()
            field858 = unwrapped_fields856[1]
            self.pretty_abstraction(field858)
            self.newline()
            field859 = unwrapped_fields856[2]
            self.pretty_terms(field859)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat864 = self._try_flat(msg, self.pretty_terms)
        if flat864 is not None:
            assert flat864 is not None
            self.write(flat864)
            return None
        else:
            fields861 = msg
            self.write("(")
            self.write("terms")
            self.indent_sexp()
            if not len(fields861) == 0:
                self.newline()
                for i863, elem862 in enumerate(fields861):
                    if (i863 > 0):
                        self.newline()
                    self.pretty_term(elem862)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat869 = self._try_flat(msg, self.pretty_term)
        if flat869 is not None:
            assert flat869 is not None
            self.write(flat869)
            return None
        else:
            def _t1453(_dollar_dollar):
                if _dollar_dollar.HasField("var"):
                    _t1454 = _dollar_dollar.var
                else:
                    _t1454 = None
                return _t1454
            _t1455 = _t1453(msg)
            deconstruct_result867 = _t1455
            if deconstruct_result867 is not None:
                assert deconstruct_result867 is not None
                unwrapped868 = deconstruct_result867
                self.pretty_var(unwrapped868)
            else:
                def _t1456(_dollar_dollar):
                    if _dollar_dollar.HasField("constant"):
                        _t1457 = _dollar_dollar.constant
                    else:
                        _t1457 = None
                    return _t1457
                _t1458 = _t1456(msg)
                deconstruct_result865 = _t1458
                if deconstruct_result865 is not None:
                    assert deconstruct_result865 is not None
                    unwrapped866 = deconstruct_result865
                    self.pretty_constant(unwrapped866)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat872 = self._try_flat(msg, self.pretty_var)
        if flat872 is not None:
            assert flat872 is not None
            self.write(flat872)
            return None
        else:
            def _t1459(_dollar_dollar):
                return _dollar_dollar.name
            _t1460 = _t1459(msg)
            fields870 = _t1460
            assert fields870 is not None
            unwrapped_fields871 = fields870
            self.write(unwrapped_fields871)

    def pretty_constant(self, msg: logic_pb2.Value):
        flat874 = self._try_flat(msg, self.pretty_constant)
        if flat874 is not None:
            assert flat874 is not None
            self.write(flat874)
            return None
        else:
            fields873 = msg
            self.pretty_value(fields873)

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat879 = self._try_flat(msg, self.pretty_conjunction)
        if flat879 is not None:
            assert flat879 is not None
            self.write(flat879)
            return None
        else:
            def _t1461(_dollar_dollar):
                return _dollar_dollar.args
            _t1462 = _t1461(msg)
            fields875 = _t1462
            assert fields875 is not None
            unwrapped_fields876 = fields875
            self.write("(")
            self.write("and")
            self.indent_sexp()
            if not len(unwrapped_fields876) == 0:
                self.newline()
                for i878, elem877 in enumerate(unwrapped_fields876):
                    if (i878 > 0):
                        self.newline()
                    self.pretty_formula(elem877)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat884 = self._try_flat(msg, self.pretty_disjunction)
        if flat884 is not None:
            assert flat884 is not None
            self.write(flat884)
            return None
        else:
            def _t1463(_dollar_dollar):
                return _dollar_dollar.args
            _t1464 = _t1463(msg)
            fields880 = _t1464
            assert fields880 is not None
            unwrapped_fields881 = fields880
            self.write("(")
            self.write("or")
            self.indent_sexp()
            if not len(unwrapped_fields881) == 0:
                self.newline()
                for i883, elem882 in enumerate(unwrapped_fields881):
                    if (i883 > 0):
                        self.newline()
                    self.pretty_formula(elem882)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat887 = self._try_flat(msg, self.pretty_not)
        if flat887 is not None:
            assert flat887 is not None
            self.write(flat887)
            return None
        else:
            def _t1465(_dollar_dollar):
                return _dollar_dollar.arg
            _t1466 = _t1465(msg)
            fields885 = _t1466
            assert fields885 is not None
            unwrapped_fields886 = fields885
            self.write("(")
            self.write("not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields886)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat893 = self._try_flat(msg, self.pretty_ffi)
        if flat893 is not None:
            assert flat893 is not None
            self.write(flat893)
            return None
        else:
            def _t1467(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            _t1468 = _t1467(msg)
            fields888 = _t1468
            assert fields888 is not None
            unwrapped_fields889 = fields888
            self.write("(")
            self.write("ffi")
            self.indent_sexp()
            self.newline()
            field890 = unwrapped_fields889[0]
            self.pretty_name(field890)
            self.newline()
            field891 = unwrapped_fields889[1]
            self.pretty_ffi_args(field891)
            self.newline()
            field892 = unwrapped_fields889[2]
            self.pretty_terms(field892)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat895 = self._try_flat(msg, self.pretty_name)
        if flat895 is not None:
            assert flat895 is not None
            self.write(flat895)
            return None
        else:
            fields894 = msg
            self.write(":")
            self.write(fields894)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat899 = self._try_flat(msg, self.pretty_ffi_args)
        if flat899 is not None:
            assert flat899 is not None
            self.write(flat899)
            return None
        else:
            fields896 = msg
            self.write("(")
            self.write("args")
            self.indent_sexp()
            if not len(fields896) == 0:
                self.newline()
                for i898, elem897 in enumerate(fields896):
                    if (i898 > 0):
                        self.newline()
                    self.pretty_abstraction(elem897)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat906 = self._try_flat(msg, self.pretty_atom)
        if flat906 is not None:
            assert flat906 is not None
            self.write(flat906)
            return None
        else:
            def _t1469(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1470 = _t1469(msg)
            fields900 = _t1470
            assert fields900 is not None
            unwrapped_fields901 = fields900
            self.write("(")
            self.write("atom")
            self.indent_sexp()
            self.newline()
            field902 = unwrapped_fields901[0]
            self.pretty_relation_id(field902)
            field903 = unwrapped_fields901[1]
            if not len(field903) == 0:
                self.newline()
                for i905, elem904 in enumerate(field903):
                    if (i905 > 0):
                        self.newline()
                    self.pretty_term(elem904)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat913 = self._try_flat(msg, self.pretty_pragma)
        if flat913 is not None:
            assert flat913 is not None
            self.write(flat913)
            return None
        else:
            def _t1471(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1472 = _t1471(msg)
            fields907 = _t1472
            assert fields907 is not None
            unwrapped_fields908 = fields907
            self.write("(")
            self.write("pragma")
            self.indent_sexp()
            self.newline()
            field909 = unwrapped_fields908[0]
            self.pretty_name(field909)
            field910 = unwrapped_fields908[1]
            if not len(field910) == 0:
                self.newline()
                for i912, elem911 in enumerate(field910):
                    if (i912 > 0):
                        self.newline()
                    self.pretty_term(elem911)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat929 = self._try_flat(msg, self.pretty_primitive)
        if flat929 is not None:
            assert flat929 is not None
            self.write(flat929)
            return None
        else:
            def _t1473(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1474 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1474 = None
                return _t1474
            _t1475 = _t1473(msg)
            guard_result928 = _t1475
            if guard_result928 is not None:
                self.pretty_eq(msg)
            else:
                def _t1476(_dollar_dollar):
                    if _dollar_dollar.name == "rel_primitive_lt_monotype":
                        _t1477 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1477 = None
                    return _t1477
                _t1478 = _t1476(msg)
                guard_result927 = _t1478
                if guard_result927 is not None:
                    self.pretty_lt(msg)
                else:
                    def _t1479(_dollar_dollar):
                        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                            _t1480 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1480 = None
                        return _t1480
                    _t1481 = _t1479(msg)
                    guard_result926 = _t1481
                    if guard_result926 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        def _t1482(_dollar_dollar):
                            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                                _t1483 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1483 = None
                            return _t1483
                        _t1484 = _t1482(msg)
                        guard_result925 = _t1484
                        if guard_result925 is not None:
                            self.pretty_gt(msg)
                        else:
                            def _t1485(_dollar_dollar):
                                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                    _t1486 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                                else:
                                    _t1486 = None
                                return _t1486
                            _t1487 = _t1485(msg)
                            guard_result924 = _t1487
                            if guard_result924 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                def _t1488(_dollar_dollar):
                                    if _dollar_dollar.name == "rel_primitive_add_monotype":
                                        _t1489 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1489 = None
                                    return _t1489
                                _t1490 = _t1488(msg)
                                guard_result923 = _t1490
                                if guard_result923 is not None:
                                    self.pretty_add(msg)
                                else:
                                    def _t1491(_dollar_dollar):
                                        if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                            _t1492 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1492 = None
                                        return _t1492
                                    _t1493 = _t1491(msg)
                                    guard_result922 = _t1493
                                    if guard_result922 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        def _t1494(_dollar_dollar):
                                            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                                _t1495 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1495 = None
                                            return _t1495
                                        _t1496 = _t1494(msg)
                                        guard_result921 = _t1496
                                        if guard_result921 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            def _t1497(_dollar_dollar):
                                                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                    _t1498 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                                else:
                                                    _t1498 = None
                                                return _t1498
                                            _t1499 = _t1497(msg)
                                            guard_result920 = _t1499
                                            if guard_result920 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                def _t1500(_dollar_dollar):
                                                    return (_dollar_dollar.name, _dollar_dollar.terms,)
                                                _t1501 = _t1500(msg)
                                                fields914 = _t1501
                                                assert fields914 is not None
                                                unwrapped_fields915 = fields914
                                                self.write("(")
                                                self.write("primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field916 = unwrapped_fields915[0]
                                                self.pretty_name(field916)
                                                field917 = unwrapped_fields915[1]
                                                if not len(field917) == 0:
                                                    self.newline()
                                                    for i919, elem918 in enumerate(field917):
                                                        if (i919 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem918)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat934 = self._try_flat(msg, self.pretty_eq)
        if flat934 is not None:
            assert flat934 is not None
            self.write(flat934)
            return None
        else:
            def _t1502(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1503 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1503 = None
                return _t1503
            _t1504 = _t1502(msg)
            fields930 = _t1504
            assert fields930 is not None
            unwrapped_fields931 = fields930
            self.write("(")
            self.write("=")
            self.indent_sexp()
            self.newline()
            field932 = unwrapped_fields931[0]
            self.pretty_term(field932)
            self.newline()
            field933 = unwrapped_fields931[1]
            self.pretty_term(field933)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat939 = self._try_flat(msg, self.pretty_lt)
        if flat939 is not None:
            assert flat939 is not None
            self.write(flat939)
            return None
        else:
            def _t1505(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1506 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1506 = None
                return _t1506
            _t1507 = _t1505(msg)
            fields935 = _t1507
            assert fields935 is not None
            unwrapped_fields936 = fields935
            self.write("(")
            self.write("<")
            self.indent_sexp()
            self.newline()
            field937 = unwrapped_fields936[0]
            self.pretty_term(field937)
            self.newline()
            field938 = unwrapped_fields936[1]
            self.pretty_term(field938)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat944 = self._try_flat(msg, self.pretty_lt_eq)
        if flat944 is not None:
            assert flat944 is not None
            self.write(flat944)
            return None
        else:
            def _t1508(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                    _t1509 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1509 = None
                return _t1509
            _t1510 = _t1508(msg)
            fields940 = _t1510
            assert fields940 is not None
            unwrapped_fields941 = fields940
            self.write("(")
            self.write("<=")
            self.indent_sexp()
            self.newline()
            field942 = unwrapped_fields941[0]
            self.pretty_term(field942)
            self.newline()
            field943 = unwrapped_fields941[1]
            self.pretty_term(field943)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat949 = self._try_flat(msg, self.pretty_gt)
        if flat949 is not None:
            assert flat949 is not None
            self.write(flat949)
            return None
        else:
            def _t1511(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_monotype":
                    _t1512 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1512 = None
                return _t1512
            _t1513 = _t1511(msg)
            fields945 = _t1513
            assert fields945 is not None
            unwrapped_fields946 = fields945
            self.write("(")
            self.write(">")
            self.indent_sexp()
            self.newline()
            field947 = unwrapped_fields946[0]
            self.pretty_term(field947)
            self.newline()
            field948 = unwrapped_fields946[1]
            self.pretty_term(field948)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat954 = self._try_flat(msg, self.pretty_gt_eq)
        if flat954 is not None:
            assert flat954 is not None
            self.write(flat954)
            return None
        else:
            def _t1514(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                    _t1515 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1515 = None
                return _t1515
            _t1516 = _t1514(msg)
            fields950 = _t1516
            assert fields950 is not None
            unwrapped_fields951 = fields950
            self.write("(")
            self.write(">=")
            self.indent_sexp()
            self.newline()
            field952 = unwrapped_fields951[0]
            self.pretty_term(field952)
            self.newline()
            field953 = unwrapped_fields951[1]
            self.pretty_term(field953)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat960 = self._try_flat(msg, self.pretty_add)
        if flat960 is not None:
            assert flat960 is not None
            self.write(flat960)
            return None
        else:
            def _t1517(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_add_monotype":
                    _t1518 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1518 = None
                return _t1518
            _t1519 = _t1517(msg)
            fields955 = _t1519
            assert fields955 is not None
            unwrapped_fields956 = fields955
            self.write("(")
            self.write("+")
            self.indent_sexp()
            self.newline()
            field957 = unwrapped_fields956[0]
            self.pretty_term(field957)
            self.newline()
            field958 = unwrapped_fields956[1]
            self.pretty_term(field958)
            self.newline()
            field959 = unwrapped_fields956[2]
            self.pretty_term(field959)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat966 = self._try_flat(msg, self.pretty_minus)
        if flat966 is not None:
            assert flat966 is not None
            self.write(flat966)
            return None
        else:
            def _t1520(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                    _t1521 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1521 = None
                return _t1521
            _t1522 = _t1520(msg)
            fields961 = _t1522
            assert fields961 is not None
            unwrapped_fields962 = fields961
            self.write("(")
            self.write("-")
            self.indent_sexp()
            self.newline()
            field963 = unwrapped_fields962[0]
            self.pretty_term(field963)
            self.newline()
            field964 = unwrapped_fields962[1]
            self.pretty_term(field964)
            self.newline()
            field965 = unwrapped_fields962[2]
            self.pretty_term(field965)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat972 = self._try_flat(msg, self.pretty_multiply)
        if flat972 is not None:
            assert flat972 is not None
            self.write(flat972)
            return None
        else:
            def _t1523(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                    _t1524 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1524 = None
                return _t1524
            _t1525 = _t1523(msg)
            fields967 = _t1525
            assert fields967 is not None
            unwrapped_fields968 = fields967
            self.write("(")
            self.write("*")
            self.indent_sexp()
            self.newline()
            field969 = unwrapped_fields968[0]
            self.pretty_term(field969)
            self.newline()
            field970 = unwrapped_fields968[1]
            self.pretty_term(field970)
            self.newline()
            field971 = unwrapped_fields968[2]
            self.pretty_term(field971)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat978 = self._try_flat(msg, self.pretty_divide)
        if flat978 is not None:
            assert flat978 is not None
            self.write(flat978)
            return None
        else:
            def _t1526(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                    _t1527 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1527 = None
                return _t1527
            _t1528 = _t1526(msg)
            fields973 = _t1528
            assert fields973 is not None
            unwrapped_fields974 = fields973
            self.write("(")
            self.write("/")
            self.indent_sexp()
            self.newline()
            field975 = unwrapped_fields974[0]
            self.pretty_term(field975)
            self.newline()
            field976 = unwrapped_fields974[1]
            self.pretty_term(field976)
            self.newline()
            field977 = unwrapped_fields974[2]
            self.pretty_term(field977)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat983 = self._try_flat(msg, self.pretty_rel_term)
        if flat983 is not None:
            assert flat983 is not None
            self.write(flat983)
            return None
        else:
            def _t1529(_dollar_dollar):
                if _dollar_dollar.HasField("specialized_value"):
                    _t1530 = _dollar_dollar.specialized_value
                else:
                    _t1530 = None
                return _t1530
            _t1531 = _t1529(msg)
            deconstruct_result981 = _t1531
            if deconstruct_result981 is not None:
                assert deconstruct_result981 is not None
                unwrapped982 = deconstruct_result981
                self.pretty_specialized_value(unwrapped982)
            else:
                def _t1532(_dollar_dollar):
                    if _dollar_dollar.HasField("term"):
                        _t1533 = _dollar_dollar.term
                    else:
                        _t1533 = None
                    return _t1533
                _t1534 = _t1532(msg)
                deconstruct_result979 = _t1534
                if deconstruct_result979 is not None:
                    assert deconstruct_result979 is not None
                    unwrapped980 = deconstruct_result979
                    self.pretty_term(unwrapped980)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat985 = self._try_flat(msg, self.pretty_specialized_value)
        if flat985 is not None:
            assert flat985 is not None
            self.write(flat985)
            return None
        else:
            fields984 = msg
            self.write("#")
            self.pretty_value(fields984)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat992 = self._try_flat(msg, self.pretty_rel_atom)
        if flat992 is not None:
            assert flat992 is not None
            self.write(flat992)
            return None
        else:
            def _t1535(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1536 = _t1535(msg)
            fields986 = _t1536
            assert fields986 is not None
            unwrapped_fields987 = fields986
            self.write("(")
            self.write("relatom")
            self.indent_sexp()
            self.newline()
            field988 = unwrapped_fields987[0]
            self.pretty_name(field988)
            field989 = unwrapped_fields987[1]
            if not len(field989) == 0:
                self.newline()
                for i991, elem990 in enumerate(field989):
                    if (i991 > 0):
                        self.newline()
                    self.pretty_rel_term(elem990)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat997 = self._try_flat(msg, self.pretty_cast)
        if flat997 is not None:
            assert flat997 is not None
            self.write(flat997)
            return None
        else:
            def _t1537(_dollar_dollar):
                return (_dollar_dollar.input, _dollar_dollar.result,)
            _t1538 = _t1537(msg)
            fields993 = _t1538
            assert fields993 is not None
            unwrapped_fields994 = fields993
            self.write("(")
            self.write("cast")
            self.indent_sexp()
            self.newline()
            field995 = unwrapped_fields994[0]
            self.pretty_term(field995)
            self.newline()
            field996 = unwrapped_fields994[1]
            self.pretty_term(field996)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1001 = self._try_flat(msg, self.pretty_attrs)
        if flat1001 is not None:
            assert flat1001 is not None
            self.write(flat1001)
            return None
        else:
            fields998 = msg
            self.write("(")
            self.write("attrs")
            self.indent_sexp()
            if not len(fields998) == 0:
                self.newline()
                for i1000, elem999 in enumerate(fields998):
                    if (i1000 > 0):
                        self.newline()
                    self.pretty_attribute(elem999)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1008 = self._try_flat(msg, self.pretty_attribute)
        if flat1008 is not None:
            assert flat1008 is not None
            self.write(flat1008)
            return None
        else:
            def _t1539(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args,)
            _t1540 = _t1539(msg)
            fields1002 = _t1540
            assert fields1002 is not None
            unwrapped_fields1003 = fields1002
            self.write("(")
            self.write("attribute")
            self.indent_sexp()
            self.newline()
            field1004 = unwrapped_fields1003[0]
            self.pretty_name(field1004)
            field1005 = unwrapped_fields1003[1]
            if not len(field1005) == 0:
                self.newline()
                for i1007, elem1006 in enumerate(field1005):
                    if (i1007 > 0):
                        self.newline()
                    self.pretty_value(elem1006)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1015 = self._try_flat(msg, self.pretty_algorithm)
        if flat1015 is not None:
            assert flat1015 is not None
            self.write(flat1015)
            return None
        else:
            def _t1541(_dollar_dollar):
                return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            _t1542 = _t1541(msg)
            fields1009 = _t1542
            assert fields1009 is not None
            unwrapped_fields1010 = fields1009
            self.write("(")
            self.write("algorithm")
            self.indent_sexp()
            field1011 = unwrapped_fields1010[0]
            if not len(field1011) == 0:
                self.newline()
                for i1013, elem1012 in enumerate(field1011):
                    if (i1013 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1012)
            self.newline()
            field1014 = unwrapped_fields1010[1]
            self.pretty_script(field1014)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1020 = self._try_flat(msg, self.pretty_script)
        if flat1020 is not None:
            assert flat1020 is not None
            self.write(flat1020)
            return None
        else:
            def _t1543(_dollar_dollar):
                return _dollar_dollar.constructs
            _t1544 = _t1543(msg)
            fields1016 = _t1544
            assert fields1016 is not None
            unwrapped_fields1017 = fields1016
            self.write("(")
            self.write("script")
            self.indent_sexp()
            if not len(unwrapped_fields1017) == 0:
                self.newline()
                for i1019, elem1018 in enumerate(unwrapped_fields1017):
                    if (i1019 > 0):
                        self.newline()
                    self.pretty_construct(elem1018)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1025 = self._try_flat(msg, self.pretty_construct)
        if flat1025 is not None:
            assert flat1025 is not None
            self.write(flat1025)
            return None
        else:
            def _t1545(_dollar_dollar):
                if _dollar_dollar.HasField("loop"):
                    _t1546 = _dollar_dollar.loop
                else:
                    _t1546 = None
                return _t1546
            _t1547 = _t1545(msg)
            deconstruct_result1023 = _t1547
            if deconstruct_result1023 is not None:
                assert deconstruct_result1023 is not None
                unwrapped1024 = deconstruct_result1023
                self.pretty_loop(unwrapped1024)
            else:
                def _t1548(_dollar_dollar):
                    if _dollar_dollar.HasField("instruction"):
                        _t1549 = _dollar_dollar.instruction
                    else:
                        _t1549 = None
                    return _t1549
                _t1550 = _t1548(msg)
                deconstruct_result1021 = _t1550
                if deconstruct_result1021 is not None:
                    assert deconstruct_result1021 is not None
                    unwrapped1022 = deconstruct_result1021
                    self.pretty_instruction(unwrapped1022)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1030 = self._try_flat(msg, self.pretty_loop)
        if flat1030 is not None:
            assert flat1030 is not None
            self.write(flat1030)
            return None
        else:
            def _t1551(_dollar_dollar):
                return (_dollar_dollar.init, _dollar_dollar.body,)
            _t1552 = _t1551(msg)
            fields1026 = _t1552
            assert fields1026 is not None
            unwrapped_fields1027 = fields1026
            self.write("(")
            self.write("loop")
            self.indent_sexp()
            self.newline()
            field1028 = unwrapped_fields1027[0]
            self.pretty_init(field1028)
            self.newline()
            field1029 = unwrapped_fields1027[1]
            self.pretty_script(field1029)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1034 = self._try_flat(msg, self.pretty_init)
        if flat1034 is not None:
            assert flat1034 is not None
            self.write(flat1034)
            return None
        else:
            fields1031 = msg
            self.write("(")
            self.write("init")
            self.indent_sexp()
            if not len(fields1031) == 0:
                self.newline()
                for i1033, elem1032 in enumerate(fields1031):
                    if (i1033 > 0):
                        self.newline()
                    self.pretty_instruction(elem1032)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1045 = self._try_flat(msg, self.pretty_instruction)
        if flat1045 is not None:
            assert flat1045 is not None
            self.write(flat1045)
            return None
        else:
            def _t1553(_dollar_dollar):
                if _dollar_dollar.HasField("assign"):
                    _t1554 = _dollar_dollar.assign
                else:
                    _t1554 = None
                return _t1554
            _t1555 = _t1553(msg)
            deconstruct_result1043 = _t1555
            if deconstruct_result1043 is not None:
                assert deconstruct_result1043 is not None
                unwrapped1044 = deconstruct_result1043
                self.pretty_assign(unwrapped1044)
            else:
                def _t1556(_dollar_dollar):
                    if _dollar_dollar.HasField("upsert"):
                        _t1557 = _dollar_dollar.upsert
                    else:
                        _t1557 = None
                    return _t1557
                _t1558 = _t1556(msg)
                deconstruct_result1041 = _t1558
                if deconstruct_result1041 is not None:
                    assert deconstruct_result1041 is not None
                    unwrapped1042 = deconstruct_result1041
                    self.pretty_upsert(unwrapped1042)
                else:
                    def _t1559(_dollar_dollar):
                        if _dollar_dollar.HasField("break"):
                            _t1560 = getattr(_dollar_dollar, 'break')
                        else:
                            _t1560 = None
                        return _t1560
                    _t1561 = _t1559(msg)
                    deconstruct_result1039 = _t1561
                    if deconstruct_result1039 is not None:
                        assert deconstruct_result1039 is not None
                        unwrapped1040 = deconstruct_result1039
                        self.pretty_break(unwrapped1040)
                    else:
                        def _t1562(_dollar_dollar):
                            if _dollar_dollar.HasField("monoid_def"):
                                _t1563 = _dollar_dollar.monoid_def
                            else:
                                _t1563 = None
                            return _t1563
                        _t1564 = _t1562(msg)
                        deconstruct_result1037 = _t1564
                        if deconstruct_result1037 is not None:
                            assert deconstruct_result1037 is not None
                            unwrapped1038 = deconstruct_result1037
                            self.pretty_monoid_def(unwrapped1038)
                        else:
                            def _t1565(_dollar_dollar):
                                if _dollar_dollar.HasField("monus_def"):
                                    _t1566 = _dollar_dollar.monus_def
                                else:
                                    _t1566 = None
                                return _t1566
                            _t1567 = _t1565(msg)
                            deconstruct_result1035 = _t1567
                            if deconstruct_result1035 is not None:
                                assert deconstruct_result1035 is not None
                                unwrapped1036 = deconstruct_result1035
                                self.pretty_monus_def(unwrapped1036)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1052 = self._try_flat(msg, self.pretty_assign)
        if flat1052 is not None:
            assert flat1052 is not None
            self.write(flat1052)
            return None
        else:
            def _t1568(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1569 = _dollar_dollar.attrs
                else:
                    _t1569 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1569,)
            _t1570 = _t1568(msg)
            fields1046 = _t1570
            assert fields1046 is not None
            unwrapped_fields1047 = fields1046
            self.write("(")
            self.write("assign")
            self.indent_sexp()
            self.newline()
            field1048 = unwrapped_fields1047[0]
            self.pretty_relation_id(field1048)
            self.newline()
            field1049 = unwrapped_fields1047[1]
            self.pretty_abstraction(field1049)
            field1050 = unwrapped_fields1047[2]
            if field1050 is not None:
                self.newline()
                assert field1050 is not None
                opt_val1051 = field1050
                self.pretty_attrs(opt_val1051)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1059 = self._try_flat(msg, self.pretty_upsert)
        if flat1059 is not None:
            assert flat1059 is not None
            self.write(flat1059)
            return None
        else:
            def _t1571(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1572 = _dollar_dollar.attrs
                else:
                    _t1572 = None
                return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1572,)
            _t1573 = _t1571(msg)
            fields1053 = _t1573
            assert fields1053 is not None
            unwrapped_fields1054 = fields1053
            self.write("(")
            self.write("upsert")
            self.indent_sexp()
            self.newline()
            field1055 = unwrapped_fields1054[0]
            self.pretty_relation_id(field1055)
            self.newline()
            field1056 = unwrapped_fields1054[1]
            self.pretty_abstraction_with_arity(field1056)
            field1057 = unwrapped_fields1054[2]
            if field1057 is not None:
                self.newline()
                assert field1057 is not None
                opt_val1058 = field1057
                self.pretty_attrs(opt_val1058)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1064 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1064 is not None:
            assert flat1064 is not None
            self.write(flat1064)
            return None
        else:
            def _t1574(_dollar_dollar):
                _t1575 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
                return (_t1575, _dollar_dollar[0].value,)
            _t1576 = _t1574(msg)
            fields1060 = _t1576
            assert fields1060 is not None
            unwrapped_fields1061 = fields1060
            self.write("(")
            self.indent()
            field1062 = unwrapped_fields1061[0]
            self.pretty_bindings(field1062)
            self.newline()
            field1063 = unwrapped_fields1061[1]
            self.pretty_formula(field1063)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1071 = self._try_flat(msg, self.pretty_break)
        if flat1071 is not None:
            assert flat1071 is not None
            self.write(flat1071)
            return None
        else:
            def _t1577(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1578 = _dollar_dollar.attrs
                else:
                    _t1578 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1578,)
            _t1579 = _t1577(msg)
            fields1065 = _t1579
            assert fields1065 is not None
            unwrapped_fields1066 = fields1065
            self.write("(")
            self.write("break")
            self.indent_sexp()
            self.newline()
            field1067 = unwrapped_fields1066[0]
            self.pretty_relation_id(field1067)
            self.newline()
            field1068 = unwrapped_fields1066[1]
            self.pretty_abstraction(field1068)
            field1069 = unwrapped_fields1066[2]
            if field1069 is not None:
                self.newline()
                assert field1069 is not None
                opt_val1070 = field1069
                self.pretty_attrs(opt_val1070)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1079 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1079 is not None:
            assert flat1079 is not None
            self.write(flat1079)
            return None
        else:
            def _t1580(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1581 = _dollar_dollar.attrs
                else:
                    _t1581 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1581,)
            _t1582 = _t1580(msg)
            fields1072 = _t1582
            assert fields1072 is not None
            unwrapped_fields1073 = fields1072
            self.write("(")
            self.write("monoid")
            self.indent_sexp()
            self.newline()
            field1074 = unwrapped_fields1073[0]
            self.pretty_monoid(field1074)
            self.newline()
            field1075 = unwrapped_fields1073[1]
            self.pretty_relation_id(field1075)
            self.newline()
            field1076 = unwrapped_fields1073[2]
            self.pretty_abstraction_with_arity(field1076)
            field1077 = unwrapped_fields1073[3]
            if field1077 is not None:
                self.newline()
                assert field1077 is not None
                opt_val1078 = field1077
                self.pretty_attrs(opt_val1078)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1088 = self._try_flat(msg, self.pretty_monoid)
        if flat1088 is not None:
            assert flat1088 is not None
            self.write(flat1088)
            return None
        else:
            def _t1583(_dollar_dollar):
                if _dollar_dollar.HasField("or_monoid"):
                    _t1584 = _dollar_dollar.or_monoid
                else:
                    _t1584 = None
                return _t1584
            _t1585 = _t1583(msg)
            deconstruct_result1086 = _t1585
            if deconstruct_result1086 is not None:
                assert deconstruct_result1086 is not None
                unwrapped1087 = deconstruct_result1086
                self.pretty_or_monoid(unwrapped1087)
            else:
                def _t1586(_dollar_dollar):
                    if _dollar_dollar.HasField("min_monoid"):
                        _t1587 = _dollar_dollar.min_monoid
                    else:
                        _t1587 = None
                    return _t1587
                _t1588 = _t1586(msg)
                deconstruct_result1084 = _t1588
                if deconstruct_result1084 is not None:
                    assert deconstruct_result1084 is not None
                    unwrapped1085 = deconstruct_result1084
                    self.pretty_min_monoid(unwrapped1085)
                else:
                    def _t1589(_dollar_dollar):
                        if _dollar_dollar.HasField("max_monoid"):
                            _t1590 = _dollar_dollar.max_monoid
                        else:
                            _t1590 = None
                        return _t1590
                    _t1591 = _t1589(msg)
                    deconstruct_result1082 = _t1591
                    if deconstruct_result1082 is not None:
                        assert deconstruct_result1082 is not None
                        unwrapped1083 = deconstruct_result1082
                        self.pretty_max_monoid(unwrapped1083)
                    else:
                        def _t1592(_dollar_dollar):
                            if _dollar_dollar.HasField("sum_monoid"):
                                _t1593 = _dollar_dollar.sum_monoid
                            else:
                                _t1593 = None
                            return _t1593
                        _t1594 = _t1592(msg)
                        deconstruct_result1080 = _t1594
                        if deconstruct_result1080 is not None:
                            assert deconstruct_result1080 is not None
                            unwrapped1081 = deconstruct_result1080
                            self.pretty_sum_monoid(unwrapped1081)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1089 = msg
        self.write("(")
        self.write("or")
        self.write(")")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1092 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1092 is not None:
            assert flat1092 is not None
            self.write(flat1092)
            return None
        else:
            def _t1595(_dollar_dollar):
                return _dollar_dollar.type
            _t1596 = _t1595(msg)
            fields1090 = _t1596
            assert fields1090 is not None
            unwrapped_fields1091 = fields1090
            self.write("(")
            self.write("min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1091)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1095 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1095 is not None:
            assert flat1095 is not None
            self.write(flat1095)
            return None
        else:
            def _t1597(_dollar_dollar):
                return _dollar_dollar.type
            _t1598 = _t1597(msg)
            fields1093 = _t1598
            assert fields1093 is not None
            unwrapped_fields1094 = fields1093
            self.write("(")
            self.write("max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1094)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1098 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1098 is not None:
            assert flat1098 is not None
            self.write(flat1098)
            return None
        else:
            def _t1599(_dollar_dollar):
                return _dollar_dollar.type
            _t1600 = _t1599(msg)
            fields1096 = _t1600
            assert fields1096 is not None
            unwrapped_fields1097 = fields1096
            self.write("(")
            self.write("sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1097)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1106 = self._try_flat(msg, self.pretty_monus_def)
        if flat1106 is not None:
            assert flat1106 is not None
            self.write(flat1106)
            return None
        else:
            def _t1601(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1602 = _dollar_dollar.attrs
                else:
                    _t1602 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1602,)
            _t1603 = _t1601(msg)
            fields1099 = _t1603
            assert fields1099 is not None
            unwrapped_fields1100 = fields1099
            self.write("(")
            self.write("monus")
            self.indent_sexp()
            self.newline()
            field1101 = unwrapped_fields1100[0]
            self.pretty_monoid(field1101)
            self.newline()
            field1102 = unwrapped_fields1100[1]
            self.pretty_relation_id(field1102)
            self.newline()
            field1103 = unwrapped_fields1100[2]
            self.pretty_abstraction_with_arity(field1103)
            field1104 = unwrapped_fields1100[3]
            if field1104 is not None:
                self.newline()
                assert field1104 is not None
                opt_val1105 = field1104
                self.pretty_attrs(opt_val1105)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1113 = self._try_flat(msg, self.pretty_constraint)
        if flat1113 is not None:
            assert flat1113 is not None
            self.write(flat1113)
            return None
        else:
            def _t1604(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            _t1605 = _t1604(msg)
            fields1107 = _t1605
            assert fields1107 is not None
            unwrapped_fields1108 = fields1107
            self.write("(")
            self.write("functional_dependency")
            self.indent_sexp()
            self.newline()
            field1109 = unwrapped_fields1108[0]
            self.pretty_relation_id(field1109)
            self.newline()
            field1110 = unwrapped_fields1108[1]
            self.pretty_abstraction(field1110)
            self.newline()
            field1111 = unwrapped_fields1108[2]
            self.pretty_functional_dependency_keys(field1111)
            self.newline()
            field1112 = unwrapped_fields1108[3]
            self.pretty_functional_dependency_values(field1112)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1117 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1117 is not None:
            assert flat1117 is not None
            self.write(flat1117)
            return None
        else:
            fields1114 = msg
            self.write("(")
            self.write("keys")
            self.indent_sexp()
            if not len(fields1114) == 0:
                self.newline()
                for i1116, elem1115 in enumerate(fields1114):
                    if (i1116 > 0):
                        self.newline()
                    self.pretty_var(elem1115)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1121 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1121 is not None:
            assert flat1121 is not None
            self.write(flat1121)
            return None
        else:
            fields1118 = msg
            self.write("(")
            self.write("values")
            self.indent_sexp()
            if not len(fields1118) == 0:
                self.newline()
                for i1120, elem1119 in enumerate(fields1118):
                    if (i1120 > 0):
                        self.newline()
                    self.pretty_var(elem1119)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1128 = self._try_flat(msg, self.pretty_data)
        if flat1128 is not None:
            assert flat1128 is not None
            self.write(flat1128)
            return None
        else:
            def _t1606(_dollar_dollar):
                if _dollar_dollar.HasField("edb"):
                    _t1607 = _dollar_dollar.edb
                else:
                    _t1607 = None
                return _t1607
            _t1608 = _t1606(msg)
            deconstruct_result1126 = _t1608
            if deconstruct_result1126 is not None:
                assert deconstruct_result1126 is not None
                unwrapped1127 = deconstruct_result1126
                self.pretty_edb(unwrapped1127)
            else:
                def _t1609(_dollar_dollar):
                    if _dollar_dollar.HasField("betree_relation"):
                        _t1610 = _dollar_dollar.betree_relation
                    else:
                        _t1610 = None
                    return _t1610
                _t1611 = _t1609(msg)
                deconstruct_result1124 = _t1611
                if deconstruct_result1124 is not None:
                    assert deconstruct_result1124 is not None
                    unwrapped1125 = deconstruct_result1124
                    self.pretty_betree_relation(unwrapped1125)
                else:
                    def _t1612(_dollar_dollar):
                        if _dollar_dollar.HasField("csv_data"):
                            _t1613 = _dollar_dollar.csv_data
                        else:
                            _t1613 = None
                        return _t1613
                    _t1614 = _t1612(msg)
                    deconstruct_result1122 = _t1614
                    if deconstruct_result1122 is not None:
                        assert deconstruct_result1122 is not None
                        unwrapped1123 = deconstruct_result1122
                        self.pretty_csv_data(unwrapped1123)
                    else:
                        raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1134 = self._try_flat(msg, self.pretty_edb)
        if flat1134 is not None:
            assert flat1134 is not None
            self.write(flat1134)
            return None
        else:
            def _t1615(_dollar_dollar):
                return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            _t1616 = _t1615(msg)
            fields1129 = _t1616
            assert fields1129 is not None
            unwrapped_fields1130 = fields1129
            self.write("(")
            self.write("edb")
            self.indent_sexp()
            self.newline()
            field1131 = unwrapped_fields1130[0]
            self.pretty_relation_id(field1131)
            self.newline()
            field1132 = unwrapped_fields1130[1]
            self.pretty_edb_path(field1132)
            self.newline()
            field1133 = unwrapped_fields1130[2]
            self.pretty_edb_types(field1133)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1138 = self._try_flat(msg, self.pretty_edb_path)
        if flat1138 is not None:
            assert flat1138 is not None
            self.write(flat1138)
            return None
        else:
            fields1135 = msg
            self.write("[")
            self.indent()
            for i1137, elem1136 in enumerate(fields1135):
                if (i1137 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1136))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1142 = self._try_flat(msg, self.pretty_edb_types)
        if flat1142 is not None:
            assert flat1142 is not None
            self.write(flat1142)
            return None
        else:
            fields1139 = msg
            self.write("[")
            self.indent()
            for i1141, elem1140 in enumerate(fields1139):
                if (i1141 > 0):
                    self.newline()
                self.pretty_type(elem1140)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1147 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1147 is not None:
            assert flat1147 is not None
            self.write(flat1147)
            return None
        else:
            def _t1617(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_info,)
            _t1618 = _t1617(msg)
            fields1143 = _t1618
            assert fields1143 is not None
            unwrapped_fields1144 = fields1143
            self.write("(")
            self.write("betree_relation")
            self.indent_sexp()
            self.newline()
            field1145 = unwrapped_fields1144[0]
            self.pretty_relation_id(field1145)
            self.newline()
            field1146 = unwrapped_fields1144[1]
            self.pretty_betree_info(field1146)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1153 = self._try_flat(msg, self.pretty_betree_info)
        if flat1153 is not None:
            assert flat1153 is not None
            self.write(flat1153)
            return None
        else:
            def _t1619(_dollar_dollar):
                _t1620 = self.deconstruct_betree_info_config(_dollar_dollar)
                return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1620,)
            _t1621 = _t1619(msg)
            fields1148 = _t1621
            assert fields1148 is not None
            unwrapped_fields1149 = fields1148
            self.write("(")
            self.write("betree_info")
            self.indent_sexp()
            self.newline()
            field1150 = unwrapped_fields1149[0]
            self.pretty_betree_info_key_types(field1150)
            self.newline()
            field1151 = unwrapped_fields1149[1]
            self.pretty_betree_info_value_types(field1151)
            self.newline()
            field1152 = unwrapped_fields1149[2]
            self.pretty_config_dict(field1152)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1157 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1157 is not None:
            assert flat1157 is not None
            self.write(flat1157)
            return None
        else:
            fields1154 = msg
            self.write("(")
            self.write("key_types")
            self.indent_sexp()
            if not len(fields1154) == 0:
                self.newline()
                for i1156, elem1155 in enumerate(fields1154):
                    if (i1156 > 0):
                        self.newline()
                    self.pretty_type(elem1155)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1161 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1161 is not None:
            assert flat1161 is not None
            self.write(flat1161)
            return None
        else:
            fields1158 = msg
            self.write("(")
            self.write("value_types")
            self.indent_sexp()
            if not len(fields1158) == 0:
                self.newline()
                for i1160, elem1159 in enumerate(fields1158):
                    if (i1160 > 0):
                        self.newline()
                    self.pretty_type(elem1159)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1168 = self._try_flat(msg, self.pretty_csv_data)
        if flat1168 is not None:
            assert flat1168 is not None
            self.write(flat1168)
            return None
        else:
            def _t1622(_dollar_dollar):
                return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            _t1623 = _t1622(msg)
            fields1162 = _t1623
            assert fields1162 is not None
            unwrapped_fields1163 = fields1162
            self.write("(")
            self.write("csv_data")
            self.indent_sexp()
            self.newline()
            field1164 = unwrapped_fields1163[0]
            self.pretty_csvlocator(field1164)
            self.newline()
            field1165 = unwrapped_fields1163[1]
            self.pretty_csv_config(field1165)
            self.newline()
            field1166 = unwrapped_fields1163[2]
            self.pretty_gnf_columns(field1166)
            self.newline()
            field1167 = unwrapped_fields1163[3]
            self.pretty_csv_asof(field1167)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1175 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1175 is not None:
            assert flat1175 is not None
            self.write(flat1175)
            return None
        else:
            def _t1624(_dollar_dollar):
                if not len(_dollar_dollar.paths) == 0:
                    _t1625 = _dollar_dollar.paths
                else:
                    _t1625 = None
                if _dollar_dollar.inline_data.decode('utf-8') != "":
                    _t1626 = _dollar_dollar.inline_data.decode('utf-8')
                else:
                    _t1626 = None
                return (_t1625, _t1626,)
            _t1627 = _t1624(msg)
            fields1169 = _t1627
            assert fields1169 is not None
            unwrapped_fields1170 = fields1169
            self.write("(")
            self.write("csv_locator")
            self.indent_sexp()
            field1171 = unwrapped_fields1170[0]
            if field1171 is not None:
                self.newline()
                assert field1171 is not None
                opt_val1172 = field1171
                self.pretty_csv_locator_paths(opt_val1172)
            field1173 = unwrapped_fields1170[1]
            if field1173 is not None:
                self.newline()
                assert field1173 is not None
                opt_val1174 = field1173
                self.pretty_csv_locator_inline_data(opt_val1174)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1179 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1179 is not None:
            assert flat1179 is not None
            self.write(flat1179)
            return None
        else:
            fields1176 = msg
            self.write("(")
            self.write("paths")
            self.indent_sexp()
            if not len(fields1176) == 0:
                self.newline()
                for i1178, elem1177 in enumerate(fields1176):
                    if (i1178 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1177))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1181 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1181 is not None:
            assert flat1181 is not None
            self.write(flat1181)
            return None
        else:
            fields1180 = msg
            self.write("(")
            self.write("inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1180))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1184 = self._try_flat(msg, self.pretty_csv_config)
        if flat1184 is not None:
            assert flat1184 is not None
            self.write(flat1184)
            return None
        else:
            def _t1628(_dollar_dollar):
                _t1629 = self.deconstruct_csv_config(_dollar_dollar)
                return _t1629
            _t1630 = _t1628(msg)
            fields1182 = _t1630
            assert fields1182 is not None
            unwrapped_fields1183 = fields1182
            self.write("(")
            self.write("csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1183)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1188 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1188 is not None:
            assert flat1188 is not None
            self.write(flat1188)
            return None
        else:
            fields1185 = msg
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(fields1185) == 0:
                self.newline()
                for i1187, elem1186 in enumerate(fields1185):
                    if (i1187 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1186)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1197 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1197 is not None:
            assert flat1197 is not None
            self.write(flat1197)
            return None
        else:
            def _t1631(_dollar_dollar):
                if _dollar_dollar.HasField("target_id"):
                    _t1632 = _dollar_dollar.target_id
                else:
                    _t1632 = None
                return (_dollar_dollar.column_path, _t1632, _dollar_dollar.types,)
            _t1633 = _t1631(msg)
            fields1189 = _t1633
            assert fields1189 is not None
            unwrapped_fields1190 = fields1189
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field1191 = unwrapped_fields1190[0]
            self.pretty_gnf_column_path(field1191)
            field1192 = unwrapped_fields1190[1]
            if field1192 is not None:
                self.newline()
                assert field1192 is not None
                opt_val1193 = field1192
                self.pretty_relation_id(opt_val1193)
            self.newline()
            self.write("[")
            field1194 = unwrapped_fields1190[2]
            for i1196, elem1195 in enumerate(field1194):
                if (i1196 > 0):
                    self.newline()
                self.pretty_type(elem1195)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1204 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1204 is not None:
            assert flat1204 is not None
            self.write(flat1204)
            return None
        else:
            def _t1634(_dollar_dollar):
                if len(_dollar_dollar) == 1:
                    _t1635 = _dollar_dollar[0]
                else:
                    _t1635 = None
                return _t1635
            _t1636 = _t1634(msg)
            deconstruct_result1202 = _t1636
            if deconstruct_result1202 is not None:
                assert deconstruct_result1202 is not None
                unwrapped1203 = deconstruct_result1202
                self.write(self.format_string_value(unwrapped1203))
            else:
                def _t1637(_dollar_dollar):
                    if len(_dollar_dollar) != 1:
                        _t1638 = _dollar_dollar
                    else:
                        _t1638 = None
                    return _t1638
                _t1639 = _t1637(msg)
                deconstruct_result1198 = _t1639
                if deconstruct_result1198 is not None:
                    assert deconstruct_result1198 is not None
                    unwrapped1199 = deconstruct_result1198
                    self.write("[")
                    self.indent()
                    for i1201, elem1200 in enumerate(unwrapped1199):
                        if (i1201 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1200))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1206 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1206 is not None:
            assert flat1206 is not None
            self.write(flat1206)
            return None
        else:
            fields1205 = msg
            self.write("(")
            self.write("asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1205))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1209 = self._try_flat(msg, self.pretty_undefine)
        if flat1209 is not None:
            assert flat1209 is not None
            self.write(flat1209)
            return None
        else:
            def _t1640(_dollar_dollar):
                return _dollar_dollar.fragment_id
            _t1641 = _t1640(msg)
            fields1207 = _t1641
            assert fields1207 is not None
            unwrapped_fields1208 = fields1207
            self.write("(")
            self.write("undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1208)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1214 = self._try_flat(msg, self.pretty_context)
        if flat1214 is not None:
            assert flat1214 is not None
            self.write(flat1214)
            return None
        else:
            def _t1642(_dollar_dollar):
                return _dollar_dollar.relations
            _t1643 = _t1642(msg)
            fields1210 = _t1643
            assert fields1210 is not None
            unwrapped_fields1211 = fields1210
            self.write("(")
            self.write("context")
            self.indent_sexp()
            if not len(unwrapped_fields1211) == 0:
                self.newline()
                for i1213, elem1212 in enumerate(unwrapped_fields1211):
                    if (i1213 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1212)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1219 = self._try_flat(msg, self.pretty_snapshot)
        if flat1219 is not None:
            assert flat1219 is not None
            self.write(flat1219)
            return None
        else:
            def _t1644(_dollar_dollar):
                return (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            _t1645 = _t1644(msg)
            fields1215 = _t1645
            assert fields1215 is not None
            unwrapped_fields1216 = fields1215
            self.write("(")
            self.write("snapshot")
            self.indent_sexp()
            self.newline()
            field1217 = unwrapped_fields1216[0]
            self.pretty_edb_path(field1217)
            self.newline()
            field1218 = unwrapped_fields1216[1]
            self.pretty_relation_id(field1218)
            self.dedent()
            self.write(")")

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1223 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1223 is not None:
            assert flat1223 is not None
            self.write(flat1223)
            return None
        else:
            fields1220 = msg
            self.write("(")
            self.write("reads")
            self.indent_sexp()
            if not len(fields1220) == 0:
                self.newline()
                for i1222, elem1221 in enumerate(fields1220):
                    if (i1222 > 0):
                        self.newline()
                    self.pretty_read(elem1221)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1234 = self._try_flat(msg, self.pretty_read)
        if flat1234 is not None:
            assert flat1234 is not None
            self.write(flat1234)
            return None
        else:
            def _t1646(_dollar_dollar):
                if _dollar_dollar.HasField("demand"):
                    _t1647 = _dollar_dollar.demand
                else:
                    _t1647 = None
                return _t1647
            _t1648 = _t1646(msg)
            deconstruct_result1232 = _t1648
            if deconstruct_result1232 is not None:
                assert deconstruct_result1232 is not None
                unwrapped1233 = deconstruct_result1232
                self.pretty_demand(unwrapped1233)
            else:
                def _t1649(_dollar_dollar):
                    if _dollar_dollar.HasField("output"):
                        _t1650 = _dollar_dollar.output
                    else:
                        _t1650 = None
                    return _t1650
                _t1651 = _t1649(msg)
                deconstruct_result1230 = _t1651
                if deconstruct_result1230 is not None:
                    assert deconstruct_result1230 is not None
                    unwrapped1231 = deconstruct_result1230
                    self.pretty_output(unwrapped1231)
                else:
                    def _t1652(_dollar_dollar):
                        if _dollar_dollar.HasField("what_if"):
                            _t1653 = _dollar_dollar.what_if
                        else:
                            _t1653 = None
                        return _t1653
                    _t1654 = _t1652(msg)
                    deconstruct_result1228 = _t1654
                    if deconstruct_result1228 is not None:
                        assert deconstruct_result1228 is not None
                        unwrapped1229 = deconstruct_result1228
                        self.pretty_what_if(unwrapped1229)
                    else:
                        def _t1655(_dollar_dollar):
                            if _dollar_dollar.HasField("abort"):
                                _t1656 = _dollar_dollar.abort
                            else:
                                _t1656 = None
                            return _t1656
                        _t1657 = _t1655(msg)
                        deconstruct_result1226 = _t1657
                        if deconstruct_result1226 is not None:
                            assert deconstruct_result1226 is not None
                            unwrapped1227 = deconstruct_result1226
                            self.pretty_abort(unwrapped1227)
                        else:
                            def _t1658(_dollar_dollar):
                                if _dollar_dollar.HasField("export"):
                                    _t1659 = _dollar_dollar.export
                                else:
                                    _t1659 = None
                                return _t1659
                            _t1660 = _t1658(msg)
                            deconstruct_result1224 = _t1660
                            if deconstruct_result1224 is not None:
                                assert deconstruct_result1224 is not None
                                unwrapped1225 = deconstruct_result1224
                                self.pretty_export(unwrapped1225)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1237 = self._try_flat(msg, self.pretty_demand)
        if flat1237 is not None:
            assert flat1237 is not None
            self.write(flat1237)
            return None
        else:
            def _t1661(_dollar_dollar):
                return _dollar_dollar.relation_id
            _t1662 = _t1661(msg)
            fields1235 = _t1662
            assert fields1235 is not None
            unwrapped_fields1236 = fields1235
            self.write("(")
            self.write("demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1236)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1242 = self._try_flat(msg, self.pretty_output)
        if flat1242 is not None:
            assert flat1242 is not None
            self.write(flat1242)
            return None
        else:
            def _t1663(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_id,)
            _t1664 = _t1663(msg)
            fields1238 = _t1664
            assert fields1238 is not None
            unwrapped_fields1239 = fields1238
            self.write("(")
            self.write("output")
            self.indent_sexp()
            self.newline()
            field1240 = unwrapped_fields1239[0]
            self.pretty_name(field1240)
            self.newline()
            field1241 = unwrapped_fields1239[1]
            self.pretty_relation_id(field1241)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1247 = self._try_flat(msg, self.pretty_what_if)
        if flat1247 is not None:
            assert flat1247 is not None
            self.write(flat1247)
            return None
        else:
            def _t1665(_dollar_dollar):
                return (_dollar_dollar.branch, _dollar_dollar.epoch,)
            _t1666 = _t1665(msg)
            fields1243 = _t1666
            assert fields1243 is not None
            unwrapped_fields1244 = fields1243
            self.write("(")
            self.write("what_if")
            self.indent_sexp()
            self.newline()
            field1245 = unwrapped_fields1244[0]
            self.pretty_name(field1245)
            self.newline()
            field1246 = unwrapped_fields1244[1]
            self.pretty_epoch(field1246)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1253 = self._try_flat(msg, self.pretty_abort)
        if flat1253 is not None:
            assert flat1253 is not None
            self.write(flat1253)
            return None
        else:
            def _t1667(_dollar_dollar):
                if _dollar_dollar.name != "abort":
                    _t1668 = _dollar_dollar.name
                else:
                    _t1668 = None
                return (_t1668, _dollar_dollar.relation_id,)
            _t1669 = _t1667(msg)
            fields1248 = _t1669
            assert fields1248 is not None
            unwrapped_fields1249 = fields1248
            self.write("(")
            self.write("abort")
            self.indent_sexp()
            field1250 = unwrapped_fields1249[0]
            if field1250 is not None:
                self.newline()
                assert field1250 is not None
                opt_val1251 = field1250
                self.pretty_name(opt_val1251)
            self.newline()
            field1252 = unwrapped_fields1249[1]
            self.pretty_relation_id(field1252)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1256 = self._try_flat(msg, self.pretty_export)
        if flat1256 is not None:
            assert flat1256 is not None
            self.write(flat1256)
            return None
        else:
            def _t1670(_dollar_dollar):
                return _dollar_dollar.csv_config
            _t1671 = _t1670(msg)
            fields1254 = _t1671
            assert fields1254 is not None
            unwrapped_fields1255 = fields1254
            self.write("(")
            self.write("export")
            self.indent_sexp()
            self.newline()
            self.pretty_export_csv_config(unwrapped_fields1255)
            self.dedent()
            self.write(")")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1262 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1262 is not None:
            assert flat1262 is not None
            self.write(flat1262)
            return None
        else:
            def _t1672(_dollar_dollar):
                _t1673 = self.deconstruct_export_csv_config(_dollar_dollar)
                return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1673,)
            _t1674 = _t1672(msg)
            fields1257 = _t1674
            assert fields1257 is not None
            unwrapped_fields1258 = fields1257
            self.write("(")
            self.write("export_csv_config")
            self.indent_sexp()
            self.newline()
            field1259 = unwrapped_fields1258[0]
            self.pretty_export_csv_path(field1259)
            self.newline()
            field1260 = unwrapped_fields1258[1]
            self.pretty_export_csv_columns(field1260)
            self.newline()
            field1261 = unwrapped_fields1258[2]
            self.pretty_config_dict(field1261)
            self.dedent()
            self.write(")")

    def pretty_export_csv_path(self, msg: str):
        flat1264 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1264 is not None:
            assert flat1264 is not None
            self.write(flat1264)
            return None
        else:
            fields1263 = msg
            self.write("(")
            self.write("path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1263))
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1268 = self._try_flat(msg, self.pretty_export_csv_columns)
        if flat1268 is not None:
            assert flat1268 is not None
            self.write(flat1268)
            return None
        else:
            fields1265 = msg
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(fields1265) == 0:
                self.newline()
                for i1267, elem1266 in enumerate(fields1265):
                    if (i1267 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1266)
            self.dedent()
            self.write(")")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1273 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1273 is not None:
            assert flat1273 is not None
            self.write(flat1273)
            return None
        else:
            def _t1675(_dollar_dollar):
                return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            _t1676 = _t1675(msg)
            fields1269 = _t1676
            assert fields1269 is not None
            unwrapped_fields1270 = fields1269
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field1271 = unwrapped_fields1270[0]
            self.write(self.format_string_value(field1271))
            self.newline()
            field1272 = unwrapped_fields1270[1]
            self.pretty_relation_id(field1272)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1714 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1714)
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
        self.write(":keys ")
        self.write("(")
        for _idx, _elem in enumerate(msg.keys):
            if (_idx > 0):
                self.write(" ")
            self.pprint_dispatch(_elem)
        self.write(")")
        self.newline()
        self.write(":values ")
        self.write("(")
        for _idx, _elem in enumerate(msg.values):
            if (_idx > 0):
                self.write(" ")
            self.pprint_dispatch(_elem)
        self.write(")")
        self.write(")")
        self.dedent()

    def pretty_int128_value(self, msg: logic_pb2.Int128Value):
        self.write(self.format_int128(msg))

    def pretty_missing_value(self, msg: logic_pb2.MissingValue):
        self.write("missing")

    def pretty_u_int128_value(self, msg: logic_pb2.UInt128Value):
        self.write(self.format_uint128(msg))

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
