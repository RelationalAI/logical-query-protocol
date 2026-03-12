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
            _t1902 = value.HasField("int32_value")
        else:
            _t1902 = False
        if _t1902:
            assert value is not None
            return value.int32_value
        else:
            _t1903 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t1904 = value.HasField("int_value")
        else:
            _t1904 = False
        if _t1904:
            assert value is not None
            return value.int_value
        else:
            _t1905 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t1906 = value.HasField("string_value")
        else:
            _t1906 = False
        if _t1906:
            assert value is not None
            return value.string_value
        else:
            _t1907 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1908 = value.HasField("boolean_value")
        else:
            _t1908 = False
        if _t1908:
            assert value is not None
            return value.boolean_value
        else:
            _t1909 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1910 = value.HasField("string_value")
        else:
            _t1910 = False
        if _t1910:
            assert value is not None
            return [value.string_value]
        else:
            _t1911 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t1912 = value.HasField("int_value")
        else:
            _t1912 = False
        if _t1912:
            assert value is not None
            return value.int_value
        else:
            _t1913 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t1914 = value.HasField("float_value")
        else:
            _t1914 = False
        if _t1914:
            assert value is not None
            return value.float_value
        else:
            _t1915 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t1916 = value.HasField("string_value")
        else:
            _t1916 = False
        if _t1916:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1917 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t1918 = value.HasField("uint128_value")
        else:
            _t1918 = False
        if _t1918:
            assert value is not None
            return value.uint128_value
        else:
            _t1919 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1920 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1920
        _t1921 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1921
        _t1922 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1922
        _t1923 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1923
        _t1924 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1924
        _t1925 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1925
        _t1926 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1926
        _t1927 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1927
        _t1928 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1928
        _t1929 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1929
        _t1930 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1930
        _t1931 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t1931
        _t1932 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t1932

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1933 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1933
        _t1934 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1934
        _t1935 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1935
        _t1936 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1936
        _t1937 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1937
        _t1938 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1938
        _t1939 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1939
        _t1940 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1940
        _t1941 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1941
        _t1942 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1942
        _t1943 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1943

    def default_configure(self) -> transactions_pb2.Configure:
        _t1944 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1944
        _t1945 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1945

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
        _t1946 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1946
        _t1947 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1947
        _t1948 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1948

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1949 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1949
        _t1950 = self._extract_value_string(config.get("compression"), "")
        compression = _t1950
        _t1951 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1951
        _t1952 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1952
        _t1953 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1953
        _t1954 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1954
        _t1955 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1955
        _t1956 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1956

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t1957 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t1957

    def construct_iceberg_config(self, catalog_uri: str, scope: str | None, properties: Sequence[tuple[str, str]] | None, credentials: Sequence[tuple[str, str]] | None) -> logic_pb2.IcebergConfig:
        props = dict((properties if properties is not None else []))
        creds = dict((credentials if credentials is not None else []))
        _t1958 = logic_pb2.IcebergConfig(catalog_uri=catalog_uri, scope=(scope if scope is not None else ""), properties=props, credentials=creds)
        return _t1958

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start618 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1225 = self.parse_configure()
            _t1224 = _t1225
        else:
            _t1224 = None
        configure612 = _t1224
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1227 = self.parse_sync()
            _t1226 = _t1227
        else:
            _t1226 = None
        sync613 = _t1226
        xs614 = []
        cond615 = self.match_lookahead_literal("(", 0)
        while cond615:
            _t1228 = self.parse_epoch()
            item616 = _t1228
            xs614.append(item616)
            cond615 = self.match_lookahead_literal("(", 0)
        epochs617 = xs614
        self.consume_literal(")")
        _t1229 = self.default_configure()
        _t1230 = transactions_pb2.Transaction(epochs=epochs617, configure=(configure612 if configure612 is not None else _t1229), sync=sync613)
        result619 = _t1230
        self.record_span(span_start618, "Transaction")
        return result619

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start621 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1231 = self.parse_config_dict()
        config_dict620 = _t1231
        self.consume_literal(")")
        _t1232 = self.construct_configure(config_dict620)
        result622 = _t1232
        self.record_span(span_start621, "Configure")
        return result622

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs623 = []
        cond624 = self.match_lookahead_literal(":", 0)
        while cond624:
            _t1233 = self.parse_config_key_value()
            item625 = _t1233
            xs623.append(item625)
            cond624 = self.match_lookahead_literal(":", 0)
        config_key_values626 = xs623
        self.consume_literal("}")
        return config_key_values626

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol627 = self.consume_terminal("SYMBOL")
        _t1234 = self.parse_value()
        value628 = _t1234
        return (symbol627, value628,)

    def parse_value(self) -> logic_pb2.Value:
        span_start642 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1235 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1236 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1237 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1239 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1240 = 0
                            else:
                                _t1240 = -1
                            _t1239 = _t1240
                        _t1238 = _t1239
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1241 = 12
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1242 = 5
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1243 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1244 = 10
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1245 = 6
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1246 = 3
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1247 = 11
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1248 = 4
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1249 = 7
                                                        else:
                                                            _t1249 = -1
                                                        _t1248 = _t1249
                                                    _t1247 = _t1248
                                                _t1246 = _t1247
                                            _t1245 = _t1246
                                        _t1244 = _t1245
                                    _t1243 = _t1244
                                _t1242 = _t1243
                            _t1241 = _t1242
                        _t1238 = _t1241
                    _t1237 = _t1238
                _t1236 = _t1237
            _t1235 = _t1236
        prediction629 = _t1235
        if prediction629 == 12:
            uint32641 = self.consume_terminal("UINT32")
            _t1251 = logic_pb2.Value(uint32_value=uint32641)
            _t1250 = _t1251
        else:
            if prediction629 == 11:
                float32640 = self.consume_terminal("FLOAT32")
                _t1253 = logic_pb2.Value(float32_value=float32640)
                _t1252 = _t1253
            else:
                if prediction629 == 10:
                    int32639 = self.consume_terminal("INT32")
                    _t1255 = logic_pb2.Value(int32_value=int32639)
                    _t1254 = _t1255
                else:
                    if prediction629 == 9:
                        _t1257 = self.parse_boolean_value()
                        boolean_value638 = _t1257
                        _t1258 = logic_pb2.Value(boolean_value=boolean_value638)
                        _t1256 = _t1258
                    else:
                        if prediction629 == 8:
                            self.consume_literal("missing")
                            _t1260 = logic_pb2.MissingValue()
                            _t1261 = logic_pb2.Value(missing_value=_t1260)
                            _t1259 = _t1261
                        else:
                            if prediction629 == 7:
                                decimal637 = self.consume_terminal("DECIMAL")
                                _t1263 = logic_pb2.Value(decimal_value=decimal637)
                                _t1262 = _t1263
                            else:
                                if prediction629 == 6:
                                    int128636 = self.consume_terminal("INT128")
                                    _t1265 = logic_pb2.Value(int128_value=int128636)
                                    _t1264 = _t1265
                                else:
                                    if prediction629 == 5:
                                        uint128635 = self.consume_terminal("UINT128")
                                        _t1267 = logic_pb2.Value(uint128_value=uint128635)
                                        _t1266 = _t1267
                                    else:
                                        if prediction629 == 4:
                                            float634 = self.consume_terminal("FLOAT")
                                            _t1269 = logic_pb2.Value(float_value=float634)
                                            _t1268 = _t1269
                                        else:
                                            if prediction629 == 3:
                                                int633 = self.consume_terminal("INT")
                                                _t1271 = logic_pb2.Value(int_value=int633)
                                                _t1270 = _t1271
                                            else:
                                                if prediction629 == 2:
                                                    string632 = self.consume_terminal("STRING")
                                                    _t1273 = logic_pb2.Value(string_value=string632)
                                                    _t1272 = _t1273
                                                else:
                                                    if prediction629 == 1:
                                                        _t1275 = self.parse_datetime()
                                                        datetime631 = _t1275
                                                        _t1276 = logic_pb2.Value(datetime_value=datetime631)
                                                        _t1274 = _t1276
                                                    else:
                                                        if prediction629 == 0:
                                                            _t1278 = self.parse_date()
                                                            date630 = _t1278
                                                            _t1279 = logic_pb2.Value(date_value=date630)
                                                            _t1277 = _t1279
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1274 = _t1277
                                                    _t1272 = _t1274
                                                _t1270 = _t1272
                                            _t1268 = _t1270
                                        _t1266 = _t1268
                                    _t1264 = _t1266
                                _t1262 = _t1264
                            _t1259 = _t1262
                        _t1256 = _t1259
                    _t1254 = _t1256
                _t1252 = _t1254
            _t1250 = _t1252
        result643 = _t1250
        self.record_span(span_start642, "Value")
        return result643

    def parse_date(self) -> logic_pb2.DateValue:
        span_start647 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int644 = self.consume_terminal("INT")
        int_3645 = self.consume_terminal("INT")
        int_4646 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1280 = logic_pb2.DateValue(year=int(int644), month=int(int_3645), day=int(int_4646))
        result648 = _t1280
        self.record_span(span_start647, "DateValue")
        return result648

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start656 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int649 = self.consume_terminal("INT")
        int_3650 = self.consume_terminal("INT")
        int_4651 = self.consume_terminal("INT")
        int_5652 = self.consume_terminal("INT")
        int_6653 = self.consume_terminal("INT")
        int_7654 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1281 = self.consume_terminal("INT")
        else:
            _t1281 = None
        int_8655 = _t1281
        self.consume_literal(")")
        _t1282 = logic_pb2.DateTimeValue(year=int(int649), month=int(int_3650), day=int(int_4651), hour=int(int_5652), minute=int(int_6653), second=int(int_7654), microsecond=int((int_8655 if int_8655 is not None else 0)))
        result657 = _t1282
        self.record_span(span_start656, "DateTimeValue")
        return result657

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1283 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1284 = 1
            else:
                _t1284 = -1
            _t1283 = _t1284
        prediction658 = _t1283
        if prediction658 == 1:
            self.consume_literal("false")
            _t1285 = False
        else:
            if prediction658 == 0:
                self.consume_literal("true")
                _t1286 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1285 = _t1286
        return _t1285

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start663 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs659 = []
        cond660 = self.match_lookahead_literal(":", 0)
        while cond660:
            _t1287 = self.parse_fragment_id()
            item661 = _t1287
            xs659.append(item661)
            cond660 = self.match_lookahead_literal(":", 0)
        fragment_ids662 = xs659
        self.consume_literal(")")
        _t1288 = transactions_pb2.Sync(fragments=fragment_ids662)
        result664 = _t1288
        self.record_span(span_start663, "Sync")
        return result664

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start666 = self.span_start()
        self.consume_literal(":")
        symbol665 = self.consume_terminal("SYMBOL")
        result667 = fragments_pb2.FragmentId(id=symbol665.encode())
        self.record_span(span_start666, "FragmentId")
        return result667

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start670 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1290 = self.parse_epoch_writes()
            _t1289 = _t1290
        else:
            _t1289 = None
        epoch_writes668 = _t1289
        if self.match_lookahead_literal("(", 0):
            _t1292 = self.parse_epoch_reads()
            _t1291 = _t1292
        else:
            _t1291 = None
        epoch_reads669 = _t1291
        self.consume_literal(")")
        _t1293 = transactions_pb2.Epoch(writes=(epoch_writes668 if epoch_writes668 is not None else []), reads=(epoch_reads669 if epoch_reads669 is not None else []))
        result671 = _t1293
        self.record_span(span_start670, "Epoch")
        return result671

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs672 = []
        cond673 = self.match_lookahead_literal("(", 0)
        while cond673:
            _t1294 = self.parse_write()
            item674 = _t1294
            xs672.append(item674)
            cond673 = self.match_lookahead_literal("(", 0)
        writes675 = xs672
        self.consume_literal(")")
        return writes675

    def parse_write(self) -> transactions_pb2.Write:
        span_start681 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1296 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1297 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1298 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1299 = 2
                        else:
                            _t1299 = -1
                        _t1298 = _t1299
                    _t1297 = _t1298
                _t1296 = _t1297
            _t1295 = _t1296
        else:
            _t1295 = -1
        prediction676 = _t1295
        if prediction676 == 3:
            _t1301 = self.parse_snapshot()
            snapshot680 = _t1301
            _t1302 = transactions_pb2.Write(snapshot=snapshot680)
            _t1300 = _t1302
        else:
            if prediction676 == 2:
                _t1304 = self.parse_context()
                context679 = _t1304
                _t1305 = transactions_pb2.Write(context=context679)
                _t1303 = _t1305
            else:
                if prediction676 == 1:
                    _t1307 = self.parse_undefine()
                    undefine678 = _t1307
                    _t1308 = transactions_pb2.Write(undefine=undefine678)
                    _t1306 = _t1308
                else:
                    if prediction676 == 0:
                        _t1310 = self.parse_define()
                        define677 = _t1310
                        _t1311 = transactions_pb2.Write(define=define677)
                        _t1309 = _t1311
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1306 = _t1309
                _t1303 = _t1306
            _t1300 = _t1303
        result682 = _t1300
        self.record_span(span_start681, "Write")
        return result682

    def parse_define(self) -> transactions_pb2.Define:
        span_start684 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1312 = self.parse_fragment()
        fragment683 = _t1312
        self.consume_literal(")")
        _t1313 = transactions_pb2.Define(fragment=fragment683)
        result685 = _t1313
        self.record_span(span_start684, "Define")
        return result685

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start691 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1314 = self.parse_new_fragment_id()
        new_fragment_id686 = _t1314
        xs687 = []
        cond688 = self.match_lookahead_literal("(", 0)
        while cond688:
            _t1315 = self.parse_declaration()
            item689 = _t1315
            xs687.append(item689)
            cond688 = self.match_lookahead_literal("(", 0)
        declarations690 = xs687
        self.consume_literal(")")
        result692 = self.construct_fragment(new_fragment_id686, declarations690)
        self.record_span(span_start691, "Fragment")
        return result692

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start694 = self.span_start()
        _t1316 = self.parse_fragment_id()
        fragment_id693 = _t1316
        self.start_fragment(fragment_id693)
        result695 = fragment_id693
        self.record_span(span_start694, "FragmentId")
        return result695

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start701 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1318 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1319 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1320 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1321 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1322 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1323 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1324 = 1
                                    else:
                                        _t1324 = -1
                                    _t1323 = _t1324
                                _t1322 = _t1323
                            _t1321 = _t1322
                        _t1320 = _t1321
                    _t1319 = _t1320
                _t1318 = _t1319
            _t1317 = _t1318
        else:
            _t1317 = -1
        prediction696 = _t1317
        if prediction696 == 3:
            _t1326 = self.parse_data()
            data700 = _t1326
            _t1327 = logic_pb2.Declaration(data=data700)
            _t1325 = _t1327
        else:
            if prediction696 == 2:
                _t1329 = self.parse_constraint()
                constraint699 = _t1329
                _t1330 = logic_pb2.Declaration(constraint=constraint699)
                _t1328 = _t1330
            else:
                if prediction696 == 1:
                    _t1332 = self.parse_algorithm()
                    algorithm698 = _t1332
                    _t1333 = logic_pb2.Declaration(algorithm=algorithm698)
                    _t1331 = _t1333
                else:
                    if prediction696 == 0:
                        _t1335 = self.parse_def()
                        def697 = _t1335
                        _t1336 = logic_pb2.Declaration()
                        getattr(_t1336, 'def').CopyFrom(def697)
                        _t1334 = _t1336
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1331 = _t1334
                _t1328 = _t1331
            _t1325 = _t1328
        result702 = _t1325
        self.record_span(span_start701, "Declaration")
        return result702

    def parse_def(self) -> logic_pb2.Def:
        span_start706 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1337 = self.parse_relation_id()
        relation_id703 = _t1337
        _t1338 = self.parse_abstraction()
        abstraction704 = _t1338
        if self.match_lookahead_literal("(", 0):
            _t1340 = self.parse_attrs()
            _t1339 = _t1340
        else:
            _t1339 = None
        attrs705 = _t1339
        self.consume_literal(")")
        _t1341 = logic_pb2.Def(name=relation_id703, body=abstraction704, attrs=(attrs705 if attrs705 is not None else []))
        result707 = _t1341
        self.record_span(span_start706, "Def")
        return result707

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start711 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1342 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1343 = 1
            else:
                _t1343 = -1
            _t1342 = _t1343
        prediction708 = _t1342
        if prediction708 == 1:
            uint128710 = self.consume_terminal("UINT128")
            _t1344 = logic_pb2.RelationId(id_low=uint128710.low, id_high=uint128710.high)
        else:
            if prediction708 == 0:
                self.consume_literal(":")
                symbol709 = self.consume_terminal("SYMBOL")
                _t1345 = self.relation_id_from_string(symbol709)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1344 = _t1345
        result712 = _t1344
        self.record_span(span_start711, "RelationId")
        return result712

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start715 = self.span_start()
        self.consume_literal("(")
        _t1346 = self.parse_bindings()
        bindings713 = _t1346
        _t1347 = self.parse_formula()
        formula714 = _t1347
        self.consume_literal(")")
        _t1348 = logic_pb2.Abstraction(vars=(list(bindings713[0]) + list(bindings713[1] if bindings713[1] is not None else [])), value=formula714)
        result716 = _t1348
        self.record_span(span_start715, "Abstraction")
        return result716

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs717 = []
        cond718 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond718:
            _t1349 = self.parse_binding()
            item719 = _t1349
            xs717.append(item719)
            cond718 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings720 = xs717
        if self.match_lookahead_literal("|", 0):
            _t1351 = self.parse_value_bindings()
            _t1350 = _t1351
        else:
            _t1350 = None
        value_bindings721 = _t1350
        self.consume_literal("]")
        return (bindings720, (value_bindings721 if value_bindings721 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start724 = self.span_start()
        symbol722 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1352 = self.parse_type()
        type723 = _t1352
        _t1353 = logic_pb2.Var(name=symbol722)
        _t1354 = logic_pb2.Binding(var=_t1353, type=type723)
        result725 = _t1354
        self.record_span(span_start724, "Binding")
        return result725

    def parse_type(self) -> logic_pb2.Type:
        span_start741 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1355 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1356 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1357 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1358 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1359 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1360 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1361 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1362 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1363 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1364 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1365 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1366 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1367 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1368 = 9
                                                            else:
                                                                _t1368 = -1
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
                _t1356 = _t1357
            _t1355 = _t1356
        prediction726 = _t1355
        if prediction726 == 13:
            _t1370 = self.parse_uint32_type()
            uint32_type740 = _t1370
            _t1371 = logic_pb2.Type(uint32_type=uint32_type740)
            _t1369 = _t1371
        else:
            if prediction726 == 12:
                _t1373 = self.parse_float32_type()
                float32_type739 = _t1373
                _t1374 = logic_pb2.Type(float32_type=float32_type739)
                _t1372 = _t1374
            else:
                if prediction726 == 11:
                    _t1376 = self.parse_int32_type()
                    int32_type738 = _t1376
                    _t1377 = logic_pb2.Type(int32_type=int32_type738)
                    _t1375 = _t1377
                else:
                    if prediction726 == 10:
                        _t1379 = self.parse_boolean_type()
                        boolean_type737 = _t1379
                        _t1380 = logic_pb2.Type(boolean_type=boolean_type737)
                        _t1378 = _t1380
                    else:
                        if prediction726 == 9:
                            _t1382 = self.parse_decimal_type()
                            decimal_type736 = _t1382
                            _t1383 = logic_pb2.Type(decimal_type=decimal_type736)
                            _t1381 = _t1383
                        else:
                            if prediction726 == 8:
                                _t1385 = self.parse_missing_type()
                                missing_type735 = _t1385
                                _t1386 = logic_pb2.Type(missing_type=missing_type735)
                                _t1384 = _t1386
                            else:
                                if prediction726 == 7:
                                    _t1388 = self.parse_datetime_type()
                                    datetime_type734 = _t1388
                                    _t1389 = logic_pb2.Type(datetime_type=datetime_type734)
                                    _t1387 = _t1389
                                else:
                                    if prediction726 == 6:
                                        _t1391 = self.parse_date_type()
                                        date_type733 = _t1391
                                        _t1392 = logic_pb2.Type(date_type=date_type733)
                                        _t1390 = _t1392
                                    else:
                                        if prediction726 == 5:
                                            _t1394 = self.parse_int128_type()
                                            int128_type732 = _t1394
                                            _t1395 = logic_pb2.Type(int128_type=int128_type732)
                                            _t1393 = _t1395
                                        else:
                                            if prediction726 == 4:
                                                _t1397 = self.parse_uint128_type()
                                                uint128_type731 = _t1397
                                                _t1398 = logic_pb2.Type(uint128_type=uint128_type731)
                                                _t1396 = _t1398
                                            else:
                                                if prediction726 == 3:
                                                    _t1400 = self.parse_float_type()
                                                    float_type730 = _t1400
                                                    _t1401 = logic_pb2.Type(float_type=float_type730)
                                                    _t1399 = _t1401
                                                else:
                                                    if prediction726 == 2:
                                                        _t1403 = self.parse_int_type()
                                                        int_type729 = _t1403
                                                        _t1404 = logic_pb2.Type(int_type=int_type729)
                                                        _t1402 = _t1404
                                                    else:
                                                        if prediction726 == 1:
                                                            _t1406 = self.parse_string_type()
                                                            string_type728 = _t1406
                                                            _t1407 = logic_pb2.Type(string_type=string_type728)
                                                            _t1405 = _t1407
                                                        else:
                                                            if prediction726 == 0:
                                                                _t1409 = self.parse_unspecified_type()
                                                                unspecified_type727 = _t1409
                                                                _t1410 = logic_pb2.Type(unspecified_type=unspecified_type727)
                                                                _t1408 = _t1410
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1405 = _t1408
                                                        _t1402 = _t1405
                                                    _t1399 = _t1402
                                                _t1396 = _t1399
                                            _t1393 = _t1396
                                        _t1390 = _t1393
                                    _t1387 = _t1390
                                _t1384 = _t1387
                            _t1381 = _t1384
                        _t1378 = _t1381
                    _t1375 = _t1378
                _t1372 = _t1375
            _t1369 = _t1372
        result742 = _t1369
        self.record_span(span_start741, "Type")
        return result742

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start743 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1411 = logic_pb2.UnspecifiedType()
        result744 = _t1411
        self.record_span(span_start743, "UnspecifiedType")
        return result744

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start745 = self.span_start()
        self.consume_literal("STRING")
        _t1412 = logic_pb2.StringType()
        result746 = _t1412
        self.record_span(span_start745, "StringType")
        return result746

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start747 = self.span_start()
        self.consume_literal("INT")
        _t1413 = logic_pb2.IntType()
        result748 = _t1413
        self.record_span(span_start747, "IntType")
        return result748

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start749 = self.span_start()
        self.consume_literal("FLOAT")
        _t1414 = logic_pb2.FloatType()
        result750 = _t1414
        self.record_span(span_start749, "FloatType")
        return result750

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start751 = self.span_start()
        self.consume_literal("UINT128")
        _t1415 = logic_pb2.UInt128Type()
        result752 = _t1415
        self.record_span(span_start751, "UInt128Type")
        return result752

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start753 = self.span_start()
        self.consume_literal("INT128")
        _t1416 = logic_pb2.Int128Type()
        result754 = _t1416
        self.record_span(span_start753, "Int128Type")
        return result754

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start755 = self.span_start()
        self.consume_literal("DATE")
        _t1417 = logic_pb2.DateType()
        result756 = _t1417
        self.record_span(span_start755, "DateType")
        return result756

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start757 = self.span_start()
        self.consume_literal("DATETIME")
        _t1418 = logic_pb2.DateTimeType()
        result758 = _t1418
        self.record_span(span_start757, "DateTimeType")
        return result758

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start759 = self.span_start()
        self.consume_literal("MISSING")
        _t1419 = logic_pb2.MissingType()
        result760 = _t1419
        self.record_span(span_start759, "MissingType")
        return result760

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start763 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int761 = self.consume_terminal("INT")
        int_3762 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1420 = logic_pb2.DecimalType(precision=int(int761), scale=int(int_3762))
        result764 = _t1420
        self.record_span(span_start763, "DecimalType")
        return result764

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start765 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1421 = logic_pb2.BooleanType()
        result766 = _t1421
        self.record_span(span_start765, "BooleanType")
        return result766

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start767 = self.span_start()
        self.consume_literal("INT32")
        _t1422 = logic_pb2.Int32Type()
        result768 = _t1422
        self.record_span(span_start767, "Int32Type")
        return result768

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start769 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1423 = logic_pb2.Float32Type()
        result770 = _t1423
        self.record_span(span_start769, "Float32Type")
        return result770

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start771 = self.span_start()
        self.consume_literal("UINT32")
        _t1424 = logic_pb2.UInt32Type()
        result772 = _t1424
        self.record_span(span_start771, "UInt32Type")
        return result772

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs773 = []
        cond774 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond774:
            _t1425 = self.parse_binding()
            item775 = _t1425
            xs773.append(item775)
            cond774 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings776 = xs773
        return bindings776

    def parse_formula(self) -> logic_pb2.Formula:
        span_start791 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1427 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1428 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1429 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1430 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1431 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1432 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1433 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1434 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1435 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1436 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1437 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1438 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1439 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1440 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1441 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1442 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1443 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1444 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1445 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1446 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1447 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1448 = 10
                                                                                                else:
                                                                                                    _t1448 = -1
                                                                                                _t1447 = _t1448
                                                                                            _t1446 = _t1447
                                                                                        _t1445 = _t1446
                                                                                    _t1444 = _t1445
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
                                        _t1433 = _t1434
                                    _t1432 = _t1433
                                _t1431 = _t1432
                            _t1430 = _t1431
                        _t1429 = _t1430
                    _t1428 = _t1429
                _t1427 = _t1428
            _t1426 = _t1427
        else:
            _t1426 = -1
        prediction777 = _t1426
        if prediction777 == 12:
            _t1450 = self.parse_cast()
            cast790 = _t1450
            _t1451 = logic_pb2.Formula(cast=cast790)
            _t1449 = _t1451
        else:
            if prediction777 == 11:
                _t1453 = self.parse_rel_atom()
                rel_atom789 = _t1453
                _t1454 = logic_pb2.Formula(rel_atom=rel_atom789)
                _t1452 = _t1454
            else:
                if prediction777 == 10:
                    _t1456 = self.parse_primitive()
                    primitive788 = _t1456
                    _t1457 = logic_pb2.Formula(primitive=primitive788)
                    _t1455 = _t1457
                else:
                    if prediction777 == 9:
                        _t1459 = self.parse_pragma()
                        pragma787 = _t1459
                        _t1460 = logic_pb2.Formula(pragma=pragma787)
                        _t1458 = _t1460
                    else:
                        if prediction777 == 8:
                            _t1462 = self.parse_atom()
                            atom786 = _t1462
                            _t1463 = logic_pb2.Formula(atom=atom786)
                            _t1461 = _t1463
                        else:
                            if prediction777 == 7:
                                _t1465 = self.parse_ffi()
                                ffi785 = _t1465
                                _t1466 = logic_pb2.Formula(ffi=ffi785)
                                _t1464 = _t1466
                            else:
                                if prediction777 == 6:
                                    _t1468 = self.parse_not()
                                    not784 = _t1468
                                    _t1469 = logic_pb2.Formula()
                                    getattr(_t1469, 'not').CopyFrom(not784)
                                    _t1467 = _t1469
                                else:
                                    if prediction777 == 5:
                                        _t1471 = self.parse_disjunction()
                                        disjunction783 = _t1471
                                        _t1472 = logic_pb2.Formula(disjunction=disjunction783)
                                        _t1470 = _t1472
                                    else:
                                        if prediction777 == 4:
                                            _t1474 = self.parse_conjunction()
                                            conjunction782 = _t1474
                                            _t1475 = logic_pb2.Formula(conjunction=conjunction782)
                                            _t1473 = _t1475
                                        else:
                                            if prediction777 == 3:
                                                _t1477 = self.parse_reduce()
                                                reduce781 = _t1477
                                                _t1478 = logic_pb2.Formula(reduce=reduce781)
                                                _t1476 = _t1478
                                            else:
                                                if prediction777 == 2:
                                                    _t1480 = self.parse_exists()
                                                    exists780 = _t1480
                                                    _t1481 = logic_pb2.Formula(exists=exists780)
                                                    _t1479 = _t1481
                                                else:
                                                    if prediction777 == 1:
                                                        _t1483 = self.parse_false()
                                                        false779 = _t1483
                                                        _t1484 = logic_pb2.Formula(disjunction=false779)
                                                        _t1482 = _t1484
                                                    else:
                                                        if prediction777 == 0:
                                                            _t1486 = self.parse_true()
                                                            true778 = _t1486
                                                            _t1487 = logic_pb2.Formula(conjunction=true778)
                                                            _t1485 = _t1487
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1482 = _t1485
                                                    _t1479 = _t1482
                                                _t1476 = _t1479
                                            _t1473 = _t1476
                                        _t1470 = _t1473
                                    _t1467 = _t1470
                                _t1464 = _t1467
                            _t1461 = _t1464
                        _t1458 = _t1461
                    _t1455 = _t1458
                _t1452 = _t1455
            _t1449 = _t1452
        result792 = _t1449
        self.record_span(span_start791, "Formula")
        return result792

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start793 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1488 = logic_pb2.Conjunction(args=[])
        result794 = _t1488
        self.record_span(span_start793, "Conjunction")
        return result794

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start795 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1489 = logic_pb2.Disjunction(args=[])
        result796 = _t1489
        self.record_span(span_start795, "Disjunction")
        return result796

    def parse_exists(self) -> logic_pb2.Exists:
        span_start799 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1490 = self.parse_bindings()
        bindings797 = _t1490
        _t1491 = self.parse_formula()
        formula798 = _t1491
        self.consume_literal(")")
        _t1492 = logic_pb2.Abstraction(vars=(list(bindings797[0]) + list(bindings797[1] if bindings797[1] is not None else [])), value=formula798)
        _t1493 = logic_pb2.Exists(body=_t1492)
        result800 = _t1493
        self.record_span(span_start799, "Exists")
        return result800

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start804 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1494 = self.parse_abstraction()
        abstraction801 = _t1494
        _t1495 = self.parse_abstraction()
        abstraction_3802 = _t1495
        _t1496 = self.parse_terms()
        terms803 = _t1496
        self.consume_literal(")")
        _t1497 = logic_pb2.Reduce(op=abstraction801, body=abstraction_3802, terms=terms803)
        result805 = _t1497
        self.record_span(span_start804, "Reduce")
        return result805

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs806 = []
        cond807 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond807:
            _t1498 = self.parse_term()
            item808 = _t1498
            xs806.append(item808)
            cond807 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        terms809 = xs806
        self.consume_literal(")")
        return terms809

    def parse_term(self) -> logic_pb2.Term:
        span_start813 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1499 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1500 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1501 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1502 = 1
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1503 = 1
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1504 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1505 = 0
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1506 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1507 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1508 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1509 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1510 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1511 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1512 = 1
                                                            else:
                                                                _t1512 = -1
                                                            _t1511 = _t1512
                                                        _t1510 = _t1511
                                                    _t1509 = _t1510
                                                _t1508 = _t1509
                                            _t1507 = _t1508
                                        _t1506 = _t1507
                                    _t1505 = _t1506
                                _t1504 = _t1505
                            _t1503 = _t1504
                        _t1502 = _t1503
                    _t1501 = _t1502
                _t1500 = _t1501
            _t1499 = _t1500
        prediction810 = _t1499
        if prediction810 == 1:
            _t1514 = self.parse_constant()
            constant812 = _t1514
            _t1515 = logic_pb2.Term(constant=constant812)
            _t1513 = _t1515
        else:
            if prediction810 == 0:
                _t1517 = self.parse_var()
                var811 = _t1517
                _t1518 = logic_pb2.Term(var=var811)
                _t1516 = _t1518
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1513 = _t1516
        result814 = _t1513
        self.record_span(span_start813, "Term")
        return result814

    def parse_var(self) -> logic_pb2.Var:
        span_start816 = self.span_start()
        symbol815 = self.consume_terminal("SYMBOL")
        _t1519 = logic_pb2.Var(name=symbol815)
        result817 = _t1519
        self.record_span(span_start816, "Var")
        return result817

    def parse_constant(self) -> logic_pb2.Value:
        span_start819 = self.span_start()
        _t1520 = self.parse_value()
        value818 = _t1520
        result820 = value818
        self.record_span(span_start819, "Value")
        return result820

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start825 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs821 = []
        cond822 = self.match_lookahead_literal("(", 0)
        while cond822:
            _t1521 = self.parse_formula()
            item823 = _t1521
            xs821.append(item823)
            cond822 = self.match_lookahead_literal("(", 0)
        formulas824 = xs821
        self.consume_literal(")")
        _t1522 = logic_pb2.Conjunction(args=formulas824)
        result826 = _t1522
        self.record_span(span_start825, "Conjunction")
        return result826

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start831 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs827 = []
        cond828 = self.match_lookahead_literal("(", 0)
        while cond828:
            _t1523 = self.parse_formula()
            item829 = _t1523
            xs827.append(item829)
            cond828 = self.match_lookahead_literal("(", 0)
        formulas830 = xs827
        self.consume_literal(")")
        _t1524 = logic_pb2.Disjunction(args=formulas830)
        result832 = _t1524
        self.record_span(span_start831, "Disjunction")
        return result832

    def parse_not(self) -> logic_pb2.Not:
        span_start834 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1525 = self.parse_formula()
        formula833 = _t1525
        self.consume_literal(")")
        _t1526 = logic_pb2.Not(arg=formula833)
        result835 = _t1526
        self.record_span(span_start834, "Not")
        return result835

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start839 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1527 = self.parse_name()
        name836 = _t1527
        _t1528 = self.parse_ffi_args()
        ffi_args837 = _t1528
        _t1529 = self.parse_terms()
        terms838 = _t1529
        self.consume_literal(")")
        _t1530 = logic_pb2.FFI(name=name836, args=ffi_args837, terms=terms838)
        result840 = _t1530
        self.record_span(span_start839, "FFI")
        return result840

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol841 = self.consume_terminal("SYMBOL")
        return symbol841

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs842 = []
        cond843 = self.match_lookahead_literal("(", 0)
        while cond843:
            _t1531 = self.parse_abstraction()
            item844 = _t1531
            xs842.append(item844)
            cond843 = self.match_lookahead_literal("(", 0)
        abstractions845 = xs842
        self.consume_literal(")")
        return abstractions845

    def parse_atom(self) -> logic_pb2.Atom:
        span_start851 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1532 = self.parse_relation_id()
        relation_id846 = _t1532
        xs847 = []
        cond848 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond848:
            _t1533 = self.parse_term()
            item849 = _t1533
            xs847.append(item849)
            cond848 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        terms850 = xs847
        self.consume_literal(")")
        _t1534 = logic_pb2.Atom(name=relation_id846, terms=terms850)
        result852 = _t1534
        self.record_span(span_start851, "Atom")
        return result852

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start858 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1535 = self.parse_name()
        name853 = _t1535
        xs854 = []
        cond855 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond855:
            _t1536 = self.parse_term()
            item856 = _t1536
            xs854.append(item856)
            cond855 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        terms857 = xs854
        self.consume_literal(")")
        _t1537 = logic_pb2.Pragma(name=name853, terms=terms857)
        result859 = _t1537
        self.record_span(span_start858, "Pragma")
        return result859

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start875 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1539 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1540 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1541 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1542 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1543 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1544 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1545 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1546 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1547 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1548 = 7
                                                else:
                                                    _t1548 = -1
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
        else:
            _t1538 = -1
        prediction860 = _t1538
        if prediction860 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1550 = self.parse_name()
            name870 = _t1550
            xs871 = []
            cond872 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
            while cond872:
                _t1551 = self.parse_rel_term()
                item873 = _t1551
                xs871.append(item873)
                cond872 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
            rel_terms874 = xs871
            self.consume_literal(")")
            _t1552 = logic_pb2.Primitive(name=name870, terms=rel_terms874)
            _t1549 = _t1552
        else:
            if prediction860 == 8:
                _t1554 = self.parse_divide()
                divide869 = _t1554
                _t1553 = divide869
            else:
                if prediction860 == 7:
                    _t1556 = self.parse_multiply()
                    multiply868 = _t1556
                    _t1555 = multiply868
                else:
                    if prediction860 == 6:
                        _t1558 = self.parse_minus()
                        minus867 = _t1558
                        _t1557 = minus867
                    else:
                        if prediction860 == 5:
                            _t1560 = self.parse_add()
                            add866 = _t1560
                            _t1559 = add866
                        else:
                            if prediction860 == 4:
                                _t1562 = self.parse_gt_eq()
                                gt_eq865 = _t1562
                                _t1561 = gt_eq865
                            else:
                                if prediction860 == 3:
                                    _t1564 = self.parse_gt()
                                    gt864 = _t1564
                                    _t1563 = gt864
                                else:
                                    if prediction860 == 2:
                                        _t1566 = self.parse_lt_eq()
                                        lt_eq863 = _t1566
                                        _t1565 = lt_eq863
                                    else:
                                        if prediction860 == 1:
                                            _t1568 = self.parse_lt()
                                            lt862 = _t1568
                                            _t1567 = lt862
                                        else:
                                            if prediction860 == 0:
                                                _t1570 = self.parse_eq()
                                                eq861 = _t1570
                                                _t1569 = eq861
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1567 = _t1569
                                        _t1565 = _t1567
                                    _t1563 = _t1565
                                _t1561 = _t1563
                            _t1559 = _t1561
                        _t1557 = _t1559
                    _t1555 = _t1557
                _t1553 = _t1555
            _t1549 = _t1553
        result876 = _t1549
        self.record_span(span_start875, "Primitive")
        return result876

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start879 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1571 = self.parse_term()
        term877 = _t1571
        _t1572 = self.parse_term()
        term_3878 = _t1572
        self.consume_literal(")")
        _t1573 = logic_pb2.RelTerm(term=term877)
        _t1574 = logic_pb2.RelTerm(term=term_3878)
        _t1575 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1573, _t1574])
        result880 = _t1575
        self.record_span(span_start879, "Primitive")
        return result880

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start883 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1576 = self.parse_term()
        term881 = _t1576
        _t1577 = self.parse_term()
        term_3882 = _t1577
        self.consume_literal(")")
        _t1578 = logic_pb2.RelTerm(term=term881)
        _t1579 = logic_pb2.RelTerm(term=term_3882)
        _t1580 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1578, _t1579])
        result884 = _t1580
        self.record_span(span_start883, "Primitive")
        return result884

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start887 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1581 = self.parse_term()
        term885 = _t1581
        _t1582 = self.parse_term()
        term_3886 = _t1582
        self.consume_literal(")")
        _t1583 = logic_pb2.RelTerm(term=term885)
        _t1584 = logic_pb2.RelTerm(term=term_3886)
        _t1585 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1583, _t1584])
        result888 = _t1585
        self.record_span(span_start887, "Primitive")
        return result888

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start891 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1586 = self.parse_term()
        term889 = _t1586
        _t1587 = self.parse_term()
        term_3890 = _t1587
        self.consume_literal(")")
        _t1588 = logic_pb2.RelTerm(term=term889)
        _t1589 = logic_pb2.RelTerm(term=term_3890)
        _t1590 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1588, _t1589])
        result892 = _t1590
        self.record_span(span_start891, "Primitive")
        return result892

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start895 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1591 = self.parse_term()
        term893 = _t1591
        _t1592 = self.parse_term()
        term_3894 = _t1592
        self.consume_literal(")")
        _t1593 = logic_pb2.RelTerm(term=term893)
        _t1594 = logic_pb2.RelTerm(term=term_3894)
        _t1595 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1593, _t1594])
        result896 = _t1595
        self.record_span(span_start895, "Primitive")
        return result896

    def parse_add(self) -> logic_pb2.Primitive:
        span_start900 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1596 = self.parse_term()
        term897 = _t1596
        _t1597 = self.parse_term()
        term_3898 = _t1597
        _t1598 = self.parse_term()
        term_4899 = _t1598
        self.consume_literal(")")
        _t1599 = logic_pb2.RelTerm(term=term897)
        _t1600 = logic_pb2.RelTerm(term=term_3898)
        _t1601 = logic_pb2.RelTerm(term=term_4899)
        _t1602 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1599, _t1600, _t1601])
        result901 = _t1602
        self.record_span(span_start900, "Primitive")
        return result901

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start905 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1603 = self.parse_term()
        term902 = _t1603
        _t1604 = self.parse_term()
        term_3903 = _t1604
        _t1605 = self.parse_term()
        term_4904 = _t1605
        self.consume_literal(")")
        _t1606 = logic_pb2.RelTerm(term=term902)
        _t1607 = logic_pb2.RelTerm(term=term_3903)
        _t1608 = logic_pb2.RelTerm(term=term_4904)
        _t1609 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1606, _t1607, _t1608])
        result906 = _t1609
        self.record_span(span_start905, "Primitive")
        return result906

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start910 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1610 = self.parse_term()
        term907 = _t1610
        _t1611 = self.parse_term()
        term_3908 = _t1611
        _t1612 = self.parse_term()
        term_4909 = _t1612
        self.consume_literal(")")
        _t1613 = logic_pb2.RelTerm(term=term907)
        _t1614 = logic_pb2.RelTerm(term=term_3908)
        _t1615 = logic_pb2.RelTerm(term=term_4909)
        _t1616 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1613, _t1614, _t1615])
        result911 = _t1616
        self.record_span(span_start910, "Primitive")
        return result911

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start915 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1617 = self.parse_term()
        term912 = _t1617
        _t1618 = self.parse_term()
        term_3913 = _t1618
        _t1619 = self.parse_term()
        term_4914 = _t1619
        self.consume_literal(")")
        _t1620 = logic_pb2.RelTerm(term=term912)
        _t1621 = logic_pb2.RelTerm(term=term_3913)
        _t1622 = logic_pb2.RelTerm(term=term_4914)
        _t1623 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1620, _t1621, _t1622])
        result916 = _t1623
        self.record_span(span_start915, "Primitive")
        return result916

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start920 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1624 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1625 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1626 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1627 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1628 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1629 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1630 = 1
                                else:
                                    if self.match_lookahead_terminal("SYMBOL", 0):
                                        _t1631 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1632 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1633 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1634 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1635 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1636 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1637 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1638 = 1
                                                                else:
                                                                    _t1638 = -1
                                                                _t1637 = _t1638
                                                            _t1636 = _t1637
                                                        _t1635 = _t1636
                                                    _t1634 = _t1635
                                                _t1633 = _t1634
                                            _t1632 = _t1633
                                        _t1631 = _t1632
                                    _t1630 = _t1631
                                _t1629 = _t1630
                            _t1628 = _t1629
                        _t1627 = _t1628
                    _t1626 = _t1627
                _t1625 = _t1626
            _t1624 = _t1625
        prediction917 = _t1624
        if prediction917 == 1:
            _t1640 = self.parse_term()
            term919 = _t1640
            _t1641 = logic_pb2.RelTerm(term=term919)
            _t1639 = _t1641
        else:
            if prediction917 == 0:
                _t1643 = self.parse_specialized_value()
                specialized_value918 = _t1643
                _t1644 = logic_pb2.RelTerm(specialized_value=specialized_value918)
                _t1642 = _t1644
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1639 = _t1642
        result921 = _t1639
        self.record_span(span_start920, "RelTerm")
        return result921

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start923 = self.span_start()
        self.consume_literal("#")
        _t1645 = self.parse_value()
        value922 = _t1645
        result924 = value922
        self.record_span(span_start923, "Value")
        return result924

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start930 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1646 = self.parse_name()
        name925 = _t1646
        xs926 = []
        cond927 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond927:
            _t1647 = self.parse_rel_term()
            item928 = _t1647
            xs926.append(item928)
            cond927 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        rel_terms929 = xs926
        self.consume_literal(")")
        _t1648 = logic_pb2.RelAtom(name=name925, terms=rel_terms929)
        result931 = _t1648
        self.record_span(span_start930, "RelAtom")
        return result931

    def parse_cast(self) -> logic_pb2.Cast:
        span_start934 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1649 = self.parse_term()
        term932 = _t1649
        _t1650 = self.parse_term()
        term_3933 = _t1650
        self.consume_literal(")")
        _t1651 = logic_pb2.Cast(input=term932, result=term_3933)
        result935 = _t1651
        self.record_span(span_start934, "Cast")
        return result935

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs936 = []
        cond937 = self.match_lookahead_literal("(", 0)
        while cond937:
            _t1652 = self.parse_attribute()
            item938 = _t1652
            xs936.append(item938)
            cond937 = self.match_lookahead_literal("(", 0)
        attributes939 = xs936
        self.consume_literal(")")
        return attributes939

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start945 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1653 = self.parse_name()
        name940 = _t1653
        xs941 = []
        cond942 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond942:
            _t1654 = self.parse_value()
            item943 = _t1654
            xs941.append(item943)
            cond942 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        values944 = xs941
        self.consume_literal(")")
        _t1655 = logic_pb2.Attribute(name=name940, args=values944)
        result946 = _t1655
        self.record_span(span_start945, "Attribute")
        return result946

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start952 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs947 = []
        cond948 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond948:
            _t1656 = self.parse_relation_id()
            item949 = _t1656
            xs947.append(item949)
            cond948 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids950 = xs947
        _t1657 = self.parse_script()
        script951 = _t1657
        self.consume_literal(")")
        _t1658 = logic_pb2.Algorithm(body=script951)
        getattr(_t1658, 'global').extend(relation_ids950)
        result953 = _t1658
        self.record_span(span_start952, "Algorithm")
        return result953

    def parse_script(self) -> logic_pb2.Script:
        span_start958 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs954 = []
        cond955 = self.match_lookahead_literal("(", 0)
        while cond955:
            _t1659 = self.parse_construct()
            item956 = _t1659
            xs954.append(item956)
            cond955 = self.match_lookahead_literal("(", 0)
        constructs957 = xs954
        self.consume_literal(")")
        _t1660 = logic_pb2.Script(constructs=constructs957)
        result959 = _t1660
        self.record_span(span_start958, "Script")
        return result959

    def parse_construct(self) -> logic_pb2.Construct:
        span_start963 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1662 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1663 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1664 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1665 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1666 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1667 = 1
                                else:
                                    _t1667 = -1
                                _t1666 = _t1667
                            _t1665 = _t1666
                        _t1664 = _t1665
                    _t1663 = _t1664
                _t1662 = _t1663
            _t1661 = _t1662
        else:
            _t1661 = -1
        prediction960 = _t1661
        if prediction960 == 1:
            _t1669 = self.parse_instruction()
            instruction962 = _t1669
            _t1670 = logic_pb2.Construct(instruction=instruction962)
            _t1668 = _t1670
        else:
            if prediction960 == 0:
                _t1672 = self.parse_loop()
                loop961 = _t1672
                _t1673 = logic_pb2.Construct(loop=loop961)
                _t1671 = _t1673
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1668 = _t1671
        result964 = _t1668
        self.record_span(span_start963, "Construct")
        return result964

    def parse_loop(self) -> logic_pb2.Loop:
        span_start967 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1674 = self.parse_init()
        init965 = _t1674
        _t1675 = self.parse_script()
        script966 = _t1675
        self.consume_literal(")")
        _t1676 = logic_pb2.Loop(init=init965, body=script966)
        result968 = _t1676
        self.record_span(span_start967, "Loop")
        return result968

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs969 = []
        cond970 = self.match_lookahead_literal("(", 0)
        while cond970:
            _t1677 = self.parse_instruction()
            item971 = _t1677
            xs969.append(item971)
            cond970 = self.match_lookahead_literal("(", 0)
        instructions972 = xs969
        self.consume_literal(")")
        return instructions972

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start979 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1679 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1680 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1681 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1682 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1683 = 0
                            else:
                                _t1683 = -1
                            _t1682 = _t1683
                        _t1681 = _t1682
                    _t1680 = _t1681
                _t1679 = _t1680
            _t1678 = _t1679
        else:
            _t1678 = -1
        prediction973 = _t1678
        if prediction973 == 4:
            _t1685 = self.parse_monus_def()
            monus_def978 = _t1685
            _t1686 = logic_pb2.Instruction(monus_def=monus_def978)
            _t1684 = _t1686
        else:
            if prediction973 == 3:
                _t1688 = self.parse_monoid_def()
                monoid_def977 = _t1688
                _t1689 = logic_pb2.Instruction(monoid_def=monoid_def977)
                _t1687 = _t1689
            else:
                if prediction973 == 2:
                    _t1691 = self.parse_break()
                    break976 = _t1691
                    _t1692 = logic_pb2.Instruction()
                    getattr(_t1692, 'break').CopyFrom(break976)
                    _t1690 = _t1692
                else:
                    if prediction973 == 1:
                        _t1694 = self.parse_upsert()
                        upsert975 = _t1694
                        _t1695 = logic_pb2.Instruction(upsert=upsert975)
                        _t1693 = _t1695
                    else:
                        if prediction973 == 0:
                            _t1697 = self.parse_assign()
                            assign974 = _t1697
                            _t1698 = logic_pb2.Instruction(assign=assign974)
                            _t1696 = _t1698
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1693 = _t1696
                    _t1690 = _t1693
                _t1687 = _t1690
            _t1684 = _t1687
        result980 = _t1684
        self.record_span(span_start979, "Instruction")
        return result980

    def parse_assign(self) -> logic_pb2.Assign:
        span_start984 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1699 = self.parse_relation_id()
        relation_id981 = _t1699
        _t1700 = self.parse_abstraction()
        abstraction982 = _t1700
        if self.match_lookahead_literal("(", 0):
            _t1702 = self.parse_attrs()
            _t1701 = _t1702
        else:
            _t1701 = None
        attrs983 = _t1701
        self.consume_literal(")")
        _t1703 = logic_pb2.Assign(name=relation_id981, body=abstraction982, attrs=(attrs983 if attrs983 is not None else []))
        result985 = _t1703
        self.record_span(span_start984, "Assign")
        return result985

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start989 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1704 = self.parse_relation_id()
        relation_id986 = _t1704
        _t1705 = self.parse_abstraction_with_arity()
        abstraction_with_arity987 = _t1705
        if self.match_lookahead_literal("(", 0):
            _t1707 = self.parse_attrs()
            _t1706 = _t1707
        else:
            _t1706 = None
        attrs988 = _t1706
        self.consume_literal(")")
        _t1708 = logic_pb2.Upsert(name=relation_id986, body=abstraction_with_arity987[0], attrs=(attrs988 if attrs988 is not None else []), value_arity=abstraction_with_arity987[1])
        result990 = _t1708
        self.record_span(span_start989, "Upsert")
        return result990

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1709 = self.parse_bindings()
        bindings991 = _t1709
        _t1710 = self.parse_formula()
        formula992 = _t1710
        self.consume_literal(")")
        _t1711 = logic_pb2.Abstraction(vars=(list(bindings991[0]) + list(bindings991[1] if bindings991[1] is not None else [])), value=formula992)
        return (_t1711, len(bindings991[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start996 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1712 = self.parse_relation_id()
        relation_id993 = _t1712
        _t1713 = self.parse_abstraction()
        abstraction994 = _t1713
        if self.match_lookahead_literal("(", 0):
            _t1715 = self.parse_attrs()
            _t1714 = _t1715
        else:
            _t1714 = None
        attrs995 = _t1714
        self.consume_literal(")")
        _t1716 = logic_pb2.Break(name=relation_id993, body=abstraction994, attrs=(attrs995 if attrs995 is not None else []))
        result997 = _t1716
        self.record_span(span_start996, "Break")
        return result997

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1002 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1717 = self.parse_monoid()
        monoid998 = _t1717
        _t1718 = self.parse_relation_id()
        relation_id999 = _t1718
        _t1719 = self.parse_abstraction_with_arity()
        abstraction_with_arity1000 = _t1719
        if self.match_lookahead_literal("(", 0):
            _t1721 = self.parse_attrs()
            _t1720 = _t1721
        else:
            _t1720 = None
        attrs1001 = _t1720
        self.consume_literal(")")
        _t1722 = logic_pb2.MonoidDef(monoid=monoid998, name=relation_id999, body=abstraction_with_arity1000[0], attrs=(attrs1001 if attrs1001 is not None else []), value_arity=abstraction_with_arity1000[1])
        result1003 = _t1722
        self.record_span(span_start1002, "MonoidDef")
        return result1003

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1009 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1724 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1725 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1726 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1727 = 2
                        else:
                            _t1727 = -1
                        _t1726 = _t1727
                    _t1725 = _t1726
                _t1724 = _t1725
            _t1723 = _t1724
        else:
            _t1723 = -1
        prediction1004 = _t1723
        if prediction1004 == 3:
            _t1729 = self.parse_sum_monoid()
            sum_monoid1008 = _t1729
            _t1730 = logic_pb2.Monoid(sum_monoid=sum_monoid1008)
            _t1728 = _t1730
        else:
            if prediction1004 == 2:
                _t1732 = self.parse_max_monoid()
                max_monoid1007 = _t1732
                _t1733 = logic_pb2.Monoid(max_monoid=max_monoid1007)
                _t1731 = _t1733
            else:
                if prediction1004 == 1:
                    _t1735 = self.parse_min_monoid()
                    min_monoid1006 = _t1735
                    _t1736 = logic_pb2.Monoid(min_monoid=min_monoid1006)
                    _t1734 = _t1736
                else:
                    if prediction1004 == 0:
                        _t1738 = self.parse_or_monoid()
                        or_monoid1005 = _t1738
                        _t1739 = logic_pb2.Monoid(or_monoid=or_monoid1005)
                        _t1737 = _t1739
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1734 = _t1737
                _t1731 = _t1734
            _t1728 = _t1731
        result1010 = _t1728
        self.record_span(span_start1009, "Monoid")
        return result1010

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1011 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1740 = logic_pb2.OrMonoid()
        result1012 = _t1740
        self.record_span(span_start1011, "OrMonoid")
        return result1012

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1014 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1741 = self.parse_type()
        type1013 = _t1741
        self.consume_literal(")")
        _t1742 = logic_pb2.MinMonoid(type=type1013)
        result1015 = _t1742
        self.record_span(span_start1014, "MinMonoid")
        return result1015

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1017 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1743 = self.parse_type()
        type1016 = _t1743
        self.consume_literal(")")
        _t1744 = logic_pb2.MaxMonoid(type=type1016)
        result1018 = _t1744
        self.record_span(span_start1017, "MaxMonoid")
        return result1018

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1020 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1745 = self.parse_type()
        type1019 = _t1745
        self.consume_literal(")")
        _t1746 = logic_pb2.SumMonoid(type=type1019)
        result1021 = _t1746
        self.record_span(span_start1020, "SumMonoid")
        return result1021

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1026 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1747 = self.parse_monoid()
        monoid1022 = _t1747
        _t1748 = self.parse_relation_id()
        relation_id1023 = _t1748
        _t1749 = self.parse_abstraction_with_arity()
        abstraction_with_arity1024 = _t1749
        if self.match_lookahead_literal("(", 0):
            _t1751 = self.parse_attrs()
            _t1750 = _t1751
        else:
            _t1750 = None
        attrs1025 = _t1750
        self.consume_literal(")")
        _t1752 = logic_pb2.MonusDef(monoid=monoid1022, name=relation_id1023, body=abstraction_with_arity1024[0], attrs=(attrs1025 if attrs1025 is not None else []), value_arity=abstraction_with_arity1024[1])
        result1027 = _t1752
        self.record_span(span_start1026, "MonusDef")
        return result1027

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1032 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1753 = self.parse_relation_id()
        relation_id1028 = _t1753
        _t1754 = self.parse_abstraction()
        abstraction1029 = _t1754
        _t1755 = self.parse_functional_dependency_keys()
        functional_dependency_keys1030 = _t1755
        _t1756 = self.parse_functional_dependency_values()
        functional_dependency_values1031 = _t1756
        self.consume_literal(")")
        _t1757 = logic_pb2.FunctionalDependency(guard=abstraction1029, keys=functional_dependency_keys1030, values=functional_dependency_values1031)
        _t1758 = logic_pb2.Constraint(name=relation_id1028, functional_dependency=_t1757)
        result1033 = _t1758
        self.record_span(span_start1032, "Constraint")
        return result1033

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1034 = []
        cond1035 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1035:
            _t1759 = self.parse_var()
            item1036 = _t1759
            xs1034.append(item1036)
            cond1035 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1037 = xs1034
        self.consume_literal(")")
        return vars1037

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1038 = []
        cond1039 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1039:
            _t1760 = self.parse_var()
            item1040 = _t1760
            xs1038.append(item1040)
            cond1039 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1041 = xs1038
        self.consume_literal(")")
        return vars1041

    def parse_data(self) -> logic_pb2.Data:
        span_start1047 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1762 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1763 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1764 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1765 = 1
                        else:
                            _t1765 = -1
                        _t1764 = _t1765
                    _t1763 = _t1764
                _t1762 = _t1763
            _t1761 = _t1762
        else:
            _t1761 = -1
        prediction1042 = _t1761
        if prediction1042 == 3:
            _t1767 = self.parse_iceberg_data()
            iceberg_data1046 = _t1767
            _t1768 = logic_pb2.Data(iceberg_data=iceberg_data1046)
            _t1766 = _t1768
        else:
            if prediction1042 == 2:
                _t1770 = self.parse_csv_data()
                csv_data1045 = _t1770
                _t1771 = logic_pb2.Data(csv_data=csv_data1045)
                _t1769 = _t1771
            else:
                if prediction1042 == 1:
                    _t1773 = self.parse_betree_relation()
                    betree_relation1044 = _t1773
                    _t1774 = logic_pb2.Data(betree_relation=betree_relation1044)
                    _t1772 = _t1774
                else:
                    if prediction1042 == 0:
                        _t1776 = self.parse_edb()
                        edb1043 = _t1776
                        _t1777 = logic_pb2.Data(edb=edb1043)
                        _t1775 = _t1777
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1772 = _t1775
                _t1769 = _t1772
            _t1766 = _t1769
        result1048 = _t1766
        self.record_span(span_start1047, "Data")
        return result1048

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1052 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1778 = self.parse_relation_id()
        relation_id1049 = _t1778
        _t1779 = self.parse_edb_path()
        edb_path1050 = _t1779
        _t1780 = self.parse_edb_types()
        edb_types1051 = _t1780
        self.consume_literal(")")
        _t1781 = logic_pb2.EDB(target_id=relation_id1049, path=edb_path1050, types=edb_types1051)
        result1053 = _t1781
        self.record_span(span_start1052, "EDB")
        return result1053

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1054 = []
        cond1055 = self.match_lookahead_terminal("STRING", 0)
        while cond1055:
            item1056 = self.consume_terminal("STRING")
            xs1054.append(item1056)
            cond1055 = self.match_lookahead_terminal("STRING", 0)
        strings1057 = xs1054
        self.consume_literal("]")
        return strings1057

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1058 = []
        cond1059 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1059:
            _t1782 = self.parse_type()
            item1060 = _t1782
            xs1058.append(item1060)
            cond1059 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1061 = xs1058
        self.consume_literal("]")
        return types1061

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1064 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1783 = self.parse_relation_id()
        relation_id1062 = _t1783
        _t1784 = self.parse_betree_info()
        betree_info1063 = _t1784
        self.consume_literal(")")
        _t1785 = logic_pb2.BeTreeRelation(name=relation_id1062, relation_info=betree_info1063)
        result1065 = _t1785
        self.record_span(span_start1064, "BeTreeRelation")
        return result1065

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1069 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1786 = self.parse_betree_info_key_types()
        betree_info_key_types1066 = _t1786
        _t1787 = self.parse_betree_info_value_types()
        betree_info_value_types1067 = _t1787
        _t1788 = self.parse_config_dict()
        config_dict1068 = _t1788
        self.consume_literal(")")
        _t1789 = self.construct_betree_info(betree_info_key_types1066, betree_info_value_types1067, config_dict1068)
        result1070 = _t1789
        self.record_span(span_start1069, "BeTreeInfo")
        return result1070

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1071 = []
        cond1072 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1072:
            _t1790 = self.parse_type()
            item1073 = _t1790
            xs1071.append(item1073)
            cond1072 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1074 = xs1071
        self.consume_literal(")")
        return types1074

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1075 = []
        cond1076 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1076:
            _t1791 = self.parse_type()
            item1077 = _t1791
            xs1075.append(item1077)
            cond1076 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1078 = xs1075
        self.consume_literal(")")
        return types1078

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1083 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1792 = self.parse_csvlocator()
        csvlocator1079 = _t1792
        _t1793 = self.parse_csv_config()
        csv_config1080 = _t1793
        _t1794 = self.parse_gnf_columns()
        gnf_columns1081 = _t1794
        _t1795 = self.parse_csv_asof()
        csv_asof1082 = _t1795
        self.consume_literal(")")
        _t1796 = logic_pb2.CSVData(locator=csvlocator1079, config=csv_config1080, columns=gnf_columns1081, asof=csv_asof1082)
        result1084 = _t1796
        self.record_span(span_start1083, "CSVData")
        return result1084

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1087 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1798 = self.parse_csv_locator_paths()
            _t1797 = _t1798
        else:
            _t1797 = None
        csv_locator_paths1085 = _t1797
        if self.match_lookahead_literal("(", 0):
            _t1800 = self.parse_csv_locator_inline_data()
            _t1799 = _t1800
        else:
            _t1799 = None
        csv_locator_inline_data1086 = _t1799
        self.consume_literal(")")
        _t1801 = logic_pb2.CSVLocator(paths=(csv_locator_paths1085 if csv_locator_paths1085 is not None else []), inline_data=(csv_locator_inline_data1086 if csv_locator_inline_data1086 is not None else "").encode())
        result1088 = _t1801
        self.record_span(span_start1087, "CSVLocator")
        return result1088

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1089 = []
        cond1090 = self.match_lookahead_terminal("STRING", 0)
        while cond1090:
            item1091 = self.consume_terminal("STRING")
            xs1089.append(item1091)
            cond1090 = self.match_lookahead_terminal("STRING", 0)
        strings1092 = xs1089
        self.consume_literal(")")
        return strings1092

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1093 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1093

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1095 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1802 = self.parse_config_dict()
        config_dict1094 = _t1802
        self.consume_literal(")")
        _t1803 = self.construct_csv_config(config_dict1094)
        result1096 = _t1803
        self.record_span(span_start1095, "CSVConfig")
        return result1096

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1097 = []
        cond1098 = self.match_lookahead_literal("(", 0)
        while cond1098:
            _t1804 = self.parse_gnf_column()
            item1099 = _t1804
            xs1097.append(item1099)
            cond1098 = self.match_lookahead_literal("(", 0)
        gnf_columns1100 = xs1097
        self.consume_literal(")")
        return gnf_columns1100

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1107 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1805 = self.parse_gnf_column_path()
        gnf_column_path1101 = _t1805
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1807 = self.parse_relation_id()
            _t1806 = _t1807
        else:
            _t1806 = None
        relation_id1102 = _t1806
        self.consume_literal("[")
        xs1103 = []
        cond1104 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1104:
            _t1808 = self.parse_type()
            item1105 = _t1808
            xs1103.append(item1105)
            cond1104 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1106 = xs1103
        self.consume_literal("]")
        self.consume_literal(")")
        _t1809 = logic_pb2.GNFColumn(column_path=gnf_column_path1101, target_id=relation_id1102, types=types1106)
        result1108 = _t1809
        self.record_span(span_start1107, "GNFColumn")
        return result1108

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1810 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1811 = 0
            else:
                _t1811 = -1
            _t1810 = _t1811
        prediction1109 = _t1810
        if prediction1109 == 1:
            self.consume_literal("[")
            xs1111 = []
            cond1112 = self.match_lookahead_terminal("STRING", 0)
            while cond1112:
                item1113 = self.consume_terminal("STRING")
                xs1111.append(item1113)
                cond1112 = self.match_lookahead_terminal("STRING", 0)
            strings1114 = xs1111
            self.consume_literal("]")
            _t1812 = strings1114
        else:
            if prediction1109 == 0:
                string1110 = self.consume_terminal("STRING")
                _t1813 = [string1110]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1812 = _t1813
        return _t1812

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1115 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1115

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1120 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1814 = self.parse_iceberg_locator()
        iceberg_locator1116 = _t1814
        _t1815 = self.parse_iceberg_config()
        iceberg_config1117 = _t1815
        _t1816 = self.parse_gnf_columns()
        gnf_columns1118 = _t1816
        if self.match_lookahead_literal("(", 0):
            _t1818 = self.parse_iceberg_to_snapshot()
            _t1817 = _t1818
        else:
            _t1817 = None
        iceberg_to_snapshot1119 = _t1817
        self.consume_literal(")")
        _t1819 = logic_pb2.IcebergData(locator=iceberg_locator1116, config=iceberg_config1117, columns=gnf_columns1118, to_snapshot=iceberg_to_snapshot1119)
        result1121 = _t1819
        self.record_span(span_start1120, "IcebergData")
        return result1121

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1125 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        string1122 = self.consume_terminal("STRING")
        _t1820 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1123 = _t1820
        string_41124 = self.consume_terminal("STRING")
        self.consume_literal(")")
        _t1821 = logic_pb2.IcebergLocator(table_name=string1122, namespace=iceberg_locator_namespace1123, warehouse=string_41124)
        result1126 = _t1821
        self.record_span(span_start1125, "IcebergLocator")
        return result1126

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1127 = []
        cond1128 = self.match_lookahead_terminal("STRING", 0)
        while cond1128:
            item1129 = self.consume_terminal("STRING")
            xs1127.append(item1129)
            cond1128 = self.match_lookahead_terminal("STRING", 0)
        strings1130 = xs1127
        self.consume_literal(")")
        return strings1130

    def parse_iceberg_config(self) -> logic_pb2.IcebergConfig:
        span_start1135 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_config")
        string1131 = self.consume_terminal("STRING")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t1823 = self.parse_iceberg_config_scope()
            _t1822 = _t1823
        else:
            _t1822 = None
        iceberg_config_scope1132 = _t1822
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("properties", 1)):
            _t1825 = self.parse_iceberg_config_properties()
            _t1824 = _t1825
        else:
            _t1824 = None
        iceberg_config_properties1133 = _t1824
        if self.match_lookahead_literal("(", 0):
            _t1827 = self.parse_iceberg_config_credentials()
            _t1826 = _t1827
        else:
            _t1826 = None
        iceberg_config_credentials1134 = _t1826
        self.consume_literal(")")
        _t1828 = self.construct_iceberg_config(string1131, iceberg_config_scope1132, iceberg_config_properties1133, iceberg_config_credentials1134)
        result1136 = _t1828
        self.record_span(span_start1135, "IcebergConfig")
        return result1136

    def parse_iceberg_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1137 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1137

    def parse_iceberg_config_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1138 = []
        cond1139 = self.match_lookahead_literal("(", 0)
        while cond1139:
            _t1829 = self.parse_iceberg_kv_pair()
            item1140 = _t1829
            xs1138.append(item1140)
            cond1139 = self.match_lookahead_literal("(", 0)
        iceberg_kv_pairs1141 = xs1138
        self.consume_literal(")")
        return iceberg_kv_pairs1141

    def parse_iceberg_kv_pair(self) -> tuple[str, str]:
        self.consume_literal("(")
        string1142 = self.consume_terminal("STRING")
        string_21143 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1142, string_21143,)

    def parse_iceberg_config_credentials(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("credentials")
        xs1144 = []
        cond1145 = self.match_lookahead_literal("(", 0)
        while cond1145:
            _t1830 = self.parse_iceberg_kv_pair()
            item1146 = _t1830
            xs1144.append(item1146)
            cond1145 = self.match_lookahead_literal("(", 0)
        iceberg_kv_pairs1147 = xs1144
        self.consume_literal(")")
        return iceberg_kv_pairs1147

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1148 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1148

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1150 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1831 = self.parse_fragment_id()
        fragment_id1149 = _t1831
        self.consume_literal(")")
        _t1832 = transactions_pb2.Undefine(fragment_id=fragment_id1149)
        result1151 = _t1832
        self.record_span(span_start1150, "Undefine")
        return result1151

    def parse_context(self) -> transactions_pb2.Context:
        span_start1156 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1152 = []
        cond1153 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1153:
            _t1833 = self.parse_relation_id()
            item1154 = _t1833
            xs1152.append(item1154)
            cond1153 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1155 = xs1152
        self.consume_literal(")")
        _t1834 = transactions_pb2.Context(relations=relation_ids1155)
        result1157 = _t1834
        self.record_span(span_start1156, "Context")
        return result1157

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1162 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1158 = []
        cond1159 = self.match_lookahead_literal("[", 0)
        while cond1159:
            _t1835 = self.parse_snapshot_mapping()
            item1160 = _t1835
            xs1158.append(item1160)
            cond1159 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1161 = xs1158
        self.consume_literal(")")
        _t1836 = transactions_pb2.Snapshot(mappings=snapshot_mappings1161)
        result1163 = _t1836
        self.record_span(span_start1162, "Snapshot")
        return result1163

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1166 = self.span_start()
        _t1837 = self.parse_edb_path()
        edb_path1164 = _t1837
        _t1838 = self.parse_relation_id()
        relation_id1165 = _t1838
        _t1839 = transactions_pb2.SnapshotMapping(destination_path=edb_path1164, source_relation=relation_id1165)
        result1167 = _t1839
        self.record_span(span_start1166, "SnapshotMapping")
        return result1167

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1168 = []
        cond1169 = self.match_lookahead_literal("(", 0)
        while cond1169:
            _t1840 = self.parse_read()
            item1170 = _t1840
            xs1168.append(item1170)
            cond1169 = self.match_lookahead_literal("(", 0)
        reads1171 = xs1168
        self.consume_literal(")")
        return reads1171

    def parse_read(self) -> transactions_pb2.Read:
        span_start1178 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1842 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1843 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1844 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1845 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1846 = 3
                            else:
                                _t1846 = -1
                            _t1845 = _t1846
                        _t1844 = _t1845
                    _t1843 = _t1844
                _t1842 = _t1843
            _t1841 = _t1842
        else:
            _t1841 = -1
        prediction1172 = _t1841
        if prediction1172 == 4:
            _t1848 = self.parse_export()
            export1177 = _t1848
            _t1849 = transactions_pb2.Read(export=export1177)
            _t1847 = _t1849
        else:
            if prediction1172 == 3:
                _t1851 = self.parse_abort()
                abort1176 = _t1851
                _t1852 = transactions_pb2.Read(abort=abort1176)
                _t1850 = _t1852
            else:
                if prediction1172 == 2:
                    _t1854 = self.parse_what_if()
                    what_if1175 = _t1854
                    _t1855 = transactions_pb2.Read(what_if=what_if1175)
                    _t1853 = _t1855
                else:
                    if prediction1172 == 1:
                        _t1857 = self.parse_output()
                        output1174 = _t1857
                        _t1858 = transactions_pb2.Read(output=output1174)
                        _t1856 = _t1858
                    else:
                        if prediction1172 == 0:
                            _t1860 = self.parse_demand()
                            demand1173 = _t1860
                            _t1861 = transactions_pb2.Read(demand=demand1173)
                            _t1859 = _t1861
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1856 = _t1859
                    _t1853 = _t1856
                _t1850 = _t1853
            _t1847 = _t1850
        result1179 = _t1847
        self.record_span(span_start1178, "Read")
        return result1179

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1181 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1862 = self.parse_relation_id()
        relation_id1180 = _t1862
        self.consume_literal(")")
        _t1863 = transactions_pb2.Demand(relation_id=relation_id1180)
        result1182 = _t1863
        self.record_span(span_start1181, "Demand")
        return result1182

    def parse_output(self) -> transactions_pb2.Output:
        span_start1185 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t1864 = self.parse_name()
        name1183 = _t1864
        _t1865 = self.parse_relation_id()
        relation_id1184 = _t1865
        self.consume_literal(")")
        _t1866 = transactions_pb2.Output(name=name1183, relation_id=relation_id1184)
        result1186 = _t1866
        self.record_span(span_start1185, "Output")
        return result1186

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1189 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1867 = self.parse_name()
        name1187 = _t1867
        _t1868 = self.parse_epoch()
        epoch1188 = _t1868
        self.consume_literal(")")
        _t1869 = transactions_pb2.WhatIf(branch=name1187, epoch=epoch1188)
        result1190 = _t1869
        self.record_span(span_start1189, "WhatIf")
        return result1190

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1193 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1871 = self.parse_name()
            _t1870 = _t1871
        else:
            _t1870 = None
        name1191 = _t1870
        _t1872 = self.parse_relation_id()
        relation_id1192 = _t1872
        self.consume_literal(")")
        _t1873 = transactions_pb2.Abort(name=(name1191 if name1191 is not None else "abort"), relation_id=relation_id1192)
        result1194 = _t1873
        self.record_span(span_start1193, "Abort")
        return result1194

    def parse_export(self) -> transactions_pb2.Export:
        span_start1196 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export")
        _t1874 = self.parse_export_csv_config()
        export_csv_config1195 = _t1874
        self.consume_literal(")")
        _t1875 = transactions_pb2.Export(csv_config=export_csv_config1195)
        result1197 = _t1875
        self.record_span(span_start1196, "Export")
        return result1197

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1205 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t1877 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t1878 = 1
                else:
                    _t1878 = -1
                _t1877 = _t1878
            _t1876 = _t1877
        else:
            _t1876 = -1
        prediction1198 = _t1876
        if prediction1198 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t1880 = self.parse_export_csv_path()
            export_csv_path1202 = _t1880
            _t1881 = self.parse_export_csv_columns_list()
            export_csv_columns_list1203 = _t1881
            _t1882 = self.parse_config_dict()
            config_dict1204 = _t1882
            self.consume_literal(")")
            _t1883 = self.construct_export_csv_config(export_csv_path1202, export_csv_columns_list1203, config_dict1204)
            _t1879 = _t1883
        else:
            if prediction1198 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t1885 = self.parse_export_csv_path()
                export_csv_path1199 = _t1885
                _t1886 = self.parse_export_csv_source()
                export_csv_source1200 = _t1886
                _t1887 = self.parse_csv_config()
                csv_config1201 = _t1887
                self.consume_literal(")")
                _t1888 = self.construct_export_csv_config_with_source(export_csv_path1199, export_csv_source1200, csv_config1201)
                _t1884 = _t1888
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1879 = _t1884
        result1206 = _t1879
        self.record_span(span_start1205, "ExportCSVConfig")
        return result1206

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1207 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1207

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1214 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t1890 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t1891 = 0
                else:
                    _t1891 = -1
                _t1890 = _t1891
            _t1889 = _t1890
        else:
            _t1889 = -1
        prediction1208 = _t1889
        if prediction1208 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t1893 = self.parse_relation_id()
            relation_id1213 = _t1893
            self.consume_literal(")")
            _t1894 = transactions_pb2.ExportCSVSource(table_def=relation_id1213)
            _t1892 = _t1894
        else:
            if prediction1208 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1209 = []
                cond1210 = self.match_lookahead_literal("(", 0)
                while cond1210:
                    _t1896 = self.parse_export_csv_column()
                    item1211 = _t1896
                    xs1209.append(item1211)
                    cond1210 = self.match_lookahead_literal("(", 0)
                export_csv_columns1212 = xs1209
                self.consume_literal(")")
                _t1897 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1212)
                _t1898 = transactions_pb2.ExportCSVSource(gnf_columns=_t1897)
                _t1895 = _t1898
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1892 = _t1895
        result1215 = _t1892
        self.record_span(span_start1214, "ExportCSVSource")
        return result1215

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1218 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1216 = self.consume_terminal("STRING")
        _t1899 = self.parse_relation_id()
        relation_id1217 = _t1899
        self.consume_literal(")")
        _t1900 = transactions_pb2.ExportCSVColumn(column_name=string1216, column_data=relation_id1217)
        result1219 = _t1900
        self.record_span(span_start1218, "ExportCSVColumn")
        return result1219

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1220 = []
        cond1221 = self.match_lookahead_literal("(", 0)
        while cond1221:
            _t1901 = self.parse_export_csv_column()
            item1222 = _t1901
            xs1220.append(item1222)
            cond1221 = self.match_lookahead_literal("(", 0)
        export_csv_columns1223 = xs1220
        self.consume_literal(")")
        return export_csv_columns1223


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
