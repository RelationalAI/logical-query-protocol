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

    def relation_id_to_uint128(self, msg: logic_pb2.RelationId) -> logic_pb2.UInt128Value:
        """Convert RelationId to UInt128Value representation."""
        return logic_pb2.UInt128Value(low=msg.id_low, high=msg.id_high)

    def format_string_value(self, s: str) -> str:
        """Format a string value with double quotes for LQP output."""
        escaped = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return '"' + escaped + '"'

    # --- Helper functions ---

    def _make_value_int32(self, v: int) -> logic_pb2.Value:
        _t1634 = logic_pb2.Value(int_value=int(v))
        return _t1634

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1635 = logic_pb2.Value(int_value=v)
        return _t1635

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1636 = logic_pb2.Value(float_value=v)
        return _t1636

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1637 = logic_pb2.Value(string_value=v)
        return _t1637

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1638 = logic_pb2.Value(boolean_value=v)
        return _t1638

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1639 = logic_pb2.Value(uint128_value=v)
        return _t1639

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1640 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1640,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1641 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1641,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1642 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1642,))
        _t1643 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1643,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1644 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1644,))
        _t1645 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1645,))
        if msg.new_line != "":
            _t1646 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1646,))
        _t1647 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1647,))
        _t1648 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1648,))
        _t1649 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1649,))
        if msg.comment != "":
            _t1650 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1650,))
        for missing_string in msg.missing_strings:
            _t1651 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1651,))
        _t1652 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1652,))
        _t1653 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1653,))
        _t1654 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1654,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1655 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1655,))
        _t1656 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1656,))
        _t1657 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1657,))
        _t1658 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1658,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1659 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1659,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1660 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1660,))
        _t1661 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1661,))
        _t1662 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1662,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1663 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1663,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1664 = self._make_value_string(msg.compression)
            result.append(("compression", _t1664,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1665 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1665,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1666 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1666,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1667 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1667,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1668 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1668,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1669 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1669,))
        return sorted(result)

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> Optional[str]:
        name = self.relation_id_to_string(msg)
        if name != "":
            return name
        else:
            _t1670 = None
        return None

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name == "":
            return self.relation_id_to_uint128(msg)
        else:
            _t1671 = None
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
        flat631 = self._try_flat(msg, self.pretty_transaction)
        if flat631 is not None:
            assert flat631 is not None
            self.write(flat631)
            return None
        else:
            def _t1244(_dollar_dollar):
                if _dollar_dollar.HasField("configure"):
                    _t1245 = _dollar_dollar.configure
                else:
                    _t1245 = None
                if _dollar_dollar.HasField("sync"):
                    _t1246 = _dollar_dollar.sync
                else:
                    _t1246 = None
                return (_t1245, _t1246, _dollar_dollar.epochs,)
            _t1247 = _t1244(msg)
            fields622 = _t1247
            assert fields622 is not None
            unwrapped_fields623 = fields622
            self.write("(")
            self.write("transaction")
            self.indent_sexp()
            field624 = unwrapped_fields623[0]
            if field624 is not None:
                self.newline()
                assert field624 is not None
                opt_val625 = field624
                self.pretty_configure(opt_val625)
            field626 = unwrapped_fields623[1]
            if field626 is not None:
                self.newline()
                assert field626 is not None
                opt_val627 = field626
                self.pretty_sync(opt_val627)
            field628 = unwrapped_fields623[2]
            if not len(field628) == 0:
                self.newline()
                for i630, elem629 in enumerate(field628):
                    if (i630 > 0):
                        self.newline()
                    self.pretty_epoch(elem629)
            self.dedent()
            self.write(")")

    def pretty_configure(self, msg: transactions_pb2.Configure):
        flat634 = self._try_flat(msg, self.pretty_configure)
        if flat634 is not None:
            assert flat634 is not None
            self.write(flat634)
            return None
        else:
            def _t1248(_dollar_dollar):
                _t1249 = self.deconstruct_configure(_dollar_dollar)
                return _t1249
            _t1250 = _t1248(msg)
            fields632 = _t1250
            assert fields632 is not None
            unwrapped_fields633 = fields632
            self.write("(")
            self.write("configure")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields633)
            self.dedent()
            self.write(")")

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]):
        flat638 = self._try_flat(msg, self.pretty_config_dict)
        if flat638 is not None:
            assert flat638 is not None
            self.write(flat638)
            return None
        else:
            fields635 = msg
            self.write("{")
            self.indent()
            if not len(fields635) == 0:
                self.newline()
                for i637, elem636 in enumerate(fields635):
                    if (i637 > 0):
                        self.newline()
                    self.pretty_config_key_value(elem636)
            self.dedent()
            self.write("}")

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]):
        flat643 = self._try_flat(msg, self.pretty_config_key_value)
        if flat643 is not None:
            assert flat643 is not None
            self.write(flat643)
            return None
        else:
            def _t1251(_dollar_dollar):
                return (_dollar_dollar[0], _dollar_dollar[1],)
            _t1252 = _t1251(msg)
            fields639 = _t1252
            assert fields639 is not None
            unwrapped_fields640 = fields639
            self.write(":")
            field641 = unwrapped_fields640[0]
            self.write(field641)
            self.write(" ")
            field642 = unwrapped_fields640[1]
            self.pretty_value(field642)

    def pretty_value(self, msg: logic_pb2.Value):
        flat663 = self._try_flat(msg, self.pretty_value)
        if flat663 is not None:
            assert flat663 is not None
            self.write(flat663)
            return None
        else:
            def _t1253(_dollar_dollar):
                if _dollar_dollar.HasField("date_value"):
                    _t1254 = _dollar_dollar.date_value
                else:
                    _t1254 = None
                return _t1254
            _t1255 = _t1253(msg)
            deconstruct_result661 = _t1255
            if deconstruct_result661 is not None:
                assert deconstruct_result661 is not None
                unwrapped662 = deconstruct_result661
                self.pretty_date(unwrapped662)
            else:
                def _t1256(_dollar_dollar):
                    if _dollar_dollar.HasField("datetime_value"):
                        _t1257 = _dollar_dollar.datetime_value
                    else:
                        _t1257 = None
                    return _t1257
                _t1258 = _t1256(msg)
                deconstruct_result659 = _t1258
                if deconstruct_result659 is not None:
                    assert deconstruct_result659 is not None
                    unwrapped660 = deconstruct_result659
                    self.pretty_datetime(unwrapped660)
                else:
                    def _t1259(_dollar_dollar):
                        if _dollar_dollar.HasField("string_value"):
                            _t1260 = _dollar_dollar.string_value
                        else:
                            _t1260 = None
                        return _t1260
                    _t1261 = _t1259(msg)
                    deconstruct_result657 = _t1261
                    if deconstruct_result657 is not None:
                        assert deconstruct_result657 is not None
                        unwrapped658 = deconstruct_result657
                        self.write(self.format_string_value(unwrapped658))
                    else:
                        def _t1262(_dollar_dollar):
                            if _dollar_dollar.HasField("int_value"):
                                _t1263 = _dollar_dollar.int_value
                            else:
                                _t1263 = None
                            return _t1263
                        _t1264 = _t1262(msg)
                        deconstruct_result655 = _t1264
                        if deconstruct_result655 is not None:
                            assert deconstruct_result655 is not None
                            unwrapped656 = deconstruct_result655
                            self.write(str(unwrapped656))
                        else:
                            def _t1265(_dollar_dollar):
                                if _dollar_dollar.HasField("float_value"):
                                    _t1266 = _dollar_dollar.float_value
                                else:
                                    _t1266 = None
                                return _t1266
                            _t1267 = _t1265(msg)
                            deconstruct_result653 = _t1267
                            if deconstruct_result653 is not None:
                                assert deconstruct_result653 is not None
                                unwrapped654 = deconstruct_result653
                                self.write(str(unwrapped654))
                            else:
                                def _t1268(_dollar_dollar):
                                    if _dollar_dollar.HasField("uint128_value"):
                                        _t1269 = _dollar_dollar.uint128_value
                                    else:
                                        _t1269 = None
                                    return _t1269
                                _t1270 = _t1268(msg)
                                deconstruct_result651 = _t1270
                                if deconstruct_result651 is not None:
                                    assert deconstruct_result651 is not None
                                    unwrapped652 = deconstruct_result651
                                    self.write(self.format_uint128(unwrapped652))
                                else:
                                    def _t1271(_dollar_dollar):
                                        if _dollar_dollar.HasField("int128_value"):
                                            _t1272 = _dollar_dollar.int128_value
                                        else:
                                            _t1272 = None
                                        return _t1272
                                    _t1273 = _t1271(msg)
                                    deconstruct_result649 = _t1273
                                    if deconstruct_result649 is not None:
                                        assert deconstruct_result649 is not None
                                        unwrapped650 = deconstruct_result649
                                        self.write(self.format_int128(unwrapped650))
                                    else:
                                        def _t1274(_dollar_dollar):
                                            if _dollar_dollar.HasField("decimal_value"):
                                                _t1275 = _dollar_dollar.decimal_value
                                            else:
                                                _t1275 = None
                                            return _t1275
                                        _t1276 = _t1274(msg)
                                        deconstruct_result647 = _t1276
                                        if deconstruct_result647 is not None:
                                            assert deconstruct_result647 is not None
                                            unwrapped648 = deconstruct_result647
                                            self.write(self.format_decimal(unwrapped648))
                                        else:
                                            def _t1277(_dollar_dollar):
                                                if _dollar_dollar.HasField("boolean_value"):
                                                    _t1278 = _dollar_dollar.boolean_value
                                                else:
                                                    _t1278 = None
                                                return _t1278
                                            _t1279 = _t1277(msg)
                                            deconstruct_result645 = _t1279
                                            if deconstruct_result645 is not None:
                                                assert deconstruct_result645 is not None
                                                unwrapped646 = deconstruct_result645
                                                self.pretty_boolean_value(unwrapped646)
                                            else:
                                                fields644 = msg
                                                self.write("missing")

    def pretty_date(self, msg: logic_pb2.DateValue):
        flat669 = self._try_flat(msg, self.pretty_date)
        if flat669 is not None:
            assert flat669 is not None
            self.write(flat669)
            return None
        else:
            def _t1280(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
            _t1281 = _t1280(msg)
            fields664 = _t1281
            assert fields664 is not None
            unwrapped_fields665 = fields664
            self.write("(")
            self.write("date")
            self.indent_sexp()
            self.newline()
            field666 = unwrapped_fields665[0]
            self.write(str(field666))
            self.newline()
            field667 = unwrapped_fields665[1]
            self.write(str(field667))
            self.newline()
            field668 = unwrapped_fields665[2]
            self.write(str(field668))
            self.dedent()
            self.write(")")

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue):
        flat680 = self._try_flat(msg, self.pretty_datetime)
        if flat680 is not None:
            assert flat680 is not None
            self.write(flat680)
            return None
        else:
            def _t1282(_dollar_dollar):
                return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
            _t1283 = _t1282(msg)
            fields670 = _t1283
            assert fields670 is not None
            unwrapped_fields671 = fields670
            self.write("(")
            self.write("datetime")
            self.indent_sexp()
            self.newline()
            field672 = unwrapped_fields671[0]
            self.write(str(field672))
            self.newline()
            field673 = unwrapped_fields671[1]
            self.write(str(field673))
            self.newline()
            field674 = unwrapped_fields671[2]
            self.write(str(field674))
            self.newline()
            field675 = unwrapped_fields671[3]
            self.write(str(field675))
            self.newline()
            field676 = unwrapped_fields671[4]
            self.write(str(field676))
            self.newline()
            field677 = unwrapped_fields671[5]
            self.write(str(field677))
            field678 = unwrapped_fields671[6]
            if field678 is not None:
                self.newline()
                assert field678 is not None
                opt_val679 = field678
                self.write(str(opt_val679))
            self.dedent()
            self.write(")")

    def pretty_boolean_value(self, msg: bool):
        def _t1284(_dollar_dollar):
            if _dollar_dollar:
                _t1285 = ()
            else:
                _t1285 = None
            return _t1285
        _t1286 = _t1284(msg)
        deconstruct_result683 = _t1286
        if deconstruct_result683 is not None:
            assert deconstruct_result683 is not None
            unwrapped684 = deconstruct_result683
            self.write("true")
        else:
            def _t1287(_dollar_dollar):
                if not _dollar_dollar:
                    _t1288 = ()
                else:
                    _t1288 = None
                return _t1288
            _t1289 = _t1287(msg)
            deconstruct_result681 = _t1289
            if deconstruct_result681 is not None:
                assert deconstruct_result681 is not None
                unwrapped682 = deconstruct_result681
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")

    def pretty_sync(self, msg: transactions_pb2.Sync):
        flat689 = self._try_flat(msg, self.pretty_sync)
        if flat689 is not None:
            assert flat689 is not None
            self.write(flat689)
            return None
        else:
            def _t1290(_dollar_dollar):
                return _dollar_dollar.fragments
            _t1291 = _t1290(msg)
            fields685 = _t1291
            assert fields685 is not None
            unwrapped_fields686 = fields685
            self.write("(")
            self.write("sync")
            self.indent_sexp()
            if not len(unwrapped_fields686) == 0:
                self.newline()
                for i688, elem687 in enumerate(unwrapped_fields686):
                    if (i688 > 0):
                        self.newline()
                    self.pretty_fragment_id(elem687)
            self.dedent()
            self.write(")")

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat692 = self._try_flat(msg, self.pretty_fragment_id)
        if flat692 is not None:
            assert flat692 is not None
            self.write(flat692)
            return None
        else:
            def _t1292(_dollar_dollar):
                return self.fragment_id_to_string(_dollar_dollar)
            _t1293 = _t1292(msg)
            fields690 = _t1293
            assert fields690 is not None
            unwrapped_fields691 = fields690
            self.write(":")
            self.write(unwrapped_fields691)

    def pretty_epoch(self, msg: transactions_pb2.Epoch):
        flat699 = self._try_flat(msg, self.pretty_epoch)
        if flat699 is not None:
            assert flat699 is not None
            self.write(flat699)
            return None
        else:
            def _t1294(_dollar_dollar):
                if not len(_dollar_dollar.writes) == 0:
                    _t1295 = _dollar_dollar.writes
                else:
                    _t1295 = None
                if not len(_dollar_dollar.reads) == 0:
                    _t1296 = _dollar_dollar.reads
                else:
                    _t1296 = None
                return (_t1295, _t1296,)
            _t1297 = _t1294(msg)
            fields693 = _t1297
            assert fields693 is not None
            unwrapped_fields694 = fields693
            self.write("(")
            self.write("epoch")
            self.indent_sexp()
            field695 = unwrapped_fields694[0]
            if field695 is not None:
                self.newline()
                assert field695 is not None
                opt_val696 = field695
                self.pretty_epoch_writes(opt_val696)
            field697 = unwrapped_fields694[1]
            if field697 is not None:
                self.newline()
                assert field697 is not None
                opt_val698 = field697
                self.pretty_epoch_reads(opt_val698)
            self.dedent()
            self.write(")")

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]):
        flat703 = self._try_flat(msg, self.pretty_epoch_writes)
        if flat703 is not None:
            assert flat703 is not None
            self.write(flat703)
            return None
        else:
            fields700 = msg
            self.write("(")
            self.write("writes")
            self.indent_sexp()
            if not len(fields700) == 0:
                self.newline()
                for i702, elem701 in enumerate(fields700):
                    if (i702 > 0):
                        self.newline()
                    self.pretty_write(elem701)
            self.dedent()
            self.write(")")

    def pretty_write(self, msg: transactions_pb2.Write):
        flat710 = self._try_flat(msg, self.pretty_write)
        if flat710 is not None:
            assert flat710 is not None
            self.write(flat710)
            return None
        else:
            def _t1298(_dollar_dollar):
                if _dollar_dollar.HasField("define"):
                    _t1299 = _dollar_dollar.define
                else:
                    _t1299 = None
                return _t1299
            _t1300 = _t1298(msg)
            deconstruct_result708 = _t1300
            if deconstruct_result708 is not None:
                assert deconstruct_result708 is not None
                unwrapped709 = deconstruct_result708
                self.pretty_define(unwrapped709)
            else:
                def _t1301(_dollar_dollar):
                    if _dollar_dollar.HasField("undefine"):
                        _t1302 = _dollar_dollar.undefine
                    else:
                        _t1302 = None
                    return _t1302
                _t1303 = _t1301(msg)
                deconstruct_result706 = _t1303
                if deconstruct_result706 is not None:
                    assert deconstruct_result706 is not None
                    unwrapped707 = deconstruct_result706
                    self.pretty_undefine(unwrapped707)
                else:
                    def _t1304(_dollar_dollar):
                        if _dollar_dollar.HasField("context"):
                            _t1305 = _dollar_dollar.context
                        else:
                            _t1305 = None
                        return _t1305
                    _t1306 = _t1304(msg)
                    deconstruct_result704 = _t1306
                    if deconstruct_result704 is not None:
                        assert deconstruct_result704 is not None
                        unwrapped705 = deconstruct_result704
                        self.pretty_context(unwrapped705)
                    else:
                        raise ParseError("No matching rule for write")

    def pretty_define(self, msg: transactions_pb2.Define):
        flat713 = self._try_flat(msg, self.pretty_define)
        if flat713 is not None:
            assert flat713 is not None
            self.write(flat713)
            return None
        else:
            def _t1307(_dollar_dollar):
                return _dollar_dollar.fragment
            _t1308 = _t1307(msg)
            fields711 = _t1308
            assert fields711 is not None
            unwrapped_fields712 = fields711
            self.write("(")
            self.write("define")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment(unwrapped_fields712)
            self.dedent()
            self.write(")")

    def pretty_fragment(self, msg: fragments_pb2.Fragment):
        flat720 = self._try_flat(msg, self.pretty_fragment)
        if flat720 is not None:
            assert flat720 is not None
            self.write(flat720)
            return None
        else:
            def _t1309(_dollar_dollar):
                self.start_pretty_fragment(_dollar_dollar)
                return (_dollar_dollar.id, _dollar_dollar.declarations,)
            _t1310 = _t1309(msg)
            fields714 = _t1310
            assert fields714 is not None
            unwrapped_fields715 = fields714
            self.write("(")
            self.write("fragment")
            self.indent_sexp()
            self.newline()
            field716 = unwrapped_fields715[0]
            self.pretty_new_fragment_id(field716)
            field717 = unwrapped_fields715[1]
            if not len(field717) == 0:
                self.newline()
                for i719, elem718 in enumerate(field717):
                    if (i719 > 0):
                        self.newline()
                    self.pretty_declaration(elem718)
            self.dedent()
            self.write(")")

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId):
        flat722 = self._try_flat(msg, self.pretty_new_fragment_id)
        if flat722 is not None:
            assert flat722 is not None
            self.write(flat722)
            return None
        else:
            fields721 = msg
            self.pretty_fragment_id(fields721)

    def pretty_declaration(self, msg: logic_pb2.Declaration):
        flat731 = self._try_flat(msg, self.pretty_declaration)
        if flat731 is not None:
            assert flat731 is not None
            self.write(flat731)
            return None
        else:
            def _t1311(_dollar_dollar):
                if _dollar_dollar.HasField("def"):
                    _t1312 = getattr(_dollar_dollar, 'def')
                else:
                    _t1312 = None
                return _t1312
            _t1313 = _t1311(msg)
            deconstruct_result729 = _t1313
            if deconstruct_result729 is not None:
                assert deconstruct_result729 is not None
                unwrapped730 = deconstruct_result729
                self.pretty_def(unwrapped730)
            else:
                def _t1314(_dollar_dollar):
                    if _dollar_dollar.HasField("algorithm"):
                        _t1315 = _dollar_dollar.algorithm
                    else:
                        _t1315 = None
                    return _t1315
                _t1316 = _t1314(msg)
                deconstruct_result727 = _t1316
                if deconstruct_result727 is not None:
                    assert deconstruct_result727 is not None
                    unwrapped728 = deconstruct_result727
                    self.pretty_algorithm(unwrapped728)
                else:
                    def _t1317(_dollar_dollar):
                        if _dollar_dollar.HasField("constraint"):
                            _t1318 = _dollar_dollar.constraint
                        else:
                            _t1318 = None
                        return _t1318
                    _t1319 = _t1317(msg)
                    deconstruct_result725 = _t1319
                    if deconstruct_result725 is not None:
                        assert deconstruct_result725 is not None
                        unwrapped726 = deconstruct_result725
                        self.pretty_constraint(unwrapped726)
                    else:
                        def _t1320(_dollar_dollar):
                            if _dollar_dollar.HasField("data"):
                                _t1321 = _dollar_dollar.data
                            else:
                                _t1321 = None
                            return _t1321
                        _t1322 = _t1320(msg)
                        deconstruct_result723 = _t1322
                        if deconstruct_result723 is not None:
                            assert deconstruct_result723 is not None
                            unwrapped724 = deconstruct_result723
                            self.pretty_data(unwrapped724)
                        else:
                            raise ParseError("No matching rule for declaration")

    def pretty_def(self, msg: logic_pb2.Def):
        flat738 = self._try_flat(msg, self.pretty_def)
        if flat738 is not None:
            assert flat738 is not None
            self.write(flat738)
            return None
        else:
            def _t1323(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1324 = _dollar_dollar.attrs
                else:
                    _t1324 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1324,)
            _t1325 = _t1323(msg)
            fields732 = _t1325
            assert fields732 is not None
            unwrapped_fields733 = fields732
            self.write("(")
            self.write("def")
            self.indent_sexp()
            self.newline()
            field734 = unwrapped_fields733[0]
            self.pretty_relation_id(field734)
            self.newline()
            field735 = unwrapped_fields733[1]
            self.pretty_abstraction(field735)
            field736 = unwrapped_fields733[2]
            if field736 is not None:
                self.newline()
                assert field736 is not None
                opt_val737 = field736
                self.pretty_attrs(opt_val737)
            self.dedent()
            self.write(")")

    def pretty_relation_id(self, msg: logic_pb2.RelationId):
        flat743 = self._try_flat(msg, self.pretty_relation_id)
        if flat743 is not None:
            assert flat743 is not None
            self.write(flat743)
            return None
        else:
            def _t1326(_dollar_dollar):
                _t1327 = self.deconstruct_relation_id_string(_dollar_dollar)
                return _t1327
            _t1328 = _t1326(msg)
            deconstruct_result741 = _t1328
            if deconstruct_result741 is not None:
                assert deconstruct_result741 is not None
                unwrapped742 = deconstruct_result741
                self.write(":")
                self.write(unwrapped742)
            else:
                def _t1329(_dollar_dollar):
                    _t1330 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                    return _t1330
                _t1331 = _t1329(msg)
                deconstruct_result739 = _t1331
                if deconstruct_result739 is not None:
                    assert deconstruct_result739 is not None
                    unwrapped740 = deconstruct_result739
                    self.write(self.format_uint128(unwrapped740))
                else:
                    raise ParseError("No matching rule for relation_id")

    def pretty_abstraction(self, msg: logic_pb2.Abstraction):
        flat748 = self._try_flat(msg, self.pretty_abstraction)
        if flat748 is not None:
            assert flat748 is not None
            self.write(flat748)
            return None
        else:
            def _t1332(_dollar_dollar):
                _t1333 = self.deconstruct_bindings(_dollar_dollar)
                return (_t1333, _dollar_dollar.value,)
            _t1334 = _t1332(msg)
            fields744 = _t1334
            assert fields744 is not None
            unwrapped_fields745 = fields744
            self.write("(")
            self.indent()
            field746 = unwrapped_fields745[0]
            self.pretty_bindings(field746)
            self.newline()
            field747 = unwrapped_fields745[1]
            self.pretty_formula(field747)
            self.dedent()
            self.write(")")

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]):
        flat756 = self._try_flat(msg, self.pretty_bindings)
        if flat756 is not None:
            assert flat756 is not None
            self.write(flat756)
            return None
        else:
            def _t1335(_dollar_dollar):
                if not len(_dollar_dollar[1]) == 0:
                    _t1336 = _dollar_dollar[1]
                else:
                    _t1336 = None
                return (_dollar_dollar[0], _t1336,)
            _t1337 = _t1335(msg)
            fields749 = _t1337
            assert fields749 is not None
            unwrapped_fields750 = fields749
            self.write("[")
            self.indent()
            field751 = unwrapped_fields750[0]
            for i753, elem752 in enumerate(field751):
                if (i753 > 0):
                    self.newline()
                self.pretty_binding(elem752)
            field754 = unwrapped_fields750[1]
            if field754 is not None:
                self.newline()
                assert field754 is not None
                opt_val755 = field754
                self.pretty_value_bindings(opt_val755)
            self.dedent()
            self.write("]")

    def pretty_binding(self, msg: logic_pb2.Binding):
        flat761 = self._try_flat(msg, self.pretty_binding)
        if flat761 is not None:
            assert flat761 is not None
            self.write(flat761)
            return None
        else:
            def _t1338(_dollar_dollar):
                return (_dollar_dollar.var.name, _dollar_dollar.type,)
            _t1339 = _t1338(msg)
            fields757 = _t1339
            assert fields757 is not None
            unwrapped_fields758 = fields757
            field759 = unwrapped_fields758[0]
            self.write(field759)
            self.write("::")
            field760 = unwrapped_fields758[1]
            self.pretty_type(field760)

    def pretty_type(self, msg: logic_pb2.Type):
        flat784 = self._try_flat(msg, self.pretty_type)
        if flat784 is not None:
            assert flat784 is not None
            self.write(flat784)
            return None
        else:
            def _t1340(_dollar_dollar):
                if _dollar_dollar.HasField("unspecified_type"):
                    _t1341 = _dollar_dollar.unspecified_type
                else:
                    _t1341 = None
                return _t1341
            _t1342 = _t1340(msg)
            deconstruct_result782 = _t1342
            if deconstruct_result782 is not None:
                assert deconstruct_result782 is not None
                unwrapped783 = deconstruct_result782
                self.pretty_unspecified_type(unwrapped783)
            else:
                def _t1343(_dollar_dollar):
                    if _dollar_dollar.HasField("string_type"):
                        _t1344 = _dollar_dollar.string_type
                    else:
                        _t1344 = None
                    return _t1344
                _t1345 = _t1343(msg)
                deconstruct_result780 = _t1345
                if deconstruct_result780 is not None:
                    assert deconstruct_result780 is not None
                    unwrapped781 = deconstruct_result780
                    self.pretty_string_type(unwrapped781)
                else:
                    def _t1346(_dollar_dollar):
                        if _dollar_dollar.HasField("int_type"):
                            _t1347 = _dollar_dollar.int_type
                        else:
                            _t1347 = None
                        return _t1347
                    _t1348 = _t1346(msg)
                    deconstruct_result778 = _t1348
                    if deconstruct_result778 is not None:
                        assert deconstruct_result778 is not None
                        unwrapped779 = deconstruct_result778
                        self.pretty_int_type(unwrapped779)
                    else:
                        def _t1349(_dollar_dollar):
                            if _dollar_dollar.HasField("float_type"):
                                _t1350 = _dollar_dollar.float_type
                            else:
                                _t1350 = None
                            return _t1350
                        _t1351 = _t1349(msg)
                        deconstruct_result776 = _t1351
                        if deconstruct_result776 is not None:
                            assert deconstruct_result776 is not None
                            unwrapped777 = deconstruct_result776
                            self.pretty_float_type(unwrapped777)
                        else:
                            def _t1352(_dollar_dollar):
                                if _dollar_dollar.HasField("uint128_type"):
                                    _t1353 = _dollar_dollar.uint128_type
                                else:
                                    _t1353 = None
                                return _t1353
                            _t1354 = _t1352(msg)
                            deconstruct_result774 = _t1354
                            if deconstruct_result774 is not None:
                                assert deconstruct_result774 is not None
                                unwrapped775 = deconstruct_result774
                                self.pretty_uint128_type(unwrapped775)
                            else:
                                def _t1355(_dollar_dollar):
                                    if _dollar_dollar.HasField("int128_type"):
                                        _t1356 = _dollar_dollar.int128_type
                                    else:
                                        _t1356 = None
                                    return _t1356
                                _t1357 = _t1355(msg)
                                deconstruct_result772 = _t1357
                                if deconstruct_result772 is not None:
                                    assert deconstruct_result772 is not None
                                    unwrapped773 = deconstruct_result772
                                    self.pretty_int128_type(unwrapped773)
                                else:
                                    def _t1358(_dollar_dollar):
                                        if _dollar_dollar.HasField("date_type"):
                                            _t1359 = _dollar_dollar.date_type
                                        else:
                                            _t1359 = None
                                        return _t1359
                                    _t1360 = _t1358(msg)
                                    deconstruct_result770 = _t1360
                                    if deconstruct_result770 is not None:
                                        assert deconstruct_result770 is not None
                                        unwrapped771 = deconstruct_result770
                                        self.pretty_date_type(unwrapped771)
                                    else:
                                        def _t1361(_dollar_dollar):
                                            if _dollar_dollar.HasField("datetime_type"):
                                                _t1362 = _dollar_dollar.datetime_type
                                            else:
                                                _t1362 = None
                                            return _t1362
                                        _t1363 = _t1361(msg)
                                        deconstruct_result768 = _t1363
                                        if deconstruct_result768 is not None:
                                            assert deconstruct_result768 is not None
                                            unwrapped769 = deconstruct_result768
                                            self.pretty_datetime_type(unwrapped769)
                                        else:
                                            def _t1364(_dollar_dollar):
                                                if _dollar_dollar.HasField("missing_type"):
                                                    _t1365 = _dollar_dollar.missing_type
                                                else:
                                                    _t1365 = None
                                                return _t1365
                                            _t1366 = _t1364(msg)
                                            deconstruct_result766 = _t1366
                                            if deconstruct_result766 is not None:
                                                assert deconstruct_result766 is not None
                                                unwrapped767 = deconstruct_result766
                                                self.pretty_missing_type(unwrapped767)
                                            else:
                                                def _t1367(_dollar_dollar):
                                                    if _dollar_dollar.HasField("decimal_type"):
                                                        _t1368 = _dollar_dollar.decimal_type
                                                    else:
                                                        _t1368 = None
                                                    return _t1368
                                                _t1369 = _t1367(msg)
                                                deconstruct_result764 = _t1369
                                                if deconstruct_result764 is not None:
                                                    assert deconstruct_result764 is not None
                                                    unwrapped765 = deconstruct_result764
                                                    self.pretty_decimal_type(unwrapped765)
                                                else:
                                                    def _t1370(_dollar_dollar):
                                                        if _dollar_dollar.HasField("boolean_type"):
                                                            _t1371 = _dollar_dollar.boolean_type
                                                        else:
                                                            _t1371 = None
                                                        return _t1371
                                                    _t1372 = _t1370(msg)
                                                    deconstruct_result762 = _t1372
                                                    if deconstruct_result762 is not None:
                                                        assert deconstruct_result762 is not None
                                                        unwrapped763 = deconstruct_result762
                                                        self.pretty_boolean_type(unwrapped763)
                                                    else:
                                                        raise ParseError("No matching rule for type")

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType):
        fields785 = msg
        self.write("UNKNOWN")

    def pretty_string_type(self, msg: logic_pb2.StringType):
        fields786 = msg
        self.write("STRING")

    def pretty_int_type(self, msg: logic_pb2.IntType):
        fields787 = msg
        self.write("INT")

    def pretty_float_type(self, msg: logic_pb2.FloatType):
        fields788 = msg
        self.write("FLOAT")

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type):
        fields789 = msg
        self.write("UINT128")

    def pretty_int128_type(self, msg: logic_pb2.Int128Type):
        fields790 = msg
        self.write("INT128")

    def pretty_date_type(self, msg: logic_pb2.DateType):
        fields791 = msg
        self.write("DATE")

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType):
        fields792 = msg
        self.write("DATETIME")

    def pretty_missing_type(self, msg: logic_pb2.MissingType):
        fields793 = msg
        self.write("MISSING")

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType):
        flat798 = self._try_flat(msg, self.pretty_decimal_type)
        if flat798 is not None:
            assert flat798 is not None
            self.write(flat798)
            return None
        else:
            def _t1373(_dollar_dollar):
                return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
            _t1374 = _t1373(msg)
            fields794 = _t1374
            assert fields794 is not None
            unwrapped_fields795 = fields794
            self.write("(")
            self.write("DECIMAL")
            self.indent_sexp()
            self.newline()
            field796 = unwrapped_fields795[0]
            self.write(str(field796))
            self.newline()
            field797 = unwrapped_fields795[1]
            self.write(str(field797))
            self.dedent()
            self.write(")")

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType):
        fields799 = msg
        self.write("BOOLEAN")

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]):
        flat803 = self._try_flat(msg, self.pretty_value_bindings)
        if flat803 is not None:
            assert flat803 is not None
            self.write(flat803)
            return None
        else:
            fields800 = msg
            self.write("|")
            if not len(fields800) == 0:
                self.write(" ")
                for i802, elem801 in enumerate(fields800):
                    if (i802 > 0):
                        self.newline()
                    self.pretty_binding(elem801)

    def pretty_formula(self, msg: logic_pb2.Formula):
        flat830 = self._try_flat(msg, self.pretty_formula)
        if flat830 is not None:
            assert flat830 is not None
            self.write(flat830)
            return None
        else:
            def _t1375(_dollar_dollar):
                if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                    _t1376 = _dollar_dollar.conjunction
                else:
                    _t1376 = None
                return _t1376
            _t1377 = _t1375(msg)
            deconstruct_result828 = _t1377
            if deconstruct_result828 is not None:
                assert deconstruct_result828 is not None
                unwrapped829 = deconstruct_result828
                self.pretty_true(unwrapped829)
            else:
                def _t1378(_dollar_dollar):
                    if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                        _t1379 = _dollar_dollar.disjunction
                    else:
                        _t1379 = None
                    return _t1379
                _t1380 = _t1378(msg)
                deconstruct_result826 = _t1380
                if deconstruct_result826 is not None:
                    assert deconstruct_result826 is not None
                    unwrapped827 = deconstruct_result826
                    self.pretty_false(unwrapped827)
                else:
                    def _t1381(_dollar_dollar):
                        if _dollar_dollar.HasField("exists"):
                            _t1382 = _dollar_dollar.exists
                        else:
                            _t1382 = None
                        return _t1382
                    _t1383 = _t1381(msg)
                    deconstruct_result824 = _t1383
                    if deconstruct_result824 is not None:
                        assert deconstruct_result824 is not None
                        unwrapped825 = deconstruct_result824
                        self.pretty_exists(unwrapped825)
                    else:
                        def _t1384(_dollar_dollar):
                            if _dollar_dollar.HasField("reduce"):
                                _t1385 = _dollar_dollar.reduce
                            else:
                                _t1385 = None
                            return _t1385
                        _t1386 = _t1384(msg)
                        deconstruct_result822 = _t1386
                        if deconstruct_result822 is not None:
                            assert deconstruct_result822 is not None
                            unwrapped823 = deconstruct_result822
                            self.pretty_reduce(unwrapped823)
                        else:
                            def _t1387(_dollar_dollar):
                                if _dollar_dollar.HasField("conjunction"):
                                    _t1388 = _dollar_dollar.conjunction
                                else:
                                    _t1388 = None
                                return _t1388
                            _t1389 = _t1387(msg)
                            deconstruct_result820 = _t1389
                            if deconstruct_result820 is not None:
                                assert deconstruct_result820 is not None
                                unwrapped821 = deconstruct_result820
                                self.pretty_conjunction(unwrapped821)
                            else:
                                def _t1390(_dollar_dollar):
                                    if _dollar_dollar.HasField("disjunction"):
                                        _t1391 = _dollar_dollar.disjunction
                                    else:
                                        _t1391 = None
                                    return _t1391
                                _t1392 = _t1390(msg)
                                deconstruct_result818 = _t1392
                                if deconstruct_result818 is not None:
                                    assert deconstruct_result818 is not None
                                    unwrapped819 = deconstruct_result818
                                    self.pretty_disjunction(unwrapped819)
                                else:
                                    def _t1393(_dollar_dollar):
                                        if _dollar_dollar.HasField("not"):
                                            _t1394 = getattr(_dollar_dollar, 'not')
                                        else:
                                            _t1394 = None
                                        return _t1394
                                    _t1395 = _t1393(msg)
                                    deconstruct_result816 = _t1395
                                    if deconstruct_result816 is not None:
                                        assert deconstruct_result816 is not None
                                        unwrapped817 = deconstruct_result816
                                        self.pretty_not(unwrapped817)
                                    else:
                                        def _t1396(_dollar_dollar):
                                            if _dollar_dollar.HasField("ffi"):
                                                _t1397 = _dollar_dollar.ffi
                                            else:
                                                _t1397 = None
                                            return _t1397
                                        _t1398 = _t1396(msg)
                                        deconstruct_result814 = _t1398
                                        if deconstruct_result814 is not None:
                                            assert deconstruct_result814 is not None
                                            unwrapped815 = deconstruct_result814
                                            self.pretty_ffi(unwrapped815)
                                        else:
                                            def _t1399(_dollar_dollar):
                                                if _dollar_dollar.HasField("atom"):
                                                    _t1400 = _dollar_dollar.atom
                                                else:
                                                    _t1400 = None
                                                return _t1400
                                            _t1401 = _t1399(msg)
                                            deconstruct_result812 = _t1401
                                            if deconstruct_result812 is not None:
                                                assert deconstruct_result812 is not None
                                                unwrapped813 = deconstruct_result812
                                                self.pretty_atom(unwrapped813)
                                            else:
                                                def _t1402(_dollar_dollar):
                                                    if _dollar_dollar.HasField("pragma"):
                                                        _t1403 = _dollar_dollar.pragma
                                                    else:
                                                        _t1403 = None
                                                    return _t1403
                                                _t1404 = _t1402(msg)
                                                deconstruct_result810 = _t1404
                                                if deconstruct_result810 is not None:
                                                    assert deconstruct_result810 is not None
                                                    unwrapped811 = deconstruct_result810
                                                    self.pretty_pragma(unwrapped811)
                                                else:
                                                    def _t1405(_dollar_dollar):
                                                        if _dollar_dollar.HasField("primitive"):
                                                            _t1406 = _dollar_dollar.primitive
                                                        else:
                                                            _t1406 = None
                                                        return _t1406
                                                    _t1407 = _t1405(msg)
                                                    deconstruct_result808 = _t1407
                                                    if deconstruct_result808 is not None:
                                                        assert deconstruct_result808 is not None
                                                        unwrapped809 = deconstruct_result808
                                                        self.pretty_primitive(unwrapped809)
                                                    else:
                                                        def _t1408(_dollar_dollar):
                                                            if _dollar_dollar.HasField("rel_atom"):
                                                                _t1409 = _dollar_dollar.rel_atom
                                                            else:
                                                                _t1409 = None
                                                            return _t1409
                                                        _t1410 = _t1408(msg)
                                                        deconstruct_result806 = _t1410
                                                        if deconstruct_result806 is not None:
                                                            assert deconstruct_result806 is not None
                                                            unwrapped807 = deconstruct_result806
                                                            self.pretty_rel_atom(unwrapped807)
                                                        else:
                                                            def _t1411(_dollar_dollar):
                                                                if _dollar_dollar.HasField("cast"):
                                                                    _t1412 = _dollar_dollar.cast
                                                                else:
                                                                    _t1412 = None
                                                                return _t1412
                                                            _t1413 = _t1411(msg)
                                                            deconstruct_result804 = _t1413
                                                            if deconstruct_result804 is not None:
                                                                assert deconstruct_result804 is not None
                                                                unwrapped805 = deconstruct_result804
                                                                self.pretty_cast(unwrapped805)
                                                            else:
                                                                raise ParseError("No matching rule for formula")

    def pretty_true(self, msg: logic_pb2.Conjunction):
        fields831 = msg
        self.write("(")
        self.write("true")
        self.write(")")

    def pretty_false(self, msg: logic_pb2.Disjunction):
        fields832 = msg
        self.write("(")
        self.write("false")
        self.write(")")

    def pretty_exists(self, msg: logic_pb2.Exists):
        flat837 = self._try_flat(msg, self.pretty_exists)
        if flat837 is not None:
            assert flat837 is not None
            self.write(flat837)
            return None
        else:
            def _t1414(_dollar_dollar):
                _t1415 = self.deconstruct_bindings(_dollar_dollar.body)
                return (_t1415, _dollar_dollar.body.value,)
            _t1416 = _t1414(msg)
            fields833 = _t1416
            assert fields833 is not None
            unwrapped_fields834 = fields833
            self.write("(")
            self.write("exists")
            self.indent_sexp()
            self.newline()
            field835 = unwrapped_fields834[0]
            self.pretty_bindings(field835)
            self.newline()
            field836 = unwrapped_fields834[1]
            self.pretty_formula(field836)
            self.dedent()
            self.write(")")

    def pretty_reduce(self, msg: logic_pb2.Reduce):
        flat843 = self._try_flat(msg, self.pretty_reduce)
        if flat843 is not None:
            assert flat843 is not None
            self.write(flat843)
            return None
        else:
            def _t1417(_dollar_dollar):
                return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
            _t1418 = _t1417(msg)
            fields838 = _t1418
            assert fields838 is not None
            unwrapped_fields839 = fields838
            self.write("(")
            self.write("reduce")
            self.indent_sexp()
            self.newline()
            field840 = unwrapped_fields839[0]
            self.pretty_abstraction(field840)
            self.newline()
            field841 = unwrapped_fields839[1]
            self.pretty_abstraction(field841)
            self.newline()
            field842 = unwrapped_fields839[2]
            self.pretty_terms(field842)
            self.dedent()
            self.write(")")

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]):
        flat847 = self._try_flat(msg, self.pretty_terms)
        if flat847 is not None:
            assert flat847 is not None
            self.write(flat847)
            return None
        else:
            fields844 = msg
            self.write("(")
            self.write("terms")
            self.indent_sexp()
            if not len(fields844) == 0:
                self.newline()
                for i846, elem845 in enumerate(fields844):
                    if (i846 > 0):
                        self.newline()
                    self.pretty_term(elem845)
            self.dedent()
            self.write(")")

    def pretty_term(self, msg: logic_pb2.Term):
        flat852 = self._try_flat(msg, self.pretty_term)
        if flat852 is not None:
            assert flat852 is not None
            self.write(flat852)
            return None
        else:
            def _t1419(_dollar_dollar):
                if _dollar_dollar.HasField("var"):
                    _t1420 = _dollar_dollar.var
                else:
                    _t1420 = None
                return _t1420
            _t1421 = _t1419(msg)
            deconstruct_result850 = _t1421
            if deconstruct_result850 is not None:
                assert deconstruct_result850 is not None
                unwrapped851 = deconstruct_result850
                self.pretty_var(unwrapped851)
            else:
                def _t1422(_dollar_dollar):
                    if _dollar_dollar.HasField("constant"):
                        _t1423 = _dollar_dollar.constant
                    else:
                        _t1423 = None
                    return _t1423
                _t1424 = _t1422(msg)
                deconstruct_result848 = _t1424
                if deconstruct_result848 is not None:
                    assert deconstruct_result848 is not None
                    unwrapped849 = deconstruct_result848
                    self.pretty_constant(unwrapped849)
                else:
                    raise ParseError("No matching rule for term")

    def pretty_var(self, msg: logic_pb2.Var):
        flat855 = self._try_flat(msg, self.pretty_var)
        if flat855 is not None:
            assert flat855 is not None
            self.write(flat855)
            return None
        else:
            def _t1425(_dollar_dollar):
                return _dollar_dollar.name
            _t1426 = _t1425(msg)
            fields853 = _t1426
            assert fields853 is not None
            unwrapped_fields854 = fields853
            self.write(unwrapped_fields854)

    def pretty_constant(self, msg: logic_pb2.Value):
        flat857 = self._try_flat(msg, self.pretty_constant)
        if flat857 is not None:
            assert flat857 is not None
            self.write(flat857)
            return None
        else:
            fields856 = msg
            self.pretty_value(fields856)

    def pretty_conjunction(self, msg: logic_pb2.Conjunction):
        flat862 = self._try_flat(msg, self.pretty_conjunction)
        if flat862 is not None:
            assert flat862 is not None
            self.write(flat862)
            return None
        else:
            def _t1427(_dollar_dollar):
                return _dollar_dollar.args
            _t1428 = _t1427(msg)
            fields858 = _t1428
            assert fields858 is not None
            unwrapped_fields859 = fields858
            self.write("(")
            self.write("and")
            self.indent_sexp()
            if not len(unwrapped_fields859) == 0:
                self.newline()
                for i861, elem860 in enumerate(unwrapped_fields859):
                    if (i861 > 0):
                        self.newline()
                    self.pretty_formula(elem860)
            self.dedent()
            self.write(")")

    def pretty_disjunction(self, msg: logic_pb2.Disjunction):
        flat867 = self._try_flat(msg, self.pretty_disjunction)
        if flat867 is not None:
            assert flat867 is not None
            self.write(flat867)
            return None
        else:
            def _t1429(_dollar_dollar):
                return _dollar_dollar.args
            _t1430 = _t1429(msg)
            fields863 = _t1430
            assert fields863 is not None
            unwrapped_fields864 = fields863
            self.write("(")
            self.write("or")
            self.indent_sexp()
            if not len(unwrapped_fields864) == 0:
                self.newline()
                for i866, elem865 in enumerate(unwrapped_fields864):
                    if (i866 > 0):
                        self.newline()
                    self.pretty_formula(elem865)
            self.dedent()
            self.write(")")

    def pretty_not(self, msg: logic_pb2.Not):
        flat870 = self._try_flat(msg, self.pretty_not)
        if flat870 is not None:
            assert flat870 is not None
            self.write(flat870)
            return None
        else:
            def _t1431(_dollar_dollar):
                return _dollar_dollar.arg
            _t1432 = _t1431(msg)
            fields868 = _t1432
            assert fields868 is not None
            unwrapped_fields869 = fields868
            self.write("(")
            self.write("not")
            self.indent_sexp()
            self.newline()
            self.pretty_formula(unwrapped_fields869)
            self.dedent()
            self.write(")")

    def pretty_ffi(self, msg: logic_pb2.FFI):
        flat876 = self._try_flat(msg, self.pretty_ffi)
        if flat876 is not None:
            assert flat876 is not None
            self.write(flat876)
            return None
        else:
            def _t1433(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
            _t1434 = _t1433(msg)
            fields871 = _t1434
            assert fields871 is not None
            unwrapped_fields872 = fields871
            self.write("(")
            self.write("ffi")
            self.indent_sexp()
            self.newline()
            field873 = unwrapped_fields872[0]
            self.pretty_name(field873)
            self.newline()
            field874 = unwrapped_fields872[1]
            self.pretty_ffi_args(field874)
            self.newline()
            field875 = unwrapped_fields872[2]
            self.pretty_terms(field875)
            self.dedent()
            self.write(")")

    def pretty_name(self, msg: str):
        flat878 = self._try_flat(msg, self.pretty_name)
        if flat878 is not None:
            assert flat878 is not None
            self.write(flat878)
            return None
        else:
            fields877 = msg
            self.write(":")
            self.write(fields877)

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]):
        flat882 = self._try_flat(msg, self.pretty_ffi_args)
        if flat882 is not None:
            assert flat882 is not None
            self.write(flat882)
            return None
        else:
            fields879 = msg
            self.write("(")
            self.write("args")
            self.indent_sexp()
            if not len(fields879) == 0:
                self.newline()
                for i881, elem880 in enumerate(fields879):
                    if (i881 > 0):
                        self.newline()
                    self.pretty_abstraction(elem880)
            self.dedent()
            self.write(")")

    def pretty_atom(self, msg: logic_pb2.Atom):
        flat889 = self._try_flat(msg, self.pretty_atom)
        if flat889 is not None:
            assert flat889 is not None
            self.write(flat889)
            return None
        else:
            def _t1435(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1436 = _t1435(msg)
            fields883 = _t1436
            assert fields883 is not None
            unwrapped_fields884 = fields883
            self.write("(")
            self.write("atom")
            self.indent_sexp()
            self.newline()
            field885 = unwrapped_fields884[0]
            self.pretty_relation_id(field885)
            field886 = unwrapped_fields884[1]
            if not len(field886) == 0:
                self.newline()
                for i888, elem887 in enumerate(field886):
                    if (i888 > 0):
                        self.newline()
                    self.pretty_term(elem887)
            self.dedent()
            self.write(")")

    def pretty_pragma(self, msg: logic_pb2.Pragma):
        flat896 = self._try_flat(msg, self.pretty_pragma)
        if flat896 is not None:
            assert flat896 is not None
            self.write(flat896)
            return None
        else:
            def _t1437(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1438 = _t1437(msg)
            fields890 = _t1438
            assert fields890 is not None
            unwrapped_fields891 = fields890
            self.write("(")
            self.write("pragma")
            self.indent_sexp()
            self.newline()
            field892 = unwrapped_fields891[0]
            self.pretty_name(field892)
            field893 = unwrapped_fields891[1]
            if not len(field893) == 0:
                self.newline()
                for i895, elem894 in enumerate(field893):
                    if (i895 > 0):
                        self.newline()
                    self.pretty_term(elem894)
            self.dedent()
            self.write(")")

    def pretty_primitive(self, msg: logic_pb2.Primitive):
        flat912 = self._try_flat(msg, self.pretty_primitive)
        if flat912 is not None:
            assert flat912 is not None
            self.write(flat912)
            return None
        else:
            def _t1439(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1440 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1440 = None
                return _t1440
            _t1441 = _t1439(msg)
            guard_result911 = _t1441
            if guard_result911 is not None:
                self.pretty_eq(msg)
            else:
                def _t1442(_dollar_dollar):
                    if _dollar_dollar.name == "rel_primitive_lt_monotype":
                        _t1443 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1443 = None
                    return _t1443
                _t1444 = _t1442(msg)
                guard_result910 = _t1444
                if guard_result910 is not None:
                    self.pretty_lt(msg)
                else:
                    def _t1445(_dollar_dollar):
                        if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                            _t1446 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1446 = None
                        return _t1446
                    _t1447 = _t1445(msg)
                    guard_result909 = _t1447
                    if guard_result909 is not None:
                        self.pretty_lt_eq(msg)
                    else:
                        def _t1448(_dollar_dollar):
                            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                                _t1449 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1449 = None
                            return _t1449
                        _t1450 = _t1448(msg)
                        guard_result908 = _t1450
                        if guard_result908 is not None:
                            self.pretty_gt(msg)
                        else:
                            def _t1451(_dollar_dollar):
                                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                    _t1452 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                                else:
                                    _t1452 = None
                                return _t1452
                            _t1453 = _t1451(msg)
                            guard_result907 = _t1453
                            if guard_result907 is not None:
                                self.pretty_gt_eq(msg)
                            else:
                                def _t1454(_dollar_dollar):
                                    if _dollar_dollar.name == "rel_primitive_add_monotype":
                                        _t1455 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1455 = None
                                    return _t1455
                                _t1456 = _t1454(msg)
                                guard_result906 = _t1456
                                if guard_result906 is not None:
                                    self.pretty_add(msg)
                                else:
                                    def _t1457(_dollar_dollar):
                                        if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                            _t1458 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1458 = None
                                        return _t1458
                                    _t1459 = _t1457(msg)
                                    guard_result905 = _t1459
                                    if guard_result905 is not None:
                                        self.pretty_minus(msg)
                                    else:
                                        def _t1460(_dollar_dollar):
                                            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                                _t1461 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1461 = None
                                            return _t1461
                                        _t1462 = _t1460(msg)
                                        guard_result904 = _t1462
                                        if guard_result904 is not None:
                                            self.pretty_multiply(msg)
                                        else:
                                            def _t1463(_dollar_dollar):
                                                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                    _t1464 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                                else:
                                                    _t1464 = None
                                                return _t1464
                                            _t1465 = _t1463(msg)
                                            guard_result903 = _t1465
                                            if guard_result903 is not None:
                                                self.pretty_divide(msg)
                                            else:
                                                def _t1466(_dollar_dollar):
                                                    return (_dollar_dollar.name, _dollar_dollar.terms,)
                                                _t1467 = _t1466(msg)
                                                fields897 = _t1467
                                                assert fields897 is not None
                                                unwrapped_fields898 = fields897
                                                self.write("(")
                                                self.write("primitive")
                                                self.indent_sexp()
                                                self.newline()
                                                field899 = unwrapped_fields898[0]
                                                self.pretty_name(field899)
                                                field900 = unwrapped_fields898[1]
                                                if not len(field900) == 0:
                                                    self.newline()
                                                    for i902, elem901 in enumerate(field900):
                                                        if (i902 > 0):
                                                            self.newline()
                                                        self.pretty_rel_term(elem901)
                                                self.dedent()
                                                self.write(")")

    def pretty_eq(self, msg: logic_pb2.Primitive):
        flat917 = self._try_flat(msg, self.pretty_eq)
        if flat917 is not None:
            assert flat917 is not None
            self.write(flat917)
            return None
        else:
            def _t1468(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_eq":
                    _t1469 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1469 = None
                return _t1469
            _t1470 = _t1468(msg)
            fields913 = _t1470
            assert fields913 is not None
            unwrapped_fields914 = fields913
            self.write("(")
            self.write("=")
            self.indent_sexp()
            self.newline()
            field915 = unwrapped_fields914[0]
            self.pretty_term(field915)
            self.newline()
            field916 = unwrapped_fields914[1]
            self.pretty_term(field916)
            self.dedent()
            self.write(")")

    def pretty_lt(self, msg: logic_pb2.Primitive):
        flat922 = self._try_flat(msg, self.pretty_lt)
        if flat922 is not None:
            assert flat922 is not None
            self.write(flat922)
            return None
        else:
            def _t1471(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1472 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1472 = None
                return _t1472
            _t1473 = _t1471(msg)
            fields918 = _t1473
            assert fields918 is not None
            unwrapped_fields919 = fields918
            self.write("(")
            self.write("<")
            self.indent_sexp()
            self.newline()
            field920 = unwrapped_fields919[0]
            self.pretty_term(field920)
            self.newline()
            field921 = unwrapped_fields919[1]
            self.pretty_term(field921)
            self.dedent()
            self.write(")")

    def pretty_lt_eq(self, msg: logic_pb2.Primitive):
        flat927 = self._try_flat(msg, self.pretty_lt_eq)
        if flat927 is not None:
            assert flat927 is not None
            self.write(flat927)
            return None
        else:
            def _t1474(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                    _t1475 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1475 = None
                return _t1475
            _t1476 = _t1474(msg)
            fields923 = _t1476
            assert fields923 is not None
            unwrapped_fields924 = fields923
            self.write("(")
            self.write("<=")
            self.indent_sexp()
            self.newline()
            field925 = unwrapped_fields924[0]
            self.pretty_term(field925)
            self.newline()
            field926 = unwrapped_fields924[1]
            self.pretty_term(field926)
            self.dedent()
            self.write(")")

    def pretty_gt(self, msg: logic_pb2.Primitive):
        flat932 = self._try_flat(msg, self.pretty_gt)
        if flat932 is not None:
            assert flat932 is not None
            self.write(flat932)
            return None
        else:
            def _t1477(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_monotype":
                    _t1478 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1478 = None
                return _t1478
            _t1479 = _t1477(msg)
            fields928 = _t1479
            assert fields928 is not None
            unwrapped_fields929 = fields928
            self.write("(")
            self.write(">")
            self.indent_sexp()
            self.newline()
            field930 = unwrapped_fields929[0]
            self.pretty_term(field930)
            self.newline()
            field931 = unwrapped_fields929[1]
            self.pretty_term(field931)
            self.dedent()
            self.write(")")

    def pretty_gt_eq(self, msg: logic_pb2.Primitive):
        flat937 = self._try_flat(msg, self.pretty_gt_eq)
        if flat937 is not None:
            assert flat937 is not None
            self.write(flat937)
            return None
        else:
            def _t1480(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                    _t1481 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1481 = None
                return _t1481
            _t1482 = _t1480(msg)
            fields933 = _t1482
            assert fields933 is not None
            unwrapped_fields934 = fields933
            self.write("(")
            self.write(">=")
            self.indent_sexp()
            self.newline()
            field935 = unwrapped_fields934[0]
            self.pretty_term(field935)
            self.newline()
            field936 = unwrapped_fields934[1]
            self.pretty_term(field936)
            self.dedent()
            self.write(")")

    def pretty_add(self, msg: logic_pb2.Primitive):
        flat943 = self._try_flat(msg, self.pretty_add)
        if flat943 is not None:
            assert flat943 is not None
            self.write(flat943)
            return None
        else:
            def _t1483(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_add_monotype":
                    _t1484 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1484 = None
                return _t1484
            _t1485 = _t1483(msg)
            fields938 = _t1485
            assert fields938 is not None
            unwrapped_fields939 = fields938
            self.write("(")
            self.write("+")
            self.indent_sexp()
            self.newline()
            field940 = unwrapped_fields939[0]
            self.pretty_term(field940)
            self.newline()
            field941 = unwrapped_fields939[1]
            self.pretty_term(field941)
            self.newline()
            field942 = unwrapped_fields939[2]
            self.pretty_term(field942)
            self.dedent()
            self.write(")")

    def pretty_minus(self, msg: logic_pb2.Primitive):
        flat949 = self._try_flat(msg, self.pretty_minus)
        if flat949 is not None:
            assert flat949 is not None
            self.write(flat949)
            return None
        else:
            def _t1486(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                    _t1487 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1487 = None
                return _t1487
            _t1488 = _t1486(msg)
            fields944 = _t1488
            assert fields944 is not None
            unwrapped_fields945 = fields944
            self.write("(")
            self.write("-")
            self.indent_sexp()
            self.newline()
            field946 = unwrapped_fields945[0]
            self.pretty_term(field946)
            self.newline()
            field947 = unwrapped_fields945[1]
            self.pretty_term(field947)
            self.newline()
            field948 = unwrapped_fields945[2]
            self.pretty_term(field948)
            self.dedent()
            self.write(")")

    def pretty_multiply(self, msg: logic_pb2.Primitive):
        flat955 = self._try_flat(msg, self.pretty_multiply)
        if flat955 is not None:
            assert flat955 is not None
            self.write(flat955)
            return None
        else:
            def _t1489(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                    _t1490 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1490 = None
                return _t1490
            _t1491 = _t1489(msg)
            fields950 = _t1491
            assert fields950 is not None
            unwrapped_fields951 = fields950
            self.write("(")
            self.write("*")
            self.indent_sexp()
            self.newline()
            field952 = unwrapped_fields951[0]
            self.pretty_term(field952)
            self.newline()
            field953 = unwrapped_fields951[1]
            self.pretty_term(field953)
            self.newline()
            field954 = unwrapped_fields951[2]
            self.pretty_term(field954)
            self.dedent()
            self.write(")")

    def pretty_divide(self, msg: logic_pb2.Primitive):
        flat961 = self._try_flat(msg, self.pretty_divide)
        if flat961 is not None:
            assert flat961 is not None
            self.write(flat961)
            return None
        else:
            def _t1492(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_divide_monotype":
                    _t1493 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                else:
                    _t1493 = None
                return _t1493
            _t1494 = _t1492(msg)
            fields956 = _t1494
            assert fields956 is not None
            unwrapped_fields957 = fields956
            self.write("(")
            self.write("/")
            self.indent_sexp()
            self.newline()
            field958 = unwrapped_fields957[0]
            self.pretty_term(field958)
            self.newline()
            field959 = unwrapped_fields957[1]
            self.pretty_term(field959)
            self.newline()
            field960 = unwrapped_fields957[2]
            self.pretty_term(field960)
            self.dedent()
            self.write(")")

    def pretty_rel_term(self, msg: logic_pb2.RelTerm):
        flat966 = self._try_flat(msg, self.pretty_rel_term)
        if flat966 is not None:
            assert flat966 is not None
            self.write(flat966)
            return None
        else:
            def _t1495(_dollar_dollar):
                if _dollar_dollar.HasField("specialized_value"):
                    _t1496 = _dollar_dollar.specialized_value
                else:
                    _t1496 = None
                return _t1496
            _t1497 = _t1495(msg)
            deconstruct_result964 = _t1497
            if deconstruct_result964 is not None:
                assert deconstruct_result964 is not None
                unwrapped965 = deconstruct_result964
                self.pretty_specialized_value(unwrapped965)
            else:
                def _t1498(_dollar_dollar):
                    if _dollar_dollar.HasField("term"):
                        _t1499 = _dollar_dollar.term
                    else:
                        _t1499 = None
                    return _t1499
                _t1500 = _t1498(msg)
                deconstruct_result962 = _t1500
                if deconstruct_result962 is not None:
                    assert deconstruct_result962 is not None
                    unwrapped963 = deconstruct_result962
                    self.pretty_term(unwrapped963)
                else:
                    raise ParseError("No matching rule for rel_term")

    def pretty_specialized_value(self, msg: logic_pb2.Value):
        flat968 = self._try_flat(msg, self.pretty_specialized_value)
        if flat968 is not None:
            assert flat968 is not None
            self.write(flat968)
            return None
        else:
            fields967 = msg
            self.write("#")
            self.pretty_value(fields967)

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom):
        flat975 = self._try_flat(msg, self.pretty_rel_atom)
        if flat975 is not None:
            assert flat975 is not None
            self.write(flat975)
            return None
        else:
            def _t1501(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.terms,)
            _t1502 = _t1501(msg)
            fields969 = _t1502
            assert fields969 is not None
            unwrapped_fields970 = fields969
            self.write("(")
            self.write("relatom")
            self.indent_sexp()
            self.newline()
            field971 = unwrapped_fields970[0]
            self.pretty_name(field971)
            field972 = unwrapped_fields970[1]
            if not len(field972) == 0:
                self.newline()
                for i974, elem973 in enumerate(field972):
                    if (i974 > 0):
                        self.newline()
                    self.pretty_rel_term(elem973)
            self.dedent()
            self.write(")")

    def pretty_cast(self, msg: logic_pb2.Cast):
        flat980 = self._try_flat(msg, self.pretty_cast)
        if flat980 is not None:
            assert flat980 is not None
            self.write(flat980)
            return None
        else:
            def _t1503(_dollar_dollar):
                return (_dollar_dollar.input, _dollar_dollar.result,)
            _t1504 = _t1503(msg)
            fields976 = _t1504
            assert fields976 is not None
            unwrapped_fields977 = fields976
            self.write("(")
            self.write("cast")
            self.indent_sexp()
            self.newline()
            field978 = unwrapped_fields977[0]
            self.pretty_term(field978)
            self.newline()
            field979 = unwrapped_fields977[1]
            self.pretty_term(field979)
            self.dedent()
            self.write(")")

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]):
        flat984 = self._try_flat(msg, self.pretty_attrs)
        if flat984 is not None:
            assert flat984 is not None
            self.write(flat984)
            return None
        else:
            fields981 = msg
            self.write("(")
            self.write("attrs")
            self.indent_sexp()
            if not len(fields981) == 0:
                self.newline()
                for i983, elem982 in enumerate(fields981):
                    if (i983 > 0):
                        self.newline()
                    self.pretty_attribute(elem982)
            self.dedent()
            self.write(")")

    def pretty_attribute(self, msg: logic_pb2.Attribute):
        flat991 = self._try_flat(msg, self.pretty_attribute)
        if flat991 is not None:
            assert flat991 is not None
            self.write(flat991)
            return None
        else:
            def _t1505(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.args,)
            _t1506 = _t1505(msg)
            fields985 = _t1506
            assert fields985 is not None
            unwrapped_fields986 = fields985
            self.write("(")
            self.write("attribute")
            self.indent_sexp()
            self.newline()
            field987 = unwrapped_fields986[0]
            self.pretty_name(field987)
            field988 = unwrapped_fields986[1]
            if not len(field988) == 0:
                self.newline()
                for i990, elem989 in enumerate(field988):
                    if (i990 > 0):
                        self.newline()
                    self.pretty_value(elem989)
            self.dedent()
            self.write(")")

    def pretty_algorithm(self, msg: logic_pb2.Algorithm):
        flat998 = self._try_flat(msg, self.pretty_algorithm)
        if flat998 is not None:
            assert flat998 is not None
            self.write(flat998)
            return None
        else:
            def _t1507(_dollar_dollar):
                return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
            _t1508 = _t1507(msg)
            fields992 = _t1508
            assert fields992 is not None
            unwrapped_fields993 = fields992
            self.write("(")
            self.write("algorithm")
            self.indent_sexp()
            field994 = unwrapped_fields993[0]
            if not len(field994) == 0:
                self.newline()
                for i996, elem995 in enumerate(field994):
                    if (i996 > 0):
                        self.newline()
                    self.pretty_relation_id(elem995)
            self.newline()
            field997 = unwrapped_fields993[1]
            self.pretty_script(field997)
            self.dedent()
            self.write(")")

    def pretty_script(self, msg: logic_pb2.Script):
        flat1003 = self._try_flat(msg, self.pretty_script)
        if flat1003 is not None:
            assert flat1003 is not None
            self.write(flat1003)
            return None
        else:
            def _t1509(_dollar_dollar):
                return _dollar_dollar.constructs
            _t1510 = _t1509(msg)
            fields999 = _t1510
            assert fields999 is not None
            unwrapped_fields1000 = fields999
            self.write("(")
            self.write("script")
            self.indent_sexp()
            if not len(unwrapped_fields1000) == 0:
                self.newline()
                for i1002, elem1001 in enumerate(unwrapped_fields1000):
                    if (i1002 > 0):
                        self.newline()
                    self.pretty_construct(elem1001)
            self.dedent()
            self.write(")")

    def pretty_construct(self, msg: logic_pb2.Construct):
        flat1008 = self._try_flat(msg, self.pretty_construct)
        if flat1008 is not None:
            assert flat1008 is not None
            self.write(flat1008)
            return None
        else:
            def _t1511(_dollar_dollar):
                if _dollar_dollar.HasField("loop"):
                    _t1512 = _dollar_dollar.loop
                else:
                    _t1512 = None
                return _t1512
            _t1513 = _t1511(msg)
            deconstruct_result1006 = _t1513
            if deconstruct_result1006 is not None:
                assert deconstruct_result1006 is not None
                unwrapped1007 = deconstruct_result1006
                self.pretty_loop(unwrapped1007)
            else:
                def _t1514(_dollar_dollar):
                    if _dollar_dollar.HasField("instruction"):
                        _t1515 = _dollar_dollar.instruction
                    else:
                        _t1515 = None
                    return _t1515
                _t1516 = _t1514(msg)
                deconstruct_result1004 = _t1516
                if deconstruct_result1004 is not None:
                    assert deconstruct_result1004 is not None
                    unwrapped1005 = deconstruct_result1004
                    self.pretty_instruction(unwrapped1005)
                else:
                    raise ParseError("No matching rule for construct")

    def pretty_loop(self, msg: logic_pb2.Loop):
        flat1013 = self._try_flat(msg, self.pretty_loop)
        if flat1013 is not None:
            assert flat1013 is not None
            self.write(flat1013)
            return None
        else:
            def _t1517(_dollar_dollar):
                return (_dollar_dollar.init, _dollar_dollar.body,)
            _t1518 = _t1517(msg)
            fields1009 = _t1518
            assert fields1009 is not None
            unwrapped_fields1010 = fields1009
            self.write("(")
            self.write("loop")
            self.indent_sexp()
            self.newline()
            field1011 = unwrapped_fields1010[0]
            self.pretty_init(field1011)
            self.newline()
            field1012 = unwrapped_fields1010[1]
            self.pretty_script(field1012)
            self.dedent()
            self.write(")")

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]):
        flat1017 = self._try_flat(msg, self.pretty_init)
        if flat1017 is not None:
            assert flat1017 is not None
            self.write(flat1017)
            return None
        else:
            fields1014 = msg
            self.write("(")
            self.write("init")
            self.indent_sexp()
            if not len(fields1014) == 0:
                self.newline()
                for i1016, elem1015 in enumerate(fields1014):
                    if (i1016 > 0):
                        self.newline()
                    self.pretty_instruction(elem1015)
            self.dedent()
            self.write(")")

    def pretty_instruction(self, msg: logic_pb2.Instruction):
        flat1028 = self._try_flat(msg, self.pretty_instruction)
        if flat1028 is not None:
            assert flat1028 is not None
            self.write(flat1028)
            return None
        else:
            def _t1519(_dollar_dollar):
                if _dollar_dollar.HasField("assign"):
                    _t1520 = _dollar_dollar.assign
                else:
                    _t1520 = None
                return _t1520
            _t1521 = _t1519(msg)
            deconstruct_result1026 = _t1521
            if deconstruct_result1026 is not None:
                assert deconstruct_result1026 is not None
                unwrapped1027 = deconstruct_result1026
                self.pretty_assign(unwrapped1027)
            else:
                def _t1522(_dollar_dollar):
                    if _dollar_dollar.HasField("upsert"):
                        _t1523 = _dollar_dollar.upsert
                    else:
                        _t1523 = None
                    return _t1523
                _t1524 = _t1522(msg)
                deconstruct_result1024 = _t1524
                if deconstruct_result1024 is not None:
                    assert deconstruct_result1024 is not None
                    unwrapped1025 = deconstruct_result1024
                    self.pretty_upsert(unwrapped1025)
                else:
                    def _t1525(_dollar_dollar):
                        if _dollar_dollar.HasField("break"):
                            _t1526 = getattr(_dollar_dollar, 'break')
                        else:
                            _t1526 = None
                        return _t1526
                    _t1527 = _t1525(msg)
                    deconstruct_result1022 = _t1527
                    if deconstruct_result1022 is not None:
                        assert deconstruct_result1022 is not None
                        unwrapped1023 = deconstruct_result1022
                        self.pretty_break(unwrapped1023)
                    else:
                        def _t1528(_dollar_dollar):
                            if _dollar_dollar.HasField("monoid_def"):
                                _t1529 = _dollar_dollar.monoid_def
                            else:
                                _t1529 = None
                            return _t1529
                        _t1530 = _t1528(msg)
                        deconstruct_result1020 = _t1530
                        if deconstruct_result1020 is not None:
                            assert deconstruct_result1020 is not None
                            unwrapped1021 = deconstruct_result1020
                            self.pretty_monoid_def(unwrapped1021)
                        else:
                            def _t1531(_dollar_dollar):
                                if _dollar_dollar.HasField("monus_def"):
                                    _t1532 = _dollar_dollar.monus_def
                                else:
                                    _t1532 = None
                                return _t1532
                            _t1533 = _t1531(msg)
                            deconstruct_result1018 = _t1533
                            if deconstruct_result1018 is not None:
                                assert deconstruct_result1018 is not None
                                unwrapped1019 = deconstruct_result1018
                                self.pretty_monus_def(unwrapped1019)
                            else:
                                raise ParseError("No matching rule for instruction")

    def pretty_assign(self, msg: logic_pb2.Assign):
        flat1035 = self._try_flat(msg, self.pretty_assign)
        if flat1035 is not None:
            assert flat1035 is not None
            self.write(flat1035)
            return None
        else:
            def _t1534(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1535 = _dollar_dollar.attrs
                else:
                    _t1535 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1535,)
            _t1536 = _t1534(msg)
            fields1029 = _t1536
            assert fields1029 is not None
            unwrapped_fields1030 = fields1029
            self.write("(")
            self.write("assign")
            self.indent_sexp()
            self.newline()
            field1031 = unwrapped_fields1030[0]
            self.pretty_relation_id(field1031)
            self.newline()
            field1032 = unwrapped_fields1030[1]
            self.pretty_abstraction(field1032)
            field1033 = unwrapped_fields1030[2]
            if field1033 is not None:
                self.newline()
                assert field1033 is not None
                opt_val1034 = field1033
                self.pretty_attrs(opt_val1034)
            self.dedent()
            self.write(")")

    def pretty_upsert(self, msg: logic_pb2.Upsert):
        flat1042 = self._try_flat(msg, self.pretty_upsert)
        if flat1042 is not None:
            assert flat1042 is not None
            self.write(flat1042)
            return None
        else:
            def _t1537(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1538 = _dollar_dollar.attrs
                else:
                    _t1538 = None
                return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1538,)
            _t1539 = _t1537(msg)
            fields1036 = _t1539
            assert fields1036 is not None
            unwrapped_fields1037 = fields1036
            self.write("(")
            self.write("upsert")
            self.indent_sexp()
            self.newline()
            field1038 = unwrapped_fields1037[0]
            self.pretty_relation_id(field1038)
            self.newline()
            field1039 = unwrapped_fields1037[1]
            self.pretty_abstraction_with_arity(field1039)
            field1040 = unwrapped_fields1037[2]
            if field1040 is not None:
                self.newline()
                assert field1040 is not None
                opt_val1041 = field1040
                self.pretty_attrs(opt_val1041)
            self.dedent()
            self.write(")")

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]):
        flat1047 = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if flat1047 is not None:
            assert flat1047 is not None
            self.write(flat1047)
            return None
        else:
            def _t1540(_dollar_dollar):
                _t1541 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
                return (_t1541, _dollar_dollar[0].value,)
            _t1542 = _t1540(msg)
            fields1043 = _t1542
            assert fields1043 is not None
            unwrapped_fields1044 = fields1043
            self.write("(")
            self.indent()
            field1045 = unwrapped_fields1044[0]
            self.pretty_bindings(field1045)
            self.newline()
            field1046 = unwrapped_fields1044[1]
            self.pretty_formula(field1046)
            self.dedent()
            self.write(")")

    def pretty_break(self, msg: logic_pb2.Break):
        flat1054 = self._try_flat(msg, self.pretty_break)
        if flat1054 is not None:
            assert flat1054 is not None
            self.write(flat1054)
            return None
        else:
            def _t1543(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1544 = _dollar_dollar.attrs
                else:
                    _t1544 = None
                return (_dollar_dollar.name, _dollar_dollar.body, _t1544,)
            _t1545 = _t1543(msg)
            fields1048 = _t1545
            assert fields1048 is not None
            unwrapped_fields1049 = fields1048
            self.write("(")
            self.write("break")
            self.indent_sexp()
            self.newline()
            field1050 = unwrapped_fields1049[0]
            self.pretty_relation_id(field1050)
            self.newline()
            field1051 = unwrapped_fields1049[1]
            self.pretty_abstraction(field1051)
            field1052 = unwrapped_fields1049[2]
            if field1052 is not None:
                self.newline()
                assert field1052 is not None
                opt_val1053 = field1052
                self.pretty_attrs(opt_val1053)
            self.dedent()
            self.write(")")

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef):
        flat1062 = self._try_flat(msg, self.pretty_monoid_def)
        if flat1062 is not None:
            assert flat1062 is not None
            self.write(flat1062)
            return None
        else:
            def _t1546(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1547 = _dollar_dollar.attrs
                else:
                    _t1547 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1547,)
            _t1548 = _t1546(msg)
            fields1055 = _t1548
            assert fields1055 is not None
            unwrapped_fields1056 = fields1055
            self.write("(")
            self.write("monoid")
            self.indent_sexp()
            self.newline()
            field1057 = unwrapped_fields1056[0]
            self.pretty_monoid(field1057)
            self.newline()
            field1058 = unwrapped_fields1056[1]
            self.pretty_relation_id(field1058)
            self.newline()
            field1059 = unwrapped_fields1056[2]
            self.pretty_abstraction_with_arity(field1059)
            field1060 = unwrapped_fields1056[3]
            if field1060 is not None:
                self.newline()
                assert field1060 is not None
                opt_val1061 = field1060
                self.pretty_attrs(opt_val1061)
            self.dedent()
            self.write(")")

    def pretty_monoid(self, msg: logic_pb2.Monoid):
        flat1071 = self._try_flat(msg, self.pretty_monoid)
        if flat1071 is not None:
            assert flat1071 is not None
            self.write(flat1071)
            return None
        else:
            def _t1549(_dollar_dollar):
                if _dollar_dollar.HasField("or_monoid"):
                    _t1550 = _dollar_dollar.or_monoid
                else:
                    _t1550 = None
                return _t1550
            _t1551 = _t1549(msg)
            deconstruct_result1069 = _t1551
            if deconstruct_result1069 is not None:
                assert deconstruct_result1069 is not None
                unwrapped1070 = deconstruct_result1069
                self.pretty_or_monoid(unwrapped1070)
            else:
                def _t1552(_dollar_dollar):
                    if _dollar_dollar.HasField("min_monoid"):
                        _t1553 = _dollar_dollar.min_monoid
                    else:
                        _t1553 = None
                    return _t1553
                _t1554 = _t1552(msg)
                deconstruct_result1067 = _t1554
                if deconstruct_result1067 is not None:
                    assert deconstruct_result1067 is not None
                    unwrapped1068 = deconstruct_result1067
                    self.pretty_min_monoid(unwrapped1068)
                else:
                    def _t1555(_dollar_dollar):
                        if _dollar_dollar.HasField("max_monoid"):
                            _t1556 = _dollar_dollar.max_monoid
                        else:
                            _t1556 = None
                        return _t1556
                    _t1557 = _t1555(msg)
                    deconstruct_result1065 = _t1557
                    if deconstruct_result1065 is not None:
                        assert deconstruct_result1065 is not None
                        unwrapped1066 = deconstruct_result1065
                        self.pretty_max_monoid(unwrapped1066)
                    else:
                        def _t1558(_dollar_dollar):
                            if _dollar_dollar.HasField("sum_monoid"):
                                _t1559 = _dollar_dollar.sum_monoid
                            else:
                                _t1559 = None
                            return _t1559
                        _t1560 = _t1558(msg)
                        deconstruct_result1063 = _t1560
                        if deconstruct_result1063 is not None:
                            assert deconstruct_result1063 is not None
                            unwrapped1064 = deconstruct_result1063
                            self.pretty_sum_monoid(unwrapped1064)
                        else:
                            raise ParseError("No matching rule for monoid")

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid):
        fields1072 = msg
        self.write("(")
        self.write("or")
        self.write(")")

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid):
        flat1075 = self._try_flat(msg, self.pretty_min_monoid)
        if flat1075 is not None:
            assert flat1075 is not None
            self.write(flat1075)
            return None
        else:
            def _t1561(_dollar_dollar):
                return _dollar_dollar.type
            _t1562 = _t1561(msg)
            fields1073 = _t1562
            assert fields1073 is not None
            unwrapped_fields1074 = fields1073
            self.write("(")
            self.write("min")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1074)
            self.dedent()
            self.write(")")

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid):
        flat1078 = self._try_flat(msg, self.pretty_max_monoid)
        if flat1078 is not None:
            assert flat1078 is not None
            self.write(flat1078)
            return None
        else:
            def _t1563(_dollar_dollar):
                return _dollar_dollar.type
            _t1564 = _t1563(msg)
            fields1076 = _t1564
            assert fields1076 is not None
            unwrapped_fields1077 = fields1076
            self.write("(")
            self.write("max")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1077)
            self.dedent()
            self.write(")")

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid):
        flat1081 = self._try_flat(msg, self.pretty_sum_monoid)
        if flat1081 is not None:
            assert flat1081 is not None
            self.write(flat1081)
            return None
        else:
            def _t1565(_dollar_dollar):
                return _dollar_dollar.type
            _t1566 = _t1565(msg)
            fields1079 = _t1566
            assert fields1079 is not None
            unwrapped_fields1080 = fields1079
            self.write("(")
            self.write("sum")
            self.indent_sexp()
            self.newline()
            self.pretty_type(unwrapped_fields1080)
            self.dedent()
            self.write(")")

    def pretty_monus_def(self, msg: logic_pb2.MonusDef):
        flat1089 = self._try_flat(msg, self.pretty_monus_def)
        if flat1089 is not None:
            assert flat1089 is not None
            self.write(flat1089)
            return None
        else:
            def _t1567(_dollar_dollar):
                if not len(_dollar_dollar.attrs) == 0:
                    _t1568 = _dollar_dollar.attrs
                else:
                    _t1568 = None
                return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1568,)
            _t1569 = _t1567(msg)
            fields1082 = _t1569
            assert fields1082 is not None
            unwrapped_fields1083 = fields1082
            self.write("(")
            self.write("monus")
            self.indent_sexp()
            self.newline()
            field1084 = unwrapped_fields1083[0]
            self.pretty_monoid(field1084)
            self.newline()
            field1085 = unwrapped_fields1083[1]
            self.pretty_relation_id(field1085)
            self.newline()
            field1086 = unwrapped_fields1083[2]
            self.pretty_abstraction_with_arity(field1086)
            field1087 = unwrapped_fields1083[3]
            if field1087 is not None:
                self.newline()
                assert field1087 is not None
                opt_val1088 = field1087
                self.pretty_attrs(opt_val1088)
            self.dedent()
            self.write(")")

    def pretty_constraint(self, msg: logic_pb2.Constraint):
        flat1096 = self._try_flat(msg, self.pretty_constraint)
        if flat1096 is not None:
            assert flat1096 is not None
            self.write(flat1096)
            return None
        else:
            def _t1570(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
            _t1571 = _t1570(msg)
            fields1090 = _t1571
            assert fields1090 is not None
            unwrapped_fields1091 = fields1090
            self.write("(")
            self.write("functional_dependency")
            self.indent_sexp()
            self.newline()
            field1092 = unwrapped_fields1091[0]
            self.pretty_relation_id(field1092)
            self.newline()
            field1093 = unwrapped_fields1091[1]
            self.pretty_abstraction(field1093)
            self.newline()
            field1094 = unwrapped_fields1091[2]
            self.pretty_functional_dependency_keys(field1094)
            self.newline()
            field1095 = unwrapped_fields1091[3]
            self.pretty_functional_dependency_values(field1095)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]):
        flat1100 = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if flat1100 is not None:
            assert flat1100 is not None
            self.write(flat1100)
            return None
        else:
            fields1097 = msg
            self.write("(")
            self.write("keys")
            self.indent_sexp()
            if not len(fields1097) == 0:
                self.newline()
                for i1099, elem1098 in enumerate(fields1097):
                    if (i1099 > 0):
                        self.newline()
                    self.pretty_var(elem1098)
            self.dedent()
            self.write(")")

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]):
        flat1104 = self._try_flat(msg, self.pretty_functional_dependency_values)
        if flat1104 is not None:
            assert flat1104 is not None
            self.write(flat1104)
            return None
        else:
            fields1101 = msg
            self.write("(")
            self.write("values")
            self.indent_sexp()
            if not len(fields1101) == 0:
                self.newline()
                for i1103, elem1102 in enumerate(fields1101):
                    if (i1103 > 0):
                        self.newline()
                    self.pretty_var(elem1102)
            self.dedent()
            self.write(")")

    def pretty_data(self, msg: logic_pb2.Data):
        flat1111 = self._try_flat(msg, self.pretty_data)
        if flat1111 is not None:
            assert flat1111 is not None
            self.write(flat1111)
            return None
        else:
            def _t1572(_dollar_dollar):
                if _dollar_dollar.HasField("rel_edb"):
                    _t1573 = _dollar_dollar.rel_edb
                else:
                    _t1573 = None
                return _t1573
            _t1574 = _t1572(msg)
            deconstruct_result1109 = _t1574
            if deconstruct_result1109 is not None:
                assert deconstruct_result1109 is not None
                unwrapped1110 = deconstruct_result1109
                self.pretty_rel_edb(unwrapped1110)
            else:
                def _t1575(_dollar_dollar):
                    if _dollar_dollar.HasField("betree_relation"):
                        _t1576 = _dollar_dollar.betree_relation
                    else:
                        _t1576 = None
                    return _t1576
                _t1577 = _t1575(msg)
                deconstruct_result1107 = _t1577
                if deconstruct_result1107 is not None:
                    assert deconstruct_result1107 is not None
                    unwrapped1108 = deconstruct_result1107
                    self.pretty_betree_relation(unwrapped1108)
                else:
                    def _t1578(_dollar_dollar):
                        if _dollar_dollar.HasField("csv_data"):
                            _t1579 = _dollar_dollar.csv_data
                        else:
                            _t1579 = None
                        return _t1579
                    _t1580 = _t1578(msg)
                    deconstruct_result1105 = _t1580
                    if deconstruct_result1105 is not None:
                        assert deconstruct_result1105 is not None
                        unwrapped1106 = deconstruct_result1105
                        self.pretty_csv_data(unwrapped1106)
                    else:
                        raise ParseError("No matching rule for data")

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB):
        flat1117 = self._try_flat(msg, self.pretty_rel_edb)
        if flat1117 is not None:
            assert flat1117 is not None
            self.write(flat1117)
            return None
        else:
            def _t1581(_dollar_dollar):
                return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
            _t1582 = _t1581(msg)
            fields1112 = _t1582
            assert fields1112 is not None
            unwrapped_fields1113 = fields1112
            self.write("(")
            self.write("rel_edb")
            self.indent_sexp()
            self.newline()
            field1114 = unwrapped_fields1113[0]
            self.pretty_relation_id(field1114)
            self.newline()
            field1115 = unwrapped_fields1113[1]
            self.pretty_rel_edb_path(field1115)
            self.newline()
            field1116 = unwrapped_fields1113[2]
            self.pretty_rel_edb_types(field1116)
            self.dedent()
            self.write(")")

    def pretty_rel_edb_path(self, msg: Sequence[str]):
        flat1121 = self._try_flat(msg, self.pretty_rel_edb_path)
        if flat1121 is not None:
            assert flat1121 is not None
            self.write(flat1121)
            return None
        else:
            fields1118 = msg
            self.write("[")
            self.indent()
            for i1120, elem1119 in enumerate(fields1118):
                if (i1120 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1119))
            self.dedent()
            self.write("]")

    def pretty_rel_edb_types(self, msg: Sequence[logic_pb2.Type]):
        flat1125 = self._try_flat(msg, self.pretty_rel_edb_types)
        if flat1125 is not None:
            assert flat1125 is not None
            self.write(flat1125)
            return None
        else:
            fields1122 = msg
            self.write("[")
            self.indent()
            for i1124, elem1123 in enumerate(fields1122):
                if (i1124 > 0):
                    self.newline()
                self.pretty_type(elem1123)
            self.dedent()
            self.write("]")

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation):
        flat1130 = self._try_flat(msg, self.pretty_betree_relation)
        if flat1130 is not None:
            assert flat1130 is not None
            self.write(flat1130)
            return None
        else:
            def _t1583(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_info,)
            _t1584 = _t1583(msg)
            fields1126 = _t1584
            assert fields1126 is not None
            unwrapped_fields1127 = fields1126
            self.write("(")
            self.write("betree_relation")
            self.indent_sexp()
            self.newline()
            field1128 = unwrapped_fields1127[0]
            self.pretty_relation_id(field1128)
            self.newline()
            field1129 = unwrapped_fields1127[1]
            self.pretty_betree_info(field1129)
            self.dedent()
            self.write(")")

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo):
        flat1136 = self._try_flat(msg, self.pretty_betree_info)
        if flat1136 is not None:
            assert flat1136 is not None
            self.write(flat1136)
            return None
        else:
            def _t1585(_dollar_dollar):
                _t1586 = self.deconstruct_betree_info_config(_dollar_dollar)
                return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1586,)
            _t1587 = _t1585(msg)
            fields1131 = _t1587
            assert fields1131 is not None
            unwrapped_fields1132 = fields1131
            self.write("(")
            self.write("betree_info")
            self.indent_sexp()
            self.newline()
            field1133 = unwrapped_fields1132[0]
            self.pretty_betree_info_key_types(field1133)
            self.newline()
            field1134 = unwrapped_fields1132[1]
            self.pretty_betree_info_value_types(field1134)
            self.newline()
            field1135 = unwrapped_fields1132[2]
            self.pretty_config_dict(field1135)
            self.dedent()
            self.write(")")

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]):
        flat1140 = self._try_flat(msg, self.pretty_betree_info_key_types)
        if flat1140 is not None:
            assert flat1140 is not None
            self.write(flat1140)
            return None
        else:
            fields1137 = msg
            self.write("(")
            self.write("key_types")
            self.indent_sexp()
            if not len(fields1137) == 0:
                self.newline()
                for i1139, elem1138 in enumerate(fields1137):
                    if (i1139 > 0):
                        self.newline()
                    self.pretty_type(elem1138)
            self.dedent()
            self.write(")")

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]):
        flat1144 = self._try_flat(msg, self.pretty_betree_info_value_types)
        if flat1144 is not None:
            assert flat1144 is not None
            self.write(flat1144)
            return None
        else:
            fields1141 = msg
            self.write("(")
            self.write("value_types")
            self.indent_sexp()
            if not len(fields1141) == 0:
                self.newline()
                for i1143, elem1142 in enumerate(fields1141):
                    if (i1143 > 0):
                        self.newline()
                    self.pretty_type(elem1142)
            self.dedent()
            self.write(")")

    def pretty_csv_data(self, msg: logic_pb2.CSVData):
        flat1151 = self._try_flat(msg, self.pretty_csv_data)
        if flat1151 is not None:
            assert flat1151 is not None
            self.write(flat1151)
            return None
        else:
            def _t1588(_dollar_dollar):
                return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
            _t1589 = _t1588(msg)
            fields1145 = _t1589
            assert fields1145 is not None
            unwrapped_fields1146 = fields1145
            self.write("(")
            self.write("csv_data")
            self.indent_sexp()
            self.newline()
            field1147 = unwrapped_fields1146[0]
            self.pretty_csvlocator(field1147)
            self.newline()
            field1148 = unwrapped_fields1146[1]
            self.pretty_csv_config(field1148)
            self.newline()
            field1149 = unwrapped_fields1146[2]
            self.pretty_csv_columns(field1149)
            self.newline()
            field1150 = unwrapped_fields1146[3]
            self.pretty_csv_asof(field1150)
            self.dedent()
            self.write(")")

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator):
        flat1158 = self._try_flat(msg, self.pretty_csvlocator)
        if flat1158 is not None:
            assert flat1158 is not None
            self.write(flat1158)
            return None
        else:
            def _t1590(_dollar_dollar):
                if not len(_dollar_dollar.paths) == 0:
                    _t1591 = _dollar_dollar.paths
                else:
                    _t1591 = None
                if _dollar_dollar.inline_data.decode('utf-8') != "":
                    _t1592 = _dollar_dollar.inline_data.decode('utf-8')
                else:
                    _t1592 = None
                return (_t1591, _t1592,)
            _t1593 = _t1590(msg)
            fields1152 = _t1593
            assert fields1152 is not None
            unwrapped_fields1153 = fields1152
            self.write("(")
            self.write("csv_locator")
            self.indent_sexp()
            field1154 = unwrapped_fields1153[0]
            if field1154 is not None:
                self.newline()
                assert field1154 is not None
                opt_val1155 = field1154
                self.pretty_csv_locator_paths(opt_val1155)
            field1156 = unwrapped_fields1153[1]
            if field1156 is not None:
                self.newline()
                assert field1156 is not None
                opt_val1157 = field1156
                self.pretty_csv_locator_inline_data(opt_val1157)
            self.dedent()
            self.write(")")

    def pretty_csv_locator_paths(self, msg: Sequence[str]):
        flat1162 = self._try_flat(msg, self.pretty_csv_locator_paths)
        if flat1162 is not None:
            assert flat1162 is not None
            self.write(flat1162)
            return None
        else:
            fields1159 = msg
            self.write("(")
            self.write("paths")
            self.indent_sexp()
            if not len(fields1159) == 0:
                self.newline()
                for i1161, elem1160 in enumerate(fields1159):
                    if (i1161 > 0):
                        self.newline()
                    self.write(self.format_string_value(elem1160))
            self.dedent()
            self.write(")")

    def pretty_csv_locator_inline_data(self, msg: str):
        flat1164 = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if flat1164 is not None:
            assert flat1164 is not None
            self.write(flat1164)
            return None
        else:
            fields1163 = msg
            self.write("(")
            self.write("inline_data")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1163))
            self.dedent()
            self.write(")")

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig):
        flat1167 = self._try_flat(msg, self.pretty_csv_config)
        if flat1167 is not None:
            assert flat1167 is not None
            self.write(flat1167)
            return None
        else:
            def _t1594(_dollar_dollar):
                _t1595 = self.deconstruct_csv_config(_dollar_dollar)
                return _t1595
            _t1596 = _t1594(msg)
            fields1165 = _t1596
            assert fields1165 is not None
            unwrapped_fields1166 = fields1165
            self.write("(")
            self.write("csv_config")
            self.indent_sexp()
            self.newline()
            self.pretty_config_dict(unwrapped_fields1166)
            self.dedent()
            self.write(")")

    def pretty_csv_columns(self, msg: Sequence[logic_pb2.CSVColumn]):
        flat1171 = self._try_flat(msg, self.pretty_csv_columns)
        if flat1171 is not None:
            assert flat1171 is not None
            self.write(flat1171)
            return None
        else:
            fields1168 = msg
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(fields1168) == 0:
                self.newline()
                for i1170, elem1169 in enumerate(fields1168):
                    if (i1170 > 0):
                        self.newline()
                    self.pretty_csv_column(elem1169)
            self.dedent()
            self.write(")")

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn):
        flat1179 = self._try_flat(msg, self.pretty_csv_column)
        if flat1179 is not None:
            assert flat1179 is not None
            self.write(flat1179)
            return None
        else:
            def _t1597(_dollar_dollar):
                return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
            _t1598 = _t1597(msg)
            fields1172 = _t1598
            assert fields1172 is not None
            unwrapped_fields1173 = fields1172
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field1174 = unwrapped_fields1173[0]
            self.write(self.format_string_value(field1174))
            self.newline()
            field1175 = unwrapped_fields1173[1]
            self.pretty_relation_id(field1175)
            self.newline()
            self.write("[")
            field1176 = unwrapped_fields1173[2]
            for i1178, elem1177 in enumerate(field1176):
                if (i1178 > 0):
                    self.newline()
                self.pretty_type(elem1177)
            self.write("]")
            self.dedent()
            self.write(")")

    def pretty_csv_asof(self, msg: str):
        flat1181 = self._try_flat(msg, self.pretty_csv_asof)
        if flat1181 is not None:
            assert flat1181 is not None
            self.write(flat1181)
            return None
        else:
            fields1180 = msg
            self.write("(")
            self.write("asof")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1180))
            self.dedent()
            self.write(")")

    def pretty_undefine(self, msg: transactions_pb2.Undefine):
        flat1184 = self._try_flat(msg, self.pretty_undefine)
        if flat1184 is not None:
            assert flat1184 is not None
            self.write(flat1184)
            return None
        else:
            def _t1599(_dollar_dollar):
                return _dollar_dollar.fragment_id
            _t1600 = _t1599(msg)
            fields1182 = _t1600
            assert fields1182 is not None
            unwrapped_fields1183 = fields1182
            self.write("(")
            self.write("undefine")
            self.indent_sexp()
            self.newline()
            self.pretty_fragment_id(unwrapped_fields1183)
            self.dedent()
            self.write(")")

    def pretty_context(self, msg: transactions_pb2.Context):
        flat1189 = self._try_flat(msg, self.pretty_context)
        if flat1189 is not None:
            assert flat1189 is not None
            self.write(flat1189)
            return None
        else:
            def _t1601(_dollar_dollar):
                return _dollar_dollar.relations
            _t1602 = _t1601(msg)
            fields1185 = _t1602
            assert fields1185 is not None
            unwrapped_fields1186 = fields1185
            self.write("(")
            self.write("context")
            self.indent_sexp()
            if not len(unwrapped_fields1186) == 0:
                self.newline()
                for i1188, elem1187 in enumerate(unwrapped_fields1186):
                    if (i1188 > 0):
                        self.newline()
                    self.pretty_relation_id(elem1187)
            self.dedent()
            self.write(")")

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]):
        flat1193 = self._try_flat(msg, self.pretty_epoch_reads)
        if flat1193 is not None:
            assert flat1193 is not None
            self.write(flat1193)
            return None
        else:
            fields1190 = msg
            self.write("(")
            self.write("reads")
            self.indent_sexp()
            if not len(fields1190) == 0:
                self.newline()
                for i1192, elem1191 in enumerate(fields1190):
                    if (i1192 > 0):
                        self.newline()
                    self.pretty_read(elem1191)
            self.dedent()
            self.write(")")

    def pretty_read(self, msg: transactions_pb2.Read):
        flat1204 = self._try_flat(msg, self.pretty_read)
        if flat1204 is not None:
            assert flat1204 is not None
            self.write(flat1204)
            return None
        else:
            def _t1603(_dollar_dollar):
                if _dollar_dollar.HasField("demand"):
                    _t1604 = _dollar_dollar.demand
                else:
                    _t1604 = None
                return _t1604
            _t1605 = _t1603(msg)
            deconstruct_result1202 = _t1605
            if deconstruct_result1202 is not None:
                assert deconstruct_result1202 is not None
                unwrapped1203 = deconstruct_result1202
                self.pretty_demand(unwrapped1203)
            else:
                def _t1606(_dollar_dollar):
                    if _dollar_dollar.HasField("output"):
                        _t1607 = _dollar_dollar.output
                    else:
                        _t1607 = None
                    return _t1607
                _t1608 = _t1606(msg)
                deconstruct_result1200 = _t1608
                if deconstruct_result1200 is not None:
                    assert deconstruct_result1200 is not None
                    unwrapped1201 = deconstruct_result1200
                    self.pretty_output(unwrapped1201)
                else:
                    def _t1609(_dollar_dollar):
                        if _dollar_dollar.HasField("what_if"):
                            _t1610 = _dollar_dollar.what_if
                        else:
                            _t1610 = None
                        return _t1610
                    _t1611 = _t1609(msg)
                    deconstruct_result1198 = _t1611
                    if deconstruct_result1198 is not None:
                        assert deconstruct_result1198 is not None
                        unwrapped1199 = deconstruct_result1198
                        self.pretty_what_if(unwrapped1199)
                    else:
                        def _t1612(_dollar_dollar):
                            if _dollar_dollar.HasField("abort"):
                                _t1613 = _dollar_dollar.abort
                            else:
                                _t1613 = None
                            return _t1613
                        _t1614 = _t1612(msg)
                        deconstruct_result1196 = _t1614
                        if deconstruct_result1196 is not None:
                            assert deconstruct_result1196 is not None
                            unwrapped1197 = deconstruct_result1196
                            self.pretty_abort(unwrapped1197)
                        else:
                            def _t1615(_dollar_dollar):
                                if _dollar_dollar.HasField("export"):
                                    _t1616 = _dollar_dollar.export
                                else:
                                    _t1616 = None
                                return _t1616
                            _t1617 = _t1615(msg)
                            deconstruct_result1194 = _t1617
                            if deconstruct_result1194 is not None:
                                assert deconstruct_result1194 is not None
                                unwrapped1195 = deconstruct_result1194
                                self.pretty_export(unwrapped1195)
                            else:
                                raise ParseError("No matching rule for read")

    def pretty_demand(self, msg: transactions_pb2.Demand):
        flat1207 = self._try_flat(msg, self.pretty_demand)
        if flat1207 is not None:
            assert flat1207 is not None
            self.write(flat1207)
            return None
        else:
            def _t1618(_dollar_dollar):
                return _dollar_dollar.relation_id
            _t1619 = _t1618(msg)
            fields1205 = _t1619
            assert fields1205 is not None
            unwrapped_fields1206 = fields1205
            self.write("(")
            self.write("demand")
            self.indent_sexp()
            self.newline()
            self.pretty_relation_id(unwrapped_fields1206)
            self.dedent()
            self.write(")")

    def pretty_output(self, msg: transactions_pb2.Output):
        flat1212 = self._try_flat(msg, self.pretty_output)
        if flat1212 is not None:
            assert flat1212 is not None
            self.write(flat1212)
            return None
        else:
            def _t1620(_dollar_dollar):
                return (_dollar_dollar.name, _dollar_dollar.relation_id,)
            _t1621 = _t1620(msg)
            fields1208 = _t1621
            assert fields1208 is not None
            unwrapped_fields1209 = fields1208
            self.write("(")
            self.write("output")
            self.indent_sexp()
            self.newline()
            field1210 = unwrapped_fields1209[0]
            self.pretty_name(field1210)
            self.newline()
            field1211 = unwrapped_fields1209[1]
            self.pretty_relation_id(field1211)
            self.dedent()
            self.write(")")

    def pretty_what_if(self, msg: transactions_pb2.WhatIf):
        flat1217 = self._try_flat(msg, self.pretty_what_if)
        if flat1217 is not None:
            assert flat1217 is not None
            self.write(flat1217)
            return None
        else:
            def _t1622(_dollar_dollar):
                return (_dollar_dollar.branch, _dollar_dollar.epoch,)
            _t1623 = _t1622(msg)
            fields1213 = _t1623
            assert fields1213 is not None
            unwrapped_fields1214 = fields1213
            self.write("(")
            self.write("what_if")
            self.indent_sexp()
            self.newline()
            field1215 = unwrapped_fields1214[0]
            self.pretty_name(field1215)
            self.newline()
            field1216 = unwrapped_fields1214[1]
            self.pretty_epoch(field1216)
            self.dedent()
            self.write(")")

    def pretty_abort(self, msg: transactions_pb2.Abort):
        flat1223 = self._try_flat(msg, self.pretty_abort)
        if flat1223 is not None:
            assert flat1223 is not None
            self.write(flat1223)
            return None
        else:
            def _t1624(_dollar_dollar):
                if _dollar_dollar.name != "abort":
                    _t1625 = _dollar_dollar.name
                else:
                    _t1625 = None
                return (_t1625, _dollar_dollar.relation_id,)
            _t1626 = _t1624(msg)
            fields1218 = _t1626
            assert fields1218 is not None
            unwrapped_fields1219 = fields1218
            self.write("(")
            self.write("abort")
            self.indent_sexp()
            field1220 = unwrapped_fields1219[0]
            if field1220 is not None:
                self.newline()
                assert field1220 is not None
                opt_val1221 = field1220
                self.pretty_name(opt_val1221)
            self.newline()
            field1222 = unwrapped_fields1219[1]
            self.pretty_relation_id(field1222)
            self.dedent()
            self.write(")")

    def pretty_export(self, msg: transactions_pb2.Export):
        flat1226 = self._try_flat(msg, self.pretty_export)
        if flat1226 is not None:
            assert flat1226 is not None
            self.write(flat1226)
            return None
        else:
            def _t1627(_dollar_dollar):
                return _dollar_dollar.csv_config
            _t1628 = _t1627(msg)
            fields1224 = _t1628
            assert fields1224 is not None
            unwrapped_fields1225 = fields1224
            self.write("(")
            self.write("export")
            self.indent_sexp()
            self.newline()
            self.pretty_export_csv_config(unwrapped_fields1225)
            self.dedent()
            self.write(")")

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig):
        flat1232 = self._try_flat(msg, self.pretty_export_csv_config)
        if flat1232 is not None:
            assert flat1232 is not None
            self.write(flat1232)
            return None
        else:
            def _t1629(_dollar_dollar):
                _t1630 = self.deconstruct_export_csv_config(_dollar_dollar)
                return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1630,)
            _t1631 = _t1629(msg)
            fields1227 = _t1631
            assert fields1227 is not None
            unwrapped_fields1228 = fields1227
            self.write("(")
            self.write("export_csv_config")
            self.indent_sexp()
            self.newline()
            field1229 = unwrapped_fields1228[0]
            self.pretty_export_csv_path(field1229)
            self.newline()
            field1230 = unwrapped_fields1228[1]
            self.pretty_export_csv_columns(field1230)
            self.newline()
            field1231 = unwrapped_fields1228[2]
            self.pretty_config_dict(field1231)
            self.dedent()
            self.write(")")

    def pretty_export_csv_path(self, msg: str):
        flat1234 = self._try_flat(msg, self.pretty_export_csv_path)
        if flat1234 is not None:
            assert flat1234 is not None
            self.write(flat1234)
            return None
        else:
            fields1233 = msg
            self.write("(")
            self.write("path")
            self.indent_sexp()
            self.newline()
            self.write(self.format_string_value(fields1233))
            self.dedent()
            self.write(")")

    def pretty_export_csv_columns(self, msg: Sequence[transactions_pb2.ExportCSVColumn]):
        flat1238 = self._try_flat(msg, self.pretty_export_csv_columns)
        if flat1238 is not None:
            assert flat1238 is not None
            self.write(flat1238)
            return None
        else:
            fields1235 = msg
            self.write("(")
            self.write("columns")
            self.indent_sexp()
            if not len(fields1235) == 0:
                self.newline()
                for i1237, elem1236 in enumerate(fields1235):
                    if (i1237 > 0):
                        self.newline()
                    self.pretty_export_csv_column(elem1236)
            self.dedent()
            self.write(")")

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn):
        flat1243 = self._try_flat(msg, self.pretty_export_csv_column)
        if flat1243 is not None:
            assert flat1243 is not None
            self.write(flat1243)
            return None
        else:
            def _t1632(_dollar_dollar):
                return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
            _t1633 = _t1632(msg)
            fields1239 = _t1633
            assert fields1239 is not None
            unwrapped_fields1240 = fields1239
            self.write("(")
            self.write("column")
            self.indent_sexp()
            self.newline()
            field1241 = unwrapped_fields1240[0]
            self.write(self.format_string_value(field1241))
            self.newline()
            field1242 = unwrapped_fields1240[1]
            self.pretty_relation_id(field1242)
            self.dedent()
            self.write(")")


def pretty(msg: Any, io: Optional[IO[str]] = None, max_width: int = 92) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io, max_width=max_width)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()
