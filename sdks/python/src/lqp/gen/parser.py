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
            _t2116 = value.HasField("int32_value")
        else:
            _t2116 = False
        if _t2116:
            assert value is not None
            return value.int32_value
        else:
            _t2117 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2118 = value.HasField("int_value")
        else:
            _t2118 = False
        if _t2118:
            assert value is not None
            return value.int_value
        else:
            _t2119 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2120 = value.HasField("string_value")
        else:
            _t2120 = False
        if _t2120:
            assert value is not None
            return value.string_value
        else:
            _t2121 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2122 = value.HasField("boolean_value")
        else:
            _t2122 = False
        if _t2122:
            assert value is not None
            return value.boolean_value
        else:
            _t2123 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2124 = value.HasField("string_value")
        else:
            _t2124 = False
        if _t2124:
            assert value is not None
            return [value.string_value]
        else:
            _t2125 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2126 = value.HasField("int_value")
        else:
            _t2126 = False
        if _t2126:
            assert value is not None
            return value.int_value
        else:
            _t2127 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2128 = value.HasField("float_value")
        else:
            _t2128 = False
        if _t2128:
            assert value is not None
            return value.float_value
        else:
            _t2129 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2130 = value.HasField("string_value")
        else:
            _t2130 = False
        if _t2130:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2131 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2132 = value.HasField("uint128_value")
        else:
            _t2132 = False
        if _t2132:
            assert value is not None
            return value.uint128_value
        else:
            _t2133 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]], storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2134 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2134
        _t2135 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2135
        _t2136 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2136
        _t2137 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2137
        _t2138 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2138
        _t2139 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2139
        _t2140 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2140
        _t2141 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2141
        _t2142 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2142
        _t2143 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2143
        _t2144 = self._extract_value_string(config.get("csv_compression"), "")
        compression = _t2144
        _t2145 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2145
        _t2146 = self.construct_csv_storage_integration(storage_integration_opt)
        storage_integration = _t2146
        _t2147 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
        return _t2147

    def construct_csv_storage_integration(self, storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.StorageIntegration | None:
        if storage_integration_opt is None:
            return None
        else:
            _t2148 = None
        assert storage_integration_opt is not None
        config = dict(storage_integration_opt)
        _t2149 = self._extract_value_string(config.get("provider"), "")
        _t2150 = self._extract_value_string(config.get("azure_sas_token"), "")
        _t2151 = self._extract_value_string(config.get("s3_region"), "")
        _t2152 = self._extract_value_string(config.get("s3_access_key_id"), "")
        _t2153 = self._extract_value_string(config.get("s3_secret_access_key"), "")
        _t2154 = logic_pb2.StorageIntegration(provider=_t2149, azure_sas_token=_t2150, s3_region=_t2151, s3_access_key_id=_t2152, s3_secret_access_key=_t2153)
        return _t2154

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2155 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2155
        _t2156 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2156
        _t2157 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2157
        _t2158 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2158
        _t2159 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2159
        _t2160 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2160
        _t2161 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2161
        _t2162 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2162
        _t2163 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2163
        _t2164 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2164
        _t2165 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2165

    def default_configure(self) -> transactions_pb2.Configure:
        _t2166 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2166
        _t2167 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2167

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
        _t2168 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2168
        _t2169 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2169
        _t2170 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2170

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2171 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2171
        _t2172 = self._extract_value_string(config.get("compression"), "")
        compression = _t2172
        _t2173 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2173
        _t2174 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2174
        _t2175 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2175
        _t2176 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2176
        _t2177 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2177
        _t2178 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2178

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2179 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2179

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2180 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2180

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[logic_pb2.GNFColumn], from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2181 = logic_pb2.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2181

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2182 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2182
        _t2183 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2183
        _t2184 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2184
        table_props = dict(table_property_pairs)
        _t2185 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2185

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start682 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1353 = self.parse_configure()
            _t1352 = _t1353
        else:
            _t1352 = None
        configure676 = _t1352
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1355 = self.parse_sync()
            _t1354 = _t1355
        else:
            _t1354 = None
        sync677 = _t1354
        xs678 = []
        cond679 = self.match_lookahead_literal("(", 0)
        while cond679:
            _t1356 = self.parse_epoch()
            item680 = _t1356
            xs678.append(item680)
            cond679 = self.match_lookahead_literal("(", 0)
        epochs681 = xs678
        self.consume_literal(")")
        _t1357 = self.default_configure()
        _t1358 = transactions_pb2.Transaction(epochs=epochs681, configure=(configure676 if configure676 is not None else _t1357), sync=sync677)
        result683 = _t1358
        self.record_span(span_start682, "Transaction")
        return result683

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start685 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1359 = self.parse_config_dict()
        config_dict684 = _t1359
        self.consume_literal(")")
        _t1360 = self.construct_configure(config_dict684)
        result686 = _t1360
        self.record_span(span_start685, "Configure")
        return result686

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs687 = []
        cond688 = self.match_lookahead_literal(":", 0)
        while cond688:
            _t1361 = self.parse_config_key_value()
            item689 = _t1361
            xs687.append(item689)
            cond688 = self.match_lookahead_literal(":", 0)
        config_key_values690 = xs687
        self.consume_literal("}")
        return config_key_values690

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol691 = self.consume_terminal("SYMBOL")
        _t1362 = self.parse_raw_value()
        raw_value692 = _t1362
        return (symbol691, raw_value692,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start706 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1363 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1364 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1365 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1367 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1368 = 0
                            else:
                                _t1368 = -1
                            _t1367 = _t1368
                        _t1366 = _t1367
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1369 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1370 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1371 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1372 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1373 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1374 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1375 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1376 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1377 = 10
                                                        else:
                                                            _t1377 = -1
                                                        _t1376 = _t1377
                                                    _t1375 = _t1376
                                                _t1374 = _t1375
                                            _t1373 = _t1374
                                        _t1372 = _t1373
                                    _t1371 = _t1372
                                _t1370 = _t1371
                            _t1369 = _t1370
                        _t1366 = _t1369
                    _t1365 = _t1366
                _t1364 = _t1365
            _t1363 = _t1364
        prediction693 = _t1363
        if prediction693 == 12:
            _t1379 = self.parse_boolean_value()
            boolean_value705 = _t1379
            _t1380 = logic_pb2.Value(boolean_value=boolean_value705)
            _t1378 = _t1380
        else:
            if prediction693 == 11:
                self.consume_literal("missing")
                _t1382 = logic_pb2.MissingValue()
                _t1383 = logic_pb2.Value(missing_value=_t1382)
                _t1381 = _t1383
            else:
                if prediction693 == 10:
                    decimal704 = self.consume_terminal("DECIMAL")
                    _t1385 = logic_pb2.Value(decimal_value=decimal704)
                    _t1384 = _t1385
                else:
                    if prediction693 == 9:
                        int128703 = self.consume_terminal("INT128")
                        _t1387 = logic_pb2.Value(int128_value=int128703)
                        _t1386 = _t1387
                    else:
                        if prediction693 == 8:
                            uint128702 = self.consume_terminal("UINT128")
                            _t1389 = logic_pb2.Value(uint128_value=uint128702)
                            _t1388 = _t1389
                        else:
                            if prediction693 == 7:
                                uint32701 = self.consume_terminal("UINT32")
                                _t1391 = logic_pb2.Value(uint32_value=uint32701)
                                _t1390 = _t1391
                            else:
                                if prediction693 == 6:
                                    float700 = self.consume_terminal("FLOAT")
                                    _t1393 = logic_pb2.Value(float_value=float700)
                                    _t1392 = _t1393
                                else:
                                    if prediction693 == 5:
                                        float32699 = self.consume_terminal("FLOAT32")
                                        _t1395 = logic_pb2.Value(float32_value=float32699)
                                        _t1394 = _t1395
                                    else:
                                        if prediction693 == 4:
                                            int698 = self.consume_terminal("INT")
                                            _t1397 = logic_pb2.Value(int_value=int698)
                                            _t1396 = _t1397
                                        else:
                                            if prediction693 == 3:
                                                int32697 = self.consume_terminal("INT32")
                                                _t1399 = logic_pb2.Value(int32_value=int32697)
                                                _t1398 = _t1399
                                            else:
                                                if prediction693 == 2:
                                                    string696 = self.consume_terminal("STRING")
                                                    _t1401 = logic_pb2.Value(string_value=string696)
                                                    _t1400 = _t1401
                                                else:
                                                    if prediction693 == 1:
                                                        _t1403 = self.parse_raw_datetime()
                                                        raw_datetime695 = _t1403
                                                        _t1404 = logic_pb2.Value(datetime_value=raw_datetime695)
                                                        _t1402 = _t1404
                                                    else:
                                                        if prediction693 == 0:
                                                            _t1406 = self.parse_raw_date()
                                                            raw_date694 = _t1406
                                                            _t1407 = logic_pb2.Value(date_value=raw_date694)
                                                            _t1405 = _t1407
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1402 = _t1405
                                                    _t1400 = _t1402
                                                _t1398 = _t1400
                                            _t1396 = _t1398
                                        _t1394 = _t1396
                                    _t1392 = _t1394
                                _t1390 = _t1392
                            _t1388 = _t1390
                        _t1386 = _t1388
                    _t1384 = _t1386
                _t1381 = _t1384
            _t1378 = _t1381
        result707 = _t1378
        self.record_span(span_start706, "Value")
        return result707

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start711 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int708 = self.consume_terminal("INT")
        int_3709 = self.consume_terminal("INT")
        int_4710 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1408 = logic_pb2.DateValue(year=int(int708), month=int(int_3709), day=int(int_4710))
        result712 = _t1408
        self.record_span(span_start711, "DateValue")
        return result712

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start720 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int713 = self.consume_terminal("INT")
        int_3714 = self.consume_terminal("INT")
        int_4715 = self.consume_terminal("INT")
        int_5716 = self.consume_terminal("INT")
        int_6717 = self.consume_terminal("INT")
        int_7718 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1409 = self.consume_terminal("INT")
        else:
            _t1409 = None
        int_8719 = _t1409
        self.consume_literal(")")
        _t1410 = logic_pb2.DateTimeValue(year=int(int713), month=int(int_3714), day=int(int_4715), hour=int(int_5716), minute=int(int_6717), second=int(int_7718), microsecond=int((int_8719 if int_8719 is not None else 0)))
        result721 = _t1410
        self.record_span(span_start720, "DateTimeValue")
        return result721

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1411 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1412 = 1
            else:
                _t1412 = -1
            _t1411 = _t1412
        prediction722 = _t1411
        if prediction722 == 1:
            self.consume_literal("false")
            _t1413 = False
        else:
            if prediction722 == 0:
                self.consume_literal("true")
                _t1414 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1413 = _t1414
        return _t1413

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start727 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs723 = []
        cond724 = self.match_lookahead_literal(":", 0)
        while cond724:
            _t1415 = self.parse_fragment_id()
            item725 = _t1415
            xs723.append(item725)
            cond724 = self.match_lookahead_literal(":", 0)
        fragment_ids726 = xs723
        self.consume_literal(")")
        _t1416 = transactions_pb2.Sync(fragments=fragment_ids726)
        result728 = _t1416
        self.record_span(span_start727, "Sync")
        return result728

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start730 = self.span_start()
        self.consume_literal(":")
        symbol729 = self.consume_terminal("SYMBOL")
        result731 = fragments_pb2.FragmentId(id=symbol729.encode())
        self.record_span(span_start730, "FragmentId")
        return result731

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start734 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1418 = self.parse_epoch_writes()
            _t1417 = _t1418
        else:
            _t1417 = None
        epoch_writes732 = _t1417
        if self.match_lookahead_literal("(", 0):
            _t1420 = self.parse_epoch_reads()
            _t1419 = _t1420
        else:
            _t1419 = None
        epoch_reads733 = _t1419
        self.consume_literal(")")
        _t1421 = transactions_pb2.Epoch(writes=(epoch_writes732 if epoch_writes732 is not None else []), reads=(epoch_reads733 if epoch_reads733 is not None else []))
        result735 = _t1421
        self.record_span(span_start734, "Epoch")
        return result735

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs736 = []
        cond737 = self.match_lookahead_literal("(", 0)
        while cond737:
            _t1422 = self.parse_write()
            item738 = _t1422
            xs736.append(item738)
            cond737 = self.match_lookahead_literal("(", 0)
        writes739 = xs736
        self.consume_literal(")")
        return writes739

    def parse_write(self) -> transactions_pb2.Write:
        span_start745 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1424 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1425 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1426 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1427 = 2
                        else:
                            _t1427 = -1
                        _t1426 = _t1427
                    _t1425 = _t1426
                _t1424 = _t1425
            _t1423 = _t1424
        else:
            _t1423 = -1
        prediction740 = _t1423
        if prediction740 == 3:
            _t1429 = self.parse_snapshot()
            snapshot744 = _t1429
            _t1430 = transactions_pb2.Write(snapshot=snapshot744)
            _t1428 = _t1430
        else:
            if prediction740 == 2:
                _t1432 = self.parse_context()
                context743 = _t1432
                _t1433 = transactions_pb2.Write(context=context743)
                _t1431 = _t1433
            else:
                if prediction740 == 1:
                    _t1435 = self.parse_undefine()
                    undefine742 = _t1435
                    _t1436 = transactions_pb2.Write(undefine=undefine742)
                    _t1434 = _t1436
                else:
                    if prediction740 == 0:
                        _t1438 = self.parse_define()
                        define741 = _t1438
                        _t1439 = transactions_pb2.Write(define=define741)
                        _t1437 = _t1439
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1434 = _t1437
                _t1431 = _t1434
            _t1428 = _t1431
        result746 = _t1428
        self.record_span(span_start745, "Write")
        return result746

    def parse_define(self) -> transactions_pb2.Define:
        span_start748 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1440 = self.parse_fragment()
        fragment747 = _t1440
        self.consume_literal(")")
        _t1441 = transactions_pb2.Define(fragment=fragment747)
        result749 = _t1441
        self.record_span(span_start748, "Define")
        return result749

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start755 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1442 = self.parse_new_fragment_id()
        new_fragment_id750 = _t1442
        xs751 = []
        cond752 = self.match_lookahead_literal("(", 0)
        while cond752:
            _t1443 = self.parse_declaration()
            item753 = _t1443
            xs751.append(item753)
            cond752 = self.match_lookahead_literal("(", 0)
        declarations754 = xs751
        self.consume_literal(")")
        result756 = self.construct_fragment(new_fragment_id750, declarations754)
        self.record_span(span_start755, "Fragment")
        return result756

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start758 = self.span_start()
        _t1444 = self.parse_fragment_id()
        fragment_id757 = _t1444
        self.start_fragment(fragment_id757)
        result759 = fragment_id757
        self.record_span(span_start758, "FragmentId")
        return result759

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start765 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1446 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1447 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1448 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1449 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1450 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1451 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1452 = 1
                                    else:
                                        _t1452 = -1
                                    _t1451 = _t1452
                                _t1450 = _t1451
                            _t1449 = _t1450
                        _t1448 = _t1449
                    _t1447 = _t1448
                _t1446 = _t1447
            _t1445 = _t1446
        else:
            _t1445 = -1
        prediction760 = _t1445
        if prediction760 == 3:
            _t1454 = self.parse_data()
            data764 = _t1454
            _t1455 = logic_pb2.Declaration(data=data764)
            _t1453 = _t1455
        else:
            if prediction760 == 2:
                _t1457 = self.parse_constraint()
                constraint763 = _t1457
                _t1458 = logic_pb2.Declaration(constraint=constraint763)
                _t1456 = _t1458
            else:
                if prediction760 == 1:
                    _t1460 = self.parse_algorithm()
                    algorithm762 = _t1460
                    _t1461 = logic_pb2.Declaration(algorithm=algorithm762)
                    _t1459 = _t1461
                else:
                    if prediction760 == 0:
                        _t1463 = self.parse_def()
                        def761 = _t1463
                        _t1464 = logic_pb2.Declaration()
                        getattr(_t1464, 'def').CopyFrom(def761)
                        _t1462 = _t1464
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1459 = _t1462
                _t1456 = _t1459
            _t1453 = _t1456
        result766 = _t1453
        self.record_span(span_start765, "Declaration")
        return result766

    def parse_def(self) -> logic_pb2.Def:
        span_start770 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1465 = self.parse_relation_id()
        relation_id767 = _t1465
        _t1466 = self.parse_abstraction()
        abstraction768 = _t1466
        if self.match_lookahead_literal("(", 0):
            _t1468 = self.parse_attrs()
            _t1467 = _t1468
        else:
            _t1467 = None
        attrs769 = _t1467
        self.consume_literal(")")
        _t1469 = logic_pb2.Def(name=relation_id767, body=abstraction768, attrs=(attrs769 if attrs769 is not None else []))
        result771 = _t1469
        self.record_span(span_start770, "Def")
        return result771

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start775 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1470 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1471 = 1
            else:
                _t1471 = -1
            _t1470 = _t1471
        prediction772 = _t1470
        if prediction772 == 1:
            uint128774 = self.consume_terminal("UINT128")
            _t1472 = logic_pb2.RelationId(id_low=uint128774.low, id_high=uint128774.high)
        else:
            if prediction772 == 0:
                self.consume_literal(":")
                symbol773 = self.consume_terminal("SYMBOL")
                _t1473 = self.relation_id_from_string(symbol773)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1472 = _t1473
        result776 = _t1472
        self.record_span(span_start775, "RelationId")
        return result776

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start779 = self.span_start()
        self.consume_literal("(")
        _t1474 = self.parse_bindings()
        bindings777 = _t1474
        _t1475 = self.parse_formula()
        formula778 = _t1475
        self.consume_literal(")")
        _t1476 = logic_pb2.Abstraction(vars=(list(bindings777[0]) + list(bindings777[1] if bindings777[1] is not None else [])), value=formula778)
        result780 = _t1476
        self.record_span(span_start779, "Abstraction")
        return result780

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs781 = []
        cond782 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond782:
            _t1477 = self.parse_binding()
            item783 = _t1477
            xs781.append(item783)
            cond782 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings784 = xs781
        if self.match_lookahead_literal("|", 0):
            _t1479 = self.parse_value_bindings()
            _t1478 = _t1479
        else:
            _t1478 = None
        value_bindings785 = _t1478
        self.consume_literal("]")
        return (bindings784, (value_bindings785 if value_bindings785 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start788 = self.span_start()
        symbol786 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1480 = self.parse_type()
        type787 = _t1480
        _t1481 = logic_pb2.Var(name=symbol786)
        _t1482 = logic_pb2.Binding(var=_t1481, type=type787)
        result789 = _t1482
        self.record_span(span_start788, "Binding")
        return result789

    def parse_type(self) -> logic_pb2.Type:
        span_start805 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1483 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1484 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1485 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1486 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1487 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1488 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1489 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1490 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1491 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1492 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1493 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1494 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1495 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1496 = 9
                                                            else:
                                                                _t1496 = -1
                                                            _t1495 = _t1496
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
        prediction790 = _t1483
        if prediction790 == 13:
            _t1498 = self.parse_uint32_type()
            uint32_type804 = _t1498
            _t1499 = logic_pb2.Type(uint32_type=uint32_type804)
            _t1497 = _t1499
        else:
            if prediction790 == 12:
                _t1501 = self.parse_float32_type()
                float32_type803 = _t1501
                _t1502 = logic_pb2.Type(float32_type=float32_type803)
                _t1500 = _t1502
            else:
                if prediction790 == 11:
                    _t1504 = self.parse_int32_type()
                    int32_type802 = _t1504
                    _t1505 = logic_pb2.Type(int32_type=int32_type802)
                    _t1503 = _t1505
                else:
                    if prediction790 == 10:
                        _t1507 = self.parse_boolean_type()
                        boolean_type801 = _t1507
                        _t1508 = logic_pb2.Type(boolean_type=boolean_type801)
                        _t1506 = _t1508
                    else:
                        if prediction790 == 9:
                            _t1510 = self.parse_decimal_type()
                            decimal_type800 = _t1510
                            _t1511 = logic_pb2.Type(decimal_type=decimal_type800)
                            _t1509 = _t1511
                        else:
                            if prediction790 == 8:
                                _t1513 = self.parse_missing_type()
                                missing_type799 = _t1513
                                _t1514 = logic_pb2.Type(missing_type=missing_type799)
                                _t1512 = _t1514
                            else:
                                if prediction790 == 7:
                                    _t1516 = self.parse_datetime_type()
                                    datetime_type798 = _t1516
                                    _t1517 = logic_pb2.Type(datetime_type=datetime_type798)
                                    _t1515 = _t1517
                                else:
                                    if prediction790 == 6:
                                        _t1519 = self.parse_date_type()
                                        date_type797 = _t1519
                                        _t1520 = logic_pb2.Type(date_type=date_type797)
                                        _t1518 = _t1520
                                    else:
                                        if prediction790 == 5:
                                            _t1522 = self.parse_int128_type()
                                            int128_type796 = _t1522
                                            _t1523 = logic_pb2.Type(int128_type=int128_type796)
                                            _t1521 = _t1523
                                        else:
                                            if prediction790 == 4:
                                                _t1525 = self.parse_uint128_type()
                                                uint128_type795 = _t1525
                                                _t1526 = logic_pb2.Type(uint128_type=uint128_type795)
                                                _t1524 = _t1526
                                            else:
                                                if prediction790 == 3:
                                                    _t1528 = self.parse_float_type()
                                                    float_type794 = _t1528
                                                    _t1529 = logic_pb2.Type(float_type=float_type794)
                                                    _t1527 = _t1529
                                                else:
                                                    if prediction790 == 2:
                                                        _t1531 = self.parse_int_type()
                                                        int_type793 = _t1531
                                                        _t1532 = logic_pb2.Type(int_type=int_type793)
                                                        _t1530 = _t1532
                                                    else:
                                                        if prediction790 == 1:
                                                            _t1534 = self.parse_string_type()
                                                            string_type792 = _t1534
                                                            _t1535 = logic_pb2.Type(string_type=string_type792)
                                                            _t1533 = _t1535
                                                        else:
                                                            if prediction790 == 0:
                                                                _t1537 = self.parse_unspecified_type()
                                                                unspecified_type791 = _t1537
                                                                _t1538 = logic_pb2.Type(unspecified_type=unspecified_type791)
                                                                _t1536 = _t1538
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1533 = _t1536
                                                        _t1530 = _t1533
                                                    _t1527 = _t1530
                                                _t1524 = _t1527
                                            _t1521 = _t1524
                                        _t1518 = _t1521
                                    _t1515 = _t1518
                                _t1512 = _t1515
                            _t1509 = _t1512
                        _t1506 = _t1509
                    _t1503 = _t1506
                _t1500 = _t1503
            _t1497 = _t1500
        result806 = _t1497
        self.record_span(span_start805, "Type")
        return result806

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start807 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1539 = logic_pb2.UnspecifiedType()
        result808 = _t1539
        self.record_span(span_start807, "UnspecifiedType")
        return result808

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start809 = self.span_start()
        self.consume_literal("STRING")
        _t1540 = logic_pb2.StringType()
        result810 = _t1540
        self.record_span(span_start809, "StringType")
        return result810

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start811 = self.span_start()
        self.consume_literal("INT")
        _t1541 = logic_pb2.IntType()
        result812 = _t1541
        self.record_span(span_start811, "IntType")
        return result812

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start813 = self.span_start()
        self.consume_literal("FLOAT")
        _t1542 = logic_pb2.FloatType()
        result814 = _t1542
        self.record_span(span_start813, "FloatType")
        return result814

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start815 = self.span_start()
        self.consume_literal("UINT128")
        _t1543 = logic_pb2.UInt128Type()
        result816 = _t1543
        self.record_span(span_start815, "UInt128Type")
        return result816

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start817 = self.span_start()
        self.consume_literal("INT128")
        _t1544 = logic_pb2.Int128Type()
        result818 = _t1544
        self.record_span(span_start817, "Int128Type")
        return result818

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start819 = self.span_start()
        self.consume_literal("DATE")
        _t1545 = logic_pb2.DateType()
        result820 = _t1545
        self.record_span(span_start819, "DateType")
        return result820

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start821 = self.span_start()
        self.consume_literal("DATETIME")
        _t1546 = logic_pb2.DateTimeType()
        result822 = _t1546
        self.record_span(span_start821, "DateTimeType")
        return result822

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start823 = self.span_start()
        self.consume_literal("MISSING")
        _t1547 = logic_pb2.MissingType()
        result824 = _t1547
        self.record_span(span_start823, "MissingType")
        return result824

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start827 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int825 = self.consume_terminal("INT")
        int_3826 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1548 = logic_pb2.DecimalType(precision=int(int825), scale=int(int_3826))
        result828 = _t1548
        self.record_span(span_start827, "DecimalType")
        return result828

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start829 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1549 = logic_pb2.BooleanType()
        result830 = _t1549
        self.record_span(span_start829, "BooleanType")
        return result830

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start831 = self.span_start()
        self.consume_literal("INT32")
        _t1550 = logic_pb2.Int32Type()
        result832 = _t1550
        self.record_span(span_start831, "Int32Type")
        return result832

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start833 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1551 = logic_pb2.Float32Type()
        result834 = _t1551
        self.record_span(span_start833, "Float32Type")
        return result834

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start835 = self.span_start()
        self.consume_literal("UINT32")
        _t1552 = logic_pb2.UInt32Type()
        result836 = _t1552
        self.record_span(span_start835, "UInt32Type")
        return result836

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs837 = []
        cond838 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond838:
            _t1553 = self.parse_binding()
            item839 = _t1553
            xs837.append(item839)
            cond838 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings840 = xs837
        return bindings840

    def parse_formula(self) -> logic_pb2.Formula:
        span_start855 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1555 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1556 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1557 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1558 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1559 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1560 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1561 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1562 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1563 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1564 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1565 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1566 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1567 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1568 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1569 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1570 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1571 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1572 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1573 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1574 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1575 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1576 = 10
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
                                            _t1562 = _t1563
                                        _t1561 = _t1562
                                    _t1560 = _t1561
                                _t1559 = _t1560
                            _t1558 = _t1559
                        _t1557 = _t1558
                    _t1556 = _t1557
                _t1555 = _t1556
            _t1554 = _t1555
        else:
            _t1554 = -1
        prediction841 = _t1554
        if prediction841 == 12:
            _t1578 = self.parse_cast()
            cast854 = _t1578
            _t1579 = logic_pb2.Formula(cast=cast854)
            _t1577 = _t1579
        else:
            if prediction841 == 11:
                _t1581 = self.parse_rel_atom()
                rel_atom853 = _t1581
                _t1582 = logic_pb2.Formula(rel_atom=rel_atom853)
                _t1580 = _t1582
            else:
                if prediction841 == 10:
                    _t1584 = self.parse_primitive()
                    primitive852 = _t1584
                    _t1585 = logic_pb2.Formula(primitive=primitive852)
                    _t1583 = _t1585
                else:
                    if prediction841 == 9:
                        _t1587 = self.parse_pragma()
                        pragma851 = _t1587
                        _t1588 = logic_pb2.Formula(pragma=pragma851)
                        _t1586 = _t1588
                    else:
                        if prediction841 == 8:
                            _t1590 = self.parse_atom()
                            atom850 = _t1590
                            _t1591 = logic_pb2.Formula(atom=atom850)
                            _t1589 = _t1591
                        else:
                            if prediction841 == 7:
                                _t1593 = self.parse_ffi()
                                ffi849 = _t1593
                                _t1594 = logic_pb2.Formula(ffi=ffi849)
                                _t1592 = _t1594
                            else:
                                if prediction841 == 6:
                                    _t1596 = self.parse_not()
                                    not848 = _t1596
                                    _t1597 = logic_pb2.Formula()
                                    getattr(_t1597, 'not').CopyFrom(not848)
                                    _t1595 = _t1597
                                else:
                                    if prediction841 == 5:
                                        _t1599 = self.parse_disjunction()
                                        disjunction847 = _t1599
                                        _t1600 = logic_pb2.Formula(disjunction=disjunction847)
                                        _t1598 = _t1600
                                    else:
                                        if prediction841 == 4:
                                            _t1602 = self.parse_conjunction()
                                            conjunction846 = _t1602
                                            _t1603 = logic_pb2.Formula(conjunction=conjunction846)
                                            _t1601 = _t1603
                                        else:
                                            if prediction841 == 3:
                                                _t1605 = self.parse_reduce()
                                                reduce845 = _t1605
                                                _t1606 = logic_pb2.Formula(reduce=reduce845)
                                                _t1604 = _t1606
                                            else:
                                                if prediction841 == 2:
                                                    _t1608 = self.parse_exists()
                                                    exists844 = _t1608
                                                    _t1609 = logic_pb2.Formula(exists=exists844)
                                                    _t1607 = _t1609
                                                else:
                                                    if prediction841 == 1:
                                                        _t1611 = self.parse_false()
                                                        false843 = _t1611
                                                        _t1612 = logic_pb2.Formula(disjunction=false843)
                                                        _t1610 = _t1612
                                                    else:
                                                        if prediction841 == 0:
                                                            _t1614 = self.parse_true()
                                                            true842 = _t1614
                                                            _t1615 = logic_pb2.Formula(conjunction=true842)
                                                            _t1613 = _t1615
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1610 = _t1613
                                                    _t1607 = _t1610
                                                _t1604 = _t1607
                                            _t1601 = _t1604
                                        _t1598 = _t1601
                                    _t1595 = _t1598
                                _t1592 = _t1595
                            _t1589 = _t1592
                        _t1586 = _t1589
                    _t1583 = _t1586
                _t1580 = _t1583
            _t1577 = _t1580
        result856 = _t1577
        self.record_span(span_start855, "Formula")
        return result856

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start857 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1616 = logic_pb2.Conjunction(args=[])
        result858 = _t1616
        self.record_span(span_start857, "Conjunction")
        return result858

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start859 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1617 = logic_pb2.Disjunction(args=[])
        result860 = _t1617
        self.record_span(span_start859, "Disjunction")
        return result860

    def parse_exists(self) -> logic_pb2.Exists:
        span_start863 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1618 = self.parse_bindings()
        bindings861 = _t1618
        _t1619 = self.parse_formula()
        formula862 = _t1619
        self.consume_literal(")")
        _t1620 = logic_pb2.Abstraction(vars=(list(bindings861[0]) + list(bindings861[1] if bindings861[1] is not None else [])), value=formula862)
        _t1621 = logic_pb2.Exists(body=_t1620)
        result864 = _t1621
        self.record_span(span_start863, "Exists")
        return result864

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start868 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1622 = self.parse_abstraction()
        abstraction865 = _t1622
        _t1623 = self.parse_abstraction()
        abstraction_3866 = _t1623
        _t1624 = self.parse_terms()
        terms867 = _t1624
        self.consume_literal(")")
        _t1625 = logic_pb2.Reduce(op=abstraction865, body=abstraction_3866, terms=terms867)
        result869 = _t1625
        self.record_span(span_start868, "Reduce")
        return result869

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs870 = []
        cond871 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond871:
            _t1626 = self.parse_term()
            item872 = _t1626
            xs870.append(item872)
            cond871 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms873 = xs870
        self.consume_literal(")")
        return terms873

    def parse_term(self) -> logic_pb2.Term:
        span_start877 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1627 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1628 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1629 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1630 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1631 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1632 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1633 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1634 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1635 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1636 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1637 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1638 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1639 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1640 = 1
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
        prediction874 = _t1627
        if prediction874 == 1:
            _t1642 = self.parse_value()
            value876 = _t1642
            _t1643 = logic_pb2.Term(constant=value876)
            _t1641 = _t1643
        else:
            if prediction874 == 0:
                _t1645 = self.parse_var()
                var875 = _t1645
                _t1646 = logic_pb2.Term(var=var875)
                _t1644 = _t1646
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1641 = _t1644
        result878 = _t1641
        self.record_span(span_start877, "Term")
        return result878

    def parse_var(self) -> logic_pb2.Var:
        span_start880 = self.span_start()
        symbol879 = self.consume_terminal("SYMBOL")
        _t1647 = logic_pb2.Var(name=symbol879)
        result881 = _t1647
        self.record_span(span_start880, "Var")
        return result881

    def parse_value(self) -> logic_pb2.Value:
        span_start895 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1648 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1649 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1650 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1652 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1653 = 0
                            else:
                                _t1653 = -1
                            _t1652 = _t1653
                        _t1651 = _t1652
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1654 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1655 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1656 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1657 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1658 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1659 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1660 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1661 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
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
                        _t1651 = _t1654
                    _t1650 = _t1651
                _t1649 = _t1650
            _t1648 = _t1649
        prediction882 = _t1648
        if prediction882 == 12:
            _t1664 = self.parse_boolean_value()
            boolean_value894 = _t1664
            _t1665 = logic_pb2.Value(boolean_value=boolean_value894)
            _t1663 = _t1665
        else:
            if prediction882 == 11:
                self.consume_literal("missing")
                _t1667 = logic_pb2.MissingValue()
                _t1668 = logic_pb2.Value(missing_value=_t1667)
                _t1666 = _t1668
            else:
                if prediction882 == 10:
                    formatted_decimal893 = self.consume_terminal("DECIMAL")
                    _t1670 = logic_pb2.Value(decimal_value=formatted_decimal893)
                    _t1669 = _t1670
                else:
                    if prediction882 == 9:
                        formatted_int128892 = self.consume_terminal("INT128")
                        _t1672 = logic_pb2.Value(int128_value=formatted_int128892)
                        _t1671 = _t1672
                    else:
                        if prediction882 == 8:
                            formatted_uint128891 = self.consume_terminal("UINT128")
                            _t1674 = logic_pb2.Value(uint128_value=formatted_uint128891)
                            _t1673 = _t1674
                        else:
                            if prediction882 == 7:
                                formatted_uint32890 = self.consume_terminal("UINT32")
                                _t1676 = logic_pb2.Value(uint32_value=formatted_uint32890)
                                _t1675 = _t1676
                            else:
                                if prediction882 == 6:
                                    formatted_float889 = self.consume_terminal("FLOAT")
                                    _t1678 = logic_pb2.Value(float_value=formatted_float889)
                                    _t1677 = _t1678
                                else:
                                    if prediction882 == 5:
                                        formatted_float32888 = self.consume_terminal("FLOAT32")
                                        _t1680 = logic_pb2.Value(float32_value=formatted_float32888)
                                        _t1679 = _t1680
                                    else:
                                        if prediction882 == 4:
                                            formatted_int887 = self.consume_terminal("INT")
                                            _t1682 = logic_pb2.Value(int_value=formatted_int887)
                                            _t1681 = _t1682
                                        else:
                                            if prediction882 == 3:
                                                formatted_int32886 = self.consume_terminal("INT32")
                                                _t1684 = logic_pb2.Value(int32_value=formatted_int32886)
                                                _t1683 = _t1684
                                            else:
                                                if prediction882 == 2:
                                                    formatted_string885 = self.consume_terminal("STRING")
                                                    _t1686 = logic_pb2.Value(string_value=formatted_string885)
                                                    _t1685 = _t1686
                                                else:
                                                    if prediction882 == 1:
                                                        _t1688 = self.parse_datetime()
                                                        datetime884 = _t1688
                                                        _t1689 = logic_pb2.Value(datetime_value=datetime884)
                                                        _t1687 = _t1689
                                                    else:
                                                        if prediction882 == 0:
                                                            _t1691 = self.parse_date()
                                                            date883 = _t1691
                                                            _t1692 = logic_pb2.Value(date_value=date883)
                                                            _t1690 = _t1692
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1687 = _t1690
                                                    _t1685 = _t1687
                                                _t1683 = _t1685
                                            _t1681 = _t1683
                                        _t1679 = _t1681
                                    _t1677 = _t1679
                                _t1675 = _t1677
                            _t1673 = _t1675
                        _t1671 = _t1673
                    _t1669 = _t1671
                _t1666 = _t1669
            _t1663 = _t1666
        result896 = _t1663
        self.record_span(span_start895, "Value")
        return result896

    def parse_date(self) -> logic_pb2.DateValue:
        span_start900 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int897 = self.consume_terminal("INT")
        formatted_int_3898 = self.consume_terminal("INT")
        formatted_int_4899 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1693 = logic_pb2.DateValue(year=int(formatted_int897), month=int(formatted_int_3898), day=int(formatted_int_4899))
        result901 = _t1693
        self.record_span(span_start900, "DateValue")
        return result901

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start909 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int902 = self.consume_terminal("INT")
        formatted_int_3903 = self.consume_terminal("INT")
        formatted_int_4904 = self.consume_terminal("INT")
        formatted_int_5905 = self.consume_terminal("INT")
        formatted_int_6906 = self.consume_terminal("INT")
        formatted_int_7907 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1694 = self.consume_terminal("INT")
        else:
            _t1694 = None
        formatted_int_8908 = _t1694
        self.consume_literal(")")
        _t1695 = logic_pb2.DateTimeValue(year=int(formatted_int902), month=int(formatted_int_3903), day=int(formatted_int_4904), hour=int(formatted_int_5905), minute=int(formatted_int_6906), second=int(formatted_int_7907), microsecond=int((formatted_int_8908 if formatted_int_8908 is not None else 0)))
        result910 = _t1695
        self.record_span(span_start909, "DateTimeValue")
        return result910

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start915 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs911 = []
        cond912 = self.match_lookahead_literal("(", 0)
        while cond912:
            _t1696 = self.parse_formula()
            item913 = _t1696
            xs911.append(item913)
            cond912 = self.match_lookahead_literal("(", 0)
        formulas914 = xs911
        self.consume_literal(")")
        _t1697 = logic_pb2.Conjunction(args=formulas914)
        result916 = _t1697
        self.record_span(span_start915, "Conjunction")
        return result916

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start921 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs917 = []
        cond918 = self.match_lookahead_literal("(", 0)
        while cond918:
            _t1698 = self.parse_formula()
            item919 = _t1698
            xs917.append(item919)
            cond918 = self.match_lookahead_literal("(", 0)
        formulas920 = xs917
        self.consume_literal(")")
        _t1699 = logic_pb2.Disjunction(args=formulas920)
        result922 = _t1699
        self.record_span(span_start921, "Disjunction")
        return result922

    def parse_not(self) -> logic_pb2.Not:
        span_start924 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1700 = self.parse_formula()
        formula923 = _t1700
        self.consume_literal(")")
        _t1701 = logic_pb2.Not(arg=formula923)
        result925 = _t1701
        self.record_span(span_start924, "Not")
        return result925

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start929 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1702 = self.parse_name()
        name926 = _t1702
        _t1703 = self.parse_ffi_args()
        ffi_args927 = _t1703
        _t1704 = self.parse_terms()
        terms928 = _t1704
        self.consume_literal(")")
        _t1705 = logic_pb2.FFI(name=name926, args=ffi_args927, terms=terms928)
        result930 = _t1705
        self.record_span(span_start929, "FFI")
        return result930

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol931 = self.consume_terminal("SYMBOL")
        return symbol931

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs932 = []
        cond933 = self.match_lookahead_literal("(", 0)
        while cond933:
            _t1706 = self.parse_abstraction()
            item934 = _t1706
            xs932.append(item934)
            cond933 = self.match_lookahead_literal("(", 0)
        abstractions935 = xs932
        self.consume_literal(")")
        return abstractions935

    def parse_atom(self) -> logic_pb2.Atom:
        span_start941 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1707 = self.parse_relation_id()
        relation_id936 = _t1707
        xs937 = []
        cond938 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond938:
            _t1708 = self.parse_term()
            item939 = _t1708
            xs937.append(item939)
            cond938 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms940 = xs937
        self.consume_literal(")")
        _t1709 = logic_pb2.Atom(name=relation_id936, terms=terms940)
        result942 = _t1709
        self.record_span(span_start941, "Atom")
        return result942

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start948 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1710 = self.parse_name()
        name943 = _t1710
        xs944 = []
        cond945 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond945:
            _t1711 = self.parse_term()
            item946 = _t1711
            xs944.append(item946)
            cond945 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms947 = xs944
        self.consume_literal(")")
        _t1712 = logic_pb2.Pragma(name=name943, terms=terms947)
        result949 = _t1712
        self.record_span(span_start948, "Pragma")
        return result949

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start965 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1714 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1715 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1716 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1717 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1718 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1719 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1720 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1721 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1722 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1723 = 7
                                                else:
                                                    _t1723 = -1
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
        else:
            _t1713 = -1
        prediction950 = _t1713
        if prediction950 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1725 = self.parse_name()
            name960 = _t1725
            xs961 = []
            cond962 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond962:
                _t1726 = self.parse_rel_term()
                item963 = _t1726
                xs961.append(item963)
                cond962 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms964 = xs961
            self.consume_literal(")")
            _t1727 = logic_pb2.Primitive(name=name960, terms=rel_terms964)
            _t1724 = _t1727
        else:
            if prediction950 == 8:
                _t1729 = self.parse_divide()
                divide959 = _t1729
                _t1728 = divide959
            else:
                if prediction950 == 7:
                    _t1731 = self.parse_multiply()
                    multiply958 = _t1731
                    _t1730 = multiply958
                else:
                    if prediction950 == 6:
                        _t1733 = self.parse_minus()
                        minus957 = _t1733
                        _t1732 = minus957
                    else:
                        if prediction950 == 5:
                            _t1735 = self.parse_add()
                            add956 = _t1735
                            _t1734 = add956
                        else:
                            if prediction950 == 4:
                                _t1737 = self.parse_gt_eq()
                                gt_eq955 = _t1737
                                _t1736 = gt_eq955
                            else:
                                if prediction950 == 3:
                                    _t1739 = self.parse_gt()
                                    gt954 = _t1739
                                    _t1738 = gt954
                                else:
                                    if prediction950 == 2:
                                        _t1741 = self.parse_lt_eq()
                                        lt_eq953 = _t1741
                                        _t1740 = lt_eq953
                                    else:
                                        if prediction950 == 1:
                                            _t1743 = self.parse_lt()
                                            lt952 = _t1743
                                            _t1742 = lt952
                                        else:
                                            if prediction950 == 0:
                                                _t1745 = self.parse_eq()
                                                eq951 = _t1745
                                                _t1744 = eq951
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1742 = _t1744
                                        _t1740 = _t1742
                                    _t1738 = _t1740
                                _t1736 = _t1738
                            _t1734 = _t1736
                        _t1732 = _t1734
                    _t1730 = _t1732
                _t1728 = _t1730
            _t1724 = _t1728
        result966 = _t1724
        self.record_span(span_start965, "Primitive")
        return result966

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start969 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1746 = self.parse_term()
        term967 = _t1746
        _t1747 = self.parse_term()
        term_3968 = _t1747
        self.consume_literal(")")
        _t1748 = logic_pb2.RelTerm(term=term967)
        _t1749 = logic_pb2.RelTerm(term=term_3968)
        _t1750 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1748, _t1749])
        result970 = _t1750
        self.record_span(span_start969, "Primitive")
        return result970

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start973 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1751 = self.parse_term()
        term971 = _t1751
        _t1752 = self.parse_term()
        term_3972 = _t1752
        self.consume_literal(")")
        _t1753 = logic_pb2.RelTerm(term=term971)
        _t1754 = logic_pb2.RelTerm(term=term_3972)
        _t1755 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1753, _t1754])
        result974 = _t1755
        self.record_span(span_start973, "Primitive")
        return result974

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start977 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1756 = self.parse_term()
        term975 = _t1756
        _t1757 = self.parse_term()
        term_3976 = _t1757
        self.consume_literal(")")
        _t1758 = logic_pb2.RelTerm(term=term975)
        _t1759 = logic_pb2.RelTerm(term=term_3976)
        _t1760 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1758, _t1759])
        result978 = _t1760
        self.record_span(span_start977, "Primitive")
        return result978

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start981 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1761 = self.parse_term()
        term979 = _t1761
        _t1762 = self.parse_term()
        term_3980 = _t1762
        self.consume_literal(")")
        _t1763 = logic_pb2.RelTerm(term=term979)
        _t1764 = logic_pb2.RelTerm(term=term_3980)
        _t1765 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1763, _t1764])
        result982 = _t1765
        self.record_span(span_start981, "Primitive")
        return result982

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start985 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1766 = self.parse_term()
        term983 = _t1766
        _t1767 = self.parse_term()
        term_3984 = _t1767
        self.consume_literal(")")
        _t1768 = logic_pb2.RelTerm(term=term983)
        _t1769 = logic_pb2.RelTerm(term=term_3984)
        _t1770 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1768, _t1769])
        result986 = _t1770
        self.record_span(span_start985, "Primitive")
        return result986

    def parse_add(self) -> logic_pb2.Primitive:
        span_start990 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1771 = self.parse_term()
        term987 = _t1771
        _t1772 = self.parse_term()
        term_3988 = _t1772
        _t1773 = self.parse_term()
        term_4989 = _t1773
        self.consume_literal(")")
        _t1774 = logic_pb2.RelTerm(term=term987)
        _t1775 = logic_pb2.RelTerm(term=term_3988)
        _t1776 = logic_pb2.RelTerm(term=term_4989)
        _t1777 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1774, _t1775, _t1776])
        result991 = _t1777
        self.record_span(span_start990, "Primitive")
        return result991

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start995 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1778 = self.parse_term()
        term992 = _t1778
        _t1779 = self.parse_term()
        term_3993 = _t1779
        _t1780 = self.parse_term()
        term_4994 = _t1780
        self.consume_literal(")")
        _t1781 = logic_pb2.RelTerm(term=term992)
        _t1782 = logic_pb2.RelTerm(term=term_3993)
        _t1783 = logic_pb2.RelTerm(term=term_4994)
        _t1784 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1781, _t1782, _t1783])
        result996 = _t1784
        self.record_span(span_start995, "Primitive")
        return result996

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start1000 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1785 = self.parse_term()
        term997 = _t1785
        _t1786 = self.parse_term()
        term_3998 = _t1786
        _t1787 = self.parse_term()
        term_4999 = _t1787
        self.consume_literal(")")
        _t1788 = logic_pb2.RelTerm(term=term997)
        _t1789 = logic_pb2.RelTerm(term=term_3998)
        _t1790 = logic_pb2.RelTerm(term=term_4999)
        _t1791 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1788, _t1789, _t1790])
        result1001 = _t1791
        self.record_span(span_start1000, "Primitive")
        return result1001

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start1005 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1792 = self.parse_term()
        term1002 = _t1792
        _t1793 = self.parse_term()
        term_31003 = _t1793
        _t1794 = self.parse_term()
        term_41004 = _t1794
        self.consume_literal(")")
        _t1795 = logic_pb2.RelTerm(term=term1002)
        _t1796 = logic_pb2.RelTerm(term=term_31003)
        _t1797 = logic_pb2.RelTerm(term=term_41004)
        _t1798 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1795, _t1796, _t1797])
        result1006 = _t1798
        self.record_span(span_start1005, "Primitive")
        return result1006

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1010 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1799 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1800 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1801 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1802 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1803 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1804 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1805 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1806 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1807 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1808 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1809 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1810 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1811 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1812 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1813 = 1
                                                                else:
                                                                    _t1813 = -1
                                                                _t1812 = _t1813
                                                            _t1811 = _t1812
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
                _t1800 = _t1801
            _t1799 = _t1800
        prediction1007 = _t1799
        if prediction1007 == 1:
            _t1815 = self.parse_term()
            term1009 = _t1815
            _t1816 = logic_pb2.RelTerm(term=term1009)
            _t1814 = _t1816
        else:
            if prediction1007 == 0:
                _t1818 = self.parse_specialized_value()
                specialized_value1008 = _t1818
                _t1819 = logic_pb2.RelTerm(specialized_value=specialized_value1008)
                _t1817 = _t1819
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1814 = _t1817
        result1011 = _t1814
        self.record_span(span_start1010, "RelTerm")
        return result1011

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1013 = self.span_start()
        self.consume_literal("#")
        _t1820 = self.parse_raw_value()
        raw_value1012 = _t1820
        result1014 = raw_value1012
        self.record_span(span_start1013, "Value")
        return result1014

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1020 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1821 = self.parse_name()
        name1015 = _t1821
        xs1016 = []
        cond1017 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1017:
            _t1822 = self.parse_rel_term()
            item1018 = _t1822
            xs1016.append(item1018)
            cond1017 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1019 = xs1016
        self.consume_literal(")")
        _t1823 = logic_pb2.RelAtom(name=name1015, terms=rel_terms1019)
        result1021 = _t1823
        self.record_span(span_start1020, "RelAtom")
        return result1021

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1024 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1824 = self.parse_term()
        term1022 = _t1824
        _t1825 = self.parse_term()
        term_31023 = _t1825
        self.consume_literal(")")
        _t1826 = logic_pb2.Cast(input=term1022, result=term_31023)
        result1025 = _t1826
        self.record_span(span_start1024, "Cast")
        return result1025

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1026 = []
        cond1027 = self.match_lookahead_literal("(", 0)
        while cond1027:
            _t1827 = self.parse_attribute()
            item1028 = _t1827
            xs1026.append(item1028)
            cond1027 = self.match_lookahead_literal("(", 0)
        attributes1029 = xs1026
        self.consume_literal(")")
        return attributes1029

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1035 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1828 = self.parse_name()
        name1030 = _t1828
        xs1031 = []
        cond1032 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1032:
            _t1829 = self.parse_raw_value()
            item1033 = _t1829
            xs1031.append(item1033)
            cond1032 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1034 = xs1031
        self.consume_literal(")")
        _t1830 = logic_pb2.Attribute(name=name1030, args=raw_values1034)
        result1036 = _t1830
        self.record_span(span_start1035, "Attribute")
        return result1036

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1043 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1037 = []
        cond1038 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1038:
            _t1831 = self.parse_relation_id()
            item1039 = _t1831
            xs1037.append(item1039)
            cond1038 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1040 = xs1037
        _t1832 = self.parse_script()
        script1041 = _t1832
        if self.match_lookahead_literal("(", 0):
            _t1834 = self.parse_attrs()
            _t1833 = _t1834
        else:
            _t1833 = None
        attrs1042 = _t1833
        self.consume_literal(")")
        _t1835 = logic_pb2.Algorithm(body=script1041, attrs=(attrs1042 if attrs1042 is not None else []))
        getattr(_t1835, 'global').extend(relation_ids1040)
        result1044 = _t1835
        self.record_span(span_start1043, "Algorithm")
        return result1044

    def parse_script(self) -> logic_pb2.Script:
        span_start1049 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1045 = []
        cond1046 = self.match_lookahead_literal("(", 0)
        while cond1046:
            _t1836 = self.parse_construct()
            item1047 = _t1836
            xs1045.append(item1047)
            cond1046 = self.match_lookahead_literal("(", 0)
        constructs1048 = xs1045
        self.consume_literal(")")
        _t1837 = logic_pb2.Script(constructs=constructs1048)
        result1050 = _t1837
        self.record_span(span_start1049, "Script")
        return result1050

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1054 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1839 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1840 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1841 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1842 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1843 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1844 = 1
                                else:
                                    _t1844 = -1
                                _t1843 = _t1844
                            _t1842 = _t1843
                        _t1841 = _t1842
                    _t1840 = _t1841
                _t1839 = _t1840
            _t1838 = _t1839
        else:
            _t1838 = -1
        prediction1051 = _t1838
        if prediction1051 == 1:
            _t1846 = self.parse_instruction()
            instruction1053 = _t1846
            _t1847 = logic_pb2.Construct(instruction=instruction1053)
            _t1845 = _t1847
        else:
            if prediction1051 == 0:
                _t1849 = self.parse_loop()
                loop1052 = _t1849
                _t1850 = logic_pb2.Construct(loop=loop1052)
                _t1848 = _t1850
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1845 = _t1848
        result1055 = _t1845
        self.record_span(span_start1054, "Construct")
        return result1055

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1059 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1851 = self.parse_init()
        init1056 = _t1851
        _t1852 = self.parse_script()
        script1057 = _t1852
        if self.match_lookahead_literal("(", 0):
            _t1854 = self.parse_attrs()
            _t1853 = _t1854
        else:
            _t1853 = None
        attrs1058 = _t1853
        self.consume_literal(")")
        _t1855 = logic_pb2.Loop(init=init1056, body=script1057, attrs=(attrs1058 if attrs1058 is not None else []))
        result1060 = _t1855
        self.record_span(span_start1059, "Loop")
        return result1060

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1061 = []
        cond1062 = self.match_lookahead_literal("(", 0)
        while cond1062:
            _t1856 = self.parse_instruction()
            item1063 = _t1856
            xs1061.append(item1063)
            cond1062 = self.match_lookahead_literal("(", 0)
        instructions1064 = xs1061
        self.consume_literal(")")
        return instructions1064

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1071 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1858 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1859 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1860 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1861 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1862 = 0
                            else:
                                _t1862 = -1
                            _t1861 = _t1862
                        _t1860 = _t1861
                    _t1859 = _t1860
                _t1858 = _t1859
            _t1857 = _t1858
        else:
            _t1857 = -1
        prediction1065 = _t1857
        if prediction1065 == 4:
            _t1864 = self.parse_monus_def()
            monus_def1070 = _t1864
            _t1865 = logic_pb2.Instruction(monus_def=monus_def1070)
            _t1863 = _t1865
        else:
            if prediction1065 == 3:
                _t1867 = self.parse_monoid_def()
                monoid_def1069 = _t1867
                _t1868 = logic_pb2.Instruction(monoid_def=monoid_def1069)
                _t1866 = _t1868
            else:
                if prediction1065 == 2:
                    _t1870 = self.parse_break()
                    break1068 = _t1870
                    _t1871 = logic_pb2.Instruction()
                    getattr(_t1871, 'break').CopyFrom(break1068)
                    _t1869 = _t1871
                else:
                    if prediction1065 == 1:
                        _t1873 = self.parse_upsert()
                        upsert1067 = _t1873
                        _t1874 = logic_pb2.Instruction(upsert=upsert1067)
                        _t1872 = _t1874
                    else:
                        if prediction1065 == 0:
                            _t1876 = self.parse_assign()
                            assign1066 = _t1876
                            _t1877 = logic_pb2.Instruction(assign=assign1066)
                            _t1875 = _t1877
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1872 = _t1875
                    _t1869 = _t1872
                _t1866 = _t1869
            _t1863 = _t1866
        result1072 = _t1863
        self.record_span(span_start1071, "Instruction")
        return result1072

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1076 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1878 = self.parse_relation_id()
        relation_id1073 = _t1878
        _t1879 = self.parse_abstraction()
        abstraction1074 = _t1879
        if self.match_lookahead_literal("(", 0):
            _t1881 = self.parse_attrs()
            _t1880 = _t1881
        else:
            _t1880 = None
        attrs1075 = _t1880
        self.consume_literal(")")
        _t1882 = logic_pb2.Assign(name=relation_id1073, body=abstraction1074, attrs=(attrs1075 if attrs1075 is not None else []))
        result1077 = _t1882
        self.record_span(span_start1076, "Assign")
        return result1077

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1081 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1883 = self.parse_relation_id()
        relation_id1078 = _t1883
        _t1884 = self.parse_abstraction_with_arity()
        abstraction_with_arity1079 = _t1884
        if self.match_lookahead_literal("(", 0):
            _t1886 = self.parse_attrs()
            _t1885 = _t1886
        else:
            _t1885 = None
        attrs1080 = _t1885
        self.consume_literal(")")
        _t1887 = logic_pb2.Upsert(name=relation_id1078, body=abstraction_with_arity1079[0], attrs=(attrs1080 if attrs1080 is not None else []), value_arity=abstraction_with_arity1079[1])
        result1082 = _t1887
        self.record_span(span_start1081, "Upsert")
        return result1082

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1888 = self.parse_bindings()
        bindings1083 = _t1888
        _t1889 = self.parse_formula()
        formula1084 = _t1889
        self.consume_literal(")")
        _t1890 = logic_pb2.Abstraction(vars=(list(bindings1083[0]) + list(bindings1083[1] if bindings1083[1] is not None else [])), value=formula1084)
        return (_t1890, len(bindings1083[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1088 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1891 = self.parse_relation_id()
        relation_id1085 = _t1891
        _t1892 = self.parse_abstraction()
        abstraction1086 = _t1892
        if self.match_lookahead_literal("(", 0):
            _t1894 = self.parse_attrs()
            _t1893 = _t1894
        else:
            _t1893 = None
        attrs1087 = _t1893
        self.consume_literal(")")
        _t1895 = logic_pb2.Break(name=relation_id1085, body=abstraction1086, attrs=(attrs1087 if attrs1087 is not None else []))
        result1089 = _t1895
        self.record_span(span_start1088, "Break")
        return result1089

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1094 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1896 = self.parse_monoid()
        monoid1090 = _t1896
        _t1897 = self.parse_relation_id()
        relation_id1091 = _t1897
        _t1898 = self.parse_abstraction_with_arity()
        abstraction_with_arity1092 = _t1898
        if self.match_lookahead_literal("(", 0):
            _t1900 = self.parse_attrs()
            _t1899 = _t1900
        else:
            _t1899 = None
        attrs1093 = _t1899
        self.consume_literal(")")
        _t1901 = logic_pb2.MonoidDef(monoid=monoid1090, name=relation_id1091, body=abstraction_with_arity1092[0], attrs=(attrs1093 if attrs1093 is not None else []), value_arity=abstraction_with_arity1092[1])
        result1095 = _t1901
        self.record_span(span_start1094, "MonoidDef")
        return result1095

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1101 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1903 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1904 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1905 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1906 = 2
                        else:
                            _t1906 = -1
                        _t1905 = _t1906
                    _t1904 = _t1905
                _t1903 = _t1904
            _t1902 = _t1903
        else:
            _t1902 = -1
        prediction1096 = _t1902
        if prediction1096 == 3:
            _t1908 = self.parse_sum_monoid()
            sum_monoid1100 = _t1908
            _t1909 = logic_pb2.Monoid(sum_monoid=sum_monoid1100)
            _t1907 = _t1909
        else:
            if prediction1096 == 2:
                _t1911 = self.parse_max_monoid()
                max_monoid1099 = _t1911
                _t1912 = logic_pb2.Monoid(max_monoid=max_monoid1099)
                _t1910 = _t1912
            else:
                if prediction1096 == 1:
                    _t1914 = self.parse_min_monoid()
                    min_monoid1098 = _t1914
                    _t1915 = logic_pb2.Monoid(min_monoid=min_monoid1098)
                    _t1913 = _t1915
                else:
                    if prediction1096 == 0:
                        _t1917 = self.parse_or_monoid()
                        or_monoid1097 = _t1917
                        _t1918 = logic_pb2.Monoid(or_monoid=or_monoid1097)
                        _t1916 = _t1918
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1913 = _t1916
                _t1910 = _t1913
            _t1907 = _t1910
        result1102 = _t1907
        self.record_span(span_start1101, "Monoid")
        return result1102

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1103 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1919 = logic_pb2.OrMonoid()
        result1104 = _t1919
        self.record_span(span_start1103, "OrMonoid")
        return result1104

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1106 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1920 = self.parse_type()
        type1105 = _t1920
        self.consume_literal(")")
        _t1921 = logic_pb2.MinMonoid(type=type1105)
        result1107 = _t1921
        self.record_span(span_start1106, "MinMonoid")
        return result1107

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1109 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1922 = self.parse_type()
        type1108 = _t1922
        self.consume_literal(")")
        _t1923 = logic_pb2.MaxMonoid(type=type1108)
        result1110 = _t1923
        self.record_span(span_start1109, "MaxMonoid")
        return result1110

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1112 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1924 = self.parse_type()
        type1111 = _t1924
        self.consume_literal(")")
        _t1925 = logic_pb2.SumMonoid(type=type1111)
        result1113 = _t1925
        self.record_span(span_start1112, "SumMonoid")
        return result1113

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1118 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1926 = self.parse_monoid()
        monoid1114 = _t1926
        _t1927 = self.parse_relation_id()
        relation_id1115 = _t1927
        _t1928 = self.parse_abstraction_with_arity()
        abstraction_with_arity1116 = _t1928
        if self.match_lookahead_literal("(", 0):
            _t1930 = self.parse_attrs()
            _t1929 = _t1930
        else:
            _t1929 = None
        attrs1117 = _t1929
        self.consume_literal(")")
        _t1931 = logic_pb2.MonusDef(monoid=monoid1114, name=relation_id1115, body=abstraction_with_arity1116[0], attrs=(attrs1117 if attrs1117 is not None else []), value_arity=abstraction_with_arity1116[1])
        result1119 = _t1931
        self.record_span(span_start1118, "MonusDef")
        return result1119

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1124 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1932 = self.parse_relation_id()
        relation_id1120 = _t1932
        _t1933 = self.parse_abstraction()
        abstraction1121 = _t1933
        _t1934 = self.parse_functional_dependency_keys()
        functional_dependency_keys1122 = _t1934
        _t1935 = self.parse_functional_dependency_values()
        functional_dependency_values1123 = _t1935
        self.consume_literal(")")
        _t1936 = logic_pb2.FunctionalDependency(guard=abstraction1121, keys=functional_dependency_keys1122, values=functional_dependency_values1123)
        _t1937 = logic_pb2.Constraint(name=relation_id1120, functional_dependency=_t1936)
        result1125 = _t1937
        self.record_span(span_start1124, "Constraint")
        return result1125

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1126 = []
        cond1127 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1127:
            _t1938 = self.parse_var()
            item1128 = _t1938
            xs1126.append(item1128)
            cond1127 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1129 = xs1126
        self.consume_literal(")")
        return vars1129

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1130 = []
        cond1131 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1131:
            _t1939 = self.parse_var()
            item1132 = _t1939
            xs1130.append(item1132)
            cond1131 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1133 = xs1130
        self.consume_literal(")")
        return vars1133

    def parse_data(self) -> logic_pb2.Data:
        span_start1139 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1941 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1942 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1943 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1944 = 1
                        else:
                            _t1944 = -1
                        _t1943 = _t1944
                    _t1942 = _t1943
                _t1941 = _t1942
            _t1940 = _t1941
        else:
            _t1940 = -1
        prediction1134 = _t1940
        if prediction1134 == 3:
            _t1946 = self.parse_iceberg_data()
            iceberg_data1138 = _t1946
            _t1947 = logic_pb2.Data(iceberg_data=iceberg_data1138)
            _t1945 = _t1947
        else:
            if prediction1134 == 2:
                _t1949 = self.parse_csv_data()
                csv_data1137 = _t1949
                _t1950 = logic_pb2.Data(csv_data=csv_data1137)
                _t1948 = _t1950
            else:
                if prediction1134 == 1:
                    _t1952 = self.parse_betree_relation()
                    betree_relation1136 = _t1952
                    _t1953 = logic_pb2.Data(betree_relation=betree_relation1136)
                    _t1951 = _t1953
                else:
                    if prediction1134 == 0:
                        _t1955 = self.parse_edb()
                        edb1135 = _t1955
                        _t1956 = logic_pb2.Data(edb=edb1135)
                        _t1954 = _t1956
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1951 = _t1954
                _t1948 = _t1951
            _t1945 = _t1948
        result1140 = _t1945
        self.record_span(span_start1139, "Data")
        return result1140

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1144 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1957 = self.parse_relation_id()
        relation_id1141 = _t1957
        _t1958 = self.parse_edb_path()
        edb_path1142 = _t1958
        _t1959 = self.parse_edb_types()
        edb_types1143 = _t1959
        self.consume_literal(")")
        _t1960 = logic_pb2.EDB(target_id=relation_id1141, path=edb_path1142, types=edb_types1143)
        result1145 = _t1960
        self.record_span(span_start1144, "EDB")
        return result1145

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1146 = []
        cond1147 = self.match_lookahead_terminal("STRING", 0)
        while cond1147:
            item1148 = self.consume_terminal("STRING")
            xs1146.append(item1148)
            cond1147 = self.match_lookahead_terminal("STRING", 0)
        strings1149 = xs1146
        self.consume_literal("]")
        return strings1149

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1150 = []
        cond1151 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1151:
            _t1961 = self.parse_type()
            item1152 = _t1961
            xs1150.append(item1152)
            cond1151 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1153 = xs1150
        self.consume_literal("]")
        return types1153

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1156 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1962 = self.parse_relation_id()
        relation_id1154 = _t1962
        _t1963 = self.parse_betree_info()
        betree_info1155 = _t1963
        self.consume_literal(")")
        _t1964 = logic_pb2.BeTreeRelation(name=relation_id1154, relation_info=betree_info1155)
        result1157 = _t1964
        self.record_span(span_start1156, "BeTreeRelation")
        return result1157

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1161 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1965 = self.parse_betree_info_key_types()
        betree_info_key_types1158 = _t1965
        _t1966 = self.parse_betree_info_value_types()
        betree_info_value_types1159 = _t1966
        _t1967 = self.parse_config_dict()
        config_dict1160 = _t1967
        self.consume_literal(")")
        _t1968 = self.construct_betree_info(betree_info_key_types1158, betree_info_value_types1159, config_dict1160)
        result1162 = _t1968
        self.record_span(span_start1161, "BeTreeInfo")
        return result1162

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1163 = []
        cond1164 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1164:
            _t1969 = self.parse_type()
            item1165 = _t1969
            xs1163.append(item1165)
            cond1164 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1166 = xs1163
        self.consume_literal(")")
        return types1166

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1167 = []
        cond1168 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1168:
            _t1970 = self.parse_type()
            item1169 = _t1970
            xs1167.append(item1169)
            cond1168 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1170 = xs1167
        self.consume_literal(")")
        return types1170

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1175 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1971 = self.parse_csvlocator()
        csvlocator1171 = _t1971
        _t1972 = self.parse_csv_config()
        csv_config1172 = _t1972
        _t1973 = self.parse_gnf_columns()
        gnf_columns1173 = _t1973
        _t1974 = self.parse_csv_asof()
        csv_asof1174 = _t1974
        self.consume_literal(")")
        _t1975 = logic_pb2.CSVData(locator=csvlocator1171, config=csv_config1172, columns=gnf_columns1173, asof=csv_asof1174)
        result1176 = _t1975
        self.record_span(span_start1175, "CSVData")
        return result1176

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1179 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1977 = self.parse_csv_locator_paths()
            _t1976 = _t1977
        else:
            _t1976 = None
        csv_locator_paths1177 = _t1976
        if self.match_lookahead_literal("(", 0):
            _t1979 = self.parse_csv_locator_inline_data()
            _t1978 = _t1979
        else:
            _t1978 = None
        csv_locator_inline_data1178 = _t1978
        self.consume_literal(")")
        _t1980 = logic_pb2.CSVLocator(paths=(csv_locator_paths1177 if csv_locator_paths1177 is not None else []), inline_data=(csv_locator_inline_data1178 if csv_locator_inline_data1178 is not None else "").encode())
        result1180 = _t1980
        self.record_span(span_start1179, "CSVLocator")
        return result1180

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1181 = []
        cond1182 = self.match_lookahead_terminal("STRING", 0)
        while cond1182:
            item1183 = self.consume_terminal("STRING")
            xs1181.append(item1183)
            cond1182 = self.match_lookahead_terminal("STRING", 0)
        strings1184 = xs1181
        self.consume_literal(")")
        return strings1184

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        formatted_string1185 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return formatted_string1185

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1188 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1981 = self.parse_config_dict()
        config_dict1186 = _t1981
        if self.match_lookahead_literal("(", 0):
            _t1983 = self.parse__storage_integration()
            _t1982 = _t1983
        else:
            _t1982 = None
        _storage_integration1187 = _t1982
        self.consume_literal(")")
        _t1984 = self.construct_csv_config(config_dict1186, _storage_integration1187)
        result1189 = _t1984
        self.record_span(span_start1188, "CSVConfig")
        return result1189

    def parse__storage_integration(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("(")
        self.consume_literal("storage_integration")
        _t1985 = self.parse_config_dict()
        config_dict1190 = _t1985
        self.consume_literal(")")
        return config_dict1190

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1191 = []
        cond1192 = self.match_lookahead_literal("(", 0)
        while cond1192:
            _t1986 = self.parse_gnf_column()
            item1193 = _t1986
            xs1191.append(item1193)
            cond1192 = self.match_lookahead_literal("(", 0)
        gnf_columns1194 = xs1191
        self.consume_literal(")")
        return gnf_columns1194

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1201 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1987 = self.parse_gnf_column_path()
        gnf_column_path1195 = _t1987
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1989 = self.parse_relation_id()
            _t1988 = _t1989
        else:
            _t1988 = None
        relation_id1196 = _t1988
        self.consume_literal("[")
        xs1197 = []
        cond1198 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1198:
            _t1990 = self.parse_type()
            item1199 = _t1990
            xs1197.append(item1199)
            cond1198 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1200 = xs1197
        self.consume_literal("]")
        self.consume_literal(")")
        _t1991 = logic_pb2.GNFColumn(column_path=gnf_column_path1195, target_id=relation_id1196, types=types1200)
        result1202 = _t1991
        self.record_span(span_start1201, "GNFColumn")
        return result1202

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1992 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1993 = 0
            else:
                _t1993 = -1
            _t1992 = _t1993
        prediction1203 = _t1992
        if prediction1203 == 1:
            self.consume_literal("[")
            xs1205 = []
            cond1206 = self.match_lookahead_terminal("STRING", 0)
            while cond1206:
                item1207 = self.consume_terminal("STRING")
                xs1205.append(item1207)
                cond1206 = self.match_lookahead_terminal("STRING", 0)
            strings1208 = xs1205
            self.consume_literal("]")
            _t1994 = strings1208
        else:
            if prediction1203 == 0:
                string1204 = self.consume_terminal("STRING")
                _t1995 = [string1204]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1994 = _t1995
        return _t1994

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1209 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1209

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1216 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1996 = self.parse_iceberg_locator()
        iceberg_locator1210 = _t1996
        _t1997 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1211 = _t1997
        _t1998 = self.parse_gnf_columns()
        gnf_columns1212 = _t1998
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t2000 = self.parse_iceberg_from_snapshot()
            _t1999 = _t2000
        else:
            _t1999 = None
        iceberg_from_snapshot1213 = _t1999
        if self.match_lookahead_literal("(", 0):
            _t2002 = self.parse_iceberg_to_snapshot()
            _t2001 = _t2002
        else:
            _t2001 = None
        iceberg_to_snapshot1214 = _t2001
        _t2003 = self.parse_boolean_value()
        boolean_value1215 = _t2003
        self.consume_literal(")")
        _t2004 = self.construct_iceberg_data(iceberg_locator1210, iceberg_catalog_config1211, gnf_columns1212, iceberg_from_snapshot1213, iceberg_to_snapshot1214, boolean_value1215)
        result1217 = _t2004
        self.record_span(span_start1216, "IcebergData")
        return result1217

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1221 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t2005 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1218 = _t2005
        _t2006 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1219 = _t2006
        _t2007 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1220 = _t2007
        self.consume_literal(")")
        _t2008 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1218, namespace=iceberg_locator_namespace1219, warehouse=iceberg_locator_warehouse1220)
        result1222 = _t2008
        self.record_span(span_start1221, "IcebergLocator")
        return result1222

    def parse_iceberg_locator_table_name(self) -> str:
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1223 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1223

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1224 = []
        cond1225 = self.match_lookahead_terminal("STRING", 0)
        while cond1225:
            item1226 = self.consume_terminal("STRING")
            xs1224.append(item1226)
            cond1225 = self.match_lookahead_terminal("STRING", 0)
        strings1227 = xs1224
        self.consume_literal(")")
        return strings1227

    def parse_iceberg_locator_warehouse(self) -> str:
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string1228 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1228

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1233 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t2009 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1229 = _t2009
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t2011 = self.parse_iceberg_catalog_config_scope()
            _t2010 = _t2011
        else:
            _t2010 = None
        iceberg_catalog_config_scope1230 = _t2010
        _t2012 = self.parse_iceberg_properties()
        iceberg_properties1231 = _t2012
        _t2013 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1232 = _t2013
        self.consume_literal(")")
        _t2014 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1229, iceberg_catalog_config_scope1230, iceberg_properties1231, iceberg_auth_properties1232)
        result1234 = _t2014
        self.record_span(span_start1233, "IcebergCatalogConfig")
        return result1234

    def parse_iceberg_catalog_uri(self) -> str:
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1235 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1235

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1236 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1236

    def parse_iceberg_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1237 = []
        cond1238 = self.match_lookahead_literal("(", 0)
        while cond1238:
            _t2015 = self.parse_iceberg_property_entry()
            item1239 = _t2015
            xs1237.append(item1239)
            cond1238 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1240 = xs1237
        self.consume_literal(")")
        return iceberg_property_entrys1240

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1241 = self.consume_terminal("STRING")
        string_31242 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1241, string_31242,)

    def parse_iceberg_auth_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1243 = []
        cond1244 = self.match_lookahead_literal("(", 0)
        while cond1244:
            _t2016 = self.parse_iceberg_masked_property_entry()
            item1245 = _t2016
            xs1243.append(item1245)
            cond1244 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1246 = xs1243
        self.consume_literal(")")
        return iceberg_masked_property_entrys1246

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1247 = self.consume_terminal("STRING")
        string_31248 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1247, string_31248,)

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1249 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1249

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1250 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1250

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1252 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2017 = self.parse_fragment_id()
        fragment_id1251 = _t2017
        self.consume_literal(")")
        _t2018 = transactions_pb2.Undefine(fragment_id=fragment_id1251)
        result1253 = _t2018
        self.record_span(span_start1252, "Undefine")
        return result1253

    def parse_context(self) -> transactions_pb2.Context:
        span_start1258 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1254 = []
        cond1255 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1255:
            _t2019 = self.parse_relation_id()
            item1256 = _t2019
            xs1254.append(item1256)
            cond1255 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1257 = xs1254
        self.consume_literal(")")
        _t2020 = transactions_pb2.Context(relations=relation_ids1257)
        result1259 = _t2020
        self.record_span(span_start1258, "Context")
        return result1259

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1265 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t2021 = self.parse_edb_path()
        edb_path1260 = _t2021
        xs1261 = []
        cond1262 = self.match_lookahead_literal("[", 0)
        while cond1262:
            _t2022 = self.parse_snapshot_mapping()
            item1263 = _t2022
            xs1261.append(item1263)
            cond1262 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1264 = xs1261
        self.consume_literal(")")
        _t2023 = transactions_pb2.Snapshot(prefix=edb_path1260, mappings=snapshot_mappings1264)
        result1266 = _t2023
        self.record_span(span_start1265, "Snapshot")
        return result1266

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1269 = self.span_start()
        _t2024 = self.parse_edb_path()
        edb_path1267 = _t2024
        _t2025 = self.parse_relation_id()
        relation_id1268 = _t2025
        _t2026 = transactions_pb2.SnapshotMapping(destination_path=edb_path1267, source_relation=relation_id1268)
        result1270 = _t2026
        self.record_span(span_start1269, "SnapshotMapping")
        return result1270

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1271 = []
        cond1272 = self.match_lookahead_literal("(", 0)
        while cond1272:
            _t2027 = self.parse_read()
            item1273 = _t2027
            xs1271.append(item1273)
            cond1272 = self.match_lookahead_literal("(", 0)
        reads1274 = xs1271
        self.consume_literal(")")
        return reads1274

    def parse_read(self) -> transactions_pb2.Read:
        span_start1282 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2029 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2030 = 1
                else:
                    if self.match_lookahead_literal("export_output", 1):
                        _t2031 = 5
                    else:
                        if self.match_lookahead_literal("export_iceberg", 1):
                            _t2032 = 4
                        else:
                            if self.match_lookahead_literal("export", 1):
                                _t2033 = 4
                            else:
                                if self.match_lookahead_literal("demand", 1):
                                    _t2034 = 0
                                else:
                                    if self.match_lookahead_literal("abort", 1):
                                        _t2035 = 3
                                    else:
                                        _t2035 = -1
                                    _t2034 = _t2035
                                _t2033 = _t2034
                            _t2032 = _t2033
                        _t2031 = _t2032
                    _t2030 = _t2031
                _t2029 = _t2030
            _t2028 = _t2029
        else:
            _t2028 = -1
        prediction1275 = _t2028
        if prediction1275 == 5:
            _t2037 = self.parse_export_output()
            export_output1281 = _t2037
            _t2038 = transactions_pb2.Read(export_output=export_output1281)
            _t2036 = _t2038
        else:
            if prediction1275 == 4:
                _t2040 = self.parse_export()
                export1280 = _t2040
                _t2041 = transactions_pb2.Read(export=export1280)
                _t2039 = _t2041
            else:
                if prediction1275 == 3:
                    _t2043 = self.parse_abort()
                    abort1279 = _t2043
                    _t2044 = transactions_pb2.Read(abort=abort1279)
                    _t2042 = _t2044
                else:
                    if prediction1275 == 2:
                        _t2046 = self.parse_what_if()
                        what_if1278 = _t2046
                        _t2047 = transactions_pb2.Read(what_if=what_if1278)
                        _t2045 = _t2047
                    else:
                        if prediction1275 == 1:
                            _t2049 = self.parse_output()
                            output1277 = _t2049
                            _t2050 = transactions_pb2.Read(output=output1277)
                            _t2048 = _t2050
                        else:
                            if prediction1275 == 0:
                                _t2052 = self.parse_demand()
                                demand1276 = _t2052
                                _t2053 = transactions_pb2.Read(demand=demand1276)
                                _t2051 = _t2053
                            else:
                                raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t2048 = _t2051
                        _t2045 = _t2048
                    _t2042 = _t2045
                _t2039 = _t2042
            _t2036 = _t2039
        result1283 = _t2036
        self.record_span(span_start1282, "Read")
        return result1283

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1285 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2054 = self.parse_relation_id()
        relation_id1284 = _t2054
        self.consume_literal(")")
        _t2055 = transactions_pb2.Demand(relation_id=relation_id1284)
        result1286 = _t2055
        self.record_span(span_start1285, "Demand")
        return result1286

    def parse_output(self) -> transactions_pb2.Output:
        span_start1289 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2056 = self.parse_name()
        name1287 = _t2056
        _t2057 = self.parse_relation_id()
        relation_id1288 = _t2057
        self.consume_literal(")")
        _t2058 = transactions_pb2.Output(name=name1287, relation_id=relation_id1288)
        result1290 = _t2058
        self.record_span(span_start1289, "Output")
        return result1290

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1293 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2059 = self.parse_name()
        name1291 = _t2059
        _t2060 = self.parse_epoch()
        epoch1292 = _t2060
        self.consume_literal(")")
        _t2061 = transactions_pb2.WhatIf(branch=name1291, epoch=epoch1292)
        result1294 = _t2061
        self.record_span(span_start1293, "WhatIf")
        return result1294

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1297 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2063 = self.parse_name()
            _t2062 = _t2063
        else:
            _t2062 = None
        name1295 = _t2062
        _t2064 = self.parse_relation_id()
        relation_id1296 = _t2064
        self.consume_literal(")")
        _t2065 = transactions_pb2.Abort(name=(name1295 if name1295 is not None else "abort"), relation_id=relation_id1296)
        result1298 = _t2065
        self.record_span(span_start1297, "Abort")
        return result1298

    def parse_export(self) -> transactions_pb2.Export:
        span_start1302 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2067 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2068 = 0
                else:
                    _t2068 = -1
                _t2067 = _t2068
            _t2066 = _t2067
        else:
            _t2066 = -1
        prediction1299 = _t2066
        if prediction1299 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2070 = self.parse_export_iceberg_config()
            export_iceberg_config1301 = _t2070
            self.consume_literal(")")
            _t2071 = transactions_pb2.Export(iceberg_config=export_iceberg_config1301)
            _t2069 = _t2071
        else:
            if prediction1299 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2073 = self.parse_export_csv_config()
                export_csv_config1300 = _t2073
                self.consume_literal(")")
                _t2074 = transactions_pb2.Export(csv_config=export_csv_config1300)
                _t2072 = _t2074
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2069 = _t2072
        result1303 = _t2069
        self.record_span(span_start1302, "Export")
        return result1303

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1311 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2076 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2077 = 1
                else:
                    _t2077 = -1
                _t2076 = _t2077
            _t2075 = _t2076
        else:
            _t2075 = -1
        prediction1304 = _t2075
        if prediction1304 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2079 = self.parse_export_csv_path()
            export_csv_path1308 = _t2079
            _t2080 = self.parse_export_csv_columns_list()
            export_csv_columns_list1309 = _t2080
            _t2081 = self.parse_config_dict()
            config_dict1310 = _t2081
            self.consume_literal(")")
            _t2082 = self.construct_export_csv_config(export_csv_path1308, export_csv_columns_list1309, config_dict1310)
            _t2078 = _t2082
        else:
            if prediction1304 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2084 = self.parse_export_csv_path()
                export_csv_path1305 = _t2084
                _t2085 = self.parse_export_csv_source()
                export_csv_source1306 = _t2085
                _t2086 = self.parse_csv_config()
                csv_config1307 = _t2086
                self.consume_literal(")")
                _t2087 = self.construct_export_csv_config_with_source(export_csv_path1305, export_csv_source1306, csv_config1307)
                _t2083 = _t2087
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2078 = _t2083
        result1312 = _t2078
        self.record_span(span_start1311, "ExportCSVConfig")
        return result1312

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1313 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1313

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1320 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2089 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2090 = 0
                else:
                    _t2090 = -1
                _t2089 = _t2090
            _t2088 = _t2089
        else:
            _t2088 = -1
        prediction1314 = _t2088
        if prediction1314 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2092 = self.parse_relation_id()
            relation_id1319 = _t2092
            self.consume_literal(")")
            _t2093 = transactions_pb2.ExportCSVSource(table_def=relation_id1319)
            _t2091 = _t2093
        else:
            if prediction1314 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1315 = []
                cond1316 = self.match_lookahead_literal("(", 0)
                while cond1316:
                    _t2095 = self.parse_export_csv_column()
                    item1317 = _t2095
                    xs1315.append(item1317)
                    cond1316 = self.match_lookahead_literal("(", 0)
                export_csv_columns1318 = xs1315
                self.consume_literal(")")
                _t2096 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1318)
                _t2097 = transactions_pb2.ExportCSVSource(gnf_columns=_t2096)
                _t2094 = _t2097
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2091 = _t2094
        result1321 = _t2091
        self.record_span(span_start1320, "ExportCSVSource")
        return result1321

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1324 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1322 = self.consume_terminal("STRING")
        _t2098 = self.parse_relation_id()
        relation_id1323 = _t2098
        self.consume_literal(")")
        _t2099 = transactions_pb2.ExportCSVColumn(column_name=string1322, column_data=relation_id1323)
        result1325 = _t2099
        self.record_span(span_start1324, "ExportCSVColumn")
        return result1325

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1326 = []
        cond1327 = self.match_lookahead_literal("(", 0)
        while cond1327:
            _t2100 = self.parse_export_csv_column()
            item1328 = _t2100
            xs1326.append(item1328)
            cond1327 = self.match_lookahead_literal("(", 0)
        export_csv_columns1329 = xs1326
        self.consume_literal(")")
        return export_csv_columns1329

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1335 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2101 = self.parse_iceberg_locator()
        iceberg_locator1330 = _t2101
        _t2102 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1331 = _t2102
        _t2103 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1332 = _t2103
        _t2104 = self.parse_iceberg_table_properties()
        iceberg_table_properties1333 = _t2104
        if self.match_lookahead_literal("{", 0):
            _t2106 = self.parse_config_dict()
            _t2105 = _t2106
        else:
            _t2105 = None
        config_dict1334 = _t2105
        self.consume_literal(")")
        _t2107 = self.construct_export_iceberg_config_full(iceberg_locator1330, iceberg_catalog_config1331, export_iceberg_table_def1332, iceberg_table_properties1333, config_dict1334)
        result1336 = _t2107
        self.record_span(span_start1335, "ExportIcebergConfig")
        return result1336

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1338 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2108 = self.parse_relation_id()
        relation_id1337 = _t2108
        self.consume_literal(")")
        result1339 = relation_id1337
        self.record_span(span_start1338, "RelationId")
        return result1339

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1340 = []
        cond1341 = self.match_lookahead_literal("(", 0)
        while cond1341:
            _t2109 = self.parse_iceberg_property_entry()
            item1342 = _t2109
            xs1340.append(item1342)
            cond1341 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1343 = xs1340
        self.consume_literal(")")
        return iceberg_property_entrys1343

    def parse_export_output(self) -> transactions_pb2.ExportOutput:
        span_start1346 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_output")
        _t2110 = self.parse_name()
        name1344 = _t2110
        _t2111 = self.parse_export_csv_output()
        export_csv_output1345 = _t2111
        self.consume_literal(")")
        _t2112 = transactions_pb2.ExportOutput(name=name1344, csv=export_csv_output1345)
        result1347 = _t2112
        self.record_span(span_start1346, "ExportOutput")
        return result1347

    def parse_export_csv_output(self) -> transactions_pb2.ExportCSVOutput:
        span_start1350 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv")
        _t2113 = self.parse_export_csv_source()
        export_csv_source1348 = _t2113
        _t2114 = self.parse_csv_config()
        csv_config1349 = _t2114
        self.consume_literal(")")
        _t2115 = transactions_pb2.ExportCSVOutput(csv_source=export_csv_source1348, csv_config=csv_config1349)
        result1351 = _t2115
        self.record_span(span_start1350, "ExportCSVOutput")
        return result1351


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
