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
            _t2095 = value.HasField("int32_value")
        else:
            _t2095 = False
        if _t2095:
            assert value is not None
            return value.int32_value
        else:
            _t2096 = None
        return int(default)

    def _extract_value_int64(self, value: logic_pb2.Value | None, default: int) -> int:
        if value is not None:
            assert value is not None
            _t2097 = value.HasField("int_value")
        else:
            _t2097 = False
        if _t2097:
            assert value is not None
            return value.int_value
        else:
            _t2098 = None
        return default

    def _extract_value_string(self, value: logic_pb2.Value | None, default: str) -> str:
        if value is not None:
            assert value is not None
            _t2099 = value.HasField("string_value")
        else:
            _t2099 = False
        if _t2099:
            assert value is not None
            return value.string_value
        else:
            _t2100 = None
        return default

    def _extract_value_boolean(self, value: logic_pb2.Value | None, default: bool) -> bool:
        if value is not None:
            assert value is not None
            _t2101 = value.HasField("boolean_value")
        else:
            _t2101 = False
        if _t2101:
            assert value is not None
            return value.boolean_value
        else:
            _t2102 = None
        return default

    def _extract_value_string_list(self, value: logic_pb2.Value | None, default: Sequence[str]) -> Sequence[str]:
        if value is not None:
            assert value is not None
            _t2103 = value.HasField("string_value")
        else:
            _t2103 = False
        if _t2103:
            assert value is not None
            return [value.string_value]
        else:
            _t2104 = None
        return default

    def _try_extract_value_int64(self, value: logic_pb2.Value | None) -> int | None:
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
        return None

    def _try_extract_value_float64(self, value: logic_pb2.Value | None) -> float | None:
        if value is not None:
            assert value is not None
            _t2107 = value.HasField("float_value")
        else:
            _t2107 = False
        if _t2107:
            assert value is not None
            return value.float_value
        else:
            _t2108 = None
        return None

    def _try_extract_value_bytes(self, value: logic_pb2.Value | None) -> bytes | None:
        if value is not None:
            assert value is not None
            _t2109 = value.HasField("string_value")
        else:
            _t2109 = False
        if _t2109:
            assert value is not None
            return value.string_value.encode()
        else:
            _t2110 = None
        return None

    def _try_extract_value_uint128(self, value: logic_pb2.Value | None) -> logic_pb2.UInt128Value | None:
        if value is not None:
            assert value is not None
            _t2111 = value.HasField("uint128_value")
        else:
            _t2111 = False
        if _t2111:
            assert value is not None
            return value.uint128_value
        else:
            _t2112 = None
        return None

    def construct_csv_config(self, config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.CSVConfig:
        config = dict(config_dict)
        _t2113 = self._extract_value_int32(config.get("csv_header_row"), 1)
        header_row = _t2113
        _t2114 = self._extract_value_int64(config.get("csv_skip"), 0)
        skip = _t2114
        _t2115 = self._extract_value_string(config.get("csv_new_line"), "")
        new_line = _t2115
        _t2116 = self._extract_value_string(config.get("csv_delimiter"), ",")
        delimiter = _t2116
        _t2117 = self._extract_value_string(config.get("csv_quotechar"), '"')
        quotechar = _t2117
        _t2118 = self._extract_value_string(config.get("csv_escapechar"), '"')
        escapechar = _t2118
        _t2119 = self._extract_value_string(config.get("csv_comment"), "")
        comment = _t2119
        _t2120 = self._extract_value_string_list(config.get("csv_missing_strings"), [])
        missing_strings = _t2120
        _t2121 = self._extract_value_string(config.get("csv_decimal_separator"), ".")
        decimal_separator = _t2121
        _t2122 = self._extract_value_string(config.get("csv_encoding"), "utf-8")
        encoding = _t2122
        _t2123 = self._extract_value_string(config.get("csv_compression"), "auto")
        compression = _t2123
        _t2124 = self._extract_value_int64(config.get("csv_partition_size_mb"), 0)
        partition_size_mb = _t2124
        _t2125 = logic_pb2.CSVConfig(header_row=header_row, skip=skip, new_line=new_line, delimiter=delimiter, quotechar=quotechar, escapechar=escapechar, comment=comment, missing_strings=missing_strings, decimal_separator=decimal_separator, encoding=encoding, compression=compression, partition_size_mb=partition_size_mb)
        return _t2125

    def construct_betree_info(self, key_types: Sequence[logic_pb2.Type], value_types: Sequence[logic_pb2.Type], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> logic_pb2.BeTreeInfo:
        config = dict(config_dict)
        _t2126 = self._try_extract_value_float64(config.get("betree_config_epsilon"))
        epsilon = _t2126
        _t2127 = self._try_extract_value_int64(config.get("betree_config_max_pivots"))
        max_pivots = _t2127
        _t2128 = self._try_extract_value_int64(config.get("betree_config_max_deltas"))
        max_deltas = _t2128
        _t2129 = self._try_extract_value_int64(config.get("betree_config_max_leaf"))
        max_leaf = _t2129
        _t2130 = logic_pb2.BeTreeConfig(epsilon=epsilon, max_pivots=max_pivots, max_deltas=max_deltas, max_leaf=max_leaf)
        storage_config = _t2130
        _t2131 = self._try_extract_value_uint128(config.get("betree_locator_root_pageid"))
        root_pageid = _t2131
        _t2132 = self._try_extract_value_bytes(config.get("betree_locator_inline_data"))
        inline_data = _t2132
        _t2133 = self._try_extract_value_int64(config.get("betree_locator_element_count"))
        element_count = _t2133
        _t2134 = self._try_extract_value_int64(config.get("betree_locator_tree_height"))
        tree_height = _t2134
        _t2135 = logic_pb2.BeTreeLocator(root_pageid=root_pageid, inline_data=inline_data, element_count=element_count, tree_height=tree_height)
        relation_locator = _t2135
        _t2136 = logic_pb2.BeTreeInfo(key_types=key_types, value_types=value_types, storage_config=storage_config, relation_locator=relation_locator)
        return _t2136

    def default_configure(self) -> transactions_pb2.Configure:
        _t2137 = transactions_pb2.IVMConfig(level=transactions_pb2.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
        ivm_config = _t2137
        _t2138 = transactions_pb2.Configure(semantics_version=0, ivm_config=ivm_config)
        return _t2138

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
        _t2139 = transactions_pb2.IVMConfig(level=maintenance_level)
        ivm_config = _t2139
        _t2140 = self._extract_value_int64(config.get("semantics_version"), 0)
        semantics_version = _t2140
        _t2141 = transactions_pb2.Configure(semantics_version=semantics_version, ivm_config=ivm_config)
        return _t2141

    def construct_export_csv_config(self, path: str, columns: Sequence[transactions_pb2.ExportCSVColumn], config_dict: Sequence[tuple[str, logic_pb2.Value]]) -> transactions_pb2.ExportCSVConfig:
        config = dict(config_dict)
        _t2142 = self._extract_value_int64(config.get("partition_size"), 0)
        partition_size = _t2142
        _t2143 = self._extract_value_string(config.get("compression"), "")
        compression = _t2143
        _t2144 = self._extract_value_boolean(config.get("syntax_header_row"), True)
        syntax_header_row = _t2144
        _t2145 = self._extract_value_string(config.get("syntax_missing_string"), "")
        syntax_missing_string = _t2145
        _t2146 = self._extract_value_string(config.get("syntax_delim"), ",")
        syntax_delim = _t2146
        _t2147 = self._extract_value_string(config.get("syntax_quotechar"), '"')
        syntax_quotechar = _t2147
        _t2148 = self._extract_value_string(config.get("syntax_escapechar"), "\\")
        syntax_escapechar = _t2148
        _t2149 = transactions_pb2.ExportCSVConfig(path=path, data_columns=columns, partition_size=partition_size, compression=compression, syntax_header_row=syntax_header_row, syntax_missing_string=syntax_missing_string, syntax_delim=syntax_delim, syntax_quotechar=syntax_quotechar, syntax_escapechar=syntax_escapechar)
        return _t2149

    def construct_export_csv_config_with_source(self, path: str, csv_source: transactions_pb2.ExportCSVSource, csv_config: logic_pb2.CSVConfig) -> transactions_pb2.ExportCSVConfig:
        _t2150 = transactions_pb2.ExportCSVConfig(path=path, csv_source=csv_source, csv_config=csv_config)
        return _t2150

    def construct_iceberg_catalog_config(self, catalog_uri: str, scope_opt: str | None, property_pairs: Sequence[tuple[str, str]], auth_property_pairs: Sequence[tuple[str, str]]) -> logic_pb2.IcebergCatalogConfig:
        props = dict(property_pairs)
        auth_props = dict(auth_property_pairs)
        _t2151 = logic_pb2.IcebergCatalogConfig(catalog_uri=catalog_uri, scope=(scope_opt if scope_opt is not None else ""), properties=props, auth_properties=auth_props)
        return _t2151

    def construct_iceberg_data(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, columns: Sequence[logic_pb2.GNFColumn], from_snapshot_opt: str | None, to_snapshot_opt: str | None, returns_delta: bool) -> logic_pb2.IcebergData:
        _t2152 = logic_pb2.IcebergData(locator=locator, config=config, columns=columns, from_snapshot=(from_snapshot_opt if from_snapshot_opt is not None else ""), to_snapshot=(to_snapshot_opt if to_snapshot_opt is not None else ""), returns_delta=returns_delta)
        return _t2152

    def construct_export_iceberg_config_full(self, locator: logic_pb2.IcebergLocator, config: logic_pb2.IcebergCatalogConfig, table_def: logic_pb2.RelationId, columns: Sequence[transactions_pb2.ExportColumn], table_property_pairs: Sequence[tuple[str, str]], config_dict: Sequence[tuple[str, logic_pb2.Value]] | None) -> transactions_pb2.ExportIcebergConfig:
        cfg = dict((config_dict if config_dict is not None else []))
        _t2153 = self._extract_value_string(cfg.get("prefix"), "")
        prefix = _t2153
        _t2154 = self._extract_value_int64(cfg.get("target_file_size_bytes"), 0)
        target_file_size_bytes = _t2154
        _t2155 = self._extract_value_string(cfg.get("compression"), "")
        compression = _t2155
        table_props = dict(table_property_pairs)
        _t2156 = transactions_pb2.ExportIcebergConfig(locator=locator, config=config, table_def=table_def, columns=columns, prefix=prefix, target_file_size_bytes=target_file_size_bytes, compression=compression, table_properties=table_props)
        return _t2156

    # --- Parse methods ---

    def parse_transaction(self) -> transactions_pb2.Transaction:
        span_start678 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("transaction")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("configure", 1)):
            _t1345 = self.parse_configure()
            _t1344 = _t1345
        else:
            _t1344 = None
        configure672 = _t1344
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("sync", 1)):
            _t1347 = self.parse_sync()
            _t1346 = _t1347
        else:
            _t1346 = None
        sync673 = _t1346
        xs674 = []
        cond675 = self.match_lookahead_literal("(", 0)
        while cond675:
            _t1348 = self.parse_epoch()
            item676 = _t1348
            xs674.append(item676)
            cond675 = self.match_lookahead_literal("(", 0)
        epochs677 = xs674
        self.consume_literal(")")
        _t1349 = self.default_configure()
        _t1350 = transactions_pb2.Transaction(epochs=epochs677, configure=(configure672 if configure672 is not None else _t1349), sync=sync673)
        result679 = _t1350
        self.record_span(span_start678, "Transaction")
        return result679

    def parse_configure(self) -> transactions_pb2.Configure:
        span_start681 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("configure")
        _t1351 = self.parse_config_dict()
        config_dict680 = _t1351
        self.consume_literal(")")
        _t1352 = self.construct_configure(config_dict680)
        result682 = _t1352
        self.record_span(span_start681, "Configure")
        return result682

    def parse_config_dict(self) -> Sequence[tuple[str, logic_pb2.Value]]:
        self.consume_literal("{")
        xs683 = []
        cond684 = self.match_lookahead_literal(":", 0)
        while cond684:
            _t1353 = self.parse_config_key_value()
            item685 = _t1353
            xs683.append(item685)
            cond684 = self.match_lookahead_literal(":", 0)
        config_key_values686 = xs683
        self.consume_literal("}")
        return config_key_values686

    def parse_config_key_value(self) -> tuple[str, logic_pb2.Value]:
        self.consume_literal(":")
        symbol687 = self.consume_terminal("SYMBOL")
        _t1354 = self.parse_raw_value()
        raw_value688 = _t1354
        return (symbol687, raw_value688,)

    def parse_raw_value(self) -> logic_pb2.Value:
        span_start702 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1355 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1356 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1357 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1359 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1360 = 0
                            else:
                                _t1360 = -1
                            _t1359 = _t1360
                        _t1358 = _t1359
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1361 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1362 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1363 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1364 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1365 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1366 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1367 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1368 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1369 = 10
                                                        else:
                                                            _t1369 = -1
                                                        _t1368 = _t1369
                                                    _t1367 = _t1368
                                                _t1366 = _t1367
                                            _t1365 = _t1366
                                        _t1364 = _t1365
                                    _t1363 = _t1364
                                _t1362 = _t1363
                            _t1361 = _t1362
                        _t1358 = _t1361
                    _t1357 = _t1358
                _t1356 = _t1357
            _t1355 = _t1356
        prediction689 = _t1355
        if prediction689 == 12:
            _t1371 = self.parse_boolean_value()
            boolean_value701 = _t1371
            _t1372 = logic_pb2.Value(boolean_value=boolean_value701)
            _t1370 = _t1372
        else:
            if prediction689 == 11:
                self.consume_literal("missing")
                _t1374 = logic_pb2.MissingValue()
                _t1375 = logic_pb2.Value(missing_value=_t1374)
                _t1373 = _t1375
            else:
                if prediction689 == 10:
                    decimal700 = self.consume_terminal("DECIMAL")
                    _t1377 = logic_pb2.Value(decimal_value=decimal700)
                    _t1376 = _t1377
                else:
                    if prediction689 == 9:
                        int128699 = self.consume_terminal("INT128")
                        _t1379 = logic_pb2.Value(int128_value=int128699)
                        _t1378 = _t1379
                    else:
                        if prediction689 == 8:
                            uint128698 = self.consume_terminal("UINT128")
                            _t1381 = logic_pb2.Value(uint128_value=uint128698)
                            _t1380 = _t1381
                        else:
                            if prediction689 == 7:
                                uint32697 = self.consume_terminal("UINT32")
                                _t1383 = logic_pb2.Value(uint32_value=uint32697)
                                _t1382 = _t1383
                            else:
                                if prediction689 == 6:
                                    float696 = self.consume_terminal("FLOAT")
                                    _t1385 = logic_pb2.Value(float_value=float696)
                                    _t1384 = _t1385
                                else:
                                    if prediction689 == 5:
                                        float32695 = self.consume_terminal("FLOAT32")
                                        _t1387 = logic_pb2.Value(float32_value=float32695)
                                        _t1386 = _t1387
                                    else:
                                        if prediction689 == 4:
                                            int694 = self.consume_terminal("INT")
                                            _t1389 = logic_pb2.Value(int_value=int694)
                                            _t1388 = _t1389
                                        else:
                                            if prediction689 == 3:
                                                int32693 = self.consume_terminal("INT32")
                                                _t1391 = logic_pb2.Value(int32_value=int32693)
                                                _t1390 = _t1391
                                            else:
                                                if prediction689 == 2:
                                                    string692 = self.consume_terminal("STRING")
                                                    _t1393 = logic_pb2.Value(string_value=string692)
                                                    _t1392 = _t1393
                                                else:
                                                    if prediction689 == 1:
                                                        _t1395 = self.parse_raw_datetime()
                                                        raw_datetime691 = _t1395
                                                        _t1396 = logic_pb2.Value(datetime_value=raw_datetime691)
                                                        _t1394 = _t1396
                                                    else:
                                                        if prediction689 == 0:
                                                            _t1398 = self.parse_raw_date()
                                                            raw_date690 = _t1398
                                                            _t1399 = logic_pb2.Value(date_value=raw_date690)
                                                            _t1397 = _t1399
                                                        else:
                                                            raise ParseError("Unexpected token in raw_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1394 = _t1397
                                                    _t1392 = _t1394
                                                _t1390 = _t1392
                                            _t1388 = _t1390
                                        _t1386 = _t1388
                                    _t1384 = _t1386
                                _t1382 = _t1384
                            _t1380 = _t1382
                        _t1378 = _t1380
                    _t1376 = _t1378
                _t1373 = _t1376
            _t1370 = _t1373
        result703 = _t1370
        self.record_span(span_start702, "Value")
        return result703

    def parse_raw_date(self) -> logic_pb2.DateValue:
        span_start707 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        int704 = self.consume_terminal("INT")
        int_3705 = self.consume_terminal("INT")
        int_4706 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1400 = logic_pb2.DateValue(year=int(int704), month=int(int_3705), day=int(int_4706))
        result708 = _t1400
        self.record_span(span_start707, "DateValue")
        return result708

    def parse_raw_datetime(self) -> logic_pb2.DateTimeValue:
        span_start716 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        int709 = self.consume_terminal("INT")
        int_3710 = self.consume_terminal("INT")
        int_4711 = self.consume_terminal("INT")
        int_5712 = self.consume_terminal("INT")
        int_6713 = self.consume_terminal("INT")
        int_7714 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1401 = self.consume_terminal("INT")
        else:
            _t1401 = None
        int_8715 = _t1401
        self.consume_literal(")")
        _t1402 = logic_pb2.DateTimeValue(year=int(int709), month=int(int_3710), day=int(int_4711), hour=int(int_5712), minute=int(int_6713), second=int(int_7714), microsecond=int((int_8715 if int_8715 is not None else 0)))
        result717 = _t1402
        self.record_span(span_start716, "DateTimeValue")
        return result717

    def parse_boolean_value(self) -> bool:
        if self.match_lookahead_literal("true", 0):
            _t1403 = 0
        else:
            if self.match_lookahead_literal("false", 0):
                _t1404 = 1
            else:
                _t1404 = -1
            _t1403 = _t1404
        prediction718 = _t1403
        if prediction718 == 1:
            self.consume_literal("false")
            _t1405 = False
        else:
            if prediction718 == 0:
                self.consume_literal("true")
                _t1406 = True
            else:
                raise ParseError("Unexpected token in boolean_value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1405 = _t1406
        return _t1405

    def parse_sync(self) -> transactions_pb2.Sync:
        span_start723 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sync")
        xs719 = []
        cond720 = self.match_lookahead_literal(":", 0)
        while cond720:
            _t1407 = self.parse_fragment_id()
            item721 = _t1407
            xs719.append(item721)
            cond720 = self.match_lookahead_literal(":", 0)
        fragment_ids722 = xs719
        self.consume_literal(")")
        _t1408 = transactions_pb2.Sync(fragments=fragment_ids722)
        result724 = _t1408
        self.record_span(span_start723, "Sync")
        return result724

    def parse_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start726 = self.span_start()
        self.consume_literal(":")
        symbol725 = self.consume_terminal("SYMBOL")
        result727 = fragments_pb2.FragmentId(id=symbol725.encode())
        self.record_span(span_start726, "FragmentId")
        return result727

    def parse_epoch(self) -> transactions_pb2.Epoch:
        span_start730 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("epoch")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("writes", 1)):
            _t1410 = self.parse_epoch_writes()
            _t1409 = _t1410
        else:
            _t1409 = None
        epoch_writes728 = _t1409
        if self.match_lookahead_literal("(", 0):
            _t1412 = self.parse_epoch_reads()
            _t1411 = _t1412
        else:
            _t1411 = None
        epoch_reads729 = _t1411
        self.consume_literal(")")
        _t1413 = transactions_pb2.Epoch(writes=(epoch_writes728 if epoch_writes728 is not None else []), reads=(epoch_reads729 if epoch_reads729 is not None else []))
        result731 = _t1413
        self.record_span(span_start730, "Epoch")
        return result731

    def parse_epoch_writes(self) -> Sequence[transactions_pb2.Write]:
        self.consume_literal("(")
        self.consume_literal("writes")
        xs732 = []
        cond733 = self.match_lookahead_literal("(", 0)
        while cond733:
            _t1414 = self.parse_write()
            item734 = _t1414
            xs732.append(item734)
            cond733 = self.match_lookahead_literal("(", 0)
        writes735 = xs732
        self.consume_literal(")")
        return writes735

    def parse_write(self) -> transactions_pb2.Write:
        span_start741 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("undefine", 1):
                _t1416 = 1
            else:
                if self.match_lookahead_literal("snapshot", 1):
                    _t1417 = 3
                else:
                    if self.match_lookahead_literal("define", 1):
                        _t1418 = 0
                    else:
                        if self.match_lookahead_literal("context", 1):
                            _t1419 = 2
                        else:
                            _t1419 = -1
                        _t1418 = _t1419
                    _t1417 = _t1418
                _t1416 = _t1417
            _t1415 = _t1416
        else:
            _t1415 = -1
        prediction736 = _t1415
        if prediction736 == 3:
            _t1421 = self.parse_snapshot()
            snapshot740 = _t1421
            _t1422 = transactions_pb2.Write(snapshot=snapshot740)
            _t1420 = _t1422
        else:
            if prediction736 == 2:
                _t1424 = self.parse_context()
                context739 = _t1424
                _t1425 = transactions_pb2.Write(context=context739)
                _t1423 = _t1425
            else:
                if prediction736 == 1:
                    _t1427 = self.parse_undefine()
                    undefine738 = _t1427
                    _t1428 = transactions_pb2.Write(undefine=undefine738)
                    _t1426 = _t1428
                else:
                    if prediction736 == 0:
                        _t1430 = self.parse_define()
                        define737 = _t1430
                        _t1431 = transactions_pb2.Write(define=define737)
                        _t1429 = _t1431
                    else:
                        raise ParseError("Unexpected token in write" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1426 = _t1429
                _t1423 = _t1426
            _t1420 = _t1423
        result742 = _t1420
        self.record_span(span_start741, "Write")
        return result742

    def parse_define(self) -> transactions_pb2.Define:
        span_start744 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("define")
        _t1432 = self.parse_fragment()
        fragment743 = _t1432
        self.consume_literal(")")
        _t1433 = transactions_pb2.Define(fragment=fragment743)
        result745 = _t1433
        self.record_span(span_start744, "Define")
        return result745

    def parse_fragment(self) -> fragments_pb2.Fragment:
        span_start751 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("fragment")
        _t1434 = self.parse_new_fragment_id()
        new_fragment_id746 = _t1434
        xs747 = []
        cond748 = self.match_lookahead_literal("(", 0)
        while cond748:
            _t1435 = self.parse_declaration()
            item749 = _t1435
            xs747.append(item749)
            cond748 = self.match_lookahead_literal("(", 0)
        declarations750 = xs747
        self.consume_literal(")")
        result752 = self.construct_fragment(new_fragment_id746, declarations750)
        self.record_span(span_start751, "Fragment")
        return result752

    def parse_new_fragment_id(self) -> fragments_pb2.FragmentId:
        span_start754 = self.span_start()
        _t1436 = self.parse_fragment_id()
        fragment_id753 = _t1436
        self.start_fragment(fragment_id753)
        result755 = fragment_id753
        self.record_span(span_start754, "FragmentId")
        return result755

    def parse_declaration(self) -> logic_pb2.Declaration:
        span_start761 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1438 = 3
            else:
                if self.match_lookahead_literal("functional_dependency", 1):
                    _t1439 = 2
                else:
                    if self.match_lookahead_literal("edb", 1):
                        _t1440 = 3
                    else:
                        if self.match_lookahead_literal("def", 1):
                            _t1441 = 0
                        else:
                            if self.match_lookahead_literal("csv_data", 1):
                                _t1442 = 3
                            else:
                                if self.match_lookahead_literal("betree_relation", 1):
                                    _t1443 = 3
                                else:
                                    if self.match_lookahead_literal("algorithm", 1):
                                        _t1444 = 1
                                    else:
                                        _t1444 = -1
                                    _t1443 = _t1444
                                _t1442 = _t1443
                            _t1441 = _t1442
                        _t1440 = _t1441
                    _t1439 = _t1440
                _t1438 = _t1439
            _t1437 = _t1438
        else:
            _t1437 = -1
        prediction756 = _t1437
        if prediction756 == 3:
            _t1446 = self.parse_data()
            data760 = _t1446
            _t1447 = logic_pb2.Declaration(data=data760)
            _t1445 = _t1447
        else:
            if prediction756 == 2:
                _t1449 = self.parse_constraint()
                constraint759 = _t1449
                _t1450 = logic_pb2.Declaration(constraint=constraint759)
                _t1448 = _t1450
            else:
                if prediction756 == 1:
                    _t1452 = self.parse_algorithm()
                    algorithm758 = _t1452
                    _t1453 = logic_pb2.Declaration(algorithm=algorithm758)
                    _t1451 = _t1453
                else:
                    if prediction756 == 0:
                        _t1455 = self.parse_def()
                        def757 = _t1455
                        _t1456 = logic_pb2.Declaration()
                        getattr(_t1456, 'def').CopyFrom(def757)
                        _t1454 = _t1456
                    else:
                        raise ParseError("Unexpected token in declaration" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1451 = _t1454
                _t1448 = _t1451
            _t1445 = _t1448
        result762 = _t1445
        self.record_span(span_start761, "Declaration")
        return result762

    def parse_def(self) -> logic_pb2.Def:
        span_start766 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("def")
        _t1457 = self.parse_relation_id()
        relation_id763 = _t1457
        _t1458 = self.parse_abstraction()
        abstraction764 = _t1458
        if self.match_lookahead_literal("(", 0):
            _t1460 = self.parse_attrs()
            _t1459 = _t1460
        else:
            _t1459 = None
        attrs765 = _t1459
        self.consume_literal(")")
        _t1461 = logic_pb2.Def(name=relation_id763, body=abstraction764, attrs=(attrs765 if attrs765 is not None else []))
        result767 = _t1461
        self.record_span(span_start766, "Def")
        return result767

    def parse_relation_id(self) -> logic_pb2.RelationId:
        span_start771 = self.span_start()
        if self.match_lookahead_literal(":", 0):
            _t1462 = 0
        else:
            if self.match_lookahead_terminal("UINT128", 0):
                _t1463 = 1
            else:
                _t1463 = -1
            _t1462 = _t1463
        prediction768 = _t1462
        if prediction768 == 1:
            uint128770 = self.consume_terminal("UINT128")
            _t1464 = logic_pb2.RelationId(id_low=uint128770.low, id_high=uint128770.high)
        else:
            if prediction768 == 0:
                self.consume_literal(":")
                symbol769 = self.consume_terminal("SYMBOL")
                _t1465 = self.relation_id_from_string(symbol769)
            else:
                raise ParseError("Unexpected token in relation_id" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1464 = _t1465
        result772 = _t1464
        self.record_span(span_start771, "RelationId")
        return result772

    def parse_abstraction(self) -> logic_pb2.Abstraction:
        span_start775 = self.span_start()
        self.consume_literal("(")
        _t1466 = self.parse_bindings()
        bindings773 = _t1466
        _t1467 = self.parse_formula()
        formula774 = _t1467
        self.consume_literal(")")
        _t1468 = logic_pb2.Abstraction(vars=(list(bindings773[0]) + list(bindings773[1] if bindings773[1] is not None else [])), value=formula774)
        result776 = _t1468
        self.record_span(span_start775, "Abstraction")
        return result776

    def parse_bindings(self) -> tuple[Sequence[logic_pb2.Binding], Sequence[logic_pb2.Binding]]:
        self.consume_literal("[")
        xs777 = []
        cond778 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond778:
            _t1469 = self.parse_binding()
            item779 = _t1469
            xs777.append(item779)
            cond778 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings780 = xs777
        if self.match_lookahead_literal("|", 0):
            _t1471 = self.parse_value_bindings()
            _t1470 = _t1471
        else:
            _t1470 = None
        value_bindings781 = _t1470
        self.consume_literal("]")
        return (bindings780, (value_bindings781 if value_bindings781 is not None else []),)

    def parse_binding(self) -> logic_pb2.Binding:
        span_start784 = self.span_start()
        symbol782 = self.consume_terminal("SYMBOL")
        self.consume_literal("::")
        _t1472 = self.parse_type()
        type783 = _t1472
        _t1473 = logic_pb2.Var(name=symbol782)
        _t1474 = logic_pb2.Binding(var=_t1473, type=type783)
        result785 = _t1474
        self.record_span(span_start784, "Binding")
        return result785

    def parse_type(self) -> logic_pb2.Type:
        span_start801 = self.span_start()
        if self.match_lookahead_literal("UNKNOWN", 0):
            _t1475 = 0
        else:
            if self.match_lookahead_literal("UINT32", 0):
                _t1476 = 13
            else:
                if self.match_lookahead_literal("UINT128", 0):
                    _t1477 = 4
                else:
                    if self.match_lookahead_literal("STRING", 0):
                        _t1478 = 1
                    else:
                        if self.match_lookahead_literal("MISSING", 0):
                            _t1479 = 8
                        else:
                            if self.match_lookahead_literal("INT32", 0):
                                _t1480 = 11
                            else:
                                if self.match_lookahead_literal("INT128", 0):
                                    _t1481 = 5
                                else:
                                    if self.match_lookahead_literal("INT", 0):
                                        _t1482 = 2
                                    else:
                                        if self.match_lookahead_literal("FLOAT32", 0):
                                            _t1483 = 12
                                        else:
                                            if self.match_lookahead_literal("FLOAT", 0):
                                                _t1484 = 3
                                            else:
                                                if self.match_lookahead_literal("DATETIME", 0):
                                                    _t1485 = 7
                                                else:
                                                    if self.match_lookahead_literal("DATE", 0):
                                                        _t1486 = 6
                                                    else:
                                                        if self.match_lookahead_literal("BOOLEAN", 0):
                                                            _t1487 = 10
                                                        else:
                                                            if self.match_lookahead_literal("(", 0):
                                                                _t1488 = 9
                                                            else:
                                                                _t1488 = -1
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
                _t1476 = _t1477
            _t1475 = _t1476
        prediction786 = _t1475
        if prediction786 == 13:
            _t1490 = self.parse_uint32_type()
            uint32_type800 = _t1490
            _t1491 = logic_pb2.Type(uint32_type=uint32_type800)
            _t1489 = _t1491
        else:
            if prediction786 == 12:
                _t1493 = self.parse_float32_type()
                float32_type799 = _t1493
                _t1494 = logic_pb2.Type(float32_type=float32_type799)
                _t1492 = _t1494
            else:
                if prediction786 == 11:
                    _t1496 = self.parse_int32_type()
                    int32_type798 = _t1496
                    _t1497 = logic_pb2.Type(int32_type=int32_type798)
                    _t1495 = _t1497
                else:
                    if prediction786 == 10:
                        _t1499 = self.parse_boolean_type()
                        boolean_type797 = _t1499
                        _t1500 = logic_pb2.Type(boolean_type=boolean_type797)
                        _t1498 = _t1500
                    else:
                        if prediction786 == 9:
                            _t1502 = self.parse_decimal_type()
                            decimal_type796 = _t1502
                            _t1503 = logic_pb2.Type(decimal_type=decimal_type796)
                            _t1501 = _t1503
                        else:
                            if prediction786 == 8:
                                _t1505 = self.parse_missing_type()
                                missing_type795 = _t1505
                                _t1506 = logic_pb2.Type(missing_type=missing_type795)
                                _t1504 = _t1506
                            else:
                                if prediction786 == 7:
                                    _t1508 = self.parse_datetime_type()
                                    datetime_type794 = _t1508
                                    _t1509 = logic_pb2.Type(datetime_type=datetime_type794)
                                    _t1507 = _t1509
                                else:
                                    if prediction786 == 6:
                                        _t1511 = self.parse_date_type()
                                        date_type793 = _t1511
                                        _t1512 = logic_pb2.Type(date_type=date_type793)
                                        _t1510 = _t1512
                                    else:
                                        if prediction786 == 5:
                                            _t1514 = self.parse_int128_type()
                                            int128_type792 = _t1514
                                            _t1515 = logic_pb2.Type(int128_type=int128_type792)
                                            _t1513 = _t1515
                                        else:
                                            if prediction786 == 4:
                                                _t1517 = self.parse_uint128_type()
                                                uint128_type791 = _t1517
                                                _t1518 = logic_pb2.Type(uint128_type=uint128_type791)
                                                _t1516 = _t1518
                                            else:
                                                if prediction786 == 3:
                                                    _t1520 = self.parse_float_type()
                                                    float_type790 = _t1520
                                                    _t1521 = logic_pb2.Type(float_type=float_type790)
                                                    _t1519 = _t1521
                                                else:
                                                    if prediction786 == 2:
                                                        _t1523 = self.parse_int_type()
                                                        int_type789 = _t1523
                                                        _t1524 = logic_pb2.Type(int_type=int_type789)
                                                        _t1522 = _t1524
                                                    else:
                                                        if prediction786 == 1:
                                                            _t1526 = self.parse_string_type()
                                                            string_type788 = _t1526
                                                            _t1527 = logic_pb2.Type(string_type=string_type788)
                                                            _t1525 = _t1527
                                                        else:
                                                            if prediction786 == 0:
                                                                _t1529 = self.parse_unspecified_type()
                                                                unspecified_type787 = _t1529
                                                                _t1530 = logic_pb2.Type(unspecified_type=unspecified_type787)
                                                                _t1528 = _t1530
                                                            else:
                                                                raise ParseError("Unexpected token in type" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
                _t1492 = _t1495
            _t1489 = _t1492
        result802 = _t1489
        self.record_span(span_start801, "Type")
        return result802

    def parse_unspecified_type(self) -> logic_pb2.UnspecifiedType:
        span_start803 = self.span_start()
        self.consume_literal("UNKNOWN")
        _t1531 = logic_pb2.UnspecifiedType()
        result804 = _t1531
        self.record_span(span_start803, "UnspecifiedType")
        return result804

    def parse_string_type(self) -> logic_pb2.StringType:
        span_start805 = self.span_start()
        self.consume_literal("STRING")
        _t1532 = logic_pb2.StringType()
        result806 = _t1532
        self.record_span(span_start805, "StringType")
        return result806

    def parse_int_type(self) -> logic_pb2.IntType:
        span_start807 = self.span_start()
        self.consume_literal("INT")
        _t1533 = logic_pb2.IntType()
        result808 = _t1533
        self.record_span(span_start807, "IntType")
        return result808

    def parse_float_type(self) -> logic_pb2.FloatType:
        span_start809 = self.span_start()
        self.consume_literal("FLOAT")
        _t1534 = logic_pb2.FloatType()
        result810 = _t1534
        self.record_span(span_start809, "FloatType")
        return result810

    def parse_uint128_type(self) -> logic_pb2.UInt128Type:
        span_start811 = self.span_start()
        self.consume_literal("UINT128")
        _t1535 = logic_pb2.UInt128Type()
        result812 = _t1535
        self.record_span(span_start811, "UInt128Type")
        return result812

    def parse_int128_type(self) -> logic_pb2.Int128Type:
        span_start813 = self.span_start()
        self.consume_literal("INT128")
        _t1536 = logic_pb2.Int128Type()
        result814 = _t1536
        self.record_span(span_start813, "Int128Type")
        return result814

    def parse_date_type(self) -> logic_pb2.DateType:
        span_start815 = self.span_start()
        self.consume_literal("DATE")
        _t1537 = logic_pb2.DateType()
        result816 = _t1537
        self.record_span(span_start815, "DateType")
        return result816

    def parse_datetime_type(self) -> logic_pb2.DateTimeType:
        span_start817 = self.span_start()
        self.consume_literal("DATETIME")
        _t1538 = logic_pb2.DateTimeType()
        result818 = _t1538
        self.record_span(span_start817, "DateTimeType")
        return result818

    def parse_missing_type(self) -> logic_pb2.MissingType:
        span_start819 = self.span_start()
        self.consume_literal("MISSING")
        _t1539 = logic_pb2.MissingType()
        result820 = _t1539
        self.record_span(span_start819, "MissingType")
        return result820

    def parse_decimal_type(self) -> logic_pb2.DecimalType:
        span_start823 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("DECIMAL")
        int821 = self.consume_terminal("INT")
        int_3822 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1540 = logic_pb2.DecimalType(precision=int(int821), scale=int(int_3822))
        result824 = _t1540
        self.record_span(span_start823, "DecimalType")
        return result824

    def parse_boolean_type(self) -> logic_pb2.BooleanType:
        span_start825 = self.span_start()
        self.consume_literal("BOOLEAN")
        _t1541 = logic_pb2.BooleanType()
        result826 = _t1541
        self.record_span(span_start825, "BooleanType")
        return result826

    def parse_int32_type(self) -> logic_pb2.Int32Type:
        span_start827 = self.span_start()
        self.consume_literal("INT32")
        _t1542 = logic_pb2.Int32Type()
        result828 = _t1542
        self.record_span(span_start827, "Int32Type")
        return result828

    def parse_float32_type(self) -> logic_pb2.Float32Type:
        span_start829 = self.span_start()
        self.consume_literal("FLOAT32")
        _t1543 = logic_pb2.Float32Type()
        result830 = _t1543
        self.record_span(span_start829, "Float32Type")
        return result830

    def parse_uint32_type(self) -> logic_pb2.UInt32Type:
        span_start831 = self.span_start()
        self.consume_literal("UINT32")
        _t1544 = logic_pb2.UInt32Type()
        result832 = _t1544
        self.record_span(span_start831, "UInt32Type")
        return result832

    def parse_value_bindings(self) -> Sequence[logic_pb2.Binding]:
        self.consume_literal("|")
        xs833 = []
        cond834 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond834:
            _t1545 = self.parse_binding()
            item835 = _t1545
            xs833.append(item835)
            cond834 = self.match_lookahead_terminal("SYMBOL", 0)
        bindings836 = xs833
        return bindings836

    def parse_formula(self) -> logic_pb2.Formula:
        span_start851 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("true", 1):
                _t1547 = 0
            else:
                if self.match_lookahead_literal("relatom", 1):
                    _t1548 = 11
                else:
                    if self.match_lookahead_literal("reduce", 1):
                        _t1549 = 3
                    else:
                        if self.match_lookahead_literal("primitive", 1):
                            _t1550 = 10
                        else:
                            if self.match_lookahead_literal("pragma", 1):
                                _t1551 = 9
                            else:
                                if self.match_lookahead_literal("or", 1):
                                    _t1552 = 5
                                else:
                                    if self.match_lookahead_literal("not", 1):
                                        _t1553 = 6
                                    else:
                                        if self.match_lookahead_literal("ffi", 1):
                                            _t1554 = 7
                                        else:
                                            if self.match_lookahead_literal("false", 1):
                                                _t1555 = 1
                                            else:
                                                if self.match_lookahead_literal("exists", 1):
                                                    _t1556 = 2
                                                else:
                                                    if self.match_lookahead_literal("cast", 1):
                                                        _t1557 = 12
                                                    else:
                                                        if self.match_lookahead_literal("atom", 1):
                                                            _t1558 = 8
                                                        else:
                                                            if self.match_lookahead_literal("and", 1):
                                                                _t1559 = 4
                                                            else:
                                                                if self.match_lookahead_literal(">=", 1):
                                                                    _t1560 = 10
                                                                else:
                                                                    if self.match_lookahead_literal(">", 1):
                                                                        _t1561 = 10
                                                                    else:
                                                                        if self.match_lookahead_literal("=", 1):
                                                                            _t1562 = 10
                                                                        else:
                                                                            if self.match_lookahead_literal("<=", 1):
                                                                                _t1563 = 10
                                                                            else:
                                                                                if self.match_lookahead_literal("<", 1):
                                                                                    _t1564 = 10
                                                                                else:
                                                                                    if self.match_lookahead_literal("/", 1):
                                                                                        _t1565 = 10
                                                                                    else:
                                                                                        if self.match_lookahead_literal("-", 1):
                                                                                            _t1566 = 10
                                                                                        else:
                                                                                            if self.match_lookahead_literal("+", 1):
                                                                                                _t1567 = 10
                                                                                            else:
                                                                                                if self.match_lookahead_literal("*", 1):
                                                                                                    _t1568 = 10
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
                                            _t1554 = _t1555
                                        _t1553 = _t1554
                                    _t1552 = _t1553
                                _t1551 = _t1552
                            _t1550 = _t1551
                        _t1549 = _t1550
                    _t1548 = _t1549
                _t1547 = _t1548
            _t1546 = _t1547
        else:
            _t1546 = -1
        prediction837 = _t1546
        if prediction837 == 12:
            _t1570 = self.parse_cast()
            cast850 = _t1570
            _t1571 = logic_pb2.Formula(cast=cast850)
            _t1569 = _t1571
        else:
            if prediction837 == 11:
                _t1573 = self.parse_rel_atom()
                rel_atom849 = _t1573
                _t1574 = logic_pb2.Formula(rel_atom=rel_atom849)
                _t1572 = _t1574
            else:
                if prediction837 == 10:
                    _t1576 = self.parse_primitive()
                    primitive848 = _t1576
                    _t1577 = logic_pb2.Formula(primitive=primitive848)
                    _t1575 = _t1577
                else:
                    if prediction837 == 9:
                        _t1579 = self.parse_pragma()
                        pragma847 = _t1579
                        _t1580 = logic_pb2.Formula(pragma=pragma847)
                        _t1578 = _t1580
                    else:
                        if prediction837 == 8:
                            _t1582 = self.parse_atom()
                            atom846 = _t1582
                            _t1583 = logic_pb2.Formula(atom=atom846)
                            _t1581 = _t1583
                        else:
                            if prediction837 == 7:
                                _t1585 = self.parse_ffi()
                                ffi845 = _t1585
                                _t1586 = logic_pb2.Formula(ffi=ffi845)
                                _t1584 = _t1586
                            else:
                                if prediction837 == 6:
                                    _t1588 = self.parse_not()
                                    not844 = _t1588
                                    _t1589 = logic_pb2.Formula()
                                    getattr(_t1589, 'not').CopyFrom(not844)
                                    _t1587 = _t1589
                                else:
                                    if prediction837 == 5:
                                        _t1591 = self.parse_disjunction()
                                        disjunction843 = _t1591
                                        _t1592 = logic_pb2.Formula(disjunction=disjunction843)
                                        _t1590 = _t1592
                                    else:
                                        if prediction837 == 4:
                                            _t1594 = self.parse_conjunction()
                                            conjunction842 = _t1594
                                            _t1595 = logic_pb2.Formula(conjunction=conjunction842)
                                            _t1593 = _t1595
                                        else:
                                            if prediction837 == 3:
                                                _t1597 = self.parse_reduce()
                                                reduce841 = _t1597
                                                _t1598 = logic_pb2.Formula(reduce=reduce841)
                                                _t1596 = _t1598
                                            else:
                                                if prediction837 == 2:
                                                    _t1600 = self.parse_exists()
                                                    exists840 = _t1600
                                                    _t1601 = logic_pb2.Formula(exists=exists840)
                                                    _t1599 = _t1601
                                                else:
                                                    if prediction837 == 1:
                                                        _t1603 = self.parse_false()
                                                        false839 = _t1603
                                                        _t1604 = logic_pb2.Formula(disjunction=false839)
                                                        _t1602 = _t1604
                                                    else:
                                                        if prediction837 == 0:
                                                            _t1606 = self.parse_true()
                                                            true838 = _t1606
                                                            _t1607 = logic_pb2.Formula(conjunction=true838)
                                                            _t1605 = _t1607
                                                        else:
                                                            raise ParseError("Unexpected token in formula" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
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
        result852 = _t1569
        self.record_span(span_start851, "Formula")
        return result852

    def parse_true(self) -> logic_pb2.Conjunction:
        span_start853 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("true")
        self.consume_literal(")")
        _t1608 = logic_pb2.Conjunction(args=[])
        result854 = _t1608
        self.record_span(span_start853, "Conjunction")
        return result854

    def parse_false(self) -> logic_pb2.Disjunction:
        span_start855 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("false")
        self.consume_literal(")")
        _t1609 = logic_pb2.Disjunction(args=[])
        result856 = _t1609
        self.record_span(span_start855, "Disjunction")
        return result856

    def parse_exists(self) -> logic_pb2.Exists:
        span_start859 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("exists")
        _t1610 = self.parse_bindings()
        bindings857 = _t1610
        _t1611 = self.parse_formula()
        formula858 = _t1611
        self.consume_literal(")")
        _t1612 = logic_pb2.Abstraction(vars=(list(bindings857[0]) + list(bindings857[1] if bindings857[1] is not None else [])), value=formula858)
        _t1613 = logic_pb2.Exists(body=_t1612)
        result860 = _t1613
        self.record_span(span_start859, "Exists")
        return result860

    def parse_reduce(self) -> logic_pb2.Reduce:
        span_start864 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("reduce")
        _t1614 = self.parse_abstraction()
        abstraction861 = _t1614
        _t1615 = self.parse_abstraction()
        abstraction_3862 = _t1615
        _t1616 = self.parse_terms()
        terms863 = _t1616
        self.consume_literal(")")
        _t1617 = logic_pb2.Reduce(op=abstraction861, body=abstraction_3862, terms=terms863)
        result865 = _t1617
        self.record_span(span_start864, "Reduce")
        return result865

    def parse_terms(self) -> Sequence[logic_pb2.Term]:
        self.consume_literal("(")
        self.consume_literal("terms")
        xs866 = []
        cond867 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond867:
            _t1618 = self.parse_term()
            item868 = _t1618
            xs866.append(item868)
            cond867 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms869 = xs866
        self.consume_literal(")")
        return terms869

    def parse_term(self) -> logic_pb2.Term:
        span_start873 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1619 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1620 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1621 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1622 = 1
                    else:
                        if self.match_lookahead_terminal("SYMBOL", 0):
                            _t1623 = 0
                        else:
                            if self.match_lookahead_terminal("UINT32", 0):
                                _t1624 = 1
                            else:
                                if self.match_lookahead_terminal("UINT128", 0):
                                    _t1625 = 1
                                else:
                                    if self.match_lookahead_terminal("STRING", 0):
                                        _t1626 = 1
                                    else:
                                        if self.match_lookahead_terminal("INT32", 0):
                                            _t1627 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT128", 0):
                                                _t1628 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT", 0):
                                                    _t1629 = 1
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT32", 0):
                                                        _t1630 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT", 0):
                                                            _t1631 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("DECIMAL", 0):
                                                                _t1632 = 1
                                                            else:
                                                                _t1632 = -1
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
        prediction870 = _t1619
        if prediction870 == 1:
            _t1634 = self.parse_value()
            value872 = _t1634
            _t1635 = logic_pb2.Term(constant=value872)
            _t1633 = _t1635
        else:
            if prediction870 == 0:
                _t1637 = self.parse_var()
                var871 = _t1637
                _t1638 = logic_pb2.Term(var=var871)
                _t1636 = _t1638
            else:
                raise ParseError("Unexpected token in term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1633 = _t1636
        result874 = _t1633
        self.record_span(span_start873, "Term")
        return result874

    def parse_var(self) -> logic_pb2.Var:
        span_start876 = self.span_start()
        symbol875 = self.consume_terminal("SYMBOL")
        _t1639 = logic_pb2.Var(name=symbol875)
        result877 = _t1639
        self.record_span(span_start876, "Var")
        return result877

    def parse_value(self) -> logic_pb2.Value:
        span_start891 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1640 = 12
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1641 = 11
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1642 = 12
                else:
                    if self.match_lookahead_literal("(", 0):
                        if self.match_lookahead_literal("datetime", 1):
                            _t1644 = 1
                        else:
                            if self.match_lookahead_literal("date", 1):
                                _t1645 = 0
                            else:
                                _t1645 = -1
                            _t1644 = _t1645
                        _t1643 = _t1644
                    else:
                        if self.match_lookahead_terminal("UINT32", 0):
                            _t1646 = 7
                        else:
                            if self.match_lookahead_terminal("UINT128", 0):
                                _t1647 = 8
                            else:
                                if self.match_lookahead_terminal("STRING", 0):
                                    _t1648 = 2
                                else:
                                    if self.match_lookahead_terminal("INT32", 0):
                                        _t1649 = 3
                                    else:
                                        if self.match_lookahead_terminal("INT128", 0):
                                            _t1650 = 9
                                        else:
                                            if self.match_lookahead_terminal("INT", 0):
                                                _t1651 = 4
                                            else:
                                                if self.match_lookahead_terminal("FLOAT32", 0):
                                                    _t1652 = 5
                                                else:
                                                    if self.match_lookahead_terminal("FLOAT", 0):
                                                        _t1653 = 6
                                                    else:
                                                        if self.match_lookahead_terminal("DECIMAL", 0):
                                                            _t1654 = 10
                                                        else:
                                                            _t1654 = -1
                                                        _t1653 = _t1654
                                                    _t1652 = _t1653
                                                _t1651 = _t1652
                                            _t1650 = _t1651
                                        _t1649 = _t1650
                                    _t1648 = _t1649
                                _t1647 = _t1648
                            _t1646 = _t1647
                        _t1643 = _t1646
                    _t1642 = _t1643
                _t1641 = _t1642
            _t1640 = _t1641
        prediction878 = _t1640
        if prediction878 == 12:
            _t1656 = self.parse_boolean_value()
            boolean_value890 = _t1656
            _t1657 = logic_pb2.Value(boolean_value=boolean_value890)
            _t1655 = _t1657
        else:
            if prediction878 == 11:
                self.consume_literal("missing")
                _t1659 = logic_pb2.MissingValue()
                _t1660 = logic_pb2.Value(missing_value=_t1659)
                _t1658 = _t1660
            else:
                if prediction878 == 10:
                    formatted_decimal889 = self.consume_terminal("DECIMAL")
                    _t1662 = logic_pb2.Value(decimal_value=formatted_decimal889)
                    _t1661 = _t1662
                else:
                    if prediction878 == 9:
                        formatted_int128888 = self.consume_terminal("INT128")
                        _t1664 = logic_pb2.Value(int128_value=formatted_int128888)
                        _t1663 = _t1664
                    else:
                        if prediction878 == 8:
                            formatted_uint128887 = self.consume_terminal("UINT128")
                            _t1666 = logic_pb2.Value(uint128_value=formatted_uint128887)
                            _t1665 = _t1666
                        else:
                            if prediction878 == 7:
                                formatted_uint32886 = self.consume_terminal("UINT32")
                                _t1668 = logic_pb2.Value(uint32_value=formatted_uint32886)
                                _t1667 = _t1668
                            else:
                                if prediction878 == 6:
                                    formatted_float885 = self.consume_terminal("FLOAT")
                                    _t1670 = logic_pb2.Value(float_value=formatted_float885)
                                    _t1669 = _t1670
                                else:
                                    if prediction878 == 5:
                                        formatted_float32884 = self.consume_terminal("FLOAT32")
                                        _t1672 = logic_pb2.Value(float32_value=formatted_float32884)
                                        _t1671 = _t1672
                                    else:
                                        if prediction878 == 4:
                                            formatted_int883 = self.consume_terminal("INT")
                                            _t1674 = logic_pb2.Value(int_value=formatted_int883)
                                            _t1673 = _t1674
                                        else:
                                            if prediction878 == 3:
                                                formatted_int32882 = self.consume_terminal("INT32")
                                                _t1676 = logic_pb2.Value(int32_value=formatted_int32882)
                                                _t1675 = _t1676
                                            else:
                                                if prediction878 == 2:
                                                    formatted_string881 = self.consume_terminal("STRING")
                                                    _t1678 = logic_pb2.Value(string_value=formatted_string881)
                                                    _t1677 = _t1678
                                                else:
                                                    if prediction878 == 1:
                                                        _t1680 = self.parse_datetime()
                                                        datetime880 = _t1680
                                                        _t1681 = logic_pb2.Value(datetime_value=datetime880)
                                                        _t1679 = _t1681
                                                    else:
                                                        if prediction878 == 0:
                                                            _t1683 = self.parse_date()
                                                            date879 = _t1683
                                                            _t1684 = logic_pb2.Value(date_value=date879)
                                                            _t1682 = _t1684
                                                        else:
                                                            raise ParseError("Unexpected token in value" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                                        _t1679 = _t1682
                                                    _t1677 = _t1679
                                                _t1675 = _t1677
                                            _t1673 = _t1675
                                        _t1671 = _t1673
                                    _t1669 = _t1671
                                _t1667 = _t1669
                            _t1665 = _t1667
                        _t1663 = _t1665
                    _t1661 = _t1663
                _t1658 = _t1661
            _t1655 = _t1658
        result892 = _t1655
        self.record_span(span_start891, "Value")
        return result892

    def parse_date(self) -> logic_pb2.DateValue:
        span_start896 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("date")
        formatted_int893 = self.consume_terminal("INT")
        formatted_int_3894 = self.consume_terminal("INT")
        formatted_int_4895 = self.consume_terminal("INT")
        self.consume_literal(")")
        _t1685 = logic_pb2.DateValue(year=int(formatted_int893), month=int(formatted_int_3894), day=int(formatted_int_4895))
        result897 = _t1685
        self.record_span(span_start896, "DateValue")
        return result897

    def parse_datetime(self) -> logic_pb2.DateTimeValue:
        span_start905 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("datetime")
        formatted_int898 = self.consume_terminal("INT")
        formatted_int_3899 = self.consume_terminal("INT")
        formatted_int_4900 = self.consume_terminal("INT")
        formatted_int_5901 = self.consume_terminal("INT")
        formatted_int_6902 = self.consume_terminal("INT")
        formatted_int_7903 = self.consume_terminal("INT")
        if self.match_lookahead_terminal("INT", 0):
            _t1686 = self.consume_terminal("INT")
        else:
            _t1686 = None
        formatted_int_8904 = _t1686
        self.consume_literal(")")
        _t1687 = logic_pb2.DateTimeValue(year=int(formatted_int898), month=int(formatted_int_3899), day=int(formatted_int_4900), hour=int(formatted_int_5901), minute=int(formatted_int_6902), second=int(formatted_int_7903), microsecond=int((formatted_int_8904 if formatted_int_8904 is not None else 0)))
        result906 = _t1687
        self.record_span(span_start905, "DateTimeValue")
        return result906

    def parse_conjunction(self) -> logic_pb2.Conjunction:
        span_start911 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("and")
        xs907 = []
        cond908 = self.match_lookahead_literal("(", 0)
        while cond908:
            _t1688 = self.parse_formula()
            item909 = _t1688
            xs907.append(item909)
            cond908 = self.match_lookahead_literal("(", 0)
        formulas910 = xs907
        self.consume_literal(")")
        _t1689 = logic_pb2.Conjunction(args=formulas910)
        result912 = _t1689
        self.record_span(span_start911, "Conjunction")
        return result912

    def parse_disjunction(self) -> logic_pb2.Disjunction:
        span_start917 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        xs913 = []
        cond914 = self.match_lookahead_literal("(", 0)
        while cond914:
            _t1690 = self.parse_formula()
            item915 = _t1690
            xs913.append(item915)
            cond914 = self.match_lookahead_literal("(", 0)
        formulas916 = xs913
        self.consume_literal(")")
        _t1691 = logic_pb2.Disjunction(args=formulas916)
        result918 = _t1691
        self.record_span(span_start917, "Disjunction")
        return result918

    def parse_not(self) -> logic_pb2.Not:
        span_start920 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("not")
        _t1692 = self.parse_formula()
        formula919 = _t1692
        self.consume_literal(")")
        _t1693 = logic_pb2.Not(arg=formula919)
        result921 = _t1693
        self.record_span(span_start920, "Not")
        return result921

    def parse_ffi(self) -> logic_pb2.FFI:
        span_start925 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("ffi")
        _t1694 = self.parse_name()
        name922 = _t1694
        _t1695 = self.parse_ffi_args()
        ffi_args923 = _t1695
        _t1696 = self.parse_terms()
        terms924 = _t1696
        self.consume_literal(")")
        _t1697 = logic_pb2.FFI(name=name922, args=ffi_args923, terms=terms924)
        result926 = _t1697
        self.record_span(span_start925, "FFI")
        return result926

    def parse_name(self) -> str:
        self.consume_literal(":")
        symbol927 = self.consume_terminal("SYMBOL")
        return symbol927

    def parse_ffi_args(self) -> Sequence[logic_pb2.Abstraction]:
        self.consume_literal("(")
        self.consume_literal("args")
        xs928 = []
        cond929 = self.match_lookahead_literal("(", 0)
        while cond929:
            _t1698 = self.parse_abstraction()
            item930 = _t1698
            xs928.append(item930)
            cond929 = self.match_lookahead_literal("(", 0)
        abstractions931 = xs928
        self.consume_literal(")")
        return abstractions931

    def parse_atom(self) -> logic_pb2.Atom:
        span_start937 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("atom")
        _t1699 = self.parse_relation_id()
        relation_id932 = _t1699
        xs933 = []
        cond934 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond934:
            _t1700 = self.parse_term()
            item935 = _t1700
            xs933.append(item935)
            cond934 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms936 = xs933
        self.consume_literal(")")
        _t1701 = logic_pb2.Atom(name=relation_id932, terms=terms936)
        result938 = _t1701
        self.record_span(span_start937, "Atom")
        return result938

    def parse_pragma(self) -> logic_pb2.Pragma:
        span_start944 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("pragma")
        _t1702 = self.parse_name()
        name939 = _t1702
        xs940 = []
        cond941 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond941:
            _t1703 = self.parse_term()
            item942 = _t1703
            xs940.append(item942)
            cond941 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        terms943 = xs940
        self.consume_literal(")")
        _t1704 = logic_pb2.Pragma(name=name939, terms=terms943)
        result945 = _t1704
        self.record_span(span_start944, "Pragma")
        return result945

    def parse_primitive(self) -> logic_pb2.Primitive:
        span_start961 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("primitive", 1):
                _t1706 = 9
            else:
                if self.match_lookahead_literal(">=", 1):
                    _t1707 = 4
                else:
                    if self.match_lookahead_literal(">", 1):
                        _t1708 = 3
                    else:
                        if self.match_lookahead_literal("=", 1):
                            _t1709 = 0
                        else:
                            if self.match_lookahead_literal("<=", 1):
                                _t1710 = 2
                            else:
                                if self.match_lookahead_literal("<", 1):
                                    _t1711 = 1
                                else:
                                    if self.match_lookahead_literal("/", 1):
                                        _t1712 = 8
                                    else:
                                        if self.match_lookahead_literal("-", 1):
                                            _t1713 = 6
                                        else:
                                            if self.match_lookahead_literal("+", 1):
                                                _t1714 = 5
                                            else:
                                                if self.match_lookahead_literal("*", 1):
                                                    _t1715 = 7
                                                else:
                                                    _t1715 = -1
                                                _t1714 = _t1715
                                            _t1713 = _t1714
                                        _t1712 = _t1713
                                    _t1711 = _t1712
                                _t1710 = _t1711
                            _t1709 = _t1710
                        _t1708 = _t1709
                    _t1707 = _t1708
                _t1706 = _t1707
            _t1705 = _t1706
        else:
            _t1705 = -1
        prediction946 = _t1705
        if prediction946 == 9:
            self.consume_literal("(")
            self.consume_literal("primitive")
            _t1717 = self.parse_name()
            name956 = _t1717
            xs957 = []
            cond958 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            while cond958:
                _t1718 = self.parse_rel_term()
                item959 = _t1718
                xs957.append(item959)
                cond958 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
            rel_terms960 = xs957
            self.consume_literal(")")
            _t1719 = logic_pb2.Primitive(name=name956, terms=rel_terms960)
            _t1716 = _t1719
        else:
            if prediction946 == 8:
                _t1721 = self.parse_divide()
                divide955 = _t1721
                _t1720 = divide955
            else:
                if prediction946 == 7:
                    _t1723 = self.parse_multiply()
                    multiply954 = _t1723
                    _t1722 = multiply954
                else:
                    if prediction946 == 6:
                        _t1725 = self.parse_minus()
                        minus953 = _t1725
                        _t1724 = minus953
                    else:
                        if prediction946 == 5:
                            _t1727 = self.parse_add()
                            add952 = _t1727
                            _t1726 = add952
                        else:
                            if prediction946 == 4:
                                _t1729 = self.parse_gt_eq()
                                gt_eq951 = _t1729
                                _t1728 = gt_eq951
                            else:
                                if prediction946 == 3:
                                    _t1731 = self.parse_gt()
                                    gt950 = _t1731
                                    _t1730 = gt950
                                else:
                                    if prediction946 == 2:
                                        _t1733 = self.parse_lt_eq()
                                        lt_eq949 = _t1733
                                        _t1732 = lt_eq949
                                    else:
                                        if prediction946 == 1:
                                            _t1735 = self.parse_lt()
                                            lt948 = _t1735
                                            _t1734 = lt948
                                        else:
                                            if prediction946 == 0:
                                                _t1737 = self.parse_eq()
                                                eq947 = _t1737
                                                _t1736 = eq947
                                            else:
                                                raise ParseError("Unexpected token in primitive" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                                            _t1734 = _t1736
                                        _t1732 = _t1734
                                    _t1730 = _t1732
                                _t1728 = _t1730
                            _t1726 = _t1728
                        _t1724 = _t1726
                    _t1722 = _t1724
                _t1720 = _t1722
            _t1716 = _t1720
        result962 = _t1716
        self.record_span(span_start961, "Primitive")
        return result962

    def parse_eq(self) -> logic_pb2.Primitive:
        span_start965 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("=")
        _t1738 = self.parse_term()
        term963 = _t1738
        _t1739 = self.parse_term()
        term_3964 = _t1739
        self.consume_literal(")")
        _t1740 = logic_pb2.RelTerm(term=term963)
        _t1741 = logic_pb2.RelTerm(term=term_3964)
        _t1742 = logic_pb2.Primitive(name="rel_primitive_eq", terms=[_t1740, _t1741])
        result966 = _t1742
        self.record_span(span_start965, "Primitive")
        return result966

    def parse_lt(self) -> logic_pb2.Primitive:
        span_start969 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<")
        _t1743 = self.parse_term()
        term967 = _t1743
        _t1744 = self.parse_term()
        term_3968 = _t1744
        self.consume_literal(")")
        _t1745 = logic_pb2.RelTerm(term=term967)
        _t1746 = logic_pb2.RelTerm(term=term_3968)
        _t1747 = logic_pb2.Primitive(name="rel_primitive_lt_monotype", terms=[_t1745, _t1746])
        result970 = _t1747
        self.record_span(span_start969, "Primitive")
        return result970

    def parse_lt_eq(self) -> logic_pb2.Primitive:
        span_start973 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("<=")
        _t1748 = self.parse_term()
        term971 = _t1748
        _t1749 = self.parse_term()
        term_3972 = _t1749
        self.consume_literal(")")
        _t1750 = logic_pb2.RelTerm(term=term971)
        _t1751 = logic_pb2.RelTerm(term=term_3972)
        _t1752 = logic_pb2.Primitive(name="rel_primitive_lt_eq_monotype", terms=[_t1750, _t1751])
        result974 = _t1752
        self.record_span(span_start973, "Primitive")
        return result974

    def parse_gt(self) -> logic_pb2.Primitive:
        span_start977 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">")
        _t1753 = self.parse_term()
        term975 = _t1753
        _t1754 = self.parse_term()
        term_3976 = _t1754
        self.consume_literal(")")
        _t1755 = logic_pb2.RelTerm(term=term975)
        _t1756 = logic_pb2.RelTerm(term=term_3976)
        _t1757 = logic_pb2.Primitive(name="rel_primitive_gt_monotype", terms=[_t1755, _t1756])
        result978 = _t1757
        self.record_span(span_start977, "Primitive")
        return result978

    def parse_gt_eq(self) -> logic_pb2.Primitive:
        span_start981 = self.span_start()
        self.consume_literal("(")
        self.consume_literal(">=")
        _t1758 = self.parse_term()
        term979 = _t1758
        _t1759 = self.parse_term()
        term_3980 = _t1759
        self.consume_literal(")")
        _t1760 = logic_pb2.RelTerm(term=term979)
        _t1761 = logic_pb2.RelTerm(term=term_3980)
        _t1762 = logic_pb2.Primitive(name="rel_primitive_gt_eq_monotype", terms=[_t1760, _t1761])
        result982 = _t1762
        self.record_span(span_start981, "Primitive")
        return result982

    def parse_add(self) -> logic_pb2.Primitive:
        span_start986 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("+")
        _t1763 = self.parse_term()
        term983 = _t1763
        _t1764 = self.parse_term()
        term_3984 = _t1764
        _t1765 = self.parse_term()
        term_4985 = _t1765
        self.consume_literal(")")
        _t1766 = logic_pb2.RelTerm(term=term983)
        _t1767 = logic_pb2.RelTerm(term=term_3984)
        _t1768 = logic_pb2.RelTerm(term=term_4985)
        _t1769 = logic_pb2.Primitive(name="rel_primitive_add_monotype", terms=[_t1766, _t1767, _t1768])
        result987 = _t1769
        self.record_span(span_start986, "Primitive")
        return result987

    def parse_minus(self) -> logic_pb2.Primitive:
        span_start991 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("-")
        _t1770 = self.parse_term()
        term988 = _t1770
        _t1771 = self.parse_term()
        term_3989 = _t1771
        _t1772 = self.parse_term()
        term_4990 = _t1772
        self.consume_literal(")")
        _t1773 = logic_pb2.RelTerm(term=term988)
        _t1774 = logic_pb2.RelTerm(term=term_3989)
        _t1775 = logic_pb2.RelTerm(term=term_4990)
        _t1776 = logic_pb2.Primitive(name="rel_primitive_subtract_monotype", terms=[_t1773, _t1774, _t1775])
        result992 = _t1776
        self.record_span(span_start991, "Primitive")
        return result992

    def parse_multiply(self) -> logic_pb2.Primitive:
        span_start996 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("*")
        _t1777 = self.parse_term()
        term993 = _t1777
        _t1778 = self.parse_term()
        term_3994 = _t1778
        _t1779 = self.parse_term()
        term_4995 = _t1779
        self.consume_literal(")")
        _t1780 = logic_pb2.RelTerm(term=term993)
        _t1781 = logic_pb2.RelTerm(term=term_3994)
        _t1782 = logic_pb2.RelTerm(term=term_4995)
        _t1783 = logic_pb2.Primitive(name="rel_primitive_multiply_monotype", terms=[_t1780, _t1781, _t1782])
        result997 = _t1783
        self.record_span(span_start996, "Primitive")
        return result997

    def parse_divide(self) -> logic_pb2.Primitive:
        span_start1001 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("/")
        _t1784 = self.parse_term()
        term998 = _t1784
        _t1785 = self.parse_term()
        term_3999 = _t1785
        _t1786 = self.parse_term()
        term_41000 = _t1786
        self.consume_literal(")")
        _t1787 = logic_pb2.RelTerm(term=term998)
        _t1788 = logic_pb2.RelTerm(term=term_3999)
        _t1789 = logic_pb2.RelTerm(term=term_41000)
        _t1790 = logic_pb2.Primitive(name="rel_primitive_divide_monotype", terms=[_t1787, _t1788, _t1789])
        result1002 = _t1790
        self.record_span(span_start1001, "Primitive")
        return result1002

    def parse_rel_term(self) -> logic_pb2.RelTerm:
        span_start1006 = self.span_start()
        if self.match_lookahead_literal("true", 0):
            _t1791 = 1
        else:
            if self.match_lookahead_literal("missing", 0):
                _t1792 = 1
            else:
                if self.match_lookahead_literal("false", 0):
                    _t1793 = 1
                else:
                    if self.match_lookahead_literal("(", 0):
                        _t1794 = 1
                    else:
                        if self.match_lookahead_literal("#", 0):
                            _t1795 = 0
                        else:
                            if self.match_lookahead_terminal("SYMBOL", 0):
                                _t1796 = 1
                            else:
                                if self.match_lookahead_terminal("UINT32", 0):
                                    _t1797 = 1
                                else:
                                    if self.match_lookahead_terminal("UINT128", 0):
                                        _t1798 = 1
                                    else:
                                        if self.match_lookahead_terminal("STRING", 0):
                                            _t1799 = 1
                                        else:
                                            if self.match_lookahead_terminal("INT32", 0):
                                                _t1800 = 1
                                            else:
                                                if self.match_lookahead_terminal("INT128", 0):
                                                    _t1801 = 1
                                                else:
                                                    if self.match_lookahead_terminal("INT", 0):
                                                        _t1802 = 1
                                                    else:
                                                        if self.match_lookahead_terminal("FLOAT32", 0):
                                                            _t1803 = 1
                                                        else:
                                                            if self.match_lookahead_terminal("FLOAT", 0):
                                                                _t1804 = 1
                                                            else:
                                                                if self.match_lookahead_terminal("DECIMAL", 0):
                                                                    _t1805 = 1
                                                                else:
                                                                    _t1805 = -1
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
                _t1792 = _t1793
            _t1791 = _t1792
        prediction1003 = _t1791
        if prediction1003 == 1:
            _t1807 = self.parse_term()
            term1005 = _t1807
            _t1808 = logic_pb2.RelTerm(term=term1005)
            _t1806 = _t1808
        else:
            if prediction1003 == 0:
                _t1810 = self.parse_specialized_value()
                specialized_value1004 = _t1810
                _t1811 = logic_pb2.RelTerm(specialized_value=specialized_value1004)
                _t1809 = _t1811
            else:
                raise ParseError("Unexpected token in rel_term" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1806 = _t1809
        result1007 = _t1806
        self.record_span(span_start1006, "RelTerm")
        return result1007

    def parse_specialized_value(self) -> logic_pb2.Value:
        span_start1009 = self.span_start()
        self.consume_literal("#")
        _t1812 = self.parse_raw_value()
        raw_value1008 = _t1812
        result1010 = raw_value1008
        self.record_span(span_start1009, "Value")
        return result1010

    def parse_rel_atom(self) -> logic_pb2.RelAtom:
        span_start1016 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("relatom")
        _t1813 = self.parse_name()
        name1011 = _t1813
        xs1012 = []
        cond1013 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        while cond1013:
            _t1814 = self.parse_rel_term()
            item1014 = _t1814
            xs1012.append(item1014)
            cond1013 = ((((((((((((((self.match_lookahead_literal("#", 0) or self.match_lookahead_literal("(", 0)) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0)) or self.match_lookahead_terminal("SYMBOL", 0))
        rel_terms1015 = xs1012
        self.consume_literal(")")
        _t1815 = logic_pb2.RelAtom(name=name1011, terms=rel_terms1015)
        result1017 = _t1815
        self.record_span(span_start1016, "RelAtom")
        return result1017

    def parse_cast(self) -> logic_pb2.Cast:
        span_start1020 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("cast")
        _t1816 = self.parse_term()
        term1018 = _t1816
        _t1817 = self.parse_term()
        term_31019 = _t1817
        self.consume_literal(")")
        _t1818 = logic_pb2.Cast(input=term1018, result=term_31019)
        result1021 = _t1818
        self.record_span(span_start1020, "Cast")
        return result1021

    def parse_attrs(self) -> Sequence[logic_pb2.Attribute]:
        self.consume_literal("(")
        self.consume_literal("attrs")
        xs1022 = []
        cond1023 = self.match_lookahead_literal("(", 0)
        while cond1023:
            _t1819 = self.parse_attribute()
            item1024 = _t1819
            xs1022.append(item1024)
            cond1023 = self.match_lookahead_literal("(", 0)
        attributes1025 = xs1022
        self.consume_literal(")")
        return attributes1025

    def parse_attribute(self) -> logic_pb2.Attribute:
        span_start1031 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("attribute")
        _t1820 = self.parse_name()
        name1026 = _t1820
        xs1027 = []
        cond1028 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        while cond1028:
            _t1821 = self.parse_raw_value()
            item1029 = _t1821
            xs1027.append(item1029)
            cond1028 = ((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("false", 0)) or self.match_lookahead_literal("missing", 0)) or self.match_lookahead_literal("true", 0)) or self.match_lookahead_terminal("DECIMAL", 0)) or self.match_lookahead_terminal("FLOAT", 0)) or self.match_lookahead_terminal("FLOAT32", 0)) or self.match_lookahead_terminal("INT", 0)) or self.match_lookahead_terminal("INT128", 0)) or self.match_lookahead_terminal("INT32", 0)) or self.match_lookahead_terminal("STRING", 0)) or self.match_lookahead_terminal("UINT128", 0)) or self.match_lookahead_terminal("UINT32", 0))
        raw_values1030 = xs1027
        self.consume_literal(")")
        _t1822 = logic_pb2.Attribute(name=name1026, args=raw_values1030)
        result1032 = _t1822
        self.record_span(span_start1031, "Attribute")
        return result1032

    def parse_algorithm(self) -> logic_pb2.Algorithm:
        span_start1038 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("algorithm")
        xs1033 = []
        cond1034 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1034:
            _t1823 = self.parse_relation_id()
            item1035 = _t1823
            xs1033.append(item1035)
            cond1034 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1036 = xs1033
        _t1824 = self.parse_script()
        script1037 = _t1824
        self.consume_literal(")")
        _t1825 = logic_pb2.Algorithm(body=script1037)
        getattr(_t1825, 'global').extend(relation_ids1036)
        result1039 = _t1825
        self.record_span(span_start1038, "Algorithm")
        return result1039

    def parse_script(self) -> logic_pb2.Script:
        span_start1044 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("script")
        xs1040 = []
        cond1041 = self.match_lookahead_literal("(", 0)
        while cond1041:
            _t1826 = self.parse_construct()
            item1042 = _t1826
            xs1040.append(item1042)
            cond1041 = self.match_lookahead_literal("(", 0)
        constructs1043 = xs1040
        self.consume_literal(")")
        _t1827 = logic_pb2.Script(constructs=constructs1043)
        result1045 = _t1827
        self.record_span(span_start1044, "Script")
        return result1045

    def parse_construct(self) -> logic_pb2.Construct:
        span_start1049 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1829 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1830 = 1
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1831 = 1
                    else:
                        if self.match_lookahead_literal("loop", 1):
                            _t1832 = 0
                        else:
                            if self.match_lookahead_literal("break", 1):
                                _t1833 = 1
                            else:
                                if self.match_lookahead_literal("assign", 1):
                                    _t1834 = 1
                                else:
                                    _t1834 = -1
                                _t1833 = _t1834
                            _t1832 = _t1833
                        _t1831 = _t1832
                    _t1830 = _t1831
                _t1829 = _t1830
            _t1828 = _t1829
        else:
            _t1828 = -1
        prediction1046 = _t1828
        if prediction1046 == 1:
            _t1836 = self.parse_instruction()
            instruction1048 = _t1836
            _t1837 = logic_pb2.Construct(instruction=instruction1048)
            _t1835 = _t1837
        else:
            if prediction1046 == 0:
                _t1839 = self.parse_loop()
                loop1047 = _t1839
                _t1840 = logic_pb2.Construct(loop=loop1047)
                _t1838 = _t1840
            else:
                raise ParseError("Unexpected token in construct" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1835 = _t1838
        result1050 = _t1835
        self.record_span(span_start1049, "Construct")
        return result1050

    def parse_loop(self) -> logic_pb2.Loop:
        span_start1053 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("loop")
        _t1841 = self.parse_init()
        init1051 = _t1841
        _t1842 = self.parse_script()
        script1052 = _t1842
        self.consume_literal(")")
        _t1843 = logic_pb2.Loop(init=init1051, body=script1052)
        result1054 = _t1843
        self.record_span(span_start1053, "Loop")
        return result1054

    def parse_init(self) -> Sequence[logic_pb2.Instruction]:
        self.consume_literal("(")
        self.consume_literal("init")
        xs1055 = []
        cond1056 = self.match_lookahead_literal("(", 0)
        while cond1056:
            _t1844 = self.parse_instruction()
            item1057 = _t1844
            xs1055.append(item1057)
            cond1056 = self.match_lookahead_literal("(", 0)
        instructions1058 = xs1055
        self.consume_literal(")")
        return instructions1058

    def parse_instruction(self) -> logic_pb2.Instruction:
        span_start1065 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("upsert", 1):
                _t1846 = 1
            else:
                if self.match_lookahead_literal("monus", 1):
                    _t1847 = 4
                else:
                    if self.match_lookahead_literal("monoid", 1):
                        _t1848 = 3
                    else:
                        if self.match_lookahead_literal("break", 1):
                            _t1849 = 2
                        else:
                            if self.match_lookahead_literal("assign", 1):
                                _t1850 = 0
                            else:
                                _t1850 = -1
                            _t1849 = _t1850
                        _t1848 = _t1849
                    _t1847 = _t1848
                _t1846 = _t1847
            _t1845 = _t1846
        else:
            _t1845 = -1
        prediction1059 = _t1845
        if prediction1059 == 4:
            _t1852 = self.parse_monus_def()
            monus_def1064 = _t1852
            _t1853 = logic_pb2.Instruction(monus_def=monus_def1064)
            _t1851 = _t1853
        else:
            if prediction1059 == 3:
                _t1855 = self.parse_monoid_def()
                monoid_def1063 = _t1855
                _t1856 = logic_pb2.Instruction(monoid_def=monoid_def1063)
                _t1854 = _t1856
            else:
                if prediction1059 == 2:
                    _t1858 = self.parse_break()
                    break1062 = _t1858
                    _t1859 = logic_pb2.Instruction()
                    getattr(_t1859, 'break').CopyFrom(break1062)
                    _t1857 = _t1859
                else:
                    if prediction1059 == 1:
                        _t1861 = self.parse_upsert()
                        upsert1061 = _t1861
                        _t1862 = logic_pb2.Instruction(upsert=upsert1061)
                        _t1860 = _t1862
                    else:
                        if prediction1059 == 0:
                            _t1864 = self.parse_assign()
                            assign1060 = _t1864
                            _t1865 = logic_pb2.Instruction(assign=assign1060)
                            _t1863 = _t1865
                        else:
                            raise ParseError("Unexpected token in instruction" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t1860 = _t1863
                    _t1857 = _t1860
                _t1854 = _t1857
            _t1851 = _t1854
        result1066 = _t1851
        self.record_span(span_start1065, "Instruction")
        return result1066

    def parse_assign(self) -> logic_pb2.Assign:
        span_start1070 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("assign")
        _t1866 = self.parse_relation_id()
        relation_id1067 = _t1866
        _t1867 = self.parse_abstraction()
        abstraction1068 = _t1867
        if self.match_lookahead_literal("(", 0):
            _t1869 = self.parse_attrs()
            _t1868 = _t1869
        else:
            _t1868 = None
        attrs1069 = _t1868
        self.consume_literal(")")
        _t1870 = logic_pb2.Assign(name=relation_id1067, body=abstraction1068, attrs=(attrs1069 if attrs1069 is not None else []))
        result1071 = _t1870
        self.record_span(span_start1070, "Assign")
        return result1071

    def parse_upsert(self) -> logic_pb2.Upsert:
        span_start1075 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("upsert")
        _t1871 = self.parse_relation_id()
        relation_id1072 = _t1871
        _t1872 = self.parse_abstraction_with_arity()
        abstraction_with_arity1073 = _t1872
        if self.match_lookahead_literal("(", 0):
            _t1874 = self.parse_attrs()
            _t1873 = _t1874
        else:
            _t1873 = None
        attrs1074 = _t1873
        self.consume_literal(")")
        _t1875 = logic_pb2.Upsert(name=relation_id1072, body=abstraction_with_arity1073[0], attrs=(attrs1074 if attrs1074 is not None else []), value_arity=abstraction_with_arity1073[1])
        result1076 = _t1875
        self.record_span(span_start1075, "Upsert")
        return result1076

    def parse_abstraction_with_arity(self) -> tuple[logic_pb2.Abstraction, int]:
        self.consume_literal("(")
        _t1876 = self.parse_bindings()
        bindings1077 = _t1876
        _t1877 = self.parse_formula()
        formula1078 = _t1877
        self.consume_literal(")")
        _t1878 = logic_pb2.Abstraction(vars=(list(bindings1077[0]) + list(bindings1077[1] if bindings1077[1] is not None else [])), value=formula1078)
        return (_t1878, len(bindings1077[1]),)

    def parse_break(self) -> logic_pb2.Break:
        span_start1082 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("break")
        _t1879 = self.parse_relation_id()
        relation_id1079 = _t1879
        _t1880 = self.parse_abstraction()
        abstraction1080 = _t1880
        if self.match_lookahead_literal("(", 0):
            _t1882 = self.parse_attrs()
            _t1881 = _t1882
        else:
            _t1881 = None
        attrs1081 = _t1881
        self.consume_literal(")")
        _t1883 = logic_pb2.Break(name=relation_id1079, body=abstraction1080, attrs=(attrs1081 if attrs1081 is not None else []))
        result1083 = _t1883
        self.record_span(span_start1082, "Break")
        return result1083

    def parse_monoid_def(self) -> logic_pb2.MonoidDef:
        span_start1088 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monoid")
        _t1884 = self.parse_monoid()
        monoid1084 = _t1884
        _t1885 = self.parse_relation_id()
        relation_id1085 = _t1885
        _t1886 = self.parse_abstraction_with_arity()
        abstraction_with_arity1086 = _t1886
        if self.match_lookahead_literal("(", 0):
            _t1888 = self.parse_attrs()
            _t1887 = _t1888
        else:
            _t1887 = None
        attrs1087 = _t1887
        self.consume_literal(")")
        _t1889 = logic_pb2.MonoidDef(monoid=monoid1084, name=relation_id1085, body=abstraction_with_arity1086[0], attrs=(attrs1087 if attrs1087 is not None else []), value_arity=abstraction_with_arity1086[1])
        result1089 = _t1889
        self.record_span(span_start1088, "MonoidDef")
        return result1089

    def parse_monoid(self) -> logic_pb2.Monoid:
        span_start1095 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("sum", 1):
                _t1891 = 3
            else:
                if self.match_lookahead_literal("or", 1):
                    _t1892 = 0
                else:
                    if self.match_lookahead_literal("min", 1):
                        _t1893 = 1
                    else:
                        if self.match_lookahead_literal("max", 1):
                            _t1894 = 2
                        else:
                            _t1894 = -1
                        _t1893 = _t1894
                    _t1892 = _t1893
                _t1891 = _t1892
            _t1890 = _t1891
        else:
            _t1890 = -1
        prediction1090 = _t1890
        if prediction1090 == 3:
            _t1896 = self.parse_sum_monoid()
            sum_monoid1094 = _t1896
            _t1897 = logic_pb2.Monoid(sum_monoid=sum_monoid1094)
            _t1895 = _t1897
        else:
            if prediction1090 == 2:
                _t1899 = self.parse_max_monoid()
                max_monoid1093 = _t1899
                _t1900 = logic_pb2.Monoid(max_monoid=max_monoid1093)
                _t1898 = _t1900
            else:
                if prediction1090 == 1:
                    _t1902 = self.parse_min_monoid()
                    min_monoid1092 = _t1902
                    _t1903 = logic_pb2.Monoid(min_monoid=min_monoid1092)
                    _t1901 = _t1903
                else:
                    if prediction1090 == 0:
                        _t1905 = self.parse_or_monoid()
                        or_monoid1091 = _t1905
                        _t1906 = logic_pb2.Monoid(or_monoid=or_monoid1091)
                        _t1904 = _t1906
                    else:
                        raise ParseError("Unexpected token in monoid" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1901 = _t1904
                _t1898 = _t1901
            _t1895 = _t1898
        result1096 = _t1895
        self.record_span(span_start1095, "Monoid")
        return result1096

    def parse_or_monoid(self) -> logic_pb2.OrMonoid:
        span_start1097 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("or")
        self.consume_literal(")")
        _t1907 = logic_pb2.OrMonoid()
        result1098 = _t1907
        self.record_span(span_start1097, "OrMonoid")
        return result1098

    def parse_min_monoid(self) -> logic_pb2.MinMonoid:
        span_start1100 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("min")
        _t1908 = self.parse_type()
        type1099 = _t1908
        self.consume_literal(")")
        _t1909 = logic_pb2.MinMonoid(type=type1099)
        result1101 = _t1909
        self.record_span(span_start1100, "MinMonoid")
        return result1101

    def parse_max_monoid(self) -> logic_pb2.MaxMonoid:
        span_start1103 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("max")
        _t1910 = self.parse_type()
        type1102 = _t1910
        self.consume_literal(")")
        _t1911 = logic_pb2.MaxMonoid(type=type1102)
        result1104 = _t1911
        self.record_span(span_start1103, "MaxMonoid")
        return result1104

    def parse_sum_monoid(self) -> logic_pb2.SumMonoid:
        span_start1106 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("sum")
        _t1912 = self.parse_type()
        type1105 = _t1912
        self.consume_literal(")")
        _t1913 = logic_pb2.SumMonoid(type=type1105)
        result1107 = _t1913
        self.record_span(span_start1106, "SumMonoid")
        return result1107

    def parse_monus_def(self) -> logic_pb2.MonusDef:
        span_start1112 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("monus")
        _t1914 = self.parse_monoid()
        monoid1108 = _t1914
        _t1915 = self.parse_relation_id()
        relation_id1109 = _t1915
        _t1916 = self.parse_abstraction_with_arity()
        abstraction_with_arity1110 = _t1916
        if self.match_lookahead_literal("(", 0):
            _t1918 = self.parse_attrs()
            _t1917 = _t1918
        else:
            _t1917 = None
        attrs1111 = _t1917
        self.consume_literal(")")
        _t1919 = logic_pb2.MonusDef(monoid=monoid1108, name=relation_id1109, body=abstraction_with_arity1110[0], attrs=(attrs1111 if attrs1111 is not None else []), value_arity=abstraction_with_arity1110[1])
        result1113 = _t1919
        self.record_span(span_start1112, "MonusDef")
        return result1113

    def parse_constraint(self) -> logic_pb2.Constraint:
        span_start1118 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("functional_dependency")
        _t1920 = self.parse_relation_id()
        relation_id1114 = _t1920
        _t1921 = self.parse_abstraction()
        abstraction1115 = _t1921
        _t1922 = self.parse_functional_dependency_keys()
        functional_dependency_keys1116 = _t1922
        _t1923 = self.parse_functional_dependency_values()
        functional_dependency_values1117 = _t1923
        self.consume_literal(")")
        _t1924 = logic_pb2.FunctionalDependency(guard=abstraction1115, keys=functional_dependency_keys1116, values=functional_dependency_values1117)
        _t1925 = logic_pb2.Constraint(name=relation_id1114, functional_dependency=_t1924)
        result1119 = _t1925
        self.record_span(span_start1118, "Constraint")
        return result1119

    def parse_functional_dependency_keys(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("keys")
        xs1120 = []
        cond1121 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1121:
            _t1926 = self.parse_var()
            item1122 = _t1926
            xs1120.append(item1122)
            cond1121 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1123 = xs1120
        self.consume_literal(")")
        return vars1123

    def parse_functional_dependency_values(self) -> Sequence[logic_pb2.Var]:
        self.consume_literal("(")
        self.consume_literal("values")
        xs1124 = []
        cond1125 = self.match_lookahead_terminal("SYMBOL", 0)
        while cond1125:
            _t1927 = self.parse_var()
            item1126 = _t1927
            xs1124.append(item1126)
            cond1125 = self.match_lookahead_terminal("SYMBOL", 0)
        vars1127 = xs1124
        self.consume_literal(")")
        return vars1127

    def parse_data(self) -> logic_pb2.Data:
        span_start1133 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("iceberg_data", 1):
                _t1929 = 3
            else:
                if self.match_lookahead_literal("edb", 1):
                    _t1930 = 0
                else:
                    if self.match_lookahead_literal("csv_data", 1):
                        _t1931 = 2
                    else:
                        if self.match_lookahead_literal("betree_relation", 1):
                            _t1932 = 1
                        else:
                            _t1932 = -1
                        _t1931 = _t1932
                    _t1930 = _t1931
                _t1929 = _t1930
            _t1928 = _t1929
        else:
            _t1928 = -1
        prediction1128 = _t1928
        if prediction1128 == 3:
            _t1934 = self.parse_iceberg_data()
            iceberg_data1132 = _t1934
            _t1935 = logic_pb2.Data(iceberg_data=iceberg_data1132)
            _t1933 = _t1935
        else:
            if prediction1128 == 2:
                _t1937 = self.parse_csv_data()
                csv_data1131 = _t1937
                _t1938 = logic_pb2.Data(csv_data=csv_data1131)
                _t1936 = _t1938
            else:
                if prediction1128 == 1:
                    _t1940 = self.parse_betree_relation()
                    betree_relation1130 = _t1940
                    _t1941 = logic_pb2.Data(betree_relation=betree_relation1130)
                    _t1939 = _t1941
                else:
                    if prediction1128 == 0:
                        _t1943 = self.parse_edb()
                        edb1129 = _t1943
                        _t1944 = logic_pb2.Data(edb=edb1129)
                        _t1942 = _t1944
                    else:
                        raise ParseError("Unexpected token in data" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                    _t1939 = _t1942
                _t1936 = _t1939
            _t1933 = _t1936
        result1134 = _t1933
        self.record_span(span_start1133, "Data")
        return result1134

    def parse_edb(self) -> logic_pb2.EDB:
        span_start1138 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("edb")
        _t1945 = self.parse_relation_id()
        relation_id1135 = _t1945
        _t1946 = self.parse_edb_path()
        edb_path1136 = _t1946
        _t1947 = self.parse_edb_types()
        edb_types1137 = _t1947
        self.consume_literal(")")
        _t1948 = logic_pb2.EDB(target_id=relation_id1135, path=edb_path1136, types=edb_types1137)
        result1139 = _t1948
        self.record_span(span_start1138, "EDB")
        return result1139

    def parse_edb_path(self) -> Sequence[str]:
        self.consume_literal("[")
        xs1140 = []
        cond1141 = self.match_lookahead_terminal("STRING", 0)
        while cond1141:
            item1142 = self.consume_terminal("STRING")
            xs1140.append(item1142)
            cond1141 = self.match_lookahead_terminal("STRING", 0)
        strings1143 = xs1140
        self.consume_literal("]")
        return strings1143

    def parse_edb_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("[")
        xs1144 = []
        cond1145 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1145:
            _t1949 = self.parse_type()
            item1146 = _t1949
            xs1144.append(item1146)
            cond1145 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1147 = xs1144
        self.consume_literal("]")
        return types1147

    def parse_betree_relation(self) -> logic_pb2.BeTreeRelation:
        span_start1150 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_relation")
        _t1950 = self.parse_relation_id()
        relation_id1148 = _t1950
        _t1951 = self.parse_betree_info()
        betree_info1149 = _t1951
        self.consume_literal(")")
        _t1952 = logic_pb2.BeTreeRelation(name=relation_id1148, relation_info=betree_info1149)
        result1151 = _t1952
        self.record_span(span_start1150, "BeTreeRelation")
        return result1151

    def parse_betree_info(self) -> logic_pb2.BeTreeInfo:
        span_start1155 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("betree_info")
        _t1953 = self.parse_betree_info_key_types()
        betree_info_key_types1152 = _t1953
        _t1954 = self.parse_betree_info_value_types()
        betree_info_value_types1153 = _t1954
        _t1955 = self.parse_config_dict()
        config_dict1154 = _t1955
        self.consume_literal(")")
        _t1956 = self.construct_betree_info(betree_info_key_types1152, betree_info_value_types1153, config_dict1154)
        result1156 = _t1956
        self.record_span(span_start1155, "BeTreeInfo")
        return result1156

    def parse_betree_info_key_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("key_types")
        xs1157 = []
        cond1158 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1158:
            _t1957 = self.parse_type()
            item1159 = _t1957
            xs1157.append(item1159)
            cond1158 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1160 = xs1157
        self.consume_literal(")")
        return types1160

    def parse_betree_info_value_types(self) -> Sequence[logic_pb2.Type]:
        self.consume_literal("(")
        self.consume_literal("value_types")
        xs1161 = []
        cond1162 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1162:
            _t1958 = self.parse_type()
            item1163 = _t1958
            xs1161.append(item1163)
            cond1162 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1164 = xs1161
        self.consume_literal(")")
        return types1164

    def parse_csv_data(self) -> logic_pb2.CSVData:
        span_start1169 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_data")
        _t1959 = self.parse_csvlocator()
        csvlocator1165 = _t1959
        _t1960 = self.parse_csv_config()
        csv_config1166 = _t1960
        _t1961 = self.parse_gnf_columns()
        gnf_columns1167 = _t1961
        _t1962 = self.parse_csv_asof()
        csv_asof1168 = _t1962
        self.consume_literal(")")
        _t1963 = logic_pb2.CSVData(locator=csvlocator1165, config=csv_config1166, columns=gnf_columns1167, asof=csv_asof1168)
        result1170 = _t1963
        self.record_span(span_start1169, "CSVData")
        return result1170

    def parse_csvlocator(self) -> logic_pb2.CSVLocator:
        span_start1173 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_locator")
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("paths", 1)):
            _t1965 = self.parse_csv_locator_paths()
            _t1964 = _t1965
        else:
            _t1964 = None
        csv_locator_paths1171 = _t1964
        if self.match_lookahead_literal("(", 0):
            _t1967 = self.parse_csv_locator_inline_data()
            _t1966 = _t1967
        else:
            _t1966 = None
        csv_locator_inline_data1172 = _t1966
        self.consume_literal(")")
        _t1968 = logic_pb2.CSVLocator(paths=(csv_locator_paths1171 if csv_locator_paths1171 is not None else []), inline_data=(csv_locator_inline_data1172 if csv_locator_inline_data1172 is not None else "").encode())
        result1174 = _t1968
        self.record_span(span_start1173, "CSVLocator")
        return result1174

    def parse_csv_locator_paths(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("paths")
        xs1175 = []
        cond1176 = self.match_lookahead_terminal("STRING", 0)
        while cond1176:
            item1177 = self.consume_terminal("STRING")
            xs1175.append(item1177)
            cond1176 = self.match_lookahead_terminal("STRING", 0)
        strings1178 = xs1175
        self.consume_literal(")")
        return strings1178

    def parse_csv_locator_inline_data(self) -> str:
        self.consume_literal("(")
        self.consume_literal("inline_data")
        string1179 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1179

    def parse_csv_config(self) -> logic_pb2.CSVConfig:
        span_start1181 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("csv_config")
        _t1969 = self.parse_config_dict()
        config_dict1180 = _t1969
        self.consume_literal(")")
        _t1970 = self.construct_csv_config(config_dict1180)
        result1182 = _t1970
        self.record_span(span_start1181, "CSVConfig")
        return result1182

    def parse_gnf_columns(self) -> Sequence[logic_pb2.GNFColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1183 = []
        cond1184 = self.match_lookahead_literal("(", 0)
        while cond1184:
            _t1971 = self.parse_gnf_column()
            item1185 = _t1971
            xs1183.append(item1185)
            cond1184 = self.match_lookahead_literal("(", 0)
        gnf_columns1186 = xs1183
        self.consume_literal(")")
        return gnf_columns1186

    def parse_gnf_column(self) -> logic_pb2.GNFColumn:
        span_start1193 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        _t1972 = self.parse_gnf_column_path()
        gnf_column_path1187 = _t1972
        if (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0)):
            _t1974 = self.parse_relation_id()
            _t1973 = _t1974
        else:
            _t1973 = None
        relation_id1188 = _t1973
        self.consume_literal("[")
        xs1189 = []
        cond1190 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        while cond1190:
            _t1975 = self.parse_type()
            item1191 = _t1975
            xs1189.append(item1191)
            cond1190 = (((((((((((((self.match_lookahead_literal("(", 0) or self.match_lookahead_literal("BOOLEAN", 0)) or self.match_lookahead_literal("DATE", 0)) or self.match_lookahead_literal("DATETIME", 0)) or self.match_lookahead_literal("FLOAT", 0)) or self.match_lookahead_literal("FLOAT32", 0)) or self.match_lookahead_literal("INT", 0)) or self.match_lookahead_literal("INT128", 0)) or self.match_lookahead_literal("INT32", 0)) or self.match_lookahead_literal("MISSING", 0)) or self.match_lookahead_literal("STRING", 0)) or self.match_lookahead_literal("UINT128", 0)) or self.match_lookahead_literal("UINT32", 0)) or self.match_lookahead_literal("UNKNOWN", 0))
        types1192 = xs1189
        self.consume_literal("]")
        self.consume_literal(")")
        _t1976 = logic_pb2.GNFColumn(column_path=gnf_column_path1187, target_id=relation_id1188, types=types1192)
        result1194 = _t1976
        self.record_span(span_start1193, "GNFColumn")
        return result1194

    def parse_gnf_column_path(self) -> Sequence[str]:
        if self.match_lookahead_literal("[", 0):
            _t1977 = 1
        else:
            if self.match_lookahead_terminal("STRING", 0):
                _t1978 = 0
            else:
                _t1978 = -1
            _t1977 = _t1978
        prediction1195 = _t1977
        if prediction1195 == 1:
            self.consume_literal("[")
            xs1197 = []
            cond1198 = self.match_lookahead_terminal("STRING", 0)
            while cond1198:
                item1199 = self.consume_terminal("STRING")
                xs1197.append(item1199)
                cond1198 = self.match_lookahead_terminal("STRING", 0)
            strings1200 = xs1197
            self.consume_literal("]")
            _t1979 = strings1200
        else:
            if prediction1195 == 0:
                string1196 = self.consume_terminal("STRING")
                _t1980 = [string1196]
            else:
                raise ParseError("Unexpected token in gnf_column_path" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t1979 = _t1980
        return _t1979

    def parse_csv_asof(self) -> str:
        self.consume_literal("(")
        self.consume_literal("asof")
        string1201 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1201

    def parse_iceberg_data(self) -> logic_pb2.IcebergData:
        span_start1208 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_data")
        _t1981 = self.parse_iceberg_locator()
        iceberg_locator1202 = _t1981
        _t1982 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1203 = _t1982
        _t1983 = self.parse_gnf_columns()
        gnf_columns1204 = _t1983
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("from_snapshot", 1)):
            _t1985 = self.parse_iceberg_from_snapshot()
            _t1984 = _t1985
        else:
            _t1984 = None
        iceberg_from_snapshot1205 = _t1984
        if self.match_lookahead_literal("(", 0):
            _t1987 = self.parse_iceberg_to_snapshot()
            _t1986 = _t1987
        else:
            _t1986 = None
        iceberg_to_snapshot1206 = _t1986
        _t1988 = self.parse_boolean_value()
        boolean_value1207 = _t1988
        self.consume_literal(")")
        _t1989 = self.construct_iceberg_data(iceberg_locator1202, iceberg_catalog_config1203, gnf_columns1204, iceberg_from_snapshot1205, iceberg_to_snapshot1206, boolean_value1207)
        result1209 = _t1989
        self.record_span(span_start1208, "IcebergData")
        return result1209

    def parse_iceberg_locator(self) -> logic_pb2.IcebergLocator:
        span_start1213 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_locator")
        _t1990 = self.parse_iceberg_locator_table_name()
        iceberg_locator_table_name1210 = _t1990
        _t1991 = self.parse_iceberg_locator_namespace()
        iceberg_locator_namespace1211 = _t1991
        _t1992 = self.parse_iceberg_locator_warehouse()
        iceberg_locator_warehouse1212 = _t1992
        self.consume_literal(")")
        _t1993 = logic_pb2.IcebergLocator(table_name=iceberg_locator_table_name1210, namespace=iceberg_locator_namespace1211, warehouse=iceberg_locator_warehouse1212)
        result1214 = _t1993
        self.record_span(span_start1213, "IcebergLocator")
        return result1214

    def parse_iceberg_locator_table_name(self) -> str:
        self.consume_literal("(")
        self.consume_literal("table_name")
        string1215 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1215

    def parse_iceberg_locator_namespace(self) -> Sequence[str]:
        self.consume_literal("(")
        self.consume_literal("namespace")
        xs1216 = []
        cond1217 = self.match_lookahead_terminal("STRING", 0)
        while cond1217:
            item1218 = self.consume_terminal("STRING")
            xs1216.append(item1218)
            cond1217 = self.match_lookahead_terminal("STRING", 0)
        strings1219 = xs1216
        self.consume_literal(")")
        return strings1219

    def parse_iceberg_locator_warehouse(self) -> str:
        self.consume_literal("(")
        self.consume_literal("warehouse")
        string1220 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1220

    def parse_iceberg_catalog_config(self) -> logic_pb2.IcebergCatalogConfig:
        span_start1225 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("iceberg_catalog_config")
        _t1994 = self.parse_iceberg_catalog_uri()
        iceberg_catalog_uri1221 = _t1994
        if (self.match_lookahead_literal("(", 0) and self.match_lookahead_literal("scope", 1)):
            _t1996 = self.parse_iceberg_catalog_config_scope()
            _t1995 = _t1996
        else:
            _t1995 = None
        iceberg_catalog_config_scope1222 = _t1995
        _t1997 = self.parse_iceberg_properties()
        iceberg_properties1223 = _t1997
        _t1998 = self.parse_iceberg_auth_properties()
        iceberg_auth_properties1224 = _t1998
        self.consume_literal(")")
        _t1999 = self.construct_iceberg_catalog_config(iceberg_catalog_uri1221, iceberg_catalog_config_scope1222, iceberg_properties1223, iceberg_auth_properties1224)
        result1226 = _t1999
        self.record_span(span_start1225, "IcebergCatalogConfig")
        return result1226

    def parse_iceberg_catalog_uri(self) -> str:
        self.consume_literal("(")
        self.consume_literal("catalog_uri")
        string1227 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1227

    def parse_iceberg_catalog_config_scope(self) -> str:
        self.consume_literal("(")
        self.consume_literal("scope")
        string1228 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1228

    def parse_iceberg_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("properties")
        xs1229 = []
        cond1230 = self.match_lookahead_literal("(", 0)
        while cond1230:
            _t2000 = self.parse_iceberg_property_entry()
            item1231 = _t2000
            xs1229.append(item1231)
            cond1230 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1232 = xs1229
        self.consume_literal(")")
        return iceberg_property_entrys1232

    def parse_iceberg_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1233 = self.consume_terminal("STRING")
        string_31234 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1233, string_31234,)

    def parse_iceberg_auth_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("auth_properties")
        xs1235 = []
        cond1236 = self.match_lookahead_literal("(", 0)
        while cond1236:
            _t2001 = self.parse_iceberg_masked_property_entry()
            item1237 = _t2001
            xs1235.append(item1237)
            cond1236 = self.match_lookahead_literal("(", 0)
        iceberg_masked_property_entrys1238 = xs1235
        self.consume_literal(")")
        return iceberg_masked_property_entrys1238

    def parse_iceberg_masked_property_entry(self) -> tuple[str, str]:
        self.consume_literal("(")
        self.consume_literal("prop")
        string1239 = self.consume_terminal("STRING")
        string_31240 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return (string1239, string_31240,)

    def parse_iceberg_from_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("from_snapshot")
        string1241 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1241

    def parse_iceberg_to_snapshot(self) -> str:
        self.consume_literal("(")
        self.consume_literal("to_snapshot")
        string1242 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1242

    def parse_undefine(self) -> transactions_pb2.Undefine:
        span_start1244 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("undefine")
        _t2002 = self.parse_fragment_id()
        fragment_id1243 = _t2002
        self.consume_literal(")")
        _t2003 = transactions_pb2.Undefine(fragment_id=fragment_id1243)
        result1245 = _t2003
        self.record_span(span_start1244, "Undefine")
        return result1245

    def parse_context(self) -> transactions_pb2.Context:
        span_start1250 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("context")
        xs1246 = []
        cond1247 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        while cond1247:
            _t2004 = self.parse_relation_id()
            item1248 = _t2004
            xs1246.append(item1248)
            cond1247 = (self.match_lookahead_literal(":", 0) or self.match_lookahead_terminal("UINT128", 0))
        relation_ids1249 = xs1246
        self.consume_literal(")")
        _t2005 = transactions_pb2.Context(relations=relation_ids1249)
        result1251 = _t2005
        self.record_span(span_start1250, "Context")
        return result1251

    def parse_snapshot(self) -> transactions_pb2.Snapshot:
        span_start1257 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("snapshot")
        _t2006 = self.parse_edb_path()
        edb_path1252 = _t2006
        xs1253 = []
        cond1254 = self.match_lookahead_literal("[", 0)
        while cond1254:
            _t2007 = self.parse_snapshot_mapping()
            item1255 = _t2007
            xs1253.append(item1255)
            cond1254 = self.match_lookahead_literal("[", 0)
        snapshot_mappings1256 = xs1253
        self.consume_literal(")")
        _t2008 = transactions_pb2.Snapshot(prefix=edb_path1252, mappings=snapshot_mappings1256)
        result1258 = _t2008
        self.record_span(span_start1257, "Snapshot")
        return result1258

    def parse_snapshot_mapping(self) -> transactions_pb2.SnapshotMapping:
        span_start1261 = self.span_start()
        _t2009 = self.parse_edb_path()
        edb_path1259 = _t2009
        _t2010 = self.parse_relation_id()
        relation_id1260 = _t2010
        _t2011 = transactions_pb2.SnapshotMapping(destination_path=edb_path1259, source_relation=relation_id1260)
        result1262 = _t2011
        self.record_span(span_start1261, "SnapshotMapping")
        return result1262

    def parse_epoch_reads(self) -> Sequence[transactions_pb2.Read]:
        self.consume_literal("(")
        self.consume_literal("reads")
        xs1263 = []
        cond1264 = self.match_lookahead_literal("(", 0)
        while cond1264:
            _t2012 = self.parse_read()
            item1265 = _t2012
            xs1263.append(item1265)
            cond1264 = self.match_lookahead_literal("(", 0)
        reads1266 = xs1263
        self.consume_literal(")")
        return reads1266

    def parse_read(self) -> transactions_pb2.Read:
        span_start1273 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("what_if", 1):
                _t2014 = 2
            else:
                if self.match_lookahead_literal("output", 1):
                    _t2015 = 1
                else:
                    if self.match_lookahead_literal("export_iceberg", 1):
                        _t2016 = 4
                    else:
                        if self.match_lookahead_literal("export", 1):
                            _t2017 = 4
                        else:
                            if self.match_lookahead_literal("demand", 1):
                                _t2018 = 0
                            else:
                                if self.match_lookahead_literal("abort", 1):
                                    _t2019 = 3
                                else:
                                    _t2019 = -1
                                _t2018 = _t2019
                            _t2017 = _t2018
                        _t2016 = _t2017
                    _t2015 = _t2016
                _t2014 = _t2015
            _t2013 = _t2014
        else:
            _t2013 = -1
        prediction1267 = _t2013
        if prediction1267 == 4:
            _t2021 = self.parse_export()
            export1272 = _t2021
            _t2022 = transactions_pb2.Read(export=export1272)
            _t2020 = _t2022
        else:
            if prediction1267 == 3:
                _t2024 = self.parse_abort()
                abort1271 = _t2024
                _t2025 = transactions_pb2.Read(abort=abort1271)
                _t2023 = _t2025
            else:
                if prediction1267 == 2:
                    _t2027 = self.parse_what_if()
                    what_if1270 = _t2027
                    _t2028 = transactions_pb2.Read(what_if=what_if1270)
                    _t2026 = _t2028
                else:
                    if prediction1267 == 1:
                        _t2030 = self.parse_output()
                        output1269 = _t2030
                        _t2031 = transactions_pb2.Read(output=output1269)
                        _t2029 = _t2031
                    else:
                        if prediction1267 == 0:
                            _t2033 = self.parse_demand()
                            demand1268 = _t2033
                            _t2034 = transactions_pb2.Read(demand=demand1268)
                            _t2032 = _t2034
                        else:
                            raise ParseError("Unexpected token in read" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
                        _t2029 = _t2032
                    _t2026 = _t2029
                _t2023 = _t2026
            _t2020 = _t2023
        result1274 = _t2020
        self.record_span(span_start1273, "Read")
        return result1274

    def parse_demand(self) -> transactions_pb2.Demand:
        span_start1276 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("demand")
        _t2035 = self.parse_relation_id()
        relation_id1275 = _t2035
        self.consume_literal(")")
        _t2036 = transactions_pb2.Demand(relation_id=relation_id1275)
        result1277 = _t2036
        self.record_span(span_start1276, "Demand")
        return result1277

    def parse_output(self) -> transactions_pb2.Output:
        span_start1280 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("output")
        _t2037 = self.parse_name()
        name1278 = _t2037
        _t2038 = self.parse_relation_id()
        relation_id1279 = _t2038
        self.consume_literal(")")
        _t2039 = transactions_pb2.Output(name=name1278, relation_id=relation_id1279)
        result1281 = _t2039
        self.record_span(span_start1280, "Output")
        return result1281

    def parse_what_if(self) -> transactions_pb2.WhatIf:
        span_start1284 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("what_if")
        _t2040 = self.parse_name()
        name1282 = _t2040
        _t2041 = self.parse_epoch()
        epoch1283 = _t2041
        self.consume_literal(")")
        _t2042 = transactions_pb2.WhatIf(branch=name1282, epoch=epoch1283)
        result1285 = _t2042
        self.record_span(span_start1284, "WhatIf")
        return result1285

    def parse_abort(self) -> transactions_pb2.Abort:
        span_start1288 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("abort")
        if (self.match_lookahead_literal(":", 0) and self.match_lookahead_terminal("SYMBOL", 1)):
            _t2044 = self.parse_name()
            _t2043 = _t2044
        else:
            _t2043 = None
        name1286 = _t2043
        _t2045 = self.parse_relation_id()
        relation_id1287 = _t2045
        self.consume_literal(")")
        _t2046 = transactions_pb2.Abort(name=(name1286 if name1286 is not None else "abort"), relation_id=relation_id1287)
        result1289 = _t2046
        self.record_span(span_start1288, "Abort")
        return result1289

    def parse_export(self) -> transactions_pb2.Export:
        span_start1293 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_iceberg", 1):
                _t2048 = 1
            else:
                if self.match_lookahead_literal("export", 1):
                    _t2049 = 0
                else:
                    _t2049 = -1
                _t2048 = _t2049
            _t2047 = _t2048
        else:
            _t2047 = -1
        prediction1290 = _t2047
        if prediction1290 == 1:
            self.consume_literal("(")
            self.consume_literal("export_iceberg")
            _t2051 = self.parse_export_iceberg_config()
            export_iceberg_config1292 = _t2051
            self.consume_literal(")")
            _t2052 = transactions_pb2.Export(iceberg_config=export_iceberg_config1292)
            _t2050 = _t2052
        else:
            if prediction1290 == 0:
                self.consume_literal("(")
                self.consume_literal("export")
                _t2054 = self.parse_export_csv_config()
                export_csv_config1291 = _t2054
                self.consume_literal(")")
                _t2055 = transactions_pb2.Export(csv_config=export_csv_config1291)
                _t2053 = _t2055
            else:
                raise ParseError("Unexpected token in export" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2050 = _t2053
        result1294 = _t2050
        self.record_span(span_start1293, "Export")
        return result1294

    def parse_export_csv_config(self) -> transactions_pb2.ExportCSVConfig:
        span_start1302 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("export_csv_config_v2", 1):
                _t2057 = 0
            else:
                if self.match_lookahead_literal("export_csv_config", 1):
                    _t2058 = 1
                else:
                    _t2058 = -1
                _t2057 = _t2058
            _t2056 = _t2057
        else:
            _t2056 = -1
        prediction1295 = _t2056
        if prediction1295 == 1:
            self.consume_literal("(")
            self.consume_literal("export_csv_config")
            _t2060 = self.parse_export_csv_path()
            export_csv_path1299 = _t2060
            _t2061 = self.parse_export_csv_columns_list()
            export_csv_columns_list1300 = _t2061
            _t2062 = self.parse_config_dict()
            config_dict1301 = _t2062
            self.consume_literal(")")
            _t2063 = self.construct_export_csv_config(export_csv_path1299, export_csv_columns_list1300, config_dict1301)
            _t2059 = _t2063
        else:
            if prediction1295 == 0:
                self.consume_literal("(")
                self.consume_literal("export_csv_config_v2")
                _t2065 = self.parse_export_csv_path()
                export_csv_path1296 = _t2065
                _t2066 = self.parse_export_csv_source()
                export_csv_source1297 = _t2066
                _t2067 = self.parse_csv_config()
                csv_config1298 = _t2067
                self.consume_literal(")")
                _t2068 = self.construct_export_csv_config_with_source(export_csv_path1296, export_csv_source1297, csv_config1298)
                _t2064 = _t2068
            else:
                raise ParseError("Unexpected token in export_csv_config" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2059 = _t2064
        result1303 = _t2059
        self.record_span(span_start1302, "ExportCSVConfig")
        return result1303

    def parse_export_csv_path(self) -> str:
        self.consume_literal("(")
        self.consume_literal("path")
        string1304 = self.consume_terminal("STRING")
        self.consume_literal(")")
        return string1304

    def parse_export_csv_source(self) -> transactions_pb2.ExportCSVSource:
        span_start1311 = self.span_start()
        if self.match_lookahead_literal("(", 0):
            if self.match_lookahead_literal("table_def", 1):
                _t2070 = 1
            else:
                if self.match_lookahead_literal("gnf_columns", 1):
                    _t2071 = 0
                else:
                    _t2071 = -1
                _t2070 = _t2071
            _t2069 = _t2070
        else:
            _t2069 = -1
        prediction1305 = _t2069
        if prediction1305 == 1:
            self.consume_literal("(")
            self.consume_literal("table_def")
            _t2073 = self.parse_relation_id()
            relation_id1310 = _t2073
            self.consume_literal(")")
            _t2074 = transactions_pb2.ExportCSVSource(table_def=relation_id1310)
            _t2072 = _t2074
        else:
            if prediction1305 == 0:
                self.consume_literal("(")
                self.consume_literal("gnf_columns")
                xs1306 = []
                cond1307 = self.match_lookahead_literal("(", 0)
                while cond1307:
                    _t2076 = self.parse_export_csv_column()
                    item1308 = _t2076
                    xs1306.append(item1308)
                    cond1307 = self.match_lookahead_literal("(", 0)
                export_csv_columns1309 = xs1306
                self.consume_literal(")")
                _t2077 = transactions_pb2.ExportCSVColumns(columns=export_csv_columns1309)
                _t2078 = transactions_pb2.ExportCSVSource(gnf_columns=_t2077)
                _t2075 = _t2078
            else:
                raise ParseError("Unexpected token in export_csv_source" + f": {self.lookahead(0).type}=`{self.lookahead(0).value}`")
            _t2072 = _t2075
        result1312 = _t2072
        self.record_span(span_start1311, "ExportCSVSource")
        return result1312

    def parse_export_csv_column(self) -> transactions_pb2.ExportCSVColumn:
        span_start1315 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1313 = self.consume_terminal("STRING")
        _t2079 = self.parse_relation_id()
        relation_id1314 = _t2079
        self.consume_literal(")")
        _t2080 = transactions_pb2.ExportCSVColumn(column_name=string1313, column_data=relation_id1314)
        result1316 = _t2080
        self.record_span(span_start1315, "ExportCSVColumn")
        return result1316

    def parse_export_csv_columns_list(self) -> Sequence[transactions_pb2.ExportCSVColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1317 = []
        cond1318 = self.match_lookahead_literal("(", 0)
        while cond1318:
            _t2081 = self.parse_export_csv_column()
            item1319 = _t2081
            xs1317.append(item1319)
            cond1318 = self.match_lookahead_literal("(", 0)
        export_csv_columns1320 = xs1317
        self.consume_literal(")")
        return export_csv_columns1320

    def parse_export_iceberg_config(self) -> transactions_pb2.ExportIcebergConfig:
        span_start1327 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("export_iceberg_config")
        _t2082 = self.parse_iceberg_locator()
        iceberg_locator1321 = _t2082
        _t2083 = self.parse_iceberg_catalog_config()
        iceberg_catalog_config1322 = _t2083
        _t2084 = self.parse_export_iceberg_table_def()
        export_iceberg_table_def1323 = _t2084
        _t2085 = self.parse_export_iceberg_columns()
        export_iceberg_columns1324 = _t2085
        _t2086 = self.parse_iceberg_table_properties()
        iceberg_table_properties1325 = _t2086
        if self.match_lookahead_literal("{", 0):
            _t2088 = self.parse_config_dict()
            _t2087 = _t2088
        else:
            _t2087 = None
        config_dict1326 = _t2087
        self.consume_literal(")")
        _t2089 = self.construct_export_iceberg_config_full(iceberg_locator1321, iceberg_catalog_config1322, export_iceberg_table_def1323, export_iceberg_columns1324, iceberg_table_properties1325, config_dict1326)
        result1328 = _t2089
        self.record_span(span_start1327, "ExportIcebergConfig")
        return result1328

    def parse_export_iceberg_table_def(self) -> logic_pb2.RelationId:
        span_start1330 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("table_def")
        _t2090 = self.parse_relation_id()
        relation_id1329 = _t2090
        self.consume_literal(")")
        result1331 = relation_id1329
        self.record_span(span_start1330, "RelationId")
        return result1331

    def parse_export_iceberg_columns(self) -> Sequence[transactions_pb2.ExportColumn]:
        self.consume_literal("(")
        self.consume_literal("columns")
        xs1332 = []
        cond1333 = self.match_lookahead_literal("(", 0)
        while cond1333:
            _t2091 = self.parse_export_iceberg_column()
            item1334 = _t2091
            xs1332.append(item1334)
            cond1333 = self.match_lookahead_literal("(", 0)
        export_iceberg_columns1335 = xs1332
        self.consume_literal(")")
        return export_iceberg_columns1335

    def parse_export_iceberg_column(self) -> transactions_pb2.ExportColumn:
        span_start1338 = self.span_start()
        self.consume_literal("(")
        self.consume_literal("column")
        string1336 = self.consume_terminal("STRING")
        _t2092 = self.parse_boolean_value()
        boolean_value1337 = _t2092
        self.consume_literal(")")
        _t2093 = transactions_pb2.ExportColumn(name=string1336, nullable=boolean_value1337)
        result1339 = _t2093
        self.record_span(span_start1338, "ExportColumn")
        return result1339

    def parse_iceberg_table_properties(self) -> Sequence[tuple[str, str]]:
        self.consume_literal("(")
        self.consume_literal("table_properties")
        xs1340 = []
        cond1341 = self.match_lookahead_literal("(", 0)
        while cond1341:
            _t2094 = self.parse_iceberg_property_entry()
            item1342 = _t2094
            xs1340.append(item1342)
            cond1341 = self.match_lookahead_literal("(", 0)
        iceberg_property_entrys1343 = xs1340
        self.consume_literal(")")
        return iceberg_property_entrys1343


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
