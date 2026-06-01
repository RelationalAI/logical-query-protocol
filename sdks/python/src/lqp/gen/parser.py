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

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns_opt: Sequence[logic_pb2.GNFColumn] | None, target_opt: logic_pb2.IcebergTarget | None, from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2160 = logic_pb2.IcebergData(locator=locator, config=config, columns=(columns_opt if columns_opt is not None else []), target=target_opt, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2160

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2161 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2161
        _t2162 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2162
        _t2163 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2163
        table_props = dict(table_property_pairs)
        _t2164 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2164

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start679 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1347 = self.parse_configure()
            _t1346 = _t1347
        else:
            _t1346 = None
        configure673 = _t1346
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1349 = self.parse_sync()
            _t1348 = _t1349
        else:
            _t1348 = None
        sync674 = _t1348
        xs675 = []
        cond676 = self.match_lookahead_literal("(", 0)
        while cond676:
            _t1350 = self.parse_epoch()
            item677 = _t1350
            xs675.append(item677)
            cond676 = self.match_lookahead_literal("(", 0)
        epochs678 = xs675
        self.consume_literal(")")
        _t1351 = self.default_configure()
        _t1352 = transactions_pb2.Transaction(epochs=epochs678, configure=(configure673 if configure673 is not None else _t1351), sync=sync674)
        result680 = _t1352
        self.record_span(span_start679, "Transaction")
        return result680

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start682 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1353 = self.parse_config_dict()
        config_dict681 = _t1353
        self.consume_literal(")")
        _t1354 = self.construct_configure(config_dict681)
        result683 = _t1354
        self.record_span(span_start682, "Configure")
        return result683

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs684 = []
        cond685 = self.match_lookahead_literal(":", 0)
        while cond685:
            _t1355 = self.parse_config_key_value()
            item686 = _t1355
            xs684.append(item686)
            cond685 = self.match_lookahead_literal(":", 0)
        config_key_values687 = xs684
        self.consume_literal("}")
        return config_key_values687

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol688 = self.consume_terminal("SYMBOL")
        _t1356 = self.parse_raw_value()
        raw_value689 = _t1356
        return (symbol688, raw_value689,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start703 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1357 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1358 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1359 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1361 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1362 = 0
                            else:
                                _t1362 = -1
                            _t1361 = _t1362
                        _t1360 = _t1361
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1363 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1364 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1365 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1366 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1367 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1368 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1369 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1370 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1371 = 10
                                                        else:
                                                            _t1371 = -1
                                                        _t1370 = _t1371
                                                    _t1369 = _t1370
                                                _t1368 = _t1369
                                            _t1367 = _t1368
                                        _t1366 = _t1367
                                    _t1365 = _t1366
                                _t1364 = _t1365
                            _t1363 = _t1364
                        _t1360 = _t1363
                    _t1359 = _t1360
                _t1358 = _t1359
            _t1357 = _t1358
        prediction690 = _t1357
        if prediction690 == 12:
            _t1373 = self.parse_boolean_value()
            boolean_value702 = _t1373
            _t1374 = logic_pb2.Value(boolean_value=boolean_value702)
            _t1372 = _t1374
        else:
            if prediction690 == 11:
                self.consume_literal("missing")
                _t1376 = logic_pb2.MissingValue()
                _t1377 = logic_pb2.Value(missing_value=_t1376)
                _t1375 = _t1377
            else:
                if prediction690 == 10:
                    decimal701 = self.consume_terminal("DECIMAL")
                    _t1379 = logic_pb2.Value(decimal_value=decimal701)
                    _t1378 = _t1379
                else:
                    if prediction690 == 9:
                        int128700 = self.consume_terminal("INT128")
                        _t1381 = logic_pb2.Value(int128_value=int128700)
                        _t1380 = _t1381
                    else:
                        if prediction690 == 8:
                            uint128699 = self.consume_terminal("UINT128")
                            _t1383 = logic_pb2.Value(uint128_value=uint128699)
                            _t1382 = _t1383
                        else:
                            if prediction690 == 7:
                                uint32698 = self.consume_terminal("UINT32")
                                _t1385 = logic_pb2.Value(uint32_value=uint32698)
                                _t1384 = _t1385
                            else:
                                if prediction690 == 6:
                                    float697 = self.consume_terminal("FLOAT")
                                    _t1387 = logic_pb2.Value(float_value=float697)
                                    _t1386 = _t1387
                                else:
                                    if prediction690 == 5:
                                        float32696 = self.consume_terminal("FLOAT32")
                                        _t1389 = logic_pb2.Value(float32_value=float32696)
                                        _t1388 = _t1389
                                    else:
                                        if prediction690 == 4:
                                            int695 = self.consume_terminal("INT")
                                            _t1391 = logic_pb2.Value(int_value=int695)
                                            _t1390 = _t1391
                                        else:
                                            if prediction690 == 3:
                                                int32694 = self.consume_terminal("INT32")
                                                _t1393 = logic_pb2.Value(int32_value=int32694)
                                                _t1392 = _t1393
                                            else:
                                                if prediction690 == 2:
                                                    string693 = self.consume_terminal("STRING")
                                                    _t1395 = logic_pb2.Value(string_value=string693)
                                                    _t1394 = _t1395
                                                else:
                                                    if prediction690 == 1:
                                                        _t1397 = self.parse_raw_datetime()
                                                        raw_datetime692 = _t1397
                                                        _t1398 = logic_pb2.Value(datetime_value=raw_datetime692)
                                                        _t1396 = _t1398
                                                    else:
                                                        if prediction690 == 0:
                                                            _t1400 = self.parse_raw_date()
                                                            raw_date691 = _t1400
                                                            _t1401 = logic_pb2.Value(date_value=raw_date691)
                                                            _t1399 = _t1401
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1396 = _t1399
                                                    _t1394 = _t1396
                                                _t1392 = _t1394
                                            _t1390 = _t1392
                                        _t1388 = _t1390
                                    _t1386 = _t1388
                                _t1384 = _t1386
                            _t1382 = _t1384
                        _t1380 = _t1382
                    _t1378 = _t1380
                _t1375 = _t1378
            _t1372 = _t1375
        result704 = _t1372
        self.record_span(span_start703, "Value")
        return result704

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start708 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int705 = self.consume_terminal("INT")
        int_3706 = self.consume_terminal("INT")
        int_4707 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1402 = logic_pb2.DateValue(year=int(int705), month=int(int_3706), day=int(int_4707))
        result709 = _t1402
        self.record_span(span_start708, "DateValue")
        return result709

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start717 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int710 = self.consume_terminal("INT")
        int_3711 = self.consume_terminal("INT")
        int_4712 = self.consume_terminal("INT")
        int_5713 = self.consume_terminal("INT")
        int_6714 = self.consume_terminal("INT")
        int_7715 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1403 = self.consume_terminal("INT")
        else:
            _t1403 = None
        int_8716 = _t1403
        self.consume_literal(")")
        _t1404 = logic_pb2.DateTimeValue(year=int(int710), month=int(int_3711), day=int(int_4712), hour=int(int_5713), minute=int(int_6714), second=int(int_7715), microsecond=int((int_8716 if int_8716 is not None else 0)))
        result718 = _t1404
        self.record_span(span_start717, "DateTimeValue")
        return result718

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1405 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1406 = 1
            else:
                _t1406 = -1
            _t1405 = _t1406
        prediction719 = _t1405
        if prediction719 == 1:
            self.consume_literal("false")
            _t1407 = False
        else:
            if prediction719 == 0:
                self.consume_literal("true")
                _t1408 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1407 = _t1408
        return _t1407

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start724 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs720 = []
        cond721 = self.match_lookahead_literal(":", 0)
        while cond721:
            _t1409 = self.parse_fragment_id()
            item722 = _t1409
            xs720.append(item722)
            cond721 = self.match_lookahead_literal(":", 0)
        fragment_ids723 = xs720
        self.consume_literal(")")
        _t1410 = transactions_pb2.Sync(fragments=fragment_ids723)
        result725 = _t1410
        self.record_span(span_start724, "Sync")
        return result725

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start727 = self.span_start()
        self.consume_literal(":")
        symbol726 = self.consume_terminal("SYMBOL")
        result728 = fragments_pb2.FragmentId(id=symbol726.encode())
        self.record_span(span_start727, "FragmentId")
        return result728

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start731 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1412 = self.parse_epoch_writes()
            _t1411 = _t1412
        else:
            _t1411 = None
        epoch_writes729 = _t1411
        if self.match_lookahead_literal("(", 0):
            _t1414 = self.parse_epoch_reads()
            _t1413 = _t1414
        else:
            _t1413 = None
        epoch_reads730 = _t1413
        self.consume_literal(")")
        _t1415 = transactions_pb2.Epoch(writes=(epoch_writes729 if epoch_writes729 is not None else []), reads=(epoch_reads730 if epoch_reads730 is not None else []))
        result732 = _t1415
        self.record_span(span_start731, "Epoch")
        return result732

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs733 = []
        cond734 = self.match_lookahead_literal("(", 0)
        while cond734:
            _t1416 = self.parse_write()
            item735 = _t1416
            xs733.append(item735)
            cond734 = self.match_lookahead_literal("(", 0)
        writes736 = xs733
        self.consume_literal(")")
        return writes736

    def parse_write(self) -> transactions_pb2.Write:
        span_start742 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1418 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1419 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1420 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1421 = 2
                        else:
                            _t1421 = -1
                        _t1420 = _t1421
                    _t1419 = _t1420
                _t1418 = _t1419
            _t1417 = _t1418
        else:
            _t1417 = -1
        prediction737 = _t1417
        if prediction737 == 3:
            _t1423 = self.parse_snapshot()
            snapshot741 = _t1423
            _t1424 = transactions_pb2.Write(snapshot=snapshot741)
            _t1422 = _t1424
        else:
            if prediction737 == 2:
                _t1426 = self.parse_context()
                context740 = _t1426
                _t1427 = transactions_pb2.Write(context=context740)
                _t1425 = _t1427
            else:
                if prediction737 == 1:
                    _t1429 = self.parse_undefine()
                    undefine739 = _t1429
                    _t1430 = transactions_pb2.Write(undefine=undefine739)
                    _t1428 = _t1430
                else:
                    if prediction737 == 0:
                        _t1432 = self.parse_define()
                        define738 = _t1432
                        _t1433 = transactions_pb2.Write(define=define738)
                        _t1431 = _t1433
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1428 = _t1431
                _t1425 = _t1428
            _t1422 = _t1425
        result743 = _t1422
        self.record_span(span_start742, "Write")
        return result743

    def parse_define(self) -> transactions_pb2.Define:
        span_start745 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1434 = self.parse_fragment()
        fragment744 = _t1434
        self.consume_literal(")")
        _t1435 = transactions_pb2.Define(fragment=fragment744)
        result746 = _t1435
        self.record_span(span_start745, "Define")
        return result746

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start752 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1436 = self.parse_new_fragment_id()
        new_fragment_id747 = _t1436
        xs748 = []
        cond749 = self.match_lookahead_literal("(", 0)
        while cond749:
            _t1437 = self.parse_declaration()
            item750 = _t1437
            xs748.append(item750)
            cond749 = self.match_lookahead_literal("(", 0)
        declarations751 = xs748
        self.consume_literal(")")
        result753 = self.construct_fragment(new_fragment_id747, declarations751)
        self.record_span(span_start752, "Fragment")
        return result753

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start755 = self.span_start()
        _t1438 = self.parse_fragment_id()
        fragment_id754 = _t1438
        self.start_fragment(fragment_id754)
        result756 = fragment_id754
        self.record_span(span_start755, "FragmentId")
        return result756

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start762 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1440 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1441 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1442 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1443 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1444 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1445 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1446 = 1
                                    else:
                                        _t1446 = -1
                                    _t1445 = _t1446
                                _t1444 = _t1445
                            _t1443 = _t1444
                        _t1442 = _t1443
                    _t1441 = _t1442
                _t1440 = _t1441
            _t1439 = _t1440
        else:
            _t1439 = -1
        prediction757 = _t1439
        if prediction757 == 3:
            _t1448 = self.parse_data()
            data761 = _t1448
            _t1449 = logic_pb2.Declaration(data=data761)
            _t1447 = _t1449
        else:
            if prediction757 == 2:
                _t1451 = self.parse_constraint()
                constraint760 = _t1451
                _t1452 = logic_pb2.Declaration(constraint=constraint760)
                _t1450 = _t1452
            else:
                if prediction757 == 1:
                    _t1454 = self.parse_algorithm()
                    algorithm759 = _t1454
                    _t1455 = logic_pb2.Declaration(algorithm=algorithm759)
                    _t1453 = _t1455
                else:
                    if prediction757 == 0:
                        _t1457 = self.parse_def()
                        def758 = _t1457
                        _t1458 = logic_pb2.Declaration()
                        getattr(_t1458, 'def').CopyFrom(def758)
                        _t1456 = _t1458
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1453 = _t1456
                _t1450 = _t1453
            _t1447 = _t1450
        result763 = _t1447
        self.record_span(span_start762, "Declaration")
        return result763

    def parse_def(self) -> logic_pb2.Def:
        span_start767 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1459 = self.parse_relation_id()
        relation_id764 = _t1459
        _t1460 = self.parse_abstraction()
        abstraction765 = _t1460
        if self.match_lookahead_literal("(", 0):
            _t1462 = self.parse_attrs()
            _t1461 = _t1462
        else:
            _t1461 = None
        attrs766 = _t1461
        self.consume_literal(")")
        _t1463 = logic_pb2.Def(name=relation_id764, body=abstraction765, attrs=(attrs766 if attrs766 is not None else []))
        result768 = _t1463
        self.record_span(span_start767, "Def")
        return result768

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start772 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1464 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1465 = 1
            else:
                _t1465 = -1
            _t1464 = _t1465
        prediction769 = _t1464
        if prediction769 == 1:
            uint128771 = self.consume_terminal("UINT128")
            _t1466 = logic_pb2.RelationId(id_low=uint128771.low, id_high=uint128771.high)
        else:
            if prediction769 == 0:
                self.consume_literal(":")
                symbol770 = self.consume_terminal("SYMBOL")
                _t1467 = self.relation_id_from_string(symbol770)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1466 = _t1467
        result773 = _t1466
        self.record_span(span_start772, "RelationId")
        return result773

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start776 = self.span_start()
        self.consume_literal("(")
        _t1468 = self.parse_bindings()
        bindings774 = _t1468
        _t1469 = self.parse_formula()
        formula775 = _t1469
        self.consume_literal(")")
        _t1470 = logic_pb2.Abstraction(vars=(list(bindings774[0]) + list(bindings774[1] if bindings774[1] is not None else [])), value=formula775)
        result777 = _t1470
        self.record_span(span_start776, "Abstraction")
        return result777

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs778 = []
        cond779 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond779:
            _t1471 = self.parse_binding()
            item780 = _t1471
            xs778.append(item780)
            cond779 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings781 = xs778
        if self.match_lookahead_literal("|", 0):
            _t1473 = self.parse_value_bindings()
            _t1472 = _t1473
        else:
            _t1472 = None
        value_bindings782 = _t1472
        self.consume_literal("]")
        return (bindings781, (value_bindings782 if value_bindings782 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start785 = self.span_start()
        symbol783 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1474 = self.parse_type()
        type784 = _t1474
        _t1475 = logic_pb2.Var(name=symbol783)
        _t1476 = logic_pb2.Binding(var=_t1475, type=type784)
        result786 = _t1476
        self.record_span(span_start785, "Binding")
        return result786

    def parse_type(self) -> logic_pb2.Type:
        span_start802 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1477 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1478 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1479 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1480 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1481 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1482 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1483 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1484 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1485 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1486 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1487 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1488 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1489 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1490 = 9
                                                            else:
                                                                _t1490 = -1
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
                _t1478 = _t1479
            _t1477 = _t1478
        prediction787 = _t1477
        if prediction787 == 13:
            _t1492 = self.parse_uint32_type()
            uint32_type801 = _t1492
            _t1493 = logic_pb2.Type(uint32_type=uint32_type801)
            _t1491 = _t1493
        else:
            if prediction787 == 12:
                _t1495 = self.parse_float32_type()
                float32_type800 = _t1495
                _t1496 = logic_pb2.Type(float32_type=float32_type800)
                _t1494 = _t1496
            else:
                if prediction787 == 11:
                    _t1498 = self.parse_int32_type()
                    int32_type799 = _t1498
                    _t1499 = logic_pb2.Type(int32_type=int32_type799)
                    _t1497 = _t1499
                else:
                    if prediction787 == 10:
                        _t1501 = self.parse_boolean_type()
                        boolean_type798 = _t1501
                        _t1502 = logic_pb2.Type(boolean_type=boolean_type798)
                        _t1500 = _t1502
                    else:
                        if prediction787 == 9:
                            _t1504 = self.parse_decimal_type()
                            decimal_type797 = _t1504
                            _t1505 = logic_pb2.Type(decimal_type=decimal_type797)
                            _t1503 = _t1505
                        else:
                            if prediction787 == 8:
                                _t1507 = self.parse_missing_type()
                                missing_type796 = _t1507
                                _t1508 = logic_pb2.Type(missing_type=missing_type796)
                                _t1506 = _t1508
                            else:
                                if prediction787 == 7:
                                    _t1510 = self.parse_datetime_type()
                                    datetime_type795 = _t1510
                                    _t1511 = logic_pb2.Type(datetime_type=datetime_type795)
                                    _t1509 = _t1511
                                else:
                                    if prediction787 == 6:
                                        _t1513 = self.parse_date_type()
                                        date_type794 = _t1513
                                        _t1514 = logic_pb2.Type(date_type=date_type794)
                                        _t1512 = _t1514
                                    else:
                                        if prediction787 == 5:
                                            _t1516 = self.parse_int128_type()
                                            int128_type793 = _t1516
                                            _t1517 = logic_pb2.Type(int128_type=int128_type793)
                                            _t1515 = _t1517
                                        else:
                                            if prediction787 == 4:
                                                _t1519 = self.parse_uint128_type()
                                                uint128_type792 = _t1519
                                                _t1520 = logic_pb2.Type(uint128_type=uint128_type792)
                                                _t1518 = _t1520
                                            else:
                                                if prediction787 == 3:
                                                    _t1522 = self.parse_float_type()
                                                    float_type791 = _t1522
                                                    _t1523 = logic_pb2.Type(float_type=float_type791)
                                                    _t1521 = _t1523
                                                else:
                                                    if prediction787 == 2:
                                                        _t1525 = self.parse_int_type()
                                                        int_type790 = _t1525
                                                        _t1526 = logic_pb2.Type(int_type=int_type790)
                                                        _t1524 = _t1526
                                                    else:
                                                        if prediction787 == 1:
                                                            _t1528 = self.parse_string_type()
                                                            string_type789 = _t1528
                                                            _t1529 = logic_pb2.Type(string_type=string_type789)
                                                            _t1527 = _t1529
                                                        else:
                                                            if prediction787 == 0:
                                                                _t1531 = self.parse_unspecified_type()
                                                                unspecified_type788 = _t1531
                                                                _t1532 = logic_pb2.Type(unspecified_type=unspecified_type788)
                                                                _t1530 = _t1532
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1494 = _t1497
            _t1491 = _t1494
        result803 = _t1491
        self.record_span(span_start802, "Type")
        return result803

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start804 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1533 = logic_pb2.UnspecifiedType()
        result805 = _t1533
        self.record_span(span_start804, "UnspecifiedType")
        return result805

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start806 = self.span_start()
        self.consume_literal("STRING")
        _t1534 = logic_pb2.StringType()
        result807 = _t1534
        self.record_span(span_start806, "StringType")
        return result807

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start808 = self.span_start()
        self.consume_literal("INT")
        _t1535 = logic_pb2.IntType()
        result809 = _t1535
        self.record_span(span_start808, "IntType")
        return result809

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start810 = self.span_start()
        self.consume_literal("FLOAT")
        _t1536 = logic_pb2.FloatType()
        result811 = _t1536
        self.record_span(span_start810, "FloatType")
        return result811

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start812 = self.span_start()
        self.consume_literal("UINT128")
        _t1537 = logic_pb2.UInt128Type()
        result813 = _t1537
        self.record_span(span_start812, "UInt128Type")
        return result813

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start814 = self.span_start()
        self.consume_literal("INT128")
        _t1538 = logic_pb2.Int128Type()
        result815 = _t1538
        self.record_span(span_start814, "Int128Type")
        return result815

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start816 = self.span_start()
        self.consume_literal("DATE")
        _t1539 = logic_pb2.DateType()
        result817 = _t1539
        self.record_span(span_start816, "DateType")
        return result817

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start818 = self.span_start()
        self.consume_literal("DATETIME")
        _t1540 = logic_pb2.DateTimeType()
        result819 = _t1540
        self.record_span(span_start818, "DateTimeType")
        return result819

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start820 = self.span_start()
        self.consume_literal("MISSING")
        _t1541 = logic_pb2.MissingType()
        result821 = _t1541
        self.record_span(span_start820, "MissingType")
        return result821

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start824 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int822 = self.consume_terminal("INT")
        int_3823 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1542 = logic_pb2.DecimalType(precision=int(int822), scale=int(int_3823))
        result825 = _t1542
        self.record_span(span_start824, "DecimalType")
        return result825

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start826 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1543 = logic_pb2.BooleanType()
        result827 = _t1543
        self.record_span(span_start826, "BooleanType")
        return result827

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start828 = self.span_start()
        self.consume_literal("INT32")
        _t1544 = logic_pb2.Int32Type()
        result829 = _t1544
        self.record_span(span_start828, "Int32Type")
        return result829

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start830 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1545 = logic_pb2.Float32Type()
        result831 = _t1545
        self.record_span(span_start830, "Float32Type")
        return result831

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start832 = self.span_start()
        self.consume_literal("UINT32")
        _t1546 = logic_pb2.UInt32Type()
        result833 = _t1546
        self.record_span(span_start832, "UInt32Type")
        return result833

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs834 = []
        cond835 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond835:
            _t1547 = self.parse_binding()
            item836 = _t1547
            xs834.append(item836)
            cond835 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings837 = xs834
        return bindings837

    def parse_formula(self) -> logic_pb2.Formula:
        span_start852 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1549 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1550 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1551 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1552 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1553 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1554 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1555 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1556 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1557 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1558 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1559 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1560 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1561 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1562 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1563 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1564 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1565 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1566 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1567 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1568 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1569 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1570 = 10
                                                                                                else:
                                                                                                    _t1570 = -1
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
                _t1549 = _t1550
            _t1548 = _t1549
        else:
            _t1548 = -1
        prediction838 = _t1548
        if prediction838 == 12:
            _t1572 = self.parse_cast()
            cast851 = _t1572
            _t1573 = logic_pb2.Formula(cast=cast851)
            _t1571 = _t1573
        else:
            if prediction838 == 11:
                _t1575 = self.parse_rel_atom()
                rel_atom850 = _t1575
                _t1576 = logic_pb2.Formula(rel_atom=rel_atom850)
                _t1574 = _t1576
            else:
                if prediction838 == 10:
                    _t1578 = self.parse_primitive()
                    primitive849 = _t1578
                    _t1579 = logic_pb2.Formula(primitive=primitive849)
                    _t1577 = _t1579
                else:
                    if prediction838 == 9:
                        _t1581 = self.parse_pragma()
                        pragma848 = _t1581
                        _t1582 = logic_pb2.Formula(pragma=pragma848)
                        _t1580 = _t1582
                    else:
                        if prediction838 == 8:
                            _t1584 = self.parse_atom()
                            atom847 = _t1584
                            _t1585 = logic_pb2.Formula(atom=atom847)
                            _t1583 = _t1585
                        else:
                            if prediction838 == 7:
                                _t1587 = self.parse_ffi()
                                ffi846 = _t1587
                                _t1588 = logic_pb2.Formula(ffi=ffi846)
                                _t1586 = _t1588
                            else:
                                if prediction838 == 6:
                                    _t1590 = self.parse_not()
                                    not845 = _t1590
                                    _t1591 = logic_pb2.Formula()
                                    getattr(_t1591, 'not').CopyFrom(not845)
                                    _t1589 = _t1591
                                else:
                                    if prediction838 == 5:
                                        _t1593 = self.parse_disjunction()
                                        disjunction844 = _t1593
                                        _t1594 = logic_pb2.Formula(disjunction=disjunction844)
                                        _t1592 = _t1594
                                    else:
                                        if prediction838 == 4:
                                            _t1596 = self.parse_conjunction()
                                            conjunction843 = _t1596
                                            _t1597 = logic_pb2.Formula(conjunction=conjunction843)
                                            _t1595 = _t1597
                                        else:
                                            if prediction838 == 3:
                                                _t1599 = self.parse_reduce()
                                                reduce842 = _t1599
                                                _t1600 = logic_pb2.Formula(reduce=reduce842)
                                                _t1598 = _t1600
                                            else:
                                                if prediction838 == 2:
                                                    _t1602 = self.parse_exists()
                                                    exists841 = _t1602
                                                    _t1603 = logic_pb2.Formula(exists=exists841)
                                                    _t1601 = _t1603
                                                else:
                                                    if prediction838 == 1:
                                                        _t1605 = self.parse_false()
                                                        false840 = _t1605
                                                        _t1606 = logic_pb2.Formula(disjunction=false840)
                                                        _t1604 = _t1606
                                                    else:
                                                        if prediction838 == 0:
                                                            _t1608 = self.parse_true()
                                                            true839 = _t1608
                                                            _t1609 = logic_pb2.Formula(conjunction=true839)
                                                            _t1607 = _t1609
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1574 = _t1577
            _t1571 = _t1574
        result853 = _t1571
        self.record_span(span_start852, "Formula")
        return result853

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start854 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1610 = logic_pb2.Conjunction(args=[])
        result855 = _t1610
        self.record_span(span_start854, "Conjunction")
        return result855

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start856 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1611 = logic_pb2.Disjunction(args=[])
        result857 = _t1611
        self.record_span(span_start856, "Disjunction")
        return result857

    def parse_exists(self) -> logic_pb2.Exists:
        span_start860 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1612 = self.parse_bindings()
        bindings858 = _t1612
        _t1613 = self.parse_formula()
        formula859 = _t1613
        self.consume_literal(")")
        _t1614 = logic_pb2.Abstraction(vars=(list(bindings858[0]) + list(bindings858[1] if bindings858[1] is not None else [])), value=formula859)
        _t1615 = logic_pb2.Exists(body=_t1614)
        result861 = _t1615
        self.record_span(span_start860, "Exists")
        return result861

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start865 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1616 = self.parse_abstraction()
        abstraction862 = _t1616
        _t1617 = self.parse_abstraction()
        abstraction_3863 = _t1617
        _t1618 = self.parse_terms()
        terms864 = _t1618
        self.consume_literal(")")
        _t1619 = logic_pb2.Reduce(op=abstraction862, body=abstraction_3863, terms=terms864)
        result866 = _t1619
        self.record_span(span_start865, "Reduce")
        return result866

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs867 = []
        cond868 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond868:
            _t1620 = self.parse_term()
            item869 = _t1620
            xs867.append(item869)
            cond868 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms870 = xs867
        self.consume_literal(")")
        return terms870

    def parse_term(self) -> logic_pb2.Term:
        span_start874 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1621 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1622 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1623 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1624 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1625 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1626 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1627 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1628 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1629 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1630 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1631 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1632 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1633 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1634 = 1
                                                            else:
                                                                _t1634 = -1
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
        prediction871 = _t1621
        if prediction871 == 1:
            _t1636 = self.parse_value()
            value873 = _t1636
            _t1637 = logic_pb2.Term(constant=value873)
            _t1635 = _t1637
        else:
            if prediction871 == 0:
                _t1639 = self.parse_var()
                var872 = _t1639
                _t1640 = logic_pb2.Term(var=var872)
                _t1638 = _t1640
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1635 = _t1638
        result875 = _t1635
        self.record_span(span_start874, "Term")
        return result875

    def parse_var(self) -> logic_pb2.Var:
        span_start877 = self.span_start()
        symbol876 = self.consume_terminal("SYMBOL")
        _t1641 = logic_pb2.Var(name=symbol876)
        result878 = _t1641
        self.record_span(span_start877, "Var")
        return result878

    def parse_value(self) -> logic_pb2.Value:
        span_start892 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1642 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1643 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1644 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1646 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1647 = 0
                            else:
                                _t1647 = -1
                            _t1646 = _t1647
                        _t1645 = _t1646
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1648 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1649 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1650 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1651 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1652 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1653 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1654 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1655 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1656 = 10
                                                        else:
                                                            _t1656 = -1
                                                        _t1655 = _t1656
                                                    _t1654 = _t1655
                                                _t1653 = _t1654
                                            _t1652 = _t1653
                                        _t1651 = _t1652
                                    _t1650 = _t1651
                                _t1649 = _t1650
                            _t1648 = _t1649
                        _t1645 = _t1648
                    _t1644 = _t1645
                _t1643 = _t1644
            _t1642 = _t1643
        prediction879 = _t1642
        if prediction879 == 12:
            _t1658 = self.parse_boolean_value()
            boolean_value891 = _t1658
            _t1659 = logic_pb2.Value(boolean_value=boolean_value891)
            _t1657 = _t1659
        else:
            if prediction879 == 11:
                self.consume_literal("missing")
                _t1661 = logic_pb2.MissingValue()
                _t1662 = logic_pb2.Value(missing_value=_t1661)
                _t1660 = _t1662
            else:
                if prediction879 == 10:
                    formatted_decimal890 = self.consume_terminal("DECIMAL")
                    _t1664 = logic_pb2.Value(decimal_value=formatted_decimal890)
                    _t1663 = _t1664
                else:
                    if prediction879 == 9:
                        formatted_int128889 = self.consume_terminal("INT128")
                        _t1666 = logic_pb2.Value(int128_value=formatted_int128889)
                        _t1665 = _t1666
                    else:
                        if prediction879 == 8:
                            formatted_uint128888 = self.consume_terminal("UINT128")
                            _t1668 = logic_pb2.Value(uint128_value=formatted_uint128888)
                            _t1667 = _t1668
                        else:
                            if prediction879 == 7:
                                formatted_uint32887 = self.consume_terminal("UINT32")
                                _t1670 = logic_pb2.Value(uint32_value=formatted_uint32887)
                                _t1669 = _t1670
                            else:
                                if prediction879 == 6:
                                    formatted_float886 = self.consume_terminal("FLOAT")
                                    _t1672 = logic_pb2.Value(float_value=formatted_float886)
                                    _t1671 = _t1672
                                else:
                                    if prediction879 == 5:
                                        formatted_float32885 = self.consume_terminal("FLOAT32")
                                        _t1674 = logic_pb2.Value(float32_value=formatted_float32885)
                                        _t1673 = _t1674
                                    else:
                                        if prediction879 == 4:
                                            formatted_int884 = self.consume_terminal("INT")
                                            _t1676 = logic_pb2.Value(int_value=formatted_int884)
                                            _t1675 = _t1676
                                        else:
                                            if prediction879 == 3:
                                                formatted_int32883 = self.consume_terminal("INT32")
                                                _t1678 = logic_pb2.Value(int32_value=formatted_int32883)
                                                _t1677 = _t1678
                                            else:
                                                if prediction879 == 2:
                                                    formatted_string882 = self.consume_terminal("STRING")
                                                    _t1680 = logic_pb2.Value(string_value=formatted_string882)
                                                    _t1679 = _t1680
                                                else:
                                                    if prediction879 == 1:
                                                        _t1682 = self.parse_datetime()
                                                        datetime881 = _t1682
                                                        _t1683 = logic_pb2.Value(datetime_value=datetime881)
                                                        _t1681 = _t1683
                                                    else:
                                                        if prediction879 == 0:
                                                            _t1685 = self.parse_date()
                                                            date880 = _t1685
                                                            _t1686 = logic_pb2.Value(date_value=date880)
                                                            _t1684 = _t1686
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1681 = _t1684
                                                    _t1679 = _t1681
                                                _t1677 = _t1679
                                            _t1675 = _t1677
                                        _t1673 = _t1675
                                    _t1671 = _t1673
                                _t1669 = _t1671
                            _t1667 = _t1669
                        _t1665 = _t1667
                    _t1663 = _t1665
                _t1660 = _t1663
            _t1657 = _t1660
        result893 = _t1657
        self.record_span(span_start892, "Value")
        return result893

    def parse_date(self) -> logic_pb2.DateValue:
        span_start897 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int894 = self.consume_terminal("INT")
        formatted_int_3895 = self.consume_terminal("INT")
        formatted_int_4896 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1687 = logic_pb2.DateValue(year=int(formatted_int894), month=int(formatted_int_3895), day=int(formatted_int_4896))
        result898 = _t1687
        self.record_span(span_start897, "DateValue")
        return result898

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start906 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int899 = self.consume_terminal("INT")
        formatted_int_3900 = self.consume_terminal("INT")
        formatted_int_4901 = self.consume_terminal("INT")
        formatted_int_5902 = self.consume_terminal("INT")
        formatted_int_6903 = self.consume_terminal("INT")
        formatted_int_7904 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1688 = self.consume_terminal("INT")
        else:
            _t1688 = None
        formatted_int_8905 = _t1688
        self.consume_literal(")")
        _t1689 = logic_pb2.DateTimeValue(year=int(formatted_int899), month=int(formatted_int_3900), day=int(formatted_int_4901), hour=int(formatted_int_5902), minute=int(formatted_int_6903), second=int(formatted_int_7904), microsecond=int((formatted_int_8905 if formatted_int_8905 is not None else 0)))
        result907 = _t1689
        self.record_span(span_start906, "DateTimeValue")
        return result907

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start912 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs908 = []
        cond909 = self.match_lookahead_literal("(", 0)
        while cond909:
            _t1690 = self.parse_formula()
            item910 = _t1690
            xs908.append(item910)
            cond909 = self.match_lookahead_literal("(", 0)
        formulas911 = xs908
        self.consume_literal(")")
        _t1691 = logic_pb2.Conjunction(args=formulas911)
        result913 = _t1691
        self.record_span(span_start912, "Conjunction")
        return result913

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start918 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs914 = []
        cond915 = self.match_lookahead_literal("(", 0)
        while cond915:
            _t1692 = self.parse_formula()
            item916 = _t1692
            xs914.append(item916)
            cond915 = self.match_lookahead_literal("(", 0)
        formulas917 = xs914
        self.consume_literal(")")
        _t1693 = logic_pb2.Disjunction(args=formulas917)
        result919 = _t1693
        self.record_span(span_start918, "Disjunction")
        return result919

    def parse_not(self) -> logic_pb2.Not:
        span_start921 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1694 = self.parse_formula()
        formula920 = _t1694
        self.consume_literal(")")
        _t1695 = logic_pb2.Not(arg=formula920)
        result922 = _t1695
        self.record_span(span_start921, "Not")
        return result922

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start926 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1696 = self.parse_name()
        name923 = _t1696
        _t1697 = self.parse_ffi_args()
        ffi_args924 = _t1697
        _t1698 = self.parse_terms()
        terms925 = _t1698
        self.consume_literal(")")
        _t1699 = logic_pb2.FFI(name=name923, args=ffi_args924, terms=terms925)
        result927 = _t1699
        self.record_span(span_start926, "FFI")
        return result927

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol928 = self.consume_terminal("SYMBOL")
        return symbol928

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs929 = []
        cond930 = self.match_lookahead_literal("(", 0)
        while cond930:
            _t1700 = self.parse_abstraction()
            item931 = _t1700
            xs929.append(item931)
            cond930 = self.match_lookahead_literal("(", 0)
        abstractions932 = xs929
        self.consume_literal(")")
        return abstractions932

    def parse_atom(self) -> logic_pb2.Atom:
        span_start938 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1701 = self.parse_relation_id()
        relation_id933 = _t1701
        xs934 = []
        cond935 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond935:
            _t1702 = self.parse_term()
            item936 = _t1702
            xs934.append(item936)
            cond935 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms937 = xs934
        self.consume_literal(")")
        _t1703 = logic_pb2.Atom(name=relation_id933, terms=terms937)
        result939 = _t1703
        self.record_span(span_start938, "Atom")
        return result939

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start945 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1704 = self.parse_name()
        name940 = _t1704
        xs941 = []
        cond942 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond942:
            _t1705 = self.parse_term()
            item943 = _t1705
            xs941.append(item943)
            cond942 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms944 = xs941
        self.consume_literal(")")
        _t1706 = logic_pb2.Pragma(name=name940, terms=terms944)
        result946 = _t1706
        self.record_span(span_start945, "Pragma")
        return result946

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start962 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1708 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1709 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1710 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1711 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1712 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1713 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1714 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1715 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1716 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1717 = 7
                                                else:
                                                    _t1717 = -1
                                                _t1716 = _t1717
                                            _t1715 = _t1716
                                        _t1714 = _t1715
                                    _t1713 = _t1714
                                _t1712 = _t1713
                            _t1711 = _t1712
                        _t1710 = _t1711
                    _t1709 = _t1710
                _t1708 = _t1709
            _t1707 = _t1708
        else:
            _t1707 = -1
        prediction947 = _t1707
        if prediction947 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1719 = self.parse_name()
            name957 = _t1719
            xs958 = []
            cond959 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond959:
                _t1720 = self.parse_rel_term()
                item960 = _t1720
                xs958.append(item960)
                cond959 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms961 = xs958
            self.consume_literal(")")
            _t1721 = logic_pb2.Primitive(name=name957, terms=rel_terms961)
            _t1718 = _t1721
        else:
            if prediction947 == 8:
                _t1723 = self.parse_divide()
                divide956 = _t1723
                _t1722 = divide956
            else:
                if prediction947 == 7:
                    _t1725 = self.parse_multiply()
                    multiply955 = _t1725
                    _t1724 = multiply955
                else:
                    if prediction947 == 6:
                        _t1727 = self.parse_minus()
                        minus954 = _t1727
                        _t1726 = minus954
                    else:
                        if prediction947 == 5:
                            _t1729 = self.parse_add()
                            add953 = _t1729
                            _t1728 = add953
                        else:
                            if prediction947 == 4:
                                _t1731 = self.parse_gt_eq()
                                gt_eq952 = _t1731
                                _t1730 = gt_eq952
                            else:
                                if prediction947 == 3:
                                    _t1733 = self.parse_gt()
                                    gt951 = _t1733
                                    _t1732 = gt951
                                else:
                                    if prediction947 == 2:
                                        _t1735 = self.parse_lt_eq()
                                        lt_eq950 = _t1735
                                        _t1734 = lt_eq950
                                    else:
                                        if prediction947 == 1:
                                            _t1737 = self.parse_lt()
                                            lt949 = _t1737
                                            _t1736 = lt949
                                        else:
                                            if prediction947 == 0:
                                                _t1739 = self.parse_eq()
                                                eq948 = _t1739
                                                _t1738 = eq948
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1736 = _t1738
                                        _t1734 = _t1736
                                    _t1732 = _t1734
                                _t1730 = _t1732
                            _t1728 = _t1730
                        _t1726 = _t1728
                    _t1724 = _t1726
                _t1722 = _t1724
            _t1718 = _t1722
        result963 = _t1718
        self.record_span(span_start962, "Primitive")
        return result963

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start966 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1740 = self.parse_term()
        term964 = _t1740
        _t1741 = self.parse_term()
        term_3965 = _t1741
        self.consume_literal(")")
        _t1742 = logic_pb2.RelTerm(term=term964)
        _t1743 = logic_pb2.RelTerm(term=term_3965)
        _t1744 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1742, _t1743])
        result967 = _t1744
        self.record_span(span_start966, "Primitive")
        return result967

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start970 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1745 = self.parse_term()
        term968 = _t1745
        _t1746 = self.parse_term()
        term_3969 = _t1746
        self.consume_literal(")")
        _t1747 = logic_pb2.RelTerm(term=term968)
        _t1748 = logic_pb2.RelTerm(term=term_3969)
        _t1749 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1747, _t1748])
        result971 = _t1749
        self.record_span(span_start970, "Primitive")
        return result971

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start974 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1750 = self.parse_term()
        term972 = _t1750
        _t1751 = self.parse_term()
        term_3973 = _t1751
        self.consume_literal(")")
        _t1752 = logic_pb2.RelTerm(term=term972)
        _t1753 = logic_pb2.RelTerm(term=term_3973)
        _t1754 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1752, _t1753])
        result975 = _t1754
        self.record_span(span_start974, "Primitive")
        return result975

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start978 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1755 = self.parse_term()
        term976 = _t1755
        _t1756 = self.parse_term()
        term_3977 = _t1756
        self.consume_literal(")")
        _t1757 = logic_pb2.RelTerm(term=term976)
        _t1758 = logic_pb2.RelTerm(term=term_3977)
        _t1759 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1757, _t1758])
        result979 = _t1759
        self.record_span(span_start978, "Primitive")
        return result979

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start982 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1760 = self.parse_term()
        term980 = _t1760
        _t1761 = self.parse_term()
        term_3981 = _t1761
        self.consume_literal(")")
        _t1762 = logic_pb2.RelTerm(term=term980)
        _t1763 = logic_pb2.RelTerm(term=term_3981)
        _t1764 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1762, _t1763])
        result983 = _t1764
        self.record_span(span_start982, "Primitive")
        return result983

    def parse_add(self) -> logic_pb2.Primitive:
        span_start987 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1765 = self.parse_term()
        term984 = _t1765
        _t1766 = self.parse_term()
        term_3985 = _t1766
        _t1767 = self.parse_term()
        term_4986 = _t1767
        self.consume_literal(")")
        _t1768 = logic_pb2.RelTerm(term=term984)
        _t1769 = logic_pb2.RelTerm(term=term_3985)
        _t1770 = logic_pb2.RelTerm(term=term_4986)
        _t1771 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1768, _t1769, _t1770])
        result988 = _t1771
        self.record_span(span_start987, "Primitive")
        return result988

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start992 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1772 = self.parse_term()
        term989 = _t1772
        _t1773 = self.parse_term()
        term_3990 = _t1773
        _t1774 = self.parse_term()
        term_4991 = _t1774
        self.consume_literal(")")
        _t1775 = logic_pb2.RelTerm(term=term989)
        _t1776 = logic_pb2.RelTerm(term=term_3990)
        _t1777 = logic_pb2.RelTerm(term=term_4991)
        _t1778 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1775, _t1776, _t1777])
        result993 = _t1778
        self.record_span(span_start992, "Primitive")
        return result993

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start997 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1779 = self.parse_term()
        term994 = _t1779
        _t1780 = self.parse_term()
        term_3995 = _t1780
        _t1781 = self.parse_term()
        term_4996 = _t1781
        self.consume_literal(")")
        _t1782 = logic_pb2.RelTerm(term=term994)
        _t1783 = logic_pb2.RelTerm(term=term_3995)
        _t1784 = logic_pb2.RelTerm(term=term_4996)
        _t1785 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1782, _t1783, _t1784])
        result998 = _t1785
        self.record_span(span_start997, "Primitive")
        return result998

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start1002 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1786 = self.parse_term()
        term999 = _t1786
        _t1787 = self.parse_term()
        term_31000 = _t1787
        _t1788 = self.parse_term()
        term_41001 = _t1788
        self.consume_literal(")")
        _t1789 = logic_pb2.RelTerm(term=term999)
        _t1790 = logic_pb2.RelTerm(term=term_31000)
        _t1791 = logic_pb2.RelTerm(term=term_41001)
        _t1792 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1789, _t1790, _t1791])
        result1003 = _t1792
        self.record_span(span_start1002, "Primitive")
        return result1003

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1007 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1793 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1794 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1795 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1796 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1797 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1798 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1799 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1800 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1801 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1802 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1803 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1804 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1805 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1806 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1807 = 1
                                                                else:
                                                                    _t1807 = -1
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
                _t1794 = _t1795
            _t1793 = _t1794
        prediction1004 = _t1793
        if prediction1004 == 1:
            _t1809 = self.parse_term()
            term1006 = _t1809
            _t1810 = logic_pb2.RelTerm(term=term1006)
            _t1808 = _t1810
        else:
            if prediction1004 == 0:
                _t1812 = self.parse_specialized_value()
                specialized_value1005 = _t1812
                _t1813 = logic_pb2.RelTerm(specialized_value=specialized_value1005)
                _t1811 = _t1813
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1808 = _t1811
        result1008 = _t1808
        self.record_span(span_start1007, "RelTerm")
        return result1008

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1010 = self.span_start()
        self.consume_literal("#")
        _t1814 = self.parse_raw_value()
        raw_value1009 = _t1814
        result1011 = raw_value1009
        self.record_span(span_start1010, "Value")
        return result1011

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1017 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1815 = self.parse_name()
        name1012 = _t1815
        xs1013 = []
        cond1014 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1014:
            _t1816 = self.parse_rel_term()
            item1015 = _t1816
            xs1013.append(item1015)
            cond1014 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1016 = xs1013
        self.consume_literal(")")
        _t1817 = logic_pb2.RelAtom(name=name1012, terms=rel_terms1016)
        result1018 = _t1817
        self.record_span(span_start1017, "RelAtom")
        return result1018

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1021 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1818 = self.parse_term()
        term1019 = _t1818
        _t1819 = self.parse_term()
        term_31020 = _t1819
        self.consume_literal(")")
        _t1820 = logic_pb2.Cast(input=term1019, result=term_31020)
        result1022 = _t1820
        self.record_span(span_start1021, "Cast")
        return result1022

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1023 = []
        cond1024 = self.match_lookahead_literal("(", 0)
        while cond1024:
            _t1821 = self.parse_attribute()
            item1025 = _t1821
            xs1023.append(item1025)
            cond1024 = self.match_lookahead_literal("(", 0)
        attributes1026 = xs1023
        self.consume_literal(")")
        return attributes1026

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1032 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1822 = self.parse_name()
        name1027 = _t1822
        xs1028 = []
        cond1029 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1029:
            _t1823 = self.parse_raw_value()
            item1030 = _t1823
            xs1028.append(item1030)
            cond1029 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1031 = xs1028
        self.consume_literal(")")
        _t1824 = logic_pb2.Attribute(name=name1027, args=raw_values1031)
        result1033 = _t1824
        self.record_span(span_start1032, "Attribute")
        return result1033

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1040 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1034 = []
        cond1035 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1035:
            _t1825 = self.parse_relation_id()
            item1036 = _t1825
            xs1034.append(item1036)
            cond1035 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1037 = xs1034
        _t1826 = self.parse_script()
        script1038 = _t1826
        if self.match_lookahead_literal("(", 0):
            _t1828 = self.parse_attrs()
            _t1827 = _t1828
        else:
            _t1827 = None
        attrs1039 = _t1827
        self.consume_literal(")")
        _t1829 = logic_pb2.Algorithm(body=script1038, attrs=(attrs1039 if attrs1039 is not None else []))
        getattr(_t1829, 'global').extend(relation_ids1037)
        result1041 = _t1829
        self.record_span(span_start1040, "Algorithm")
        return result1041

    def parse_script(self) -> logic_pb2.Script:
        span_start1046 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1042 = []
        cond1043 = self.match_lookahead_literal("(", 0)
        while cond1043:
            _t1830 = self.parse_construct()
            item1044 = _t1830
            xs1042.append(item1044)
            cond1043 = self.match_lookahead_literal("(", 0)
        constructs1045 = xs1042
        self.consume_literal(")")
        _t1831 = logic_pb2.Script(constructs=constructs1045)
        result1047 = _t1831
        self.record_span(span_start1046, "Script")
        return result1047

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1051 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1833 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1834 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1835 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1836 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1837 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1838 = 1
                                else:
                                    _t1838 = -1
                                _t1837 = _t1838
                            _t1836 = _t1837
                        _t1835 = _t1836
                    _t1834 = _t1835
                _t1833 = _t1834
            _t1832 = _t1833
        else:
            _t1832 = -1
        prediction1048 = _t1832
        if prediction1048 == 1:
            _t1840 = self.parse_instruction()
            instruction1050 = _t1840
            _t1841 = logic_pb2.Construct(instruction=instruction1050)
            _t1839 = _t1841
        else:
            if prediction1048 == 0:
                _t1843 = self.parse_loop()
                loop1049 = _t1843
                _t1844 = logic_pb2.Construct(loop=loop1049)
                _t1842 = _t1844
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1839 = _t1842
        result1052 = _t1839
        self.record_span(span_start1051, "Construct")
        return result1052

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1056 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1845 = self.parse_init()
        init1053 = _t1845
        _t1846 = self.parse_script()
        script1054 = _t1846
        if self.match_lookahead_literal("(", 0):
            _t1848 = self.parse_attrs()
            _t1847 = _t1848
        else:
            _t1847 = None
        attrs1055 = _t1847
        self.consume_literal(")")
        _t1849 = logic_pb2.Loop(init=init1053, body=script1054, attrs=(attrs1055 if attrs1055 is not None else []))
        result1057 = _t1849
        self.record_span(span_start1056, "Loop")
        return result1057

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1058 = []
        cond1059 = self.match_lookahead_literal("(", 0)
        while cond1059:
            _t1850 = self.parse_instruction()
            item1060 = _t1850
            xs1058.append(item1060)
            cond1059 = self.match_lookahead_literal("(", 0)
        instructions1061 = xs1058
        self.consume_literal(")")
        return instructions1061

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1068 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1852 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1853 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1854 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1855 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1856 = 0
                            else:
                                _t1856 = -1
                            _t1855 = _t1856
                        _t1854 = _t1855
                    _t1853 = _t1854
                _t1852 = _t1853
            _t1851 = _t1852
        else:
            _t1851 = -1
        prediction1062 = _t1851
        if prediction1062 == 4:
            _t1858 = self.parse_monus_def()
            monus_def1067 = _t1858
            _t1859 = logic_pb2.Instruction(monus_def=monus_def1067)
            _t1857 = _t1859
        else:
            if prediction1062 == 3:
                _t1861 = self.parse_monoid_def()
                monoid_def1066 = _t1861
                _t1862 = logic_pb2.Instruction(monoid_def=monoid_def1066)
                _t1860 = _t1862
            else:
                if prediction1062 == 2:
                    _t1864 = self.parse_break()
                    break1065 = _t1864
                    _t1865 = logic_pb2.Instruction()
                    getattr(_t1865, 'break').CopyFrom(break1065)
                    _t1863 = _t1865
                else:
                    if prediction1062 == 1:
                        _t1867 = self.parse_upsert()
                        upsert1064 = _t1867
                        _t1868 = logic_pb2.Instruction(upsert=upsert1064)
                        _t1866 = _t1868
                    else:
                        if prediction1062 == 0:
                            _t1870 = self.parse_assign()
                            assign1063 = _t1870
                            _t1871 = logic_pb2.Instruction(assign=assign1063)
                            _t1869 = _t1871
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1866 = _t1869
                    _t1863 = _t1866
                _t1860 = _t1863
            _t1857 = _t1860
        result1069 = _t1857
        self.record_span(span_start1068, "Instruction")
        return result1069

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1073 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1872 = self.parse_relation_id()
        relation_id1070 = _t1872
        _t1873 = self.parse_abstraction()
        abstraction1071 = _t1873
        if self.match_lookahead_literal("(", 0):
            _t1875 = self.parse_attrs()
            _t1874 = _t1875
        else:
            _t1874 = None
        attrs1072 = _t1874
        self.consume_literal(")")
        _t1876 = logic_pb2.Assign(name=relation_id1070, body=abstraction1071, attrs=(attrs1072 if attrs1072 is not None else []))
        result1074 = _t1876
        self.record_span(span_start1073, "Assign")
        return result1074

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1078 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1877 = self.parse_relation_id()
        relation_id1075 = _t1877
        _t1878 = self.parse_abstraction_with_arity()
        abstraction_with_arity1076 = _t1878
        if self.match_lookahead_literal("(", 0):
            _t1880 = self.parse_attrs()
            _t1879 = _t1880
        else:
            _t1879 = None
        attrs1077 = _t1879
        self.consume_literal(")")
        _t1881 = logic_pb2.Upsert(name=relation_id1075, body=abstraction_with_arity1076[0], attrs=(attrs1077 if attrs1077 is not None else []), value_arity=abstraction_with_arity1076[1])
        result1079 = _t1881
        self.record_span(span_start1078, "Upsert")
        return result1079

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1882 = self.parse_bindings()
        bindings1080 = _t1882
        _t1883 = self.parse_formula()
        formula1081 = _t1883
        self.consume_literal(")")
        _t1884 = logic_pb2.Abstraction(vars=(list(bindings1080[0]) + list(bindings1080[1] if bindings1080[1] is not None else [])), value=formula1081)
        return (_t1884, len(bindings1080[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1085 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1885 = self.parse_relation_id()
        relation_id1082 = _t1885
        _t1886 = self.parse_abstraction()
        abstraction1083 = _t1886
        if self.match_lookahead_literal("(", 0):
            _t1888 = self.parse_attrs()
            _t1887 = _t1888
        else:
            _t1887 = None
        attrs1084 = _t1887
        self.consume_literal(")")
        _t1889 = logic_pb2.Break(name=relation_id1082, body=abstraction1083, attrs=(attrs1084 if attrs1084 is not None else []))
        result1086 = _t1889
        self.record_span(span_start1085, "Break")
        return result1086

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1091 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1890 = self.parse_monoid()
        monoid1087 = _t1890
        _t1891 = self.parse_relation_id()
        relation_id1088 = _t1891
        _t1892 = self.parse_abstraction_with_arity()
        abstraction_with_arity1089 = _t1892
        if self.match_lookahead_literal("(", 0):
            _t1894 = self.parse_attrs()
            _t1893 = _t1894
        else:
            _t1893 = None
        attrs1090 = _t1893
        self.consume_literal(")")
        _t1895 = logic_pb2.MonoidDef(monoid=monoid1087, name=relation_id1088, body=abstraction_with_arity1089[0], attrs=(attrs1090 if attrs1090 is not None else []), value_arity=abstraction_with_arity1089[1])
        result1092 = _t1895
        self.record_span(span_start1091, "MonoidDef")
        return result1092

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1098 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1897 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1898 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1899 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1900 = 2
                        else:
                            _t1900 = -1
                        _t1899 = _t1900
                    _t1898 = _t1899
                _t1897 = _t1898
            _t1896 = _t1897
        else:
            _t1896 = -1
        prediction1093 = _t1896
        if prediction1093 == 3:
            _t1902 = self.parse_sum_monoid()
            sum_monoid1097 = _t1902
            _t1903 = logic_pb2.Monoid(sum_monoid=sum_monoid1097)
            _t1901 = _t1903
        else:
            if prediction1093 == 2:
                _t1905 = self.parse_max_monoid()
                max_monoid1096 = _t1905
                _t1906 = logic_pb2.Monoid(max_monoid=max_monoid1096)
                _t1904 = _t1906
            else:
                if prediction1093 == 1:
                    _t1908 = self.parse_min_monoid()
                    min_monoid1095 = _t1908
                    _t1909 = logic_pb2.Monoid(min_monoid=min_monoid1095)
                    _t1907 = _t1909
                else:
                    if prediction1093 == 0:
                        _t1911 = self.parse_or_monoid()
                        or_monoid1094 = _t1911
                        _t1912 = logic_pb2.Monoid(or_monoid=or_monoid1094)
                        _t1910 = _t1912
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1907 = _t1910
                _t1904 = _t1907
            _t1901 = _t1904
        result1099 = _t1901
        self.record_span(span_start1098, "Monoid")
        return result1099

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1100 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1913 = logic_pb2.OrMonoid()
        result1101 = _t1913
        self.record_span(span_start1100, "OrMonoid")
        return result1101

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1103 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1914 = self.parse_type()
        type1102 = _t1914
        self.consume_literal(")")
        _t1915 = logic_pb2.MinMonoid(type=type1102)
        result1104 = _t1915
        self.record_span(span_start1103, "MinMonoid")
        return result1104

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1106 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1916 = self.parse_type()
        type1105 = _t1916
        self.consume_literal(")")
        _t1917 = logic_pb2.MaxMonoid(type=type1105)
        result1107 = _t1917
        self.record_span(span_start1106, "MaxMonoid")
        return result1107

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1109 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1918 = self.parse_type()
        type1108 = _t1918
        self.consume_literal(")")
        _t1919 = logic_pb2.SumMonoid(type=type1108)
        result1110 = _t1919
        self.record_span(span_start1109, "SumMonoid")
        return result1110

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1115 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1920 = self.parse_monoid()
        monoid1111 = _t1920
        _t1921 = self.parse_relation_id()
        relation_id1112 = _t1921
        _t1922 = self.parse_abstraction_with_arity()
        abstraction_with_arity1113 = _t1922
        if self.match_lookahead_literal("(", 0):
            _t1924 = self.parse_attrs()
            _t1923 = _t1924
        else:
            _t1923 = None
        attrs1114 = _t1923
        self.consume_literal(")")
        _t1925 = logic_pb2.MonusDef(monoid=monoid1111, name=relation_id1112, body=abstraction_with_arity1113[0], attrs=(attrs1114 if attrs1114 is not None else []), value_arity=abstraction_with_arity1113[1])
        result1116 = _t1925
        self.record_span(span_start1115, "MonusDef")
        return result1116

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1121 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1926 = self.parse_relation_id()
        relation_id1117 = _t1926
        _t1927 = self.parse_abstraction()
        abstraction1118 = _t1927
        _t1928 = self.parse_functional_dependency_keys()
        functional_dependency_keys1119 = _t1928
        _t1929 = self.parse_functional_dependency_values()
        functional_dependency_values1120 = _t1929
        self.consume_literal(")")
        _t1930 = logic_pb2.FunctionalDependency(guard=abstraction1118, keys=functional_dependency_keys1119, values=functional_dependency_values1120)
        _t1931 = logic_pb2.Constraint(name=relation_id1117, functional_dependency=_t1930)
        result1122 = _t1931
        self.record_span(span_start1121, "Constraint")
        return result1122

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1123 = []
        cond1124 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1124:
            _t1932 = self.parse_var()
            item1125 = _t1932
            xs1123.append(item1125)
            cond1124 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1126 = xs1123
        self.consume_literal(")")
        return vars1126

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1127 = []
        cond1128 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1128:
            _t1933 = self.parse_var()
            item1129 = _t1933
            xs1127.append(item1129)
            cond1128 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1130 = xs1127
        self.consume_literal(")")
        return vars1130

    def parse_data(self) -> logic_pb2.Data:
        span_start1136 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1935 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1936 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1937 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1938 = 1
                        else:
                            _t1938 = -1
                        _t1937 = _t1938
                    _t1936 = _t1937
                _t1935 = _t1936
            _t1934 = _t1935
        else:
            _t1934 = -1
        prediction1131 = _t1934
        if prediction1131 == 3:
            _t1940 = self.parse_iceberg_data()
            iceberg_data1135 = _t1940
            _t1941 = logic_pb2.Data(iceberg_data=iceberg_data1135)
            _t1939 = _t1941
        else:
            if prediction1131 == 2:
                _t1943 = self.parse_csv_data()
                csv_data1134 = _t1943
                _t1944 = logic_pb2.Data(csv_data=csv_data1134)
                _t1942 = _t1944
            else:
                if prediction1131 == 1:
                    _t1946 = self.parse_betree_relation()
                    betree_relation1133 = _t1946
                    _t1947 = logic_pb2.Data(betree_relation=betree_relation1133)
                    _t1945 = _t1947
                else:
                    if prediction1131 == 0:
                        _t1949 = self.parse_edb()
                        edb1132 = _t1949
                        _t1950 = logic_pb2.Data(edb=edb1132)
                        _t1948 = _t1950
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1945 = _t1948
                _t1942 = _t1945
            _t1939 = _t1942
        result1137 = _t1939
        self.record_span(span_start1136, "Data")
        return result1137

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1141 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1951 = self.parse_relation_id()
        relation_id1138 = _t1951
        _t1952 = self.parse_edb_path()
        edb_path1139 = _t1952
        _t1953 = self.parse_edb_types()
        edb_types1140 = _t1953
        self.consume_literal(")")
        _t1954 = logic_pb2.EDB(target_id=relation_id1138, path=edb_path1139, types=edb_types1140)
        result1142 = _t1954
        self.record_span(span_start1141, "EDB")
        return result1142

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1143 = []
        cond1144 = self.match_lookahead_terminal("STRING", 0)
        while cond1144:
            item1145 = self.consume_terminal("STRING")
            xs1143.append(item1145)
            cond1144 = self.match_lookahead_terminal("STRING", 0)
        strings1146 = xs1143
        self.consume_literal("]")
        return strings1146

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1147 = []
        cond1148 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1148:
            _t1955 = self.parse_type()
            item1149 = _t1955
            xs1147.append(item1149)
            cond1148 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1150 = xs1147
        self.consume_literal("]")
        return types1150

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1153 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1956 = self.parse_relation_id()
        relation_id1151 = _t1956
        _t1957 = self.parse_betree_info()
        betree_info1152 = _t1957
        self.consume_literal(")")
        _t1958 = logic_pb2.BeTreeRelation(name=relation_id1151, relation_info=betree_info1152)
        result1154 = _t1958
        self.record_span(span_start1153, "BeTreeRelation")
        return result1154

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1158 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1959 = self.parse_betree_info_key_types()
        betree_info_key_types1155 = _t1959
        _t1960 = self.parse_betree_info_value_types()
        betree_info_value_types1156 = _t1960
        _t1961 = self.parse_config_dict()
        config_dict1157 = _t1961
        self.consume_literal(")")
        _t1962 = self.construct_betree_info(betree_info_key_types1155, betree_info_value_types1156, config_dict1157)
        result1159 = _t1962
        self.record_span(span_start1158, "BeTreeInfo")
        return result1159

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1160 = []
        cond1161 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1161:
            _t1963 = self.parse_type()
            item1162 = _t1963
            xs1160.append(item1162)
            cond1161 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1163 = xs1160
        self.consume_literal(")")
        return types1163

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1164 = []
        cond1165 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1165:
            _t1964 = self.parse_type()
            item1166 = _t1964
            xs1164.append(item1166)
            cond1165 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1167 = xs1164
        self.consume_literal(")")
        return types1167

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1172 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1965 = self.parse_csvlocator()
        csvlocator1168 = _t1965
        _t1966 = self.parse_csv_config()
        csv_config1169 = _t1966
        _t1967 = self.parse_gnf_columns()
        gnf_columns1170 = _t1967
        _t1968 = self.parse_csv_asof()
        csv_asof1171 = _t1968
        self.consume_literal(")")
        _t1969 = logic_pb2.CSVData(locator=csvlocator1168, config=csv_config1169, columns=gnf_columns1170, asof=csv_asof1171)
        result1173 = _t1969
        self.record_span(span_start1172, "CSVData")
        return result1173

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1176 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1971 = self.parse_csv_locator_paths()
            _t1970 = _t1971
        else:
            _t1970 = None
        csv_locator_paths1174 = _t1970
        if self.match_lookahead_literal("(", 0):
            _t1973 = self.parse_csv_locator_inline_data()
            _t1972 = _t1973
        else:
            _t1972 = None
        csv_locator_inline_data1175 = _t1972
        self.consume_literal(")")
        _t1974 = logic_pb2.CSVLocator(paths=(csv_locator_paths1174 if csv_locator_paths1174 is not None else []), inline_data=(csv_locator_inline_data1175 if csv_locator_inline_data1175 is not None else "").encode())
        result1177 = _t1974
        self.record_span(span_start1176, "CSVLocator")
        return result1177

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1178 = []
        cond1179 = self.match_lookahead_terminal("STRING", 0)
        while cond1179:
            item1180 = self.consume_terminal("STRING")
            xs1178.append(item1180)
            cond1179 = self.match_lookahead_terminal("STRING", 0)
        strings1181 = xs1178
        self.consume_literal(")")
        return strings1181

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1182 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1182

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1184 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1975 = self.parse_config_dict()
        config_dict1183 = _t1975
        self.consume_literal(")")
        _t1976 = self.construct_csv_config(config_dict1183)
        result1185 = _t1976
        self.record_span(span_start1184, "CSVConfig")
        return result1185

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1186 = []
        cond1187 = self.match_lookahead_literal("(", 0)
        while cond1187:
            _t1977 = self.parse_gnf_column()
            item1188 = _t1977
            xs1186.append(item1188)
            cond1187 = self.match_lookahead_literal("(", 0)
        gnf_columns1189 = xs1186
        self.consume_literal(")")
        return gnf_columns1189

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1196 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1978 = self.parse_gnf_column_path()
        gnf_column_path1190 = _t1978
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1980 = self.parse_relation_id()
            _t1979 = _t1980
        else:
            _t1979 = None
        relation_id1191 = _t1979
        self.consume_literal("[")
        xs1192 = []
        cond1193 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1193:
            _t1981 = self.parse_type()
            item1194 = _t1981
            xs1192.append(item1194)
            cond1193 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1195 = xs1192
        self.consume_literal("]")
        self.consume_literal(")")
        _t1982 = logic_pb2.GNFColumn(column_path=gnf_column_path1190, target_id=relation_id1191, types=types1195)
        result1197 = _t1982
        self.record_span(span_start1196, "GNFColumn")
        return result1197

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1983 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1984 = 0
            else:
                _t1984 = -1
            _t1983 = _t1984
        prediction1198 = _t1983
        if prediction1198 == 1:
            self.consume_literal("[")
            xs1200 = []
            cond1201 = self.match_lookahead_terminal("STRING", 0)
            while cond1201:
                item1202 = self.consume_terminal("STRING")
                xs1200.append(item1202)
                cond1201 = self.match_lookahead_terminal("STRING", 0)
            strings1203 = xs1200
            self.consume_literal("]")
            _t1985 = strings1203
        else:
            if prediction1198 == 0:
                string1199 = self.consume_terminal("STRING")
                _t1986 = [string1199]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1985 = _t1986
        return _t1985

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1204 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1204

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1212 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1987 = self.parse_iceberg_locator()
        iceberg_locator1205 = _t1987
        _t1988 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1206 = _t1988
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("columns", 1)):
            _t1990 = self.parse_gnf_columns()
            _t1989 = _t1990
        else:
            _t1989 = None
        gnf_columns1207 = _t1989
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("full_table", 1)):
            _t1992 = self.parse_full_table()
            _t1991 = _t1992
        else:
            _t1991 = None
        full_table1208 = _t1991
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t1994 = self.parse_iceberg_from_snapshot()
            _t1993 = _t1994
        else:
            _t1993 = None
        iceberg_from_snapshot1209 = _t1993
        if self.match_lookahead_literal("(", 0):
            _t1996 = self.parse_iceberg_to_snapshot()
            _t1995 = _t1996
        else:
            _t1995 = None
        iceberg_to_snapshot1210 = _t1995
        _t1997 = self.parse_boolean_value()
        boolean_value1211 = _t1997
        self.consume_literal(")")
        _t1998 = self.construct_iceberg_data(iceberg_locator1205, iceberg_catalog_config1206, gnf_columns1207, full_table1208, iceberg_from_snapshot1209, iceberg_to_snapshot1210, boolean_value1211)
        result1213 = _t1998
        self.record_span(span_start1212, "IcebergData")
        return result1213

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1217 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t1999 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1214 = _t1999
        _t2000 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1215 = _t2000
        _t2001 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1216 = _t2001
        self.consume_literal(")")
        _t2002 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1214, namespace=iceberg_locator_namespace1215, warehouse=iceberg_locator_warehouse1216)
        result1218 = _t2002
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
        _t2003 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1225 = _t2003
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t2005 = self.parse_iceberg_catalog_config_scope()
            _t2004 = _t2005
        else:
            _t2004 = None
        iceberg_catalog_config_scope1226 = _t2004
        _t2006 = self.parse_iceberg_properties()
        iceberg_properties1227 = _t2006
        _t2007 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1228 = _t2007
        self.consume_literal(")")
        _t2008 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1225, iceberg_catalog_config_scope1226, iceberg_properties1227, iceberg_auth_properties1228)
        result1230 = _t2008
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
            _t2009 = self.parse_iceberg_property_entry()
            item1235 = _t2009
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
            _t2010 = self.parse_iceberg_masked_property_entry()
            item1241 = _t2010
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

    def parse_full_table(self) -> logic_pb2.IcebergTarget:
        span_start1250 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("full_table")
        _t2011 = self.parse_relation_id()
        relation_id1245 = _t2011
        self.consume_literal("[")
        xs1246 = []
        cond1247 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1247:
            _t2012 = self.parse_type()
            item1248 = _t2012
            xs1246.append(item1248)
            cond1247 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1249 = xs1246
        self.consume_literal("]")
        self.consume_literal(")")
        _t2013 = logic_pb2.IcebergTarget(target_id=relation_id1245, types=types1249)
        result1251 = _t2013
        self.record_span(span_start1250, "IcebergTarget")
        return result1251

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1252 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1252

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1253 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1253

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1255 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2014 = self.parse_fragment_id()
        fragment_id1254 = _t2014
        self.consume_literal(")")
        _t2015 = transactions_pb2.Undefine(fragment_id=fragment_id1254)
        result1256 = _t2015
        self.record_span(span_start1255, "Undefine")
        return result1256

    def parse_context(self) -> transactions_pb2.Context:
        span_start1261 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1257 = []
        cond1258 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1258:
            _t2016 = self.parse_relation_id()
            item1259 = _t2016
            xs1257.append(item1259)
            cond1258 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1260 = xs1257
        self.consume_literal(")")
        _t2017 = transactions_pb2.Context(relations=relation_ids1260)
        result1262 = _t2017
        self.record_span(span_start1261, "Context")
        return result1262

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1268 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t2018 = self.parse_edb_path()
        edb_path1263 = _t2018
        xs1264 = []
        cond1265 = self.match_lookahead_literal("[", 0)
        while cond1265:
            _t2019 = self.parse_snapshot_mapping()
            item1266 = _t2019
            xs1264.append(item1266)
            cond1265 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1267 = xs1264
        self.consume_literal(")")
        _t2020 = transactions_pb2.Snapshot(prefix=edb_path1263, mappings=snapshot_mappings1267)
        result1269 = _t2020
        self.record_span(span_start1268, "Snapshot")
        return result1269

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1272 = self.span_start()
        _t2021 = self.parse_edb_path()
        edb_path1270 = _t2021
        _t2022 = self.parse_relation_id()
        relation_id1271 = _t2022
        _t2023 = transactions_pb2.SnapshotMapping(destination_path=edb_path1270, source_relation=relation_id1271)
        result1273 = _t2023
        self.record_span(span_start1272, "SnapshotMapping")
        return result1273

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1274 = []
        cond1275 = self.match_lookahead_literal("(", 0)
        while cond1275:
            _t2024 = self.parse_read()
            item1276 = _t2024
            xs1274.append(item1276)
            cond1275 = self.match_lookahead_literal("(", 0)
        reads1277 = xs1274
        self.consume_literal(")")
        return reads1277

    def parse_read(self) -> transactions_pb2.Read:
        span_start1284 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2026 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2027 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t2028 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t2029 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t2030 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t2031 = 3
                                else:
                                    _t2031 = -1
                                _t2030 = _t2031
                            _t2029 = _t2030
                        _t2028 = _t2029
                    _t2027 = _t2028
                _t2026 = _t2027
            _t2025 = _t2026
        else:
            _t2025 = -1
        prediction1278 = _t2025
        if prediction1278 == 4:
            _t2033 = self.parse_export()
            export1283 = _t2033
            _t2034 = transactions_pb2.Read(export=export1283)
            _t2032 = _t2034
        else:
            if prediction1278 == 3:
                _t2036 = self.parse_abort()
                abort1282 = _t2036
                _t2037 = transactions_pb2.Read(abort=abort1282)
                _t2035 = _t2037
            else:
                if prediction1278 == 2:
                    _t2039 = self.parse_what_if()
                    what_if1281 = _t2039
                    _t2040 = transactions_pb2.Read(what_if=what_if1281)
                    _t2038 = _t2040
                else:
                    if prediction1278 == 1:
                        _t2042 = self.parse_output()
                        output1280 = _t2042
                        _t2043 = transactions_pb2.Read(output=output1280)
                        _t2041 = _t2043
                    else:
                        if prediction1278 == 0:
                            _t2045 = self.parse_demand()
                            demand1279 = _t2045
                            _t2046 = transactions_pb2.Read(demand=demand1279)
                            _t2044 = _t2046
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2041 = _t2044
                    _t2038 = _t2041
                _t2035 = _t2038
            _t2032 = _t2035
        result1285 = _t2032
        self.record_span(span_start1284, "Read")
        return result1285

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1287 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2047 = self.parse_relation_id()
        relation_id1286 = _t2047
        self.consume_literal(")")
        _t2048 = transactions_pb2.Demand(relation_id=relation_id1286)
        result1288 = _t2048
        self.record_span(span_start1287, "Demand")
        return result1288

    def parse_output(self) -> transactions_pb2.Output:
        span_start1291 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2049 = self.parse_name()
        name1289 = _t2049
        _t2050 = self.parse_relation_id()
        relation_id1290 = _t2050
        self.consume_literal(")")
        _t2051 = transactions_pb2.Output(name=name1289, relation_id=relation_id1290)
        result1292 = _t2051
        self.record_span(span_start1291, "Output")
        return result1292

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1295 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2052 = self.parse_name()
        name1293 = _t2052
        _t2053 = self.parse_epoch()
        epoch1294 = _t2053
        self.consume_literal(")")
        _t2054 = transactions_pb2.WhatIf(branch=name1293, epoch=epoch1294)
        result1296 = _t2054
        self.record_span(span_start1295, "WhatIf")
        return result1296

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1299 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2056 = self.parse_name()
            _t2055 = _t2056
        else:
            _t2055 = None
        name1297 = _t2055
        _t2057 = self.parse_relation_id()
        relation_id1298 = _t2057
        self.consume_literal(")")
        _t2058 = transactions_pb2.Abort(name=(name1297 if name1297 is not None else "abort"), relation_id=relation_id1298)
        result1300 = _t2058
        self.record_span(span_start1299, "Abort")
        return result1300

    def parse_export(self) -> transactions_pb2.Export:
        span_start1304 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2060 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2061 = 0
                else:
                    _t2061 = -1
                _t2060 = _t2061
            _t2059 = _t2060
        else:
            _t2059 = -1
        prediction1301 = _t2059
        if prediction1301 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2063 = self.parse_export_iceberg_config()
            export_iceberg_config1303 = _t2063
            self.consume_literal(")")
            _t2064 = transactions_pb2.Export(iceberg_config=export_iceberg_config1303)
            _t2062 = _t2064
        else:
            if prediction1301 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2066 = self.parse_export_csv_config()
                export_csv_config1302 = _t2066
                self.consume_literal(")")
                _t2067 = transactions_pb2.Export(csv_config=export_csv_config1302)
                _t2065 = _t2067
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2062 = _t2065
        result1305 = _t2062
        self.record_span(span_start1304, "Export")
        return result1305

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1313 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2069 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2070 = 1
                else:
                    _t2070 = -1
                _t2069 = _t2070
            _t2068 = _t2069
        else:
            _t2068 = -1
        prediction1306 = _t2068
        if prediction1306 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2072 = self.parse_export_csv_path()
            export_csv_path1310 = _t2072
            _t2073 = self.parse_export_csv_columns_list()
            export_csv_columns_list1311 = _t2073
            _t2074 = self.parse_config_dict()
            config_dict1312 = _t2074
            self.consume_literal(")")
            _t2075 = self.construct_export_csv_config(export_csv_path1310, export_csv_columns_list1311, config_dict1312)
            _t2071 = _t2075
        else:
            if prediction1306 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2077 = self.parse_export_csv_path()
                export_csv_path1307 = _t2077
                _t2078 = self.parse_export_csv_source()
                export_csv_source1308 = _t2078
                _t2079 = self.parse_csv_config()
                csv_config1309 = _t2079
                self.consume_literal(")")
                _t2080 = self.construct_export_csv_config_with_source(export_csv_path1307, export_csv_source1308, csv_config1309)
                _t2076 = _t2080
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2071 = _t2076
        result1314 = _t2071
        self.record_span(span_start1313, "ExportCSVConfig")
        return result1314

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1315 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1315

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1322 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2082 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2083 = 0
                else:
                    _t2083 = -1
                _t2082 = _t2083
            _t2081 = _t2082
        else:
            _t2081 = -1
        prediction1316 = _t2081
        if prediction1316 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2085 = self.parse_relation_id()
            relation_id1321 = _t2085
            self.consume_literal(")")
            _t2086 = transactions_pb2.ExportCSVSource(table_def=relation_id1321)
            _t2084 = _t2086
        else:
            if prediction1316 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1317 = []
                cond1318 = self.match_lookahead_literal("(", 0)
                while cond1318:
                    _t2088 = self.parse_export_csv_column()
                    item1319 = _t2088
                    xs1317.append(item1319)
                    cond1318 = self.match_lookahead_literal("(", 0)
                export_csv_columns1320 = xs1317
                self.consume_literal(")")
                _t2089 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1320)
                _t2090 = transactions_pb2.ExportCSVSource(gnf_columns=_t2089)
                _t2087 = _t2090
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2084 = _t2087
        result1323 = _t2084
        self.record_span(span_start1322, "ExportCSVSource")
        return result1323

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1326 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1324 = self.consume_terminal("STRING")
        _t2091 = self.parse_relation_id()
        relation_id1325 = _t2091
        self.consume_literal(")")
        _t2092 = transactions_pb2.ExportCSVColumn(column_name=string1324, column_data=relation_id1325)
        result1327 = _t2092
        self.record_span(span_start1326, "ExportCSVColumn")
        return result1327

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1328 = []
        cond1329 = self.match_lookahead_literal("(", 0)
        while cond1329:
            _t2093 = self.parse_export_csv_column()
            item1330 = _t2093
            xs1328.append(item1330)
            cond1329 = self.match_lookahead_literal("(", 0)
        export_csv_columns1331 = xs1328
        self.consume_literal(")")
        return export_csv_columns1331

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1337 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2094 = self.parse_iceberg_locator()
        iceberg_locator1332 = _t2094
        _t2095 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1333 = _t2095
        _t2096 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1334 = _t2096
        _t2097 = self.parse_iceberg_table_properties()
        iceberg_table_properties1335 = _t2097
        if self.match_lookahead_literal("{", 0):
            _t2099 = self.parse_config_dict()
            _t2098 = _t2099
        else:
            _t2098 = None
        config_dict1336 = _t2098
        self.consume_literal(")")
        _t2100 = self.construct_export_iceberg_config_full(iceberg_locator1332, iceberg_catalog_config1333, export_iceberg_table_def1334, iceberg_table_properties1335, config_dict1336)
        result1338 = _t2100
        self.record_span(span_start1337, "ExportIcebergConfig")
        return result1338

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1340 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2101 = self.parse_relation_id()
        relation_id1339 = _t2101
        self.consume_literal(")")
        result1341 = relation_id1339
        self.record_span(span_start1340, "RelationId")
        return result1341

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1342 = []
        cond1343 = self.match_lookahead_literal("(", 0)
        while cond1343:
            _t2102 = self.parse_iceberg_property_entry()
            item1344 = _t2102
            xs1342.append(item1344)
            cond1343 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1345 = xs1342
        self.consume_literal(")")
        return iceberg_property_entrys1345


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
