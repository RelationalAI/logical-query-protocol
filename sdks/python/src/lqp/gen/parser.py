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
        re.compile(r"[a-zA-Z_][a-zA-Z0-9_.#/-]*"),
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
<<<<<<< HEAD
            _t2100 = value.HasField("int32_value")
        else:
            _t2100 = False
        if _t2100:
            assert value is not None
            return value.int32_value
        else:
            _t2101 = None
=======
            _t2187 = value.HasField("int32_value")
        else:
            _t2187 = False
        if _t2187:
            assert value is not None
            return value.int32_value
        else:
            _t2188 = None
>>>>>>> origin/main
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
<<<<<<< HEAD
            _t2102 = value.HasField("int_value")
        else:
            _t2102 = False
        if _t2102:
            assert value is not None
            return value.int_value
        else:
            _t2103 = None
=======
            _t2189 = value.HasField("int_value")
        else:
            _t2189 = False
        if _t2189:
            assert value is not None
            return value.int_value
        else:
            _t2190 = None
>>>>>>> origin/main
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
<<<<<<< HEAD
            _t2104 = value.HasField("string_value")
        else:
            _t2104 = False
        if _t2104:
            assert value is not None
            return value.string_value
        else:
            _t2105 = None
=======
            _t2191 = value.HasField("string_value")
        else:
            _t2191 = False
        if _t2191:
            assert value is not None
            return value.string_value
        else:
            _t2192 = None
>>>>>>> origin/main
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
<<<<<<< HEAD
            _t2106 = value.HasField("boolean_value")
        else:
            _t2106 = False
        if _t2106:
            assert value is not None
            return value.boolean_value
        else:
            _t2107 = None
=======
            _t2193 = value.HasField("boolean_value")
        else:
            _t2193 = False
        if _t2193:
            assert value is not None
            return value.boolean_value
        else:
            _t2194 = None
>>>>>>> origin/main
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
<<<<<<< HEAD
            _t2108 = value.HasField("string_value")
        else:
            _t2108 = False
        if _t2108:
            assert value is not None
            return [value.string_value]
        else:
            _t2109 = None
=======
            _t2195 = value.HasField("string_value")
        else:
            _t2195 = False
        if _t2195:
            assert value is not None
            return [value.string_value]
        else:
            _t2196 = None
>>>>>>> origin/main
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
<<<<<<< HEAD
            _t2110 = value.HasField("int_value")
        else:
            _t2110 = False
        if _t2110:
            assert value is not None
            return value.int_value
        else:
            _t2111 = None
=======
            _t2197 = value.HasField("int_value")
        else:
            _t2197 = False
        if _t2197:
            assert value is not None
            return value.int_value
        else:
            _t2198 = None
>>>>>>> origin/main
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
<<<<<<< HEAD
            _t2112 = value.HasField("float_value")
        else:
            _t2112 = False
        if _t2112:
            assert value is not None
            return value.float_value
        else:
            _t2113 = None
=======
            _t2199 = value.HasField("float_value")
        else:
            _t2199 = False
        if _t2199:
            assert value is not None
            return value.float_value
        else:
            _t2200 = None
>>>>>>> origin/main
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
<<<<<<< HEAD
            _t2114 = value.HasField("string_value")
        else:
            _t2114 = False
        if _t2114:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2115 = None
=======
            _t2201 = value.HasField("string_value")
        else:
            _t2201 = False
        if _t2201:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2202 = None
>>>>>>> origin/main
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
<<<<<<< HEAD
            _t2116 = value.HasField("uint128_value")
        else:
            _t2116 = False
        if _t2116:
            assert value is not None
            return value.uint128_value
        else:
            _t2117 = None
=======
            _t2203 = value.HasField("uint128_value")
        else:
            _t2203 = False
        if _t2203:
            assert value is not None
            return value.uint128_value
        else:
            _t2204 = None
>>>>>>> origin/main
        return None

    def construct_non_cdc_relations(self, targets: Sequence[logic_pb2.TargetRelation]) -> logic_pb2.TargetRelations:
        _t2205 = logic_pb2.PlainTargets(targets=targets)
        _t2206 = logic_pb2.TargetRelations(keys=[], plain=_t2205)
        return _t2206

    def construct_cdc_relations(self, inserts: Sequence[logic_pb2.TargetRelation], deletes: Sequence[logic_pb2.TargetRelation]) -> logic_pb2.TargetRelations:
        _t2207 = logic_pb2.CDCTargets(inserts=inserts, deletes=deletes)
        _t2208 = logic_pb2.TargetRelations(keys=[], cdc=_t2207)
        return _t2208

    def construct_relations(self, keys: Sequence[logic_pb2.NamedColumn], body: logic_pb2.TargetRelations) -> logic_pb2.TargetRelations:
        if body.HasField("plain"):
            _t2210 = logic_pb2.TargetRelations(keys=keys, plain=body.plain)
            return _t2210
        else:
            _t2209 = None
        _t2211 = logic_pb2.TargetRelations(keys=keys, cdc=body.cdc)
        return _t2211

    def construct_csv_data(self, locator: logic_pb2.CSVLocator, config: logic_pb2.CSVConfig, columns_opt: Sequence[logic_pb2.GNFColumn] | None, relations_opt: logic_pb2.TargetRelations | None, asof: str) -> logic_pb2.CSVData:
        _t2212 = logic_pb2.CSVData(locator=locator, config=config, columns=(columns_opt if columns_opt is not None else []), asof=asof, relations=relations_opt)
        return _t2212

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]], storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
<<<<<<< HEAD
        _t2118 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2118
        _t2119 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2119
        _t2120 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2120
        _t2121 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2121
        _t2122 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2122
        _t2123 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2123
        _t2124 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2124
        _t2125 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2125
        _t2126 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2126
        _t2127 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2127
        _t2128 = self._extract_value_string(config.get("csv_compression"), "")
        compression = _t2128
        _t2129 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2129
        _t2130 = self.construct_csv_storage_integration(storage_integration_opt)
        storage_integration = _t2130
        _t2131 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
        return _t2131
=======
        _t2213 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2213
        _t2214 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2214
        _t2215 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2215
        _t2216 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2216
        _t2217 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2217
        _t2218 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2218
        _t2219 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2219
        _t2220 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2220
        _t2221 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2221
        _t2222 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2222
        _t2223 = self._extract_value_string(config.get("csv_compression"), "")
        compression = _t2223
        _t2224 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2224
        _t2225 = self.construct_csv_storage_integration(storage_integration_opt)
        storage_integration = _t2225
        _t2226 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
        return _t2226
>>>>>>> origin/main

    def construct_csv_storage_integration(self, storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.StorageIntegration | None:
        if storage_integration_opt is None:
            return None
        else:
<<<<<<< HEAD
            _t2132 = None
        assert storage_integration_opt is not None
        config = dict(storage_integration_opt)
        _t2133 = self._extract_value_string(config.get("provider"), "")
        _t2134 = self._extract_value_string(config.get("azure_sas_token"), "")
        _t2135 = self._extract_value_string(config.get("s3_region"), "")
        _t2136 = self._extract_value_string(config.get("s3_access_key_id"), "")
        _t2137 = self._extract_value_string(config.get("s3_secret_access_key"), "")
        _t2138 = logic_pb2.StorageIntegration(provider=_t2133, azure_sas_token=_t2134, s3_region=_t2135, s3_access_key_id=_t2136, s3_secret_access_key=_t2137)
        return _t2138

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2139 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2139
        _t2140 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2140
        _t2141 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2141
        _t2142 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2142
        _t2143 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2143
        _t2144 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2144
        _t2145 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2145
        _t2146 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2146
        _t2147 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2147
        _t2148 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2148
        _t2149 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2149

    def default_configure(self) -> transactions_pb2.Configure:
        _t2150 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2150
        _t2151 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2151
=======
            _t2227 = None
        assert storage_integration_opt is not None
        config = dict(storage_integration_opt)
        _t2228 = self._extract_value_string(config.get("provider"), "")
        _t2229 = self._extract_value_string(config.get("azure_sas_token"), "")
        _t2230 = self._extract_value_string(config.get("s3_region"), "")
        _t2231 = self._extract_value_string(config.get("s3_access_key_id"), "")
        _t2232 = self._extract_value_string(config.get("s3_secret_access_key"), "")
        _t2233 = logic_pb2.StorageIntegration(provider=_t2228, azure_sas_token=_t2229, s3_region=_t2230, s3_access_key_id=_t2231, s3_secret_access_key=_t2232)
        return _t2233

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2234 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2234
        _t2235 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2235
        _t2236 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2236
        _t2237 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2237
        _t2238 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2238
        _t2239 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2239
        _t2240 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2240
        _t2241 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2241
        _t2242 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2242
        _t2243 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2243
        _t2244 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2244

    def default_configure(self) -> transactions_pb2.Configure:
        _t2245 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2245
        _t2246 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2246
>>>>>>> origin/main

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
<<<<<<< HEAD
        _t2152 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2152
        _t2153 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2153
        _t2154 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2154

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2155 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2155
        _t2156 = self._extract_value_string(config.get("compression"), "")
        compression = _t2156
        _t2157 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2157
        _t2158 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2158
        _t2159 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2159
        _t2160 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2160
        _t2161 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2161
        _t2162 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2162

    def construct_export_csv_config_with_location(self, location: tuple[str, str], csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2163 = transactions_pb2.ExportCSVConfig(path=location[0], transaction_output_name=location[1], csv_source=csv_source, csv_config=csv_config)
        return _t2163
=======
        _t2247 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2247
        _t2248 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2248
        _t2249 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2249

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2250 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2250
        _t2251 = self._extract_value_string(config.get("compression"), "")
        compression = _t2251
        _t2252 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2252
        _t2253 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2253
        _t2254 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2254
        _t2255 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2255
        _t2256 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2256
        _t2257 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2257

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2258 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2258
>>>>>>> origin/main

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
<<<<<<< HEAD
        _t2164 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2164

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[logic_pb2.GNFColumn], from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2165 = logic_pb2.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2165

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2166 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2166
        _t2167 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2167
        _t2168 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2168
        table_props = dict(table_property_pairs)
        _t2169 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2169
=======
        _t2259 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2259

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[logic_pb2.GNFColumn], from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2260 = logic_pb2.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2260

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2261 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2261
        _t2262 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2262
        _t2263 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2263
        table_props = dict(table_property_pairs)
        _t2264 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2264
>>>>>>> origin/main

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
<<<<<<< HEAD
        span_start676 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1341 = self.parse_configure()
            _t1340 = _t1341
        else:
            _t1340 = None
        configure670 = _t1340
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1343 = self.parse_sync()
            _t1342 = _t1343
        else:
            _t1342 = None
        sync671 = _t1342
        xs672 = []
        cond673 = self.match_lookahead_literal("(", 0)
        while cond673:
            _t1344 = self.parse_epoch()
            item674 = _t1344
            xs672.append(item674)
            cond673 = self.match_lookahead_literal("(", 0)
        epochs675 = xs672
        self.consume_literal(")")
        _t1345 = self.default_configure()
        _t1346 = transactions_pb2.Transaction(epochs=epochs675, configure=(configure670 if configure670 is not None else _t1345), sync=sync671)
        result677 = _t1346
        self.record_span(span_start676, "Transaction")
        return result677

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start679 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1347 = self.parse_config_dict()
        config_dict678 = _t1347
        self.consume_literal(")")
        _t1348 = self.construct_configure(config_dict678)
        result680 = _t1348
        self.record_span(span_start679, "Configure")
        return result680

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs681 = []
        cond682 = self.match_lookahead_literal(":", 0)
        while cond682:
            _t1349 = self.parse_config_key_value()
            item683 = _t1349
            xs681.append(item683)
            cond682 = self.match_lookahead_literal(":", 0)
        config_key_values684 = xs681
        self.consume_literal("}")
        return config_key_values684

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol685 = self.consume_terminal("SYMBOL")
        _t1350 = self.parse_raw_value()
        raw_value686 = _t1350
        return (symbol685, raw_value686,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start700 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1351 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1352 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1353 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1355 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1356 = 0
                            else:
                                _t1356 = -1
                            _t1355 = _t1356
                        _t1354 = _t1355
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1357 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1358 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1359 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1360 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1361 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1362 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1363 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1364 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1365 = 10
                                                        else:
                                                            _t1365 = -1
                                                        _t1364 = _t1365
                                                    _t1363 = _t1364
                                                _t1362 = _t1363
                                            _t1361 = _t1362
                                        _t1360 = _t1361
                                    _t1359 = _t1360
                                _t1358 = _t1359
                            _t1357 = _t1358
                        _t1354 = _t1357
                    _t1353 = _t1354
                _t1352 = _t1353
            _t1351 = _t1352
        prediction687 = _t1351
        if prediction687 == 12:
            _t1367 = self.parse_boolean_value()
            boolean_value699 = _t1367
            _t1368 = logic_pb2.Value(boolean_value=boolean_value699)
            _t1366 = _t1368
        else:
            if prediction687 == 11:
                self.consume_literal("missing")
                _t1370 = logic_pb2.MissingValue()
                _t1371 = logic_pb2.Value(missing_value=_t1370)
                _t1369 = _t1371
            else:
                if prediction687 == 10:
                    decimal698 = self.consume_terminal("DECIMAL")
                    _t1373 = logic_pb2.Value(decimal_value=decimal698)
                    _t1372 = _t1373
                else:
                    if prediction687 == 9:
                        int128697 = self.consume_terminal("INT128")
                        _t1375 = logic_pb2.Value(int128_value=int128697)
                        _t1374 = _t1375
                    else:
                        if prediction687 == 8:
                            uint128696 = self.consume_terminal("UINT128")
                            _t1377 = logic_pb2.Value(uint128_value=uint128696)
                            _t1376 = _t1377
                        else:
                            if prediction687 == 7:
                                uint32695 = self.consume_terminal("UINT32")
                                _t1379 = logic_pb2.Value(uint32_value=uint32695)
                                _t1378 = _t1379
                            else:
                                if prediction687 == 6:
                                    float694 = self.consume_terminal("FLOAT")
                                    _t1381 = logic_pb2.Value(float_value=float694)
                                    _t1380 = _t1381
                                else:
                                    if prediction687 == 5:
                                        float32693 = self.consume_terminal("FLOAT32")
                                        _t1383 = logic_pb2.Value(float32_value=float32693)
                                        _t1382 = _t1383
                                    else:
                                        if prediction687 == 4:
                                            int692 = self.consume_terminal("INT")
                                            _t1385 = logic_pb2.Value(int_value=int692)
                                            _t1384 = _t1385
                                        else:
                                            if prediction687 == 3:
                                                int32691 = self.consume_terminal("INT32")
                                                _t1387 = logic_pb2.Value(int32_value=int32691)
                                                _t1386 = _t1387
                                            else:
                                                if prediction687 == 2:
                                                    string690 = self.consume_terminal("STRING")
                                                    _t1389 = logic_pb2.Value(string_value=string690)
                                                    _t1388 = _t1389
                                                else:
                                                    if prediction687 == 1:
                                                        _t1391 = self.parse_raw_datetime()
                                                        raw_datetime689 = _t1391
                                                        _t1392 = logic_pb2.Value(datetime_value=raw_datetime689)
                                                        _t1390 = _t1392
                                                    else:
                                                        if prediction687 == 0:
                                                            _t1394 = self.parse_raw_date()
                                                            raw_date688 = _t1394
                                                            _t1395 = logic_pb2.Value(date_value=raw_date688)
                                                            _t1393 = _t1395
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1390 = _t1393
                                                    _t1388 = _t1390
                                                _t1386 = _t1388
                                            _t1384 = _t1386
                                        _t1382 = _t1384
                                    _t1380 = _t1382
                                _t1378 = _t1380
                            _t1376 = _t1378
                        _t1374 = _t1376
                    _t1372 = _t1374
                _t1369 = _t1372
            _t1366 = _t1369
        result701 = _t1366
        self.record_span(span_start700, "Value")
        return result701

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start705 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int702 = self.consume_terminal("INT")
        int_3703 = self.consume_terminal("INT")
        int_4704 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1396 = logic_pb2.DateValue(year=int(int702), month=int(int_3703), day=int(int_4704))
        result706 = _t1396
        self.record_span(span_start705, "DateValue")
        return result706

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start714 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int707 = self.consume_terminal("INT")
        int_3708 = self.consume_terminal("INT")
        int_4709 = self.consume_terminal("INT")
        int_5710 = self.consume_terminal("INT")
        int_6711 = self.consume_terminal("INT")
        int_7712 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1397 = self.consume_terminal("INT")
        else:
            _t1397 = None
        int_8713 = _t1397
        self.consume_literal(")")
        _t1398 = logic_pb2.DateTimeValue(year=int(int707), month=int(int_3708), day=int(int_4709), hour=int(int_5710), minute=int(int_6711), second=int(int_7712), microsecond=int((int_8713 if int_8713 is not None else 0)))
        result715 = _t1398
        self.record_span(span_start714, "DateTimeValue")
        return result715

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1399 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1400 = 1
            else:
                _t1400 = -1
            _t1399 = _t1400
        prediction716 = _t1399
        if prediction716 == 1:
            self.consume_literal("false")
            _t1401 = False
        else:
            if prediction716 == 0:
                self.consume_literal("true")
                _t1402 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1401 = _t1402
        return _t1401

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start721 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs717 = []
        cond718 = self.match_lookahead_literal(":", 0)
        while cond718:
            _t1403 = self.parse_fragment_id()
            item719 = _t1403
            xs717.append(item719)
            cond718 = self.match_lookahead_literal(":", 0)
        fragment_ids720 = xs717
        self.consume_literal(")")
        _t1404 = transactions_pb2.Sync(fragments=fragment_ids720)
        result722 = _t1404
        self.record_span(span_start721, "Sync")
        return result722
=======
        span_start710 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1409 = self.parse_configure()
            _t1408 = _t1409
        else:
            _t1408 = None
        configure704 = _t1408
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1411 = self.parse_sync()
            _t1410 = _t1411
        else:
            _t1410 = None
        sync705 = _t1410
        xs706 = []
        cond707 = self.match_lookahead_literal("(", 0)
        while cond707:
            _t1412 = self.parse_epoch()
            item708 = _t1412
            xs706.append(item708)
            cond707 = self.match_lookahead_literal("(", 0)
        epochs709 = xs706
        self.consume_literal(")")
        _t1413 = self.default_configure()
        _t1414 = transactions_pb2.Transaction(epochs=epochs709, configure=(configure704 if configure704 is not None else _t1413), sync=sync705)
        result711 = _t1414
        self.record_span(span_start710, "Transaction")
        return result711

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start713 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1415 = self.parse_config_dict()
        config_dict712 = _t1415
        self.consume_literal(")")
        _t1416 = self.construct_configure(config_dict712)
        result714 = _t1416
        self.record_span(span_start713, "Configure")
        return result714

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs715 = []
        cond716 = self.match_lookahead_literal(":", 0)
        while cond716:
            _t1417 = self.parse_config_key_value()
            item717 = _t1417
            xs715.append(item717)
            cond716 = self.match_lookahead_literal(":", 0)
        config_key_values718 = xs715
        self.consume_literal("}")
        return config_key_values718

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol719 = self.consume_terminal("SYMBOL")
        _t1418 = self.parse_raw_value()
        raw_value720 = _t1418
        return (symbol719, raw_value720,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start734 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1419 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1420 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1421 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1423 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1424 = 0
                            else:
                                _t1424 = -1
                            _t1423 = _t1424
                        _t1422 = _t1423
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1425 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1426 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1427 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1428 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1429 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1430 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1431 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1432 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1433 = 10
                                                        else:
                                                            _t1433 = -1
                                                        _t1432 = _t1433
                                                    _t1431 = _t1432
                                                _t1430 = _t1431
                                            _t1429 = _t1430
                                        _t1428 = _t1429
                                    _t1427 = _t1428
                                _t1426 = _t1427
                            _t1425 = _t1426
                        _t1422 = _t1425
                    _t1421 = _t1422
                _t1420 = _t1421
            _t1419 = _t1420
        prediction721 = _t1419
        if prediction721 == 12:
            _t1435 = self.parse_boolean_value()
            boolean_value733 = _t1435
            _t1436 = logic_pb2.Value(boolean_value=boolean_value733)
            _t1434 = _t1436
        else:
            if prediction721 == 11:
                self.consume_literal("missing")
                _t1438 = logic_pb2.MissingValue()
                _t1439 = logic_pb2.Value(missing_value=_t1438)
                _t1437 = _t1439
            else:
                if prediction721 == 10:
                    decimal732 = self.consume_terminal("DECIMAL")
                    _t1441 = logic_pb2.Value(decimal_value=decimal732)
                    _t1440 = _t1441
                else:
                    if prediction721 == 9:
                        int128731 = self.consume_terminal("INT128")
                        _t1443 = logic_pb2.Value(int128_value=int128731)
                        _t1442 = _t1443
                    else:
                        if prediction721 == 8:
                            uint128730 = self.consume_terminal("UINT128")
                            _t1445 = logic_pb2.Value(uint128_value=uint128730)
                            _t1444 = _t1445
                        else:
                            if prediction721 == 7:
                                uint32729 = self.consume_terminal("UINT32")
                                _t1447 = logic_pb2.Value(uint32_value=uint32729)
                                _t1446 = _t1447
                            else:
                                if prediction721 == 6:
                                    float728 = self.consume_terminal("FLOAT")
                                    _t1449 = logic_pb2.Value(float_value=float728)
                                    _t1448 = _t1449
                                else:
                                    if prediction721 == 5:
                                        float32727 = self.consume_terminal("FLOAT32")
                                        _t1451 = logic_pb2.Value(float32_value=float32727)
                                        _t1450 = _t1451
                                    else:
                                        if prediction721 == 4:
                                            int726 = self.consume_terminal("INT")
                                            _t1453 = logic_pb2.Value(int_value=int726)
                                            _t1452 = _t1453
                                        else:
                                            if prediction721 == 3:
                                                int32725 = self.consume_terminal("INT32")
                                                _t1455 = logic_pb2.Value(int32_value=int32725)
                                                _t1454 = _t1455
                                            else:
                                                if prediction721 == 2:
                                                    string724 = self.consume_terminal("STRING")
                                                    _t1457 = logic_pb2.Value(string_value=string724)
                                                    _t1456 = _t1457
                                                else:
                                                    if prediction721 == 1:
                                                        _t1459 = self.parse_raw_datetime()
                                                        raw_datetime723 = _t1459
                                                        _t1460 = logic_pb2.Value(datetime_value=raw_datetime723)
                                                        _t1458 = _t1460
                                                    else:
                                                        if prediction721 == 0:
                                                            _t1462 = self.parse_raw_date()
                                                            raw_date722 = _t1462
                                                            _t1463 = logic_pb2.Value(date_value=raw_date722)
                                                            _t1461 = _t1463
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1458 = _t1461
                                                    _t1456 = _t1458
                                                _t1454 = _t1456
                                            _t1452 = _t1454
                                        _t1450 = _t1452
                                    _t1448 = _t1450
                                _t1446 = _t1448
                            _t1444 = _t1446
                        _t1442 = _t1444
                    _t1440 = _t1442
                _t1437 = _t1440
            _t1434 = _t1437
        result735 = _t1434
        self.record_span(span_start734, "Value")
        return result735

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start739 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int736 = self.consume_terminal("INT")
        int_3737 = self.consume_terminal("INT")
        int_4738 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1464 = logic_pb2.DateValue(year=int(int736), month=int(int_3737), day=int(int_4738))
        result740 = _t1464
        self.record_span(span_start739, "DateValue")
        return result740

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start748 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int741 = self.consume_terminal("INT")
        int_3742 = self.consume_terminal("INT")
        int_4743 = self.consume_terminal("INT")
        int_5744 = self.consume_terminal("INT")
        int_6745 = self.consume_terminal("INT")
        int_7746 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1465 = self.consume_terminal("INT")
        else:
            _t1465 = None
        int_8747 = _t1465
        self.consume_literal(")")
        _t1466 = logic_pb2.DateTimeValue(year=int(int741), month=int(int_3742), day=int(int_4743), hour=int(int_5744), minute=int(int_6745), second=int(int_7746), microsecond=int((int_8747 if int_8747 is not None else 0)))
        result749 = _t1466
        self.record_span(span_start748, "DateTimeValue")
        return result749

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1467 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1468 = 1
            else:
                _t1468 = -1
            _t1467 = _t1468
        prediction750 = _t1467
        if prediction750 == 1:
            self.consume_literal("false")
            _t1469 = False
        else:
            if prediction750 == 0:
                self.consume_literal("true")
                _t1470 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1469 = _t1470
        return _t1469

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start755 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs751 = []
        cond752 = self.match_lookahead_literal(":", 0)
        while cond752:
            _t1471 = self.parse_fragment_id()
            item753 = _t1471
            xs751.append(item753)
            cond752 = self.match_lookahead_literal(":", 0)
        fragment_ids754 = xs751
        self.consume_literal(")")
        _t1472 = transactions_pb2.Sync(fragments=fragment_ids754)
        result756 = _t1472
        self.record_span(span_start755, "Sync")
        return result756

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start758 = self.span_start()
        self.consume_literal(":")
        symbol757 = self.consume_terminal("SYMBOL")
        result759 = fragments_pb2.FragmentId(id=symbol757.encode())
        self.record_span(span_start758, "FragmentId")
        return result759
>>>>>>> origin/main

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start724 = self.span_start()
        self.consume_literal(":")
        symbol723 = self.consume_terminal("SYMBOL")
        result725 = fragments_pb2.FragmentId(id=symbol723.encode())
        self.record_span(span_start724, "FragmentId")
        return result725

    def parse_epoch(self) -> transactions_pb2.Epoch:
<<<<<<< HEAD
        span_start728 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1406 = self.parse_epoch_writes()
            _t1405 = _t1406
        else:
            _t1405 = None
        epoch_writes726 = _t1405
        if self.match_lookahead_literal("(", 0):
            _t1408 = self.parse_epoch_reads()
            _t1407 = _t1408
        else:
            _t1407 = None
        epoch_reads727 = _t1407
        self.consume_literal(")")
        _t1409 = transactions_pb2.Epoch(writes=(epoch_writes726 if epoch_writes726 is not None else []), reads=(epoch_reads727 if epoch_reads727 is not None else []))
        result729 = _t1409
        self.record_span(span_start728, "Epoch")
        return result729
=======
        span_start762 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1474 = self.parse_epoch_writes()
            _t1473 = _t1474
        else:
            _t1473 = None
        epoch_writes760 = _t1473
        if self.match_lookahead_literal("(", 0):
            _t1476 = self.parse_epoch_reads()
            _t1475 = _t1476
        else:
            _t1475 = None
        epoch_reads761 = _t1475
        self.consume_literal(")")
        _t1477 = transactions_pb2.Epoch(writes=(epoch_writes760 if epoch_writes760 is not None else []), reads=(epoch_reads761 if epoch_reads761 is not None else []))
        result763 = _t1477
        self.record_span(span_start762, "Epoch")
        return result763
>>>>>>> origin/main

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
<<<<<<< HEAD
        xs730 = []
        cond731 = self.match_lookahead_literal("(", 0)
        while cond731:
            _t1410 = self.parse_write()
            item732 = _t1410
            xs730.append(item732)
            cond731 = self.match_lookahead_literal("(", 0)
        writes733 = xs730
        self.consume_literal(")")
        return writes733

    def parse_write(self) -> transactions_pb2.Write:
        span_start739 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1412 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1413 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1414 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1415 = 2
                        else:
                            _t1415 = -1
                        _t1414 = _t1415
                    _t1413 = _t1414
                _t1412 = _t1413
            _t1411 = _t1412
        else:
            _t1411 = -1
        prediction734 = _t1411
        if prediction734 == 3:
            _t1417 = self.parse_snapshot()
            snapshot738 = _t1417
            _t1418 = transactions_pb2.Write(snapshot=snapshot738)
            _t1416 = _t1418
        else:
            if prediction734 == 2:
                _t1420 = self.parse_context()
                context737 = _t1420
                _t1421 = transactions_pb2.Write(context=context737)
                _t1419 = _t1421
            else:
                if prediction734 == 1:
                    _t1423 = self.parse_undefine()
                    undefine736 = _t1423
                    _t1424 = transactions_pb2.Write(undefine=undefine736)
                    _t1422 = _t1424
                else:
                    if prediction734 == 0:
                        _t1426 = self.parse_define()
                        define735 = _t1426
                        _t1427 = transactions_pb2.Write(define=define735)
                        _t1425 = _t1427
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1422 = _t1425
                _t1419 = _t1422
            _t1416 = _t1419
        result740 = _t1416
        self.record_span(span_start739, "Write")
        return result740
=======
        xs764 = []
        cond765 = self.match_lookahead_literal("(", 0)
        while cond765:
            _t1478 = self.parse_write()
            item766 = _t1478
            xs764.append(item766)
            cond765 = self.match_lookahead_literal("(", 0)
        writes767 = xs764
        self.consume_literal(")")
        return writes767

    def parse_write(self) -> transactions_pb2.Write:
        span_start773 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1480 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1481 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1482 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1483 = 2
                        else:
                            _t1483 = -1
                        _t1482 = _t1483
                    _t1481 = _t1482
                _t1480 = _t1481
            _t1479 = _t1480
        else:
            _t1479 = -1
        prediction768 = _t1479
        if prediction768 == 3:
            _t1485 = self.parse_snapshot()
            snapshot772 = _t1485
            _t1486 = transactions_pb2.Write(snapshot=snapshot772)
            _t1484 = _t1486
        else:
            if prediction768 == 2:
                _t1488 = self.parse_context()
                context771 = _t1488
                _t1489 = transactions_pb2.Write(context=context771)
                _t1487 = _t1489
            else:
                if prediction768 == 1:
                    _t1491 = self.parse_undefine()
                    undefine770 = _t1491
                    _t1492 = transactions_pb2.Write(undefine=undefine770)
                    _t1490 = _t1492
                else:
                    if prediction768 == 0:
                        _t1494 = self.parse_define()
                        define769 = _t1494
                        _t1495 = transactions_pb2.Write(define=define769)
                        _t1493 = _t1495
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1490 = _t1493
                _t1487 = _t1490
            _t1484 = _t1487
        result774 = _t1484
        self.record_span(span_start773, "Write")
        return result774

    def parse_define(self) -> transactions_pb2.Define:
        span_start776 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1496 = self.parse_fragment()
        fragment775 = _t1496
        self.consume_literal(")")
        _t1497 = transactions_pb2.Define(fragment=fragment775)
        result777 = _t1497
        self.record_span(span_start776, "Define")
        return result777
>>>>>>> origin/main

    def parse_define(self) -> transactions_pb2.Define:
        span_start742 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1428 = self.parse_fragment()
        fragment741 = _t1428
        self.consume_literal(")")
        _t1429 = transactions_pb2.Define(fragment=fragment741)
        result743 = _t1429
        self.record_span(span_start742, "Define")
        return result743

    def parse_fragment(self) -> fragments_pb2.Fragment:
<<<<<<< HEAD
        span_start749 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1430 = self.parse_new_fragment_id()
        new_fragment_id744 = _t1430
        xs745 = []
        cond746 = self.match_lookahead_literal("(", 0)
        while cond746:
            _t1431 = self.parse_declaration()
            item747 = _t1431
            xs745.append(item747)
            cond746 = self.match_lookahead_literal("(", 0)
        declarations748 = xs745
        self.consume_literal(")")
        result750 = self.construct_fragment(new_fragment_id744, declarations748)
        self.record_span(span_start749, "Fragment")
        return result750
=======
        span_start783 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1498 = self.parse_new_fragment_id()
        new_fragment_id778 = _t1498
        xs779 = []
        cond780 = self.match_lookahead_literal("(", 0)
        while cond780:
            _t1499 = self.parse_declaration()
            item781 = _t1499
            xs779.append(item781)
            cond780 = self.match_lookahead_literal("(", 0)
        declarations782 = xs779
        self.consume_literal(")")
        result784 = self.construct_fragment(new_fragment_id778, declarations782)
        self.record_span(span_start783, "Fragment")
        return result784

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start786 = self.span_start()
        _t1500 = self.parse_fragment_id()
        fragment_id785 = _t1500
        self.start_fragment(fragment_id785)
        result787 = fragment_id785
        self.record_span(span_start786, "FragmentId")
        return result787
>>>>>>> origin/main

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start752 = self.span_start()
        _t1432 = self.parse_fragment_id()
        fragment_id751 = _t1432
        self.start_fragment(fragment_id751)
        result753 = fragment_id751
        self.record_span(span_start752, "FragmentId")
        return result753

    def parse_declaration(self) -> logic_pb2.Declaration:
<<<<<<< HEAD
        span_start759 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1434 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1435 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1436 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1437 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1438 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1439 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1440 = 1
                                    else:
                                        _t1440 = -1
                                    _t1439 = _t1440
                                _t1438 = _t1439
                            _t1437 = _t1438
                        _t1436 = _t1437
                    _t1435 = _t1436
                _t1434 = _t1435
            _t1433 = _t1434
        else:
            _t1433 = -1
        prediction754 = _t1433
        if prediction754 == 3:
            _t1442 = self.parse_data()
            data758 = _t1442
            _t1443 = logic_pb2.Declaration(data=data758)
            _t1441 = _t1443
        else:
            if prediction754 == 2:
                _t1445 = self.parse_constraint()
                constraint757 = _t1445
                _t1446 = logic_pb2.Declaration(constraint=constraint757)
                _t1444 = _t1446
            else:
                if prediction754 == 1:
                    _t1448 = self.parse_algorithm()
                    algorithm756 = _t1448
                    _t1449 = logic_pb2.Declaration(algorithm=algorithm756)
                    _t1447 = _t1449
                else:
                    if prediction754 == 0:
                        _t1451 = self.parse_def()
                        def755 = _t1451
                        _t1452 = logic_pb2.Declaration()
                        getattr(_t1452, 'def').CopyFrom(def755)
                        _t1450 = _t1452
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1447 = _t1450
                _t1444 = _t1447
            _t1441 = _t1444
        result760 = _t1441
        self.record_span(span_start759, "Declaration")
        return result760

    def parse_def(self) -> logic_pb2.Def:
        span_start764 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1453 = self.parse_relation_id()
        relation_id761 = _t1453
        _t1454 = self.parse_abstraction()
        abstraction762 = _t1454
        if self.match_lookahead_literal("(", 0):
            _t1456 = self.parse_attrs()
            _t1455 = _t1456
        else:
            _t1455 = None
        attrs763 = _t1455
        self.consume_literal(")")
        _t1457 = logic_pb2.Def(name=relation_id761, body=abstraction762, attrs=(attrs763 if attrs763 is not None else []))
        result765 = _t1457
        self.record_span(span_start764, "Def")
        return result765

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start769 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1458 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1459 = 1
            else:
                _t1459 = -1
            _t1458 = _t1459
        prediction766 = _t1458
        if prediction766 == 1:
            uint128768 = self.consume_terminal("UINT128")
            _t1460 = logic_pb2.RelationId(id_low=uint128768.low, id_high=uint128768.high)
        else:
            if prediction766 == 0:
                self.consume_literal(":")
                symbol767 = self.consume_terminal("SYMBOL")
                _t1461 = self.relation_id_from_string(symbol767)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1460 = _t1461
        result770 = _t1460
        self.record_span(span_start769, "RelationId")
        return result770

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start773 = self.span_start()
        self.consume_literal("(")
        _t1462 = self.parse_bindings()
        bindings771 = _t1462
        _t1463 = self.parse_formula()
        formula772 = _t1463
        self.consume_literal(")")
        _t1464 = logic_pb2.Abstraction(vars=(list(bindings771[0]) + list(bindings771[1] if bindings771[1] is not None else [])), value=formula772)
        result774 = _t1464
        self.record_span(span_start773, "Abstraction")
        return result774

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs775 = []
        cond776 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond776:
            _t1465 = self.parse_binding()
            item777 = _t1465
            xs775.append(item777)
            cond776 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings778 = xs775
        if self.match_lookahead_literal("|", 0):
            _t1467 = self.parse_value_bindings()
            _t1466 = _t1467
        else:
            _t1466 = None
        value_bindings779 = _t1466
        self.consume_literal("]")
        return (bindings778, (value_bindings779 if value_bindings779 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start782 = self.span_start()
        symbol780 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1468 = self.parse_type()
        type781 = _t1468
        _t1469 = logic_pb2.Var(name=symbol780)
        _t1470 = logic_pb2.Binding(var=_t1469, type=type781)
        result783 = _t1470
        self.record_span(span_start782, "Binding")
        return result783

    def parse_type(self) -> logic_pb2.Type:
        span_start799 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1471 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1472 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1473 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1474 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1475 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1476 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1477 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1478 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1479 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1480 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1481 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1482 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1483 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1484 = 9
                                                            else:
                                                                _t1484 = -1
                                                            _t1483 = _t1484
                                                        _t1482 = _t1483
                                                    _t1481 = _t1482
                                                _t1480 = _t1481
                                            _t1479 = _t1480
                                        _t1478 = _t1479
                                    _t1477 = _t1478
                                _t1476 = _t1477
                            _t1475 = _t1476
                        _t1474 = _t1475
                    _t1473 = _t1474
                _t1472 = _t1473
            _t1471 = _t1472
        prediction784 = _t1471
        if prediction784 == 13:
            _t1486 = self.parse_uint32_type()
            uint32_type798 = _t1486
            _t1487 = logic_pb2.Type(uint32_type=uint32_type798)
            _t1485 = _t1487
        else:
            if prediction784 == 12:
                _t1489 = self.parse_float32_type()
                float32_type797 = _t1489
                _t1490 = logic_pb2.Type(float32_type=float32_type797)
                _t1488 = _t1490
            else:
                if prediction784 == 11:
                    _t1492 = self.parse_int32_type()
                    int32_type796 = _t1492
                    _t1493 = logic_pb2.Type(int32_type=int32_type796)
                    _t1491 = _t1493
                else:
                    if prediction784 == 10:
                        _t1495 = self.parse_boolean_type()
                        boolean_type795 = _t1495
                        _t1496 = logic_pb2.Type(boolean_type=boolean_type795)
                        _t1494 = _t1496
                    else:
                        if prediction784 == 9:
                            _t1498 = self.parse_decimal_type()
                            decimal_type794 = _t1498
                            _t1499 = logic_pb2.Type(decimal_type=decimal_type794)
                            _t1497 = _t1499
                        else:
                            if prediction784 == 8:
                                _t1501 = self.parse_missing_type()
                                missing_type793 = _t1501
                                _t1502 = logic_pb2.Type(missing_type=missing_type793)
                                _t1500 = _t1502
                            else:
                                if prediction784 == 7:
                                    _t1504 = self.parse_datetime_type()
                                    datetime_type792 = _t1504
                                    _t1505 = logic_pb2.Type(datetime_type=datetime_type792)
                                    _t1503 = _t1505
                                else:
                                    if prediction784 == 6:
                                        _t1507 = self.parse_date_type()
                                        date_type791 = _t1507
                                        _t1508 = logic_pb2.Type(date_type=date_type791)
                                        _t1506 = _t1508
                                    else:
                                        if prediction784 == 5:
                                            _t1510 = self.parse_int128_type()
                                            int128_type790 = _t1510
                                            _t1511 = logic_pb2.Type(int128_type=int128_type790)
                                            _t1509 = _t1511
                                        else:
                                            if prediction784 == 4:
                                                _t1513 = self.parse_uint128_type()
                                                uint128_type789 = _t1513
                                                _t1514 = logic_pb2.Type(uint128_type=uint128_type789)
                                                _t1512 = _t1514
                                            else:
                                                if prediction784 == 3:
                                                    _t1516 = self.parse_float_type()
                                                    float_type788 = _t1516
                                                    _t1517 = logic_pb2.Type(float_type=float_type788)
                                                    _t1515 = _t1517
                                                else:
                                                    if prediction784 == 2:
                                                        _t1519 = self.parse_int_type()
                                                        int_type787 = _t1519
                                                        _t1520 = logic_pb2.Type(int_type=int_type787)
                                                        _t1518 = _t1520
                                                    else:
                                                        if prediction784 == 1:
                                                            _t1522 = self.parse_string_type()
                                                            string_type786 = _t1522
                                                            _t1523 = logic_pb2.Type(string_type=string_type786)
                                                            _t1521 = _t1523
                                                        else:
                                                            if prediction784 == 0:
                                                                _t1525 = self.parse_unspecified_type()
                                                                unspecified_type785 = _t1525
                                                                _t1526 = logic_pb2.Type(unspecified_type=unspecified_type785)
                                                                _t1524 = _t1526
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1521 = _t1524
                                                        _t1518 = _t1521
                                                    _t1515 = _t1518
                                                _t1512 = _t1515
                                            _t1509 = _t1512
                                        _t1506 = _t1509
                                    _t1503 = _t1506
                                _t1500 = _t1503
                            _t1497 = _t1500
                        _t1494 = _t1497
                    _t1491 = _t1494
                _t1488 = _t1491
            _t1485 = _t1488
        result800 = _t1485
        self.record_span(span_start799, "Type")
        return result800

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start801 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1527 = logic_pb2.UnspecifiedType()
        result802 = _t1527
        self.record_span(span_start801, "UnspecifiedType")
        return result802

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start803 = self.span_start()
        self.consume_literal("STRING")
        _t1528 = logic_pb2.StringType()
        result804 = _t1528
        self.record_span(span_start803, "StringType")
        return result804

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start805 = self.span_start()
        self.consume_literal("INT")
        _t1529 = logic_pb2.IntType()
        result806 = _t1529
        self.record_span(span_start805, "IntType")
        return result806

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start807 = self.span_start()
        self.consume_literal("FLOAT")
        _t1530 = logic_pb2.FloatType()
        result808 = _t1530
        self.record_span(span_start807, "FloatType")
        return result808

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start809 = self.span_start()
        self.consume_literal("UINT128")
        _t1531 = logic_pb2.UInt128Type()
        result810 = _t1531
        self.record_span(span_start809, "UInt128Type")
        return result810

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start811 = self.span_start()
        self.consume_literal("INT128")
        _t1532 = logic_pb2.Int128Type()
        result812 = _t1532
        self.record_span(span_start811, "Int128Type")
        return result812

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start813 = self.span_start()
        self.consume_literal("DATE")
        _t1533 = logic_pb2.DateType()
        result814 = _t1533
        self.record_span(span_start813, "DateType")
        return result814

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start815 = self.span_start()
        self.consume_literal("DATETIME")
        _t1534 = logic_pb2.DateTimeType()
        result816 = _t1534
        self.record_span(span_start815, "DateTimeType")
        return result816

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start817 = self.span_start()
        self.consume_literal("MISSING")
        _t1535 = logic_pb2.MissingType()
        result818 = _t1535
        self.record_span(span_start817, "MissingType")
        return result818

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start821 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int819 = self.consume_terminal("INT")
        int_3820 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1536 = logic_pb2.DecimalType(precision=int(int819), scale=int(int_3820))
        result822 = _t1536
        self.record_span(span_start821, "DecimalType")
        return result822

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start823 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1537 = logic_pb2.BooleanType()
        result824 = _t1537
        self.record_span(span_start823, "BooleanType")
        return result824

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start825 = self.span_start()
        self.consume_literal("INT32")
        _t1538 = logic_pb2.Int32Type()
        result826 = _t1538
        self.record_span(span_start825, "Int32Type")
        return result826

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start827 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1539 = logic_pb2.Float32Type()
        result828 = _t1539
        self.record_span(span_start827, "Float32Type")
        return result828

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start829 = self.span_start()
        self.consume_literal("UINT32")
        _t1540 = logic_pb2.UInt32Type()
        result830 = _t1540
        self.record_span(span_start829, "UInt32Type")
        return result830

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs831 = []
        cond832 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond832:
            _t1541 = self.parse_binding()
            item833 = _t1541
            xs831.append(item833)
            cond832 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings834 = xs831
        return bindings834

    def parse_formula(self) -> logic_pb2.Formula:
        span_start849 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1543 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1544 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1545 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1546 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1547 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1548 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1549 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1550 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1551 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1552 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1553 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1554 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1555 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1556 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1557 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1558 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1559 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1560 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1561 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1562 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1563 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1564 = 10
                                                                                                else:
                                                                                                    _t1564 = -1
                                                                                                _t1563 = _t1564
                                                                                            _t1562 = _t1563
                                                                                        _t1561 = _t1562
                                                                                    _t1560 = _t1561
                                                                                _t1559 = _t1560
                                                                            _t1558 = _t1559
                                                                        _t1557 = _t1558
                                                                    _t1556 = _t1557
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
                        _t1545 = _t1546
                    _t1544 = _t1545
                _t1543 = _t1544
            _t1542 = _t1543
        else:
            _t1542 = -1
        prediction835 = _t1542
        if prediction835 == 12:
            _t1566 = self.parse_cast()
            cast848 = _t1566
            _t1567 = logic_pb2.Formula(cast=cast848)
            _t1565 = _t1567
        else:
            if prediction835 == 11:
                _t1569 = self.parse_rel_atom()
                rel_atom847 = _t1569
                _t1570 = logic_pb2.Formula(rel_atom=rel_atom847)
                _t1568 = _t1570
            else:
                if prediction835 == 10:
                    _t1572 = self.parse_primitive()
                    primitive846 = _t1572
                    _t1573 = logic_pb2.Formula(primitive=primitive846)
                    _t1571 = _t1573
                else:
                    if prediction835 == 9:
                        _t1575 = self.parse_pragma()
                        pragma845 = _t1575
                        _t1576 = logic_pb2.Formula(pragma=pragma845)
                        _t1574 = _t1576
                    else:
                        if prediction835 == 8:
                            _t1578 = self.parse_atom()
                            atom844 = _t1578
                            _t1579 = logic_pb2.Formula(atom=atom844)
                            _t1577 = _t1579
                        else:
                            if prediction835 == 7:
                                _t1581 = self.parse_ffi()
                                ffi843 = _t1581
                                _t1582 = logic_pb2.Formula(ffi=ffi843)
                                _t1580 = _t1582
                            else:
                                if prediction835 == 6:
                                    _t1584 = self.parse_not()
                                    not842 = _t1584
                                    _t1585 = logic_pb2.Formula()
                                    getattr(_t1585, 'not').CopyFrom(not842)
                                    _t1583 = _t1585
                                else:
                                    if prediction835 == 5:
                                        _t1587 = self.parse_disjunction()
                                        disjunction841 = _t1587
                                        _t1588 = logic_pb2.Formula(disjunction=disjunction841)
                                        _t1586 = _t1588
                                    else:
                                        if prediction835 == 4:
                                            _t1590 = self.parse_conjunction()
                                            conjunction840 = _t1590
                                            _t1591 = logic_pb2.Formula(conjunction=conjunction840)
                                            _t1589 = _t1591
                                        else:
                                            if prediction835 == 3:
                                                _t1593 = self.parse_reduce()
                                                reduce839 = _t1593
                                                _t1594 = logic_pb2.Formula(reduce=reduce839)
                                                _t1592 = _t1594
                                            else:
                                                if prediction835 == 2:
                                                    _t1596 = self.parse_exists()
                                                    exists838 = _t1596
                                                    _t1597 = logic_pb2.Formula(exists=exists838)
                                                    _t1595 = _t1597
                                                else:
                                                    if prediction835 == 1:
                                                        _t1599 = self.parse_false()
                                                        false837 = _t1599
                                                        _t1600 = logic_pb2.Formula(disjunction=false837)
                                                        _t1598 = _t1600
                                                    else:
                                                        if prediction835 == 0:
                                                            _t1602 = self.parse_true()
                                                            true836 = _t1602
                                                            _t1603 = logic_pb2.Formula(conjunction=true836)
                                                            _t1601 = _t1603
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1598 = _t1601
                                                    _t1595 = _t1598
                                                _t1592 = _t1595
                                            _t1589 = _t1592
                                        _t1586 = _t1589
                                    _t1583 = _t1586
                                _t1580 = _t1583
                            _t1577 = _t1580
                        _t1574 = _t1577
                    _t1571 = _t1574
                _t1568 = _t1571
            _t1565 = _t1568
        result850 = _t1565
        self.record_span(span_start849, "Formula")
        return result850

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start851 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1604 = logic_pb2.Conjunction(args=[])
        result852 = _t1604
        self.record_span(span_start851, "Conjunction")
        return result852

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start853 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1605 = logic_pb2.Disjunction(args=[])
        result854 = _t1605
        self.record_span(span_start853, "Disjunction")
        return result854

    def parse_exists(self) -> logic_pb2.Exists:
        span_start857 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1606 = self.parse_bindings()
        bindings855 = _t1606
        _t1607 = self.parse_formula()
        formula856 = _t1607
        self.consume_literal(")")
        _t1608 = logic_pb2.Abstraction(vars=(list(bindings855[0]) + list(bindings855[1] if bindings855[1] is not None else [])), value=formula856)
        _t1609 = logic_pb2.Exists(body=_t1608)
        result858 = _t1609
        self.record_span(span_start857, "Exists")
        return result858

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start862 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1610 = self.parse_abstraction()
        abstraction859 = _t1610
        _t1611 = self.parse_abstraction()
        abstraction_3860 = _t1611
        _t1612 = self.parse_terms()
        terms861 = _t1612
        self.consume_literal(")")
        _t1613 = logic_pb2.Reduce(op=abstraction859, body=abstraction_3860, terms=terms861)
        result863 = _t1613
        self.record_span(span_start862, "Reduce")
        return result863
=======
        span_start793 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1502 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1503 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1504 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1505 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1506 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1507 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1508 = 1
                                    else:
                                        _t1508 = -1
                                    _t1507 = _t1508
                                _t1506 = _t1507
                            _t1505 = _t1506
                        _t1504 = _t1505
                    _t1503 = _t1504
                _t1502 = _t1503
            _t1501 = _t1502
        else:
            _t1501 = -1
        prediction788 = _t1501
        if prediction788 == 3:
            _t1510 = self.parse_data()
            data792 = _t1510
            _t1511 = logic_pb2.Declaration(data=data792)
            _t1509 = _t1511
        else:
            if prediction788 == 2:
                _t1513 = self.parse_constraint()
                constraint791 = _t1513
                _t1514 = logic_pb2.Declaration(constraint=constraint791)
                _t1512 = _t1514
            else:
                if prediction788 == 1:
                    _t1516 = self.parse_algorithm()
                    algorithm790 = _t1516
                    _t1517 = logic_pb2.Declaration(algorithm=algorithm790)
                    _t1515 = _t1517
                else:
                    if prediction788 == 0:
                        _t1519 = self.parse_def()
                        def789 = _t1519
                        _t1520 = logic_pb2.Declaration()
                        getattr(_t1520, 'def').CopyFrom(def789)
                        _t1518 = _t1520
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1515 = _t1518
                _t1512 = _t1515
            _t1509 = _t1512
        result794 = _t1509
        self.record_span(span_start793, "Declaration")
        return result794

    def parse_def(self) -> logic_pb2.Def:
        span_start798 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1521 = self.parse_relation_id()
        relation_id795 = _t1521
        _t1522 = self.parse_abstraction()
        abstraction796 = _t1522
        if self.match_lookahead_literal("(", 0):
            _t1524 = self.parse_attrs()
            _t1523 = _t1524
        else:
            _t1523 = None
        attrs797 = _t1523
        self.consume_literal(")")
        _t1525 = logic_pb2.Def(name=relation_id795, body=abstraction796, attrs=(attrs797 if attrs797 is not None else []))
        result799 = _t1525
        self.record_span(span_start798, "Def")
        return result799

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start803 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1526 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1527 = 1
            else:
                _t1527 = -1
            _t1526 = _t1527
        prediction800 = _t1526
        if prediction800 == 1:
            uint128802 = self.consume_terminal("UINT128")
            _t1528 = logic_pb2.RelationId(id_low=uint128802.low, id_high=uint128802.high)
        else:
            if prediction800 == 0:
                self.consume_literal(":")
                symbol801 = self.consume_terminal("SYMBOL")
                _t1529 = self.relation_id_from_string(symbol801)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1528 = _t1529
        result804 = _t1528
        self.record_span(span_start803, "RelationId")
        return result804

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start807 = self.span_start()
        self.consume_literal("(")
        _t1530 = self.parse_bindings()
        bindings805 = _t1530
        _t1531 = self.parse_formula()
        formula806 = _t1531
        self.consume_literal(")")
        _t1532 = logic_pb2.Abstraction(vars=(list(bindings805[0]) + list(bindings805[1] if bindings805[1] is not None else [])), value=formula806)
        result808 = _t1532
        self.record_span(span_start807, "Abstraction")
        return result808

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs809 = []
        cond810 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond810:
            _t1533 = self.parse_binding()
            item811 = _t1533
            xs809.append(item811)
            cond810 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings812 = xs809
        if self.match_lookahead_literal("|", 0):
            _t1535 = self.parse_value_bindings()
            _t1534 = _t1535
        else:
            _t1534 = None
        value_bindings813 = _t1534
        self.consume_literal("]")
        return (bindings812, (value_bindings813 if value_bindings813 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start816 = self.span_start()
        symbol814 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1536 = self.parse_type()
        type815 = _t1536
        _t1537 = logic_pb2.Var(name=symbol814)
        _t1538 = logic_pb2.Binding(var=_t1537, type=type815)
        result817 = _t1538
        self.record_span(span_start816, "Binding")
        return result817

    def parse_type(self) -> logic_pb2.Type:
        span_start833 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1539 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1540 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1541 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1542 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1543 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1544 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1545 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1546 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1547 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1548 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1549 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1550 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1551 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1552 = 9
                                                            else:
                                                                _t1552 = -1
                                                            _t1551 = _t1552
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
        prediction818 = _t1539
        if prediction818 == 13:
            _t1554 = self.parse_uint32_type()
            uint32_type832 = _t1554
            _t1555 = logic_pb2.Type(uint32_type=uint32_type832)
            _t1553 = _t1555
        else:
            if prediction818 == 12:
                _t1557 = self.parse_float32_type()
                float32_type831 = _t1557
                _t1558 = logic_pb2.Type(float32_type=float32_type831)
                _t1556 = _t1558
            else:
                if prediction818 == 11:
                    _t1560 = self.parse_int32_type()
                    int32_type830 = _t1560
                    _t1561 = logic_pb2.Type(int32_type=int32_type830)
                    _t1559 = _t1561
                else:
                    if prediction818 == 10:
                        _t1563 = self.parse_boolean_type()
                        boolean_type829 = _t1563
                        _t1564 = logic_pb2.Type(boolean_type=boolean_type829)
                        _t1562 = _t1564
                    else:
                        if prediction818 == 9:
                            _t1566 = self.parse_decimal_type()
                            decimal_type828 = _t1566
                            _t1567 = logic_pb2.Type(decimal_type=decimal_type828)
                            _t1565 = _t1567
                        else:
                            if prediction818 == 8:
                                _t1569 = self.parse_missing_type()
                                missing_type827 = _t1569
                                _t1570 = logic_pb2.Type(missing_type=missing_type827)
                                _t1568 = _t1570
                            else:
                                if prediction818 == 7:
                                    _t1572 = self.parse_datetime_type()
                                    datetime_type826 = _t1572
                                    _t1573 = logic_pb2.Type(datetime_type=datetime_type826)
                                    _t1571 = _t1573
                                else:
                                    if prediction818 == 6:
                                        _t1575 = self.parse_date_type()
                                        date_type825 = _t1575
                                        _t1576 = logic_pb2.Type(date_type=date_type825)
                                        _t1574 = _t1576
                                    else:
                                        if prediction818 == 5:
                                            _t1578 = self.parse_int128_type()
                                            int128_type824 = _t1578
                                            _t1579 = logic_pb2.Type(int128_type=int128_type824)
                                            _t1577 = _t1579
                                        else:
                                            if prediction818 == 4:
                                                _t1581 = self.parse_uint128_type()
                                                uint128_type823 = _t1581
                                                _t1582 = logic_pb2.Type(uint128_type=uint128_type823)
                                                _t1580 = _t1582
                                            else:
                                                if prediction818 == 3:
                                                    _t1584 = self.parse_float_type()
                                                    float_type822 = _t1584
                                                    _t1585 = logic_pb2.Type(float_type=float_type822)
                                                    _t1583 = _t1585
                                                else:
                                                    if prediction818 == 2:
                                                        _t1587 = self.parse_int_type()
                                                        int_type821 = _t1587
                                                        _t1588 = logic_pb2.Type(int_type=int_type821)
                                                        _t1586 = _t1588
                                                    else:
                                                        if prediction818 == 1:
                                                            _t1590 = self.parse_string_type()
                                                            string_type820 = _t1590
                                                            _t1591 = logic_pb2.Type(string_type=string_type820)
                                                            _t1589 = _t1591
                                                        else:
                                                            if prediction818 == 0:
                                                                _t1593 = self.parse_unspecified_type()
                                                                unspecified_type819 = _t1593
                                                                _t1594 = logic_pb2.Type(unspecified_type=unspecified_type819)
                                                                _t1592 = _t1594
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1589 = _t1592
                                                        _t1586 = _t1589
                                                    _t1583 = _t1586
                                                _t1580 = _t1583
                                            _t1577 = _t1580
                                        _t1574 = _t1577
                                    _t1571 = _t1574
                                _t1568 = _t1571
                            _t1565 = _t1568
                        _t1562 = _t1565
                    _t1559 = _t1562
                _t1556 = _t1559
            _t1553 = _t1556
        result834 = _t1553
        self.record_span(span_start833, "Type")
        return result834

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start835 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1595 = logic_pb2.UnspecifiedType()
        result836 = _t1595
        self.record_span(span_start835, "UnspecifiedType")
        return result836

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start837 = self.span_start()
        self.consume_literal("STRING")
        _t1596 = logic_pb2.StringType()
        result838 = _t1596
        self.record_span(span_start837, "StringType")
        return result838

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start839 = self.span_start()
        self.consume_literal("INT")
        _t1597 = logic_pb2.IntType()
        result840 = _t1597
        self.record_span(span_start839, "IntType")
        return result840

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start841 = self.span_start()
        self.consume_literal("FLOAT")
        _t1598 = logic_pb2.FloatType()
        result842 = _t1598
        self.record_span(span_start841, "FloatType")
        return result842

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start843 = self.span_start()
        self.consume_literal("UINT128")
        _t1599 = logic_pb2.UInt128Type()
        result844 = _t1599
        self.record_span(span_start843, "UInt128Type")
        return result844

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start845 = self.span_start()
        self.consume_literal("INT128")
        _t1600 = logic_pb2.Int128Type()
        result846 = _t1600
        self.record_span(span_start845, "Int128Type")
        return result846

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start847 = self.span_start()
        self.consume_literal("DATE")
        _t1601 = logic_pb2.DateType()
        result848 = _t1601
        self.record_span(span_start847, "DateType")
        return result848

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start849 = self.span_start()
        self.consume_literal("DATETIME")
        _t1602 = logic_pb2.DateTimeType()
        result850 = _t1602
        self.record_span(span_start849, "DateTimeType")
        return result850

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start851 = self.span_start()
        self.consume_literal("MISSING")
        _t1603 = logic_pb2.MissingType()
        result852 = _t1603
        self.record_span(span_start851, "MissingType")
        return result852

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start855 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int853 = self.consume_terminal("INT")
        int_3854 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1604 = logic_pb2.DecimalType(precision=int(int853), scale=int(int_3854))
        result856 = _t1604
        self.record_span(span_start855, "DecimalType")
        return result856

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start857 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1605 = logic_pb2.BooleanType()
        result858 = _t1605
        self.record_span(span_start857, "BooleanType")
        return result858

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start859 = self.span_start()
        self.consume_literal("INT32")
        _t1606 = logic_pb2.Int32Type()
        result860 = _t1606
        self.record_span(span_start859, "Int32Type")
        return result860

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start861 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1607 = logic_pb2.Float32Type()
        result862 = _t1607
        self.record_span(span_start861, "Float32Type")
        return result862

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start863 = self.span_start()
        self.consume_literal("UINT32")
        _t1608 = logic_pb2.UInt32Type()
        result864 = _t1608
        self.record_span(span_start863, "UInt32Type")
        return result864

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs865 = []
        cond866 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond866:
            _t1609 = self.parse_binding()
            item867 = _t1609
            xs865.append(item867)
            cond866 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings868 = xs865
        return bindings868

    def parse_formula(self) -> logic_pb2.Formula:
        span_start883 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1611 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1612 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1613 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1614 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1615 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1616 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1617 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1618 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1619 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1620 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1621 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1622 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1623 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1624 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1625 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1626 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1627 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1628 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1629 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1630 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1631 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1632 = 10
                                                                                                else:
                                                                                                    _t1632 = -1
                                                                                                _t1631 = _t1632
                                                                                            _t1630 = _t1631
                                                                                        _t1629 = _t1630
                                                                                    _t1628 = _t1629
                                                                                _t1627 = _t1628
                                                                            _t1626 = _t1627
                                                                        _t1625 = _t1626
                                                                    _t1624 = _t1625
                                                                _t1623 = _t1624
                                                            _t1622 = _t1623
                                                        _t1621 = _t1622
                                                    _t1620 = _t1621
                                                _t1619 = _t1620
                                            _t1618 = _t1619
                                        _t1617 = _t1618
                                    _t1616 = _t1617
                                _t1615 = _t1616
                            _t1614 = _t1615
                        _t1613 = _t1614
                    _t1612 = _t1613
                _t1611 = _t1612
            _t1610 = _t1611
        else:
            _t1610 = -1
        prediction869 = _t1610
        if prediction869 == 12:
            _t1634 = self.parse_cast()
            cast882 = _t1634
            _t1635 = logic_pb2.Formula(cast=cast882)
            _t1633 = _t1635
        else:
            if prediction869 == 11:
                _t1637 = self.parse_rel_atom()
                rel_atom881 = _t1637
                _t1638 = logic_pb2.Formula(rel_atom=rel_atom881)
                _t1636 = _t1638
            else:
                if prediction869 == 10:
                    _t1640 = self.parse_primitive()
                    primitive880 = _t1640
                    _t1641 = logic_pb2.Formula(primitive=primitive880)
                    _t1639 = _t1641
                else:
                    if prediction869 == 9:
                        _t1643 = self.parse_pragma()
                        pragma879 = _t1643
                        _t1644 = logic_pb2.Formula(pragma=pragma879)
                        _t1642 = _t1644
                    else:
                        if prediction869 == 8:
                            _t1646 = self.parse_atom()
                            atom878 = _t1646
                            _t1647 = logic_pb2.Formula(atom=atom878)
                            _t1645 = _t1647
                        else:
                            if prediction869 == 7:
                                _t1649 = self.parse_ffi()
                                ffi877 = _t1649
                                _t1650 = logic_pb2.Formula(ffi=ffi877)
                                _t1648 = _t1650
                            else:
                                if prediction869 == 6:
                                    _t1652 = self.parse_not()
                                    not876 = _t1652
                                    _t1653 = logic_pb2.Formula()
                                    getattr(_t1653, 'not').CopyFrom(not876)
                                    _t1651 = _t1653
                                else:
                                    if prediction869 == 5:
                                        _t1655 = self.parse_disjunction()
                                        disjunction875 = _t1655
                                        _t1656 = logic_pb2.Formula(disjunction=disjunction875)
                                        _t1654 = _t1656
                                    else:
                                        if prediction869 == 4:
                                            _t1658 = self.parse_conjunction()
                                            conjunction874 = _t1658
                                            _t1659 = logic_pb2.Formula(conjunction=conjunction874)
                                            _t1657 = _t1659
                                        else:
                                            if prediction869 == 3:
                                                _t1661 = self.parse_reduce()
                                                reduce873 = _t1661
                                                _t1662 = logic_pb2.Formula(reduce=reduce873)
                                                _t1660 = _t1662
                                            else:
                                                if prediction869 == 2:
                                                    _t1664 = self.parse_exists()
                                                    exists872 = _t1664
                                                    _t1665 = logic_pb2.Formula(exists=exists872)
                                                    _t1663 = _t1665
                                                else:
                                                    if prediction869 == 1:
                                                        _t1667 = self.parse_false()
                                                        false871 = _t1667
                                                        _t1668 = logic_pb2.Formula(disjunction=false871)
                                                        _t1666 = _t1668
                                                    else:
                                                        if prediction869 == 0:
                                                            _t1670 = self.parse_true()
                                                            true870 = _t1670
                                                            _t1671 = logic_pb2.Formula(conjunction=true870)
                                                            _t1669 = _t1671
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1666 = _t1669
                                                    _t1663 = _t1666
                                                _t1660 = _t1663
                                            _t1657 = _t1660
                                        _t1654 = _t1657
                                    _t1651 = _t1654
                                _t1648 = _t1651
                            _t1645 = _t1648
                        _t1642 = _t1645
                    _t1639 = _t1642
                _t1636 = _t1639
            _t1633 = _t1636
        result884 = _t1633
        self.record_span(span_start883, "Formula")
        return result884

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start885 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1672 = logic_pb2.Conjunction(args=[])
        result886 = _t1672
        self.record_span(span_start885, "Conjunction")
        return result886

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start887 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1673 = logic_pb2.Disjunction(args=[])
        result888 = _t1673
        self.record_span(span_start887, "Disjunction")
        return result888

    def parse_exists(self) -> logic_pb2.Exists:
        span_start891 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1674 = self.parse_bindings()
        bindings889 = _t1674
        _t1675 = self.parse_formula()
        formula890 = _t1675
        self.consume_literal(")")
        _t1676 = logic_pb2.Abstraction(vars=(list(bindings889[0]) + list(bindings889[1] if bindings889[1] is not None else [])), value=formula890)
        _t1677 = logic_pb2.Exists(body=_t1676)
        result892 = _t1677
        self.record_span(span_start891, "Exists")
        return result892

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start896 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1678 = self.parse_abstraction()
        abstraction893 = _t1678
        _t1679 = self.parse_abstraction()
        abstraction_3894 = _t1679
        _t1680 = self.parse_terms()
        terms895 = _t1680
        self.consume_literal(")")
        _t1681 = logic_pb2.Reduce(op=abstraction893, body=abstraction_3894, terms=terms895)
        result897 = _t1681
        self.record_span(span_start896, "Reduce")
        return result897
>>>>>>> origin/main

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
<<<<<<< HEAD
        xs864 = []
        cond865 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond865:
            _t1614 = self.parse_term()
            item866 = _t1614
            xs864.append(item866)
            cond865 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms867 = xs864
        self.consume_literal(")")
        return terms867

    def parse_term(self) -> logic_pb2.Term:
        span_start871 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1615 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1616 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1617 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1618 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1619 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1620 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1621 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1622 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1623 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1624 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1625 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1626 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1627 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1628 = 1
                                                            else:
                                                                _t1628 = -1
                                                            _t1627 = _t1628
                                                        _t1626 = _t1627
                                                    _t1625 = _t1626
                                                _t1624 = _t1625
                                            _t1623 = _t1624
                                        _t1622 = _t1623
                                    _t1621 = _t1622
                                _t1620 = _t1621
                            _t1619 = _t1620
                        _t1618 = _t1619
                    _t1617 = _t1618
                _t1616 = _t1617
            _t1615 = _t1616
        prediction868 = _t1615
        if prediction868 == 1:
            _t1630 = self.parse_value()
            value870 = _t1630
            _t1631 = logic_pb2.Term(constant=value870)
            _t1629 = _t1631
        else:
            if prediction868 == 0:
                _t1633 = self.parse_var()
                var869 = _t1633
                _t1634 = logic_pb2.Term(var=var869)
                _t1632 = _t1634
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1629 = _t1632
        result872 = _t1629
        self.record_span(span_start871, "Term")
        return result872
=======
        xs898 = []
        cond899 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond899:
            _t1682 = self.parse_term()
            item900 = _t1682
            xs898.append(item900)
            cond899 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms901 = xs898
        self.consume_literal(")")
        return terms901

    def parse_term(self) -> logic_pb2.Term:
        span_start905 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1683 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1684 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1685 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1686 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1687 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1688 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1689 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1690 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1691 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1692 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1693 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1694 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1695 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1696 = 1
                                                            else:
                                                                _t1696 = -1
                                                            _t1695 = _t1696
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
            _t1683 = _t1684
        prediction902 = _t1683
        if prediction902 == 1:
            _t1698 = self.parse_value()
            value904 = _t1698
            _t1699 = logic_pb2.Term(constant=value904)
            _t1697 = _t1699
        else:
            if prediction902 == 0:
                _t1701 = self.parse_var()
                var903 = _t1701
                _t1702 = logic_pb2.Term(var=var903)
                _t1700 = _t1702
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1697 = _t1700
        result906 = _t1697
        self.record_span(span_start905, "Term")
        return result906

    def parse_var(self) -> logic_pb2.Var:
        span_start908 = self.span_start()
        symbol907 = self.consume_terminal("SYMBOL")
        _t1703 = logic_pb2.Var(name=symbol907)
        result909 = _t1703
        self.record_span(span_start908, "Var")
        return result909
>>>>>>> origin/main

    def parse_var(self) -> logic_pb2.Var:
        span_start874 = self.span_start()
        symbol873 = self.consume_terminal("SYMBOL")
        _t1635 = logic_pb2.Var(name=symbol873)
        result875 = _t1635
        self.record_span(span_start874, "Var")
        return result875

    def parse_value(self) -> logic_pb2.Value:
<<<<<<< HEAD
        span_start889 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1636 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1637 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1638 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1640 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1641 = 0
                            else:
                                _t1641 = -1
                            _t1640 = _t1641
                        _t1639 = _t1640
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1642 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1643 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1644 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1645 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1646 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1647 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1648 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1649 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1650 = 10
                                                        else:
                                                            _t1650 = -1
                                                        _t1649 = _t1650
                                                    _t1648 = _t1649
                                                _t1647 = _t1648
                                            _t1646 = _t1647
                                        _t1645 = _t1646
                                    _t1644 = _t1645
                                _t1643 = _t1644
                            _t1642 = _t1643
                        _t1639 = _t1642
                    _t1638 = _t1639
                _t1637 = _t1638
            _t1636 = _t1637
        prediction876 = _t1636
        if prediction876 == 12:
            _t1652 = self.parse_boolean_value()
            boolean_value888 = _t1652
            _t1653 = logic_pb2.Value(boolean_value=boolean_value888)
            _t1651 = _t1653
        else:
            if prediction876 == 11:
                self.consume_literal("missing")
                _t1655 = logic_pb2.MissingValue()
                _t1656 = logic_pb2.Value(missing_value=_t1655)
                _t1654 = _t1656
            else:
                if prediction876 == 10:
                    formatted_decimal887 = self.consume_terminal("DECIMAL")
                    _t1658 = logic_pb2.Value(decimal_value=formatted_decimal887)
                    _t1657 = _t1658
                else:
                    if prediction876 == 9:
                        formatted_int128886 = self.consume_terminal("INT128")
                        _t1660 = logic_pb2.Value(int128_value=formatted_int128886)
                        _t1659 = _t1660
                    else:
                        if prediction876 == 8:
                            formatted_uint128885 = self.consume_terminal("UINT128")
                            _t1662 = logic_pb2.Value(uint128_value=formatted_uint128885)
                            _t1661 = _t1662
                        else:
                            if prediction876 == 7:
                                formatted_uint32884 = self.consume_terminal("UINT32")
                                _t1664 = logic_pb2.Value(uint32_value=formatted_uint32884)
                                _t1663 = _t1664
                            else:
                                if prediction876 == 6:
                                    formatted_float883 = self.consume_terminal("FLOAT")
                                    _t1666 = logic_pb2.Value(float_value=formatted_float883)
                                    _t1665 = _t1666
                                else:
                                    if prediction876 == 5:
                                        formatted_float32882 = self.consume_terminal("FLOAT32")
                                        _t1668 = logic_pb2.Value(float32_value=formatted_float32882)
                                        _t1667 = _t1668
                                    else:
                                        if prediction876 == 4:
                                            formatted_int881 = self.consume_terminal("INT")
                                            _t1670 = logic_pb2.Value(int_value=formatted_int881)
                                            _t1669 = _t1670
                                        else:
                                            if prediction876 == 3:
                                                formatted_int32880 = self.consume_terminal("INT32")
                                                _t1672 = logic_pb2.Value(int32_value=formatted_int32880)
                                                _t1671 = _t1672
                                            else:
                                                if prediction876 == 2:
                                                    formatted_string879 = self.consume_terminal("STRING")
                                                    _t1674 = logic_pb2.Value(string_value=formatted_string879)
                                                    _t1673 = _t1674
                                                else:
                                                    if prediction876 == 1:
                                                        _t1676 = self.parse_datetime()
                                                        datetime878 = _t1676
                                                        _t1677 = logic_pb2.Value(datetime_value=datetime878)
                                                        _t1675 = _t1677
                                                    else:
                                                        if prediction876 == 0:
                                                            _t1679 = self.parse_date()
                                                            date877 = _t1679
                                                            _t1680 = logic_pb2.Value(date_value=date877)
                                                            _t1678 = _t1680
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1675 = _t1678
                                                    _t1673 = _t1675
                                                _t1671 = _t1673
                                            _t1669 = _t1671
                                        _t1667 = _t1669
                                    _t1665 = _t1667
                                _t1663 = _t1665
                            _t1661 = _t1663
                        _t1659 = _t1661
                    _t1657 = _t1659
                _t1654 = _t1657
            _t1651 = _t1654
        result890 = _t1651
        self.record_span(span_start889, "Value")
        return result890

    def parse_date(self) -> logic_pb2.DateValue:
        span_start894 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int891 = self.consume_terminal("INT")
        formatted_int_3892 = self.consume_terminal("INT")
        formatted_int_4893 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1681 = logic_pb2.DateValue(year=int(formatted_int891), month=int(formatted_int_3892), day=int(formatted_int_4893))
        result895 = _t1681
        self.record_span(span_start894, "DateValue")
        return result895

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start903 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int896 = self.consume_terminal("INT")
        formatted_int_3897 = self.consume_terminal("INT")
        formatted_int_4898 = self.consume_terminal("INT")
        formatted_int_5899 = self.consume_terminal("INT")
        formatted_int_6900 = self.consume_terminal("INT")
        formatted_int_7901 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1682 = self.consume_terminal("INT")
        else:
            _t1682 = None
        formatted_int_8902 = _t1682
        self.consume_literal(")")
        _t1683 = logic_pb2.DateTimeValue(year=int(formatted_int896), month=int(formatted_int_3897), day=int(formatted_int_4898), hour=int(formatted_int_5899), minute=int(formatted_int_6900), second=int(formatted_int_7901), microsecond=int((formatted_int_8902 if formatted_int_8902 is not None else 0)))
        result904 = _t1683
        self.record_span(span_start903, "DateTimeValue")
        return result904

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start909 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs905 = []
        cond906 = self.match_lookahead_literal("(", 0)
        while cond906:
            _t1684 = self.parse_formula()
            item907 = _t1684
            xs905.append(item907)
            cond906 = self.match_lookahead_literal("(", 0)
        formulas908 = xs905
        self.consume_literal(")")
        _t1685 = logic_pb2.Conjunction(args=formulas908)
        result910 = _t1685
        self.record_span(span_start909, "Conjunction")
        return result910

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start915 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs911 = []
        cond912 = self.match_lookahead_literal("(", 0)
        while cond912:
            _t1686 = self.parse_formula()
            item913 = _t1686
            xs911.append(item913)
            cond912 = self.match_lookahead_literal("(", 0)
        formulas914 = xs911
        self.consume_literal(")")
        _t1687 = logic_pb2.Disjunction(args=formulas914)
        result916 = _t1687
        self.record_span(span_start915, "Disjunction")
        return result916
=======
        span_start923 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1704 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1705 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1706 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1708 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1709 = 0
                            else:
                                _t1709 = -1
                            _t1708 = _t1709
                        _t1707 = _t1708
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1710 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1711 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1712 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1713 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1714 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1715 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1716 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1717 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1718 = 10
                                                        else:
                                                            _t1718 = -1
                                                        _t1717 = _t1718
                                                    _t1716 = _t1717
                                                _t1715 = _t1716
                                            _t1714 = _t1715
                                        _t1713 = _t1714
                                    _t1712 = _t1713
                                _t1711 = _t1712
                            _t1710 = _t1711
                        _t1707 = _t1710
                    _t1706 = _t1707
                _t1705 = _t1706
            _t1704 = _t1705
        prediction910 = _t1704
        if prediction910 == 12:
            _t1720 = self.parse_boolean_value()
            boolean_value922 = _t1720
            _t1721 = logic_pb2.Value(boolean_value=boolean_value922)
            _t1719 = _t1721
        else:
            if prediction910 == 11:
                self.consume_literal("missing")
                _t1723 = logic_pb2.MissingValue()
                _t1724 = logic_pb2.Value(missing_value=_t1723)
                _t1722 = _t1724
            else:
                if prediction910 == 10:
                    formatted_decimal921 = self.consume_terminal("DECIMAL")
                    _t1726 = logic_pb2.Value(decimal_value=formatted_decimal921)
                    _t1725 = _t1726
                else:
                    if prediction910 == 9:
                        formatted_int128920 = self.consume_terminal("INT128")
                        _t1728 = logic_pb2.Value(int128_value=formatted_int128920)
                        _t1727 = _t1728
                    else:
                        if prediction910 == 8:
                            formatted_uint128919 = self.consume_terminal("UINT128")
                            _t1730 = logic_pb2.Value(uint128_value=formatted_uint128919)
                            _t1729 = _t1730
                        else:
                            if prediction910 == 7:
                                formatted_uint32918 = self.consume_terminal("UINT32")
                                _t1732 = logic_pb2.Value(uint32_value=formatted_uint32918)
                                _t1731 = _t1732
                            else:
                                if prediction910 == 6:
                                    formatted_float917 = self.consume_terminal("FLOAT")
                                    _t1734 = logic_pb2.Value(float_value=formatted_float917)
                                    _t1733 = _t1734
                                else:
                                    if prediction910 == 5:
                                        formatted_float32916 = self.consume_terminal("FLOAT32")
                                        _t1736 = logic_pb2.Value(float32_value=formatted_float32916)
                                        _t1735 = _t1736
                                    else:
                                        if prediction910 == 4:
                                            formatted_int915 = self.consume_terminal("INT")
                                            _t1738 = logic_pb2.Value(int_value=formatted_int915)
                                            _t1737 = _t1738
                                        else:
                                            if prediction910 == 3:
                                                formatted_int32914 = self.consume_terminal("INT32")
                                                _t1740 = logic_pb2.Value(int32_value=formatted_int32914)
                                                _t1739 = _t1740
                                            else:
                                                if prediction910 == 2:
                                                    formatted_string913 = self.consume_terminal("STRING")
                                                    _t1742 = logic_pb2.Value(string_value=formatted_string913)
                                                    _t1741 = _t1742
                                                else:
                                                    if prediction910 == 1:
                                                        _t1744 = self.parse_datetime()
                                                        datetime912 = _t1744
                                                        _t1745 = logic_pb2.Value(datetime_value=datetime912)
                                                        _t1743 = _t1745
                                                    else:
                                                        if prediction910 == 0:
                                                            _t1747 = self.parse_date()
                                                            date911 = _t1747
                                                            _t1748 = logic_pb2.Value(date_value=date911)
                                                            _t1746 = _t1748
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1743 = _t1746
                                                    _t1741 = _t1743
                                                _t1739 = _t1741
                                            _t1737 = _t1739
                                        _t1735 = _t1737
                                    _t1733 = _t1735
                                _t1731 = _t1733
                            _t1729 = _t1731
                        _t1727 = _t1729
                    _t1725 = _t1727
                _t1722 = _t1725
            _t1719 = _t1722
        result924 = _t1719
        self.record_span(span_start923, "Value")
        return result924

    def parse_date(self) -> logic_pb2.DateValue:
        span_start928 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int925 = self.consume_terminal("INT")
        formatted_int_3926 = self.consume_terminal("INT")
        formatted_int_4927 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1749 = logic_pb2.DateValue(year=int(formatted_int925), month=int(formatted_int_3926), day=int(formatted_int_4927))
        result929 = _t1749
        self.record_span(span_start928, "DateValue")
        return result929

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start937 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int930 = self.consume_terminal("INT")
        formatted_int_3931 = self.consume_terminal("INT")
        formatted_int_4932 = self.consume_terminal("INT")
        formatted_int_5933 = self.consume_terminal("INT")
        formatted_int_6934 = self.consume_terminal("INT")
        formatted_int_7935 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1750 = self.consume_terminal("INT")
        else:
            _t1750 = None
        formatted_int_8936 = _t1750
        self.consume_literal(")")
        _t1751 = logic_pb2.DateTimeValue(year=int(formatted_int930), month=int(formatted_int_3931), day=int(formatted_int_4932), hour=int(formatted_int_5933), minute=int(formatted_int_6934), second=int(formatted_int_7935), microsecond=int((formatted_int_8936 if formatted_int_8936 is not None else 0)))
        result938 = _t1751
        self.record_span(span_start937, "DateTimeValue")
        return result938

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start943 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs939 = []
        cond940 = self.match_lookahead_literal("(", 0)
        while cond940:
            _t1752 = self.parse_formula()
            item941 = _t1752
            xs939.append(item941)
            cond940 = self.match_lookahead_literal("(", 0)
        formulas942 = xs939
        self.consume_literal(")")
        _t1753 = logic_pb2.Conjunction(args=formulas942)
        result944 = _t1753
        self.record_span(span_start943, "Conjunction")
        return result944

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start949 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs945 = []
        cond946 = self.match_lookahead_literal("(", 0)
        while cond946:
            _t1754 = self.parse_formula()
            item947 = _t1754
            xs945.append(item947)
            cond946 = self.match_lookahead_literal("(", 0)
        formulas948 = xs945
        self.consume_literal(")")
        _t1755 = logic_pb2.Disjunction(args=formulas948)
        result950 = _t1755
        self.record_span(span_start949, "Disjunction")
        return result950

    def parse_not(self) -> logic_pb2.Not:
        span_start952 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1756 = self.parse_formula()
        formula951 = _t1756
        self.consume_literal(")")
        _t1757 = logic_pb2.Not(arg=formula951)
        result953 = _t1757
        self.record_span(span_start952, "Not")
        return result953
>>>>>>> origin/main

    def parse_not(self) -> logic_pb2.Not:
        span_start918 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1688 = self.parse_formula()
        formula917 = _t1688
        self.consume_literal(")")
        _t1689 = logic_pb2.Not(arg=formula917)
        result919 = _t1689
        self.record_span(span_start918, "Not")
        return result919

    def parse_ffi(self) -> logic_pb2.FFI:
<<<<<<< HEAD
        span_start923 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1690 = self.parse_name()
        name920 = _t1690
        _t1691 = self.parse_ffi_args()
        ffi_args921 = _t1691
        _t1692 = self.parse_terms()
        terms922 = _t1692
        self.consume_literal(")")
        _t1693 = logic_pb2.FFI(name=name920, args=ffi_args921, terms=terms922)
        result924 = _t1693
        self.record_span(span_start923, "FFI")
        return result924

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol925 = self.consume_terminal("SYMBOL")
        return symbol925
=======
        span_start957 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1758 = self.parse_name()
        name954 = _t1758
        _t1759 = self.parse_ffi_args()
        ffi_args955 = _t1759
        _t1760 = self.parse_terms()
        terms956 = _t1760
        self.consume_literal(")")
        _t1761 = logic_pb2.FFI(name=name954, args=ffi_args955, terms=terms956)
        result958 = _t1761
        self.record_span(span_start957, "FFI")
        return result958

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol959 = self.consume_terminal("SYMBOL")
        return symbol959
>>>>>>> origin/main

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
<<<<<<< HEAD
        xs926 = []
        cond927 = self.match_lookahead_literal("(", 0)
        while cond927:
            _t1694 = self.parse_abstraction()
            item928 = _t1694
            xs926.append(item928)
            cond927 = self.match_lookahead_literal("(", 0)
        abstractions929 = xs926
        self.consume_literal(")")
        return abstractions929

    def parse_atom(self) -> logic_pb2.Atom:
        span_start935 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1695 = self.parse_relation_id()
        relation_id930 = _t1695
        xs931 = []
        cond932 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond932:
            _t1696 = self.parse_term()
            item933 = _t1696
            xs931.append(item933)
            cond932 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms934 = xs931
        self.consume_literal(")")
        _t1697 = logic_pb2.Atom(name=relation_id930, terms=terms934)
        result936 = _t1697
        self.record_span(span_start935, "Atom")
        return result936

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start942 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1698 = self.parse_name()
        name937 = _t1698
        xs938 = []
        cond939 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond939:
            _t1699 = self.parse_term()
            item940 = _t1699
            xs938.append(item940)
            cond939 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms941 = xs938
        self.consume_literal(")")
        _t1700 = logic_pb2.Pragma(name=name937, terms=terms941)
        result943 = _t1700
        self.record_span(span_start942, "Pragma")
        return result943

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start959 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1702 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1703 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1704 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1705 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1706 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1707 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1708 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1709 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1710 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1711 = 7
                                                else:
                                                    _t1711 = -1
                                                _t1710 = _t1711
                                            _t1709 = _t1710
                                        _t1708 = _t1709
                                    _t1707 = _t1708
                                _t1706 = _t1707
                            _t1705 = _t1706
                        _t1704 = _t1705
                    _t1703 = _t1704
                _t1702 = _t1703
            _t1701 = _t1702
        else:
            _t1701 = -1
        prediction944 = _t1701
        if prediction944 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1713 = self.parse_name()
            name954 = _t1713
            xs955 = []
            cond956 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond956:
                _t1714 = self.parse_rel_term()
                item957 = _t1714
                xs955.append(item957)
                cond956 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms958 = xs955
            self.consume_literal(")")
            _t1715 = logic_pb2.Primitive(name=name954, terms=rel_terms958)
            _t1712 = _t1715
        else:
            if prediction944 == 8:
                _t1717 = self.parse_divide()
                divide953 = _t1717
                _t1716 = divide953
            else:
                if prediction944 == 7:
                    _t1719 = self.parse_multiply()
                    multiply952 = _t1719
                    _t1718 = multiply952
                else:
                    if prediction944 == 6:
                        _t1721 = self.parse_minus()
                        minus951 = _t1721
                        _t1720 = minus951
                    else:
                        if prediction944 == 5:
                            _t1723 = self.parse_add()
                            add950 = _t1723
                            _t1722 = add950
                        else:
                            if prediction944 == 4:
                                _t1725 = self.parse_gt_eq()
                                gt_eq949 = _t1725
                                _t1724 = gt_eq949
                            else:
                                if prediction944 == 3:
                                    _t1727 = self.parse_gt()
                                    gt948 = _t1727
                                    _t1726 = gt948
                                else:
                                    if prediction944 == 2:
                                        _t1729 = self.parse_lt_eq()
                                        lt_eq947 = _t1729
                                        _t1728 = lt_eq947
                                    else:
                                        if prediction944 == 1:
                                            _t1731 = self.parse_lt()
                                            lt946 = _t1731
                                            _t1730 = lt946
                                        else:
                                            if prediction944 == 0:
                                                _t1733 = self.parse_eq()
                                                eq945 = _t1733
                                                _t1732 = eq945
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1730 = _t1732
                                        _t1728 = _t1730
                                    _t1726 = _t1728
                                _t1724 = _t1726
                            _t1722 = _t1724
                        _t1720 = _t1722
                    _t1718 = _t1720
                _t1716 = _t1718
            _t1712 = _t1716
        result960 = _t1712
        self.record_span(span_start959, "Primitive")
        return result960

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start963 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1734 = self.parse_term()
        term961 = _t1734
        _t1735 = self.parse_term()
        term_3962 = _t1735
        self.consume_literal(")")
        _t1736 = logic_pb2.RelTerm(term=term961)
        _t1737 = logic_pb2.RelTerm(term=term_3962)
        _t1738 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1736, _t1737])
        result964 = _t1738
        self.record_span(span_start963, "Primitive")
        return result964

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start967 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1739 = self.parse_term()
        term965 = _t1739
        _t1740 = self.parse_term()
        term_3966 = _t1740
        self.consume_literal(")")
        _t1741 = logic_pb2.RelTerm(term=term965)
        _t1742 = logic_pb2.RelTerm(term=term_3966)
        _t1743 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1741, _t1742])
        result968 = _t1743
        self.record_span(span_start967, "Primitive")
        return result968

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start971 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1744 = self.parse_term()
        term969 = _t1744
        _t1745 = self.parse_term()
        term_3970 = _t1745
        self.consume_literal(")")
        _t1746 = logic_pb2.RelTerm(term=term969)
        _t1747 = logic_pb2.RelTerm(term=term_3970)
        _t1748 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1746, _t1747])
        result972 = _t1748
        self.record_span(span_start971, "Primitive")
        return result972

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start975 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1749 = self.parse_term()
        term973 = _t1749
        _t1750 = self.parse_term()
        term_3974 = _t1750
        self.consume_literal(")")
        _t1751 = logic_pb2.RelTerm(term=term973)
        _t1752 = logic_pb2.RelTerm(term=term_3974)
        _t1753 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1751, _t1752])
        result976 = _t1753
        self.record_span(span_start975, "Primitive")
        return result976

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start979 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1754 = self.parse_term()
        term977 = _t1754
        _t1755 = self.parse_term()
        term_3978 = _t1755
        self.consume_literal(")")
        _t1756 = logic_pb2.RelTerm(term=term977)
        _t1757 = logic_pb2.RelTerm(term=term_3978)
        _t1758 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1756, _t1757])
        result980 = _t1758
        self.record_span(span_start979, "Primitive")
        return result980

    def parse_add(self) -> logic_pb2.Primitive:
        span_start984 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1759 = self.parse_term()
        term981 = _t1759
        _t1760 = self.parse_term()
        term_3982 = _t1760
        _t1761 = self.parse_term()
        term_4983 = _t1761
        self.consume_literal(")")
        _t1762 = logic_pb2.RelTerm(term=term981)
        _t1763 = logic_pb2.RelTerm(term=term_3982)
        _t1764 = logic_pb2.RelTerm(term=term_4983)
        _t1765 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1762, _t1763, _t1764])
        result985 = _t1765
        self.record_span(span_start984, "Primitive")
        return result985

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start989 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1766 = self.parse_term()
        term986 = _t1766
        _t1767 = self.parse_term()
        term_3987 = _t1767
        _t1768 = self.parse_term()
        term_4988 = _t1768
        self.consume_literal(")")
        _t1769 = logic_pb2.RelTerm(term=term986)
        _t1770 = logic_pb2.RelTerm(term=term_3987)
        _t1771 = logic_pb2.RelTerm(term=term_4988)
        _t1772 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1769, _t1770, _t1771])
        result990 = _t1772
        self.record_span(span_start989, "Primitive")
        return result990

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start994 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1773 = self.parse_term()
        term991 = _t1773
        _t1774 = self.parse_term()
        term_3992 = _t1774
        _t1775 = self.parse_term()
        term_4993 = _t1775
        self.consume_literal(")")
        _t1776 = logic_pb2.RelTerm(term=term991)
        _t1777 = logic_pb2.RelTerm(term=term_3992)
        _t1778 = logic_pb2.RelTerm(term=term_4993)
        _t1779 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1776, _t1777, _t1778])
        result995 = _t1779
        self.record_span(span_start994, "Primitive")
        return result995

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start999 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1780 = self.parse_term()
        term996 = _t1780
        _t1781 = self.parse_term()
        term_3997 = _t1781
        _t1782 = self.parse_term()
        term_4998 = _t1782
        self.consume_literal(")")
        _t1783 = logic_pb2.RelTerm(term=term996)
        _t1784 = logic_pb2.RelTerm(term=term_3997)
        _t1785 = logic_pb2.RelTerm(term=term_4998)
        _t1786 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1783, _t1784, _t1785])
        result1000 = _t1786
        self.record_span(span_start999, "Primitive")
        return result1000

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1004 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1787 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1788 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1789 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1790 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1791 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1792 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1793 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1794 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1795 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1796 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1797 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1798 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1799 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1800 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1801 = 1
                                                                else:
                                                                    _t1801 = -1
                                                                _t1800 = _t1801
                                                            _t1799 = _t1800
                                                        _t1798 = _t1799
                                                    _t1797 = _t1798
                                                _t1796 = _t1797
                                            _t1795 = _t1796
                                        _t1794 = _t1795
                                    _t1793 = _t1794
                                _t1792 = _t1793
                            _t1791 = _t1792
                        _t1790 = _t1791
                    _t1789 = _t1790
                _t1788 = _t1789
            _t1787 = _t1788
        prediction1001 = _t1787
        if prediction1001 == 1:
            _t1803 = self.parse_term()
            term1003 = _t1803
            _t1804 = logic_pb2.RelTerm(term=term1003)
            _t1802 = _t1804
        else:
            if prediction1001 == 0:
                _t1806 = self.parse_specialized_value()
                specialized_value1002 = _t1806
                _t1807 = logic_pb2.RelTerm(specialized_value=specialized_value1002)
                _t1805 = _t1807
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1802 = _t1805
        result1005 = _t1802
        self.record_span(span_start1004, "RelTerm")
        return result1005
=======
        xs960 = []
        cond961 = self.match_lookahead_literal("(", 0)
        while cond961:
            _t1762 = self.parse_abstraction()
            item962 = _t1762
            xs960.append(item962)
            cond961 = self.match_lookahead_literal("(", 0)
        abstractions963 = xs960
        self.consume_literal(")")
        return abstractions963

    def parse_atom(self) -> logic_pb2.Atom:
        span_start969 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1763 = self.parse_relation_id()
        relation_id964 = _t1763
        xs965 = []
        cond966 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond966:
            _t1764 = self.parse_term()
            item967 = _t1764
            xs965.append(item967)
            cond966 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms968 = xs965
        self.consume_literal(")")
        _t1765 = logic_pb2.Atom(name=relation_id964, terms=terms968)
        result970 = _t1765
        self.record_span(span_start969, "Atom")
        return result970

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start976 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1766 = self.parse_name()
        name971 = _t1766
        xs972 = []
        cond973 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond973:
            _t1767 = self.parse_term()
            item974 = _t1767
            xs972.append(item974)
            cond973 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms975 = xs972
        self.consume_literal(")")
        _t1768 = logic_pb2.Pragma(name=name971, terms=terms975)
        result977 = _t1768
        self.record_span(span_start976, "Pragma")
        return result977

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start993 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1770 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1771 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1772 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1773 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1774 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1775 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1776 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1777 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1778 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1779 = 7
                                                else:
                                                    _t1779 = -1
                                                _t1778 = _t1779
                                            _t1777 = _t1778
                                        _t1776 = _t1777
                                    _t1775 = _t1776
                                _t1774 = _t1775
                            _t1773 = _t1774
                        _t1772 = _t1773
                    _t1771 = _t1772
                _t1770 = _t1771
            _t1769 = _t1770
        else:
            _t1769 = -1
        prediction978 = _t1769
        if prediction978 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1781 = self.parse_name()
            name988 = _t1781
            xs989 = []
            cond990 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond990:
                _t1782 = self.parse_rel_term()
                item991 = _t1782
                xs989.append(item991)
                cond990 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms992 = xs989
            self.consume_literal(")")
            _t1783 = logic_pb2.Primitive(name=name988, terms=rel_terms992)
            _t1780 = _t1783
        else:
            if prediction978 == 8:
                _t1785 = self.parse_divide()
                divide987 = _t1785
                _t1784 = divide987
            else:
                if prediction978 == 7:
                    _t1787 = self.parse_multiply()
                    multiply986 = _t1787
                    _t1786 = multiply986
                else:
                    if prediction978 == 6:
                        _t1789 = self.parse_minus()
                        minus985 = _t1789
                        _t1788 = minus985
                    else:
                        if prediction978 == 5:
                            _t1791 = self.parse_add()
                            add984 = _t1791
                            _t1790 = add984
                        else:
                            if prediction978 == 4:
                                _t1793 = self.parse_gt_eq()
                                gt_eq983 = _t1793
                                _t1792 = gt_eq983
                            else:
                                if prediction978 == 3:
                                    _t1795 = self.parse_gt()
                                    gt982 = _t1795
                                    _t1794 = gt982
                                else:
                                    if prediction978 == 2:
                                        _t1797 = self.parse_lt_eq()
                                        lt_eq981 = _t1797
                                        _t1796 = lt_eq981
                                    else:
                                        if prediction978 == 1:
                                            _t1799 = self.parse_lt()
                                            lt980 = _t1799
                                            _t1798 = lt980
                                        else:
                                            if prediction978 == 0:
                                                _t1801 = self.parse_eq()
                                                eq979 = _t1801
                                                _t1800 = eq979
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1798 = _t1800
                                        _t1796 = _t1798
                                    _t1794 = _t1796
                                _t1792 = _t1794
                            _t1790 = _t1792
                        _t1788 = _t1790
                    _t1786 = _t1788
                _t1784 = _t1786
            _t1780 = _t1784
        result994 = _t1780
        self.record_span(span_start993, "Primitive")
        return result994

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start997 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1802 = self.parse_term()
        term995 = _t1802
        _t1803 = self.parse_term()
        term_3996 = _t1803
        self.consume_literal(")")
        _t1804 = logic_pb2.RelTerm(term=term995)
        _t1805 = logic_pb2.RelTerm(term=term_3996)
        _t1806 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1804, _t1805])
        result998 = _t1806
        self.record_span(span_start997, "Primitive")
        return result998

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start1001 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1807 = self.parse_term()
        term999 = _t1807
        _t1808 = self.parse_term()
        term_31000 = _t1808
        self.consume_literal(")")
        _t1809 = logic_pb2.RelTerm(term=term999)
        _t1810 = logic_pb2.RelTerm(term=term_31000)
        _t1811 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1809, _t1810])
        result1002 = _t1811
        self.record_span(span_start1001, "Primitive")
        return result1002

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start1005 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1812 = self.parse_term()
        term1003 = _t1812
        _t1813 = self.parse_term()
        term_31004 = _t1813
        self.consume_literal(")")
        _t1814 = logic_pb2.RelTerm(term=term1003)
        _t1815 = logic_pb2.RelTerm(term=term_31004)
        _t1816 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1814, _t1815])
        result1006 = _t1816
        self.record_span(span_start1005, "Primitive")
        return result1006

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start1009 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1817 = self.parse_term()
        term1007 = _t1817
        _t1818 = self.parse_term()
        term_31008 = _t1818
        self.consume_literal(")")
        _t1819 = logic_pb2.RelTerm(term=term1007)
        _t1820 = logic_pb2.RelTerm(term=term_31008)
        _t1821 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1819, _t1820])
        result1010 = _t1821
        self.record_span(span_start1009, "Primitive")
        return result1010

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start1013 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1822 = self.parse_term()
        term1011 = _t1822
        _t1823 = self.parse_term()
        term_31012 = _t1823
        self.consume_literal(")")
        _t1824 = logic_pb2.RelTerm(term=term1011)
        _t1825 = logic_pb2.RelTerm(term=term_31012)
        _t1826 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1824, _t1825])
        result1014 = _t1826
        self.record_span(span_start1013, "Primitive")
        return result1014

    def parse_add(self) -> logic_pb2.Primitive:
        span_start1018 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1827 = self.parse_term()
        term1015 = _t1827
        _t1828 = self.parse_term()
        term_31016 = _t1828
        _t1829 = self.parse_term()
        term_41017 = _t1829
        self.consume_literal(")")
        _t1830 = logic_pb2.RelTerm(term=term1015)
        _t1831 = logic_pb2.RelTerm(term=term_31016)
        _t1832 = logic_pb2.RelTerm(term=term_41017)
        _t1833 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1830, _t1831, _t1832])
        result1019 = _t1833
        self.record_span(span_start1018, "Primitive")
        return result1019

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start1023 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1834 = self.parse_term()
        term1020 = _t1834
        _t1835 = self.parse_term()
        term_31021 = _t1835
        _t1836 = self.parse_term()
        term_41022 = _t1836
        self.consume_literal(")")
        _t1837 = logic_pb2.RelTerm(term=term1020)
        _t1838 = logic_pb2.RelTerm(term=term_31021)
        _t1839 = logic_pb2.RelTerm(term=term_41022)
        _t1840 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1837, _t1838, _t1839])
        result1024 = _t1840
        self.record_span(span_start1023, "Primitive")
        return result1024

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start1028 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1841 = self.parse_term()
        term1025 = _t1841
        _t1842 = self.parse_term()
        term_31026 = _t1842
        _t1843 = self.parse_term()
        term_41027 = _t1843
        self.consume_literal(")")
        _t1844 = logic_pb2.RelTerm(term=term1025)
        _t1845 = logic_pb2.RelTerm(term=term_31026)
        _t1846 = logic_pb2.RelTerm(term=term_41027)
        _t1847 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1844, _t1845, _t1846])
        result1029 = _t1847
        self.record_span(span_start1028, "Primitive")
        return result1029

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start1033 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1848 = self.parse_term()
        term1030 = _t1848
        _t1849 = self.parse_term()
        term_31031 = _t1849
        _t1850 = self.parse_term()
        term_41032 = _t1850
        self.consume_literal(")")
        _t1851 = logic_pb2.RelTerm(term=term1030)
        _t1852 = logic_pb2.RelTerm(term=term_31031)
        _t1853 = logic_pb2.RelTerm(term=term_41032)
        _t1854 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1851, _t1852, _t1853])
        result1034 = _t1854
        self.record_span(span_start1033, "Primitive")
        return result1034

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1038 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1855 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1856 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1857 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1858 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1859 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1860 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1861 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1862 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1863 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1864 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1865 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1866 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1867 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1868 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1869 = 1
                                                                else:
                                                                    _t1869 = -1
                                                                _t1868 = _t1869
                                                            _t1867 = _t1868
                                                        _t1866 = _t1867
                                                    _t1865 = _t1866
                                                _t1864 = _t1865
                                            _t1863 = _t1864
                                        _t1862 = _t1863
                                    _t1861 = _t1862
                                _t1860 = _t1861
                            _t1859 = _t1860
                        _t1858 = _t1859
                    _t1857 = _t1858
                _t1856 = _t1857
            _t1855 = _t1856
        prediction1035 = _t1855
        if prediction1035 == 1:
            _t1871 = self.parse_term()
            term1037 = _t1871
            _t1872 = logic_pb2.RelTerm(term=term1037)
            _t1870 = _t1872
        else:
            if prediction1035 == 0:
                _t1874 = self.parse_specialized_value()
                specialized_value1036 = _t1874
                _t1875 = logic_pb2.RelTerm(specialized_value=specialized_value1036)
                _t1873 = _t1875
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1870 = _t1873
        result1039 = _t1870
        self.record_span(span_start1038, "RelTerm")
        return result1039

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1041 = self.span_start()
        self.consume_literal("#")
        _t1876 = self.parse_raw_value()
        raw_value1040 = _t1876
        result1042 = raw_value1040
        self.record_span(span_start1041, "Value")
        return result1042
>>>>>>> origin/main

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1007 = self.span_start()
        self.consume_literal("#")
        _t1808 = self.parse_raw_value()
        raw_value1006 = _t1808
        result1008 = raw_value1006
        self.record_span(span_start1007, "Value")
        return result1008

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
<<<<<<< HEAD
        span_start1014 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1809 = self.parse_name()
        name1009 = _t1809
        xs1010 = []
        cond1011 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1011:
            _t1810 = self.parse_rel_term()
            item1012 = _t1810
            xs1010.append(item1012)
            cond1011 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1013 = xs1010
        self.consume_literal(")")
        _t1811 = logic_pb2.RelAtom(name=name1009, terms=rel_terms1013)
        result1015 = _t1811
        self.record_span(span_start1014, "RelAtom")
        return result1015

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1018 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1812 = self.parse_term()
        term1016 = _t1812
        _t1813 = self.parse_term()
        term_31017 = _t1813
        self.consume_literal(")")
        _t1814 = logic_pb2.Cast(input=term1016, result=term_31017)
        result1019 = _t1814
        self.record_span(span_start1018, "Cast")
        return result1019
=======
        span_start1048 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1877 = self.parse_name()
        name1043 = _t1877
        xs1044 = []
        cond1045 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1045:
            _t1878 = self.parse_rel_term()
            item1046 = _t1878
            xs1044.append(item1046)
            cond1045 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1047 = xs1044
        self.consume_literal(")")
        _t1879 = logic_pb2.RelAtom(name=name1043, terms=rel_terms1047)
        result1049 = _t1879
        self.record_span(span_start1048, "RelAtom")
        return result1049

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1052 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1880 = self.parse_term()
        term1050 = _t1880
        _t1881 = self.parse_term()
        term_31051 = _t1881
        self.consume_literal(")")
        _t1882 = logic_pb2.Cast(input=term1050, result=term_31051)
        result1053 = _t1882
        self.record_span(span_start1052, "Cast")
        return result1053
>>>>>>> origin/main

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
<<<<<<< HEAD
        xs1020 = []
        cond1021 = self.match_lookahead_literal("(", 0)
        while cond1021:
            _t1815 = self.parse_attribute()
            item1022 = _t1815
            xs1020.append(item1022)
            cond1021 = self.match_lookahead_literal("(", 0)
        attributes1023 = xs1020
        self.consume_literal(")")
        return attributes1023

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1029 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1816 = self.parse_name()
        name1024 = _t1816
        xs1025 = []
        cond1026 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1026:
            _t1817 = self.parse_raw_value()
            item1027 = _t1817
            xs1025.append(item1027)
            cond1026 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1028 = xs1025
        self.consume_literal(")")
        _t1818 = logic_pb2.Attribute(name=name1024, args=raw_values1028)
        result1030 = _t1818
        self.record_span(span_start1029, "Attribute")
        return result1030

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1037 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1031 = []
        cond1032 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1032:
            _t1819 = self.parse_relation_id()
            item1033 = _t1819
            xs1031.append(item1033)
            cond1032 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1034 = xs1031
        _t1820 = self.parse_script()
        script1035 = _t1820
        if self.match_lookahead_literal("(", 0):
            _t1822 = self.parse_attrs()
            _t1821 = _t1822
        else:
            _t1821 = None
        attrs1036 = _t1821
        self.consume_literal(")")
        _t1823 = logic_pb2.Algorithm(body=script1035, attrs=(attrs1036 if attrs1036 is not None else []))
        getattr(_t1823, 'global').extend(relation_ids1034)
        result1038 = _t1823
        self.record_span(span_start1037, "Algorithm")
        return result1038

    def parse_script(self) -> logic_pb2.Script:
        span_start1043 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1039 = []
        cond1040 = self.match_lookahead_literal("(", 0)
        while cond1040:
            _t1824 = self.parse_construct()
            item1041 = _t1824
            xs1039.append(item1041)
            cond1040 = self.match_lookahead_literal("(", 0)
        constructs1042 = xs1039
        self.consume_literal(")")
        _t1825 = logic_pb2.Script(constructs=constructs1042)
        result1044 = _t1825
        self.record_span(span_start1043, "Script")
        return result1044

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1048 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1827 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1828 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1829 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1830 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1831 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1832 = 1
                                else:
                                    _t1832 = -1
                                _t1831 = _t1832
                            _t1830 = _t1831
                        _t1829 = _t1830
                    _t1828 = _t1829
                _t1827 = _t1828
            _t1826 = _t1827
        else:
            _t1826 = -1
        prediction1045 = _t1826
        if prediction1045 == 1:
            _t1834 = self.parse_instruction()
            instruction1047 = _t1834
            _t1835 = logic_pb2.Construct(instruction=instruction1047)
            _t1833 = _t1835
        else:
            if prediction1045 == 0:
                _t1837 = self.parse_loop()
                loop1046 = _t1837
                _t1838 = logic_pb2.Construct(loop=loop1046)
                _t1836 = _t1838
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1833 = _t1836
        result1049 = _t1833
        self.record_span(span_start1048, "Construct")
        return result1049

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1053 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1839 = self.parse_init()
        init1050 = _t1839
        _t1840 = self.parse_script()
        script1051 = _t1840
        if self.match_lookahead_literal("(", 0):
            _t1842 = self.parse_attrs()
            _t1841 = _t1842
        else:
            _t1841 = None
        attrs1052 = _t1841
        self.consume_literal(")")
        _t1843 = logic_pb2.Loop(init=init1050, body=script1051, attrs=(attrs1052 if attrs1052 is not None else []))
        result1054 = _t1843
        self.record_span(span_start1053, "Loop")
        return result1054
=======
        xs1054 = []
        cond1055 = self.match_lookahead_literal("(", 0)
        while cond1055:
            _t1883 = self.parse_attribute()
            item1056 = _t1883
            xs1054.append(item1056)
            cond1055 = self.match_lookahead_literal("(", 0)
        attributes1057 = xs1054
        self.consume_literal(")")
        return attributes1057

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1063 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1884 = self.parse_name()
        name1058 = _t1884
        xs1059 = []
        cond1060 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1060:
            _t1885 = self.parse_raw_value()
            item1061 = _t1885
            xs1059.append(item1061)
            cond1060 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1062 = xs1059
        self.consume_literal(")")
        _t1886 = logic_pb2.Attribute(name=name1058, args=raw_values1062)
        result1064 = _t1886
        self.record_span(span_start1063, "Attribute")
        return result1064

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1071 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1065 = []
        cond1066 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1066:
            _t1887 = self.parse_relation_id()
            item1067 = _t1887
            xs1065.append(item1067)
            cond1066 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1068 = xs1065
        _t1888 = self.parse_script()
        script1069 = _t1888
        if self.match_lookahead_literal("(", 0):
            _t1890 = self.parse_attrs()
            _t1889 = _t1890
        else:
            _t1889 = None
        attrs1070 = _t1889
        self.consume_literal(")")
        _t1891 = logic_pb2.Algorithm(body=script1069, attrs=(attrs1070 if attrs1070 is not None else []))
        getattr(_t1891, 'global').extend(relation_ids1068)
        result1072 = _t1891
        self.record_span(span_start1071, "Algorithm")
        return result1072

    def parse_script(self) -> logic_pb2.Script:
        span_start1077 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1073 = []
        cond1074 = self.match_lookahead_literal("(", 0)
        while cond1074:
            _t1892 = self.parse_construct()
            item1075 = _t1892
            xs1073.append(item1075)
            cond1074 = self.match_lookahead_literal("(", 0)
        constructs1076 = xs1073
        self.consume_literal(")")
        _t1893 = logic_pb2.Script(constructs=constructs1076)
        result1078 = _t1893
        self.record_span(span_start1077, "Script")
        return result1078

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1082 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1895 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1896 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1897 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1898 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1899 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1900 = 1
                                else:
                                    _t1900 = -1
                                _t1899 = _t1900
                            _t1898 = _t1899
                        _t1897 = _t1898
                    _t1896 = _t1897
                _t1895 = _t1896
            _t1894 = _t1895
        else:
            _t1894 = -1
        prediction1079 = _t1894
        if prediction1079 == 1:
            _t1902 = self.parse_instruction()
            instruction1081 = _t1902
            _t1903 = logic_pb2.Construct(instruction=instruction1081)
            _t1901 = _t1903
        else:
            if prediction1079 == 0:
                _t1905 = self.parse_loop()
                loop1080 = _t1905
                _t1906 = logic_pb2.Construct(loop=loop1080)
                _t1904 = _t1906
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1901 = _t1904
        result1083 = _t1901
        self.record_span(span_start1082, "Construct")
        return result1083

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1087 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1907 = self.parse_init()
        init1084 = _t1907
        _t1908 = self.parse_script()
        script1085 = _t1908
        if self.match_lookahead_literal("(", 0):
            _t1910 = self.parse_attrs()
            _t1909 = _t1910
        else:
            _t1909 = None
        attrs1086 = _t1909
        self.consume_literal(")")
        _t1911 = logic_pb2.Loop(init=init1084, body=script1085, attrs=(attrs1086 if attrs1086 is not None else []))
        result1088 = _t1911
        self.record_span(span_start1087, "Loop")
        return result1088
>>>>>>> origin/main

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
<<<<<<< HEAD
        xs1055 = []
        cond1056 = self.match_lookahead_literal("(", 0)
        while cond1056:
            _t1844 = self.parse_instruction()
            item1057 = _t1844
            xs1055.append(item1057)
            cond1056 = self.match_lookahead_literal("(", 0)
        instructions1058 = xs1055
        self.consume_literal(")")
        return instructions1058

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1065 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1846 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1847 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1848 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1849 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1850 = 0
                            else:
                                _t1850 = -1
                            _t1849 = _t1850
                        _t1848 = _t1849
                    _t1847 = _t1848
                _t1846 = _t1847
            _t1845 = _t1846
        else:
            _t1845 = -1
        prediction1059 = _t1845
        if prediction1059 == 4:
            _t1852 = self.parse_monus_def()
            monus_def1064 = _t1852
            _t1853 = logic_pb2.Instruction(monus_def=monus_def1064)
            _t1851 = _t1853
        else:
            if prediction1059 == 3:
                _t1855 = self.parse_monoid_def()
                monoid_def1063 = _t1855
                _t1856 = logic_pb2.Instruction(monoid_def=monoid_def1063)
                _t1854 = _t1856
            else:
                if prediction1059 == 2:
                    _t1858 = self.parse_break()
                    break1062 = _t1858
                    _t1859 = logic_pb2.Instruction()
                    getattr(_t1859, 'break').CopyFrom(break1062)
                    _t1857 = _t1859
                else:
                    if prediction1059 == 1:
                        _t1861 = self.parse_upsert()
                        upsert1061 = _t1861
                        _t1862 = logic_pb2.Instruction(upsert=upsert1061)
                        _t1860 = _t1862
                    else:
                        if prediction1059 == 0:
                            _t1864 = self.parse_assign()
                            assign1060 = _t1864
                            _t1865 = logic_pb2.Instruction(assign=assign1060)
                            _t1863 = _t1865
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1860 = _t1863
                    _t1857 = _t1860
                _t1854 = _t1857
            _t1851 = _t1854
        result1066 = _t1851
        self.record_span(span_start1065, "Instruction")
        return result1066

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1070 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1866 = self.parse_relation_id()
        relation_id1067 = _t1866
        _t1867 = self.parse_abstraction()
        abstraction1068 = _t1867
        if self.match_lookahead_literal("(", 0):
            _t1869 = self.parse_attrs()
            _t1868 = _t1869
        else:
            _t1868 = None
        attrs1069 = _t1868
        self.consume_literal(")")
        _t1870 = logic_pb2.Assign(name=relation_id1067, body=abstraction1068, attrs=(attrs1069 if attrs1069 is not None else []))
        result1071 = _t1870
        self.record_span(span_start1070, "Assign")
        return result1071

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1075 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1871 = self.parse_relation_id()
        relation_id1072 = _t1871
        _t1872 = self.parse_abstraction_with_arity()
        abstraction_with_arity1073 = _t1872
        if self.match_lookahead_literal("(", 0):
            _t1874 = self.parse_attrs()
            _t1873 = _t1874
        else:
            _t1873 = None
        attrs1074 = _t1873
        self.consume_literal(")")
        _t1875 = logic_pb2.Upsert(name=relation_id1072, body=abstraction_with_arity1073[0], attrs=(attrs1074 if attrs1074 is not None else []), value_arity=abstraction_with_arity1073[1])
        result1076 = _t1875
        self.record_span(span_start1075, "Upsert")
        return result1076

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1876 = self.parse_bindings()
        bindings1077 = _t1876
        _t1877 = self.parse_formula()
        formula1078 = _t1877
        self.consume_literal(")")
        _t1878 = logic_pb2.Abstraction(vars=(list(bindings1077[0]) + list(bindings1077[1] if bindings1077[1] is not None else [])), value=formula1078)
        return (_t1878, len(bindings1077[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1082 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1879 = self.parse_relation_id()
        relation_id1079 = _t1879
        _t1880 = self.parse_abstraction()
        abstraction1080 = _t1880
=======
        xs1089 = []
        cond1090 = self.match_lookahead_literal("(", 0)
        while cond1090:
            _t1912 = self.parse_instruction()
            item1091 = _t1912
            xs1089.append(item1091)
            cond1090 = self.match_lookahead_literal("(", 0)
        instructions1092 = xs1089
        self.consume_literal(")")
        return instructions1092

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1099 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1914 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1915 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1916 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1917 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1918 = 0
                            else:
                                _t1918 = -1
                            _t1917 = _t1918
                        _t1916 = _t1917
                    _t1915 = _t1916
                _t1914 = _t1915
            _t1913 = _t1914
        else:
            _t1913 = -1
        prediction1093 = _t1913
        if prediction1093 == 4:
            _t1920 = self.parse_monus_def()
            monus_def1098 = _t1920
            _t1921 = logic_pb2.Instruction(monus_def=monus_def1098)
            _t1919 = _t1921
        else:
            if prediction1093 == 3:
                _t1923 = self.parse_monoid_def()
                monoid_def1097 = _t1923
                _t1924 = logic_pb2.Instruction(monoid_def=monoid_def1097)
                _t1922 = _t1924
            else:
                if prediction1093 == 2:
                    _t1926 = self.parse_break()
                    break1096 = _t1926
                    _t1927 = logic_pb2.Instruction()
                    getattr(_t1927, 'break').CopyFrom(break1096)
                    _t1925 = _t1927
                else:
                    if prediction1093 == 1:
                        _t1929 = self.parse_upsert()
                        upsert1095 = _t1929
                        _t1930 = logic_pb2.Instruction(upsert=upsert1095)
                        _t1928 = _t1930
                    else:
                        if prediction1093 == 0:
                            _t1932 = self.parse_assign()
                            assign1094 = _t1932
                            _t1933 = logic_pb2.Instruction(assign=assign1094)
                            _t1931 = _t1933
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1928 = _t1931
                    _t1925 = _t1928
                _t1922 = _t1925
            _t1919 = _t1922
        result1100 = _t1919
        self.record_span(span_start1099, "Instruction")
        return result1100

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1104 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1934 = self.parse_relation_id()
        relation_id1101 = _t1934
        _t1935 = self.parse_abstraction()
        abstraction1102 = _t1935
        if self.match_lookahead_literal("(", 0):
            _t1937 = self.parse_attrs()
            _t1936 = _t1937
        else:
            _t1936 = None
        attrs1103 = _t1936
        self.consume_literal(")")
        _t1938 = logic_pb2.Assign(name=relation_id1101, body=abstraction1102, attrs=(attrs1103 if attrs1103 is not None else []))
        result1105 = _t1938
        self.record_span(span_start1104, "Assign")
        return result1105

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1109 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1939 = self.parse_relation_id()
        relation_id1106 = _t1939
        _t1940 = self.parse_abstraction_with_arity()
        abstraction_with_arity1107 = _t1940
        if self.match_lookahead_literal("(", 0):
            _t1942 = self.parse_attrs()
            _t1941 = _t1942
        else:
            _t1941 = None
        attrs1108 = _t1941
        self.consume_literal(")")
        _t1943 = logic_pb2.Upsert(name=relation_id1106, body=abstraction_with_arity1107[0], attrs=(attrs1108 if attrs1108 is not None else []), value_arity=abstraction_with_arity1107[1])
        result1110 = _t1943
        self.record_span(span_start1109, "Upsert")
        return result1110

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1944 = self.parse_bindings()
        bindings1111 = _t1944
        _t1945 = self.parse_formula()
        formula1112 = _t1945
        self.consume_literal(")")
        _t1946 = logic_pb2.Abstraction(vars=(list(bindings1111[0]) + list(bindings1111[1] if bindings1111[1] is not None else [])), value=formula1112)
        return (_t1946, len(bindings1111[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1116 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1947 = self.parse_relation_id()
        relation_id1113 = _t1947
        _t1948 = self.parse_abstraction()
        abstraction1114 = _t1948
        if self.match_lookahead_literal("(", 0):
            _t1950 = self.parse_attrs()
            _t1949 = _t1950
        else:
            _t1949 = None
        attrs1115 = _t1949
        self.consume_literal(")")
        _t1951 = logic_pb2.Break(name=relation_id1113, body=abstraction1114, attrs=(attrs1115 if attrs1115 is not None else []))
        result1117 = _t1951
        self.record_span(span_start1116, "Break")
        return result1117

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1122 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1952 = self.parse_monoid()
        monoid1118 = _t1952
        _t1953 = self.parse_relation_id()
        relation_id1119 = _t1953
        _t1954 = self.parse_abstraction_with_arity()
        abstraction_with_arity1120 = _t1954
>>>>>>> origin/main
        if self.match_lookahead_literal("(", 0):
            _t1956 = self.parse_attrs()
            _t1955 = _t1956
        else:
<<<<<<< HEAD
            _t1881 = None
        attrs1081 = _t1881
        self.consume_literal(")")
        _t1883 = logic_pb2.Break(name=relation_id1079, body=abstraction1080, attrs=(attrs1081 if attrs1081 is not None else []))
        result1083 = _t1883
        self.record_span(span_start1082, "Break")
        return result1083

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1088 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1884 = self.parse_monoid()
        monoid1084 = _t1884
        _t1885 = self.parse_relation_id()
        relation_id1085 = _t1885
        _t1886 = self.parse_abstraction_with_arity()
        abstraction_with_arity1086 = _t1886
        if self.match_lookahead_literal("(", 0):
            _t1888 = self.parse_attrs()
            _t1887 = _t1888
        else:
            _t1887 = None
        attrs1087 = _t1887
        self.consume_literal(")")
        _t1889 = logic_pb2.MonoidDef(monoid=monoid1084, name=relation_id1085, body=abstraction_with_arity1086[0], attrs=(attrs1087 if attrs1087 is not None else []), value_arity=abstraction_with_arity1086[1])
        result1089 = _t1889
        self.record_span(span_start1088, "MonoidDef")
        return result1089

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1095 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1891 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1892 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1893 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1894 = 2
                        else:
                            _t1894 = -1
                        _t1893 = _t1894
                    _t1892 = _t1893
                _t1891 = _t1892
            _t1890 = _t1891
        else:
            _t1890 = -1
        prediction1090 = _t1890
        if prediction1090 == 3:
            _t1896 = self.parse_sum_monoid()
            sum_monoid1094 = _t1896
            _t1897 = logic_pb2.Monoid(sum_monoid=sum_monoid1094)
            _t1895 = _t1897
        else:
            if prediction1090 == 2:
                _t1899 = self.parse_max_monoid()
                max_monoid1093 = _t1899
                _t1900 = logic_pb2.Monoid(max_monoid=max_monoid1093)
                _t1898 = _t1900
            else:
                if prediction1090 == 1:
                    _t1902 = self.parse_min_monoid()
                    min_monoid1092 = _t1902
                    _t1903 = logic_pb2.Monoid(min_monoid=min_monoid1092)
                    _t1901 = _t1903
                else:
                    if prediction1090 == 0:
                        _t1905 = self.parse_or_monoid()
                        or_monoid1091 = _t1905
                        _t1906 = logic_pb2.Monoid(or_monoid=or_monoid1091)
                        _t1904 = _t1906
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1901 = _t1904
                _t1898 = _t1901
            _t1895 = _t1898
        result1096 = _t1895
        self.record_span(span_start1095, "Monoid")
        return result1096

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1097 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1907 = logic_pb2.OrMonoid()
        result1098 = _t1907
        self.record_span(span_start1097, "OrMonoid")
        return result1098

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1100 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1908 = self.parse_type()
        type1099 = _t1908
        self.consume_literal(")")
        _t1909 = logic_pb2.MinMonoid(type=type1099)
        result1101 = _t1909
        self.record_span(span_start1100, "MinMonoid")
        return result1101

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1103 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1910 = self.parse_type()
        type1102 = _t1910
        self.consume_literal(")")
        _t1911 = logic_pb2.MaxMonoid(type=type1102)
        result1104 = _t1911
        self.record_span(span_start1103, "MaxMonoid")
        return result1104
=======
            _t1955 = None
        attrs1121 = _t1955
        self.consume_literal(")")
        _t1957 = logic_pb2.MonoidDef(monoid=monoid1118, name=relation_id1119, body=abstraction_with_arity1120[0], attrs=(attrs1121 if attrs1121 is not None else []), value_arity=abstraction_with_arity1120[1])
        result1123 = _t1957
        self.record_span(span_start1122, "MonoidDef")
        return result1123

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1129 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1959 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1960 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1961 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1962 = 2
                        else:
                            _t1962 = -1
                        _t1961 = _t1962
                    _t1960 = _t1961
                _t1959 = _t1960
            _t1958 = _t1959
        else:
            _t1958 = -1
        prediction1124 = _t1958
        if prediction1124 == 3:
            _t1964 = self.parse_sum_monoid()
            sum_monoid1128 = _t1964
            _t1965 = logic_pb2.Monoid(sum_monoid=sum_monoid1128)
            _t1963 = _t1965
        else:
            if prediction1124 == 2:
                _t1967 = self.parse_max_monoid()
                max_monoid1127 = _t1967
                _t1968 = logic_pb2.Monoid(max_monoid=max_monoid1127)
                _t1966 = _t1968
            else:
                if prediction1124 == 1:
                    _t1970 = self.parse_min_monoid()
                    min_monoid1126 = _t1970
                    _t1971 = logic_pb2.Monoid(min_monoid=min_monoid1126)
                    _t1969 = _t1971
                else:
                    if prediction1124 == 0:
                        _t1973 = self.parse_or_monoid()
                        or_monoid1125 = _t1973
                        _t1974 = logic_pb2.Monoid(or_monoid=or_monoid1125)
                        _t1972 = _t1974
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1969 = _t1972
                _t1966 = _t1969
            _t1963 = _t1966
        result1130 = _t1963
        self.record_span(span_start1129, "Monoid")
        return result1130

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1131 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1975 = logic_pb2.OrMonoid()
        result1132 = _t1975
        self.record_span(span_start1131, "OrMonoid")
        return result1132

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1134 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1976 = self.parse_type()
        type1133 = _t1976
        self.consume_literal(")")
        _t1977 = logic_pb2.MinMonoid(type=type1133)
        result1135 = _t1977
        self.record_span(span_start1134, "MinMonoid")
        return result1135

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1137 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1978 = self.parse_type()
        type1136 = _t1978
        self.consume_literal(")")
        _t1979 = logic_pb2.MaxMonoid(type=type1136)
        result1138 = _t1979
        self.record_span(span_start1137, "MaxMonoid")
        return result1138

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1140 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1980 = self.parse_type()
        type1139 = _t1980
        self.consume_literal(")")
        _t1981 = logic_pb2.SumMonoid(type=type1139)
        result1141 = _t1981
        self.record_span(span_start1140, "SumMonoid")
        return result1141
>>>>>>> origin/main

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1106 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1912 = self.parse_type()
        type1105 = _t1912
        self.consume_literal(")")
        _t1913 = logic_pb2.SumMonoid(type=type1105)
        result1107 = _t1913
        self.record_span(span_start1106, "SumMonoid")
        return result1107

    def parse_monus_def(self) -> logic_pb2.MonusDef:
<<<<<<< HEAD
        span_start1112 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1914 = self.parse_monoid()
        monoid1108 = _t1914
        _t1915 = self.parse_relation_id()
        relation_id1109 = _t1915
        _t1916 = self.parse_abstraction_with_arity()
        abstraction_with_arity1110 = _t1916
        if self.match_lookahead_literal("(", 0):
            _t1918 = self.parse_attrs()
            _t1917 = _t1918
        else:
            _t1917 = None
        attrs1111 = _t1917
        self.consume_literal(")")
        _t1919 = logic_pb2.MonusDef(monoid=monoid1108, name=relation_id1109, body=abstraction_with_arity1110[0], attrs=(attrs1111 if attrs1111 is not None else []), value_arity=abstraction_with_arity1110[1])
        result1113 = _t1919
        self.record_span(span_start1112, "MonusDef")
        return result1113

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1118 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1920 = self.parse_relation_id()
        relation_id1114 = _t1920
        _t1921 = self.parse_abstraction()
        abstraction1115 = _t1921
        _t1922 = self.parse_functional_dependency_keys()
        functional_dependency_keys1116 = _t1922
        _t1923 = self.parse_functional_dependency_values()
        functional_dependency_values1117 = _t1923
        self.consume_literal(")")
        _t1924 = logic_pb2.FunctionalDependency(guard=abstraction1115, keys=functional_dependency_keys1116, values=functional_dependency_values1117)
        _t1925 = logic_pb2.Constraint(name=relation_id1114, functional_dependency=_t1924)
        result1119 = _t1925
        self.record_span(span_start1118, "Constraint")
        return result1119
=======
        span_start1146 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1982 = self.parse_monoid()
        monoid1142 = _t1982
        _t1983 = self.parse_relation_id()
        relation_id1143 = _t1983
        _t1984 = self.parse_abstraction_with_arity()
        abstraction_with_arity1144 = _t1984
        if self.match_lookahead_literal("(", 0):
            _t1986 = self.parse_attrs()
            _t1985 = _t1986
        else:
            _t1985 = None
        attrs1145 = _t1985
        self.consume_literal(")")
        _t1987 = logic_pb2.MonusDef(monoid=monoid1142, name=relation_id1143, body=abstraction_with_arity1144[0], attrs=(attrs1145 if attrs1145 is not None else []), value_arity=abstraction_with_arity1144[1])
        result1147 = _t1987
        self.record_span(span_start1146, "MonusDef")
        return result1147

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1152 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1988 = self.parse_relation_id()
        relation_id1148 = _t1988
        _t1989 = self.parse_abstraction()
        abstraction1149 = _t1989
        _t1990 = self.parse_functional_dependency_keys()
        functional_dependency_keys1150 = _t1990
        _t1991 = self.parse_functional_dependency_values()
        functional_dependency_values1151 = _t1991
        self.consume_literal(")")
        _t1992 = logic_pb2.FunctionalDependency(guard=abstraction1149, keys=functional_dependency_keys1150, values=functional_dependency_values1151)
        _t1993 = logic_pb2.Constraint(name=relation_id1148, functional_dependency=_t1992)
        result1153 = _t1993
        self.record_span(span_start1152, "Constraint")
        return result1153
>>>>>>> origin/main

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
<<<<<<< HEAD
        xs1120 = []
        cond1121 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1121:
            _t1926 = self.parse_var()
            item1122 = _t1926
            xs1120.append(item1122)
            cond1121 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1123 = xs1120
        self.consume_literal(")")
        return vars1123
=======
        xs1154 = []
        cond1155 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1155:
            _t1994 = self.parse_var()
            item1156 = _t1994
            xs1154.append(item1156)
            cond1155 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1157 = xs1154
        self.consume_literal(")")
        return vars1157
>>>>>>> origin/main

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
<<<<<<< HEAD
        xs1124 = []
        cond1125 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1125:
            _t1927 = self.parse_var()
            item1126 = _t1927
            xs1124.append(item1126)
            cond1125 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1127 = xs1124
        self.consume_literal(")")
        return vars1127

    def parse_data(self) -> logic_pb2.Data:
        span_start1133 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1929 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1930 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1931 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1932 = 1
                        else:
                            _t1932 = -1
                        _t1931 = _t1932
                    _t1930 = _t1931
                _t1929 = _t1930
            _t1928 = _t1929
        else:
            _t1928 = -1
        prediction1128 = _t1928
        if prediction1128 == 3:
            _t1934 = self.parse_iceberg_data()
            iceberg_data1132 = _t1934
            _t1935 = logic_pb2.Data(iceberg_data=iceberg_data1132)
            _t1933 = _t1935
        else:
            if prediction1128 == 2:
                _t1937 = self.parse_csv_data()
                csv_data1131 = _t1937
                _t1938 = logic_pb2.Data(csv_data=csv_data1131)
                _t1936 = _t1938
            else:
                if prediction1128 == 1:
                    _t1940 = self.parse_betree_relation()
                    betree_relation1130 = _t1940
                    _t1941 = logic_pb2.Data(betree_relation=betree_relation1130)
                    _t1939 = _t1941
                else:
                    if prediction1128 == 0:
                        _t1943 = self.parse_edb()
                        edb1129 = _t1943
                        _t1944 = logic_pb2.Data(edb=edb1129)
                        _t1942 = _t1944
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1939 = _t1942
                _t1936 = _t1939
            _t1933 = _t1936
        result1134 = _t1933
        self.record_span(span_start1133, "Data")
        return result1134

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1138 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1945 = self.parse_relation_id()
        relation_id1135 = _t1945
        _t1946 = self.parse_edb_path()
        edb_path1136 = _t1946
        _t1947 = self.parse_edb_types()
        edb_types1137 = _t1947
        self.consume_literal(")")
        _t1948 = logic_pb2.EDB(target_id=relation_id1135, path=edb_path1136, types=edb_types1137)
        result1139 = _t1948
        self.record_span(span_start1138, "EDB")
        return result1139

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1140 = []
        cond1141 = self.match_lookahead_terminal("STRING", 0)
        while cond1141:
            item1142 = self.consume_terminal("STRING")
            xs1140.append(item1142)
            cond1141 = self.match_lookahead_terminal("STRING", 0)
        strings1143 = xs1140
        self.consume_literal("]")
        return strings1143

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1144 = []
        cond1145 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1145:
            _t1949 = self.parse_type()
            item1146 = _t1949
            xs1144.append(item1146)
            cond1145 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1147 = xs1144
        self.consume_literal("]")
        return types1147

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1150 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1950 = self.parse_relation_id()
        relation_id1148 = _t1950
        _t1951 = self.parse_betree_info()
        betree_info1149 = _t1951
        self.consume_literal(")")
        _t1952 = logic_pb2.BeTreeRelation(name=relation_id1148, relation_info=betree_info1149)
        result1151 = _t1952
        self.record_span(span_start1150, "BeTreeRelation")
        return result1151

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1155 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1953 = self.parse_betree_info_key_types()
        betree_info_key_types1152 = _t1953
        _t1954 = self.parse_betree_info_value_types()
        betree_info_value_types1153 = _t1954
        _t1955 = self.parse_config_dict()
        config_dict1154 = _t1955
        self.consume_literal(")")
        _t1956 = self.construct_betree_info(betree_info_key_types1152, betree_info_value_types1153, config_dict1154)
        result1156 = _t1956
        self.record_span(span_start1155, "BeTreeInfo")
        return result1156
=======
        xs1158 = []
        cond1159 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1159:
            _t1995 = self.parse_var()
            item1160 = _t1995
            xs1158.append(item1160)
            cond1159 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1161 = xs1158
        self.consume_literal(")")
        return vars1161

    def parse_data(self) -> logic_pb2.Data:
        span_start1167 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1997 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1998 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1999 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t2000 = 1
                        else:
                            _t2000 = -1
                        _t1999 = _t2000
                    _t1998 = _t1999
                _t1997 = _t1998
            _t1996 = _t1997
        else:
            _t1996 = -1
        prediction1162 = _t1996
        if prediction1162 == 3:
            _t2002 = self.parse_iceberg_data()
            iceberg_data1166 = _t2002
            _t2003 = logic_pb2.Data(iceberg_data=iceberg_data1166)
            _t2001 = _t2003
        else:
            if prediction1162 == 2:
                _t2005 = self.parse_csv_data()
                csv_data1165 = _t2005
                _t2006 = logic_pb2.Data(csv_data=csv_data1165)
                _t2004 = _t2006
            else:
                if prediction1162 == 1:
                    _t2008 = self.parse_betree_relation()
                    betree_relation1164 = _t2008
                    _t2009 = logic_pb2.Data(betree_relation=betree_relation1164)
                    _t2007 = _t2009
                else:
                    if prediction1162 == 0:
                        _t2011 = self.parse_edb()
                        edb1163 = _t2011
                        _t2012 = logic_pb2.Data(edb=edb1163)
                        _t2010 = _t2012
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t2007 = _t2010
                _t2004 = _t2007
            _t2001 = _t2004
        result1168 = _t2001
        self.record_span(span_start1167, "Data")
        return result1168

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1172 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t2013 = self.parse_relation_id()
        relation_id1169 = _t2013
        _t2014 = self.parse_edb_path()
        edb_path1170 = _t2014
        _t2015 = self.parse_edb_types()
        edb_types1171 = _t2015
        self.consume_literal(")")
        _t2016 = logic_pb2.EDB(target_id=relation_id1169, path=edb_path1170, types=edb_types1171)
        result1173 = _t2016
        self.record_span(span_start1172, "EDB")
        return result1173

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1174 = []
        cond1175 = self.match_lookahead_terminal("STRING", 0)
        while cond1175:
            item1176 = self.consume_terminal("STRING")
            xs1174.append(item1176)
            cond1175 = self.match_lookahead_terminal("STRING", 0)
        strings1177 = xs1174
        self.consume_literal("]")
        return strings1177

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1178 = []
        cond1179 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1179:
            _t2017 = self.parse_type()
            item1180 = _t2017
            xs1178.append(item1180)
            cond1179 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1181 = xs1178
        self.consume_literal("]")
        return types1181

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1184 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t2018 = self.parse_relation_id()
        relation_id1182 = _t2018
        _t2019 = self.parse_betree_info()
        betree_info1183 = _t2019
        self.consume_literal(")")
        _t2020 = logic_pb2.BeTreeRelation(name=relation_id1182, relation_info=betree_info1183)
        result1185 = _t2020
        self.record_span(span_start1184, "BeTreeRelation")
        return result1185

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1189 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t2021 = self.parse_betree_info_key_types()
        betree_info_key_types1186 = _t2021
        _t2022 = self.parse_betree_info_value_types()
        betree_info_value_types1187 = _t2022
        _t2023 = self.parse_config_dict()
        config_dict1188 = _t2023
        self.consume_literal(")")
        _t2024 = self.construct_betree_info(betree_info_key_types1186, betree_info_value_types1187, config_dict1188)
        result1190 = _t2024
        self.record_span(span_start1189, "BeTreeInfo")
        return result1190
>>>>>>> origin/main

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
<<<<<<< HEAD
        xs1157 = []
        cond1158 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1158:
            _t1957 = self.parse_type()
            item1159 = _t1957
            xs1157.append(item1159)
            cond1158 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1160 = xs1157
        self.consume_literal(")")
        return types1160
=======
        xs1191 = []
        cond1192 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1192:
            _t2025 = self.parse_type()
            item1193 = _t2025
            xs1191.append(item1193)
            cond1192 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1194 = xs1191
        self.consume_literal(")")
        return types1194
>>>>>>> origin/main

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
<<<<<<< HEAD
        xs1161 = []
        cond1162 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1162:
            _t1958 = self.parse_type()
            item1163 = _t1958
            xs1161.append(item1163)
            cond1162 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1164 = xs1161
        self.consume_literal(")")
        return types1164

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1169 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1959 = self.parse_csvlocator()
        csvlocator1165 = _t1959
        _t1960 = self.parse_csv_config()
        csv_config1166 = _t1960
        _t1961 = self.parse_gnf_columns()
        gnf_columns1167 = _t1961
        _t1962 = self.parse_csv_asof()
        csv_asof1168 = _t1962
        self.consume_literal(")")
        _t1963 = logic_pb2.CSVData(locator=csvlocator1165, config=csv_config1166, columns=gnf_columns1167, asof=csv_asof1168)
        result1170 = _t1963
        self.record_span(span_start1169, "CSVData")
        return result1170

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1173 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1965 = self.parse_csv_locator_paths()
            _t1964 = _t1965
        else:
            _t1964 = None
        csv_locator_paths1171 = _t1964
        if self.match_lookahead_literal("(", 0):
            _t1967 = self.parse_csv_locator_inline_data()
            _t1966 = _t1967
        else:
            _t1966 = None
        csv_locator_inline_data1172 = _t1966
        self.consume_literal(")")
        _t1968 = logic_pb2.CSVLocator(paths=(csv_locator_paths1171 if csv_locator_paths1171 is not None else []), inline_data=(csv_locator_inline_data1172 if csv_locator_inline_data1172 is not None else "").encode())
        result1174 = _t1968
        self.record_span(span_start1173, "CSVLocator")
        return result1174
=======
        xs1195 = []
        cond1196 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1196:
            _t2026 = self.parse_type()
            item1197 = _t2026
            xs1195.append(item1197)
            cond1196 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1198 = xs1195
        self.consume_literal(")")
        return types1198

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1204 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t2027 = self.parse_csvlocator()
        csvlocator1199 = _t2027
        _t2028 = self.parse_csv_config()
        csv_config1200 = _t2028
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("columns", 1)):
            _t2030 = self.parse_gnf_columns()
            _t2029 = _t2030
        else:
            _t2029 = None
        gnf_columns1201 = _t2029
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("relations", 1)):
            _t2032 = self.parse_target_relations()
            _t2031 = _t2032
        else:
            _t2031 = None
        target_relations1202 = _t2031
        _t2033 = self.parse_csv_asof()
        csv_asof1203 = _t2033
        self.consume_literal(")")
        _t2034 = self.construct_csv_data(csvlocator1199, csv_config1200, gnf_columns1201, target_relations1202, csv_asof1203)
        result1205 = _t2034
        self.record_span(span_start1204, "CSVData")
        return result1205

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1208 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t2036 = self.parse_csv_locator_paths()
            _t2035 = _t2036
        else:
            _t2035 = None
        csv_locator_paths1206 = _t2035
        if self.match_lookahead_literal("(", 0):
            _t2038 = self.parse_csv_locator_inline_data()
            _t2037 = _t2038
        else:
            _t2037 = None
        csv_locator_inline_data1207 = _t2037
        self.consume_literal(")")
        _t2039 = logic_pb2.CSVLocator(paths=(csv_locator_paths1206 if csv_locator_paths1206 is not None else []), inline_data=(csv_locator_inline_data1207 if csv_locator_inline_data1207 is not None else "").encode())
        result1209 = _t2039
        self.record_span(span_start1208, "CSVLocator")
        return result1209
>>>>>>> origin/main

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
<<<<<<< HEAD
        xs1175 = []
        cond1176 = self.match_lookahead_terminal("STRING", 0)
        while cond1176:
            item1177 = self.consume_terminal("STRING")
            xs1175.append(item1177)
            cond1176 = self.match_lookahead_terminal("STRING", 0)
        strings1178 = xs1175
        self.consume_literal(")")
        return strings1178
=======
        xs1210 = []
        cond1211 = self.match_lookahead_terminal("STRING", 0)
        while cond1211:
            item1212 = self.consume_terminal("STRING")
            xs1210.append(item1212)
            cond1211 = self.match_lookahead_terminal("STRING", 0)
        strings1213 = xs1210
        self.consume_literal(")")
        return strings1213
>>>>>>> origin/main

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
<<<<<<< HEAD
        formatted_string1179 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return formatted_string1179

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1182 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1969 = self.parse_config_dict()
        config_dict1180 = _t1969
        if self.match_lookahead_literal("(", 0):
            _t1971 = self.parse__storage_integration()
            _t1970 = _t1971
        else:
            _t1970 = None
        _storage_integration1181 = _t1970
        self.consume_literal(")")
        _t1972 = self.construct_csv_config(config_dict1180, _storage_integration1181)
        result1183 = _t1972
        self.record_span(span_start1182, "CSVConfig")
        return result1183
=======
        formatted_string1214 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return formatted_string1214

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1217 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t2040 = self.parse_config_dict()
        config_dict1215 = _t2040
        if self.match_lookahead_literal("(", 0):
            _t2042 = self.parse__storage_integration()
            _t2041 = _t2042
        else:
            _t2041 = None
        _storage_integration1216 = _t2041
        self.consume_literal(")")
        _t2043 = self.construct_csv_config(config_dict1215, _storage_integration1216)
        result1218 = _t2043
        self.record_span(span_start1217, "CSVConfig")
        return result1218
>>>>>>> origin/main

    def parse__storage_integration(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("(")
        self.consume_literal("storage_integration")
<<<<<<< HEAD
        _t1973 = self.parse_config_dict()
        config_dict1184 = _t1973
        self.consume_literal(")")
        return config_dict1184
=======
        _t2044 = self.parse_config_dict()
        config_dict1219 = _t2044
        self.consume_literal(")")
        return config_dict1219
>>>>>>> origin/main

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
<<<<<<< HEAD
        xs1185 = []
        cond1186 = self.match_lookahead_literal("(", 0)
        while cond1186:
            _t1974 = self.parse_gnf_column()
            item1187 = _t1974
            xs1185.append(item1187)
            cond1186 = self.match_lookahead_literal("(", 0)
        gnf_columns1188 = xs1185
        self.consume_literal(")")
        return gnf_columns1188

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1195 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1975 = self.parse_gnf_column_path()
        gnf_column_path1189 = _t1975
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1977 = self.parse_relation_id()
            _t1976 = _t1977
        else:
            _t1976 = None
        relation_id1190 = _t1976
        self.consume_literal("[")
        xs1191 = []
        cond1192 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1192:
            _t1978 = self.parse_type()
            item1193 = _t1978
            xs1191.append(item1193)
            cond1192 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1194 = xs1191
        self.consume_literal("]")
        self.consume_literal(")")
        _t1979 = logic_pb2.GNFColumn(column_path=gnf_column_path1189, target_id=relation_id1190, types=types1194)
        result1196 = _t1979
        self.record_span(span_start1195, "GNFColumn")
        return result1196

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1980 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1981 = 0
            else:
                _t1981 = -1
            _t1980 = _t1981
        prediction1197 = _t1980
        if prediction1197 == 1:
            self.consume_literal("[")
            xs1199 = []
            cond1200 = self.match_lookahead_terminal("STRING", 0)
            while cond1200:
                item1201 = self.consume_terminal("STRING")
                xs1199.append(item1201)
                cond1200 = self.match_lookahead_terminal("STRING", 0)
            strings1202 = xs1199
            self.consume_literal("]")
            _t1982 = strings1202
        else:
            if prediction1197 == 0:
                string1198 = self.consume_terminal("STRING")
                _t1983 = [string1198]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1982 = _t1983
        return _t1982
=======
        xs1220 = []
        cond1221 = self.match_lookahead_literal("(", 0)
        while cond1221:
            _t2045 = self.parse_gnf_column()
            item1222 = _t2045
            xs1220.append(item1222)
            cond1221 = self.match_lookahead_literal("(", 0)
        gnf_columns1223 = xs1220
        self.consume_literal(")")
        return gnf_columns1223

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1230 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t2046 = self.parse_gnf_column_path()
        gnf_column_path1224 = _t2046
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t2048 = self.parse_relation_id()
            _t2047 = _t2048
        else:
            _t2047 = None
        relation_id1225 = _t2047
        self.consume_literal("[")
        xs1226 = []
        cond1227 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1227:
            _t2049 = self.parse_type()
            item1228 = _t2049
            xs1226.append(item1228)
            cond1227 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1229 = xs1226
        self.consume_literal("]")
        self.consume_literal(")")
        _t2050 = logic_pb2.GNFColumn(column_path=gnf_column_path1224, target_id=relation_id1225, types=types1229)
        result1231 = _t2050
        self.record_span(span_start1230, "GNFColumn")
        return result1231

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t2051 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t2052 = 0
            else:
                _t2052 = -1
            _t2051 = _t2052
        prediction1232 = _t2051
        if prediction1232 == 1:
            self.consume_literal("[")
            xs1234 = []
            cond1235 = self.match_lookahead_terminal("STRING", 0)
            while cond1235:
                item1236 = self.consume_terminal("STRING")
                xs1234.append(item1236)
                cond1235 = self.match_lookahead_terminal("STRING", 0)
            strings1237 = xs1234
            self.consume_literal("]")
            _t2053 = strings1237
        else:
            if prediction1232 == 0:
                string1233 = self.consume_terminal("STRING")
                _t2054 = [string1233]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2053 = _t2054
        return _t2053

    def parse_target_relations(self) -> logic_pb2.TargetRelations:
        span_start1240 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relations")
        _t2055 = self.parse_relation_keys()
        relation_keys1238 = _t2055
        _t2056 = self.parse_relation_body()
        relation_body1239 = _t2056
        self.consume_literal(")")
        _t2057 = self.construct_relations(relation_keys1238, relation_body1239)
        result1241 = _t2057
        self.record_span(span_start1240, "TargetRelations")
        return result1241

    def parse_relation_keys(self) -> Sequence[logic_pb2.NamedColumn]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1242 = []
        cond1243 = self.match_lookahead_literal("(", 0)
        while cond1243:
            _t2058 = self.parse_named_column()
            item1244 = _t2058
            xs1242.append(item1244)
            cond1243 = self.match_lookahead_literal("(", 0)
        named_columns1245 = xs1242
        self.consume_literal(")")
        return named_columns1245

    def parse_named_column(self) -> logic_pb2.NamedColumn:
        span_start1248 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1246 = self.consume_terminal("STRING")
        _t2059 = self.parse_type()
        type1247 = _t2059
        self.consume_literal(")")
        _t2060 = logic_pb2.NamedColumn(name=string1246, type=type1247)
        result1249 = _t2060
        self.record_span(span_start1248, "NamedColumn")
        return result1249

    def parse_relation_body(self) -> logic_pb2.TargetRelations:
        span_start1254 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("relation", 1):
                _t2062 = 0
            else:
                if self.match_lookahead_literal("inserts", 1):
                    _t2063 = 1
                else:
                    _t2063 = 0
                _t2062 = _t2063
            _t2061 = _t2062
        else:
            _t2061 = 0
        prediction1250 = _t2061
        if prediction1250 == 1:
            _t2065 = self.parse_cdc_inserts()
            cdc_inserts1252 = _t2065
            _t2066 = self.parse_cdc_deletes()
            cdc_deletes1253 = _t2066
            _t2067 = self.construct_cdc_relations(cdc_inserts1252, cdc_deletes1253)
            _t2064 = _t2067
        else:
            if prediction1250 == 0:
                _t2069 = self.parse_non_cdc_relations()
                non_cdc_relations1251 = _t2069
                _t2070 = self.construct_non_cdc_relations(non_cdc_relations1251)
                _t2068 = _t2070
            else:
                raise ParseError("Unexpected token in relation_body" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2064 = _t2068
        result1255 = _t2064
        self.record_span(span_start1254, "TargetRelations")
        return result1255

    def parse_non_cdc_relations(self) -> Sequence[logic_pb2.TargetRelation]:
        xs1256 = []
        cond1257 = self.match_lookahead_literal("(", 0)
        while cond1257:
            _t2071 = self.parse_target_relation()
            item1258 = _t2071
            xs1256.append(item1258)
            cond1257 = self.match_lookahead_literal("(", 0)
        return xs1256

    def parse_target_relation(self) -> logic_pb2.TargetRelation:
        span_start1264 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relation")
        _t2072 = self.parse_relation_id()
        relation_id1259 = _t2072
        xs1260 = []
        cond1261 = self.match_lookahead_literal("(", 0)
        while cond1261:
            _t2073 = self.parse_named_column()
            item1262 = _t2073
            xs1260.append(item1262)
            cond1261 = self.match_lookahead_literal("(", 0)
        named_columns1263 = xs1260
        self.consume_literal(")")
        _t2074 = logic_pb2.TargetRelation(target_id=relation_id1259, values=named_columns1263)
        result1265 = _t2074
        self.record_span(span_start1264, "TargetRelation")
        return result1265

    def parse_cdc_inserts(self) -> Sequence[logic_pb2.TargetRelation]:
        self.consume_literal("(")
        self.consume_literal("inserts")
        xs1266 = []
        cond1267 = self.match_lookahead_literal("(", 0)
        while cond1267:
            _t2075 = self.parse_target_relation()
            item1268 = _t2075
            xs1266.append(item1268)
            cond1267 = self.match_lookahead_literal("(", 0)
        target_relations1269 = xs1266
        self.consume_literal(")")
        return target_relations1269

    def parse_cdc_deletes(self) -> Sequence[logic_pb2.TargetRelation]:
        self.consume_literal("(")
        self.consume_literal("deletes")
        xs1270 = []
        cond1271 = self.match_lookahead_literal("(", 0)
        while cond1271:
            _t2076 = self.parse_target_relation()
            item1272 = _t2076
            xs1270.append(item1272)
            cond1271 = self.match_lookahead_literal("(", 0)
        target_relations1273 = xs1270
        self.consume_literal(")")
        return target_relations1273
>>>>>>> origin/main

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
<<<<<<< HEAD
        string1203 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1203

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1210 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1984 = self.parse_iceberg_locator()
        iceberg_locator1204 = _t1984
        _t1985 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1205 = _t1985
        _t1986 = self.parse_gnf_columns()
        gnf_columns1206 = _t1986
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t1988 = self.parse_iceberg_from_snapshot()
            _t1987 = _t1988
        else:
            _t1987 = None
        iceberg_from_snapshot1207 = _t1987
        if self.match_lookahead_literal("(", 0):
            _t1990 = self.parse_iceberg_to_snapshot()
            _t1989 = _t1990
        else:
            _t1989 = None
        iceberg_to_snapshot1208 = _t1989
        _t1991 = self.parse_boolean_value()
        boolean_value1209 = _t1991
        self.consume_literal(")")
        _t1992 = self.construct_iceberg_data(iceberg_locator1204, iceberg_catalog_config1205, gnf_columns1206, iceberg_from_snapshot1207, iceberg_to_snapshot1208, boolean_value1209)
        result1211 = _t1992
        self.record_span(span_start1210, "IcebergData")
        return result1211

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1215 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t1993 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1212 = _t1993
        _t1994 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1213 = _t1994
        _t1995 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1214 = _t1995
        self.consume_literal(")")
        _t1996 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1212, namespace=iceberg_locator_namespace1213, warehouse=iceberg_locator_warehouse1214)
        result1216 = _t1996
        self.record_span(span_start1215, "IcebergLocator")
        return result1216
=======
        string1274 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1274

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1281 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t2077 = self.parse_iceberg_locator()
        iceberg_locator1275 = _t2077
        _t2078 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1276 = _t2078
        _t2079 = self.parse_gnf_columns()
        gnf_columns1277 = _t2079
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t2081 = self.parse_iceberg_from_snapshot()
            _t2080 = _t2081
        else:
            _t2080 = None
        iceberg_from_snapshot1278 = _t2080
        if self.match_lookahead_literal("(", 0):
            _t2083 = self.parse_iceberg_to_snapshot()
            _t2082 = _t2083
        else:
            _t2082 = None
        iceberg_to_snapshot1279 = _t2082
        _t2084 = self.parse_boolean_value()
        boolean_value1280 = _t2084
        self.consume_literal(")")
        _t2085 = self.construct_iceberg_data(iceberg_locator1275, iceberg_catalog_config1276, gnf_columns1277, iceberg_from_snapshot1278, iceberg_to_snapshot1279, boolean_value1280)
        result1282 = _t2085
        self.record_span(span_start1281, "IcebergData")
        return result1282

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1286 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t2086 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1283 = _t2086
        _t2087 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1284 = _t2087
        _t2088 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1285 = _t2088
        self.consume_literal(")")
        _t2089 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1283, namespace=iceberg_locator_namespace1284, warehouse=iceberg_locator_warehouse1285)
        result1287 = _t2089
        self.record_span(span_start1286, "IcebergLocator")
        return result1287
>>>>>>> origin/main

    def parse_iceberg_locator_table_name(self) -> str:
        self.consume_literal("(")
        self.consume_literal("table_name")
<<<<<<< HEAD
        string1217 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1217
=======
        string1288 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1288
>>>>>>> origin/main

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
<<<<<<< HEAD
        xs1218 = []
        cond1219 = self.match_lookahead_terminal("STRING", 0)
        while cond1219:
            item1220 = self.consume_terminal("STRING")
            xs1218.append(item1220)
            cond1219 = self.match_lookahead_terminal("STRING", 0)
        strings1221 = xs1218
        self.consume_literal(")")
        return strings1221
=======
        xs1289 = []
        cond1290 = self.match_lookahead_terminal("STRING", 0)
        while cond1290:
            item1291 = self.consume_terminal("STRING")
            xs1289.append(item1291)
            cond1290 = self.match_lookahead_terminal("STRING", 0)
        strings1292 = xs1289
        self.consume_literal(")")
        return strings1292
>>>>>>> origin/main

    def parse_iceberg_locator_warehouse(self) -> str:
        self.consume_literal("(")
        self.consume_literal("warehouse")
<<<<<<< HEAD
        string1222 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1222

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1227 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t1997 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1223 = _t1997
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t1999 = self.parse_iceberg_catalog_config_scope()
            _t1998 = _t1999
        else:
            _t1998 = None
        iceberg_catalog_config_scope1224 = _t1998
        _t2000 = self.parse_iceberg_properties()
        iceberg_properties1225 = _t2000
        _t2001 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1226 = _t2001
        self.consume_literal(")")
        _t2002 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1223, iceberg_catalog_config_scope1224, iceberg_properties1225, iceberg_auth_properties1226)
        result1228 = _t2002
        self.record_span(span_start1227, "IcebergCatalogConfig")
        return result1228
=======
        string1293 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1293

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1298 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t2090 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1294 = _t2090
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t2092 = self.parse_iceberg_catalog_config_scope()
            _t2091 = _t2092
        else:
            _t2091 = None
        iceberg_catalog_config_scope1295 = _t2091
        _t2093 = self.parse_iceberg_properties()
        iceberg_properties1296 = _t2093
        _t2094 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1297 = _t2094
        self.consume_literal(")")
        _t2095 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1294, iceberg_catalog_config_scope1295, iceberg_properties1296, iceberg_auth_properties1297)
        result1299 = _t2095
        self.record_span(span_start1298, "IcebergCatalogConfig")
        return result1299
>>>>>>> origin/main

    def parse_iceberg_catalog_uri(self) -> str:
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
<<<<<<< HEAD
        string1229 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1229
=======
        string1300 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1300
>>>>>>> origin/main

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
<<<<<<< HEAD
        string1230 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1230
=======
        string1301 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1301
>>>>>>> origin/main

    def parse_iceberg_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
<<<<<<< HEAD
        xs1231 = []
        cond1232 = self.match_lookahead_literal("(", 0)
        while cond1232:
            _t2003 = self.parse_iceberg_property_entry()
            item1233 = _t2003
            xs1231.append(item1233)
            cond1232 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1234 = xs1231
        self.consume_literal(")")
        return iceberg_property_entrys1234
=======
        xs1302 = []
        cond1303 = self.match_lookahead_literal("(", 0)
        while cond1303:
            _t2096 = self.parse_iceberg_property_entry()
            item1304 = _t2096
            xs1302.append(item1304)
            cond1303 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1305 = xs1302
        self.consume_literal(")")
        return iceberg_property_entrys1305
>>>>>>> origin/main

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
<<<<<<< HEAD
        string1235 = self.consume_terminal("STRING")
        string_31236 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1235, string_31236,)
=======
        string1306 = self.consume_terminal("STRING")
        string_31307 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1306, string_31307,)
>>>>>>> origin/main

    def parse_iceberg_auth_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("auth_properties")
<<<<<<< HEAD
        xs1237 = []
        cond1238 = self.match_lookahead_literal("(", 0)
        while cond1238:
            _t2004 = self.parse_iceberg_masked_property_entry()
            item1239 = _t2004
            xs1237.append(item1239)
            cond1238 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1240 = xs1237
        self.consume_literal(")")
        return iceberg_masked_property_entrys1240
=======
        xs1308 = []
        cond1309 = self.match_lookahead_literal("(", 0)
        while cond1309:
            _t2097 = self.parse_iceberg_masked_property_entry()
            item1310 = _t2097
            xs1308.append(item1310)
            cond1309 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1311 = xs1308
        self.consume_literal(")")
        return iceberg_masked_property_entrys1311
>>>>>>> origin/main

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
<<<<<<< HEAD
        string1241 = self.consume_terminal("STRING")
        string_31242 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1241, string_31242,)
=======
        string1312 = self.consume_terminal("STRING")
        string_31313 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1312, string_31313,)
>>>>>>> origin/main

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
<<<<<<< HEAD
        string1243 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1243
=======
        string1314 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1314
>>>>>>> origin/main

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
<<<<<<< HEAD
        string1244 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1244

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1246 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2005 = self.parse_fragment_id()
        fragment_id1245 = _t2005
        self.consume_literal(")")
        _t2006 = transactions_pb2.Undefine(fragment_id=fragment_id1245)
        result1247 = _t2006
        self.record_span(span_start1246, "Undefine")
        return result1247

    def parse_context(self) -> transactions_pb2.Context:
        span_start1252 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1248 = []
        cond1249 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1249:
            _t2007 = self.parse_relation_id()
            item1250 = _t2007
            xs1248.append(item1250)
            cond1249 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1251 = xs1248
        self.consume_literal(")")
        _t2008 = transactions_pb2.Context(relations=relation_ids1251)
        result1253 = _t2008
        self.record_span(span_start1252, "Context")
        return result1253

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1259 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t2009 = self.parse_edb_path()
        edb_path1254 = _t2009
        xs1255 = []
        cond1256 = self.match_lookahead_literal("[", 0)
        while cond1256:
            _t2010 = self.parse_snapshot_mapping()
            item1257 = _t2010
            xs1255.append(item1257)
            cond1256 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1258 = xs1255
        self.consume_literal(")")
        _t2011 = transactions_pb2.Snapshot(prefix=edb_path1254, mappings=snapshot_mappings1258)
        result1260 = _t2011
        self.record_span(span_start1259, "Snapshot")
        return result1260

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1263 = self.span_start()
        _t2012 = self.parse_edb_path()
        edb_path1261 = _t2012
        _t2013 = self.parse_relation_id()
        relation_id1262 = _t2013
        _t2014 = transactions_pb2.SnapshotMapping(destination_path=edb_path1261, source_relation=relation_id1262)
        result1264 = _t2014
        self.record_span(span_start1263, "SnapshotMapping")
        return result1264
=======
        string1315 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1315

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1317 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2098 = self.parse_fragment_id()
        fragment_id1316 = _t2098
        self.consume_literal(")")
        _t2099 = transactions_pb2.Undefine(fragment_id=fragment_id1316)
        result1318 = _t2099
        self.record_span(span_start1317, "Undefine")
        return result1318

    def parse_context(self) -> transactions_pb2.Context:
        span_start1323 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1319 = []
        cond1320 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1320:
            _t2100 = self.parse_relation_id()
            item1321 = _t2100
            xs1319.append(item1321)
            cond1320 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1322 = xs1319
        self.consume_literal(")")
        _t2101 = transactions_pb2.Context(relations=relation_ids1322)
        result1324 = _t2101
        self.record_span(span_start1323, "Context")
        return result1324

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1330 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t2102 = self.parse_edb_path()
        edb_path1325 = _t2102
        xs1326 = []
        cond1327 = self.match_lookahead_literal("[", 0)
        while cond1327:
            _t2103 = self.parse_snapshot_mapping()
            item1328 = _t2103
            xs1326.append(item1328)
            cond1327 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1329 = xs1326
        self.consume_literal(")")
        _t2104 = transactions_pb2.Snapshot(prefix=edb_path1325, mappings=snapshot_mappings1329)
        result1331 = _t2104
        self.record_span(span_start1330, "Snapshot")
        return result1331

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1334 = self.span_start()
        _t2105 = self.parse_edb_path()
        edb_path1332 = _t2105
        _t2106 = self.parse_relation_id()
        relation_id1333 = _t2106
        _t2107 = transactions_pb2.SnapshotMapping(destination_path=edb_path1332, source_relation=relation_id1333)
        result1335 = _t2107
        self.record_span(span_start1334, "SnapshotMapping")
        return result1335
>>>>>>> origin/main

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
<<<<<<< HEAD
        xs1265 = []
        cond1266 = self.match_lookahead_literal("(", 0)
        while cond1266:
            _t2015 = self.parse_read()
            item1267 = _t2015
            xs1265.append(item1267)
            cond1266 = self.match_lookahead_literal("(", 0)
        reads1268 = xs1265
        self.consume_literal(")")
        return reads1268

    def parse_read(self) -> transactions_pb2.Read:
        span_start1275 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2017 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2018 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t2019 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t2020 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t2021 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t2022 = 3
                                else:
                                    _t2022 = -1
                                _t2021 = _t2022
                            _t2020 = _t2021
                        _t2019 = _t2020
                    _t2018 = _t2019
                _t2017 = _t2018
            _t2016 = _t2017
        else:
            _t2016 = -1
        prediction1269 = _t2016
        if prediction1269 == 4:
            _t2024 = self.parse_export()
            export1274 = _t2024
            _t2025 = transactions_pb2.Read(export=export1274)
            _t2023 = _t2025
        else:
            if prediction1269 == 3:
                _t2027 = self.parse_abort()
                abort1273 = _t2027
                _t2028 = transactions_pb2.Read(abort=abort1273)
                _t2026 = _t2028
            else:
                if prediction1269 == 2:
                    _t2030 = self.parse_what_if()
                    what_if1272 = _t2030
                    _t2031 = transactions_pb2.Read(what_if=what_if1272)
                    _t2029 = _t2031
                else:
                    if prediction1269 == 1:
                        _t2033 = self.parse_output()
                        output1271 = _t2033
                        _t2034 = transactions_pb2.Read(output=output1271)
                        _t2032 = _t2034
                    else:
                        if prediction1269 == 0:
                            _t2036 = self.parse_demand()
                            demand1270 = _t2036
                            _t2037 = transactions_pb2.Read(demand=demand1270)
                            _t2035 = _t2037
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2032 = _t2035
                    _t2029 = _t2032
                _t2026 = _t2029
            _t2023 = _t2026
        result1276 = _t2023
        self.record_span(span_start1275, "Read")
        return result1276
=======
        xs1336 = []
        cond1337 = self.match_lookahead_literal("(", 0)
        while cond1337:
            _t2108 = self.parse_read()
            item1338 = _t2108
            xs1336.append(item1338)
            cond1337 = self.match_lookahead_literal("(", 0)
        reads1339 = xs1336
        self.consume_literal(")")
        return reads1339

    def parse_read(self) -> transactions_pb2.Read:
        span_start1346 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2110 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2111 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t2112 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t2113 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t2114 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t2115 = 3
                                else:
                                    _t2115 = -1
                                _t2114 = _t2115
                            _t2113 = _t2114
                        _t2112 = _t2113
                    _t2111 = _t2112
                _t2110 = _t2111
            _t2109 = _t2110
        else:
            _t2109 = -1
        prediction1340 = _t2109
        if prediction1340 == 4:
            _t2117 = self.parse_export()
            export1345 = _t2117
            _t2118 = transactions_pb2.Read(export=export1345)
            _t2116 = _t2118
        else:
            if prediction1340 == 3:
                _t2120 = self.parse_abort()
                abort1344 = _t2120
                _t2121 = transactions_pb2.Read(abort=abort1344)
                _t2119 = _t2121
            else:
                if prediction1340 == 2:
                    _t2123 = self.parse_what_if()
                    what_if1343 = _t2123
                    _t2124 = transactions_pb2.Read(what_if=what_if1343)
                    _t2122 = _t2124
                else:
                    if prediction1340 == 1:
                        _t2126 = self.parse_output()
                        output1342 = _t2126
                        _t2127 = transactions_pb2.Read(output=output1342)
                        _t2125 = _t2127
                    else:
                        if prediction1340 == 0:
                            _t2129 = self.parse_demand()
                            demand1341 = _t2129
                            _t2130 = transactions_pb2.Read(demand=demand1341)
                            _t2128 = _t2130
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2125 = _t2128
                    _t2122 = _t2125
                _t2119 = _t2122
            _t2116 = _t2119
        result1347 = _t2116
        self.record_span(span_start1346, "Read")
        return result1347

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1349 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2131 = self.parse_relation_id()
        relation_id1348 = _t2131
        self.consume_literal(")")
        _t2132 = transactions_pb2.Demand(relation_id=relation_id1348)
        result1350 = _t2132
        self.record_span(span_start1349, "Demand")
        return result1350
>>>>>>> origin/main

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1278 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2038 = self.parse_relation_id()
        relation_id1277 = _t2038
        self.consume_literal(")")
        _t2039 = transactions_pb2.Demand(relation_id=relation_id1277)
        result1279 = _t2039
        self.record_span(span_start1278, "Demand")
        return result1279

    def parse_output(self) -> transactions_pb2.Output:
<<<<<<< HEAD
        span_start1282 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2040 = self.parse_name()
        name1280 = _t2040
        _t2041 = self.parse_relation_id()
        relation_id1281 = _t2041
        self.consume_literal(")")
        _t2042 = transactions_pb2.Output(name=name1280, relation_id=relation_id1281)
        result1283 = _t2042
        self.record_span(span_start1282, "Output")
        return result1283

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1286 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2043 = self.parse_name()
        name1284 = _t2043
        _t2044 = self.parse_epoch()
        epoch1285 = _t2044
        self.consume_literal(")")
        _t2045 = transactions_pb2.WhatIf(branch=name1284, epoch=epoch1285)
        result1287 = _t2045
        self.record_span(span_start1286, "WhatIf")
        return result1287

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1290 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2047 = self.parse_name()
            _t2046 = _t2047
        else:
            _t2046 = None
        name1288 = _t2046
        _t2048 = self.parse_relation_id()
        relation_id1289 = _t2048
        self.consume_literal(")")
        _t2049 = transactions_pb2.Abort(name=(name1288 if name1288 is not None else "abort"), relation_id=relation_id1289)
        result1291 = _t2049
        self.record_span(span_start1290, "Abort")
        return result1291

    def parse_export(self) -> transactions_pb2.Export:
        span_start1295 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2051 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2052 = 0
                else:
                    _t2052 = -1
                _t2051 = _t2052
            _t2050 = _t2051
        else:
            _t2050 = -1
        prediction1292 = _t2050
        if prediction1292 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2054 = self.parse_export_iceberg_config()
            export_iceberg_config1294 = _t2054
            self.consume_literal(")")
            _t2055 = transactions_pb2.Export(iceberg_config=export_iceberg_config1294)
            _t2053 = _t2055
        else:
            if prediction1292 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2057 = self.parse_export_csv_config()
                export_csv_config1293 = _t2057
                self.consume_literal(")")
                _t2058 = transactions_pb2.Export(csv_config=export_csv_config1293)
                _t2056 = _t2058
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2053 = _t2056
        result1296 = _t2053
        self.record_span(span_start1295, "Export")
        return result1296

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1304 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2060 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2061 = 1
                else:
                    _t2061 = -1
                _t2060 = _t2061
            _t2059 = _t2060
        else:
            _t2059 = -1
        prediction1297 = _t2059
        if prediction1297 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2063 = self.parse_export_csv_path()
            export_csv_path1301 = _t2063
            _t2064 = self.parse_export_csv_columns_list()
            export_csv_columns_list1302 = _t2064
            _t2065 = self.parse_config_dict()
            config_dict1303 = _t2065
            self.consume_literal(")")
            _t2066 = self.construct_export_csv_config(export_csv_path1301, export_csv_columns_list1302, config_dict1303)
            _t2062 = _t2066
        else:
            if prediction1297 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2068 = self.parse_export_csv_output_location()
                export_csv_output_location1298 = _t2068
                _t2069 = self.parse_export_csv_source()
                export_csv_source1299 = _t2069
                _t2070 = self.parse_csv_config()
                csv_config1300 = _t2070
                self.consume_literal(")")
                _t2071 = self.construct_export_csv_config_with_location(export_csv_output_location1298, export_csv_source1299, csv_config1300)
                _t2067 = _t2071
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2062 = _t2067
        result1305 = _t2062
        self.record_span(span_start1304, "ExportCSVConfig")
        return result1305

    def parse_export_csv_output_location(self) -> tuple[str, str]:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("transaction_output_name", 1):
                _t2073 = 1
            else:
                if self.match_lookahead_literal("path", 1):
                    _t2074 = 0
                else:
                    _t2074 = -1
                _t2073 = _t2074
            _t2072 = _t2073
        else:
            _t2072 = -1
        prediction1306 = _t2072
        if prediction1306 == 1:
            self.consume_literal("(")
            self.consume_literal("transaction_output_name")
            _t2076 = self.parse_name()
            name1308 = _t2076
            self.consume_literal(")")
            _t2075 = ("", name1308,)
        else:
            if prediction1306 == 0:
                self.consume_literal("(")
                self.consume_literal("path")
                string1307 = self.consume_terminal("STRING")
                self.consume_literal(")")
                _t2077 = (string1307, "",)
            else:
                raise ParseError("Unexpected token in export_csv_output_location" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2075 = _t2077
        return _t2075

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1315 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2079 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2080 = 0
                else:
                    _t2080 = -1
                _t2079 = _t2080
            _t2078 = _t2079
        else:
            _t2078 = -1
        prediction1309 = _t2078
        if prediction1309 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2082 = self.parse_relation_id()
            relation_id1314 = _t2082
            self.consume_literal(")")
            _t2083 = transactions_pb2.ExportCSVSource(table_def=relation_id1314)
            _t2081 = _t2083
        else:
            if prediction1309 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1310 = []
                cond1311 = self.match_lookahead_literal("(", 0)
                while cond1311:
                    _t2085 = self.parse_export_csv_column()
                    item1312 = _t2085
                    xs1310.append(item1312)
                    cond1311 = self.match_lookahead_literal("(", 0)
                export_csv_columns1313 = xs1310
                self.consume_literal(")")
                _t2086 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1313)
                _t2087 = transactions_pb2.ExportCSVSource(gnf_columns=_t2086)
                _t2084 = _t2087
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2081 = _t2084
        result1316 = _t2081
        self.record_span(span_start1315, "ExportCSVSource")
        return result1316

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1319 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1317 = self.consume_terminal("STRING")
        _t2088 = self.parse_relation_id()
        relation_id1318 = _t2088
        self.consume_literal(")")
        _t2089 = transactions_pb2.ExportCSVColumn(column_name=string1317, column_data=relation_id1318)
        result1320 = _t2089
        self.record_span(span_start1319, "ExportCSVColumn")
        return result1320
=======
        span_start1353 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2133 = self.parse_name()
        name1351 = _t2133
        _t2134 = self.parse_relation_id()
        relation_id1352 = _t2134
        self.consume_literal(")")
        _t2135 = transactions_pb2.Output(name=name1351, relation_id=relation_id1352)
        result1354 = _t2135
        self.record_span(span_start1353, "Output")
        return result1354

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1357 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2136 = self.parse_name()
        name1355 = _t2136
        _t2137 = self.parse_epoch()
        epoch1356 = _t2137
        self.consume_literal(")")
        _t2138 = transactions_pb2.WhatIf(branch=name1355, epoch=epoch1356)
        result1358 = _t2138
        self.record_span(span_start1357, "WhatIf")
        return result1358

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1361 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2140 = self.parse_name()
            _t2139 = _t2140
        else:
            _t2139 = None
        name1359 = _t2139
        _t2141 = self.parse_relation_id()
        relation_id1360 = _t2141
        self.consume_literal(")")
        _t2142 = transactions_pb2.Abort(name=(name1359 if name1359 is not None else "abort"), relation_id=relation_id1360)
        result1362 = _t2142
        self.record_span(span_start1361, "Abort")
        return result1362

    def parse_export(self) -> transactions_pb2.Export:
        span_start1366 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2144 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2145 = 0
                else:
                    _t2145 = -1
                _t2144 = _t2145
            _t2143 = _t2144
        else:
            _t2143 = -1
        prediction1363 = _t2143
        if prediction1363 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2147 = self.parse_export_iceberg_config()
            export_iceberg_config1365 = _t2147
            self.consume_literal(")")
            _t2148 = transactions_pb2.Export(iceberg_config=export_iceberg_config1365)
            _t2146 = _t2148
        else:
            if prediction1363 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2150 = self.parse_export_csv_config()
                export_csv_config1364 = _t2150
                self.consume_literal(")")
                _t2151 = transactions_pb2.Export(csv_config=export_csv_config1364)
                _t2149 = _t2151
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2146 = _t2149
        result1367 = _t2146
        self.record_span(span_start1366, "Export")
        return result1367

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1375 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2153 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2154 = 1
                else:
                    _t2154 = -1
                _t2153 = _t2154
            _t2152 = _t2153
        else:
            _t2152 = -1
        prediction1368 = _t2152
        if prediction1368 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2156 = self.parse_export_csv_path()
            export_csv_path1372 = _t2156
            _t2157 = self.parse_export_csv_columns_list()
            export_csv_columns_list1373 = _t2157
            _t2158 = self.parse_config_dict()
            config_dict1374 = _t2158
            self.consume_literal(")")
            _t2159 = self.construct_export_csv_config(export_csv_path1372, export_csv_columns_list1373, config_dict1374)
            _t2155 = _t2159
        else:
            if prediction1368 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2161 = self.parse_export_csv_path()
                export_csv_path1369 = _t2161
                _t2162 = self.parse_export_csv_source()
                export_csv_source1370 = _t2162
                _t2163 = self.parse_csv_config()
                csv_config1371 = _t2163
                self.consume_literal(")")
                _t2164 = self.construct_export_csv_config_with_source(export_csv_path1369, export_csv_source1370, csv_config1371)
                _t2160 = _t2164
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2155 = _t2160
        result1376 = _t2155
        self.record_span(span_start1375, "ExportCSVConfig")
        return result1376
>>>>>>> origin/main

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
<<<<<<< HEAD
        string1321 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1321
=======
        string1377 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1377

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1384 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2166 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2167 = 0
                else:
                    _t2167 = -1
                _t2166 = _t2167
            _t2165 = _t2166
        else:
            _t2165 = -1
        prediction1378 = _t2165
        if prediction1378 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2169 = self.parse_relation_id()
            relation_id1383 = _t2169
            self.consume_literal(")")
            _t2170 = transactions_pb2.ExportCSVSource(table_def=relation_id1383)
            _t2168 = _t2170
        else:
            if prediction1378 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1379 = []
                cond1380 = self.match_lookahead_literal("(", 0)
                while cond1380:
                    _t2172 = self.parse_export_csv_column()
                    item1381 = _t2172
                    xs1379.append(item1381)
                    cond1380 = self.match_lookahead_literal("(", 0)
                export_csv_columns1382 = xs1379
                self.consume_literal(")")
                _t2173 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1382)
                _t2174 = transactions_pb2.ExportCSVSource(gnf_columns=_t2173)
                _t2171 = _t2174
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2168 = _t2171
        result1385 = _t2168
        self.record_span(span_start1384, "ExportCSVSource")
        return result1385

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1388 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1386 = self.consume_terminal("STRING")
        _t2175 = self.parse_relation_id()
        relation_id1387 = _t2175
        self.consume_literal(")")
        _t2176 = transactions_pb2.ExportCSVColumn(column_name=string1386, column_data=relation_id1387)
        result1389 = _t2176
        self.record_span(span_start1388, "ExportCSVColumn")
        return result1389
>>>>>>> origin/main

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
<<<<<<< HEAD
        xs1322 = []
        cond1323 = self.match_lookahead_literal("(", 0)
        while cond1323:
            _t2090 = self.parse_export_csv_column()
            item1324 = _t2090
            xs1322.append(item1324)
            cond1323 = self.match_lookahead_literal("(", 0)
        export_csv_columns1325 = xs1322
        self.consume_literal(")")
        return export_csv_columns1325

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1331 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2091 = self.parse_iceberg_locator()
        iceberg_locator1326 = _t2091
        _t2092 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1327 = _t2092
        _t2093 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1328 = _t2093
        _t2094 = self.parse_iceberg_table_properties()
        iceberg_table_properties1329 = _t2094
        if self.match_lookahead_literal("{", 0):
            _t2096 = self.parse_config_dict()
            _t2095 = _t2096
        else:
            _t2095 = None
        config_dict1330 = _t2095
        self.consume_literal(")")
        _t2097 = self.construct_export_iceberg_config_full(iceberg_locator1326, iceberg_catalog_config1327, export_iceberg_table_def1328, iceberg_table_properties1329, config_dict1330)
        result1332 = _t2097
        self.record_span(span_start1331, "ExportIcebergConfig")
        return result1332

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1334 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2098 = self.parse_relation_id()
        relation_id1333 = _t2098
        self.consume_literal(")")
        result1335 = relation_id1333
        self.record_span(span_start1334, "RelationId")
        return result1335
=======
        xs1390 = []
        cond1391 = self.match_lookahead_literal("(", 0)
        while cond1391:
            _t2177 = self.parse_export_csv_column()
            item1392 = _t2177
            xs1390.append(item1392)
            cond1391 = self.match_lookahead_literal("(", 0)
        export_csv_columns1393 = xs1390
        self.consume_literal(")")
        return export_csv_columns1393

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1399 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2178 = self.parse_iceberg_locator()
        iceberg_locator1394 = _t2178
        _t2179 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1395 = _t2179
        _t2180 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1396 = _t2180
        _t2181 = self.parse_iceberg_table_properties()
        iceberg_table_properties1397 = _t2181
        if self.match_lookahead_literal("{", 0):
            _t2183 = self.parse_config_dict()
            _t2182 = _t2183
        else:
            _t2182 = None
        config_dict1398 = _t2182
        self.consume_literal(")")
        _t2184 = self.construct_export_iceberg_config_full(iceberg_locator1394, iceberg_catalog_config1395, export_iceberg_table_def1396, iceberg_table_properties1397, config_dict1398)
        result1400 = _t2184
        self.record_span(span_start1399, "ExportIcebergConfig")
        return result1400

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1402 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2185 = self.parse_relation_id()
        relation_id1401 = _t2185
        self.consume_literal(")")
        result1403 = relation_id1401
        self.record_span(span_start1402, "RelationId")
        return result1403
>>>>>>> origin/main

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
<<<<<<< HEAD
        xs1336 = []
        cond1337 = self.match_lookahead_literal("(", 0)
        while cond1337:
            _t2099 = self.parse_iceberg_property_entry()
            item1338 = _t2099
            xs1336.append(item1338)
            cond1337 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1339 = xs1336
        self.consume_literal(")")
        return iceberg_property_entrys1339
=======
        xs1404 = []
        cond1405 = self.match_lookahead_literal("(", 0)
        while cond1405:
            _t2186 = self.parse_iceberg_property_entry()
            item1406 = _t2186
            xs1404.append(item1406)
            cond1405 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1407 = xs1404
        self.consume_literal(")")
        return iceberg_property_entrys1407
>>>>>>> origin/main


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
