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
            _t2233 = None
        assert value is not None
        if value.HasField("int32_value"):
            assert value is not None
            return value.int32_value
        else:
            _t2234 = None
        raise ParseError("expected an int32 value (e.g. `1i32`) for this config field")

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2235 = value.HasField("int_value")
        else:
            _t2235 = False
        if _t2235:
            assert value is not None
            return value.int_value
        else:
            _t2236 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2237 = value.HasField("string_value")
        else:
            _t2237 = False
        if _t2237:
            assert value is not None
            return value.string_value
        else:
            _t2238 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2239 = value.HasField("boolean_value")
        else:
            _t2239 = False
        if _t2239:
            assert value is not None
            return value.boolean_value
        else:
            _t2240 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2241 = value.HasField("string_value")
        else:
            _t2241 = False
        if _t2241:
            assert value is not None
            return [value.string_value]
        else:
            _t2242 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2243 = value.HasField("int_value")
        else:
            _t2243 = False
        if _t2243:
            assert value is not None
            return value.int_value
        else:
            _t2244 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2245 = value.HasField("float_value")
        else:
            _t2245 = False
        if _t2245:
            assert value is not None
            return value.float_value
        else:
            _t2246 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2247 = value.HasField("string_value")
        else:
            _t2247 = False
        if _t2247:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2248 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2249 = value.HasField("uint128_value")
        else:
            _t2249 = False
        if _t2249:
            assert value is not None
            return value.uint128_value
        else:
            _t2250 = None
        return None

    def construct_non_cdc_relations(self, targets: Sequence[logic_pb2.TargetRelation]) -> logic_pb2.TargetRelations:
        _t2251 = logic_pb2.PlainTargets(targets=targets)
        _t2252 = logic_pb2.TargetRelations(keys=[], plain=_t2251)
        return _t2252

    def construct_cdc_relations(self, inserts: Sequence[logic_pb2.TargetRelation], deletes: Sequence[logic_pb2.TargetRelation]) -> logic_pb2.TargetRelations:
        _t2253 = logic_pb2.CDCTargets(inserts=inserts, deletes=deletes)
        _t2254 = logic_pb2.TargetRelations(keys=[], cdc=_t2253)
        return _t2254

    def construct_relations(self, keys: tuple[Sequence[logic_pb2.NamedColumn], bool], body: logic_pb2.TargetRelations, load_errors_opt: logic_pb2.RelationId | None) -> logic_pb2.TargetRelations:
        if body.HasField("plain"):
            _t2256 = logic_pb2.TargetRelations(keys=keys[0], synthetic_key=keys[1], plain=body.plain, load_errors=load_errors_opt)
            return _t2256
        else:
            _t2255 = None
        _t2257 = logic_pb2.TargetRelations(keys=keys[0], synthetic_key=keys[1], cdc=body.cdc, load_errors=load_errors_opt)
        return _t2257

    def construct_csv_data(self, locator: logic_pb2.CSVLocator, config: logic_pb2.CSVConfig, columns_opt: Sequence[logic_pb2.GNFColumn] | None, relations_opt: logic_pb2.TargetRelations | None, asof: str) -> logic_pb2.CSVData:
        _t2258 = logic_pb2.CSVData(locator=locator, config=config, columns=(columns_opt if columns_opt is not None else []), asof=asof, relations=relations_opt)
        return _t2258

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]], storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2259 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2259
        _t2260 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2260
        _t2261 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2261
        _t2262 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2262
        _t2263 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2263
        _t2264 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2264
        _t2265 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2265
        _t2266 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2266
        _t2267 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2267
        _t2268 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2268
        _t2269 = self._extract_value_string(config.get("csv_compression"), "")
        compression = _t2269
        _t2270 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2270
        _t2271 = self.construct_csv_storage_integration(storage_integration_opt)
        storage_integration = _t2271
        _t2272 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
        return _t2272

    def construct_csv_storage_integration(self, storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.StorageIntegration | None:
        if storage_integration_opt is None:
            return None
        else:
            _t2273 = None
        assert storage_integration_opt is not None
        config = dict(storage_integration_opt)
        _t2274 = self._extract_value_string(config.get("provider"), "")
        _t2275 = self._extract_value_string(config.get("azure_sas_token"), "")
        _t2276 = self._extract_value_string(config.get("s3_region"), "")
        _t2277 = self._extract_value_string(config.get("s3_access_key_id"), "")
        _t2278 = self._extract_value_string(config.get("s3_secret_access_key"), "")
        _t2279 = logic_pb2.StorageIntegration(provider=_t2274, azure_sas_token=_t2275, s3_region=_t2276, s3_access_key_id=_t2277, s3_secret_access_key=_t2278)
        return _t2279

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2280 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2280
        _t2281 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2281
        _t2282 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2282
        _t2283 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2283
        _t2284 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2284
        _t2285 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2285
        _t2286 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2286
        _t2287 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2287
        _t2288 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2288
        _t2289 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2289
        _t2290 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2290

    def default_configure(self) -> transactions_pb2.Configure:
        _t2291 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2291
        _t2292 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2292

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
        _t2293 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2293
        _t2294 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2294
        config_values_pairs = []
        for pair in config_dict:
            if (pair[0] != "semantics_version" and pair[0] != "ivm.maintenance_level"):
                config_values_pairs.append(pair)
        configuration_values = dict(config_values_pairs)
        _t2295 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config, configuration_values=configuration_values)
        return _t2295

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2296 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2296
        _t2297 = self._extract_value_string(config.get("compression"), "")
        compression = _t2297
        _t2298 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2298
        _t2299 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2299
        _t2300 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2300
        _t2301 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2301
        _t2302 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2302
        _t2303 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2303

    def construct_export_csv_config_with_location(self, location: tuple[str, str], csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2304 = transactions_pb2.ExportCSVConfig(path=location[0], transaction_output_name=location[1], csv_source=csv_source, csv_config=csv_config)
        return _t2304

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2305 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2305

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[logic_pb2.GNFColumn], from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2306 = logic_pb2.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2306

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2307 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2307
        _t2308 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2308
        _t2309 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2309
        table_props = dict(table_property_pairs)
        _t2310 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2310

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start722 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1433 = self.parse_configure()
            _t1432 = _t1433
        else:
            _t1432 = None
        configure716 = _t1432
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1435 = self.parse_sync()
            _t1434 = _t1435
        else:
            _t1434 = None
        sync717 = _t1434
        xs718 = []
        cond719 = self.match_lookahead_literal("(", 0)
        while cond719:
            _t1436 = self.parse_epoch()
            item720 = _t1436
            xs718.append(item720)
            cond719 = self.match_lookahead_literal("(", 0)
        epochs721 = xs718
        self.consume_literal(")")
        _t1437 = self.default_configure()
        _t1438 = transactions_pb2.Transaction(epochs=epochs721, configure=(configure716 if configure716 is not None else _t1437), sync=sync717)
        result723 = _t1438
        self.record_span(span_start722, "Transaction")
        return result723

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start725 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1439 = self.parse_config_dict()
        config_dict724 = _t1439
        self.consume_literal(")")
        _t1440 = self.construct_configure(config_dict724)
        result726 = _t1440
        self.record_span(span_start725, "Configure")
        return result726

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs727 = []
        cond728 = self.match_lookahead_literal(":", 0)
        while cond728:
            _t1441 = self.parse_config_key_value()
            item729 = _t1441
            xs727.append(item729)
            cond728 = self.match_lookahead_literal(":", 0)
        config_key_values730 = xs727
        self.consume_literal("}")
        return config_key_values730

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol731 = self.consume_terminal("SYMBOL")
        _t1442 = self.parse_raw_value()
        raw_value732 = _t1442
        return (symbol731, raw_value732,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start746 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1443 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1444 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1445 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1447 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1448 = 0
                            else:
                                _t1448 = -1
                            _t1447 = _t1448
                        _t1446 = _t1447
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1449 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1450 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1451 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1452 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1453 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1454 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1455 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1456 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1457 = 10
                                                        else:
                                                            _t1457 = -1
                                                        _t1456 = _t1457
                                                    _t1455 = _t1456
                                                _t1454 = _t1455
                                            _t1453 = _t1454
                                        _t1452 = _t1453
                                    _t1451 = _t1452
                                _t1450 = _t1451
                            _t1449 = _t1450
                        _t1446 = _t1449
                    _t1445 = _t1446
                _t1444 = _t1445
            _t1443 = _t1444
        prediction733 = _t1443
        if prediction733 == 12:
            _t1459 = self.parse_boolean_value()
            boolean_value745 = _t1459
            _t1460 = logic_pb2.Value(boolean_value=boolean_value745)
            _t1458 = _t1460
        else:
            if prediction733 == 11:
                self.consume_literal("missing")
                _t1462 = logic_pb2.MissingValue()
                _t1463 = logic_pb2.Value(missing_value=_t1462)
                _t1461 = _t1463
            else:
                if prediction733 == 10:
                    decimal744 = self.consume_terminal("DECIMAL")
                    _t1465 = logic_pb2.Value(decimal_value=decimal744)
                    _t1464 = _t1465
                else:
                    if prediction733 == 9:
                        int128743 = self.consume_terminal("INT128")
                        _t1467 = logic_pb2.Value(int128_value=int128743)
                        _t1466 = _t1467
                    else:
                        if prediction733 == 8:
                            uint128742 = self.consume_terminal("UINT128")
                            _t1469 = logic_pb2.Value(uint128_value=uint128742)
                            _t1468 = _t1469
                        else:
                            if prediction733 == 7:
                                uint32741 = self.consume_terminal("UINT32")
                                _t1471 = logic_pb2.Value(uint32_value=uint32741)
                                _t1470 = _t1471
                            else:
                                if prediction733 == 6:
                                    float740 = self.consume_terminal("FLOAT")
                                    _t1473 = logic_pb2.Value(float_value=float740)
                                    _t1472 = _t1473
                                else:
                                    if prediction733 == 5:
                                        float32739 = self.consume_terminal("FLOAT32")
                                        _t1475 = logic_pb2.Value(float32_value=float32739)
                                        _t1474 = _t1475
                                    else:
                                        if prediction733 == 4:
                                            int738 = self.consume_terminal("INT")
                                            _t1477 = logic_pb2.Value(int_value=int738)
                                            _t1476 = _t1477
                                        else:
                                            if prediction733 == 3:
                                                int32737 = self.consume_terminal("INT32")
                                                _t1479 = logic_pb2.Value(int32_value=int32737)
                                                _t1478 = _t1479
                                            else:
                                                if prediction733 == 2:
                                                    string736 = self.consume_terminal("STRING")
                                                    _t1481 = logic_pb2.Value(string_value=string736)
                                                    _t1480 = _t1481
                                                else:
                                                    if prediction733 == 1:
                                                        _t1483 = self.parse_raw_datetime()
                                                        raw_datetime735 = _t1483
                                                        _t1484 = logic_pb2.Value(datetime_value=raw_datetime735)
                                                        _t1482 = _t1484
                                                    else:
                                                        if prediction733 == 0:
                                                            _t1486 = self.parse_raw_date()
                                                            raw_date734 = _t1486
                                                            _t1487 = logic_pb2.Value(date_value=raw_date734)
                                                            _t1485 = _t1487
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1482 = _t1485
                                                    _t1480 = _t1482
                                                _t1478 = _t1480
                                            _t1476 = _t1478
                                        _t1474 = _t1476
                                    _t1472 = _t1474
                                _t1470 = _t1472
                            _t1468 = _t1470
                        _t1466 = _t1468
                    _t1464 = _t1466
                _t1461 = _t1464
            _t1458 = _t1461
        result747 = _t1458
        self.record_span(span_start746, "Value")
        return result747

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start751 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int748 = self.consume_terminal("INT")
        int_3749 = self.consume_terminal("INT")
        int_4750 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1488 = logic_pb2.DateValue(year=int(int748), month=int(int_3749), day=int(int_4750))
        result752 = _t1488
        self.record_span(span_start751, "DateValue")
        return result752

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start760 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int753 = self.consume_terminal("INT")
        int_3754 = self.consume_terminal("INT")
        int_4755 = self.consume_terminal("INT")
        int_5756 = self.consume_terminal("INT")
        int_6757 = self.consume_terminal("INT")
        int_7758 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1489 = self.consume_terminal("INT")
        else:
            _t1489 = None
        int_8759 = _t1489
        self.consume_literal(")")
        _t1490 = logic_pb2.DateTimeValue(year=int(int753), month=int(int_3754), day=int(int_4755), hour=int(int_5756), minute=int(int_6757), second=int(int_7758), microsecond=int((int_8759 if int_8759 is not None else 0)))
        result761 = _t1490
        self.record_span(span_start760, "DateTimeValue")
        return result761

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1491 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1492 = 1
            else:
                _t1492 = -1
            _t1491 = _t1492
        prediction762 = _t1491
        if prediction762 == 1:
            self.consume_literal("false")
            _t1493 = False
        else:
            if prediction762 == 0:
                self.consume_literal("true")
                _t1494 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1493 = _t1494
        return _t1493

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start767 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs763 = []
        cond764 = self.match_lookahead_literal(":", 0)
        while cond764:
            _t1495 = self.parse_fragment_id()
            item765 = _t1495
            xs763.append(item765)
            cond764 = self.match_lookahead_literal(":", 0)
        fragment_ids766 = xs763
        self.consume_literal(")")
        _t1496 = transactions_pb2.Sync(fragments=fragment_ids766)
        result768 = _t1496
        self.record_span(span_start767, "Sync")
        return result768

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start770 = self.span_start()
        self.consume_literal(":")
        symbol769 = self.consume_terminal("SYMBOL")
        result771 = fragments_pb2.FragmentId(id=symbol769.encode())
        self.record_span(span_start770, "FragmentId")
        return result771

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start774 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1498 = self.parse_epoch_writes()
            _t1497 = _t1498
        else:
            _t1497 = None
        epoch_writes772 = _t1497
        if self.match_lookahead_literal("(", 0):
            _t1500 = self.parse_epoch_reads()
            _t1499 = _t1500
        else:
            _t1499 = None
        epoch_reads773 = _t1499
        self.consume_literal(")")
        _t1501 = transactions_pb2.Epoch(writes=(epoch_writes772 if epoch_writes772 is not None else []), reads=(epoch_reads773 if epoch_reads773 is not None else []))
        result775 = _t1501
        self.record_span(span_start774, "Epoch")
        return result775

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs776 = []
        cond777 = self.match_lookahead_literal("(", 0)
        while cond777:
            _t1502 = self.parse_write()
            item778 = _t1502
            xs776.append(item778)
            cond777 = self.match_lookahead_literal("(", 0)
        writes779 = xs776
        self.consume_literal(")")
        return writes779

    def parse_write(self) -> transactions_pb2.Write:
        span_start785 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1504 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1505 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1506 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1507 = 2
                        else:
                            _t1507 = -1
                        _t1506 = _t1507
                    _t1505 = _t1506
                _t1504 = _t1505
            _t1503 = _t1504
        else:
            _t1503 = -1
        prediction780 = _t1503
        if prediction780 == 3:
            _t1509 = self.parse_snapshot()
            snapshot784 = _t1509
            _t1510 = transactions_pb2.Write(snapshot=snapshot784)
            _t1508 = _t1510
        else:
            if prediction780 == 2:
                _t1512 = self.parse_context()
                context783 = _t1512
                _t1513 = transactions_pb2.Write(context=context783)
                _t1511 = _t1513
            else:
                if prediction780 == 1:
                    _t1515 = self.parse_undefine()
                    undefine782 = _t1515
                    _t1516 = transactions_pb2.Write(undefine=undefine782)
                    _t1514 = _t1516
                else:
                    if prediction780 == 0:
                        _t1518 = self.parse_define()
                        define781 = _t1518
                        _t1519 = transactions_pb2.Write(define=define781)
                        _t1517 = _t1519
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1514 = _t1517
                _t1511 = _t1514
            _t1508 = _t1511
        result786 = _t1508
        self.record_span(span_start785, "Write")
        return result786

    def parse_define(self) -> transactions_pb2.Define:
        span_start788 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1520 = self.parse_fragment()
        fragment787 = _t1520
        self.consume_literal(")")
        _t1521 = transactions_pb2.Define(fragment=fragment787)
        result789 = _t1521
        self.record_span(span_start788, "Define")
        return result789

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start795 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1522 = self.parse_new_fragment_id()
        new_fragment_id790 = _t1522
        xs791 = []
        cond792 = self.match_lookahead_literal("(", 0)
        while cond792:
            _t1523 = self.parse_declaration()
            item793 = _t1523
            xs791.append(item793)
            cond792 = self.match_lookahead_literal("(", 0)
        declarations794 = xs791
        self.consume_literal(")")
        result796 = self.construct_fragment(new_fragment_id790, declarations794)
        self.record_span(span_start795, "Fragment")
        return result796

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start798 = self.span_start()
        _t1524 = self.parse_fragment_id()
        fragment_id797 = _t1524
        self.start_fragment(fragment_id797)
        result799 = fragment_id797
        self.record_span(span_start798, "FragmentId")
        return result799

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start805 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1526 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1527 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1528 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1529 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1530 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1531 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1532 = 1
                                    else:
                                        _t1532 = -1
                                    _t1531 = _t1532
                                _t1530 = _t1531
                            _t1529 = _t1530
                        _t1528 = _t1529
                    _t1527 = _t1528
                _t1526 = _t1527
            _t1525 = _t1526
        else:
            _t1525 = -1
        prediction800 = _t1525
        if prediction800 == 3:
            _t1534 = self.parse_data()
            data804 = _t1534
            _t1535 = logic_pb2.Declaration(data=data804)
            _t1533 = _t1535
        else:
            if prediction800 == 2:
                _t1537 = self.parse_constraint()
                constraint803 = _t1537
                _t1538 = logic_pb2.Declaration(constraint=constraint803)
                _t1536 = _t1538
            else:
                if prediction800 == 1:
                    _t1540 = self.parse_algorithm()
                    algorithm802 = _t1540
                    _t1541 = logic_pb2.Declaration(algorithm=algorithm802)
                    _t1539 = _t1541
                else:
                    if prediction800 == 0:
                        _t1543 = self.parse_def()
                        def801 = _t1543
                        _t1544 = logic_pb2.Declaration()
                        getattr(_t1544, 'def').CopyFrom(def801)
                        _t1542 = _t1544
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1539 = _t1542
                _t1536 = _t1539
            _t1533 = _t1536
        result806 = _t1533
        self.record_span(span_start805, "Declaration")
        return result806

    def parse_def(self) -> logic_pb2.Def:
        span_start810 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1545 = self.parse_relation_id()
        relation_id807 = _t1545
        _t1546 = self.parse_abstraction()
        abstraction808 = _t1546
        if self.match_lookahead_literal("(", 0):
            _t1548 = self.parse_attrs()
            _t1547 = _t1548
        else:
            _t1547 = None
        attrs809 = _t1547
        self.consume_literal(")")
        _t1549 = logic_pb2.Def(name=relation_id807, body=abstraction808, attrs=(attrs809 if attrs809 is not None else []))
        result811 = _t1549
        self.record_span(span_start810, "Def")
        return result811

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start815 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1550 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1551 = 1
            else:
                _t1551 = -1
            _t1550 = _t1551
        prediction812 = _t1550
        if prediction812 == 1:
            uint128814 = self.consume_terminal("UINT128")
            _t1552 = logic_pb2.RelationId(id_low=uint128814.low, id_high=uint128814.high)
        else:
            if prediction812 == 0:
                self.consume_literal(":")
                symbol813 = self.consume_terminal("SYMBOL")
                _t1553 = self.relation_id_from_string(symbol813)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1552 = _t1553
        result816 = _t1552
        self.record_span(span_start815, "RelationId")
        return result816

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start819 = self.span_start()
        self.consume_literal("(")
        _t1554 = self.parse_bindings()
        bindings817 = _t1554
        _t1555 = self.parse_formula()
        formula818 = _t1555
        self.consume_literal(")")
        _t1556 = logic_pb2.Abstraction(vars=(list(bindings817[0]) + list(bindings817[1] if bindings817[1] is not None else [])), value=formula818)
        result820 = _t1556
        self.record_span(span_start819, "Abstraction")
        return result820

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs821 = []
        cond822 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond822:
            _t1557 = self.parse_binding()
            item823 = _t1557
            xs821.append(item823)
            cond822 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings824 = xs821
        if self.match_lookahead_literal("|", 0):
            _t1559 = self.parse_value_bindings()
            _t1558 = _t1559
        else:
            _t1558 = None
        value_bindings825 = _t1558
        self.consume_literal("]")
        return (bindings824, (value_bindings825 if value_bindings825 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start828 = self.span_start()
        symbol826 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1560 = self.parse_type()
        type827 = _t1560
        _t1561 = logic_pb2.Var(name=symbol826)
        _t1562 = logic_pb2.Binding(var=_t1561, type=type827)
        result829 = _t1562
        self.record_span(span_start828, "Binding")
        return result829

    def parse_type(self) -> logic_pb2.Type:
        span_start846 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1563 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1564 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1565 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1566 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1567 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1568 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1569 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1570 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1571 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1572 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1573 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1574 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1575 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                if self.match_lookahead_literal("FIXED", 1):
                                                                    _t1577 = 14
                                                                else:
                                                                    if self.match_lookahead_literal("DECIMAL", 1):
                                                                        _t1578 = 9
                                                                    else:
                                                                        _t1578 = -1
                                                                    _t1577 = _t1578
                                                                _t1576 = _t1577
                                                            else:
                                                                _t1576 = -1
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
                _t1564 = _t1565
            _t1563 = _t1564
        prediction830 = _t1563
        if prediction830 == 14:
            _t1580 = self.parse_fixed_type()
            fixed_type845 = _t1580
            _t1581 = logic_pb2.Type(fixed_type=fixed_type845)
            _t1579 = _t1581
        else:
            if prediction830 == 13:
                _t1583 = self.parse_uint32_type()
                uint32_type844 = _t1583
                _t1584 = logic_pb2.Type(uint32_type=uint32_type844)
                _t1582 = _t1584
            else:
                if prediction830 == 12:
                    _t1586 = self.parse_float32_type()
                    float32_type843 = _t1586
                    _t1587 = logic_pb2.Type(float32_type=float32_type843)
                    _t1585 = _t1587
                else:
                    if prediction830 == 11:
                        _t1589 = self.parse_int32_type()
                        int32_type842 = _t1589
                        _t1590 = logic_pb2.Type(int32_type=int32_type842)
                        _t1588 = _t1590
                    else:
                        if prediction830 == 10:
                            _t1592 = self.parse_boolean_type()
                            boolean_type841 = _t1592
                            _t1593 = logic_pb2.Type(boolean_type=boolean_type841)
                            _t1591 = _t1593
                        else:
                            if prediction830 == 9:
                                _t1595 = self.parse_decimal_type()
                                decimal_type840 = _t1595
                                _t1596 = logic_pb2.Type(decimal_type=decimal_type840)
                                _t1594 = _t1596
                            else:
                                if prediction830 == 8:
                                    _t1598 = self.parse_missing_type()
                                    missing_type839 = _t1598
                                    _t1599 = logic_pb2.Type(missing_type=missing_type839)
                                    _t1597 = _t1599
                                else:
                                    if prediction830 == 7:
                                        _t1601 = self.parse_datetime_type()
                                        datetime_type838 = _t1601
                                        _t1602 = logic_pb2.Type(datetime_type=datetime_type838)
                                        _t1600 = _t1602
                                    else:
                                        if prediction830 == 6:
                                            _t1604 = self.parse_date_type()
                                            date_type837 = _t1604
                                            _t1605 = logic_pb2.Type(date_type=date_type837)
                                            _t1603 = _t1605
                                        else:
                                            if prediction830 == 5:
                                                _t1607 = self.parse_int128_type()
                                                int128_type836 = _t1607
                                                _t1608 = logic_pb2.Type(int128_type=int128_type836)
                                                _t1606 = _t1608
                                            else:
                                                if prediction830 == 4:
                                                    _t1610 = self.parse_uint128_type()
                                                    uint128_type835 = _t1610
                                                    _t1611 = logic_pb2.Type(uint128_type=uint128_type835)
                                                    _t1609 = _t1611
                                                else:
                                                    if prediction830 == 3:
                                                        _t1613 = self.parse_float_type()
                                                        float_type834 = _t1613
                                                        _t1614 = logic_pb2.Type(float_type=float_type834)
                                                        _t1612 = _t1614
                                                    else:
                                                        if prediction830 == 2:
                                                            _t1616 = self.parse_int_type()
                                                            int_type833 = _t1616
                                                            _t1617 = logic_pb2.Type(int_type=int_type833)
                                                            _t1615 = _t1617
                                                        else:
                                                            if prediction830 == 1:
                                                                _t1619 = self.parse_string_type()
                                                                string_type832 = _t1619
                                                                _t1620 = logic_pb2.Type(string_type=string_type832)
                                                                _t1618 = _t1620
                                                            else:
                                                                if prediction830 == 0:
                                                                    _t1622 = self.parse_unspecified_type()
                                                                    unspecified_type831 = _t1622
                                                                    _t1623 = logic_pb2.Type(unspecified_type=unspecified_type831)
                                                                    _t1621 = _t1623
                                                                else:
                                                                    raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                                _t1618 = _t1621
                                                            _t1615 = _t1618
                                                        _t1612 = _t1615
                                                    _t1609 = _t1612
                                                _t1606 = _t1609
                                            _t1603 = _t1606
                                        _t1600 = _t1603
                                    _t1597 = _t1600
                                _t1594 = _t1597
                            _t1591 = _t1594
                        _t1588 = _t1591
                    _t1585 = _t1588
                _t1582 = _t1585
            _t1579 = _t1582
        result847 = _t1579
        self.record_span(span_start846, "Type")
        return result847

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start848 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1624 = logic_pb2.UnspecifiedType()
        result849 = _t1624
        self.record_span(span_start848, "UnspecifiedType")
        return result849

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start850 = self.span_start()
        self.consume_literal("STRING")
        _t1625 = logic_pb2.StringType()
        result851 = _t1625
        self.record_span(span_start850, "StringType")
        return result851

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start852 = self.span_start()
        self.consume_literal("INT")
        _t1626 = logic_pb2.IntType()
        result853 = _t1626
        self.record_span(span_start852, "IntType")
        return result853

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start854 = self.span_start()
        self.consume_literal("FLOAT")
        _t1627 = logic_pb2.FloatType()
        result855 = _t1627
        self.record_span(span_start854, "FloatType")
        return result855

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start856 = self.span_start()
        self.consume_literal("UINT128")
        _t1628 = logic_pb2.UInt128Type()
        result857 = _t1628
        self.record_span(span_start856, "UInt128Type")
        return result857

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start858 = self.span_start()
        self.consume_literal("INT128")
        _t1629 = logic_pb2.Int128Type()
        result859 = _t1629
        self.record_span(span_start858, "Int128Type")
        return result859

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start860 = self.span_start()
        self.consume_literal("DATE")
        _t1630 = logic_pb2.DateType()
        result861 = _t1630
        self.record_span(span_start860, "DateType")
        return result861

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start862 = self.span_start()
        self.consume_literal("DATETIME")
        _t1631 = logic_pb2.DateTimeType()
        result863 = _t1631
        self.record_span(span_start862, "DateTimeType")
        return result863

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start864 = self.span_start()
        self.consume_literal("MISSING")
        _t1632 = logic_pb2.MissingType()
        result865 = _t1632
        self.record_span(span_start864, "MissingType")
        return result865

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start868 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int866 = self.consume_terminal("INT")
        int_3867 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1633 = logic_pb2.DecimalType(precision=int(int866), scale=int(int_3867))
        result869 = _t1633
        self.record_span(span_start868, "DecimalType")
        return result869

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start870 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1634 = logic_pb2.BooleanType()
        result871 = _t1634
        self.record_span(span_start870, "BooleanType")
        return result871

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start872 = self.span_start()
        self.consume_literal("INT32")
        _t1635 = logic_pb2.Int32Type()
        result873 = _t1635
        self.record_span(span_start872, "Int32Type")
        return result873

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start874 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1636 = logic_pb2.Float32Type()
        result875 = _t1636
        self.record_span(span_start874, "Float32Type")
        return result875

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start876 = self.span_start()
        self.consume_literal("UINT32")
        _t1637 = logic_pb2.UInt32Type()
        result877 = _t1637
        self.record_span(span_start876, "UInt32Type")
        return result877

    def parse_fixed_type(self) -> logic_pb2.FixedType:
        span_start879 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("FIXED")
        int878 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1638 = logic_pb2.FixedType(length=int(int878))
        result880 = _t1638
        self.record_span(span_start879, "FixedType")
        return result880

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs881 = []
        cond882 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond882:
            _t1639 = self.parse_binding()
            item883 = _t1639
            xs881.append(item883)
            cond882 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings884 = xs881
        return bindings884

    def parse_formula(self) -> logic_pb2.Formula:
        span_start899 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1641 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1642 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1643 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1644 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1645 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1646 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1647 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1648 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1649 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1650 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1651 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1652 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1653 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1654 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1655 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1656 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1657 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1658 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1659 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1660 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1661 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1662 = 10
                                                                                                else:
                                                                                                    _t1662 = -1
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
                _t1641 = _t1642
            _t1640 = _t1641
        else:
            _t1640 = -1
        prediction885 = _t1640
        if prediction885 == 12:
            _t1664 = self.parse_cast()
            cast898 = _t1664
            _t1665 = logic_pb2.Formula(cast=cast898)
            _t1663 = _t1665
        else:
            if prediction885 == 11:
                _t1667 = self.parse_rel_atom()
                rel_atom897 = _t1667
                _t1668 = logic_pb2.Formula(rel_atom=rel_atom897)
                _t1666 = _t1668
            else:
                if prediction885 == 10:
                    _t1670 = self.parse_primitive()
                    primitive896 = _t1670
                    _t1671 = logic_pb2.Formula(primitive=primitive896)
                    _t1669 = _t1671
                else:
                    if prediction885 == 9:
                        _t1673 = self.parse_pragma()
                        pragma895 = _t1673
                        _t1674 = logic_pb2.Formula(pragma=pragma895)
                        _t1672 = _t1674
                    else:
                        if prediction885 == 8:
                            _t1676 = self.parse_atom()
                            atom894 = _t1676
                            _t1677 = logic_pb2.Formula(atom=atom894)
                            _t1675 = _t1677
                        else:
                            if prediction885 == 7:
                                _t1679 = self.parse_ffi()
                                ffi893 = _t1679
                                _t1680 = logic_pb2.Formula(ffi=ffi893)
                                _t1678 = _t1680
                            else:
                                if prediction885 == 6:
                                    _t1682 = self.parse_not()
                                    not892 = _t1682
                                    _t1683 = logic_pb2.Formula()
                                    getattr(_t1683, 'not').CopyFrom(not892)
                                    _t1681 = _t1683
                                else:
                                    if prediction885 == 5:
                                        _t1685 = self.parse_disjunction()
                                        disjunction891 = _t1685
                                        _t1686 = logic_pb2.Formula(disjunction=disjunction891)
                                        _t1684 = _t1686
                                    else:
                                        if prediction885 == 4:
                                            _t1688 = self.parse_conjunction()
                                            conjunction890 = _t1688
                                            _t1689 = logic_pb2.Formula(conjunction=conjunction890)
                                            _t1687 = _t1689
                                        else:
                                            if prediction885 == 3:
                                                _t1691 = self.parse_reduce()
                                                reduce889 = _t1691
                                                _t1692 = logic_pb2.Formula(reduce=reduce889)
                                                _t1690 = _t1692
                                            else:
                                                if prediction885 == 2:
                                                    _t1694 = self.parse_exists()
                                                    exists888 = _t1694
                                                    _t1695 = logic_pb2.Formula(exists=exists888)
                                                    _t1693 = _t1695
                                                else:
                                                    if prediction885 == 1:
                                                        _t1697 = self.parse_false()
                                                        false887 = _t1697
                                                        _t1698 = logic_pb2.Formula(disjunction=false887)
                                                        _t1696 = _t1698
                                                    else:
                                                        if prediction885 == 0:
                                                            _t1700 = self.parse_true()
                                                            true886 = _t1700
                                                            _t1701 = logic_pb2.Formula(conjunction=true886)
                                                            _t1699 = _t1701
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1696 = _t1699
                                                    _t1693 = _t1696
                                                _t1690 = _t1693
                                            _t1687 = _t1690
                                        _t1684 = _t1687
                                    _t1681 = _t1684
                                _t1678 = _t1681
                            _t1675 = _t1678
                        _t1672 = _t1675
                    _t1669 = _t1672
                _t1666 = _t1669
            _t1663 = _t1666
        result900 = _t1663
        self.record_span(span_start899, "Formula")
        return result900

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start901 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1702 = logic_pb2.Conjunction(args=[])
        result902 = _t1702
        self.record_span(span_start901, "Conjunction")
        return result902

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start903 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1703 = logic_pb2.Disjunction(args=[])
        result904 = _t1703
        self.record_span(span_start903, "Disjunction")
        return result904

    def parse_exists(self) -> logic_pb2.Exists:
        span_start907 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1704 = self.parse_bindings()
        bindings905 = _t1704
        _t1705 = self.parse_formula()
        formula906 = _t1705
        self.consume_literal(")")
        _t1706 = logic_pb2.Abstraction(vars=(list(bindings905[0]) + list(bindings905[1] if bindings905[1] is not None else [])), value=formula906)
        _t1707 = logic_pb2.Exists(body=_t1706)
        result908 = _t1707
        self.record_span(span_start907, "Exists")
        return result908

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start912 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1708 = self.parse_abstraction()
        abstraction909 = _t1708
        _t1709 = self.parse_abstraction()
        abstraction_3910 = _t1709
        _t1710 = self.parse_terms()
        terms911 = _t1710
        self.consume_literal(")")
        _t1711 = logic_pb2.Reduce(op=abstraction909, body=abstraction_3910, terms=terms911)
        result913 = _t1711
        self.record_span(span_start912, "Reduce")
        return result913

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs914 = []
        cond915 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond915:
            _t1712 = self.parse_term()
            item916 = _t1712
            xs914.append(item916)
            cond915 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms917 = xs914
        self.consume_literal(")")
        return terms917

    def parse_term(self) -> logic_pb2.Term:
        span_start921 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1713 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1714 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1715 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1716 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1717 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1718 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1719 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1720 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1721 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1722 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1723 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1724 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1725 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1726 = 1
                                                            else:
                                                                _t1726 = -1
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
                _t1714 = _t1715
            _t1713 = _t1714
        prediction918 = _t1713
        if prediction918 == 1:
            _t1728 = self.parse_value()
            value920 = _t1728
            _t1729 = logic_pb2.Term(constant=value920)
            _t1727 = _t1729
        else:
            if prediction918 == 0:
                _t1731 = self.parse_var()
                var919 = _t1731
                _t1732 = logic_pb2.Term(var=var919)
                _t1730 = _t1732
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1727 = _t1730
        result922 = _t1727
        self.record_span(span_start921, "Term")
        return result922

    def parse_var(self) -> logic_pb2.Var:
        span_start924 = self.span_start()
        symbol923 = self.consume_terminal("SYMBOL")
        _t1733 = logic_pb2.Var(name=symbol923)
        result925 = _t1733
        self.record_span(span_start924, "Var")
        return result925

    def parse_value(self) -> logic_pb2.Value:
        span_start939 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1734 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1735 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1736 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1738 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1739 = 0
                            else:
                                _t1739 = -1
                            _t1738 = _t1739
                        _t1737 = _t1738
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1740 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1741 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1742 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1743 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1744 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1745 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1746 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1747 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1748 = 10
                                                        else:
                                                            _t1748 = -1
                                                        _t1747 = _t1748
                                                    _t1746 = _t1747
                                                _t1745 = _t1746
                                            _t1744 = _t1745
                                        _t1743 = _t1744
                                    _t1742 = _t1743
                                _t1741 = _t1742
                            _t1740 = _t1741
                        _t1737 = _t1740
                    _t1736 = _t1737
                _t1735 = _t1736
            _t1734 = _t1735
        prediction926 = _t1734
        if prediction926 == 12:
            _t1750 = self.parse_boolean_value()
            boolean_value938 = _t1750
            _t1751 = logic_pb2.Value(boolean_value=boolean_value938)
            _t1749 = _t1751
        else:
            if prediction926 == 11:
                self.consume_literal("missing")
                _t1753 = logic_pb2.MissingValue()
                _t1754 = logic_pb2.Value(missing_value=_t1753)
                _t1752 = _t1754
            else:
                if prediction926 == 10:
                    formatted_decimal937 = self.consume_terminal("DECIMAL")
                    _t1756 = logic_pb2.Value(decimal_value=formatted_decimal937)
                    _t1755 = _t1756
                else:
                    if prediction926 == 9:
                        formatted_int128936 = self.consume_terminal("INT128")
                        _t1758 = logic_pb2.Value(int128_value=formatted_int128936)
                        _t1757 = _t1758
                    else:
                        if prediction926 == 8:
                            formatted_uint128935 = self.consume_terminal("UINT128")
                            _t1760 = logic_pb2.Value(uint128_value=formatted_uint128935)
                            _t1759 = _t1760
                        else:
                            if prediction926 == 7:
                                formatted_uint32934 = self.consume_terminal("UINT32")
                                _t1762 = logic_pb2.Value(uint32_value=formatted_uint32934)
                                _t1761 = _t1762
                            else:
                                if prediction926 == 6:
                                    formatted_float933 = self.consume_terminal("FLOAT")
                                    _t1764 = logic_pb2.Value(float_value=formatted_float933)
                                    _t1763 = _t1764
                                else:
                                    if prediction926 == 5:
                                        formatted_float32932 = self.consume_terminal("FLOAT32")
                                        _t1766 = logic_pb2.Value(float32_value=formatted_float32932)
                                        _t1765 = _t1766
                                    else:
                                        if prediction926 == 4:
                                            formatted_int931 = self.consume_terminal("INT")
                                            _t1768 = logic_pb2.Value(int_value=formatted_int931)
                                            _t1767 = _t1768
                                        else:
                                            if prediction926 == 3:
                                                formatted_int32930 = self.consume_terminal("INT32")
                                                _t1770 = logic_pb2.Value(int32_value=formatted_int32930)
                                                _t1769 = _t1770
                                            else:
                                                if prediction926 == 2:
                                                    formatted_string929 = self.consume_terminal("STRING")
                                                    _t1772 = logic_pb2.Value(string_value=formatted_string929)
                                                    _t1771 = _t1772
                                                else:
                                                    if prediction926 == 1:
                                                        _t1774 = self.parse_datetime()
                                                        datetime928 = _t1774
                                                        _t1775 = logic_pb2.Value(datetime_value=datetime928)
                                                        _t1773 = _t1775
                                                    else:
                                                        if prediction926 == 0:
                                                            _t1777 = self.parse_date()
                                                            date927 = _t1777
                                                            _t1778 = logic_pb2.Value(date_value=date927)
                                                            _t1776 = _t1778
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1773 = _t1776
                                                    _t1771 = _t1773
                                                _t1769 = _t1771
                                            _t1767 = _t1769
                                        _t1765 = _t1767
                                    _t1763 = _t1765
                                _t1761 = _t1763
                            _t1759 = _t1761
                        _t1757 = _t1759
                    _t1755 = _t1757
                _t1752 = _t1755
            _t1749 = _t1752
        result940 = _t1749
        self.record_span(span_start939, "Value")
        return result940

    def parse_date(self) -> logic_pb2.DateValue:
        span_start944 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int941 = self.consume_terminal("INT")
        formatted_int_3942 = self.consume_terminal("INT")
        formatted_int_4943 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1779 = logic_pb2.DateValue(year=int(formatted_int941), month=int(formatted_int_3942), day=int(formatted_int_4943))
        result945 = _t1779
        self.record_span(span_start944, "DateValue")
        return result945

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start953 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int946 = self.consume_terminal("INT")
        formatted_int_3947 = self.consume_terminal("INT")
        formatted_int_4948 = self.consume_terminal("INT")
        formatted_int_5949 = self.consume_terminal("INT")
        formatted_int_6950 = self.consume_terminal("INT")
        formatted_int_7951 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1780 = self.consume_terminal("INT")
        else:
            _t1780 = None
        formatted_int_8952 = _t1780
        self.consume_literal(")")
        _t1781 = logic_pb2.DateTimeValue(year=int(formatted_int946), month=int(formatted_int_3947), day=int(formatted_int_4948), hour=int(formatted_int_5949), minute=int(formatted_int_6950), second=int(formatted_int_7951), microsecond=int((formatted_int_8952 if formatted_int_8952 is not None else 0)))
        result954 = _t1781
        self.record_span(span_start953, "DateTimeValue")
        return result954

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start959 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs955 = []
        cond956 = self.match_lookahead_literal("(", 0)
        while cond956:
            _t1782 = self.parse_formula()
            item957 = _t1782
            xs955.append(item957)
            cond956 = self.match_lookahead_literal("(", 0)
        formulas958 = xs955
        self.consume_literal(")")
        _t1783 = logic_pb2.Conjunction(args=formulas958)
        result960 = _t1783
        self.record_span(span_start959, "Conjunction")
        return result960

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start965 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs961 = []
        cond962 = self.match_lookahead_literal("(", 0)
        while cond962:
            _t1784 = self.parse_formula()
            item963 = _t1784
            xs961.append(item963)
            cond962 = self.match_lookahead_literal("(", 0)
        formulas964 = xs961
        self.consume_literal(")")
        _t1785 = logic_pb2.Disjunction(args=formulas964)
        result966 = _t1785
        self.record_span(span_start965, "Disjunction")
        return result966

    def parse_not(self) -> logic_pb2.Not:
        span_start968 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1786 = self.parse_formula()
        formula967 = _t1786
        self.consume_literal(")")
        _t1787 = logic_pb2.Not(arg=formula967)
        result969 = _t1787
        self.record_span(span_start968, "Not")
        return result969

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start973 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1788 = self.parse_name()
        name970 = _t1788
        _t1789 = self.parse_ffi_args()
        ffi_args971 = _t1789
        _t1790 = self.parse_terms()
        terms972 = _t1790
        self.consume_literal(")")
        _t1791 = logic_pb2.FFI(name=name970, args=ffi_args971, terms=terms972)
        result974 = _t1791
        self.record_span(span_start973, "FFI")
        return result974

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol975 = self.consume_terminal("SYMBOL")
        return symbol975

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs976 = []
        cond977 = self.match_lookahead_literal("(", 0)
        while cond977:
            _t1792 = self.parse_abstraction()
            item978 = _t1792
            xs976.append(item978)
            cond977 = self.match_lookahead_literal("(", 0)
        abstractions979 = xs976
        self.consume_literal(")")
        return abstractions979

    def parse_atom(self) -> logic_pb2.Atom:
        span_start985 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1793 = self.parse_relation_id()
        relation_id980 = _t1793
        xs981 = []
        cond982 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond982:
            _t1794 = self.parse_term()
            item983 = _t1794
            xs981.append(item983)
            cond982 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms984 = xs981
        self.consume_literal(")")
        _t1795 = logic_pb2.Atom(name=relation_id980, terms=terms984)
        result986 = _t1795
        self.record_span(span_start985, "Atom")
        return result986

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start992 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1796 = self.parse_name()
        name987 = _t1796
        xs988 = []
        cond989 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond989:
            _t1797 = self.parse_term()
            item990 = _t1797
            xs988.append(item990)
            cond989 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms991 = xs988
        self.consume_literal(")")
        _t1798 = logic_pb2.Pragma(name=name987, terms=terms991)
        result993 = _t1798
        self.record_span(span_start992, "Pragma")
        return result993

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start1009 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1800 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1801 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1802 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1803 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1804 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1805 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1806 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1807 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1808 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1809 = 7
                                                else:
                                                    _t1809 = -1
                                                _t1808 = _t1809
                                            _t1807 = _t1808
                                        _t1806 = _t1807
                                    _t1805 = _t1806
                                _t1804 = _t1805
                            _t1803 = _t1804
                        _t1802 = _t1803
                    _t1801 = _t1802
                _t1800 = _t1801
            _t1799 = _t1800
        else:
            _t1799 = -1
        prediction994 = _t1799
        if prediction994 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1811 = self.parse_name()
            name1004 = _t1811
            xs1005 = []
            cond1006 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond1006:
                _t1812 = self.parse_rel_term()
                item1007 = _t1812
                xs1005.append(item1007)
                cond1006 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms1008 = xs1005
            self.consume_literal(")")
            _t1813 = logic_pb2.Primitive(name=name1004, terms=rel_terms1008)
            _t1810 = _t1813
        else:
            if prediction994 == 8:
                _t1815 = self.parse_divide()
                divide1003 = _t1815
                _t1814 = divide1003
            else:
                if prediction994 == 7:
                    _t1817 = self.parse_multiply()
                    multiply1002 = _t1817
                    _t1816 = multiply1002
                else:
                    if prediction994 == 6:
                        _t1819 = self.parse_minus()
                        minus1001 = _t1819
                        _t1818 = minus1001
                    else:
                        if prediction994 == 5:
                            _t1821 = self.parse_add()
                            add1000 = _t1821
                            _t1820 = add1000
                        else:
                            if prediction994 == 4:
                                _t1823 = self.parse_gt_eq()
                                gt_eq999 = _t1823
                                _t1822 = gt_eq999
                            else:
                                if prediction994 == 3:
                                    _t1825 = self.parse_gt()
                                    gt998 = _t1825
                                    _t1824 = gt998
                                else:
                                    if prediction994 == 2:
                                        _t1827 = self.parse_lt_eq()
                                        lt_eq997 = _t1827
                                        _t1826 = lt_eq997
                                    else:
                                        if prediction994 == 1:
                                            _t1829 = self.parse_lt()
                                            lt996 = _t1829
                                            _t1828 = lt996
                                        else:
                                            if prediction994 == 0:
                                                _t1831 = self.parse_eq()
                                                eq995 = _t1831
                                                _t1830 = eq995
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1828 = _t1830
                                        _t1826 = _t1828
                                    _t1824 = _t1826
                                _t1822 = _t1824
                            _t1820 = _t1822
                        _t1818 = _t1820
                    _t1816 = _t1818
                _t1814 = _t1816
            _t1810 = _t1814
        result1010 = _t1810
        self.record_span(span_start1009, "Primitive")
        return result1010

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start1013 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1832 = self.parse_term()
        term1011 = _t1832
        _t1833 = self.parse_term()
        term_31012 = _t1833
        self.consume_literal(")")
        _t1834 = logic_pb2.RelTerm(term=term1011)
        _t1835 = logic_pb2.RelTerm(term=term_31012)
        _t1836 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1834, _t1835])
        result1014 = _t1836
        self.record_span(span_start1013, "Primitive")
        return result1014

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start1017 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1837 = self.parse_term()
        term1015 = _t1837
        _t1838 = self.parse_term()
        term_31016 = _t1838
        self.consume_literal(")")
        _t1839 = logic_pb2.RelTerm(term=term1015)
        _t1840 = logic_pb2.RelTerm(term=term_31016)
        _t1841 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1839, _t1840])
        result1018 = _t1841
        self.record_span(span_start1017, "Primitive")
        return result1018

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start1021 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1842 = self.parse_term()
        term1019 = _t1842
        _t1843 = self.parse_term()
        term_31020 = _t1843
        self.consume_literal(")")
        _t1844 = logic_pb2.RelTerm(term=term1019)
        _t1845 = logic_pb2.RelTerm(term=term_31020)
        _t1846 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1844, _t1845])
        result1022 = _t1846
        self.record_span(span_start1021, "Primitive")
        return result1022

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start1025 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1847 = self.parse_term()
        term1023 = _t1847
        _t1848 = self.parse_term()
        term_31024 = _t1848
        self.consume_literal(")")
        _t1849 = logic_pb2.RelTerm(term=term1023)
        _t1850 = logic_pb2.RelTerm(term=term_31024)
        _t1851 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1849, _t1850])
        result1026 = _t1851
        self.record_span(span_start1025, "Primitive")
        return result1026

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start1029 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1852 = self.parse_term()
        term1027 = _t1852
        _t1853 = self.parse_term()
        term_31028 = _t1853
        self.consume_literal(")")
        _t1854 = logic_pb2.RelTerm(term=term1027)
        _t1855 = logic_pb2.RelTerm(term=term_31028)
        _t1856 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1854, _t1855])
        result1030 = _t1856
        self.record_span(span_start1029, "Primitive")
        return result1030

    def parse_add(self) -> logic_pb2.Primitive:
        span_start1034 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1857 = self.parse_term()
        term1031 = _t1857
        _t1858 = self.parse_term()
        term_31032 = _t1858
        _t1859 = self.parse_term()
        term_41033 = _t1859
        self.consume_literal(")")
        _t1860 = logic_pb2.RelTerm(term=term1031)
        _t1861 = logic_pb2.RelTerm(term=term_31032)
        _t1862 = logic_pb2.RelTerm(term=term_41033)
        _t1863 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1860, _t1861, _t1862])
        result1035 = _t1863
        self.record_span(span_start1034, "Primitive")
        return result1035

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start1039 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1864 = self.parse_term()
        term1036 = _t1864
        _t1865 = self.parse_term()
        term_31037 = _t1865
        _t1866 = self.parse_term()
        term_41038 = _t1866
        self.consume_literal(")")
        _t1867 = logic_pb2.RelTerm(term=term1036)
        _t1868 = logic_pb2.RelTerm(term=term_31037)
        _t1869 = logic_pb2.RelTerm(term=term_41038)
        _t1870 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1867, _t1868, _t1869])
        result1040 = _t1870
        self.record_span(span_start1039, "Primitive")
        return result1040

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start1044 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1871 = self.parse_term()
        term1041 = _t1871
        _t1872 = self.parse_term()
        term_31042 = _t1872
        _t1873 = self.parse_term()
        term_41043 = _t1873
        self.consume_literal(")")
        _t1874 = logic_pb2.RelTerm(term=term1041)
        _t1875 = logic_pb2.RelTerm(term=term_31042)
        _t1876 = logic_pb2.RelTerm(term=term_41043)
        _t1877 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1874, _t1875, _t1876])
        result1045 = _t1877
        self.record_span(span_start1044, "Primitive")
        return result1045

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start1049 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1878 = self.parse_term()
        term1046 = _t1878
        _t1879 = self.parse_term()
        term_31047 = _t1879
        _t1880 = self.parse_term()
        term_41048 = _t1880
        self.consume_literal(")")
        _t1881 = logic_pb2.RelTerm(term=term1046)
        _t1882 = logic_pb2.RelTerm(term=term_31047)
        _t1883 = logic_pb2.RelTerm(term=term_41048)
        _t1884 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1881, _t1882, _t1883])
        result1050 = _t1884
        self.record_span(span_start1049, "Primitive")
        return result1050

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1054 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1885 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1886 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1887 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1888 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1889 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1890 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1891 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1892 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1893 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1894 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1895 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1896 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1897 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1898 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1899 = 1
                                                                else:
                                                                    _t1899 = -1
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
                _t1886 = _t1887
            _t1885 = _t1886
        prediction1051 = _t1885
        if prediction1051 == 1:
            _t1901 = self.parse_term()
            term1053 = _t1901
            _t1902 = logic_pb2.RelTerm(term=term1053)
            _t1900 = _t1902
        else:
            if prediction1051 == 0:
                _t1904 = self.parse_specialized_value()
                specialized_value1052 = _t1904
                _t1905 = logic_pb2.RelTerm(specialized_value=specialized_value1052)
                _t1903 = _t1905
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1900 = _t1903
        result1055 = _t1900
        self.record_span(span_start1054, "RelTerm")
        return result1055

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1057 = self.span_start()
        self.consume_literal("#")
        _t1906 = self.parse_raw_value()
        raw_value1056 = _t1906
        result1058 = raw_value1056
        self.record_span(span_start1057, "Value")
        return result1058

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1064 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1907 = self.parse_name()
        name1059 = _t1907
        xs1060 = []
        cond1061 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1061:
            _t1908 = self.parse_rel_term()
            item1062 = _t1908
            xs1060.append(item1062)
            cond1061 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1063 = xs1060
        self.consume_literal(")")
        _t1909 = logic_pb2.RelAtom(name=name1059, terms=rel_terms1063)
        result1065 = _t1909
        self.record_span(span_start1064, "RelAtom")
        return result1065

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1068 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1910 = self.parse_term()
        term1066 = _t1910
        _t1911 = self.parse_term()
        term_31067 = _t1911
        self.consume_literal(")")
        _t1912 = logic_pb2.Cast(input=term1066, result=term_31067)
        result1069 = _t1912
        self.record_span(span_start1068, "Cast")
        return result1069

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1070 = []
        cond1071 = self.match_lookahead_literal("(", 0)
        while cond1071:
            _t1913 = self.parse_attribute()
            item1072 = _t1913
            xs1070.append(item1072)
            cond1071 = self.match_lookahead_literal("(", 0)
        attributes1073 = xs1070
        self.consume_literal(")")
        return attributes1073

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1079 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1914 = self.parse_name()
        name1074 = _t1914
        xs1075 = []
        cond1076 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1076:
            _t1915 = self.parse_raw_value()
            item1077 = _t1915
            xs1075.append(item1077)
            cond1076 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1078 = xs1075
        self.consume_literal(")")
        _t1916 = logic_pb2.Attribute(name=name1074, args=raw_values1078)
        result1080 = _t1916
        self.record_span(span_start1079, "Attribute")
        return result1080

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1087 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1081 = []
        cond1082 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1082:
            _t1917 = self.parse_relation_id()
            item1083 = _t1917
            xs1081.append(item1083)
            cond1082 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1084 = xs1081
        _t1918 = self.parse_script()
        script1085 = _t1918
        if self.match_lookahead_literal("(", 0):
            _t1920 = self.parse_attrs()
            _t1919 = _t1920
        else:
            _t1919 = None
        attrs1086 = _t1919
        self.consume_literal(")")
        _t1921 = logic_pb2.Algorithm(body=script1085, attrs=(attrs1086 if attrs1086 is not None else []))
        getattr(_t1921, 'global').extend(relation_ids1084)
        result1088 = _t1921
        self.record_span(span_start1087, "Algorithm")
        return result1088

    def parse_script(self) -> logic_pb2.Script:
        span_start1093 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1089 = []
        cond1090 = self.match_lookahead_literal("(", 0)
        while cond1090:
            _t1922 = self.parse_construct()
            item1091 = _t1922
            xs1089.append(item1091)
            cond1090 = self.match_lookahead_literal("(", 0)
        constructs1092 = xs1089
        self.consume_literal(")")
        _t1923 = logic_pb2.Script(constructs=constructs1092)
        result1094 = _t1923
        self.record_span(span_start1093, "Script")
        return result1094

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1098 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1925 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1926 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1927 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1928 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1929 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1930 = 1
                                else:
                                    _t1930 = -1
                                _t1929 = _t1930
                            _t1928 = _t1929
                        _t1927 = _t1928
                    _t1926 = _t1927
                _t1925 = _t1926
            _t1924 = _t1925
        else:
            _t1924 = -1
        prediction1095 = _t1924
        if prediction1095 == 1:
            _t1932 = self.parse_instruction()
            instruction1097 = _t1932
            _t1933 = logic_pb2.Construct(instruction=instruction1097)
            _t1931 = _t1933
        else:
            if prediction1095 == 0:
                _t1935 = self.parse_loop()
                loop1096 = _t1935
                _t1936 = logic_pb2.Construct(loop=loop1096)
                _t1934 = _t1936
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1931 = _t1934
        result1099 = _t1931
        self.record_span(span_start1098, "Construct")
        return result1099

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1103 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1937 = self.parse_init()
        init1100 = _t1937
        _t1938 = self.parse_script()
        script1101 = _t1938
        if self.match_lookahead_literal("(", 0):
            _t1940 = self.parse_attrs()
            _t1939 = _t1940
        else:
            _t1939 = None
        attrs1102 = _t1939
        self.consume_literal(")")
        _t1941 = logic_pb2.Loop(init=init1100, body=script1101, attrs=(attrs1102 if attrs1102 is not None else []))
        result1104 = _t1941
        self.record_span(span_start1103, "Loop")
        return result1104

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1105 = []
        cond1106 = self.match_lookahead_literal("(", 0)
        while cond1106:
            _t1942 = self.parse_instruction()
            item1107 = _t1942
            xs1105.append(item1107)
            cond1106 = self.match_lookahead_literal("(", 0)
        instructions1108 = xs1105
        self.consume_literal(")")
        return instructions1108

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1115 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1944 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1945 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1946 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1947 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1948 = 0
                            else:
                                _t1948 = -1
                            _t1947 = _t1948
                        _t1946 = _t1947
                    _t1945 = _t1946
                _t1944 = _t1945
            _t1943 = _t1944
        else:
            _t1943 = -1
        prediction1109 = _t1943
        if prediction1109 == 4:
            _t1950 = self.parse_monus_def()
            monus_def1114 = _t1950
            _t1951 = logic_pb2.Instruction(monus_def=monus_def1114)
            _t1949 = _t1951
        else:
            if prediction1109 == 3:
                _t1953 = self.parse_monoid_def()
                monoid_def1113 = _t1953
                _t1954 = logic_pb2.Instruction(monoid_def=monoid_def1113)
                _t1952 = _t1954
            else:
                if prediction1109 == 2:
                    _t1956 = self.parse_break()
                    break1112 = _t1956
                    _t1957 = logic_pb2.Instruction()
                    getattr(_t1957, 'break').CopyFrom(break1112)
                    _t1955 = _t1957
                else:
                    if prediction1109 == 1:
                        _t1959 = self.parse_upsert()
                        upsert1111 = _t1959
                        _t1960 = logic_pb2.Instruction(upsert=upsert1111)
                        _t1958 = _t1960
                    else:
                        if prediction1109 == 0:
                            _t1962 = self.parse_assign()
                            assign1110 = _t1962
                            _t1963 = logic_pb2.Instruction(assign=assign1110)
                            _t1961 = _t1963
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1958 = _t1961
                    _t1955 = _t1958
                _t1952 = _t1955
            _t1949 = _t1952
        result1116 = _t1949
        self.record_span(span_start1115, "Instruction")
        return result1116

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1120 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1964 = self.parse_relation_id()
        relation_id1117 = _t1964
        _t1965 = self.parse_abstraction()
        abstraction1118 = _t1965
        if self.match_lookahead_literal("(", 0):
            _t1967 = self.parse_attrs()
            _t1966 = _t1967
        else:
            _t1966 = None
        attrs1119 = _t1966
        self.consume_literal(")")
        _t1968 = logic_pb2.Assign(name=relation_id1117, body=abstraction1118, attrs=(attrs1119 if attrs1119 is not None else []))
        result1121 = _t1968
        self.record_span(span_start1120, "Assign")
        return result1121

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1125 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1969 = self.parse_relation_id()
        relation_id1122 = _t1969
        _t1970 = self.parse_abstraction_with_arity()
        abstraction_with_arity1123 = _t1970
        if self.match_lookahead_literal("(", 0):
            _t1972 = self.parse_attrs()
            _t1971 = _t1972
        else:
            _t1971 = None
        attrs1124 = _t1971
        self.consume_literal(")")
        _t1973 = logic_pb2.Upsert(name=relation_id1122, body=abstraction_with_arity1123[0], attrs=(attrs1124 if attrs1124 is not None else []), value_arity=abstraction_with_arity1123[1])
        result1126 = _t1973
        self.record_span(span_start1125, "Upsert")
        return result1126

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1974 = self.parse_bindings()
        bindings1127 = _t1974
        _t1975 = self.parse_formula()
        formula1128 = _t1975
        self.consume_literal(")")
        _t1976 = logic_pb2.Abstraction(vars=(list(bindings1127[0]) + list(bindings1127[1] if bindings1127[1] is not None else [])), value=formula1128)
        return (_t1976, len(bindings1127[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1132 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1977 = self.parse_relation_id()
        relation_id1129 = _t1977
        _t1978 = self.parse_abstraction()
        abstraction1130 = _t1978
        if self.match_lookahead_literal("(", 0):
            _t1980 = self.parse_attrs()
            _t1979 = _t1980
        else:
            _t1979 = None
        attrs1131 = _t1979
        self.consume_literal(")")
        _t1981 = logic_pb2.Break(name=relation_id1129, body=abstraction1130, attrs=(attrs1131 if attrs1131 is not None else []))
        result1133 = _t1981
        self.record_span(span_start1132, "Break")
        return result1133

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1138 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1982 = self.parse_monoid()
        monoid1134 = _t1982
        _t1983 = self.parse_relation_id()
        relation_id1135 = _t1983
        _t1984 = self.parse_abstraction_with_arity()
        abstraction_with_arity1136 = _t1984
        if self.match_lookahead_literal("(", 0):
            _t1986 = self.parse_attrs()
            _t1985 = _t1986
        else:
            _t1985 = None
        attrs1137 = _t1985
        self.consume_literal(")")
        _t1987 = logic_pb2.MonoidDef(monoid=monoid1134, name=relation_id1135, body=abstraction_with_arity1136[0], attrs=(attrs1137 if attrs1137 is not None else []), value_arity=abstraction_with_arity1136[1])
        result1139 = _t1987
        self.record_span(span_start1138, "MonoidDef")
        return result1139

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1145 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1989 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1990 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1991 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1992 = 2
                        else:
                            _t1992 = -1
                        _t1991 = _t1992
                    _t1990 = _t1991
                _t1989 = _t1990
            _t1988 = _t1989
        else:
            _t1988 = -1
        prediction1140 = _t1988
        if prediction1140 == 3:
            _t1994 = self.parse_sum_monoid()
            sum_monoid1144 = _t1994
            _t1995 = logic_pb2.Monoid(sum_monoid=sum_monoid1144)
            _t1993 = _t1995
        else:
            if prediction1140 == 2:
                _t1997 = self.parse_max_monoid()
                max_monoid1143 = _t1997
                _t1998 = logic_pb2.Monoid(max_monoid=max_monoid1143)
                _t1996 = _t1998
            else:
                if prediction1140 == 1:
                    _t2000 = self.parse_min_monoid()
                    min_monoid1142 = _t2000
                    _t2001 = logic_pb2.Monoid(min_monoid=min_monoid1142)
                    _t1999 = _t2001
                else:
                    if prediction1140 == 0:
                        _t2003 = self.parse_or_monoid()
                        or_monoid1141 = _t2003
                        _t2004 = logic_pb2.Monoid(or_monoid=or_monoid1141)
                        _t2002 = _t2004
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1999 = _t2002
                _t1996 = _t1999
            _t1993 = _t1996
        result1146 = _t1993
        self.record_span(span_start1145, "Monoid")
        return result1146

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1147 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t2005 = logic_pb2.OrMonoid()
        result1148 = _t2005
        self.record_span(span_start1147, "OrMonoid")
        return result1148

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1150 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t2006 = self.parse_type()
        type1149 = _t2006
        self.consume_literal(")")
        _t2007 = logic_pb2.MinMonoid(type=type1149)
        result1151 = _t2007
        self.record_span(span_start1150, "MinMonoid")
        return result1151

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1153 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t2008 = self.parse_type()
        type1152 = _t2008
        self.consume_literal(")")
        _t2009 = logic_pb2.MaxMonoid(type=type1152)
        result1154 = _t2009
        self.record_span(span_start1153, "MaxMonoid")
        return result1154

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1156 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t2010 = self.parse_type()
        type1155 = _t2010
        self.consume_literal(")")
        _t2011 = logic_pb2.SumMonoid(type=type1155)
        result1157 = _t2011
        self.record_span(span_start1156, "SumMonoid")
        return result1157

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1162 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t2012 = self.parse_monoid()
        monoid1158 = _t2012
        _t2013 = self.parse_relation_id()
        relation_id1159 = _t2013
        _t2014 = self.parse_abstraction_with_arity()
        abstraction_with_arity1160 = _t2014
        if self.match_lookahead_literal("(", 0):
            _t2016 = self.parse_attrs()
            _t2015 = _t2016
        else:
            _t2015 = None
        attrs1161 = _t2015
        self.consume_literal(")")
        _t2017 = logic_pb2.MonusDef(monoid=monoid1158, name=relation_id1159, body=abstraction_with_arity1160[0], attrs=(attrs1161 if attrs1161 is not None else []), value_arity=abstraction_with_arity1160[1])
        result1163 = _t2017
        self.record_span(span_start1162, "MonusDef")
        return result1163

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1168 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t2018 = self.parse_relation_id()
        relation_id1164 = _t2018
        _t2019 = self.parse_abstraction()
        abstraction1165 = _t2019
        _t2020 = self.parse_functional_dependency_keys()
        functional_dependency_keys1166 = _t2020
        _t2021 = self.parse_functional_dependency_values()
        functional_dependency_values1167 = _t2021
        self.consume_literal(")")
        _t2022 = logic_pb2.FunctionalDependency(guard=abstraction1165, keys=functional_dependency_keys1166, values=functional_dependency_values1167)
        _t2023 = logic_pb2.Constraint(name=relation_id1164, functional_dependency=_t2022)
        result1169 = _t2023
        self.record_span(span_start1168, "Constraint")
        return result1169

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1170 = []
        cond1171 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1171:
            _t2024 = self.parse_var()
            item1172 = _t2024
            xs1170.append(item1172)
            cond1171 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1173 = xs1170
        self.consume_literal(")")
        return vars1173

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1174 = []
        cond1175 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1175:
            _t2025 = self.parse_var()
            item1176 = _t2025
            xs1174.append(item1176)
            cond1175 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1177 = xs1174
        self.consume_literal(")")
        return vars1177

    def parse_data(self) -> logic_pb2.Data:
        span_start1183 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t2027 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t2028 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t2029 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t2030 = 1
                        else:
                            _t2030 = -1
                        _t2029 = _t2030
                    _t2028 = _t2029
                _t2027 = _t2028
            _t2026 = _t2027
        else:
            _t2026 = -1
        prediction1178 = _t2026
        if prediction1178 == 3:
            _t2032 = self.parse_iceberg_data()
            iceberg_data1182 = _t2032
            _t2033 = logic_pb2.Data(iceberg_data=iceberg_data1182)
            _t2031 = _t2033
        else:
            if prediction1178 == 2:
                _t2035 = self.parse_csv_data()
                csv_data1181 = _t2035
                _t2036 = logic_pb2.Data(csv_data=csv_data1181)
                _t2034 = _t2036
            else:
                if prediction1178 == 1:
                    _t2038 = self.parse_betree_relation()
                    betree_relation1180 = _t2038
                    _t2039 = logic_pb2.Data(betree_relation=betree_relation1180)
                    _t2037 = _t2039
                else:
                    if prediction1178 == 0:
                        _t2041 = self.parse_edb()
                        edb1179 = _t2041
                        _t2042 = logic_pb2.Data(edb=edb1179)
                        _t2040 = _t2042
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t2037 = _t2040
                _t2034 = _t2037
            _t2031 = _t2034
        result1184 = _t2031
        self.record_span(span_start1183, "Data")
        return result1184

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1188 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t2043 = self.parse_relation_id()
        relation_id1185 = _t2043
        _t2044 = self.parse_edb_path()
        edb_path1186 = _t2044
        _t2045 = self.parse_edb_types()
        edb_types1187 = _t2045
        self.consume_literal(")")
        _t2046 = logic_pb2.EDB(target_id=relation_id1185, path=edb_path1186, types=edb_types1187)
        result1189 = _t2046
        self.record_span(span_start1188, "EDB")
        return result1189

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1190 = []
        cond1191 = self.match_lookahead_terminal("STRING", 0)
        while cond1191:
            item1192 = self.consume_terminal("STRING")
            xs1190.append(item1192)
            cond1191 = self.match_lookahead_terminal("STRING", 0)
        strings1193 = xs1190
        self.consume_literal("]")
        return strings1193

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1194 = []
        cond1195 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1195:
            _t2047 = self.parse_type()
            item1196 = _t2047
            xs1194.append(item1196)
            cond1195 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1197 = xs1194
        self.consume_literal("]")
        return types1197

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1200 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t2048 = self.parse_relation_id()
        relation_id1198 = _t2048
        _t2049 = self.parse_betree_info()
        betree_info1199 = _t2049
        self.consume_literal(")")
        _t2050 = logic_pb2.BeTreeRelation(name=relation_id1198, relation_info=betree_info1199)
        result1201 = _t2050
        self.record_span(span_start1200, "BeTreeRelation")
        return result1201

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1205 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t2051 = self.parse_betree_info_key_types()
        betree_info_key_types1202 = _t2051
        _t2052 = self.parse_betree_info_value_types()
        betree_info_value_types1203 = _t2052
        _t2053 = self.parse_config_dict()
        config_dict1204 = _t2053
        self.consume_literal(")")
        _t2054 = self.construct_betree_info(betree_info_key_types1202, betree_info_value_types1203, config_dict1204)
        result1206 = _t2054
        self.record_span(span_start1205, "BeTreeInfo")
        return result1206

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1207 = []
        cond1208 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1208:
            _t2055 = self.parse_type()
            item1209 = _t2055
            xs1207.append(item1209)
            cond1208 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1210 = xs1207
        self.consume_literal(")")
        return types1210

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1211 = []
        cond1212 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1212:
            _t2056 = self.parse_type()
            item1213 = _t2056
            xs1211.append(item1213)
            cond1212 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1214 = xs1211
        self.consume_literal(")")
        return types1214

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1220 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t2057 = self.parse_csvlocator()
        csvlocator1215 = _t2057
        _t2058 = self.parse_csv_config()
        csv_config1216 = _t2058
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("columns", 1)):
            _t2060 = self.parse_gnf_columns()
            _t2059 = _t2060
        else:
            _t2059 = None
        gnf_columns1217 = _t2059
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("relations", 1)):
            _t2062 = self.parse_target_relations()
            _t2061 = _t2062
        else:
            _t2061 = None
        target_relations1218 = _t2061
        _t2063 = self.parse_csv_asof()
        csv_asof1219 = _t2063
        self.consume_literal(")")
        _t2064 = self.construct_csv_data(csvlocator1215, csv_config1216, gnf_columns1217, target_relations1218, csv_asof1219)
        result1221 = _t2064
        self.record_span(span_start1220, "CSVData")
        return result1221

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1224 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t2066 = self.parse_csv_locator_paths()
            _t2065 = _t2066
        else:
            _t2065 = None
        csv_locator_paths1222 = _t2065
        if self.match_lookahead_literal("(", 0):
            _t2068 = self.parse_csv_locator_inline_data()
            _t2067 = _t2068
        else:
            _t2067 = None
        csv_locator_inline_data1223 = _t2067
        self.consume_literal(")")
        _t2069 = logic_pb2.CSVLocator(paths=(csv_locator_paths1222 if csv_locator_paths1222 is not None else []), inline_data=(csv_locator_inline_data1223 if csv_locator_inline_data1223 is not None else "").encode())
        result1225 = _t2069
        self.record_span(span_start1224, "CSVLocator")
        return result1225

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1226 = []
        cond1227 = self.match_lookahead_terminal("STRING", 0)
        while cond1227:
            item1228 = self.consume_terminal("STRING")
            xs1226.append(item1228)
            cond1227 = self.match_lookahead_terminal("STRING", 0)
        strings1229 = xs1226
        self.consume_literal(")")
        return strings1229

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        formatted_string1230 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return formatted_string1230

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1233 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t2070 = self.parse_config_dict()
        config_dict1231 = _t2070
        if self.match_lookahead_literal("(", 0):
            _t2072 = self.parse__storage_integration()
            _t2071 = _t2072
        else:
            _t2071 = None
        _storage_integration1232 = _t2071
        self.consume_literal(")")
        _t2073 = self.construct_csv_config(config_dict1231, _storage_integration1232)
        result1234 = _t2073
        self.record_span(span_start1233, "CSVConfig")
        return result1234

    def parse__storage_integration(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("(")
        self.consume_literal("storage_integration")
        _t2074 = self.parse_config_dict()
        config_dict1235 = _t2074
        self.consume_literal(")")
        return config_dict1235

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1236 = []
        cond1237 = self.match_lookahead_literal("(", 0)
        while cond1237:
            _t2075 = self.parse_gnf_column()
            item1238 = _t2075
            xs1236.append(item1238)
            cond1237 = self.match_lookahead_literal("(", 0)
        gnf_columns1239 = xs1236
        self.consume_literal(")")
        return gnf_columns1239

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1246 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t2076 = self.parse_gnf_column_path()
        gnf_column_path1240 = _t2076
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t2078 = self.parse_relation_id()
            _t2077 = _t2078
        else:
            _t2077 = None
        relation_id1241 = _t2077
        self.consume_literal("[")
        xs1242 = []
        cond1243 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1243:
            _t2079 = self.parse_type()
            item1244 = _t2079
            xs1242.append(item1244)
            cond1243 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1245 = xs1242
        self.consume_literal("]")
        self.consume_literal(")")
        _t2080 = logic_pb2.GNFColumn(column_path=gnf_column_path1240, target_id=relation_id1241, types=types1245)
        result1247 = _t2080
        self.record_span(span_start1246, "GNFColumn")
        return result1247

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t2081 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t2082 = 0
            else:
                _t2082 = -1
            _t2081 = _t2082
        prediction1248 = _t2081
        if prediction1248 == 1:
            self.consume_literal("[")
            xs1250 = []
            cond1251 = self.match_lookahead_terminal("STRING", 0)
            while cond1251:
                item1252 = self.consume_terminal("STRING")
                xs1250.append(item1252)
                cond1251 = self.match_lookahead_terminal("STRING", 0)
            strings1253 = xs1250
            self.consume_literal("]")
            _t2083 = strings1253
        else:
            if prediction1248 == 0:
                string1249 = self.consume_terminal("STRING")
                _t2084 = [string1249]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2083 = _t2084
        return _t2083

    def parse_target_relations(self) -> logic_pb2.TargetRelations:
        span_start1257 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relations")
        _t2085 = self.parse_relation_keys()
        relation_keys1254 = _t2085
        _t2086 = self.parse_relation_body()
        relation_body1255 = _t2086
        if self.match_lookahead_literal("(", 0):
            _t2088 = self.parse_load_errors()
            _t2087 = _t2088
        else:
            _t2087 = None
        load_errors1256 = _t2087
        self.consume_literal(")")
        _t2089 = self.construct_relations(relation_keys1254, relation_body1255, load_errors1256)
        result1258 = _t2089
        self.record_span(span_start1257, "TargetRelations")
        return result1258

    def parse_relation_keys(self) -> tuple[Sequence[logic_pb2.NamedColumn], bool]:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("keys", 1):
                if self.match_lookahead_literal("synthetic", 2):
                    _t2092 = 1
                else:
                    if self.match_lookahead_literal(")", 2):
                        _t2093 = 0
                    else:
                        if self.match_lookahead_literal("(", 2):
                            _t2094 = 0
                        else:
                            _t2094 = -1
                        _t2093 = _t2094
                    _t2092 = _t2093
                _t2091 = _t2092
            else:
                _t2091 = -1
            _t2090 = _t2091
        else:
            _t2090 = -1
        prediction1259 = _t2090
        if prediction1259 == 1:
            self.consume_literal("(")
            self.consume_literal("keys")
            self.consume_literal("synthetic")
            self.consume_literal(")")
            _t2095 = ([], True,)
        else:
            if prediction1259 == 0:
                self.consume_literal("(")
                self.consume_literal("keys")
                xs1260 = []
                cond1261 = self.match_lookahead_literal("(", 0)
                while cond1261:
                    _t2097 = self.parse_named_column()
                    item1262 = _t2097
                    xs1260.append(item1262)
                    cond1261 = self.match_lookahead_literal("(", 0)
                named_columns1263 = xs1260
                self.consume_literal(")")
                _t2096 = (named_columns1263, False,)
            else:
                raise ParseError("Unexpected token in relation_keys" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2095 = _t2096
        return _t2095

    def parse_named_column(self) -> logic_pb2.NamedColumn:
        span_start1266 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1264 = self.consume_terminal("STRING")
        _t2098 = self.parse_type()
        type1265 = _t2098
        self.consume_literal(")")
        _t2099 = logic_pb2.NamedColumn(name=string1264, type=type1265)
        result1267 = _t2099
        self.record_span(span_start1266, "NamedColumn")
        return result1267

    def parse_relation_body(self) -> logic_pb2.TargetRelations:
        span_start1272 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("relation", 1):
                _t2101 = 0
            else:
                if self.match_lookahead_literal("inserts", 1):
                    _t2102 = 1
                else:
                    _t2102 = 0
                _t2101 = _t2102
            _t2100 = _t2101
        else:
            _t2100 = 0
        prediction1268 = _t2100
        if prediction1268 == 1:
            _t2104 = self.parse_cdc_inserts()
            cdc_inserts1270 = _t2104
            _t2105 = self.parse_cdc_deletes()
            cdc_deletes1271 = _t2105
            _t2106 = self.construct_cdc_relations(cdc_inserts1270, cdc_deletes1271)
            _t2103 = _t2106
        else:
            if prediction1268 == 0:
                _t2108 = self.parse_non_cdc_relations()
                non_cdc_relations1269 = _t2108
                _t2109 = self.construct_non_cdc_relations(non_cdc_relations1269)
                _t2107 = _t2109
            else:
                raise ParseError("Unexpected token in relation_body" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2103 = _t2107
        result1273 = _t2103
        self.record_span(span_start1272, "TargetRelations")
        return result1273

    def parse_non_cdc_relations(self) -> Sequence[logic_pb2.TargetRelation]:
        xs1274 = []
        cond1275 = (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("relation", 1))
        while cond1275:
            _t2110 = self.parse_target_relation()
            item1276 = _t2110
            xs1274.append(item1276)
            cond1275 = (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("relation", 1))
        return xs1274

    def parse_target_relation(self) -> logic_pb2.TargetRelation:
        span_start1282 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relation")
        _t2111 = self.parse_relation_id()
        relation_id1277 = _t2111
        xs1278 = []
        cond1279 = self.match_lookahead_literal("(", 0)
        while cond1279:
            _t2112 = self.parse_named_column()
            item1280 = _t2112
            xs1278.append(item1280)
            cond1279 = self.match_lookahead_literal("(", 0)
        named_columns1281 = xs1278
        self.consume_literal(")")
        _t2113 = logic_pb2.TargetRelation(target_id=relation_id1277, values=named_columns1281)
        result1283 = _t2113
        self.record_span(span_start1282, "TargetRelation")
        return result1283

    def parse_cdc_inserts(self) -> Sequence[logic_pb2.TargetRelation]:
        self.consume_literal("(")
        self.consume_literal("inserts")
        xs1284 = []
        cond1285 = self.match_lookahead_literal("(", 0)
        while cond1285:
            _t2114 = self.parse_target_relation()
            item1286 = _t2114
            xs1284.append(item1286)
            cond1285 = self.match_lookahead_literal("(", 0)
        target_relations1287 = xs1284
        self.consume_literal(")")
        return target_relations1287

    def parse_cdc_deletes(self) -> Sequence[logic_pb2.TargetRelation]:
        self.consume_literal("(")
        self.consume_literal("deletes")
        xs1288 = []
        cond1289 = self.match_lookahead_literal("(", 0)
        while cond1289:
            _t2115 = self.parse_target_relation()
            item1290 = _t2115
            xs1288.append(item1290)
            cond1289 = self.match_lookahead_literal("(", 0)
        target_relations1291 = xs1288
        self.consume_literal(")")
        return target_relations1291

    def parse_load_errors(self) -> logic_pb2.RelationId:
        span_start1293 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("load_errors")
        _t2116 = self.parse_relation_id()
        relation_id1292 = _t2116
        self.consume_literal(")")
        result1294 = relation_id1292
        self.record_span(span_start1293, "RelationId")
        return result1294

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1295 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1295

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1302 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t2117 = self.parse_iceberg_locator()
        iceberg_locator1296 = _t2117
        _t2118 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1297 = _t2118
        _t2119 = self.parse_gnf_columns()
        gnf_columns1298 = _t2119
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t2121 = self.parse_iceberg_from_snapshot()
            _t2120 = _t2121
        else:
            _t2120 = None
        iceberg_from_snapshot1299 = _t2120
        if self.match_lookahead_literal("(", 0):
            _t2123 = self.parse_iceberg_to_snapshot()
            _t2122 = _t2123
        else:
            _t2122 = None
        iceberg_to_snapshot1300 = _t2122
        _t2124 = self.parse_boolean_value()
        boolean_value1301 = _t2124
        self.consume_literal(")")
        _t2125 = self.construct_iceberg_data(iceberg_locator1296, iceberg_catalog_config1297, gnf_columns1298, iceberg_from_snapshot1299, iceberg_to_snapshot1300, boolean_value1301)
        result1303 = _t2125
        self.record_span(span_start1302, "IcebergData")
        return result1303

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1307 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t2126 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1304 = _t2126
        _t2127 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1305 = _t2127
        _t2128 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1306 = _t2128
        self.consume_literal(")")
        _t2129 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1304, namespace=iceberg_locator_namespace1305, warehouse=iceberg_locator_warehouse1306)
        result1308 = _t2129
        self.record_span(span_start1307, "IcebergLocator")
        return result1308

    def parse_iceberg_locator_table_name(self) -> str:
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1309 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1309

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1310 = []
        cond1311 = self.match_lookahead_terminal("STRING", 0)
        while cond1311:
            item1312 = self.consume_terminal("STRING")
            xs1310.append(item1312)
            cond1311 = self.match_lookahead_terminal("STRING", 0)
        strings1313 = xs1310
        self.consume_literal(")")
        return strings1313

    def parse_iceberg_locator_warehouse(self) -> str:
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string1314 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1314

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1319 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t2130 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1315 = _t2130
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t2132 = self.parse_iceberg_catalog_config_scope()
            _t2131 = _t2132
        else:
            _t2131 = None
        iceberg_catalog_config_scope1316 = _t2131
        _t2133 = self.parse_iceberg_properties()
        iceberg_properties1317 = _t2133
        _t2134 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1318 = _t2134
        self.consume_literal(")")
        _t2135 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1315, iceberg_catalog_config_scope1316, iceberg_properties1317, iceberg_auth_properties1318)
        result1320 = _t2135
        self.record_span(span_start1319, "IcebergCatalogConfig")
        return result1320

    def parse_iceberg_catalog_uri(self) -> str:
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1321 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1321

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1322 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1322

    def parse_iceberg_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1323 = []
        cond1324 = self.match_lookahead_literal("(", 0)
        while cond1324:
            _t2136 = self.parse_iceberg_property_entry()
            item1325 = _t2136
            xs1323.append(item1325)
            cond1324 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1326 = xs1323
        self.consume_literal(")")
        return iceberg_property_entrys1326

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1327 = self.consume_terminal("STRING")
        string_31328 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1327, string_31328,)

    def parse_iceberg_auth_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1329 = []
        cond1330 = self.match_lookahead_literal("(", 0)
        while cond1330:
            _t2137 = self.parse_iceberg_masked_property_entry()
            item1331 = _t2137
            xs1329.append(item1331)
            cond1330 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1332 = xs1329
        self.consume_literal(")")
        return iceberg_masked_property_entrys1332

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1333 = self.consume_terminal("STRING")
        string_31334 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1333, string_31334,)

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1335 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1335

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1336 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1336

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1338 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2138 = self.parse_fragment_id()
        fragment_id1337 = _t2138
        self.consume_literal(")")
        _t2139 = transactions_pb2.Undefine(fragment_id=fragment_id1337)
        result1339 = _t2139
        self.record_span(span_start1338, "Undefine")
        return result1339

    def parse_context(self) -> transactions_pb2.Context:
        span_start1344 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1340 = []
        cond1341 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1341:
            _t2140 = self.parse_relation_id()
            item1342 = _t2140
            xs1340.append(item1342)
            cond1341 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1343 = xs1340
        self.consume_literal(")")
        _t2141 = transactions_pb2.Context(relations=relation_ids1343)
        result1345 = _t2141
        self.record_span(span_start1344, "Context")
        return result1345

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1351 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t2142 = self.parse_edb_path()
        edb_path1346 = _t2142
        xs1347 = []
        cond1348 = self.match_lookahead_literal("[", 0)
        while cond1348:
            _t2143 = self.parse_snapshot_mapping()
            item1349 = _t2143
            xs1347.append(item1349)
            cond1348 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1350 = xs1347
        self.consume_literal(")")
        _t2144 = transactions_pb2.Snapshot(prefix=edb_path1346, mappings=snapshot_mappings1350)
        result1352 = _t2144
        self.record_span(span_start1351, "Snapshot")
        return result1352

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1355 = self.span_start()
        _t2145 = self.parse_edb_path()
        edb_path1353 = _t2145
        _t2146 = self.parse_relation_id()
        relation_id1354 = _t2146
        _t2147 = transactions_pb2.SnapshotMapping(destination_path=edb_path1353, source_relation=relation_id1354)
        result1356 = _t2147
        self.record_span(span_start1355, "SnapshotMapping")
        return result1356

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1357 = []
        cond1358 = self.match_lookahead_literal("(", 0)
        while cond1358:
            _t2148 = self.parse_read()
            item1359 = _t2148
            xs1357.append(item1359)
            cond1358 = self.match_lookahead_literal("(", 0)
        reads1360 = xs1357
        self.consume_literal(")")
        return reads1360

    def parse_read(self) -> transactions_pb2.Read:
        span_start1367 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2150 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2151 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t2152 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t2153 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t2154 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t2155 = 3
                                else:
                                    _t2155 = -1
                                _t2154 = _t2155
                            _t2153 = _t2154
                        _t2152 = _t2153
                    _t2151 = _t2152
                _t2150 = _t2151
            _t2149 = _t2150
        else:
            _t2149 = -1
        prediction1361 = _t2149
        if prediction1361 == 4:
            _t2157 = self.parse_export()
            export1366 = _t2157
            _t2158 = transactions_pb2.Read(export=export1366)
            _t2156 = _t2158
        else:
            if prediction1361 == 3:
                _t2160 = self.parse_abort()
                abort1365 = _t2160
                _t2161 = transactions_pb2.Read(abort=abort1365)
                _t2159 = _t2161
            else:
                if prediction1361 == 2:
                    _t2163 = self.parse_what_if()
                    what_if1364 = _t2163
                    _t2164 = transactions_pb2.Read(what_if=what_if1364)
                    _t2162 = _t2164
                else:
                    if prediction1361 == 1:
                        _t2166 = self.parse_output()
                        output1363 = _t2166
                        _t2167 = transactions_pb2.Read(output=output1363)
                        _t2165 = _t2167
                    else:
                        if prediction1361 == 0:
                            _t2169 = self.parse_demand()
                            demand1362 = _t2169
                            _t2170 = transactions_pb2.Read(demand=demand1362)
                            _t2168 = _t2170
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2165 = _t2168
                    _t2162 = _t2165
                _t2159 = _t2162
            _t2156 = _t2159
        result1368 = _t2156
        self.record_span(span_start1367, "Read")
        return result1368

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1370 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2171 = self.parse_relation_id()
        relation_id1369 = _t2171
        self.consume_literal(")")
        _t2172 = transactions_pb2.Demand(relation_id=relation_id1369)
        result1371 = _t2172
        self.record_span(span_start1370, "Demand")
        return result1371

    def parse_output(self) -> transactions_pb2.Output:
        span_start1374 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2173 = self.parse_name()
        name1372 = _t2173
        _t2174 = self.parse_relation_id()
        relation_id1373 = _t2174
        self.consume_literal(")")
        _t2175 = transactions_pb2.Output(name=name1372, relation_id=relation_id1373)
        result1375 = _t2175
        self.record_span(span_start1374, "Output")
        return result1375

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1378 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2176 = self.parse_name()
        name1376 = _t2176
        _t2177 = self.parse_epoch()
        epoch1377 = _t2177
        self.consume_literal(")")
        _t2178 = transactions_pb2.WhatIf(branch=name1376, epoch=epoch1377)
        result1379 = _t2178
        self.record_span(span_start1378, "WhatIf")
        return result1379

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1382 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2180 = self.parse_name()
            _t2179 = _t2180
        else:
            _t2179 = None
        name1380 = _t2179
        _t2181 = self.parse_relation_id()
        relation_id1381 = _t2181
        self.consume_literal(")")
        _t2182 = transactions_pb2.Abort(name=(name1380 if name1380 is not None else "abort"), relation_id=relation_id1381)
        result1383 = _t2182
        self.record_span(span_start1382, "Abort")
        return result1383

    def parse_export(self) -> transactions_pb2.Export:
        span_start1387 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2184 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2185 = 0
                else:
                    _t2185 = -1
                _t2184 = _t2185
            _t2183 = _t2184
        else:
            _t2183 = -1
        prediction1384 = _t2183
        if prediction1384 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2187 = self.parse_export_iceberg_config()
            export_iceberg_config1386 = _t2187
            self.consume_literal(")")
            _t2188 = transactions_pb2.Export(iceberg_config=export_iceberg_config1386)
            _t2186 = _t2188
        else:
            if prediction1384 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2190 = self.parse_export_csv_config()
                export_csv_config1385 = _t2190
                self.consume_literal(")")
                _t2191 = transactions_pb2.Export(csv_config=export_csv_config1385)
                _t2189 = _t2191
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2186 = _t2189
        result1388 = _t2186
        self.record_span(span_start1387, "Export")
        return result1388

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1396 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2193 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2194 = 1
                else:
                    _t2194 = -1
                _t2193 = _t2194
            _t2192 = _t2193
        else:
            _t2192 = -1
        prediction1389 = _t2192
        if prediction1389 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2196 = self.parse_export_csv_path()
            export_csv_path1393 = _t2196
            _t2197 = self.parse_export_csv_columns_list()
            export_csv_columns_list1394 = _t2197
            _t2198 = self.parse_config_dict()
            config_dict1395 = _t2198
            self.consume_literal(")")
            _t2199 = self.construct_export_csv_config(export_csv_path1393, export_csv_columns_list1394, config_dict1395)
            _t2195 = _t2199
        else:
            if prediction1389 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2201 = self.parse_export_csv_output_location()
                export_csv_output_location1390 = _t2201
                _t2202 = self.parse_export_csv_source()
                export_csv_source1391 = _t2202
                _t2203 = self.parse_csv_config()
                csv_config1392 = _t2203
                self.consume_literal(")")
                _t2204 = self.construct_export_csv_config_with_location(export_csv_output_location1390, export_csv_source1391, csv_config1392)
                _t2200 = _t2204
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2195 = _t2200
        result1397 = _t2195
        self.record_span(span_start1396, "ExportCSVConfig")
        return result1397

    def parse_export_csv_output_location(self) -> tuple[str, str]:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("transaction_output_name", 1):
                _t2206 = 1
            else:
                if self.match_lookahead_literal("path", 1):
                    _t2207 = 0
                else:
                    _t2207 = -1
                _t2206 = _t2207
            _t2205 = _t2206
        else:
            _t2205 = -1
        prediction1398 = _t2205
        if prediction1398 == 1:
            self.consume_literal("(")
            self.consume_literal("transaction_output_name")
            _t2209 = self.parse_name()
            name1400 = _t2209
            self.consume_literal(")")
            _t2208 = ("", name1400,)
        else:
            if prediction1398 == 0:
                self.consume_literal("(")
                self.consume_literal("path")
                string1399 = self.consume_terminal("STRING")
                self.consume_literal(")")
                _t2210 = (string1399, "",)
            else:
                raise ParseError("Unexpected token in export_csv_output_location" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2208 = _t2210
        return _t2208

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1407 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2212 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2213 = 0
                else:
                    _t2213 = -1
                _t2212 = _t2213
            _t2211 = _t2212
        else:
            _t2211 = -1
        prediction1401 = _t2211
        if prediction1401 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2215 = self.parse_relation_id()
            relation_id1406 = _t2215
            self.consume_literal(")")
            _t2216 = transactions_pb2.ExportCSVSource(table_def=relation_id1406)
            _t2214 = _t2216
        else:
            if prediction1401 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1402 = []
                cond1403 = self.match_lookahead_literal("(", 0)
                while cond1403:
                    _t2218 = self.parse_export_csv_column()
                    item1404 = _t2218
                    xs1402.append(item1404)
                    cond1403 = self.match_lookahead_literal("(", 0)
                export_csv_columns1405 = xs1402
                self.consume_literal(")")
                _t2219 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1405)
                _t2220 = transactions_pb2.ExportCSVSource(gnf_columns=_t2219)
                _t2217 = _t2220
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2214 = _t2217
        result1408 = _t2214
        self.record_span(span_start1407, "ExportCSVSource")
        return result1408

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1411 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1409 = self.consume_terminal("STRING")
        _t2221 = self.parse_relation_id()
        relation_id1410 = _t2221
        self.consume_literal(")")
        _t2222 = transactions_pb2.ExportCSVColumn(column_name=string1409, column_data=relation_id1410)
        result1412 = _t2222
        self.record_span(span_start1411, "ExportCSVColumn")
        return result1412

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1413 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1413

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1414 = []
        cond1415 = self.match_lookahead_literal("(", 0)
        while cond1415:
            _t2223 = self.parse_export_csv_column()
            item1416 = _t2223
            xs1414.append(item1416)
            cond1415 = self.match_lookahead_literal("(", 0)
        export_csv_columns1417 = xs1414
        self.consume_literal(")")
        return export_csv_columns1417

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1423 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2224 = self.parse_iceberg_locator()
        iceberg_locator1418 = _t2224
        _t2225 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1419 = _t2225
        _t2226 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1420 = _t2226
        _t2227 = self.parse_iceberg_table_properties()
        iceberg_table_properties1421 = _t2227
        if self.match_lookahead_literal("{", 0):
            _t2229 = self.parse_config_dict()
            _t2228 = _t2229
        else:
            _t2228 = None
        config_dict1422 = _t2228
        self.consume_literal(")")
        _t2230 = self.construct_export_iceberg_config_full(iceberg_locator1418, iceberg_catalog_config1419, export_iceberg_table_def1420, iceberg_table_properties1421, config_dict1422)
        result1424 = _t2230
        self.record_span(span_start1423, "ExportIcebergConfig")
        return result1424

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1426 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2231 = self.parse_relation_id()
        relation_id1425 = _t2231
        self.consume_literal(")")
        result1427 = relation_id1425
        self.record_span(span_start1426, "RelationId")
        return result1427

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1428 = []
        cond1429 = self.match_lookahead_literal("(", 0)
        while cond1429:
            _t2232 = self.parse_iceberg_property_entry()
            item1430 = _t2232
            xs1428.append(item1430)
            cond1429 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1431 = xs1428
        self.consume_literal(")")
        return iceberg_property_entrys1431


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
