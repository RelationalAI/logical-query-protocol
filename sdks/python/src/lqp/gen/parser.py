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
            _t2211 = None
        assert value is not None
        if value.HasField("int32_value"):
            assert value is not None
            return value.int32_value
        else:
            _t2212 = None
        raise ParseError("expected an int32 value (e.g. `1i32`) for this config field")

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2213 = value.HasField("int_value")
        else:
            _t2213 = False
        if _t2213:
            assert value is not None
            return value.int_value
        else:
            _t2214 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2215 = value.HasField("string_value")
        else:
            _t2215 = False
        if _t2215:
            assert value is not None
            return value.string_value
        else:
            _t2216 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2217 = value.HasField("boolean_value")
        else:
            _t2217 = False
        if _t2217:
            assert value is not None
            return value.boolean_value
        else:
            _t2218 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2219 = value.HasField("string_value")
        else:
            _t2219 = False
        if _t2219:
            assert value is not None
            return [value.string_value]
        else:
            _t2220 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
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
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2223 = value.HasField("float_value")
        else:
            _t2223 = False
        if _t2223:
            assert value is not None
            return value.float_value
        else:
            _t2224 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2225 = value.HasField("string_value")
        else:
            _t2225 = False
        if _t2225:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2226 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2227 = value.HasField("uint128_value")
        else:
            _t2227 = False
        if _t2227:
            assert value is not None
            return value.uint128_value
        else:
            _t2228 = None
        return None

    def construct_non_cdc_relations(self, targets: Sequence[logic_pb2.TargetRelation]) -> logic_pb2.TargetRelations:
        _t2229 = logic_pb2.PlainTargets(targets=targets)
        _t2230 = logic_pb2.TargetRelations(keys=[], plain=_t2229)
        return _t2230

    def construct_cdc_relations(self, inserts: Sequence[logic_pb2.TargetRelation], deletes: Sequence[logic_pb2.TargetRelation]) -> logic_pb2.TargetRelations:
        _t2231 = logic_pb2.CDCTargets(inserts=inserts, deletes=deletes)
        _t2232 = logic_pb2.TargetRelations(keys=[], cdc=_t2231)
        return _t2232

    def construct_synthetic_keys(self, marker: str) -> tuple[Sequence[logic_pb2.NamedColumn], bool]:
        if marker != "synthetic_key":
            raise ParseError("expected the `:synthetic_key` marker in the relation keys clause")
        else:
            _t2233 = None
        return ([], True,)

    def construct_relations(self, keys: tuple[Sequence[logic_pb2.NamedColumn], bool], body: logic_pb2.TargetRelations) -> logic_pb2.TargetRelations:
        if body.HasField("plain"):
            _t2235 = logic_pb2.TargetRelations(keys=keys[0], synthetic_key=keys[1], plain=body.plain)
            return _t2235
        else:
            _t2234 = None
        _t2236 = logic_pb2.TargetRelations(keys=keys[0], synthetic_key=keys[1], cdc=body.cdc)
        return _t2236

    def construct_csv_data(self, locator: logic_pb2.CSVLocator, config: logic_pb2.CSVConfig, columns_opt: Sequence[logic_pb2.GNFColumn] | None, relations_opt: logic_pb2.TargetRelations | None, asof: str) -> logic_pb2.CSVData:
        _t2237 = logic_pb2.CSVData(locator=locator, config=config, columns=(columns_opt if columns_opt is not None else []), asof=asof, relations=relations_opt)
        return _t2237

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]], storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2238 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2238
        _t2239 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2239
        _t2240 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2240
        _t2241 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2241
        _t2242 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2242
        _t2243 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2243
        _t2244 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2244
        _t2245 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2245
        _t2246 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2246
        _t2247 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2247
        _t2248 = self._extract_value_string(config.get("csv_compression"), "")
        compression = _t2248
        _t2249 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2249
        _t2250 = self.construct_csv_storage_integration(storage_integration_opt)
        storage_integration = _t2250
        _t2251 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
        return _t2251

    def construct_csv_storage_integration(self, storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.StorageIntegration | None:
        if storage_integration_opt is None:
            return None
        else:
            _t2252 = None
        assert storage_integration_opt is not None
        config = dict(storage_integration_opt)
        _t2253 = self._extract_value_string(config.get("provider"), "")
        _t2254 = self._extract_value_string(config.get("azure_sas_token"), "")
        _t2255 = self._extract_value_string(config.get("s3_region"), "")
        _t2256 = self._extract_value_string(config.get("s3_access_key_id"), "")
        _t2257 = self._extract_value_string(config.get("s3_secret_access_key"), "")
        _t2258 = logic_pb2.StorageIntegration(provider=_t2253, azure_sas_token=_t2254, s3_region=_t2255, s3_access_key_id=_t2256, s3_secret_access_key=_t2257)
        return _t2258

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2259 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2259
        _t2260 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2260
        _t2261 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2261
        _t2262 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2262
        _t2263 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2263
        _t2264 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2264
        _t2265 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2265
        _t2266 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2266
        _t2267 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2267
        _t2268 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2268
        _t2269 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2269

    def default_configure(self) -> transactions_pb2.Configure:
        _t2270 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2270
        _t2271 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2271

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
        _t2272 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2272
        _t2273 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2273
        _t2274 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2274

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2275 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2275
        _t2276 = self._extract_value_string(config.get("compression"), "")
        compression = _t2276
        _t2277 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2277
        _t2278 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2278
        _t2279 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2279
        _t2280 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2280
        _t2281 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2281
        _t2282 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2282

    def construct_export_csv_config_with_location(self, location: tuple[str, str], csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2283 = transactions_pb2.ExportCSVConfig(path=location[0], transaction_output_name=location[1], csv_source=csv_source, csv_config=csv_config)
        return _t2283

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2284 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2284

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[logic_pb2.GNFColumn], from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2285 = logic_pb2.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2285

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2286 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2286
        _t2287 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2287
        _t2288 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2288
        table_props = dict(table_property_pairs)
        _t2289 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2289

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start715 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1419 = self.parse_configure()
            _t1418 = _t1419
        else:
            _t1418 = None
        configure709 = _t1418
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1421 = self.parse_sync()
            _t1420 = _t1421
        else:
            _t1420 = None
        sync710 = _t1420
        xs711 = []
        cond712 = self.match_lookahead_literal("(", 0)
        while cond712:
            _t1422 = self.parse_epoch()
            item713 = _t1422
            xs711.append(item713)
            cond712 = self.match_lookahead_literal("(", 0)
        epochs714 = xs711
        self.consume_literal(")")
        _t1423 = self.default_configure()
        _t1424 = transactions_pb2.Transaction(epochs=epochs714, configure=(configure709 if configure709 is not None else _t1423), sync=sync710)
        result716 = _t1424
        self.record_span(span_start715, "Transaction")
        return result716

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start718 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1425 = self.parse_config_dict()
        config_dict717 = _t1425
        self.consume_literal(")")
        _t1426 = self.construct_configure(config_dict717)
        result719 = _t1426
        self.record_span(span_start718, "Configure")
        return result719

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs720 = []
        cond721 = self.match_lookahead_literal(":", 0)
        while cond721:
            _t1427 = self.parse_config_key_value()
            item722 = _t1427
            xs720.append(item722)
            cond721 = self.match_lookahead_literal(":", 0)
        config_key_values723 = xs720
        self.consume_literal("}")
        return config_key_values723

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol724 = self.consume_terminal("SYMBOL")
        _t1428 = self.parse_raw_value()
        raw_value725 = _t1428
        return (symbol724, raw_value725,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start739 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1429 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1430 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1431 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1433 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1434 = 0
                            else:
                                _t1434 = -1
                            _t1433 = _t1434
                        _t1432 = _t1433
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1435 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1436 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1437 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1438 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1439 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1440 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1441 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1442 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1443 = 10
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
                        _t1432 = _t1435
                    _t1431 = _t1432
                _t1430 = _t1431
            _t1429 = _t1430
        prediction726 = _t1429
        if prediction726 == 12:
            _t1445 = self.parse_boolean_value()
            boolean_value738 = _t1445
            _t1446 = logic_pb2.Value(boolean_value=boolean_value738)
            _t1444 = _t1446
        else:
            if prediction726 == 11:
                self.consume_literal("missing")
                _t1448 = logic_pb2.MissingValue()
                _t1449 = logic_pb2.Value(missing_value=_t1448)
                _t1447 = _t1449
            else:
                if prediction726 == 10:
                    decimal737 = self.consume_terminal("DECIMAL")
                    _t1451 = logic_pb2.Value(decimal_value=decimal737)
                    _t1450 = _t1451
                else:
                    if prediction726 == 9:
                        int128736 = self.consume_terminal("INT128")
                        _t1453 = logic_pb2.Value(int128_value=int128736)
                        _t1452 = _t1453
                    else:
                        if prediction726 == 8:
                            uint128735 = self.consume_terminal("UINT128")
                            _t1455 = logic_pb2.Value(uint128_value=uint128735)
                            _t1454 = _t1455
                        else:
                            if prediction726 == 7:
                                uint32734 = self.consume_terminal("UINT32")
                                _t1457 = logic_pb2.Value(uint32_value=uint32734)
                                _t1456 = _t1457
                            else:
                                if prediction726 == 6:
                                    float733 = self.consume_terminal("FLOAT")
                                    _t1459 = logic_pb2.Value(float_value=float733)
                                    _t1458 = _t1459
                                else:
                                    if prediction726 == 5:
                                        float32732 = self.consume_terminal("FLOAT32")
                                        _t1461 = logic_pb2.Value(float32_value=float32732)
                                        _t1460 = _t1461
                                    else:
                                        if prediction726 == 4:
                                            int731 = self.consume_terminal("INT")
                                            _t1463 = logic_pb2.Value(int_value=int731)
                                            _t1462 = _t1463
                                        else:
                                            if prediction726 == 3:
                                                int32730 = self.consume_terminal("INT32")
                                                _t1465 = logic_pb2.Value(int32_value=int32730)
                                                _t1464 = _t1465
                                            else:
                                                if prediction726 == 2:
                                                    string729 = self.consume_terminal("STRING")
                                                    _t1467 = logic_pb2.Value(string_value=string729)
                                                    _t1466 = _t1467
                                                else:
                                                    if prediction726 == 1:
                                                        _t1469 = self.parse_raw_datetime()
                                                        raw_datetime728 = _t1469
                                                        _t1470 = logic_pb2.Value(datetime_value=raw_datetime728)
                                                        _t1468 = _t1470
                                                    else:
                                                        if prediction726 == 0:
                                                            _t1472 = self.parse_raw_date()
                                                            raw_date727 = _t1472
                                                            _t1473 = logic_pb2.Value(date_value=raw_date727)
                                                            _t1471 = _t1473
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1468 = _t1471
                                                    _t1466 = _t1468
                                                _t1464 = _t1466
                                            _t1462 = _t1464
                                        _t1460 = _t1462
                                    _t1458 = _t1460
                                _t1456 = _t1458
                            _t1454 = _t1456
                        _t1452 = _t1454
                    _t1450 = _t1452
                _t1447 = _t1450
            _t1444 = _t1447
        result740 = _t1444
        self.record_span(span_start739, "Value")
        return result740

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start744 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int741 = self.consume_terminal("INT")
        int_3742 = self.consume_terminal("INT")
        int_4743 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1474 = logic_pb2.DateValue(year=int(int741), month=int(int_3742), day=int(int_4743))
        result745 = _t1474
        self.record_span(span_start744, "DateValue")
        return result745

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start753 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int746 = self.consume_terminal("INT")
        int_3747 = self.consume_terminal("INT")
        int_4748 = self.consume_terminal("INT")
        int_5749 = self.consume_terminal("INT")
        int_6750 = self.consume_terminal("INT")
        int_7751 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1475 = self.consume_terminal("INT")
        else:
            _t1475 = None
        int_8752 = _t1475
        self.consume_literal(")")
        _t1476 = logic_pb2.DateTimeValue(year=int(int746), month=int(int_3747), day=int(int_4748), hour=int(int_5749), minute=int(int_6750), second=int(int_7751), microsecond=int((int_8752 if int_8752 is not None else 0)))
        result754 = _t1476
        self.record_span(span_start753, "DateTimeValue")
        return result754

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1477 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1478 = 1
            else:
                _t1478 = -1
            _t1477 = _t1478
        prediction755 = _t1477
        if prediction755 == 1:
            self.consume_literal("false")
            _t1479 = False
        else:
            if prediction755 == 0:
                self.consume_literal("true")
                _t1480 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1479 = _t1480
        return _t1479

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start760 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs756 = []
        cond757 = self.match_lookahead_literal(":", 0)
        while cond757:
            _t1481 = self.parse_fragment_id()
            item758 = _t1481
            xs756.append(item758)
            cond757 = self.match_lookahead_literal(":", 0)
        fragment_ids759 = xs756
        self.consume_literal(")")
        _t1482 = transactions_pb2.Sync(fragments=fragment_ids759)
        result761 = _t1482
        self.record_span(span_start760, "Sync")
        return result761

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start763 = self.span_start()
        self.consume_literal(":")
        symbol762 = self.consume_terminal("SYMBOL")
        result764 = fragments_pb2.FragmentId(id=symbol762.encode())
        self.record_span(span_start763, "FragmentId")
        return result764

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start767 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1484 = self.parse_epoch_writes()
            _t1483 = _t1484
        else:
            _t1483 = None
        epoch_writes765 = _t1483
        if self.match_lookahead_literal("(", 0):
            _t1486 = self.parse_epoch_reads()
            _t1485 = _t1486
        else:
            _t1485 = None
        epoch_reads766 = _t1485
        self.consume_literal(")")
        _t1487 = transactions_pb2.Epoch(writes=(epoch_writes765 if epoch_writes765 is not None else []), reads=(epoch_reads766 if epoch_reads766 is not None else []))
        result768 = _t1487
        self.record_span(span_start767, "Epoch")
        return result768

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs769 = []
        cond770 = self.match_lookahead_literal("(", 0)
        while cond770:
            _t1488 = self.parse_write()
            item771 = _t1488
            xs769.append(item771)
            cond770 = self.match_lookahead_literal("(", 0)
        writes772 = xs769
        self.consume_literal(")")
        return writes772

    def parse_write(self) -> transactions_pb2.Write:
        span_start778 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1490 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1491 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1492 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1493 = 2
                        else:
                            _t1493 = -1
                        _t1492 = _t1493
                    _t1491 = _t1492
                _t1490 = _t1491
            _t1489 = _t1490
        else:
            _t1489 = -1
        prediction773 = _t1489
        if prediction773 == 3:
            _t1495 = self.parse_snapshot()
            snapshot777 = _t1495
            _t1496 = transactions_pb2.Write(snapshot=snapshot777)
            _t1494 = _t1496
        else:
            if prediction773 == 2:
                _t1498 = self.parse_context()
                context776 = _t1498
                _t1499 = transactions_pb2.Write(context=context776)
                _t1497 = _t1499
            else:
                if prediction773 == 1:
                    _t1501 = self.parse_undefine()
                    undefine775 = _t1501
                    _t1502 = transactions_pb2.Write(undefine=undefine775)
                    _t1500 = _t1502
                else:
                    if prediction773 == 0:
                        _t1504 = self.parse_define()
                        define774 = _t1504
                        _t1505 = transactions_pb2.Write(define=define774)
                        _t1503 = _t1505
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1500 = _t1503
                _t1497 = _t1500
            _t1494 = _t1497
        result779 = _t1494
        self.record_span(span_start778, "Write")
        return result779

    def parse_define(self) -> transactions_pb2.Define:
        span_start781 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1506 = self.parse_fragment()
        fragment780 = _t1506
        self.consume_literal(")")
        _t1507 = transactions_pb2.Define(fragment=fragment780)
        result782 = _t1507
        self.record_span(span_start781, "Define")
        return result782

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start788 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1508 = self.parse_new_fragment_id()
        new_fragment_id783 = _t1508
        xs784 = []
        cond785 = self.match_lookahead_literal("(", 0)
        while cond785:
            _t1509 = self.parse_declaration()
            item786 = _t1509
            xs784.append(item786)
            cond785 = self.match_lookahead_literal("(", 0)
        declarations787 = xs784
        self.consume_literal(")")
        result789 = self.construct_fragment(new_fragment_id783, declarations787)
        self.record_span(span_start788, "Fragment")
        return result789

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start791 = self.span_start()
        _t1510 = self.parse_fragment_id()
        fragment_id790 = _t1510
        self.start_fragment(fragment_id790)
        result792 = fragment_id790
        self.record_span(span_start791, "FragmentId")
        return result792

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start798 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1512 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1513 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1514 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1515 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1516 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1517 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1518 = 1
                                    else:
                                        _t1518 = -1
                                    _t1517 = _t1518
                                _t1516 = _t1517
                            _t1515 = _t1516
                        _t1514 = _t1515
                    _t1513 = _t1514
                _t1512 = _t1513
            _t1511 = _t1512
        else:
            _t1511 = -1
        prediction793 = _t1511
        if prediction793 == 3:
            _t1520 = self.parse_data()
            data797 = _t1520
            _t1521 = logic_pb2.Declaration(data=data797)
            _t1519 = _t1521
        else:
            if prediction793 == 2:
                _t1523 = self.parse_constraint()
                constraint796 = _t1523
                _t1524 = logic_pb2.Declaration(constraint=constraint796)
                _t1522 = _t1524
            else:
                if prediction793 == 1:
                    _t1526 = self.parse_algorithm()
                    algorithm795 = _t1526
                    _t1527 = logic_pb2.Declaration(algorithm=algorithm795)
                    _t1525 = _t1527
                else:
                    if prediction793 == 0:
                        _t1529 = self.parse_def()
                        def794 = _t1529
                        _t1530 = logic_pb2.Declaration()
                        getattr(_t1530, 'def').CopyFrom(def794)
                        _t1528 = _t1530
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1525 = _t1528
                _t1522 = _t1525
            _t1519 = _t1522
        result799 = _t1519
        self.record_span(span_start798, "Declaration")
        return result799

    def parse_def(self) -> logic_pb2.Def:
        span_start803 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1531 = self.parse_relation_id()
        relation_id800 = _t1531
        _t1532 = self.parse_abstraction()
        abstraction801 = _t1532
        if self.match_lookahead_literal("(", 0):
            _t1534 = self.parse_attrs()
            _t1533 = _t1534
        else:
            _t1533 = None
        attrs802 = _t1533
        self.consume_literal(")")
        _t1535 = logic_pb2.Def(name=relation_id800, body=abstraction801, attrs=(attrs802 if attrs802 is not None else []))
        result804 = _t1535
        self.record_span(span_start803, "Def")
        return result804

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start808 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1536 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1537 = 1
            else:
                _t1537 = -1
            _t1536 = _t1537
        prediction805 = _t1536
        if prediction805 == 1:
            uint128807 = self.consume_terminal("UINT128")
            _t1538 = logic_pb2.RelationId(id_low=uint128807.low, id_high=uint128807.high)
        else:
            if prediction805 == 0:
                self.consume_literal(":")
                symbol806 = self.consume_terminal("SYMBOL")
                _t1539 = self.relation_id_from_string(symbol806)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1538 = _t1539
        result809 = _t1538
        self.record_span(span_start808, "RelationId")
        return result809

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start812 = self.span_start()
        self.consume_literal("(")
        _t1540 = self.parse_bindings()
        bindings810 = _t1540
        _t1541 = self.parse_formula()
        formula811 = _t1541
        self.consume_literal(")")
        _t1542 = logic_pb2.Abstraction(vars=(list(bindings810[0]) + list(bindings810[1] if bindings810[1] is not None else [])), value=formula811)
        result813 = _t1542
        self.record_span(span_start812, "Abstraction")
        return result813

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs814 = []
        cond815 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond815:
            _t1543 = self.parse_binding()
            item816 = _t1543
            xs814.append(item816)
            cond815 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings817 = xs814
        if self.match_lookahead_literal("|", 0):
            _t1545 = self.parse_value_bindings()
            _t1544 = _t1545
        else:
            _t1544 = None
        value_bindings818 = _t1544
        self.consume_literal("]")
        return (bindings817, (value_bindings818 if value_bindings818 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start821 = self.span_start()
        symbol819 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1546 = self.parse_type()
        type820 = _t1546
        _t1547 = logic_pb2.Var(name=symbol819)
        _t1548 = logic_pb2.Binding(var=_t1547, type=type820)
        result822 = _t1548
        self.record_span(span_start821, "Binding")
        return result822

    def parse_type(self) -> logic_pb2.Type:
        span_start838 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1549 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1550 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1551 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1552 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1553 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1554 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1555 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1556 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1557 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1558 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1559 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1560 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1561 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1562 = 9
                                                            else:
                                                                _t1562 = -1
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
        prediction823 = _t1549
        if prediction823 == 13:
            _t1564 = self.parse_uint32_type()
            uint32_type837 = _t1564
            _t1565 = logic_pb2.Type(uint32_type=uint32_type837)
            _t1563 = _t1565
        else:
            if prediction823 == 12:
                _t1567 = self.parse_float32_type()
                float32_type836 = _t1567
                _t1568 = logic_pb2.Type(float32_type=float32_type836)
                _t1566 = _t1568
            else:
                if prediction823 == 11:
                    _t1570 = self.parse_int32_type()
                    int32_type835 = _t1570
                    _t1571 = logic_pb2.Type(int32_type=int32_type835)
                    _t1569 = _t1571
                else:
                    if prediction823 == 10:
                        _t1573 = self.parse_boolean_type()
                        boolean_type834 = _t1573
                        _t1574 = logic_pb2.Type(boolean_type=boolean_type834)
                        _t1572 = _t1574
                    else:
                        if prediction823 == 9:
                            _t1576 = self.parse_decimal_type()
                            decimal_type833 = _t1576
                            _t1577 = logic_pb2.Type(decimal_type=decimal_type833)
                            _t1575 = _t1577
                        else:
                            if prediction823 == 8:
                                _t1579 = self.parse_missing_type()
                                missing_type832 = _t1579
                                _t1580 = logic_pb2.Type(missing_type=missing_type832)
                                _t1578 = _t1580
                            else:
                                if prediction823 == 7:
                                    _t1582 = self.parse_datetime_type()
                                    datetime_type831 = _t1582
                                    _t1583 = logic_pb2.Type(datetime_type=datetime_type831)
                                    _t1581 = _t1583
                                else:
                                    if prediction823 == 6:
                                        _t1585 = self.parse_date_type()
                                        date_type830 = _t1585
                                        _t1586 = logic_pb2.Type(date_type=date_type830)
                                        _t1584 = _t1586
                                    else:
                                        if prediction823 == 5:
                                            _t1588 = self.parse_int128_type()
                                            int128_type829 = _t1588
                                            _t1589 = logic_pb2.Type(int128_type=int128_type829)
                                            _t1587 = _t1589
                                        else:
                                            if prediction823 == 4:
                                                _t1591 = self.parse_uint128_type()
                                                uint128_type828 = _t1591
                                                _t1592 = logic_pb2.Type(uint128_type=uint128_type828)
                                                _t1590 = _t1592
                                            else:
                                                if prediction823 == 3:
                                                    _t1594 = self.parse_float_type()
                                                    float_type827 = _t1594
                                                    _t1595 = logic_pb2.Type(float_type=float_type827)
                                                    _t1593 = _t1595
                                                else:
                                                    if prediction823 == 2:
                                                        _t1597 = self.parse_int_type()
                                                        int_type826 = _t1597
                                                        _t1598 = logic_pb2.Type(int_type=int_type826)
                                                        _t1596 = _t1598
                                                    else:
                                                        if prediction823 == 1:
                                                            _t1600 = self.parse_string_type()
                                                            string_type825 = _t1600
                                                            _t1601 = logic_pb2.Type(string_type=string_type825)
                                                            _t1599 = _t1601
                                                        else:
                                                            if prediction823 == 0:
                                                                _t1603 = self.parse_unspecified_type()
                                                                unspecified_type824 = _t1603
                                                                _t1604 = logic_pb2.Type(unspecified_type=unspecified_type824)
                                                                _t1602 = _t1604
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1566 = _t1569
            _t1563 = _t1566
        result839 = _t1563
        self.record_span(span_start838, "Type")
        return result839

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start840 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1605 = logic_pb2.UnspecifiedType()
        result841 = _t1605
        self.record_span(span_start840, "UnspecifiedType")
        return result841

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start842 = self.span_start()
        self.consume_literal("STRING")
        _t1606 = logic_pb2.StringType()
        result843 = _t1606
        self.record_span(span_start842, "StringType")
        return result843

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start844 = self.span_start()
        self.consume_literal("INT")
        _t1607 = logic_pb2.IntType()
        result845 = _t1607
        self.record_span(span_start844, "IntType")
        return result845

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start846 = self.span_start()
        self.consume_literal("FLOAT")
        _t1608 = logic_pb2.FloatType()
        result847 = _t1608
        self.record_span(span_start846, "FloatType")
        return result847

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start848 = self.span_start()
        self.consume_literal("UINT128")
        _t1609 = logic_pb2.UInt128Type()
        result849 = _t1609
        self.record_span(span_start848, "UInt128Type")
        return result849

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start850 = self.span_start()
        self.consume_literal("INT128")
        _t1610 = logic_pb2.Int128Type()
        result851 = _t1610
        self.record_span(span_start850, "Int128Type")
        return result851

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start852 = self.span_start()
        self.consume_literal("DATE")
        _t1611 = logic_pb2.DateType()
        result853 = _t1611
        self.record_span(span_start852, "DateType")
        return result853

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start854 = self.span_start()
        self.consume_literal("DATETIME")
        _t1612 = logic_pb2.DateTimeType()
        result855 = _t1612
        self.record_span(span_start854, "DateTimeType")
        return result855

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start856 = self.span_start()
        self.consume_literal("MISSING")
        _t1613 = logic_pb2.MissingType()
        result857 = _t1613
        self.record_span(span_start856, "MissingType")
        return result857

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start860 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int858 = self.consume_terminal("INT")
        int_3859 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1614 = logic_pb2.DecimalType(precision=int(int858), scale=int(int_3859))
        result861 = _t1614
        self.record_span(span_start860, "DecimalType")
        return result861

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start862 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1615 = logic_pb2.BooleanType()
        result863 = _t1615
        self.record_span(span_start862, "BooleanType")
        return result863

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start864 = self.span_start()
        self.consume_literal("INT32")
        _t1616 = logic_pb2.Int32Type()
        result865 = _t1616
        self.record_span(span_start864, "Int32Type")
        return result865

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start866 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1617 = logic_pb2.Float32Type()
        result867 = _t1617
        self.record_span(span_start866, "Float32Type")
        return result867

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start868 = self.span_start()
        self.consume_literal("UINT32")
        _t1618 = logic_pb2.UInt32Type()
        result869 = _t1618
        self.record_span(span_start868, "UInt32Type")
        return result869

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs870 = []
        cond871 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond871:
            _t1619 = self.parse_binding()
            item872 = _t1619
            xs870.append(item872)
            cond871 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings873 = xs870
        return bindings873

    def parse_formula(self) -> logic_pb2.Formula:
        span_start888 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1621 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1622 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1623 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1624 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1625 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1626 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1627 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1628 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1629 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1630 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1631 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1632 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1633 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1634 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1635 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1636 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1637 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1638 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1639 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1640 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1641 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1642 = 10
                                                                                                else:
                                                                                                    _t1642 = -1
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
                                _t1625 = _t1626
                            _t1624 = _t1625
                        _t1623 = _t1624
                    _t1622 = _t1623
                _t1621 = _t1622
            _t1620 = _t1621
        else:
            _t1620 = -1
        prediction874 = _t1620
        if prediction874 == 12:
            _t1644 = self.parse_cast()
            cast887 = _t1644
            _t1645 = logic_pb2.Formula(cast=cast887)
            _t1643 = _t1645
        else:
            if prediction874 == 11:
                _t1647 = self.parse_rel_atom()
                rel_atom886 = _t1647
                _t1648 = logic_pb2.Formula(rel_atom=rel_atom886)
                _t1646 = _t1648
            else:
                if prediction874 == 10:
                    _t1650 = self.parse_primitive()
                    primitive885 = _t1650
                    _t1651 = logic_pb2.Formula(primitive=primitive885)
                    _t1649 = _t1651
                else:
                    if prediction874 == 9:
                        _t1653 = self.parse_pragma()
                        pragma884 = _t1653
                        _t1654 = logic_pb2.Formula(pragma=pragma884)
                        _t1652 = _t1654
                    else:
                        if prediction874 == 8:
                            _t1656 = self.parse_atom()
                            atom883 = _t1656
                            _t1657 = logic_pb2.Formula(atom=atom883)
                            _t1655 = _t1657
                        else:
                            if prediction874 == 7:
                                _t1659 = self.parse_ffi()
                                ffi882 = _t1659
                                _t1660 = logic_pb2.Formula(ffi=ffi882)
                                _t1658 = _t1660
                            else:
                                if prediction874 == 6:
                                    _t1662 = self.parse_not()
                                    not881 = _t1662
                                    _t1663 = logic_pb2.Formula()
                                    getattr(_t1663, 'not').CopyFrom(not881)
                                    _t1661 = _t1663
                                else:
                                    if prediction874 == 5:
                                        _t1665 = self.parse_disjunction()
                                        disjunction880 = _t1665
                                        _t1666 = logic_pb2.Formula(disjunction=disjunction880)
                                        _t1664 = _t1666
                                    else:
                                        if prediction874 == 4:
                                            _t1668 = self.parse_conjunction()
                                            conjunction879 = _t1668
                                            _t1669 = logic_pb2.Formula(conjunction=conjunction879)
                                            _t1667 = _t1669
                                        else:
                                            if prediction874 == 3:
                                                _t1671 = self.parse_reduce()
                                                reduce878 = _t1671
                                                _t1672 = logic_pb2.Formula(reduce=reduce878)
                                                _t1670 = _t1672
                                            else:
                                                if prediction874 == 2:
                                                    _t1674 = self.parse_exists()
                                                    exists877 = _t1674
                                                    _t1675 = logic_pb2.Formula(exists=exists877)
                                                    _t1673 = _t1675
                                                else:
                                                    if prediction874 == 1:
                                                        _t1677 = self.parse_false()
                                                        false876 = _t1677
                                                        _t1678 = logic_pb2.Formula(disjunction=false876)
                                                        _t1676 = _t1678
                                                    else:
                                                        if prediction874 == 0:
                                                            _t1680 = self.parse_true()
                                                            true875 = _t1680
                                                            _t1681 = logic_pb2.Formula(conjunction=true875)
                                                            _t1679 = _t1681
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1646 = _t1649
            _t1643 = _t1646
        result889 = _t1643
        self.record_span(span_start888, "Formula")
        return result889

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start890 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1682 = logic_pb2.Conjunction(args=[])
        result891 = _t1682
        self.record_span(span_start890, "Conjunction")
        return result891

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start892 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1683 = logic_pb2.Disjunction(args=[])
        result893 = _t1683
        self.record_span(span_start892, "Disjunction")
        return result893

    def parse_exists(self) -> logic_pb2.Exists:
        span_start896 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1684 = self.parse_bindings()
        bindings894 = _t1684
        _t1685 = self.parse_formula()
        formula895 = _t1685
        self.consume_literal(")")
        _t1686 = logic_pb2.Abstraction(vars=(list(bindings894[0]) + list(bindings894[1] if bindings894[1] is not None else [])), value=formula895)
        _t1687 = logic_pb2.Exists(body=_t1686)
        result897 = _t1687
        self.record_span(span_start896, "Exists")
        return result897

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start901 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1688 = self.parse_abstraction()
        abstraction898 = _t1688
        _t1689 = self.parse_abstraction()
        abstraction_3899 = _t1689
        _t1690 = self.parse_terms()
        terms900 = _t1690
        self.consume_literal(")")
        _t1691 = logic_pb2.Reduce(op=abstraction898, body=abstraction_3899, terms=terms900)
        result902 = _t1691
        self.record_span(span_start901, "Reduce")
        return result902

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs903 = []
        cond904 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond904:
            _t1692 = self.parse_term()
            item905 = _t1692
            xs903.append(item905)
            cond904 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms906 = xs903
        self.consume_literal(")")
        return terms906

    def parse_term(self) -> logic_pb2.Term:
        span_start910 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1693 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1694 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1695 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1696 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1697 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1698 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1699 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1700 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1701 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1702 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1703 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1704 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1705 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1706 = 1
                                                            else:
                                                                _t1706 = -1
                                                            _t1705 = _t1706
                                                        _t1704 = _t1705
                                                    _t1703 = _t1704
                                                _t1702 = _t1703
                                            _t1701 = _t1702
                                        _t1700 = _t1701
                                    _t1699 = _t1700
                                _t1698 = _t1699
                            _t1697 = _t1698
                        _t1696 = _t1697
                    _t1695 = _t1696
                _t1694 = _t1695
            _t1693 = _t1694
        prediction907 = _t1693
        if prediction907 == 1:
            _t1708 = self.parse_value()
            value909 = _t1708
            _t1709 = logic_pb2.Term(constant=value909)
            _t1707 = _t1709
        else:
            if prediction907 == 0:
                _t1711 = self.parse_var()
                var908 = _t1711
                _t1712 = logic_pb2.Term(var=var908)
                _t1710 = _t1712
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1707 = _t1710
        result911 = _t1707
        self.record_span(span_start910, "Term")
        return result911

    def parse_var(self) -> logic_pb2.Var:
        span_start913 = self.span_start()
        symbol912 = self.consume_terminal("SYMBOL")
        _t1713 = logic_pb2.Var(name=symbol912)
        result914 = _t1713
        self.record_span(span_start913, "Var")
        return result914

    def parse_value(self) -> logic_pb2.Value:
        span_start928 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1714 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1715 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1716 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1718 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1719 = 0
                            else:
                                _t1719 = -1
                            _t1718 = _t1719
                        _t1717 = _t1718
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1720 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1721 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1722 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1723 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1724 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1725 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1726 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1727 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1728 = 10
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
                        _t1717 = _t1720
                    _t1716 = _t1717
                _t1715 = _t1716
            _t1714 = _t1715
        prediction915 = _t1714
        if prediction915 == 12:
            _t1730 = self.parse_boolean_value()
            boolean_value927 = _t1730
            _t1731 = logic_pb2.Value(boolean_value=boolean_value927)
            _t1729 = _t1731
        else:
            if prediction915 == 11:
                self.consume_literal("missing")
                _t1733 = logic_pb2.MissingValue()
                _t1734 = logic_pb2.Value(missing_value=_t1733)
                _t1732 = _t1734
            else:
                if prediction915 == 10:
                    formatted_decimal926 = self.consume_terminal("DECIMAL")
                    _t1736 = logic_pb2.Value(decimal_value=formatted_decimal926)
                    _t1735 = _t1736
                else:
                    if prediction915 == 9:
                        formatted_int128925 = self.consume_terminal("INT128")
                        _t1738 = logic_pb2.Value(int128_value=formatted_int128925)
                        _t1737 = _t1738
                    else:
                        if prediction915 == 8:
                            formatted_uint128924 = self.consume_terminal("UINT128")
                            _t1740 = logic_pb2.Value(uint128_value=formatted_uint128924)
                            _t1739 = _t1740
                        else:
                            if prediction915 == 7:
                                formatted_uint32923 = self.consume_terminal("UINT32")
                                _t1742 = logic_pb2.Value(uint32_value=formatted_uint32923)
                                _t1741 = _t1742
                            else:
                                if prediction915 == 6:
                                    formatted_float922 = self.consume_terminal("FLOAT")
                                    _t1744 = logic_pb2.Value(float_value=formatted_float922)
                                    _t1743 = _t1744
                                else:
                                    if prediction915 == 5:
                                        formatted_float32921 = self.consume_terminal("FLOAT32")
                                        _t1746 = logic_pb2.Value(float32_value=formatted_float32921)
                                        _t1745 = _t1746
                                    else:
                                        if prediction915 == 4:
                                            formatted_int920 = self.consume_terminal("INT")
                                            _t1748 = logic_pb2.Value(int_value=formatted_int920)
                                            _t1747 = _t1748
                                        else:
                                            if prediction915 == 3:
                                                formatted_int32919 = self.consume_terminal("INT32")
                                                _t1750 = logic_pb2.Value(int32_value=formatted_int32919)
                                                _t1749 = _t1750
                                            else:
                                                if prediction915 == 2:
                                                    formatted_string918 = self.consume_terminal("STRING")
                                                    _t1752 = logic_pb2.Value(string_value=formatted_string918)
                                                    _t1751 = _t1752
                                                else:
                                                    if prediction915 == 1:
                                                        _t1754 = self.parse_datetime()
                                                        datetime917 = _t1754
                                                        _t1755 = logic_pb2.Value(datetime_value=datetime917)
                                                        _t1753 = _t1755
                                                    else:
                                                        if prediction915 == 0:
                                                            _t1757 = self.parse_date()
                                                            date916 = _t1757
                                                            _t1758 = logic_pb2.Value(date_value=date916)
                                                            _t1756 = _t1758
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1753 = _t1756
                                                    _t1751 = _t1753
                                                _t1749 = _t1751
                                            _t1747 = _t1749
                                        _t1745 = _t1747
                                    _t1743 = _t1745
                                _t1741 = _t1743
                            _t1739 = _t1741
                        _t1737 = _t1739
                    _t1735 = _t1737
                _t1732 = _t1735
            _t1729 = _t1732
        result929 = _t1729
        self.record_span(span_start928, "Value")
        return result929

    def parse_date(self) -> logic_pb2.DateValue:
        span_start933 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int930 = self.consume_terminal("INT")
        formatted_int_3931 = self.consume_terminal("INT")
        formatted_int_4932 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1759 = logic_pb2.DateValue(year=int(formatted_int930), month=int(formatted_int_3931), day=int(formatted_int_4932))
        result934 = _t1759
        self.record_span(span_start933, "DateValue")
        return result934

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start942 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int935 = self.consume_terminal("INT")
        formatted_int_3936 = self.consume_terminal("INT")
        formatted_int_4937 = self.consume_terminal("INT")
        formatted_int_5938 = self.consume_terminal("INT")
        formatted_int_6939 = self.consume_terminal("INT")
        formatted_int_7940 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1760 = self.consume_terminal("INT")
        else:
            _t1760 = None
        formatted_int_8941 = _t1760
        self.consume_literal(")")
        _t1761 = logic_pb2.DateTimeValue(year=int(formatted_int935), month=int(formatted_int_3936), day=int(formatted_int_4937), hour=int(formatted_int_5938), minute=int(formatted_int_6939), second=int(formatted_int_7940), microsecond=int((formatted_int_8941 if formatted_int_8941 is not None else 0)))
        result943 = _t1761
        self.record_span(span_start942, "DateTimeValue")
        return result943

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start948 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs944 = []
        cond945 = self.match_lookahead_literal("(", 0)
        while cond945:
            _t1762 = self.parse_formula()
            item946 = _t1762
            xs944.append(item946)
            cond945 = self.match_lookahead_literal("(", 0)
        formulas947 = xs944
        self.consume_literal(")")
        _t1763 = logic_pb2.Conjunction(args=formulas947)
        result949 = _t1763
        self.record_span(span_start948, "Conjunction")
        return result949

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start954 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs950 = []
        cond951 = self.match_lookahead_literal("(", 0)
        while cond951:
            _t1764 = self.parse_formula()
            item952 = _t1764
            xs950.append(item952)
            cond951 = self.match_lookahead_literal("(", 0)
        formulas953 = xs950
        self.consume_literal(")")
        _t1765 = logic_pb2.Disjunction(args=formulas953)
        result955 = _t1765
        self.record_span(span_start954, "Disjunction")
        return result955

    def parse_not(self) -> logic_pb2.Not:
        span_start957 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1766 = self.parse_formula()
        formula956 = _t1766
        self.consume_literal(")")
        _t1767 = logic_pb2.Not(arg=formula956)
        result958 = _t1767
        self.record_span(span_start957, "Not")
        return result958

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start962 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1768 = self.parse_name()
        name959 = _t1768
        _t1769 = self.parse_ffi_args()
        ffi_args960 = _t1769
        _t1770 = self.parse_terms()
        terms961 = _t1770
        self.consume_literal(")")
        _t1771 = logic_pb2.FFI(name=name959, args=ffi_args960, terms=terms961)
        result963 = _t1771
        self.record_span(span_start962, "FFI")
        return result963

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol964 = self.consume_terminal("SYMBOL")
        return symbol964

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs965 = []
        cond966 = self.match_lookahead_literal("(", 0)
        while cond966:
            _t1772 = self.parse_abstraction()
            item967 = _t1772
            xs965.append(item967)
            cond966 = self.match_lookahead_literal("(", 0)
        abstractions968 = xs965
        self.consume_literal(")")
        return abstractions968

    def parse_atom(self) -> logic_pb2.Atom:
        span_start974 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1773 = self.parse_relation_id()
        relation_id969 = _t1773
        xs970 = []
        cond971 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond971:
            _t1774 = self.parse_term()
            item972 = _t1774
            xs970.append(item972)
            cond971 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms973 = xs970
        self.consume_literal(")")
        _t1775 = logic_pb2.Atom(name=relation_id969, terms=terms973)
        result975 = _t1775
        self.record_span(span_start974, "Atom")
        return result975

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start981 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1776 = self.parse_name()
        name976 = _t1776
        xs977 = []
        cond978 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond978:
            _t1777 = self.parse_term()
            item979 = _t1777
            xs977.append(item979)
            cond978 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms980 = xs977
        self.consume_literal(")")
        _t1778 = logic_pb2.Pragma(name=name976, terms=terms980)
        result982 = _t1778
        self.record_span(span_start981, "Pragma")
        return result982

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start998 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1780 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1781 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1782 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1783 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1784 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1785 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1786 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1787 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1788 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1789 = 7
                                                else:
                                                    _t1789 = -1
                                                _t1788 = _t1789
                                            _t1787 = _t1788
                                        _t1786 = _t1787
                                    _t1785 = _t1786
                                _t1784 = _t1785
                            _t1783 = _t1784
                        _t1782 = _t1783
                    _t1781 = _t1782
                _t1780 = _t1781
            _t1779 = _t1780
        else:
            _t1779 = -1
        prediction983 = _t1779
        if prediction983 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1791 = self.parse_name()
            name993 = _t1791
            xs994 = []
            cond995 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond995:
                _t1792 = self.parse_rel_term()
                item996 = _t1792
                xs994.append(item996)
                cond995 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms997 = xs994
            self.consume_literal(")")
            _t1793 = logic_pb2.Primitive(name=name993, terms=rel_terms997)
            _t1790 = _t1793
        else:
            if prediction983 == 8:
                _t1795 = self.parse_divide()
                divide992 = _t1795
                _t1794 = divide992
            else:
                if prediction983 == 7:
                    _t1797 = self.parse_multiply()
                    multiply991 = _t1797
                    _t1796 = multiply991
                else:
                    if prediction983 == 6:
                        _t1799 = self.parse_minus()
                        minus990 = _t1799
                        _t1798 = minus990
                    else:
                        if prediction983 == 5:
                            _t1801 = self.parse_add()
                            add989 = _t1801
                            _t1800 = add989
                        else:
                            if prediction983 == 4:
                                _t1803 = self.parse_gt_eq()
                                gt_eq988 = _t1803
                                _t1802 = gt_eq988
                            else:
                                if prediction983 == 3:
                                    _t1805 = self.parse_gt()
                                    gt987 = _t1805
                                    _t1804 = gt987
                                else:
                                    if prediction983 == 2:
                                        _t1807 = self.parse_lt_eq()
                                        lt_eq986 = _t1807
                                        _t1806 = lt_eq986
                                    else:
                                        if prediction983 == 1:
                                            _t1809 = self.parse_lt()
                                            lt985 = _t1809
                                            _t1808 = lt985
                                        else:
                                            if prediction983 == 0:
                                                _t1811 = self.parse_eq()
                                                eq984 = _t1811
                                                _t1810 = eq984
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1808 = _t1810
                                        _t1806 = _t1808
                                    _t1804 = _t1806
                                _t1802 = _t1804
                            _t1800 = _t1802
                        _t1798 = _t1800
                    _t1796 = _t1798
                _t1794 = _t1796
            _t1790 = _t1794
        result999 = _t1790
        self.record_span(span_start998, "Primitive")
        return result999

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start1002 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1812 = self.parse_term()
        term1000 = _t1812
        _t1813 = self.parse_term()
        term_31001 = _t1813
        self.consume_literal(")")
        _t1814 = logic_pb2.RelTerm(term=term1000)
        _t1815 = logic_pb2.RelTerm(term=term_31001)
        _t1816 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1814, _t1815])
        result1003 = _t1816
        self.record_span(span_start1002, "Primitive")
        return result1003

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start1006 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1817 = self.parse_term()
        term1004 = _t1817
        _t1818 = self.parse_term()
        term_31005 = _t1818
        self.consume_literal(")")
        _t1819 = logic_pb2.RelTerm(term=term1004)
        _t1820 = logic_pb2.RelTerm(term=term_31005)
        _t1821 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1819, _t1820])
        result1007 = _t1821
        self.record_span(span_start1006, "Primitive")
        return result1007

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start1010 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1822 = self.parse_term()
        term1008 = _t1822
        _t1823 = self.parse_term()
        term_31009 = _t1823
        self.consume_literal(")")
        _t1824 = logic_pb2.RelTerm(term=term1008)
        _t1825 = logic_pb2.RelTerm(term=term_31009)
        _t1826 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1824, _t1825])
        result1011 = _t1826
        self.record_span(span_start1010, "Primitive")
        return result1011

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start1014 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1827 = self.parse_term()
        term1012 = _t1827
        _t1828 = self.parse_term()
        term_31013 = _t1828
        self.consume_literal(")")
        _t1829 = logic_pb2.RelTerm(term=term1012)
        _t1830 = logic_pb2.RelTerm(term=term_31013)
        _t1831 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1829, _t1830])
        result1015 = _t1831
        self.record_span(span_start1014, "Primitive")
        return result1015

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start1018 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1832 = self.parse_term()
        term1016 = _t1832
        _t1833 = self.parse_term()
        term_31017 = _t1833
        self.consume_literal(")")
        _t1834 = logic_pb2.RelTerm(term=term1016)
        _t1835 = logic_pb2.RelTerm(term=term_31017)
        _t1836 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1834, _t1835])
        result1019 = _t1836
        self.record_span(span_start1018, "Primitive")
        return result1019

    def parse_add(self) -> logic_pb2.Primitive:
        span_start1023 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1837 = self.parse_term()
        term1020 = _t1837
        _t1838 = self.parse_term()
        term_31021 = _t1838
        _t1839 = self.parse_term()
        term_41022 = _t1839
        self.consume_literal(")")
        _t1840 = logic_pb2.RelTerm(term=term1020)
        _t1841 = logic_pb2.RelTerm(term=term_31021)
        _t1842 = logic_pb2.RelTerm(term=term_41022)
        _t1843 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1840, _t1841, _t1842])
        result1024 = _t1843
        self.record_span(span_start1023, "Primitive")
        return result1024

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start1028 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1844 = self.parse_term()
        term1025 = _t1844
        _t1845 = self.parse_term()
        term_31026 = _t1845
        _t1846 = self.parse_term()
        term_41027 = _t1846
        self.consume_literal(")")
        _t1847 = logic_pb2.RelTerm(term=term1025)
        _t1848 = logic_pb2.RelTerm(term=term_31026)
        _t1849 = logic_pb2.RelTerm(term=term_41027)
        _t1850 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1847, _t1848, _t1849])
        result1029 = _t1850
        self.record_span(span_start1028, "Primitive")
        return result1029

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start1033 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1851 = self.parse_term()
        term1030 = _t1851
        _t1852 = self.parse_term()
        term_31031 = _t1852
        _t1853 = self.parse_term()
        term_41032 = _t1853
        self.consume_literal(")")
        _t1854 = logic_pb2.RelTerm(term=term1030)
        _t1855 = logic_pb2.RelTerm(term=term_31031)
        _t1856 = logic_pb2.RelTerm(term=term_41032)
        _t1857 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1854, _t1855, _t1856])
        result1034 = _t1857
        self.record_span(span_start1033, "Primitive")
        return result1034

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start1038 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1858 = self.parse_term()
        term1035 = _t1858
        _t1859 = self.parse_term()
        term_31036 = _t1859
        _t1860 = self.parse_term()
        term_41037 = _t1860
        self.consume_literal(")")
        _t1861 = logic_pb2.RelTerm(term=term1035)
        _t1862 = logic_pb2.RelTerm(term=term_31036)
        _t1863 = logic_pb2.RelTerm(term=term_41037)
        _t1864 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1861, _t1862, _t1863])
        result1039 = _t1864
        self.record_span(span_start1038, "Primitive")
        return result1039

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1043 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1865 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1866 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1867 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1868 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1869 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1870 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1871 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1872 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1873 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1874 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1875 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1876 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1877 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1878 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1879 = 1
                                                                else:
                                                                    _t1879 = -1
                                                                _t1878 = _t1879
                                                            _t1877 = _t1878
                                                        _t1876 = _t1877
                                                    _t1875 = _t1876
                                                _t1874 = _t1875
                                            _t1873 = _t1874
                                        _t1872 = _t1873
                                    _t1871 = _t1872
                                _t1870 = _t1871
                            _t1869 = _t1870
                        _t1868 = _t1869
                    _t1867 = _t1868
                _t1866 = _t1867
            _t1865 = _t1866
        prediction1040 = _t1865
        if prediction1040 == 1:
            _t1881 = self.parse_term()
            term1042 = _t1881
            _t1882 = logic_pb2.RelTerm(term=term1042)
            _t1880 = _t1882
        else:
            if prediction1040 == 0:
                _t1884 = self.parse_specialized_value()
                specialized_value1041 = _t1884
                _t1885 = logic_pb2.RelTerm(specialized_value=specialized_value1041)
                _t1883 = _t1885
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1880 = _t1883
        result1044 = _t1880
        self.record_span(span_start1043, "RelTerm")
        return result1044

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1046 = self.span_start()
        self.consume_literal("#")
        _t1886 = self.parse_raw_value()
        raw_value1045 = _t1886
        result1047 = raw_value1045
        self.record_span(span_start1046, "Value")
        return result1047

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1053 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1887 = self.parse_name()
        name1048 = _t1887
        xs1049 = []
        cond1050 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1050:
            _t1888 = self.parse_rel_term()
            item1051 = _t1888
            xs1049.append(item1051)
            cond1050 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1052 = xs1049
        self.consume_literal(")")
        _t1889 = logic_pb2.RelAtom(name=name1048, terms=rel_terms1052)
        result1054 = _t1889
        self.record_span(span_start1053, "RelAtom")
        return result1054

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1057 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1890 = self.parse_term()
        term1055 = _t1890
        _t1891 = self.parse_term()
        term_31056 = _t1891
        self.consume_literal(")")
        _t1892 = logic_pb2.Cast(input=term1055, result=term_31056)
        result1058 = _t1892
        self.record_span(span_start1057, "Cast")
        return result1058

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1059 = []
        cond1060 = self.match_lookahead_literal("(", 0)
        while cond1060:
            _t1893 = self.parse_attribute()
            item1061 = _t1893
            xs1059.append(item1061)
            cond1060 = self.match_lookahead_literal("(", 0)
        attributes1062 = xs1059
        self.consume_literal(")")
        return attributes1062

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1068 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1894 = self.parse_name()
        name1063 = _t1894
        xs1064 = []
        cond1065 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1065:
            _t1895 = self.parse_raw_value()
            item1066 = _t1895
            xs1064.append(item1066)
            cond1065 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1067 = xs1064
        self.consume_literal(")")
        _t1896 = logic_pb2.Attribute(name=name1063, args=raw_values1067)
        result1069 = _t1896
        self.record_span(span_start1068, "Attribute")
        return result1069

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1076 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1070 = []
        cond1071 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1071:
            _t1897 = self.parse_relation_id()
            item1072 = _t1897
            xs1070.append(item1072)
            cond1071 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1073 = xs1070
        _t1898 = self.parse_script()
        script1074 = _t1898
        if self.match_lookahead_literal("(", 0):
            _t1900 = self.parse_attrs()
            _t1899 = _t1900
        else:
            _t1899 = None
        attrs1075 = _t1899
        self.consume_literal(")")
        _t1901 = logic_pb2.Algorithm(body=script1074, attrs=(attrs1075 if attrs1075 is not None else []))
        getattr(_t1901, 'global').extend(relation_ids1073)
        result1077 = _t1901
        self.record_span(span_start1076, "Algorithm")
        return result1077

    def parse_script(self) -> logic_pb2.Script:
        span_start1082 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1078 = []
        cond1079 = self.match_lookahead_literal("(", 0)
        while cond1079:
            _t1902 = self.parse_construct()
            item1080 = _t1902
            xs1078.append(item1080)
            cond1079 = self.match_lookahead_literal("(", 0)
        constructs1081 = xs1078
        self.consume_literal(")")
        _t1903 = logic_pb2.Script(constructs=constructs1081)
        result1083 = _t1903
        self.record_span(span_start1082, "Script")
        return result1083

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1087 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1905 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1906 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1907 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1908 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1909 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1910 = 1
                                else:
                                    _t1910 = -1
                                _t1909 = _t1910
                            _t1908 = _t1909
                        _t1907 = _t1908
                    _t1906 = _t1907
                _t1905 = _t1906
            _t1904 = _t1905
        else:
            _t1904 = -1
        prediction1084 = _t1904
        if prediction1084 == 1:
            _t1912 = self.parse_instruction()
            instruction1086 = _t1912
            _t1913 = logic_pb2.Construct(instruction=instruction1086)
            _t1911 = _t1913
        else:
            if prediction1084 == 0:
                _t1915 = self.parse_loop()
                loop1085 = _t1915
                _t1916 = logic_pb2.Construct(loop=loop1085)
                _t1914 = _t1916
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1911 = _t1914
        result1088 = _t1911
        self.record_span(span_start1087, "Construct")
        return result1088

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1092 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1917 = self.parse_init()
        init1089 = _t1917
        _t1918 = self.parse_script()
        script1090 = _t1918
        if self.match_lookahead_literal("(", 0):
            _t1920 = self.parse_attrs()
            _t1919 = _t1920
        else:
            _t1919 = None
        attrs1091 = _t1919
        self.consume_literal(")")
        _t1921 = logic_pb2.Loop(init=init1089, body=script1090, attrs=(attrs1091 if attrs1091 is not None else []))
        result1093 = _t1921
        self.record_span(span_start1092, "Loop")
        return result1093

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1094 = []
        cond1095 = self.match_lookahead_literal("(", 0)
        while cond1095:
            _t1922 = self.parse_instruction()
            item1096 = _t1922
            xs1094.append(item1096)
            cond1095 = self.match_lookahead_literal("(", 0)
        instructions1097 = xs1094
        self.consume_literal(")")
        return instructions1097

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1104 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1924 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1925 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1926 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1927 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1928 = 0
                            else:
                                _t1928 = -1
                            _t1927 = _t1928
                        _t1926 = _t1927
                    _t1925 = _t1926
                _t1924 = _t1925
            _t1923 = _t1924
        else:
            _t1923 = -1
        prediction1098 = _t1923
        if prediction1098 == 4:
            _t1930 = self.parse_monus_def()
            monus_def1103 = _t1930
            _t1931 = logic_pb2.Instruction(monus_def=monus_def1103)
            _t1929 = _t1931
        else:
            if prediction1098 == 3:
                _t1933 = self.parse_monoid_def()
                monoid_def1102 = _t1933
                _t1934 = logic_pb2.Instruction(monoid_def=monoid_def1102)
                _t1932 = _t1934
            else:
                if prediction1098 == 2:
                    _t1936 = self.parse_break()
                    break1101 = _t1936
                    _t1937 = logic_pb2.Instruction()
                    getattr(_t1937, 'break').CopyFrom(break1101)
                    _t1935 = _t1937
                else:
                    if prediction1098 == 1:
                        _t1939 = self.parse_upsert()
                        upsert1100 = _t1939
                        _t1940 = logic_pb2.Instruction(upsert=upsert1100)
                        _t1938 = _t1940
                    else:
                        if prediction1098 == 0:
                            _t1942 = self.parse_assign()
                            assign1099 = _t1942
                            _t1943 = logic_pb2.Instruction(assign=assign1099)
                            _t1941 = _t1943
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1938 = _t1941
                    _t1935 = _t1938
                _t1932 = _t1935
            _t1929 = _t1932
        result1105 = _t1929
        self.record_span(span_start1104, "Instruction")
        return result1105

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1109 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1944 = self.parse_relation_id()
        relation_id1106 = _t1944
        _t1945 = self.parse_abstraction()
        abstraction1107 = _t1945
        if self.match_lookahead_literal("(", 0):
            _t1947 = self.parse_attrs()
            _t1946 = _t1947
        else:
            _t1946 = None
        attrs1108 = _t1946
        self.consume_literal(")")
        _t1948 = logic_pb2.Assign(name=relation_id1106, body=abstraction1107, attrs=(attrs1108 if attrs1108 is not None else []))
        result1110 = _t1948
        self.record_span(span_start1109, "Assign")
        return result1110

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1114 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1949 = self.parse_relation_id()
        relation_id1111 = _t1949
        _t1950 = self.parse_abstraction_with_arity()
        abstraction_with_arity1112 = _t1950
        if self.match_lookahead_literal("(", 0):
            _t1952 = self.parse_attrs()
            _t1951 = _t1952
        else:
            _t1951 = None
        attrs1113 = _t1951
        self.consume_literal(")")
        _t1953 = logic_pb2.Upsert(name=relation_id1111, body=abstraction_with_arity1112[0], attrs=(attrs1113 if attrs1113 is not None else []), value_arity=abstraction_with_arity1112[1])
        result1115 = _t1953
        self.record_span(span_start1114, "Upsert")
        return result1115

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1954 = self.parse_bindings()
        bindings1116 = _t1954
        _t1955 = self.parse_formula()
        formula1117 = _t1955
        self.consume_literal(")")
        _t1956 = logic_pb2.Abstraction(vars=(list(bindings1116[0]) + list(bindings1116[1] if bindings1116[1] is not None else [])), value=formula1117)
        return (_t1956, len(bindings1116[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1121 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1957 = self.parse_relation_id()
        relation_id1118 = _t1957
        _t1958 = self.parse_abstraction()
        abstraction1119 = _t1958
        if self.match_lookahead_literal("(", 0):
            _t1960 = self.parse_attrs()
            _t1959 = _t1960
        else:
            _t1959 = None
        attrs1120 = _t1959
        self.consume_literal(")")
        _t1961 = logic_pb2.Break(name=relation_id1118, body=abstraction1119, attrs=(attrs1120 if attrs1120 is not None else []))
        result1122 = _t1961
        self.record_span(span_start1121, "Break")
        return result1122

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1127 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1962 = self.parse_monoid()
        monoid1123 = _t1962
        _t1963 = self.parse_relation_id()
        relation_id1124 = _t1963
        _t1964 = self.parse_abstraction_with_arity()
        abstraction_with_arity1125 = _t1964
        if self.match_lookahead_literal("(", 0):
            _t1966 = self.parse_attrs()
            _t1965 = _t1966
        else:
            _t1965 = None
        attrs1126 = _t1965
        self.consume_literal(")")
        _t1967 = logic_pb2.MonoidDef(monoid=monoid1123, name=relation_id1124, body=abstraction_with_arity1125[0], attrs=(attrs1126 if attrs1126 is not None else []), value_arity=abstraction_with_arity1125[1])
        result1128 = _t1967
        self.record_span(span_start1127, "MonoidDef")
        return result1128

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1134 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1969 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1970 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1971 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1972 = 2
                        else:
                            _t1972 = -1
                        _t1971 = _t1972
                    _t1970 = _t1971
                _t1969 = _t1970
            _t1968 = _t1969
        else:
            _t1968 = -1
        prediction1129 = _t1968
        if prediction1129 == 3:
            _t1974 = self.parse_sum_monoid()
            sum_monoid1133 = _t1974
            _t1975 = logic_pb2.Monoid(sum_monoid=sum_monoid1133)
            _t1973 = _t1975
        else:
            if prediction1129 == 2:
                _t1977 = self.parse_max_monoid()
                max_monoid1132 = _t1977
                _t1978 = logic_pb2.Monoid(max_monoid=max_monoid1132)
                _t1976 = _t1978
            else:
                if prediction1129 == 1:
                    _t1980 = self.parse_min_monoid()
                    min_monoid1131 = _t1980
                    _t1981 = logic_pb2.Monoid(min_monoid=min_monoid1131)
                    _t1979 = _t1981
                else:
                    if prediction1129 == 0:
                        _t1983 = self.parse_or_monoid()
                        or_monoid1130 = _t1983
                        _t1984 = logic_pb2.Monoid(or_monoid=or_monoid1130)
                        _t1982 = _t1984
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1979 = _t1982
                _t1976 = _t1979
            _t1973 = _t1976
        result1135 = _t1973
        self.record_span(span_start1134, "Monoid")
        return result1135

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1136 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1985 = logic_pb2.OrMonoid()
        result1137 = _t1985
        self.record_span(span_start1136, "OrMonoid")
        return result1137

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1139 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1986 = self.parse_type()
        type1138 = _t1986
        self.consume_literal(")")
        _t1987 = logic_pb2.MinMonoid(type=type1138)
        result1140 = _t1987
        self.record_span(span_start1139, "MinMonoid")
        return result1140

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1142 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1988 = self.parse_type()
        type1141 = _t1988
        self.consume_literal(")")
        _t1989 = logic_pb2.MaxMonoid(type=type1141)
        result1143 = _t1989
        self.record_span(span_start1142, "MaxMonoid")
        return result1143

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1145 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1990 = self.parse_type()
        type1144 = _t1990
        self.consume_literal(")")
        _t1991 = logic_pb2.SumMonoid(type=type1144)
        result1146 = _t1991
        self.record_span(span_start1145, "SumMonoid")
        return result1146

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1151 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1992 = self.parse_monoid()
        monoid1147 = _t1992
        _t1993 = self.parse_relation_id()
        relation_id1148 = _t1993
        _t1994 = self.parse_abstraction_with_arity()
        abstraction_with_arity1149 = _t1994
        if self.match_lookahead_literal("(", 0):
            _t1996 = self.parse_attrs()
            _t1995 = _t1996
        else:
            _t1995 = None
        attrs1150 = _t1995
        self.consume_literal(")")
        _t1997 = logic_pb2.MonusDef(monoid=monoid1147, name=relation_id1148, body=abstraction_with_arity1149[0], attrs=(attrs1150 if attrs1150 is not None else []), value_arity=abstraction_with_arity1149[1])
        result1152 = _t1997
        self.record_span(span_start1151, "MonusDef")
        return result1152

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1157 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1998 = self.parse_relation_id()
        relation_id1153 = _t1998
        _t1999 = self.parse_abstraction()
        abstraction1154 = _t1999
        _t2000 = self.parse_functional_dependency_keys()
        functional_dependency_keys1155 = _t2000
        _t2001 = self.parse_functional_dependency_values()
        functional_dependency_values1156 = _t2001
        self.consume_literal(")")
        _t2002 = logic_pb2.FunctionalDependency(guard=abstraction1154, keys=functional_dependency_keys1155, values=functional_dependency_values1156)
        _t2003 = logic_pb2.Constraint(name=relation_id1153, functional_dependency=_t2002)
        result1158 = _t2003
        self.record_span(span_start1157, "Constraint")
        return result1158

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1159 = []
        cond1160 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1160:
            _t2004 = self.parse_var()
            item1161 = _t2004
            xs1159.append(item1161)
            cond1160 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1162 = xs1159
        self.consume_literal(")")
        return vars1162

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1163 = []
        cond1164 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1164:
            _t2005 = self.parse_var()
            item1165 = _t2005
            xs1163.append(item1165)
            cond1164 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1166 = xs1163
        self.consume_literal(")")
        return vars1166

    def parse_data(self) -> logic_pb2.Data:
        span_start1172 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t2007 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t2008 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t2009 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t2010 = 1
                        else:
                            _t2010 = -1
                        _t2009 = _t2010
                    _t2008 = _t2009
                _t2007 = _t2008
            _t2006 = _t2007
        else:
            _t2006 = -1
        prediction1167 = _t2006
        if prediction1167 == 3:
            _t2012 = self.parse_iceberg_data()
            iceberg_data1171 = _t2012
            _t2013 = logic_pb2.Data(iceberg_data=iceberg_data1171)
            _t2011 = _t2013
        else:
            if prediction1167 == 2:
                _t2015 = self.parse_csv_data()
                csv_data1170 = _t2015
                _t2016 = logic_pb2.Data(csv_data=csv_data1170)
                _t2014 = _t2016
            else:
                if prediction1167 == 1:
                    _t2018 = self.parse_betree_relation()
                    betree_relation1169 = _t2018
                    _t2019 = logic_pb2.Data(betree_relation=betree_relation1169)
                    _t2017 = _t2019
                else:
                    if prediction1167 == 0:
                        _t2021 = self.parse_edb()
                        edb1168 = _t2021
                        _t2022 = logic_pb2.Data(edb=edb1168)
                        _t2020 = _t2022
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t2017 = _t2020
                _t2014 = _t2017
            _t2011 = _t2014
        result1173 = _t2011
        self.record_span(span_start1172, "Data")
        return result1173

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1177 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t2023 = self.parse_relation_id()
        relation_id1174 = _t2023
        _t2024 = self.parse_edb_path()
        edb_path1175 = _t2024
        _t2025 = self.parse_edb_types()
        edb_types1176 = _t2025
        self.consume_literal(")")
        _t2026 = logic_pb2.EDB(target_id=relation_id1174, path=edb_path1175, types=edb_types1176)
        result1178 = _t2026
        self.record_span(span_start1177, "EDB")
        return result1178

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1179 = []
        cond1180 = self.match_lookahead_terminal("STRING", 0)
        while cond1180:
            item1181 = self.consume_terminal("STRING")
            xs1179.append(item1181)
            cond1180 = self.match_lookahead_terminal("STRING", 0)
        strings1182 = xs1179
        self.consume_literal("]")
        return strings1182

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1183 = []
        cond1184 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1184:
            _t2027 = self.parse_type()
            item1185 = _t2027
            xs1183.append(item1185)
            cond1184 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1186 = xs1183
        self.consume_literal("]")
        return types1186

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1189 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t2028 = self.parse_relation_id()
        relation_id1187 = _t2028
        _t2029 = self.parse_betree_info()
        betree_info1188 = _t2029
        self.consume_literal(")")
        _t2030 = logic_pb2.BeTreeRelation(name=relation_id1187, relation_info=betree_info1188)
        result1190 = _t2030
        self.record_span(span_start1189, "BeTreeRelation")
        return result1190

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1194 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t2031 = self.parse_betree_info_key_types()
        betree_info_key_types1191 = _t2031
        _t2032 = self.parse_betree_info_value_types()
        betree_info_value_types1192 = _t2032
        _t2033 = self.parse_config_dict()
        config_dict1193 = _t2033
        self.consume_literal(")")
        _t2034 = self.construct_betree_info(betree_info_key_types1191, betree_info_value_types1192, config_dict1193)
        result1195 = _t2034
        self.record_span(span_start1194, "BeTreeInfo")
        return result1195

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1196 = []
        cond1197 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1197:
            _t2035 = self.parse_type()
            item1198 = _t2035
            xs1196.append(item1198)
            cond1197 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1199 = xs1196
        self.consume_literal(")")
        return types1199

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1200 = []
        cond1201 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1201:
            _t2036 = self.parse_type()
            item1202 = _t2036
            xs1200.append(item1202)
            cond1201 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1203 = xs1200
        self.consume_literal(")")
        return types1203

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1209 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t2037 = self.parse_csvlocator()
        csvlocator1204 = _t2037
        _t2038 = self.parse_csv_config()
        csv_config1205 = _t2038
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("columns", 1)):
            _t2040 = self.parse_gnf_columns()
            _t2039 = _t2040
        else:
            _t2039 = None
        gnf_columns1206 = _t2039
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("relations", 1)):
            _t2042 = self.parse_target_relations()
            _t2041 = _t2042
        else:
            _t2041 = None
        target_relations1207 = _t2041
        _t2043 = self.parse_csv_asof()
        csv_asof1208 = _t2043
        self.consume_literal(")")
        _t2044 = self.construct_csv_data(csvlocator1204, csv_config1205, gnf_columns1206, target_relations1207, csv_asof1208)
        result1210 = _t2044
        self.record_span(span_start1209, "CSVData")
        return result1210

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1213 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t2046 = self.parse_csv_locator_paths()
            _t2045 = _t2046
        else:
            _t2045 = None
        csv_locator_paths1211 = _t2045
        if self.match_lookahead_literal("(", 0):
            _t2048 = self.parse_csv_locator_inline_data()
            _t2047 = _t2048
        else:
            _t2047 = None
        csv_locator_inline_data1212 = _t2047
        self.consume_literal(")")
        _t2049 = logic_pb2.CSVLocator(paths=(csv_locator_paths1211 if csv_locator_paths1211 is not None else []), inline_data=(csv_locator_inline_data1212 if csv_locator_inline_data1212 is not None else "").encode())
        result1214 = _t2049
        self.record_span(span_start1213, "CSVLocator")
        return result1214

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1215 = []
        cond1216 = self.match_lookahead_terminal("STRING", 0)
        while cond1216:
            item1217 = self.consume_terminal("STRING")
            xs1215.append(item1217)
            cond1216 = self.match_lookahead_terminal("STRING", 0)
        strings1218 = xs1215
        self.consume_literal(")")
        return strings1218

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        formatted_string1219 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return formatted_string1219

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1222 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t2050 = self.parse_config_dict()
        config_dict1220 = _t2050
        if self.match_lookahead_literal("(", 0):
            _t2052 = self.parse__storage_integration()
            _t2051 = _t2052
        else:
            _t2051 = None
        _storage_integration1221 = _t2051
        self.consume_literal(")")
        _t2053 = self.construct_csv_config(config_dict1220, _storage_integration1221)
        result1223 = _t2053
        self.record_span(span_start1222, "CSVConfig")
        return result1223

    def parse__storage_integration(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("(")
        self.consume_literal("storage_integration")
        _t2054 = self.parse_config_dict()
        config_dict1224 = _t2054
        self.consume_literal(")")
        return config_dict1224

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1225 = []
        cond1226 = self.match_lookahead_literal("(", 0)
        while cond1226:
            _t2055 = self.parse_gnf_column()
            item1227 = _t2055
            xs1225.append(item1227)
            cond1226 = self.match_lookahead_literal("(", 0)
        gnf_columns1228 = xs1225
        self.consume_literal(")")
        return gnf_columns1228

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1235 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t2056 = self.parse_gnf_column_path()
        gnf_column_path1229 = _t2056
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t2058 = self.parse_relation_id()
            _t2057 = _t2058
        else:
            _t2057 = None
        relation_id1230 = _t2057
        self.consume_literal("[")
        xs1231 = []
        cond1232 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1232:
            _t2059 = self.parse_type()
            item1233 = _t2059
            xs1231.append(item1233)
            cond1232 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1234 = xs1231
        self.consume_literal("]")
        self.consume_literal(")")
        _t2060 = logic_pb2.GNFColumn(column_path=gnf_column_path1229, target_id=relation_id1230, types=types1234)
        result1236 = _t2060
        self.record_span(span_start1235, "GNFColumn")
        return result1236

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t2061 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t2062 = 0
            else:
                _t2062 = -1
            _t2061 = _t2062
        prediction1237 = _t2061
        if prediction1237 == 1:
            self.consume_literal("[")
            xs1239 = []
            cond1240 = self.match_lookahead_terminal("STRING", 0)
            while cond1240:
                item1241 = self.consume_terminal("STRING")
                xs1239.append(item1241)
                cond1240 = self.match_lookahead_terminal("STRING", 0)
            strings1242 = xs1239
            self.consume_literal("]")
            _t2063 = strings1242
        else:
            if prediction1237 == 0:
                string1238 = self.consume_terminal("STRING")
                _t2064 = [string1238]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2063 = _t2064
        return _t2063

    def parse_target_relations(self) -> logic_pb2.TargetRelations:
        span_start1245 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relations")
        _t2065 = self.parse_relation_keys()
        relation_keys1243 = _t2065
        _t2066 = self.parse_relation_body()
        relation_body1244 = _t2066
        self.consume_literal(")")
        _t2067 = self.construct_relations(relation_keys1243, relation_body1244)
        result1246 = _t2067
        self.record_span(span_start1245, "TargetRelations")
        return result1246

    def parse_relation_keys(self) -> tuple[Sequence[logic_pb2.NamedColumn], bool]:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("keys", 1):
                if self.match_lookahead_literal(":", 2):
                    _t2070 = 1
                else:
                    if self.match_lookahead_literal(")", 2):
                        _t2071 = 0
                    else:
                        if self.match_lookahead_literal("(", 2):
                            _t2072 = 0
                        else:
                            _t2072 = -1
                        _t2071 = _t2072
                    _t2070 = _t2071
                _t2069 = _t2070
            else:
                _t2069 = -1
            _t2068 = _t2069
        else:
            _t2068 = -1
        prediction1247 = _t2068
        if prediction1247 == 1:
            self.consume_literal("(")
            self.consume_literal("keys")
            self.consume_literal(":")
            symbol1252 = self.consume_terminal("SYMBOL")
            self.consume_literal(")")
            _t2074 = self.construct_synthetic_keys(symbol1252)
            _t2073 = _t2074
        else:
            if prediction1247 == 0:
                self.consume_literal("(")
                self.consume_literal("keys")
                xs1248 = []
                cond1249 = self.match_lookahead_literal("(", 0)
                while cond1249:
                    _t2076 = self.parse_named_column()
                    item1250 = _t2076
                    xs1248.append(item1250)
                    cond1249 = self.match_lookahead_literal("(", 0)
                named_columns1251 = xs1248
                self.consume_literal(")")
                _t2075 = (named_columns1251, False,)
            else:
                raise ParseError("Unexpected token in relation_keys" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2073 = _t2075
        return _t2073

    def parse_named_column(self) -> logic_pb2.NamedColumn:
        span_start1255 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1253 = self.consume_terminal("STRING")
        _t2077 = self.parse_type()
        type1254 = _t2077
        self.consume_literal(")")
        _t2078 = logic_pb2.NamedColumn(name=string1253, type=type1254)
        result1256 = _t2078
        self.record_span(span_start1255, "NamedColumn")
        return result1256

    def parse_relation_body(self) -> logic_pb2.TargetRelations:
        span_start1261 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("relation", 1):
                _t2080 = 0
            else:
                if self.match_lookahead_literal("inserts", 1):
                    _t2081 = 1
                else:
                    _t2081 = 0
                _t2080 = _t2081
            _t2079 = _t2080
        else:
            _t2079 = 0
        prediction1257 = _t2079
        if prediction1257 == 1:
            _t2083 = self.parse_cdc_inserts()
            cdc_inserts1259 = _t2083
            _t2084 = self.parse_cdc_deletes()
            cdc_deletes1260 = _t2084
            _t2085 = self.construct_cdc_relations(cdc_inserts1259, cdc_deletes1260)
            _t2082 = _t2085
        else:
            if prediction1257 == 0:
                _t2087 = self.parse_non_cdc_relations()
                non_cdc_relations1258 = _t2087
                _t2088 = self.construct_non_cdc_relations(non_cdc_relations1258)
                _t2086 = _t2088
            else:
                raise ParseError("Unexpected token in relation_body" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2082 = _t2086
        result1262 = _t2082
        self.record_span(span_start1261, "TargetRelations")
        return result1262

    def parse_non_cdc_relations(self) -> Sequence[logic_pb2.TargetRelation]:
        xs1263 = []
        cond1264 = self.match_lookahead_literal("(", 0)
        while cond1264:
            _t2089 = self.parse_target_relation()
            item1265 = _t2089
            xs1263.append(item1265)
            cond1264 = self.match_lookahead_literal("(", 0)
        return xs1263

    def parse_target_relation(self) -> logic_pb2.TargetRelation:
        span_start1271 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relation")
        _t2090 = self.parse_relation_id()
        relation_id1266 = _t2090
        xs1267 = []
        cond1268 = self.match_lookahead_literal("(", 0)
        while cond1268:
            _t2091 = self.parse_named_column()
            item1269 = _t2091
            xs1267.append(item1269)
            cond1268 = self.match_lookahead_literal("(", 0)
        named_columns1270 = xs1267
        self.consume_literal(")")
        _t2092 = logic_pb2.TargetRelation(target_id=relation_id1266, values=named_columns1270)
        result1272 = _t2092
        self.record_span(span_start1271, "TargetRelation")
        return result1272

    def parse_cdc_inserts(self) -> Sequence[logic_pb2.TargetRelation]:
        self.consume_literal("(")
        self.consume_literal("inserts")
        xs1273 = []
        cond1274 = self.match_lookahead_literal("(", 0)
        while cond1274:
            _t2093 = self.parse_target_relation()
            item1275 = _t2093
            xs1273.append(item1275)
            cond1274 = self.match_lookahead_literal("(", 0)
        target_relations1276 = xs1273
        self.consume_literal(")")
        return target_relations1276

    def parse_cdc_deletes(self) -> Sequence[logic_pb2.TargetRelation]:
        self.consume_literal("(")
        self.consume_literal("deletes")
        xs1277 = []
        cond1278 = self.match_lookahead_literal("(", 0)
        while cond1278:
            _t2094 = self.parse_target_relation()
            item1279 = _t2094
            xs1277.append(item1279)
            cond1278 = self.match_lookahead_literal("(", 0)
        target_relations1280 = xs1277
        self.consume_literal(")")
        return target_relations1280

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1281 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1281

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1288 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t2095 = self.parse_iceberg_locator()
        iceberg_locator1282 = _t2095
        _t2096 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1283 = _t2096
        _t2097 = self.parse_gnf_columns()
        gnf_columns1284 = _t2097
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t2099 = self.parse_iceberg_from_snapshot()
            _t2098 = _t2099
        else:
            _t2098 = None
        iceberg_from_snapshot1285 = _t2098
        if self.match_lookahead_literal("(", 0):
            _t2101 = self.parse_iceberg_to_snapshot()
            _t2100 = _t2101
        else:
            _t2100 = None
        iceberg_to_snapshot1286 = _t2100
        _t2102 = self.parse_boolean_value()
        boolean_value1287 = _t2102
        self.consume_literal(")")
        _t2103 = self.construct_iceberg_data(iceberg_locator1282, iceberg_catalog_config1283, gnf_columns1284, iceberg_from_snapshot1285, iceberg_to_snapshot1286, boolean_value1287)
        result1289 = _t2103
        self.record_span(span_start1288, "IcebergData")
        return result1289

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1293 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t2104 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1290 = _t2104
        _t2105 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1291 = _t2105
        _t2106 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1292 = _t2106
        self.consume_literal(")")
        _t2107 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1290, namespace=iceberg_locator_namespace1291, warehouse=iceberg_locator_warehouse1292)
        result1294 = _t2107
        self.record_span(span_start1293, "IcebergLocator")
        return result1294

    def parse_iceberg_locator_table_name(self) -> str:
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1295 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1295

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1296 = []
        cond1297 = self.match_lookahead_terminal("STRING", 0)
        while cond1297:
            item1298 = self.consume_terminal("STRING")
            xs1296.append(item1298)
            cond1297 = self.match_lookahead_terminal("STRING", 0)
        strings1299 = xs1296
        self.consume_literal(")")
        return strings1299

    def parse_iceberg_locator_warehouse(self) -> str:
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string1300 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1300

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1305 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t2108 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1301 = _t2108
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t2110 = self.parse_iceberg_catalog_config_scope()
            _t2109 = _t2110
        else:
            _t2109 = None
        iceberg_catalog_config_scope1302 = _t2109
        _t2111 = self.parse_iceberg_properties()
        iceberg_properties1303 = _t2111
        _t2112 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1304 = _t2112
        self.consume_literal(")")
        _t2113 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1301, iceberg_catalog_config_scope1302, iceberg_properties1303, iceberg_auth_properties1304)
        result1306 = _t2113
        self.record_span(span_start1305, "IcebergCatalogConfig")
        return result1306

    def parse_iceberg_catalog_uri(self) -> str:
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1307 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1307

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1308 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1308

    def parse_iceberg_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1309 = []
        cond1310 = self.match_lookahead_literal("(", 0)
        while cond1310:
            _t2114 = self.parse_iceberg_property_entry()
            item1311 = _t2114
            xs1309.append(item1311)
            cond1310 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1312 = xs1309
        self.consume_literal(")")
        return iceberg_property_entrys1312

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1313 = self.consume_terminal("STRING")
        string_31314 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1313, string_31314,)

    def parse_iceberg_auth_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1315 = []
        cond1316 = self.match_lookahead_literal("(", 0)
        while cond1316:
            _t2115 = self.parse_iceberg_masked_property_entry()
            item1317 = _t2115
            xs1315.append(item1317)
            cond1316 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1318 = xs1315
        self.consume_literal(")")
        return iceberg_masked_property_entrys1318

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1319 = self.consume_terminal("STRING")
        string_31320 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1319, string_31320,)

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1321 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1321

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1322 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1322

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1324 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2116 = self.parse_fragment_id()
        fragment_id1323 = _t2116
        self.consume_literal(")")
        _t2117 = transactions_pb2.Undefine(fragment_id=fragment_id1323)
        result1325 = _t2117
        self.record_span(span_start1324, "Undefine")
        return result1325

    def parse_context(self) -> transactions_pb2.Context:
        span_start1330 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1326 = []
        cond1327 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1327:
            _t2118 = self.parse_relation_id()
            item1328 = _t2118
            xs1326.append(item1328)
            cond1327 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1329 = xs1326
        self.consume_literal(")")
        _t2119 = transactions_pb2.Context(relations=relation_ids1329)
        result1331 = _t2119
        self.record_span(span_start1330, "Context")
        return result1331

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1337 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t2120 = self.parse_edb_path()
        edb_path1332 = _t2120
        xs1333 = []
        cond1334 = self.match_lookahead_literal("[", 0)
        while cond1334:
            _t2121 = self.parse_snapshot_mapping()
            item1335 = _t2121
            xs1333.append(item1335)
            cond1334 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1336 = xs1333
        self.consume_literal(")")
        _t2122 = transactions_pb2.Snapshot(prefix=edb_path1332, mappings=snapshot_mappings1336)
        result1338 = _t2122
        self.record_span(span_start1337, "Snapshot")
        return result1338

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1341 = self.span_start()
        _t2123 = self.parse_edb_path()
        edb_path1339 = _t2123
        _t2124 = self.parse_relation_id()
        relation_id1340 = _t2124
        _t2125 = transactions_pb2.SnapshotMapping(destination_path=edb_path1339, source_relation=relation_id1340)
        result1342 = _t2125
        self.record_span(span_start1341, "SnapshotMapping")
        return result1342

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1343 = []
        cond1344 = self.match_lookahead_literal("(", 0)
        while cond1344:
            _t2126 = self.parse_read()
            item1345 = _t2126
            xs1343.append(item1345)
            cond1344 = self.match_lookahead_literal("(", 0)
        reads1346 = xs1343
        self.consume_literal(")")
        return reads1346

    def parse_read(self) -> transactions_pb2.Read:
        span_start1353 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2128 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2129 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t2130 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t2131 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t2132 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t2133 = 3
                                else:
                                    _t2133 = -1
                                _t2132 = _t2133
                            _t2131 = _t2132
                        _t2130 = _t2131
                    _t2129 = _t2130
                _t2128 = _t2129
            _t2127 = _t2128
        else:
            _t2127 = -1
        prediction1347 = _t2127
        if prediction1347 == 4:
            _t2135 = self.parse_export()
            export1352 = _t2135
            _t2136 = transactions_pb2.Read(export=export1352)
            _t2134 = _t2136
        else:
            if prediction1347 == 3:
                _t2138 = self.parse_abort()
                abort1351 = _t2138
                _t2139 = transactions_pb2.Read(abort=abort1351)
                _t2137 = _t2139
            else:
                if prediction1347 == 2:
                    _t2141 = self.parse_what_if()
                    what_if1350 = _t2141
                    _t2142 = transactions_pb2.Read(what_if=what_if1350)
                    _t2140 = _t2142
                else:
                    if prediction1347 == 1:
                        _t2144 = self.parse_output()
                        output1349 = _t2144
                        _t2145 = transactions_pb2.Read(output=output1349)
                        _t2143 = _t2145
                    else:
                        if prediction1347 == 0:
                            _t2147 = self.parse_demand()
                            demand1348 = _t2147
                            _t2148 = transactions_pb2.Read(demand=demand1348)
                            _t2146 = _t2148
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2143 = _t2146
                    _t2140 = _t2143
                _t2137 = _t2140
            _t2134 = _t2137
        result1354 = _t2134
        self.record_span(span_start1353, "Read")
        return result1354

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1356 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2149 = self.parse_relation_id()
        relation_id1355 = _t2149
        self.consume_literal(")")
        _t2150 = transactions_pb2.Demand(relation_id=relation_id1355)
        result1357 = _t2150
        self.record_span(span_start1356, "Demand")
        return result1357

    def parse_output(self) -> transactions_pb2.Output:
        span_start1360 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2151 = self.parse_name()
        name1358 = _t2151
        _t2152 = self.parse_relation_id()
        relation_id1359 = _t2152
        self.consume_literal(")")
        _t2153 = transactions_pb2.Output(name=name1358, relation_id=relation_id1359)
        result1361 = _t2153
        self.record_span(span_start1360, "Output")
        return result1361

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1364 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2154 = self.parse_name()
        name1362 = _t2154
        _t2155 = self.parse_epoch()
        epoch1363 = _t2155
        self.consume_literal(")")
        _t2156 = transactions_pb2.WhatIf(branch=name1362, epoch=epoch1363)
        result1365 = _t2156
        self.record_span(span_start1364, "WhatIf")
        return result1365

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1368 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2158 = self.parse_name()
            _t2157 = _t2158
        else:
            _t2157 = None
        name1366 = _t2157
        _t2159 = self.parse_relation_id()
        relation_id1367 = _t2159
        self.consume_literal(")")
        _t2160 = transactions_pb2.Abort(name=(name1366 if name1366 is not None else "abort"), relation_id=relation_id1367)
        result1369 = _t2160
        self.record_span(span_start1368, "Abort")
        return result1369

    def parse_export(self) -> transactions_pb2.Export:
        span_start1373 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2162 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2163 = 0
                else:
                    _t2163 = -1
                _t2162 = _t2163
            _t2161 = _t2162
        else:
            _t2161 = -1
        prediction1370 = _t2161
        if prediction1370 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2165 = self.parse_export_iceberg_config()
            export_iceberg_config1372 = _t2165
            self.consume_literal(")")
            _t2166 = transactions_pb2.Export(iceberg_config=export_iceberg_config1372)
            _t2164 = _t2166
        else:
            if prediction1370 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2168 = self.parse_export_csv_config()
                export_csv_config1371 = _t2168
                self.consume_literal(")")
                _t2169 = transactions_pb2.Export(csv_config=export_csv_config1371)
                _t2167 = _t2169
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2164 = _t2167
        result1374 = _t2164
        self.record_span(span_start1373, "Export")
        return result1374

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1382 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2171 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2172 = 1
                else:
                    _t2172 = -1
                _t2171 = _t2172
            _t2170 = _t2171
        else:
            _t2170 = -1
        prediction1375 = _t2170
        if prediction1375 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2174 = self.parse_export_csv_path()
            export_csv_path1379 = _t2174
            _t2175 = self.parse_export_csv_columns_list()
            export_csv_columns_list1380 = _t2175
            _t2176 = self.parse_config_dict()
            config_dict1381 = _t2176
            self.consume_literal(")")
            _t2177 = self.construct_export_csv_config(export_csv_path1379, export_csv_columns_list1380, config_dict1381)
            _t2173 = _t2177
        else:
            if prediction1375 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2179 = self.parse_export_csv_output_location()
                export_csv_output_location1376 = _t2179
                _t2180 = self.parse_export_csv_source()
                export_csv_source1377 = _t2180
                _t2181 = self.parse_csv_config()
                csv_config1378 = _t2181
                self.consume_literal(")")
                _t2182 = self.construct_export_csv_config_with_location(export_csv_output_location1376, export_csv_source1377, csv_config1378)
                _t2178 = _t2182
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2173 = _t2178
        result1383 = _t2173
        self.record_span(span_start1382, "ExportCSVConfig")
        return result1383

    def parse_export_csv_output_location(self) -> tuple[str, str]:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("transaction_output_name", 1):
                _t2184 = 1
            else:
                if self.match_lookahead_literal("path", 1):
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
            self.consume_literal("transaction_output_name")
            _t2187 = self.parse_name()
            name1386 = _t2187
            self.consume_literal(")")
            _t2186 = ("", name1386,)
        else:
            if prediction1384 == 0:
                self.consume_literal("(")
                self.consume_literal("path")
                string1385 = self.consume_terminal("STRING")
                self.consume_literal(")")
                _t2188 = (string1385, "",)
            else:
                raise ParseError("Unexpected token in export_csv_output_location" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2186 = _t2188
        return _t2186

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1393 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2190 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2191 = 0
                else:
                    _t2191 = -1
                _t2190 = _t2191
            _t2189 = _t2190
        else:
            _t2189 = -1
        prediction1387 = _t2189
        if prediction1387 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2193 = self.parse_relation_id()
            relation_id1392 = _t2193
            self.consume_literal(")")
            _t2194 = transactions_pb2.ExportCSVSource(table_def=relation_id1392)
            _t2192 = _t2194
        else:
            if prediction1387 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1388 = []
                cond1389 = self.match_lookahead_literal("(", 0)
                while cond1389:
                    _t2196 = self.parse_export_csv_column()
                    item1390 = _t2196
                    xs1388.append(item1390)
                    cond1389 = self.match_lookahead_literal("(", 0)
                export_csv_columns1391 = xs1388
                self.consume_literal(")")
                _t2197 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1391)
                _t2198 = transactions_pb2.ExportCSVSource(gnf_columns=_t2197)
                _t2195 = _t2198
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2192 = _t2195
        result1394 = _t2192
        self.record_span(span_start1393, "ExportCSVSource")
        return result1394

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1397 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1395 = self.consume_terminal("STRING")
        _t2199 = self.parse_relation_id()
        relation_id1396 = _t2199
        self.consume_literal(")")
        _t2200 = transactions_pb2.ExportCSVColumn(column_name=string1395, column_data=relation_id1396)
        result1398 = _t2200
        self.record_span(span_start1397, "ExportCSVColumn")
        return result1398

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1399 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1399

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1400 = []
        cond1401 = self.match_lookahead_literal("(", 0)
        while cond1401:
            _t2201 = self.parse_export_csv_column()
            item1402 = _t2201
            xs1400.append(item1402)
            cond1401 = self.match_lookahead_literal("(", 0)
        export_csv_columns1403 = xs1400
        self.consume_literal(")")
        return export_csv_columns1403

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1409 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2202 = self.parse_iceberg_locator()
        iceberg_locator1404 = _t2202
        _t2203 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1405 = _t2203
        _t2204 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1406 = _t2204
        _t2205 = self.parse_iceberg_table_properties()
        iceberg_table_properties1407 = _t2205
        if self.match_lookahead_literal("{", 0):
            _t2207 = self.parse_config_dict()
            _t2206 = _t2207
        else:
            _t2206 = None
        config_dict1408 = _t2206
        self.consume_literal(")")
        _t2208 = self.construct_export_iceberg_config_full(iceberg_locator1404, iceberg_catalog_config1405, export_iceberg_table_def1406, iceberg_table_properties1407, config_dict1408)
        result1410 = _t2208
        self.record_span(span_start1409, "ExportIcebergConfig")
        return result1410

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1412 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2209 = self.parse_relation_id()
        relation_id1411 = _t2209
        self.consume_literal(")")
        result1413 = relation_id1411
        self.record_span(span_start1412, "RelationId")
        return result1413

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1414 = []
        cond1415 = self.match_lookahead_literal("(", 0)
        while cond1415:
            _t2210 = self.parse_iceberg_property_entry()
            item1416 = _t2210
            xs1414.append(item1416)
            cond1415 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1417 = xs1414
        self.consume_literal(")")
        return iceberg_property_entrys1417


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
