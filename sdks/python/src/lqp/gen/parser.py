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
            _t2113 = value.HasField("int32_value")
        else:
            _t2113 = False
        if _t2113:
            assert value is not None
            return value.int32_value
        else:
            _t2114 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2115 = value.HasField("int_value")
        else:
            _t2115 = False
        if _t2115:
            assert value is not None
            return value.int_value
        else:
            _t2116 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2117 = value.HasField("string_value")
        else:
            _t2117 = False
        if _t2117:
            assert value is not None
            return value.string_value
        else:
            _t2118 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2119 = value.HasField("boolean_value")
        else:
            _t2119 = False
        if _t2119:
            assert value is not None
            return value.boolean_value
        else:
            _t2120 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2121 = value.HasField("string_value")
        else:
            _t2121 = False
        if _t2121:
            assert value is not None
            return [value.string_value]
        else:
            _t2122 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2123 = value.HasField("int_value")
        else:
            _t2123 = False
        if _t2123:
            assert value is not None
            return value.int_value
        else:
            _t2124 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2125 = value.HasField("float_value")
        else:
            _t2125 = False
        if _t2125:
            assert value is not None
            return value.float_value
        else:
            _t2126 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2127 = value.HasField("string_value")
        else:
            _t2127 = False
        if _t2127:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2128 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2129 = value.HasField("uint128_value")
        else:
            _t2129 = False
        if _t2129:
            assert value is not None
            return value.uint128_value
        else:
            _t2130 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]], storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2131 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2131
        _t2132 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2132
        _t2133 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2133
        _t2134 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2134
        _t2135 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2135
        _t2136 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2136
        _t2137 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2137
        _t2138 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2138
        _t2139 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2139
        _t2140 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2140
        _t2141 = self._extract_value_string(config.get("csv_compression"), "")
        compression = _t2141
        _t2142 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2142
        _t2143 = self.construct_csv_storage_integration(storage_integration_opt)
        storage_integration = _t2143
        _t2144 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb, storage_integration=storage_integration)
        return _t2144

    def construct_csv_storage_integration(self, storage_integration_opt: Sequence[tuple[str, logic_pb2.Value]] | None) -> logic_pb2.StorageIntegration | None:
        if storage_integration_opt is None:
            return None
        else:
            _t2145 = None
        assert storage_integration_opt is not None
        config = dict(storage_integration_opt)
        _t2146 = self._extract_value_string(config.get("provider"), "")
        _t2147 = self._extract_value_string(config.get("azure_sas_token"), "")
        _t2148 = self._extract_value_string(config.get("s3_region"), "")
        _t2149 = self._extract_value_string(config.get("s3_access_key_id"), "")
        _t2150 = self._extract_value_string(config.get("s3_secret_access_key"), "")
        _t2151 = logic_pb2.StorageIntegration(provider=_t2146, azure_sas_token=_t2147, s3_region=_t2148, s3_access_key_id=_t2149, s3_secret_access_key=_t2150)
        return _t2151

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2152 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2152
        _t2153 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2153
        _t2154 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2154
        _t2155 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2155
        _t2156 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2156
        _t2157 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2157
        _t2158 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2158
        _t2159 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2159
        _t2160 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2160
        _t2161 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2161
        _t2162 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2162

    def default_configure(self) -> transactions_pb2.Configure:
        _t2163 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2163
        _t2164 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2164

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
        _t2165 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2165
        _t2166 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2166
        _t2167 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2167

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2168 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2168
        _t2169 = self._extract_value_string(config.get("compression"), "")
        compression = _t2169
        _t2170 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2170
        _t2171 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2171
        _t2172 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2172
        _t2173 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2173
        _t2174 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2174
        _t2175 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2175

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2176 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2176

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2177 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2177

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[logic_pb2.GNFColumn], from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2178 = logic_pb2.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2178

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2179 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2179
        _t2180 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2180
        _t2181 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2181
        table_props = dict(table_property_pairs)
        _t2182 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2182

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start681 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1351 = self.parse_configure()
            _t1350 = _t1351
        else:
            _t1350 = None
        configure675 = _t1350
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1353 = self.parse_sync()
            _t1352 = _t1353
        else:
            _t1352 = None
        sync676 = _t1352
        xs677 = []
        cond678 = self.match_lookahead_literal("(", 0)
        while cond678:
            _t1354 = self.parse_epoch()
            item679 = _t1354
            xs677.append(item679)
            cond678 = self.match_lookahead_literal("(", 0)
        epochs680 = xs677
        self.consume_literal(")")
        _t1355 = self.default_configure()
        _t1356 = transactions_pb2.Transaction(epochs=epochs680, configure=(configure675 if configure675 is not None else _t1355), sync=sync676)
        result682 = _t1356
        self.record_span(span_start681, "Transaction")
        return result682

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start684 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1357 = self.parse_config_dict()
        config_dict683 = _t1357
        self.consume_literal(")")
        _t1358 = self.construct_configure(config_dict683)
        result685 = _t1358
        self.record_span(span_start684, "Configure")
        return result685

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs686 = []
        cond687 = self.match_lookahead_literal(":", 0)
        while cond687:
            _t1359 = self.parse_config_key_value()
            item688 = _t1359
            xs686.append(item688)
            cond687 = self.match_lookahead_literal(":", 0)
        config_key_values689 = xs686
        self.consume_literal("}")
        return config_key_values689

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol690 = self.consume_terminal("SYMBOL")
        _t1360 = self.parse_raw_value()
        raw_value691 = _t1360
        return (symbol690, raw_value691,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start705 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1361 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1362 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1363 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1365 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1366 = 0
                            else:
                                _t1366 = -1
                            _t1365 = _t1366
                        _t1364 = _t1365
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1367 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1368 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1369 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1370 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1371 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1372 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1373 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1374 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1375 = 10
                                                        else:
                                                            _t1375 = -1
                                                        _t1374 = _t1375
                                                    _t1373 = _t1374
                                                _t1372 = _t1373
                                            _t1371 = _t1372
                                        _t1370 = _t1371
                                    _t1369 = _t1370
                                _t1368 = _t1369
                            _t1367 = _t1368
                        _t1364 = _t1367
                    _t1363 = _t1364
                _t1362 = _t1363
            _t1361 = _t1362
        prediction692 = _t1361
        if prediction692 == 12:
            _t1377 = self.parse_boolean_value()
            boolean_value704 = _t1377
            _t1378 = logic_pb2.Value(boolean_value=boolean_value704)
            _t1376 = _t1378
        else:
            if prediction692 == 11:
                self.consume_literal("missing")
                _t1380 = logic_pb2.MissingValue()
                _t1381 = logic_pb2.Value(missing_value=_t1380)
                _t1379 = _t1381
            else:
                if prediction692 == 10:
                    decimal703 = self.consume_terminal("DECIMAL")
                    _t1383 = logic_pb2.Value(decimal_value=decimal703)
                    _t1382 = _t1383
                else:
                    if prediction692 == 9:
                        int128702 = self.consume_terminal("INT128")
                        _t1385 = logic_pb2.Value(int128_value=int128702)
                        _t1384 = _t1385
                    else:
                        if prediction692 == 8:
                            uint128701 = self.consume_terminal("UINT128")
                            _t1387 = logic_pb2.Value(uint128_value=uint128701)
                            _t1386 = _t1387
                        else:
                            if prediction692 == 7:
                                uint32700 = self.consume_terminal("UINT32")
                                _t1389 = logic_pb2.Value(uint32_value=uint32700)
                                _t1388 = _t1389
                            else:
                                if prediction692 == 6:
                                    float699 = self.consume_terminal("FLOAT")
                                    _t1391 = logic_pb2.Value(float_value=float699)
                                    _t1390 = _t1391
                                else:
                                    if prediction692 == 5:
                                        float32698 = self.consume_terminal("FLOAT32")
                                        _t1393 = logic_pb2.Value(float32_value=float32698)
                                        _t1392 = _t1393
                                    else:
                                        if prediction692 == 4:
                                            int697 = self.consume_terminal("INT")
                                            _t1395 = logic_pb2.Value(int_value=int697)
                                            _t1394 = _t1395
                                        else:
                                            if prediction692 == 3:
                                                int32696 = self.consume_terminal("INT32")
                                                _t1397 = logic_pb2.Value(int32_value=int32696)
                                                _t1396 = _t1397
                                            else:
                                                if prediction692 == 2:
                                                    string695 = self.consume_terminal("STRING")
                                                    _t1399 = logic_pb2.Value(string_value=string695)
                                                    _t1398 = _t1399
                                                else:
                                                    if prediction692 == 1:
                                                        _t1401 = self.parse_raw_datetime()
                                                        raw_datetime694 = _t1401
                                                        _t1402 = logic_pb2.Value(datetime_value=raw_datetime694)
                                                        _t1400 = _t1402
                                                    else:
                                                        if prediction692 == 0:
                                                            _t1404 = self.parse_raw_date()
                                                            raw_date693 = _t1404
                                                            _t1405 = logic_pb2.Value(date_value=raw_date693)
                                                            _t1403 = _t1405
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1400 = _t1403
                                                    _t1398 = _t1400
                                                _t1396 = _t1398
                                            _t1394 = _t1396
                                        _t1392 = _t1394
                                    _t1390 = _t1392
                                _t1388 = _t1390
                            _t1386 = _t1388
                        _t1384 = _t1386
                    _t1382 = _t1384
                _t1379 = _t1382
            _t1376 = _t1379
        result706 = _t1376
        self.record_span(span_start705, "Value")
        return result706

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start710 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int707 = self.consume_terminal("INT")
        int_3708 = self.consume_terminal("INT")
        int_4709 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1406 = logic_pb2.DateValue(year=int(int707), month=int(int_3708), day=int(int_4709))
        result711 = _t1406
        self.record_span(span_start710, "DateValue")
        return result711

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start719 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int712 = self.consume_terminal("INT")
        int_3713 = self.consume_terminal("INT")
        int_4714 = self.consume_terminal("INT")
        int_5715 = self.consume_terminal("INT")
        int_6716 = self.consume_terminal("INT")
        int_7717 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1407 = self.consume_terminal("INT")
        else:
            _t1407 = None
        int_8718 = _t1407
        self.consume_literal(")")
        _t1408 = logic_pb2.DateTimeValue(year=int(int712), month=int(int_3713), day=int(int_4714), hour=int(int_5715), minute=int(int_6716), second=int(int_7717), microsecond=int((int_8718 if int_8718 is not None else 0)))
        result720 = _t1408
        self.record_span(span_start719, "DateTimeValue")
        return result720

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1409 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1410 = 1
            else:
                _t1410 = -1
            _t1409 = _t1410
        prediction721 = _t1409
        if prediction721 == 1:
            self.consume_literal("false")
            _t1411 = False
        else:
            if prediction721 == 0:
                self.consume_literal("true")
                _t1412 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1411 = _t1412
        return _t1411

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start726 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs722 = []
        cond723 = self.match_lookahead_literal(":", 0)
        while cond723:
            _t1413 = self.parse_fragment_id()
            item724 = _t1413
            xs722.append(item724)
            cond723 = self.match_lookahead_literal(":", 0)
        fragment_ids725 = xs722
        self.consume_literal(")")
        _t1414 = transactions_pb2.Sync(fragments=fragment_ids725)
        result727 = _t1414
        self.record_span(span_start726, "Sync")
        return result727

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start729 = self.span_start()
        self.consume_literal(":")
        symbol728 = self.consume_terminal("SYMBOL")
        result730 = fragments_pb2.FragmentId(id=symbol728.encode())
        self.record_span(span_start729, "FragmentId")
        return result730

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start733 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1416 = self.parse_epoch_writes()
            _t1415 = _t1416
        else:
            _t1415 = None
        epoch_writes731 = _t1415
        if self.match_lookahead_literal("(", 0):
            _t1418 = self.parse_epoch_reads()
            _t1417 = _t1418
        else:
            _t1417 = None
        epoch_reads732 = _t1417
        self.consume_literal(")")
        _t1419 = transactions_pb2.Epoch(writes=(epoch_writes731 if epoch_writes731 is not None else []), reads=(epoch_reads732 if epoch_reads732 is not None else []))
        result734 = _t1419
        self.record_span(span_start733, "Epoch")
        return result734

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs735 = []
        cond736 = self.match_lookahead_literal("(", 0)
        while cond736:
            _t1420 = self.parse_write()
            item737 = _t1420
            xs735.append(item737)
            cond736 = self.match_lookahead_literal("(", 0)
        writes738 = xs735
        self.consume_literal(")")
        return writes738

    def parse_write(self) -> transactions_pb2.Write:
        span_start744 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1422 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1423 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1424 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1425 = 2
                        else:
                            _t1425 = -1
                        _t1424 = _t1425
                    _t1423 = _t1424
                _t1422 = _t1423
            _t1421 = _t1422
        else:
            _t1421 = -1
        prediction739 = _t1421
        if prediction739 == 3:
            _t1427 = self.parse_snapshot()
            snapshot743 = _t1427
            _t1428 = transactions_pb2.Write(snapshot=snapshot743)
            _t1426 = _t1428
        else:
            if prediction739 == 2:
                _t1430 = self.parse_context()
                context742 = _t1430
                _t1431 = transactions_pb2.Write(context=context742)
                _t1429 = _t1431
            else:
                if prediction739 == 1:
                    _t1433 = self.parse_undefine()
                    undefine741 = _t1433
                    _t1434 = transactions_pb2.Write(undefine=undefine741)
                    _t1432 = _t1434
                else:
                    if prediction739 == 0:
                        _t1436 = self.parse_define()
                        define740 = _t1436
                        _t1437 = transactions_pb2.Write(define=define740)
                        _t1435 = _t1437
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1432 = _t1435
                _t1429 = _t1432
            _t1426 = _t1429
        result745 = _t1426
        self.record_span(span_start744, "Write")
        return result745

    def parse_define(self) -> transactions_pb2.Define:
        span_start747 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1438 = self.parse_fragment()
        fragment746 = _t1438
        self.consume_literal(")")
        _t1439 = transactions_pb2.Define(fragment=fragment746)
        result748 = _t1439
        self.record_span(span_start747, "Define")
        return result748

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start754 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1440 = self.parse_new_fragment_id()
        new_fragment_id749 = _t1440
        xs750 = []
        cond751 = self.match_lookahead_literal("(", 0)
        while cond751:
            _t1441 = self.parse_declaration()
            item752 = _t1441
            xs750.append(item752)
            cond751 = self.match_lookahead_literal("(", 0)
        declarations753 = xs750
        self.consume_literal(")")
        result755 = self.construct_fragment(new_fragment_id749, declarations753)
        self.record_span(span_start754, "Fragment")
        return result755

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start757 = self.span_start()
        _t1442 = self.parse_fragment_id()
        fragment_id756 = _t1442
        self.start_fragment(fragment_id756)
        result758 = fragment_id756
        self.record_span(span_start757, "FragmentId")
        return result758

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start764 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1444 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1445 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1446 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1447 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1448 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1449 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1450 = 1
                                    else:
                                        _t1450 = -1
                                    _t1449 = _t1450
                                _t1448 = _t1449
                            _t1447 = _t1448
                        _t1446 = _t1447
                    _t1445 = _t1446
                _t1444 = _t1445
            _t1443 = _t1444
        else:
            _t1443 = -1
        prediction759 = _t1443
        if prediction759 == 3:
            _t1452 = self.parse_data()
            data763 = _t1452
            _t1453 = logic_pb2.Declaration(data=data763)
            _t1451 = _t1453
        else:
            if prediction759 == 2:
                _t1455 = self.parse_constraint()
                constraint762 = _t1455
                _t1456 = logic_pb2.Declaration(constraint=constraint762)
                _t1454 = _t1456
            else:
                if prediction759 == 1:
                    _t1458 = self.parse_algorithm()
                    algorithm761 = _t1458
                    _t1459 = logic_pb2.Declaration(algorithm=algorithm761)
                    _t1457 = _t1459
                else:
                    if prediction759 == 0:
                        _t1461 = self.parse_def()
                        def760 = _t1461
                        _t1462 = logic_pb2.Declaration()
                        getattr(_t1462, 'def').CopyFrom(def760)
                        _t1460 = _t1462
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1457 = _t1460
                _t1454 = _t1457
            _t1451 = _t1454
        result765 = _t1451
        self.record_span(span_start764, "Declaration")
        return result765

    def parse_def(self) -> logic_pb2.Def:
        span_start769 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1463 = self.parse_relation_id()
        relation_id766 = _t1463
        _t1464 = self.parse_abstraction()
        abstraction767 = _t1464
        if self.match_lookahead_literal("(", 0):
            _t1466 = self.parse_attrs()
            _t1465 = _t1466
        else:
            _t1465 = None
        attrs768 = _t1465
        self.consume_literal(")")
        _t1467 = logic_pb2.Def(name=relation_id766, body=abstraction767, attrs=(attrs768 if attrs768 is not None else []))
        result770 = _t1467
        self.record_span(span_start769, "Def")
        return result770

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start774 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1468 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1469 = 1
            else:
                _t1469 = -1
            _t1468 = _t1469
        prediction771 = _t1468
        if prediction771 == 1:
            uint128773 = self.consume_terminal("UINT128")
            _t1470 = logic_pb2.RelationId(id_low=uint128773.low, id_high=uint128773.high)
        else:
            if prediction771 == 0:
                self.consume_literal(":")
                symbol772 = self.consume_terminal("SYMBOL")
                _t1471 = self.relation_id_from_string(symbol772)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1470 = _t1471
        result775 = _t1470
        self.record_span(span_start774, "RelationId")
        return result775

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start778 = self.span_start()
        self.consume_literal("(")
        _t1472 = self.parse_bindings()
        bindings776 = _t1472
        _t1473 = self.parse_formula()
        formula777 = _t1473
        self.consume_literal(")")
        _t1474 = logic_pb2.Abstraction(vars=(list(bindings776[0]) + list(bindings776[1] if bindings776[1] is not None else [])), value=formula777)
        result779 = _t1474
        self.record_span(span_start778, "Abstraction")
        return result779

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs780 = []
        cond781 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond781:
            _t1475 = self.parse_binding()
            item782 = _t1475
            xs780.append(item782)
            cond781 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings783 = xs780
        if self.match_lookahead_literal("|", 0):
            _t1477 = self.parse_value_bindings()
            _t1476 = _t1477
        else:
            _t1476 = None
        value_bindings784 = _t1476
        self.consume_literal("]")
        return (bindings783, (value_bindings784 if value_bindings784 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start787 = self.span_start()
        symbol785 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1478 = self.parse_type()
        type786 = _t1478
        _t1479 = logic_pb2.Var(name=symbol785)
        _t1480 = logic_pb2.Binding(var=_t1479, type=type786)
        result788 = _t1480
        self.record_span(span_start787, "Binding")
        return result788

    def parse_type(self) -> logic_pb2.Type:
        span_start804 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1481 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1482 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1483 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1484 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1485 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1486 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1487 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1488 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1489 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1490 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1491 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1492 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1493 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1494 = 9
                                                            else:
                                                                _t1494 = -1
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
                _t1482 = _t1483
            _t1481 = _t1482
        prediction789 = _t1481
        if prediction789 == 13:
            _t1496 = self.parse_uint32_type()
            uint32_type803 = _t1496
            _t1497 = logic_pb2.Type(uint32_type=uint32_type803)
            _t1495 = _t1497
        else:
            if prediction789 == 12:
                _t1499 = self.parse_float32_type()
                float32_type802 = _t1499
                _t1500 = logic_pb2.Type(float32_type=float32_type802)
                _t1498 = _t1500
            else:
                if prediction789 == 11:
                    _t1502 = self.parse_int32_type()
                    int32_type801 = _t1502
                    _t1503 = logic_pb2.Type(int32_type=int32_type801)
                    _t1501 = _t1503
                else:
                    if prediction789 == 10:
                        _t1505 = self.parse_boolean_type()
                        boolean_type800 = _t1505
                        _t1506 = logic_pb2.Type(boolean_type=boolean_type800)
                        _t1504 = _t1506
                    else:
                        if prediction789 == 9:
                            _t1508 = self.parse_decimal_type()
                            decimal_type799 = _t1508
                            _t1509 = logic_pb2.Type(decimal_type=decimal_type799)
                            _t1507 = _t1509
                        else:
                            if prediction789 == 8:
                                _t1511 = self.parse_missing_type()
                                missing_type798 = _t1511
                                _t1512 = logic_pb2.Type(missing_type=missing_type798)
                                _t1510 = _t1512
                            else:
                                if prediction789 == 7:
                                    _t1514 = self.parse_datetime_type()
                                    datetime_type797 = _t1514
                                    _t1515 = logic_pb2.Type(datetime_type=datetime_type797)
                                    _t1513 = _t1515
                                else:
                                    if prediction789 == 6:
                                        _t1517 = self.parse_date_type()
                                        date_type796 = _t1517
                                        _t1518 = logic_pb2.Type(date_type=date_type796)
                                        _t1516 = _t1518
                                    else:
                                        if prediction789 == 5:
                                            _t1520 = self.parse_int128_type()
                                            int128_type795 = _t1520
                                            _t1521 = logic_pb2.Type(int128_type=int128_type795)
                                            _t1519 = _t1521
                                        else:
                                            if prediction789 == 4:
                                                _t1523 = self.parse_uint128_type()
                                                uint128_type794 = _t1523
                                                _t1524 = logic_pb2.Type(uint128_type=uint128_type794)
                                                _t1522 = _t1524
                                            else:
                                                if prediction789 == 3:
                                                    _t1526 = self.parse_float_type()
                                                    float_type793 = _t1526
                                                    _t1527 = logic_pb2.Type(float_type=float_type793)
                                                    _t1525 = _t1527
                                                else:
                                                    if prediction789 == 2:
                                                        _t1529 = self.parse_int_type()
                                                        int_type792 = _t1529
                                                        _t1530 = logic_pb2.Type(int_type=int_type792)
                                                        _t1528 = _t1530
                                                    else:
                                                        if prediction789 == 1:
                                                            _t1532 = self.parse_string_type()
                                                            string_type791 = _t1532
                                                            _t1533 = logic_pb2.Type(string_type=string_type791)
                                                            _t1531 = _t1533
                                                        else:
                                                            if prediction789 == 0:
                                                                _t1535 = self.parse_unspecified_type()
                                                                unspecified_type790 = _t1535
                                                                _t1536 = logic_pb2.Type(unspecified_type=unspecified_type790)
                                                                _t1534 = _t1536
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1531 = _t1534
                                                        _t1528 = _t1531
                                                    _t1525 = _t1528
                                                _t1522 = _t1525
                                            _t1519 = _t1522
                                        _t1516 = _t1519
                                    _t1513 = _t1516
                                _t1510 = _t1513
                            _t1507 = _t1510
                        _t1504 = _t1507
                    _t1501 = _t1504
                _t1498 = _t1501
            _t1495 = _t1498
        result805 = _t1495
        self.record_span(span_start804, "Type")
        return result805

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start806 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1537 = logic_pb2.UnspecifiedType()
        result807 = _t1537
        self.record_span(span_start806, "UnspecifiedType")
        return result807

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start808 = self.span_start()
        self.consume_literal("STRING")
        _t1538 = logic_pb2.StringType()
        result809 = _t1538
        self.record_span(span_start808, "StringType")
        return result809

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start810 = self.span_start()
        self.consume_literal("INT")
        _t1539 = logic_pb2.IntType()
        result811 = _t1539
        self.record_span(span_start810, "IntType")
        return result811

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start812 = self.span_start()
        self.consume_literal("FLOAT")
        _t1540 = logic_pb2.FloatType()
        result813 = _t1540
        self.record_span(span_start812, "FloatType")
        return result813

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start814 = self.span_start()
        self.consume_literal("UINT128")
        _t1541 = logic_pb2.UInt128Type()
        result815 = _t1541
        self.record_span(span_start814, "UInt128Type")
        return result815

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start816 = self.span_start()
        self.consume_literal("INT128")
        _t1542 = logic_pb2.Int128Type()
        result817 = _t1542
        self.record_span(span_start816, "Int128Type")
        return result817

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start818 = self.span_start()
        self.consume_literal("DATE")
        _t1543 = logic_pb2.DateType()
        result819 = _t1543
        self.record_span(span_start818, "DateType")
        return result819

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start820 = self.span_start()
        self.consume_literal("DATETIME")
        _t1544 = logic_pb2.DateTimeType()
        result821 = _t1544
        self.record_span(span_start820, "DateTimeType")
        return result821

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start822 = self.span_start()
        self.consume_literal("MISSING")
        _t1545 = logic_pb2.MissingType()
        result823 = _t1545
        self.record_span(span_start822, "MissingType")
        return result823

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start826 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int824 = self.consume_terminal("INT")
        int_3825 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1546 = logic_pb2.DecimalType(precision=int(int824), scale=int(int_3825))
        result827 = _t1546
        self.record_span(span_start826, "DecimalType")
        return result827

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start828 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1547 = logic_pb2.BooleanType()
        result829 = _t1547
        self.record_span(span_start828, "BooleanType")
        return result829

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start830 = self.span_start()
        self.consume_literal("INT32")
        _t1548 = logic_pb2.Int32Type()
        result831 = _t1548
        self.record_span(span_start830, "Int32Type")
        return result831

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start832 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1549 = logic_pb2.Float32Type()
        result833 = _t1549
        self.record_span(span_start832, "Float32Type")
        return result833

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start834 = self.span_start()
        self.consume_literal("UINT32")
        _t1550 = logic_pb2.UInt32Type()
        result835 = _t1550
        self.record_span(span_start834, "UInt32Type")
        return result835

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs836 = []
        cond837 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond837:
            _t1551 = self.parse_binding()
            item838 = _t1551
            xs836.append(item838)
            cond837 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings839 = xs836
        return bindings839

    def parse_formula(self) -> logic_pb2.Formula:
        span_start854 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1553 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1554 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1555 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1556 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1557 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1558 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1559 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1560 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1561 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1562 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1563 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1564 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1565 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1566 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1567 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1568 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1569 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1570 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1571 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1572 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1573 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1574 = 10
                                                                                                else:
                                                                                                    _t1574 = -1
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
                _t1553 = _t1554
            _t1552 = _t1553
        else:
            _t1552 = -1
        prediction840 = _t1552
        if prediction840 == 12:
            _t1576 = self.parse_cast()
            cast853 = _t1576
            _t1577 = logic_pb2.Formula(cast=cast853)
            _t1575 = _t1577
        else:
            if prediction840 == 11:
                _t1579 = self.parse_rel_atom()
                rel_atom852 = _t1579
                _t1580 = logic_pb2.Formula(rel_atom=rel_atom852)
                _t1578 = _t1580
            else:
                if prediction840 == 10:
                    _t1582 = self.parse_primitive()
                    primitive851 = _t1582
                    _t1583 = logic_pb2.Formula(primitive=primitive851)
                    _t1581 = _t1583
                else:
                    if prediction840 == 9:
                        _t1585 = self.parse_pragma()
                        pragma850 = _t1585
                        _t1586 = logic_pb2.Formula(pragma=pragma850)
                        _t1584 = _t1586
                    else:
                        if prediction840 == 8:
                            _t1588 = self.parse_atom()
                            atom849 = _t1588
                            _t1589 = logic_pb2.Formula(atom=atom849)
                            _t1587 = _t1589
                        else:
                            if prediction840 == 7:
                                _t1591 = self.parse_ffi()
                                ffi848 = _t1591
                                _t1592 = logic_pb2.Formula(ffi=ffi848)
                                _t1590 = _t1592
                            else:
                                if prediction840 == 6:
                                    _t1594 = self.parse_not()
                                    not847 = _t1594
                                    _t1595 = logic_pb2.Formula()
                                    getattr(_t1595, 'not').CopyFrom(not847)
                                    _t1593 = _t1595
                                else:
                                    if prediction840 == 5:
                                        _t1597 = self.parse_disjunction()
                                        disjunction846 = _t1597
                                        _t1598 = logic_pb2.Formula(disjunction=disjunction846)
                                        _t1596 = _t1598
                                    else:
                                        if prediction840 == 4:
                                            _t1600 = self.parse_conjunction()
                                            conjunction845 = _t1600
                                            _t1601 = logic_pb2.Formula(conjunction=conjunction845)
                                            _t1599 = _t1601
                                        else:
                                            if prediction840 == 3:
                                                _t1603 = self.parse_reduce()
                                                reduce844 = _t1603
                                                _t1604 = logic_pb2.Formula(reduce=reduce844)
                                                _t1602 = _t1604
                                            else:
                                                if prediction840 == 2:
                                                    _t1606 = self.parse_exists()
                                                    exists843 = _t1606
                                                    _t1607 = logic_pb2.Formula(exists=exists843)
                                                    _t1605 = _t1607
                                                else:
                                                    if prediction840 == 1:
                                                        _t1609 = self.parse_false()
                                                        false842 = _t1609
                                                        _t1610 = logic_pb2.Formula(disjunction=false842)
                                                        _t1608 = _t1610
                                                    else:
                                                        if prediction840 == 0:
                                                            _t1612 = self.parse_true()
                                                            true841 = _t1612
                                                            _t1613 = logic_pb2.Formula(conjunction=true841)
                                                            _t1611 = _t1613
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1578 = _t1581
            _t1575 = _t1578
        result855 = _t1575
        self.record_span(span_start854, "Formula")
        return result855

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start856 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1614 = logic_pb2.Conjunction(args=[])
        result857 = _t1614
        self.record_span(span_start856, "Conjunction")
        return result857

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start858 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1615 = logic_pb2.Disjunction(args=[])
        result859 = _t1615
        self.record_span(span_start858, "Disjunction")
        return result859

    def parse_exists(self) -> logic_pb2.Exists:
        span_start862 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1616 = self.parse_bindings()
        bindings860 = _t1616
        _t1617 = self.parse_formula()
        formula861 = _t1617
        self.consume_literal(")")
        _t1618 = logic_pb2.Abstraction(vars=(list(bindings860[0]) + list(bindings860[1] if bindings860[1] is not None else [])), value=formula861)
        _t1619 = logic_pb2.Exists(body=_t1618)
        result863 = _t1619
        self.record_span(span_start862, "Exists")
        return result863

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start867 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1620 = self.parse_abstraction()
        abstraction864 = _t1620
        _t1621 = self.parse_abstraction()
        abstraction_3865 = _t1621
        _t1622 = self.parse_terms()
        terms866 = _t1622
        self.consume_literal(")")
        _t1623 = logic_pb2.Reduce(op=abstraction864, body=abstraction_3865, terms=terms866)
        result868 = _t1623
        self.record_span(span_start867, "Reduce")
        return result868

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs869 = []
        cond870 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond870:
            _t1624 = self.parse_term()
            item871 = _t1624
            xs869.append(item871)
            cond870 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms872 = xs869
        self.consume_literal(")")
        return terms872

    def parse_term(self) -> logic_pb2.Term:
        span_start876 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1625 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1626 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1627 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1628 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1629 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1630 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1631 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1632 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1633 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1634 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1635 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1636 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1637 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1638 = 1
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
        prediction873 = _t1625
        if prediction873 == 1:
            _t1640 = self.parse_value()
            value875 = _t1640
            _t1641 = logic_pb2.Term(constant=value875)
            _t1639 = _t1641
        else:
            if prediction873 == 0:
                _t1643 = self.parse_var()
                var874 = _t1643
                _t1644 = logic_pb2.Term(var=var874)
                _t1642 = _t1644
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1639 = _t1642
        result877 = _t1639
        self.record_span(span_start876, "Term")
        return result877

    def parse_var(self) -> logic_pb2.Var:
        span_start879 = self.span_start()
        symbol878 = self.consume_terminal("SYMBOL")
        _t1645 = logic_pb2.Var(name=symbol878)
        result880 = _t1645
        self.record_span(span_start879, "Var")
        return result880

    def parse_value(self) -> logic_pb2.Value:
        span_start894 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1646 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1647 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1648 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1650 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1651 = 0
                            else:
                                _t1651 = -1
                            _t1650 = _t1651
                        _t1649 = _t1650
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1652 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1653 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1654 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1655 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1656 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1657 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1658 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1659 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1660 = 10
                                                        else:
                                                            _t1660 = -1
                                                        _t1659 = _t1660
                                                    _t1658 = _t1659
                                                _t1657 = _t1658
                                            _t1656 = _t1657
                                        _t1655 = _t1656
                                    _t1654 = _t1655
                                _t1653 = _t1654
                            _t1652 = _t1653
                        _t1649 = _t1652
                    _t1648 = _t1649
                _t1647 = _t1648
            _t1646 = _t1647
        prediction881 = _t1646
        if prediction881 == 12:
            _t1662 = self.parse_boolean_value()
            boolean_value893 = _t1662
            _t1663 = logic_pb2.Value(boolean_value=boolean_value893)
            _t1661 = _t1663
        else:
            if prediction881 == 11:
                self.consume_literal("missing")
                _t1665 = logic_pb2.MissingValue()
                _t1666 = logic_pb2.Value(missing_value=_t1665)
                _t1664 = _t1666
            else:
                if prediction881 == 10:
                    formatted_decimal892 = self.consume_terminal("DECIMAL")
                    _t1668 = logic_pb2.Value(decimal_value=formatted_decimal892)
                    _t1667 = _t1668
                else:
                    if prediction881 == 9:
                        formatted_int128891 = self.consume_terminal("INT128")
                        _t1670 = logic_pb2.Value(int128_value=formatted_int128891)
                        _t1669 = _t1670
                    else:
                        if prediction881 == 8:
                            formatted_uint128890 = self.consume_terminal("UINT128")
                            _t1672 = logic_pb2.Value(uint128_value=formatted_uint128890)
                            _t1671 = _t1672
                        else:
                            if prediction881 == 7:
                                formatted_uint32889 = self.consume_terminal("UINT32")
                                _t1674 = logic_pb2.Value(uint32_value=formatted_uint32889)
                                _t1673 = _t1674
                            else:
                                if prediction881 == 6:
                                    formatted_float888 = self.consume_terminal("FLOAT")
                                    _t1676 = logic_pb2.Value(float_value=formatted_float888)
                                    _t1675 = _t1676
                                else:
                                    if prediction881 == 5:
                                        formatted_float32887 = self.consume_terminal("FLOAT32")
                                        _t1678 = logic_pb2.Value(float32_value=formatted_float32887)
                                        _t1677 = _t1678
                                    else:
                                        if prediction881 == 4:
                                            formatted_int886 = self.consume_terminal("INT")
                                            _t1680 = logic_pb2.Value(int_value=formatted_int886)
                                            _t1679 = _t1680
                                        else:
                                            if prediction881 == 3:
                                                formatted_int32885 = self.consume_terminal("INT32")
                                                _t1682 = logic_pb2.Value(int32_value=formatted_int32885)
                                                _t1681 = _t1682
                                            else:
                                                if prediction881 == 2:
                                                    formatted_string884 = self.consume_terminal("STRING")
                                                    _t1684 = logic_pb2.Value(string_value=formatted_string884)
                                                    _t1683 = _t1684
                                                else:
                                                    if prediction881 == 1:
                                                        _t1686 = self.parse_datetime()
                                                        datetime883 = _t1686
                                                        _t1687 = logic_pb2.Value(datetime_value=datetime883)
                                                        _t1685 = _t1687
                                                    else:
                                                        if prediction881 == 0:
                                                            _t1689 = self.parse_date()
                                                            date882 = _t1689
                                                            _t1690 = logic_pb2.Value(date_value=date882)
                                                            _t1688 = _t1690
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1685 = _t1688
                                                    _t1683 = _t1685
                                                _t1681 = _t1683
                                            _t1679 = _t1681
                                        _t1677 = _t1679
                                    _t1675 = _t1677
                                _t1673 = _t1675
                            _t1671 = _t1673
                        _t1669 = _t1671
                    _t1667 = _t1669
                _t1664 = _t1667
            _t1661 = _t1664
        result895 = _t1661
        self.record_span(span_start894, "Value")
        return result895

    def parse_date(self) -> logic_pb2.DateValue:
        span_start899 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int896 = self.consume_terminal("INT")
        formatted_int_3897 = self.consume_terminal("INT")
        formatted_int_4898 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1691 = logic_pb2.DateValue(year=int(formatted_int896), month=int(formatted_int_3897), day=int(formatted_int_4898))
        result900 = _t1691
        self.record_span(span_start899, "DateValue")
        return result900

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start908 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int901 = self.consume_terminal("INT")
        formatted_int_3902 = self.consume_terminal("INT")
        formatted_int_4903 = self.consume_terminal("INT")
        formatted_int_5904 = self.consume_terminal("INT")
        formatted_int_6905 = self.consume_terminal("INT")
        formatted_int_7906 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1692 = self.consume_terminal("INT")
        else:
            _t1692 = None
        formatted_int_8907 = _t1692
        self.consume_literal(")")
        _t1693 = logic_pb2.DateTimeValue(year=int(formatted_int901), month=int(formatted_int_3902), day=int(formatted_int_4903), hour=int(formatted_int_5904), minute=int(formatted_int_6905), second=int(formatted_int_7906), microsecond=int((formatted_int_8907 if formatted_int_8907 is not None else 0)))
        result909 = _t1693
        self.record_span(span_start908, "DateTimeValue")
        return result909

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start914 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs910 = []
        cond911 = self.match_lookahead_literal("(", 0)
        while cond911:
            _t1694 = self.parse_formula()
            item912 = _t1694
            xs910.append(item912)
            cond911 = self.match_lookahead_literal("(", 0)
        formulas913 = xs910
        self.consume_literal(")")
        _t1695 = logic_pb2.Conjunction(args=formulas913)
        result915 = _t1695
        self.record_span(span_start914, "Conjunction")
        return result915

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start920 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs916 = []
        cond917 = self.match_lookahead_literal("(", 0)
        while cond917:
            _t1696 = self.parse_formula()
            item918 = _t1696
            xs916.append(item918)
            cond917 = self.match_lookahead_literal("(", 0)
        formulas919 = xs916
        self.consume_literal(")")
        _t1697 = logic_pb2.Disjunction(args=formulas919)
        result921 = _t1697
        self.record_span(span_start920, "Disjunction")
        return result921

    def parse_not(self) -> logic_pb2.Not:
        span_start923 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1698 = self.parse_formula()
        formula922 = _t1698
        self.consume_literal(")")
        _t1699 = logic_pb2.Not(arg=formula922)
        result924 = _t1699
        self.record_span(span_start923, "Not")
        return result924

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start928 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1700 = self.parse_name()
        name925 = _t1700
        _t1701 = self.parse_ffi_args()
        ffi_args926 = _t1701
        _t1702 = self.parse_terms()
        terms927 = _t1702
        self.consume_literal(")")
        _t1703 = logic_pb2.FFI(name=name925, args=ffi_args926, terms=terms927)
        result929 = _t1703
        self.record_span(span_start928, "FFI")
        return result929

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol930 = self.consume_terminal("SYMBOL")
        return symbol930

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs931 = []
        cond932 = self.match_lookahead_literal("(", 0)
        while cond932:
            _t1704 = self.parse_abstraction()
            item933 = _t1704
            xs931.append(item933)
            cond932 = self.match_lookahead_literal("(", 0)
        abstractions934 = xs931
        self.consume_literal(")")
        return abstractions934

    def parse_atom(self) -> logic_pb2.Atom:
        span_start940 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1705 = self.parse_relation_id()
        relation_id935 = _t1705
        xs936 = []
        cond937 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond937:
            _t1706 = self.parse_term()
            item938 = _t1706
            xs936.append(item938)
            cond937 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms939 = xs936
        self.consume_literal(")")
        _t1707 = logic_pb2.Atom(name=relation_id935, terms=terms939)
        result941 = _t1707
        self.record_span(span_start940, "Atom")
        return result941

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start947 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1708 = self.parse_name()
        name942 = _t1708
        xs943 = []
        cond944 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond944:
            _t1709 = self.parse_term()
            item945 = _t1709
            xs943.append(item945)
            cond944 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms946 = xs943
        self.consume_literal(")")
        _t1710 = logic_pb2.Pragma(name=name942, terms=terms946)
        result948 = _t1710
        self.record_span(span_start947, "Pragma")
        return result948

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start964 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1712 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1713 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1714 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1715 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1716 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1717 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1718 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1719 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1720 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1721 = 7
                                                else:
                                                    _t1721 = -1
                                                _t1720 = _t1721
                                            _t1719 = _t1720
                                        _t1718 = _t1719
                                    _t1717 = _t1718
                                _t1716 = _t1717
                            _t1715 = _t1716
                        _t1714 = _t1715
                    _t1713 = _t1714
                _t1712 = _t1713
            _t1711 = _t1712
        else:
            _t1711 = -1
        prediction949 = _t1711
        if prediction949 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1723 = self.parse_name()
            name959 = _t1723
            xs960 = []
            cond961 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond961:
                _t1724 = self.parse_rel_term()
                item962 = _t1724
                xs960.append(item962)
                cond961 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms963 = xs960
            self.consume_literal(")")
            _t1725 = logic_pb2.Primitive(name=name959, terms=rel_terms963)
            _t1722 = _t1725
        else:
            if prediction949 == 8:
                _t1727 = self.parse_divide()
                divide958 = _t1727
                _t1726 = divide958
            else:
                if prediction949 == 7:
                    _t1729 = self.parse_multiply()
                    multiply957 = _t1729
                    _t1728 = multiply957
                else:
                    if prediction949 == 6:
                        _t1731 = self.parse_minus()
                        minus956 = _t1731
                        _t1730 = minus956
                    else:
                        if prediction949 == 5:
                            _t1733 = self.parse_add()
                            add955 = _t1733
                            _t1732 = add955
                        else:
                            if prediction949 == 4:
                                _t1735 = self.parse_gt_eq()
                                gt_eq954 = _t1735
                                _t1734 = gt_eq954
                            else:
                                if prediction949 == 3:
                                    _t1737 = self.parse_gt()
                                    gt953 = _t1737
                                    _t1736 = gt953
                                else:
                                    if prediction949 == 2:
                                        _t1739 = self.parse_lt_eq()
                                        lt_eq952 = _t1739
                                        _t1738 = lt_eq952
                                    else:
                                        if prediction949 == 1:
                                            _t1741 = self.parse_lt()
                                            lt951 = _t1741
                                            _t1740 = lt951
                                        else:
                                            if prediction949 == 0:
                                                _t1743 = self.parse_eq()
                                                eq950 = _t1743
                                                _t1742 = eq950
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1740 = _t1742
                                        _t1738 = _t1740
                                    _t1736 = _t1738
                                _t1734 = _t1736
                            _t1732 = _t1734
                        _t1730 = _t1732
                    _t1728 = _t1730
                _t1726 = _t1728
            _t1722 = _t1726
        result965 = _t1722
        self.record_span(span_start964, "Primitive")
        return result965

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start968 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1744 = self.parse_term()
        term966 = _t1744
        _t1745 = self.parse_term()
        term_3967 = _t1745
        self.consume_literal(")")
        _t1746 = logic_pb2.RelTerm(term=term966)
        _t1747 = logic_pb2.RelTerm(term=term_3967)
        _t1748 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1746, _t1747])
        result969 = _t1748
        self.record_span(span_start968, "Primitive")
        return result969

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start972 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1749 = self.parse_term()
        term970 = _t1749
        _t1750 = self.parse_term()
        term_3971 = _t1750
        self.consume_literal(")")
        _t1751 = logic_pb2.RelTerm(term=term970)
        _t1752 = logic_pb2.RelTerm(term=term_3971)
        _t1753 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1751, _t1752])
        result973 = _t1753
        self.record_span(span_start972, "Primitive")
        return result973

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start976 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1754 = self.parse_term()
        term974 = _t1754
        _t1755 = self.parse_term()
        term_3975 = _t1755
        self.consume_literal(")")
        _t1756 = logic_pb2.RelTerm(term=term974)
        _t1757 = logic_pb2.RelTerm(term=term_3975)
        _t1758 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1756, _t1757])
        result977 = _t1758
        self.record_span(span_start976, "Primitive")
        return result977

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start980 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1759 = self.parse_term()
        term978 = _t1759
        _t1760 = self.parse_term()
        term_3979 = _t1760
        self.consume_literal(")")
        _t1761 = logic_pb2.RelTerm(term=term978)
        _t1762 = logic_pb2.RelTerm(term=term_3979)
        _t1763 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1761, _t1762])
        result981 = _t1763
        self.record_span(span_start980, "Primitive")
        return result981

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start984 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1764 = self.parse_term()
        term982 = _t1764
        _t1765 = self.parse_term()
        term_3983 = _t1765
        self.consume_literal(")")
        _t1766 = logic_pb2.RelTerm(term=term982)
        _t1767 = logic_pb2.RelTerm(term=term_3983)
        _t1768 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1766, _t1767])
        result985 = _t1768
        self.record_span(span_start984, "Primitive")
        return result985

    def parse_add(self) -> logic_pb2.Primitive:
        span_start989 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1769 = self.parse_term()
        term986 = _t1769
        _t1770 = self.parse_term()
        term_3987 = _t1770
        _t1771 = self.parse_term()
        term_4988 = _t1771
        self.consume_literal(")")
        _t1772 = logic_pb2.RelTerm(term=term986)
        _t1773 = logic_pb2.RelTerm(term=term_3987)
        _t1774 = logic_pb2.RelTerm(term=term_4988)
        _t1775 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1772, _t1773, _t1774])
        result990 = _t1775
        self.record_span(span_start989, "Primitive")
        return result990

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start994 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1776 = self.parse_term()
        term991 = _t1776
        _t1777 = self.parse_term()
        term_3992 = _t1777
        _t1778 = self.parse_term()
        term_4993 = _t1778
        self.consume_literal(")")
        _t1779 = logic_pb2.RelTerm(term=term991)
        _t1780 = logic_pb2.RelTerm(term=term_3992)
        _t1781 = logic_pb2.RelTerm(term=term_4993)
        _t1782 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1779, _t1780, _t1781])
        result995 = _t1782
        self.record_span(span_start994, "Primitive")
        return result995

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start999 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1783 = self.parse_term()
        term996 = _t1783
        _t1784 = self.parse_term()
        term_3997 = _t1784
        _t1785 = self.parse_term()
        term_4998 = _t1785
        self.consume_literal(")")
        _t1786 = logic_pb2.RelTerm(term=term996)
        _t1787 = logic_pb2.RelTerm(term=term_3997)
        _t1788 = logic_pb2.RelTerm(term=term_4998)
        _t1789 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1786, _t1787, _t1788])
        result1000 = _t1789
        self.record_span(span_start999, "Primitive")
        return result1000

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start1004 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1790 = self.parse_term()
        term1001 = _t1790
        _t1791 = self.parse_term()
        term_31002 = _t1791
        _t1792 = self.parse_term()
        term_41003 = _t1792
        self.consume_literal(")")
        _t1793 = logic_pb2.RelTerm(term=term1001)
        _t1794 = logic_pb2.RelTerm(term=term_31002)
        _t1795 = logic_pb2.RelTerm(term=term_41003)
        _t1796 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1793, _t1794, _t1795])
        result1005 = _t1796
        self.record_span(span_start1004, "Primitive")
        return result1005

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1009 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1797 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1798 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1799 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1800 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1801 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1802 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1803 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1804 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1805 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1806 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1807 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1808 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1809 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1810 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1811 = 1
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
                        _t1800 = _t1801
                    _t1799 = _t1800
                _t1798 = _t1799
            _t1797 = _t1798
        prediction1006 = _t1797
        if prediction1006 == 1:
            _t1813 = self.parse_term()
            term1008 = _t1813
            _t1814 = logic_pb2.RelTerm(term=term1008)
            _t1812 = _t1814
        else:
            if prediction1006 == 0:
                _t1816 = self.parse_specialized_value()
                specialized_value1007 = _t1816
                _t1817 = logic_pb2.RelTerm(specialized_value=specialized_value1007)
                _t1815 = _t1817
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1812 = _t1815
        result1010 = _t1812
        self.record_span(span_start1009, "RelTerm")
        return result1010

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1012 = self.span_start()
        self.consume_literal("#")
        _t1818 = self.parse_raw_value()
        raw_value1011 = _t1818
        result1013 = raw_value1011
        self.record_span(span_start1012, "Value")
        return result1013

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1019 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1819 = self.parse_name()
        name1014 = _t1819
        xs1015 = []
        cond1016 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1016:
            _t1820 = self.parse_rel_term()
            item1017 = _t1820
            xs1015.append(item1017)
            cond1016 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1018 = xs1015
        self.consume_literal(")")
        _t1821 = logic_pb2.RelAtom(name=name1014, terms=rel_terms1018)
        result1020 = _t1821
        self.record_span(span_start1019, "RelAtom")
        return result1020

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1023 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1822 = self.parse_term()
        term1021 = _t1822
        _t1823 = self.parse_term()
        term_31022 = _t1823
        self.consume_literal(")")
        _t1824 = logic_pb2.Cast(input=term1021, result=term_31022)
        result1024 = _t1824
        self.record_span(span_start1023, "Cast")
        return result1024

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1025 = []
        cond1026 = self.match_lookahead_literal("(", 0)
        while cond1026:
            _t1825 = self.parse_attribute()
            item1027 = _t1825
            xs1025.append(item1027)
            cond1026 = self.match_lookahead_literal("(", 0)
        attributes1028 = xs1025
        self.consume_literal(")")
        return attributes1028

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1034 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1826 = self.parse_name()
        name1029 = _t1826
        xs1030 = []
        cond1031 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1031:
            _t1827 = self.parse_raw_value()
            item1032 = _t1827
            xs1030.append(item1032)
            cond1031 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1033 = xs1030
        self.consume_literal(")")
        _t1828 = logic_pb2.Attribute(name=name1029, args=raw_values1033)
        result1035 = _t1828
        self.record_span(span_start1034, "Attribute")
        return result1035

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1042 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1036 = []
        cond1037 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1037:
            _t1829 = self.parse_relation_id()
            item1038 = _t1829
            xs1036.append(item1038)
            cond1037 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1039 = xs1036
        _t1830 = self.parse_script()
        script1040 = _t1830
        if self.match_lookahead_literal("(", 0):
            _t1832 = self.parse_attrs()
            _t1831 = _t1832
        else:
            _t1831 = None
        attrs1041 = _t1831
        self.consume_literal(")")
        _t1833 = logic_pb2.Algorithm(body=script1040, attrs=(attrs1041 if attrs1041 is not None else []))
        getattr(_t1833, 'global').extend(relation_ids1039)
        result1043 = _t1833
        self.record_span(span_start1042, "Algorithm")
        return result1043

    def parse_script(self) -> logic_pb2.Script:
        span_start1048 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1044 = []
        cond1045 = self.match_lookahead_literal("(", 0)
        while cond1045:
            _t1834 = self.parse_construct()
            item1046 = _t1834
            xs1044.append(item1046)
            cond1045 = self.match_lookahead_literal("(", 0)
        constructs1047 = xs1044
        self.consume_literal(")")
        _t1835 = logic_pb2.Script(constructs=constructs1047)
        result1049 = _t1835
        self.record_span(span_start1048, "Script")
        return result1049

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1053 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1837 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1838 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1839 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1840 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1841 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1842 = 1
                                else:
                                    _t1842 = -1
                                _t1841 = _t1842
                            _t1840 = _t1841
                        _t1839 = _t1840
                    _t1838 = _t1839
                _t1837 = _t1838
            _t1836 = _t1837
        else:
            _t1836 = -1
        prediction1050 = _t1836
        if prediction1050 == 1:
            _t1844 = self.parse_instruction()
            instruction1052 = _t1844
            _t1845 = logic_pb2.Construct(instruction=instruction1052)
            _t1843 = _t1845
        else:
            if prediction1050 == 0:
                _t1847 = self.parse_loop()
                loop1051 = _t1847
                _t1848 = logic_pb2.Construct(loop=loop1051)
                _t1846 = _t1848
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1843 = _t1846
        result1054 = _t1843
        self.record_span(span_start1053, "Construct")
        return result1054

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1058 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1849 = self.parse_init()
        init1055 = _t1849
        _t1850 = self.parse_script()
        script1056 = _t1850
        if self.match_lookahead_literal("(", 0):
            _t1852 = self.parse_attrs()
            _t1851 = _t1852
        else:
            _t1851 = None
        attrs1057 = _t1851
        self.consume_literal(")")
        _t1853 = logic_pb2.Loop(init=init1055, body=script1056, attrs=(attrs1057 if attrs1057 is not None else []))
        result1059 = _t1853
        self.record_span(span_start1058, "Loop")
        return result1059

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1060 = []
        cond1061 = self.match_lookahead_literal("(", 0)
        while cond1061:
            _t1854 = self.parse_instruction()
            item1062 = _t1854
            xs1060.append(item1062)
            cond1061 = self.match_lookahead_literal("(", 0)
        instructions1063 = xs1060
        self.consume_literal(")")
        return instructions1063

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1070 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1856 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1857 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1858 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1859 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1860 = 0
                            else:
                                _t1860 = -1
                            _t1859 = _t1860
                        _t1858 = _t1859
                    _t1857 = _t1858
                _t1856 = _t1857
            _t1855 = _t1856
        else:
            _t1855 = -1
        prediction1064 = _t1855
        if prediction1064 == 4:
            _t1862 = self.parse_monus_def()
            monus_def1069 = _t1862
            _t1863 = logic_pb2.Instruction(monus_def=monus_def1069)
            _t1861 = _t1863
        else:
            if prediction1064 == 3:
                _t1865 = self.parse_monoid_def()
                monoid_def1068 = _t1865
                _t1866 = logic_pb2.Instruction(monoid_def=monoid_def1068)
                _t1864 = _t1866
            else:
                if prediction1064 == 2:
                    _t1868 = self.parse_break()
                    break1067 = _t1868
                    _t1869 = logic_pb2.Instruction()
                    getattr(_t1869, 'break').CopyFrom(break1067)
                    _t1867 = _t1869
                else:
                    if prediction1064 == 1:
                        _t1871 = self.parse_upsert()
                        upsert1066 = _t1871
                        _t1872 = logic_pb2.Instruction(upsert=upsert1066)
                        _t1870 = _t1872
                    else:
                        if prediction1064 == 0:
                            _t1874 = self.parse_assign()
                            assign1065 = _t1874
                            _t1875 = logic_pb2.Instruction(assign=assign1065)
                            _t1873 = _t1875
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1870 = _t1873
                    _t1867 = _t1870
                _t1864 = _t1867
            _t1861 = _t1864
        result1071 = _t1861
        self.record_span(span_start1070, "Instruction")
        return result1071

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1075 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1876 = self.parse_relation_id()
        relation_id1072 = _t1876
        _t1877 = self.parse_abstraction()
        abstraction1073 = _t1877
        if self.match_lookahead_literal("(", 0):
            _t1879 = self.parse_attrs()
            _t1878 = _t1879
        else:
            _t1878 = None
        attrs1074 = _t1878
        self.consume_literal(")")
        _t1880 = logic_pb2.Assign(name=relation_id1072, body=abstraction1073, attrs=(attrs1074 if attrs1074 is not None else []))
        result1076 = _t1880
        self.record_span(span_start1075, "Assign")
        return result1076

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1080 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1881 = self.parse_relation_id()
        relation_id1077 = _t1881
        _t1882 = self.parse_abstraction_with_arity()
        abstraction_with_arity1078 = _t1882
        if self.match_lookahead_literal("(", 0):
            _t1884 = self.parse_attrs()
            _t1883 = _t1884
        else:
            _t1883 = None
        attrs1079 = _t1883
        self.consume_literal(")")
        _t1885 = logic_pb2.Upsert(name=relation_id1077, body=abstraction_with_arity1078[0], attrs=(attrs1079 if attrs1079 is not None else []), value_arity=abstraction_with_arity1078[1])
        result1081 = _t1885
        self.record_span(span_start1080, "Upsert")
        return result1081

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1886 = self.parse_bindings()
        bindings1082 = _t1886
        _t1887 = self.parse_formula()
        formula1083 = _t1887
        self.consume_literal(")")
        _t1888 = logic_pb2.Abstraction(vars=(list(bindings1082[0]) + list(bindings1082[1] if bindings1082[1] is not None else [])), value=formula1083)
        return (_t1888, len(bindings1082[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1087 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1889 = self.parse_relation_id()
        relation_id1084 = _t1889
        _t1890 = self.parse_abstraction()
        abstraction1085 = _t1890
        if self.match_lookahead_literal("(", 0):
            _t1892 = self.parse_attrs()
            _t1891 = _t1892
        else:
            _t1891 = None
        attrs1086 = _t1891
        self.consume_literal(")")
        _t1893 = logic_pb2.Break(name=relation_id1084, body=abstraction1085, attrs=(attrs1086 if attrs1086 is not None else []))
        result1088 = _t1893
        self.record_span(span_start1087, "Break")
        return result1088

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1093 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1894 = self.parse_monoid()
        monoid1089 = _t1894
        _t1895 = self.parse_relation_id()
        relation_id1090 = _t1895
        _t1896 = self.parse_abstraction_with_arity()
        abstraction_with_arity1091 = _t1896
        if self.match_lookahead_literal("(", 0):
            _t1898 = self.parse_attrs()
            _t1897 = _t1898
        else:
            _t1897 = None
        attrs1092 = _t1897
        self.consume_literal(")")
        _t1899 = logic_pb2.MonoidDef(monoid=monoid1089, name=relation_id1090, body=abstraction_with_arity1091[0], attrs=(attrs1092 if attrs1092 is not None else []), value_arity=abstraction_with_arity1091[1])
        result1094 = _t1899
        self.record_span(span_start1093, "MonoidDef")
        return result1094

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1100 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1901 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1902 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1903 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1904 = 2
                        else:
                            _t1904 = -1
                        _t1903 = _t1904
                    _t1902 = _t1903
                _t1901 = _t1902
            _t1900 = _t1901
        else:
            _t1900 = -1
        prediction1095 = _t1900
        if prediction1095 == 3:
            _t1906 = self.parse_sum_monoid()
            sum_monoid1099 = _t1906
            _t1907 = logic_pb2.Monoid(sum_monoid=sum_monoid1099)
            _t1905 = _t1907
        else:
            if prediction1095 == 2:
                _t1909 = self.parse_max_monoid()
                max_monoid1098 = _t1909
                _t1910 = logic_pb2.Monoid(max_monoid=max_monoid1098)
                _t1908 = _t1910
            else:
                if prediction1095 == 1:
                    _t1912 = self.parse_min_monoid()
                    min_monoid1097 = _t1912
                    _t1913 = logic_pb2.Monoid(min_monoid=min_monoid1097)
                    _t1911 = _t1913
                else:
                    if prediction1095 == 0:
                        _t1915 = self.parse_or_monoid()
                        or_monoid1096 = _t1915
                        _t1916 = logic_pb2.Monoid(or_monoid=or_monoid1096)
                        _t1914 = _t1916
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1911 = _t1914
                _t1908 = _t1911
            _t1905 = _t1908
        result1101 = _t1905
        self.record_span(span_start1100, "Monoid")
        return result1101

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1102 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1917 = logic_pb2.OrMonoid()
        result1103 = _t1917
        self.record_span(span_start1102, "OrMonoid")
        return result1103

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1105 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1918 = self.parse_type()
        type1104 = _t1918
        self.consume_literal(")")
        _t1919 = logic_pb2.MinMonoid(type=type1104)
        result1106 = _t1919
        self.record_span(span_start1105, "MinMonoid")
        return result1106

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1108 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1920 = self.parse_type()
        type1107 = _t1920
        self.consume_literal(")")
        _t1921 = logic_pb2.MaxMonoid(type=type1107)
        result1109 = _t1921
        self.record_span(span_start1108, "MaxMonoid")
        return result1109

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1111 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1922 = self.parse_type()
        type1110 = _t1922
        self.consume_literal(")")
        _t1923 = logic_pb2.SumMonoid(type=type1110)
        result1112 = _t1923
        self.record_span(span_start1111, "SumMonoid")
        return result1112

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1117 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1924 = self.parse_monoid()
        monoid1113 = _t1924
        _t1925 = self.parse_relation_id()
        relation_id1114 = _t1925
        _t1926 = self.parse_abstraction_with_arity()
        abstraction_with_arity1115 = _t1926
        if self.match_lookahead_literal("(", 0):
            _t1928 = self.parse_attrs()
            _t1927 = _t1928
        else:
            _t1927 = None
        attrs1116 = _t1927
        self.consume_literal(")")
        _t1929 = logic_pb2.MonusDef(monoid=monoid1113, name=relation_id1114, body=abstraction_with_arity1115[0], attrs=(attrs1116 if attrs1116 is not None else []), value_arity=abstraction_with_arity1115[1])
        result1118 = _t1929
        self.record_span(span_start1117, "MonusDef")
        return result1118

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1123 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1930 = self.parse_relation_id()
        relation_id1119 = _t1930
        _t1931 = self.parse_abstraction()
        abstraction1120 = _t1931
        _t1932 = self.parse_functional_dependency_keys()
        functional_dependency_keys1121 = _t1932
        _t1933 = self.parse_functional_dependency_values()
        functional_dependency_values1122 = _t1933
        self.consume_literal(")")
        _t1934 = logic_pb2.FunctionalDependency(guard=abstraction1120, keys=functional_dependency_keys1121, values=functional_dependency_values1122)
        _t1935 = logic_pb2.Constraint(name=relation_id1119, functional_dependency=_t1934)
        result1124 = _t1935
        self.record_span(span_start1123, "Constraint")
        return result1124

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1125 = []
        cond1126 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1126:
            _t1936 = self.parse_var()
            item1127 = _t1936
            xs1125.append(item1127)
            cond1126 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1128 = xs1125
        self.consume_literal(")")
        return vars1128

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1129 = []
        cond1130 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1130:
            _t1937 = self.parse_var()
            item1131 = _t1937
            xs1129.append(item1131)
            cond1130 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1132 = xs1129
        self.consume_literal(")")
        return vars1132

    def parse_data(self) -> logic_pb2.Data:
        span_start1138 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1939 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1940 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1941 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1942 = 1
                        else:
                            _t1942 = -1
                        _t1941 = _t1942
                    _t1940 = _t1941
                _t1939 = _t1940
            _t1938 = _t1939
        else:
            _t1938 = -1
        prediction1133 = _t1938
        if prediction1133 == 3:
            _t1944 = self.parse_iceberg_data()
            iceberg_data1137 = _t1944
            _t1945 = logic_pb2.Data(iceberg_data=iceberg_data1137)
            _t1943 = _t1945
        else:
            if prediction1133 == 2:
                _t1947 = self.parse_csv_data()
                csv_data1136 = _t1947
                _t1948 = logic_pb2.Data(csv_data=csv_data1136)
                _t1946 = _t1948
            else:
                if prediction1133 == 1:
                    _t1950 = self.parse_betree_relation()
                    betree_relation1135 = _t1950
                    _t1951 = logic_pb2.Data(betree_relation=betree_relation1135)
                    _t1949 = _t1951
                else:
                    if prediction1133 == 0:
                        _t1953 = self.parse_edb()
                        edb1134 = _t1953
                        _t1954 = logic_pb2.Data(edb=edb1134)
                        _t1952 = _t1954
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1949 = _t1952
                _t1946 = _t1949
            _t1943 = _t1946
        result1139 = _t1943
        self.record_span(span_start1138, "Data")
        return result1139

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1143 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1955 = self.parse_relation_id()
        relation_id1140 = _t1955
        _t1956 = self.parse_edb_path()
        edb_path1141 = _t1956
        _t1957 = self.parse_edb_types()
        edb_types1142 = _t1957
        self.consume_literal(")")
        _t1958 = logic_pb2.EDB(target_id=relation_id1140, path=edb_path1141, types=edb_types1142)
        result1144 = _t1958
        self.record_span(span_start1143, "EDB")
        return result1144

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1145 = []
        cond1146 = self.match_lookahead_terminal("STRING", 0)
        while cond1146:
            item1147 = self.consume_terminal("STRING")
            xs1145.append(item1147)
            cond1146 = self.match_lookahead_terminal("STRING", 0)
        strings1148 = xs1145
        self.consume_literal("]")
        return strings1148

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1149 = []
        cond1150 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1150:
            _t1959 = self.parse_type()
            item1151 = _t1959
            xs1149.append(item1151)
            cond1150 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1152 = xs1149
        self.consume_literal("]")
        return types1152

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1155 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1960 = self.parse_relation_id()
        relation_id1153 = _t1960
        _t1961 = self.parse_betree_info()
        betree_info1154 = _t1961
        self.consume_literal(")")
        _t1962 = logic_pb2.BeTreeRelation(name=relation_id1153, relation_info=betree_info1154)
        result1156 = _t1962
        self.record_span(span_start1155, "BeTreeRelation")
        return result1156

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1160 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1963 = self.parse_betree_info_key_types()
        betree_info_key_types1157 = _t1963
        _t1964 = self.parse_betree_info_value_types()
        betree_info_value_types1158 = _t1964
        _t1965 = self.parse_config_dict()
        config_dict1159 = _t1965
        self.consume_literal(")")
        _t1966 = self.construct_betree_info(betree_info_key_types1157, betree_info_value_types1158, config_dict1159)
        result1161 = _t1966
        self.record_span(span_start1160, "BeTreeInfo")
        return result1161

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1162 = []
        cond1163 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1163:
            _t1967 = self.parse_type()
            item1164 = _t1967
            xs1162.append(item1164)
            cond1163 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1165 = xs1162
        self.consume_literal(")")
        return types1165

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1166 = []
        cond1167 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1167:
            _t1968 = self.parse_type()
            item1168 = _t1968
            xs1166.append(item1168)
            cond1167 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1169 = xs1166
        self.consume_literal(")")
        return types1169

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1174 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1969 = self.parse_csvlocator()
        csvlocator1170 = _t1969
        _t1970 = self.parse_csv_config()
        csv_config1171 = _t1970
        _t1971 = self.parse_gnf_columns()
        gnf_columns1172 = _t1971
        _t1972 = self.parse_csv_asof()
        csv_asof1173 = _t1972
        self.consume_literal(")")
        _t1973 = logic_pb2.CSVData(locator=csvlocator1170, config=csv_config1171, columns=gnf_columns1172, asof=csv_asof1173)
        result1175 = _t1973
        self.record_span(span_start1174, "CSVData")
        return result1175

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1178 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1975 = self.parse_csv_locator_paths()
            _t1974 = _t1975
        else:
            _t1974 = None
        csv_locator_paths1176 = _t1974
        if self.match_lookahead_literal("(", 0):
            _t1977 = self.parse_csv_locator_inline_data()
            _t1976 = _t1977
        else:
            _t1976 = None
        csv_locator_inline_data1177 = _t1976
        self.consume_literal(")")
        _t1978 = logic_pb2.CSVLocator(paths=(csv_locator_paths1176 if csv_locator_paths1176 is not None else []), inline_data=(csv_locator_inline_data1177 if csv_locator_inline_data1177 is not None else "").encode())
        result1179 = _t1978
        self.record_span(span_start1178, "CSVLocator")
        return result1179

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1180 = []
        cond1181 = self.match_lookahead_terminal("STRING", 0)
        while cond1181:
            item1182 = self.consume_terminal("STRING")
            xs1180.append(item1182)
            cond1181 = self.match_lookahead_terminal("STRING", 0)
        strings1183 = xs1180
        self.consume_literal(")")
        return strings1183

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        formatted_string1184 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return formatted_string1184

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1187 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1979 = self.parse_config_dict()
        config_dict1185 = _t1979
        if self.match_lookahead_literal("(", 0):
            _t1981 = self.parse__storage_integration()
            _t1980 = _t1981
        else:
            _t1980 = None
        _storage_integration1186 = _t1980
        self.consume_literal(")")
        _t1982 = self.construct_csv_config(config_dict1185, _storage_integration1186)
        result1188 = _t1982
        self.record_span(span_start1187, "CSVConfig")
        return result1188

    def parse__storage_integration(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("(")
        self.consume_literal("storage_integration")
        _t1983 = self.parse_config_dict()
        config_dict1189 = _t1983
        self.consume_literal(")")
        return config_dict1189

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1190 = []
        cond1191 = self.match_lookahead_literal("(", 0)
        while cond1191:
            _t1984 = self.parse_gnf_column()
            item1192 = _t1984
            xs1190.append(item1192)
            cond1191 = self.match_lookahead_literal("(", 0)
        gnf_columns1193 = xs1190
        self.consume_literal(")")
        return gnf_columns1193

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1200 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1985 = self.parse_gnf_column_path()
        gnf_column_path1194 = _t1985
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1987 = self.parse_relation_id()
            _t1986 = _t1987
        else:
            _t1986 = None
        relation_id1195 = _t1986
        self.consume_literal("[")
        xs1196 = []
        cond1197 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1197:
            _t1988 = self.parse_type()
            item1198 = _t1988
            xs1196.append(item1198)
            cond1197 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1199 = xs1196
        self.consume_literal("]")
        self.consume_literal(")")
        _t1989 = logic_pb2.GNFColumn(column_path=gnf_column_path1194, target_id=relation_id1195, types=types1199)
        result1201 = _t1989
        self.record_span(span_start1200, "GNFColumn")
        return result1201

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1990 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1991 = 0
            else:
                _t1991 = -1
            _t1990 = _t1991
        prediction1202 = _t1990
        if prediction1202 == 1:
            self.consume_literal("[")
            xs1204 = []
            cond1205 = self.match_lookahead_terminal("STRING", 0)
            while cond1205:
                item1206 = self.consume_terminal("STRING")
                xs1204.append(item1206)
                cond1205 = self.match_lookahead_terminal("STRING", 0)
            strings1207 = xs1204
            self.consume_literal("]")
            _t1992 = strings1207
        else:
            if prediction1202 == 0:
                string1203 = self.consume_terminal("STRING")
                _t1993 = [string1203]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1992 = _t1993
        return _t1992

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1208 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1208

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1215 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1994 = self.parse_iceberg_locator()
        iceberg_locator1209 = _t1994
        _t1995 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1210 = _t1995
        _t1996 = self.parse_gnf_columns()
        gnf_columns1211 = _t1996
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t1998 = self.parse_iceberg_from_snapshot()
            _t1997 = _t1998
        else:
            _t1997 = None
        iceberg_from_snapshot1212 = _t1997
        if self.match_lookahead_literal("(", 0):
            _t2000 = self.parse_iceberg_to_snapshot()
            _t1999 = _t2000
        else:
            _t1999 = None
        iceberg_to_snapshot1213 = _t1999
        _t2001 = self.parse_boolean_value()
        boolean_value1214 = _t2001
        self.consume_literal(")")
        _t2002 = self.construct_iceberg_data(iceberg_locator1209, iceberg_catalog_config1210, gnf_columns1211, iceberg_from_snapshot1212, iceberg_to_snapshot1213, boolean_value1214)
        result1216 = _t2002
        self.record_span(span_start1215, "IcebergData")
        return result1216

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1220 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t2003 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1217 = _t2003
        _t2004 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1218 = _t2004
        _t2005 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1219 = _t2005
        self.consume_literal(")")
        _t2006 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1217, namespace=iceberg_locator_namespace1218, warehouse=iceberg_locator_warehouse1219)
        result1221 = _t2006
        self.record_span(span_start1220, "IcebergLocator")
        return result1221

    def parse_iceberg_locator_table_name(self) -> str:
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1222 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1222

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1223 = []
        cond1224 = self.match_lookahead_terminal("STRING", 0)
        while cond1224:
            item1225 = self.consume_terminal("STRING")
            xs1223.append(item1225)
            cond1224 = self.match_lookahead_terminal("STRING", 0)
        strings1226 = xs1223
        self.consume_literal(")")
        return strings1226

    def parse_iceberg_locator_warehouse(self) -> str:
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string1227 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1227

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1232 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t2007 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1228 = _t2007
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t2009 = self.parse_iceberg_catalog_config_scope()
            _t2008 = _t2009
        else:
            _t2008 = None
        iceberg_catalog_config_scope1229 = _t2008
        _t2010 = self.parse_iceberg_properties()
        iceberg_properties1230 = _t2010
        _t2011 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1231 = _t2011
        self.consume_literal(")")
        _t2012 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1228, iceberg_catalog_config_scope1229, iceberg_properties1230, iceberg_auth_properties1231)
        result1233 = _t2012
        self.record_span(span_start1232, "IcebergCatalogConfig")
        return result1233

    def parse_iceberg_catalog_uri(self) -> str:
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1234 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1234

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1235 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1235

    def parse_iceberg_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1236 = []
        cond1237 = self.match_lookahead_literal("(", 0)
        while cond1237:
            _t2013 = self.parse_iceberg_property_entry()
            item1238 = _t2013
            xs1236.append(item1238)
            cond1237 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1239 = xs1236
        self.consume_literal(")")
        return iceberg_property_entrys1239

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1240 = self.consume_terminal("STRING")
        string_31241 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1240, string_31241,)

    def parse_iceberg_auth_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1242 = []
        cond1243 = self.match_lookahead_literal("(", 0)
        while cond1243:
            _t2014 = self.parse_iceberg_masked_property_entry()
            item1244 = _t2014
            xs1242.append(item1244)
            cond1243 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1245 = xs1242
        self.consume_literal(")")
        return iceberg_masked_property_entrys1245

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1246 = self.consume_terminal("STRING")
        string_31247 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1246, string_31247,)

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1248 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1248

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1249 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1249

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1251 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2015 = self.parse_fragment_id()
        fragment_id1250 = _t2015
        self.consume_literal(")")
        _t2016 = transactions_pb2.Undefine(fragment_id=fragment_id1250)
        result1252 = _t2016
        self.record_span(span_start1251, "Undefine")
        return result1252

    def parse_context(self) -> transactions_pb2.Context:
        span_start1257 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1253 = []
        cond1254 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1254:
            _t2017 = self.parse_relation_id()
            item1255 = _t2017
            xs1253.append(item1255)
            cond1254 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1256 = xs1253
        self.consume_literal(")")
        _t2018 = transactions_pb2.Context(relations=relation_ids1256)
        result1258 = _t2018
        self.record_span(span_start1257, "Context")
        return result1258

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1264 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t2019 = self.parse_edb_path()
        edb_path1259 = _t2019
        xs1260 = []
        cond1261 = self.match_lookahead_literal("[", 0)
        while cond1261:
            _t2020 = self.parse_snapshot_mapping()
            item1262 = _t2020
            xs1260.append(item1262)
            cond1261 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1263 = xs1260
        self.consume_literal(")")
        _t2021 = transactions_pb2.Snapshot(prefix=edb_path1259, mappings=snapshot_mappings1263)
        result1265 = _t2021
        self.record_span(span_start1264, "Snapshot")
        return result1265

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1268 = self.span_start()
        _t2022 = self.parse_edb_path()
        edb_path1266 = _t2022
        _t2023 = self.parse_relation_id()
        relation_id1267 = _t2023
        _t2024 = transactions_pb2.SnapshotMapping(destination_path=edb_path1266, source_relation=relation_id1267)
        result1269 = _t2024
        self.record_span(span_start1268, "SnapshotMapping")
        return result1269

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1270 = []
        cond1271 = self.match_lookahead_literal("(", 0)
        while cond1271:
            _t2025 = self.parse_read()
            item1272 = _t2025
            xs1270.append(item1272)
            cond1271 = self.match_lookahead_literal("(", 0)
        reads1273 = xs1270
        self.consume_literal(")")
        return reads1273

    def parse_read(self) -> transactions_pb2.Read:
        span_start1281 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2027 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2028 = 1
                else:
                    if self.match_lookahead_literal("export_output", 1):
                        _t2029 = 5
                    else:
                        if self.match_lookahead_literal("export_iceberg", 1):
                            _t2030 = 4
                        else:
                            if self.match_lookahead_literal("export", 1):
                                _t2031 = 4
                            else:
                                if self.match_lookahead_literal("demand", 1):
                                    _t2032 = 0
                                else:
                                    if self.match_lookahead_literal("abort", 1):
                                        _t2033 = 3
                                    else:
                                        _t2033 = -1
                                    _t2032 = _t2033
                                _t2031 = _t2032
                            _t2030 = _t2031
                        _t2029 = _t2030
                    _t2028 = _t2029
                _t2027 = _t2028
            _t2026 = _t2027
        else:
            _t2026 = -1
        prediction1274 = _t2026
        if prediction1274 == 5:
            _t2035 = self.parse_export_output()
            export_output1280 = _t2035
            _t2036 = transactions_pb2.Read(export_output=export_output1280)
            _t2034 = _t2036
        else:
            if prediction1274 == 4:
                _t2038 = self.parse_export()
                export1279 = _t2038
                _t2039 = transactions_pb2.Read(export=export1279)
                _t2037 = _t2039
            else:
                if prediction1274 == 3:
                    _t2041 = self.parse_abort()
                    abort1278 = _t2041
                    _t2042 = transactions_pb2.Read(abort=abort1278)
                    _t2040 = _t2042
                else:
                    if prediction1274 == 2:
                        _t2044 = self.parse_what_if()
                        what_if1277 = _t2044
                        _t2045 = transactions_pb2.Read(what_if=what_if1277)
                        _t2043 = _t2045
                    else:
                        if prediction1274 == 1:
                            _t2047 = self.parse_output()
                            output1276 = _t2047
                            _t2048 = transactions_pb2.Read(output=output1276)
                            _t2046 = _t2048
                        else:
                            if prediction1274 == 0:
                                _t2050 = self.parse_demand()
                                demand1275 = _t2050
                                _t2051 = transactions_pb2.Read(demand=demand1275)
                                _t2049 = _t2051
                            else:
                                raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                            _t2046 = _t2049
                        _t2043 = _t2046
                    _t2040 = _t2043
                _t2037 = _t2040
            _t2034 = _t2037
        result1282 = _t2034
        self.record_span(span_start1281, "Read")
        return result1282

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1284 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2052 = self.parse_relation_id()
        relation_id1283 = _t2052
        self.consume_literal(")")
        _t2053 = transactions_pb2.Demand(relation_id=relation_id1283)
        result1285 = _t2053
        self.record_span(span_start1284, "Demand")
        return result1285

    def parse_output(self) -> transactions_pb2.Output:
        span_start1288 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2054 = self.parse_name()
        name1286 = _t2054
        _t2055 = self.parse_relation_id()
        relation_id1287 = _t2055
        self.consume_literal(")")
        _t2056 = transactions_pb2.Output(name=name1286, relation_id=relation_id1287)
        result1289 = _t2056
        self.record_span(span_start1288, "Output")
        return result1289

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1292 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2057 = self.parse_name()
        name1290 = _t2057
        _t2058 = self.parse_epoch()
        epoch1291 = _t2058
        self.consume_literal(")")
        _t2059 = transactions_pb2.WhatIf(branch=name1290, epoch=epoch1291)
        result1293 = _t2059
        self.record_span(span_start1292, "WhatIf")
        return result1293

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1296 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2061 = self.parse_name()
            _t2060 = _t2061
        else:
            _t2060 = None
        name1294 = _t2060
        _t2062 = self.parse_relation_id()
        relation_id1295 = _t2062
        self.consume_literal(")")
        _t2063 = transactions_pb2.Abort(name=(name1294 if name1294 is not None else "abort"), relation_id=relation_id1295)
        result1297 = _t2063
        self.record_span(span_start1296, "Abort")
        return result1297

    def parse_export(self) -> transactions_pb2.Export:
        span_start1301 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2065 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2066 = 0
                else:
                    _t2066 = -1
                _t2065 = _t2066
            _t2064 = _t2065
        else:
            _t2064 = -1
        prediction1298 = _t2064
        if prediction1298 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2068 = self.parse_export_iceberg_config()
            export_iceberg_config1300 = _t2068
            self.consume_literal(")")
            _t2069 = transactions_pb2.Export(iceberg_config=export_iceberg_config1300)
            _t2067 = _t2069
        else:
            if prediction1298 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2071 = self.parse_export_csv_config()
                export_csv_config1299 = _t2071
                self.consume_literal(")")
                _t2072 = transactions_pb2.Export(csv_config=export_csv_config1299)
                _t2070 = _t2072
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2067 = _t2070
        result1302 = _t2067
        self.record_span(span_start1301, "Export")
        return result1302

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1310 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2074 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2075 = 1
                else:
                    _t2075 = -1
                _t2074 = _t2075
            _t2073 = _t2074
        else:
            _t2073 = -1
        prediction1303 = _t2073
        if prediction1303 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2077 = self.parse_export_csv_path()
            export_csv_path1307 = _t2077
            _t2078 = self.parse_export_csv_columns_list()
            export_csv_columns_list1308 = _t2078
            _t2079 = self.parse_config_dict()
            config_dict1309 = _t2079
            self.consume_literal(")")
            _t2080 = self.construct_export_csv_config(export_csv_path1307, export_csv_columns_list1308, config_dict1309)
            _t2076 = _t2080
        else:
            if prediction1303 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2082 = self.parse_export_csv_path()
                export_csv_path1304 = _t2082
                _t2083 = self.parse_export_csv_source()
                export_csv_source1305 = _t2083
                _t2084 = self.parse_csv_config()
                csv_config1306 = _t2084
                self.consume_literal(")")
                _t2085 = self.construct_export_csv_config_with_source(export_csv_path1304, export_csv_source1305, csv_config1306)
                _t2081 = _t2085
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2076 = _t2081
        result1311 = _t2076
        self.record_span(span_start1310, "ExportCSVConfig")
        return result1311

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1312 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1312

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1319 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2087 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2088 = 0
                else:
                    _t2088 = -1
                _t2087 = _t2088
            _t2086 = _t2087
        else:
            _t2086 = -1
        prediction1313 = _t2086
        if prediction1313 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2090 = self.parse_relation_id()
            relation_id1318 = _t2090
            self.consume_literal(")")
            _t2091 = transactions_pb2.ExportCSVSource(table_def=relation_id1318)
            _t2089 = _t2091
        else:
            if prediction1313 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1314 = []
                cond1315 = self.match_lookahead_literal("(", 0)
                while cond1315:
                    _t2093 = self.parse_export_csv_column()
                    item1316 = _t2093
                    xs1314.append(item1316)
                    cond1315 = self.match_lookahead_literal("(", 0)
                export_csv_columns1317 = xs1314
                self.consume_literal(")")
                _t2094 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1317)
                _t2095 = transactions_pb2.ExportCSVSource(gnf_columns=_t2094)
                _t2092 = _t2095
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2089 = _t2092
        result1320 = _t2089
        self.record_span(span_start1319, "ExportCSVSource")
        return result1320

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1323 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1321 = self.consume_terminal("STRING")
        _t2096 = self.parse_relation_id()
        relation_id1322 = _t2096
        self.consume_literal(")")
        _t2097 = transactions_pb2.ExportCSVColumn(column_name=string1321, column_data=relation_id1322)
        result1324 = _t2097
        self.record_span(span_start1323, "ExportCSVColumn")
        return result1324

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1325 = []
        cond1326 = self.match_lookahead_literal("(", 0)
        while cond1326:
            _t2098 = self.parse_export_csv_column()
            item1327 = _t2098
            xs1325.append(item1327)
            cond1326 = self.match_lookahead_literal("(", 0)
        export_csv_columns1328 = xs1325
        self.consume_literal(")")
        return export_csv_columns1328

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1334 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2099 = self.parse_iceberg_locator()
        iceberg_locator1329 = _t2099
        _t2100 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1330 = _t2100
        _t2101 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1331 = _t2101
        _t2102 = self.parse_iceberg_table_properties()
        iceberg_table_properties1332 = _t2102
        if self.match_lookahead_literal("{", 0):
            _t2104 = self.parse_config_dict()
            _t2103 = _t2104
        else:
            _t2103 = None
        config_dict1333 = _t2103
        self.consume_literal(")")
        _t2105 = self.construct_export_iceberg_config_full(iceberg_locator1329, iceberg_catalog_config1330, export_iceberg_table_def1331, iceberg_table_properties1332, config_dict1333)
        result1335 = _t2105
        self.record_span(span_start1334, "ExportIcebergConfig")
        return result1335

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1337 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2106 = self.parse_relation_id()
        relation_id1336 = _t2106
        self.consume_literal(")")
        result1338 = relation_id1336
        self.record_span(span_start1337, "RelationId")
        return result1338

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1339 = []
        cond1340 = self.match_lookahead_literal("(", 0)
        while cond1340:
            _t2107 = self.parse_iceberg_property_entry()
            item1341 = _t2107
            xs1339.append(item1341)
            cond1340 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1342 = xs1339
        self.consume_literal(")")
        return iceberg_property_entrys1342

    def parse_export_output(self) -> transactions_pb2.ExportOutput:
        span_start1344 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_output")
        _t2108 = self.parse_export_csv_output()
        export_csv_output1343 = _t2108
        self.consume_literal(")")
        _t2109 = transactions_pb2.ExportOutput(csv=export_csv_output1343)
        result1345 = _t2109
        self.record_span(span_start1344, "ExportOutput")
        return result1345

    def parse_export_csv_output(self) -> transactions_pb2.ExportCSVOutput:
        span_start1348 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv")
        _t2110 = self.parse_export_csv_source()
        export_csv_source1346 = _t2110
        _t2111 = self.parse_csv_config()
        csv_config1347 = _t2111
        self.consume_literal(")")
        _t2112 = transactions_pb2.ExportCSVOutput(csv_source=export_csv_source1346, csv_config=csv_config1347)
        result1349 = _t2112
        self.record_span(span_start1348, "ExportCSVOutput")
        return result1349


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
