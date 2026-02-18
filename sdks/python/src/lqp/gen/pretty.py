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
        _t1933 = logic_pb2.Value(int_value=int(v))
        return _t1933

    def _make_value_int64(self, v: int) -> logic_pb2.Value:
        _t1934 = logic_pb2.Value(int_value=v)
        return _t1934

    def _make_value_float64(self, v: float) -> logic_pb2.Value:
        _t1935 = logic_pb2.Value(float_value=v)
        return _t1935

    def _make_value_string(self, v: str) -> logic_pb2.Value:
        _t1936 = logic_pb2.Value(string_value=v)
        return _t1936

    def _make_value_boolean(self, v: bool) -> logic_pb2.Value:
        _t1937 = logic_pb2.Value(boolean_value=v)
        return _t1937

    def _make_value_uint128(self, v: logic_pb2.UInt128Value) -> logic_pb2.Value:
        _t1938 = logic_pb2.Value(uint128_value=v)
        return _t1938

    def deconstruct_configure(self, msg: transactions_pb2.Configure) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
            _t1939 = self._make_value_string("auto")
            result.append(("ivm.maintenance_level", _t1939,))
        else:
            if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
                _t1940 = self._make_value_string("all")
                result.append(("ivm.maintenance_level", _t1940,))
            else:
                if msg.ivm_config.level == transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
                    _t1941 = self._make_value_string("off")
                    result.append(("ivm.maintenance_level", _t1941,))
        _t1942 = self._make_value_int64(msg.semantics_version)
        result.append(("semantics_version", _t1942,))
        return sorted(result)

    def deconstruct_csv_config(self, msg: logic_pb2.CSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1943 = self._make_value_int32(msg.header_row)
        result.append(("csv_header_row", _t1943,))
        _t1944 = self._make_value_int64(msg.skip)
        result.append(("csv_skip", _t1944,))
        if msg.new_line != "":
            _t1945 = self._make_value_string(msg.new_line)
            result.append(("csv_new_line", _t1945,))
        _t1946 = self._make_value_string(msg.delimiter)
        result.append(("csv_delimiter", _t1946,))
        _t1947 = self._make_value_string(msg.quotechar)
        result.append(("csv_quotechar", _t1947,))
        _t1948 = self._make_value_string(msg.escapechar)
        result.append(("csv_escapechar", _t1948,))
        if msg.comment != "":
            _t1949 = self._make_value_string(msg.comment)
            result.append(("csv_comment", _t1949,))
        for missing_string in msg.missing_strings:
            _t1950 = self._make_value_string(missing_string)
            result.append(("csv_missing_strings", _t1950,))
        _t1951 = self._make_value_string(msg.decimal_separator)
        result.append(("csv_decimal_separator", _t1951,))
        _t1952 = self._make_value_string(msg.encoding)
        result.append(("csv_encoding", _t1952,))
        _t1953 = self._make_value_string(msg.compression)
        result.append(("csv_compression", _t1953,))
        return sorted(result)

    def deconstruct_betree_info_config(self, msg: logic_pb2.BeTreeInfo) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        _t1954 = self._make_value_float64(msg.storage_config.epsilon)
        result.append(("betree_config_epsilon", _t1954,))
        _t1955 = self._make_value_int64(msg.storage_config.max_pivots)
        result.append(("betree_config_max_pivots", _t1955,))
        _t1956 = self._make_value_int64(msg.storage_config.max_deltas)
        result.append(("betree_config_max_deltas", _t1956,))
        _t1957 = self._make_value_int64(msg.storage_config.max_leaf)
        result.append(("betree_config_max_leaf", _t1957,))
        if msg.relation_locator.HasField("root_pageid"):
            if msg.relation_locator.root_pageid is not None:
                assert msg.relation_locator.root_pageid is not None
                _t1958 = self._make_value_uint128(msg.relation_locator.root_pageid)
                result.append(("betree_locator_root_pageid", _t1958,))
        if msg.relation_locator.HasField("inline_data"):
            if msg.relation_locator.inline_data is not None:
                assert msg.relation_locator.inline_data is not None
                _t1959 = self._make_value_string(msg.relation_locator.inline_data.decode('utf-8'))
                result.append(("betree_locator_inline_data", _t1959,))
        _t1960 = self._make_value_int64(msg.relation_locator.element_count)
        result.append(("betree_locator_element_count", _t1960,))
        _t1961 = self._make_value_int64(msg.relation_locator.tree_height)
        result.append(("betree_locator_tree_height", _t1961,))
        return sorted(result)

    def deconstruct_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> list[tuple[str, logic_pb2.Value]]:
        result = []
        if msg.partition_size is not None:
            assert msg.partition_size is not None
            _t1962 = self._make_value_int64(msg.partition_size)
            result.append(("partition_size", _t1962,))
        if msg.compression is not None:
            assert msg.compression is not None
            _t1963 = self._make_value_string(msg.compression)
            result.append(("compression", _t1963,))
        if msg.syntax_header_row is not None:
            assert msg.syntax_header_row is not None
            _t1964 = self._make_value_boolean(msg.syntax_header_row)
            result.append(("syntax_header_row", _t1964,))
        if msg.syntax_missing_string is not None:
            assert msg.syntax_missing_string is not None
            _t1965 = self._make_value_string(msg.syntax_missing_string)
            result.append(("syntax_missing_string", _t1965,))
        if msg.syntax_delim is not None:
            assert msg.syntax_delim is not None
            _t1966 = self._make_value_string(msg.syntax_delim)
            result.append(("syntax_delim", _t1966,))
        if msg.syntax_quotechar is not None:
            assert msg.syntax_quotechar is not None
            _t1967 = self._make_value_string(msg.syntax_quotechar)
            result.append(("syntax_quotechar", _t1967,))
        if msg.syntax_escapechar is not None:
            assert msg.syntax_escapechar is not None
            _t1968 = self._make_value_string(msg.syntax_escapechar)
            result.append(("syntax_escapechar", _t1968,))
        return sorted(result)

    def deconstruct_relation_id_string(self, msg: logic_pb2.RelationId) -> Optional[str]:
        name = self.relation_id_to_string(msg)
        if name != "":
            return name
        else:
            _t1969 = None
        return None

    def deconstruct_relation_id_uint128(self, msg: logic_pb2.RelationId) -> Optional[logic_pb2.UInt128Value]:
        name = self.relation_id_to_string(msg)
        if name == "":
            return self.relation_id_to_uint128(msg)
        else:
            _t1970 = None
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
        def _t1467(_dollar_dollar):
            if _dollar_dollar.HasField("configure"):
                _t1468 = _dollar_dollar.configure
            else:
                _t1468 = None
            if _dollar_dollar.HasField("sync"):
                _t1469 = _dollar_dollar.sync
            else:
                _t1469 = None
            return (_t1468, _t1469, _dollar_dollar.epochs,)
        _t1470 = _t1467(msg)
        fields910 = _t1470
        assert fields910 is not None
        unwrapped_fields911 = fields910
        self.write("(")
        self.write("transaction")
        self.indent_sexp()
        field912 = unwrapped_fields911[0]
        if field912 is not None:
            self.newline()
            assert field912 is not None
            opt_val913 = field912
            self.pretty_configure(opt_val913)
        field914 = unwrapped_fields911[1]
        if field914 is not None:
            self.newline()
            assert field914 is not None
            opt_val915 = field914
            self.pretty_sync(opt_val915)
        field916 = unwrapped_fields911[2]
        if not len(field916) == 0:
            self.newline()
            for i918, elem917 in enumerate(field916):
                if (i918 > 0):
                    self.newline()
                self.pretty_epoch(elem917)
        self.dedent()
        self.write(")")
        return None

    def pretty_configure(self, msg: transactions_pb2.Configure) -> None:
        _flat = self._try_flat(msg, self.pretty_configure)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1471(_dollar_dollar):
            _t1472 = self.deconstruct_configure(_dollar_dollar)
            return _t1472
        _t1473 = _t1471(msg)
        fields919 = _t1473
        assert fields919 is not None
        unwrapped_fields920 = fields919
        self.write("(")
        self.write("configure")
        self.indent_sexp()
        self.newline()
        self.pretty_config_dict(unwrapped_fields920)
        self.dedent()
        self.write(")")
        return None

    def pretty_config_dict(self, msg: Sequence[tuple[str, logic_pb2.Value]]) -> None:
        _flat = self._try_flat(msg, self.pretty_config_dict)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1474(_dollar_dollar):
            return _dollar_dollar
        _t1475 = _t1474(msg)
        fields921 = _t1475
        assert fields921 is not None
        unwrapped_fields922 = fields921
        self.write("{")
        if not len(unwrapped_fields922) == 0:
            self.newline()
            for i924, elem923 in enumerate(unwrapped_fields922):
                if (i924 > 0):
                    self.newline()
                self.pretty_config_key_value(elem923)
        self.write("}")
        return None

    def pretty_config_key_value(self, msg: tuple[str, logic_pb2.Value]) -> None:
        _flat = self._try_flat(msg, self.pretty_config_key_value)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1476(_dollar_dollar):
            return (_dollar_dollar[0], _dollar_dollar[1],)
        _t1477 = _t1476(msg)
        fields925 = _t1477
        assert fields925 is not None
        unwrapped_fields926 = fields925
        self.write(":")
        field927 = unwrapped_fields926[0]
        self.write(field927)
        self.write(" ")
        field928 = unwrapped_fields926[1]
        self.pretty_value(field928)
        return None

    def pretty_value(self, msg: logic_pb2.Value) -> None:
        _flat = self._try_flat(msg, self.pretty_value)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1478(_dollar_dollar):
            if _dollar_dollar.HasField("date_value"):
                _t1479 = _dollar_dollar.date_value
            else:
                _t1479 = None
            return _t1479
        _t1480 = _t1478(msg)
        deconstruct_result947 = _t1480
        if deconstruct_result947 is not None:
            assert deconstruct_result947 is not None
            unwrapped948 = deconstruct_result947
            self.pretty_date(unwrapped948)
        else:
            def _t1481(_dollar_dollar):
                if _dollar_dollar.HasField("datetime_value"):
                    _t1482 = _dollar_dollar.datetime_value
                else:
                    _t1482 = None
                return _t1482
            _t1483 = _t1481(msg)
            deconstruct_result945 = _t1483
            if deconstruct_result945 is not None:
                assert deconstruct_result945 is not None
                unwrapped946 = deconstruct_result945
                self.pretty_datetime(unwrapped946)
            else:
                def _t1484(_dollar_dollar):
                    if _dollar_dollar.HasField("string_value"):
                        _t1485 = _dollar_dollar.string_value
                    else:
                        _t1485 = None
                    return _t1485
                _t1486 = _t1484(msg)
                deconstruct_result943 = _t1486
                if deconstruct_result943 is not None:
                    assert deconstruct_result943 is not None
                    unwrapped944 = deconstruct_result943
                    self.write(self.format_string_value(unwrapped944))
                else:
                    def _t1487(_dollar_dollar):
                        if _dollar_dollar.HasField("int_value"):
                            _t1488 = _dollar_dollar.int_value
                        else:
                            _t1488 = None
                        return _t1488
                    _t1489 = _t1487(msg)
                    deconstruct_result941 = _t1489
                    if deconstruct_result941 is not None:
                        assert deconstruct_result941 is not None
                        unwrapped942 = deconstruct_result941
                        self.write(str(unwrapped942))
                    else:
                        def _t1490(_dollar_dollar):
                            if _dollar_dollar.HasField("float_value"):
                                _t1491 = _dollar_dollar.float_value
                            else:
                                _t1491 = None
                            return _t1491
                        _t1492 = _t1490(msg)
                        deconstruct_result939 = _t1492
                        if deconstruct_result939 is not None:
                            assert deconstruct_result939 is not None
                            unwrapped940 = deconstruct_result939
                            self.write(str(unwrapped940))
                        else:
                            def _t1493(_dollar_dollar):
                                if _dollar_dollar.HasField("uint128_value"):
                                    _t1494 = _dollar_dollar.uint128_value
                                else:
                                    _t1494 = None
                                return _t1494
                            _t1495 = _t1493(msg)
                            deconstruct_result937 = _t1495
                            if deconstruct_result937 is not None:
                                assert deconstruct_result937 is not None
                                unwrapped938 = deconstruct_result937
                                self.write(self.format_uint128(unwrapped938))
                            else:
                                def _t1496(_dollar_dollar):
                                    if _dollar_dollar.HasField("int128_value"):
                                        _t1497 = _dollar_dollar.int128_value
                                    else:
                                        _t1497 = None
                                    return _t1497
                                _t1498 = _t1496(msg)
                                deconstruct_result935 = _t1498
                                if deconstruct_result935 is not None:
                                    assert deconstruct_result935 is not None
                                    unwrapped936 = deconstruct_result935
                                    self.write(self.format_int128(unwrapped936))
                                else:
                                    def _t1499(_dollar_dollar):
                                        if _dollar_dollar.HasField("decimal_value"):
                                            _t1500 = _dollar_dollar.decimal_value
                                        else:
                                            _t1500 = None
                                        return _t1500
                                    _t1501 = _t1499(msg)
                                    deconstruct_result933 = _t1501
                                    if deconstruct_result933 is not None:
                                        assert deconstruct_result933 is not None
                                        unwrapped934 = deconstruct_result933
                                        self.write(self.format_decimal(unwrapped934))
                                    else:
                                        def _t1502(_dollar_dollar):
                                            if _dollar_dollar.HasField("boolean_value"):
                                                _t1503 = _dollar_dollar.boolean_value
                                            else:
                                                _t1503 = None
                                            return _t1503
                                        _t1504 = _t1502(msg)
                                        deconstruct_result931 = _t1504
                                        if deconstruct_result931 is not None:
                                            assert deconstruct_result931 is not None
                                            unwrapped932 = deconstruct_result931
                                            self.pretty_boolean_value(unwrapped932)
                                        else:
                                            def _t1505(_dollar_dollar):
                                                return _dollar_dollar
                                            _t1506 = _t1505(msg)
                                            fields929 = _t1506
                                            assert fields929 is not None
                                            unwrapped_fields930 = fields929
                                            self.write("missing")
        return None

    def pretty_date(self, msg: logic_pb2.DateValue) -> None:
        _flat = self._try_flat(msg, self.pretty_date)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1507(_dollar_dollar):
            return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day),)
        _t1508 = _t1507(msg)
        fields949 = _t1508
        assert fields949 is not None
        unwrapped_fields950 = fields949
        self.write("(")
        self.write("date")
        self.indent_sexp()
        self.newline()
        field951 = unwrapped_fields950[0]
        self.write(str(field951))
        self.newline()
        field952 = unwrapped_fields950[1]
        self.write(str(field952))
        self.newline()
        field953 = unwrapped_fields950[2]
        self.write(str(field953))
        self.dedent()
        self.write(")")
        return None

    def pretty_datetime(self, msg: logic_pb2.DateTimeValue) -> None:
        _flat = self._try_flat(msg, self.pretty_datetime)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1509(_dollar_dollar):
            return (int(_dollar_dollar.year), int(_dollar_dollar.month), int(_dollar_dollar.day), int(_dollar_dollar.hour), int(_dollar_dollar.minute), int(_dollar_dollar.second), int(_dollar_dollar.microsecond),)
        _t1510 = _t1509(msg)
        fields954 = _t1510
        assert fields954 is not None
        unwrapped_fields955 = fields954
        self.write("(")
        self.write("datetime")
        self.indent_sexp()
        self.newline()
        field956 = unwrapped_fields955[0]
        self.write(str(field956))
        self.newline()
        field957 = unwrapped_fields955[1]
        self.write(str(field957))
        self.newline()
        field958 = unwrapped_fields955[2]
        self.write(str(field958))
        self.newline()
        field959 = unwrapped_fields955[3]
        self.write(str(field959))
        self.newline()
        field960 = unwrapped_fields955[4]
        self.write(str(field960))
        self.newline()
        field961 = unwrapped_fields955[5]
        self.write(str(field961))
        field962 = unwrapped_fields955[6]
        if field962 is not None:
            self.newline()
            assert field962 is not None
            opt_val963 = field962
            self.write(str(opt_val963))
        self.dedent()
        self.write(")")
        return None

    def pretty_boolean_value(self, msg: bool) -> None:
        _flat = self._try_flat(msg, self.pretty_boolean_value)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1511(_dollar_dollar):
            if _dollar_dollar:
                _t1512 = ()
            else:
                _t1512 = None
            return _t1512
        _t1513 = _t1511(msg)
        deconstruct_result966 = _t1513
        if deconstruct_result966 is not None:
            assert deconstruct_result966 is not None
            unwrapped967 = deconstruct_result966
            self.write("true")
        else:
            def _t1514(_dollar_dollar):
                if not _dollar_dollar:
                    _t1515 = ()
                else:
                    _t1515 = None
                return _t1515
            _t1516 = _t1514(msg)
            deconstruct_result964 = _t1516
            if deconstruct_result964 is not None:
                assert deconstruct_result964 is not None
                unwrapped965 = deconstruct_result964
                self.write("false")
            else:
                raise ParseError("No matching rule for boolean_value")
        return None

    def pretty_sync(self, msg: transactions_pb2.Sync) -> None:
        _flat = self._try_flat(msg, self.pretty_sync)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1517(_dollar_dollar):
            return _dollar_dollar.fragments
        _t1518 = _t1517(msg)
        fields968 = _t1518
        assert fields968 is not None
        unwrapped_fields969 = fields968
        self.write("(")
        self.write("sync")
        self.indent_sexp()
        if not len(unwrapped_fields969) == 0:
            self.newline()
            for i971, elem970 in enumerate(unwrapped_fields969):
                if (i971 > 0):
                    self.newline()
                self.pretty_fragment_id(elem970)
        self.dedent()
        self.write(")")
        return None

    def pretty_fragment_id(self, msg: fragments_pb2.FragmentId) -> None:
        _flat = self._try_flat(msg, self.pretty_fragment_id)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1519(_dollar_dollar):
            return self.fragment_id_to_string(_dollar_dollar)
        _t1520 = _t1519(msg)
        fields972 = _t1520
        assert fields972 is not None
        unwrapped_fields973 = fields972
        self.write(":")
        self.write(unwrapped_fields973)
        return None

    def pretty_epoch(self, msg: transactions_pb2.Epoch) -> None:
        _flat = self._try_flat(msg, self.pretty_epoch)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1521(_dollar_dollar):
            if not len(_dollar_dollar.writes) == 0:
                _t1522 = _dollar_dollar.writes
            else:
                _t1522 = None
            if not len(_dollar_dollar.reads) == 0:
                _t1523 = _dollar_dollar.reads
            else:
                _t1523 = None
            return (_t1522, _t1523,)
        _t1524 = _t1521(msg)
        fields974 = _t1524
        assert fields974 is not None
        unwrapped_fields975 = fields974
        self.write("(")
        self.write("epoch")
        self.indent_sexp()
        field976 = unwrapped_fields975[0]
        if field976 is not None:
            self.newline()
            assert field976 is not None
            opt_val977 = field976
            self.pretty_epoch_writes(opt_val977)
        field978 = unwrapped_fields975[1]
        if field978 is not None:
            self.newline()
            assert field978 is not None
            opt_val979 = field978
            self.pretty_epoch_reads(opt_val979)
        self.dedent()
        self.write(")")
        return None

    def pretty_epoch_writes(self, msg: Sequence[transactions_pb2.Write]) -> None:
        _flat = self._try_flat(msg, self.pretty_epoch_writes)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1525(_dollar_dollar):
            return _dollar_dollar
        _t1526 = _t1525(msg)
        fields980 = _t1526
        assert fields980 is not None
        unwrapped_fields981 = fields980
        self.write("(")
        self.write("writes")
        self.indent_sexp()
        if not len(unwrapped_fields981) == 0:
            self.newline()
            for i983, elem982 in enumerate(unwrapped_fields981):
                if (i983 > 0):
                    self.newline()
                self.pretty_write(elem982)
        self.dedent()
        self.write(")")
        return None

    def pretty_write(self, msg: transactions_pb2.Write) -> None:
        _flat = self._try_flat(msg, self.pretty_write)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1527(_dollar_dollar):
            if _dollar_dollar.HasField("define"):
                _t1528 = _dollar_dollar.define
            else:
                _t1528 = None
            return _t1528
        _t1529 = _t1527(msg)
        deconstruct_result988 = _t1529
        if deconstruct_result988 is not None:
            assert deconstruct_result988 is not None
            unwrapped989 = deconstruct_result988
            self.pretty_define(unwrapped989)
        else:
            def _t1530(_dollar_dollar):
                if _dollar_dollar.HasField("undefine"):
                    _t1531 = _dollar_dollar.undefine
                else:
                    _t1531 = None
                return _t1531
            _t1532 = _t1530(msg)
            deconstruct_result986 = _t1532
            if deconstruct_result986 is not None:
                assert deconstruct_result986 is not None
                unwrapped987 = deconstruct_result986
                self.pretty_undefine(unwrapped987)
            else:
                def _t1533(_dollar_dollar):
                    if _dollar_dollar.HasField("context"):
                        _t1534 = _dollar_dollar.context
                    else:
                        _t1534 = None
                    return _t1534
                _t1535 = _t1533(msg)
                deconstruct_result984 = _t1535
                if deconstruct_result984 is not None:
                    assert deconstruct_result984 is not None
                    unwrapped985 = deconstruct_result984
                    self.pretty_context(unwrapped985)
                else:
                    raise ParseError("No matching rule for write")
        return None

    def pretty_define(self, msg: transactions_pb2.Define) -> None:
        _flat = self._try_flat(msg, self.pretty_define)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1536(_dollar_dollar):
            return _dollar_dollar.fragment
        _t1537 = _t1536(msg)
        fields990 = _t1537
        assert fields990 is not None
        unwrapped_fields991 = fields990
        self.write("(")
        self.write("define")
        self.indent_sexp()
        self.newline()
        self.pretty_fragment(unwrapped_fields991)
        self.dedent()
        self.write(")")
        return None

    def pretty_fragment(self, msg: fragments_pb2.Fragment) -> None:
        _flat = self._try_flat(msg, self.pretty_fragment)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1538(_dollar_dollar):
            self.start_pretty_fragment(_dollar_dollar)
            return (_dollar_dollar.id, _dollar_dollar.declarations,)
        _t1539 = _t1538(msg)
        fields992 = _t1539
        assert fields992 is not None
        unwrapped_fields993 = fields992
        self.write("(")
        self.write("fragment")
        self.indent_sexp()
        self.newline()
        field994 = unwrapped_fields993[0]
        self.pretty_new_fragment_id(field994)
        field995 = unwrapped_fields993[1]
        if not len(field995) == 0:
            self.newline()
            for i997, elem996 in enumerate(field995):
                if (i997 > 0):
                    self.newline()
                self.pretty_declaration(elem996)
        self.dedent()
        self.write(")")
        return None

    def pretty_new_fragment_id(self, msg: fragments_pb2.FragmentId) -> None:
        _flat = self._try_flat(msg, self.pretty_new_fragment_id)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1540(_dollar_dollar):
            return _dollar_dollar
        _t1541 = _t1540(msg)
        fields998 = _t1541
        assert fields998 is not None
        unwrapped_fields999 = fields998
        self.pretty_fragment_id(unwrapped_fields999)
        return None

    def pretty_declaration(self, msg: logic_pb2.Declaration) -> None:
        _flat = self._try_flat(msg, self.pretty_declaration)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1542(_dollar_dollar):
            if _dollar_dollar.HasField("def"):
                _t1543 = getattr(_dollar_dollar, 'def')
            else:
                _t1543 = None
            return _t1543
        _t1544 = _t1542(msg)
        deconstruct_result1006 = _t1544
        if deconstruct_result1006 is not None:
            assert deconstruct_result1006 is not None
            unwrapped1007 = deconstruct_result1006
            self.pretty_def(unwrapped1007)
        else:
            def _t1545(_dollar_dollar):
                if _dollar_dollar.HasField("algorithm"):
                    _t1546 = _dollar_dollar.algorithm
                else:
                    _t1546 = None
                return _t1546
            _t1547 = _t1545(msg)
            deconstruct_result1004 = _t1547
            if deconstruct_result1004 is not None:
                assert deconstruct_result1004 is not None
                unwrapped1005 = deconstruct_result1004
                self.pretty_algorithm(unwrapped1005)
            else:
                def _t1548(_dollar_dollar):
                    if _dollar_dollar.HasField("constraint"):
                        _t1549 = _dollar_dollar.constraint
                    else:
                        _t1549 = None
                    return _t1549
                _t1550 = _t1548(msg)
                deconstruct_result1002 = _t1550
                if deconstruct_result1002 is not None:
                    assert deconstruct_result1002 is not None
                    unwrapped1003 = deconstruct_result1002
                    self.pretty_constraint(unwrapped1003)
                else:
                    def _t1551(_dollar_dollar):
                        if _dollar_dollar.HasField("data"):
                            _t1552 = _dollar_dollar.data
                        else:
                            _t1552 = None
                        return _t1552
                    _t1553 = _t1551(msg)
                    deconstruct_result1000 = _t1553
                    if deconstruct_result1000 is not None:
                        assert deconstruct_result1000 is not None
                        unwrapped1001 = deconstruct_result1000
                        self.pretty_data(unwrapped1001)
                    else:
                        raise ParseError("No matching rule for declaration")
        return None

    def pretty_def(self, msg: logic_pb2.Def) -> None:
        _flat = self._try_flat(msg, self.pretty_def)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1554(_dollar_dollar):
            if not len(_dollar_dollar.attrs) == 0:
                _t1555 = _dollar_dollar.attrs
            else:
                _t1555 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1555,)
        _t1556 = _t1554(msg)
        fields1008 = _t1556
        assert fields1008 is not None
        unwrapped_fields1009 = fields1008
        self.write("(")
        self.write("def")
        self.indent_sexp()
        self.newline()
        field1010 = unwrapped_fields1009[0]
        self.pretty_relation_id(field1010)
        self.newline()
        field1011 = unwrapped_fields1009[1]
        self.pretty_abstraction(field1011)
        field1012 = unwrapped_fields1009[2]
        if field1012 is not None:
            self.newline()
            assert field1012 is not None
            opt_val1013 = field1012
            self.pretty_attrs(opt_val1013)
        self.dedent()
        self.write(")")
        return None

    def pretty_relation_id(self, msg: logic_pb2.RelationId) -> None:
        _flat = self._try_flat(msg, self.pretty_relation_id)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1557(_dollar_dollar):
            _t1558 = self.deconstruct_relation_id_string(_dollar_dollar)
            return _t1558
        _t1559 = _t1557(msg)
        deconstruct_result1016 = _t1559
        if deconstruct_result1016 is not None:
            assert deconstruct_result1016 is not None
            unwrapped1017 = deconstruct_result1016
            self.write(":")
            self.write(unwrapped1017)
        else:
            def _t1560(_dollar_dollar):
                _t1561 = self.deconstruct_relation_id_uint128(_dollar_dollar)
                return _t1561
            _t1562 = _t1560(msg)
            deconstruct_result1014 = _t1562
            if deconstruct_result1014 is not None:
                assert deconstruct_result1014 is not None
                unwrapped1015 = deconstruct_result1014
                self.write(self.format_uint128(unwrapped1015))
            else:
                raise ParseError("No matching rule for relation_id")
        return None

    def pretty_abstraction(self, msg: logic_pb2.Abstraction) -> None:
        _flat = self._try_flat(msg, self.pretty_abstraction)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1563(_dollar_dollar):
            _t1564 = self.deconstruct_bindings(_dollar_dollar)
            return (_t1564, _dollar_dollar.value,)
        _t1565 = _t1563(msg)
        fields1018 = _t1565
        assert fields1018 is not None
        unwrapped_fields1019 = fields1018
        self.write("(")
        self.indent()
        field1020 = unwrapped_fields1019[0]
        self.pretty_bindings(field1020)
        self.newline()
        field1021 = unwrapped_fields1019[1]
        self.pretty_formula(field1021)
        self.dedent()
        self.write(")")
        return None

    def pretty_bindings(self, msg: tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]) -> None:
        _flat = self._try_flat(msg, self.pretty_bindings)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1566(_dollar_dollar):
            if not len(_dollar_dollar[1]) == 0:
                _t1567 = _dollar_dollar[1]
            else:
                _t1567 = None
            return (_dollar_dollar[0], _t1567,)
        _t1568 = _t1566(msg)
        fields1022 = _t1568
        assert fields1022 is not None
        unwrapped_fields1023 = fields1022
        self.write("[")
        self.indent()
        field1024 = unwrapped_fields1023[0]
        for i1026, elem1025 in enumerate(field1024):
            if (i1026 > 0):
                self.newline()
            self.pretty_binding(elem1025)
        field1027 = unwrapped_fields1023[1]
        if field1027 is not None:
            self.newline()
            assert field1027 is not None
            opt_val1028 = field1027
            self.pretty_value_bindings(opt_val1028)
        self.dedent()
        self.write("]")
        return None

    def pretty_binding(self, msg: logic_pb2.Binding) -> None:
        _flat = self._try_flat(msg, self.pretty_binding)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1569(_dollar_dollar):
            return (_dollar_dollar.var.name, _dollar_dollar.type,)
        _t1570 = _t1569(msg)
        fields1029 = _t1570
        assert fields1029 is not None
        unwrapped_fields1030 = fields1029
        field1031 = unwrapped_fields1030[0]
        self.write(field1031)
        self.write("::")
        field1032 = unwrapped_fields1030[1]
        self.pretty_type(field1032)
        return None

    def pretty_type(self, msg: logic_pb2.Type) -> None:
        _flat = self._try_flat(msg, self.pretty_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1571(_dollar_dollar):
            if _dollar_dollar.HasField("unspecified_type"):
                _t1572 = _dollar_dollar.unspecified_type
            else:
                _t1572 = None
            return _t1572
        _t1573 = _t1571(msg)
        deconstruct_result1053 = _t1573
        if deconstruct_result1053 is not None:
            assert deconstruct_result1053 is not None
            unwrapped1054 = deconstruct_result1053
            self.pretty_unspecified_type(unwrapped1054)
        else:
            def _t1574(_dollar_dollar):
                if _dollar_dollar.HasField("string_type"):
                    _t1575 = _dollar_dollar.string_type
                else:
                    _t1575 = None
                return _t1575
            _t1576 = _t1574(msg)
            deconstruct_result1051 = _t1576
            if deconstruct_result1051 is not None:
                assert deconstruct_result1051 is not None
                unwrapped1052 = deconstruct_result1051
                self.pretty_string_type(unwrapped1052)
            else:
                def _t1577(_dollar_dollar):
                    if _dollar_dollar.HasField("int_type"):
                        _t1578 = _dollar_dollar.int_type
                    else:
                        _t1578 = None
                    return _t1578
                _t1579 = _t1577(msg)
                deconstruct_result1049 = _t1579
                if deconstruct_result1049 is not None:
                    assert deconstruct_result1049 is not None
                    unwrapped1050 = deconstruct_result1049
                    self.pretty_int_type(unwrapped1050)
                else:
                    def _t1580(_dollar_dollar):
                        if _dollar_dollar.HasField("float_type"):
                            _t1581 = _dollar_dollar.float_type
                        else:
                            _t1581 = None
                        return _t1581
                    _t1582 = _t1580(msg)
                    deconstruct_result1047 = _t1582
                    if deconstruct_result1047 is not None:
                        assert deconstruct_result1047 is not None
                        unwrapped1048 = deconstruct_result1047
                        self.pretty_float_type(unwrapped1048)
                    else:
                        def _t1583(_dollar_dollar):
                            if _dollar_dollar.HasField("uint128_type"):
                                _t1584 = _dollar_dollar.uint128_type
                            else:
                                _t1584 = None
                            return _t1584
                        _t1585 = _t1583(msg)
                        deconstruct_result1045 = _t1585
                        if deconstruct_result1045 is not None:
                            assert deconstruct_result1045 is not None
                            unwrapped1046 = deconstruct_result1045
                            self.pretty_uint128_type(unwrapped1046)
                        else:
                            def _t1586(_dollar_dollar):
                                if _dollar_dollar.HasField("int128_type"):
                                    _t1587 = _dollar_dollar.int128_type
                                else:
                                    _t1587 = None
                                return _t1587
                            _t1588 = _t1586(msg)
                            deconstruct_result1043 = _t1588
                            if deconstruct_result1043 is not None:
                                assert deconstruct_result1043 is not None
                                unwrapped1044 = deconstruct_result1043
                                self.pretty_int128_type(unwrapped1044)
                            else:
                                def _t1589(_dollar_dollar):
                                    if _dollar_dollar.HasField("date_type"):
                                        _t1590 = _dollar_dollar.date_type
                                    else:
                                        _t1590 = None
                                    return _t1590
                                _t1591 = _t1589(msg)
                                deconstruct_result1041 = _t1591
                                if deconstruct_result1041 is not None:
                                    assert deconstruct_result1041 is not None
                                    unwrapped1042 = deconstruct_result1041
                                    self.pretty_date_type(unwrapped1042)
                                else:
                                    def _t1592(_dollar_dollar):
                                        if _dollar_dollar.HasField("datetime_type"):
                                            _t1593 = _dollar_dollar.datetime_type
                                        else:
                                            _t1593 = None
                                        return _t1593
                                    _t1594 = _t1592(msg)
                                    deconstruct_result1039 = _t1594
                                    if deconstruct_result1039 is not None:
                                        assert deconstruct_result1039 is not None
                                        unwrapped1040 = deconstruct_result1039
                                        self.pretty_datetime_type(unwrapped1040)
                                    else:
                                        def _t1595(_dollar_dollar):
                                            if _dollar_dollar.HasField("missing_type"):
                                                _t1596 = _dollar_dollar.missing_type
                                            else:
                                                _t1596 = None
                                            return _t1596
                                        _t1597 = _t1595(msg)
                                        deconstruct_result1037 = _t1597
                                        if deconstruct_result1037 is not None:
                                            assert deconstruct_result1037 is not None
                                            unwrapped1038 = deconstruct_result1037
                                            self.pretty_missing_type(unwrapped1038)
                                        else:
                                            def _t1598(_dollar_dollar):
                                                if _dollar_dollar.HasField("decimal_type"):
                                                    _t1599 = _dollar_dollar.decimal_type
                                                else:
                                                    _t1599 = None
                                                return _t1599
                                            _t1600 = _t1598(msg)
                                            deconstruct_result1035 = _t1600
                                            if deconstruct_result1035 is not None:
                                                assert deconstruct_result1035 is not None
                                                unwrapped1036 = deconstruct_result1035
                                                self.pretty_decimal_type(unwrapped1036)
                                            else:
                                                def _t1601(_dollar_dollar):
                                                    if _dollar_dollar.HasField("boolean_type"):
                                                        _t1602 = _dollar_dollar.boolean_type
                                                    else:
                                                        _t1602 = None
                                                    return _t1602
                                                _t1603 = _t1601(msg)
                                                deconstruct_result1033 = _t1603
                                                if deconstruct_result1033 is not None:
                                                    assert deconstruct_result1033 is not None
                                                    unwrapped1034 = deconstruct_result1033
                                                    self.pretty_boolean_type(unwrapped1034)
                                                else:
                                                    raise ParseError("No matching rule for type")
        return None

    def pretty_unspecified_type(self, msg: logic_pb2.UnspecifiedType) -> None:
        _flat = self._try_flat(msg, self.pretty_unspecified_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1604(_dollar_dollar):
            return _dollar_dollar
        _t1605 = _t1604(msg)
        fields1055 = _t1605
        assert fields1055 is not None
        unwrapped_fields1056 = fields1055
        self.write("UNKNOWN")
        return None

    def pretty_string_type(self, msg: logic_pb2.StringType) -> None:
        _flat = self._try_flat(msg, self.pretty_string_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1606(_dollar_dollar):
            return _dollar_dollar
        _t1607 = _t1606(msg)
        fields1057 = _t1607
        assert fields1057 is not None
        unwrapped_fields1058 = fields1057
        self.write("STRING")
        return None

    def pretty_int_type(self, msg: logic_pb2.IntType) -> None:
        _flat = self._try_flat(msg, self.pretty_int_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1608(_dollar_dollar):
            return _dollar_dollar
        _t1609 = _t1608(msg)
        fields1059 = _t1609
        assert fields1059 is not None
        unwrapped_fields1060 = fields1059
        self.write("INT")
        return None

    def pretty_float_type(self, msg: logic_pb2.FloatType) -> None:
        _flat = self._try_flat(msg, self.pretty_float_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1610(_dollar_dollar):
            return _dollar_dollar
        _t1611 = _t1610(msg)
        fields1061 = _t1611
        assert fields1061 is not None
        unwrapped_fields1062 = fields1061
        self.write("FLOAT")
        return None

    def pretty_uint128_type(self, msg: logic_pb2.UInt128Type) -> None:
        _flat = self._try_flat(msg, self.pretty_uint128_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1612(_dollar_dollar):
            return _dollar_dollar
        _t1613 = _t1612(msg)
        fields1063 = _t1613
        assert fields1063 is not None
        unwrapped_fields1064 = fields1063
        self.write("UINT128")
        return None

    def pretty_int128_type(self, msg: logic_pb2.Int128Type) -> None:
        _flat = self._try_flat(msg, self.pretty_int128_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1614(_dollar_dollar):
            return _dollar_dollar
        _t1615 = _t1614(msg)
        fields1065 = _t1615
        assert fields1065 is not None
        unwrapped_fields1066 = fields1065
        self.write("INT128")
        return None

    def pretty_date_type(self, msg: logic_pb2.DateType) -> None:
        _flat = self._try_flat(msg, self.pretty_date_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1616(_dollar_dollar):
            return _dollar_dollar
        _t1617 = _t1616(msg)
        fields1067 = _t1617
        assert fields1067 is not None
        unwrapped_fields1068 = fields1067
        self.write("DATE")
        return None

    def pretty_datetime_type(self, msg: logic_pb2.DateTimeType) -> None:
        _flat = self._try_flat(msg, self.pretty_datetime_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1618(_dollar_dollar):
            return _dollar_dollar
        _t1619 = _t1618(msg)
        fields1069 = _t1619
        assert fields1069 is not None
        unwrapped_fields1070 = fields1069
        self.write("DATETIME")
        return None

    def pretty_missing_type(self, msg: logic_pb2.MissingType) -> None:
        _flat = self._try_flat(msg, self.pretty_missing_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1620(_dollar_dollar):
            return _dollar_dollar
        _t1621 = _t1620(msg)
        fields1071 = _t1621
        assert fields1071 is not None
        unwrapped_fields1072 = fields1071
        self.write("MISSING")
        return None

    def pretty_decimal_type(self, msg: logic_pb2.DecimalType) -> None:
        _flat = self._try_flat(msg, self.pretty_decimal_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1622(_dollar_dollar):
            return (int(_dollar_dollar.precision), int(_dollar_dollar.scale),)
        _t1623 = _t1622(msg)
        fields1073 = _t1623
        assert fields1073 is not None
        unwrapped_fields1074 = fields1073
        self.write("(")
        self.write("DECIMAL")
        self.indent_sexp()
        self.newline()
        field1075 = unwrapped_fields1074[0]
        self.write(str(field1075))
        self.newline()
        field1076 = unwrapped_fields1074[1]
        self.write(str(field1076))
        self.dedent()
        self.write(")")
        return None

    def pretty_boolean_type(self, msg: logic_pb2.BooleanType) -> None:
        _flat = self._try_flat(msg, self.pretty_boolean_type)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1624(_dollar_dollar):
            return _dollar_dollar
        _t1625 = _t1624(msg)
        fields1077 = _t1625
        assert fields1077 is not None
        unwrapped_fields1078 = fields1077
        self.write("BOOLEAN")
        return None

    def pretty_value_bindings(self, msg: Sequence[logic_pb2.Binding]) -> None:
        _flat = self._try_flat(msg, self.pretty_value_bindings)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1626(_dollar_dollar):
            return _dollar_dollar
        _t1627 = _t1626(msg)
        fields1079 = _t1627
        assert fields1079 is not None
        unwrapped_fields1080 = fields1079
        self.write("|")
        if not len(unwrapped_fields1080) == 0:
            self.write(" ")
            for i1082, elem1081 in enumerate(unwrapped_fields1080):
                if (i1082 > 0):
                    self.newline()
                self.pretty_binding(elem1081)
        return None

    def pretty_formula(self, msg: logic_pb2.Formula) -> None:
        _flat = self._try_flat(msg, self.pretty_formula)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1628(_dollar_dollar):
            if (_dollar_dollar.HasField("conjunction") and len(_dollar_dollar.conjunction.args) == 0):
                _t1629 = _dollar_dollar.conjunction
            else:
                _t1629 = None
            return _t1629
        _t1630 = _t1628(msg)
        deconstruct_result1107 = _t1630
        if deconstruct_result1107 is not None:
            assert deconstruct_result1107 is not None
            unwrapped1108 = deconstruct_result1107
            self.pretty_true(unwrapped1108)
        else:
            def _t1631(_dollar_dollar):
                if (_dollar_dollar.HasField("disjunction") and len(_dollar_dollar.disjunction.args) == 0):
                    _t1632 = _dollar_dollar.disjunction
                else:
                    _t1632 = None
                return _t1632
            _t1633 = _t1631(msg)
            deconstruct_result1105 = _t1633
            if deconstruct_result1105 is not None:
                assert deconstruct_result1105 is not None
                unwrapped1106 = deconstruct_result1105
                self.pretty_false(unwrapped1106)
            else:
                def _t1634(_dollar_dollar):
                    if _dollar_dollar.HasField("exists"):
                        _t1635 = _dollar_dollar.exists
                    else:
                        _t1635 = None
                    return _t1635
                _t1636 = _t1634(msg)
                deconstruct_result1103 = _t1636
                if deconstruct_result1103 is not None:
                    assert deconstruct_result1103 is not None
                    unwrapped1104 = deconstruct_result1103
                    self.pretty_exists(unwrapped1104)
                else:
                    def _t1637(_dollar_dollar):
                        if _dollar_dollar.HasField("reduce"):
                            _t1638 = _dollar_dollar.reduce
                        else:
                            _t1638 = None
                        return _t1638
                    _t1639 = _t1637(msg)
                    deconstruct_result1101 = _t1639
                    if deconstruct_result1101 is not None:
                        assert deconstruct_result1101 is not None
                        unwrapped1102 = deconstruct_result1101
                        self.pretty_reduce(unwrapped1102)
                    else:
                        def _t1640(_dollar_dollar):
                            if _dollar_dollar.HasField("conjunction"):
                                _t1641 = _dollar_dollar.conjunction
                            else:
                                _t1641 = None
                            return _t1641
                        _t1642 = _t1640(msg)
                        deconstruct_result1099 = _t1642
                        if deconstruct_result1099 is not None:
                            assert deconstruct_result1099 is not None
                            unwrapped1100 = deconstruct_result1099
                            self.pretty_conjunction(unwrapped1100)
                        else:
                            def _t1643(_dollar_dollar):
                                if _dollar_dollar.HasField("disjunction"):
                                    _t1644 = _dollar_dollar.disjunction
                                else:
                                    _t1644 = None
                                return _t1644
                            _t1645 = _t1643(msg)
                            deconstruct_result1097 = _t1645
                            if deconstruct_result1097 is not None:
                                assert deconstruct_result1097 is not None
                                unwrapped1098 = deconstruct_result1097
                                self.pretty_disjunction(unwrapped1098)
                            else:
                                def _t1646(_dollar_dollar):
                                    if _dollar_dollar.HasField("not"):
                                        _t1647 = getattr(_dollar_dollar, 'not')
                                    else:
                                        _t1647 = None
                                    return _t1647
                                _t1648 = _t1646(msg)
                                deconstruct_result1095 = _t1648
                                if deconstruct_result1095 is not None:
                                    assert deconstruct_result1095 is not None
                                    unwrapped1096 = deconstruct_result1095
                                    self.pretty_not(unwrapped1096)
                                else:
                                    def _t1649(_dollar_dollar):
                                        if _dollar_dollar.HasField("ffi"):
                                            _t1650 = _dollar_dollar.ffi
                                        else:
                                            _t1650 = None
                                        return _t1650
                                    _t1651 = _t1649(msg)
                                    deconstruct_result1093 = _t1651
                                    if deconstruct_result1093 is not None:
                                        assert deconstruct_result1093 is not None
                                        unwrapped1094 = deconstruct_result1093
                                        self.pretty_ffi(unwrapped1094)
                                    else:
                                        def _t1652(_dollar_dollar):
                                            if _dollar_dollar.HasField("atom"):
                                                _t1653 = _dollar_dollar.atom
                                            else:
                                                _t1653 = None
                                            return _t1653
                                        _t1654 = _t1652(msg)
                                        deconstruct_result1091 = _t1654
                                        if deconstruct_result1091 is not None:
                                            assert deconstruct_result1091 is not None
                                            unwrapped1092 = deconstruct_result1091
                                            self.pretty_atom(unwrapped1092)
                                        else:
                                            def _t1655(_dollar_dollar):
                                                if _dollar_dollar.HasField("pragma"):
                                                    _t1656 = _dollar_dollar.pragma
                                                else:
                                                    _t1656 = None
                                                return _t1656
                                            _t1657 = _t1655(msg)
                                            deconstruct_result1089 = _t1657
                                            if deconstruct_result1089 is not None:
                                                assert deconstruct_result1089 is not None
                                                unwrapped1090 = deconstruct_result1089
                                                self.pretty_pragma(unwrapped1090)
                                            else:
                                                def _t1658(_dollar_dollar):
                                                    if _dollar_dollar.HasField("primitive"):
                                                        _t1659 = _dollar_dollar.primitive
                                                    else:
                                                        _t1659 = None
                                                    return _t1659
                                                _t1660 = _t1658(msg)
                                                deconstruct_result1087 = _t1660
                                                if deconstruct_result1087 is not None:
                                                    assert deconstruct_result1087 is not None
                                                    unwrapped1088 = deconstruct_result1087
                                                    self.pretty_primitive(unwrapped1088)
                                                else:
                                                    def _t1661(_dollar_dollar):
                                                        if _dollar_dollar.HasField("rel_atom"):
                                                            _t1662 = _dollar_dollar.rel_atom
                                                        else:
                                                            _t1662 = None
                                                        return _t1662
                                                    _t1663 = _t1661(msg)
                                                    deconstruct_result1085 = _t1663
                                                    if deconstruct_result1085 is not None:
                                                        assert deconstruct_result1085 is not None
                                                        unwrapped1086 = deconstruct_result1085
                                                        self.pretty_rel_atom(unwrapped1086)
                                                    else:
                                                        def _t1664(_dollar_dollar):
                                                            if _dollar_dollar.HasField("cast"):
                                                                _t1665 = _dollar_dollar.cast
                                                            else:
                                                                _t1665 = None
                                                            return _t1665
                                                        _t1666 = _t1664(msg)
                                                        deconstruct_result1083 = _t1666
                                                        if deconstruct_result1083 is not None:
                                                            assert deconstruct_result1083 is not None
                                                            unwrapped1084 = deconstruct_result1083
                                                            self.pretty_cast(unwrapped1084)
                                                        else:
                                                            raise ParseError("No matching rule for formula")
        return None

    def pretty_true(self, msg: logic_pb2.Conjunction) -> None:
        _flat = self._try_flat(msg, self.pretty_true)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1667(_dollar_dollar):
            return _dollar_dollar
        _t1668 = _t1667(msg)
        fields1109 = _t1668
        assert fields1109 is not None
        unwrapped_fields1110 = fields1109
        self.write("(")
        self.write("true")
        self.write(")")
        return None

    def pretty_false(self, msg: logic_pb2.Disjunction) -> None:
        _flat = self._try_flat(msg, self.pretty_false)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1669(_dollar_dollar):
            return _dollar_dollar
        _t1670 = _t1669(msg)
        fields1111 = _t1670
        assert fields1111 is not None
        unwrapped_fields1112 = fields1111
        self.write("(")
        self.write("false")
        self.write(")")
        return None

    def pretty_exists(self, msg: logic_pb2.Exists) -> None:
        _flat = self._try_flat(msg, self.pretty_exists)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1671(_dollar_dollar):
            _t1672 = self.deconstruct_bindings(_dollar_dollar.body)
            return (_t1672, _dollar_dollar.body.value,)
        _t1673 = _t1671(msg)
        fields1113 = _t1673
        assert fields1113 is not None
        unwrapped_fields1114 = fields1113
        self.write("(")
        self.write("exists")
        self.indent_sexp()
        self.newline()
        field1115 = unwrapped_fields1114[0]
        self.pretty_bindings(field1115)
        self.newline()
        field1116 = unwrapped_fields1114[1]
        self.pretty_formula(field1116)
        self.dedent()
        self.write(")")
        return None

    def pretty_reduce(self, msg: logic_pb2.Reduce) -> None:
        _flat = self._try_flat(msg, self.pretty_reduce)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1674(_dollar_dollar):
            return (_dollar_dollar.op, _dollar_dollar.body, _dollar_dollar.terms,)
        _t1675 = _t1674(msg)
        fields1117 = _t1675
        assert fields1117 is not None
        unwrapped_fields1118 = fields1117
        self.write("(")
        self.write("reduce")
        self.indent_sexp()
        self.newline()
        field1119 = unwrapped_fields1118[0]
        self.pretty_abstraction(field1119)
        self.newline()
        field1120 = unwrapped_fields1118[1]
        self.pretty_abstraction(field1120)
        self.newline()
        field1121 = unwrapped_fields1118[2]
        self.pretty_terms(field1121)
        self.dedent()
        self.write(")")
        return None

    def pretty_terms(self, msg: Sequence[logic_pb2.Term]) -> None:
        _flat = self._try_flat(msg, self.pretty_terms)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1676(_dollar_dollar):
            return _dollar_dollar
        _t1677 = _t1676(msg)
        fields1122 = _t1677
        assert fields1122 is not None
        unwrapped_fields1123 = fields1122
        self.write("(")
        self.write("terms")
        self.indent_sexp()
        if not len(unwrapped_fields1123) == 0:
            self.newline()
            for i1125, elem1124 in enumerate(unwrapped_fields1123):
                if (i1125 > 0):
                    self.newline()
                self.pretty_term(elem1124)
        self.dedent()
        self.write(")")
        return None

    def pretty_term(self, msg: logic_pb2.Term) -> None:
        _flat = self._try_flat(msg, self.pretty_term)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1678(_dollar_dollar):
            if _dollar_dollar.HasField("var"):
                _t1679 = _dollar_dollar.var
            else:
                _t1679 = None
            return _t1679
        _t1680 = _t1678(msg)
        deconstruct_result1128 = _t1680
        if deconstruct_result1128 is not None:
            assert deconstruct_result1128 is not None
            unwrapped1129 = deconstruct_result1128
            self.pretty_var(unwrapped1129)
        else:
            def _t1681(_dollar_dollar):
                if _dollar_dollar.HasField("constant"):
                    _t1682 = _dollar_dollar.constant
                else:
                    _t1682 = None
                return _t1682
            _t1683 = _t1681(msg)
            deconstruct_result1126 = _t1683
            if deconstruct_result1126 is not None:
                assert deconstruct_result1126 is not None
                unwrapped1127 = deconstruct_result1126
                self.pretty_constant(unwrapped1127)
            else:
                raise ParseError("No matching rule for term")
        return None

    def pretty_var(self, msg: logic_pb2.Var) -> None:
        _flat = self._try_flat(msg, self.pretty_var)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1684(_dollar_dollar):
            return _dollar_dollar.name
        _t1685 = _t1684(msg)
        fields1130 = _t1685
        assert fields1130 is not None
        unwrapped_fields1131 = fields1130
        self.write(unwrapped_fields1131)
        return None

    def pretty_constant(self, msg: logic_pb2.Value) -> None:
        _flat = self._try_flat(msg, self.pretty_constant)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1686(_dollar_dollar):
            return _dollar_dollar
        _t1687 = _t1686(msg)
        fields1132 = _t1687
        assert fields1132 is not None
        unwrapped_fields1133 = fields1132
        self.pretty_value(unwrapped_fields1133)
        return None

    def pretty_conjunction(self, msg: logic_pb2.Conjunction) -> None:
        _flat = self._try_flat(msg, self.pretty_conjunction)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1688(_dollar_dollar):
            return _dollar_dollar.args
        _t1689 = _t1688(msg)
        fields1134 = _t1689
        assert fields1134 is not None
        unwrapped_fields1135 = fields1134
        self.write("(")
        self.write("and")
        self.indent_sexp()
        if not len(unwrapped_fields1135) == 0:
            self.newline()
            for i1137, elem1136 in enumerate(unwrapped_fields1135):
                if (i1137 > 0):
                    self.newline()
                self.pretty_formula(elem1136)
        self.dedent()
        self.write(")")
        return None

    def pretty_disjunction(self, msg: logic_pb2.Disjunction) -> None:
        _flat = self._try_flat(msg, self.pretty_disjunction)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1690(_dollar_dollar):
            return _dollar_dollar.args
        _t1691 = _t1690(msg)
        fields1138 = _t1691
        assert fields1138 is not None
        unwrapped_fields1139 = fields1138
        self.write("(")
        self.write("or")
        self.indent_sexp()
        if not len(unwrapped_fields1139) == 0:
            self.newline()
            for i1141, elem1140 in enumerate(unwrapped_fields1139):
                if (i1141 > 0):
                    self.newline()
                self.pretty_formula(elem1140)
        self.dedent()
        self.write(")")
        return None

    def pretty_not(self, msg: logic_pb2.Not) -> None:
        _flat = self._try_flat(msg, self.pretty_not)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1692(_dollar_dollar):
            return _dollar_dollar.arg
        _t1693 = _t1692(msg)
        fields1142 = _t1693
        assert fields1142 is not None
        unwrapped_fields1143 = fields1142
        self.write("(")
        self.write("not")
        self.indent_sexp()
        self.newline()
        self.pretty_formula(unwrapped_fields1143)
        self.dedent()
        self.write(")")
        return None

    def pretty_ffi(self, msg: logic_pb2.FFI) -> None:
        _flat = self._try_flat(msg, self.pretty_ffi)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1694(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args, _dollar_dollar.terms,)
        _t1695 = _t1694(msg)
        fields1144 = _t1695
        assert fields1144 is not None
        unwrapped_fields1145 = fields1144
        self.write("(")
        self.write("ffi")
        self.indent_sexp()
        self.newline()
        field1146 = unwrapped_fields1145[0]
        self.pretty_name(field1146)
        self.newline()
        field1147 = unwrapped_fields1145[1]
        self.pretty_ffi_args(field1147)
        self.newline()
        field1148 = unwrapped_fields1145[2]
        self.pretty_terms(field1148)
        self.dedent()
        self.write(")")
        return None

    def pretty_name(self, msg: str) -> None:
        _flat = self._try_flat(msg, self.pretty_name)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1696(_dollar_dollar):
            return _dollar_dollar
        _t1697 = _t1696(msg)
        fields1149 = _t1697
        assert fields1149 is not None
        unwrapped_fields1150 = fields1149
        self.write(":")
        self.write(unwrapped_fields1150)
        return None

    def pretty_ffi_args(self, msg: Sequence[logic_pb2.Abstraction]) -> None:
        _flat = self._try_flat(msg, self.pretty_ffi_args)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1698(_dollar_dollar):
            return _dollar_dollar
        _t1699 = _t1698(msg)
        fields1151 = _t1699
        assert fields1151 is not None
        unwrapped_fields1152 = fields1151
        self.write("(")
        self.write("args")
        self.indent_sexp()
        if not len(unwrapped_fields1152) == 0:
            self.newline()
            for i1154, elem1153 in enumerate(unwrapped_fields1152):
                if (i1154 > 0):
                    self.newline()
                self.pretty_abstraction(elem1153)
        self.dedent()
        self.write(")")
        return None

    def pretty_atom(self, msg: logic_pb2.Atom) -> None:
        _flat = self._try_flat(msg, self.pretty_atom)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1700(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t1701 = _t1700(msg)
        fields1155 = _t1701
        assert fields1155 is not None
        unwrapped_fields1156 = fields1155
        self.write("(")
        self.write("atom")
        self.indent_sexp()
        self.newline()
        field1157 = unwrapped_fields1156[0]
        self.pretty_relation_id(field1157)
        field1158 = unwrapped_fields1156[1]
        if not len(field1158) == 0:
            self.newline()
            for i1160, elem1159 in enumerate(field1158):
                if (i1160 > 0):
                    self.newline()
                self.pretty_term(elem1159)
        self.dedent()
        self.write(")")
        return None

    def pretty_pragma(self, msg: logic_pb2.Pragma) -> None:
        _flat = self._try_flat(msg, self.pretty_pragma)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1702(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t1703 = _t1702(msg)
        fields1161 = _t1703
        assert fields1161 is not None
        unwrapped_fields1162 = fields1161
        self.write("(")
        self.write("pragma")
        self.indent_sexp()
        self.newline()
        field1163 = unwrapped_fields1162[0]
        self.pretty_name(field1163)
        field1164 = unwrapped_fields1162[1]
        if not len(field1164) == 0:
            self.newline()
            for i1166, elem1165 in enumerate(field1164):
                if (i1166 > 0):
                    self.newline()
                self.pretty_term(elem1165)
        self.dedent()
        self.write(")")
        return None

    def pretty_primitive(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_primitive)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1704(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1705 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1705 = None
            return _t1705
        _t1706 = _t1704(msg)
        guard_result1181 = _t1706
        if guard_result1181 is not None:
            self.pretty_eq(msg)
        else:
            def _t1707(_dollar_dollar):
                if _dollar_dollar.name == "rel_primitive_lt_monotype":
                    _t1708 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                else:
                    _t1708 = None
                return _t1708
            _t1709 = _t1707(msg)
            guard_result1180 = _t1709
            if guard_result1180 is not None:
                self.pretty_lt(msg)
            else:
                def _t1710(_dollar_dollar):
                    if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                        _t1711 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                    else:
                        _t1711 = None
                    return _t1711
                _t1712 = _t1710(msg)
                guard_result1179 = _t1712
                if guard_result1179 is not None:
                    self.pretty_lt_eq(msg)
                else:
                    def _t1713(_dollar_dollar):
                        if _dollar_dollar.name == "rel_primitive_gt_monotype":
                            _t1714 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                        else:
                            _t1714 = None
                        return _t1714
                    _t1715 = _t1713(msg)
                    guard_result1178 = _t1715
                    if guard_result1178 is not None:
                        self.pretty_gt(msg)
                    else:
                        def _t1716(_dollar_dollar):
                            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                                _t1717 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
                            else:
                                _t1717 = None
                            return _t1717
                        _t1718 = _t1716(msg)
                        guard_result1177 = _t1718
                        if guard_result1177 is not None:
                            self.pretty_gt_eq(msg)
                        else:
                            def _t1719(_dollar_dollar):
                                if _dollar_dollar.name == "rel_primitive_add_monotype":
                                    _t1720 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                else:
                                    _t1720 = None
                                return _t1720
                            _t1721 = _t1719(msg)
                            guard_result1176 = _t1721
                            if guard_result1176 is not None:
                                self.pretty_add(msg)
                            else:
                                def _t1722(_dollar_dollar):
                                    if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                                        _t1723 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                    else:
                                        _t1723 = None
                                    return _t1723
                                _t1724 = _t1722(msg)
                                guard_result1175 = _t1724
                                if guard_result1175 is not None:
                                    self.pretty_minus(msg)
                                else:
                                    def _t1725(_dollar_dollar):
                                        if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                                            _t1726 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                        else:
                                            _t1726 = None
                                        return _t1726
                                    _t1727 = _t1725(msg)
                                    guard_result1174 = _t1727
                                    if guard_result1174 is not None:
                                        self.pretty_multiply(msg)
                                    else:
                                        def _t1728(_dollar_dollar):
                                            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                                                _t1729 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
                                            else:
                                                _t1729 = None
                                            return _t1729
                                        _t1730 = _t1728(msg)
                                        guard_result1173 = _t1730
                                        if guard_result1173 is not None:
                                            self.pretty_divide(msg)
                                        else:
                                            def _t1731(_dollar_dollar):
                                                return (_dollar_dollar.name, _dollar_dollar.terms,)
                                            _t1732 = _t1731(msg)
                                            fields1167 = _t1732
                                            assert fields1167 is not None
                                            unwrapped_fields1168 = fields1167
                                            self.write("(")
                                            self.write("primitive")
                                            self.indent_sexp()
                                            self.newline()
                                            field1169 = unwrapped_fields1168[0]
                                            self.pretty_name(field1169)
                                            field1170 = unwrapped_fields1168[1]
                                            if not len(field1170) == 0:
                                                self.newline()
                                                for i1172, elem1171 in enumerate(field1170):
                                                    if (i1172 > 0):
                                                        self.newline()
                                                    self.pretty_rel_term(elem1171)
                                            self.dedent()
                                            self.write(")")
        return None

    def pretty_eq(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_eq)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1733(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_eq":
                _t1734 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1734 = None
            return _t1734
        _t1735 = _t1733(msg)
        fields1182 = _t1735
        assert fields1182 is not None
        unwrapped_fields1183 = fields1182
        self.write("(")
        self.write("=")
        self.indent_sexp()
        self.newline()
        field1184 = unwrapped_fields1183[0]
        self.pretty_term(field1184)
        self.newline()
        field1185 = unwrapped_fields1183[1]
        self.pretty_term(field1185)
        self.dedent()
        self.write(")")
        return None

    def pretty_lt(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_lt)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1736(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_lt_monotype":
                _t1737 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1737 = None
            return _t1737
        _t1738 = _t1736(msg)
        fields1186 = _t1738
        assert fields1186 is not None
        unwrapped_fields1187 = fields1186
        self.write("(")
        self.write("<")
        self.indent_sexp()
        self.newline()
        field1188 = unwrapped_fields1187[0]
        self.pretty_term(field1188)
        self.newline()
        field1189 = unwrapped_fields1187[1]
        self.pretty_term(field1189)
        self.dedent()
        self.write(")")
        return None

    def pretty_lt_eq(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_lt_eq)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1739(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_lt_eq_monotype":
                _t1740 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1740 = None
            return _t1740
        _t1741 = _t1739(msg)
        fields1190 = _t1741
        assert fields1190 is not None
        unwrapped_fields1191 = fields1190
        self.write("(")
        self.write("<=")
        self.indent_sexp()
        self.newline()
        field1192 = unwrapped_fields1191[0]
        self.pretty_term(field1192)
        self.newline()
        field1193 = unwrapped_fields1191[1]
        self.pretty_term(field1193)
        self.dedent()
        self.write(")")
        return None

    def pretty_gt(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_gt)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1742(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_gt_monotype":
                _t1743 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1743 = None
            return _t1743
        _t1744 = _t1742(msg)
        fields1194 = _t1744
        assert fields1194 is not None
        unwrapped_fields1195 = fields1194
        self.write("(")
        self.write(">")
        self.indent_sexp()
        self.newline()
        field1196 = unwrapped_fields1195[0]
        self.pretty_term(field1196)
        self.newline()
        field1197 = unwrapped_fields1195[1]
        self.pretty_term(field1197)
        self.dedent()
        self.write(")")
        return None

    def pretty_gt_eq(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_gt_eq)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1745(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_gt_eq_monotype":
                _t1746 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term,)
            else:
                _t1746 = None
            return _t1746
        _t1747 = _t1745(msg)
        fields1198 = _t1747
        assert fields1198 is not None
        unwrapped_fields1199 = fields1198
        self.write("(")
        self.write(">=")
        self.indent_sexp()
        self.newline()
        field1200 = unwrapped_fields1199[0]
        self.pretty_term(field1200)
        self.newline()
        field1201 = unwrapped_fields1199[1]
        self.pretty_term(field1201)
        self.dedent()
        self.write(")")
        return None

    def pretty_add(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_add)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1748(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_add_monotype":
                _t1749 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1749 = None
            return _t1749
        _t1750 = _t1748(msg)
        fields1202 = _t1750
        assert fields1202 is not None
        unwrapped_fields1203 = fields1202
        self.write("(")
        self.write("+")
        self.indent_sexp()
        self.newline()
        field1204 = unwrapped_fields1203[0]
        self.pretty_term(field1204)
        self.newline()
        field1205 = unwrapped_fields1203[1]
        self.pretty_term(field1205)
        self.newline()
        field1206 = unwrapped_fields1203[2]
        self.pretty_term(field1206)
        self.dedent()
        self.write(")")
        return None

    def pretty_minus(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_minus)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1751(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_subtract_monotype":
                _t1752 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1752 = None
            return _t1752
        _t1753 = _t1751(msg)
        fields1207 = _t1753
        assert fields1207 is not None
        unwrapped_fields1208 = fields1207
        self.write("(")
        self.write("-")
        self.indent_sexp()
        self.newline()
        field1209 = unwrapped_fields1208[0]
        self.pretty_term(field1209)
        self.newline()
        field1210 = unwrapped_fields1208[1]
        self.pretty_term(field1210)
        self.newline()
        field1211 = unwrapped_fields1208[2]
        self.pretty_term(field1211)
        self.dedent()
        self.write(")")
        return None

    def pretty_multiply(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_multiply)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1754(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_multiply_monotype":
                _t1755 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1755 = None
            return _t1755
        _t1756 = _t1754(msg)
        fields1212 = _t1756
        assert fields1212 is not None
        unwrapped_fields1213 = fields1212
        self.write("(")
        self.write("*")
        self.indent_sexp()
        self.newline()
        field1214 = unwrapped_fields1213[0]
        self.pretty_term(field1214)
        self.newline()
        field1215 = unwrapped_fields1213[1]
        self.pretty_term(field1215)
        self.newline()
        field1216 = unwrapped_fields1213[2]
        self.pretty_term(field1216)
        self.dedent()
        self.write(")")
        return None

    def pretty_divide(self, msg: logic_pb2.Primitive) -> None:
        _flat = self._try_flat(msg, self.pretty_divide)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1757(_dollar_dollar):
            if _dollar_dollar.name == "rel_primitive_divide_monotype":
                _t1758 = (_dollar_dollar.terms[0].term, _dollar_dollar.terms[1].term, _dollar_dollar.terms[2].term,)
            else:
                _t1758 = None
            return _t1758
        _t1759 = _t1757(msg)
        fields1217 = _t1759
        assert fields1217 is not None
        unwrapped_fields1218 = fields1217
        self.write("(")
        self.write("/")
        self.indent_sexp()
        self.newline()
        field1219 = unwrapped_fields1218[0]
        self.pretty_term(field1219)
        self.newline()
        field1220 = unwrapped_fields1218[1]
        self.pretty_term(field1220)
        self.newline()
        field1221 = unwrapped_fields1218[2]
        self.pretty_term(field1221)
        self.dedent()
        self.write(")")
        return None

    def pretty_rel_term(self, msg: logic_pb2.RelTerm) -> None:
        _flat = self._try_flat(msg, self.pretty_rel_term)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1760(_dollar_dollar):
            if _dollar_dollar.HasField("specialized_value"):
                _t1761 = _dollar_dollar.specialized_value
            else:
                _t1761 = None
            return _t1761
        _t1762 = _t1760(msg)
        deconstruct_result1224 = _t1762
        if deconstruct_result1224 is not None:
            assert deconstruct_result1224 is not None
            unwrapped1225 = deconstruct_result1224
            self.pretty_specialized_value(unwrapped1225)
        else:
            def _t1763(_dollar_dollar):
                if _dollar_dollar.HasField("term"):
                    _t1764 = _dollar_dollar.term
                else:
                    _t1764 = None
                return _t1764
            _t1765 = _t1763(msg)
            deconstruct_result1222 = _t1765
            if deconstruct_result1222 is not None:
                assert deconstruct_result1222 is not None
                unwrapped1223 = deconstruct_result1222
                self.pretty_term(unwrapped1223)
            else:
                raise ParseError("No matching rule for rel_term")
        return None

    def pretty_specialized_value(self, msg: logic_pb2.Value) -> None:
        _flat = self._try_flat(msg, self.pretty_specialized_value)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1766(_dollar_dollar):
            return _dollar_dollar
        _t1767 = _t1766(msg)
        fields1226 = _t1767
        assert fields1226 is not None
        unwrapped_fields1227 = fields1226
        self.write("#")
        self.pretty_value(unwrapped_fields1227)
        return None

    def pretty_rel_atom(self, msg: logic_pb2.RelAtom) -> None:
        _flat = self._try_flat(msg, self.pretty_rel_atom)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1768(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.terms,)
        _t1769 = _t1768(msg)
        fields1228 = _t1769
        assert fields1228 is not None
        unwrapped_fields1229 = fields1228
        self.write("(")
        self.write("relatom")
        self.indent_sexp()
        self.newline()
        field1230 = unwrapped_fields1229[0]
        self.pretty_name(field1230)
        field1231 = unwrapped_fields1229[1]
        if not len(field1231) == 0:
            self.newline()
            for i1233, elem1232 in enumerate(field1231):
                if (i1233 > 0):
                    self.newline()
                self.pretty_rel_term(elem1232)
        self.dedent()
        self.write(")")
        return None

    def pretty_cast(self, msg: logic_pb2.Cast) -> None:
        _flat = self._try_flat(msg, self.pretty_cast)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1770(_dollar_dollar):
            return (_dollar_dollar.input, _dollar_dollar.result,)
        _t1771 = _t1770(msg)
        fields1234 = _t1771
        assert fields1234 is not None
        unwrapped_fields1235 = fields1234
        self.write("(")
        self.write("cast")
        self.indent_sexp()
        self.newline()
        field1236 = unwrapped_fields1235[0]
        self.pretty_term(field1236)
        self.newline()
        field1237 = unwrapped_fields1235[1]
        self.pretty_term(field1237)
        self.dedent()
        self.write(")")
        return None

    def pretty_attrs(self, msg: Sequence[logic_pb2.Attribute]) -> None:
        _flat = self._try_flat(msg, self.pretty_attrs)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1772(_dollar_dollar):
            return _dollar_dollar
        _t1773 = _t1772(msg)
        fields1238 = _t1773
        assert fields1238 is not None
        unwrapped_fields1239 = fields1238
        self.write("(")
        self.write("attrs")
        self.indent_sexp()
        if not len(unwrapped_fields1239) == 0:
            self.newline()
            for i1241, elem1240 in enumerate(unwrapped_fields1239):
                if (i1241 > 0):
                    self.newline()
                self.pretty_attribute(elem1240)
        self.dedent()
        self.write(")")
        return None

    def pretty_attribute(self, msg: logic_pb2.Attribute) -> None:
        _flat = self._try_flat(msg, self.pretty_attribute)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1774(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.args,)
        _t1775 = _t1774(msg)
        fields1242 = _t1775
        assert fields1242 is not None
        unwrapped_fields1243 = fields1242
        self.write("(")
        self.write("attribute")
        self.indent_sexp()
        self.newline()
        field1244 = unwrapped_fields1243[0]
        self.pretty_name(field1244)
        field1245 = unwrapped_fields1243[1]
        if not len(field1245) == 0:
            self.newline()
            for i1247, elem1246 in enumerate(field1245):
                if (i1247 > 0):
                    self.newline()
                self.pretty_value(elem1246)
        self.dedent()
        self.write(")")
        return None

    def pretty_algorithm(self, msg: logic_pb2.Algorithm) -> None:
        _flat = self._try_flat(msg, self.pretty_algorithm)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1776(_dollar_dollar):
            return (getattr(_dollar_dollar, 'global'), _dollar_dollar.body,)
        _t1777 = _t1776(msg)
        fields1248 = _t1777
        assert fields1248 is not None
        unwrapped_fields1249 = fields1248
        self.write("(")
        self.write("algorithm")
        self.indent_sexp()
        field1250 = unwrapped_fields1249[0]
        if not len(field1250) == 0:
            self.newline()
            for i1252, elem1251 in enumerate(field1250):
                if (i1252 > 0):
                    self.newline()
                self.pretty_relation_id(elem1251)
        self.newline()
        field1253 = unwrapped_fields1249[1]
        self.pretty_script(field1253)
        self.dedent()
        self.write(")")
        return None

    def pretty_script(self, msg: logic_pb2.Script) -> None:
        _flat = self._try_flat(msg, self.pretty_script)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1778(_dollar_dollar):
            return _dollar_dollar.constructs
        _t1779 = _t1778(msg)
        fields1254 = _t1779
        assert fields1254 is not None
        unwrapped_fields1255 = fields1254
        self.write("(")
        self.write("script")
        self.indent_sexp()
        if not len(unwrapped_fields1255) == 0:
            self.newline()
            for i1257, elem1256 in enumerate(unwrapped_fields1255):
                if (i1257 > 0):
                    self.newline()
                self.pretty_construct(elem1256)
        self.dedent()
        self.write(")")
        return None

    def pretty_construct(self, msg: logic_pb2.Construct) -> None:
        _flat = self._try_flat(msg, self.pretty_construct)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1780(_dollar_dollar):
            if _dollar_dollar.HasField("loop"):
                _t1781 = _dollar_dollar.loop
            else:
                _t1781 = None
            return _t1781
        _t1782 = _t1780(msg)
        deconstruct_result1260 = _t1782
        if deconstruct_result1260 is not None:
            assert deconstruct_result1260 is not None
            unwrapped1261 = deconstruct_result1260
            self.pretty_loop(unwrapped1261)
        else:
            def _t1783(_dollar_dollar):
                if _dollar_dollar.HasField("instruction"):
                    _t1784 = _dollar_dollar.instruction
                else:
                    _t1784 = None
                return _t1784
            _t1785 = _t1783(msg)
            deconstruct_result1258 = _t1785
            if deconstruct_result1258 is not None:
                assert deconstruct_result1258 is not None
                unwrapped1259 = deconstruct_result1258
                self.pretty_instruction(unwrapped1259)
            else:
                raise ParseError("No matching rule for construct")
        return None

    def pretty_loop(self, msg: logic_pb2.Loop) -> None:
        _flat = self._try_flat(msg, self.pretty_loop)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1786(_dollar_dollar):
            return (_dollar_dollar.init, _dollar_dollar.body,)
        _t1787 = _t1786(msg)
        fields1262 = _t1787
        assert fields1262 is not None
        unwrapped_fields1263 = fields1262
        self.write("(")
        self.write("loop")
        self.indent_sexp()
        self.newline()
        field1264 = unwrapped_fields1263[0]
        self.pretty_init(field1264)
        self.newline()
        field1265 = unwrapped_fields1263[1]
        self.pretty_script(field1265)
        self.dedent()
        self.write(")")
        return None

    def pretty_init(self, msg: Sequence[logic_pb2.Instruction]) -> None:
        _flat = self._try_flat(msg, self.pretty_init)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1788(_dollar_dollar):
            return _dollar_dollar
        _t1789 = _t1788(msg)
        fields1266 = _t1789
        assert fields1266 is not None
        unwrapped_fields1267 = fields1266
        self.write("(")
        self.write("init")
        self.indent_sexp()
        if not len(unwrapped_fields1267) == 0:
            self.newline()
            for i1269, elem1268 in enumerate(unwrapped_fields1267):
                if (i1269 > 0):
                    self.newline()
                self.pretty_instruction(elem1268)
        self.dedent()
        self.write(")")
        return None

    def pretty_instruction(self, msg: logic_pb2.Instruction) -> None:
        _flat = self._try_flat(msg, self.pretty_instruction)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1790(_dollar_dollar):
            if _dollar_dollar.HasField("assign"):
                _t1791 = _dollar_dollar.assign
            else:
                _t1791 = None
            return _t1791
        _t1792 = _t1790(msg)
        deconstruct_result1278 = _t1792
        if deconstruct_result1278 is not None:
            assert deconstruct_result1278 is not None
            unwrapped1279 = deconstruct_result1278
            self.pretty_assign(unwrapped1279)
        else:
            def _t1793(_dollar_dollar):
                if _dollar_dollar.HasField("upsert"):
                    _t1794 = _dollar_dollar.upsert
                else:
                    _t1794 = None
                return _t1794
            _t1795 = _t1793(msg)
            deconstruct_result1276 = _t1795
            if deconstruct_result1276 is not None:
                assert deconstruct_result1276 is not None
                unwrapped1277 = deconstruct_result1276
                self.pretty_upsert(unwrapped1277)
            else:
                def _t1796(_dollar_dollar):
                    if _dollar_dollar.HasField("break"):
                        _t1797 = getattr(_dollar_dollar, 'break')
                    else:
                        _t1797 = None
                    return _t1797
                _t1798 = _t1796(msg)
                deconstruct_result1274 = _t1798
                if deconstruct_result1274 is not None:
                    assert deconstruct_result1274 is not None
                    unwrapped1275 = deconstruct_result1274
                    self.pretty_break(unwrapped1275)
                else:
                    def _t1799(_dollar_dollar):
                        if _dollar_dollar.HasField("monoid_def"):
                            _t1800 = _dollar_dollar.monoid_def
                        else:
                            _t1800 = None
                        return _t1800
                    _t1801 = _t1799(msg)
                    deconstruct_result1272 = _t1801
                    if deconstruct_result1272 is not None:
                        assert deconstruct_result1272 is not None
                        unwrapped1273 = deconstruct_result1272
                        self.pretty_monoid_def(unwrapped1273)
                    else:
                        def _t1802(_dollar_dollar):
                            if _dollar_dollar.HasField("monus_def"):
                                _t1803 = _dollar_dollar.monus_def
                            else:
                                _t1803 = None
                            return _t1803
                        _t1804 = _t1802(msg)
                        deconstruct_result1270 = _t1804
                        if deconstruct_result1270 is not None:
                            assert deconstruct_result1270 is not None
                            unwrapped1271 = deconstruct_result1270
                            self.pretty_monus_def(unwrapped1271)
                        else:
                            raise ParseError("No matching rule for instruction")
        return None

    def pretty_assign(self, msg: logic_pb2.Assign) -> None:
        _flat = self._try_flat(msg, self.pretty_assign)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1805(_dollar_dollar):
            if not len(_dollar_dollar.attrs) == 0:
                _t1806 = _dollar_dollar.attrs
            else:
                _t1806 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1806,)
        _t1807 = _t1805(msg)
        fields1280 = _t1807
        assert fields1280 is not None
        unwrapped_fields1281 = fields1280
        self.write("(")
        self.write("assign")
        self.indent_sexp()
        self.newline()
        field1282 = unwrapped_fields1281[0]
        self.pretty_relation_id(field1282)
        self.newline()
        field1283 = unwrapped_fields1281[1]
        self.pretty_abstraction(field1283)
        field1284 = unwrapped_fields1281[2]
        if field1284 is not None:
            self.newline()
            assert field1284 is not None
            opt_val1285 = field1284
            self.pretty_attrs(opt_val1285)
        self.dedent()
        self.write(")")
        return None

    def pretty_upsert(self, msg: logic_pb2.Upsert) -> None:
        _flat = self._try_flat(msg, self.pretty_upsert)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1808(_dollar_dollar):
            if not len(_dollar_dollar.attrs) == 0:
                _t1809 = _dollar_dollar.attrs
            else:
                _t1809 = None
            return (_dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1809,)
        _t1810 = _t1808(msg)
        fields1286 = _t1810
        assert fields1286 is not None
        unwrapped_fields1287 = fields1286
        self.write("(")
        self.write("upsert")
        self.indent_sexp()
        self.newline()
        field1288 = unwrapped_fields1287[0]
        self.pretty_relation_id(field1288)
        self.newline()
        field1289 = unwrapped_fields1287[1]
        self.pretty_abstraction_with_arity(field1289)
        field1290 = unwrapped_fields1287[2]
        if field1290 is not None:
            self.newline()
            assert field1290 is not None
            opt_val1291 = field1290
            self.pretty_attrs(opt_val1291)
        self.dedent()
        self.write(")")
        return None

    def pretty_abstraction_with_arity(self, msg: tuple[logic_pb2.Abstraction, int]) -> None:
        _flat = self._try_flat(msg, self.pretty_abstraction_with_arity)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1811(_dollar_dollar):
            _t1812 = self.deconstruct_bindings_with_arity(_dollar_dollar[0], _dollar_dollar[1])
            return (_t1812, _dollar_dollar[0].value,)
        _t1813 = _t1811(msg)
        fields1292 = _t1813
        assert fields1292 is not None
        unwrapped_fields1293 = fields1292
        self.write("(")
        self.indent()
        field1294 = unwrapped_fields1293[0]
        self.pretty_bindings(field1294)
        self.newline()
        field1295 = unwrapped_fields1293[1]
        self.pretty_formula(field1295)
        self.dedent()
        self.write(")")
        return None

    def pretty_break(self, msg: logic_pb2.Break) -> None:
        _flat = self._try_flat(msg, self.pretty_break)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1814(_dollar_dollar):
            if not len(_dollar_dollar.attrs) == 0:
                _t1815 = _dollar_dollar.attrs
            else:
                _t1815 = None
            return (_dollar_dollar.name, _dollar_dollar.body, _t1815,)
        _t1816 = _t1814(msg)
        fields1296 = _t1816
        assert fields1296 is not None
        unwrapped_fields1297 = fields1296
        self.write("(")
        self.write("break")
        self.indent_sexp()
        self.newline()
        field1298 = unwrapped_fields1297[0]
        self.pretty_relation_id(field1298)
        self.newline()
        field1299 = unwrapped_fields1297[1]
        self.pretty_abstraction(field1299)
        field1300 = unwrapped_fields1297[2]
        if field1300 is not None:
            self.newline()
            assert field1300 is not None
            opt_val1301 = field1300
            self.pretty_attrs(opt_val1301)
        self.dedent()
        self.write(")")
        return None

    def pretty_monoid_def(self, msg: logic_pb2.MonoidDef) -> None:
        _flat = self._try_flat(msg, self.pretty_monoid_def)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1817(_dollar_dollar):
            if not len(_dollar_dollar.attrs) == 0:
                _t1818 = _dollar_dollar.attrs
            else:
                _t1818 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1818,)
        _t1819 = _t1817(msg)
        fields1302 = _t1819
        assert fields1302 is not None
        unwrapped_fields1303 = fields1302
        self.write("(")
        self.write("monoid")
        self.indent_sexp()
        self.newline()
        field1304 = unwrapped_fields1303[0]
        self.pretty_monoid(field1304)
        self.newline()
        field1305 = unwrapped_fields1303[1]
        self.pretty_relation_id(field1305)
        self.newline()
        field1306 = unwrapped_fields1303[2]
        self.pretty_abstraction_with_arity(field1306)
        field1307 = unwrapped_fields1303[3]
        if field1307 is not None:
            self.newline()
            assert field1307 is not None
            opt_val1308 = field1307
            self.pretty_attrs(opt_val1308)
        self.dedent()
        self.write(")")
        return None

    def pretty_monoid(self, msg: logic_pb2.Monoid) -> None:
        _flat = self._try_flat(msg, self.pretty_monoid)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1820(_dollar_dollar):
            if _dollar_dollar.HasField("or_monoid"):
                _t1821 = _dollar_dollar.or_monoid
            else:
                _t1821 = None
            return _t1821
        _t1822 = _t1820(msg)
        deconstruct_result1315 = _t1822
        if deconstruct_result1315 is not None:
            assert deconstruct_result1315 is not None
            unwrapped1316 = deconstruct_result1315
            self.pretty_or_monoid(unwrapped1316)
        else:
            def _t1823(_dollar_dollar):
                if _dollar_dollar.HasField("min_monoid"):
                    _t1824 = _dollar_dollar.min_monoid
                else:
                    _t1824 = None
                return _t1824
            _t1825 = _t1823(msg)
            deconstruct_result1313 = _t1825
            if deconstruct_result1313 is not None:
                assert deconstruct_result1313 is not None
                unwrapped1314 = deconstruct_result1313
                self.pretty_min_monoid(unwrapped1314)
            else:
                def _t1826(_dollar_dollar):
                    if _dollar_dollar.HasField("max_monoid"):
                        _t1827 = _dollar_dollar.max_monoid
                    else:
                        _t1827 = None
                    return _t1827
                _t1828 = _t1826(msg)
                deconstruct_result1311 = _t1828
                if deconstruct_result1311 is not None:
                    assert deconstruct_result1311 is not None
                    unwrapped1312 = deconstruct_result1311
                    self.pretty_max_monoid(unwrapped1312)
                else:
                    def _t1829(_dollar_dollar):
                        if _dollar_dollar.HasField("sum_monoid"):
                            _t1830 = _dollar_dollar.sum_monoid
                        else:
                            _t1830 = None
                        return _t1830
                    _t1831 = _t1829(msg)
                    deconstruct_result1309 = _t1831
                    if deconstruct_result1309 is not None:
                        assert deconstruct_result1309 is not None
                        unwrapped1310 = deconstruct_result1309
                        self.pretty_sum_monoid(unwrapped1310)
                    else:
                        raise ParseError("No matching rule for monoid")
        return None

    def pretty_or_monoid(self, msg: logic_pb2.OrMonoid) -> None:
        _flat = self._try_flat(msg, self.pretty_or_monoid)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1832(_dollar_dollar):
            return _dollar_dollar
        _t1833 = _t1832(msg)
        fields1317 = _t1833
        assert fields1317 is not None
        unwrapped_fields1318 = fields1317
        self.write("(")
        self.write("or")
        self.write(")")
        return None

    def pretty_min_monoid(self, msg: logic_pb2.MinMonoid) -> None:
        _flat = self._try_flat(msg, self.pretty_min_monoid)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1834(_dollar_dollar):
            return _dollar_dollar.type
        _t1835 = _t1834(msg)
        fields1319 = _t1835
        assert fields1319 is not None
        unwrapped_fields1320 = fields1319
        self.write("(")
        self.write("min")
        self.indent_sexp()
        self.newline()
        self.pretty_type(unwrapped_fields1320)
        self.dedent()
        self.write(")")
        return None

    def pretty_max_monoid(self, msg: logic_pb2.MaxMonoid) -> None:
        _flat = self._try_flat(msg, self.pretty_max_monoid)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1836(_dollar_dollar):
            return _dollar_dollar.type
        _t1837 = _t1836(msg)
        fields1321 = _t1837
        assert fields1321 is not None
        unwrapped_fields1322 = fields1321
        self.write("(")
        self.write("max")
        self.indent_sexp()
        self.newline()
        self.pretty_type(unwrapped_fields1322)
        self.dedent()
        self.write(")")
        return None

    def pretty_sum_monoid(self, msg: logic_pb2.SumMonoid) -> None:
        _flat = self._try_flat(msg, self.pretty_sum_monoid)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1838(_dollar_dollar):
            return _dollar_dollar.type
        _t1839 = _t1838(msg)
        fields1323 = _t1839
        assert fields1323 is not None
        unwrapped_fields1324 = fields1323
        self.write("(")
        self.write("sum")
        self.indent_sexp()
        self.newline()
        self.pretty_type(unwrapped_fields1324)
        self.dedent()
        self.write(")")
        return None

    def pretty_monus_def(self, msg: logic_pb2.MonusDef) -> None:
        _flat = self._try_flat(msg, self.pretty_monus_def)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1840(_dollar_dollar):
            if not len(_dollar_dollar.attrs) == 0:
                _t1841 = _dollar_dollar.attrs
            else:
                _t1841 = None
            return (_dollar_dollar.monoid, _dollar_dollar.name, (_dollar_dollar.body, _dollar_dollar.value_arity,), _t1841,)
        _t1842 = _t1840(msg)
        fields1325 = _t1842
        assert fields1325 is not None
        unwrapped_fields1326 = fields1325
        self.write("(")
        self.write("monus")
        self.indent_sexp()
        self.newline()
        field1327 = unwrapped_fields1326[0]
        self.pretty_monoid(field1327)
        self.newline()
        field1328 = unwrapped_fields1326[1]
        self.pretty_relation_id(field1328)
        self.newline()
        field1329 = unwrapped_fields1326[2]
        self.pretty_abstraction_with_arity(field1329)
        field1330 = unwrapped_fields1326[3]
        if field1330 is not None:
            self.newline()
            assert field1330 is not None
            opt_val1331 = field1330
            self.pretty_attrs(opt_val1331)
        self.dedent()
        self.write(")")
        return None

    def pretty_constraint(self, msg: logic_pb2.Constraint) -> None:
        _flat = self._try_flat(msg, self.pretty_constraint)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1843(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.functional_dependency.guard, _dollar_dollar.functional_dependency.keys, _dollar_dollar.functional_dependency.values,)
        _t1844 = _t1843(msg)
        fields1332 = _t1844
        assert fields1332 is not None
        unwrapped_fields1333 = fields1332
        self.write("(")
        self.write("functional_dependency")
        self.indent_sexp()
        self.newline()
        field1334 = unwrapped_fields1333[0]
        self.pretty_relation_id(field1334)
        self.newline()
        field1335 = unwrapped_fields1333[1]
        self.pretty_abstraction(field1335)
        self.newline()
        field1336 = unwrapped_fields1333[2]
        self.pretty_functional_dependency_keys(field1336)
        self.newline()
        field1337 = unwrapped_fields1333[3]
        self.pretty_functional_dependency_values(field1337)
        self.dedent()
        self.write(")")
        return None

    def pretty_functional_dependency_keys(self, msg: Sequence[logic_pb2.Var]) -> None:
        _flat = self._try_flat(msg, self.pretty_functional_dependency_keys)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1845(_dollar_dollar):
            return _dollar_dollar
        _t1846 = _t1845(msg)
        fields1338 = _t1846
        assert fields1338 is not None
        unwrapped_fields1339 = fields1338
        self.write("(")
        self.write("keys")
        self.indent_sexp()
        if not len(unwrapped_fields1339) == 0:
            self.newline()
            for i1341, elem1340 in enumerate(unwrapped_fields1339):
                if (i1341 > 0):
                    self.newline()
                self.pretty_var(elem1340)
        self.dedent()
        self.write(")")
        return None

    def pretty_functional_dependency_values(self, msg: Sequence[logic_pb2.Var]) -> None:
        _flat = self._try_flat(msg, self.pretty_functional_dependency_values)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1847(_dollar_dollar):
            return _dollar_dollar
        _t1848 = _t1847(msg)
        fields1342 = _t1848
        assert fields1342 is not None
        unwrapped_fields1343 = fields1342
        self.write("(")
        self.write("values")
        self.indent_sexp()
        if not len(unwrapped_fields1343) == 0:
            self.newline()
            for i1345, elem1344 in enumerate(unwrapped_fields1343):
                if (i1345 > 0):
                    self.newline()
                self.pretty_var(elem1344)
        self.dedent()
        self.write(")")
        return None

    def pretty_data(self, msg: logic_pb2.Data) -> None:
        _flat = self._try_flat(msg, self.pretty_data)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1849(_dollar_dollar):
            if _dollar_dollar.HasField("rel_edb"):
                _t1850 = _dollar_dollar.rel_edb
            else:
                _t1850 = None
            return _t1850
        _t1851 = _t1849(msg)
        deconstruct_result1350 = _t1851
        if deconstruct_result1350 is not None:
            assert deconstruct_result1350 is not None
            unwrapped1351 = deconstruct_result1350
            self.pretty_rel_edb(unwrapped1351)
        else:
            def _t1852(_dollar_dollar):
                if _dollar_dollar.HasField("betree_relation"):
                    _t1853 = _dollar_dollar.betree_relation
                else:
                    _t1853 = None
                return _t1853
            _t1854 = _t1852(msg)
            deconstruct_result1348 = _t1854
            if deconstruct_result1348 is not None:
                assert deconstruct_result1348 is not None
                unwrapped1349 = deconstruct_result1348
                self.pretty_betree_relation(unwrapped1349)
            else:
                def _t1855(_dollar_dollar):
                    if _dollar_dollar.HasField("csv_data"):
                        _t1856 = _dollar_dollar.csv_data
                    else:
                        _t1856 = None
                    return _t1856
                _t1857 = _t1855(msg)
                deconstruct_result1346 = _t1857
                if deconstruct_result1346 is not None:
                    assert deconstruct_result1346 is not None
                    unwrapped1347 = deconstruct_result1346
                    self.pretty_csv_data(unwrapped1347)
                else:
                    raise ParseError("No matching rule for data")
        return None

    def pretty_rel_edb(self, msg: logic_pb2.RelEDB) -> None:
        _flat = self._try_flat(msg, self.pretty_rel_edb)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1858(_dollar_dollar):
            return (_dollar_dollar.target_id, _dollar_dollar.path, _dollar_dollar.types,)
        _t1859 = _t1858(msg)
        fields1352 = _t1859
        assert fields1352 is not None
        unwrapped_fields1353 = fields1352
        self.write("(")
        self.write("rel_edb")
        self.indent_sexp()
        self.newline()
        field1354 = unwrapped_fields1353[0]
        self.pretty_relation_id(field1354)
        self.newline()
        field1355 = unwrapped_fields1353[1]
        self.pretty_rel_edb_path(field1355)
        self.newline()
        field1356 = unwrapped_fields1353[2]
        self.pretty_rel_edb_types(field1356)
        self.dedent()
        self.write(")")
        return None

    def pretty_rel_edb_path(self, msg: Sequence[str]) -> None:
        _flat = self._try_flat(msg, self.pretty_rel_edb_path)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1860(_dollar_dollar):
            return _dollar_dollar
        _t1861 = _t1860(msg)
        fields1357 = _t1861
        assert fields1357 is not None
        unwrapped_fields1358 = fields1357
        self.write("[")
        self.indent()
        for i1360, elem1359 in enumerate(unwrapped_fields1358):
            if (i1360 > 0):
                self.newline()
            self.write(self.format_string_value(elem1359))
        self.dedent()
        self.write("]")
        return None

    def pretty_rel_edb_types(self, msg: Sequence[logic_pb2.Type]) -> None:
        _flat = self._try_flat(msg, self.pretty_rel_edb_types)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1862(_dollar_dollar):
            return _dollar_dollar
        _t1863 = _t1862(msg)
        fields1361 = _t1863
        assert fields1361 is not None
        unwrapped_fields1362 = fields1361
        self.write("[")
        self.indent()
        for i1364, elem1363 in enumerate(unwrapped_fields1362):
            if (i1364 > 0):
                self.newline()
            self.pretty_type(elem1363)
        self.dedent()
        self.write("]")
        return None

    def pretty_betree_relation(self, msg: logic_pb2.BeTreeRelation) -> None:
        _flat = self._try_flat(msg, self.pretty_betree_relation)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1864(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_info,)
        _t1865 = _t1864(msg)
        fields1365 = _t1865
        assert fields1365 is not None
        unwrapped_fields1366 = fields1365
        self.write("(")
        self.write("betree_relation")
        self.indent_sexp()
        self.newline()
        field1367 = unwrapped_fields1366[0]
        self.pretty_relation_id(field1367)
        self.newline()
        field1368 = unwrapped_fields1366[1]
        self.pretty_betree_info(field1368)
        self.dedent()
        self.write(")")
        return None

    def pretty_betree_info(self, msg: logic_pb2.BeTreeInfo) -> None:
        _flat = self._try_flat(msg, self.pretty_betree_info)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1866(_dollar_dollar):
            _t1867 = self.deconstruct_betree_info_config(_dollar_dollar)
            return (_dollar_dollar.key_types, _dollar_dollar.value_types, _t1867,)
        _t1868 = _t1866(msg)
        fields1369 = _t1868
        assert fields1369 is not None
        unwrapped_fields1370 = fields1369
        self.write("(")
        self.write("betree_info")
        self.indent_sexp()
        self.newline()
        field1371 = unwrapped_fields1370[0]
        self.pretty_betree_info_key_types(field1371)
        self.newline()
        field1372 = unwrapped_fields1370[1]
        self.pretty_betree_info_value_types(field1372)
        self.newline()
        field1373 = unwrapped_fields1370[2]
        self.pretty_config_dict(field1373)
        self.dedent()
        self.write(")")
        return None

    def pretty_betree_info_key_types(self, msg: Sequence[logic_pb2.Type]) -> None:
        _flat = self._try_flat(msg, self.pretty_betree_info_key_types)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1869(_dollar_dollar):
            return _dollar_dollar
        _t1870 = _t1869(msg)
        fields1374 = _t1870
        assert fields1374 is not None
        unwrapped_fields1375 = fields1374
        self.write("(")
        self.write("key_types")
        self.indent_sexp()
        if not len(unwrapped_fields1375) == 0:
            self.newline()
            for i1377, elem1376 in enumerate(unwrapped_fields1375):
                if (i1377 > 0):
                    self.newline()
                self.pretty_type(elem1376)
        self.dedent()
        self.write(")")
        return None

    def pretty_betree_info_value_types(self, msg: Sequence[logic_pb2.Type]) -> None:
        _flat = self._try_flat(msg, self.pretty_betree_info_value_types)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1871(_dollar_dollar):
            return _dollar_dollar
        _t1872 = _t1871(msg)
        fields1378 = _t1872
        assert fields1378 is not None
        unwrapped_fields1379 = fields1378
        self.write("(")
        self.write("value_types")
        self.indent_sexp()
        if not len(unwrapped_fields1379) == 0:
            self.newline()
            for i1381, elem1380 in enumerate(unwrapped_fields1379):
                if (i1381 > 0):
                    self.newline()
                self.pretty_type(elem1380)
        self.dedent()
        self.write(")")
        return None

    def pretty_csv_data(self, msg: logic_pb2.CSVData) -> None:
        _flat = self._try_flat(msg, self.pretty_csv_data)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1873(_dollar_dollar):
            return (_dollar_dollar.locator, _dollar_dollar.config, _dollar_dollar.columns, _dollar_dollar.asof,)
        _t1874 = _t1873(msg)
        fields1382 = _t1874
        assert fields1382 is not None
        unwrapped_fields1383 = fields1382
        self.write("(")
        self.write("csv_data")
        self.indent_sexp()
        self.newline()
        field1384 = unwrapped_fields1383[0]
        self.pretty_csvlocator(field1384)
        self.newline()
        field1385 = unwrapped_fields1383[1]
        self.pretty_csv_config(field1385)
        self.newline()
        field1386 = unwrapped_fields1383[2]
        self.pretty_csv_columns(field1386)
        self.newline()
        field1387 = unwrapped_fields1383[3]
        self.pretty_csv_asof(field1387)
        self.dedent()
        self.write(")")
        return None

    def pretty_csvlocator(self, msg: logic_pb2.CSVLocator) -> None:
        _flat = self._try_flat(msg, self.pretty_csvlocator)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1875(_dollar_dollar):
            if not len(_dollar_dollar.paths) == 0:
                _t1876 = _dollar_dollar.paths
            else:
                _t1876 = None
            if _dollar_dollar.inline_data.decode('utf-8') != "":
                _t1877 = _dollar_dollar.inline_data.decode('utf-8')
            else:
                _t1877 = None
            return (_t1876, _t1877,)
        _t1878 = _t1875(msg)
        fields1388 = _t1878
        assert fields1388 is not None
        unwrapped_fields1389 = fields1388
        self.write("(")
        self.write("csv_locator")
        self.indent_sexp()
        field1390 = unwrapped_fields1389[0]
        if field1390 is not None:
            self.newline()
            assert field1390 is not None
            opt_val1391 = field1390
            self.pretty_csv_locator_paths(opt_val1391)
        field1392 = unwrapped_fields1389[1]
        if field1392 is not None:
            self.newline()
            assert field1392 is not None
            opt_val1393 = field1392
            self.pretty_csv_locator_inline_data(opt_val1393)
        self.dedent()
        self.write(")")
        return None

    def pretty_csv_locator_paths(self, msg: Sequence[str]) -> None:
        _flat = self._try_flat(msg, self.pretty_csv_locator_paths)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1879(_dollar_dollar):
            return _dollar_dollar
        _t1880 = _t1879(msg)
        fields1394 = _t1880
        assert fields1394 is not None
        unwrapped_fields1395 = fields1394
        self.write("(")
        self.write("paths")
        self.indent_sexp()
        if not len(unwrapped_fields1395) == 0:
            self.newline()
            for i1397, elem1396 in enumerate(unwrapped_fields1395):
                if (i1397 > 0):
                    self.newline()
                self.write(self.format_string_value(elem1396))
        self.dedent()
        self.write(")")
        return None

    def pretty_csv_locator_inline_data(self, msg: str) -> None:
        _flat = self._try_flat(msg, self.pretty_csv_locator_inline_data)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1881(_dollar_dollar):
            return _dollar_dollar
        _t1882 = _t1881(msg)
        fields1398 = _t1882
        assert fields1398 is not None
        unwrapped_fields1399 = fields1398
        self.write("(")
        self.write("inline_data")
        self.indent_sexp()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields1399))
        self.dedent()
        self.write(")")
        return None

    def pretty_csv_config(self, msg: logic_pb2.CSVConfig) -> None:
        _flat = self._try_flat(msg, self.pretty_csv_config)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1883(_dollar_dollar):
            _t1884 = self.deconstruct_csv_config(_dollar_dollar)
            return _t1884
        _t1885 = _t1883(msg)
        fields1400 = _t1885
        assert fields1400 is not None
        unwrapped_fields1401 = fields1400
        self.write("(")
        self.write("csv_config")
        self.indent_sexp()
        self.newline()
        self.pretty_config_dict(unwrapped_fields1401)
        self.dedent()
        self.write(")")
        return None

    def pretty_csv_columns(self, msg: Sequence[logic_pb2.CSVColumn]) -> None:
        _flat = self._try_flat(msg, self.pretty_csv_columns)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1886(_dollar_dollar):
            return _dollar_dollar
        _t1887 = _t1886(msg)
        fields1402 = _t1887
        assert fields1402 is not None
        unwrapped_fields1403 = fields1402
        self.write("(")
        self.write("columns")
        self.indent_sexp()
        if not len(unwrapped_fields1403) == 0:
            self.newline()
            for i1405, elem1404 in enumerate(unwrapped_fields1403):
                if (i1405 > 0):
                    self.newline()
                self.pretty_csv_column(elem1404)
        self.dedent()
        self.write(")")
        return None

    def pretty_csv_column(self, msg: logic_pb2.CSVColumn) -> None:
        _flat = self._try_flat(msg, self.pretty_csv_column)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1888(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.target_id, _dollar_dollar.types,)
        _t1889 = _t1888(msg)
        fields1406 = _t1889
        assert fields1406 is not None
        unwrapped_fields1407 = fields1406
        self.write("(")
        self.write("column")
        self.indent_sexp()
        self.newline()
        field1408 = unwrapped_fields1407[0]
        self.write(self.format_string_value(field1408))
        self.newline()
        field1409 = unwrapped_fields1407[1]
        self.pretty_relation_id(field1409)
        self.newline()
        self.write("[")
        field1410 = unwrapped_fields1407[2]
        for i1412, elem1411 in enumerate(field1410):
            if (i1412 > 0):
                self.newline()
            self.pretty_type(elem1411)
        self.write("]")
        self.dedent()
        self.write(")")
        return None

    def pretty_csv_asof(self, msg: str) -> None:
        _flat = self._try_flat(msg, self.pretty_csv_asof)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1890(_dollar_dollar):
            return _dollar_dollar
        _t1891 = _t1890(msg)
        fields1413 = _t1891
        assert fields1413 is not None
        unwrapped_fields1414 = fields1413
        self.write("(")
        self.write("asof")
        self.indent_sexp()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields1414))
        self.dedent()
        self.write(")")
        return None

    def pretty_undefine(self, msg: transactions_pb2.Undefine) -> None:
        _flat = self._try_flat(msg, self.pretty_undefine)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1892(_dollar_dollar):
            return _dollar_dollar.fragment_id
        _t1893 = _t1892(msg)
        fields1415 = _t1893
        assert fields1415 is not None
        unwrapped_fields1416 = fields1415
        self.write("(")
        self.write("undefine")
        self.indent_sexp()
        self.newline()
        self.pretty_fragment_id(unwrapped_fields1416)
        self.dedent()
        self.write(")")
        return None

    def pretty_context(self, msg: transactions_pb2.Context) -> None:
        _flat = self._try_flat(msg, self.pretty_context)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1894(_dollar_dollar):
            return _dollar_dollar.relations
        _t1895 = _t1894(msg)
        fields1417 = _t1895
        assert fields1417 is not None
        unwrapped_fields1418 = fields1417
        self.write("(")
        self.write("context")
        self.indent_sexp()
        if not len(unwrapped_fields1418) == 0:
            self.newline()
            for i1420, elem1419 in enumerate(unwrapped_fields1418):
                if (i1420 > 0):
                    self.newline()
                self.pretty_relation_id(elem1419)
        self.dedent()
        self.write(")")
        return None

    def pretty_epoch_reads(self, msg: Sequence[transactions_pb2.Read]) -> None:
        _flat = self._try_flat(msg, self.pretty_epoch_reads)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1896(_dollar_dollar):
            return _dollar_dollar
        _t1897 = _t1896(msg)
        fields1421 = _t1897
        assert fields1421 is not None
        unwrapped_fields1422 = fields1421
        self.write("(")
        self.write("reads")
        self.indent_sexp()
        if not len(unwrapped_fields1422) == 0:
            self.newline()
            for i1424, elem1423 in enumerate(unwrapped_fields1422):
                if (i1424 > 0):
                    self.newline()
                self.pretty_read(elem1423)
        self.dedent()
        self.write(")")
        return None

    def pretty_read(self, msg: transactions_pb2.Read) -> None:
        _flat = self._try_flat(msg, self.pretty_read)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1898(_dollar_dollar):
            if _dollar_dollar.HasField("demand"):
                _t1899 = _dollar_dollar.demand
            else:
                _t1899 = None
            return _t1899
        _t1900 = _t1898(msg)
        deconstruct_result1433 = _t1900
        if deconstruct_result1433 is not None:
            assert deconstruct_result1433 is not None
            unwrapped1434 = deconstruct_result1433
            self.pretty_demand(unwrapped1434)
        else:
            def _t1901(_dollar_dollar):
                if _dollar_dollar.HasField("output"):
                    _t1902 = _dollar_dollar.output
                else:
                    _t1902 = None
                return _t1902
            _t1903 = _t1901(msg)
            deconstruct_result1431 = _t1903
            if deconstruct_result1431 is not None:
                assert deconstruct_result1431 is not None
                unwrapped1432 = deconstruct_result1431
                self.pretty_output(unwrapped1432)
            else:
                def _t1904(_dollar_dollar):
                    if _dollar_dollar.HasField("what_if"):
                        _t1905 = _dollar_dollar.what_if
                    else:
                        _t1905 = None
                    return _t1905
                _t1906 = _t1904(msg)
                deconstruct_result1429 = _t1906
                if deconstruct_result1429 is not None:
                    assert deconstruct_result1429 is not None
                    unwrapped1430 = deconstruct_result1429
                    self.pretty_what_if(unwrapped1430)
                else:
                    def _t1907(_dollar_dollar):
                        if _dollar_dollar.HasField("abort"):
                            _t1908 = _dollar_dollar.abort
                        else:
                            _t1908 = None
                        return _t1908
                    _t1909 = _t1907(msg)
                    deconstruct_result1427 = _t1909
                    if deconstruct_result1427 is not None:
                        assert deconstruct_result1427 is not None
                        unwrapped1428 = deconstruct_result1427
                        self.pretty_abort(unwrapped1428)
                    else:
                        def _t1910(_dollar_dollar):
                            if _dollar_dollar.HasField("export"):
                                _t1911 = _dollar_dollar.export
                            else:
                                _t1911 = None
                            return _t1911
                        _t1912 = _t1910(msg)
                        deconstruct_result1425 = _t1912
                        if deconstruct_result1425 is not None:
                            assert deconstruct_result1425 is not None
                            unwrapped1426 = deconstruct_result1425
                            self.pretty_export(unwrapped1426)
                        else:
                            raise ParseError("No matching rule for read")
        return None

    def pretty_demand(self, msg: transactions_pb2.Demand) -> None:
        _flat = self._try_flat(msg, self.pretty_demand)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1913(_dollar_dollar):
            return _dollar_dollar.relation_id
        _t1914 = _t1913(msg)
        fields1435 = _t1914
        assert fields1435 is not None
        unwrapped_fields1436 = fields1435
        self.write("(")
        self.write("demand")
        self.indent_sexp()
        self.newline()
        self.pretty_relation_id(unwrapped_fields1436)
        self.dedent()
        self.write(")")
        return None

    def pretty_output(self, msg: transactions_pb2.Output) -> None:
        _flat = self._try_flat(msg, self.pretty_output)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1915(_dollar_dollar):
            return (_dollar_dollar.name, _dollar_dollar.relation_id,)
        _t1916 = _t1915(msg)
        fields1437 = _t1916
        assert fields1437 is not None
        unwrapped_fields1438 = fields1437
        self.write("(")
        self.write("output")
        self.indent_sexp()
        self.newline()
        field1439 = unwrapped_fields1438[0]
        self.pretty_name(field1439)
        self.newline()
        field1440 = unwrapped_fields1438[1]
        self.pretty_relation_id(field1440)
        self.dedent()
        self.write(")")
        return None

    def pretty_what_if(self, msg: transactions_pb2.WhatIf) -> None:
        _flat = self._try_flat(msg, self.pretty_what_if)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1917(_dollar_dollar):
            return (_dollar_dollar.branch, _dollar_dollar.epoch,)
        _t1918 = _t1917(msg)
        fields1441 = _t1918
        assert fields1441 is not None
        unwrapped_fields1442 = fields1441
        self.write("(")
        self.write("what_if")
        self.indent_sexp()
        self.newline()
        field1443 = unwrapped_fields1442[0]
        self.pretty_name(field1443)
        self.newline()
        field1444 = unwrapped_fields1442[1]
        self.pretty_epoch(field1444)
        self.dedent()
        self.write(")")
        return None

    def pretty_abort(self, msg: transactions_pb2.Abort) -> None:
        _flat = self._try_flat(msg, self.pretty_abort)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1919(_dollar_dollar):
            if _dollar_dollar.name != "abort":
                _t1920 = _dollar_dollar.name
            else:
                _t1920 = None
            return (_t1920, _dollar_dollar.relation_id,)
        _t1921 = _t1919(msg)
        fields1445 = _t1921
        assert fields1445 is not None
        unwrapped_fields1446 = fields1445
        self.write("(")
        self.write("abort")
        self.indent_sexp()
        field1447 = unwrapped_fields1446[0]
        if field1447 is not None:
            self.newline()
            assert field1447 is not None
            opt_val1448 = field1447
            self.pretty_name(opt_val1448)
        self.newline()
        field1449 = unwrapped_fields1446[1]
        self.pretty_relation_id(field1449)
        self.dedent()
        self.write(")")
        return None

    def pretty_export(self, msg: transactions_pb2.Export) -> None:
        _flat = self._try_flat(msg, self.pretty_export)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1922(_dollar_dollar):
            return _dollar_dollar.csv_config
        _t1923 = _t1922(msg)
        fields1450 = _t1923
        assert fields1450 is not None
        unwrapped_fields1451 = fields1450
        self.write("(")
        self.write("export")
        self.indent_sexp()
        self.newline()
        self.pretty_export_csv_config(unwrapped_fields1451)
        self.dedent()
        self.write(")")
        return None

    def pretty_export_csv_config(self, msg: transactions_pb2.ExportCSVConfig) -> None:
        _flat = self._try_flat(msg, self.pretty_export_csv_config)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1924(_dollar_dollar):
            _t1925 = self.deconstruct_export_csv_config(_dollar_dollar)
            return (_dollar_dollar.path, _dollar_dollar.data_columns, _t1925,)
        _t1926 = _t1924(msg)
        fields1452 = _t1926
        assert fields1452 is not None
        unwrapped_fields1453 = fields1452
        self.write("(")
        self.write("export_csv_config")
        self.indent_sexp()
        self.newline()
        field1454 = unwrapped_fields1453[0]
        self.pretty_export_csv_path(field1454)
        self.newline()
        field1455 = unwrapped_fields1453[1]
        self.pretty_export_csv_columns(field1455)
        self.newline()
        field1456 = unwrapped_fields1453[2]
        self.pretty_config_dict(field1456)
        self.dedent()
        self.write(")")
        return None

    def pretty_export_csv_path(self, msg: str) -> None:
        _flat = self._try_flat(msg, self.pretty_export_csv_path)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1927(_dollar_dollar):
            return _dollar_dollar
        _t1928 = _t1927(msg)
        fields1457 = _t1928
        assert fields1457 is not None
        unwrapped_fields1458 = fields1457
        self.write("(")
        self.write("path")
        self.indent_sexp()
        self.newline()
        self.write(self.format_string_value(unwrapped_fields1458))
        self.dedent()
        self.write(")")
        return None

    def pretty_export_csv_columns(self, msg: Sequence[transactions_pb2.ExportCSVColumn]) -> None:
        _flat = self._try_flat(msg, self.pretty_export_csv_columns)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1929(_dollar_dollar):
            return _dollar_dollar
        _t1930 = _t1929(msg)
        fields1459 = _t1930
        assert fields1459 is not None
        unwrapped_fields1460 = fields1459
        self.write("(")
        self.write("columns")
        self.indent_sexp()
        if not len(unwrapped_fields1460) == 0:
            self.newline()
            for i1462, elem1461 in enumerate(unwrapped_fields1460):
                if (i1462 > 0):
                    self.newline()
                self.pretty_export_csv_column(elem1461)
        self.dedent()
        self.write(")")
        return None

    def pretty_export_csv_column(self, msg: transactions_pb2.ExportCSVColumn) -> None:
        _flat = self._try_flat(msg, self.pretty_export_csv_column)
        if _flat is not None:
            self.write(_flat)
            return None
        def _t1931(_dollar_dollar):
            return (_dollar_dollar.column_name, _dollar_dollar.column_data,)
        _t1932 = _t1931(msg)
        fields1463 = _t1932
        assert fields1463 is not None
        unwrapped_fields1464 = fields1463
        self.write("(")
        self.write("column")
        self.indent_sexp()
        self.newline()
        field1465 = unwrapped_fields1464[0]
        self.write(self.format_string_value(field1465))
        self.newline()
        field1466 = unwrapped_fields1464[1]
        self.pretty_relation_id(field1466)
        self.dedent()
        self.write(")")
        return None


def pretty(msg: Any, io: Optional[IO[str]] = None, max_width: int = 92) -> str:
    """Pretty print a protobuf message and return the string representation."""
    printer = PrettyPrinter(io, max_width=max_width)
    printer.pretty_transaction(msg)
    printer.newline()
    return printer.get_output()
