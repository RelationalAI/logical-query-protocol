"""
Auto-generated LL(k) recursive-descent parser.

Generated from protobuf specifications.
Do not modify this file! If you need to modify the parser, edit the generator code
in `meta/` or edit the protobuf specification in `proto/v1`.


Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --parser python
"""

import ast
import bisect
import hashlib
import re
from collections.abc import Sequence
from typing import Any

from lqp.proto.v1 import logic_pb2, fragments_pb2, transactions_pb2


class ParseError(Exception):
    """Parse error exception."""

    pass


class Location:
    """Source location (1-based line and column, 0-based byte offset)."""

    __slots__ = ("line", "column", "offset")

    def __init__(self, line: int, column: int, offset: int):
        self.line = line
        self.column = column
        self.offset = offset

    def __repr__(self) -> str:
        return f"Location({self.line}, {self.column}, {self.offset})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Location):
            return NotImplemented
        return self.line == other.line and self.column == other.column and self.offset == other.offset

    def __hash__(self) -> int:
        return hash((self.line, self.column, self.offset))


class Span:
    """Source span from start to stop location."""

    __slots__ = ("start", "stop")

    def __init__(self, start: Location, stop: Location):
        self.start = start
        self.stop = stop

    def __repr__(self) -> str:
        return f"Span({self.start}, {self.stop})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Span):
            return NotImplemented
        return self.start == other.start and self.stop == other.stop

    def __hash__(self) -> int:
        return hash((self.start, self.stop))


class Token:
    """Token representation."""

    def __init__(self, type: str, value: str, start_pos: int, end_pos: int):
        self.type = type
        self.value = value
        self.start_pos = start_pos
        self.end_pos = end_pos

    @property
    def pos(self) -> int:
        return self.start_pos

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r}, {self.start_pos})"


_WHITESPACE_RE = re.compile(r"\s+")
_COMMENT_RE = re.compile(r";;.*")
_TOKEN_SPECS = [
    ("LITERAL", re.compile(r"::"), lambda x: x),
    ("LITERAL", re.compile(r"<="), lambda x: x),
    ("LITERAL", re.compile(r">="), lambda x: x),
    ("LITERAL", re.compile(r"\#"), lambda x: x),
    ("LITERAL", re.compile(r"\("), lambda x: x),
    ("LITERAL", re.compile(r"\)"), lambda x: x),
    ("LITERAL", re.compile(r"\*"), lambda x: x),
    ("LITERAL", re.compile(r"\+"), lambda x: x),
    ("LITERAL", re.compile(r"\-"), lambda x: x),
    ("LITERAL", re.compile(r"/"), lambda x: x),
    ("LITERAL", re.compile(r":"), lambda x: x),
    ("LITERAL", re.compile(r"<"), lambda x: x),
    ("LITERAL", re.compile(r"="), lambda x: x),
    ("LITERAL", re.compile(r">"), lambda x: x),
    ("LITERAL", re.compile(r"\["), lambda x: x),
    ("LITERAL", re.compile(r"\]"), lambda x: x),
    ("LITERAL", re.compile(r"\{"), lambda x: x),
    ("LITERAL", re.compile(r"\|"), lambda x: x),
    ("LITERAL", re.compile(r"\}"), lambda x: x),
    ("DECIMAL", re.compile(r"[-]?\d+\.\d+d\d+"), lambda x: Lexer.scan_decimal(x)),
    ("FLOAT", re.compile(r"([-]?\d+\.\d+|inf|nan)"), lambda x: Lexer.scan_float(x)),
    ("INT", re.compile(r"[-]?\d+"), lambda x: Lexer.scan_int(x)),
    ("INT128", re.compile(r"[-]?\d+i128"), lambda x: Lexer.scan_int128(x)),
    ("STRING", re.compile(r'"(?:[^"\\]|\\.)*"'), lambda x: Lexer.scan_string(x)),
    ("SYMBOL", re.compile(r"[a-zA-Z_][a-zA-Z0-9_.-]*"), lambda x: Lexer.scan_symbol(x)),
    ("UINT128", re.compile(r"0x[0-9a-fA-F]+"), lambda x: Lexer.scan_uint128(x)),
]


class Lexer:
    """Tokenizer for the input."""

    def __init__(self, input_str: str):
        self.input = input_str
        self.pos = 0
        self.tokens: list[Token] = []
        self._tokenize()

    def _tokenize(self) -> None:
        """Tokenize the input string."""
        while self.pos < len(self.input):
            match = _WHITESPACE_RE.match(self.input, self.pos)
            if match:
                self.pos = match.end()
                continue

            match = _COMMENT_RE.match(self.input, self.pos)
            if match:
                self.pos = match.end()
                continue

            # Collect all matching tokens
            candidates = []

            for token_type, regex, action in _TOKEN_SPECS:
                match = regex.match(self.input, self.pos)
                if match:
                    value = match.group(0)
                    candidates.append((token_type, value, action, match.end()))

            if not candidates:
                raise ParseError(
                    f"Unexpected character at position {self.pos}: {self.input[self.pos]!r}"
                )

            # Pick the longest match
            token_type, value, action, end_pos = max(candidates, key=lambda x: x[3])
            self.tokens.append(Token(token_type, action(value), self.pos, end_pos))
            self.pos = end_pos

        self.tokens.append(Token("$", "", self.pos, self.pos))

    @staticmethod
    def scan_symbol(s: str) -> str:
        """Parse SYMBOL token."""
        return s

    @staticmethod
    def scan_string(s: str) -> str:
        """Parse STRING token."""
        return ast.literal_eval(s)

    @staticmethod
    def scan_int(n: str) -> int:
        """Parse INT token."""
        val = int(n)
        if val < -(1 << 63) or val >= (1 << 63):
            raise ParseError(f"Integer literal out of 64-bit range: {n}")
        return val

    @staticmethod
    def scan_float(f: str) -> float:
        """Parse FLOAT token."""
        if f == "inf":
            return float("inf")
        elif f == "nan":
            return float("nan")
        return float(f)

    @staticmethod
    def scan_uint128(u: str) -> Any:
        """Parse UINT128 token."""
        uint128_val = int(u, 16)
        if uint128_val < 0 or uint128_val >= (1 << 128):
            raise ParseError(f"UInt128 literal out of range: {u}")
        low = uint128_val & 0xFFFFFFFFFFFFFFFF
        high = (uint128_val >> 64) & 0xFFFFFFFFFFFFFFFF
        return logic_pb2.UInt128Value(low=low, high=high)

    @staticmethod
    def scan_int128(u: str) -> Any:
        """Parse INT128 token."""
        u = u[:-4]  # Remove the "i128" suffix
        int128_val = int(u)
        if int128_val < -(1 << 127) or int128_val >= (1 << 127):
            raise ParseError(f"Int128 literal out of range: {u}")
        low = int128_val & 0xFFFFFFFFFFFFFFFF
        high = (int128_val >> 64) & 0xFFFFFFFFFFFFFFFF
        return logic_pb2.Int128Value(low=low, high=high)

    @staticmethod
    def scan_decimal(d: str) -> Any:
        """Parse DECIMAL token."""
        # Decimal is a string like "123.456d12" where the last part after `d` is the
        # precision, and the scale is the number of digits between the decimal point and `d`
        parts = d.split("d")
        if len(parts) != 2:
            raise ValueError(f"Invalid decimal format: {d}")
        scale = len(parts[0].split(".")[1])
        precision = int(parts[1])
        # Parse the integer value directly without calling scan_int128 which strips "i128" suffix
        int_str = parts[0].replace(".", "")
        int128_val = int(int_str)
        low = int128_val & 0xFFFFFFFFFFFFFFFF
        high = (int128_val >> 64) & 0xFFFFFFFFFFFFFFFF
        value = logic_pb2.Int128Value(low=low, high=high)
        return logic_pb2.DecimalValue(precision=precision, scale=scale, value=value)


def _compute_line_starts(text: str) -> list[int]:
    """Compute byte offsets where each line starts (0-based)."""
    starts = [0]
    for i, ch in enumerate(text):
        if ch == '\n':
            starts.append(i + 1)
    return starts


class Parser:
    """LL(k) recursive-descent parser with backtracking."""

    def __init__(self, tokens: list[Token], input_str: str):
        self.tokens = tokens
        self.pos = 0
        self.id_to_debuginfo = {}
        self._current_fragment_id: bytes | None = None
        self._relation_id_to_name = {}
        self.provenance: dict[tuple[int, ...], Span] = {}
        self._line_starts = _compute_line_starts(input_str)

    def _make_location(self, offset: int) -> Location:
        """Convert byte offset to Location with 1-based line/column."""
        line_idx = bisect.bisect_right(self._line_starts, offset) - 1
        col = offset - self._line_starts[line_idx]
        return Location(line_idx + 1, col + 1, offset)

    def span_start(self) -> int:
        """Return the start offset of the current token."""
        return self.lookahead(0).start_pos

    def record_span(self, start_offset: int) -> None:
        """Record a span from start_offset to the previous token's end."""
        if self.pos > 0:
            end_offset = self.tokens[self.pos - 1].end_pos
        else:
            end_offset = start_offset
        span = Span(self._make_location(start_offset), self._make_location(end_offset))
        self.provenance[tuple()] = span

    def lookahead(self, k: int = 0) -> Token:
        """Get lookahead token at offset k."""
        idx = self.pos + k
        return self.tokens[idx] if idx < len(self.tokens) else Token("$", "", -1, -1)

    def consume_literal(self, expected: str) -> None:
        """Consume a literal token."""
        if not self.match_lookahead_literal(expected, 0):
            token = self.lookahead(0)
            raise ParseError(
                f"Expected literal {expected!r} but got {token.type}=`{token.value!r}` at position {token.pos}"
            )
        self.pos += 1

    def consume_terminal(self, expected: str) -> Any:
        """Consume a terminal token and return parsed value."""
        if not self.match_lookahead_terminal(expected, 0):
            token = self.lookahead(0)
            raise ParseError(
                f"Expected terminal {expected} but got {token.type}=`{token.value!r}` at position {token.pos}"
            )
        token = self.lookahead(0)
        self.pos += 1
        return token.value

    def match_lookahead_literal(self, literal: str, k: int) -> bool:
        """Check if lookahead token at position k matches literal.

        Supports soft keywords: alphanumeric literals are lexed as SYMBOL tokens,
        so we check both LITERAL and SYMBOL token types.
        """
        token = self.lookahead(k)
        if token.type == "LITERAL" and token.value == literal:
            return True
        if token.type == "SYMBOL" and token.value == literal:
            return True
        return False

    def match_lookahead_terminal(self, terminal: str, k: int) -> bool:
        """Check if lookahead token at position k matches terminal."""
        token = self.lookahead(k)
        return token.type == terminal

    def start_fragment(
        self, fragment_id: fragments_pb2.FragmentId
    ) -> fragments_pb2.FragmentId:
        """Set current fragment ID for debug info tracking."""
        self._current_fragment_id = fragment_id.id
        return fragment_id

    def relation_id_from_string(self, name: str) -> Any:
        """Create RelationId from string and track mapping for debug info."""
        id_low = int(hashlib.sha256(name.encode()).hexdigest()[:16], 16)
        id_high = 0
        relation_id = logic_pb2.RelationId(id_low=id_low, id_high=id_high)

        # Store the mapping for the current fragment if we're inside one
        if self._current_fragment_id is not None:
            if self._current_fragment_id not in self.id_to_debuginfo:
                self.id_to_debuginfo[self._current_fragment_id] = {}
            key = (relation_id.id_low, relation_id.id_high)
            self.id_to_debuginfo[self._current_fragment_id][key] = name

        return relation_id

    def construct_fragment(
        self,
        fragment_id: fragments_pb2.FragmentId,
        declarations: list[logic_pb2.Declaration],
    ) -> fragments_pb2.Fragment:
        """Construct Fragment from fragment_id, declarations, and debug info from parser state."""
        # Get the debug info for this fragment
        debug_info_dict = self.id_to_debuginfo.get(fragment_id.id, {})

        # Convert to DebugInfo protobuf
        ids = []
        orig_names = []
        for (id_low, id_high), name in debug_info_dict.items():
            ids.append(logic_pb2.RelationId(id_low=id_low, id_high=id_high))
            orig_names.append(name)

        # Create DebugInfo
        debug_info = fragments_pb2.DebugInfo(ids=ids, orig_names=orig_names)

        # Clear _current_fragment_id before the return
        self._current_fragment_id = None

        # Create and return Fragment
        return fragments_pb2.Fragment(
            id=fragment_id, declarations=declarations, debug_info=debug_info
        )

    def relation_id_to_string(self, msg) -> str:
        """Stub: only used in pretty printer."""
        raise NotImplementedError(
            "relation_id_to_string is only available in PrettyPrinter"
        )

    def relation_id_to_uint128(self, msg):
        """Stub: only used in pretty printer."""
        raise NotImplementedError(
            "relation_id_to_uint128 is only available in PrettyPrinter"
        )

    # --- Helper functions ---

    def _extract_value_int32(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t1783 = value.HasField("int_value")
        else:
            _t1783 = False
        if _t1783:
            assert value is not None
            return int(value.int_value)
        else:
            _t1784 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t1785 = value.HasField("int_value")
        else:
            _t1785 = False
        if _t1785:
            assert value is not None
            return value.int_value
        else:
            _t1786 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t1787 = value.HasField("string_value")
        else:
            _t1787 = False
        if _t1787:
            assert value is not None
            return value.string_value
        else:
            _t1788 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1789 = value.HasField("boolean_value")
        else:
            _t1789 = False
        if _t1789:
            assert value is not None
            return value.boolean_value
        else:
            _t1790 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1791 = value.HasField("string_value")
        else:
            _t1791 = False
        if _t1791:
            assert value is not None
            return [value.string_value]
        else:
            _t1792 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t1793 = value.HasField("int_value")
        else:
            _t1793 = False
        if _t1793:
            assert value is not None
            return value.int_value
        else:
            _t1794 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t1795 = value.HasField("float_value")
        else:
            _t1795 = False
        if _t1795:
            assert value is not None
            return value.float_value
        else:
            _t1796 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t1797 = value.HasField("string_value")
        else:
            _t1797 = False
        if _t1797:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1798 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t1799 = value.HasField("uint128_value")
        else:
            _t1799 = False
        if _t1799:
            assert value is not None
            return value.uint128_value
        else:
            _t1800 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1801 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1801
        _t1802 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1802
        _t1803 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1803
        _t1804 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1804
        _t1805 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1805
        _t1806 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1806
        _t1807 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1807
        _t1808 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1808
        _t1809 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1809
        _t1810 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1810
        _t1811 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1811
        _t1812 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1812

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1813 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1813
        _t1814 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1814
        _t1815 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1815
        _t1816 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1816
        _t1817 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1817
        _t1818 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1818
        _t1819 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1819
        _t1820 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1820
        _t1821 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1821
        _t1822 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1822
        _t1823 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1823

    def default_configure(self) -> transactions_pb2.Configure:
        _t1824 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1824
        _t1825 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1825

    def construct_configure(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.Configure:
        config = dict(config_dict)
        maintenance_level_val = config.get("ivm.maintenance_level")
        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
        if (maintenance_level_val is not None and maintenance_level_val.HasField("string_value")):
            if maintenance_level_val.string_value == "off":
                maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
            else:
                if maintenance_level_val.string_value == "auto":
                    maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
                else:
                    if maintenance_level_val.string_value == "all":
                        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
                    else:
                        maintenance_level = transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
        _t1826 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1826
        _t1827 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1827
        _t1828 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1828

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1829 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1829
        _t1830 = self._extract_value_string(config.get("compression"), "")
        compression = _t1830
        _t1831 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1831
        _t1832 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1832
        _t1833 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1833
        _t1834 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1834
        _t1835 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1835
        _t1836 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1836

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start598 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1185 = self.parse_configure()
            _t1184 = _t1185
        else:
            _t1184 = None
        configure592 = _t1184
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1187 = self.parse_sync()
            _t1186 = _t1187
        else:
            _t1186 = None
        sync593 = _t1186
        xs594 = []
        cond595 = self.match_lookahead_literal("(", 0)
        while cond595:
            _t1188 = self.parse_epoch()
            item596 = _t1188
            xs594.append(item596)
            cond595 = self.match_lookahead_literal("(", 0)
        epochs597 = xs594
        self.consume_literal(")")
        _t1189 = self.default_configure()
        _t1190 = transactions_pb2.Transaction(epochs=epochs597, configure=(configure592 if configure592 is not None else _t1189), sync=sync593)
        result599 = _t1190
        self.record_span(span_start598)
        return result599

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start601 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1191 = self.parse_config_dict()
        config_dict600 = _t1191
        self.consume_literal(")")
        _t1192 = self.construct_configure(config_dict600)
        result602 = _t1192
        self.record_span(span_start601)
        return result602

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        span_start607 = self.span_start()
        self.consume_literal("{")
        xs603 = []
        cond604 = self.match_lookahead_literal(":", 0)
        while cond604:
            _t1193 = self.parse_config_key_value()
            item605 = _t1193
            xs603.append(item605)
            cond604 = self.match_lookahead_literal(":", 0)
        config_key_values606 = xs603
        self.consume_literal("}")
        result608 = config_key_values606
        self.record_span(span_start607)
        return result608

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        span_start611 = self.span_start()
        self.consume_literal(":")
        symbol609 = self.consume_terminal("SYMBOL")
        _t1194 = self.parse_value()
        value610 = _t1194
        result612 = (symbol609, value610,)
        self.record_span(span_start611)
        return result612

    def parse_value(self) -> logic_pb2.Value:
        span_start623 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1195 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1196 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1197 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1199 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1200 = 0
                            else:
                                _t1200 = -1
                            _t1199 = _t1200
                        _t1198 = _t1199
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1201 = 5
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t1202 = 2
                            else:
                                if self.match_lookahead_terminal("INT128", 0):
                                    _t1203 = 6
                                else:
                                    if self.match_lookahead_terminal("INT", 0):
                                        _t1204 = 3
                                    else:
                                        if self.match_lookahead_terminal("FLOAT", 0):
                                            _t1205 = 4
                                        else:
                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                _t1206 = 7
                                            else:
                                                _t1206 = -1
                                            _t1205 = _t1206
                                        _t1204 = _t1205
                                    _t1203 = _t1204
                                _t1202 = _t1203
                            _t1201 = _t1202
                        _t1198 = _t1201
                    _t1197 = _t1198
                _t1196 = _t1197
            _t1195 = _t1196
        prediction613 = _t1195
        if prediction613 == 9:
            _t1208 = self.parse_boolean_value()
            boolean_value622 = _t1208
            _t1209 = logic_pb2.Value(boolean_value=boolean_value622)
            _t1207 = _t1209
        else:
            if prediction613 == 8:
                self.consume_literal("missing")
                _t1211 = logic_pb2.MissingValue()
                _t1212 = logic_pb2.Value(missing_value=_t1211)
                _t1210 = _t1212
            else:
                if prediction613 == 7:
                    decimal621 = self.consume_terminal("DECIMAL")
                    _t1214 = logic_pb2.Value(decimal_value=decimal621)
                    _t1213 = _t1214
                else:
                    if prediction613 == 6:
                        int128620 = self.consume_terminal("INT128")
                        _t1216 = logic_pb2.Value(int128_value=int128620)
                        _t1215 = _t1216
                    else:
                        if prediction613 == 5:
                            uint128619 = self.consume_terminal("UINT128")
                            _t1218 = logic_pb2.Value(uint128_value=uint128619)
                            _t1217 = _t1218
                        else:
                            if prediction613 == 4:
                                float618 = self.consume_terminal("FLOAT")
                                _t1220 = logic_pb2.Value(float_value=float618)
                                _t1219 = _t1220
                            else:
                                if prediction613 == 3:
                                    int617 = self.consume_terminal("INT")
                                    _t1222 = logic_pb2.Value(int_value=int617)
                                    _t1221 = _t1222
                                else:
                                    if prediction613 == 2:
                                        string616 = self.consume_terminal("STRING")
                                        _t1224 = logic_pb2.Value(string_value=string616)
                                        _t1223 = _t1224
                                    else:
                                        if prediction613 == 1:
                                            _t1226 = self.parse_datetime()
                                            datetime615 = _t1226
                                            _t1227 = logic_pb2.Value(datetime_value=datetime615)
                                            _t1225 = _t1227
                                        else:
                                            if prediction613 == 0:
                                                _t1229 = self.parse_date()
                                                date614 = _t1229
                                                _t1230 = logic_pb2.Value(date_value=date614)
                                                _t1228 = _t1230
                                            else:
                                                raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1225 = _t1228
                                        _t1223 = _t1225
                                    _t1221 = _t1223
                                _t1219 = _t1221
                            _t1217 = _t1219
                        _t1215 = _t1217
                    _t1213 = _t1215
                _t1210 = _t1213
            _t1207 = _t1210
        result624 = _t1207
        self.record_span(span_start623)
        return result624

    def parse_date(self) -> logic_pb2.DateValue:
        span_start628 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int625 = self.consume_terminal("INT")
        int_3626 = self.consume_terminal("INT")
        int_4627 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1231 = logic_pb2.DateValue(year=int(int625), month=int(int_3626), day=int(int_4627))
        result629 = _t1231
        self.record_span(span_start628)
        return result629

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start637 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int630 = self.consume_terminal("INT")
        int_3631 = self.consume_terminal("INT")
        int_4632 = self.consume_terminal("INT")
        int_5633 = self.consume_terminal("INT")
        int_6634 = self.consume_terminal("INT")
        int_7635 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1232 = self.consume_terminal("INT")
        else:
            _t1232 = None
        int_8636 = _t1232
        self.consume_literal(")")
        _t1233 = logic_pb2.DateTimeValue(year=int(int630), month=int(int_3631), day=int(int_4632), hour=int(int_5633), minute=int(int_6634), second=int(int_7635), microsecond=int((int_8636 if int_8636 is not None else 0)))
        result638 = _t1233
        self.record_span(span_start637)
        return result638

    def parse_boolean_value(self) -> bool:
        span_start640 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1234 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1235 = 1
            else:
                _t1235 = -1
            _t1234 = _t1235
        prediction639 = _t1234
        if prediction639 == 1:
            self.consume_literal("false")
            _t1236 = False
        else:
            if prediction639 == 0:
                self.consume_literal("true")
                _t1237 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1236 = _t1237
        result641 = _t1236
        self.record_span(span_start640)
        return result641

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start646 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs642 = []
        cond643 = self.match_lookahead_literal(":", 0)
        while cond643:
            _t1238 = self.parse_fragment_id()
            item644 = _t1238
            xs642.append(item644)
            cond643 = self.match_lookahead_literal(":", 0)
        fragment_ids645 = xs642
        self.consume_literal(")")
        _t1239 = transactions_pb2.Sync(fragments=fragment_ids645)
        result647 = _t1239
        self.record_span(span_start646)
        return result647

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start649 = self.span_start()
        self.consume_literal(":")
        symbol648 = self.consume_terminal("SYMBOL")
        result650 = fragments_pb2.FragmentId(id=symbol648.encode())
        self.record_span(span_start649)
        return result650

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start653 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1241 = self.parse_epoch_writes()
            _t1240 = _t1241
        else:
            _t1240 = None
        epoch_writes651 = _t1240
        if self.match_lookahead_literal("(", 0):
            _t1243 = self.parse_epoch_reads()
            _t1242 = _t1243
        else:
            _t1242 = None
        epoch_reads652 = _t1242
        self.consume_literal(")")
        _t1244 = transactions_pb2.Epoch(writes=(epoch_writes651 if epoch_writes651 is not None else []), reads=(epoch_reads652 if epoch_reads652 is not None else []))
        result654 = _t1244
        self.record_span(span_start653)
        return result654

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        span_start659 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("writes")
        xs655 = []
        cond656 = self.match_lookahead_literal("(", 0)
        while cond656:
            _t1245 = self.parse_write()
            item657 = _t1245
            xs655.append(item657)
            cond656 = self.match_lookahead_literal("(", 0)
        writes658 = xs655
        self.consume_literal(")")
        result660 = writes658
        self.record_span(span_start659)
        return result660

    def parse_write(self) -> transactions_pb2.Write:
        span_start666 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1247 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1248 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1249 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1250 = 2
                        else:
                            _t1250 = -1
                        _t1249 = _t1250
                    _t1248 = _t1249
                _t1247 = _t1248
            _t1246 = _t1247
        else:
            _t1246 = -1
        prediction661 = _t1246
        if prediction661 == 3:
            _t1252 = self.parse_snapshot()
            snapshot665 = _t1252
            _t1253 = transactions_pb2.Write(snapshot=snapshot665)
            _t1251 = _t1253
        else:
            if prediction661 == 2:
                _t1255 = self.parse_context()
                context664 = _t1255
                _t1256 = transactions_pb2.Write(context=context664)
                _t1254 = _t1256
            else:
                if prediction661 == 1:
                    _t1258 = self.parse_undefine()
                    undefine663 = _t1258
                    _t1259 = transactions_pb2.Write(undefine=undefine663)
                    _t1257 = _t1259
                else:
                    if prediction661 == 0:
                        _t1261 = self.parse_define()
                        define662 = _t1261
                        _t1262 = transactions_pb2.Write(define=define662)
                        _t1260 = _t1262
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1257 = _t1260
                _t1254 = _t1257
            _t1251 = _t1254
        result667 = _t1251
        self.record_span(span_start666)
        return result667

    def parse_define(self) -> transactions_pb2.Define:
        span_start669 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1263 = self.parse_fragment()
        fragment668 = _t1263
        self.consume_literal(")")
        _t1264 = transactions_pb2.Define(fragment=fragment668)
        result670 = _t1264
        self.record_span(span_start669)
        return result670

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start676 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1265 = self.parse_new_fragment_id()
        new_fragment_id671 = _t1265
        xs672 = []
        cond673 = self.match_lookahead_literal("(", 0)
        while cond673:
            _t1266 = self.parse_declaration()
            item674 = _t1266
            xs672.append(item674)
            cond673 = self.match_lookahead_literal("(", 0)
        declarations675 = xs672
        self.consume_literal(")")
        result677 = self.construct_fragment(new_fragment_id671, declarations675)
        self.record_span(span_start676)
        return result677

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start679 = self.span_start()
        _t1267 = self.parse_fragment_id()
        fragment_id678 = _t1267
        self.start_fragment(fragment_id678)
        result680 = fragment_id678
        self.record_span(span_start679)
        return result680

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start686 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t1269 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1270 = 2
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t1271 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t1272 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t1273 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t1274 = 1
                                else:
                                    _t1274 = -1
                                _t1273 = _t1274
                            _t1272 = _t1273
                        _t1271 = _t1272
                    _t1270 = _t1271
                _t1269 = _t1270
            _t1268 = _t1269
        else:
            _t1268 = -1
        prediction681 = _t1268
        if prediction681 == 3:
            _t1276 = self.parse_data()
            data685 = _t1276
            _t1277 = logic_pb2.Declaration(data=data685)
            _t1275 = _t1277
        else:
            if prediction681 == 2:
                _t1279 = self.parse_constraint()
                constraint684 = _t1279
                _t1280 = logic_pb2.Declaration(constraint=constraint684)
                _t1278 = _t1280
            else:
                if prediction681 == 1:
                    _t1282 = self.parse_algorithm()
                    algorithm683 = _t1282
                    _t1283 = logic_pb2.Declaration(algorithm=algorithm683)
                    _t1281 = _t1283
                else:
                    if prediction681 == 0:
                        _t1285 = self.parse_def()
                        def682 = _t1285
                        _t1286 = logic_pb2.Declaration()
                        getattr(_t1286, 'def').CopyFrom(def682)
                        _t1284 = _t1286
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1281 = _t1284
                _t1278 = _t1281
            _t1275 = _t1278
        result687 = _t1275
        self.record_span(span_start686)
        return result687

    def parse_def(self) -> logic_pb2.Def:
        span_start691 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1287 = self.parse_relation_id()
        relation_id688 = _t1287
        _t1288 = self.parse_abstraction()
        abstraction689 = _t1288
        if self.match_lookahead_literal("(", 0):
            _t1290 = self.parse_attrs()
            _t1289 = _t1290
        else:
            _t1289 = None
        attrs690 = _t1289
        self.consume_literal(")")
        _t1291 = logic_pb2.Def(name=relation_id688, body=abstraction689, attrs=(attrs690 if attrs690 is not None else []))
        result692 = _t1291
        self.record_span(span_start691)
        return result692

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start696 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1292 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1293 = 1
            else:
                _t1293 = -1
            _t1292 = _t1293
        prediction693 = _t1292
        if prediction693 == 1:
            uint128695 = self.consume_terminal("UINT128")
            _t1294 = logic_pb2.RelationId(id_low=uint128695.low, id_high=uint128695.high)
        else:
            if prediction693 == 0:
                self.consume_literal(":")
                symbol694 = self.consume_terminal("SYMBOL")
                _t1295 = self.relation_id_from_string(symbol694)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1294 = _t1295
        result697 = _t1294
        self.record_span(span_start696)
        return result697

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start700 = self.span_start()
        self.consume_literal("(")
        _t1296 = self.parse_bindings()
        bindings698 = _t1296
        _t1297 = self.parse_formula()
        formula699 = _t1297
        self.consume_literal(")")
        _t1298 = logic_pb2.Abstraction(vars=(list(bindings698[0]) + list(bindings698[1] if bindings698[1] is not None else [])), value=formula699)
        result701 = _t1298
        self.record_span(span_start700)
        return result701

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        span_start707 = self.span_start()
        self.consume_literal("[")
        xs702 = []
        cond703 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond703:
            _t1299 = self.parse_binding()
            item704 = _t1299
            xs702.append(item704)
            cond703 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings705 = xs702
        if self.match_lookahead_literal("|", 0):
            _t1301 = self.parse_value_bindings()
            _t1300 = _t1301
        else:
            _t1300 = None
        value_bindings706 = _t1300
        self.consume_literal("]")
        result708 = (bindings705, (value_bindings706 if value_bindings706 is not None else []),)
        self.record_span(span_start707)
        return result708

    def parse_binding(self) -> logic_pb2.Binding:
        span_start711 = self.span_start()
        symbol709 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1302 = self.parse_type()
        type710 = _t1302
        _t1303 = logic_pb2.Var(name=symbol709)
        _t1304 = logic_pb2.Binding(var=_t1303, type=type710)
        result712 = _t1304
        self.record_span(span_start711)
        return result712

    def parse_type(self) -> logic_pb2.Type:
        span_start725 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1305 = 0
        else:
            if self.match_lookahead_literal("UINT128", 0):
                _t1306 = 4
            else:
                if self.match_lookahead_literal("STRING", 0):
                    _t1307 = 1
                else:
                    if self.match_lookahead_literal("MISSING", 0):
                        _t1308 = 8
                    else:
                        if self.match_lookahead_literal("INT128", 0):
                            _t1309 = 5
                        else:
                            if self.match_lookahead_literal("INT", 0):
                                _t1310 = 2
                            else:
                                if self.match_lookahead_literal("FLOAT", 0):
                                    _t1311 = 3
                                else:
                                    if self.match_lookahead_literal("DATETIME", 0):
                                        _t1312 = 7
                                    else:
                                        if self.match_lookahead_literal("DATE", 0):
                                            _t1313 = 6
                                        else:
                                            if self.match_lookahead_literal("BOOLEAN", 0):
                                                _t1314 = 10
                                            else:
                                                if self.match_lookahead_literal("(", 0):
                                                    _t1315 = 9
                                                else:
                                                    _t1315 = -1
                                                _t1314 = _t1315
                                            _t1313 = _t1314
                                        _t1312 = _t1313
                                    _t1311 = _t1312
                                _t1310 = _t1311
                            _t1309 = _t1310
                        _t1308 = _t1309
                    _t1307 = _t1308
                _t1306 = _t1307
            _t1305 = _t1306
        prediction713 = _t1305
        if prediction713 == 10:
            _t1317 = self.parse_boolean_type()
            boolean_type724 = _t1317
            _t1318 = logic_pb2.Type(boolean_type=boolean_type724)
            _t1316 = _t1318
        else:
            if prediction713 == 9:
                _t1320 = self.parse_decimal_type()
                decimal_type723 = _t1320
                _t1321 = logic_pb2.Type(decimal_type=decimal_type723)
                _t1319 = _t1321
            else:
                if prediction713 == 8:
                    _t1323 = self.parse_missing_type()
                    missing_type722 = _t1323
                    _t1324 = logic_pb2.Type(missing_type=missing_type722)
                    _t1322 = _t1324
                else:
                    if prediction713 == 7:
                        _t1326 = self.parse_datetime_type()
                        datetime_type721 = _t1326
                        _t1327 = logic_pb2.Type(datetime_type=datetime_type721)
                        _t1325 = _t1327
                    else:
                        if prediction713 == 6:
                            _t1329 = self.parse_date_type()
                            date_type720 = _t1329
                            _t1330 = logic_pb2.Type(date_type=date_type720)
                            _t1328 = _t1330
                        else:
                            if prediction713 == 5:
                                _t1332 = self.parse_int128_type()
                                int128_type719 = _t1332
                                _t1333 = logic_pb2.Type(int128_type=int128_type719)
                                _t1331 = _t1333
                            else:
                                if prediction713 == 4:
                                    _t1335 = self.parse_uint128_type()
                                    uint128_type718 = _t1335
                                    _t1336 = logic_pb2.Type(uint128_type=uint128_type718)
                                    _t1334 = _t1336
                                else:
                                    if prediction713 == 3:
                                        _t1338 = self.parse_float_type()
                                        float_type717 = _t1338
                                        _t1339 = logic_pb2.Type(float_type=float_type717)
                                        _t1337 = _t1339
                                    else:
                                        if prediction713 == 2:
                                            _t1341 = self.parse_int_type()
                                            int_type716 = _t1341
                                            _t1342 = logic_pb2.Type(int_type=int_type716)
                                            _t1340 = _t1342
                                        else:
                                            if prediction713 == 1:
                                                _t1344 = self.parse_string_type()
                                                string_type715 = _t1344
                                                _t1345 = logic_pb2.Type(string_type=string_type715)
                                                _t1343 = _t1345
                                            else:
                                                if prediction713 == 0:
                                                    _t1347 = self.parse_unspecified_type()
                                                    unspecified_type714 = _t1347
                                                    _t1348 = logic_pb2.Type(unspecified_type=unspecified_type714)
                                                    _t1346 = _t1348
                                                else:
                                                    raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t1343 = _t1346
                                            _t1340 = _t1343
                                        _t1337 = _t1340
                                    _t1334 = _t1337
                                _t1331 = _t1334
                            _t1328 = _t1331
                        _t1325 = _t1328
                    _t1322 = _t1325
                _t1319 = _t1322
            _t1316 = _t1319
        result726 = _t1316
        self.record_span(span_start725)
        return result726

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start727 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1349 = logic_pb2.UnspecifiedType()
        result728 = _t1349
        self.record_span(span_start727)
        return result728

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start729 = self.span_start()
        self.consume_literal("STRING")
        _t1350 = logic_pb2.StringType()
        result730 = _t1350
        self.record_span(span_start729)
        return result730

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start731 = self.span_start()
        self.consume_literal("INT")
        _t1351 = logic_pb2.IntType()
        result732 = _t1351
        self.record_span(span_start731)
        return result732

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start733 = self.span_start()
        self.consume_literal("FLOAT")
        _t1352 = logic_pb2.FloatType()
        result734 = _t1352
        self.record_span(span_start733)
        return result734

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start735 = self.span_start()
        self.consume_literal("UINT128")
        _t1353 = logic_pb2.UInt128Type()
        result736 = _t1353
        self.record_span(span_start735)
        return result736

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start737 = self.span_start()
        self.consume_literal("INT128")
        _t1354 = logic_pb2.Int128Type()
        result738 = _t1354
        self.record_span(span_start737)
        return result738

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start739 = self.span_start()
        self.consume_literal("DATE")
        _t1355 = logic_pb2.DateType()
        result740 = _t1355
        self.record_span(span_start739)
        return result740

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start741 = self.span_start()
        self.consume_literal("DATETIME")
        _t1356 = logic_pb2.DateTimeType()
        result742 = _t1356
        self.record_span(span_start741)
        return result742

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start743 = self.span_start()
        self.consume_literal("MISSING")
        _t1357 = logic_pb2.MissingType()
        result744 = _t1357
        self.record_span(span_start743)
        return result744

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start747 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int745 = self.consume_terminal("INT")
        int_3746 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1358 = logic_pb2.DecimalType(precision=int(int745), scale=int(int_3746))
        result748 = _t1358
        self.record_span(span_start747)
        return result748

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start749 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1359 = logic_pb2.BooleanType()
        result750 = _t1359
        self.record_span(span_start749)
        return result750

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        span_start755 = self.span_start()
        self.consume_literal("|")
        xs751 = []
        cond752 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond752:
            _t1360 = self.parse_binding()
            item753 = _t1360
            xs751.append(item753)
            cond752 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings754 = xs751
        result756 = bindings754
        self.record_span(span_start755)
        return result756

    def parse_formula(self) -> logic_pb2.Formula:
        span_start771 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1362 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1363 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1364 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1365 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1366 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1367 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1368 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1369 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1370 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1371 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1372 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1373 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1374 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1375 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1376 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1377 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1378 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1379 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1380 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1381 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1382 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1383 = 10
                                                                                                else:
                                                                                                    _t1383 = -1
                                                                                                _t1382 = _t1383
                                                                                            _t1381 = _t1382
                                                                                        _t1380 = _t1381
                                                                                    _t1379 = _t1380
                                                                                _t1378 = _t1379
                                                                            _t1377 = _t1378
                                                                        _t1376 = _t1377
                                                                    _t1375 = _t1376
                                                                _t1374 = _t1375
                                                            _t1373 = _t1374
                                                        _t1372 = _t1373
                                                    _t1371 = _t1372
                                                _t1370 = _t1371
                                            _t1369 = _t1370
                                        _t1368 = _t1369
                                    _t1367 = _t1368
                                _t1366 = _t1367
                            _t1365 = _t1366
                        _t1364 = _t1365
                    _t1363 = _t1364
                _t1362 = _t1363
            _t1361 = _t1362
        else:
            _t1361 = -1
        prediction757 = _t1361
        if prediction757 == 12:
            _t1385 = self.parse_cast()
            cast770 = _t1385
            _t1386 = logic_pb2.Formula(cast=cast770)
            _t1384 = _t1386
        else:
            if prediction757 == 11:
                _t1388 = self.parse_rel_atom()
                rel_atom769 = _t1388
                _t1389 = logic_pb2.Formula(rel_atom=rel_atom769)
                _t1387 = _t1389
            else:
                if prediction757 == 10:
                    _t1391 = self.parse_primitive()
                    primitive768 = _t1391
                    _t1392 = logic_pb2.Formula(primitive=primitive768)
                    _t1390 = _t1392
                else:
                    if prediction757 == 9:
                        _t1394 = self.parse_pragma()
                        pragma767 = _t1394
                        _t1395 = logic_pb2.Formula(pragma=pragma767)
                        _t1393 = _t1395
                    else:
                        if prediction757 == 8:
                            _t1397 = self.parse_atom()
                            atom766 = _t1397
                            _t1398 = logic_pb2.Formula(atom=atom766)
                            _t1396 = _t1398
                        else:
                            if prediction757 == 7:
                                _t1400 = self.parse_ffi()
                                ffi765 = _t1400
                                _t1401 = logic_pb2.Formula(ffi=ffi765)
                                _t1399 = _t1401
                            else:
                                if prediction757 == 6:
                                    _t1403 = self.parse_not()
                                    not764 = _t1403
                                    _t1404 = logic_pb2.Formula()
                                    getattr(_t1404, 'not').CopyFrom(not764)
                                    _t1402 = _t1404
                                else:
                                    if prediction757 == 5:
                                        _t1406 = self.parse_disjunction()
                                        disjunction763 = _t1406
                                        _t1407 = logic_pb2.Formula(disjunction=disjunction763)
                                        _t1405 = _t1407
                                    else:
                                        if prediction757 == 4:
                                            _t1409 = self.parse_conjunction()
                                            conjunction762 = _t1409
                                            _t1410 = logic_pb2.Formula(conjunction=conjunction762)
                                            _t1408 = _t1410
                                        else:
                                            if prediction757 == 3:
                                                _t1412 = self.parse_reduce()
                                                reduce761 = _t1412
                                                _t1413 = logic_pb2.Formula(reduce=reduce761)
                                                _t1411 = _t1413
                                            else:
                                                if prediction757 == 2:
                                                    _t1415 = self.parse_exists()
                                                    exists760 = _t1415
                                                    _t1416 = logic_pb2.Formula(exists=exists760)
                                                    _t1414 = _t1416
                                                else:
                                                    if prediction757 == 1:
                                                        _t1418 = self.parse_false()
                                                        false759 = _t1418
                                                        _t1419 = logic_pb2.Formula(disjunction=false759)
                                                        _t1417 = _t1419
                                                    else:
                                                        if prediction757 == 0:
                                                            _t1421 = self.parse_true()
                                                            true758 = _t1421
                                                            _t1422 = logic_pb2.Formula(conjunction=true758)
                                                            _t1420 = _t1422
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1417 = _t1420
                                                    _t1414 = _t1417
                                                _t1411 = _t1414
                                            _t1408 = _t1411
                                        _t1405 = _t1408
                                    _t1402 = _t1405
                                _t1399 = _t1402
                            _t1396 = _t1399
                        _t1393 = _t1396
                    _t1390 = _t1393
                _t1387 = _t1390
            _t1384 = _t1387
        result772 = _t1384
        self.record_span(span_start771)
        return result772

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start773 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1423 = logic_pb2.Conjunction(args=[])
        result774 = _t1423
        self.record_span(span_start773)
        return result774

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start775 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1424 = logic_pb2.Disjunction(args=[])
        result776 = _t1424
        self.record_span(span_start775)
        return result776

    def parse_exists(self) -> logic_pb2.Exists:
        span_start779 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1425 = self.parse_bindings()
        bindings777 = _t1425
        _t1426 = self.parse_formula()
        formula778 = _t1426
        self.consume_literal(")")
        _t1427 = logic_pb2.Abstraction(vars=(list(bindings777[0]) + list(bindings777[1] if bindings777[1] is not None else [])), value=formula778)
        _t1428 = logic_pb2.Exists(body=_t1427)
        result780 = _t1428
        self.record_span(span_start779)
        return result780

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start784 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1429 = self.parse_abstraction()
        abstraction781 = _t1429
        _t1430 = self.parse_abstraction()
        abstraction_3782 = _t1430
        _t1431 = self.parse_terms()
        terms783 = _t1431
        self.consume_literal(")")
        _t1432 = logic_pb2.Reduce(op=abstraction781, body=abstraction_3782, terms=terms783)
        result785 = _t1432
        self.record_span(span_start784)
        return result785

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        span_start790 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("terms")
        xs786 = []
        cond787 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond787:
            _t1433 = self.parse_term()
            item788 = _t1433
            xs786.append(item788)
            cond787 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms789 = xs786
        self.consume_literal(")")
        result791 = terms789
        self.record_span(span_start790)
        return result791

    def parse_term(self) -> logic_pb2.Term:
        span_start795 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1434 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1435 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1436 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1437 = 1
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1438 = 1
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1439 = 0
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1440 = 1
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t1441 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t1442 = 1
                                        else:
                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                _t1443 = 1
                                            else:
                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                    _t1444 = 1
                                                else:
                                                    _t1444 = -1
                                                _t1443 = _t1444
                                            _t1442 = _t1443
                                        _t1441 = _t1442
                                    _t1440 = _t1441
                                _t1439 = _t1440
                            _t1438 = _t1439
                        _t1437 = _t1438
                    _t1436 = _t1437
                _t1435 = _t1436
            _t1434 = _t1435
        prediction792 = _t1434
        if prediction792 == 1:
            _t1446 = self.parse_constant()
            constant794 = _t1446
            _t1447 = logic_pb2.Term(constant=constant794)
            _t1445 = _t1447
        else:
            if prediction792 == 0:
                _t1449 = self.parse_var()
                var793 = _t1449
                _t1450 = logic_pb2.Term(var=var793)
                _t1448 = _t1450
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1445 = _t1448
        result796 = _t1445
        self.record_span(span_start795)
        return result796

    def parse_var(self) -> logic_pb2.Var:
        span_start798 = self.span_start()
        symbol797 = self.consume_terminal("SYMBOL")
        _t1451 = logic_pb2.Var(name=symbol797)
        result799 = _t1451
        self.record_span(span_start798)
        return result799

    def parse_constant(self) -> logic_pb2.Value:
        span_start801 = self.span_start()
        _t1452 = self.parse_value()
        value800 = _t1452
        result802 = value800
        self.record_span(span_start801)
        return result802

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start807 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs803 = []
        cond804 = self.match_lookahead_literal("(", 0)
        while cond804:
            _t1453 = self.parse_formula()
            item805 = _t1453
            xs803.append(item805)
            cond804 = self.match_lookahead_literal("(", 0)
        formulas806 = xs803
        self.consume_literal(")")
        _t1454 = logic_pb2.Conjunction(args=formulas806)
        result808 = _t1454
        self.record_span(span_start807)
        return result808

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start813 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs809 = []
        cond810 = self.match_lookahead_literal("(", 0)
        while cond810:
            _t1455 = self.parse_formula()
            item811 = _t1455
            xs809.append(item811)
            cond810 = self.match_lookahead_literal("(", 0)
        formulas812 = xs809
        self.consume_literal(")")
        _t1456 = logic_pb2.Disjunction(args=formulas812)
        result814 = _t1456
        self.record_span(span_start813)
        return result814

    def parse_not(self) -> logic_pb2.Not:
        span_start816 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1457 = self.parse_formula()
        formula815 = _t1457
        self.consume_literal(")")
        _t1458 = logic_pb2.Not(arg=formula815)
        result817 = _t1458
        self.record_span(span_start816)
        return result817

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start821 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1459 = self.parse_name()
        name818 = _t1459
        _t1460 = self.parse_ffi_args()
        ffi_args819 = _t1460
        _t1461 = self.parse_terms()
        terms820 = _t1461
        self.consume_literal(")")
        _t1462 = logic_pb2.FFI(name=name818, args=ffi_args819, terms=terms820)
        result822 = _t1462
        self.record_span(span_start821)
        return result822

    def parse_name(self) -> str:
        span_start824 = self.span_start()
        self.consume_literal(":")
        symbol823 = self.consume_terminal("SYMBOL")
        result825 = symbol823
        self.record_span(span_start824)
        return result825

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        span_start830 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("args")
        xs826 = []
        cond827 = self.match_lookahead_literal("(", 0)
        while cond827:
            _t1463 = self.parse_abstraction()
            item828 = _t1463
            xs826.append(item828)
            cond827 = self.match_lookahead_literal("(", 0)
        abstractions829 = xs826
        self.consume_literal(")")
        result831 = abstractions829
        self.record_span(span_start830)
        return result831

    def parse_atom(self) -> logic_pb2.Atom:
        span_start837 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1464 = self.parse_relation_id()
        relation_id832 = _t1464
        xs833 = []
        cond834 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond834:
            _t1465 = self.parse_term()
            item835 = _t1465
            xs833.append(item835)
            cond834 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms836 = xs833
        self.consume_literal(")")
        _t1466 = logic_pb2.Atom(name=relation_id832, terms=terms836)
        result838 = _t1466
        self.record_span(span_start837)
        return result838

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start844 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1467 = self.parse_name()
        name839 = _t1467
        xs840 = []
        cond841 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond841:
            _t1468 = self.parse_term()
            item842 = _t1468
            xs840.append(item842)
            cond841 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms843 = xs840
        self.consume_literal(")")
        _t1469 = logic_pb2.Pragma(name=name839, terms=terms843)
        result845 = _t1469
        self.record_span(span_start844)
        return result845

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start861 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1471 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1472 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1473 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1474 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1475 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1476 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1477 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1478 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1479 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1480 = 7
                                                else:
                                                    _t1480 = -1
                                                _t1479 = _t1480
                                            _t1478 = _t1479
                                        _t1477 = _t1478
                                    _t1476 = _t1477
                                _t1475 = _t1476
                            _t1474 = _t1475
                        _t1473 = _t1474
                    _t1472 = _t1473
                _t1471 = _t1472
            _t1470 = _t1471
        else:
            _t1470 = -1
        prediction846 = _t1470
        if prediction846 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1482 = self.parse_name()
            name856 = _t1482
            xs857 = []
            cond858 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            while cond858:
                _t1483 = self.parse_rel_term()
                item859 = _t1483
                xs857.append(item859)
                cond858 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            rel_terms860 = xs857
            self.consume_literal(")")
            _t1484 = logic_pb2.Primitive(name=name856, terms=rel_terms860)
            _t1481 = _t1484
        else:
            if prediction846 == 8:
                _t1486 = self.parse_divide()
                divide855 = _t1486
                _t1485 = divide855
            else:
                if prediction846 == 7:
                    _t1488 = self.parse_multiply()
                    multiply854 = _t1488
                    _t1487 = multiply854
                else:
                    if prediction846 == 6:
                        _t1490 = self.parse_minus()
                        minus853 = _t1490
                        _t1489 = minus853
                    else:
                        if prediction846 == 5:
                            _t1492 = self.parse_add()
                            add852 = _t1492
                            _t1491 = add852
                        else:
                            if prediction846 == 4:
                                _t1494 = self.parse_gt_eq()
                                gt_eq851 = _t1494
                                _t1493 = gt_eq851
                            else:
                                if prediction846 == 3:
                                    _t1496 = self.parse_gt()
                                    gt850 = _t1496
                                    _t1495 = gt850
                                else:
                                    if prediction846 == 2:
                                        _t1498 = self.parse_lt_eq()
                                        lt_eq849 = _t1498
                                        _t1497 = lt_eq849
                                    else:
                                        if prediction846 == 1:
                                            _t1500 = self.parse_lt()
                                            lt848 = _t1500
                                            _t1499 = lt848
                                        else:
                                            if prediction846 == 0:
                                                _t1502 = self.parse_eq()
                                                eq847 = _t1502
                                                _t1501 = eq847
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1499 = _t1501
                                        _t1497 = _t1499
                                    _t1495 = _t1497
                                _t1493 = _t1495
                            _t1491 = _t1493
                        _t1489 = _t1491
                    _t1487 = _t1489
                _t1485 = _t1487
            _t1481 = _t1485
        result862 = _t1481
        self.record_span(span_start861)
        return result862

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start865 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1503 = self.parse_term()
        term863 = _t1503
        _t1504 = self.parse_term()
        term_3864 = _t1504
        self.consume_literal(")")
        _t1505 = logic_pb2.RelTerm(term=term863)
        _t1506 = logic_pb2.RelTerm(term=term_3864)
        _t1507 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1505, _t1506])
        result866 = _t1507
        self.record_span(span_start865)
        return result866

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start869 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1508 = self.parse_term()
        term867 = _t1508
        _t1509 = self.parse_term()
        term_3868 = _t1509
        self.consume_literal(")")
        _t1510 = logic_pb2.RelTerm(term=term867)
        _t1511 = logic_pb2.RelTerm(term=term_3868)
        _t1512 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1510, _t1511])
        result870 = _t1512
        self.record_span(span_start869)
        return result870

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start873 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1513 = self.parse_term()
        term871 = _t1513
        _t1514 = self.parse_term()
        term_3872 = _t1514
        self.consume_literal(")")
        _t1515 = logic_pb2.RelTerm(term=term871)
        _t1516 = logic_pb2.RelTerm(term=term_3872)
        _t1517 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1515, _t1516])
        result874 = _t1517
        self.record_span(span_start873)
        return result874

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start877 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1518 = self.parse_term()
        term875 = _t1518
        _t1519 = self.parse_term()
        term_3876 = _t1519
        self.consume_literal(")")
        _t1520 = logic_pb2.RelTerm(term=term875)
        _t1521 = logic_pb2.RelTerm(term=term_3876)
        _t1522 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1520, _t1521])
        result878 = _t1522
        self.record_span(span_start877)
        return result878

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start881 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1523 = self.parse_term()
        term879 = _t1523
        _t1524 = self.parse_term()
        term_3880 = _t1524
        self.consume_literal(")")
        _t1525 = logic_pb2.RelTerm(term=term879)
        _t1526 = logic_pb2.RelTerm(term=term_3880)
        _t1527 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1525, _t1526])
        result882 = _t1527
        self.record_span(span_start881)
        return result882

    def parse_add(self) -> logic_pb2.Primitive:
        span_start886 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1528 = self.parse_term()
        term883 = _t1528
        _t1529 = self.parse_term()
        term_3884 = _t1529
        _t1530 = self.parse_term()
        term_4885 = _t1530
        self.consume_literal(")")
        _t1531 = logic_pb2.RelTerm(term=term883)
        _t1532 = logic_pb2.RelTerm(term=term_3884)
        _t1533 = logic_pb2.RelTerm(term=term_4885)
        _t1534 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1531, _t1532, _t1533])
        result887 = _t1534
        self.record_span(span_start886)
        return result887

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start891 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1535 = self.parse_term()
        term888 = _t1535
        _t1536 = self.parse_term()
        term_3889 = _t1536
        _t1537 = self.parse_term()
        term_4890 = _t1537
        self.consume_literal(")")
        _t1538 = logic_pb2.RelTerm(term=term888)
        _t1539 = logic_pb2.RelTerm(term=term_3889)
        _t1540 = logic_pb2.RelTerm(term=term_4890)
        _t1541 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1538, _t1539, _t1540])
        result892 = _t1541
        self.record_span(span_start891)
        return result892

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start896 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1542 = self.parse_term()
        term893 = _t1542
        _t1543 = self.parse_term()
        term_3894 = _t1543
        _t1544 = self.parse_term()
        term_4895 = _t1544
        self.consume_literal(")")
        _t1545 = logic_pb2.RelTerm(term=term893)
        _t1546 = logic_pb2.RelTerm(term=term_3894)
        _t1547 = logic_pb2.RelTerm(term=term_4895)
        _t1548 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1545, _t1546, _t1547])
        result897 = _t1548
        self.record_span(span_start896)
        return result897

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start901 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1549 = self.parse_term()
        term898 = _t1549
        _t1550 = self.parse_term()
        term_3899 = _t1550
        _t1551 = self.parse_term()
        term_4900 = _t1551
        self.consume_literal(")")
        _t1552 = logic_pb2.RelTerm(term=term898)
        _t1553 = logic_pb2.RelTerm(term=term_3899)
        _t1554 = logic_pb2.RelTerm(term=term_4900)
        _t1555 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1552, _t1553, _t1554])
        result902 = _t1555
        self.record_span(span_start901)
        return result902

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start906 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1556 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1557 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1558 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1559 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1560 = 0
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1561 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1562 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1563 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1564 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1565 = 1
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1566 = 1
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1567 = 1
                                                    else:
                                                        _t1567 = -1
                                                    _t1566 = _t1567
                                                _t1565 = _t1566
                                            _t1564 = _t1565
                                        _t1563 = _t1564
                                    _t1562 = _t1563
                                _t1561 = _t1562
                            _t1560 = _t1561
                        _t1559 = _t1560
                    _t1558 = _t1559
                _t1557 = _t1558
            _t1556 = _t1557
        prediction903 = _t1556
        if prediction903 == 1:
            _t1569 = self.parse_term()
            term905 = _t1569
            _t1570 = logic_pb2.RelTerm(term=term905)
            _t1568 = _t1570
        else:
            if prediction903 == 0:
                _t1572 = self.parse_specialized_value()
                specialized_value904 = _t1572
                _t1573 = logic_pb2.RelTerm(specialized_value=specialized_value904)
                _t1571 = _t1573
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1568 = _t1571
        result907 = _t1568
        self.record_span(span_start906)
        return result907

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start909 = self.span_start()
        self.consume_literal("#")
        _t1574 = self.parse_value()
        value908 = _t1574
        result910 = value908
        self.record_span(span_start909)
        return result910

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start916 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1575 = self.parse_name()
        name911 = _t1575
        xs912 = []
        cond913 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond913:
            _t1576 = self.parse_rel_term()
            item914 = _t1576
            xs912.append(item914)
            cond913 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        rel_terms915 = xs912
        self.consume_literal(")")
        _t1577 = logic_pb2.RelAtom(name=name911, terms=rel_terms915)
        result917 = _t1577
        self.record_span(span_start916)
        return result917

    def parse_cast(self) -> logic_pb2.Cast:
        span_start920 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1578 = self.parse_term()
        term918 = _t1578
        _t1579 = self.parse_term()
        term_3919 = _t1579
        self.consume_literal(")")
        _t1580 = logic_pb2.Cast(input=term918, result=term_3919)
        result921 = _t1580
        self.record_span(span_start920)
        return result921

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        span_start926 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs922 = []
        cond923 = self.match_lookahead_literal("(", 0)
        while cond923:
            _t1581 = self.parse_attribute()
            item924 = _t1581
            xs922.append(item924)
            cond923 = self.match_lookahead_literal("(", 0)
        attributes925 = xs922
        self.consume_literal(")")
        result927 = attributes925
        self.record_span(span_start926)
        return result927

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start933 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1582 = self.parse_name()
        name928 = _t1582
        xs929 = []
        cond930 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond930:
            _t1583 = self.parse_value()
            item931 = _t1583
            xs929.append(item931)
            cond930 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        values932 = xs929
        self.consume_literal(")")
        _t1584 = logic_pb2.Attribute(name=name928, args=values932)
        result934 = _t1584
        self.record_span(span_start933)
        return result934

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start940 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs935 = []
        cond936 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond936:
            _t1585 = self.parse_relation_id()
            item937 = _t1585
            xs935.append(item937)
            cond936 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids938 = xs935
        _t1586 = self.parse_script()
        script939 = _t1586
        self.consume_literal(")")
        _t1587 = logic_pb2.Algorithm(body=script939)
        getattr(_t1587, 'global').extend(relation_ids938)
        result941 = _t1587
        self.record_span(span_start940)
        return result941

    def parse_script(self) -> logic_pb2.Script:
        span_start946 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs942 = []
        cond943 = self.match_lookahead_literal("(", 0)
        while cond943:
            _t1588 = self.parse_construct()
            item944 = _t1588
            xs942.append(item944)
            cond943 = self.match_lookahead_literal("(", 0)
        constructs945 = xs942
        self.consume_literal(")")
        _t1589 = logic_pb2.Script(constructs=constructs945)
        result947 = _t1589
        self.record_span(span_start946)
        return result947

    def parse_construct(self) -> logic_pb2.Construct:
        span_start951 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1591 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1592 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1593 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1594 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1595 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1596 = 1
                                else:
                                    _t1596 = -1
                                _t1595 = _t1596
                            _t1594 = _t1595
                        _t1593 = _t1594
                    _t1592 = _t1593
                _t1591 = _t1592
            _t1590 = _t1591
        else:
            _t1590 = -1
        prediction948 = _t1590
        if prediction948 == 1:
            _t1598 = self.parse_instruction()
            instruction950 = _t1598
            _t1599 = logic_pb2.Construct(instruction=instruction950)
            _t1597 = _t1599
        else:
            if prediction948 == 0:
                _t1601 = self.parse_loop()
                loop949 = _t1601
                _t1602 = logic_pb2.Construct(loop=loop949)
                _t1600 = _t1602
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1597 = _t1600
        result952 = _t1597
        self.record_span(span_start951)
        return result952

    def parse_loop(self) -> logic_pb2.Loop:
        span_start955 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1603 = self.parse_init()
        init953 = _t1603
        _t1604 = self.parse_script()
        script954 = _t1604
        self.consume_literal(")")
        _t1605 = logic_pb2.Loop(init=init953, body=script954)
        result956 = _t1605
        self.record_span(span_start955)
        return result956

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        span_start961 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("init")
        xs957 = []
        cond958 = self.match_lookahead_literal("(", 0)
        while cond958:
            _t1606 = self.parse_instruction()
            item959 = _t1606
            xs957.append(item959)
            cond958 = self.match_lookahead_literal("(", 0)
        instructions960 = xs957
        self.consume_literal(")")
        result962 = instructions960
        self.record_span(span_start961)
        return result962

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start969 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1608 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1609 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1610 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1611 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1612 = 0
                            else:
                                _t1612 = -1
                            _t1611 = _t1612
                        _t1610 = _t1611
                    _t1609 = _t1610
                _t1608 = _t1609
            _t1607 = _t1608
        else:
            _t1607 = -1
        prediction963 = _t1607
        if prediction963 == 4:
            _t1614 = self.parse_monus_def()
            monus_def968 = _t1614
            _t1615 = logic_pb2.Instruction(monus_def=monus_def968)
            _t1613 = _t1615
        else:
            if prediction963 == 3:
                _t1617 = self.parse_monoid_def()
                monoid_def967 = _t1617
                _t1618 = logic_pb2.Instruction(monoid_def=monoid_def967)
                _t1616 = _t1618
            else:
                if prediction963 == 2:
                    _t1620 = self.parse_break()
                    break966 = _t1620
                    _t1621 = logic_pb2.Instruction()
                    getattr(_t1621, 'break').CopyFrom(break966)
                    _t1619 = _t1621
                else:
                    if prediction963 == 1:
                        _t1623 = self.parse_upsert()
                        upsert965 = _t1623
                        _t1624 = logic_pb2.Instruction(upsert=upsert965)
                        _t1622 = _t1624
                    else:
                        if prediction963 == 0:
                            _t1626 = self.parse_assign()
                            assign964 = _t1626
                            _t1627 = logic_pb2.Instruction(assign=assign964)
                            _t1625 = _t1627
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1622 = _t1625
                    _t1619 = _t1622
                _t1616 = _t1619
            _t1613 = _t1616
        result970 = _t1613
        self.record_span(span_start969)
        return result970

    def parse_assign(self) -> logic_pb2.Assign:
        span_start974 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1628 = self.parse_relation_id()
        relation_id971 = _t1628
        _t1629 = self.parse_abstraction()
        abstraction972 = _t1629
        if self.match_lookahead_literal("(", 0):
            _t1631 = self.parse_attrs()
            _t1630 = _t1631
        else:
            _t1630 = None
        attrs973 = _t1630
        self.consume_literal(")")
        _t1632 = logic_pb2.Assign(name=relation_id971, body=abstraction972, attrs=(attrs973 if attrs973 is not None else []))
        result975 = _t1632
        self.record_span(span_start974)
        return result975

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start979 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1633 = self.parse_relation_id()
        relation_id976 = _t1633
        _t1634 = self.parse_abstraction_with_arity()
        abstraction_with_arity977 = _t1634
        if self.match_lookahead_literal("(", 0):
            _t1636 = self.parse_attrs()
            _t1635 = _t1636
        else:
            _t1635 = None
        attrs978 = _t1635
        self.consume_literal(")")
        _t1637 = logic_pb2.Upsert(name=relation_id976, body=abstraction_with_arity977[0], attrs=(attrs978 if attrs978 is not None else []), value_arity=abstraction_with_arity977[1])
        result980 = _t1637
        self.record_span(span_start979)
        return result980

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        span_start983 = self.span_start()
        self.consume_literal("(")
        _t1638 = self.parse_bindings()
        bindings981 = _t1638
        _t1639 = self.parse_formula()
        formula982 = _t1639
        self.consume_literal(")")
        _t1640 = logic_pb2.Abstraction(vars=(list(bindings981[0]) + list(bindings981[1] if bindings981[1] is not None else [])), value=formula982)
        result984 = (_t1640, len(bindings981[1]),)
        self.record_span(span_start983)
        return result984

    def parse_break(self) -> logic_pb2.Break:
        span_start988 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1641 = self.parse_relation_id()
        relation_id985 = _t1641
        _t1642 = self.parse_abstraction()
        abstraction986 = _t1642
        if self.match_lookahead_literal("(", 0):
            _t1644 = self.parse_attrs()
            _t1643 = _t1644
        else:
            _t1643 = None
        attrs987 = _t1643
        self.consume_literal(")")
        _t1645 = logic_pb2.Break(name=relation_id985, body=abstraction986, attrs=(attrs987 if attrs987 is not None else []))
        result989 = _t1645
        self.record_span(span_start988)
        return result989

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start994 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1646 = self.parse_monoid()
        monoid990 = _t1646
        _t1647 = self.parse_relation_id()
        relation_id991 = _t1647
        _t1648 = self.parse_abstraction_with_arity()
        abstraction_with_arity992 = _t1648
        if self.match_lookahead_literal("(", 0):
            _t1650 = self.parse_attrs()
            _t1649 = _t1650
        else:
            _t1649 = None
        attrs993 = _t1649
        self.consume_literal(")")
        _t1651 = logic_pb2.MonoidDef(monoid=monoid990, name=relation_id991, body=abstraction_with_arity992[0], attrs=(attrs993 if attrs993 is not None else []), value_arity=abstraction_with_arity992[1])
        result995 = _t1651
        self.record_span(span_start994)
        return result995

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1001 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1653 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1654 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1655 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1656 = 2
                        else:
                            _t1656 = -1
                        _t1655 = _t1656
                    _t1654 = _t1655
                _t1653 = _t1654
            _t1652 = _t1653
        else:
            _t1652 = -1
        prediction996 = _t1652
        if prediction996 == 3:
            _t1658 = self.parse_sum_monoid()
            sum_monoid1000 = _t1658
            _t1659 = logic_pb2.Monoid(sum_monoid=sum_monoid1000)
            _t1657 = _t1659
        else:
            if prediction996 == 2:
                _t1661 = self.parse_max_monoid()
                max_monoid999 = _t1661
                _t1662 = logic_pb2.Monoid(max_monoid=max_monoid999)
                _t1660 = _t1662
            else:
                if prediction996 == 1:
                    _t1664 = self.parse_min_monoid()
                    min_monoid998 = _t1664
                    _t1665 = logic_pb2.Monoid(min_monoid=min_monoid998)
                    _t1663 = _t1665
                else:
                    if prediction996 == 0:
                        _t1667 = self.parse_or_monoid()
                        or_monoid997 = _t1667
                        _t1668 = logic_pb2.Monoid(or_monoid=or_monoid997)
                        _t1666 = _t1668
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1663 = _t1666
                _t1660 = _t1663
            _t1657 = _t1660
        result1002 = _t1657
        self.record_span(span_start1001)
        return result1002

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1003 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1669 = logic_pb2.OrMonoid()
        result1004 = _t1669
        self.record_span(span_start1003)
        return result1004

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1006 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1670 = self.parse_type()
        type1005 = _t1670
        self.consume_literal(")")
        _t1671 = logic_pb2.MinMonoid(type=type1005)
        result1007 = _t1671
        self.record_span(span_start1006)
        return result1007

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1009 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1672 = self.parse_type()
        type1008 = _t1672
        self.consume_literal(")")
        _t1673 = logic_pb2.MaxMonoid(type=type1008)
        result1010 = _t1673
        self.record_span(span_start1009)
        return result1010

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1012 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1674 = self.parse_type()
        type1011 = _t1674
        self.consume_literal(")")
        _t1675 = logic_pb2.SumMonoid(type=type1011)
        result1013 = _t1675
        self.record_span(span_start1012)
        return result1013

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1018 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1676 = self.parse_monoid()
        monoid1014 = _t1676
        _t1677 = self.parse_relation_id()
        relation_id1015 = _t1677
        _t1678 = self.parse_abstraction_with_arity()
        abstraction_with_arity1016 = _t1678
        if self.match_lookahead_literal("(", 0):
            _t1680 = self.parse_attrs()
            _t1679 = _t1680
        else:
            _t1679 = None
        attrs1017 = _t1679
        self.consume_literal(")")
        _t1681 = logic_pb2.MonusDef(monoid=monoid1014, name=relation_id1015, body=abstraction_with_arity1016[0], attrs=(attrs1017 if attrs1017 is not None else []), value_arity=abstraction_with_arity1016[1])
        result1019 = _t1681
        self.record_span(span_start1018)
        return result1019

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1024 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1682 = self.parse_relation_id()
        relation_id1020 = _t1682
        _t1683 = self.parse_abstraction()
        abstraction1021 = _t1683
        _t1684 = self.parse_functional_dependency_keys()
        functional_dependency_keys1022 = _t1684
        _t1685 = self.parse_functional_dependency_values()
        functional_dependency_values1023 = _t1685
        self.consume_literal(")")
        _t1686 = logic_pb2.FunctionalDependency(guard=abstraction1021, keys=functional_dependency_keys1022, values=functional_dependency_values1023)
        _t1687 = logic_pb2.Constraint(name=relation_id1020, functional_dependency=_t1686)
        result1025 = _t1687
        self.record_span(span_start1024)
        return result1025

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        span_start1030 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1026 = []
        cond1027 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1027:
            _t1688 = self.parse_var()
            item1028 = _t1688
            xs1026.append(item1028)
            cond1027 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1029 = xs1026
        self.consume_literal(")")
        result1031 = vars1029
        self.record_span(span_start1030)
        return result1031

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        span_start1036 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("values")
        xs1032 = []
        cond1033 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1033:
            _t1689 = self.parse_var()
            item1034 = _t1689
            xs1032.append(item1034)
            cond1033 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1035 = xs1032
        self.consume_literal(")")
        result1037 = vars1035
        self.record_span(span_start1036)
        return result1037

    def parse_data(self) -> logic_pb2.Data:
        span_start1042 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t1691 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1692 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1693 = 1
                    else:
                        _t1693 = -1
                    _t1692 = _t1693
                _t1691 = _t1692
            _t1690 = _t1691
        else:
            _t1690 = -1
        prediction1038 = _t1690
        if prediction1038 == 2:
            _t1695 = self.parse_csv_data()
            csv_data1041 = _t1695
            _t1696 = logic_pb2.Data(csv_data=csv_data1041)
            _t1694 = _t1696
        else:
            if prediction1038 == 1:
                _t1698 = self.parse_betree_relation()
                betree_relation1040 = _t1698
                _t1699 = logic_pb2.Data(betree_relation=betree_relation1040)
                _t1697 = _t1699
            else:
                if prediction1038 == 0:
                    _t1701 = self.parse_rel_edb()
                    rel_edb1039 = _t1701
                    _t1702 = logic_pb2.Data(rel_edb=rel_edb1039)
                    _t1700 = _t1702
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1697 = _t1700
            _t1694 = _t1697
        result1043 = _t1694
        self.record_span(span_start1042)
        return result1043

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        span_start1047 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("rel_edb")
        _t1703 = self.parse_relation_id()
        relation_id1044 = _t1703
        _t1704 = self.parse_rel_edb_path()
        rel_edb_path1045 = _t1704
        _t1705 = self.parse_rel_edb_types()
        rel_edb_types1046 = _t1705
        self.consume_literal(")")
        _t1706 = logic_pb2.RelEDB(target_id=relation_id1044, path=rel_edb_path1045, types=rel_edb_types1046)
        result1048 = _t1706
        self.record_span(span_start1047)
        return result1048

    def parse_rel_edb_path(self) -> Sequence[str]:
        span_start1053 = self.span_start()
        self.consume_literal("[")
        xs1049 = []
        cond1050 = self.match_lookahead_terminal("STRING", 0)
        while cond1050:
            item1051 = self.consume_terminal("STRING")
            xs1049.append(item1051)
            cond1050 = self.match_lookahead_terminal("STRING", 0)
        strings1052 = xs1049
        self.consume_literal("]")
        result1054 = strings1052
        self.record_span(span_start1053)
        return result1054

    def parse_rel_edb_types(self) -> Sequence[logic_pb2.Type]:
        span_start1059 = self.span_start()
        self.consume_literal("[")
        xs1055 = []
        cond1056 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1056:
            _t1707 = self.parse_type()
            item1057 = _t1707
            xs1055.append(item1057)
            cond1056 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1058 = xs1055
        self.consume_literal("]")
        result1060 = types1058
        self.record_span(span_start1059)
        return result1060

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1063 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1708 = self.parse_relation_id()
        relation_id1061 = _t1708
        _t1709 = self.parse_betree_info()
        betree_info1062 = _t1709
        self.consume_literal(")")
        _t1710 = logic_pb2.BeTreeRelation(name=relation_id1061, relation_info=betree_info1062)
        result1064 = _t1710
        self.record_span(span_start1063)
        return result1064

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1068 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1711 = self.parse_betree_info_key_types()
        betree_info_key_types1065 = _t1711
        _t1712 = self.parse_betree_info_value_types()
        betree_info_value_types1066 = _t1712
        _t1713 = self.parse_config_dict()
        config_dict1067 = _t1713
        self.consume_literal(")")
        _t1714 = self.construct_betree_info(betree_info_key_types1065, betree_info_value_types1066, config_dict1067)
        result1069 = _t1714
        self.record_span(span_start1068)
        return result1069

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        span_start1074 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1070 = []
        cond1071 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1071:
            _t1715 = self.parse_type()
            item1072 = _t1715
            xs1070.append(item1072)
            cond1071 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1073 = xs1070
        self.consume_literal(")")
        result1075 = types1073
        self.record_span(span_start1074)
        return result1075

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        span_start1080 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1076 = []
        cond1077 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1077:
            _t1716 = self.parse_type()
            item1078 = _t1716
            xs1076.append(item1078)
            cond1077 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1079 = xs1076
        self.consume_literal(")")
        result1081 = types1079
        self.record_span(span_start1080)
        return result1081

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1086 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1717 = self.parse_csvlocator()
        csvlocator1082 = _t1717
        _t1718 = self.parse_csv_config()
        csv_config1083 = _t1718
        _t1719 = self.parse_csv_columns()
        csv_columns1084 = _t1719
        _t1720 = self.parse_csv_asof()
        csv_asof1085 = _t1720
        self.consume_literal(")")
        _t1721 = logic_pb2.CSVData(locator=csvlocator1082, config=csv_config1083, columns=csv_columns1084, asof=csv_asof1085)
        result1087 = _t1721
        self.record_span(span_start1086)
        return result1087

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1090 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1723 = self.parse_csv_locator_paths()
            _t1722 = _t1723
        else:
            _t1722 = None
        csv_locator_paths1088 = _t1722
        if self.match_lookahead_literal("(", 0):
            _t1725 = self.parse_csv_locator_inline_data()
            _t1724 = _t1725
        else:
            _t1724 = None
        csv_locator_inline_data1089 = _t1724
        self.consume_literal(")")
        _t1726 = logic_pb2.CSVLocator(paths=(csv_locator_paths1088 if csv_locator_paths1088 is not None else []), inline_data=(csv_locator_inline_data1089 if csv_locator_inline_data1089 is not None else "").encode())
        result1091 = _t1726
        self.record_span(span_start1090)
        return result1091

    def parse_csv_locator_paths(self) -> Sequence[str]:
        span_start1096 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1092 = []
        cond1093 = self.match_lookahead_terminal("STRING", 0)
        while cond1093:
            item1094 = self.consume_terminal("STRING")
            xs1092.append(item1094)
            cond1093 = self.match_lookahead_terminal("STRING", 0)
        strings1095 = xs1092
        self.consume_literal(")")
        result1097 = strings1095
        self.record_span(span_start1096)
        return result1097

    def parse_csv_locator_inline_data(self) -> str:
        span_start1099 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1098 = self.consume_terminal("STRING")
        self.consume_literal(")")
        result1100 = string1098
        self.record_span(span_start1099)
        return result1100

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1102 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1727 = self.parse_config_dict()
        config_dict1101 = _t1727
        self.consume_literal(")")
        _t1728 = self.construct_csv_config(config_dict1101)
        result1103 = _t1728
        self.record_span(span_start1102)
        return result1103

    def parse_csv_columns(self) -> Sequence[logic_pb2.CSVColumn]:
        span_start1108 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1104 = []
        cond1105 = self.match_lookahead_literal("(", 0)
        while cond1105:
            _t1729 = self.parse_csv_column()
            item1106 = _t1729
            xs1104.append(item1106)
            cond1105 = self.match_lookahead_literal("(", 0)
        csv_columns1107 = xs1104
        self.consume_literal(")")
        result1109 = csv_columns1107
        self.record_span(span_start1108)
        return result1109

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        span_start1116 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1110 = self.consume_terminal("STRING")
        _t1730 = self.parse_relation_id()
        relation_id1111 = _t1730
        self.consume_literal("[")
        xs1112 = []
        cond1113 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1113:
            _t1731 = self.parse_type()
            item1114 = _t1731
            xs1112.append(item1114)
            cond1113 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1115 = xs1112
        self.consume_literal("]")
        self.consume_literal(")")
        _t1732 = logic_pb2.CSVColumn(column_name=string1110, target_id=relation_id1111, types=types1115)
        result1117 = _t1732
        self.record_span(span_start1116)
        return result1117

    def parse_csv_asof(self) -> str:
        span_start1119 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("asof")
        string1118 = self.consume_terminal("STRING")
        self.consume_literal(")")
        result1120 = string1118
        self.record_span(span_start1119)
        return result1120

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1122 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1733 = self.parse_fragment_id()
        fragment_id1121 = _t1733
        self.consume_literal(")")
        _t1734 = transactions_pb2.Undefine(fragment_id=fragment_id1121)
        result1123 = _t1734
        self.record_span(span_start1122)
        return result1123

    def parse_context(self) -> transactions_pb2.Context:
        span_start1128 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1124 = []
        cond1125 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1125:
            _t1735 = self.parse_relation_id()
            item1126 = _t1735
            xs1124.append(item1126)
            cond1125 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1127 = xs1124
        self.consume_literal(")")
        _t1736 = transactions_pb2.Context(relations=relation_ids1127)
        result1129 = _t1736
        self.record_span(span_start1128)
        return result1129

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1132 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t1737 = self.parse_rel_edb_path()
        rel_edb_path1130 = _t1737
        _t1738 = self.parse_relation_id()
        relation_id1131 = _t1738
        self.consume_literal(")")
        _t1739 = transactions_pb2.Snapshot(destination_path=rel_edb_path1130, source_relation=relation_id1131)
        result1133 = _t1739
        self.record_span(span_start1132)
        return result1133

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        span_start1138 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1134 = []
        cond1135 = self.match_lookahead_literal("(", 0)
        while cond1135:
            _t1740 = self.parse_read()
            item1136 = _t1740
            xs1134.append(item1136)
            cond1135 = self.match_lookahead_literal("(", 0)
        reads1137 = xs1134
        self.consume_literal(")")
        result1139 = reads1137
        self.record_span(span_start1138)
        return result1139

    def parse_read(self) -> transactions_pb2.Read:
        span_start1146 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1742 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1743 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1744 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1745 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1746 = 3
                            else:
                                _t1746 = -1
                            _t1745 = _t1746
                        _t1744 = _t1745
                    _t1743 = _t1744
                _t1742 = _t1743
            _t1741 = _t1742
        else:
            _t1741 = -1
        prediction1140 = _t1741
        if prediction1140 == 4:
            _t1748 = self.parse_export()
            export1145 = _t1748
            _t1749 = transactions_pb2.Read(export=export1145)
            _t1747 = _t1749
        else:
            if prediction1140 == 3:
                _t1751 = self.parse_abort()
                abort1144 = _t1751
                _t1752 = transactions_pb2.Read(abort=abort1144)
                _t1750 = _t1752
            else:
                if prediction1140 == 2:
                    _t1754 = self.parse_what_if()
                    what_if1143 = _t1754
                    _t1755 = transactions_pb2.Read(what_if=what_if1143)
                    _t1753 = _t1755
                else:
                    if prediction1140 == 1:
                        _t1757 = self.parse_output()
                        output1142 = _t1757
                        _t1758 = transactions_pb2.Read(output=output1142)
                        _t1756 = _t1758
                    else:
                        if prediction1140 == 0:
                            _t1760 = self.parse_demand()
                            demand1141 = _t1760
                            _t1761 = transactions_pb2.Read(demand=demand1141)
                            _t1759 = _t1761
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1756 = _t1759
                    _t1753 = _t1756
                _t1750 = _t1753
            _t1747 = _t1750
        result1147 = _t1747
        self.record_span(span_start1146)
        return result1147

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1149 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1762 = self.parse_relation_id()
        relation_id1148 = _t1762
        self.consume_literal(")")
        _t1763 = transactions_pb2.Demand(relation_id=relation_id1148)
        result1150 = _t1763
        self.record_span(span_start1149)
        return result1150

    def parse_output(self) -> transactions_pb2.Output:
        span_start1153 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t1764 = self.parse_name()
        name1151 = _t1764
        _t1765 = self.parse_relation_id()
        relation_id1152 = _t1765
        self.consume_literal(")")
        _t1766 = transactions_pb2.Output(name=name1151, relation_id=relation_id1152)
        result1154 = _t1766
        self.record_span(span_start1153)
        return result1154

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1157 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1767 = self.parse_name()
        name1155 = _t1767
        _t1768 = self.parse_epoch()
        epoch1156 = _t1768
        self.consume_literal(")")
        _t1769 = transactions_pb2.WhatIf(branch=name1155, epoch=epoch1156)
        result1158 = _t1769
        self.record_span(span_start1157)
        return result1158

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1161 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1771 = self.parse_name()
            _t1770 = _t1771
        else:
            _t1770 = None
        name1159 = _t1770
        _t1772 = self.parse_relation_id()
        relation_id1160 = _t1772
        self.consume_literal(")")
        _t1773 = transactions_pb2.Abort(name=(name1159 if name1159 is not None else "abort"), relation_id=relation_id1160)
        result1162 = _t1773
        self.record_span(span_start1161)
        return result1162

    def parse_export(self) -> transactions_pb2.Export:
        span_start1164 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export")
        _t1774 = self.parse_export_csv_config()
        export_csv_config1163 = _t1774
        self.consume_literal(")")
        _t1775 = transactions_pb2.Export(csv_config=export_csv_config1163)
        result1165 = _t1775
        self.record_span(span_start1164)
        return result1165

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1169 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_csv_config")
        _t1776 = self.parse_export_csv_path()
        export_csv_path1166 = _t1776
        _t1777 = self.parse_export_csv_columns()
        export_csv_columns1167 = _t1777
        _t1778 = self.parse_config_dict()
        config_dict1168 = _t1778
        self.consume_literal(")")
        _t1779 = self.export_csv_config(export_csv_path1166, export_csv_columns1167, config_dict1168)
        result1170 = _t1779
        self.record_span(span_start1169)
        return result1170

    def parse_export_csv_path(self) -> str:
        span_start1172 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("path")
        string1171 = self.consume_terminal("STRING")
        self.consume_literal(")")
        result1173 = string1171
        self.record_span(span_start1172)
        return result1173

    def parse_export_csv_columns(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        span_start1178 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1174 = []
        cond1175 = self.match_lookahead_literal("(", 0)
        while cond1175:
            _t1780 = self.parse_export_csv_column()
            item1176 = _t1780
            xs1174.append(item1176)
            cond1175 = self.match_lookahead_literal("(", 0)
        export_csv_columns1177 = xs1174
        self.consume_literal(")")
        result1179 = export_csv_columns1177
        self.record_span(span_start1178)
        return result1179

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1182 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1180 = self.consume_terminal("STRING")
        _t1781 = self.parse_relation_id()
        relation_id1181 = _t1781
        self.consume_literal(")")
        _t1782 = transactions_pb2.ExportCSVColumn(column_name=string1180, column_data=relation_id1181)
        result1183 = _t1782
        self.record_span(span_start1182)
        return result1183


def parse(input_str: str) -> tuple[Any, dict[tuple[int, ...], Span]]:
    """Parse input string and return (result, provenance) tuple."""
    lexer = Lexer(input_str)
    parser = Parser(lexer.tokens, input_str)
    result = parser.parse_transaction()
    # Check for unconsumed tokens (except EOF)
    if parser.pos < len(parser.tokens):
        remaining_token = parser.lookahead(0)
        if remaining_token.type != "$":
            raise ParseError(f"Unexpected token at end of input: {remaining_token}")
    return result, parser.provenance
