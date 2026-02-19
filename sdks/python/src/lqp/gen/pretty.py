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
        return f"0x{value:032x}"

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
        _t1653 = logic_pb2.Value(int_value=int(v))
        return _t1653

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1654 = logic_pb2.Value(int_value=v)
        return _t1654

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1655 = logic_pb2.Value(float_value=v)
        return _t1655

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1656 = logic_pb2.Value(string_value=v)
        return _t1656

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1657 = logic_pb2.Value(boolean_value=v)
        return _t1657

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1658 = logic_pb2.Value(uint128_value=v)
        return _t1658

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1659 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1659,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1660 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1660,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1661 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1661,))
        _t1662 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1662,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1663 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1663,))
        _t1664 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1664,))
        if msg.new_line != "":
            _t1665 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1665,))
        _t1666 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1666,))
        _t1667 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1667,))
        _t1668 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1668,))
        if msg.comment != "":
            _t1669 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1669,))
        for missing_string in msg.missing_strings:
            _t1670 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1670,))
        _t1671 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1671,))
        _t1672 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1672,))
        _t1673 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1673,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1674 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1674,))
        _t1675 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1675,))
        _t1676 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1676,))
        _t1677 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1677,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1678 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1678,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1679 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1679,))
        _t1680 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1680,))
        _t1681 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1681,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1682 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1682,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1683 = self._make_value_string(msg.compression)
            result.append(("compression", _t1683,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1684 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1684,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1685 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1685,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1686 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1686,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1687 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1687,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1688 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1688,))
        return sorted(result)

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> Optional[str]:
        name = self.relation_id_to_string(msg)
        if name is not None:
            assert name is not None
            return name
        else:
            _t1689 = None
        return None

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name is None:
            return self.relation_id_to_uint128(msg)
        else:
            _t1690 = None
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
        flat638 = self._try_flat(msg, self.pretty_transaction)
        if flat638 is not None:
            assert flat638 is not None
            self.write(flat638)
            return None
        else:
            def _t1258(_dollar_dollar):
                if _dollar_dollar.HasField("configure"):
                    _t1259 = _dollar_dollar.configure
                else:
                    _t1259 = None
                if _dollar_dollar.HasField("sync"):
                    _t1260 = _dollar_dollar.sync
                else:
                    _t1260 = None
                return (_t1259, _t1260, _dollar_dollar.epochs,)
            _t1261 = _t1258(msg)
            fields629 = _t1261
            assert fields629 is not None
            unwrapped_fields630 = fields629
            self.write("(")
            self.write("transaction")
            self.indent_sexp()
            field631 = unwrapped_fields630[0]
            if field631 is not None:
                self.newline()
                assert field631 is not None
                opt_val632 = field631
                self.pretty_configure(opt_val632)
            field633 = unwrapped_fields630[1]
            if field633 is not None:
                self.newline()
                assert field633 is not None
                opt_val634 = field633
                self.pretty_sync(opt_val634)
            field635 = unwrapped_fields630[2]
            if not len(field635) == 0:
                self.newline()
                for i637, elem636 in enumerate(field635):
                    if (i637 > 0):
                        self.newline()
                    self.pretty_epoch(elem636)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat641 = self._try_flat(msg, self.pretty_configure)
        if flat641 is not None:
            assert flat641 is not None
            self.write(flat641)
            return None
        else:
            def _t1262(_dollar_dollar):
                _t1263 = self.deconstruct_configure(_dollar_dollar)
                return _t1263
            _t1264 = _t1262(msg)
            fields639 = _t1264
            assert fields639 is not None
            unwrapped_fields640 = fields639
            self.write("(")
            self.write("configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields640)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat645 = self._try_flat(msg, self.pretty_config_dict)
        if flat645 is not None:
            assert flat645 is not None
            self.write(flat645)
            return None
        else:
            fields642 = msg
            self.write("{")
            self.indent()
            if not len(fields642) == 0:
                self.newline()
                for i644, elem643 in enumerate(fields642):
                    if (i644 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem643)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat650 = self._try_flat(msg, self.pretty_config_key_value)
        if flat650 is not None:
            assert flat650 is not None
            self.write(flat650)
            return None
        else:
            def _t1265(_dollar_dollar):
                return (_dollar_dollar[0], _dollar_dollar[1],)
            _t1266 = _t1265(msg)
            fields646 = _t1266
            assert fields646 is not None
            unwrapped_fields647 = fields646
            self.write(":")
            field648 = unwrapped_fields647[0]
            self.write(field648)
            self.write(" ")
            field649 = unwrapped_fields647[1]
            self.pretty_value(field649)

    def pretty_value(self, msg: logic_pb2.Value):
        flat670 = self._try_flat(msg, self.pretty_value)
        if flat670 is not None:
            assert flat670 is not None
            self.write(flat670)
            return None
        else:
            def _t1267(_dollar_dollar):
                if _dollar_dollar.HasField("date_value"):
                    _t1268 = _dollar_dollar.date_value
                else:
                    _t1268 = None
                return _t1268
            _t1269 = _t1267(msg)
            deconstruct_result668 = _t1269
            if deconstruct_result668 is not None:
                assert deconstruct_result668 is not None
                unwrapped669 = deconstruct_result668
                self.pretty_date(unwrapped669)
            else:
                def _t1270(_dollar_dollar):
                    if _dollar_dollar.HasField("datetime_value"):
                        _t1271 = _dollar_dollar.datetime_value
                    else:
                        _t1271 = None
                    return _t1271
                _t1272 = _t1270(msg)
                deconstruct_result666 = _t1272
                if deconstruct_result666 is not None:
                    assert deconstruct_result666 is not None
                    unwrapped667 = deconstruct_result666
                    self.pretty_datetime(unwrapped667)
                else:
                    def _t1273(_dollar_dollar):
                        if _dollar_dollar.HasField("string_value"):
                            _t1274 = _dollar_dollar.string_value
                        else:
                            _t1274 = None
                        return _t1274
                    _t1275 = _t1273(msg)
                    deconstruct_result664 = _t1275
                    if deconstruct_result664 is not None:
                        assert deconstruct_result664 is not None
                        unwrapped665 = deconstruct_result664
                        self.write(self.format_string_value(unwrapped665))
                    else:
                        def _t1276(_dollar_dollar):
                            if _dollar_dollar.HasField("int_value"):
                                _t1277 = _dollar_dollar.int_value
                            else:
                                _t1277 = None
                            return _t1277
                        _t1278 = _t1276(msg)
                        deconstruct_result662 = _t1278
                        if deconstruct_result662 is not None:
                            assert deconstruct_result662 is not None
                            unwrapped663 = deconstruct_result662
                            self.write(str(unwrapped663))
                        else:
                            def _t1279(_dollar_dollar):
                                if _dollar_dollar.HasField("float_value"):
                                    _t1280 = _dollar_dollar.float_value
                                else:
                                    _t1280 = None
                                return _t1280
                            _t1281 = _t1279(msg)
                            deconstruct_result660 = _t1281
                            if deconstruct_result660 is not None:
                                assert deconstruct_result660 is not None
                                unwrapped661 = deconstruct_result660
                                self.write(str(unwrapped661))
                            else:
                                def _t1282(_dollar_dollar):
                                    if _dollar_dollar.HasField("uint128_value"):
                                        _t1283 = _dollar_dollar.uint128_value
                                    else:
                                        _t1283 = None
                                    return _t1283
                                _t1284 = _t1282(msg)
                                deconstruct_result658 = _t1284
                                if deconstruct_result658 is not None:
                                    assert deconstruct_result658 is not None
                                    unwrapped659 = deconstruct_result658
                                    self.write(self.format_uint128(unwrapped659))
                                else:
                                    def _t1285(_dollar_dollar):
                                        if _dollar_dollar.HasField("int128_value"):
                                            _t1286 = _dollar_dollar.int128_value
                                        else:
                                            _t1286 = None
                                        return _t1286
                                    _t1287 = _t1285(msg)
                                    deconstruct_result656 = _t1287
                                    if deconstruct_result656 is not None:
                                        assert deconstruct_result656 is not None
                                        unwrapped657 = deconstruct_result656
                                        self.write(self.format_int128(unwrapped657))
                                    else:
                                        def _t1288(_dollar_dollar):
                                            if _dollar_dollar.HasField("decimal_value"):
                                                _t1289 = _dollar_dollar.decimal_value
                                            else:
                                                _t1289 = None
                                            return _t1289
                                        _t1290 = _t1288(msg)
                                        deconstruct_result654 = _t1290
                                        if deconstruct_result654 is not None:
                                            assert deconstruct_result654 is not None
                                            unwrapped655 = deconstruct_result654
                                            self.write(self.format_decimal(unwrapped655))
                                        else:
                                            def _t1291(_dollar_dollar):
                                                if _dollar_dollar.HasField("boolean_value"):
                                                    _t1292 = _dollar_dollar.boolean_value
                                                else:
                                                    _t1292 = None
                                                return _t1292
                                            _t1293 = _t1291(msg)
                                            deconstruct_result652 = _t1293
                                            if deconstruct_result652 is not None:
                                                assert deconstruct_result652 is not None
                                                unwrapped653 = deconstruct_result652
                                                self.pretty_boolean_value(unwrapped653)
                                            else:
                                                fields651 = msg
                                                self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat676 = self._try_flat(msg, self.pretty_date)
        if flat676 is not None:
            assert flat676 is not None
            self.write(flat676)
            return None
        else:
            def _t1294(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            _t1295 = _t1294(msg)
            fields671 = _t1295
            assert fields671 is not None
            unwrapped_fields672 = fields671
            self.write("(")
            self.write("date")
            self.indent_sexp()
            self.newline()
            field673 = unwrapped_fields672[0]
            self.write(str(field673))
            self.newline()
            field674 = unwrapped_fields672[1]
            self.write(str(field674))
            self.newline()
            field675 = unwrapped_fields672[2]
            self.write(str(field675))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat687 = self._try_flat(msg, self.pretty_datetime)
        if flat687 is not None:
            assert flat687 is not None
            self.write(flat687)
            return None
        else:
            def _t1296(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            _t1297 = _t1296(msg)
            fields677 = _t1297
            assert fields677 is not None
            unwrapped_fields678 = fields677
            self.write("(")
            self.write("datetime")
            self.indent_sexp()
            self.newline()
            field679 = unwrapped_fields678[0]
            self.write(str(field679))
            self.newline()
            field680 = unwrapped_fields678[1]
            self.write(str(field680))
            self.newline()
            field681 = unwrapped_fields678[2]
            self.write(str(field681))
            self.newline()
            field682 = unwrapped_fields678[3]
            self.write(str(field682))
            self.newline()
            field683 = unwrapped_fields678[4]
            self.write(str(field683))
            self.newline()
            field684 = unwrapped_fields678[5]
            self.write(str(field684))
            field685 = unwrapped_fields678[6]
            if field685 is not None:
                self.newline()
                assert field685 is not None
                opt_val686 = field685
                self.write(str(opt_val686))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        def _t1298(_dollar_dollar):
            if _dollar_dollar:
                _t1299 = ()
            else:
                _t1299 = None
            return _t1299
        _t1300 = _t1298(msg)
        deconstruct_result690 = _t1300
        if deconstruct_result690 is not None:
            assert deconstruct_result690 is not None
            unwrapped691 = deconstruct_result690
            self.write("true")
        else:
            def _t1301(_dollar_dollar):
                if not _dollar_dollar:
                    _t1302 = ()
                else:
                    _t1302 = None
                return _t1302
            _t1303 = _t1301(msg)
            deconstruct_result688 = _t1303
            if deconstruct_result688 is not None:
                assert deconstruct_result688 is not None
                unwrapped689 = deconstruct_result688
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat696 = self._try_flat(msg, self.pretty_sync)
        if flat696 is not None:
            assert flat696 is not None
            self.write(flat696)
            return None
        else:
            def _t1304(_dollar_dollar):
                return _dollar_dollar.fragments
            _t1305 = _t1304(msg)
            fields692 = _t1305
            assert fields692 is not None
            unwrapped_fields693 = fields692
            self.write("(")
            self.write("sync")
            self.indent_sexp()
            if not len(unwrapped_fields693) == 0:
                self.newline()
                for i695, elem694 in enumerate(unwrapped_fields693):
                    if (i695 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem694)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat699 = self._try_flat(msg, self.pretty_fragment_id)
        if flat699 is not None:
            assert flat699 is not None
            self.write(flat699)
            return None
        else:
            def _t1306(_dollar_dollar):
                return self.fragment_id_to_string(_dollar_dollar)
            _t1307 = _t1306(msg)
            fields697 = _t1307
            assert fields697 is not None
            unwrapped_fields698 = fields697
            self.write(":")
            self.write(unwrapped_fields698)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat706 = self._try_flat(msg, self.pretty_epoch)
        if flat706 is not None:
            assert flat706 is not None
            self.write(flat706)
            return None
        else:
            def _t1308(_dollar_dollar):
                if not len(_dollar_dollar.writes) == 0:
                    _t1309 = _dollar_dollar.writes
                else:
                    _t1309 = None
                if not len(_dollar_dollar.reads) == 0:
                    _t1310 = _dollar_dollar.reads
                else:
                    _t1310 = None
                return (_t1309, _t1310,)
            _t1311 = _t1308(msg)
            fields700 = _t1311
            assert fields700 is not None
            unwrapped_fields701 = fields700
            self.write("(")
            self.write("epoch")
            self.indent_sexp()
            field702 = unwrapped_fields701[0]
            if field702 is not None:
                self.newline()
                assert field702 is not None
                opt_val703 = field702
                self.pretty_epoch_writes(opt_val703)
            field704 = unwrapped_fields701[1]
            if field704 is not None:
                self.newline()
                assert field704 is not None
                opt_val705 = field704
                self.pretty_epoch_reads(opt_val705)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat710 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat710 is not None:
            assert flat710 is not None
            self.write(flat710)
            return None
        else:
            fields707 = msg
            self.write("(")
            self.write("writes")
            self.indent_sexp()
            if not len(fields707) == 0:
                self.newline()
                for i709, elem708 in enumerate(fields707):
                    if (i709 > 0):
                        self.newline()
                    self.pretty_write(elem708)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat719 = self._try_flat(msg, self.pretty_write)
        if flat719 is not None:
            assert flat719 is not None
            self.write(flat719)
            return None
        else:
            def _t1312(_dollar_dollar):
                if _dollar_dollar.HasField("define"):
                    _t1313 = _dollar_dollar.define
                else:
                    _t1313 = None
                return _t1313
            _t1314 = _t1312(msg)
            deconstruct_result717 = _t1314
            if deconstruct_result717 is not None:
                assert deconstruct_result717 is not None
                unwrapped718 = deconstruct_result717
                self.pretty_define(unwrapped718)
            else:
                def _t1315(_dollar_dollar):
                    if _dollar_dollar.HasField("undefine"):
                        _t1316 = _dollar_dollar.undefine
                    else:
                        _t1316 = None
                    return _t1316
                _t1317 = _t1315(msg)
                deconstruct_result715 = _t1317
                if deconstruct_result715 is not None:
                    assert deconstruct_result715 is not None
                    unwrapped716 = deconstruct_result715
                    self.pretty_undefine(unwrapped716)
                else:
                    def _t1318(_dollar_dollar):
                        if _dollar_dollar.HasField("context"):
                            _t1319 = _dollar_dollar.context
                        else:
                            _t1319 = None
                        return _t1319
                    _t1320 = _t1318(msg)
                    deconstruct_result713 = _t1320
                    if deconstruct_result713 is not None:
                        assert deconstruct_result713 is not None
                        unwrapped714 = deconstruct_result713
                        self.pretty_context(unwrapped714)
                    else:
                        def _t1321(_dollar_dollar):
                            if _dollar_dollar.HasField("snapshot"):
                                _t1322 = _dollar_dollar.snapshot
                            else:
                                _t1322 = None
                            return _t1322
                        _t1323 = _t1321(msg)
                        deconstruct_result711 = _t1323
                        if deconstruct_result711 is not None:
                            assert deconstruct_result711 is not None
                            unwrapped712 = deconstruct_result711
                            self.pretty_snapshot(unwrapped712)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat722 = self._try_flat(msg, self.pretty_define)
        if flat722 is not None:
            assert flat722 is not None
            self.write(flat722)
            return None
        else:
            def _t1324(_dollar_dollar):
                return _dollar_dollar.fragment
            _t1325 = _t1324(msg)
            fields720 = _t1325
            assert fields720 is not None
            unwrapped_fields721 = fields720
            self.write("(")
            self.write("define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields721)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat729 = self._try_flat(msg, self.pretty_fragment)
        if flat729 is not None:
            assert flat729 is not None
            self.write(flat729)
            return None
        else:
            def _t1326(_dollar_dollar):
                self.start_pretty_fragment(_dollar_dollar)
                return (_dollar_dollar.id, _dollar_dollar.declarations,)
            _t1327 = _t1326(msg)
            fields723 = _t1327
            assert fields723 is not None
            unwrapped_fields724 = fields723
            self.write("(")
            self.write("fragment")
            self.indent_sexp()
            self.newline()
            field725 = unwrapped_fields724[0]
            self.pretty_new_fragment_id(field725)
            field726 = unwrapped_fields724[1]
            if not len(field726) == 0:
                self.newline()
                for i728, elem727 in enumerate(field726):
                    if (i728 > 0):
                        self.newline()
                    self.pretty_declaration(elem727)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat731 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat731 is not None:
            assert flat731 is not None
            self.write(flat731)
            return None
        else:
            fields730 = msg
            self.pretty_fragment_id(fields730)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat740 = self._try_flat(msg, self.pretty_declaration)
        if flat740 is not None:
            assert flat740 is not None
            self.write(flat740)
            return None
        else:
            def _t1328(_dollar_dollar):
                if _dollar_dollar.HasField("def"):
                    _t1329 = getattr(_dollar_dollar, 'def')
                else:
                    _t1329 = None
                return _t1329
            _t1330 = _t1328(msg)
            deconstruct_result738 = _t1330
            if deconstruct_result738 is not None:
                assert deconstruct_result738 is not None
                unwrapped739 = deconstruct_result738
                self.pretty_def(unwrapped739)
            else:
                def _t1331(_dollar_dollar):
                    if _dollar_dollar.HasField("algorithm"):
                        _t1332 = _dollar_dollar.algorithm
                    else:
                        _t1332 = None
                    return _t1332
                _t1333 = _t1331(msg)
                deconstruct_result736 = _t1333
                if deconstruct_result736 is not None:
                    assert deconstruct_result736 is not None
                    unwrapped737 = deconstruct_result736
                    self.pretty_algorithm(unwrapped737)
                else:
                    def _t1334(_dollar_dollar):
                        if _dollar_dollar.HasField("constraint"):
                            _t1335 = _dollar_dollar.constraint
                        else:
                            _t1335 = None
                        return _t1335
                    _t1336 = _t1334(msg)
                    deconstruct_result734 = _t1336
                    if deconstruct_result734 is not None:
                        assert deconstruct_result734 is not None
                        unwrapped735 = deconstruct_result734
                        self.pretty_constraint(unwrapped735)
                    else:
                        def _t1337(_dollar_dollar):
                            if _dollar_dollar.HasField("data"):
                                _t1338 = _dollar_dollar.data
                            else:
                                _t1338 = None
                            return _t1338
                        _t1339 = _t1337(msg)
                        deconstruct_result732 = _t1339
                        if deconstruct_result732 is not None:
                            assert deconstruct_result732 is not None
                            unwrapped733 = deconstruct_result732
                            self.pretty_data(unwrapped733)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat747 = self._try_flat(msg, self.pretty_def)
        if flat747 is not None:
            assert flat747 is not None
            self.write(flat747)
            return None
        else:
            def _t1340(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1341 = _dollar_dollar.attrs
                else:
                    _t1341 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1341,)
            _t1342 = _t1340(msg)
            fields741 = _t1342
            assert fields741 is not None
            unwrapped_fields742 = fields741
            self.write("(")
            self.write("def")
            self.indent_sexp()
            self.newline()
            field743 = unwrapped_fields742[0]
            self.pretty_relation_id(field743)
            self.newline()
            field744 = unwrapped_fields742[1]
            self.pretty_abstraction(field744)
            field745 = unwrapped_fields742[2]
            if field745 is not None:
                self.newline()
                assert field745 is not None
                opt_val746 = field745
                self.pretty_attrs(opt_val746)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat752 = self._try_flat(msg, self.pretty_relation_id)
        if flat752 is not None:
            assert flat752 is not None
            self.write(flat752)
            return None
        else:
            def _t1343(_dollar_dollar):
                _t1344 = self.deconstruct_relation_id_string(_dollar_dollar)
                return _t1344
            _t1345 = _t1343(msg)
            deconstruct_result750 = _t1345
            if deconstruct_result750 is not None:
                assert deconstruct_result750 is not None
                unwrapped751 = deconstruct_result750
                self.write(":")
                self.write(unwrapped751)
            else:
                def _t1346(_dollar_dollar):
                    _t1347 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                    return _t1347
                _t1348 = _t1346(msg)
                deconstruct_result748 = _t1348
                if deconstruct_result748 is not None:
                    assert deconstruct_result748 is not None
                    unwrapped749 = deconstruct_result748
                    self.write(self.format_uint128(unwrapped749))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat757 = self._try_flat(msg, self.pretty_abstraction)
        if flat757 is not None:
            assert flat757 is not None
            self.write(flat757)
            return None
        else:
            def _t1349(_dollar_dollar):
                _t1350 = self.deconstruct_bindings(_dollar_dollar)
                return (_t1350, _dollar_dollar.value,)
            _t1351 = _t1349(msg)
            fields753 = _t1351
            assert fields753 is not None
            unwrapped_fields754 = fields753
            self.write("(")
            self.indent()
            field755 = unwrapped_fields754[0]
            self.pretty_bindings(field755)
            self.newline()
            field756 = unwrapped_fields754[1]
            self.pretty_formula(field756)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat765 = self._try_flat(msg, self.pretty_bindings)
        if flat765 is not None:
            assert flat765 is not None
            self.write(flat765)
            return None
        else:
            def _t1352(_dollar_dollar):
                if not len(_dollar_dollar[1]) == 0:
                    _t1353 = _dollar_dollar[1]
                else:
                    _t1353 = None
                return (_dollar_dollar[0], _t1353,)
            _t1354 = _t1352(msg)
            fields758 = _t1354
            assert fields758 is not None
            unwrapped_fields759 = fields758
            self.write("[")
            self.indent()
            field760 = unwrapped_fields759[0]
            for i762, elem761 in enumerate(field760):
                if (i762 > 0):
                    self.newline()
                self.pretty_binding(elem761)
            field763 = unwrapped_fields759[1]
            if field763 is not None:
                self.newline()
                assert field763 is not None
                opt_val764 = field763
                self.pretty_value_bindings(opt_val764)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat770 = self._try_flat(msg, self.pretty_binding)
        if flat770 is not None:
            assert flat770 is not None
            self.write(flat770)
            return None
        else:
            def _t1355(_dollar_dollar):
                return (_dollar_dollar.var.name, _dollar_dollar.type,)
            _t1356 = _t1355(msg)
            fields766 = _t1356
            assert fields766 is not None
            unwrapped_fields767 = fields766
            field768 = unwrapped_fields767[0]
            self.write(field768)
            self.write("::")
            field769 = unwrapped_fields767[1]
            self.pretty_type(field769)

    def pretty_type(self, msg: logic_pb2.Type):
        flat793 = self._try_flat(msg, self.pretty_type)
        if flat793 is not None:
            assert flat793 is not None
            self.write(flat793)
            return None
        else:
            def _t1357(_dollar_dollar):
                if _dollar_dollar.HasField("unspecified_type"):
                    _t1358 = _dollar_dollar.unspecified_type
                else:
                    _t1358 = None
                return _t1358
            _t1359 = _t1357(msg)
            deconstruct_result791 = _t1359
            if deconstruct_result791 is not None:
                assert deconstruct_result791 is not None
                unwrapped792 = deconstruct_result791
                self.pretty_unspecified_type(unwrapped792)
            else:
                def _t1360(_dollar_dollar):
                    if _dollar_dollar.HasField("string_type"):
                        _t1361 = _dollar_dollar.string_type
                    else:
                        _t1361 = None
                    return _t1361
                _t1362 = _t1360(msg)
                deconstruct_result789 = _t1362
                if deconstruct_result789 is not None:
                    assert deconstruct_result789 is not None
                    unwrapped790 = deconstruct_result789
                    self.pretty_string_type(unwrapped790)
                else:
                    def _t1363(_dollar_dollar):
                        if _dollar_dollar.HasField("int_type"):
                            _t1364 = _dollar_dollar.int_type
                        else:
                            _t1364 = None
                        return _t1364
                    _t1365 = _t1363(msg)
                    deconstruct_result787 = _t1365
                    if deconstruct_result787 is not None:
                        assert deconstruct_result787 is not None
                        unwrapped788 = deconstruct_result787
                        self.pretty_int_type(unwrapped788)
                    else:
                        def _t1366(_dollar_dollar):
                            if _dollar_dollar.HasField("float_type"):
                                _t1367 = _dollar_dollar.float_type
                            else:
                                _t1367 = None
                            return _t1367
                        _t1368 = _t1366(msg)
                        deconstruct_result785 = _t1368
                        if deconstruct_result785 is not None:
                            assert deconstruct_result785 is not None
                            unwrapped786 = deconstruct_result785
                            self.pretty_float_type(unwrapped786)
                        else:
                            def _t1369(_dollar_dollar):
                                if _dollar_dollar.HasField("uint128_type"):
                                    _t1370 = _dollar_dollar.uint128_type
                                else:
                                    _t1370 = None
                                return _t1370
                            _t1371 = _t1369(msg)
                            deconstruct_result783 = _t1371
                            if deconstruct_result783 is not None:
                                assert deconstruct_result783 is not None
                                unwrapped784 = deconstruct_result783
                                self.pretty_uint128_type(unwrapped784)
                            else:
                                def _t1372(_dollar_dollar):
                                    if _dollar_dollar.HasField("int128_type"):
                                        _t1373 = _dollar_dollar.int128_type
                                    else:
                                        _t1373 = None
                                    return _t1373
                                _t1374 = _t1372(msg)
                                deconstruct_result781 = _t1374
                                if deconstruct_result781 is not None:
                                    assert deconstruct_result781 is not None
                                    unwrapped782 = deconstruct_result781
                                    self.pretty_int128_type(unwrapped782)
                                else:
                                    def _t1375(_dollar_dollar):
                                        if _dollar_dollar.HasField("date_type"):
                                            _t1376 = _dollar_dollar.date_type
                                        else:
                                            _t1376 = None
                                        return _t1376
                                    _t1377 = _t1375(msg)
                                    deconstruct_result779 = _t1377
                                    if deconstruct_result779 is not None:
                                        assert deconstruct_result779 is not None
                                        unwrapped780 = deconstruct_result779
                                        self.pretty_date_type(unwrapped780)
                                    else:
                                        def _t1378(_dollar_dollar):
                                            if _dollar_dollar.HasField("datetime_type"):
                                                _t1379 = _dollar_dollar.datetime_type
                                            else:
                                                _t1379 = None
                                            return _t1379
                                        _t1380 = _t1378(msg)
                                        deconstruct_result777 = _t1380
                                        if deconstruct_result777 is not None:
                                            assert deconstruct_result777 is not None
                                            unwrapped778 = deconstruct_result777
                                            self.pretty_datetime_type(unwrapped778)
                                        else:
                                            def _t1381(_dollar_dollar):
                                                if _dollar_dollar.HasField("missing_type"):
                                                    _t1382 = _dollar_dollar.missing_type
                                                else:
                                                    _t1382 = None
                                                return _t1382
                                            _t1383 = _t1381(msg)
                                            deconstruct_result775 = _t1383
                                            if deconstruct_result775 is not None:
                                                assert deconstruct_result775 is not None
                                                unwrapped776 = deconstruct_result775
                                                self.pretty_missing_type(unwrapped776)
                                            else:
                                                def _t1384(_dollar_dollar):
                                                    if _dollar_dollar.HasField("decimal_type"):
                                                        _t1385 = _dollar_dollar.decimal_type
                                                    else:
                                                        _t1385 = None
                                                    return _t1385
                                                _t1386 = _t1384(msg)
                                                deconstruct_result773 = _t1386
                                                if deconstruct_result773 is not None:
                                                    assert deconstruct_result773 is not None
                                                    unwrapped774 = deconstruct_result773
                                                    self.pretty_decimal_type(unwrapped774)
                                                else:
                                                    def _t1387(_dollar_dollar):
                                                        if _dollar_dollar.HasField("boolean_type"):
                                                            _t1388 = _dollar_dollar.boolean_type
                                                        else:
                                                            _t1388 = None
                                                        return _t1388
                                                    _t1389 = _t1387(msg)
                                                    deconstruct_result771 = _t1389
                                                    if deconstruct_result771 is not None:
                                                        assert deconstruct_result771 is not None
                                                        unwrapped772 = deconstruct_result771
                                                        self.pretty_boolean_type(unwrapped772)
                                                    else:
                                                        raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields794 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields795 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields796 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields797 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields798 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields799 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields800 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields801 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields802 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat807 = self._try_flat(msg, self.pretty_decimal_type)
        if flat807 is not None:
            assert flat807 is not None
            self.write(flat807)
            return None
        else:
            def _t1390(_dollar_dollar):
                return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            _t1391 = _t1390(msg)
            fields803 = _t1391
            assert fields803 is not None
            unwrapped_fields804 = fields803
            self.write("(")
            self.write("DECIMAL")
            self.indent_sexp()
            self.newline()
            field805 = unwrapped_fields804[0]
            self.write(str(field805))
            self.newline()
            field806 = unwrapped_fields804[1]
            self.write(str(field806))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields808 = msg
        self.write("BOOLEAN")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat812 = self._try_flat(msg, self.pretty_value_bindings)
        if flat812 is not None:
            assert flat812 is not None
            self.write(flat812)
            return None
        else:
            fields809 = msg
            self.write("|")
            if not len(fields809) == 0:
                self.write(" ")
                for i811, elem810 in enumerate(fields809):
                    if (i811 > 0):
                        self.newline()
                    self.pretty_binding(elem810)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat839 = self._try_flat(msg, self.pretty_formula)
        if flat839 is not None:
            assert flat839 is not None
            self.write(flat839)
            return None
        else:
            def _t1392(_dollar_dollar):
                if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                    _t1393 = _dollar_dollar.conjunction
                else:
                    _t1393 = None
                return _t1393
            _t1394 = _t1392(msg)
            deconstruct_result837 = _t1394
            if deconstruct_result837 is not None:
                assert deconstruct_result837 is not None
                unwrapped838 = deconstruct_result837
                self.pretty_true(unwrapped838)
            else:
                def _t1395(_dollar_dollar):
                    if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                        _t1396 = _dollar_dollar.disjunction
                    else:
                        _t1396 = None
                    return _t1396
                _t1397 = _t1395(msg)
                deconstruct_result835 = _t1397
                if deconstruct_result835 is not None:
                    assert deconstruct_result835 is not None
                    unwrapped836 = deconstruct_result835
                    self.pretty_false(unwrapped836)
                else:
                    def _t1398(_dollar_dollar):
                        if _dollar_dollar.HasField("exists"):
                            _t1399 = _dollar_dollar.exists
                        else:
                            _t1399 = None
                        return _t1399
                    _t1400 = _t1398(msg)
                    deconstruct_result833 = _t1400
                    if deconstruct_result833 is not None:
                        assert deconstruct_result833 is not None
                        unwrapped834 = deconstruct_result833
                        self.pretty_exists(unwrapped834)
                    else:
                        def _t1401(_dollar_dollar):
                            if _dollar_dollar.HasField("reduce"):
                                _t1402 = _dollar_dollar.reduce
                            else:
                                _t1402 = None
                            return _t1402
                        _t1403 = _t1401(msg)
                        deconstruct_result831 = _t1403
                        if deconstruct_result831 is not None:
                            assert deconstruct_result831 is not None
                            unwrapped832 = deconstruct_result831
                            self.pretty_reduce(unwrapped832)
                        else:
                            def _t1404(_dollar_dollar):
                                if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                    _t1405 = _dollar_dollar.conjunction
                                else:
                                    _t1405 = None
                                return _t1405
                            _t1406 = _t1404(msg)
                            deconstruct_result829 = _t1406
                            if deconstruct_result829 is not None:
                                assert deconstruct_result829 is not None
                                unwrapped830 = deconstruct_result829
                                self.pretty_conjunction(unwrapped830)
                            else:
                                def _t1407(_dollar_dollar):
                                    if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                        _t1408 = _dollar_dollar.disjunction
                                    else:
                                        _t1408 = None
                                    return _t1408
                                _t1409 = _t1407(msg)
                                deconstruct_result827 = _t1409
                                if deconstruct_result827 is not None:
                                    assert deconstruct_result827 is not None
                                    unwrapped828 = deconstruct_result827
                                    self.pretty_disjunction(unwrapped828)
                                else:
                                    def _t1410(_dollar_dollar):
                                        if _dollar_dollar.HasField("not"):
                                            _t1411 = getattr(_dollar_dollar, 'not')
                                        else:
                                            _t1411 = None
                                        return _t1411
                                    _t1412 = _t1410(msg)
                                    deconstruct_result825 = _t1412
                                    if deconstruct_result825 is not None:
                                        assert deconstruct_result825 is not None
                                        unwrapped826 = deconstruct_result825
                                        self.pretty_not(unwrapped826)
                                    else:
                                        def _t1413(_dollar_dollar):
                                            if _dollar_dollar.HasField("ffi"):
                                                _t1414 = _dollar_dollar.ffi
                                            else:
                                                _t1414 = None
                                            return _t1414
                                        _t1415 = _t1413(msg)
                                        deconstruct_result823 = _t1415
                                        if deconstruct_result823 is not None:
                                            assert deconstruct_result823 is not None
                                            unwrapped824 = deconstruct_result823
                                            self.pretty_ffi(unwrapped824)
                                        else:
                                            def _t1416(_dollar_dollar):
                                                if _dollar_dollar.HasField("atom"):
                                                    _t1417 = _dollar_dollar.atom
                                                else:
                                                    _t1417 = None
                                                return _t1417
                                            _t1418 = _t1416(msg)
                                            deconstruct_result821 = _t1418
                                            if deconstruct_result821 is not None:
                                                assert deconstruct_result821 is not None
                                                unwrapped822 = deconstruct_result821
                                                self.pretty_atom(unwrapped822)
                                            else:
                                                def _t1419(_dollar_dollar):
                                                    if _dollar_dollar.HasField("pragma"):
                                                        _t1420 = _dollar_dollar.pragma
                                                    else:
                                                        _t1420 = None
                                                    return _t1420
                                                _t1421 = _t1419(msg)
                                                deconstruct_result819 = _t1421
                                                if deconstruct_result819 is not None:
                                                    assert deconstruct_result819 is not None
                                                    unwrapped820 = deconstruct_result819
                                                    self.pretty_pragma(unwrapped820)
                                                else:
                                                    def _t1422(_dollar_dollar):
                                                        if _dollar_dollar.HasField("primitive"):
                                                            _t1423 = _dollar_dollar.primitive
                                                        else:
                                                            _t1423 = None
                                                        return _t1423
                                                    _t1424 = _t1422(msg)
                                                    deconstruct_result817 = _t1424
                                                    if deconstruct_result817 is not None:
                                                        assert deconstruct_result817 is not None
                                                        unwrapped818 = deconstruct_result817
                                                        self.pretty_primitive(unwrapped818)
                                                    else:
                                                        def _t1425(_dollar_dollar):
                                                            if _dollar_dollar.HasField("rel_atom"):
                                                                _t1426 = _dollar_dollar.rel_atom
                                                            else:
                                                                _t1426 = None
                                                            return _t1426
                                                        _t1427 = _t1425(msg)
                                                        deconstruct_result815 = _t1427
                                                        if deconstruct_result815 is not None:
                                                            assert deconstruct_result815 is not None
                                                            unwrapped816 = deconstruct_result815
                                                            self.pretty_rel_atom(unwrapped816)
                                                        else:
                                                            def _t1428(_dollar_dollar):
                                                                if _dollar_dollar.HasField("cast"):
                                                                    _t1429 = _dollar_dollar.cast
                                                                else:
                                                                    _t1429 = None
                                                                return _t1429
                                                            _t1430 = _t1428(msg)
                                                            deconstruct_result813 = _t1430
                                                            if deconstruct_result813 is not None:
                                                                assert deconstruct_result813 is not None
                                                                unwrapped814 = deconstruct_result813
                                                                self.pretty_cast(unwrapped814)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields840 = msg
        self.write("(")
        self.write("true")
        self.write(")")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields841 = msg
        self.write("(")
        self.write("false")
        self.write(")")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat846 = self._try_flat(msg, self.pretty_exists)
        if flat846 is not None:
            assert flat846 is not None
            self.write(flat846)
            return None
        else:
            def _t1431(_dollar_dollar):
                _t1432 = self.deconstruct_bindings(_dollar_dollar.body)
                return (_t1432, _dollar_dollar.body.value,)
            _t1433 = _t1431(msg)
            fields842 = _t1433
            assert fields842 is not None
            unwrapped_fields843 = fields842
            self.write("(")
            self.write("exists")
            self.indent_sexp()
            self.newline()
            field844 = unwrapped_fields843[0]
            self.pretty_bindings(field844)
            self.newline()
            field845 = unwrapped_fields843[1]
            self.pretty_formula(field845)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat852 = self._try_flat(msg, self.pretty_reduce)
        if flat852 is not None:
            assert flat852 is not None
            self.write(flat852)
            return None
        else:
            def _t1434(_dollar_dollar):
                return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            _t1435 = _t1434(msg)
            fields847 = _t1435
            assert fields847 is not None
            unwrapped_fields848 = fields847
            self.write("(")
            self.write("reduce")
            self.indent_sexp()
            self.newline()
            field849 = unwrapped_fields848[0]
            self.pretty_abstraction(field849)
            self.newline()
            field850 = unwrapped_fields848[1]
            self.pretty_abstraction(field850)
            self.newline()
            field851 = unwrapped_fields848[2]
            self.pretty_terms(field851)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat856 = self._try_flat(msg, self.pretty_terms)
        if flat856 is not None:
            assert flat856 is not None
            self.write(flat856)
            return None
        else:
            fields853 = msg
            self.write("(")
            self.write("terms")
            self.indent_sexp()
            if not len(fields853) == 0:
                self.newline()
                for i855, elem854 in enumerate(fields853):
                    if (i855 > 0):
                        self.newline()
                    self.pretty_term(elem854)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat861 = self._try_flat(msg, self.pretty_term)
        if flat861 is not None:
            assert flat861 is not None
            self.write(flat861)
            return None
        else:
            def _t1436(_dollar_dollar):
                if _dollar_dollar.HasField("var"):
                    _t1437 = _dollar_dollar.var
                else:
                    _t1437 = None
                return _t1437
            _t1438 = _t1436(msg)
            deconstruct_result859 = _t1438
            if deconstruct_result859 is not None:
                assert deconstruct_result859 is not None
                unwrapped860 = deconstruct_result859
                self.pretty_var(unwrapped860)
            else:
                def _t1439(_dollar_dollar):
                    if _dollar_dollar.HasField("constant"):
                        _t1440 = _dollar_dollar.constant
                    else:
                        _t1440 = None
                    return _t1440
                _t1441 = _t1439(msg)
                deconstruct_result857 = _t1441
                if deconstruct_result857 is not None:
                    assert deconstruct_result857 is not None
                    unwrapped858 = deconstruct_result857
                    self.pretty_constant(unwrapped858)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat864 = self._try_flat(msg, self.pretty_var)
        if flat864 is not None:
            assert flat864 is not None
            self.write(flat864)
            return None
        else:
            def _t1442(_dollar_dollar):
                return _dollar_dollar.name
            _t1443 = _t1442(msg)
            fields862 = _t1443
            assert fields862 is not None
            unwrapped_fields863 = fields862
            self.write(unwrapped_fields863)

    def pretty_constant(self, msg: logic_pb2.Value):
        flat866 = self._try_flat(msg, self.pretty_constant)
        if flat866 is not None:
            assert flat866 is not None
            self.write(flat866)
            return None
        else:
            fields865 = msg
            self.pretty_value(fields865)

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat871 = self._try_flat(msg, self.pretty_conjunction)
        if flat871 is not None:
            assert flat871 is not None
            self.write(flat871)
            return None
        else:
            def _t1444(_dollar_dollar):
                return _dollar_dollar.args
            _t1445 = _t1444(msg)
            fields867 = _t1445
            assert fields867 is not None
            unwrapped_fields868 = fields867
            self.write("(")
            self.write("and")
            self.indent_sexp()
            if not len(unwrapped_fields868) == 0:
                self.newline()
                for i870, elem869 in enumerate(unwrapped_fields868):
                    if (i870 > 0):
                        self.newline()
                    self.pretty_formula(elem869)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat876 = self._try_flat(msg, self.pretty_disjunction)
        if flat876 is not None:
            assert flat876 is not None
            self.write(flat876)
            return None
        else:
            def _t1446(_dollar_dollar):
                return _dollar_dollar.args
            _t1447 = _t1446(msg)
            fields872 = _t1447
            assert fields872 is not None
            unwrapped_fields873 = fields872
            self.write("(")
            self.write("or")
            self.indent_sexp()
            if not len(unwrapped_fields873) == 0:
                self.newline()
                for i875, elem874 in enumerate(unwrapped_fields873):
                    if (i875 > 0):
                        self.newline()
                    self.pretty_formula(elem874)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat879 = self._try_flat(msg, self.pretty_not)
        if flat879 is not None:
            assert flat879 is not None
            self.write(flat879)
            return None
        else:
            def _t1448(_dollar_dollar):
                return _dollar_dollar.arg
            _t1449 = _t1448(msg)
            fields877 = _t1449
            assert fields877 is not None
            unwrapped_fields878 = fields877
            self.write("(")
            self.write("not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields878)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat885 = self._try_flat(msg, self.pretty_ffi)
        if flat885 is not None:
            assert flat885 is not None
            self.write(flat885)
            return None
        else:
            def _t1450(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            _t1451 = _t1450(msg)
            fields880 = _t1451
            assert fields880 is not None
            unwrapped_fields881 = fields880
            self.write("(")
            self.write("ffi")
            self.indent_sexp()
            self.newline()
            field882 = unwrapped_fields881[0]
            self.pretty_name(field882)
            self.newline()
            field883 = unwrapped_fields881[1]
            self.pretty_ffi_args(field883)
            self.newline()
            field884 = unwrapped_fields881[2]
            self.pretty_terms(field884)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat887 = self._try_flat(msg, self.pretty_name)
        if flat887 is not None:
            assert flat887 is not None
            self.write(flat887)
            return None
        else:
            fields886 = msg
            self.write(":")
            self.write(fields886)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat891 = self._try_flat(msg, self.pretty_ffi_args)
        if flat891 is not None:
            assert flat891 is not None
            self.write(flat891)
            return None
        else:
            fields888 = msg
            self.write("(")
            self.write("args")
            self.indent_sexp()
            if not len(fields888) == 0:
                self.newline()
                for i890, elem889 in enumerate(fields888):
                    if (i890 > 0):
                        self.newline()
                    self.pretty_abstraction(elem889)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat898 = self._try_flat(msg, self.pretty_atom)
        if flat898 is not None:
            assert flat898 is not None
            self.write(flat898)
            return None
        else:
            def _t1452(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1453 = _t1452(msg)
            fields892 = _t1453
            assert fields892 is not None
            unwrapped_fields893 = fields892
            self.write("(")
            self.write("atom")
            self.indent_sexp()
            self.newline()
            field894 = unwrapped_fields893[0]
            self.pretty_relation_id(field894)
            field895 = unwrapped_fields893[1]
            if not len(field895) == 0:
                self.newline()
                for i897, elem896 in enumerate(field895):
                    if (i897 > 0):
                        self.newline()
                    self.pretty_term(elem896)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat905 = self._try_flat(msg, self.pretty_pragma)
        if flat905 is not None:
            assert flat905 is not None
            self.write(flat905)
            return None
        else:
            def _t1454(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1455 = _t1454(msg)
            fields899 = _t1455
            assert fields899 is not None
            unwrapped_fields900 = fields899
            self.write("(")
            self.write("pragma")
            self.indent_sexp()
            self.newline()
            field901 = unwrapped_fields900[0]
            self.pretty_name(field901)
            field902 = unwrapped_fields900[1]
            if not len(field902) == 0:
                self.newline()
                for i904, elem903 in enumerate(field902):
                    if (i904 > 0):
                        self.newline()
                    self.pretty_term(elem903)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat921 = self._try_flat(msg, self.pretty_primitive)
        if flat921 is not None:
            assert flat921 is not None
            self.write(flat921)
            return None
        else:
            def _t1456(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1457 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1457 = None
                return _t1457
            _t1458 = _t1456(msg)
            guard_result920 = _t1458
            if guard_result920 is not None:
                self.pretty_eq(msg)
            else:
                def _t1459(_dollar_dollar):
                    if _dollar_dollar.name == "rel_primitive_lt_monotype":
                        _t1460 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1460 = None
                    return _t1460
                _t1461 = _t1459(msg)
                guard_result919 = _t1461
                if guard_result919 is not None:
                    self.pretty_lt(msg)
                else:
                    def _t1462(_dollar_dollar):
                        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                            _t1463 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1463 = None
                        return _t1463
                    _t1464 = _t1462(msg)
                    guard_result918 = _t1464
                    if guard_result918 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        def _t1465(_dollar_dollar):
                            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                                _t1466 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1466 = None
                            return _t1466
                        _t1467 = _t1465(msg)
                        guard_result917 = _t1467
                        if guard_result917 is not None:
                            self.pretty_gt(msg)
                        else:
                            def _t1468(_dollar_dollar):
                                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                    _t1469 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                                else:
                                    _t1469 = None
                                return _t1469
                            _t1470 = _t1468(msg)
                            guard_result916 = _t1470
                            if guard_result916 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                def _t1471(_dollar_dollar):
                                    if _dollar_dollar.name == "rel_primitive_add_monotype":
                                        _t1472 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1472 = None
                                    return _t1472
                                _t1473 = _t1471(msg)
                                guard_result915 = _t1473
                                if guard_result915 is not None:
                                    self.pretty_add(msg)
                                else:
                                    def _t1474(_dollar_dollar):
                                        if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                            _t1475 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1475 = None
                                        return _t1475
                                    _t1476 = _t1474(msg)
                                    guard_result914 = _t1476
                                    if guard_result914 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        def _t1477(_dollar_dollar):
                                            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                                _t1478 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1478 = None
                                            return _t1478
                                        _t1479 = _t1477(msg)
                                        guard_result913 = _t1479
                                        if guard_result913 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            def _t1480(_dollar_dollar):
                                                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                    _t1481 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                                else:
                                                    _t1481 = None
                                                return _t1481
                                            _t1482 = _t1480(msg)
                                            guard_result912 = _t1482
                                            if guard_result912 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                def _t1483(_dollar_dollar):
                                                    return (_dollar_dollar.name, _dollar_dollar.terms,)
                                                _t1484 = _t1483(msg)
                                                fields906 = _t1484
                                                assert fields906 is not None
                                                unwrapped_fields907 = fields906
                                                self.write("(")
                                                self.write("primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field908 = unwrapped_fields907[0]
                                                self.pretty_name(field908)
                                                field909 = unwrapped_fields907[1]
                                                if not len(field909) == 0:
                                                    self.newline()
                                                    for i911, elem910 in enumerate(field909):
                                                        if (i911 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem910)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat926 = self._try_flat(msg, self.pretty_eq)
        if flat926 is not None:
            assert flat926 is not None
            self.write(flat926)
            return None
        else:
            def _t1485(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1486 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1486 = None
                return _t1486
            _t1487 = _t1485(msg)
            fields922 = _t1487
            assert fields922 is not None
            unwrapped_fields923 = fields922
            self.write("(")
            self.write("=")
            self.indent_sexp()
            self.newline()
            field924 = unwrapped_fields923[0]
            self.pretty_term(field924)
            self.newline()
            field925 = unwrapped_fields923[1]
            self.pretty_term(field925)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat931 = self._try_flat(msg, self.pretty_lt)
        if flat931 is not None:
            assert flat931 is not None
            self.write(flat931)
            return None
        else:
            def _t1488(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1489 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1489 = None
                return _t1489
            _t1490 = _t1488(msg)
            fields927 = _t1490
            assert fields927 is not None
            unwrapped_fields928 = fields927
            self.write("(")
            self.write("<")
            self.indent_sexp()
            self.newline()
            field929 = unwrapped_fields928[0]
            self.pretty_term(field929)
            self.newline()
            field930 = unwrapped_fields928[1]
            self.pretty_term(field930)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat936 = self._try_flat(msg, self.pretty_lt_eq)
        if flat936 is not None:
            assert flat936 is not None
            self.write(flat936)
            return None
        else:
            def _t1491(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                    _t1492 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1492 = None
                return _t1492
            _t1493 = _t1491(msg)
            fields932 = _t1493
            assert fields932 is not None
            unwrapped_fields933 = fields932
            self.write("(")
            self.write("<=")
            self.indent_sexp()
            self.newline()
            field934 = unwrapped_fields933[0]
            self.pretty_term(field934)
            self.newline()
            field935 = unwrapped_fields933[1]
            self.pretty_term(field935)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat941 = self._try_flat(msg, self.pretty_gt)
        if flat941 is not None:
            assert flat941 is not None
            self.write(flat941)
            return None
        else:
            def _t1494(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_monotype":
                    _t1495 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1495 = None
                return _t1495
            _t1496 = _t1494(msg)
            fields937 = _t1496
            assert fields937 is not None
            unwrapped_fields938 = fields937
            self.write("(")
            self.write(">")
            self.indent_sexp()
            self.newline()
            field939 = unwrapped_fields938[0]
            self.pretty_term(field939)
            self.newline()
            field940 = unwrapped_fields938[1]
            self.pretty_term(field940)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat946 = self._try_flat(msg, self.pretty_gt_eq)
        if flat946 is not None:
            assert flat946 is not None
            self.write(flat946)
            return None
        else:
            def _t1497(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                    _t1498 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1498 = None
                return _t1498
            _t1499 = _t1497(msg)
            fields942 = _t1499
            assert fields942 is not None
            unwrapped_fields943 = fields942
            self.write("(")
            self.write(">=")
            self.indent_sexp()
            self.newline()
            field944 = unwrapped_fields943[0]
            self.pretty_term(field944)
            self.newline()
            field945 = unwrapped_fields943[1]
            self.pretty_term(field945)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat952 = self._try_flat(msg, self.pretty_add)
        if flat952 is not None:
            assert flat952 is not None
            self.write(flat952)
            return None
        else:
            def _t1500(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_add_monotype":
                    _t1501 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1501 = None
                return _t1501
            _t1502 = _t1500(msg)
            fields947 = _t1502
            assert fields947 is not None
            unwrapped_fields948 = fields947
            self.write("(")
            self.write("+")
            self.indent_sexp()
            self.newline()
            field949 = unwrapped_fields948[0]
            self.pretty_term(field949)
            self.newline()
            field950 = unwrapped_fields948[1]
            self.pretty_term(field950)
            self.newline()
            field951 = unwrapped_fields948[2]
            self.pretty_term(field951)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat958 = self._try_flat(msg, self.pretty_minus)
        if flat958 is not None:
            assert flat958 is not None
            self.write(flat958)
            return None
        else:
            def _t1503(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                    _t1504 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1504 = None
                return _t1504
            _t1505 = _t1503(msg)
            fields953 = _t1505
            assert fields953 is not None
            unwrapped_fields954 = fields953
            self.write("(")
            self.write("-")
            self.indent_sexp()
            self.newline()
            field955 = unwrapped_fields954[0]
            self.pretty_term(field955)
            self.newline()
            field956 = unwrapped_fields954[1]
            self.pretty_term(field956)
            self.newline()
            field957 = unwrapped_fields954[2]
            self.pretty_term(field957)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat964 = self._try_flat(msg, self.pretty_multiply)
        if flat964 is not None:
            assert flat964 is not None
            self.write(flat964)
            return None
        else:
            def _t1506(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                    _t1507 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1507 = None
                return _t1507
            _t1508 = _t1506(msg)
            fields959 = _t1508
            assert fields959 is not None
            unwrapped_fields960 = fields959
            self.write("(")
            self.write("*")
            self.indent_sexp()
            self.newline()
            field961 = unwrapped_fields960[0]
            self.pretty_term(field961)
            self.newline()
            field962 = unwrapped_fields960[1]
            self.pretty_term(field962)
            self.newline()
            field963 = unwrapped_fields960[2]
            self.pretty_term(field963)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat970 = self._try_flat(msg, self.pretty_divide)
        if flat970 is not None:
            assert flat970 is not None
            self.write(flat970)
            return None
        else:
            def _t1509(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                    _t1510 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1510 = None
                return _t1510
            _t1511 = _t1509(msg)
            fields965 = _t1511
            assert fields965 is not None
            unwrapped_fields966 = fields965
            self.write("(")
            self.write("/")
            self.indent_sexp()
            self.newline()
            field967 = unwrapped_fields966[0]
            self.pretty_term(field967)
            self.newline()
            field968 = unwrapped_fields966[1]
            self.pretty_term(field968)
            self.newline()
            field969 = unwrapped_fields966[2]
            self.pretty_term(field969)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat975 = self._try_flat(msg, self.pretty_rel_term)
        if flat975 is not None:
            assert flat975 is not None
            self.write(flat975)
            return None
        else:
            def _t1512(_dollar_dollar):
                if _dollar_dollar.HasField("specialized_value"):
                    _t1513 = _dollar_dollar.specialized_value
                else:
                    _t1513 = None
                return _t1513
            _t1514 = _t1512(msg)
            deconstruct_result973 = _t1514
            if deconstruct_result973 is not None:
                assert deconstruct_result973 is not None
                unwrapped974 = deconstruct_result973
                self.pretty_specialized_value(unwrapped974)
            else:
                def _t1515(_dollar_dollar):
                    if _dollar_dollar.HasField("term"):
                        _t1516 = _dollar_dollar.term
                    else:
                        _t1516 = None
                    return _t1516
                _t1517 = _t1515(msg)
                deconstruct_result971 = _t1517
                if deconstruct_result971 is not None:
                    assert deconstruct_result971 is not None
                    unwrapped972 = deconstruct_result971
                    self.pretty_term(unwrapped972)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat977 = self._try_flat(msg, self.pretty_specialized_value)
        if flat977 is not None:
            assert flat977 is not None
            self.write(flat977)
            return None
        else:
            fields976 = msg
            self.write("#")
            self.pretty_value(fields976)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat984 = self._try_flat(msg, self.pretty_rel_atom)
        if flat984 is not None:
            assert flat984 is not None
            self.write(flat984)
            return None
        else:
            def _t1518(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1519 = _t1518(msg)
            fields978 = _t1519
            assert fields978 is not None
            unwrapped_fields979 = fields978
            self.write("(")
            self.write("relatom")
            self.indent_sexp()
            self.newline()
            field980 = unwrapped_fields979[0]
            self.pretty_name(field980)
            field981 = unwrapped_fields979[1]
            if not len(field981) == 0:
                self.newline()
                for i983, elem982 in enumerate(field981):
                    if (i983 > 0):
                        self.newline()
                    self.pretty_rel_term(elem982)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat989 = self._try_flat(msg, self.pretty_cast)
        if flat989 is not None:
            assert flat989 is not None
            self.write(flat989)
            return None
        else:
            def _t1520(_dollar_dollar):
                return (_dollar_dollar.input, _dollar_dollar.result,)
            _t1521 = _t1520(msg)
            fields985 = _t1521
            assert fields985 is not None
            unwrapped_fields986 = fields985
            self.write("(")
            self.write("cast")
            self.indent_sexp()
            self.newline()
            field987 = unwrapped_fields986[0]
            self.pretty_term(field987)
            self.newline()
            field988 = unwrapped_fields986[1]
            self.pretty_term(field988)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat993 = self._try_flat(msg, self.pretty_attrs)
        if flat993 is not None:
            assert flat993 is not None
            self.write(flat993)
            return None
        else:
            fields990 = msg
            self.write("(")
            self.write("attrs")
            self.indent_sexp()
            if not len(fields990) == 0:
                self.newline()
                for i992, elem991 in enumerate(fields990):
                    if (i992 > 0):
                        self.newline()
                    self.pretty_attribute(elem991)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1000 = self._try_flat(msg, self.pretty_attribute)
        if flat1000 is not None:
            assert flat1000 is not None
            self.write(flat1000)
            return None
        else:
            def _t1522(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args,)
            _t1523 = _t1522(msg)
            fields994 = _t1523
            assert fields994 is not None
            unwrapped_fields995 = fields994
            self.write("(")
            self.write("attribute")
            self.indent_sexp()
            self.newline()
            field996 = unwrapped_fields995[0]
            self.pretty_name(field996)
            field997 = unwrapped_fields995[1]
            if not len(field997) == 0:
                self.newline()
                for i999, elem998 in enumerate(field997):
                    if (i999 > 0):
                        self.newline()
                    self.pretty_value(elem998)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1007 = self._try_flat(msg, self.pretty_algorithm)
        if flat1007 is not None:
            assert flat1007 is not None
            self.write(flat1007)
            return None
        else:
            def _t1524(_dollar_dollar):
                return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            _t1525 = _t1524(msg)
            fields1001 = _t1525
            assert fields1001 is not None
            unwrapped_fields1002 = fields1001
            self.write("(")
            self.write("algorithm")
            self.indent_sexp()
            field1003 = unwrapped_fields1002[0]
            if not len(field1003) == 0:
                self.newline()
                for i1005, elem1004 in enumerate(field1003):
                    if (i1005 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1004)
            self.newline()
            field1006 = unwrapped_fields1002[1]
            self.pretty_script(field1006)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1012 = self._try_flat(msg, self.pretty_script)
        if flat1012 is not None:
            assert flat1012 is not None
            self.write(flat1012)
            return None
        else:
            def _t1526(_dollar_dollar):
                return _dollar_dollar.constructs
            _t1527 = _t1526(msg)
            fields1008 = _t1527
            assert fields1008 is not None
            unwrapped_fields1009 = fields1008
            self.write("(")
            self.write("script")
            self.indent_sexp()
            if not len(unwrapped_fields1009) == 0:
                self.newline()
                for i1011, elem1010 in enumerate(unwrapped_fields1009):
                    if (i1011 > 0):
                        self.newline()
                    self.pretty_construct(elem1010)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1017 = self._try_flat(msg, self.pretty_construct)
        if flat1017 is not None:
            assert flat1017 is not None
            self.write(flat1017)
            return None
        else:
            def _t1528(_dollar_dollar):
                if _dollar_dollar.HasField("loop"):
                    _t1529 = _dollar_dollar.loop
                else:
                    _t1529 = None
                return _t1529
            _t1530 = _t1528(msg)
            deconstruct_result1015 = _t1530
            if deconstruct_result1015 is not None:
                assert deconstruct_result1015 is not None
                unwrapped1016 = deconstruct_result1015
                self.pretty_loop(unwrapped1016)
            else:
                def _t1531(_dollar_dollar):
                    if _dollar_dollar.HasField("instruction"):
                        _t1532 = _dollar_dollar.instruction
                    else:
                        _t1532 = None
                    return _t1532
                _t1533 = _t1531(msg)
                deconstruct_result1013 = _t1533
                if deconstruct_result1013 is not None:
                    assert deconstruct_result1013 is not None
                    unwrapped1014 = deconstruct_result1013
                    self.pretty_instruction(unwrapped1014)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1022 = self._try_flat(msg, self.pretty_loop)
        if flat1022 is not None:
            assert flat1022 is not None
            self.write(flat1022)
            return None
        else:
            def _t1534(_dollar_dollar):
                return (_dollar_dollar.init, _dollar_dollar.body,)
            _t1535 = _t1534(msg)
            fields1018 = _t1535
            assert fields1018 is not None
            unwrapped_fields1019 = fields1018
            self.write("(")
            self.write("loop")
            self.indent_sexp()
            self.newline()
            field1020 = unwrapped_fields1019[0]
            self.pretty_init(field1020)
            self.newline()
            field1021 = unwrapped_fields1019[1]
            self.pretty_script(field1021)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1026 = self._try_flat(msg, self.pretty_init)
        if flat1026 is not None:
            assert flat1026 is not None
            self.write(flat1026)
            return None
        else:
            fields1023 = msg
            self.write("(")
            self.write("init")
            self.indent_sexp()
            if not len(fields1023) == 0:
                self.newline()
                for i1025, elem1024 in enumerate(fields1023):
                    if (i1025 > 0):
                        self.newline()
                    self.pretty_instruction(elem1024)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1037 = self._try_flat(msg, self.pretty_instruction)
        if flat1037 is not None:
            assert flat1037 is not None
            self.write(flat1037)
            return None
        else:
            def _t1536(_dollar_dollar):
                if _dollar_dollar.HasField("assign"):
                    _t1537 = _dollar_dollar.assign
                else:
                    _t1537 = None
                return _t1537
            _t1538 = _t1536(msg)
            deconstruct_result1035 = _t1538
            if deconstruct_result1035 is not None:
                assert deconstruct_result1035 is not None
                unwrapped1036 = deconstruct_result1035
                self.pretty_assign(unwrapped1036)
            else:
                def _t1539(_dollar_dollar):
                    if _dollar_dollar.HasField("upsert"):
                        _t1540 = _dollar_dollar.upsert
                    else:
                        _t1540 = None
                    return _t1540
                _t1541 = _t1539(msg)
                deconstruct_result1033 = _t1541
                if deconstruct_result1033 is not None:
                    assert deconstruct_result1033 is not None
                    unwrapped1034 = deconstruct_result1033
                    self.pretty_upsert(unwrapped1034)
                else:
                    def _t1542(_dollar_dollar):
                        if _dollar_dollar.HasField("break"):
                            _t1543 = getattr(_dollar_dollar, 'break')
                        else:
                            _t1543 = None
                        return _t1543
                    _t1544 = _t1542(msg)
                    deconstruct_result1031 = _t1544
                    if deconstruct_result1031 is not None:
                        assert deconstruct_result1031 is not None
                        unwrapped1032 = deconstruct_result1031
                        self.pretty_break(unwrapped1032)
                    else:
                        def _t1545(_dollar_dollar):
                            if _dollar_dollar.HasField("monoid_def"):
                                _t1546 = _dollar_dollar.monoid_def
                            else:
                                _t1546 = None
                            return _t1546
                        _t1547 = _t1545(msg)
                        deconstruct_result1029 = _t1547
                        if deconstruct_result1029 is not None:
                            assert deconstruct_result1029 is not None
                            unwrapped1030 = deconstruct_result1029
                            self.pretty_monoid_def(unwrapped1030)
                        else:
                            def _t1548(_dollar_dollar):
                                if _dollar_dollar.HasField("monus_def"):
                                    _t1549 = _dollar_dollar.monus_def
                                else:
                                    _t1549 = None
                                return _t1549
                            _t1550 = _t1548(msg)
                            deconstruct_result1027 = _t1550
                            if deconstruct_result1027 is not None:
                                assert deconstruct_result1027 is not None
                                unwrapped1028 = deconstruct_result1027
                                self.pretty_monus_def(unwrapped1028)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1044 = self._try_flat(msg, self.pretty_assign)
        if flat1044 is not None:
            assert flat1044 is not None
            self.write(flat1044)
            return None
        else:
            def _t1551(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1552 = _dollar_dollar.attrs
                else:
                    _t1552 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1552,)
            _t1553 = _t1551(msg)
            fields1038 = _t1553
            assert fields1038 is not None
            unwrapped_fields1039 = fields1038
            self.write("(")
            self.write("assign")
            self.indent_sexp()
            self.newline()
            field1040 = unwrapped_fields1039[0]
            self.pretty_relation_id(field1040)
            self.newline()
            field1041 = unwrapped_fields1039[1]
            self.pretty_abstraction(field1041)
            field1042 = unwrapped_fields1039[2]
            if field1042 is not None:
                self.newline()
                assert field1042 is not None
                opt_val1043 = field1042
                self.pretty_attrs(opt_val1043)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1051 = self._try_flat(msg, self.pretty_upsert)
        if flat1051 is not None:
            assert flat1051 is not None
            self.write(flat1051)
            return None
        else:
            def _t1554(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1555 = _dollar_dollar.attrs
                else:
                    _t1555 = None
                return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1555,)
            _t1556 = _t1554(msg)
            fields1045 = _t1556
            assert fields1045 is not None
            unwrapped_fields1046 = fields1045
            self.write("(")
            self.write("upsert")
            self.indent_sexp()
            self.newline()
            field1047 = unwrapped_fields1046[0]
            self.pretty_relation_id(field1047)
            self.newline()
            field1048 = unwrapped_fields1046[1]
            self.pretty_abstraction_with_arity(field1048)
            field1049 = unwrapped_fields1046[2]
            if field1049 is not None:
                self.newline()
                assert field1049 is not None
                opt_val1050 = field1049
                self.pretty_attrs(opt_val1050)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1056 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1056 is not None:
            assert flat1056 is not None
            self.write(flat1056)
            return None
        else:
            def _t1557(_dollar_dollar):
                _t1558 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
                return (_t1558, _dollar_dollar[0].value,)
            _t1559 = _t1557(msg)
            fields1052 = _t1559
            assert fields1052 is not None
            unwrapped_fields1053 = fields1052
            self.write("(")
            self.indent()
            field1054 = unwrapped_fields1053[0]
            self.pretty_bindings(field1054)
            self.newline()
            field1055 = unwrapped_fields1053[1]
            self.pretty_formula(field1055)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1063 = self._try_flat(msg, self.pretty_break)
        if flat1063 is not None:
            assert flat1063 is not None
            self.write(flat1063)
            return None
        else:
            def _t1560(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1561 = _dollar_dollar.attrs
                else:
                    _t1561 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1561,)
            _t1562 = _t1560(msg)
            fields1057 = _t1562
            assert fields1057 is not None
            unwrapped_fields1058 = fields1057
            self.write("(")
            self.write("break")
            self.indent_sexp()
            self.newline()
            field1059 = unwrapped_fields1058[0]
            self.pretty_relation_id(field1059)
            self.newline()
            field1060 = unwrapped_fields1058[1]
            self.pretty_abstraction(field1060)
            field1061 = unwrapped_fields1058[2]
            if field1061 is not None:
                self.newline()
                assert field1061 is not None
                opt_val1062 = field1061
                self.pretty_attrs(opt_val1062)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1071 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1071 is not None:
            assert flat1071 is not None
            self.write(flat1071)
            return None
        else:
            def _t1563(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1564 = _dollar_dollar.attrs
                else:
                    _t1564 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1564,)
            _t1565 = _t1563(msg)
            fields1064 = _t1565
            assert fields1064 is not None
            unwrapped_fields1065 = fields1064
            self.write("(")
            self.write("monoid")
            self.indent_sexp()
            self.newline()
            field1066 = unwrapped_fields1065[0]
            self.pretty_monoid(field1066)
            self.newline()
            field1067 = unwrapped_fields1065[1]
            self.pretty_relation_id(field1067)
            self.newline()
            field1068 = unwrapped_fields1065[2]
            self.pretty_abstraction_with_arity(field1068)
            field1069 = unwrapped_fields1065[3]
            if field1069 is not None:
                self.newline()
                assert field1069 is not None
                opt_val1070 = field1069
                self.pretty_attrs(opt_val1070)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1080 = self._try_flat(msg, self.pretty_monoid)
        if flat1080 is not None:
            assert flat1080 is not None
            self.write(flat1080)
            return None
        else:
            def _t1566(_dollar_dollar):
                if _dollar_dollar.HasField("or_monoid"):
                    _t1567 = _dollar_dollar.or_monoid
                else:
                    _t1567 = None
                return _t1567
            _t1568 = _t1566(msg)
            deconstruct_result1078 = _t1568
            if deconstruct_result1078 is not None:
                assert deconstruct_result1078 is not None
                unwrapped1079 = deconstruct_result1078
                self.pretty_or_monoid(unwrapped1079)
            else:
                def _t1569(_dollar_dollar):
                    if _dollar_dollar.HasField("min_monoid"):
                        _t1570 = _dollar_dollar.min_monoid
                    else:
                        _t1570 = None
                    return _t1570
                _t1571 = _t1569(msg)
                deconstruct_result1076 = _t1571
                if deconstruct_result1076 is not None:
                    assert deconstruct_result1076 is not None
                    unwrapped1077 = deconstruct_result1076
                    self.pretty_min_monoid(unwrapped1077)
                else:
                    def _t1572(_dollar_dollar):
                        if _dollar_dollar.HasField("max_monoid"):
                            _t1573 = _dollar_dollar.max_monoid
                        else:
                            _t1573 = None
                        return _t1573
                    _t1574 = _t1572(msg)
                    deconstruct_result1074 = _t1574
                    if deconstruct_result1074 is not None:
                        assert deconstruct_result1074 is not None
                        unwrapped1075 = deconstruct_result1074
                        self.pretty_max_monoid(unwrapped1075)
                    else:
                        def _t1575(_dollar_dollar):
                            if _dollar_dollar.HasField("sum_monoid"):
                                _t1576 = _dollar_dollar.sum_monoid
                            else:
                                _t1576 = None
                            return _t1576
                        _t1577 = _t1575(msg)
                        deconstruct_result1072 = _t1577
                        if deconstruct_result1072 is not None:
                            assert deconstruct_result1072 is not None
                            unwrapped1073 = deconstruct_result1072
                            self.pretty_sum_monoid(unwrapped1073)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1081 = msg
        self.write("(")
        self.write("or")
        self.write(")")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1084 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1084 is not None:
            assert flat1084 is not None
            self.write(flat1084)
            return None
        else:
            def _t1578(_dollar_dollar):
                return _dollar_dollar.type
            _t1579 = _t1578(msg)
            fields1082 = _t1579
            assert fields1082 is not None
            unwrapped_fields1083 = fields1082
            self.write("(")
            self.write("min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1083)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1087 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1087 is not None:
            assert flat1087 is not None
            self.write(flat1087)
            return None
        else:
            def _t1580(_dollar_dollar):
                return _dollar_dollar.type
            _t1581 = _t1580(msg)
            fields1085 = _t1581
            assert fields1085 is not None
            unwrapped_fields1086 = fields1085
            self.write("(")
            self.write("max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1086)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1090 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1090 is not None:
            assert flat1090 is not None
            self.write(flat1090)
            return None
        else:
            def _t1582(_dollar_dollar):
                return _dollar_dollar.type
            _t1583 = _t1582(msg)
            fields1088 = _t1583
            assert fields1088 is not None
            unwrapped_fields1089 = fields1088
            self.write("(")
            self.write("sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1089)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1098 = self._try_flat(msg, self.pretty_monus_def)
        if flat1098 is not None:
            assert flat1098 is not None
            self.write(flat1098)
            return None
        else:
            def _t1584(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1585 = _dollar_dollar.attrs
                else:
                    _t1585 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1585,)
            _t1586 = _t1584(msg)
            fields1091 = _t1586
            assert fields1091 is not None
            unwrapped_fields1092 = fields1091
            self.write("(")
            self.write("monus")
            self.indent_sexp()
            self.newline()
            field1093 = unwrapped_fields1092[0]
            self.pretty_monoid(field1093)
            self.newline()
            field1094 = unwrapped_fields1092[1]
            self.pretty_relation_id(field1094)
            self.newline()
            field1095 = unwrapped_fields1092[2]
            self.pretty_abstraction_with_arity(field1095)
            field1096 = unwrapped_fields1092[3]
            if field1096 is not None:
                self.newline()
                assert field1096 is not None
                opt_val1097 = field1096
                self.pretty_attrs(opt_val1097)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1105 = self._try_flat(msg, self.pretty_constraint)
        if flat1105 is not None:
            assert flat1105 is not None
            self.write(flat1105)
            return None
        else:
            def _t1587(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            _t1588 = _t1587(msg)
            fields1099 = _t1588
            assert fields1099 is not None
            unwrapped_fields1100 = fields1099
            self.write("(")
            self.write("functional_dependency")
            self.indent_sexp()
            self.newline()
            field1101 = unwrapped_fields1100[0]
            self.pretty_relation_id(field1101)
            self.newline()
            field1102 = unwrapped_fields1100[1]
            self.pretty_abstraction(field1102)
            self.newline()
            field1103 = unwrapped_fields1100[2]
            self.pretty_functional_dependency_keys(field1103)
            self.newline()
            field1104 = unwrapped_fields1100[3]
            self.pretty_functional_dependency_values(field1104)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1109 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1109 is not None:
            assert flat1109 is not None
            self.write(flat1109)
            return None
        else:
            fields1106 = msg
            self.write("(")
            self.write("keys")
            self.indent_sexp()
            if not len(fields1106) == 0:
                self.newline()
                for i1108, elem1107 in enumerate(fields1106):
                    if (i1108 > 0):
                        self.newline()
                    self.pretty_var(elem1107)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1113 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1113 is not None:
            assert flat1113 is not None
            self.write(flat1113)
            return None
        else:
            fields1110 = msg
            self.write("(")
            self.write("values")
            self.indent_sexp()
            if not len(fields1110) == 0:
                self.newline()
                for i1112, elem1111 in enumerate(fields1110):
                    if (i1112 > 0):
                        self.newline()
                    self.pretty_var(elem1111)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1120 = self._try_flat(msg, self.pretty_data)
        if flat1120 is not None:
            assert flat1120 is not None
            self.write(flat1120)
            return None
        else:
            def _t1589(_dollar_dollar):
                if _dollar_dollar.HasField("rel_edb"):
                    _t1590 = _dollar_dollar.rel_edb
                else:
                    _t1590 = None
                return _t1590
            _t1591 = _t1589(msg)
            deconstruct_result1118 = _t1591
            if deconstruct_result1118 is not None:
                assert deconstruct_result1118 is not None
                unwrapped1119 = deconstruct_result1118
                self.pretty_rel_edb(unwrapped1119)
            else:
                def _t1592(_dollar_dollar):
                    if _dollar_dollar.HasField("betree_relation"):
                        _t1593 = _dollar_dollar.betree_relation
                    else:
                        _t1593 = None
                    return _t1593
                _t1594 = _t1592(msg)
                deconstruct_result1116 = _t1594
                if deconstruct_result1116 is not None:
                    assert deconstruct_result1116 is not None
                    unwrapped1117 = deconstruct_result1116
                    self.pretty_betree_relation(unwrapped1117)
                else:
                    def _t1595(_dollar_dollar):
                        if _dollar_dollar.HasField("csv_data"):
                            _t1596 = _dollar_dollar.csv_data
                        else:
                            _t1596 = None
                        return _t1596
                    _t1597 = _t1595(msg)
                    deconstruct_result1114 = _t1597
                    if deconstruct_result1114 is not None:
                        assert deconstruct_result1114 is not None
                        unwrapped1115 = deconstruct_result1114
                        self.pretty_csv_data(unwrapped1115)
                    else:
                        raise ParseError("No matching rule for data")

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB):
        flat1126 = self._try_flat(msg, self.pretty_rel_edb)
        if flat1126 is not None:
            assert flat1126 is not None
            self.write(flat1126)
            return None
        else:
            def _t1598(_dollar_dollar):
                return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            _t1599 = _t1598(msg)
            fields1121 = _t1599
            assert fields1121 is not None
            unwrapped_fields1122 = fields1121
            self.write("(")
            self.write("rel_edb")
            self.indent_sexp()
            self.newline()
            field1123 = unwrapped_fields1122[0]
            self.pretty_relation_id(field1123)
            self.newline()
            field1124 = unwrapped_fields1122[1]
            self.pretty_rel_edb_path(field1124)
            self.newline()
            field1125 = unwrapped_fields1122[2]
            self.pretty_rel_edb_types(field1125)
            self.dedent()
            self.write(")")

    def pretty_rel_edb_path(self, msg: Sequence[str]):
        flat1130 = self._try_flat(msg, self.pretty_rel_edb_path)
        if flat1130 is not None:
            assert flat1130 is not None
            self.write(flat1130)
            return None
        else:
            fields1127 = msg
            self.write("[")
            self.indent()
            for i1129, elem1128 in enumerate(fields1127):
                if (i1129 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1128))
            self.dedent()
            self.write("]")

    def pretty_rel_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1134 = self._try_flat(msg, self.pretty_rel_edb_types)
        if flat1134 is not None:
            assert flat1134 is not None
            self.write(flat1134)
            return None
        else:
            fields1131 = msg
            self.write("[")
            self.indent()
            for i1133, elem1132 in enumerate(fields1131):
                if (i1133 > 0):
                    self.newline()
                self.pretty_type(elem1132)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1139 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1139 is not None:
            assert flat1139 is not None
            self.write(flat1139)
            return None
        else:
            def _t1600(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_info,)
            _t1601 = _t1600(msg)
            fields1135 = _t1601
            assert fields1135 is not None
            unwrapped_fields1136 = fields1135
            self.write("(")
            self.write("betree_relation")
            self.indent_sexp()
            self.newline()
            field1137 = unwrapped_fields1136[0]
            self.pretty_relation_id(field1137)
            self.newline()
            field1138 = unwrapped_fields1136[1]
            self.pretty_betree_info(field1138)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1145 = self._try_flat(msg, self.pretty_betree_info)
        if flat1145 is not None:
            assert flat1145 is not None
            self.write(flat1145)
            return None
        else:
            def _t1602(_dollar_dollar):
                _t1603 = self.deconstruct_betree_info_config(_dollar_dollar)
                return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1603,)
            _t1604 = _t1602(msg)
            fields1140 = _t1604
            assert fields1140 is not None
            unwrapped_fields1141 = fields1140
            self.write("(")
            self.write("betree_info")
            self.indent_sexp()
            self.newline()
            field1142 = unwrapped_fields1141[0]
            self.pretty_betree_info_key_types(field1142)
            self.newline()
            field1143 = unwrapped_fields1141[1]
            self.pretty_betree_info_value_types(field1143)
            self.newline()
            field1144 = unwrapped_fields1141[2]
            self.pretty_config_dict(field1144)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1149 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1149 is not None:
            assert flat1149 is not None
            self.write(flat1149)
            return None
        else:
            fields1146 = msg
            self.write("(")
            self.write("key_types")
            self.indent_sexp()
            if not len(fields1146) == 0:
                self.newline()
                for i1148, elem1147 in enumerate(fields1146):
                    if (i1148 > 0):
                        self.newline()
                    self.pretty_type(elem1147)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1153 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1153 is not None:
            assert flat1153 is not None
            self.write(flat1153)
            return None
        else:
            fields1150 = msg
            self.write("(")
            self.write("value_types")
            self.indent_sexp()
            if not len(fields1150) == 0:
                self.newline()
                for i1152, elem1151 in enumerate(fields1150):
                    if (i1152 > 0):
                        self.newline()
                    self.pretty_type(elem1151)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1160 = self._try_flat(msg, self.pretty_csv_data)
        if flat1160 is not None:
            assert flat1160 is not None
            self.write(flat1160)
            return None
        else:
            def _t1605(_dollar_dollar):
                return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            _t1606 = _t1605(msg)
            fields1154 = _t1606
            assert fields1154 is not None
            unwrapped_fields1155 = fields1154
            self.write("(")
            self.write("csv_data")
            self.indent_sexp()
            self.newline()
            field1156 = unwrapped_fields1155[0]
            self.pretty_csvlocator(field1156)
            self.newline()
            field1157 = unwrapped_fields1155[1]
            self.pretty_csv_config(field1157)
            self.newline()
            field1158 = unwrapped_fields1155[2]
            self.pretty_csv_columns(field1158)
            self.newline()
            field1159 = unwrapped_fields1155[3]
            self.pretty_csv_asof(field1159)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1167 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1167 is not None:
            assert flat1167 is not None
            self.write(flat1167)
            return None
        else:
            def _t1607(_dollar_dollar):
                if not len(_dollar_dollar.paths) == 0:
                    _t1608 = _dollar_dollar.paths
                else:
                    _t1608 = None
                if _dollar_dollar.inline_data.decode('utf-8') != "":
                    _t1609 = _dollar_dollar.inline_data.decode('utf-8')
                else:
                    _t1609 = None
                return (_t1608, _t1609,)
            _t1610 = _t1607(msg)
            fields1161 = _t1610
            assert fields1161 is not None
            unwrapped_fields1162 = fields1161
            self.write("(")
            self.write("csv_locator")
            self.indent_sexp()
            field1163 = unwrapped_fields1162[0]
            if field1163 is not None:
                self.newline()
                assert field1163 is not None
                opt_val1164 = field1163
                self.pretty_csv_locator_paths(opt_val1164)
            field1165 = unwrapped_fields1162[1]
            if field1165 is not None:
                self.newline()
                assert field1165 is not None
                opt_val1166 = field1165
                self.pretty_csv_locator_inline_data(opt_val1166)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1171 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1171 is not None:
            assert flat1171 is not None
            self.write(flat1171)
            return None
        else:
            fields1168 = msg
            self.write("(")
            self.write("paths")
            self.indent_sexp()
            if not len(fields1168) == 0:
                self.newline()
                for i1170, elem1169 in enumerate(fields1168):
                    if (i1170 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1169))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1173 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1173 is not None:
            assert flat1173 is not None
            self.write(flat1173)
            return None
        else:
            fields1172 = msg
            self.write("(")
            self.write("inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1172))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1176 = self._try_flat(msg, self.pretty_csv_config)
        if flat1176 is not None:
            assert flat1176 is not None
            self.write(flat1176)
            return None
        else:
            def _t1611(_dollar_dollar):
                _t1612 = self.deconstruct_csv_config(_dollar_dollar)
                return _t1612
            _t1613 = _t1611(msg)
            fields1174 = _t1613
            assert fields1174 is not None
            unwrapped_fields1175 = fields1174
            self.write("(")
            self.write("csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1175)
            self.dedent()
            self.write(")")

    def pretty_csv_columns(self, msg: Sequence[logic_pb2.CSVColumn]):
        flat1180 = self._try_flat(msg, self.pretty_csv_columns)
        if flat1180 is not None:
            assert flat1180 is not None
            self.write(flat1180)
            return None
        else:
            fields1177 = msg
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(fields1177) == 0:
                self.newline()
                for i1179, elem1178 in enumerate(fields1177):
                    if (i1179 > 0):
                        self.newline()
                    self.pretty_csv_column(elem1178)
            self.dedent()
            self.write(")")

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn):
        flat1188 = self._try_flat(msg, self.pretty_csv_column)
        if flat1188 is not None:
            assert flat1188 is not None
            self.write(flat1188)
            return None
        else:
            def _t1614(_dollar_dollar):
                return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
            _t1615 = _t1614(msg)
            fields1181 = _t1615
            assert fields1181 is not None
            unwrapped_fields1182 = fields1181
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field1183 = unwrapped_fields1182[0]
            self.write(self.format_string_value(field1183))
            self.newline()
            field1184 = unwrapped_fields1182[1]
            self.pretty_relation_id(field1184)
            self.newline()
            self.write("[")
            field1185 = unwrapped_fields1182[2]
            for i1187, elem1186 in enumerate(field1185):
                if (i1187 > 0):
                    self.newline()
                self.pretty_type(elem1186)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_csv_asof(self, msg: str):
        flat1190 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1190 is not None:
            assert flat1190 is not None
            self.write(flat1190)
            return None
        else:
            fields1189 = msg
            self.write("(")
            self.write("asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1189))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1193 = self._try_flat(msg, self.pretty_undefine)
        if flat1193 is not None:
            assert flat1193 is not None
            self.write(flat1193)
            return None
        else:
            def _t1616(_dollar_dollar):
                return _dollar_dollar.fragment_id
            _t1617 = _t1616(msg)
            fields1191 = _t1617
            assert fields1191 is not None
            unwrapped_fields1192 = fields1191
            self.write("(")
            self.write("undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1192)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1198 = self._try_flat(msg, self.pretty_context)
        if flat1198 is not None:
            assert flat1198 is not None
            self.write(flat1198)
            return None
        else:
            def _t1618(_dollar_dollar):
                return _dollar_dollar.relations
            _t1619 = _t1618(msg)
            fields1194 = _t1619
            assert fields1194 is not None
            unwrapped_fields1195 = fields1194
            self.write("(")
            self.write("context")
            self.indent_sexp()
            if not len(unwrapped_fields1195) == 0:
                self.newline()
                for i1197, elem1196 in enumerate(unwrapped_fields1195):
                    if (i1197 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1196)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1203 = self._try_flat(msg, self.pretty_snapshot)
        if flat1203 is not None:
            assert flat1203 is not None
            self.write(flat1203)
            return None
        else:
            def _t1620(_dollar_dollar):
                return (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            _t1621 = _t1620(msg)
            fields1199 = _t1621
            assert fields1199 is not None
            unwrapped_fields1200 = fields1199
            self.write("(")
            self.write("snapshot")
            self.indent_sexp()
            self.newline()
            field1201 = unwrapped_fields1200[0]
            self.pretty_rel_edb_path(field1201)
            self.newline()
            field1202 = unwrapped_fields1200[1]
            self.pretty_relation_id(field1202)
            self.dedent()
            self.write(")")

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1207 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1207 is not None:
            assert flat1207 is not None
            self.write(flat1207)
            return None
        else:
            fields1204 = msg
            self.write("(")
            self.write("reads")
            self.indent_sexp()
            if not len(fields1204) == 0:
                self.newline()
                for i1206, elem1205 in enumerate(fields1204):
                    if (i1206 > 0):
                        self.newline()
                    self.pretty_read(elem1205)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1218 = self._try_flat(msg, self.pretty_read)
        if flat1218 is not None:
            assert flat1218 is not None
            self.write(flat1218)
            return None
        else:
            def _t1622(_dollar_dollar):
                if _dollar_dollar.HasField("demand"):
                    _t1623 = _dollar_dollar.demand
                else:
                    _t1623 = None
                return _t1623
            _t1624 = _t1622(msg)
            deconstruct_result1216 = _t1624
            if deconstruct_result1216 is not None:
                assert deconstruct_result1216 is not None
                unwrapped1217 = deconstruct_result1216
                self.pretty_demand(unwrapped1217)
            else:
                def _t1625(_dollar_dollar):
                    if _dollar_dollar.HasField("output"):
                        _t1626 = _dollar_dollar.output
                    else:
                        _t1626 = None
                    return _t1626
                _t1627 = _t1625(msg)
                deconstruct_result1214 = _t1627
                if deconstruct_result1214 is not None:
                    assert deconstruct_result1214 is not None
                    unwrapped1215 = deconstruct_result1214
                    self.pretty_output(unwrapped1215)
                else:
                    def _t1628(_dollar_dollar):
                        if _dollar_dollar.HasField("what_if"):
                            _t1629 = _dollar_dollar.what_if
                        else:
                            _t1629 = None
                        return _t1629
                    _t1630 = _t1628(msg)
                    deconstruct_result1212 = _t1630
                    if deconstruct_result1212 is not None:
                        assert deconstruct_result1212 is not None
                        unwrapped1213 = deconstruct_result1212
                        self.pretty_what_if(unwrapped1213)
                    else:
                        def _t1631(_dollar_dollar):
                            if _dollar_dollar.HasField("abort"):
                                _t1632 = _dollar_dollar.abort
                            else:
                                _t1632 = None
                            return _t1632
                        _t1633 = _t1631(msg)
                        deconstruct_result1210 = _t1633
                        if deconstruct_result1210 is not None:
                            assert deconstruct_result1210 is not None
                            unwrapped1211 = deconstruct_result1210
                            self.pretty_abort(unwrapped1211)
                        else:
                            def _t1634(_dollar_dollar):
                                if _dollar_dollar.HasField("export"):
                                    _t1635 = _dollar_dollar.export
                                else:
                                    _t1635 = None
                                return _t1635
                            _t1636 = _t1634(msg)
                            deconstruct_result1208 = _t1636
                            if deconstruct_result1208 is not None:
                                assert deconstruct_result1208 is not None
                                unwrapped1209 = deconstruct_result1208
                                self.pretty_export(unwrapped1209)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1221 = self._try_flat(msg, self.pretty_demand)
        if flat1221 is not None:
            assert flat1221 is not None
            self.write(flat1221)
            return None
        else:
            def _t1637(_dollar_dollar):
                return _dollar_dollar.relation_id
            _t1638 = _t1637(msg)
            fields1219 = _t1638
            assert fields1219 is not None
            unwrapped_fields1220 = fields1219
            self.write("(")
            self.write("demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1220)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1226 = self._try_flat(msg, self.pretty_output)
        if flat1226 is not None:
            assert flat1226 is not None
            self.write(flat1226)
            return None
        else:
            def _t1639(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_id,)
            _t1640 = _t1639(msg)
            fields1222 = _t1640
            assert fields1222 is not None
            unwrapped_fields1223 = fields1222
            self.write("(")
            self.write("output")
            self.indent_sexp()
            self.newline()
            field1224 = unwrapped_fields1223[0]
            self.pretty_name(field1224)
            self.newline()
            field1225 = unwrapped_fields1223[1]
            self.pretty_relation_id(field1225)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1231 = self._try_flat(msg, self.pretty_what_if)
        if flat1231 is not None:
            assert flat1231 is not None
            self.write(flat1231)
            return None
        else:
            def _t1641(_dollar_dollar):
                return (_dollar_dollar.branch, _dollar_dollar.epoch,)
            _t1642 = _t1641(msg)
            fields1227 = _t1642
            assert fields1227 is not None
            unwrapped_fields1228 = fields1227
            self.write("(")
            self.write("what_if")
            self.indent_sexp()
            self.newline()
            field1229 = unwrapped_fields1228[0]
            self.pretty_name(field1229)
            self.newline()
            field1230 = unwrapped_fields1228[1]
            self.pretty_epoch(field1230)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1237 = self._try_flat(msg, self.pretty_abort)
        if flat1237 is not None:
            assert flat1237 is not None
            self.write(flat1237)
            return None
        else:
            def _t1643(_dollar_dollar):
                if _dollar_dollar.name != "abort":
                    _t1644 = _dollar_dollar.name
                else:
                    _t1644 = None
                return (_t1644, _dollar_dollar.relation_id,)
            _t1645 = _t1643(msg)
            fields1232 = _t1645
            assert fields1232 is not None
            unwrapped_fields1233 = fields1232
            self.write("(")
            self.write("abort")
            self.indent_sexp()
            field1234 = unwrapped_fields1233[0]
            if field1234 is not None:
                self.newline()
                assert field1234 is not None
                opt_val1235 = field1234
                self.pretty_name(opt_val1235)
            self.newline()
            field1236 = unwrapped_fields1233[1]
            self.pretty_relation_id(field1236)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1240 = self._try_flat(msg, self.pretty_export)
        if flat1240 is not None:
            assert flat1240 is not None
            self.write(flat1240)
            return None
        else:
            def _t1646(_dollar_dollar):
                return _dollar_dollar.csv_config
            _t1647 = _t1646(msg)
            fields1238 = _t1647
            assert fields1238 is not None
            unwrapped_fields1239 = fields1238
            self.write("(")
            self.write("export")
            self.indent_sexp()
            self.newline()
            self.pretty_export_csv_config(unwrapped_fields1239)
            self.dedent()
            self.write(")")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1246 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1246 is not None:
            assert flat1246 is not None
            self.write(flat1246)
            return None
        else:
            def _t1648(_dollar_dollar):
                _t1649 = self.deconstruct_export_csv_config(_dollar_dollar)
                return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1649,)
            _t1650 = _t1648(msg)
            fields1241 = _t1650
            assert fields1241 is not None
            unwrapped_fields1242 = fields1241
            self.write("(")
            self.write("export_csv_config")
            self.indent_sexp()
            self.newline()
            field1243 = unwrapped_fields1242[0]
            self.pretty_export_csv_path(field1243)
            self.newline()
            field1244 = unwrapped_fields1242[1]
            self.pretty_export_csv_columns(field1244)
            self.newline()
            field1245 = unwrapped_fields1242[2]
            self.pretty_config_dict(field1245)
            self.dedent()
            self.write(")")

    def pretty_export_csv_path(self, msg: str):
        flat1248 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1248 is not None:
            assert flat1248 is not None
            self.write(flat1248)
            return None
        else:
            fields1247 = msg
            self.write("(")
            self.write("path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1247))
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1252 = self._try_flat(msg, self.pretty_export_csv_columns)
        if flat1252 is not None:
            assert flat1252 is not None
            self.write(flat1252)
            return None
        else:
            fields1249 = msg
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(fields1249) == 0:
                self.newline()
                for i1251, elem1250 in enumerate(fields1249):
                    if (i1251 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1250)
            self.dedent()
            self.write(")")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1257 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1257 is not None:
            assert flat1257 is not None
            self.write(flat1257)
            return None
        else:
            def _t1651(_dollar_dollar):
                return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            _t1652 = _t1651(msg)
            fields1253 = _t1652
            assert fields1253 is not None
            unwrapped_fields1254 = fields1253
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field1255 = unwrapped_fields1254[0]
            self.write(self.format_string_value(field1255))
            self.newline()
            field1256 = unwrapped_fields1254[1]
            self.pretty_relation_id(field1256)
            self.dedent()
            self.write(")")




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
