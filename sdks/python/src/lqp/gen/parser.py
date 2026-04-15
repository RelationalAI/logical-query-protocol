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
            _t2103 = value.HasField("int32_value")
        else:
            _t2103 = False
        if _t2103:
            assert value is not None
            return value.int32_value
        else:
            _t2104 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2105 = value.HasField("int_value")
        else:
            _t2105 = False
        if _t2105:
            assert value is not None
            return value.int_value
        else:
            _t2106 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2107 = value.HasField("string_value")
        else:
            _t2107 = False
        if _t2107:
            assert value is not None
            return value.string_value
        else:
            _t2108 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2109 = value.HasField("boolean_value")
        else:
            _t2109 = False
        if _t2109:
            assert value is not None
            return value.boolean_value
        else:
            _t2110 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2111 = value.HasField("string_value")
        else:
            _t2111 = False
        if _t2111:
            assert value is not None
            return [value.string_value]
        else:
            _t2112 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
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
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2115 = value.HasField("float_value")
        else:
            _t2115 = False
        if _t2115:
            assert value is not None
            return value.float_value
        else:
            _t2116 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2117 = value.HasField("string_value")
        else:
            _t2117 = False
        if _t2117:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2118 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2119 = value.HasField("uint128_value")
        else:
            _t2119 = False
        if _t2119:
            assert value is not None
            return value.uint128_value
        else:
            _t2120 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2121 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2121
        _t2122 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2122
        _t2123 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2123
        _t2124 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2124
        _t2125 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2125
        _t2126 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2126
        _t2127 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2127
        _t2128 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2128
        _t2129 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2129
        _t2130 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2130
        _t2131 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t2131
        _t2132 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2132
        _t2133 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t2133

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2134 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2134
        _t2135 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2135
        _t2136 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2136
        _t2137 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2137
        _t2138 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2138
        _t2139 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2139
        _t2140 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2140
        _t2141 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2141
        _t2142 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2142
        _t2143 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2143
        _t2144 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2144

    def default_configure(self) -> transactions_pb2.Configure:
        _t2145 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2145
        _t2146 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2146

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
        _t2147 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2147
        _t2148 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2148
        _t2149 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2149

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2150 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2150
        _t2151 = self._extract_value_string(config.get("compression"), "")
        compression = _t2151
        _t2152 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2152
        _t2153 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2153
        _t2154 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2154
        _t2155 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2155
        _t2156 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2156
        _t2157 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2157

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2158 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2158

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2159 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2159

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[logic_pb2.GNFColumn], from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2160 = logic_pb2.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2160

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, columns: Sequence[transactions_pb2.ExportColumn], table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2161 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2161
        _t2162 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2162
        _t2163 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2163
        table_props = dict(table_property_pairs)
        _t2164 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2164

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start680 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1349 = self.parse_configure()
            _t1348 = _t1349
        else:
            _t1348 = None
        configure674 = _t1348
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1351 = self.parse_sync()
            _t1350 = _t1351
        else:
            _t1350 = None
        sync675 = _t1350
        xs676 = []
        cond677 = self.match_lookahead_literal("(", 0)
        while cond677:
            _t1352 = self.parse_epoch()
            item678 = _t1352
            xs676.append(item678)
            cond677 = self.match_lookahead_literal("(", 0)
        epochs679 = xs676
        self.consume_literal(")")
        _t1353 = self.default_configure()
        _t1354 = transactions_pb2.Transaction(epochs=epochs679, configure=(configure674 if configure674 is not None else _t1353), sync=sync675)
        result681 = _t1354
        self.record_span(span_start680, "Transaction")
        return result681

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start683 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1355 = self.parse_config_dict()
        config_dict682 = _t1355
        self.consume_literal(")")
        _t1356 = self.construct_configure(config_dict682)
        result684 = _t1356
        self.record_span(span_start683, "Configure")
        return result684

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs685 = []
        cond686 = self.match_lookahead_literal(":", 0)
        while cond686:
            _t1357 = self.parse_config_key_value()
            item687 = _t1357
            xs685.append(item687)
            cond686 = self.match_lookahead_literal(":", 0)
        config_key_values688 = xs685
        self.consume_literal("}")
        return config_key_values688

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol689 = self.consume_terminal("SYMBOL")
        _t1358 = self.parse_raw_value()
        raw_value690 = _t1358
        return (symbol689, raw_value690,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start704 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1359 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1360 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1361 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1363 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1364 = 0
                            else:
                                _t1364 = -1
                            _t1363 = _t1364
                        _t1362 = _t1363
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1365 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1366 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1367 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1368 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1369 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1370 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1371 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1372 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1373 = 10
                                                        else:
                                                            _t1373 = -1
                                                        _t1372 = _t1373
                                                    _t1371 = _t1372
                                                _t1370 = _t1371
                                            _t1369 = _t1370
                                        _t1368 = _t1369
                                    _t1367 = _t1368
                                _t1366 = _t1367
                            _t1365 = _t1366
                        _t1362 = _t1365
                    _t1361 = _t1362
                _t1360 = _t1361
            _t1359 = _t1360
        prediction691 = _t1359
        if prediction691 == 12:
            _t1375 = self.parse_boolean_value()
            boolean_value703 = _t1375
            _t1376 = logic_pb2.Value(boolean_value=boolean_value703)
            _t1374 = _t1376
        else:
            if prediction691 == 11:
                self.consume_literal("missing")
                _t1378 = logic_pb2.MissingValue()
                _t1379 = logic_pb2.Value(missing_value=_t1378)
                _t1377 = _t1379
            else:
                if prediction691 == 10:
                    decimal702 = self.consume_terminal("DECIMAL")
                    _t1381 = logic_pb2.Value(decimal_value=decimal702)
                    _t1380 = _t1381
                else:
                    if prediction691 == 9:
                        int128701 = self.consume_terminal("INT128")
                        _t1383 = logic_pb2.Value(int128_value=int128701)
                        _t1382 = _t1383
                    else:
                        if prediction691 == 8:
                            uint128700 = self.consume_terminal("UINT128")
                            _t1385 = logic_pb2.Value(uint128_value=uint128700)
                            _t1384 = _t1385
                        else:
                            if prediction691 == 7:
                                uint32699 = self.consume_terminal("UINT32")
                                _t1387 = logic_pb2.Value(uint32_value=uint32699)
                                _t1386 = _t1387
                            else:
                                if prediction691 == 6:
                                    float698 = self.consume_terminal("FLOAT")
                                    _t1389 = logic_pb2.Value(float_value=float698)
                                    _t1388 = _t1389
                                else:
                                    if prediction691 == 5:
                                        float32697 = self.consume_terminal("FLOAT32")
                                        _t1391 = logic_pb2.Value(float32_value=float32697)
                                        _t1390 = _t1391
                                    else:
                                        if prediction691 == 4:
                                            int696 = self.consume_terminal("INT")
                                            _t1393 = logic_pb2.Value(int_value=int696)
                                            _t1392 = _t1393
                                        else:
                                            if prediction691 == 3:
                                                int32695 = self.consume_terminal("INT32")
                                                _t1395 = logic_pb2.Value(int32_value=int32695)
                                                _t1394 = _t1395
                                            else:
                                                if prediction691 == 2:
                                                    string694 = self.consume_terminal("STRING")
                                                    _t1397 = logic_pb2.Value(string_value=string694)
                                                    _t1396 = _t1397
                                                else:
                                                    if prediction691 == 1:
                                                        _t1399 = self.parse_raw_datetime()
                                                        raw_datetime693 = _t1399
                                                        _t1400 = logic_pb2.Value(datetime_value=raw_datetime693)
                                                        _t1398 = _t1400
                                                    else:
                                                        if prediction691 == 0:
                                                            _t1402 = self.parse_raw_date()
                                                            raw_date692 = _t1402
                                                            _t1403 = logic_pb2.Value(date_value=raw_date692)
                                                            _t1401 = _t1403
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1398 = _t1401
                                                    _t1396 = _t1398
                                                _t1394 = _t1396
                                            _t1392 = _t1394
                                        _t1390 = _t1392
                                    _t1388 = _t1390
                                _t1386 = _t1388
                            _t1384 = _t1386
                        _t1382 = _t1384
                    _t1380 = _t1382
                _t1377 = _t1380
            _t1374 = _t1377
        result705 = _t1374
        self.record_span(span_start704, "Value")
        return result705

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start709 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int706 = self.consume_terminal("INT")
        int_3707 = self.consume_terminal("INT")
        int_4708 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1404 = logic_pb2.DateValue(year=int(int706), month=int(int_3707), day=int(int_4708))
        result710 = _t1404
        self.record_span(span_start709, "DateValue")
        return result710

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start718 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int711 = self.consume_terminal("INT")
        int_3712 = self.consume_terminal("INT")
        int_4713 = self.consume_terminal("INT")
        int_5714 = self.consume_terminal("INT")
        int_6715 = self.consume_terminal("INT")
        int_7716 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1405 = self.consume_terminal("INT")
        else:
            _t1405 = None
        int_8717 = _t1405
        self.consume_literal(")")
        _t1406 = logic_pb2.DateTimeValue(year=int(int711), month=int(int_3712), day=int(int_4713), hour=int(int_5714), minute=int(int_6715), second=int(int_7716), microsecond=int((int_8717 if int_8717 is not None else 0)))
        result719 = _t1406
        self.record_span(span_start718, "DateTimeValue")
        return result719

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1407 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1408 = 1
            else:
                _t1408 = -1
            _t1407 = _t1408
        prediction720 = _t1407
        if prediction720 == 1:
            self.consume_literal("false")
            _t1409 = False
        else:
            if prediction720 == 0:
                self.consume_literal("true")
                _t1410 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1409 = _t1410
        return _t1409

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start725 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs721 = []
        cond722 = self.match_lookahead_literal(":", 0)
        while cond722:
            _t1411 = self.parse_fragment_id()
            item723 = _t1411
            xs721.append(item723)
            cond722 = self.match_lookahead_literal(":", 0)
        fragment_ids724 = xs721
        self.consume_literal(")")
        _t1412 = transactions_pb2.Sync(fragments=fragment_ids724)
        result726 = _t1412
        self.record_span(span_start725, "Sync")
        return result726

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start728 = self.span_start()
        self.consume_literal(":")
        symbol727 = self.consume_terminal("SYMBOL")
        result729 = fragments_pb2.FragmentId(id=symbol727.encode())
        self.record_span(span_start728, "FragmentId")
        return result729

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start732 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1414 = self.parse_epoch_writes()
            _t1413 = _t1414
        else:
            _t1413 = None
        epoch_writes730 = _t1413
        if self.match_lookahead_literal("(", 0):
            _t1416 = self.parse_epoch_reads()
            _t1415 = _t1416
        else:
            _t1415 = None
        epoch_reads731 = _t1415
        self.consume_literal(")")
        _t1417 = transactions_pb2.Epoch(writes=(epoch_writes730 if epoch_writes730 is not None else []), reads=(epoch_reads731 if epoch_reads731 is not None else []))
        result733 = _t1417
        self.record_span(span_start732, "Epoch")
        return result733

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs734 = []
        cond735 = self.match_lookahead_literal("(", 0)
        while cond735:
            _t1418 = self.parse_write()
            item736 = _t1418
            xs734.append(item736)
            cond735 = self.match_lookahead_literal("(", 0)
        writes737 = xs734
        self.consume_literal(")")
        return writes737

    def parse_write(self) -> transactions_pb2.Write:
        span_start743 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1420 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1421 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1422 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1423 = 2
                        else:
                            _t1423 = -1
                        _t1422 = _t1423
                    _t1421 = _t1422
                _t1420 = _t1421
            _t1419 = _t1420
        else:
            _t1419 = -1
        prediction738 = _t1419
        if prediction738 == 3:
            _t1425 = self.parse_snapshot()
            snapshot742 = _t1425
            _t1426 = transactions_pb2.Write(snapshot=snapshot742)
            _t1424 = _t1426
        else:
            if prediction738 == 2:
                _t1428 = self.parse_context()
                context741 = _t1428
                _t1429 = transactions_pb2.Write(context=context741)
                _t1427 = _t1429
            else:
                if prediction738 == 1:
                    _t1431 = self.parse_undefine()
                    undefine740 = _t1431
                    _t1432 = transactions_pb2.Write(undefine=undefine740)
                    _t1430 = _t1432
                else:
                    if prediction738 == 0:
                        _t1434 = self.parse_define()
                        define739 = _t1434
                        _t1435 = transactions_pb2.Write(define=define739)
                        _t1433 = _t1435
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1430 = _t1433
                _t1427 = _t1430
            _t1424 = _t1427
        result744 = _t1424
        self.record_span(span_start743, "Write")
        return result744

    def parse_define(self) -> transactions_pb2.Define:
        span_start746 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1436 = self.parse_fragment()
        fragment745 = _t1436
        self.consume_literal(")")
        _t1437 = transactions_pb2.Define(fragment=fragment745)
        result747 = _t1437
        self.record_span(span_start746, "Define")
        return result747

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start753 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1438 = self.parse_new_fragment_id()
        new_fragment_id748 = _t1438
        xs749 = []
        cond750 = self.match_lookahead_literal("(", 0)
        while cond750:
            _t1439 = self.parse_declaration()
            item751 = _t1439
            xs749.append(item751)
            cond750 = self.match_lookahead_literal("(", 0)
        declarations752 = xs749
        self.consume_literal(")")
        result754 = self.construct_fragment(new_fragment_id748, declarations752)
        self.record_span(span_start753, "Fragment")
        return result754

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start756 = self.span_start()
        _t1440 = self.parse_fragment_id()
        fragment_id755 = _t1440
        self.start_fragment(fragment_id755)
        result757 = fragment_id755
        self.record_span(span_start756, "FragmentId")
        return result757

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start763 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1442 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1443 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1444 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1445 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1446 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1447 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1448 = 1
                                    else:
                                        _t1448 = -1
                                    _t1447 = _t1448
                                _t1446 = _t1447
                            _t1445 = _t1446
                        _t1444 = _t1445
                    _t1443 = _t1444
                _t1442 = _t1443
            _t1441 = _t1442
        else:
            _t1441 = -1
        prediction758 = _t1441
        if prediction758 == 3:
            _t1450 = self.parse_data()
            data762 = _t1450
            _t1451 = logic_pb2.Declaration(data=data762)
            _t1449 = _t1451
        else:
            if prediction758 == 2:
                _t1453 = self.parse_constraint()
                constraint761 = _t1453
                _t1454 = logic_pb2.Declaration(constraint=constraint761)
                _t1452 = _t1454
            else:
                if prediction758 == 1:
                    _t1456 = self.parse_algorithm()
                    algorithm760 = _t1456
                    _t1457 = logic_pb2.Declaration(algorithm=algorithm760)
                    _t1455 = _t1457
                else:
                    if prediction758 == 0:
                        _t1459 = self.parse_def()
                        def759 = _t1459
                        _t1460 = logic_pb2.Declaration()
                        getattr(_t1460, 'def').CopyFrom(def759)
                        _t1458 = _t1460
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1455 = _t1458
                _t1452 = _t1455
            _t1449 = _t1452
        result764 = _t1449
        self.record_span(span_start763, "Declaration")
        return result764

    def parse_def(self) -> logic_pb2.Def:
        span_start768 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1461 = self.parse_relation_id()
        relation_id765 = _t1461
        _t1462 = self.parse_abstraction()
        abstraction766 = _t1462
        if self.match_lookahead_literal("(", 0):
            _t1464 = self.parse_attrs()
            _t1463 = _t1464
        else:
            _t1463 = None
        attrs767 = _t1463
        self.consume_literal(")")
        _t1465 = logic_pb2.Def(name=relation_id765, body=abstraction766, attrs=(attrs767 if attrs767 is not None else []))
        result769 = _t1465
        self.record_span(span_start768, "Def")
        return result769

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start773 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1466 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1467 = 1
            else:
                _t1467 = -1
            _t1466 = _t1467
        prediction770 = _t1466
        if prediction770 == 1:
            uint128772 = self.consume_terminal("UINT128")
            _t1468 = logic_pb2.RelationId(id_low=uint128772.low, id_high=uint128772.high)
        else:
            if prediction770 == 0:
                self.consume_literal(":")
                symbol771 = self.consume_terminal("SYMBOL")
                _t1469 = self.relation_id_from_string(symbol771)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1468 = _t1469
        result774 = _t1468
        self.record_span(span_start773, "RelationId")
        return result774

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start777 = self.span_start()
        self.consume_literal("(")
        _t1470 = self.parse_bindings()
        bindings775 = _t1470
        _t1471 = self.parse_formula()
        formula776 = _t1471
        self.consume_literal(")")
        _t1472 = logic_pb2.Abstraction(vars=(list(bindings775[0]) + list(bindings775[1] if bindings775[1] is not None else [])), value=formula776)
        result778 = _t1472
        self.record_span(span_start777, "Abstraction")
        return result778

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs779 = []
        cond780 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond780:
            _t1473 = self.parse_binding()
            item781 = _t1473
            xs779.append(item781)
            cond780 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings782 = xs779
        if self.match_lookahead_literal("|", 0):
            _t1475 = self.parse_value_bindings()
            _t1474 = _t1475
        else:
            _t1474 = None
        value_bindings783 = _t1474
        self.consume_literal("]")
        return (bindings782, (value_bindings783 if value_bindings783 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start786 = self.span_start()
        symbol784 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1476 = self.parse_type()
        type785 = _t1476
        _t1477 = logic_pb2.Var(name=symbol784)
        _t1478 = logic_pb2.Binding(var=_t1477, type=type785)
        result787 = _t1478
        self.record_span(span_start786, "Binding")
        return result787

    def parse_type(self) -> logic_pb2.Type:
        span_start803 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1479 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1480 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1481 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1482 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1483 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1484 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1485 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1486 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1487 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1488 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1489 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1490 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1491 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1492 = 9
                                                            else:
                                                                _t1492 = -1
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
                _t1480 = _t1481
            _t1479 = _t1480
        prediction788 = _t1479
        if prediction788 == 13:
            _t1494 = self.parse_uint32_type()
            uint32_type802 = _t1494
            _t1495 = logic_pb2.Type(uint32_type=uint32_type802)
            _t1493 = _t1495
        else:
            if prediction788 == 12:
                _t1497 = self.parse_float32_type()
                float32_type801 = _t1497
                _t1498 = logic_pb2.Type(float32_type=float32_type801)
                _t1496 = _t1498
            else:
                if prediction788 == 11:
                    _t1500 = self.parse_int32_type()
                    int32_type800 = _t1500
                    _t1501 = logic_pb2.Type(int32_type=int32_type800)
                    _t1499 = _t1501
                else:
                    if prediction788 == 10:
                        _t1503 = self.parse_boolean_type()
                        boolean_type799 = _t1503
                        _t1504 = logic_pb2.Type(boolean_type=boolean_type799)
                        _t1502 = _t1504
                    else:
                        if prediction788 == 9:
                            _t1506 = self.parse_decimal_type()
                            decimal_type798 = _t1506
                            _t1507 = logic_pb2.Type(decimal_type=decimal_type798)
                            _t1505 = _t1507
                        else:
                            if prediction788 == 8:
                                _t1509 = self.parse_missing_type()
                                missing_type797 = _t1509
                                _t1510 = logic_pb2.Type(missing_type=missing_type797)
                                _t1508 = _t1510
                            else:
                                if prediction788 == 7:
                                    _t1512 = self.parse_datetime_type()
                                    datetime_type796 = _t1512
                                    _t1513 = logic_pb2.Type(datetime_type=datetime_type796)
                                    _t1511 = _t1513
                                else:
                                    if prediction788 == 6:
                                        _t1515 = self.parse_date_type()
                                        date_type795 = _t1515
                                        _t1516 = logic_pb2.Type(date_type=date_type795)
                                        _t1514 = _t1516
                                    else:
                                        if prediction788 == 5:
                                            _t1518 = self.parse_int128_type()
                                            int128_type794 = _t1518
                                            _t1519 = logic_pb2.Type(int128_type=int128_type794)
                                            _t1517 = _t1519
                                        else:
                                            if prediction788 == 4:
                                                _t1521 = self.parse_uint128_type()
                                                uint128_type793 = _t1521
                                                _t1522 = logic_pb2.Type(uint128_type=uint128_type793)
                                                _t1520 = _t1522
                                            else:
                                                if prediction788 == 3:
                                                    _t1524 = self.parse_float_type()
                                                    float_type792 = _t1524
                                                    _t1525 = logic_pb2.Type(float_type=float_type792)
                                                    _t1523 = _t1525
                                                else:
                                                    if prediction788 == 2:
                                                        _t1527 = self.parse_int_type()
                                                        int_type791 = _t1527
                                                        _t1528 = logic_pb2.Type(int_type=int_type791)
                                                        _t1526 = _t1528
                                                    else:
                                                        if prediction788 == 1:
                                                            _t1530 = self.parse_string_type()
                                                            string_type790 = _t1530
                                                            _t1531 = logic_pb2.Type(string_type=string_type790)
                                                            _t1529 = _t1531
                                                        else:
                                                            if prediction788 == 0:
                                                                _t1533 = self.parse_unspecified_type()
                                                                unspecified_type789 = _t1533
                                                                _t1534 = logic_pb2.Type(unspecified_type=unspecified_type789)
                                                                _t1532 = _t1534
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1496 = _t1499
            _t1493 = _t1496
        result804 = _t1493
        self.record_span(span_start803, "Type")
        return result804

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start805 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1535 = logic_pb2.UnspecifiedType()
        result806 = _t1535
        self.record_span(span_start805, "UnspecifiedType")
        return result806

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start807 = self.span_start()
        self.consume_literal("STRING")
        _t1536 = logic_pb2.StringType()
        result808 = _t1536
        self.record_span(span_start807, "StringType")
        return result808

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start809 = self.span_start()
        self.consume_literal("INT")
        _t1537 = logic_pb2.IntType()
        result810 = _t1537
        self.record_span(span_start809, "IntType")
        return result810

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start811 = self.span_start()
        self.consume_literal("FLOAT")
        _t1538 = logic_pb2.FloatType()
        result812 = _t1538
        self.record_span(span_start811, "FloatType")
        return result812

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start813 = self.span_start()
        self.consume_literal("UINT128")
        _t1539 = logic_pb2.UInt128Type()
        result814 = _t1539
        self.record_span(span_start813, "UInt128Type")
        return result814

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start815 = self.span_start()
        self.consume_literal("INT128")
        _t1540 = logic_pb2.Int128Type()
        result816 = _t1540
        self.record_span(span_start815, "Int128Type")
        return result816

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start817 = self.span_start()
        self.consume_literal("DATE")
        _t1541 = logic_pb2.DateType()
        result818 = _t1541
        self.record_span(span_start817, "DateType")
        return result818

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start819 = self.span_start()
        self.consume_literal("DATETIME")
        _t1542 = logic_pb2.DateTimeType()
        result820 = _t1542
        self.record_span(span_start819, "DateTimeType")
        return result820

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start821 = self.span_start()
        self.consume_literal("MISSING")
        _t1543 = logic_pb2.MissingType()
        result822 = _t1543
        self.record_span(span_start821, "MissingType")
        return result822

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start825 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int823 = self.consume_terminal("INT")
        int_3824 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1544 = logic_pb2.DecimalType(precision=int(int823), scale=int(int_3824))
        result826 = _t1544
        self.record_span(span_start825, "DecimalType")
        return result826

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start827 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1545 = logic_pb2.BooleanType()
        result828 = _t1545
        self.record_span(span_start827, "BooleanType")
        return result828

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start829 = self.span_start()
        self.consume_literal("INT32")
        _t1546 = logic_pb2.Int32Type()
        result830 = _t1546
        self.record_span(span_start829, "Int32Type")
        return result830

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start831 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1547 = logic_pb2.Float32Type()
        result832 = _t1547
        self.record_span(span_start831, "Float32Type")
        return result832

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start833 = self.span_start()
        self.consume_literal("UINT32")
        _t1548 = logic_pb2.UInt32Type()
        result834 = _t1548
        self.record_span(span_start833, "UInt32Type")
        return result834

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs835 = []
        cond836 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond836:
            _t1549 = self.parse_binding()
            item837 = _t1549
            xs835.append(item837)
            cond836 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings838 = xs835
        return bindings838

    def parse_formula(self) -> logic_pb2.Formula:
        span_start853 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1551 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1552 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1553 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1554 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1555 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1556 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1557 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1558 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1559 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1560 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1561 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1562 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1563 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1564 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1565 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1566 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1567 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1568 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1569 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1570 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1571 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1572 = 10
                                                                                                else:
                                                                                                    _t1572 = -1
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
                _t1551 = _t1552
            _t1550 = _t1551
        else:
            _t1550 = -1
        prediction839 = _t1550
        if prediction839 == 12:
            _t1574 = self.parse_cast()
            cast852 = _t1574
            _t1575 = logic_pb2.Formula(cast=cast852)
            _t1573 = _t1575
        else:
            if prediction839 == 11:
                _t1577 = self.parse_rel_atom()
                rel_atom851 = _t1577
                _t1578 = logic_pb2.Formula(rel_atom=rel_atom851)
                _t1576 = _t1578
            else:
                if prediction839 == 10:
                    _t1580 = self.parse_primitive()
                    primitive850 = _t1580
                    _t1581 = logic_pb2.Formula(primitive=primitive850)
                    _t1579 = _t1581
                else:
                    if prediction839 == 9:
                        _t1583 = self.parse_pragma()
                        pragma849 = _t1583
                        _t1584 = logic_pb2.Formula(pragma=pragma849)
                        _t1582 = _t1584
                    else:
                        if prediction839 == 8:
                            _t1586 = self.parse_atom()
                            atom848 = _t1586
                            _t1587 = logic_pb2.Formula(atom=atom848)
                            _t1585 = _t1587
                        else:
                            if prediction839 == 7:
                                _t1589 = self.parse_ffi()
                                ffi847 = _t1589
                                _t1590 = logic_pb2.Formula(ffi=ffi847)
                                _t1588 = _t1590
                            else:
                                if prediction839 == 6:
                                    _t1592 = self.parse_not()
                                    not846 = _t1592
                                    _t1593 = logic_pb2.Formula()
                                    getattr(_t1593, 'not').CopyFrom(not846)
                                    _t1591 = _t1593
                                else:
                                    if prediction839 == 5:
                                        _t1595 = self.parse_disjunction()
                                        disjunction845 = _t1595
                                        _t1596 = logic_pb2.Formula(disjunction=disjunction845)
                                        _t1594 = _t1596
                                    else:
                                        if prediction839 == 4:
                                            _t1598 = self.parse_conjunction()
                                            conjunction844 = _t1598
                                            _t1599 = logic_pb2.Formula(conjunction=conjunction844)
                                            _t1597 = _t1599
                                        else:
                                            if prediction839 == 3:
                                                _t1601 = self.parse_reduce()
                                                reduce843 = _t1601
                                                _t1602 = logic_pb2.Formula(reduce=reduce843)
                                                _t1600 = _t1602
                                            else:
                                                if prediction839 == 2:
                                                    _t1604 = self.parse_exists()
                                                    exists842 = _t1604
                                                    _t1605 = logic_pb2.Formula(exists=exists842)
                                                    _t1603 = _t1605
                                                else:
                                                    if prediction839 == 1:
                                                        _t1607 = self.parse_false()
                                                        false841 = _t1607
                                                        _t1608 = logic_pb2.Formula(disjunction=false841)
                                                        _t1606 = _t1608
                                                    else:
                                                        if prediction839 == 0:
                                                            _t1610 = self.parse_true()
                                                            true840 = _t1610
                                                            _t1611 = logic_pb2.Formula(conjunction=true840)
                                                            _t1609 = _t1611
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1576 = _t1579
            _t1573 = _t1576
        result854 = _t1573
        self.record_span(span_start853, "Formula")
        return result854

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start855 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1612 = logic_pb2.Conjunction(args=[])
        result856 = _t1612
        self.record_span(span_start855, "Conjunction")
        return result856

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start857 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1613 = logic_pb2.Disjunction(args=[])
        result858 = _t1613
        self.record_span(span_start857, "Disjunction")
        return result858

    def parse_exists(self) -> logic_pb2.Exists:
        span_start861 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1614 = self.parse_bindings()
        bindings859 = _t1614
        _t1615 = self.parse_formula()
        formula860 = _t1615
        self.consume_literal(")")
        _t1616 = logic_pb2.Abstraction(vars=(list(bindings859[0]) + list(bindings859[1] if bindings859[1] is not None else [])), value=formula860)
        _t1617 = logic_pb2.Exists(body=_t1616)
        result862 = _t1617
        self.record_span(span_start861, "Exists")
        return result862

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start866 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1618 = self.parse_abstraction()
        abstraction863 = _t1618
        _t1619 = self.parse_abstraction()
        abstraction_3864 = _t1619
        _t1620 = self.parse_terms()
        terms865 = _t1620
        self.consume_literal(")")
        _t1621 = logic_pb2.Reduce(op=abstraction863, body=abstraction_3864, terms=terms865)
        result867 = _t1621
        self.record_span(span_start866, "Reduce")
        return result867

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs868 = []
        cond869 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond869:
            _t1622 = self.parse_term()
            item870 = _t1622
            xs868.append(item870)
            cond869 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms871 = xs868
        self.consume_literal(")")
        return terms871

    def parse_term(self) -> logic_pb2.Term:
        span_start875 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1623 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1624 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1625 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1626 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1627 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1628 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1629 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1630 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1631 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1632 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1633 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1634 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1635 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1636 = 1
                                                            else:
                                                                _t1636 = -1
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
        prediction872 = _t1623
        if prediction872 == 1:
            _t1638 = self.parse_value()
            value874 = _t1638
            _t1639 = logic_pb2.Term(constant=value874)
            _t1637 = _t1639
        else:
            if prediction872 == 0:
                _t1641 = self.parse_var()
                var873 = _t1641
                _t1642 = logic_pb2.Term(var=var873)
                _t1640 = _t1642
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1637 = _t1640
        result876 = _t1637
        self.record_span(span_start875, "Term")
        return result876

    def parse_var(self) -> logic_pb2.Var:
        span_start878 = self.span_start()
        symbol877 = self.consume_terminal("SYMBOL")
        _t1643 = logic_pb2.Var(name=symbol877)
        result879 = _t1643
        self.record_span(span_start878, "Var")
        return result879

    def parse_value(self) -> logic_pb2.Value:
        span_start893 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1644 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1645 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1646 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1648 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1649 = 0
                            else:
                                _t1649 = -1
                            _t1648 = _t1649
                        _t1647 = _t1648
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1650 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1651 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1652 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1653 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1654 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1655 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1656 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1657 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1658 = 10
                                                        else:
                                                            _t1658 = -1
                                                        _t1657 = _t1658
                                                    _t1656 = _t1657
                                                _t1655 = _t1656
                                            _t1654 = _t1655
                                        _t1653 = _t1654
                                    _t1652 = _t1653
                                _t1651 = _t1652
                            _t1650 = _t1651
                        _t1647 = _t1650
                    _t1646 = _t1647
                _t1645 = _t1646
            _t1644 = _t1645
        prediction880 = _t1644
        if prediction880 == 12:
            _t1660 = self.parse_boolean_value()
            boolean_value892 = _t1660
            _t1661 = logic_pb2.Value(boolean_value=boolean_value892)
            _t1659 = _t1661
        else:
            if prediction880 == 11:
                self.consume_literal("missing")
                _t1663 = logic_pb2.MissingValue()
                _t1664 = logic_pb2.Value(missing_value=_t1663)
                _t1662 = _t1664
            else:
                if prediction880 == 10:
                    formatted_decimal891 = self.consume_terminal("DECIMAL")
                    _t1666 = logic_pb2.Value(decimal_value=formatted_decimal891)
                    _t1665 = _t1666
                else:
                    if prediction880 == 9:
                        formatted_int128890 = self.consume_terminal("INT128")
                        _t1668 = logic_pb2.Value(int128_value=formatted_int128890)
                        _t1667 = _t1668
                    else:
                        if prediction880 == 8:
                            formatted_uint128889 = self.consume_terminal("UINT128")
                            _t1670 = logic_pb2.Value(uint128_value=formatted_uint128889)
                            _t1669 = _t1670
                        else:
                            if prediction880 == 7:
                                formatted_uint32888 = self.consume_terminal("UINT32")
                                _t1672 = logic_pb2.Value(uint32_value=formatted_uint32888)
                                _t1671 = _t1672
                            else:
                                if prediction880 == 6:
                                    formatted_float887 = self.consume_terminal("FLOAT")
                                    _t1674 = logic_pb2.Value(float_value=formatted_float887)
                                    _t1673 = _t1674
                                else:
                                    if prediction880 == 5:
                                        formatted_float32886 = self.consume_terminal("FLOAT32")
                                        _t1676 = logic_pb2.Value(float32_value=formatted_float32886)
                                        _t1675 = _t1676
                                    else:
                                        if prediction880 == 4:
                                            formatted_int885 = self.consume_terminal("INT")
                                            _t1678 = logic_pb2.Value(int_value=formatted_int885)
                                            _t1677 = _t1678
                                        else:
                                            if prediction880 == 3:
                                                formatted_int32884 = self.consume_terminal("INT32")
                                                _t1680 = logic_pb2.Value(int32_value=formatted_int32884)
                                                _t1679 = _t1680
                                            else:
                                                if prediction880 == 2:
                                                    formatted_string883 = self.consume_terminal("STRING")
                                                    _t1682 = logic_pb2.Value(string_value=formatted_string883)
                                                    _t1681 = _t1682
                                                else:
                                                    if prediction880 == 1:
                                                        _t1684 = self.parse_datetime()
                                                        datetime882 = _t1684
                                                        _t1685 = logic_pb2.Value(datetime_value=datetime882)
                                                        _t1683 = _t1685
                                                    else:
                                                        if prediction880 == 0:
                                                            _t1687 = self.parse_date()
                                                            date881 = _t1687
                                                            _t1688 = logic_pb2.Value(date_value=date881)
                                                            _t1686 = _t1688
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1683 = _t1686
                                                    _t1681 = _t1683
                                                _t1679 = _t1681
                                            _t1677 = _t1679
                                        _t1675 = _t1677
                                    _t1673 = _t1675
                                _t1671 = _t1673
                            _t1669 = _t1671
                        _t1667 = _t1669
                    _t1665 = _t1667
                _t1662 = _t1665
            _t1659 = _t1662
        result894 = _t1659
        self.record_span(span_start893, "Value")
        return result894

    def parse_date(self) -> logic_pb2.DateValue:
        span_start898 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int895 = self.consume_terminal("INT")
        formatted_int_3896 = self.consume_terminal("INT")
        formatted_int_4897 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1689 = logic_pb2.DateValue(year=int(formatted_int895), month=int(formatted_int_3896), day=int(formatted_int_4897))
        result899 = _t1689
        self.record_span(span_start898, "DateValue")
        return result899

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start907 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int900 = self.consume_terminal("INT")
        formatted_int_3901 = self.consume_terminal("INT")
        formatted_int_4902 = self.consume_terminal("INT")
        formatted_int_5903 = self.consume_terminal("INT")
        formatted_int_6904 = self.consume_terminal("INT")
        formatted_int_7905 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1690 = self.consume_terminal("INT")
        else:
            _t1690 = None
        formatted_int_8906 = _t1690
        self.consume_literal(")")
        _t1691 = logic_pb2.DateTimeValue(year=int(formatted_int900), month=int(formatted_int_3901), day=int(formatted_int_4902), hour=int(formatted_int_5903), minute=int(formatted_int_6904), second=int(formatted_int_7905), microsecond=int((formatted_int_8906 if formatted_int_8906 is not None else 0)))
        result908 = _t1691
        self.record_span(span_start907, "DateTimeValue")
        return result908

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start913 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs909 = []
        cond910 = self.match_lookahead_literal("(", 0)
        while cond910:
            _t1692 = self.parse_formula()
            item911 = _t1692
            xs909.append(item911)
            cond910 = self.match_lookahead_literal("(", 0)
        formulas912 = xs909
        self.consume_literal(")")
        _t1693 = logic_pb2.Conjunction(args=formulas912)
        result914 = _t1693
        self.record_span(span_start913, "Conjunction")
        return result914

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start919 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs915 = []
        cond916 = self.match_lookahead_literal("(", 0)
        while cond916:
            _t1694 = self.parse_formula()
            item917 = _t1694
            xs915.append(item917)
            cond916 = self.match_lookahead_literal("(", 0)
        formulas918 = xs915
        self.consume_literal(")")
        _t1695 = logic_pb2.Disjunction(args=formulas918)
        result920 = _t1695
        self.record_span(span_start919, "Disjunction")
        return result920

    def parse_not(self) -> logic_pb2.Not:
        span_start922 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1696 = self.parse_formula()
        formula921 = _t1696
        self.consume_literal(")")
        _t1697 = logic_pb2.Not(arg=formula921)
        result923 = _t1697
        self.record_span(span_start922, "Not")
        return result923

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start927 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1698 = self.parse_name()
        name924 = _t1698
        _t1699 = self.parse_ffi_args()
        ffi_args925 = _t1699
        _t1700 = self.parse_terms()
        terms926 = _t1700
        self.consume_literal(")")
        _t1701 = logic_pb2.FFI(name=name924, args=ffi_args925, terms=terms926)
        result928 = _t1701
        self.record_span(span_start927, "FFI")
        return result928

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol929 = self.consume_terminal("SYMBOL")
        return symbol929

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs930 = []
        cond931 = self.match_lookahead_literal("(", 0)
        while cond931:
            _t1702 = self.parse_abstraction()
            item932 = _t1702
            xs930.append(item932)
            cond931 = self.match_lookahead_literal("(", 0)
        abstractions933 = xs930
        self.consume_literal(")")
        return abstractions933

    def parse_atom(self) -> logic_pb2.Atom:
        span_start939 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1703 = self.parse_relation_id()
        relation_id934 = _t1703
        xs935 = []
        cond936 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond936:
            _t1704 = self.parse_term()
            item937 = _t1704
            xs935.append(item937)
            cond936 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms938 = xs935
        self.consume_literal(")")
        _t1705 = logic_pb2.Atom(name=relation_id934, terms=terms938)
        result940 = _t1705
        self.record_span(span_start939, "Atom")
        return result940

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start946 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1706 = self.parse_name()
        name941 = _t1706
        xs942 = []
        cond943 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond943:
            _t1707 = self.parse_term()
            item944 = _t1707
            xs942.append(item944)
            cond943 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms945 = xs942
        self.consume_literal(")")
        _t1708 = logic_pb2.Pragma(name=name941, terms=terms945)
        result947 = _t1708
        self.record_span(span_start946, "Pragma")
        return result947

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start963 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1710 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1711 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1712 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1713 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1714 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1715 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1716 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1717 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1718 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1719 = 7
                                                else:
                                                    _t1719 = -1
                                                _t1718 = _t1719
                                            _t1717 = _t1718
                                        _t1716 = _t1717
                                    _t1715 = _t1716
                                _t1714 = _t1715
                            _t1713 = _t1714
                        _t1712 = _t1713
                    _t1711 = _t1712
                _t1710 = _t1711
            _t1709 = _t1710
        else:
            _t1709 = -1
        prediction948 = _t1709
        if prediction948 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1721 = self.parse_name()
            name958 = _t1721
            xs959 = []
            cond960 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond960:
                _t1722 = self.parse_rel_term()
                item961 = _t1722
                xs959.append(item961)
                cond960 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms962 = xs959
            self.consume_literal(")")
            _t1723 = logic_pb2.Primitive(name=name958, terms=rel_terms962)
            _t1720 = _t1723
        else:
            if prediction948 == 8:
                _t1725 = self.parse_divide()
                divide957 = _t1725
                _t1724 = divide957
            else:
                if prediction948 == 7:
                    _t1727 = self.parse_multiply()
                    multiply956 = _t1727
                    _t1726 = multiply956
                else:
                    if prediction948 == 6:
                        _t1729 = self.parse_minus()
                        minus955 = _t1729
                        _t1728 = minus955
                    else:
                        if prediction948 == 5:
                            _t1731 = self.parse_add()
                            add954 = _t1731
                            _t1730 = add954
                        else:
                            if prediction948 == 4:
                                _t1733 = self.parse_gt_eq()
                                gt_eq953 = _t1733
                                _t1732 = gt_eq953
                            else:
                                if prediction948 == 3:
                                    _t1735 = self.parse_gt()
                                    gt952 = _t1735
                                    _t1734 = gt952
                                else:
                                    if prediction948 == 2:
                                        _t1737 = self.parse_lt_eq()
                                        lt_eq951 = _t1737
                                        _t1736 = lt_eq951
                                    else:
                                        if prediction948 == 1:
                                            _t1739 = self.parse_lt()
                                            lt950 = _t1739
                                            _t1738 = lt950
                                        else:
                                            if prediction948 == 0:
                                                _t1741 = self.parse_eq()
                                                eq949 = _t1741
                                                _t1740 = eq949
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1738 = _t1740
                                        _t1736 = _t1738
                                    _t1734 = _t1736
                                _t1732 = _t1734
                            _t1730 = _t1732
                        _t1728 = _t1730
                    _t1726 = _t1728
                _t1724 = _t1726
            _t1720 = _t1724
        result964 = _t1720
        self.record_span(span_start963, "Primitive")
        return result964

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start967 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1742 = self.parse_term()
        term965 = _t1742
        _t1743 = self.parse_term()
        term_3966 = _t1743
        self.consume_literal(")")
        _t1744 = logic_pb2.RelTerm(term=term965)
        _t1745 = logic_pb2.RelTerm(term=term_3966)
        _t1746 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1744, _t1745])
        result968 = _t1746
        self.record_span(span_start967, "Primitive")
        return result968

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start971 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1747 = self.parse_term()
        term969 = _t1747
        _t1748 = self.parse_term()
        term_3970 = _t1748
        self.consume_literal(")")
        _t1749 = logic_pb2.RelTerm(term=term969)
        _t1750 = logic_pb2.RelTerm(term=term_3970)
        _t1751 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1749, _t1750])
        result972 = _t1751
        self.record_span(span_start971, "Primitive")
        return result972

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start975 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1752 = self.parse_term()
        term973 = _t1752
        _t1753 = self.parse_term()
        term_3974 = _t1753
        self.consume_literal(")")
        _t1754 = logic_pb2.RelTerm(term=term973)
        _t1755 = logic_pb2.RelTerm(term=term_3974)
        _t1756 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1754, _t1755])
        result976 = _t1756
        self.record_span(span_start975, "Primitive")
        return result976

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start979 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1757 = self.parse_term()
        term977 = _t1757
        _t1758 = self.parse_term()
        term_3978 = _t1758
        self.consume_literal(")")
        _t1759 = logic_pb2.RelTerm(term=term977)
        _t1760 = logic_pb2.RelTerm(term=term_3978)
        _t1761 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1759, _t1760])
        result980 = _t1761
        self.record_span(span_start979, "Primitive")
        return result980

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start983 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1762 = self.parse_term()
        term981 = _t1762
        _t1763 = self.parse_term()
        term_3982 = _t1763
        self.consume_literal(")")
        _t1764 = logic_pb2.RelTerm(term=term981)
        _t1765 = logic_pb2.RelTerm(term=term_3982)
        _t1766 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1764, _t1765])
        result984 = _t1766
        self.record_span(span_start983, "Primitive")
        return result984

    def parse_add(self) -> logic_pb2.Primitive:
        span_start988 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1767 = self.parse_term()
        term985 = _t1767
        _t1768 = self.parse_term()
        term_3986 = _t1768
        _t1769 = self.parse_term()
        term_4987 = _t1769
        self.consume_literal(")")
        _t1770 = logic_pb2.RelTerm(term=term985)
        _t1771 = logic_pb2.RelTerm(term=term_3986)
        _t1772 = logic_pb2.RelTerm(term=term_4987)
        _t1773 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1770, _t1771, _t1772])
        result989 = _t1773
        self.record_span(span_start988, "Primitive")
        return result989

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start993 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1774 = self.parse_term()
        term990 = _t1774
        _t1775 = self.parse_term()
        term_3991 = _t1775
        _t1776 = self.parse_term()
        term_4992 = _t1776
        self.consume_literal(")")
        _t1777 = logic_pb2.RelTerm(term=term990)
        _t1778 = logic_pb2.RelTerm(term=term_3991)
        _t1779 = logic_pb2.RelTerm(term=term_4992)
        _t1780 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1777, _t1778, _t1779])
        result994 = _t1780
        self.record_span(span_start993, "Primitive")
        return result994

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start998 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1781 = self.parse_term()
        term995 = _t1781
        _t1782 = self.parse_term()
        term_3996 = _t1782
        _t1783 = self.parse_term()
        term_4997 = _t1783
        self.consume_literal(")")
        _t1784 = logic_pb2.RelTerm(term=term995)
        _t1785 = logic_pb2.RelTerm(term=term_3996)
        _t1786 = logic_pb2.RelTerm(term=term_4997)
        _t1787 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1784, _t1785, _t1786])
        result999 = _t1787
        self.record_span(span_start998, "Primitive")
        return result999

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start1003 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1788 = self.parse_term()
        term1000 = _t1788
        _t1789 = self.parse_term()
        term_31001 = _t1789
        _t1790 = self.parse_term()
        term_41002 = _t1790
        self.consume_literal(")")
        _t1791 = logic_pb2.RelTerm(term=term1000)
        _t1792 = logic_pb2.RelTerm(term=term_31001)
        _t1793 = logic_pb2.RelTerm(term=term_41002)
        _t1794 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1791, _t1792, _t1793])
        result1004 = _t1794
        self.record_span(span_start1003, "Primitive")
        return result1004

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1008 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1795 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1796 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1797 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1798 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1799 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1800 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1801 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1802 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1803 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1804 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1805 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1806 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1807 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1808 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1809 = 1
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
                        _t1798 = _t1799
                    _t1797 = _t1798
                _t1796 = _t1797
            _t1795 = _t1796
        prediction1005 = _t1795
        if prediction1005 == 1:
            _t1811 = self.parse_term()
            term1007 = _t1811
            _t1812 = logic_pb2.RelTerm(term=term1007)
            _t1810 = _t1812
        else:
            if prediction1005 == 0:
                _t1814 = self.parse_specialized_value()
                specialized_value1006 = _t1814
                _t1815 = logic_pb2.RelTerm(specialized_value=specialized_value1006)
                _t1813 = _t1815
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1810 = _t1813
        result1009 = _t1810
        self.record_span(span_start1008, "RelTerm")
        return result1009

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1011 = self.span_start()
        self.consume_literal("#")
        _t1816 = self.parse_raw_value()
        raw_value1010 = _t1816
        result1012 = raw_value1010
        self.record_span(span_start1011, "Value")
        return result1012

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1018 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1817 = self.parse_name()
        name1013 = _t1817
        xs1014 = []
        cond1015 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1015:
            _t1818 = self.parse_rel_term()
            item1016 = _t1818
            xs1014.append(item1016)
            cond1015 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1017 = xs1014
        self.consume_literal(")")
        _t1819 = logic_pb2.RelAtom(name=name1013, terms=rel_terms1017)
        result1019 = _t1819
        self.record_span(span_start1018, "RelAtom")
        return result1019

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1022 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1820 = self.parse_term()
        term1020 = _t1820
        _t1821 = self.parse_term()
        term_31021 = _t1821
        self.consume_literal(")")
        _t1822 = logic_pb2.Cast(input=term1020, result=term_31021)
        result1023 = _t1822
        self.record_span(span_start1022, "Cast")
        return result1023

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1024 = []
        cond1025 = self.match_lookahead_literal("(", 0)
        while cond1025:
            _t1823 = self.parse_attribute()
            item1026 = _t1823
            xs1024.append(item1026)
            cond1025 = self.match_lookahead_literal("(", 0)
        attributes1027 = xs1024
        self.consume_literal(")")
        return attributes1027

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1033 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1824 = self.parse_name()
        name1028 = _t1824
        xs1029 = []
        cond1030 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1030:
            _t1825 = self.parse_raw_value()
            item1031 = _t1825
            xs1029.append(item1031)
            cond1030 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1032 = xs1029
        self.consume_literal(")")
        _t1826 = logic_pb2.Attribute(name=name1028, args=raw_values1032)
        result1034 = _t1826
        self.record_span(span_start1033, "Attribute")
        return result1034

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1041 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1035 = []
        cond1036 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1036:
            _t1827 = self.parse_relation_id()
            item1037 = _t1827
            xs1035.append(item1037)
            cond1036 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1038 = xs1035
        _t1828 = self.parse_script()
        script1039 = _t1828
        if self.match_lookahead_literal("(", 0):
            _t1830 = self.parse_attrs()
            _t1829 = _t1830
        else:
            _t1829 = None
        attrs1040 = _t1829
        self.consume_literal(")")
        _t1831 = logic_pb2.Algorithm(body=script1039, attrs=(attrs1040 if attrs1040 is not None else []))
        getattr(_t1831, 'global').extend(relation_ids1038)
        result1042 = _t1831
        self.record_span(span_start1041, "Algorithm")
        return result1042

    def parse_script(self) -> logic_pb2.Script:
        span_start1047 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1043 = []
        cond1044 = self.match_lookahead_literal("(", 0)
        while cond1044:
            _t1832 = self.parse_construct()
            item1045 = _t1832
            xs1043.append(item1045)
            cond1044 = self.match_lookahead_literal("(", 0)
        constructs1046 = xs1043
        self.consume_literal(")")
        _t1833 = logic_pb2.Script(constructs=constructs1046)
        result1048 = _t1833
        self.record_span(span_start1047, "Script")
        return result1048

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1052 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1835 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1836 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1837 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1838 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1839 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1840 = 1
                                else:
                                    _t1840 = -1
                                _t1839 = _t1840
                            _t1838 = _t1839
                        _t1837 = _t1838
                    _t1836 = _t1837
                _t1835 = _t1836
            _t1834 = _t1835
        else:
            _t1834 = -1
        prediction1049 = _t1834
        if prediction1049 == 1:
            _t1842 = self.parse_instruction()
            instruction1051 = _t1842
            _t1843 = logic_pb2.Construct(instruction=instruction1051)
            _t1841 = _t1843
        else:
            if prediction1049 == 0:
                _t1845 = self.parse_loop()
                loop1050 = _t1845
                _t1846 = logic_pb2.Construct(loop=loop1050)
                _t1844 = _t1846
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1841 = _t1844
        result1053 = _t1841
        self.record_span(span_start1052, "Construct")
        return result1053

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1057 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1847 = self.parse_init()
        init1054 = _t1847
        _t1848 = self.parse_script()
        script1055 = _t1848
        if self.match_lookahead_literal("(", 0):
            _t1850 = self.parse_attrs()
            _t1849 = _t1850
        else:
            _t1849 = None
        attrs1056 = _t1849
        self.consume_literal(")")
        _t1851 = logic_pb2.Loop(init=init1054, body=script1055, attrs=(attrs1056 if attrs1056 is not None else []))
        result1058 = _t1851
        self.record_span(span_start1057, "Loop")
        return result1058

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1059 = []
        cond1060 = self.match_lookahead_literal("(", 0)
        while cond1060:
            _t1852 = self.parse_instruction()
            item1061 = _t1852
            xs1059.append(item1061)
            cond1060 = self.match_lookahead_literal("(", 0)
        instructions1062 = xs1059
        self.consume_literal(")")
        return instructions1062

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1069 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1854 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1855 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1856 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1857 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1858 = 0
                            else:
                                _t1858 = -1
                            _t1857 = _t1858
                        _t1856 = _t1857
                    _t1855 = _t1856
                _t1854 = _t1855
            _t1853 = _t1854
        else:
            _t1853 = -1
        prediction1063 = _t1853
        if prediction1063 == 4:
            _t1860 = self.parse_monus_def()
            monus_def1068 = _t1860
            _t1861 = logic_pb2.Instruction(monus_def=monus_def1068)
            _t1859 = _t1861
        else:
            if prediction1063 == 3:
                _t1863 = self.parse_monoid_def()
                monoid_def1067 = _t1863
                _t1864 = logic_pb2.Instruction(monoid_def=monoid_def1067)
                _t1862 = _t1864
            else:
                if prediction1063 == 2:
                    _t1866 = self.parse_break()
                    break1066 = _t1866
                    _t1867 = logic_pb2.Instruction()
                    getattr(_t1867, 'break').CopyFrom(break1066)
                    _t1865 = _t1867
                else:
                    if prediction1063 == 1:
                        _t1869 = self.parse_upsert()
                        upsert1065 = _t1869
                        _t1870 = logic_pb2.Instruction(upsert=upsert1065)
                        _t1868 = _t1870
                    else:
                        if prediction1063 == 0:
                            _t1872 = self.parse_assign()
                            assign1064 = _t1872
                            _t1873 = logic_pb2.Instruction(assign=assign1064)
                            _t1871 = _t1873
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1868 = _t1871
                    _t1865 = _t1868
                _t1862 = _t1865
            _t1859 = _t1862
        result1070 = _t1859
        self.record_span(span_start1069, "Instruction")
        return result1070

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1074 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1874 = self.parse_relation_id()
        relation_id1071 = _t1874
        _t1875 = self.parse_abstraction()
        abstraction1072 = _t1875
        if self.match_lookahead_literal("(", 0):
            _t1877 = self.parse_attrs()
            _t1876 = _t1877
        else:
            _t1876 = None
        attrs1073 = _t1876
        self.consume_literal(")")
        _t1878 = logic_pb2.Assign(name=relation_id1071, body=abstraction1072, attrs=(attrs1073 if attrs1073 is not None else []))
        result1075 = _t1878
        self.record_span(span_start1074, "Assign")
        return result1075

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1079 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1879 = self.parse_relation_id()
        relation_id1076 = _t1879
        _t1880 = self.parse_abstraction_with_arity()
        abstraction_with_arity1077 = _t1880
        if self.match_lookahead_literal("(", 0):
            _t1882 = self.parse_attrs()
            _t1881 = _t1882
        else:
            _t1881 = None
        attrs1078 = _t1881
        self.consume_literal(")")
        _t1883 = logic_pb2.Upsert(name=relation_id1076, body=abstraction_with_arity1077[0], attrs=(attrs1078 if attrs1078 is not None else []), value_arity=abstraction_with_arity1077[1])
        result1080 = _t1883
        self.record_span(span_start1079, "Upsert")
        return result1080

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1884 = self.parse_bindings()
        bindings1081 = _t1884
        _t1885 = self.parse_formula()
        formula1082 = _t1885
        self.consume_literal(")")
        _t1886 = logic_pb2.Abstraction(vars=(list(bindings1081[0]) + list(bindings1081[1] if bindings1081[1] is not None else [])), value=formula1082)
        return (_t1886, len(bindings1081[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1086 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1887 = self.parse_relation_id()
        relation_id1083 = _t1887
        _t1888 = self.parse_abstraction()
        abstraction1084 = _t1888
        if self.match_lookahead_literal("(", 0):
            _t1890 = self.parse_attrs()
            _t1889 = _t1890
        else:
            _t1889 = None
        attrs1085 = _t1889
        self.consume_literal(")")
        _t1891 = logic_pb2.Break(name=relation_id1083, body=abstraction1084, attrs=(attrs1085 if attrs1085 is not None else []))
        result1087 = _t1891
        self.record_span(span_start1086, "Break")
        return result1087

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1092 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1892 = self.parse_monoid()
        monoid1088 = _t1892
        _t1893 = self.parse_relation_id()
        relation_id1089 = _t1893
        _t1894 = self.parse_abstraction_with_arity()
        abstraction_with_arity1090 = _t1894
        if self.match_lookahead_literal("(", 0):
            _t1896 = self.parse_attrs()
            _t1895 = _t1896
        else:
            _t1895 = None
        attrs1091 = _t1895
        self.consume_literal(")")
        _t1897 = logic_pb2.MonoidDef(monoid=monoid1088, name=relation_id1089, body=abstraction_with_arity1090[0], attrs=(attrs1091 if attrs1091 is not None else []), value_arity=abstraction_with_arity1090[1])
        result1093 = _t1897
        self.record_span(span_start1092, "MonoidDef")
        return result1093

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1099 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1899 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1900 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1901 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1902 = 2
                        else:
                            _t1902 = -1
                        _t1901 = _t1902
                    _t1900 = _t1901
                _t1899 = _t1900
            _t1898 = _t1899
        else:
            _t1898 = -1
        prediction1094 = _t1898
        if prediction1094 == 3:
            _t1904 = self.parse_sum_monoid()
            sum_monoid1098 = _t1904
            _t1905 = logic_pb2.Monoid(sum_monoid=sum_monoid1098)
            _t1903 = _t1905
        else:
            if prediction1094 == 2:
                _t1907 = self.parse_max_monoid()
                max_monoid1097 = _t1907
                _t1908 = logic_pb2.Monoid(max_monoid=max_monoid1097)
                _t1906 = _t1908
            else:
                if prediction1094 == 1:
                    _t1910 = self.parse_min_monoid()
                    min_monoid1096 = _t1910
                    _t1911 = logic_pb2.Monoid(min_monoid=min_monoid1096)
                    _t1909 = _t1911
                else:
                    if prediction1094 == 0:
                        _t1913 = self.parse_or_monoid()
                        or_monoid1095 = _t1913
                        _t1914 = logic_pb2.Monoid(or_monoid=or_monoid1095)
                        _t1912 = _t1914
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1909 = _t1912
                _t1906 = _t1909
            _t1903 = _t1906
        result1100 = _t1903
        self.record_span(span_start1099, "Monoid")
        return result1100

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1101 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1915 = logic_pb2.OrMonoid()
        result1102 = _t1915
        self.record_span(span_start1101, "OrMonoid")
        return result1102

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1104 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1916 = self.parse_type()
        type1103 = _t1916
        self.consume_literal(")")
        _t1917 = logic_pb2.MinMonoid(type=type1103)
        result1105 = _t1917
        self.record_span(span_start1104, "MinMonoid")
        return result1105

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1107 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1918 = self.parse_type()
        type1106 = _t1918
        self.consume_literal(")")
        _t1919 = logic_pb2.MaxMonoid(type=type1106)
        result1108 = _t1919
        self.record_span(span_start1107, "MaxMonoid")
        return result1108

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1110 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1920 = self.parse_type()
        type1109 = _t1920
        self.consume_literal(")")
        _t1921 = logic_pb2.SumMonoid(type=type1109)
        result1111 = _t1921
        self.record_span(span_start1110, "SumMonoid")
        return result1111

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1116 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1922 = self.parse_monoid()
        monoid1112 = _t1922
        _t1923 = self.parse_relation_id()
        relation_id1113 = _t1923
        _t1924 = self.parse_abstraction_with_arity()
        abstraction_with_arity1114 = _t1924
        if self.match_lookahead_literal("(", 0):
            _t1926 = self.parse_attrs()
            _t1925 = _t1926
        else:
            _t1925 = None
        attrs1115 = _t1925
        self.consume_literal(")")
        _t1927 = logic_pb2.MonusDef(monoid=monoid1112, name=relation_id1113, body=abstraction_with_arity1114[0], attrs=(attrs1115 if attrs1115 is not None else []), value_arity=abstraction_with_arity1114[1])
        result1117 = _t1927
        self.record_span(span_start1116, "MonusDef")
        return result1117

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1122 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1928 = self.parse_relation_id()
        relation_id1118 = _t1928
        _t1929 = self.parse_abstraction()
        abstraction1119 = _t1929
        _t1930 = self.parse_functional_dependency_keys()
        functional_dependency_keys1120 = _t1930
        _t1931 = self.parse_functional_dependency_values()
        functional_dependency_values1121 = _t1931
        self.consume_literal(")")
        _t1932 = logic_pb2.FunctionalDependency(guard=abstraction1119, keys=functional_dependency_keys1120, values=functional_dependency_values1121)
        _t1933 = logic_pb2.Constraint(name=relation_id1118, functional_dependency=_t1932)
        result1123 = _t1933
        self.record_span(span_start1122, "Constraint")
        return result1123

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1124 = []
        cond1125 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1125:
            _t1934 = self.parse_var()
            item1126 = _t1934
            xs1124.append(item1126)
            cond1125 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1127 = xs1124
        self.consume_literal(")")
        return vars1127

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1128 = []
        cond1129 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1129:
            _t1935 = self.parse_var()
            item1130 = _t1935
            xs1128.append(item1130)
            cond1129 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1131 = xs1128
        self.consume_literal(")")
        return vars1131

    def parse_data(self) -> logic_pb2.Data:
        span_start1137 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1937 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1938 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1939 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1940 = 1
                        else:
                            _t1940 = -1
                        _t1939 = _t1940
                    _t1938 = _t1939
                _t1937 = _t1938
            _t1936 = _t1937
        else:
            _t1936 = -1
        prediction1132 = _t1936
        if prediction1132 == 3:
            _t1942 = self.parse_iceberg_data()
            iceberg_data1136 = _t1942
            _t1943 = logic_pb2.Data(iceberg_data=iceberg_data1136)
            _t1941 = _t1943
        else:
            if prediction1132 == 2:
                _t1945 = self.parse_csv_data()
                csv_data1135 = _t1945
                _t1946 = logic_pb2.Data(csv_data=csv_data1135)
                _t1944 = _t1946
            else:
                if prediction1132 == 1:
                    _t1948 = self.parse_betree_relation()
                    betree_relation1134 = _t1948
                    _t1949 = logic_pb2.Data(betree_relation=betree_relation1134)
                    _t1947 = _t1949
                else:
                    if prediction1132 == 0:
                        _t1951 = self.parse_edb()
                        edb1133 = _t1951
                        _t1952 = logic_pb2.Data(edb=edb1133)
                        _t1950 = _t1952
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1947 = _t1950
                _t1944 = _t1947
            _t1941 = _t1944
        result1138 = _t1941
        self.record_span(span_start1137, "Data")
        return result1138

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1142 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1953 = self.parse_relation_id()
        relation_id1139 = _t1953
        _t1954 = self.parse_edb_path()
        edb_path1140 = _t1954
        _t1955 = self.parse_edb_types()
        edb_types1141 = _t1955
        self.consume_literal(")")
        _t1956 = logic_pb2.EDB(target_id=relation_id1139, path=edb_path1140, types=edb_types1141)
        result1143 = _t1956
        self.record_span(span_start1142, "EDB")
        return result1143

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1144 = []
        cond1145 = self.match_lookahead_terminal("STRING", 0)
        while cond1145:
            item1146 = self.consume_terminal("STRING")
            xs1144.append(item1146)
            cond1145 = self.match_lookahead_terminal("STRING", 0)
        strings1147 = xs1144
        self.consume_literal("]")
        return strings1147

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1148 = []
        cond1149 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1149:
            _t1957 = self.parse_type()
            item1150 = _t1957
            xs1148.append(item1150)
            cond1149 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1151 = xs1148
        self.consume_literal("]")
        return types1151

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1154 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1958 = self.parse_relation_id()
        relation_id1152 = _t1958
        _t1959 = self.parse_betree_info()
        betree_info1153 = _t1959
        self.consume_literal(")")
        _t1960 = logic_pb2.BeTreeRelation(name=relation_id1152, relation_info=betree_info1153)
        result1155 = _t1960
        self.record_span(span_start1154, "BeTreeRelation")
        return result1155

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1159 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1961 = self.parse_betree_info_key_types()
        betree_info_key_types1156 = _t1961
        _t1962 = self.parse_betree_info_value_types()
        betree_info_value_types1157 = _t1962
        _t1963 = self.parse_config_dict()
        config_dict1158 = _t1963
        self.consume_literal(")")
        _t1964 = self.construct_betree_info(betree_info_key_types1156, betree_info_value_types1157, config_dict1158)
        result1160 = _t1964
        self.record_span(span_start1159, "BeTreeInfo")
        return result1160

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1161 = []
        cond1162 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1162:
            _t1965 = self.parse_type()
            item1163 = _t1965
            xs1161.append(item1163)
            cond1162 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1164 = xs1161
        self.consume_literal(")")
        return types1164

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1165 = []
        cond1166 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1166:
            _t1966 = self.parse_type()
            item1167 = _t1966
            xs1165.append(item1167)
            cond1166 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1168 = xs1165
        self.consume_literal(")")
        return types1168

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1173 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1967 = self.parse_csvlocator()
        csvlocator1169 = _t1967
        _t1968 = self.parse_csv_config()
        csv_config1170 = _t1968
        _t1969 = self.parse_gnf_columns()
        gnf_columns1171 = _t1969
        _t1970 = self.parse_csv_asof()
        csv_asof1172 = _t1970
        self.consume_literal(")")
        _t1971 = logic_pb2.CSVData(locator=csvlocator1169, config=csv_config1170, columns=gnf_columns1171, asof=csv_asof1172)
        result1174 = _t1971
        self.record_span(span_start1173, "CSVData")
        return result1174

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1177 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1973 = self.parse_csv_locator_paths()
            _t1972 = _t1973
        else:
            _t1972 = None
        csv_locator_paths1175 = _t1972
        if self.match_lookahead_literal("(", 0):
            _t1975 = self.parse_csv_locator_inline_data()
            _t1974 = _t1975
        else:
            _t1974 = None
        csv_locator_inline_data1176 = _t1974
        self.consume_literal(")")
        _t1976 = logic_pb2.CSVLocator(paths=(csv_locator_paths1175 if csv_locator_paths1175 is not None else []), inline_data=(csv_locator_inline_data1176 if csv_locator_inline_data1176 is not None else "").encode())
        result1178 = _t1976
        self.record_span(span_start1177, "CSVLocator")
        return result1178

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1179 = []
        cond1180 = self.match_lookahead_terminal("STRING", 0)
        while cond1180:
            item1181 = self.consume_terminal("STRING")
            xs1179.append(item1181)
            cond1180 = self.match_lookahead_terminal("STRING", 0)
        strings1182 = xs1179
        self.consume_literal(")")
        return strings1182

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1183 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1183

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1185 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1977 = self.parse_config_dict()
        config_dict1184 = _t1977
        self.consume_literal(")")
        _t1978 = self.construct_csv_config(config_dict1184)
        result1186 = _t1978
        self.record_span(span_start1185, "CSVConfig")
        return result1186

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1187 = []
        cond1188 = self.match_lookahead_literal("(", 0)
        while cond1188:
            _t1979 = self.parse_gnf_column()
            item1189 = _t1979
            xs1187.append(item1189)
            cond1188 = self.match_lookahead_literal("(", 0)
        gnf_columns1190 = xs1187
        self.consume_literal(")")
        return gnf_columns1190

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1197 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1980 = self.parse_gnf_column_path()
        gnf_column_path1191 = _t1980
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1982 = self.parse_relation_id()
            _t1981 = _t1982
        else:
            _t1981 = None
        relation_id1192 = _t1981
        self.consume_literal("[")
        xs1193 = []
        cond1194 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1194:
            _t1983 = self.parse_type()
            item1195 = _t1983
            xs1193.append(item1195)
            cond1194 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1196 = xs1193
        self.consume_literal("]")
        self.consume_literal(")")
        _t1984 = logic_pb2.GNFColumn(column_path=gnf_column_path1191, target_id=relation_id1192, types=types1196)
        result1198 = _t1984
        self.record_span(span_start1197, "GNFColumn")
        return result1198

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1985 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1986 = 0
            else:
                _t1986 = -1
            _t1985 = _t1986
        prediction1199 = _t1985
        if prediction1199 == 1:
            self.consume_literal("[")
            xs1201 = []
            cond1202 = self.match_lookahead_terminal("STRING", 0)
            while cond1202:
                item1203 = self.consume_terminal("STRING")
                xs1201.append(item1203)
                cond1202 = self.match_lookahead_terminal("STRING", 0)
            strings1204 = xs1201
            self.consume_literal("]")
            _t1987 = strings1204
        else:
            if prediction1199 == 0:
                string1200 = self.consume_terminal("STRING")
                _t1988 = [string1200]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1987 = _t1988
        return _t1987

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1205 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1205

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1212 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1989 = self.parse_iceberg_locator()
        iceberg_locator1206 = _t1989
        _t1990 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1207 = _t1990
        _t1991 = self.parse_gnf_columns()
        gnf_columns1208 = _t1991
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t1993 = self.parse_iceberg_from_snapshot()
            _t1992 = _t1993
        else:
            _t1992 = None
        iceberg_from_snapshot1209 = _t1992
        if self.match_lookahead_literal("(", 0):
            _t1995 = self.parse_iceberg_to_snapshot()
            _t1994 = _t1995
        else:
            _t1994 = None
        iceberg_to_snapshot1210 = _t1994
        _t1996 = self.parse_boolean_value()
        boolean_value1211 = _t1996
        self.consume_literal(")")
        _t1997 = self.construct_iceberg_data(iceberg_locator1206, iceberg_catalog_config1207, gnf_columns1208, iceberg_from_snapshot1209, iceberg_to_snapshot1210, boolean_value1211)
        result1213 = _t1997
        self.record_span(span_start1212, "IcebergData")
        return result1213

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1217 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t1998 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1214 = _t1998
        _t1999 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1215 = _t1999
        _t2000 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1216 = _t2000
        self.consume_literal(")")
        _t2001 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1214, namespace=iceberg_locator_namespace1215, warehouse=iceberg_locator_warehouse1216)
        result1218 = _t2001
        self.record_span(span_start1217, "IcebergLocator")
        return result1218

    def parse_iceberg_locator_table_name(self) -> str:
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1219 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1219

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1220 = []
        cond1221 = self.match_lookahead_terminal("STRING", 0)
        while cond1221:
            item1222 = self.consume_terminal("STRING")
            xs1220.append(item1222)
            cond1221 = self.match_lookahead_terminal("STRING", 0)
        strings1223 = xs1220
        self.consume_literal(")")
        return strings1223

    def parse_iceberg_locator_warehouse(self) -> str:
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string1224 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1224

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1229 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t2002 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1225 = _t2002
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t2004 = self.parse_iceberg_catalog_config_scope()
            _t2003 = _t2004
        else:
            _t2003 = None
        iceberg_catalog_config_scope1226 = _t2003
        _t2005 = self.parse_iceberg_properties()
        iceberg_properties1227 = _t2005
        _t2006 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1228 = _t2006
        self.consume_literal(")")
        _t2007 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1225, iceberg_catalog_config_scope1226, iceberg_properties1227, iceberg_auth_properties1228)
        result1230 = _t2007
        self.record_span(span_start1229, "IcebergCatalogConfig")
        return result1230

    def parse_iceberg_catalog_uri(self) -> str:
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1231 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1231

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1232 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1232

    def parse_iceberg_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1233 = []
        cond1234 = self.match_lookahead_literal("(", 0)
        while cond1234:
            _t2008 = self.parse_iceberg_property_entry()
            item1235 = _t2008
            xs1233.append(item1235)
            cond1234 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1236 = xs1233
        self.consume_literal(")")
        return iceberg_property_entrys1236

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1237 = self.consume_terminal("STRING")
        string_31238 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1237, string_31238,)

    def parse_iceberg_auth_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1239 = []
        cond1240 = self.match_lookahead_literal("(", 0)
        while cond1240:
            _t2009 = self.parse_iceberg_masked_property_entry()
            item1241 = _t2009
            xs1239.append(item1241)
            cond1240 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1242 = xs1239
        self.consume_literal(")")
        return iceberg_masked_property_entrys1242

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1243 = self.consume_terminal("STRING")
        string_31244 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1243, string_31244,)

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1245 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1245

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1246 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1246

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1248 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2010 = self.parse_fragment_id()
        fragment_id1247 = _t2010
        self.consume_literal(")")
        _t2011 = transactions_pb2.Undefine(fragment_id=fragment_id1247)
        result1249 = _t2011
        self.record_span(span_start1248, "Undefine")
        return result1249

    def parse_context(self) -> transactions_pb2.Context:
        span_start1254 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1250 = []
        cond1251 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1251:
            _t2012 = self.parse_relation_id()
            item1252 = _t2012
            xs1250.append(item1252)
            cond1251 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1253 = xs1250
        self.consume_literal(")")
        _t2013 = transactions_pb2.Context(relations=relation_ids1253)
        result1255 = _t2013
        self.record_span(span_start1254, "Context")
        return result1255

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1261 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t2014 = self.parse_edb_path()
        edb_path1256 = _t2014
        xs1257 = []
        cond1258 = self.match_lookahead_literal("[", 0)
        while cond1258:
            _t2015 = self.parse_snapshot_mapping()
            item1259 = _t2015
            xs1257.append(item1259)
            cond1258 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1260 = xs1257
        self.consume_literal(")")
        _t2016 = transactions_pb2.Snapshot(prefix=edb_path1256, mappings=snapshot_mappings1260)
        result1262 = _t2016
        self.record_span(span_start1261, "Snapshot")
        return result1262

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1265 = self.span_start()
        _t2017 = self.parse_edb_path()
        edb_path1263 = _t2017
        _t2018 = self.parse_relation_id()
        relation_id1264 = _t2018
        _t2019 = transactions_pb2.SnapshotMapping(destination_path=edb_path1263, source_relation=relation_id1264)
        result1266 = _t2019
        self.record_span(span_start1265, "SnapshotMapping")
        return result1266

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1267 = []
        cond1268 = self.match_lookahead_literal("(", 0)
        while cond1268:
            _t2020 = self.parse_read()
            item1269 = _t2020
            xs1267.append(item1269)
            cond1268 = self.match_lookahead_literal("(", 0)
        reads1270 = xs1267
        self.consume_literal(")")
        return reads1270

    def parse_read(self) -> transactions_pb2.Read:
        span_start1277 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2022 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2023 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t2024 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t2025 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t2026 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t2027 = 3
                                else:
                                    _t2027 = -1
                                _t2026 = _t2027
                            _t2025 = _t2026
                        _t2024 = _t2025
                    _t2023 = _t2024
                _t2022 = _t2023
            _t2021 = _t2022
        else:
            _t2021 = -1
        prediction1271 = _t2021
        if prediction1271 == 4:
            _t2029 = self.parse_export()
            export1276 = _t2029
            _t2030 = transactions_pb2.Read(export=export1276)
            _t2028 = _t2030
        else:
            if prediction1271 == 3:
                _t2032 = self.parse_abort()
                abort1275 = _t2032
                _t2033 = transactions_pb2.Read(abort=abort1275)
                _t2031 = _t2033
            else:
                if prediction1271 == 2:
                    _t2035 = self.parse_what_if()
                    what_if1274 = _t2035
                    _t2036 = transactions_pb2.Read(what_if=what_if1274)
                    _t2034 = _t2036
                else:
                    if prediction1271 == 1:
                        _t2038 = self.parse_output()
                        output1273 = _t2038
                        _t2039 = transactions_pb2.Read(output=output1273)
                        _t2037 = _t2039
                    else:
                        if prediction1271 == 0:
                            _t2041 = self.parse_demand()
                            demand1272 = _t2041
                            _t2042 = transactions_pb2.Read(demand=demand1272)
                            _t2040 = _t2042
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2037 = _t2040
                    _t2034 = _t2037
                _t2031 = _t2034
            _t2028 = _t2031
        result1278 = _t2028
        self.record_span(span_start1277, "Read")
        return result1278

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1280 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2043 = self.parse_relation_id()
        relation_id1279 = _t2043
        self.consume_literal(")")
        _t2044 = transactions_pb2.Demand(relation_id=relation_id1279)
        result1281 = _t2044
        self.record_span(span_start1280, "Demand")
        return result1281

    def parse_output(self) -> transactions_pb2.Output:
        span_start1284 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2045 = self.parse_name()
        name1282 = _t2045
        _t2046 = self.parse_relation_id()
        relation_id1283 = _t2046
        self.consume_literal(")")
        _t2047 = transactions_pb2.Output(name=name1282, relation_id=relation_id1283)
        result1285 = _t2047
        self.record_span(span_start1284, "Output")
        return result1285

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1288 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2048 = self.parse_name()
        name1286 = _t2048
        _t2049 = self.parse_epoch()
        epoch1287 = _t2049
        self.consume_literal(")")
        _t2050 = transactions_pb2.WhatIf(branch=name1286, epoch=epoch1287)
        result1289 = _t2050
        self.record_span(span_start1288, "WhatIf")
        return result1289

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1292 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2052 = self.parse_name()
            _t2051 = _t2052
        else:
            _t2051 = None
        name1290 = _t2051
        _t2053 = self.parse_relation_id()
        relation_id1291 = _t2053
        self.consume_literal(")")
        _t2054 = transactions_pb2.Abort(name=(name1290 if name1290 is not None else "abort"), relation_id=relation_id1291)
        result1293 = _t2054
        self.record_span(span_start1292, "Abort")
        return result1293

    def parse_export(self) -> transactions_pb2.Export:
        span_start1297 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2056 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2057 = 0
                else:
                    _t2057 = -1
                _t2056 = _t2057
            _t2055 = _t2056
        else:
            _t2055 = -1
        prediction1294 = _t2055
        if prediction1294 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2059 = self.parse_export_iceberg_config()
            export_iceberg_config1296 = _t2059
            self.consume_literal(")")
            _t2060 = transactions_pb2.Export(iceberg_config=export_iceberg_config1296)
            _t2058 = _t2060
        else:
            if prediction1294 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2062 = self.parse_export_csv_config()
                export_csv_config1295 = _t2062
                self.consume_literal(")")
                _t2063 = transactions_pb2.Export(csv_config=export_csv_config1295)
                _t2061 = _t2063
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2058 = _t2061
        result1298 = _t2058
        self.record_span(span_start1297, "Export")
        return result1298

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1306 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2065 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2066 = 1
                else:
                    _t2066 = -1
                _t2065 = _t2066
            _t2064 = _t2065
        else:
            _t2064 = -1
        prediction1299 = _t2064
        if prediction1299 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2068 = self.parse_export_csv_path()
            export_csv_path1303 = _t2068
            _t2069 = self.parse_export_csv_columns_list()
            export_csv_columns_list1304 = _t2069
            _t2070 = self.parse_config_dict()
            config_dict1305 = _t2070
            self.consume_literal(")")
            _t2071 = self.construct_export_csv_config(export_csv_path1303, export_csv_columns_list1304, config_dict1305)
            _t2067 = _t2071
        else:
            if prediction1299 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2073 = self.parse_export_csv_path()
                export_csv_path1300 = _t2073
                _t2074 = self.parse_export_csv_source()
                export_csv_source1301 = _t2074
                _t2075 = self.parse_csv_config()
                csv_config1302 = _t2075
                self.consume_literal(")")
                _t2076 = self.construct_export_csv_config_with_source(export_csv_path1300, export_csv_source1301, csv_config1302)
                _t2072 = _t2076
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2067 = _t2072
        result1307 = _t2067
        self.record_span(span_start1306, "ExportCSVConfig")
        return result1307

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1308 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1308

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1315 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2078 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2079 = 0
                else:
                    _t2079 = -1
                _t2078 = _t2079
            _t2077 = _t2078
        else:
            _t2077 = -1
        prediction1309 = _t2077
        if prediction1309 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2081 = self.parse_relation_id()
            relation_id1314 = _t2081
            self.consume_literal(")")
            _t2082 = transactions_pb2.ExportCSVSource(table_def=relation_id1314)
            _t2080 = _t2082
        else:
            if prediction1309 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1310 = []
                cond1311 = self.match_lookahead_literal("(", 0)
                while cond1311:
                    _t2084 = self.parse_export_csv_column()
                    item1312 = _t2084
                    xs1310.append(item1312)
                    cond1311 = self.match_lookahead_literal("(", 0)
                export_csv_columns1313 = xs1310
                self.consume_literal(")")
                _t2085 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1313)
                _t2086 = transactions_pb2.ExportCSVSource(gnf_columns=_t2085)
                _t2083 = _t2086
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2080 = _t2083
        result1316 = _t2080
        self.record_span(span_start1315, "ExportCSVSource")
        return result1316

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1319 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1317 = self.consume_terminal("STRING")
        _t2087 = self.parse_relation_id()
        relation_id1318 = _t2087
        self.consume_literal(")")
        _t2088 = transactions_pb2.ExportCSVColumn(column_name=string1317, column_data=relation_id1318)
        result1320 = _t2088
        self.record_span(span_start1319, "ExportCSVColumn")
        return result1320

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1321 = []
        cond1322 = self.match_lookahead_literal("(", 0)
        while cond1322:
            _t2089 = self.parse_export_csv_column()
            item1323 = _t2089
            xs1321.append(item1323)
            cond1322 = self.match_lookahead_literal("(", 0)
        export_csv_columns1324 = xs1321
        self.consume_literal(")")
        return export_csv_columns1324

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1331 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2090 = self.parse_iceberg_locator()
        iceberg_locator1325 = _t2090
        _t2091 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1326 = _t2091
        _t2092 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1327 = _t2092
        _t2093 = self.parse_export_iceberg_columns()
        export_iceberg_columns1328 = _t2093
        _t2094 = self.parse_iceberg_table_properties()
        iceberg_table_properties1329 = _t2094
        if self.match_lookahead_literal("{", 0):
            _t2096 = self.parse_config_dict()
            _t2095 = _t2096
        else:
            _t2095 = None
        config_dict1330 = _t2095
        self.consume_literal(")")
        _t2097 = self.construct_export_iceberg_config_full(iceberg_locator1325, iceberg_catalog_config1326, export_iceberg_table_def1327, export_iceberg_columns1328, iceberg_table_properties1329, config_dict1330)
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

    def parse_export_iceberg_columns(self) -> Sequence[transactions_pb2.ExportColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1336 = []
        cond1337 = self.match_lookahead_literal("(", 0)
        while cond1337:
            _t2099 = self.parse_export_iceberg_column()
            item1338 = _t2099
            xs1336.append(item1338)
            cond1337 = self.match_lookahead_literal("(", 0)
        export_iceberg_columns1339 = xs1336
        self.consume_literal(")")
        return export_iceberg_columns1339

    def parse_export_iceberg_column(self) -> transactions_pb2.ExportColumn:
        span_start1342 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1340 = self.consume_terminal("STRING")
        _t2100 = self.parse_boolean_value()
        boolean_value1341 = _t2100
        self.consume_literal(")")
        _t2101 = transactions_pb2.ExportColumn(name=string1340, nullable=boolean_value1341)
        result1343 = _t2101
        self.record_span(span_start1342, "ExportColumn")
        return result1343

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1344 = []
        cond1345 = self.match_lookahead_literal("(", 0)
        while cond1345:
            _t2102 = self.parse_iceberg_property_entry()
            item1346 = _t2102
            xs1344.append(item1346)
            cond1345 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1347 = xs1344
        self.consume_literal(")")
        return iceberg_property_entrys1347


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
