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
    (
        "FLOAT32",
        re.compile(r"([-]?\d+\.\d+f32|inf32|nan32)"),
        lambda x: Lexer.scan_float32(x),
    ),
    ("FLOAT", re.compile(r"([-]?\d+\.\d+|inf|nan)"), lambda x: Lexer.scan_float(x)),
    ("INT32", re.compile(r"[-]?\d+i32"), lambda x: Lexer.scan_int32(x)),
    ("INT", re.compile(r"[-]?\d+"), lambda x: Lexer.scan_int(x)),
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
        if f == "inf32":
            return float("inf")
        elif f == "nan32":
            return float("nan")
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
            _t1911 = value.HasField("int32_value")
        else:
            _t1911 = False
        if _t1911:
            assert value is not None
            return value.int32_value
        else:
            _t1912 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t1913 = value.HasField("int_value")
        else:
            _t1913 = False
        if _t1913:
            assert value is not None
            return value.int_value
        else:
            _t1914 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t1915 = value.HasField("string_value")
        else:
            _t1915 = False
        if _t1915:
            assert value is not None
            return value.string_value
        else:
            _t1916 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t1917 = value.HasField("boolean_value")
        else:
            _t1917 = False
        if _t1917:
            assert value is not None
            return value.boolean_value
        else:
            _t1918 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t1919 = value.HasField("string_value")
        else:
            _t1919 = False
        if _t1919:
            assert value is not None
            return [value.string_value]
        else:
            _t1920 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t1921 = value.HasField("int_value")
        else:
            _t1921 = False
        if _t1921:
            assert value is not None
            return value.int_value
        else:
            _t1922 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t1923 = value.HasField("float_value")
        else:
            _t1923 = False
        if _t1923:
            assert value is not None
            return value.float_value
        else:
            _t1924 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t1925 = value.HasField("string_value")
        else:
            _t1925 = False
        if _t1925:
            assert value is not None
            return value.string_value.encode()
        else:
            _t1926 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t1927 = value.HasField("uint128_value")
        else:
            _t1927 = False
        if _t1927:
            assert value is not None
            return value.uint128_value
        else:
            _t1928 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t1929 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t1929
        _t1930 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t1930
        _t1931 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t1931
        _t1932 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t1932
        _t1933 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t1933
        _t1934 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t1934
        _t1935 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t1935
        _t1936 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t1936
        _t1937 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t1937
        _t1938 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t1938
        _t1939 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t1939
        _t1940 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t1940
        _t1941 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t1941

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1942 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1942
        _t1943 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1943
        _t1944 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1944
        _t1945 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1945
        _t1946 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1946
        _t1947 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1947
        _t1948 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1948
        _t1949 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1949
        _t1950 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1950
        _t1951 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1951
        _t1952 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1952

    def default_configure(self) -> transactions_pb2.Configure:
        _t1953 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1953
        _t1954 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1954

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
        _t1955 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1955
        _t1956 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1956
        _t1957 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1957

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1958 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1958
        _t1959 = self._extract_value_string(config.get("compression"), "")
        compression = _t1959
        _t1960 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1960
        _t1961 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1961
        _t1962 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1962
        _t1963 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1963
        _t1964 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1964
        _t1965 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1965

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t1966 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t1966

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start610 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1209 = self.parse_configure()
            _t1208 = _t1209
        else:
            _t1208 = None
        configure604 = _t1208
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1211 = self.parse_sync()
            _t1210 = _t1211
        else:
            _t1210 = None
        sync605 = _t1210
        xs606 = []
        cond607 = self.match_lookahead_literal("(", 0)
        while cond607:
            _t1212 = self.parse_epoch()
            item608 = _t1212
            xs606.append(item608)
            cond607 = self.match_lookahead_literal("(", 0)
        epochs609 = xs606
        self.consume_literal(")")
        _t1213 = self.default_configure()
        _t1214 = transactions_pb2.Transaction(epochs=epochs609, configure=(configure604 if configure604 is not None else _t1213), sync=sync605)
        result611 = _t1214
        self.record_span(span_start610, "Transaction")
        return result611

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start613 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1215 = self.parse_config_dict()
        config_dict612 = _t1215
        self.consume_literal(")")
        _t1216 = self.construct_configure(config_dict612)
        result614 = _t1216
        self.record_span(span_start613, "Configure")
        return result614

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs615 = []
        cond616 = self.match_lookahead_literal(":", 0)
        while cond616:
            _t1217 = self.parse_config_key_value()
            item617 = _t1217
            xs615.append(item617)
            cond616 = self.match_lookahead_literal(":", 0)
        config_key_values618 = xs615
        self.consume_literal("}")
        return config_key_values618

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol619 = self.consume_terminal("SYMBOL")
        _t1218 = self.parse_raw_value()
        raw_value620 = _t1218
        return (symbol619, raw_value620,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start634 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1219 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1220 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1221 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1223 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1224 = 0
                            else:
                                _t1224 = -1
                            _t1223 = _t1224
                        _t1222 = _t1223
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1225 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1226 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1227 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1228 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1229 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1230 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1231 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1232 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1233 = 10
                                                        else:
                                                            _t1233 = -1
                                                        _t1232 = _t1233
                                                    _t1231 = _t1232
                                                _t1230 = _t1231
                                            _t1229 = _t1230
                                        _t1228 = _t1229
                                    _t1227 = _t1228
                                _t1226 = _t1227
                            _t1225 = _t1226
                        _t1222 = _t1225
                    _t1221 = _t1222
                _t1220 = _t1221
            _t1219 = _t1220
        prediction621 = _t1219
        if prediction621 == 12:
            _t1235 = self.parse_boolean_value()
            boolean_value633 = _t1235
            _t1236 = logic_pb2.Value(boolean_value=boolean_value633)
            _t1234 = _t1236
        else:
            if prediction621 == 11:
                self.consume_literal("missing")
                _t1238 = logic_pb2.MissingValue()
                _t1239 = logic_pb2.Value(missing_value=_t1238)
                _t1237 = _t1239
            else:
                if prediction621 == 10:
                    decimal632 = self.consume_terminal("DECIMAL")
                    _t1241 = logic_pb2.Value(decimal_value=decimal632)
                    _t1240 = _t1241
                else:
                    if prediction621 == 9:
                        int128631 = self.consume_terminal("INT128")
                        _t1243 = logic_pb2.Value(int128_value=int128631)
                        _t1242 = _t1243
                    else:
                        if prediction621 == 8:
                            uint128630 = self.consume_terminal("UINT128")
                            _t1245 = logic_pb2.Value(uint128_value=uint128630)
                            _t1244 = _t1245
                        else:
                            if prediction621 == 7:
                                uint32629 = self.consume_terminal("UINT32")
                                _t1247 = logic_pb2.Value(uint32_value=uint32629)
                                _t1246 = _t1247
                            else:
                                if prediction621 == 6:
                                    float628 = self.consume_terminal("FLOAT")
                                    _t1249 = logic_pb2.Value(float_value=float628)
                                    _t1248 = _t1249
                                else:
                                    if prediction621 == 5:
                                        float32627 = self.consume_terminal("FLOAT32")
                                        _t1251 = logic_pb2.Value(float32_value=float32627)
                                        _t1250 = _t1251
                                    else:
                                        if prediction621 == 4:
                                            int626 = self.consume_terminal("INT")
                                            _t1253 = logic_pb2.Value(int_value=int626)
                                            _t1252 = _t1253
                                        else:
                                            if prediction621 == 3:
                                                int32625 = self.consume_terminal("INT32")
                                                _t1255 = logic_pb2.Value(int32_value=int32625)
                                                _t1254 = _t1255
                                            else:
                                                if prediction621 == 2:
                                                    string624 = self.consume_terminal("STRING")
                                                    _t1257 = logic_pb2.Value(string_value=string624)
                                                    _t1256 = _t1257
                                                else:
                                                    if prediction621 == 1:
                                                        _t1259 = self.parse_raw_datetime()
                                                        raw_datetime623 = _t1259
                                                        _t1260 = logic_pb2.Value(datetime_value=raw_datetime623)
                                                        _t1258 = _t1260
                                                    else:
                                                        if prediction621 == 0:
                                                            _t1262 = self.parse_raw_date()
                                                            raw_date622 = _t1262
                                                            _t1263 = logic_pb2.Value(date_value=raw_date622)
                                                            _t1261 = _t1263
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1258 = _t1261
                                                    _t1256 = _t1258
                                                _t1254 = _t1256
                                            _t1252 = _t1254
                                        _t1250 = _t1252
                                    _t1248 = _t1250
                                _t1246 = _t1248
                            _t1244 = _t1246
                        _t1242 = _t1244
                    _t1240 = _t1242
                _t1237 = _t1240
            _t1234 = _t1237
        result635 = _t1234
        self.record_span(span_start634, "Value")
        return result635

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start639 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int636 = self.consume_terminal("INT")
        int_3637 = self.consume_terminal("INT")
        int_4638 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1264 = logic_pb2.DateValue(year=int(int636), month=int(int_3637), day=int(int_4638))
        result640 = _t1264
        self.record_span(span_start639, "DateValue")
        return result640

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start648 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int641 = self.consume_terminal("INT")
        int_3642 = self.consume_terminal("INT")
        int_4643 = self.consume_terminal("INT")
        int_5644 = self.consume_terminal("INT")
        int_6645 = self.consume_terminal("INT")
        int_7646 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1265 = self.consume_terminal("INT")
        else:
            _t1265 = None
        int_8647 = _t1265
        self.consume_literal(")")
        _t1266 = logic_pb2.DateTimeValue(year=int(int641), month=int(int_3642), day=int(int_4643), hour=int(int_5644), minute=int(int_6645), second=int(int_7646), microsecond=int((int_8647 if int_8647 is not None else 0)))
        result649 = _t1266
        self.record_span(span_start648, "DateTimeValue")
        return result649

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1267 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1268 = 1
            else:
                _t1268 = -1
            _t1267 = _t1268
        prediction650 = _t1267
        if prediction650 == 1:
            self.consume_literal("false")
            _t1269 = False
        else:
            if prediction650 == 0:
                self.consume_literal("true")
                _t1270 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1269 = _t1270
        return _t1269

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start655 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs651 = []
        cond652 = self.match_lookahead_literal(":", 0)
        while cond652:
            _t1271 = self.parse_fragment_id()
            item653 = _t1271
            xs651.append(item653)
            cond652 = self.match_lookahead_literal(":", 0)
        fragment_ids654 = xs651
        self.consume_literal(")")
        _t1272 = transactions_pb2.Sync(fragments=fragment_ids654)
        result656 = _t1272
        self.record_span(span_start655, "Sync")
        return result656

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start658 = self.span_start()
        self.consume_literal(":")
        symbol657 = self.consume_terminal("SYMBOL")
        result659 = fragments_pb2.FragmentId(id=symbol657.encode())
        self.record_span(span_start658, "FragmentId")
        return result659

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start662 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1274 = self.parse_epoch_writes()
            _t1273 = _t1274
        else:
            _t1273 = None
        epoch_writes660 = _t1273
        if self.match_lookahead_literal("(", 0):
            _t1276 = self.parse_epoch_reads()
            _t1275 = _t1276
        else:
            _t1275 = None
        epoch_reads661 = _t1275
        self.consume_literal(")")
        _t1277 = transactions_pb2.Epoch(writes=(epoch_writes660 if epoch_writes660 is not None else []), reads=(epoch_reads661 if epoch_reads661 is not None else []))
        result663 = _t1277
        self.record_span(span_start662, "Epoch")
        return result663

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs664 = []
        cond665 = self.match_lookahead_literal("(", 0)
        while cond665:
            _t1278 = self.parse_write()
            item666 = _t1278
            xs664.append(item666)
            cond665 = self.match_lookahead_literal("(", 0)
        writes667 = xs664
        self.consume_literal(")")
        return writes667

    def parse_write(self) -> transactions_pb2.Write:
        span_start673 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1280 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1281 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1282 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1283 = 2
                        else:
                            _t1283 = -1
                        _t1282 = _t1283
                    _t1281 = _t1282
                _t1280 = _t1281
            _t1279 = _t1280
        else:
            _t1279 = -1
        prediction668 = _t1279
        if prediction668 == 3:
            _t1285 = self.parse_snapshot()
            snapshot672 = _t1285
            _t1286 = transactions_pb2.Write(snapshot=snapshot672)
            _t1284 = _t1286
        else:
            if prediction668 == 2:
                _t1288 = self.parse_context()
                context671 = _t1288
                _t1289 = transactions_pb2.Write(context=context671)
                _t1287 = _t1289
            else:
                if prediction668 == 1:
                    _t1291 = self.parse_undefine()
                    undefine670 = _t1291
                    _t1292 = transactions_pb2.Write(undefine=undefine670)
                    _t1290 = _t1292
                else:
                    if prediction668 == 0:
                        _t1294 = self.parse_define()
                        define669 = _t1294
                        _t1295 = transactions_pb2.Write(define=define669)
                        _t1293 = _t1295
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1290 = _t1293
                _t1287 = _t1290
            _t1284 = _t1287
        result674 = _t1284
        self.record_span(span_start673, "Write")
        return result674

    def parse_define(self) -> transactions_pb2.Define:
        span_start676 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1296 = self.parse_fragment()
        fragment675 = _t1296
        self.consume_literal(")")
        _t1297 = transactions_pb2.Define(fragment=fragment675)
        result677 = _t1297
        self.record_span(span_start676, "Define")
        return result677

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start683 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1298 = self.parse_new_fragment_id()
        new_fragment_id678 = _t1298
        xs679 = []
        cond680 = self.match_lookahead_literal("(", 0)
        while cond680:
            _t1299 = self.parse_declaration()
            item681 = _t1299
            xs679.append(item681)
            cond680 = self.match_lookahead_literal("(", 0)
        declarations682 = xs679
        self.consume_literal(")")
        result684 = self.construct_fragment(new_fragment_id678, declarations682)
        self.record_span(span_start683, "Fragment")
        return result684

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start686 = self.span_start()
        _t1300 = self.parse_fragment_id()
        fragment_id685 = _t1300
        self.start_fragment(fragment_id685)
        result687 = fragment_id685
        self.record_span(span_start686, "FragmentId")
        return result687

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start693 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("functional_dependency", 1):
                _t1302 = 2
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1303 = 3
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t1304 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t1305 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t1306 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t1307 = 1
                                else:
                                    _t1307 = -1
                                _t1306 = _t1307
                            _t1305 = _t1306
                        _t1304 = _t1305
                    _t1303 = _t1304
                _t1302 = _t1303
            _t1301 = _t1302
        else:
            _t1301 = -1
        prediction688 = _t1301
        if prediction688 == 3:
            _t1309 = self.parse_data()
            data692 = _t1309
            _t1310 = logic_pb2.Declaration(data=data692)
            _t1308 = _t1310
        else:
            if prediction688 == 2:
                _t1312 = self.parse_constraint()
                constraint691 = _t1312
                _t1313 = logic_pb2.Declaration(constraint=constraint691)
                _t1311 = _t1313
            else:
                if prediction688 == 1:
                    _t1315 = self.parse_algorithm()
                    algorithm690 = _t1315
                    _t1316 = logic_pb2.Declaration(algorithm=algorithm690)
                    _t1314 = _t1316
                else:
                    if prediction688 == 0:
                        _t1318 = self.parse_def()
                        def689 = _t1318
                        _t1319 = logic_pb2.Declaration()
                        getattr(_t1319, 'def').CopyFrom(def689)
                        _t1317 = _t1319
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1314 = _t1317
                _t1311 = _t1314
            _t1308 = _t1311
        result694 = _t1308
        self.record_span(span_start693, "Declaration")
        return result694

    def parse_def(self) -> logic_pb2.Def:
        span_start698 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1320 = self.parse_relation_id()
        relation_id695 = _t1320
        _t1321 = self.parse_abstraction()
        abstraction696 = _t1321
        if self.match_lookahead_literal("(", 0):
            _t1323 = self.parse_attrs()
            _t1322 = _t1323
        else:
            _t1322 = None
        attrs697 = _t1322
        self.consume_literal(")")
        _t1324 = logic_pb2.Def(name=relation_id695, body=abstraction696, attrs=(attrs697 if attrs697 is not None else []))
        result699 = _t1324
        self.record_span(span_start698, "Def")
        return result699

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start703 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1325 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1326 = 1
            else:
                _t1326 = -1
            _t1325 = _t1326
        prediction700 = _t1325
        if prediction700 == 1:
            uint128702 = self.consume_terminal("UINT128")
            _t1327 = logic_pb2.RelationId(id_low=uint128702.low, id_high=uint128702.high)
        else:
            if prediction700 == 0:
                self.consume_literal(":")
                symbol701 = self.consume_terminal("SYMBOL")
                _t1328 = self.relation_id_from_string(symbol701)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1327 = _t1328
        result704 = _t1327
        self.record_span(span_start703, "RelationId")
        return result704

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start707 = self.span_start()
        self.consume_literal("(")
        _t1329 = self.parse_bindings()
        bindings705 = _t1329
        _t1330 = self.parse_formula()
        formula706 = _t1330
        self.consume_literal(")")
        _t1331 = logic_pb2.Abstraction(vars=(list(bindings705[0]) + list(bindings705[1] if bindings705[1] is not None else [])), value=formula706)
        result708 = _t1331
        self.record_span(span_start707, "Abstraction")
        return result708

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs709 = []
        cond710 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond710:
            _t1332 = self.parse_binding()
            item711 = _t1332
            xs709.append(item711)
            cond710 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings712 = xs709
        if self.match_lookahead_literal("|", 0):
            _t1334 = self.parse_value_bindings()
            _t1333 = _t1334
        else:
            _t1333 = None
        value_bindings713 = _t1333
        self.consume_literal("]")
        return (bindings712, (value_bindings713 if value_bindings713 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start716 = self.span_start()
        symbol714 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1335 = self.parse_type()
        type715 = _t1335
        _t1336 = logic_pb2.Var(name=symbol714)
        _t1337 = logic_pb2.Binding(var=_t1336, type=type715)
        result717 = _t1337
        self.record_span(span_start716, "Binding")
        return result717

    def parse_type(self) -> logic_pb2.Type:
        span_start733 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1338 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1339 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1340 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1341 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1342 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1343 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1344 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1345 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1346 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1347 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1348 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1349 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1350 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1351 = 9
                                                            else:
                                                                _t1351 = -1
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
                    _t1340 = _t1341
                _t1339 = _t1340
            _t1338 = _t1339
        prediction718 = _t1338
        if prediction718 == 13:
            _t1353 = self.parse_uint32_type()
            uint32_type732 = _t1353
            _t1354 = logic_pb2.Type(uint32_type=uint32_type732)
            _t1352 = _t1354
        else:
            if prediction718 == 12:
                _t1356 = self.parse_float32_type()
                float32_type731 = _t1356
                _t1357 = logic_pb2.Type(float32_type=float32_type731)
                _t1355 = _t1357
            else:
                if prediction718 == 11:
                    _t1359 = self.parse_int32_type()
                    int32_type730 = _t1359
                    _t1360 = logic_pb2.Type(int32_type=int32_type730)
                    _t1358 = _t1360
                else:
                    if prediction718 == 10:
                        _t1362 = self.parse_boolean_type()
                        boolean_type729 = _t1362
                        _t1363 = logic_pb2.Type(boolean_type=boolean_type729)
                        _t1361 = _t1363
                    else:
                        if prediction718 == 9:
                            _t1365 = self.parse_decimal_type()
                            decimal_type728 = _t1365
                            _t1366 = logic_pb2.Type(decimal_type=decimal_type728)
                            _t1364 = _t1366
                        else:
                            if prediction718 == 8:
                                _t1368 = self.parse_missing_type()
                                missing_type727 = _t1368
                                _t1369 = logic_pb2.Type(missing_type=missing_type727)
                                _t1367 = _t1369
                            else:
                                if prediction718 == 7:
                                    _t1371 = self.parse_datetime_type()
                                    datetime_type726 = _t1371
                                    _t1372 = logic_pb2.Type(datetime_type=datetime_type726)
                                    _t1370 = _t1372
                                else:
                                    if prediction718 == 6:
                                        _t1374 = self.parse_date_type()
                                        date_type725 = _t1374
                                        _t1375 = logic_pb2.Type(date_type=date_type725)
                                        _t1373 = _t1375
                                    else:
                                        if prediction718 == 5:
                                            _t1377 = self.parse_int128_type()
                                            int128_type724 = _t1377
                                            _t1378 = logic_pb2.Type(int128_type=int128_type724)
                                            _t1376 = _t1378
                                        else:
                                            if prediction718 == 4:
                                                _t1380 = self.parse_uint128_type()
                                                uint128_type723 = _t1380
                                                _t1381 = logic_pb2.Type(uint128_type=uint128_type723)
                                                _t1379 = _t1381
                                            else:
                                                if prediction718 == 3:
                                                    _t1383 = self.parse_float_type()
                                                    float_type722 = _t1383
                                                    _t1384 = logic_pb2.Type(float_type=float_type722)
                                                    _t1382 = _t1384
                                                else:
                                                    if prediction718 == 2:
                                                        _t1386 = self.parse_int_type()
                                                        int_type721 = _t1386
                                                        _t1387 = logic_pb2.Type(int_type=int_type721)
                                                        _t1385 = _t1387
                                                    else:
                                                        if prediction718 == 1:
                                                            _t1389 = self.parse_string_type()
                                                            string_type720 = _t1389
                                                            _t1390 = logic_pb2.Type(string_type=string_type720)
                                                            _t1388 = _t1390
                                                        else:
                                                            if prediction718 == 0:
                                                                _t1392 = self.parse_unspecified_type()
                                                                unspecified_type719 = _t1392
                                                                _t1393 = logic_pb2.Type(unspecified_type=unspecified_type719)
                                                                _t1391 = _t1393
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1388 = _t1391
                                                        _t1385 = _t1388
                                                    _t1382 = _t1385
                                                _t1379 = _t1382
                                            _t1376 = _t1379
                                        _t1373 = _t1376
                                    _t1370 = _t1373
                                _t1367 = _t1370
                            _t1364 = _t1367
                        _t1361 = _t1364
                    _t1358 = _t1361
                _t1355 = _t1358
            _t1352 = _t1355
        result734 = _t1352
        self.record_span(span_start733, "Type")
        return result734

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start735 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1394 = logic_pb2.UnspecifiedType()
        result736 = _t1394
        self.record_span(span_start735, "UnspecifiedType")
        return result736

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start737 = self.span_start()
        self.consume_literal("STRING")
        _t1395 = logic_pb2.StringType()
        result738 = _t1395
        self.record_span(span_start737, "StringType")
        return result738

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start739 = self.span_start()
        self.consume_literal("INT")
        _t1396 = logic_pb2.IntType()
        result740 = _t1396
        self.record_span(span_start739, "IntType")
        return result740

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start741 = self.span_start()
        self.consume_literal("FLOAT")
        _t1397 = logic_pb2.FloatType()
        result742 = _t1397
        self.record_span(span_start741, "FloatType")
        return result742

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start743 = self.span_start()
        self.consume_literal("UINT128")
        _t1398 = logic_pb2.UInt128Type()
        result744 = _t1398
        self.record_span(span_start743, "UInt128Type")
        return result744

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start745 = self.span_start()
        self.consume_literal("INT128")
        _t1399 = logic_pb2.Int128Type()
        result746 = _t1399
        self.record_span(span_start745, "Int128Type")
        return result746

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start747 = self.span_start()
        self.consume_literal("DATE")
        _t1400 = logic_pb2.DateType()
        result748 = _t1400
        self.record_span(span_start747, "DateType")
        return result748

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start749 = self.span_start()
        self.consume_literal("DATETIME")
        _t1401 = logic_pb2.DateTimeType()
        result750 = _t1401
        self.record_span(span_start749, "DateTimeType")
        return result750

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start751 = self.span_start()
        self.consume_literal("MISSING")
        _t1402 = logic_pb2.MissingType()
        result752 = _t1402
        self.record_span(span_start751, "MissingType")
        return result752

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start755 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int753 = self.consume_terminal("INT")
        int_3754 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1403 = logic_pb2.DecimalType(precision=int(int753), scale=int(int_3754))
        result756 = _t1403
        self.record_span(span_start755, "DecimalType")
        return result756

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start757 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1404 = logic_pb2.BooleanType()
        result758 = _t1404
        self.record_span(span_start757, "BooleanType")
        return result758

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start759 = self.span_start()
        self.consume_literal("INT32")
        _t1405 = logic_pb2.Int32Type()
        result760 = _t1405
        self.record_span(span_start759, "Int32Type")
        return result760

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start761 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1406 = logic_pb2.Float32Type()
        result762 = _t1406
        self.record_span(span_start761, "Float32Type")
        return result762

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start763 = self.span_start()
        self.consume_literal("UINT32")
        _t1407 = logic_pb2.UInt32Type()
        result764 = _t1407
        self.record_span(span_start763, "UInt32Type")
        return result764

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs765 = []
        cond766 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond766:
            _t1408 = self.parse_binding()
            item767 = _t1408
            xs765.append(item767)
            cond766 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings768 = xs765
        return bindings768

    def parse_formula(self) -> logic_pb2.Formula:
        span_start783 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1410 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1411 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1412 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1413 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1414 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1415 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1416 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1417 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1418 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1419 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1420 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1421 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1422 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1423 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1424 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1425 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1426 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1427 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1428 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1429 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1430 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1431 = 10
                                                                                                else:
                                                                                                    _t1431 = -1
                                                                                                _t1430 = _t1431
                                                                                            _t1429 = _t1430
                                                                                        _t1428 = _t1429
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
                                            _t1417 = _t1418
                                        _t1416 = _t1417
                                    _t1415 = _t1416
                                _t1414 = _t1415
                            _t1413 = _t1414
                        _t1412 = _t1413
                    _t1411 = _t1412
                _t1410 = _t1411
            _t1409 = _t1410
        else:
            _t1409 = -1
        prediction769 = _t1409
        if prediction769 == 12:
            _t1433 = self.parse_cast()
            cast782 = _t1433
            _t1434 = logic_pb2.Formula(cast=cast782)
            _t1432 = _t1434
        else:
            if prediction769 == 11:
                _t1436 = self.parse_rel_atom()
                rel_atom781 = _t1436
                _t1437 = logic_pb2.Formula(rel_atom=rel_atom781)
                _t1435 = _t1437
            else:
                if prediction769 == 10:
                    _t1439 = self.parse_primitive()
                    primitive780 = _t1439
                    _t1440 = logic_pb2.Formula(primitive=primitive780)
                    _t1438 = _t1440
                else:
                    if prediction769 == 9:
                        _t1442 = self.parse_pragma()
                        pragma779 = _t1442
                        _t1443 = logic_pb2.Formula(pragma=pragma779)
                        _t1441 = _t1443
                    else:
                        if prediction769 == 8:
                            _t1445 = self.parse_atom()
                            atom778 = _t1445
                            _t1446 = logic_pb2.Formula(atom=atom778)
                            _t1444 = _t1446
                        else:
                            if prediction769 == 7:
                                _t1448 = self.parse_ffi()
                                ffi777 = _t1448
                                _t1449 = logic_pb2.Formula(ffi=ffi777)
                                _t1447 = _t1449
                            else:
                                if prediction769 == 6:
                                    _t1451 = self.parse_not()
                                    not776 = _t1451
                                    _t1452 = logic_pb2.Formula()
                                    getattr(_t1452, 'not').CopyFrom(not776)
                                    _t1450 = _t1452
                                else:
                                    if prediction769 == 5:
                                        _t1454 = self.parse_disjunction()
                                        disjunction775 = _t1454
                                        _t1455 = logic_pb2.Formula(disjunction=disjunction775)
                                        _t1453 = _t1455
                                    else:
                                        if prediction769 == 4:
                                            _t1457 = self.parse_conjunction()
                                            conjunction774 = _t1457
                                            _t1458 = logic_pb2.Formula(conjunction=conjunction774)
                                            _t1456 = _t1458
                                        else:
                                            if prediction769 == 3:
                                                _t1460 = self.parse_reduce()
                                                reduce773 = _t1460
                                                _t1461 = logic_pb2.Formula(reduce=reduce773)
                                                _t1459 = _t1461
                                            else:
                                                if prediction769 == 2:
                                                    _t1463 = self.parse_exists()
                                                    exists772 = _t1463
                                                    _t1464 = logic_pb2.Formula(exists=exists772)
                                                    _t1462 = _t1464
                                                else:
                                                    if prediction769 == 1:
                                                        _t1466 = self.parse_false()
                                                        false771 = _t1466
                                                        _t1467 = logic_pb2.Formula(disjunction=false771)
                                                        _t1465 = _t1467
                                                    else:
                                                        if prediction769 == 0:
                                                            _t1469 = self.parse_true()
                                                            true770 = _t1469
                                                            _t1470 = logic_pb2.Formula(conjunction=true770)
                                                            _t1468 = _t1470
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1465 = _t1468
                                                    _t1462 = _t1465
                                                _t1459 = _t1462
                                            _t1456 = _t1459
                                        _t1453 = _t1456
                                    _t1450 = _t1453
                                _t1447 = _t1450
                            _t1444 = _t1447
                        _t1441 = _t1444
                    _t1438 = _t1441
                _t1435 = _t1438
            _t1432 = _t1435
        result784 = _t1432
        self.record_span(span_start783, "Formula")
        return result784

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start785 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1471 = logic_pb2.Conjunction(args=[])
        result786 = _t1471
        self.record_span(span_start785, "Conjunction")
        return result786

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start787 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1472 = logic_pb2.Disjunction(args=[])
        result788 = _t1472
        self.record_span(span_start787, "Disjunction")
        return result788

    def parse_exists(self) -> logic_pb2.Exists:
        span_start791 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1473 = self.parse_bindings()
        bindings789 = _t1473
        _t1474 = self.parse_formula()
        formula790 = _t1474
        self.consume_literal(")")
        _t1475 = logic_pb2.Abstraction(vars=(list(bindings789[0]) + list(bindings789[1] if bindings789[1] is not None else [])), value=formula790)
        _t1476 = logic_pb2.Exists(body=_t1475)
        result792 = _t1476
        self.record_span(span_start791, "Exists")
        return result792

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start796 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1477 = self.parse_abstraction()
        abstraction793 = _t1477
        _t1478 = self.parse_abstraction()
        abstraction_3794 = _t1478
        _t1479 = self.parse_terms()
        terms795 = _t1479
        self.consume_literal(")")
        _t1480 = logic_pb2.Reduce(op=abstraction793, body=abstraction_3794, terms=terms795)
        result797 = _t1480
        self.record_span(span_start796, "Reduce")
        return result797

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs798 = []
        cond799 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond799:
            _t1481 = self.parse_term()
            item800 = _t1481
            xs798.append(item800)
            cond799 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms801 = xs798
        self.consume_literal(")")
        return terms801

    def parse_term(self) -> logic_pb2.Term:
        span_start805 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1482 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1483 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1484 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1485 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1486 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1487 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1488 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1489 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1490 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1491 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1492 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1493 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1494 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1495 = 1
                                                            else:
                                                                _t1495 = -1
                                                            _t1494 = _t1495
                                                        _t1493 = _t1494
                                                    _t1492 = _t1493
                                                _t1491 = _t1492
                                            _t1490 = _t1491
                                        _t1489 = _t1490
                                    _t1488 = _t1489
                                _t1487 = _t1488
                            _t1486 = _t1487
                        _t1485 = _t1486
                    _t1484 = _t1485
                _t1483 = _t1484
            _t1482 = _t1483
        prediction802 = _t1482
        if prediction802 == 1:
            _t1497 = self.parse_value()
            value804 = _t1497
            _t1498 = logic_pb2.Term(constant=value804)
            _t1496 = _t1498
        else:
            if prediction802 == 0:
                _t1500 = self.parse_var()
                var803 = _t1500
                _t1501 = logic_pb2.Term(var=var803)
                _t1499 = _t1501
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1496 = _t1499
        result806 = _t1496
        self.record_span(span_start805, "Term")
        return result806

    def parse_var(self) -> logic_pb2.Var:
        span_start808 = self.span_start()
        symbol807 = self.consume_terminal("SYMBOL")
        _t1502 = logic_pb2.Var(name=symbol807)
        result809 = _t1502
        self.record_span(span_start808, "Var")
        return result809

    def parse_value(self) -> logic_pb2.Value:
        span_start823 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1503 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1504 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1505 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1507 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1508 = 0
                            else:
                                _t1508 = -1
                            _t1507 = _t1508
                        _t1506 = _t1507
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1509 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1510 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1511 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1512 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1513 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1514 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1515 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1516 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1517 = 10
                                                        else:
                                                            _t1517 = -1
                                                        _t1516 = _t1517
                                                    _t1515 = _t1516
                                                _t1514 = _t1515
                                            _t1513 = _t1514
                                        _t1512 = _t1513
                                    _t1511 = _t1512
                                _t1510 = _t1511
                            _t1509 = _t1510
                        _t1506 = _t1509
                    _t1505 = _t1506
                _t1504 = _t1505
            _t1503 = _t1504
        prediction810 = _t1503
        if prediction810 == 12:
            _t1519 = self.parse_boolean_value()
            boolean_value822 = _t1519
            _t1520 = logic_pb2.Value(boolean_value=boolean_value822)
            _t1518 = _t1520
        else:
            if prediction810 == 11:
                self.consume_literal("missing")
                _t1522 = logic_pb2.MissingValue()
                _t1523 = logic_pb2.Value(missing_value=_t1522)
                _t1521 = _t1523
            else:
                if prediction810 == 10:
                    formatted_decimal821 = self.consume_terminal("DECIMAL")
                    _t1525 = logic_pb2.Value(decimal_value=formatted_decimal821)
                    _t1524 = _t1525
                else:
                    if prediction810 == 9:
                        formatted_int128820 = self.consume_terminal("INT128")
                        _t1527 = logic_pb2.Value(int128_value=formatted_int128820)
                        _t1526 = _t1527
                    else:
                        if prediction810 == 8:
                            formatted_uint128819 = self.consume_terminal("UINT128")
                            _t1529 = logic_pb2.Value(uint128_value=formatted_uint128819)
                            _t1528 = _t1529
                        else:
                            if prediction810 == 7:
                                formatted_uint32818 = self.consume_terminal("UINT32")
                                _t1531 = logic_pb2.Value(uint32_value=formatted_uint32818)
                                _t1530 = _t1531
                            else:
                                if prediction810 == 6:
                                    formatted_float817 = self.consume_terminal("FLOAT")
                                    _t1533 = logic_pb2.Value(float_value=formatted_float817)
                                    _t1532 = _t1533
                                else:
                                    if prediction810 == 5:
                                        formatted_float32816 = self.consume_terminal("FLOAT32")
                                        _t1535 = logic_pb2.Value(float32_value=formatted_float32816)
                                        _t1534 = _t1535
                                    else:
                                        if prediction810 == 4:
                                            formatted_int815 = self.consume_terminal("INT")
                                            _t1537 = logic_pb2.Value(int_value=formatted_int815)
                                            _t1536 = _t1537
                                        else:
                                            if prediction810 == 3:
                                                formatted_int32814 = self.consume_terminal("INT32")
                                                _t1539 = logic_pb2.Value(int32_value=formatted_int32814)
                                                _t1538 = _t1539
                                            else:
                                                if prediction810 == 2:
                                                    formatted_string813 = self.consume_terminal("STRING")
                                                    _t1541 = logic_pb2.Value(string_value=formatted_string813)
                                                    _t1540 = _t1541
                                                else:
                                                    if prediction810 == 1:
                                                        _t1543 = self.parse_datetime()
                                                        datetime812 = _t1543
                                                        _t1544 = logic_pb2.Value(datetime_value=datetime812)
                                                        _t1542 = _t1544
                                                    else:
                                                        if prediction810 == 0:
                                                            _t1546 = self.parse_date()
                                                            date811 = _t1546
                                                            _t1547 = logic_pb2.Value(date_value=date811)
                                                            _t1545 = _t1547
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1542 = _t1545
                                                    _t1540 = _t1542
                                                _t1538 = _t1540
                                            _t1536 = _t1538
                                        _t1534 = _t1536
                                    _t1532 = _t1534
                                _t1530 = _t1532
                            _t1528 = _t1530
                        _t1526 = _t1528
                    _t1524 = _t1526
                _t1521 = _t1524
            _t1518 = _t1521
        result824 = _t1518
        self.record_span(span_start823, "Value")
        return result824

    def parse_date(self) -> logic_pb2.DateValue:
        span_start828 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int825 = self.consume_terminal("INT")
        formatted_int_3826 = self.consume_terminal("INT")
        formatted_int_4827 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1548 = logic_pb2.DateValue(year=int(formatted_int825), month=int(formatted_int_3826), day=int(formatted_int_4827))
        result829 = _t1548
        self.record_span(span_start828, "DateValue")
        return result829

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start837 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int830 = self.consume_terminal("INT")
        formatted_int_3831 = self.consume_terminal("INT")
        formatted_int_4832 = self.consume_terminal("INT")
        formatted_int_5833 = self.consume_terminal("INT")
        formatted_int_6834 = self.consume_terminal("INT")
        formatted_int_7835 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1549 = self.consume_terminal("INT")
        else:
            _t1549 = None
        formatted_int_8836 = _t1549
        self.consume_literal(")")
        _t1550 = logic_pb2.DateTimeValue(year=int(formatted_int830), month=int(formatted_int_3831), day=int(formatted_int_4832), hour=int(formatted_int_5833), minute=int(formatted_int_6834), second=int(formatted_int_7835), microsecond=int((formatted_int_8836 if formatted_int_8836 is not None else 0)))
        result838 = _t1550
        self.record_span(span_start837, "DateTimeValue")
        return result838

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start843 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs839 = []
        cond840 = self.match_lookahead_literal("(", 0)
        while cond840:
            _t1551 = self.parse_formula()
            item841 = _t1551
            xs839.append(item841)
            cond840 = self.match_lookahead_literal("(", 0)
        formulas842 = xs839
        self.consume_literal(")")
        _t1552 = logic_pb2.Conjunction(args=formulas842)
        result844 = _t1552
        self.record_span(span_start843, "Conjunction")
        return result844

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start849 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs845 = []
        cond846 = self.match_lookahead_literal("(", 0)
        while cond846:
            _t1553 = self.parse_formula()
            item847 = _t1553
            xs845.append(item847)
            cond846 = self.match_lookahead_literal("(", 0)
        formulas848 = xs845
        self.consume_literal(")")
        _t1554 = logic_pb2.Disjunction(args=formulas848)
        result850 = _t1554
        self.record_span(span_start849, "Disjunction")
        return result850

    def parse_not(self) -> logic_pb2.Not:
        span_start852 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1555 = self.parse_formula()
        formula851 = _t1555
        self.consume_literal(")")
        _t1556 = logic_pb2.Not(arg=formula851)
        result853 = _t1556
        self.record_span(span_start852, "Not")
        return result853

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start857 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1557 = self.parse_name()
        name854 = _t1557
        _t1558 = self.parse_ffi_args()
        ffi_args855 = _t1558
        _t1559 = self.parse_terms()
        terms856 = _t1559
        self.consume_literal(")")
        _t1560 = logic_pb2.FFI(name=name854, args=ffi_args855, terms=terms856)
        result858 = _t1560
        self.record_span(span_start857, "FFI")
        return result858

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol859 = self.consume_terminal("SYMBOL")
        return symbol859

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs860 = []
        cond861 = self.match_lookahead_literal("(", 0)
        while cond861:
            _t1561 = self.parse_abstraction()
            item862 = _t1561
            xs860.append(item862)
            cond861 = self.match_lookahead_literal("(", 0)
        abstractions863 = xs860
        self.consume_literal(")")
        return abstractions863

    def parse_atom(self) -> logic_pb2.Atom:
        span_start869 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1562 = self.parse_relation_id()
        relation_id864 = _t1562
        xs865 = []
        cond866 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond866:
            _t1563 = self.parse_term()
            item867 = _t1563
            xs865.append(item867)
            cond866 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms868 = xs865
        self.consume_literal(")")
        _t1564 = logic_pb2.Atom(name=relation_id864, terms=terms868)
        result870 = _t1564
        self.record_span(span_start869, "Atom")
        return result870

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start876 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1565 = self.parse_name()
        name871 = _t1565
        xs872 = []
        cond873 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond873:
            _t1566 = self.parse_term()
            item874 = _t1566
            xs872.append(item874)
            cond873 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms875 = xs872
        self.consume_literal(")")
        _t1567 = logic_pb2.Pragma(name=name871, terms=terms875)
        result877 = _t1567
        self.record_span(span_start876, "Pragma")
        return result877

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start893 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1569 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1570 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1571 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1572 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1573 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1574 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1575 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1576 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1577 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1578 = 7
                                                else:
                                                    _t1578 = -1
                                                _t1577 = _t1578
                                            _t1576 = _t1577
                                        _t1575 = _t1576
                                    _t1574 = _t1575
                                _t1573 = _t1574
                            _t1572 = _t1573
                        _t1571 = _t1572
                    _t1570 = _t1571
                _t1569 = _t1570
            _t1568 = _t1569
        else:
            _t1568 = -1
        prediction878 = _t1568
        if prediction878 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1580 = self.parse_name()
            name888 = _t1580
            xs889 = []
            cond890 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond890:
                _t1581 = self.parse_rel_term()
                item891 = _t1581
                xs889.append(item891)
                cond890 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms892 = xs889
            self.consume_literal(")")
            _t1582 = logic_pb2.Primitive(name=name888, terms=rel_terms892)
            _t1579 = _t1582
        else:
            if prediction878 == 8:
                _t1584 = self.parse_divide()
                divide887 = _t1584
                _t1583 = divide887
            else:
                if prediction878 == 7:
                    _t1586 = self.parse_multiply()
                    multiply886 = _t1586
                    _t1585 = multiply886
                else:
                    if prediction878 == 6:
                        _t1588 = self.parse_minus()
                        minus885 = _t1588
                        _t1587 = minus885
                    else:
                        if prediction878 == 5:
                            _t1590 = self.parse_add()
                            add884 = _t1590
                            _t1589 = add884
                        else:
                            if prediction878 == 4:
                                _t1592 = self.parse_gt_eq()
                                gt_eq883 = _t1592
                                _t1591 = gt_eq883
                            else:
                                if prediction878 == 3:
                                    _t1594 = self.parse_gt()
                                    gt882 = _t1594
                                    _t1593 = gt882
                                else:
                                    if prediction878 == 2:
                                        _t1596 = self.parse_lt_eq()
                                        lt_eq881 = _t1596
                                        _t1595 = lt_eq881
                                    else:
                                        if prediction878 == 1:
                                            _t1598 = self.parse_lt()
                                            lt880 = _t1598
                                            _t1597 = lt880
                                        else:
                                            if prediction878 == 0:
                                                _t1600 = self.parse_eq()
                                                eq879 = _t1600
                                                _t1599 = eq879
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1597 = _t1599
                                        _t1595 = _t1597
                                    _t1593 = _t1595
                                _t1591 = _t1593
                            _t1589 = _t1591
                        _t1587 = _t1589
                    _t1585 = _t1587
                _t1583 = _t1585
            _t1579 = _t1583
        result894 = _t1579
        self.record_span(span_start893, "Primitive")
        return result894

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start897 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1601 = self.parse_term()
        term895 = _t1601
        _t1602 = self.parse_term()
        term_3896 = _t1602
        self.consume_literal(")")
        _t1603 = logic_pb2.RelTerm(term=term895)
        _t1604 = logic_pb2.RelTerm(term=term_3896)
        _t1605 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1603, _t1604])
        result898 = _t1605
        self.record_span(span_start897, "Primitive")
        return result898

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start901 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1606 = self.parse_term()
        term899 = _t1606
        _t1607 = self.parse_term()
        term_3900 = _t1607
        self.consume_literal(")")
        _t1608 = logic_pb2.RelTerm(term=term899)
        _t1609 = logic_pb2.RelTerm(term=term_3900)
        _t1610 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1608, _t1609])
        result902 = _t1610
        self.record_span(span_start901, "Primitive")
        return result902

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start905 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1611 = self.parse_term()
        term903 = _t1611
        _t1612 = self.parse_term()
        term_3904 = _t1612
        self.consume_literal(")")
        _t1613 = logic_pb2.RelTerm(term=term903)
        _t1614 = logic_pb2.RelTerm(term=term_3904)
        _t1615 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1613, _t1614])
        result906 = _t1615
        self.record_span(span_start905, "Primitive")
        return result906

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start909 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1616 = self.parse_term()
        term907 = _t1616
        _t1617 = self.parse_term()
        term_3908 = _t1617
        self.consume_literal(")")
        _t1618 = logic_pb2.RelTerm(term=term907)
        _t1619 = logic_pb2.RelTerm(term=term_3908)
        _t1620 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1618, _t1619])
        result910 = _t1620
        self.record_span(span_start909, "Primitive")
        return result910

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start913 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1621 = self.parse_term()
        term911 = _t1621
        _t1622 = self.parse_term()
        term_3912 = _t1622
        self.consume_literal(")")
        _t1623 = logic_pb2.RelTerm(term=term911)
        _t1624 = logic_pb2.RelTerm(term=term_3912)
        _t1625 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1623, _t1624])
        result914 = _t1625
        self.record_span(span_start913, "Primitive")
        return result914

    def parse_add(self) -> logic_pb2.Primitive:
        span_start918 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1626 = self.parse_term()
        term915 = _t1626
        _t1627 = self.parse_term()
        term_3916 = _t1627
        _t1628 = self.parse_term()
        term_4917 = _t1628
        self.consume_literal(")")
        _t1629 = logic_pb2.RelTerm(term=term915)
        _t1630 = logic_pb2.RelTerm(term=term_3916)
        _t1631 = logic_pb2.RelTerm(term=term_4917)
        _t1632 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1629, _t1630, _t1631])
        result919 = _t1632
        self.record_span(span_start918, "Primitive")
        return result919

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start923 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1633 = self.parse_term()
        term920 = _t1633
        _t1634 = self.parse_term()
        term_3921 = _t1634
        _t1635 = self.parse_term()
        term_4922 = _t1635
        self.consume_literal(")")
        _t1636 = logic_pb2.RelTerm(term=term920)
        _t1637 = logic_pb2.RelTerm(term=term_3921)
        _t1638 = logic_pb2.RelTerm(term=term_4922)
        _t1639 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1636, _t1637, _t1638])
        result924 = _t1639
        self.record_span(span_start923, "Primitive")
        return result924

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start928 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1640 = self.parse_term()
        term925 = _t1640
        _t1641 = self.parse_term()
        term_3926 = _t1641
        _t1642 = self.parse_term()
        term_4927 = _t1642
        self.consume_literal(")")
        _t1643 = logic_pb2.RelTerm(term=term925)
        _t1644 = logic_pb2.RelTerm(term=term_3926)
        _t1645 = logic_pb2.RelTerm(term=term_4927)
        _t1646 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1643, _t1644, _t1645])
        result929 = _t1646
        self.record_span(span_start928, "Primitive")
        return result929

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start933 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1647 = self.parse_term()
        term930 = _t1647
        _t1648 = self.parse_term()
        term_3931 = _t1648
        _t1649 = self.parse_term()
        term_4932 = _t1649
        self.consume_literal(")")
        _t1650 = logic_pb2.RelTerm(term=term930)
        _t1651 = logic_pb2.RelTerm(term=term_3931)
        _t1652 = logic_pb2.RelTerm(term=term_4932)
        _t1653 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1650, _t1651, _t1652])
        result934 = _t1653
        self.record_span(span_start933, "Primitive")
        return result934

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start938 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1654 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1655 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1656 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1657 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1658 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1659 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1660 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1661 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1662 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1663 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1664 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1665 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1666 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1667 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1668 = 1
                                                                else:
                                                                    _t1668 = -1
                                                                _t1667 = _t1668
                                                            _t1666 = _t1667
                                                        _t1665 = _t1666
                                                    _t1664 = _t1665
                                                _t1663 = _t1664
                                            _t1662 = _t1663
                                        _t1661 = _t1662
                                    _t1660 = _t1661
                                _t1659 = _t1660
                            _t1658 = _t1659
                        _t1657 = _t1658
                    _t1656 = _t1657
                _t1655 = _t1656
            _t1654 = _t1655
        prediction935 = _t1654
        if prediction935 == 1:
            _t1670 = self.parse_term()
            term937 = _t1670
            _t1671 = logic_pb2.RelTerm(term=term937)
            _t1669 = _t1671
        else:
            if prediction935 == 0:
                _t1673 = self.parse_specialized_value()
                specialized_value936 = _t1673
                _t1674 = logic_pb2.RelTerm(specialized_value=specialized_value936)
                _t1672 = _t1674
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1669 = _t1672
        result939 = _t1669
        self.record_span(span_start938, "RelTerm")
        return result939

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start941 = self.span_start()
        self.consume_literal("#")
        _t1675 = self.parse_raw_value()
        raw_value940 = _t1675
        result942 = raw_value940
        self.record_span(span_start941, "Value")
        return result942

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start948 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1676 = self.parse_name()
        name943 = _t1676
        xs944 = []
        cond945 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond945:
            _t1677 = self.parse_rel_term()
            item946 = _t1677
            xs944.append(item946)
            cond945 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms947 = xs944
        self.consume_literal(")")
        _t1678 = logic_pb2.RelAtom(name=name943, terms=rel_terms947)
        result949 = _t1678
        self.record_span(span_start948, "RelAtom")
        return result949

    def parse_cast(self) -> logic_pb2.Cast:
        span_start952 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1679 = self.parse_term()
        term950 = _t1679
        _t1680 = self.parse_term()
        term_3951 = _t1680
        self.consume_literal(")")
        _t1681 = logic_pb2.Cast(input=term950, result=term_3951)
        result953 = _t1681
        self.record_span(span_start952, "Cast")
        return result953

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs954 = []
        cond955 = self.match_lookahead_literal("(", 0)
        while cond955:
            _t1682 = self.parse_attribute()
            item956 = _t1682
            xs954.append(item956)
            cond955 = self.match_lookahead_literal("(", 0)
        attributes957 = xs954
        self.consume_literal(")")
        return attributes957

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start963 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1683 = self.parse_name()
        name958 = _t1683
        xs959 = []
        cond960 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond960:
            _t1684 = self.parse_raw_value()
            item961 = _t1684
            xs959.append(item961)
            cond960 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values962 = xs959
        self.consume_literal(")")
        _t1685 = logic_pb2.Attribute(name=name958, args=raw_values962)
        result964 = _t1685
        self.record_span(span_start963, "Attribute")
        return result964

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start970 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs965 = []
        cond966 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond966:
            _t1686 = self.parse_relation_id()
            item967 = _t1686
            xs965.append(item967)
            cond966 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids968 = xs965
        _t1687 = self.parse_script()
        script969 = _t1687
        self.consume_literal(")")
        _t1688 = logic_pb2.Algorithm(body=script969)
        getattr(_t1688, 'global').extend(relation_ids968)
        result971 = _t1688
        self.record_span(span_start970, "Algorithm")
        return result971

    def parse_script(self) -> logic_pb2.Script:
        span_start976 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs972 = []
        cond973 = self.match_lookahead_literal("(", 0)
        while cond973:
            _t1689 = self.parse_construct()
            item974 = _t1689
            xs972.append(item974)
            cond973 = self.match_lookahead_literal("(", 0)
        constructs975 = xs972
        self.consume_literal(")")
        _t1690 = logic_pb2.Script(constructs=constructs975)
        result977 = _t1690
        self.record_span(span_start976, "Script")
        return result977

    def parse_construct(self) -> logic_pb2.Construct:
        span_start981 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1692 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1693 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1694 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1695 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1696 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1697 = 1
                                else:
                                    _t1697 = -1
                                _t1696 = _t1697
                            _t1695 = _t1696
                        _t1694 = _t1695
                    _t1693 = _t1694
                _t1692 = _t1693
            _t1691 = _t1692
        else:
            _t1691 = -1
        prediction978 = _t1691
        if prediction978 == 1:
            _t1699 = self.parse_instruction()
            instruction980 = _t1699
            _t1700 = logic_pb2.Construct(instruction=instruction980)
            _t1698 = _t1700
        else:
            if prediction978 == 0:
                _t1702 = self.parse_loop()
                loop979 = _t1702
                _t1703 = logic_pb2.Construct(loop=loop979)
                _t1701 = _t1703
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1698 = _t1701
        result982 = _t1698
        self.record_span(span_start981, "Construct")
        return result982

    def parse_loop(self) -> logic_pb2.Loop:
        span_start985 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1704 = self.parse_init()
        init983 = _t1704
        _t1705 = self.parse_script()
        script984 = _t1705
        self.consume_literal(")")
        _t1706 = logic_pb2.Loop(init=init983, body=script984)
        result986 = _t1706
        self.record_span(span_start985, "Loop")
        return result986

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs987 = []
        cond988 = self.match_lookahead_literal("(", 0)
        while cond988:
            _t1707 = self.parse_instruction()
            item989 = _t1707
            xs987.append(item989)
            cond988 = self.match_lookahead_literal("(", 0)
        instructions990 = xs987
        self.consume_literal(")")
        return instructions990

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start997 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1709 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1710 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1711 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1712 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1713 = 0
                            else:
                                _t1713 = -1
                            _t1712 = _t1713
                        _t1711 = _t1712
                    _t1710 = _t1711
                _t1709 = _t1710
            _t1708 = _t1709
        else:
            _t1708 = -1
        prediction991 = _t1708
        if prediction991 == 4:
            _t1715 = self.parse_monus_def()
            monus_def996 = _t1715
            _t1716 = logic_pb2.Instruction(monus_def=monus_def996)
            _t1714 = _t1716
        else:
            if prediction991 == 3:
                _t1718 = self.parse_monoid_def()
                monoid_def995 = _t1718
                _t1719 = logic_pb2.Instruction(monoid_def=monoid_def995)
                _t1717 = _t1719
            else:
                if prediction991 == 2:
                    _t1721 = self.parse_break()
                    break994 = _t1721
                    _t1722 = logic_pb2.Instruction()
                    getattr(_t1722, 'break').CopyFrom(break994)
                    _t1720 = _t1722
                else:
                    if prediction991 == 1:
                        _t1724 = self.parse_upsert()
                        upsert993 = _t1724
                        _t1725 = logic_pb2.Instruction(upsert=upsert993)
                        _t1723 = _t1725
                    else:
                        if prediction991 == 0:
                            _t1727 = self.parse_assign()
                            assign992 = _t1727
                            _t1728 = logic_pb2.Instruction(assign=assign992)
                            _t1726 = _t1728
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1723 = _t1726
                    _t1720 = _t1723
                _t1717 = _t1720
            _t1714 = _t1717
        result998 = _t1714
        self.record_span(span_start997, "Instruction")
        return result998

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1002 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1729 = self.parse_relation_id()
        relation_id999 = _t1729
        _t1730 = self.parse_abstraction()
        abstraction1000 = _t1730
        if self.match_lookahead_literal("(", 0):
            _t1732 = self.parse_attrs()
            _t1731 = _t1732
        else:
            _t1731 = None
        attrs1001 = _t1731
        self.consume_literal(")")
        _t1733 = logic_pb2.Assign(name=relation_id999, body=abstraction1000, attrs=(attrs1001 if attrs1001 is not None else []))
        result1003 = _t1733
        self.record_span(span_start1002, "Assign")
        return result1003

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1007 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1734 = self.parse_relation_id()
        relation_id1004 = _t1734
        _t1735 = self.parse_abstraction_with_arity()
        abstraction_with_arity1005 = _t1735
        if self.match_lookahead_literal("(", 0):
            _t1737 = self.parse_attrs()
            _t1736 = _t1737
        else:
            _t1736 = None
        attrs1006 = _t1736
        self.consume_literal(")")
        _t1738 = logic_pb2.Upsert(name=relation_id1004, body=abstraction_with_arity1005[0], attrs=(attrs1006 if attrs1006 is not None else []), value_arity=abstraction_with_arity1005[1])
        result1008 = _t1738
        self.record_span(span_start1007, "Upsert")
        return result1008

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1739 = self.parse_bindings()
        bindings1009 = _t1739
        _t1740 = self.parse_formula()
        formula1010 = _t1740
        self.consume_literal(")")
        _t1741 = logic_pb2.Abstraction(vars=(list(bindings1009[0]) + list(bindings1009[1] if bindings1009[1] is not None else [])), value=formula1010)
        return (_t1741, len(bindings1009[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1014 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1742 = self.parse_relation_id()
        relation_id1011 = _t1742
        _t1743 = self.parse_abstraction()
        abstraction1012 = _t1743
        if self.match_lookahead_literal("(", 0):
            _t1745 = self.parse_attrs()
            _t1744 = _t1745
        else:
            _t1744 = None
        attrs1013 = _t1744
        self.consume_literal(")")
        _t1746 = logic_pb2.Break(name=relation_id1011, body=abstraction1012, attrs=(attrs1013 if attrs1013 is not None else []))
        result1015 = _t1746
        self.record_span(span_start1014, "Break")
        return result1015

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1020 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1747 = self.parse_monoid()
        monoid1016 = _t1747
        _t1748 = self.parse_relation_id()
        relation_id1017 = _t1748
        _t1749 = self.parse_abstraction_with_arity()
        abstraction_with_arity1018 = _t1749
        if self.match_lookahead_literal("(", 0):
            _t1751 = self.parse_attrs()
            _t1750 = _t1751
        else:
            _t1750 = None
        attrs1019 = _t1750
        self.consume_literal(")")
        _t1752 = logic_pb2.MonoidDef(monoid=monoid1016, name=relation_id1017, body=abstraction_with_arity1018[0], attrs=(attrs1019 if attrs1019 is not None else []), value_arity=abstraction_with_arity1018[1])
        result1021 = _t1752
        self.record_span(span_start1020, "MonoidDef")
        return result1021

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1027 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1754 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1755 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1756 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1757 = 2
                        else:
                            _t1757 = -1
                        _t1756 = _t1757
                    _t1755 = _t1756
                _t1754 = _t1755
            _t1753 = _t1754
        else:
            _t1753 = -1
        prediction1022 = _t1753
        if prediction1022 == 3:
            _t1759 = self.parse_sum_monoid()
            sum_monoid1026 = _t1759
            _t1760 = logic_pb2.Monoid(sum_monoid=sum_monoid1026)
            _t1758 = _t1760
        else:
            if prediction1022 == 2:
                _t1762 = self.parse_max_monoid()
                max_monoid1025 = _t1762
                _t1763 = logic_pb2.Monoid(max_monoid=max_monoid1025)
                _t1761 = _t1763
            else:
                if prediction1022 == 1:
                    _t1765 = self.parse_min_monoid()
                    min_monoid1024 = _t1765
                    _t1766 = logic_pb2.Monoid(min_monoid=min_monoid1024)
                    _t1764 = _t1766
                else:
                    if prediction1022 == 0:
                        _t1768 = self.parse_or_monoid()
                        or_monoid1023 = _t1768
                        _t1769 = logic_pb2.Monoid(or_monoid=or_monoid1023)
                        _t1767 = _t1769
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1764 = _t1767
                _t1761 = _t1764
            _t1758 = _t1761
        result1028 = _t1758
        self.record_span(span_start1027, "Monoid")
        return result1028

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1029 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1770 = logic_pb2.OrMonoid()
        result1030 = _t1770
        self.record_span(span_start1029, "OrMonoid")
        return result1030

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1032 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1771 = self.parse_type()
        type1031 = _t1771
        self.consume_literal(")")
        _t1772 = logic_pb2.MinMonoid(type=type1031)
        result1033 = _t1772
        self.record_span(span_start1032, "MinMonoid")
        return result1033

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1035 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1773 = self.parse_type()
        type1034 = _t1773
        self.consume_literal(")")
        _t1774 = logic_pb2.MaxMonoid(type=type1034)
        result1036 = _t1774
        self.record_span(span_start1035, "MaxMonoid")
        return result1036

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1038 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1775 = self.parse_type()
        type1037 = _t1775
        self.consume_literal(")")
        _t1776 = logic_pb2.SumMonoid(type=type1037)
        result1039 = _t1776
        self.record_span(span_start1038, "SumMonoid")
        return result1039

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1044 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1777 = self.parse_monoid()
        monoid1040 = _t1777
        _t1778 = self.parse_relation_id()
        relation_id1041 = _t1778
        _t1779 = self.parse_abstraction_with_arity()
        abstraction_with_arity1042 = _t1779
        if self.match_lookahead_literal("(", 0):
            _t1781 = self.parse_attrs()
            _t1780 = _t1781
        else:
            _t1780 = None
        attrs1043 = _t1780
        self.consume_literal(")")
        _t1782 = logic_pb2.MonusDef(monoid=monoid1040, name=relation_id1041, body=abstraction_with_arity1042[0], attrs=(attrs1043 if attrs1043 is not None else []), value_arity=abstraction_with_arity1042[1])
        result1045 = _t1782
        self.record_span(span_start1044, "MonusDef")
        return result1045

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1050 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1783 = self.parse_relation_id()
        relation_id1046 = _t1783
        _t1784 = self.parse_abstraction()
        abstraction1047 = _t1784
        _t1785 = self.parse_functional_dependency_keys()
        functional_dependency_keys1048 = _t1785
        _t1786 = self.parse_functional_dependency_values()
        functional_dependency_values1049 = _t1786
        self.consume_literal(")")
        _t1787 = logic_pb2.FunctionalDependency(guard=abstraction1047, keys=functional_dependency_keys1048, values=functional_dependency_values1049)
        _t1788 = logic_pb2.Constraint(name=relation_id1046, functional_dependency=_t1787)
        result1051 = _t1788
        self.record_span(span_start1050, "Constraint")
        return result1051

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1052 = []
        cond1053 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1053:
            _t1789 = self.parse_var()
            item1054 = _t1789
            xs1052.append(item1054)
            cond1053 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1055 = xs1052
        self.consume_literal(")")
        return vars1055

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1056 = []
        cond1057 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1057:
            _t1790 = self.parse_var()
            item1058 = _t1790
            xs1056.append(item1058)
            cond1057 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1059 = xs1056
        self.consume_literal(")")
        return vars1059

    def parse_data(self) -> logic_pb2.Data:
        span_start1064 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("edb", 1):
                _t1792 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1793 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1794 = 1
                    else:
                        _t1794 = -1
                    _t1793 = _t1794
                _t1792 = _t1793
            _t1791 = _t1792
        else:
            _t1791 = -1
        prediction1060 = _t1791
        if prediction1060 == 2:
            _t1796 = self.parse_csv_data()
            csv_data1063 = _t1796
            _t1797 = logic_pb2.Data(csv_data=csv_data1063)
            _t1795 = _t1797
        else:
            if prediction1060 == 1:
                _t1799 = self.parse_betree_relation()
                betree_relation1062 = _t1799
                _t1800 = logic_pb2.Data(betree_relation=betree_relation1062)
                _t1798 = _t1800
            else:
                if prediction1060 == 0:
                    _t1802 = self.parse_edb()
                    edb1061 = _t1802
                    _t1803 = logic_pb2.Data(edb=edb1061)
                    _t1801 = _t1803
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1798 = _t1801
            _t1795 = _t1798
        result1065 = _t1795
        self.record_span(span_start1064, "Data")
        return result1065

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1069 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1804 = self.parse_relation_id()
        relation_id1066 = _t1804
        _t1805 = self.parse_edb_path()
        edb_path1067 = _t1805
        _t1806 = self.parse_edb_types()
        edb_types1068 = _t1806
        self.consume_literal(")")
        _t1807 = logic_pb2.EDB(target_id=relation_id1066, path=edb_path1067, types=edb_types1068)
        result1070 = _t1807
        self.record_span(span_start1069, "EDB")
        return result1070

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1071 = []
        cond1072 = self.match_lookahead_terminal("STRING", 0)
        while cond1072:
            item1073 = self.consume_terminal("STRING")
            xs1071.append(item1073)
            cond1072 = self.match_lookahead_terminal("STRING", 0)
        strings1074 = xs1071
        self.consume_literal("]")
        return strings1074

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1075 = []
        cond1076 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1076:
            _t1808 = self.parse_type()
            item1077 = _t1808
            xs1075.append(item1077)
            cond1076 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1078 = xs1075
        self.consume_literal("]")
        return types1078

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1081 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1809 = self.parse_relation_id()
        relation_id1079 = _t1809
        _t1810 = self.parse_betree_info()
        betree_info1080 = _t1810
        self.consume_literal(")")
        _t1811 = logic_pb2.BeTreeRelation(name=relation_id1079, relation_info=betree_info1080)
        result1082 = _t1811
        self.record_span(span_start1081, "BeTreeRelation")
        return result1082

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1086 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1812 = self.parse_betree_info_key_types()
        betree_info_key_types1083 = _t1812
        _t1813 = self.parse_betree_info_value_types()
        betree_info_value_types1084 = _t1813
        _t1814 = self.parse_config_dict()
        config_dict1085 = _t1814
        self.consume_literal(")")
        _t1815 = self.construct_betree_info(betree_info_key_types1083, betree_info_value_types1084, config_dict1085)
        result1087 = _t1815
        self.record_span(span_start1086, "BeTreeInfo")
        return result1087

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1088 = []
        cond1089 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1089:
            _t1816 = self.parse_type()
            item1090 = _t1816
            xs1088.append(item1090)
            cond1089 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1091 = xs1088
        self.consume_literal(")")
        return types1091

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1092 = []
        cond1093 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1093:
            _t1817 = self.parse_type()
            item1094 = _t1817
            xs1092.append(item1094)
            cond1093 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1095 = xs1092
        self.consume_literal(")")
        return types1095

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1100 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1818 = self.parse_csvlocator()
        csvlocator1096 = _t1818
        _t1819 = self.parse_csv_config()
        csv_config1097 = _t1819
        _t1820 = self.parse_gnf_columns()
        gnf_columns1098 = _t1820
        _t1821 = self.parse_csv_asof()
        csv_asof1099 = _t1821
        self.consume_literal(")")
        _t1822 = logic_pb2.CSVData(locator=csvlocator1096, config=csv_config1097, columns=gnf_columns1098, asof=csv_asof1099)
        result1101 = _t1822
        self.record_span(span_start1100, "CSVData")
        return result1101

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1104 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1824 = self.parse_csv_locator_paths()
            _t1823 = _t1824
        else:
            _t1823 = None
        csv_locator_paths1102 = _t1823
        if self.match_lookahead_literal("(", 0):
            _t1826 = self.parse_csv_locator_inline_data()
            _t1825 = _t1826
        else:
            _t1825 = None
        csv_locator_inline_data1103 = _t1825
        self.consume_literal(")")
        _t1827 = logic_pb2.CSVLocator(paths=(csv_locator_paths1102 if csv_locator_paths1102 is not None else []), inline_data=(csv_locator_inline_data1103 if csv_locator_inline_data1103 is not None else "").encode())
        result1105 = _t1827
        self.record_span(span_start1104, "CSVLocator")
        return result1105

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1106 = []
        cond1107 = self.match_lookahead_terminal("STRING", 0)
        while cond1107:
            item1108 = self.consume_terminal("STRING")
            xs1106.append(item1108)
            cond1107 = self.match_lookahead_terminal("STRING", 0)
        strings1109 = xs1106
        self.consume_literal(")")
        return strings1109

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1110 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1110

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1112 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1828 = self.parse_config_dict()
        config_dict1111 = _t1828
        self.consume_literal(")")
        _t1829 = self.construct_csv_config(config_dict1111)
        result1113 = _t1829
        self.record_span(span_start1112, "CSVConfig")
        return result1113

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1114 = []
        cond1115 = self.match_lookahead_literal("(", 0)
        while cond1115:
            _t1830 = self.parse_gnf_column()
            item1116 = _t1830
            xs1114.append(item1116)
            cond1115 = self.match_lookahead_literal("(", 0)
        gnf_columns1117 = xs1114
        self.consume_literal(")")
        return gnf_columns1117

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1124 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1831 = self.parse_gnf_column_path()
        gnf_column_path1118 = _t1831
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1833 = self.parse_relation_id()
            _t1832 = _t1833
        else:
            _t1832 = None
        relation_id1119 = _t1832
        self.consume_literal("[")
        xs1120 = []
        cond1121 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1121:
            _t1834 = self.parse_type()
            item1122 = _t1834
            xs1120.append(item1122)
            cond1121 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1123 = xs1120
        self.consume_literal("]")
        self.consume_literal(")")
        _t1835 = logic_pb2.GNFColumn(column_path=gnf_column_path1118, target_id=relation_id1119, types=types1123)
        result1125 = _t1835
        self.record_span(span_start1124, "GNFColumn")
        return result1125

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1836 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1837 = 0
            else:
                _t1837 = -1
            _t1836 = _t1837
        prediction1126 = _t1836
        if prediction1126 == 1:
            self.consume_literal("[")
            xs1128 = []
            cond1129 = self.match_lookahead_terminal("STRING", 0)
            while cond1129:
                item1130 = self.consume_terminal("STRING")
                xs1128.append(item1130)
                cond1129 = self.match_lookahead_terminal("STRING", 0)
            strings1131 = xs1128
            self.consume_literal("]")
            _t1838 = strings1131
        else:
            if prediction1126 == 0:
                string1127 = self.consume_terminal("STRING")
                _t1839 = [string1127]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1838 = _t1839
        return _t1838

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1132 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1132

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1134 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1840 = self.parse_fragment_id()
        fragment_id1133 = _t1840
        self.consume_literal(")")
        _t1841 = transactions_pb2.Undefine(fragment_id=fragment_id1133)
        result1135 = _t1841
        self.record_span(span_start1134, "Undefine")
        return result1135

    def parse_context(self) -> transactions_pb2.Context:
        span_start1140 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1136 = []
        cond1137 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1137:
            _t1842 = self.parse_relation_id()
            item1138 = _t1842
            xs1136.append(item1138)
            cond1137 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1139 = xs1136
        self.consume_literal(")")
        _t1843 = transactions_pb2.Context(relations=relation_ids1139)
        result1141 = _t1843
        self.record_span(span_start1140, "Context")
        return result1141

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1146 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1142 = []
        cond1143 = self.match_lookahead_literal("[", 0)
        while cond1143:
            _t1844 = self.parse_snapshot_mapping()
            item1144 = _t1844
            xs1142.append(item1144)
            cond1143 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1145 = xs1142
        self.consume_literal(")")
        _t1845 = transactions_pb2.Snapshot(mappings=snapshot_mappings1145)
        result1147 = _t1845
        self.record_span(span_start1146, "Snapshot")
        return result1147

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1150 = self.span_start()
        _t1846 = self.parse_edb_path()
        edb_path1148 = _t1846
        _t1847 = self.parse_relation_id()
        relation_id1149 = _t1847
        _t1848 = transactions_pb2.SnapshotMapping(destination_path=edb_path1148, source_relation=relation_id1149)
        result1151 = _t1848
        self.record_span(span_start1150, "SnapshotMapping")
        return result1151

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1152 = []
        cond1153 = self.match_lookahead_literal("(", 0)
        while cond1153:
            _t1849 = self.parse_read()
            item1154 = _t1849
            xs1152.append(item1154)
            cond1153 = self.match_lookahead_literal("(", 0)
        reads1155 = xs1152
        self.consume_literal(")")
        return reads1155

    def parse_read(self) -> transactions_pb2.Read:
        span_start1162 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1851 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1852 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1853 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1854 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1855 = 3
                            else:
                                _t1855 = -1
                            _t1854 = _t1855
                        _t1853 = _t1854
                    _t1852 = _t1853
                _t1851 = _t1852
            _t1850 = _t1851
        else:
            _t1850 = -1
        prediction1156 = _t1850
        if prediction1156 == 4:
            _t1857 = self.parse_export()
            export1161 = _t1857
            _t1858 = transactions_pb2.Read(export=export1161)
            _t1856 = _t1858
        else:
            if prediction1156 == 3:
                _t1860 = self.parse_abort()
                abort1160 = _t1860
                _t1861 = transactions_pb2.Read(abort=abort1160)
                _t1859 = _t1861
            else:
                if prediction1156 == 2:
                    _t1863 = self.parse_what_if()
                    what_if1159 = _t1863
                    _t1864 = transactions_pb2.Read(what_if=what_if1159)
                    _t1862 = _t1864
                else:
                    if prediction1156 == 1:
                        _t1866 = self.parse_output()
                        output1158 = _t1866
                        _t1867 = transactions_pb2.Read(output=output1158)
                        _t1865 = _t1867
                    else:
                        if prediction1156 == 0:
                            _t1869 = self.parse_demand()
                            demand1157 = _t1869
                            _t1870 = transactions_pb2.Read(demand=demand1157)
                            _t1868 = _t1870
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1865 = _t1868
                    _t1862 = _t1865
                _t1859 = _t1862
            _t1856 = _t1859
        result1163 = _t1856
        self.record_span(span_start1162, "Read")
        return result1163

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1165 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1871 = self.parse_relation_id()
        relation_id1164 = _t1871
        self.consume_literal(")")
        _t1872 = transactions_pb2.Demand(relation_id=relation_id1164)
        result1166 = _t1872
        self.record_span(span_start1165, "Demand")
        return result1166

    def parse_output(self) -> transactions_pb2.Output:
        span_start1169 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t1873 = self.parse_name()
        name1167 = _t1873
        _t1874 = self.parse_relation_id()
        relation_id1168 = _t1874
        self.consume_literal(")")
        _t1875 = transactions_pb2.Output(name=name1167, relation_id=relation_id1168)
        result1170 = _t1875
        self.record_span(span_start1169, "Output")
        return result1170

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1173 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1876 = self.parse_name()
        name1171 = _t1876
        _t1877 = self.parse_epoch()
        epoch1172 = _t1877
        self.consume_literal(")")
        _t1878 = transactions_pb2.WhatIf(branch=name1171, epoch=epoch1172)
        result1174 = _t1878
        self.record_span(span_start1173, "WhatIf")
        return result1174

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1177 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1880 = self.parse_name()
            _t1879 = _t1880
        else:
            _t1879 = None
        name1175 = _t1879
        _t1881 = self.parse_relation_id()
        relation_id1176 = _t1881
        self.consume_literal(")")
        _t1882 = transactions_pb2.Abort(name=(name1175 if name1175 is not None else "abort"), relation_id=relation_id1176)
        result1178 = _t1882
        self.record_span(span_start1177, "Abort")
        return result1178

    def parse_export(self) -> transactions_pb2.Export:
        span_start1180 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export")
        _t1883 = self.parse_export_csv_config()
        export_csv_config1179 = _t1883
        self.consume_literal(")")
        _t1884 = transactions_pb2.Export(csv_config=export_csv_config1179)
        result1181 = _t1884
        self.record_span(span_start1180, "Export")
        return result1181

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1189 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t1886 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t1887 = 1
                else:
                    _t1887 = -1
                _t1886 = _t1887
            _t1885 = _t1886
        else:
            _t1885 = -1
        prediction1182 = _t1885
        if prediction1182 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t1889 = self.parse_export_csv_path()
            export_csv_path1186 = _t1889
            _t1890 = self.parse_export_csv_columns_list()
            export_csv_columns_list1187 = _t1890
            _t1891 = self.parse_config_dict()
            config_dict1188 = _t1891
            self.consume_literal(")")
            _t1892 = self.construct_export_csv_config(export_csv_path1186, export_csv_columns_list1187, config_dict1188)
            _t1888 = _t1892
        else:
            if prediction1182 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t1894 = self.parse_export_csv_path()
                export_csv_path1183 = _t1894
                _t1895 = self.parse_export_csv_source()
                export_csv_source1184 = _t1895
                _t1896 = self.parse_csv_config()
                csv_config1185 = _t1896
                self.consume_literal(")")
                _t1897 = self.construct_export_csv_config_with_source(export_csv_path1183, export_csv_source1184, csv_config1185)
                _t1893 = _t1897
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1888 = _t1893
        result1190 = _t1888
        self.record_span(span_start1189, "ExportCSVConfig")
        return result1190

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1191 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1191

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1198 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t1899 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t1900 = 0
                else:
                    _t1900 = -1
                _t1899 = _t1900
            _t1898 = _t1899
        else:
            _t1898 = -1
        prediction1192 = _t1898
        if prediction1192 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t1902 = self.parse_relation_id()
            relation_id1197 = _t1902
            self.consume_literal(")")
            _t1903 = transactions_pb2.ExportCSVSource(table_def=relation_id1197)
            _t1901 = _t1903
        else:
            if prediction1192 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1193 = []
                cond1194 = self.match_lookahead_literal("(", 0)
                while cond1194:
                    _t1905 = self.parse_export_csv_column()
                    item1195 = _t1905
                    xs1193.append(item1195)
                    cond1194 = self.match_lookahead_literal("(", 0)
                export_csv_columns1196 = xs1193
                self.consume_literal(")")
                _t1906 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1196)
                _t1907 = transactions_pb2.ExportCSVSource(gnf_columns=_t1906)
                _t1904 = _t1907
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1901 = _t1904
        result1199 = _t1901
        self.record_span(span_start1198, "ExportCSVSource")
        return result1199

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1202 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1200 = self.consume_terminal("STRING")
        _t1908 = self.parse_relation_id()
        relation_id1201 = _t1908
        self.consume_literal(")")
        _t1909 = transactions_pb2.ExportCSVColumn(column_name=string1200, column_data=relation_id1201)
        result1203 = _t1909
        self.record_span(span_start1202, "ExportCSVColumn")
        return result1203

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1204 = []
        cond1205 = self.match_lookahead_literal("(", 0)
        while cond1205:
            _t1910 = self.parse_export_csv_column()
            item1206 = _t1910
            xs1204.append(item1206)
            cond1205 = self.match_lookahead_literal("(", 0)
        export_csv_columns1207 = xs1204
        self.consume_literal(")")
        return export_csv_columns1207


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
