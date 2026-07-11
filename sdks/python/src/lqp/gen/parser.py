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
            _t2199 = None
        assert value is not None
        if value.HasField("int32_value"):
            assert value is not None
            return value.int32_value
        else:
            _t2200 = None
        raise ParseError("expected an int32 value (e.g. `1i32`) for this config field")

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2201 = value.HasField("int_value")
        else:
            _t2201 = False
        if _t2201:
            assert value is not None
            return value.int_value
        else:
            _t2202 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2203 = value.HasField("string_value")
        else:
            _t2203 = False
        if _t2203:
            assert value is not None
            return value.string_value
        else:
            _t2204 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2205 = value.HasField("boolean_value")
        else:
            _t2205 = False
        if _t2205:
            assert value is not None
            return value.boolean_value
        else:
            _t2206 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2207 = value.HasField("string_value")
        else:
            _t2207 = False
        if _t2207:
            assert value is not None
            return [value.string_value]
        else:
            _t2208 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2209 = value.HasField("int_value")
        else:
            _t2209 = False
        if _t2209:
            assert value is not None
            return value.int_value
        else:
            _t2210 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2211 = value.HasField("float_value")
        else:
            _t2211 = False
        if _t2211:
            assert value is not None
            return value.float_value
        else:
            _t2212 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2213 = value.HasField("string_value")
        else:
            _t2213 = False
        if _t2213:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2214 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2215 = value.HasField("uint128_value")
        else:
            _t2215 = False
        if _t2215:
            assert value is not None
            return value.uint128_value
        else:
            _t2216 = None
        return None

    def construct_non_cdc_relations(self, targets: Sequence[logic_pb2.TargetRelation]) -> logic_pb2.TargetRelations:
        _t2217 = logic_pb2.PlainTargets(targets=targets)
        _t2218 = logic_pb2.TargetRelations(keys=[], plain=_t2217)
        return _t2218

    def construct_cdc_relations(self, inserts: Sequence[logic_pb2.TargetRelation], deletes: Sequence[logic_pb2.TargetRelation]) -> logic_pb2.TargetRelations:
        _t2219 = logic_pb2.CDCTargets(inserts=inserts, deletes=deletes)
        _t2220 = logic_pb2.TargetRelations(keys=[], cdc=_t2219)
        return _t2220

    def construct_relations(self, keys: Sequence[logic_pb2.NamedColumn], body: logic_pb2.TargetRelations) -> logic_pb2.TargetRelations:
        if body.HasField("plain"):
            _t2222 = logic_pb2.TargetRelations(keys=keys, plain=body.plain)
            return _t2222
        else:
            _t2221 = None
        _t2223 = logic_pb2.TargetRelations(keys=keys, cdc=body.cdc)
        return _t2223

    def construct_csv_data(self, locator: logic_pb2.CSVLocator, config: logic_pb2.CSVConfig, columns_opt: Sequence[logic_pb2.GNFColumn] | None, relations_opt: logic_pb2.TargetRelations | None, asof: str) -> logic_pb2.CSVData:
        _t2224 = logic_pb2.CSVData(locator=locator, config=config, columns=(columns_opt if columns_opt is not None else []), asof=asof, relations=relations_opt)
        return _t2224

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]], storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2225 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2225
        _t2226 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2226
        _t2227 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2227
        _t2228 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2228
        _t2229 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2229
        _t2230 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2230
        _t2231 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2231
        _t2232 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2232
        _t2233 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2233
        _t2234 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2234
        _t2235 = self._extract_value_string(config.get("csv_compression"), "")
        compression = _t2235
        _t2236 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2236
        _t2237 = self.construct_csv_storage_integration(storage_integration_opt)
        storage_integration = _t2237
        _t2238 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
        return _t2238

    def construct_csv_storage_integration(self, storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.StorageIntegration | None:
        if storage_integration_opt is None:
            return None
        else:
            _t2239 = None
        assert storage_integration_opt is not None
        config = dict(storage_integration_opt)
        _t2240 = self._extract_value_string(config.get("provider"), "")
        _t2241 = self._extract_value_string(config.get("azure_sas_token"), "")
        _t2242 = self._extract_value_string(config.get("s3_region"), "")
        _t2243 = self._extract_value_string(config.get("s3_access_key_id"), "")
        _t2244 = self._extract_value_string(config.get("s3_secret_access_key"), "")
        _t2245 = logic_pb2.StorageIntegration(provider=_t2240, azure_sas_token=_t2241, s3_region=_t2242, s3_access_key_id=_t2243, s3_secret_access_key=_t2244)
        return _t2245

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2246 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2246
        _t2247 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2247
        _t2248 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2248
        _t2249 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2249
        _t2250 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2250
        _t2251 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2251
        _t2252 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2252
        _t2253 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2253
        _t2254 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2254
        _t2255 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2255
        _t2256 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2256

    def default_configure(self) -> transactions_pb2.Configure:
        _t2257 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2257
        _t2258 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2258

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
        _t2259 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2259
        _t2260 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2260
        _t2261 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2261

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2262 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2262
        _t2263 = self._extract_value_string(config.get("compression"), "")
        compression = _t2263
        _t2264 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2264
        _t2265 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2265
        _t2266 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2266
        _t2267 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2267
        _t2268 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2268
        _t2269 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2269

    def construct_export_csv_config_with_location(self, location: tuple[str, str], csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2270 = transactions_pb2.ExportCSVConfig(path=location[0], transaction_output_name=location[1], csv_source=csv_source, csv_config=csv_config)
        return _t2270

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2271 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2271

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[logic_pb2.GNFColumn], from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2272 = logic_pb2.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2272

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2273 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2273
        _t2274 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2274
        _t2275 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2275
        table_props = dict(table_property_pairs)
        _t2276 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2276

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start713 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1415 = self.parse_configure()
            _t1414 = _t1415
        else:
            _t1414 = None
        configure707 = _t1414
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1417 = self.parse_sync()
            _t1416 = _t1417
        else:
            _t1416 = None
        sync708 = _t1416
        xs709 = []
        cond710 = self.match_lookahead_literal("(", 0)
        while cond710:
            _t1418 = self.parse_epoch()
            item711 = _t1418
            xs709.append(item711)
            cond710 = self.match_lookahead_literal("(", 0)
        epochs712 = xs709
        self.consume_literal(")")
        _t1419 = self.default_configure()
        _t1420 = transactions_pb2.Transaction(epochs=epochs712, configure=(configure707 if configure707 is not None else _t1419), sync=sync708)
        result714 = _t1420
        self.record_span(span_start713, "Transaction")
        return result714

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start716 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1421 = self.parse_config_dict()
        config_dict715 = _t1421
        self.consume_literal(")")
        _t1422 = self.construct_configure(config_dict715)
        result717 = _t1422
        self.record_span(span_start716, "Configure")
        return result717

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs718 = []
        cond719 = self.match_lookahead_literal(":", 0)
        while cond719:
            _t1423 = self.parse_config_key_value()
            item720 = _t1423
            xs718.append(item720)
            cond719 = self.match_lookahead_literal(":", 0)
        config_key_values721 = xs718
        self.consume_literal("}")
        return config_key_values721

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol722 = self.consume_terminal("SYMBOL")
        _t1424 = self.parse_raw_value()
        raw_value723 = _t1424
        return (symbol722, raw_value723,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start737 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1425 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1426 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1427 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1429 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1430 = 0
                            else:
                                _t1430 = -1
                            _t1429 = _t1430
                        _t1428 = _t1429
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1431 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1432 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1433 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1434 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1435 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1436 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1437 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1438 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1439 = 10
                                                        else:
                                                            _t1439 = -1
                                                        _t1438 = _t1439
                                                    _t1437 = _t1438
                                                _t1436 = _t1437
                                            _t1435 = _t1436
                                        _t1434 = _t1435
                                    _t1433 = _t1434
                                _t1432 = _t1433
                            _t1431 = _t1432
                        _t1428 = _t1431
                    _t1427 = _t1428
                _t1426 = _t1427
            _t1425 = _t1426
        prediction724 = _t1425
        if prediction724 == 12:
            _t1441 = self.parse_boolean_value()
            boolean_value736 = _t1441
            _t1442 = logic_pb2.Value(boolean_value=boolean_value736)
            _t1440 = _t1442
        else:
            if prediction724 == 11:
                self.consume_literal("missing")
                _t1444 = logic_pb2.MissingValue()
                _t1445 = logic_pb2.Value(missing_value=_t1444)
                _t1443 = _t1445
            else:
                if prediction724 == 10:
                    decimal735 = self.consume_terminal("DECIMAL")
                    _t1447 = logic_pb2.Value(decimal_value=decimal735)
                    _t1446 = _t1447
                else:
                    if prediction724 == 9:
                        int128734 = self.consume_terminal("INT128")
                        _t1449 = logic_pb2.Value(int128_value=int128734)
                        _t1448 = _t1449
                    else:
                        if prediction724 == 8:
                            uint128733 = self.consume_terminal("UINT128")
                            _t1451 = logic_pb2.Value(uint128_value=uint128733)
                            _t1450 = _t1451
                        else:
                            if prediction724 == 7:
                                uint32732 = self.consume_terminal("UINT32")
                                _t1453 = logic_pb2.Value(uint32_value=uint32732)
                                _t1452 = _t1453
                            else:
                                if prediction724 == 6:
                                    float731 = self.consume_terminal("FLOAT")
                                    _t1455 = logic_pb2.Value(float_value=float731)
                                    _t1454 = _t1455
                                else:
                                    if prediction724 == 5:
                                        float32730 = self.consume_terminal("FLOAT32")
                                        _t1457 = logic_pb2.Value(float32_value=float32730)
                                        _t1456 = _t1457
                                    else:
                                        if prediction724 == 4:
                                            int729 = self.consume_terminal("INT")
                                            _t1459 = logic_pb2.Value(int_value=int729)
                                            _t1458 = _t1459
                                        else:
                                            if prediction724 == 3:
                                                int32728 = self.consume_terminal("INT32")
                                                _t1461 = logic_pb2.Value(int32_value=int32728)
                                                _t1460 = _t1461
                                            else:
                                                if prediction724 == 2:
                                                    string727 = self.consume_terminal("STRING")
                                                    _t1463 = logic_pb2.Value(string_value=string727)
                                                    _t1462 = _t1463
                                                else:
                                                    if prediction724 == 1:
                                                        _t1465 = self.parse_raw_datetime()
                                                        raw_datetime726 = _t1465
                                                        _t1466 = logic_pb2.Value(datetime_value=raw_datetime726)
                                                        _t1464 = _t1466
                                                    else:
                                                        if prediction724 == 0:
                                                            _t1468 = self.parse_raw_date()
                                                            raw_date725 = _t1468
                                                            _t1469 = logic_pb2.Value(date_value=raw_date725)
                                                            _t1467 = _t1469
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1464 = _t1467
                                                    _t1462 = _t1464
                                                _t1460 = _t1462
                                            _t1458 = _t1460
                                        _t1456 = _t1458
                                    _t1454 = _t1456
                                _t1452 = _t1454
                            _t1450 = _t1452
                        _t1448 = _t1450
                    _t1446 = _t1448
                _t1443 = _t1446
            _t1440 = _t1443
        result738 = _t1440
        self.record_span(span_start737, "Value")
        return result738

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start742 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int739 = self.consume_terminal("INT")
        int_3740 = self.consume_terminal("INT")
        int_4741 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1470 = logic_pb2.DateValue(year=int(int739), month=int(int_3740), day=int(int_4741))
        result743 = _t1470
        self.record_span(span_start742, "DateValue")
        return result743

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start751 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int744 = self.consume_terminal("INT")
        int_3745 = self.consume_terminal("INT")
        int_4746 = self.consume_terminal("INT")
        int_5747 = self.consume_terminal("INT")
        int_6748 = self.consume_terminal("INT")
        int_7749 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1471 = self.consume_terminal("INT")
        else:
            _t1471 = None
        int_8750 = _t1471
        self.consume_literal(")")
        _t1472 = logic_pb2.DateTimeValue(year=int(int744), month=int(int_3745), day=int(int_4746), hour=int(int_5747), minute=int(int_6748), second=int(int_7749), microsecond=int((int_8750 if int_8750 is not None else 0)))
        result752 = _t1472
        self.record_span(span_start751, "DateTimeValue")
        return result752

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1473 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1474 = 1
            else:
                _t1474 = -1
            _t1473 = _t1474
        prediction753 = _t1473
        if prediction753 == 1:
            self.consume_literal("false")
            _t1475 = False
        else:
            if prediction753 == 0:
                self.consume_literal("true")
                _t1476 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1475 = _t1476
        return _t1475

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start758 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs754 = []
        cond755 = self.match_lookahead_literal(":", 0)
        while cond755:
            _t1477 = self.parse_fragment_id()
            item756 = _t1477
            xs754.append(item756)
            cond755 = self.match_lookahead_literal(":", 0)
        fragment_ids757 = xs754
        self.consume_literal(")")
        _t1478 = transactions_pb2.Sync(fragments=fragment_ids757)
        result759 = _t1478
        self.record_span(span_start758, "Sync")
        return result759

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start761 = self.span_start()
        self.consume_literal(":")
        symbol760 = self.consume_terminal("SYMBOL")
        result762 = fragments_pb2.FragmentId(id=symbol760.encode())
        self.record_span(span_start761, "FragmentId")
        return result762

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start765 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1480 = self.parse_epoch_writes()
            _t1479 = _t1480
        else:
            _t1479 = None
        epoch_writes763 = _t1479
        if self.match_lookahead_literal("(", 0):
            _t1482 = self.parse_epoch_reads()
            _t1481 = _t1482
        else:
            _t1481 = None
        epoch_reads764 = _t1481
        self.consume_literal(")")
        _t1483 = transactions_pb2.Epoch(writes=(epoch_writes763 if epoch_writes763 is not None else []), reads=(epoch_reads764 if epoch_reads764 is not None else []))
        result766 = _t1483
        self.record_span(span_start765, "Epoch")
        return result766

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs767 = []
        cond768 = self.match_lookahead_literal("(", 0)
        while cond768:
            _t1484 = self.parse_write()
            item769 = _t1484
            xs767.append(item769)
            cond768 = self.match_lookahead_literal("(", 0)
        writes770 = xs767
        self.consume_literal(")")
        return writes770

    def parse_write(self) -> transactions_pb2.Write:
        span_start776 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1486 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1487 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1488 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1489 = 2
                        else:
                            _t1489 = -1
                        _t1488 = _t1489
                    _t1487 = _t1488
                _t1486 = _t1487
            _t1485 = _t1486
        else:
            _t1485 = -1
        prediction771 = _t1485
        if prediction771 == 3:
            _t1491 = self.parse_snapshot()
            snapshot775 = _t1491
            _t1492 = transactions_pb2.Write(snapshot=snapshot775)
            _t1490 = _t1492
        else:
            if prediction771 == 2:
                _t1494 = self.parse_context()
                context774 = _t1494
                _t1495 = transactions_pb2.Write(context=context774)
                _t1493 = _t1495
            else:
                if prediction771 == 1:
                    _t1497 = self.parse_undefine()
                    undefine773 = _t1497
                    _t1498 = transactions_pb2.Write(undefine=undefine773)
                    _t1496 = _t1498
                else:
                    if prediction771 == 0:
                        _t1500 = self.parse_define()
                        define772 = _t1500
                        _t1501 = transactions_pb2.Write(define=define772)
                        _t1499 = _t1501
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1496 = _t1499
                _t1493 = _t1496
            _t1490 = _t1493
        result777 = _t1490
        self.record_span(span_start776, "Write")
        return result777

    def parse_define(self) -> transactions_pb2.Define:
        span_start779 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1502 = self.parse_fragment()
        fragment778 = _t1502
        self.consume_literal(")")
        _t1503 = transactions_pb2.Define(fragment=fragment778)
        result780 = _t1503
        self.record_span(span_start779, "Define")
        return result780

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start786 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1504 = self.parse_new_fragment_id()
        new_fragment_id781 = _t1504
        xs782 = []
        cond783 = self.match_lookahead_literal("(", 0)
        while cond783:
            _t1505 = self.parse_declaration()
            item784 = _t1505
            xs782.append(item784)
            cond783 = self.match_lookahead_literal("(", 0)
        declarations785 = xs782
        self.consume_literal(")")
        result787 = self.construct_fragment(new_fragment_id781, declarations785)
        self.record_span(span_start786, "Fragment")
        return result787

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start789 = self.span_start()
        _t1506 = self.parse_fragment_id()
        fragment_id788 = _t1506
        self.start_fragment(fragment_id788)
        result790 = fragment_id788
        self.record_span(span_start789, "FragmentId")
        return result790

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start796 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1508 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1509 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1510 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1511 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1512 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1513 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1514 = 1
                                    else:
                                        _t1514 = -1
                                    _t1513 = _t1514
                                _t1512 = _t1513
                            _t1511 = _t1512
                        _t1510 = _t1511
                    _t1509 = _t1510
                _t1508 = _t1509
            _t1507 = _t1508
        else:
            _t1507 = -1
        prediction791 = _t1507
        if prediction791 == 3:
            _t1516 = self.parse_data()
            data795 = _t1516
            _t1517 = logic_pb2.Declaration(data=data795)
            _t1515 = _t1517
        else:
            if prediction791 == 2:
                _t1519 = self.parse_constraint()
                constraint794 = _t1519
                _t1520 = logic_pb2.Declaration(constraint=constraint794)
                _t1518 = _t1520
            else:
                if prediction791 == 1:
                    _t1522 = self.parse_algorithm()
                    algorithm793 = _t1522
                    _t1523 = logic_pb2.Declaration(algorithm=algorithm793)
                    _t1521 = _t1523
                else:
                    if prediction791 == 0:
                        _t1525 = self.parse_def()
                        def792 = _t1525
                        _t1526 = logic_pb2.Declaration()
                        getattr(_t1526, 'def').CopyFrom(def792)
                        _t1524 = _t1526
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1521 = _t1524
                _t1518 = _t1521
            _t1515 = _t1518
        result797 = _t1515
        self.record_span(span_start796, "Declaration")
        return result797

    def parse_def(self) -> logic_pb2.Def:
        span_start801 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1527 = self.parse_relation_id()
        relation_id798 = _t1527
        _t1528 = self.parse_abstraction()
        abstraction799 = _t1528
        if self.match_lookahead_literal("(", 0):
            _t1530 = self.parse_attrs()
            _t1529 = _t1530
        else:
            _t1529 = None
        attrs800 = _t1529
        self.consume_literal(")")
        _t1531 = logic_pb2.Def(name=relation_id798, body=abstraction799, attrs=(attrs800 if attrs800 is not None else []))
        result802 = _t1531
        self.record_span(span_start801, "Def")
        return result802

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start806 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1532 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1533 = 1
            else:
                _t1533 = -1
            _t1532 = _t1533
        prediction803 = _t1532
        if prediction803 == 1:
            uint128805 = self.consume_terminal("UINT128")
            _t1534 = logic_pb2.RelationId(id_low=uint128805.low, id_high=uint128805.high)
        else:
            if prediction803 == 0:
                self.consume_literal(":")
                symbol804 = self.consume_terminal("SYMBOL")
                _t1535 = self.relation_id_from_string(symbol804)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1534 = _t1535
        result807 = _t1534
        self.record_span(span_start806, "RelationId")
        return result807

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start810 = self.span_start()
        self.consume_literal("(")
        _t1536 = self.parse_bindings()
        bindings808 = _t1536
        _t1537 = self.parse_formula()
        formula809 = _t1537
        self.consume_literal(")")
        _t1538 = logic_pb2.Abstraction(vars=(list(bindings808[0]) + list(bindings808[1] if bindings808[1] is not None else [])), value=formula809)
        result811 = _t1538
        self.record_span(span_start810, "Abstraction")
        return result811

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs812 = []
        cond813 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond813:
            _t1539 = self.parse_binding()
            item814 = _t1539
            xs812.append(item814)
            cond813 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings815 = xs812
        if self.match_lookahead_literal("|", 0):
            _t1541 = self.parse_value_bindings()
            _t1540 = _t1541
        else:
            _t1540 = None
        value_bindings816 = _t1540
        self.consume_literal("]")
        return (bindings815, (value_bindings816 if value_bindings816 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start819 = self.span_start()
        symbol817 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1542 = self.parse_type()
        type818 = _t1542
        _t1543 = logic_pb2.Var(name=symbol817)
        _t1544 = logic_pb2.Binding(var=_t1543, type=type818)
        result820 = _t1544
        self.record_span(span_start819, "Binding")
        return result820

    def parse_type(self) -> logic_pb2.Type:
        span_start836 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1545 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1546 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1547 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1548 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1549 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1550 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1551 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1552 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1553 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1554 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1555 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1556 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1557 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1558 = 9
                                                            else:
                                                                _t1558 = -1
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
        prediction821 = _t1545
        if prediction821 == 13:
            _t1560 = self.parse_uint32_type()
            uint32_type835 = _t1560
            _t1561 = logic_pb2.Type(uint32_type=uint32_type835)
            _t1559 = _t1561
        else:
            if prediction821 == 12:
                _t1563 = self.parse_float32_type()
                float32_type834 = _t1563
                _t1564 = logic_pb2.Type(float32_type=float32_type834)
                _t1562 = _t1564
            else:
                if prediction821 == 11:
                    _t1566 = self.parse_int32_type()
                    int32_type833 = _t1566
                    _t1567 = logic_pb2.Type(int32_type=int32_type833)
                    _t1565 = _t1567
                else:
                    if prediction821 == 10:
                        _t1569 = self.parse_boolean_type()
                        boolean_type832 = _t1569
                        _t1570 = logic_pb2.Type(boolean_type=boolean_type832)
                        _t1568 = _t1570
                    else:
                        if prediction821 == 9:
                            _t1572 = self.parse_decimal_type()
                            decimal_type831 = _t1572
                            _t1573 = logic_pb2.Type(decimal_type=decimal_type831)
                            _t1571 = _t1573
                        else:
                            if prediction821 == 8:
                                _t1575 = self.parse_missing_type()
                                missing_type830 = _t1575
                                _t1576 = logic_pb2.Type(missing_type=missing_type830)
                                _t1574 = _t1576
                            else:
                                if prediction821 == 7:
                                    _t1578 = self.parse_datetime_type()
                                    datetime_type829 = _t1578
                                    _t1579 = logic_pb2.Type(datetime_type=datetime_type829)
                                    _t1577 = _t1579
                                else:
                                    if prediction821 == 6:
                                        _t1581 = self.parse_date_type()
                                        date_type828 = _t1581
                                        _t1582 = logic_pb2.Type(date_type=date_type828)
                                        _t1580 = _t1582
                                    else:
                                        if prediction821 == 5:
                                            _t1584 = self.parse_int128_type()
                                            int128_type827 = _t1584
                                            _t1585 = logic_pb2.Type(int128_type=int128_type827)
                                            _t1583 = _t1585
                                        else:
                                            if prediction821 == 4:
                                                _t1587 = self.parse_uint128_type()
                                                uint128_type826 = _t1587
                                                _t1588 = logic_pb2.Type(uint128_type=uint128_type826)
                                                _t1586 = _t1588
                                            else:
                                                if prediction821 == 3:
                                                    _t1590 = self.parse_float_type()
                                                    float_type825 = _t1590
                                                    _t1591 = logic_pb2.Type(float_type=float_type825)
                                                    _t1589 = _t1591
                                                else:
                                                    if prediction821 == 2:
                                                        _t1593 = self.parse_int_type()
                                                        int_type824 = _t1593
                                                        _t1594 = logic_pb2.Type(int_type=int_type824)
                                                        _t1592 = _t1594
                                                    else:
                                                        if prediction821 == 1:
                                                            _t1596 = self.parse_string_type()
                                                            string_type823 = _t1596
                                                            _t1597 = logic_pb2.Type(string_type=string_type823)
                                                            _t1595 = _t1597
                                                        else:
                                                            if prediction821 == 0:
                                                                _t1599 = self.parse_unspecified_type()
                                                                unspecified_type822 = _t1599
                                                                _t1600 = logic_pb2.Type(unspecified_type=unspecified_type822)
                                                                _t1598 = _t1600
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1562 = _t1565
            _t1559 = _t1562
        result837 = _t1559
        self.record_span(span_start836, "Type")
        return result837

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start838 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1601 = logic_pb2.UnspecifiedType()
        result839 = _t1601
        self.record_span(span_start838, "UnspecifiedType")
        return result839

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start840 = self.span_start()
        self.consume_literal("STRING")
        _t1602 = logic_pb2.StringType()
        result841 = _t1602
        self.record_span(span_start840, "StringType")
        return result841

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start842 = self.span_start()
        self.consume_literal("INT")
        _t1603 = logic_pb2.IntType()
        result843 = _t1603
        self.record_span(span_start842, "IntType")
        return result843

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start844 = self.span_start()
        self.consume_literal("FLOAT")
        _t1604 = logic_pb2.FloatType()
        result845 = _t1604
        self.record_span(span_start844, "FloatType")
        return result845

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start846 = self.span_start()
        self.consume_literal("UINT128")
        _t1605 = logic_pb2.UInt128Type()
        result847 = _t1605
        self.record_span(span_start846, "UInt128Type")
        return result847

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start848 = self.span_start()
        self.consume_literal("INT128")
        _t1606 = logic_pb2.Int128Type()
        result849 = _t1606
        self.record_span(span_start848, "Int128Type")
        return result849

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start850 = self.span_start()
        self.consume_literal("DATE")
        _t1607 = logic_pb2.DateType()
        result851 = _t1607
        self.record_span(span_start850, "DateType")
        return result851

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start852 = self.span_start()
        self.consume_literal("DATETIME")
        _t1608 = logic_pb2.DateTimeType()
        result853 = _t1608
        self.record_span(span_start852, "DateTimeType")
        return result853

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start854 = self.span_start()
        self.consume_literal("MISSING")
        _t1609 = logic_pb2.MissingType()
        result855 = _t1609
        self.record_span(span_start854, "MissingType")
        return result855

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start858 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int856 = self.consume_terminal("INT")
        int_3857 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1610 = logic_pb2.DecimalType(precision=int(int856), scale=int(int_3857))
        result859 = _t1610
        self.record_span(span_start858, "DecimalType")
        return result859

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start860 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1611 = logic_pb2.BooleanType()
        result861 = _t1611
        self.record_span(span_start860, "BooleanType")
        return result861

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start862 = self.span_start()
        self.consume_literal("INT32")
        _t1612 = logic_pb2.Int32Type()
        result863 = _t1612
        self.record_span(span_start862, "Int32Type")
        return result863

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start864 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1613 = logic_pb2.Float32Type()
        result865 = _t1613
        self.record_span(span_start864, "Float32Type")
        return result865

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start866 = self.span_start()
        self.consume_literal("UINT32")
        _t1614 = logic_pb2.UInt32Type()
        result867 = _t1614
        self.record_span(span_start866, "UInt32Type")
        return result867

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs868 = []
        cond869 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond869:
            _t1615 = self.parse_binding()
            item870 = _t1615
            xs868.append(item870)
            cond869 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings871 = xs868
        return bindings871

    def parse_formula(self) -> logic_pb2.Formula:
        span_start886 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1617 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1618 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1619 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1620 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1621 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1622 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1623 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1624 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1625 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1626 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1627 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1628 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1629 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1630 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1631 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1632 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1633 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1634 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1635 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1636 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1637 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1638 = 10
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
                                        _t1623 = _t1624
                                    _t1622 = _t1623
                                _t1621 = _t1622
                            _t1620 = _t1621
                        _t1619 = _t1620
                    _t1618 = _t1619
                _t1617 = _t1618
            _t1616 = _t1617
        else:
            _t1616 = -1
        prediction872 = _t1616
        if prediction872 == 12:
            _t1640 = self.parse_cast()
            cast885 = _t1640
            _t1641 = logic_pb2.Formula(cast=cast885)
            _t1639 = _t1641
        else:
            if prediction872 == 11:
                _t1643 = self.parse_rel_atom()
                rel_atom884 = _t1643
                _t1644 = logic_pb2.Formula(rel_atom=rel_atom884)
                _t1642 = _t1644
            else:
                if prediction872 == 10:
                    _t1646 = self.parse_primitive()
                    primitive883 = _t1646
                    _t1647 = logic_pb2.Formula(primitive=primitive883)
                    _t1645 = _t1647
                else:
                    if prediction872 == 9:
                        _t1649 = self.parse_pragma()
                        pragma882 = _t1649
                        _t1650 = logic_pb2.Formula(pragma=pragma882)
                        _t1648 = _t1650
                    else:
                        if prediction872 == 8:
                            _t1652 = self.parse_atom()
                            atom881 = _t1652
                            _t1653 = logic_pb2.Formula(atom=atom881)
                            _t1651 = _t1653
                        else:
                            if prediction872 == 7:
                                _t1655 = self.parse_ffi()
                                ffi880 = _t1655
                                _t1656 = logic_pb2.Formula(ffi=ffi880)
                                _t1654 = _t1656
                            else:
                                if prediction872 == 6:
                                    _t1658 = self.parse_not()
                                    not879 = _t1658
                                    _t1659 = logic_pb2.Formula()
                                    getattr(_t1659, 'not').CopyFrom(not879)
                                    _t1657 = _t1659
                                else:
                                    if prediction872 == 5:
                                        _t1661 = self.parse_disjunction()
                                        disjunction878 = _t1661
                                        _t1662 = logic_pb2.Formula(disjunction=disjunction878)
                                        _t1660 = _t1662
                                    else:
                                        if prediction872 == 4:
                                            _t1664 = self.parse_conjunction()
                                            conjunction877 = _t1664
                                            _t1665 = logic_pb2.Formula(conjunction=conjunction877)
                                            _t1663 = _t1665
                                        else:
                                            if prediction872 == 3:
                                                _t1667 = self.parse_reduce()
                                                reduce876 = _t1667
                                                _t1668 = logic_pb2.Formula(reduce=reduce876)
                                                _t1666 = _t1668
                                            else:
                                                if prediction872 == 2:
                                                    _t1670 = self.parse_exists()
                                                    exists875 = _t1670
                                                    _t1671 = logic_pb2.Formula(exists=exists875)
                                                    _t1669 = _t1671
                                                else:
                                                    if prediction872 == 1:
                                                        _t1673 = self.parse_false()
                                                        false874 = _t1673
                                                        _t1674 = logic_pb2.Formula(disjunction=false874)
                                                        _t1672 = _t1674
                                                    else:
                                                        if prediction872 == 0:
                                                            _t1676 = self.parse_true()
                                                            true873 = _t1676
                                                            _t1677 = logic_pb2.Formula(conjunction=true873)
                                                            _t1675 = _t1677
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1672 = _t1675
                                                    _t1669 = _t1672
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
        result887 = _t1639
        self.record_span(span_start886, "Formula")
        return result887

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start888 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1678 = logic_pb2.Conjunction(args=[])
        result889 = _t1678
        self.record_span(span_start888, "Conjunction")
        return result889

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start890 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1679 = logic_pb2.Disjunction(args=[])
        result891 = _t1679
        self.record_span(span_start890, "Disjunction")
        return result891

    def parse_exists(self) -> logic_pb2.Exists:
        span_start894 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1680 = self.parse_bindings()
        bindings892 = _t1680
        _t1681 = self.parse_formula()
        formula893 = _t1681
        self.consume_literal(")")
        _t1682 = logic_pb2.Abstraction(vars=(list(bindings892[0]) + list(bindings892[1] if bindings892[1] is not None else [])), value=formula893)
        _t1683 = logic_pb2.Exists(body=_t1682)
        result895 = _t1683
        self.record_span(span_start894, "Exists")
        return result895

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start899 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1684 = self.parse_abstraction()
        abstraction896 = _t1684
        _t1685 = self.parse_abstraction()
        abstraction_3897 = _t1685
        _t1686 = self.parse_terms()
        terms898 = _t1686
        self.consume_literal(")")
        _t1687 = logic_pb2.Reduce(op=abstraction896, body=abstraction_3897, terms=terms898)
        result900 = _t1687
        self.record_span(span_start899, "Reduce")
        return result900

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs901 = []
        cond902 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond902:
            _t1688 = self.parse_term()
            item903 = _t1688
            xs901.append(item903)
            cond902 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms904 = xs901
        self.consume_literal(")")
        return terms904

    def parse_term(self) -> logic_pb2.Term:
        span_start908 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1689 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1690 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1691 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1692 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1693 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1694 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1695 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1696 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1697 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1698 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1699 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1700 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1701 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1702 = 1
                                                            else:
                                                                _t1702 = -1
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
                _t1690 = _t1691
            _t1689 = _t1690
        prediction905 = _t1689
        if prediction905 == 1:
            _t1704 = self.parse_value()
            value907 = _t1704
            _t1705 = logic_pb2.Term(constant=value907)
            _t1703 = _t1705
        else:
            if prediction905 == 0:
                _t1707 = self.parse_var()
                var906 = _t1707
                _t1708 = logic_pb2.Term(var=var906)
                _t1706 = _t1708
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1703 = _t1706
        result909 = _t1703
        self.record_span(span_start908, "Term")
        return result909

    def parse_var(self) -> logic_pb2.Var:
        span_start911 = self.span_start()
        symbol910 = self.consume_terminal("SYMBOL")
        _t1709 = logic_pb2.Var(name=symbol910)
        result912 = _t1709
        self.record_span(span_start911, "Var")
        return result912

    def parse_value(self) -> logic_pb2.Value:
        span_start926 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1710 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1711 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1712 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1714 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1715 = 0
                            else:
                                _t1715 = -1
                            _t1714 = _t1715
                        _t1713 = _t1714
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1716 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1717 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1718 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1719 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1720 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1721 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1722 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1723 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1724 = 10
                                                        else:
                                                            _t1724 = -1
                                                        _t1723 = _t1724
                                                    _t1722 = _t1723
                                                _t1721 = _t1722
                                            _t1720 = _t1721
                                        _t1719 = _t1720
                                    _t1718 = _t1719
                                _t1717 = _t1718
                            _t1716 = _t1717
                        _t1713 = _t1716
                    _t1712 = _t1713
                _t1711 = _t1712
            _t1710 = _t1711
        prediction913 = _t1710
        if prediction913 == 12:
            _t1726 = self.parse_boolean_value()
            boolean_value925 = _t1726
            _t1727 = logic_pb2.Value(boolean_value=boolean_value925)
            _t1725 = _t1727
        else:
            if prediction913 == 11:
                self.consume_literal("missing")
                _t1729 = logic_pb2.MissingValue()
                _t1730 = logic_pb2.Value(missing_value=_t1729)
                _t1728 = _t1730
            else:
                if prediction913 == 10:
                    formatted_decimal924 = self.consume_terminal("DECIMAL")
                    _t1732 = logic_pb2.Value(decimal_value=formatted_decimal924)
                    _t1731 = _t1732
                else:
                    if prediction913 == 9:
                        formatted_int128923 = self.consume_terminal("INT128")
                        _t1734 = logic_pb2.Value(int128_value=formatted_int128923)
                        _t1733 = _t1734
                    else:
                        if prediction913 == 8:
                            formatted_uint128922 = self.consume_terminal("UINT128")
                            _t1736 = logic_pb2.Value(uint128_value=formatted_uint128922)
                            _t1735 = _t1736
                        else:
                            if prediction913 == 7:
                                formatted_uint32921 = self.consume_terminal("UINT32")
                                _t1738 = logic_pb2.Value(uint32_value=formatted_uint32921)
                                _t1737 = _t1738
                            else:
                                if prediction913 == 6:
                                    formatted_float920 = self.consume_terminal("FLOAT")
                                    _t1740 = logic_pb2.Value(float_value=formatted_float920)
                                    _t1739 = _t1740
                                else:
                                    if prediction913 == 5:
                                        formatted_float32919 = self.consume_terminal("FLOAT32")
                                        _t1742 = logic_pb2.Value(float32_value=formatted_float32919)
                                        _t1741 = _t1742
                                    else:
                                        if prediction913 == 4:
                                            formatted_int918 = self.consume_terminal("INT")
                                            _t1744 = logic_pb2.Value(int_value=formatted_int918)
                                            _t1743 = _t1744
                                        else:
                                            if prediction913 == 3:
                                                formatted_int32917 = self.consume_terminal("INT32")
                                                _t1746 = logic_pb2.Value(int32_value=formatted_int32917)
                                                _t1745 = _t1746
                                            else:
                                                if prediction913 == 2:
                                                    formatted_string916 = self.consume_terminal("STRING")
                                                    _t1748 = logic_pb2.Value(string_value=formatted_string916)
                                                    _t1747 = _t1748
                                                else:
                                                    if prediction913 == 1:
                                                        _t1750 = self.parse_datetime()
                                                        datetime915 = _t1750
                                                        _t1751 = logic_pb2.Value(datetime_value=datetime915)
                                                        _t1749 = _t1751
                                                    else:
                                                        if prediction913 == 0:
                                                            _t1753 = self.parse_date()
                                                            date914 = _t1753
                                                            _t1754 = logic_pb2.Value(date_value=date914)
                                                            _t1752 = _t1754
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1749 = _t1752
                                                    _t1747 = _t1749
                                                _t1745 = _t1747
                                            _t1743 = _t1745
                                        _t1741 = _t1743
                                    _t1739 = _t1741
                                _t1737 = _t1739
                            _t1735 = _t1737
                        _t1733 = _t1735
                    _t1731 = _t1733
                _t1728 = _t1731
            _t1725 = _t1728
        result927 = _t1725
        self.record_span(span_start926, "Value")
        return result927

    def parse_date(self) -> logic_pb2.DateValue:
        span_start931 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int928 = self.consume_terminal("INT")
        formatted_int_3929 = self.consume_terminal("INT")
        formatted_int_4930 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1755 = logic_pb2.DateValue(year=int(formatted_int928), month=int(formatted_int_3929), day=int(formatted_int_4930))
        result932 = _t1755
        self.record_span(span_start931, "DateValue")
        return result932

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start940 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int933 = self.consume_terminal("INT")
        formatted_int_3934 = self.consume_terminal("INT")
        formatted_int_4935 = self.consume_terminal("INT")
        formatted_int_5936 = self.consume_terminal("INT")
        formatted_int_6937 = self.consume_terminal("INT")
        formatted_int_7938 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1756 = self.consume_terminal("INT")
        else:
            _t1756 = None
        formatted_int_8939 = _t1756
        self.consume_literal(")")
        _t1757 = logic_pb2.DateTimeValue(year=int(formatted_int933), month=int(formatted_int_3934), day=int(formatted_int_4935), hour=int(formatted_int_5936), minute=int(formatted_int_6937), second=int(formatted_int_7938), microsecond=int((formatted_int_8939 if formatted_int_8939 is not None else 0)))
        result941 = _t1757
        self.record_span(span_start940, "DateTimeValue")
        return result941

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start946 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs942 = []
        cond943 = self.match_lookahead_literal("(", 0)
        while cond943:
            _t1758 = self.parse_formula()
            item944 = _t1758
            xs942.append(item944)
            cond943 = self.match_lookahead_literal("(", 0)
        formulas945 = xs942
        self.consume_literal(")")
        _t1759 = logic_pb2.Conjunction(args=formulas945)
        result947 = _t1759
        self.record_span(span_start946, "Conjunction")
        return result947

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start952 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs948 = []
        cond949 = self.match_lookahead_literal("(", 0)
        while cond949:
            _t1760 = self.parse_formula()
            item950 = _t1760
            xs948.append(item950)
            cond949 = self.match_lookahead_literal("(", 0)
        formulas951 = xs948
        self.consume_literal(")")
        _t1761 = logic_pb2.Disjunction(args=formulas951)
        result953 = _t1761
        self.record_span(span_start952, "Disjunction")
        return result953

    def parse_not(self) -> logic_pb2.Not:
        span_start955 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1762 = self.parse_formula()
        formula954 = _t1762
        self.consume_literal(")")
        _t1763 = logic_pb2.Not(arg=formula954)
        result956 = _t1763
        self.record_span(span_start955, "Not")
        return result956

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start960 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1764 = self.parse_name()
        name957 = _t1764
        _t1765 = self.parse_ffi_args()
        ffi_args958 = _t1765
        _t1766 = self.parse_terms()
        terms959 = _t1766
        self.consume_literal(")")
        _t1767 = logic_pb2.FFI(name=name957, args=ffi_args958, terms=terms959)
        result961 = _t1767
        self.record_span(span_start960, "FFI")
        return result961

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol962 = self.consume_terminal("SYMBOL")
        return symbol962

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs963 = []
        cond964 = self.match_lookahead_literal("(", 0)
        while cond964:
            _t1768 = self.parse_abstraction()
            item965 = _t1768
            xs963.append(item965)
            cond964 = self.match_lookahead_literal("(", 0)
        abstractions966 = xs963
        self.consume_literal(")")
        return abstractions966

    def parse_atom(self) -> logic_pb2.Atom:
        span_start972 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1769 = self.parse_relation_id()
        relation_id967 = _t1769
        xs968 = []
        cond969 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond969:
            _t1770 = self.parse_term()
            item970 = _t1770
            xs968.append(item970)
            cond969 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms971 = xs968
        self.consume_literal(")")
        _t1771 = logic_pb2.Atom(name=relation_id967, terms=terms971)
        result973 = _t1771
        self.record_span(span_start972, "Atom")
        return result973

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start979 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1772 = self.parse_name()
        name974 = _t1772
        xs975 = []
        cond976 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond976:
            _t1773 = self.parse_term()
            item977 = _t1773
            xs975.append(item977)
            cond976 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms978 = xs975
        self.consume_literal(")")
        _t1774 = logic_pb2.Pragma(name=name974, terms=terms978)
        result980 = _t1774
        self.record_span(span_start979, "Pragma")
        return result980

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start996 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1776 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1777 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1778 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1779 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1780 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1781 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1782 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1783 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1784 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1785 = 7
                                                else:
                                                    _t1785 = -1
                                                _t1784 = _t1785
                                            _t1783 = _t1784
                                        _t1782 = _t1783
                                    _t1781 = _t1782
                                _t1780 = _t1781
                            _t1779 = _t1780
                        _t1778 = _t1779
                    _t1777 = _t1778
                _t1776 = _t1777
            _t1775 = _t1776
        else:
            _t1775 = -1
        prediction981 = _t1775
        if prediction981 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1787 = self.parse_name()
            name991 = _t1787
            xs992 = []
            cond993 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond993:
                _t1788 = self.parse_rel_term()
                item994 = _t1788
                xs992.append(item994)
                cond993 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms995 = xs992
            self.consume_literal(")")
            _t1789 = logic_pb2.Primitive(name=name991, terms=rel_terms995)
            _t1786 = _t1789
        else:
            if prediction981 == 8:
                _t1791 = self.parse_divide()
                divide990 = _t1791
                _t1790 = divide990
            else:
                if prediction981 == 7:
                    _t1793 = self.parse_multiply()
                    multiply989 = _t1793
                    _t1792 = multiply989
                else:
                    if prediction981 == 6:
                        _t1795 = self.parse_minus()
                        minus988 = _t1795
                        _t1794 = minus988
                    else:
                        if prediction981 == 5:
                            _t1797 = self.parse_add()
                            add987 = _t1797
                            _t1796 = add987
                        else:
                            if prediction981 == 4:
                                _t1799 = self.parse_gt_eq()
                                gt_eq986 = _t1799
                                _t1798 = gt_eq986
                            else:
                                if prediction981 == 3:
                                    _t1801 = self.parse_gt()
                                    gt985 = _t1801
                                    _t1800 = gt985
                                else:
                                    if prediction981 == 2:
                                        _t1803 = self.parse_lt_eq()
                                        lt_eq984 = _t1803
                                        _t1802 = lt_eq984
                                    else:
                                        if prediction981 == 1:
                                            _t1805 = self.parse_lt()
                                            lt983 = _t1805
                                            _t1804 = lt983
                                        else:
                                            if prediction981 == 0:
                                                _t1807 = self.parse_eq()
                                                eq982 = _t1807
                                                _t1806 = eq982
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1804 = _t1806
                                        _t1802 = _t1804
                                    _t1800 = _t1802
                                _t1798 = _t1800
                            _t1796 = _t1798
                        _t1794 = _t1796
                    _t1792 = _t1794
                _t1790 = _t1792
            _t1786 = _t1790
        result997 = _t1786
        self.record_span(span_start996, "Primitive")
        return result997

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start1000 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1808 = self.parse_term()
        term998 = _t1808
        _t1809 = self.parse_term()
        term_3999 = _t1809
        self.consume_literal(")")
        _t1810 = logic_pb2.RelTerm(term=term998)
        _t1811 = logic_pb2.RelTerm(term=term_3999)
        _t1812 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1810, _t1811])
        result1001 = _t1812
        self.record_span(span_start1000, "Primitive")
        return result1001

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start1004 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1813 = self.parse_term()
        term1002 = _t1813
        _t1814 = self.parse_term()
        term_31003 = _t1814
        self.consume_literal(")")
        _t1815 = logic_pb2.RelTerm(term=term1002)
        _t1816 = logic_pb2.RelTerm(term=term_31003)
        _t1817 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1815, _t1816])
        result1005 = _t1817
        self.record_span(span_start1004, "Primitive")
        return result1005

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start1008 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1818 = self.parse_term()
        term1006 = _t1818
        _t1819 = self.parse_term()
        term_31007 = _t1819
        self.consume_literal(")")
        _t1820 = logic_pb2.RelTerm(term=term1006)
        _t1821 = logic_pb2.RelTerm(term=term_31007)
        _t1822 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1820, _t1821])
        result1009 = _t1822
        self.record_span(span_start1008, "Primitive")
        return result1009

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start1012 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1823 = self.parse_term()
        term1010 = _t1823
        _t1824 = self.parse_term()
        term_31011 = _t1824
        self.consume_literal(")")
        _t1825 = logic_pb2.RelTerm(term=term1010)
        _t1826 = logic_pb2.RelTerm(term=term_31011)
        _t1827 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1825, _t1826])
        result1013 = _t1827
        self.record_span(span_start1012, "Primitive")
        return result1013

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start1016 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1828 = self.parse_term()
        term1014 = _t1828
        _t1829 = self.parse_term()
        term_31015 = _t1829
        self.consume_literal(")")
        _t1830 = logic_pb2.RelTerm(term=term1014)
        _t1831 = logic_pb2.RelTerm(term=term_31015)
        _t1832 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1830, _t1831])
        result1017 = _t1832
        self.record_span(span_start1016, "Primitive")
        return result1017

    def parse_add(self) -> logic_pb2.Primitive:
        span_start1021 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1833 = self.parse_term()
        term1018 = _t1833
        _t1834 = self.parse_term()
        term_31019 = _t1834
        _t1835 = self.parse_term()
        term_41020 = _t1835
        self.consume_literal(")")
        _t1836 = logic_pb2.RelTerm(term=term1018)
        _t1837 = logic_pb2.RelTerm(term=term_31019)
        _t1838 = logic_pb2.RelTerm(term=term_41020)
        _t1839 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1836, _t1837, _t1838])
        result1022 = _t1839
        self.record_span(span_start1021, "Primitive")
        return result1022

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start1026 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1840 = self.parse_term()
        term1023 = _t1840
        _t1841 = self.parse_term()
        term_31024 = _t1841
        _t1842 = self.parse_term()
        term_41025 = _t1842
        self.consume_literal(")")
        _t1843 = logic_pb2.RelTerm(term=term1023)
        _t1844 = logic_pb2.RelTerm(term=term_31024)
        _t1845 = logic_pb2.RelTerm(term=term_41025)
        _t1846 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1843, _t1844, _t1845])
        result1027 = _t1846
        self.record_span(span_start1026, "Primitive")
        return result1027

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start1031 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1847 = self.parse_term()
        term1028 = _t1847
        _t1848 = self.parse_term()
        term_31029 = _t1848
        _t1849 = self.parse_term()
        term_41030 = _t1849
        self.consume_literal(")")
        _t1850 = logic_pb2.RelTerm(term=term1028)
        _t1851 = logic_pb2.RelTerm(term=term_31029)
        _t1852 = logic_pb2.RelTerm(term=term_41030)
        _t1853 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1850, _t1851, _t1852])
        result1032 = _t1853
        self.record_span(span_start1031, "Primitive")
        return result1032

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start1036 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1854 = self.parse_term()
        term1033 = _t1854
        _t1855 = self.parse_term()
        term_31034 = _t1855
        _t1856 = self.parse_term()
        term_41035 = _t1856
        self.consume_literal(")")
        _t1857 = logic_pb2.RelTerm(term=term1033)
        _t1858 = logic_pb2.RelTerm(term=term_31034)
        _t1859 = logic_pb2.RelTerm(term=term_41035)
        _t1860 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1857, _t1858, _t1859])
        result1037 = _t1860
        self.record_span(span_start1036, "Primitive")
        return result1037

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1041 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1861 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1862 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1863 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1864 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1865 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1866 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1867 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1868 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1869 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1870 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1871 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1872 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1873 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1874 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1875 = 1
                                                                else:
                                                                    _t1875 = -1
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
                _t1862 = _t1863
            _t1861 = _t1862
        prediction1038 = _t1861
        if prediction1038 == 1:
            _t1877 = self.parse_term()
            term1040 = _t1877
            _t1878 = logic_pb2.RelTerm(term=term1040)
            _t1876 = _t1878
        else:
            if prediction1038 == 0:
                _t1880 = self.parse_specialized_value()
                specialized_value1039 = _t1880
                _t1881 = logic_pb2.RelTerm(specialized_value=specialized_value1039)
                _t1879 = _t1881
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1876 = _t1879
        result1042 = _t1876
        self.record_span(span_start1041, "RelTerm")
        return result1042

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1044 = self.span_start()
        self.consume_literal("#")
        _t1882 = self.parse_raw_value()
        raw_value1043 = _t1882
        result1045 = raw_value1043
        self.record_span(span_start1044, "Value")
        return result1045

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1051 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1883 = self.parse_name()
        name1046 = _t1883
        xs1047 = []
        cond1048 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1048:
            _t1884 = self.parse_rel_term()
            item1049 = _t1884
            xs1047.append(item1049)
            cond1048 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1050 = xs1047
        self.consume_literal(")")
        _t1885 = logic_pb2.RelAtom(name=name1046, terms=rel_terms1050)
        result1052 = _t1885
        self.record_span(span_start1051, "RelAtom")
        return result1052

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1055 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1886 = self.parse_term()
        term1053 = _t1886
        _t1887 = self.parse_term()
        term_31054 = _t1887
        self.consume_literal(")")
        _t1888 = logic_pb2.Cast(input=term1053, result=term_31054)
        result1056 = _t1888
        self.record_span(span_start1055, "Cast")
        return result1056

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1057 = []
        cond1058 = self.match_lookahead_literal("(", 0)
        while cond1058:
            _t1889 = self.parse_attribute()
            item1059 = _t1889
            xs1057.append(item1059)
            cond1058 = self.match_lookahead_literal("(", 0)
        attributes1060 = xs1057
        self.consume_literal(")")
        return attributes1060

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1066 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1890 = self.parse_name()
        name1061 = _t1890
        xs1062 = []
        cond1063 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1063:
            _t1891 = self.parse_raw_value()
            item1064 = _t1891
            xs1062.append(item1064)
            cond1063 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1065 = xs1062
        self.consume_literal(")")
        _t1892 = logic_pb2.Attribute(name=name1061, args=raw_values1065)
        result1067 = _t1892
        self.record_span(span_start1066, "Attribute")
        return result1067

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1074 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1068 = []
        cond1069 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1069:
            _t1893 = self.parse_relation_id()
            item1070 = _t1893
            xs1068.append(item1070)
            cond1069 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1071 = xs1068
        _t1894 = self.parse_script()
        script1072 = _t1894
        if self.match_lookahead_literal("(", 0):
            _t1896 = self.parse_attrs()
            _t1895 = _t1896
        else:
            _t1895 = None
        attrs1073 = _t1895
        self.consume_literal(")")
        _t1897 = logic_pb2.Algorithm(body=script1072, attrs=(attrs1073 if attrs1073 is not None else []))
        getattr(_t1897, 'global').extend(relation_ids1071)
        result1075 = _t1897
        self.record_span(span_start1074, "Algorithm")
        return result1075

    def parse_script(self) -> logic_pb2.Script:
        span_start1080 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1076 = []
        cond1077 = self.match_lookahead_literal("(", 0)
        while cond1077:
            _t1898 = self.parse_construct()
            item1078 = _t1898
            xs1076.append(item1078)
            cond1077 = self.match_lookahead_literal("(", 0)
        constructs1079 = xs1076
        self.consume_literal(")")
        _t1899 = logic_pb2.Script(constructs=constructs1079)
        result1081 = _t1899
        self.record_span(span_start1080, "Script")
        return result1081

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1085 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1901 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1902 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1903 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1904 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1905 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1906 = 1
                                else:
                                    _t1906 = -1
                                _t1905 = _t1906
                            _t1904 = _t1905
                        _t1903 = _t1904
                    _t1902 = _t1903
                _t1901 = _t1902
            _t1900 = _t1901
        else:
            _t1900 = -1
        prediction1082 = _t1900
        if prediction1082 == 1:
            _t1908 = self.parse_instruction()
            instruction1084 = _t1908
            _t1909 = logic_pb2.Construct(instruction=instruction1084)
            _t1907 = _t1909
        else:
            if prediction1082 == 0:
                _t1911 = self.parse_loop()
                loop1083 = _t1911
                _t1912 = logic_pb2.Construct(loop=loop1083)
                _t1910 = _t1912
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1907 = _t1910
        result1086 = _t1907
        self.record_span(span_start1085, "Construct")
        return result1086

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1090 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1913 = self.parse_init()
        init1087 = _t1913
        _t1914 = self.parse_script()
        script1088 = _t1914
        if self.match_lookahead_literal("(", 0):
            _t1916 = self.parse_attrs()
            _t1915 = _t1916
        else:
            _t1915 = None
        attrs1089 = _t1915
        self.consume_literal(")")
        _t1917 = logic_pb2.Loop(init=init1087, body=script1088, attrs=(attrs1089 if attrs1089 is not None else []))
        result1091 = _t1917
        self.record_span(span_start1090, "Loop")
        return result1091

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1092 = []
        cond1093 = self.match_lookahead_literal("(", 0)
        while cond1093:
            _t1918 = self.parse_instruction()
            item1094 = _t1918
            xs1092.append(item1094)
            cond1093 = self.match_lookahead_literal("(", 0)
        instructions1095 = xs1092
        self.consume_literal(")")
        return instructions1095

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1102 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1920 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1921 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1922 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1923 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1924 = 0
                            else:
                                _t1924 = -1
                            _t1923 = _t1924
                        _t1922 = _t1923
                    _t1921 = _t1922
                _t1920 = _t1921
            _t1919 = _t1920
        else:
            _t1919 = -1
        prediction1096 = _t1919
        if prediction1096 == 4:
            _t1926 = self.parse_monus_def()
            monus_def1101 = _t1926
            _t1927 = logic_pb2.Instruction(monus_def=monus_def1101)
            _t1925 = _t1927
        else:
            if prediction1096 == 3:
                _t1929 = self.parse_monoid_def()
                monoid_def1100 = _t1929
                _t1930 = logic_pb2.Instruction(monoid_def=monoid_def1100)
                _t1928 = _t1930
            else:
                if prediction1096 == 2:
                    _t1932 = self.parse_break()
                    break1099 = _t1932
                    _t1933 = logic_pb2.Instruction()
                    getattr(_t1933, 'break').CopyFrom(break1099)
                    _t1931 = _t1933
                else:
                    if prediction1096 == 1:
                        _t1935 = self.parse_upsert()
                        upsert1098 = _t1935
                        _t1936 = logic_pb2.Instruction(upsert=upsert1098)
                        _t1934 = _t1936
                    else:
                        if prediction1096 == 0:
                            _t1938 = self.parse_assign()
                            assign1097 = _t1938
                            _t1939 = logic_pb2.Instruction(assign=assign1097)
                            _t1937 = _t1939
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1934 = _t1937
                    _t1931 = _t1934
                _t1928 = _t1931
            _t1925 = _t1928
        result1103 = _t1925
        self.record_span(span_start1102, "Instruction")
        return result1103

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1107 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1940 = self.parse_relation_id()
        relation_id1104 = _t1940
        _t1941 = self.parse_abstraction()
        abstraction1105 = _t1941
        if self.match_lookahead_literal("(", 0):
            _t1943 = self.parse_attrs()
            _t1942 = _t1943
        else:
            _t1942 = None
        attrs1106 = _t1942
        self.consume_literal(")")
        _t1944 = logic_pb2.Assign(name=relation_id1104, body=abstraction1105, attrs=(attrs1106 if attrs1106 is not None else []))
        result1108 = _t1944
        self.record_span(span_start1107, "Assign")
        return result1108

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1112 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1945 = self.parse_relation_id()
        relation_id1109 = _t1945
        _t1946 = self.parse_abstraction_with_arity()
        abstraction_with_arity1110 = _t1946
        if self.match_lookahead_literal("(", 0):
            _t1948 = self.parse_attrs()
            _t1947 = _t1948
        else:
            _t1947 = None
        attrs1111 = _t1947
        self.consume_literal(")")
        _t1949 = logic_pb2.Upsert(name=relation_id1109, body=abstraction_with_arity1110[0], attrs=(attrs1111 if attrs1111 is not None else []), value_arity=abstraction_with_arity1110[1])
        result1113 = _t1949
        self.record_span(span_start1112, "Upsert")
        return result1113

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1950 = self.parse_bindings()
        bindings1114 = _t1950
        _t1951 = self.parse_formula()
        formula1115 = _t1951
        self.consume_literal(")")
        _t1952 = logic_pb2.Abstraction(vars=(list(bindings1114[0]) + list(bindings1114[1] if bindings1114[1] is not None else [])), value=formula1115)
        return (_t1952, len(bindings1114[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1119 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1953 = self.parse_relation_id()
        relation_id1116 = _t1953
        _t1954 = self.parse_abstraction()
        abstraction1117 = _t1954
        if self.match_lookahead_literal("(", 0):
            _t1956 = self.parse_attrs()
            _t1955 = _t1956
        else:
            _t1955 = None
        attrs1118 = _t1955
        self.consume_literal(")")
        _t1957 = logic_pb2.Break(name=relation_id1116, body=abstraction1117, attrs=(attrs1118 if attrs1118 is not None else []))
        result1120 = _t1957
        self.record_span(span_start1119, "Break")
        return result1120

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1125 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1958 = self.parse_monoid()
        monoid1121 = _t1958
        _t1959 = self.parse_relation_id()
        relation_id1122 = _t1959
        _t1960 = self.parse_abstraction_with_arity()
        abstraction_with_arity1123 = _t1960
        if self.match_lookahead_literal("(", 0):
            _t1962 = self.parse_attrs()
            _t1961 = _t1962
        else:
            _t1961 = None
        attrs1124 = _t1961
        self.consume_literal(")")
        _t1963 = logic_pb2.MonoidDef(monoid=monoid1121, name=relation_id1122, body=abstraction_with_arity1123[0], attrs=(attrs1124 if attrs1124 is not None else []), value_arity=abstraction_with_arity1123[1])
        result1126 = _t1963
        self.record_span(span_start1125, "MonoidDef")
        return result1126

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1132 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1965 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1966 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1967 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1968 = 2
                        else:
                            _t1968 = -1
                        _t1967 = _t1968
                    _t1966 = _t1967
                _t1965 = _t1966
            _t1964 = _t1965
        else:
            _t1964 = -1
        prediction1127 = _t1964
        if prediction1127 == 3:
            _t1970 = self.parse_sum_monoid()
            sum_monoid1131 = _t1970
            _t1971 = logic_pb2.Monoid(sum_monoid=sum_monoid1131)
            _t1969 = _t1971
        else:
            if prediction1127 == 2:
                _t1973 = self.parse_max_monoid()
                max_monoid1130 = _t1973
                _t1974 = logic_pb2.Monoid(max_monoid=max_monoid1130)
                _t1972 = _t1974
            else:
                if prediction1127 == 1:
                    _t1976 = self.parse_min_monoid()
                    min_monoid1129 = _t1976
                    _t1977 = logic_pb2.Monoid(min_monoid=min_monoid1129)
                    _t1975 = _t1977
                else:
                    if prediction1127 == 0:
                        _t1979 = self.parse_or_monoid()
                        or_monoid1128 = _t1979
                        _t1980 = logic_pb2.Monoid(or_monoid=or_monoid1128)
                        _t1978 = _t1980
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1975 = _t1978
                _t1972 = _t1975
            _t1969 = _t1972
        result1133 = _t1969
        self.record_span(span_start1132, "Monoid")
        return result1133

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1134 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1981 = logic_pb2.OrMonoid()
        result1135 = _t1981
        self.record_span(span_start1134, "OrMonoid")
        return result1135

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1137 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1982 = self.parse_type()
        type1136 = _t1982
        self.consume_literal(")")
        _t1983 = logic_pb2.MinMonoid(type=type1136)
        result1138 = _t1983
        self.record_span(span_start1137, "MinMonoid")
        return result1138

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1140 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1984 = self.parse_type()
        type1139 = _t1984
        self.consume_literal(")")
        _t1985 = logic_pb2.MaxMonoid(type=type1139)
        result1141 = _t1985
        self.record_span(span_start1140, "MaxMonoid")
        return result1141

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1143 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1986 = self.parse_type()
        type1142 = _t1986
        self.consume_literal(")")
        _t1987 = logic_pb2.SumMonoid(type=type1142)
        result1144 = _t1987
        self.record_span(span_start1143, "SumMonoid")
        return result1144

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1149 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1988 = self.parse_monoid()
        monoid1145 = _t1988
        _t1989 = self.parse_relation_id()
        relation_id1146 = _t1989
        _t1990 = self.parse_abstraction_with_arity()
        abstraction_with_arity1147 = _t1990
        if self.match_lookahead_literal("(", 0):
            _t1992 = self.parse_attrs()
            _t1991 = _t1992
        else:
            _t1991 = None
        attrs1148 = _t1991
        self.consume_literal(")")
        _t1993 = logic_pb2.MonusDef(monoid=monoid1145, name=relation_id1146, body=abstraction_with_arity1147[0], attrs=(attrs1148 if attrs1148 is not None else []), value_arity=abstraction_with_arity1147[1])
        result1150 = _t1993
        self.record_span(span_start1149, "MonusDef")
        return result1150

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1155 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1994 = self.parse_relation_id()
        relation_id1151 = _t1994
        _t1995 = self.parse_abstraction()
        abstraction1152 = _t1995
        _t1996 = self.parse_functional_dependency_keys()
        functional_dependency_keys1153 = _t1996
        _t1997 = self.parse_functional_dependency_values()
        functional_dependency_values1154 = _t1997
        self.consume_literal(")")
        _t1998 = logic_pb2.FunctionalDependency(guard=abstraction1152, keys=functional_dependency_keys1153, values=functional_dependency_values1154)
        _t1999 = logic_pb2.Constraint(name=relation_id1151, functional_dependency=_t1998)
        result1156 = _t1999
        self.record_span(span_start1155, "Constraint")
        return result1156

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1157 = []
        cond1158 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1158:
            _t2000 = self.parse_var()
            item1159 = _t2000
            xs1157.append(item1159)
            cond1158 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1160 = xs1157
        self.consume_literal(")")
        return vars1160

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1161 = []
        cond1162 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1162:
            _t2001 = self.parse_var()
            item1163 = _t2001
            xs1161.append(item1163)
            cond1162 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1164 = xs1161
        self.consume_literal(")")
        return vars1164

    def parse_data(self) -> logic_pb2.Data:
        span_start1170 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t2003 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t2004 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t2005 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t2006 = 1
                        else:
                            _t2006 = -1
                        _t2005 = _t2006
                    _t2004 = _t2005
                _t2003 = _t2004
            _t2002 = _t2003
        else:
            _t2002 = -1
        prediction1165 = _t2002
        if prediction1165 == 3:
            _t2008 = self.parse_iceberg_data()
            iceberg_data1169 = _t2008
            _t2009 = logic_pb2.Data(iceberg_data=iceberg_data1169)
            _t2007 = _t2009
        else:
            if prediction1165 == 2:
                _t2011 = self.parse_csv_data()
                csv_data1168 = _t2011
                _t2012 = logic_pb2.Data(csv_data=csv_data1168)
                _t2010 = _t2012
            else:
                if prediction1165 == 1:
                    _t2014 = self.parse_betree_relation()
                    betree_relation1167 = _t2014
                    _t2015 = logic_pb2.Data(betree_relation=betree_relation1167)
                    _t2013 = _t2015
                else:
                    if prediction1165 == 0:
                        _t2017 = self.parse_edb()
                        edb1166 = _t2017
                        _t2018 = logic_pb2.Data(edb=edb1166)
                        _t2016 = _t2018
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t2013 = _t2016
                _t2010 = _t2013
            _t2007 = _t2010
        result1171 = _t2007
        self.record_span(span_start1170, "Data")
        return result1171

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1175 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t2019 = self.parse_relation_id()
        relation_id1172 = _t2019
        _t2020 = self.parse_edb_path()
        edb_path1173 = _t2020
        _t2021 = self.parse_edb_types()
        edb_types1174 = _t2021
        self.consume_literal(")")
        _t2022 = logic_pb2.EDB(target_id=relation_id1172, path=edb_path1173, types=edb_types1174)
        result1176 = _t2022
        self.record_span(span_start1175, "EDB")
        return result1176

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1177 = []
        cond1178 = self.match_lookahead_terminal("STRING", 0)
        while cond1178:
            item1179 = self.consume_terminal("STRING")
            xs1177.append(item1179)
            cond1178 = self.match_lookahead_terminal("STRING", 0)
        strings1180 = xs1177
        self.consume_literal("]")
        return strings1180

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1181 = []
        cond1182 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1182:
            _t2023 = self.parse_type()
            item1183 = _t2023
            xs1181.append(item1183)
            cond1182 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1184 = xs1181
        self.consume_literal("]")
        return types1184

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1187 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t2024 = self.parse_relation_id()
        relation_id1185 = _t2024
        _t2025 = self.parse_betree_info()
        betree_info1186 = _t2025
        self.consume_literal(")")
        _t2026 = logic_pb2.BeTreeRelation(name=relation_id1185, relation_info=betree_info1186)
        result1188 = _t2026
        self.record_span(span_start1187, "BeTreeRelation")
        return result1188

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1192 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t2027 = self.parse_betree_info_key_types()
        betree_info_key_types1189 = _t2027
        _t2028 = self.parse_betree_info_value_types()
        betree_info_value_types1190 = _t2028
        _t2029 = self.parse_config_dict()
        config_dict1191 = _t2029
        self.consume_literal(")")
        _t2030 = self.construct_betree_info(betree_info_key_types1189, betree_info_value_types1190, config_dict1191)
        result1193 = _t2030
        self.record_span(span_start1192, "BeTreeInfo")
        return result1193

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1194 = []
        cond1195 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1195:
            _t2031 = self.parse_type()
            item1196 = _t2031
            xs1194.append(item1196)
            cond1195 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1197 = xs1194
        self.consume_literal(")")
        return types1197

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1198 = []
        cond1199 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1199:
            _t2032 = self.parse_type()
            item1200 = _t2032
            xs1198.append(item1200)
            cond1199 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1201 = xs1198
        self.consume_literal(")")
        return types1201

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1207 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t2033 = self.parse_csvlocator()
        csvlocator1202 = _t2033
        _t2034 = self.parse_csv_config()
        csv_config1203 = _t2034
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("columns", 1)):
            _t2036 = self.parse_gnf_columns()
            _t2035 = _t2036
        else:
            _t2035 = None
        gnf_columns1204 = _t2035
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("relations", 1)):
            _t2038 = self.parse_target_relations()
            _t2037 = _t2038
        else:
            _t2037 = None
        target_relations1205 = _t2037
        _t2039 = self.parse_csv_asof()
        csv_asof1206 = _t2039
        self.consume_literal(")")
        _t2040 = self.construct_csv_data(csvlocator1202, csv_config1203, gnf_columns1204, target_relations1205, csv_asof1206)
        result1208 = _t2040
        self.record_span(span_start1207, "CSVData")
        return result1208

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1211 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t2042 = self.parse_csv_locator_paths()
            _t2041 = _t2042
        else:
            _t2041 = None
        csv_locator_paths1209 = _t2041
        if self.match_lookahead_literal("(", 0):
            _t2044 = self.parse_csv_locator_inline_data()
            _t2043 = _t2044
        else:
            _t2043 = None
        csv_locator_inline_data1210 = _t2043
        self.consume_literal(")")
        _t2045 = logic_pb2.CSVLocator(paths=(csv_locator_paths1209 if csv_locator_paths1209 is not None else []), inline_data=(csv_locator_inline_data1210 if csv_locator_inline_data1210 is not None else "").encode())
        result1212 = _t2045
        self.record_span(span_start1211, "CSVLocator")
        return result1212

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1213 = []
        cond1214 = self.match_lookahead_terminal("STRING", 0)
        while cond1214:
            item1215 = self.consume_terminal("STRING")
            xs1213.append(item1215)
            cond1214 = self.match_lookahead_terminal("STRING", 0)
        strings1216 = xs1213
        self.consume_literal(")")
        return strings1216

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        formatted_string1217 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return formatted_string1217

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1220 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t2046 = self.parse_config_dict()
        config_dict1218 = _t2046
        if self.match_lookahead_literal("(", 0):
            _t2048 = self.parse__storage_integration()
            _t2047 = _t2048
        else:
            _t2047 = None
        _storage_integration1219 = _t2047
        self.consume_literal(")")
        _t2049 = self.construct_csv_config(config_dict1218, _storage_integration1219)
        result1221 = _t2049
        self.record_span(span_start1220, "CSVConfig")
        return result1221

    def parse__storage_integration(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("(")
        self.consume_literal("storage_integration")
        _t2050 = self.parse_config_dict()
        config_dict1222 = _t2050
        self.consume_literal(")")
        return config_dict1222

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1223 = []
        cond1224 = self.match_lookahead_literal("(", 0)
        while cond1224:
            _t2051 = self.parse_gnf_column()
            item1225 = _t2051
            xs1223.append(item1225)
            cond1224 = self.match_lookahead_literal("(", 0)
        gnf_columns1226 = xs1223
        self.consume_literal(")")
        return gnf_columns1226

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1233 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t2052 = self.parse_gnf_column_path()
        gnf_column_path1227 = _t2052
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t2054 = self.parse_relation_id()
            _t2053 = _t2054
        else:
            _t2053 = None
        relation_id1228 = _t2053
        self.consume_literal("[")
        xs1229 = []
        cond1230 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1230:
            _t2055 = self.parse_type()
            item1231 = _t2055
            xs1229.append(item1231)
            cond1230 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1232 = xs1229
        self.consume_literal("]")
        self.consume_literal(")")
        _t2056 = logic_pb2.GNFColumn(column_path=gnf_column_path1227, target_id=relation_id1228, types=types1232)
        result1234 = _t2056
        self.record_span(span_start1233, "GNFColumn")
        return result1234

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t2057 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t2058 = 0
            else:
                _t2058 = -1
            _t2057 = _t2058
        prediction1235 = _t2057
        if prediction1235 == 1:
            self.consume_literal("[")
            xs1237 = []
            cond1238 = self.match_lookahead_terminal("STRING", 0)
            while cond1238:
                item1239 = self.consume_terminal("STRING")
                xs1237.append(item1239)
                cond1238 = self.match_lookahead_terminal("STRING", 0)
            strings1240 = xs1237
            self.consume_literal("]")
            _t2059 = strings1240
        else:
            if prediction1235 == 0:
                string1236 = self.consume_terminal("STRING")
                _t2060 = [string1236]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2059 = _t2060
        return _t2059

    def parse_target_relations(self) -> logic_pb2.TargetRelations:
        span_start1243 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relations")
        _t2061 = self.parse_relation_keys()
        relation_keys1241 = _t2061
        _t2062 = self.parse_relation_body()
        relation_body1242 = _t2062
        self.consume_literal(")")
        _t2063 = self.construct_relations(relation_keys1241, relation_body1242)
        result1244 = _t2063
        self.record_span(span_start1243, "TargetRelations")
        return result1244

    def parse_relation_keys(self) -> Sequence[logic_pb2.NamedColumn]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1245 = []
        cond1246 = self.match_lookahead_literal("(", 0)
        while cond1246:
            _t2064 = self.parse_named_column()
            item1247 = _t2064
            xs1245.append(item1247)
            cond1246 = self.match_lookahead_literal("(", 0)
        named_columns1248 = xs1245
        self.consume_literal(")")
        return named_columns1248

    def parse_named_column(self) -> logic_pb2.NamedColumn:
        span_start1251 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1249 = self.consume_terminal("STRING")
        _t2065 = self.parse_type()
        type1250 = _t2065
        self.consume_literal(")")
        _t2066 = logic_pb2.NamedColumn(name=string1249, type=type1250)
        result1252 = _t2066
        self.record_span(span_start1251, "NamedColumn")
        return result1252

    def parse_relation_body(self) -> logic_pb2.TargetRelations:
        span_start1257 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("relation", 1):
                _t2068 = 0
            else:
                if self.match_lookahead_literal("inserts", 1):
                    _t2069 = 1
                else:
                    _t2069 = 0
                _t2068 = _t2069
            _t2067 = _t2068
        else:
            _t2067 = 0
        prediction1253 = _t2067
        if prediction1253 == 1:
            _t2071 = self.parse_cdc_inserts()
            cdc_inserts1255 = _t2071
            _t2072 = self.parse_cdc_deletes()
            cdc_deletes1256 = _t2072
            _t2073 = self.construct_cdc_relations(cdc_inserts1255, cdc_deletes1256)
            _t2070 = _t2073
        else:
            if prediction1253 == 0:
                _t2075 = self.parse_non_cdc_relations()
                non_cdc_relations1254 = _t2075
                _t2076 = self.construct_non_cdc_relations(non_cdc_relations1254)
                _t2074 = _t2076
            else:
                raise ParseError("Unexpected token in relation_body" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2070 = _t2074
        result1258 = _t2070
        self.record_span(span_start1257, "TargetRelations")
        return result1258

    def parse_non_cdc_relations(self) -> Sequence[logic_pb2.TargetRelation]:
        xs1259 = []
        cond1260 = self.match_lookahead_literal("(", 0)
        while cond1260:
            _t2077 = self.parse_target_relation()
            item1261 = _t2077
            xs1259.append(item1261)
            cond1260 = self.match_lookahead_literal("(", 0)
        return xs1259

    def parse_target_relation(self) -> logic_pb2.TargetRelation:
        span_start1267 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relation")
        _t2078 = self.parse_relation_id()
        relation_id1262 = _t2078
        xs1263 = []
        cond1264 = self.match_lookahead_literal("(", 0)
        while cond1264:
            _t2079 = self.parse_named_column()
            item1265 = _t2079
            xs1263.append(item1265)
            cond1264 = self.match_lookahead_literal("(", 0)
        named_columns1266 = xs1263
        self.consume_literal(")")
        _t2080 = logic_pb2.TargetRelation(target_id=relation_id1262, values=named_columns1266)
        result1268 = _t2080
        self.record_span(span_start1267, "TargetRelation")
        return result1268

    def parse_cdc_inserts(self) -> Sequence[logic_pb2.TargetRelation]:
        self.consume_literal("(")
        self.consume_literal("inserts")
        xs1269 = []
        cond1270 = self.match_lookahead_literal("(", 0)
        while cond1270:
            _t2081 = self.parse_target_relation()
            item1271 = _t2081
            xs1269.append(item1271)
            cond1270 = self.match_lookahead_literal("(", 0)
        target_relations1272 = xs1269
        self.consume_literal(")")
        return target_relations1272

    def parse_cdc_deletes(self) -> Sequence[logic_pb2.TargetRelation]:
        self.consume_literal("(")
        self.consume_literal("deletes")
        xs1273 = []
        cond1274 = self.match_lookahead_literal("(", 0)
        while cond1274:
            _t2082 = self.parse_target_relation()
            item1275 = _t2082
            xs1273.append(item1275)
            cond1274 = self.match_lookahead_literal("(", 0)
        target_relations1276 = xs1273
        self.consume_literal(")")
        return target_relations1276

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1277 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1277

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1284 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t2083 = self.parse_iceberg_locator()
        iceberg_locator1278 = _t2083
        _t2084 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1279 = _t2084
        _t2085 = self.parse_gnf_columns()
        gnf_columns1280 = _t2085
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t2087 = self.parse_iceberg_from_snapshot()
            _t2086 = _t2087
        else:
            _t2086 = None
        iceberg_from_snapshot1281 = _t2086
        if self.match_lookahead_literal("(", 0):
            _t2089 = self.parse_iceberg_to_snapshot()
            _t2088 = _t2089
        else:
            _t2088 = None
        iceberg_to_snapshot1282 = _t2088
        _t2090 = self.parse_boolean_value()
        boolean_value1283 = _t2090
        self.consume_literal(")")
        _t2091 = self.construct_iceberg_data(iceberg_locator1278, iceberg_catalog_config1279, gnf_columns1280, iceberg_from_snapshot1281, iceberg_to_snapshot1282, boolean_value1283)
        result1285 = _t2091
        self.record_span(span_start1284, "IcebergData")
        return result1285

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1289 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t2092 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1286 = _t2092
        _t2093 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1287 = _t2093
        _t2094 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1288 = _t2094
        self.consume_literal(")")
        _t2095 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1286, namespace=iceberg_locator_namespace1287, warehouse=iceberg_locator_warehouse1288)
        result1290 = _t2095
        self.record_span(span_start1289, "IcebergLocator")
        return result1290

    def parse_iceberg_locator_table_name(self) -> str:
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1291 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1291

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1292 = []
        cond1293 = self.match_lookahead_terminal("STRING", 0)
        while cond1293:
            item1294 = self.consume_terminal("STRING")
            xs1292.append(item1294)
            cond1293 = self.match_lookahead_terminal("STRING", 0)
        strings1295 = xs1292
        self.consume_literal(")")
        return strings1295

    def parse_iceberg_locator_warehouse(self) -> str:
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string1296 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1296

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1301 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t2096 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1297 = _t2096
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t2098 = self.parse_iceberg_catalog_config_scope()
            _t2097 = _t2098
        else:
            _t2097 = None
        iceberg_catalog_config_scope1298 = _t2097
        _t2099 = self.parse_iceberg_properties()
        iceberg_properties1299 = _t2099
        _t2100 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1300 = _t2100
        self.consume_literal(")")
        _t2101 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1297, iceberg_catalog_config_scope1298, iceberg_properties1299, iceberg_auth_properties1300)
        result1302 = _t2101
        self.record_span(span_start1301, "IcebergCatalogConfig")
        return result1302

    def parse_iceberg_catalog_uri(self) -> str:
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1303 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1303

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1304 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1304

    def parse_iceberg_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1305 = []
        cond1306 = self.match_lookahead_literal("(", 0)
        while cond1306:
            _t2102 = self.parse_iceberg_property_entry()
            item1307 = _t2102
            xs1305.append(item1307)
            cond1306 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1308 = xs1305
        self.consume_literal(")")
        return iceberg_property_entrys1308

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1309 = self.consume_terminal("STRING")
        string_31310 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1309, string_31310,)

    def parse_iceberg_auth_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1311 = []
        cond1312 = self.match_lookahead_literal("(", 0)
        while cond1312:
            _t2103 = self.parse_iceberg_masked_property_entry()
            item1313 = _t2103
            xs1311.append(item1313)
            cond1312 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1314 = xs1311
        self.consume_literal(")")
        return iceberg_masked_property_entrys1314

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1315 = self.consume_terminal("STRING")
        string_31316 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1315, string_31316,)

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1317 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1317

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1318 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1318

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1320 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2104 = self.parse_fragment_id()
        fragment_id1319 = _t2104
        self.consume_literal(")")
        _t2105 = transactions_pb2.Undefine(fragment_id=fragment_id1319)
        result1321 = _t2105
        self.record_span(span_start1320, "Undefine")
        return result1321

    def parse_context(self) -> transactions_pb2.Context:
        span_start1326 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1322 = []
        cond1323 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1323:
            _t2106 = self.parse_relation_id()
            item1324 = _t2106
            xs1322.append(item1324)
            cond1323 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1325 = xs1322
        self.consume_literal(")")
        _t2107 = transactions_pb2.Context(relations=relation_ids1325)
        result1327 = _t2107
        self.record_span(span_start1326, "Context")
        return result1327

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1333 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t2108 = self.parse_edb_path()
        edb_path1328 = _t2108
        xs1329 = []
        cond1330 = self.match_lookahead_literal("[", 0)
        while cond1330:
            _t2109 = self.parse_snapshot_mapping()
            item1331 = _t2109
            xs1329.append(item1331)
            cond1330 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1332 = xs1329
        self.consume_literal(")")
        _t2110 = transactions_pb2.Snapshot(prefix=edb_path1328, mappings=snapshot_mappings1332)
        result1334 = _t2110
        self.record_span(span_start1333, "Snapshot")
        return result1334

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1337 = self.span_start()
        _t2111 = self.parse_edb_path()
        edb_path1335 = _t2111
        _t2112 = self.parse_relation_id()
        relation_id1336 = _t2112
        _t2113 = transactions_pb2.SnapshotMapping(destination_path=edb_path1335, source_relation=relation_id1336)
        result1338 = _t2113
        self.record_span(span_start1337, "SnapshotMapping")
        return result1338

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1339 = []
        cond1340 = self.match_lookahead_literal("(", 0)
        while cond1340:
            _t2114 = self.parse_read()
            item1341 = _t2114
            xs1339.append(item1341)
            cond1340 = self.match_lookahead_literal("(", 0)
        reads1342 = xs1339
        self.consume_literal(")")
        return reads1342

    def parse_read(self) -> transactions_pb2.Read:
        span_start1349 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2116 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2117 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t2118 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t2119 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t2120 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t2121 = 3
                                else:
                                    _t2121 = -1
                                _t2120 = _t2121
                            _t2119 = _t2120
                        _t2118 = _t2119
                    _t2117 = _t2118
                _t2116 = _t2117
            _t2115 = _t2116
        else:
            _t2115 = -1
        prediction1343 = _t2115
        if prediction1343 == 4:
            _t2123 = self.parse_export()
            export1348 = _t2123
            _t2124 = transactions_pb2.Read(export=export1348)
            _t2122 = _t2124
        else:
            if prediction1343 == 3:
                _t2126 = self.parse_abort()
                abort1347 = _t2126
                _t2127 = transactions_pb2.Read(abort=abort1347)
                _t2125 = _t2127
            else:
                if prediction1343 == 2:
                    _t2129 = self.parse_what_if()
                    what_if1346 = _t2129
                    _t2130 = transactions_pb2.Read(what_if=what_if1346)
                    _t2128 = _t2130
                else:
                    if prediction1343 == 1:
                        _t2132 = self.parse_output()
                        output1345 = _t2132
                        _t2133 = transactions_pb2.Read(output=output1345)
                        _t2131 = _t2133
                    else:
                        if prediction1343 == 0:
                            _t2135 = self.parse_demand()
                            demand1344 = _t2135
                            _t2136 = transactions_pb2.Read(demand=demand1344)
                            _t2134 = _t2136
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2131 = _t2134
                    _t2128 = _t2131
                _t2125 = _t2128
            _t2122 = _t2125
        result1350 = _t2122
        self.record_span(span_start1349, "Read")
        return result1350

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1352 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2137 = self.parse_relation_id()
        relation_id1351 = _t2137
        self.consume_literal(")")
        _t2138 = transactions_pb2.Demand(relation_id=relation_id1351)
        result1353 = _t2138
        self.record_span(span_start1352, "Demand")
        return result1353

    def parse_output(self) -> transactions_pb2.Output:
        span_start1356 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2139 = self.parse_name()
        name1354 = _t2139
        _t2140 = self.parse_relation_id()
        relation_id1355 = _t2140
        self.consume_literal(")")
        _t2141 = transactions_pb2.Output(name=name1354, relation_id=relation_id1355)
        result1357 = _t2141
        self.record_span(span_start1356, "Output")
        return result1357

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1360 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2142 = self.parse_name()
        name1358 = _t2142
        _t2143 = self.parse_epoch()
        epoch1359 = _t2143
        self.consume_literal(")")
        _t2144 = transactions_pb2.WhatIf(branch=name1358, epoch=epoch1359)
        result1361 = _t2144
        self.record_span(span_start1360, "WhatIf")
        return result1361

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1364 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2146 = self.parse_name()
            _t2145 = _t2146
        else:
            _t2145 = None
        name1362 = _t2145
        _t2147 = self.parse_relation_id()
        relation_id1363 = _t2147
        self.consume_literal(")")
        _t2148 = transactions_pb2.Abort(name=(name1362 if name1362 is not None else "abort"), relation_id=relation_id1363)
        result1365 = _t2148
        self.record_span(span_start1364, "Abort")
        return result1365

    def parse_export(self) -> transactions_pb2.Export:
        span_start1369 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2150 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2151 = 0
                else:
                    _t2151 = -1
                _t2150 = _t2151
            _t2149 = _t2150
        else:
            _t2149 = -1
        prediction1366 = _t2149
        if prediction1366 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2153 = self.parse_export_iceberg_config()
            export_iceberg_config1368 = _t2153
            self.consume_literal(")")
            _t2154 = transactions_pb2.Export(iceberg_config=export_iceberg_config1368)
            _t2152 = _t2154
        else:
            if prediction1366 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2156 = self.parse_export_csv_config()
                export_csv_config1367 = _t2156
                self.consume_literal(")")
                _t2157 = transactions_pb2.Export(csv_config=export_csv_config1367)
                _t2155 = _t2157
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2152 = _t2155
        result1370 = _t2152
        self.record_span(span_start1369, "Export")
        return result1370

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1378 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2159 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2160 = 1
                else:
                    _t2160 = -1
                _t2159 = _t2160
            _t2158 = _t2159
        else:
            _t2158 = -1
        prediction1371 = _t2158
        if prediction1371 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2162 = self.parse_export_csv_path()
            export_csv_path1375 = _t2162
            _t2163 = self.parse_export_csv_columns_list()
            export_csv_columns_list1376 = _t2163
            _t2164 = self.parse_config_dict()
            config_dict1377 = _t2164
            self.consume_literal(")")
            _t2165 = self.construct_export_csv_config(export_csv_path1375, export_csv_columns_list1376, config_dict1377)
            _t2161 = _t2165
        else:
            if prediction1371 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2167 = self.parse_export_csv_output_location()
                export_csv_output_location1372 = _t2167
                _t2168 = self.parse_export_csv_source()
                export_csv_source1373 = _t2168
                _t2169 = self.parse_csv_config()
                csv_config1374 = _t2169
                self.consume_literal(")")
                _t2170 = self.construct_export_csv_config_with_location(export_csv_output_location1372, export_csv_source1373, csv_config1374)
                _t2166 = _t2170
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2161 = _t2166
        result1379 = _t2161
        self.record_span(span_start1378, "ExportCSVConfig")
        return result1379

    def parse_export_csv_output_location(self) -> tuple[str, str]:
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("transaction_output_name", 1):
                _t2172 = 1
            else:
                if self.match_lookahead_literal("path", 1):
                    _t2173 = 0
                else:
                    _t2173 = -1
                _t2172 = _t2173
            _t2171 = _t2172
        else:
            _t2171 = -1
        prediction1380 = _t2171
        if prediction1380 == 1:
            self.consume_literal("(")
            self.consume_literal("transaction_output_name")
            _t2175 = self.parse_name()
            name1382 = _t2175
            self.consume_literal(")")
            _t2174 = ("", name1382,)
        else:
            if prediction1380 == 0:
                self.consume_literal("(")
                self.consume_literal("path")
                string1381 = self.consume_terminal("STRING")
                self.consume_literal(")")
                _t2176 = (string1381, "",)
            else:
                raise ParseError("Unexpected token in export_csv_output_location" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2174 = _t2176
        return _t2174

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1389 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2178 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2179 = 0
                else:
                    _t2179 = -1
                _t2178 = _t2179
            _t2177 = _t2178
        else:
            _t2177 = -1
        prediction1383 = _t2177
        if prediction1383 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2181 = self.parse_relation_id()
            relation_id1388 = _t2181
            self.consume_literal(")")
            _t2182 = transactions_pb2.ExportCSVSource(table_def=relation_id1388)
            _t2180 = _t2182
        else:
            if prediction1383 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1384 = []
                cond1385 = self.match_lookahead_literal("(", 0)
                while cond1385:
                    _t2184 = self.parse_export_csv_column()
                    item1386 = _t2184
                    xs1384.append(item1386)
                    cond1385 = self.match_lookahead_literal("(", 0)
                export_csv_columns1387 = xs1384
                self.consume_literal(")")
                _t2185 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1387)
                _t2186 = transactions_pb2.ExportCSVSource(gnf_columns=_t2185)
                _t2183 = _t2186
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2180 = _t2183
        result1390 = _t2180
        self.record_span(span_start1389, "ExportCSVSource")
        return result1390

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1393 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1391 = self.consume_terminal("STRING")
        _t2187 = self.parse_relation_id()
        relation_id1392 = _t2187
        self.consume_literal(")")
        _t2188 = transactions_pb2.ExportCSVColumn(column_name=string1391, column_data=relation_id1392)
        result1394 = _t2188
        self.record_span(span_start1393, "ExportCSVColumn")
        return result1394

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1395 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1395

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1396 = []
        cond1397 = self.match_lookahead_literal("(", 0)
        while cond1397:
            _t2189 = self.parse_export_csv_column()
            item1398 = _t2189
            xs1396.append(item1398)
            cond1397 = self.match_lookahead_literal("(", 0)
        export_csv_columns1399 = xs1396
        self.consume_literal(")")
        return export_csv_columns1399

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1405 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2190 = self.parse_iceberg_locator()
        iceberg_locator1400 = _t2190
        _t2191 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1401 = _t2191
        _t2192 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1402 = _t2192
        _t2193 = self.parse_iceberg_table_properties()
        iceberg_table_properties1403 = _t2193
        if self.match_lookahead_literal("{", 0):
            _t2195 = self.parse_config_dict()
            _t2194 = _t2195
        else:
            _t2194 = None
        config_dict1404 = _t2194
        self.consume_literal(")")
        _t2196 = self.construct_export_iceberg_config_full(iceberg_locator1400, iceberg_catalog_config1401, export_iceberg_table_def1402, iceberg_table_properties1403, config_dict1404)
        result1406 = _t2196
        self.record_span(span_start1405, "ExportIcebergConfig")
        return result1406

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1408 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2197 = self.parse_relation_id()
        relation_id1407 = _t2197
        self.consume_literal(")")
        result1409 = relation_id1407
        self.record_span(span_start1408, "RelationId")
        return result1409

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1410 = []
        cond1411 = self.match_lookahead_literal("(", 0)
        while cond1411:
            _t2198 = self.parse_iceberg_property_entry()
            item1412 = _t2198
            xs1410.append(item1412)
            cond1411 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1413 = xs1410
        self.consume_literal(")")
        return iceberg_property_entrys1413


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
