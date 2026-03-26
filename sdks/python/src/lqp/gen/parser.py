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
            _t2039 = value.HasField("int32_value")
        else:
            _t2039 = False
        if _t2039:
            assert value is not None
            return value.int32_value
        else:
            _t2040 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2041 = value.HasField("int_value")
        else:
            _t2041 = False
        if _t2041:
            assert value is not None
            return value.int_value
        else:
            _t2042 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2043 = value.HasField("string_value")
        else:
            _t2043 = False
        if _t2043:
            assert value is not None
            return value.string_value
        else:
            _t2044 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2045 = value.HasField("boolean_value")
        else:
            _t2045 = False
        if _t2045:
            assert value is not None
            return value.boolean_value
        else:
            _t2046 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2047 = value.HasField("string_value")
        else:
            _t2047 = False
        if _t2047:
            assert value is not None
            return [value.string_value]
        else:
            _t2048 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2049 = value.HasField("int_value")
        else:
            _t2049 = False
        if _t2049:
            assert value is not None
            return value.int_value
        else:
            _t2050 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2051 = value.HasField("float_value")
        else:
            _t2051 = False
        if _t2051:
            assert value is not None
            return value.float_value
        else:
            _t2052 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2053 = value.HasField("string_value")
        else:
            _t2053 = False
        if _t2053:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2054 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2055 = value.HasField("uint128_value")
        else:
            _t2055 = False
        if _t2055:
            assert value is not None
            return value.uint128_value
        else:
            _t2056 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2057 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2057
        _t2058 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2058
        _t2059 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2059
        _t2060 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2060
        _t2061 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2061
        _t2062 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2062
        _t2063 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2063
        _t2064 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2064
        _t2065 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2065
        _t2066 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2066
        _t2067 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t2067
        _t2068 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2068
        _t2069 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t2069

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2070 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2070
        _t2071 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2071
        _t2072 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2072
        _t2073 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2073
        _t2074 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2074
        _t2075 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2075
        _t2076 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2076
        _t2077 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2077
        _t2078 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2078
        _t2079 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2079
        _t2080 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2080

    def default_configure(self) -> transactions_pb2.Configure:
        _t2081 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2081
        _t2082 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2082

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
        _t2083 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2083
        _t2084 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2084
        _t2085 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2085

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2086 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2086
        _t2087 = self._extract_value_string(config.get("compression"), "")
        compression = _t2087
        _t2088 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2088
        _t2089 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2089
        _t2090 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2090
        _t2091 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2091
        _t2092 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2092
        _t2093 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2093

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2094 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2094

    def construct_iceberg_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2095 = logic_pb2.IcebergConfig(catalog_uri=catalog_uri, scope=scope_opt, properties=props, auth_properties=auth_props)
        return _t2095

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergConfig, columns: Sequence[transactions_pb2.IcebergExportColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        prefix = ""
        target_file_size_bytes = 0
        compression = ""
        if config_dict is not None:
            assert config_dict is not None
            cfg = dict(config_dict)
            _t2096 = self._extract_value_string(cfg.get("prefix"), "")
            prefix = _t2096
            _t2097 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
            target_file_size_bytes = _t2097
            _t2098 = self._extract_value_string(cfg.get("compression"), "")
            compression = _t2098
        _t2099 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression)
        return _t2099

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start657 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1303 = self.parse_configure()
            _t1302 = _t1303
        else:
            _t1302 = None
        configure651 = _t1302
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1305 = self.parse_sync()
            _t1304 = _t1305
        else:
            _t1304 = None
        sync652 = _t1304
        xs653 = []
        cond654 = self.match_lookahead_literal("(", 0)
        while cond654:
            _t1306 = self.parse_epoch()
            item655 = _t1306
            xs653.append(item655)
            cond654 = self.match_lookahead_literal("(", 0)
        epochs656 = xs653
        self.consume_literal(")")
        _t1307 = self.default_configure()
        _t1308 = transactions_pb2.Transaction(epochs=epochs656, configure=(configure651 if configure651 is not None else _t1307), sync=sync652)
        result658 = _t1308
        self.record_span(span_start657, "Transaction")
        return result658

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start660 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1309 = self.parse_config_dict()
        config_dict659 = _t1309
        self.consume_literal(")")
        _t1310 = self.construct_configure(config_dict659)
        result661 = _t1310
        self.record_span(span_start660, "Configure")
        return result661

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs662 = []
        cond663 = self.match_lookahead_literal(":", 0)
        while cond663:
            _t1311 = self.parse_config_key_value()
            item664 = _t1311
            xs662.append(item664)
            cond663 = self.match_lookahead_literal(":", 0)
        config_key_values665 = xs662
        self.consume_literal("}")
        return config_key_values665

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol666 = self.consume_terminal("SYMBOL")
        _t1312 = self.parse_raw_value()
        raw_value667 = _t1312
        return (symbol666, raw_value667,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start681 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1313 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1314 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1315 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1317 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1318 = 0
                            else:
                                _t1318 = -1
                            _t1317 = _t1318
                        _t1316 = _t1317
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1319 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1320 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1321 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1322 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1323 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1324 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1325 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1326 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1327 = 10
                                                        else:
                                                            _t1327 = -1
                                                        _t1326 = _t1327
                                                    _t1325 = _t1326
                                                _t1324 = _t1325
                                            _t1323 = _t1324
                                        _t1322 = _t1323
                                    _t1321 = _t1322
                                _t1320 = _t1321
                            _t1319 = _t1320
                        _t1316 = _t1319
                    _t1315 = _t1316
                _t1314 = _t1315
            _t1313 = _t1314
        prediction668 = _t1313
        if prediction668 == 12:
            _t1329 = self.parse_boolean_value()
            boolean_value680 = _t1329
            _t1330 = logic_pb2.Value(boolean_value=boolean_value680)
            _t1328 = _t1330
        else:
            if prediction668 == 11:
                self.consume_literal("missing")
                _t1332 = logic_pb2.MissingValue()
                _t1333 = logic_pb2.Value(missing_value=_t1332)
                _t1331 = _t1333
            else:
                if prediction668 == 10:
                    decimal679 = self.consume_terminal("DECIMAL")
                    _t1335 = logic_pb2.Value(decimal_value=decimal679)
                    _t1334 = _t1335
                else:
                    if prediction668 == 9:
                        int128678 = self.consume_terminal("INT128")
                        _t1337 = logic_pb2.Value(int128_value=int128678)
                        _t1336 = _t1337
                    else:
                        if prediction668 == 8:
                            uint128677 = self.consume_terminal("UINT128")
                            _t1339 = logic_pb2.Value(uint128_value=uint128677)
                            _t1338 = _t1339
                        else:
                            if prediction668 == 7:
                                uint32676 = self.consume_terminal("UINT32")
                                _t1341 = logic_pb2.Value(uint32_value=uint32676)
                                _t1340 = _t1341
                            else:
                                if prediction668 == 6:
                                    float675 = self.consume_terminal("FLOAT")
                                    _t1343 = logic_pb2.Value(float_value=float675)
                                    _t1342 = _t1343
                                else:
                                    if prediction668 == 5:
                                        float32674 = self.consume_terminal("FLOAT32")
                                        _t1345 = logic_pb2.Value(float32_value=float32674)
                                        _t1344 = _t1345
                                    else:
                                        if prediction668 == 4:
                                            int673 = self.consume_terminal("INT")
                                            _t1347 = logic_pb2.Value(int_value=int673)
                                            _t1346 = _t1347
                                        else:
                                            if prediction668 == 3:
                                                int32672 = self.consume_terminal("INT32")
                                                _t1349 = logic_pb2.Value(int32_value=int32672)
                                                _t1348 = _t1349
                                            else:
                                                if prediction668 == 2:
                                                    string671 = self.consume_terminal("STRING")
                                                    _t1351 = logic_pb2.Value(string_value=string671)
                                                    _t1350 = _t1351
                                                else:
                                                    if prediction668 == 1:
                                                        _t1353 = self.parse_raw_datetime()
                                                        raw_datetime670 = _t1353
                                                        _t1354 = logic_pb2.Value(datetime_value=raw_datetime670)
                                                        _t1352 = _t1354
                                                    else:
                                                        if prediction668 == 0:
                                                            _t1356 = self.parse_raw_date()
                                                            raw_date669 = _t1356
                                                            _t1357 = logic_pb2.Value(date_value=raw_date669)
                                                            _t1355 = _t1357
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1352 = _t1355
                                                    _t1350 = _t1352
                                                _t1348 = _t1350
                                            _t1346 = _t1348
                                        _t1344 = _t1346
                                    _t1342 = _t1344
                                _t1340 = _t1342
                            _t1338 = _t1340
                        _t1336 = _t1338
                    _t1334 = _t1336
                _t1331 = _t1334
            _t1328 = _t1331
        result682 = _t1328
        self.record_span(span_start681, "Value")
        return result682

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start686 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int683 = self.consume_terminal("INT")
        int_3684 = self.consume_terminal("INT")
        int_4685 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1358 = logic_pb2.DateValue(year=int(int683), month=int(int_3684), day=int(int_4685))
        result687 = _t1358
        self.record_span(span_start686, "DateValue")
        return result687

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start695 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int688 = self.consume_terminal("INT")
        int_3689 = self.consume_terminal("INT")
        int_4690 = self.consume_terminal("INT")
        int_5691 = self.consume_terminal("INT")
        int_6692 = self.consume_terminal("INT")
        int_7693 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1359 = self.consume_terminal("INT")
        else:
            _t1359 = None
        int_8694 = _t1359
        self.consume_literal(")")
        _t1360 = logic_pb2.DateTimeValue(year=int(int688), month=int(int_3689), day=int(int_4690), hour=int(int_5691), minute=int(int_6692), second=int(int_7693), microsecond=int((int_8694 if int_8694 is not None else 0)))
        result696 = _t1360
        self.record_span(span_start695, "DateTimeValue")
        return result696

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1361 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1362 = 1
            else:
                _t1362 = -1
            _t1361 = _t1362
        prediction697 = _t1361
        if prediction697 == 1:
            self.consume_literal("false")
            _t1363 = False
        else:
            if prediction697 == 0:
                self.consume_literal("true")
                _t1364 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1363 = _t1364
        return _t1363

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start702 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs698 = []
        cond699 = self.match_lookahead_literal(":", 0)
        while cond699:
            _t1365 = self.parse_fragment_id()
            item700 = _t1365
            xs698.append(item700)
            cond699 = self.match_lookahead_literal(":", 0)
        fragment_ids701 = xs698
        self.consume_literal(")")
        _t1366 = transactions_pb2.Sync(fragments=fragment_ids701)
        result703 = _t1366
        self.record_span(span_start702, "Sync")
        return result703

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start705 = self.span_start()
        self.consume_literal(":")
        symbol704 = self.consume_terminal("SYMBOL")
        result706 = fragments_pb2.FragmentId(id=symbol704.encode())
        self.record_span(span_start705, "FragmentId")
        return result706

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start709 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1368 = self.parse_epoch_writes()
            _t1367 = _t1368
        else:
            _t1367 = None
        epoch_writes707 = _t1367
        if self.match_lookahead_literal("(", 0):
            _t1370 = self.parse_epoch_reads()
            _t1369 = _t1370
        else:
            _t1369 = None
        epoch_reads708 = _t1369
        self.consume_literal(")")
        _t1371 = transactions_pb2.Epoch(writes=(epoch_writes707 if epoch_writes707 is not None else []), reads=(epoch_reads708 if epoch_reads708 is not None else []))
        result710 = _t1371
        self.record_span(span_start709, "Epoch")
        return result710

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs711 = []
        cond712 = self.match_lookahead_literal("(", 0)
        while cond712:
            _t1372 = self.parse_write()
            item713 = _t1372
            xs711.append(item713)
            cond712 = self.match_lookahead_literal("(", 0)
        writes714 = xs711
        self.consume_literal(")")
        return writes714

    def parse_write(self) -> transactions_pb2.Write:
        span_start720 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1374 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1375 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1376 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1377 = 2
                        else:
                            _t1377 = -1
                        _t1376 = _t1377
                    _t1375 = _t1376
                _t1374 = _t1375
            _t1373 = _t1374
        else:
            _t1373 = -1
        prediction715 = _t1373
        if prediction715 == 3:
            _t1379 = self.parse_snapshot()
            snapshot719 = _t1379
            _t1380 = transactions_pb2.Write(snapshot=snapshot719)
            _t1378 = _t1380
        else:
            if prediction715 == 2:
                _t1382 = self.parse_context()
                context718 = _t1382
                _t1383 = transactions_pb2.Write(context=context718)
                _t1381 = _t1383
            else:
                if prediction715 == 1:
                    _t1385 = self.parse_undefine()
                    undefine717 = _t1385
                    _t1386 = transactions_pb2.Write(undefine=undefine717)
                    _t1384 = _t1386
                else:
                    if prediction715 == 0:
                        _t1388 = self.parse_define()
                        define716 = _t1388
                        _t1389 = transactions_pb2.Write(define=define716)
                        _t1387 = _t1389
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1384 = _t1387
                _t1381 = _t1384
            _t1378 = _t1381
        result721 = _t1378
        self.record_span(span_start720, "Write")
        return result721

    def parse_define(self) -> transactions_pb2.Define:
        span_start723 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1390 = self.parse_fragment()
        fragment722 = _t1390
        self.consume_literal(")")
        _t1391 = transactions_pb2.Define(fragment=fragment722)
        result724 = _t1391
        self.record_span(span_start723, "Define")
        return result724

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start730 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1392 = self.parse_new_fragment_id()
        new_fragment_id725 = _t1392
        xs726 = []
        cond727 = self.match_lookahead_literal("(", 0)
        while cond727:
            _t1393 = self.parse_declaration()
            item728 = _t1393
            xs726.append(item728)
            cond727 = self.match_lookahead_literal("(", 0)
        declarations729 = xs726
        self.consume_literal(")")
        result731 = self.construct_fragment(new_fragment_id725, declarations729)
        self.record_span(span_start730, "Fragment")
        return result731

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start733 = self.span_start()
        _t1394 = self.parse_fragment_id()
        fragment_id732 = _t1394
        self.start_fragment(fragment_id732)
        result734 = fragment_id732
        self.record_span(span_start733, "FragmentId")
        return result734

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start740 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1396 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1397 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1398 = 3
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
            _t1395 = _t1396
        else:
            _t1395 = -1
        prediction735 = _t1395
        if prediction735 == 3:
            _t1404 = self.parse_data()
            data739 = _t1404
            _t1405 = logic_pb2.Declaration(data=data739)
            _t1403 = _t1405
        else:
            if prediction735 == 2:
                _t1407 = self.parse_constraint()
                constraint738 = _t1407
                _t1408 = logic_pb2.Declaration(constraint=constraint738)
                _t1406 = _t1408
            else:
                if prediction735 == 1:
                    _t1410 = self.parse_algorithm()
                    algorithm737 = _t1410
                    _t1411 = logic_pb2.Declaration(algorithm=algorithm737)
                    _t1409 = _t1411
                else:
                    if prediction735 == 0:
                        _t1413 = self.parse_def()
                        def736 = _t1413
                        _t1414 = logic_pb2.Declaration()
                        getattr(_t1414, 'def').CopyFrom(def736)
                        _t1412 = _t1414
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1409 = _t1412
                _t1406 = _t1409
            _t1403 = _t1406
        result741 = _t1403
        self.record_span(span_start740, "Declaration")
        return result741

    def parse_def(self) -> logic_pb2.Def:
        span_start745 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1415 = self.parse_relation_id()
        relation_id742 = _t1415
        _t1416 = self.parse_abstraction()
        abstraction743 = _t1416
        if self.match_lookahead_literal("(", 0):
            _t1418 = self.parse_attrs()
            _t1417 = _t1418
        else:
            _t1417 = None
        attrs744 = _t1417
        self.consume_literal(")")
        _t1419 = logic_pb2.Def(name=relation_id742, body=abstraction743, attrs=(attrs744 if attrs744 is not None else []))
        result746 = _t1419
        self.record_span(span_start745, "Def")
        return result746

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start750 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1420 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1421 = 1
            else:
                _t1421 = -1
            _t1420 = _t1421
        prediction747 = _t1420
        if prediction747 == 1:
            uint128749 = self.consume_terminal("UINT128")
            _t1422 = logic_pb2.RelationId(id_low=uint128749.low, id_high=uint128749.high)
        else:
            if prediction747 == 0:
                self.consume_literal(":")
                symbol748 = self.consume_terminal("SYMBOL")
                _t1423 = self.relation_id_from_string(symbol748)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1422 = _t1423
        result751 = _t1422
        self.record_span(span_start750, "RelationId")
        return result751

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start754 = self.span_start()
        self.consume_literal("(")
        _t1424 = self.parse_bindings()
        bindings752 = _t1424
        _t1425 = self.parse_formula()
        formula753 = _t1425
        self.consume_literal(")")
        _t1426 = logic_pb2.Abstraction(vars=(list(bindings752[0]) + list(bindings752[1] if bindings752[1] is not None else [])), value=formula753)
        result755 = _t1426
        self.record_span(span_start754, "Abstraction")
        return result755

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs756 = []
        cond757 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond757:
            _t1427 = self.parse_binding()
            item758 = _t1427
            xs756.append(item758)
            cond757 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings759 = xs756
        if self.match_lookahead_literal("|", 0):
            _t1429 = self.parse_value_bindings()
            _t1428 = _t1429
        else:
            _t1428 = None
        value_bindings760 = _t1428
        self.consume_literal("]")
        return (bindings759, (value_bindings760 if value_bindings760 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start763 = self.span_start()
        symbol761 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1430 = self.parse_type()
        type762 = _t1430
        _t1431 = logic_pb2.Var(name=symbol761)
        _t1432 = logic_pb2.Binding(var=_t1431, type=type762)
        result764 = _t1432
        self.record_span(span_start763, "Binding")
        return result764

    def parse_type(self) -> logic_pb2.Type:
        span_start780 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1433 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1434 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1435 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1436 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1437 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1438 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1439 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1440 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1441 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1442 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1443 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1444 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1445 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1446 = 9
                                                            else:
                                                                _t1446 = -1
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
        prediction765 = _t1433
        if prediction765 == 13:
            _t1448 = self.parse_uint32_type()
            uint32_type779 = _t1448
            _t1449 = logic_pb2.Type(uint32_type=uint32_type779)
            _t1447 = _t1449
        else:
            if prediction765 == 12:
                _t1451 = self.parse_float32_type()
                float32_type778 = _t1451
                _t1452 = logic_pb2.Type(float32_type=float32_type778)
                _t1450 = _t1452
            else:
                if prediction765 == 11:
                    _t1454 = self.parse_int32_type()
                    int32_type777 = _t1454
                    _t1455 = logic_pb2.Type(int32_type=int32_type777)
                    _t1453 = _t1455
                else:
                    if prediction765 == 10:
                        _t1457 = self.parse_boolean_type()
                        boolean_type776 = _t1457
                        _t1458 = logic_pb2.Type(boolean_type=boolean_type776)
                        _t1456 = _t1458
                    else:
                        if prediction765 == 9:
                            _t1460 = self.parse_decimal_type()
                            decimal_type775 = _t1460
                            _t1461 = logic_pb2.Type(decimal_type=decimal_type775)
                            _t1459 = _t1461
                        else:
                            if prediction765 == 8:
                                _t1463 = self.parse_missing_type()
                                missing_type774 = _t1463
                                _t1464 = logic_pb2.Type(missing_type=missing_type774)
                                _t1462 = _t1464
                            else:
                                if prediction765 == 7:
                                    _t1466 = self.parse_datetime_type()
                                    datetime_type773 = _t1466
                                    _t1467 = logic_pb2.Type(datetime_type=datetime_type773)
                                    _t1465 = _t1467
                                else:
                                    if prediction765 == 6:
                                        _t1469 = self.parse_date_type()
                                        date_type772 = _t1469
                                        _t1470 = logic_pb2.Type(date_type=date_type772)
                                        _t1468 = _t1470
                                    else:
                                        if prediction765 == 5:
                                            _t1472 = self.parse_int128_type()
                                            int128_type771 = _t1472
                                            _t1473 = logic_pb2.Type(int128_type=int128_type771)
                                            _t1471 = _t1473
                                        else:
                                            if prediction765 == 4:
                                                _t1475 = self.parse_uint128_type()
                                                uint128_type770 = _t1475
                                                _t1476 = logic_pb2.Type(uint128_type=uint128_type770)
                                                _t1474 = _t1476
                                            else:
                                                if prediction765 == 3:
                                                    _t1478 = self.parse_float_type()
                                                    float_type769 = _t1478
                                                    _t1479 = logic_pb2.Type(float_type=float_type769)
                                                    _t1477 = _t1479
                                                else:
                                                    if prediction765 == 2:
                                                        _t1481 = self.parse_int_type()
                                                        int_type768 = _t1481
                                                        _t1482 = logic_pb2.Type(int_type=int_type768)
                                                        _t1480 = _t1482
                                                    else:
                                                        if prediction765 == 1:
                                                            _t1484 = self.parse_string_type()
                                                            string_type767 = _t1484
                                                            _t1485 = logic_pb2.Type(string_type=string_type767)
                                                            _t1483 = _t1485
                                                        else:
                                                            if prediction765 == 0:
                                                                _t1487 = self.parse_unspecified_type()
                                                                unspecified_type766 = _t1487
                                                                _t1488 = logic_pb2.Type(unspecified_type=unspecified_type766)
                                                                _t1486 = _t1488
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1483 = _t1486
                                                        _t1480 = _t1483
                                                    _t1477 = _t1480
                                                _t1474 = _t1477
                                            _t1471 = _t1474
                                        _t1468 = _t1471
                                    _t1465 = _t1468
                                _t1462 = _t1465
                            _t1459 = _t1462
                        _t1456 = _t1459
                    _t1453 = _t1456
                _t1450 = _t1453
            _t1447 = _t1450
        result781 = _t1447
        self.record_span(span_start780, "Type")
        return result781

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start782 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1489 = logic_pb2.UnspecifiedType()
        result783 = _t1489
        self.record_span(span_start782, "UnspecifiedType")
        return result783

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start784 = self.span_start()
        self.consume_literal("STRING")
        _t1490 = logic_pb2.StringType()
        result785 = _t1490
        self.record_span(span_start784, "StringType")
        return result785

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start786 = self.span_start()
        self.consume_literal("INT")
        _t1491 = logic_pb2.IntType()
        result787 = _t1491
        self.record_span(span_start786, "IntType")
        return result787

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start788 = self.span_start()
        self.consume_literal("FLOAT")
        _t1492 = logic_pb2.FloatType()
        result789 = _t1492
        self.record_span(span_start788, "FloatType")
        return result789

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start790 = self.span_start()
        self.consume_literal("UINT128")
        _t1493 = logic_pb2.UInt128Type()
        result791 = _t1493
        self.record_span(span_start790, "UInt128Type")
        return result791

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start792 = self.span_start()
        self.consume_literal("INT128")
        _t1494 = logic_pb2.Int128Type()
        result793 = _t1494
        self.record_span(span_start792, "Int128Type")
        return result793

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start794 = self.span_start()
        self.consume_literal("DATE")
        _t1495 = logic_pb2.DateType()
        result795 = _t1495
        self.record_span(span_start794, "DateType")
        return result795

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start796 = self.span_start()
        self.consume_literal("DATETIME")
        _t1496 = logic_pb2.DateTimeType()
        result797 = _t1496
        self.record_span(span_start796, "DateTimeType")
        return result797

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start798 = self.span_start()
        self.consume_literal("MISSING")
        _t1497 = logic_pb2.MissingType()
        result799 = _t1497
        self.record_span(span_start798, "MissingType")
        return result799

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start802 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int800 = self.consume_terminal("INT")
        int_3801 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1498 = logic_pb2.DecimalType(precision=int(int800), scale=int(int_3801))
        result803 = _t1498
        self.record_span(span_start802, "DecimalType")
        return result803

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start804 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1499 = logic_pb2.BooleanType()
        result805 = _t1499
        self.record_span(span_start804, "BooleanType")
        return result805

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start806 = self.span_start()
        self.consume_literal("INT32")
        _t1500 = logic_pb2.Int32Type()
        result807 = _t1500
        self.record_span(span_start806, "Int32Type")
        return result807

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start808 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1501 = logic_pb2.Float32Type()
        result809 = _t1501
        self.record_span(span_start808, "Float32Type")
        return result809

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start810 = self.span_start()
        self.consume_literal("UINT32")
        _t1502 = logic_pb2.UInt32Type()
        result811 = _t1502
        self.record_span(span_start810, "UInt32Type")
        return result811

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs812 = []
        cond813 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond813:
            _t1503 = self.parse_binding()
            item814 = _t1503
            xs812.append(item814)
            cond813 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings815 = xs812
        return bindings815

    def parse_formula(self) -> logic_pb2.Formula:
        span_start830 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1505 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1506 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1507 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1508 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1509 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1510 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1511 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1512 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1513 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1514 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1515 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1516 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1517 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1518 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1519 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1520 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1521 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1522 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1523 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1524 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1525 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1526 = 10
                                                                                                else:
                                                                                                    _t1526 = -1
                                                                                                _t1525 = _t1526
                                                                                            _t1524 = _t1525
                                                                                        _t1523 = _t1524
                                                                                    _t1522 = _t1523
                                                                                _t1521 = _t1522
                                                                            _t1520 = _t1521
                                                                        _t1519 = _t1520
                                                                    _t1518 = _t1519
                                                                _t1517 = _t1518
                                                            _t1516 = _t1517
                                                        _t1515 = _t1516
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
        else:
            _t1504 = -1
        prediction816 = _t1504
        if prediction816 == 12:
            _t1528 = self.parse_cast()
            cast829 = _t1528
            _t1529 = logic_pb2.Formula(cast=cast829)
            _t1527 = _t1529
        else:
            if prediction816 == 11:
                _t1531 = self.parse_rel_atom()
                rel_atom828 = _t1531
                _t1532 = logic_pb2.Formula(rel_atom=rel_atom828)
                _t1530 = _t1532
            else:
                if prediction816 == 10:
                    _t1534 = self.parse_primitive()
                    primitive827 = _t1534
                    _t1535 = logic_pb2.Formula(primitive=primitive827)
                    _t1533 = _t1535
                else:
                    if prediction816 == 9:
                        _t1537 = self.parse_pragma()
                        pragma826 = _t1537
                        _t1538 = logic_pb2.Formula(pragma=pragma826)
                        _t1536 = _t1538
                    else:
                        if prediction816 == 8:
                            _t1540 = self.parse_atom()
                            atom825 = _t1540
                            _t1541 = logic_pb2.Formula(atom=atom825)
                            _t1539 = _t1541
                        else:
                            if prediction816 == 7:
                                _t1543 = self.parse_ffi()
                                ffi824 = _t1543
                                _t1544 = logic_pb2.Formula(ffi=ffi824)
                                _t1542 = _t1544
                            else:
                                if prediction816 == 6:
                                    _t1546 = self.parse_not()
                                    not823 = _t1546
                                    _t1547 = logic_pb2.Formula()
                                    getattr(_t1547, 'not').CopyFrom(not823)
                                    _t1545 = _t1547
                                else:
                                    if prediction816 == 5:
                                        _t1549 = self.parse_disjunction()
                                        disjunction822 = _t1549
                                        _t1550 = logic_pb2.Formula(disjunction=disjunction822)
                                        _t1548 = _t1550
                                    else:
                                        if prediction816 == 4:
                                            _t1552 = self.parse_conjunction()
                                            conjunction821 = _t1552
                                            _t1553 = logic_pb2.Formula(conjunction=conjunction821)
                                            _t1551 = _t1553
                                        else:
                                            if prediction816 == 3:
                                                _t1555 = self.parse_reduce()
                                                reduce820 = _t1555
                                                _t1556 = logic_pb2.Formula(reduce=reduce820)
                                                _t1554 = _t1556
                                            else:
                                                if prediction816 == 2:
                                                    _t1558 = self.parse_exists()
                                                    exists819 = _t1558
                                                    _t1559 = logic_pb2.Formula(exists=exists819)
                                                    _t1557 = _t1559
                                                else:
                                                    if prediction816 == 1:
                                                        _t1561 = self.parse_false()
                                                        false818 = _t1561
                                                        _t1562 = logic_pb2.Formula(disjunction=false818)
                                                        _t1560 = _t1562
                                                    else:
                                                        if prediction816 == 0:
                                                            _t1564 = self.parse_true()
                                                            true817 = _t1564
                                                            _t1565 = logic_pb2.Formula(conjunction=true817)
                                                            _t1563 = _t1565
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1560 = _t1563
                                                    _t1557 = _t1560
                                                _t1554 = _t1557
                                            _t1551 = _t1554
                                        _t1548 = _t1551
                                    _t1545 = _t1548
                                _t1542 = _t1545
                            _t1539 = _t1542
                        _t1536 = _t1539
                    _t1533 = _t1536
                _t1530 = _t1533
            _t1527 = _t1530
        result831 = _t1527
        self.record_span(span_start830, "Formula")
        return result831

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start832 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1566 = logic_pb2.Conjunction(args=[])
        result833 = _t1566
        self.record_span(span_start832, "Conjunction")
        return result833

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start834 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1567 = logic_pb2.Disjunction(args=[])
        result835 = _t1567
        self.record_span(span_start834, "Disjunction")
        return result835

    def parse_exists(self) -> logic_pb2.Exists:
        span_start838 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1568 = self.parse_bindings()
        bindings836 = _t1568
        _t1569 = self.parse_formula()
        formula837 = _t1569
        self.consume_literal(")")
        _t1570 = logic_pb2.Abstraction(vars=(list(bindings836[0]) + list(bindings836[1] if bindings836[1] is not None else [])), value=formula837)
        _t1571 = logic_pb2.Exists(body=_t1570)
        result839 = _t1571
        self.record_span(span_start838, "Exists")
        return result839

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start843 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1572 = self.parse_abstraction()
        abstraction840 = _t1572
        _t1573 = self.parse_abstraction()
        abstraction_3841 = _t1573
        _t1574 = self.parse_terms()
        terms842 = _t1574
        self.consume_literal(")")
        _t1575 = logic_pb2.Reduce(op=abstraction840, body=abstraction_3841, terms=terms842)
        result844 = _t1575
        self.record_span(span_start843, "Reduce")
        return result844

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs845 = []
        cond846 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond846:
            _t1576 = self.parse_term()
            item847 = _t1576
            xs845.append(item847)
            cond846 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms848 = xs845
        self.consume_literal(")")
        return terms848

    def parse_term(self) -> logic_pb2.Term:
        span_start852 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1577 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1578 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1579 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1580 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1581 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1582 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1583 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1584 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1585 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1586 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1587 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1588 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1589 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1590 = 1
                                                            else:
                                                                _t1590 = -1
                                                            _t1589 = _t1590
                                                        _t1588 = _t1589
                                                    _t1587 = _t1588
                                                _t1586 = _t1587
                                            _t1585 = _t1586
                                        _t1584 = _t1585
                                    _t1583 = _t1584
                                _t1582 = _t1583
                            _t1581 = _t1582
                        _t1580 = _t1581
                    _t1579 = _t1580
                _t1578 = _t1579
            _t1577 = _t1578
        prediction849 = _t1577
        if prediction849 == 1:
            _t1592 = self.parse_value()
            value851 = _t1592
            _t1593 = logic_pb2.Term(constant=value851)
            _t1591 = _t1593
        else:
            if prediction849 == 0:
                _t1595 = self.parse_var()
                var850 = _t1595
                _t1596 = logic_pb2.Term(var=var850)
                _t1594 = _t1596
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1591 = _t1594
        result853 = _t1591
        self.record_span(span_start852, "Term")
        return result853

    def parse_var(self) -> logic_pb2.Var:
        span_start855 = self.span_start()
        symbol854 = self.consume_terminal("SYMBOL")
        _t1597 = logic_pb2.Var(name=symbol854)
        result856 = _t1597
        self.record_span(span_start855, "Var")
        return result856

    def parse_value(self) -> logic_pb2.Value:
        span_start870 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1598 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1599 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1600 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1602 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1603 = 0
                            else:
                                _t1603 = -1
                            _t1602 = _t1603
                        _t1601 = _t1602
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1604 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1605 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1606 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1607 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1608 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1609 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1610 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1611 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1612 = 10
                                                        else:
                                                            _t1612 = -1
                                                        _t1611 = _t1612
                                                    _t1610 = _t1611
                                                _t1609 = _t1610
                                            _t1608 = _t1609
                                        _t1607 = _t1608
                                    _t1606 = _t1607
                                _t1605 = _t1606
                            _t1604 = _t1605
                        _t1601 = _t1604
                    _t1600 = _t1601
                _t1599 = _t1600
            _t1598 = _t1599
        prediction857 = _t1598
        if prediction857 == 12:
            _t1614 = self.parse_boolean_value()
            boolean_value869 = _t1614
            _t1615 = logic_pb2.Value(boolean_value=boolean_value869)
            _t1613 = _t1615
        else:
            if prediction857 == 11:
                self.consume_literal("missing")
                _t1617 = logic_pb2.MissingValue()
                _t1618 = logic_pb2.Value(missing_value=_t1617)
                _t1616 = _t1618
            else:
                if prediction857 == 10:
                    formatted_decimal868 = self.consume_terminal("DECIMAL")
                    _t1620 = logic_pb2.Value(decimal_value=formatted_decimal868)
                    _t1619 = _t1620
                else:
                    if prediction857 == 9:
                        formatted_int128867 = self.consume_terminal("INT128")
                        _t1622 = logic_pb2.Value(int128_value=formatted_int128867)
                        _t1621 = _t1622
                    else:
                        if prediction857 == 8:
                            formatted_uint128866 = self.consume_terminal("UINT128")
                            _t1624 = logic_pb2.Value(uint128_value=formatted_uint128866)
                            _t1623 = _t1624
                        else:
                            if prediction857 == 7:
                                formatted_uint32865 = self.consume_terminal("UINT32")
                                _t1626 = logic_pb2.Value(uint32_value=formatted_uint32865)
                                _t1625 = _t1626
                            else:
                                if prediction857 == 6:
                                    formatted_float864 = self.consume_terminal("FLOAT")
                                    _t1628 = logic_pb2.Value(float_value=formatted_float864)
                                    _t1627 = _t1628
                                else:
                                    if prediction857 == 5:
                                        formatted_float32863 = self.consume_terminal("FLOAT32")
                                        _t1630 = logic_pb2.Value(float32_value=formatted_float32863)
                                        _t1629 = _t1630
                                    else:
                                        if prediction857 == 4:
                                            formatted_int862 = self.consume_terminal("INT")
                                            _t1632 = logic_pb2.Value(int_value=formatted_int862)
                                            _t1631 = _t1632
                                        else:
                                            if prediction857 == 3:
                                                formatted_int32861 = self.consume_terminal("INT32")
                                                _t1634 = logic_pb2.Value(int32_value=formatted_int32861)
                                                _t1633 = _t1634
                                            else:
                                                if prediction857 == 2:
                                                    formatted_string860 = self.consume_terminal("STRING")
                                                    _t1636 = logic_pb2.Value(string_value=formatted_string860)
                                                    _t1635 = _t1636
                                                else:
                                                    if prediction857 == 1:
                                                        _t1638 = self.parse_datetime()
                                                        datetime859 = _t1638
                                                        _t1639 = logic_pb2.Value(datetime_value=datetime859)
                                                        _t1637 = _t1639
                                                    else:
                                                        if prediction857 == 0:
                                                            _t1641 = self.parse_date()
                                                            date858 = _t1641
                                                            _t1642 = logic_pb2.Value(date_value=date858)
                                                            _t1640 = _t1642
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1637 = _t1640
                                                    _t1635 = _t1637
                                                _t1633 = _t1635
                                            _t1631 = _t1633
                                        _t1629 = _t1631
                                    _t1627 = _t1629
                                _t1625 = _t1627
                            _t1623 = _t1625
                        _t1621 = _t1623
                    _t1619 = _t1621
                _t1616 = _t1619
            _t1613 = _t1616
        result871 = _t1613
        self.record_span(span_start870, "Value")
        return result871

    def parse_date(self) -> logic_pb2.DateValue:
        span_start875 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int872 = self.consume_terminal("INT")
        formatted_int_3873 = self.consume_terminal("INT")
        formatted_int_4874 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1643 = logic_pb2.DateValue(year=int(formatted_int872), month=int(formatted_int_3873), day=int(formatted_int_4874))
        result876 = _t1643
        self.record_span(span_start875, "DateValue")
        return result876

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start884 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int877 = self.consume_terminal("INT")
        formatted_int_3878 = self.consume_terminal("INT")
        formatted_int_4879 = self.consume_terminal("INT")
        formatted_int_5880 = self.consume_terminal("INT")
        formatted_int_6881 = self.consume_terminal("INT")
        formatted_int_7882 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1644 = self.consume_terminal("INT")
        else:
            _t1644 = None
        formatted_int_8883 = _t1644
        self.consume_literal(")")
        _t1645 = logic_pb2.DateTimeValue(year=int(formatted_int877), month=int(formatted_int_3878), day=int(formatted_int_4879), hour=int(formatted_int_5880), minute=int(formatted_int_6881), second=int(formatted_int_7882), microsecond=int((formatted_int_8883 if formatted_int_8883 is not None else 0)))
        result885 = _t1645
        self.record_span(span_start884, "DateTimeValue")
        return result885

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start890 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs886 = []
        cond887 = self.match_lookahead_literal("(", 0)
        while cond887:
            _t1646 = self.parse_formula()
            item888 = _t1646
            xs886.append(item888)
            cond887 = self.match_lookahead_literal("(", 0)
        formulas889 = xs886
        self.consume_literal(")")
        _t1647 = logic_pb2.Conjunction(args=formulas889)
        result891 = _t1647
        self.record_span(span_start890, "Conjunction")
        return result891

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start896 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs892 = []
        cond893 = self.match_lookahead_literal("(", 0)
        while cond893:
            _t1648 = self.parse_formula()
            item894 = _t1648
            xs892.append(item894)
            cond893 = self.match_lookahead_literal("(", 0)
        formulas895 = xs892
        self.consume_literal(")")
        _t1649 = logic_pb2.Disjunction(args=formulas895)
        result897 = _t1649
        self.record_span(span_start896, "Disjunction")
        return result897

    def parse_not(self) -> logic_pb2.Not:
        span_start899 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1650 = self.parse_formula()
        formula898 = _t1650
        self.consume_literal(")")
        _t1651 = logic_pb2.Not(arg=formula898)
        result900 = _t1651
        self.record_span(span_start899, "Not")
        return result900

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start904 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1652 = self.parse_name()
        name901 = _t1652
        _t1653 = self.parse_ffi_args()
        ffi_args902 = _t1653
        _t1654 = self.parse_terms()
        terms903 = _t1654
        self.consume_literal(")")
        _t1655 = logic_pb2.FFI(name=name901, args=ffi_args902, terms=terms903)
        result905 = _t1655
        self.record_span(span_start904, "FFI")
        return result905

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol906 = self.consume_terminal("SYMBOL")
        return symbol906

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs907 = []
        cond908 = self.match_lookahead_literal("(", 0)
        while cond908:
            _t1656 = self.parse_abstraction()
            item909 = _t1656
            xs907.append(item909)
            cond908 = self.match_lookahead_literal("(", 0)
        abstractions910 = xs907
        self.consume_literal(")")
        return abstractions910

    def parse_atom(self) -> logic_pb2.Atom:
        span_start916 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1657 = self.parse_relation_id()
        relation_id911 = _t1657
        xs912 = []
        cond913 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond913:
            _t1658 = self.parse_term()
            item914 = _t1658
            xs912.append(item914)
            cond913 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms915 = xs912
        self.consume_literal(")")
        _t1659 = logic_pb2.Atom(name=relation_id911, terms=terms915)
        result917 = _t1659
        self.record_span(span_start916, "Atom")
        return result917

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start923 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1660 = self.parse_name()
        name918 = _t1660
        xs919 = []
        cond920 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond920:
            _t1661 = self.parse_term()
            item921 = _t1661
            xs919.append(item921)
            cond920 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms922 = xs919
        self.consume_literal(")")
        _t1662 = logic_pb2.Pragma(name=name918, terms=terms922)
        result924 = _t1662
        self.record_span(span_start923, "Pragma")
        return result924

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start940 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1664 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1665 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1666 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1667 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1668 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1669 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1670 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1671 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1672 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1673 = 7
                                                else:
                                                    _t1673 = -1
                                                _t1672 = _t1673
                                            _t1671 = _t1672
                                        _t1670 = _t1671
                                    _t1669 = _t1670
                                _t1668 = _t1669
                            _t1667 = _t1668
                        _t1666 = _t1667
                    _t1665 = _t1666
                _t1664 = _t1665
            _t1663 = _t1664
        else:
            _t1663 = -1
        prediction925 = _t1663
        if prediction925 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1675 = self.parse_name()
            name935 = _t1675
            xs936 = []
            cond937 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond937:
                _t1676 = self.parse_rel_term()
                item938 = _t1676
                xs936.append(item938)
                cond937 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms939 = xs936
            self.consume_literal(")")
            _t1677 = logic_pb2.Primitive(name=name935, terms=rel_terms939)
            _t1674 = _t1677
        else:
            if prediction925 == 8:
                _t1679 = self.parse_divide()
                divide934 = _t1679
                _t1678 = divide934
            else:
                if prediction925 == 7:
                    _t1681 = self.parse_multiply()
                    multiply933 = _t1681
                    _t1680 = multiply933
                else:
                    if prediction925 == 6:
                        _t1683 = self.parse_minus()
                        minus932 = _t1683
                        _t1682 = minus932
                    else:
                        if prediction925 == 5:
                            _t1685 = self.parse_add()
                            add931 = _t1685
                            _t1684 = add931
                        else:
                            if prediction925 == 4:
                                _t1687 = self.parse_gt_eq()
                                gt_eq930 = _t1687
                                _t1686 = gt_eq930
                            else:
                                if prediction925 == 3:
                                    _t1689 = self.parse_gt()
                                    gt929 = _t1689
                                    _t1688 = gt929
                                else:
                                    if prediction925 == 2:
                                        _t1691 = self.parse_lt_eq()
                                        lt_eq928 = _t1691
                                        _t1690 = lt_eq928
                                    else:
                                        if prediction925 == 1:
                                            _t1693 = self.parse_lt()
                                            lt927 = _t1693
                                            _t1692 = lt927
                                        else:
                                            if prediction925 == 0:
                                                _t1695 = self.parse_eq()
                                                eq926 = _t1695
                                                _t1694 = eq926
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1692 = _t1694
                                        _t1690 = _t1692
                                    _t1688 = _t1690
                                _t1686 = _t1688
                            _t1684 = _t1686
                        _t1682 = _t1684
                    _t1680 = _t1682
                _t1678 = _t1680
            _t1674 = _t1678
        result941 = _t1674
        self.record_span(span_start940, "Primitive")
        return result941

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start944 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1696 = self.parse_term()
        term942 = _t1696
        _t1697 = self.parse_term()
        term_3943 = _t1697
        self.consume_literal(")")
        _t1698 = logic_pb2.RelTerm(term=term942)
        _t1699 = logic_pb2.RelTerm(term=term_3943)
        _t1700 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1698, _t1699])
        result945 = _t1700
        self.record_span(span_start944, "Primitive")
        return result945

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start948 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1701 = self.parse_term()
        term946 = _t1701
        _t1702 = self.parse_term()
        term_3947 = _t1702
        self.consume_literal(")")
        _t1703 = logic_pb2.RelTerm(term=term946)
        _t1704 = logic_pb2.RelTerm(term=term_3947)
        _t1705 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1703, _t1704])
        result949 = _t1705
        self.record_span(span_start948, "Primitive")
        return result949

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start952 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1706 = self.parse_term()
        term950 = _t1706
        _t1707 = self.parse_term()
        term_3951 = _t1707
        self.consume_literal(")")
        _t1708 = logic_pb2.RelTerm(term=term950)
        _t1709 = logic_pb2.RelTerm(term=term_3951)
        _t1710 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1708, _t1709])
        result953 = _t1710
        self.record_span(span_start952, "Primitive")
        return result953

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start956 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1711 = self.parse_term()
        term954 = _t1711
        _t1712 = self.parse_term()
        term_3955 = _t1712
        self.consume_literal(")")
        _t1713 = logic_pb2.RelTerm(term=term954)
        _t1714 = logic_pb2.RelTerm(term=term_3955)
        _t1715 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1713, _t1714])
        result957 = _t1715
        self.record_span(span_start956, "Primitive")
        return result957

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start960 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1716 = self.parse_term()
        term958 = _t1716
        _t1717 = self.parse_term()
        term_3959 = _t1717
        self.consume_literal(")")
        _t1718 = logic_pb2.RelTerm(term=term958)
        _t1719 = logic_pb2.RelTerm(term=term_3959)
        _t1720 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1718, _t1719])
        result961 = _t1720
        self.record_span(span_start960, "Primitive")
        return result961

    def parse_add(self) -> logic_pb2.Primitive:
        span_start965 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1721 = self.parse_term()
        term962 = _t1721
        _t1722 = self.parse_term()
        term_3963 = _t1722
        _t1723 = self.parse_term()
        term_4964 = _t1723
        self.consume_literal(")")
        _t1724 = logic_pb2.RelTerm(term=term962)
        _t1725 = logic_pb2.RelTerm(term=term_3963)
        _t1726 = logic_pb2.RelTerm(term=term_4964)
        _t1727 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1724, _t1725, _t1726])
        result966 = _t1727
        self.record_span(span_start965, "Primitive")
        return result966

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start970 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1728 = self.parse_term()
        term967 = _t1728
        _t1729 = self.parse_term()
        term_3968 = _t1729
        _t1730 = self.parse_term()
        term_4969 = _t1730
        self.consume_literal(")")
        _t1731 = logic_pb2.RelTerm(term=term967)
        _t1732 = logic_pb2.RelTerm(term=term_3968)
        _t1733 = logic_pb2.RelTerm(term=term_4969)
        _t1734 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1731, _t1732, _t1733])
        result971 = _t1734
        self.record_span(span_start970, "Primitive")
        return result971

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start975 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1735 = self.parse_term()
        term972 = _t1735
        _t1736 = self.parse_term()
        term_3973 = _t1736
        _t1737 = self.parse_term()
        term_4974 = _t1737
        self.consume_literal(")")
        _t1738 = logic_pb2.RelTerm(term=term972)
        _t1739 = logic_pb2.RelTerm(term=term_3973)
        _t1740 = logic_pb2.RelTerm(term=term_4974)
        _t1741 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1738, _t1739, _t1740])
        result976 = _t1741
        self.record_span(span_start975, "Primitive")
        return result976

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start980 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1742 = self.parse_term()
        term977 = _t1742
        _t1743 = self.parse_term()
        term_3978 = _t1743
        _t1744 = self.parse_term()
        term_4979 = _t1744
        self.consume_literal(")")
        _t1745 = logic_pb2.RelTerm(term=term977)
        _t1746 = logic_pb2.RelTerm(term=term_3978)
        _t1747 = logic_pb2.RelTerm(term=term_4979)
        _t1748 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1745, _t1746, _t1747])
        result981 = _t1748
        self.record_span(span_start980, "Primitive")
        return result981

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start985 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1749 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1750 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1751 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1752 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1753 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1754 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1755 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1756 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1757 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1758 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1759 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1760 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1761 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1762 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1763 = 1
                                                                else:
                                                                    _t1763 = -1
                                                                _t1762 = _t1763
                                                            _t1761 = _t1762
                                                        _t1760 = _t1761
                                                    _t1759 = _t1760
                                                _t1758 = _t1759
                                            _t1757 = _t1758
                                        _t1756 = _t1757
                                    _t1755 = _t1756
                                _t1754 = _t1755
                            _t1753 = _t1754
                        _t1752 = _t1753
                    _t1751 = _t1752
                _t1750 = _t1751
            _t1749 = _t1750
        prediction982 = _t1749
        if prediction982 == 1:
            _t1765 = self.parse_term()
            term984 = _t1765
            _t1766 = logic_pb2.RelTerm(term=term984)
            _t1764 = _t1766
        else:
            if prediction982 == 0:
                _t1768 = self.parse_specialized_value()
                specialized_value983 = _t1768
                _t1769 = logic_pb2.RelTerm(specialized_value=specialized_value983)
                _t1767 = _t1769
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1764 = _t1767
        result986 = _t1764
        self.record_span(span_start985, "RelTerm")
        return result986

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start988 = self.span_start()
        self.consume_literal("#")
        _t1770 = self.parse_raw_value()
        raw_value987 = _t1770
        result989 = raw_value987
        self.record_span(span_start988, "Value")
        return result989

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start995 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1771 = self.parse_name()
        name990 = _t1771
        xs991 = []
        cond992 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond992:
            _t1772 = self.parse_rel_term()
            item993 = _t1772
            xs991.append(item993)
            cond992 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms994 = xs991
        self.consume_literal(")")
        _t1773 = logic_pb2.RelAtom(name=name990, terms=rel_terms994)
        result996 = _t1773
        self.record_span(span_start995, "RelAtom")
        return result996

    def parse_cast(self) -> logic_pb2.Cast:
        span_start999 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1774 = self.parse_term()
        term997 = _t1774
        _t1775 = self.parse_term()
        term_3998 = _t1775
        self.consume_literal(")")
        _t1776 = logic_pb2.Cast(input=term997, result=term_3998)
        result1000 = _t1776
        self.record_span(span_start999, "Cast")
        return result1000

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1001 = []
        cond1002 = self.match_lookahead_literal("(", 0)
        while cond1002:
            _t1777 = self.parse_attribute()
            item1003 = _t1777
            xs1001.append(item1003)
            cond1002 = self.match_lookahead_literal("(", 0)
        attributes1004 = xs1001
        self.consume_literal(")")
        return attributes1004

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1010 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1778 = self.parse_name()
        name1005 = _t1778
        xs1006 = []
        cond1007 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1007:
            _t1779 = self.parse_raw_value()
            item1008 = _t1779
            xs1006.append(item1008)
            cond1007 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1009 = xs1006
        self.consume_literal(")")
        _t1780 = logic_pb2.Attribute(name=name1005, args=raw_values1009)
        result1011 = _t1780
        self.record_span(span_start1010, "Attribute")
        return result1011

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1017 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1012 = []
        cond1013 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1013:
            _t1781 = self.parse_relation_id()
            item1014 = _t1781
            xs1012.append(item1014)
            cond1013 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1015 = xs1012
        _t1782 = self.parse_script()
        script1016 = _t1782
        self.consume_literal(")")
        _t1783 = logic_pb2.Algorithm(body=script1016)
        getattr(_t1783, 'global').extend(relation_ids1015)
        result1018 = _t1783
        self.record_span(span_start1017, "Algorithm")
        return result1018

    def parse_script(self) -> logic_pb2.Script:
        span_start1023 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1019 = []
        cond1020 = self.match_lookahead_literal("(", 0)
        while cond1020:
            _t1784 = self.parse_construct()
            item1021 = _t1784
            xs1019.append(item1021)
            cond1020 = self.match_lookahead_literal("(", 0)
        constructs1022 = xs1019
        self.consume_literal(")")
        _t1785 = logic_pb2.Script(constructs=constructs1022)
        result1024 = _t1785
        self.record_span(span_start1023, "Script")
        return result1024

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1028 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1787 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1788 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1789 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1790 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1791 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1792 = 1
                                else:
                                    _t1792 = -1
                                _t1791 = _t1792
                            _t1790 = _t1791
                        _t1789 = _t1790
                    _t1788 = _t1789
                _t1787 = _t1788
            _t1786 = _t1787
        else:
            _t1786 = -1
        prediction1025 = _t1786
        if prediction1025 == 1:
            _t1794 = self.parse_instruction()
            instruction1027 = _t1794
            _t1795 = logic_pb2.Construct(instruction=instruction1027)
            _t1793 = _t1795
        else:
            if prediction1025 == 0:
                _t1797 = self.parse_loop()
                loop1026 = _t1797
                _t1798 = logic_pb2.Construct(loop=loop1026)
                _t1796 = _t1798
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1793 = _t1796
        result1029 = _t1793
        self.record_span(span_start1028, "Construct")
        return result1029

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1032 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1799 = self.parse_init()
        init1030 = _t1799
        _t1800 = self.parse_script()
        script1031 = _t1800
        self.consume_literal(")")
        _t1801 = logic_pb2.Loop(init=init1030, body=script1031)
        result1033 = _t1801
        self.record_span(span_start1032, "Loop")
        return result1033

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1034 = []
        cond1035 = self.match_lookahead_literal("(", 0)
        while cond1035:
            _t1802 = self.parse_instruction()
            item1036 = _t1802
            xs1034.append(item1036)
            cond1035 = self.match_lookahead_literal("(", 0)
        instructions1037 = xs1034
        self.consume_literal(")")
        return instructions1037

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1044 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1804 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1805 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1806 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1807 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1808 = 0
                            else:
                                _t1808 = -1
                            _t1807 = _t1808
                        _t1806 = _t1807
                    _t1805 = _t1806
                _t1804 = _t1805
            _t1803 = _t1804
        else:
            _t1803 = -1
        prediction1038 = _t1803
        if prediction1038 == 4:
            _t1810 = self.parse_monus_def()
            monus_def1043 = _t1810
            _t1811 = logic_pb2.Instruction(monus_def=monus_def1043)
            _t1809 = _t1811
        else:
            if prediction1038 == 3:
                _t1813 = self.parse_monoid_def()
                monoid_def1042 = _t1813
                _t1814 = logic_pb2.Instruction(monoid_def=monoid_def1042)
                _t1812 = _t1814
            else:
                if prediction1038 == 2:
                    _t1816 = self.parse_break()
                    break1041 = _t1816
                    _t1817 = logic_pb2.Instruction()
                    getattr(_t1817, 'break').CopyFrom(break1041)
                    _t1815 = _t1817
                else:
                    if prediction1038 == 1:
                        _t1819 = self.parse_upsert()
                        upsert1040 = _t1819
                        _t1820 = logic_pb2.Instruction(upsert=upsert1040)
                        _t1818 = _t1820
                    else:
                        if prediction1038 == 0:
                            _t1822 = self.parse_assign()
                            assign1039 = _t1822
                            _t1823 = logic_pb2.Instruction(assign=assign1039)
                            _t1821 = _t1823
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1818 = _t1821
                    _t1815 = _t1818
                _t1812 = _t1815
            _t1809 = _t1812
        result1045 = _t1809
        self.record_span(span_start1044, "Instruction")
        return result1045

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1049 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1824 = self.parse_relation_id()
        relation_id1046 = _t1824
        _t1825 = self.parse_abstraction()
        abstraction1047 = _t1825
        if self.match_lookahead_literal("(", 0):
            _t1827 = self.parse_attrs()
            _t1826 = _t1827
        else:
            _t1826 = None
        attrs1048 = _t1826
        self.consume_literal(")")
        _t1828 = logic_pb2.Assign(name=relation_id1046, body=abstraction1047, attrs=(attrs1048 if attrs1048 is not None else []))
        result1050 = _t1828
        self.record_span(span_start1049, "Assign")
        return result1050

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1054 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1829 = self.parse_relation_id()
        relation_id1051 = _t1829
        _t1830 = self.parse_abstraction_with_arity()
        abstraction_with_arity1052 = _t1830
        if self.match_lookahead_literal("(", 0):
            _t1832 = self.parse_attrs()
            _t1831 = _t1832
        else:
            _t1831 = None
        attrs1053 = _t1831
        self.consume_literal(")")
        _t1833 = logic_pb2.Upsert(name=relation_id1051, body=abstraction_with_arity1052[0], attrs=(attrs1053 if attrs1053 is not None else []), value_arity=abstraction_with_arity1052[1])
        result1055 = _t1833
        self.record_span(span_start1054, "Upsert")
        return result1055

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1834 = self.parse_bindings()
        bindings1056 = _t1834
        _t1835 = self.parse_formula()
        formula1057 = _t1835
        self.consume_literal(")")
        _t1836 = logic_pb2.Abstraction(vars=(list(bindings1056[0]) + list(bindings1056[1] if bindings1056[1] is not None else [])), value=formula1057)
        return (_t1836, len(bindings1056[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1061 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1837 = self.parse_relation_id()
        relation_id1058 = _t1837
        _t1838 = self.parse_abstraction()
        abstraction1059 = _t1838
        if self.match_lookahead_literal("(", 0):
            _t1840 = self.parse_attrs()
            _t1839 = _t1840
        else:
            _t1839 = None
        attrs1060 = _t1839
        self.consume_literal(")")
        _t1841 = logic_pb2.Break(name=relation_id1058, body=abstraction1059, attrs=(attrs1060 if attrs1060 is not None else []))
        result1062 = _t1841
        self.record_span(span_start1061, "Break")
        return result1062

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1067 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1842 = self.parse_monoid()
        monoid1063 = _t1842
        _t1843 = self.parse_relation_id()
        relation_id1064 = _t1843
        _t1844 = self.parse_abstraction_with_arity()
        abstraction_with_arity1065 = _t1844
        if self.match_lookahead_literal("(", 0):
            _t1846 = self.parse_attrs()
            _t1845 = _t1846
        else:
            _t1845 = None
        attrs1066 = _t1845
        self.consume_literal(")")
        _t1847 = logic_pb2.MonoidDef(monoid=monoid1063, name=relation_id1064, body=abstraction_with_arity1065[0], attrs=(attrs1066 if attrs1066 is not None else []), value_arity=abstraction_with_arity1065[1])
        result1068 = _t1847
        self.record_span(span_start1067, "MonoidDef")
        return result1068

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1074 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1849 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1850 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1851 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1852 = 2
                        else:
                            _t1852 = -1
                        _t1851 = _t1852
                    _t1850 = _t1851
                _t1849 = _t1850
            _t1848 = _t1849
        else:
            _t1848 = -1
        prediction1069 = _t1848
        if prediction1069 == 3:
            _t1854 = self.parse_sum_monoid()
            sum_monoid1073 = _t1854
            _t1855 = logic_pb2.Monoid(sum_monoid=sum_monoid1073)
            _t1853 = _t1855
        else:
            if prediction1069 == 2:
                _t1857 = self.parse_max_monoid()
                max_monoid1072 = _t1857
                _t1858 = logic_pb2.Monoid(max_monoid=max_monoid1072)
                _t1856 = _t1858
            else:
                if prediction1069 == 1:
                    _t1860 = self.parse_min_monoid()
                    min_monoid1071 = _t1860
                    _t1861 = logic_pb2.Monoid(min_monoid=min_monoid1071)
                    _t1859 = _t1861
                else:
                    if prediction1069 == 0:
                        _t1863 = self.parse_or_monoid()
                        or_monoid1070 = _t1863
                        _t1864 = logic_pb2.Monoid(or_monoid=or_monoid1070)
                        _t1862 = _t1864
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1859 = _t1862
                _t1856 = _t1859
            _t1853 = _t1856
        result1075 = _t1853
        self.record_span(span_start1074, "Monoid")
        return result1075

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1076 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1865 = logic_pb2.OrMonoid()
        result1077 = _t1865
        self.record_span(span_start1076, "OrMonoid")
        return result1077

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1079 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1866 = self.parse_type()
        type1078 = _t1866
        self.consume_literal(")")
        _t1867 = logic_pb2.MinMonoid(type=type1078)
        result1080 = _t1867
        self.record_span(span_start1079, "MinMonoid")
        return result1080

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1082 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1868 = self.parse_type()
        type1081 = _t1868
        self.consume_literal(")")
        _t1869 = logic_pb2.MaxMonoid(type=type1081)
        result1083 = _t1869
        self.record_span(span_start1082, "MaxMonoid")
        return result1083

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1085 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1870 = self.parse_type()
        type1084 = _t1870
        self.consume_literal(")")
        _t1871 = logic_pb2.SumMonoid(type=type1084)
        result1086 = _t1871
        self.record_span(span_start1085, "SumMonoid")
        return result1086

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1091 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1872 = self.parse_monoid()
        monoid1087 = _t1872
        _t1873 = self.parse_relation_id()
        relation_id1088 = _t1873
        _t1874 = self.parse_abstraction_with_arity()
        abstraction_with_arity1089 = _t1874
        if self.match_lookahead_literal("(", 0):
            _t1876 = self.parse_attrs()
            _t1875 = _t1876
        else:
            _t1875 = None
        attrs1090 = _t1875
        self.consume_literal(")")
        _t1877 = logic_pb2.MonusDef(monoid=monoid1087, name=relation_id1088, body=abstraction_with_arity1089[0], attrs=(attrs1090 if attrs1090 is not None else []), value_arity=abstraction_with_arity1089[1])
        result1092 = _t1877
        self.record_span(span_start1091, "MonusDef")
        return result1092

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1097 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1878 = self.parse_relation_id()
        relation_id1093 = _t1878
        _t1879 = self.parse_abstraction()
        abstraction1094 = _t1879
        _t1880 = self.parse_functional_dependency_keys()
        functional_dependency_keys1095 = _t1880
        _t1881 = self.parse_functional_dependency_values()
        functional_dependency_values1096 = _t1881
        self.consume_literal(")")
        _t1882 = logic_pb2.FunctionalDependency(guard=abstraction1094, keys=functional_dependency_keys1095, values=functional_dependency_values1096)
        _t1883 = logic_pb2.Constraint(name=relation_id1093, functional_dependency=_t1882)
        result1098 = _t1883
        self.record_span(span_start1097, "Constraint")
        return result1098

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1099 = []
        cond1100 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1100:
            _t1884 = self.parse_var()
            item1101 = _t1884
            xs1099.append(item1101)
            cond1100 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1102 = xs1099
        self.consume_literal(")")
        return vars1102

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1103 = []
        cond1104 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1104:
            _t1885 = self.parse_var()
            item1105 = _t1885
            xs1103.append(item1105)
            cond1104 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1106 = xs1103
        self.consume_literal(")")
        return vars1106

    def parse_data(self) -> logic_pb2.Data:
        span_start1112 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1887 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1888 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1889 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1890 = 1
                        else:
                            _t1890 = -1
                        _t1889 = _t1890
                    _t1888 = _t1889
                _t1887 = _t1888
            _t1886 = _t1887
        else:
            _t1886 = -1
        prediction1107 = _t1886
        if prediction1107 == 3:
            _t1892 = self.parse_iceberg_data()
            iceberg_data1111 = _t1892
            _t1893 = logic_pb2.Data(iceberg_data=iceberg_data1111)
            _t1891 = _t1893
        else:
            if prediction1107 == 2:
                _t1895 = self.parse_csv_data()
                csv_data1110 = _t1895
                _t1896 = logic_pb2.Data(csv_data=csv_data1110)
                _t1894 = _t1896
            else:
                if prediction1107 == 1:
                    _t1898 = self.parse_betree_relation()
                    betree_relation1109 = _t1898
                    _t1899 = logic_pb2.Data(betree_relation=betree_relation1109)
                    _t1897 = _t1899
                else:
                    if prediction1107 == 0:
                        _t1901 = self.parse_edb()
                        edb1108 = _t1901
                        _t1902 = logic_pb2.Data(edb=edb1108)
                        _t1900 = _t1902
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1897 = _t1900
                _t1894 = _t1897
            _t1891 = _t1894
        result1113 = _t1891
        self.record_span(span_start1112, "Data")
        return result1113

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1117 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1903 = self.parse_relation_id()
        relation_id1114 = _t1903
        _t1904 = self.parse_edb_path()
        edb_path1115 = _t1904
        _t1905 = self.parse_edb_types()
        edb_types1116 = _t1905
        self.consume_literal(")")
        _t1906 = logic_pb2.EDB(target_id=relation_id1114, path=edb_path1115, types=edb_types1116)
        result1118 = _t1906
        self.record_span(span_start1117, "EDB")
        return result1118

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1119 = []
        cond1120 = self.match_lookahead_terminal("STRING", 0)
        while cond1120:
            item1121 = self.consume_terminal("STRING")
            xs1119.append(item1121)
            cond1120 = self.match_lookahead_terminal("STRING", 0)
        strings1122 = xs1119
        self.consume_literal("]")
        return strings1122

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1123 = []
        cond1124 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1124:
            _t1907 = self.parse_type()
            item1125 = _t1907
            xs1123.append(item1125)
            cond1124 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1126 = xs1123
        self.consume_literal("]")
        return types1126

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1129 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1908 = self.parse_relation_id()
        relation_id1127 = _t1908
        _t1909 = self.parse_betree_info()
        betree_info1128 = _t1909
        self.consume_literal(")")
        _t1910 = logic_pb2.BeTreeRelation(name=relation_id1127, relation_info=betree_info1128)
        result1130 = _t1910
        self.record_span(span_start1129, "BeTreeRelation")
        return result1130

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1134 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1911 = self.parse_betree_info_key_types()
        betree_info_key_types1131 = _t1911
        _t1912 = self.parse_betree_info_value_types()
        betree_info_value_types1132 = _t1912
        _t1913 = self.parse_config_dict()
        config_dict1133 = _t1913
        self.consume_literal(")")
        _t1914 = self.construct_betree_info(betree_info_key_types1131, betree_info_value_types1132, config_dict1133)
        result1135 = _t1914
        self.record_span(span_start1134, "BeTreeInfo")
        return result1135

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1136 = []
        cond1137 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1137:
            _t1915 = self.parse_type()
            item1138 = _t1915
            xs1136.append(item1138)
            cond1137 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1139 = xs1136
        self.consume_literal(")")
        return types1139

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1140 = []
        cond1141 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1141:
            _t1916 = self.parse_type()
            item1142 = _t1916
            xs1140.append(item1142)
            cond1141 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1143 = xs1140
        self.consume_literal(")")
        return types1143

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1148 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1917 = self.parse_csvlocator()
        csvlocator1144 = _t1917
        _t1918 = self.parse_csv_config()
        csv_config1145 = _t1918
        _t1919 = self.parse_gnf_columns()
        gnf_columns1146 = _t1919
        _t1920 = self.parse_csv_asof()
        csv_asof1147 = _t1920
        self.consume_literal(")")
        _t1921 = logic_pb2.CSVData(locator=csvlocator1144, config=csv_config1145, columns=gnf_columns1146, asof=csv_asof1147)
        result1149 = _t1921
        self.record_span(span_start1148, "CSVData")
        return result1149

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1152 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1923 = self.parse_csv_locator_paths()
            _t1922 = _t1923
        else:
            _t1922 = None
        csv_locator_paths1150 = _t1922
        if self.match_lookahead_literal("(", 0):
            _t1925 = self.parse_csv_locator_inline_data()
            _t1924 = _t1925
        else:
            _t1924 = None
        csv_locator_inline_data1151 = _t1924
        self.consume_literal(")")
        _t1926 = logic_pb2.CSVLocator(paths=(csv_locator_paths1150 if csv_locator_paths1150 is not None else []), inline_data=(csv_locator_inline_data1151 if csv_locator_inline_data1151 is not None else "").encode())
        result1153 = _t1926
        self.record_span(span_start1152, "CSVLocator")
        return result1153

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1154 = []
        cond1155 = self.match_lookahead_terminal("STRING", 0)
        while cond1155:
            item1156 = self.consume_terminal("STRING")
            xs1154.append(item1156)
            cond1155 = self.match_lookahead_terminal("STRING", 0)
        strings1157 = xs1154
        self.consume_literal(")")
        return strings1157

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1158 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1158

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1160 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1927 = self.parse_config_dict()
        config_dict1159 = _t1927
        self.consume_literal(")")
        _t1928 = self.construct_csv_config(config_dict1159)
        result1161 = _t1928
        self.record_span(span_start1160, "CSVConfig")
        return result1161

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1162 = []
        cond1163 = self.match_lookahead_literal("(", 0)
        while cond1163:
            _t1929 = self.parse_gnf_column()
            item1164 = _t1929
            xs1162.append(item1164)
            cond1163 = self.match_lookahead_literal("(", 0)
        gnf_columns1165 = xs1162
        self.consume_literal(")")
        return gnf_columns1165

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1172 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1930 = self.parse_gnf_column_path()
        gnf_column_path1166 = _t1930
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1932 = self.parse_relation_id()
            _t1931 = _t1932
        else:
            _t1931 = None
        relation_id1167 = _t1931
        self.consume_literal("[")
        xs1168 = []
        cond1169 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1169:
            _t1933 = self.parse_type()
            item1170 = _t1933
            xs1168.append(item1170)
            cond1169 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1171 = xs1168
        self.consume_literal("]")
        self.consume_literal(")")
        _t1934 = logic_pb2.GNFColumn(column_path=gnf_column_path1166, target_id=relation_id1167, types=types1171)
        result1173 = _t1934
        self.record_span(span_start1172, "GNFColumn")
        return result1173

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1935 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1936 = 0
            else:
                _t1936 = -1
            _t1935 = _t1936
        prediction1174 = _t1935
        if prediction1174 == 1:
            self.consume_literal("[")
            xs1176 = []
            cond1177 = self.match_lookahead_terminal("STRING", 0)
            while cond1177:
                item1178 = self.consume_terminal("STRING")
                xs1176.append(item1178)
                cond1177 = self.match_lookahead_terminal("STRING", 0)
            strings1179 = xs1176
            self.consume_literal("]")
            _t1937 = strings1179
        else:
            if prediction1174 == 0:
                string1175 = self.consume_terminal("STRING")
                _t1938 = [string1175]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1937 = _t1938
        return _t1937

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1180 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1180

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1185 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1939 = self.parse_iceberg_locator()
        iceberg_locator1181 = _t1939
        _t1940 = self.parse_iceberg_config()
        iceberg_config1182 = _t1940
        _t1941 = self.parse_gnf_columns()
        gnf_columns1183 = _t1941
        if self.match_lookahead_literal("(", 0):
            _t1943 = self.parse_iceberg_to_snapshot()
            _t1942 = _t1943
        else:
            _t1942 = None
        iceberg_to_snapshot1184 = _t1942
        self.consume_literal(")")
        _t1944 = logic_pb2.IcebergData(locator=iceberg_locator1181, config=iceberg_config1182, columns=gnf_columns1183, to_snapshot=iceberg_to_snapshot1184)
        result1186 = _t1944
        self.record_span(span_start1185, "IcebergData")
        return result1186

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1193 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1187 = self.consume_terminal("STRING")
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1188 = []
        cond1189 = self.match_lookahead_terminal("STRING", 0)
        while cond1189:
            item1190 = self.consume_terminal("STRING")
            xs1188.append(item1190)
            cond1189 = self.match_lookahead_terminal("STRING", 0)
        strings1191 = xs1188
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string_121192 = self.consume_terminal("STRING")
        self.consume_literal(")")
        self.consume_literal(")")
        _t1945 = logic_pb2.IcebergLocator(table_name=string1187, namespace=strings1191, warehouse=string_121192)
        result1194 = _t1945
        self.record_span(span_start1193, "IcebergLocator")
        return result1194

    def parse_iceberg_config(self) -> logic_pb2.IcebergConfig:
        span_start1205 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_config")
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1195 = self.consume_terminal("STRING")
        self.consume_literal(")")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t1947 = self.parse_iceberg_config_scope()
            _t1946 = _t1947
        else:
            _t1946 = None
        iceberg_config_scope1196 = _t1946
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1197 = []
        cond1198 = self.match_lookahead_literal("(", 0)
        while cond1198:
            _t1948 = self.parse_iceberg_property_entry()
            item1199 = _t1948
            xs1197.append(item1199)
            cond1198 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1200 = xs1197
        self.consume_literal(")")
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1201 = []
        cond1202 = self.match_lookahead_literal("(", 0)
        while cond1202:
            _t1949 = self.parse_iceberg_property_entry()
            item1203 = _t1949
            xs1201.append(item1203)
            cond1202 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys_131204 = xs1201
        self.consume_literal(")")
        self.consume_literal(")")
        _t1950 = self.construct_iceberg_config(string1195, iceberg_config_scope1196, iceberg_property_entrys1200, iceberg_property_entrys_131204)
        result1206 = _t1950
        self.record_span(span_start1205, "IcebergConfig")
        return result1206

    def parse_iceberg_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1207 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1207

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1208 = self.consume_terminal("STRING")
        string_31209 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1208, string_31209,)

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1210 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1210

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1212 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t1951 = self.parse_fragment_id()
        fragment_id1211 = _t1951
        self.consume_literal(")")
        _t1952 = transactions_pb2.Undefine(fragment_id=fragment_id1211)
        result1213 = _t1952
        self.record_span(span_start1212, "Undefine")
        return result1213

    def parse_context(self) -> transactions_pb2.Context:
        span_start1218 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1214 = []
        cond1215 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1215:
            _t1953 = self.parse_relation_id()
            item1216 = _t1953
            xs1214.append(item1216)
            cond1215 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1217 = xs1214
        self.consume_literal(")")
        _t1954 = transactions_pb2.Context(relations=relation_ids1217)
        result1219 = _t1954
        self.record_span(span_start1218, "Context")
        return result1219

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1224 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1220 = []
        cond1221 = self.match_lookahead_literal("[", 0)
        while cond1221:
            _t1955 = self.parse_snapshot_mapping()
            item1222 = _t1955
            xs1220.append(item1222)
            cond1221 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1223 = xs1220
        self.consume_literal(")")
        _t1956 = transactions_pb2.Snapshot(mappings=snapshot_mappings1223)
        result1225 = _t1956
        self.record_span(span_start1224, "Snapshot")
        return result1225

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1228 = self.span_start()
        _t1957 = self.parse_edb_path()
        edb_path1226 = _t1957
        _t1958 = self.parse_relation_id()
        relation_id1227 = _t1958
        _t1959 = transactions_pb2.SnapshotMapping(destination_path=edb_path1226, source_relation=relation_id1227)
        result1229 = _t1959
        self.record_span(span_start1228, "SnapshotMapping")
        return result1229

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1230 = []
        cond1231 = self.match_lookahead_literal("(", 0)
        while cond1231:
            _t1960 = self.parse_read()
            item1232 = _t1960
            xs1230.append(item1232)
            cond1231 = self.match_lookahead_literal("(", 0)
        reads1233 = xs1230
        self.consume_literal(")")
        return reads1233

    def parse_read(self) -> transactions_pb2.Read:
        span_start1240 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t1962 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t1963 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t1964 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t1965 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t1966 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t1967 = 3
                                else:
                                    _t1967 = -1
                                _t1966 = _t1967
                            _t1965 = _t1966
                        _t1964 = _t1965
                    _t1963 = _t1964
                _t1962 = _t1963
            _t1961 = _t1962
        else:
            _t1961 = -1
        prediction1234 = _t1961
        if prediction1234 == 4:
            _t1969 = self.parse_export()
            export1239 = _t1969
            _t1970 = transactions_pb2.Read(export=export1239)
            _t1968 = _t1970
        else:
            if prediction1234 == 3:
                _t1972 = self.parse_abort()
                abort1238 = _t1972
                _t1973 = transactions_pb2.Read(abort=abort1238)
                _t1971 = _t1973
            else:
                if prediction1234 == 2:
                    _t1975 = self.parse_what_if()
                    what_if1237 = _t1975
                    _t1976 = transactions_pb2.Read(what_if=what_if1237)
                    _t1974 = _t1976
                else:
                    if prediction1234 == 1:
                        _t1978 = self.parse_output()
                        output1236 = _t1978
                        _t1979 = transactions_pb2.Read(output=output1236)
                        _t1977 = _t1979
                    else:
                        if prediction1234 == 0:
                            _t1981 = self.parse_demand()
                            demand1235 = _t1981
                            _t1982 = transactions_pb2.Read(demand=demand1235)
                            _t1980 = _t1982
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1977 = _t1980
                    _t1974 = _t1977
                _t1971 = _t1974
            _t1968 = _t1971
        result1241 = _t1968
        self.record_span(span_start1240, "Read")
        return result1241

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1243 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t1983 = self.parse_relation_id()
        relation_id1242 = _t1983
        self.consume_literal(")")
        _t1984 = transactions_pb2.Demand(relation_id=relation_id1242)
        result1244 = _t1984
        self.record_span(span_start1243, "Demand")
        return result1244

    def parse_output(self) -> transactions_pb2.Output:
        span_start1247 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t1985 = self.parse_name()
        name1245 = _t1985
        _t1986 = self.parse_relation_id()
        relation_id1246 = _t1986
        self.consume_literal(")")
        _t1987 = transactions_pb2.Output(name=name1245, relation_id=relation_id1246)
        result1248 = _t1987
        self.record_span(span_start1247, "Output")
        return result1248

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1251 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t1988 = self.parse_name()
        name1249 = _t1988
        _t1989 = self.parse_epoch()
        epoch1250 = _t1989
        self.consume_literal(")")
        _t1990 = transactions_pb2.WhatIf(branch=name1249, epoch=epoch1250)
        result1252 = _t1990
        self.record_span(span_start1251, "WhatIf")
        return result1252

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1255 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t1992 = self.parse_name()
            _t1991 = _t1992
        else:
            _t1991 = None
        name1253 = _t1991
        _t1993 = self.parse_relation_id()
        relation_id1254 = _t1993
        self.consume_literal(")")
        _t1994 = transactions_pb2.Abort(name=(name1253 if name1253 is not None else "abort"), relation_id=relation_id1254)
        result1256 = _t1994
        self.record_span(span_start1255, "Abort")
        return result1256

    def parse_export(self) -> transactions_pb2.Export:
        span_start1260 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t1996 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t1997 = 0
                else:
                    _t1997 = -1
                _t1996 = _t1997
            _t1995 = _t1996
        else:
            _t1995 = -1
        prediction1257 = _t1995
        if prediction1257 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t1999 = self.parse_export_iceberg_config()
            export_iceberg_config1259 = _t1999
            self.consume_literal(")")
            _t2000 = transactions_pb2.Export(iceberg_config=export_iceberg_config1259)
            _t1998 = _t2000
        else:
            if prediction1257 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2002 = self.parse_export_csv_config()
                export_csv_config1258 = _t2002
                self.consume_literal(")")
                _t2003 = transactions_pb2.Export(csv_config=export_csv_config1258)
                _t2001 = _t2003
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1998 = _t2001
        result1261 = _t1998
        self.record_span(span_start1260, "Export")
        return result1261

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1269 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2005 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2006 = 1
                else:
                    _t2006 = -1
                _t2005 = _t2006
            _t2004 = _t2005
        else:
            _t2004 = -1
        prediction1262 = _t2004
        if prediction1262 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2008 = self.parse_export_csv_path()
            export_csv_path1266 = _t2008
            _t2009 = self.parse_export_csv_columns_list()
            export_csv_columns_list1267 = _t2009
            _t2010 = self.parse_config_dict()
            config_dict1268 = _t2010
            self.consume_literal(")")
            _t2011 = self.construct_export_csv_config(export_csv_path1266, export_csv_columns_list1267, config_dict1268)
            _t2007 = _t2011
        else:
            if prediction1262 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2013 = self.parse_export_csv_path()
                export_csv_path1263 = _t2013
                _t2014 = self.parse_export_csv_source()
                export_csv_source1264 = _t2014
                _t2015 = self.parse_csv_config()
                csv_config1265 = _t2015
                self.consume_literal(")")
                _t2016 = self.construct_export_csv_config_with_source(export_csv_path1263, export_csv_source1264, csv_config1265)
                _t2012 = _t2016
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2007 = _t2012
        result1270 = _t2007
        self.record_span(span_start1269, "ExportCSVConfig")
        return result1270

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1271 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1271

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1278 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2018 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2019 = 0
                else:
                    _t2019 = -1
                _t2018 = _t2019
            _t2017 = _t2018
        else:
            _t2017 = -1
        prediction1272 = _t2017
        if prediction1272 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2021 = self.parse_relation_id()
            relation_id1277 = _t2021
            self.consume_literal(")")
            _t2022 = transactions_pb2.ExportCSVSource(table_def=relation_id1277)
            _t2020 = _t2022
        else:
            if prediction1272 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1273 = []
                cond1274 = self.match_lookahead_literal("(", 0)
                while cond1274:
                    _t2024 = self.parse_export_csv_column()
                    item1275 = _t2024
                    xs1273.append(item1275)
                    cond1274 = self.match_lookahead_literal("(", 0)
                export_csv_columns1276 = xs1273
                self.consume_literal(")")
                _t2025 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1276)
                _t2026 = transactions_pb2.ExportCSVSource(gnf_columns=_t2025)
                _t2023 = _t2026
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2020 = _t2023
        result1279 = _t2020
        self.record_span(span_start1278, "ExportCSVSource")
        return result1279

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1282 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1280 = self.consume_terminal("STRING")
        _t2027 = self.parse_relation_id()
        relation_id1281 = _t2027
        self.consume_literal(")")
        _t2028 = transactions_pb2.ExportCSVColumn(column_name=string1280, column_data=relation_id1281)
        result1283 = _t2028
        self.record_span(span_start1282, "ExportCSVColumn")
        return result1283

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1284 = []
        cond1285 = self.match_lookahead_literal("(", 0)
        while cond1285:
            _t2029 = self.parse_export_csv_column()
            item1286 = _t2029
            xs1284.append(item1286)
            cond1285 = self.match_lookahead_literal("(", 0)
        export_csv_columns1287 = xs1284
        self.consume_literal(")")
        return export_csv_columns1287

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1295 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2030 = self.parse_iceberg_locator()
        iceberg_locator1288 = _t2030
        _t2031 = self.parse_iceberg_config()
        iceberg_config1289 = _t2031
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1290 = []
        cond1291 = self.match_lookahead_literal("(", 0)
        while cond1291:
            _t2032 = self.parse_iceberg_export_column()
            item1292 = _t2032
            xs1290.append(item1292)
            cond1291 = self.match_lookahead_literal("(", 0)
        iceberg_export_columns1293 = xs1290
        self.consume_literal(")")
        if self.match_lookahead_literal("{", 0):
            _t2034 = self.parse_config_dict()
            _t2033 = _t2034
        else:
            _t2033 = None
        config_dict1294 = _t2033
        self.consume_literal(")")
        _t2035 = self.construct_export_iceberg_config_full(iceberg_locator1288, iceberg_config1289, iceberg_export_columns1293, config_dict1294)
        result1296 = _t2035
        self.record_span(span_start1295, "ExportIcebergConfig")
        return result1296

    def parse_iceberg_export_column(self) -> transactions_pb2.IcebergExportColumn:
        span_start1300 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_column")
        string1297 = self.consume_terminal("STRING")
        _t2036 = self.parse_type()
        type1298 = _t2036
        _t2037 = self.parse_boolean_value()
        boolean_value1299 = _t2037
        self.consume_literal(")")
        _t2038 = transactions_pb2.IcebergExportColumn(name=string1297, type=type1298, nullable=boolean_value1299)
        result1301 = _t2038
        self.record_span(span_start1300, "IcebergExportColumn")
        return result1301


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
