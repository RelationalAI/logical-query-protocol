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
            _t2111 = value.HasField("int32_value")
        else:
            _t2111 = False
        if _t2111:
            assert value is not None
            return value.int32_value
        else:
            _t2112 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2113 = value.HasField("int_value")
        else:
            _t2113 = False
        if _t2113:
            assert value is not None
            return value.int_value
        else:
            _t2114 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2115 = value.HasField("string_value")
        else:
            _t2115 = False
        if _t2115:
            assert value is not None
            return value.string_value
        else:
            _t2116 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2117 = value.HasField("boolean_value")
        else:
            _t2117 = False
        if _t2117:
            assert value is not None
            return value.boolean_value
        else:
            _t2118 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2119 = value.HasField("string_value")
        else:
            _t2119 = False
        if _t2119:
            assert value is not None
            return [value.string_value]
        else:
            _t2120 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2121 = value.HasField("int_value")
        else:
            _t2121 = False
        if _t2121:
            assert value is not None
            return value.int_value
        else:
            _t2122 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2123 = value.HasField("float_value")
        else:
            _t2123 = False
        if _t2123:
            assert value is not None
            return value.float_value
        else:
            _t2124 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2125 = value.HasField("string_value")
        else:
            _t2125 = False
        if _t2125:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2126 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2127 = value.HasField("uint128_value")
        else:
            _t2127 = False
        if _t2127:
            assert value is not None
            return value.uint128_value
        else:
            _t2128 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2129 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2129
        _t2130 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2130
        _t2131 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2131
        _t2132 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2132
        _t2133 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2133
        _t2134 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2134
        _t2135 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2135
        _t2136 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2136
        _t2137 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2137
        _t2138 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2138
        _t2139 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t2139
        _t2140 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2140
        _t2141 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t2141

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2142 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2142
        _t2143 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2143
        _t2144 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2144
        _t2145 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2145
        _t2146 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2146
        _t2147 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2147
        _t2148 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2148
        _t2149 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2149
        _t2150 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2150
        _t2151 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2151
        _t2152 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2152

    def default_configure(self) -> transactions_pb2.Configure:
        _t2153 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2153
        _t2154 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2154

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
        _t2155 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2155
        _t2156 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2156
        _t2157 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2157

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2158 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2158
        _t2159 = self._extract_value_string(config.get("compression"), "")
        compression = _t2159
        _t2160 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2160
        _t2161 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2161
        _t2162 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2162
        _t2163 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2163
        _t2164 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2164
        _t2165 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2165

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2166 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2166

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2167 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2167

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[logic_pb2.GNFColumn], from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2168 = logic_pb2.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2168

    def construct_csv_data(self, locator: logic_pb2.CSVLocator, config: logic_pb2.CSVConfig, columns_opt: Sequence[logic_pb2.GNFColumn] | None, target_opt: logic_pb2.CSVTarget | None, asof: str) -> logic_pb2.CSVData:
        _t2169 = logic_pb2.CSVData(locator=locator, config=config, columns=(columns_opt if columns_opt is not None else []), asof=asof, target=target_opt)
        return _t2169

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2170 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2170
        _t2171 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2171
        _t2172 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2172
        table_props = dict(table_property_pairs)
        _t2173 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2173

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start683 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1355 = self.parse_configure()
            _t1354 = _t1355
        else:
            _t1354 = None
        configure677 = _t1354
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1357 = self.parse_sync()
            _t1356 = _t1357
        else:
            _t1356 = None
        sync678 = _t1356
        xs679 = []
        cond680 = self.match_lookahead_literal("(", 0)
        while cond680:
            _t1358 = self.parse_epoch()
            item681 = _t1358
            xs679.append(item681)
            cond680 = self.match_lookahead_literal("(", 0)
        epochs682 = xs679
        self.consume_literal(")")
        _t1359 = self.default_configure()
        _t1360 = transactions_pb2.Transaction(epochs=epochs682, configure=(configure677 if configure677 is not None else _t1359), sync=sync678)
        result684 = _t1360
        self.record_span(span_start683, "Transaction")
        return result684

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start686 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1361 = self.parse_config_dict()
        config_dict685 = _t1361
        self.consume_literal(")")
        _t1362 = self.construct_configure(config_dict685)
        result687 = _t1362
        self.record_span(span_start686, "Configure")
        return result687

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs688 = []
        cond689 = self.match_lookahead_literal(":", 0)
        while cond689:
            _t1363 = self.parse_config_key_value()
            item690 = _t1363
            xs688.append(item690)
            cond689 = self.match_lookahead_literal(":", 0)
        config_key_values691 = xs688
        self.consume_literal("}")
        return config_key_values691

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol692 = self.consume_terminal("SYMBOL")
        _t1364 = self.parse_raw_value()
        raw_value693 = _t1364
        return (symbol692, raw_value693,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start707 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1365 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1366 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1367 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1369 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1370 = 0
                            else:
                                _t1370 = -1
                            _t1369 = _t1370
                        _t1368 = _t1369
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1371 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1372 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1373 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1374 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1375 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1376 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1377 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1378 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1379 = 10
                                                        else:
                                                            _t1379 = -1
                                                        _t1378 = _t1379
                                                    _t1377 = _t1378
                                                _t1376 = _t1377
                                            _t1375 = _t1376
                                        _t1374 = _t1375
                                    _t1373 = _t1374
                                _t1372 = _t1373
                            _t1371 = _t1372
                        _t1368 = _t1371
                    _t1367 = _t1368
                _t1366 = _t1367
            _t1365 = _t1366
        prediction694 = _t1365
        if prediction694 == 12:
            _t1381 = self.parse_boolean_value()
            boolean_value706 = _t1381
            _t1382 = logic_pb2.Value(boolean_value=boolean_value706)
            _t1380 = _t1382
        else:
            if prediction694 == 11:
                self.consume_literal("missing")
                _t1384 = logic_pb2.MissingValue()
                _t1385 = logic_pb2.Value(missing_value=_t1384)
                _t1383 = _t1385
            else:
                if prediction694 == 10:
                    decimal705 = self.consume_terminal("DECIMAL")
                    _t1387 = logic_pb2.Value(decimal_value=decimal705)
                    _t1386 = _t1387
                else:
                    if prediction694 == 9:
                        int128704 = self.consume_terminal("INT128")
                        _t1389 = logic_pb2.Value(int128_value=int128704)
                        _t1388 = _t1389
                    else:
                        if prediction694 == 8:
                            uint128703 = self.consume_terminal("UINT128")
                            _t1391 = logic_pb2.Value(uint128_value=uint128703)
                            _t1390 = _t1391
                        else:
                            if prediction694 == 7:
                                uint32702 = self.consume_terminal("UINT32")
                                _t1393 = logic_pb2.Value(uint32_value=uint32702)
                                _t1392 = _t1393
                            else:
                                if prediction694 == 6:
                                    float701 = self.consume_terminal("FLOAT")
                                    _t1395 = logic_pb2.Value(float_value=float701)
                                    _t1394 = _t1395
                                else:
                                    if prediction694 == 5:
                                        float32700 = self.consume_terminal("FLOAT32")
                                        _t1397 = logic_pb2.Value(float32_value=float32700)
                                        _t1396 = _t1397
                                    else:
                                        if prediction694 == 4:
                                            int699 = self.consume_terminal("INT")
                                            _t1399 = logic_pb2.Value(int_value=int699)
                                            _t1398 = _t1399
                                        else:
                                            if prediction694 == 3:
                                                int32698 = self.consume_terminal("INT32")
                                                _t1401 = logic_pb2.Value(int32_value=int32698)
                                                _t1400 = _t1401
                                            else:
                                                if prediction694 == 2:
                                                    string697 = self.consume_terminal("STRING")
                                                    _t1403 = logic_pb2.Value(string_value=string697)
                                                    _t1402 = _t1403
                                                else:
                                                    if prediction694 == 1:
                                                        _t1405 = self.parse_raw_datetime()
                                                        raw_datetime696 = _t1405
                                                        _t1406 = logic_pb2.Value(datetime_value=raw_datetime696)
                                                        _t1404 = _t1406
                                                    else:
                                                        if prediction694 == 0:
                                                            _t1408 = self.parse_raw_date()
                                                            raw_date695 = _t1408
                                                            _t1409 = logic_pb2.Value(date_value=raw_date695)
                                                            _t1407 = _t1409
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1404 = _t1407
                                                    _t1402 = _t1404
                                                _t1400 = _t1402
                                            _t1398 = _t1400
                                        _t1396 = _t1398
                                    _t1394 = _t1396
                                _t1392 = _t1394
                            _t1390 = _t1392
                        _t1388 = _t1390
                    _t1386 = _t1388
                _t1383 = _t1386
            _t1380 = _t1383
        result708 = _t1380
        self.record_span(span_start707, "Value")
        return result708

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start712 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int709 = self.consume_terminal("INT")
        int_3710 = self.consume_terminal("INT")
        int_4711 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1410 = logic_pb2.DateValue(year=int(int709), month=int(int_3710), day=int(int_4711))
        result713 = _t1410
        self.record_span(span_start712, "DateValue")
        return result713

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start721 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int714 = self.consume_terminal("INT")
        int_3715 = self.consume_terminal("INT")
        int_4716 = self.consume_terminal("INT")
        int_5717 = self.consume_terminal("INT")
        int_6718 = self.consume_terminal("INT")
        int_7719 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1411 = self.consume_terminal("INT")
        else:
            _t1411 = None
        int_8720 = _t1411
        self.consume_literal(")")
        _t1412 = logic_pb2.DateTimeValue(year=int(int714), month=int(int_3715), day=int(int_4716), hour=int(int_5717), minute=int(int_6718), second=int(int_7719), microsecond=int((int_8720 if int_8720 is not None else 0)))
        result722 = _t1412
        self.record_span(span_start721, "DateTimeValue")
        return result722

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1413 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1414 = 1
            else:
                _t1414 = -1
            _t1413 = _t1414
        prediction723 = _t1413
        if prediction723 == 1:
            self.consume_literal("false")
            _t1415 = False
        else:
            if prediction723 == 0:
                self.consume_literal("true")
                _t1416 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1415 = _t1416
        return _t1415

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start728 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs724 = []
        cond725 = self.match_lookahead_literal(":", 0)
        while cond725:
            _t1417 = self.parse_fragment_id()
            item726 = _t1417
            xs724.append(item726)
            cond725 = self.match_lookahead_literal(":", 0)
        fragment_ids727 = xs724
        self.consume_literal(")")
        _t1418 = transactions_pb2.Sync(fragments=fragment_ids727)
        result729 = _t1418
        self.record_span(span_start728, "Sync")
        return result729

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start731 = self.span_start()
        self.consume_literal(":")
        symbol730 = self.consume_terminal("SYMBOL")
        result732 = fragments_pb2.FragmentId(id=symbol730.encode())
        self.record_span(span_start731, "FragmentId")
        return result732

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start735 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1420 = self.parse_epoch_writes()
            _t1419 = _t1420
        else:
            _t1419 = None
        epoch_writes733 = _t1419
        if self.match_lookahead_literal("(", 0):
            _t1422 = self.parse_epoch_reads()
            _t1421 = _t1422
        else:
            _t1421 = None
        epoch_reads734 = _t1421
        self.consume_literal(")")
        _t1423 = transactions_pb2.Epoch(writes=(epoch_writes733 if epoch_writes733 is not None else []), reads=(epoch_reads734 if epoch_reads734 is not None else []))
        result736 = _t1423
        self.record_span(span_start735, "Epoch")
        return result736

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs737 = []
        cond738 = self.match_lookahead_literal("(", 0)
        while cond738:
            _t1424 = self.parse_write()
            item739 = _t1424
            xs737.append(item739)
            cond738 = self.match_lookahead_literal("(", 0)
        writes740 = xs737
        self.consume_literal(")")
        return writes740

    def parse_write(self) -> transactions_pb2.Write:
        span_start746 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1426 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1427 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1428 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1429 = 2
                        else:
                            _t1429 = -1
                        _t1428 = _t1429
                    _t1427 = _t1428
                _t1426 = _t1427
            _t1425 = _t1426
        else:
            _t1425 = -1
        prediction741 = _t1425
        if prediction741 == 3:
            _t1431 = self.parse_snapshot()
            snapshot745 = _t1431
            _t1432 = transactions_pb2.Write(snapshot=snapshot745)
            _t1430 = _t1432
        else:
            if prediction741 == 2:
                _t1434 = self.parse_context()
                context744 = _t1434
                _t1435 = transactions_pb2.Write(context=context744)
                _t1433 = _t1435
            else:
                if prediction741 == 1:
                    _t1437 = self.parse_undefine()
                    undefine743 = _t1437
                    _t1438 = transactions_pb2.Write(undefine=undefine743)
                    _t1436 = _t1438
                else:
                    if prediction741 == 0:
                        _t1440 = self.parse_define()
                        define742 = _t1440
                        _t1441 = transactions_pb2.Write(define=define742)
                        _t1439 = _t1441
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1436 = _t1439
                _t1433 = _t1436
            _t1430 = _t1433
        result747 = _t1430
        self.record_span(span_start746, "Write")
        return result747

    def parse_define(self) -> transactions_pb2.Define:
        span_start749 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1442 = self.parse_fragment()
        fragment748 = _t1442
        self.consume_literal(")")
        _t1443 = transactions_pb2.Define(fragment=fragment748)
        result750 = _t1443
        self.record_span(span_start749, "Define")
        return result750

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start756 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1444 = self.parse_new_fragment_id()
        new_fragment_id751 = _t1444
        xs752 = []
        cond753 = self.match_lookahead_literal("(", 0)
        while cond753:
            _t1445 = self.parse_declaration()
            item754 = _t1445
            xs752.append(item754)
            cond753 = self.match_lookahead_literal("(", 0)
        declarations755 = xs752
        self.consume_literal(")")
        result757 = self.construct_fragment(new_fragment_id751, declarations755)
        self.record_span(span_start756, "Fragment")
        return result757

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start759 = self.span_start()
        _t1446 = self.parse_fragment_id()
        fragment_id758 = _t1446
        self.start_fragment(fragment_id758)
        result760 = fragment_id758
        self.record_span(span_start759, "FragmentId")
        return result760

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start766 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1448 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1449 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1450 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1451 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1452 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1453 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1454 = 1
                                    else:
                                        _t1454 = -1
                                    _t1453 = _t1454
                                _t1452 = _t1453
                            _t1451 = _t1452
                        _t1450 = _t1451
                    _t1449 = _t1450
                _t1448 = _t1449
            _t1447 = _t1448
        else:
            _t1447 = -1
        prediction761 = _t1447
        if prediction761 == 3:
            _t1456 = self.parse_data()
            data765 = _t1456
            _t1457 = logic_pb2.Declaration(data=data765)
            _t1455 = _t1457
        else:
            if prediction761 == 2:
                _t1459 = self.parse_constraint()
                constraint764 = _t1459
                _t1460 = logic_pb2.Declaration(constraint=constraint764)
                _t1458 = _t1460
            else:
                if prediction761 == 1:
                    _t1462 = self.parse_algorithm()
                    algorithm763 = _t1462
                    _t1463 = logic_pb2.Declaration(algorithm=algorithm763)
                    _t1461 = _t1463
                else:
                    if prediction761 == 0:
                        _t1465 = self.parse_def()
                        def762 = _t1465
                        _t1466 = logic_pb2.Declaration()
                        getattr(_t1466, 'def').CopyFrom(def762)
                        _t1464 = _t1466
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1461 = _t1464
                _t1458 = _t1461
            _t1455 = _t1458
        result767 = _t1455
        self.record_span(span_start766, "Declaration")
        return result767

    def parse_def(self) -> logic_pb2.Def:
        span_start771 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1467 = self.parse_relation_id()
        relation_id768 = _t1467
        _t1468 = self.parse_abstraction()
        abstraction769 = _t1468
        if self.match_lookahead_literal("(", 0):
            _t1470 = self.parse_attrs()
            _t1469 = _t1470
        else:
            _t1469 = None
        attrs770 = _t1469
        self.consume_literal(")")
        _t1471 = logic_pb2.Def(name=relation_id768, body=abstraction769, attrs=(attrs770 if attrs770 is not None else []))
        result772 = _t1471
        self.record_span(span_start771, "Def")
        return result772

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start776 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1472 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1473 = 1
            else:
                _t1473 = -1
            _t1472 = _t1473
        prediction773 = _t1472
        if prediction773 == 1:
            uint128775 = self.consume_terminal("UINT128")
            _t1474 = logic_pb2.RelationId(id_low=uint128775.low, id_high=uint128775.high)
        else:
            if prediction773 == 0:
                self.consume_literal(":")
                symbol774 = self.consume_terminal("SYMBOL")
                _t1475 = self.relation_id_from_string(symbol774)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1474 = _t1475
        result777 = _t1474
        self.record_span(span_start776, "RelationId")
        return result777

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start780 = self.span_start()
        self.consume_literal("(")
        _t1476 = self.parse_bindings()
        bindings778 = _t1476
        _t1477 = self.parse_formula()
        formula779 = _t1477
        self.consume_literal(")")
        _t1478 = logic_pb2.Abstraction(vars=(list(bindings778[0]) + list(bindings778[1] if bindings778[1] is not None else [])), value=formula779)
        result781 = _t1478
        self.record_span(span_start780, "Abstraction")
        return result781

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs782 = []
        cond783 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond783:
            _t1479 = self.parse_binding()
            item784 = _t1479
            xs782.append(item784)
            cond783 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings785 = xs782
        if self.match_lookahead_literal("|", 0):
            _t1481 = self.parse_value_bindings()
            _t1480 = _t1481
        else:
            _t1480 = None
        value_bindings786 = _t1480
        self.consume_literal("]")
        return (bindings785, (value_bindings786 if value_bindings786 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start789 = self.span_start()
        symbol787 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1482 = self.parse_type()
        type788 = _t1482
        _t1483 = logic_pb2.Var(name=symbol787)
        _t1484 = logic_pb2.Binding(var=_t1483, type=type788)
        result790 = _t1484
        self.record_span(span_start789, "Binding")
        return result790

    def parse_type(self) -> logic_pb2.Type:
        span_start806 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1485 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1486 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1487 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1488 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1489 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1490 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1491 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1492 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1493 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1494 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1495 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1496 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1497 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1498 = 9
                                                            else:
                                                                _t1498 = -1
                                                            _t1497 = _t1498
                                                        _t1496 = _t1497
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
        prediction791 = _t1485
        if prediction791 == 13:
            _t1500 = self.parse_uint32_type()
            uint32_type805 = _t1500
            _t1501 = logic_pb2.Type(uint32_type=uint32_type805)
            _t1499 = _t1501
        else:
            if prediction791 == 12:
                _t1503 = self.parse_float32_type()
                float32_type804 = _t1503
                _t1504 = logic_pb2.Type(float32_type=float32_type804)
                _t1502 = _t1504
            else:
                if prediction791 == 11:
                    _t1506 = self.parse_int32_type()
                    int32_type803 = _t1506
                    _t1507 = logic_pb2.Type(int32_type=int32_type803)
                    _t1505 = _t1507
                else:
                    if prediction791 == 10:
                        _t1509 = self.parse_boolean_type()
                        boolean_type802 = _t1509
                        _t1510 = logic_pb2.Type(boolean_type=boolean_type802)
                        _t1508 = _t1510
                    else:
                        if prediction791 == 9:
                            _t1512 = self.parse_decimal_type()
                            decimal_type801 = _t1512
                            _t1513 = logic_pb2.Type(decimal_type=decimal_type801)
                            _t1511 = _t1513
                        else:
                            if prediction791 == 8:
                                _t1515 = self.parse_missing_type()
                                missing_type800 = _t1515
                                _t1516 = logic_pb2.Type(missing_type=missing_type800)
                                _t1514 = _t1516
                            else:
                                if prediction791 == 7:
                                    _t1518 = self.parse_datetime_type()
                                    datetime_type799 = _t1518
                                    _t1519 = logic_pb2.Type(datetime_type=datetime_type799)
                                    _t1517 = _t1519
                                else:
                                    if prediction791 == 6:
                                        _t1521 = self.parse_date_type()
                                        date_type798 = _t1521
                                        _t1522 = logic_pb2.Type(date_type=date_type798)
                                        _t1520 = _t1522
                                    else:
                                        if prediction791 == 5:
                                            _t1524 = self.parse_int128_type()
                                            int128_type797 = _t1524
                                            _t1525 = logic_pb2.Type(int128_type=int128_type797)
                                            _t1523 = _t1525
                                        else:
                                            if prediction791 == 4:
                                                _t1527 = self.parse_uint128_type()
                                                uint128_type796 = _t1527
                                                _t1528 = logic_pb2.Type(uint128_type=uint128_type796)
                                                _t1526 = _t1528
                                            else:
                                                if prediction791 == 3:
                                                    _t1530 = self.parse_float_type()
                                                    float_type795 = _t1530
                                                    _t1531 = logic_pb2.Type(float_type=float_type795)
                                                    _t1529 = _t1531
                                                else:
                                                    if prediction791 == 2:
                                                        _t1533 = self.parse_int_type()
                                                        int_type794 = _t1533
                                                        _t1534 = logic_pb2.Type(int_type=int_type794)
                                                        _t1532 = _t1534
                                                    else:
                                                        if prediction791 == 1:
                                                            _t1536 = self.parse_string_type()
                                                            string_type793 = _t1536
                                                            _t1537 = logic_pb2.Type(string_type=string_type793)
                                                            _t1535 = _t1537
                                                        else:
                                                            if prediction791 == 0:
                                                                _t1539 = self.parse_unspecified_type()
                                                                unspecified_type792 = _t1539
                                                                _t1540 = logic_pb2.Type(unspecified_type=unspecified_type792)
                                                                _t1538 = _t1540
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                            _t1535 = _t1538
                                                        _t1532 = _t1535
                                                    _t1529 = _t1532
                                                _t1526 = _t1529
                                            _t1523 = _t1526
                                        _t1520 = _t1523
                                    _t1517 = _t1520
                                _t1514 = _t1517
                            _t1511 = _t1514
                        _t1508 = _t1511
                    _t1505 = _t1508
                _t1502 = _t1505
            _t1499 = _t1502
        result807 = _t1499
        self.record_span(span_start806, "Type")
        return result807

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start808 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1541 = logic_pb2.UnspecifiedType()
        result809 = _t1541
        self.record_span(span_start808, "UnspecifiedType")
        return result809

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start810 = self.span_start()
        self.consume_literal("STRING")
        _t1542 = logic_pb2.StringType()
        result811 = _t1542
        self.record_span(span_start810, "StringType")
        return result811

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start812 = self.span_start()
        self.consume_literal("INT")
        _t1543 = logic_pb2.IntType()
        result813 = _t1543
        self.record_span(span_start812, "IntType")
        return result813

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start814 = self.span_start()
        self.consume_literal("FLOAT")
        _t1544 = logic_pb2.FloatType()
        result815 = _t1544
        self.record_span(span_start814, "FloatType")
        return result815

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start816 = self.span_start()
        self.consume_literal("UINT128")
        _t1545 = logic_pb2.UInt128Type()
        result817 = _t1545
        self.record_span(span_start816, "UInt128Type")
        return result817

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start818 = self.span_start()
        self.consume_literal("INT128")
        _t1546 = logic_pb2.Int128Type()
        result819 = _t1546
        self.record_span(span_start818, "Int128Type")
        return result819

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start820 = self.span_start()
        self.consume_literal("DATE")
        _t1547 = logic_pb2.DateType()
        result821 = _t1547
        self.record_span(span_start820, "DateType")
        return result821

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start822 = self.span_start()
        self.consume_literal("DATETIME")
        _t1548 = logic_pb2.DateTimeType()
        result823 = _t1548
        self.record_span(span_start822, "DateTimeType")
        return result823

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start824 = self.span_start()
        self.consume_literal("MISSING")
        _t1549 = logic_pb2.MissingType()
        result825 = _t1549
        self.record_span(span_start824, "MissingType")
        return result825

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start828 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int826 = self.consume_terminal("INT")
        int_3827 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1550 = logic_pb2.DecimalType(precision=int(int826), scale=int(int_3827))
        result829 = _t1550
        self.record_span(span_start828, "DecimalType")
        return result829

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start830 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1551 = logic_pb2.BooleanType()
        result831 = _t1551
        self.record_span(span_start830, "BooleanType")
        return result831

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start832 = self.span_start()
        self.consume_literal("INT32")
        _t1552 = logic_pb2.Int32Type()
        result833 = _t1552
        self.record_span(span_start832, "Int32Type")
        return result833

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start834 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1553 = logic_pb2.Float32Type()
        result835 = _t1553
        self.record_span(span_start834, "Float32Type")
        return result835

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start836 = self.span_start()
        self.consume_literal("UINT32")
        _t1554 = logic_pb2.UInt32Type()
        result837 = _t1554
        self.record_span(span_start836, "UInt32Type")
        return result837

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs838 = []
        cond839 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond839:
            _t1555 = self.parse_binding()
            item840 = _t1555
            xs838.append(item840)
            cond839 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings841 = xs838
        return bindings841

    def parse_formula(self) -> logic_pb2.Formula:
        span_start856 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1557 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1558 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1559 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1560 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1561 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1562 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1563 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1564 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1565 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1566 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1567 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1568 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1569 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1570 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1571 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1572 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1573 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1574 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1575 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1576 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1577 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1578 = 10
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
                                            _t1564 = _t1565
                                        _t1563 = _t1564
                                    _t1562 = _t1563
                                _t1561 = _t1562
                            _t1560 = _t1561
                        _t1559 = _t1560
                    _t1558 = _t1559
                _t1557 = _t1558
            _t1556 = _t1557
        else:
            _t1556 = -1
        prediction842 = _t1556
        if prediction842 == 12:
            _t1580 = self.parse_cast()
            cast855 = _t1580
            _t1581 = logic_pb2.Formula(cast=cast855)
            _t1579 = _t1581
        else:
            if prediction842 == 11:
                _t1583 = self.parse_rel_atom()
                rel_atom854 = _t1583
                _t1584 = logic_pb2.Formula(rel_atom=rel_atom854)
                _t1582 = _t1584
            else:
                if prediction842 == 10:
                    _t1586 = self.parse_primitive()
                    primitive853 = _t1586
                    _t1587 = logic_pb2.Formula(primitive=primitive853)
                    _t1585 = _t1587
                else:
                    if prediction842 == 9:
                        _t1589 = self.parse_pragma()
                        pragma852 = _t1589
                        _t1590 = logic_pb2.Formula(pragma=pragma852)
                        _t1588 = _t1590
                    else:
                        if prediction842 == 8:
                            _t1592 = self.parse_atom()
                            atom851 = _t1592
                            _t1593 = logic_pb2.Formula(atom=atom851)
                            _t1591 = _t1593
                        else:
                            if prediction842 == 7:
                                _t1595 = self.parse_ffi()
                                ffi850 = _t1595
                                _t1596 = logic_pb2.Formula(ffi=ffi850)
                                _t1594 = _t1596
                            else:
                                if prediction842 == 6:
                                    _t1598 = self.parse_not()
                                    not849 = _t1598
                                    _t1599 = logic_pb2.Formula()
                                    getattr(_t1599, 'not').CopyFrom(not849)
                                    _t1597 = _t1599
                                else:
                                    if prediction842 == 5:
                                        _t1601 = self.parse_disjunction()
                                        disjunction848 = _t1601
                                        _t1602 = logic_pb2.Formula(disjunction=disjunction848)
                                        _t1600 = _t1602
                                    else:
                                        if prediction842 == 4:
                                            _t1604 = self.parse_conjunction()
                                            conjunction847 = _t1604
                                            _t1605 = logic_pb2.Formula(conjunction=conjunction847)
                                            _t1603 = _t1605
                                        else:
                                            if prediction842 == 3:
                                                _t1607 = self.parse_reduce()
                                                reduce846 = _t1607
                                                _t1608 = logic_pb2.Formula(reduce=reduce846)
                                                _t1606 = _t1608
                                            else:
                                                if prediction842 == 2:
                                                    _t1610 = self.parse_exists()
                                                    exists845 = _t1610
                                                    _t1611 = logic_pb2.Formula(exists=exists845)
                                                    _t1609 = _t1611
                                                else:
                                                    if prediction842 == 1:
                                                        _t1613 = self.parse_false()
                                                        false844 = _t1613
                                                        _t1614 = logic_pb2.Formula(disjunction=false844)
                                                        _t1612 = _t1614
                                                    else:
                                                        if prediction842 == 0:
                                                            _t1616 = self.parse_true()
                                                            true843 = _t1616
                                                            _t1617 = logic_pb2.Formula(conjunction=true843)
                                                            _t1615 = _t1617
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
        result857 = _t1579
        self.record_span(span_start856, "Formula")
        return result857

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start858 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1618 = logic_pb2.Conjunction(args=[])
        result859 = _t1618
        self.record_span(span_start858, "Conjunction")
        return result859

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start860 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1619 = logic_pb2.Disjunction(args=[])
        result861 = _t1619
        self.record_span(span_start860, "Disjunction")
        return result861

    def parse_exists(self) -> logic_pb2.Exists:
        span_start864 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1620 = self.parse_bindings()
        bindings862 = _t1620
        _t1621 = self.parse_formula()
        formula863 = _t1621
        self.consume_literal(")")
        _t1622 = logic_pb2.Abstraction(vars=(list(bindings862[0]) + list(bindings862[1] if bindings862[1] is not None else [])), value=formula863)
        _t1623 = logic_pb2.Exists(body=_t1622)
        result865 = _t1623
        self.record_span(span_start864, "Exists")
        return result865

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start869 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1624 = self.parse_abstraction()
        abstraction866 = _t1624
        _t1625 = self.parse_abstraction()
        abstraction_3867 = _t1625
        _t1626 = self.parse_terms()
        terms868 = _t1626
        self.consume_literal(")")
        _t1627 = logic_pb2.Reduce(op=abstraction866, body=abstraction_3867, terms=terms868)
        result870 = _t1627
        self.record_span(span_start869, "Reduce")
        return result870

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs871 = []
        cond872 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond872:
            _t1628 = self.parse_term()
            item873 = _t1628
            xs871.append(item873)
            cond872 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms874 = xs871
        self.consume_literal(")")
        return terms874

    def parse_term(self) -> logic_pb2.Term:
        span_start878 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1629 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1630 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1631 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1632 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1633 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1634 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1635 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1636 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1637 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1638 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1639 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1640 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1641 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1642 = 1
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
        prediction875 = _t1629
        if prediction875 == 1:
            _t1644 = self.parse_value()
            value877 = _t1644
            _t1645 = logic_pb2.Term(constant=value877)
            _t1643 = _t1645
        else:
            if prediction875 == 0:
                _t1647 = self.parse_var()
                var876 = _t1647
                _t1648 = logic_pb2.Term(var=var876)
                _t1646 = _t1648
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1643 = _t1646
        result879 = _t1643
        self.record_span(span_start878, "Term")
        return result879

    def parse_var(self) -> logic_pb2.Var:
        span_start881 = self.span_start()
        symbol880 = self.consume_terminal("SYMBOL")
        _t1649 = logic_pb2.Var(name=symbol880)
        result882 = _t1649
        self.record_span(span_start881, "Var")
        return result882

    def parse_value(self) -> logic_pb2.Value:
        span_start896 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1650 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1651 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1652 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1654 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1655 = 0
                            else:
                                _t1655 = -1
                            _t1654 = _t1655
                        _t1653 = _t1654
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1656 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1657 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1658 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1659 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1660 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1661 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1662 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1663 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
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
                        _t1653 = _t1656
                    _t1652 = _t1653
                _t1651 = _t1652
            _t1650 = _t1651
        prediction883 = _t1650
        if prediction883 == 12:
            _t1666 = self.parse_boolean_value()
            boolean_value895 = _t1666
            _t1667 = logic_pb2.Value(boolean_value=boolean_value895)
            _t1665 = _t1667
        else:
            if prediction883 == 11:
                self.consume_literal("missing")
                _t1669 = logic_pb2.MissingValue()
                _t1670 = logic_pb2.Value(missing_value=_t1669)
                _t1668 = _t1670
            else:
                if prediction883 == 10:
                    formatted_decimal894 = self.consume_terminal("DECIMAL")
                    _t1672 = logic_pb2.Value(decimal_value=formatted_decimal894)
                    _t1671 = _t1672
                else:
                    if prediction883 == 9:
                        formatted_int128893 = self.consume_terminal("INT128")
                        _t1674 = logic_pb2.Value(int128_value=formatted_int128893)
                        _t1673 = _t1674
                    else:
                        if prediction883 == 8:
                            formatted_uint128892 = self.consume_terminal("UINT128")
                            _t1676 = logic_pb2.Value(uint128_value=formatted_uint128892)
                            _t1675 = _t1676
                        else:
                            if prediction883 == 7:
                                formatted_uint32891 = self.consume_terminal("UINT32")
                                _t1678 = logic_pb2.Value(uint32_value=formatted_uint32891)
                                _t1677 = _t1678
                            else:
                                if prediction883 == 6:
                                    formatted_float890 = self.consume_terminal("FLOAT")
                                    _t1680 = logic_pb2.Value(float_value=formatted_float890)
                                    _t1679 = _t1680
                                else:
                                    if prediction883 == 5:
                                        formatted_float32889 = self.consume_terminal("FLOAT32")
                                        _t1682 = logic_pb2.Value(float32_value=formatted_float32889)
                                        _t1681 = _t1682
                                    else:
                                        if prediction883 == 4:
                                            formatted_int888 = self.consume_terminal("INT")
                                            _t1684 = logic_pb2.Value(int_value=formatted_int888)
                                            _t1683 = _t1684
                                        else:
                                            if prediction883 == 3:
                                                formatted_int32887 = self.consume_terminal("INT32")
                                                _t1686 = logic_pb2.Value(int32_value=formatted_int32887)
                                                _t1685 = _t1686
                                            else:
                                                if prediction883 == 2:
                                                    formatted_string886 = self.consume_terminal("STRING")
                                                    _t1688 = logic_pb2.Value(string_value=formatted_string886)
                                                    _t1687 = _t1688
                                                else:
                                                    if prediction883 == 1:
                                                        _t1690 = self.parse_datetime()
                                                        datetime885 = _t1690
                                                        _t1691 = logic_pb2.Value(datetime_value=datetime885)
                                                        _t1689 = _t1691
                                                    else:
                                                        if prediction883 == 0:
                                                            _t1693 = self.parse_date()
                                                            date884 = _t1693
                                                            _t1694 = logic_pb2.Value(date_value=date884)
                                                            _t1692 = _t1694
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1689 = _t1692
                                                    _t1687 = _t1689
                                                _t1685 = _t1687
                                            _t1683 = _t1685
                                        _t1681 = _t1683
                                    _t1679 = _t1681
                                _t1677 = _t1679
                            _t1675 = _t1677
                        _t1673 = _t1675
                    _t1671 = _t1673
                _t1668 = _t1671
            _t1665 = _t1668
        result897 = _t1665
        self.record_span(span_start896, "Value")
        return result897

    def parse_date(self) -> logic_pb2.DateValue:
        span_start901 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int898 = self.consume_terminal("INT")
        formatted_int_3899 = self.consume_terminal("INT")
        formatted_int_4900 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1695 = logic_pb2.DateValue(year=int(formatted_int898), month=int(formatted_int_3899), day=int(formatted_int_4900))
        result902 = _t1695
        self.record_span(span_start901, "DateValue")
        return result902

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start910 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int903 = self.consume_terminal("INT")
        formatted_int_3904 = self.consume_terminal("INT")
        formatted_int_4905 = self.consume_terminal("INT")
        formatted_int_5906 = self.consume_terminal("INT")
        formatted_int_6907 = self.consume_terminal("INT")
        formatted_int_7908 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1696 = self.consume_terminal("INT")
        else:
            _t1696 = None
        formatted_int_8909 = _t1696
        self.consume_literal(")")
        _t1697 = logic_pb2.DateTimeValue(year=int(formatted_int903), month=int(formatted_int_3904), day=int(formatted_int_4905), hour=int(formatted_int_5906), minute=int(formatted_int_6907), second=int(formatted_int_7908), microsecond=int((formatted_int_8909 if formatted_int_8909 is not None else 0)))
        result911 = _t1697
        self.record_span(span_start910, "DateTimeValue")
        return result911

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start916 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs912 = []
        cond913 = self.match_lookahead_literal("(", 0)
        while cond913:
            _t1698 = self.parse_formula()
            item914 = _t1698
            xs912.append(item914)
            cond913 = self.match_lookahead_literal("(", 0)
        formulas915 = xs912
        self.consume_literal(")")
        _t1699 = logic_pb2.Conjunction(args=formulas915)
        result917 = _t1699
        self.record_span(span_start916, "Conjunction")
        return result917

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start922 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs918 = []
        cond919 = self.match_lookahead_literal("(", 0)
        while cond919:
            _t1700 = self.parse_formula()
            item920 = _t1700
            xs918.append(item920)
            cond919 = self.match_lookahead_literal("(", 0)
        formulas921 = xs918
        self.consume_literal(")")
        _t1701 = logic_pb2.Disjunction(args=formulas921)
        result923 = _t1701
        self.record_span(span_start922, "Disjunction")
        return result923

    def parse_not(self) -> logic_pb2.Not:
        span_start925 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1702 = self.parse_formula()
        formula924 = _t1702
        self.consume_literal(")")
        _t1703 = logic_pb2.Not(arg=formula924)
        result926 = _t1703
        self.record_span(span_start925, "Not")
        return result926

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start930 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1704 = self.parse_name()
        name927 = _t1704
        _t1705 = self.parse_ffi_args()
        ffi_args928 = _t1705
        _t1706 = self.parse_terms()
        terms929 = _t1706
        self.consume_literal(")")
        _t1707 = logic_pb2.FFI(name=name927, args=ffi_args928, terms=terms929)
        result931 = _t1707
        self.record_span(span_start930, "FFI")
        return result931

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol932 = self.consume_terminal("SYMBOL")
        return symbol932

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs933 = []
        cond934 = self.match_lookahead_literal("(", 0)
        while cond934:
            _t1708 = self.parse_abstraction()
            item935 = _t1708
            xs933.append(item935)
            cond934 = self.match_lookahead_literal("(", 0)
        abstractions936 = xs933
        self.consume_literal(")")
        return abstractions936

    def parse_atom(self) -> logic_pb2.Atom:
        span_start942 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1709 = self.parse_relation_id()
        relation_id937 = _t1709
        xs938 = []
        cond939 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond939:
            _t1710 = self.parse_term()
            item940 = _t1710
            xs938.append(item940)
            cond939 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms941 = xs938
        self.consume_literal(")")
        _t1711 = logic_pb2.Atom(name=relation_id937, terms=terms941)
        result943 = _t1711
        self.record_span(span_start942, "Atom")
        return result943

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start949 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1712 = self.parse_name()
        name944 = _t1712
        xs945 = []
        cond946 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond946:
            _t1713 = self.parse_term()
            item947 = _t1713
            xs945.append(item947)
            cond946 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms948 = xs945
        self.consume_literal(")")
        _t1714 = logic_pb2.Pragma(name=name944, terms=terms948)
        result950 = _t1714
        self.record_span(span_start949, "Pragma")
        return result950

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start966 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1716 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1717 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1718 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1719 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1720 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1721 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1722 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1723 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1724 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1725 = 7
                                                else:
                                                    _t1725 = -1
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
        else:
            _t1715 = -1
        prediction951 = _t1715
        if prediction951 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1727 = self.parse_name()
            name961 = _t1727
            xs962 = []
            cond963 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond963:
                _t1728 = self.parse_rel_term()
                item964 = _t1728
                xs962.append(item964)
                cond963 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms965 = xs962
            self.consume_literal(")")
            _t1729 = logic_pb2.Primitive(name=name961, terms=rel_terms965)
            _t1726 = _t1729
        else:
            if prediction951 == 8:
                _t1731 = self.parse_divide()
                divide960 = _t1731
                _t1730 = divide960
            else:
                if prediction951 == 7:
                    _t1733 = self.parse_multiply()
                    multiply959 = _t1733
                    _t1732 = multiply959
                else:
                    if prediction951 == 6:
                        _t1735 = self.parse_minus()
                        minus958 = _t1735
                        _t1734 = minus958
                    else:
                        if prediction951 == 5:
                            _t1737 = self.parse_add()
                            add957 = _t1737
                            _t1736 = add957
                        else:
                            if prediction951 == 4:
                                _t1739 = self.parse_gt_eq()
                                gt_eq956 = _t1739
                                _t1738 = gt_eq956
                            else:
                                if prediction951 == 3:
                                    _t1741 = self.parse_gt()
                                    gt955 = _t1741
                                    _t1740 = gt955
                                else:
                                    if prediction951 == 2:
                                        _t1743 = self.parse_lt_eq()
                                        lt_eq954 = _t1743
                                        _t1742 = lt_eq954
                                    else:
                                        if prediction951 == 1:
                                            _t1745 = self.parse_lt()
                                            lt953 = _t1745
                                            _t1744 = lt953
                                        else:
                                            if prediction951 == 0:
                                                _t1747 = self.parse_eq()
                                                eq952 = _t1747
                                                _t1746 = eq952
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1744 = _t1746
                                        _t1742 = _t1744
                                    _t1740 = _t1742
                                _t1738 = _t1740
                            _t1736 = _t1738
                        _t1734 = _t1736
                    _t1732 = _t1734
                _t1730 = _t1732
            _t1726 = _t1730
        result967 = _t1726
        self.record_span(span_start966, "Primitive")
        return result967

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start970 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1748 = self.parse_term()
        term968 = _t1748
        _t1749 = self.parse_term()
        term_3969 = _t1749
        self.consume_literal(")")
        _t1750 = logic_pb2.RelTerm(term=term968)
        _t1751 = logic_pb2.RelTerm(term=term_3969)
        _t1752 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1750, _t1751])
        result971 = _t1752
        self.record_span(span_start970, "Primitive")
        return result971

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start974 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1753 = self.parse_term()
        term972 = _t1753
        _t1754 = self.parse_term()
        term_3973 = _t1754
        self.consume_literal(")")
        _t1755 = logic_pb2.RelTerm(term=term972)
        _t1756 = logic_pb2.RelTerm(term=term_3973)
        _t1757 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1755, _t1756])
        result975 = _t1757
        self.record_span(span_start974, "Primitive")
        return result975

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start978 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1758 = self.parse_term()
        term976 = _t1758
        _t1759 = self.parse_term()
        term_3977 = _t1759
        self.consume_literal(")")
        _t1760 = logic_pb2.RelTerm(term=term976)
        _t1761 = logic_pb2.RelTerm(term=term_3977)
        _t1762 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1760, _t1761])
        result979 = _t1762
        self.record_span(span_start978, "Primitive")
        return result979

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start982 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1763 = self.parse_term()
        term980 = _t1763
        _t1764 = self.parse_term()
        term_3981 = _t1764
        self.consume_literal(")")
        _t1765 = logic_pb2.RelTerm(term=term980)
        _t1766 = logic_pb2.RelTerm(term=term_3981)
        _t1767 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1765, _t1766])
        result983 = _t1767
        self.record_span(span_start982, "Primitive")
        return result983

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start986 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1768 = self.parse_term()
        term984 = _t1768
        _t1769 = self.parse_term()
        term_3985 = _t1769
        self.consume_literal(")")
        _t1770 = logic_pb2.RelTerm(term=term984)
        _t1771 = logic_pb2.RelTerm(term=term_3985)
        _t1772 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1770, _t1771])
        result987 = _t1772
        self.record_span(span_start986, "Primitive")
        return result987

    def parse_add(self) -> logic_pb2.Primitive:
        span_start991 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1773 = self.parse_term()
        term988 = _t1773
        _t1774 = self.parse_term()
        term_3989 = _t1774
        _t1775 = self.parse_term()
        term_4990 = _t1775
        self.consume_literal(")")
        _t1776 = logic_pb2.RelTerm(term=term988)
        _t1777 = logic_pb2.RelTerm(term=term_3989)
        _t1778 = logic_pb2.RelTerm(term=term_4990)
        _t1779 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1776, _t1777, _t1778])
        result992 = _t1779
        self.record_span(span_start991, "Primitive")
        return result992

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start996 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1780 = self.parse_term()
        term993 = _t1780
        _t1781 = self.parse_term()
        term_3994 = _t1781
        _t1782 = self.parse_term()
        term_4995 = _t1782
        self.consume_literal(")")
        _t1783 = logic_pb2.RelTerm(term=term993)
        _t1784 = logic_pb2.RelTerm(term=term_3994)
        _t1785 = logic_pb2.RelTerm(term=term_4995)
        _t1786 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1783, _t1784, _t1785])
        result997 = _t1786
        self.record_span(span_start996, "Primitive")
        return result997

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start1001 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1787 = self.parse_term()
        term998 = _t1787
        _t1788 = self.parse_term()
        term_3999 = _t1788
        _t1789 = self.parse_term()
        term_41000 = _t1789
        self.consume_literal(")")
        _t1790 = logic_pb2.RelTerm(term=term998)
        _t1791 = logic_pb2.RelTerm(term=term_3999)
        _t1792 = logic_pb2.RelTerm(term=term_41000)
        _t1793 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1790, _t1791, _t1792])
        result1002 = _t1793
        self.record_span(span_start1001, "Primitive")
        return result1002

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start1006 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1794 = self.parse_term()
        term1003 = _t1794
        _t1795 = self.parse_term()
        term_31004 = _t1795
        _t1796 = self.parse_term()
        term_41005 = _t1796
        self.consume_literal(")")
        _t1797 = logic_pb2.RelTerm(term=term1003)
        _t1798 = logic_pb2.RelTerm(term=term_31004)
        _t1799 = logic_pb2.RelTerm(term=term_41005)
        _t1800 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1797, _t1798, _t1799])
        result1007 = _t1800
        self.record_span(span_start1006, "Primitive")
        return result1007

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1011 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1801 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1802 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1803 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1804 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1805 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1806 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1807 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1808 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1809 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1810 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1811 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1812 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1813 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1814 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1815 = 1
                                                                else:
                                                                    _t1815 = -1
                                                                _t1814 = _t1815
                                                            _t1813 = _t1814
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
        prediction1008 = _t1801
        if prediction1008 == 1:
            _t1817 = self.parse_term()
            term1010 = _t1817
            _t1818 = logic_pb2.RelTerm(term=term1010)
            _t1816 = _t1818
        else:
            if prediction1008 == 0:
                _t1820 = self.parse_specialized_value()
                specialized_value1009 = _t1820
                _t1821 = logic_pb2.RelTerm(specialized_value=specialized_value1009)
                _t1819 = _t1821
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1816 = _t1819
        result1012 = _t1816
        self.record_span(span_start1011, "RelTerm")
        return result1012

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1014 = self.span_start()
        self.consume_literal("#")
        _t1822 = self.parse_raw_value()
        raw_value1013 = _t1822
        result1015 = raw_value1013
        self.record_span(span_start1014, "Value")
        return result1015

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1021 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1823 = self.parse_name()
        name1016 = _t1823
        xs1017 = []
        cond1018 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1018:
            _t1824 = self.parse_rel_term()
            item1019 = _t1824
            xs1017.append(item1019)
            cond1018 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1020 = xs1017
        self.consume_literal(")")
        _t1825 = logic_pb2.RelAtom(name=name1016, terms=rel_terms1020)
        result1022 = _t1825
        self.record_span(span_start1021, "RelAtom")
        return result1022

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1025 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1826 = self.parse_term()
        term1023 = _t1826
        _t1827 = self.parse_term()
        term_31024 = _t1827
        self.consume_literal(")")
        _t1828 = logic_pb2.Cast(input=term1023, result=term_31024)
        result1026 = _t1828
        self.record_span(span_start1025, "Cast")
        return result1026

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1027 = []
        cond1028 = self.match_lookahead_literal("(", 0)
        while cond1028:
            _t1829 = self.parse_attribute()
            item1029 = _t1829
            xs1027.append(item1029)
            cond1028 = self.match_lookahead_literal("(", 0)
        attributes1030 = xs1027
        self.consume_literal(")")
        return attributes1030

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1036 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1830 = self.parse_name()
        name1031 = _t1830
        xs1032 = []
        cond1033 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1033:
            _t1831 = self.parse_raw_value()
            item1034 = _t1831
            xs1032.append(item1034)
            cond1033 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1035 = xs1032
        self.consume_literal(")")
        _t1832 = logic_pb2.Attribute(name=name1031, args=raw_values1035)
        result1037 = _t1832
        self.record_span(span_start1036, "Attribute")
        return result1037

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1044 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1038 = []
        cond1039 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1039:
            _t1833 = self.parse_relation_id()
            item1040 = _t1833
            xs1038.append(item1040)
            cond1039 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1041 = xs1038
        _t1834 = self.parse_script()
        script1042 = _t1834
        if self.match_lookahead_literal("(", 0):
            _t1836 = self.parse_attrs()
            _t1835 = _t1836
        else:
            _t1835 = None
        attrs1043 = _t1835
        self.consume_literal(")")
        _t1837 = logic_pb2.Algorithm(body=script1042, attrs=(attrs1043 if attrs1043 is not None else []))
        getattr(_t1837, 'global').extend(relation_ids1041)
        result1045 = _t1837
        self.record_span(span_start1044, "Algorithm")
        return result1045

    def parse_script(self) -> logic_pb2.Script:
        span_start1050 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1046 = []
        cond1047 = self.match_lookahead_literal("(", 0)
        while cond1047:
            _t1838 = self.parse_construct()
            item1048 = _t1838
            xs1046.append(item1048)
            cond1047 = self.match_lookahead_literal("(", 0)
        constructs1049 = xs1046
        self.consume_literal(")")
        _t1839 = logic_pb2.Script(constructs=constructs1049)
        result1051 = _t1839
        self.record_span(span_start1050, "Script")
        return result1051

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1055 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1841 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1842 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1843 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1844 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1845 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1846 = 1
                                else:
                                    _t1846 = -1
                                _t1845 = _t1846
                            _t1844 = _t1845
                        _t1843 = _t1844
                    _t1842 = _t1843
                _t1841 = _t1842
            _t1840 = _t1841
        else:
            _t1840 = -1
        prediction1052 = _t1840
        if prediction1052 == 1:
            _t1848 = self.parse_instruction()
            instruction1054 = _t1848
            _t1849 = logic_pb2.Construct(instruction=instruction1054)
            _t1847 = _t1849
        else:
            if prediction1052 == 0:
                _t1851 = self.parse_loop()
                loop1053 = _t1851
                _t1852 = logic_pb2.Construct(loop=loop1053)
                _t1850 = _t1852
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1847 = _t1850
        result1056 = _t1847
        self.record_span(span_start1055, "Construct")
        return result1056

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1060 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1853 = self.parse_init()
        init1057 = _t1853
        _t1854 = self.parse_script()
        script1058 = _t1854
        if self.match_lookahead_literal("(", 0):
            _t1856 = self.parse_attrs()
            _t1855 = _t1856
        else:
            _t1855 = None
        attrs1059 = _t1855
        self.consume_literal(")")
        _t1857 = logic_pb2.Loop(init=init1057, body=script1058, attrs=(attrs1059 if attrs1059 is not None else []))
        result1061 = _t1857
        self.record_span(span_start1060, "Loop")
        return result1061

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1062 = []
        cond1063 = self.match_lookahead_literal("(", 0)
        while cond1063:
            _t1858 = self.parse_instruction()
            item1064 = _t1858
            xs1062.append(item1064)
            cond1063 = self.match_lookahead_literal("(", 0)
        instructions1065 = xs1062
        self.consume_literal(")")
        return instructions1065

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1072 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1860 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1861 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1862 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1863 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1864 = 0
                            else:
                                _t1864 = -1
                            _t1863 = _t1864
                        _t1862 = _t1863
                    _t1861 = _t1862
                _t1860 = _t1861
            _t1859 = _t1860
        else:
            _t1859 = -1
        prediction1066 = _t1859
        if prediction1066 == 4:
            _t1866 = self.parse_monus_def()
            monus_def1071 = _t1866
            _t1867 = logic_pb2.Instruction(monus_def=monus_def1071)
            _t1865 = _t1867
        else:
            if prediction1066 == 3:
                _t1869 = self.parse_monoid_def()
                monoid_def1070 = _t1869
                _t1870 = logic_pb2.Instruction(monoid_def=monoid_def1070)
                _t1868 = _t1870
            else:
                if prediction1066 == 2:
                    _t1872 = self.parse_break()
                    break1069 = _t1872
                    _t1873 = logic_pb2.Instruction()
                    getattr(_t1873, 'break').CopyFrom(break1069)
                    _t1871 = _t1873
                else:
                    if prediction1066 == 1:
                        _t1875 = self.parse_upsert()
                        upsert1068 = _t1875
                        _t1876 = logic_pb2.Instruction(upsert=upsert1068)
                        _t1874 = _t1876
                    else:
                        if prediction1066 == 0:
                            _t1878 = self.parse_assign()
                            assign1067 = _t1878
                            _t1879 = logic_pb2.Instruction(assign=assign1067)
                            _t1877 = _t1879
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1874 = _t1877
                    _t1871 = _t1874
                _t1868 = _t1871
            _t1865 = _t1868
        result1073 = _t1865
        self.record_span(span_start1072, "Instruction")
        return result1073

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1077 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1880 = self.parse_relation_id()
        relation_id1074 = _t1880
        _t1881 = self.parse_abstraction()
        abstraction1075 = _t1881
        if self.match_lookahead_literal("(", 0):
            _t1883 = self.parse_attrs()
            _t1882 = _t1883
        else:
            _t1882 = None
        attrs1076 = _t1882
        self.consume_literal(")")
        _t1884 = logic_pb2.Assign(name=relation_id1074, body=abstraction1075, attrs=(attrs1076 if attrs1076 is not None else []))
        result1078 = _t1884
        self.record_span(span_start1077, "Assign")
        return result1078

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1082 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1885 = self.parse_relation_id()
        relation_id1079 = _t1885
        _t1886 = self.parse_abstraction_with_arity()
        abstraction_with_arity1080 = _t1886
        if self.match_lookahead_literal("(", 0):
            _t1888 = self.parse_attrs()
            _t1887 = _t1888
        else:
            _t1887 = None
        attrs1081 = _t1887
        self.consume_literal(")")
        _t1889 = logic_pb2.Upsert(name=relation_id1079, body=abstraction_with_arity1080[0], attrs=(attrs1081 if attrs1081 is not None else []), value_arity=abstraction_with_arity1080[1])
        result1083 = _t1889
        self.record_span(span_start1082, "Upsert")
        return result1083

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1890 = self.parse_bindings()
        bindings1084 = _t1890
        _t1891 = self.parse_formula()
        formula1085 = _t1891
        self.consume_literal(")")
        _t1892 = logic_pb2.Abstraction(vars=(list(bindings1084[0]) + list(bindings1084[1] if bindings1084[1] is not None else [])), value=formula1085)
        return (_t1892, len(bindings1084[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1089 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1893 = self.parse_relation_id()
        relation_id1086 = _t1893
        _t1894 = self.parse_abstraction()
        abstraction1087 = _t1894
        if self.match_lookahead_literal("(", 0):
            _t1896 = self.parse_attrs()
            _t1895 = _t1896
        else:
            _t1895 = None
        attrs1088 = _t1895
        self.consume_literal(")")
        _t1897 = logic_pb2.Break(name=relation_id1086, body=abstraction1087, attrs=(attrs1088 if attrs1088 is not None else []))
        result1090 = _t1897
        self.record_span(span_start1089, "Break")
        return result1090

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1095 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1898 = self.parse_monoid()
        monoid1091 = _t1898
        _t1899 = self.parse_relation_id()
        relation_id1092 = _t1899
        _t1900 = self.parse_abstraction_with_arity()
        abstraction_with_arity1093 = _t1900
        if self.match_lookahead_literal("(", 0):
            _t1902 = self.parse_attrs()
            _t1901 = _t1902
        else:
            _t1901 = None
        attrs1094 = _t1901
        self.consume_literal(")")
        _t1903 = logic_pb2.MonoidDef(monoid=monoid1091, name=relation_id1092, body=abstraction_with_arity1093[0], attrs=(attrs1094 if attrs1094 is not None else []), value_arity=abstraction_with_arity1093[1])
        result1096 = _t1903
        self.record_span(span_start1095, "MonoidDef")
        return result1096

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1102 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1905 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1906 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1907 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1908 = 2
                        else:
                            _t1908 = -1
                        _t1907 = _t1908
                    _t1906 = _t1907
                _t1905 = _t1906
            _t1904 = _t1905
        else:
            _t1904 = -1
        prediction1097 = _t1904
        if prediction1097 == 3:
            _t1910 = self.parse_sum_monoid()
            sum_monoid1101 = _t1910
            _t1911 = logic_pb2.Monoid(sum_monoid=sum_monoid1101)
            _t1909 = _t1911
        else:
            if prediction1097 == 2:
                _t1913 = self.parse_max_monoid()
                max_monoid1100 = _t1913
                _t1914 = logic_pb2.Monoid(max_monoid=max_monoid1100)
                _t1912 = _t1914
            else:
                if prediction1097 == 1:
                    _t1916 = self.parse_min_monoid()
                    min_monoid1099 = _t1916
                    _t1917 = logic_pb2.Monoid(min_monoid=min_monoid1099)
                    _t1915 = _t1917
                else:
                    if prediction1097 == 0:
                        _t1919 = self.parse_or_monoid()
                        or_monoid1098 = _t1919
                        _t1920 = logic_pb2.Monoid(or_monoid=or_monoid1098)
                        _t1918 = _t1920
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1915 = _t1918
                _t1912 = _t1915
            _t1909 = _t1912
        result1103 = _t1909
        self.record_span(span_start1102, "Monoid")
        return result1103

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1104 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1921 = logic_pb2.OrMonoid()
        result1105 = _t1921
        self.record_span(span_start1104, "OrMonoid")
        return result1105

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1107 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1922 = self.parse_type()
        type1106 = _t1922
        self.consume_literal(")")
        _t1923 = logic_pb2.MinMonoid(type=type1106)
        result1108 = _t1923
        self.record_span(span_start1107, "MinMonoid")
        return result1108

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1110 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1924 = self.parse_type()
        type1109 = _t1924
        self.consume_literal(")")
        _t1925 = logic_pb2.MaxMonoid(type=type1109)
        result1111 = _t1925
        self.record_span(span_start1110, "MaxMonoid")
        return result1111

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1113 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1926 = self.parse_type()
        type1112 = _t1926
        self.consume_literal(")")
        _t1927 = logic_pb2.SumMonoid(type=type1112)
        result1114 = _t1927
        self.record_span(span_start1113, "SumMonoid")
        return result1114

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1119 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1928 = self.parse_monoid()
        monoid1115 = _t1928
        _t1929 = self.parse_relation_id()
        relation_id1116 = _t1929
        _t1930 = self.parse_abstraction_with_arity()
        abstraction_with_arity1117 = _t1930
        if self.match_lookahead_literal("(", 0):
            _t1932 = self.parse_attrs()
            _t1931 = _t1932
        else:
            _t1931 = None
        attrs1118 = _t1931
        self.consume_literal(")")
        _t1933 = logic_pb2.MonusDef(monoid=monoid1115, name=relation_id1116, body=abstraction_with_arity1117[0], attrs=(attrs1118 if attrs1118 is not None else []), value_arity=abstraction_with_arity1117[1])
        result1120 = _t1933
        self.record_span(span_start1119, "MonusDef")
        return result1120

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1125 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1934 = self.parse_relation_id()
        relation_id1121 = _t1934
        _t1935 = self.parse_abstraction()
        abstraction1122 = _t1935
        _t1936 = self.parse_functional_dependency_keys()
        functional_dependency_keys1123 = _t1936
        _t1937 = self.parse_functional_dependency_values()
        functional_dependency_values1124 = _t1937
        self.consume_literal(")")
        _t1938 = logic_pb2.FunctionalDependency(guard=abstraction1122, keys=functional_dependency_keys1123, values=functional_dependency_values1124)
        _t1939 = logic_pb2.Constraint(name=relation_id1121, functional_dependency=_t1938)
        result1126 = _t1939
        self.record_span(span_start1125, "Constraint")
        return result1126

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1127 = []
        cond1128 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1128:
            _t1940 = self.parse_var()
            item1129 = _t1940
            xs1127.append(item1129)
            cond1128 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1130 = xs1127
        self.consume_literal(")")
        return vars1130

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1131 = []
        cond1132 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1132:
            _t1941 = self.parse_var()
            item1133 = _t1941
            xs1131.append(item1133)
            cond1132 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1134 = xs1131
        self.consume_literal(")")
        return vars1134

    def parse_data(self) -> logic_pb2.Data:
        span_start1140 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1943 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1944 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1945 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1946 = 1
                        else:
                            _t1946 = -1
                        _t1945 = _t1946
                    _t1944 = _t1945
                _t1943 = _t1944
            _t1942 = _t1943
        else:
            _t1942 = -1
        prediction1135 = _t1942
        if prediction1135 == 3:
            _t1948 = self.parse_iceberg_data()
            iceberg_data1139 = _t1948
            _t1949 = logic_pb2.Data(iceberg_data=iceberg_data1139)
            _t1947 = _t1949
        else:
            if prediction1135 == 2:
                _t1951 = self.parse_csv_data()
                csv_data1138 = _t1951
                _t1952 = logic_pb2.Data(csv_data=csv_data1138)
                _t1950 = _t1952
            else:
                if prediction1135 == 1:
                    _t1954 = self.parse_betree_relation()
                    betree_relation1137 = _t1954
                    _t1955 = logic_pb2.Data(betree_relation=betree_relation1137)
                    _t1953 = _t1955
                else:
                    if prediction1135 == 0:
                        _t1957 = self.parse_edb()
                        edb1136 = _t1957
                        _t1958 = logic_pb2.Data(edb=edb1136)
                        _t1956 = _t1958
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1953 = _t1956
                _t1950 = _t1953
            _t1947 = _t1950
        result1141 = _t1947
        self.record_span(span_start1140, "Data")
        return result1141

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1145 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1959 = self.parse_relation_id()
        relation_id1142 = _t1959
        _t1960 = self.parse_edb_path()
        edb_path1143 = _t1960
        _t1961 = self.parse_edb_types()
        edb_types1144 = _t1961
        self.consume_literal(")")
        _t1962 = logic_pb2.EDB(target_id=relation_id1142, path=edb_path1143, types=edb_types1144)
        result1146 = _t1962
        self.record_span(span_start1145, "EDB")
        return result1146

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1147 = []
        cond1148 = self.match_lookahead_terminal("STRING", 0)
        while cond1148:
            item1149 = self.consume_terminal("STRING")
            xs1147.append(item1149)
            cond1148 = self.match_lookahead_terminal("STRING", 0)
        strings1150 = xs1147
        self.consume_literal("]")
        return strings1150

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1151 = []
        cond1152 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1152:
            _t1963 = self.parse_type()
            item1153 = _t1963
            xs1151.append(item1153)
            cond1152 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1154 = xs1151
        self.consume_literal("]")
        return types1154

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1157 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1964 = self.parse_relation_id()
        relation_id1155 = _t1964
        _t1965 = self.parse_betree_info()
        betree_info1156 = _t1965
        self.consume_literal(")")
        _t1966 = logic_pb2.BeTreeRelation(name=relation_id1155, relation_info=betree_info1156)
        result1158 = _t1966
        self.record_span(span_start1157, "BeTreeRelation")
        return result1158

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1162 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1967 = self.parse_betree_info_key_types()
        betree_info_key_types1159 = _t1967
        _t1968 = self.parse_betree_info_value_types()
        betree_info_value_types1160 = _t1968
        _t1969 = self.parse_config_dict()
        config_dict1161 = _t1969
        self.consume_literal(")")
        _t1970 = self.construct_betree_info(betree_info_key_types1159, betree_info_value_types1160, config_dict1161)
        result1163 = _t1970
        self.record_span(span_start1162, "BeTreeInfo")
        return result1163

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1164 = []
        cond1165 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1165:
            _t1971 = self.parse_type()
            item1166 = _t1971
            xs1164.append(item1166)
            cond1165 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1167 = xs1164
        self.consume_literal(")")
        return types1167

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1168 = []
        cond1169 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1169:
            _t1972 = self.parse_type()
            item1170 = _t1972
            xs1168.append(item1170)
            cond1169 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1171 = xs1168
        self.consume_literal(")")
        return types1171

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1177 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1973 = self.parse_csvlocator()
        csvlocator1172 = _t1973
        _t1974 = self.parse_csv_config()
        csv_config1173 = _t1974
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("columns", 1)):
            _t1976 = self.parse_gnf_columns()
            _t1975 = _t1976
        else:
            _t1975 = None
        gnf_columns1174 = _t1975
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("table", 1)):
            _t1978 = self.parse_csv_table()
            _t1977 = _t1978
        else:
            _t1977 = None
        csv_table1175 = _t1977
        _t1979 = self.parse_csv_asof()
        csv_asof1176 = _t1979
        self.consume_literal(")")
        _t1980 = self.construct_csv_data(csvlocator1172, csv_config1173, gnf_columns1174, csv_table1175, csv_asof1176)
        result1178 = _t1980
        self.record_span(span_start1177, "CSVData")
        return result1178

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1181 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1982 = self.parse_csv_locator_paths()
            _t1981 = _t1982
        else:
            _t1981 = None
        csv_locator_paths1179 = _t1981
        if self.match_lookahead_literal("(", 0):
            _t1984 = self.parse_csv_locator_inline_data()
            _t1983 = _t1984
        else:
            _t1983 = None
        csv_locator_inline_data1180 = _t1983
        self.consume_literal(")")
        _t1985 = logic_pb2.CSVLocator(paths=(csv_locator_paths1179 if csv_locator_paths1179 is not None else []), inline_data=(csv_locator_inline_data1180 if csv_locator_inline_data1180 is not None else "").encode())
        result1182 = _t1985
        self.record_span(span_start1181, "CSVLocator")
        return result1182

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1183 = []
        cond1184 = self.match_lookahead_terminal("STRING", 0)
        while cond1184:
            item1185 = self.consume_terminal("STRING")
            xs1183.append(item1185)
            cond1184 = self.match_lookahead_terminal("STRING", 0)
        strings1186 = xs1183
        self.consume_literal(")")
        return strings1186

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        formatted_string1187 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return formatted_string1187

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1189 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1986 = self.parse_config_dict()
        config_dict1188 = _t1986
        self.consume_literal(")")
        _t1987 = self.construct_csv_config(config_dict1188)
        result1190 = _t1987
        self.record_span(span_start1189, "CSVConfig")
        return result1190

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1191 = []
        cond1192 = self.match_lookahead_literal("(", 0)
        while cond1192:
            _t1988 = self.parse_gnf_column()
            item1193 = _t1988
            xs1191.append(item1193)
            cond1192 = self.match_lookahead_literal("(", 0)
        gnf_columns1194 = xs1191
        self.consume_literal(")")
        return gnf_columns1194

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1201 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1989 = self.parse_gnf_column_path()
        gnf_column_path1195 = _t1989
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1991 = self.parse_relation_id()
            _t1990 = _t1991
        else:
            _t1990 = None
        relation_id1196 = _t1990
        self.consume_literal("[")
        xs1197 = []
        cond1198 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1198:
            _t1992 = self.parse_type()
            item1199 = _t1992
            xs1197.append(item1199)
            cond1198 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1200 = xs1197
        self.consume_literal("]")
        self.consume_literal(")")
        _t1993 = logic_pb2.GNFColumn(column_path=gnf_column_path1195, target_id=relation_id1196, types=types1200)
        result1202 = _t1993
        self.record_span(span_start1201, "GNFColumn")
        return result1202

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1994 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1995 = 0
            else:
                _t1995 = -1
            _t1994 = _t1995
        prediction1203 = _t1994
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
            _t1996 = strings1208
        else:
            if prediction1203 == 0:
                string1204 = self.consume_terminal("STRING")
                _t1997 = [string1204]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1996 = _t1997
        return _t1996

    def parse_csv_table(self) -> logic_pb2.CSVTarget:
        span_start1218 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table")
        _t1998 = self.parse_relation_id()
        relation_id1209 = _t1998
        self.consume_literal("[")
        xs1210 = []
        cond1211 = self.match_lookahead_terminal("STRING", 0)
        while cond1211:
            item1212 = self.consume_terminal("STRING")
            xs1210.append(item1212)
            cond1211 = self.match_lookahead_terminal("STRING", 0)
        strings1213 = xs1210
        self.consume_literal("]")
        self.consume_literal("[")
        xs1214 = []
        cond1215 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1215:
            _t1999 = self.parse_type()
            item1216 = _t1999
            xs1214.append(item1216)
            cond1215 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1217 = xs1214
        self.consume_literal("]")
        self.consume_literal(")")
        _t2000 = logic_pb2.CSVTarget(target_id=relation_id1209, column_names=strings1213, types=types1217)
        result1219 = _t2000
        self.record_span(span_start1218, "CSVTarget")
        return result1219

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1220 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1220

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1227 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t2001 = self.parse_iceberg_locator()
        iceberg_locator1221 = _t2001
        _t2002 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1222 = _t2002
        _t2003 = self.parse_gnf_columns()
        gnf_columns1223 = _t2003
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t2005 = self.parse_iceberg_from_snapshot()
            _t2004 = _t2005
        else:
            _t2004 = None
        iceberg_from_snapshot1224 = _t2004
        if self.match_lookahead_literal("(", 0):
            _t2007 = self.parse_iceberg_to_snapshot()
            _t2006 = _t2007
        else:
            _t2006 = None
        iceberg_to_snapshot1225 = _t2006
        _t2008 = self.parse_boolean_value()
        boolean_value1226 = _t2008
        self.consume_literal(")")
        _t2009 = self.construct_iceberg_data(iceberg_locator1221, iceberg_catalog_config1222, gnf_columns1223, iceberg_from_snapshot1224, iceberg_to_snapshot1225, boolean_value1226)
        result1228 = _t2009
        self.record_span(span_start1227, "IcebergData")
        return result1228

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1232 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t2010 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1229 = _t2010
        _t2011 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1230 = _t2011
        _t2012 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1231 = _t2012
        self.consume_literal(")")
        _t2013 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1229, namespace=iceberg_locator_namespace1230, warehouse=iceberg_locator_warehouse1231)
        result1233 = _t2013
        self.record_span(span_start1232, "IcebergLocator")
        return result1233

    def parse_iceberg_locator_table_name(self) -> str:
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1234 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1234

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1235 = []
        cond1236 = self.match_lookahead_terminal("STRING", 0)
        while cond1236:
            item1237 = self.consume_terminal("STRING")
            xs1235.append(item1237)
            cond1236 = self.match_lookahead_terminal("STRING", 0)
        strings1238 = xs1235
        self.consume_literal(")")
        return strings1238

    def parse_iceberg_locator_warehouse(self) -> str:
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string1239 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1239

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1244 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t2014 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1240 = _t2014
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t2016 = self.parse_iceberg_catalog_config_scope()
            _t2015 = _t2016
        else:
            _t2015 = None
        iceberg_catalog_config_scope1241 = _t2015
        _t2017 = self.parse_iceberg_properties()
        iceberg_properties1242 = _t2017
        _t2018 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1243 = _t2018
        self.consume_literal(")")
        _t2019 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1240, iceberg_catalog_config_scope1241, iceberg_properties1242, iceberg_auth_properties1243)
        result1245 = _t2019
        self.record_span(span_start1244, "IcebergCatalogConfig")
        return result1245

    def parse_iceberg_catalog_uri(self) -> str:
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1246 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1246

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1247 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1247

    def parse_iceberg_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1248 = []
        cond1249 = self.match_lookahead_literal("(", 0)
        while cond1249:
            _t2020 = self.parse_iceberg_property_entry()
            item1250 = _t2020
            xs1248.append(item1250)
            cond1249 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1251 = xs1248
        self.consume_literal(")")
        return iceberg_property_entrys1251

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1252 = self.consume_terminal("STRING")
        string_31253 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1252, string_31253,)

    def parse_iceberg_auth_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1254 = []
        cond1255 = self.match_lookahead_literal("(", 0)
        while cond1255:
            _t2021 = self.parse_iceberg_masked_property_entry()
            item1256 = _t2021
            xs1254.append(item1256)
            cond1255 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1257 = xs1254
        self.consume_literal(")")
        return iceberg_masked_property_entrys1257

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1258 = self.consume_terminal("STRING")
        string_31259 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1258, string_31259,)

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1260 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1260

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1261 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1261

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1263 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2022 = self.parse_fragment_id()
        fragment_id1262 = _t2022
        self.consume_literal(")")
        _t2023 = transactions_pb2.Undefine(fragment_id=fragment_id1262)
        result1264 = _t2023
        self.record_span(span_start1263, "Undefine")
        return result1264

    def parse_context(self) -> transactions_pb2.Context:
        span_start1269 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1265 = []
        cond1266 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1266:
            _t2024 = self.parse_relation_id()
            item1267 = _t2024
            xs1265.append(item1267)
            cond1266 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1268 = xs1265
        self.consume_literal(")")
        _t2025 = transactions_pb2.Context(relations=relation_ids1268)
        result1270 = _t2025
        self.record_span(span_start1269, "Context")
        return result1270

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1276 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t2026 = self.parse_edb_path()
        edb_path1271 = _t2026
        xs1272 = []
        cond1273 = self.match_lookahead_literal("[", 0)
        while cond1273:
            _t2027 = self.parse_snapshot_mapping()
            item1274 = _t2027
            xs1272.append(item1274)
            cond1273 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1275 = xs1272
        self.consume_literal(")")
        _t2028 = transactions_pb2.Snapshot(prefix=edb_path1271, mappings=snapshot_mappings1275)
        result1277 = _t2028
        self.record_span(span_start1276, "Snapshot")
        return result1277

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1280 = self.span_start()
        _t2029 = self.parse_edb_path()
        edb_path1278 = _t2029
        _t2030 = self.parse_relation_id()
        relation_id1279 = _t2030
        _t2031 = transactions_pb2.SnapshotMapping(destination_path=edb_path1278, source_relation=relation_id1279)
        result1281 = _t2031
        self.record_span(span_start1280, "SnapshotMapping")
        return result1281

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1282 = []
        cond1283 = self.match_lookahead_literal("(", 0)
        while cond1283:
            _t2032 = self.parse_read()
            item1284 = _t2032
            xs1282.append(item1284)
            cond1283 = self.match_lookahead_literal("(", 0)
        reads1285 = xs1282
        self.consume_literal(")")
        return reads1285

    def parse_read(self) -> transactions_pb2.Read:
        span_start1292 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2034 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2035 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t2036 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t2037 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t2038 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t2039 = 3
                                else:
                                    _t2039 = -1
                                _t2038 = _t2039
                            _t2037 = _t2038
                        _t2036 = _t2037
                    _t2035 = _t2036
                _t2034 = _t2035
            _t2033 = _t2034
        else:
            _t2033 = -1
        prediction1286 = _t2033
        if prediction1286 == 4:
            _t2041 = self.parse_export()
            export1291 = _t2041
            _t2042 = transactions_pb2.Read(export=export1291)
            _t2040 = _t2042
        else:
            if prediction1286 == 3:
                _t2044 = self.parse_abort()
                abort1290 = _t2044
                _t2045 = transactions_pb2.Read(abort=abort1290)
                _t2043 = _t2045
            else:
                if prediction1286 == 2:
                    _t2047 = self.parse_what_if()
                    what_if1289 = _t2047
                    _t2048 = transactions_pb2.Read(what_if=what_if1289)
                    _t2046 = _t2048
                else:
                    if prediction1286 == 1:
                        _t2050 = self.parse_output()
                        output1288 = _t2050
                        _t2051 = transactions_pb2.Read(output=output1288)
                        _t2049 = _t2051
                    else:
                        if prediction1286 == 0:
                            _t2053 = self.parse_demand()
                            demand1287 = _t2053
                            _t2054 = transactions_pb2.Read(demand=demand1287)
                            _t2052 = _t2054
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2049 = _t2052
                    _t2046 = _t2049
                _t2043 = _t2046
            _t2040 = _t2043
        result1293 = _t2040
        self.record_span(span_start1292, "Read")
        return result1293

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1295 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2055 = self.parse_relation_id()
        relation_id1294 = _t2055
        self.consume_literal(")")
        _t2056 = transactions_pb2.Demand(relation_id=relation_id1294)
        result1296 = _t2056
        self.record_span(span_start1295, "Demand")
        return result1296

    def parse_output(self) -> transactions_pb2.Output:
        span_start1299 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2057 = self.parse_name()
        name1297 = _t2057
        _t2058 = self.parse_relation_id()
        relation_id1298 = _t2058
        self.consume_literal(")")
        _t2059 = transactions_pb2.Output(name=name1297, relation_id=relation_id1298)
        result1300 = _t2059
        self.record_span(span_start1299, "Output")
        return result1300

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1303 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2060 = self.parse_name()
        name1301 = _t2060
        _t2061 = self.parse_epoch()
        epoch1302 = _t2061
        self.consume_literal(")")
        _t2062 = transactions_pb2.WhatIf(branch=name1301, epoch=epoch1302)
        result1304 = _t2062
        self.record_span(span_start1303, "WhatIf")
        return result1304

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1307 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2064 = self.parse_name()
            _t2063 = _t2064
        else:
            _t2063 = None
        name1305 = _t2063
        _t2065 = self.parse_relation_id()
        relation_id1306 = _t2065
        self.consume_literal(")")
        _t2066 = transactions_pb2.Abort(name=(name1305 if name1305 is not None else "abort"), relation_id=relation_id1306)
        result1308 = _t2066
        self.record_span(span_start1307, "Abort")
        return result1308

    def parse_export(self) -> transactions_pb2.Export:
        span_start1312 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2068 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2069 = 0
                else:
                    _t2069 = -1
                _t2068 = _t2069
            _t2067 = _t2068
        else:
            _t2067 = -1
        prediction1309 = _t2067
        if prediction1309 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2071 = self.parse_export_iceberg_config()
            export_iceberg_config1311 = _t2071
            self.consume_literal(")")
            _t2072 = transactions_pb2.Export(iceberg_config=export_iceberg_config1311)
            _t2070 = _t2072
        else:
            if prediction1309 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2074 = self.parse_export_csv_config()
                export_csv_config1310 = _t2074
                self.consume_literal(")")
                _t2075 = transactions_pb2.Export(csv_config=export_csv_config1310)
                _t2073 = _t2075
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2070 = _t2073
        result1313 = _t2070
        self.record_span(span_start1312, "Export")
        return result1313

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1321 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2077 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2078 = 1
                else:
                    _t2078 = -1
                _t2077 = _t2078
            _t2076 = _t2077
        else:
            _t2076 = -1
        prediction1314 = _t2076
        if prediction1314 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2080 = self.parse_export_csv_path()
            export_csv_path1318 = _t2080
            _t2081 = self.parse_export_csv_columns_list()
            export_csv_columns_list1319 = _t2081
            _t2082 = self.parse_config_dict()
            config_dict1320 = _t2082
            self.consume_literal(")")
            _t2083 = self.construct_export_csv_config(export_csv_path1318, export_csv_columns_list1319, config_dict1320)
            _t2079 = _t2083
        else:
            if prediction1314 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2085 = self.parse_export_csv_path()
                export_csv_path1315 = _t2085
                _t2086 = self.parse_export_csv_source()
                export_csv_source1316 = _t2086
                _t2087 = self.parse_csv_config()
                csv_config1317 = _t2087
                self.consume_literal(")")
                _t2088 = self.construct_export_csv_config_with_source(export_csv_path1315, export_csv_source1316, csv_config1317)
                _t2084 = _t2088
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2079 = _t2084
        result1322 = _t2079
        self.record_span(span_start1321, "ExportCSVConfig")
        return result1322

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1323 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1323

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1330 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2090 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2091 = 0
                else:
                    _t2091 = -1
                _t2090 = _t2091
            _t2089 = _t2090
        else:
            _t2089 = -1
        prediction1324 = _t2089
        if prediction1324 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2093 = self.parse_relation_id()
            relation_id1329 = _t2093
            self.consume_literal(")")
            _t2094 = transactions_pb2.ExportCSVSource(table_def=relation_id1329)
            _t2092 = _t2094
        else:
            if prediction1324 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1325 = []
                cond1326 = self.match_lookahead_literal("(", 0)
                while cond1326:
                    _t2096 = self.parse_export_csv_column()
                    item1327 = _t2096
                    xs1325.append(item1327)
                    cond1326 = self.match_lookahead_literal("(", 0)
                export_csv_columns1328 = xs1325
                self.consume_literal(")")
                _t2097 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1328)
                _t2098 = transactions_pb2.ExportCSVSource(gnf_columns=_t2097)
                _t2095 = _t2098
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2092 = _t2095
        result1331 = _t2092
        self.record_span(span_start1330, "ExportCSVSource")
        return result1331

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1334 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1332 = self.consume_terminal("STRING")
        _t2099 = self.parse_relation_id()
        relation_id1333 = _t2099
        self.consume_literal(")")
        _t2100 = transactions_pb2.ExportCSVColumn(column_name=string1332, column_data=relation_id1333)
        result1335 = _t2100
        self.record_span(span_start1334, "ExportCSVColumn")
        return result1335

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1336 = []
        cond1337 = self.match_lookahead_literal("(", 0)
        while cond1337:
            _t2101 = self.parse_export_csv_column()
            item1338 = _t2101
            xs1336.append(item1338)
            cond1337 = self.match_lookahead_literal("(", 0)
        export_csv_columns1339 = xs1336
        self.consume_literal(")")
        return export_csv_columns1339

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1345 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2102 = self.parse_iceberg_locator()
        iceberg_locator1340 = _t2102
        _t2103 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1341 = _t2103
        _t2104 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1342 = _t2104
        _t2105 = self.parse_iceberg_table_properties()
        iceberg_table_properties1343 = _t2105
        if self.match_lookahead_literal("{", 0):
            _t2107 = self.parse_config_dict()
            _t2106 = _t2107
        else:
            _t2106 = None
        config_dict1344 = _t2106
        self.consume_literal(")")
        _t2108 = self.construct_export_iceberg_config_full(iceberg_locator1340, iceberg_catalog_config1341, export_iceberg_table_def1342, iceberg_table_properties1343, config_dict1344)
        result1346 = _t2108
        self.record_span(span_start1345, "ExportIcebergConfig")
        return result1346

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1348 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2109 = self.parse_relation_id()
        relation_id1347 = _t2109
        self.consume_literal(")")
        result1349 = relation_id1347
        self.record_span(span_start1348, "RelationId")
        return result1349

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1350 = []
        cond1351 = self.match_lookahead_literal("(", 0)
        while cond1351:
            _t2110 = self.parse_iceberg_property_entry()
            item1352 = _t2110
            xs1350.append(item1352)
            cond1351 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1353 = xs1350
        self.consume_literal(")")
        return iceberg_property_entrys1353


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
