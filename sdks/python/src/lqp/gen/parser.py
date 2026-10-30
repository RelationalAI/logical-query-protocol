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
        if value is None:
            return int(default)
        else:
            _t2238 = None
        assert value is not None
        if value.HasField("int32_value"):
            assert value is not None
            return value.int32_value
        else:
            _t2239 = None
        raise ParseError("expected an int32 value (e.g. `1i32`) for this config field")

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2240 = value.HasField("int_value")
        else:
            _t2240 = False
        if _t2240:
            assert value is not None
            return value.int_value
        else:
            _t2241 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2242 = value.HasField("string_value")
        else:
            _t2242 = False
        if _t2242:
            assert value is not None
            return value.string_value
        else:
            _t2243 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2244 = value.HasField("boolean_value")
        else:
            _t2244 = False
        if _t2244:
            assert value is not None
            return value.boolean_value
        else:
            _t2245 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2246 = value.HasField("string_value")
        else:
            _t2246 = False
        if _t2246:
            assert value is not None
            return [value.string_value]
        else:
            _t2247 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2248 = value.HasField("int_value")
        else:
            _t2248 = False
        if _t2248:
            assert value is not None
            return value.int_value
        else:
            _t2249 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2250 = value.HasField("float_value")
        else:
            _t2250 = False
        if _t2250:
            assert value is not None
            return value.float_value
        else:
            _t2251 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2252 = value.HasField("string_value")
        else:
            _t2252 = False
        if _t2252:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2253 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2254 = value.HasField("uint128_value")
        else:
            _t2254 = False
        if _t2254:
            assert value is not None
            return value.uint128_value
        else:
            _t2255 = None
        return None

    def construct_non_cdc_relations(self, targets: Sequence[logic_pb2.TargetRelation]) -> logic_pb2.TargetRelations:
        _t2256 = logic_pb2.PlainTargets(targets=targets)
        _t2257 = logic_pb2.TargetRelations(keys=[], plain=_t2256)
        return _t2257

    def construct_cdc_relations(self, inserts: Sequence[logic_pb2.TargetRelation], deletes: Sequence[logic_pb2.TargetRelation]) -> logic_pb2.TargetRelations:
        _t2258 = logic_pb2.CDCTargets(inserts=inserts, deletes=deletes)
        _t2259 = logic_pb2.TargetRelations(keys=[], cdc=_t2258)
        return _t2259

    def construct_relations(self, keys: tuple[Sequence[logic_pb2.NamedColumn], bool], body: logic_pb2.TargetRelations, load_errors_opt: logic_pb2.RelationId | None) -> logic_pb2.TargetRelations:
        if body.HasField("plain"):
            _t2261 = logic_pb2.TargetRelations(keys=keys[0], synthetic_key=keys[1], plain=body.plain, load_errors=load_errors_opt)
            return _t2261
        else:
            _t2260 = None
        _t2262 = logic_pb2.TargetRelations(keys=keys[0], synthetic_key=keys[1], cdc=body.cdc, load_errors=load_errors_opt)
        return _t2262

    def construct_csv_data(self, locator: logic_pb2.CSVLocator, config: logic_pb2.CSVConfig, columns_opt: Sequence[logic_pb2.GNFColumn] | None, relations_opt: logic_pb2.TargetRelations | None, asof: str) -> logic_pb2.CSVData:
        if (columns_opt is not None and relations_opt is not None):
            raise ParseError("csv_data takes either `(columns ...)` or `(relations ...)`, not both")
        else:
            _t2263 = None
        _t2264 = logic_pb2.CSVData(locator=locator, config=config, columns=(columns_opt if columns_opt is not None else []), asof=asof, relations=relations_opt)
        return _t2264

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]], storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2265 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2265
        _t2266 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2266
        _t2267 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2267
        _t2268 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2268
        _t2269 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2269
        _t2270 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2270
        _t2271 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2271
        _t2272 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2272
        _t2273 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2273
        _t2274 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2274
        _t2275 = self._extract_value_string(config.get("csv_compression"), "")
        compression = _t2275
        _t2276 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2276
        _t2277 = self.construct_csv_storage_integration(storage_integration_opt)
        storage_integration = _t2277
        _t2278 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
        return _t2278

    def construct_csv_storage_integration(self, storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.StorageIntegration | None:
        if storage_integration_opt is None:
            return None
        else:
            _t2279 = None
        assert storage_integration_opt is not None
        config = dict(storage_integration_opt)
        _t2280 = self._extract_value_string(config.get("provider"), "")
        _t2281 = self._extract_value_string(config.get("azure_sas_token"), "")
        _t2282 = self._extract_value_string(config.get("s3_region"), "")
        _t2283 = self._extract_value_string(config.get("s3_access_key_id"), "")
        _t2284 = self._extract_value_string(config.get("s3_secret_access_key"), "")
        _t2285 = logic_pb2.StorageIntegration(provider=_t2280, azure_sas_token=_t2281, s3_region=_t2282, s3_access_key_id=_t2283, s3_secret_access_key=_t2284)
        return _t2285

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2286 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2286
        _t2287 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2287
        _t2288 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2288
        _t2289 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2289
        _t2290 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2290
        _t2291 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2291
        _t2292 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2292
        _t2293 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2293
        _t2294 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2294
        _t2295 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2295
        _t2296 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2296

    def default_configure(self) -> transactions_pb2.Configure:
        _t2297 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2297
        _t2298 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2298

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
        _t2299 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2299
        _t2300 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2300
        config_values_pairs = []
        for pair in config_dict:
            if (pair[0] != "semantics_version" and pair[0] != "ivm.maintenance_level"):
                config_values_pairs.append(pair)
        configuration_values = dict(config_values_pairs)
        _t2301 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config, configuration_values=configuration_values)
        return _t2301

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2302 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2302
        _t2303 = self._extract_value_string(config.get("compression"), "")
        compression = _t2303
        _t2304 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2304
        _t2305 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2305
        _t2306 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2306
        _t2307 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2307
        _t2308 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2308
        _t2309 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2309

    def construct_export_csv_config_with_location(self, location: tuple[str, str], csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2310 = transactions_pb2.ExportCSVConfig(path=location[0], transaction_output_name=location[1], csv_source=csv_source, csv_config=csv_config)
        return _t2310

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2311 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2311

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns_opt: Sequence[logic_pb2.GNFColumn] | None, relations_opt: logic_pb2.TargetRelations | None, from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        if (columns_opt is not None and relations_opt is not None):
            raise ParseError("iceberg_data takes either `(columns ...)` or `(relations ...)`, not both")
        else:
            _t2312 = None
        _t2313 = logic_pb2.IcebergData(locator=locator, config=config, columns=(columns_opt if columns_opt is not None else []), from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta, relations=relations_opt)
        return _t2313

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2314 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2314
        _t2315 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2315
        _t2316 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2316
        table_props = dict(table_property_pairs)
        _t2317 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2317

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start723 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1435 = self.parse_configure()
            _t1434 = _t1435
        else:
            _t1434 = None
        configure717 = _t1434
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1437 = self.parse_sync()
            _t1436 = _t1437
        else:
            _t1436 = None
        sync718 = _t1436
        xs719 = []
        cond720 = self.match_lookahead_literal("(", 0)
        while cond720:
            _t1438 = self.parse_epoch()
            item721 = _t1438
            xs719.append(item721)
            cond720 = self.match_lookahead_literal("(", 0)
        epochs722 = xs719
        self.consume_literal(")")
        _t1439 = self.default_configure()
        _t1440 = transactions_pb2.Transaction(epochs=epochs722, configure=(configure717 if configure717 is not None else _t1439), sync=sync718)
        result724 = _t1440
        self.record_span(span_start723, "Transaction")
        return result724

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start726 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1441 = self.parse_config_dict()
        config_dict725 = _t1441
        self.consume_literal(")")
        _t1442 = self.construct_configure(config_dict725)
        result727 = _t1442
        self.record_span(span_start726, "Configure")
        return result727

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs728 = []
        cond729 = self.match_lookahead_literal(":", 0)
        while cond729:
            _t1443 = self.parse_config_key_value()
            item730 = _t1443
            xs728.append(item730)
            cond729 = self.match_lookahead_literal(":", 0)
        config_key_values731 = xs728
        self.consume_literal("}")
        return config_key_values731

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol732 = self.consume_terminal("SYMBOL")
        _t1444 = self.parse_raw_value()
        raw_value733 = _t1444
        return (symbol732, raw_value733,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start747 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1445 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1446 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1447 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1449 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1450 = 0
                            else:
                                _t1450 = -1
                            _t1449 = _t1450
                        _t1448 = _t1449
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1451 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1452 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1453 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1454 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1455 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1456 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1457 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1458 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1459 = 10
                                                        else:
                                                            _t1459 = -1
                                                        _t1458 = _t1459
                                                    _t1457 = _t1458
                                                _t1456 = _t1457
                                            _t1455 = _t1456
                                        _t1454 = _t1455
                                    _t1453 = _t1454
                                _t1452 = _t1453
                            _t1451 = _t1452
                        _t1448 = _t1451
                    _t1447 = _t1448
                _t1446 = _t1447
            _t1445 = _t1446
        prediction734 = _t1445
        if prediction734 == 12:
            _t1461 = self.parse_boolean_value()
            boolean_value746 = _t1461
            _t1462 = logic_pb2.Value(boolean_value=boolean_value746)
            _t1460 = _t1462
        else:
            if prediction734 == 11:
                self.consume_literal("missing")
                _t1464 = logic_pb2.MissingValue()
                _t1465 = logic_pb2.Value(missing_value=_t1464)
                _t1463 = _t1465
            else:
                if prediction734 == 10:
                    decimal745 = self.consume_terminal("DECIMAL")
                    _t1467 = logic_pb2.Value(decimal_value=decimal745)
                    _t1466 = _t1467
                else:
                    if prediction734 == 9:
                        int128744 = self.consume_terminal("INT128")
                        _t1469 = logic_pb2.Value(int128_value=int128744)
                        _t1468 = _t1469
                    else:
                        if prediction734 == 8:
                            uint128743 = self.consume_terminal("UINT128")
                            _t1471 = logic_pb2.Value(uint128_value=uint128743)
                            _t1470 = _t1471
                        else:
                            if prediction734 == 7:
                                uint32742 = self.consume_terminal("UINT32")
                                _t1473 = logic_pb2.Value(uint32_value=uint32742)
                                _t1472 = _t1473
                            else:
                                if prediction734 == 6:
                                    float741 = self.consume_terminal("FLOAT")
                                    _t1475 = logic_pb2.Value(float_value=float741)
                                    _t1474 = _t1475
                                else:
                                    if prediction734 == 5:
                                        float32740 = self.consume_terminal("FLOAT32")
                                        _t1477 = logic_pb2.Value(float32_value=float32740)
                                        _t1476 = _t1477
                                    else:
                                        if prediction734 == 4:
                                            int739 = self.consume_terminal("INT")
                                            _t1479 = logic_pb2.Value(int_value=int739)
                                            _t1478 = _t1479
                                        else:
                                            if prediction734 == 3:
                                                int32738 = self.consume_terminal("INT32")
                                                _t1481 = logic_pb2.Value(int32_value=int32738)
                                                _t1480 = _t1481
                                            else:
                                                if prediction734 == 2:
                                                    string737 = self.consume_terminal("STRING")
                                                    _t1483 = logic_pb2.Value(string_value=string737)
                                                    _t1482 = _t1483
                                                else:
                                                    if prediction734 == 1:
                                                        _t1485 = self.parse_raw_datetime()
                                                        raw_datetime736 = _t1485
                                                        _t1486 = logic_pb2.Value(datetime_value=raw_datetime736)
                                                        _t1484 = _t1486
                                                    else:
                                                        if prediction734 == 0:
                                                            _t1488 = self.parse_raw_date()
                                                            raw_date735 = _t1488
                                                            _t1489 = logic_pb2.Value(date_value=raw_date735)
                                                            _t1487 = _t1489
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1484 = _t1487
                                                    _t1482 = _t1484
                                                _t1480 = _t1482
                                            _t1478 = _t1480
                                        _t1476 = _t1478
                                    _t1474 = _t1476
                                _t1472 = _t1474
                            _t1470 = _t1472
                        _t1468 = _t1470
                    _t1466 = _t1468
                _t1463 = _t1466
            _t1460 = _t1463
        result748 = _t1460
        self.record_span(span_start747, "Value")
        return result748

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start752 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int749 = self.consume_terminal("INT")
        int_3750 = self.consume_terminal("INT")
        int_4751 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1490 = logic_pb2.DateValue(year=int(int749), month=int(int_3750), day=int(int_4751))
        result753 = _t1490
        self.record_span(span_start752, "DateValue")
        return result753

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start761 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int754 = self.consume_terminal("INT")
        int_3755 = self.consume_terminal("INT")
        int_4756 = self.consume_terminal("INT")
        int_5757 = self.consume_terminal("INT")
        int_6758 = self.consume_terminal("INT")
        int_7759 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1491 = self.consume_terminal("INT")
        else:
            _t1491 = None
        int_8760 = _t1491
        self.consume_literal(")")
        _t1492 = logic_pb2.DateTimeValue(year=int(int754), month=int(int_3755), day=int(int_4756), hour=int(int_5757), minute=int(int_6758), second=int(int_7759), microsecond=int((int_8760 if int_8760 is not None else 0)))
        result762 = _t1492
        self.record_span(span_start761, "DateTimeValue")
        return result762

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1493 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1494 = 1
            else:
                _t1494 = -1
            _t1493 = _t1494
        prediction763 = _t1493
        if prediction763 == 1:
            self.consume_literal("false")
            _t1495 = False
        else:
            if prediction763 == 0:
                self.consume_literal("true")
                _t1496 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1495 = _t1496
        return _t1495

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start768 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs764 = []
        cond765 = self.match_lookahead_literal(":", 0)
        while cond765:
            _t1497 = self.parse_fragment_id()
            item766 = _t1497
            xs764.append(item766)
            cond765 = self.match_lookahead_literal(":", 0)
        fragment_ids767 = xs764
        self.consume_literal(")")
        _t1498 = transactions_pb2.Sync(fragments=fragment_ids767)
        result769 = _t1498
        self.record_span(span_start768, "Sync")
        return result769

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start771 = self.span_start()
        self.consume_literal(":")
        symbol770 = self.consume_terminal("SYMBOL")
        result772 = fragments_pb2.FragmentId(id=symbol770.encode())
        self.record_span(span_start771, "FragmentId")
        return result772

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start775 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1500 = self.parse_epoch_writes()
            _t1499 = _t1500
        else:
            _t1499 = None
        epoch_writes773 = _t1499
        if self.match_lookahead_literal("(", 0):
            _t1502 = self.parse_epoch_reads()
            _t1501 = _t1502
        else:
            _t1501 = None
        epoch_reads774 = _t1501
        self.consume_literal(")")
        _t1503 = transactions_pb2.Epoch(writes=(epoch_writes773 if epoch_writes773 is not None else []), reads=(epoch_reads774 if epoch_reads774 is not None else []))
        result776 = _t1503
        self.record_span(span_start775, "Epoch")
        return result776

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs777 = []
        cond778 = self.match_lookahead_literal("(", 0)
        while cond778:
            _t1504 = self.parse_write()
            item779 = _t1504
            xs777.append(item779)
            cond778 = self.match_lookahead_literal("(", 0)
        writes780 = xs777
        self.consume_literal(")")
        return writes780

    def parse_write(self) -> transactions_pb2.Write:
        span_start786 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1506 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1507 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1508 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1509 = 2
                        else:
                            _t1509 = -1
                        _t1508 = _t1509
                    _t1507 = _t1508
                _t1506 = _t1507
            _t1505 = _t1506
        else:
            _t1505 = -1
        prediction781 = _t1505
        if prediction781 == 3:
            _t1511 = self.parse_snapshot()
            snapshot785 = _t1511
            _t1512 = transactions_pb2.Write(snapshot=snapshot785)
            _t1510 = _t1512
        else:
            if prediction781 == 2:
                _t1514 = self.parse_context()
                context784 = _t1514
                _t1515 = transactions_pb2.Write(context=context784)
                _t1513 = _t1515
            else:
                if prediction781 == 1:
                    _t1517 = self.parse_undefine()
                    undefine783 = _t1517
                    _t1518 = transactions_pb2.Write(undefine=undefine783)
                    _t1516 = _t1518
                else:
                    if prediction781 == 0:
                        _t1520 = self.parse_define()
                        define782 = _t1520
                        _t1521 = transactions_pb2.Write(define=define782)
                        _t1519 = _t1521
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1516 = _t1519
                _t1513 = _t1516
            _t1510 = _t1513
        result787 = _t1510
        self.record_span(span_start786, "Write")
        return result787

    def parse_define(self) -> transactions_pb2.Define:
        span_start789 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1522 = self.parse_fragment()
        fragment788 = _t1522
        self.consume_literal(")")
        _t1523 = transactions_pb2.Define(fragment=fragment788)
        result790 = _t1523
        self.record_span(span_start789, "Define")
        return result790

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start796 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1524 = self.parse_new_fragment_id()
        new_fragment_id791 = _t1524
        xs792 = []
        cond793 = self.match_lookahead_literal("(", 0)
        while cond793:
            _t1525 = self.parse_declaration()
            item794 = _t1525
            xs792.append(item794)
            cond793 = self.match_lookahead_literal("(", 0)
        declarations795 = xs792
        self.consume_literal(")")
        result797 = self.construct_fragment(new_fragment_id791, declarations795)
        self.record_span(span_start796, "Fragment")
        return result797

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start799 = self.span_start()
        _t1526 = self.parse_fragment_id()
        fragment_id798 = _t1526
        self.start_fragment(fragment_id798)
        result800 = fragment_id798
        self.record_span(span_start799, "FragmentId")
        return result800

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start806 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1528 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1529 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1530 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1531 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1532 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1533 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1534 = 1
                                    else:
                                        _t1534 = -1
                                    _t1533 = _t1534
                                _t1532 = _t1533
                            _t1531 = _t1532
                        _t1530 = _t1531
                    _t1529 = _t1530
                _t1528 = _t1529
            _t1527 = _t1528
        else:
            _t1527 = -1
        prediction801 = _t1527
        if prediction801 == 3:
            _t1536 = self.parse_data()
            data805 = _t1536
            _t1537 = logic_pb2.Declaration(data=data805)
            _t1535 = _t1537
        else:
            if prediction801 == 2:
                _t1539 = self.parse_constraint()
                constraint804 = _t1539
                _t1540 = logic_pb2.Declaration(constraint=constraint804)
                _t1538 = _t1540
            else:
                if prediction801 == 1:
                    _t1542 = self.parse_algorithm()
                    algorithm803 = _t1542
                    _t1543 = logic_pb2.Declaration(algorithm=algorithm803)
                    _t1541 = _t1543
                else:
                    if prediction801 == 0:
                        _t1545 = self.parse_def()
                        def802 = _t1545
                        _t1546 = logic_pb2.Declaration()
                        getattr(_t1546, 'def').CopyFrom(def802)
                        _t1544 = _t1546
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1541 = _t1544
                _t1538 = _t1541
            _t1535 = _t1538
        result807 = _t1535
        self.record_span(span_start806, "Declaration")
        return result807

    def parse_def(self) -> logic_pb2.Def:
        span_start811 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1547 = self.parse_relation_id()
        relation_id808 = _t1547
        _t1548 = self.parse_abstraction()
        abstraction809 = _t1548
        if self.match_lookahead_literal("(", 0):
            _t1550 = self.parse_attrs()
            _t1549 = _t1550
        else:
            _t1549 = None
        attrs810 = _t1549
        self.consume_literal(")")
        _t1551 = logic_pb2.Def(name=relation_id808, body=abstraction809, attrs=(attrs810 if attrs810 is not None else []))
        result812 = _t1551
        self.record_span(span_start811, "Def")
        return result812

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start816 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1552 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1553 = 1
            else:
                _t1553 = -1
            _t1552 = _t1553
        prediction813 = _t1552
        if prediction813 == 1:
            uint128815 = self.consume_terminal("UINT128")
            _t1554 = logic_pb2.RelationId(id_low=uint128815.low, id_high=uint128815.high)
        else:
            if prediction813 == 0:
                self.consume_literal(":")
                symbol814 = self.consume_terminal("SYMBOL")
                _t1555 = self.relation_id_from_string(symbol814)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1554 = _t1555
        result817 = _t1554
        self.record_span(span_start816, "RelationId")
        return result817

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start820 = self.span_start()
        self.consume_literal("(")
        _t1556 = self.parse_bindings()
        bindings818 = _t1556
        _t1557 = self.parse_formula()
        formula819 = _t1557
        self.consume_literal(")")
        _t1558 = logic_pb2.Abstraction(vars=(list(bindings818[0]) + list(bindings818[1] if bindings818[1] is not None else [])), value=formula819)
        result821 = _t1558
        self.record_span(span_start820, "Abstraction")
        return result821

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs822 = []
        cond823 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond823:
            _t1559 = self.parse_binding()
            item824 = _t1559
            xs822.append(item824)
            cond823 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings825 = xs822
        if self.match_lookahead_literal("|", 0):
            _t1561 = self.parse_value_bindings()
            _t1560 = _t1561
        else:
            _t1560 = None
        value_bindings826 = _t1560
        self.consume_literal("]")
        return (bindings825, (value_bindings826 if value_bindings826 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start829 = self.span_start()
        symbol827 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1562 = self.parse_type()
        type828 = _t1562
        _t1563 = logic_pb2.Var(name=symbol827)
        _t1564 = logic_pb2.Binding(var=_t1563, type=type828)
        result830 = _t1564
        self.record_span(span_start829, "Binding")
        return result830

    def parse_type(self) -> logic_pb2.Type:
        span_start847 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1565 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1566 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1567 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1568 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1569 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1570 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1571 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1572 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1573 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1574 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1575 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1576 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1577 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                if self.match_lookahead_literal("FIXED", 1):
                                                                    _t1579 = 14
                                                                else:
                                                                    if self.match_lookahead_literal("DECIMAL", 1):
                                                                        _t1580 = 9
                                                                    else:
                                                                        _t1580 = -1
                                                                    _t1579 = _t1580
                                                                _t1578 = _t1579
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
                    _t1567 = _t1568
                _t1566 = _t1567
            _t1565 = _t1566
        prediction831 = _t1565
        if prediction831 == 14:
            _t1582 = self.parse_fixed_type()
            fixed_type846 = _t1582
            _t1583 = logic_pb2.Type(fixed_type=fixed_type846)
            _t1581 = _t1583
        else:
            if prediction831 == 13:
                _t1585 = self.parse_uint32_type()
                uint32_type845 = _t1585
                _t1586 = logic_pb2.Type(uint32_type=uint32_type845)
                _t1584 = _t1586
            else:
                if prediction831 == 12:
                    _t1588 = self.parse_float32_type()
                    float32_type844 = _t1588
                    _t1589 = logic_pb2.Type(float32_type=float32_type844)
                    _t1587 = _t1589
                else:
                    if prediction831 == 11:
                        _t1591 = self.parse_int32_type()
                        int32_type843 = _t1591
                        _t1592 = logic_pb2.Type(int32_type=int32_type843)
                        _t1590 = _t1592
                    else:
                        if prediction831 == 10:
                            _t1594 = self.parse_boolean_type()
                            boolean_type842 = _t1594
                            _t1595 = logic_pb2.Type(boolean_type=boolean_type842)
                            _t1593 = _t1595
                        else:
                            if prediction831 == 9:
                                _t1597 = self.parse_decimal_type()
                                decimal_type841 = _t1597
                                _t1598 = logic_pb2.Type(decimal_type=decimal_type841)
                                _t1596 = _t1598
                            else:
                                if prediction831 == 8:
                                    _t1600 = self.parse_missing_type()
                                    missing_type840 = _t1600
                                    _t1601 = logic_pb2.Type(missing_type=missing_type840)
                                    _t1599 = _t1601
                                else:
                                    if prediction831 == 7:
                                        _t1603 = self.parse_datetime_type()
                                        datetime_type839 = _t1603
                                        _t1604 = logic_pb2.Type(datetime_type=datetime_type839)
                                        _t1602 = _t1604
                                    else:
                                        if prediction831 == 6:
                                            _t1606 = self.parse_date_type()
                                            date_type838 = _t1606
                                            _t1607 = logic_pb2.Type(date_type=date_type838)
                                            _t1605 = _t1607
                                        else:
                                            if prediction831 == 5:
                                                _t1609 = self.parse_int128_type()
                                                int128_type837 = _t1609
                                                _t1610 = logic_pb2.Type(int128_type=int128_type837)
                                                _t1608 = _t1610
                                            else:
                                                if prediction831 == 4:
                                                    _t1612 = self.parse_uint128_type()
                                                    uint128_type836 = _t1612
                                                    _t1613 = logic_pb2.Type(uint128_type=uint128_type836)
                                                    _t1611 = _t1613
                                                else:
                                                    if prediction831 == 3:
                                                        _t1615 = self.parse_float_type()
                                                        float_type835 = _t1615
                                                        _t1616 = logic_pb2.Type(float_type=float_type835)
                                                        _t1614 = _t1616
                                                    else:
                                                        if prediction831 == 2:
                                                            _t1618 = self.parse_int_type()
                                                            int_type834 = _t1618
                                                            _t1619 = logic_pb2.Type(int_type=int_type834)
                                                            _t1617 = _t1619
                                                        else:
                                                            if prediction831 == 1:
                                                                _t1621 = self.parse_string_type()
                                                                string_type833 = _t1621
                                                                _t1622 = logic_pb2.Type(string_type=string_type833)
                                                                _t1620 = _t1622
                                                            else:
                                                                if prediction831 == 0:
                                                                    _t1624 = self.parse_unspecified_type()
                                                                    unspecified_type832 = _t1624
                                                                    _t1625 = logic_pb2.Type(unspecified_type=unspecified_type832)
                                                                    _t1623 = _t1625
                                                                else:
                                                                    raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                                _t1620 = _t1623
                                                            _t1617 = _t1620
                                                        _t1614 = _t1617
                                                    _t1611 = _t1614
                                                _t1608 = _t1611
                                            _t1605 = _t1608
                                        _t1602 = _t1605
                                    _t1599 = _t1602
                                _t1596 = _t1599
                            _t1593 = _t1596
                        _t1590 = _t1593
                    _t1587 = _t1590
                _t1584 = _t1587
            _t1581 = _t1584
        result848 = _t1581
        self.record_span(span_start847, "Type")
        return result848

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start849 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1626 = logic_pb2.UnspecifiedType()
        result850 = _t1626
        self.record_span(span_start849, "UnspecifiedType")
        return result850

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start851 = self.span_start()
        self.consume_literal("STRING")
        _t1627 = logic_pb2.StringType()
        result852 = _t1627
        self.record_span(span_start851, "StringType")
        return result852

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start853 = self.span_start()
        self.consume_literal("INT")
        _t1628 = logic_pb2.IntType()
        result854 = _t1628
        self.record_span(span_start853, "IntType")
        return result854

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start855 = self.span_start()
        self.consume_literal("FLOAT")
        _t1629 = logic_pb2.FloatType()
        result856 = _t1629
        self.record_span(span_start855, "FloatType")
        return result856

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start857 = self.span_start()
        self.consume_literal("UINT128")
        _t1630 = logic_pb2.UInt128Type()
        result858 = _t1630
        self.record_span(span_start857, "UInt128Type")
        return result858

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start859 = self.span_start()
        self.consume_literal("INT128")
        _t1631 = logic_pb2.Int128Type()
        result860 = _t1631
        self.record_span(span_start859, "Int128Type")
        return result860

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start861 = self.span_start()
        self.consume_literal("DATE")
        _t1632 = logic_pb2.DateType()
        result862 = _t1632
        self.record_span(span_start861, "DateType")
        return result862

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start863 = self.span_start()
        self.consume_literal("DATETIME")
        _t1633 = logic_pb2.DateTimeType()
        result864 = _t1633
        self.record_span(span_start863, "DateTimeType")
        return result864

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start865 = self.span_start()
        self.consume_literal("MISSING")
        _t1634 = logic_pb2.MissingType()
        result866 = _t1634
        self.record_span(span_start865, "MissingType")
        return result866

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start869 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int867 = self.consume_terminal("INT")
        int_3868 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1635 = logic_pb2.DecimalType(precision=int(int867), scale=int(int_3868))
        result870 = _t1635
        self.record_span(span_start869, "DecimalType")
        return result870

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start871 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1636 = logic_pb2.BooleanType()
        result872 = _t1636
        self.record_span(span_start871, "BooleanType")
        return result872

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start873 = self.span_start()
        self.consume_literal("INT32")
        _t1637 = logic_pb2.Int32Type()
        result874 = _t1637
        self.record_span(span_start873, "Int32Type")
        return result874

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start875 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1638 = logic_pb2.Float32Type()
        result876 = _t1638
        self.record_span(span_start875, "Float32Type")
        return result876

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start877 = self.span_start()
        self.consume_literal("UINT32")
        _t1639 = logic_pb2.UInt32Type()
        result878 = _t1639
        self.record_span(span_start877, "UInt32Type")
        return result878

    def parse_fixed_type(self) -> logic_pb2.FixedType:
        span_start880 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("FIXED")
        int879 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1640 = logic_pb2.FixedType(length=int(int879))
        result881 = _t1640
        self.record_span(span_start880, "FixedType")
        return result881

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs882 = []
        cond883 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond883:
            _t1641 = self.parse_binding()
            item884 = _t1641
            xs882.append(item884)
            cond883 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings885 = xs882
        return bindings885

    def parse_formula(self) -> logic_pb2.Formula:
        span_start900 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1643 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1644 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1645 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1646 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1647 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1648 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1649 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1650 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1651 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1652 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1653 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1654 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1655 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1656 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1657 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1658 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1659 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1660 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1661 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1662 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1663 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1664 = 10
                                                                                                else:
                                                                                                    _t1664 = -1
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
                                                        _t1653 = _t1654
                                                    _t1652 = _t1653
                                                _t1651 = _t1652
                                            _t1650 = _t1651
                                        _t1649 = _t1650
                                    _t1648 = _t1649
                                _t1647 = _t1648
                            _t1646 = _t1647
                        _t1645 = _t1646
                    _t1644 = _t1645
                _t1643 = _t1644
            _t1642 = _t1643
        else:
            _t1642 = -1
        prediction886 = _t1642
        if prediction886 == 12:
            _t1666 = self.parse_cast()
            cast899 = _t1666
            _t1667 = logic_pb2.Formula(cast=cast899)
            _t1665 = _t1667
        else:
            if prediction886 == 11:
                _t1669 = self.parse_rel_atom()
                rel_atom898 = _t1669
                _t1670 = logic_pb2.Formula(rel_atom=rel_atom898)
                _t1668 = _t1670
            else:
                if prediction886 == 10:
                    _t1672 = self.parse_primitive()
                    primitive897 = _t1672
                    _t1673 = logic_pb2.Formula(primitive=primitive897)
                    _t1671 = _t1673
                else:
                    if prediction886 == 9:
                        _t1675 = self.parse_pragma()
                        pragma896 = _t1675
                        _t1676 = logic_pb2.Formula(pragma=pragma896)
                        _t1674 = _t1676
                    else:
                        if prediction886 == 8:
                            _t1678 = self.parse_atom()
                            atom895 = _t1678
                            _t1679 = logic_pb2.Formula(atom=atom895)
                            _t1677 = _t1679
                        else:
                            if prediction886 == 7:
                                _t1681 = self.parse_ffi()
                                ffi894 = _t1681
                                _t1682 = logic_pb2.Formula(ffi=ffi894)
                                _t1680 = _t1682
                            else:
                                if prediction886 == 6:
                                    _t1684 = self.parse_not()
                                    not893 = _t1684
                                    _t1685 = logic_pb2.Formula()
                                    getattr(_t1685, 'not').CopyFrom(not893)
                                    _t1683 = _t1685
                                else:
                                    if prediction886 == 5:
                                        _t1687 = self.parse_disjunction()
                                        disjunction892 = _t1687
                                        _t1688 = logic_pb2.Formula(disjunction=disjunction892)
                                        _t1686 = _t1688
                                    else:
                                        if prediction886 == 4:
                                            _t1690 = self.parse_conjunction()
                                            conjunction891 = _t1690
                                            _t1691 = logic_pb2.Formula(conjunction=conjunction891)
                                            _t1689 = _t1691
                                        else:
                                            if prediction886 == 3:
                                                _t1693 = self.parse_reduce()
                                                reduce890 = _t1693
                                                _t1694 = logic_pb2.Formula(reduce=reduce890)
                                                _t1692 = _t1694
                                            else:
                                                if prediction886 == 2:
                                                    _t1696 = self.parse_exists()
                                                    exists889 = _t1696
                                                    _t1697 = logic_pb2.Formula(exists=exists889)
                                                    _t1695 = _t1697
                                                else:
                                                    if prediction886 == 1:
                                                        _t1699 = self.parse_false()
                                                        false888 = _t1699
                                                        _t1700 = logic_pb2.Formula(disjunction=false888)
                                                        _t1698 = _t1700
                                                    else:
                                                        if prediction886 == 0:
                                                            _t1702 = self.parse_true()
                                                            true887 = _t1702
                                                            _t1703 = logic_pb2.Formula(conjunction=true887)
                                                            _t1701 = _t1703
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1698 = _t1701
                                                    _t1695 = _t1698
                                                _t1692 = _t1695
                                            _t1689 = _t1692
                                        _t1686 = _t1689
                                    _t1683 = _t1686
                                _t1680 = _t1683
                            _t1677 = _t1680
                        _t1674 = _t1677
                    _t1671 = _t1674
                _t1668 = _t1671
            _t1665 = _t1668
        result901 = _t1665
        self.record_span(span_start900, "Formula")
        return result901

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start902 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1704 = logic_pb2.Conjunction(args=[])
        result903 = _t1704
        self.record_span(span_start902, "Conjunction")
        return result903

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start904 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1705 = logic_pb2.Disjunction(args=[])
        result905 = _t1705
        self.record_span(span_start904, "Disjunction")
        return result905

    def parse_exists(self) -> logic_pb2.Exists:
        span_start908 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1706 = self.parse_bindings()
        bindings906 = _t1706
        _t1707 = self.parse_formula()
        formula907 = _t1707
        self.consume_literal(")")
        _t1708 = logic_pb2.Abstraction(vars=(list(bindings906[0]) + list(bindings906[1] if bindings906[1] is not None else [])), value=formula907)
        _t1709 = logic_pb2.Exists(body=_t1708)
        result909 = _t1709
        self.record_span(span_start908, "Exists")
        return result909

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start913 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1710 = self.parse_abstraction()
        abstraction910 = _t1710
        _t1711 = self.parse_abstraction()
        abstraction_3911 = _t1711
        _t1712 = self.parse_terms()
        terms912 = _t1712
        self.consume_literal(")")
        _t1713 = logic_pb2.Reduce(op=abstraction910, body=abstraction_3911, terms=terms912)
        result914 = _t1713
        self.record_span(span_start913, "Reduce")
        return result914

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs915 = []
        cond916 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond916:
            _t1714 = self.parse_term()
            item917 = _t1714
            xs915.append(item917)
            cond916 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms918 = xs915
        self.consume_literal(")")
        return terms918

    def parse_term(self) -> logic_pb2.Term:
        span_start922 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1715 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1716 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1717 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1718 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1719 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1720 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1721 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1722 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1723 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1724 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1725 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1726 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1727 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1728 = 1
                                                            else:
                                                                _t1728 = -1
                                                            _t1727 = _t1728
                                                        _t1726 = _t1727
                                                    _t1725 = _t1726
                                                _t1724 = _t1725
                                            _t1723 = _t1724
                                        _t1722 = _t1723
                                    _t1721 = _t1722
                                _t1720 = _t1721
                            _t1719 = _t1720
                        _t1718 = _t1719
                    _t1717 = _t1718
                _t1716 = _t1717
            _t1715 = _t1716
        prediction919 = _t1715
        if prediction919 == 1:
            _t1730 = self.parse_value()
            value921 = _t1730
            _t1731 = logic_pb2.Term(constant=value921)
            _t1729 = _t1731
        else:
            if prediction919 == 0:
                _t1733 = self.parse_var()
                var920 = _t1733
                _t1734 = logic_pb2.Term(var=var920)
                _t1732 = _t1734
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1729 = _t1732
        result923 = _t1729
        self.record_span(span_start922, "Term")
        return result923

    def parse_var(self) -> logic_pb2.Var:
        span_start925 = self.span_start()
        symbol924 = self.consume_terminal("SYMBOL")
        _t1735 = logic_pb2.Var(name=symbol924)
        result926 = _t1735
        self.record_span(span_start925, "Var")
        return result926

    def parse_value(self) -> logic_pb2.Value:
        span_start940 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1736 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1737 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1738 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1740 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1741 = 0
                            else:
                                _t1741 = -1
                            _t1740 = _t1741
                        _t1739 = _t1740
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1742 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1743 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1744 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1745 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1746 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1747 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1748 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1749 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1750 = 10
                                                        else:
                                                            _t1750 = -1
                                                        _t1749 = _t1750
                                                    _t1748 = _t1749
                                                _t1747 = _t1748
                                            _t1746 = _t1747
                                        _t1745 = _t1746
                                    _t1744 = _t1745
                                _t1743 = _t1744
                            _t1742 = _t1743
                        _t1739 = _t1742
                    _t1738 = _t1739
                _t1737 = _t1738
            _t1736 = _t1737
        prediction927 = _t1736
        if prediction927 == 12:
            _t1752 = self.parse_boolean_value()
            boolean_value939 = _t1752
            _t1753 = logic_pb2.Value(boolean_value=boolean_value939)
            _t1751 = _t1753
        else:
            if prediction927 == 11:
                self.consume_literal("missing")
                _t1755 = logic_pb2.MissingValue()
                _t1756 = logic_pb2.Value(missing_value=_t1755)
                _t1754 = _t1756
            else:
                if prediction927 == 10:
                    formatted_decimal938 = self.consume_terminal("DECIMAL")
                    _t1758 = logic_pb2.Value(decimal_value=formatted_decimal938)
                    _t1757 = _t1758
                else:
                    if prediction927 == 9:
                        formatted_int128937 = self.consume_terminal("INT128")
                        _t1760 = logic_pb2.Value(int128_value=formatted_int128937)
                        _t1759 = _t1760
                    else:
                        if prediction927 == 8:
                            formatted_uint128936 = self.consume_terminal("UINT128")
                            _t1762 = logic_pb2.Value(uint128_value=formatted_uint128936)
                            _t1761 = _t1762
                        else:
                            if prediction927 == 7:
                                formatted_uint32935 = self.consume_terminal("UINT32")
                                _t1764 = logic_pb2.Value(uint32_value=formatted_uint32935)
                                _t1763 = _t1764
                            else:
                                if prediction927 == 6:
                                    formatted_float934 = self.consume_terminal("FLOAT")
                                    _t1766 = logic_pb2.Value(float_value=formatted_float934)
                                    _t1765 = _t1766
                                else:
                                    if prediction927 == 5:
                                        formatted_float32933 = self.consume_terminal("FLOAT32")
                                        _t1768 = logic_pb2.Value(float32_value=formatted_float32933)
                                        _t1767 = _t1768
                                    else:
                                        if prediction927 == 4:
                                            formatted_int932 = self.consume_terminal("INT")
                                            _t1770 = logic_pb2.Value(int_value=formatted_int932)
                                            _t1769 = _t1770
                                        else:
                                            if prediction927 == 3:
                                                formatted_int32931 = self.consume_terminal("INT32")
                                                _t1772 = logic_pb2.Value(int32_value=formatted_int32931)
                                                _t1771 = _t1772
                                            else:
                                                if prediction927 == 2:
                                                    formatted_string930 = self.consume_terminal("STRING")
                                                    _t1774 = logic_pb2.Value(string_value=formatted_string930)
                                                    _t1773 = _t1774
                                                else:
                                                    if prediction927 == 1:
                                                        _t1776 = self.parse_datetime()
                                                        datetime929 = _t1776
                                                        _t1777 = logic_pb2.Value(datetime_value=datetime929)
                                                        _t1775 = _t1777
                                                    else:
                                                        if prediction927 == 0:
                                                            _t1779 = self.parse_date()
                                                            date928 = _t1779
                                                            _t1780 = logic_pb2.Value(date_value=date928)
                                                            _t1778 = _t1780
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1775 = _t1778
                                                    _t1773 = _t1775
                                                _t1771 = _t1773
                                            _t1769 = _t1771
                                        _t1767 = _t1769
                                    _t1765 = _t1767
                                _t1763 = _t1765
                            _t1761 = _t1763
                        _t1759 = _t1761
                    _t1757 = _t1759
                _t1754 = _t1757
            _t1751 = _t1754
        result941 = _t1751
        self.record_span(span_start940, "Value")
        return result941

    def parse_date(self) -> logic_pb2.DateValue:
        span_start945 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int942 = self.consume_terminal("INT")
        formatted_int_3943 = self.consume_terminal("INT")
        formatted_int_4944 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1781 = logic_pb2.DateValue(year=int(formatted_int942), month=int(formatted_int_3943), day=int(formatted_int_4944))
        result946 = _t1781
        self.record_span(span_start945, "DateValue")
        return result946

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start954 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int947 = self.consume_terminal("INT")
        formatted_int_3948 = self.consume_terminal("INT")
        formatted_int_4949 = self.consume_terminal("INT")
        formatted_int_5950 = self.consume_terminal("INT")
        formatted_int_6951 = self.consume_terminal("INT")
        formatted_int_7952 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1782 = self.consume_terminal("INT")
        else:
            _t1782 = None
        formatted_int_8953 = _t1782
        self.consume_literal(")")
        _t1783 = logic_pb2.DateTimeValue(year=int(formatted_int947), month=int(formatted_int_3948), day=int(formatted_int_4949), hour=int(formatted_int_5950), minute=int(formatted_int_6951), second=int(formatted_int_7952), microsecond=int((formatted_int_8953 if formatted_int_8953 is not None else 0)))
        result955 = _t1783
        self.record_span(span_start954, "DateTimeValue")
        return result955

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start960 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs956 = []
        cond957 = self.match_lookahead_literal("(", 0)
        while cond957:
            _t1784 = self.parse_formula()
            item958 = _t1784
            xs956.append(item958)
            cond957 = self.match_lookahead_literal("(", 0)
        formulas959 = xs956
        self.consume_literal(")")
        _t1785 = logic_pb2.Conjunction(args=formulas959)
        result961 = _t1785
        self.record_span(span_start960, "Conjunction")
        return result961

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start966 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs962 = []
        cond963 = self.match_lookahead_literal("(", 0)
        while cond963:
            _t1786 = self.parse_formula()
            item964 = _t1786
            xs962.append(item964)
            cond963 = self.match_lookahead_literal("(", 0)
        formulas965 = xs962
        self.consume_literal(")")
        _t1787 = logic_pb2.Disjunction(args=formulas965)
        result967 = _t1787
        self.record_span(span_start966, "Disjunction")
        return result967

    def parse_not(self) -> logic_pb2.Not:
        span_start969 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1788 = self.parse_formula()
        formula968 = _t1788
        self.consume_literal(")")
        _t1789 = logic_pb2.Not(arg=formula968)
        result970 = _t1789
        self.record_span(span_start969, "Not")
        return result970

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start974 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1790 = self.parse_name()
        name971 = _t1790
        _t1791 = self.parse_ffi_args()
        ffi_args972 = _t1791
        _t1792 = self.parse_terms()
        terms973 = _t1792
        self.consume_literal(")")
        _t1793 = logic_pb2.FFI(name=name971, args=ffi_args972, terms=terms973)
        result975 = _t1793
        self.record_span(span_start974, "FFI")
        return result975

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol976 = self.consume_terminal("SYMBOL")
        return symbol976

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs977 = []
        cond978 = self.match_lookahead_literal("(", 0)
        while cond978:
            _t1794 = self.parse_abstraction()
            item979 = _t1794
            xs977.append(item979)
            cond978 = self.match_lookahead_literal("(", 0)
        abstractions980 = xs977
        self.consume_literal(")")
        return abstractions980

    def parse_atom(self) -> logic_pb2.Atom:
        span_start986 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1795 = self.parse_relation_id()
        relation_id981 = _t1795
        xs982 = []
        cond983 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond983:
            _t1796 = self.parse_term()
            item984 = _t1796
            xs982.append(item984)
            cond983 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms985 = xs982
        self.consume_literal(")")
        _t1797 = logic_pb2.Atom(name=relation_id981, terms=terms985)
        result987 = _t1797
        self.record_span(span_start986, "Atom")
        return result987

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start993 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1798 = self.parse_name()
        name988 = _t1798
        xs989 = []
        cond990 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond990:
            _t1799 = self.parse_term()
            item991 = _t1799
            xs989.append(item991)
            cond990 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms992 = xs989
        self.consume_literal(")")
        _t1800 = logic_pb2.Pragma(name=name988, terms=terms992)
        result994 = _t1800
        self.record_span(span_start993, "Pragma")
        return result994

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start1010 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1802 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1803 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1804 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1805 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1806 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1807 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1808 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1809 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1810 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1811 = 7
                                                else:
                                                    _t1811 = -1
                                                _t1810 = _t1811
                                            _t1809 = _t1810
                                        _t1808 = _t1809
                                    _t1807 = _t1808
                                _t1806 = _t1807
                            _t1805 = _t1806
                        _t1804 = _t1805
                    _t1803 = _t1804
                _t1802 = _t1803
            _t1801 = _t1802
        else:
            _t1801 = -1
        prediction995 = _t1801
        if prediction995 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1813 = self.parse_name()
            name1005 = _t1813
            xs1006 = []
            cond1007 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond1007:
                _t1814 = self.parse_rel_term()
                item1008 = _t1814
                xs1006.append(item1008)
                cond1007 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms1009 = xs1006
            self.consume_literal(")")
            _t1815 = logic_pb2.Primitive(name=name1005, terms=rel_terms1009)
            _t1812 = _t1815
        else:
            if prediction995 == 8:
                _t1817 = self.parse_divide()
                divide1004 = _t1817
                _t1816 = divide1004
            else:
                if prediction995 == 7:
                    _t1819 = self.parse_multiply()
                    multiply1003 = _t1819
                    _t1818 = multiply1003
                else:
                    if prediction995 == 6:
                        _t1821 = self.parse_minus()
                        minus1002 = _t1821
                        _t1820 = minus1002
                    else:
                        if prediction995 == 5:
                            _t1823 = self.parse_add()
                            add1001 = _t1823
                            _t1822 = add1001
                        else:
                            if prediction995 == 4:
                                _t1825 = self.parse_gt_eq()
                                gt_eq1000 = _t1825
                                _t1824 = gt_eq1000
                            else:
                                if prediction995 == 3:
                                    _t1827 = self.parse_gt()
                                    gt999 = _t1827
                                    _t1826 = gt999
                                else:
                                    if prediction995 == 2:
                                        _t1829 = self.parse_lt_eq()
                                        lt_eq998 = _t1829
                                        _t1828 = lt_eq998
                                    else:
                                        if prediction995 == 1:
                                            _t1831 = self.parse_lt()
                                            lt997 = _t1831
                                            _t1830 = lt997
                                        else:
                                            if prediction995 == 0:
                                                _t1833 = self.parse_eq()
                                                eq996 = _t1833
                                                _t1832 = eq996
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1830 = _t1832
                                        _t1828 = _t1830
                                    _t1826 = _t1828
                                _t1824 = _t1826
                            _t1822 = _t1824
                        _t1820 = _t1822
                    _t1818 = _t1820
                _t1816 = _t1818
            _t1812 = _t1816
        result1011 = _t1812
        self.record_span(span_start1010, "Primitive")
        return result1011

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start1014 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1834 = self.parse_term()
        term1012 = _t1834
        _t1835 = self.parse_term()
        term_31013 = _t1835
        self.consume_literal(")")
        _t1836 = logic_pb2.RelTerm(term=term1012)
        _t1837 = logic_pb2.RelTerm(term=term_31013)
        _t1838 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1836, _t1837])
        result1015 = _t1838
        self.record_span(span_start1014, "Primitive")
        return result1015

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start1018 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1839 = self.parse_term()
        term1016 = _t1839
        _t1840 = self.parse_term()
        term_31017 = _t1840
        self.consume_literal(")")
        _t1841 = logic_pb2.RelTerm(term=term1016)
        _t1842 = logic_pb2.RelTerm(term=term_31017)
        _t1843 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1841, _t1842])
        result1019 = _t1843
        self.record_span(span_start1018, "Primitive")
        return result1019

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start1022 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1844 = self.parse_term()
        term1020 = _t1844
        _t1845 = self.parse_term()
        term_31021 = _t1845
        self.consume_literal(")")
        _t1846 = logic_pb2.RelTerm(term=term1020)
        _t1847 = logic_pb2.RelTerm(term=term_31021)
        _t1848 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1846, _t1847])
        result1023 = _t1848
        self.record_span(span_start1022, "Primitive")
        return result1023

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start1026 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1849 = self.parse_term()
        term1024 = _t1849
        _t1850 = self.parse_term()
        term_31025 = _t1850
        self.consume_literal(")")
        _t1851 = logic_pb2.RelTerm(term=term1024)
        _t1852 = logic_pb2.RelTerm(term=term_31025)
        _t1853 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1851, _t1852])
        result1027 = _t1853
        self.record_span(span_start1026, "Primitive")
        return result1027

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start1030 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1854 = self.parse_term()
        term1028 = _t1854
        _t1855 = self.parse_term()
        term_31029 = _t1855
        self.consume_literal(")")
        _t1856 = logic_pb2.RelTerm(term=term1028)
        _t1857 = logic_pb2.RelTerm(term=term_31029)
        _t1858 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1856, _t1857])
        result1031 = _t1858
        self.record_span(span_start1030, "Primitive")
        return result1031

    def parse_add(self) -> logic_pb2.Primitive:
        span_start1035 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1859 = self.parse_term()
        term1032 = _t1859
        _t1860 = self.parse_term()
        term_31033 = _t1860
        _t1861 = self.parse_term()
        term_41034 = _t1861
        self.consume_literal(")")
        _t1862 = logic_pb2.RelTerm(term=term1032)
        _t1863 = logic_pb2.RelTerm(term=term_31033)
        _t1864 = logic_pb2.RelTerm(term=term_41034)
        _t1865 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1862, _t1863, _t1864])
        result1036 = _t1865
        self.record_span(span_start1035, "Primitive")
        return result1036

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start1040 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1866 = self.parse_term()
        term1037 = _t1866
        _t1867 = self.parse_term()
        term_31038 = _t1867
        _t1868 = self.parse_term()
        term_41039 = _t1868
        self.consume_literal(")")
        _t1869 = logic_pb2.RelTerm(term=term1037)
        _t1870 = logic_pb2.RelTerm(term=term_31038)
        _t1871 = logic_pb2.RelTerm(term=term_41039)
        _t1872 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1869, _t1870, _t1871])
        result1041 = _t1872
        self.record_span(span_start1040, "Primitive")
        return result1041

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start1045 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1873 = self.parse_term()
        term1042 = _t1873
        _t1874 = self.parse_term()
        term_31043 = _t1874
        _t1875 = self.parse_term()
        term_41044 = _t1875
        self.consume_literal(")")
        _t1876 = logic_pb2.RelTerm(term=term1042)
        _t1877 = logic_pb2.RelTerm(term=term_31043)
        _t1878 = logic_pb2.RelTerm(term=term_41044)
        _t1879 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1876, _t1877, _t1878])
        result1046 = _t1879
        self.record_span(span_start1045, "Primitive")
        return result1046

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start1050 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1880 = self.parse_term()
        term1047 = _t1880
        _t1881 = self.parse_term()
        term_31048 = _t1881
        _t1882 = self.parse_term()
        term_41049 = _t1882
        self.consume_literal(")")
        _t1883 = logic_pb2.RelTerm(term=term1047)
        _t1884 = logic_pb2.RelTerm(term=term_31048)
        _t1885 = logic_pb2.RelTerm(term=term_41049)
        _t1886 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1883, _t1884, _t1885])
        result1051 = _t1886
        self.record_span(span_start1050, "Primitive")
        return result1051

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1055 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1887 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1888 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1889 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1890 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1891 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1892 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1893 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1894 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1895 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1896 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1897 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1898 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1899 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1900 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1901 = 1
                                                                else:
                                                                    _t1901 = -1
                                                                _t1900 = _t1901
                                                            _t1899 = _t1900
                                                        _t1898 = _t1899
                                                    _t1897 = _t1898
                                                _t1896 = _t1897
                                            _t1895 = _t1896
                                        _t1894 = _t1895
                                    _t1893 = _t1894
                                _t1892 = _t1893
                            _t1891 = _t1892
                        _t1890 = _t1891
                    _t1889 = _t1890
                _t1888 = _t1889
            _t1887 = _t1888
        prediction1052 = _t1887
        if prediction1052 == 1:
            _t1903 = self.parse_term()
            term1054 = _t1903
            _t1904 = logic_pb2.RelTerm(term=term1054)
            _t1902 = _t1904
        else:
            if prediction1052 == 0:
                _t1906 = self.parse_specialized_value()
                specialized_value1053 = _t1906
                _t1907 = logic_pb2.RelTerm(specialized_value=specialized_value1053)
                _t1905 = _t1907
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1902 = _t1905
        result1056 = _t1902
        self.record_span(span_start1055, "RelTerm")
        return result1056

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1058 = self.span_start()
        self.consume_literal("#")
        _t1908 = self.parse_raw_value()
        raw_value1057 = _t1908
        result1059 = raw_value1057
        self.record_span(span_start1058, "Value")
        return result1059

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1065 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1909 = self.parse_name()
        name1060 = _t1909
        xs1061 = []
        cond1062 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1062:
            _t1910 = self.parse_rel_term()
            item1063 = _t1910
            xs1061.append(item1063)
            cond1062 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1064 = xs1061
        self.consume_literal(")")
        _t1911 = logic_pb2.RelAtom(name=name1060, terms=rel_terms1064)
        result1066 = _t1911
        self.record_span(span_start1065, "RelAtom")
        return result1066

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1069 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1912 = self.parse_term()
        term1067 = _t1912
        _t1913 = self.parse_term()
        term_31068 = _t1913
        self.consume_literal(")")
        _t1914 = logic_pb2.Cast(input=term1067, result=term_31068)
        result1070 = _t1914
        self.record_span(span_start1069, "Cast")
        return result1070

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1071 = []
        cond1072 = self.match_lookahead_literal("(", 0)
        while cond1072:
            _t1915 = self.parse_attribute()
            item1073 = _t1915
            xs1071.append(item1073)
            cond1072 = self.match_lookahead_literal("(", 0)
        attributes1074 = xs1071
        self.consume_literal(")")
        return attributes1074

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1080 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1916 = self.parse_name()
        name1075 = _t1916
        xs1076 = []
        cond1077 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1077:
            _t1917 = self.parse_raw_value()
            item1078 = _t1917
            xs1076.append(item1078)
            cond1077 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1079 = xs1076
        self.consume_literal(")")
        _t1918 = logic_pb2.Attribute(name=name1075, args=raw_values1079)
        result1081 = _t1918
        self.record_span(span_start1080, "Attribute")
        return result1081

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1088 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1082 = []
        cond1083 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1083:
            _t1919 = self.parse_relation_id()
            item1084 = _t1919
            xs1082.append(item1084)
            cond1083 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1085 = xs1082
        _t1920 = self.parse_script()
        script1086 = _t1920
        if self.match_lookahead_literal("(", 0):
            _t1922 = self.parse_attrs()
            _t1921 = _t1922
        else:
            _t1921 = None
        attrs1087 = _t1921
        self.consume_literal(")")
        _t1923 = logic_pb2.Algorithm(body=script1086, attrs=(attrs1087 if attrs1087 is not None else []))
        getattr(_t1923, 'global').extend(relation_ids1085)
        result1089 = _t1923
        self.record_span(span_start1088, "Algorithm")
        return result1089

    def parse_script(self) -> logic_pb2.Script:
        span_start1094 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1090 = []
        cond1091 = self.match_lookahead_literal("(", 0)
        while cond1091:
            _t1924 = self.parse_construct()
            item1092 = _t1924
            xs1090.append(item1092)
            cond1091 = self.match_lookahead_literal("(", 0)
        constructs1093 = xs1090
        self.consume_literal(")")
        _t1925 = logic_pb2.Script(constructs=constructs1093)
        result1095 = _t1925
        self.record_span(span_start1094, "Script")
        return result1095

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1099 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1927 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1928 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1929 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1930 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1931 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1932 = 1
                                else:
                                    _t1932 = -1
                                _t1931 = _t1932
                            _t1930 = _t1931
                        _t1929 = _t1930
                    _t1928 = _t1929
                _t1927 = _t1928
            _t1926 = _t1927
        else:
            _t1926 = -1
        prediction1096 = _t1926
        if prediction1096 == 1:
            _t1934 = self.parse_instruction()
            instruction1098 = _t1934
            _t1935 = logic_pb2.Construct(instruction=instruction1098)
            _t1933 = _t1935
        else:
            if prediction1096 == 0:
                _t1937 = self.parse_loop()
                loop1097 = _t1937
                _t1938 = logic_pb2.Construct(loop=loop1097)
                _t1936 = _t1938
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1933 = _t1936
        result1100 = _t1933
        self.record_span(span_start1099, "Construct")
        return result1100

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1104 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1939 = self.parse_init()
        init1101 = _t1939
        _t1940 = self.parse_script()
        script1102 = _t1940
        if self.match_lookahead_literal("(", 0):
            _t1942 = self.parse_attrs()
            _t1941 = _t1942
        else:
            _t1941 = None
        attrs1103 = _t1941
        self.consume_literal(")")
        _t1943 = logic_pb2.Loop(init=init1101, body=script1102, attrs=(attrs1103 if attrs1103 is not None else []))
        result1105 = _t1943
        self.record_span(span_start1104, "Loop")
        return result1105

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1106 = []
        cond1107 = self.match_lookahead_literal("(", 0)
        while cond1107:
            _t1944 = self.parse_instruction()
            item1108 = _t1944
            xs1106.append(item1108)
            cond1107 = self.match_lookahead_literal("(", 0)
        instructions1109 = xs1106
        self.consume_literal(")")
        return instructions1109

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1116 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1946 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1947 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1948 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1949 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1950 = 0
                            else:
                                _t1950 = -1
                            _t1949 = _t1950
                        _t1948 = _t1949
                    _t1947 = _t1948
                _t1946 = _t1947
            _t1945 = _t1946
        else:
            _t1945 = -1
        prediction1110 = _t1945
        if prediction1110 == 4:
            _t1952 = self.parse_monus_def()
            monus_def1115 = _t1952
            _t1953 = logic_pb2.Instruction(monus_def=monus_def1115)
            _t1951 = _t1953
        else:
            if prediction1110 == 3:
                _t1955 = self.parse_monoid_def()
                monoid_def1114 = _t1955
                _t1956 = logic_pb2.Instruction(monoid_def=monoid_def1114)
                _t1954 = _t1956
            else:
                if prediction1110 == 2:
                    _t1958 = self.parse_break()
                    break1113 = _t1958
                    _t1959 = logic_pb2.Instruction()
                    getattr(_t1959, 'break').CopyFrom(break1113)
                    _t1957 = _t1959
                else:
                    if prediction1110 == 1:
                        _t1961 = self.parse_upsert()
                        upsert1112 = _t1961
                        _t1962 = logic_pb2.Instruction(upsert=upsert1112)
                        _t1960 = _t1962
                    else:
                        if prediction1110 == 0:
                            _t1964 = self.parse_assign()
                            assign1111 = _t1964
                            _t1965 = logic_pb2.Instruction(assign=assign1111)
                            _t1963 = _t1965
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1960 = _t1963
                    _t1957 = _t1960
                _t1954 = _t1957
            _t1951 = _t1954
        result1117 = _t1951
        self.record_span(span_start1116, "Instruction")
        return result1117

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1121 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1966 = self.parse_relation_id()
        relation_id1118 = _t1966
        _t1967 = self.parse_abstraction()
        abstraction1119 = _t1967
        if self.match_lookahead_literal("(", 0):
            _t1969 = self.parse_attrs()
            _t1968 = _t1969
        else:
            _t1968 = None
        attrs1120 = _t1968
        self.consume_literal(")")
        _t1970 = logic_pb2.Assign(name=relation_id1118, body=abstraction1119, attrs=(attrs1120 if attrs1120 is not None else []))
        result1122 = _t1970
        self.record_span(span_start1121, "Assign")
        return result1122

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1126 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1971 = self.parse_relation_id()
        relation_id1123 = _t1971
        _t1972 = self.parse_abstraction_with_arity()
        abstraction_with_arity1124 = _t1972
        if self.match_lookahead_literal("(", 0):
            _t1974 = self.parse_attrs()
            _t1973 = _t1974
        else:
            _t1973 = None
        attrs1125 = _t1973
        self.consume_literal(")")
        _t1975 = logic_pb2.Upsert(name=relation_id1123, body=abstraction_with_arity1124[0], attrs=(attrs1125 if attrs1125 is not None else []), value_arity=abstraction_with_arity1124[1])
        result1127 = _t1975
        self.record_span(span_start1126, "Upsert")
        return result1127

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1976 = self.parse_bindings()
        bindings1128 = _t1976
        _t1977 = self.parse_formula()
        formula1129 = _t1977
        self.consume_literal(")")
        _t1978 = logic_pb2.Abstraction(vars=(list(bindings1128[0]) + list(bindings1128[1] if bindings1128[1] is not None else [])), value=formula1129)
        return (_t1978, len(bindings1128[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1133 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1979 = self.parse_relation_id()
        relation_id1130 = _t1979
        _t1980 = self.parse_abstraction()
        abstraction1131 = _t1980
        if self.match_lookahead_literal("(", 0):
            _t1982 = self.parse_attrs()
            _t1981 = _t1982
        else:
            _t1981 = None
        attrs1132 = _t1981
        self.consume_literal(")")
        _t1983 = logic_pb2.Break(name=relation_id1130, body=abstraction1131, attrs=(attrs1132 if attrs1132 is not None else []))
        result1134 = _t1983
        self.record_span(span_start1133, "Break")
        return result1134

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1139 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1984 = self.parse_monoid()
        monoid1135 = _t1984
        _t1985 = self.parse_relation_id()
        relation_id1136 = _t1985
        _t1986 = self.parse_abstraction_with_arity()
        abstraction_with_arity1137 = _t1986
        if self.match_lookahead_literal("(", 0):
            _t1988 = self.parse_attrs()
            _t1987 = _t1988
        else:
            _t1987 = None
        attrs1138 = _t1987
        self.consume_literal(")")
        _t1989 = logic_pb2.MonoidDef(monoid=monoid1135, name=relation_id1136, body=abstraction_with_arity1137[0], attrs=(attrs1138 if attrs1138 is not None else []), value_arity=abstraction_with_arity1137[1])
        result1140 = _t1989
        self.record_span(span_start1139, "MonoidDef")
        return result1140

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1146 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1991 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1992 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1993 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1994 = 2
                        else:
                            _t1994 = -1
                        _t1993 = _t1994
                    _t1992 = _t1993
                _t1991 = _t1992
            _t1990 = _t1991
        else:
            _t1990 = -1
        prediction1141 = _t1990
        if prediction1141 == 3:
            _t1996 = self.parse_sum_monoid()
            sum_monoid1145 = _t1996
            _t1997 = logic_pb2.Monoid(sum_monoid=sum_monoid1145)
            _t1995 = _t1997
        else:
            if prediction1141 == 2:
                _t1999 = self.parse_max_monoid()
                max_monoid1144 = _t1999
                _t2000 = logic_pb2.Monoid(max_monoid=max_monoid1144)
                _t1998 = _t2000
            else:
                if prediction1141 == 1:
                    _t2002 = self.parse_min_monoid()
                    min_monoid1143 = _t2002
                    _t2003 = logic_pb2.Monoid(min_monoid=min_monoid1143)
                    _t2001 = _t2003
                else:
                    if prediction1141 == 0:
                        _t2005 = self.parse_or_monoid()
                        or_monoid1142 = _t2005
                        _t2006 = logic_pb2.Monoid(or_monoid=or_monoid1142)
                        _t2004 = _t2006
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t2001 = _t2004
                _t1998 = _t2001
            _t1995 = _t1998
        result1147 = _t1995
        self.record_span(span_start1146, "Monoid")
        return result1147

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1148 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t2007 = logic_pb2.OrMonoid()
        result1149 = _t2007
        self.record_span(span_start1148, "OrMonoid")
        return result1149

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1151 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t2008 = self.parse_type()
        type1150 = _t2008
        self.consume_literal(")")
        _t2009 = logic_pb2.MinMonoid(type=type1150)
        result1152 = _t2009
        self.record_span(span_start1151, "MinMonoid")
        return result1152

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1154 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t2010 = self.parse_type()
        type1153 = _t2010
        self.consume_literal(")")
        _t2011 = logic_pb2.MaxMonoid(type=type1153)
        result1155 = _t2011
        self.record_span(span_start1154, "MaxMonoid")
        return result1155

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1157 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t2012 = self.parse_type()
        type1156 = _t2012
        self.consume_literal(")")
        _t2013 = logic_pb2.SumMonoid(type=type1156)
        result1158 = _t2013
        self.record_span(span_start1157, "SumMonoid")
        return result1158

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1163 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t2014 = self.parse_monoid()
        monoid1159 = _t2014
        _t2015 = self.parse_relation_id()
        relation_id1160 = _t2015
        _t2016 = self.parse_abstraction_with_arity()
        abstraction_with_arity1161 = _t2016
        if self.match_lookahead_literal("(", 0):
            _t2018 = self.parse_attrs()
            _t2017 = _t2018
        else:
            _t2017 = None
        attrs1162 = _t2017
        self.consume_literal(")")
        _t2019 = logic_pb2.MonusDef(monoid=monoid1159, name=relation_id1160, body=abstraction_with_arity1161[0], attrs=(attrs1162 if attrs1162 is not None else []), value_arity=abstraction_with_arity1161[1])
        result1164 = _t2019
        self.record_span(span_start1163, "MonusDef")
        return result1164

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1169 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t2020 = self.parse_relation_id()
        relation_id1165 = _t2020
        _t2021 = self.parse_abstraction()
        abstraction1166 = _t2021
        _t2022 = self.parse_functional_dependency_keys()
        functional_dependency_keys1167 = _t2022
        _t2023 = self.parse_functional_dependency_values()
        functional_dependency_values1168 = _t2023
        self.consume_literal(")")
        _t2024 = logic_pb2.FunctionalDependency(guard=abstraction1166, keys=functional_dependency_keys1167, values=functional_dependency_values1168)
        _t2025 = logic_pb2.Constraint(name=relation_id1165, functional_dependency=_t2024)
        result1170 = _t2025
        self.record_span(span_start1169, "Constraint")
        return result1170

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1171 = []
        cond1172 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1172:
            _t2026 = self.parse_var()
            item1173 = _t2026
            xs1171.append(item1173)
            cond1172 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1174 = xs1171
        self.consume_literal(")")
        return vars1174

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1175 = []
        cond1176 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1176:
            _t2027 = self.parse_var()
            item1177 = _t2027
            xs1175.append(item1177)
            cond1176 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1178 = xs1175
        self.consume_literal(")")
        return vars1178

    def parse_data(self) -> logic_pb2.Data:
        span_start1184 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t2029 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t2030 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t2031 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t2032 = 1
                        else:
                            _t2032 = -1
                        _t2031 = _t2032
                    _t2030 = _t2031
                _t2029 = _t2030
            _t2028 = _t2029
        else:
            _t2028 = -1
        prediction1179 = _t2028
        if prediction1179 == 3:
            _t2034 = self.parse_iceberg_data()
            iceberg_data1183 = _t2034
            _t2035 = logic_pb2.Data(iceberg_data=iceberg_data1183)
            _t2033 = _t2035
        else:
            if prediction1179 == 2:
                _t2037 = self.parse_csv_data()
                csv_data1182 = _t2037
                _t2038 = logic_pb2.Data(csv_data=csv_data1182)
                _t2036 = _t2038
            else:
                if prediction1179 == 1:
                    _t2040 = self.parse_betree_relation()
                    betree_relation1181 = _t2040
                    _t2041 = logic_pb2.Data(betree_relation=betree_relation1181)
                    _t2039 = _t2041
                else:
                    if prediction1179 == 0:
                        _t2043 = self.parse_edb()
                        edb1180 = _t2043
                        _t2044 = logic_pb2.Data(edb=edb1180)
                        _t2042 = _t2044
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t2039 = _t2042
                _t2036 = _t2039
            _t2033 = _t2036
        result1185 = _t2033
        self.record_span(span_start1184, "Data")
        return result1185

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1189 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t2045 = self.parse_relation_id()
        relation_id1186 = _t2045
        _t2046 = self.parse_edb_path()
        edb_path1187 = _t2046
        _t2047 = self.parse_edb_types()
        edb_types1188 = _t2047
        self.consume_literal(")")
        _t2048 = logic_pb2.EDB(target_id=relation_id1186, path=edb_path1187, types=edb_types1188)
        result1190 = _t2048
        self.record_span(span_start1189, "EDB")
        return result1190

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1191 = []
        cond1192 = self.match_lookahead_terminal("STRING", 0)
        while cond1192:
            item1193 = self.consume_terminal("STRING")
            xs1191.append(item1193)
            cond1192 = self.match_lookahead_terminal("STRING", 0)
        strings1194 = xs1191
        self.consume_literal("]")
        return strings1194

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1195 = []
        cond1196 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1196:
            _t2049 = self.parse_type()
            item1197 = _t2049
            xs1195.append(item1197)
            cond1196 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1198 = xs1195
        self.consume_literal("]")
        return types1198

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1201 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t2050 = self.parse_relation_id()
        relation_id1199 = _t2050
        _t2051 = self.parse_betree_info()
        betree_info1200 = _t2051
        self.consume_literal(")")
        _t2052 = logic_pb2.BeTreeRelation(name=relation_id1199, relation_info=betree_info1200)
        result1202 = _t2052
        self.record_span(span_start1201, "BeTreeRelation")
        return result1202

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1206 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t2053 = self.parse_betree_info_key_types()
        betree_info_key_types1203 = _t2053
        _t2054 = self.parse_betree_info_value_types()
        betree_info_value_types1204 = _t2054
        _t2055 = self.parse_config_dict()
        config_dict1205 = _t2055
        self.consume_literal(")")
        _t2056 = self.construct_betree_info(betree_info_key_types1203, betree_info_value_types1204, config_dict1205)
        result1207 = _t2056
        self.record_span(span_start1206, "BeTreeInfo")
        return result1207

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1208 = []
        cond1209 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1209:
            _t2057 = self.parse_type()
            item1210 = _t2057
            xs1208.append(item1210)
            cond1209 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1211 = xs1208
        self.consume_literal(")")
        return types1211

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1212 = []
        cond1213 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1213:
            _t2058 = self.parse_type()
            item1214 = _t2058
            xs1212.append(item1214)
            cond1213 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1215 = xs1212
        self.consume_literal(")")
        return types1215

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1221 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t2059 = self.parse_csvlocator()
        csvlocator1216 = _t2059
        _t2060 = self.parse_csv_config()
        csv_config1217 = _t2060
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("columns", 1)):
            _t2062 = self.parse_gnf_columns()
            _t2061 = _t2062
        else:
            _t2061 = None
        gnf_columns1218 = _t2061
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("relations", 1)):
            _t2064 = self.parse_target_relations()
            _t2063 = _t2064
        else:
            _t2063 = None
        target_relations1219 = _t2063
        _t2065 = self.parse_csv_asof()
        csv_asof1220 = _t2065
        self.consume_literal(")")
        _t2066 = self.construct_csv_data(csvlocator1216, csv_config1217, gnf_columns1218, target_relations1219, csv_asof1220)
        result1222 = _t2066
        self.record_span(span_start1221, "CSVData")
        return result1222

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1225 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t2068 = self.parse_csv_locator_paths()
            _t2067 = _t2068
        else:
            _t2067 = None
        csv_locator_paths1223 = _t2067
        if self.match_lookahead_literal("(", 0):
            _t2070 = self.parse_csv_locator_inline_data()
            _t2069 = _t2070
        else:
            _t2069 = None
        csv_locator_inline_data1224 = _t2069
        self.consume_literal(")")
        _t2071 = logic_pb2.CSVLocator(paths=(csv_locator_paths1223 if csv_locator_paths1223 is not None else []), inline_data=(csv_locator_inline_data1224 if csv_locator_inline_data1224 is not None else "").encode())
        result1226 = _t2071
        self.record_span(span_start1225, "CSVLocator")
        return result1226

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1227 = []
        cond1228 = self.match_lookahead_terminal("STRING", 0)
        while cond1228:
            item1229 = self.consume_terminal("STRING")
            xs1227.append(item1229)
            cond1228 = self.match_lookahead_terminal("STRING", 0)
        strings1230 = xs1227
        self.consume_literal(")")
        return strings1230

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        formatted_string1231 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return formatted_string1231

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1234 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t2072 = self.parse_config_dict()
        config_dict1232 = _t2072
        if self.match_lookahead_literal("(", 0):
            _t2074 = self.parse__storage_integration()
            _t2073 = _t2074
        else:
            _t2073 = None
        _storage_integration1233 = _t2073
        self.consume_literal(")")
        _t2075 = self.construct_csv_config(config_dict1232, _storage_integration1233)
        result1235 = _t2075
        self.record_span(span_start1234, "CSVConfig")
        return result1235

    def parse__storage_integration(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("(")
        self.consume_literal("storage_integration")
        _t2076 = self.parse_config_dict()
        config_dict1236 = _t2076
        self.consume_literal(")")
        return config_dict1236

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1237 = []
        cond1238 = self.match_lookahead_literal("(", 0)
        while cond1238:
            _t2077 = self.parse_gnf_column()
            item1239 = _t2077
            xs1237.append(item1239)
            cond1238 = self.match_lookahead_literal("(", 0)
        gnf_columns1240 = xs1237
        self.consume_literal(")")
        return gnf_columns1240

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1247 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t2078 = self.parse_gnf_column_path()
        gnf_column_path1241 = _t2078
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t2080 = self.parse_relation_id()
            _t2079 = _t2080
        else:
            _t2079 = None
        relation_id1242 = _t2079
        self.consume_literal("[")
        xs1243 = []
        cond1244 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1244:
            _t2081 = self.parse_type()
            item1245 = _t2081
            xs1243.append(item1245)
            cond1244 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1246 = xs1243
        self.consume_literal("]")
        self.consume_literal(")")
        _t2082 = logic_pb2.GNFColumn(column_path=gnf_column_path1241, target_id=relation_id1242, types=types1246)
        result1248 = _t2082
        self.record_span(span_start1247, "GNFColumn")
        return result1248

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t2083 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t2084 = 0
            else:
                _t2084 = -1
            _t2083 = _t2084
        prediction1249 = _t2083
        if prediction1249 == 1:
            self.consume_literal("[")
            xs1251 = []
            cond1252 = self.match_lookahead_terminal("STRING", 0)
            while cond1252:
                item1253 = self.consume_terminal("STRING")
                xs1251.append(item1253)
                cond1252 = self.match_lookahead_terminal("STRING", 0)
            strings1254 = xs1251
            self.consume_literal("]")
            _t2085 = strings1254
        else:
            if prediction1249 == 0:
                string1250 = self.consume_terminal("STRING")
                _t2086 = [string1250]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2085 = _t2086
        return _t2085

    def parse_target_relations(self) -> logic_pb2.TargetRelations:
        span_start1258 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relations")
        _t2087 = self.parse_relation_keys()
        relation_keys1255 = _t2087
        _t2088 = self.parse_relation_body()
        relation_body1256 = _t2088
        if self.match_lookahead_literal("(", 0):
            _t2090 = self.parse_load_errors()
            _t2089 = _t2090
        else:
            _t2089 = None
        load_errors1257 = _t2089
        self.consume_literal(")")
        _t2091 = self.construct_relations(relation_keys1255, relation_body1256, load_errors1257)
        result1259 = _t2091
        self.record_span(span_start1258, "TargetRelations")
        return result1259

    def parse_relation_keys(self) -> tuple[Sequence[logic_pb2.NamedColumn], bool]:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("keys", 1):
                if self.match_lookahead_literal("synthetic", 2):
                    _t2094 = 1
                else:
                    if self.match_lookahead_literal(")", 2):
                        _t2095 = 0
                    else:
                        if self.match_lookahead_literal("(", 2):
                            _t2096 = 0
                        else:
                            _t2096 = -1
                        _t2095 = _t2096
                    _t2094 = _t2095
                _t2093 = _t2094
            else:
                _t2093 = -1
            _t2092 = _t2093
        else:
            _t2092 = -1
        prediction1260 = _t2092
        if prediction1260 == 1:
            self.consume_literal("(")
            self.consume_literal("keys")
            self.consume_literal("synthetic")
            self.consume_literal(")")
            _t2097 = ([], True,)
        else:
            if prediction1260 == 0:
                self.consume_literal("(")
                self.consume_literal("keys")
                xs1261 = []
                cond1262 = self.match_lookahead_literal("(", 0)
                while cond1262:
                    _t2099 = self.parse_named_column()
                    item1263 = _t2099
                    xs1261.append(item1263)
                    cond1262 = self.match_lookahead_literal("(", 0)
                named_columns1264 = xs1261
                self.consume_literal(")")
                _t2098 = (named_columns1264, False,)
            else:
                raise ParseError("Unexpected token in relation_keys" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2097 = _t2098
        return _t2097

    def parse_named_column(self) -> logic_pb2.NamedColumn:
        span_start1267 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1265 = self.consume_terminal("STRING")
        _t2100 = self.parse_type()
        type1266 = _t2100
        self.consume_literal(")")
        _t2101 = logic_pb2.NamedColumn(name=string1265, type=type1266)
        result1268 = _t2101
        self.record_span(span_start1267, "NamedColumn")
        return result1268

    def parse_relation_body(self) -> logic_pb2.TargetRelations:
        span_start1273 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("relation", 1):
                _t2103 = 0
            else:
                if self.match_lookahead_literal("inserts", 1):
                    _t2104 = 1
                else:
                    _t2104 = 0
                _t2103 = _t2104
            _t2102 = _t2103
        else:
            _t2102 = 0
        prediction1269 = _t2102
        if prediction1269 == 1:
            _t2106 = self.parse_cdc_inserts()
            cdc_inserts1271 = _t2106
            _t2107 = self.parse_cdc_deletes()
            cdc_deletes1272 = _t2107
            _t2108 = self.construct_cdc_relations(cdc_inserts1271, cdc_deletes1272)
            _t2105 = _t2108
        else:
            if prediction1269 == 0:
                _t2110 = self.parse_non_cdc_relations()
                non_cdc_relations1270 = _t2110
                _t2111 = self.construct_non_cdc_relations(non_cdc_relations1270)
                _t2109 = _t2111
            else:
                raise ParseError("Unexpected token in relation_body" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2105 = _t2109
        result1274 = _t2105
        self.record_span(span_start1273, "TargetRelations")
        return result1274

    def parse_non_cdc_relations(self) -> Sequence[logic_pb2.TargetRelation]:
        xs1275 = []
        cond1276 = (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("relation", 1))
        while cond1276:
            _t2112 = self.parse_target_relation()
            item1277 = _t2112
            xs1275.append(item1277)
            cond1276 = (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("relation", 1))
        return xs1275

    def parse_target_relation(self) -> logic_pb2.TargetRelation:
        span_start1283 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relation")
        _t2113 = self.parse_relation_id()
        relation_id1278 = _t2113
        xs1279 = []
        cond1280 = self.match_lookahead_literal("(", 0)
        while cond1280:
            _t2114 = self.parse_named_column()
            item1281 = _t2114
            xs1279.append(item1281)
            cond1280 = self.match_lookahead_literal("(", 0)
        named_columns1282 = xs1279
        self.consume_literal(")")
        _t2115 = logic_pb2.TargetRelation(target_id=relation_id1278, values=named_columns1282)
        result1284 = _t2115
        self.record_span(span_start1283, "TargetRelation")
        return result1284

    def parse_cdc_inserts(self) -> Sequence[logic_pb2.TargetRelation]:
        self.consume_literal("(")
        self.consume_literal("inserts")
        xs1285 = []
        cond1286 = self.match_lookahead_literal("(", 0)
        while cond1286:
            _t2116 = self.parse_target_relation()
            item1287 = _t2116
            xs1285.append(item1287)
            cond1286 = self.match_lookahead_literal("(", 0)
        target_relations1288 = xs1285
        self.consume_literal(")")
        return target_relations1288

    def parse_cdc_deletes(self) -> Sequence[logic_pb2.TargetRelation]:
        self.consume_literal("(")
        self.consume_literal("deletes")
        xs1289 = []
        cond1290 = self.match_lookahead_literal("(", 0)
        while cond1290:
            _t2117 = self.parse_target_relation()
            item1291 = _t2117
            xs1289.append(item1291)
            cond1290 = self.match_lookahead_literal("(", 0)
        target_relations1292 = xs1289
        self.consume_literal(")")
        return target_relations1292

    def parse_load_errors(self) -> logic_pb2.RelationId:
        span_start1294 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("load_errors")
        _t2118 = self.parse_relation_id()
        relation_id1293 = _t2118
        self.consume_literal(")")
        result1295 = relation_id1293
        self.record_span(span_start1294, "RelationId")
        return result1295

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1296 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1296

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1304 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t2119 = self.parse_iceberg_locator()
        iceberg_locator1297 = _t2119
        _t2120 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1298 = _t2120
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("columns", 1)):
            _t2122 = self.parse_gnf_columns()
            _t2121 = _t2122
        else:
            _t2121 = None
        gnf_columns1299 = _t2121
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("relations", 1)):
            _t2124 = self.parse_target_relations()
            _t2123 = _t2124
        else:
            _t2123 = None
        target_relations1300 = _t2123
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t2126 = self.parse_iceberg_from_snapshot()
            _t2125 = _t2126
        else:
            _t2125 = None
        iceberg_from_snapshot1301 = _t2125
        if self.match_lookahead_literal("(", 0):
            _t2128 = self.parse_iceberg_to_snapshot()
            _t2127 = _t2128
        else:
            _t2127 = None
        iceberg_to_snapshot1302 = _t2127
        _t2129 = self.parse_boolean_value()
        boolean_value1303 = _t2129
        self.consume_literal(")")
        _t2130 = self.construct_iceberg_data(iceberg_locator1297, iceberg_catalog_config1298, gnf_columns1299, target_relations1300, iceberg_from_snapshot1301, iceberg_to_snapshot1302, boolean_value1303)
        result1305 = _t2130
        self.record_span(span_start1304, "IcebergData")
        return result1305

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1309 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t2131 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1306 = _t2131
        _t2132 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1307 = _t2132
        _t2133 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1308 = _t2133
        self.consume_literal(")")
        _t2134 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1306, namespace=iceberg_locator_namespace1307, warehouse=iceberg_locator_warehouse1308)
        result1310 = _t2134
        self.record_span(span_start1309, "IcebergLocator")
        return result1310

    def parse_iceberg_locator_table_name(self) -> str:
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1311 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1311

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1312 = []
        cond1313 = self.match_lookahead_terminal("STRING", 0)
        while cond1313:
            item1314 = self.consume_terminal("STRING")
            xs1312.append(item1314)
            cond1313 = self.match_lookahead_terminal("STRING", 0)
        strings1315 = xs1312
        self.consume_literal(")")
        return strings1315

    def parse_iceberg_locator_warehouse(self) -> str:
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string1316 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1316

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1321 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t2135 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1317 = _t2135
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t2137 = self.parse_iceberg_catalog_config_scope()
            _t2136 = _t2137
        else:
            _t2136 = None
        iceberg_catalog_config_scope1318 = _t2136
        _t2138 = self.parse_iceberg_properties()
        iceberg_properties1319 = _t2138
        _t2139 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1320 = _t2139
        self.consume_literal(")")
        _t2140 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1317, iceberg_catalog_config_scope1318, iceberg_properties1319, iceberg_auth_properties1320)
        result1322 = _t2140
        self.record_span(span_start1321, "IcebergCatalogConfig")
        return result1322

    def parse_iceberg_catalog_uri(self) -> str:
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1323 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1323

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1324 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1324

    def parse_iceberg_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1325 = []
        cond1326 = self.match_lookahead_literal("(", 0)
        while cond1326:
            _t2141 = self.parse_iceberg_property_entry()
            item1327 = _t2141
            xs1325.append(item1327)
            cond1326 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1328 = xs1325
        self.consume_literal(")")
        return iceberg_property_entrys1328

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1329 = self.consume_terminal("STRING")
        string_31330 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1329, string_31330,)

    def parse_iceberg_auth_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1331 = []
        cond1332 = self.match_lookahead_literal("(", 0)
        while cond1332:
            _t2142 = self.parse_iceberg_masked_property_entry()
            item1333 = _t2142
            xs1331.append(item1333)
            cond1332 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1334 = xs1331
        self.consume_literal(")")
        return iceberg_masked_property_entrys1334

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1335 = self.consume_terminal("STRING")
        string_31336 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1335, string_31336,)

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1337 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1337

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1338 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1338

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1340 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2143 = self.parse_fragment_id()
        fragment_id1339 = _t2143
        self.consume_literal(")")
        _t2144 = transactions_pb2.Undefine(fragment_id=fragment_id1339)
        result1341 = _t2144
        self.record_span(span_start1340, "Undefine")
        return result1341

    def parse_context(self) -> transactions_pb2.Context:
        span_start1346 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1342 = []
        cond1343 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1343:
            _t2145 = self.parse_relation_id()
            item1344 = _t2145
            xs1342.append(item1344)
            cond1343 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1345 = xs1342
        self.consume_literal(")")
        _t2146 = transactions_pb2.Context(relations=relation_ids1345)
        result1347 = _t2146
        self.record_span(span_start1346, "Context")
        return result1347

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1353 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t2147 = self.parse_edb_path()
        edb_path1348 = _t2147
        xs1349 = []
        cond1350 = self.match_lookahead_literal("[", 0)
        while cond1350:
            _t2148 = self.parse_snapshot_mapping()
            item1351 = _t2148
            xs1349.append(item1351)
            cond1350 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1352 = xs1349
        self.consume_literal(")")
        _t2149 = transactions_pb2.Snapshot(prefix=edb_path1348, mappings=snapshot_mappings1352)
        result1354 = _t2149
        self.record_span(span_start1353, "Snapshot")
        return result1354

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1357 = self.span_start()
        _t2150 = self.parse_edb_path()
        edb_path1355 = _t2150
        _t2151 = self.parse_relation_id()
        relation_id1356 = _t2151
        _t2152 = transactions_pb2.SnapshotMapping(destination_path=edb_path1355, source_relation=relation_id1356)
        result1358 = _t2152
        self.record_span(span_start1357, "SnapshotMapping")
        return result1358

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1359 = []
        cond1360 = self.match_lookahead_literal("(", 0)
        while cond1360:
            _t2153 = self.parse_read()
            item1361 = _t2153
            xs1359.append(item1361)
            cond1360 = self.match_lookahead_literal("(", 0)
        reads1362 = xs1359
        self.consume_literal(")")
        return reads1362

    def parse_read(self) -> transactions_pb2.Read:
        span_start1369 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2155 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2156 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t2157 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t2158 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t2159 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t2160 = 3
                                else:
                                    _t2160 = -1
                                _t2159 = _t2160
                            _t2158 = _t2159
                        _t2157 = _t2158
                    _t2156 = _t2157
                _t2155 = _t2156
            _t2154 = _t2155
        else:
            _t2154 = -1
        prediction1363 = _t2154
        if prediction1363 == 4:
            _t2162 = self.parse_export()
            export1368 = _t2162
            _t2163 = transactions_pb2.Read(export=export1368)
            _t2161 = _t2163
        else:
            if prediction1363 == 3:
                _t2165 = self.parse_abort()
                abort1367 = _t2165
                _t2166 = transactions_pb2.Read(abort=abort1367)
                _t2164 = _t2166
            else:
                if prediction1363 == 2:
                    _t2168 = self.parse_what_if()
                    what_if1366 = _t2168
                    _t2169 = transactions_pb2.Read(what_if=what_if1366)
                    _t2167 = _t2169
                else:
                    if prediction1363 == 1:
                        _t2171 = self.parse_output()
                        output1365 = _t2171
                        _t2172 = transactions_pb2.Read(output=output1365)
                        _t2170 = _t2172
                    else:
                        if prediction1363 == 0:
                            _t2174 = self.parse_demand()
                            demand1364 = _t2174
                            _t2175 = transactions_pb2.Read(demand=demand1364)
                            _t2173 = _t2175
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2170 = _t2173
                    _t2167 = _t2170
                _t2164 = _t2167
            _t2161 = _t2164
        result1370 = _t2161
        self.record_span(span_start1369, "Read")
        return result1370

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1372 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2176 = self.parse_relation_id()
        relation_id1371 = _t2176
        self.consume_literal(")")
        _t2177 = transactions_pb2.Demand(relation_id=relation_id1371)
        result1373 = _t2177
        self.record_span(span_start1372, "Demand")
        return result1373

    def parse_output(self) -> transactions_pb2.Output:
        span_start1376 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2178 = self.parse_name()
        name1374 = _t2178
        _t2179 = self.parse_relation_id()
        relation_id1375 = _t2179
        self.consume_literal(")")
        _t2180 = transactions_pb2.Output(name=name1374, relation_id=relation_id1375)
        result1377 = _t2180
        self.record_span(span_start1376, "Output")
        return result1377

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1380 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2181 = self.parse_name()
        name1378 = _t2181
        _t2182 = self.parse_epoch()
        epoch1379 = _t2182
        self.consume_literal(")")
        _t2183 = transactions_pb2.WhatIf(branch=name1378, epoch=epoch1379)
        result1381 = _t2183
        self.record_span(span_start1380, "WhatIf")
        return result1381

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1384 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2185 = self.parse_name()
            _t2184 = _t2185
        else:
            _t2184 = None
        name1382 = _t2184
        _t2186 = self.parse_relation_id()
        relation_id1383 = _t2186
        self.consume_literal(")")
        _t2187 = transactions_pb2.Abort(name=(name1382 if name1382 is not None else "abort"), relation_id=relation_id1383)
        result1385 = _t2187
        self.record_span(span_start1384, "Abort")
        return result1385

    def parse_export(self) -> transactions_pb2.Export:
        span_start1389 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2189 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2190 = 0
                else:
                    _t2190 = -1
                _t2189 = _t2190
            _t2188 = _t2189
        else:
            _t2188 = -1
        prediction1386 = _t2188
        if prediction1386 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2192 = self.parse_export_iceberg_config()
            export_iceberg_config1388 = _t2192
            self.consume_literal(")")
            _t2193 = transactions_pb2.Export(iceberg_config=export_iceberg_config1388)
            _t2191 = _t2193
        else:
            if prediction1386 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2195 = self.parse_export_csv_config()
                export_csv_config1387 = _t2195
                self.consume_literal(")")
                _t2196 = transactions_pb2.Export(csv_config=export_csv_config1387)
                _t2194 = _t2196
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2191 = _t2194
        result1390 = _t2191
        self.record_span(span_start1389, "Export")
        return result1390

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1398 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2198 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2199 = 1
                else:
                    _t2199 = -1
                _t2198 = _t2199
            _t2197 = _t2198
        else:
            _t2197 = -1
        prediction1391 = _t2197
        if prediction1391 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2201 = self.parse_export_csv_path()
            export_csv_path1395 = _t2201
            _t2202 = self.parse_export_csv_columns_list()
            export_csv_columns_list1396 = _t2202
            _t2203 = self.parse_config_dict()
            config_dict1397 = _t2203
            self.consume_literal(")")
            _t2204 = self.construct_export_csv_config(export_csv_path1395, export_csv_columns_list1396, config_dict1397)
            _t2200 = _t2204
        else:
            if prediction1391 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2206 = self.parse_export_csv_output_location()
                export_csv_output_location1392 = _t2206
                _t2207 = self.parse_export_csv_source()
                export_csv_source1393 = _t2207
                _t2208 = self.parse_csv_config()
                csv_config1394 = _t2208
                self.consume_literal(")")
                _t2209 = self.construct_export_csv_config_with_location(export_csv_output_location1392, export_csv_source1393, csv_config1394)
                _t2205 = _t2209
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2200 = _t2205
        result1399 = _t2200
        self.record_span(span_start1398, "ExportCSVConfig")
        return result1399

    def parse_export_csv_output_location(self) -> tuple[str, str]:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("transaction_output_name", 1):
                _t2211 = 1
            else:
                if self.match_lookahead_literal("path", 1):
                    _t2212 = 0
                else:
                    _t2212 = -1
                _t2211 = _t2212
            _t2210 = _t2211
        else:
            _t2210 = -1
        prediction1400 = _t2210
        if prediction1400 == 1:
            self.consume_literal("(")
            self.consume_literal("transaction_output_name")
            _t2214 = self.parse_name()
            name1402 = _t2214
            self.consume_literal(")")
            _t2213 = ("", name1402,)
        else:
            if prediction1400 == 0:
                self.consume_literal("(")
                self.consume_literal("path")
                string1401 = self.consume_terminal("STRING")
                self.consume_literal(")")
                _t2215 = (string1401, "",)
            else:
                raise ParseError("Unexpected token in export_csv_output_location" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2213 = _t2215
        return _t2213

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1409 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2217 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2218 = 0
                else:
                    _t2218 = -1
                _t2217 = _t2218
            _t2216 = _t2217
        else:
            _t2216 = -1
        prediction1403 = _t2216
        if prediction1403 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2220 = self.parse_relation_id()
            relation_id1408 = _t2220
            self.consume_literal(")")
            _t2221 = transactions_pb2.ExportCSVSource(table_def=relation_id1408)
            _t2219 = _t2221
        else:
            if prediction1403 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1404 = []
                cond1405 = self.match_lookahead_literal("(", 0)
                while cond1405:
                    _t2223 = self.parse_export_csv_column()
                    item1406 = _t2223
                    xs1404.append(item1406)
                    cond1405 = self.match_lookahead_literal("(", 0)
                export_csv_columns1407 = xs1404
                self.consume_literal(")")
                _t2224 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1407)
                _t2225 = transactions_pb2.ExportCSVSource(gnf_columns=_t2224)
                _t2222 = _t2225
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2219 = _t2222
        result1410 = _t2219
        self.record_span(span_start1409, "ExportCSVSource")
        return result1410

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1413 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1411 = self.consume_terminal("STRING")
        _t2226 = self.parse_relation_id()
        relation_id1412 = _t2226
        self.consume_literal(")")
        _t2227 = transactions_pb2.ExportCSVColumn(column_name=string1411, column_data=relation_id1412)
        result1414 = _t2227
        self.record_span(span_start1413, "ExportCSVColumn")
        return result1414

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1415 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1415

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1416 = []
        cond1417 = self.match_lookahead_literal("(", 0)
        while cond1417:
            _t2228 = self.parse_export_csv_column()
            item1418 = _t2228
            xs1416.append(item1418)
            cond1417 = self.match_lookahead_literal("(", 0)
        export_csv_columns1419 = xs1416
        self.consume_literal(")")
        return export_csv_columns1419

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1425 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2229 = self.parse_iceberg_locator()
        iceberg_locator1420 = _t2229
        _t2230 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1421 = _t2230
        _t2231 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1422 = _t2231
        _t2232 = self.parse_iceberg_table_properties()
        iceberg_table_properties1423 = _t2232
        if self.match_lookahead_literal("{", 0):
            _t2234 = self.parse_config_dict()
            _t2233 = _t2234
        else:
            _t2233 = None
        config_dict1424 = _t2233
        self.consume_literal(")")
        _t2235 = self.construct_export_iceberg_config_full(iceberg_locator1420, iceberg_catalog_config1421, export_iceberg_table_def1422, iceberg_table_properties1423, config_dict1424)
        result1426 = _t2235
        self.record_span(span_start1425, "ExportIcebergConfig")
        return result1426

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1428 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2236 = self.parse_relation_id()
        relation_id1427 = _t2236
        self.consume_literal(")")
        result1429 = relation_id1427
        self.record_span(span_start1428, "RelationId")
        return result1429

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1430 = []
        cond1431 = self.match_lookahead_literal("(", 0)
        while cond1431:
            _t2237 = self.parse_iceberg_property_entry()
            item1432 = _t2237
            xs1430.append(item1432)
            cond1431 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1433 = xs1430
        self.consume_literal(")")
        return iceberg_property_entrys1433


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
