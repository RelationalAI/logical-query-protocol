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
    ("FLOAT32", re.compile(r"[-]?\d+\.\d+f32"), lambda x: Lexer.scan_float32(x)),
    ("INT", re.compile(r"[-]?\d+"), lambda x: Lexer.scan_int(x)),
    ("INT32", re.compile(r"[-]?\d+i32"), lambda x: Lexer.scan_int32(x)),
    ("INT128", re.compile(r"[-]?\d+i128"), lambda x: Lexer.scan_int128(x)),
    ("STRING", re.compile(r'"(?:[^"\\]|\\.)*"'), lambda x: Lexer.scan_string(x)),
    (
        "SYMBOL",
        re.compile(r"[a-zA-Z_][a-zA-Z0-9_./#-]*"),
        lambda x: Lexer.scan_symbol(x),
    ),
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
    def scan_int32(n: str) -> int:
        """Parse INT32 token."""
        n = n[:-3]  # Remove "i32" suffix
        val = int(n)
        if val < -(1 << 31) or val >= (1 << 31):
            raise ParseError(f"Int32 literal out of range: {n}")
        return val

    @staticmethod
    def scan_float32(f: str) -> float:
        """Parse FLOAT32 token."""
        f = f[:-3]  # Remove "f32" suffix
        return float(f)

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
        hash_bytes = hashlib.sha256(name.encode()).digest()
        # Use big-endian and the lower 128 bits of the hash, consistent with pyrel.
        id_high = int.from_bytes(hash_bytes[16:24], byteorder='big')
        id_low = int.from_bytes(hash_bytes[24:32], byteorder='big')
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
            _t1794 = value.HasField("int_value")
        else:
            _t1794 = False
        if _t1794:
            assert value is not None
            return int(value.int_value)
        else:
            _t1795 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t1796 = value.HasField("int_value")
        else:
            _t1796 = False
        if _t1796:
            assert value is not None
            return value.int_value
        else:
            _t1797 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t1798 = value.HasField("string_value")
        else:
            _t1798 = False
        if _t1798:
            assert value is not None
            return value.string_value
        else:
            _t1799 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1800 = value.HasField("boolean_value")
        else:
            _t1800 = False
        if _t1800:
            assert value is not None
            return value.boolean_value
        else:
            _t1801 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1802 = value.HasField("string_value")
        else:
            _t1802 = False
        if _t1802:
            assert value is not None
            return [value.string_value]
        else:
            _t1803 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t1804 = value.HasField("int_value")
        else:
            _t1804 = False
        if _t1804:
            assert value is not None
            return value.int_value
        else:
            _t1805 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t1806 = value.HasField("float_value")
        else:
            _t1806 = False
        if _t1806:
            assert value is not None
            return value.float_value
        else:
            _t1807 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t1808 = value.HasField("string_value")
        else:
            _t1808 = False
        if _t1808:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1809 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t1810 = value.HasField("uint128_value")
        else:
            _t1810 = False
        if _t1810:
            assert value is not None
            return value.uint128_value
        else:
            _t1811 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1812 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1812
        _t1813 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1813
        _t1814 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1814
        _t1815 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1815
        _t1816 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1816
        _t1817 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1817
        _t1818 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1818
        _t1819 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1819
        _t1820 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1820
        _t1821 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1821
        _t1822 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1822
        _t1823 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t1823
        _t1824 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t1824

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1825 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1825
        _t1826 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1826
        _t1827 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1827
        _t1828 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1828
        _t1829 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1829
        _t1830 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1830
        _t1831 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1831
        _t1832 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1832
        _t1833 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1833
        _t1834 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1834
        _t1835 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1835

    def default_configure(self) -> transactions_pb2.Configure:
        _t1836 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1836
        _t1837 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1837

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
        _t1838 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1838
        _t1839 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1839
        _t1840 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1840

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1841 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1841
        _t1842 = self._extract_value_string(config.get("compression"), "")
        compression = _t1842
        _t1843 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1843
        _t1844 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1844
        _t1845 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1845
        _t1846 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1846
        _t1847 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1847
        _t1848 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1848

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t1849 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t1849

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start580 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1149 = self.parse_configure()
            _t1148 = _t1149
        else:
            _t1148 = None
        configure574 = _t1148
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1151 = self.parse_sync()
            _t1150 = _t1151
        else:
            _t1150 = None
        sync575 = _t1150
        xs576 = []
        cond577 = self.match_lookahead_literal("(", 0)
        while cond577:
            _t1152 = self.parse_epoch()
            item578 = _t1152
            xs576.append(item578)
            cond577 = self.match_lookahead_literal("(", 0)
        epochs579 = xs576
        self.consume_literal(")")
        _t1153 = self.default_configure()
        _t1154 = transactions_pb2.Transaction(epochs=epochs579, configure=(configure574 if configure574 is not None else _t1153), sync=sync575)
        result581 = _t1154
        self.record_span(span_start580, "Transaction")
        return result581

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start583 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1155 = self.parse_config_dict()
        config_dict582 = _t1155
        self.consume_literal(")")
        _t1156 = self.construct_configure(config_dict582)
        result584 = _t1156
        self.record_span(span_start583, "Configure")
        return result584

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs585 = []
        cond586 = self.match_lookahead_literal(":", 0)
        while cond586:
            _t1157 = self.parse_config_key_value()
            item587 = _t1157
            xs585.append(item587)
            cond586 = self.match_lookahead_literal(":", 0)
        config_key_values588 = xs585
        self.consume_literal("}")
        return config_key_values588

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol589 = self.consume_terminal("SYMBOL")
        _t1158 = self.parse_value()
        value590 = _t1158
        return (symbol589, value590,)

    def parse_value(self) -> logic_pb2.Value:
        span_start603 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1159 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1160 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1161 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1163 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1164 = 0
                            else:
                                _t1164 = -1
                            _t1163 = _t1164
                        _t1162 = _t1163
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1165 = 5
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t1166 = 2
                            else:
                                if self.match_lookahead_terminal("INT32", 0):
                                    _t1167 = 10
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t1168 = 6
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t1169 = 3
                                        else:
                                            if self.match_lookahead_terminal("FLOAT32", 0):
                                                _t1170 = 11
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1171 = 4
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1172 = 7
                                                    else:
                                                        _t1172 = -1
                                                    _t1171 = _t1172
                                                _t1170 = _t1171
                                            _t1169 = _t1170
                                        _t1168 = _t1169
                                    _t1167 = _t1168
                                _t1166 = _t1167
                            _t1165 = _t1166
                        _t1162 = _t1165
                    _t1161 = _t1162
                _t1160 = _t1161
            _t1159 = _t1160
        prediction591 = _t1159
        if prediction591 == 11:
            float32602 = self.consume_terminal("FLOAT32")
            _t1174 = logic_pb2.Value(float32_value=float32602)
            _t1173 = _t1174
        else:
            if prediction591 == 10:
                int32601 = self.consume_terminal("INT32")
                _t1176 = logic_pb2.Value(int32_value=int32601)
                _t1175 = _t1176
            else:
                if prediction591 == 9:
                    _t1178 = self.parse_boolean_value()
                    boolean_value600 = _t1178
                    _t1179 = logic_pb2.Value(boolean_value=boolean_value600)
                    _t1177 = _t1179
                else:
                    if prediction591 == 8:
                        self.consume_literal("missing")
                        _t1181 = logic_pb2.MissingValue()
                        _t1182 = logic_pb2.Value(missing_value=_t1181)
                        _t1180 = _t1182
                    else:
                        if prediction591 == 7:
                            decimal599 = self.consume_terminal("DECIMAL")
                            _t1184 = logic_pb2.Value(decimal_value=decimal599)
                            _t1183 = _t1184
                        else:
                            if prediction591 == 6:
                                int128598 = self.consume_terminal("INT128")
                                _t1186 = logic_pb2.Value(int128_value=int128598)
                                _t1185 = _t1186
                            else:
                                if prediction591 == 5:
                                    uint128597 = self.consume_terminal("UINT128")
                                    _t1188 = logic_pb2.Value(uint128_value=uint128597)
                                    _t1187 = _t1188
                                else:
                                    if prediction591 == 4:
                                        float596 = self.consume_terminal("FLOAT")
                                        _t1190 = logic_pb2.Value(float_value=float596)
                                        _t1189 = _t1190
                                    else:
                                        if prediction591 == 3:
                                            int595 = self.consume_terminal("INT")
                                            _t1192 = logic_pb2.Value(int_value=int595)
                                            _t1191 = _t1192
                                        else:
                                            if prediction591 == 2:
                                                string594 = self.consume_terminal("STRING")
                                                _t1194 = logic_pb2.Value(string_value=string594)
                                                _t1193 = _t1194
                                            else:
                                                if prediction591 == 1:
                                                    _t1196 = self.parse_datetime()
                                                    datetime593 = _t1196
                                                    _t1197 = logic_pb2.Value(datetime_value=datetime593)
                                                    _t1195 = _t1197
                                                else:
                                                    if prediction591 == 0:
                                                        _t1199 = self.parse_date()
                                                        date592 = _t1199
                                                        _t1200 = logic_pb2.Value(date_value=date592)
                                                        _t1198 = _t1200
                                                    else:
                                                        raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                    _t1195 = _t1198
                                                _t1193 = _t1195
                                            _t1191 = _t1193
                                        _t1189 = _t1191
                                    _t1187 = _t1189
                                _t1185 = _t1187
                            _t1183 = _t1185
                        _t1180 = _t1183
                    _t1177 = _t1180
                _t1175 = _t1177
            _t1173 = _t1175
        result604 = _t1173
        self.record_span(span_start603, "Value")
        return result604

    def parse_date(self) -> logic_pb2.DateValue:
        span_start608 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int605 = self.consume_terminal("INT")
        int_3606 = self.consume_terminal("INT")
        int_4607 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1201 = logic_pb2.DateValue(year=int(int605), month=int(int_3606), day=int(int_4607))
        result609 = _t1201
        self.record_span(span_start608, "DateValue")
        return result609

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start617 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int610 = self.consume_terminal("INT")
        int_3611 = self.consume_terminal("INT")
        int_4612 = self.consume_terminal("INT")
        int_5613 = self.consume_terminal("INT")
        int_6614 = self.consume_terminal("INT")
        int_7615 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1202 = self.consume_terminal("INT")
        else:
            _t1202 = None
        int_8616 = _t1202
        self.consume_literal(")")
        _t1203 = logic_pb2.DateTimeValue(year=int(int610), month=int(int_3611), day=int(int_4612), hour=int(int_5613), minute=int(int_6614), second=int(int_7615), microsecond=int((int_8616 if int_8616 is not None else 0)))
        result618 = _t1203
        self.record_span(span_start617, "DateTimeValue")
        return result618

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1204 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1205 = 1
            else:
                _t1205 = -1
            _t1204 = _t1205
        prediction619 = _t1204
        if prediction619 == 1:
            self.consume_literal("false")
            _t1206 = False
        else:
            if prediction619 == 0:
                self.consume_literal("true")
                _t1207 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1206 = _t1207
        return _t1206

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start624 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs620 = []
        cond621 = self.match_lookahead_literal(":", 0)
        while cond621:
            _t1208 = self.parse_fragment_id()
            item622 = _t1208
            xs620.append(item622)
            cond621 = self.match_lookahead_literal(":", 0)
        fragment_ids623 = xs620
        self.consume_literal(")")
        _t1209 = transactions_pb2.Sync(fragments=fragment_ids623)
        result625 = _t1209
        self.record_span(span_start624, "Sync")
        return result625

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start627 = self.span_start()
        self.consume_literal(":")
        symbol626 = self.consume_terminal("SYMBOL")
        result628 = fragments_pb2.FragmentId(id=symbol626.encode())
        self.record_span(span_start627, "FragmentId")
        return result628

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start631 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1211 = self.parse_epoch_writes()
            _t1210 = _t1211
        else:
            _t1210 = None
        epoch_writes629 = _t1210
        if self.match_lookahead_literal("(", 0):
            _t1213 = self.parse_epoch_reads()
            _t1212 = _t1213
        else:
            _t1212 = None
        epoch_reads630 = _t1212
        self.consume_literal(")")
        _t1214 = transactions_pb2.Epoch(writes=(epoch_writes629 if epoch_writes629 is not None else []), reads=(epoch_reads630 if epoch_reads630 is not None else []))
        result632 = _t1214
        self.record_span(span_start631, "Epoch")
        return result632

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs633 = []
        cond634 = self.match_lookahead_literal("(", 0)
        while cond634:
            _t1215 = self.parse_write()
            item635 = _t1215
            xs633.append(item635)
            cond634 = self.match_lookahead_literal("(", 0)
        writes636 = xs633
        self.consume_literal(")")
        return writes636

    def parse_write(self) -> transactions_pb2.Write:
        span_start642 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1217 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1218 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1219 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1220 = 2
                        else:
                            _t1220 = -1
                        _t1219 = _t1220
                    _t1218 = _t1219
                _t1217 = _t1218
            _t1216 = _t1217
        else:
            _t1216 = -1
        prediction637 = _t1216
        if prediction637 == 3:
            _t1222 = self.parse_snapshot()
            snapshot641 = _t1222
            _t1223 = transactions_pb2.Write(snapshot=snapshot641)
            _t1221 = _t1223
        else:
            if prediction637 == 2:
                _t1225 = self.parse_context()
                context640 = _t1225
                _t1226 = transactions_pb2.Write(context=context640)
                _t1224 = _t1226
            else:
                if prediction637 == 1:
                    _t1228 = self.parse_undefine()
                    undefine639 = _t1228
                    _t1229 = transactions_pb2.Write(undefine=undefine639)
                    _t1227 = _t1229
                else:
                    if prediction637 == 0:
                        _t1231 = self.parse_define()
                        define638 = _t1231
                        _t1232 = transactions_pb2.Write(define=define638)
                        _t1230 = _t1232
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1227 = _t1230
                _t1224 = _t1227
            _t1221 = _t1224
        result643 = _t1221
        self.record_span(span_start642, "Write")
        return result643

    def parse_define(self) -> transactions_pb2.Define:
        span_start645 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1233 = self.parse_fragment()
        fragment644 = _t1233
        self.consume_literal(")")
        _t1234 = transactions_pb2.Define(fragment=fragment644)
        result646 = _t1234
        self.record_span(span_start645, "Define")
        return result646

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start652 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1235 = self.parse_new_fragment_id()
        new_fragment_id647 = _t1235
        xs648 = []
        cond649 = self.match_lookahead_literal("(", 0)
        while cond649:
            _t1236 = self.parse_declaration()
            item650 = _t1236
            xs648.append(item650)
            cond649 = self.match_lookahead_literal("(", 0)
        declarations651 = xs648
        self.consume_literal(")")
        result653 = self.construct_fragment(new_fragment_id647, declarations651)
        self.record_span(span_start652, "Fragment")
        return result653

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start655 = self.span_start()
        _t1237 = self.parse_fragment_id()
        fragment_id654 = _t1237
        self.start_fragment(fragment_id654)
        result656 = fragment_id654
        self.record_span(span_start655, "FragmentId")
        return result656

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start662 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("functional_dependency", 1):
                _t1239 = 2
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1240 = 3
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t1241 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t1242 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t1243 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t1244 = 1
                                else:
                                    _t1244 = -1
                                _t1243 = _t1244
                            _t1242 = _t1243
                        _t1241 = _t1242
                    _t1240 = _t1241
                _t1239 = _t1240
            _t1238 = _t1239
        else:
            _t1238 = -1
        prediction657 = _t1238
        if prediction657 == 3:
            _t1246 = self.parse_data()
            data661 = _t1246
            _t1247 = logic_pb2.Declaration(data=data661)
            _t1245 = _t1247
        else:
            if prediction657 == 2:
                _t1249 = self.parse_constraint()
                constraint660 = _t1249
                _t1250 = logic_pb2.Declaration(constraint=constraint660)
                _t1248 = _t1250
            else:
                if prediction657 == 1:
                    _t1252 = self.parse_algorithm()
                    algorithm659 = _t1252
                    _t1253 = logic_pb2.Declaration(algorithm=algorithm659)
                    _t1251 = _t1253
                else:
                    if prediction657 == 0:
                        _t1255 = self.parse_def()
                        def658 = _t1255
                        _t1256 = logic_pb2.Declaration()
                        getattr(_t1256, 'def').CopyFrom(def658)
                        _t1254 = _t1256
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1251 = _t1254
                _t1248 = _t1251
            _t1245 = _t1248
        result663 = _t1245
        self.record_span(span_start662, "Declaration")
        return result663

    def parse_def(self) -> logic_pb2.Def:
        span_start667 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1257 = self.parse_relation_id()
        relation_id664 = _t1257
        _t1258 = self.parse_abstraction()
        abstraction665 = _t1258
        if self.match_lookahead_literal("(", 0):
            _t1260 = self.parse_attrs()
            _t1259 = _t1260
        else:
            _t1259 = None
        attrs666 = _t1259
        self.consume_literal(")")
        _t1261 = logic_pb2.Def(name=relation_id664, body=abstraction665, attrs=(attrs666 if attrs666 is not None else []))
        result668 = _t1261
        self.record_span(span_start667, "Def")
        return result668

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start672 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1262 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1263 = 1
            else:
                _t1263 = -1
            _t1262 = _t1263
        prediction669 = _t1262
        if prediction669 == 1:
            uint128671 = self.consume_terminal("UINT128")
            _t1264 = logic_pb2.RelationId(id_low=uint128671.low, id_high=uint128671.high)
        else:
            if prediction669 == 0:
                self.consume_literal(":")
                symbol670 = self.consume_terminal("SYMBOL")
                _t1265 = self.relation_id_from_string(symbol670)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1264 = _t1265
        result673 = _t1264
        self.record_span(span_start672, "RelationId")
        return result673

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start676 = self.span_start()
        self.consume_literal("(")
        _t1266 = self.parse_bindings()
        bindings674 = _t1266
        _t1267 = self.parse_formula()
        formula675 = _t1267
        self.consume_literal(")")
        _t1268 = logic_pb2.Abstraction(vars=(list(bindings674[0]) + list(bindings674[1] if bindings674[1] is not None else [])), value=formula675)
        result677 = _t1268
        self.record_span(span_start676, "Abstraction")
        return result677

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs678 = []
        cond679 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond679:
            _t1269 = self.parse_binding()
            item680 = _t1269
            xs678.append(item680)
            cond679 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings681 = xs678
        if self.match_lookahead_literal("|", 0):
            _t1271 = self.parse_value_bindings()
            _t1270 = _t1271
        else:
            _t1270 = None
        value_bindings682 = _t1270
        self.consume_literal("]")
        return (bindings681, (value_bindings682 if value_bindings682 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start685 = self.span_start()
        symbol683 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1272 = self.parse_type()
        type684 = _t1272
        _t1273 = logic_pb2.Var(name=symbol683)
        _t1274 = logic_pb2.Binding(var=_t1273, type=type684)
        result686 = _t1274
        self.record_span(span_start685, "Binding")
        return result686

    def parse_type(self) -> logic_pb2.Type:
        span_start701 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1275 = 0
        else:
            if self.match_lookahead_literal("UINT128", 0):
                _t1276 = 4
            else:
                if self.match_lookahead_literal("STRING", 0):
                    _t1277 = 1
                else:
                    if self.match_lookahead_literal("MISSING", 0):
                        _t1278 = 8
                    else:
                        if self.match_lookahead_literal("INT32", 0):
                            _t1279 = 11
                        else:
                            if self.match_lookahead_literal("INT128", 0):
                                _t1280 = 5
                            else:
                                if self.match_lookahead_literal("INT", 0):
                                    _t1281 = 2
                                else:
                                    if self.match_lookahead_literal("FLOAT32", 0):
                                        _t1282 = 12
                                    else:
                                        if self.match_lookahead_literal("FLOAT", 0):
                                            _t1283 = 3
                                        else:
                                            if self.match_lookahead_literal("DATETIME", 0):
                                                _t1284 = 7
                                            else:
                                                if self.match_lookahead_literal("DATE", 0):
                                                    _t1285 = 6
                                                else:
                                                    if self.match_lookahead_literal("BOOLEAN", 0):
                                                        _t1286 = 10
                                                    else:
                                                        if self.match_lookahead_literal("(", 0):
                                                            _t1287 = 9
                                                        else:
                                                            _t1287 = -1
                                                        _t1286 = _t1287
                                                    _t1285 = _t1286
                                                _t1284 = _t1285
                                            _t1283 = _t1284
                                        _t1282 = _t1283
                                    _t1281 = _t1282
                                _t1280 = _t1281
                            _t1279 = _t1280
                        _t1278 = _t1279
                    _t1277 = _t1278
                _t1276 = _t1277
            _t1275 = _t1276
        prediction687 = _t1275
        if prediction687 == 12:
            _t1289 = self.parse_float32_type()
            float32_type700 = _t1289
            _t1290 = logic_pb2.Type(float32_type=float32_type700)
            _t1288 = _t1290
        else:
            if prediction687 == 11:
                _t1292 = self.parse_int32_type()
                int32_type699 = _t1292
                _t1293 = logic_pb2.Type(int32_type=int32_type699)
                _t1291 = _t1293
            else:
                if prediction687 == 10:
                    _t1295 = self.parse_boolean_type()
                    boolean_type698 = _t1295
                    _t1296 = logic_pb2.Type(boolean_type=boolean_type698)
                    _t1294 = _t1296
                else:
                    if prediction687 == 9:
                        _t1298 = self.parse_decimal_type()
                        decimal_type697 = _t1298
                        _t1299 = logic_pb2.Type(decimal_type=decimal_type697)
                        _t1297 = _t1299
                    else:
                        if prediction687 == 8:
                            _t1301 = self.parse_missing_type()
                            missing_type696 = _t1301
                            _t1302 = logic_pb2.Type(missing_type=missing_type696)
                            _t1300 = _t1302
                        else:
                            if prediction687 == 7:
                                _t1304 = self.parse_datetime_type()
                                datetime_type695 = _t1304
                                _t1305 = logic_pb2.Type(datetime_type=datetime_type695)
                                _t1303 = _t1305
                            else:
                                if prediction687 == 6:
                                    _t1307 = self.parse_date_type()
                                    date_type694 = _t1307
                                    _t1308 = logic_pb2.Type(date_type=date_type694)
                                    _t1306 = _t1308
                                else:
                                    if prediction687 == 5:
                                        _t1310 = self.parse_int128_type()
                                        int128_type693 = _t1310
                                        _t1311 = logic_pb2.Type(int128_type=int128_type693)
                                        _t1309 = _t1311
                                    else:
                                        if prediction687 == 4:
                                            _t1313 = self.parse_uint128_type()
                                            uint128_type692 = _t1313
                                            _t1314 = logic_pb2.Type(uint128_type=uint128_type692)
                                            _t1312 = _t1314
                                        else:
                                            if prediction687 == 3:
                                                _t1316 = self.parse_float_type()
                                                float_type691 = _t1316
                                                _t1317 = logic_pb2.Type(float_type=float_type691)
                                                _t1315 = _t1317
                                            else:
                                                if prediction687 == 2:
                                                    _t1319 = self.parse_int_type()
                                                    int_type690 = _t1319
                                                    _t1320 = logic_pb2.Type(int_type=int_type690)
                                                    _t1318 = _t1320
                                                else:
                                                    if prediction687 == 1:
                                                        _t1322 = self.parse_string_type()
                                                        string_type689 = _t1322
                                                        _t1323 = logic_pb2.Type(string_type=string_type689)
                                                        _t1321 = _t1323
                                                    else:
                                                        if prediction687 == 0:
                                                            _t1325 = self.parse_unspecified_type()
                                                            unspecified_type688 = _t1325
                                                            _t1326 = logic_pb2.Type(unspecified_type=unspecified_type688)
                                                            _t1324 = _t1326
                                                        else:
                                                            raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1321 = _t1324
                                                    _t1318 = _t1321
                                                _t1315 = _t1318
                                            _t1312 = _t1315
                                        _t1309 = _t1312
                                    _t1306 = _t1309
                                _t1303 = _t1306
                            _t1300 = _t1303
                        _t1297 = _t1300
                    _t1294 = _t1297
                _t1291 = _t1294
            _t1288 = _t1291
        result702 = _t1288
        self.record_span(span_start701, "Type")
        return result702

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start703 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1327 = logic_pb2.UnspecifiedType()
        result704 = _t1327
        self.record_span(span_start703, "UnspecifiedType")
        return result704

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start705 = self.span_start()
        self.consume_literal("STRING")
        _t1328 = logic_pb2.StringType()
        result706 = _t1328
        self.record_span(span_start705, "StringType")
        return result706

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start707 = self.span_start()
        self.consume_literal("INT")
        _t1329 = logic_pb2.IntType()
        result708 = _t1329
        self.record_span(span_start707, "IntType")
        return result708

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start709 = self.span_start()
        self.consume_literal("FLOAT")
        _t1330 = logic_pb2.FloatType()
        result710 = _t1330
        self.record_span(span_start709, "FloatType")
        return result710

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start711 = self.span_start()
        self.consume_literal("UINT128")
        _t1331 = logic_pb2.UInt128Type()
        result712 = _t1331
        self.record_span(span_start711, "UInt128Type")
        return result712

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start713 = self.span_start()
        self.consume_literal("INT128")
        _t1332 = logic_pb2.Int128Type()
        result714 = _t1332
        self.record_span(span_start713, "Int128Type")
        return result714

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start715 = self.span_start()
        self.consume_literal("DATE")
        _t1333 = logic_pb2.DateType()
        result716 = _t1333
        self.record_span(span_start715, "DateType")
        return result716

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start717 = self.span_start()
        self.consume_literal("DATETIME")
        _t1334 = logic_pb2.DateTimeType()
        result718 = _t1334
        self.record_span(span_start717, "DateTimeType")
        return result718

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start719 = self.span_start()
        self.consume_literal("MISSING")
        _t1335 = logic_pb2.MissingType()
        result720 = _t1335
        self.record_span(span_start719, "MissingType")
        return result720

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start723 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int721 = self.consume_terminal("INT")
        int_3722 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1336 = logic_pb2.DecimalType(precision=int(int721), scale=int(int_3722))
        result724 = _t1336
        self.record_span(span_start723, "DecimalType")
        return result724

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start725 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1337 = logic_pb2.BooleanType()
        result726 = _t1337
        self.record_span(span_start725, "BooleanType")
        return result726

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start727 = self.span_start()
        self.consume_literal("INT32")
        _t1338 = logic_pb2.Int32Type()
        result728 = _t1338
        self.record_span(span_start727, "Int32Type")
        return result728

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start729 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1339 = logic_pb2.Float32Type()
        result730 = _t1339
        self.record_span(span_start729, "Float32Type")
        return result730

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs731 = []
        cond732 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond732:
            _t1340 = self.parse_binding()
            item733 = _t1340
            xs731.append(item733)
            cond732 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings734 = xs731
        return bindings734

    def parse_formula(self) -> logic_pb2.Formula:
        span_start749 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1342 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1343 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1344 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1345 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1346 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1347 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1348 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1349 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1350 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1351 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1352 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1353 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1354 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1355 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1356 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1357 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1358 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1359 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1360 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1361 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1362 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1363 = 10
                                                                                                else:
                                                                                                    _t1363 = -1
                                                                                                _t1362 = _t1363
                                                                                            _t1361 = _t1362
                                                                                        _t1360 = _t1361
                                                                                    _t1359 = _t1360
                                                                                _t1358 = _t1359
                                                                            _t1357 = _t1358
                                                                        _t1356 = _t1357
                                                                    _t1355 = _t1356
                                                                _t1354 = _t1355
                                                            _t1353 = _t1354
                                                        _t1352 = _t1353
                                                    _t1351 = _t1352
                                                _t1350 = _t1351
                                            _t1349 = _t1350
                                        _t1348 = _t1349
                                    _t1347 = _t1348
                                _t1346 = _t1347
                            _t1345 = _t1346
                        _t1344 = _t1345
                    _t1343 = _t1344
                _t1342 = _t1343
            _t1341 = _t1342
        else:
            _t1341 = -1
        prediction735 = _t1341
        if prediction735 == 12:
            _t1365 = self.parse_cast()
            cast748 = _t1365
            _t1366 = logic_pb2.Formula(cast=cast748)
            _t1364 = _t1366
        else:
            if prediction735 == 11:
                _t1368 = self.parse_rel_atom()
                rel_atom747 = _t1368
                _t1369 = logic_pb2.Formula(rel_atom=rel_atom747)
                _t1367 = _t1369
            else:
                if prediction735 == 10:
                    _t1371 = self.parse_primitive()
                    primitive746 = _t1371
                    _t1372 = logic_pb2.Formula(primitive=primitive746)
                    _t1370 = _t1372
                else:
                    if prediction735 == 9:
                        _t1374 = self.parse_pragma()
                        pragma745 = _t1374
                        _t1375 = logic_pb2.Formula(pragma=pragma745)
                        _t1373 = _t1375
                    else:
                        if prediction735 == 8:
                            _t1377 = self.parse_atom()
                            atom744 = _t1377
                            _t1378 = logic_pb2.Formula(atom=atom744)
                            _t1376 = _t1378
                        else:
                            if prediction735 == 7:
                                _t1380 = self.parse_ffi()
                                ffi743 = _t1380
                                _t1381 = logic_pb2.Formula(ffi=ffi743)
                                _t1379 = _t1381
                            else:
                                if prediction735 == 6:
                                    _t1383 = self.parse_not()
                                    not742 = _t1383
                                    _t1384 = logic_pb2.Formula()
                                    getattr(_t1384, 'not').CopyFrom(not742)
                                    _t1382 = _t1384
                                else:
                                    if prediction735 == 5:
                                        _t1386 = self.parse_disjunction()
                                        disjunction741 = _t1386
                                        _t1387 = logic_pb2.Formula(disjunction=disjunction741)
                                        _t1385 = _t1387
                                    else:
                                        if prediction735 == 4:
                                            _t1389 = self.parse_conjunction()
                                            conjunction740 = _t1389
                                            _t1390 = logic_pb2.Formula(conjunction=conjunction740)
                                            _t1388 = _t1390
                                        else:
                                            if prediction735 == 3:
                                                _t1392 = self.parse_reduce()
                                                reduce739 = _t1392
                                                _t1393 = logic_pb2.Formula(reduce=reduce739)
                                                _t1391 = _t1393
                                            else:
                                                if prediction735 == 2:
                                                    _t1395 = self.parse_exists()
                                                    exists738 = _t1395
                                                    _t1396 = logic_pb2.Formula(exists=exists738)
                                                    _t1394 = _t1396
                                                else:
                                                    if prediction735 == 1:
                                                        _t1398 = self.parse_false()
                                                        false737 = _t1398
                                                        _t1399 = logic_pb2.Formula(disjunction=false737)
                                                        _t1397 = _t1399
                                                    else:
                                                        if prediction735 == 0:
                                                            _t1401 = self.parse_true()
                                                            true736 = _t1401
                                                            _t1402 = logic_pb2.Formula(conjunction=true736)
                                                            _t1400 = _t1402
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1397 = _t1400
                                                    _t1394 = _t1397
                                                _t1391 = _t1394
                                            _t1388 = _t1391
                                        _t1385 = _t1388
                                    _t1382 = _t1385
                                _t1379 = _t1382
                            _t1376 = _t1379
                        _t1373 = _t1376
                    _t1370 = _t1373
                _t1367 = _t1370
            _t1364 = _t1367
        result750 = _t1364
        self.record_span(span_start749, "Formula")
        return result750

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start751 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1403 = logic_pb2.Conjunction(args=[])
        result752 = _t1403
        self.record_span(span_start751, "Conjunction")
        return result752

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start753 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1404 = logic_pb2.Disjunction(args=[])
        result754 = _t1404
        self.record_span(span_start753, "Disjunction")
        return result754

    def parse_exists(self) -> logic_pb2.Exists:
        span_start757 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1405 = self.parse_bindings()
        bindings755 = _t1405
        _t1406 = self.parse_formula()
        formula756 = _t1406
        self.consume_literal(")")
        _t1407 = logic_pb2.Abstraction(vars=(list(bindings755[0]) + list(bindings755[1] if bindings755[1] is not None else [])), value=formula756)
        _t1408 = logic_pb2.Exists(body=_t1407)
        result758 = _t1408
        self.record_span(span_start757, "Exists")
        return result758

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start762 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1409 = self.parse_abstraction()
        abstraction759 = _t1409
        _t1410 = self.parse_abstraction()
        abstraction_3760 = _t1410
        _t1411 = self.parse_terms()
        terms761 = _t1411
        self.consume_literal(")")
        _t1412 = logic_pb2.Reduce(op=abstraction759, body=abstraction_3760, terms=terms761)
        result763 = _t1412
        self.record_span(span_start762, "Reduce")
        return result763

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs764 = []
        cond765 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond765:
            _t1413 = self.parse_term()
            item766 = _t1413
            xs764.append(item766)
            cond765 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms767 = xs764
        self.consume_literal(")")
        return terms767

    def parse_term(self) -> logic_pb2.Term:
        span_start771 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1414 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1415 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1416 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1417 = 1
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1418 = 1
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1419 = 0
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1420 = 1
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1421 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1422 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1423 = 1
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1424 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1425 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1426 = 1
                                                        else:
                                                            _t1426 = -1
                                                        _t1425 = _t1426
                                                    _t1424 = _t1425
                                                _t1423 = _t1424
                                            _t1422 = _t1423
                                        _t1421 = _t1422
                                    _t1420 = _t1421
                                _t1419 = _t1420
                            _t1418 = _t1419
                        _t1417 = _t1418
                    _t1416 = _t1417
                _t1415 = _t1416
            _t1414 = _t1415
        prediction768 = _t1414
        if prediction768 == 1:
            _t1428 = self.parse_constant()
            constant770 = _t1428
            _t1429 = logic_pb2.Term(constant=constant770)
            _t1427 = _t1429
        else:
            if prediction768 == 0:
                _t1431 = self.parse_var()
                var769 = _t1431
                _t1432 = logic_pb2.Term(var=var769)
                _t1430 = _t1432
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1427 = _t1430
        result772 = _t1427
        self.record_span(span_start771, "Term")
        return result772

    def parse_var(self) -> logic_pb2.Var:
        span_start774 = self.span_start()
        symbol773 = self.consume_terminal("SYMBOL")
        _t1433 = logic_pb2.Var(name=symbol773)
        result775 = _t1433
        self.record_span(span_start774, "Var")
        return result775

    def parse_constant(self) -> logic_pb2.Value:
        span_start777 = self.span_start()
        _t1434 = self.parse_value()
        value776 = _t1434
        result778 = value776
        self.record_span(span_start777, "Value")
        return result778

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start783 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs779 = []
        cond780 = self.match_lookahead_literal("(", 0)
        while cond780:
            _t1435 = self.parse_formula()
            item781 = _t1435
            xs779.append(item781)
            cond780 = self.match_lookahead_literal("(", 0)
        formulas782 = xs779
        self.consume_literal(")")
        _t1436 = logic_pb2.Conjunction(args=formulas782)
        result784 = _t1436
        self.record_span(span_start783, "Conjunction")
        return result784

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start789 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs785 = []
        cond786 = self.match_lookahead_literal("(", 0)
        while cond786:
            _t1437 = self.parse_formula()
            item787 = _t1437
            xs785.append(item787)
            cond786 = self.match_lookahead_literal("(", 0)
        formulas788 = xs785
        self.consume_literal(")")
        _t1438 = logic_pb2.Disjunction(args=formulas788)
        result790 = _t1438
        self.record_span(span_start789, "Disjunction")
        return result790

    def parse_not(self) -> logic_pb2.Not:
        span_start792 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1439 = self.parse_formula()
        formula791 = _t1439
        self.consume_literal(")")
        _t1440 = logic_pb2.Not(arg=formula791)
        result793 = _t1440
        self.record_span(span_start792, "Not")
        return result793

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start797 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1441 = self.parse_name()
        name794 = _t1441
        _t1442 = self.parse_ffi_args()
        ffi_args795 = _t1442
        _t1443 = self.parse_terms()
        terms796 = _t1443
        self.consume_literal(")")
        _t1444 = logic_pb2.FFI(name=name794, args=ffi_args795, terms=terms796)
        result798 = _t1444
        self.record_span(span_start797, "FFI")
        return result798

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol799 = self.consume_terminal("SYMBOL")
        return symbol799

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs800 = []
        cond801 = self.match_lookahead_literal("(", 0)
        while cond801:
            _t1445 = self.parse_abstraction()
            item802 = _t1445
            xs800.append(item802)
            cond801 = self.match_lookahead_literal("(", 0)
        abstractions803 = xs800
        self.consume_literal(")")
        return abstractions803

    def parse_atom(self) -> logic_pb2.Atom:
        span_start809 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1446 = self.parse_relation_id()
        relation_id804 = _t1446
        xs805 = []
        cond806 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond806:
            _t1447 = self.parse_term()
            item807 = _t1447
            xs805.append(item807)
            cond806 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms808 = xs805
        self.consume_literal(")")
        _t1448 = logic_pb2.Atom(name=relation_id804, terms=terms808)
        result810 = _t1448
        self.record_span(span_start809, "Atom")
        return result810

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start816 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1449 = self.parse_name()
        name811 = _t1449
        xs812 = []
        cond813 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond813:
            _t1450 = self.parse_term()
            item814 = _t1450
            xs812.append(item814)
            cond813 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms815 = xs812
        self.consume_literal(")")
        _t1451 = logic_pb2.Pragma(name=name811, terms=terms815)
        result817 = _t1451
        self.record_span(span_start816, "Pragma")
        return result817

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start833 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1453 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1454 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1455 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1456 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1457 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1458 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1459 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1460 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1461 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1462 = 7
                                                else:
                                                    _t1462 = -1
                                                _t1461 = _t1462
                                            _t1460 = _t1461
                                        _t1459 = _t1460
                                    _t1458 = _t1459
                                _t1457 = _t1458
                            _t1456 = _t1457
                        _t1455 = _t1456
                    _t1454 = _t1455
                _t1453 = _t1454
            _t1452 = _t1453
        else:
            _t1452 = -1
        prediction818 = _t1452
        if prediction818 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1464 = self.parse_name()
            name828 = _t1464
            xs829 = []
            cond830 = (((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            while cond830:
                _t1465 = self.parse_rel_term()
                item831 = _t1465
                xs829.append(item831)
                cond830 = (((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            rel_terms832 = xs829
            self.consume_literal(")")
            _t1466 = logic_pb2.Primitive(name=name828, terms=rel_terms832)
            _t1463 = _t1466
        else:
            if prediction818 == 8:
                _t1468 = self.parse_divide()
                divide827 = _t1468
                _t1467 = divide827
            else:
                if prediction818 == 7:
                    _t1470 = self.parse_multiply()
                    multiply826 = _t1470
                    _t1469 = multiply826
                else:
                    if prediction818 == 6:
                        _t1472 = self.parse_minus()
                        minus825 = _t1472
                        _t1471 = minus825
                    else:
                        if prediction818 == 5:
                            _t1474 = self.parse_add()
                            add824 = _t1474
                            _t1473 = add824
                        else:
                            if prediction818 == 4:
                                _t1476 = self.parse_gt_eq()
                                gt_eq823 = _t1476
                                _t1475 = gt_eq823
                            else:
                                if prediction818 == 3:
                                    _t1478 = self.parse_gt()
                                    gt822 = _t1478
                                    _t1477 = gt822
                                else:
                                    if prediction818 == 2:
                                        _t1480 = self.parse_lt_eq()
                                        lt_eq821 = _t1480
                                        _t1479 = lt_eq821
                                    else:
                                        if prediction818 == 1:
                                            _t1482 = self.parse_lt()
                                            lt820 = _t1482
                                            _t1481 = lt820
                                        else:
                                            if prediction818 == 0:
                                                _t1484 = self.parse_eq()
                                                eq819 = _t1484
                                                _t1483 = eq819
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1481 = _t1483
                                        _t1479 = _t1481
                                    _t1477 = _t1479
                                _t1475 = _t1477
                            _t1473 = _t1475
                        _t1471 = _t1473
                    _t1469 = _t1471
                _t1467 = _t1469
            _t1463 = _t1467
        result834 = _t1463
        self.record_span(span_start833, "Primitive")
        return result834

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start837 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1485 = self.parse_term()
        term835 = _t1485
        _t1486 = self.parse_term()
        term_3836 = _t1486
        self.consume_literal(")")
        _t1487 = logic_pb2.RelTerm(term=term835)
        _t1488 = logic_pb2.RelTerm(term=term_3836)
        _t1489 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1487, _t1488])
        result838 = _t1489
        self.record_span(span_start837, "Primitive")
        return result838

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start841 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1490 = self.parse_term()
        term839 = _t1490
        _t1491 = self.parse_term()
        term_3840 = _t1491
        self.consume_literal(")")
        _t1492 = logic_pb2.RelTerm(term=term839)
        _t1493 = logic_pb2.RelTerm(term=term_3840)
        _t1494 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1492, _t1493])
        result842 = _t1494
        self.record_span(span_start841, "Primitive")
        return result842

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start845 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1495 = self.parse_term()
        term843 = _t1495
        _t1496 = self.parse_term()
        term_3844 = _t1496
        self.consume_literal(")")
        _t1497 = logic_pb2.RelTerm(term=term843)
        _t1498 = logic_pb2.RelTerm(term=term_3844)
        _t1499 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1497, _t1498])
        result846 = _t1499
        self.record_span(span_start845, "Primitive")
        return result846

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start849 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1500 = self.parse_term()
        term847 = _t1500
        _t1501 = self.parse_term()
        term_3848 = _t1501
        self.consume_literal(")")
        _t1502 = logic_pb2.RelTerm(term=term847)
        _t1503 = logic_pb2.RelTerm(term=term_3848)
        _t1504 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1502, _t1503])
        result850 = _t1504
        self.record_span(span_start849, "Primitive")
        return result850

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start853 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1505 = self.parse_term()
        term851 = _t1505
        _t1506 = self.parse_term()
        term_3852 = _t1506
        self.consume_literal(")")
        _t1507 = logic_pb2.RelTerm(term=term851)
        _t1508 = logic_pb2.RelTerm(term=term_3852)
        _t1509 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1507, _t1508])
        result854 = _t1509
        self.record_span(span_start853, "Primitive")
        return result854

    def parse_add(self) -> logic_pb2.Primitive:
        span_start858 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1510 = self.parse_term()
        term855 = _t1510
        _t1511 = self.parse_term()
        term_3856 = _t1511
        _t1512 = self.parse_term()
        term_4857 = _t1512
        self.consume_literal(")")
        _t1513 = logic_pb2.RelTerm(term=term855)
        _t1514 = logic_pb2.RelTerm(term=term_3856)
        _t1515 = logic_pb2.RelTerm(term=term_4857)
        _t1516 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1513, _t1514, _t1515])
        result859 = _t1516
        self.record_span(span_start858, "Primitive")
        return result859

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start863 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1517 = self.parse_term()
        term860 = _t1517
        _t1518 = self.parse_term()
        term_3861 = _t1518
        _t1519 = self.parse_term()
        term_4862 = _t1519
        self.consume_literal(")")
        _t1520 = logic_pb2.RelTerm(term=term860)
        _t1521 = logic_pb2.RelTerm(term=term_3861)
        _t1522 = logic_pb2.RelTerm(term=term_4862)
        _t1523 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1520, _t1521, _t1522])
        result864 = _t1523
        self.record_span(span_start863, "Primitive")
        return result864

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start868 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1524 = self.parse_term()
        term865 = _t1524
        _t1525 = self.parse_term()
        term_3866 = _t1525
        _t1526 = self.parse_term()
        term_4867 = _t1526
        self.consume_literal(")")
        _t1527 = logic_pb2.RelTerm(term=term865)
        _t1528 = logic_pb2.RelTerm(term=term_3866)
        _t1529 = logic_pb2.RelTerm(term=term_4867)
        _t1530 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1527, _t1528, _t1529])
        result869 = _t1530
        self.record_span(span_start868, "Primitive")
        return result869

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start873 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1531 = self.parse_term()
        term870 = _t1531
        _t1532 = self.parse_term()
        term_3871 = _t1532
        _t1533 = self.parse_term()
        term_4872 = _t1533
        self.consume_literal(")")
        _t1534 = logic_pb2.RelTerm(term=term870)
        _t1535 = logic_pb2.RelTerm(term=term_3871)
        _t1536 = logic_pb2.RelTerm(term=term_4872)
        _t1537 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1534, _t1535, _t1536])
        result874 = _t1537
        self.record_span(span_start873, "Primitive")
        return result874

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start878 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1538 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1539 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1540 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1541 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1542 = 0
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1543 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1544 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1545 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1546 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1547 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1548 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1549 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1550 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1551 = 1
                                                            else:
                                                                _t1551 = -1
                                                            _t1550 = _t1551
                                                        _t1549 = _t1550
                                                    _t1548 = _t1549
                                                _t1547 = _t1548
                                            _t1546 = _t1547
                                        _t1545 = _t1546
                                    _t1544 = _t1545
                                _t1543 = _t1544
                            _t1542 = _t1543
                        _t1541 = _t1542
                    _t1540 = _t1541
                _t1539 = _t1540
            _t1538 = _t1539
        prediction875 = _t1538
        if prediction875 == 1:
            _t1553 = self.parse_term()
            term877 = _t1553
            _t1554 = logic_pb2.RelTerm(term=term877)
            _t1552 = _t1554
        else:
            if prediction875 == 0:
                _t1556 = self.parse_specialized_value()
                specialized_value876 = _t1556
                _t1557 = logic_pb2.RelTerm(specialized_value=specialized_value876)
                _t1555 = _t1557
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1552 = _t1555
        result879 = _t1552
        self.record_span(span_start878, "RelTerm")
        return result879

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start881 = self.span_start()
        self.consume_literal("#")
        _t1558 = self.parse_value()
        value880 = _t1558
        result882 = value880
        self.record_span(span_start881, "Value")
        return result882

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start888 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1559 = self.parse_name()
        name883 = _t1559
        xs884 = []
        cond885 = (((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond885:
            _t1560 = self.parse_rel_term()
            item886 = _t1560
            xs884.append(item886)
            cond885 = (((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        rel_terms887 = xs884
        self.consume_literal(")")
        _t1561 = logic_pb2.RelAtom(name=name883, terms=rel_terms887)
        result889 = _t1561
        self.record_span(span_start888, "RelAtom")
        return result889

    def parse_cast(self) -> logic_pb2.Cast:
        span_start892 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1562 = self.parse_term()
        term890 = _t1562
        _t1563 = self.parse_term()
        term_3891 = _t1563
        self.consume_literal(")")
        _t1564 = logic_pb2.Cast(input=term890, result=term_3891)
        result893 = _t1564
        self.record_span(span_start892, "Cast")
        return result893

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs894 = []
        cond895 = self.match_lookahead_literal("(", 0)
        while cond895:
            _t1565 = self.parse_attribute()
            item896 = _t1565
            xs894.append(item896)
            cond895 = self.match_lookahead_literal("(", 0)
        attributes897 = xs894
        self.consume_literal(")")
        return attributes897

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start903 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1566 = self.parse_name()
        name898 = _t1566
        xs899 = []
        cond900 = (((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond900:
            _t1567 = self.parse_value()
            item901 = _t1567
            xs899.append(item901)
            cond900 = (((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        values902 = xs899
        self.consume_literal(")")
        _t1568 = logic_pb2.Attribute(name=name898, args=values902)
        result904 = _t1568
        self.record_span(span_start903, "Attribute")
        return result904

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start910 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs905 = []
        cond906 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond906:
            _t1569 = self.parse_relation_id()
            item907 = _t1569
            xs905.append(item907)
            cond906 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids908 = xs905
        _t1570 = self.parse_script()
        script909 = _t1570
        self.consume_literal(")")
        _t1571 = logic_pb2.Algorithm(body=script909)
        getattr(_t1571, 'global').extend(relation_ids908)
        result911 = _t1571
        self.record_span(span_start910, "Algorithm")
        return result911

    def parse_script(self) -> logic_pb2.Script:
        span_start916 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs912 = []
        cond913 = self.match_lookahead_literal("(", 0)
        while cond913:
            _t1572 = self.parse_construct()
            item914 = _t1572
            xs912.append(item914)
            cond913 = self.match_lookahead_literal("(", 0)
        constructs915 = xs912
        self.consume_literal(")")
        _t1573 = logic_pb2.Script(constructs=constructs915)
        result917 = _t1573
        self.record_span(span_start916, "Script")
        return result917

    def parse_construct(self) -> logic_pb2.Construct:
        span_start921 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1575 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1576 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1577 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1578 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1579 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1580 = 1
                                else:
                                    _t1580 = -1
                                _t1579 = _t1580
                            _t1578 = _t1579
                        _t1577 = _t1578
                    _t1576 = _t1577
                _t1575 = _t1576
            _t1574 = _t1575
        else:
            _t1574 = -1
        prediction918 = _t1574
        if prediction918 == 1:
            _t1582 = self.parse_instruction()
            instruction920 = _t1582
            _t1583 = logic_pb2.Construct(instruction=instruction920)
            _t1581 = _t1583
        else:
            if prediction918 == 0:
                _t1585 = self.parse_loop()
                loop919 = _t1585
                _t1586 = logic_pb2.Construct(loop=loop919)
                _t1584 = _t1586
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1581 = _t1584
        result922 = _t1581
        self.record_span(span_start921, "Construct")
        return result922

    def parse_loop(self) -> logic_pb2.Loop:
        span_start925 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1587 = self.parse_init()
        init923 = _t1587
        _t1588 = self.parse_script()
        script924 = _t1588
        self.consume_literal(")")
        _t1589 = logic_pb2.Loop(init=init923, body=script924)
        result926 = _t1589
        self.record_span(span_start925, "Loop")
        return result926

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs927 = []
        cond928 = self.match_lookahead_literal("(", 0)
        while cond928:
            _t1590 = self.parse_instruction()
            item929 = _t1590
            xs927.append(item929)
            cond928 = self.match_lookahead_literal("(", 0)
        instructions930 = xs927
        self.consume_literal(")")
        return instructions930

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start937 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1592 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1593 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1594 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1595 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1596 = 0
                            else:
                                _t1596 = -1
                            _t1595 = _t1596
                        _t1594 = _t1595
                    _t1593 = _t1594
                _t1592 = _t1593
            _t1591 = _t1592
        else:
            _t1591 = -1
        prediction931 = _t1591
        if prediction931 == 4:
            _t1598 = self.parse_monus_def()
            monus_def936 = _t1598
            _t1599 = logic_pb2.Instruction(monus_def=monus_def936)
            _t1597 = _t1599
        else:
            if prediction931 == 3:
                _t1601 = self.parse_monoid_def()
                monoid_def935 = _t1601
                _t1602 = logic_pb2.Instruction(monoid_def=monoid_def935)
                _t1600 = _t1602
            else:
                if prediction931 == 2:
                    _t1604 = self.parse_break()
                    break934 = _t1604
                    _t1605 = logic_pb2.Instruction()
                    getattr(_t1605, 'break').CopyFrom(break934)
                    _t1603 = _t1605
                else:
                    if prediction931 == 1:
                        _t1607 = self.parse_upsert()
                        upsert933 = _t1607
                        _t1608 = logic_pb2.Instruction(upsert=upsert933)
                        _t1606 = _t1608
                    else:
                        if prediction931 == 0:
                            _t1610 = self.parse_assign()
                            assign932 = _t1610
                            _t1611 = logic_pb2.Instruction(assign=assign932)
                            _t1609 = _t1611
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1606 = _t1609
                    _t1603 = _t1606
                _t1600 = _t1603
            _t1597 = _t1600
        result938 = _t1597
        self.record_span(span_start937, "Instruction")
        return result938

    def parse_assign(self) -> logic_pb2.Assign:
        span_start942 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1612 = self.parse_relation_id()
        relation_id939 = _t1612
        _t1613 = self.parse_abstraction()
        abstraction940 = _t1613
        if self.match_lookahead_literal("(", 0):
            _t1615 = self.parse_attrs()
            _t1614 = _t1615
        else:
            _t1614 = None
        attrs941 = _t1614
        self.consume_literal(")")
        _t1616 = logic_pb2.Assign(name=relation_id939, body=abstraction940, attrs=(attrs941 if attrs941 is not None else []))
        result943 = _t1616
        self.record_span(span_start942, "Assign")
        return result943

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start947 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1617 = self.parse_relation_id()
        relation_id944 = _t1617
        _t1618 = self.parse_abstraction_with_arity()
        abstraction_with_arity945 = _t1618
        if self.match_lookahead_literal("(", 0):
            _t1620 = self.parse_attrs()
            _t1619 = _t1620
        else:
            _t1619 = None
        attrs946 = _t1619
        self.consume_literal(")")
        _t1621 = logic_pb2.Upsert(name=relation_id944, body=abstraction_with_arity945[0], attrs=(attrs946 if attrs946 is not None else []), value_arity=abstraction_with_arity945[1])
        result948 = _t1621
        self.record_span(span_start947, "Upsert")
        return result948

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1622 = self.parse_bindings()
        bindings949 = _t1622
        _t1623 = self.parse_formula()
        formula950 = _t1623
        self.consume_literal(")")
        _t1624 = logic_pb2.Abstraction(vars=(list(bindings949[0]) + list(bindings949[1] if bindings949[1] is not None else [])), value=formula950)
        return (_t1624, len(bindings949[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start954 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1625 = self.parse_relation_id()
        relation_id951 = _t1625
        _t1626 = self.parse_abstraction()
        abstraction952 = _t1626
        if self.match_lookahead_literal("(", 0):
            _t1628 = self.parse_attrs()
            _t1627 = _t1628
        else:
            _t1627 = None
        attrs953 = _t1627
        self.consume_literal(")")
        _t1629 = logic_pb2.Break(name=relation_id951, body=abstraction952, attrs=(attrs953 if attrs953 is not None else []))
        result955 = _t1629
        self.record_span(span_start954, "Break")
        return result955

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start960 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1630 = self.parse_monoid()
        monoid956 = _t1630
        _t1631 = self.parse_relation_id()
        relation_id957 = _t1631
        _t1632 = self.parse_abstraction_with_arity()
        abstraction_with_arity958 = _t1632
        if self.match_lookahead_literal("(", 0):
            _t1634 = self.parse_attrs()
            _t1633 = _t1634
        else:
            _t1633 = None
        attrs959 = _t1633
        self.consume_literal(")")
        _t1635 = logic_pb2.MonoidDef(monoid=monoid956, name=relation_id957, body=abstraction_with_arity958[0], attrs=(attrs959 if attrs959 is not None else []), value_arity=abstraction_with_arity958[1])
        result961 = _t1635
        self.record_span(span_start960, "MonoidDef")
        return result961

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start967 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1637 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1638 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1639 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1640 = 2
                        else:
                            _t1640 = -1
                        _t1639 = _t1640
                    _t1638 = _t1639
                _t1637 = _t1638
            _t1636 = _t1637
        else:
            _t1636 = -1
        prediction962 = _t1636
        if prediction962 == 3:
            _t1642 = self.parse_sum_monoid()
            sum_monoid966 = _t1642
            _t1643 = logic_pb2.Monoid(sum_monoid=sum_monoid966)
            _t1641 = _t1643
        else:
            if prediction962 == 2:
                _t1645 = self.parse_max_monoid()
                max_monoid965 = _t1645
                _t1646 = logic_pb2.Monoid(max_monoid=max_monoid965)
                _t1644 = _t1646
            else:
                if prediction962 == 1:
                    _t1648 = self.parse_min_monoid()
                    min_monoid964 = _t1648
                    _t1649 = logic_pb2.Monoid(min_monoid=min_monoid964)
                    _t1647 = _t1649
                else:
                    if prediction962 == 0:
                        _t1651 = self.parse_or_monoid()
                        or_monoid963 = _t1651
                        _t1652 = logic_pb2.Monoid(or_monoid=or_monoid963)
                        _t1650 = _t1652
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1647 = _t1650
                _t1644 = _t1647
            _t1641 = _t1644
        result968 = _t1641
        self.record_span(span_start967, "Monoid")
        return result968

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start969 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1653 = logic_pb2.OrMonoid()
        result970 = _t1653
        self.record_span(span_start969, "OrMonoid")
        return result970

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start972 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1654 = self.parse_type()
        type971 = _t1654
        self.consume_literal(")")
        _t1655 = logic_pb2.MinMonoid(type=type971)
        result973 = _t1655
        self.record_span(span_start972, "MinMonoid")
        return result973

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start975 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1656 = self.parse_type()
        type974 = _t1656
        self.consume_literal(")")
        _t1657 = logic_pb2.MaxMonoid(type=type974)
        result976 = _t1657
        self.record_span(span_start975, "MaxMonoid")
        return result976

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start978 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1658 = self.parse_type()
        type977 = _t1658
        self.consume_literal(")")
        _t1659 = logic_pb2.SumMonoid(type=type977)
        result979 = _t1659
        self.record_span(span_start978, "SumMonoid")
        return result979

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start984 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1660 = self.parse_monoid()
        monoid980 = _t1660
        _t1661 = self.parse_relation_id()
        relation_id981 = _t1661
        _t1662 = self.parse_abstraction_with_arity()
        abstraction_with_arity982 = _t1662
        if self.match_lookahead_literal("(", 0):
            _t1664 = self.parse_attrs()
            _t1663 = _t1664
        else:
            _t1663 = None
        attrs983 = _t1663
        self.consume_literal(")")
        _t1665 = logic_pb2.MonusDef(monoid=monoid980, name=relation_id981, body=abstraction_with_arity982[0], attrs=(attrs983 if attrs983 is not None else []), value_arity=abstraction_with_arity982[1])
        result985 = _t1665
        self.record_span(span_start984, "MonusDef")
        return result985

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start990 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1666 = self.parse_relation_id()
        relation_id986 = _t1666
        _t1667 = self.parse_abstraction()
        abstraction987 = _t1667
        _t1668 = self.parse_functional_dependency_keys()
        functional_dependency_keys988 = _t1668
        _t1669 = self.parse_functional_dependency_values()
        functional_dependency_values989 = _t1669
        self.consume_literal(")")
        _t1670 = logic_pb2.FunctionalDependency(guard=abstraction987, keys=functional_dependency_keys988, values=functional_dependency_values989)
        _t1671 = logic_pb2.Constraint(name=relation_id986, functional_dependency=_t1670)
        result991 = _t1671
        self.record_span(span_start990, "Constraint")
        return result991

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs992 = []
        cond993 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond993:
            _t1672 = self.parse_var()
            item994 = _t1672
            xs992.append(item994)
            cond993 = self.match_lookahead_terminal("SYMBOL", 0)
        vars995 = xs992
        self.consume_literal(")")
        return vars995

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs996 = []
        cond997 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond997:
            _t1673 = self.parse_var()
            item998 = _t1673
            xs996.append(item998)
            cond997 = self.match_lookahead_terminal("SYMBOL", 0)
        vars999 = xs996
        self.consume_literal(")")
        return vars999

    def parse_data(self) -> logic_pb2.Data:
        span_start1004 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("edb", 1):
                _t1675 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1676 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1677 = 1
                    else:
                        _t1677 = -1
                    _t1676 = _t1677
                _t1675 = _t1676
            _t1674 = _t1675
        else:
            _t1674 = -1
        prediction1000 = _t1674
        if prediction1000 == 2:
            _t1679 = self.parse_csv_data()
            csv_data1003 = _t1679
            _t1680 = logic_pb2.Data(csv_data=csv_data1003)
            _t1678 = _t1680
        else:
            if prediction1000 == 1:
                _t1682 = self.parse_betree_relation()
                betree_relation1002 = _t1682
                _t1683 = logic_pb2.Data(betree_relation=betree_relation1002)
                _t1681 = _t1683
            else:
                if prediction1000 == 0:
                    _t1685 = self.parse_edb()
                    edb1001 = _t1685
                    _t1686 = logic_pb2.Data(edb=edb1001)
                    _t1684 = _t1686
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1681 = _t1684
            _t1678 = _t1681
        result1005 = _t1678
        self.record_span(span_start1004, "Data")
        return result1005

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1009 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1687 = self.parse_relation_id()
        relation_id1006 = _t1687
        _t1688 = self.parse_edb_path()
        edb_path1007 = _t1688
        _t1689 = self.parse_edb_types()
        edb_types1008 = _t1689
        self.consume_literal(")")
        _t1690 = logic_pb2.EDB(target_id=relation_id1006, path=edb_path1007, types=edb_types1008)
        result1010 = _t1690
        self.record_span(span_start1009, "EDB")
        return result1010

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1011 = []
        cond1012 = self.match_lookahead_terminal("STRING", 0)
        while cond1012:
            item1013 = self.consume_terminal("STRING")
            xs1011.append(item1013)
            cond1012 = self.match_lookahead_terminal("STRING", 0)
        strings1014 = xs1011
        self.consume_literal("]")
        return strings1014

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1015 = []
        cond1016 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1016:
            _t1691 = self.parse_type()
            item1017 = _t1691
            xs1015.append(item1017)
            cond1016 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1018 = xs1015
        self.consume_literal("]")
        return types1018

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1021 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1692 = self.parse_relation_id()
        relation_id1019 = _t1692
        _t1693 = self.parse_betree_info()
        betree_info1020 = _t1693
        self.consume_literal(")")
        _t1694 = logic_pb2.BeTreeRelation(name=relation_id1019, relation_info=betree_info1020)
        result1022 = _t1694
        self.record_span(span_start1021, "BeTreeRelation")
        return result1022

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1026 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1695 = self.parse_betree_info_key_types()
        betree_info_key_types1023 = _t1695
        _t1696 = self.parse_betree_info_value_types()
        betree_info_value_types1024 = _t1696
        _t1697 = self.parse_config_dict()
        config_dict1025 = _t1697
        self.consume_literal(")")
        _t1698 = self.construct_betree_info(betree_info_key_types1023, betree_info_value_types1024, config_dict1025)
        result1027 = _t1698
        self.record_span(span_start1026, "BeTreeInfo")
        return result1027

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1028 = []
        cond1029 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1029:
            _t1699 = self.parse_type()
            item1030 = _t1699
            xs1028.append(item1030)
            cond1029 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1031 = xs1028
        self.consume_literal(")")
        return types1031

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1032 = []
        cond1033 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1033:
            _t1700 = self.parse_type()
            item1034 = _t1700
            xs1032.append(item1034)
            cond1033 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1035 = xs1032
        self.consume_literal(")")
        return types1035

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1040 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1701 = self.parse_csvlocator()
        csvlocator1036 = _t1701
        _t1702 = self.parse_csv_config()
        csv_config1037 = _t1702
        _t1703 = self.parse_gnf_columns()
        gnf_columns1038 = _t1703
        _t1704 = self.parse_csv_asof()
        csv_asof1039 = _t1704
        self.consume_literal(")")
        _t1705 = logic_pb2.CSVData(locator=csvlocator1036, config=csv_config1037, columns=gnf_columns1038, asof=csv_asof1039)
        result1041 = _t1705
        self.record_span(span_start1040, "CSVData")
        return result1041

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1044 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1707 = self.parse_csv_locator_paths()
            _t1706 = _t1707
        else:
            _t1706 = None
        csv_locator_paths1042 = _t1706
        if self.match_lookahead_literal("(", 0):
            _t1709 = self.parse_csv_locator_inline_data()
            _t1708 = _t1709
        else:
            _t1708 = None
        csv_locator_inline_data1043 = _t1708
        self.consume_literal(")")
        _t1710 = logic_pb2.CSVLocator(paths=(csv_locator_paths1042 if csv_locator_paths1042 is not None else []), inline_data=(csv_locator_inline_data1043 if csv_locator_inline_data1043 is not None else "").encode())
        result1045 = _t1710
        self.record_span(span_start1044, "CSVLocator")
        return result1045

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1046 = []
        cond1047 = self.match_lookahead_terminal("STRING", 0)
        while cond1047:
            item1048 = self.consume_terminal("STRING")
            xs1046.append(item1048)
            cond1047 = self.match_lookahead_terminal("STRING", 0)
        strings1049 = xs1046
        self.consume_literal(")")
        return strings1049

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1050 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1050

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1052 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1711 = self.parse_config_dict()
        config_dict1051 = _t1711
        self.consume_literal(")")
        _t1712 = self.construct_csv_config(config_dict1051)
        result1053 = _t1712
        self.record_span(span_start1052, "CSVConfig")
        return result1053

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1054 = []
        cond1055 = self.match_lookahead_literal("(", 0)
        while cond1055:
            _t1713 = self.parse_gnf_column()
            item1056 = _t1713
            xs1054.append(item1056)
            cond1055 = self.match_lookahead_literal("(", 0)
        gnf_columns1057 = xs1054
        self.consume_literal(")")
        return gnf_columns1057

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1064 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1714 = self.parse_gnf_column_path()
        gnf_column_path1058 = _t1714
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1716 = self.parse_relation_id()
            _t1715 = _t1716
        else:
            _t1715 = None
        relation_id1059 = _t1715
        self.consume_literal("[")
        xs1060 = []
        cond1061 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1061:
            _t1717 = self.parse_type()
            item1062 = _t1717
            xs1060.append(item1062)
            cond1061 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1063 = xs1060
        self.consume_literal("]")
        self.consume_literal(")")
        _t1718 = logic_pb2.GNFColumn(column_path=gnf_column_path1058, target_id=relation_id1059, types=types1063)
        result1065 = _t1718
        self.record_span(span_start1064, "GNFColumn")
        return result1065

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1719 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1720 = 0
            else:
                _t1720 = -1
            _t1719 = _t1720
        prediction1066 = _t1719
        if prediction1066 == 1:
            self.consume_literal("[")
            xs1068 = []
            cond1069 = self.match_lookahead_terminal("STRING", 0)
            while cond1069:
                item1070 = self.consume_terminal("STRING")
                xs1068.append(item1070)
                cond1069 = self.match_lookahead_terminal("STRING", 0)
            strings1071 = xs1068
            self.consume_literal("]")
            _t1721 = strings1071
        else:
            if prediction1066 == 0:
                string1067 = self.consume_terminal("STRING")
                _t1722 = [string1067]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1721 = _t1722
        return _t1721

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1072 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1072

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1074 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1723 = self.parse_fragment_id()
        fragment_id1073 = _t1723
        self.consume_literal(")")
        _t1724 = transactions_pb2.Undefine(fragment_id=fragment_id1073)
        result1075 = _t1724
        self.record_span(span_start1074, "Undefine")
        return result1075

    def parse_context(self) -> transactions_pb2.Context:
        span_start1080 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1076 = []
        cond1077 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1077:
            _t1725 = self.parse_relation_id()
            item1078 = _t1725
            xs1076.append(item1078)
            cond1077 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1079 = xs1076
        self.consume_literal(")")
        _t1726 = transactions_pb2.Context(relations=relation_ids1079)
        result1081 = _t1726
        self.record_span(span_start1080, "Context")
        return result1081

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1086 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1082 = []
        cond1083 = self.match_lookahead_literal("[", 0)
        while cond1083:
            _t1727 = self.parse_snapshot_mapping()
            item1084 = _t1727
            xs1082.append(item1084)
            cond1083 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1085 = xs1082
        self.consume_literal(")")
        _t1728 = transactions_pb2.Snapshot(mappings=snapshot_mappings1085)
        result1087 = _t1728
        self.record_span(span_start1086, "Snapshot")
        return result1087

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1090 = self.span_start()
        _t1729 = self.parse_edb_path()
        edb_path1088 = _t1729
        _t1730 = self.parse_relation_id()
        relation_id1089 = _t1730
        _t1731 = transactions_pb2.SnapshotMapping(destination_path=edb_path1088, source_relation=relation_id1089)
        result1091 = _t1731
        self.record_span(span_start1090, "SnapshotMapping")
        return result1091

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1092 = []
        cond1093 = self.match_lookahead_literal("(", 0)
        while cond1093:
            _t1732 = self.parse_read()
            item1094 = _t1732
            xs1092.append(item1094)
            cond1093 = self.match_lookahead_literal("(", 0)
        reads1095 = xs1092
        self.consume_literal(")")
        return reads1095

    def parse_read(self) -> transactions_pb2.Read:
        span_start1102 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1734 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1735 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1736 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1737 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1738 = 3
                            else:
                                _t1738 = -1
                            _t1737 = _t1738
                        _t1736 = _t1737
                    _t1735 = _t1736
                _t1734 = _t1735
            _t1733 = _t1734
        else:
            _t1733 = -1
        prediction1096 = _t1733
        if prediction1096 == 4:
            _t1740 = self.parse_export()
            export1101 = _t1740
            _t1741 = transactions_pb2.Read(export=export1101)
            _t1739 = _t1741
        else:
            if prediction1096 == 3:
                _t1743 = self.parse_abort()
                abort1100 = _t1743
                _t1744 = transactions_pb2.Read(abort=abort1100)
                _t1742 = _t1744
            else:
                if prediction1096 == 2:
                    _t1746 = self.parse_what_if()
                    what_if1099 = _t1746
                    _t1747 = transactions_pb2.Read(what_if=what_if1099)
                    _t1745 = _t1747
                else:
                    if prediction1096 == 1:
                        _t1749 = self.parse_output()
                        output1098 = _t1749
                        _t1750 = transactions_pb2.Read(output=output1098)
                        _t1748 = _t1750
                    else:
                        if prediction1096 == 0:
                            _t1752 = self.parse_demand()
                            demand1097 = _t1752
                            _t1753 = transactions_pb2.Read(demand=demand1097)
                            _t1751 = _t1753
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1748 = _t1751
                    _t1745 = _t1748
                _t1742 = _t1745
            _t1739 = _t1742
        result1103 = _t1739
        self.record_span(span_start1102, "Read")
        return result1103

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1105 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1754 = self.parse_relation_id()
        relation_id1104 = _t1754
        self.consume_literal(")")
        _t1755 = transactions_pb2.Demand(relation_id=relation_id1104)
        result1106 = _t1755
        self.record_span(span_start1105, "Demand")
        return result1106

    def parse_output(self) -> transactions_pb2.Output:
        span_start1109 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t1756 = self.parse_name()
        name1107 = _t1756
        _t1757 = self.parse_relation_id()
        relation_id1108 = _t1757
        self.consume_literal(")")
        _t1758 = transactions_pb2.Output(name=name1107, relation_id=relation_id1108)
        result1110 = _t1758
        self.record_span(span_start1109, "Output")
        return result1110

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1113 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1759 = self.parse_name()
        name1111 = _t1759
        _t1760 = self.parse_epoch()
        epoch1112 = _t1760
        self.consume_literal(")")
        _t1761 = transactions_pb2.WhatIf(branch=name1111, epoch=epoch1112)
        result1114 = _t1761
        self.record_span(span_start1113, "WhatIf")
        return result1114

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1117 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1763 = self.parse_name()
            _t1762 = _t1763
        else:
            _t1762 = None
        name1115 = _t1762
        _t1764 = self.parse_relation_id()
        relation_id1116 = _t1764
        self.consume_literal(")")
        _t1765 = transactions_pb2.Abort(name=(name1115 if name1115 is not None else "abort"), relation_id=relation_id1116)
        result1118 = _t1765
        self.record_span(span_start1117, "Abort")
        return result1118

    def parse_export(self) -> transactions_pb2.Export:
        span_start1120 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export")
        _t1766 = self.parse_export_csv_config()
        export_csv_config1119 = _t1766
        self.consume_literal(")")
        _t1767 = transactions_pb2.Export(csv_config=export_csv_config1119)
        result1121 = _t1767
        self.record_span(span_start1120, "Export")
        return result1121

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1129 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t1769 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t1770 = 1
                else:
                    _t1770 = -1
                _t1769 = _t1770
            _t1768 = _t1769
        else:
            _t1768 = -1
        prediction1122 = _t1768
        if prediction1122 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t1772 = self.parse_export_csv_path()
            export_csv_path1126 = _t1772
            _t1773 = self.parse_export_csv_columns_list()
            export_csv_columns_list1127 = _t1773
            _t1774 = self.parse_config_dict()
            config_dict1128 = _t1774
            self.consume_literal(")")
            _t1775 = self.construct_export_csv_config(export_csv_path1126, export_csv_columns_list1127, config_dict1128)
            _t1771 = _t1775
        else:
            if prediction1122 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t1777 = self.parse_export_csv_path()
                export_csv_path1123 = _t1777
                _t1778 = self.parse_export_csv_source()
                export_csv_source1124 = _t1778
                _t1779 = self.parse_csv_config()
                csv_config1125 = _t1779
                self.consume_literal(")")
                _t1780 = self.construct_export_csv_config_with_source(export_csv_path1123, export_csv_source1124, csv_config1125)
                _t1776 = _t1780
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1771 = _t1776
        result1130 = _t1771
        self.record_span(span_start1129, "ExportCSVConfig")
        return result1130

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1131 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1131

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1138 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t1782 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t1783 = 0
                else:
                    _t1783 = -1
                _t1782 = _t1783
            _t1781 = _t1782
        else:
            _t1781 = -1
        prediction1132 = _t1781
        if prediction1132 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t1785 = self.parse_relation_id()
            relation_id1137 = _t1785
            self.consume_literal(")")
            _t1786 = transactions_pb2.ExportCSVSource(table_def=relation_id1137)
            _t1784 = _t1786
        else:
            if prediction1132 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1133 = []
                cond1134 = self.match_lookahead_literal("(", 0)
                while cond1134:
                    _t1788 = self.parse_export_csv_column()
                    item1135 = _t1788
                    xs1133.append(item1135)
                    cond1134 = self.match_lookahead_literal("(", 0)
                export_csv_columns1136 = xs1133
                self.consume_literal(")")
                _t1789 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1136)
                _t1790 = transactions_pb2.ExportCSVSource(gnf_columns=_t1789)
                _t1787 = _t1790
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1784 = _t1787
        result1139 = _t1784
        self.record_span(span_start1138, "ExportCSVSource")
        return result1139

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1142 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1140 = self.consume_terminal("STRING")
        _t1791 = self.parse_relation_id()
        relation_id1141 = _t1791
        self.consume_literal(")")
        _t1792 = transactions_pb2.ExportCSVColumn(column_name=string1140, column_data=relation_id1141)
        result1143 = _t1792
        self.record_span(span_start1142, "ExportCSVColumn")
        return result1143

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1144 = []
        cond1145 = self.match_lookahead_literal("(", 0)
        while cond1145:
            _t1793 = self.parse_export_csv_column()
            item1146 = _t1793
            xs1144.append(item1146)
            cond1145 = self.match_lookahead_literal("(", 0)
        export_csv_columns1147 = xs1144
        self.consume_literal(")")
        return export_csv_columns1147


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
