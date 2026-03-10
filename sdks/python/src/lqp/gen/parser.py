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
    ("UINT32", re.compile(r"\d+u32"), lambda x: Lexer.scan_uint32(x)),
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
    def scan_uint32(n: str) -> int:
        """Parse UINT32 token."""
        n = n[:-3]  # Remove "u32" suffix
        val = int(n)
        if val < 0 or val >= (1 << 32):
            raise ParseError(f"UInt32 literal out of range: {n}")
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
            _t1812 = value.HasField("int32_value")
        else:
            _t1812 = False
        if _t1812:
            assert value is not None
            return value.int32_value
        else:
            _t1813 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t1814 = value.HasField("int_value")
        else:
            _t1814 = False
        if _t1814:
            assert value is not None
            return value.int_value
        else:
            _t1815 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t1816 = value.HasField("string_value")
        else:
            _t1816 = False
        if _t1816:
            assert value is not None
            return value.string_value
        else:
            _t1817 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1818 = value.HasField("boolean_value")
        else:
            _t1818 = False
        if _t1818:
            assert value is not None
            return value.boolean_value
        else:
            _t1819 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1820 = value.HasField("string_value")
        else:
            _t1820 = False
        if _t1820:
            assert value is not None
            return [value.string_value]
        else:
            _t1821 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t1822 = value.HasField("int_value")
        else:
            _t1822 = False
        if _t1822:
            assert value is not None
            return value.int_value
        else:
            _t1823 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t1824 = value.HasField("float_value")
        else:
            _t1824 = False
        if _t1824:
            assert value is not None
            return value.float_value
        else:
            _t1825 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t1826 = value.HasField("string_value")
        else:
            _t1826 = False
        if _t1826:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1827 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t1828 = value.HasField("uint128_value")
        else:
            _t1828 = False
        if _t1828:
            assert value is not None
            return value.uint128_value
        else:
            _t1829 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1830 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1830
        _t1831 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1831
        _t1832 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1832
        _t1833 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1833
        _t1834 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1834
        _t1835 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1835
        _t1836 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1836
        _t1837 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1837
        _t1838 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1838
        _t1839 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1839
        _t1840 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1840
        _t1841 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t1841
        _t1842 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t1842

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1843 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1843
        _t1844 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1844
        _t1845 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1845
        _t1846 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1846
        _t1847 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1847
        _t1848 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1848
        _t1849 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1849
        _t1850 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1850
        _t1851 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1851
        _t1852 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1852
        _t1853 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1853

    def default_configure(self) -> transactions_pb2.Configure:
        _t1854 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1854
        _t1855 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1855

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
        _t1856 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1856
        _t1857 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1857
        _t1858 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1858

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1859 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1859
        _t1860 = self._extract_value_string(config.get("compression"), "")
        compression = _t1860
        _t1861 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1861
        _t1862 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1862
        _t1863 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1863
        _t1864 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1864
        _t1865 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1865
        _t1866 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1866

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t1867 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t1867

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start584 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1157 = self.parse_configure()
            _t1156 = _t1157
        else:
            _t1156 = None
        configure578 = _t1156
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1159 = self.parse_sync()
            _t1158 = _t1159
        else:
            _t1158 = None
        sync579 = _t1158
        xs580 = []
        cond581 = self.match_lookahead_literal("(", 0)
        while cond581:
            _t1160 = self.parse_epoch()
            item582 = _t1160
            xs580.append(item582)
            cond581 = self.match_lookahead_literal("(", 0)
        epochs583 = xs580
        self.consume_literal(")")
        _t1161 = self.default_configure()
        _t1162 = transactions_pb2.Transaction(epochs=epochs583, configure=(configure578 if configure578 is not None else _t1161), sync=sync579)
        result585 = _t1162
        self.record_span(span_start584, "Transaction")
        return result585

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start587 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1163 = self.parse_config_dict()
        config_dict586 = _t1163
        self.consume_literal(")")
        _t1164 = self.construct_configure(config_dict586)
        result588 = _t1164
        self.record_span(span_start587, "Configure")
        return result588

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs589 = []
        cond590 = self.match_lookahead_literal(":", 0)
        while cond590:
            _t1165 = self.parse_config_key_value()
            item591 = _t1165
            xs589.append(item591)
            cond590 = self.match_lookahead_literal(":", 0)
        config_key_values592 = xs589
        self.consume_literal("}")
        return config_key_values592

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol593 = self.consume_terminal("SYMBOL")
        _t1166 = self.parse_value()
        value594 = _t1166
        return (symbol593, value594,)

    def parse_value(self) -> logic_pb2.Value:
        span_start608 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1167 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1168 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1169 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1171 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1172 = 0
                            else:
                                _t1172 = -1
                            _t1171 = _t1172
                        _t1170 = _t1171
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1173 = 12
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1174 = 5
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1175 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1176 = 10
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1177 = 6
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1178 = 3
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1179 = 11
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1180 = 4
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1181 = 7
                                                        else:
                                                            _t1181 = -1
                                                        _t1180 = _t1181
                                                    _t1179 = _t1180
                                                _t1178 = _t1179
                                            _t1177 = _t1178
                                        _t1176 = _t1177
                                    _t1175 = _t1176
                                _t1174 = _t1175
                            _t1173 = _t1174
                        _t1170 = _t1173
                    _t1169 = _t1170
                _t1168 = _t1169
            _t1167 = _t1168
        prediction595 = _t1167
        if prediction595 == 12:
            uint32607 = self.consume_terminal("UINT32")
            _t1183 = logic_pb2.Value(uint32_value=uint32607)
            _t1182 = _t1183
        else:
            if prediction595 == 11:
                float32606 = self.consume_terminal("FLOAT32")
                _t1185 = logic_pb2.Value(float32_value=float32606)
                _t1184 = _t1185
            else:
                if prediction595 == 10:
                    int32605 = self.consume_terminal("INT32")
                    _t1187 = logic_pb2.Value(int32_value=int32605)
                    _t1186 = _t1187
                else:
                    if prediction595 == 9:
                        _t1189 = self.parse_boolean_value()
                        boolean_value604 = _t1189
                        _t1190 = logic_pb2.Value(boolean_value=boolean_value604)
                        _t1188 = _t1190
                    else:
                        if prediction595 == 8:
                            self.consume_literal("missing")
                            _t1192 = logic_pb2.MissingValue()
                            _t1193 = logic_pb2.Value(missing_value=_t1192)
                            _t1191 = _t1193
                        else:
                            if prediction595 == 7:
                                decimal603 = self.consume_terminal("DECIMAL")
                                _t1195 = logic_pb2.Value(decimal_value=decimal603)
                                _t1194 = _t1195
                            else:
                                if prediction595 == 6:
                                    int128602 = self.consume_terminal("INT128")
                                    _t1197 = logic_pb2.Value(int128_value=int128602)
                                    _t1196 = _t1197
                                else:
                                    if prediction595 == 5:
                                        uint128601 = self.consume_terminal("UINT128")
                                        _t1199 = logic_pb2.Value(uint128_value=uint128601)
                                        _t1198 = _t1199
                                    else:
                                        if prediction595 == 4:
                                            float600 = self.consume_terminal("FLOAT")
                                            _t1201 = logic_pb2.Value(float_value=float600)
                                            _t1200 = _t1201
                                        else:
                                            if prediction595 == 3:
                                                int599 = self.consume_terminal("INT")
                                                _t1203 = logic_pb2.Value(int_value=int599)
                                                _t1202 = _t1203
                                            else:
                                                if prediction595 == 2:
                                                    string598 = self.consume_terminal("STRING")
                                                    _t1205 = logic_pb2.Value(string_value=string598)
                                                    _t1204 = _t1205
                                                else:
                                                    if prediction595 == 1:
                                                        _t1207 = self.parse_datetime()
                                                        datetime597 = _t1207
                                                        _t1208 = logic_pb2.Value(datetime_value=datetime597)
                                                        _t1206 = _t1208
                                                    else:
                                                        if prediction595 == 0:
                                                            _t1210 = self.parse_date()
                                                            date596 = _t1210
                                                            _t1211 = logic_pb2.Value(date_value=date596)
                                                            _t1209 = _t1211
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1206 = _t1209
                                                    _t1204 = _t1206
                                                _t1202 = _t1204
                                            _t1200 = _t1202
                                        _t1198 = _t1200
                                    _t1196 = _t1198
                                _t1194 = _t1196
                            _t1191 = _t1194
                        _t1188 = _t1191
                    _t1186 = _t1188
                _t1184 = _t1186
            _t1182 = _t1184
        result609 = _t1182
        self.record_span(span_start608, "Value")
        return result609

    def parse_date(self) -> logic_pb2.DateValue:
        span_start613 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int610 = self.consume_terminal("INT")
        int_3611 = self.consume_terminal("INT")
        int_4612 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1212 = logic_pb2.DateValue(year=int(int610), month=int(int_3611), day=int(int_4612))
        result614 = _t1212
        self.record_span(span_start613, "DateValue")
        return result614

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start622 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int615 = self.consume_terminal("INT")
        int_3616 = self.consume_terminal("INT")
        int_4617 = self.consume_terminal("INT")
        int_5618 = self.consume_terminal("INT")
        int_6619 = self.consume_terminal("INT")
        int_7620 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1213 = self.consume_terminal("INT")
        else:
            _t1213 = None
        int_8621 = _t1213
        self.consume_literal(")")
        _t1214 = logic_pb2.DateTimeValue(year=int(int615), month=int(int_3616), day=int(int_4617), hour=int(int_5618), minute=int(int_6619), second=int(int_7620), microsecond=int((int_8621 if int_8621 is not None else 0)))
        result623 = _t1214
        self.record_span(span_start622, "DateTimeValue")
        return result623

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1215 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1216 = 1
            else:
                _t1216 = -1
            _t1215 = _t1216
        prediction624 = _t1215
        if prediction624 == 1:
            self.consume_literal("false")
            _t1217 = False
        else:
            if prediction624 == 0:
                self.consume_literal("true")
                _t1218 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1217 = _t1218
        return _t1217

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start629 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs625 = []
        cond626 = self.match_lookahead_literal(":", 0)
        while cond626:
            _t1219 = self.parse_fragment_id()
            item627 = _t1219
            xs625.append(item627)
            cond626 = self.match_lookahead_literal(":", 0)
        fragment_ids628 = xs625
        self.consume_literal(")")
        _t1220 = transactions_pb2.Sync(fragments=fragment_ids628)
        result630 = _t1220
        self.record_span(span_start629, "Sync")
        return result630

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start632 = self.span_start()
        self.consume_literal(":")
        symbol631 = self.consume_terminal("SYMBOL")
        result633 = fragments_pb2.FragmentId(id=symbol631.encode())
        self.record_span(span_start632, "FragmentId")
        return result633

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start636 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1222 = self.parse_epoch_writes()
            _t1221 = _t1222
        else:
            _t1221 = None
        epoch_writes634 = _t1221
        if self.match_lookahead_literal("(", 0):
            _t1224 = self.parse_epoch_reads()
            _t1223 = _t1224
        else:
            _t1223 = None
        epoch_reads635 = _t1223
        self.consume_literal(")")
        _t1225 = transactions_pb2.Epoch(writes=(epoch_writes634 if epoch_writes634 is not None else []), reads=(epoch_reads635 if epoch_reads635 is not None else []))
        result637 = _t1225
        self.record_span(span_start636, "Epoch")
        return result637

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs638 = []
        cond639 = self.match_lookahead_literal("(", 0)
        while cond639:
            _t1226 = self.parse_write()
            item640 = _t1226
            xs638.append(item640)
            cond639 = self.match_lookahead_literal("(", 0)
        writes641 = xs638
        self.consume_literal(")")
        return writes641

    def parse_write(self) -> transactions_pb2.Write:
        span_start647 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1228 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1229 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1230 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1231 = 2
                        else:
                            _t1231 = -1
                        _t1230 = _t1231
                    _t1229 = _t1230
                _t1228 = _t1229
            _t1227 = _t1228
        else:
            _t1227 = -1
        prediction642 = _t1227
        if prediction642 == 3:
            _t1233 = self.parse_snapshot()
            snapshot646 = _t1233
            _t1234 = transactions_pb2.Write(snapshot=snapshot646)
            _t1232 = _t1234
        else:
            if prediction642 == 2:
                _t1236 = self.parse_context()
                context645 = _t1236
                _t1237 = transactions_pb2.Write(context=context645)
                _t1235 = _t1237
            else:
                if prediction642 == 1:
                    _t1239 = self.parse_undefine()
                    undefine644 = _t1239
                    _t1240 = transactions_pb2.Write(undefine=undefine644)
                    _t1238 = _t1240
                else:
                    if prediction642 == 0:
                        _t1242 = self.parse_define()
                        define643 = _t1242
                        _t1243 = transactions_pb2.Write(define=define643)
                        _t1241 = _t1243
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1238 = _t1241
                _t1235 = _t1238
            _t1232 = _t1235
        result648 = _t1232
        self.record_span(span_start647, "Write")
        return result648

    def parse_define(self) -> transactions_pb2.Define:
        span_start650 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1244 = self.parse_fragment()
        fragment649 = _t1244
        self.consume_literal(")")
        _t1245 = transactions_pb2.Define(fragment=fragment649)
        result651 = _t1245
        self.record_span(span_start650, "Define")
        return result651

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start657 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1246 = self.parse_new_fragment_id()
        new_fragment_id652 = _t1246
        xs653 = []
        cond654 = self.match_lookahead_literal("(", 0)
        while cond654:
            _t1247 = self.parse_declaration()
            item655 = _t1247
            xs653.append(item655)
            cond654 = self.match_lookahead_literal("(", 0)
        declarations656 = xs653
        self.consume_literal(")")
        result658 = self.construct_fragment(new_fragment_id652, declarations656)
        self.record_span(span_start657, "Fragment")
        return result658

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start660 = self.span_start()
        _t1248 = self.parse_fragment_id()
        fragment_id659 = _t1248
        self.start_fragment(fragment_id659)
        result661 = fragment_id659
        self.record_span(span_start660, "FragmentId")
        return result661

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start667 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("functional_dependency", 1):
                _t1250 = 2
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1251 = 3
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t1252 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t1253 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t1254 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t1255 = 1
                                else:
                                    _t1255 = -1
                                _t1254 = _t1255
                            _t1253 = _t1254
                        _t1252 = _t1253
                    _t1251 = _t1252
                _t1250 = _t1251
            _t1249 = _t1250
        else:
            _t1249 = -1
        prediction662 = _t1249
        if prediction662 == 3:
            _t1257 = self.parse_data()
            data666 = _t1257
            _t1258 = logic_pb2.Declaration(data=data666)
            _t1256 = _t1258
        else:
            if prediction662 == 2:
                _t1260 = self.parse_constraint()
                constraint665 = _t1260
                _t1261 = logic_pb2.Declaration(constraint=constraint665)
                _t1259 = _t1261
            else:
                if prediction662 == 1:
                    _t1263 = self.parse_algorithm()
                    algorithm664 = _t1263
                    _t1264 = logic_pb2.Declaration(algorithm=algorithm664)
                    _t1262 = _t1264
                else:
                    if prediction662 == 0:
                        _t1266 = self.parse_def()
                        def663 = _t1266
                        _t1267 = logic_pb2.Declaration()
                        getattr(_t1267, 'def').CopyFrom(def663)
                        _t1265 = _t1267
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1262 = _t1265
                _t1259 = _t1262
            _t1256 = _t1259
        result668 = _t1256
        self.record_span(span_start667, "Declaration")
        return result668

    def parse_def(self) -> logic_pb2.Def:
        span_start672 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1268 = self.parse_relation_id()
        relation_id669 = _t1268
        _t1269 = self.parse_abstraction()
        abstraction670 = _t1269
        if self.match_lookahead_literal("(", 0):
            _t1271 = self.parse_attrs()
            _t1270 = _t1271
        else:
            _t1270 = None
        attrs671 = _t1270
        self.consume_literal(")")
        _t1272 = logic_pb2.Def(name=relation_id669, body=abstraction670, attrs=(attrs671 if attrs671 is not None else []))
        result673 = _t1272
        self.record_span(span_start672, "Def")
        return result673

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start677 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1273 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1274 = 1
            else:
                _t1274 = -1
            _t1273 = _t1274
        prediction674 = _t1273
        if prediction674 == 1:
            uint128676 = self.consume_terminal("UINT128")
            _t1275 = logic_pb2.RelationId(id_low=uint128676.low, id_high=uint128676.high)
        else:
            if prediction674 == 0:
                self.consume_literal(":")
                symbol675 = self.consume_terminal("SYMBOL")
                _t1276 = self.relation_id_from_string(symbol675)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1275 = _t1276
        result678 = _t1275
        self.record_span(span_start677, "RelationId")
        return result678

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start681 = self.span_start()
        self.consume_literal("(")
        _t1277 = self.parse_bindings()
        bindings679 = _t1277
        _t1278 = self.parse_formula()
        formula680 = _t1278
        self.consume_literal(")")
        _t1279 = logic_pb2.Abstraction(vars=(list(bindings679[0]) + list(bindings679[1] if bindings679[1] is not None else [])), value=formula680)
        result682 = _t1279
        self.record_span(span_start681, "Abstraction")
        return result682

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs683 = []
        cond684 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond684:
            _t1280 = self.parse_binding()
            item685 = _t1280
            xs683.append(item685)
            cond684 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings686 = xs683
        if self.match_lookahead_literal("|", 0):
            _t1282 = self.parse_value_bindings()
            _t1281 = _t1282
        else:
            _t1281 = None
        value_bindings687 = _t1281
        self.consume_literal("]")
        return (bindings686, (value_bindings687 if value_bindings687 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start690 = self.span_start()
        symbol688 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1283 = self.parse_type()
        type689 = _t1283
        _t1284 = logic_pb2.Var(name=symbol688)
        _t1285 = logic_pb2.Binding(var=_t1284, type=type689)
        result691 = _t1285
        self.record_span(span_start690, "Binding")
        return result691

    def parse_type(self) -> logic_pb2.Type:
        span_start707 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1286 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1287 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1288 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1289 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1290 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1291 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1292 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1293 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1294 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1295 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1296 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1297 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1298 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1299 = 9
                                                            else:
                                                                _t1299 = -1
                                                            _t1298 = _t1299
                                                        _t1297 = _t1298
                                                    _t1296 = _t1297
                                                _t1295 = _t1296
                                            _t1294 = _t1295
                                        _t1293 = _t1294
                                    _t1292 = _t1293
                                _t1291 = _t1292
                            _t1290 = _t1291
                        _t1289 = _t1290
                    _t1288 = _t1289
                _t1287 = _t1288
            _t1286 = _t1287
        prediction692 = _t1286
        if prediction692 == 13:
            _t1301 = self.parse_uint32_type()
            uint32_type706 = _t1301
            _t1302 = logic_pb2.Type(uint32_type=uint32_type706)
            _t1300 = _t1302
        else:
            if prediction692 == 12:
                _t1304 = self.parse_float32_type()
                float32_type705 = _t1304
                _t1305 = logic_pb2.Type(float32_type=float32_type705)
                _t1303 = _t1305
            else:
                if prediction692 == 11:
                    _t1307 = self.parse_int32_type()
                    int32_type704 = _t1307
                    _t1308 = logic_pb2.Type(int32_type=int32_type704)
                    _t1306 = _t1308
                else:
                    if prediction692 == 10:
                        _t1310 = self.parse_boolean_type()
                        boolean_type703 = _t1310
                        _t1311 = logic_pb2.Type(boolean_type=boolean_type703)
                        _t1309 = _t1311
                    else:
                        if prediction692 == 9:
                            _t1313 = self.parse_decimal_type()
                            decimal_type702 = _t1313
                            _t1314 = logic_pb2.Type(decimal_type=decimal_type702)
                            _t1312 = _t1314
                        else:
                            if prediction692 == 8:
                                _t1316 = self.parse_missing_type()
                                missing_type701 = _t1316
                                _t1317 = logic_pb2.Type(missing_type=missing_type701)
                                _t1315 = _t1317
                            else:
                                if prediction692 == 7:
                                    _t1319 = self.parse_datetime_type()
                                    datetime_type700 = _t1319
                                    _t1320 = logic_pb2.Type(datetime_type=datetime_type700)
                                    _t1318 = _t1320
                                else:
                                    if prediction692 == 6:
                                        _t1322 = self.parse_date_type()
                                        date_type699 = _t1322
                                        _t1323 = logic_pb2.Type(date_type=date_type699)
                                        _t1321 = _t1323
                                    else:
                                        if prediction692 == 5:
                                            _t1325 = self.parse_int128_type()
                                            int128_type698 = _t1325
                                            _t1326 = logic_pb2.Type(int128_type=int128_type698)
                                            _t1324 = _t1326
                                        else:
                                            if prediction692 == 4:
                                                _t1328 = self.parse_uint128_type()
                                                uint128_type697 = _t1328
                                                _t1329 = logic_pb2.Type(uint128_type=uint128_type697)
                                                _t1327 = _t1329
                                            else:
                                                if prediction692 == 3:
                                                    _t1331 = self.parse_float_type()
                                                    float_type696 = _t1331
                                                    _t1332 = logic_pb2.Type(float_type=float_type696)
                                                    _t1330 = _t1332
                                                else:
                                                    if prediction692 == 2:
                                                        _t1334 = self.parse_int_type()
                                                        int_type695 = _t1334
                                                        _t1335 = logic_pb2.Type(int_type=int_type695)
                                                        _t1333 = _t1335
                                                    else:
                                                        if prediction692 == 1:
                                                            _t1337 = self.parse_string_type()
                                                            string_type694 = _t1337
                                                            _t1338 = logic_pb2.Type(string_type=string_type694)
                                                            _t1336 = _t1338
                                                        else:
                                                            if prediction692 == 0:
                                                                _t1340 = self.parse_unspecified_type()
                                                                unspecified_type693 = _t1340
                                                                _t1341 = logic_pb2.Type(unspecified_type=unspecified_type693)
                                                                _t1339 = _t1341
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1336 = _t1339
                                                        _t1333 = _t1336
                                                    _t1330 = _t1333
                                                _t1327 = _t1330
                                            _t1324 = _t1327
                                        _t1321 = _t1324
                                    _t1318 = _t1321
                                _t1315 = _t1318
                            _t1312 = _t1315
                        _t1309 = _t1312
                    _t1306 = _t1309
                _t1303 = _t1306
            _t1300 = _t1303
        result708 = _t1300
        self.record_span(span_start707, "Type")
        return result708

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start709 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1342 = logic_pb2.UnspecifiedType()
        result710 = _t1342
        self.record_span(span_start709, "UnspecifiedType")
        return result710

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start711 = self.span_start()
        self.consume_literal("STRING")
        _t1343 = logic_pb2.StringType()
        result712 = _t1343
        self.record_span(span_start711, "StringType")
        return result712

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start713 = self.span_start()
        self.consume_literal("INT")
        _t1344 = logic_pb2.IntType()
        result714 = _t1344
        self.record_span(span_start713, "IntType")
        return result714

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start715 = self.span_start()
        self.consume_literal("FLOAT")
        _t1345 = logic_pb2.FloatType()
        result716 = _t1345
        self.record_span(span_start715, "FloatType")
        return result716

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start717 = self.span_start()
        self.consume_literal("UINT128")
        _t1346 = logic_pb2.UInt128Type()
        result718 = _t1346
        self.record_span(span_start717, "UInt128Type")
        return result718

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start719 = self.span_start()
        self.consume_literal("INT128")
        _t1347 = logic_pb2.Int128Type()
        result720 = _t1347
        self.record_span(span_start719, "Int128Type")
        return result720

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start721 = self.span_start()
        self.consume_literal("DATE")
        _t1348 = logic_pb2.DateType()
        result722 = _t1348
        self.record_span(span_start721, "DateType")
        return result722

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start723 = self.span_start()
        self.consume_literal("DATETIME")
        _t1349 = logic_pb2.DateTimeType()
        result724 = _t1349
        self.record_span(span_start723, "DateTimeType")
        return result724

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start725 = self.span_start()
        self.consume_literal("MISSING")
        _t1350 = logic_pb2.MissingType()
        result726 = _t1350
        self.record_span(span_start725, "MissingType")
        return result726

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start729 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int727 = self.consume_terminal("INT")
        int_3728 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1351 = logic_pb2.DecimalType(precision=int(int727), scale=int(int_3728))
        result730 = _t1351
        self.record_span(span_start729, "DecimalType")
        return result730

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start731 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1352 = logic_pb2.BooleanType()
        result732 = _t1352
        self.record_span(span_start731, "BooleanType")
        return result732

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start733 = self.span_start()
        self.consume_literal("INT32")
        _t1353 = logic_pb2.Int32Type()
        result734 = _t1353
        self.record_span(span_start733, "Int32Type")
        return result734

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start735 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1354 = logic_pb2.Float32Type()
        result736 = _t1354
        self.record_span(span_start735, "Float32Type")
        return result736

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start737 = self.span_start()
        self.consume_literal("UINT32")
        _t1355 = logic_pb2.UInt32Type()
        result738 = _t1355
        self.record_span(span_start737, "UInt32Type")
        return result738

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs739 = []
        cond740 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond740:
            _t1356 = self.parse_binding()
            item741 = _t1356
            xs739.append(item741)
            cond740 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings742 = xs739
        return bindings742

    def parse_formula(self) -> logic_pb2.Formula:
        span_start757 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1358 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1359 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1360 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1361 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1362 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1363 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1364 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1365 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1366 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1367 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1368 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1369 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1370 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1371 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1372 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1373 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1374 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1375 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1376 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1377 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1378 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1379 = 10
                                                                                                else:
                                                                                                    _t1379 = -1
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
                        _t1360 = _t1361
                    _t1359 = _t1360
                _t1358 = _t1359
            _t1357 = _t1358
        else:
            _t1357 = -1
        prediction743 = _t1357
        if prediction743 == 12:
            _t1381 = self.parse_cast()
            cast756 = _t1381
            _t1382 = logic_pb2.Formula(cast=cast756)
            _t1380 = _t1382
        else:
            if prediction743 == 11:
                _t1384 = self.parse_rel_atom()
                rel_atom755 = _t1384
                _t1385 = logic_pb2.Formula(rel_atom=rel_atom755)
                _t1383 = _t1385
            else:
                if prediction743 == 10:
                    _t1387 = self.parse_primitive()
                    primitive754 = _t1387
                    _t1388 = logic_pb2.Formula(primitive=primitive754)
                    _t1386 = _t1388
                else:
                    if prediction743 == 9:
                        _t1390 = self.parse_pragma()
                        pragma753 = _t1390
                        _t1391 = logic_pb2.Formula(pragma=pragma753)
                        _t1389 = _t1391
                    else:
                        if prediction743 == 8:
                            _t1393 = self.parse_atom()
                            atom752 = _t1393
                            _t1394 = logic_pb2.Formula(atom=atom752)
                            _t1392 = _t1394
                        else:
                            if prediction743 == 7:
                                _t1396 = self.parse_ffi()
                                ffi751 = _t1396
                                _t1397 = logic_pb2.Formula(ffi=ffi751)
                                _t1395 = _t1397
                            else:
                                if prediction743 == 6:
                                    _t1399 = self.parse_not()
                                    not750 = _t1399
                                    _t1400 = logic_pb2.Formula()
                                    getattr(_t1400, 'not').CopyFrom(not750)
                                    _t1398 = _t1400
                                else:
                                    if prediction743 == 5:
                                        _t1402 = self.parse_disjunction()
                                        disjunction749 = _t1402
                                        _t1403 = logic_pb2.Formula(disjunction=disjunction749)
                                        _t1401 = _t1403
                                    else:
                                        if prediction743 == 4:
                                            _t1405 = self.parse_conjunction()
                                            conjunction748 = _t1405
                                            _t1406 = logic_pb2.Formula(conjunction=conjunction748)
                                            _t1404 = _t1406
                                        else:
                                            if prediction743 == 3:
                                                _t1408 = self.parse_reduce()
                                                reduce747 = _t1408
                                                _t1409 = logic_pb2.Formula(reduce=reduce747)
                                                _t1407 = _t1409
                                            else:
                                                if prediction743 == 2:
                                                    _t1411 = self.parse_exists()
                                                    exists746 = _t1411
                                                    _t1412 = logic_pb2.Formula(exists=exists746)
                                                    _t1410 = _t1412
                                                else:
                                                    if prediction743 == 1:
                                                        _t1414 = self.parse_false()
                                                        false745 = _t1414
                                                        _t1415 = logic_pb2.Formula(disjunction=false745)
                                                        _t1413 = _t1415
                                                    else:
                                                        if prediction743 == 0:
                                                            _t1417 = self.parse_true()
                                                            true744 = _t1417
                                                            _t1418 = logic_pb2.Formula(conjunction=true744)
                                                            _t1416 = _t1418
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1413 = _t1416
                                                    _t1410 = _t1413
                                                _t1407 = _t1410
                                            _t1404 = _t1407
                                        _t1401 = _t1404
                                    _t1398 = _t1401
                                _t1395 = _t1398
                            _t1392 = _t1395
                        _t1389 = _t1392
                    _t1386 = _t1389
                _t1383 = _t1386
            _t1380 = _t1383
        result758 = _t1380
        self.record_span(span_start757, "Formula")
        return result758

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start759 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1419 = logic_pb2.Conjunction(args=[])
        result760 = _t1419
        self.record_span(span_start759, "Conjunction")
        return result760

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start761 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1420 = logic_pb2.Disjunction(args=[])
        result762 = _t1420
        self.record_span(span_start761, "Disjunction")
        return result762

    def parse_exists(self) -> logic_pb2.Exists:
        span_start765 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1421 = self.parse_bindings()
        bindings763 = _t1421
        _t1422 = self.parse_formula()
        formula764 = _t1422
        self.consume_literal(")")
        _t1423 = logic_pb2.Abstraction(vars=(list(bindings763[0]) + list(bindings763[1] if bindings763[1] is not None else [])), value=formula764)
        _t1424 = logic_pb2.Exists(body=_t1423)
        result766 = _t1424
        self.record_span(span_start765, "Exists")
        return result766

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start770 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1425 = self.parse_abstraction()
        abstraction767 = _t1425
        _t1426 = self.parse_abstraction()
        abstraction_3768 = _t1426
        _t1427 = self.parse_terms()
        terms769 = _t1427
        self.consume_literal(")")
        _t1428 = logic_pb2.Reduce(op=abstraction767, body=abstraction_3768, terms=terms769)
        result771 = _t1428
        self.record_span(span_start770, "Reduce")
        return result771

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs772 = []
        cond773 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond773:
            _t1429 = self.parse_term()
            item774 = _t1429
            xs772.append(item774)
            cond773 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        terms775 = xs772
        self.consume_literal(")")
        return terms775

    def parse_term(self) -> logic_pb2.Term:
        span_start779 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1430 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1431 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1432 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1433 = 1
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1434 = 1
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1435 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1436 = 0
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1437 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1438 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1439 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1440 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1441 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1442 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1443 = 1
                                                            else:
                                                                _t1443 = -1
                                                            _t1442 = _t1443
                                                        _t1441 = _t1442
                                                    _t1440 = _t1441
                                                _t1439 = _t1440
                                            _t1438 = _t1439
                                        _t1437 = _t1438
                                    _t1436 = _t1437
                                _t1435 = _t1436
                            _t1434 = _t1435
                        _t1433 = _t1434
                    _t1432 = _t1433
                _t1431 = _t1432
            _t1430 = _t1431
        prediction776 = _t1430
        if prediction776 == 1:
            _t1445 = self.parse_constant()
            constant778 = _t1445
            _t1446 = logic_pb2.Term(constant=constant778)
            _t1444 = _t1446
        else:
            if prediction776 == 0:
                _t1448 = self.parse_var()
                var777 = _t1448
                _t1449 = logic_pb2.Term(var=var777)
                _t1447 = _t1449
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1444 = _t1447
        result780 = _t1444
        self.record_span(span_start779, "Term")
        return result780

    def parse_var(self) -> logic_pb2.Var:
        span_start782 = self.span_start()
        symbol781 = self.consume_terminal("SYMBOL")
        _t1450 = logic_pb2.Var(name=symbol781)
        result783 = _t1450
        self.record_span(span_start782, "Var")
        return result783

    def parse_constant(self) -> logic_pb2.Value:
        span_start785 = self.span_start()
        _t1451 = self.parse_value()
        value784 = _t1451
        result786 = value784
        self.record_span(span_start785, "Value")
        return result786

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start791 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs787 = []
        cond788 = self.match_lookahead_literal("(", 0)
        while cond788:
            _t1452 = self.parse_formula()
            item789 = _t1452
            xs787.append(item789)
            cond788 = self.match_lookahead_literal("(", 0)
        formulas790 = xs787
        self.consume_literal(")")
        _t1453 = logic_pb2.Conjunction(args=formulas790)
        result792 = _t1453
        self.record_span(span_start791, "Conjunction")
        return result792

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start797 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs793 = []
        cond794 = self.match_lookahead_literal("(", 0)
        while cond794:
            _t1454 = self.parse_formula()
            item795 = _t1454
            xs793.append(item795)
            cond794 = self.match_lookahead_literal("(", 0)
        formulas796 = xs793
        self.consume_literal(")")
        _t1455 = logic_pb2.Disjunction(args=formulas796)
        result798 = _t1455
        self.record_span(span_start797, "Disjunction")
        return result798

    def parse_not(self) -> logic_pb2.Not:
        span_start800 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1456 = self.parse_formula()
        formula799 = _t1456
        self.consume_literal(")")
        _t1457 = logic_pb2.Not(arg=formula799)
        result801 = _t1457
        self.record_span(span_start800, "Not")
        return result801

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start805 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1458 = self.parse_name()
        name802 = _t1458
        _t1459 = self.parse_ffi_args()
        ffi_args803 = _t1459
        _t1460 = self.parse_terms()
        terms804 = _t1460
        self.consume_literal(")")
        _t1461 = logic_pb2.FFI(name=name802, args=ffi_args803, terms=terms804)
        result806 = _t1461
        self.record_span(span_start805, "FFI")
        return result806

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol807 = self.consume_terminal("SYMBOL")
        return symbol807

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs808 = []
        cond809 = self.match_lookahead_literal("(", 0)
        while cond809:
            _t1462 = self.parse_abstraction()
            item810 = _t1462
            xs808.append(item810)
            cond809 = self.match_lookahead_literal("(", 0)
        abstractions811 = xs808
        self.consume_literal(")")
        return abstractions811

    def parse_atom(self) -> logic_pb2.Atom:
        span_start817 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1463 = self.parse_relation_id()
        relation_id812 = _t1463
        xs813 = []
        cond814 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond814:
            _t1464 = self.parse_term()
            item815 = _t1464
            xs813.append(item815)
            cond814 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        terms816 = xs813
        self.consume_literal(")")
        _t1465 = logic_pb2.Atom(name=relation_id812, terms=terms816)
        result818 = _t1465
        self.record_span(span_start817, "Atom")
        return result818

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start824 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1466 = self.parse_name()
        name819 = _t1466
        xs820 = []
        cond821 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond821:
            _t1467 = self.parse_term()
            item822 = _t1467
            xs820.append(item822)
            cond821 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        terms823 = xs820
        self.consume_literal(")")
        _t1468 = logic_pb2.Pragma(name=name819, terms=terms823)
        result825 = _t1468
        self.record_span(span_start824, "Pragma")
        return result825

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start841 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1470 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1471 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1472 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1473 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1474 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1475 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1476 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1477 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1478 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1479 = 7
                                                else:
                                                    _t1479 = -1
                                                _t1478 = _t1479
                                            _t1477 = _t1478
                                        _t1476 = _t1477
                                    _t1475 = _t1476
                                _t1474 = _t1475
                            _t1473 = _t1474
                        _t1472 = _t1473
                    _t1471 = _t1472
                _t1470 = _t1471
            _t1469 = _t1470
        else:
            _t1469 = -1
        prediction826 = _t1469
        if prediction826 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1481 = self.parse_name()
            name836 = _t1481
            xs837 = []
            cond838 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
            while cond838:
                _t1482 = self.parse_rel_term()
                item839 = _t1482
                xs837.append(item839)
                cond838 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
            rel_terms840 = xs837
            self.consume_literal(")")
            _t1483 = logic_pb2.Primitive(name=name836, terms=rel_terms840)
            _t1480 = _t1483
        else:
            if prediction826 == 8:
                _t1485 = self.parse_divide()
                divide835 = _t1485
                _t1484 = divide835
            else:
                if prediction826 == 7:
                    _t1487 = self.parse_multiply()
                    multiply834 = _t1487
                    _t1486 = multiply834
                else:
                    if prediction826 == 6:
                        _t1489 = self.parse_minus()
                        minus833 = _t1489
                        _t1488 = minus833
                    else:
                        if prediction826 == 5:
                            _t1491 = self.parse_add()
                            add832 = _t1491
                            _t1490 = add832
                        else:
                            if prediction826 == 4:
                                _t1493 = self.parse_gt_eq()
                                gt_eq831 = _t1493
                                _t1492 = gt_eq831
                            else:
                                if prediction826 == 3:
                                    _t1495 = self.parse_gt()
                                    gt830 = _t1495
                                    _t1494 = gt830
                                else:
                                    if prediction826 == 2:
                                        _t1497 = self.parse_lt_eq()
                                        lt_eq829 = _t1497
                                        _t1496 = lt_eq829
                                    else:
                                        if prediction826 == 1:
                                            _t1499 = self.parse_lt()
                                            lt828 = _t1499
                                            _t1498 = lt828
                                        else:
                                            if prediction826 == 0:
                                                _t1501 = self.parse_eq()
                                                eq827 = _t1501
                                                _t1500 = eq827
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1498 = _t1500
                                        _t1496 = _t1498
                                    _t1494 = _t1496
                                _t1492 = _t1494
                            _t1490 = _t1492
                        _t1488 = _t1490
                    _t1486 = _t1488
                _t1484 = _t1486
            _t1480 = _t1484
        result842 = _t1480
        self.record_span(span_start841, "Primitive")
        return result842

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start845 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1502 = self.parse_term()
        term843 = _t1502
        _t1503 = self.parse_term()
        term_3844 = _t1503
        self.consume_literal(")")
        _t1504 = logic_pb2.RelTerm(term=term843)
        _t1505 = logic_pb2.RelTerm(term=term_3844)
        _t1506 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1504, _t1505])
        result846 = _t1506
        self.record_span(span_start845, "Primitive")
        return result846

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start849 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1507 = self.parse_term()
        term847 = _t1507
        _t1508 = self.parse_term()
        term_3848 = _t1508
        self.consume_literal(")")
        _t1509 = logic_pb2.RelTerm(term=term847)
        _t1510 = logic_pb2.RelTerm(term=term_3848)
        _t1511 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1509, _t1510])
        result850 = _t1511
        self.record_span(span_start849, "Primitive")
        return result850

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start853 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1512 = self.parse_term()
        term851 = _t1512
        _t1513 = self.parse_term()
        term_3852 = _t1513
        self.consume_literal(")")
        _t1514 = logic_pb2.RelTerm(term=term851)
        _t1515 = logic_pb2.RelTerm(term=term_3852)
        _t1516 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1514, _t1515])
        result854 = _t1516
        self.record_span(span_start853, "Primitive")
        return result854

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start857 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1517 = self.parse_term()
        term855 = _t1517
        _t1518 = self.parse_term()
        term_3856 = _t1518
        self.consume_literal(")")
        _t1519 = logic_pb2.RelTerm(term=term855)
        _t1520 = logic_pb2.RelTerm(term=term_3856)
        _t1521 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1519, _t1520])
        result858 = _t1521
        self.record_span(span_start857, "Primitive")
        return result858

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start861 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1522 = self.parse_term()
        term859 = _t1522
        _t1523 = self.parse_term()
        term_3860 = _t1523
        self.consume_literal(")")
        _t1524 = logic_pb2.RelTerm(term=term859)
        _t1525 = logic_pb2.RelTerm(term=term_3860)
        _t1526 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1524, _t1525])
        result862 = _t1526
        self.record_span(span_start861, "Primitive")
        return result862

    def parse_add(self) -> logic_pb2.Primitive:
        span_start866 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1527 = self.parse_term()
        term863 = _t1527
        _t1528 = self.parse_term()
        term_3864 = _t1528
        _t1529 = self.parse_term()
        term_4865 = _t1529
        self.consume_literal(")")
        _t1530 = logic_pb2.RelTerm(term=term863)
        _t1531 = logic_pb2.RelTerm(term=term_3864)
        _t1532 = logic_pb2.RelTerm(term=term_4865)
        _t1533 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1530, _t1531, _t1532])
        result867 = _t1533
        self.record_span(span_start866, "Primitive")
        return result867

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start871 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1534 = self.parse_term()
        term868 = _t1534
        _t1535 = self.parse_term()
        term_3869 = _t1535
        _t1536 = self.parse_term()
        term_4870 = _t1536
        self.consume_literal(")")
        _t1537 = logic_pb2.RelTerm(term=term868)
        _t1538 = logic_pb2.RelTerm(term=term_3869)
        _t1539 = logic_pb2.RelTerm(term=term_4870)
        _t1540 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1537, _t1538, _t1539])
        result872 = _t1540
        self.record_span(span_start871, "Primitive")
        return result872

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start876 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1541 = self.parse_term()
        term873 = _t1541
        _t1542 = self.parse_term()
        term_3874 = _t1542
        _t1543 = self.parse_term()
        term_4875 = _t1543
        self.consume_literal(")")
        _t1544 = logic_pb2.RelTerm(term=term873)
        _t1545 = logic_pb2.RelTerm(term=term_3874)
        _t1546 = logic_pb2.RelTerm(term=term_4875)
        _t1547 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1544, _t1545, _t1546])
        result877 = _t1547
        self.record_span(span_start876, "Primitive")
        return result877

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start881 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1548 = self.parse_term()
        term878 = _t1548
        _t1549 = self.parse_term()
        term_3879 = _t1549
        _t1550 = self.parse_term()
        term_4880 = _t1550
        self.consume_literal(")")
        _t1551 = logic_pb2.RelTerm(term=term878)
        _t1552 = logic_pb2.RelTerm(term=term_3879)
        _t1553 = logic_pb2.RelTerm(term=term_4880)
        _t1554 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1551, _t1552, _t1553])
        result882 = _t1554
        self.record_span(span_start881, "Primitive")
        return result882

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start886 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1555 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1556 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1557 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1558 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1559 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1560 = 1
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
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1564 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1565 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1566 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1567 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1568 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1569 = 1
                                                                else:
                                                                    _t1569 = -1
                                                                _t1568 = _t1569
                                                            _t1567 = _t1568
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
            _t1555 = _t1556
        prediction883 = _t1555
        if prediction883 == 1:
            _t1571 = self.parse_term()
            term885 = _t1571
            _t1572 = logic_pb2.RelTerm(term=term885)
            _t1570 = _t1572
        else:
            if prediction883 == 0:
                _t1574 = self.parse_specialized_value()
                specialized_value884 = _t1574
                _t1575 = logic_pb2.RelTerm(specialized_value=specialized_value884)
                _t1573 = _t1575
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1570 = _t1573
        result887 = _t1570
        self.record_span(span_start886, "RelTerm")
        return result887

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start889 = self.span_start()
        self.consume_literal("#")
        _t1576 = self.parse_value()
        value888 = _t1576
        result890 = value888
        self.record_span(span_start889, "Value")
        return result890

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start896 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1577 = self.parse_name()
        name891 = _t1577
        xs892 = []
        cond893 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond893:
            _t1578 = self.parse_rel_term()
            item894 = _t1578
            xs892.append(item894)
            cond893 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        rel_terms895 = xs892
        self.consume_literal(")")
        _t1579 = logic_pb2.RelAtom(name=name891, terms=rel_terms895)
        result897 = _t1579
        self.record_span(span_start896, "RelAtom")
        return result897

    def parse_cast(self) -> logic_pb2.Cast:
        span_start900 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1580 = self.parse_term()
        term898 = _t1580
        _t1581 = self.parse_term()
        term_3899 = _t1581
        self.consume_literal(")")
        _t1582 = logic_pb2.Cast(input=term898, result=term_3899)
        result901 = _t1582
        self.record_span(span_start900, "Cast")
        return result901

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs902 = []
        cond903 = self.match_lookahead_literal("(", 0)
        while cond903:
            _t1583 = self.parse_attribute()
            item904 = _t1583
            xs902.append(item904)
            cond903 = self.match_lookahead_literal("(", 0)
        attributes905 = xs902
        self.consume_literal(")")
        return attributes905

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start911 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1584 = self.parse_name()
        name906 = _t1584
        xs907 = []
        cond908 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond908:
            _t1585 = self.parse_value()
            item909 = _t1585
            xs907.append(item909)
            cond908 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        values910 = xs907
        self.consume_literal(")")
        _t1586 = logic_pb2.Attribute(name=name906, args=values910)
        result912 = _t1586
        self.record_span(span_start911, "Attribute")
        return result912

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start918 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs913 = []
        cond914 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond914:
            _t1587 = self.parse_relation_id()
            item915 = _t1587
            xs913.append(item915)
            cond914 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids916 = xs913
        _t1588 = self.parse_script()
        script917 = _t1588
        self.consume_literal(")")
        _t1589 = logic_pb2.Algorithm(body=script917)
        getattr(_t1589, 'global').extend(relation_ids916)
        result919 = _t1589
        self.record_span(span_start918, "Algorithm")
        return result919

    def parse_script(self) -> logic_pb2.Script:
        span_start924 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs920 = []
        cond921 = self.match_lookahead_literal("(", 0)
        while cond921:
            _t1590 = self.parse_construct()
            item922 = _t1590
            xs920.append(item922)
            cond921 = self.match_lookahead_literal("(", 0)
        constructs923 = xs920
        self.consume_literal(")")
        _t1591 = logic_pb2.Script(constructs=constructs923)
        result925 = _t1591
        self.record_span(span_start924, "Script")
        return result925

    def parse_construct(self) -> logic_pb2.Construct:
        span_start929 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1593 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1594 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1595 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1596 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1597 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1598 = 1
                                else:
                                    _t1598 = -1
                                _t1597 = _t1598
                            _t1596 = _t1597
                        _t1595 = _t1596
                    _t1594 = _t1595
                _t1593 = _t1594
            _t1592 = _t1593
        else:
            _t1592 = -1
        prediction926 = _t1592
        if prediction926 == 1:
            _t1600 = self.parse_instruction()
            instruction928 = _t1600
            _t1601 = logic_pb2.Construct(instruction=instruction928)
            _t1599 = _t1601
        else:
            if prediction926 == 0:
                _t1603 = self.parse_loop()
                loop927 = _t1603
                _t1604 = logic_pb2.Construct(loop=loop927)
                _t1602 = _t1604
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1599 = _t1602
        result930 = _t1599
        self.record_span(span_start929, "Construct")
        return result930

    def parse_loop(self) -> logic_pb2.Loop:
        span_start933 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1605 = self.parse_init()
        init931 = _t1605
        _t1606 = self.parse_script()
        script932 = _t1606
        self.consume_literal(")")
        _t1607 = logic_pb2.Loop(init=init931, body=script932)
        result934 = _t1607
        self.record_span(span_start933, "Loop")
        return result934

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs935 = []
        cond936 = self.match_lookahead_literal("(", 0)
        while cond936:
            _t1608 = self.parse_instruction()
            item937 = _t1608
            xs935.append(item937)
            cond936 = self.match_lookahead_literal("(", 0)
        instructions938 = xs935
        self.consume_literal(")")
        return instructions938

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start945 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1610 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1611 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1612 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1613 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1614 = 0
                            else:
                                _t1614 = -1
                            _t1613 = _t1614
                        _t1612 = _t1613
                    _t1611 = _t1612
                _t1610 = _t1611
            _t1609 = _t1610
        else:
            _t1609 = -1
        prediction939 = _t1609
        if prediction939 == 4:
            _t1616 = self.parse_monus_def()
            monus_def944 = _t1616
            _t1617 = logic_pb2.Instruction(monus_def=monus_def944)
            _t1615 = _t1617
        else:
            if prediction939 == 3:
                _t1619 = self.parse_monoid_def()
                monoid_def943 = _t1619
                _t1620 = logic_pb2.Instruction(monoid_def=monoid_def943)
                _t1618 = _t1620
            else:
                if prediction939 == 2:
                    _t1622 = self.parse_break()
                    break942 = _t1622
                    _t1623 = logic_pb2.Instruction()
                    getattr(_t1623, 'break').CopyFrom(break942)
                    _t1621 = _t1623
                else:
                    if prediction939 == 1:
                        _t1625 = self.parse_upsert()
                        upsert941 = _t1625
                        _t1626 = logic_pb2.Instruction(upsert=upsert941)
                        _t1624 = _t1626
                    else:
                        if prediction939 == 0:
                            _t1628 = self.parse_assign()
                            assign940 = _t1628
                            _t1629 = logic_pb2.Instruction(assign=assign940)
                            _t1627 = _t1629
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1624 = _t1627
                    _t1621 = _t1624
                _t1618 = _t1621
            _t1615 = _t1618
        result946 = _t1615
        self.record_span(span_start945, "Instruction")
        return result946

    def parse_assign(self) -> logic_pb2.Assign:
        span_start950 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1630 = self.parse_relation_id()
        relation_id947 = _t1630
        _t1631 = self.parse_abstraction()
        abstraction948 = _t1631
        if self.match_lookahead_literal("(", 0):
            _t1633 = self.parse_attrs()
            _t1632 = _t1633
        else:
            _t1632 = None
        attrs949 = _t1632
        self.consume_literal(")")
        _t1634 = logic_pb2.Assign(name=relation_id947, body=abstraction948, attrs=(attrs949 if attrs949 is not None else []))
        result951 = _t1634
        self.record_span(span_start950, "Assign")
        return result951

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start955 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1635 = self.parse_relation_id()
        relation_id952 = _t1635
        _t1636 = self.parse_abstraction_with_arity()
        abstraction_with_arity953 = _t1636
        if self.match_lookahead_literal("(", 0):
            _t1638 = self.parse_attrs()
            _t1637 = _t1638
        else:
            _t1637 = None
        attrs954 = _t1637
        self.consume_literal(")")
        _t1639 = logic_pb2.Upsert(name=relation_id952, body=abstraction_with_arity953[0], attrs=(attrs954 if attrs954 is not None else []), value_arity=abstraction_with_arity953[1])
        result956 = _t1639
        self.record_span(span_start955, "Upsert")
        return result956

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1640 = self.parse_bindings()
        bindings957 = _t1640
        _t1641 = self.parse_formula()
        formula958 = _t1641
        self.consume_literal(")")
        _t1642 = logic_pb2.Abstraction(vars=(list(bindings957[0]) + list(bindings957[1] if bindings957[1] is not None else [])), value=formula958)
        return (_t1642, len(bindings957[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start962 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1643 = self.parse_relation_id()
        relation_id959 = _t1643
        _t1644 = self.parse_abstraction()
        abstraction960 = _t1644
        if self.match_lookahead_literal("(", 0):
            _t1646 = self.parse_attrs()
            _t1645 = _t1646
        else:
            _t1645 = None
        attrs961 = _t1645
        self.consume_literal(")")
        _t1647 = logic_pb2.Break(name=relation_id959, body=abstraction960, attrs=(attrs961 if attrs961 is not None else []))
        result963 = _t1647
        self.record_span(span_start962, "Break")
        return result963

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start968 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1648 = self.parse_monoid()
        monoid964 = _t1648
        _t1649 = self.parse_relation_id()
        relation_id965 = _t1649
        _t1650 = self.parse_abstraction_with_arity()
        abstraction_with_arity966 = _t1650
        if self.match_lookahead_literal("(", 0):
            _t1652 = self.parse_attrs()
            _t1651 = _t1652
        else:
            _t1651 = None
        attrs967 = _t1651
        self.consume_literal(")")
        _t1653 = logic_pb2.MonoidDef(monoid=monoid964, name=relation_id965, body=abstraction_with_arity966[0], attrs=(attrs967 if attrs967 is not None else []), value_arity=abstraction_with_arity966[1])
        result969 = _t1653
        self.record_span(span_start968, "MonoidDef")
        return result969

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start975 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1655 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1656 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1657 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1658 = 2
                        else:
                            _t1658 = -1
                        _t1657 = _t1658
                    _t1656 = _t1657
                _t1655 = _t1656
            _t1654 = _t1655
        else:
            _t1654 = -1
        prediction970 = _t1654
        if prediction970 == 3:
            _t1660 = self.parse_sum_monoid()
            sum_monoid974 = _t1660
            _t1661 = logic_pb2.Monoid(sum_monoid=sum_monoid974)
            _t1659 = _t1661
        else:
            if prediction970 == 2:
                _t1663 = self.parse_max_monoid()
                max_monoid973 = _t1663
                _t1664 = logic_pb2.Monoid(max_monoid=max_monoid973)
                _t1662 = _t1664
            else:
                if prediction970 == 1:
                    _t1666 = self.parse_min_monoid()
                    min_monoid972 = _t1666
                    _t1667 = logic_pb2.Monoid(min_monoid=min_monoid972)
                    _t1665 = _t1667
                else:
                    if prediction970 == 0:
                        _t1669 = self.parse_or_monoid()
                        or_monoid971 = _t1669
                        _t1670 = logic_pb2.Monoid(or_monoid=or_monoid971)
                        _t1668 = _t1670
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1665 = _t1668
                _t1662 = _t1665
            _t1659 = _t1662
        result976 = _t1659
        self.record_span(span_start975, "Monoid")
        return result976

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start977 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1671 = logic_pb2.OrMonoid()
        result978 = _t1671
        self.record_span(span_start977, "OrMonoid")
        return result978

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start980 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1672 = self.parse_type()
        type979 = _t1672
        self.consume_literal(")")
        _t1673 = logic_pb2.MinMonoid(type=type979)
        result981 = _t1673
        self.record_span(span_start980, "MinMonoid")
        return result981

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start983 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1674 = self.parse_type()
        type982 = _t1674
        self.consume_literal(")")
        _t1675 = logic_pb2.MaxMonoid(type=type982)
        result984 = _t1675
        self.record_span(span_start983, "MaxMonoid")
        return result984

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start986 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1676 = self.parse_type()
        type985 = _t1676
        self.consume_literal(")")
        _t1677 = logic_pb2.SumMonoid(type=type985)
        result987 = _t1677
        self.record_span(span_start986, "SumMonoid")
        return result987

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start992 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1678 = self.parse_monoid()
        monoid988 = _t1678
        _t1679 = self.parse_relation_id()
        relation_id989 = _t1679
        _t1680 = self.parse_abstraction_with_arity()
        abstraction_with_arity990 = _t1680
        if self.match_lookahead_literal("(", 0):
            _t1682 = self.parse_attrs()
            _t1681 = _t1682
        else:
            _t1681 = None
        attrs991 = _t1681
        self.consume_literal(")")
        _t1683 = logic_pb2.MonusDef(monoid=monoid988, name=relation_id989, body=abstraction_with_arity990[0], attrs=(attrs991 if attrs991 is not None else []), value_arity=abstraction_with_arity990[1])
        result993 = _t1683
        self.record_span(span_start992, "MonusDef")
        return result993

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start998 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1684 = self.parse_relation_id()
        relation_id994 = _t1684
        _t1685 = self.parse_abstraction()
        abstraction995 = _t1685
        _t1686 = self.parse_functional_dependency_keys()
        functional_dependency_keys996 = _t1686
        _t1687 = self.parse_functional_dependency_values()
        functional_dependency_values997 = _t1687
        self.consume_literal(")")
        _t1688 = logic_pb2.FunctionalDependency(guard=abstraction995, keys=functional_dependency_keys996, values=functional_dependency_values997)
        _t1689 = logic_pb2.Constraint(name=relation_id994, functional_dependency=_t1688)
        result999 = _t1689
        self.record_span(span_start998, "Constraint")
        return result999

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1000 = []
        cond1001 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1001:
            _t1690 = self.parse_var()
            item1002 = _t1690
            xs1000.append(item1002)
            cond1001 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1003 = xs1000
        self.consume_literal(")")
        return vars1003

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1004 = []
        cond1005 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1005:
            _t1691 = self.parse_var()
            item1006 = _t1691
            xs1004.append(item1006)
            cond1005 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1007 = xs1004
        self.consume_literal(")")
        return vars1007

    def parse_data(self) -> logic_pb2.Data:
        span_start1012 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("edb", 1):
                _t1693 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1694 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1695 = 1
                    else:
                        _t1695 = -1
                    _t1694 = _t1695
                _t1693 = _t1694
            _t1692 = _t1693
        else:
            _t1692 = -1
        prediction1008 = _t1692
        if prediction1008 == 2:
            _t1697 = self.parse_csv_data()
            csv_data1011 = _t1697
            _t1698 = logic_pb2.Data(csv_data=csv_data1011)
            _t1696 = _t1698
        else:
            if prediction1008 == 1:
                _t1700 = self.parse_betree_relation()
                betree_relation1010 = _t1700
                _t1701 = logic_pb2.Data(betree_relation=betree_relation1010)
                _t1699 = _t1701
            else:
                if prediction1008 == 0:
                    _t1703 = self.parse_edb()
                    edb1009 = _t1703
                    _t1704 = logic_pb2.Data(edb=edb1009)
                    _t1702 = _t1704
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1699 = _t1702
            _t1696 = _t1699
        result1013 = _t1696
        self.record_span(span_start1012, "Data")
        return result1013

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1017 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1705 = self.parse_relation_id()
        relation_id1014 = _t1705
        _t1706 = self.parse_edb_path()
        edb_path1015 = _t1706
        _t1707 = self.parse_edb_types()
        edb_types1016 = _t1707
        self.consume_literal(")")
        _t1708 = logic_pb2.EDB(target_id=relation_id1014, path=edb_path1015, types=edb_types1016)
        result1018 = _t1708
        self.record_span(span_start1017, "EDB")
        return result1018

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1019 = []
        cond1020 = self.match_lookahead_terminal("STRING", 0)
        while cond1020:
            item1021 = self.consume_terminal("STRING")
            xs1019.append(item1021)
            cond1020 = self.match_lookahead_terminal("STRING", 0)
        strings1022 = xs1019
        self.consume_literal("]")
        return strings1022

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1023 = []
        cond1024 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1024:
            _t1709 = self.parse_type()
            item1025 = _t1709
            xs1023.append(item1025)
            cond1024 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1026 = xs1023
        self.consume_literal("]")
        return types1026

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1029 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1710 = self.parse_relation_id()
        relation_id1027 = _t1710
        _t1711 = self.parse_betree_info()
        betree_info1028 = _t1711
        self.consume_literal(")")
        _t1712 = logic_pb2.BeTreeRelation(name=relation_id1027, relation_info=betree_info1028)
        result1030 = _t1712
        self.record_span(span_start1029, "BeTreeRelation")
        return result1030

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1034 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1713 = self.parse_betree_info_key_types()
        betree_info_key_types1031 = _t1713
        _t1714 = self.parse_betree_info_value_types()
        betree_info_value_types1032 = _t1714
        _t1715 = self.parse_config_dict()
        config_dict1033 = _t1715
        self.consume_literal(")")
        _t1716 = self.construct_betree_info(betree_info_key_types1031, betree_info_value_types1032, config_dict1033)
        result1035 = _t1716
        self.record_span(span_start1034, "BeTreeInfo")
        return result1035

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1036 = []
        cond1037 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1037:
            _t1717 = self.parse_type()
            item1038 = _t1717
            xs1036.append(item1038)
            cond1037 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1039 = xs1036
        self.consume_literal(")")
        return types1039

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1040 = []
        cond1041 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1041:
            _t1718 = self.parse_type()
            item1042 = _t1718
            xs1040.append(item1042)
            cond1041 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1043 = xs1040
        self.consume_literal(")")
        return types1043

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1048 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1719 = self.parse_csvlocator()
        csvlocator1044 = _t1719
        _t1720 = self.parse_csv_config()
        csv_config1045 = _t1720
        _t1721 = self.parse_gnf_columns()
        gnf_columns1046 = _t1721
        _t1722 = self.parse_csv_asof()
        csv_asof1047 = _t1722
        self.consume_literal(")")
        _t1723 = logic_pb2.CSVData(locator=csvlocator1044, config=csv_config1045, columns=gnf_columns1046, asof=csv_asof1047)
        result1049 = _t1723
        self.record_span(span_start1048, "CSVData")
        return result1049

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1052 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1725 = self.parse_csv_locator_paths()
            _t1724 = _t1725
        else:
            _t1724 = None
        csv_locator_paths1050 = _t1724
        if self.match_lookahead_literal("(", 0):
            _t1727 = self.parse_csv_locator_inline_data()
            _t1726 = _t1727
        else:
            _t1726 = None
        csv_locator_inline_data1051 = _t1726
        self.consume_literal(")")
        _t1728 = logic_pb2.CSVLocator(paths=(csv_locator_paths1050 if csv_locator_paths1050 is not None else []), inline_data=(csv_locator_inline_data1051 if csv_locator_inline_data1051 is not None else "").encode())
        result1053 = _t1728
        self.record_span(span_start1052, "CSVLocator")
        return result1053

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1054 = []
        cond1055 = self.match_lookahead_terminal("STRING", 0)
        while cond1055:
            item1056 = self.consume_terminal("STRING")
            xs1054.append(item1056)
            cond1055 = self.match_lookahead_terminal("STRING", 0)
        strings1057 = xs1054
        self.consume_literal(")")
        return strings1057

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1058 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1058

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1060 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1729 = self.parse_config_dict()
        config_dict1059 = _t1729
        self.consume_literal(")")
        _t1730 = self.construct_csv_config(config_dict1059)
        result1061 = _t1730
        self.record_span(span_start1060, "CSVConfig")
        return result1061

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1062 = []
        cond1063 = self.match_lookahead_literal("(", 0)
        while cond1063:
            _t1731 = self.parse_gnf_column()
            item1064 = _t1731
            xs1062.append(item1064)
            cond1063 = self.match_lookahead_literal("(", 0)
        gnf_columns1065 = xs1062
        self.consume_literal(")")
        return gnf_columns1065

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1072 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1732 = self.parse_gnf_column_path()
        gnf_column_path1066 = _t1732
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1734 = self.parse_relation_id()
            _t1733 = _t1734
        else:
            _t1733 = None
        relation_id1067 = _t1733
        self.consume_literal("[")
        xs1068 = []
        cond1069 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1069:
            _t1735 = self.parse_type()
            item1070 = _t1735
            xs1068.append(item1070)
            cond1069 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1071 = xs1068
        self.consume_literal("]")
        self.consume_literal(")")
        _t1736 = logic_pb2.GNFColumn(column_path=gnf_column_path1066, target_id=relation_id1067, types=types1071)
        result1073 = _t1736
        self.record_span(span_start1072, "GNFColumn")
        return result1073

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1737 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1738 = 0
            else:
                _t1738 = -1
            _t1737 = _t1738
        prediction1074 = _t1737
        if prediction1074 == 1:
            self.consume_literal("[")
            xs1076 = []
            cond1077 = self.match_lookahead_terminal("STRING", 0)
            while cond1077:
                item1078 = self.consume_terminal("STRING")
                xs1076.append(item1078)
                cond1077 = self.match_lookahead_terminal("STRING", 0)
            strings1079 = xs1076
            self.consume_literal("]")
            _t1739 = strings1079
        else:
            if prediction1074 == 0:
                string1075 = self.consume_terminal("STRING")
                _t1740 = [string1075]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1739 = _t1740
        return _t1739

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1080 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1080

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1082 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1741 = self.parse_fragment_id()
        fragment_id1081 = _t1741
        self.consume_literal(")")
        _t1742 = transactions_pb2.Undefine(fragment_id=fragment_id1081)
        result1083 = _t1742
        self.record_span(span_start1082, "Undefine")
        return result1083

    def parse_context(self) -> transactions_pb2.Context:
        span_start1088 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1084 = []
        cond1085 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1085:
            _t1743 = self.parse_relation_id()
            item1086 = _t1743
            xs1084.append(item1086)
            cond1085 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1087 = xs1084
        self.consume_literal(")")
        _t1744 = transactions_pb2.Context(relations=relation_ids1087)
        result1089 = _t1744
        self.record_span(span_start1088, "Context")
        return result1089

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1094 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1090 = []
        cond1091 = self.match_lookahead_literal("[", 0)
        while cond1091:
            _t1745 = self.parse_snapshot_mapping()
            item1092 = _t1745
            xs1090.append(item1092)
            cond1091 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1093 = xs1090
        self.consume_literal(")")
        _t1746 = transactions_pb2.Snapshot(mappings=snapshot_mappings1093)
        result1095 = _t1746
        self.record_span(span_start1094, "Snapshot")
        return result1095

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1098 = self.span_start()
        _t1747 = self.parse_edb_path()
        edb_path1096 = _t1747
        _t1748 = self.parse_relation_id()
        relation_id1097 = _t1748
        _t1749 = transactions_pb2.SnapshotMapping(destination_path=edb_path1096, source_relation=relation_id1097)
        result1099 = _t1749
        self.record_span(span_start1098, "SnapshotMapping")
        return result1099

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1100 = []
        cond1101 = self.match_lookahead_literal("(", 0)
        while cond1101:
            _t1750 = self.parse_read()
            item1102 = _t1750
            xs1100.append(item1102)
            cond1101 = self.match_lookahead_literal("(", 0)
        reads1103 = xs1100
        self.consume_literal(")")
        return reads1103

    def parse_read(self) -> transactions_pb2.Read:
        span_start1110 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1752 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1753 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1754 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1755 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1756 = 3
                            else:
                                _t1756 = -1
                            _t1755 = _t1756
                        _t1754 = _t1755
                    _t1753 = _t1754
                _t1752 = _t1753
            _t1751 = _t1752
        else:
            _t1751 = -1
        prediction1104 = _t1751
        if prediction1104 == 4:
            _t1758 = self.parse_export()
            export1109 = _t1758
            _t1759 = transactions_pb2.Read(export=export1109)
            _t1757 = _t1759
        else:
            if prediction1104 == 3:
                _t1761 = self.parse_abort()
                abort1108 = _t1761
                _t1762 = transactions_pb2.Read(abort=abort1108)
                _t1760 = _t1762
            else:
                if prediction1104 == 2:
                    _t1764 = self.parse_what_if()
                    what_if1107 = _t1764
                    _t1765 = transactions_pb2.Read(what_if=what_if1107)
                    _t1763 = _t1765
                else:
                    if prediction1104 == 1:
                        _t1767 = self.parse_output()
                        output1106 = _t1767
                        _t1768 = transactions_pb2.Read(output=output1106)
                        _t1766 = _t1768
                    else:
                        if prediction1104 == 0:
                            _t1770 = self.parse_demand()
                            demand1105 = _t1770
                            _t1771 = transactions_pb2.Read(demand=demand1105)
                            _t1769 = _t1771
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1766 = _t1769
                    _t1763 = _t1766
                _t1760 = _t1763
            _t1757 = _t1760
        result1111 = _t1757
        self.record_span(span_start1110, "Read")
        return result1111

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1113 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1772 = self.parse_relation_id()
        relation_id1112 = _t1772
        self.consume_literal(")")
        _t1773 = transactions_pb2.Demand(relation_id=relation_id1112)
        result1114 = _t1773
        self.record_span(span_start1113, "Demand")
        return result1114

    def parse_output(self) -> transactions_pb2.Output:
        span_start1117 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t1774 = self.parse_name()
        name1115 = _t1774
        _t1775 = self.parse_relation_id()
        relation_id1116 = _t1775
        self.consume_literal(")")
        _t1776 = transactions_pb2.Output(name=name1115, relation_id=relation_id1116)
        result1118 = _t1776
        self.record_span(span_start1117, "Output")
        return result1118

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1121 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1777 = self.parse_name()
        name1119 = _t1777
        _t1778 = self.parse_epoch()
        epoch1120 = _t1778
        self.consume_literal(")")
        _t1779 = transactions_pb2.WhatIf(branch=name1119, epoch=epoch1120)
        result1122 = _t1779
        self.record_span(span_start1121, "WhatIf")
        return result1122

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1125 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1781 = self.parse_name()
            _t1780 = _t1781
        else:
            _t1780 = None
        name1123 = _t1780
        _t1782 = self.parse_relation_id()
        relation_id1124 = _t1782
        self.consume_literal(")")
        _t1783 = transactions_pb2.Abort(name=(name1123 if name1123 is not None else "abort"), relation_id=relation_id1124)
        result1126 = _t1783
        self.record_span(span_start1125, "Abort")
        return result1126

    def parse_export(self) -> transactions_pb2.Export:
        span_start1128 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export")
        _t1784 = self.parse_export_csv_config()
        export_csv_config1127 = _t1784
        self.consume_literal(")")
        _t1785 = transactions_pb2.Export(csv_config=export_csv_config1127)
        result1129 = _t1785
        self.record_span(span_start1128, "Export")
        return result1129

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1137 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t1787 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t1788 = 1
                else:
                    _t1788 = -1
                _t1787 = _t1788
            _t1786 = _t1787
        else:
            _t1786 = -1
        prediction1130 = _t1786
        if prediction1130 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t1790 = self.parse_export_csv_path()
            export_csv_path1134 = _t1790
            _t1791 = self.parse_export_csv_columns_list()
            export_csv_columns_list1135 = _t1791
            _t1792 = self.parse_config_dict()
            config_dict1136 = _t1792
            self.consume_literal(")")
            _t1793 = self.construct_export_csv_config(export_csv_path1134, export_csv_columns_list1135, config_dict1136)
            _t1789 = _t1793
        else:
            if prediction1130 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t1795 = self.parse_export_csv_path()
                export_csv_path1131 = _t1795
                _t1796 = self.parse_export_csv_source()
                export_csv_source1132 = _t1796
                _t1797 = self.parse_csv_config()
                csv_config1133 = _t1797
                self.consume_literal(")")
                _t1798 = self.construct_export_csv_config_with_source(export_csv_path1131, export_csv_source1132, csv_config1133)
                _t1794 = _t1798
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1789 = _t1794
        result1138 = _t1789
        self.record_span(span_start1137, "ExportCSVConfig")
        return result1138

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1139 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1139

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1146 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t1800 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t1801 = 0
                else:
                    _t1801 = -1
                _t1800 = _t1801
            _t1799 = _t1800
        else:
            _t1799 = -1
        prediction1140 = _t1799
        if prediction1140 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t1803 = self.parse_relation_id()
            relation_id1145 = _t1803
            self.consume_literal(")")
            _t1804 = transactions_pb2.ExportCSVSource(table_def=relation_id1145)
            _t1802 = _t1804
        else:
            if prediction1140 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1141 = []
                cond1142 = self.match_lookahead_literal("(", 0)
                while cond1142:
                    _t1806 = self.parse_export_csv_column()
                    item1143 = _t1806
                    xs1141.append(item1143)
                    cond1142 = self.match_lookahead_literal("(", 0)
                export_csv_columns1144 = xs1141
                self.consume_literal(")")
                _t1807 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1144)
                _t1808 = transactions_pb2.ExportCSVSource(gnf_columns=_t1807)
                _t1805 = _t1808
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1802 = _t1805
        result1147 = _t1802
        self.record_span(span_start1146, "ExportCSVSource")
        return result1147

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1150 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1148 = self.consume_terminal("STRING")
        _t1809 = self.parse_relation_id()
        relation_id1149 = _t1809
        self.consume_literal(")")
        _t1810 = transactions_pb2.ExportCSVColumn(column_name=string1148, column_data=relation_id1149)
        result1151 = _t1810
        self.record_span(span_start1150, "ExportCSVColumn")
        return result1151

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1152 = []
        cond1153 = self.match_lookahead_literal("(", 0)
        while cond1153:
            _t1811 = self.parse_export_csv_column()
            item1154 = _t1811
            xs1152.append(item1154)
            cond1153 = self.match_lookahead_literal("(", 0)
        export_csv_columns1155 = xs1152
        self.consume_literal(")")
        return export_csv_columns1155


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
