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
            _t2208 = None
        assert value is not None
        if value.HasField("int32_value"):
            assert value is not None
            return value.int32_value
        else:
            _t2209 = None
        raise ParseError("expected an int32 value (e.g. `1i32`) for this config field")

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2210 = value.HasField("int_value")
        else:
            _t2210 = False
        if _t2210:
            assert value is not None
            return value.int_value
        else:
            _t2211 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2212 = value.HasField("string_value")
        else:
            _t2212 = False
        if _t2212:
            assert value is not None
            return value.string_value
        else:
            _t2213 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2214 = value.HasField("boolean_value")
        else:
            _t2214 = False
        if _t2214:
            assert value is not None
            return value.boolean_value
        else:
            _t2215 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2216 = value.HasField("string_value")
        else:
            _t2216 = False
        if _t2216:
            assert value is not None
            return [value.string_value]
        else:
            _t2217 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2218 = value.HasField("int_value")
        else:
            _t2218 = False
        if _t2218:
            assert value is not None
            return value.int_value
        else:
            _t2219 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2220 = value.HasField("float_value")
        else:
            _t2220 = False
        if _t2220:
            assert value is not None
            return value.float_value
        else:
            _t2221 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2222 = value.HasField("string_value")
        else:
            _t2222 = False
        if _t2222:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2223 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2224 = value.HasField("uint128_value")
        else:
            _t2224 = False
        if _t2224:
            assert value is not None
            return value.uint128_value
        else:
            _t2225 = None
        return None

    def construct_non_cdc_relations(self, targets: Sequence[logic_pb2.TargetRelation]) -> logic_pb2.TargetRelations:
        _t2226 = logic_pb2.PlainTargets(targets=targets)
        _t2227 = logic_pb2.TargetRelations(keys=[], plain=_t2226)
        return _t2227

    def construct_cdc_relations(self, inserts: Sequence[logic_pb2.TargetRelation], deletes: Sequence[logic_pb2.TargetRelation]) -> logic_pb2.TargetRelations:
        _t2228 = logic_pb2.CDCTargets(inserts=inserts, deletes=deletes)
        _t2229 = logic_pb2.TargetRelations(keys=[], cdc=_t2228)
        return _t2229

    def construct_relations(self, keys: tuple[Sequence[logic_pb2.NamedColumn], bool], body: logic_pb2.TargetRelations) -> logic_pb2.TargetRelations:
        if body.HasField("plain"):
            _t2231 = logic_pb2.TargetRelations(keys=keys[0], synthetic_key=keys[1], plain=body.plain)
            return _t2231
        else:
            _t2230 = None
        _t2232 = logic_pb2.TargetRelations(keys=keys[0], synthetic_key=keys[1], cdc=body.cdc)
        return _t2232

    def construct_csv_data(self, locator: logic_pb2.CSVLocator, config: logic_pb2.CSVConfig, columns_opt: Sequence[logic_pb2.GNFColumn] | None, relations_opt: logic_pb2.TargetRelations | None, asof: str) -> logic_pb2.CSVData:
        _t2233 = logic_pb2.CSVData(locator=locator, config=config, columns=(columns_opt if columns_opt is not None else []), asof=asof, relations=relations_opt)
        return _t2233

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]], storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2234 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2234
        _t2235 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2235
        _t2236 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2236
        _t2237 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2237
        _t2238 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2238
        _t2239 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2239
        _t2240 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2240
        _t2241 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2241
        _t2242 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2242
        _t2243 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2243
        _t2244 = self._extract_value_string(config.get("csv_compression"), "")
        compression = _t2244
        _t2245 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2245
        _t2246 = self.construct_csv_storage_integration(storage_integration_opt)
        storage_integration = _t2246
        _t2247 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
        return _t2247

    def construct_csv_storage_integration(self, storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.StorageIntegration | None:
        if storage_integration_opt is None:
            return None
        else:
            _t2248 = None
        assert storage_integration_opt is not None
        config = dict(storage_integration_opt)
        _t2249 = self._extract_value_string(config.get("provider"), "")
        _t2250 = self._extract_value_string(config.get("azure_sas_token"), "")
        _t2251 = self._extract_value_string(config.get("s3_region"), "")
        _t2252 = self._extract_value_string(config.get("s3_access_key_id"), "")
        _t2253 = self._extract_value_string(config.get("s3_secret_access_key"), "")
        _t2254 = logic_pb2.StorageIntegration(provider=_t2249, azure_sas_token=_t2250, s3_region=_t2251, s3_access_key_id=_t2252, s3_secret_access_key=_t2253)
        return _t2254

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2255 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2255
        _t2256 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2256
        _t2257 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2257
        _t2258 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2258
        _t2259 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2259
        _t2260 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2260
        _t2261 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2261
        _t2262 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2262
        _t2263 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2263
        _t2264 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2264
        _t2265 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2265

    def default_configure(self) -> transactions_pb2.Configure:
        _t2266 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2266
        _t2267 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2267

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
        _t2268 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2268
        _t2269 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2269
        config_values_pairs = []
        for pair in config_dict:
            if (pair[0] != "semantics_version" and pair[0] != "ivm.maintenance_level"):
                config_values_pairs.append(pair)
        configuration_values = dict(config_values_pairs)
        _t2270 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config, configuration_values=configuration_values)
        return _t2270

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2271 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2271
        _t2272 = self._extract_value_string(config.get("compression"), "")
        compression = _t2272
        _t2273 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2273
        _t2274 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2274
        _t2275 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2275
        _t2276 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2276
        _t2277 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2277
        _t2278 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2278

    def construct_export_csv_config_with_location(self, location: tuple[str, str], csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2279 = transactions_pb2.ExportCSVConfig(path=location[0], transaction_output_name=location[1], csv_source=csv_source, csv_config=csv_config)
        return _t2279

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2280 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2280

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[logic_pb2.GNFColumn], from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2281 = logic_pb2.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2281

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2282 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2282
        _t2283 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2283
        _t2284 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2284
        table_props = dict(table_property_pairs)
        _t2285 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2285

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start714 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1417 = self.parse_configure()
            _t1416 = _t1417
        else:
            _t1416 = None
        configure708 = _t1416
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1419 = self.parse_sync()
            _t1418 = _t1419
        else:
            _t1418 = None
        sync709 = _t1418
        xs710 = []
        cond711 = self.match_lookahead_literal("(", 0)
        while cond711:
            _t1420 = self.parse_epoch()
            item712 = _t1420
            xs710.append(item712)
            cond711 = self.match_lookahead_literal("(", 0)
        epochs713 = xs710
        self.consume_literal(")")
        _t1421 = self.default_configure()
        _t1422 = transactions_pb2.Transaction(epochs=epochs713, configure=(configure708 if configure708 is not None else _t1421), sync=sync709)
        result715 = _t1422
        self.record_span(span_start714, "Transaction")
        return result715

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start717 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1423 = self.parse_config_dict()
        config_dict716 = _t1423
        self.consume_literal(")")
        _t1424 = self.construct_configure(config_dict716)
        result718 = _t1424
        self.record_span(span_start717, "Configure")
        return result718

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs719 = []
        cond720 = self.match_lookahead_literal(":", 0)
        while cond720:
            _t1425 = self.parse_config_key_value()
            item721 = _t1425
            xs719.append(item721)
            cond720 = self.match_lookahead_literal(":", 0)
        config_key_values722 = xs719
        self.consume_literal("}")
        return config_key_values722

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol723 = self.consume_terminal("SYMBOL")
        _t1426 = self.parse_raw_value()
        raw_value724 = _t1426
        return (symbol723, raw_value724,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start738 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1427 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1428 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1429 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1431 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1432 = 0
                            else:
                                _t1432 = -1
                            _t1431 = _t1432
                        _t1430 = _t1431
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1433 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1434 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1435 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1436 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1437 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1438 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1439 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1440 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1441 = 10
                                                        else:
                                                            _t1441 = -1
                                                        _t1440 = _t1441
                                                    _t1439 = _t1440
                                                _t1438 = _t1439
                                            _t1437 = _t1438
                                        _t1436 = _t1437
                                    _t1435 = _t1436
                                _t1434 = _t1435
                            _t1433 = _t1434
                        _t1430 = _t1433
                    _t1429 = _t1430
                _t1428 = _t1429
            _t1427 = _t1428
        prediction725 = _t1427
        if prediction725 == 12:
            _t1443 = self.parse_boolean_value()
            boolean_value737 = _t1443
            _t1444 = logic_pb2.Value(boolean_value=boolean_value737)
            _t1442 = _t1444
        else:
            if prediction725 == 11:
                self.consume_literal("missing")
                _t1446 = logic_pb2.MissingValue()
                _t1447 = logic_pb2.Value(missing_value=_t1446)
                _t1445 = _t1447
            else:
                if prediction725 == 10:
                    decimal736 = self.consume_terminal("DECIMAL")
                    _t1449 = logic_pb2.Value(decimal_value=decimal736)
                    _t1448 = _t1449
                else:
                    if prediction725 == 9:
                        int128735 = self.consume_terminal("INT128")
                        _t1451 = logic_pb2.Value(int128_value=int128735)
                        _t1450 = _t1451
                    else:
                        if prediction725 == 8:
                            uint128734 = self.consume_terminal("UINT128")
                            _t1453 = logic_pb2.Value(uint128_value=uint128734)
                            _t1452 = _t1453
                        else:
                            if prediction725 == 7:
                                uint32733 = self.consume_terminal("UINT32")
                                _t1455 = logic_pb2.Value(uint32_value=uint32733)
                                _t1454 = _t1455
                            else:
                                if prediction725 == 6:
                                    float732 = self.consume_terminal("FLOAT")
                                    _t1457 = logic_pb2.Value(float_value=float732)
                                    _t1456 = _t1457
                                else:
                                    if prediction725 == 5:
                                        float32731 = self.consume_terminal("FLOAT32")
                                        _t1459 = logic_pb2.Value(float32_value=float32731)
                                        _t1458 = _t1459
                                    else:
                                        if prediction725 == 4:
                                            int730 = self.consume_terminal("INT")
                                            _t1461 = logic_pb2.Value(int_value=int730)
                                            _t1460 = _t1461
                                        else:
                                            if prediction725 == 3:
                                                int32729 = self.consume_terminal("INT32")
                                                _t1463 = logic_pb2.Value(int32_value=int32729)
                                                _t1462 = _t1463
                                            else:
                                                if prediction725 == 2:
                                                    string728 = self.consume_terminal("STRING")
                                                    _t1465 = logic_pb2.Value(string_value=string728)
                                                    _t1464 = _t1465
                                                else:
                                                    if prediction725 == 1:
                                                        _t1467 = self.parse_raw_datetime()
                                                        raw_datetime727 = _t1467
                                                        _t1468 = logic_pb2.Value(datetime_value=raw_datetime727)
                                                        _t1466 = _t1468
                                                    else:
                                                        if prediction725 == 0:
                                                            _t1470 = self.parse_raw_date()
                                                            raw_date726 = _t1470
                                                            _t1471 = logic_pb2.Value(date_value=raw_date726)
                                                            _t1469 = _t1471
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1466 = _t1469
                                                    _t1464 = _t1466
                                                _t1462 = _t1464
                                            _t1460 = _t1462
                                        _t1458 = _t1460
                                    _t1456 = _t1458
                                _t1454 = _t1456
                            _t1452 = _t1454
                        _t1450 = _t1452
                    _t1448 = _t1450
                _t1445 = _t1448
            _t1442 = _t1445
        result739 = _t1442
        self.record_span(span_start738, "Value")
        return result739

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start743 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int740 = self.consume_terminal("INT")
        int_3741 = self.consume_terminal("INT")
        int_4742 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1472 = logic_pb2.DateValue(year=int(int740), month=int(int_3741), day=int(int_4742))
        result744 = _t1472
        self.record_span(span_start743, "DateValue")
        return result744

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start752 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int745 = self.consume_terminal("INT")
        int_3746 = self.consume_terminal("INT")
        int_4747 = self.consume_terminal("INT")
        int_5748 = self.consume_terminal("INT")
        int_6749 = self.consume_terminal("INT")
        int_7750 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1473 = self.consume_terminal("INT")
        else:
            _t1473 = None
        int_8751 = _t1473
        self.consume_literal(")")
        _t1474 = logic_pb2.DateTimeValue(year=int(int745), month=int(int_3746), day=int(int_4747), hour=int(int_5748), minute=int(int_6749), second=int(int_7750), microsecond=int((int_8751 if int_8751 is not None else 0)))
        result753 = _t1474
        self.record_span(span_start752, "DateTimeValue")
        return result753

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1475 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1476 = 1
            else:
                _t1476 = -1
            _t1475 = _t1476
        prediction754 = _t1475
        if prediction754 == 1:
            self.consume_literal("false")
            _t1477 = False
        else:
            if prediction754 == 0:
                self.consume_literal("true")
                _t1478 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1477 = _t1478
        return _t1477

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start759 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs755 = []
        cond756 = self.match_lookahead_literal(":", 0)
        while cond756:
            _t1479 = self.parse_fragment_id()
            item757 = _t1479
            xs755.append(item757)
            cond756 = self.match_lookahead_literal(":", 0)
        fragment_ids758 = xs755
        self.consume_literal(")")
        _t1480 = transactions_pb2.Sync(fragments=fragment_ids758)
        result760 = _t1480
        self.record_span(span_start759, "Sync")
        return result760

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start762 = self.span_start()
        self.consume_literal(":")
        symbol761 = self.consume_terminal("SYMBOL")
        result763 = fragments_pb2.FragmentId(id=symbol761.encode())
        self.record_span(span_start762, "FragmentId")
        return result763

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start766 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1482 = self.parse_epoch_writes()
            _t1481 = _t1482
        else:
            _t1481 = None
        epoch_writes764 = _t1481
        if self.match_lookahead_literal("(", 0):
            _t1484 = self.parse_epoch_reads()
            _t1483 = _t1484
        else:
            _t1483 = None
        epoch_reads765 = _t1483
        self.consume_literal(")")
        _t1485 = transactions_pb2.Epoch(writes=(epoch_writes764 if epoch_writes764 is not None else []), reads=(epoch_reads765 if epoch_reads765 is not None else []))
        result767 = _t1485
        self.record_span(span_start766, "Epoch")
        return result767

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs768 = []
        cond769 = self.match_lookahead_literal("(", 0)
        while cond769:
            _t1486 = self.parse_write()
            item770 = _t1486
            xs768.append(item770)
            cond769 = self.match_lookahead_literal("(", 0)
        writes771 = xs768
        self.consume_literal(")")
        return writes771

    def parse_write(self) -> transactions_pb2.Write:
        span_start777 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1488 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1489 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1490 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1491 = 2
                        else:
                            _t1491 = -1
                        _t1490 = _t1491
                    _t1489 = _t1490
                _t1488 = _t1489
            _t1487 = _t1488
        else:
            _t1487 = -1
        prediction772 = _t1487
        if prediction772 == 3:
            _t1493 = self.parse_snapshot()
            snapshot776 = _t1493
            _t1494 = transactions_pb2.Write(snapshot=snapshot776)
            _t1492 = _t1494
        else:
            if prediction772 == 2:
                _t1496 = self.parse_context()
                context775 = _t1496
                _t1497 = transactions_pb2.Write(context=context775)
                _t1495 = _t1497
            else:
                if prediction772 == 1:
                    _t1499 = self.parse_undefine()
                    undefine774 = _t1499
                    _t1500 = transactions_pb2.Write(undefine=undefine774)
                    _t1498 = _t1500
                else:
                    if prediction772 == 0:
                        _t1502 = self.parse_define()
                        define773 = _t1502
                        _t1503 = transactions_pb2.Write(define=define773)
                        _t1501 = _t1503
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1498 = _t1501
                _t1495 = _t1498
            _t1492 = _t1495
        result778 = _t1492
        self.record_span(span_start777, "Write")
        return result778

    def parse_define(self) -> transactions_pb2.Define:
        span_start780 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1504 = self.parse_fragment()
        fragment779 = _t1504
        self.consume_literal(")")
        _t1505 = transactions_pb2.Define(fragment=fragment779)
        result781 = _t1505
        self.record_span(span_start780, "Define")
        return result781

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start787 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1506 = self.parse_new_fragment_id()
        new_fragment_id782 = _t1506
        xs783 = []
        cond784 = self.match_lookahead_literal("(", 0)
        while cond784:
            _t1507 = self.parse_declaration()
            item785 = _t1507
            xs783.append(item785)
            cond784 = self.match_lookahead_literal("(", 0)
        declarations786 = xs783
        self.consume_literal(")")
        result788 = self.construct_fragment(new_fragment_id782, declarations786)
        self.record_span(span_start787, "Fragment")
        return result788

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start790 = self.span_start()
        _t1508 = self.parse_fragment_id()
        fragment_id789 = _t1508
        self.start_fragment(fragment_id789)
        result791 = fragment_id789
        self.record_span(span_start790, "FragmentId")
        return result791

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start797 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1510 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1511 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1512 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1513 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1514 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1515 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1516 = 1
                                    else:
                                        _t1516 = -1
                                    _t1515 = _t1516
                                _t1514 = _t1515
                            _t1513 = _t1514
                        _t1512 = _t1513
                    _t1511 = _t1512
                _t1510 = _t1511
            _t1509 = _t1510
        else:
            _t1509 = -1
        prediction792 = _t1509
        if prediction792 == 3:
            _t1518 = self.parse_data()
            data796 = _t1518
            _t1519 = logic_pb2.Declaration(data=data796)
            _t1517 = _t1519
        else:
            if prediction792 == 2:
                _t1521 = self.parse_constraint()
                constraint795 = _t1521
                _t1522 = logic_pb2.Declaration(constraint=constraint795)
                _t1520 = _t1522
            else:
                if prediction792 == 1:
                    _t1524 = self.parse_algorithm()
                    algorithm794 = _t1524
                    _t1525 = logic_pb2.Declaration(algorithm=algorithm794)
                    _t1523 = _t1525
                else:
                    if prediction792 == 0:
                        _t1527 = self.parse_def()
                        def793 = _t1527
                        _t1528 = logic_pb2.Declaration()
                        getattr(_t1528, 'def').CopyFrom(def793)
                        _t1526 = _t1528
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1523 = _t1526
                _t1520 = _t1523
            _t1517 = _t1520
        result798 = _t1517
        self.record_span(span_start797, "Declaration")
        return result798

    def parse_def(self) -> logic_pb2.Def:
        span_start802 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1529 = self.parse_relation_id()
        relation_id799 = _t1529
        _t1530 = self.parse_abstraction()
        abstraction800 = _t1530
        if self.match_lookahead_literal("(", 0):
            _t1532 = self.parse_attrs()
            _t1531 = _t1532
        else:
            _t1531 = None
        attrs801 = _t1531
        self.consume_literal(")")
        _t1533 = logic_pb2.Def(name=relation_id799, body=abstraction800, attrs=(attrs801 if attrs801 is not None else []))
        result803 = _t1533
        self.record_span(span_start802, "Def")
        return result803

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start807 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1534 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1535 = 1
            else:
                _t1535 = -1
            _t1534 = _t1535
        prediction804 = _t1534
        if prediction804 == 1:
            uint128806 = self.consume_terminal("UINT128")
            _t1536 = logic_pb2.RelationId(id_low=uint128806.low, id_high=uint128806.high)
        else:
            if prediction804 == 0:
                self.consume_literal(":")
                symbol805 = self.consume_terminal("SYMBOL")
                _t1537 = self.relation_id_from_string(symbol805)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1536 = _t1537
        result808 = _t1536
        self.record_span(span_start807, "RelationId")
        return result808

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start811 = self.span_start()
        self.consume_literal("(")
        _t1538 = self.parse_bindings()
        bindings809 = _t1538
        _t1539 = self.parse_formula()
        formula810 = _t1539
        self.consume_literal(")")
        _t1540 = logic_pb2.Abstraction(vars=(list(bindings809[0]) + list(bindings809[1] if bindings809[1] is not None else [])), value=formula810)
        result812 = _t1540
        self.record_span(span_start811, "Abstraction")
        return result812

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs813 = []
        cond814 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond814:
            _t1541 = self.parse_binding()
            item815 = _t1541
            xs813.append(item815)
            cond814 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings816 = xs813
        if self.match_lookahead_literal("|", 0):
            _t1543 = self.parse_value_bindings()
            _t1542 = _t1543
        else:
            _t1542 = None
        value_bindings817 = _t1542
        self.consume_literal("]")
        return (bindings816, (value_bindings817 if value_bindings817 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start820 = self.span_start()
        symbol818 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1544 = self.parse_type()
        type819 = _t1544
        _t1545 = logic_pb2.Var(name=symbol818)
        _t1546 = logic_pb2.Binding(var=_t1545, type=type819)
        result821 = _t1546
        self.record_span(span_start820, "Binding")
        return result821

    def parse_type(self) -> logic_pb2.Type:
        span_start837 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1547 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1548 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1549 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1550 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1551 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1552 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1553 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1554 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1555 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1556 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1557 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1558 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1559 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1560 = 9
                                                            else:
                                                                _t1560 = -1
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
        prediction822 = _t1547
        if prediction822 == 13:
            _t1562 = self.parse_uint32_type()
            uint32_type836 = _t1562
            _t1563 = logic_pb2.Type(uint32_type=uint32_type836)
            _t1561 = _t1563
        else:
            if prediction822 == 12:
                _t1565 = self.parse_float32_type()
                float32_type835 = _t1565
                _t1566 = logic_pb2.Type(float32_type=float32_type835)
                _t1564 = _t1566
            else:
                if prediction822 == 11:
                    _t1568 = self.parse_int32_type()
                    int32_type834 = _t1568
                    _t1569 = logic_pb2.Type(int32_type=int32_type834)
                    _t1567 = _t1569
                else:
                    if prediction822 == 10:
                        _t1571 = self.parse_boolean_type()
                        boolean_type833 = _t1571
                        _t1572 = logic_pb2.Type(boolean_type=boolean_type833)
                        _t1570 = _t1572
                    else:
                        if prediction822 == 9:
                            _t1574 = self.parse_decimal_type()
                            decimal_type832 = _t1574
                            _t1575 = logic_pb2.Type(decimal_type=decimal_type832)
                            _t1573 = _t1575
                        else:
                            if prediction822 == 8:
                                _t1577 = self.parse_missing_type()
                                missing_type831 = _t1577
                                _t1578 = logic_pb2.Type(missing_type=missing_type831)
                                _t1576 = _t1578
                            else:
                                if prediction822 == 7:
                                    _t1580 = self.parse_datetime_type()
                                    datetime_type830 = _t1580
                                    _t1581 = logic_pb2.Type(datetime_type=datetime_type830)
                                    _t1579 = _t1581
                                else:
                                    if prediction822 == 6:
                                        _t1583 = self.parse_date_type()
                                        date_type829 = _t1583
                                        _t1584 = logic_pb2.Type(date_type=date_type829)
                                        _t1582 = _t1584
                                    else:
                                        if prediction822 == 5:
                                            _t1586 = self.parse_int128_type()
                                            int128_type828 = _t1586
                                            _t1587 = logic_pb2.Type(int128_type=int128_type828)
                                            _t1585 = _t1587
                                        else:
                                            if prediction822 == 4:
                                                _t1589 = self.parse_uint128_type()
                                                uint128_type827 = _t1589
                                                _t1590 = logic_pb2.Type(uint128_type=uint128_type827)
                                                _t1588 = _t1590
                                            else:
                                                if prediction822 == 3:
                                                    _t1592 = self.parse_float_type()
                                                    float_type826 = _t1592
                                                    _t1593 = logic_pb2.Type(float_type=float_type826)
                                                    _t1591 = _t1593
                                                else:
                                                    if prediction822 == 2:
                                                        _t1595 = self.parse_int_type()
                                                        int_type825 = _t1595
                                                        _t1596 = logic_pb2.Type(int_type=int_type825)
                                                        _t1594 = _t1596
                                                    else:
                                                        if prediction822 == 1:
                                                            _t1598 = self.parse_string_type()
                                                            string_type824 = _t1598
                                                            _t1599 = logic_pb2.Type(string_type=string_type824)
                                                            _t1597 = _t1599
                                                        else:
                                                            if prediction822 == 0:
                                                                _t1601 = self.parse_unspecified_type()
                                                                unspecified_type823 = _t1601
                                                                _t1602 = logic_pb2.Type(unspecified_type=unspecified_type823)
                                                                _t1600 = _t1602
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1597 = _t1600
                                                        _t1594 = _t1597
                                                    _t1591 = _t1594
                                                _t1588 = _t1591
                                            _t1585 = _t1588
                                        _t1582 = _t1585
                                    _t1579 = _t1582
                                _t1576 = _t1579
                            _t1573 = _t1576
                        _t1570 = _t1573
                    _t1567 = _t1570
                _t1564 = _t1567
            _t1561 = _t1564
        result838 = _t1561
        self.record_span(span_start837, "Type")
        return result838

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start839 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1603 = logic_pb2.UnspecifiedType()
        result840 = _t1603
        self.record_span(span_start839, "UnspecifiedType")
        return result840

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start841 = self.span_start()
        self.consume_literal("STRING")
        _t1604 = logic_pb2.StringType()
        result842 = _t1604
        self.record_span(span_start841, "StringType")
        return result842

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start843 = self.span_start()
        self.consume_literal("INT")
        _t1605 = logic_pb2.IntType()
        result844 = _t1605
        self.record_span(span_start843, "IntType")
        return result844

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start845 = self.span_start()
        self.consume_literal("FLOAT")
        _t1606 = logic_pb2.FloatType()
        result846 = _t1606
        self.record_span(span_start845, "FloatType")
        return result846

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start847 = self.span_start()
        self.consume_literal("UINT128")
        _t1607 = logic_pb2.UInt128Type()
        result848 = _t1607
        self.record_span(span_start847, "UInt128Type")
        return result848

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start849 = self.span_start()
        self.consume_literal("INT128")
        _t1608 = logic_pb2.Int128Type()
        result850 = _t1608
        self.record_span(span_start849, "Int128Type")
        return result850

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start851 = self.span_start()
        self.consume_literal("DATE")
        _t1609 = logic_pb2.DateType()
        result852 = _t1609
        self.record_span(span_start851, "DateType")
        return result852

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start853 = self.span_start()
        self.consume_literal("DATETIME")
        _t1610 = logic_pb2.DateTimeType()
        result854 = _t1610
        self.record_span(span_start853, "DateTimeType")
        return result854

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start855 = self.span_start()
        self.consume_literal("MISSING")
        _t1611 = logic_pb2.MissingType()
        result856 = _t1611
        self.record_span(span_start855, "MissingType")
        return result856

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start859 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int857 = self.consume_terminal("INT")
        int_3858 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1612 = logic_pb2.DecimalType(precision=int(int857), scale=int(int_3858))
        result860 = _t1612
        self.record_span(span_start859, "DecimalType")
        return result860

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start861 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1613 = logic_pb2.BooleanType()
        result862 = _t1613
        self.record_span(span_start861, "BooleanType")
        return result862

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start863 = self.span_start()
        self.consume_literal("INT32")
        _t1614 = logic_pb2.Int32Type()
        result864 = _t1614
        self.record_span(span_start863, "Int32Type")
        return result864

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start865 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1615 = logic_pb2.Float32Type()
        result866 = _t1615
        self.record_span(span_start865, "Float32Type")
        return result866

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start867 = self.span_start()
        self.consume_literal("UINT32")
        _t1616 = logic_pb2.UInt32Type()
        result868 = _t1616
        self.record_span(span_start867, "UInt32Type")
        return result868

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs869 = []
        cond870 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond870:
            _t1617 = self.parse_binding()
            item871 = _t1617
            xs869.append(item871)
            cond870 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings872 = xs869
        return bindings872

    def parse_formula(self) -> logic_pb2.Formula:
        span_start887 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1619 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1620 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1621 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1622 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1623 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1624 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1625 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1626 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1627 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1628 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1629 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1630 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1631 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1632 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1633 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1634 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1635 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1636 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1637 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1638 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1639 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1640 = 10
                                                                                                else:
                                                                                                    _t1640 = -1
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
                _t1619 = _t1620
            _t1618 = _t1619
        else:
            _t1618 = -1
        prediction873 = _t1618
        if prediction873 == 12:
            _t1642 = self.parse_cast()
            cast886 = _t1642
            _t1643 = logic_pb2.Formula(cast=cast886)
            _t1641 = _t1643
        else:
            if prediction873 == 11:
                _t1645 = self.parse_rel_atom()
                rel_atom885 = _t1645
                _t1646 = logic_pb2.Formula(rel_atom=rel_atom885)
                _t1644 = _t1646
            else:
                if prediction873 == 10:
                    _t1648 = self.parse_primitive()
                    primitive884 = _t1648
                    _t1649 = logic_pb2.Formula(primitive=primitive884)
                    _t1647 = _t1649
                else:
                    if prediction873 == 9:
                        _t1651 = self.parse_pragma()
                        pragma883 = _t1651
                        _t1652 = logic_pb2.Formula(pragma=pragma883)
                        _t1650 = _t1652
                    else:
                        if prediction873 == 8:
                            _t1654 = self.parse_atom()
                            atom882 = _t1654
                            _t1655 = logic_pb2.Formula(atom=atom882)
                            _t1653 = _t1655
                        else:
                            if prediction873 == 7:
                                _t1657 = self.parse_ffi()
                                ffi881 = _t1657
                                _t1658 = logic_pb2.Formula(ffi=ffi881)
                                _t1656 = _t1658
                            else:
                                if prediction873 == 6:
                                    _t1660 = self.parse_not()
                                    not880 = _t1660
                                    _t1661 = logic_pb2.Formula()
                                    getattr(_t1661, 'not').CopyFrom(not880)
                                    _t1659 = _t1661
                                else:
                                    if prediction873 == 5:
                                        _t1663 = self.parse_disjunction()
                                        disjunction879 = _t1663
                                        _t1664 = logic_pb2.Formula(disjunction=disjunction879)
                                        _t1662 = _t1664
                                    else:
                                        if prediction873 == 4:
                                            _t1666 = self.parse_conjunction()
                                            conjunction878 = _t1666
                                            _t1667 = logic_pb2.Formula(conjunction=conjunction878)
                                            _t1665 = _t1667
                                        else:
                                            if prediction873 == 3:
                                                _t1669 = self.parse_reduce()
                                                reduce877 = _t1669
                                                _t1670 = logic_pb2.Formula(reduce=reduce877)
                                                _t1668 = _t1670
                                            else:
                                                if prediction873 == 2:
                                                    _t1672 = self.parse_exists()
                                                    exists876 = _t1672
                                                    _t1673 = logic_pb2.Formula(exists=exists876)
                                                    _t1671 = _t1673
                                                else:
                                                    if prediction873 == 1:
                                                        _t1675 = self.parse_false()
                                                        false875 = _t1675
                                                        _t1676 = logic_pb2.Formula(disjunction=false875)
                                                        _t1674 = _t1676
                                                    else:
                                                        if prediction873 == 0:
                                                            _t1678 = self.parse_true()
                                                            true874 = _t1678
                                                            _t1679 = logic_pb2.Formula(conjunction=true874)
                                                            _t1677 = _t1679
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1674 = _t1677
                                                    _t1671 = _t1674
                                                _t1668 = _t1671
                                            _t1665 = _t1668
                                        _t1662 = _t1665
                                    _t1659 = _t1662
                                _t1656 = _t1659
                            _t1653 = _t1656
                        _t1650 = _t1653
                    _t1647 = _t1650
                _t1644 = _t1647
            _t1641 = _t1644
        result888 = _t1641
        self.record_span(span_start887, "Formula")
        return result888

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start889 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1680 = logic_pb2.Conjunction(args=[])
        result890 = _t1680
        self.record_span(span_start889, "Conjunction")
        return result890

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start891 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1681 = logic_pb2.Disjunction(args=[])
        result892 = _t1681
        self.record_span(span_start891, "Disjunction")
        return result892

    def parse_exists(self) -> logic_pb2.Exists:
        span_start895 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1682 = self.parse_bindings()
        bindings893 = _t1682
        _t1683 = self.parse_formula()
        formula894 = _t1683
        self.consume_literal(")")
        _t1684 = logic_pb2.Abstraction(vars=(list(bindings893[0]) + list(bindings893[1] if bindings893[1] is not None else [])), value=formula894)
        _t1685 = logic_pb2.Exists(body=_t1684)
        result896 = _t1685
        self.record_span(span_start895, "Exists")
        return result896

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start900 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1686 = self.parse_abstraction()
        abstraction897 = _t1686
        _t1687 = self.parse_abstraction()
        abstraction_3898 = _t1687
        _t1688 = self.parse_terms()
        terms899 = _t1688
        self.consume_literal(")")
        _t1689 = logic_pb2.Reduce(op=abstraction897, body=abstraction_3898, terms=terms899)
        result901 = _t1689
        self.record_span(span_start900, "Reduce")
        return result901

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs902 = []
        cond903 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond903:
            _t1690 = self.parse_term()
            item904 = _t1690
            xs902.append(item904)
            cond903 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms905 = xs902
        self.consume_literal(")")
        return terms905

    def parse_term(self) -> logic_pb2.Term:
        span_start909 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1691 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1692 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1693 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1694 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1695 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1696 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1697 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1698 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1699 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1700 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1701 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1702 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1703 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1704 = 1
                                                            else:
                                                                _t1704 = -1
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
                _t1692 = _t1693
            _t1691 = _t1692
        prediction906 = _t1691
        if prediction906 == 1:
            _t1706 = self.parse_value()
            value908 = _t1706
            _t1707 = logic_pb2.Term(constant=value908)
            _t1705 = _t1707
        else:
            if prediction906 == 0:
                _t1709 = self.parse_var()
                var907 = _t1709
                _t1710 = logic_pb2.Term(var=var907)
                _t1708 = _t1710
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1705 = _t1708
        result910 = _t1705
        self.record_span(span_start909, "Term")
        return result910

    def parse_var(self) -> logic_pb2.Var:
        span_start912 = self.span_start()
        symbol911 = self.consume_terminal("SYMBOL")
        _t1711 = logic_pb2.Var(name=symbol911)
        result913 = _t1711
        self.record_span(span_start912, "Var")
        return result913

    def parse_value(self) -> logic_pb2.Value:
        span_start927 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1712 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1713 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1714 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1716 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1717 = 0
                            else:
                                _t1717 = -1
                            _t1716 = _t1717
                        _t1715 = _t1716
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1718 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1719 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1720 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1721 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1722 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1723 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1724 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1725 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1726 = 10
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
                        _t1715 = _t1718
                    _t1714 = _t1715
                _t1713 = _t1714
            _t1712 = _t1713
        prediction914 = _t1712
        if prediction914 == 12:
            _t1728 = self.parse_boolean_value()
            boolean_value926 = _t1728
            _t1729 = logic_pb2.Value(boolean_value=boolean_value926)
            _t1727 = _t1729
        else:
            if prediction914 == 11:
                self.consume_literal("missing")
                _t1731 = logic_pb2.MissingValue()
                _t1732 = logic_pb2.Value(missing_value=_t1731)
                _t1730 = _t1732
            else:
                if prediction914 == 10:
                    formatted_decimal925 = self.consume_terminal("DECIMAL")
                    _t1734 = logic_pb2.Value(decimal_value=formatted_decimal925)
                    _t1733 = _t1734
                else:
                    if prediction914 == 9:
                        formatted_int128924 = self.consume_terminal("INT128")
                        _t1736 = logic_pb2.Value(int128_value=formatted_int128924)
                        _t1735 = _t1736
                    else:
                        if prediction914 == 8:
                            formatted_uint128923 = self.consume_terminal("UINT128")
                            _t1738 = logic_pb2.Value(uint128_value=formatted_uint128923)
                            _t1737 = _t1738
                        else:
                            if prediction914 == 7:
                                formatted_uint32922 = self.consume_terminal("UINT32")
                                _t1740 = logic_pb2.Value(uint32_value=formatted_uint32922)
                                _t1739 = _t1740
                            else:
                                if prediction914 == 6:
                                    formatted_float921 = self.consume_terminal("FLOAT")
                                    _t1742 = logic_pb2.Value(float_value=formatted_float921)
                                    _t1741 = _t1742
                                else:
                                    if prediction914 == 5:
                                        formatted_float32920 = self.consume_terminal("FLOAT32")
                                        _t1744 = logic_pb2.Value(float32_value=formatted_float32920)
                                        _t1743 = _t1744
                                    else:
                                        if prediction914 == 4:
                                            formatted_int919 = self.consume_terminal("INT")
                                            _t1746 = logic_pb2.Value(int_value=formatted_int919)
                                            _t1745 = _t1746
                                        else:
                                            if prediction914 == 3:
                                                formatted_int32918 = self.consume_terminal("INT32")
                                                _t1748 = logic_pb2.Value(int32_value=formatted_int32918)
                                                _t1747 = _t1748
                                            else:
                                                if prediction914 == 2:
                                                    formatted_string917 = self.consume_terminal("STRING")
                                                    _t1750 = logic_pb2.Value(string_value=formatted_string917)
                                                    _t1749 = _t1750
                                                else:
                                                    if prediction914 == 1:
                                                        _t1752 = self.parse_datetime()
                                                        datetime916 = _t1752
                                                        _t1753 = logic_pb2.Value(datetime_value=datetime916)
                                                        _t1751 = _t1753
                                                    else:
                                                        if prediction914 == 0:
                                                            _t1755 = self.parse_date()
                                                            date915 = _t1755
                                                            _t1756 = logic_pb2.Value(date_value=date915)
                                                            _t1754 = _t1756
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1751 = _t1754
                                                    _t1749 = _t1751
                                                _t1747 = _t1749
                                            _t1745 = _t1747
                                        _t1743 = _t1745
                                    _t1741 = _t1743
                                _t1739 = _t1741
                            _t1737 = _t1739
                        _t1735 = _t1737
                    _t1733 = _t1735
                _t1730 = _t1733
            _t1727 = _t1730
        result928 = _t1727
        self.record_span(span_start927, "Value")
        return result928

    def parse_date(self) -> logic_pb2.DateValue:
        span_start932 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int929 = self.consume_terminal("INT")
        formatted_int_3930 = self.consume_terminal("INT")
        formatted_int_4931 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1757 = logic_pb2.DateValue(year=int(formatted_int929), month=int(formatted_int_3930), day=int(formatted_int_4931))
        result933 = _t1757
        self.record_span(span_start932, "DateValue")
        return result933

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start941 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int934 = self.consume_terminal("INT")
        formatted_int_3935 = self.consume_terminal("INT")
        formatted_int_4936 = self.consume_terminal("INT")
        formatted_int_5937 = self.consume_terminal("INT")
        formatted_int_6938 = self.consume_terminal("INT")
        formatted_int_7939 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1758 = self.consume_terminal("INT")
        else:
            _t1758 = None
        formatted_int_8940 = _t1758
        self.consume_literal(")")
        _t1759 = logic_pb2.DateTimeValue(year=int(formatted_int934), month=int(formatted_int_3935), day=int(formatted_int_4936), hour=int(formatted_int_5937), minute=int(formatted_int_6938), second=int(formatted_int_7939), microsecond=int((formatted_int_8940 if formatted_int_8940 is not None else 0)))
        result942 = _t1759
        self.record_span(span_start941, "DateTimeValue")
        return result942

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start947 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs943 = []
        cond944 = self.match_lookahead_literal("(", 0)
        while cond944:
            _t1760 = self.parse_formula()
            item945 = _t1760
            xs943.append(item945)
            cond944 = self.match_lookahead_literal("(", 0)
        formulas946 = xs943
        self.consume_literal(")")
        _t1761 = logic_pb2.Conjunction(args=formulas946)
        result948 = _t1761
        self.record_span(span_start947, "Conjunction")
        return result948

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start953 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs949 = []
        cond950 = self.match_lookahead_literal("(", 0)
        while cond950:
            _t1762 = self.parse_formula()
            item951 = _t1762
            xs949.append(item951)
            cond950 = self.match_lookahead_literal("(", 0)
        formulas952 = xs949
        self.consume_literal(")")
        _t1763 = logic_pb2.Disjunction(args=formulas952)
        result954 = _t1763
        self.record_span(span_start953, "Disjunction")
        return result954

    def parse_not(self) -> logic_pb2.Not:
        span_start956 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1764 = self.parse_formula()
        formula955 = _t1764
        self.consume_literal(")")
        _t1765 = logic_pb2.Not(arg=formula955)
        result957 = _t1765
        self.record_span(span_start956, "Not")
        return result957

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start961 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1766 = self.parse_name()
        name958 = _t1766
        _t1767 = self.parse_ffi_args()
        ffi_args959 = _t1767
        _t1768 = self.parse_terms()
        terms960 = _t1768
        self.consume_literal(")")
        _t1769 = logic_pb2.FFI(name=name958, args=ffi_args959, terms=terms960)
        result962 = _t1769
        self.record_span(span_start961, "FFI")
        return result962

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol963 = self.consume_terminal("SYMBOL")
        return symbol963

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs964 = []
        cond965 = self.match_lookahead_literal("(", 0)
        while cond965:
            _t1770 = self.parse_abstraction()
            item966 = _t1770
            xs964.append(item966)
            cond965 = self.match_lookahead_literal("(", 0)
        abstractions967 = xs964
        self.consume_literal(")")
        return abstractions967

    def parse_atom(self) -> logic_pb2.Atom:
        span_start973 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1771 = self.parse_relation_id()
        relation_id968 = _t1771
        xs969 = []
        cond970 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond970:
            _t1772 = self.parse_term()
            item971 = _t1772
            xs969.append(item971)
            cond970 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms972 = xs969
        self.consume_literal(")")
        _t1773 = logic_pb2.Atom(name=relation_id968, terms=terms972)
        result974 = _t1773
        self.record_span(span_start973, "Atom")
        return result974

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start980 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1774 = self.parse_name()
        name975 = _t1774
        xs976 = []
        cond977 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond977:
            _t1775 = self.parse_term()
            item978 = _t1775
            xs976.append(item978)
            cond977 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms979 = xs976
        self.consume_literal(")")
        _t1776 = logic_pb2.Pragma(name=name975, terms=terms979)
        result981 = _t1776
        self.record_span(span_start980, "Pragma")
        return result981

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start997 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1778 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1779 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1780 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1781 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1782 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1783 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1784 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1785 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1786 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1787 = 7
                                                else:
                                                    _t1787 = -1
                                                _t1786 = _t1787
                                            _t1785 = _t1786
                                        _t1784 = _t1785
                                    _t1783 = _t1784
                                _t1782 = _t1783
                            _t1781 = _t1782
                        _t1780 = _t1781
                    _t1779 = _t1780
                _t1778 = _t1779
            _t1777 = _t1778
        else:
            _t1777 = -1
        prediction982 = _t1777
        if prediction982 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1789 = self.parse_name()
            name992 = _t1789
            xs993 = []
            cond994 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond994:
                _t1790 = self.parse_rel_term()
                item995 = _t1790
                xs993.append(item995)
                cond994 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms996 = xs993
            self.consume_literal(")")
            _t1791 = logic_pb2.Primitive(name=name992, terms=rel_terms996)
            _t1788 = _t1791
        else:
            if prediction982 == 8:
                _t1793 = self.parse_divide()
                divide991 = _t1793
                _t1792 = divide991
            else:
                if prediction982 == 7:
                    _t1795 = self.parse_multiply()
                    multiply990 = _t1795
                    _t1794 = multiply990
                else:
                    if prediction982 == 6:
                        _t1797 = self.parse_minus()
                        minus989 = _t1797
                        _t1796 = minus989
                    else:
                        if prediction982 == 5:
                            _t1799 = self.parse_add()
                            add988 = _t1799
                            _t1798 = add988
                        else:
                            if prediction982 == 4:
                                _t1801 = self.parse_gt_eq()
                                gt_eq987 = _t1801
                                _t1800 = gt_eq987
                            else:
                                if prediction982 == 3:
                                    _t1803 = self.parse_gt()
                                    gt986 = _t1803
                                    _t1802 = gt986
                                else:
                                    if prediction982 == 2:
                                        _t1805 = self.parse_lt_eq()
                                        lt_eq985 = _t1805
                                        _t1804 = lt_eq985
                                    else:
                                        if prediction982 == 1:
                                            _t1807 = self.parse_lt()
                                            lt984 = _t1807
                                            _t1806 = lt984
                                        else:
                                            if prediction982 == 0:
                                                _t1809 = self.parse_eq()
                                                eq983 = _t1809
                                                _t1808 = eq983
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1806 = _t1808
                                        _t1804 = _t1806
                                    _t1802 = _t1804
                                _t1800 = _t1802
                            _t1798 = _t1800
                        _t1796 = _t1798
                    _t1794 = _t1796
                _t1792 = _t1794
            _t1788 = _t1792
        result998 = _t1788
        self.record_span(span_start997, "Primitive")
        return result998

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start1001 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1810 = self.parse_term()
        term999 = _t1810
        _t1811 = self.parse_term()
        term_31000 = _t1811
        self.consume_literal(")")
        _t1812 = logic_pb2.RelTerm(term=term999)
        _t1813 = logic_pb2.RelTerm(term=term_31000)
        _t1814 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1812, _t1813])
        result1002 = _t1814
        self.record_span(span_start1001, "Primitive")
        return result1002

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start1005 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1815 = self.parse_term()
        term1003 = _t1815
        _t1816 = self.parse_term()
        term_31004 = _t1816
        self.consume_literal(")")
        _t1817 = logic_pb2.RelTerm(term=term1003)
        _t1818 = logic_pb2.RelTerm(term=term_31004)
        _t1819 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1817, _t1818])
        result1006 = _t1819
        self.record_span(span_start1005, "Primitive")
        return result1006

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start1009 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1820 = self.parse_term()
        term1007 = _t1820
        _t1821 = self.parse_term()
        term_31008 = _t1821
        self.consume_literal(")")
        _t1822 = logic_pb2.RelTerm(term=term1007)
        _t1823 = logic_pb2.RelTerm(term=term_31008)
        _t1824 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1822, _t1823])
        result1010 = _t1824
        self.record_span(span_start1009, "Primitive")
        return result1010

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start1013 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1825 = self.parse_term()
        term1011 = _t1825
        _t1826 = self.parse_term()
        term_31012 = _t1826
        self.consume_literal(")")
        _t1827 = logic_pb2.RelTerm(term=term1011)
        _t1828 = logic_pb2.RelTerm(term=term_31012)
        _t1829 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1827, _t1828])
        result1014 = _t1829
        self.record_span(span_start1013, "Primitive")
        return result1014

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start1017 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1830 = self.parse_term()
        term1015 = _t1830
        _t1831 = self.parse_term()
        term_31016 = _t1831
        self.consume_literal(")")
        _t1832 = logic_pb2.RelTerm(term=term1015)
        _t1833 = logic_pb2.RelTerm(term=term_31016)
        _t1834 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1832, _t1833])
        result1018 = _t1834
        self.record_span(span_start1017, "Primitive")
        return result1018

    def parse_add(self) -> logic_pb2.Primitive:
        span_start1022 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1835 = self.parse_term()
        term1019 = _t1835
        _t1836 = self.parse_term()
        term_31020 = _t1836
        _t1837 = self.parse_term()
        term_41021 = _t1837
        self.consume_literal(")")
        _t1838 = logic_pb2.RelTerm(term=term1019)
        _t1839 = logic_pb2.RelTerm(term=term_31020)
        _t1840 = logic_pb2.RelTerm(term=term_41021)
        _t1841 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1838, _t1839, _t1840])
        result1023 = _t1841
        self.record_span(span_start1022, "Primitive")
        return result1023

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start1027 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1842 = self.parse_term()
        term1024 = _t1842
        _t1843 = self.parse_term()
        term_31025 = _t1843
        _t1844 = self.parse_term()
        term_41026 = _t1844
        self.consume_literal(")")
        _t1845 = logic_pb2.RelTerm(term=term1024)
        _t1846 = logic_pb2.RelTerm(term=term_31025)
        _t1847 = logic_pb2.RelTerm(term=term_41026)
        _t1848 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1845, _t1846, _t1847])
        result1028 = _t1848
        self.record_span(span_start1027, "Primitive")
        return result1028

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start1032 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1849 = self.parse_term()
        term1029 = _t1849
        _t1850 = self.parse_term()
        term_31030 = _t1850
        _t1851 = self.parse_term()
        term_41031 = _t1851
        self.consume_literal(")")
        _t1852 = logic_pb2.RelTerm(term=term1029)
        _t1853 = logic_pb2.RelTerm(term=term_31030)
        _t1854 = logic_pb2.RelTerm(term=term_41031)
        _t1855 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1852, _t1853, _t1854])
        result1033 = _t1855
        self.record_span(span_start1032, "Primitive")
        return result1033

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start1037 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1856 = self.parse_term()
        term1034 = _t1856
        _t1857 = self.parse_term()
        term_31035 = _t1857
        _t1858 = self.parse_term()
        term_41036 = _t1858
        self.consume_literal(")")
        _t1859 = logic_pb2.RelTerm(term=term1034)
        _t1860 = logic_pb2.RelTerm(term=term_31035)
        _t1861 = logic_pb2.RelTerm(term=term_41036)
        _t1862 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1859, _t1860, _t1861])
        result1038 = _t1862
        self.record_span(span_start1037, "Primitive")
        return result1038

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1042 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1863 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1864 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1865 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1866 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1867 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1868 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1869 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1870 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1871 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1872 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1873 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1874 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1875 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1876 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1877 = 1
                                                                else:
                                                                    _t1877 = -1
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
                _t1864 = _t1865
            _t1863 = _t1864
        prediction1039 = _t1863
        if prediction1039 == 1:
            _t1879 = self.parse_term()
            term1041 = _t1879
            _t1880 = logic_pb2.RelTerm(term=term1041)
            _t1878 = _t1880
        else:
            if prediction1039 == 0:
                _t1882 = self.parse_specialized_value()
                specialized_value1040 = _t1882
                _t1883 = logic_pb2.RelTerm(specialized_value=specialized_value1040)
                _t1881 = _t1883
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1878 = _t1881
        result1043 = _t1878
        self.record_span(span_start1042, "RelTerm")
        return result1043

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1045 = self.span_start()
        self.consume_literal("#")
        _t1884 = self.parse_raw_value()
        raw_value1044 = _t1884
        result1046 = raw_value1044
        self.record_span(span_start1045, "Value")
        return result1046

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1052 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1885 = self.parse_name()
        name1047 = _t1885
        xs1048 = []
        cond1049 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1049:
            _t1886 = self.parse_rel_term()
            item1050 = _t1886
            xs1048.append(item1050)
            cond1049 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1051 = xs1048
        self.consume_literal(")")
        _t1887 = logic_pb2.RelAtom(name=name1047, terms=rel_terms1051)
        result1053 = _t1887
        self.record_span(span_start1052, "RelAtom")
        return result1053

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1056 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1888 = self.parse_term()
        term1054 = _t1888
        _t1889 = self.parse_term()
        term_31055 = _t1889
        self.consume_literal(")")
        _t1890 = logic_pb2.Cast(input=term1054, result=term_31055)
        result1057 = _t1890
        self.record_span(span_start1056, "Cast")
        return result1057

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1058 = []
        cond1059 = self.match_lookahead_literal("(", 0)
        while cond1059:
            _t1891 = self.parse_attribute()
            item1060 = _t1891
            xs1058.append(item1060)
            cond1059 = self.match_lookahead_literal("(", 0)
        attributes1061 = xs1058
        self.consume_literal(")")
        return attributes1061

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1067 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1892 = self.parse_name()
        name1062 = _t1892
        xs1063 = []
        cond1064 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1064:
            _t1893 = self.parse_raw_value()
            item1065 = _t1893
            xs1063.append(item1065)
            cond1064 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1066 = xs1063
        self.consume_literal(")")
        _t1894 = logic_pb2.Attribute(name=name1062, args=raw_values1066)
        result1068 = _t1894
        self.record_span(span_start1067, "Attribute")
        return result1068

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1075 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1069 = []
        cond1070 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1070:
            _t1895 = self.parse_relation_id()
            item1071 = _t1895
            xs1069.append(item1071)
            cond1070 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1072 = xs1069
        _t1896 = self.parse_script()
        script1073 = _t1896
        if self.match_lookahead_literal("(", 0):
            _t1898 = self.parse_attrs()
            _t1897 = _t1898
        else:
            _t1897 = None
        attrs1074 = _t1897
        self.consume_literal(")")
        _t1899 = logic_pb2.Algorithm(body=script1073, attrs=(attrs1074 if attrs1074 is not None else []))
        getattr(_t1899, 'global').extend(relation_ids1072)
        result1076 = _t1899
        self.record_span(span_start1075, "Algorithm")
        return result1076

    def parse_script(self) -> logic_pb2.Script:
        span_start1081 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1077 = []
        cond1078 = self.match_lookahead_literal("(", 0)
        while cond1078:
            _t1900 = self.parse_construct()
            item1079 = _t1900
            xs1077.append(item1079)
            cond1078 = self.match_lookahead_literal("(", 0)
        constructs1080 = xs1077
        self.consume_literal(")")
        _t1901 = logic_pb2.Script(constructs=constructs1080)
        result1082 = _t1901
        self.record_span(span_start1081, "Script")
        return result1082

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1086 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1903 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1904 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1905 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1906 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1907 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1908 = 1
                                else:
                                    _t1908 = -1
                                _t1907 = _t1908
                            _t1906 = _t1907
                        _t1905 = _t1906
                    _t1904 = _t1905
                _t1903 = _t1904
            _t1902 = _t1903
        else:
            _t1902 = -1
        prediction1083 = _t1902
        if prediction1083 == 1:
            _t1910 = self.parse_instruction()
            instruction1085 = _t1910
            _t1911 = logic_pb2.Construct(instruction=instruction1085)
            _t1909 = _t1911
        else:
            if prediction1083 == 0:
                _t1913 = self.parse_loop()
                loop1084 = _t1913
                _t1914 = logic_pb2.Construct(loop=loop1084)
                _t1912 = _t1914
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1909 = _t1912
        result1087 = _t1909
        self.record_span(span_start1086, "Construct")
        return result1087

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1091 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1915 = self.parse_init()
        init1088 = _t1915
        _t1916 = self.parse_script()
        script1089 = _t1916
        if self.match_lookahead_literal("(", 0):
            _t1918 = self.parse_attrs()
            _t1917 = _t1918
        else:
            _t1917 = None
        attrs1090 = _t1917
        self.consume_literal(")")
        _t1919 = logic_pb2.Loop(init=init1088, body=script1089, attrs=(attrs1090 if attrs1090 is not None else []))
        result1092 = _t1919
        self.record_span(span_start1091, "Loop")
        return result1092

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1093 = []
        cond1094 = self.match_lookahead_literal("(", 0)
        while cond1094:
            _t1920 = self.parse_instruction()
            item1095 = _t1920
            xs1093.append(item1095)
            cond1094 = self.match_lookahead_literal("(", 0)
        instructions1096 = xs1093
        self.consume_literal(")")
        return instructions1096

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1103 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1922 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1923 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1924 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1925 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1926 = 0
                            else:
                                _t1926 = -1
                            _t1925 = _t1926
                        _t1924 = _t1925
                    _t1923 = _t1924
                _t1922 = _t1923
            _t1921 = _t1922
        else:
            _t1921 = -1
        prediction1097 = _t1921
        if prediction1097 == 4:
            _t1928 = self.parse_monus_def()
            monus_def1102 = _t1928
            _t1929 = logic_pb2.Instruction(monus_def=monus_def1102)
            _t1927 = _t1929
        else:
            if prediction1097 == 3:
                _t1931 = self.parse_monoid_def()
                monoid_def1101 = _t1931
                _t1932 = logic_pb2.Instruction(monoid_def=monoid_def1101)
                _t1930 = _t1932
            else:
                if prediction1097 == 2:
                    _t1934 = self.parse_break()
                    break1100 = _t1934
                    _t1935 = logic_pb2.Instruction()
                    getattr(_t1935, 'break').CopyFrom(break1100)
                    _t1933 = _t1935
                else:
                    if prediction1097 == 1:
                        _t1937 = self.parse_upsert()
                        upsert1099 = _t1937
                        _t1938 = logic_pb2.Instruction(upsert=upsert1099)
                        _t1936 = _t1938
                    else:
                        if prediction1097 == 0:
                            _t1940 = self.parse_assign()
                            assign1098 = _t1940
                            _t1941 = logic_pb2.Instruction(assign=assign1098)
                            _t1939 = _t1941
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1936 = _t1939
                    _t1933 = _t1936
                _t1930 = _t1933
            _t1927 = _t1930
        result1104 = _t1927
        self.record_span(span_start1103, "Instruction")
        return result1104

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1108 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1942 = self.parse_relation_id()
        relation_id1105 = _t1942
        _t1943 = self.parse_abstraction()
        abstraction1106 = _t1943
        if self.match_lookahead_literal("(", 0):
            _t1945 = self.parse_attrs()
            _t1944 = _t1945
        else:
            _t1944 = None
        attrs1107 = _t1944
        self.consume_literal(")")
        _t1946 = logic_pb2.Assign(name=relation_id1105, body=abstraction1106, attrs=(attrs1107 if attrs1107 is not None else []))
        result1109 = _t1946
        self.record_span(span_start1108, "Assign")
        return result1109

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1113 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1947 = self.parse_relation_id()
        relation_id1110 = _t1947
        _t1948 = self.parse_abstraction_with_arity()
        abstraction_with_arity1111 = _t1948
        if self.match_lookahead_literal("(", 0):
            _t1950 = self.parse_attrs()
            _t1949 = _t1950
        else:
            _t1949 = None
        attrs1112 = _t1949
        self.consume_literal(")")
        _t1951 = logic_pb2.Upsert(name=relation_id1110, body=abstraction_with_arity1111[0], attrs=(attrs1112 if attrs1112 is not None else []), value_arity=abstraction_with_arity1111[1])
        result1114 = _t1951
        self.record_span(span_start1113, "Upsert")
        return result1114

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1952 = self.parse_bindings()
        bindings1115 = _t1952
        _t1953 = self.parse_formula()
        formula1116 = _t1953
        self.consume_literal(")")
        _t1954 = logic_pb2.Abstraction(vars=(list(bindings1115[0]) + list(bindings1115[1] if bindings1115[1] is not None else [])), value=formula1116)
        return (_t1954, len(bindings1115[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1120 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1955 = self.parse_relation_id()
        relation_id1117 = _t1955
        _t1956 = self.parse_abstraction()
        abstraction1118 = _t1956
        if self.match_lookahead_literal("(", 0):
            _t1958 = self.parse_attrs()
            _t1957 = _t1958
        else:
            _t1957 = None
        attrs1119 = _t1957
        self.consume_literal(")")
        _t1959 = logic_pb2.Break(name=relation_id1117, body=abstraction1118, attrs=(attrs1119 if attrs1119 is not None else []))
        result1121 = _t1959
        self.record_span(span_start1120, "Break")
        return result1121

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1126 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1960 = self.parse_monoid()
        monoid1122 = _t1960
        _t1961 = self.parse_relation_id()
        relation_id1123 = _t1961
        _t1962 = self.parse_abstraction_with_arity()
        abstraction_with_arity1124 = _t1962
        if self.match_lookahead_literal("(", 0):
            _t1964 = self.parse_attrs()
            _t1963 = _t1964
        else:
            _t1963 = None
        attrs1125 = _t1963
        self.consume_literal(")")
        _t1965 = logic_pb2.MonoidDef(monoid=monoid1122, name=relation_id1123, body=abstraction_with_arity1124[0], attrs=(attrs1125 if attrs1125 is not None else []), value_arity=abstraction_with_arity1124[1])
        result1127 = _t1965
        self.record_span(span_start1126, "MonoidDef")
        return result1127

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1133 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1967 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1968 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1969 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1970 = 2
                        else:
                            _t1970 = -1
                        _t1969 = _t1970
                    _t1968 = _t1969
                _t1967 = _t1968
            _t1966 = _t1967
        else:
            _t1966 = -1
        prediction1128 = _t1966
        if prediction1128 == 3:
            _t1972 = self.parse_sum_monoid()
            sum_monoid1132 = _t1972
            _t1973 = logic_pb2.Monoid(sum_monoid=sum_monoid1132)
            _t1971 = _t1973
        else:
            if prediction1128 == 2:
                _t1975 = self.parse_max_monoid()
                max_monoid1131 = _t1975
                _t1976 = logic_pb2.Monoid(max_monoid=max_monoid1131)
                _t1974 = _t1976
            else:
                if prediction1128 == 1:
                    _t1978 = self.parse_min_monoid()
                    min_monoid1130 = _t1978
                    _t1979 = logic_pb2.Monoid(min_monoid=min_monoid1130)
                    _t1977 = _t1979
                else:
                    if prediction1128 == 0:
                        _t1981 = self.parse_or_monoid()
                        or_monoid1129 = _t1981
                        _t1982 = logic_pb2.Monoid(or_monoid=or_monoid1129)
                        _t1980 = _t1982
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1977 = _t1980
                _t1974 = _t1977
            _t1971 = _t1974
        result1134 = _t1971
        self.record_span(span_start1133, "Monoid")
        return result1134

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1135 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1983 = logic_pb2.OrMonoid()
        result1136 = _t1983
        self.record_span(span_start1135, "OrMonoid")
        return result1136

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1138 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1984 = self.parse_type()
        type1137 = _t1984
        self.consume_literal(")")
        _t1985 = logic_pb2.MinMonoid(type=type1137)
        result1139 = _t1985
        self.record_span(span_start1138, "MinMonoid")
        return result1139

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1141 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1986 = self.parse_type()
        type1140 = _t1986
        self.consume_literal(")")
        _t1987 = logic_pb2.MaxMonoid(type=type1140)
        result1142 = _t1987
        self.record_span(span_start1141, "MaxMonoid")
        return result1142

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1144 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1988 = self.parse_type()
        type1143 = _t1988
        self.consume_literal(")")
        _t1989 = logic_pb2.SumMonoid(type=type1143)
        result1145 = _t1989
        self.record_span(span_start1144, "SumMonoid")
        return result1145

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1150 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1990 = self.parse_monoid()
        monoid1146 = _t1990
        _t1991 = self.parse_relation_id()
        relation_id1147 = _t1991
        _t1992 = self.parse_abstraction_with_arity()
        abstraction_with_arity1148 = _t1992
        if self.match_lookahead_literal("(", 0):
            _t1994 = self.parse_attrs()
            _t1993 = _t1994
        else:
            _t1993 = None
        attrs1149 = _t1993
        self.consume_literal(")")
        _t1995 = logic_pb2.MonusDef(monoid=monoid1146, name=relation_id1147, body=abstraction_with_arity1148[0], attrs=(attrs1149 if attrs1149 is not None else []), value_arity=abstraction_with_arity1148[1])
        result1151 = _t1995
        self.record_span(span_start1150, "MonusDef")
        return result1151

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1156 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1996 = self.parse_relation_id()
        relation_id1152 = _t1996
        _t1997 = self.parse_abstraction()
        abstraction1153 = _t1997
        _t1998 = self.parse_functional_dependency_keys()
        functional_dependency_keys1154 = _t1998
        _t1999 = self.parse_functional_dependency_values()
        functional_dependency_values1155 = _t1999
        self.consume_literal(")")
        _t2000 = logic_pb2.FunctionalDependency(guard=abstraction1153, keys=functional_dependency_keys1154, values=functional_dependency_values1155)
        _t2001 = logic_pb2.Constraint(name=relation_id1152, functional_dependency=_t2000)
        result1157 = _t2001
        self.record_span(span_start1156, "Constraint")
        return result1157

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1158 = []
        cond1159 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1159:
            _t2002 = self.parse_var()
            item1160 = _t2002
            xs1158.append(item1160)
            cond1159 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1161 = xs1158
        self.consume_literal(")")
        return vars1161

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1162 = []
        cond1163 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1163:
            _t2003 = self.parse_var()
            item1164 = _t2003
            xs1162.append(item1164)
            cond1163 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1165 = xs1162
        self.consume_literal(")")
        return vars1165

    def parse_data(self) -> logic_pb2.Data:
        span_start1171 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t2005 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t2006 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t2007 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t2008 = 1
                        else:
                            _t2008 = -1
                        _t2007 = _t2008
                    _t2006 = _t2007
                _t2005 = _t2006
            _t2004 = _t2005
        else:
            _t2004 = -1
        prediction1166 = _t2004
        if prediction1166 == 3:
            _t2010 = self.parse_iceberg_data()
            iceberg_data1170 = _t2010
            _t2011 = logic_pb2.Data(iceberg_data=iceberg_data1170)
            _t2009 = _t2011
        else:
            if prediction1166 == 2:
                _t2013 = self.parse_csv_data()
                csv_data1169 = _t2013
                _t2014 = logic_pb2.Data(csv_data=csv_data1169)
                _t2012 = _t2014
            else:
                if prediction1166 == 1:
                    _t2016 = self.parse_betree_relation()
                    betree_relation1168 = _t2016
                    _t2017 = logic_pb2.Data(betree_relation=betree_relation1168)
                    _t2015 = _t2017
                else:
                    if prediction1166 == 0:
                        _t2019 = self.parse_edb()
                        edb1167 = _t2019
                        _t2020 = logic_pb2.Data(edb=edb1167)
                        _t2018 = _t2020
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t2015 = _t2018
                _t2012 = _t2015
            _t2009 = _t2012
        result1172 = _t2009
        self.record_span(span_start1171, "Data")
        return result1172

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1176 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t2021 = self.parse_relation_id()
        relation_id1173 = _t2021
        _t2022 = self.parse_edb_path()
        edb_path1174 = _t2022
        _t2023 = self.parse_edb_types()
        edb_types1175 = _t2023
        self.consume_literal(")")
        _t2024 = logic_pb2.EDB(target_id=relation_id1173, path=edb_path1174, types=edb_types1175)
        result1177 = _t2024
        self.record_span(span_start1176, "EDB")
        return result1177

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1178 = []
        cond1179 = self.match_lookahead_terminal("STRING", 0)
        while cond1179:
            item1180 = self.consume_terminal("STRING")
            xs1178.append(item1180)
            cond1179 = self.match_lookahead_terminal("STRING", 0)
        strings1181 = xs1178
        self.consume_literal("]")
        return strings1181

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1182 = []
        cond1183 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1183:
            _t2025 = self.parse_type()
            item1184 = _t2025
            xs1182.append(item1184)
            cond1183 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1185 = xs1182
        self.consume_literal("]")
        return types1185

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1188 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t2026 = self.parse_relation_id()
        relation_id1186 = _t2026
        _t2027 = self.parse_betree_info()
        betree_info1187 = _t2027
        self.consume_literal(")")
        _t2028 = logic_pb2.BeTreeRelation(name=relation_id1186, relation_info=betree_info1187)
        result1189 = _t2028
        self.record_span(span_start1188, "BeTreeRelation")
        return result1189

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1193 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t2029 = self.parse_betree_info_key_types()
        betree_info_key_types1190 = _t2029
        _t2030 = self.parse_betree_info_value_types()
        betree_info_value_types1191 = _t2030
        _t2031 = self.parse_config_dict()
        config_dict1192 = _t2031
        self.consume_literal(")")
        _t2032 = self.construct_betree_info(betree_info_key_types1190, betree_info_value_types1191, config_dict1192)
        result1194 = _t2032
        self.record_span(span_start1193, "BeTreeInfo")
        return result1194

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1195 = []
        cond1196 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1196:
            _t2033 = self.parse_type()
            item1197 = _t2033
            xs1195.append(item1197)
            cond1196 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1198 = xs1195
        self.consume_literal(")")
        return types1198

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1199 = []
        cond1200 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1200:
            _t2034 = self.parse_type()
            item1201 = _t2034
            xs1199.append(item1201)
            cond1200 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1202 = xs1199
        self.consume_literal(")")
        return types1202

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1208 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t2035 = self.parse_csvlocator()
        csvlocator1203 = _t2035
        _t2036 = self.parse_csv_config()
        csv_config1204 = _t2036
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("columns", 1)):
            _t2038 = self.parse_gnf_columns()
            _t2037 = _t2038
        else:
            _t2037 = None
        gnf_columns1205 = _t2037
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("relations", 1)):
            _t2040 = self.parse_target_relations()
            _t2039 = _t2040
        else:
            _t2039 = None
        target_relations1206 = _t2039
        _t2041 = self.parse_csv_asof()
        csv_asof1207 = _t2041
        self.consume_literal(")")
        _t2042 = self.construct_csv_data(csvlocator1203, csv_config1204, gnf_columns1205, target_relations1206, csv_asof1207)
        result1209 = _t2042
        self.record_span(span_start1208, "CSVData")
        return result1209

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1212 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t2044 = self.parse_csv_locator_paths()
            _t2043 = _t2044
        else:
            _t2043 = None
        csv_locator_paths1210 = _t2043
        if self.match_lookahead_literal("(", 0):
            _t2046 = self.parse_csv_locator_inline_data()
            _t2045 = _t2046
        else:
            _t2045 = None
        csv_locator_inline_data1211 = _t2045
        self.consume_literal(")")
        _t2047 = logic_pb2.CSVLocator(paths=(csv_locator_paths1210 if csv_locator_paths1210 is not None else []), inline_data=(csv_locator_inline_data1211 if csv_locator_inline_data1211 is not None else "").encode())
        result1213 = _t2047
        self.record_span(span_start1212, "CSVLocator")
        return result1213

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1214 = []
        cond1215 = self.match_lookahead_terminal("STRING", 0)
        while cond1215:
            item1216 = self.consume_terminal("STRING")
            xs1214.append(item1216)
            cond1215 = self.match_lookahead_terminal("STRING", 0)
        strings1217 = xs1214
        self.consume_literal(")")
        return strings1217

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        formatted_string1218 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return formatted_string1218

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1221 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t2048 = self.parse_config_dict()
        config_dict1219 = _t2048
        if self.match_lookahead_literal("(", 0):
            _t2050 = self.parse__storage_integration()
            _t2049 = _t2050
        else:
            _t2049 = None
        _storage_integration1220 = _t2049
        self.consume_literal(")")
        _t2051 = self.construct_csv_config(config_dict1219, _storage_integration1220)
        result1222 = _t2051
        self.record_span(span_start1221, "CSVConfig")
        return result1222

    def parse__storage_integration(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("(")
        self.consume_literal("storage_integration")
        _t2052 = self.parse_config_dict()
        config_dict1223 = _t2052
        self.consume_literal(")")
        return config_dict1223

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1224 = []
        cond1225 = self.match_lookahead_literal("(", 0)
        while cond1225:
            _t2053 = self.parse_gnf_column()
            item1226 = _t2053
            xs1224.append(item1226)
            cond1225 = self.match_lookahead_literal("(", 0)
        gnf_columns1227 = xs1224
        self.consume_literal(")")
        return gnf_columns1227

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1234 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t2054 = self.parse_gnf_column_path()
        gnf_column_path1228 = _t2054
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t2056 = self.parse_relation_id()
            _t2055 = _t2056
        else:
            _t2055 = None
        relation_id1229 = _t2055
        self.consume_literal("[")
        xs1230 = []
        cond1231 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1231:
            _t2057 = self.parse_type()
            item1232 = _t2057
            xs1230.append(item1232)
            cond1231 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1233 = xs1230
        self.consume_literal("]")
        self.consume_literal(")")
        _t2058 = logic_pb2.GNFColumn(column_path=gnf_column_path1228, target_id=relation_id1229, types=types1233)
        result1235 = _t2058
        self.record_span(span_start1234, "GNFColumn")
        return result1235

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t2059 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t2060 = 0
            else:
                _t2060 = -1
            _t2059 = _t2060
        prediction1236 = _t2059
        if prediction1236 == 1:
            self.consume_literal("[")
            xs1238 = []
            cond1239 = self.match_lookahead_terminal("STRING", 0)
            while cond1239:
                item1240 = self.consume_terminal("STRING")
                xs1238.append(item1240)
                cond1239 = self.match_lookahead_terminal("STRING", 0)
            strings1241 = xs1238
            self.consume_literal("]")
            _t2061 = strings1241
        else:
            if prediction1236 == 0:
                string1237 = self.consume_terminal("STRING")
                _t2062 = [string1237]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2061 = _t2062
        return _t2061

    def parse_target_relations(self) -> logic_pb2.TargetRelations:
        span_start1244 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relations")
        _t2063 = self.parse_relation_keys()
        relation_keys1242 = _t2063
        _t2064 = self.parse_relation_body()
        relation_body1243 = _t2064
        self.consume_literal(")")
        _t2065 = self.construct_relations(relation_keys1242, relation_body1243)
        result1245 = _t2065
        self.record_span(span_start1244, "TargetRelations")
        return result1245

    def parse_relation_keys(self) -> tuple[Sequence[logic_pb2.NamedColumn], bool]:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("keys", 1):
                if self.match_lookahead_literal("synthetic", 2):
                    _t2068 = 1
                else:
                    if self.match_lookahead_literal(")", 2):
                        _t2069 = 0
                    else:
                        if self.match_lookahead_literal("(", 2):
                            _t2070 = 0
                        else:
                            _t2070 = -1
                        _t2069 = _t2070
                    _t2068 = _t2069
                _t2067 = _t2068
            else:
                _t2067 = -1
            _t2066 = _t2067
        else:
            _t2066 = -1
        prediction1246 = _t2066
        if prediction1246 == 1:
            self.consume_literal("(")
            self.consume_literal("keys")
            self.consume_literal("synthetic")
            self.consume_literal(")")
            _t2071 = ([], True,)
        else:
            if prediction1246 == 0:
                self.consume_literal("(")
                self.consume_literal("keys")
                xs1247 = []
                cond1248 = self.match_lookahead_literal("(", 0)
                while cond1248:
                    _t2073 = self.parse_named_column()
                    item1249 = _t2073
                    xs1247.append(item1249)
                    cond1248 = self.match_lookahead_literal("(", 0)
                named_columns1250 = xs1247
                self.consume_literal(")")
                _t2072 = (named_columns1250, False,)
            else:
                raise ParseError("Unexpected token in relation_keys" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2071 = _t2072
        return _t2071

    def parse_named_column(self) -> logic_pb2.NamedColumn:
        span_start1253 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1251 = self.consume_terminal("STRING")
        _t2074 = self.parse_type()
        type1252 = _t2074
        self.consume_literal(")")
        _t2075 = logic_pb2.NamedColumn(name=string1251, type=type1252)
        result1254 = _t2075
        self.record_span(span_start1253, "NamedColumn")
        return result1254

    def parse_relation_body(self) -> logic_pb2.TargetRelations:
        span_start1259 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("relation", 1):
                _t2077 = 0
            else:
                if self.match_lookahead_literal("inserts", 1):
                    _t2078 = 1
                else:
                    _t2078 = 0
                _t2077 = _t2078
            _t2076 = _t2077
        else:
            _t2076 = 0
        prediction1255 = _t2076
        if prediction1255 == 1:
            _t2080 = self.parse_cdc_inserts()
            cdc_inserts1257 = _t2080
            _t2081 = self.parse_cdc_deletes()
            cdc_deletes1258 = _t2081
            _t2082 = self.construct_cdc_relations(cdc_inserts1257, cdc_deletes1258)
            _t2079 = _t2082
        else:
            if prediction1255 == 0:
                _t2084 = self.parse_non_cdc_relations()
                non_cdc_relations1256 = _t2084
                _t2085 = self.construct_non_cdc_relations(non_cdc_relations1256)
                _t2083 = _t2085
            else:
                raise ParseError("Unexpected token in relation_body" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2079 = _t2083
        result1260 = _t2079
        self.record_span(span_start1259, "TargetRelations")
        return result1260

    def parse_non_cdc_relations(self) -> Sequence[logic_pb2.TargetRelation]:
        xs1261 = []
        cond1262 = self.match_lookahead_literal("(", 0)
        while cond1262:
            _t2086 = self.parse_target_relation()
            item1263 = _t2086
            xs1261.append(item1263)
            cond1262 = self.match_lookahead_literal("(", 0)
        return xs1261

    def parse_target_relation(self) -> logic_pb2.TargetRelation:
        span_start1269 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relation")
        _t2087 = self.parse_relation_id()
        relation_id1264 = _t2087
        xs1265 = []
        cond1266 = self.match_lookahead_literal("(", 0)
        while cond1266:
            _t2088 = self.parse_named_column()
            item1267 = _t2088
            xs1265.append(item1267)
            cond1266 = self.match_lookahead_literal("(", 0)
        named_columns1268 = xs1265
        self.consume_literal(")")
        _t2089 = logic_pb2.TargetRelation(target_id=relation_id1264, values=named_columns1268)
        result1270 = _t2089
        self.record_span(span_start1269, "TargetRelation")
        return result1270

    def parse_cdc_inserts(self) -> Sequence[logic_pb2.TargetRelation]:
        self.consume_literal("(")
        self.consume_literal("inserts")
        xs1271 = []
        cond1272 = self.match_lookahead_literal("(", 0)
        while cond1272:
            _t2090 = self.parse_target_relation()
            item1273 = _t2090
            xs1271.append(item1273)
            cond1272 = self.match_lookahead_literal("(", 0)
        target_relations1274 = xs1271
        self.consume_literal(")")
        return target_relations1274

    def parse_cdc_deletes(self) -> Sequence[logic_pb2.TargetRelation]:
        self.consume_literal("(")
        self.consume_literal("deletes")
        xs1275 = []
        cond1276 = self.match_lookahead_literal("(", 0)
        while cond1276:
            _t2091 = self.parse_target_relation()
            item1277 = _t2091
            xs1275.append(item1277)
            cond1276 = self.match_lookahead_literal("(", 0)
        target_relations1278 = xs1275
        self.consume_literal(")")
        return target_relations1278

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1279 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1279

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1286 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t2092 = self.parse_iceberg_locator()
        iceberg_locator1280 = _t2092
        _t2093 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1281 = _t2093
        _t2094 = self.parse_gnf_columns()
        gnf_columns1282 = _t2094
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t2096 = self.parse_iceberg_from_snapshot()
            _t2095 = _t2096
        else:
            _t2095 = None
        iceberg_from_snapshot1283 = _t2095
        if self.match_lookahead_literal("(", 0):
            _t2098 = self.parse_iceberg_to_snapshot()
            _t2097 = _t2098
        else:
            _t2097 = None
        iceberg_to_snapshot1284 = _t2097
        _t2099 = self.parse_boolean_value()
        boolean_value1285 = _t2099
        self.consume_literal(")")
        _t2100 = self.construct_iceberg_data(iceberg_locator1280, iceberg_catalog_config1281, gnf_columns1282, iceberg_from_snapshot1283, iceberg_to_snapshot1284, boolean_value1285)
        result1287 = _t2100
        self.record_span(span_start1286, "IcebergData")
        return result1287

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1291 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t2101 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1288 = _t2101
        _t2102 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1289 = _t2102
        _t2103 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1290 = _t2103
        self.consume_literal(")")
        _t2104 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1288, namespace=iceberg_locator_namespace1289, warehouse=iceberg_locator_warehouse1290)
        result1292 = _t2104
        self.record_span(span_start1291, "IcebergLocator")
        return result1292

    def parse_iceberg_locator_table_name(self) -> str:
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1293 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1293

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1294 = []
        cond1295 = self.match_lookahead_terminal("STRING", 0)
        while cond1295:
            item1296 = self.consume_terminal("STRING")
            xs1294.append(item1296)
            cond1295 = self.match_lookahead_terminal("STRING", 0)
        strings1297 = xs1294
        self.consume_literal(")")
        return strings1297

    def parse_iceberg_locator_warehouse(self) -> str:
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string1298 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1298

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1303 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t2105 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1299 = _t2105
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t2107 = self.parse_iceberg_catalog_config_scope()
            _t2106 = _t2107
        else:
            _t2106 = None
        iceberg_catalog_config_scope1300 = _t2106
        _t2108 = self.parse_iceberg_properties()
        iceberg_properties1301 = _t2108
        _t2109 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1302 = _t2109
        self.consume_literal(")")
        _t2110 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1299, iceberg_catalog_config_scope1300, iceberg_properties1301, iceberg_auth_properties1302)
        result1304 = _t2110
        self.record_span(span_start1303, "IcebergCatalogConfig")
        return result1304

    def parse_iceberg_catalog_uri(self) -> str:
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1305 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1305

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1306 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1306

    def parse_iceberg_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1307 = []
        cond1308 = self.match_lookahead_literal("(", 0)
        while cond1308:
            _t2111 = self.parse_iceberg_property_entry()
            item1309 = _t2111
            xs1307.append(item1309)
            cond1308 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1310 = xs1307
        self.consume_literal(")")
        return iceberg_property_entrys1310

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1311 = self.consume_terminal("STRING")
        string_31312 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1311, string_31312,)

    def parse_iceberg_auth_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1313 = []
        cond1314 = self.match_lookahead_literal("(", 0)
        while cond1314:
            _t2112 = self.parse_iceberg_masked_property_entry()
            item1315 = _t2112
            xs1313.append(item1315)
            cond1314 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1316 = xs1313
        self.consume_literal(")")
        return iceberg_masked_property_entrys1316

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1317 = self.consume_terminal("STRING")
        string_31318 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1317, string_31318,)

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1319 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1319

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1320 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1320

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1322 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2113 = self.parse_fragment_id()
        fragment_id1321 = _t2113
        self.consume_literal(")")
        _t2114 = transactions_pb2.Undefine(fragment_id=fragment_id1321)
        result1323 = _t2114
        self.record_span(span_start1322, "Undefine")
        return result1323

    def parse_context(self) -> transactions_pb2.Context:
        span_start1328 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1324 = []
        cond1325 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1325:
            _t2115 = self.parse_relation_id()
            item1326 = _t2115
            xs1324.append(item1326)
            cond1325 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1327 = xs1324
        self.consume_literal(")")
        _t2116 = transactions_pb2.Context(relations=relation_ids1327)
        result1329 = _t2116
        self.record_span(span_start1328, "Context")
        return result1329

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1335 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t2117 = self.parse_edb_path()
        edb_path1330 = _t2117
        xs1331 = []
        cond1332 = self.match_lookahead_literal("[", 0)
        while cond1332:
            _t2118 = self.parse_snapshot_mapping()
            item1333 = _t2118
            xs1331.append(item1333)
            cond1332 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1334 = xs1331
        self.consume_literal(")")
        _t2119 = transactions_pb2.Snapshot(prefix=edb_path1330, mappings=snapshot_mappings1334)
        result1336 = _t2119
        self.record_span(span_start1335, "Snapshot")
        return result1336

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1339 = self.span_start()
        _t2120 = self.parse_edb_path()
        edb_path1337 = _t2120
        _t2121 = self.parse_relation_id()
        relation_id1338 = _t2121
        _t2122 = transactions_pb2.SnapshotMapping(destination_path=edb_path1337, source_relation=relation_id1338)
        result1340 = _t2122
        self.record_span(span_start1339, "SnapshotMapping")
        return result1340

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1341 = []
        cond1342 = self.match_lookahead_literal("(", 0)
        while cond1342:
            _t2123 = self.parse_read()
            item1343 = _t2123
            xs1341.append(item1343)
            cond1342 = self.match_lookahead_literal("(", 0)
        reads1344 = xs1341
        self.consume_literal(")")
        return reads1344

    def parse_read(self) -> transactions_pb2.Read:
        span_start1351 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2125 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2126 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t2127 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t2128 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t2129 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t2130 = 3
                                else:
                                    _t2130 = -1
                                _t2129 = _t2130
                            _t2128 = _t2129
                        _t2127 = _t2128
                    _t2126 = _t2127
                _t2125 = _t2126
            _t2124 = _t2125
        else:
            _t2124 = -1
        prediction1345 = _t2124
        if prediction1345 == 4:
            _t2132 = self.parse_export()
            export1350 = _t2132
            _t2133 = transactions_pb2.Read(export=export1350)
            _t2131 = _t2133
        else:
            if prediction1345 == 3:
                _t2135 = self.parse_abort()
                abort1349 = _t2135
                _t2136 = transactions_pb2.Read(abort=abort1349)
                _t2134 = _t2136
            else:
                if prediction1345 == 2:
                    _t2138 = self.parse_what_if()
                    what_if1348 = _t2138
                    _t2139 = transactions_pb2.Read(what_if=what_if1348)
                    _t2137 = _t2139
                else:
                    if prediction1345 == 1:
                        _t2141 = self.parse_output()
                        output1347 = _t2141
                        _t2142 = transactions_pb2.Read(output=output1347)
                        _t2140 = _t2142
                    else:
                        if prediction1345 == 0:
                            _t2144 = self.parse_demand()
                            demand1346 = _t2144
                            _t2145 = transactions_pb2.Read(demand=demand1346)
                            _t2143 = _t2145
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2140 = _t2143
                    _t2137 = _t2140
                _t2134 = _t2137
            _t2131 = _t2134
        result1352 = _t2131
        self.record_span(span_start1351, "Read")
        return result1352

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1354 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2146 = self.parse_relation_id()
        relation_id1353 = _t2146
        self.consume_literal(")")
        _t2147 = transactions_pb2.Demand(relation_id=relation_id1353)
        result1355 = _t2147
        self.record_span(span_start1354, "Demand")
        return result1355

    def parse_output(self) -> transactions_pb2.Output:
        span_start1358 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2148 = self.parse_name()
        name1356 = _t2148
        _t2149 = self.parse_relation_id()
        relation_id1357 = _t2149
        self.consume_literal(")")
        _t2150 = transactions_pb2.Output(name=name1356, relation_id=relation_id1357)
        result1359 = _t2150
        self.record_span(span_start1358, "Output")
        return result1359

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1362 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2151 = self.parse_name()
        name1360 = _t2151
        _t2152 = self.parse_epoch()
        epoch1361 = _t2152
        self.consume_literal(")")
        _t2153 = transactions_pb2.WhatIf(branch=name1360, epoch=epoch1361)
        result1363 = _t2153
        self.record_span(span_start1362, "WhatIf")
        return result1363

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1366 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2155 = self.parse_name()
            _t2154 = _t2155
        else:
            _t2154 = None
        name1364 = _t2154
        _t2156 = self.parse_relation_id()
        relation_id1365 = _t2156
        self.consume_literal(")")
        _t2157 = transactions_pb2.Abort(name=(name1364 if name1364 is not None else "abort"), relation_id=relation_id1365)
        result1367 = _t2157
        self.record_span(span_start1366, "Abort")
        return result1367

    def parse_export(self) -> transactions_pb2.Export:
        span_start1371 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2159 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2160 = 0
                else:
                    _t2160 = -1
                _t2159 = _t2160
            _t2158 = _t2159
        else:
            _t2158 = -1
        prediction1368 = _t2158
        if prediction1368 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2162 = self.parse_export_iceberg_config()
            export_iceberg_config1370 = _t2162
            self.consume_literal(")")
            _t2163 = transactions_pb2.Export(iceberg_config=export_iceberg_config1370)
            _t2161 = _t2163
        else:
            if prediction1368 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2165 = self.parse_export_csv_config()
                export_csv_config1369 = _t2165
                self.consume_literal(")")
                _t2166 = transactions_pb2.Export(csv_config=export_csv_config1369)
                _t2164 = _t2166
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2161 = _t2164
        result1372 = _t2161
        self.record_span(span_start1371, "Export")
        return result1372

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1380 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2168 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2169 = 1
                else:
                    _t2169 = -1
                _t2168 = _t2169
            _t2167 = _t2168
        else:
            _t2167 = -1
        prediction1373 = _t2167
        if prediction1373 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2171 = self.parse_export_csv_path()
            export_csv_path1377 = _t2171
            _t2172 = self.parse_export_csv_columns_list()
            export_csv_columns_list1378 = _t2172
            _t2173 = self.parse_config_dict()
            config_dict1379 = _t2173
            self.consume_literal(")")
            _t2174 = self.construct_export_csv_config(export_csv_path1377, export_csv_columns_list1378, config_dict1379)
            _t2170 = _t2174
        else:
            if prediction1373 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2176 = self.parse_export_csv_output_location()
                export_csv_output_location1374 = _t2176
                _t2177 = self.parse_export_csv_source()
                export_csv_source1375 = _t2177
                _t2178 = self.parse_csv_config()
                csv_config1376 = _t2178
                self.consume_literal(")")
                _t2179 = self.construct_export_csv_config_with_location(export_csv_output_location1374, export_csv_source1375, csv_config1376)
                _t2175 = _t2179
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2170 = _t2175
        result1381 = _t2170
        self.record_span(span_start1380, "ExportCSVConfig")
        return result1381

    def parse_export_csv_output_location(self) -> tuple[str, str]:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("transaction_output_name", 1):
                _t2181 = 1
            else:
                if self.match_lookahead_literal("path", 1):
                    _t2182 = 0
                else:
                    _t2182 = -1
                _t2181 = _t2182
            _t2180 = _t2181
        else:
            _t2180 = -1
        prediction1382 = _t2180
        if prediction1382 == 1:
            self.consume_literal("(")
            self.consume_literal("transaction_output_name")
            _t2184 = self.parse_name()
            name1384 = _t2184
            self.consume_literal(")")
            _t2183 = ("", name1384,)
        else:
            if prediction1382 == 0:
                self.consume_literal("(")
                self.consume_literal("path")
                string1383 = self.consume_terminal("STRING")
                self.consume_literal(")")
                _t2185 = (string1383, "",)
            else:
                raise ParseError("Unexpected token in export_csv_output_location" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2183 = _t2185
        return _t2183

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1391 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2187 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2188 = 0
                else:
                    _t2188 = -1
                _t2187 = _t2188
            _t2186 = _t2187
        else:
            _t2186 = -1
        prediction1385 = _t2186
        if prediction1385 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2190 = self.parse_relation_id()
            relation_id1390 = _t2190
            self.consume_literal(")")
            _t2191 = transactions_pb2.ExportCSVSource(table_def=relation_id1390)
            _t2189 = _t2191
        else:
            if prediction1385 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1386 = []
                cond1387 = self.match_lookahead_literal("(", 0)
                while cond1387:
                    _t2193 = self.parse_export_csv_column()
                    item1388 = _t2193
                    xs1386.append(item1388)
                    cond1387 = self.match_lookahead_literal("(", 0)
                export_csv_columns1389 = xs1386
                self.consume_literal(")")
                _t2194 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1389)
                _t2195 = transactions_pb2.ExportCSVSource(gnf_columns=_t2194)
                _t2192 = _t2195
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2189 = _t2192
        result1392 = _t2189
        self.record_span(span_start1391, "ExportCSVSource")
        return result1392

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1395 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1393 = self.consume_terminal("STRING")
        _t2196 = self.parse_relation_id()
        relation_id1394 = _t2196
        self.consume_literal(")")
        _t2197 = transactions_pb2.ExportCSVColumn(column_name=string1393, column_data=relation_id1394)
        result1396 = _t2197
        self.record_span(span_start1395, "ExportCSVColumn")
        return result1396

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1397 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1397

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1398 = []
        cond1399 = self.match_lookahead_literal("(", 0)
        while cond1399:
            _t2198 = self.parse_export_csv_column()
            item1400 = _t2198
            xs1398.append(item1400)
            cond1399 = self.match_lookahead_literal("(", 0)
        export_csv_columns1401 = xs1398
        self.consume_literal(")")
        return export_csv_columns1401

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1407 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2199 = self.parse_iceberg_locator()
        iceberg_locator1402 = _t2199
        _t2200 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1403 = _t2200
        _t2201 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1404 = _t2201
        _t2202 = self.parse_iceberg_table_properties()
        iceberg_table_properties1405 = _t2202
        if self.match_lookahead_literal("{", 0):
            _t2204 = self.parse_config_dict()
            _t2203 = _t2204
        else:
            _t2203 = None
        config_dict1406 = _t2203
        self.consume_literal(")")
        _t2205 = self.construct_export_iceberg_config_full(iceberg_locator1402, iceberg_catalog_config1403, export_iceberg_table_def1404, iceberg_table_properties1405, config_dict1406)
        result1408 = _t2205
        self.record_span(span_start1407, "ExportIcebergConfig")
        return result1408

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1410 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2206 = self.parse_relation_id()
        relation_id1409 = _t2206
        self.consume_literal(")")
        result1411 = relation_id1409
        self.record_span(span_start1410, "RelationId")
        return result1411

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1412 = []
        cond1413 = self.match_lookahead_literal("(", 0)
        while cond1413:
            _t2207 = self.parse_iceberg_property_entry()
            item1414 = _t2207
            xs1412.append(item1414)
            cond1413 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1415 = xs1412
        self.consume_literal(")")
        return iceberg_property_entrys1415


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
