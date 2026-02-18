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
        _t1580 = logic_pb2.Value(int_value=int(v))
        return _t1580

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1581 = logic_pb2.Value(int_value=v)
        return _t1581

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1582 = logic_pb2.Value(float_value=v)
        return _t1582

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1583 = logic_pb2.Value(string_value=v)
        return _t1583

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1584 = logic_pb2.Value(boolean_value=v)
        return _t1584

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1585 = logic_pb2.Value(uint128_value=v)
        return _t1585

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1586 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1586,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1587 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1587,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1588 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1588,))
        _t1589 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1589,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1590 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1590,))
        _t1591 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1591,))
        if msg.new_line != "":
            _t1592 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1592,))
        _t1593 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1593,))
        _t1594 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1594,))
        _t1595 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1595,))
        if msg.comment != "":
            _t1596 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1596,))
        for missing_string in msg.missing_strings:
            _t1597 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1597,))
        _t1598 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1598,))
        _t1599 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1599,))
        _t1600 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1600,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1601 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1601,))
        _t1602 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1602,))
        _t1603 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1603,))
        _t1604 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1604,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1605 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1605,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1606 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1606,))
        _t1607 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1607,))
        _t1608 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1608,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1609 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1609,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1610 = self._make_value_string(msg.compression)
            result.append(("compression", _t1610,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1611 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1611,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1612 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1612,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1613 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1613,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1614 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1614,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1615 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1615,))
        return sorted(result)

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> Optional[str]:
        name = self.relation_id_to_string(msg)
        if name != "":
            return name
        else:
            _t1616 = None
        return None

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name == "":
            return self.relation_id_to_uint128(msg)
        else:
            _t1617 = None
        return None

    def deconstruct_bindings(self, abs: logic_pb2.Abstraction) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        n = len(abs.vars)
        return (abs.vars[0:n], [],)

    def deconstruct_bindings_with_arity(self, abs: logic_pb2.Abstraction, value_arity: int) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        n = len(abs.vars)
        key_end = (n - value_arity)
        return (abs.vars[0:key_end], abs.vars[key_end:n],)

    # --- Pretty-print methods ---

    def pretty_transaction(self, msg: transactions_pb2.Transaction) -> None:
        _flat = self._try_flat(msg, self.pretty_transaction)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1114(_dollar_dollar):
            if _dollar_dollar.HasField("configure"):
                _t1115 = _dollar_dollar.configure
            else:
                _t1115 = None
            if _dollar_dollar.HasField("sync"):
                _t1116 = _dollar_dollar.sync
            else:
                _t1116 = None
            return (_t1115, _t1116, _dollar_dollar.epochs,)
        _t1117 = _t1114(msg)
        fields557 = _t1117
        assert fields557 is not None
        unwrapped_fields558 = fields557
        self.write("(")
        self.write("transaction")
        self.indent_sexp()
        field559 = unwrapped_fields558[0]
        if field559 is not None:
            self.newline()
            assert field559 is not None
            opt_val560 = field559
            self.pretty_configure(opt_val560)
        field561 = unwrapped_fields558[1]
        if field561 is not None:
            self.newline()
            assert field561 is not None
            opt_val562 = field561
            self.pretty_sync(opt_val562)
        field563 = unwrapped_fields558[2]
        if not len(field563) == 0:
            self.newline()
            for i565, elem564 in enumerate(field563):
                if (i565 > 0):
                    self.newline()
                self.pretty_epoch(elem564)
        self.dedent()
        self.write(")")
        return None

    def pretty_configure(self, msg: transactions_pb2.Configure) -> None:
        _flat = self._try_flat(msg, self.pretty_configure)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1118(_dollar_dollar):
            _t1119 = self.deconstruct_configure(_dollar_dollar)
            return _t1119
        _t1120 = _t1118(msg)
        fields566 = _t1120
        assert fields566 is not None
        unwrapped_fields567 = fields566
        self.write("(")
        self.write("configure")
        self.indent_sexp()
        self.newline()
        self.pretty_config_dict(unwrapped_fields567)
        self.dedent()
        self.write(")")
        return None

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]) -> None:
        _flat = self._try_flat(msg, self.pretty_config_dict)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1121(_dollar_dollar):
            return _dollar_dollar
        _t1122 = _t1121(msg)
        fields568 = _t1122
        assert fields568 is not None
        unwrapped_fields569 = fields568
        self.write("{")
        if not len(unwrapped_fields569) == 0:
            self.newline()
            for i571, elem570 in enumerate(unwrapped_fields569):
                if (i571 > 0):
                    self.newline()
                self.pretty_config_key_value(elem570)
        self.write("}")
        return None

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]) -> None:
        _flat = self._try_flat(msg, self.pretty_config_key_value)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1123(_dollar_dollar):
            return (_dollar_dollar[0], _dollar_dollar[1],)
        _t1124 = _t1123(msg)
        fields572 = _t1124
        assert fields572 is not None
        unwrapped_fields573 = fields572
        self.write(":")
        field574 = unwrapped_fields573[0]
        self.write(field574)
        self.write(" ")
        field575 = unwrapped_fields573[1]
        self.pretty_value(field575)
        return None

    def pretty_value(self, msg: logic_pb2.Value) -> None:
        _flat = self._try_flat(msg, self.pretty_value)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1125(_dollar_dollar):
            if _dollar_dollar.HasField("date_value"):
                _t1126 = _dollar_dollar.date_value
            else:
                _t1126 = None
            return _t1126
        _t1127 = _t1125(msg)
        deconstruct_result594 = _t1127
        if deconstruct_result594 is not None:
            assert deconstruct_result594 is not None
            unwrapped595 = deconstruct_result594
            self.pretty_date(unwrapped595)
        else:
            def _t1128(_dollar_dollar):
                if _dollar_dollar.HasField("datetime_value"):
                    _t1129 = _dollar_dollar.datetime_value
                else:
                    _t1129 = None
                return _t1129
            _t1130 = _t1128(msg)
            deconstruct_result592 = _t1130
            if deconstruct_result592 is not None:
                assert deconstruct_result592 is not None
                unwrapped593 = deconstruct_result592
                self.pretty_datetime(unwrapped593)
            else:
                def _t1131(_dollar_dollar):
                    if _dollar_dollar.HasField("string_value"):
                        _t1132 = _dollar_dollar.string_value
                    else:
                        _t1132 = None
                    return _t1132
                _t1133 = _t1131(msg)
                deconstruct_result590 = _t1133
                if deconstruct_result590 is not None:
                    assert deconstruct_result590 is not None
                    unwrapped591 = deconstruct_result590
                    self.write(self.format_string_value(unwrapped591))
                else:
                    def _t1134(_dollar_dollar):
                        if _dollar_dollar.HasField("int_value"):
                            _t1135 = _dollar_dollar.int_value
                        else:
                            _t1135 = None
                        return _t1135
                    _t1136 = _t1134(msg)
                    deconstruct_result588 = _t1136
                    if deconstruct_result588 is not None:
                        assert deconstruct_result588 is not None
                        unwrapped589 = deconstruct_result588
                        self.write(str(unwrapped589))
                    else:
                        def _t1137(_dollar_dollar):
                            if _dollar_dollar.HasField("float_value"):
                                _t1138 = _dollar_dollar.float_value
                            else:
                                _t1138 = None
                            return _t1138
                        _t1139 = _t1137(msg)
                        deconstruct_result586 = _t1139
                        if deconstruct_result586 is not None:
                            assert deconstruct_result586 is not None
                            unwrapped587 = deconstruct_result586
                            self.write(str(unwrapped587))
                        else:
                            def _t1140(_dollar_dollar):
                                if _dollar_dollar.HasField("uint128_value"):
                                    _t1141 = _dollar_dollar.uint128_value
                                else:
                                    _t1141 = None
                                return _t1141
                            _t1142 = _t1140(msg)
                            deconstruct_result584 = _t1142
                            if deconstruct_result584 is not None:
                                assert deconstruct_result584 is not None
                                unwrapped585 = deconstruct_result584
                                self.write(self.format_uint128(unwrapped585))
                            else:
                                def _t1143(_dollar_dollar):
                                    if _dollar_dollar.HasField("int128_value"):
                                        _t1144 = _dollar_dollar.int128_value
                                    else:
                                        _t1144 = None
                                    return _t1144
                                _t1145 = _t1143(msg)
                                deconstruct_result582 = _t1145
                                if deconstruct_result582 is not None:
                                    assert deconstruct_result582 is not None
                                    unwrapped583 = deconstruct_result582
                                    self.write(self.format_int128(unwrapped583))
                                else:
                                    def _t1146(_dollar_dollar):
                                        if _dollar_dollar.HasField("decimal_value"):
                                            _t1147 = _dollar_dollar.decimal_value
                                        else:
                                            _t1147 = None
                                        return _t1147
                                    _t1148 = _t1146(msg)
                                    deconstruct_result580 = _t1148
                                    if deconstruct_result580 is not None:
                                        assert deconstruct_result580 is not None
                                        unwrapped581 = deconstruct_result580
                                        self.write(self.format_decimal(unwrapped581))
                                    else:
                                        def _t1149(_dollar_dollar):
                                            if _dollar_dollar.HasField("boolean_value"):
                                                _t1150 = _dollar_dollar.boolean_value
                                            else:
                                                _t1150 = None
                                            return _t1150
                                        _t1151 = _t1149(msg)
                                        deconstruct_result578 = _t1151
                                        if deconstruct_result578 is not None:
                                            assert deconstruct_result578 is not None
                                            unwrapped579 = deconstruct_result578
                                            self.pretty_boolean_value(unwrapped579)
                                        else:
                                            def _t1152(_dollar_dollar):
                                                return _dollar_dollar
                                            _t1153 = _t1152(msg)
                                            fields576 = _t1153
                                            assert fields576 is not None
                                            unwrapped_fields577 = fields576
                                            self.write("missing")
        return None

    def pretty_date(self, msg: logic_pb2.DateValue) -> None:
        _flat = self._try_flat(msg, self.pretty_date)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1154(_dollar_dollar):
            return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
        _t1155 = _t1154(msg)
        fields596 = _t1155
        assert fields596 is not None
        unwrapped_fields597 = fields596
        self.write("(")
        self.write("date")
        self.indent_sexp()
        self.newline()
        field598 = unwrapped_fields597[0]
        self.write(str(field598))
        self.newline()
        field599 = unwrapped_fields597[1]
        self.write(str(field599))
        self.newline()
        field600 = unwrapped_fields597[2]
        self.write(str(field600))
        self.dedent()
        self.write(")")
        return None

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue) -> None:
        _flat = self._try_flat(msg, self.pretty_datetime)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1156(_dollar_dollar):
            return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
        _t1157 = _t1156(msg)
        fields601 = _t1157
        assert fields601 is not None
        unwrapped_fields602 = fields601
        self.write("(")
        self.write("datetime")
        self.indent_sexp()
        self.newline()
        field603 = unwrapped_fields602[0]
        self.write(str(field603))
        self.newline()
        field604 = unwrapped_fields602[1]
        self.write(str(field604))
        self.newline()
        field605 = unwrapped_fields602[2]
        self.write(str(field605))
        self.newline()
        field606 = unwrapped_fields602[3]
        self.write(str(field606))
        self.newline()
        field607 = unwrapped_fields602[4]
        self.write(str(field607))
        self.newline()
        field608 = unwrapped_fields602[5]
        self.write(str(field608))
        field609 = unwrapped_fields602[6]
        if field609 is not None:
            self.newline()
            assert field609 is not None
            opt_val610 = field609
            self.write(str(opt_val610))
        self.dedent()
        self.write(")")
        return None

    def pretty_boolean_value(self, msg: bool) -> None:
        _flat = self._try_flat(msg, self.pretty_boolean_value)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1158(_dollar_dollar):
            if _dollar_dollar:
                _t1159 = ()
            else:
                _t1159 = None
            return _t1159
        _t1160 = _t1158(msg)
        deconstruct_result613 = _t1160
        if deconstruct_result613 is not None:
            assert deconstruct_result613 is not None
            unwrapped614 = deconstruct_result613
            self.write("true")
        else:
            def _t1161(_dollar_dollar):
                if not _dollar_dollar:
                    _t1162 = ()
                else:
                    _t1162 = None
                return _t1162
            _t1163 = _t1161(msg)
            deconstruct_result611 = _t1163
            if deconstruct_result611 is not None:
                assert deconstruct_result611 is not None
                unwrapped612 = deconstruct_result611
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")
        return None

    def pretty_sync(self, msg: transactions_pb2.Sync) -> None:
        _flat = self._try_flat(msg, self.pretty_sync)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1164(_dollar_dollar):
            return _dollar_dollar.fragments
        _t1165 = _t1164(msg)
        fields615 = _t1165
        assert fields615 is not None
        unwrapped_fields616 = fields615
        self.write("(")
        self.write("sync")
        self.indent_sexp()
        if not len(unwrapped_fields616) == 0:
            self.newline()
            for i618, elem617 in enumerate(unwrapped_fields616):
                if (i618 > 0):
                    self.newline()
                self.pretty_fragment_id(elem617)
        self.dedent()
        self.write(")")
        return None

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId) -> None:
        _flat = self._try_flat(msg, self.pretty_fragment_id)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1166(_dollar_dollar):
            return self.fragment_id_to_string(_dollar_dollar)
        _t1167 = _t1166(msg)
        fields619 = _t1167
        assert fields619 is not None
        unwrapped_fields620 = fields619
        self.write(":")
        self.write(unwrapped_fields620)
        return None

    def pretty_epoch(self, msg: transactions_pb2.Epoch) -> None:
        _flat = self._try_flat(msg, self.pretty_epoch)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1168(_dollar_dollar):
            if not len(_dollar_dollar.writes) == 0:
                _t1169 = _dollar_dollar.writes
            else:
                _t1169 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1170 = _dollar_dollar.reads
            else:
                _t1170 = None
            return (_t1169, _t1170,)
        _t1171 = _t1168(msg)
        fields621 = _t1171
        assert fields621 is not None
        unwrapped_fields622 = fields621
        self.write("(")
        self.write("epoch")
        self.indent_sexp()
        field623 = unwrapped_fields622[0]
        if field623 is not None:
            self.newline()
            assert field623 is not None
            opt_val624 = field623
            self.pretty_epoch_writes(opt_val624)
        field625 = unwrapped_fields622[1]
        if field625 is not None:
            self.newline()
            assert field625 is not None
            opt_val626 = field625
            self.pretty_epoch_reads(opt_val626)
        self.dedent()
        self.write(")")
        return None

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]) -> None:
        _flat = self._try_flat(msg, self.pretty_epoch_writes)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1172(_dollar_dollar):
            return _dollar_dollar
        _t1173 = _t1172(msg)
        fields627 = _t1173
        assert fields627 is not None
        unwrapped_fields628 = fields627
        self.write("(")
        self.write("writes")
        self.indent_sexp()
        if not len(unwrapped_fields628) == 0:
            self.newline()
            for i630, elem629 in enumerate(unwrapped_fields628):
                if (i630 > 0):
                    self.newline()
                self.pretty_write(elem629)
        self.dedent()
        self.write(")")
        return None

    def pretty_write(self, msg: transactions_pb2.Write) -> None:
        _flat = self._try_flat(msg, self.pretty_write)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1174(_dollar_dollar):
            if _dollar_dollar.HasField("define"):
                _t1175 = _dollar_dollar.define
            else:
                _t1175 = None
            return _t1175
        _t1176 = _t1174(msg)
        deconstruct_result635 = _t1176
        if deconstruct_result635 is not None:
            assert deconstruct_result635 is not None
            unwrapped636 = deconstruct_result635
            self.pretty_define(unwrapped636)
        else:
            def _t1177(_dollar_dollar):
                if _dollar_dollar.HasField("undefine"):
                    _t1178 = _dollar_dollar.undefine
                else:
                    _t1178 = None
                return _t1178
            _t1179 = _t1177(msg)
            deconstruct_result633 = _t1179
            if deconstruct_result633 is not None:
                assert deconstruct_result633 is not None
                unwrapped634 = deconstruct_result633
                self.pretty_undefine(unwrapped634)
            else:
                def _t1180(_dollar_dollar):
                    if _dollar_dollar.HasField("context"):
                        _t1181 = _dollar_dollar.context
                    else:
                        _t1181 = None
                    return _t1181
                _t1182 = _t1180(msg)
                deconstruct_result631 = _t1182
                if deconstruct_result631 is not None:
                    assert deconstruct_result631 is not None
                    unwrapped632 = deconstruct_result631
                    self.pretty_context(unwrapped632)
                else:
                    raise ParseError("No matching rule for write")
        return None

    def pretty_define(self, msg: transactions_pb2.Define) -> None:
        _flat = self._try_flat(msg, self.pretty_define)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1183(_dollar_dollar):
            return _dollar_dollar.fragment
        _t1184 = _t1183(msg)
        fields637 = _t1184
        assert fields637 is not None
        unwrapped_fields638 = fields637
        self.write("(")
        self.write("define")
        self.indent_sexp()
        self.newline()
        self.pretty_fragment(unwrapped_fields638)
        self.dedent()
        self.write(")")
        return None

    def pretty_fragment(self, msg: fragments_pb2.Fragment) -> None:
        _flat = self._try_flat(msg, self.pretty_fragment)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1185(_dollar_dollar):
            self.start_pretty_fragment(_dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        _t1186 = _t1185(msg)
        fields639 = _t1186
        assert fields639 is not None
        unwrapped_fields640 = fields639
        self.write("(")
        self.write("fragment")
        self.indent_sexp()
        self.newline()
        field641 = unwrapped_fields640[0]
        self.pretty_new_fragment_id(field641)
        field642 = unwrapped_fields640[1]
        if not len(field642) == 0:
            self.newline()
            for i644, elem643 in enumerate(field642):
                if (i644 > 0):
                    self.newline()
                self.pretty_declaration(elem643)
        self.dedent()
        self.write(")")
        return None

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId) -> None:
        _flat = self._try_flat(msg, self.pretty_new_fragment_id)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1187(_dollar_dollar):
            return _dollar_dollar
        _t1188 = _t1187(msg)
        fields645 = _t1188
        assert fields645 is not None
        unwrapped_fields646 = fields645
        self.pretty_fragment_id(unwrapped_fields646)
        return None

    def pretty_declaration(self, msg: logic_pb2.Declaration) -> None:
        _flat = self._try_flat(msg, self.pretty_declaration)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1189(_dollar_dollar):
            if _dollar_dollar.HasField("def"):
                _t1190 = getattr(_dollar_dollar, 'def')
            else:
                _t1190 = None
            return _t1190
        _t1191 = _t1189(msg)
        deconstruct_result653 = _t1191
        if deconstruct_result653 is not None:
            assert deconstruct_result653 is not None
            unwrapped654 = deconstruct_result653
            self.pretty_def(unwrapped654)
        else:
            def _t1192(_dollar_dollar):
                if _dollar_dollar.HasField("algorithm"):
                    _t1193 = _dollar_dollar.algorithm
                else:
                    _t1193 = None
                return _t1193
            _t1194 = _t1192(msg)
            deconstruct_result651 = _t1194
            if deconstruct_result651 is not None:
                assert deconstruct_result651 is not None
                unwrapped652 = deconstruct_result651
                self.pretty_algorithm(unwrapped652)
            else:
                def _t1195(_dollar_dollar):
                    if _dollar_dollar.HasField("constraint"):
                        _t1196 = _dollar_dollar.constraint
                    else:
                        _t1196 = None
                    return _t1196
                _t1197 = _t1195(msg)
                deconstruct_result649 = _t1197
                if deconstruct_result649 is not None:
                    assert deconstruct_result649 is not None
                    unwrapped650 = deconstruct_result649
                    self.pretty_constraint(unwrapped650)
                else:
                    def _t1198(_dollar_dollar):
                        if _dollar_dollar.HasField("data"):
                            _t1199 = _dollar_dollar.data
                        else:
                            _t1199 = None
                        return _t1199
                    _t1200 = _t1198(msg)
                    deconstruct_result647 = _t1200
                    if deconstruct_result647 is not None:
                        assert deconstruct_result647 is not None
                        unwrapped648 = deconstruct_result647
                        self.pretty_data(unwrapped648)
                    else:
                        raise ParseError("No matching rule for declaration")
        return None

    def pretty_def(self, msg: logic_pb2.Def) -> None:
        _flat = self._try_flat(msg, self.pretty_def)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1201(_dollar_dollar):
            if not len(_dollar_dollar.attrs) == 0:
                _t1202 = _dollar_dollar.attrs
            else:
                _t1202 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1202,)
        _t1203 = _t1201(msg)
        fields655 = _t1203
        assert fields655 is not None
        unwrapped_fields656 = fields655
        self.write("(")
        self.write("def")
        self.indent_sexp()
        self.newline()
        field657 = unwrapped_fields656[0]
        self.pretty_relation_id(field657)
        self.newline()
        field658 = unwrapped_fields656[1]
        self.pretty_abstraction(field658)
        field659 = unwrapped_fields656[2]
        if field659 is not None:
            self.newline()
            assert field659 is not None
            opt_val660 = field659
            self.pretty_attrs(opt_val660)
        self.dedent()
        self.write(")")
        return None

    def pretty_relation_id(self, msg: logic_pb2.RelationId) -> None:
        _flat = self._try_flat(msg, self.pretty_relation_id)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1204(_dollar_dollar):
            _t1205 = self.deconstruct_relation_id_string(_dollar_dollar)
            return _t1205
        _t1206 = _t1204(msg)
        deconstruct_result663 = _t1206
        if deconstruct_result663 is not None:
            assert deconstruct_result663 is not None
            unwrapped664 = deconstruct_result663
            self.write(":")
            self.write(unwrapped664)
        else:
            def _t1207(_dollar_dollar):
                _t1208 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                return _t1208
            _t1209 = _t1207(msg)
            deconstruct_result661 = _t1209
            if deconstruct_result661 is not None:
                assert deconstruct_result661 is not None
                unwrapped662 = deconstruct_result661
                self.write(self.format_uint128(unwrapped662))
            else:
                raise ParseError("No matching rule for relation_id")
        return None

    def pretty_abstraction(self, msg: logic_pb2.Abstraction) -> None:
        _flat = self._try_flat(msg, self.pretty_abstraction)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1210(_dollar_dollar):
            _t1211 = self.deconstruct_bindings(_dollar_dollar)
            return (_t1211, _dollar_dollar.value,)
        _t1212 = _t1210(msg)
        fields665 = _t1212
        assert fields665 is not None
        unwrapped_fields666 = fields665
        self.write("(")
        self.indent()
        field667 = unwrapped_fields666[0]
        self.pretty_bindings(field667)
        self.newline()
        field668 = unwrapped_fields666[1]
        self.pretty_formula(field668)
        self.dedent()
        self.write(")")
        return None

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]) -> None:
        _flat = self._try_flat(msg, self.pretty_bindings)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1213(_dollar_dollar):
            if not len(_dollar_dollar[1]) == 0:
                _t1214 = _dollar_dollar[1]
            else:
                _t1214 = None
            return (_dollar_dollar[0], _t1214,)
        _t1215 = _t1213(msg)
        fields669 = _t1215
        assert fields669 is not None
        unwrapped_fields670 = fields669
        self.write("[")
        self.indent()
        field671 = unwrapped_fields670[0]
        for i673, elem672 in enumerate(field671):
            if (i673 > 0):
                self.newline()
            self.pretty_binding(elem672)
        field674 = unwrapped_fields670[1]
        if field674 is not None:
            self.newline()
            assert field674 is not None
            opt_val675 = field674
            self.pretty_value_bindings(opt_val675)
        self.dedent()
        self.write("]")
        return None

    def pretty_binding(self, msg: logic_pb2.Binding) -> None:
        _flat = self._try_flat(msg, self.pretty_binding)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1216(_dollar_dollar):
            return (_dollar_dollar.var.name, _dollar_dollar.type,)
        _t1217 = _t1216(msg)
        fields676 = _t1217
        assert fields676 is not None
        unwrapped_fields677 = fields676
        field678 = unwrapped_fields677[0]
        self.write(field678)
        self.write("::")
        field679 = unwrapped_fields677[1]
        self.pretty_type(field679)
        return None

    def pretty_type(self, msg: logic_pb2.Type) -> None:
        _flat = self._try_flat(msg, self.pretty_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1218(_dollar_dollar):
            if _dollar_dollar.HasField("unspecified_type"):
                _t1219 = _dollar_dollar.unspecified_type
            else:
                _t1219 = None
            return _t1219
        _t1220 = _t1218(msg)
        deconstruct_result700 = _t1220
        if deconstruct_result700 is not None:
            assert deconstruct_result700 is not None
            unwrapped701 = deconstruct_result700
            self.pretty_unspecified_type(unwrapped701)
        else:
            def _t1221(_dollar_dollar):
                if _dollar_dollar.HasField("string_type"):
                    _t1222 = _dollar_dollar.string_type
                else:
                    _t1222 = None
                return _t1222
            _t1223 = _t1221(msg)
            deconstruct_result698 = _t1223
            if deconstruct_result698 is not None:
                assert deconstruct_result698 is not None
                unwrapped699 = deconstruct_result698
                self.pretty_string_type(unwrapped699)
            else:
                def _t1224(_dollar_dollar):
                    if _dollar_dollar.HasField("int_type"):
                        _t1225 = _dollar_dollar.int_type
                    else:
                        _t1225 = None
                    return _t1225
                _t1226 = _t1224(msg)
                deconstruct_result696 = _t1226
                if deconstruct_result696 is not None:
                    assert deconstruct_result696 is not None
                    unwrapped697 = deconstruct_result696
                    self.pretty_int_type(unwrapped697)
                else:
                    def _t1227(_dollar_dollar):
                        if _dollar_dollar.HasField("float_type"):
                            _t1228 = _dollar_dollar.float_type
                        else:
                            _t1228 = None
                        return _t1228
                    _t1229 = _t1227(msg)
                    deconstruct_result694 = _t1229
                    if deconstruct_result694 is not None:
                        assert deconstruct_result694 is not None
                        unwrapped695 = deconstruct_result694
                        self.pretty_float_type(unwrapped695)
                    else:
                        def _t1230(_dollar_dollar):
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1231 = _dollar_dollar.uint128_type
                            else:
                                _t1231 = None
                            return _t1231
                        _t1232 = _t1230(msg)
                        deconstruct_result692 = _t1232
                        if deconstruct_result692 is not None:
                            assert deconstruct_result692 is not None
                            unwrapped693 = deconstruct_result692
                            self.pretty_uint128_type(unwrapped693)
                        else:
                            def _t1233(_dollar_dollar):
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1234 = _dollar_dollar.int128_type
                                else:
                                    _t1234 = None
                                return _t1234
                            _t1235 = _t1233(msg)
                            deconstruct_result690 = _t1235
                            if deconstruct_result690 is not None:
                                assert deconstruct_result690 is not None
                                unwrapped691 = deconstruct_result690
                                self.pretty_int128_type(unwrapped691)
                            else:
                                def _t1236(_dollar_dollar):
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1237 = _dollar_dollar.date_type
                                    else:
                                        _t1237 = None
                                    return _t1237
                                _t1238 = _t1236(msg)
                                deconstruct_result688 = _t1238
                                if deconstruct_result688 is not None:
                                    assert deconstruct_result688 is not None
                                    unwrapped689 = deconstruct_result688
                                    self.pretty_date_type(unwrapped689)
                                else:
                                    def _t1239(_dollar_dollar):
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1240 = _dollar_dollar.datetime_type
                                        else:
                                            _t1240 = None
                                        return _t1240
                                    _t1241 = _t1239(msg)
                                    deconstruct_result686 = _t1241
                                    if deconstruct_result686 is not None:
                                        assert deconstruct_result686 is not None
                                        unwrapped687 = deconstruct_result686
                                        self.pretty_datetime_type(unwrapped687)
                                    else:
                                        def _t1242(_dollar_dollar):
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1243 = _dollar_dollar.missing_type
                                            else:
                                                _t1243 = None
                                            return _t1243
                                        _t1244 = _t1242(msg)
                                        deconstruct_result684 = _t1244
                                        if deconstruct_result684 is not None:
                                            assert deconstruct_result684 is not None
                                            unwrapped685 = deconstruct_result684
                                            self.pretty_missing_type(unwrapped685)
                                        else:
                                            def _t1245(_dollar_dollar):
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1246 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1246 = None
                                                return _t1246
                                            _t1247 = _t1245(msg)
                                            deconstruct_result682 = _t1247
                                            if deconstruct_result682 is not None:
                                                assert deconstruct_result682 is not None
                                                unwrapped683 = deconstruct_result682
                                                self.pretty_decimal_type(unwrapped683)
                                            else:
                                                def _t1248(_dollar_dollar):
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1249 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1249 = None
                                                    return _t1249
                                                _t1250 = _t1248(msg)
                                                deconstruct_result680 = _t1250
                                                if deconstruct_result680 is not None:
                                                    assert deconstruct_result680 is not None
                                                    unwrapped681 = deconstruct_result680
                                                    self.pretty_boolean_type(unwrapped681)
                                                else:
                                                    raise ParseError("No matching rule for type")
        return None

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType) -> None:
        _flat = self._try_flat(msg, self.pretty_unspecified_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1251(_dollar_dollar):
            return _dollar_dollar
        _t1252 = _t1251(msg)
        fields702 = _t1252
        assert fields702 is not None
        unwrapped_fields703 = fields702
        self.write("UNKNOWN")
        return None

    def pretty_string_type(self, msg: logic_pb2.StringType) -> None:
        _flat = self._try_flat(msg, self.pretty_string_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1253(_dollar_dollar):
            return _dollar_dollar
        _t1254 = _t1253(msg)
        fields704 = _t1254
        assert fields704 is not None
        unwrapped_fields705 = fields704
        self.write("STRING")
        return None

    def pretty_int_type(self, msg: logic_pb2.IntType) -> None:
        _flat = self._try_flat(msg, self.pretty_int_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1255(_dollar_dollar):
            return _dollar_dollar
        _t1256 = _t1255(msg)
        fields706 = _t1256
        assert fields706 is not None
        unwrapped_fields707 = fields706
        self.write("INT")
        return None

    def pretty_float_type(self, msg: logic_pb2.FloatType) -> None:
        _flat = self._try_flat(msg, self.pretty_float_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1257(_dollar_dollar):
            return _dollar_dollar
        _t1258 = _t1257(msg)
        fields708 = _t1258
        assert fields708 is not None
        unwrapped_fields709 = fields708
        self.write("FLOAT")
        return None

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type) -> None:
        _flat = self._try_flat(msg, self.pretty_uint128_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1259(_dollar_dollar):
            return _dollar_dollar
        _t1260 = _t1259(msg)
        fields710 = _t1260
        assert fields710 is not None
        unwrapped_fields711 = fields710
        self.write("UINT128")
        return None

    def pretty_int128_type(self, msg: logic_pb2.Int128Type) -> None:
        _flat = self._try_flat(msg, self.pretty_int128_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1261(_dollar_dollar):
            return _dollar_dollar
        _t1262 = _t1261(msg)
        fields712 = _t1262
        assert fields712 is not None
        unwrapped_fields713 = fields712
        self.write("INT128")
        return None

    def pretty_date_type(self, msg: logic_pb2.DateType) -> None:
        _flat = self._try_flat(msg, self.pretty_date_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1263(_dollar_dollar):
            return _dollar_dollar
        _t1264 = _t1263(msg)
        fields714 = _t1264
        assert fields714 is not None
        unwrapped_fields715 = fields714
        self.write("DATE")
        return None

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType) -> None:
        _flat = self._try_flat(msg, self.pretty_datetime_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1265(_dollar_dollar):
            return _dollar_dollar
        _t1266 = _t1265(msg)
        fields716 = _t1266
        assert fields716 is not None
        unwrapped_fields717 = fields716
        self.write("DATETIME")
        return None

    def pretty_missing_type(self, msg: logic_pb2.MissingType) -> None:
        _flat = self._try_flat(msg, self.pretty_missing_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1267(_dollar_dollar):
            return _dollar_dollar
        _t1268 = _t1267(msg)
        fields718 = _t1268
        assert fields718 is not None
        unwrapped_fields719 = fields718
        self.write("MISSING")
        return None

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType) -> None:
        _flat = self._try_flat(msg, self.pretty_decimal_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1269(_dollar_dollar):
            return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
        _t1270 = _t1269(msg)
        fields720 = _t1270
        assert fields720 is not None
        unwrapped_fields721 = fields720
        self.write("(")
        self.write("DECIMAL")
        self.indent_sexp()
        self.newline()
        field722 = unwrapped_fields721[0]
        self.write(str(field722))
        self.newline()
        field723 = unwrapped_fields721[1]
        self.write(str(field723))
        self.dedent()
        self.write(")")
        return None

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType) -> None:
        _flat = self._try_flat(msg, self.pretty_boolean_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1271(_dollar_dollar):
            return _dollar_dollar
        _t1272 = _t1271(msg)
        fields724 = _t1272
        assert fields724 is not None
        unwrapped_fields725 = fields724
        self.write("BOOLEAN")
        return None

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]) -> None:
        _flat = self._try_flat(msg, self.pretty_value_bindings)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1273(_dollar_dollar):
            return _dollar_dollar
        _t1274 = _t1273(msg)
        fields726 = _t1274
        assert fields726 is not None
        unwrapped_fields727 = fields726
        self.write("|")
        if not len(unwrapped_fields727) == 0:
            self.write(" ")
            for i729, elem728 in enumerate(unwrapped_fields727):
                if (i729 > 0):
                    self.newline()
                self.pretty_binding(elem728)
        return None

    def pretty_formula(self, msg: logic_pb2.Formula) -> None:
        _flat = self._try_flat(msg, self.pretty_formula)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1275(_dollar_dollar):
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1276 = _dollar_dollar.conjunction
            else:
                _t1276 = None
            return _t1276
        _t1277 = _t1275(msg)
        deconstruct_result754 = _t1277
        if deconstruct_result754 is not None:
            assert deconstruct_result754 is not None
            unwrapped755 = deconstruct_result754
            self.pretty_true(unwrapped755)
        else:
            def _t1278(_dollar_dollar):
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1279 = _dollar_dollar.disjunction
                else:
                    _t1279 = None
                return _t1279
            _t1280 = _t1278(msg)
            deconstruct_result752 = _t1280
            if deconstruct_result752 is not None:
                assert deconstruct_result752 is not None
                unwrapped753 = deconstruct_result752
                self.pretty_false(unwrapped753)
            else:
                def _t1281(_dollar_dollar):
                    if _dollar_dollar.HasField("exists"):
                        _t1282 = _dollar_dollar.exists
                    else:
                        _t1282 = None
                    return _t1282
                _t1283 = _t1281(msg)
                deconstruct_result750 = _t1283
                if deconstruct_result750 is not None:
                    assert deconstruct_result750 is not None
                    unwrapped751 = deconstruct_result750
                    self.pretty_exists(unwrapped751)
                else:
                    def _t1284(_dollar_dollar):
                        if _dollar_dollar.HasField("reduce"):
                            _t1285 = _dollar_dollar.reduce
                        else:
                            _t1285 = None
                        return _t1285
                    _t1286 = _t1284(msg)
                    deconstruct_result748 = _t1286
                    if deconstruct_result748 is not None:
                        assert deconstruct_result748 is not None
                        unwrapped749 = deconstruct_result748
                        self.pretty_reduce(unwrapped749)
                    else:
                        def _t1287(_dollar_dollar):
                            if _dollar_dollar.HasField("conjunction"):
                                _t1288 = _dollar_dollar.conjunction
                            else:
                                _t1288 = None
                            return _t1288
                        _t1289 = _t1287(msg)
                        deconstruct_result746 = _t1289
                        if deconstruct_result746 is not None:
                            assert deconstruct_result746 is not None
                            unwrapped747 = deconstruct_result746
                            self.pretty_conjunction(unwrapped747)
                        else:
                            def _t1290(_dollar_dollar):
                                if _dollar_dollar.HasField("disjunction"):
                                    _t1291 = _dollar_dollar.disjunction
                                else:
                                    _t1291 = None
                                return _t1291
                            _t1292 = _t1290(msg)
                            deconstruct_result744 = _t1292
                            if deconstruct_result744 is not None:
                                assert deconstruct_result744 is not None
                                unwrapped745 = deconstruct_result744
                                self.pretty_disjunction(unwrapped745)
                            else:
                                def _t1293(_dollar_dollar):
                                    if _dollar_dollar.HasField("not"):
                                        _t1294 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1294 = None
                                    return _t1294
                                _t1295 = _t1293(msg)
                                deconstruct_result742 = _t1295
                                if deconstruct_result742 is not None:
                                    assert deconstruct_result742 is not None
                                    unwrapped743 = deconstruct_result742
                                    self.pretty_not(unwrapped743)
                                else:
                                    def _t1296(_dollar_dollar):
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1297 = _dollar_dollar.ffi
                                        else:
                                            _t1297 = None
                                        return _t1297
                                    _t1298 = _t1296(msg)
                                    deconstruct_result740 = _t1298
                                    if deconstruct_result740 is not None:
                                        assert deconstruct_result740 is not None
                                        unwrapped741 = deconstruct_result740
                                        self.pretty_ffi(unwrapped741)
                                    else:
                                        def _t1299(_dollar_dollar):
                                            if _dollar_dollar.HasField("atom"):
                                                _t1300 = _dollar_dollar.atom
                                            else:
                                                _t1300 = None
                                            return _t1300
                                        _t1301 = _t1299(msg)
                                        deconstruct_result738 = _t1301
                                        if deconstruct_result738 is not None:
                                            assert deconstruct_result738 is not None
                                            unwrapped739 = deconstruct_result738
                                            self.pretty_atom(unwrapped739)
                                        else:
                                            def _t1302(_dollar_dollar):
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1303 = _dollar_dollar.pragma
                                                else:
                                                    _t1303 = None
                                                return _t1303
                                            _t1304 = _t1302(msg)
                                            deconstruct_result736 = _t1304
                                            if deconstruct_result736 is not None:
                                                assert deconstruct_result736 is not None
                                                unwrapped737 = deconstruct_result736
                                                self.pretty_pragma(unwrapped737)
                                            else:
                                                def _t1305(_dollar_dollar):
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1306 = _dollar_dollar.primitive
                                                    else:
                                                        _t1306 = None
                                                    return _t1306
                                                _t1307 = _t1305(msg)
                                                deconstruct_result734 = _t1307
                                                if deconstruct_result734 is not None:
                                                    assert deconstruct_result734 is not None
                                                    unwrapped735 = deconstruct_result734
                                                    self.pretty_primitive(unwrapped735)
                                                else:
                                                    def _t1308(_dollar_dollar):
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1309 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1309 = None
                                                        return _t1309
                                                    _t1310 = _t1308(msg)
                                                    deconstruct_result732 = _t1310
                                                    if deconstruct_result732 is not None:
                                                        assert deconstruct_result732 is not None
                                                        unwrapped733 = deconstruct_result732
                                                        self.pretty_rel_atom(unwrapped733)
                                                    else:
                                                        def _t1311(_dollar_dollar):
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1312 = _dollar_dollar.cast
                                                            else:
                                                                _t1312 = None
                                                            return _t1312
                                                        _t1313 = _t1311(msg)
                                                        deconstruct_result730 = _t1313
                                                        if deconstruct_result730 is not None:
                                                            assert deconstruct_result730 is not None
                                                            unwrapped731 = deconstruct_result730
                                                            self.pretty_cast(unwrapped731)
                                                        else:
                                                            raise ParseError("No matching rule for formula")
        return None

    def pretty_true(self, msg: logic_pb2.Conjunction) -> None:
        _flat = self._try_flat(msg, self.pretty_true)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1314(_dollar_dollar):
            return _dollar_dollar
        _t1315 = _t1314(msg)
        fields756 = _t1315
        assert fields756 is not None
        unwrapped_fields757 = fields756
        self.write("(")
        self.write("true")
        self.write(")")
        return None

    def pretty_false(self, msg: logic_pb2.Disjunction) -> None:
        _flat = self._try_flat(msg, self.pretty_false)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1316(_dollar_dollar):
            return _dollar_dollar
        _t1317 = _t1316(msg)
        fields758 = _t1317
        assert fields758 is not None
        unwrapped_fields759 = fields758
        self.write("(")
        self.write("false")
        self.write(")")
        return None

    def pretty_exists(self, msg: logic_pb2.Exists) -> None:
        _flat = self._try_flat(msg, self.pretty_exists)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1318(_dollar_dollar):
            _t1319 = self.deconstruct_bindings(_dollar_dollar.body)
            return (_t1319, _dollar_dollar.body.value,)
        _t1320 = _t1318(msg)
        fields760 = _t1320
        assert fields760 is not None
        unwrapped_fields761 = fields760
        self.write("(")
        self.write("exists")
        self.indent_sexp()
        self.newline()
        field762 = unwrapped_fields761[0]
        self.pretty_bindings(field762)
        self.newline()
        field763 = unwrapped_fields761[1]
        self.pretty_formula(field763)
        self.dedent()
        self.write(")")
        return None

    def pretty_reduce(self, msg: logic_pb2.Reduce) -> None:
        _flat = self._try_flat(msg, self.pretty_reduce)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1321(_dollar_dollar):
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        _t1322 = _t1321(msg)
        fields764 = _t1322
        assert fields764 is not None
        unwrapped_fields765 = fields764
        self.write("(")
        self.write("reduce")
        self.indent_sexp()
        self.newline()
        field766 = unwrapped_fields765[0]
        self.pretty_abstraction(field766)
        self.newline()
        field767 = unwrapped_fields765[1]
        self.pretty_abstraction(field767)
        self.newline()
        field768 = unwrapped_fields765[2]
        self.pretty_terms(field768)
        self.dedent()
        self.write(")")
        return None

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]) -> None:
        _flat = self._try_flat(msg, self.pretty_terms)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1323(_dollar_dollar):
            return _dollar_dollar
        _t1324 = _t1323(msg)
        fields769 = _t1324
        assert fields769 is not None
        unwrapped_fields770 = fields769
        self.write("(")
        self.write("terms")
        self.indent_sexp()
        if not len(unwrapped_fields770) == 0:
            self.newline()
            for i772, elem771 in enumerate(unwrapped_fields770):
                if (i772 > 0):
                    self.newline()
                self.pretty_term(elem771)
        self.dedent()
        self.write(")")
        return None

    def pretty_term(self, msg: logic_pb2.Term) -> None:
        _flat = self._try_flat(msg, self.pretty_term)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1325(_dollar_dollar):
            if _dollar_dollar.HasField("var"):
                _t1326 = _dollar_dollar.var
            else:
                _t1326 = None
            return _t1326
        _t1327 = _t1325(msg)
        deconstruct_result775 = _t1327
        if deconstruct_result775 is not None:
            assert deconstruct_result775 is not None
            unwrapped776 = deconstruct_result775
            self.pretty_var(unwrapped776)
        else:
            def _t1328(_dollar_dollar):
                if _dollar_dollar.HasField("constant"):
                    _t1329 = _dollar_dollar.constant
                else:
                    _t1329 = None
                return _t1329
            _t1330 = _t1328(msg)
            deconstruct_result773 = _t1330
            if deconstruct_result773 is not None:
                assert deconstruct_result773 is not None
                unwrapped774 = deconstruct_result773
                self.pretty_constant(unwrapped774)
            else:
                raise ParseError("No matching rule for term")
        return None

    def pretty_var(self, msg: logic_pb2.Var) -> None:
        _flat = self._try_flat(msg, self.pretty_var)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1331(_dollar_dollar):
            return _dollar_dollar.name
        _t1332 = _t1331(msg)
        fields777 = _t1332
        assert fields777 is not None
        unwrapped_fields778 = fields777
        self.write(unwrapped_fields778)
        return None

    def pretty_constant(self, msg: logic_pb2.Value) -> None:
        _flat = self._try_flat(msg, self.pretty_constant)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1333(_dollar_dollar):
            return _dollar_dollar
        _t1334 = _t1333(msg)
        fields779 = _t1334
        assert fields779 is not None
        unwrapped_fields780 = fields779
        self.pretty_value(unwrapped_fields780)
        return None

    def pretty_conjunction(self, msg: logic_pb2.Conjunction) -> None:
        _flat = self._try_flat(msg, self.pretty_conjunction)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1335(_dollar_dollar):
            return _dollar_dollar.args
        _t1336 = _t1335(msg)
        fields781 = _t1336
        assert fields781 is not None
        unwrapped_fields782 = fields781
        self.write("(")
        self.write("and")
        self.indent_sexp()
        if not len(unwrapped_fields782) == 0:
            self.newline()
            for i784, elem783 in enumerate(unwrapped_fields782):
                if (i784 > 0):
                    self.newline()
                self.pretty_formula(elem783)
        self.dedent()
        self.write(")")
        return None

    def pretty_disjunction(self, msg: logic_pb2.Disjunction) -> None:
        _flat = self._try_flat(msg, self.pretty_disjunction)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1337(_dollar_dollar):
            return _dollar_dollar.args
        _t1338 = _t1337(msg)
        fields785 = _t1338
        assert fields785 is not None
        unwrapped_fields786 = fields785
        self.write("(")
        self.write("or")
        self.indent_sexp()
        if not len(unwrapped_fields786) == 0:
            self.newline()
            for i788, elem787 in enumerate(unwrapped_fields786):
                if (i788 > 0):
                    self.newline()
                self.pretty_formula(elem787)
        self.dedent()
        self.write(")")
        return None

    def pretty_not(self, msg: logic_pb2.Not) -> None:
        _flat = self._try_flat(msg, self.pretty_not)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1339(_dollar_dollar):
            return _dollar_dollar.arg
        _t1340 = _t1339(msg)
        fields789 = _t1340
        assert fields789 is not None
        unwrapped_fields790 = fields789
        self.write("(")
        self.write("not")
        self.indent_sexp()
        self.newline()
        self.pretty_formula(unwrapped_fields790)
        self.dedent()
        self.write(")")
        return None

    def pretty_ffi(self, msg: logic_pb2.FFI) -> None:
        _flat = self._try_flat(msg, self.pretty_ffi)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1341(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        _t1342 = _t1341(msg)
        fields791 = _t1342
        assert fields791 is not None
        unwrapped_fields792 = fields791
        self.write("(")
        self.write("ffi")
        self.indent_sexp()
        self.newline()
        field793 = unwrapped_fields792[0]
        self.pretty_name(field793)
        self.newline()
        field794 = unwrapped_fields792[1]
        self.pretty_ffi_args(field794)
        self.newline()
        field795 = unwrapped_fields792[2]
        self.pretty_terms(field795)
        self.dedent()
        self.write(")")
        return None

    def pretty_name(self, msg: str) -> None:
        _flat = self._try_flat(msg, self.pretty_name)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1343(_dollar_dollar):
            return _dollar_dollar
        _t1344 = _t1343(msg)
        fields796 = _t1344
        assert fields796 is not None
        unwrapped_fields797 = fields796
        self.write(":")
        self.write(unwrapped_fields797)
        return None

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]) -> None:
        _flat = self._try_flat(msg, self.pretty_ffi_args)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1345(_dollar_dollar):
            return _dollar_dollar
        _t1346 = _t1345(msg)
        fields798 = _t1346
        assert fields798 is not None
        unwrapped_fields799 = fields798
        self.write("(")
        self.write("args")
        self.indent_sexp()
        if not len(unwrapped_fields799) == 0:
            self.newline()
            for i801, elem800 in enumerate(unwrapped_fields799):
                if (i801 > 0):
                    self.newline()
                self.pretty_abstraction(elem800)
        self.dedent()
        self.write(")")
        return None

    def pretty_atom(self, msg: logic_pb2.Atom) -> None:
        _flat = self._try_flat(msg, self.pretty_atom)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1347(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t1348 = _t1347(msg)
        fields802 = _t1348
        assert fields802 is not None
        unwrapped_fields803 = fields802
        self.write("(")
        self.write("atom")
        self.indent_sexp()
        self.newline()
        field804 = unwrapped_fields803[0]
        self.pretty_relation_id(field804)
        field805 = unwrapped_fields803[1]
        if not len(field805) == 0:
            self.newline()
            for i807, elem806 in enumerate(field805):
                if (i807 > 0):
                    self.newline()
                self.pretty_term(elem806)
        self.dedent()
        self.write(")")
        return None

    def pretty_pragma(self, msg: logic_pb2.Pragma) -> None:
        _flat = self._try_flat(msg, self.pretty_pragma)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1349(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t1350 = _t1349(msg)
        fields808 = _t1350
        assert fields808 is not None
        unwrapped_fields809 = fields808
        self.write("(")
        self.write("pragma")
        self.indent_sexp()
        self.newline()
        field810 = unwrapped_fields809[0]
        self.pretty_name(field810)
        field811 = unwrapped_fields809[1]
        if not len(field811) == 0:
            self.newline()
            for i813, elem812 in enumerate(field811):
                if (i813 > 0):
                    self.newline()
                self.pretty_term(elem812)
        self.dedent()
        self.write(")")
        return None

    def pretty_primitive(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_primitive)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1351(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1352 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1352 = None
            return _t1352
        _t1353 = _t1351(msg)
        guard_result828 = _t1353
        if guard_result828 is not None:
            self.pretty_eq(msg)
        else:
            def _t1354(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1355 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1355 = None
                return _t1355
            _t1356 = _t1354(msg)
            guard_result827 = _t1356
            if guard_result827 is not None:
                self.pretty_lt(msg)
            else:
                def _t1357(_dollar_dollar):
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1358 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1358 = None
                    return _t1358
                _t1359 = _t1357(msg)
                guard_result826 = _t1359
                if guard_result826 is not None:
                    self.pretty_lt_eq(msg)
                else:
                    def _t1360(_dollar_dollar):
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1361 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1361 = None
                        return _t1361
                    _t1362 = _t1360(msg)
                    guard_result825 = _t1362
                    if guard_result825 is not None:
                        self.pretty_gt(msg)
                    else:
                        def _t1363(_dollar_dollar):
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1364 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1364 = None
                            return _t1364
                        _t1365 = _t1363(msg)
                        guard_result824 = _t1365
                        if guard_result824 is not None:
                            self.pretty_gt_eq(msg)
                        else:
                            def _t1366(_dollar_dollar):
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1367 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1367 = None
                                return _t1367
                            _t1368 = _t1366(msg)
                            guard_result823 = _t1368
                            if guard_result823 is not None:
                                self.pretty_add(msg)
                            else:
                                def _t1369(_dollar_dollar):
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1370 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1370 = None
                                    return _t1370
                                _t1371 = _t1369(msg)
                                guard_result822 = _t1371
                                if guard_result822 is not None:
                                    self.pretty_minus(msg)
                                else:
                                    def _t1372(_dollar_dollar):
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1373 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1373 = None
                                        return _t1373
                                    _t1374 = _t1372(msg)
                                    guard_result821 = _t1374
                                    if guard_result821 is not None:
                                        self.pretty_multiply(msg)
                                    else:
                                        def _t1375(_dollar_dollar):
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1376 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1376 = None
                                            return _t1376
                                        _t1377 = _t1375(msg)
                                        guard_result820 = _t1377
                                        if guard_result820 is not None:
                                            self.pretty_divide(msg)
                                        else:
                                            def _t1378(_dollar_dollar):
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            _t1379 = _t1378(msg)
                                            fields814 = _t1379
                                            assert fields814 is not None
                                            unwrapped_fields815 = fields814
                                            self.write("(")
                                            self.write("primitive")
                                            self.indent_sexp()
                                            self.newline()
                                            field816 = unwrapped_fields815[0]
                                            self.pretty_name(field816)
                                            field817 = unwrapped_fields815[1]
                                            if not len(field817) == 0:
                                                self.newline()
                                                for i819, elem818 in enumerate(field817):
                                                    if (i819 > 0):
                                                        self.newline()
                                                    self.pretty_rel_term(elem818)
                                            self.dedent()
                                            self.write(")")
        return None

    def pretty_eq(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_eq)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1380(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1381 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1381 = None
            return _t1381
        _t1382 = _t1380(msg)
        fields829 = _t1382
        assert fields829 is not None
        unwrapped_fields830 = fields829
        self.write("(")
        self.write("=")
        self.indent_sexp()
        self.newline()
        field831 = unwrapped_fields830[0]
        self.pretty_term(field831)
        self.newline()
        field832 = unwrapped_fields830[1]
        self.pretty_term(field832)
        self.dedent()
        self.write(")")
        return None

    def pretty_lt(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_lt)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1383(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1384 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1384 = None
            return _t1384
        _t1385 = _t1383(msg)
        fields833 = _t1385
        assert fields833 is not None
        unwrapped_fields834 = fields833
        self.write("(")
        self.write("<")
        self.indent_sexp()
        self.newline()
        field835 = unwrapped_fields834[0]
        self.pretty_term(field835)
        self.newline()
        field836 = unwrapped_fields834[1]
        self.pretty_term(field836)
        self.dedent()
        self.write(")")
        return None

    def pretty_lt_eq(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_lt_eq)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1386(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1387 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1387 = None
            return _t1387
        _t1388 = _t1386(msg)
        fields837 = _t1388
        assert fields837 is not None
        unwrapped_fields838 = fields837
        self.write("(")
        self.write("<=")
        self.indent_sexp()
        self.newline()
        field839 = unwrapped_fields838[0]
        self.pretty_term(field839)
        self.newline()
        field840 = unwrapped_fields838[1]
        self.pretty_term(field840)
        self.dedent()
        self.write(")")
        return None

    def pretty_gt(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_gt)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1389(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1390 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1390 = None
            return _t1390
        _t1391 = _t1389(msg)
        fields841 = _t1391
        assert fields841 is not None
        unwrapped_fields842 = fields841
        self.write("(")
        self.write(">")
        self.indent_sexp()
        self.newline()
        field843 = unwrapped_fields842[0]
        self.pretty_term(field843)
        self.newline()
        field844 = unwrapped_fields842[1]
        self.pretty_term(field844)
        self.dedent()
        self.write(")")
        return None

    def pretty_gt_eq(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_gt_eq)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1392(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1393 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1393 = None
            return _t1393
        _t1394 = _t1392(msg)
        fields845 = _t1394
        assert fields845 is not None
        unwrapped_fields846 = fields845
        self.write("(")
        self.write(">=")
        self.indent_sexp()
        self.newline()
        field847 = unwrapped_fields846[0]
        self.pretty_term(field847)
        self.newline()
        field848 = unwrapped_fields846[1]
        self.pretty_term(field848)
        self.dedent()
        self.write(")")
        return None

    def pretty_add(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_add)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1395(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1396 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1396 = None
            return _t1396
        _t1397 = _t1395(msg)
        fields849 = _t1397
        assert fields849 is not None
        unwrapped_fields850 = fields849
        self.write("(")
        self.write("+")
        self.indent_sexp()
        self.newline()
        field851 = unwrapped_fields850[0]
        self.pretty_term(field851)
        self.newline()
        field852 = unwrapped_fields850[1]
        self.pretty_term(field852)
        self.newline()
        field853 = unwrapped_fields850[2]
        self.pretty_term(field853)
        self.dedent()
        self.write(")")
        return None

    def pretty_minus(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_minus)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1398(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1399 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1399 = None
            return _t1399
        _t1400 = _t1398(msg)
        fields854 = _t1400
        assert fields854 is not None
        unwrapped_fields855 = fields854
        self.write("(")
        self.write("-")
        self.indent_sexp()
        self.newline()
        field856 = unwrapped_fields855[0]
        self.pretty_term(field856)
        self.newline()
        field857 = unwrapped_fields855[1]
        self.pretty_term(field857)
        self.newline()
        field858 = unwrapped_fields855[2]
        self.pretty_term(field858)
        self.dedent()
        self.write(")")
        return None

    def pretty_multiply(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_multiply)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1401(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1402 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1402 = None
            return _t1402
        _t1403 = _t1401(msg)
        fields859 = _t1403
        assert fields859 is not None
        unwrapped_fields860 = fields859
        self.write("(")
        self.write("*")
        self.indent_sexp()
        self.newline()
        field861 = unwrapped_fields860[0]
        self.pretty_term(field861)
        self.newline()
        field862 = unwrapped_fields860[1]
        self.pretty_term(field862)
        self.newline()
        field863 = unwrapped_fields860[2]
        self.pretty_term(field863)
        self.dedent()
        self.write(")")
        return None

    def pretty_divide(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_divide)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1404(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1405 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1405 = None
            return _t1405
        _t1406 = _t1404(msg)
        fields864 = _t1406
        assert fields864 is not None
        unwrapped_fields865 = fields864
        self.write("(")
        self.write("/")
        self.indent_sexp()
        self.newline()
        field866 = unwrapped_fields865[0]
        self.pretty_term(field866)
        self.newline()
        field867 = unwrapped_fields865[1]
        self.pretty_term(field867)
        self.newline()
        field868 = unwrapped_fields865[2]
        self.pretty_term(field868)
        self.dedent()
        self.write(")")
        return None

    def pretty_rel_term(self, msg: logic_pb2.RelTerm) -> None:
        _flat = self._try_flat(msg, self.pretty_rel_term)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1407(_dollar_dollar):
            if _dollar_dollar.HasField("specialized_value"):
                _t1408 = _dollar_dollar.specialized_value
            else:
                _t1408 = None
            return _t1408
        _t1409 = _t1407(msg)
        deconstruct_result871 = _t1409
        if deconstruct_result871 is not None:
            assert deconstruct_result871 is not None
            unwrapped872 = deconstruct_result871
            self.pretty_specialized_value(unwrapped872)
        else:
            def _t1410(_dollar_dollar):
                if _dollar_dollar.HasField("term"):
                    _t1411 = _dollar_dollar.term
                else:
                    _t1411 = None
                return _t1411
            _t1412 = _t1410(msg)
            deconstruct_result869 = _t1412
            if deconstruct_result869 is not None:
                assert deconstruct_result869 is not None
                unwrapped870 = deconstruct_result869
                self.pretty_term(unwrapped870)
            else:
                raise ParseError("No matching rule for rel_term")
        return None

    def pretty_specialized_value(self, msg: logic_pb2.Value) -> None:
        _flat = self._try_flat(msg, self.pretty_specialized_value)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1413(_dollar_dollar):
            return _dollar_dollar
        _t1414 = _t1413(msg)
        fields873 = _t1414
        assert fields873 is not None
        unwrapped_fields874 = fields873
        self.write("#")
        self.pretty_value(unwrapped_fields874)
        return None

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom) -> None:
        _flat = self._try_flat(msg, self.pretty_rel_atom)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1415(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t1416 = _t1415(msg)
        fields875 = _t1416
        assert fields875 is not None
        unwrapped_fields876 = fields875
        self.write("(")
        self.write("relatom")
        self.indent_sexp()
        self.newline()
        field877 = unwrapped_fields876[0]
        self.pretty_name(field877)
        field878 = unwrapped_fields876[1]
        if not len(field878) == 0:
            self.newline()
            for i880, elem879 in enumerate(field878):
                if (i880 > 0):
                    self.newline()
                self.pretty_rel_term(elem879)
        self.dedent()
        self.write(")")
        return None

    def pretty_cast(self, msg: logic_pb2.Cast) -> None:
        _flat = self._try_flat(msg, self.pretty_cast)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1417(_dollar_dollar):
            return (_dollar_dollar.input, _dollar_dollar.result,)
        _t1418 = _t1417(msg)
        fields881 = _t1418
        assert fields881 is not None
        unwrapped_fields882 = fields881
        self.write("(")
        self.write("cast")
        self.indent_sexp()
        self.newline()
        field883 = unwrapped_fields882[0]
        self.pretty_term(field883)
        self.newline()
        field884 = unwrapped_fields882[1]
        self.pretty_term(field884)
        self.dedent()
        self.write(")")
        return None

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]) -> None:
        _flat = self._try_flat(msg, self.pretty_attrs)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1419(_dollar_dollar):
            return _dollar_dollar
        _t1420 = _t1419(msg)
        fields885 = _t1420
        assert fields885 is not None
        unwrapped_fields886 = fields885
        self.write("(")
        self.write("attrs")
        self.indent_sexp()
        if not len(unwrapped_fields886) == 0:
            self.newline()
            for i888, elem887 in enumerate(unwrapped_fields886):
                if (i888 > 0):
                    self.newline()
                self.pretty_attribute(elem887)
        self.dedent()
        self.write(")")
        return None

    def pretty_attribute(self, msg: logic_pb2.Attribute) -> None:
        _flat = self._try_flat(msg, self.pretty_attribute)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1421(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args,)
        _t1422 = _t1421(msg)
        fields889 = _t1422
        assert fields889 is not None
        unwrapped_fields890 = fields889
        self.write("(")
        self.write("attribute")
        self.indent_sexp()
        self.newline()
        field891 = unwrapped_fields890[0]
        self.pretty_name(field891)
        field892 = unwrapped_fields890[1]
        if not len(field892) == 0:
            self.newline()
            for i894, elem893 in enumerate(field892):
                if (i894 > 0):
                    self.newline()
                self.pretty_value(elem893)
        self.dedent()
        self.write(")")
        return None

    def pretty_algorithm(self, msg: logic_pb2.Algorithm) -> None:
        _flat = self._try_flat(msg, self.pretty_algorithm)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1423(_dollar_dollar):
            return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
        _t1424 = _t1423(msg)
        fields895 = _t1424
        assert fields895 is not None
        unwrapped_fields896 = fields895
        self.write("(")
        self.write("algorithm")
        self.indent_sexp()
        field897 = unwrapped_fields896[0]
        if not len(field897) == 0:
            self.newline()
            for i899, elem898 in enumerate(field897):
                if (i899 > 0):
                    self.newline()
                self.pretty_relation_id(elem898)
        self.newline()
        field900 = unwrapped_fields896[1]
        self.pretty_script(field900)
        self.dedent()
        self.write(")")
        return None

    def pretty_script(self, msg: logic_pb2.Script) -> None:
        _flat = self._try_flat(msg, self.pretty_script)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1425(_dollar_dollar):
            return _dollar_dollar.constructs
        _t1426 = _t1425(msg)
        fields901 = _t1426
        assert fields901 is not None
        unwrapped_fields902 = fields901
        self.write("(")
        self.write("script")
        self.indent_sexp()
        if not len(unwrapped_fields902) == 0:
            self.newline()
            for i904, elem903 in enumerate(unwrapped_fields902):
                if (i904 > 0):
                    self.newline()
                self.pretty_construct(elem903)
        self.dedent()
        self.write(")")
        return None

    def pretty_construct(self, msg: logic_pb2.Construct) -> None:
        _flat = self._try_flat(msg, self.pretty_construct)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1427(_dollar_dollar):
            if _dollar_dollar.HasField("loop"):
                _t1428 = _dollar_dollar.loop
            else:
                _t1428 = None
            return _t1428
        _t1429 = _t1427(msg)
        deconstruct_result907 = _t1429
        if deconstruct_result907 is not None:
            assert deconstruct_result907 is not None
            unwrapped908 = deconstruct_result907
            self.pretty_loop(unwrapped908)
        else:
            def _t1430(_dollar_dollar):
                if _dollar_dollar.HasField("instruction"):
                    _t1431 = _dollar_dollar.instruction
                else:
                    _t1431 = None
                return _t1431
            _t1432 = _t1430(msg)
            deconstruct_result905 = _t1432
            if deconstruct_result905 is not None:
                assert deconstruct_result905 is not None
                unwrapped906 = deconstruct_result905
                self.pretty_instruction(unwrapped906)
            else:
                raise ParseError("No matching rule for construct")
        return None

    def pretty_loop(self, msg: logic_pb2.Loop) -> None:
        _flat = self._try_flat(msg, self.pretty_loop)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1433(_dollar_dollar):
            return (_dollar_dollar.init, _dollar_dollar.body,)
        _t1434 = _t1433(msg)
        fields909 = _t1434
        assert fields909 is not None
        unwrapped_fields910 = fields909
        self.write("(")
        self.write("loop")
        self.indent_sexp()
        self.newline()
        field911 = unwrapped_fields910[0]
        self.pretty_init(field911)
        self.newline()
        field912 = unwrapped_fields910[1]
        self.pretty_script(field912)
        self.dedent()
        self.write(")")
        return None

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]) -> None:
        _flat = self._try_flat(msg, self.pretty_init)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1435(_dollar_dollar):
            return _dollar_dollar
        _t1436 = _t1435(msg)
        fields913 = _t1436
        assert fields913 is not None
        unwrapped_fields914 = fields913
        self.write("(")
        self.write("init")
        self.indent_sexp()
        if not len(unwrapped_fields914) == 0:
            self.newline()
            for i916, elem915 in enumerate(unwrapped_fields914):
                if (i916 > 0):
                    self.newline()
                self.pretty_instruction(elem915)
        self.dedent()
        self.write(")")
        return None

    def pretty_instruction(self, msg: logic_pb2.Instruction) -> None:
        _flat = self._try_flat(msg, self.pretty_instruction)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1437(_dollar_dollar):
            if _dollar_dollar.HasField("assign"):
                _t1438 = _dollar_dollar.assign
            else:
                _t1438 = None
            return _t1438
        _t1439 = _t1437(msg)
        deconstruct_result925 = _t1439
        if deconstruct_result925 is not None:
            assert deconstruct_result925 is not None
            unwrapped926 = deconstruct_result925
            self.pretty_assign(unwrapped926)
        else:
            def _t1440(_dollar_dollar):
                if _dollar_dollar.HasField("upsert"):
                    _t1441 = _dollar_dollar.upsert
                else:
                    _t1441 = None
                return _t1441
            _t1442 = _t1440(msg)
            deconstruct_result923 = _t1442
            if deconstruct_result923 is not None:
                assert deconstruct_result923 is not None
                unwrapped924 = deconstruct_result923
                self.pretty_upsert(unwrapped924)
            else:
                def _t1443(_dollar_dollar):
                    if _dollar_dollar.HasField("break"):
                        _t1444 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1444 = None
                    return _t1444
                _t1445 = _t1443(msg)
                deconstruct_result921 = _t1445
                if deconstruct_result921 is not None:
                    assert deconstruct_result921 is not None
                    unwrapped922 = deconstruct_result921
                    self.pretty_break(unwrapped922)
                else:
                    def _t1446(_dollar_dollar):
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1447 = _dollar_dollar.monoid_def
                        else:
                            _t1447 = None
                        return _t1447
                    _t1448 = _t1446(msg)
                    deconstruct_result919 = _t1448
                    if deconstruct_result919 is not None:
                        assert deconstruct_result919 is not None
                        unwrapped920 = deconstruct_result919
                        self.pretty_monoid_def(unwrapped920)
                    else:
                        def _t1449(_dollar_dollar):
                            if _dollar_dollar.HasField("monus_def"):
                                _t1450 = _dollar_dollar.monus_def
                            else:
                                _t1450 = None
                            return _t1450
                        _t1451 = _t1449(msg)
                        deconstruct_result917 = _t1451
                        if deconstruct_result917 is not None:
                            assert deconstruct_result917 is not None
                            unwrapped918 = deconstruct_result917
                            self.pretty_monus_def(unwrapped918)
                        else:
                            raise ParseError("No matching rule for instruction")
        return None

    def pretty_assign(self, msg: logic_pb2.Assign) -> None:
        _flat = self._try_flat(msg, self.pretty_assign)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1452(_dollar_dollar):
            if not len(_dollar_dollar.attrs) == 0:
                _t1453 = _dollar_dollar.attrs
            else:
                _t1453 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1453,)
        _t1454 = _t1452(msg)
        fields927 = _t1454
        assert fields927 is not None
        unwrapped_fields928 = fields927
        self.write("(")
        self.write("assign")
        self.indent_sexp()
        self.newline()
        field929 = unwrapped_fields928[0]
        self.pretty_relation_id(field929)
        self.newline()
        field930 = unwrapped_fields928[1]
        self.pretty_abstraction(field930)
        field931 = unwrapped_fields928[2]
        if field931 is not None:
            self.newline()
            assert field931 is not None
            opt_val932 = field931
            self.pretty_attrs(opt_val932)
        self.dedent()
        self.write(")")
        return None

    def pretty_upsert(self, msg: logic_pb2.Upsert) -> None:
        _flat = self._try_flat(msg, self.pretty_upsert)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1455(_dollar_dollar):
            if not len(_dollar_dollar.attrs) == 0:
                _t1456 = _dollar_dollar.attrs
            else:
                _t1456 = None
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1456,)
        _t1457 = _t1455(msg)
        fields933 = _t1457
        assert fields933 is not None
        unwrapped_fields934 = fields933
        self.write("(")
        self.write("upsert")
        self.indent_sexp()
        self.newline()
        field935 = unwrapped_fields934[0]
        self.pretty_relation_id(field935)
        self.newline()
        field936 = unwrapped_fields934[1]
        self.pretty_abstraction_with_arity(field936)
        field937 = unwrapped_fields934[2]
        if field937 is not None:
            self.newline()
            assert field937 is not None
            opt_val938 = field937
            self.pretty_attrs(opt_val938)
        self.dedent()
        self.write(")")
        return None

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]) -> None:
        _flat = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1458(_dollar_dollar):
            _t1459 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            return (_t1459, _dollar_dollar[0].value,)
        _t1460 = _t1458(msg)
        fields939 = _t1460
        assert fields939 is not None
        unwrapped_fields940 = fields939
        self.write("(")
        self.indent()
        field941 = unwrapped_fields940[0]
        self.pretty_bindings(field941)
        self.newline()
        field942 = unwrapped_fields940[1]
        self.pretty_formula(field942)
        self.dedent()
        self.write(")")
        return None

    def pretty_break(self, msg: logic_pb2.Break) -> None:
        _flat = self._try_flat(msg, self.pretty_break)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1461(_dollar_dollar):
            if not len(_dollar_dollar.attrs) == 0:
                _t1462 = _dollar_dollar.attrs
            else:
                _t1462 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1462,)
        _t1463 = _t1461(msg)
        fields943 = _t1463
        assert fields943 is not None
        unwrapped_fields944 = fields943
        self.write("(")
        self.write("break")
        self.indent_sexp()
        self.newline()
        field945 = unwrapped_fields944[0]
        self.pretty_relation_id(field945)
        self.newline()
        field946 = unwrapped_fields944[1]
        self.pretty_abstraction(field946)
        field947 = unwrapped_fields944[2]
        if field947 is not None:
            self.newline()
            assert field947 is not None
            opt_val948 = field947
            self.pretty_attrs(opt_val948)
        self.dedent()
        self.write(")")
        return None

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef) -> None:
        _flat = self._try_flat(msg, self.pretty_monoid_def)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1464(_dollar_dollar):
            if not len(_dollar_dollar.attrs) == 0:
                _t1465 = _dollar_dollar.attrs
            else:
                _t1465 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1465,)
        _t1466 = _t1464(msg)
        fields949 = _t1466
        assert fields949 is not None
        unwrapped_fields950 = fields949
        self.write("(")
        self.write("monoid")
        self.indent_sexp()
        self.newline()
        field951 = unwrapped_fields950[0]
        self.pretty_monoid(field951)
        self.newline()
        field952 = unwrapped_fields950[1]
        self.pretty_relation_id(field952)
        self.newline()
        field953 = unwrapped_fields950[2]
        self.pretty_abstraction_with_arity(field953)
        field954 = unwrapped_fields950[3]
        if field954 is not None:
            self.newline()
            assert field954 is not None
            opt_val955 = field954
            self.pretty_attrs(opt_val955)
        self.dedent()
        self.write(")")
        return None

    def pretty_monoid(self, msg: logic_pb2.Monoid) -> None:
        _flat = self._try_flat(msg, self.pretty_monoid)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1467(_dollar_dollar):
            if _dollar_dollar.HasField("or_monoid"):
                _t1468 = _dollar_dollar.or_monoid
            else:
                _t1468 = None
            return _t1468
        _t1469 = _t1467(msg)
        deconstruct_result962 = _t1469
        if deconstruct_result962 is not None:
            assert deconstruct_result962 is not None
            unwrapped963 = deconstruct_result962
            self.pretty_or_monoid(unwrapped963)
        else:
            def _t1470(_dollar_dollar):
                if _dollar_dollar.HasField("min_monoid"):
                    _t1471 = _dollar_dollar.min_monoid
                else:
                    _t1471 = None
                return _t1471
            _t1472 = _t1470(msg)
            deconstruct_result960 = _t1472
            if deconstruct_result960 is not None:
                assert deconstruct_result960 is not None
                unwrapped961 = deconstruct_result960
                self.pretty_min_monoid(unwrapped961)
            else:
                def _t1473(_dollar_dollar):
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1474 = _dollar_dollar.max_monoid
                    else:
                        _t1474 = None
                    return _t1474
                _t1475 = _t1473(msg)
                deconstruct_result958 = _t1475
                if deconstruct_result958 is not None:
                    assert deconstruct_result958 is not None
                    unwrapped959 = deconstruct_result958
                    self.pretty_max_monoid(unwrapped959)
                else:
                    def _t1476(_dollar_dollar):
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1477 = _dollar_dollar.sum_monoid
                        else:
                            _t1477 = None
                        return _t1477
                    _t1478 = _t1476(msg)
                    deconstruct_result956 = _t1478
                    if deconstruct_result956 is not None:
                        assert deconstruct_result956 is not None
                        unwrapped957 = deconstruct_result956
                        self.pretty_sum_monoid(unwrapped957)
                    else:
                        raise ParseError("No matching rule for monoid")
        return None

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid) -> None:
        _flat = self._try_flat(msg, self.pretty_or_monoid)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1479(_dollar_dollar):
            return _dollar_dollar
        _t1480 = _t1479(msg)
        fields964 = _t1480
        assert fields964 is not None
        unwrapped_fields965 = fields964
        self.write("(")
        self.write("or")
        self.write(")")
        return None

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid) -> None:
        _flat = self._try_flat(msg, self.pretty_min_monoid)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1481(_dollar_dollar):
            return _dollar_dollar.type
        _t1482 = _t1481(msg)
        fields966 = _t1482
        assert fields966 is not None
        unwrapped_fields967 = fields966
        self.write("(")
        self.write("min")
        self.indent_sexp()
        self.newline()
        self.pretty_type(unwrapped_fields967)
        self.dedent()
        self.write(")")
        return None

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid) -> None:
        _flat = self._try_flat(msg, self.pretty_max_monoid)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1483(_dollar_dollar):
            return _dollar_dollar.type
        _t1484 = _t1483(msg)
        fields968 = _t1484
        assert fields968 is not None
        unwrapped_fields969 = fields968
        self.write("(")
        self.write("max")
        self.indent_sexp()
        self.newline()
        self.pretty_type(unwrapped_fields969)
        self.dedent()
        self.write(")")
        return None

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid) -> None:
        _flat = self._try_flat(msg, self.pretty_sum_monoid)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1485(_dollar_dollar):
            return _dollar_dollar.type
        _t1486 = _t1485(msg)
        fields970 = _t1486
        assert fields970 is not None
        unwrapped_fields971 = fields970
        self.write("(")
        self.write("sum")
        self.indent_sexp()
        self.newline()
        self.pretty_type(unwrapped_fields971)
        self.dedent()
        self.write(")")
        return None

    def pretty_monus_def(self, msg: logic_pb2.MonusDef) -> None:
        _flat = self._try_flat(msg, self.pretty_monus_def)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1487(_dollar_dollar):
            if not len(_dollar_dollar.attrs) == 0:
                _t1488 = _dollar_dollar.attrs
            else:
                _t1488 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1488,)
        _t1489 = _t1487(msg)
        fields972 = _t1489
        assert fields972 is not None
        unwrapped_fields973 = fields972
        self.write("(")
        self.write("monus")
        self.indent_sexp()
        self.newline()
        field974 = unwrapped_fields973[0]
        self.pretty_monoid(field974)
        self.newline()
        field975 = unwrapped_fields973[1]
        self.pretty_relation_id(field975)
        self.newline()
        field976 = unwrapped_fields973[2]
        self.pretty_abstraction_with_arity(field976)
        field977 = unwrapped_fields973[3]
        if field977 is not None:
            self.newline()
            assert field977 is not None
            opt_val978 = field977
            self.pretty_attrs(opt_val978)
        self.dedent()
        self.write(")")
        return None

    def pretty_constraint(self, msg: logic_pb2.Constraint) -> None:
        _flat = self._try_flat(msg, self.pretty_constraint)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1490(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
        _t1491 = _t1490(msg)
        fields979 = _t1491
        assert fields979 is not None
        unwrapped_fields980 = fields979
        self.write("(")
        self.write("functional_dependency")
        self.indent_sexp()
        self.newline()
        field981 = unwrapped_fields980[0]
        self.pretty_relation_id(field981)
        self.newline()
        field982 = unwrapped_fields980[1]
        self.pretty_abstraction(field982)
        self.newline()
        field983 = unwrapped_fields980[2]
        self.pretty_functional_dependency_keys(field983)
        self.newline()
        field984 = unwrapped_fields980[3]
        self.pretty_functional_dependency_values(field984)
        self.dedent()
        self.write(")")
        return None

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]) -> None:
        _flat = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1492(_dollar_dollar):
            return _dollar_dollar
        _t1493 = _t1492(msg)
        fields985 = _t1493
        assert fields985 is not None
        unwrapped_fields986 = fields985
        self.write("(")
        self.write("keys")
        self.indent_sexp()
        if not len(unwrapped_fields986) == 0:
            self.newline()
            for i988, elem987 in enumerate(unwrapped_fields986):
                if (i988 > 0):
                    self.newline()
                self.pretty_var(elem987)
        self.dedent()
        self.write(")")
        return None

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]) -> None:
        _flat = self._try_flat(msg, self.pretty_functional_dependency_values)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1494(_dollar_dollar):
            return _dollar_dollar
        _t1495 = _t1494(msg)
        fields989 = _t1495
        assert fields989 is not None
        unwrapped_fields990 = fields989
        self.write("(")
        self.write("values")
        self.indent_sexp()
        if not len(unwrapped_fields990) == 0:
            self.newline()
            for i992, elem991 in enumerate(unwrapped_fields990):
                if (i992 > 0):
                    self.newline()
                self.pretty_var(elem991)
        self.dedent()
        self.write(")")
        return None

    def pretty_data(self, msg: logic_pb2.Data) -> None:
        _flat = self._try_flat(msg, self.pretty_data)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1496(_dollar_dollar):
            if _dollar_dollar.HasField("rel_edb"):
                _t1497 = _dollar_dollar.rel_edb
            else:
                _t1497 = None
            return _t1497
        _t1498 = _t1496(msg)
        deconstruct_result997 = _t1498
        if deconstruct_result997 is not None:
            assert deconstruct_result997 is not None
            unwrapped998 = deconstruct_result997
            self.pretty_rel_edb(unwrapped998)
        else:
            def _t1499(_dollar_dollar):
                if _dollar_dollar.HasField("betree_relation"):
                    _t1500 = _dollar_dollar.betree_relation
                else:
                    _t1500 = None
                return _t1500
            _t1501 = _t1499(msg)
            deconstruct_result995 = _t1501
            if deconstruct_result995 is not None:
                assert deconstruct_result995 is not None
                unwrapped996 = deconstruct_result995
                self.pretty_betree_relation(unwrapped996)
            else:
                def _t1502(_dollar_dollar):
                    if _dollar_dollar.HasField("csv_data"):
                        _t1503 = _dollar_dollar.csv_data
                    else:
                        _t1503 = None
                    return _t1503
                _t1504 = _t1502(msg)
                deconstruct_result993 = _t1504
                if deconstruct_result993 is not None:
                    assert deconstruct_result993 is not None
                    unwrapped994 = deconstruct_result993
                    self.pretty_csv_data(unwrapped994)
                else:
                    raise ParseError("No matching rule for data")
        return None

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB) -> None:
        _flat = self._try_flat(msg, self.pretty_rel_edb)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1505(_dollar_dollar):
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        _t1506 = _t1505(msg)
        fields999 = _t1506
        assert fields999 is not None
        unwrapped_fields1000 = fields999
        self.write("(")
        self.write("rel_edb")
        self.indent_sexp()
        self.newline()
        field1001 = unwrapped_fields1000[0]
        self.pretty_relation_id(field1001)
        self.newline()
        field1002 = unwrapped_fields1000[1]
        self.pretty_rel_edb_path(field1002)
        self.newline()
        field1003 = unwrapped_fields1000[2]
        self.pretty_rel_edb_types(field1003)
        self.dedent()
        self.write(")")
        return None

    def pretty_rel_edb_path(self, msg: Sequence[str]) -> None:
        _flat = self._try_flat(msg, self.pretty_rel_edb_path)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1507(_dollar_dollar):
            return _dollar_dollar
        _t1508 = _t1507(msg)
        fields1004 = _t1508
        assert fields1004 is not None
        unwrapped_fields1005 = fields1004
        self.write("[")
        self.indent()
        for i1007, elem1006 in enumerate(unwrapped_fields1005):
            if (i1007 > 0):
                self.newline()
            self.write(self.format_string_value(elem1006))
        self.dedent()
        self.write("]")
        return None

    def pretty_rel_edb_types(self, msg: Sequence[logic_pb2.Type]) -> None:
        _flat = self._try_flat(msg, self.pretty_rel_edb_types)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1509(_dollar_dollar):
            return _dollar_dollar
        _t1510 = _t1509(msg)
        fields1008 = _t1510
        assert fields1008 is not None
        unwrapped_fields1009 = fields1008
        self.write("[")
        self.indent()
        for i1011, elem1010 in enumerate(unwrapped_fields1009):
            if (i1011 > 0):
                self.newline()
            self.pretty_type(elem1010)
        self.dedent()
        self.write("]")
        return None

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation) -> None:
        _flat = self._try_flat(msg, self.pretty_betree_relation)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1511(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        _t1512 = _t1511(msg)
        fields1012 = _t1512
        assert fields1012 is not None
        unwrapped_fields1013 = fields1012
        self.write("(")
        self.write("betree_relation")
        self.indent_sexp()
        self.newline()
        field1014 = unwrapped_fields1013[0]
        self.pretty_relation_id(field1014)
        self.newline()
        field1015 = unwrapped_fields1013[1]
        self.pretty_betree_info(field1015)
        self.dedent()
        self.write(")")
        return None

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo) -> None:
        _flat = self._try_flat(msg, self.pretty_betree_info)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1513(_dollar_dollar):
            _t1514 = self.deconstruct_betree_info_config(_dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1514,)
        _t1515 = _t1513(msg)
        fields1016 = _t1515
        assert fields1016 is not None
        unwrapped_fields1017 = fields1016
        self.write("(")
        self.write("betree_info")
        self.indent_sexp()
        self.newline()
        field1018 = unwrapped_fields1017[0]
        self.pretty_betree_info_key_types(field1018)
        self.newline()
        field1019 = unwrapped_fields1017[1]
        self.pretty_betree_info_value_types(field1019)
        self.newline()
        field1020 = unwrapped_fields1017[2]
        self.pretty_config_dict(field1020)
        self.dedent()
        self.write(")")
        return None

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]) -> None:
        _flat = self._try_flat(msg, self.pretty_betree_info_key_types)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1516(_dollar_dollar):
            return _dollar_dollar
        _t1517 = _t1516(msg)
        fields1021 = _t1517
        assert fields1021 is not None
        unwrapped_fields1022 = fields1021
        self.write("(")
        self.write("key_types")
        self.indent_sexp()
        if not len(unwrapped_fields1022) == 0:
            self.newline()
            for i1024, elem1023 in enumerate(unwrapped_fields1022):
                if (i1024 > 0):
                    self.newline()
                self.pretty_type(elem1023)
        self.dedent()
        self.write(")")
        return None

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]) -> None:
        _flat = self._try_flat(msg, self.pretty_betree_info_value_types)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1518(_dollar_dollar):
            return _dollar_dollar
        _t1519 = _t1518(msg)
        fields1025 = _t1519
        assert fields1025 is not None
        unwrapped_fields1026 = fields1025
        self.write("(")
        self.write("value_types")
        self.indent_sexp()
        if not len(unwrapped_fields1026) == 0:
            self.newline()
            for i1028, elem1027 in enumerate(unwrapped_fields1026):
                if (i1028 > 0):
                    self.newline()
                self.pretty_type(elem1027)
        self.dedent()
        self.write(")")
        return None

    def pretty_csv_data(self, msg: logic_pb2.CSVData) -> None:
        _flat = self._try_flat(msg, self.pretty_csv_data)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1520(_dollar_dollar):
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        _t1521 = _t1520(msg)
        fields1029 = _t1521
        assert fields1029 is not None
        unwrapped_fields1030 = fields1029
        self.write("(")
        self.write("csv_data")
        self.indent_sexp()
        self.newline()
        field1031 = unwrapped_fields1030[0]
        self.pretty_csvlocator(field1031)
        self.newline()
        field1032 = unwrapped_fields1030[1]
        self.pretty_csv_config(field1032)
        self.newline()
        field1033 = unwrapped_fields1030[2]
        self.pretty_csv_columns(field1033)
        self.newline()
        field1034 = unwrapped_fields1030[3]
        self.pretty_csv_asof(field1034)
        self.dedent()
        self.write(")")
        return None

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator) -> None:
        _flat = self._try_flat(msg, self.pretty_csvlocator)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1522(_dollar_dollar):
            if not len(_dollar_dollar.paths) == 0:
                _t1523 = _dollar_dollar.paths
            else:
                _t1523 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1524 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1524 = None
            return (_t1523, _t1524,)
        _t1525 = _t1522(msg)
        fields1035 = _t1525
        assert fields1035 is not None
        unwrapped_fields1036 = fields1035
        self.write("(")
        self.write("csv_locator")
        self.indent_sexp()
        field1037 = unwrapped_fields1036[0]
        if field1037 is not None:
            self.newline()
            assert field1037 is not None
            opt_val1038 = field1037
            self.pretty_csv_locator_paths(opt_val1038)
        field1039 = unwrapped_fields1036[1]
        if field1039 is not None:
            self.newline()
            assert field1039 is not None
            opt_val1040 = field1039
            self.pretty_csv_locator_inline_data(opt_val1040)
        self.dedent()
        self.write(")")
        return None

    def pretty_csv_locator_paths(self, msg: Sequence[str]) -> None:
        _flat = self._try_flat(msg, self.pretty_csv_locator_paths)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1526(_dollar_dollar):
            return _dollar_dollar
        _t1527 = _t1526(msg)
        fields1041 = _t1527
        assert fields1041 is not None
        unwrapped_fields1042 = fields1041
        self.write("(")
        self.write("paths")
        self.indent_sexp()
        if not len(unwrapped_fields1042) == 0:
            self.newline()
            for i1044, elem1043 in enumerate(unwrapped_fields1042):
                if (i1044 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1043))
        self.dedent()
        self.write(")")
        return None

    def pretty_csv_locator_inline_data(self, msg: str) -> None:
        _flat = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1528(_dollar_dollar):
            return _dollar_dollar
        _t1529 = _t1528(msg)
        fields1045 = _t1529
        assert fields1045 is not None
        unwrapped_fields1046 = fields1045
        self.write("(")
        self.write("inline_data")
        self.indent_sexp()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields1046))
        self.dedent()
        self.write(")")
        return None

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig) -> None:
        _flat = self._try_flat(msg, self.pretty_csv_config)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1530(_dollar_dollar):
            _t1531 = self.deconstruct_csv_config(_dollar_dollar)
            return _t1531
        _t1532 = _t1530(msg)
        fields1047 = _t1532
        assert fields1047 is not None
        unwrapped_fields1048 = fields1047
        self.write("(")
        self.write("csv_config")
        self.indent_sexp()
        self.newline()
        self.pretty_config_dict(unwrapped_fields1048)
        self.dedent()
        self.write(")")
        return None

    def pretty_csv_columns(self, msg: Sequence[logic_pb2.CSVColumn]) -> None:
        _flat = self._try_flat(msg, self.pretty_csv_columns)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1533(_dollar_dollar):
            return _dollar_dollar
        _t1534 = _t1533(msg)
        fields1049 = _t1534
        assert fields1049 is not None
        unwrapped_fields1050 = fields1049
        self.write("(")
        self.write("columns")
        self.indent_sexp()
        if not len(unwrapped_fields1050) == 0:
            self.newline()
            for i1052, elem1051 in enumerate(unwrapped_fields1050):
                if (i1052 > 0):
                    self.newline()
                self.pretty_csv_column(elem1051)
        self.dedent()
        self.write(")")
        return None

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn) -> None:
        _flat = self._try_flat(msg, self.pretty_csv_column)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1535(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        _t1536 = _t1535(msg)
        fields1053 = _t1536
        assert fields1053 is not None
        unwrapped_fields1054 = fields1053
        self.write("(")
        self.write("column")
        self.indent_sexp()
        self.newline()
        field1055 = unwrapped_fields1054[0]
        self.write(self.format_string_value(field1055))
        self.newline()
        field1056 = unwrapped_fields1054[1]
        self.pretty_relation_id(field1056)
        self.newline()
        self.write("[")
        field1057 = unwrapped_fields1054[2]
        for i1059, elem1058 in enumerate(field1057):
            if (i1059 > 0):
                self.newline()
            self.pretty_type(elem1058)
        self.write("]")
        self.dedent()
        self.write(")")
        return None

    def pretty_csv_asof(self, msg: str) -> None:
        _flat = self._try_flat(msg, self.pretty_csv_asof)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1537(_dollar_dollar):
            return _dollar_dollar
        _t1538 = _t1537(msg)
        fields1060 = _t1538
        assert fields1060 is not None
        unwrapped_fields1061 = fields1060
        self.write("(")
        self.write("asof")
        self.indent_sexp()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields1061))
        self.dedent()
        self.write(")")
        return None

    def pretty_undefine(self, msg: transactions_pb2.Undefine) -> None:
        _flat = self._try_flat(msg, self.pretty_undefine)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1539(_dollar_dollar):
            return _dollar_dollar.fragment_id
        _t1540 = _t1539(msg)
        fields1062 = _t1540
        assert fields1062 is not None
        unwrapped_fields1063 = fields1062
        self.write("(")
        self.write("undefine")
        self.indent_sexp()
        self.newline()
        self.pretty_fragment_id(unwrapped_fields1063)
        self.dedent()
        self.write(")")
        return None

    def pretty_context(self, msg: transactions_pb2.Context) -> None:
        _flat = self._try_flat(msg, self.pretty_context)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1541(_dollar_dollar):
            return _dollar_dollar.relations
        _t1542 = _t1541(msg)
        fields1064 = _t1542
        assert fields1064 is not None
        unwrapped_fields1065 = fields1064
        self.write("(")
        self.write("context")
        self.indent_sexp()
        if not len(unwrapped_fields1065) == 0:
            self.newline()
            for i1067, elem1066 in enumerate(unwrapped_fields1065):
                if (i1067 > 0):
                    self.newline()
                self.pretty_relation_id(elem1066)
        self.dedent()
        self.write(")")
        return None

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]) -> None:
        _flat = self._try_flat(msg, self.pretty_epoch_reads)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1543(_dollar_dollar):
            return _dollar_dollar
        _t1544 = _t1543(msg)
        fields1068 = _t1544
        assert fields1068 is not None
        unwrapped_fields1069 = fields1068
        self.write("(")
        self.write("reads")
        self.indent_sexp()
        if not len(unwrapped_fields1069) == 0:
            self.newline()
            for i1071, elem1070 in enumerate(unwrapped_fields1069):
                if (i1071 > 0):
                    self.newline()
                self.pretty_read(elem1070)
        self.dedent()
        self.write(")")
        return None

    def pretty_read(self, msg: transactions_pb2.Read) -> None:
        _flat = self._try_flat(msg, self.pretty_read)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1545(_dollar_dollar):
            if _dollar_dollar.HasField("demand"):
                _t1546 = _dollar_dollar.demand
            else:
                _t1546 = None
            return _t1546
        _t1547 = _t1545(msg)
        deconstruct_result1080 = _t1547
        if deconstruct_result1080 is not None:
            assert deconstruct_result1080 is not None
            unwrapped1081 = deconstruct_result1080
            self.pretty_demand(unwrapped1081)
        else:
            def _t1548(_dollar_dollar):
                if _dollar_dollar.HasField("output"):
                    _t1549 = _dollar_dollar.output
                else:
                    _t1549 = None
                return _t1549
            _t1550 = _t1548(msg)
            deconstruct_result1078 = _t1550
            if deconstruct_result1078 is not None:
                assert deconstruct_result1078 is not None
                unwrapped1079 = deconstruct_result1078
                self.pretty_output(unwrapped1079)
            else:
                def _t1551(_dollar_dollar):
                    if _dollar_dollar.HasField("what_if"):
                        _t1552 = _dollar_dollar.what_if
                    else:
                        _t1552 = None
                    return _t1552
                _t1553 = _t1551(msg)
                deconstruct_result1076 = _t1553
                if deconstruct_result1076 is not None:
                    assert deconstruct_result1076 is not None
                    unwrapped1077 = deconstruct_result1076
                    self.pretty_what_if(unwrapped1077)
                else:
                    def _t1554(_dollar_dollar):
                        if _dollar_dollar.HasField("abort"):
                            _t1555 = _dollar_dollar.abort
                        else:
                            _t1555 = None
                        return _t1555
                    _t1556 = _t1554(msg)
                    deconstruct_result1074 = _t1556
                    if deconstruct_result1074 is not None:
                        assert deconstruct_result1074 is not None
                        unwrapped1075 = deconstruct_result1074
                        self.pretty_abort(unwrapped1075)
                    else:
                        def _t1557(_dollar_dollar):
                            if _dollar_dollar.HasField("export"):
                                _t1558 = _dollar_dollar.export
                            else:
                                _t1558 = None
                            return _t1558
                        _t1559 = _t1557(msg)
                        deconstruct_result1072 = _t1559
                        if deconstruct_result1072 is not None:
                            assert deconstruct_result1072 is not None
                            unwrapped1073 = deconstruct_result1072
                            self.pretty_export(unwrapped1073)
                        else:
                            raise ParseError("No matching rule for read")
        return None

    def pretty_demand(self, msg: transactions_pb2.Demand) -> None:
        _flat = self._try_flat(msg, self.pretty_demand)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1560(_dollar_dollar):
            return _dollar_dollar.relation_id
        _t1561 = _t1560(msg)
        fields1082 = _t1561
        assert fields1082 is not None
        unwrapped_fields1083 = fields1082
        self.write("(")
        self.write("demand")
        self.indent_sexp()
        self.newline()
        self.pretty_relation_id(unwrapped_fields1083)
        self.dedent()
        self.write(")")
        return None

    def pretty_output(self, msg: transactions_pb2.Output) -> None:
        _flat = self._try_flat(msg, self.pretty_output)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1562(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        _t1563 = _t1562(msg)
        fields1084 = _t1563
        assert fields1084 is not None
        unwrapped_fields1085 = fields1084
        self.write("(")
        self.write("output")
        self.indent_sexp()
        self.newline()
        field1086 = unwrapped_fields1085[0]
        self.pretty_name(field1086)
        self.newline()
        field1087 = unwrapped_fields1085[1]
        self.pretty_relation_id(field1087)
        self.dedent()
        self.write(")")
        return None

    def pretty_what_if(self, msg: transactions_pb2.WhatIf) -> None:
        _flat = self._try_flat(msg, self.pretty_what_if)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1564(_dollar_dollar):
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        _t1565 = _t1564(msg)
        fields1088 = _t1565
        assert fields1088 is not None
        unwrapped_fields1089 = fields1088
        self.write("(")
        self.write("what_if")
        self.indent_sexp()
        self.newline()
        field1090 = unwrapped_fields1089[0]
        self.pretty_name(field1090)
        self.newline()
        field1091 = unwrapped_fields1089[1]
        self.pretty_epoch(field1091)
        self.dedent()
        self.write(")")
        return None

    def pretty_abort(self, msg: transactions_pb2.Abort) -> None:
        _flat = self._try_flat(msg, self.pretty_abort)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1566(_dollar_dollar):
            if _dollar_dollar.name != "abort":
                _t1567 = _dollar_dollar.name
            else:
                _t1567 = None
            return (_t1567, _dollar_dollar.relation_id,)
        _t1568 = _t1566(msg)
        fields1092 = _t1568
        assert fields1092 is not None
        unwrapped_fields1093 = fields1092
        self.write("(")
        self.write("abort")
        self.indent_sexp()
        field1094 = unwrapped_fields1093[0]
        if field1094 is not None:
            self.newline()
            assert field1094 is not None
            opt_val1095 = field1094
            self.pretty_name(opt_val1095)
        self.newline()
        field1096 = unwrapped_fields1093[1]
        self.pretty_relation_id(field1096)
        self.dedent()
        self.write(")")
        return None

    def pretty_export(self, msg: transactions_pb2.Export) -> None:
        _flat = self._try_flat(msg, self.pretty_export)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1569(_dollar_dollar):
            return _dollar_dollar.csv_config
        _t1570 = _t1569(msg)
        fields1097 = _t1570
        assert fields1097 is not None
        unwrapped_fields1098 = fields1097
        self.write("(")
        self.write("export")
        self.indent_sexp()
        self.newline()
        self.pretty_export_csv_config(unwrapped_fields1098)
        self.dedent()
        self.write(")")
        return None

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> None:
        _flat = self._try_flat(msg, self.pretty_export_csv_config)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1571(_dollar_dollar):
            _t1572 = self.deconstruct_export_csv_config(_dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1572,)
        _t1573 = _t1571(msg)
        fields1099 = _t1573
        assert fields1099 is not None
        unwrapped_fields1100 = fields1099
        self.write("(")
        self.write("export_csv_config")
        self.indent_sexp()
        self.newline()
        field1101 = unwrapped_fields1100[0]
        self.pretty_export_csv_path(field1101)
        self.newline()
        field1102 = unwrapped_fields1100[1]
        self.pretty_export_csv_columns(field1102)
        self.newline()
        field1103 = unwrapped_fields1100[2]
        self.pretty_config_dict(field1103)
        self.dedent()
        self.write(")")
        return None

    def pretty_export_csv_path(self, msg: str) -> None:
        _flat = self._try_flat(msg, self.pretty_export_csv_path)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1574(_dollar_dollar):
            return _dollar_dollar
        _t1575 = _t1574(msg)
        fields1104 = _t1575
        assert fields1104 is not None
        unwrapped_fields1105 = fields1104
        self.write("(")
        self.write("path")
        self.indent_sexp()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields1105))
        self.dedent()
        self.write(")")
        return None

    def pretty_export_csv_columns(self, msg: Sequence[transactions_pb2.ExportCSVColumn]) -> None:
        _flat = self._try_flat(msg, self.pretty_export_csv_columns)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1576(_dollar_dollar):
            return _dollar_dollar
        _t1577 = _t1576(msg)
        fields1106 = _t1577
        assert fields1106 is not None
        unwrapped_fields1107 = fields1106
        self.write("(")
        self.write("columns")
        self.indent_sexp()
        if not len(unwrapped_fields1107) == 0:
            self.newline()
            for i1109, elem1108 in enumerate(unwrapped_fields1107):
                if (i1109 > 0):
                    self.newline()
                self.pretty_export_csv_column(elem1108)
        self.dedent()
        self.write(")")
        return None

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn) -> None:
        _flat = self._try_flat(msg, self.pretty_export_csv_column)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1578(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        _t1579 = _t1578(msg)
        fields1110 = _t1579
        assert fields1110 is not None
        unwrapped_fields1111 = fields1110
        self.write("(")
        self.write("column")
        self.indent_sexp()
        self.newline()
        field1112 = unwrapped_fields1111[0]
        self.write(self.format_string_value(field1112))
        self.newline()
        field1113 = unwrapped_fields1111[1]
        self.pretty_relation_id(field1113)
        self.dedent()
        self.write(")")
        return None


def pretty(msg: Any, io: Optional[IO[str]] = None, max_width: int = 92) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io, max_width=max_width)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()
