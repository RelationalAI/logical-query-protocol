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
            _t2092 = value.HasField("int32_value")
        else:
            _t2092 = False
        if _t2092:
            assert value is not None
            return value.int32_value
        else:
            _t2093 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2094 = value.HasField("int_value")
        else:
            _t2094 = False
        if _t2094:
            assert value is not None
            return value.int_value
        else:
            _t2095 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2096 = value.HasField("string_value")
        else:
            _t2096 = False
        if _t2096:
            assert value is not None
            return value.string_value
        else:
            _t2097 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2098 = value.HasField("boolean_value")
        else:
            _t2098 = False
        if _t2098:
            assert value is not None
            return value.boolean_value
        else:
            _t2099 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2100 = value.HasField("string_value")
        else:
            _t2100 = False
        if _t2100:
            assert value is not None
            return [value.string_value]
        else:
            _t2101 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
        if value is not None:
            assert value is not None
            _t2102 = value.HasField("int_value")
        else:
            _t2102 = False
        if _t2102:
            assert value is not None
            return value.int_value
        else:
            _t2103 = None
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2104 = value.HasField("float_value")
        else:
            _t2104 = False
        if _t2104:
            assert value is not None
            return value.float_value
        else:
            _t2105 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2106 = value.HasField("string_value")
        else:
            _t2106 = False
        if _t2106:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2107 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2108 = value.HasField("uint128_value")
        else:
            _t2108 = False
        if _t2108:
            assert value is not None
            return value.uint128_value
        else:
            _t2109 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2110 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2110
        _t2111 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2111
        _t2112 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2112
        _t2113 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2113
        _t2114 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2114
        _t2115 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2115
        _t2116 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2116
        _t2117 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2117
        _t2118 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2118
        _t2119 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2119
        _t2120 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t2120
        _t2121 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2121
        _t2122 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t2122

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2123 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2123
        _t2124 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2124
        _t2125 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2125
        _t2126 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2126
        _t2127 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2127
        _t2128 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2128
        _t2129 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2129
        _t2130 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2130
        _t2131 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2131
        _t2132 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2132
        _t2133 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2133

    def default_configure(self) -> transactions_pb2.Configure:
        _t2134 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2134
        _t2135 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2135

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
        _t2136 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2136
        _t2137 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2137
        _t2138 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2138

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2139 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2139
        _t2140 = self._extract_value_string(config.get("compression"), "")
        compression = _t2140
        _t2141 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2141
        _t2142 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2142
        _t2143 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2143
        _t2144 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2144
        _t2145 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2145
        _t2146 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2146

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2147 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2147

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2148 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2148

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[logic_pb2.GNFColumn], from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2149 = logic_pb2.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2149

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, columns: Sequence[transactions_pb2.ExportColumn], table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2150 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2150
        _t2151 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2151
        _t2152 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2152
        table_props = dict(table_property_pairs)
        _t2153 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2153

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start677 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1343 = self.parse_configure()
            _t1342 = _t1343
        else:
            _t1342 = None
        configure671 = _t1342
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1345 = self.parse_sync()
            _t1344 = _t1345
        else:
            _t1344 = None
        sync672 = _t1344
        xs673 = []
        cond674 = self.match_lookahead_literal("(", 0)
        while cond674:
            _t1346 = self.parse_epoch()
            item675 = _t1346
            xs673.append(item675)
            cond674 = self.match_lookahead_literal("(", 0)
        epochs676 = xs673
        self.consume_literal(")")
        _t1347 = self.default_configure()
        _t1348 = transactions_pb2.Transaction(epochs=epochs676, configure=(configure671 if configure671 is not None else _t1347), sync=sync672)
        result678 = _t1348
        self.record_span(span_start677, "Transaction")
        return result678

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start680 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1349 = self.parse_config_dict()
        config_dict679 = _t1349
        self.consume_literal(")")
        _t1350 = self.construct_configure(config_dict679)
        result681 = _t1350
        self.record_span(span_start680, "Configure")
        return result681

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs682 = []
        cond683 = self.match_lookahead_literal(":", 0)
        while cond683:
            _t1351 = self.parse_config_key_value()
            item684 = _t1351
            xs682.append(item684)
            cond683 = self.match_lookahead_literal(":", 0)
        config_key_values685 = xs682
        self.consume_literal("}")
        return config_key_values685

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol686 = self.consume_terminal("SYMBOL")
        _t1352 = self.parse_raw_value()
        raw_value687 = _t1352
        return (symbol686, raw_value687,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start701 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1353 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1354 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1355 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1357 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1358 = 0
                            else:
                                _t1358 = -1
                            _t1357 = _t1358
                        _t1356 = _t1357
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1359 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1360 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1361 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1362 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1363 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1364 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1365 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1366 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1367 = 10
                                                        else:
                                                            _t1367 = -1
                                                        _t1366 = _t1367
                                                    _t1365 = _t1366
                                                _t1364 = _t1365
                                            _t1363 = _t1364
                                        _t1362 = _t1363
                                    _t1361 = _t1362
                                _t1360 = _t1361
                            _t1359 = _t1360
                        _t1356 = _t1359
                    _t1355 = _t1356
                _t1354 = _t1355
            _t1353 = _t1354
        prediction688 = _t1353
        if prediction688 == 12:
            _t1369 = self.parse_boolean_value()
            boolean_value700 = _t1369
            _t1370 = logic_pb2.Value(boolean_value=boolean_value700)
            _t1368 = _t1370
        else:
            if prediction688 == 11:
                self.consume_literal("missing")
                _t1372 = logic_pb2.MissingValue()
                _t1373 = logic_pb2.Value(missing_value=_t1372)
                _t1371 = _t1373
            else:
                if prediction688 == 10:
                    decimal699 = self.consume_terminal("DECIMAL")
                    _t1375 = logic_pb2.Value(decimal_value=decimal699)
                    _t1374 = _t1375
                else:
                    if prediction688 == 9:
                        int128698 = self.consume_terminal("INT128")
                        _t1377 = logic_pb2.Value(int128_value=int128698)
                        _t1376 = _t1377
                    else:
                        if prediction688 == 8:
                            uint128697 = self.consume_terminal("UINT128")
                            _t1379 = logic_pb2.Value(uint128_value=uint128697)
                            _t1378 = _t1379
                        else:
                            if prediction688 == 7:
                                uint32696 = self.consume_terminal("UINT32")
                                _t1381 = logic_pb2.Value(uint32_value=uint32696)
                                _t1380 = _t1381
                            else:
                                if prediction688 == 6:
                                    float695 = self.consume_terminal("FLOAT")
                                    _t1383 = logic_pb2.Value(float_value=float695)
                                    _t1382 = _t1383
                                else:
                                    if prediction688 == 5:
                                        float32694 = self.consume_terminal("FLOAT32")
                                        _t1385 = logic_pb2.Value(float32_value=float32694)
                                        _t1384 = _t1385
                                    else:
                                        if prediction688 == 4:
                                            int693 = self.consume_terminal("INT")
                                            _t1387 = logic_pb2.Value(int_value=int693)
                                            _t1386 = _t1387
                                        else:
                                            if prediction688 == 3:
                                                int32692 = self.consume_terminal("INT32")
                                                _t1389 = logic_pb2.Value(int32_value=int32692)
                                                _t1388 = _t1389
                                            else:
                                                if prediction688 == 2:
                                                    string691 = self.consume_terminal("STRING")
                                                    _t1391 = logic_pb2.Value(string_value=string691)
                                                    _t1390 = _t1391
                                                else:
                                                    if prediction688 == 1:
                                                        _t1393 = self.parse_raw_datetime()
                                                        raw_datetime690 = _t1393
                                                        _t1394 = logic_pb2.Value(datetime_value=raw_datetime690)
                                                        _t1392 = _t1394
                                                    else:
                                                        if prediction688 == 0:
                                                            _t1396 = self.parse_raw_date()
                                                            raw_date689 = _t1396
                                                            _t1397 = logic_pb2.Value(date_value=raw_date689)
                                                            _t1395 = _t1397
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1392 = _t1395
                                                    _t1390 = _t1392
                                                _t1388 = _t1390
                                            _t1386 = _t1388
                                        _t1384 = _t1386
                                    _t1382 = _t1384
                                _t1380 = _t1382
                            _t1378 = _t1380
                        _t1376 = _t1378
                    _t1374 = _t1376
                _t1371 = _t1374
            _t1368 = _t1371
        result702 = _t1368
        self.record_span(span_start701, "Value")
        return result702

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start706 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int703 = self.consume_terminal("INT")
        int_3704 = self.consume_terminal("INT")
        int_4705 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1398 = logic_pb2.DateValue(year=int(int703), month=int(int_3704), day=int(int_4705))
        result707 = _t1398
        self.record_span(span_start706, "DateValue")
        return result707

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start715 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int708 = self.consume_terminal("INT")
        int_3709 = self.consume_terminal("INT")
        int_4710 = self.consume_terminal("INT")
        int_5711 = self.consume_terminal("INT")
        int_6712 = self.consume_terminal("INT")
        int_7713 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1399 = self.consume_terminal("INT")
        else:
            _t1399 = None
        int_8714 = _t1399
        self.consume_literal(")")
        _t1400 = logic_pb2.DateTimeValue(year=int(int708), month=int(int_3709), day=int(int_4710), hour=int(int_5711), minute=int(int_6712), second=int(int_7713), microsecond=int((int_8714 if int_8714 is not None else 0)))
        result716 = _t1400
        self.record_span(span_start715, "DateTimeValue")
        return result716

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1401 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1402 = 1
            else:
                _t1402 = -1
            _t1401 = _t1402
        prediction717 = _t1401
        if prediction717 == 1:
            self.consume_literal("false")
            _t1403 = False
        else:
            if prediction717 == 0:
                self.consume_literal("true")
                _t1404 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1403 = _t1404
        return _t1403

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start722 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs718 = []
        cond719 = self.match_lookahead_literal(":", 0)
        while cond719:
            _t1405 = self.parse_fragment_id()
            item720 = _t1405
            xs718.append(item720)
            cond719 = self.match_lookahead_literal(":", 0)
        fragment_ids721 = xs718
        self.consume_literal(")")
        _t1406 = transactions_pb2.Sync(fragments=fragment_ids721)
        result723 = _t1406
        self.record_span(span_start722, "Sync")
        return result723

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start725 = self.span_start()
        self.consume_literal(":")
        symbol724 = self.consume_terminal("SYMBOL")
        result726 = fragments_pb2.FragmentId(id=symbol724.encode())
        self.record_span(span_start725, "FragmentId")
        return result726

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start729 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1408 = self.parse_epoch_writes()
            _t1407 = _t1408
        else:
            _t1407 = None
        epoch_writes727 = _t1407
        if self.match_lookahead_literal("(", 0):
            _t1410 = self.parse_epoch_reads()
            _t1409 = _t1410
        else:
            _t1409 = None
        epoch_reads728 = _t1409
        self.consume_literal(")")
        _t1411 = transactions_pb2.Epoch(writes=(epoch_writes727 if epoch_writes727 is not None else []), reads=(epoch_reads728 if epoch_reads728 is not None else []))
        result730 = _t1411
        self.record_span(span_start729, "Epoch")
        return result730

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs731 = []
        cond732 = self.match_lookahead_literal("(", 0)
        while cond732:
            _t1412 = self.parse_write()
            item733 = _t1412
            xs731.append(item733)
            cond732 = self.match_lookahead_literal("(", 0)
        writes734 = xs731
        self.consume_literal(")")
        return writes734

    def parse_write(self) -> transactions_pb2.Write:
        span_start740 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1414 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1415 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1416 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1417 = 2
                        else:
                            _t1417 = -1
                        _t1416 = _t1417
                    _t1415 = _t1416
                _t1414 = _t1415
            _t1413 = _t1414
        else:
            _t1413 = -1
        prediction735 = _t1413
        if prediction735 == 3:
            _t1419 = self.parse_snapshot()
            snapshot739 = _t1419
            _t1420 = transactions_pb2.Write(snapshot=snapshot739)
            _t1418 = _t1420
        else:
            if prediction735 == 2:
                _t1422 = self.parse_context()
                context738 = _t1422
                _t1423 = transactions_pb2.Write(context=context738)
                _t1421 = _t1423
            else:
                if prediction735 == 1:
                    _t1425 = self.parse_undefine()
                    undefine737 = _t1425
                    _t1426 = transactions_pb2.Write(undefine=undefine737)
                    _t1424 = _t1426
                else:
                    if prediction735 == 0:
                        _t1428 = self.parse_define()
                        define736 = _t1428
                        _t1429 = transactions_pb2.Write(define=define736)
                        _t1427 = _t1429
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1424 = _t1427
                _t1421 = _t1424
            _t1418 = _t1421
        result741 = _t1418
        self.record_span(span_start740, "Write")
        return result741

    def parse_define(self) -> transactions_pb2.Define:
        span_start743 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1430 = self.parse_fragment()
        fragment742 = _t1430
        self.consume_literal(")")
        _t1431 = transactions_pb2.Define(fragment=fragment742)
        result744 = _t1431
        self.record_span(span_start743, "Define")
        return result744

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start750 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1432 = self.parse_new_fragment_id()
        new_fragment_id745 = _t1432
        xs746 = []
        cond747 = self.match_lookahead_literal("(", 0)
        while cond747:
            _t1433 = self.parse_declaration()
            item748 = _t1433
            xs746.append(item748)
            cond747 = self.match_lookahead_literal("(", 0)
        declarations749 = xs746
        self.consume_literal(")")
        result751 = self.construct_fragment(new_fragment_id745, declarations749)
        self.record_span(span_start750, "Fragment")
        return result751

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start753 = self.span_start()
        _t1434 = self.parse_fragment_id()
        fragment_id752 = _t1434
        self.start_fragment(fragment_id752)
        result754 = fragment_id752
        self.record_span(span_start753, "FragmentId")
        return result754

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start760 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1436 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1437 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1438 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1439 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1440 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1441 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1442 = 1
                                    else:
                                        _t1442 = -1
                                    _t1441 = _t1442
                                _t1440 = _t1441
                            _t1439 = _t1440
                        _t1438 = _t1439
                    _t1437 = _t1438
                _t1436 = _t1437
            _t1435 = _t1436
        else:
            _t1435 = -1
        prediction755 = _t1435
        if prediction755 == 3:
            _t1444 = self.parse_data()
            data759 = _t1444
            _t1445 = logic_pb2.Declaration(data=data759)
            _t1443 = _t1445
        else:
            if prediction755 == 2:
                _t1447 = self.parse_constraint()
                constraint758 = _t1447
                _t1448 = logic_pb2.Declaration(constraint=constraint758)
                _t1446 = _t1448
            else:
                if prediction755 == 1:
                    _t1450 = self.parse_algorithm()
                    algorithm757 = _t1450
                    _t1451 = logic_pb2.Declaration(algorithm=algorithm757)
                    _t1449 = _t1451
                else:
                    if prediction755 == 0:
                        _t1453 = self.parse_def()
                        def756 = _t1453
                        _t1454 = logic_pb2.Declaration()
                        getattr(_t1454, 'def').CopyFrom(def756)
                        _t1452 = _t1454
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1449 = _t1452
                _t1446 = _t1449
            _t1443 = _t1446
        result761 = _t1443
        self.record_span(span_start760, "Declaration")
        return result761

    def parse_def(self) -> logic_pb2.Def:
        span_start765 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1455 = self.parse_relation_id()
        relation_id762 = _t1455
        _t1456 = self.parse_abstraction()
        abstraction763 = _t1456
        if self.match_lookahead_literal("(", 0):
            _t1458 = self.parse_attrs()
            _t1457 = _t1458
        else:
            _t1457 = None
        attrs764 = _t1457
        self.consume_literal(")")
        _t1459 = logic_pb2.Def(name=relation_id762, body=abstraction763, attrs=(attrs764 if attrs764 is not None else []))
        result766 = _t1459
        self.record_span(span_start765, "Def")
        return result766

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start770 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1460 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1461 = 1
            else:
                _t1461 = -1
            _t1460 = _t1461
        prediction767 = _t1460
        if prediction767 == 1:
            uint128769 = self.consume_terminal("UINT128")
            _t1462 = logic_pb2.RelationId(id_low=uint128769.low, id_high=uint128769.high)
        else:
            if prediction767 == 0:
                self.consume_literal(":")
                symbol768 = self.consume_terminal("SYMBOL")
                _t1463 = self.relation_id_from_string(symbol768)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1462 = _t1463
        result771 = _t1462
        self.record_span(span_start770, "RelationId")
        return result771

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start774 = self.span_start()
        self.consume_literal("(")
        _t1464 = self.parse_bindings()
        bindings772 = _t1464
        _t1465 = self.parse_formula()
        formula773 = _t1465
        self.consume_literal(")")
        _t1466 = logic_pb2.Abstraction(vars=(list(bindings772[0]) + list(bindings772[1] if bindings772[1] is not None else [])), value=formula773)
        result775 = _t1466
        self.record_span(span_start774, "Abstraction")
        return result775

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs776 = []
        cond777 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond777:
            _t1467 = self.parse_binding()
            item778 = _t1467
            xs776.append(item778)
            cond777 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings779 = xs776
        if self.match_lookahead_literal("|", 0):
            _t1469 = self.parse_value_bindings()
            _t1468 = _t1469
        else:
            _t1468 = None
        value_bindings780 = _t1468
        self.consume_literal("]")
        return (bindings779, (value_bindings780 if value_bindings780 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start783 = self.span_start()
        symbol781 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1470 = self.parse_type()
        type782 = _t1470
        _t1471 = logic_pb2.Var(name=symbol781)
        _t1472 = logic_pb2.Binding(var=_t1471, type=type782)
        result784 = _t1472
        self.record_span(span_start783, "Binding")
        return result784

    def parse_type(self) -> logic_pb2.Type:
        span_start800 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1473 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1474 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1475 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1476 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1477 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1478 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1479 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1480 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1481 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1482 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1483 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1484 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1485 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1486 = 9
                                                            else:
                                                                _t1486 = -1
                                                            _t1485 = _t1486
                                                        _t1484 = _t1485
                                                    _t1483 = _t1484
                                                _t1482 = _t1483
                                            _t1481 = _t1482
                                        _t1480 = _t1481
                                    _t1479 = _t1480
                                _t1478 = _t1479
                            _t1477 = _t1478
                        _t1476 = _t1477
                    _t1475 = _t1476
                _t1474 = _t1475
            _t1473 = _t1474
        prediction785 = _t1473
        if prediction785 == 13:
            _t1488 = self.parse_uint32_type()
            uint32_type799 = _t1488
            _t1489 = logic_pb2.Type(uint32_type=uint32_type799)
            _t1487 = _t1489
        else:
            if prediction785 == 12:
                _t1491 = self.parse_float32_type()
                float32_type798 = _t1491
                _t1492 = logic_pb2.Type(float32_type=float32_type798)
                _t1490 = _t1492
            else:
                if prediction785 == 11:
                    _t1494 = self.parse_int32_type()
                    int32_type797 = _t1494
                    _t1495 = logic_pb2.Type(int32_type=int32_type797)
                    _t1493 = _t1495
                else:
                    if prediction785 == 10:
                        _t1497 = self.parse_boolean_type()
                        boolean_type796 = _t1497
                        _t1498 = logic_pb2.Type(boolean_type=boolean_type796)
                        _t1496 = _t1498
                    else:
                        if prediction785 == 9:
                            _t1500 = self.parse_decimal_type()
                            decimal_type795 = _t1500
                            _t1501 = logic_pb2.Type(decimal_type=decimal_type795)
                            _t1499 = _t1501
                        else:
                            if prediction785 == 8:
                                _t1503 = self.parse_missing_type()
                                missing_type794 = _t1503
                                _t1504 = logic_pb2.Type(missing_type=missing_type794)
                                _t1502 = _t1504
                            else:
                                if prediction785 == 7:
                                    _t1506 = self.parse_datetime_type()
                                    datetime_type793 = _t1506
                                    _t1507 = logic_pb2.Type(datetime_type=datetime_type793)
                                    _t1505 = _t1507
                                else:
                                    if prediction785 == 6:
                                        _t1509 = self.parse_date_type()
                                        date_type792 = _t1509
                                        _t1510 = logic_pb2.Type(date_type=date_type792)
                                        _t1508 = _t1510
                                    else:
                                        if prediction785 == 5:
                                            _t1512 = self.parse_int128_type()
                                            int128_type791 = _t1512
                                            _t1513 = logic_pb2.Type(int128_type=int128_type791)
                                            _t1511 = _t1513
                                        else:
                                            if prediction785 == 4:
                                                _t1515 = self.parse_uint128_type()
                                                uint128_type790 = _t1515
                                                _t1516 = logic_pb2.Type(uint128_type=uint128_type790)
                                                _t1514 = _t1516
                                            else:
                                                if prediction785 == 3:
                                                    _t1518 = self.parse_float_type()
                                                    float_type789 = _t1518
                                                    _t1519 = logic_pb2.Type(float_type=float_type789)
                                                    _t1517 = _t1519
                                                else:
                                                    if prediction785 == 2:
                                                        _t1521 = self.parse_int_type()
                                                        int_type788 = _t1521
                                                        _t1522 = logic_pb2.Type(int_type=int_type788)
                                                        _t1520 = _t1522
                                                    else:
                                                        if prediction785 == 1:
                                                            _t1524 = self.parse_string_type()
                                                            string_type787 = _t1524
                                                            _t1525 = logic_pb2.Type(string_type=string_type787)
                                                            _t1523 = _t1525
                                                        else:
                                                            if prediction785 == 0:
                                                                _t1527 = self.parse_unspecified_type()
                                                                unspecified_type786 = _t1527
                                                                _t1528 = logic_pb2.Type(unspecified_type=unspecified_type786)
                                                                _t1526 = _t1528
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1490 = _t1493
            _t1487 = _t1490
        result801 = _t1487
        self.record_span(span_start800, "Type")
        return result801

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start802 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1529 = logic_pb2.UnspecifiedType()
        result803 = _t1529
        self.record_span(span_start802, "UnspecifiedType")
        return result803

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start804 = self.span_start()
        self.consume_literal("STRING")
        _t1530 = logic_pb2.StringType()
        result805 = _t1530
        self.record_span(span_start804, "StringType")
        return result805

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start806 = self.span_start()
        self.consume_literal("INT")
        _t1531 = logic_pb2.IntType()
        result807 = _t1531
        self.record_span(span_start806, "IntType")
        return result807

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start808 = self.span_start()
        self.consume_literal("FLOAT")
        _t1532 = logic_pb2.FloatType()
        result809 = _t1532
        self.record_span(span_start808, "FloatType")
        return result809

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start810 = self.span_start()
        self.consume_literal("UINT128")
        _t1533 = logic_pb2.UInt128Type()
        result811 = _t1533
        self.record_span(span_start810, "UInt128Type")
        return result811

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start812 = self.span_start()
        self.consume_literal("INT128")
        _t1534 = logic_pb2.Int128Type()
        result813 = _t1534
        self.record_span(span_start812, "Int128Type")
        return result813

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start814 = self.span_start()
        self.consume_literal("DATE")
        _t1535 = logic_pb2.DateType()
        result815 = _t1535
        self.record_span(span_start814, "DateType")
        return result815

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start816 = self.span_start()
        self.consume_literal("DATETIME")
        _t1536 = logic_pb2.DateTimeType()
        result817 = _t1536
        self.record_span(span_start816, "DateTimeType")
        return result817

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start818 = self.span_start()
        self.consume_literal("MISSING")
        _t1537 = logic_pb2.MissingType()
        result819 = _t1537
        self.record_span(span_start818, "MissingType")
        return result819

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start822 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int820 = self.consume_terminal("INT")
        int_3821 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1538 = logic_pb2.DecimalType(precision=int(int820), scale=int(int_3821))
        result823 = _t1538
        self.record_span(span_start822, "DecimalType")
        return result823

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start824 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1539 = logic_pb2.BooleanType()
        result825 = _t1539
        self.record_span(span_start824, "BooleanType")
        return result825

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start826 = self.span_start()
        self.consume_literal("INT32")
        _t1540 = logic_pb2.Int32Type()
        result827 = _t1540
        self.record_span(span_start826, "Int32Type")
        return result827

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start828 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1541 = logic_pb2.Float32Type()
        result829 = _t1541
        self.record_span(span_start828, "Float32Type")
        return result829

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start830 = self.span_start()
        self.consume_literal("UINT32")
        _t1542 = logic_pb2.UInt32Type()
        result831 = _t1542
        self.record_span(span_start830, "UInt32Type")
        return result831

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs832 = []
        cond833 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond833:
            _t1543 = self.parse_binding()
            item834 = _t1543
            xs832.append(item834)
            cond833 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings835 = xs832
        return bindings835

    def parse_formula(self) -> logic_pb2.Formula:
        span_start850 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1545 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1546 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1547 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1548 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1549 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1550 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1551 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1552 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1553 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1554 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1555 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1556 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1557 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1558 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1559 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1560 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1561 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1562 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1563 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1564 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1565 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1566 = 10
                                                                                                else:
                                                                                                    _t1566 = -1
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
                        _t1547 = _t1548
                    _t1546 = _t1547
                _t1545 = _t1546
            _t1544 = _t1545
        else:
            _t1544 = -1
        prediction836 = _t1544
        if prediction836 == 12:
            _t1568 = self.parse_cast()
            cast849 = _t1568
            _t1569 = logic_pb2.Formula(cast=cast849)
            _t1567 = _t1569
        else:
            if prediction836 == 11:
                _t1571 = self.parse_rel_atom()
                rel_atom848 = _t1571
                _t1572 = logic_pb2.Formula(rel_atom=rel_atom848)
                _t1570 = _t1572
            else:
                if prediction836 == 10:
                    _t1574 = self.parse_primitive()
                    primitive847 = _t1574
                    _t1575 = logic_pb2.Formula(primitive=primitive847)
                    _t1573 = _t1575
                else:
                    if prediction836 == 9:
                        _t1577 = self.parse_pragma()
                        pragma846 = _t1577
                        _t1578 = logic_pb2.Formula(pragma=pragma846)
                        _t1576 = _t1578
                    else:
                        if prediction836 == 8:
                            _t1580 = self.parse_atom()
                            atom845 = _t1580
                            _t1581 = logic_pb2.Formula(atom=atom845)
                            _t1579 = _t1581
                        else:
                            if prediction836 == 7:
                                _t1583 = self.parse_ffi()
                                ffi844 = _t1583
                                _t1584 = logic_pb2.Formula(ffi=ffi844)
                                _t1582 = _t1584
                            else:
                                if prediction836 == 6:
                                    _t1586 = self.parse_not()
                                    not843 = _t1586
                                    _t1587 = logic_pb2.Formula()
                                    getattr(_t1587, 'not').CopyFrom(not843)
                                    _t1585 = _t1587
                                else:
                                    if prediction836 == 5:
                                        _t1589 = self.parse_disjunction()
                                        disjunction842 = _t1589
                                        _t1590 = logic_pb2.Formula(disjunction=disjunction842)
                                        _t1588 = _t1590
                                    else:
                                        if prediction836 == 4:
                                            _t1592 = self.parse_conjunction()
                                            conjunction841 = _t1592
                                            _t1593 = logic_pb2.Formula(conjunction=conjunction841)
                                            _t1591 = _t1593
                                        else:
                                            if prediction836 == 3:
                                                _t1595 = self.parse_reduce()
                                                reduce840 = _t1595
                                                _t1596 = logic_pb2.Formula(reduce=reduce840)
                                                _t1594 = _t1596
                                            else:
                                                if prediction836 == 2:
                                                    _t1598 = self.parse_exists()
                                                    exists839 = _t1598
                                                    _t1599 = logic_pb2.Formula(exists=exists839)
                                                    _t1597 = _t1599
                                                else:
                                                    if prediction836 == 1:
                                                        _t1601 = self.parse_false()
                                                        false838 = _t1601
                                                        _t1602 = logic_pb2.Formula(disjunction=false838)
                                                        _t1600 = _t1602
                                                    else:
                                                        if prediction836 == 0:
                                                            _t1604 = self.parse_true()
                                                            true837 = _t1604
                                                            _t1605 = logic_pb2.Formula(conjunction=true837)
                                                            _t1603 = _t1605
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1570 = _t1573
            _t1567 = _t1570
        result851 = _t1567
        self.record_span(span_start850, "Formula")
        return result851

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start852 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1606 = logic_pb2.Conjunction(args=[])
        result853 = _t1606
        self.record_span(span_start852, "Conjunction")
        return result853

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start854 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1607 = logic_pb2.Disjunction(args=[])
        result855 = _t1607
        self.record_span(span_start854, "Disjunction")
        return result855

    def parse_exists(self) -> logic_pb2.Exists:
        span_start858 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1608 = self.parse_bindings()
        bindings856 = _t1608
        _t1609 = self.parse_formula()
        formula857 = _t1609
        self.consume_literal(")")
        _t1610 = logic_pb2.Abstraction(vars=(list(bindings856[0]) + list(bindings856[1] if bindings856[1] is not None else [])), value=formula857)
        _t1611 = logic_pb2.Exists(body=_t1610)
        result859 = _t1611
        self.record_span(span_start858, "Exists")
        return result859

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start863 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1612 = self.parse_abstraction()
        abstraction860 = _t1612
        _t1613 = self.parse_abstraction()
        abstraction_3861 = _t1613
        _t1614 = self.parse_terms()
        terms862 = _t1614
        self.consume_literal(")")
        _t1615 = logic_pb2.Reduce(op=abstraction860, body=abstraction_3861, terms=terms862)
        result864 = _t1615
        self.record_span(span_start863, "Reduce")
        return result864

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs865 = []
        cond866 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond866:
            _t1616 = self.parse_term()
            item867 = _t1616
            xs865.append(item867)
            cond866 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms868 = xs865
        self.consume_literal(")")
        return terms868

    def parse_term(self) -> logic_pb2.Term:
        span_start872 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1617 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1618 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1619 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1620 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1621 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1622 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1623 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1624 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1625 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1626 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1627 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1628 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1629 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1630 = 1
                                                            else:
                                                                _t1630 = -1
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
        prediction869 = _t1617
        if prediction869 == 1:
            _t1632 = self.parse_value()
            value871 = _t1632
            _t1633 = logic_pb2.Term(constant=value871)
            _t1631 = _t1633
        else:
            if prediction869 == 0:
                _t1635 = self.parse_var()
                var870 = _t1635
                _t1636 = logic_pb2.Term(var=var870)
                _t1634 = _t1636
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1631 = _t1634
        result873 = _t1631
        self.record_span(span_start872, "Term")
        return result873

    def parse_var(self) -> logic_pb2.Var:
        span_start875 = self.span_start()
        symbol874 = self.consume_terminal("SYMBOL")
        _t1637 = logic_pb2.Var(name=symbol874)
        result876 = _t1637
        self.record_span(span_start875, "Var")
        return result876

    def parse_value(self) -> logic_pb2.Value:
        span_start890 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1638 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1639 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1640 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1642 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1643 = 0
                            else:
                                _t1643 = -1
                            _t1642 = _t1643
                        _t1641 = _t1642
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1644 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1645 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1646 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1647 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1648 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1649 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1650 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1651 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1652 = 10
                                                        else:
                                                            _t1652 = -1
                                                        _t1651 = _t1652
                                                    _t1650 = _t1651
                                                _t1649 = _t1650
                                            _t1648 = _t1649
                                        _t1647 = _t1648
                                    _t1646 = _t1647
                                _t1645 = _t1646
                            _t1644 = _t1645
                        _t1641 = _t1644
                    _t1640 = _t1641
                _t1639 = _t1640
            _t1638 = _t1639
        prediction877 = _t1638
        if prediction877 == 12:
            _t1654 = self.parse_boolean_value()
            boolean_value889 = _t1654
            _t1655 = logic_pb2.Value(boolean_value=boolean_value889)
            _t1653 = _t1655
        else:
            if prediction877 == 11:
                self.consume_literal("missing")
                _t1657 = logic_pb2.MissingValue()
                _t1658 = logic_pb2.Value(missing_value=_t1657)
                _t1656 = _t1658
            else:
                if prediction877 == 10:
                    formatted_decimal888 = self.consume_terminal("DECIMAL")
                    _t1660 = logic_pb2.Value(decimal_value=formatted_decimal888)
                    _t1659 = _t1660
                else:
                    if prediction877 == 9:
                        formatted_int128887 = self.consume_terminal("INT128")
                        _t1662 = logic_pb2.Value(int128_value=formatted_int128887)
                        _t1661 = _t1662
                    else:
                        if prediction877 == 8:
                            formatted_uint128886 = self.consume_terminal("UINT128")
                            _t1664 = logic_pb2.Value(uint128_value=formatted_uint128886)
                            _t1663 = _t1664
                        else:
                            if prediction877 == 7:
                                formatted_uint32885 = self.consume_terminal("UINT32")
                                _t1666 = logic_pb2.Value(uint32_value=formatted_uint32885)
                                _t1665 = _t1666
                            else:
                                if prediction877 == 6:
                                    formatted_float884 = self.consume_terminal("FLOAT")
                                    _t1668 = logic_pb2.Value(float_value=formatted_float884)
                                    _t1667 = _t1668
                                else:
                                    if prediction877 == 5:
                                        formatted_float32883 = self.consume_terminal("FLOAT32")
                                        _t1670 = logic_pb2.Value(float32_value=formatted_float32883)
                                        _t1669 = _t1670
                                    else:
                                        if prediction877 == 4:
                                            formatted_int882 = self.consume_terminal("INT")
                                            _t1672 = logic_pb2.Value(int_value=formatted_int882)
                                            _t1671 = _t1672
                                        else:
                                            if prediction877 == 3:
                                                formatted_int32881 = self.consume_terminal("INT32")
                                                _t1674 = logic_pb2.Value(int32_value=formatted_int32881)
                                                _t1673 = _t1674
                                            else:
                                                if prediction877 == 2:
                                                    formatted_string880 = self.consume_terminal("STRING")
                                                    _t1676 = logic_pb2.Value(string_value=formatted_string880)
                                                    _t1675 = _t1676
                                                else:
                                                    if prediction877 == 1:
                                                        _t1678 = self.parse_datetime()
                                                        datetime879 = _t1678
                                                        _t1679 = logic_pb2.Value(datetime_value=datetime879)
                                                        _t1677 = _t1679
                                                    else:
                                                        if prediction877 == 0:
                                                            _t1681 = self.parse_date()
                                                            date878 = _t1681
                                                            _t1682 = logic_pb2.Value(date_value=date878)
                                                            _t1680 = _t1682
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1677 = _t1680
                                                    _t1675 = _t1677
                                                _t1673 = _t1675
                                            _t1671 = _t1673
                                        _t1669 = _t1671
                                    _t1667 = _t1669
                                _t1665 = _t1667
                            _t1663 = _t1665
                        _t1661 = _t1663
                    _t1659 = _t1661
                _t1656 = _t1659
            _t1653 = _t1656
        result891 = _t1653
        self.record_span(span_start890, "Value")
        return result891

    def parse_date(self) -> logic_pb2.DateValue:
        span_start895 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int892 = self.consume_terminal("INT")
        formatted_int_3893 = self.consume_terminal("INT")
        formatted_int_4894 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1683 = logic_pb2.DateValue(year=int(formatted_int892), month=int(formatted_int_3893), day=int(formatted_int_4894))
        result896 = _t1683
        self.record_span(span_start895, "DateValue")
        return result896

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start904 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int897 = self.consume_terminal("INT")
        formatted_int_3898 = self.consume_terminal("INT")
        formatted_int_4899 = self.consume_terminal("INT")
        formatted_int_5900 = self.consume_terminal("INT")
        formatted_int_6901 = self.consume_terminal("INT")
        formatted_int_7902 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1684 = self.consume_terminal("INT")
        else:
            _t1684 = None
        formatted_int_8903 = _t1684
        self.consume_literal(")")
        _t1685 = logic_pb2.DateTimeValue(year=int(formatted_int897), month=int(formatted_int_3898), day=int(formatted_int_4899), hour=int(formatted_int_5900), minute=int(formatted_int_6901), second=int(formatted_int_7902), microsecond=int((formatted_int_8903 if formatted_int_8903 is not None else 0)))
        result905 = _t1685
        self.record_span(span_start904, "DateTimeValue")
        return result905

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start910 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs906 = []
        cond907 = self.match_lookahead_literal("(", 0)
        while cond907:
            _t1686 = self.parse_formula()
            item908 = _t1686
            xs906.append(item908)
            cond907 = self.match_lookahead_literal("(", 0)
        formulas909 = xs906
        self.consume_literal(")")
        _t1687 = logic_pb2.Conjunction(args=formulas909)
        result911 = _t1687
        self.record_span(span_start910, "Conjunction")
        return result911

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start916 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs912 = []
        cond913 = self.match_lookahead_literal("(", 0)
        while cond913:
            _t1688 = self.parse_formula()
            item914 = _t1688
            xs912.append(item914)
            cond913 = self.match_lookahead_literal("(", 0)
        formulas915 = xs912
        self.consume_literal(")")
        _t1689 = logic_pb2.Disjunction(args=formulas915)
        result917 = _t1689
        self.record_span(span_start916, "Disjunction")
        return result917

    def parse_not(self) -> logic_pb2.Not:
        span_start919 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1690 = self.parse_formula()
        formula918 = _t1690
        self.consume_literal(")")
        _t1691 = logic_pb2.Not(arg=formula918)
        result920 = _t1691
        self.record_span(span_start919, "Not")
        return result920

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start924 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1692 = self.parse_name()
        name921 = _t1692
        _t1693 = self.parse_ffi_args()
        ffi_args922 = _t1693
        _t1694 = self.parse_terms()
        terms923 = _t1694
        self.consume_literal(")")
        _t1695 = logic_pb2.FFI(name=name921, args=ffi_args922, terms=terms923)
        result925 = _t1695
        self.record_span(span_start924, "FFI")
        return result925

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol926 = self.consume_terminal("SYMBOL")
        return symbol926

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs927 = []
        cond928 = self.match_lookahead_literal("(", 0)
        while cond928:
            _t1696 = self.parse_abstraction()
            item929 = _t1696
            xs927.append(item929)
            cond928 = self.match_lookahead_literal("(", 0)
        abstractions930 = xs927
        self.consume_literal(")")
        return abstractions930

    def parse_atom(self) -> logic_pb2.Atom:
        span_start936 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1697 = self.parse_relation_id()
        relation_id931 = _t1697
        xs932 = []
        cond933 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond933:
            _t1698 = self.parse_term()
            item934 = _t1698
            xs932.append(item934)
            cond933 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms935 = xs932
        self.consume_literal(")")
        _t1699 = logic_pb2.Atom(name=relation_id931, terms=terms935)
        result937 = _t1699
        self.record_span(span_start936, "Atom")
        return result937

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start943 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1700 = self.parse_name()
        name938 = _t1700
        xs939 = []
        cond940 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond940:
            _t1701 = self.parse_term()
            item941 = _t1701
            xs939.append(item941)
            cond940 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms942 = xs939
        self.consume_literal(")")
        _t1702 = logic_pb2.Pragma(name=name938, terms=terms942)
        result944 = _t1702
        self.record_span(span_start943, "Pragma")
        return result944

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start960 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1704 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1705 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1706 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1707 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1708 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1709 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1710 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1711 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1712 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1713 = 7
                                                else:
                                                    _t1713 = -1
                                                _t1712 = _t1713
                                            _t1711 = _t1712
                                        _t1710 = _t1711
                                    _t1709 = _t1710
                                _t1708 = _t1709
                            _t1707 = _t1708
                        _t1706 = _t1707
                    _t1705 = _t1706
                _t1704 = _t1705
            _t1703 = _t1704
        else:
            _t1703 = -1
        prediction945 = _t1703
        if prediction945 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1715 = self.parse_name()
            name955 = _t1715
            xs956 = []
            cond957 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond957:
                _t1716 = self.parse_rel_term()
                item958 = _t1716
                xs956.append(item958)
                cond957 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms959 = xs956
            self.consume_literal(")")
            _t1717 = logic_pb2.Primitive(name=name955, terms=rel_terms959)
            _t1714 = _t1717
        else:
            if prediction945 == 8:
                _t1719 = self.parse_divide()
                divide954 = _t1719
                _t1718 = divide954
            else:
                if prediction945 == 7:
                    _t1721 = self.parse_multiply()
                    multiply953 = _t1721
                    _t1720 = multiply953
                else:
                    if prediction945 == 6:
                        _t1723 = self.parse_minus()
                        minus952 = _t1723
                        _t1722 = minus952
                    else:
                        if prediction945 == 5:
                            _t1725 = self.parse_add()
                            add951 = _t1725
                            _t1724 = add951
                        else:
                            if prediction945 == 4:
                                _t1727 = self.parse_gt_eq()
                                gt_eq950 = _t1727
                                _t1726 = gt_eq950
                            else:
                                if prediction945 == 3:
                                    _t1729 = self.parse_gt()
                                    gt949 = _t1729
                                    _t1728 = gt949
                                else:
                                    if prediction945 == 2:
                                        _t1731 = self.parse_lt_eq()
                                        lt_eq948 = _t1731
                                        _t1730 = lt_eq948
                                    else:
                                        if prediction945 == 1:
                                            _t1733 = self.parse_lt()
                                            lt947 = _t1733
                                            _t1732 = lt947
                                        else:
                                            if prediction945 == 0:
                                                _t1735 = self.parse_eq()
                                                eq946 = _t1735
                                                _t1734 = eq946
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1732 = _t1734
                                        _t1730 = _t1732
                                    _t1728 = _t1730
                                _t1726 = _t1728
                            _t1724 = _t1726
                        _t1722 = _t1724
                    _t1720 = _t1722
                _t1718 = _t1720
            _t1714 = _t1718
        result961 = _t1714
        self.record_span(span_start960, "Primitive")
        return result961

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start964 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1736 = self.parse_term()
        term962 = _t1736
        _t1737 = self.parse_term()
        term_3963 = _t1737
        self.consume_literal(")")
        _t1738 = logic_pb2.RelTerm(term=term962)
        _t1739 = logic_pb2.RelTerm(term=term_3963)
        _t1740 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1738, _t1739])
        result965 = _t1740
        self.record_span(span_start964, "Primitive")
        return result965

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start968 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1741 = self.parse_term()
        term966 = _t1741
        _t1742 = self.parse_term()
        term_3967 = _t1742
        self.consume_literal(")")
        _t1743 = logic_pb2.RelTerm(term=term966)
        _t1744 = logic_pb2.RelTerm(term=term_3967)
        _t1745 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1743, _t1744])
        result969 = _t1745
        self.record_span(span_start968, "Primitive")
        return result969

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start972 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1746 = self.parse_term()
        term970 = _t1746
        _t1747 = self.parse_term()
        term_3971 = _t1747
        self.consume_literal(")")
        _t1748 = logic_pb2.RelTerm(term=term970)
        _t1749 = logic_pb2.RelTerm(term=term_3971)
        _t1750 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1748, _t1749])
        result973 = _t1750
        self.record_span(span_start972, "Primitive")
        return result973

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start976 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1751 = self.parse_term()
        term974 = _t1751
        _t1752 = self.parse_term()
        term_3975 = _t1752
        self.consume_literal(")")
        _t1753 = logic_pb2.RelTerm(term=term974)
        _t1754 = logic_pb2.RelTerm(term=term_3975)
        _t1755 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1753, _t1754])
        result977 = _t1755
        self.record_span(span_start976, "Primitive")
        return result977

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start980 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1756 = self.parse_term()
        term978 = _t1756
        _t1757 = self.parse_term()
        term_3979 = _t1757
        self.consume_literal(")")
        _t1758 = logic_pb2.RelTerm(term=term978)
        _t1759 = logic_pb2.RelTerm(term=term_3979)
        _t1760 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1758, _t1759])
        result981 = _t1760
        self.record_span(span_start980, "Primitive")
        return result981

    def parse_add(self) -> logic_pb2.Primitive:
        span_start985 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1761 = self.parse_term()
        term982 = _t1761
        _t1762 = self.parse_term()
        term_3983 = _t1762
        _t1763 = self.parse_term()
        term_4984 = _t1763
        self.consume_literal(")")
        _t1764 = logic_pb2.RelTerm(term=term982)
        _t1765 = logic_pb2.RelTerm(term=term_3983)
        _t1766 = logic_pb2.RelTerm(term=term_4984)
        _t1767 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1764, _t1765, _t1766])
        result986 = _t1767
        self.record_span(span_start985, "Primitive")
        return result986

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start990 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1768 = self.parse_term()
        term987 = _t1768
        _t1769 = self.parse_term()
        term_3988 = _t1769
        _t1770 = self.parse_term()
        term_4989 = _t1770
        self.consume_literal(")")
        _t1771 = logic_pb2.RelTerm(term=term987)
        _t1772 = logic_pb2.RelTerm(term=term_3988)
        _t1773 = logic_pb2.RelTerm(term=term_4989)
        _t1774 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1771, _t1772, _t1773])
        result991 = _t1774
        self.record_span(span_start990, "Primitive")
        return result991

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start995 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1775 = self.parse_term()
        term992 = _t1775
        _t1776 = self.parse_term()
        term_3993 = _t1776
        _t1777 = self.parse_term()
        term_4994 = _t1777
        self.consume_literal(")")
        _t1778 = logic_pb2.RelTerm(term=term992)
        _t1779 = logic_pb2.RelTerm(term=term_3993)
        _t1780 = logic_pb2.RelTerm(term=term_4994)
        _t1781 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1778, _t1779, _t1780])
        result996 = _t1781
        self.record_span(span_start995, "Primitive")
        return result996

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start1000 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1782 = self.parse_term()
        term997 = _t1782
        _t1783 = self.parse_term()
        term_3998 = _t1783
        _t1784 = self.parse_term()
        term_4999 = _t1784
        self.consume_literal(")")
        _t1785 = logic_pb2.RelTerm(term=term997)
        _t1786 = logic_pb2.RelTerm(term=term_3998)
        _t1787 = logic_pb2.RelTerm(term=term_4999)
        _t1788 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1785, _t1786, _t1787])
        result1001 = _t1788
        self.record_span(span_start1000, "Primitive")
        return result1001

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1005 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1789 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1790 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1791 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1792 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1793 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1794 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1795 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1796 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1797 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1798 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1799 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1800 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1801 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1802 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1803 = 1
                                                                else:
                                                                    _t1803 = -1
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
                        _t1792 = _t1793
                    _t1791 = _t1792
                _t1790 = _t1791
            _t1789 = _t1790
        prediction1002 = _t1789
        if prediction1002 == 1:
            _t1805 = self.parse_term()
            term1004 = _t1805
            _t1806 = logic_pb2.RelTerm(term=term1004)
            _t1804 = _t1806
        else:
            if prediction1002 == 0:
                _t1808 = self.parse_specialized_value()
                specialized_value1003 = _t1808
                _t1809 = logic_pb2.RelTerm(specialized_value=specialized_value1003)
                _t1807 = _t1809
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1804 = _t1807
        result1006 = _t1804
        self.record_span(span_start1005, "RelTerm")
        return result1006

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1008 = self.span_start()
        self.consume_literal("#")
        _t1810 = self.parse_raw_value()
        raw_value1007 = _t1810
        result1009 = raw_value1007
        self.record_span(span_start1008, "Value")
        return result1009

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1015 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1811 = self.parse_name()
        name1010 = _t1811
        xs1011 = []
        cond1012 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1012:
            _t1812 = self.parse_rel_term()
            item1013 = _t1812
            xs1011.append(item1013)
            cond1012 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1014 = xs1011
        self.consume_literal(")")
        _t1813 = logic_pb2.RelAtom(name=name1010, terms=rel_terms1014)
        result1016 = _t1813
        self.record_span(span_start1015, "RelAtom")
        return result1016

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1019 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1814 = self.parse_term()
        term1017 = _t1814
        _t1815 = self.parse_term()
        term_31018 = _t1815
        self.consume_literal(")")
        _t1816 = logic_pb2.Cast(input=term1017, result=term_31018)
        result1020 = _t1816
        self.record_span(span_start1019, "Cast")
        return result1020

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1021 = []
        cond1022 = self.match_lookahead_literal("(", 0)
        while cond1022:
            _t1817 = self.parse_attribute()
            item1023 = _t1817
            xs1021.append(item1023)
            cond1022 = self.match_lookahead_literal("(", 0)
        attributes1024 = xs1021
        self.consume_literal(")")
        return attributes1024

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1030 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1818 = self.parse_name()
        name1025 = _t1818
        xs1026 = []
        cond1027 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1027:
            _t1819 = self.parse_raw_value()
            item1028 = _t1819
            xs1026.append(item1028)
            cond1027 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1029 = xs1026
        self.consume_literal(")")
        _t1820 = logic_pb2.Attribute(name=name1025, args=raw_values1029)
        result1031 = _t1820
        self.record_span(span_start1030, "Attribute")
        return result1031

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1037 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1032 = []
        cond1033 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1033:
            _t1821 = self.parse_relation_id()
            item1034 = _t1821
            xs1032.append(item1034)
            cond1033 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1035 = xs1032
        _t1822 = self.parse_script()
        script1036 = _t1822
        self.consume_literal(")")
        _t1823 = logic_pb2.Algorithm(body=script1036)
        getattr(_t1823, 'global').extend(relation_ids1035)
        result1038 = _t1823
        self.record_span(span_start1037, "Algorithm")
        return result1038

    def parse_script(self) -> logic_pb2.Script:
        span_start1043 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1039 = []
        cond1040 = self.match_lookahead_literal("(", 0)
        while cond1040:
            _t1824 = self.parse_construct()
            item1041 = _t1824
            xs1039.append(item1041)
            cond1040 = self.match_lookahead_literal("(", 0)
        constructs1042 = xs1039
        self.consume_literal(")")
        _t1825 = logic_pb2.Script(constructs=constructs1042)
        result1044 = _t1825
        self.record_span(span_start1043, "Script")
        return result1044

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1048 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1827 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1828 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1829 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1830 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1831 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1832 = 1
                                else:
                                    _t1832 = -1
                                _t1831 = _t1832
                            _t1830 = _t1831
                        _t1829 = _t1830
                    _t1828 = _t1829
                _t1827 = _t1828
            _t1826 = _t1827
        else:
            _t1826 = -1
        prediction1045 = _t1826
        if prediction1045 == 1:
            _t1834 = self.parse_instruction()
            instruction1047 = _t1834
            _t1835 = logic_pb2.Construct(instruction=instruction1047)
            _t1833 = _t1835
        else:
            if prediction1045 == 0:
                _t1837 = self.parse_loop()
                loop1046 = _t1837
                _t1838 = logic_pb2.Construct(loop=loop1046)
                _t1836 = _t1838
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1833 = _t1836
        result1049 = _t1833
        self.record_span(span_start1048, "Construct")
        return result1049

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1052 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1839 = self.parse_init()
        init1050 = _t1839
        _t1840 = self.parse_script()
        script1051 = _t1840
        self.consume_literal(")")
        _t1841 = logic_pb2.Loop(init=init1050, body=script1051)
        result1053 = _t1841
        self.record_span(span_start1052, "Loop")
        return result1053

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1054 = []
        cond1055 = self.match_lookahead_literal("(", 0)
        while cond1055:
            _t1842 = self.parse_instruction()
            item1056 = _t1842
            xs1054.append(item1056)
            cond1055 = self.match_lookahead_literal("(", 0)
        instructions1057 = xs1054
        self.consume_literal(")")
        return instructions1057

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1064 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1844 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1845 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1846 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1847 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1848 = 0
                            else:
                                _t1848 = -1
                            _t1847 = _t1848
                        _t1846 = _t1847
                    _t1845 = _t1846
                _t1844 = _t1845
            _t1843 = _t1844
        else:
            _t1843 = -1
        prediction1058 = _t1843
        if prediction1058 == 4:
            _t1850 = self.parse_monus_def()
            monus_def1063 = _t1850
            _t1851 = logic_pb2.Instruction(monus_def=monus_def1063)
            _t1849 = _t1851
        else:
            if prediction1058 == 3:
                _t1853 = self.parse_monoid_def()
                monoid_def1062 = _t1853
                _t1854 = logic_pb2.Instruction(monoid_def=monoid_def1062)
                _t1852 = _t1854
            else:
                if prediction1058 == 2:
                    _t1856 = self.parse_break()
                    break1061 = _t1856
                    _t1857 = logic_pb2.Instruction()
                    getattr(_t1857, 'break').CopyFrom(break1061)
                    _t1855 = _t1857
                else:
                    if prediction1058 == 1:
                        _t1859 = self.parse_upsert()
                        upsert1060 = _t1859
                        _t1860 = logic_pb2.Instruction(upsert=upsert1060)
                        _t1858 = _t1860
                    else:
                        if prediction1058 == 0:
                            _t1862 = self.parse_assign()
                            assign1059 = _t1862
                            _t1863 = logic_pb2.Instruction(assign=assign1059)
                            _t1861 = _t1863
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1858 = _t1861
                    _t1855 = _t1858
                _t1852 = _t1855
            _t1849 = _t1852
        result1065 = _t1849
        self.record_span(span_start1064, "Instruction")
        return result1065

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1069 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1864 = self.parse_relation_id()
        relation_id1066 = _t1864
        _t1865 = self.parse_abstraction()
        abstraction1067 = _t1865
        if self.match_lookahead_literal("(", 0):
            _t1867 = self.parse_attrs()
            _t1866 = _t1867
        else:
            _t1866 = None
        attrs1068 = _t1866
        self.consume_literal(")")
        _t1868 = logic_pb2.Assign(name=relation_id1066, body=abstraction1067, attrs=(attrs1068 if attrs1068 is not None else []))
        result1070 = _t1868
        self.record_span(span_start1069, "Assign")
        return result1070

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1074 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1869 = self.parse_relation_id()
        relation_id1071 = _t1869
        _t1870 = self.parse_abstraction_with_arity()
        abstraction_with_arity1072 = _t1870
        if self.match_lookahead_literal("(", 0):
            _t1872 = self.parse_attrs()
            _t1871 = _t1872
        else:
            _t1871 = None
        attrs1073 = _t1871
        self.consume_literal(")")
        _t1873 = logic_pb2.Upsert(name=relation_id1071, body=abstraction_with_arity1072[0], attrs=(attrs1073 if attrs1073 is not None else []), value_arity=abstraction_with_arity1072[1])
        result1075 = _t1873
        self.record_span(span_start1074, "Upsert")
        return result1075

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1874 = self.parse_bindings()
        bindings1076 = _t1874
        _t1875 = self.parse_formula()
        formula1077 = _t1875
        self.consume_literal(")")
        _t1876 = logic_pb2.Abstraction(vars=(list(bindings1076[0]) + list(bindings1076[1] if bindings1076[1] is not None else [])), value=formula1077)
        return (_t1876, len(bindings1076[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1081 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1877 = self.parse_relation_id()
        relation_id1078 = _t1877
        _t1878 = self.parse_abstraction()
        abstraction1079 = _t1878
        if self.match_lookahead_literal("(", 0):
            _t1880 = self.parse_attrs()
            _t1879 = _t1880
        else:
            _t1879 = None
        attrs1080 = _t1879
        self.consume_literal(")")
        _t1881 = logic_pb2.Break(name=relation_id1078, body=abstraction1079, attrs=(attrs1080 if attrs1080 is not None else []))
        result1082 = _t1881
        self.record_span(span_start1081, "Break")
        return result1082

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1087 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1882 = self.parse_monoid()
        monoid1083 = _t1882
        _t1883 = self.parse_relation_id()
        relation_id1084 = _t1883
        _t1884 = self.parse_abstraction_with_arity()
        abstraction_with_arity1085 = _t1884
        if self.match_lookahead_literal("(", 0):
            _t1886 = self.parse_attrs()
            _t1885 = _t1886
        else:
            _t1885 = None
        attrs1086 = _t1885
        self.consume_literal(")")
        _t1887 = logic_pb2.MonoidDef(monoid=monoid1083, name=relation_id1084, body=abstraction_with_arity1085[0], attrs=(attrs1086 if attrs1086 is not None else []), value_arity=abstraction_with_arity1085[1])
        result1088 = _t1887
        self.record_span(span_start1087, "MonoidDef")
        return result1088

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1094 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1889 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1890 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1891 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1892 = 2
                        else:
                            _t1892 = -1
                        _t1891 = _t1892
                    _t1890 = _t1891
                _t1889 = _t1890
            _t1888 = _t1889
        else:
            _t1888 = -1
        prediction1089 = _t1888
        if prediction1089 == 3:
            _t1894 = self.parse_sum_monoid()
            sum_monoid1093 = _t1894
            _t1895 = logic_pb2.Monoid(sum_monoid=sum_monoid1093)
            _t1893 = _t1895
        else:
            if prediction1089 == 2:
                _t1897 = self.parse_max_monoid()
                max_monoid1092 = _t1897
                _t1898 = logic_pb2.Monoid(max_monoid=max_monoid1092)
                _t1896 = _t1898
            else:
                if prediction1089 == 1:
                    _t1900 = self.parse_min_monoid()
                    min_monoid1091 = _t1900
                    _t1901 = logic_pb2.Monoid(min_monoid=min_monoid1091)
                    _t1899 = _t1901
                else:
                    if prediction1089 == 0:
                        _t1903 = self.parse_or_monoid()
                        or_monoid1090 = _t1903
                        _t1904 = logic_pb2.Monoid(or_monoid=or_monoid1090)
                        _t1902 = _t1904
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1899 = _t1902
                _t1896 = _t1899
            _t1893 = _t1896
        result1095 = _t1893
        self.record_span(span_start1094, "Monoid")
        return result1095

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1096 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1905 = logic_pb2.OrMonoid()
        result1097 = _t1905
        self.record_span(span_start1096, "OrMonoid")
        return result1097

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1099 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1906 = self.parse_type()
        type1098 = _t1906
        self.consume_literal(")")
        _t1907 = logic_pb2.MinMonoid(type=type1098)
        result1100 = _t1907
        self.record_span(span_start1099, "MinMonoid")
        return result1100

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1102 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1908 = self.parse_type()
        type1101 = _t1908
        self.consume_literal(")")
        _t1909 = logic_pb2.MaxMonoid(type=type1101)
        result1103 = _t1909
        self.record_span(span_start1102, "MaxMonoid")
        return result1103

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1105 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1910 = self.parse_type()
        type1104 = _t1910
        self.consume_literal(")")
        _t1911 = logic_pb2.SumMonoid(type=type1104)
        result1106 = _t1911
        self.record_span(span_start1105, "SumMonoid")
        return result1106

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1111 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1912 = self.parse_monoid()
        monoid1107 = _t1912
        _t1913 = self.parse_relation_id()
        relation_id1108 = _t1913
        _t1914 = self.parse_abstraction_with_arity()
        abstraction_with_arity1109 = _t1914
        if self.match_lookahead_literal("(", 0):
            _t1916 = self.parse_attrs()
            _t1915 = _t1916
        else:
            _t1915 = None
        attrs1110 = _t1915
        self.consume_literal(")")
        _t1917 = logic_pb2.MonusDef(monoid=monoid1107, name=relation_id1108, body=abstraction_with_arity1109[0], attrs=(attrs1110 if attrs1110 is not None else []), value_arity=abstraction_with_arity1109[1])
        result1112 = _t1917
        self.record_span(span_start1111, "MonusDef")
        return result1112

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1117 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1918 = self.parse_relation_id()
        relation_id1113 = _t1918
        _t1919 = self.parse_abstraction()
        abstraction1114 = _t1919
        _t1920 = self.parse_functional_dependency_keys()
        functional_dependency_keys1115 = _t1920
        _t1921 = self.parse_functional_dependency_values()
        functional_dependency_values1116 = _t1921
        self.consume_literal(")")
        _t1922 = logic_pb2.FunctionalDependency(guard=abstraction1114, keys=functional_dependency_keys1115, values=functional_dependency_values1116)
        _t1923 = logic_pb2.Constraint(name=relation_id1113, functional_dependency=_t1922)
        result1118 = _t1923
        self.record_span(span_start1117, "Constraint")
        return result1118

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1119 = []
        cond1120 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1120:
            _t1924 = self.parse_var()
            item1121 = _t1924
            xs1119.append(item1121)
            cond1120 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1122 = xs1119
        self.consume_literal(")")
        return vars1122

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1123 = []
        cond1124 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1124:
            _t1925 = self.parse_var()
            item1125 = _t1925
            xs1123.append(item1125)
            cond1124 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1126 = xs1123
        self.consume_literal(")")
        return vars1126

    def parse_data(self) -> logic_pb2.Data:
        span_start1132 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1927 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1928 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1929 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1930 = 1
                        else:
                            _t1930 = -1
                        _t1929 = _t1930
                    _t1928 = _t1929
                _t1927 = _t1928
            _t1926 = _t1927
        else:
            _t1926 = -1
        prediction1127 = _t1926
        if prediction1127 == 3:
            _t1932 = self.parse_iceberg_data()
            iceberg_data1131 = _t1932
            _t1933 = logic_pb2.Data(iceberg_data=iceberg_data1131)
            _t1931 = _t1933
        else:
            if prediction1127 == 2:
                _t1935 = self.parse_csv_data()
                csv_data1130 = _t1935
                _t1936 = logic_pb2.Data(csv_data=csv_data1130)
                _t1934 = _t1936
            else:
                if prediction1127 == 1:
                    _t1938 = self.parse_betree_relation()
                    betree_relation1129 = _t1938
                    _t1939 = logic_pb2.Data(betree_relation=betree_relation1129)
                    _t1937 = _t1939
                else:
                    if prediction1127 == 0:
                        _t1941 = self.parse_edb()
                        edb1128 = _t1941
                        _t1942 = logic_pb2.Data(edb=edb1128)
                        _t1940 = _t1942
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1937 = _t1940
                _t1934 = _t1937
            _t1931 = _t1934
        result1133 = _t1931
        self.record_span(span_start1132, "Data")
        return result1133

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1137 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1943 = self.parse_relation_id()
        relation_id1134 = _t1943
        _t1944 = self.parse_edb_path()
        edb_path1135 = _t1944
        _t1945 = self.parse_edb_types()
        edb_types1136 = _t1945
        self.consume_literal(")")
        _t1946 = logic_pb2.EDB(target_id=relation_id1134, path=edb_path1135, types=edb_types1136)
        result1138 = _t1946
        self.record_span(span_start1137, "EDB")
        return result1138

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1139 = []
        cond1140 = self.match_lookahead_terminal("STRING", 0)
        while cond1140:
            item1141 = self.consume_terminal("STRING")
            xs1139.append(item1141)
            cond1140 = self.match_lookahead_terminal("STRING", 0)
        strings1142 = xs1139
        self.consume_literal("]")
        return strings1142

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1143 = []
        cond1144 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1144:
            _t1947 = self.parse_type()
            item1145 = _t1947
            xs1143.append(item1145)
            cond1144 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1146 = xs1143
        self.consume_literal("]")
        return types1146

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1149 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1948 = self.parse_relation_id()
        relation_id1147 = _t1948
        _t1949 = self.parse_betree_info()
        betree_info1148 = _t1949
        self.consume_literal(")")
        _t1950 = logic_pb2.BeTreeRelation(name=relation_id1147, relation_info=betree_info1148)
        result1150 = _t1950
        self.record_span(span_start1149, "BeTreeRelation")
        return result1150

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1154 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1951 = self.parse_betree_info_key_types()
        betree_info_key_types1151 = _t1951
        _t1952 = self.parse_betree_info_value_types()
        betree_info_value_types1152 = _t1952
        _t1953 = self.parse_config_dict()
        config_dict1153 = _t1953
        self.consume_literal(")")
        _t1954 = self.construct_betree_info(betree_info_key_types1151, betree_info_value_types1152, config_dict1153)
        result1155 = _t1954
        self.record_span(span_start1154, "BeTreeInfo")
        return result1155

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1156 = []
        cond1157 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1157:
            _t1955 = self.parse_type()
            item1158 = _t1955
            xs1156.append(item1158)
            cond1157 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1159 = xs1156
        self.consume_literal(")")
        return types1159

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1160 = []
        cond1161 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1161:
            _t1956 = self.parse_type()
            item1162 = _t1956
            xs1160.append(item1162)
            cond1161 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1163 = xs1160
        self.consume_literal(")")
        return types1163

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1168 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1957 = self.parse_csvlocator()
        csvlocator1164 = _t1957
        _t1958 = self.parse_csv_config()
        csv_config1165 = _t1958
        _t1959 = self.parse_gnf_columns()
        gnf_columns1166 = _t1959
        _t1960 = self.parse_csv_asof()
        csv_asof1167 = _t1960
        self.consume_literal(")")
        _t1961 = logic_pb2.CSVData(locator=csvlocator1164, config=csv_config1165, columns=gnf_columns1166, asof=csv_asof1167)
        result1169 = _t1961
        self.record_span(span_start1168, "CSVData")
        return result1169

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1172 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1963 = self.parse_csv_locator_paths()
            _t1962 = _t1963
        else:
            _t1962 = None
        csv_locator_paths1170 = _t1962
        if self.match_lookahead_literal("(", 0):
            _t1965 = self.parse_csv_locator_inline_data()
            _t1964 = _t1965
        else:
            _t1964 = None
        csv_locator_inline_data1171 = _t1964
        self.consume_literal(")")
        _t1966 = logic_pb2.CSVLocator(paths=(csv_locator_paths1170 if csv_locator_paths1170 is not None else []), inline_data=(csv_locator_inline_data1171 if csv_locator_inline_data1171 is not None else "").encode())
        result1173 = _t1966
        self.record_span(span_start1172, "CSVLocator")
        return result1173

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1174 = []
        cond1175 = self.match_lookahead_terminal("STRING", 0)
        while cond1175:
            item1176 = self.consume_terminal("STRING")
            xs1174.append(item1176)
            cond1175 = self.match_lookahead_terminal("STRING", 0)
        strings1177 = xs1174
        self.consume_literal(")")
        return strings1177

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1178 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1178

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1180 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1967 = self.parse_config_dict()
        config_dict1179 = _t1967
        self.consume_literal(")")
        _t1968 = self.construct_csv_config(config_dict1179)
        result1181 = _t1968
        self.record_span(span_start1180, "CSVConfig")
        return result1181

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1182 = []
        cond1183 = self.match_lookahead_literal("(", 0)
        while cond1183:
            _t1969 = self.parse_gnf_column()
            item1184 = _t1969
            xs1182.append(item1184)
            cond1183 = self.match_lookahead_literal("(", 0)
        gnf_columns1185 = xs1182
        self.consume_literal(")")
        return gnf_columns1185

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1192 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1970 = self.parse_gnf_column_path()
        gnf_column_path1186 = _t1970
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1972 = self.parse_relation_id()
            _t1971 = _t1972
        else:
            _t1971 = None
        relation_id1187 = _t1971
        self.consume_literal("[")
        xs1188 = []
        cond1189 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1189:
            _t1973 = self.parse_type()
            item1190 = _t1973
            xs1188.append(item1190)
            cond1189 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1191 = xs1188
        self.consume_literal("]")
        self.consume_literal(")")
        _t1974 = logic_pb2.GNFColumn(column_path=gnf_column_path1186, target_id=relation_id1187, types=types1191)
        result1193 = _t1974
        self.record_span(span_start1192, "GNFColumn")
        return result1193

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1975 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1976 = 0
            else:
                _t1976 = -1
            _t1975 = _t1976
        prediction1194 = _t1975
        if prediction1194 == 1:
            self.consume_literal("[")
            xs1196 = []
            cond1197 = self.match_lookahead_terminal("STRING", 0)
            while cond1197:
                item1198 = self.consume_terminal("STRING")
                xs1196.append(item1198)
                cond1197 = self.match_lookahead_terminal("STRING", 0)
            strings1199 = xs1196
            self.consume_literal("]")
            _t1977 = strings1199
        else:
            if prediction1194 == 0:
                string1195 = self.consume_terminal("STRING")
                _t1978 = [string1195]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1977 = _t1978
        return _t1977

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1200 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1200

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1207 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1979 = self.parse_iceberg_locator()
        iceberg_locator1201 = _t1979
        _t1980 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1202 = _t1980
        _t1981 = self.parse_gnf_columns()
        gnf_columns1203 = _t1981
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t1983 = self.parse_iceberg_from_snapshot()
            _t1982 = _t1983
        else:
            _t1982 = None
        iceberg_from_snapshot1204 = _t1982
        if self.match_lookahead_literal("(", 0):
            _t1985 = self.parse_iceberg_to_snapshot()
            _t1984 = _t1985
        else:
            _t1984 = None
        iceberg_to_snapshot1205 = _t1984
        _t1986 = self.parse_boolean_value()
        boolean_value1206 = _t1986
        self.consume_literal(")")
        _t1987 = self.construct_iceberg_data(iceberg_locator1201, iceberg_catalog_config1202, gnf_columns1203, iceberg_from_snapshot1204, iceberg_to_snapshot1205, boolean_value1206)
        result1208 = _t1987
        self.record_span(span_start1207, "IcebergData")
        return result1208

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1212 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t1988 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1209 = _t1988
        _t1989 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1210 = _t1989
        _t1990 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1211 = _t1990
        self.consume_literal(")")
        _t1991 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1209, namespace=iceberg_locator_namespace1210, warehouse=iceberg_locator_warehouse1211)
        result1213 = _t1991
        self.record_span(span_start1212, "IcebergLocator")
        return result1213

    def parse_iceberg_locator_table_name(self) -> str:
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1214 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1214

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1215 = []
        cond1216 = self.match_lookahead_terminal("STRING", 0)
        while cond1216:
            item1217 = self.consume_terminal("STRING")
            xs1215.append(item1217)
            cond1216 = self.match_lookahead_terminal("STRING", 0)
        strings1218 = xs1215
        self.consume_literal(")")
        return strings1218

    def parse_iceberg_locator_warehouse(self) -> str:
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string1219 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1219

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1224 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t1992 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1220 = _t1992
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t1994 = self.parse_iceberg_catalog_config_scope()
            _t1993 = _t1994
        else:
            _t1993 = None
        iceberg_catalog_config_scope1221 = _t1993
        _t1995 = self.parse_iceberg_properties()
        iceberg_properties1222 = _t1995
        _t1996 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1223 = _t1996
        self.consume_literal(")")
        _t1997 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1220, iceberg_catalog_config_scope1221, iceberg_properties1222, iceberg_auth_properties1223)
        result1225 = _t1997
        self.record_span(span_start1224, "IcebergCatalogConfig")
        return result1225

    def parse_iceberg_catalog_uri(self) -> str:
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1226 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1226

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1227 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1227

    def parse_iceberg_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1228 = []
        cond1229 = self.match_lookahead_literal("(", 0)
        while cond1229:
            _t1998 = self.parse_iceberg_property_entry()
            item1230 = _t1998
            xs1228.append(item1230)
            cond1229 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1231 = xs1228
        self.consume_literal(")")
        return iceberg_property_entrys1231

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1232 = self.consume_terminal("STRING")
        string_31233 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1232, string_31233,)

    def parse_iceberg_auth_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1234 = []
        cond1235 = self.match_lookahead_literal("(", 0)
        while cond1235:
            _t1999 = self.parse_iceberg_masked_property_entry()
            item1236 = _t1999
            xs1234.append(item1236)
            cond1235 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1237 = xs1234
        self.consume_literal(")")
        return iceberg_masked_property_entrys1237

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1238 = self.consume_terminal("STRING")
        string_31239 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1238, string_31239,)

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1240 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1240

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1241 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1241

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1243 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2000 = self.parse_fragment_id()
        fragment_id1242 = _t2000
        self.consume_literal(")")
        _t2001 = transactions_pb2.Undefine(fragment_id=fragment_id1242)
        result1244 = _t2001
        self.record_span(span_start1243, "Undefine")
        return result1244

    def parse_context(self) -> transactions_pb2.Context:
        span_start1249 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1245 = []
        cond1246 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1246:
            _t2002 = self.parse_relation_id()
            item1247 = _t2002
            xs1245.append(item1247)
            cond1246 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1248 = xs1245
        self.consume_literal(")")
        _t2003 = transactions_pb2.Context(relations=relation_ids1248)
        result1250 = _t2003
        self.record_span(span_start1249, "Context")
        return result1250

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1255 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        xs1251 = []
        cond1252 = self.match_lookahead_literal("[", 0)
        while cond1252:
            _t2004 = self.parse_snapshot_mapping()
            item1253 = _t2004
            xs1251.append(item1253)
            cond1252 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1254 = xs1251
        self.consume_literal(")")
        _t2005 = transactions_pb2.Snapshot(mappings=snapshot_mappings1254)
        result1256 = _t2005
        self.record_span(span_start1255, "Snapshot")
        return result1256

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1259 = self.span_start()
        _t2006 = self.parse_edb_path()
        edb_path1257 = _t2006
        _t2007 = self.parse_relation_id()
        relation_id1258 = _t2007
        _t2008 = transactions_pb2.SnapshotMapping(destination_path=edb_path1257, source_relation=relation_id1258)
        result1260 = _t2008
        self.record_span(span_start1259, "SnapshotMapping")
        return result1260

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1261 = []
        cond1262 = self.match_lookahead_literal("(", 0)
        while cond1262:
            _t2009 = self.parse_read()
            item1263 = _t2009
            xs1261.append(item1263)
            cond1262 = self.match_lookahead_literal("(", 0)
        reads1264 = xs1261
        self.consume_literal(")")
        return reads1264

    def parse_read(self) -> transactions_pb2.Read:
        span_start1271 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2011 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2012 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t2013 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t2014 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t2015 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t2016 = 3
                                else:
                                    _t2016 = -1
                                _t2015 = _t2016
                            _t2014 = _t2015
                        _t2013 = _t2014
                    _t2012 = _t2013
                _t2011 = _t2012
            _t2010 = _t2011
        else:
            _t2010 = -1
        prediction1265 = _t2010
        if prediction1265 == 4:
            _t2018 = self.parse_export()
            export1270 = _t2018
            _t2019 = transactions_pb2.Read(export=export1270)
            _t2017 = _t2019
        else:
            if prediction1265 == 3:
                _t2021 = self.parse_abort()
                abort1269 = _t2021
                _t2022 = transactions_pb2.Read(abort=abort1269)
                _t2020 = _t2022
            else:
                if prediction1265 == 2:
                    _t2024 = self.parse_what_if()
                    what_if1268 = _t2024
                    _t2025 = transactions_pb2.Read(what_if=what_if1268)
                    _t2023 = _t2025
                else:
                    if prediction1265 == 1:
                        _t2027 = self.parse_output()
                        output1267 = _t2027
                        _t2028 = transactions_pb2.Read(output=output1267)
                        _t2026 = _t2028
                    else:
                        if prediction1265 == 0:
                            _t2030 = self.parse_demand()
                            demand1266 = _t2030
                            _t2031 = transactions_pb2.Read(demand=demand1266)
                            _t2029 = _t2031
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2026 = _t2029
                    _t2023 = _t2026
                _t2020 = _t2023
            _t2017 = _t2020
        result1272 = _t2017
        self.record_span(span_start1271, "Read")
        return result1272

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1274 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2032 = self.parse_relation_id()
        relation_id1273 = _t2032
        self.consume_literal(")")
        _t2033 = transactions_pb2.Demand(relation_id=relation_id1273)
        result1275 = _t2033
        self.record_span(span_start1274, "Demand")
        return result1275

    def parse_output(self) -> transactions_pb2.Output:
        span_start1278 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2034 = self.parse_name()
        name1276 = _t2034
        _t2035 = self.parse_relation_id()
        relation_id1277 = _t2035
        self.consume_literal(")")
        _t2036 = transactions_pb2.Output(name=name1276, relation_id=relation_id1277)
        result1279 = _t2036
        self.record_span(span_start1278, "Output")
        return result1279

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1282 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2037 = self.parse_name()
        name1280 = _t2037
        _t2038 = self.parse_epoch()
        epoch1281 = _t2038
        self.consume_literal(")")
        _t2039 = transactions_pb2.WhatIf(branch=name1280, epoch=epoch1281)
        result1283 = _t2039
        self.record_span(span_start1282, "WhatIf")
        return result1283

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1286 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2041 = self.parse_name()
            _t2040 = _t2041
        else:
            _t2040 = None
        name1284 = _t2040
        _t2042 = self.parse_relation_id()
        relation_id1285 = _t2042
        self.consume_literal(")")
        _t2043 = transactions_pb2.Abort(name=(name1284 if name1284 is not None else "abort"), relation_id=relation_id1285)
        result1287 = _t2043
        self.record_span(span_start1286, "Abort")
        return result1287

    def parse_export(self) -> transactions_pb2.Export:
        span_start1291 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2045 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2046 = 0
                else:
                    _t2046 = -1
                _t2045 = _t2046
            _t2044 = _t2045
        else:
            _t2044 = -1
        prediction1288 = _t2044
        if prediction1288 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2048 = self.parse_export_iceberg_config()
            export_iceberg_config1290 = _t2048
            self.consume_literal(")")
            _t2049 = transactions_pb2.Export(iceberg_config=export_iceberg_config1290)
            _t2047 = _t2049
        else:
            if prediction1288 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2051 = self.parse_export_csv_config()
                export_csv_config1289 = _t2051
                self.consume_literal(")")
                _t2052 = transactions_pb2.Export(csv_config=export_csv_config1289)
                _t2050 = _t2052
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2047 = _t2050
        result1292 = _t2047
        self.record_span(span_start1291, "Export")
        return result1292

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1300 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2054 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2055 = 1
                else:
                    _t2055 = -1
                _t2054 = _t2055
            _t2053 = _t2054
        else:
            _t2053 = -1
        prediction1293 = _t2053
        if prediction1293 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2057 = self.parse_export_csv_path()
            export_csv_path1297 = _t2057
            _t2058 = self.parse_export_csv_columns_list()
            export_csv_columns_list1298 = _t2058
            _t2059 = self.parse_config_dict()
            config_dict1299 = _t2059
            self.consume_literal(")")
            _t2060 = self.construct_export_csv_config(export_csv_path1297, export_csv_columns_list1298, config_dict1299)
            _t2056 = _t2060
        else:
            if prediction1293 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2062 = self.parse_export_csv_path()
                export_csv_path1294 = _t2062
                _t2063 = self.parse_export_csv_source()
                export_csv_source1295 = _t2063
                _t2064 = self.parse_csv_config()
                csv_config1296 = _t2064
                self.consume_literal(")")
                _t2065 = self.construct_export_csv_config_with_source(export_csv_path1294, export_csv_source1295, csv_config1296)
                _t2061 = _t2065
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2056 = _t2061
        result1301 = _t2056
        self.record_span(span_start1300, "ExportCSVConfig")
        return result1301

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1302 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1302

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1309 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2067 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2068 = 0
                else:
                    _t2068 = -1
                _t2067 = _t2068
            _t2066 = _t2067
        else:
            _t2066 = -1
        prediction1303 = _t2066
        if prediction1303 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2070 = self.parse_relation_id()
            relation_id1308 = _t2070
            self.consume_literal(")")
            _t2071 = transactions_pb2.ExportCSVSource(table_def=relation_id1308)
            _t2069 = _t2071
        else:
            if prediction1303 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1304 = []
                cond1305 = self.match_lookahead_literal("(", 0)
                while cond1305:
                    _t2073 = self.parse_export_csv_column()
                    item1306 = _t2073
                    xs1304.append(item1306)
                    cond1305 = self.match_lookahead_literal("(", 0)
                export_csv_columns1307 = xs1304
                self.consume_literal(")")
                _t2074 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1307)
                _t2075 = transactions_pb2.ExportCSVSource(gnf_columns=_t2074)
                _t2072 = _t2075
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2069 = _t2072
        result1310 = _t2069
        self.record_span(span_start1309, "ExportCSVSource")
        return result1310

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1313 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1311 = self.consume_terminal("STRING")
        _t2076 = self.parse_relation_id()
        relation_id1312 = _t2076
        self.consume_literal(")")
        _t2077 = transactions_pb2.ExportCSVColumn(column_name=string1311, column_data=relation_id1312)
        result1314 = _t2077
        self.record_span(span_start1313, "ExportCSVColumn")
        return result1314

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1315 = []
        cond1316 = self.match_lookahead_literal("(", 0)
        while cond1316:
            _t2078 = self.parse_export_csv_column()
            item1317 = _t2078
            xs1315.append(item1317)
            cond1316 = self.match_lookahead_literal("(", 0)
        export_csv_columns1318 = xs1315
        self.consume_literal(")")
        return export_csv_columns1318

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1325 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2079 = self.parse_iceberg_locator()
        iceberg_locator1319 = _t2079
        _t2080 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1320 = _t2080
        _t2081 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1321 = _t2081
        _t2082 = self.parse_export_iceberg_columns()
        export_iceberg_columns1322 = _t2082
        _t2083 = self.parse_iceberg_table_properties()
        iceberg_table_properties1323 = _t2083
        if self.match_lookahead_literal("{", 0):
            _t2085 = self.parse_config_dict()
            _t2084 = _t2085
        else:
            _t2084 = None
        config_dict1324 = _t2084
        self.consume_literal(")")
        _t2086 = self.construct_export_iceberg_config_full(iceberg_locator1319, iceberg_catalog_config1320, export_iceberg_table_def1321, export_iceberg_columns1322, iceberg_table_properties1323, config_dict1324)
        result1326 = _t2086
        self.record_span(span_start1325, "ExportIcebergConfig")
        return result1326

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1328 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2087 = self.parse_relation_id()
        relation_id1327 = _t2087
        self.consume_literal(")")
        result1329 = relation_id1327
        self.record_span(span_start1328, "RelationId")
        return result1329

    def parse_export_iceberg_columns(self) -> Sequence[transactions_pb2.ExportColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1330 = []
        cond1331 = self.match_lookahead_literal("(", 0)
        while cond1331:
            _t2088 = self.parse_export_iceberg_column()
            item1332 = _t2088
            xs1330.append(item1332)
            cond1331 = self.match_lookahead_literal("(", 0)
        export_iceberg_columns1333 = xs1330
        self.consume_literal(")")
        return export_iceberg_columns1333

    def parse_export_iceberg_column(self) -> transactions_pb2.ExportColumn:
        span_start1336 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1334 = self.consume_terminal("STRING")
        _t2089 = self.parse_boolean_value()
        boolean_value1335 = _t2089
        self.consume_literal(")")
        _t2090 = transactions_pb2.ExportColumn(name=string1334, nullable=boolean_value1335)
        result1337 = _t2090
        self.record_span(span_start1336, "ExportColumn")
        return result1337

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1338 = []
        cond1339 = self.match_lookahead_literal("(", 0)
        while cond1339:
            _t2091 = self.parse_iceberg_property_entry()
            item1340 = _t2091
            xs1338.append(item1340)
            cond1339 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1341 = xs1338
        self.consume_literal(")")
        return iceberg_property_entrys1341


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
