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
            _t1888 = value.HasField("int32_value")
        else:
            _t1888 = False
        if _t1888:
            assert value is not None
            return value.int32_value
        else:
            _t1889 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t1890 = value.HasField("int_value")
        else:
            _t1890 = False
        if _t1890:
            assert value is not None
            return value.int_value
        else:
            _t1891 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t1892 = value.HasField("string_value")
        else:
            _t1892 = False
        if _t1892:
            assert value is not None
            return value.string_value
        else:
            _t1893 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1894 = value.HasField("boolean_value")
        else:
            _t1894 = False
        if _t1894:
            assert value is not None
            return value.boolean_value
        else:
            _t1895 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1896 = value.HasField("string_value")
        else:
            _t1896 = False
        if _t1896:
            assert value is not None
            return [value.string_value]
        else:
            _t1897 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t1898 = value.HasField("int_value")
        else:
            _t1898 = False
        if _t1898:
            assert value is not None
            return value.int_value
        else:
            _t1899 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t1900 = value.HasField("float_value")
        else:
            _t1900 = False
        if _t1900:
            assert value is not None
            return value.float_value
        else:
            _t1901 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t1902 = value.HasField("string_value")
        else:
            _t1902 = False
        if _t1902:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1903 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t1904 = value.HasField("uint128_value")
        else:
            _t1904 = False
        if _t1904:
            assert value is not None
            return value.uint128_value
        else:
            _t1905 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1906 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1906
        _t1907 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1907
        _t1908 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1908
        _t1909 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1909
        _t1910 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1910
        _t1911 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1911
        _t1912 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1912
        _t1913 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1913
        _t1914 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1914
        _t1915 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1915
        _t1916 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1916
        _t1917 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t1917
        _t1918 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t1918

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1919 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1919
        _t1920 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1920
        _t1921 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1921
        _t1922 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1922
        _t1923 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1923
        _t1924 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1924
        _t1925 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1925
        _t1926 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1926
        _t1927 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1927
        _t1928 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1928
        _t1929 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1929

    def default_configure(self) -> transactions_pb2.Configure:
        _t1930 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1930
        _t1931 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1931

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
        _t1932 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1932
        _t1933 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1933
        _t1934 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1934

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1935 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1935
        _t1936 = self._extract_value_string(config.get("compression"), "")
        compression = _t1936
        _t1937 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1937
        _t1938 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1938
        _t1939 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1939
        _t1940 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1940
        _t1941 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1941
        _t1942 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1942

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t1943 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t1943

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start605 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1199 = self.parse_configure()
            _t1198 = _t1199
        else:
            _t1198 = None
        configure599 = _t1198
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1201 = self.parse_sync()
            _t1200 = _t1201
        else:
            _t1200 = None
        sync600 = _t1200
        xs601 = []
        cond602 = self.match_lookahead_literal("(", 0)
        while cond602:
            _t1202 = self.parse_epoch()
            item603 = _t1202
            xs601.append(item603)
            cond602 = self.match_lookahead_literal("(", 0)
        epochs604 = xs601
        self.consume_literal(")")
        _t1203 = self.default_configure()
        _t1204 = transactions_pb2.Transaction(epochs=epochs604, configure=(configure599 if configure599 is not None else _t1203), sync=sync600)
        result606 = _t1204
        self.record_span(span_start605, "Transaction")
        return result606

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start608 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1205 = self.parse_config_dict()
        config_dict607 = _t1205
        self.consume_literal(")")
        _t1206 = self.construct_configure(config_dict607)
        result609 = _t1206
        self.record_span(span_start608, "Configure")
        return result609

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs610 = []
        cond611 = self.match_lookahead_literal(":", 0)
        while cond611:
            _t1207 = self.parse_config_key_value()
            item612 = _t1207
            xs610.append(item612)
            cond611 = self.match_lookahead_literal(":", 0)
        config_key_values613 = xs610
        self.consume_literal("}")
        return config_key_values613

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol614 = self.consume_terminal("SYMBOL")
        _t1208 = self.parse_raw_value()
        raw_value615 = _t1208
        return (symbol614, raw_value615,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start628 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1209 = 11
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1210 = 10
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1211 = 11
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1213 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1214 = 0
                            else:
                                _t1214 = -1
                            _t1213 = _t1214
                        _t1212 = _t1213
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1215 = 7
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t1216 = 2
                            else:
                                if self.match_lookahead_terminal("INT32", 0):
                                    _t1217 = 3
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t1218 = 8
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t1219 = 4
                                        else:
                                            if self.match_lookahead_terminal("FLOAT32", 0):
                                                _t1220 = 5
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1221 = 6
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1222 = 9
                                                    else:
                                                        _t1222 = -1
                                                    _t1221 = _t1222
                                                _t1220 = _t1221
                                            _t1219 = _t1220
                                        _t1218 = _t1219
                                    _t1217 = _t1218
                                _t1216 = _t1217
                            _t1215 = _t1216
                        _t1212 = _t1215
                    _t1211 = _t1212
                _t1210 = _t1211
            _t1209 = _t1210
        prediction616 = _t1209
        if prediction616 == 11:
            _t1224 = self.parse_boolean_value()
            boolean_value627 = _t1224
            _t1225 = logic_pb2.Value(boolean_value=boolean_value627)
            _t1223 = _t1225
        else:
            if prediction616 == 10:
                self.consume_literal("missing")
                _t1227 = logic_pb2.MissingValue()
                _t1228 = logic_pb2.Value(missing_value=_t1227)
                _t1226 = _t1228
            else:
                if prediction616 == 9:
                    decimal626 = self.consume_terminal("DECIMAL")
                    _t1230 = logic_pb2.Value(decimal_value=decimal626)
                    _t1229 = _t1230
                else:
                    if prediction616 == 8:
                        int128625 = self.consume_terminal("INT128")
                        _t1232 = logic_pb2.Value(int128_value=int128625)
                        _t1231 = _t1232
                    else:
                        if prediction616 == 7:
                            uint128624 = self.consume_terminal("UINT128")
                            _t1234 = logic_pb2.Value(uint128_value=uint128624)
                            _t1233 = _t1234
                        else:
                            if prediction616 == 6:
                                float623 = self.consume_terminal("FLOAT")
                                _t1236 = logic_pb2.Value(float_value=float623)
                                _t1235 = _t1236
                            else:
                                if prediction616 == 5:
                                    float32622 = self.consume_terminal("FLOAT32")
                                    _t1238 = logic_pb2.Value(float32_value=float32622)
                                    _t1237 = _t1238
                                else:
                                    if prediction616 == 4:
                                        int621 = self.consume_terminal("INT")
                                        _t1240 = logic_pb2.Value(int_value=int621)
                                        _t1239 = _t1240
                                    else:
                                        if prediction616 == 3:
                                            int32620 = self.consume_terminal("INT32")
                                            _t1242 = logic_pb2.Value(int32_value=int32620)
                                            _t1241 = _t1242
                                        else:
                                            if prediction616 == 2:
                                                string619 = self.consume_terminal("STRING")
                                                _t1244 = logic_pb2.Value(string_value=string619)
                                                _t1243 = _t1244
                                            else:
                                                if prediction616 == 1:
                                                    _t1246 = self.parse_raw_datetime()
                                                    raw_datetime618 = _t1246
                                                    _t1247 = logic_pb2.Value(datetime_value=raw_datetime618)
                                                    _t1245 = _t1247
                                                else:
                                                    if prediction616 == 0:
                                                        _t1249 = self.parse_raw_date()
                                                        raw_date617 = _t1249
                                                        _t1250 = logic_pb2.Value(date_value=raw_date617)
                                                        _t1248 = _t1250
                                                    else:
                                                        raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                    _t1245 = _t1248
                                                _t1243 = _t1245
                                            _t1241 = _t1243
                                        _t1239 = _t1241
                                    _t1237 = _t1239
                                _t1235 = _t1237
                            _t1233 = _t1235
                        _t1231 = _t1233
                    _t1229 = _t1231
                _t1226 = _t1229
            _t1223 = _t1226
        result629 = _t1223
        self.record_span(span_start628, "Value")
        return result629

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start633 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int630 = self.consume_terminal("INT")
        int_3631 = self.consume_terminal("INT")
        int_4632 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1251 = logic_pb2.DateValue(year=int(int630), month=int(int_3631), day=int(int_4632))
        result634 = _t1251
        self.record_span(span_start633, "DateValue")
        return result634

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start642 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int635 = self.consume_terminal("INT")
        int_3636 = self.consume_terminal("INT")
        int_4637 = self.consume_terminal("INT")
        int_5638 = self.consume_terminal("INT")
        int_6639 = self.consume_terminal("INT")
        int_7640 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1252 = self.consume_terminal("INT")
        else:
            _t1252 = None
        int_8641 = _t1252
        self.consume_literal(")")
        _t1253 = logic_pb2.DateTimeValue(year=int(int635), month=int(int_3636), day=int(int_4637), hour=int(int_5638), minute=int(int_6639), second=int(int_7640), microsecond=int((int_8641 if int_8641 is not None else 0)))
        result643 = _t1253
        self.record_span(span_start642, "DateTimeValue")
        return result643

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1254 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1255 = 1
            else:
                _t1255 = -1
            _t1254 = _t1255
        prediction644 = _t1254
        if prediction644 == 1:
            self.consume_literal("false")
            _t1256 = False
        else:
            if prediction644 == 0:
                self.consume_literal("true")
                _t1257 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1256 = _t1257
        return _t1256

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start649 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs645 = []
        cond646 = self.match_lookahead_literal(":", 0)
        while cond646:
            _t1258 = self.parse_fragment_id()
            item647 = _t1258
            xs645.append(item647)
            cond646 = self.match_lookahead_literal(":", 0)
        fragment_ids648 = xs645
        self.consume_literal(")")
        _t1259 = transactions_pb2.Sync(fragments=fragment_ids648)
        result650 = _t1259
        self.record_span(span_start649, "Sync")
        return result650

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start652 = self.span_start()
        self.consume_literal(":")
        symbol651 = self.consume_terminal("SYMBOL")
        result653 = fragments_pb2.FragmentId(id=symbol651.encode())
        self.record_span(span_start652, "FragmentId")
        return result653

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start656 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1261 = self.parse_epoch_writes()
            _t1260 = _t1261
        else:
            _t1260 = None
        epoch_writes654 = _t1260
        if self.match_lookahead_literal("(", 0):
            _t1263 = self.parse_epoch_reads()
            _t1262 = _t1263
        else:
            _t1262 = None
        epoch_reads655 = _t1262
        self.consume_literal(")")
        _t1264 = transactions_pb2.Epoch(writes=(epoch_writes654 if epoch_writes654 is not None else []), reads=(epoch_reads655 if epoch_reads655 is not None else []))
        result657 = _t1264
        self.record_span(span_start656, "Epoch")
        return result657

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs658 = []
        cond659 = self.match_lookahead_literal("(", 0)
        while cond659:
            _t1265 = self.parse_write()
            item660 = _t1265
            xs658.append(item660)
            cond659 = self.match_lookahead_literal("(", 0)
        writes661 = xs658
        self.consume_literal(")")
        return writes661

    def parse_write(self) -> transactions_pb2.Write:
        span_start667 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1267 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1268 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1269 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1270 = 2
                        else:
                            _t1270 = -1
                        _t1269 = _t1270
                    _t1268 = _t1269
                _t1267 = _t1268
            _t1266 = _t1267
        else:
            _t1266 = -1
        prediction662 = _t1266
        if prediction662 == 3:
            _t1272 = self.parse_snapshot()
            snapshot666 = _t1272
            _t1273 = transactions_pb2.Write(snapshot=snapshot666)
            _t1271 = _t1273
        else:
            if prediction662 == 2:
                _t1275 = self.parse_context()
                context665 = _t1275
                _t1276 = transactions_pb2.Write(context=context665)
                _t1274 = _t1276
            else:
                if prediction662 == 1:
                    _t1278 = self.parse_undefine()
                    undefine664 = _t1278
                    _t1279 = transactions_pb2.Write(undefine=undefine664)
                    _t1277 = _t1279
                else:
                    if prediction662 == 0:
                        _t1281 = self.parse_define()
                        define663 = _t1281
                        _t1282 = transactions_pb2.Write(define=define663)
                        _t1280 = _t1282
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1277 = _t1280
                _t1274 = _t1277
            _t1271 = _t1274
        result668 = _t1271
        self.record_span(span_start667, "Write")
        return result668

    def parse_define(self) -> transactions_pb2.Define:
        span_start670 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1283 = self.parse_fragment()
        fragment669 = _t1283
        self.consume_literal(")")
        _t1284 = transactions_pb2.Define(fragment=fragment669)
        result671 = _t1284
        self.record_span(span_start670, "Define")
        return result671

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start677 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1285 = self.parse_new_fragment_id()
        new_fragment_id672 = _t1285
        xs673 = []
        cond674 = self.match_lookahead_literal("(", 0)
        while cond674:
            _t1286 = self.parse_declaration()
            item675 = _t1286
            xs673.append(item675)
            cond674 = self.match_lookahead_literal("(", 0)
        declarations676 = xs673
        self.consume_literal(")")
        result678 = self.construct_fragment(new_fragment_id672, declarations676)
        self.record_span(span_start677, "Fragment")
        return result678

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start680 = self.span_start()
        _t1287 = self.parse_fragment_id()
        fragment_id679 = _t1287
        self.start_fragment(fragment_id679)
        result681 = fragment_id679
        self.record_span(span_start680, "FragmentId")
        return result681

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start687 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("functional_dependency", 1):
                _t1289 = 2
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1290 = 3
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t1291 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t1292 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t1293 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t1294 = 1
                                else:
                                    _t1294 = -1
                                _t1293 = _t1294
                            _t1292 = _t1293
                        _t1291 = _t1292
                    _t1290 = _t1291
                _t1289 = _t1290
            _t1288 = _t1289
        else:
            _t1288 = -1
        prediction682 = _t1288
        if prediction682 == 3:
            _t1296 = self.parse_data()
            data686 = _t1296
            _t1297 = logic_pb2.Declaration(data=data686)
            _t1295 = _t1297
        else:
            if prediction682 == 2:
                _t1299 = self.parse_constraint()
                constraint685 = _t1299
                _t1300 = logic_pb2.Declaration(constraint=constraint685)
                _t1298 = _t1300
            else:
                if prediction682 == 1:
                    _t1302 = self.parse_algorithm()
                    algorithm684 = _t1302
                    _t1303 = logic_pb2.Declaration(algorithm=algorithm684)
                    _t1301 = _t1303
                else:
                    if prediction682 == 0:
                        _t1305 = self.parse_def()
                        def683 = _t1305
                        _t1306 = logic_pb2.Declaration()
                        getattr(_t1306, 'def').CopyFrom(def683)
                        _t1304 = _t1306
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1301 = _t1304
                _t1298 = _t1301
            _t1295 = _t1298
        result688 = _t1295
        self.record_span(span_start687, "Declaration")
        return result688

    def parse_def(self) -> logic_pb2.Def:
        span_start692 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1307 = self.parse_relation_id()
        relation_id689 = _t1307
        _t1308 = self.parse_abstraction()
        abstraction690 = _t1308
        if self.match_lookahead_literal("(", 0):
            _t1310 = self.parse_attrs()
            _t1309 = _t1310
        else:
            _t1309 = None
        attrs691 = _t1309
        self.consume_literal(")")
        _t1311 = logic_pb2.Def(name=relation_id689, body=abstraction690, attrs=(attrs691 if attrs691 is not None else []))
        result693 = _t1311
        self.record_span(span_start692, "Def")
        return result693

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start697 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1312 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1313 = 1
            else:
                _t1313 = -1
            _t1312 = _t1313
        prediction694 = _t1312
        if prediction694 == 1:
            uint128696 = self.consume_terminal("UINT128")
            _t1314 = logic_pb2.RelationId(id_low=uint128696.low, id_high=uint128696.high)
        else:
            if prediction694 == 0:
                self.consume_literal(":")
                symbol695 = self.consume_terminal("SYMBOL")
                _t1315 = self.relation_id_from_string(symbol695)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1314 = _t1315
        result698 = _t1314
        self.record_span(span_start697, "RelationId")
        return result698

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start701 = self.span_start()
        self.consume_literal("(")
        _t1316 = self.parse_bindings()
        bindings699 = _t1316
        _t1317 = self.parse_formula()
        formula700 = _t1317
        self.consume_literal(")")
        _t1318 = logic_pb2.Abstraction(vars=(list(bindings699[0]) + list(bindings699[1] if bindings699[1] is not None else [])), value=formula700)
        result702 = _t1318
        self.record_span(span_start701, "Abstraction")
        return result702

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs703 = []
        cond704 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond704:
            _t1319 = self.parse_binding()
            item705 = _t1319
            xs703.append(item705)
            cond704 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings706 = xs703
        if self.match_lookahead_literal("|", 0):
            _t1321 = self.parse_value_bindings()
            _t1320 = _t1321
        else:
            _t1320 = None
        value_bindings707 = _t1320
        self.consume_literal("]")
        return (bindings706, (value_bindings707 if value_bindings707 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start710 = self.span_start()
        symbol708 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1322 = self.parse_type()
        type709 = _t1322
        _t1323 = logic_pb2.Var(name=symbol708)
        _t1324 = logic_pb2.Binding(var=_t1323, type=type709)
        result711 = _t1324
        self.record_span(span_start710, "Binding")
        return result711

    def parse_type(self) -> logic_pb2.Type:
        span_start726 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1325 = 0
        else:
            if self.match_lookahead_literal("UINT128", 0):
                _t1326 = 4
            else:
                if self.match_lookahead_literal("STRING", 0):
                    _t1327 = 1
                else:
                    if self.match_lookahead_literal("MISSING", 0):
                        _t1328 = 8
                    else:
                        if self.match_lookahead_literal("INT32", 0):
                            _t1329 = 11
                        else:
                            if self.match_lookahead_literal("INT128", 0):
                                _t1330 = 5
                            else:
                                if self.match_lookahead_literal("INT", 0):
                                    _t1331 = 2
                                else:
                                    if self.match_lookahead_literal("FLOAT32", 0):
                                        _t1332 = 12
                                    else:
                                        if self.match_lookahead_literal("FLOAT", 0):
                                            _t1333 = 3
                                        else:
                                            if self.match_lookahead_literal("DATETIME", 0):
                                                _t1334 = 7
                                            else:
                                                if self.match_lookahead_literal("DATE", 0):
                                                    _t1335 = 6
                                                else:
                                                    if self.match_lookahead_literal("BOOLEAN", 0):
                                                        _t1336 = 10
                                                    else:
                                                        if self.match_lookahead_literal("(", 0):
                                                            _t1337 = 9
                                                        else:
                                                            _t1337 = -1
                                                        _t1336 = _t1337
                                                    _t1335 = _t1336
                                                _t1334 = _t1335
                                            _t1333 = _t1334
                                        _t1332 = _t1333
                                    _t1331 = _t1332
                                _t1330 = _t1331
                            _t1329 = _t1330
                        _t1328 = _t1329
                    _t1327 = _t1328
                _t1326 = _t1327
            _t1325 = _t1326
        prediction712 = _t1325
        if prediction712 == 12:
            _t1339 = self.parse_float32_type()
            float32_type725 = _t1339
            _t1340 = logic_pb2.Type(float32_type=float32_type725)
            _t1338 = _t1340
        else:
            if prediction712 == 11:
                _t1342 = self.parse_int32_type()
                int32_type724 = _t1342
                _t1343 = logic_pb2.Type(int32_type=int32_type724)
                _t1341 = _t1343
            else:
                if prediction712 == 10:
                    _t1345 = self.parse_boolean_type()
                    boolean_type723 = _t1345
                    _t1346 = logic_pb2.Type(boolean_type=boolean_type723)
                    _t1344 = _t1346
                else:
                    if prediction712 == 9:
                        _t1348 = self.parse_decimal_type()
                        decimal_type722 = _t1348
                        _t1349 = logic_pb2.Type(decimal_type=decimal_type722)
                        _t1347 = _t1349
                    else:
                        if prediction712 == 8:
                            _t1351 = self.parse_missing_type()
                            missing_type721 = _t1351
                            _t1352 = logic_pb2.Type(missing_type=missing_type721)
                            _t1350 = _t1352
                        else:
                            if prediction712 == 7:
                                _t1354 = self.parse_datetime_type()
                                datetime_type720 = _t1354
                                _t1355 = logic_pb2.Type(datetime_type=datetime_type720)
                                _t1353 = _t1355
                            else:
                                if prediction712 == 6:
                                    _t1357 = self.parse_date_type()
                                    date_type719 = _t1357
                                    _t1358 = logic_pb2.Type(date_type=date_type719)
                                    _t1356 = _t1358
                                else:
                                    if prediction712 == 5:
                                        _t1360 = self.parse_int128_type()
                                        int128_type718 = _t1360
                                        _t1361 = logic_pb2.Type(int128_type=int128_type718)
                                        _t1359 = _t1361
                                    else:
                                        if prediction712 == 4:
                                            _t1363 = self.parse_uint128_type()
                                            uint128_type717 = _t1363
                                            _t1364 = logic_pb2.Type(uint128_type=uint128_type717)
                                            _t1362 = _t1364
                                        else:
                                            if prediction712 == 3:
                                                _t1366 = self.parse_float_type()
                                                float_type716 = _t1366
                                                _t1367 = logic_pb2.Type(float_type=float_type716)
                                                _t1365 = _t1367
                                            else:
                                                if prediction712 == 2:
                                                    _t1369 = self.parse_int_type()
                                                    int_type715 = _t1369
                                                    _t1370 = logic_pb2.Type(int_type=int_type715)
                                                    _t1368 = _t1370
                                                else:
                                                    if prediction712 == 1:
                                                        _t1372 = self.parse_string_type()
                                                        string_type714 = _t1372
                                                        _t1373 = logic_pb2.Type(string_type=string_type714)
                                                        _t1371 = _t1373
                                                    else:
                                                        if prediction712 == 0:
                                                            _t1375 = self.parse_unspecified_type()
                                                            unspecified_type713 = _t1375
                                                            _t1376 = logic_pb2.Type(unspecified_type=unspecified_type713)
                                                            _t1374 = _t1376
                                                        else:
                                                            raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1371 = _t1374
                                                    _t1368 = _t1371
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
        result727 = _t1338
        self.record_span(span_start726, "Type")
        return result727

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start728 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1377 = logic_pb2.UnspecifiedType()
        result729 = _t1377
        self.record_span(span_start728, "UnspecifiedType")
        return result729

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start730 = self.span_start()
        self.consume_literal("STRING")
        _t1378 = logic_pb2.StringType()
        result731 = _t1378
        self.record_span(span_start730, "StringType")
        return result731

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start732 = self.span_start()
        self.consume_literal("INT")
        _t1379 = logic_pb2.IntType()
        result733 = _t1379
        self.record_span(span_start732, "IntType")
        return result733

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start734 = self.span_start()
        self.consume_literal("FLOAT")
        _t1380 = logic_pb2.FloatType()
        result735 = _t1380
        self.record_span(span_start734, "FloatType")
        return result735

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start736 = self.span_start()
        self.consume_literal("UINT128")
        _t1381 = logic_pb2.UInt128Type()
        result737 = _t1381
        self.record_span(span_start736, "UInt128Type")
        return result737

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start738 = self.span_start()
        self.consume_literal("INT128")
        _t1382 = logic_pb2.Int128Type()
        result739 = _t1382
        self.record_span(span_start738, "Int128Type")
        return result739

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start740 = self.span_start()
        self.consume_literal("DATE")
        _t1383 = logic_pb2.DateType()
        result741 = _t1383
        self.record_span(span_start740, "DateType")
        return result741

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start742 = self.span_start()
        self.consume_literal("DATETIME")
        _t1384 = logic_pb2.DateTimeType()
        result743 = _t1384
        self.record_span(span_start742, "DateTimeType")
        return result743

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start744 = self.span_start()
        self.consume_literal("MISSING")
        _t1385 = logic_pb2.MissingType()
        result745 = _t1385
        self.record_span(span_start744, "MissingType")
        return result745

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start748 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int746 = self.consume_terminal("INT")
        int_3747 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1386 = logic_pb2.DecimalType(precision=int(int746), scale=int(int_3747))
        result749 = _t1386
        self.record_span(span_start748, "DecimalType")
        return result749

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start750 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1387 = logic_pb2.BooleanType()
        result751 = _t1387
        self.record_span(span_start750, "BooleanType")
        return result751

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start752 = self.span_start()
        self.consume_literal("INT32")
        _t1388 = logic_pb2.Int32Type()
        result753 = _t1388
        self.record_span(span_start752, "Int32Type")
        return result753

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start754 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1389 = logic_pb2.Float32Type()
        result755 = _t1389
        self.record_span(span_start754, "Float32Type")
        return result755

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs756 = []
        cond757 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond757:
            _t1390 = self.parse_binding()
            item758 = _t1390
            xs756.append(item758)
            cond757 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings759 = xs756
        return bindings759

    def parse_formula(self) -> logic_pb2.Formula:
        span_start774 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1392 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1393 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1394 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1395 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1396 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1397 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1398 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1399 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1400 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1401 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1402 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1403 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1404 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1405 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1406 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1407 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1408 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1409 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1410 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1411 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1412 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1413 = 10
                                                                                                else:
                                                                                                    _t1413 = -1
                                                                                                _t1412 = _t1413
                                                                                            _t1411 = _t1412
                                                                                        _t1410 = _t1411
                                                                                    _t1409 = _t1410
                                                                                _t1408 = _t1409
                                                                            _t1407 = _t1408
                                                                        _t1406 = _t1407
                                                                    _t1405 = _t1406
                                                                _t1404 = _t1405
                                                            _t1403 = _t1404
                                                        _t1402 = _t1403
                                                    _t1401 = _t1402
                                                _t1400 = _t1401
                                            _t1399 = _t1400
                                        _t1398 = _t1399
                                    _t1397 = _t1398
                                _t1396 = _t1397
                            _t1395 = _t1396
                        _t1394 = _t1395
                    _t1393 = _t1394
                _t1392 = _t1393
            _t1391 = _t1392
        else:
            _t1391 = -1
        prediction760 = _t1391
        if prediction760 == 12:
            _t1415 = self.parse_cast()
            cast773 = _t1415
            _t1416 = logic_pb2.Formula(cast=cast773)
            _t1414 = _t1416
        else:
            if prediction760 == 11:
                _t1418 = self.parse_rel_atom()
                rel_atom772 = _t1418
                _t1419 = logic_pb2.Formula(rel_atom=rel_atom772)
                _t1417 = _t1419
            else:
                if prediction760 == 10:
                    _t1421 = self.parse_primitive()
                    primitive771 = _t1421
                    _t1422 = logic_pb2.Formula(primitive=primitive771)
                    _t1420 = _t1422
                else:
                    if prediction760 == 9:
                        _t1424 = self.parse_pragma()
                        pragma770 = _t1424
                        _t1425 = logic_pb2.Formula(pragma=pragma770)
                        _t1423 = _t1425
                    else:
                        if prediction760 == 8:
                            _t1427 = self.parse_atom()
                            atom769 = _t1427
                            _t1428 = logic_pb2.Formula(atom=atom769)
                            _t1426 = _t1428
                        else:
                            if prediction760 == 7:
                                _t1430 = self.parse_ffi()
                                ffi768 = _t1430
                                _t1431 = logic_pb2.Formula(ffi=ffi768)
                                _t1429 = _t1431
                            else:
                                if prediction760 == 6:
                                    _t1433 = self.parse_not()
                                    not767 = _t1433
                                    _t1434 = logic_pb2.Formula()
                                    getattr(_t1434, 'not').CopyFrom(not767)
                                    _t1432 = _t1434
                                else:
                                    if prediction760 == 5:
                                        _t1436 = self.parse_disjunction()
                                        disjunction766 = _t1436
                                        _t1437 = logic_pb2.Formula(disjunction=disjunction766)
                                        _t1435 = _t1437
                                    else:
                                        if prediction760 == 4:
                                            _t1439 = self.parse_conjunction()
                                            conjunction765 = _t1439
                                            _t1440 = logic_pb2.Formula(conjunction=conjunction765)
                                            _t1438 = _t1440
                                        else:
                                            if prediction760 == 3:
                                                _t1442 = self.parse_reduce()
                                                reduce764 = _t1442
                                                _t1443 = logic_pb2.Formula(reduce=reduce764)
                                                _t1441 = _t1443
                                            else:
                                                if prediction760 == 2:
                                                    _t1445 = self.parse_exists()
                                                    exists763 = _t1445
                                                    _t1446 = logic_pb2.Formula(exists=exists763)
                                                    _t1444 = _t1446
                                                else:
                                                    if prediction760 == 1:
                                                        _t1448 = self.parse_false()
                                                        false762 = _t1448
                                                        _t1449 = logic_pb2.Formula(disjunction=false762)
                                                        _t1447 = _t1449
                                                    else:
                                                        if prediction760 == 0:
                                                            _t1451 = self.parse_true()
                                                            true761 = _t1451
                                                            _t1452 = logic_pb2.Formula(conjunction=true761)
                                                            _t1450 = _t1452
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1447 = _t1450
                                                    _t1444 = _t1447
                                                _t1441 = _t1444
                                            _t1438 = _t1441
                                        _t1435 = _t1438
                                    _t1432 = _t1435
                                _t1429 = _t1432
                            _t1426 = _t1429
                        _t1423 = _t1426
                    _t1420 = _t1423
                _t1417 = _t1420
            _t1414 = _t1417
        result775 = _t1414
        self.record_span(span_start774, "Formula")
        return result775

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start776 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1453 = logic_pb2.Conjunction(args=[])
        result777 = _t1453
        self.record_span(span_start776, "Conjunction")
        return result777

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start778 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1454 = logic_pb2.Disjunction(args=[])
        result779 = _t1454
        self.record_span(span_start778, "Disjunction")
        return result779

    def parse_exists(self) -> logic_pb2.Exists:
        span_start782 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1455 = self.parse_bindings()
        bindings780 = _t1455
        _t1456 = self.parse_formula()
        formula781 = _t1456
        self.consume_literal(")")
        _t1457 = logic_pb2.Abstraction(vars=(list(bindings780[0]) + list(bindings780[1] if bindings780[1] is not None else [])), value=formula781)
        _t1458 = logic_pb2.Exists(body=_t1457)
        result783 = _t1458
        self.record_span(span_start782, "Exists")
        return result783

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start787 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1459 = self.parse_abstraction()
        abstraction784 = _t1459
        _t1460 = self.parse_abstraction()
        abstraction_3785 = _t1460
        _t1461 = self.parse_terms()
        terms786 = _t1461
        self.consume_literal(")")
        _t1462 = logic_pb2.Reduce(op=abstraction784, body=abstraction_3785, terms=terms786)
        result788 = _t1462
        self.record_span(span_start787, "Reduce")
        return result788

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs789 = []
        cond790 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond790:
            _t1463 = self.parse_term()
            item791 = _t1463
            xs789.append(item791)
            cond790 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms792 = xs789
        self.consume_literal(")")
        return terms792

    def parse_term(self) -> logic_pb2.Term:
        span_start796 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1464 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1465 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1466 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1467 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1468 = 0
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1469 = 1
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1470 = 1
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1471 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1472 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1473 = 1
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1474 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1475 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1476 = 1
                                                        else:
                                                            _t1476 = -1
                                                        _t1475 = _t1476
                                                    _t1474 = _t1475
                                                _t1473 = _t1474
                                            _t1472 = _t1473
                                        _t1471 = _t1472
                                    _t1470 = _t1471
                                _t1469 = _t1470
                            _t1468 = _t1469
                        _t1467 = _t1468
                    _t1466 = _t1467
                _t1465 = _t1466
            _t1464 = _t1465
        prediction793 = _t1464
        if prediction793 == 1:
            _t1478 = self.parse_value()
            value795 = _t1478
            _t1479 = logic_pb2.Term(constant=value795)
            _t1477 = _t1479
        else:
            if prediction793 == 0:
                _t1481 = self.parse_var()
                var794 = _t1481
                _t1482 = logic_pb2.Term(var=var794)
                _t1480 = _t1482
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1477 = _t1480
        result797 = _t1477
        self.record_span(span_start796, "Term")
        return result797

    def parse_var(self) -> logic_pb2.Var:
        span_start799 = self.span_start()
        symbol798 = self.consume_terminal("SYMBOL")
        _t1483 = logic_pb2.Var(name=symbol798)
        result800 = _t1483
        self.record_span(span_start799, "Var")
        return result800

    def parse_value(self) -> logic_pb2.Value:
        span_start813 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1484 = 11
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1485 = 10
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1486 = 11
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1488 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1489 = 0
                            else:
                                _t1489 = -1
                            _t1488 = _t1489
                        _t1487 = _t1488
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1490 = 7
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t1491 = 2
                            else:
                                if self.match_lookahead_terminal("INT32", 0):
                                    _t1492 = 3
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t1493 = 8
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t1494 = 4
                                        else:
                                            if self.match_lookahead_terminal("FLOAT32", 0):
                                                _t1495 = 5
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1496 = 6
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1497 = 9
                                                    else:
                                                        _t1497 = -1
                                                    _t1496 = _t1497
                                                _t1495 = _t1496
                                            _t1494 = _t1495
                                        _t1493 = _t1494
                                    _t1492 = _t1493
                                _t1491 = _t1492
                            _t1490 = _t1491
                        _t1487 = _t1490
                    _t1486 = _t1487
                _t1485 = _t1486
            _t1484 = _t1485
        prediction801 = _t1484
        if prediction801 == 11:
            _t1499 = self.parse_boolean_value()
            boolean_value812 = _t1499
            _t1500 = logic_pb2.Value(boolean_value=boolean_value812)
            _t1498 = _t1500
        else:
            if prediction801 == 10:
                self.consume_literal("missing")
                _t1502 = logic_pb2.MissingValue()
                _t1503 = logic_pb2.Value(missing_value=_t1502)
                _t1501 = _t1503
            else:
                if prediction801 == 9:
                    formatted_decimal811 = self.consume_terminal("DECIMAL")
                    _t1505 = logic_pb2.Value(decimal_value=formatted_decimal811)
                    _t1504 = _t1505
                else:
                    if prediction801 == 8:
                        formatted_int128810 = self.consume_terminal("INT128")
                        _t1507 = logic_pb2.Value(int128_value=formatted_int128810)
                        _t1506 = _t1507
                    else:
                        if prediction801 == 7:
                            formatted_uint128809 = self.consume_terminal("UINT128")
                            _t1509 = logic_pb2.Value(uint128_value=formatted_uint128809)
                            _t1508 = _t1509
                        else:
                            if prediction801 == 6:
                                formatted_float808 = self.consume_terminal("FLOAT")
                                _t1511 = logic_pb2.Value(float_value=formatted_float808)
                                _t1510 = _t1511
                            else:
                                if prediction801 == 5:
                                    formatted_float32807 = self.consume_terminal("FLOAT32")
                                    _t1513 = logic_pb2.Value(float32_value=formatted_float32807)
                                    _t1512 = _t1513
                                else:
                                    if prediction801 == 4:
                                        formatted_int806 = self.consume_terminal("INT")
                                        _t1515 = logic_pb2.Value(int_value=formatted_int806)
                                        _t1514 = _t1515
                                    else:
                                        if prediction801 == 3:
                                            formatted_int32805 = self.consume_terminal("INT32")
                                            _t1517 = logic_pb2.Value(int32_value=formatted_int32805)
                                            _t1516 = _t1517
                                        else:
                                            if prediction801 == 2:
                                                formatted_string804 = self.consume_terminal("STRING")
                                                _t1519 = logic_pb2.Value(string_value=formatted_string804)
                                                _t1518 = _t1519
                                            else:
                                                if prediction801 == 1:
                                                    _t1521 = self.parse_datetime()
                                                    datetime803 = _t1521
                                                    _t1522 = logic_pb2.Value(datetime_value=datetime803)
                                                    _t1520 = _t1522
                                                else:
                                                    if prediction801 == 0:
                                                        _t1524 = self.parse_date()
                                                        date802 = _t1524
                                                        _t1525 = logic_pb2.Value(date_value=date802)
                                                        _t1523 = _t1525
                                                    else:
                                                        raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                    _t1520 = _t1523
                                                _t1518 = _t1520
                                            _t1516 = _t1518
                                        _t1514 = _t1516
                                    _t1512 = _t1514
                                _t1510 = _t1512
                            _t1508 = _t1510
                        _t1506 = _t1508
                    _t1504 = _t1506
                _t1501 = _t1504
            _t1498 = _t1501
        result814 = _t1498
        self.record_span(span_start813, "Value")
        return result814

    def parse_date(self) -> logic_pb2.DateValue:
        span_start818 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int815 = self.consume_terminal("INT")
        formatted_int_3816 = self.consume_terminal("INT")
        formatted_int_4817 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1526 = logic_pb2.DateValue(year=int(formatted_int815), month=int(formatted_int_3816), day=int(formatted_int_4817))
        result819 = _t1526
        self.record_span(span_start818, "DateValue")
        return result819

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start827 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int820 = self.consume_terminal("INT")
        formatted_int_3821 = self.consume_terminal("INT")
        formatted_int_4822 = self.consume_terminal("INT")
        formatted_int_5823 = self.consume_terminal("INT")
        formatted_int_6824 = self.consume_terminal("INT")
        formatted_int_7825 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1527 = self.consume_terminal("INT")
        else:
            _t1527 = None
        formatted_int_8826 = _t1527
        self.consume_literal(")")
        _t1528 = logic_pb2.DateTimeValue(year=int(formatted_int820), month=int(formatted_int_3821), day=int(formatted_int_4822), hour=int(formatted_int_5823), minute=int(formatted_int_6824), second=int(formatted_int_7825), microsecond=int((formatted_int_8826 if formatted_int_8826 is not None else 0)))
        result828 = _t1528
        self.record_span(span_start827, "DateTimeValue")
        return result828

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start833 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs829 = []
        cond830 = self.match_lookahead_literal("(", 0)
        while cond830:
            _t1529 = self.parse_formula()
            item831 = _t1529
            xs829.append(item831)
            cond830 = self.match_lookahead_literal("(", 0)
        formulas832 = xs829
        self.consume_literal(")")
        _t1530 = logic_pb2.Conjunction(args=formulas832)
        result834 = _t1530
        self.record_span(span_start833, "Conjunction")
        return result834

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start839 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs835 = []
        cond836 = self.match_lookahead_literal("(", 0)
        while cond836:
            _t1531 = self.parse_formula()
            item837 = _t1531
            xs835.append(item837)
            cond836 = self.match_lookahead_literal("(", 0)
        formulas838 = xs835
        self.consume_literal(")")
        _t1532 = logic_pb2.Disjunction(args=formulas838)
        result840 = _t1532
        self.record_span(span_start839, "Disjunction")
        return result840

    def parse_not(self) -> logic_pb2.Not:
        span_start842 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1533 = self.parse_formula()
        formula841 = _t1533
        self.consume_literal(")")
        _t1534 = logic_pb2.Not(arg=formula841)
        result843 = _t1534
        self.record_span(span_start842, "Not")
        return result843

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start847 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1535 = self.parse_name()
        name844 = _t1535
        _t1536 = self.parse_ffi_args()
        ffi_args845 = _t1536
        _t1537 = self.parse_terms()
        terms846 = _t1537
        self.consume_literal(")")
        _t1538 = logic_pb2.FFI(name=name844, args=ffi_args845, terms=terms846)
        result848 = _t1538
        self.record_span(span_start847, "FFI")
        return result848

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol849 = self.consume_terminal("SYMBOL")
        return symbol849

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs850 = []
        cond851 = self.match_lookahead_literal("(", 0)
        while cond851:
            _t1539 = self.parse_abstraction()
            item852 = _t1539
            xs850.append(item852)
            cond851 = self.match_lookahead_literal("(", 0)
        abstractions853 = xs850
        self.consume_literal(")")
        return abstractions853

    def parse_atom(self) -> logic_pb2.Atom:
        span_start859 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1540 = self.parse_relation_id()
        relation_id854 = _t1540
        xs855 = []
        cond856 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond856:
            _t1541 = self.parse_term()
            item857 = _t1541
            xs855.append(item857)
            cond856 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms858 = xs855
        self.consume_literal(")")
        _t1542 = logic_pb2.Atom(name=relation_id854, terms=terms858)
        result860 = _t1542
        self.record_span(span_start859, "Atom")
        return result860

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start866 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1543 = self.parse_name()
        name861 = _t1543
        xs862 = []
        cond863 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond863:
            _t1544 = self.parse_term()
            item864 = _t1544
            xs862.append(item864)
            cond863 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms865 = xs862
        self.consume_literal(")")
        _t1545 = logic_pb2.Pragma(name=name861, terms=terms865)
        result867 = _t1545
        self.record_span(span_start866, "Pragma")
        return result867

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start883 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1547 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1548 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1549 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1550 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1551 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1552 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1553 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1554 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1555 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1556 = 7
                                                else:
                                                    _t1556 = -1
                                                _t1555 = _t1556
                                            _t1554 = _t1555
                                        _t1553 = _t1554
                                    _t1552 = _t1553
                                _t1551 = _t1552
                            _t1550 = _t1551
                        _t1549 = _t1550
                    _t1548 = _t1549
                _t1547 = _t1548
            _t1546 = _t1547
        else:
            _t1546 = -1
        prediction868 = _t1546
        if prediction868 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1558 = self.parse_name()
            name878 = _t1558
            xs879 = []
            cond880 = (((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond880:
                _t1559 = self.parse_rel_term()
                item881 = _t1559
                xs879.append(item881)
                cond880 = (((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms882 = xs879
            self.consume_literal(")")
            _t1560 = logic_pb2.Primitive(name=name878, terms=rel_terms882)
            _t1557 = _t1560
        else:
            if prediction868 == 8:
                _t1562 = self.parse_divide()
                divide877 = _t1562
                _t1561 = divide877
            else:
                if prediction868 == 7:
                    _t1564 = self.parse_multiply()
                    multiply876 = _t1564
                    _t1563 = multiply876
                else:
                    if prediction868 == 6:
                        _t1566 = self.parse_minus()
                        minus875 = _t1566
                        _t1565 = minus875
                    else:
                        if prediction868 == 5:
                            _t1568 = self.parse_add()
                            add874 = _t1568
                            _t1567 = add874
                        else:
                            if prediction868 == 4:
                                _t1570 = self.parse_gt_eq()
                                gt_eq873 = _t1570
                                _t1569 = gt_eq873
                            else:
                                if prediction868 == 3:
                                    _t1572 = self.parse_gt()
                                    gt872 = _t1572
                                    _t1571 = gt872
                                else:
                                    if prediction868 == 2:
                                        _t1574 = self.parse_lt_eq()
                                        lt_eq871 = _t1574
                                        _t1573 = lt_eq871
                                    else:
                                        if prediction868 == 1:
                                            _t1576 = self.parse_lt()
                                            lt870 = _t1576
                                            _t1575 = lt870
                                        else:
                                            if prediction868 == 0:
                                                _t1578 = self.parse_eq()
                                                eq869 = _t1578
                                                _t1577 = eq869
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1575 = _t1577
                                        _t1573 = _t1575
                                    _t1571 = _t1573
                                _t1569 = _t1571
                            _t1567 = _t1569
                        _t1565 = _t1567
                    _t1563 = _t1565
                _t1561 = _t1563
            _t1557 = _t1561
        result884 = _t1557
        self.record_span(span_start883, "Primitive")
        return result884

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start887 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1579 = self.parse_term()
        term885 = _t1579
        _t1580 = self.parse_term()
        term_3886 = _t1580
        self.consume_literal(")")
        _t1581 = logic_pb2.RelTerm(term=term885)
        _t1582 = logic_pb2.RelTerm(term=term_3886)
        _t1583 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1581, _t1582])
        result888 = _t1583
        self.record_span(span_start887, "Primitive")
        return result888

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start891 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1584 = self.parse_term()
        term889 = _t1584
        _t1585 = self.parse_term()
        term_3890 = _t1585
        self.consume_literal(")")
        _t1586 = logic_pb2.RelTerm(term=term889)
        _t1587 = logic_pb2.RelTerm(term=term_3890)
        _t1588 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1586, _t1587])
        result892 = _t1588
        self.record_span(span_start891, "Primitive")
        return result892

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start895 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1589 = self.parse_term()
        term893 = _t1589
        _t1590 = self.parse_term()
        term_3894 = _t1590
        self.consume_literal(")")
        _t1591 = logic_pb2.RelTerm(term=term893)
        _t1592 = logic_pb2.RelTerm(term=term_3894)
        _t1593 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1591, _t1592])
        result896 = _t1593
        self.record_span(span_start895, "Primitive")
        return result896

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start899 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1594 = self.parse_term()
        term897 = _t1594
        _t1595 = self.parse_term()
        term_3898 = _t1595
        self.consume_literal(")")
        _t1596 = logic_pb2.RelTerm(term=term897)
        _t1597 = logic_pb2.RelTerm(term=term_3898)
        _t1598 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1596, _t1597])
        result900 = _t1598
        self.record_span(span_start899, "Primitive")
        return result900

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start903 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1599 = self.parse_term()
        term901 = _t1599
        _t1600 = self.parse_term()
        term_3902 = _t1600
        self.consume_literal(")")
        _t1601 = logic_pb2.RelTerm(term=term901)
        _t1602 = logic_pb2.RelTerm(term=term_3902)
        _t1603 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1601, _t1602])
        result904 = _t1603
        self.record_span(span_start903, "Primitive")
        return result904

    def parse_add(self) -> logic_pb2.Primitive:
        span_start908 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1604 = self.parse_term()
        term905 = _t1604
        _t1605 = self.parse_term()
        term_3906 = _t1605
        _t1606 = self.parse_term()
        term_4907 = _t1606
        self.consume_literal(")")
        _t1607 = logic_pb2.RelTerm(term=term905)
        _t1608 = logic_pb2.RelTerm(term=term_3906)
        _t1609 = logic_pb2.RelTerm(term=term_4907)
        _t1610 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1607, _t1608, _t1609])
        result909 = _t1610
        self.record_span(span_start908, "Primitive")
        return result909

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start913 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1611 = self.parse_term()
        term910 = _t1611
        _t1612 = self.parse_term()
        term_3911 = _t1612
        _t1613 = self.parse_term()
        term_4912 = _t1613
        self.consume_literal(")")
        _t1614 = logic_pb2.RelTerm(term=term910)
        _t1615 = logic_pb2.RelTerm(term=term_3911)
        _t1616 = logic_pb2.RelTerm(term=term_4912)
        _t1617 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1614, _t1615, _t1616])
        result914 = _t1617
        self.record_span(span_start913, "Primitive")
        return result914

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start918 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1618 = self.parse_term()
        term915 = _t1618
        _t1619 = self.parse_term()
        term_3916 = _t1619
        _t1620 = self.parse_term()
        term_4917 = _t1620
        self.consume_literal(")")
        _t1621 = logic_pb2.RelTerm(term=term915)
        _t1622 = logic_pb2.RelTerm(term=term_3916)
        _t1623 = logic_pb2.RelTerm(term=term_4917)
        _t1624 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1621, _t1622, _t1623])
        result919 = _t1624
        self.record_span(span_start918, "Primitive")
        return result919

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start923 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1625 = self.parse_term()
        term920 = _t1625
        _t1626 = self.parse_term()
        term_3921 = _t1626
        _t1627 = self.parse_term()
        term_4922 = _t1627
        self.consume_literal(")")
        _t1628 = logic_pb2.RelTerm(term=term920)
        _t1629 = logic_pb2.RelTerm(term=term_3921)
        _t1630 = logic_pb2.RelTerm(term=term_4922)
        _t1631 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1628, _t1629, _t1630])
        result924 = _t1631
        self.record_span(span_start923, "Primitive")
        return result924

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start928 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1632 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1633 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1634 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1635 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1636 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1637 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1638 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1639 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1640 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1641 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1642 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1643 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1644 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1645 = 1
                                                            else:
                                                                _t1645 = -1
                                                            _t1644 = _t1645
                                                        _t1643 = _t1644
                                                    _t1642 = _t1643
                                                _t1641 = _t1642
                                            _t1640 = _t1641
                                        _t1639 = _t1640
                                    _t1638 = _t1639
                                _t1637 = _t1638
                            _t1636 = _t1637
                        _t1635 = _t1636
                    _t1634 = _t1635
                _t1633 = _t1634
            _t1632 = _t1633
        prediction925 = _t1632
        if prediction925 == 1:
            _t1647 = self.parse_term()
            term927 = _t1647
            _t1648 = logic_pb2.RelTerm(term=term927)
            _t1646 = _t1648
        else:
            if prediction925 == 0:
                _t1650 = self.parse_specialized_value()
                specialized_value926 = _t1650
                _t1651 = logic_pb2.RelTerm(specialized_value=specialized_value926)
                _t1649 = _t1651
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1646 = _t1649
        result929 = _t1646
        self.record_span(span_start928, "RelTerm")
        return result929

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start931 = self.span_start()
        self.consume_literal("#")
        _t1652 = self.parse_raw_value()
        raw_value930 = _t1652
        result932 = raw_value930
        self.record_span(span_start931, "Value")
        return result932

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start938 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1653 = self.parse_name()
        name933 = _t1653
        xs934 = []
        cond935 = (((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond935:
            _t1654 = self.parse_rel_term()
            item936 = _t1654
            xs934.append(item936)
            cond935 = (((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms937 = xs934
        self.consume_literal(")")
        _t1655 = logic_pb2.RelAtom(name=name933, terms=rel_terms937)
        result939 = _t1655
        self.record_span(span_start938, "RelAtom")
        return result939

    def parse_cast(self) -> logic_pb2.Cast:
        span_start942 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1656 = self.parse_term()
        term940 = _t1656
        _t1657 = self.parse_term()
        term_3941 = _t1657
        self.consume_literal(")")
        _t1658 = logic_pb2.Cast(input=term940, result=term_3941)
        result943 = _t1658
        self.record_span(span_start942, "Cast")
        return result943

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs944 = []
        cond945 = self.match_lookahead_literal("(", 0)
        while cond945:
            _t1659 = self.parse_attribute()
            item946 = _t1659
            xs944.append(item946)
            cond945 = self.match_lookahead_literal("(", 0)
        attributes947 = xs944
        self.consume_literal(")")
        return attributes947

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start953 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1660 = self.parse_name()
        name948 = _t1660
        xs949 = []
        cond950 = (((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        while cond950:
            _t1661 = self.parse_raw_value()
            item951 = _t1661
            xs949.append(item951)
            cond950 = (((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        raw_values952 = xs949
        self.consume_literal(")")
        _t1662 = logic_pb2.Attribute(name=name948, args=raw_values952)
        result954 = _t1662
        self.record_span(span_start953, "Attribute")
        return result954

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start960 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs955 = []
        cond956 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond956:
            _t1663 = self.parse_relation_id()
            item957 = _t1663
            xs955.append(item957)
            cond956 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids958 = xs955
        _t1664 = self.parse_script()
        script959 = _t1664
        self.consume_literal(")")
        _t1665 = logic_pb2.Algorithm(body=script959)
        getattr(_t1665, 'global').extend(relation_ids958)
        result961 = _t1665
        self.record_span(span_start960, "Algorithm")
        return result961

    def parse_script(self) -> logic_pb2.Script:
        span_start966 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs962 = []
        cond963 = self.match_lookahead_literal("(", 0)
        while cond963:
            _t1666 = self.parse_construct()
            item964 = _t1666
            xs962.append(item964)
            cond963 = self.match_lookahead_literal("(", 0)
        constructs965 = xs962
        self.consume_literal(")")
        _t1667 = logic_pb2.Script(constructs=constructs965)
        result967 = _t1667
        self.record_span(span_start966, "Script")
        return result967

    def parse_construct(self) -> logic_pb2.Construct:
        span_start971 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1669 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1670 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1671 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1672 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1673 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1674 = 1
                                else:
                                    _t1674 = -1
                                _t1673 = _t1674
                            _t1672 = _t1673
                        _t1671 = _t1672
                    _t1670 = _t1671
                _t1669 = _t1670
            _t1668 = _t1669
        else:
            _t1668 = -1
        prediction968 = _t1668
        if prediction968 == 1:
            _t1676 = self.parse_instruction()
            instruction970 = _t1676
            _t1677 = logic_pb2.Construct(instruction=instruction970)
            _t1675 = _t1677
        else:
            if prediction968 == 0:
                _t1679 = self.parse_loop()
                loop969 = _t1679
                _t1680 = logic_pb2.Construct(loop=loop969)
                _t1678 = _t1680
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1675 = _t1678
        result972 = _t1675
        self.record_span(span_start971, "Construct")
        return result972

    def parse_loop(self) -> logic_pb2.Loop:
        span_start975 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1681 = self.parse_init()
        init973 = _t1681
        _t1682 = self.parse_script()
        script974 = _t1682
        self.consume_literal(")")
        _t1683 = logic_pb2.Loop(init=init973, body=script974)
        result976 = _t1683
        self.record_span(span_start975, "Loop")
        return result976

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs977 = []
        cond978 = self.match_lookahead_literal("(", 0)
        while cond978:
            _t1684 = self.parse_instruction()
            item979 = _t1684
            xs977.append(item979)
            cond978 = self.match_lookahead_literal("(", 0)
        instructions980 = xs977
        self.consume_literal(")")
        return instructions980

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start987 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1686 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1687 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1688 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1689 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1690 = 0
                            else:
                                _t1690 = -1
                            _t1689 = _t1690
                        _t1688 = _t1689
                    _t1687 = _t1688
                _t1686 = _t1687
            _t1685 = _t1686
        else:
            _t1685 = -1
        prediction981 = _t1685
        if prediction981 == 4:
            _t1692 = self.parse_monus_def()
            monus_def986 = _t1692
            _t1693 = logic_pb2.Instruction(monus_def=monus_def986)
            _t1691 = _t1693
        else:
            if prediction981 == 3:
                _t1695 = self.parse_monoid_def()
                monoid_def985 = _t1695
                _t1696 = logic_pb2.Instruction(monoid_def=monoid_def985)
                _t1694 = _t1696
            else:
                if prediction981 == 2:
                    _t1698 = self.parse_break()
                    break984 = _t1698
                    _t1699 = logic_pb2.Instruction()
                    getattr(_t1699, 'break').CopyFrom(break984)
                    _t1697 = _t1699
                else:
                    if prediction981 == 1:
                        _t1701 = self.parse_upsert()
                        upsert983 = _t1701
                        _t1702 = logic_pb2.Instruction(upsert=upsert983)
                        _t1700 = _t1702
                    else:
                        if prediction981 == 0:
                            _t1704 = self.parse_assign()
                            assign982 = _t1704
                            _t1705 = logic_pb2.Instruction(assign=assign982)
                            _t1703 = _t1705
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1700 = _t1703
                    _t1697 = _t1700
                _t1694 = _t1697
            _t1691 = _t1694
        result988 = _t1691
        self.record_span(span_start987, "Instruction")
        return result988

    def parse_assign(self) -> logic_pb2.Assign:
        span_start992 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1706 = self.parse_relation_id()
        relation_id989 = _t1706
        _t1707 = self.parse_abstraction()
        abstraction990 = _t1707
        if self.match_lookahead_literal("(", 0):
            _t1709 = self.parse_attrs()
            _t1708 = _t1709
        else:
            _t1708 = None
        attrs991 = _t1708
        self.consume_literal(")")
        _t1710 = logic_pb2.Assign(name=relation_id989, body=abstraction990, attrs=(attrs991 if attrs991 is not None else []))
        result993 = _t1710
        self.record_span(span_start992, "Assign")
        return result993

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start997 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1711 = self.parse_relation_id()
        relation_id994 = _t1711
        _t1712 = self.parse_abstraction_with_arity()
        abstraction_with_arity995 = _t1712
        if self.match_lookahead_literal("(", 0):
            _t1714 = self.parse_attrs()
            _t1713 = _t1714
        else:
            _t1713 = None
        attrs996 = _t1713
        self.consume_literal(")")
        _t1715 = logic_pb2.Upsert(name=relation_id994, body=abstraction_with_arity995[0], attrs=(attrs996 if attrs996 is not None else []), value_arity=abstraction_with_arity995[1])
        result998 = _t1715
        self.record_span(span_start997, "Upsert")
        return result998

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1716 = self.parse_bindings()
        bindings999 = _t1716
        _t1717 = self.parse_formula()
        formula1000 = _t1717
        self.consume_literal(")")
        _t1718 = logic_pb2.Abstraction(vars=(list(bindings999[0]) + list(bindings999[1] if bindings999[1] is not None else [])), value=formula1000)
        return (_t1718, len(bindings999[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1004 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1719 = self.parse_relation_id()
        relation_id1001 = _t1719
        _t1720 = self.parse_abstraction()
        abstraction1002 = _t1720
        if self.match_lookahead_literal("(", 0):
            _t1722 = self.parse_attrs()
            _t1721 = _t1722
        else:
            _t1721 = None
        attrs1003 = _t1721
        self.consume_literal(")")
        _t1723 = logic_pb2.Break(name=relation_id1001, body=abstraction1002, attrs=(attrs1003 if attrs1003 is not None else []))
        result1005 = _t1723
        self.record_span(span_start1004, "Break")
        return result1005

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1010 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1724 = self.parse_monoid()
        monoid1006 = _t1724
        _t1725 = self.parse_relation_id()
        relation_id1007 = _t1725
        _t1726 = self.parse_abstraction_with_arity()
        abstraction_with_arity1008 = _t1726
        if self.match_lookahead_literal("(", 0):
            _t1728 = self.parse_attrs()
            _t1727 = _t1728
        else:
            _t1727 = None
        attrs1009 = _t1727
        self.consume_literal(")")
        _t1729 = logic_pb2.MonoidDef(monoid=monoid1006, name=relation_id1007, body=abstraction_with_arity1008[0], attrs=(attrs1009 if attrs1009 is not None else []), value_arity=abstraction_with_arity1008[1])
        result1011 = _t1729
        self.record_span(span_start1010, "MonoidDef")
        return result1011

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1017 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1731 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1732 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1733 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1734 = 2
                        else:
                            _t1734 = -1
                        _t1733 = _t1734
                    _t1732 = _t1733
                _t1731 = _t1732
            _t1730 = _t1731
        else:
            _t1730 = -1
        prediction1012 = _t1730
        if prediction1012 == 3:
            _t1736 = self.parse_sum_monoid()
            sum_monoid1016 = _t1736
            _t1737 = logic_pb2.Monoid(sum_monoid=sum_monoid1016)
            _t1735 = _t1737
        else:
            if prediction1012 == 2:
                _t1739 = self.parse_max_monoid()
                max_monoid1015 = _t1739
                _t1740 = logic_pb2.Monoid(max_monoid=max_monoid1015)
                _t1738 = _t1740
            else:
                if prediction1012 == 1:
                    _t1742 = self.parse_min_monoid()
                    min_monoid1014 = _t1742
                    _t1743 = logic_pb2.Monoid(min_monoid=min_monoid1014)
                    _t1741 = _t1743
                else:
                    if prediction1012 == 0:
                        _t1745 = self.parse_or_monoid()
                        or_monoid1013 = _t1745
                        _t1746 = logic_pb2.Monoid(or_monoid=or_monoid1013)
                        _t1744 = _t1746
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1741 = _t1744
                _t1738 = _t1741
            _t1735 = _t1738
        result1018 = _t1735
        self.record_span(span_start1017, "Monoid")
        return result1018

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1019 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1747 = logic_pb2.OrMonoid()
        result1020 = _t1747
        self.record_span(span_start1019, "OrMonoid")
        return result1020

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1022 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1748 = self.parse_type()
        type1021 = _t1748
        self.consume_literal(")")
        _t1749 = logic_pb2.MinMonoid(type=type1021)
        result1023 = _t1749
        self.record_span(span_start1022, "MinMonoid")
        return result1023

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1025 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1750 = self.parse_type()
        type1024 = _t1750
        self.consume_literal(")")
        _t1751 = logic_pb2.MaxMonoid(type=type1024)
        result1026 = _t1751
        self.record_span(span_start1025, "MaxMonoid")
        return result1026

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1028 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1752 = self.parse_type()
        type1027 = _t1752
        self.consume_literal(")")
        _t1753 = logic_pb2.SumMonoid(type=type1027)
        result1029 = _t1753
        self.record_span(span_start1028, "SumMonoid")
        return result1029

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1034 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1754 = self.parse_monoid()
        monoid1030 = _t1754
        _t1755 = self.parse_relation_id()
        relation_id1031 = _t1755
        _t1756 = self.parse_abstraction_with_arity()
        abstraction_with_arity1032 = _t1756
        if self.match_lookahead_literal("(", 0):
            _t1758 = self.parse_attrs()
            _t1757 = _t1758
        else:
            _t1757 = None
        attrs1033 = _t1757
        self.consume_literal(")")
        _t1759 = logic_pb2.MonusDef(monoid=monoid1030, name=relation_id1031, body=abstraction_with_arity1032[0], attrs=(attrs1033 if attrs1033 is not None else []), value_arity=abstraction_with_arity1032[1])
        result1035 = _t1759
        self.record_span(span_start1034, "MonusDef")
        return result1035

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1040 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1760 = self.parse_relation_id()
        relation_id1036 = _t1760
        _t1761 = self.parse_abstraction()
        abstraction1037 = _t1761
        _t1762 = self.parse_functional_dependency_keys()
        functional_dependency_keys1038 = _t1762
        _t1763 = self.parse_functional_dependency_values()
        functional_dependency_values1039 = _t1763
        self.consume_literal(")")
        _t1764 = logic_pb2.FunctionalDependency(guard=abstraction1037, keys=functional_dependency_keys1038, values=functional_dependency_values1039)
        _t1765 = logic_pb2.Constraint(name=relation_id1036, functional_dependency=_t1764)
        result1041 = _t1765
        self.record_span(span_start1040, "Constraint")
        return result1041

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1042 = []
        cond1043 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1043:
            _t1766 = self.parse_var()
            item1044 = _t1766
            xs1042.append(item1044)
            cond1043 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1045 = xs1042
        self.consume_literal(")")
        return vars1045

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1046 = []
        cond1047 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1047:
            _t1767 = self.parse_var()
            item1048 = _t1767
            xs1046.append(item1048)
            cond1047 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1049 = xs1046
        self.consume_literal(")")
        return vars1049

    def parse_data(self) -> logic_pb2.Data:
        span_start1054 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("edb", 1):
                _t1769 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1770 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1771 = 1
                    else:
                        _t1771 = -1
                    _t1770 = _t1771
                _t1769 = _t1770
            _t1768 = _t1769
        else:
            _t1768 = -1
        prediction1050 = _t1768
        if prediction1050 == 2:
            _t1773 = self.parse_csv_data()
            csv_data1053 = _t1773
            _t1774 = logic_pb2.Data(csv_data=csv_data1053)
            _t1772 = _t1774
        else:
            if prediction1050 == 1:
                _t1776 = self.parse_betree_relation()
                betree_relation1052 = _t1776
                _t1777 = logic_pb2.Data(betree_relation=betree_relation1052)
                _t1775 = _t1777
            else:
                if prediction1050 == 0:
                    _t1779 = self.parse_edb()
                    edb1051 = _t1779
                    _t1780 = logic_pb2.Data(edb=edb1051)
                    _t1778 = _t1780
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1775 = _t1778
            _t1772 = _t1775
        result1055 = _t1772
        self.record_span(span_start1054, "Data")
        return result1055

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1059 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1781 = self.parse_relation_id()
        relation_id1056 = _t1781
        _t1782 = self.parse_edb_path()
        edb_path1057 = _t1782
        _t1783 = self.parse_edb_types()
        edb_types1058 = _t1783
        self.consume_literal(")")
        _t1784 = logic_pb2.EDB(target_id=relation_id1056, path=edb_path1057, types=edb_types1058)
        result1060 = _t1784
        self.record_span(span_start1059, "EDB")
        return result1060

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1061 = []
        cond1062 = self.match_lookahead_terminal("STRING", 0)
        while cond1062:
            item1063 = self.consume_terminal("STRING")
            xs1061.append(item1063)
            cond1062 = self.match_lookahead_terminal("STRING", 0)
        strings1064 = xs1061
        self.consume_literal("]")
        return strings1064

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1065 = []
        cond1066 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1066:
            _t1785 = self.parse_type()
            item1067 = _t1785
            xs1065.append(item1067)
            cond1066 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1068 = xs1065
        self.consume_literal("]")
        return types1068

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1071 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1786 = self.parse_relation_id()
        relation_id1069 = _t1786
        _t1787 = self.parse_betree_info()
        betree_info1070 = _t1787
        self.consume_literal(")")
        _t1788 = logic_pb2.BeTreeRelation(name=relation_id1069, relation_info=betree_info1070)
        result1072 = _t1788
        self.record_span(span_start1071, "BeTreeRelation")
        return result1072

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1076 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1789 = self.parse_betree_info_key_types()
        betree_info_key_types1073 = _t1789
        _t1790 = self.parse_betree_info_value_types()
        betree_info_value_types1074 = _t1790
        _t1791 = self.parse_config_dict()
        config_dict1075 = _t1791
        self.consume_literal(")")
        _t1792 = self.construct_betree_info(betree_info_key_types1073, betree_info_value_types1074, config_dict1075)
        result1077 = _t1792
        self.record_span(span_start1076, "BeTreeInfo")
        return result1077

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1078 = []
        cond1079 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1079:
            _t1793 = self.parse_type()
            item1080 = _t1793
            xs1078.append(item1080)
            cond1079 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1081 = xs1078
        self.consume_literal(")")
        return types1081

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1082 = []
        cond1083 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1083:
            _t1794 = self.parse_type()
            item1084 = _t1794
            xs1082.append(item1084)
            cond1083 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1085 = xs1082
        self.consume_literal(")")
        return types1085

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1090 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1795 = self.parse_csvlocator()
        csvlocator1086 = _t1795
        _t1796 = self.parse_csv_config()
        csv_config1087 = _t1796
        _t1797 = self.parse_gnf_columns()
        gnf_columns1088 = _t1797
        _t1798 = self.parse_csv_asof()
        csv_asof1089 = _t1798
        self.consume_literal(")")
        _t1799 = logic_pb2.CSVData(locator=csvlocator1086, config=csv_config1087, columns=gnf_columns1088, asof=csv_asof1089)
        result1091 = _t1799
        self.record_span(span_start1090, "CSVData")
        return result1091

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1094 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1801 = self.parse_csv_locator_paths()
            _t1800 = _t1801
        else:
            _t1800 = None
        csv_locator_paths1092 = _t1800
        if self.match_lookahead_literal("(", 0):
            _t1803 = self.parse_csv_locator_inline_data()
            _t1802 = _t1803
        else:
            _t1802 = None
        csv_locator_inline_data1093 = _t1802
        self.consume_literal(")")
        _t1804 = logic_pb2.CSVLocator(paths=(csv_locator_paths1092 if csv_locator_paths1092 is not None else []), inline_data=(csv_locator_inline_data1093 if csv_locator_inline_data1093 is not None else "").encode())
        result1095 = _t1804
        self.record_span(span_start1094, "CSVLocator")
        return result1095

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1096 = []
        cond1097 = self.match_lookahead_terminal("STRING", 0)
        while cond1097:
            item1098 = self.consume_terminal("STRING")
            xs1096.append(item1098)
            cond1097 = self.match_lookahead_terminal("STRING", 0)
        strings1099 = xs1096
        self.consume_literal(")")
        return strings1099

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1100 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1100

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1102 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1805 = self.parse_config_dict()
        config_dict1101 = _t1805
        self.consume_literal(")")
        _t1806 = self.construct_csv_config(config_dict1101)
        result1103 = _t1806
        self.record_span(span_start1102, "CSVConfig")
        return result1103

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1104 = []
        cond1105 = self.match_lookahead_literal("(", 0)
        while cond1105:
            _t1807 = self.parse_gnf_column()
            item1106 = _t1807
            xs1104.append(item1106)
            cond1105 = self.match_lookahead_literal("(", 0)
        gnf_columns1107 = xs1104
        self.consume_literal(")")
        return gnf_columns1107

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1114 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1808 = self.parse_gnf_column_path()
        gnf_column_path1108 = _t1808
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1810 = self.parse_relation_id()
            _t1809 = _t1810
        else:
            _t1809 = None
        relation_id1109 = _t1809
        self.consume_literal("[")
        xs1110 = []
        cond1111 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1111:
            _t1811 = self.parse_type()
            item1112 = _t1811
            xs1110.append(item1112)
            cond1111 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1113 = xs1110
        self.consume_literal("]")
        self.consume_literal(")")
        _t1812 = logic_pb2.GNFColumn(column_path=gnf_column_path1108, target_id=relation_id1109, types=types1113)
        result1115 = _t1812
        self.record_span(span_start1114, "GNFColumn")
        return result1115

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1813 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1814 = 0
            else:
                _t1814 = -1
            _t1813 = _t1814
        prediction1116 = _t1813
        if prediction1116 == 1:
            self.consume_literal("[")
            xs1118 = []
            cond1119 = self.match_lookahead_terminal("STRING", 0)
            while cond1119:
                item1120 = self.consume_terminal("STRING")
                xs1118.append(item1120)
                cond1119 = self.match_lookahead_terminal("STRING", 0)
            strings1121 = xs1118
            self.consume_literal("]")
            _t1815 = strings1121
        else:
            if prediction1116 == 0:
                string1117 = self.consume_terminal("STRING")
                _t1816 = [string1117]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1815 = _t1816
        return _t1815

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1122 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1122

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1124 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1817 = self.parse_fragment_id()
        fragment_id1123 = _t1817
        self.consume_literal(")")
        _t1818 = transactions_pb2.Undefine(fragment_id=fragment_id1123)
        result1125 = _t1818
        self.record_span(span_start1124, "Undefine")
        return result1125

    def parse_context(self) -> transactions_pb2.Context:
        span_start1130 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1126 = []
        cond1127 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1127:
            _t1819 = self.parse_relation_id()
            item1128 = _t1819
            xs1126.append(item1128)
            cond1127 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1129 = xs1126
        self.consume_literal(")")
        _t1820 = transactions_pb2.Context(relations=relation_ids1129)
        result1131 = _t1820
        self.record_span(span_start1130, "Context")
        return result1131

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1136 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1132 = []
        cond1133 = self.match_lookahead_literal("[", 0)
        while cond1133:
            _t1821 = self.parse_snapshot_mapping()
            item1134 = _t1821
            xs1132.append(item1134)
            cond1133 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1135 = xs1132
        self.consume_literal(")")
        _t1822 = transactions_pb2.Snapshot(mappings=snapshot_mappings1135)
        result1137 = _t1822
        self.record_span(span_start1136, "Snapshot")
        return result1137

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1140 = self.span_start()
        _t1823 = self.parse_edb_path()
        edb_path1138 = _t1823
        _t1824 = self.parse_relation_id()
        relation_id1139 = _t1824
        _t1825 = transactions_pb2.SnapshotMapping(destination_path=edb_path1138, source_relation=relation_id1139)
        result1141 = _t1825
        self.record_span(span_start1140, "SnapshotMapping")
        return result1141

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1142 = []
        cond1143 = self.match_lookahead_literal("(", 0)
        while cond1143:
            _t1826 = self.parse_read()
            item1144 = _t1826
            xs1142.append(item1144)
            cond1143 = self.match_lookahead_literal("(", 0)
        reads1145 = xs1142
        self.consume_literal(")")
        return reads1145

    def parse_read(self) -> transactions_pb2.Read:
        span_start1152 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1828 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1829 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1830 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1831 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1832 = 3
                            else:
                                _t1832 = -1
                            _t1831 = _t1832
                        _t1830 = _t1831
                    _t1829 = _t1830
                _t1828 = _t1829
            _t1827 = _t1828
        else:
            _t1827 = -1
        prediction1146 = _t1827
        if prediction1146 == 4:
            _t1834 = self.parse_export()
            export1151 = _t1834
            _t1835 = transactions_pb2.Read(export=export1151)
            _t1833 = _t1835
        else:
            if prediction1146 == 3:
                _t1837 = self.parse_abort()
                abort1150 = _t1837
                _t1838 = transactions_pb2.Read(abort=abort1150)
                _t1836 = _t1838
            else:
                if prediction1146 == 2:
                    _t1840 = self.parse_what_if()
                    what_if1149 = _t1840
                    _t1841 = transactions_pb2.Read(what_if=what_if1149)
                    _t1839 = _t1841
                else:
                    if prediction1146 == 1:
                        _t1843 = self.parse_output()
                        output1148 = _t1843
                        _t1844 = transactions_pb2.Read(output=output1148)
                        _t1842 = _t1844
                    else:
                        if prediction1146 == 0:
                            _t1846 = self.parse_demand()
                            demand1147 = _t1846
                            _t1847 = transactions_pb2.Read(demand=demand1147)
                            _t1845 = _t1847
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1842 = _t1845
                    _t1839 = _t1842
                _t1836 = _t1839
            _t1833 = _t1836
        result1153 = _t1833
        self.record_span(span_start1152, "Read")
        return result1153

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1155 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1848 = self.parse_relation_id()
        relation_id1154 = _t1848
        self.consume_literal(")")
        _t1849 = transactions_pb2.Demand(relation_id=relation_id1154)
        result1156 = _t1849
        self.record_span(span_start1155, "Demand")
        return result1156

    def parse_output(self) -> transactions_pb2.Output:
        span_start1159 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t1850 = self.parse_name()
        name1157 = _t1850
        _t1851 = self.parse_relation_id()
        relation_id1158 = _t1851
        self.consume_literal(")")
        _t1852 = transactions_pb2.Output(name=name1157, relation_id=relation_id1158)
        result1160 = _t1852
        self.record_span(span_start1159, "Output")
        return result1160

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1163 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1853 = self.parse_name()
        name1161 = _t1853
        _t1854 = self.parse_epoch()
        epoch1162 = _t1854
        self.consume_literal(")")
        _t1855 = transactions_pb2.WhatIf(branch=name1161, epoch=epoch1162)
        result1164 = _t1855
        self.record_span(span_start1163, "WhatIf")
        return result1164

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1167 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1857 = self.parse_name()
            _t1856 = _t1857
        else:
            _t1856 = None
        name1165 = _t1856
        _t1858 = self.parse_relation_id()
        relation_id1166 = _t1858
        self.consume_literal(")")
        _t1859 = transactions_pb2.Abort(name=(name1165 if name1165 is not None else "abort"), relation_id=relation_id1166)
        result1168 = _t1859
        self.record_span(span_start1167, "Abort")
        return result1168

    def parse_export(self) -> transactions_pb2.Export:
        span_start1170 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export")
        _t1860 = self.parse_export_csv_config()
        export_csv_config1169 = _t1860
        self.consume_literal(")")
        _t1861 = transactions_pb2.Export(csv_config=export_csv_config1169)
        result1171 = _t1861
        self.record_span(span_start1170, "Export")
        return result1171

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1179 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t1863 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t1864 = 1
                else:
                    _t1864 = -1
                _t1863 = _t1864
            _t1862 = _t1863
        else:
            _t1862 = -1
        prediction1172 = _t1862
        if prediction1172 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t1866 = self.parse_export_csv_path()
            export_csv_path1176 = _t1866
            _t1867 = self.parse_export_csv_columns_list()
            export_csv_columns_list1177 = _t1867
            _t1868 = self.parse_config_dict()
            config_dict1178 = _t1868
            self.consume_literal(")")
            _t1869 = self.construct_export_csv_config(export_csv_path1176, export_csv_columns_list1177, config_dict1178)
            _t1865 = _t1869
        else:
            if prediction1172 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t1871 = self.parse_export_csv_path()
                export_csv_path1173 = _t1871
                _t1872 = self.parse_export_csv_source()
                export_csv_source1174 = _t1872
                _t1873 = self.parse_csv_config()
                csv_config1175 = _t1873
                self.consume_literal(")")
                _t1874 = self.construct_export_csv_config_with_source(export_csv_path1173, export_csv_source1174, csv_config1175)
                _t1870 = _t1874
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1865 = _t1870
        result1180 = _t1865
        self.record_span(span_start1179, "ExportCSVConfig")
        return result1180

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1181 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1181

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1188 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t1876 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t1877 = 0
                else:
                    _t1877 = -1
                _t1876 = _t1877
            _t1875 = _t1876
        else:
            _t1875 = -1
        prediction1182 = _t1875
        if prediction1182 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t1879 = self.parse_relation_id()
            relation_id1187 = _t1879
            self.consume_literal(")")
            _t1880 = transactions_pb2.ExportCSVSource(table_def=relation_id1187)
            _t1878 = _t1880
        else:
            if prediction1182 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1183 = []
                cond1184 = self.match_lookahead_literal("(", 0)
                while cond1184:
                    _t1882 = self.parse_export_csv_column()
                    item1185 = _t1882
                    xs1183.append(item1185)
                    cond1184 = self.match_lookahead_literal("(", 0)
                export_csv_columns1186 = xs1183
                self.consume_literal(")")
                _t1883 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1186)
                _t1884 = transactions_pb2.ExportCSVSource(gnf_columns=_t1883)
                _t1881 = _t1884
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1878 = _t1881
        result1189 = _t1878
        self.record_span(span_start1188, "ExportCSVSource")
        return result1189

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1192 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1190 = self.consume_terminal("STRING")
        _t1885 = self.parse_relation_id()
        relation_id1191 = _t1885
        self.consume_literal(")")
        _t1886 = transactions_pb2.ExportCSVColumn(column_name=string1190, column_data=relation_id1191)
        result1193 = _t1886
        self.record_span(span_start1192, "ExportCSVColumn")
        return result1193

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1194 = []
        cond1195 = self.match_lookahead_literal("(", 0)
        while cond1195:
            _t1887 = self.parse_export_csv_column()
            item1196 = _t1887
            xs1194.append(item1196)
            cond1195 = self.match_lookahead_literal("(", 0)
        export_csv_columns1197 = xs1194
        self.consume_literal(")")
        return export_csv_columns1197


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
