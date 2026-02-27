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

    __slots__ = ("start", "stop", "type_name")

    def __init__(self, start: Location, stop: Location, type_name: str = ""):
        self.start = start
        self.stop = stop
        self.type_name = type_name

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
        self.provenance: dict[int, Span] = {}
        self._line_starts = _compute_line_starts(input_str)

    def _make_location(self, offset: int) -> Location:
        """Convert byte offset to Location with 1-based line/column."""
        line_idx = bisect.bisect_right(self._line_starts, offset) - 1
        col = offset - self._line_starts[line_idx]
        return Location(line_idx + 1, col + 1, offset)

    def span_start(self) -> int:
        """Return the start offset of the current token."""
        return self.lookahead(0).start_pos

    def record_span(self, start_offset: int, type_name: str = "") -> None:
        """Record a span from start_offset to the previous token's end.

        Uses first-wins semantics: the innermost parse function records first,
        and outer wrappers that share the same offset do not overwrite.
        """
        if start_offset in self.provenance:
            return
        if self.pos > 0:
            end_offset = self.tokens[self.pos - 1].end_pos
        else:
            end_offset = start_offset
        span = Span(self._make_location(start_offset), self._make_location(end_offset), type_name)
        self.provenance[start_offset] = span

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
            _t1758 = value.HasField("int_value")
        else:
            _t1758 = False
        if _t1758:
            assert value is not None
            return int(value.int_value)
        else:
            _t1759 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t1760 = value.HasField("int_value")
        else:
            _t1760 = False
        if _t1760:
            assert value is not None
            return value.int_value
        else:
            _t1761 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t1762 = value.HasField("string_value")
        else:
            _t1762 = False
        if _t1762:
            assert value is not None
            return value.string_value
        else:
            _t1763 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1764 = value.HasField("boolean_value")
        else:
            _t1764 = False
        if _t1764:
            assert value is not None
            return value.boolean_value
        else:
            _t1765 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1766 = value.HasField("string_value")
        else:
            _t1766 = False
        if _t1766:
            assert value is not None
            return [value.string_value]
        else:
            _t1767 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t1768 = value.HasField("int_value")
        else:
            _t1768 = False
        if _t1768:
            assert value is not None
            return value.int_value
        else:
            _t1769 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t1770 = value.HasField("float_value")
        else:
            _t1770 = False
        if _t1770:
            assert value is not None
            return value.float_value
        else:
            _t1771 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t1772 = value.HasField("string_value")
        else:
            _t1772 = False
        if _t1772:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1773 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t1774 = value.HasField("uint128_value")
        else:
            _t1774 = False
        if _t1774:
            assert value is not None
            return value.uint128_value
        else:
            _t1775 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1776 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1776
        _t1777 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1777
        _t1778 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1778
        _t1779 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1779
        _t1780 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1780
        _t1781 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1781
        _t1782 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1782
        _t1783 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1783
        _t1784 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1784
        _t1785 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1785
        _t1786 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1786
        _t1787 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t1787
        _t1788 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t1788

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1789 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1789
        _t1790 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1790
        _t1791 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1791
        _t1792 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1792
        _t1793 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1793
        _t1794 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1794
        _t1795 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1795
        _t1796 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1796
        _t1797 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1797
        _t1798 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1798
        _t1799 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1799

    def default_configure(self) -> transactions_pb2.Configure:
        _t1800 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1800
        _t1801 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1801

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
        _t1802 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1802
        _t1803 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1803
        _t1804 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1804

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1805 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1805
        _t1806 = self._extract_value_string(config.get("compression"), "")
        compression = _t1806
        _t1807 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1807
        _t1808 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1808
        _t1809 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1809
        _t1810 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1810
        _t1811 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1811
        _t1812 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1812

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t1813 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t1813

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start572 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1133 = self.parse_configure()
            _t1132 = _t1133
        else:
            _t1132 = None
        configure566 = _t1132
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1135 = self.parse_sync()
            _t1134 = _t1135
        else:
            _t1134 = None
        sync567 = _t1134
        xs568 = []
        cond569 = self.match_lookahead_literal("(", 0)
        while cond569:
            _t1136 = self.parse_epoch()
            item570 = _t1136
            xs568.append(item570)
            cond569 = self.match_lookahead_literal("(", 0)
        epochs571 = xs568
        self.consume_literal(")")
        _t1137 = self.default_configure()
        _t1138 = transactions_pb2.Transaction(epochs=epochs571, configure=(configure566 if configure566 is not None else _t1137), sync=sync567)
        result573 = _t1138
        self.record_span(span_start572, "Transaction")
        return result573

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start575 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1139 = self.parse_config_dict()
        config_dict574 = _t1139
        self.consume_literal(")")
        _t1140 = self.construct_configure(config_dict574)
        result576 = _t1140
        self.record_span(span_start575, "Configure")
        return result576

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs577 = []
        cond578 = self.match_lookahead_literal(":", 0)
        while cond578:
            _t1141 = self.parse_config_key_value()
            item579 = _t1141
            xs577.append(item579)
            cond578 = self.match_lookahead_literal(":", 0)
        config_key_values580 = xs577
        self.consume_literal("}")
        return config_key_values580

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol581 = self.consume_terminal("SYMBOL")
        _t1142 = self.parse_value()
        value582 = _t1142
        return (symbol581, value582,)

    def parse_value(self) -> logic_pb2.Value:
        span_start593 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1143 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1144 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1145 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1147 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1148 = 0
                            else:
                                _t1148 = -1
                            _t1147 = _t1148
                        _t1146 = _t1147
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1149 = 5
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t1150 = 2
                            else:
                                if self.match_lookahead_terminal("INT128", 0):
                                    _t1151 = 6
                                else:
                                    if self.match_lookahead_terminal("INT", 0):
                                        _t1152 = 3
                                    else:
                                        if self.match_lookahead_terminal("FLOAT", 0):
                                            _t1153 = 4
                                        else:
                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                _t1154 = 7
                                            else:
                                                _t1154 = -1
                                            _t1153 = _t1154
                                        _t1152 = _t1153
                                    _t1151 = _t1152
                                _t1150 = _t1151
                            _t1149 = _t1150
                        _t1146 = _t1149
                    _t1145 = _t1146
                _t1144 = _t1145
            _t1143 = _t1144
        prediction583 = _t1143
        if prediction583 == 9:
            _t1156 = self.parse_boolean_value()
            boolean_value592 = _t1156
            _t1157 = logic_pb2.Value(boolean_value=boolean_value592)
            _t1155 = _t1157
        else:
            if prediction583 == 8:
                self.consume_literal("missing")
                _t1159 = logic_pb2.MissingValue()
                _t1160 = logic_pb2.Value(missing_value=_t1159)
                _t1158 = _t1160
            else:
                if prediction583 == 7:
                    decimal591 = self.consume_terminal("DECIMAL")
                    _t1162 = logic_pb2.Value(decimal_value=decimal591)
                    _t1161 = _t1162
                else:
                    if prediction583 == 6:
                        int128590 = self.consume_terminal("INT128")
                        _t1164 = logic_pb2.Value(int128_value=int128590)
                        _t1163 = _t1164
                    else:
                        if prediction583 == 5:
                            uint128589 = self.consume_terminal("UINT128")
                            _t1166 = logic_pb2.Value(uint128_value=uint128589)
                            _t1165 = _t1166
                        else:
                            if prediction583 == 4:
                                float588 = self.consume_terminal("FLOAT")
                                _t1168 = logic_pb2.Value(float_value=float588)
                                _t1167 = _t1168
                            else:
                                if prediction583 == 3:
                                    int587 = self.consume_terminal("INT")
                                    _t1170 = logic_pb2.Value(int_value=int587)
                                    _t1169 = _t1170
                                else:
                                    if prediction583 == 2:
                                        string586 = self.consume_terminal("STRING")
                                        _t1172 = logic_pb2.Value(string_value=string586)
                                        _t1171 = _t1172
                                    else:
                                        if prediction583 == 1:
                                            _t1174 = self.parse_datetime()
                                            datetime585 = _t1174
                                            _t1175 = logic_pb2.Value(datetime_value=datetime585)
                                            _t1173 = _t1175
                                        else:
                                            if prediction583 == 0:
                                                _t1177 = self.parse_date()
                                                date584 = _t1177
                                                _t1178 = logic_pb2.Value(date_value=date584)
                                                _t1176 = _t1178
                                            else:
                                                raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1173 = _t1176
                                        _t1171 = _t1173
                                    _t1169 = _t1171
                                _t1167 = _t1169
                            _t1165 = _t1167
                        _t1163 = _t1165
                    _t1161 = _t1163
                _t1158 = _t1161
            _t1155 = _t1158
        result594 = _t1155
        self.record_span(span_start593, "Value")
        return result594

    def parse_date(self) -> logic_pb2.DateValue:
        span_start598 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int595 = self.consume_terminal("INT")
        int_3596 = self.consume_terminal("INT")
        int_4597 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1179 = logic_pb2.DateValue(year=int(int595), month=int(int_3596), day=int(int_4597))
        result599 = _t1179
        self.record_span(span_start598, "DateValue")
        return result599

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start607 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int600 = self.consume_terminal("INT")
        int_3601 = self.consume_terminal("INT")
        int_4602 = self.consume_terminal("INT")
        int_5603 = self.consume_terminal("INT")
        int_6604 = self.consume_terminal("INT")
        int_7605 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1180 = self.consume_terminal("INT")
        else:
            _t1180 = None
        int_8606 = _t1180
        self.consume_literal(")")
        _t1181 = logic_pb2.DateTimeValue(year=int(int600), month=int(int_3601), day=int(int_4602), hour=int(int_5603), minute=int(int_6604), second=int(int_7605), microsecond=int((int_8606 if int_8606 is not None else 0)))
        result608 = _t1181
        self.record_span(span_start607, "DateTimeValue")
        return result608

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1182 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1183 = 1
            else:
                _t1183 = -1
            _t1182 = _t1183
        prediction609 = _t1182
        if prediction609 == 1:
            self.consume_literal("false")
            _t1184 = False
        else:
            if prediction609 == 0:
                self.consume_literal("true")
                _t1185 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1184 = _t1185
        return _t1184

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start614 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs610 = []
        cond611 = self.match_lookahead_literal(":", 0)
        while cond611:
            _t1186 = self.parse_fragment_id()
            item612 = _t1186
            xs610.append(item612)
            cond611 = self.match_lookahead_literal(":", 0)
        fragment_ids613 = xs610
        self.consume_literal(")")
        _t1187 = transactions_pb2.Sync(fragments=fragment_ids613)
        result615 = _t1187
        self.record_span(span_start614, "Sync")
        return result615

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start617 = self.span_start()
        self.consume_literal(":")
        symbol616 = self.consume_terminal("SYMBOL")
        result618 = fragments_pb2.FragmentId(id=symbol616.encode())
        self.record_span(span_start617, "FragmentId")
        return result618

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start621 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1189 = self.parse_epoch_writes()
            _t1188 = _t1189
        else:
            _t1188 = None
        epoch_writes619 = _t1188
        if self.match_lookahead_literal("(", 0):
            _t1191 = self.parse_epoch_reads()
            _t1190 = _t1191
        else:
            _t1190 = None
        epoch_reads620 = _t1190
        self.consume_literal(")")
        _t1192 = transactions_pb2.Epoch(writes=(epoch_writes619 if epoch_writes619 is not None else []), reads=(epoch_reads620 if epoch_reads620 is not None else []))
        result622 = _t1192
        self.record_span(span_start621, "Epoch")
        return result622

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs623 = []
        cond624 = self.match_lookahead_literal("(", 0)
        while cond624:
            _t1193 = self.parse_write()
            item625 = _t1193
            xs623.append(item625)
            cond624 = self.match_lookahead_literal("(", 0)
        writes626 = xs623
        self.consume_literal(")")
        return writes626

    def parse_write(self) -> transactions_pb2.Write:
        span_start632 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1195 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1196 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1197 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1198 = 2
                        else:
                            _t1198 = -1
                        _t1197 = _t1198
                    _t1196 = _t1197
                _t1195 = _t1196
            _t1194 = _t1195
        else:
            _t1194 = -1
        prediction627 = _t1194
        if prediction627 == 3:
            _t1200 = self.parse_snapshot()
            snapshot631 = _t1200
            _t1201 = transactions_pb2.Write(snapshot=snapshot631)
            _t1199 = _t1201
        else:
            if prediction627 == 2:
                _t1203 = self.parse_context()
                context630 = _t1203
                _t1204 = transactions_pb2.Write(context=context630)
                _t1202 = _t1204
            else:
                if prediction627 == 1:
                    _t1206 = self.parse_undefine()
                    undefine629 = _t1206
                    _t1207 = transactions_pb2.Write(undefine=undefine629)
                    _t1205 = _t1207
                else:
                    if prediction627 == 0:
                        _t1209 = self.parse_define()
                        define628 = _t1209
                        _t1210 = transactions_pb2.Write(define=define628)
                        _t1208 = _t1210
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1205 = _t1208
                _t1202 = _t1205
            _t1199 = _t1202
        result633 = _t1199
        self.record_span(span_start632, "Write")
        return result633

    def parse_define(self) -> transactions_pb2.Define:
        span_start635 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1211 = self.parse_fragment()
        fragment634 = _t1211
        self.consume_literal(")")
        _t1212 = transactions_pb2.Define(fragment=fragment634)
        result636 = _t1212
        self.record_span(span_start635, "Define")
        return result636

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start642 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1213 = self.parse_new_fragment_id()
        new_fragment_id637 = _t1213
        xs638 = []
        cond639 = self.match_lookahead_literal("(", 0)
        while cond639:
            _t1214 = self.parse_declaration()
            item640 = _t1214
            xs638.append(item640)
            cond639 = self.match_lookahead_literal("(", 0)
        declarations641 = xs638
        self.consume_literal(")")
        result643 = self.construct_fragment(new_fragment_id637, declarations641)
        self.record_span(span_start642, "Fragment")
        return result643

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start645 = self.span_start()
        _t1215 = self.parse_fragment_id()
        fragment_id644 = _t1215
        self.start_fragment(fragment_id644)
        result646 = fragment_id644
        self.record_span(span_start645, "FragmentId")
        return result646

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start652 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("functional_dependency", 1):
                _t1217 = 2
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1218 = 3
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t1219 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t1220 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t1221 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t1222 = 1
                                else:
                                    _t1222 = -1
                                _t1221 = _t1222
                            _t1220 = _t1221
                        _t1219 = _t1220
                    _t1218 = _t1219
                _t1217 = _t1218
            _t1216 = _t1217
        else:
            _t1216 = -1
        prediction647 = _t1216
        if prediction647 == 3:
            _t1224 = self.parse_data()
            data651 = _t1224
            _t1225 = logic_pb2.Declaration(data=data651)
            _t1223 = _t1225
        else:
            if prediction647 == 2:
                _t1227 = self.parse_constraint()
                constraint650 = _t1227
                _t1228 = logic_pb2.Declaration(constraint=constraint650)
                _t1226 = _t1228
            else:
                if prediction647 == 1:
                    _t1230 = self.parse_algorithm()
                    algorithm649 = _t1230
                    _t1231 = logic_pb2.Declaration(algorithm=algorithm649)
                    _t1229 = _t1231
                else:
                    if prediction647 == 0:
                        _t1233 = self.parse_def()
                        def648 = _t1233
                        _t1234 = logic_pb2.Declaration()
                        getattr(_t1234, 'def').CopyFrom(def648)
                        _t1232 = _t1234
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1229 = _t1232
                _t1226 = _t1229
            _t1223 = _t1226
        result653 = _t1223
        self.record_span(span_start652, "Declaration")
        return result653

    def parse_def(self) -> logic_pb2.Def:
        span_start657 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1235 = self.parse_relation_id()
        relation_id654 = _t1235
        _t1236 = self.parse_abstraction()
        abstraction655 = _t1236
        if self.match_lookahead_literal("(", 0):
            _t1238 = self.parse_attrs()
            _t1237 = _t1238
        else:
            _t1237 = None
        attrs656 = _t1237
        self.consume_literal(")")
        _t1239 = logic_pb2.Def(name=relation_id654, body=abstraction655, attrs=(attrs656 if attrs656 is not None else []))
        result658 = _t1239
        self.record_span(span_start657, "Def")
        return result658

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start662 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1240 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1241 = 1
            else:
                _t1241 = -1
            _t1240 = _t1241
        prediction659 = _t1240
        if prediction659 == 1:
            uint128661 = self.consume_terminal("UINT128")
            _t1242 = logic_pb2.RelationId(id_low=uint128661.low, id_high=uint128661.high)
        else:
            if prediction659 == 0:
                self.consume_literal(":")
                symbol660 = self.consume_terminal("SYMBOL")
                _t1243 = self.relation_id_from_string(symbol660)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1242 = _t1243
        result663 = _t1242
        self.record_span(span_start662, "RelationId")
        return result663

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start666 = self.span_start()
        self.consume_literal("(")
        _t1244 = self.parse_bindings()
        bindings664 = _t1244
        _t1245 = self.parse_formula()
        formula665 = _t1245
        self.consume_literal(")")
        _t1246 = logic_pb2.Abstraction(vars=(list(bindings664[0]) + list(bindings664[1] if bindings664[1] is not None else [])), value=formula665)
        result667 = _t1246
        self.record_span(span_start666, "Abstraction")
        return result667

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs668 = []
        cond669 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond669:
            _t1247 = self.parse_binding()
            item670 = _t1247
            xs668.append(item670)
            cond669 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings671 = xs668
        if self.match_lookahead_literal("|", 0):
            _t1249 = self.parse_value_bindings()
            _t1248 = _t1249
        else:
            _t1248 = None
        value_bindings672 = _t1248
        self.consume_literal("]")
        return (bindings671, (value_bindings672 if value_bindings672 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start675 = self.span_start()
        symbol673 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1250 = self.parse_type()
        type674 = _t1250
        _t1251 = logic_pb2.Var(name=symbol673)
        _t1252 = logic_pb2.Binding(var=_t1251, type=type674)
        result676 = _t1252
        self.record_span(span_start675, "Binding")
        return result676

    def parse_type(self) -> logic_pb2.Type:
        span_start689 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1253 = 0
        else:
            if self.match_lookahead_literal("UINT128", 0):
                _t1254 = 4
            else:
                if self.match_lookahead_literal("STRING", 0):
                    _t1255 = 1
                else:
                    if self.match_lookahead_literal("MISSING", 0):
                        _t1256 = 8
                    else:
                        if self.match_lookahead_literal("INT128", 0):
                            _t1257 = 5
                        else:
                            if self.match_lookahead_literal("INT", 0):
                                _t1258 = 2
                            else:
                                if self.match_lookahead_literal("FLOAT", 0):
                                    _t1259 = 3
                                else:
                                    if self.match_lookahead_literal("DATETIME", 0):
                                        _t1260 = 7
                                    else:
                                        if self.match_lookahead_literal("DATE", 0):
                                            _t1261 = 6
                                        else:
                                            if self.match_lookahead_literal("BOOLEAN", 0):
                                                _t1262 = 10
                                            else:
                                                if self.match_lookahead_literal("(", 0):
                                                    _t1263 = 9
                                                else:
                                                    _t1263 = -1
                                                _t1262 = _t1263
                                            _t1261 = _t1262
                                        _t1260 = _t1261
                                    _t1259 = _t1260
                                _t1258 = _t1259
                            _t1257 = _t1258
                        _t1256 = _t1257
                    _t1255 = _t1256
                _t1254 = _t1255
            _t1253 = _t1254
        prediction677 = _t1253
        if prediction677 == 10:
            _t1265 = self.parse_boolean_type()
            boolean_type688 = _t1265
            _t1266 = logic_pb2.Type(boolean_type=boolean_type688)
            _t1264 = _t1266
        else:
            if prediction677 == 9:
                _t1268 = self.parse_decimal_type()
                decimal_type687 = _t1268
                _t1269 = logic_pb2.Type(decimal_type=decimal_type687)
                _t1267 = _t1269
            else:
                if prediction677 == 8:
                    _t1271 = self.parse_missing_type()
                    missing_type686 = _t1271
                    _t1272 = logic_pb2.Type(missing_type=missing_type686)
                    _t1270 = _t1272
                else:
                    if prediction677 == 7:
                        _t1274 = self.parse_datetime_type()
                        datetime_type685 = _t1274
                        _t1275 = logic_pb2.Type(datetime_type=datetime_type685)
                        _t1273 = _t1275
                    else:
                        if prediction677 == 6:
                            _t1277 = self.parse_date_type()
                            date_type684 = _t1277
                            _t1278 = logic_pb2.Type(date_type=date_type684)
                            _t1276 = _t1278
                        else:
                            if prediction677 == 5:
                                _t1280 = self.parse_int128_type()
                                int128_type683 = _t1280
                                _t1281 = logic_pb2.Type(int128_type=int128_type683)
                                _t1279 = _t1281
                            else:
                                if prediction677 == 4:
                                    _t1283 = self.parse_uint128_type()
                                    uint128_type682 = _t1283
                                    _t1284 = logic_pb2.Type(uint128_type=uint128_type682)
                                    _t1282 = _t1284
                                else:
                                    if prediction677 == 3:
                                        _t1286 = self.parse_float_type()
                                        float_type681 = _t1286
                                        _t1287 = logic_pb2.Type(float_type=float_type681)
                                        _t1285 = _t1287
                                    else:
                                        if prediction677 == 2:
                                            _t1289 = self.parse_int_type()
                                            int_type680 = _t1289
                                            _t1290 = logic_pb2.Type(int_type=int_type680)
                                            _t1288 = _t1290
                                        else:
                                            if prediction677 == 1:
                                                _t1292 = self.parse_string_type()
                                                string_type679 = _t1292
                                                _t1293 = logic_pb2.Type(string_type=string_type679)
                                                _t1291 = _t1293
                                            else:
                                                if prediction677 == 0:
                                                    _t1295 = self.parse_unspecified_type()
                                                    unspecified_type678 = _t1295
                                                    _t1296 = logic_pb2.Type(unspecified_type=unspecified_type678)
                                                    _t1294 = _t1296
                                                else:
                                                    raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t1291 = _t1294
                                            _t1288 = _t1291
                                        _t1285 = _t1288
                                    _t1282 = _t1285
                                _t1279 = _t1282
                            _t1276 = _t1279
                        _t1273 = _t1276
                    _t1270 = _t1273
                _t1267 = _t1270
            _t1264 = _t1267
        result690 = _t1264
        self.record_span(span_start689, "Type")
        return result690

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start691 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1297 = logic_pb2.UnspecifiedType()
        result692 = _t1297
        self.record_span(span_start691, "UnspecifiedType")
        return result692

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start693 = self.span_start()
        self.consume_literal("STRING")
        _t1298 = logic_pb2.StringType()
        result694 = _t1298
        self.record_span(span_start693, "StringType")
        return result694

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start695 = self.span_start()
        self.consume_literal("INT")
        _t1299 = logic_pb2.IntType()
        result696 = _t1299
        self.record_span(span_start695, "IntType")
        return result696

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start697 = self.span_start()
        self.consume_literal("FLOAT")
        _t1300 = logic_pb2.FloatType()
        result698 = _t1300
        self.record_span(span_start697, "FloatType")
        return result698

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start699 = self.span_start()
        self.consume_literal("UINT128")
        _t1301 = logic_pb2.UInt128Type()
        result700 = _t1301
        self.record_span(span_start699, "UInt128Type")
        return result700

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start701 = self.span_start()
        self.consume_literal("INT128")
        _t1302 = logic_pb2.Int128Type()
        result702 = _t1302
        self.record_span(span_start701, "Int128Type")
        return result702

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start703 = self.span_start()
        self.consume_literal("DATE")
        _t1303 = logic_pb2.DateType()
        result704 = _t1303
        self.record_span(span_start703, "DateType")
        return result704

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start705 = self.span_start()
        self.consume_literal("DATETIME")
        _t1304 = logic_pb2.DateTimeType()
        result706 = _t1304
        self.record_span(span_start705, "DateTimeType")
        return result706

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start707 = self.span_start()
        self.consume_literal("MISSING")
        _t1305 = logic_pb2.MissingType()
        result708 = _t1305
        self.record_span(span_start707, "MissingType")
        return result708

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start711 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int709 = self.consume_terminal("INT")
        int_3710 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1306 = logic_pb2.DecimalType(precision=int(int709), scale=int(int_3710))
        result712 = _t1306
        self.record_span(span_start711, "DecimalType")
        return result712

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start713 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1307 = logic_pb2.BooleanType()
        result714 = _t1307
        self.record_span(span_start713, "BooleanType")
        return result714

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs715 = []
        cond716 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond716:
            _t1308 = self.parse_binding()
            item717 = _t1308
            xs715.append(item717)
            cond716 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings718 = xs715
        return bindings718

    def parse_formula(self) -> logic_pb2.Formula:
        span_start733 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1310 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1311 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1312 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1313 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1314 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1315 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1316 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1317 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1318 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1319 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1320 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1321 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1322 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1323 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1324 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1325 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1326 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1327 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1328 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1329 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1330 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1331 = 10
                                                                                                else:
                                                                                                    _t1331 = -1
                                                                                                _t1330 = _t1331
                                                                                            _t1329 = _t1330
                                                                                        _t1328 = _t1329
                                                                                    _t1327 = _t1328
                                                                                _t1326 = _t1327
                                                                            _t1325 = _t1326
                                                                        _t1324 = _t1325
                                                                    _t1323 = _t1324
                                                                _t1322 = _t1323
                                                            _t1321 = _t1322
                                                        _t1320 = _t1321
                                                    _t1319 = _t1320
                                                _t1318 = _t1319
                                            _t1317 = _t1318
                                        _t1316 = _t1317
                                    _t1315 = _t1316
                                _t1314 = _t1315
                            _t1313 = _t1314
                        _t1312 = _t1313
                    _t1311 = _t1312
                _t1310 = _t1311
            _t1309 = _t1310
        else:
            _t1309 = -1
        prediction719 = _t1309
        if prediction719 == 12:
            _t1333 = self.parse_cast()
            cast732 = _t1333
            _t1334 = logic_pb2.Formula(cast=cast732)
            _t1332 = _t1334
        else:
            if prediction719 == 11:
                _t1336 = self.parse_rel_atom()
                rel_atom731 = _t1336
                _t1337 = logic_pb2.Formula(rel_atom=rel_atom731)
                _t1335 = _t1337
            else:
                if prediction719 == 10:
                    _t1339 = self.parse_primitive()
                    primitive730 = _t1339
                    _t1340 = logic_pb2.Formula(primitive=primitive730)
                    _t1338 = _t1340
                else:
                    if prediction719 == 9:
                        _t1342 = self.parse_pragma()
                        pragma729 = _t1342
                        _t1343 = logic_pb2.Formula(pragma=pragma729)
                        _t1341 = _t1343
                    else:
                        if prediction719 == 8:
                            _t1345 = self.parse_atom()
                            atom728 = _t1345
                            _t1346 = logic_pb2.Formula(atom=atom728)
                            _t1344 = _t1346
                        else:
                            if prediction719 == 7:
                                _t1348 = self.parse_ffi()
                                ffi727 = _t1348
                                _t1349 = logic_pb2.Formula(ffi=ffi727)
                                _t1347 = _t1349
                            else:
                                if prediction719 == 6:
                                    _t1351 = self.parse_not()
                                    not726 = _t1351
                                    _t1352 = logic_pb2.Formula()
                                    getattr(_t1352, 'not').CopyFrom(not726)
                                    _t1350 = _t1352
                                else:
                                    if prediction719 == 5:
                                        _t1354 = self.parse_disjunction()
                                        disjunction725 = _t1354
                                        _t1355 = logic_pb2.Formula(disjunction=disjunction725)
                                        _t1353 = _t1355
                                    else:
                                        if prediction719 == 4:
                                            _t1357 = self.parse_conjunction()
                                            conjunction724 = _t1357
                                            _t1358 = logic_pb2.Formula(conjunction=conjunction724)
                                            _t1356 = _t1358
                                        else:
                                            if prediction719 == 3:
                                                _t1360 = self.parse_reduce()
                                                reduce723 = _t1360
                                                _t1361 = logic_pb2.Formula(reduce=reduce723)
                                                _t1359 = _t1361
                                            else:
                                                if prediction719 == 2:
                                                    _t1363 = self.parse_exists()
                                                    exists722 = _t1363
                                                    _t1364 = logic_pb2.Formula(exists=exists722)
                                                    _t1362 = _t1364
                                                else:
                                                    if prediction719 == 1:
                                                        _t1366 = self.parse_false()
                                                        false721 = _t1366
                                                        _t1367 = logic_pb2.Formula(disjunction=false721)
                                                        _t1365 = _t1367
                                                    else:
                                                        if prediction719 == 0:
                                                            _t1369 = self.parse_true()
                                                            true720 = _t1369
                                                            _t1370 = logic_pb2.Formula(conjunction=true720)
                                                            _t1368 = _t1370
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1365 = _t1368
                                                    _t1362 = _t1365
                                                _t1359 = _t1362
                                            _t1356 = _t1359
                                        _t1353 = _t1356
                                    _t1350 = _t1353
                                _t1347 = _t1350
                            _t1344 = _t1347
                        _t1341 = _t1344
                    _t1338 = _t1341
                _t1335 = _t1338
            _t1332 = _t1335
        result734 = _t1332
        self.record_span(span_start733, "Formula")
        return result734

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start735 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1371 = logic_pb2.Conjunction(args=[])
        result736 = _t1371
        self.record_span(span_start735, "Conjunction")
        return result736

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start737 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1372 = logic_pb2.Disjunction(args=[])
        result738 = _t1372
        self.record_span(span_start737, "Disjunction")
        return result738

    def parse_exists(self) -> logic_pb2.Exists:
        span_start741 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1373 = self.parse_bindings()
        bindings739 = _t1373
        _t1374 = self.parse_formula()
        formula740 = _t1374
        self.consume_literal(")")
        _t1375 = logic_pb2.Abstraction(vars=(list(bindings739[0]) + list(bindings739[1] if bindings739[1] is not None else [])), value=formula740)
        _t1376 = logic_pb2.Exists(body=_t1375)
        result742 = _t1376
        self.record_span(span_start741, "Exists")
        return result742

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start746 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1377 = self.parse_abstraction()
        abstraction743 = _t1377
        _t1378 = self.parse_abstraction()
        abstraction_3744 = _t1378
        _t1379 = self.parse_terms()
        terms745 = _t1379
        self.consume_literal(")")
        _t1380 = logic_pb2.Reduce(op=abstraction743, body=abstraction_3744, terms=terms745)
        result747 = _t1380
        self.record_span(span_start746, "Reduce")
        return result747

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs748 = []
        cond749 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond749:
            _t1381 = self.parse_term()
            item750 = _t1381
            xs748.append(item750)
            cond749 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms751 = xs748
        self.consume_literal(")")
        return terms751

    def parse_term(self) -> logic_pb2.Term:
        span_start755 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1382 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1383 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1384 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1385 = 1
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1386 = 1
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1387 = 0
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1388 = 1
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t1389 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t1390 = 1
                                        else:
                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                _t1391 = 1
                                            else:
                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                    _t1392 = 1
                                                else:
                                                    _t1392 = -1
                                                _t1391 = _t1392
                                            _t1390 = _t1391
                                        _t1389 = _t1390
                                    _t1388 = _t1389
                                _t1387 = _t1388
                            _t1386 = _t1387
                        _t1385 = _t1386
                    _t1384 = _t1385
                _t1383 = _t1384
            _t1382 = _t1383
        prediction752 = _t1382
        if prediction752 == 1:
            _t1394 = self.parse_constant()
            constant754 = _t1394
            _t1395 = logic_pb2.Term(constant=constant754)
            _t1393 = _t1395
        else:
            if prediction752 == 0:
                _t1397 = self.parse_var()
                var753 = _t1397
                _t1398 = logic_pb2.Term(var=var753)
                _t1396 = _t1398
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1393 = _t1396
        result756 = _t1393
        self.record_span(span_start755, "Term")
        return result756

    def parse_var(self) -> logic_pb2.Var:
        span_start758 = self.span_start()
        symbol757 = self.consume_terminal("SYMBOL")
        _t1399 = logic_pb2.Var(name=symbol757)
        result759 = _t1399
        self.record_span(span_start758, "Var")
        return result759

    def parse_constant(self) -> logic_pb2.Value:
        span_start761 = self.span_start()
        _t1400 = self.parse_value()
        value760 = _t1400
        result762 = value760
        self.record_span(span_start761, "Value")
        return result762

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start767 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs763 = []
        cond764 = self.match_lookahead_literal("(", 0)
        while cond764:
            _t1401 = self.parse_formula()
            item765 = _t1401
            xs763.append(item765)
            cond764 = self.match_lookahead_literal("(", 0)
        formulas766 = xs763
        self.consume_literal(")")
        _t1402 = logic_pb2.Conjunction(args=formulas766)
        result768 = _t1402
        self.record_span(span_start767, "Conjunction")
        return result768

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start773 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs769 = []
        cond770 = self.match_lookahead_literal("(", 0)
        while cond770:
            _t1403 = self.parse_formula()
            item771 = _t1403
            xs769.append(item771)
            cond770 = self.match_lookahead_literal("(", 0)
        formulas772 = xs769
        self.consume_literal(")")
        _t1404 = logic_pb2.Disjunction(args=formulas772)
        result774 = _t1404
        self.record_span(span_start773, "Disjunction")
        return result774

    def parse_not(self) -> logic_pb2.Not:
        span_start776 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1405 = self.parse_formula()
        formula775 = _t1405
        self.consume_literal(")")
        _t1406 = logic_pb2.Not(arg=formula775)
        result777 = _t1406
        self.record_span(span_start776, "Not")
        return result777

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start781 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1407 = self.parse_name()
        name778 = _t1407
        _t1408 = self.parse_ffi_args()
        ffi_args779 = _t1408
        _t1409 = self.parse_terms()
        terms780 = _t1409
        self.consume_literal(")")
        _t1410 = logic_pb2.FFI(name=name778, args=ffi_args779, terms=terms780)
        result782 = _t1410
        self.record_span(span_start781, "FFI")
        return result782

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol783 = self.consume_terminal("SYMBOL")
        return symbol783

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs784 = []
        cond785 = self.match_lookahead_literal("(", 0)
        while cond785:
            _t1411 = self.parse_abstraction()
            item786 = _t1411
            xs784.append(item786)
            cond785 = self.match_lookahead_literal("(", 0)
        abstractions787 = xs784
        self.consume_literal(")")
        return abstractions787

    def parse_atom(self) -> logic_pb2.Atom:
        span_start793 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1412 = self.parse_relation_id()
        relation_id788 = _t1412
        xs789 = []
        cond790 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond790:
            _t1413 = self.parse_term()
            item791 = _t1413
            xs789.append(item791)
            cond790 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms792 = xs789
        self.consume_literal(")")
        _t1414 = logic_pb2.Atom(name=relation_id788, terms=terms792)
        result794 = _t1414
        self.record_span(span_start793, "Atom")
        return result794

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start800 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1415 = self.parse_name()
        name795 = _t1415
        xs796 = []
        cond797 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond797:
            _t1416 = self.parse_term()
            item798 = _t1416
            xs796.append(item798)
            cond797 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms799 = xs796
        self.consume_literal(")")
        _t1417 = logic_pb2.Pragma(name=name795, terms=terms799)
        result801 = _t1417
        self.record_span(span_start800, "Pragma")
        return result801

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start817 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1419 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1420 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1421 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1422 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1423 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1424 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1425 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1426 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1427 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1428 = 7
                                                else:
                                                    _t1428 = -1
                                                _t1427 = _t1428
                                            _t1426 = _t1427
                                        _t1425 = _t1426
                                    _t1424 = _t1425
                                _t1423 = _t1424
                            _t1422 = _t1423
                        _t1421 = _t1422
                    _t1420 = _t1421
                _t1419 = _t1420
            _t1418 = _t1419
        else:
            _t1418 = -1
        prediction802 = _t1418
        if prediction802 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1430 = self.parse_name()
            name812 = _t1430
            xs813 = []
            cond814 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            while cond814:
                _t1431 = self.parse_rel_term()
                item815 = _t1431
                xs813.append(item815)
                cond814 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            rel_terms816 = xs813
            self.consume_literal(")")
            _t1432 = logic_pb2.Primitive(name=name812, terms=rel_terms816)
            _t1429 = _t1432
        else:
            if prediction802 == 8:
                _t1434 = self.parse_divide()
                divide811 = _t1434
                _t1433 = divide811
            else:
                if prediction802 == 7:
                    _t1436 = self.parse_multiply()
                    multiply810 = _t1436
                    _t1435 = multiply810
                else:
                    if prediction802 == 6:
                        _t1438 = self.parse_minus()
                        minus809 = _t1438
                        _t1437 = minus809
                    else:
                        if prediction802 == 5:
                            _t1440 = self.parse_add()
                            add808 = _t1440
                            _t1439 = add808
                        else:
                            if prediction802 == 4:
                                _t1442 = self.parse_gt_eq()
                                gt_eq807 = _t1442
                                _t1441 = gt_eq807
                            else:
                                if prediction802 == 3:
                                    _t1444 = self.parse_gt()
                                    gt806 = _t1444
                                    _t1443 = gt806
                                else:
                                    if prediction802 == 2:
                                        _t1446 = self.parse_lt_eq()
                                        lt_eq805 = _t1446
                                        _t1445 = lt_eq805
                                    else:
                                        if prediction802 == 1:
                                            _t1448 = self.parse_lt()
                                            lt804 = _t1448
                                            _t1447 = lt804
                                        else:
                                            if prediction802 == 0:
                                                _t1450 = self.parse_eq()
                                                eq803 = _t1450
                                                _t1449 = eq803
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1447 = _t1449
                                        _t1445 = _t1447
                                    _t1443 = _t1445
                                _t1441 = _t1443
                            _t1439 = _t1441
                        _t1437 = _t1439
                    _t1435 = _t1437
                _t1433 = _t1435
            _t1429 = _t1433
        result818 = _t1429
        self.record_span(span_start817, "Primitive")
        return result818

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start821 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1451 = self.parse_term()
        term819 = _t1451
        _t1452 = self.parse_term()
        term_3820 = _t1452
        self.consume_literal(")")
        _t1453 = logic_pb2.RelTerm(term=term819)
        _t1454 = logic_pb2.RelTerm(term=term_3820)
        _t1455 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1453, _t1454])
        result822 = _t1455
        self.record_span(span_start821, "Primitive")
        return result822

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start825 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1456 = self.parse_term()
        term823 = _t1456
        _t1457 = self.parse_term()
        term_3824 = _t1457
        self.consume_literal(")")
        _t1458 = logic_pb2.RelTerm(term=term823)
        _t1459 = logic_pb2.RelTerm(term=term_3824)
        _t1460 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1458, _t1459])
        result826 = _t1460
        self.record_span(span_start825, "Primitive")
        return result826

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start829 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1461 = self.parse_term()
        term827 = _t1461
        _t1462 = self.parse_term()
        term_3828 = _t1462
        self.consume_literal(")")
        _t1463 = logic_pb2.RelTerm(term=term827)
        _t1464 = logic_pb2.RelTerm(term=term_3828)
        _t1465 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1463, _t1464])
        result830 = _t1465
        self.record_span(span_start829, "Primitive")
        return result830

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start833 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1466 = self.parse_term()
        term831 = _t1466
        _t1467 = self.parse_term()
        term_3832 = _t1467
        self.consume_literal(")")
        _t1468 = logic_pb2.RelTerm(term=term831)
        _t1469 = logic_pb2.RelTerm(term=term_3832)
        _t1470 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1468, _t1469])
        result834 = _t1470
        self.record_span(span_start833, "Primitive")
        return result834

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start837 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1471 = self.parse_term()
        term835 = _t1471
        _t1472 = self.parse_term()
        term_3836 = _t1472
        self.consume_literal(")")
        _t1473 = logic_pb2.RelTerm(term=term835)
        _t1474 = logic_pb2.RelTerm(term=term_3836)
        _t1475 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1473, _t1474])
        result838 = _t1475
        self.record_span(span_start837, "Primitive")
        return result838

    def parse_add(self) -> logic_pb2.Primitive:
        span_start842 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1476 = self.parse_term()
        term839 = _t1476
        _t1477 = self.parse_term()
        term_3840 = _t1477
        _t1478 = self.parse_term()
        term_4841 = _t1478
        self.consume_literal(")")
        _t1479 = logic_pb2.RelTerm(term=term839)
        _t1480 = logic_pb2.RelTerm(term=term_3840)
        _t1481 = logic_pb2.RelTerm(term=term_4841)
        _t1482 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1479, _t1480, _t1481])
        result843 = _t1482
        self.record_span(span_start842, "Primitive")
        return result843

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start847 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1483 = self.parse_term()
        term844 = _t1483
        _t1484 = self.parse_term()
        term_3845 = _t1484
        _t1485 = self.parse_term()
        term_4846 = _t1485
        self.consume_literal(")")
        _t1486 = logic_pb2.RelTerm(term=term844)
        _t1487 = logic_pb2.RelTerm(term=term_3845)
        _t1488 = logic_pb2.RelTerm(term=term_4846)
        _t1489 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1486, _t1487, _t1488])
        result848 = _t1489
        self.record_span(span_start847, "Primitive")
        return result848

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start852 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1490 = self.parse_term()
        term849 = _t1490
        _t1491 = self.parse_term()
        term_3850 = _t1491
        _t1492 = self.parse_term()
        term_4851 = _t1492
        self.consume_literal(")")
        _t1493 = logic_pb2.RelTerm(term=term849)
        _t1494 = logic_pb2.RelTerm(term=term_3850)
        _t1495 = logic_pb2.RelTerm(term=term_4851)
        _t1496 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1493, _t1494, _t1495])
        result853 = _t1496
        self.record_span(span_start852, "Primitive")
        return result853

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start857 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1497 = self.parse_term()
        term854 = _t1497
        _t1498 = self.parse_term()
        term_3855 = _t1498
        _t1499 = self.parse_term()
        term_4856 = _t1499
        self.consume_literal(")")
        _t1500 = logic_pb2.RelTerm(term=term854)
        _t1501 = logic_pb2.RelTerm(term=term_3855)
        _t1502 = logic_pb2.RelTerm(term=term_4856)
        _t1503 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1500, _t1501, _t1502])
        result858 = _t1503
        self.record_span(span_start857, "Primitive")
        return result858

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start862 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1504 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1505 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1506 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1507 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1508 = 0
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1509 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1510 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1511 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1512 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1513 = 1
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1514 = 1
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1515 = 1
                                                    else:
                                                        _t1515 = -1
                                                    _t1514 = _t1515
                                                _t1513 = _t1514
                                            _t1512 = _t1513
                                        _t1511 = _t1512
                                    _t1510 = _t1511
                                _t1509 = _t1510
                            _t1508 = _t1509
                        _t1507 = _t1508
                    _t1506 = _t1507
                _t1505 = _t1506
            _t1504 = _t1505
        prediction859 = _t1504
        if prediction859 == 1:
            _t1517 = self.parse_term()
            term861 = _t1517
            _t1518 = logic_pb2.RelTerm(term=term861)
            _t1516 = _t1518
        else:
            if prediction859 == 0:
                _t1520 = self.parse_specialized_value()
                specialized_value860 = _t1520
                _t1521 = logic_pb2.RelTerm(specialized_value=specialized_value860)
                _t1519 = _t1521
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1516 = _t1519
        result863 = _t1516
        self.record_span(span_start862, "RelTerm")
        return result863

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start865 = self.span_start()
        self.consume_literal("#")
        _t1522 = self.parse_value()
        value864 = _t1522
        result866 = value864
        self.record_span(span_start865, "Value")
        return result866

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start872 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1523 = self.parse_name()
        name867 = _t1523
        xs868 = []
        cond869 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond869:
            _t1524 = self.parse_rel_term()
            item870 = _t1524
            xs868.append(item870)
            cond869 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        rel_terms871 = xs868
        self.consume_literal(")")
        _t1525 = logic_pb2.RelAtom(name=name867, terms=rel_terms871)
        result873 = _t1525
        self.record_span(span_start872, "RelAtom")
        return result873

    def parse_cast(self) -> logic_pb2.Cast:
        span_start876 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1526 = self.parse_term()
        term874 = _t1526
        _t1527 = self.parse_term()
        term_3875 = _t1527
        self.consume_literal(")")
        _t1528 = logic_pb2.Cast(input=term874, result=term_3875)
        result877 = _t1528
        self.record_span(span_start876, "Cast")
        return result877

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs878 = []
        cond879 = self.match_lookahead_literal("(", 0)
        while cond879:
            _t1529 = self.parse_attribute()
            item880 = _t1529
            xs878.append(item880)
            cond879 = self.match_lookahead_literal("(", 0)
        attributes881 = xs878
        self.consume_literal(")")
        return attributes881

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start887 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1530 = self.parse_name()
        name882 = _t1530
        xs883 = []
        cond884 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond884:
            _t1531 = self.parse_value()
            item885 = _t1531
            xs883.append(item885)
            cond884 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        values886 = xs883
        self.consume_literal(")")
        _t1532 = logic_pb2.Attribute(name=name882, args=values886)
        result888 = _t1532
        self.record_span(span_start887, "Attribute")
        return result888

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start894 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs889 = []
        cond890 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond890:
            _t1533 = self.parse_relation_id()
            item891 = _t1533
            xs889.append(item891)
            cond890 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids892 = xs889
        _t1534 = self.parse_script()
        script893 = _t1534
        self.consume_literal(")")
        _t1535 = logic_pb2.Algorithm(body=script893)
        getattr(_t1535, 'global').extend(relation_ids892)
        result895 = _t1535
        self.record_span(span_start894, "Algorithm")
        return result895

    def parse_script(self) -> logic_pb2.Script:
        span_start900 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs896 = []
        cond897 = self.match_lookahead_literal("(", 0)
        while cond897:
            _t1536 = self.parse_construct()
            item898 = _t1536
            xs896.append(item898)
            cond897 = self.match_lookahead_literal("(", 0)
        constructs899 = xs896
        self.consume_literal(")")
        _t1537 = logic_pb2.Script(constructs=constructs899)
        result901 = _t1537
        self.record_span(span_start900, "Script")
        return result901

    def parse_construct(self) -> logic_pb2.Construct:
        span_start905 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1539 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1540 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1541 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1542 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1543 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1544 = 1
                                else:
                                    _t1544 = -1
                                _t1543 = _t1544
                            _t1542 = _t1543
                        _t1541 = _t1542
                    _t1540 = _t1541
                _t1539 = _t1540
            _t1538 = _t1539
        else:
            _t1538 = -1
        prediction902 = _t1538
        if prediction902 == 1:
            _t1546 = self.parse_instruction()
            instruction904 = _t1546
            _t1547 = logic_pb2.Construct(instruction=instruction904)
            _t1545 = _t1547
        else:
            if prediction902 == 0:
                _t1549 = self.parse_loop()
                loop903 = _t1549
                _t1550 = logic_pb2.Construct(loop=loop903)
                _t1548 = _t1550
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1545 = _t1548
        result906 = _t1545
        self.record_span(span_start905, "Construct")
        return result906

    def parse_loop(self) -> logic_pb2.Loop:
        span_start909 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1551 = self.parse_init()
        init907 = _t1551
        _t1552 = self.parse_script()
        script908 = _t1552
        self.consume_literal(")")
        _t1553 = logic_pb2.Loop(init=init907, body=script908)
        result910 = _t1553
        self.record_span(span_start909, "Loop")
        return result910

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs911 = []
        cond912 = self.match_lookahead_literal("(", 0)
        while cond912:
            _t1554 = self.parse_instruction()
            item913 = _t1554
            xs911.append(item913)
            cond912 = self.match_lookahead_literal("(", 0)
        instructions914 = xs911
        self.consume_literal(")")
        return instructions914

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start921 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1556 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1557 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1558 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1559 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1560 = 0
                            else:
                                _t1560 = -1
                            _t1559 = _t1560
                        _t1558 = _t1559
                    _t1557 = _t1558
                _t1556 = _t1557
            _t1555 = _t1556
        else:
            _t1555 = -1
        prediction915 = _t1555
        if prediction915 == 4:
            _t1562 = self.parse_monus_def()
            monus_def920 = _t1562
            _t1563 = logic_pb2.Instruction(monus_def=monus_def920)
            _t1561 = _t1563
        else:
            if prediction915 == 3:
                _t1565 = self.parse_monoid_def()
                monoid_def919 = _t1565
                _t1566 = logic_pb2.Instruction(monoid_def=monoid_def919)
                _t1564 = _t1566
            else:
                if prediction915 == 2:
                    _t1568 = self.parse_break()
                    break918 = _t1568
                    _t1569 = logic_pb2.Instruction()
                    getattr(_t1569, 'break').CopyFrom(break918)
                    _t1567 = _t1569
                else:
                    if prediction915 == 1:
                        _t1571 = self.parse_upsert()
                        upsert917 = _t1571
                        _t1572 = logic_pb2.Instruction(upsert=upsert917)
                        _t1570 = _t1572
                    else:
                        if prediction915 == 0:
                            _t1574 = self.parse_assign()
                            assign916 = _t1574
                            _t1575 = logic_pb2.Instruction(assign=assign916)
                            _t1573 = _t1575
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1570 = _t1573
                    _t1567 = _t1570
                _t1564 = _t1567
            _t1561 = _t1564
        result922 = _t1561
        self.record_span(span_start921, "Instruction")
        return result922

    def parse_assign(self) -> logic_pb2.Assign:
        span_start926 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1576 = self.parse_relation_id()
        relation_id923 = _t1576
        _t1577 = self.parse_abstraction()
        abstraction924 = _t1577
        if self.match_lookahead_literal("(", 0):
            _t1579 = self.parse_attrs()
            _t1578 = _t1579
        else:
            _t1578 = None
        attrs925 = _t1578
        self.consume_literal(")")
        _t1580 = logic_pb2.Assign(name=relation_id923, body=abstraction924, attrs=(attrs925 if attrs925 is not None else []))
        result927 = _t1580
        self.record_span(span_start926, "Assign")
        return result927

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start931 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1581 = self.parse_relation_id()
        relation_id928 = _t1581
        _t1582 = self.parse_abstraction_with_arity()
        abstraction_with_arity929 = _t1582
        if self.match_lookahead_literal("(", 0):
            _t1584 = self.parse_attrs()
            _t1583 = _t1584
        else:
            _t1583 = None
        attrs930 = _t1583
        self.consume_literal(")")
        _t1585 = logic_pb2.Upsert(name=relation_id928, body=abstraction_with_arity929[0], attrs=(attrs930 if attrs930 is not None else []), value_arity=abstraction_with_arity929[1])
        result932 = _t1585
        self.record_span(span_start931, "Upsert")
        return result932

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1586 = self.parse_bindings()
        bindings933 = _t1586
        _t1587 = self.parse_formula()
        formula934 = _t1587
        self.consume_literal(")")
        _t1588 = logic_pb2.Abstraction(vars=(list(bindings933[0]) + list(bindings933[1] if bindings933[1] is not None else [])), value=formula934)
        return (_t1588, len(bindings933[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start938 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1589 = self.parse_relation_id()
        relation_id935 = _t1589
        _t1590 = self.parse_abstraction()
        abstraction936 = _t1590
        if self.match_lookahead_literal("(", 0):
            _t1592 = self.parse_attrs()
            _t1591 = _t1592
        else:
            _t1591 = None
        attrs937 = _t1591
        self.consume_literal(")")
        _t1593 = logic_pb2.Break(name=relation_id935, body=abstraction936, attrs=(attrs937 if attrs937 is not None else []))
        result939 = _t1593
        self.record_span(span_start938, "Break")
        return result939

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start944 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1594 = self.parse_monoid()
        monoid940 = _t1594
        _t1595 = self.parse_relation_id()
        relation_id941 = _t1595
        _t1596 = self.parse_abstraction_with_arity()
        abstraction_with_arity942 = _t1596
        if self.match_lookahead_literal("(", 0):
            _t1598 = self.parse_attrs()
            _t1597 = _t1598
        else:
            _t1597 = None
        attrs943 = _t1597
        self.consume_literal(")")
        _t1599 = logic_pb2.MonoidDef(monoid=monoid940, name=relation_id941, body=abstraction_with_arity942[0], attrs=(attrs943 if attrs943 is not None else []), value_arity=abstraction_with_arity942[1])
        result945 = _t1599
        self.record_span(span_start944, "MonoidDef")
        return result945

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start951 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1601 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1602 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1603 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1604 = 2
                        else:
                            _t1604 = -1
                        _t1603 = _t1604
                    _t1602 = _t1603
                _t1601 = _t1602
            _t1600 = _t1601
        else:
            _t1600 = -1
        prediction946 = _t1600
        if prediction946 == 3:
            _t1606 = self.parse_sum_monoid()
            sum_monoid950 = _t1606
            _t1607 = logic_pb2.Monoid(sum_monoid=sum_monoid950)
            _t1605 = _t1607
        else:
            if prediction946 == 2:
                _t1609 = self.parse_max_monoid()
                max_monoid949 = _t1609
                _t1610 = logic_pb2.Monoid(max_monoid=max_monoid949)
                _t1608 = _t1610
            else:
                if prediction946 == 1:
                    _t1612 = self.parse_min_monoid()
                    min_monoid948 = _t1612
                    _t1613 = logic_pb2.Monoid(min_monoid=min_monoid948)
                    _t1611 = _t1613
                else:
                    if prediction946 == 0:
                        _t1615 = self.parse_or_monoid()
                        or_monoid947 = _t1615
                        _t1616 = logic_pb2.Monoid(or_monoid=or_monoid947)
                        _t1614 = _t1616
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1611 = _t1614
                _t1608 = _t1611
            _t1605 = _t1608
        result952 = _t1605
        self.record_span(span_start951, "Monoid")
        return result952

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start953 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1617 = logic_pb2.OrMonoid()
        result954 = _t1617
        self.record_span(span_start953, "OrMonoid")
        return result954

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start956 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1618 = self.parse_type()
        type955 = _t1618
        self.consume_literal(")")
        _t1619 = logic_pb2.MinMonoid(type=type955)
        result957 = _t1619
        self.record_span(span_start956, "MinMonoid")
        return result957

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start959 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1620 = self.parse_type()
        type958 = _t1620
        self.consume_literal(")")
        _t1621 = logic_pb2.MaxMonoid(type=type958)
        result960 = _t1621
        self.record_span(span_start959, "MaxMonoid")
        return result960

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start962 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1622 = self.parse_type()
        type961 = _t1622
        self.consume_literal(")")
        _t1623 = logic_pb2.SumMonoid(type=type961)
        result963 = _t1623
        self.record_span(span_start962, "SumMonoid")
        return result963

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start968 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1624 = self.parse_monoid()
        monoid964 = _t1624
        _t1625 = self.parse_relation_id()
        relation_id965 = _t1625
        _t1626 = self.parse_abstraction_with_arity()
        abstraction_with_arity966 = _t1626
        if self.match_lookahead_literal("(", 0):
            _t1628 = self.parse_attrs()
            _t1627 = _t1628
        else:
            _t1627 = None
        attrs967 = _t1627
        self.consume_literal(")")
        _t1629 = logic_pb2.MonusDef(monoid=monoid964, name=relation_id965, body=abstraction_with_arity966[0], attrs=(attrs967 if attrs967 is not None else []), value_arity=abstraction_with_arity966[1])
        result969 = _t1629
        self.record_span(span_start968, "MonusDef")
        return result969

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start974 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1630 = self.parse_relation_id()
        relation_id970 = _t1630
        _t1631 = self.parse_abstraction()
        abstraction971 = _t1631
        _t1632 = self.parse_functional_dependency_keys()
        functional_dependency_keys972 = _t1632
        _t1633 = self.parse_functional_dependency_values()
        functional_dependency_values973 = _t1633
        self.consume_literal(")")
        _t1634 = logic_pb2.FunctionalDependency(guard=abstraction971, keys=functional_dependency_keys972, values=functional_dependency_values973)
        _t1635 = logic_pb2.Constraint(name=relation_id970, functional_dependency=_t1634)
        result975 = _t1635
        self.record_span(span_start974, "Constraint")
        return result975

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs976 = []
        cond977 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond977:
            _t1636 = self.parse_var()
            item978 = _t1636
            xs976.append(item978)
            cond977 = self.match_lookahead_terminal("SYMBOL", 0)
        vars979 = xs976
        self.consume_literal(")")
        return vars979

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs980 = []
        cond981 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond981:
            _t1637 = self.parse_var()
            item982 = _t1637
            xs980.append(item982)
            cond981 = self.match_lookahead_terminal("SYMBOL", 0)
        vars983 = xs980
        self.consume_literal(")")
        return vars983

    def parse_data(self) -> logic_pb2.Data:
        span_start988 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("edb", 1):
                _t1639 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1640 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1641 = 1
                    else:
                        _t1641 = -1
                    _t1640 = _t1641
                _t1639 = _t1640
            _t1638 = _t1639
        else:
            _t1638 = -1
        prediction984 = _t1638
        if prediction984 == 2:
            _t1643 = self.parse_csv_data()
            csv_data987 = _t1643
            _t1644 = logic_pb2.Data(csv_data=csv_data987)
            _t1642 = _t1644
        else:
            if prediction984 == 1:
                _t1646 = self.parse_betree_relation()
                betree_relation986 = _t1646
                _t1647 = logic_pb2.Data(betree_relation=betree_relation986)
                _t1645 = _t1647
            else:
                if prediction984 == 0:
                    _t1649 = self.parse_edb()
                    edb985 = _t1649
                    _t1650 = logic_pb2.Data(edb=edb985)
                    _t1648 = _t1650
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1645 = _t1648
            _t1642 = _t1645
        result989 = _t1642
        self.record_span(span_start988, "Data")
        return result989

    def parse_edb(self) -> logic_pb2.EDB:
        span_start993 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1651 = self.parse_relation_id()
        relation_id990 = _t1651
        _t1652 = self.parse_edb_path()
        edb_path991 = _t1652
        _t1653 = self.parse_edb_types()
        edb_types992 = _t1653
        self.consume_literal(")")
        _t1654 = logic_pb2.EDB(target_id=relation_id990, path=edb_path991, types=edb_types992)
        result994 = _t1654
        self.record_span(span_start993, "EDB")
        return result994

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs995 = []
        cond996 = self.match_lookahead_terminal("STRING", 0)
        while cond996:
            item997 = self.consume_terminal("STRING")
            xs995.append(item997)
            cond996 = self.match_lookahead_terminal("STRING", 0)
        strings998 = xs995
        self.consume_literal("]")
        return strings998

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs999 = []
        cond1000 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1000:
            _t1655 = self.parse_type()
            item1001 = _t1655
            xs999.append(item1001)
            cond1000 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1002 = xs999
        self.consume_literal("]")
        return types1002

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1005 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1656 = self.parse_relation_id()
        relation_id1003 = _t1656
        _t1657 = self.parse_betree_info()
        betree_info1004 = _t1657
        self.consume_literal(")")
        _t1658 = logic_pb2.BeTreeRelation(name=relation_id1003, relation_info=betree_info1004)
        result1006 = _t1658
        self.record_span(span_start1005, "BeTreeRelation")
        return result1006

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1010 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1659 = self.parse_betree_info_key_types()
        betree_info_key_types1007 = _t1659
        _t1660 = self.parse_betree_info_value_types()
        betree_info_value_types1008 = _t1660
        _t1661 = self.parse_config_dict()
        config_dict1009 = _t1661
        self.consume_literal(")")
        _t1662 = self.construct_betree_info(betree_info_key_types1007, betree_info_value_types1008, config_dict1009)
        result1011 = _t1662
        self.record_span(span_start1010, "BeTreeInfo")
        return result1011

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1012 = []
        cond1013 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1013:
            _t1663 = self.parse_type()
            item1014 = _t1663
            xs1012.append(item1014)
            cond1013 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1015 = xs1012
        self.consume_literal(")")
        return types1015

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1016 = []
        cond1017 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1017:
            _t1664 = self.parse_type()
            item1018 = _t1664
            xs1016.append(item1018)
            cond1017 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1019 = xs1016
        self.consume_literal(")")
        return types1019

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1024 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1665 = self.parse_csvlocator()
        csvlocator1020 = _t1665
        _t1666 = self.parse_csv_config()
        csv_config1021 = _t1666
        _t1667 = self.parse_gnf_columns()
        gnf_columns1022 = _t1667
        _t1668 = self.parse_csv_asof()
        csv_asof1023 = _t1668
        self.consume_literal(")")
        _t1669 = logic_pb2.CSVData(locator=csvlocator1020, config=csv_config1021, columns=gnf_columns1022, asof=csv_asof1023)
        result1025 = _t1669
        self.record_span(span_start1024, "CSVData")
        return result1025

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1028 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1671 = self.parse_csv_locator_paths()
            _t1670 = _t1671
        else:
            _t1670 = None
        csv_locator_paths1026 = _t1670
        if self.match_lookahead_literal("(", 0):
            _t1673 = self.parse_csv_locator_inline_data()
            _t1672 = _t1673
        else:
            _t1672 = None
        csv_locator_inline_data1027 = _t1672
        self.consume_literal(")")
        _t1674 = logic_pb2.CSVLocator(paths=(csv_locator_paths1026 if csv_locator_paths1026 is not None else []), inline_data=(csv_locator_inline_data1027 if csv_locator_inline_data1027 is not None else "").encode())
        result1029 = _t1674
        self.record_span(span_start1028, "CSVLocator")
        return result1029

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1030 = []
        cond1031 = self.match_lookahead_terminal("STRING", 0)
        while cond1031:
            item1032 = self.consume_terminal("STRING")
            xs1030.append(item1032)
            cond1031 = self.match_lookahead_terminal("STRING", 0)
        strings1033 = xs1030
        self.consume_literal(")")
        return strings1033

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1034 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1034

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1036 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1675 = self.parse_config_dict()
        config_dict1035 = _t1675
        self.consume_literal(")")
        _t1676 = self.construct_csv_config(config_dict1035)
        result1037 = _t1676
        self.record_span(span_start1036, "CSVConfig")
        return result1037

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1038 = []
        cond1039 = self.match_lookahead_literal("(", 0)
        while cond1039:
            _t1677 = self.parse_gnf_column()
            item1040 = _t1677
            xs1038.append(item1040)
            cond1039 = self.match_lookahead_literal("(", 0)
        gnf_columns1041 = xs1038
        self.consume_literal(")")
        return gnf_columns1041

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1048 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1678 = self.parse_gnf_column_path()
        gnf_column_path1042 = _t1678
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1680 = self.parse_relation_id()
            _t1679 = _t1680
        else:
            _t1679 = None
        relation_id1043 = _t1679
        self.consume_literal("[")
        xs1044 = []
        cond1045 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1045:
            _t1681 = self.parse_type()
            item1046 = _t1681
            xs1044.append(item1046)
            cond1045 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1047 = xs1044
        self.consume_literal("]")
        self.consume_literal(")")
        _t1682 = logic_pb2.GNFColumn(column_path=gnf_column_path1042, target_id=relation_id1043, types=types1047)
        result1049 = _t1682
        self.record_span(span_start1048, "GNFColumn")
        return result1049

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1683 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1684 = 0
            else:
                _t1684 = -1
            _t1683 = _t1684
        prediction1050 = _t1683
        if prediction1050 == 1:
            self.consume_literal("[")
            xs1052 = []
            cond1053 = self.match_lookahead_terminal("STRING", 0)
            while cond1053:
                item1054 = self.consume_terminal("STRING")
                xs1052.append(item1054)
                cond1053 = self.match_lookahead_terminal("STRING", 0)
            strings1055 = xs1052
            self.consume_literal("]")
            _t1685 = strings1055
        else:
            if prediction1050 == 0:
                string1051 = self.consume_terminal("STRING")
                _t1686 = [string1051]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1685 = _t1686
        return _t1685

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1056 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1056

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1058 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1687 = self.parse_fragment_id()
        fragment_id1057 = _t1687
        self.consume_literal(")")
        _t1688 = transactions_pb2.Undefine(fragment_id=fragment_id1057)
        result1059 = _t1688
        self.record_span(span_start1058, "Undefine")
        return result1059

    def parse_context(self) -> transactions_pb2.Context:
        span_start1064 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1060 = []
        cond1061 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1061:
            _t1689 = self.parse_relation_id()
            item1062 = _t1689
            xs1060.append(item1062)
            cond1061 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1063 = xs1060
        self.consume_literal(")")
        _t1690 = transactions_pb2.Context(relations=relation_ids1063)
        result1065 = _t1690
        self.record_span(span_start1064, "Context")
        return result1065

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1070 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1066 = []
        cond1067 = self.match_lookahead_literal("[", 0)
        while cond1067:
            _t1691 = self.parse_snapshot_mapping()
            item1068 = _t1691
            xs1066.append(item1068)
            cond1067 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1069 = xs1066
        self.consume_literal(")")
        _t1692 = transactions_pb2.Snapshot(mappings=snapshot_mappings1069)
        result1071 = _t1692
        self.record_span(span_start1070, "Snapshot")
        return result1071

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1074 = self.span_start()
        _t1693 = self.parse_edb_path()
        edb_path1072 = _t1693
        _t1694 = self.parse_relation_id()
        relation_id1073 = _t1694
        _t1695 = transactions_pb2.SnapshotMapping(destination_path=edb_path1072, source_relation=relation_id1073)
        result1075 = _t1695
        self.record_span(span_start1074, "SnapshotMapping")
        return result1075

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1076 = []
        cond1077 = self.match_lookahead_literal("(", 0)
        while cond1077:
            _t1696 = self.parse_read()
            item1078 = _t1696
            xs1076.append(item1078)
            cond1077 = self.match_lookahead_literal("(", 0)
        reads1079 = xs1076
        self.consume_literal(")")
        return reads1079

    def parse_read(self) -> transactions_pb2.Read:
        span_start1086 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1698 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1699 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1700 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1701 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1702 = 3
                            else:
                                _t1702 = -1
                            _t1701 = _t1702
                        _t1700 = _t1701
                    _t1699 = _t1700
                _t1698 = _t1699
            _t1697 = _t1698
        else:
            _t1697 = -1
        prediction1080 = _t1697
        if prediction1080 == 4:
            _t1704 = self.parse_export()
            export1085 = _t1704
            _t1705 = transactions_pb2.Read(export=export1085)
            _t1703 = _t1705
        else:
            if prediction1080 == 3:
                _t1707 = self.parse_abort()
                abort1084 = _t1707
                _t1708 = transactions_pb2.Read(abort=abort1084)
                _t1706 = _t1708
            else:
                if prediction1080 == 2:
                    _t1710 = self.parse_what_if()
                    what_if1083 = _t1710
                    _t1711 = transactions_pb2.Read(what_if=what_if1083)
                    _t1709 = _t1711
                else:
                    if prediction1080 == 1:
                        _t1713 = self.parse_output()
                        output1082 = _t1713
                        _t1714 = transactions_pb2.Read(output=output1082)
                        _t1712 = _t1714
                    else:
                        if prediction1080 == 0:
                            _t1716 = self.parse_demand()
                            demand1081 = _t1716
                            _t1717 = transactions_pb2.Read(demand=demand1081)
                            _t1715 = _t1717
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1712 = _t1715
                    _t1709 = _t1712
                _t1706 = _t1709
            _t1703 = _t1706
        result1087 = _t1703
        self.record_span(span_start1086, "Read")
        return result1087

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1089 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1718 = self.parse_relation_id()
        relation_id1088 = _t1718
        self.consume_literal(")")
        _t1719 = transactions_pb2.Demand(relation_id=relation_id1088)
        result1090 = _t1719
        self.record_span(span_start1089, "Demand")
        return result1090

    def parse_output(self) -> transactions_pb2.Output:
        span_start1093 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t1720 = self.parse_name()
        name1091 = _t1720
        _t1721 = self.parse_relation_id()
        relation_id1092 = _t1721
        self.consume_literal(")")
        _t1722 = transactions_pb2.Output(name=name1091, relation_id=relation_id1092)
        result1094 = _t1722
        self.record_span(span_start1093, "Output")
        return result1094

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1097 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1723 = self.parse_name()
        name1095 = _t1723
        _t1724 = self.parse_epoch()
        epoch1096 = _t1724
        self.consume_literal(")")
        _t1725 = transactions_pb2.WhatIf(branch=name1095, epoch=epoch1096)
        result1098 = _t1725
        self.record_span(span_start1097, "WhatIf")
        return result1098

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1101 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1727 = self.parse_name()
            _t1726 = _t1727
        else:
            _t1726 = None
        name1099 = _t1726
        _t1728 = self.parse_relation_id()
        relation_id1100 = _t1728
        self.consume_literal(")")
        _t1729 = transactions_pb2.Abort(name=(name1099 if name1099 is not None else "abort"), relation_id=relation_id1100)
        result1102 = _t1729
        self.record_span(span_start1101, "Abort")
        return result1102

    def parse_export(self) -> transactions_pb2.Export:
        span_start1104 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export")
        _t1730 = self.parse_export_csv_config()
        export_csv_config1103 = _t1730
        self.consume_literal(")")
        _t1731 = transactions_pb2.Export(csv_config=export_csv_config1103)
        result1105 = _t1731
        self.record_span(span_start1104, "Export")
        return result1105

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1113 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t1733 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t1734 = 1
                else:
                    _t1734 = -1
                _t1733 = _t1734
            _t1732 = _t1733
        else:
            _t1732 = -1
        prediction1106 = _t1732
        if prediction1106 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t1736 = self.parse_export_csv_path()
            export_csv_path1110 = _t1736
            _t1737 = self.parse_export_csv_columns_list()
            export_csv_columns_list1111 = _t1737
            _t1738 = self.parse_config_dict()
            config_dict1112 = _t1738
            self.consume_literal(")")
            _t1739 = self.construct_export_csv_config(export_csv_path1110, export_csv_columns_list1111, config_dict1112)
            _t1735 = _t1739
        else:
            if prediction1106 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t1741 = self.parse_export_csv_path()
                export_csv_path1107 = _t1741
                _t1742 = self.parse_export_csv_source()
                export_csv_source1108 = _t1742
                _t1743 = self.parse_csv_config()
                csv_config1109 = _t1743
                self.consume_literal(")")
                _t1744 = self.construct_export_csv_config_with_source(export_csv_path1107, export_csv_source1108, csv_config1109)
                _t1740 = _t1744
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1735 = _t1740
        result1114 = _t1735
        self.record_span(span_start1113, "ExportCSVConfig")
        return result1114

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1115 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1115

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1122 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t1746 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t1747 = 0
                else:
                    _t1747 = -1
                _t1746 = _t1747
            _t1745 = _t1746
        else:
            _t1745 = -1
        prediction1116 = _t1745
        if prediction1116 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t1749 = self.parse_relation_id()
            relation_id1121 = _t1749
            self.consume_literal(")")
            _t1750 = transactions_pb2.ExportCSVSource(table_def=relation_id1121)
            _t1748 = _t1750
        else:
            if prediction1116 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1117 = []
                cond1118 = self.match_lookahead_literal("(", 0)
                while cond1118:
                    _t1752 = self.parse_export_csv_column()
                    item1119 = _t1752
                    xs1117.append(item1119)
                    cond1118 = self.match_lookahead_literal("(", 0)
                export_csv_columns1120 = xs1117
                self.consume_literal(")")
                _t1753 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1120)
                _t1754 = transactions_pb2.ExportCSVSource(gnf_columns=_t1753)
                _t1751 = _t1754
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1748 = _t1751
        result1123 = _t1748
        self.record_span(span_start1122, "ExportCSVSource")
        return result1123

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1126 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1124 = self.consume_terminal("STRING")
        _t1755 = self.parse_relation_id()
        relation_id1125 = _t1755
        self.consume_literal(")")
        _t1756 = transactions_pb2.ExportCSVColumn(column_name=string1124, column_data=relation_id1125)
        result1127 = _t1756
        self.record_span(span_start1126, "ExportCSVColumn")
        return result1127

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1128 = []
        cond1129 = self.match_lookahead_literal("(", 0)
        while cond1129:
            _t1757 = self.parse_export_csv_column()
            item1130 = _t1757
            xs1128.append(item1130)
            cond1129 = self.match_lookahead_literal("(", 0)
        export_csv_columns1131 = xs1128
        self.consume_literal(")")
        return export_csv_columns1131


def parse_transaction(input_str: str) -> tuple[Any, dict[int, Span]]:
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


def parse_fragment(input_str: str) -> tuple[Any, dict[int, Span]]:
    """Parse input string and return (result, provenance) tuple."""
    lexer = Lexer(input_str)
    parser = Parser(lexer.tokens, input_str)
    result = parser.parse_fragment()
    # Check for unconsumed tokens (except EOF)
    if parser.pos < len(parser.tokens):
        remaining_token = parser.lookahead(0)
        if remaining_token.type != "$":
            raise ParseError(f"Unexpected token at end of input: {remaining_token}")
    return result, parser.provenance


def parse(input_str: str) -> tuple[Any, dict[int, Span]]:
    """Parse input string and return (result, provenance) tuple."""
    return parse_transaction(input_str)
