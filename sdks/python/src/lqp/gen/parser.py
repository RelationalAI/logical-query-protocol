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
            _t2219 = None
        assert value is not None
        if value.HasField("int32_value"):
            assert value is not None
            return value.int32_value
        else:
            _t2220 = None
        raise ParseError("expected an int32 value (e.g. `1i32`) for this config field")

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2221 = value.HasField("int_value")
        else:
            _t2221 = False
        if _t2221:
            assert value is not None
            return value.int_value
        else:
            _t2222 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2223 = value.HasField("string_value")
        else:
            _t2223 = False
        if _t2223:
            assert value is not None
            return value.string_value
        else:
            _t2224 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2225 = value.HasField("boolean_value")
        else:
            _t2225 = False
        if _t2225:
            assert value is not None
            return value.boolean_value
        else:
            _t2226 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2227 = value.HasField("string_value")
        else:
            _t2227 = False
        if _t2227:
            assert value is not None
            return [value.string_value]
        else:
            _t2228 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2229 = value.HasField("int_value")
        else:
            _t2229 = False
        if _t2229:
            assert value is not None
            return value.int_value
        else:
            _t2230 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2231 = value.HasField("float_value")
        else:
            _t2231 = False
        if _t2231:
            assert value is not None
            return value.float_value
        else:
            _t2232 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2233 = value.HasField("string_value")
        else:
            _t2233 = False
        if _t2233:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2234 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2235 = value.HasField("uint128_value")
        else:
            _t2235 = False
        if _t2235:
            assert value is not None
            return value.uint128_value
        else:
            _t2236 = None
        return None

    def construct_non_cdc_relations(self, targets: Sequence[logic_pb2.TargetRelation]) -> logic_pb2.TargetRelations:
        _t2237 = logic_pb2.PlainTargets(targets=targets)
        _t2238 = logic_pb2.TargetRelations(keys=[], plain=_t2237)
        return _t2238

    def construct_cdc_relations(self, inserts: Sequence[logic_pb2.TargetRelation], deletes: Sequence[logic_pb2.TargetRelation]) -> logic_pb2.TargetRelations:
        _t2239 = logic_pb2.CDCTargets(inserts=inserts, deletes=deletes)
        _t2240 = logic_pb2.TargetRelations(keys=[], cdc=_t2239)
        return _t2240

    def construct_relations(self, keys: tuple[Sequence[logic_pb2.NamedColumn], bool], body: logic_pb2.TargetRelations, load_errors_opt: logic_pb2.RelationId | None) -> logic_pb2.TargetRelations:
        if body.HasField("plain"):
            _t2242 = logic_pb2.TargetRelations(keys=keys[0], synthetic_key=keys[1], plain=body.plain, load_errors=load_errors_opt)
            return _t2242
        else:
            _t2241 = None
        _t2243 = logic_pb2.TargetRelations(keys=keys[0], synthetic_key=keys[1], cdc=body.cdc, load_errors=load_errors_opt)
        return _t2243

    def construct_csv_data(self, locator: logic_pb2.CSVLocator, config: logic_pb2.CSVConfig, columns_opt: Sequence[logic_pb2.GNFColumn] | None, relations_opt: logic_pb2.TargetRelations | None, asof: str) -> logic_pb2.CSVData:
        _t2244 = logic_pb2.CSVData(locator=locator, config=config, columns=(columns_opt if columns_opt is not None else []), asof=asof, relations=relations_opt)
        return _t2244

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]], storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2245 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2245
        _t2246 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2246
        _t2247 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2247
        _t2248 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2248
        _t2249 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2249
        _t2250 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2250
        _t2251 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2251
        _t2252 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2252
        _t2253 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2253
        _t2254 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2254
        _t2255 = self._extract_value_string(config.get("csv_compression"), "")
        compression = _t2255
        _t2256 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2256
        _t2257 = self.construct_csv_storage_integration(storage_integration_opt)
        storage_integration = _t2257
        _t2258 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
        return _t2258

    def construct_csv_storage_integration(self, storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.StorageIntegration | None:
        if storage_integration_opt is None:
            return None
        else:
            _t2259 = None
        assert storage_integration_opt is not None
        config = dict(storage_integration_opt)
        _t2260 = self._extract_value_string(config.get("provider"), "")
        _t2261 = self._extract_value_string(config.get("azure_sas_token"), "")
        _t2262 = self._extract_value_string(config.get("s3_region"), "")
        _t2263 = self._extract_value_string(config.get("s3_access_key_id"), "")
        _t2264 = self._extract_value_string(config.get("s3_secret_access_key"), "")
        _t2265 = logic_pb2.StorageIntegration(provider=_t2260, azure_sas_token=_t2261, s3_region=_t2262, s3_access_key_id=_t2263, s3_secret_access_key=_t2264)
        return _t2265

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2266 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2266
        _t2267 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2267
        _t2268 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2268
        _t2269 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2269
        _t2270 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2270
        _t2271 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2271
        _t2272 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2272
        _t2273 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2273
        _t2274 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2274
        _t2275 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2275
        _t2276 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2276

    def default_configure(self) -> transactions_pb2.Configure:
        _t2277 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2277
        _t2278 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2278

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
        _t2279 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2279
        _t2280 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2280
        config_values_pairs = []
        for pair in config_dict:
            if (pair[0] != "semantics_version" and pair[0] != "ivm.maintenance_level"):
                config_values_pairs.append(pair)
        configuration_values = dict(config_values_pairs)
        _t2281 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config, configuration_values=configuration_values)
        return _t2281

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2282 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2282
        _t2283 = self._extract_value_string(config.get("compression"), "")
        compression = _t2283
        _t2284 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2284
        _t2285 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2285
        _t2286 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2286
        _t2287 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2287
        _t2288 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2288
        _t2289 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2289

    def construct_export_csv_config_with_location(self, location: tuple[str, str], csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2290 = transactions_pb2.ExportCSVConfig(path=location[0], transaction_output_name=location[1], csv_source=csv_source, csv_config=csv_config)
        return _t2290

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2291 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2291

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[logic_pb2.GNFColumn], from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2292 = logic_pb2.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2292

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2293 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2293
        _t2294 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2294
        _t2295 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2295
        table_props = dict(table_property_pairs)
        _t2296 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2296

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start718 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1425 = self.parse_configure()
            _t1424 = _t1425
        else:
            _t1424 = None
        configure712 = _t1424
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1427 = self.parse_sync()
            _t1426 = _t1427
        else:
            _t1426 = None
        sync713 = _t1426
        xs714 = []
        cond715 = self.match_lookahead_literal("(", 0)
        while cond715:
            _t1428 = self.parse_epoch()
            item716 = _t1428
            xs714.append(item716)
            cond715 = self.match_lookahead_literal("(", 0)
        epochs717 = xs714
        self.consume_literal(")")
        _t1429 = self.default_configure()
        _t1430 = transactions_pb2.Transaction(epochs=epochs717, configure=(configure712 if configure712 is not None else _t1429), sync=sync713)
        result719 = _t1430
        self.record_span(span_start718, "Transaction")
        return result719

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start721 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1431 = self.parse_config_dict()
        config_dict720 = _t1431
        self.consume_literal(")")
        _t1432 = self.construct_configure(config_dict720)
        result722 = _t1432
        self.record_span(span_start721, "Configure")
        return result722

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs723 = []
        cond724 = self.match_lookahead_literal(":", 0)
        while cond724:
            _t1433 = self.parse_config_key_value()
            item725 = _t1433
            xs723.append(item725)
            cond724 = self.match_lookahead_literal(":", 0)
        config_key_values726 = xs723
        self.consume_literal("}")
        return config_key_values726

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol727 = self.consume_terminal("SYMBOL")
        _t1434 = self.parse_raw_value()
        raw_value728 = _t1434
        return (symbol727, raw_value728,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start742 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1435 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1436 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1437 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1439 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1440 = 0
                            else:
                                _t1440 = -1
                            _t1439 = _t1440
                        _t1438 = _t1439
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1441 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1442 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1443 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1444 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1445 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1446 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1447 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1448 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1449 = 10
                                                        else:
                                                            _t1449 = -1
                                                        _t1448 = _t1449
                                                    _t1447 = _t1448
                                                _t1446 = _t1447
                                            _t1445 = _t1446
                                        _t1444 = _t1445
                                    _t1443 = _t1444
                                _t1442 = _t1443
                            _t1441 = _t1442
                        _t1438 = _t1441
                    _t1437 = _t1438
                _t1436 = _t1437
            _t1435 = _t1436
        prediction729 = _t1435
        if prediction729 == 12:
            _t1451 = self.parse_boolean_value()
            boolean_value741 = _t1451
            _t1452 = logic_pb2.Value(boolean_value=boolean_value741)
            _t1450 = _t1452
        else:
            if prediction729 == 11:
                self.consume_literal("missing")
                _t1454 = logic_pb2.MissingValue()
                _t1455 = logic_pb2.Value(missing_value=_t1454)
                _t1453 = _t1455
            else:
                if prediction729 == 10:
                    decimal740 = self.consume_terminal("DECIMAL")
                    _t1457 = logic_pb2.Value(decimal_value=decimal740)
                    _t1456 = _t1457
                else:
                    if prediction729 == 9:
                        int128739 = self.consume_terminal("INT128")
                        _t1459 = logic_pb2.Value(int128_value=int128739)
                        _t1458 = _t1459
                    else:
                        if prediction729 == 8:
                            uint128738 = self.consume_terminal("UINT128")
                            _t1461 = logic_pb2.Value(uint128_value=uint128738)
                            _t1460 = _t1461
                        else:
                            if prediction729 == 7:
                                uint32737 = self.consume_terminal("UINT32")
                                _t1463 = logic_pb2.Value(uint32_value=uint32737)
                                _t1462 = _t1463
                            else:
                                if prediction729 == 6:
                                    float736 = self.consume_terminal("FLOAT")
                                    _t1465 = logic_pb2.Value(float_value=float736)
                                    _t1464 = _t1465
                                else:
                                    if prediction729 == 5:
                                        float32735 = self.consume_terminal("FLOAT32")
                                        _t1467 = logic_pb2.Value(float32_value=float32735)
                                        _t1466 = _t1467
                                    else:
                                        if prediction729 == 4:
                                            int734 = self.consume_terminal("INT")
                                            _t1469 = logic_pb2.Value(int_value=int734)
                                            _t1468 = _t1469
                                        else:
                                            if prediction729 == 3:
                                                int32733 = self.consume_terminal("INT32")
                                                _t1471 = logic_pb2.Value(int32_value=int32733)
                                                _t1470 = _t1471
                                            else:
                                                if prediction729 == 2:
                                                    string732 = self.consume_terminal("STRING")
                                                    _t1473 = logic_pb2.Value(string_value=string732)
                                                    _t1472 = _t1473
                                                else:
                                                    if prediction729 == 1:
                                                        _t1475 = self.parse_raw_datetime()
                                                        raw_datetime731 = _t1475
                                                        _t1476 = logic_pb2.Value(datetime_value=raw_datetime731)
                                                        _t1474 = _t1476
                                                    else:
                                                        if prediction729 == 0:
                                                            _t1478 = self.parse_raw_date()
                                                            raw_date730 = _t1478
                                                            _t1479 = logic_pb2.Value(date_value=raw_date730)
                                                            _t1477 = _t1479
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1474 = _t1477
                                                    _t1472 = _t1474
                                                _t1470 = _t1472
                                            _t1468 = _t1470
                                        _t1466 = _t1468
                                    _t1464 = _t1466
                                _t1462 = _t1464
                            _t1460 = _t1462
                        _t1458 = _t1460
                    _t1456 = _t1458
                _t1453 = _t1456
            _t1450 = _t1453
        result743 = _t1450
        self.record_span(span_start742, "Value")
        return result743

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start747 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int744 = self.consume_terminal("INT")
        int_3745 = self.consume_terminal("INT")
        int_4746 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1480 = logic_pb2.DateValue(year=int(int744), month=int(int_3745), day=int(int_4746))
        result748 = _t1480
        self.record_span(span_start747, "DateValue")
        return result748

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start756 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int749 = self.consume_terminal("INT")
        int_3750 = self.consume_terminal("INT")
        int_4751 = self.consume_terminal("INT")
        int_5752 = self.consume_terminal("INT")
        int_6753 = self.consume_terminal("INT")
        int_7754 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1481 = self.consume_terminal("INT")
        else:
            _t1481 = None
        int_8755 = _t1481
        self.consume_literal(")")
        _t1482 = logic_pb2.DateTimeValue(year=int(int749), month=int(int_3750), day=int(int_4751), hour=int(int_5752), minute=int(int_6753), second=int(int_7754), microsecond=int((int_8755 if int_8755 is not None else 0)))
        result757 = _t1482
        self.record_span(span_start756, "DateTimeValue")
        return result757

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1483 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1484 = 1
            else:
                _t1484 = -1
            _t1483 = _t1484
        prediction758 = _t1483
        if prediction758 == 1:
            self.consume_literal("false")
            _t1485 = False
        else:
            if prediction758 == 0:
                self.consume_literal("true")
                _t1486 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1485 = _t1486
        return _t1485

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start763 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs759 = []
        cond760 = self.match_lookahead_literal(":", 0)
        while cond760:
            _t1487 = self.parse_fragment_id()
            item761 = _t1487
            xs759.append(item761)
            cond760 = self.match_lookahead_literal(":", 0)
        fragment_ids762 = xs759
        self.consume_literal(")")
        _t1488 = transactions_pb2.Sync(fragments=fragment_ids762)
        result764 = _t1488
        self.record_span(span_start763, "Sync")
        return result764

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start766 = self.span_start()
        self.consume_literal(":")
        symbol765 = self.consume_terminal("SYMBOL")
        result767 = fragments_pb2.FragmentId(id=symbol765.encode())
        self.record_span(span_start766, "FragmentId")
        return result767

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start770 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1490 = self.parse_epoch_writes()
            _t1489 = _t1490
        else:
            _t1489 = None
        epoch_writes768 = _t1489
        if self.match_lookahead_literal("(", 0):
            _t1492 = self.parse_epoch_reads()
            _t1491 = _t1492
        else:
            _t1491 = None
        epoch_reads769 = _t1491
        self.consume_literal(")")
        _t1493 = transactions_pb2.Epoch(writes=(epoch_writes768 if epoch_writes768 is not None else []), reads=(epoch_reads769 if epoch_reads769 is not None else []))
        result771 = _t1493
        self.record_span(span_start770, "Epoch")
        return result771

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs772 = []
        cond773 = self.match_lookahead_literal("(", 0)
        while cond773:
            _t1494 = self.parse_write()
            item774 = _t1494
            xs772.append(item774)
            cond773 = self.match_lookahead_literal("(", 0)
        writes775 = xs772
        self.consume_literal(")")
        return writes775

    def parse_write(self) -> transactions_pb2.Write:
        span_start781 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1496 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1497 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1498 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1499 = 2
                        else:
                            _t1499 = -1
                        _t1498 = _t1499
                    _t1497 = _t1498
                _t1496 = _t1497
            _t1495 = _t1496
        else:
            _t1495 = -1
        prediction776 = _t1495
        if prediction776 == 3:
            _t1501 = self.parse_snapshot()
            snapshot780 = _t1501
            _t1502 = transactions_pb2.Write(snapshot=snapshot780)
            _t1500 = _t1502
        else:
            if prediction776 == 2:
                _t1504 = self.parse_context()
                context779 = _t1504
                _t1505 = transactions_pb2.Write(context=context779)
                _t1503 = _t1505
            else:
                if prediction776 == 1:
                    _t1507 = self.parse_undefine()
                    undefine778 = _t1507
                    _t1508 = transactions_pb2.Write(undefine=undefine778)
                    _t1506 = _t1508
                else:
                    if prediction776 == 0:
                        _t1510 = self.parse_define()
                        define777 = _t1510
                        _t1511 = transactions_pb2.Write(define=define777)
                        _t1509 = _t1511
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1506 = _t1509
                _t1503 = _t1506
            _t1500 = _t1503
        result782 = _t1500
        self.record_span(span_start781, "Write")
        return result782

    def parse_define(self) -> transactions_pb2.Define:
        span_start784 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1512 = self.parse_fragment()
        fragment783 = _t1512
        self.consume_literal(")")
        _t1513 = transactions_pb2.Define(fragment=fragment783)
        result785 = _t1513
        self.record_span(span_start784, "Define")
        return result785

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start791 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1514 = self.parse_new_fragment_id()
        new_fragment_id786 = _t1514
        xs787 = []
        cond788 = self.match_lookahead_literal("(", 0)
        while cond788:
            _t1515 = self.parse_declaration()
            item789 = _t1515
            xs787.append(item789)
            cond788 = self.match_lookahead_literal("(", 0)
        declarations790 = xs787
        self.consume_literal(")")
        result792 = self.construct_fragment(new_fragment_id786, declarations790)
        self.record_span(span_start791, "Fragment")
        return result792

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start794 = self.span_start()
        _t1516 = self.parse_fragment_id()
        fragment_id793 = _t1516
        self.start_fragment(fragment_id793)
        result795 = fragment_id793
        self.record_span(span_start794, "FragmentId")
        return result795

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start801 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1518 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1519 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1520 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1521 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1522 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1523 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1524 = 1
                                    else:
                                        _t1524 = -1
                                    _t1523 = _t1524
                                _t1522 = _t1523
                            _t1521 = _t1522
                        _t1520 = _t1521
                    _t1519 = _t1520
                _t1518 = _t1519
            _t1517 = _t1518
        else:
            _t1517 = -1
        prediction796 = _t1517
        if prediction796 == 3:
            _t1526 = self.parse_data()
            data800 = _t1526
            _t1527 = logic_pb2.Declaration(data=data800)
            _t1525 = _t1527
        else:
            if prediction796 == 2:
                _t1529 = self.parse_constraint()
                constraint799 = _t1529
                _t1530 = logic_pb2.Declaration(constraint=constraint799)
                _t1528 = _t1530
            else:
                if prediction796 == 1:
                    _t1532 = self.parse_algorithm()
                    algorithm798 = _t1532
                    _t1533 = logic_pb2.Declaration(algorithm=algorithm798)
                    _t1531 = _t1533
                else:
                    if prediction796 == 0:
                        _t1535 = self.parse_def()
                        def797 = _t1535
                        _t1536 = logic_pb2.Declaration()
                        getattr(_t1536, 'def').CopyFrom(def797)
                        _t1534 = _t1536
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1531 = _t1534
                _t1528 = _t1531
            _t1525 = _t1528
        result802 = _t1525
        self.record_span(span_start801, "Declaration")
        return result802

    def parse_def(self) -> logic_pb2.Def:
        span_start806 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1537 = self.parse_relation_id()
        relation_id803 = _t1537
        _t1538 = self.parse_abstraction()
        abstraction804 = _t1538
        if self.match_lookahead_literal("(", 0):
            _t1540 = self.parse_attrs()
            _t1539 = _t1540
        else:
            _t1539 = None
        attrs805 = _t1539
        self.consume_literal(")")
        _t1541 = logic_pb2.Def(name=relation_id803, body=abstraction804, attrs=(attrs805 if attrs805 is not None else []))
        result807 = _t1541
        self.record_span(span_start806, "Def")
        return result807

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start811 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1542 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1543 = 1
            else:
                _t1543 = -1
            _t1542 = _t1543
        prediction808 = _t1542
        if prediction808 == 1:
            uint128810 = self.consume_terminal("UINT128")
            _t1544 = logic_pb2.RelationId(id_low=uint128810.low, id_high=uint128810.high)
        else:
            if prediction808 == 0:
                self.consume_literal(":")
                symbol809 = self.consume_terminal("SYMBOL")
                _t1545 = self.relation_id_from_string(symbol809)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1544 = _t1545
        result812 = _t1544
        self.record_span(span_start811, "RelationId")
        return result812

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start815 = self.span_start()
        self.consume_literal("(")
        _t1546 = self.parse_bindings()
        bindings813 = _t1546
        _t1547 = self.parse_formula()
        formula814 = _t1547
        self.consume_literal(")")
        _t1548 = logic_pb2.Abstraction(vars=(list(bindings813[0]) + list(bindings813[1] if bindings813[1] is not None else [])), value=formula814)
        result816 = _t1548
        self.record_span(span_start815, "Abstraction")
        return result816

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs817 = []
        cond818 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond818:
            _t1549 = self.parse_binding()
            item819 = _t1549
            xs817.append(item819)
            cond818 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings820 = xs817
        if self.match_lookahead_literal("|", 0):
            _t1551 = self.parse_value_bindings()
            _t1550 = _t1551
        else:
            _t1550 = None
        value_bindings821 = _t1550
        self.consume_literal("]")
        return (bindings820, (value_bindings821 if value_bindings821 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start824 = self.span_start()
        symbol822 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1552 = self.parse_type()
        type823 = _t1552
        _t1553 = logic_pb2.Var(name=symbol822)
        _t1554 = logic_pb2.Binding(var=_t1553, type=type823)
        result825 = _t1554
        self.record_span(span_start824, "Binding")
        return result825

    def parse_type(self) -> logic_pb2.Type:
        span_start841 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1555 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1556 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1557 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1558 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1559 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1560 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1561 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1562 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1563 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1564 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1565 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1566 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1567 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1568 = 9
                                                            else:
                                                                _t1568 = -1
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
        prediction826 = _t1555
        if prediction826 == 13:
            _t1570 = self.parse_uint32_type()
            uint32_type840 = _t1570
            _t1571 = logic_pb2.Type(uint32_type=uint32_type840)
            _t1569 = _t1571
        else:
            if prediction826 == 12:
                _t1573 = self.parse_float32_type()
                float32_type839 = _t1573
                _t1574 = logic_pb2.Type(float32_type=float32_type839)
                _t1572 = _t1574
            else:
                if prediction826 == 11:
                    _t1576 = self.parse_int32_type()
                    int32_type838 = _t1576
                    _t1577 = logic_pb2.Type(int32_type=int32_type838)
                    _t1575 = _t1577
                else:
                    if prediction826 == 10:
                        _t1579 = self.parse_boolean_type()
                        boolean_type837 = _t1579
                        _t1580 = logic_pb2.Type(boolean_type=boolean_type837)
                        _t1578 = _t1580
                    else:
                        if prediction826 == 9:
                            _t1582 = self.parse_decimal_type()
                            decimal_type836 = _t1582
                            _t1583 = logic_pb2.Type(decimal_type=decimal_type836)
                            _t1581 = _t1583
                        else:
                            if prediction826 == 8:
                                _t1585 = self.parse_missing_type()
                                missing_type835 = _t1585
                                _t1586 = logic_pb2.Type(missing_type=missing_type835)
                                _t1584 = _t1586
                            else:
                                if prediction826 == 7:
                                    _t1588 = self.parse_datetime_type()
                                    datetime_type834 = _t1588
                                    _t1589 = logic_pb2.Type(datetime_type=datetime_type834)
                                    _t1587 = _t1589
                                else:
                                    if prediction826 == 6:
                                        _t1591 = self.parse_date_type()
                                        date_type833 = _t1591
                                        _t1592 = logic_pb2.Type(date_type=date_type833)
                                        _t1590 = _t1592
                                    else:
                                        if prediction826 == 5:
                                            _t1594 = self.parse_int128_type()
                                            int128_type832 = _t1594
                                            _t1595 = logic_pb2.Type(int128_type=int128_type832)
                                            _t1593 = _t1595
                                        else:
                                            if prediction826 == 4:
                                                _t1597 = self.parse_uint128_type()
                                                uint128_type831 = _t1597
                                                _t1598 = logic_pb2.Type(uint128_type=uint128_type831)
                                                _t1596 = _t1598
                                            else:
                                                if prediction826 == 3:
                                                    _t1600 = self.parse_float_type()
                                                    float_type830 = _t1600
                                                    _t1601 = logic_pb2.Type(float_type=float_type830)
                                                    _t1599 = _t1601
                                                else:
                                                    if prediction826 == 2:
                                                        _t1603 = self.parse_int_type()
                                                        int_type829 = _t1603
                                                        _t1604 = logic_pb2.Type(int_type=int_type829)
                                                        _t1602 = _t1604
                                                    else:
                                                        if prediction826 == 1:
                                                            _t1606 = self.parse_string_type()
                                                            string_type828 = _t1606
                                                            _t1607 = logic_pb2.Type(string_type=string_type828)
                                                            _t1605 = _t1607
                                                        else:
                                                            if prediction826 == 0:
                                                                _t1609 = self.parse_unspecified_type()
                                                                unspecified_type827 = _t1609
                                                                _t1610 = logic_pb2.Type(unspecified_type=unspecified_type827)
                                                                _t1608 = _t1610
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1605 = _t1608
                                                        _t1602 = _t1605
                                                    _t1599 = _t1602
                                                _t1596 = _t1599
                                            _t1593 = _t1596
                                        _t1590 = _t1593
                                    _t1587 = _t1590
                                _t1584 = _t1587
                            _t1581 = _t1584
                        _t1578 = _t1581
                    _t1575 = _t1578
                _t1572 = _t1575
            _t1569 = _t1572
        result842 = _t1569
        self.record_span(span_start841, "Type")
        return result842

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start843 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1611 = logic_pb2.UnspecifiedType()
        result844 = _t1611
        self.record_span(span_start843, "UnspecifiedType")
        return result844

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start845 = self.span_start()
        self.consume_literal("STRING")
        _t1612 = logic_pb2.StringType()
        result846 = _t1612
        self.record_span(span_start845, "StringType")
        return result846

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start847 = self.span_start()
        self.consume_literal("INT")
        _t1613 = logic_pb2.IntType()
        result848 = _t1613
        self.record_span(span_start847, "IntType")
        return result848

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start849 = self.span_start()
        self.consume_literal("FLOAT")
        _t1614 = logic_pb2.FloatType()
        result850 = _t1614
        self.record_span(span_start849, "FloatType")
        return result850

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start851 = self.span_start()
        self.consume_literal("UINT128")
        _t1615 = logic_pb2.UInt128Type()
        result852 = _t1615
        self.record_span(span_start851, "UInt128Type")
        return result852

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start853 = self.span_start()
        self.consume_literal("INT128")
        _t1616 = logic_pb2.Int128Type()
        result854 = _t1616
        self.record_span(span_start853, "Int128Type")
        return result854

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start855 = self.span_start()
        self.consume_literal("DATE")
        _t1617 = logic_pb2.DateType()
        result856 = _t1617
        self.record_span(span_start855, "DateType")
        return result856

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start857 = self.span_start()
        self.consume_literal("DATETIME")
        _t1618 = logic_pb2.DateTimeType()
        result858 = _t1618
        self.record_span(span_start857, "DateTimeType")
        return result858

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start859 = self.span_start()
        self.consume_literal("MISSING")
        _t1619 = logic_pb2.MissingType()
        result860 = _t1619
        self.record_span(span_start859, "MissingType")
        return result860

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start863 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int861 = self.consume_terminal("INT")
        int_3862 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1620 = logic_pb2.DecimalType(precision=int(int861), scale=int(int_3862))
        result864 = _t1620
        self.record_span(span_start863, "DecimalType")
        return result864

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start865 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1621 = logic_pb2.BooleanType()
        result866 = _t1621
        self.record_span(span_start865, "BooleanType")
        return result866

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start867 = self.span_start()
        self.consume_literal("INT32")
        _t1622 = logic_pb2.Int32Type()
        result868 = _t1622
        self.record_span(span_start867, "Int32Type")
        return result868

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start869 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1623 = logic_pb2.Float32Type()
        result870 = _t1623
        self.record_span(span_start869, "Float32Type")
        return result870

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start871 = self.span_start()
        self.consume_literal("UINT32")
        _t1624 = logic_pb2.UInt32Type()
        result872 = _t1624
        self.record_span(span_start871, "UInt32Type")
        return result872

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs873 = []
        cond874 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond874:
            _t1625 = self.parse_binding()
            item875 = _t1625
            xs873.append(item875)
            cond874 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings876 = xs873
        return bindings876

    def parse_formula(self) -> logic_pb2.Formula:
        span_start891 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1627 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1628 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1629 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1630 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1631 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1632 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1633 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1634 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1635 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1636 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1637 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1638 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1639 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1640 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1641 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1642 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1643 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1644 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1645 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1646 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1647 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1648 = 10
                                                                                                else:
                                                                                                    _t1648 = -1
                                                                                                _t1647 = _t1648
                                                                                            _t1646 = _t1647
                                                                                        _t1645 = _t1646
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
                                _t1631 = _t1632
                            _t1630 = _t1631
                        _t1629 = _t1630
                    _t1628 = _t1629
                _t1627 = _t1628
            _t1626 = _t1627
        else:
            _t1626 = -1
        prediction877 = _t1626
        if prediction877 == 12:
            _t1650 = self.parse_cast()
            cast890 = _t1650
            _t1651 = logic_pb2.Formula(cast=cast890)
            _t1649 = _t1651
        else:
            if prediction877 == 11:
                _t1653 = self.parse_rel_atom()
                rel_atom889 = _t1653
                _t1654 = logic_pb2.Formula(rel_atom=rel_atom889)
                _t1652 = _t1654
            else:
                if prediction877 == 10:
                    _t1656 = self.parse_primitive()
                    primitive888 = _t1656
                    _t1657 = logic_pb2.Formula(primitive=primitive888)
                    _t1655 = _t1657
                else:
                    if prediction877 == 9:
                        _t1659 = self.parse_pragma()
                        pragma887 = _t1659
                        _t1660 = logic_pb2.Formula(pragma=pragma887)
                        _t1658 = _t1660
                    else:
                        if prediction877 == 8:
                            _t1662 = self.parse_atom()
                            atom886 = _t1662
                            _t1663 = logic_pb2.Formula(atom=atom886)
                            _t1661 = _t1663
                        else:
                            if prediction877 == 7:
                                _t1665 = self.parse_ffi()
                                ffi885 = _t1665
                                _t1666 = logic_pb2.Formula(ffi=ffi885)
                                _t1664 = _t1666
                            else:
                                if prediction877 == 6:
                                    _t1668 = self.parse_not()
                                    not884 = _t1668
                                    _t1669 = logic_pb2.Formula()
                                    getattr(_t1669, 'not').CopyFrom(not884)
                                    _t1667 = _t1669
                                else:
                                    if prediction877 == 5:
                                        _t1671 = self.parse_disjunction()
                                        disjunction883 = _t1671
                                        _t1672 = logic_pb2.Formula(disjunction=disjunction883)
                                        _t1670 = _t1672
                                    else:
                                        if prediction877 == 4:
                                            _t1674 = self.parse_conjunction()
                                            conjunction882 = _t1674
                                            _t1675 = logic_pb2.Formula(conjunction=conjunction882)
                                            _t1673 = _t1675
                                        else:
                                            if prediction877 == 3:
                                                _t1677 = self.parse_reduce()
                                                reduce881 = _t1677
                                                _t1678 = logic_pb2.Formula(reduce=reduce881)
                                                _t1676 = _t1678
                                            else:
                                                if prediction877 == 2:
                                                    _t1680 = self.parse_exists()
                                                    exists880 = _t1680
                                                    _t1681 = logic_pb2.Formula(exists=exists880)
                                                    _t1679 = _t1681
                                                else:
                                                    if prediction877 == 1:
                                                        _t1683 = self.parse_false()
                                                        false879 = _t1683
                                                        _t1684 = logic_pb2.Formula(disjunction=false879)
                                                        _t1682 = _t1684
                                                    else:
                                                        if prediction877 == 0:
                                                            _t1686 = self.parse_true()
                                                            true878 = _t1686
                                                            _t1687 = logic_pb2.Formula(conjunction=true878)
                                                            _t1685 = _t1687
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1682 = _t1685
                                                    _t1679 = _t1682
                                                _t1676 = _t1679
                                            _t1673 = _t1676
                                        _t1670 = _t1673
                                    _t1667 = _t1670
                                _t1664 = _t1667
                            _t1661 = _t1664
                        _t1658 = _t1661
                    _t1655 = _t1658
                _t1652 = _t1655
            _t1649 = _t1652
        result892 = _t1649
        self.record_span(span_start891, "Formula")
        return result892

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start893 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1688 = logic_pb2.Conjunction(args=[])
        result894 = _t1688
        self.record_span(span_start893, "Conjunction")
        return result894

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start895 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1689 = logic_pb2.Disjunction(args=[])
        result896 = _t1689
        self.record_span(span_start895, "Disjunction")
        return result896

    def parse_exists(self) -> logic_pb2.Exists:
        span_start899 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1690 = self.parse_bindings()
        bindings897 = _t1690
        _t1691 = self.parse_formula()
        formula898 = _t1691
        self.consume_literal(")")
        _t1692 = logic_pb2.Abstraction(vars=(list(bindings897[0]) + list(bindings897[1] if bindings897[1] is not None else [])), value=formula898)
        _t1693 = logic_pb2.Exists(body=_t1692)
        result900 = _t1693
        self.record_span(span_start899, "Exists")
        return result900

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start904 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1694 = self.parse_abstraction()
        abstraction901 = _t1694
        _t1695 = self.parse_abstraction()
        abstraction_3902 = _t1695
        _t1696 = self.parse_terms()
        terms903 = _t1696
        self.consume_literal(")")
        _t1697 = logic_pb2.Reduce(op=abstraction901, body=abstraction_3902, terms=terms903)
        result905 = _t1697
        self.record_span(span_start904, "Reduce")
        return result905

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs906 = []
        cond907 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond907:
            _t1698 = self.parse_term()
            item908 = _t1698
            xs906.append(item908)
            cond907 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms909 = xs906
        self.consume_literal(")")
        return terms909

    def parse_term(self) -> logic_pb2.Term:
        span_start913 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1699 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1700 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1701 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1702 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1703 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1704 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1705 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1706 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1707 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1708 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1709 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1710 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1711 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1712 = 1
                                                            else:
                                                                _t1712 = -1
                                                            _t1711 = _t1712
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
                _t1700 = _t1701
            _t1699 = _t1700
        prediction910 = _t1699
        if prediction910 == 1:
            _t1714 = self.parse_value()
            value912 = _t1714
            _t1715 = logic_pb2.Term(constant=value912)
            _t1713 = _t1715
        else:
            if prediction910 == 0:
                _t1717 = self.parse_var()
                var911 = _t1717
                _t1718 = logic_pb2.Term(var=var911)
                _t1716 = _t1718
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1713 = _t1716
        result914 = _t1713
        self.record_span(span_start913, "Term")
        return result914

    def parse_var(self) -> logic_pb2.Var:
        span_start916 = self.span_start()
        symbol915 = self.consume_terminal("SYMBOL")
        _t1719 = logic_pb2.Var(name=symbol915)
        result917 = _t1719
        self.record_span(span_start916, "Var")
        return result917

    def parse_value(self) -> logic_pb2.Value:
        span_start931 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1720 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1721 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1722 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1724 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1725 = 0
                            else:
                                _t1725 = -1
                            _t1724 = _t1725
                        _t1723 = _t1724
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1726 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1727 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1728 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1729 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1730 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1731 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1732 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1733 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1734 = 10
                                                        else:
                                                            _t1734 = -1
                                                        _t1733 = _t1734
                                                    _t1732 = _t1733
                                                _t1731 = _t1732
                                            _t1730 = _t1731
                                        _t1729 = _t1730
                                    _t1728 = _t1729
                                _t1727 = _t1728
                            _t1726 = _t1727
                        _t1723 = _t1726
                    _t1722 = _t1723
                _t1721 = _t1722
            _t1720 = _t1721
        prediction918 = _t1720
        if prediction918 == 12:
            _t1736 = self.parse_boolean_value()
            boolean_value930 = _t1736
            _t1737 = logic_pb2.Value(boolean_value=boolean_value930)
            _t1735 = _t1737
        else:
            if prediction918 == 11:
                self.consume_literal("missing")
                _t1739 = logic_pb2.MissingValue()
                _t1740 = logic_pb2.Value(missing_value=_t1739)
                _t1738 = _t1740
            else:
                if prediction918 == 10:
                    formatted_decimal929 = self.consume_terminal("DECIMAL")
                    _t1742 = logic_pb2.Value(decimal_value=formatted_decimal929)
                    _t1741 = _t1742
                else:
                    if prediction918 == 9:
                        formatted_int128928 = self.consume_terminal("INT128")
                        _t1744 = logic_pb2.Value(int128_value=formatted_int128928)
                        _t1743 = _t1744
                    else:
                        if prediction918 == 8:
                            formatted_uint128927 = self.consume_terminal("UINT128")
                            _t1746 = logic_pb2.Value(uint128_value=formatted_uint128927)
                            _t1745 = _t1746
                        else:
                            if prediction918 == 7:
                                formatted_uint32926 = self.consume_terminal("UINT32")
                                _t1748 = logic_pb2.Value(uint32_value=formatted_uint32926)
                                _t1747 = _t1748
                            else:
                                if prediction918 == 6:
                                    formatted_float925 = self.consume_terminal("FLOAT")
                                    _t1750 = logic_pb2.Value(float_value=formatted_float925)
                                    _t1749 = _t1750
                                else:
                                    if prediction918 == 5:
                                        formatted_float32924 = self.consume_terminal("FLOAT32")
                                        _t1752 = logic_pb2.Value(float32_value=formatted_float32924)
                                        _t1751 = _t1752
                                    else:
                                        if prediction918 == 4:
                                            formatted_int923 = self.consume_terminal("INT")
                                            _t1754 = logic_pb2.Value(int_value=formatted_int923)
                                            _t1753 = _t1754
                                        else:
                                            if prediction918 == 3:
                                                formatted_int32922 = self.consume_terminal("INT32")
                                                _t1756 = logic_pb2.Value(int32_value=formatted_int32922)
                                                _t1755 = _t1756
                                            else:
                                                if prediction918 == 2:
                                                    formatted_string921 = self.consume_terminal("STRING")
                                                    _t1758 = logic_pb2.Value(string_value=formatted_string921)
                                                    _t1757 = _t1758
                                                else:
                                                    if prediction918 == 1:
                                                        _t1760 = self.parse_datetime()
                                                        datetime920 = _t1760
                                                        _t1761 = logic_pb2.Value(datetime_value=datetime920)
                                                        _t1759 = _t1761
                                                    else:
                                                        if prediction918 == 0:
                                                            _t1763 = self.parse_date()
                                                            date919 = _t1763
                                                            _t1764 = logic_pb2.Value(date_value=date919)
                                                            _t1762 = _t1764
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1759 = _t1762
                                                    _t1757 = _t1759
                                                _t1755 = _t1757
                                            _t1753 = _t1755
                                        _t1751 = _t1753
                                    _t1749 = _t1751
                                _t1747 = _t1749
                            _t1745 = _t1747
                        _t1743 = _t1745
                    _t1741 = _t1743
                _t1738 = _t1741
            _t1735 = _t1738
        result932 = _t1735
        self.record_span(span_start931, "Value")
        return result932

    def parse_date(self) -> logic_pb2.DateValue:
        span_start936 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int933 = self.consume_terminal("INT")
        formatted_int_3934 = self.consume_terminal("INT")
        formatted_int_4935 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1765 = logic_pb2.DateValue(year=int(formatted_int933), month=int(formatted_int_3934), day=int(formatted_int_4935))
        result937 = _t1765
        self.record_span(span_start936, "DateValue")
        return result937

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start945 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int938 = self.consume_terminal("INT")
        formatted_int_3939 = self.consume_terminal("INT")
        formatted_int_4940 = self.consume_terminal("INT")
        formatted_int_5941 = self.consume_terminal("INT")
        formatted_int_6942 = self.consume_terminal("INT")
        formatted_int_7943 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1766 = self.consume_terminal("INT")
        else:
            _t1766 = None
        formatted_int_8944 = _t1766
        self.consume_literal(")")
        _t1767 = logic_pb2.DateTimeValue(year=int(formatted_int938), month=int(formatted_int_3939), day=int(formatted_int_4940), hour=int(formatted_int_5941), minute=int(formatted_int_6942), second=int(formatted_int_7943), microsecond=int((formatted_int_8944 if formatted_int_8944 is not None else 0)))
        result946 = _t1767
        self.record_span(span_start945, "DateTimeValue")
        return result946

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start951 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs947 = []
        cond948 = self.match_lookahead_literal("(", 0)
        while cond948:
            _t1768 = self.parse_formula()
            item949 = _t1768
            xs947.append(item949)
            cond948 = self.match_lookahead_literal("(", 0)
        formulas950 = xs947
        self.consume_literal(")")
        _t1769 = logic_pb2.Conjunction(args=formulas950)
        result952 = _t1769
        self.record_span(span_start951, "Conjunction")
        return result952

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start957 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs953 = []
        cond954 = self.match_lookahead_literal("(", 0)
        while cond954:
            _t1770 = self.parse_formula()
            item955 = _t1770
            xs953.append(item955)
            cond954 = self.match_lookahead_literal("(", 0)
        formulas956 = xs953
        self.consume_literal(")")
        _t1771 = logic_pb2.Disjunction(args=formulas956)
        result958 = _t1771
        self.record_span(span_start957, "Disjunction")
        return result958

    def parse_not(self) -> logic_pb2.Not:
        span_start960 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1772 = self.parse_formula()
        formula959 = _t1772
        self.consume_literal(")")
        _t1773 = logic_pb2.Not(arg=formula959)
        result961 = _t1773
        self.record_span(span_start960, "Not")
        return result961

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start965 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1774 = self.parse_name()
        name962 = _t1774
        _t1775 = self.parse_ffi_args()
        ffi_args963 = _t1775
        _t1776 = self.parse_terms()
        terms964 = _t1776
        self.consume_literal(")")
        _t1777 = logic_pb2.FFI(name=name962, args=ffi_args963, terms=terms964)
        result966 = _t1777
        self.record_span(span_start965, "FFI")
        return result966

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol967 = self.consume_terminal("SYMBOL")
        return symbol967

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs968 = []
        cond969 = self.match_lookahead_literal("(", 0)
        while cond969:
            _t1778 = self.parse_abstraction()
            item970 = _t1778
            xs968.append(item970)
            cond969 = self.match_lookahead_literal("(", 0)
        abstractions971 = xs968
        self.consume_literal(")")
        return abstractions971

    def parse_atom(self) -> logic_pb2.Atom:
        span_start977 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1779 = self.parse_relation_id()
        relation_id972 = _t1779
        xs973 = []
        cond974 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond974:
            _t1780 = self.parse_term()
            item975 = _t1780
            xs973.append(item975)
            cond974 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms976 = xs973
        self.consume_literal(")")
        _t1781 = logic_pb2.Atom(name=relation_id972, terms=terms976)
        result978 = _t1781
        self.record_span(span_start977, "Atom")
        return result978

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start984 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1782 = self.parse_name()
        name979 = _t1782
        xs980 = []
        cond981 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond981:
            _t1783 = self.parse_term()
            item982 = _t1783
            xs980.append(item982)
            cond981 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms983 = xs980
        self.consume_literal(")")
        _t1784 = logic_pb2.Pragma(name=name979, terms=terms983)
        result985 = _t1784
        self.record_span(span_start984, "Pragma")
        return result985

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start1001 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1786 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1787 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1788 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1789 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1790 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1791 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1792 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1793 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1794 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1795 = 7
                                                else:
                                                    _t1795 = -1
                                                _t1794 = _t1795
                                            _t1793 = _t1794
                                        _t1792 = _t1793
                                    _t1791 = _t1792
                                _t1790 = _t1791
                            _t1789 = _t1790
                        _t1788 = _t1789
                    _t1787 = _t1788
                _t1786 = _t1787
            _t1785 = _t1786
        else:
            _t1785 = -1
        prediction986 = _t1785
        if prediction986 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1797 = self.parse_name()
            name996 = _t1797
            xs997 = []
            cond998 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond998:
                _t1798 = self.parse_rel_term()
                item999 = _t1798
                xs997.append(item999)
                cond998 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms1000 = xs997
            self.consume_literal(")")
            _t1799 = logic_pb2.Primitive(name=name996, terms=rel_terms1000)
            _t1796 = _t1799
        else:
            if prediction986 == 8:
                _t1801 = self.parse_divide()
                divide995 = _t1801
                _t1800 = divide995
            else:
                if prediction986 == 7:
                    _t1803 = self.parse_multiply()
                    multiply994 = _t1803
                    _t1802 = multiply994
                else:
                    if prediction986 == 6:
                        _t1805 = self.parse_minus()
                        minus993 = _t1805
                        _t1804 = minus993
                    else:
                        if prediction986 == 5:
                            _t1807 = self.parse_add()
                            add992 = _t1807
                            _t1806 = add992
                        else:
                            if prediction986 == 4:
                                _t1809 = self.parse_gt_eq()
                                gt_eq991 = _t1809
                                _t1808 = gt_eq991
                            else:
                                if prediction986 == 3:
                                    _t1811 = self.parse_gt()
                                    gt990 = _t1811
                                    _t1810 = gt990
                                else:
                                    if prediction986 == 2:
                                        _t1813 = self.parse_lt_eq()
                                        lt_eq989 = _t1813
                                        _t1812 = lt_eq989
                                    else:
                                        if prediction986 == 1:
                                            _t1815 = self.parse_lt()
                                            lt988 = _t1815
                                            _t1814 = lt988
                                        else:
                                            if prediction986 == 0:
                                                _t1817 = self.parse_eq()
                                                eq987 = _t1817
                                                _t1816 = eq987
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1814 = _t1816
                                        _t1812 = _t1814
                                    _t1810 = _t1812
                                _t1808 = _t1810
                            _t1806 = _t1808
                        _t1804 = _t1806
                    _t1802 = _t1804
                _t1800 = _t1802
            _t1796 = _t1800
        result1002 = _t1796
        self.record_span(span_start1001, "Primitive")
        return result1002

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start1005 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1818 = self.parse_term()
        term1003 = _t1818
        _t1819 = self.parse_term()
        term_31004 = _t1819
        self.consume_literal(")")
        _t1820 = logic_pb2.RelTerm(term=term1003)
        _t1821 = logic_pb2.RelTerm(term=term_31004)
        _t1822 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1820, _t1821])
        result1006 = _t1822
        self.record_span(span_start1005, "Primitive")
        return result1006

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start1009 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1823 = self.parse_term()
        term1007 = _t1823
        _t1824 = self.parse_term()
        term_31008 = _t1824
        self.consume_literal(")")
        _t1825 = logic_pb2.RelTerm(term=term1007)
        _t1826 = logic_pb2.RelTerm(term=term_31008)
        _t1827 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1825, _t1826])
        result1010 = _t1827
        self.record_span(span_start1009, "Primitive")
        return result1010

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start1013 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1828 = self.parse_term()
        term1011 = _t1828
        _t1829 = self.parse_term()
        term_31012 = _t1829
        self.consume_literal(")")
        _t1830 = logic_pb2.RelTerm(term=term1011)
        _t1831 = logic_pb2.RelTerm(term=term_31012)
        _t1832 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1830, _t1831])
        result1014 = _t1832
        self.record_span(span_start1013, "Primitive")
        return result1014

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start1017 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1833 = self.parse_term()
        term1015 = _t1833
        _t1834 = self.parse_term()
        term_31016 = _t1834
        self.consume_literal(")")
        _t1835 = logic_pb2.RelTerm(term=term1015)
        _t1836 = logic_pb2.RelTerm(term=term_31016)
        _t1837 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1835, _t1836])
        result1018 = _t1837
        self.record_span(span_start1017, "Primitive")
        return result1018

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start1021 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1838 = self.parse_term()
        term1019 = _t1838
        _t1839 = self.parse_term()
        term_31020 = _t1839
        self.consume_literal(")")
        _t1840 = logic_pb2.RelTerm(term=term1019)
        _t1841 = logic_pb2.RelTerm(term=term_31020)
        _t1842 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1840, _t1841])
        result1022 = _t1842
        self.record_span(span_start1021, "Primitive")
        return result1022

    def parse_add(self) -> logic_pb2.Primitive:
        span_start1026 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1843 = self.parse_term()
        term1023 = _t1843
        _t1844 = self.parse_term()
        term_31024 = _t1844
        _t1845 = self.parse_term()
        term_41025 = _t1845
        self.consume_literal(")")
        _t1846 = logic_pb2.RelTerm(term=term1023)
        _t1847 = logic_pb2.RelTerm(term=term_31024)
        _t1848 = logic_pb2.RelTerm(term=term_41025)
        _t1849 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1846, _t1847, _t1848])
        result1027 = _t1849
        self.record_span(span_start1026, "Primitive")
        return result1027

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start1031 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1850 = self.parse_term()
        term1028 = _t1850
        _t1851 = self.parse_term()
        term_31029 = _t1851
        _t1852 = self.parse_term()
        term_41030 = _t1852
        self.consume_literal(")")
        _t1853 = logic_pb2.RelTerm(term=term1028)
        _t1854 = logic_pb2.RelTerm(term=term_31029)
        _t1855 = logic_pb2.RelTerm(term=term_41030)
        _t1856 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1853, _t1854, _t1855])
        result1032 = _t1856
        self.record_span(span_start1031, "Primitive")
        return result1032

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start1036 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1857 = self.parse_term()
        term1033 = _t1857
        _t1858 = self.parse_term()
        term_31034 = _t1858
        _t1859 = self.parse_term()
        term_41035 = _t1859
        self.consume_literal(")")
        _t1860 = logic_pb2.RelTerm(term=term1033)
        _t1861 = logic_pb2.RelTerm(term=term_31034)
        _t1862 = logic_pb2.RelTerm(term=term_41035)
        _t1863 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1860, _t1861, _t1862])
        result1037 = _t1863
        self.record_span(span_start1036, "Primitive")
        return result1037

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start1041 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1864 = self.parse_term()
        term1038 = _t1864
        _t1865 = self.parse_term()
        term_31039 = _t1865
        _t1866 = self.parse_term()
        term_41040 = _t1866
        self.consume_literal(")")
        _t1867 = logic_pb2.RelTerm(term=term1038)
        _t1868 = logic_pb2.RelTerm(term=term_31039)
        _t1869 = logic_pb2.RelTerm(term=term_41040)
        _t1870 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1867, _t1868, _t1869])
        result1042 = _t1870
        self.record_span(span_start1041, "Primitive")
        return result1042

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1046 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1871 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1872 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1873 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1874 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1875 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1876 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1877 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1878 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1879 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1880 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1881 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1882 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1883 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1884 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1885 = 1
                                                                else:
                                                                    _t1885 = -1
                                                                _t1884 = _t1885
                                                            _t1883 = _t1884
                                                        _t1882 = _t1883
                                                    _t1881 = _t1882
                                                _t1880 = _t1881
                                            _t1879 = _t1880
                                        _t1878 = _t1879
                                    _t1877 = _t1878
                                _t1876 = _t1877
                            _t1875 = _t1876
                        _t1874 = _t1875
                    _t1873 = _t1874
                _t1872 = _t1873
            _t1871 = _t1872
        prediction1043 = _t1871
        if prediction1043 == 1:
            _t1887 = self.parse_term()
            term1045 = _t1887
            _t1888 = logic_pb2.RelTerm(term=term1045)
            _t1886 = _t1888
        else:
            if prediction1043 == 0:
                _t1890 = self.parse_specialized_value()
                specialized_value1044 = _t1890
                _t1891 = logic_pb2.RelTerm(specialized_value=specialized_value1044)
                _t1889 = _t1891
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1886 = _t1889
        result1047 = _t1886
        self.record_span(span_start1046, "RelTerm")
        return result1047

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1049 = self.span_start()
        self.consume_literal("#")
        _t1892 = self.parse_raw_value()
        raw_value1048 = _t1892
        result1050 = raw_value1048
        self.record_span(span_start1049, "Value")
        return result1050

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1056 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1893 = self.parse_name()
        name1051 = _t1893
        xs1052 = []
        cond1053 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1053:
            _t1894 = self.parse_rel_term()
            item1054 = _t1894
            xs1052.append(item1054)
            cond1053 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1055 = xs1052
        self.consume_literal(")")
        _t1895 = logic_pb2.RelAtom(name=name1051, terms=rel_terms1055)
        result1057 = _t1895
        self.record_span(span_start1056, "RelAtom")
        return result1057

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1060 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1896 = self.parse_term()
        term1058 = _t1896
        _t1897 = self.parse_term()
        term_31059 = _t1897
        self.consume_literal(")")
        _t1898 = logic_pb2.Cast(input=term1058, result=term_31059)
        result1061 = _t1898
        self.record_span(span_start1060, "Cast")
        return result1061

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1062 = []
        cond1063 = self.match_lookahead_literal("(", 0)
        while cond1063:
            _t1899 = self.parse_attribute()
            item1064 = _t1899
            xs1062.append(item1064)
            cond1063 = self.match_lookahead_literal("(", 0)
        attributes1065 = xs1062
        self.consume_literal(")")
        return attributes1065

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1071 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1900 = self.parse_name()
        name1066 = _t1900
        xs1067 = []
        cond1068 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1068:
            _t1901 = self.parse_raw_value()
            item1069 = _t1901
            xs1067.append(item1069)
            cond1068 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1070 = xs1067
        self.consume_literal(")")
        _t1902 = logic_pb2.Attribute(name=name1066, args=raw_values1070)
        result1072 = _t1902
        self.record_span(span_start1071, "Attribute")
        return result1072

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1079 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1073 = []
        cond1074 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1074:
            _t1903 = self.parse_relation_id()
            item1075 = _t1903
            xs1073.append(item1075)
            cond1074 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1076 = xs1073
        _t1904 = self.parse_script()
        script1077 = _t1904
        if self.match_lookahead_literal("(", 0):
            _t1906 = self.parse_attrs()
            _t1905 = _t1906
        else:
            _t1905 = None
        attrs1078 = _t1905
        self.consume_literal(")")
        _t1907 = logic_pb2.Algorithm(body=script1077, attrs=(attrs1078 if attrs1078 is not None else []))
        getattr(_t1907, 'global').extend(relation_ids1076)
        result1080 = _t1907
        self.record_span(span_start1079, "Algorithm")
        return result1080

    def parse_script(self) -> logic_pb2.Script:
        span_start1085 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1081 = []
        cond1082 = self.match_lookahead_literal("(", 0)
        while cond1082:
            _t1908 = self.parse_construct()
            item1083 = _t1908
            xs1081.append(item1083)
            cond1082 = self.match_lookahead_literal("(", 0)
        constructs1084 = xs1081
        self.consume_literal(")")
        _t1909 = logic_pb2.Script(constructs=constructs1084)
        result1086 = _t1909
        self.record_span(span_start1085, "Script")
        return result1086

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1090 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1911 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1912 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1913 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1914 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1915 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1916 = 1
                                else:
                                    _t1916 = -1
                                _t1915 = _t1916
                            _t1914 = _t1915
                        _t1913 = _t1914
                    _t1912 = _t1913
                _t1911 = _t1912
            _t1910 = _t1911
        else:
            _t1910 = -1
        prediction1087 = _t1910
        if prediction1087 == 1:
            _t1918 = self.parse_instruction()
            instruction1089 = _t1918
            _t1919 = logic_pb2.Construct(instruction=instruction1089)
            _t1917 = _t1919
        else:
            if prediction1087 == 0:
                _t1921 = self.parse_loop()
                loop1088 = _t1921
                _t1922 = logic_pb2.Construct(loop=loop1088)
                _t1920 = _t1922
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1917 = _t1920
        result1091 = _t1917
        self.record_span(span_start1090, "Construct")
        return result1091

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1095 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1923 = self.parse_init()
        init1092 = _t1923
        _t1924 = self.parse_script()
        script1093 = _t1924
        if self.match_lookahead_literal("(", 0):
            _t1926 = self.parse_attrs()
            _t1925 = _t1926
        else:
            _t1925 = None
        attrs1094 = _t1925
        self.consume_literal(")")
        _t1927 = logic_pb2.Loop(init=init1092, body=script1093, attrs=(attrs1094 if attrs1094 is not None else []))
        result1096 = _t1927
        self.record_span(span_start1095, "Loop")
        return result1096

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1097 = []
        cond1098 = self.match_lookahead_literal("(", 0)
        while cond1098:
            _t1928 = self.parse_instruction()
            item1099 = _t1928
            xs1097.append(item1099)
            cond1098 = self.match_lookahead_literal("(", 0)
        instructions1100 = xs1097
        self.consume_literal(")")
        return instructions1100

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1107 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1930 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1931 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1932 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1933 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1934 = 0
                            else:
                                _t1934 = -1
                            _t1933 = _t1934
                        _t1932 = _t1933
                    _t1931 = _t1932
                _t1930 = _t1931
            _t1929 = _t1930
        else:
            _t1929 = -1
        prediction1101 = _t1929
        if prediction1101 == 4:
            _t1936 = self.parse_monus_def()
            monus_def1106 = _t1936
            _t1937 = logic_pb2.Instruction(monus_def=monus_def1106)
            _t1935 = _t1937
        else:
            if prediction1101 == 3:
                _t1939 = self.parse_monoid_def()
                monoid_def1105 = _t1939
                _t1940 = logic_pb2.Instruction(monoid_def=monoid_def1105)
                _t1938 = _t1940
            else:
                if prediction1101 == 2:
                    _t1942 = self.parse_break()
                    break1104 = _t1942
                    _t1943 = logic_pb2.Instruction()
                    getattr(_t1943, 'break').CopyFrom(break1104)
                    _t1941 = _t1943
                else:
                    if prediction1101 == 1:
                        _t1945 = self.parse_upsert()
                        upsert1103 = _t1945
                        _t1946 = logic_pb2.Instruction(upsert=upsert1103)
                        _t1944 = _t1946
                    else:
                        if prediction1101 == 0:
                            _t1948 = self.parse_assign()
                            assign1102 = _t1948
                            _t1949 = logic_pb2.Instruction(assign=assign1102)
                            _t1947 = _t1949
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1944 = _t1947
                    _t1941 = _t1944
                _t1938 = _t1941
            _t1935 = _t1938
        result1108 = _t1935
        self.record_span(span_start1107, "Instruction")
        return result1108

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1112 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1950 = self.parse_relation_id()
        relation_id1109 = _t1950
        _t1951 = self.parse_abstraction()
        abstraction1110 = _t1951
        if self.match_lookahead_literal("(", 0):
            _t1953 = self.parse_attrs()
            _t1952 = _t1953
        else:
            _t1952 = None
        attrs1111 = _t1952
        self.consume_literal(")")
        _t1954 = logic_pb2.Assign(name=relation_id1109, body=abstraction1110, attrs=(attrs1111 if attrs1111 is not None else []))
        result1113 = _t1954
        self.record_span(span_start1112, "Assign")
        return result1113

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1117 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1955 = self.parse_relation_id()
        relation_id1114 = _t1955
        _t1956 = self.parse_abstraction_with_arity()
        abstraction_with_arity1115 = _t1956
        if self.match_lookahead_literal("(", 0):
            _t1958 = self.parse_attrs()
            _t1957 = _t1958
        else:
            _t1957 = None
        attrs1116 = _t1957
        self.consume_literal(")")
        _t1959 = logic_pb2.Upsert(name=relation_id1114, body=abstraction_with_arity1115[0], attrs=(attrs1116 if attrs1116 is not None else []), value_arity=abstraction_with_arity1115[1])
        result1118 = _t1959
        self.record_span(span_start1117, "Upsert")
        return result1118

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1960 = self.parse_bindings()
        bindings1119 = _t1960
        _t1961 = self.parse_formula()
        formula1120 = _t1961
        self.consume_literal(")")
        _t1962 = logic_pb2.Abstraction(vars=(list(bindings1119[0]) + list(bindings1119[1] if bindings1119[1] is not None else [])), value=formula1120)
        return (_t1962, len(bindings1119[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1124 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1963 = self.parse_relation_id()
        relation_id1121 = _t1963
        _t1964 = self.parse_abstraction()
        abstraction1122 = _t1964
        if self.match_lookahead_literal("(", 0):
            _t1966 = self.parse_attrs()
            _t1965 = _t1966
        else:
            _t1965 = None
        attrs1123 = _t1965
        self.consume_literal(")")
        _t1967 = logic_pb2.Break(name=relation_id1121, body=abstraction1122, attrs=(attrs1123 if attrs1123 is not None else []))
        result1125 = _t1967
        self.record_span(span_start1124, "Break")
        return result1125

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1130 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1968 = self.parse_monoid()
        monoid1126 = _t1968
        _t1969 = self.parse_relation_id()
        relation_id1127 = _t1969
        _t1970 = self.parse_abstraction_with_arity()
        abstraction_with_arity1128 = _t1970
        if self.match_lookahead_literal("(", 0):
            _t1972 = self.parse_attrs()
            _t1971 = _t1972
        else:
            _t1971 = None
        attrs1129 = _t1971
        self.consume_literal(")")
        _t1973 = logic_pb2.MonoidDef(monoid=monoid1126, name=relation_id1127, body=abstraction_with_arity1128[0], attrs=(attrs1129 if attrs1129 is not None else []), value_arity=abstraction_with_arity1128[1])
        result1131 = _t1973
        self.record_span(span_start1130, "MonoidDef")
        return result1131

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1137 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1975 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1976 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1977 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1978 = 2
                        else:
                            _t1978 = -1
                        _t1977 = _t1978
                    _t1976 = _t1977
                _t1975 = _t1976
            _t1974 = _t1975
        else:
            _t1974 = -1
        prediction1132 = _t1974
        if prediction1132 == 3:
            _t1980 = self.parse_sum_monoid()
            sum_monoid1136 = _t1980
            _t1981 = logic_pb2.Monoid(sum_monoid=sum_monoid1136)
            _t1979 = _t1981
        else:
            if prediction1132 == 2:
                _t1983 = self.parse_max_monoid()
                max_monoid1135 = _t1983
                _t1984 = logic_pb2.Monoid(max_monoid=max_monoid1135)
                _t1982 = _t1984
            else:
                if prediction1132 == 1:
                    _t1986 = self.parse_min_monoid()
                    min_monoid1134 = _t1986
                    _t1987 = logic_pb2.Monoid(min_monoid=min_monoid1134)
                    _t1985 = _t1987
                else:
                    if prediction1132 == 0:
                        _t1989 = self.parse_or_monoid()
                        or_monoid1133 = _t1989
                        _t1990 = logic_pb2.Monoid(or_monoid=or_monoid1133)
                        _t1988 = _t1990
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1985 = _t1988
                _t1982 = _t1985
            _t1979 = _t1982
        result1138 = _t1979
        self.record_span(span_start1137, "Monoid")
        return result1138

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1139 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1991 = logic_pb2.OrMonoid()
        result1140 = _t1991
        self.record_span(span_start1139, "OrMonoid")
        return result1140

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1142 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1992 = self.parse_type()
        type1141 = _t1992
        self.consume_literal(")")
        _t1993 = logic_pb2.MinMonoid(type=type1141)
        result1143 = _t1993
        self.record_span(span_start1142, "MinMonoid")
        return result1143

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1145 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1994 = self.parse_type()
        type1144 = _t1994
        self.consume_literal(")")
        _t1995 = logic_pb2.MaxMonoid(type=type1144)
        result1146 = _t1995
        self.record_span(span_start1145, "MaxMonoid")
        return result1146

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1148 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1996 = self.parse_type()
        type1147 = _t1996
        self.consume_literal(")")
        _t1997 = logic_pb2.SumMonoid(type=type1147)
        result1149 = _t1997
        self.record_span(span_start1148, "SumMonoid")
        return result1149

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1154 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1998 = self.parse_monoid()
        monoid1150 = _t1998
        _t1999 = self.parse_relation_id()
        relation_id1151 = _t1999
        _t2000 = self.parse_abstraction_with_arity()
        abstraction_with_arity1152 = _t2000
        if self.match_lookahead_literal("(", 0):
            _t2002 = self.parse_attrs()
            _t2001 = _t2002
        else:
            _t2001 = None
        attrs1153 = _t2001
        self.consume_literal(")")
        _t2003 = logic_pb2.MonusDef(monoid=monoid1150, name=relation_id1151, body=abstraction_with_arity1152[0], attrs=(attrs1153 if attrs1153 is not None else []), value_arity=abstraction_with_arity1152[1])
        result1155 = _t2003
        self.record_span(span_start1154, "MonusDef")
        return result1155

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1160 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t2004 = self.parse_relation_id()
        relation_id1156 = _t2004
        _t2005 = self.parse_abstraction()
        abstraction1157 = _t2005
        _t2006 = self.parse_functional_dependency_keys()
        functional_dependency_keys1158 = _t2006
        _t2007 = self.parse_functional_dependency_values()
        functional_dependency_values1159 = _t2007
        self.consume_literal(")")
        _t2008 = logic_pb2.FunctionalDependency(guard=abstraction1157, keys=functional_dependency_keys1158, values=functional_dependency_values1159)
        _t2009 = logic_pb2.Constraint(name=relation_id1156, functional_dependency=_t2008)
        result1161 = _t2009
        self.record_span(span_start1160, "Constraint")
        return result1161

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1162 = []
        cond1163 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1163:
            _t2010 = self.parse_var()
            item1164 = _t2010
            xs1162.append(item1164)
            cond1163 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1165 = xs1162
        self.consume_literal(")")
        return vars1165

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1166 = []
        cond1167 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1167:
            _t2011 = self.parse_var()
            item1168 = _t2011
            xs1166.append(item1168)
            cond1167 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1169 = xs1166
        self.consume_literal(")")
        return vars1169

    def parse_data(self) -> logic_pb2.Data:
        span_start1175 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t2013 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t2014 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t2015 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t2016 = 1
                        else:
                            _t2016 = -1
                        _t2015 = _t2016
                    _t2014 = _t2015
                _t2013 = _t2014
            _t2012 = _t2013
        else:
            _t2012 = -1
        prediction1170 = _t2012
        if prediction1170 == 3:
            _t2018 = self.parse_iceberg_data()
            iceberg_data1174 = _t2018
            _t2019 = logic_pb2.Data(iceberg_data=iceberg_data1174)
            _t2017 = _t2019
        else:
            if prediction1170 == 2:
                _t2021 = self.parse_csv_data()
                csv_data1173 = _t2021
                _t2022 = logic_pb2.Data(csv_data=csv_data1173)
                _t2020 = _t2022
            else:
                if prediction1170 == 1:
                    _t2024 = self.parse_betree_relation()
                    betree_relation1172 = _t2024
                    _t2025 = logic_pb2.Data(betree_relation=betree_relation1172)
                    _t2023 = _t2025
                else:
                    if prediction1170 == 0:
                        _t2027 = self.parse_edb()
                        edb1171 = _t2027
                        _t2028 = logic_pb2.Data(edb=edb1171)
                        _t2026 = _t2028
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t2023 = _t2026
                _t2020 = _t2023
            _t2017 = _t2020
        result1176 = _t2017
        self.record_span(span_start1175, "Data")
        return result1176

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1180 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t2029 = self.parse_relation_id()
        relation_id1177 = _t2029
        _t2030 = self.parse_edb_path()
        edb_path1178 = _t2030
        _t2031 = self.parse_edb_types()
        edb_types1179 = _t2031
        self.consume_literal(")")
        _t2032 = logic_pb2.EDB(target_id=relation_id1177, path=edb_path1178, types=edb_types1179)
        result1181 = _t2032
        self.record_span(span_start1180, "EDB")
        return result1181

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1182 = []
        cond1183 = self.match_lookahead_terminal("STRING", 0)
        while cond1183:
            item1184 = self.consume_terminal("STRING")
            xs1182.append(item1184)
            cond1183 = self.match_lookahead_terminal("STRING", 0)
        strings1185 = xs1182
        self.consume_literal("]")
        return strings1185

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1186 = []
        cond1187 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1187:
            _t2033 = self.parse_type()
            item1188 = _t2033
            xs1186.append(item1188)
            cond1187 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1189 = xs1186
        self.consume_literal("]")
        return types1189

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1192 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t2034 = self.parse_relation_id()
        relation_id1190 = _t2034
        _t2035 = self.parse_betree_info()
        betree_info1191 = _t2035
        self.consume_literal(")")
        _t2036 = logic_pb2.BeTreeRelation(name=relation_id1190, relation_info=betree_info1191)
        result1193 = _t2036
        self.record_span(span_start1192, "BeTreeRelation")
        return result1193

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1197 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t2037 = self.parse_betree_info_key_types()
        betree_info_key_types1194 = _t2037
        _t2038 = self.parse_betree_info_value_types()
        betree_info_value_types1195 = _t2038
        _t2039 = self.parse_config_dict()
        config_dict1196 = _t2039
        self.consume_literal(")")
        _t2040 = self.construct_betree_info(betree_info_key_types1194, betree_info_value_types1195, config_dict1196)
        result1198 = _t2040
        self.record_span(span_start1197, "BeTreeInfo")
        return result1198

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1199 = []
        cond1200 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1200:
            _t2041 = self.parse_type()
            item1201 = _t2041
            xs1199.append(item1201)
            cond1200 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1202 = xs1199
        self.consume_literal(")")
        return types1202

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1203 = []
        cond1204 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1204:
            _t2042 = self.parse_type()
            item1205 = _t2042
            xs1203.append(item1205)
            cond1204 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1206 = xs1203
        self.consume_literal(")")
        return types1206

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1212 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t2043 = self.parse_csvlocator()
        csvlocator1207 = _t2043
        _t2044 = self.parse_csv_config()
        csv_config1208 = _t2044
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("columns", 1)):
            _t2046 = self.parse_gnf_columns()
            _t2045 = _t2046
        else:
            _t2045 = None
        gnf_columns1209 = _t2045
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("relations", 1)):
            _t2048 = self.parse_target_relations()
            _t2047 = _t2048
        else:
            _t2047 = None
        target_relations1210 = _t2047
        _t2049 = self.parse_csv_asof()
        csv_asof1211 = _t2049
        self.consume_literal(")")
        _t2050 = self.construct_csv_data(csvlocator1207, csv_config1208, gnf_columns1209, target_relations1210, csv_asof1211)
        result1213 = _t2050
        self.record_span(span_start1212, "CSVData")
        return result1213

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1216 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t2052 = self.parse_csv_locator_paths()
            _t2051 = _t2052
        else:
            _t2051 = None
        csv_locator_paths1214 = _t2051
        if self.match_lookahead_literal("(", 0):
            _t2054 = self.parse_csv_locator_inline_data()
            _t2053 = _t2054
        else:
            _t2053 = None
        csv_locator_inline_data1215 = _t2053
        self.consume_literal(")")
        _t2055 = logic_pb2.CSVLocator(paths=(csv_locator_paths1214 if csv_locator_paths1214 is not None else []), inline_data=(csv_locator_inline_data1215 if csv_locator_inline_data1215 is not None else "").encode())
        result1217 = _t2055
        self.record_span(span_start1216, "CSVLocator")
        return result1217

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1218 = []
        cond1219 = self.match_lookahead_terminal("STRING", 0)
        while cond1219:
            item1220 = self.consume_terminal("STRING")
            xs1218.append(item1220)
            cond1219 = self.match_lookahead_terminal("STRING", 0)
        strings1221 = xs1218
        self.consume_literal(")")
        return strings1221

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        formatted_string1222 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return formatted_string1222

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1225 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t2056 = self.parse_config_dict()
        config_dict1223 = _t2056
        if self.match_lookahead_literal("(", 0):
            _t2058 = self.parse__storage_integration()
            _t2057 = _t2058
        else:
            _t2057 = None
        _storage_integration1224 = _t2057
        self.consume_literal(")")
        _t2059 = self.construct_csv_config(config_dict1223, _storage_integration1224)
        result1226 = _t2059
        self.record_span(span_start1225, "CSVConfig")
        return result1226

    def parse__storage_integration(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("(")
        self.consume_literal("storage_integration")
        _t2060 = self.parse_config_dict()
        config_dict1227 = _t2060
        self.consume_literal(")")
        return config_dict1227

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1228 = []
        cond1229 = self.match_lookahead_literal("(", 0)
        while cond1229:
            _t2061 = self.parse_gnf_column()
            item1230 = _t2061
            xs1228.append(item1230)
            cond1229 = self.match_lookahead_literal("(", 0)
        gnf_columns1231 = xs1228
        self.consume_literal(")")
        return gnf_columns1231

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1238 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t2062 = self.parse_gnf_column_path()
        gnf_column_path1232 = _t2062
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t2064 = self.parse_relation_id()
            _t2063 = _t2064
        else:
            _t2063 = None
        relation_id1233 = _t2063
        self.consume_literal("[")
        xs1234 = []
        cond1235 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1235:
            _t2065 = self.parse_type()
            item1236 = _t2065
            xs1234.append(item1236)
            cond1235 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1237 = xs1234
        self.consume_literal("]")
        self.consume_literal(")")
        _t2066 = logic_pb2.GNFColumn(column_path=gnf_column_path1232, target_id=relation_id1233, types=types1237)
        result1239 = _t2066
        self.record_span(span_start1238, "GNFColumn")
        return result1239

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t2067 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t2068 = 0
            else:
                _t2068 = -1
            _t2067 = _t2068
        prediction1240 = _t2067
        if prediction1240 == 1:
            self.consume_literal("[")
            xs1242 = []
            cond1243 = self.match_lookahead_terminal("STRING", 0)
            while cond1243:
                item1244 = self.consume_terminal("STRING")
                xs1242.append(item1244)
                cond1243 = self.match_lookahead_terminal("STRING", 0)
            strings1245 = xs1242
            self.consume_literal("]")
            _t2069 = strings1245
        else:
            if prediction1240 == 0:
                string1241 = self.consume_terminal("STRING")
                _t2070 = [string1241]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2069 = _t2070
        return _t2069

    def parse_target_relations(self) -> logic_pb2.TargetRelations:
        span_start1249 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relations")
        _t2071 = self.parse_relation_keys()
        relation_keys1246 = _t2071
        _t2072 = self.parse_relation_body()
        relation_body1247 = _t2072
        if self.match_lookahead_literal("(", 0):
            _t2074 = self.parse_load_errors()
            _t2073 = _t2074
        else:
            _t2073 = None
        load_errors1248 = _t2073
        self.consume_literal(")")
        _t2075 = self.construct_relations(relation_keys1246, relation_body1247, load_errors1248)
        result1250 = _t2075
        self.record_span(span_start1249, "TargetRelations")
        return result1250

    def parse_relation_keys(self) -> tuple[Sequence[logic_pb2.NamedColumn], bool]:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("keys", 1):
                if self.match_lookahead_literal("synthetic", 2):
                    _t2078 = 1
                else:
                    if self.match_lookahead_literal(")", 2):
                        _t2079 = 0
                    else:
                        if self.match_lookahead_literal("(", 2):
                            _t2080 = 0
                        else:
                            _t2080 = -1
                        _t2079 = _t2080
                    _t2078 = _t2079
                _t2077 = _t2078
            else:
                _t2077 = -1
            _t2076 = _t2077
        else:
            _t2076 = -1
        prediction1251 = _t2076
        if prediction1251 == 1:
            self.consume_literal("(")
            self.consume_literal("keys")
            self.consume_literal("synthetic")
            self.consume_literal(")")
            _t2081 = ([], True,)
        else:
            if prediction1251 == 0:
                self.consume_literal("(")
                self.consume_literal("keys")
                xs1252 = []
                cond1253 = self.match_lookahead_literal("(", 0)
                while cond1253:
                    _t2083 = self.parse_named_column()
                    item1254 = _t2083
                    xs1252.append(item1254)
                    cond1253 = self.match_lookahead_literal("(", 0)
                named_columns1255 = xs1252
                self.consume_literal(")")
                _t2082 = (named_columns1255, False,)
            else:
                raise ParseError("Unexpected token in relation_keys" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2081 = _t2082
        return _t2081

    def parse_named_column(self) -> logic_pb2.NamedColumn:
        span_start1258 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1256 = self.consume_terminal("STRING")
        _t2084 = self.parse_type()
        type1257 = _t2084
        self.consume_literal(")")
        _t2085 = logic_pb2.NamedColumn(name=string1256, type=type1257)
        result1259 = _t2085
        self.record_span(span_start1258, "NamedColumn")
        return result1259

    def parse_relation_body(self) -> logic_pb2.TargetRelations:
        span_start1264 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("relation", 1):
                _t2087 = 0
            else:
                if self.match_lookahead_literal("inserts", 1):
                    _t2088 = 1
                else:
                    _t2088 = 0
                _t2087 = _t2088
            _t2086 = _t2087
        else:
            _t2086 = 0
        prediction1260 = _t2086
        if prediction1260 == 1:
            _t2090 = self.parse_cdc_inserts()
            cdc_inserts1262 = _t2090
            _t2091 = self.parse_cdc_deletes()
            cdc_deletes1263 = _t2091
            _t2092 = self.construct_cdc_relations(cdc_inserts1262, cdc_deletes1263)
            _t2089 = _t2092
        else:
            if prediction1260 == 0:
                _t2094 = self.parse_non_cdc_relations()
                non_cdc_relations1261 = _t2094
                _t2095 = self.construct_non_cdc_relations(non_cdc_relations1261)
                _t2093 = _t2095
            else:
                raise ParseError("Unexpected token in relation_body" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2089 = _t2093
        result1265 = _t2089
        self.record_span(span_start1264, "TargetRelations")
        return result1265

    def parse_non_cdc_relations(self) -> Sequence[logic_pb2.TargetRelation]:
        xs1266 = []
        cond1267 = (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("relation", 1))
        while cond1267:
            _t2096 = self.parse_target_relation()
            item1268 = _t2096
            xs1266.append(item1268)
            cond1267 = (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("relation", 1))
        return xs1266

    def parse_target_relation(self) -> logic_pb2.TargetRelation:
        span_start1274 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relation")
        _t2097 = self.parse_relation_id()
        relation_id1269 = _t2097
        xs1270 = []
        cond1271 = self.match_lookahead_literal("(", 0)
        while cond1271:
            _t2098 = self.parse_named_column()
            item1272 = _t2098
            xs1270.append(item1272)
            cond1271 = self.match_lookahead_literal("(", 0)
        named_columns1273 = xs1270
        self.consume_literal(")")
        _t2099 = logic_pb2.TargetRelation(target_id=relation_id1269, values=named_columns1273)
        result1275 = _t2099
        self.record_span(span_start1274, "TargetRelation")
        return result1275

    def parse_cdc_inserts(self) -> Sequence[logic_pb2.TargetRelation]:
        self.consume_literal("(")
        self.consume_literal("inserts")
        xs1276 = []
        cond1277 = self.match_lookahead_literal("(", 0)
        while cond1277:
            _t2100 = self.parse_target_relation()
            item1278 = _t2100
            xs1276.append(item1278)
            cond1277 = self.match_lookahead_literal("(", 0)
        target_relations1279 = xs1276
        self.consume_literal(")")
        return target_relations1279

    def parse_cdc_deletes(self) -> Sequence[logic_pb2.TargetRelation]:
        self.consume_literal("(")
        self.consume_literal("deletes")
        xs1280 = []
        cond1281 = self.match_lookahead_literal("(", 0)
        while cond1281:
            _t2101 = self.parse_target_relation()
            item1282 = _t2101
            xs1280.append(item1282)
            cond1281 = self.match_lookahead_literal("(", 0)
        target_relations1283 = xs1280
        self.consume_literal(")")
        return target_relations1283

    def parse_load_errors(self) -> logic_pb2.RelationId:
        span_start1285 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("load_errors")
        _t2102 = self.parse_relation_id()
        relation_id1284 = _t2102
        self.consume_literal(")")
        result1286 = relation_id1284
        self.record_span(span_start1285, "RelationId")
        return result1286

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1287 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1287

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1294 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t2103 = self.parse_iceberg_locator()
        iceberg_locator1288 = _t2103
        _t2104 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1289 = _t2104
        _t2105 = self.parse_gnf_columns()
        gnf_columns1290 = _t2105
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t2107 = self.parse_iceberg_from_snapshot()
            _t2106 = _t2107
        else:
            _t2106 = None
        iceberg_from_snapshot1291 = _t2106
        if self.match_lookahead_literal("(", 0):
            _t2109 = self.parse_iceberg_to_snapshot()
            _t2108 = _t2109
        else:
            _t2108 = None
        iceberg_to_snapshot1292 = _t2108
        _t2110 = self.parse_boolean_value()
        boolean_value1293 = _t2110
        self.consume_literal(")")
        _t2111 = self.construct_iceberg_data(iceberg_locator1288, iceberg_catalog_config1289, gnf_columns1290, iceberg_from_snapshot1291, iceberg_to_snapshot1292, boolean_value1293)
        result1295 = _t2111
        self.record_span(span_start1294, "IcebergData")
        return result1295

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1299 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t2112 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1296 = _t2112
        _t2113 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1297 = _t2113
        _t2114 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1298 = _t2114
        self.consume_literal(")")
        _t2115 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1296, namespace=iceberg_locator_namespace1297, warehouse=iceberg_locator_warehouse1298)
        result1300 = _t2115
        self.record_span(span_start1299, "IcebergLocator")
        return result1300

    def parse_iceberg_locator_table_name(self) -> str:
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1301 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1301

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1302 = []
        cond1303 = self.match_lookahead_terminal("STRING", 0)
        while cond1303:
            item1304 = self.consume_terminal("STRING")
            xs1302.append(item1304)
            cond1303 = self.match_lookahead_terminal("STRING", 0)
        strings1305 = xs1302
        self.consume_literal(")")
        return strings1305

    def parse_iceberg_locator_warehouse(self) -> str:
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string1306 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1306

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1311 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t2116 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1307 = _t2116
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t2118 = self.parse_iceberg_catalog_config_scope()
            _t2117 = _t2118
        else:
            _t2117 = None
        iceberg_catalog_config_scope1308 = _t2117
        _t2119 = self.parse_iceberg_properties()
        iceberg_properties1309 = _t2119
        _t2120 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1310 = _t2120
        self.consume_literal(")")
        _t2121 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1307, iceberg_catalog_config_scope1308, iceberg_properties1309, iceberg_auth_properties1310)
        result1312 = _t2121
        self.record_span(span_start1311, "IcebergCatalogConfig")
        return result1312

    def parse_iceberg_catalog_uri(self) -> str:
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1313 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1313

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1314 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1314

    def parse_iceberg_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1315 = []
        cond1316 = self.match_lookahead_literal("(", 0)
        while cond1316:
            _t2122 = self.parse_iceberg_property_entry()
            item1317 = _t2122
            xs1315.append(item1317)
            cond1316 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1318 = xs1315
        self.consume_literal(")")
        return iceberg_property_entrys1318

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1319 = self.consume_terminal("STRING")
        string_31320 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1319, string_31320,)

    def parse_iceberg_auth_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1321 = []
        cond1322 = self.match_lookahead_literal("(", 0)
        while cond1322:
            _t2123 = self.parse_iceberg_masked_property_entry()
            item1323 = _t2123
            xs1321.append(item1323)
            cond1322 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1324 = xs1321
        self.consume_literal(")")
        return iceberg_masked_property_entrys1324

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1325 = self.consume_terminal("STRING")
        string_31326 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1325, string_31326,)

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1327 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1327

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1328 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1328

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1330 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2124 = self.parse_fragment_id()
        fragment_id1329 = _t2124
        self.consume_literal(")")
        _t2125 = transactions_pb2.Undefine(fragment_id=fragment_id1329)
        result1331 = _t2125
        self.record_span(span_start1330, "Undefine")
        return result1331

    def parse_context(self) -> transactions_pb2.Context:
        span_start1336 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1332 = []
        cond1333 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1333:
            _t2126 = self.parse_relation_id()
            item1334 = _t2126
            xs1332.append(item1334)
            cond1333 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1335 = xs1332
        self.consume_literal(")")
        _t2127 = transactions_pb2.Context(relations=relation_ids1335)
        result1337 = _t2127
        self.record_span(span_start1336, "Context")
        return result1337

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1343 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t2128 = self.parse_edb_path()
        edb_path1338 = _t2128
        xs1339 = []
        cond1340 = self.match_lookahead_literal("[", 0)
        while cond1340:
            _t2129 = self.parse_snapshot_mapping()
            item1341 = _t2129
            xs1339.append(item1341)
            cond1340 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1342 = xs1339
        self.consume_literal(")")
        _t2130 = transactions_pb2.Snapshot(prefix=edb_path1338, mappings=snapshot_mappings1342)
        result1344 = _t2130
        self.record_span(span_start1343, "Snapshot")
        return result1344

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1347 = self.span_start()
        _t2131 = self.parse_edb_path()
        edb_path1345 = _t2131
        _t2132 = self.parse_relation_id()
        relation_id1346 = _t2132
        _t2133 = transactions_pb2.SnapshotMapping(destination_path=edb_path1345, source_relation=relation_id1346)
        result1348 = _t2133
        self.record_span(span_start1347, "SnapshotMapping")
        return result1348

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1349 = []
        cond1350 = self.match_lookahead_literal("(", 0)
        while cond1350:
            _t2134 = self.parse_read()
            item1351 = _t2134
            xs1349.append(item1351)
            cond1350 = self.match_lookahead_literal("(", 0)
        reads1352 = xs1349
        self.consume_literal(")")
        return reads1352

    def parse_read(self) -> transactions_pb2.Read:
        span_start1359 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2136 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2137 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t2138 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t2139 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t2140 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t2141 = 3
                                else:
                                    _t2141 = -1
                                _t2140 = _t2141
                            _t2139 = _t2140
                        _t2138 = _t2139
                    _t2137 = _t2138
                _t2136 = _t2137
            _t2135 = _t2136
        else:
            _t2135 = -1
        prediction1353 = _t2135
        if prediction1353 == 4:
            _t2143 = self.parse_export()
            export1358 = _t2143
            _t2144 = transactions_pb2.Read(export=export1358)
            _t2142 = _t2144
        else:
            if prediction1353 == 3:
                _t2146 = self.parse_abort()
                abort1357 = _t2146
                _t2147 = transactions_pb2.Read(abort=abort1357)
                _t2145 = _t2147
            else:
                if prediction1353 == 2:
                    _t2149 = self.parse_what_if()
                    what_if1356 = _t2149
                    _t2150 = transactions_pb2.Read(what_if=what_if1356)
                    _t2148 = _t2150
                else:
                    if prediction1353 == 1:
                        _t2152 = self.parse_output()
                        output1355 = _t2152
                        _t2153 = transactions_pb2.Read(output=output1355)
                        _t2151 = _t2153
                    else:
                        if prediction1353 == 0:
                            _t2155 = self.parse_demand()
                            demand1354 = _t2155
                            _t2156 = transactions_pb2.Read(demand=demand1354)
                            _t2154 = _t2156
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2151 = _t2154
                    _t2148 = _t2151
                _t2145 = _t2148
            _t2142 = _t2145
        result1360 = _t2142
        self.record_span(span_start1359, "Read")
        return result1360

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1362 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2157 = self.parse_relation_id()
        relation_id1361 = _t2157
        self.consume_literal(")")
        _t2158 = transactions_pb2.Demand(relation_id=relation_id1361)
        result1363 = _t2158
        self.record_span(span_start1362, "Demand")
        return result1363

    def parse_output(self) -> transactions_pb2.Output:
        span_start1366 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2159 = self.parse_name()
        name1364 = _t2159
        _t2160 = self.parse_relation_id()
        relation_id1365 = _t2160
        self.consume_literal(")")
        _t2161 = transactions_pb2.Output(name=name1364, relation_id=relation_id1365)
        result1367 = _t2161
        self.record_span(span_start1366, "Output")
        return result1367

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1370 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2162 = self.parse_name()
        name1368 = _t2162
        _t2163 = self.parse_epoch()
        epoch1369 = _t2163
        self.consume_literal(")")
        _t2164 = transactions_pb2.WhatIf(branch=name1368, epoch=epoch1369)
        result1371 = _t2164
        self.record_span(span_start1370, "WhatIf")
        return result1371

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1374 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2166 = self.parse_name()
            _t2165 = _t2166
        else:
            _t2165 = None
        name1372 = _t2165
        _t2167 = self.parse_relation_id()
        relation_id1373 = _t2167
        self.consume_literal(")")
        _t2168 = transactions_pb2.Abort(name=(name1372 if name1372 is not None else "abort"), relation_id=relation_id1373)
        result1375 = _t2168
        self.record_span(span_start1374, "Abort")
        return result1375

    def parse_export(self) -> transactions_pb2.Export:
        span_start1379 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2170 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2171 = 0
                else:
                    _t2171 = -1
                _t2170 = _t2171
            _t2169 = _t2170
        else:
            _t2169 = -1
        prediction1376 = _t2169
        if prediction1376 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2173 = self.parse_export_iceberg_config()
            export_iceberg_config1378 = _t2173
            self.consume_literal(")")
            _t2174 = transactions_pb2.Export(iceberg_config=export_iceberg_config1378)
            _t2172 = _t2174
        else:
            if prediction1376 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2176 = self.parse_export_csv_config()
                export_csv_config1377 = _t2176
                self.consume_literal(")")
                _t2177 = transactions_pb2.Export(csv_config=export_csv_config1377)
                _t2175 = _t2177
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2172 = _t2175
        result1380 = _t2172
        self.record_span(span_start1379, "Export")
        return result1380

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1388 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2179 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2180 = 1
                else:
                    _t2180 = -1
                _t2179 = _t2180
            _t2178 = _t2179
        else:
            _t2178 = -1
        prediction1381 = _t2178
        if prediction1381 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2182 = self.parse_export_csv_path()
            export_csv_path1385 = _t2182
            _t2183 = self.parse_export_csv_columns_list()
            export_csv_columns_list1386 = _t2183
            _t2184 = self.parse_config_dict()
            config_dict1387 = _t2184
            self.consume_literal(")")
            _t2185 = self.construct_export_csv_config(export_csv_path1385, export_csv_columns_list1386, config_dict1387)
            _t2181 = _t2185
        else:
            if prediction1381 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2187 = self.parse_export_csv_output_location()
                export_csv_output_location1382 = _t2187
                _t2188 = self.parse_export_csv_source()
                export_csv_source1383 = _t2188
                _t2189 = self.parse_csv_config()
                csv_config1384 = _t2189
                self.consume_literal(")")
                _t2190 = self.construct_export_csv_config_with_location(export_csv_output_location1382, export_csv_source1383, csv_config1384)
                _t2186 = _t2190
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2181 = _t2186
        result1389 = _t2181
        self.record_span(span_start1388, "ExportCSVConfig")
        return result1389

    def parse_export_csv_output_location(self) -> tuple[str, str]:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("transaction_output_name", 1):
                _t2192 = 1
            else:
                if self.match_lookahead_literal("path", 1):
                    _t2193 = 0
                else:
                    _t2193 = -1
                _t2192 = _t2193
            _t2191 = _t2192
        else:
            _t2191 = -1
        prediction1390 = _t2191
        if prediction1390 == 1:
            self.consume_literal("(")
            self.consume_literal("transaction_output_name")
            _t2195 = self.parse_name()
            name1392 = _t2195
            self.consume_literal(")")
            _t2194 = ("", name1392,)
        else:
            if prediction1390 == 0:
                self.consume_literal("(")
                self.consume_literal("path")
                string1391 = self.consume_terminal("STRING")
                self.consume_literal(")")
                _t2196 = (string1391, "",)
            else:
                raise ParseError("Unexpected token in export_csv_output_location" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2194 = _t2196
        return _t2194

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1399 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2198 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2199 = 0
                else:
                    _t2199 = -1
                _t2198 = _t2199
            _t2197 = _t2198
        else:
            _t2197 = -1
        prediction1393 = _t2197
        if prediction1393 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2201 = self.parse_relation_id()
            relation_id1398 = _t2201
            self.consume_literal(")")
            _t2202 = transactions_pb2.ExportCSVSource(table_def=relation_id1398)
            _t2200 = _t2202
        else:
            if prediction1393 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1394 = []
                cond1395 = self.match_lookahead_literal("(", 0)
                while cond1395:
                    _t2204 = self.parse_export_csv_column()
                    item1396 = _t2204
                    xs1394.append(item1396)
                    cond1395 = self.match_lookahead_literal("(", 0)
                export_csv_columns1397 = xs1394
                self.consume_literal(")")
                _t2205 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1397)
                _t2206 = transactions_pb2.ExportCSVSource(gnf_columns=_t2205)
                _t2203 = _t2206
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2200 = _t2203
        result1400 = _t2200
        self.record_span(span_start1399, "ExportCSVSource")
        return result1400

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1403 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1401 = self.consume_terminal("STRING")
        _t2207 = self.parse_relation_id()
        relation_id1402 = _t2207
        self.consume_literal(")")
        _t2208 = transactions_pb2.ExportCSVColumn(column_name=string1401, column_data=relation_id1402)
        result1404 = _t2208
        self.record_span(span_start1403, "ExportCSVColumn")
        return result1404

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1405 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1405

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1406 = []
        cond1407 = self.match_lookahead_literal("(", 0)
        while cond1407:
            _t2209 = self.parse_export_csv_column()
            item1408 = _t2209
            xs1406.append(item1408)
            cond1407 = self.match_lookahead_literal("(", 0)
        export_csv_columns1409 = xs1406
        self.consume_literal(")")
        return export_csv_columns1409

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1415 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2210 = self.parse_iceberg_locator()
        iceberg_locator1410 = _t2210
        _t2211 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1411 = _t2211
        _t2212 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1412 = _t2212
        _t2213 = self.parse_iceberg_table_properties()
        iceberg_table_properties1413 = _t2213
        if self.match_lookahead_literal("{", 0):
            _t2215 = self.parse_config_dict()
            _t2214 = _t2215
        else:
            _t2214 = None
        config_dict1414 = _t2214
        self.consume_literal(")")
        _t2216 = self.construct_export_iceberg_config_full(iceberg_locator1410, iceberg_catalog_config1411, export_iceberg_table_def1412, iceberg_table_properties1413, config_dict1414)
        result1416 = _t2216
        self.record_span(span_start1415, "ExportIcebergConfig")
        return result1416

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1418 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2217 = self.parse_relation_id()
        relation_id1417 = _t2217
        self.consume_literal(")")
        result1419 = relation_id1417
        self.record_span(span_start1418, "RelationId")
        return result1419

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1420 = []
        cond1421 = self.match_lookahead_literal("(", 0)
        while cond1421:
            _t2218 = self.parse_iceberg_property_entry()
            item1422 = _t2218
            xs1420.append(item1422)
            cond1421 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1423 = xs1420
        self.consume_literal(")")
        return iceberg_property_entrys1423


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
