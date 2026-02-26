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
        self._path: list[int] = []
        self._line_starts = _compute_line_starts(input_str)

    def _make_location(self, offset: int) -> Location:
        """Convert byte offset to Location with 1-based line/column."""
        line_idx = bisect.bisect_right(self._line_starts, offset) - 1
        col = offset - self._line_starts[line_idx]
        return Location(line_idx + 1, col + 1, offset)

    def push_path(self, n: int) -> None:
        """Push a field number onto the provenance path."""
        self._path.append(n)

    def pop_path(self) -> None:
        """Pop from the provenance path."""
        self._path.pop()

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
        self.provenance[tuple(self._path)] = span

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
            _t1911 = value.HasField("int_value")
        else:
            _t1911 = False
        if _t1911:
            assert value is not None
            return int(value.int_value)
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
        _t1940 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression)
        return _t1940

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t1941 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t1941
        _t1942 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t1942
        _t1943 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t1943
        _t1944 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t1944
        _t1945 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t1945
        _t1946 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t1946
        _t1947 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t1947
        _t1948 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t1948
        _t1949 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t1949
        _t1950 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t1950
        _t1951 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t1951

    def default_configure(self) -> transactions_pb2.Configure:
        _t1952 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t1952
        _t1953 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t1953

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
        _t1954 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t1954
        _t1955 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t1955
        _t1956 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t1956

    def export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t1957 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t1957
        _t1958 = self._extract_value_string(config.get("compression"), "")
        compression = _t1958
        _t1959 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t1959
        _t1960 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t1960
        _t1961 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t1961
        _t1962 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t1962
        _t1963 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t1963
        _t1964 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t1964

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start602 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        self.push_path(2)
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1313 = self.parse_configure()
            _t1312 = _t1313
        else:
            _t1312 = None
        configure592 = _t1312
        self.pop_path()
        self.push_path(3)
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1315 = self.parse_sync()
            _t1314 = _t1315
        else:
            _t1314 = None
        sync593 = _t1314
        self.pop_path()
        self.push_path(1)
        xs598 = []
        cond599 = self.match_lookahead_literal("(", 0)
        idx600 = 0
        while cond599:
            self.push_path(idx600)
            _t1316 = self.parse_epoch()
            item601 = _t1316
            self.pop_path()
            xs598.append(item601)
            idx600 = (idx600 + 1)
            cond599 = self.match_lookahead_literal("(", 0)
        epochs597 = xs598
        self.pop_path()
        self.consume_literal(")")
        _t1317 = self.default_configure()
        _t1318 = transactions_pb2.Transaction(epochs=epochs597, configure=(configure592 if configure592 is not None else _t1317), sync=sync593)
        result603 = _t1318
        self.record_span(span_start602)
        return result603

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start605 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1319 = self.parse_config_dict()
        config_dict604 = _t1319
        self.consume_literal(")")
        _t1320 = self.construct_configure(config_dict604)
        result606 = _t1320
        self.record_span(span_start605)
        return result606

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        span_start615 = self.span_start()
        self.consume_literal("{")
        xs611 = []
        cond612 = self.match_lookahead_literal(":", 0)
        idx613 = 0
        while cond612:
            self.push_path(idx613)
            _t1321 = self.parse_config_key_value()
            item614 = _t1321
            self.pop_path()
            xs611.append(item614)
            idx613 = (idx613 + 1)
            cond612 = self.match_lookahead_literal(":", 0)
        config_key_values610 = xs611
        self.consume_literal("}")
        result616 = config_key_values610
        self.record_span(span_start615)
        return result616

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        span_start619 = self.span_start()
        self.consume_literal(":")
        symbol617 = self.consume_terminal("SYMBOL")
        _t1322 = self.parse_value()
        value618 = _t1322
        result620 = (symbol617, value618,)
        self.record_span(span_start619)
        return result620

    def parse_value(self) -> logic_pb2.Value:
        span_start631 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1323 = 9
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1324 = 8
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1325 = 9
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1327 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1328 = 0
                            else:
                                _t1328 = -1
                            _t1327 = _t1328
                        _t1326 = _t1327
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1329 = 5
                        else:
                            if self.match_lookahead_terminal("STRING", 0):
                                _t1330 = 2
                            else:
                                if self.match_lookahead_terminal("INT128", 0):
                                    _t1331 = 6
                                else:
                                    if self.match_lookahead_terminal("INT", 0):
                                        _t1332 = 3
                                    else:
                                        if self.match_lookahead_terminal("FLOAT", 0):
                                            _t1333 = 4
                                        else:
                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                _t1334 = 7
                                            else:
                                                _t1334 = -1
                                            _t1333 = _t1334
                                        _t1332 = _t1333
                                    _t1331 = _t1332
                                _t1330 = _t1331
                            _t1329 = _t1330
                        _t1326 = _t1329
                    _t1325 = _t1326
                _t1324 = _t1325
            _t1323 = _t1324
        prediction621 = _t1323
        if prediction621 == 9:
            self.push_path(10)
            _t1336 = self.parse_boolean_value()
            boolean_value630 = _t1336
            self.pop_path()
            _t1337 = logic_pb2.Value(boolean_value=boolean_value630)
            _t1335 = _t1337
        else:
            if prediction621 == 8:
                self.consume_literal("missing")
                _t1339 = logic_pb2.MissingValue()
                _t1340 = logic_pb2.Value(missing_value=_t1339)
                _t1338 = _t1340
            else:
                if prediction621 == 7:
                    decimal629 = self.consume_terminal("DECIMAL")
                    _t1342 = logic_pb2.Value(decimal_value=decimal629)
                    _t1341 = _t1342
                else:
                    if prediction621 == 6:
                        int128628 = self.consume_terminal("INT128")
                        _t1344 = logic_pb2.Value(int128_value=int128628)
                        _t1343 = _t1344
                    else:
                        if prediction621 == 5:
                            uint128627 = self.consume_terminal("UINT128")
                            _t1346 = logic_pb2.Value(uint128_value=uint128627)
                            _t1345 = _t1346
                        else:
                            if prediction621 == 4:
                                float626 = self.consume_terminal("FLOAT")
                                _t1348 = logic_pb2.Value(float_value=float626)
                                _t1347 = _t1348
                            else:
                                if prediction621 == 3:
                                    int625 = self.consume_terminal("INT")
                                    _t1350 = logic_pb2.Value(int_value=int625)
                                    _t1349 = _t1350
                                else:
                                    if prediction621 == 2:
                                        string624 = self.consume_terminal("STRING")
                                        _t1352 = logic_pb2.Value(string_value=string624)
                                        _t1351 = _t1352
                                    else:
                                        if prediction621 == 1:
                                            self.push_path(8)
                                            _t1354 = self.parse_datetime()
                                            datetime623 = _t1354
                                            self.pop_path()
                                            _t1355 = logic_pb2.Value(datetime_value=datetime623)
                                            _t1353 = _t1355
                                        else:
                                            if prediction621 == 0:
                                                self.push_path(7)
                                                _t1357 = self.parse_date()
                                                date622 = _t1357
                                                self.pop_path()
                                                _t1358 = logic_pb2.Value(date_value=date622)
                                                _t1356 = _t1358
                                            else:
                                                raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1353 = _t1356
                                        _t1351 = _t1353
                                    _t1349 = _t1351
                                _t1347 = _t1349
                            _t1345 = _t1347
                        _t1343 = _t1345
                    _t1341 = _t1343
                _t1338 = _t1341
            _t1335 = _t1338
        result632 = _t1335
        self.record_span(span_start631)
        return result632

    def parse_date(self) -> logic_pb2.DateValue:
        span_start636 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        self.push_path(1)
        int633 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(2)
        int_3634 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(3)
        int_4635 = self.consume_terminal("INT")
        self.pop_path()
        self.consume_literal(")")
        _t1359 = logic_pb2.DateValue(year=int(int633), month=int(int_3634), day=int(int_4635))
        result637 = _t1359
        self.record_span(span_start636)
        return result637

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start645 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        self.push_path(1)
        int638 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(2)
        int_3639 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(3)
        int_4640 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(4)
        int_5641 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(5)
        int_6642 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(6)
        int_7643 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(7)
        if self.match_lookahead_terminal("INT", 0):
            _t1360 = self.consume_terminal("INT")
        else:
            _t1360 = None
        int_8644 = _t1360
        self.pop_path()
        self.consume_literal(")")
        _t1361 = logic_pb2.DateTimeValue(year=int(int638), month=int(int_3639), day=int(int_4640), hour=int(int_5641), minute=int(int_6642), second=int(int_7643), microsecond=int((int_8644 if int_8644 is not None else 0)))
        result646 = _t1361
        self.record_span(span_start645)
        return result646

    def parse_boolean_value(self) -> bool:
        span_start648 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1362 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1363 = 1
            else:
                _t1363 = -1
            _t1362 = _t1363
        prediction647 = _t1362
        if prediction647 == 1:
            self.consume_literal("false")
            _t1364 = False
        else:
            if prediction647 == 0:
                self.consume_literal("true")
                _t1365 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1364 = _t1365
        result649 = _t1364
        self.record_span(span_start648)
        return result649

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start658 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        self.push_path(1)
        xs654 = []
        cond655 = self.match_lookahead_literal(":", 0)
        idx656 = 0
        while cond655:
            self.push_path(idx656)
            _t1366 = self.parse_fragment_id()
            item657 = _t1366
            self.pop_path()
            xs654.append(item657)
            idx656 = (idx656 + 1)
            cond655 = self.match_lookahead_literal(":", 0)
        fragment_ids653 = xs654
        self.pop_path()
        self.consume_literal(")")
        _t1367 = transactions_pb2.Sync(fragments=fragment_ids653)
        result659 = _t1367
        self.record_span(span_start658)
        return result659

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start661 = self.span_start()
        self.consume_literal(":")
        symbol660 = self.consume_terminal("SYMBOL")
        result662 = fragments_pb2.FragmentId(id=symbol660.encode())
        self.record_span(span_start661)
        return result662

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start665 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        self.push_path(1)
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1369 = self.parse_epoch_writes()
            _t1368 = _t1369
        else:
            _t1368 = None
        epoch_writes663 = _t1368
        self.pop_path()
        self.push_path(2)
        if self.match_lookahead_literal("(", 0):
            _t1371 = self.parse_epoch_reads()
            _t1370 = _t1371
        else:
            _t1370 = None
        epoch_reads664 = _t1370
        self.pop_path()
        self.consume_literal(")")
        _t1372 = transactions_pb2.Epoch(writes=(epoch_writes663 if epoch_writes663 is not None else []), reads=(epoch_reads664 if epoch_reads664 is not None else []))
        result666 = _t1372
        self.record_span(span_start665)
        return result666

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        span_start675 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("writes")
        xs671 = []
        cond672 = self.match_lookahead_literal("(", 0)
        idx673 = 0
        while cond672:
            self.push_path(idx673)
            _t1373 = self.parse_write()
            item674 = _t1373
            self.pop_path()
            xs671.append(item674)
            idx673 = (idx673 + 1)
            cond672 = self.match_lookahead_literal("(", 0)
        writes670 = xs671
        self.consume_literal(")")
        result676 = writes670
        self.record_span(span_start675)
        return result676

    def parse_write(self) -> transactions_pb2.Write:
        span_start682 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1375 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1376 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1377 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1378 = 2
                        else:
                            _t1378 = -1
                        _t1377 = _t1378
                    _t1376 = _t1377
                _t1375 = _t1376
            _t1374 = _t1375
        else:
            _t1374 = -1
        prediction677 = _t1374
        if prediction677 == 3:
            self.push_path(5)
            _t1380 = self.parse_snapshot()
            snapshot681 = _t1380
            self.pop_path()
            _t1381 = transactions_pb2.Write(snapshot=snapshot681)
            _t1379 = _t1381
        else:
            if prediction677 == 2:
                self.push_path(3)
                _t1383 = self.parse_context()
                context680 = _t1383
                self.pop_path()
                _t1384 = transactions_pb2.Write(context=context680)
                _t1382 = _t1384
            else:
                if prediction677 == 1:
                    self.push_path(2)
                    _t1386 = self.parse_undefine()
                    undefine679 = _t1386
                    self.pop_path()
                    _t1387 = transactions_pb2.Write(undefine=undefine679)
                    _t1385 = _t1387
                else:
                    if prediction677 == 0:
                        self.push_path(1)
                        _t1389 = self.parse_define()
                        define678 = _t1389
                        self.pop_path()
                        _t1390 = transactions_pb2.Write(define=define678)
                        _t1388 = _t1390
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1385 = _t1388
                _t1382 = _t1385
            _t1379 = _t1382
        result683 = _t1379
        self.record_span(span_start682)
        return result683

    def parse_define(self) -> transactions_pb2.Define:
        span_start685 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        self.push_path(1)
        _t1391 = self.parse_fragment()
        fragment684 = _t1391
        self.pop_path()
        self.consume_literal(")")
        _t1392 = transactions_pb2.Define(fragment=fragment684)
        result686 = _t1392
        self.record_span(span_start685)
        return result686

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start696 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1393 = self.parse_new_fragment_id()
        new_fragment_id687 = _t1393
        self.push_path(2)
        xs692 = []
        cond693 = self.match_lookahead_literal("(", 0)
        idx694 = 0
        while cond693:
            self.push_path(idx694)
            _t1394 = self.parse_declaration()
            item695 = _t1394
            self.pop_path()
            xs692.append(item695)
            idx694 = (idx694 + 1)
            cond693 = self.match_lookahead_literal("(", 0)
        declarations691 = xs692
        self.pop_path()
        self.consume_literal(")")
        result697 = self.construct_fragment(new_fragment_id687, declarations691)
        self.record_span(span_start696)
        return result697

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start699 = self.span_start()
        _t1395 = self.parse_fragment_id()
        fragment_id698 = _t1395
        self.start_fragment(fragment_id698)
        result700 = fragment_id698
        self.record_span(span_start699)
        return result700

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start706 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t1397 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1398 = 2
                else:
                    if self.match_lookahead_literal("def", 1):
                        _t1399 = 0
                    else:
                        if self.match_lookahead_literal("csv_data", 1):
                            _t1400 = 3
                        else:
                            if self.match_lookahead_literal("betree_relation", 1):
                                _t1401 = 3
                            else:
                                if self.match_lookahead_literal("algorithm", 1):
                                    _t1402 = 1
                                else:
                                    _t1402 = -1
                                _t1401 = _t1402
                            _t1400 = _t1401
                        _t1399 = _t1400
                    _t1398 = _t1399
                _t1397 = _t1398
            _t1396 = _t1397
        else:
            _t1396 = -1
        prediction701 = _t1396
        if prediction701 == 3:
            self.push_path(4)
            _t1404 = self.parse_data()
            data705 = _t1404
            self.pop_path()
            _t1405 = logic_pb2.Declaration(data=data705)
            _t1403 = _t1405
        else:
            if prediction701 == 2:
                self.push_path(3)
                _t1407 = self.parse_constraint()
                constraint704 = _t1407
                self.pop_path()
                _t1408 = logic_pb2.Declaration(constraint=constraint704)
                _t1406 = _t1408
            else:
                if prediction701 == 1:
                    self.push_path(2)
                    _t1410 = self.parse_algorithm()
                    algorithm703 = _t1410
                    self.pop_path()
                    _t1411 = logic_pb2.Declaration(algorithm=algorithm703)
                    _t1409 = _t1411
                else:
                    if prediction701 == 0:
                        self.push_path(1)
                        _t1413 = self.parse_def()
                        def702 = _t1413
                        self.pop_path()
                        _t1414 = logic_pb2.Declaration()
                        getattr(_t1414, 'def').CopyFrom(def702)
                        _t1412 = _t1414
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1409 = _t1412
                _t1406 = _t1409
            _t1403 = _t1406
        result707 = _t1403
        self.record_span(span_start706)
        return result707

    def parse_def(self) -> logic_pb2.Def:
        span_start711 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        self.push_path(1)
        _t1415 = self.parse_relation_id()
        relation_id708 = _t1415
        self.pop_path()
        self.push_path(2)
        _t1416 = self.parse_abstraction()
        abstraction709 = _t1416
        self.pop_path()
        self.push_path(3)
        if self.match_lookahead_literal("(", 0):
            _t1418 = self.parse_attrs()
            _t1417 = _t1418
        else:
            _t1417 = None
        attrs710 = _t1417
        self.pop_path()
        self.consume_literal(")")
        _t1419 = logic_pb2.Def(name=relation_id708, body=abstraction709, attrs=(attrs710 if attrs710 is not None else []))
        result712 = _t1419
        self.record_span(span_start711)
        return result712

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start716 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1420 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1421 = 1
            else:
                _t1421 = -1
            _t1420 = _t1421
        prediction713 = _t1420
        if prediction713 == 1:
            uint128715 = self.consume_terminal("UINT128")
            _t1422 = logic_pb2.RelationId(id_low=uint128715.low, id_high=uint128715.high)
        else:
            if prediction713 == 0:
                self.consume_literal(":")
                symbol714 = self.consume_terminal("SYMBOL")
                _t1423 = self.relation_id_from_string(symbol714)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1422 = _t1423
        result717 = _t1422
        self.record_span(span_start716)
        return result717

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start720 = self.span_start()
        self.consume_literal("(")
        _t1424 = self.parse_bindings()
        bindings718 = _t1424
        self.push_path(2)
        _t1425 = self.parse_formula()
        formula719 = _t1425
        self.pop_path()
        self.consume_literal(")")
        _t1426 = logic_pb2.Abstraction(vars=(list(bindings718[0]) + list(bindings718[1] if bindings718[1] is not None else [])), value=formula719)
        result721 = _t1426
        self.record_span(span_start720)
        return result721

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        span_start731 = self.span_start()
        self.consume_literal("[")
        xs726 = []
        cond727 = self.match_lookahead_terminal("SYMBOL", 0)
        idx728 = 0
        while cond727:
            self.push_path(idx728)
            _t1427 = self.parse_binding()
            item729 = _t1427
            self.pop_path()
            xs726.append(item729)
            idx728 = (idx728 + 1)
            cond727 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings725 = xs726
        if self.match_lookahead_literal("|", 0):
            _t1429 = self.parse_value_bindings()
            _t1428 = _t1429
        else:
            _t1428 = None
        value_bindings730 = _t1428
        self.consume_literal("]")
        result732 = (bindings725, (value_bindings730 if value_bindings730 is not None else []),)
        self.record_span(span_start731)
        return result732

    def parse_binding(self) -> logic_pb2.Binding:
        span_start735 = self.span_start()
        symbol733 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        self.push_path(2)
        _t1430 = self.parse_type()
        type734 = _t1430
        self.pop_path()
        _t1431 = logic_pb2.Var(name=symbol733)
        _t1432 = logic_pb2.Binding(var=_t1431, type=type734)
        result736 = _t1432
        self.record_span(span_start735)
        return result736

    def parse_type(self) -> logic_pb2.Type:
        span_start749 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1433 = 0
        else:
            if self.match_lookahead_literal("UINT128", 0):
                _t1434 = 4
            else:
                if self.match_lookahead_literal("STRING", 0):
                    _t1435 = 1
                else:
                    if self.match_lookahead_literal("MISSING", 0):
                        _t1436 = 8
                    else:
                        if self.match_lookahead_literal("INT128", 0):
                            _t1437 = 5
                        else:
                            if self.match_lookahead_literal("INT", 0):
                                _t1438 = 2
                            else:
                                if self.match_lookahead_literal("FLOAT", 0):
                                    _t1439 = 3
                                else:
                                    if self.match_lookahead_literal("DATETIME", 0):
                                        _t1440 = 7
                                    else:
                                        if self.match_lookahead_literal("DATE", 0):
                                            _t1441 = 6
                                        else:
                                            if self.match_lookahead_literal("BOOLEAN", 0):
                                                _t1442 = 10
                                            else:
                                                if self.match_lookahead_literal("(", 0):
                                                    _t1443 = 9
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
        prediction737 = _t1433
        if prediction737 == 10:
            self.push_path(11)
            _t1445 = self.parse_boolean_type()
            boolean_type748 = _t1445
            self.pop_path()
            _t1446 = logic_pb2.Type(boolean_type=boolean_type748)
            _t1444 = _t1446
        else:
            if prediction737 == 9:
                self.push_path(10)
                _t1448 = self.parse_decimal_type()
                decimal_type747 = _t1448
                self.pop_path()
                _t1449 = logic_pb2.Type(decimal_type=decimal_type747)
                _t1447 = _t1449
            else:
                if prediction737 == 8:
                    self.push_path(9)
                    _t1451 = self.parse_missing_type()
                    missing_type746 = _t1451
                    self.pop_path()
                    _t1452 = logic_pb2.Type(missing_type=missing_type746)
                    _t1450 = _t1452
                else:
                    if prediction737 == 7:
                        self.push_path(8)
                        _t1454 = self.parse_datetime_type()
                        datetime_type745 = _t1454
                        self.pop_path()
                        _t1455 = logic_pb2.Type(datetime_type=datetime_type745)
                        _t1453 = _t1455
                    else:
                        if prediction737 == 6:
                            self.push_path(7)
                            _t1457 = self.parse_date_type()
                            date_type744 = _t1457
                            self.pop_path()
                            _t1458 = logic_pb2.Type(date_type=date_type744)
                            _t1456 = _t1458
                        else:
                            if prediction737 == 5:
                                self.push_path(6)
                                _t1460 = self.parse_int128_type()
                                int128_type743 = _t1460
                                self.pop_path()
                                _t1461 = logic_pb2.Type(int128_type=int128_type743)
                                _t1459 = _t1461
                            else:
                                if prediction737 == 4:
                                    self.push_path(5)
                                    _t1463 = self.parse_uint128_type()
                                    uint128_type742 = _t1463
                                    self.pop_path()
                                    _t1464 = logic_pb2.Type(uint128_type=uint128_type742)
                                    _t1462 = _t1464
                                else:
                                    if prediction737 == 3:
                                        self.push_path(4)
                                        _t1466 = self.parse_float_type()
                                        float_type741 = _t1466
                                        self.pop_path()
                                        _t1467 = logic_pb2.Type(float_type=float_type741)
                                        _t1465 = _t1467
                                    else:
                                        if prediction737 == 2:
                                            self.push_path(3)
                                            _t1469 = self.parse_int_type()
                                            int_type740 = _t1469
                                            self.pop_path()
                                            _t1470 = logic_pb2.Type(int_type=int_type740)
                                            _t1468 = _t1470
                                        else:
                                            if prediction737 == 1:
                                                self.push_path(2)
                                                _t1472 = self.parse_string_type()
                                                string_type739 = _t1472
                                                self.pop_path()
                                                _t1473 = logic_pb2.Type(string_type=string_type739)
                                                _t1471 = _t1473
                                            else:
                                                if prediction737 == 0:
                                                    self.push_path(1)
                                                    _t1475 = self.parse_unspecified_type()
                                                    unspecified_type738 = _t1475
                                                    self.pop_path()
                                                    _t1476 = logic_pb2.Type(unspecified_type=unspecified_type738)
                                                    _t1474 = _t1476
                                                else:
                                                    raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                _t1471 = _t1474
                                            _t1468 = _t1471
                                        _t1465 = _t1468
                                    _t1462 = _t1465
                                _t1459 = _t1462
                            _t1456 = _t1459
                        _t1453 = _t1456
                    _t1450 = _t1453
                _t1447 = _t1450
            _t1444 = _t1447
        result750 = _t1444
        self.record_span(span_start749)
        return result750

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start751 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1477 = logic_pb2.UnspecifiedType()
        result752 = _t1477
        self.record_span(span_start751)
        return result752

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start753 = self.span_start()
        self.consume_literal("STRING")
        _t1478 = logic_pb2.StringType()
        result754 = _t1478
        self.record_span(span_start753)
        return result754

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start755 = self.span_start()
        self.consume_literal("INT")
        _t1479 = logic_pb2.IntType()
        result756 = _t1479
        self.record_span(span_start755)
        return result756

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start757 = self.span_start()
        self.consume_literal("FLOAT")
        _t1480 = logic_pb2.FloatType()
        result758 = _t1480
        self.record_span(span_start757)
        return result758

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start759 = self.span_start()
        self.consume_literal("UINT128")
        _t1481 = logic_pb2.UInt128Type()
        result760 = _t1481
        self.record_span(span_start759)
        return result760

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start761 = self.span_start()
        self.consume_literal("INT128")
        _t1482 = logic_pb2.Int128Type()
        result762 = _t1482
        self.record_span(span_start761)
        return result762

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start763 = self.span_start()
        self.consume_literal("DATE")
        _t1483 = logic_pb2.DateType()
        result764 = _t1483
        self.record_span(span_start763)
        return result764

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start765 = self.span_start()
        self.consume_literal("DATETIME")
        _t1484 = logic_pb2.DateTimeType()
        result766 = _t1484
        self.record_span(span_start765)
        return result766

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start767 = self.span_start()
        self.consume_literal("MISSING")
        _t1485 = logic_pb2.MissingType()
        result768 = _t1485
        self.record_span(span_start767)
        return result768

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start771 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        self.push_path(1)
        int769 = self.consume_terminal("INT")
        self.pop_path()
        self.push_path(2)
        int_3770 = self.consume_terminal("INT")
        self.pop_path()
        self.consume_literal(")")
        _t1486 = logic_pb2.DecimalType(precision=int(int769), scale=int(int_3770))
        result772 = _t1486
        self.record_span(span_start771)
        return result772

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start773 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1487 = logic_pb2.BooleanType()
        result774 = _t1487
        self.record_span(span_start773)
        return result774

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        span_start783 = self.span_start()
        self.consume_literal("|")
        xs779 = []
        cond780 = self.match_lookahead_terminal("SYMBOL", 0)
        idx781 = 0
        while cond780:
            self.push_path(idx781)
            _t1488 = self.parse_binding()
            item782 = _t1488
            self.pop_path()
            xs779.append(item782)
            idx781 = (idx781 + 1)
            cond780 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings778 = xs779
        result784 = bindings778
        self.record_span(span_start783)
        return result784

    def parse_formula(self) -> logic_pb2.Formula:
        span_start799 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1490 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1491 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1492 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1493 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1494 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1495 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1496 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1497 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1498 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1499 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1500 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1501 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1502 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1503 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1504 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1505 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1506 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1507 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1508 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1509 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1510 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1511 = 10
                                                                                                else:
                                                                                                    _t1511 = -1
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
                                                _t1498 = _t1499
                                            _t1497 = _t1498
                                        _t1496 = _t1497
                                    _t1495 = _t1496
                                _t1494 = _t1495
                            _t1493 = _t1494
                        _t1492 = _t1493
                    _t1491 = _t1492
                _t1490 = _t1491
            _t1489 = _t1490
        else:
            _t1489 = -1
        prediction785 = _t1489
        if prediction785 == 12:
            self.push_path(11)
            _t1513 = self.parse_cast()
            cast798 = _t1513
            self.pop_path()
            _t1514 = logic_pb2.Formula(cast=cast798)
            _t1512 = _t1514
        else:
            if prediction785 == 11:
                self.push_path(10)
                _t1516 = self.parse_rel_atom()
                rel_atom797 = _t1516
                self.pop_path()
                _t1517 = logic_pb2.Formula(rel_atom=rel_atom797)
                _t1515 = _t1517
            else:
                if prediction785 == 10:
                    self.push_path(9)
                    _t1519 = self.parse_primitive()
                    primitive796 = _t1519
                    self.pop_path()
                    _t1520 = logic_pb2.Formula(primitive=primitive796)
                    _t1518 = _t1520
                else:
                    if prediction785 == 9:
                        self.push_path(8)
                        _t1522 = self.parse_pragma()
                        pragma795 = _t1522
                        self.pop_path()
                        _t1523 = logic_pb2.Formula(pragma=pragma795)
                        _t1521 = _t1523
                    else:
                        if prediction785 == 8:
                            self.push_path(7)
                            _t1525 = self.parse_atom()
                            atom794 = _t1525
                            self.pop_path()
                            _t1526 = logic_pb2.Formula(atom=atom794)
                            _t1524 = _t1526
                        else:
                            if prediction785 == 7:
                                self.push_path(6)
                                _t1528 = self.parse_ffi()
                                ffi793 = _t1528
                                self.pop_path()
                                _t1529 = logic_pb2.Formula(ffi=ffi793)
                                _t1527 = _t1529
                            else:
                                if prediction785 == 6:
                                    self.push_path(5)
                                    _t1531 = self.parse_not()
                                    not792 = _t1531
                                    self.pop_path()
                                    _t1532 = logic_pb2.Formula()
                                    getattr(_t1532, 'not').CopyFrom(not792)
                                    _t1530 = _t1532
                                else:
                                    if prediction785 == 5:
                                        self.push_path(4)
                                        _t1534 = self.parse_disjunction()
                                        disjunction791 = _t1534
                                        self.pop_path()
                                        _t1535 = logic_pb2.Formula(disjunction=disjunction791)
                                        _t1533 = _t1535
                                    else:
                                        if prediction785 == 4:
                                            self.push_path(3)
                                            _t1537 = self.parse_conjunction()
                                            conjunction790 = _t1537
                                            self.pop_path()
                                            _t1538 = logic_pb2.Formula(conjunction=conjunction790)
                                            _t1536 = _t1538
                                        else:
                                            if prediction785 == 3:
                                                self.push_path(2)
                                                _t1540 = self.parse_reduce()
                                                reduce789 = _t1540
                                                self.pop_path()
                                                _t1541 = logic_pb2.Formula(reduce=reduce789)
                                                _t1539 = _t1541
                                            else:
                                                if prediction785 == 2:
                                                    self.push_path(1)
                                                    _t1543 = self.parse_exists()
                                                    exists788 = _t1543
                                                    self.pop_path()
                                                    _t1544 = logic_pb2.Formula(exists=exists788)
                                                    _t1542 = _t1544
                                                else:
                                                    if prediction785 == 1:
                                                        self.push_path(4)
                                                        _t1546 = self.parse_false()
                                                        false787 = _t1546
                                                        self.pop_path()
                                                        _t1547 = logic_pb2.Formula(disjunction=false787)
                                                        _t1545 = _t1547
                                                    else:
                                                        if prediction785 == 0:
                                                            self.push_path(3)
                                                            _t1549 = self.parse_true()
                                                            true786 = _t1549
                                                            self.pop_path()
                                                            _t1550 = logic_pb2.Formula(conjunction=true786)
                                                            _t1548 = _t1550
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1545 = _t1548
                                                    _t1542 = _t1545
                                                _t1539 = _t1542
                                            _t1536 = _t1539
                                        _t1533 = _t1536
                                    _t1530 = _t1533
                                _t1527 = _t1530
                            _t1524 = _t1527
                        _t1521 = _t1524
                    _t1518 = _t1521
                _t1515 = _t1518
            _t1512 = _t1515
        result800 = _t1512
        self.record_span(span_start799)
        return result800

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start801 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1551 = logic_pb2.Conjunction(args=[])
        result802 = _t1551
        self.record_span(span_start801)
        return result802

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start803 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1552 = logic_pb2.Disjunction(args=[])
        result804 = _t1552
        self.record_span(span_start803)
        return result804

    def parse_exists(self) -> logic_pb2.Exists:
        span_start807 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1553 = self.parse_bindings()
        bindings805 = _t1553
        _t1554 = self.parse_formula()
        formula806 = _t1554
        self.consume_literal(")")
        _t1555 = logic_pb2.Abstraction(vars=(list(bindings805[0]) + list(bindings805[1] if bindings805[1] is not None else [])), value=formula806)
        _t1556 = logic_pb2.Exists(body=_t1555)
        result808 = _t1556
        self.record_span(span_start807)
        return result808

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start812 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        self.push_path(1)
        _t1557 = self.parse_abstraction()
        abstraction809 = _t1557
        self.pop_path()
        self.push_path(2)
        _t1558 = self.parse_abstraction()
        abstraction_3810 = _t1558
        self.pop_path()
        self.push_path(3)
        _t1559 = self.parse_terms()
        terms811 = _t1559
        self.pop_path()
        self.consume_literal(")")
        _t1560 = logic_pb2.Reduce(op=abstraction809, body=abstraction_3810, terms=terms811)
        result813 = _t1560
        self.record_span(span_start812)
        return result813

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        span_start822 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("terms")
        xs818 = []
        cond819 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        idx820 = 0
        while cond819:
            self.push_path(idx820)
            _t1561 = self.parse_term()
            item821 = _t1561
            self.pop_path()
            xs818.append(item821)
            idx820 = (idx820 + 1)
            cond819 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms817 = xs818
        self.consume_literal(")")
        result823 = terms817
        self.record_span(span_start822)
        return result823

    def parse_term(self) -> logic_pb2.Term:
        span_start827 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1562 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1563 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1564 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1565 = 1
                    else:
                        if self.match_lookahead_terminal("UINT128", 0):
                            _t1566 = 1
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1567 = 0
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1568 = 1
                                else:
                                    if self.match_lookahead_terminal("INT128", 0):
                                        _t1569 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT", 0):
                                            _t1570 = 1
                                        else:
                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                _t1571 = 1
                                            else:
                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                    _t1572 = 1
                                                else:
                                                    _t1572 = -1
                                                _t1571 = _t1572
                                            _t1570 = _t1571
                                        _t1569 = _t1570
                                    _t1568 = _t1569
                                _t1567 = _t1568
                            _t1566 = _t1567
                        _t1565 = _t1566
                    _t1564 = _t1565
                _t1563 = _t1564
            _t1562 = _t1563
        prediction824 = _t1562
        if prediction824 == 1:
            self.push_path(2)
            _t1574 = self.parse_constant()
            constant826 = _t1574
            self.pop_path()
            _t1575 = logic_pb2.Term(constant=constant826)
            _t1573 = _t1575
        else:
            if prediction824 == 0:
                self.push_path(1)
                _t1577 = self.parse_var()
                var825 = _t1577
                self.pop_path()
                _t1578 = logic_pb2.Term(var=var825)
                _t1576 = _t1578
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1573 = _t1576
        result828 = _t1573
        self.record_span(span_start827)
        return result828

    def parse_var(self) -> logic_pb2.Var:
        span_start830 = self.span_start()
        symbol829 = self.consume_terminal("SYMBOL")
        _t1579 = logic_pb2.Var(name=symbol829)
        result831 = _t1579
        self.record_span(span_start830)
        return result831

    def parse_constant(self) -> logic_pb2.Value:
        span_start833 = self.span_start()
        _t1580 = self.parse_value()
        value832 = _t1580
        result834 = value832
        self.record_span(span_start833)
        return result834

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start843 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        self.push_path(1)
        xs839 = []
        cond840 = self.match_lookahead_literal("(", 0)
        idx841 = 0
        while cond840:
            self.push_path(idx841)
            _t1581 = self.parse_formula()
            item842 = _t1581
            self.pop_path()
            xs839.append(item842)
            idx841 = (idx841 + 1)
            cond840 = self.match_lookahead_literal("(", 0)
        formulas838 = xs839
        self.pop_path()
        self.consume_literal(")")
        _t1582 = logic_pb2.Conjunction(args=formulas838)
        result844 = _t1582
        self.record_span(span_start843)
        return result844

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start853 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.push_path(1)
        xs849 = []
        cond850 = self.match_lookahead_literal("(", 0)
        idx851 = 0
        while cond850:
            self.push_path(idx851)
            _t1583 = self.parse_formula()
            item852 = _t1583
            self.pop_path()
            xs849.append(item852)
            idx851 = (idx851 + 1)
            cond850 = self.match_lookahead_literal("(", 0)
        formulas848 = xs849
        self.pop_path()
        self.consume_literal(")")
        _t1584 = logic_pb2.Disjunction(args=formulas848)
        result854 = _t1584
        self.record_span(span_start853)
        return result854

    def parse_not(self) -> logic_pb2.Not:
        span_start856 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        self.push_path(1)
        _t1585 = self.parse_formula()
        formula855 = _t1585
        self.pop_path()
        self.consume_literal(")")
        _t1586 = logic_pb2.Not(arg=formula855)
        result857 = _t1586
        self.record_span(span_start856)
        return result857

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start861 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        self.push_path(1)
        _t1587 = self.parse_name()
        name858 = _t1587
        self.pop_path()
        self.push_path(2)
        _t1588 = self.parse_ffi_args()
        ffi_args859 = _t1588
        self.pop_path()
        self.push_path(3)
        _t1589 = self.parse_terms()
        terms860 = _t1589
        self.pop_path()
        self.consume_literal(")")
        _t1590 = logic_pb2.FFI(name=name858, args=ffi_args859, terms=terms860)
        result862 = _t1590
        self.record_span(span_start861)
        return result862

    def parse_name(self) -> str:
        span_start864 = self.span_start()
        self.consume_literal(":")
        symbol863 = self.consume_terminal("SYMBOL")
        result865 = symbol863
        self.record_span(span_start864)
        return result865

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        span_start874 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("args")
        xs870 = []
        cond871 = self.match_lookahead_literal("(", 0)
        idx872 = 0
        while cond871:
            self.push_path(idx872)
            _t1591 = self.parse_abstraction()
            item873 = _t1591
            self.pop_path()
            xs870.append(item873)
            idx872 = (idx872 + 1)
            cond871 = self.match_lookahead_literal("(", 0)
        abstractions869 = xs870
        self.consume_literal(")")
        result875 = abstractions869
        self.record_span(span_start874)
        return result875

    def parse_atom(self) -> logic_pb2.Atom:
        span_start885 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        self.push_path(1)
        _t1592 = self.parse_relation_id()
        relation_id876 = _t1592
        self.pop_path()
        self.push_path(2)
        xs881 = []
        cond882 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        idx883 = 0
        while cond882:
            self.push_path(idx883)
            _t1593 = self.parse_term()
            item884 = _t1593
            self.pop_path()
            xs881.append(item884)
            idx883 = (idx883 + 1)
            cond882 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms880 = xs881
        self.pop_path()
        self.consume_literal(")")
        _t1594 = logic_pb2.Atom(name=relation_id876, terms=terms880)
        result886 = _t1594
        self.record_span(span_start885)
        return result886

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start896 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        self.push_path(1)
        _t1595 = self.parse_name()
        name887 = _t1595
        self.pop_path()
        self.push_path(2)
        xs892 = []
        cond893 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        idx894 = 0
        while cond893:
            self.push_path(idx894)
            _t1596 = self.parse_term()
            item895 = _t1596
            self.pop_path()
            xs892.append(item895)
            idx894 = (idx894 + 1)
            cond893 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        terms891 = xs892
        self.pop_path()
        self.consume_literal(")")
        _t1597 = logic_pb2.Pragma(name=name887, terms=terms891)
        result897 = _t1597
        self.record_span(span_start896)
        return result897

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start917 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1599 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1600 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1601 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1602 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1603 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1604 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1605 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1606 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1607 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1608 = 7
                                                else:
                                                    _t1608 = -1
                                                _t1607 = _t1608
                                            _t1606 = _t1607
                                        _t1605 = _t1606
                                    _t1604 = _t1605
                                _t1603 = _t1604
                            _t1602 = _t1603
                        _t1601 = _t1602
                    _t1600 = _t1601
                _t1599 = _t1600
            _t1598 = _t1599
        else:
            _t1598 = -1
        prediction898 = _t1598
        if prediction898 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            self.push_path(1)
            _t1610 = self.parse_name()
            name908 = _t1610
            self.pop_path()
            self.push_path(2)
            xs913 = []
            cond914 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            idx915 = 0
            while cond914:
                self.push_path(idx915)
                _t1611 = self.parse_rel_term()
                item916 = _t1611
                self.pop_path()
                xs913.append(item916)
                idx915 = (idx915 + 1)
                cond914 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
            rel_terms912 = xs913
            self.pop_path()
            self.consume_literal(")")
            _t1612 = logic_pb2.Primitive(name=name908, terms=rel_terms912)
            _t1609 = _t1612
        else:
            if prediction898 == 8:
                _t1614 = self.parse_divide()
                divide907 = _t1614
                _t1613 = divide907
            else:
                if prediction898 == 7:
                    _t1616 = self.parse_multiply()
                    multiply906 = _t1616
                    _t1615 = multiply906
                else:
                    if prediction898 == 6:
                        _t1618 = self.parse_minus()
                        minus905 = _t1618
                        _t1617 = minus905
                    else:
                        if prediction898 == 5:
                            _t1620 = self.parse_add()
                            add904 = _t1620
                            _t1619 = add904
                        else:
                            if prediction898 == 4:
                                _t1622 = self.parse_gt_eq()
                                gt_eq903 = _t1622
                                _t1621 = gt_eq903
                            else:
                                if prediction898 == 3:
                                    _t1624 = self.parse_gt()
                                    gt902 = _t1624
                                    _t1623 = gt902
                                else:
                                    if prediction898 == 2:
                                        _t1626 = self.parse_lt_eq()
                                        lt_eq901 = _t1626
                                        _t1625 = lt_eq901
                                    else:
                                        if prediction898 == 1:
                                            _t1628 = self.parse_lt()
                                            lt900 = _t1628
                                            _t1627 = lt900
                                        else:
                                            if prediction898 == 0:
                                                _t1630 = self.parse_eq()
                                                eq899 = _t1630
                                                _t1629 = eq899
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1627 = _t1629
                                        _t1625 = _t1627
                                    _t1623 = _t1625
                                _t1621 = _t1623
                            _t1619 = _t1621
                        _t1617 = _t1619
                    _t1615 = _t1617
                _t1613 = _t1615
            _t1609 = _t1613
        result918 = _t1609
        self.record_span(span_start917)
        return result918

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start921 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1631 = self.parse_term()
        term919 = _t1631
        _t1632 = self.parse_term()
        term_3920 = _t1632
        self.consume_literal(")")
        _t1633 = logic_pb2.RelTerm(term=term919)
        _t1634 = logic_pb2.RelTerm(term=term_3920)
        _t1635 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1633, _t1634])
        result922 = _t1635
        self.record_span(span_start921)
        return result922

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start925 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1636 = self.parse_term()
        term923 = _t1636
        _t1637 = self.parse_term()
        term_3924 = _t1637
        self.consume_literal(")")
        _t1638 = logic_pb2.RelTerm(term=term923)
        _t1639 = logic_pb2.RelTerm(term=term_3924)
        _t1640 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1638, _t1639])
        result926 = _t1640
        self.record_span(span_start925)
        return result926

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start929 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1641 = self.parse_term()
        term927 = _t1641
        _t1642 = self.parse_term()
        term_3928 = _t1642
        self.consume_literal(")")
        _t1643 = logic_pb2.RelTerm(term=term927)
        _t1644 = logic_pb2.RelTerm(term=term_3928)
        _t1645 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1643, _t1644])
        result930 = _t1645
        self.record_span(span_start929)
        return result930

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start933 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1646 = self.parse_term()
        term931 = _t1646
        _t1647 = self.parse_term()
        term_3932 = _t1647
        self.consume_literal(")")
        _t1648 = logic_pb2.RelTerm(term=term931)
        _t1649 = logic_pb2.RelTerm(term=term_3932)
        _t1650 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1648, _t1649])
        result934 = _t1650
        self.record_span(span_start933)
        return result934

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start937 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1651 = self.parse_term()
        term935 = _t1651
        _t1652 = self.parse_term()
        term_3936 = _t1652
        self.consume_literal(")")
        _t1653 = logic_pb2.RelTerm(term=term935)
        _t1654 = logic_pb2.RelTerm(term=term_3936)
        _t1655 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1653, _t1654])
        result938 = _t1655
        self.record_span(span_start937)
        return result938

    def parse_add(self) -> logic_pb2.Primitive:
        span_start942 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1656 = self.parse_term()
        term939 = _t1656
        _t1657 = self.parse_term()
        term_3940 = _t1657
        _t1658 = self.parse_term()
        term_4941 = _t1658
        self.consume_literal(")")
        _t1659 = logic_pb2.RelTerm(term=term939)
        _t1660 = logic_pb2.RelTerm(term=term_3940)
        _t1661 = logic_pb2.RelTerm(term=term_4941)
        _t1662 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1659, _t1660, _t1661])
        result943 = _t1662
        self.record_span(span_start942)
        return result943

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start947 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1663 = self.parse_term()
        term944 = _t1663
        _t1664 = self.parse_term()
        term_3945 = _t1664
        _t1665 = self.parse_term()
        term_4946 = _t1665
        self.consume_literal(")")
        _t1666 = logic_pb2.RelTerm(term=term944)
        _t1667 = logic_pb2.RelTerm(term=term_3945)
        _t1668 = logic_pb2.RelTerm(term=term_4946)
        _t1669 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1666, _t1667, _t1668])
        result948 = _t1669
        self.record_span(span_start947)
        return result948

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start952 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1670 = self.parse_term()
        term949 = _t1670
        _t1671 = self.parse_term()
        term_3950 = _t1671
        _t1672 = self.parse_term()
        term_4951 = _t1672
        self.consume_literal(")")
        _t1673 = logic_pb2.RelTerm(term=term949)
        _t1674 = logic_pb2.RelTerm(term=term_3950)
        _t1675 = logic_pb2.RelTerm(term=term_4951)
        _t1676 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1673, _t1674, _t1675])
        result953 = _t1676
        self.record_span(span_start952)
        return result953

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start957 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1677 = self.parse_term()
        term954 = _t1677
        _t1678 = self.parse_term()
        term_3955 = _t1678
        _t1679 = self.parse_term()
        term_4956 = _t1679
        self.consume_literal(")")
        _t1680 = logic_pb2.RelTerm(term=term954)
        _t1681 = logic_pb2.RelTerm(term=term_3955)
        _t1682 = logic_pb2.RelTerm(term=term_4956)
        _t1683 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1680, _t1681, _t1682])
        result958 = _t1683
        self.record_span(span_start957)
        return result958

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start962 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1684 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1685 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1686 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1687 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1688 = 0
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1689 = 1
                            else:
                                if self.match_lookahead_terminal("SYMBOL", 0):
                                    _t1690 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1691 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1692 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1693 = 1
                                            else:
                                                if self.match_lookahead_terminal("FLOAT", 0):
                                                    _t1694 = 1
                                                else:
                                                    if self.match_lookahead_terminal("DECIMAL", 0):
                                                        _t1695 = 1
                                                    else:
                                                        _t1695 = -1
                                                    _t1694 = _t1695
                                                _t1693 = _t1694
                                            _t1692 = _t1693
                                        _t1691 = _t1692
                                    _t1690 = _t1691
                                _t1689 = _t1690
                            _t1688 = _t1689
                        _t1687 = _t1688
                    _t1686 = _t1687
                _t1685 = _t1686
            _t1684 = _t1685
        prediction959 = _t1684
        if prediction959 == 1:
            self.push_path(2)
            _t1697 = self.parse_term()
            term961 = _t1697
            self.pop_path()
            _t1698 = logic_pb2.RelTerm(term=term961)
            _t1696 = _t1698
        else:
            if prediction959 == 0:
                self.push_path(1)
                _t1700 = self.parse_specialized_value()
                specialized_value960 = _t1700
                self.pop_path()
                _t1701 = logic_pb2.RelTerm(specialized_value=specialized_value960)
                _t1699 = _t1701
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1696 = _t1699
        result963 = _t1696
        self.record_span(span_start962)
        return result963

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start965 = self.span_start()
        self.consume_literal("#")
        _t1702 = self.parse_value()
        value964 = _t1702
        result966 = value964
        self.record_span(span_start965)
        return result966

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start976 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        self.push_path(3)
        _t1703 = self.parse_name()
        name967 = _t1703
        self.pop_path()
        self.push_path(2)
        xs972 = []
        cond973 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        idx974 = 0
        while cond973:
            self.push_path(idx974)
            _t1704 = self.parse_rel_term()
            item975 = _t1704
            self.pop_path()
            xs972.append(item975)
            idx974 = (idx974 + 1)
            cond973 = (((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("SYMBOL", 0)) or self.match_lookahead_terminal("UINT128", 0))
        rel_terms971 = xs972
        self.pop_path()
        self.consume_literal(")")
        _t1705 = logic_pb2.RelAtom(name=name967, terms=rel_terms971)
        result977 = _t1705
        self.record_span(span_start976)
        return result977

    def parse_cast(self) -> logic_pb2.Cast:
        span_start980 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        self.push_path(2)
        _t1706 = self.parse_term()
        term978 = _t1706
        self.pop_path()
        self.push_path(3)
        _t1707 = self.parse_term()
        term_3979 = _t1707
        self.pop_path()
        self.consume_literal(")")
        _t1708 = logic_pb2.Cast(input=term978, result=term_3979)
        result981 = _t1708
        self.record_span(span_start980)
        return result981

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        span_start990 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs986 = []
        cond987 = self.match_lookahead_literal("(", 0)
        idx988 = 0
        while cond987:
            self.push_path(idx988)
            _t1709 = self.parse_attribute()
            item989 = _t1709
            self.pop_path()
            xs986.append(item989)
            idx988 = (idx988 + 1)
            cond987 = self.match_lookahead_literal("(", 0)
        attributes985 = xs986
        self.consume_literal(")")
        result991 = attributes985
        self.record_span(span_start990)
        return result991

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1001 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        self.push_path(1)
        _t1710 = self.parse_name()
        name992 = _t1710
        self.pop_path()
        self.push_path(2)
        xs997 = []
        cond998 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        idx999 = 0
        while cond998:
            self.push_path(idx999)
            _t1711 = self.parse_value()
            item1000 = _t1711
            self.pop_path()
            xs997.append(item1000)
            idx999 = (idx999 + 1)
            cond998 = (((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0))
        values996 = xs997
        self.pop_path()
        self.consume_literal(")")
        _t1712 = logic_pb2.Attribute(name=name992, args=values996)
        result1002 = _t1712
        self.record_span(span_start1001)
        return result1002

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1012 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        self.push_path(1)
        xs1007 = []
        cond1008 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        idx1009 = 0
        while cond1008:
            self.push_path(idx1009)
            _t1713 = self.parse_relation_id()
            item1010 = _t1713
            self.pop_path()
            xs1007.append(item1010)
            idx1009 = (idx1009 + 1)
            cond1008 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1006 = xs1007
        self.pop_path()
        self.push_path(2)
        _t1714 = self.parse_script()
        script1011 = _t1714
        self.pop_path()
        self.consume_literal(")")
        _t1715 = logic_pb2.Algorithm(body=script1011)
        getattr(_t1715, 'global').extend(relation_ids1006)
        result1013 = _t1715
        self.record_span(span_start1012)
        return result1013

    def parse_script(self) -> logic_pb2.Script:
        span_start1022 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        self.push_path(1)
        xs1018 = []
        cond1019 = self.match_lookahead_literal("(", 0)
        idx1020 = 0
        while cond1019:
            self.push_path(idx1020)
            _t1716 = self.parse_construct()
            item1021 = _t1716
            self.pop_path()
            xs1018.append(item1021)
            idx1020 = (idx1020 + 1)
            cond1019 = self.match_lookahead_literal("(", 0)
        constructs1017 = xs1018
        self.pop_path()
        self.consume_literal(")")
        _t1717 = logic_pb2.Script(constructs=constructs1017)
        result1023 = _t1717
        self.record_span(span_start1022)
        return result1023

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1027 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1719 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1720 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1721 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1722 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1723 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1724 = 1
                                else:
                                    _t1724 = -1
                                _t1723 = _t1724
                            _t1722 = _t1723
                        _t1721 = _t1722
                    _t1720 = _t1721
                _t1719 = _t1720
            _t1718 = _t1719
        else:
            _t1718 = -1
        prediction1024 = _t1718
        if prediction1024 == 1:
            self.push_path(2)
            _t1726 = self.parse_instruction()
            instruction1026 = _t1726
            self.pop_path()
            _t1727 = logic_pb2.Construct(instruction=instruction1026)
            _t1725 = _t1727
        else:
            if prediction1024 == 0:
                self.push_path(1)
                _t1729 = self.parse_loop()
                loop1025 = _t1729
                self.pop_path()
                _t1730 = logic_pb2.Construct(loop=loop1025)
                _t1728 = _t1730
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1725 = _t1728
        result1028 = _t1725
        self.record_span(span_start1027)
        return result1028

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1031 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        self.push_path(1)
        _t1731 = self.parse_init()
        init1029 = _t1731
        self.pop_path()
        self.push_path(2)
        _t1732 = self.parse_script()
        script1030 = _t1732
        self.pop_path()
        self.consume_literal(")")
        _t1733 = logic_pb2.Loop(init=init1029, body=script1030)
        result1032 = _t1733
        self.record_span(span_start1031)
        return result1032

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        span_start1041 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("init")
        xs1037 = []
        cond1038 = self.match_lookahead_literal("(", 0)
        idx1039 = 0
        while cond1038:
            self.push_path(idx1039)
            _t1734 = self.parse_instruction()
            item1040 = _t1734
            self.pop_path()
            xs1037.append(item1040)
            idx1039 = (idx1039 + 1)
            cond1038 = self.match_lookahead_literal("(", 0)
        instructions1036 = xs1037
        self.consume_literal(")")
        result1042 = instructions1036
        self.record_span(span_start1041)
        return result1042

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1049 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1736 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1737 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1738 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1739 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1740 = 0
                            else:
                                _t1740 = -1
                            _t1739 = _t1740
                        _t1738 = _t1739
                    _t1737 = _t1738
                _t1736 = _t1737
            _t1735 = _t1736
        else:
            _t1735 = -1
        prediction1043 = _t1735
        if prediction1043 == 4:
            self.push_path(6)
            _t1742 = self.parse_monus_def()
            monus_def1048 = _t1742
            self.pop_path()
            _t1743 = logic_pb2.Instruction(monus_def=monus_def1048)
            _t1741 = _t1743
        else:
            if prediction1043 == 3:
                self.push_path(5)
                _t1745 = self.parse_monoid_def()
                monoid_def1047 = _t1745
                self.pop_path()
                _t1746 = logic_pb2.Instruction(monoid_def=monoid_def1047)
                _t1744 = _t1746
            else:
                if prediction1043 == 2:
                    self.push_path(3)
                    _t1748 = self.parse_break()
                    break1046 = _t1748
                    self.pop_path()
                    _t1749 = logic_pb2.Instruction()
                    getattr(_t1749, 'break').CopyFrom(break1046)
                    _t1747 = _t1749
                else:
                    if prediction1043 == 1:
                        self.push_path(2)
                        _t1751 = self.parse_upsert()
                        upsert1045 = _t1751
                        self.pop_path()
                        _t1752 = logic_pb2.Instruction(upsert=upsert1045)
                        _t1750 = _t1752
                    else:
                        if prediction1043 == 0:
                            self.push_path(1)
                            _t1754 = self.parse_assign()
                            assign1044 = _t1754
                            self.pop_path()
                            _t1755 = logic_pb2.Instruction(assign=assign1044)
                            _t1753 = _t1755
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1750 = _t1753
                    _t1747 = _t1750
                _t1744 = _t1747
            _t1741 = _t1744
        result1050 = _t1741
        self.record_span(span_start1049)
        return result1050

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1054 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        self.push_path(1)
        _t1756 = self.parse_relation_id()
        relation_id1051 = _t1756
        self.pop_path()
        self.push_path(2)
        _t1757 = self.parse_abstraction()
        abstraction1052 = _t1757
        self.pop_path()
        self.push_path(3)
        if self.match_lookahead_literal("(", 0):
            _t1759 = self.parse_attrs()
            _t1758 = _t1759
        else:
            _t1758 = None
        attrs1053 = _t1758
        self.pop_path()
        self.consume_literal(")")
        _t1760 = logic_pb2.Assign(name=relation_id1051, body=abstraction1052, attrs=(attrs1053 if attrs1053 is not None else []))
        result1055 = _t1760
        self.record_span(span_start1054)
        return result1055

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1059 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        self.push_path(1)
        _t1761 = self.parse_relation_id()
        relation_id1056 = _t1761
        self.pop_path()
        _t1762 = self.parse_abstraction_with_arity()
        abstraction_with_arity1057 = _t1762
        self.push_path(3)
        if self.match_lookahead_literal("(", 0):
            _t1764 = self.parse_attrs()
            _t1763 = _t1764
        else:
            _t1763 = None
        attrs1058 = _t1763
        self.pop_path()
        self.consume_literal(")")
        _t1765 = logic_pb2.Upsert(name=relation_id1056, body=abstraction_with_arity1057[0], attrs=(attrs1058 if attrs1058 is not None else []), value_arity=abstraction_with_arity1057[1])
        result1060 = _t1765
        self.record_span(span_start1059)
        return result1060

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        span_start1063 = self.span_start()
        self.consume_literal("(")
        _t1766 = self.parse_bindings()
        bindings1061 = _t1766
        _t1767 = self.parse_formula()
        formula1062 = _t1767
        self.consume_literal(")")
        _t1768 = logic_pb2.Abstraction(vars=(list(bindings1061[0]) + list(bindings1061[1] if bindings1061[1] is not None else [])), value=formula1062)
        result1064 = (_t1768, len(bindings1061[1]),)
        self.record_span(span_start1063)
        return result1064

    def parse_break(self) -> logic_pb2.Break:
        span_start1068 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        self.push_path(1)
        _t1769 = self.parse_relation_id()
        relation_id1065 = _t1769
        self.pop_path()
        self.push_path(2)
        _t1770 = self.parse_abstraction()
        abstraction1066 = _t1770
        self.pop_path()
        self.push_path(3)
        if self.match_lookahead_literal("(", 0):
            _t1772 = self.parse_attrs()
            _t1771 = _t1772
        else:
            _t1771 = None
        attrs1067 = _t1771
        self.pop_path()
        self.consume_literal(")")
        _t1773 = logic_pb2.Break(name=relation_id1065, body=abstraction1066, attrs=(attrs1067 if attrs1067 is not None else []))
        result1069 = _t1773
        self.record_span(span_start1068)
        return result1069

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1074 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        self.push_path(1)
        _t1774 = self.parse_monoid()
        monoid1070 = _t1774
        self.pop_path()
        self.push_path(2)
        _t1775 = self.parse_relation_id()
        relation_id1071 = _t1775
        self.pop_path()
        _t1776 = self.parse_abstraction_with_arity()
        abstraction_with_arity1072 = _t1776
        self.push_path(4)
        if self.match_lookahead_literal("(", 0):
            _t1778 = self.parse_attrs()
            _t1777 = _t1778
        else:
            _t1777 = None
        attrs1073 = _t1777
        self.pop_path()
        self.consume_literal(")")
        _t1779 = logic_pb2.MonoidDef(monoid=monoid1070, name=relation_id1071, body=abstraction_with_arity1072[0], attrs=(attrs1073 if attrs1073 is not None else []), value_arity=abstraction_with_arity1072[1])
        result1075 = _t1779
        self.record_span(span_start1074)
        return result1075

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1081 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1781 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1782 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1783 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1784 = 2
                        else:
                            _t1784 = -1
                        _t1783 = _t1784
                    _t1782 = _t1783
                _t1781 = _t1782
            _t1780 = _t1781
        else:
            _t1780 = -1
        prediction1076 = _t1780
        if prediction1076 == 3:
            self.push_path(4)
            _t1786 = self.parse_sum_monoid()
            sum_monoid1080 = _t1786
            self.pop_path()
            _t1787 = logic_pb2.Monoid(sum_monoid=sum_monoid1080)
            _t1785 = _t1787
        else:
            if prediction1076 == 2:
                self.push_path(3)
                _t1789 = self.parse_max_monoid()
                max_monoid1079 = _t1789
                self.pop_path()
                _t1790 = logic_pb2.Monoid(max_monoid=max_monoid1079)
                _t1788 = _t1790
            else:
                if prediction1076 == 1:
                    self.push_path(2)
                    _t1792 = self.parse_min_monoid()
                    min_monoid1078 = _t1792
                    self.pop_path()
                    _t1793 = logic_pb2.Monoid(min_monoid=min_monoid1078)
                    _t1791 = _t1793
                else:
                    if prediction1076 == 0:
                        self.push_path(1)
                        _t1795 = self.parse_or_monoid()
                        or_monoid1077 = _t1795
                        self.pop_path()
                        _t1796 = logic_pb2.Monoid(or_monoid=or_monoid1077)
                        _t1794 = _t1796
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1791 = _t1794
                _t1788 = _t1791
            _t1785 = _t1788
        result1082 = _t1785
        self.record_span(span_start1081)
        return result1082

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1083 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1797 = logic_pb2.OrMonoid()
        result1084 = _t1797
        self.record_span(span_start1083)
        return result1084

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1086 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        self.push_path(1)
        _t1798 = self.parse_type()
        type1085 = _t1798
        self.pop_path()
        self.consume_literal(")")
        _t1799 = logic_pb2.MinMonoid(type=type1085)
        result1087 = _t1799
        self.record_span(span_start1086)
        return result1087

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1089 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        self.push_path(1)
        _t1800 = self.parse_type()
        type1088 = _t1800
        self.pop_path()
        self.consume_literal(")")
        _t1801 = logic_pb2.MaxMonoid(type=type1088)
        result1090 = _t1801
        self.record_span(span_start1089)
        return result1090

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1092 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        self.push_path(1)
        _t1802 = self.parse_type()
        type1091 = _t1802
        self.pop_path()
        self.consume_literal(")")
        _t1803 = logic_pb2.SumMonoid(type=type1091)
        result1093 = _t1803
        self.record_span(span_start1092)
        return result1093

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1098 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        self.push_path(1)
        _t1804 = self.parse_monoid()
        monoid1094 = _t1804
        self.pop_path()
        self.push_path(2)
        _t1805 = self.parse_relation_id()
        relation_id1095 = _t1805
        self.pop_path()
        _t1806 = self.parse_abstraction_with_arity()
        abstraction_with_arity1096 = _t1806
        self.push_path(4)
        if self.match_lookahead_literal("(", 0):
            _t1808 = self.parse_attrs()
            _t1807 = _t1808
        else:
            _t1807 = None
        attrs1097 = _t1807
        self.pop_path()
        self.consume_literal(")")
        _t1809 = logic_pb2.MonusDef(monoid=monoid1094, name=relation_id1095, body=abstraction_with_arity1096[0], attrs=(attrs1097 if attrs1097 is not None else []), value_arity=abstraction_with_arity1096[1])
        result1099 = _t1809
        self.record_span(span_start1098)
        return result1099

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1104 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        self.push_path(2)
        _t1810 = self.parse_relation_id()
        relation_id1100 = _t1810
        self.pop_path()
        _t1811 = self.parse_abstraction()
        abstraction1101 = _t1811
        _t1812 = self.parse_functional_dependency_keys()
        functional_dependency_keys1102 = _t1812
        _t1813 = self.parse_functional_dependency_values()
        functional_dependency_values1103 = _t1813
        self.consume_literal(")")
        _t1814 = logic_pb2.FunctionalDependency(guard=abstraction1101, keys=functional_dependency_keys1102, values=functional_dependency_values1103)
        _t1815 = logic_pb2.Constraint(name=relation_id1100, functional_dependency=_t1814)
        result1105 = _t1815
        self.record_span(span_start1104)
        return result1105

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        span_start1114 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1110 = []
        cond1111 = self.match_lookahead_terminal("SYMBOL", 0)
        idx1112 = 0
        while cond1111:
            self.push_path(idx1112)
            _t1816 = self.parse_var()
            item1113 = _t1816
            self.pop_path()
            xs1110.append(item1113)
            idx1112 = (idx1112 + 1)
            cond1111 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1109 = xs1110
        self.consume_literal(")")
        result1115 = vars1109
        self.record_span(span_start1114)
        return result1115

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        span_start1124 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("values")
        xs1120 = []
        cond1121 = self.match_lookahead_terminal("SYMBOL", 0)
        idx1122 = 0
        while cond1121:
            self.push_path(idx1122)
            _t1817 = self.parse_var()
            item1123 = _t1817
            self.pop_path()
            xs1120.append(item1123)
            idx1122 = (idx1122 + 1)
            cond1121 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1119 = xs1120
        self.consume_literal(")")
        result1125 = vars1119
        self.record_span(span_start1124)
        return result1125

    def parse_data(self) -> logic_pb2.Data:
        span_start1130 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("rel_edb", 1):
                _t1819 = 0
            else:
                if self.match_lookahead_literal("csv_data", 1):
                    _t1820 = 2
                else:
                    if self.match_lookahead_literal("betree_relation", 1):
                        _t1821 = 1
                    else:
                        _t1821 = -1
                    _t1820 = _t1821
                _t1819 = _t1820
            _t1818 = _t1819
        else:
            _t1818 = -1
        prediction1126 = _t1818
        if prediction1126 == 2:
            self.push_path(3)
            _t1823 = self.parse_csv_data()
            csv_data1129 = _t1823
            self.pop_path()
            _t1824 = logic_pb2.Data(csv_data=csv_data1129)
            _t1822 = _t1824
        else:
            if prediction1126 == 1:
                self.push_path(2)
                _t1826 = self.parse_betree_relation()
                betree_relation1128 = _t1826
                self.pop_path()
                _t1827 = logic_pb2.Data(betree_relation=betree_relation1128)
                _t1825 = _t1827
            else:
                if prediction1126 == 0:
                    self.push_path(1)
                    _t1829 = self.parse_rel_edb()
                    rel_edb1127 = _t1829
                    self.pop_path()
                    _t1830 = logic_pb2.Data(rel_edb=rel_edb1127)
                    _t1828 = _t1830
                else:
                    raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                _t1825 = _t1828
            _t1822 = _t1825
        result1131 = _t1822
        self.record_span(span_start1130)
        return result1131

    def parse_rel_edb(self) -> logic_pb2.RelEDB:
        span_start1135 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("rel_edb")
        self.push_path(1)
        _t1831 = self.parse_relation_id()
        relation_id1132 = _t1831
        self.pop_path()
        self.push_path(2)
        _t1832 = self.parse_rel_edb_path()
        rel_edb_path1133 = _t1832
        self.pop_path()
        self.push_path(3)
        _t1833 = self.parse_rel_edb_types()
        rel_edb_types1134 = _t1833
        self.pop_path()
        self.consume_literal(")")
        _t1834 = logic_pb2.RelEDB(target_id=relation_id1132, path=rel_edb_path1133, types=rel_edb_types1134)
        result1136 = _t1834
        self.record_span(span_start1135)
        return result1136

    def parse_rel_edb_path(self) -> Sequence[str]:
        span_start1145 = self.span_start()
        self.consume_literal("[")
        xs1141 = []
        cond1142 = self.match_lookahead_terminal("STRING", 0)
        idx1143 = 0
        while cond1142:
            self.push_path(idx1143)
            item1144 = self.consume_terminal("STRING")
            self.pop_path()
            xs1141.append(item1144)
            idx1143 = (idx1143 + 1)
            cond1142 = self.match_lookahead_terminal("STRING", 0)
        strings1140 = xs1141
        self.consume_literal("]")
        result1146 = strings1140
        self.record_span(span_start1145)
        return result1146

    def parse_rel_edb_types(self) -> Sequence[logic_pb2.Type]:
        span_start1155 = self.span_start()
        self.consume_literal("[")
        xs1151 = []
        cond1152 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        idx1153 = 0
        while cond1152:
            self.push_path(idx1153)
            _t1835 = self.parse_type()
            item1154 = _t1835
            self.pop_path()
            xs1151.append(item1154)
            idx1153 = (idx1153 + 1)
            cond1152 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1150 = xs1151
        self.consume_literal("]")
        result1156 = types1150
        self.record_span(span_start1155)
        return result1156

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1159 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        self.push_path(1)
        _t1836 = self.parse_relation_id()
        relation_id1157 = _t1836
        self.pop_path()
        self.push_path(2)
        _t1837 = self.parse_betree_info()
        betree_info1158 = _t1837
        self.pop_path()
        self.consume_literal(")")
        _t1838 = logic_pb2.BeTreeRelation(name=relation_id1157, relation_info=betree_info1158)
        result1160 = _t1838
        self.record_span(span_start1159)
        return result1160

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1164 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1839 = self.parse_betree_info_key_types()
        betree_info_key_types1161 = _t1839
        _t1840 = self.parse_betree_info_value_types()
        betree_info_value_types1162 = _t1840
        _t1841 = self.parse_config_dict()
        config_dict1163 = _t1841
        self.consume_literal(")")
        _t1842 = self.construct_betree_info(betree_info_key_types1161, betree_info_value_types1162, config_dict1163)
        result1165 = _t1842
        self.record_span(span_start1164)
        return result1165

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        span_start1174 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1170 = []
        cond1171 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        idx1172 = 0
        while cond1171:
            self.push_path(idx1172)
            _t1843 = self.parse_type()
            item1173 = _t1843
            self.pop_path()
            xs1170.append(item1173)
            idx1172 = (idx1172 + 1)
            cond1171 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1169 = xs1170
        self.consume_literal(")")
        result1175 = types1169
        self.record_span(span_start1174)
        return result1175

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        span_start1184 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1180 = []
        cond1181 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        idx1182 = 0
        while cond1181:
            self.push_path(idx1182)
            _t1844 = self.parse_type()
            item1183 = _t1844
            self.pop_path()
            xs1180.append(item1183)
            idx1182 = (idx1182 + 1)
            cond1181 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1179 = xs1180
        self.consume_literal(")")
        result1185 = types1179
        self.record_span(span_start1184)
        return result1185

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1190 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        self.push_path(1)
        _t1845 = self.parse_csvlocator()
        csvlocator1186 = _t1845
        self.pop_path()
        self.push_path(2)
        _t1846 = self.parse_csv_config()
        csv_config1187 = _t1846
        self.pop_path()
        self.push_path(3)
        _t1847 = self.parse_csv_columns()
        csv_columns1188 = _t1847
        self.pop_path()
        self.push_path(4)
        _t1848 = self.parse_csv_asof()
        csv_asof1189 = _t1848
        self.pop_path()
        self.consume_literal(")")
        _t1849 = logic_pb2.CSVData(locator=csvlocator1186, config=csv_config1187, columns=csv_columns1188, asof=csv_asof1189)
        result1191 = _t1849
        self.record_span(span_start1190)
        return result1191

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1194 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        self.push_path(1)
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1851 = self.parse_csv_locator_paths()
            _t1850 = _t1851
        else:
            _t1850 = None
        csv_locator_paths1192 = _t1850
        self.pop_path()
        self.push_path(2)
        if self.match_lookahead_literal("(", 0):
            _t1853 = self.parse_csv_locator_inline_data()
            _t1852 = _t1853
        else:
            _t1852 = None
        csv_locator_inline_data1193 = _t1852
        self.pop_path()
        self.consume_literal(")")
        _t1854 = logic_pb2.CSVLocator(paths=(csv_locator_paths1192 if csv_locator_paths1192 is not None else []), inline_data=(csv_locator_inline_data1193 if csv_locator_inline_data1193 is not None else "").encode())
        result1195 = _t1854
        self.record_span(span_start1194)
        return result1195

    def parse_csv_locator_paths(self) -> Sequence[str]:
        span_start1204 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1200 = []
        cond1201 = self.match_lookahead_terminal("STRING", 0)
        idx1202 = 0
        while cond1201:
            self.push_path(idx1202)
            item1203 = self.consume_terminal("STRING")
            self.pop_path()
            xs1200.append(item1203)
            idx1202 = (idx1202 + 1)
            cond1201 = self.match_lookahead_terminal("STRING", 0)
        strings1199 = xs1200
        self.consume_literal(")")
        result1205 = strings1199
        self.record_span(span_start1204)
        return result1205

    def parse_csv_locator_inline_data(self) -> str:
        span_start1207 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1206 = self.consume_terminal("STRING")
        self.consume_literal(")")
        result1208 = string1206
        self.record_span(span_start1207)
        return result1208

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1210 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1855 = self.parse_config_dict()
        config_dict1209 = _t1855
        self.consume_literal(")")
        _t1856 = self.construct_csv_config(config_dict1209)
        result1211 = _t1856
        self.record_span(span_start1210)
        return result1211

    def parse_csv_columns(self) -> Sequence[logic_pb2.CSVColumn]:
        span_start1220 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1216 = []
        cond1217 = self.match_lookahead_literal("(", 0)
        idx1218 = 0
        while cond1217:
            self.push_path(idx1218)
            _t1857 = self.parse_csv_column()
            item1219 = _t1857
            self.pop_path()
            xs1216.append(item1219)
            idx1218 = (idx1218 + 1)
            cond1217 = self.match_lookahead_literal("(", 0)
        csv_columns1215 = xs1216
        self.consume_literal(")")
        result1221 = csv_columns1215
        self.record_span(span_start1220)
        return result1221

    def parse_csv_column(self) -> logic_pb2.CSVColumn:
        span_start1232 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        self.push_path(1)
        string1222 = self.consume_terminal("STRING")
        self.pop_path()
        self.push_path(2)
        _t1858 = self.parse_relation_id()
        relation_id1223 = _t1858
        self.pop_path()
        self.consume_literal("[")
        self.push_path(3)
        xs1228 = []
        cond1229 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        idx1230 = 0
        while cond1229:
            self.push_path(idx1230)
            _t1859 = self.parse_type()
            item1231 = _t1859
            self.pop_path()
            xs1228.append(item1231)
            idx1230 = (idx1230 + 1)
            cond1229 = ((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1227 = xs1228
        self.pop_path()
        self.consume_literal("]")
        self.consume_literal(")")
        _t1860 = logic_pb2.CSVColumn(column_name=string1222, target_id=relation_id1223, types=types1227)
        result1233 = _t1860
        self.record_span(span_start1232)
        return result1233

    def parse_csv_asof(self) -> str:
        span_start1235 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("asof")
        string1234 = self.consume_terminal("STRING")
        self.consume_literal(")")
        result1236 = string1234
        self.record_span(span_start1235)
        return result1236

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1238 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        self.push_path(1)
        _t1861 = self.parse_fragment_id()
        fragment_id1237 = _t1861
        self.pop_path()
        self.consume_literal(")")
        _t1862 = transactions_pb2.Undefine(fragment_id=fragment_id1237)
        result1239 = _t1862
        self.record_span(span_start1238)
        return result1239

    def parse_context(self) -> transactions_pb2.Context:
        span_start1248 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        self.push_path(1)
        xs1244 = []
        cond1245 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        idx1246 = 0
        while cond1245:
            self.push_path(idx1246)
            _t1863 = self.parse_relation_id()
            item1247 = _t1863
            self.pop_path()
            xs1244.append(item1247)
            idx1246 = (idx1246 + 1)
            cond1245 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1243 = xs1244
        self.pop_path()
        self.consume_literal(")")
        _t1864 = transactions_pb2.Context(relations=relation_ids1243)
        result1249 = _t1864
        self.record_span(span_start1248)
        return result1249

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1252 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        self.push_path(1)
        _t1865 = self.parse_rel_edb_path()
        rel_edb_path1250 = _t1865
        self.pop_path()
        self.push_path(2)
        _t1866 = self.parse_relation_id()
        relation_id1251 = _t1866
        self.pop_path()
        self.consume_literal(")")
        _t1867 = transactions_pb2.Snapshot(destination_path=rel_edb_path1250, source_relation=relation_id1251)
        result1253 = _t1867
        self.record_span(span_start1252)
        return result1253

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        span_start1262 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1258 = []
        cond1259 = self.match_lookahead_literal("(", 0)
        idx1260 = 0
        while cond1259:
            self.push_path(idx1260)
            _t1868 = self.parse_read()
            item1261 = _t1868
            self.pop_path()
            xs1258.append(item1261)
            idx1260 = (idx1260 + 1)
            cond1259 = self.match_lookahead_literal("(", 0)
        reads1257 = xs1258
        self.consume_literal(")")
        result1263 = reads1257
        self.record_span(span_start1262)
        return result1263

    def parse_read(self) -> transactions_pb2.Read:
        span_start1270 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1870 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1871 = 1
                else:
                    if self.match_lookahead_literal("export", 1):
                        _t1872 = 4
                    else:
                        if self.match_lookahead_literal("demand", 1):
                            _t1873 = 0
                        else:
                            if self.match_lookahead_literal("abort", 1):
                                _t1874 = 3
                            else:
                                _t1874 = -1
                            _t1873 = _t1874
                        _t1872 = _t1873
                    _t1871 = _t1872
                _t1870 = _t1871
            _t1869 = _t1870
        else:
            _t1869 = -1
        prediction1264 = _t1869
        if prediction1264 == 4:
            self.push_path(5)
            _t1876 = self.parse_export()
            export1269 = _t1876
            self.pop_path()
            _t1877 = transactions_pb2.Read(export=export1269)
            _t1875 = _t1877
        else:
            if prediction1264 == 3:
                self.push_path(4)
                _t1879 = self.parse_abort()
                abort1268 = _t1879
                self.pop_path()
                _t1880 = transactions_pb2.Read(abort=abort1268)
                _t1878 = _t1880
            else:
                if prediction1264 == 2:
                    self.push_path(3)
                    _t1882 = self.parse_what_if()
                    what_if1267 = _t1882
                    self.pop_path()
                    _t1883 = transactions_pb2.Read(what_if=what_if1267)
                    _t1881 = _t1883
                else:
                    if prediction1264 == 1:
                        self.push_path(2)
                        _t1885 = self.parse_output()
                        output1266 = _t1885
                        self.pop_path()
                        _t1886 = transactions_pb2.Read(output=output1266)
                        _t1884 = _t1886
                    else:
                        if prediction1264 == 0:
                            self.push_path(1)
                            _t1888 = self.parse_demand()
                            demand1265 = _t1888
                            self.pop_path()
                            _t1889 = transactions_pb2.Read(demand=demand1265)
                            _t1887 = _t1889
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1884 = _t1887
                    _t1881 = _t1884
                _t1878 = _t1881
            _t1875 = _t1878
        result1271 = _t1875
        self.record_span(span_start1270)
        return result1271

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1273 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        self.push_path(1)
        _t1890 = self.parse_relation_id()
        relation_id1272 = _t1890
        self.pop_path()
        self.consume_literal(")")
        _t1891 = transactions_pb2.Demand(relation_id=relation_id1272)
        result1274 = _t1891
        self.record_span(span_start1273)
        return result1274

    def parse_output(self) -> transactions_pb2.Output:
        span_start1277 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        self.push_path(1)
        _t1892 = self.parse_name()
        name1275 = _t1892
        self.pop_path()
        self.push_path(2)
        _t1893 = self.parse_relation_id()
        relation_id1276 = _t1893
        self.pop_path()
        self.consume_literal(")")
        _t1894 = transactions_pb2.Output(name=name1275, relation_id=relation_id1276)
        result1278 = _t1894
        self.record_span(span_start1277)
        return result1278

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1281 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        self.push_path(1)
        _t1895 = self.parse_name()
        name1279 = _t1895
        self.pop_path()
        self.push_path(2)
        _t1896 = self.parse_epoch()
        epoch1280 = _t1896
        self.pop_path()
        self.consume_literal(")")
        _t1897 = transactions_pb2.WhatIf(branch=name1279, epoch=epoch1280)
        result1282 = _t1897
        self.record_span(span_start1281)
        return result1282

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1285 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        self.push_path(1)
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1899 = self.parse_name()
            _t1898 = _t1899
        else:
            _t1898 = None
        name1283 = _t1898
        self.pop_path()
        self.push_path(2)
        _t1900 = self.parse_relation_id()
        relation_id1284 = _t1900
        self.pop_path()
        self.consume_literal(")")
        _t1901 = transactions_pb2.Abort(name=(name1283 if name1283 is not None else "abort"), relation_id=relation_id1284)
        result1286 = _t1901
        self.record_span(span_start1285)
        return result1286

    def parse_export(self) -> transactions_pb2.Export:
        span_start1288 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export")
        self.push_path(1)
        _t1902 = self.parse_export_csv_config()
        export_csv_config1287 = _t1902
        self.pop_path()
        self.consume_literal(")")
        _t1903 = transactions_pb2.Export(csv_config=export_csv_config1287)
        result1289 = _t1903
        self.record_span(span_start1288)
        return result1289

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1293 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_csv_config")
        _t1904 = self.parse_export_csv_path()
        export_csv_path1290 = _t1904
        _t1905 = self.parse_export_csv_columns()
        export_csv_columns1291 = _t1905
        _t1906 = self.parse_config_dict()
        config_dict1292 = _t1906
        self.consume_literal(")")
        _t1907 = self.export_csv_config(export_csv_path1290, export_csv_columns1291, config_dict1292)
        result1294 = _t1907
        self.record_span(span_start1293)
        return result1294

    def parse_export_csv_path(self) -> str:
        span_start1296 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("path")
        string1295 = self.consume_terminal("STRING")
        self.consume_literal(")")
        result1297 = string1295
        self.record_span(span_start1296)
        return result1297

    def parse_export_csv_columns(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        span_start1306 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1302 = []
        cond1303 = self.match_lookahead_literal("(", 0)
        idx1304 = 0
        while cond1303:
            self.push_path(idx1304)
            _t1908 = self.parse_export_csv_column()
            item1305 = _t1908
            self.pop_path()
            xs1302.append(item1305)
            idx1304 = (idx1304 + 1)
            cond1303 = self.match_lookahead_literal("(", 0)
        export_csv_columns1301 = xs1302
        self.consume_literal(")")
        result1307 = export_csv_columns1301
        self.record_span(span_start1306)
        return result1307

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1310 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        self.push_path(1)
        string1308 = self.consume_terminal("STRING")
        self.pop_path()
        self.push_path(2)
        _t1909 = self.parse_relation_id()
        relation_id1309 = _t1909
        self.pop_path()
        self.consume_literal(")")
        _t1910 = transactions_pb2.ExportCSVColumn(column_name=string1308, column_data=relation_id1309)
        result1311 = _t1910
        self.record_span(span_start1310)
        return result1311


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
