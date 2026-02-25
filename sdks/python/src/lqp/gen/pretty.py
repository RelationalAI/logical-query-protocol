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
        _t1689 = logic_pb2.Value(int_value=int(v))
        return _t1689

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1690 = logic_pb2.Value(int_value=v)
        return _t1690

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1691 = logic_pb2.Value(float_value=v)
        return _t1691

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1692 = logic_pb2.Value(string_value=v)
        return _t1692

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1693 = logic_pb2.Value(boolean_value=v)
        return _t1693

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1694 = logic_pb2.Value(uint128_value=v)
        return _t1694

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1695 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1695,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1696 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1696,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1697 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1697,))
        _t1698 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1698,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1699 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1699,))
        _t1700 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1700,))
        if msg.new_line != "":
            _t1701 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1701,))
        _t1702 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1702,))
        _t1703 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1703,))
        _t1704 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1704,))
        if msg.comment != "":
            _t1705 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1705,))
        for missing_string in msg.missing_strings:
            _t1706 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1706,))
        _t1707 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1707,))
        _t1708 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1708,))
        _t1709 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1709,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1710 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1710,))
        _t1711 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1711,))
        _t1712 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1712,))
        _t1713 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1713,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1714 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1714,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1715 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1715,))
        _t1716 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1716,))
        _t1717 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1717,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1718 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1718,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1719 = self._make_value_string(msg.compression)
            result.append(("compression", _t1719,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1720 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1720,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1721 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1721,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1722 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1722,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1723 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1723,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1724 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1724,))
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
            _t1725 = None
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
        flat651 = self._try_flat(msg, self.pretty_transaction)
        if flat651 is not None:
            assert flat651 is not None
            self.write(flat651)
            return None
        else:
            def _t1284(_dollar_dollar):
                if _dollar_dollar.HasField("configure"):
                    _t1285 = _dollar_dollar.configure
                else:
                    _t1285 = None
                if _dollar_dollar.HasField("sync"):
                    _t1286 = _dollar_dollar.sync
                else:
                    _t1286 = None
                return (_t1285, _t1286, _dollar_dollar.epochs,)
            _t1287 = _t1284(msg)
            fields642 = _t1287
            assert fields642 is not None
            unwrapped_fields643 = fields642
            self.write("(")
            self.write("transaction")
            self.indent_sexp()
            field644 = unwrapped_fields643[0]
            if field644 is not None:
                self.newline()
                assert field644 is not None
                opt_val645 = field644
                self.pretty_configure(opt_val645)
            field646 = unwrapped_fields643[1]
            if field646 is not None:
                self.newline()
                assert field646 is not None
                opt_val647 = field646
                self.pretty_sync(opt_val647)
            field648 = unwrapped_fields643[2]
            if not len(field648) == 0:
                self.newline()
                for i650, elem649 in enumerate(field648):
                    if (i650 > 0):
                        self.newline()
                    self.pretty_epoch(elem649)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat654 = self._try_flat(msg, self.pretty_configure)
        if flat654 is not None:
            assert flat654 is not None
            self.write(flat654)
            return None
        else:
            def _t1288(_dollar_dollar):
                _t1289 = self.deconstruct_configure(_dollar_dollar)
                return _t1289
            _t1290 = _t1288(msg)
            fields652 = _t1290
            assert fields652 is not None
            unwrapped_fields653 = fields652
            self.write("(")
            self.write("configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields653)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat658 = self._try_flat(msg, self.pretty_config_dict)
        if flat658 is not None:
            assert flat658 is not None
            self.write(flat658)
            return None
        else:
            fields655 = msg
            self.write("{")
            self.indent()
            if not len(fields655) == 0:
                self.newline()
                for i657, elem656 in enumerate(fields655):
                    if (i657 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem656)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat663 = self._try_flat(msg, self.pretty_config_key_value)
        if flat663 is not None:
            assert flat663 is not None
            self.write(flat663)
            return None
        else:
            def _t1291(_dollar_dollar):
                return (_dollar_dollar[0], _dollar_dollar[1],)
            _t1292 = _t1291(msg)
            fields659 = _t1292
            assert fields659 is not None
            unwrapped_fields660 = fields659
            self.write(":")
            field661 = unwrapped_fields660[0]
            self.write(field661)
            self.write(" ")
            field662 = unwrapped_fields660[1]
            self.pretty_value(field662)

    def pretty_value(self, msg: logic_pb2.Value):
        flat683 = self._try_flat(msg, self.pretty_value)
        if flat683 is not None:
            assert flat683 is not None
            self.write(flat683)
            return None
        else:
            def _t1293(_dollar_dollar):
                if _dollar_dollar.HasField("date_value"):
                    _t1294 = _dollar_dollar.date_value
                else:
                    _t1294 = None
                return _t1294
            _t1295 = _t1293(msg)
            deconstruct_result681 = _t1295
            if deconstruct_result681 is not None:
                assert deconstruct_result681 is not None
                unwrapped682 = deconstruct_result681
                self.pretty_date(unwrapped682)
            else:
                def _t1296(_dollar_dollar):
                    if _dollar_dollar.HasField("datetime_value"):
                        _t1297 = _dollar_dollar.datetime_value
                    else:
                        _t1297 = None
                    return _t1297
                _t1298 = _t1296(msg)
                deconstruct_result679 = _t1298
                if deconstruct_result679 is not None:
                    assert deconstruct_result679 is not None
                    unwrapped680 = deconstruct_result679
                    self.pretty_datetime(unwrapped680)
                else:
                    def _t1299(_dollar_dollar):
                        if _dollar_dollar.HasField("string_value"):
                            _t1300 = _dollar_dollar.string_value
                        else:
                            _t1300 = None
                        return _t1300
                    _t1301 = _t1299(msg)
                    deconstruct_result677 = _t1301
                    if deconstruct_result677 is not None:
                        assert deconstruct_result677 is not None
                        unwrapped678 = deconstruct_result677
                        self.write(self.format_string_value(unwrapped678))
                    else:
                        def _t1302(_dollar_dollar):
                            if _dollar_dollar.HasField("int_value"):
                                _t1303 = _dollar_dollar.int_value
                            else:
                                _t1303 = None
                            return _t1303
                        _t1304 = _t1302(msg)
                        deconstruct_result675 = _t1304
                        if deconstruct_result675 is not None:
                            assert deconstruct_result675 is not None
                            unwrapped676 = deconstruct_result675
                            self.write(str(unwrapped676))
                        else:
                            def _t1305(_dollar_dollar):
                                if _dollar_dollar.HasField("float_value"):
                                    _t1306 = _dollar_dollar.float_value
                                else:
                                    _t1306 = None
                                return _t1306
                            _t1307 = _t1305(msg)
                            deconstruct_result673 = _t1307
                            if deconstruct_result673 is not None:
                                assert deconstruct_result673 is not None
                                unwrapped674 = deconstruct_result673
                                self.write(str(unwrapped674))
                            else:
                                def _t1308(_dollar_dollar):
                                    if _dollar_dollar.HasField("uint128_value"):
                                        _t1309 = _dollar_dollar.uint128_value
                                    else:
                                        _t1309 = None
                                    return _t1309
                                _t1310 = _t1308(msg)
                                deconstruct_result671 = _t1310
                                if deconstruct_result671 is not None:
                                    assert deconstruct_result671 is not None
                                    unwrapped672 = deconstruct_result671
                                    self.write(self.format_uint128(unwrapped672))
                                else:
                                    def _t1311(_dollar_dollar):
                                        if _dollar_dollar.HasField("int128_value"):
                                            _t1312 = _dollar_dollar.int128_value
                                        else:
                                            _t1312 = None
                                        return _t1312
                                    _t1313 = _t1311(msg)
                                    deconstruct_result669 = _t1313
                                    if deconstruct_result669 is not None:
                                        assert deconstruct_result669 is not None
                                        unwrapped670 = deconstruct_result669
                                        self.write(self.format_int128(unwrapped670))
                                    else:
                                        def _t1314(_dollar_dollar):
                                            if _dollar_dollar.HasField("decimal_value"):
                                                _t1315 = _dollar_dollar.decimal_value
                                            else:
                                                _t1315 = None
                                            return _t1315
                                        _t1316 = _t1314(msg)
                                        deconstruct_result667 = _t1316
                                        if deconstruct_result667 is not None:
                                            assert deconstruct_result667 is not None
                                            unwrapped668 = deconstruct_result667
                                            self.write(self.format_decimal(unwrapped668))
                                        else:
                                            def _t1317(_dollar_dollar):
                                                if _dollar_dollar.HasField("boolean_value"):
                                                    _t1318 = _dollar_dollar.boolean_value
                                                else:
                                                    _t1318 = None
                                                return _t1318
                                            _t1319 = _t1317(msg)
                                            deconstruct_result665 = _t1319
                                            if deconstruct_result665 is not None:
                                                assert deconstruct_result665 is not None
                                                unwrapped666 = deconstruct_result665
                                                self.pretty_boolean_value(unwrapped666)
                                            else:
                                                fields664 = msg
                                                self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat689 = self._try_flat(msg, self.pretty_date)
        if flat689 is not None:
            assert flat689 is not None
            self.write(flat689)
            return None
        else:
            def _t1320(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            _t1321 = _t1320(msg)
            fields684 = _t1321
            assert fields684 is not None
            unwrapped_fields685 = fields684
            self.write("(")
            self.write("date")
            self.indent_sexp()
            self.newline()
            field686 = unwrapped_fields685[0]
            self.write(str(field686))
            self.newline()
            field687 = unwrapped_fields685[1]
            self.write(str(field687))
            self.newline()
            field688 = unwrapped_fields685[2]
            self.write(str(field688))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat700 = self._try_flat(msg, self.pretty_datetime)
        if flat700 is not None:
            assert flat700 is not None
            self.write(flat700)
            return None
        else:
            def _t1322(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            _t1323 = _t1322(msg)
            fields690 = _t1323
            assert fields690 is not None
            unwrapped_fields691 = fields690
            self.write("(")
            self.write("datetime")
            self.indent_sexp()
            self.newline()
            field692 = unwrapped_fields691[0]
            self.write(str(field692))
            self.newline()
            field693 = unwrapped_fields691[1]
            self.write(str(field693))
            self.newline()
            field694 = unwrapped_fields691[2]
            self.write(str(field694))
            self.newline()
            field695 = unwrapped_fields691[3]
            self.write(str(field695))
            self.newline()
            field696 = unwrapped_fields691[4]
            self.write(str(field696))
            self.newline()
            field697 = unwrapped_fields691[5]
            self.write(str(field697))
            field698 = unwrapped_fields691[6]
            if field698 is not None:
                self.newline()
                assert field698 is not None
                opt_val699 = field698
                self.write(str(opt_val699))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        def _t1324(_dollar_dollar):
            if _dollar_dollar:
                _t1325 = ()
            else:
                _t1325 = None
            return _t1325
        _t1326 = _t1324(msg)
        deconstruct_result703 = _t1326
        if deconstruct_result703 is not None:
            assert deconstruct_result703 is not None
            unwrapped704 = deconstruct_result703
            self.write("true")
        else:
            def _t1327(_dollar_dollar):
                if not _dollar_dollar:
                    _t1328 = ()
                else:
                    _t1328 = None
                return _t1328
            _t1329 = _t1327(msg)
            deconstruct_result701 = _t1329
            if deconstruct_result701 is not None:
                assert deconstruct_result701 is not None
                unwrapped702 = deconstruct_result701
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat709 = self._try_flat(msg, self.pretty_sync)
        if flat709 is not None:
            assert flat709 is not None
            self.write(flat709)
            return None
        else:
            def _t1330(_dollar_dollar):
                return _dollar_dollar.fragments
            _t1331 = _t1330(msg)
            fields705 = _t1331
            assert fields705 is not None
            unwrapped_fields706 = fields705
            self.write("(")
            self.write("sync")
            self.indent_sexp()
            if not len(unwrapped_fields706) == 0:
                self.newline()
                for i708, elem707 in enumerate(unwrapped_fields706):
                    if (i708 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem707)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat712 = self._try_flat(msg, self.pretty_fragment_id)
        if flat712 is not None:
            assert flat712 is not None
            self.write(flat712)
            return None
        else:
            def _t1332(_dollar_dollar):
                return self.fragment_id_to_string(_dollar_dollar)
            _t1333 = _t1332(msg)
            fields710 = _t1333
            assert fields710 is not None
            unwrapped_fields711 = fields710
            self.write(":")
            self.write(unwrapped_fields711)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat719 = self._try_flat(msg, self.pretty_epoch)
        if flat719 is not None:
            assert flat719 is not None
            self.write(flat719)
            return None
        else:
            def _t1334(_dollar_dollar):
                if not len(_dollar_dollar.writes) == 0:
                    _t1335 = _dollar_dollar.writes
                else:
                    _t1335 = None
                if not len(_dollar_dollar.reads) == 0:
                    _t1336 = _dollar_dollar.reads
                else:
                    _t1336 = None
                return (_t1335, _t1336,)
            _t1337 = _t1334(msg)
            fields713 = _t1337
            assert fields713 is not None
            unwrapped_fields714 = fields713
            self.write("(")
            self.write("epoch")
            self.indent_sexp()
            field715 = unwrapped_fields714[0]
            if field715 is not None:
                self.newline()
                assert field715 is not None
                opt_val716 = field715
                self.pretty_epoch_writes(opt_val716)
            field717 = unwrapped_fields714[1]
            if field717 is not None:
                self.newline()
                assert field717 is not None
                opt_val718 = field717
                self.pretty_epoch_reads(opt_val718)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat723 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat723 is not None:
            assert flat723 is not None
            self.write(flat723)
            return None
        else:
            fields720 = msg
            self.write("(")
            self.write("writes")
            self.indent_sexp()
            if not len(fields720) == 0:
                self.newline()
                for i722, elem721 in enumerate(fields720):
                    if (i722 > 0):
                        self.newline()
                    self.pretty_write(elem721)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat732 = self._try_flat(msg, self.pretty_write)
        if flat732 is not None:
            assert flat732 is not None
            self.write(flat732)
            return None
        else:
            def _t1338(_dollar_dollar):
                if _dollar_dollar.HasField("define"):
                    _t1339 = _dollar_dollar.define
                else:
                    _t1339 = None
                return _t1339
            _t1340 = _t1338(msg)
            deconstruct_result730 = _t1340
            if deconstruct_result730 is not None:
                assert deconstruct_result730 is not None
                unwrapped731 = deconstruct_result730
                self.pretty_define(unwrapped731)
            else:
                def _t1341(_dollar_dollar):
                    if _dollar_dollar.HasField("undefine"):
                        _t1342 = _dollar_dollar.undefine
                    else:
                        _t1342 = None
                    return _t1342
                _t1343 = _t1341(msg)
                deconstruct_result728 = _t1343
                if deconstruct_result728 is not None:
                    assert deconstruct_result728 is not None
                    unwrapped729 = deconstruct_result728
                    self.pretty_undefine(unwrapped729)
                else:
                    def _t1344(_dollar_dollar):
                        if _dollar_dollar.HasField("context"):
                            _t1345 = _dollar_dollar.context
                        else:
                            _t1345 = None
                        return _t1345
                    _t1346 = _t1344(msg)
                    deconstruct_result726 = _t1346
                    if deconstruct_result726 is not None:
                        assert deconstruct_result726 is not None
                        unwrapped727 = deconstruct_result726
                        self.pretty_context(unwrapped727)
                    else:
                        def _t1347(_dollar_dollar):
                            if _dollar_dollar.HasField("snapshot"):
                                _t1348 = _dollar_dollar.snapshot
                            else:
                                _t1348 = None
                            return _t1348
                        _t1349 = _t1347(msg)
                        deconstruct_result724 = _t1349
                        if deconstruct_result724 is not None:
                            assert deconstruct_result724 is not None
                            unwrapped725 = deconstruct_result724
                            self.pretty_snapshot(unwrapped725)
                        else:
                            raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat735 = self._try_flat(msg, self.pretty_define)
        if flat735 is not None:
            assert flat735 is not None
            self.write(flat735)
            return None
        else:
            def _t1350(_dollar_dollar):
                return _dollar_dollar.fragment
            _t1351 = _t1350(msg)
            fields733 = _t1351
            assert fields733 is not None
            unwrapped_fields734 = fields733
            self.write("(")
            self.write("define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields734)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat742 = self._try_flat(msg, self.pretty_fragment)
        if flat742 is not None:
            assert flat742 is not None
            self.write(flat742)
            return None
        else:
            def _t1352(_dollar_dollar):
                self.start_pretty_fragment(_dollar_dollar)
                return (_dollar_dollar.id, _dollar_dollar.declarations,)
            _t1353 = _t1352(msg)
            fields736 = _t1353
            assert fields736 is not None
            unwrapped_fields737 = fields736
            self.write("(")
            self.write("fragment")
            self.indent_sexp()
            self.newline()
            field738 = unwrapped_fields737[0]
            self.pretty_new_fragment_id(field738)
            field739 = unwrapped_fields737[1]
            if not len(field739) == 0:
                self.newline()
                for i741, elem740 in enumerate(field739):
                    if (i741 > 0):
                        self.newline()
                    self.pretty_declaration(elem740)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat744 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat744 is not None:
            assert flat744 is not None
            self.write(flat744)
            return None
        else:
            fields743 = msg
            self.pretty_fragment_id(fields743)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat753 = self._try_flat(msg, self.pretty_declaration)
        if flat753 is not None:
            assert flat753 is not None
            self.write(flat753)
            return None
        else:
            def _t1354(_dollar_dollar):
                if _dollar_dollar.HasField("def"):
                    _t1355 = getattr(_dollar_dollar, 'def')
                else:
                    _t1355 = None
                return _t1355
            _t1356 = _t1354(msg)
            deconstruct_result751 = _t1356
            if deconstruct_result751 is not None:
                assert deconstruct_result751 is not None
                unwrapped752 = deconstruct_result751
                self.pretty_def(unwrapped752)
            else:
                def _t1357(_dollar_dollar):
                    if _dollar_dollar.HasField("algorithm"):
                        _t1358 = _dollar_dollar.algorithm
                    else:
                        _t1358 = None
                    return _t1358
                _t1359 = _t1357(msg)
                deconstruct_result749 = _t1359
                if deconstruct_result749 is not None:
                    assert deconstruct_result749 is not None
                    unwrapped750 = deconstruct_result749
                    self.pretty_algorithm(unwrapped750)
                else:
                    def _t1360(_dollar_dollar):
                        if _dollar_dollar.HasField("constraint"):
                            _t1361 = _dollar_dollar.constraint
                        else:
                            _t1361 = None
                        return _t1361
                    _t1362 = _t1360(msg)
                    deconstruct_result747 = _t1362
                    if deconstruct_result747 is not None:
                        assert deconstruct_result747 is not None
                        unwrapped748 = deconstruct_result747
                        self.pretty_constraint(unwrapped748)
                    else:
                        def _t1363(_dollar_dollar):
                            if _dollar_dollar.HasField("data"):
                                _t1364 = _dollar_dollar.data
                            else:
                                _t1364 = None
                            return _t1364
                        _t1365 = _t1363(msg)
                        deconstruct_result745 = _t1365
                        if deconstruct_result745 is not None:
                            assert deconstruct_result745 is not None
                            unwrapped746 = deconstruct_result745
                            self.pretty_data(unwrapped746)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat760 = self._try_flat(msg, self.pretty_def)
        if flat760 is not None:
            assert flat760 is not None
            self.write(flat760)
            return None
        else:
            def _t1366(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1367 = _dollar_dollar.attrs
                else:
                    _t1367 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1367,)
            _t1368 = _t1366(msg)
            fields754 = _t1368
            assert fields754 is not None
            unwrapped_fields755 = fields754
            self.write("(")
            self.write("def")
            self.indent_sexp()
            self.newline()
            field756 = unwrapped_fields755[0]
            self.pretty_relation_id(field756)
            self.newline()
            field757 = unwrapped_fields755[1]
            self.pretty_abstraction(field757)
            field758 = unwrapped_fields755[2]
            if field758 is not None:
                self.newline()
                assert field758 is not None
                opt_val759 = field758
                self.pretty_attrs(opt_val759)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat765 = self._try_flat(msg, self.pretty_relation_id)
        if flat765 is not None:
            assert flat765 is not None
            self.write(flat765)
            return None
        else:
            def _t1369(_dollar_dollar):
                if self.relation_id_to_string(_dollar_dollar) is not None:
                    _t1371 = self.deconstruct_relation_id_string(_dollar_dollar)
                    _t1370 = _t1371
                else:
                    _t1370 = None
                return _t1370
            _t1372 = _t1369(msg)
            deconstruct_result763 = _t1372
            if deconstruct_result763 is not None:
                assert deconstruct_result763 is not None
                unwrapped764 = deconstruct_result763
                self.write(":")
                self.write(unwrapped764)
            else:
                def _t1373(_dollar_dollar):
                    _t1374 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                    return _t1374
                _t1375 = _t1373(msg)
                deconstruct_result761 = _t1375
                if deconstruct_result761 is not None:
                    assert deconstruct_result761 is not None
                    unwrapped762 = deconstruct_result761
                    self.write(self.format_uint128(unwrapped762))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat770 = self._try_flat(msg, self.pretty_abstraction)
        if flat770 is not None:
            assert flat770 is not None
            self.write(flat770)
            return None
        else:
            def _t1376(_dollar_dollar):
                _t1377 = self.deconstruct_bindings(_dollar_dollar)
                return (_t1377, _dollar_dollar.value,)
            _t1378 = _t1376(msg)
            fields766 = _t1378
            assert fields766 is not None
            unwrapped_fields767 = fields766
            self.write("(")
            self.indent()
            field768 = unwrapped_fields767[0]
            self.pretty_bindings(field768)
            self.newline()
            field769 = unwrapped_fields767[1]
            self.pretty_formula(field769)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat778 = self._try_flat(msg, self.pretty_bindings)
        if flat778 is not None:
            assert flat778 is not None
            self.write(flat778)
            return None
        else:
            def _t1379(_dollar_dollar):
                if not len(_dollar_dollar[1]) == 0:
                    _t1380 = _dollar_dollar[1]
                else:
                    _t1380 = None
                return (_dollar_dollar[0], _t1380,)
            _t1381 = _t1379(msg)
            fields771 = _t1381
            assert fields771 is not None
            unwrapped_fields772 = fields771
            self.write("[")
            self.indent()
            field773 = unwrapped_fields772[0]
            for i775, elem774 in enumerate(field773):
                if (i775 > 0):
                    self.newline()
                self.pretty_binding(elem774)
            field776 = unwrapped_fields772[1]
            if field776 is not None:
                self.newline()
                assert field776 is not None
                opt_val777 = field776
                self.pretty_value_bindings(opt_val777)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat783 = self._try_flat(msg, self.pretty_binding)
        if flat783 is not None:
            assert flat783 is not None
            self.write(flat783)
            return None
        else:
            def _t1382(_dollar_dollar):
                return (_dollar_dollar.var.name, _dollar_dollar.type,)
            _t1383 = _t1382(msg)
            fields779 = _t1383
            assert fields779 is not None
            unwrapped_fields780 = fields779
            field781 = unwrapped_fields780[0]
            self.write(field781)
            self.write("::")
            field782 = unwrapped_fields780[1]
            self.pretty_type(field782)

    def pretty_type(self, msg: logic_pb2.Type):
        flat806 = self._try_flat(msg, self.pretty_type)
        if flat806 is not None:
            assert flat806 is not None
            self.write(flat806)
            return None
        else:
            def _t1384(_dollar_dollar):
                if _dollar_dollar.HasField("unspecified_type"):
                    _t1385 = _dollar_dollar.unspecified_type
                else:
                    _t1385 = None
                return _t1385
            _t1386 = _t1384(msg)
            deconstruct_result804 = _t1386
            if deconstruct_result804 is not None:
                assert deconstruct_result804 is not None
                unwrapped805 = deconstruct_result804
                self.pretty_unspecified_type(unwrapped805)
            else:
                def _t1387(_dollar_dollar):
                    if _dollar_dollar.HasField("string_type"):
                        _t1388 = _dollar_dollar.string_type
                    else:
                        _t1388 = None
                    return _t1388
                _t1389 = _t1387(msg)
                deconstruct_result802 = _t1389
                if deconstruct_result802 is not None:
                    assert deconstruct_result802 is not None
                    unwrapped803 = deconstruct_result802
                    self.pretty_string_type(unwrapped803)
                else:
                    def _t1390(_dollar_dollar):
                        if _dollar_dollar.HasField("int_type"):
                            _t1391 = _dollar_dollar.int_type
                        else:
                            _t1391 = None
                        return _t1391
                    _t1392 = _t1390(msg)
                    deconstruct_result800 = _t1392
                    if deconstruct_result800 is not None:
                        assert deconstruct_result800 is not None
                        unwrapped801 = deconstruct_result800
                        self.pretty_int_type(unwrapped801)
                    else:
                        def _t1393(_dollar_dollar):
                            if _dollar_dollar.HasField("float_type"):
                                _t1394 = _dollar_dollar.float_type
                            else:
                                _t1394 = None
                            return _t1394
                        _t1395 = _t1393(msg)
                        deconstruct_result798 = _t1395
                        if deconstruct_result798 is not None:
                            assert deconstruct_result798 is not None
                            unwrapped799 = deconstruct_result798
                            self.pretty_float_type(unwrapped799)
                        else:
                            def _t1396(_dollar_dollar):
                                if _dollar_dollar.HasField("uint128_type"):
                                    _t1397 = _dollar_dollar.uint128_type
                                else:
                                    _t1397 = None
                                return _t1397
                            _t1398 = _t1396(msg)
                            deconstruct_result796 = _t1398
                            if deconstruct_result796 is not None:
                                assert deconstruct_result796 is not None
                                unwrapped797 = deconstruct_result796
                                self.pretty_uint128_type(unwrapped797)
                            else:
                                def _t1399(_dollar_dollar):
                                    if _dollar_dollar.HasField("int128_type"):
                                        _t1400 = _dollar_dollar.int128_type
                                    else:
                                        _t1400 = None
                                    return _t1400
                                _t1401 = _t1399(msg)
                                deconstruct_result794 = _t1401
                                if deconstruct_result794 is not None:
                                    assert deconstruct_result794 is not None
                                    unwrapped795 = deconstruct_result794
                                    self.pretty_int128_type(unwrapped795)
                                else:
                                    def _t1402(_dollar_dollar):
                                        if _dollar_dollar.HasField("date_type"):
                                            _t1403 = _dollar_dollar.date_type
                                        else:
                                            _t1403 = None
                                        return _t1403
                                    _t1404 = _t1402(msg)
                                    deconstruct_result792 = _t1404
                                    if deconstruct_result792 is not None:
                                        assert deconstruct_result792 is not None
                                        unwrapped793 = deconstruct_result792
                                        self.pretty_date_type(unwrapped793)
                                    else:
                                        def _t1405(_dollar_dollar):
                                            if _dollar_dollar.HasField("datetime_type"):
                                                _t1406 = _dollar_dollar.datetime_type
                                            else:
                                                _t1406 = None
                                            return _t1406
                                        _t1407 = _t1405(msg)
                                        deconstruct_result790 = _t1407
                                        if deconstruct_result790 is not None:
                                            assert deconstruct_result790 is not None
                                            unwrapped791 = deconstruct_result790
                                            self.pretty_datetime_type(unwrapped791)
                                        else:
                                            def _t1408(_dollar_dollar):
                                                if _dollar_dollar.HasField("missing_type"):
                                                    _t1409 = _dollar_dollar.missing_type
                                                else:
                                                    _t1409 = None
                                                return _t1409
                                            _t1410 = _t1408(msg)
                                            deconstruct_result788 = _t1410
                                            if deconstruct_result788 is not None:
                                                assert deconstruct_result788 is not None
                                                unwrapped789 = deconstruct_result788
                                                self.pretty_missing_type(unwrapped789)
                                            else:
                                                def _t1411(_dollar_dollar):
                                                    if _dollar_dollar.HasField("decimal_type"):
                                                        _t1412 = _dollar_dollar.decimal_type
                                                    else:
                                                        _t1412 = None
                                                    return _t1412
                                                _t1413 = _t1411(msg)
                                                deconstruct_result786 = _t1413
                                                if deconstruct_result786 is not None:
                                                    assert deconstruct_result786 is not None
                                                    unwrapped787 = deconstruct_result786
                                                    self.pretty_decimal_type(unwrapped787)
                                                else:
                                                    def _t1414(_dollar_dollar):
                                                        if _dollar_dollar.HasField("boolean_type"):
                                                            _t1415 = _dollar_dollar.boolean_type
                                                        else:
                                                            _t1415 = None
                                                        return _t1415
                                                    _t1416 = _t1414(msg)
                                                    deconstruct_result784 = _t1416
                                                    if deconstruct_result784 is not None:
                                                        assert deconstruct_result784 is not None
                                                        unwrapped785 = deconstruct_result784
                                                        self.pretty_boolean_type(unwrapped785)
                                                    else:
                                                        raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields807 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields808 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields809 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields810 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields811 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields812 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields813 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields814 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields815 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat820 = self._try_flat(msg, self.pretty_decimal_type)
        if flat820 is not None:
            assert flat820 is not None
            self.write(flat820)
            return None
        else:
            def _t1417(_dollar_dollar):
                return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            _t1418 = _t1417(msg)
            fields816 = _t1418
            assert fields816 is not None
            unwrapped_fields817 = fields816
            self.write("(")
            self.write("DECIMAL")
            self.indent_sexp()
            self.newline()
            field818 = unwrapped_fields817[0]
            self.write(str(field818))
            self.newline()
            field819 = unwrapped_fields817[1]
            self.write(str(field819))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields821 = msg
        self.write("BOOLEAN")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat825 = self._try_flat(msg, self.pretty_value_bindings)
        if flat825 is not None:
            assert flat825 is not None
            self.write(flat825)
            return None
        else:
            fields822 = msg
            self.write("|")
            if not len(fields822) == 0:
                self.write(" ")
                for i824, elem823 in enumerate(fields822):
                    if (i824 > 0):
                        self.newline()
                    self.pretty_binding(elem823)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat852 = self._try_flat(msg, self.pretty_formula)
        if flat852 is not None:
            assert flat852 is not None
            self.write(flat852)
            return None
        else:
            def _t1419(_dollar_dollar):
                if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                    _t1420 = _dollar_dollar.conjunction
                else:
                    _t1420 = None
                return _t1420
            _t1421 = _t1419(msg)
            deconstruct_result850 = _t1421
            if deconstruct_result850 is not None:
                assert deconstruct_result850 is not None
                unwrapped851 = deconstruct_result850
                self.pretty_true(unwrapped851)
            else:
                def _t1422(_dollar_dollar):
                    if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                        _t1423 = _dollar_dollar.disjunction
                    else:
                        _t1423 = None
                    return _t1423
                _t1424 = _t1422(msg)
                deconstruct_result848 = _t1424
                if deconstruct_result848 is not None:
                    assert deconstruct_result848 is not None
                    unwrapped849 = deconstruct_result848
                    self.pretty_false(unwrapped849)
                else:
                    def _t1425(_dollar_dollar):
                        if _dollar_dollar.HasField("exists"):
                            _t1426 = _dollar_dollar.exists
                        else:
                            _t1426 = None
                        return _t1426
                    _t1427 = _t1425(msg)
                    deconstruct_result846 = _t1427
                    if deconstruct_result846 is not None:
                        assert deconstruct_result846 is not None
                        unwrapped847 = deconstruct_result846
                        self.pretty_exists(unwrapped847)
                    else:
                        def _t1428(_dollar_dollar):
                            if _dollar_dollar.HasField("reduce"):
                                _t1429 = _dollar_dollar.reduce
                            else:
                                _t1429 = None
                            return _t1429
                        _t1430 = _t1428(msg)
                        deconstruct_result844 = _t1430
                        if deconstruct_result844 is not None:
                            assert deconstruct_result844 is not None
                            unwrapped845 = deconstruct_result844
                            self.pretty_reduce(unwrapped845)
                        else:
                            def _t1431(_dollar_dollar):
                                if (_dollar_dollar.HasField("conjunction") and not len(_dollar_dollar.conjunction.args) == 0):
                                    _t1432 = _dollar_dollar.conjunction
                                else:
                                    _t1432 = None
                                return _t1432
                            _t1433 = _t1431(msg)
                            deconstruct_result842 = _t1433
                            if deconstruct_result842 is not None:
                                assert deconstruct_result842 is not None
                                unwrapped843 = deconstruct_result842
                                self.pretty_conjunction(unwrapped843)
                            else:
                                def _t1434(_dollar_dollar):
                                    if (_dollar_dollar.HasField("disjunction") and not len(_dollar_dollar.disjunction.args) == 0):
                                        _t1435 = _dollar_dollar.disjunction
                                    else:
                                        _t1435 = None
                                    return _t1435
                                _t1436 = _t1434(msg)
                                deconstruct_result840 = _t1436
                                if deconstruct_result840 is not None:
                                    assert deconstruct_result840 is not None
                                    unwrapped841 = deconstruct_result840
                                    self.pretty_disjunction(unwrapped841)
                                else:
                                    def _t1437(_dollar_dollar):
                                        if _dollar_dollar.HasField("not"):
                                            _t1438 = getattr(_dollar_dollar, 'not')
                                        else:
                                            _t1438 = None
                                        return _t1438
                                    _t1439 = _t1437(msg)
                                    deconstruct_result838 = _t1439
                                    if deconstruct_result838 is not None:
                                        assert deconstruct_result838 is not None
                                        unwrapped839 = deconstruct_result838
                                        self.pretty_not(unwrapped839)
                                    else:
                                        def _t1440(_dollar_dollar):
                                            if _dollar_dollar.HasField("ffi"):
                                                _t1441 = _dollar_dollar.ffi
                                            else:
                                                _t1441 = None
                                            return _t1441
                                        _t1442 = _t1440(msg)
                                        deconstruct_result836 = _t1442
                                        if deconstruct_result836 is not None:
                                            assert deconstruct_result836 is not None
                                            unwrapped837 = deconstruct_result836
                                            self.pretty_ffi(unwrapped837)
                                        else:
                                            def _t1443(_dollar_dollar):
                                                if _dollar_dollar.HasField("atom"):
                                                    _t1444 = _dollar_dollar.atom
                                                else:
                                                    _t1444 = None
                                                return _t1444
                                            _t1445 = _t1443(msg)
                                            deconstruct_result834 = _t1445
                                            if deconstruct_result834 is not None:
                                                assert deconstruct_result834 is not None
                                                unwrapped835 = deconstruct_result834
                                                self.pretty_atom(unwrapped835)
                                            else:
                                                def _t1446(_dollar_dollar):
                                                    if _dollar_dollar.HasField("pragma"):
                                                        _t1447 = _dollar_dollar.pragma
                                                    else:
                                                        _t1447 = None
                                                    return _t1447
                                                _t1448 = _t1446(msg)
                                                deconstruct_result832 = _t1448
                                                if deconstruct_result832 is not None:
                                                    assert deconstruct_result832 is not None
                                                    unwrapped833 = deconstruct_result832
                                                    self.pretty_pragma(unwrapped833)
                                                else:
                                                    def _t1449(_dollar_dollar):
                                                        if _dollar_dollar.HasField("primitive"):
                                                            _t1450 = _dollar_dollar.primitive
                                                        else:
                                                            _t1450 = None
                                                        return _t1450
                                                    _t1451 = _t1449(msg)
                                                    deconstruct_result830 = _t1451
                                                    if deconstruct_result830 is not None:
                                                        assert deconstruct_result830 is not None
                                                        unwrapped831 = deconstruct_result830
                                                        self.pretty_primitive(unwrapped831)
                                                    else:
                                                        def _t1452(_dollar_dollar):
                                                            if _dollar_dollar.HasField("rel_atom"):
                                                                _t1453 = _dollar_dollar.rel_atom
                                                            else:
                                                                _t1453 = None
                                                            return _t1453
                                                        _t1454 = _t1452(msg)
                                                        deconstruct_result828 = _t1454
                                                        if deconstruct_result828 is not None:
                                                            assert deconstruct_result828 is not None
                                                            unwrapped829 = deconstruct_result828
                                                            self.pretty_rel_atom(unwrapped829)
                                                        else:
                                                            def _t1455(_dollar_dollar):
                                                                if _dollar_dollar.HasField("cast"):
                                                                    _t1456 = _dollar_dollar.cast
                                                                else:
                                                                    _t1456 = None
                                                                return _t1456
                                                            _t1457 = _t1455(msg)
                                                            deconstruct_result826 = _t1457
                                                            if deconstruct_result826 is not None:
                                                                assert deconstruct_result826 is not None
                                                                unwrapped827 = deconstruct_result826
                                                                self.pretty_cast(unwrapped827)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields853 = msg
        self.write("(")
        self.write("true")
        self.write(")")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields854 = msg
        self.write("(")
        self.write("false")
        self.write(")")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat859 = self._try_flat(msg, self.pretty_exists)
        if flat859 is not None:
            assert flat859 is not None
            self.write(flat859)
            return None
        else:
            def _t1458(_dollar_dollar):
                _t1459 = self.deconstruct_bindings(_dollar_dollar.body)
                return (_t1459, _dollar_dollar.body.value,)
            _t1460 = _t1458(msg)
            fields855 = _t1460
            assert fields855 is not None
            unwrapped_fields856 = fields855
            self.write("(")
            self.write("exists")
            self.indent_sexp()
            self.newline()
            field857 = unwrapped_fields856[0]
            self.pretty_bindings(field857)
            self.newline()
            field858 = unwrapped_fields856[1]
            self.pretty_formula(field858)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat865 = self._try_flat(msg, self.pretty_reduce)
        if flat865 is not None:
            assert flat865 is not None
            self.write(flat865)
            return None
        else:
            def _t1461(_dollar_dollar):
                return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            _t1462 = _t1461(msg)
            fields860 = _t1462
            assert fields860 is not None
            unwrapped_fields861 = fields860
            self.write("(")
            self.write("reduce")
            self.indent_sexp()
            self.newline()
            field862 = unwrapped_fields861[0]
            self.pretty_abstraction(field862)
            self.newline()
            field863 = unwrapped_fields861[1]
            self.pretty_abstraction(field863)
            self.newline()
            field864 = unwrapped_fields861[2]
            self.pretty_terms(field864)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat869 = self._try_flat(msg, self.pretty_terms)
        if flat869 is not None:
            assert flat869 is not None
            self.write(flat869)
            return None
        else:
            fields866 = msg
            self.write("(")
            self.write("terms")
            self.indent_sexp()
            if not len(fields866) == 0:
                self.newline()
                for i868, elem867 in enumerate(fields866):
                    if (i868 > 0):
                        self.newline()
                    self.pretty_term(elem867)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat874 = self._try_flat(msg, self.pretty_term)
        if flat874 is not None:
            assert flat874 is not None
            self.write(flat874)
            return None
        else:
            def _t1463(_dollar_dollar):
                if _dollar_dollar.HasField("var"):
                    _t1464 = _dollar_dollar.var
                else:
                    _t1464 = None
                return _t1464
            _t1465 = _t1463(msg)
            deconstruct_result872 = _t1465
            if deconstruct_result872 is not None:
                assert deconstruct_result872 is not None
                unwrapped873 = deconstruct_result872
                self.pretty_var(unwrapped873)
            else:
                def _t1466(_dollar_dollar):
                    if _dollar_dollar.HasField("constant"):
                        _t1467 = _dollar_dollar.constant
                    else:
                        _t1467 = None
                    return _t1467
                _t1468 = _t1466(msg)
                deconstruct_result870 = _t1468
                if deconstruct_result870 is not None:
                    assert deconstruct_result870 is not None
                    unwrapped871 = deconstruct_result870
                    self.pretty_constant(unwrapped871)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat877 = self._try_flat(msg, self.pretty_var)
        if flat877 is not None:
            assert flat877 is not None
            self.write(flat877)
            return None
        else:
            def _t1469(_dollar_dollar):
                return _dollar_dollar.name
            _t1470 = _t1469(msg)
            fields875 = _t1470
            assert fields875 is not None
            unwrapped_fields876 = fields875
            self.write(unwrapped_fields876)

    def pretty_constant(self, msg: logic_pb2.Value):
        flat879 = self._try_flat(msg, self.pretty_constant)
        if flat879 is not None:
            assert flat879 is not None
            self.write(flat879)
            return None
        else:
            fields878 = msg
            self.pretty_value(fields878)

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat884 = self._try_flat(msg, self.pretty_conjunction)
        if flat884 is not None:
            assert flat884 is not None
            self.write(flat884)
            return None
        else:
            def _t1471(_dollar_dollar):
                return _dollar_dollar.args
            _t1472 = _t1471(msg)
            fields880 = _t1472
            assert fields880 is not None
            unwrapped_fields881 = fields880
            self.write("(")
            self.write("and")
            self.indent_sexp()
            if not len(unwrapped_fields881) == 0:
                self.newline()
                for i883, elem882 in enumerate(unwrapped_fields881):
                    if (i883 > 0):
                        self.newline()
                    self.pretty_formula(elem882)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat889 = self._try_flat(msg, self.pretty_disjunction)
        if flat889 is not None:
            assert flat889 is not None
            self.write(flat889)
            return None
        else:
            def _t1473(_dollar_dollar):
                return _dollar_dollar.args
            _t1474 = _t1473(msg)
            fields885 = _t1474
            assert fields885 is not None
            unwrapped_fields886 = fields885
            self.write("(")
            self.write("or")
            self.indent_sexp()
            if not len(unwrapped_fields886) == 0:
                self.newline()
                for i888, elem887 in enumerate(unwrapped_fields886):
                    if (i888 > 0):
                        self.newline()
                    self.pretty_formula(elem887)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat892 = self._try_flat(msg, self.pretty_not)
        if flat892 is not None:
            assert flat892 is not None
            self.write(flat892)
            return None
        else:
            def _t1475(_dollar_dollar):
                return _dollar_dollar.arg
            _t1476 = _t1475(msg)
            fields890 = _t1476
            assert fields890 is not None
            unwrapped_fields891 = fields890
            self.write("(")
            self.write("not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields891)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat898 = self._try_flat(msg, self.pretty_ffi)
        if flat898 is not None:
            assert flat898 is not None
            self.write(flat898)
            return None
        else:
            def _t1477(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            _t1478 = _t1477(msg)
            fields893 = _t1478
            assert fields893 is not None
            unwrapped_fields894 = fields893
            self.write("(")
            self.write("ffi")
            self.indent_sexp()
            self.newline()
            field895 = unwrapped_fields894[0]
            self.pretty_name(field895)
            self.newline()
            field896 = unwrapped_fields894[1]
            self.pretty_ffi_args(field896)
            self.newline()
            field897 = unwrapped_fields894[2]
            self.pretty_terms(field897)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat900 = self._try_flat(msg, self.pretty_name)
        if flat900 is not None:
            assert flat900 is not None
            self.write(flat900)
            return None
        else:
            fields899 = msg
            self.write(":")
            self.write(fields899)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat904 = self._try_flat(msg, self.pretty_ffi_args)
        if flat904 is not None:
            assert flat904 is not None
            self.write(flat904)
            return None
        else:
            fields901 = msg
            self.write("(")
            self.write("args")
            self.indent_sexp()
            if not len(fields901) == 0:
                self.newline()
                for i903, elem902 in enumerate(fields901):
                    if (i903 > 0):
                        self.newline()
                    self.pretty_abstraction(elem902)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat911 = self._try_flat(msg, self.pretty_atom)
        if flat911 is not None:
            assert flat911 is not None
            self.write(flat911)
            return None
        else:
            def _t1479(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1480 = _t1479(msg)
            fields905 = _t1480
            assert fields905 is not None
            unwrapped_fields906 = fields905
            self.write("(")
            self.write("atom")
            self.indent_sexp()
            self.newline()
            field907 = unwrapped_fields906[0]
            self.pretty_relation_id(field907)
            field908 = unwrapped_fields906[1]
            if not len(field908) == 0:
                self.newline()
                for i910, elem909 in enumerate(field908):
                    if (i910 > 0):
                        self.newline()
                    self.pretty_term(elem909)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat918 = self._try_flat(msg, self.pretty_pragma)
        if flat918 is not None:
            assert flat918 is not None
            self.write(flat918)
            return None
        else:
            def _t1481(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1482 = _t1481(msg)
            fields912 = _t1482
            assert fields912 is not None
            unwrapped_fields913 = fields912
            self.write("(")
            self.write("pragma")
            self.indent_sexp()
            self.newline()
            field914 = unwrapped_fields913[0]
            self.pretty_name(field914)
            field915 = unwrapped_fields913[1]
            if not len(field915) == 0:
                self.newline()
                for i917, elem916 in enumerate(field915):
                    if (i917 > 0):
                        self.newline()
                    self.pretty_term(elem916)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat934 = self._try_flat(msg, self.pretty_primitive)
        if flat934 is not None:
            assert flat934 is not None
            self.write(flat934)
            return None
        else:
            def _t1483(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1484 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1484 = None
                return _t1484
            _t1485 = _t1483(msg)
            guard_result933 = _t1485
            if guard_result933 is not None:
                self.pretty_eq(msg)
            else:
                def _t1486(_dollar_dollar):
                    if _dollar_dollar.name == "rel_primitive_lt_monotype":
                        _t1487 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1487 = None
                    return _t1487
                _t1488 = _t1486(msg)
                guard_result932 = _t1488
                if guard_result932 is not None:
                    self.pretty_lt(msg)
                else:
                    def _t1489(_dollar_dollar):
                        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                            _t1490 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1490 = None
                        return _t1490
                    _t1491 = _t1489(msg)
                    guard_result931 = _t1491
                    if guard_result931 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        def _t1492(_dollar_dollar):
                            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                                _t1493 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1493 = None
                            return _t1493
                        _t1494 = _t1492(msg)
                        guard_result930 = _t1494
                        if guard_result930 is not None:
                            self.pretty_gt(msg)
                        else:
                            def _t1495(_dollar_dollar):
                                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                    _t1496 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                                else:
                                    _t1496 = None
                                return _t1496
                            _t1497 = _t1495(msg)
                            guard_result929 = _t1497
                            if guard_result929 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                def _t1498(_dollar_dollar):
                                    if _dollar_dollar.name == "rel_primitive_add_monotype":
                                        _t1499 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1499 = None
                                    return _t1499
                                _t1500 = _t1498(msg)
                                guard_result928 = _t1500
                                if guard_result928 is not None:
                                    self.pretty_add(msg)
                                else:
                                    def _t1501(_dollar_dollar):
                                        if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                            _t1502 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1502 = None
                                        return _t1502
                                    _t1503 = _t1501(msg)
                                    guard_result927 = _t1503
                                    if guard_result927 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        def _t1504(_dollar_dollar):
                                            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                                _t1505 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1505 = None
                                            return _t1505
                                        _t1506 = _t1504(msg)
                                        guard_result926 = _t1506
                                        if guard_result926 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            def _t1507(_dollar_dollar):
                                                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                    _t1508 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                                else:
                                                    _t1508 = None
                                                return _t1508
                                            _t1509 = _t1507(msg)
                                            guard_result925 = _t1509
                                            if guard_result925 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                def _t1510(_dollar_dollar):
                                                    return (_dollar_dollar.name, _dollar_dollar.terms,)
                                                _t1511 = _t1510(msg)
                                                fields919 = _t1511
                                                assert fields919 is not None
                                                unwrapped_fields920 = fields919
                                                self.write("(")
                                                self.write("primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field921 = unwrapped_fields920[0]
                                                self.pretty_name(field921)
                                                field922 = unwrapped_fields920[1]
                                                if not len(field922) == 0:
                                                    self.newline()
                                                    for i924, elem923 in enumerate(field922):
                                                        if (i924 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem923)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat939 = self._try_flat(msg, self.pretty_eq)
        if flat939 is not None:
            assert flat939 is not None
            self.write(flat939)
            return None
        else:
            def _t1512(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1513 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1513 = None
                return _t1513
            _t1514 = _t1512(msg)
            fields935 = _t1514
            assert fields935 is not None
            unwrapped_fields936 = fields935
            self.write("(")
            self.write("=")
            self.indent_sexp()
            self.newline()
            field937 = unwrapped_fields936[0]
            self.pretty_term(field937)
            self.newline()
            field938 = unwrapped_fields936[1]
            self.pretty_term(field938)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat944 = self._try_flat(msg, self.pretty_lt)
        if flat944 is not None:
            assert flat944 is not None
            self.write(flat944)
            return None
        else:
            def _t1515(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1516 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1516 = None
                return _t1516
            _t1517 = _t1515(msg)
            fields940 = _t1517
            assert fields940 is not None
            unwrapped_fields941 = fields940
            self.write("(")
            self.write("<")
            self.indent_sexp()
            self.newline()
            field942 = unwrapped_fields941[0]
            self.pretty_term(field942)
            self.newline()
            field943 = unwrapped_fields941[1]
            self.pretty_term(field943)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat949 = self._try_flat(msg, self.pretty_lt_eq)
        if flat949 is not None:
            assert flat949 is not None
            self.write(flat949)
            return None
        else:
            def _t1518(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                    _t1519 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1519 = None
                return _t1519
            _t1520 = _t1518(msg)
            fields945 = _t1520
            assert fields945 is not None
            unwrapped_fields946 = fields945
            self.write("(")
            self.write("<=")
            self.indent_sexp()
            self.newline()
            field947 = unwrapped_fields946[0]
            self.pretty_term(field947)
            self.newline()
            field948 = unwrapped_fields946[1]
            self.pretty_term(field948)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat954 = self._try_flat(msg, self.pretty_gt)
        if flat954 is not None:
            assert flat954 is not None
            self.write(flat954)
            return None
        else:
            def _t1521(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_monotype":
                    _t1522 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1522 = None
                return _t1522
            _t1523 = _t1521(msg)
            fields950 = _t1523
            assert fields950 is not None
            unwrapped_fields951 = fields950
            self.write("(")
            self.write(">")
            self.indent_sexp()
            self.newline()
            field952 = unwrapped_fields951[0]
            self.pretty_term(field952)
            self.newline()
            field953 = unwrapped_fields951[1]
            self.pretty_term(field953)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat959 = self._try_flat(msg, self.pretty_gt_eq)
        if flat959 is not None:
            assert flat959 is not None
            self.write(flat959)
            return None
        else:
            def _t1524(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                    _t1525 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1525 = None
                return _t1525
            _t1526 = _t1524(msg)
            fields955 = _t1526
            assert fields955 is not None
            unwrapped_fields956 = fields955
            self.write("(")
            self.write(">=")
            self.indent_sexp()
            self.newline()
            field957 = unwrapped_fields956[0]
            self.pretty_term(field957)
            self.newline()
            field958 = unwrapped_fields956[1]
            self.pretty_term(field958)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat965 = self._try_flat(msg, self.pretty_add)
        if flat965 is not None:
            assert flat965 is not None
            self.write(flat965)
            return None
        else:
            def _t1527(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_add_monotype":
                    _t1528 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1528 = None
                return _t1528
            _t1529 = _t1527(msg)
            fields960 = _t1529
            assert fields960 is not None
            unwrapped_fields961 = fields960
            self.write("(")
            self.write("+")
            self.indent_sexp()
            self.newline()
            field962 = unwrapped_fields961[0]
            self.pretty_term(field962)
            self.newline()
            field963 = unwrapped_fields961[1]
            self.pretty_term(field963)
            self.newline()
            field964 = unwrapped_fields961[2]
            self.pretty_term(field964)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat971 = self._try_flat(msg, self.pretty_minus)
        if flat971 is not None:
            assert flat971 is not None
            self.write(flat971)
            return None
        else:
            def _t1530(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                    _t1531 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1531 = None
                return _t1531
            _t1532 = _t1530(msg)
            fields966 = _t1532
            assert fields966 is not None
            unwrapped_fields967 = fields966
            self.write("(")
            self.write("-")
            self.indent_sexp()
            self.newline()
            field968 = unwrapped_fields967[0]
            self.pretty_term(field968)
            self.newline()
            field969 = unwrapped_fields967[1]
            self.pretty_term(field969)
            self.newline()
            field970 = unwrapped_fields967[2]
            self.pretty_term(field970)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat977 = self._try_flat(msg, self.pretty_multiply)
        if flat977 is not None:
            assert flat977 is not None
            self.write(flat977)
            return None
        else:
            def _t1533(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                    _t1534 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1534 = None
                return _t1534
            _t1535 = _t1533(msg)
            fields972 = _t1535
            assert fields972 is not None
            unwrapped_fields973 = fields972
            self.write("(")
            self.write("*")
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

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat983 = self._try_flat(msg, self.pretty_divide)
        if flat983 is not None:
            assert flat983 is not None
            self.write(flat983)
            return None
        else:
            def _t1536(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                    _t1537 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1537 = None
                return _t1537
            _t1538 = _t1536(msg)
            fields978 = _t1538
            assert fields978 is not None
            unwrapped_fields979 = fields978
            self.write("(")
            self.write("/")
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

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat988 = self._try_flat(msg, self.pretty_rel_term)
        if flat988 is not None:
            assert flat988 is not None
            self.write(flat988)
            return None
        else:
            def _t1539(_dollar_dollar):
                if _dollar_dollar.HasField("specialized_value"):
                    _t1540 = _dollar_dollar.specialized_value
                else:
                    _t1540 = None
                return _t1540
            _t1541 = _t1539(msg)
            deconstruct_result986 = _t1541
            if deconstruct_result986 is not None:
                assert deconstruct_result986 is not None
                unwrapped987 = deconstruct_result986
                self.pretty_specialized_value(unwrapped987)
            else:
                def _t1542(_dollar_dollar):
                    if _dollar_dollar.HasField("term"):
                        _t1543 = _dollar_dollar.term
                    else:
                        _t1543 = None
                    return _t1543
                _t1544 = _t1542(msg)
                deconstruct_result984 = _t1544
                if deconstruct_result984 is not None:
                    assert deconstruct_result984 is not None
                    unwrapped985 = deconstruct_result984
                    self.pretty_term(unwrapped985)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat990 = self._try_flat(msg, self.pretty_specialized_value)
        if flat990 is not None:
            assert flat990 is not None
            self.write(flat990)
            return None
        else:
            fields989 = msg
            self.write("#")
            self.pretty_value(fields989)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat997 = self._try_flat(msg, self.pretty_rel_atom)
        if flat997 is not None:
            assert flat997 is not None
            self.write(flat997)
            return None
        else:
            def _t1545(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1546 = _t1545(msg)
            fields991 = _t1546
            assert fields991 is not None
            unwrapped_fields992 = fields991
            self.write("(")
            self.write("relatom")
            self.indent_sexp()
            self.newline()
            field993 = unwrapped_fields992[0]
            self.pretty_name(field993)
            field994 = unwrapped_fields992[1]
            if not len(field994) == 0:
                self.newline()
                for i996, elem995 in enumerate(field994):
                    if (i996 > 0):
                        self.newline()
                    self.pretty_rel_term(elem995)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat1002 = self._try_flat(msg, self.pretty_cast)
        if flat1002 is not None:
            assert flat1002 is not None
            self.write(flat1002)
            return None
        else:
            def _t1547(_dollar_dollar):
                return (_dollar_dollar.input, _dollar_dollar.result,)
            _t1548 = _t1547(msg)
            fields998 = _t1548
            assert fields998 is not None
            unwrapped_fields999 = fields998
            self.write("(")
            self.write("cast")
            self.indent_sexp()
            self.newline()
            field1000 = unwrapped_fields999[0]
            self.pretty_term(field1000)
            self.newline()
            field1001 = unwrapped_fields999[1]
            self.pretty_term(field1001)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat1006 = self._try_flat(msg, self.pretty_attrs)
        if flat1006 is not None:
            assert flat1006 is not None
            self.write(flat1006)
            return None
        else:
            fields1003 = msg
            self.write("(")
            self.write("attrs")
            self.indent_sexp()
            if not len(fields1003) == 0:
                self.newline()
                for i1005, elem1004 in enumerate(fields1003):
                    if (i1005 > 0):
                        self.newline()
                    self.pretty_attribute(elem1004)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat1013 = self._try_flat(msg, self.pretty_attribute)
        if flat1013 is not None:
            assert flat1013 is not None
            self.write(flat1013)
            return None
        else:
            def _t1549(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args,)
            _t1550 = _t1549(msg)
            fields1007 = _t1550
            assert fields1007 is not None
            unwrapped_fields1008 = fields1007
            self.write("(")
            self.write("attribute")
            self.indent_sexp()
            self.newline()
            field1009 = unwrapped_fields1008[0]
            self.pretty_name(field1009)
            field1010 = unwrapped_fields1008[1]
            if not len(field1010) == 0:
                self.newline()
                for i1012, elem1011 in enumerate(field1010):
                    if (i1012 > 0):
                        self.newline()
                    self.pretty_value(elem1011)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat1020 = self._try_flat(msg, self.pretty_algorithm)
        if flat1020 is not None:
            assert flat1020 is not None
            self.write(flat1020)
            return None
        else:
            def _t1551(_dollar_dollar):
                return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            _t1552 = _t1551(msg)
            fields1014 = _t1552
            assert fields1014 is not None
            unwrapped_fields1015 = fields1014
            self.write("(")
            self.write("algorithm")
            self.indent_sexp()
            field1016 = unwrapped_fields1015[0]
            if not len(field1016) == 0:
                self.newline()
                for i1018, elem1017 in enumerate(field1016):
                    if (i1018 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1017)
            self.newline()
            field1019 = unwrapped_fields1015[1]
            self.pretty_script(field1019)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1025 = self._try_flat(msg, self.pretty_script)
        if flat1025 is not None:
            assert flat1025 is not None
            self.write(flat1025)
            return None
        else:
            def _t1553(_dollar_dollar):
                return _dollar_dollar.constructs
            _t1554 = _t1553(msg)
            fields1021 = _t1554
            assert fields1021 is not None
            unwrapped_fields1022 = fields1021
            self.write("(")
            self.write("script")
            self.indent_sexp()
            if not len(unwrapped_fields1022) == 0:
                self.newline()
                for i1024, elem1023 in enumerate(unwrapped_fields1022):
                    if (i1024 > 0):
                        self.newline()
                    self.pretty_construct(elem1023)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1030 = self._try_flat(msg, self.pretty_construct)
        if flat1030 is not None:
            assert flat1030 is not None
            self.write(flat1030)
            return None
        else:
            def _t1555(_dollar_dollar):
                if _dollar_dollar.HasField("loop"):
                    _t1556 = _dollar_dollar.loop
                else:
                    _t1556 = None
                return _t1556
            _t1557 = _t1555(msg)
            deconstruct_result1028 = _t1557
            if deconstruct_result1028 is not None:
                assert deconstruct_result1028 is not None
                unwrapped1029 = deconstruct_result1028
                self.pretty_loop(unwrapped1029)
            else:
                def _t1558(_dollar_dollar):
                    if _dollar_dollar.HasField("instruction"):
                        _t1559 = _dollar_dollar.instruction
                    else:
                        _t1559 = None
                    return _t1559
                _t1560 = _t1558(msg)
                deconstruct_result1026 = _t1560
                if deconstruct_result1026 is not None:
                    assert deconstruct_result1026 is not None
                    unwrapped1027 = deconstruct_result1026
                    self.pretty_instruction(unwrapped1027)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1035 = self._try_flat(msg, self.pretty_loop)
        if flat1035 is not None:
            assert flat1035 is not None
            self.write(flat1035)
            return None
        else:
            def _t1561(_dollar_dollar):
                return (_dollar_dollar.init, _dollar_dollar.body,)
            _t1562 = _t1561(msg)
            fields1031 = _t1562
            assert fields1031 is not None
            unwrapped_fields1032 = fields1031
            self.write("(")
            self.write("loop")
            self.indent_sexp()
            self.newline()
            field1033 = unwrapped_fields1032[0]
            self.pretty_init(field1033)
            self.newline()
            field1034 = unwrapped_fields1032[1]
            self.pretty_script(field1034)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1039 = self._try_flat(msg, self.pretty_init)
        if flat1039 is not None:
            assert flat1039 is not None
            self.write(flat1039)
            return None
        else:
            fields1036 = msg
            self.write("(")
            self.write("init")
            self.indent_sexp()
            if not len(fields1036) == 0:
                self.newline()
                for i1038, elem1037 in enumerate(fields1036):
                    if (i1038 > 0):
                        self.newline()
                    self.pretty_instruction(elem1037)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1050 = self._try_flat(msg, self.pretty_instruction)
        if flat1050 is not None:
            assert flat1050 is not None
            self.write(flat1050)
            return None
        else:
            def _t1563(_dollar_dollar):
                if _dollar_dollar.HasField("assign"):
                    _t1564 = _dollar_dollar.assign
                else:
                    _t1564 = None
                return _t1564
            _t1565 = _t1563(msg)
            deconstruct_result1048 = _t1565
            if deconstruct_result1048 is not None:
                assert deconstruct_result1048 is not None
                unwrapped1049 = deconstruct_result1048
                self.pretty_assign(unwrapped1049)
            else:
                def _t1566(_dollar_dollar):
                    if _dollar_dollar.HasField("upsert"):
                        _t1567 = _dollar_dollar.upsert
                    else:
                        _t1567 = None
                    return _t1567
                _t1568 = _t1566(msg)
                deconstruct_result1046 = _t1568
                if deconstruct_result1046 is not None:
                    assert deconstruct_result1046 is not None
                    unwrapped1047 = deconstruct_result1046
                    self.pretty_upsert(unwrapped1047)
                else:
                    def _t1569(_dollar_dollar):
                        if _dollar_dollar.HasField("break"):
                            _t1570 = getattr(_dollar_dollar, 'break')
                        else:
                            _t1570 = None
                        return _t1570
                    _t1571 = _t1569(msg)
                    deconstruct_result1044 = _t1571
                    if deconstruct_result1044 is not None:
                        assert deconstruct_result1044 is not None
                        unwrapped1045 = deconstruct_result1044
                        self.pretty_break(unwrapped1045)
                    else:
                        def _t1572(_dollar_dollar):
                            if _dollar_dollar.HasField("monoid_def"):
                                _t1573 = _dollar_dollar.monoid_def
                            else:
                                _t1573 = None
                            return _t1573
                        _t1574 = _t1572(msg)
                        deconstruct_result1042 = _t1574
                        if deconstruct_result1042 is not None:
                            assert deconstruct_result1042 is not None
                            unwrapped1043 = deconstruct_result1042
                            self.pretty_monoid_def(unwrapped1043)
                        else:
                            def _t1575(_dollar_dollar):
                                if _dollar_dollar.HasField("monus_def"):
                                    _t1576 = _dollar_dollar.monus_def
                                else:
                                    _t1576 = None
                                return _t1576
                            _t1577 = _t1575(msg)
                            deconstruct_result1040 = _t1577
                            if deconstruct_result1040 is not None:
                                assert deconstruct_result1040 is not None
                                unwrapped1041 = deconstruct_result1040
                                self.pretty_monus_def(unwrapped1041)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1057 = self._try_flat(msg, self.pretty_assign)
        if flat1057 is not None:
            assert flat1057 is not None
            self.write(flat1057)
            return None
        else:
            def _t1578(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1579 = _dollar_dollar.attrs
                else:
                    _t1579 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1579,)
            _t1580 = _t1578(msg)
            fields1051 = _t1580
            assert fields1051 is not None
            unwrapped_fields1052 = fields1051
            self.write("(")
            self.write("assign")
            self.indent_sexp()
            self.newline()
            field1053 = unwrapped_fields1052[0]
            self.pretty_relation_id(field1053)
            self.newline()
            field1054 = unwrapped_fields1052[1]
            self.pretty_abstraction(field1054)
            field1055 = unwrapped_fields1052[2]
            if field1055 is not None:
                self.newline()
                assert field1055 is not None
                opt_val1056 = field1055
                self.pretty_attrs(opt_val1056)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1064 = self._try_flat(msg, self.pretty_upsert)
        if flat1064 is not None:
            assert flat1064 is not None
            self.write(flat1064)
            return None
        else:
            def _t1581(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1582 = _dollar_dollar.attrs
                else:
                    _t1582 = None
                return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1582,)
            _t1583 = _t1581(msg)
            fields1058 = _t1583
            assert fields1058 is not None
            unwrapped_fields1059 = fields1058
            self.write("(")
            self.write("upsert")
            self.indent_sexp()
            self.newline()
            field1060 = unwrapped_fields1059[0]
            self.pretty_relation_id(field1060)
            self.newline()
            field1061 = unwrapped_fields1059[1]
            self.pretty_abstraction_with_arity(field1061)
            field1062 = unwrapped_fields1059[2]
            if field1062 is not None:
                self.newline()
                assert field1062 is not None
                opt_val1063 = field1062
                self.pretty_attrs(opt_val1063)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1069 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1069 is not None:
            assert flat1069 is not None
            self.write(flat1069)
            return None
        else:
            def _t1584(_dollar_dollar):
                _t1585 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
                return (_t1585, _dollar_dollar[0].value,)
            _t1586 = _t1584(msg)
            fields1065 = _t1586
            assert fields1065 is not None
            unwrapped_fields1066 = fields1065
            self.write("(")
            self.indent()
            field1067 = unwrapped_fields1066[0]
            self.pretty_bindings(field1067)
            self.newline()
            field1068 = unwrapped_fields1066[1]
            self.pretty_formula(field1068)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1076 = self._try_flat(msg, self.pretty_break)
        if flat1076 is not None:
            assert flat1076 is not None
            self.write(flat1076)
            return None
        else:
            def _t1587(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1588 = _dollar_dollar.attrs
                else:
                    _t1588 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1588,)
            _t1589 = _t1587(msg)
            fields1070 = _t1589
            assert fields1070 is not None
            unwrapped_fields1071 = fields1070
            self.write("(")
            self.write("break")
            self.indent_sexp()
            self.newline()
            field1072 = unwrapped_fields1071[0]
            self.pretty_relation_id(field1072)
            self.newline()
            field1073 = unwrapped_fields1071[1]
            self.pretty_abstraction(field1073)
            field1074 = unwrapped_fields1071[2]
            if field1074 is not None:
                self.newline()
                assert field1074 is not None
                opt_val1075 = field1074
                self.pretty_attrs(opt_val1075)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1084 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1084 is not None:
            assert flat1084 is not None
            self.write(flat1084)
            return None
        else:
            def _t1590(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1591 = _dollar_dollar.attrs
                else:
                    _t1591 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1591,)
            _t1592 = _t1590(msg)
            fields1077 = _t1592
            assert fields1077 is not None
            unwrapped_fields1078 = fields1077
            self.write("(")
            self.write("monoid")
            self.indent_sexp()
            self.newline()
            field1079 = unwrapped_fields1078[0]
            self.pretty_monoid(field1079)
            self.newline()
            field1080 = unwrapped_fields1078[1]
            self.pretty_relation_id(field1080)
            self.newline()
            field1081 = unwrapped_fields1078[2]
            self.pretty_abstraction_with_arity(field1081)
            field1082 = unwrapped_fields1078[3]
            if field1082 is not None:
                self.newline()
                assert field1082 is not None
                opt_val1083 = field1082
                self.pretty_attrs(opt_val1083)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1093 = self._try_flat(msg, self.pretty_monoid)
        if flat1093 is not None:
            assert flat1093 is not None
            self.write(flat1093)
            return None
        else:
            def _t1593(_dollar_dollar):
                if _dollar_dollar.HasField("or_monoid"):
                    _t1594 = _dollar_dollar.or_monoid
                else:
                    _t1594 = None
                return _t1594
            _t1595 = _t1593(msg)
            deconstruct_result1091 = _t1595
            if deconstruct_result1091 is not None:
                assert deconstruct_result1091 is not None
                unwrapped1092 = deconstruct_result1091
                self.pretty_or_monoid(unwrapped1092)
            else:
                def _t1596(_dollar_dollar):
                    if _dollar_dollar.HasField("min_monoid"):
                        _t1597 = _dollar_dollar.min_monoid
                    else:
                        _t1597 = None
                    return _t1597
                _t1598 = _t1596(msg)
                deconstruct_result1089 = _t1598
                if deconstruct_result1089 is not None:
                    assert deconstruct_result1089 is not None
                    unwrapped1090 = deconstruct_result1089
                    self.pretty_min_monoid(unwrapped1090)
                else:
                    def _t1599(_dollar_dollar):
                        if _dollar_dollar.HasField("max_monoid"):
                            _t1600 = _dollar_dollar.max_monoid
                        else:
                            _t1600 = None
                        return _t1600
                    _t1601 = _t1599(msg)
                    deconstruct_result1087 = _t1601
                    if deconstruct_result1087 is not None:
                        assert deconstruct_result1087 is not None
                        unwrapped1088 = deconstruct_result1087
                        self.pretty_max_monoid(unwrapped1088)
                    else:
                        def _t1602(_dollar_dollar):
                            if _dollar_dollar.HasField("sum_monoid"):
                                _t1603 = _dollar_dollar.sum_monoid
                            else:
                                _t1603 = None
                            return _t1603
                        _t1604 = _t1602(msg)
                        deconstruct_result1085 = _t1604
                        if deconstruct_result1085 is not None:
                            assert deconstruct_result1085 is not None
                            unwrapped1086 = deconstruct_result1085
                            self.pretty_sum_monoid(unwrapped1086)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1094 = msg
        self.write("(")
        self.write("or")
        self.write(")")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1097 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1097 is not None:
            assert flat1097 is not None
            self.write(flat1097)
            return None
        else:
            def _t1605(_dollar_dollar):
                return _dollar_dollar.type
            _t1606 = _t1605(msg)
            fields1095 = _t1606
            assert fields1095 is not None
            unwrapped_fields1096 = fields1095
            self.write("(")
            self.write("min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1096)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1100 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1100 is not None:
            assert flat1100 is not None
            self.write(flat1100)
            return None
        else:
            def _t1607(_dollar_dollar):
                return _dollar_dollar.type
            _t1608 = _t1607(msg)
            fields1098 = _t1608
            assert fields1098 is not None
            unwrapped_fields1099 = fields1098
            self.write("(")
            self.write("max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1099)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1103 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1103 is not None:
            assert flat1103 is not None
            self.write(flat1103)
            return None
        else:
            def _t1609(_dollar_dollar):
                return _dollar_dollar.type
            _t1610 = _t1609(msg)
            fields1101 = _t1610
            assert fields1101 is not None
            unwrapped_fields1102 = fields1101
            self.write("(")
            self.write("sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1102)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1111 = self._try_flat(msg, self.pretty_monus_def)
        if flat1111 is not None:
            assert flat1111 is not None
            self.write(flat1111)
            return None
        else:
            def _t1611(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1612 = _dollar_dollar.attrs
                else:
                    _t1612 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1612,)
            _t1613 = _t1611(msg)
            fields1104 = _t1613
            assert fields1104 is not None
            unwrapped_fields1105 = fields1104
            self.write("(")
            self.write("monus")
            self.indent_sexp()
            self.newline()
            field1106 = unwrapped_fields1105[0]
            self.pretty_monoid(field1106)
            self.newline()
            field1107 = unwrapped_fields1105[1]
            self.pretty_relation_id(field1107)
            self.newline()
            field1108 = unwrapped_fields1105[2]
            self.pretty_abstraction_with_arity(field1108)
            field1109 = unwrapped_fields1105[3]
            if field1109 is not None:
                self.newline()
                assert field1109 is not None
                opt_val1110 = field1109
                self.pretty_attrs(opt_val1110)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1118 = self._try_flat(msg, self.pretty_constraint)
        if flat1118 is not None:
            assert flat1118 is not None
            self.write(flat1118)
            return None
        else:
            def _t1614(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            _t1615 = _t1614(msg)
            fields1112 = _t1615
            assert fields1112 is not None
            unwrapped_fields1113 = fields1112
            self.write("(")
            self.write("functional_dependency")
            self.indent_sexp()
            self.newline()
            field1114 = unwrapped_fields1113[0]
            self.pretty_relation_id(field1114)
            self.newline()
            field1115 = unwrapped_fields1113[1]
            self.pretty_abstraction(field1115)
            self.newline()
            field1116 = unwrapped_fields1113[2]
            self.pretty_functional_dependency_keys(field1116)
            self.newline()
            field1117 = unwrapped_fields1113[3]
            self.pretty_functional_dependency_values(field1117)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1122 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1122 is not None:
            assert flat1122 is not None
            self.write(flat1122)
            return None
        else:
            fields1119 = msg
            self.write("(")
            self.write("keys")
            self.indent_sexp()
            if not len(fields1119) == 0:
                self.newline()
                for i1121, elem1120 in enumerate(fields1119):
                    if (i1121 > 0):
                        self.newline()
                    self.pretty_var(elem1120)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1126 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1126 is not None:
            assert flat1126 is not None
            self.write(flat1126)
            return None
        else:
            fields1123 = msg
            self.write("(")
            self.write("values")
            self.indent_sexp()
            if not len(fields1123) == 0:
                self.newline()
                for i1125, elem1124 in enumerate(fields1123):
                    if (i1125 > 0):
                        self.newline()
                    self.pretty_var(elem1124)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1133 = self._try_flat(msg, self.pretty_data)
        if flat1133 is not None:
            assert flat1133 is not None
            self.write(flat1133)
            return None
        else:
            def _t1616(_dollar_dollar):
                if _dollar_dollar.HasField("edb"):
                    _t1617 = _dollar_dollar.edb
                else:
                    _t1617 = None
                return _t1617
            _t1618 = _t1616(msg)
            deconstruct_result1131 = _t1618
            if deconstruct_result1131 is not None:
                assert deconstruct_result1131 is not None
                unwrapped1132 = deconstruct_result1131
                self.pretty_edb(unwrapped1132)
            else:
                def _t1619(_dollar_dollar):
                    if _dollar_dollar.HasField("betree_relation"):
                        _t1620 = _dollar_dollar.betree_relation
                    else:
                        _t1620 = None
                    return _t1620
                _t1621 = _t1619(msg)
                deconstruct_result1129 = _t1621
                if deconstruct_result1129 is not None:
                    assert deconstruct_result1129 is not None
                    unwrapped1130 = deconstruct_result1129
                    self.pretty_betree_relation(unwrapped1130)
                else:
                    def _t1622(_dollar_dollar):
                        if _dollar_dollar.HasField("csv_data"):
                            _t1623 = _dollar_dollar.csv_data
                        else:
                            _t1623 = None
                        return _t1623
                    _t1624 = _t1622(msg)
                    deconstruct_result1127 = _t1624
                    if deconstruct_result1127 is not None:
                        assert deconstruct_result1127 is not None
                        unwrapped1128 = deconstruct_result1127
                        self.pretty_csv_data(unwrapped1128)
                    else:
                        raise ParseError("No matching rule for data")

    def pretty_edb(self, msg: logic_pb2.EDB):
        flat1139 = self._try_flat(msg, self.pretty_edb)
        if flat1139 is not None:
            assert flat1139 is not None
            self.write(flat1139)
            return None
        else:
            def _t1625(_dollar_dollar):
                return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            _t1626 = _t1625(msg)
            fields1134 = _t1626
            assert fields1134 is not None
            unwrapped_fields1135 = fields1134
            self.write("(")
            self.write("edb")
            self.indent_sexp()
            self.newline()
            field1136 = unwrapped_fields1135[0]
            self.pretty_relation_id(field1136)
            self.newline()
            field1137 = unwrapped_fields1135[1]
            self.pretty_edb_path(field1137)
            self.newline()
            field1138 = unwrapped_fields1135[2]
            self.pretty_edb_types(field1138)
            self.dedent()
            self.write(")")

    def pretty_edb_path(self, msg: Sequence[str]):
        flat1143 = self._try_flat(msg, self.pretty_edb_path)
        if flat1143 is not None:
            assert flat1143 is not None
            self.write(flat1143)
            return None
        else:
            fields1140 = msg
            self.write("[")
            self.indent()
            for i1142, elem1141 in enumerate(fields1140):
                if (i1142 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1141))
            self.dedent()
            self.write("]")

    def pretty_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1147 = self._try_flat(msg, self.pretty_edb_types)
        if flat1147 is not None:
            assert flat1147 is not None
            self.write(flat1147)
            return None
        else:
            fields1144 = msg
            self.write("[")
            self.indent()
            for i1146, elem1145 in enumerate(fields1144):
                if (i1146 > 0):
                    self.newline()
                self.pretty_type(elem1145)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1152 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1152 is not None:
            assert flat1152 is not None
            self.write(flat1152)
            return None
        else:
            def _t1627(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_info,)
            _t1628 = _t1627(msg)
            fields1148 = _t1628
            assert fields1148 is not None
            unwrapped_fields1149 = fields1148
            self.write("(")
            self.write("betree_relation")
            self.indent_sexp()
            self.newline()
            field1150 = unwrapped_fields1149[0]
            self.pretty_relation_id(field1150)
            self.newline()
            field1151 = unwrapped_fields1149[1]
            self.pretty_betree_info(field1151)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1158 = self._try_flat(msg, self.pretty_betree_info)
        if flat1158 is not None:
            assert flat1158 is not None
            self.write(flat1158)
            return None
        else:
            def _t1629(_dollar_dollar):
                _t1630 = self.deconstruct_betree_info_config(_dollar_dollar)
                return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1630,)
            _t1631 = _t1629(msg)
            fields1153 = _t1631
            assert fields1153 is not None
            unwrapped_fields1154 = fields1153
            self.write("(")
            self.write("betree_info")
            self.indent_sexp()
            self.newline()
            field1155 = unwrapped_fields1154[0]
            self.pretty_betree_info_key_types(field1155)
            self.newline()
            field1156 = unwrapped_fields1154[1]
            self.pretty_betree_info_value_types(field1156)
            self.newline()
            field1157 = unwrapped_fields1154[2]
            self.pretty_config_dict(field1157)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1162 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1162 is not None:
            assert flat1162 is not None
            self.write(flat1162)
            return None
        else:
            fields1159 = msg
            self.write("(")
            self.write("key_types")
            self.indent_sexp()
            if not len(fields1159) == 0:
                self.newline()
                for i1161, elem1160 in enumerate(fields1159):
                    if (i1161 > 0):
                        self.newline()
                    self.pretty_type(elem1160)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1166 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1166 is not None:
            assert flat1166 is not None
            self.write(flat1166)
            return None
        else:
            fields1163 = msg
            self.write("(")
            self.write("value_types")
            self.indent_sexp()
            if not len(fields1163) == 0:
                self.newline()
                for i1165, elem1164 in enumerate(fields1163):
                    if (i1165 > 0):
                        self.newline()
                    self.pretty_type(elem1164)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1173 = self._try_flat(msg, self.pretty_csv_data)
        if flat1173 is not None:
            assert flat1173 is not None
            self.write(flat1173)
            return None
        else:
            def _t1632(_dollar_dollar):
                return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            _t1633 = _t1632(msg)
            fields1167 = _t1633
            assert fields1167 is not None
            unwrapped_fields1168 = fields1167
            self.write("(")
            self.write("csv_data")
            self.indent_sexp()
            self.newline()
            field1169 = unwrapped_fields1168[0]
            self.pretty_csvlocator(field1169)
            self.newline()
            field1170 = unwrapped_fields1168[1]
            self.pretty_csv_config(field1170)
            self.newline()
            field1171 = unwrapped_fields1168[2]
            self.pretty_gnf_columns(field1171)
            self.newline()
            field1172 = unwrapped_fields1168[3]
            self.pretty_csv_asof(field1172)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1180 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1180 is not None:
            assert flat1180 is not None
            self.write(flat1180)
            return None
        else:
            def _t1634(_dollar_dollar):
                if not len(_dollar_dollar.paths) == 0:
                    _t1635 = _dollar_dollar.paths
                else:
                    _t1635 = None
                if _dollar_dollar.inline_data.decode('utf-8') != "":
                    _t1636 = _dollar_dollar.inline_data.decode('utf-8')
                else:
                    _t1636 = None
                return (_t1635, _t1636,)
            _t1637 = _t1634(msg)
            fields1174 = _t1637
            assert fields1174 is not None
            unwrapped_fields1175 = fields1174
            self.write("(")
            self.write("csv_locator")
            self.indent_sexp()
            field1176 = unwrapped_fields1175[0]
            if field1176 is not None:
                self.newline()
                assert field1176 is not None
                opt_val1177 = field1176
                self.pretty_csv_locator_paths(opt_val1177)
            field1178 = unwrapped_fields1175[1]
            if field1178 is not None:
                self.newline()
                assert field1178 is not None
                opt_val1179 = field1178
                self.pretty_csv_locator_inline_data(opt_val1179)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1184 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1184 is not None:
            assert flat1184 is not None
            self.write(flat1184)
            return None
        else:
            fields1181 = msg
            self.write("(")
            self.write("paths")
            self.indent_sexp()
            if not len(fields1181) == 0:
                self.newline()
                for i1183, elem1182 in enumerate(fields1181):
                    if (i1183 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1182))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1186 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1186 is not None:
            assert flat1186 is not None
            self.write(flat1186)
            return None
        else:
            fields1185 = msg
            self.write("(")
            self.write("inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1185))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1189 = self._try_flat(msg, self.pretty_csv_config)
        if flat1189 is not None:
            assert flat1189 is not None
            self.write(flat1189)
            return None
        else:
            def _t1638(_dollar_dollar):
                _t1639 = self.deconstruct_csv_config(_dollar_dollar)
                return _t1639
            _t1640 = _t1638(msg)
            fields1187 = _t1640
            assert fields1187 is not None
            unwrapped_fields1188 = fields1187
            self.write("(")
            self.write("csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1188)
            self.dedent()
            self.write(")")

    def pretty_gnf_columns(self, msg: Sequence[logic_pb2.GNFColumn]):
        flat1193 = self._try_flat(msg, self.pretty_gnf_columns)
        if flat1193 is not None:
            assert flat1193 is not None
            self.write(flat1193)
            return None
        else:
            fields1190 = msg
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(fields1190) == 0:
                self.newline()
                for i1192, elem1191 in enumerate(fields1190):
                    if (i1192 > 0):
                        self.newline()
                    self.pretty_gnf_column(elem1191)
            self.dedent()
            self.write(")")

    def pretty_gnf_column(self, msg: logic_pb2.GNFColumn):
        flat1202 = self._try_flat(msg, self.pretty_gnf_column)
        if flat1202 is not None:
            assert flat1202 is not None
            self.write(flat1202)
            return None
        else:
            def _t1641(_dollar_dollar):
                if _dollar_dollar.HasField("target_id"):
                    _t1642 = _dollar_dollar.target_id
                else:
                    _t1642 = None
                return (_dollar_dollar.column_path, _t1642, _dollar_dollar.types,)
            _t1643 = _t1641(msg)
            fields1194 = _t1643
            assert fields1194 is not None
            unwrapped_fields1195 = fields1194
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field1196 = unwrapped_fields1195[0]
            self.pretty_gnf_column_path(field1196)
            field1197 = unwrapped_fields1195[1]
            if field1197 is not None:
                self.newline()
                assert field1197 is not None
                opt_val1198 = field1197
                self.pretty_relation_id(opt_val1198)
            self.newline()
            self.write("[")
            field1199 = unwrapped_fields1195[2]
            for i1201, elem1200 in enumerate(field1199):
                if (i1201 > 0):
                    self.newline()
                self.pretty_type(elem1200)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_gnf_column_path(self, msg: Sequence[str]):
        flat1209 = self._try_flat(msg, self.pretty_gnf_column_path)
        if flat1209 is not None:
            assert flat1209 is not None
            self.write(flat1209)
            return None
        else:
            def _t1644(_dollar_dollar):
                if len(_dollar_dollar) == 1:
                    _t1645 = _dollar_dollar[0]
                else:
                    _t1645 = None
                return _t1645
            _t1646 = _t1644(msg)
            deconstruct_result1207 = _t1646
            if deconstruct_result1207 is not None:
                assert deconstruct_result1207 is not None
                unwrapped1208 = deconstruct_result1207
                self.write(self.format_string_value(unwrapped1208))
            else:
                def _t1647(_dollar_dollar):
                    if len(_dollar_dollar) != 1:
                        _t1648 = _dollar_dollar
                    else:
                        _t1648 = None
                    return _t1648
                _t1649 = _t1647(msg)
                deconstruct_result1203 = _t1649
                if deconstruct_result1203 is not None:
                    assert deconstruct_result1203 is not None
                    unwrapped1204 = deconstruct_result1203
                    self.write("[")
                    self.indent()
                    for i1206, elem1205 in enumerate(unwrapped1204):
                        if (i1206 > 0):
                            self.newline()
                        self.write(self.format_string_value(elem1205))
                    self.dedent()
                    self.write("]")
                else:
                    raise ParseError("No matching rule for gnf_column_path")

    def pretty_csv_asof(self, msg: str):
        flat1211 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1211 is not None:
            assert flat1211 is not None
            self.write(flat1211)
            return None
        else:
            fields1210 = msg
            self.write("(")
            self.write("asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1210))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1214 = self._try_flat(msg, self.pretty_undefine)
        if flat1214 is not None:
            assert flat1214 is not None
            self.write(flat1214)
            return None
        else:
            def _t1650(_dollar_dollar):
                return _dollar_dollar.fragment_id
            _t1651 = _t1650(msg)
            fields1212 = _t1651
            assert fields1212 is not None
            unwrapped_fields1213 = fields1212
            self.write("(")
            self.write("undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1213)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1219 = self._try_flat(msg, self.pretty_context)
        if flat1219 is not None:
            assert flat1219 is not None
            self.write(flat1219)
            return None
        else:
            def _t1652(_dollar_dollar):
                return _dollar_dollar.relations
            _t1653 = _t1652(msg)
            fields1215 = _t1653
            assert fields1215 is not None
            unwrapped_fields1216 = fields1215
            self.write("(")
            self.write("context")
            self.indent_sexp()
            if not len(unwrapped_fields1216) == 0:
                self.newline()
                for i1218, elem1217 in enumerate(unwrapped_fields1216):
                    if (i1218 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1217)
            self.dedent()
            self.write(")")

    def pretty_snapshot(self, msg: transactions_pb2.Snapshot):
        flat1224 = self._try_flat(msg, self.pretty_snapshot)
        if flat1224 is not None:
            assert flat1224 is not None
            self.write(flat1224)
            return None
        else:
            def _t1654(_dollar_dollar):
                return _dollar_dollar.mappings
            _t1655 = _t1654(msg)
            fields1220 = _t1655
            assert fields1220 is not None
            unwrapped_fields1221 = fields1220
            self.write("(")
            self.write("snapshot")
            self.indent_sexp()
            if not len(unwrapped_fields1221) == 0:
                self.newline()
                for i1223, elem1222 in enumerate(unwrapped_fields1221):
                    if (i1223 > 0):
                        self.newline()
                    self.pretty_snapshot_mapping(elem1222)
            self.dedent()
            self.write(")")

    def pretty_snapshot_mapping(self, msg: transactions_pb2.SnapshotMapping):
        flat1229 = self._try_flat(msg, self.pretty_snapshot_mapping)
        if flat1229 is not None:
            assert flat1229 is not None
            self.write(flat1229)
            return None
        else:
            def _t1656(_dollar_dollar):
                return (_dollar_dollar.destination_path, _dollar_dollar.source_relation,)
            _t1657 = _t1656(msg)
            fields1225 = _t1657
            assert fields1225 is not None
            unwrapped_fields1226 = fields1225
            field1227 = unwrapped_fields1226[0]
            self.pretty_edb_path(field1227)
            self.write(" ")
            field1228 = unwrapped_fields1226[1]
            self.pretty_relation_id(field1228)

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1233 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1233 is not None:
            assert flat1233 is not None
            self.write(flat1233)
            return None
        else:
            fields1230 = msg
            self.write("(")
            self.write("reads")
            self.indent_sexp()
            if not len(fields1230) == 0:
                self.newline()
                for i1232, elem1231 in enumerate(fields1230):
                    if (i1232 > 0):
                        self.newline()
                    self.pretty_read(elem1231)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1244 = self._try_flat(msg, self.pretty_read)
        if flat1244 is not None:
            assert flat1244 is not None
            self.write(flat1244)
            return None
        else:
            def _t1658(_dollar_dollar):
                if _dollar_dollar.HasField("demand"):
                    _t1659 = _dollar_dollar.demand
                else:
                    _t1659 = None
                return _t1659
            _t1660 = _t1658(msg)
            deconstruct_result1242 = _t1660
            if deconstruct_result1242 is not None:
                assert deconstruct_result1242 is not None
                unwrapped1243 = deconstruct_result1242
                self.pretty_demand(unwrapped1243)
            else:
                def _t1661(_dollar_dollar):
                    if _dollar_dollar.HasField("output"):
                        _t1662 = _dollar_dollar.output
                    else:
                        _t1662 = None
                    return _t1662
                _t1663 = _t1661(msg)
                deconstruct_result1240 = _t1663
                if deconstruct_result1240 is not None:
                    assert deconstruct_result1240 is not None
                    unwrapped1241 = deconstruct_result1240
                    self.pretty_output(unwrapped1241)
                else:
                    def _t1664(_dollar_dollar):
                        if _dollar_dollar.HasField("what_if"):
                            _t1665 = _dollar_dollar.what_if
                        else:
                            _t1665 = None
                        return _t1665
                    _t1666 = _t1664(msg)
                    deconstruct_result1238 = _t1666
                    if deconstruct_result1238 is not None:
                        assert deconstruct_result1238 is not None
                        unwrapped1239 = deconstruct_result1238
                        self.pretty_what_if(unwrapped1239)
                    else:
                        def _t1667(_dollar_dollar):
                            if _dollar_dollar.HasField("abort"):
                                _t1668 = _dollar_dollar.abort
                            else:
                                _t1668 = None
                            return _t1668
                        _t1669 = _t1667(msg)
                        deconstruct_result1236 = _t1669
                        if deconstruct_result1236 is not None:
                            assert deconstruct_result1236 is not None
                            unwrapped1237 = deconstruct_result1236
                            self.pretty_abort(unwrapped1237)
                        else:
                            def _t1670(_dollar_dollar):
                                if _dollar_dollar.HasField("export"):
                                    _t1671 = _dollar_dollar.export
                                else:
                                    _t1671 = None
                                return _t1671
                            _t1672 = _t1670(msg)
                            deconstruct_result1234 = _t1672
                            if deconstruct_result1234 is not None:
                                assert deconstruct_result1234 is not None
                                unwrapped1235 = deconstruct_result1234
                                self.pretty_export(unwrapped1235)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1247 = self._try_flat(msg, self.pretty_demand)
        if flat1247 is not None:
            assert flat1247 is not None
            self.write(flat1247)
            return None
        else:
            def _t1673(_dollar_dollar):
                return _dollar_dollar.relation_id
            _t1674 = _t1673(msg)
            fields1245 = _t1674
            assert fields1245 is not None
            unwrapped_fields1246 = fields1245
            self.write("(")
            self.write("demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1246)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1252 = self._try_flat(msg, self.pretty_output)
        if flat1252 is not None:
            assert flat1252 is not None
            self.write(flat1252)
            return None
        else:
            def _t1675(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_id,)
            _t1676 = _t1675(msg)
            fields1248 = _t1676
            assert fields1248 is not None
            unwrapped_fields1249 = fields1248
            self.write("(")
            self.write("output")
            self.indent_sexp()
            self.newline()
            field1250 = unwrapped_fields1249[0]
            self.pretty_name(field1250)
            self.newline()
            field1251 = unwrapped_fields1249[1]
            self.pretty_relation_id(field1251)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1257 = self._try_flat(msg, self.pretty_what_if)
        if flat1257 is not None:
            assert flat1257 is not None
            self.write(flat1257)
            return None
        else:
            def _t1677(_dollar_dollar):
                return (_dollar_dollar.branch, _dollar_dollar.epoch,)
            _t1678 = _t1677(msg)
            fields1253 = _t1678
            assert fields1253 is not None
            unwrapped_fields1254 = fields1253
            self.write("(")
            self.write("what_if")
            self.indent_sexp()
            self.newline()
            field1255 = unwrapped_fields1254[0]
            self.pretty_name(field1255)
            self.newline()
            field1256 = unwrapped_fields1254[1]
            self.pretty_epoch(field1256)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1263 = self._try_flat(msg, self.pretty_abort)
        if flat1263 is not None:
            assert flat1263 is not None
            self.write(flat1263)
            return None
        else:
            def _t1679(_dollar_dollar):
                if _dollar_dollar.name != "abort":
                    _t1680 = _dollar_dollar.name
                else:
                    _t1680 = None
                return (_t1680, _dollar_dollar.relation_id,)
            _t1681 = _t1679(msg)
            fields1258 = _t1681
            assert fields1258 is not None
            unwrapped_fields1259 = fields1258
            self.write("(")
            self.write("abort")
            self.indent_sexp()
            field1260 = unwrapped_fields1259[0]
            if field1260 is not None:
                self.newline()
                assert field1260 is not None
                opt_val1261 = field1260
                self.pretty_name(opt_val1261)
            self.newline()
            field1262 = unwrapped_fields1259[1]
            self.pretty_relation_id(field1262)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1266 = self._try_flat(msg, self.pretty_export)
        if flat1266 is not None:
            assert flat1266 is not None
            self.write(flat1266)
            return None
        else:
            def _t1682(_dollar_dollar):
                return _dollar_dollar.csv_config
            _t1683 = _t1682(msg)
            fields1264 = _t1683
            assert fields1264 is not None
            unwrapped_fields1265 = fields1264
            self.write("(")
            self.write("export")
            self.indent_sexp()
            self.newline()
            self.pretty_export_csv_config(unwrapped_fields1265)
            self.dedent()
            self.write(")")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1272 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1272 is not None:
            assert flat1272 is not None
            self.write(flat1272)
            return None
        else:
            def _t1684(_dollar_dollar):
                _t1685 = self.deconstruct_export_csv_config(_dollar_dollar)
                return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1685,)
            _t1686 = _t1684(msg)
            fields1267 = _t1686
            assert fields1267 is not None
            unwrapped_fields1268 = fields1267
            self.write("(")
            self.write("export_csv_config")
            self.indent_sexp()
            self.newline()
            field1269 = unwrapped_fields1268[0]
            self.pretty_export_csv_path(field1269)
            self.newline()
            field1270 = unwrapped_fields1268[1]
            self.pretty_export_csv_columns(field1270)
            self.newline()
            field1271 = unwrapped_fields1268[2]
            self.pretty_config_dict(field1271)
            self.dedent()
            self.write(")")

    def pretty_export_csv_path(self, msg: str):
        flat1274 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1274 is not None:
            assert flat1274 is not None
            self.write(flat1274)
            return None
        else:
            fields1273 = msg
            self.write("(")
            self.write("path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1273))
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1278 = self._try_flat(msg, self.pretty_export_csv_columns)
        if flat1278 is not None:
            assert flat1278 is not None
            self.write(flat1278)
            return None
        else:
            fields1275 = msg
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(fields1275) == 0:
                self.newline()
                for i1277, elem1276 in enumerate(fields1275):
                    if (i1277 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1276)
            self.dedent()
            self.write(")")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1283 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1283 is not None:
            assert flat1283 is not None
            self.write(flat1283)
            return None
        else:
            def _t1687(_dollar_dollar):
                return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            _t1688 = _t1687(msg)
            fields1279 = _t1688
            assert fields1279 is not None
            unwrapped_fields1280 = fields1279
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field1281 = unwrapped_fields1280[0]
            self.write(self.format_string_value(field1281))
            self.newline()
            field1282 = unwrapped_fields1280[1]
            self.pretty_relation_id(field1282)
            self.dedent()
            self.write(")")


    # --- Auto-generated printers for uncovered proto types ---

    def pretty_debug_info(self, msg: fragments_pb2.DebugInfo):
        self.write("(debug_info")
        self.indent_sexp()
        for _idx, _rid in enumerate(msg.ids):
            self.newline()
            self.write("(")
            _t1726 = logic_pb2.UInt128Value(low=_rid.id_low, high=_rid.id_high)
            self.pprint_dispatch(_t1726)
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
